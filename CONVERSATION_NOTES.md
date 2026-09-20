# 使用一块 ICS55 ROM 实现面积优先的 AES-128 S-box

## 目标与已确认信息

- 项目目标是仅加密的 AES-128，优先减小面积，性能和功耗次要。
- 当前 `sub_bytes` 并行使用16个S-box，`key_expansion` 并行使用4个S-box，共20个组合S-box。
- 当前还保存10个128-bit轮密钥，即1280 bit的 `round_keys` 寄存器阵列。
- 已下载 `ics55_ecos_rom_256x8_m8_b1`：256 words × 8 bits、单Bank、单读端口同步ROM，宏面积估计约1761 um^2。
- 文件包位于 `ip/ics55_ecos_rom_256x8_m8_b1/`，位置合适；厂商IP不要搬进 `rtl/core/`。

## ROM接口和工作方式

模块名为 `ics55_ecos_rom_256x8_m8_b1`，端口如下：

```text
A[7:0]   读取地址
CLK      上升沿采样地址
CEB      片选，低电平有效
MARE     Margin（读延迟调节）功能使能
MAR[3:0] Margin控制值
Q[7:0]   读取数据
```

正常工作采用默认Margin设置：

```verilog
.MARE (1'b0),
.MAR  (4'b0000)
```

它是同步ROM：上升沿前保持 `A` 和 `CEB=0`，上升沿采样地址，上升沿后 `Q` 才变成读取结果。因此不能直接替换目前异步组合查表形式的 `sbox_byte`，控制器必须加入请求和接收步骤。

## 文件包用途

```text
ip/ics55_ecos_rom_256x8_m8_b1/
├── doc/*.ds          数据手册
├── verilog/*_core.v  简单功能仿真模型
├── verilog/*.v       完整时序仿真模型
├── verilog/*_stub.v  综合时使用的黑盒接口
├── verilog/*.romcode ROM内容，256行二进制数据
├── lib/*.lib         综合和STA时序/功耗模型
├── lef/*.lef         布局布线所需的物理抽象
└── power/*.cpf       电源意图描述
```

下载包没有GDS和CDL/SPICE。平台说明流片时根据订单备注和 `.romcode` 生成匹配版图，因此提交前必须确认GDS合并、LVS模型和ROM内容的交付方式。

## 推荐的新架构

一块ROM由状态变换和密钥扩展分时复用：

```text
state_reg ---\
              >-- ROM address MUX --> 256x8 S-box ROM --> state_temp_reg
key_reg -----/                                      \--> key_temp_reg
```

同时完成两项面积优化：

1. 删除20个并行组合S-box，只保留一个ROM实例。
2. 删除10组轮密钥寄存器，每轮由当前 `key_reg` 即时生成下一轮密钥（on-the-fly key expansion）。

主要寄存器和计数器建议为：

```text
state_reg[127:0]       当前AES状态
state_temp_reg[127:0]  接收SubBytes和ShiftRows结果
key_reg[127:0]         当前轮密钥
key_temp_reg[31:0]     保存4次SubWord读取结果
byte_index[4:0]        状态字节编号0～15
key_byte_index[1:0]    密钥字节编号0～3
column_index[1:0]      MixColumns列编号0～3
round_index[3:0]       AES轮编号1～10
```

## 推荐控制流程

第一版优先采用容易验证的两阶段ROM读取，每个字节使用两个状态：

```text
ROM_REQUEST：地址和CEB在整个周期保持稳定
ROM_CAPTURE：Q已经有效，在下一个上升沿保存Q
```

性能不是目标，暂时不做连续地址流水化。完整流程为：

```text
IDLE
  等待start

INITIAL_ADD_KEY
  state_reg <= data_in XOR key
  key_reg <= key
  round_index <= 1

KEY_SBOX_REQUEST / KEY_SBOX_CAPTURE
  依次查询RotWord的4个字节，结果写入key_temp_reg

KEY_UPDATE
  加Rcon并计算下一轮密钥，更新key_reg

STATE_SBOX_REQUEST / STATE_SBOX_CAPTURE
  依次查询16个状态字节
  ROM结果直接按ShiftRows之后的位置写入state_temp_reg

MIX_COLUMN
  第1～9轮依次处理4列；第10轮跳过

ADD_ROUND_KEY
  state_reg <= 轮变换结果 XOR key_reg

ROUND_CHECK
  轮号小于10则进入下一轮；等于10则锁存data_out并产生done脉冲

IDLE
```

