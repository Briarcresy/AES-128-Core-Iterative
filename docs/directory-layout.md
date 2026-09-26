# 目录与文件用途

## 当前布局

    AES-128-Core-Iterative/
    ├── rtl/                    # AES 核与接口封装 RTL
    ├── tests/                  # RTL 仿真测试
    ├── model/                  # Python 参考模型
    ├── mem/                    # AES S-box 内容源文件
    ├── constraints/            # 主工程时序约束
    ├── scripts/                # 仿真、STA 与 ECC 后端脚本
    ├── artifacts/              # 架构图、原理图、报告和配图
    ├── aes-mpc-ecc/            # ECC 后端及最终流片工程
    │   ├── ecc.toml            # 20 MHz、50% 利用率配置
    │   ├── optimization.json   # AREA 0 综合策略
    │   ├── ws-area20/          # 唯一的最终后端工作区
    │   └── signoff/ws-area20/  # 已下单的 .v/.def、ROM 附件与备注
    ├── backend/                # 主工程 make sta 的输出
    ├── my-frame-design/        # MPC-Frame 接入及系统测试
    ├── pdk/                    # RTL、仿真和后端依赖的工艺/IP 资源
    └── yosys-sta/              # STA 工具及资源

aes-mpc-ecc/ws-area20 是本项目唯一的最终流片后端结果，已用于 ECOS Factory 下单。交付文件、ROM 内容附件和订单备注集中在 aes-mpc-ecc/signoff/ws-area20/。最终参数和检查记录见 ECC 后端指南及最终流片版本说明。

artifacts/ 包含可编辑源文件，不作为构建缓存清理。rtl/ 与 frame 用户目录中的 RTL 属于不同工程入口，不会自动互相覆盖。my-frame-design 是独立 Git 仓库。

## 常用操作

在仓库根目录运行 make test、make lint 或 make sta CLK_FREQ_MHZ=20。主工程 STA 输出位于 backend/sta-results/Aes128Iterative-20MHz/。

Frame 检查入口：

    cd my-frame-design
    make check DESIGN=designs/aes128-iterative

此入口检查 Frame 工程集成；最终用户模块流片结果和交付文件以 aes-mpc-ecc/ws-area20 及其 signoff 目录为准。
