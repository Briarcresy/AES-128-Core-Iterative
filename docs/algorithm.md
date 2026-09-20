# AES-128 加密算法流程

本文说明本项目需要用到的 AES-128 加密算法。重点是算法本身、字节排列和各步骤的输入输出，硬件的多周期实现方式见 [ARCHITECTURE.md](ARCHITECTURE.md)。

## 1. AES-128 的基本参数

AES（Advanced Encryption Standard，高级加密标准）是分组密码。AES-128 的参数为：

| 参数 | 数值 |
|---|---:|
| 明文分组长度 | 128 bit，即16 byte |
| 密文分组长度 | 128 bit，即16 byte |
| 密钥长度 | 128 bit，即16 byte |
| 状态矩阵 | 4行×4列，每项8 bit |
| 加密轮数 | 10轮 |
| 轮密钥数量 | 11个，每个128 bit |

AES-128只加密一个128-bit分组。ECB、CBC、CTR和GCM等工作模式不属于AES基本轮函数，本项目也没有实现这些模式。

## 2. 完整加密流程

AES-128加密可以概括为：

```text
128-bit Cipher Key
        |
        v
   Key Expansion
        |
        +--> RoundKey[0] ... RoundKey[10]

128-bit Plaintext
        |
        v
AddRoundKey(RoundKey[0])       初始轮密钥加
        |
        v
Round 1～9:
    SubBytes
    ShiftRows
    MixColumns
    AddRoundKey
        |
        v
Round 10:
    SubBytes
    ShiftRows
    AddRoundKey                 最后一轮没有MixColumns
        |
        v
128-bit Ciphertext
```

用伪代码表示：

```text
round_key[0..10] = KeyExpansion(key)

state = plaintext XOR round_key[0]

for round = 1 to 9:
    state = SubBytes(state)
    state = ShiftRows(state)
    state = MixColumns(state)
    state = state XOR round_key[round]

state = SubBytes(state)
state = ShiftRows(state)
state = state XOR round_key[10]

ciphertext = state
```

顺序不能交换。特别要注意：第10轮没有 `MixColumns`。

## 3. 状态矩阵与字节顺序

AES把16个输入字节放入一个4×4状态矩阵（State）。矩阵采用列优先（column-major）排列，而不是通常软件中常见的行优先排列。

设输入字节依次为：

```text
b0 b1 b2 b3 b4 b5 b6 b7 b8 b9 b10 b11 b12 b13 b14 b15
```

对应状态矩阵为：

```text
| b0  b4  b8  b12 |
| b1  b5  b9  b13 |
| b2  b6  b10 b14 |
| b3  b7  b11 b15 |
```

矩阵位置与线性字节编号的关系是：

```text
byte_index = 4 * column + row
```

本项目把最左侧字节放在128-bit向量的最高位：

```text
b0  = state[127:120]
b1  = state[119:112]
...
b15 = state[7:0]
```

例如明文：

```text
00112233445566778899aabbccddeeff
```

其状态矩阵为：

```text
| 00 44 88 cc |
| 11 55 99 dd |
| 22 66 aa ee |
| 33 77 bb ff |
```

矩阵只是帮助理解的表示方式。RTL端口仍然是一个连续的128-bit向量。

## 4. AddRoundKey：轮密钥加

`AddRoundKey` 把128-bit状态与当前128-bit轮密钥逐位异或（XOR）：

```text
state_out = state_in XOR round_key
```

对每个字节也可以写成：

```text
state_out[i] = state_in[i] XOR round_key[i]
```

异或是其自身的逆运算，但本项目只实现加密，不实现解密。

## 5. SubBytes：字节替换

`SubBytes` 使用固定的 AES S-box，把状态中的每个字节独立替换为另一个字节：

```text
output_byte = SBOX[input_byte]
```

输入字节本身就是查找表地址。例如：

```text
SBOX[00] = 63
SBOX[53] = ed
SBOX[ff] = 16
```

完整S-box包含256项，每项8 bit，因此可以存入一块 `256 × 8 bit` ROM。

### 5.1 S-box的数学来源

AES S-box不是随意排列的常数表，其构造分为两步：

1. 在有限域 `GF(2^8)` 中求输入字节的乘法逆元，输入 `00` 特别定义为 `00`。
2. 对结果执行固定的仿射变换（affine transformation）。

