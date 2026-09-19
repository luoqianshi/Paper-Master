#!/usr/bin/env python3
"""
为 paper-slides/ 下的每个 HTML 幻灯片生成首页缩略图。
使用 Playwright 截取首屏，输出到 assets/thumbnails/。
"""
import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright

# 本脚本位于 <项目根>/.qoder/skills/blog-to-slides/scripts/，
# 向上 5 级回到项目根目录
BASE_DIR = Path(__file__).resolve().parents[4]
SLIDES_DIR = BASE_DIR / "paper-slides"
THUMB_DIR = BASE_DIR / "assets" / "thumbnails"
MANIFEST_PATH = BASE_DIR / "slides-manifest.json"

# 截图视口：16:9，保证清晰度
VIEWPORT = {"width": 1280, "height": 720}
# 输出缩略图尺寸（CSS 会用 object-fit: cover，所以比例接近即可）
OUTPUT_WIDTH = 640
OUTPUT_HEIGHT = 360


def discover_html_files():
    """遍历 paper-slides 目录，返回所有 .html 文件路径（相对于 BASE_DIR）。"""
    files = []
    for f in sorted(SLIDES_DIR.iterdir()):
        if f.is_file() and f.suffix.lower() == ".html":
            rel = f.relative_to(BASE_DIR).as_posix()
            files.append(rel)
    return files


async def capture_thumbnail(browser, html_path: str, thumb_path: Path):
    """截取单个 HTML 的首屏并保存为缩略图。"""
    page = await browser.new_page(viewport=VIEWPORT)
    file_url = html_path if html_path.startswith("http") else f"file:///{(BASE_DIR / html_path).resolve().as_posix()}"
    try:
        await page.goto(file_url, wait_until="networkidle", timeout=30000)
        # 等待可能的首页动画完成（slide.active 过渡 0.5s）
        await asyncio.sleep(0.8)
        # 截图整张页面
        await page.screenshot(
            path=str(thumb_path),
            type="png",
            full_page=False,
        )
        print(f"  [OK] {thumb_path.name}")
    except Exception as e:
        print(f"  [ERR] {thumb_path.name}: {e}")
    finally:
        await page.close()


async def main():
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    html_files = discover_html_files()
    print(f"Found {len(html_files)} HTML slides, generating thumbnails...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for rel_path in html_files:
            stem = Path(rel_path).stem
            thumb_name = f"{stem}.png"
            thumb_path = THUMB_DIR / thumb_name
            print(f"[CAPTURE] {rel_path}")
            await capture_thumbnail(browser, rel_path, thumb_path)

        await browser.close()

    # 更新 slides-manifest.json，为每个 slide 添加 thumbnail 字段
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        slides = manifest.get("slides", manifest if isinstance(manifest, list) else [])
        for slide in slides:
            file_path = slide.get("file", "")
            stem = Path(file_path).stem
            thumb_name = f"{stem}.png"
            thumb_rel = f"assets/thumbnails/{thumb_name}"
            # 只有当缩略图实际存在时才写入
            if (BASE_DIR / thumb_rel).exists():
                slide["thumbnail"] = thumb_rel
            else:
                # 尝试匹配（某些文件名可能不完全一致）
                candidates = list(THUMB_DIR.glob(f"{stem}*.png"))
                if candidates:
                    slide["thumbnail"] = f"assets/thumbnails/{candidates[0].name}"

        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print(f"\n[UPDATED] {MANIFEST_PATH.name}")

    print("\n[DONE] All thumbnails generated!")


if __name__ == "__main__":
    asyncio.run(main())
