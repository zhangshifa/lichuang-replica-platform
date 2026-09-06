# 示例：HelixLink 多功能调试器

> 本目录由「立创开源智能复刻平台」自动生成（manifest 驱动），演示从立创开源链接到可复刻归档的完整流程。

- **项目链接**：<https://oshwhub.com/flyn/helixlink>
- **原作者**：flyn
- **许可证**：CC BY-NC-SA 4.0
- **主仓库**：<https://gitee.com/helixlink/helixlink>

## 本平台归档结构

| 目录 | 内容 |
| --- | --- |
| [`01_hardware/`](01_hardware/) | 硬件设计：原理图 / PCB 说明、BOM 物料清单 |
| [`02_software/`](02_software/) | 软件与固件：源码克隆、第三方依赖（vendor）、克隆报告 |
| [`03_materials/`](03_materials/) | 材料清单与采购指南 |
| [`04_docs/`](04_docs/) | 复刻指南 + 完整技术设计文档 |

## 怎么复现这个归档

```bash
# 用 manifest 驱动（最稳，规避立创反爬/登录墙）
python scripts/replica_cli.py https://oshwhub.com/flyn/helixlink \
    --manifest examples/HelixLink/manifest.json --name HelixLink

# 或离线仅生成文档
python scripts/run_example.py
```

> 注：实际克隆主仓库（gitee）在本环境受匿名鉴权限制，平台会自动记录手动克隆命令于
> `02_software/CLONE_REPORT.md`，并在 `02_software/source/vendor/` 实证克隆了真实第三方依赖
> （如 `lwrb`）。这是平台「克隆失败优雅降级」能力的真实演示。
