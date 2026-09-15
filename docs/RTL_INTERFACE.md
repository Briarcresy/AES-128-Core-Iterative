# AES-128 加密 RTL 接口

顶层模块为 `aes128_iterative`，内部结构见 [ARCHITECTURE.md](ARCHITECTURE.md)。

| 信号 | 方向 | 含义 |
| --- | --- | --- |
| `clk` | 输入 | 上升沿时钟 |
| `rst_n` | 输入 | 低有效异步复位 |
| `start` | 输入 | `busy=0` 时置 1，启动一块数据的加密 |
| `key[127:0]` | 输入 | 128-bit 密钥 |
| `data_in[127:0]` | 输入 | 128-bit 明文 |
| `data_out[127:0]` | 输出 | 128-bit 密文，保持到下次完成 |
| `busy` | 输出 | 正在执行密钥扩展或加密轮 |
| `done` | 输出 | 密文有效脉冲，持续一个时钟 |

输入在 `start && !busy` 的上升沿锁存，随后可以改变。接收输入后经过 10 个密钥扩展时钟和 10 个加密轮时钟，`data_out` 有效且 `done=1`。字节 0 位于 `[127:120]`。

运行仿真：

```bash
iverilog -g2005 -s tb_aes128_iterative -o /tmp/aes128_tb.vvp \
  -f files.f tests/tb_aes128_iterative.v
vvp -N /tmp/aes128_tb.vvp
```
