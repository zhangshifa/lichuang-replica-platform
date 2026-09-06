"""根据抓取到的项目数据，渲染示例目录与中文技术设计文档。"""

from __future__ import annotations

import os
from typing import List

from .models import CloneResult, Project


def _write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _clone_report_md(results: List[CloneResult]) -> str:
    lines = ["# 源码克隆报告", "", "本表由平台自动生成，记录对各开源仓库的克隆结果。", ""]
    lines.append("| 仓库 | 状态 | 本地路径 | 手动命令 |")
    lines.append("| --- | --- | --- | --- |")
    for r in results:
        status = "✅ 成功" if r.success else "⚠️ 失败(需手动)"
        path = r.dest or "-"
        cmd = r.manual_cmd or "-"
        lines.append(f"| {r.url} | {status} | `{path}` | `{cmd}` |")
    lines.append("")
    return "\n".join(lines) + "\n"


def render_example(project: Project, base_dir: str, results: List[CloneResult]) -> None:
    """在 base_dir 下生成 01~04 归档目录与文档。"""
    os.makedirs(base_dir, exist_ok=True)

    # 顶层示例 README
    _write(
        os.path.join(base_dir, "README.md"),
        f"# 示例：{project.title}\n\n"
        f"> 本目录由「立创开源智能复刻平台」自动生成，演示从立创开源链接到可复刻归档的完整流程。\n\n"
        f"- 项目链接：{project.url}\n"
        f"- 作者：{project.author or project.owner}\n"
        f"- 许可证：{project.license or '未提供'}\n\n"
        f"## 目录\n"
        f"- `01_hardware/` 硬件设计（原理图 / PCB / BOM）\n"
        f"- `02_software/` 软件与固件源码（含第三方依赖）\n"
        f"- `03_materials/` 材料清单与采购\n"
        f"- `04_docs/` 复刻指南与完整技术设计文档\n",
    )

    # 01 硬件
    hw = project.hardware or {}
    feats = hw.get("features", [])
    hw_md = (
        "# 硬件设计\n\n"
        f"## 核心特性\n"
        + ("".join(f"- {x}\n" for x in feats) if feats else "- 详见立创开源工程。\n")
        + f"\n## 原理图 / PCB\n"
        f"- 原理图格式：{hw.get('schematic_format', '立创 EDA 工程')}\n"
        f"- PCB 是否开源：{'是' if hw.get('pcb_open') else '请以立创页面为准'}\n"
        f"- 核心 MCU（提示）：{hw.get('core_mcu_hint', '以立创工程为准')}\n\n"
        f"## 说明\n完整的原理图与 PCB 源文件请从立创开源项目页导出（立创 EDA 一键克隆工程）。"
        f"平台会自动把工程归档到本目录。\n"
    )
    _write(os.path.join(base_dir, "01_hardware", "README.md"), hw_md)

    # BOM
    bom_lines = ["# BOM 物料清单", "",
                 "> " + (project.bom_note or "完整 BOM 见立创开源项目 BOM 附件。"), ""]
    if project.bom:
        cols = ["序号", "名称", "位号", "封装", "数量", "型号", "制造商", "供应商", "供应商料号"]
        bom_lines.append("| " + " | ".join(cols) + " |")
        bom_lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
        for b in project.bom:
            bom_lines.append(
                f"| {b.index} | {b.name} | {b.designator} | {b.footprint} | "
                f"{b.quantity} | {b.manufacturer_part} | {b.manufacturer} | "
                f"{b.supplier} | {b.supplier_part} |"
            )
    else:
        bom_lines.append("平台在自动抓取成功时会解析 BOM 表格并填充于此；"
                         "当前为 manifest 模式，请在立创页面导出 BOM 后粘贴到 `manifest.json` 的 `bom` 字段。")
    bom_lines.append("")
    _write(os.path.join(base_dir, "01_hardware", "BOM.md"), "\n".join(bom_lines) + "\n")

    # 02 软件
    src_md = (
        "# 软件 / 固件\n\n"
        "源码由平台克隆至 `02_software/source/`：\n\n"
        "- `01_*` 项目主仓库（固件 + 桌面上位机）\n"
        "- `vendor/` 第三方开源依赖\n\n"
        "## 第三方依赖\n"
    )
    for v in project.vendor_deps:
        src_md += f"- {v.url} —— {v.desc}\n"
    src_md += "\n## 构建\n具体编译步骤见各仓库 README；通用流程：安装工具链 → 编译固件 → 烧录 → 运行上位机联调。\n"
    _write(os.path.join(base_dir, "02_software", "README.md"), src_md)

    # 克隆报告
    _write(os.path.join(base_dir, "02_software", "CLONE_REPORT.md"), _clone_report_md(results))

    # 03 材料
    mat_md = (
        "# 材料清单与采购\n\n"
        "复刻本开源项目所需的材料分为三类：\n\n"
        "1. **PCB 与 SMT**：在嘉立创下单（立创开源一键下单，含 PCB 打样与 SMT 贴片）。\n"
        "2. **分立器件**：按 BOM（`01_hardware/BOM.md`）在立创商城 / 得捷 / 贸泽采购。\n"
        "3. **结构件与辅料**：外壳、排针、线缆、焊锡等。\n\n"
        "## 采购注意事项\n"
        "- 优先使用立创商城「BOM 表一键配单」功能，避免型号选错。\n"
        "- 注意器件封装（footprint）与 BOM 严格一致。\n"
        "- 备品：易损/极性器件（LED、电解电容、IC）建议多备 10%~20%。\n"
    )
    _write(os.path.join(base_dir, "03_materials", "README.md"), mat_md)

    # 04 文档：复刻指南
    steps = project.replication_steps or [
        "在立创开源导出/下单 PCB 与 SMT",
        "采购 BOM 中器件",
        "焊接/回流装配",
        "克隆固件源码并编译烧录",
        "运行桌面上位机联调",
    ]
    rep_md = (
        "# 复刻步骤指南\n\n" + "".join(f"{i}. {s}\n" for i, s in enumerate(steps, 1)) + "\n"
    )
    _write(os.path.join(base_dir, "04_docs", "复刻指南.md"), rep_md)

    # 04 文档：完整技术设计文档
    _write(
        os.path.join(base_dir, "04_docs", "技术设计文档.md"),
        _tech_design_md(project, results),
    )


