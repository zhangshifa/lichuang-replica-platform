"""自动化归纳引擎：把粘贴的项目文本/HTML 归纳成结构化 Project。

为什么需要它：
  立创开源(oshwhub)页面常被反爬/登录墙拦截，平台无法稳定地「自动抓取」。
  但用户在浏览器里能正常打开项目页 —— 只需把页面里的
  「项目简介 / 硬件功能 / 软件仓库链接 / BOM / 复刻步骤」选中复制，
  粘贴进 GUI，本模块即可自动归纳出结构化信息并生成归档文档。

归纳策略（全部为启发式，best-effort，能归纳多少算多少）：
  1) 源码仓库：正则匹配 github/gitee/gitlab/codeberg 链接。
  2) 开源协议：正则匹配常见 License 关键字。
  3) 章节切分：按 硬件 / 软件 / 材料 / 复刻 / BOM / 特性 / 功能 等标题分段。
  4) 硬件特性：特性/功能/硬件 章节下的条目(以 - * • 或数字 开头)。
  5) BOM：识别含 序号/名称/位号/封装/数量 表头的 Markdown 表格并解析行。
  6) 复刻步骤：复刻/步骤/制作/教程 章节下的条目。
  7) 简介：取首段作为 summary。
"""

from __future__ import annotations

import re
from typing import List, Optional

from .models import BomItem, Project, SourceRepo

SRC_RE = re.compile(
    r"(https?://(?:www\.)?(?:github\.com|gitee\.com|gitlab\.com|codeberg\.org)"
    r"[^\s\"'<>)\]]+)",
    re.I,
)
LIC_RE = re.compile(
    r"(MIT|Apache[- ]?2\.0|GPL[- ]?v?3\.0?|GPL[- ]?v?2\.0?|GPL|AGPL|LGPL|BSD[- ]?(?:2|3)[- ]?Clause|"
    r"MPL[- ]?2\.0|CC[- ]?BY[- ]?(?:NC|SA|ND)?[- ]?(?:[0-9]\.[0-9])?|Unlicense|ISC|"
    r"知识共享(署名|非商业|相同方式))",
    re.I,
)
OSH_RE = re.compile(r"oshwhub\.com/([A-Za-z0-9_-]+)/([A-Za-z0-9_-]+)")

# 章节标题关键字 -> 角色
SECTION_ROLES = {
    "硬件": "hardware",
    "特性": "hardware",
    "功能": "hardware",
    "接口": "hardware",
    "规格": "hardware",
    "软件": "software",
    "固件": "software",
    "源码": "software",
    "代码": "software",
    "材料": "materials",
    "物料": "materials",
    "采购": "materials",
    "复刻": "replication",
    "步骤": "replication",
    "制作": "replication",
    "教程": "replication",
    "搭建": "replication",
    "bom": "bom",
    "清单": "bom",
}

BULLET_RE = re.compile(r"^\s*(?:[-*•·◦]|[0-9]+[.、)])\s+(.*)$")
HEADING_RE = re.compile(r"^[ \t]*(?:#{1,6}\s*|【|\[)(.+?)(?:】|\])\s*$", re.M)
H2_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.M)


