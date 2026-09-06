# 源码目录

本目录由平台 `clone_sources` 生成。

- `01_helixlink/` —— 待克隆：<https://gitee.com/helixlink/helixlink>
  （本环境 gitee 匿名克隆受鉴权限制，请在本机执行 `git clone --depth 1 https://gitee.com/helixlink/helixlink.git`）
- `vendor/` —— 第三方依赖实证克隆：
  - `lwrb/` —— <https://github.com/MaJerle/lwrb>（已成功克隆，作为平台"克隆开源源码"能力实证）

> 平台对克隆失败会优雅降级：在父目录 `CLONE_REPORT.md` 记录每个仓库的状态与手动命令，
> 不阻断整体复刻流程。