简单两阶段方案每轮进行20次S-box查询，至少约40个ROM周期。完整加密预计约450～500周期；10 MHz下约45～50 us，属于用吞吐率交换面积的预期结果。

## 合并SubBytes与ShiftRows

AES状态保持列优先（column-major）布局：

```text
byte index = 4 * column + row
```

按照ShiftRows的目标位置遍历：

```text
目标行 row        = byte_index % 4
目标列 column     = byte_index / 4
源列 source_col   = (column + row) % 4
源字节 source_idx = 4 * source_col + row
```

把 `state_reg` 的 `source_idx` 字节送入ROM，把ROM输出直接写入 `state_temp_reg` 的 `byte_index` 字节。建议在Verilog-2005中用 `case (byte_index)` 明确列出16组映射，便于初学者核查，也避免在RTL中出现运行时乘除和取模。

必须保留单独的 `state_temp_reg`；若直接写回 `state_reg`，ShiftRows可能提前覆盖尚未读取的源字节。

## 密钥扩展复用ROM

当前密钥分为：

```text
w0 = key_reg[127:96]
w1 = key_reg[95:64]
w2 = key_reg[63:32]
w3 = key_reg[31:0]
```

RotWord(w3)的4个ROM地址依次是：

```text
w3[23:16]
w3[15:8]
w3[7:0]
w3[31:24]
```

4次读取结果组成 `key_temp_reg = SubWord(RotWord(w3))`，然后计算：

```text
temp   = key_temp_reg XOR {Rcon, 24'h000000}
new_w0 = w0 XOR temp
new_w1 = w1 XOR new_w0
new_w2 = w2 XOR new_w1
new_w3 = w3 XOR new_w2
key_reg <= {new_w0, new_w1, new_w2, new_w3}
```

Rcon继续用当前 `case (round_index)`，不需要另一块ROM。

## MixColumns面积优化

建议把128-bit四列并行的 `mix_columns` 改成一个复用的32-bit模块：

```text
mix_column
  input  [31:0] column_in
  output [31:0] column_out
```

用 `column_index` 在4个周期中依次处理四列。第一版让一个 `mix_column` 在一个周期完成一列；如果综合后仍占较大面积，再改成共享一个 `xtime` 的更多周期结构。第10轮必须旁路MixColumns。

## 推荐RTL划分

```text
rtl/core/
├── aes128_iterative_core.v  寄存器、数据通路和模块连接
├── controller.v             多周期状态机和计数器
├── sbox_rom_adapter.v       ROM统一接口与仿真/综合切换
├── key_expansion_serial.v   4次ROM查询及轮密钥更新（可选独立模块）
├── mix_column.v             一次处理一列
├── add_round_key.v          128-bit XOR
└── includes/xtime.vh
```

旧的 `sbox_byte.v`、`sub_bytes.v`、`round.v` 和 `mix_columns.v` 在新架构全部验证完成前先保留，但不要让新旧架构同时接入顶层。验证完成后再从 `files.f` 移除并删除不用的模块。

## ROM适配模块原则

AES内部只使用简单接口：

```verilog
module sbox_rom_adapter (
    input  wire       clk,
    input  wire       enable,
    input  wire [7:0] address,
    output wire [7:0] data
);
```

适配模块内部连接厂商宏：

```verilog
ics55_ecos_rom_256x8_m8_b1 u_rom (
    .A    (address),
    .CEB  (~enable),
    .CLK  (clk),
    .MARE (1'b0),
    .MAR  (4'b0000),
    .Q    (data)
);
```

整个AES层次中只能出现一个 `u_rom`。由地址MUX选择当前查询来自状态数据还是密钥数据。

厂商模型默认 `codefile` 为 `verilog/ics55_ecos_rom_256x8_m8_b1.romcode`，假定从IP目录启动仿真，而本项目通常从仓库根目录启动。稳妥方案是：RTL仿真使用自己的简化同步ROM模型并读取完整项目相对路径；综合时通过编译宏切换到厂商宏实例和stub。不要直接修改厂商原始文件。

## 生成和检查 `.romcode`