def _clean(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip()


def _split_sections(text: str) -> List[tuple]:
    """返回 [(role_or_None, heading, body), ...]，按出现顺序。"""
    # 找到所有标题位置
    positions = []
    for m in H2_RE.finditer(text):
        positions.append((m.start(), m.group(1).strip()))
    # 也识别「【xxx】」形式
    for m in re.finditer(r"【(.+?)】", text):
        positions.append((m.start(), m.group(1).strip()))
    positions.sort(key=lambda x: x[0])

    sections = []
    for i, (pos, heading) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        body = text[pos:end]
        role = None
        hl = heading.lower()
        for kw, r in SECTION_ROLES.items():
            if kw.lower() in hl:
                role = r
                break
        sections.append((role, heading, body))
    if not sections:
        # 整段作为一个无名章节
        sections.append((None, "", text))
    return sections


def _extract_bullets(body: str) -> List[str]:
    out = []
    for line in body.splitlines():
        m = BULLET_RE.match(line)
        if m:
            out.append(_clean(m.group(1)))
    return out


def _parse_bom_table(text: str) -> List[BomItem]:
    """从文本中找 Markdown 表格，识别含 BOM 表头的表并解析。"""
    items: List[BomItem] = []
    # 按表格块切分（连续 | 行）
    blocks = re.findall(r"(?:\|.*\|\n?)+", text)
    for block in blocks:
        rows = [r.strip().strip("|").split("|") for r in block.strip().splitlines() if r.strip()]
        if len(rows) < 2:
            continue
        header = [h.strip().lower() for h in rows[0]]
        # 判断是否为 BOM 表（表头含名称/位号/封装/数量/型号 之一）
        if not any(k in " ".join(header) for k in ("名称", "位号", "封装", "数量", "型号", "name", "designator", "footprint", "qty", "quantity")):
            continue
        # 跳过分隔行（| --- |）
        data_rows = [r for r in rows[1:] if not all(set(c.strip()) <= set("-: ") for c in r)]
        # 建立列索引
        def idx(*names):
            for n in names:
                for i, h in enumerate(header):
                    if n in h:
                        return i
            return None

        i_name = idx("名称", "name", "元件")
        i_desig = idx("位号", "designator")
        i_fp = idx("封装", "footprint", "封装类型")
        i_qty = idx("数量", "qty", "quantity")
        i_mp = idx("型号", "manufacturer part", "规格", "model")
        i_mf = idx("制造商", "manufacturer")
        i_sup = idx("供应商", "supplier")
        i_sp = idx("供应商料号", "supplier part", "料号")
        for r in data_rows:
            if max(i_name or 0, i_desig or 0, i_qty or 0) is None and i_name is None:
                continue
            get = lambda i: r[i].strip() if (i is not None and i < len(r)) else ""

            def g(i):
                return r[i].strip() if (isinstance(i, int) and 0 <= i < len(r)) else ""

            items.append(
                BomItem(
                    name=g(i_name),
                    designator=g(i_desig),
                    footprint=g(i_fp),
                    quantity=g(i_qty),
                    manufacturer_part=g(i_mp),
                    manufacturer=g(i_mf),
                    supplier=g(i_sup),
                    supplier_part=g(i_sp),
                )
            )
    return items


def analyze(content: str, url: str = "", title: str = "") -> Project:
    """从粘贴文本归纳出 Project。content 可为纯文本或 HTML（自动去标签）。"""
    text = _strip_html(content)
    p = Project(url=url or "")
    # owner / project
    if url:
        m = OSH_RE.search(url)
        if m:
            p.owner, p.project = m.group(1), m.group(2)

    # 标题
    if title:
        p.title = title.strip()
    else:
        p.title = _guess_title(text, p)

    # 源码仓库
    seen = set()
    for u in SRC_RE.findall(text):
        u = u.rstrip("/").replace(".git", "") + ".git"
        if "oshwhub.com" in u:
            continue
        if u in seen:
            continue
        seen.add(u)
        repo = SourceRepo(url=u, priority="primary")
        p.source_repos.append(repo)

    # 开源协议
    ml = LIC_RE.search(text)
    if ml:
        p.license = _normalize_license(ml.group(1))

    sections = _split_sections(text)

    # 硬件特性：在 hardware 章节下的条目
    hw_features: List[str] = []
    sw_repos_extra: List[str] = []
    rep_steps: List[str] = []
    bom_items: List[BomItem] = _parse_bom_table(text)

    for role, heading, body in sections:
        bullets = _extract_bullets(body)
        if role == "hardware":
            hw_features.extend(bullets)
        elif role == "replication":
            rep_steps.extend(bullets)
        # 软件章节里若含仓库链接已在上面统一收集；此处仅收集正文
        # 把软件章节的条目也作为 vendor 提示（非链接）
        if role == "software":
            # 提取软件章节里提到的其他 github/gitee 行（已在 SRC_RE 收集）
            pass

    # 去重
    hw_features = _dedupe(hw_features)
    rep_steps = _dedupe(rep_steps)

    if hw_features:
        p.hardware["features"] = hw_features[:30]
        p.hardware["schematic_format"] = "立创 EDA 工程（由平台归纳，请在立创页面确认）"
        p.hardware["pcb_open"] = True
    if rep_steps:
        p.replication_steps = rep_steps[:20]

    # 简介：首段（去掉标题/空行）
    p.summary = _guess_summary(text, p)

    # BOM
    if bom_items:
        p.bom = bom_items[:200]
        p.bom_note = f"已从粘贴内容中自动解析出 {len(bom_items)} 行 BOM。"
    else:
        p.bom_note = "未在粘贴内容中识别到 BOM 表格；可在立创开源项目页导出 BOM 后补充到 manifest。"

    # 把归纳结果也存入 extra，便于回溯
    p.extra["analyzed_by"] = "analyzer.analyze (自动化归纳)"
    p.extra["section_count"] = len(sections)
    return p


def _strip_html(html: str) -> str:
    if "<" not in html:
        return html
    # 去掉 script/style
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"&nbsp;", " ", html)
    html = re.sub(r"&amp;", "&", html)
    html = re.sub(r"&lt;", "<", html)
    html = re.sub(r"&gt;", ">", html)
    return html


