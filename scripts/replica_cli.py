#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""立创开源智能复刻平台 —— 命令行入口。

用法示例：
  # 1) 直接用立创开源链接（自动抓取，可能受反爬限制）
  python scripts/replica_cli.py https://oshwhub.com/flyn/helixlink

  # 2) 用已提取的 manifest（最稳，规避登录墙/反爬）
  python scripts/replica_cli.py https://oshwhub.com/flyn/helixlink \
      --manifest examples/HelixLink/manifest.json --name HelixLink

  # 3) 仅生成文档、不实际克隆（离线可用）
  python scripts/replica_cli.py <url> --manifest manifest.json --no-clone

零外部依赖，Python 3.9+。
"""

import argparse
import os
import sys

# 让脚本可直接 import src 包
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.lichuang_replica import run_pipeline  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="立创开源智能复刻平台：链接 -> 抓取硬件/原理图/BOM -> 克隆源码 -> 归档 -> 生成中文技术设计文档"
    )
    ap.add_argument("url", help="立创开源项目链接，如 https://oshwhub.com/owner/project")
    ap.add_argument("--manifest", help="已提取的项目信息 JSON（绕过反爬/登录墙）")
    ap.add_argument("--name", help="示例目录名（默认取 owner_project）")
    ap.add_argument("--out", default=ROOT, help="输出根目录（默认仓库根）")
    ap.add_argument("--no-clone", action="store_true", help="仅生成文档，不克隆源码")
    args = ap.parse_args(argv)

    try:
        result = run_pipeline(
            args.url,
            args.out,
            manifest=args.manifest,
            name=args.name,
            no_clone=args.no_clone,
        )
    except RuntimeError as e:
        print(f"[错误] {e}", file=sys.stderr)
        return 2

    proj = result["project"]
    print("\n✅ 流水线完成")
    print(f"  项目：{proj.title}（{proj.owner}/{proj.project}）")
    print(f"  归档目录：{result['example_dir']}")
    ok = sum(1 for r in result["results"] if r.success)
    print(f"  源码克隆：{ok}/{len(result['results'])} 成功"
          + ("（--no-clone 未执行克隆）" if args.no_clone else ""))
    print("\n下一步：")
    print("  - 阅读 examples/ 下生成的硬件/软件/材料/文档")
    print("  - 用 scripts/github_push.py 推送到 GitHub（需设置 GITHUB_TOKEN 环境变量）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
