# 平台技术设计文档

## 1. 目标与定位

把「复刻一个立创开源硬件项目」从手工多步操作，变成「给链接 → 出归档」的单命令流程。
产出一份结构标准化、含中文技术设计文档的目录，可直接推送到 GitHub 分享。

## 2. 总体架构

```
                ┌─────────────────────────────────────────┐
  立创链接 ───▶ │            replica_cli.py (编排)          │
                └─────────────────────────────────────────┘
                                 │
        ┌────────────┬───────────┼────────────┬────────────┐
        ▼            ▼           ▼            ▼            ▼
   [fetcher]    [cloner]    [docgen]    [github_push]  [models]
   抓取元数据   克隆源码     渲染文档     推送 GitHub     数据模型
```

- **fetcher**：解析 `oshwhub.com/owner/project`；优先读 `--manifest` JSON，否则 HTTP 抓取页面并正则提取
  标题/简介/源码仓库链接。网络受限时优雅降级到 manifest。
- **cloner**：对每个源码仓库尝试多种克隆通道（常规 / 绕过 insteadOf 镜像 / :443 直连），
  任一成功即剥离 `.git` 保留源码树；全部失败则记录手动命令。
- **docgen**：依据 `Project` 数据渲染 `01_hardware / 02_software / 03_materials / 04_docs`
  四类目录与中文技术设计文档。
- **github_push**：经 GitHub REST API（Contents API）建库并分文件推送；
  token 仅从环境变量 `GITHUB_TOKEN` 读取，绝不硬编码。

## 3. 数据模型（models.py）

- `Project`：统一项目表示（owner/project/url/title/license/source_repos/vendor_deps/hardware/bom/...）。
- `SourceRepo`：需克隆的仓库（primary=主仓，vendor=第三方依赖）。
- `BomItem`：BOM 单行，字段对齐立创 EDA 导出（名称/位号/封装/数量/型号/制造商/供应商...）。
- `CloneResult`：单次克隆结果，含成功标志与手动命令（用于失败降级）。

## 4. 关键流程

1. `fetch_project(url, manifest)` → `Project`
2. `clone_sources(project, base_dir)` → `List[CloneResult]`
3. `render_example(project, base_dir, results)` → 写入 01~04 目录与文档
4. （可选）`github_push.py` 把整个仓库推送到 GitHub

## 5. 容错设计

| 风险 | 处理 |
| --- | --- |
| 立创页面反爬/登录墙 | 降级为 `--manifest` 传入已提取 JSON |
| gitee 匿名克隆 401 | 记录手动命令，不阻断流程（见示例 CLONE_REPORT） |
| gitclone 镜像 504 | 多通道重试（常规→绕过镜像→:443） |
| api.github.com 偶发 5xx | HTTP 请求带指数退避重试 |
| 大仓/子模块 | `--depth 1` 浅克隆，剥离 `.git` 仅留源码树 |

## 6. 依赖与运行环境

- Python 3.9+，仅标准库（零第三方依赖）。
- 克隆需本机 `git`；推送需网络可达 `api.github.com` 与 `GITHUB_TOKEN`。

## 7. 扩展性

- 新增抓取源（如其他开源硬件平台）：实现 `fetcher` 的解析器即可。
- 新增文档模板：扩展 `docgen.render_example`。
- 新增推送后端：替换 `github_push.py`（如 Gitee API、本地静态托管）。
