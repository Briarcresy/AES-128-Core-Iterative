# AES-128 RTL 宏观架构图

本组图依据当前 [`rtl/core/`](../../rtl/core/) 的全部 Verilog 模块及 [`xtime.vh`](../../rtl/core/includes/xtime.vh) 绘制，顶层为 [`aes128_iterative_core`](../../rtl/core/aes128_iterative_core.v)。图中标题、模块名、端口名、信号名和注释均使用英文；本文用中文解释 RTL 细节。源 RTL 未作修改。

## 图件

交付格式为原生可编辑 `.drawio` 文件，可在 draw.io / diagrams.net 中打开。模块框、文字标签与连接线均为原生 mxGraph 对象，支持分别选择和编辑。

| 架构图 | 原生可编辑文件 |
| --- | --- |
| Top-Level Architecture | [01_top_level.drawio](01_top_level.drawio) |
| AES Round Architecture | [02_aes_round.drawio](02_aes_round.drawio) |
| Key Expansion Architecture | [03_key_expansion.drawio](03_key_expansion.drawio) |
| Controller Overview | [04_controller.drawio](04_controller.drawio) |
| AES Transform Overview | [05_aes_transforms.drawio](05_aes_transforms.drawio) |

五图合订版：[aes128_rtl_architecture.drawio](aes128_rtl_architecture.drawio)，包含按上述标题命名的 5 个独立页面。文件未将整图作为图片嵌入。

在仓库根目录执行以下命令可重新生成 draw.io 文件：

```bash
python3 artifacts/architecture/export_drawio.py
```

生成脚本使用 Python 3 与 `pycairo` 测量字体；同目录的 SVG 是生成中间文件。`.drawio` 文件本身不依赖 Python，可直接打开编辑。脚本复现的是本次经人工 RTL 审阅确定的架构，不会自动解析后续 RTL 修改。

## 绘图前的 RTL 差异核对

用户给出的迭代式加密、10 个密钥扩展周期、10 个加密轮周期和末轮旁路 MixColumns 等主要描述与 RTL 一致。以下细节必须按现有代码解释：

1. **State Register 就是 `data_out`。** 顶层仅有这一组 128-bit 状态寄存器；没有额外的输入寄存器、输出寄存器或轮间流水寄存器。`data_out` 在处理期间直接显示当前状态，只有 `done=1` 时表示本次密文有效。
2. **IDLE 每个时钟都装载 `data_in`。** 装载不以 `start` 为使能条件。因此完成后的下一上升沿会用 `data_in` 覆盖密文，即使 `start=0`；输出并不保持到下一次加密完成。
3. **原始 `key` 没有锁存。** 第一个轮密钥生成与初始 AddRoundKey 都直接读取顶层 `key`。接口使用时应保持 `key` 从启动到第 10 个扩展周期完成时稳定。
4. **Round Counter 属于 `controller` 内部。** 图中将其展开以说明数据依赖。Round Index Generator 对应顶层的 `round_index = count + 1`，其 `+1 Incrementer` 是组合逻辑，不是新增寄存器或新增 RTL 模块。控制器内部还存在更新 `count` 的递增逻辑。
5. **`final_step` 仅判断 `count == 9`。** 它没有与 `phase == ROUND` 相与，因此在 EXPAND 最后一周期和完成后的 IDLE 期间也可能为 1；只有 ROUND 阶段才将旁路后的轮结果写回。
6. **`rst` 为高有效同步复位。** 它复位 State Register 以及控制器的 `phase`、`count`、`done`，不清零 Round Key Registers。轮密钥写进程也没有 `rst` 屏蔽：若复位上升沿之前处于 EXPAND，该沿仍可能写入一个轮密钥。

仓库原有 [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) 和 [`docs/RTL_INTERFACE.md`](../../docs/RTL_INTERFACE.md) 中的旧顶层名 `aes128_iterative`、`rst_n` 低有效异步复位、锁存原始密钥、`round_keys[0]`、额外 `input_reg`、密文持续保持等描述不符合当前 RTL，本组图不沿用这些内容。

## 1. Top-Level Architecture

依据：[aes128_iterative_core.v](../../rtl/core/aes128_iterative_core.v)、[controller.v](../../rtl/core/controller.v)。

顶层接口为 `clk`、`rst`、`start`、`key[127:0]`、`data_in[127:0]`、`data_out[127:0]`、`busy`、`done`。图中区分 State/Data Path、Round-Key Path 和 Control Path。

### 轮密钥路径

