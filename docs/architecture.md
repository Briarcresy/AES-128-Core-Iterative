# AES-128 单ROM串行架构

## 总体结构

本项目实现仅加密的 AES-128，采用 Verilog-2005。外部顶层为
`Aes128Iterative`，加密核心为 `aes128_iterative_core`。

为了减小面积，状态变换和密钥扩展共享一块 256×8 bit 同步ROM：

```text
key / plaintext
       |
       v
+------------------------+
| aes128_iterative_core  |
|                        |
| state_reg    key_reg   |
|     \          /       |
|      ROM address MUX   |
|             |          |
|             v          |
|       256x8 S-box ROM  |
|             |          |
|      +------+-------+  |
|      v              v  |
| state_temp      key_temp|
|      |              |  |
| mix_column    key update|
|      \              /  |
|        AddRoundKey     |
+------------------------+
       |
       v
   ciphertext
```

设计中只有一个ROM实例。旧架构的20个并行S-box和10组预存轮密钥均已移除。

完整的控制状态跳转见 [控制流程图](control_flow.svg)。图中的菱形表示转移条件，不是额外的时钟状态。

## 模块

| 模块 | 作用 |
|---|---|
| `Aes128Iterative` | 32-bit共享IO wrapper |
| `aes128_iterative_core` | 连接控制器、密钥通路、状态通路和共享ROM；选择ROM地址 |
| `controller` | 多周期控制状态机和计数器 |
| `key_schedule` | 保存当前轮密钥，收集4次S-box输出并生成下一轮密钥 |
| `state_path` | 保存AES状态，完成SubBytes/ShiftRows、MixColumns和AddRoundKey |
| `shift_rows` | 16条固定字节连线，显式表示ShiftRows的行移位，不含寄存器 |
| `add_round_key` | 128位逐位异或；用于初始加轮密钥和每轮末尾 |
| `sbox_rom` | 直接例化ICS55 ROM IP，连接地址、时钟和低有效片选 |
| `mix_column` | `state_path` 内部复用的32-bit单列MixColumns逻辑 |
| `ics55_ecos_rom_256x8_m8_b1` | 256×8同步S-box硬宏 |

厂商IP保存在 `ip/ics55_ecos_rom_256x8_m8_b1/`，不放入 `rtl/core/`。
`key_schedule` 和 `state_path` 共用一块ROM：两者分别给出地址，顶层根据控制器状态选择其中一路。
寄存器输入按“保持、装载输入、装载轮结果”组织为MUX，选择信号由 `controller` 输出；
`key_schedule` 和 `state_path` 只根据这些信号选数据，不实现状态机。
此次拆分和RTL改写不改变控制状态、寄存器更新时机或加密周期数。

## 每轮执行过程

```text
4次密钥S-box读取
        |
        v
生成下一轮key_reg
        |
        v
16次状态S-box读取，同时完成ShiftRows
        |
        v
4次复用mix_column（第10轮跳过）
        |
        v
AddRoundKey
```

每次ROM查询使用两个控制周期：`REQUEST` 送出地址，`CAPTURE` 保存输出。
第1～9轮各使用46周期，第10轮使用42周期。从接受 `start` 到 `done` 共456周期。

## 状态矩阵

AES状态按列优先（column-major）保存，最左侧字节为 `[127:120]`：

```text
byte_index = 4 * column + row
```

`shift_rows` 将 `state_reg` 的16个字节按固定连线排列。状态S-box查询按其输出位置遍历，
ROM输出直接写入 `state_temp_reg` 的对应位置。这个模块只是连线，不增加寄存器或时钟周期。

## 密钥扩展

核心只保存当前 `key_reg`，不保存全部10个轮密钥。每轮依次把 `w3` 的RotWord四个字节
送入共享ROM，形成SubWord，然后与Rcon和 `w0`～`w3` 异或得到下一轮密钥。

## ROM模型

- RTL仿真：`sbox_rom` 直接例化ROM IP，编译厂商提供的 `*_core.v` 功能模型读取 `.romcode`。
- 综合：同一个 `sbox_rom` 实例使用厂商 `*_stub.v` 声明硬宏接口。
- STA：同时读取标准单元Liberty和ROM Liberty。

ROM内容由 `scripts/generate_romcode.py` 从 `mem/sbox.mem` 生成。

## 验证

运行全部测试：

```sh
make test
```

分别测试：

```sh
make test-rom
make test-mix
make test-core
make test-wrapper
```

综合、STA和PPA摘要：

```sh
make ppa
```
