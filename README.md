# 立创开源智能复刻平台

> 粘贴一个立创开源（oshwhub.com）链接，平台自动完成：抓取硬件/原理图/BOM → 克隆对应开源源码 →
> 按 **硬件 / 软件 / 材料 / 文档** 归档 → 生成中文技术设计文档，方便社区一键复刻开源硬件项目。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.9%2B-3776AB.svg)

---

## 这是什么

[立创开源（嘉立创开源硬件平台）](https://oshwhub.com) 上有大量优秀的开源硬件项目，但复刻它们往往需要：

1. 手动从页面扒原理图、BOM、源码仓库链接；
2. 逐个克隆固件/上位机及其第三方依赖；
3. 把零散信息整理成可复刻的技术文档。

**本平台把上面三步自动化**：你只需给一个链接，它就产出一份结构清晰、软硬件齐全、带中文技术设计文档的归档目录，可直接推送到 GitHub 分享。

## 特性

- 🔗 **链接即归档**：输入 `https://oshwhub.com/owner/project` 即可。
- 📐 **软硬件一体**：自动分离 `01_hardware / 02_software / 03_materials / 04_docs`。
- 📦 **克隆开源源码**：尝试多种通道克隆主仓库与第三方依赖，失败则记录手动命令，不阻断流程。
- 📝 **中文技术设计文档**：自动渲染背景、硬件、软件架构、BOM、复刻步骤、许可证。
- 🚀 **一键推送 GitHub**：内置 Git Data / Contents API 推送脚本（token 仅读环境变量）。
- 🧩 **零依赖**：核心库仅用 Python 标准库（3.9+），开箱即跑。

## 目录结构

```
.
├── README.md                 # 本文件（平台总览）
├── requirements.md           # 需求文档原文（一字不改存档）
├── docs/
│   ├── platform_design.md    # 平台技术设计文档（架构/模块/数据流/容错）
│   └── usage.md              # 使用手册
├── scripts/
│   ├── replica_cli.py        # 主 CLI：链接 → 抓取 → 克隆 → 归档 → 文档
│   ├── github_push.py        # 通过 GitHub API 推送目录（含中文描述）
│   └── run_example.py        # 一键复现 HelixLink 示例（离线）
├── src/lichuang_replica/     # 平台核心库（零依赖）
└── examples/
    └── HelixLink/            # 示例：HelixLink 多功能调试器（完整归档）
        ├── 01_hardware/      # 硬件：原理图/PCB 说明 + BOM
        ├── 02_software/      # 软件：源码 + vendor 依赖 + 克隆报告
        ├── 03_materials/     # 材料清单与采购
        └── 04_docs/          # 复刻指南 + 完整技术设计文档
```

## 快速开始

```bash
# 仓库根目录
cd lichuang-replica-platform

# 方式一：用 manifest（最稳，规避立创反爬/登录墙）
python scripts/replica_cli.py https://oshwhub.com/flyn/helixlink \
    --manifest examples/HelixLink/manifest.json --name HelixLink

# 方式二：离线仅生成文档（不联网克隆）
python scripts/run_example.py

# 方式三：推送到 GitHub（先设置 token）
set GITHUB_TOKEN=ghp_xxx
python scripts/github_push.py --dir . --repo lichuang-replica-platform \
    --description "立创开源智能复刻平台：粘贴立创开源链接即可自动抓取硬件/原理图/BOM、克隆开源源码、生成中文技术设计文档并归档，方便社区复刻开源硬件项目。"
```

## 典型流程

```
立创开源链接
   │
   ▼
[1] 抓取 fetcher      → 标题/作者/许可证/源码仓库/BOM 链接
   │                   （失败则降级读取 manifest.json）
   ▼
[2] 克隆 cloner        → git clone 主仓库 + vendor 依赖（多通道重试）
   │                   （失败记录手动命令，写入 CLONE_REPORT.md）
   ▼
[3] 归档 docgen        → 生成 01~04 目录与中文技术设计文档
   │
   ▼
[4] 推送 github_push   → 通过 GitHub API 建库并推送（中文 description）
```

## 示例项目

[`examples/HelixLink`](examples/HelixLink/) —— 以 **HelixLink 多功能调试器**（立创开源 flyn，CC BY-NC-SA 4.0）
为示例，演示从链接到可复刻归档的完整产物：硬件设计、BOM、固件依赖栈（nanopb/lwrb/CherryUSB）、
材料采购与复刻步骤一应俱全。

## 许可证

平台代码以 MIT 许可证发布。示例归档中的原始硬件/固件设计版权归各自原作者所有，
复刻与二次开发请遵守其原始许可证（如 CC BY-NC-SA 4.0）。
