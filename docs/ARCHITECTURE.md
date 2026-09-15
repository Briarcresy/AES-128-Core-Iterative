# AES-128 迭代式加密核架构

当前 RTL 只实现 AES-128 单块加密，使用 Verilog-2005。顶层模块是 `aes128_iterative`。

## 模块与数据路径

```text
 start ──► controller ──► accept / key_step / round_step / final_step
                │                    │
                └──────────────► round_index

 key ──► round_keys[0..10] ◄── key_expansion ◄── 上一个轮密钥
                    │
                    └──► 当前轮密钥 ───────────────────────────┐
                                                              │
 data_in ──► input_reg ──► 初始 AddRoundKey ──► state_reg ──► round ──► state_reg
                                                              │
                                                   最后一轮 ──└──► data_out
```

| 模块 | RTL 文件 | 职责 |
| --- | --- | --- |
| `aes128_iterative` | `rtl/aes128_iterative.v` | 顶层接口、状态寄存器、轮密钥寄存器及连线 |
| `controller` | `rtl/controller.v` | `IDLE → EXPAND → ROUND` 状态机和 0～9 计数器 |
| `key_expansion` | `rtl/key_expansion.v` | 每时钟生成一个新轮密钥 |
| `round` | `rtl/round.v` | 每时钟执行一轮加密，最后一轮旁路 MixColumns |
| `sub_bytes` | `rtl/sub_bytes.v` | 16 个字节并行 S-box 替换 |
| `sbox_byte` | `rtl/sbox_byte.v` | 从 256×8 的 `rtl/sbox.mem` 查表 |
| `shift_rows` | `rtl/shift_rows.v` | 按 AES 规则移动四行字节 |
| `mix_columns` | `rtl/mix_columns.v` | 对四列分别执行有限域运算 |
| `add_round_key` | `rtl/add_round_key.v` | 状态与轮密钥逐位异或 |

`round` 内的数据顺序是：

```text
state → SubBytes → ShiftRows → [MixColumns] → AddRoundKey → 下一轮 state
```

方括号中的 MixColumns 在第 10 轮由 `final_step` 旁路。初始 AddRoundKey 在顶层完成，不经过 `round` 模块。同一套 `round` 组合逻辑在 10 个轮周期中重复使用。

## 时序

把接受 `start` 的时钟上升沿记为 `T0`：

| 时刻 | 阶段 | 动作 |
| --- | --- | --- |
| `T0` | `IDLE → EXPAND` | 锁存 `key` 和 `data_in`，`busy` 拉高 |
| `T1`～`T10` | `EXPAND` | 依次生成并存储 `round_keys[1]`～`round_keys[10]` |
| `T10` | `EXPAND → ROUND` | 明文与 `round_keys[0]` 异或，写入 `state_reg` |
| `T11`～`T20` | `ROUND` | 逐轮使用 `round_keys[1]`～`round_keys[10]` |
| `T20` | `ROUND → IDLE` | 输出密文，`done` 拉高一个时钟，`busy` 拉低 |

从接收输入到输出有效共 20 个处理时钟。`busy=1` 时忽略新的 `start`；`data_out` 保持到下次加密完成。

## 字节排列与 ROM

输入的最左侧字节位于 `[127:120]`。AES 状态按列优先存储，矩阵位置 `(row, col)` 的字节下标是 `4*col + row`。

`sbox_byte` 通过 `$readmemh` 加载 `rtl/sbox.mem`，输入字节作为 ROM 地址，异步读出替换值。`sub_bytes` 为状态实例化 16 个 S-box，`key_expansion` 为 `SubWord` 实例化 4 个。仿真和综合请从仓库根目录运行，以便找到 ROM 数据文件；是否映射为物理 ROM 取决于目标工艺和综合流程。

## 验证

```bash
iverilog -g2005 -s tb_aes128_iterative -o /tmp/aes128_tb.vvp \
  -f files.f tests/tb_aes128_iterative.v
vvp -N /tmp/aes128_tb.vvp

iverilog -g2005 -s tb_sbox_byte -o /tmp/sbox_tb.vvp \
  rtl/sbox_byte.v tests/tb_sbox_byte.v
vvp -N /tmp/sbox_tb.vvp
```

这只是功能级 RTL；目标工艺的面积、时序、功耗和侧信道特性尚未验证。
