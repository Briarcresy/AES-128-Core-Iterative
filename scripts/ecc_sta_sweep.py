#!/usr/bin/env python3
"""Re-time one fixed routed implementation; never modifies the source workspace.

All clock periods use the same external 10 ns input/output budgets as ecc_backend.
This produces analysis reports, not a replacement ECC signoff package.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def worker(job_path):
    os.environ.setdefault("ECC_LOGGER_THROW_ON_ERROR", "1")
    from ecc_tools_bin import ecc_py as ecc
    job = json.loads(Path(job_path).read_text())
    out = Path(job["output"])
    cfg = json.loads(Path(job["db_config"]).read_text())
    assert ecc.db_init(config_path=job["db_config"], output_path=str(out), feature_path=str(out))
    assert ecc.tech_lef_init(cfg["INPUT"]["tech_lef_path"])
    assert ecc.lef_init(cfg["INPUT"]["lef_paths"])
    assert ecc.def_init(job["def"])
    ecc.lib_init(lib_paths=job["libs"])
    ecc.sdc_init(job["sdc"])
    ecc.spef_init(job["spef"])
    ecc.init_sta(config=job["sta_config"], config_dict={
        "-temp_directory_path": str(out), "-output_timing_reports": "1",
        "-output_timing_features": "1", "-timing_path_limit": "100",
        "-max_paths": "1000", "-timing_corner": job["corner"],
    })
    ecc.run_sta()
    ecc.destroy_sta()
    ecc.reset_data()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frequencies", type=float, nargs="+", required=True)
    parser.add_argument("--corners", nargs="+", help="e.g. WCL_m40/Cworst; default all 13")
    args = parser.parse_args()
    ws, out = args.workspace.resolve(), args.output.resolve()
    if out.exists():
        parser.error("output already exists; choose a fresh directory")
    if out.is_relative_to(ws):
        parser.error("analysis output must be outside the source workspace")
    wrapper = Path(shutil.which("ecc")).read_text()
    values = dict(re.findall(r"^(?:export )?([A-Z_]+)='([^']*)'", wrapper, re.M))
    if values.get("ECC_VERSION") != "v0.1.0-alpha.12":
        parser.error("this helper is validated for ECC alpha.12 only")
    runtime = Path(values["ECC_DATA_ROOT"]) / values["ECC_VERSION"] / "_internal"
    python = Path(values["CHIPCOMPILER_OSS_CAD_DIR"]) / "py3bin/python3.11"
    sta = json.loads((ws / "config/sta_ecc.json").read_text())
    original = (ws / "origin/aes.sdc").read_text()
    routed = ws / "RCX_ecc/output"
    defs = list(routed.glob("*.def.gz"))
    if len(defs) != 1:
        parser.error("expected exactly one extracted routed DEF")
    corners = []
    for group in sta["signoff"]:
        for name, rcs in group.items():
            lib = next(x for x in sta["liberty"] if x["corner"] == name)
            temp = str(lib["temperature"]).replace("-", "m")
            for rc in rcs:
                corner = f"{name}_{temp}/{rc}"
                if args.corners and corner not in args.corners:
                    continue
                spef = routed / f"Aes128Iterative_{rc}_{temp}C.spef"
                if not spef.is_file():
                    parser.error(f"missing SPEF: {spef}")
                corners.append((corner, lib["path"], spef))
    if not corners or (args.corners and set(args.corners) != {x[0] for x in corners}):
        parser.error("unknown or empty corner selection")
    if any(not math.isfinite(f) or f <= 0 or 500 / f <= 10.2 for f in args.frequencies):
        parser.error("frequency leaves no half-cycle input budget")
    out.mkdir(parents=True)
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
              [defs[0], *sorted(routed.glob("*.v.gz")), ws / "origin/aes.sdc", ws / "config/sta_ecc.json",
               *sorted(set(x[2] for x in corners))]}
    (out / "source.sha256.json").write_text(json.dumps(hashes, indent=2) + "\n")
    results = []
    for freq in args.frequencies:
        period = 1000 / freq
        sdc, n = re.subn(r"(create_clock[^\n]*-period )\S+", rf"\g<1>{period:.9f}", original)
        assert n == 1
        sdc = re.sub(r"^# Generated from ecc.toml:.*$", f"# Fixed-layout frequency scan: {freq:g} MHz; IO budgets unchanged.", sdc, flags=re.M)
        for mode, delay in [("max", period / 2 + 10), ("min", period / 2)]:
            sdc, n = re.subn(rf"(set_input_delay -clock test_clock -{mode} )\S+", rf"\g<1>{delay:.9f}", sdc)
            assert n == 1
        sdc_path = out / f"{freq:g}MHz.sdc"
        sdc_path.write_text(sdc)
        for corner, libs, spef in corners:
            dest = out / f"{freq:g}MHz" / corner
            dest.mkdir(parents=True)
            # Native STA recreates its temporary directory. Keep job and process
            # logs in the parent so the run remains reproducible and auditable.
            job = {"output": str(dest / "native"), "db_config": str(ws / "config/db_ecc.json"),
                   "sta_config": str(ws / "config/sta_ecc.json"), "def": str(defs[0]),
                   "libs": libs, "sdc": str(sdc_path), "spef": str(spef), "corner": corner}
            job_path = dest / "job.json"
            job_path.write_text(json.dumps(job, indent=2))
            env = os.environ.copy()
            env["PYTHONPATH"] = str(runtime)
            log_path = dest / "process.log"
            with log_path.open("w") as log:
                subprocess.run([str(python), str(Path(__file__).resolve()), "--worker", str(job_path)],
                               stdout=log, stderr=subprocess.STDOUT, env=env, check=True)
            if any("SDC command failed" in p.read_text(errors="replace") for p in dest.rglob("*.log")):
                raise ValueError(f"SDC rejected: {log_path}")
            summaries = list(dest.rglob("qor_summary.json"))
            if len(summaries) != 1:
                raise ValueError(f"expected one summary in {dest}, got {summaries}")
            result = {"frequency_mhz": freq, "corner": corner,
                      **json.loads(summaries[0].read_text())["summary"]}
            results.append(result)
            (out / "results.json").write_text(json.dumps(results, indent=2) + "\n")
            print(json.dumps(result), flush=True)
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest() != h for p, h in hashes.items()):
        raise ValueError("source workspace changed during analysis")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        worker(sys.argv[2])
    else:
        main()
