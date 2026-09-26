# AES + ROM 的 ECC 后端

本工程用于 AES-128 加密核流片的 ECC 后端。最终流片版本为 aes-mpc-ecc/ws-area20，配置为 20 MHz、核心利用率 50%、布局目标密度 50%、综合策略 AREA 0。ECC 版本为 0.1.0a12，用户模块顶层为 Aes128Iterative。用户已基于此版本提交流片订单。

交付的 .v 门级网表和 .def 来自该工作区，描述 MPC-Frame 用户模块，不包含公共 FrameTop。

## 查看最终结果

在仓库根目录执行：

    python3 scripts/ecc_backend.py inspect --workspace area20
    ecc log --project aes-mpc-ecc --workspace ws-area20

最终流片结果保存在 aes-mpc-ecc/ws-area20/，交付文件已导出。

## 配置说明

- 综合从 ROM Liberty 导入黑盒端口，保留宏实例；布局布线用 LEF；时序用 Liberty；仿真和等价性检查用同步 ROM 功能模型。
- 本流程使用 Liberty 宏声明，并检查网表中恰好存在一个 ROM 宏实例。
- MAX/WCL/TYP/MIN/ML 分别使用 SS 125℃、SS -40℃、TT 25℃、FF -40℃、FF 125℃ 的 ROM 库。
- 20 MHz 对应 50 ns 周期。FPGA 下降沿发数据，ASIC 上升沿采样；输入 max/min 为 35/25 ns，输出 max/min 为 10/0 ns，setup/hold uncertainty 为 0.2/0 ns，并启用传播时钟。hold 预算应结合 FPGA 时序、板级延迟和时钟偏斜由平台核对。
- 布局采用核心利用率 50%、目标密度 50%、边缘留白 5 µm。ROM LEF 尺寸为 67.680 × 26.025 µm，位置为 (20,20) µm，方向 N，halo 为 3 µm。
- RTL 测试验证 AES 与接口；LEC 验证逻辑等价；STA 验证时序；DRC/LVS 验证物理规则和连接。

## 文件分工

- aes-mpc-ecc/ecc.toml：顶层、时钟、工艺库和布局参数。
- aes-mpc-ecc/macro-placement.json：ROM 实例、坐标和方向。
- aes-mpc-ecc/optimization.json：AREA 0 综合策略。
- scripts/ecc_backend.py：准备工艺库链接、生成综合输入和 SDC、运行后端流程。
- scripts/ecc_yosys.py：ECC a12 等价性检查适配器。
- scripts/ecc_rom_floorplan.py：生成 ROM 预放置 DEF。
- aes-mpc-ecc/generated/：自动生成输入。
- aes-mpc-ecc/pdk/：工艺资源链接。
- aes-mpc-ecc/ws-area20/：最终流片版本的冻结输入、配置、日志、报告和输出。

ECC a12 的 LEC 默认将 Liberty 当作标准单元库读取，不能直接处理 ROM bus 接口。本工程适配器仅在 LEC 阶段使用由 mem/sbox.mem 生成的同步 ROM 功能模型，标准单元仍使用原库；不跳过等价性检查，也不改变综合得到的 ROM 硬宏。脚本会补齐 ECC 默认 STA 配置中缺少的五组 ROM 工况。

## 流片交付

最终交付目录为 aes-mpc-ecc/signoff/ws-area20/，上传其中同一次运行生成的 aes128-iterative.v 和 aes128-iterative.def。原始 ECC 签核包位于 aes-mpc-ecc/signoff/ws-area20.tar.gz。目录还包含 sha256.json、ROM 内容附件和 rom-order-note.txt。

该版本已用于 ECOS Factory 流片下单。订单中的 ROM 内容替换要求应与交付文件一并核对。ROM 宏为 ics55_ecos_rom_256x8_m8_b1，实例路径为 u_core.u_sbox_rom.u_rom，容量为 256×8 bit。.romcode 与 mem/sbox.mem 的 256 项一致。按平台说明，平台需按附件内容替换默认 ROM 并生成匹配版图；应确认平台完成替换和集成。

## 最终版本验证记录

工作区 aes-mpc-ecc/ws-area20 使用 20 MHz、50% 核心利用率、50% 布局密度及 AREA 0。15 个后端步骤成功，13 个 STA 工况通过；Setup/Hold WNS 为 +3.981/+0.071 ns，DRC/LVS 为 0/0，综合后及布线后 LEC 均通过。ECC 签核检查为 34 项通过、0 项阻塞、4 项提醒。运行前 ROM、MixColumns、AES 核和接口封装四项测试通过。
