#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把本地目录通过 GitHub REST API（Contents API）推送到 GitHub。

特点：
  * 零外部依赖（仅标准库）。
  * token 只从环境变量 GITHUB_TOKEN 读取，绝不硬编码。
  * 自动建库（若不存在），并设置中文 description 与 topics。
  * 自动避开 .git / node_modules 等，分文件提交。

用法：
  set GITHUB_TOKEN=ghp_xxx
  python scripts/github_push.py --dir . --repo lichuang-replica-platform \
      --description "立创开源智能复刻平台：粘贴链接即可自动抓取硬件/原理图/BOM、克隆开源源码、生成中文技术设计文档并归档，方便社区复刻。"
"""

import argparse
import base64
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.github.com"
EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".workbuddy", ".DS_Store", "dist", "build"}
EXCLUDE_FILES = {".DS_Store", "Thumbs.db"}


def _req(method, url, token, data=None, retry=5):
    last = None
    for attempt in range(retry):
        try:
            body = json.dumps(data).encode() if data is not None else None
            req = urllib.request.Request(url, data=body, method=method)
            req.add_header("Authorization", f"Bearer {token}")
            req.add_header("Accept", "application/vnd.github+json")
            req.add_header("User-Agent", "lichuang-replica-platform")
            if body:
                req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            last = (e.code, e.read().decode()[:300])
            if e.code in (502, 503, 504) and attempt < retry - 1:
                time.sleep(2 * (attempt + 1))
                continue
            return last
        except Exception as e:  # noqa: BLE001
            last = (0, str(e)[:300])
            if attempt < retry - 1:
                time.sleep(2)
                continue
            return last
    return last or (0, "retry exhausted")


def whoami(token):
    s, d = _req("GET", f"{API}/user", token)
    if s == 200 and isinstance(d, dict):
        return d.get("login", "")
    return ""


def create_repo(token, name, description, private=False, topics=None):
    s, d = _req("POST", f"{API}/user/repos", token, {
        "name": name,
        "description": description,
        "private": private,
        "auto_init": False,
        "has_issues": True,
        "has_wiki": False,
    })
    if s in (201, 200):
        full = d.get("full_name")
        if topics:
            _req("PUT", f"{API}/repos/{full}/topics", token, {"names": topics})
        return full
    if s == 422 and "already exist" in str(d):
        login = whoami(token)
        return f"{login}/{name}" if login else name
    raise RuntimeError(f"建库失败 {s}: {d}")


def put_file(token, repo, path, content, message, branch="main"):
    b64 = base64.b64encode(content.encode("utf-8")).decode()
    return _req("PUT", f"{API}/repos/{repo}/contents/{path}", token, {
        "message": message,
        "content": b64,
        "branch": branch,
    })


def git_blob_sha(content: str) -> str:
    """计算 git blob 的 SHA1（与 GitHub 存储的 sha 一致），用于增量跳过未变更文件。"""
    data = content.encode("utf-8")
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def get_remote_sha(token, repo, path, branch="main"):
    s, d = _req("GET", f"{API}/repos/{repo}/contents/{path}?ref={branch}", token)
    if s == 200:
        return d.get("sha")
    return None


def collect_files(local_dir):
    out = []
    for root, dirs, fnames in os.walk(local_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fn in fnames:
            if fn in EXCLUDE_FILES:
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, local_dir).replace("\\", "/")
            out.append((rel, full))
    return sorted(out)


def push_dir(token, repo_full, local_dir, message, branch="main"):
    files = collect_files(local_dir)
    ok = 0
    skip = 0
    for rel, full in files:
        try:
            with open(full, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:  # noqa: BLE001
            continue
        # 增量跳过：远程已存在且内容一致则不重复上传（避免每次重传整库）
        local_sha = git_blob_sha(content)
        remote_sha = get_remote_sha(token, repo_full, rel, branch)
        if remote_sha == local_sha:
            skip += 1
            print(f"  = {rel} (未变更，跳过)")
            ok += 1
            continue
        s, d = put_file(token, repo_full, rel, content, message, branch)
        if s in (200, 201):
            ok += 1
            print(f"  ✓ {rel}")
        else:
            msg = d.get("message", "") if isinstance(d, dict) else str(d)
            print(f"  ✗ {rel} -> {s} {msg}")
    return ok, len(files), skip


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="通过 GitHub API 推送目录")
    ap.add_argument("--dir", default=".", help="要推送的本地目录（默认当前目录）")
    ap.add_argument("--repo", required=True, help="仓库名（如 lichuang-replica-platform）")
    ap.add_argument("--description", default="", help="仓库中文描述")
    ap.add_argument("--topics", default="", help="逗号分隔的 topics")
    ap.add_argument("--message", default="feat: 立创开源智能复刻平台 初始提交")
    ap.add_argument("--branch", default="main")
    args = ap.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("[错误] 请先设置环境变量 GITHUB_TOKEN", file=sys.stderr)
        return 2

    local_dir = os.path.abspath(args.dir)
    print(f"==> 登录 GitHub：{whoami(token) or '(未知)'}")
    print(f"==> 建库 / 复用：{args.repo}")
    full = create_repo(token, args.repo, args.description, topics=[
        t.strip() for t in args.topics.split(",") if t.strip()
    ] or None)
    print(f"==> 目标仓库：{full}")
    print("==> 推送文件：")
    ok, total, skip = push_dir(token, full, local_dir, args.message, args.branch)
    print(f"\n✅ 完成：{ok}/{total} 个文件已处理（其中 {skip} 个未变更已跳过）-> https://github.com/{full}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
