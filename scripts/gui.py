#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""立创开源智能复刻平台 —— 本地 GUI（零依赖，Python 标准库 http.server）。

启动：
    python scripts/gui.py
默认监听 http://127.0.0.1:8765

功能：
    - 粘贴立创开源项目链接，一键「自动提取并归纳」
    - 若立创反爬拦截自动抓取，可改为「粘贴项目页面文本」模式，同样自动归纳
    - 归纳出 硬件特性 / 软件仓库 / BOM / 许可证 / 复刻步骤，并生成 01~04 归档文档
    - 右侧实时预览生成的中文技术设计文档
"""

import json
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.lichuang_replica.analyzer import analyze  # noqa: E402
from src.lichuang_replica.docgen import render_example  # noqa: E402
from src.lichuang_replica.fetcher import fetch_http, parse_url  # noqa: E402
from src.lichuang_replica.models import CloneResult, Project  # noqa: E402

PORT = int(os.environ.get("GUI_PORT", "8765"))


# ----------------------------------------------------------------------------
# 核心：分析 + 生成
# ----------------------------------------------------------------------------
def do_run(url: str, content: str, title: str, do_clone: bool) -> dict:
    """分析并生成归档，返回结果字典。"""
    results = []
    if content and content.strip():
        project = analyze(content, url=url, title=title)
    elif url:
        # 尝试服务端自动抓取
        try:
            html = fetch_http(url, timeout=12)
            project = analyze(html, url=url, title=title)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 418, 429):
                raise RuntimeError(
                    "立创开源对该请求返回了拦截状态码(%s)，自动抓取被反爬/登录墙阻挡。"
                    "请在浏览器打开项目页，把「项目简介 / 硬件功能 / 软件仓库链接 / BOM / 复刻步骤」"
                    "复制粘贴到文本框，再点「用粘贴内容归纳」。" % e.code
                )
            raise RuntimeError(f"自动抓取失败：HTTP {e.code}。请改用粘贴内容模式。")
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(
                f"自动抓取失败（{e}）。请改用「粘贴项目页面文本」模式：在浏览器打开项目页复制相关内容粘贴即可。"
            )
    else:
        raise RuntimeError("请至少提供「项目链接」或「粘贴的项目内容」。")

    if not project.title or project.title == "未命名开源项目":
        if url:
            try:
                o, pr = parse_url(url)
                project.title = f"{o}/{pr}"
            except Exception:
                pass

    example_dir = os.path.join(ROOT, "examples", project.safe_name)
    if do_clone:
        # 克隆（可能较慢/被墙，失败不阻断文档生成）
        try:
            from src.lichuang_replica.cloner import clone_sources

            results = clone_sources(project, example_dir)
        except Exception as e:  # noqa: BLE001
            results = [
                CloneResult(url=r.url, success=False, error=str(e)[:200])
                for r in project.source_repos
            ]

    render_example(project, example_dir, results)

    files = []
    for root, _, fs in os.walk(example_dir):
        for f in fs:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            files.append(rel)
    files.sort()

    tech_path = os.path.join(example_dir, "04_docs", "技术设计文档.md")
    tech_doc = open(tech_path, encoding="utf-8").read() if os.path.exists(tech_path) else ""

    return {
        "ok": True,
        "project": {
            "title": project.title,
            "owner": project.owner,
            "author": project.author or project.owner,
            "license": project.license or "未识别",
            "url": project.url,
            "summary": project.summary,
            "hw_features": project.hardware.get("features", []),
            "source_repos": [r.url for r in project.source_repos],
            "vendor_deps": [r.url for r in project.vendor_deps],
            "bom_count": len(project.bom),
            "steps": project.replication_steps,
        },
        "example_dir": os.path.relpath(example_dir, ROOT).replace(os.sep, "/"),
        "files": files,
        "tech_doc": tech_doc,
        "message": f"已归纳并生成归档到 {os.path.relpath(example_dir, ROOT)}",
    }


# ----------------------------------------------------------------------------
# HTTP 处理
# ----------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # 静默
        pass

    def _send(self, code, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, INDEX_HTML.encode("utf-8"), "text/html; charset=utf-8")
        else:
            self._send(404, b"not found")

    def do_POST(self):
        if self.path != "/api/run":
            self._send(404, b"not found")
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            data = json.loads(raw.decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            self._send(400, json.dumps({"ok": False, "error": f"请求解析失败: {e}"}).encode("utf-8"))
            return

        url = (data.get("url") or "").strip()
        content = (data.get("content") or "").strip()
        title = (data.get("title") or "").strip()
        do_clone = bool(data.get("clone"))

        try:
            out = do_run(url, content, title, do_clone)
        except RuntimeError as e:
            self._send(200, json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False).encode("utf-8"))
            return
        except Exception as e:  # noqa: BLE001
            self._send(200, json.dumps({"ok": False, "error": f"处理出错: {e}"}, ensure_ascii=False).encode("utf-8"))
            return

        self._send(200, json.dumps(out, ensure_ascii=False).encode("utf-8"))


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"✅ 立创开源智能复刻平台 GUI 已启动： http://127.0.0.1:{PORT}")
    print("   按 Ctrl+C 停止。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


# ----------------------------------------------------------------------------
# 前端页面（内嵌，零外部依赖）
# ----------------------------------------------------------------------------
INDEX_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>立创开源智能复刻平台</title>
<style>
  :root{ --bg:#0f1115; --panel:#171a21; --panel2:#1f232c; --border:#2a2f3a;
         --txt:#e6e9ef; --muted:#9aa3b2; --accent:#4f8cff; --accent2:#34d399; --warn:#f59e0b; --err:#ef4444; }
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;
       background:var(--bg);color:var(--txt);font-size:14px;line-height:1.6}
  header{padding:18px 24px;border-bottom:1px solid var(--border);background:linear-gradient(180deg,#14171d,#0f1115)}
  header h1{margin:0;font-size:19px}
  header p{margin:4px 0 0;color:var(--muted);font-size:13px}
  .wrap{display:grid;grid-template-columns:420px 1fr;gap:16px;padding:16px 24px;align-items:start}
  @media(max-width:900px){.wrap{grid-template-columns:1fr}}
  .card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:16px}
  label{display:block;font-size:12px;color:var(--muted);margin:10px 0 4px}
  input[type=text],textarea{width:100%;background:var(--panel2);border:1px solid var(--border);
       color:var(--txt);border-radius:8px;padding:9px 10px;font-size:13px;font-family:inherit;outline:none}
  input[type=text]:focus,textarea:focus{border-color:var(--accent)}
  textarea{resize:vertical;min-height:150px}
  .btn{display:inline-flex;align-items:center;gap:6px;background:var(--accent);color:#fff;border:none;
       padding:9px 14px;border-radius:8px;cursor:pointer;font-size:13px;font-weight:600;margin-top:12px}
  .btn:hover{filter:brightness(1.08)}
  .btn.ghost{background:transparent;border:1px solid var(--border);color:var(--txt);font-weight:500}
  .row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
  .chk{display:flex;align-items:center;gap:6px;color:var(--muted);font-size:12px;margin-top:12px}
  .msg{padding:9px 11px;border-radius:8px;margin-top:12px;font-size:13px;display:none}
  .msg.err{background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.4);color:#fca5a5;display:block}
  .msg.ok{background:rgba(52,211,153,.10);border:1px solid rgba(52,211,153,.35);color:#6ee7b7;display:block}
  .msg.warn{background:rgba(245,158,11,.10);border:1px solid rgba(245,158,11,.35);color:#fcd34d;display:block}
  h3{margin:0 0 10px;font-size:15px}
  .kv{font-size:13px}
  .kv b{color:var(--muted);font-weight:500}
  ul.tags{list-style:none;padding:0;margin:6px 0;display:flex;flex-wrap:wrap;gap:6px}
  ul.tags li{background:var(--panel2);border:1px solid var(--border);border-radius:6px;padding:3px 8px;font-size:12px}
  .files{font-size:12px;color:var(--muted);max-height:140px;overflow:auto;border:1px solid var(--border);
         border-radius:8px;padding:8px;background:var(--panel2)}
  .files a{color:var(--accent);text-decoration:none}
  pre.doc{background:#0b0d11;border:1px solid var(--border);border-radius:10px;padding:16px;
          white-space:pre-wrap;word-break:break-word;font-family:"SFMono-Regular",Consolas,Menlo,monospace;
          font-size:12.5px;line-height:1.55;max-height:70vh;overflow:auto;margin:0}
  .badge{display:inline-block;background:var(--panel2);border:1px solid var(--border);border-radius:20px;
         padding:2px 10px;font-size:12px;color:var(--muted);margin-left:8px}
  .hint{font-size:12px;color:var(--muted);margin-top:6px}
</style>
</head>
<body>
<header>
  <h1>🔧 立创开源智能复刻平台 <span class="badge">粘贴链接 · 自动归纳软硬件 · 生成复刻文档</span></h1>
  <p>把立创开源(oshwhub.com)项目链接贴进来，平台自动提取硬件特性 / 软件源码仓库 / BOM / 许可证 / 复刻步骤，并归档为可复刻的中文技术文档。</p>
</header>

<div class="wrap">
  <!-- 左侧输入 -->
  <div class="card">
    <h3>① 输入项目</h3>
    <label>立创开源项目链接</label>
    <input type="text" id="url" placeholder="https://oshwhub.com/owner/project" />
    <div class="hint">例如 https://oshwhub.com/flyn/helixlink</div>

    <button class="btn" id="btnAuto">🚀 自动提取并归纳</button>

    <div id="fallback" style="display:none;margin-top:14px;border-top:1px dashed var(--border);padding-top:12px">
      <label>项目页面文本（自动抓取被拦截时使用）</label>
      <textarea id="content" placeholder="在浏览器打开项目页，复制「项目简介 / 硬件功能 / 软件仓库链接 / BOM / 复刻步骤」粘贴到这里"></textarea>
      <label>项目标题（可选，留空自动识别）</label>
      <input type="text" id="title" placeholder="HelixLink 多功能调试器" />
      <button class="btn ghost" id="btnPaste">📋 用粘贴内容归纳</button>
    </div>

    <label class="chk"><input type="checkbox" id="clone"/> 尝试克隆源码仓库（网络较慢/可能被墙，默认关闭）</label>

    <div class="msg" id="msg"></div>
  </div>

  <!-- 右侧结果 -->
  <div class="card">
    <h3>② 归纳结果 <span class="badge" id="dirBadge"></span></h3>
    <div id="result">
      <p class="hint">左侧点击「自动提取并归纳」后，这里会显示提取出的软硬件信息与生成的技术设计文档预览。</p>
    </div>
    <h3 style="margin-top:18px">③ 技术设计文档预览</h3>
    <pre class="doc" id="doc">（无）</pre>
  </div>
</div>

<script>
const $ = s => document.querySelector(s);
function showMsg(text, kind){
  const m = $('#msg'); m.textContent = text; m.className = 'msg ' + (kind||'');
}
async function run(payload){
  $('#result').innerHTML = '<p class="hint">处理中…</p>';
  $('#doc').textContent = '（生成中…）';
  showMsg('正在归纳分析…', 'warn');
  try{
    const r = await fetch('/api/run', {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify(payload)});
    const d = await r.json();
    if(!d.ok){ $('#fallback').style.display = (d.error||'').includes('反爬')||(d.error||'').includes('粘贴') ? 'block':'none';
      showMsg(d.error||'处理失败', 'err'); return; }
    render(d);
    showMsg(d.message||'完成', 'ok');
  }catch(e){ showMsg('请求失败：'+e, 'err'); }
}
$('#btnAuto').onclick = () => run({url:$('#url').value, content:'', title:$('#title').value, clone:$('#clone').checked});
$('#btnPaste').onclick = () => run({url:$('#url').value, content:$('#content').value, title:$('#title').value, clone:$('#clone').checked});

function render(d){
  const p = d.project;
  $('#dirBadge').textContent = d.example_dir;
  let h = '';
  h += `<div class="kv"><b>标题：</b>${esc(p.title)}</div>`;
  h += `<div class="kv"><b>作者：</b>${esc(p.author||'-')} &nbsp; <b>许可证：</b>${esc(p.license||'-')}</div>`;
  if(p.url) h += `<div class="kv"><b>链接：</b><a style="color:var(--accent)" href="${esc(p.url)}" target="_blank">${esc(p.url)}</a></div>`;
  if(p.summary) h += `<div class="kv" style="margin-top:8px"><b>简介：</b>${esc(p.summary)}</div>`;

  h += `<div style="margin-top:12px"><b style="color:var(--muted)">硬件特性（自动归纳 ${p.hw_features.length} 项）：</b><ul class="tags">` +
       p.hw_features.map(x=>`<li>${esc(x)}</li>`).join('') + `</ul></div>`;

  h += `<div style="margin-top:10px"><b style="color:var(--muted)">软件源码仓库（${p.source_repos.length}）：</b><ul class="tags">` +
       p.source_repos.map(x=>`<li>${esc(x)}</li>`).join('') + `</ul></div>`;

  if(p.vendor_deps.length) h += `<div style="margin-top:6px"><b style="color:var(--muted)">第三方依赖（${p.vendor_deps.length}）：</b><ul class="tags">` +
       p.vendor_deps.map(x=>`<li>${esc(x)}</li>`).join('') + `</ul></div>`;

  h += `<div style="margin-top:10px"><b style="color:var(--muted)">BOM：</b>${p.bom_count>0?('已解析 '+p.bom_count+' 行'):'未识别（请补充 BOM 表）'} &nbsp; `+
       `<b style="color:var(--muted)">复刻步骤：</b>${p.steps.length} 步</div>`;

  if(p.steps.length){
    h += '<ol style="margin:6px 0 0 18px;color:var(--txt);font-size:13px">'+ p.steps.map(x=>`<li>${esc(x)}</li>`).join('')+'</ol>';
  }

  h += `<div style="margin-top:14px"><b style="color:var(--muted)">已生成文件（${d.files.length}）：</b>
        <div class="files">`+ d.files.map(f=>`<div>📄 ${esc(f)}</div>`).join('') + `</div></div>`;

  $('#result').innerHTML = h;
  $('#doc').textContent = d.tech_doc || '（无）';
}
function esc(s){ return (s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
</script>
</body>
</html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
