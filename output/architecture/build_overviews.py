"""Generate the RTL-derived controller and transform overview figures."""
from figure_lib import Figure, ROOT, DATA, KEY, CTRL, INK, MUTED, BLUE, GOLD, GRAY, LINE


def _matrix(fig, x, y, values, cell_w=50, cell_h=39, color=DATA, fill=BLUE, size=18):
    for row, cells in enumerate(values):
        for col, value in enumerate(cells):
            fig.rect(x + col * cell_w, y + row * cell_h, cell_w, cell_h,
                     fill=fill, stroke=LINE, width=1)
            fig.text(x + (col + .5) * cell_w, y + row * cell_h + cell_h * .66,
                     value, size, color, anchor='middle')


def build_controller():
    f = Figure(1600, 1160, 'Controller Overview',
               'Three-phase controller with a shared round counter and a one-clock done pulse', 4)

    f.panel(45, 120, 1510, 360, 'Phase Sequencer  |  controller', color=CTRL)
    f.block(180, 230, 260, 115, 'IDLE', 'Load data_in\nAccept start',
            color=CTRL, fill=GRAY)
    f.block(665, 230, 300, 115, 'EXPAND', 'Write next round key\n10 clocks',
            color=CTRL, fill=GRAY)
    f.block(1190, 230, 260, 115, 'ROUND', 'Update State Register\n10 clocks',
            color=CTRL, fill=GRAY)
    f.path([(440, 287), (665, 287)], color=CTRL, dash=True)
    f.label(552, 266, 'start = 1', color=CTRL)
    f.text(552, 317, 'count ← 0', 17, CTRL, anchor='middle')
    f.path([(965, 287), (1190, 287)], color=CTRL, dash=True)
    f.label(1077, 266, 'count = 9', color=CTRL)
    f.text(1077, 317, 'count ← 0', 17, CTRL, anchor='middle')
    f.path([(1320, 230), (1320, 186), (310, 186), (310, 230)], color=CTRL, dash=True)
    f.label(815, 179, 'count = 9 / done ← 1; count holds 9', color=CTRL)
    f.text(310, 380, 'start = 0: stay in IDLE', 17, CTRL, anchor='middle')
    f.text(815, 380, 'count < 9: stay; count ← count + 1', 17, CTRL, anchor='middle')
    f.text(1320, 380, 'count < 9: stay;', 17, CTRL, anchor='middle')
    f.text(1320, 405, 'count ← count + 1', 17, CTRL, anchor='middle')
    f.path([(75, 421), (1525, 421)], color=LINE, width=1, arrow=False)
    f.text(75, 452, 'Synchronous rst: phase ← IDLE; count ← 0; done ← 0.', 18, CTRL)
    f.text(1525, 452, 'start is sampled only in IDLE.', 18, CTRL, anchor='end')

    f.panel(45, 505, 930, 300, 'State Input MUX and Key Write Decode', color=CTRL)
    xs = [65, 278, 398, 533, 668, 955]
    y0, rh = 554, 43
    f.rect(xs[0], y0, xs[-1] - xs[0], 5 * rh, fill='white', stroke=LINE, width=1)
    f.rect(xs[0], y0, xs[-1] - xs[0], rh, fill=GRAY, stroke='none')
    headers = ['phase', 'count', 'data_sel', 'key_step', 'Selected state source']
    rows = [
        ['IDLE', 'any', '0', '0', 'data_in'],
        ['EXPAND', '0–8', '3', '1', 'State hold / feedback'],
        ['EXPAND', '9', '1', '1', 'Initial AddRoundKey'],
        ['ROUND', '0–9', '2', '0', 'AES Round result'],
    ]
    for c, heading in enumerate(headers):
        f.text(xs[c] + 12, y0 + 28, heading, 17, CTRL, bold=True)
    for r, row in enumerate(rows):
        y = y0 + (r + 1) * rh
        f.path([(xs[0], y), (xs[-1], y)], color=LINE, width=1, arrow=False)
        for c, value in enumerate(row):
            f.text(xs[c] + 12, y + 28, value, 17, INK)
    for x in xs[1:-1]:
        f.path([(x, y0), (x, y0 + 5 * rh)], color=LINE, width=1, arrow=False)

    f.panel(1000, 505, 555, 300, 'Registers and Status Outputs', color=CTRL)
    f.block(1025, 554, 240, 80, 'Round Counter', 'count[3:0]', color=CTRL, fill=GRAY)
    f.block(1290, 554, 240, 80, 'Done Register', 'done', color=CTRL, fill=GRAY)
    f.text(1025, 668, 'count is reused in EXPAND and ROUND.', 18, CTRL)
    f.text(1025, 700, 'busy = (phase != IDLE)', 18, CTRL)
    f.text(1025, 732, 'final_step = (count == 9)', 18, CTRL)
    f.text(1025, 764, 'done clears on the next clock.', 18, CTRL)

    f.panel(45, 830, 1510, 255, 'Transaction Timing  |  rising clock edges', color=CTRL)
    f.block(75, 901, 230, 88, 'Accept start', 'Cycle 0\nCapture data_in', color=CTRL, fill=GRAY)
    f.block(355, 901, 395, 88, 'EXPAND', 'Cycles 1–10\nGenerate K1–K10', color=KEY, fill=GOLD)
    f.block(800, 901, 395, 88, 'ROUND', 'Cycles 11–20\nApply rounds 1–10', color=DATA, fill=BLUE)
    f.block(1245, 901, 280, 88, 'Next IDLE clock', 'Cycle 21\nReload data_in', color=CTRL, fill=GRAY)
    for a, b in [(305, 355), (750, 800), (1195, 1245)]:
        f.path([(a, 945), (b, 945)], color=CTRL, dash=True)
    f.text(75, 1027, 'Final EXPAND edge: K10 write + Initial AddRoundKey.', 18, KEY)
    f.text(800, 1027, 'Final ROUND edge: ciphertext; done = 1; busy = 0.', 18, DATA)
    f.text(75, 1060, 'final_step is a count comparison only; it is also high at the end of EXPAND and may remain high in IDLE.', 17, MUTED)
    f.footer('Source: rtl/core/controller.v:13–57; aes128_iterative_core.v:54–71')
    return f.save('04_controller')


