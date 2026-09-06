# 使用手册

## 环境准备

- Python 3.9+
- 本机安装 `git`（用于克隆源码）
- 推送 GitHub 需 `api.github.com` 可达，并设置 `GITHUB_TOKEN`

```bash
git --version
python --version
```

## 场景一：用已提取的 manifest（推荐，最稳）

当立创页面无法直接抓取（反爬/登录墙）时，先用浏览器或 AI 提取项目信息保存为 `manifest.json`，
再交给平台：

```bash
python scripts/replica_cli.py https://oshwhub.com/flyn/helixlink \
    --manifest examples/HelixLink/manifest.json --name HelixLink
```

`manifest.json` 字段见 `examples/HelixLink/manifest.json`。

## 场景二：直接给链接（自动抓取）

```bash
python scripts/replica_cli.py https://oshwhub.com/flyn/helixlink
```

若自动抓取失败，命令行会提示改用 `--manifest` 模式。

## 场景三：仅生成文档（离线）

```bash
python scripts/run_example.py
```

## 场景四：推送到 GitHub

```bash
set GITHUB_TOKEN=ghp_xxx        # Windows
# export GITHUB_TOKEN=ghp_xxx   # Linux/macOS

python scripts/github_push.py --dir . --repo lichuang-replica-platform \
    --description "立创开源智能复刻平台：粘贴立创开源链接即可自动抓取硬件/原理图/BOM、克隆开源源码、生成中文技术设计文档并归档，方便社区复刻开源硬件项目。" \
    --topics "oshwhub,open-source-hardware,replication,lcsc,esp32"
```

脚本会：自动建库（若存在则复用）→ 设置中文描述与 topics → 分文件推送（自动排除 `.git` 等）。

## 产物说明

运行后会在 `examples/<项目名>/` 下生成：

- `01_hardware/`：硬件设计说明 + BOM
- `02_software/`：源码目录 + `CLONE_REPORT.md`（克隆状态与手动命令）
- `03_materials/`：材料清单与采购
- `04_docs/`：`复刻指南.md` + `技术设计文档.md`

## 常见问题

- **克隆主仓库失败**：多为 gitee 匿名鉴权限制，按 `CLONE_REPORT.md` 的手动命令在本机克隆即可。
- **推送 401**：检查 `GITHUB_TOKEN` 是否正确、是否有建库权限。
- **推送 5xx**：脚本已带重试；若持续失败，可分批或稍后重试。
