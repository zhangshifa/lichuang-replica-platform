"""流程编排：把抓取、克隆、文档生成串成一条流水线。"""

from __future__ import annotations

import os
from typing import List, Optional

from .cloner import clone_sources
from .docgen import render_example
from .fetcher import fetch_project
from .models import CloneResult, Project


def run_pipeline(
    url: str,
    out_base: str,
    *,
    manifest: Optional[str] = None,
    name: Optional[str] = None,
    no_clone: bool = False,
) -> dict:
    """运行完整复刻流水线。

    返回包含 project / results / example_dir 的字典，供 CLI / 脚本进一步使用。
    """
    project: Project = fetch_project(url, manifest_path=manifest)
    example_dir = os.path.join(out_base, "examples", name or project.safe_name)

    results: List[CloneResult] = []
    if not no_clone:
        results = clone_sources(project, example_dir)

    render_example(project, example_dir, results)

    return {
        "project": project,
        "results": results,
        "example_dir": example_dir,
    }