`mem/sbox.mem` 是256行十六进制，ROM模型用 `$readmemb`，所以 `.romcode` 必须是256行8位二进制：

```text
63 -> 01100011
7c -> 01111100
77 -> 01110111
...
16 -> 00010110
```

建议在 `scripts/` 保存转换脚本，从 `mem/sbox.mem` 可重复生成 `.romcode`。生成后检查：

```text
总行数       = 256
每行字符数   = 8
地址00的数据 = 01100011
地址53的数据 = 11101101
地址FF的数据 = 00010110
```

## 分阶段实施和验收

### 阶段1：单独验证ROM

1. 生成非零 `.romcode`。
2. 编写 `sbox_rom_adapter.v`。
3. 新建 `tests/tb_sbox_rom.v`。
4. 遍历全部256个地址，与 `mem/sbox.mem` 比较。

验收：256个地址全部匹配；正确处理同步延迟；`CEB=1` 时不发起读取；没有X或文件路径错误。

### 阶段2：串行密钥扩展

用同一ROM依次完成4次SubWord读取，并逐轮更新 `key_reg`。先单独测试。FIPS-197关键检查值：

```text
Cipher Key   = 000102030405060708090a0b0c0d0e0f
Round 1 Key  = d6aa74fdd2af72fadaa678f1d6ab76fe
Round 10 Key = 13111d7fe3944a17f307a78b4d2b30c5
```

### 阶段3：串行SubBytes并合并ShiftRows

顺序查询16个源字节，按ShiftRows目标位置写入 `state_temp_reg`。与Python golden model或现有并行RTL的中间结果比较。

### 阶段4：单列MixColumns

编写32-bit `mix_column`，用4周期处理四列。随机输入下应与现有128-bit `mix_columns.v` 完全一致，并验证第10轮旁路。

### 阶段5：完整AES核

替换顶层控制器和数据通路，删除 `round_keys[1:10]`，确认只例化一块ROM。保持外部 `start/busy/done/data_in/key/data_out` 接口不变，避免影响wrapper。

验收：`start` 只在空闲时接受；`busy` 覆盖整个运算；`done` 只持续一个周期；`done` 时 `data_out` 有效；全部AES测试向量通过。

### 阶段6：综合、STA和面积比较

1. 综合时使用 `*_stub.v` 声明黑盒。
2. 读取相应工艺角的ROM `.lib`。
3. 确保工具保留ROM实例，不展开或删除。
4. 分别报告标准单元面积和ROM宏面积，再相加比较总面积。

工艺角参考：

```text
典型：tt1p2v25cctyp
慢角建立时间：ss1p08v125ccmax
快角保持时间：ff1p32vm40ccmin（最终以平台要求为准）
```

检查综合网表：ROM实例数量为1；没有20份S-box逻辑；没有 `round_keys[1:10]` 阵列。只有功能测试通过后，PPA结果才有效。

## 后端和流片检查

- PnR加载ROM LEF，并把它作为macro摆放。
- 给宏保留halo和布线空间，正确连接电源、地和时钟树。
- STA加载对应corner的ROM Liberty。
- 确认共享流片模板允许该ROM硬宏。

订单备注建议写明：

```text
ROM macro: ics55_ecos_rom_256x8_m8_b1
Organization: 256 words x 8 bits
Content: AES forward S-box
Please generate the physical ROM content exactly matching the submitted
ics55_ecos_rom_256x8_m8_b1.romcode file.
Address 0x00 must read 0x63, address 0x53 must read 0xED,
and address 0xFF must read 0x16.
```

流片前获得平台确认：`.romcode` 上传位置；地址0对应文件第一行还是最后一行；内容是否同步进入GDS和LVS网表；ROM电源连接方法；最终GDS/CDL由平台自动合并还是用户处理。

## 推荐执行顺序

```text
1. 生成并验证romcode
2. 验证单块同步ROM
3. 验证串行key expansion
4. 验证串行SubBytes + ShiftRows
5. 验证单列MixColumns
6. 连接完整AES状态机
7. 跑全部RTL测试
8. 接入ROM Liberty和stub进行综合/STA
9. 比较新旧面积
10. 完成后端和流片内容确认
```

每完成一步都保留可运行测试。某一步失败时，只排查刚增加的模块，不要同时推进多个阶段。
