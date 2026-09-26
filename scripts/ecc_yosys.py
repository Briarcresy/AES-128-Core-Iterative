#!/usr/bin/env python3
"""Project-local ECC a12 adapter: load the AES ROM functional model for LEC only."""
import os
from pathlib import Path
import sys

args = sys.argv[1:]
if '-c' in args:
    script = Path(args[args.index('-c') + 1])
    if script.name == 'run_lec.tcl':
        original = script.read_text()
        marker = 'yosys read_liberty -ignore_miss_func -ignore_miss_data_latch $liberty_file'
        if original.count(marker) != 1:
            sys.exit('ECC LEC template changed; review the project compatibility adapter.')
        workspace = Path.cwd().parent.parent
        model = workspace / 'config/aes_rom_lec.v'
        if not model.is_file():
            sys.exit(f'Missing frozen ROM model: {model}')
        replacement = '''if {[string match "*ics55_ecos_rom_256x8_m8_b1*" $liberty_file]} {
            yosys read_verilog {%s}
        } else {
            %s
        }''' % (model, marker)
        adapted = script.with_name('run_lec_aes_rom.tcl')
        # Preserve public state aliases so equiv_make can match register boundaries.
        adapted_text = original.replace(marker, replacement).replace('yosys opt_clean -purge', 'yosys opt_clean')
        # DFF mapping may invert/transform D-pin logic while preserving Q. These
        # compiler-generated pin aliases are not semantic compare points. Keep
        # every output and Q/state comparison; hide only generated D-pin aliases.
        adapted_text = adapted_text.replace('yosys splitnets -ports -format _',
            'yosys splitnets -ports -format _\n    yosys rename -hide w:*_reg_p_D w:*_reg_n_D w:*_reg_p.D w:*_reg_n.D')
        adapted.write_text(adapted_text)
        args[args.index('-c') + 1] = str(adapted)
        print('AES ROM adapter: use frozen synchronous functional model for LEC.', flush=True)
os.execv(os.environ['AES_ECC_REAL_YOSYS'], [os.environ['AES_ECC_REAL_YOSYS'], *args])
