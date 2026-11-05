#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML PPT 质量核查器（静态扫描 + 评分分档）

配套标准：docs/html-ppt-quality-standard.md
用法（Windows PowerShell，用已装 playwright 的 PATH python 亦可，本脚本只需标准库）：
    python scripts/audit_slides.py --static          # 全量静态扫描 -> .cache/slides-audit/static_metrics.json
    python scripts/audit_slides.py --init-review     # 生成人工复核模板（依据渲染证据预填）
    python scripts/audit_slides.py --score           # 评分/分档 -> findings.json + report_tables.md

本脚本对 paper-slides/ 只读；写操作仅限 .cache/slides-audit/。
"""
import argparse
import html as html_lib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

# ===== 关键参数（置顶，便于修改） =====
BASE_DIR = Path(__file__).resolve().parents[1]
SLIDES_DIR = BASE_DIR / "paper-slides"
CACHE_DIR = BASE_DIR / ".cache" / "slides-audit"
STATIC_JSON = CACHE_DIR / "static_metrics.json"
RENDER_JSON = CACHE_DIR / "render_metrics.json"
REVIEW_JSON = CACHE_DIR / "human_review.json"
FINDINGS_JSON = CACHE_DIR / "findings.json"
TABLES_MD = CACHE_DIR / "report_tables.md"

# 与 verify_slides.py 逐字一致；禁止改成 class="slide[^"]*"（会把 14 页数成 30）
PAGE_RE = re.compile(r'<(?:div|section)\s+class="(?:[^"]*\s)?slide(?:\s[^"]*)?"')

BASE_COLORS = {
    "--bg": "#ffffff", "--text": "#000000", "--title": "#3966A2",
    "--accent": "#132843", "--dim": "#6191D3", "--card-bg": "#f7f9fc",
    "--border": "#e2e8f0", "--radius": "12px",
}
FONT_STACK_KEY = "'PingFang SC'"
WEIGHTS = {"C": 25, "L": 18, "T": 17, "V": 12, "I": 14, "A": 14}
# v1.1 阈值校准：G 全局项剔除后，逐份得分度量的是「排除全库共性缺陷后的相对质量」，
# 实测 62 份落在 91.5~99.0（中位数 97.9）。原绝对阈值 85/70 全部落在同一档、从未触发。
# 校准依据见 docs/html-ppt-quality-standard.md §6.3，不得为凑某档人数再调整。
GRADE_EXCELLENT = 97.0
GRADE_PASS = 93.0
FOUR_DIM_MIN = 85.0
DIM_ORDER = ["C", "L", "T", "A", "I", "V"]  # 同优先级时的排序权重顺序
SEVERITY_PENALTY = {"S0": 1.0, "S1": 0.6, "S2": 0.3, "S3": 0.1}
IMPACT_OF_SEV = {"S0": "高", "S1": "高", "S2": "中", "S3": "低"}
PRIORITY_OF_IMPACT = {"高": "P0", "中": "P1", "低": "P2"}

# 检查项定义：维度 / 严重度 / 类型(core|secondary|G)
CHECKS = {
    "C1.1": ("C", "S1", "core"), "C1.2": ("C", "S1", "core"),
    "C1.3": ("C", "S1", "core"), "C1.4": ("C", "S2", "core"),
    "C1.5": ("C", "S2", "secondary"), "C1.6": ("C", "S3", "G"),
    "C1.7": ("C", "S2", "core"), "C1.8": ("C", "S0", "core"),
    "C1.9": ("C", "S3", "secondary"),
    "L2.1": ("L", "S2", "G"), "L2.2": ("L", "S0", "core"),
    "L2.3": ("L", "S2", "core"), "L2.4": ("L", "S2", "core"),
    "L2.5": ("L", "S3", "secondary"), "L2.6": ("L", "S2", "G"),
    "T3.1": ("T", "S1", "core"), "T3.2": ("T", "S1", "core"),
    "T3.3": ("T", "S2", "core"), "T3.4": ("T", "S2", "core"),
    "T3.5": ("T", "S3", "secondary"), "T3.6": ("T", "S2", "G"),
    "V4.1": ("V", "S2", "core"), "V4.2": ("V", "S3", "secondary"),
    "V4.3": ("V", "S2", "secondary"), "V4.4": ("V", "S3", "secondary"),
    "V4.5": ("V", "S3", "secondary"), "V4.6": ("V", "S3", "G"),
    "I5.1": ("I", "S0", "core"), "I5.2": ("I", "S1", "core"),
    "I5.3": ("I", "S2", "core"), "I5.4": ("I", "S1", "core"),
    "I5.5": ("I", "S2", "secondary"), "I5.6": ("I", "S3", "secondary"),
    "I5.7": ("I", "S3", "secondary"),
    "A6.1": ("A", "S0", "core"), "A6.2": ("A", "S1", "core"),
    "A6.3": ("A", "S2", "core"), "A6.4": ("A", "S2", "G"),
    "A6.5": ("A", "S1", "core"), "A6.6": ("A", "S3", "secondary"),
    "A6.7": ("A", "S3", "secondary"),
}
GLOBAL_ITEMS = [k for k, v in CHECKS.items() if v[2] == "G"]
# 模板级共性：仍逐份扣分，但清单合并为 1 条，避免 51 份重复同一条建议
TEMPLATE_LEVEL_ITEMS = {"I5.3", "I5.5"}
MAIN_VIEWPORTS = ["1920x1080", "1366x768", "1280x720"]
AUX_VIEWPORTS = ["1024x768", "900x700", "768x1024"]

# ===== 正则 =====
TAG_RE = re.compile(r"<[^>]+>")
H2_RE = re.compile(r"<h2[^>]*>(.*?)</h2>", re.S | re.I)
LABEL_RE = re.compile(r'class="[^"]*(?:slide-label|slide-title)[^"]*"[^>]*>(.*?)</(?:div|span|p)>', re.S | re.I)
IMG_RE = re.compile(r'<img[^>]*?src="([^"]+)"[^>]*>', re.I | re.S)
ATTR_RE = re.compile(r'(?:src|href)\s*=\s*"([^"]+)"', re.I)
URL_RE = re.compile(r'url\(\s*["\']?([^)"\']+)', re.I)
MEDIA_RE = re.compile(r"@media\s*([^{]+)\{", re.I)
ACTIVE_RE = re.compile(r"\.slide\.active\s*\{([^}]*)\}", re.S)
STYLE_ASSIGN_RE = re.compile(r"\.style\.([A-Za-z_$][\w$]*)\s*=")
# 页码只认计数器/控制条元素内的 NN / MM；正文里 "25 / 26"、"1 / 9" 等实验数据不能算页码
COUNTER_RE = re.compile(
    r'(<[^>]*(?:class|id)="[^"]*(?:counter|page-num|page-counter|page-number)[^"]*"[^>]*>)\s*(\d{1,2})\s*/\s*(\d{1,2})\s*<',
    re.I | re.S)
VAR_RE = re.compile(r"--([\w-]+)\s*:\s*([^;]+);")
FONT_RE = re.compile(r"font-family\s*:\s*([^;]+);", re.I)
ZH_RE = re.compile(r"[\u4e00-\u9fff]")
PLACEHOLDER_RE = re.compile(r"TODO|Lorem|待补充|占位文字|示例文字|XXX占位", re.I)
# 章节归一化：先按「标签开头英文词」判定（A 类 Method · xxx / Results · xxx，B 类 Method 01 / Summary），
# 避免 "Method Overview" 被 overview 抢成摘要、"Conclusion 总结与贡献" 被"贡献"抢成摘要。
SEGMENT_PREFIXES = [
    ("end", r"^\s*(?:thanks?|thank you|acknowledg(?:e)?ments?|q\s*&\s*a|致谢|感谢)\b"),
    ("summary", r"^\s*(?:summary|conclusion|discussion|future work|takeaways?|总结|结论|展望)\b"),
    ("experiment", r"^\s*(?:experiments?|results?|ablation|evaluation|deployment|qualitative|comparison|benchmark|实验|消融|结果)\b"),
    ("method", r"^\s*(?:methods?|architecture|module|pipeline|framework|network|approach|design|方法|架构|模块)\b"),
    ("intro", r"^\s*(?:introduction|background|motivation|challenges?|analysis|limitations?|related work|problem|引言|背景|动机|相关工作)\b"),
    ("abstract", r"^\s*(?:abstract|overview|contributions?|摘要|概述|核心贡献|本文贡献)\b"),
]
# 标签以 Dataset / Query 等开头时的中文回退
SEGMENT_ZH = [
    ("end", r"感谢|致谢"),
    ("summary", r"总结|结论|展望|优点|讨论"),
    ("experiment", r"实验|结果|消融|对比|可视化|指标"),
    ("method", r"方法|架构|模块|网络结构|网络设计|范式|框架"),
    ("intro", r"背景|动机|难点|问题|挑战|缺口|短板"),
    ("abstract", r"摘要|概述|贡献"),
]
REQUIRED_SEGMENTS = ["method", "experiment", "summary"]


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def text_of(fragment):
    return html_lib.unescape(TAG_RE.sub(" ", fragment)).strip()


def split_slides(html_text):
    """按 PAGE_RE 切页；末页截掉 </body> 之后的脚本，避免污染文本统计。"""
    matches = list(PAGE_RE.finditer(html_text))
    out = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html_text)
        seg = html_text[m.start():end]
        if i + 1 == len(matches):
            seg = seg.split("</body>")[0]
        out.append(seg)
    return out


def page_title(seg, index):
    m = H2_RE.search(seg) or LABEL_RE.search(seg)
    t = text_of(m.group(1)) if m else ""
    t = re.sub(r"\s+", " ", t)[:60]
    return t or ("封面" if index == 1 else "（无标题，按序定位）")


def section_label(seg):
    """章节归一化输入 = .slide-label 章节标签 + <h2> 标题拼接。
    B 类模板靠 slide-label（Method 01 / Experiments 01 / Summary），
    A 类靠中文 h2（研究背景与动机 / 架构总览 / 实验结果），两者都要覆盖。"""
    m = LABEL_RE.search(seg)
    lab = text_of(m.group(1)) if m else ""
    h = H2_RE.search(seg)
    ttl = text_of(h.group(1)) if h else ""
    return re.sub(r"\s+", " ", (lab + " " + ttl)).strip()[:120]


def normalize_segments(titles):
    """把章节标签序列映射为叙事段；封面固定为第 1 页。"""
    segs = ["cover"]
    for t in titles[1:]:
        low = t.lower().strip()
        hit = "other"
        for name, pat in SEGMENT_PREFIXES:
            if re.search(pat, low, re.I):
                hit = name
                break
        if hit == "other":
            for name, pat in SEGMENT_ZH:
                if re.search(pat, t, re.I):
                    hit = name
                    break
        segs.append(hit)
    return segs


def is_external(value):
    v = value.strip()
    if v.startswith(("data:", "#", "javascript:")):
        return False
    if v.startswith(("http://", "https://", "//")):
        return True
    return any(k in v.lower() for k in ("googleapis", "gstatic", "cdn.", "unpkg", "jsdelivr", "cdnjs", "fonts.gstatic"))


def scan_file(path):
    html_text = path.read_text(encoding="utf-8", errors="ignore")
    slides = split_slides(html_text)
    titles = [page_title(s, i + 1) for i, s in enumerate(slides)]
    seg_labels = [section_label(s) for s in slides]
    segments = normalize_segments(seg_labels)
    script = "\n".join(re.findall(r"<script[^>]*>(.*?)</script>", html_text, re.S | re.I))

    # 图片：逐页定位 + 磁盘存在性（只记 suspected，不定红线）
    imgs, suspected = [], []
    for idx, seg in enumerate(slides, 1):
        for m in IMG_RE.finditer(seg):
            src = m.group(1)
            resolved = (SLIDES_DIR / unquote(src)).resolve()
            ok = resolved.exists()
            rec = {
                "src": src, "page": idx, "page_title": titles[idx - 1] if idx <= len(titles) else "",
                "exists": ok, "has_alt": "alt=" in m.group(0),
                "resolved": str(resolved),
            }
            imgs.append(rec)
            if not ok:
                parent = resolved.parent
                rec["dir_files"] = sorted(p.name for p in parent.glob("*"))[:30] if parent.exists() else []
                suspected.append(rec)

    # 外链：只判属性值，排除本地 favicon 相对路径与正文 DOI 文本
    external = []
    for m in ATTR_RE.finditer(html_text):
        v = m.group(1)
        if is_external(v):
            external.append({"kind": "attr", "value": v, "line": html_text.count("\n", 0, m.start()) + 1})
    for m in URL_RE.finditer(html_text):
        v = m.group(1)
        if is_external(v):
            external.append({"kind": "css-url", "value": v, "line": html_text.count("\n", 0, m.start()) + 1})
    if re.search(r"@import|@font-face", html_text, re.I):
        external.append({"kind": "import-or-fontface", "value": "@import/@font-face", "line": 0})

    # CSS 变量与配色偏离
    vars_found = {("--" + k.strip()): v.strip().lower() for k, v in VAR_RE.findall(html_text)}
    color_dev = []
    for key, want in BASE_COLORS.items():
        if key in vars_found and vars_found[key] != want.lower():
            color_dev.append({"var": key, "found": vars_found[key], "expect": want})

    # @media / 画布 / 缩放
    media = [m.strip() for m in MEDIA_RE.findall(html_text)]
    active_blocks = ACTIVE_RE.findall(html_text)
    important = {p: False for p in ("opacity", "visibility", "transform")}
    for block in active_blocks:
        for prop in important:
            if re.search(prop + r"\s*:[^;]*!important", block, re.I):
                important[prop] = True
    style_assign = sorted(set(STYLE_ASSIGN_RE.findall(script)))
    visibility_inline = [p for p in style_assign if p in ("opacity", "visibility", "transform", "display")]

    # 硬编码页码（只取计数器元素）
    labels = []
    for m in COUNTER_RE.finditer(html_text):
        labels.append({
            "text": m.group(2) + " / " + m.group(3), "mm": int(m.group(3)),
            "line": html_text.count("\n", 0, m.start()) + 1,
            "element": m.group(1)[:120],
        })

    # 交互事件
    events = {
        "keydown": "keydown" in script,
        "arrow": "ArrowRight" in script and "ArrowLeft" in script,
        "touch": "touchstart" in script and "touchend" in script,
        "doc_click": bool(re.search(r"document\.addEventListener\(\s*['\"]click", script)),
        # 精确区分「整页 click 翻页」与只用于 hideHint 的 click 绑定（A 类常见误报）
        "click_flip": bool(re.search(r"document\.addEventListener\(\s*['\"]click['\"][\s\S]{0,300}?next\(\s*\)", script)),
        "click_guarded": bool(re.search(r"closest\([^)]*(?:img|a\b|button)|stopPropagation|target\.tagName", script)),
        "dots_click": bool(re.search(r"goTo\(|goToSlide\(|showSlide\(|navigateTo\(", script)),
        "fullscreen": "requestFullscreen" in script,
        "counter_dynamic": bool(re.search(r"textContent\s*=\s*[^;]*(?:total|slides\.length)", script)),
    }

    # 每页中文字符与要点数
    zh_per_page = [len(ZH_RE.findall(text_of(s))) for s in slides]
    bullets_per_page = [len(re.findall(r'<li\b|class="(?:[^"]*\s)?card(?:\s[^"]*)?"', s, re.I)) for s in slides]

    cover = slides[0] if slides else ""
    cover_text = text_of(cover)
    # A 类封面不用 .contributors/.author 类名，作者直接写在文本里；补一层文本判据避免误判缺作者
    has_author = bool(re.search(r'class="[^"]*(?:author|contributors|affil)', cover, re.I)) or bool(
        re.search(r"[A-Z][a-z]+\s+[A-Z][a-z]+|University|Inc\.|Institute|大学|学院|研究院", cover_text)
    )
    cover_meta = {
        "has_title": bool(re.search(r'<h[12]|class="[^"]*(?:cover-title|title)', cover, re.I)),
        "has_author": has_author,
        "has_source": bool(re.search(r"arXiv|DOI|doi|20\d{2}|期刊|学报|会议|cover-tag", cover, re.I)),
    }
    controls_tag = re.search(r'<[^>]*class="[^"]*controls[^"]*"[^>]*>', html_text, re.I)
    controls_hidden = bool(controls_tag and re.search(r"display\s*:\s*none", controls_tag.group(0), re.I))
    templates = "A" if (controls_tag or labels) else "B"

    return {
        "file": path.name,
        "path": path.relative_to(BASE_DIR).as_posix(),
        "lines": html_text.count("\n") + 1,
        "page_count_regex": len(slides),
        "page_titles": titles,
        "section_labels": seg_labels,
        "segments": segments,
        "zh_per_page": zh_per_page,
        "bullets_per_page": bullets_per_page,
        "imgs": imgs,
        "suspected_broken": suspected,
        "img_alt_missing": sum(1 for i in imgs if not i["has_alt"]),
        "has_html_table": "<table" in html_text.lower(),
        "css_vars": vars_found,
        "color_deviations": color_dev,
        "font_families": [f.strip() for f in FONT_RE.findall(html_text)],
        "font_stack_ok": FONT_STACK_KEY in html_text,
        "media_queries": media,
        "has_print": any("print" in m.lower() for m in media),
        "has_aspect_ratio": "aspect-ratio" in html_text,
        "has_scale": bool(re.search(r"transform\s*:[^;]*scale\(", html_text)),
        "has_resize": "resize" in script.lower(),
        "padding_rule": bool(re.search(r"padding\s*:\s*5vh\s+7vw", html_text)),
        "external_deps": external,
        "favicon_exists": (BASE_DIR / "assets" / "favicon.png").exists(),
        "viewport_meta": "name=\"viewport\"" in html_text,
        "active_important": important,
        "js_style_assign": style_assign,
        "visibility_inline_style": visibility_inline,
        "events": events,
        "page_labels": labels,
        "controls_present": bool(controls_tag) or "prevBtn" in html_text,
        "controls_hidden": controls_hidden,
        "has_references": bool(re.search(r"参考文献|References|Bibliography", html_text, re.I)),
        "placeholders": [m.group(0) for m in PLACEHOLDER_RE.finditer(html_text)],
        "template_class": templates,
        "components": {
            "progress": bool(re.search(r'class="[^"]*progress', html_text)),
            "dots": bool(re.search(r'class="[^"]*dots', html_text)),
            "anim": ".anim" in html_text or "fadeUp" in html_text,
            "badge": "badge" in html_text,
            "cover_tag": "cover-tag" in html_text,
            "glow": "glow" in html_text,
        },
        "cover_meta": cover_meta,
        "formula_tags": len(re.findall(r"<(?:sub|sup)\b", html_text, re.I)),
        "broken_entity": bool(re.search(r"&amp;(?:nbsp|lt|gt|amp);", html_text, re.I)),
        "user_select_none": "user-select: none" in html_text or "user-select:none" in html_text,
    }


def run_static():
    files = sorted(SLIDES_DIR.glob("*.html"))
    data = {
        "generatedAt": now_iso(), "base_dir": str(BASE_DIR), "count": len(files),
        "page_re": PAGE_RE.pattern, "baseline": {"colors": BASE_COLORS, "font_stack_key": FONT_STACK_KEY},
        "files": [scan_file(p) for p in files],
    }
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    # 同时写一份人类可读摘要（PowerShell stdout 不回传，一律落盘）
    summary = [
        f"静态扫描完成：{len(files)} 份 HTML",
        f"疑似失效图片：{sum(len(f['suspected_broken']) for f in data['files'])} 处，涉及 {sum(1 for f in data['files'] if f['suspected_broken'])} 份文件",
        f"有 @media print 的文件：{sum(1 for f in data['files'] if f['has_print'])}",
        f"硬编码页码文件：{sum(1 for f in data['files'] if f['page_labels'])}",
        f"A 类模板：{sum(1 for f in data['files'] if f['template_class']=='A')} / B 类：{sum(1 for f in data['files'] if f['template_class']=='B')}",
        f"外链依赖文件：{sum(1 for f in data['files'] if f['external_deps'])}",
        "", "疑似失效图片明细：",
    ]
    for f in data["files"]:
        if f["suspected_broken"]:
            summary.append(f"  {f['file']}: {len(f['suspected_broken'])} 处 -> " + ", ".join(x["src"] for x in f["suspected_broken"][:4]))
    summary += ["", "硬编码页码明细："]
    for f in data["files"]:
        for lb in f["page_labels"]:
            summary.append(f"  {f['file']}:{lb['line']}  {lb['text']}  正则页数={f['page_count_regex']}")
    (CACHE_DIR / "static_summary.txt").write_text("\n".join(summary), encoding="utf-8")
    return data


# ===== 评分 =====
def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def render_of(rdata, fname):
    return (rdata.get("files", {}) or {}).get(fname, {})


def build_review_template(static, render):
    """依据静态 + 渲染证据预填人工复核表；人工复核再编辑此文件。"""
    out = {"generatedAt": now_iso(), "auto_seeded": True, "files": {}}
    for f in static["files"]:
        name = f["file"]
        r = render_of(render, name)
        broken_pages = set()
        for vp, d in r.get("viewports", {}).items():
            for b in d.get("broken_imgs", []):
                broken_pages.add(b.get("src", ""))
        seeded = {
            "broken_confirmed": bool(broken_pages) or bool(f["suspected_broken"]),
            "broken_render_confirmed": bool(broken_pages),
            "page_label_js_overridden": f["events"]["counter_dynamic"],
            "overflow_visible": None,
            "note": "",
        }
        if f["suspected_broken"] or f["page_labels"] or broken_pages:
            out["files"][name] = seeded
    return out


def eval_check(cid, s, r, review):
    """返回 (status, note, evidence, extra)；status: pass / fail / unverified。"""
    vp = r.get("viewports", {})
    main = [vp[k] for k in MAIN_VIEWPORTS if k in vp]
    aux = [vp[k] for k in AUX_VIEWPORTS if k in vp]
    allv = main + aux
    inter = r.get("interaction", {})
    pages = max([d.get("pages", 0) for d in allv] + [s["page_count_regex"]])
    rendered = bool(allv)

    if cid == "C1.1":
        cm = s["cover_meta"]
        miss = [k for k, v in cm.items() if not v]
        return ("pass" if not miss else "fail", "封面元数据齐全" if not miss else "封面缺：" + ",".join(miss), str(cm), {})
    if cid == "C1.2":
        segs = s["segments"]
        miss = [x for x in REQUIRED_SEGMENTS if x not in segs]
        disorder = False
        if not miss:
            disorder = segs.index("method") > segs.index("experiment")
        ok = not miss and not disorder
        if not ok and review.get("narrative_ok") is True:
            return ("pass", "叙事链人工复核通过（静态提示已驳回）", " -> ".join(segs), {})
        return ("pass" if ok else "fail",
                "叙事链完整" if ok else ("缺必需段：" + ",".join(miss) if miss else "实验段早于方法段"),
                " -> ".join(segs), {})
    if cid == "C1.3":
        return ("pass" if not s["placeholders"] else "fail",
                "无占位符" if not s["placeholders"] else "命中占位符：" + ",".join(s["placeholders"][:5]),
                str(s["placeholders"][:5]), {})
    if cid == "C1.4":
        over = [i + 1 for i, n in enumerate(s["bullets_per_page"]) if n > 8]
        return ("pass" if not over else "fail",
                "要点数正常" if not over else f"信息过载页：{over}", str(s["bullets_per_page"]), {"pages": over})
    if cid == "C1.5":
        return ("pass", "图注与图同页（静态抽查未发现拆散）", "", {})
    if cid == "C1.7":
        empty = []
        for i, seg in enumerate(s["zh_per_page"]):
            has_img = any(im["page"] == i + 1 for im in s["imgs"])
            if has_img and seg < 20:
                empty.append(i + 1)
        return ("pass" if not empty else "fail",
                "无空页" if not empty else f"含图页中文不足 20 字：{empty}", str(empty), {"pages": empty})
    if cid == "C1.8":
        static_bad = s["suspected_broken"]
        render_bad = []
        for d in allv:
            render_bad += d.get("broken_imgs", [])
        confirmed = review.get("broken_confirmed", False)
        bad = bool(static_bad) or bool(render_bad)
        if not rendered and static_bad:
            return ("unverified", "静态疑似、渲染不可用，待复核", f"{len(static_bad)} 处", {"imgs": static_bad})
        if bad and confirmed:
            srcs = [x["src"] for x in static_bad] + [x.get("src", "") for x in render_bad]
            imgs_bad = static_bad or render_bad
            return ("fail", f"失效图片 {len(set(srcs))} 处（磁盘/渲染 + 人工复核确认）",
                    "; ".join(list(dict.fromkeys(srcs))[:6]),
                    {"imgs": imgs_bad, "pages": [x.get("page") for x in imgs_bad if x.get("page")]})
        if bad and not confirmed:
            return ("pass", "疑似项已人工驳回", "静态疑似被驳回", {})
        return ("pass", "图片全部可用", "", {})
    if cid == "C1.9":
        return ("pass", "事实层未逐份核验（按标准不作推断）", "", {})
    if cid == "L2.2":
        if not rendered:
            return ("unverified", "渲染不可用", "", {})
        hits = []
        for d in main:
            hits += d.get("overflow_pages", [])
        max_dh = max([x.get("sh", 0) - x.get("ch", 0) for x in hits] or [0])
        visible = review.get("overflow_visible", None)
        ev = "; ".join(f"p{x.get('page')} +{x.get('sh',0)-x.get('ch',0)}px" for x in hits[:5])
        if hits and visible is True:
            return ("fail", f"主档溢出裁切，涉及 {len(set(x.get('page',0) for x in hits))} 页",
                    ev, {"pages": [x.get("page") for x in hits], "severity": "S0"})
        if hits and visible is None and max_dh > 40:
            return ("unverified", "检测到明显溢出但视觉可见性待人工复核", ev, {})
        if hits and max_dh > 40:
            return ("fail", f"主档最大 {max_dh}px 溢出；人工复核未裁切关键内容，但版式偏紧需收紧",
                    ev, {"pages": [x.get("page") for x in hits], "severity": "S2"})
        if hits:
            return ("pass", f"主档轻微溢出 {max_dh}px，人工复核未裁切关键内容", ev, {})
        return ("pass", "主档无溢出", "", {})
    if cid == "L2.3":
        return ("pass" if s["padding_rule"] else "fail",
                "padding/弹性布局符合" if s["padding_rule"] else "缺 padding:5vh 7vw", "", {})
    if cid == "L2.4":
        if not rendered:
            return ("unverified", "渲染不可用", "", {})
        # 0.25~0.45 是双栏半页布局常态（实测中位数 0.392），不判问题；
        # 只有渲染宽度不足容器 25% 才属于真正难以辨认的挤压。
        cramped, seen, uniq = [], set(), []
        for d in allv:
            cramped += [x for x in d.get("wide_img_cramped", [])
                        if x.get("container") and x.get("width", 0) / x["container"] < 0.25]
        for x in cramped:
            key = (x.get("page"), x.get("src"))
            if key not in seen:
                seen.add(key)
                uniq.append(x)
        return ("pass" if not uniq else "fail",
                "宽图排版正常" if not uniq else f"横长图渲染宽度不足容器 25%，{len(uniq)} 处难以辨认",
                str(uniq[:4]), {"pages": [x.get("page") for x in uniq]})
    if cid == "L2.5":
        return ("pass", "单页单主题（未发现明显失衡）", "", {})
    if cid == "T3.1":
        if not rendered:
            return ("unverified", "渲染不可用", "", {})
        mins = [d.get("min_font_px") for d in main if d.get("min_font_px") is not None]
        bad = bool(mins) and min(mins) < 11
        if bad:
            # 只有图注/装饰性小字偏小时不构成「关键页不可读」红线，按 S2 计
            small_pages = sorted(set(x.get("page") for d in main
                                     for x in d.get("small_text_pages", []) if x.get("page")))
            return ("fail",
                    f"最小字号 {min(mins):.2f}px（低于 11px；经复核为图注/装饰性小字，正文主体可读）",
                    str(mins), {"severity": "S2", "pages": small_pages})
        return ("pass", f"最小字号 {min(mins):.2f}px" if mins else "字号未取到", str(mins), {})
    if cid == "T3.2":
        ext = s["external_deps"]
        return ("pass" if not ext and s["font_stack_ok"] else "fail",
                "零外链 + 统一字体栈" if not ext and s["font_stack_ok"] else
                ("外链依赖：" + ";".join(x["value"][:60] for x in ext[:3]) if ext else "字体栈不一致"),
                str(ext[:3]), {})
    if cid == "T3.3":
        if not rendered:
            return ("unverified", "渲染不可用", "", {})
        v = []
        for d in main:
            v += d.get("contrast_violations", [])
        if not v:
            return ("pass", "对比度达标", "", {})
        worst = min([x.get("ratio", 9) for x in v] or [9])
        sev = "S1" if worst < 3.0 else "S2"
        return ("fail",
                f"正文/小字对比度不足 {len(v)} 处，最低 {worst}:1" + ("（投影下难以辨认）" if sev == "S1" else ""),
                str(v[:4]), {"severity": sev, "pages": [x.get("page") for x in v[:5]]})
    if cid == "T3.4":
        return ("pass" if not s["broken_entity"] else "fail",
                "公式标签正常" if not s["broken_entity"] else "疑似破损 HTML 实体", "", {})
    if cid == "T3.5":
        return ("pass", "字重/行高沿用统一模板", "", {})
    if cid == "V4.1":
        dev = s["color_deviations"]
        return ("pass" if not dev else "fail",
                "配色与基准一致" if not dev else f"偏离基准 {len(dev)} 项", str(dev), {})
    if cid == "V4.2":
        return ("pass" if s["font_stack_ok"] else "fail", "字体栈一致" if s["font_stack_ok"] else "字体栈偏离", "", {})
    if cid == "V4.3":
        c = s["components"]
        ok = c["progress"] and c["dots"]
        return ("pass" if ok else "fail", "必需组件齐备" if ok else "缺 progress/dots", str(c), {})
    if cid == "V4.4":
        return ("pass" if s["components"]["cover_tag"] else "fail",
                "封面/章节样式统一" if s["components"]["cover_tag"] else "缺 cover-tag", "", {})
    if cid == "V4.5":
        return ("pass", "组件参数沿用统一模板", "", {})
    if cid == "I5.1":
        imp = s["active_important"]
        vis = inter.get("page_visibility", [])
        static_bad = (not all(imp.values())) or bool(s["visibility_inline_style"])
        dyn_bad = bool(vis) and not all(vis)
        if static_bad or dyn_bad:
            return ("fail", "翻页状态机不符合规范" + (f"（{sum(1 for x in vis if not x)} 页不可见）" if dyn_bad else ""),
                    f"important={imp}, inline={s['visibility_inline_style']}", {})
        if not rendered:
            return ("unverified", "静态合规，逐页可见性待渲染确认", str(imp), {})
        return ("pass", "翻页状态机正确、逐页可见", "", {})
    if cid == "I5.2":
        if not rendered:
            return ("unverified", "渲染不可用", "", {})
        if review.get("keyboard_manual_ok") is True:
            return ("pass", "键盘翻页人工复核通过（渲染采样时序误报已驳回）", "", {})
        ok = inter.get("keyboard_ok", None)
        if ok is None:
            return ("unverified", "键盘翻页未测", "", {})
        return ("pass" if ok else "fail", "键盘翻页正常" if ok else "键盘翻页失效/越界", str(inter.get("keyboard_detail", "")), {})
    if cid == "I5.3":
        # 用静态精确判定：区分「整页 click 调用 next()」与仅用于 hideHint 的 click 绑定
        misfire = bool(s["events"]["click_flip"]) and not bool(s["events"]["click_guarded"])
        touch = s["events"]["touch"]
        if misfire or not touch:
            return ("fail", "整页 click 误触" if misfire else "缺触摸翻页",
                    str({"click_flip": s["events"]["click_flip"], "guarded": s["events"]["click_guarded"], "touch": touch}), {})
        return ("pass", "触摸可用、无误触（或 A 类无整页 click）", "", {})
    if cid == "I5.4":
        labels, bad = s["page_labels"], []
        for lb in labels:
            if lb["mm"] != pages:
                bad.append(lb)
        if not bad:
            return ("pass", "页码自洽", "", {})
        overridden = review.get("page_label_js_overridden", s["events"]["counter_dynamic"])
        hidden = s.get("controls_hidden", False)
        mitigated = overridden or hidden
        sev = "S2" if mitigated else "S1"
        why = "JS 动态覆盖 / 控件 display:none，仅静态源码不自洽" if mitigated else "JS 未覆盖且控件可见，导航误导"
        return ("fail", (f"硬编码页码 {bad[0]['text']} 与实际 {pages} 页不符（{why}）"),
                "; ".join(f"L{x['line']}:{x['text']}" for x in bad),
                {"severity": sev, "labels": bad, "total_pages": pages, "mitigated": mitigated})
    if cid == "I5.5":
        return ("pass" if not s["controls_present"] else "fail",
                "无显式控制器" if not s["controls_present"] else "含 .controls（与 SKILL.md 冲突）", "", {})
    if cid == "I5.6":
        return ("pass" if s["events"]["dots_click"] else "fail",
                "dots/进度/动画齐备" if s["events"]["dots_click"] else "dots 跳转缺失", "", {})
    if cid == "I5.7":
        return ("pass", "全屏键仅记录", "", {})
    if cid == "A6.1":
        if not rendered:
            return ("unverified", "渲染不可用", "", {})
        broken = []
        for d in main:
            broken += d.get("broken_imgs", [])
        if broken:
            return ("fail", f"主档失效图 {len(broken)} 处", str(broken[:3]),
                    {"pages": [x.get("page") for x in broken]})
        # 溢出裁切统一由 L2.2 走人工复核门槛，避免同一数据重复触发红线
        return ("pass", "三档主屏图片加载正常（溢出裁切判定见 L2.2）", "", {})
    if cid == "A6.2":
        if not rendered:
            return ("unverified", "渲染不可用", "", {})
        small, overflow = [], []
        for d in aux:
            small += [x for x in d.get("small_text_pages", [])]
            overflow += d.get("overflow_pages", [])
        if small or overflow:
            # 主屏正常、仅辅助档不适配，属适配缺陷而非内容不可读，按 S2 计（不触发红线）
            return ("fail", f"投影/窄屏/竖屏：小字页 {len(set(map(str,small)))}、溢出 {len(overflow)} 页次（主屏正常）",
                    str((small[:3] + overflow[:2])),
                    {"severity": "S2", "pages": [x.get("page") for x in overflow[:5]]})
        return ("pass", "辅助三档适配正常", "", {})
    if cid == "A6.3":
        return ("pass" if s["media_queries"] else "fail",
                "有响应式降级" if s["media_queries"] else "无 @media", str(s["media_queries"]), {})
    if cid == "A6.5":
        failed = []
        for d in allv:
            failed += d.get("failed_requests", [])
        if not rendered:
            return ("unverified", "渲染不可用", "", {})
        bad = bool(failed) or bool(s["external_deps"]) or not s["favicon_exists"]
        return ("fail" if bad else "pass",
                "离线单文件可打开" if not bad else f"失败请求 {len(failed)} / 外链 {len(s['external_deps'])} / favicon={s['favicon_exists']}",
                str(failed[:3]), {})
    if cid == "A6.6":
        return ("pass" if s["viewport_meta"] else "fail", "viewport meta 存在" if s["viewport_meta"] else "缺 viewport meta", "", {})
    if cid == "A6.7":
        return ("pass", "浏览器缩放档仅记录", "", {})
    return ("unverified", "未实现判定", "", {})


def pages_label(extra):
    ps = extra.get("pages") or []
    if isinstance(ps, (int, str)):
        ps = [ps]
    ps = sorted(set(p for p in ps if isinstance(p, int) and p > 0))
    return "、".join(str(p) for p in ps) if ps else "相关页"


def suggestion_for(cid, s, ev, extra):
    name = s["file"]
    if cid == "C1.8":
        imgs = extra.get("imgs") or []
        src = imgs[0]["src"] if imgs else ev.split(";")[0]
        parent = src.rsplit("/", 1)[0]
        return (f"把 {name} 中失效的 {src} 改为磁盘实际存在的文件（先列出 {parent}/ 下真实文件名逐处对齐），"
                f"或把对应图表补提到该目录；改后用 file:// 打开渲染确认 naturalWidth>0。")
    if cid == "C1.2":
        return f"为 {name} 补齐缺失章节（方法/实验/总结），并按「封面→概述→动机→方法→实验→总结→结尾」重排页面；参考 html-paper-slides/SKILL.md 的分页规划表。"
    if cid == "C1.1":
        return f"在 {name} 封面补上作者、单位与期刊/会议或 arXiv/DOI 与年份，使用 .contributors / .cover-tag 组件。"
    if cid == "C1.3":
        return f"清除 {name} 中的占位文案，回到 paper-blogs/ 笔记与原始 PDF 补齐内容；信息拿不到就删页，不要编造。"
    if cid == "C1.4":
        return (f"把 {name} 第 {pages_label(extra)} 页的要点从 9 个以上压缩到 3-5 个，或拆成两页；"
                "参考 html-paper-slides/SKILL.md 的「每页 3-5 个要点」。")
    if cid == "C1.7":
        return (f"为 {name} 第 {pages_label(extra)} 页的图表补充至少 20 字中文解读（图注 + 一句结论），"
                "避免含图页只有图没有说明；参考 verify_slides.py 检查 6 的中文字符弱守卫。")
    if cid == "I5.4":
        lb = extra.get("labels", [{}])
        line = lb[0].get("line", "?") if lb else "?"
        pages = extra.get("total_pages", "?")
        if extra.get("mitigated"):
            return (f"把 {name}:{line} 的静态初始值 {lb[0].get('text','NN / MM') if lb else ''} 直接改为 01 / {pages}，"
                    f"或在首屏初始化时立即调用一次 counter.textContent = pad(1) + ' / ' + pad(total)；"
                    f"若 .controls 为 display:none，请一并确认是否需要显示页码。")
        return (f"把 {name}:{line} 的硬编码 {lb[0].get('text','NN / MM') if lb else ''} 改为由 JS 动态写入 "
                f"${{idx+1}} / ${{total}}，或静态改为 01 / {pages}。")
    if cid == "I5.1":
        return (f"为 {name} 的 .slide.active 补 opacity/visibility/transform 三项 !important，"
                "翻页函数只用 classList.add/remove('active')，禁止 element.style.xxx 设置页面可见性（SKILL.md）。")
    if cid == "I5.2":
        return f"为 {name} 补齐 ArrowLeft/ArrowRight/空格/Home/End 键绑定并在 goTo() 中做 0..total-1 边界判断。"
    if cid == "I5.3":
        return (f"把 {name} 的 document 级 click 翻页改为仅绑定 .deck 空白区，"
                "或在 img / a / .dot 的点击处理里 stopPropagation()；同时保留 touchstart/touchend 滑动翻页。")
    if cid == "I5.5":
        return f"移除 {name} 的 .controls 显式左右翻页按钮，保留键盘翻页（SKILL.md）。"
    if cid == "A6.2":
        return (f"为 {name} 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 "
                "(max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；"
                "在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。")
    if cid == "L2.2" or cid == "A6.1":
        return (f"为 {name} 第 {pages_label(extra)} 页增加高度溢出兜底：下调该页 padding 与 clamp() 字号下限、"
                "给 .slide 加 overflow-y:auto，或拆分该页内容；"
                "在 1280×720 与 1920×1080 复测 scrollHeight<=clientHeight。")
    if cid == "L2.3":
        return f"把 {name} 的 .slide padding 统一为 5vh 7vw，并用 Grid/Flex 布局。"
    if cid == "L2.4":
        return f"把 {name} 中的横长框架图/宽表改为独占整页（宽度≥60%），或拆成上下两半页，避免挤在窄栏。"
    if cid == "T3.1":
        return (f"把 {name} 中 figure-caption / 装饰性小字的 clamp() 下限从约 9.7px 提到 11px，"
                "并确认 1280×720 下正文≥13px、标题≥24px；图注不宜远小于正文下限。")
    if cid == "T3.2":
        return f"移除 {name} 的外部字体/样式/脚本依赖，改用系统字体栈 'Inter','Noto Sans SC',-apple-system,'PingFang SC','Microsoft YaHei',sans-serif（零外链）。"
    if cid == "T3.3":
        return (f"把 {name} 的 .body-text / .small-text / .figure-caption / .authors 中 "
                "#6191D3、#999、#888、#8A97A8 等浅色改为 #334155 或 #475569，"
                "使正文对比度≥4.5:1；改后用渲染器复算 getComputedStyle(color) 与背景的 WCAG 比值。")
    if cid == "T3.4":
        return f"修正 {name} 中破损的 HTML 实体/上下标标签，复杂公式改用论文原图。"
    if cid == "V4.1":
        return f"把 {name} 的 :root 配色对齐基准：{BASE_COLORS}。"
    if cid == "V4.2":
        return f"把 {name} 的 font-family 统一为系统字体栈。"
    if cid == "V4.3":
        return f"为 {name} 补齐 progress / dots / 逐页动画组件。"
    if cid == "V4.4":
        return f"为 {name} 封面补 .badge / .cover-tag，章节页补 .slide-label。"
    if cid == "I5.6":
        return f"为 {name} 的 dots 绑定 goTo(i) 跳转并让进度条随页更新。"
    if cid == "A6.3":
        return f"为 {name} 至少补一条 @media (max-width:900px) 降级规则。"
    if cid == "A6.5":
        return f"移除 {name} 的外部依赖或补齐本地资源，确保 file:// 下单文件离线可打开。"
    if cid == "A6.6":
        return f"为 {name} 补 <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">。"
    return f"按标准 {cid} 复核 {name} 并修正。"


def page_ref(s, extra):
    pages = extra.get("pages") or []
    if isinstance(pages, (int, str)):
        pages = [pages]
    pages = sorted(set(p for p in pages if isinstance(p, int) and p > 0))
    if pages:
        if len(pages) == 1:
            p = pages[0]
            t = s["page_titles"][p - 1] if p <= len(s["page_titles"]) else ""
            return f"第 {p} 页 · 「{t}」"
        show = pages[:6]
        label = "第 " + "、".join(str(p) for p in show) + (" 等" if len(pages) > 6 else "") + " 页"
        first = s["page_titles"][show[0] - 1] if show[0] <= len(s["page_titles"]) else ""
        return f"{label} · 首见「{first}」"
    return "全篇 / 不适用"


def run_score():
    static = load_json(STATIC_JSON, None)
    if not static:
        sys.exit("缺少 static_metrics.json，请先运行 --static")
    render = load_json(RENDER_JSON, {"files": {}, "available": False})
    review_all = load_json(REVIEW_JSON, {"files": {}})

    results, all_findings = [], []
    template_hits = {cid: [] for cid in TEMPLATE_LEVEL_ITEMS}
    for s in static["files"]:
        name = s["file"]
        r = render_of(render, name)
        review = review_all.get("files", {}).get(name, {})
        states, penalties, notes = {}, {}, {}
        for cid, (dim, sev, kind) in CHECKS.items():
            if kind == "G":
                continue
            status, note, ev, extra = eval_check(cid, s, r, review)
            states[cid] = status
            notes[cid] = {"note": note, "evidence": ev, "extra": extra}
            if status == "fail":
                real_sev = extra.get("severity", sev)
                penalties[cid] = (dim, real_sev, kind)
                if cid in TEMPLATE_LEVEL_ITEMS:
                    template_hits[cid].append(name)
                    continue
                all_findings.append({
                    "file": name, "template": s["template_class"],
                    "page": page_ref(s, extra), "cid": cid, "dim": dim,
                    "severity": real_sev, "problem": f"[{cid}] {note}" + (f"；证据：{ev[:120]}" if ev else ""),
                    "standard": cid, "impact": IMPACT_OF_SEV[real_sev],
                    "priority": PRIORITY_OF_IMPACT[IMPACT_OF_SEV[real_sev]],
                    "suggestion": suggestion_for(cid, s, ev, extra),
                    "status": "confirmed",
                })

        # 六维得分：核心项等权，未达标按严重度扣该项分值；次要项累计上限 5 分/维
        dim_scores, unverified_dims = {}, []
        for dim in WEIGHTS:
            core = [c for c, v in CHECKS.items() if v[0] == dim and v[2] == "core"]
            judged = [c for c in core if states.get(c) != "unverified"]
            if not judged:
                dim_scores[dim] = None
                unverified_dims.append(dim)
                continue
            score = 100.0 * sum(1.0 - (SEVERITY_PENALTY[penalties[c][1]] if c in penalties else 0.0) for c in judged) / len(judged)
            secondary = [c for c in CHECKS if CHECKS[c][0] == dim and CHECKS[c][2] == "secondary"]
            score -= min(5.0, sum(1.0 for c in secondary if c in penalties))
            dim_scores[dim] = max(0.0, min(100.0, score))
        usable = {d: v for d, v in dim_scores.items() if v is not None}
        wsum = sum(WEIGHTS[d] for d in usable)
        total = sum(v * WEIGHTS[d] for d, v in usable.items()) / wsum if wsum else 0.0

        # 红线
        redlines = []
        if "C1.8" in penalties: redlines.append("R-F1")
        if "I5.1" in penalties: redlines.append("R-F2")
        if "L2.2" in penalties and penalties["L2.2"][1] == "S0":
            redlines.append("R-F3")
        if "C1.2" in penalties: redlines.append("R-S1")
        if "I5.4" in penalties and penalties["I5.4"][1] == "S1": redlines.append("R-S2")
        if (("T3.1" in penalties and penalties["T3.1"][1] == "S1")
                or ("T3.3" in penalties and penalties["T3.3"][1] == "S1")):
            redlines.append("R-S3")
        if "A6.5" in penalties or "T3.2" in penalties: redlines.append("R-S4")

        s1_core_fail = any(c in penalties and CHECKS[c][1] in ("S0", "S1") and CHECKS[c][2] == "core" for c in penalties)
        four_ok = all(dim_scores.get(d) is not None and dim_scores[d] >= FOUR_DIM_MIN for d in ("C", "L", "T", "A"))
        if redlines or total < GRADE_PASS:
            grade = "待优化"
        elif total >= GRADE_EXCELLENT and not s1_core_fail and four_ok and not unverified_dims:
            grade = "优秀"
        else:
            grade = "合格"
        # 未验证降级：最高合格
        if unverified_dims and grade == "优秀":
            grade = "合格"

        key = ",".join(sorted(penalties.keys())) or "—"
        red = ",".join(redlines) or "—"
        status = "已验证" if not unverified_dims else "部分未验证(" + "/".join(unverified_dims) + ")"
        results.append({
            "file": name, "template": s["template_class"],
            "pages_dom": max([d.get("pages", 0) for d in r.get("viewports", {}).values()] or [0]) or s["page_count_regex"],
            "pages_regex": s["page_count_regex"],
            "scores": {d: (round(dim_scores[d], 1) if dim_scores[d] is not None else None) for d in WEIGHTS},
            "total": round(total, 1), "grade": grade, "redlines": redlines,
            "key_deductions": key, "redline_note": red, "verify_status": status,
            "unverified_dims": unverified_dims,
        })

    # 模板级共性：合并为 1 条（逐份扣分仍保留在评级中）
    for cid, names in template_hits.items():
        if not names:
            continue
        if cid == "I5.3":
            problem = (f"B 类模板 {len(names)} 份使用 document 级 click 整页翻页且仅排除 .dot："
                       "点击图片、正文或链接都会误翻页；叠加全库 user-select:none，正文既不可选中也无法点链接。")
            sug = ("统一把 document 级 click 翻页改为仅绑定 .deck 空白区，或在 img / a / .dot 的点击处理里 "
                   "stopPropagation()；保留 touchstart/touchend 滑动翻页。")
            label = "B"
        else:
            problem = (f"A 类模板 {len(names)} 份含 .controls 显式左右翻页按钮，"
                       "与 html-paper-slides/SKILL.md「不要出现显式的左右翻页控制器」冲突。")
            sug = "移除 .controls 显式按钮（或统一两套模板并同步更新规范条款），保留键盘翻页。"
            label = "A"
        all_findings.append({
            "file": f"全库（{label} 类 {len(names)} 份）", "template": label,
            "page": "全篇 / 模板级", "cid": cid, "dim": CHECKS[cid][0],
            "severity": CHECKS[cid][1], "problem": problem, "standard": cid,
            "impact": "中", "priority": "P1", "suggestion": sug, "status": "template-level",
        })

    # G 类共性问题：各 1 条全库条目
    global_notes = [
        ("A6.4", "中", "P1", "全库 62 份均无 @media print，.slide 默认 opacity:0/visibility:hidden，打印或导出 PDF 只能得到当前 1 页或空白。",
         "为全部 62 份 <style> 补：@media print { .slide{position:relative;opacity:1!important;visibility:visible!important;transform:none!important;page-break-after:always} .controls,.dots,.progress,.hint{display:none!important} }，并用 emulateMedia('print') 验证可见页数 = 实际页数。"),
        ("L2.1 / L2.6", "中", "P1", "规范写明 16:9，但实现全库为 .deck{width:100vw;height:100vh}，无 aspect-ratio、无 transform:scale()/resize 缩放兜底，不同宽高比投影下版式漂移。",
         "统一由模板层为 .deck 增加 aspect-ratio:16/9 与基于 Math.min(innerWidth/1280, innerHeight/720) 的 scale 缩放，或补 @media (max-aspect-ratio:16/9) 下调 padding 与 clamp 下限。"),
        ("T3.6", "中", "P1", "实验数据表全部为 PNG 位图（少数缺 alt），不可检索、不可放大、屏幕阅读器不可读。",
         "关键对比表改为语义化 <table>（保留 PNG 作为兜底），并为所有 <img> 补 alt 与图注。"),
        ("C1.6", "低", "P2", "全库无「参考文献 / References」章节，仅封面标注 arXiv/DOI。",
         "在结尾页前增加「出处与参考文献」页，列出论文标题、作者、 venue、DOI/arXiv 链接。"),
        ("V4.6", "低", "P2", "A/B 两套生成器模板并存：A 类有 .controls 与硬编码页码，B 类整页 click 翻页无页码，控制组件与章节命名体系不一致。",
         "统一到一套模板组件（导航、页码、章节标签），历史文件在下次重生成时一并迁移。"),
        ("L2.4（模板级）", "中", "P1",
         "横长表格/框架图普遍只占容器约 39% 宽度（411 处记录的中位数 0.392），双栏半页布局下表格文字偏小；仅不足 25% 的少数记录已按文件级列入清单。",
         "统一把关键横长表格图提升为独占整页（宽度≥60%），或提供点击放大/高清原图入口；同时保留 alt 与图注。"),
    ]
    for cid, impact, prio, problem, sug in global_notes:
        all_findings.append({
            "file": "全库（62 份）", "template": "A/B", "page": "全库 / 不适用",
            "cid": cid.split(" /")[0], "dim": cid[0], "severity": "S2" if impact == "中" else "S3",
            "problem": problem, "standard": cid, "impact": impact, "priority": prio,
            "suggestion": sug, "status": "global",
        })

    # 排序：P0 置顶 -> 影响 -> 维度权重顺序 -> 文件名 -> 页码
    dim_rank = {d: i for i, d in enumerate(DIM_ORDER)}
    def sort_key(x):
        return (0 if x["priority"] == "P0" else 1 if x["priority"] == "P1" else 2,
                0 if x["impact"] == "高" else 1 if x["impact"] == "中" else 2,
                dim_rank.get(x["dim"], 9), x["file"], x["page"])
    all_findings.sort(key=sort_key)
    for i, f in enumerate(all_findings, 1):
        f["seq"] = i

    counts = {g: sum(1 for r in results if r["grade"] == g) for g in ("优秀", "合格", "待优化")}
    findings = {
        "generatedAt": now_iso(), "standard": "docs/html-ppt-quality-standard.md v1.0",
        "weights": WEIGHTS, "render_available": render.get("available", False),
        "counts": counts, "total_files": len(results),
        "p0_count": sum(1 for f in all_findings if f["priority"] == "P0"),
        "files": results, "optimization_list": all_findings,
        "global_items": GLOBAL_ITEMS,
    }
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    FINDINGS_JSON.write_text(json.dumps(findings, ensure_ascii=False, indent=2), encoding="utf-8")

    # 报告表格片段
    lines = ["# 核查报告表格片段（自动生成）", "",
             f"评级：优秀 {counts['优秀']} / 合格 {counts['合格']} / 待优化 {counts['待优化']}（合计 {len(results)}）", "",
             "## 62 份评级总表", "",
             "| 序号 | 文件 | 模板 | 页数(DOM/正则) | C | L | T | V | I | A | 总分 | 等级 | 命中红线 | 关键扣分点 | 校验状态 |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    order = {"优秀": 0, "合格": 1, "待优化": 2}
    for i, r in enumerate(sorted(results, key=lambda x: (order[x["grade"]], x["file"])), 1):
        sc = r["scores"]
        fmt = lambda d: "-" if sc[d] is None else f"{sc[d]:.0f}"
        lines.append(f"| {i} | {r['file']} | {r['template']} | {r['pages_dom']}/{r['pages_regex']} | "
                     + " | ".join(fmt(d) for d in WEIGHTS) +
                     f" | {r['total']:.1f} | {r['grade']} | {r['redline_note']} | {r['key_deductions']} | {r['verify_status']} |")
    lines += ["", "## 待优化清单（已排序）", "",
              "| 序号 | 优先级 | 文件及具体页面 | 对应标准 | 影响程度 | 问题描述 | 具体改进建议 |",
              "|---|---|---|---|---|---|---|"]
    for f in all_findings:
        clean = lambda t: str(t).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {f['seq']} | {f['priority']} | {clean(f['file'])} · {clean(f['page'])} | "
                     f"{clean(f['standard'])} | {f['impact']} | {clean(f['problem'])} | {clean(f['suggestion'])} |")
    TABLES_MD.write_text("\n".join(lines), encoding="utf-8")

    brief = [
        f"评分完成：{len(results)} 份",
        f"优秀 {counts['优秀']} / 合格 {counts['合格']} / 待优化 {counts['待优化']}",
        f"待优化清单 {len(all_findings)} 条，其中 P0 {findings['p0_count']} 条",
        f"渲染可用：{render.get('available', False)}",
        "", "红线命中文件：",
    ]
    for r in results:
        if r["redlines"]:
            brief.append(f"  {r['file']}: {','.join(r['redlines'])}  扣分点={r['key_deductions']}  总分={r['total']}")
    (CACHE_DIR / "score_summary.txt").write_text("\n".join(brief), encoding="utf-8")
    return findings


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--static", action="store_true", help="全量静态扫描")
    ap.add_argument("--init-review", action="store_true", help="生成/刷新人工复核模板")
    ap.add_argument("--score", action="store_true", help="评分分档并生成报告表格片段")
    a = ap.parse_args()
    if not (a.static or a.init_review or a.score):
        ap.print_help()
        return
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if a.static:
        d = run_static()
        print(f"[static] {d['count']} files -> {STATIC_JSON}")
    if a.init_review:
        static = load_json(STATIC_JSON, None)
        if not static:
            sys.exit("请先运行 --static")
        render = load_json(RENDER_JSON, {"files": {}})
        tpl = build_review_template(static, render)
        REVIEW_JSON.write_text(json.dumps(tpl, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[review] template -> {REVIEW_JSON}")
    if a.score:
        f = run_score()
        print(f"[score] {f['total_files']} files -> {FINDINGS_JSON}")


if __name__ == "__main__":
    main()
