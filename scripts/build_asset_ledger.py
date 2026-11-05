#!/usr/bin/env python3
"""
为 PDF 直转和博客转 PPT 生成共享素材账本（asset ledger）。

定位原始 PDF、抽取列感知正文、合成图片全集，并给出页数预算。
图片一律不重新提取，只复用 assets/paper-imgs/ 下已有文件。
全部产物写入 .cache/blog-to-slides/<论文名>/（gitignore，不发布到 GitHub Pages）。

依赖：pymupdf（fitz）、Pillow。缺失时先 `pip install pymupdf Pillow`。
"""
import argparse
import json
import math
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
BLOGS = BASE_DIR / "paper-blogs"
IMGS = BASE_DIR / "assets" / "paper-imgs"
CACHE = BASE_DIR / ".cache" / "blog-to-slides"
STRUCT_PAGES = 7


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
    from paper_assets import blog_images
    refs = blog_images(name, BASE_DIR)
    if refs is None:
        return None
    return {r["path"].name: {k: r[k] for k in ("section", "alt", "note")} for r in refs}


def build(name: str, manual: str, emit_text: bool, full_json: bool, no_blog=False):
    from paper_assets import register, check, source_path, write_json
    manifest = register(name, manual, BASE_DIR)
    report = check(manifest, BASE_DIR)
    pdf_path = source_path(manifest, BASE_DIR)
    pdf_text, pdf_pages = "", 0
    if pdf_path and pdf_path.is_file():
        import fitz
        with fitz.open(pdf_path) as doc:
            pdf_pages = len(doc)
            texts = []
            for i, page in enumerate(doc, 1):
                boxes = [a["bbox"] for a in manifest["assets"]
                         if a.get("page") == i and a.get("bbox") and a["status"] == "verified"]
                texts.append(f"[PDF PAGE {i}]\n" + column_text(page, boxes))
            pdf_text = "\n\n".join(texts)
    refs = {} if no_blog else parse_blog(name)
    if refs is None:
        raise ValueError(f"笔记不存在：{BLOGS / (name + '.md')}；PDF 直转流程请加 --no-blog")
    images = []
    for a in manifest["assets"]:
        if a["status"] == "excluded":
            continue
        filename = a.get("file")
        r = refs.get(filename) or {}
        w, h = a.get("width", 0), a.get("height", 0)
        ratio = w / h if h else 1
        images.append({"id": a["id"], "file": filename, "type": a["kind"],
                       "num": a.get("number"), "page": a.get("page"), "w": w, "h": h,
                       "aspect": "wide" if ratio > 1.6 else ("tall" if ratio < .8 else "square"),
                       "caption": a.get("caption"), "status": a["status"],
                       "in_blog": filename in refs, "required": True,
                       "blog_section": r.get("section"), "blog_caption": r.get("alt"),
                       "blog_note": r.get("note")})
    n = len(images)
    sections = {}
    for f, r in refs.items():
        sections.setdefault(r["section"] or "(未归属)", []).append(f)
    files = {a.get("file") for a in manifest["assets"]
             if a.get("file") and (IMGS / name / a["file"]).is_file()}
    ledger = {
        "paper": name, "manifest": f"assets/paper-imgs/{name}/asset_manifest.json",
        "pdf_path": str(pdf_path) if pdf_path else None,
        "pdf_resolution": "manifest" if pdf_path else "none",
        "pdf_pages": pdf_pages, "pdf_text_chars": len(pdf_text),
        "page_budget": {"min": STRUCT_PAGES + math.ceil(n / 2),
                        "max": STRUCT_PAGES + 1 + n, "cap": None},
        "extracted_count": len(files), "required_count": n, "blog_ref_count": len(refs),
        "blog_sections": [{"section": k, "images": v} for k, v in sections.items()],
        "images": images, "asset_check": report,
        "unused_in_blog": sorted(files - set(refs)),
        "broken_blog_refs": sorted(set(refs) - files),
    }
    out = CACHE / name
    write_json(out / "asset_ledger.json", ledger)
    (out / "paper_text.txt").write_text(pdf_text, encoding="utf-8")
    rows = ["| ID | 文件 | 页码 | 状态 | 博客引用 | 图注 |", "| --- | --- | --- | --- | --- | --- |"]
    for a in images:
        caption = (a.get("caption") or "").replace("\n", " ").replace("|", "\\|")
        rows.append(f"| {a['id']} | {a['file'] or '-'} | {a['page']} | {a['status']} | {a['in_blog']} | {caption} |")
    (out / "asset_ledger.md").write_text("\n".join([
        f"# 素材账本 · {name}", "", "全部非 excluded 素材必须在 PPT 主讲或附录可读呈现。",
        f"- assets_verified: {report['ok']}", f"- errors: {report['errors']}",
        f"- broken_blog_refs: {ledger['broken_blog_refs']}",
        f"- suggested_page_budget: {ledger['page_budget']}", "", *rows, ""]), encoding="utf-8")
    print(pdf_text if emit_text else json.dumps(ledger if full_json else {
        k: ledger[k] for k in ("paper", "required_count", "blog_ref_count", "page_budget", "asset_check", "broken_blog_refs")
    }, ensure_ascii=False, indent=2))
    return ledger


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paper")
    ap.add_argument("--pdf", help="指定源 PDF 路径并校验其清单指纹")
    ap.add_argument("--no-blog", action="store_true", help="PDF 直接转 PPT：不要求已有博客")
    ap.add_argument("--emit-text", action="store_true", help="把列感知正文打印到 stdout")
    ap.add_argument("--json", action="store_true", help="输出完整账本 JSON")
    a = ap.parse_args()
    try:
        build(a.paper, a.pdf, a.emit_text, a.json, a.no_blog)
    except (ImportError, ValueError, OSError) as e:
        sys.exit(f"[ledger] {e}。请检查输入与素材清单；依赖：pip install pymupdf Pillow")


if __name__ == "__main__":
    main()
