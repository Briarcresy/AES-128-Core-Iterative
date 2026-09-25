# 目录与文件用途

## 当前布局

```text
AES-128-Core-Iterative/
├── rtl/                    # 主工程 RTL：接口封装和 AES 核
├── tests/                  # RTL 仿真测试
├── model/                  # Python 参考模型
├── mem/                    # AES S-box 内容源文件
├── constraints/            # 时序约束
├── scripts/                # ROM 转换、STA 配置和结果汇总
├── files.f                 # 主工程综合文件列表
├── Makefile                # 测试、lint、STA/PPA 入口
├── docs/                   # 设计说明和工程指南
│   └── links.txt           # 原 link.txt，保持本地忽略
├── artifacts/              # 图纸、报告及其可编辑源文件
│   ├── architecture/       # 架构图、绘图脚本及校验记录
│   ├── schematic/          # 原理图、绘图脚本及导出包
│   ├── pdf/                # 设计报告、LaTeX 源文件及配图
│   ├── screenshots/        # 原根目录 image1.png、image2.png
│   └── aes128_rtl_architecture.pdf
├── backend/                # ECC 工程和后端结果
│   ├── project.json        # 已有 ECC 项目元数据
│   ├── workspace/          # 已有工作区，保留原路径
│   ├── ws_0001/            # 已有工作区，保留原路径
│   ├── signoff/            # 已有导出包，不能默认视为可流片版本
│   └── sta-results/        # STA/PPA 历史结果及后续 make sta 输出
├── backend_new/            # 当前为空，待用户批准后再删除
├── my-frame-design/        # 独立 Git 仓库：frame 接入和系统测试
├── pdk/                    # 当前 RTL、仿真和后端依赖的工艺/IP 资源
└── yosys-sta/              # 独立下载的 STA 工具及其资源
```

`artifacts/` 包含可编辑源文件，不能当作可随意清空的构建缓存。
`rtl/` 和 frame 用户目录中的 RTL 属于不同工程入口，不自动互相覆盖。
`my-frame-design` 在父仓库中是 gitlink，且拥有自己的 `.git`；本次不改变它的版本管理方式。

## 常用操作

在仓库根目录运行 `make test`、`make lint` 或 `make sta CLK_FREQ_MHZ=20`。
STA/PPA 的新输出位于 `backend/sta-results/Aes128Iterative-20MHz/`。

frame 检查入口仍为：

```sh
cd my-frame-design
make check DESIGN=designs/aes128-iterative
```

该命令是现有入口，不表示 frame 工程已通过验证；其 ROM 模型文件列表问题需单独修复。

## 路径迁移

| 原路径 | 当前路径 |
|---|---|
| `output/` | `artifacts/` |
| `sta-results/` | `backend/sta-results/` |
| `image1.png`、`image2.png` | `artifacts/screenshots/` 下同名文件 |
| `link.txt` | `docs/links.txt` |

已更新 README、绘图使用说明、脚本中的使用示例、LaTeX 图片搜索路径、Makefile 和忽略规则。
历史日志、导出 manifest、压缩包和对话记录保持原内容，因此可能仍记录当时的旧绝对路径。
历史 STA 目录作为结果归档保存；需要重新执行分析时从根目录 `make sta` 开始。
ECC 工作区、PDK 和工具原路径保留，避免破坏已有工程的绝对路径依赖。

## 待批准的清理项

本次只移动和整理，没有删除文件。以下项目需用户批准后才清理：

| 项目 | 约占用 | 判断 |
|---|---:|---|
| `backend_new/` | 空目录 | 可删除空目录 |
| `artifacts/architecture/__pycache__/` | 56 KB | Python 缓存，可重新生成 |
| `artifacts/pdf/aes128_design_report.synctex.gz` | 20 KB | LaTeX 编辑器正反向定位辅助文件，非报告正文 |
| `my-frame-design/build/` | 2.7 MB | 可重建的仿真产物；含波形等调试资料，删除前确认不再需要 |

暂不建议删除 `backend/signoff/` 的压缩包、原理图 ZIP、历史 STA 结果及两处 PDK。
压缩包可能是独立交付快照，历史结果用于比较；工具自带 PDK 与项目 PDK 尚未证明等价。
