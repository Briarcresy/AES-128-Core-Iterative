#!/usr/bin/env python3
"""Enable hard-ROM support in the separately downloaded yosys-sta tool."""

from pathlib import Path

root = Path(__file__).resolve().parent.parent
tool = root / "yosys-sta"


def insert_once(path, marker, addition):
    text = path.read_text()
    if addition.strip() not in text:
        if marker not in text:
            raise SystemExit(f"cannot find integration point in {path}")
        path.write_text(text.replace(marker, marker + addition, 1))


insert_once(
    tool / "scripts" / "common.tcl",
    "source $PROJ_HOME/scripts/pdk/$PDK.tcl\n",
    "\nif {[info exists env(EXTRA_LIB_FILES)] && $env(EXTRA_LIB_FILES) ne \"\"} {\n"
    "  foreach lib $env(EXTRA_LIB_FILES) {\n"
    "    lappend LIB_FILES $lib\n"
    "  }\n"
    "}\n",
)

yosys_script = tool / "scripts" / "yosys.tcl"
text = yosys_script.read_text()
if "read_verilog -sv $file" in text:
    text = text.replace("read_verilog -sv $file", "read_verilog -D SYNTHESIS $file")
elif "read_verilog -D SYNTHESIS $file" not in text:
    raise SystemExit(f"cannot find Verilog read command in {yosys_script}")
yosys_script.write_text(text)

insert_once(
    tool / "Makefile",
    "export CLK_PORT_NAME ?= clk\n",
    "export EXTRA_LIB_FILES ?=\n",
)

print("yosys-sta hard-ROM integration is configured")