硬件不必在运行时完成上述数学计算。本项目直接使用ROM保存最终256项结果，面积更容易控制。

## 6. ShiftRows：行移位

`ShiftRows` 对状态矩阵的每一行执行循环左移：

| 行号 | 操作 |
|---:|---|
| 0 | 不移动 |
| 1 | 循环左移1 byte |
| 2 | 循环左移2 byte |
| 3 | 循环左移3 byte |

假设输入为：

```text
| a0 a4 a8 ac |
| a1 a5 a9 ad |
| a2 a6 aa ae |
| a3 a7 ab af |
```

ShiftRows之后为：

```text
| a0 a4 a8 ac |
| a5 a9 ad a1 |
| aa ae a2 a6 |
| af a3 a7 ab |
```

若目标位置为 `(row, column)`，其数据来自：

```text
source_column = (column + row) mod 4
```

因此：

```text
output[row, column] = input[row, (column + row) mod 4]
```

ShiftRows只重新排列字节，不改变任何字节的数值。

## 7. MixColumns：列混合

`MixColumns` 分别处理状态矩阵的四列。每列4个字节经过 `GF(2^8)` 上的矩阵乘法，产生新的4个字节。

设一列输入为：

```text
| a |
| b |
| c |
| d |
```

计算为：

```text
| a' |   | 02 03 01 01 |   | a |
| b' | = | 01 02 03 01 | × | b |
| c' |   | 01 01 02 03 |   | c |
| d' |   | 03 01 01 02 |   | d |
```

展开后：

```text
a' = (02·a) XOR (03·b) XOR c XOR d
b' = a XOR (02·b) XOR (03·c) XOR d
c' = a XOR b XOR (02·c) XOR (03·d)
d' = (03·a) XOR b XOR c XOR (02·d)
```

这里的乘法不是普通整数乘法，而是AES有限域乘法。

## 8. GF(2^8) 有限域运算

AES把一个字节看成系数只能为0或1的多项式。例如：

```text
57(hex) = 01010111(binary)
        = x^6 + x^4 + x^2 + x + 1
```

所有结果都对不可约多项式取模：

```text
m(x) = x^8 + x^4 + x^3 + x + 1
```

它的二进制表示是 `0x11b`。由于字节只能保存低8位，化简时常使用低8位常数 `0x1b`。

### 8.1 加法

有限域加法就是按位异或：

```text
a + b = a XOR b
```

### 8.2 乘以02：xtime

乘以 `02` 等价于多项式乘以 `x`：

```text
if x[7] == 0:
    xtime(x) = x << 1
else:
    xtime(x) = (x << 1) XOR 1b
```

结果只保留低8位。RTL常写成：

```verilog
{x[6:0], 1'b0} ^ (8'h1b & {8{x[7]}})
```

例如：

```text
02 · 57 = ae
02 · ae = 47
```

第二个例子中 `ae` 的最高位为1，因此左移后需要异或 `1b`。

### 8.3 乘以03

因为有限域中 `03 = 02 + 01`，所以：

```text
03 · x = (02 · x) XOR x
       = xtime(x) XOR x
```

因此加密方向的MixColumns只需要 `xtime` 和异或门。

## 9. AES-128 密钥扩展

128-bit原始密钥需要扩展成11个128-bit轮密钥：

```text
RoundKey[0]  = 原始密钥
RoundKey[1]
...
RoundKey[10]
```

### 9.1 按32-bit字划分

把原始密钥按从左到右分成4个32-bit字：

```text
w[0], w[1], w[2], w[3]
```

继续生成 `w[4]` 到 `w[43]`，每4个字构成一个轮密钥：

```text
RoundKey[r] = {w[4r], w[4r+1], w[4r+2], w[4r+3]}
```

### 9.2 生成公式

对于 `i = 4 ... 43`：

```text
temp = w[i-1]

if i mod 4 == 0:
    temp = SubWord(RotWord(temp)) XOR Rcon[i/4]

w[i] = w[i-4] XOR temp
```

其中：

- `RotWord`：把32-bit字循环左移一个字节。
- `SubWord`：对该字的4个字节分别查询AES S-box。
- `Rcon`：轮常数，只作用于最高字节。

例如：

```text
RotWord({a0, a1, a2, a3}) = {a1, a2, a3, a0}
SubWord({a0, a1, a2, a3}) = {SBOX[a0], SBOX[a1], SBOX[a2], SBOX[a3]}
```

