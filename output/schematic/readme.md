# AES-128 schematic

本套图依据仓库主目录 `rtl/` 中的当前实现绘制。唯一图形源文件是 [aes128_schematic.drawio](aes128_schematic.drawio)，包含 6 个可编辑图页。PDF 与每页 PNG 均由官方 draw.io Desktop 31.3.2 从该文件导出，没有 SVG 或位图中间源。

| 页 | 内容 | RTL 来源 | PNG |
| --- | --- | --- | --- |
| 01 | 32-bit 共享 IO、输入寄存器、输出选择和 done 延迟 | `rtl/Aes128Iterative.v` | [01_top_level.png](01_top_level.png) |
| 02 | 核心连接、控制寄存器、唯一共享同步 ROM | `rtl/core/aes128_iterative_core.v`、`controller.v`、`sbox_rom.v` | [02_core.png](02_core.png) |
| 03 | 状态更新、ShiftRows、串行查表、单列复用 | `rtl/core/state_path.v`、`shift_rows.v`、`add_round_key.v` | [03_state_path.png](03_state_path.png) |
| 04 | RotWord、SubWord 捕获、Rcon 和轮密钥 XOR 链 | `rtl/core/key_schedule.v` | [04_key_schedule.png](04_key_schedule.png) |
| 05 | 单列 MixColumns 的四路 xtime 与 XOR 网络 | `rtl/core/mix_column.v` | [05_mix_column.png](05_mix_column.png) |
| 06 | xtime 的位移布线和条件模约减 | `rtl/core/mix_column.v` 中的 `function xtime` | [06_xtime.png](06_xtime.png) |

汇总：[aes128_schematic.pdf](aes128_schematic.pdf)。

## 图例与抽象

- 圆内十字为 XOR（异或）；梯形为 MUX（选择器）；绿色带时钟三角的框为真实寄存器，明确标注 bit 长度。
- 浅蓝表示数据运算或模块边界，浅褐表示控制或组合选择。颜色仅辅助分组，黑白时符号与文字仍可区分。
- 六边形标签为 tunnel（命名网络端点）；同名网络在相应模块作用域中相连。实心点表示连接，跳线弧表示交叉但不连接。
- 较粗线表示主要数据总线；部分读写用位切片或 byte/column lane 注明。按切片拆出/拼合的总线不表示将不同位短接。
- 寄存器默认 `posedge clk`、同步高有效 `rst`；wrapper 使用 `clock/reset`。共用时钟、复位、使能译码和保持选择适度省略。ROM 无复位输入。
- 图 03/04 的 S-box 标签引用图 02 的同一个实例，未增加 ROM。Q 同时广播，分别按 capture 写入；REQUEST/CAPTURE 是控制阶段划分，不代表 ROM 内有两拍流水。
- `state_temp_reg` 的 Byte write 是部分写入选择逻辑的抽象；未选字节/列保持。RTL 若同时置 `state_capture` 与 `mix_step`，后者覆盖对应列；正常 FSM 中二者互斥。
- ShiftRows 为固定连线，按列优先编号；其前置于 S-box 与逐字节 SubBytes 可交换。第 10 轮由控制器跳过 MixColumns，没有新增旁路器。
- xtime 框只封装组合 function 的绘图细节。图 06 的条件 MUX 等价于 RTL 的 `8'h1b & {8{x[7]}}`；没有新增寄存器、通用乘法器或进位加法器。
- 图 04 只存当前 `round_key` 与 `key_temp_reg`；Rcon 是组合常数选择。文字声明为 Verilog `reg` 的组合变量没有画作寄存器。

## 修改与复现

在 draw.io 中直接打开 `.drawio` 文件后修改。模块、寄存器、XOR、MUX、矩阵单元、文字和连线都是原生对象；模块内部对象按父子关系分组，数据连接线绑定端点。MUX 由分组原生轮廓线和文字构成，避免字体或外部图片依赖。字体为 `Noto Sans CJK SC`。

保存修改后，运行下列命令，使用官方应用重新导出所有格式：

```sh
python3 output/schematic/export_drawio.py
```

导出脚本默认使用本机 `/snap/drawio/current/app/drawio` 和 `xvfb-run`；可通过 `--application` 指定应用路径，已有显示环境可加 `--no-xvfb`。PDF 以 `--all-pages --crop` 导出；PNG 使用 1-based `--page-index`、`--scale 3.125`，白底约 5085 × 3210 像素。实际导出命令、应用版本及源/输出 SHA-256 记录在 `export_manifest.json`。

如需从本次审核确定的结构重新生成源文件，运行：

```sh
python3 output/schematic/build_schematic.py
python3 output/schematic/export_drawio.py
```

生成器会覆盖该目录的同名图形文件，也会覆盖对 drawio 的手工修改。手工修改后通常只运行导出脚本；需要重新生成时请先另存手工版本。生成器不自动解析未来 RTL 变更。

## 检查范围

逐项对照当前 RTL 的寄存器、位宽、实例数、共享关系、字节顺序与控制语义；检查原生 XML 的端点引用及未嵌入图片。导出 PDF 共 6 页，Creator 为 diagrams.net，字体嵌入且文字可提取。逐页检查实际导出的 PNG 及 PDF 渲染；另在官方编辑器中验证原生对象可编辑。

本次仅制作图形与脚本，未修改 RTL、测试或对话记录，也未运行 PPA。RTL 来源摘要见 `rtl_sources.sha256`。
