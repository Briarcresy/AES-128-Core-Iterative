"""Native draw.io pages for the RTL MixColumns and xtime datapaths."""
from drawio_lib import Page, DATA, INK, MUTED, CTRL


def build_mix():
    p = Page(
        5, '05 mix_column', 'mix_column — 单列组合运算',
        '一个 32-bit 列单元在四列间分时复用；单元内部有四路并行 xtime，全部为组合逻辑。',
        'rtl/core/mix_column.v')

    p.text('① 字节拆分与常数乘法', 48, 144, 670, 32, size=20, bold=True)
    p.text('② 按 RTL 表达式形成四个输出字节', 820, 144, 700, 32,
           size=20, bold=True)
    p.line([(795, 181), (795, 821)], arrow=False, width=1,
           color='#bcc8d2')

    column = p.tag('column_in · 32 bit', 45, 186, 220, 40)
    # The heavy native wire is a schematic byte breakout, not a register.
    trunk = p.dot(88, 246, visible=False)
    p.edge(column, trunk, sp=(.195, 1), tp=(.5, .5), arrow=False, width=2.6)
    previous = trunk
    result_dots = []
    input_slices = ['[31:24]', '[23:16]', '[15:8]', '[7:0]']
    operands = [
        ('a2', 'b3', 'c', 'd'),
        ('a', 'b2', 'c3', 'd'),
        ('a', 'b', 'c2', 'd3'),
        ('a3', 'b', 'c', 'd2'),
    ]

    for row, (name, slc, terms) in enumerate(zip('abcd', input_slices, operands)):
        cy = 320 + row * 150
        tap = p.dot(88, cy)
        p.edge(previous, tap, sp=(.5, .5), tp=(.5, .5), arrow=False, width=2.6)
        previous = tap
        byte = p.tag(f'{name} · 8 bit', 145, cy - 17, 140, 34)
        p.edge(tap, byte, sp=(.5, .5))
        p.text(slc, 112, cy - 49, 160, 25, size=14, color=MUTED,
               align='center')
        in_branch = p.dot(318, cy)
        p.edge(byte, in_branch, tp=(.5, .5), arrow=False)
        xt = p.box('xtime\n×02', 349, cy - 36, 110, 72,
                   fill=DATA, size=18, bold=True)
        p.edge(in_branch, xt, sp=(.5, .5))
        double_branch = p.dot(490, cy)
        p.edge(xt, double_branch, tp=(.5, .5), arrow=False)

        twice = p.tag(f'{name}2 · 8 bit', 509, cy - 69, 120, 32)
        p.edge(double_branch, twice, sp=(.5, .5),
               via=[(490, cy - 53)])
        times3 = p.xor(604, cy - 21)
        p.edge(double_branch, times3, sp=(.5, .5))
        p.edge(in_branch, times3, sp=(.5, .5), tp=(.5, 1),
               via=[(318, cy + 49), (625, cy + 49)])
        third = p.tag(f'{name}3 · 8 bit', 669, cy - 17, 113, 34)
        p.edge(times3, third)
        p.text('×03 = ×02 ⊕ 原字节', 398, cy + 53, 363, 25,
               size=15, color=MUTED, align='center')

        # Three 8-bit XORs realize each four-term RTL expression. The tags
        # refer to the very same byte nets on the left; they are not storage.
        first = p.tag(f'{terms[0]} · 8 bit', 817, cy - 17, 110, 34)
        chain = []
        for col, term in enumerate(terms[1:]):
            xx = 964 + col * 132
            gate = p.xor(xx, cy - 21)
            top = p.tag(f'{term} · 8 bit', xx - 34, cy - 87, 110, 32)
            p.edge(top, gate, sp=(.5, 1), tp=(.5, 0))
            if col == 0:
                p.edge(first, gate)
            else:
                p.edge(chain[-1], gate)
            p.text('8 bit', xx - 7, cy + 26, 57, 23,
                   size=13, color=MUTED, align='center')
            chain.append(gate)
        result = p.tag(f'column_out{slc}\n8 bit', 1336, cy - 27, 174, 54)
        p.edge(chain[-1], result)
        joined = p.dot(1540, cy)
        p.edge(result, joined, tp=(.5, .5), arrow=False)
        result_dots.append(joined)

    for first, second in zip(result_dots, result_dots[1:]):
        p.edge(first, second, sp=(.5, .5), tp=(.5, .5),
               arrow=False, width=2.6)
    result_bus = p.tag('column_out · 32 bit', 1300, 825, 240, 40)
    p.edge(result_dots[-1], result_bus, sp=(.5, .5), tp=(1, .5),
           via=[(1540, 845)], width=2.6)

    p.note('GF(2⁸)（8 位有限域）：×02 由 xtime 实现；\n×03 由 xtime(x) ⊕ x 实现。xtime 的展开见图 06。',
           48, 851, 720, 68)
    p.note('同名 tunnel（网络标签）连接同一 8-bit 数据网。\n三个 XOR 符号表示每个输出的四项异或，未进行公共项优化。',
           817, 872, 723, 54)
    return p


