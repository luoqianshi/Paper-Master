#!/usr/bin/env python3
"""Update slides-manifest.json with new HTML slides generated from blogs."""
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOGS_MANIFEST = ROOT / "blogs-manifest.json"
SLIDES_MANIFEST = ROOT / "slides-manifest.json"
SLIDES_DIR = ROOT / "paper-slides"

def blog_name_to_slide_file(blog_file: str) -> str:
    """Convert blog filename (e.g. 'paper-blogs/CSFC.md') to expected slide filename."""
    name = Path(blog_file).stem
    return f"{name}.html"

def load_blogs_index():
    """Load blogs-manifest.json and index by blog stem name."""
    with open(BLOGS_MANIFEST, "r", encoding="utf-8") as f:
        data = json.load(f)
    index = {}
    for blog in data["blogs"]:
        stem = Path(blog["file"]).stem
        index[stem] = blog
    return index

def main():
    blogs_index = load_blogs_index()

    with open(SLIDES_MANIFEST, "r", encoding="utf-8") as f:
        slides_data = json.load(f)

    existing_files = {entry["file"] for entry in slides_data["slides"]}

    # Find all HTML files in paper-slides/
    html_files = sorted(SLIDES_DIR.glob("*.html"))

    new_entries = []
    for html_file in html_files:
        rel_path = f"paper-slides/{html_file.name}"
        if rel_path in existing_files:
            continue

        # Try to match with a blog
        stem = html_file.stem
        blog = blogs_index.get(stem)

        if blog:
            title = blog["title"]
            category = blog.get("category", "")
            description = f"{title} 论文演示文稿，基于阅读笔记生成。"
            kind = "期刊/会议"
            thumbnail = blog.get("thumbnail", f"assets/thumbnails/{html_file.stem}.png")
        else:
            title = html_file.stem.replace("_", " ").replace("-", " ")
            description = f"{title} 论文演示文稿。"
            kind = "期刊/会议"
            thumbnail = f"assets/thumbnails/{html_file.stem}.png"

        entry = {
            "title": title,
            "file": rel_path,
            "description": description,
            "kind": kind,
            "accent": "rgba(57,102,162,.18)",
            "thumbnail": thumbnail
        }
        new_entries.append(entry)

    if not new_entries:
        print("No new slides to add to manifest.")
        return

    slides_data["slides"].extend(new_entries)

    with open(SLIDES_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(slides_data, f, ensure_ascii=False, indent=2)

    print(f"Added {len(new_entries)} new entries to slides-manifest.json:")
    for e in new_entries:
        print(f"  - {e['title']} → {e['file']}")

if __name__ == "__main__":
    main()
