"""克隆开源源码，含多重通道与失败降级。"""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import List

from .models import CloneResult, Project, SourceRepo


def _repo_name(url: str) -> str:
    base = url.replace(".git", "").rstrip("/")
    return base.split("/")[-1] or "repo"


def _run(cmd, timeout: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def clone_one(repo: SourceRepo, dest: str) -> CloneResult:
    """尝试多种克隆通道，任一成功即返回；全部失败则记录手动命令。"""
    res = CloneResult(url=repo.url)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    base = repo.url.replace(".git", "")
    attempts: List[List[str]] = [
        # 1) 常规（本机可能经 insteadOf 镜像，偶发 504）
        ["git", "clone", "--depth", "1", base + ".git", dest],
        # 2) 绕过 insteadOf 镜像，强制直连 github
        ["git", "-c", "url.https://gitclone.com/github.com/.insteadof=",
         "clone", "--depth", "1", base + ".git", dest],
        # 3) :443 直连（部分网络可绕过重写）
        ["git", "clone", "--depth", "1",
         base.replace("https://github.com", "https://github.com:443") + ".git", dest],
    ]

    for i, cmd in enumerate(attempts, 1):
        try:
            r = _run(cmd)
            if r.returncode == 0 and os.path.exists(os.path.join(dest, ".git")):
                shutil.rmtree(os.path.join(dest, ".git"), ignore_errors=True)
                res.success = True
                res.dest = dest
                res.manual_cmd = " ".join(cmd)
                return res
            res.error = (res.error + f"\n[尝试{i}] " + (r.stderr or r.stdout)[:280]).strip()
        except Exception as e:  # noqa: BLE001
            res.error = (res.error + f"\n[尝试{i}] {e}").strip()

    res.manual_cmd = f"git clone --depth 1 {base}.git {dest}"
    return res


def clone_sources(project: Project, base_dir: str) -> List[CloneResult]:
    results: List[CloneResult] = []
    src_dir = os.path.join(base_dir, "02_software", "source")
    os.makedirs(src_dir, exist_ok=True)

    for i, repo in enumerate(project.source_repos, 1):
        dest = os.path.join(src_dir, f"{i:02d}_{_repo_name(repo.url)}")
        results.append(clone_one(repo, dest))

    vdir = os.path.join(src_dir, "vendor")
    for repo in project.vendor_deps:
        dest = os.path.join(vdir, _repo_name(repo.url))
        results.append(clone_one(repo, dest))

    return results
