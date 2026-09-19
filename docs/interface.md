# AES-128 RTL 接口

设计分为两层：

- `Aes128Iterative`：连接 MPC-Frame 的 66-bit IO Wrapper（封装层）。
- `aes128_iterative_core`：执行 AES-128 单块加密的迭代式核心。

## FPGA 提供共同测试时钟

硅后测试采用 FPGA 提供测试时钟的同步方案：

```text
FPGA clock output ──> FrameTop.clock ──> Aes128Iterative.clock
                                      └─> aes128_iterative_core.clk
```

FPGA 测试控制器和 ASIC 必须使用同一个测试时钟。不要用 FPGA 板载时钟驱动测试
控制状态机、同时又让 ASIC 使用另一个无关的板载振荡器进行本接口通信。

推荐边沿约定：

- FPGA 在 `clock` 下降沿更新送往 ASIC 的数据和控制信号。
- ASIC Wrapper 在 `clock` 上升沿采样写入和启动信号。
- FPGA 在 `clock` 上升沿之后采样 ASIC 的 `busy`、`done` 和读数据。
- FPGA 输出必须在下一个上升沿前满足 ASIC 输入的建立时间和保持时间。

初次硅后测试应从低频开始，例如 100 kHz 或 1 MHz，再逐步提高频率。FPGA、ASIC
测试板和板载振荡器不得同时驱动同一个时钟网络。

## Wrapper IO 映射

| Wrapper IO | 方向 | 含义 |
| --- | --- | --- |
| `io_[31:0]` | 双向 | 32-bit 数据总线 |
| `io_in[33:32]` | 输入 | `word_index` |
| `io_in[34]` | 输入 | `input_select`：0=明文，1=密钥 |
| `io_in[35]` | 输入 | `write_enable` |
| `io_in[36]` | 输入 | `start` |
| `io_in[37]` | 输入 | `read_enable` |
| `io_out[38]` | 输出 | `busy` |
| `io_out[39]` | 输出 | `done` |
| `io_[65:40]` | 未使用 | 输出使能保持0 |

字序固定为：

| `word_index` | 128-bit 字段 |
| --- | --- |
| `2'd0` | `[127:96]` |
| `2'd1` | `[95:64]` |
| `2'd2` | `[63:32]` |
| `2'd3` | `[31:0]` |

MPC-Frame 的物理对应关系为：

```text
Wrapper io_*[n] <-> FrameTop user_io[n + 7]
```

`user_io[6:0]` 在复位期间用于选择 Design ID，不属于 Wrapper 的 66-bit payload。

## 复位

`reset` 为高有效同步复位。FPGA应在提供稳定测试时钟后拉高 `reset`，保持至少20个
上升沿，再在下降沿将其拉低。复位期间 FPGA 还应按照 MPC-Frame 协议保持正确的
Design ID。

## 写入密钥或明文

每个32-bit 字的写入过程为：

1. FPGA 在下降沿设置 `io_in[31:0]`、`word_index` 和 `input_select`。
2. 同时将 `write_enable` 置1。
3. ASIC 在下一个上升沿写入对应的32-bit 寄存器。
4. FPGA 在随后一个下降沿将 `write_enable` 清零。

`busy=1` 时 Wrapper 不接受写入。FPGA不得在同一个上升沿同时写最后一个输入字并
启动加密；最后一次写入完成后至少等待一个下降沿，再发送 `start`。

## 启动加密

FPGA 在下降沿将 `start` 置1，保持到下一个下降沿后清零，使 ASIC 只在一个上升沿
看到有效启动请求。启动前必须写完4个密钥字和4个明文字。

启动后应先观察 `busy=1`，再等待 `done=1`。不要在 FPGA RTL 中仅依赖固定周期数。
当前 `done` 是一个测试时钟周期宽的同步脉冲，FPGA状态机必须在每个上升沿采样它。
当前单ROM串行核心从接受 `start` 到产生 `done` 需要456个时钟周期。这个固定值只用于
RTL验证；FPGA测试控制器仍应以 `done` 为完成条件，并设置大于456周期的超时保护。

## 读取密文与总线换向

读取前必须避免 FPGA 和 ASIC 同时驱动 `io[31:0]`：

1. FPGA 在下降沿关闭自己的32-bit 数据总线输出使能。
2. 保持 FPGA 数据总线为高阻至少半个测试时钟周期。
3. FPGA设置 `word_index`，再将 `read_enable` 置1。
4. `read_enable=1` 时 ASIC 驱动 `io_out[31:0]`，并令 `io_oe[31:0]=1`。
5. FPGA在随后的上升沿之后采样32-bit 密文。
6. FPGA在下降沿将 `read_enable` 清零，ASIC随即释放数据总线。
7. FPGA确认 ASIC 已释放后，才能重新驱动该数据总线。

## AES Core 接口

| 信号 | 方向 | 含义 |
| --- | --- | --- |
| `clk` | 输入 | 上升沿测试时钟 |
| `rst` | 输入 | 高有效同步复位 |
| `start` | 输入 | 空闲时保持一个周期，启动单块加密 |
| `key[127:0]` | 输入 | 128-bit 密钥 |
| `data_in[127:0]` | 输入 | 128-bit 明文 |
| `data_out[127:0]` | 输出 | 直接连接内部 `state_reg`；仅在 `done=1` 时作为最终密文使用 |
| `busy` | 输出 | 正在进行密钥扩展或轮运算 |
| `done` | 输出 | 核心完成脉冲 |

Wrapper 会将核心结果锁存到 `ciphertext_reg`，再通过32-bit 读出 MUX 分4次输出。
核心运算期间 `data_out` 会随轮状态变化，不保证保持上一块密文；Wrapper仍在完成时锁存密文，因此其读出接口不受影响。

## 验证

运行全部测试：

```bash
make test
```

也可以分别运行：

```bash
make test-rom
make test-mix
make test-core
make test-wrapper
```
