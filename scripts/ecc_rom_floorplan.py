#!/usr/bin/env python3
"""Create a pre-floorplan DEF with the existing ROM instance fixed at 20um,20um.
Run with the Python 3.11 interpreter and native libraries shipped with ECC.
"""
import json
import gzip
import os
from pathlib import Path
import re
import sys
os.environ.setdefault('ECC_LOGGER_THROW_ON_ERROR', '1')
from ecc_tools_bin import ecc_py as ecc

workspace = Path(sys.argv[1])
config = json.loads((workspace / 'config/db_ecc.json').read_text())
inputs = config['INPUT']
out = workspace / 'Synthesis_yosys/output/aes128-iterative_Synthesis.def.gz'
if out.exists():
    sys.exit('Seed DEF already exists; no replacement performed.')
netlist = workspace / 'Synthesis_yosys/output/aes128-iterative_Synthesis.v.gz'
units = int(re.search(r'DATABASE MICRONS\s+(\d+)', Path(inputs['tech_lef_path']).read_text())[1])
assert ecc.db_init(config_path=str(workspace / 'config/db_ecc.json'))
assert ecc.tech_lef_init(inputs['tech_lef_path'])
assert ecc.lef_init(inputs['lef_paths'])
assert ecc.verilog_init(str(netlist), 'Aes128Iterative')
placement = json.loads((workspace / 'config/macro-placement.json').read_text())
assert ecc.place_instance(placement['instance'], round(placement['x_um'] * units),
                          round(placement['y_um'] * units), placement['orientation'],
                          placement['cell'], '', 'fixed', False)
assert ecc.def_save(str(out))
ecc.reset_data()
# The native writer emits an invalid empty DIEAREA before floorplanning. Omit
# this optional statement; ECC iFP computes the actual die from utilization.
text = gzip.open(out, 'rt').read()
if 'DIEAREA ;' not in text:
    raise RuntimeError('Unexpected seed DEF format; review the ECC version.')
with gzip.open(out, 'wt') as stream:
    stream.write(text.replace('DIEAREA ;\n', ''))
print('Created pre-floorplan DEF:', placement)