def _guess_title(text: str, p: Project) -> str:
    # 1) 形如 「xxx - 立创开源」/「xxx | 嘉立创」取第一段
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # 去掉 markdown 标题符号
        m = re.match(r"^#{1,6}\s+(.+)$", line)
        cand = m.group(1).strip() if m else line
        # 排除明显是描述的长句
        if 2 <= len(cand) <= 40 and "立创" not in cand[:6]:
            return cand
    if p.owner and p.project:
        return f"{p.owner}/{p.project}"
    return "未命名开源项目"


def _guess_summary(text: str, p: Project) -> str:
    # 取第一个像「项目简介」的段落，长度 20~400（忽略标题行/列表/表格/元数据行）
    paras = [t.strip() for t in re.split(r"\n\s*\n", text) if t.strip()]
    for para in paras:
        lines = [ln for ln in para.splitlines() if not re.match(r"^#{1,6}\s+", ln.strip())]
        body = " ".join(lines).strip()
        if not body or "|" in body:
            continue
        # 跳过明显的元数据行（作者/许可证/链接等），它们不是简介
        if re.search(r"许可证|license|作者[：:]|github\.com|gitee\.com", body, re.I):
            continue
        if 20 <= len(body) <= 400:
            return body
    return ""


def _normalize_license(raw: str) -> str:
    r = raw.strip()
    low = r.lower().replace("_", " ")
    mapping = {
        "mit": "MIT",
        "apache 2.0": "Apache-2.0",
        "apache-2.0": "Apache-2.0",
        "gpl 3.0": "GPL-3.0",
        "gpl 3": "GPL-3.0",
        "gpl v3": "GPL-3.0",
        "gplv3": "GPL-3.0",
        "gpl 2.0": "GPL-2.0",
        "gpl 2": "GPL-2.0",
        "gpl v2": "GPL-2.0",
        "gplv2": "GPL-2.0",
        "agpl": "AGPL-3.0",
        "lgpl": "LGPL",
        "bsd 2 clause": "BSD-2-Clause",
        "bsd 3 clause": "BSD-3-Clause",
        "mpl 2.0": "MPL-2.0",
        "isc": "ISC",
        "unlicense": "Unlicense",
    }
    for k, v in mapping.items():
        if k in low:
            return v
    if low.startswith("gpl"):
        return "GPL（版本未指定）"
    if low.startswith("cc") or "知识共享" in low:
        return "CC（详见项目页）"
    return r


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for it in items:
        k = it.lower()
        if k in seen or not it:
            continue
        seen.add(k)
        out.append(it)
    return out