def build_transforms():
    f = Figure(1600, 1200, 'AES Transform Overview',
               'Combinational forward transforms and byte organization implemented by the RTL', 5)

    f.panel(45, 120, 730, 360, 'AES State  |  column-major byte ordering', color=DATA)
    f.text(70, 205, '128-bit state', 21, DATA, bold=True)
    f.text(70, 244, 'b0 = state[127:120]', 18, DATA)
    f.text(70, 275, 'b15 = state[7:0]', 18, DATA)
    original = [[f'b{4*c+r}' for c in range(4)] for r in range(4)]
    mx, my, cw, ch = 360, 207, 80, 42
    for c in range(4):
        f.text(mx + (c + .5) * cw, my - 15, f'col {c}', 16, MUTED, anchor='middle')
    for r in range(4):
        f.text(mx - 13, my + r * ch + 28, f'r{r}', 16, MUTED, anchor='end')
    _matrix(f, mx, my, original, cw, ch)
    f.text(70, 418, 'Byte index = 4 × column + row', 18, DATA)
    f.text(70, 451, 'state = {b0, b1, ..., b15}', 18, DATA)

    f.panel(805, 120, 750, 360, 'S-box Lookup and RTL Replication', color=DATA)
    f.text(830, 235, 'in_byte[7:0]', 18, DATA)
    f.path([(970, 228), (1050, 228)], color=DATA)
    f.block(1050, 177, 280, 102, 'S-box', '256 × 8-bit ROM\nAsynchronous lookup', color=DATA, fill=BLUE)
    f.path([(1330, 228), (1450, 228), (1450, 283)], color=DATA)
    f.text(1370, 307, 'out_byte[7:0]', 18, DATA)
    f.text(830, 315, 'Independent instances in each transform', 17, MUTED)
    f.block(830, 335, 340, 94, 'SubBytes', '16 parallel S-box instances', color=DATA, fill=BLUE)
    f.block(1195, 335, 335, 94, 'SubWord', '4 separate S-box instances', color=KEY, fill=GOLD)
    f.text(830, 455, 'ROM image: mem/sbox.mem; no registered S-box output.', 17, MUTED)

    f.panel(45, 505, 730, 330, 'ShiftRows', color=DATA)
    f.text(65, 563, 'Fixed byte permutation; row r rotates left by r bytes.', 18, DATA)
    f.text(190, 593, 'Input state', 17, MUTED, anchor='middle')
    f.text(595, 593, 'Output state', 17, MUTED, anchor='middle')
    _matrix(f, 90, 610, original)
    shifted = [[f'b{4*((c+r)%4)+r}' for c in range(4)] for r in range(4)]
    _matrix(f, 495, 610, shifted)
    f.path([(315, 688), (470, 688)], color=DATA)
    f.label(392, 672, 'ShiftRows', size=17, color=DATA)
    f.text(65, 806, 'out[r,c] = in[r,(c+r) mod 4]', 18, DATA)

    f.panel(805, 505, 750, 330, 'MixColumns', color=DATA)
    f.text(825, 563, 'Four independent 32-bit column transforms', 18, DATA)
    f.text(830, 637, 'state_in[127:0]', 17, DATA)
    f.path([(993, 630), (1045, 630)], color=DATA)
    f.block(1045, 590, 280, 80, 'MixColumns', '4 parallel GF(2^8) transforms', color=DATA, fill=BLUE)
    f.path([(1325, 630), (1445, 630), (1445, 672)], color=DATA)
    f.text(1360, 696, 'state_out[127:0]', 17, DATA)
    coeffs = [['02', '03', '01', '01'], ['01', '02', '03', '01'],
              ['01', '01', '02', '03'], ['03', '01', '01', '02']]
    f.text(845, 765, 'M =', 20, DATA)
    _matrix(f, 920, 707, coeffs, 42, 25, size=16)
    f.text(1115, 749, 'Applied to each column', 17, DATA)
    f.text(1115, 778, 'Reduction polynomial: 0x11B', 17, DATA)
    f.text(1115, 807, 'No pipeline registers', 17, MUTED)

    f.panel(45, 860, 1510, 270, 'AddRoundKey  |  128-bit XOR', color=DATA)
    f.text(110, 953, 'state_in[127:0]', 18, DATA)
    f.path([(320, 946), (680, 946)], color=DATA)
    f.xor(702, 946, color=INK)
    f.path([(724, 946), (1000, 946)], color=DATA)
    f.text(1030, 953, 'state_out[127:0]', 18, DATA)
    f.text(110, 1022, 'round_key[127:0]', 18, KEY)
    f.path([(320, 1015), (702, 1015), (702, 968)], color=KEY)
    f.text(850, 1022, 'state_out = state_in ^ round_key', 18, DATA)
    f.text(80, 1090, 'Two RTL instances: Initial AddRoundKey at the top level, and AddRoundKey inside AES Round.', 18, MUTED)
    f.footer('Source: rtl/core/{sub_bytes, sbox_byte, shift_rows, mix_columns, add_round_key, key_expansion}.v')
    return f.save('05_aes_transforms')


if __name__ == '__main__':
    print(build_controller())
    print(build_transforms())