- Previous Key MUX：`count == 0` 时选择 `key`；`count > 0` 时选择 `round_keys[count]`。
- Round Index Generator：4-bit `round_index = count + 1`；有效扩展和加密阶段的索引为 1～10。
- Key Expansion：组合生成 `next_key`；在 `key_step=1` 的上升沿写入 `round_keys[round_index]`。
- Round Key Registers：真实声明为 `reg [127:0] round_keys[1:10]`，统一画作 **Round Key Registers (10 × 128-bit)**；不包含原始密钥寄存器。
- 两条索引读取分别提供 Previous Key MUX 的 `round_keys[count]` 和 AES Round 的 `round_keys[round_index]`。这些是寄存器数组的 RTL 访问，不额外假定物理双口 RAM。

密钥反馈环为：`Round Key Registers → Previous Key MUX → Key Expansion → Round Key Registers`。第一步的反馈源由外部 `key` 替代。

### 状态路径

State Register 的 RTL 名为 `data_out`，其组合下一值为 `data_next`。State Input MUX 的精确映射如下：

| `data_sel` | MUX 输入 | 触发条件 |
| --- | --- | --- |
| `2'd0` | `data_in` | `phase == IDLE` |
| `2'd1` | Initial AddRoundKey result：`data_out ^ key` | `phase == EXPAND && count == 9` |
| `2'd2` | AES Round result：`round_result` | `phase == ROUND` |
| `2'd3` | State hold/feedback：`data_out` | EXPAND 的其余周期 |

同步复位在 State Register 的时序进程中优先于上述 MUX 结果。初始 AddRoundKey 是顶层独立的 128-bit XOR 组合模块，与 AES Round 内部的 AddRoundKey 是两个实例。

状态反馈环为：`State Register → AES Round → State Input MUX → State Register`，在 ROUND 阶段执行 10 次。State Register 还分别向 Initial AddRoundKey 和 MUX 的保持输入提供反馈。输出端口直接连接 State Register，无额外密文捕获级。

## 2. AES Round Architecture

依据：[round.v](../../rtl/core/round.v)。

```text
state_in → SubBytes → ShiftRows → MixColumns → Final-Round MUX
                                                    ↓
round_key ────────────────────────────────────→ AddRoundKey → state_out
```

ShiftRows 输出另有一条旁路线，直接接 Final-Round MUX；该 MUX 的实际表达式是：

```verilog
before_key = final_round ? after_shift : after_mix;
```

- `final_round=0`：选择 `after_mix`，用于第 1～9 轮。
- `final_round=1`：选择 `after_shift`，用于第 10 轮。
- AddRoundKey 始终执行：`state_out = before_key ^ round_key`。
- `after_sub`、`after_shift`、`after_mix`、`before_key` 都是 128-bit 组合网络。

整个 `round` 模块无时钟、复位或内部寄存器。只有顶层 State Register 保存每轮结果，同一个 Round 组合电路跨 10 个时钟复用。末轮的选择器旁路 MixColumns 输出，不表示 RTL 存在该单元的时钟门控或电源门控。

## 3. Key Expansion Architecture

依据：[key_expansion.v](../../rtl/core/key_expansion.v)。

设旧密钥四个 32-bit 字分别为 `old_key[127:96]`、`old_key[95:64]`、`old_key[63:32]`、`old_key[31:0]`。末字经 RotWord、4 个并行 S-box 的 SubWord，再与轮常量异或：

```text
rotated = {old_key[23:0], old_key[31:24]}
temp = SubWord(rotated) XOR {rcon, 24'h0}
w0 = old_key[127:96] XOR temp
w1 = old_key[95:64] XOR w0
w2 = old_key[63:32] XOR w1
w3 = old_key[31:0] XOR w2
new_key = {w0, w1, w2, w3}
```

`round_index` 通过组合 `case` 选择 Rcon，索引 1～10 对应 `01, 02, 04, 08, 10, 20, 40, 80, 1b, 36`；默认值为 `00`。这些常量由 `localparam` 与 `xtime` 推导，没有 Rcon 时序寄存器。

`w0`、`w1`、`w2`、`w3`、`temp`、`rcon` 和输出 `new_key` 虽声明为 Verilog `reg`，但均在完整赋值的 `always @*` 中计算，代表组合逻辑而非寄存器。真正保存轮密钥的寄存器组在顶层。图中 `new_key` 是本模块端口名，其顶层连线名为 `next_key`。

## 4. Controller Overview

依据：[controller.v](../../rtl/core/controller.v)。

控制器包含 2-bit `phase` 寄存器、4-bit `count` 寄存器以及 1-bit `done` 寄存器，状态为 `IDLE`、`EXPAND`、`ROUND`。`busy = (phase != IDLE)`、`key_step = (phase == EXPAND)`、`final_step = (count == 9)` 为组合译码；`data_sel` 也为组合输出。注释掉的 `accept` 和 `round_step` 并非实际信号。

将 IDLE 中采样到 `start=1` 的上升沿记为 T0，表中状态变化与输出值均指该上升沿之后：