def build_xtime():
    p = Page(
        6, '06 xtime', 'xtime — ×02 in GF(2⁸)',
        '固定左移布线与条件模约减；这是 mix_column 内 Verilog function 的图形封装，无寄存器。',
        'rtl/core/mix_column.v : function xtime')
    p.text("xtime(x) = {x[6:0], 1'b0} ⊕ (x[7] ? 8'h1b : 8'h00)",
           67, 150, 1455, 48, size=25, bold=True)

    source = p.tag('x[7:0] · 8 bit', 69, 331, 181, 48)
    branch = p.dot(295, 355)
    p.edge(source, branch, tp=(.5, .5), arrow=False)

    shift = p.box('', 390, 235, 400, 240, fill='#ffffff')
    p.text('Fixed shift（固定左移布线）', 15, 11, 370, 32,
           size=19, bold=True, align='center', parent=shift)
    p.text('输入位', 12, 50, 70, 23, size=13, color=MUTED, parent=shift)
    p.text('输出位', 12, 190, 70, 23, size=13, color=MUTED, parent=shift)
    top_bits = []
    bottom_bits = []
    for i in range(8):
        bx = 20 + i * 45
        top_bits.append(p.box(f'x{7-i}', bx, 78, 38, 32,
                              fill=CTRL if i == 0 else DATA,
                              size=15, parent=shift))
        bottom_bits.append(p.box(f'x{6-i}' if i < 7 else '0',
                                 bx, 157, 38, 32,
                                 fill=DATA if i < 7 else CTRL,
                                 size=15, parent=shift))
    for i in range(1, 8):
        p.edge(top_bits[i], bottom_bits[i-1], sp=(.5, 1), tp=(.5, 0))
    p.text('x7 不进入移位结果', 104, 207, 271, 23,
           size=13, color=MUTED, align='right', parent=shift)
    p.edge(branch, shift, sp=(.5, .5))
    p.note('8-bit 左移结果；最低位补 0。\n仅为固定布线，不是移位寄存器。', 414, 488, 412, 68)

    out_xor = p.xor(1090, 331, d=48)
    p.edge(shift, out_xor)
    p.text("{x[6:0], 1'b0} · 8 bit", 814, 313, 262, 29,
           size=16, align='center')
    result = p.tag('xtime(x) · 8 bit', 1260, 331, 242, 48)
    p.edge(out_xor, result)
    p.text('8 bit', 1081, 299, 66, 27, size=14,
           color=MUTED, align='center')

    zero = p.tag("8'h00 · 8 bit", 658, 583, 190, 44)
    poly = p.tag("8'h1b · 8 bit", 658, 663, 190, 44)
    mask_mux = p.mux('', 950, 565, 85, 160)
    p.text('0', 16, 26, 26, 26, size=18, parent=mask_mux)
    p.text('1', 16, 106, 26, 26, size=18, parent=mask_mux)
    p.edge(zero, mask_mux, tp=(0, .25))
    p.edge(poly, mask_mux, tp=(0, .75))
    p.edge(mask_mux, out_xor, tp=(.5, 1),
           via=[(1114, 645)])
    p.text('mask · 8 bit', 1052, 653, 150, 30, size=15, color=MUTED)

    select = p.tag('x[7] · 1 bit', 434, 766, 220, 38, control=True)
    p.edge(branch, select, sp=(.5, .5), via=[(295, 785)])
    p.edge(select, mask_mux, sp=(1, .5), tp=(.5, 1),
           via=[(992.5, 785)])
    p.text('select', 1005, 739, 84, 25, size=14, color=MUTED)
    p.note('MSB（最高位）决定是否需要模约减。', 354, 812, 594, 44)

    p.text('Conditional reduction（条件约减）', 1190, 501, 360, 54,
           size=19, bold=True)
    p.note('x[7] = 0：保留左移结果\nx[7] = 1：再 XOR 0x1b',
           1190, 568, 360, 75)
    p.note('AES 模多项式：\nm(t) = t⁸ + t⁴ + t³ + t + 1\n\n0x1b 对应 t⁴ + t³ + t + 1。',
           1190, 676, 362, 122)
    p.note("MUX（选择器）是 RTL 中 8'h1b & {8{x[7]}} 的等价示意表达；它不是额外的时序级。",
           68, 869, 1460, 48)
    return p
