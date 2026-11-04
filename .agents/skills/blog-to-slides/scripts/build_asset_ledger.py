#!/usr/bin/env python3
"""
为 blog-to-slides 生成素材账本（asset ledger）。

定位原始 PDF、抽取列感知正文、合成图片全集，并给出页数预算。
图片一律不重新提取，只复用 assets/paper-imgs/ 下已有文件。
全部产物写入 .cache/blog-to-slides/<论文名>/（gitignore，不发布到 GitHub Pages）。

依赖：pymupdf（fitz）、Pillow。缺失时先 `pip install pymupdf Pillow`。
"""
import argparse
import difflib
import json
import math
import os
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[4]
BLOGS = BASE_DIR / "paper-blogs"
IMGS = BASE_DIR / "assets" / "paper-imgs"
PDFS = BASE_DIR / "pdf-papers"
CACHE = BASE_DIR / ".cache" / "blog-to-slides"
IMG_EXT = (".png", ".jpg", ".jpeg")
STRUCT_PAGES = 7
PAGE_CAP = 30
TOP1_MIN = 0.85
MARGIN_MIN = 0.15


def norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"^\s*(?:19|20)\d{2}[\s_\-]*", "", s.strip())
    s = re.sub(r"\.pdf$", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def all_pdfs():
    return sorted(PDFS.rglob("*.pdf")) if PDFS.is_dir() else []


def blog_title(name: str):
    bp = BLOGS / f"{name}.md"
    if not bp.exists():
        return None
    m = re.search(r'^title:\s*"?(.+?)"?\s*$', bp.read_text(encoding="utf-8", errors="ignore"), re.M)
    return m.group(1).strip() if m else None


def resolve_pdf(name: str, manual: str, summary: dict):
    """三级兜底定位原始 PDF。返回 (path, resolution)。"""
    if manual:
        p = Path(manual)
        return (str(p), "manual") if p.exists() else (None, "none")
    if summary and summary.get("pdf_path") and Path(summary["pdf_path"]).exists():
        return summary["pdf_path"], "summary"
    bynorm = {norm(p.name): p for p in all_pdfs()}
    if summary and summary.get("pdf_path"):
        want = norm(Path(summary["pdf_path"]).name)
        if want in bynorm:
            return str(bynorm[want]), "filename_search"
    title = blog_title(name)
    if title:
        tn = norm(title)
        scored = sorted(
            ((difflib.SequenceMatcher(None, tn, pn).ratio(), p) for pn, p in bynorm.items()),
            reverse=True,
        )
        if scored:
            top1, p1 = scored[0]
            top2 = scored[1][0] if len(scored) > 1 else 0.0
            # 必须 top-1 + 间距：扁平阈值会把同族论文（如 cbp-yolo / gcmd-yolo）一起命中
            if top1 >= TOP1_MIN and (top1 - top2) >= MARGIN_MIN:
                return str(p1), "filename_search"
    return None, "none"


def column_text(page, fig_bboxes):
    """列感知块抽取。裸 get_text() 与 sort=True 对双栏论文均不可用（见设计文档 §5.1）。"""
    width = page.rect.width
    blocks = [b for b in page.get_text("blocks") if b[6] == 0]
    if fig_bboxes:
        def in_fig(b):
            for (x0, y0, x1, y1) in fig_bboxes:
                if b[0] < x1 + 4 and b[2] > x0 - 4 and b[1] < y1 + 4 and b[3] > y0 - 4:
                    return True
            return False
        blocks = [b for b in blocks if not in_fig(b)]
    left = [b for b in blocks if (b[0] + b[2]) / 2 < width / 2]
    right = [b for b in blocks if (b[0] + b[2]) / 2 >= width / 2]
    out = []
    for col in (left, right):
        col.sort(key=lambda b: (round(b[1] / 6), b[0]))
        out.extend(t for t in (b[4].strip() for b in col) if t)
    return "\n".join(out)


def parse_blog(name: str):
    """返回 {filename: {section, alt, note}}，按出现顺序。"""
    bp = BLOGS / f"{name}.md"
    if not bp.exists():
        return None
    refs = {}
    section = None
    lines = bp.read_text(encoding="utf-8", errors="ignore").split("\n")
    img_re = re.compile(r"!\[([^\]]*)\]\([^)]*paper-imgs/" + re.escape(name) + r"/([\w\-.]+)\)")
    for i, line in enumerate(lines):
        m = re.match(r"^(#{2,3})\s+(.*)", line)
        if m:
            section = m.group(2).strip()
        for im in img_re.finditer(line):
            after = [x.strip() for x in lines[i + 1:i + 4] if x.strip()]
            refs[im.group(2)] = {
                "section": section,
                "alt": im.group(1).strip(),
                "note": after[0] if after else "",
            }
    return refs


def build(name: str, manual: str, emit_text: bool, full_json: bool):
    d = IMGS / name
    if not d.is_dir():
        sys.exit(f"[ledger] 目录不存在：{d}")
    summ_path = d / "extraction_summary.json"
    summary = None
    if summ_path.exists():
        try:
            summary = json.loads(summ_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[ledger] 警告：extraction_summary.json 解析失败（{e}），按无 summary 处理", file=sys.stderr)

    # 基准集 = 磁盘上实际存在的图片文件（存在性唯一权威）
    disk = sorted(f for f in os.listdir(d) if f.lower().endswith(IMG_EXT)) if d.is_dir() else []
    items = {it["filename"]: it for it in (summary or {}).get("items", [])}

    pdf_path, resolution = resolve_pdf(name, manual, summary)

    pdf_pages = 0
    pdf_text = ""
    fig_pages = {}
    if pdf_path:
        import fitz
        doc = fitz.open(pdf_path)
        pdf_pages = doc.page_count
        for it in items.values():
            if isinstance(it.get("page"), int) and it.get("bbox"):
                fig_pages.setdefault(it["page"], []).append(tuple(it["bbox"]))
        pages_text = [column_text(doc[i], fig_pages.get(i + 1, [])) for i in range(pdf_pages)]
        pdf_text = "\n\n".join(pages_text)
        doc.close()

    refs = parse_blog(name)
    if refs is None:
        sys.exit(f"[ledger] 笔记不存在：{BLOGS / (name + '.md')}（本技能输入前提）")

    from PIL import Image
    images = []
    for f in disk:
        it = items.get(f)
        with Image.open(d / f) as im:
            w, h = im.size
        ratio = w / h if h else 1.0
        aspect = "wide" if ratio > 1.6 else ("tall" if ratio < 0.8 else "square")
        r = refs.get(f)
        images.append({
            "file": f,
            "type": (it or {}).get("type", "unknown"),
            "num": (it or {}).get("number"),
            "page": (it or {}).get("page"),
            "w": w,
            "h": h,
            "aspect": aspect,
            "caption": (it or {}).get("caption"),
            "caption_source": "summary" if it else "none",
            "in_blog": f in refs,
            "blog_section": r["section"] if r else None,
            "blog_caption": r["alt"] if r else None,
            "blog_note": r["note"] if r else None,
        })

    n = len(refs)
    budget = {
        "min": STRUCT_PAGES + math.ceil(n / 2),
        "max": min(STRUCT_PAGES + 1 + n, PAGE_CAP),
        "cap": PAGE_CAP,
    }
    sections = {}
    for f, r in refs.items():
        sections.setdefault(r["section"] or "(未归属)", []).append(f)

    ledger = {
        "paper": name,
        "pdf_path": pdf_path,
        "pdf_resolution": resolution,
        "pdf_pages": pdf_pages,
        "pdf_text_chars": len(pdf_text),
        "page_budget": budget,
        "extracted_count": len(disk),
        "blog_ref_count": n,
        "blog_sections": [{"section": s, "images": fs} for s, fs in sections.items()],
        "images": images,
        "unused_in_blog": sorted(set(disk) - set(refs)),
        "stale_summary_entries": sorted(set(items) - set(disk)),
        "broken_blog_refs": sorted(set(refs) - set(disk)),
    }

    out = CACHE / name
    out.mkdir(parents=True, exist_ok=True)
    (out / "asset_ledger.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "paper_text.txt").write_text(pdf_text, encoding="utf-8")

    rows = ["| 文件 | PDF页 | 尺寸 | 形态 | 博客引用 | 博客章节 | 中文图注 |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for im in images:
        rows.append(
            f"| {im['file']} | {im['page'] if im['page'] is not None else '-'} | {im['w']}x{im['h']} | {im['aspect']} "
            f"| {'是' if im['in_blog'] else '否'} | {im['blog_section'] or '-'} | {im['blog_caption'] or '-'} |"
        )
    md = [
        f"# 素材账本 · {name}",
        "",
        f"- pdf: `{pdf_path or '(未找到)'}` （resolution={resolution}）",
        f"- pdf_pages={pdf_pages}  pdf_text_chars={len(pdf_text)}",
        f"- extracted={len(disk)}  blog_refs={n}  page_budget={budget}",
        f"- stale_summary_entries={ledger['stale_summary_entries']}",
        f"- broken_blog_refs={ledger['broken_blog_refs']}",
        f"- unused_in_blog={ledger['unused_in_blog']}",
        "",
        *rows,
        "",
    ]
    (out / "asset_ledger.md").write_text("\n".join(md), encoding="utf-8")

    if emit_text:
        print(pdf_text)
    elif full_json:
        print(json.dumps(ledger, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({k: ledger[k] for k in
                          ("paper", "pdf_path", "pdf_resolution", "pdf_pages", "pdf_text_chars",
                           "page_budget", "extracted_count", "blog_ref_count",
                           "unused_in_blog", "stale_summary_entries", "broken_blog_refs")},
                         ensure_ascii=False, indent=2))
        print(f"\n[ledger] 账本已写入 {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paper")
    ap.add_argument("--pdf", help="人工指定 PDF 路径（定位第 3 级兜底）")
    ap.add_argument("--emit-text", action="store_true", help="把列感知正文打印到 stdout")
    ap.add_argument("--json", action="store_true", help="输出完整账本 JSON")
    a = ap.parse_args()
    try:
        build(a.paper, a.pdf, a.emit_text, a.json)
    except ImportError as e:
        sys.exit(f"[ledger] 缺少依赖：{e}。请先执行：pip install pymupdf Pillow")


if __name__ == "__main__":
    main()