| 时刻 | 行为 | 状态与输出 |
| --- | --- | --- |
| T0 | `data_out ← data_in`；`count ← 0` | 进入 EXPAND，`busy=1` |
| T1～T9 | 写入 `round_keys[1]`～`round_keys[9]`；State 保持 | EXPAND，计数逐次递增 |
| T10 | 写入 `round_keys[10]`；同时执行 `data_out ← data_out ^ key`；`count ← 0` | 进入 ROUND |
| T11～T19 | 依次执行第 1～9 轮并写回 State | ROUND |
| T20 | 第 10 轮旁路 MixColumns 并写回密文 | 进入 IDLE，`done=1`、`busy=0`，`count` 保持为 9 |
| T21 | IDLE 装载当前 `data_in`，覆盖密文；`done ← 0` | 若 `start=1` 则接受下一块并进入 EXPAND，否则保持 IDLE |

因此启动到完成相隔 20 个周期；初始 AddRoundKey 与最后一次密钥扩展共用 T10，无额外初始处理周期。`busy=1` 时的 `start` 不被采纳；若 `start` 一直保持为 1，控制器将在完成后的下一个 IDLE 上升沿启动下一块。

`data_in` 只需在 T0 被采样时满足时序，此后忙期间可改变。由于没有原始密钥寄存器，`key` 应从 T0 保持到 T10 完成；它在 T1 生成第一个轮密钥，在 T10 再用于初始 AddRoundKey。下游应在 `done=1` 的有效窗口采集密文。

## 5. AES Transform Overview

依据：[sub_bytes.v](../../rtl/core/sub_bytes.v)、[sbox_byte.v](../../rtl/core/sbox_byte.v)、[shift_rows.v](../../rtl/core/shift_rows.v)、[mix_columns.v](../../rtl/core/mix_columns.v)、[add_round_key.v](../../rtl/core/add_round_key.v)。

- **SubBytes / S-box：** `sub_bytes` 实例化 16 个并行 `sbox_byte`。每个 S-box 是 256 × 8-bit 异步 ROM 查表，输入字节直接作地址，没有输出寄存器。`key_expansion` 另有 4 个并行实例，因此全核 RTL 共 20 个 S-box 实例；没有两条数据路径之间的 S-box 共享 MUX。ROM 数据由 `$readmemh("mem/sbox.mem", sbox_rom)` 加载，源文件为 [`mem/sbox.mem`](../../mem/sbox.mem)；综合后是否成为物理 ROM 取决于实现流程。
- **ShiftRows：** 采用固定字节连线。状态位置 `(row, col)` 的字节下标为 `4*col + row`，对应 `state[127-8*(4*col+row) -: 8]`；第一个字节为 `[127:120]`。输出 `(row, col)` 从输入 `(row, (col+row)%4)` 取字节，等价于第 0、1、2、3 行分别循环左移 0、1、2、3 个字节。
- **MixColumns：** 4 列并行组合变换，每列 32-bit，独立应用 AES 正向列混合；系数为 `02/03/01/01` 的循环矩阵。`xtime` 通过移位与条件 XOR `8'h1b` 实现有限域乘 2；乘 3 为 `xtime(x) ^ x`。图件保留列变换功能框，不展开门级 XOR 网络。
- **AddRoundKey：** 128-bit 按位 XOR。顶层初始异或使用原始 `key`，轮内异或使用 `round_keys[round_index]`。

以上变换均为组合逻辑；图中的分组框用于说明 RTL 功能，不表示额外的流水边界或时序单元。

## 验证范围

已使用本机 draw.io 31.3.2 打开并导出五页 `.drawio` 合集，逐页检查模块边界、箭头端点、标签层级、末轮旁路及两条主要反馈路径。五个独立文件与合集对应页面使用相同的原生图元；XML 中没有嵌入图片。

本次核对所用 RTL 和 ROM 的 SHA-256 摘要保存在 [rtl_sources.sha256](rtl_sources.sha256)。在仓库根目录运行 `sha256sum -c artifacts/architecture/rtl_sources.sha256` 可检查后续源文件是否发生变化。

本次使用 Icarus Verilog 的 `-g2005`，直接编译当前 `rtl/core/*.v`，运行既有 [AES testbench](../../tests/tb_aes128_iterative.v) 和 [S-box testbench](../../tests/tb_sbox_byte.v)：6 组加密向量通过，20-cycle latency、`busy` 和单周期 `done` 检查通过；S-box 全部 256 个地址的查表一致性检查通过。S-box 测试的期望值也读取同一 ROM 文件，因此该项验证的是地址到文件内容的映射，不是独立推导 S-box 数学定义的证明。

图件依据功能级 RTL，不对综合后的门数、物理存储映射、面积或时序作推断。