def _tech_design_md(project: Project, results: List[CloneResult]) -> str:
    hw = project.hardware or {}
    feats = hw.get("features", [])
    lines = [
        f"# {project.title} —— 技术设计文档",
        "",
        f"> 自动归档于「立创开源智能复刻平台」。源链接：{project.url}",
        "",
        "## 1. 项目背景与目标",
        "",
        project.summary or "（待补充：项目简介）",
        "",
        "## 2. 硬件设计",
        "",
        "### 2.1 核心特性",
        "".join(f"- {x}\n" for x in feats) if feats else "- 详见立创开源工程。",
        "",
        "### 2.2 原理图与 PCB",
        f"- 原理图格式：{hw.get('schematic_format', '立创 EDA 工程')}",
        f"- PCB 开源：{'是' if hw.get('pcb_open') else '以立创页面为准'}",
        f"- 核心 MCU：{hw.get('core_mcu_hint', '以立创工程为准')}",
        "",
        "### 2.3 BOM 物料清单",
        "见 `01_hardware/BOM.md`。",
        "",
        "## 3. 软件 / 固件设计",
        "",
        "### 3.1 源码仓库",
    ]
    for i, r in enumerate(project.source_repos, 1):
        lines.append(f"{i}. {r.url} —— {r.desc or '项目主仓库'}")
    lines += [
        "",
        "### 3.2 第三方开源依赖",
    ]
    for v in project.vendor_deps:
        lines.append(f"- {v.url} —— {v.desc}")
    lines += [
        "",
        "### 3.3 克隆结果",
        "",
        "| 仓库 | 状态 |",
        "| --- | --- |",
    ]
    for r in results:
        lines.append(f"| {r.url} | {'✅' if r.success else '⚠️ 需手动'} |")
    lines += [
        "",
        "## 4. 材料清单与采购",
        "见 `03_materials/README.md`。",
        "",
        "## 5. 复刻与部署",
        "见 `04_docs/复刻指南.md`。",
        "",
        "## 6. 许可证与致谢",
        f"- 许可证：{project.license or '未提供'}",
        f"- 原作者：{project.author or project.owner}",
        "- 本归档由「立创开源智能复刻平台」自动生成，便于社区复刻与二次开发。",
        "",
    ]
    return "\n".join(lines)
