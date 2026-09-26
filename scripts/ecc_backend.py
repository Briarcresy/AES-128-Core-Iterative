#!/usr/bin/env python3
"""Prepare and run the AES hard-ROM flow with ECC 0.1.0a12 (no installed-tool edits)."""

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import shutil
import tomllib
import tarfile

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "aes-mpc-ecc"
ROM = "ics55_ecos_rom_256x8_m8_b1"
CORNERS = {
    "MAX": "ss1p08v125ccmax",
    "WCL": "ss1p08vm40ccmax",
    "TYP": "tt1p2v25cctyp",
    "MIN": "ff1p32vm40ccmin",
    "ML": "ff1p32v125ccmin",
}


def run(*args):
    print("+", " ".join(map(str, args)), flush=True)
    command = list(map(str, args))
    env = os.environ.copy()
    if command[0] == "ecc":
        policy_path = PROJECT / "optimization.json"
        if policy_path.exists():
            policy = json.loads(policy_path.read_text())
            strategy = policy["synthesis_strategy"]
            if not re.fullmatch(r"AREA (?:[0-9]|1[0-2])", strategy):
                raise ValueError("Area-first policy requires AREA 0..12.")
            env["YOSYS_SYNTH_STRATEGY"] = strategy
            print("Area-first synthesis:", strategy, flush=True)
        # Read the installed release wrapper without modifying it or executing its text.
        wrapper = Path(shutil.which("ecc")).read_text()
        values = dict(re.findall(r"^(?:export )?([A-Z_]+)='([^']*)'", wrapper, re.M))
        required = [
            "ECC_DATA_ROOT",
            "ECC_VERSION",
            "CHIPCOMPILER_OSS_CAD_DIR",
            "CHIPCOMPILER_ECC_SIZER_ROOT",
        ]
        if not all(k in values for k in required):
            raise ValueError(
                "Unsupported ECC launcher; expected the installed release wrapper."
            )
        if values["ECC_VERSION"] != "v0.1.0-alpha.12":
            raise ValueError(
                "This adapter is validated for ECC alpha.12; review after upgrading."
            )
        env.update({k: v for k, v in values.items() if k.startswith("CHIPCOMPILER_")})
        env["AES_ECC_REAL_YOSYS"] = str(
            Path(values["CHIPCOMPILER_OSS_CAD_DIR"]) / "bin/yosys"
        )
        local = PROJECT / "generated/toolchain/bin"
        local.mkdir(parents=True, exist_ok=True)
        launcher = local / "yosys"
        launcher.write_text(
            "#!" + sys.executable + "\n" + (ROOT / "scripts/ecc_yosys.py").read_text()
        )
        launcher.chmod(0o755)
        env["CHIPCOMPILER_OSS_CAD_DIR"] = str(local.parent)
        env["PATH"] = (
            values["CHIPCOMPILER_ECC_SIZER_ROOT"] + "/bin:" + env.get("PATH", "")
        )
        command[0] = str(Path(values["ECC_DATA_ROOT"]) / values["ECC_VERSION"] / "ecc")
    subprocess.run(command, cwd=ROOT, check=True, env=env)


