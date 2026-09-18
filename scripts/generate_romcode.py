#!/usr/bin/env python3
"""Convert the hexadecimal AES S-box file to the ROM macro's binary format."""

from pathlib import Path

root = Path(__file__).resolve().parent.parent
source = root / "mem" / "sbox.mem"
target = root / "ip" / "ics55_ecos_rom_256x8_m8_b1" / "verilog" / "ics55_ecos_rom_256x8_m8_b1.romcode"

values = [int(line, 16) for line in source.read_text().splitlines() if line.strip()]
if len(values) != 256:
    raise SystemExit(f"expected 256 S-box values, found {len(values)}")

target.write_text("".join(f"{value:08b}\n" for value in values))
print(f"wrote {len(values)} entries to {target}")
