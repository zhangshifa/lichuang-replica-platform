#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键复现示例：用 HelixLink 的 manifest 生成归档目录（不联网克隆）。

用于演示平台能力、生成可推送的目录，而不依赖实时网络。
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.lichuang_replica import run_pipeline  # noqa: E402

MANIFEST = os.path.join(ROOT, "examples", "HelixLink", "manifest.json")
URL = "https://oshwhub.com/flyn/helixlink"


def main():
    res = run_pipeline(URL, ROOT, manifest=MANIFEST, name="HelixLink", no_clone=True)
    print("示例已生成：", res["example_dir"])


if __name__ == "__main__":
    main()