def link(target, source):
    if not source.is_dir():
        raise ValueError(f"Missing PDK directory: {source}")
    if target.is_symlink() and target.resolve() == source.resolve():
        return
    if target.exists() or target.is_symlink():
        raise ValueError(f"Refusing to replace existing path: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(source.resolve(), target_is_directory=True)


def prepare(pdk_root):
    cfg = tomllib.loads((PROJECT / "ecc.toml").read_text())
    # Use complete standard cells from the ECC installation, local ROM from this repo.
    base = Path(pdk_root).expanduser().resolve()
    overlay = PROJECT / "pdk"
    link(overlay / "prtech", base / "prtech")
    link(overlay / "IP/STD_cell", base / "IP/STD_cell")
    link(overlay / "IP/ROM", ROOT / "pdk/IP/ROM")
    for field in ("lefs", "libs"):
        for name in cfg["pdk"]["overrides"][field]:
            if not (overlay / name).is_file():
                raise ValueError(f"Missing {field}: {overlay / name}")
    for suffix in CORNERS.values():
        p = overlay / f"IP/ROM/{ROM}/lib/{ROM}_{suffix}.lib"
        if not p.is_file():
            raise ValueError(f"Missing ROM corner: {p}")
    generated = PROJECT / "generated"
    generated.mkdir(exist_ok=True)
    # Read synthesis declarations from Liberty. Do not feed the behavioral ROM model,
    # or an empty RTL stub that could override the imported Liberty module, to synthesis.
    sources = [
        ROOT / name.strip()
        for name in (ROOT / "files.f").read_text().splitlines()
        if name.strip().startswith("rtl/")
    ]
    combined = "`define SYNTHESIS\n" + "\n".join(
        f"// Source: {p.relative_to(ROOT)}\n{p.read_text()}\n" for p in sources
    )
    (generated / "aes_synthesis.v").write_text(combined)
    freq = cfg["design"]["frequency_mhz"]
    if not isinstance(freq, (int, float)) or freq <= 0:
        raise ValueError("frequency_mhz must be positive.")
    period = 1000.0 / freq
    if period / 2 <= 10.2:
        raise ValueError(
            "Target frequency leaves no half-cycle input budget; review IO constraints."
        )
    input_ports = " ".join(["reset"] + [f"io_in_{i}" for i in range(66)])
    output_ports = " ".join(
        f"{bus}_{i}" for bus in ("io_out", "io_oe") for i in range(66)
    )
    (generated / "aes.sdc").write_text(
        f"""# Generated from ecc.toml: {freq:g} MHz. IO budgets are board assumptions.
create_clock -name test_clock -period {period:.6f} [get_ports clock]
# Separate provisional setup/hold budgets; zero hold uncertainty requires
# platform/clock-budget validation and is not proof that old violations were false.
set_clock_uncertainty -setup 0.200 [get_clocks test_clock]
set_clock_uncertainty -hold 0.000 [get_clocks test_clock]
# Propagate actual CTS insertion delay/skew. This does not replace the
# independent uncertainty budgets above.
set_propagated_clock [get_clocks test_clock]
# FPGA launches on falling edge: fold the half-cycle phase into input delay.
# This ECC release does not support the -clock_fall input-delay switch.
set_input_delay -clock test_clock -max {period / 2 + 10:.6f} [get_ports {{{input_ports}}}]
set_input_delay -clock test_clock -min {period / 2:.6f} [get_ports {{{input_ports}}}]
# FPGA captures outputs on the rising edge. No false-path exemption for reset.
set_output_delay -clock test_clock -max 10.000 [get_ports {{{output_ports}}}]
set_output_delay -clock test_clock -min 0.000 [get_ports {{{output_ports}}}]
"""
    )
    snapshot = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [
            *sources,
            ROOT / "mem/sbox.mem",
            PROJECT / "ecc.toml",
            PROJECT / "macro-placement.json",
            *([PROJECT / "optimization.json"] if (PROJECT / "optimization.json").exists() else []),
        ]
    }
    (generated / "inputs.sha256.json").write_text(json.dumps(snapshot, indent=2) + "\n")
    run("make", "test")
    check = ["ecc", "check", "--project", PROJECT]
    manifest = PROJECT / "project.json"
    if manifest.exists():
        entries = json.loads(manifest.read_text()).get("workspaces", [])
        if entries:
            check += ["--workspace", entries[0]["workspace_id"]]
    run(*check)
    print("Prepared: top=Aes128Iterative, ROM=hard macro, target=", freq, "MHz")
    print(
        "Delivery: final/design .v + .def; ROM physical content must be confirmed with the integrator."
    )


def read_text(path):
    return gzip.open(path, "rt").read() if path.suffix == ".gz" else path.read_text()


def verify_rom(workspace, physical=False):
    folder = workspace / (
        "Floorplan_ecc/output" if physical else "Synthesis_yosys/output"
    )
    paths = list(folder.glob("*.def*" if physical else "*.v*"))
    paths = [p for p in paths if p.is_file()]
    if not paths:
        raise ValueError(f"No outputs in {folder}")
    counts = []
    for p in paths:
        text = read_text(p)
        pattern = rf"^\s*-\s+\S+\s+{ROM}\b" if physical else rf"^\s*{ROM}\s+\\?\S+\s*\("
        count = len(re.findall(pattern, text, re.M))
        counts.append(count)
        print(f"{p.name}: {count} ROM instance(s)")
    if any(count != 1 for count in counts):
        raise ValueError(
            "Expected exactly one hard-ROM instance; refusing to continue."
        )


