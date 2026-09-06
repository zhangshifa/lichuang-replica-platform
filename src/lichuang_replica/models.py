"""数据模型：项目、BOM 物料、源码仓库、克隆结果。"""

from __future__ import annotations

import dataclasses
from typing import Dict, List


@dataclasses.dataclass
class BomItem:
    """BOM 物料清单单行。字段对齐立创开源 / 嘉立创 EDA 导出格式。"""

    index: str = ""              # 序号
    name: str = ""               # 元件名称
    designator: str = ""         # 位号
    footprint: str = ""          # 封装
    quantity: str = ""           # 数量
    manufacturer_part: str = ""  # 制造商型号
    manufacturer: str = ""       # 制造商
    supplier: str = ""           # 供应商
    supplier_part: str = ""      # 供应商料号
    note: str = ""               # 备注

    @classmethod
    def fields(cls) -> List[str]:
        return list(cls.__dataclass_fields__.keys())


@dataclasses.dataclass
class SourceRepo:
    """一个需要克隆的开源源码仓库。"""

    url: str
    desc: str = ""
    priority: str = "primary"  # primary=项目主仓 / vendor=第三方依赖


@dataclasses.dataclass
class CloneResult:
    """单次克隆尝试的结果，用于归档与失败降级。"""

    url: str
    success: bool = False
    dest: str = ""
    error: str = ""
    manual_cmd: str = ""  # 失败时给出的手动克隆命令


@dataclasses.dataclass
class Project:
    """立创开源项目在平台内的统一表示。"""

    platform: str = "oshwhub"
    owner: str = ""
    project: str = ""
    url: str = ""
    title: str = ""
    author: str = ""
    summary: str = ""
    license: str = ""
    source_repos: List[SourceRepo] = dataclasses.field(default_factory=list)
    vendor_deps: List[SourceRepo] = dataclasses.field(default_factory=list)
    hardware: Dict = dataclasses.field(default_factory=dict)
    bom_note: str = ""
    bom: List[BomItem] = dataclasses.field(default_factory=list)
    replication_steps: List[str] = dataclasses.field(default_factory=list)
    extra: Dict = dataclasses.field(default_factory=dict)

    @property
    def safe_name(self) -> str:
        """用于目录名的项目标识。"""
        if self.owner and self.project:
            return f"{self.owner}_{self.project}"
        return (self.title or self.project or "project").strip().replace(" ", "_")
