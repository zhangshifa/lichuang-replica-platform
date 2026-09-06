"""立创开源(oshwhub.com)项目抓取。

策略：
  1) 优先用 --manifest 传入已由人工/AI 提取好的 JSON（最稳，规避反爬与登录墙）。
  2) 否则尝试直接 HTTP 抓取页面，正则提取标题/简介/源码仓库链接。
  3) 抓取失败抛出清晰指引，提示改用 manifest 模式。
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Optional

from .models import BomItem, Project, SourceRepo

OSHWHUB_RE = re.compile(r"oshwhub\.com/([A-Za-z0-9_-]+)/([A-Za-z0-9_-]+)")
SRC_RE = re.compile(r"(https?://(?:github\.com|gitee\.com|gitlab\.com)[^\s\"'<>]+)", re.I)


def parse_url(url: str):
    """从立创开源链接解析 owner / project。"""
    m = OSHWHUB_RE.search(url)
    if not m:
        raise ValueError(f"无法从链接解析立创开源项目: {url}")
    return m.group(1), m.group(2)


def fetch_http(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def extract_from_html(html: str, url: str) -> Project:
    owner, proj = parse_url(url)
    p = Project(platform="oshwhub", owner=owner, project=proj, url=url)
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if m:
        p.title = m.group(1).split("|")[0].strip()
    m = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', html, re.I)
    if m:
        p.summary = m.group(1).strip()
    for u in SRC_RE.findall(html):
        if "oshwhub.com" in u:
            continue
        p.source_repos.append(SourceRepo(url=u.rstrip("/").replace(".git", "") + ".git"))
    return p


def load_manifest(path: str) -> Project:
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    p = Project(
        platform=d.get("platform", "oshwhub"),
        owner=d.get("owner", ""),
        project=d.get("project", ""),
        url=d.get("url", ""),
        title=d.get("title", ""),
        author=d.get("author", ""),
        summary=d.get("summary", ""),
        license=d.get("license", ""),
        hardware=d.get("hardware", {}),
        bom_note=d.get("bom_note", ""),
        replication_steps=d.get("replication_steps", []),
        extra=d.get("extra", {}),
    )
    for r in d.get("source_repos", []):
        p.source_repos.append(
            SourceRepo(url=r["url"], desc=r.get("desc", ""), priority=r.get("priority", "primary"))
        )
    for r in d.get("vendor_deps", []):
        p.vendor_deps.append(
            SourceRepo(url=r["url"], desc=r.get("desc", ""), priority="vendor")
        )
    for b in d.get("bom", []):
        p.bom.append(BomItem(**{k: b.get(k, "") for k in BomItem.fields()}))
    if not p.owner or not p.project:
        try:
            o, pr = parse_url(p.url)
            p.owner, p.project = o, pr
        except Exception:
            pass
    return p


def fetch_project(url: str, manifest_path: Optional[str] = None) -> Project:
    if manifest_path:
        return load_manifest(manifest_path)
    try:
        html = fetch_http(url)
        return extract_from_html(html, url)
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"自动抓取失败（{e}）。立创开源页面常含反爬/登录墙，请改用 manifest 模式：\n"
            f"  1) 用浏览器或 AI 提取项目信息保存为 manifest.json；\n"
            f"  2) 运行 replica_cli.py {url} --manifest manifest.json"
        )
