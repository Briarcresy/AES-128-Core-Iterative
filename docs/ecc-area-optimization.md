# 最终流片版本

本项目最终流片版本为 ws-area20，用户已据此下单。项目相关配置、交付和后端说明均以此版本为准。

## 配置和结果

- ECC 工作区：aes-mpc-ecc/ws-area20/
- 流片交付目录：aes-mpc-ecc/signoff/ws-area20/
- ECC 原始签核包：aes-mpc-ecc/signoff/ws-area20.tar.gz
- 顶层：Aes128Iterative；工艺：ICS55；ECC：0.1.0a12
- 频率：20 MHz（周期 50 ns）；核心利用率：50%；布局目标密度：50%
- 综合策略：AREA 0
- 模块面积：25090.56 µm²；综合标准单元面积（不含 ROM）：10991.852 µm²
- 15 个后端步骤成功，13 个 STA 工况通过；Setup/Hold WNS：+3.981/+0.071 ns
- DRC/LVS：0/0；综合后和布线后 LEC 均通过
- ECC 签核检查：34 项通过、0 项阻塞、4 项提醒

## 提交文件和 ROM 内容

交付目录中的 aes128-iterative.v 与 aes128-iterative.def 是同一工作区导出的配套文件，描述 MPC-Frame 用户模块 Aes128Iterative。同目录还包含 sha256.json、ROM 内容附件 ics55_ecos_rom_256x8_m8_b1.romcode、十六进制对照 sbox.mem 和订单备注 rom-order-note.txt。

ROM 有 256 个 8 位地址项。抽查值为地址 0x00→0x63、0x01→0x7C、0xFF→0x16。ROM 存储阵列版图由平台根据订单内容替换要求处理，需确认内容替换及版图集成完成。

## 检查

在仓库根目录查看后端和签核状态：

    python3 scripts/ecc_backend.py inspect --workspace area20

运行前 ROM、MixColumns、AES 核及接口封装测试通过。时序约束采用 50 ns 周期，输入 max/min=35/25 ns、输出 max/min=10/0 ns、setup/hold uncertainty=0.2/0 ns，并启用传播时钟。板级时序预算与 ROM 版图集成由平台确认。
