# 软件 / 固件

源码由平台克隆至 `02_software/source/`：

- `01_helixlink/` —— 项目主仓库（固件 + 桌面上位机），地址 <https://gitee.com/helixlink/helixlink>
- `vendor/` —— 第三方开源依赖（已实证克隆 `lwrb` 等）

> 由于本环境对 gitee 匿名克隆有鉴权限制，主仓库克隆由平台记录手动命令
> （见 [`CLONE_REPORT.md`](CLONE_REPORT.md)）。请在本机执行报告中的命令完成克隆。

## 固件依赖栈（来自主仓库 `share/`）

- **nanopb** <https://github.com/nanopb/nanopb> —— 轻量 protobuf，固件-上位机通信协议
- **lwrb** <https://github.com/MaJerle/lwrb> —— 环形缓冲区，串口/USB 数据缓冲（已实证克隆）
- **CherryUSB** <https://github.com/cherry-embedded/CherryUSB> —— 嵌入式 USB 协议栈

## 构建流程（通用）

1. 安装 MCU 工具链（如 ARM GCC）与烧录工具（如 OpenOCD / 厂商工具）。
2. 拉取 `vendor/` 依赖（或按主仓库子模块说明）。
3. 编译固件并烧录到目标 MCU。
4. 编译/运行桌面上位机，连接设备联调。

具体步骤以主仓库 README 为准。