def configure_workspace(workspace):
    log = workspace / "Synthesis_yosys/log/Synthesis.log"
    if log.is_file() and "SDC command failed" in log.read_text(errors="replace"):
        raise ValueError(
            "Synthesis STA rejected SDC commands; fix constraints and use a new workspace."
        )
    frozen = workspace / "config/inputs.sha256.json"
    snapshot = frozen if frozen.exists() else PROJECT / "generated/inputs.sha256.json"
    expected = json.loads(snapshot.read_text())
    changed = [
        name
        for name, digest in expected.items()
        if not (ROOT / name).is_file()
        or hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest
    ]
    if changed:
        raise ValueError("Inputs changed; use a new workspace: " + ", ".join(changed))
    if not frozen.exists():
        frozen.write_text(snapshot.read_text())
    policy_source = PROJECT / "optimization.json"
    if policy_source.exists():
        policy_copy = workspace / "config/optimization.json"
        if not policy_copy.exists():
            policy_copy.write_text(policy_source.read_text())
    path = workspace / "config/sta_ecc.json"
    data = json.loads(path.read_text())
    # ECC a12 refreshes these existing arrays in place; PDK overrides alone do not
    # append a macro to the five STA corner libraries. Keep paths under overlay root.
    if {entry["corner"] for entry in data["liberty"]} != set(CORNERS):
        raise ValueError(
            "Unexpected ECC STA corners; review script for this ECC version."
        )
    for entry in data["liberty"]:
        suffix = CORNERS[entry["corner"]]
        library = PROJECT / f"pdk/IP/ROM/{ROM}/lib/{ROM}_{suffix}.lib"
        paths = [p for p in entry["path"] if ROM not in p]
        entry["path"] = paths + [str(library)]
        if not all(Path(p).is_file() for p in entry["path"]):
            raise ValueError(f"Missing STA libraries: {entry}")
    path.write_text(json.dumps(data, indent=2) + "\n")
    model = workspace / "config/aes_rom_lec.v"
    if not model.exists():
        values = [int(x, 16) for x in (ROOT / "mem/sbox.mem").read_text().split()]
        if len(values) != 256:
            raise ValueError("S-box must contain 256 bytes.")
        cases = "\n".join(
            f"8'h{i:02x}: value = 8'h{v:02x};" for i, v in enumerate(values)
        )
        model.write_text(
            f"""// Frozen AES ROM functional model for LEC; never a synthesis input.
module {ROM}(input [7:0] A, input CEB, CLK, MARE, input [3:0] MAR, output reg [7:0] Q);
reg [7:0] value;
always @* begin
case(A)
{cases}
endcase
end
always @(posedge CLK) if (!CEB) Q <= value;
endmodule
"""
        )
    placement = workspace / "config/macro-placement.json"
    if not placement.exists():
        placement.write_text((PROJECT / "macro-placement.json").read_text())
    seed = workspace / "Synthesis_yosys/output/aes128-iterative_Synthesis.def.gz"
    if not seed.exists():
        wrapper = Path(shutil.which("ecc")).read_text()
        values = dict(re.findall(r"^(?:export )?([A-Z_]+)='([^']*)'", wrapper, re.M))
        native = Path(values["ECC_DATA_ROOT"]) / values["ECC_VERSION"] / "_internal"
        python = Path(values["CHIPCOMPILER_OSS_CAD_DIR"]) / "py3bin/python3.11"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(native)
        log = workspace / "config/rom-floorplan.log"
        with log.open("w") as output:
            subprocess.run(
                [
                    str(python),
                    str(ROOT / "scripts/ecc_rom_floorplan.py"),
                    str(workspace),
                ],
                env=env,
                stdout=output,
                stderr=subprocess.STDOUT,
                check=True,
            )
        print("ROM seed DEF created; log:", log)
    verify_rom(workspace)
    print("All five STA corners include their corresponding ROM library.")


