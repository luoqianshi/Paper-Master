"""Regenerate blogs-manifest.json and slides-manifest.json.

Same logic as the inline steps in .github/workflows/pages.yml, so the
manifests can be refreshed locally before committing (required when the
Pages site runs in "Deploy from a branch" mode, which serves the
committed files as-is).
"""

import argparse
import datetime
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
TITLE_PATTERN = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
FM_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
IMG_PATTERN = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")


def fm_value(fm, key):
    match = re.search(rf"^{key}:\s*(.+?)\s*$", fm, re.M)
    return match.group(1).strip('"').strip("'") if match else ""


def title_from_file(path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = TITLE_PATTERN.search(text)
    if match:
        return html.unescape(re.sub(r"\s+", " ", match.group(1))).strip()
    return path.stem.replace("_", " ").replace("-", " ").title()


def load_curated(manifest_path, list_key):
    curated = {}
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
            entries = existing if isinstance(existing, list) else existing.get(list_key, [])
            curated = {
                entry.get("file"): entry
                for entry in entries
                if isinstance(entry, dict) and entry.get("file")
            }
        except (json.JSONDecodeError, OSError):
            curated = {}
    return curated


def generate_blogs():
    blogs = []
    for path in sorted((ROOT / "paper-blogs").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        match = FM_PATTERN.match(text)
        if not match:
            print(f"skip {path.name}: no front matter")
            continue
        fm = match.group(1)
        img = IMG_PATTERN.search(text[match.end():])
        thumbnail = re.sub(r"^\.\./", "", img.group(1)) if img else ""
        blogs.append({
            "title": fm_value(fm, "title"),
            "file": path.relative_to(ROOT).as_posix(),
            "category": fm_value(fm, "category"),
            "date": fm_value(fm, "date"),
            "source_url": fm_value(fm, "source_url"),
            "thumbnail": thumbnail,
        })
    blogs.sort(key=lambda item: item["date"], reverse=True)
    manifest = {
        "generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "blogs": blogs,
    }
    out = ROOT / "blogs-manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{out.name}: {len(blogs)} blogs")


def generate_slides():
    curated = load_curated(ROOT / "slides-manifest.json", "slides")
    slides = []
    paths = sorted((ROOT / "paper-slides").glob("*.html"), key=lambda item: item.name.lower())
    for index, path in enumerate(paths):
        rel = path.relative_to(ROOT).as_posix()
        kept = curated.get(rel, {})
        slides.append({
            "title": kept.get("title") or title_from_file(path),
            "file": rel,
            "description": kept.get("description") or "从 paper-slides 目录自动发现的 HTML 格式 PPT，可直接嵌入放映或打开原页。",
            "kind": kept.get("kind") or "HTML PPT",
            "accent": kept.get("accent") or ("rgba(93,112,82,.2)" if index % 2 == 0 else "rgba(193,140,93,.22)"),
            **({"thumbnail": kept["thumbnail"]} if kept.get("thumbnail") else {}),
        })
    manifest = {
        "generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "slides": slides,
    }
    out = ROOT / "slides-manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{out.name}: {len(slides)} slides")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blogs-only", action="store_true")
    parser.add_argument("--slides-only", action="store_true")
    args = parser.parse_args()
    if not args.slides_only:
        generate_blogs()
    if not args.blogs_only:
        generate_slides()


if __name__ == "__main__":
    main()
