"""立创开源智能复刻平台 —— 核心库。

给定立创开源(oshwhub.com)项目链接，自动完成：
  抓取硬件/原理图/BOM  ->  克隆对应开源源码  ->  归档(硬件/软件/材料/文档)
  ->  生成中文技术设计文档  ->  (可选) 推送 GitHub。

设计原则：
  * 零外部依赖，仅使用 Python 标准库（3.9+ 即可运行）。
  * 网络受限时优雅降级：自动抓取失败可改用 --manifest 传入已提取的 JSON。
  * 克隆失败时记录手动命令，不阻断整体流程。
"""

__version__ = "0.1.0"
__all__ = ["core", "fetcher", "cloner", "docgen", "models"]

from . import models
from .models import (
    Project,
    SourceRepo,
    BomItem,
    CloneResult,
)
from .fetcher import fetch_project
from .cloner import clone_sources
from .docgen import render_example
from .core import run_pipeline

__all__ += [
    "Project",
    "SourceRepo",
    "BomItem",
    "CloneResult",
    "fetch_project",
    "clone_sources",
    "render_example",
    "run_pipeline",
]