def export_delivery(workspace):
    for log in workspace.glob("*/log/*.log"):
        if "SDC command failed" in log.read_text(errors="replace"):
            raise ValueError(
                f"Cannot export: rejected timing constraints recorded in {log}. Use a clean corrected run."
            )
    directory = PROJECT / "signoff" / workspace.name
    archive = PROJECT / "signoff" / (workspace.name + ".tar.gz")
    if directory.exists() or archive.exists():
        raise ValueError(
            "Export already exists; retain it and use another workspace for a new delivery."
        )
    archive.parent.mkdir(exist_ok=True)
    run(
        "ecc",
        "signoff",
        "export",
        "--project",
        PROJECT,
        "--workspace",
        workspace.name,
        "--output",
        archive,
    )
    outputs = {}
    with tarfile.open(archive) as package:
        for ext in ("v", "def"):
            members = [
                m
                for m in package.getmembers()
                if m.isfile()
                and "/final/design/" in "/" + m.name
                and m.name.endswith((f".{ext}", f".{ext}.gz"))
            ]
            if len(members) != 1:
                raise ValueError(
                    f"Expected one final .{ext} in package, found {len(members)}."
                )
            member = members[0]
            payload = package.extractfile(member).read()
            if member.name.endswith(".gz"):
                payload = gzip.decompress(payload)
            text = payload.decode()
            pattern = (
                rf"^\s*-\s+\S+\s+{ROM}\b"
                if ext == "def"
                else rf"^\s*{ROM}\s+\\?\S+\s*\("
            )
            if len(re.findall(pattern, text, re.M)) != 1:
                raise ValueError(
                    f"Final .{ext} does not contain exactly one ROM macro."
                )
            top = (
                r"DESIGN\s+Aes128Iterative\s*;"
                if ext == "def"
                else r"module\s+Aes128Iterative\b"
            )
            if not re.search(top, text):
                raise ValueError(f"Unexpected top in final .{ext}.")
            outputs[f"aes128-iterative.{ext}"] = payload
    directory.mkdir()
    for name, payload in outputs.items():
        (directory / name).write_bytes(payload)
    (directory / "sha256.json").write_text(
        json.dumps(
            {name: hashlib.sha256(data).hexdigest() for name, data in outputs.items()},
            indent=2,
        )
        + "\n"
    )
    print("Upload the matched .v and .def in:", directory)


def main():
    global PROJECT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=["prepare", "synth", "run", "resume", "inspect", "export"]
    )
    parser.add_argument(
        "--workspace", default="area20", help="Workspace name; use a new name for a fresh run"
    )
    parser.add_argument(
        "--project", type=Path, default=PROJECT,
        help="ECC project directory; use separate directories for independent experiments",
    )
    parser.add_argument(
        "--pdk-root",
        default=os.environ.get(
            "AES_ECC_PDK_ROOT",
            str(Path.home() / ".local/share/ecc/pdks/icsprout55/v1.10.102"),
        ),
    )
    args = parser.parse_args()
    PROJECT = args.project.expanduser().resolve()
    if not PROJECT.is_relative_to(ROOT):
        parser.error("project must be inside this repository")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.workspace):
        parser.error(
            "workspace must contain only letters, digits, underscores or hyphens"
        )
    workspace = PROJECT / ("ws-" + args.workspace)
    ecc = ["ecc", "run", "--project", PROJECT, "--workspace", workspace.name]
    # No automatic overwrite/deletion of old runs. New RTL/frequency => new workspace.
    if args.action in ("synth", "run") and workspace.exists():
        raise ValueError(
            f"{workspace} already exists: use resume or choose another --workspace."
        )
    if args.action in ("prepare", "synth", "run"):
        prepare(args.pdk_root)
    if args.action in ("synth", "run"):
        run(*ecc, "--from", "synthesis", "--to", "synthesis")
        configure_workspace(workspace)
    elif args.action == "resume":
        if not workspace.is_dir():
            raise ValueError(f"Workspace does not exist: {workspace}")
        configure_workspace(workspace)
    if args.action in ("run", "resume"):
        # Reconcile the synthesis prefix to the full rtl2gds preset, then continue.
        run(*ecc)
    if args.action == "export":
        export_delivery(workspace)
    if args.action in ("inspect", "run", "resume"):
        verify_rom(workspace)
        if (workspace / "Floorplan_ecc/output").is_dir():
            verify_rom(workspace, physical=True)
        run("ecc", "status", "--project", PROJECT, "--workspace", workspace.name)
        run(
            "ecc",
            "signoff",
            "inspect",
            "--project",
            PROJECT,
            "--workspace",
            workspace.name,
        )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        sys.exit(f"ERROR: {exc}")