### 9.3 Rcon轮常数

AES-128十轮使用：

```text
Rcon[1]  = 01 00 00 00
Rcon[2]  = 02 00 00 00
Rcon[3]  = 04 00 00 00
Rcon[4]  = 08 00 00 00
Rcon[5]  = 10 00 00 00
Rcon[6]  = 20 00 00 00
Rcon[7]  = 40 00 00 00
Rcon[8]  = 80 00 00 00
Rcon[9]  = 1b 00 00 00
Rcon[10] = 36 00 00 00
```

轮常数的第一个字节逐轮执行 `xtime`，其余三个字节为0。

### 9.4 第一轮密钥示例

原始密钥：

```text
000102030405060708090a0b0c0d0e0f
```

划分为：

```text
w0 = 00010203
w1 = 04050607
w2 = 08090a0b
w3 = 0c0d0e0f
```

对 `w3` 计算：

```text
RotWord(w3) = 0d0e0f0c
SubWord(...) = d7ab76fe
XOR Rcon[1]  = d6ab76fe
```

于是：

```text
new_w0 = w0 XOR d6ab76fe = d6aa74fd
new_w1 = w1 XOR new_w0   = d2af72fa
new_w2 = w2 XOR new_w1   = daa678f1
new_w3 = w3 XOR new_w2   = d6ab76fe
```

第一轮密钥为：

```text
d6aa74fdd2af72fadaa678f1d6ab76fe
```

## 10. 标准示例与中间结果

使用常见AES-128测试向量：

```text
Plaintext  = 00112233445566778899aabbccddeeff
Cipher Key = 000102030405060708090a0b0c0d0e0f
Ciphertext = 69c4e0d86a7b0430d8cdb78070b4c55a
```

初始AddRoundKey之后：

```text
00102030405060708090a0b0c0d0e0f0
```

第1轮中间结果：

```text
After SubBytes:    63cab7040953d051cd60e0e7ba70e18c
After ShiftRows:   6353e08c0960e104cd70b751bacad0e7
After MixColumns:  5f72641557f5bc92f7be3b291db9f91a
Round 1 Key:       d6aa74fdd2af72fadaa678f1d6ab76fe
After AddRoundKey: 89d810e8855ace682d1843d8cb128fe4
```

第10轮使用的轮密钥为：

```text
13111d7fe3944a17f307a78b4d2b30c5
```

最终输出必须是：

```text
69c4e0d86a7b0430d8cdb78070b4c55a
```

这些中间结果适合定位错误：若SubBytes正确但ShiftRows错误，通常是状态矩阵的行列顺序或字节切片方向写反；若前两步正确但MixColumns错误，应重点检查 `xtime` 和列边界。

## 11. 算法与当前硬件实现的对应关系

算法规定“做什么”，硬件架构决定“用多少周期完成”。当前设计为了减小面积采用一块单端口同步S-box ROM：

- 密钥扩展的4次S-box查询顺序执行。
- 状态的16次S-box查询顺序执行。
- SubBytes的结果直接写入ShiftRows后的目标位置。
- 一套32-bit `mix_column` 逻辑依次处理四列。
- 每轮即时生成下一轮密钥，不保存全部轮密钥。

虽然硬件把一个AES轮拆成许多时钟周期，但每轮完成后的 `state_reg` 必须与上述标准算法结果完全一致。

## 12. 常见错误检查表

1. 把AES状态误写成行优先排列。
2. 把 `[127:120]` 当成最后一个字节，而不是第一个字节。
3. ShiftRows方向写成循环右移。
4. 第10轮仍然执行MixColumns。
5. 把MixColumns的有限域乘法当成普通整数乘法。
6. `xtime` 在最高位为1时忘记异或 `8'h1b`。
7. `03·x` 写成普通的 `3*x`，而不是 `xtime(x) XOR x`。
8. RotWord旋转方向错误。
9. Rcon异或到错误的字节。
10. 同步ROM地址送出后，在同一时钟沿立即使用尚未更新的输出。
11. 在串行ShiftRows过程中直接覆盖仍未读取的源状态字节。
12. 在新轮密钥完成前就执行该轮AddRoundKey。

完成RTL修改后，应至少运行：

```sh
make test
```

并用本节标准向量及第1轮中间值检查算法步骤。
