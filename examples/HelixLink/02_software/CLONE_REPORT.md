# 源码克隆报告

> 本表由「立创开源智能复刻平台」自动生成，记录对各开源仓库的克隆尝试结果。

| 仓库 | 状态 | 本地路径 | 手动命令 |
| --- | --- | --- | --- |
| <https://gitee.com/helixlink/helixlink> | ⚠️ 失败(需手动) | - | `git clone --depth 1 https://gitee.com/helixlink/helixlink.git 01_helixlink` |
| <https://github.com/nanopb/nanopb> | ⚠️ 受限(需手动) | - | `git clone --depth 1 https://github.com/nanopb/nanopb.git vendor/nanopb` |
| <https://github.com/MaJerle/lwrb> | ✅ 成功 | `vendor/lwrb` | `git clone --depth 1 https://github.com/MaJerle/lwrb.git vendor/lwrb` |
| <https://github.com/cherry-embedded/CherryUSB> | ⚠️ 受限(需手动) | - | `git clone --depth 1 https://github.com/cherry-embedded/CherryUSB.git vendor/CherryUSB` |

## 说明

- **lwrb** 已成功克隆到 `vendor/lwrb`，作为平台「克隆开源源码」能力的实证。
- gitee 主仓库在本环境受匿名鉴权限制（401），请在本机执行上表手动命令完成克隆。
- 平台的多通道重试（常规 / 绕过镜像 / :443）已尽力尝试，失败不阻断整体复刻流程。
