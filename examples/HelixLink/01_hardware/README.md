# 硬件设计

HelixLink 的硬件设计（原理图 / PCB）在立创开源平台完全开源，可直接用立创 EDA 一键克隆工程。

## 核心特性

- SWD / JTAG 调试接口
- UART 串口透传
- USB 虚拟串口 / CDC
- 信号隔离保护
- 可扩展的调试/测量通道

## 原理图 / PCB

- **原理图格式**：嘉立创 EDA（立创 EDA）工程
- **PCB 是否开源**：是（立创开源项目页可导出）
- **核心 MCU（提示）**：带 USB 外设的 ARM Cortex-M 系列 MCU（具体型号以立创工程为准）

## 说明

完整的原理图与 PCB 源文件请从立创开源项目页导出（立创 EDA 一键克隆工程）。
平台在自动抓取成功时会把工程文件归档到本目录；当前为 manifest 模式，
请在立创页面导出工程后放入本目录（建议命名 `HelixLink_SCH_PCB.epro` 或拆分 `schematic.pdf` / `pcb.pdf`）。

## BOM

见同目录 [`BOM.md`](BOM.md)。
