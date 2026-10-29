#!/usr/bin/env python3
"""
blog-to-slides 生成后门禁：在真实 DOM 上校验六项检查。

未通过时不得登记 slides-manifest.json、不得运行 generate-thumbnails.py。

检查项：
  1 博客引用图覆盖率 100%（--allow-missing 显式豁免）
  2 图片真实加载（naturalWidth > 0）
  3 页数 >= page_budget.min
  4 页数 <= page_budget.max（--allow-extra-pages 显式上调）
  5 图片 src 前缀必须为 ../assets/paper-imgs/<名>/
  6 含图页中文字符 >= 20（弱守卫：空页检测）

依赖 playwright（本技能 generate-thumbnails.py 的既有依赖）。
playwright 不可用时页数检查退化为正则兜底，并在报告中标注 page_count_source=regex_fallback。

退出码：0 通过；1 门禁失败；2 环境/输入错误。
"""
import argparse
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[4]
BLOGS = BASE_DIR / "paper-blogs"
CACHE = BASE_DIR / ".cache" / "blog-to-slides"
SLIDES = BASE_DIR / "paper-slides"

# 页数正则兜底：必须限定容器标签 + class token 精确匹配。
# 禁止使用 class="slide[^"]*" —— 会误吞 slide-title / slide-subtitle
# （实测 smooth-tail_learning.html 因此把 14 页数成 30）。
PAGE_RE = re.compile(r'<(?:div|section)\s+class="(?:[^"]*\s)?slide(?:\s[^"]*)?"')
ZH_RE = re.compile(r"[一-鿿]")


def regex_page_count(html: str) -> int:
    return len(PAGE_RE.findall(html))


def dom_probe(html_path: Path):
    """用 playwright 取真实 DOM。返回 None 表示不可用。"""
    try:
        import asyncio
        from playwright.async_api import async_playwright
    except Exception:
        return None

    async def run():
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await browser.new_page(viewport={"width": 1280, "height": 720})
            await page.goto(f"file:///{html_path.resolve().as_posix()}", wait_until="load", timeout=30000)
            await page.wait_for_timeout(300)
            r = await page.evaluate("""() => {
              const slides = [...document.querySelectorAll('.slide')];
              const imgs = [...document.querySelectorAll('img')].filter(i => i.src.includes('paper-imgs'));
              return {
                pages: slides.length,
                imgs: imgs.map(i => ({ src: i.getAttribute('src') || '', loaded: i.naturalWidth > 0 })),
                zh: slides.map(s => {
                  const has = [...s.querySelectorAll('img')].some(i => i.src.includes('paper-imgs'));
                  return { has, zh: (s.textContent.match(/[\\u4e00-\\u9fa5]/g) || []).length };
                })
              };
            }""")
            await browser.close()
            return r

    return asyncio.run(run())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paper")
    ap.add_argument("--allow-missing", nargs="*", default=[], help="显式豁免的博客引用图文件名")
    ap.add_argument("--allow-extra-pages", type=int, default=0, help="显式上调页数上限")
    ap.add_argument("--html", help="校验指定 HTML 而非 paper-slides/<名>.html（用于对历史版本做负例测试）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    name = a.paper
    ledger_path = CACHE / name / "asset_ledger.json"
    if not ledger_path.exists():
        sys.exit(f"[verify] 缺少账本：{ledger_path}\n请先运行：python .qoder/skills/blog-to-slides/scripts/build_asset_ledger.py {name}")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))

    html_path = Path(a.html) if a.html else SLIDES / f"{name}.html"
    if not html_path.exists():
        sys.exit(f"[verify] 幻灯片不存在：{html_path}")
    html = html_path.read_text(encoding="utf-8", errors="ignore")

    budget = ledger["page_budget"]
    pmin = budget["min"]
    pmax = budget["max"] + a.allow_extra_pages

    blog_files = {im["file"] for im in ledger["images"] if im["in_blog"]}
    allowed = set(a.allow_missing)
    unknown_allow = allowed - blog_files
    if unknown_allow:
        sys.exit(f"[verify] --allow-missing 含非博客引用图，拒绝豁免：{sorted(unknown_allow)}")

    probe = dom_probe(html_path)
    src_re = re.compile(r'paper-imgs/' + re.escape(name) + r'/([\w\-.]+)')
    used = set(src_re.findall(html))

    failures = []
    report = {"paper": name, "page_count_source": "dom", "checks": {}}

    # 1 覆盖率
    missing = sorted((blog_files - allowed) - used)
    report["checks"]["coverage"] = {
        "blog_refs": len(blog_files), "used": len(blog_files & used),
        "allowed_missing": sorted(allowed), "missing": missing,
    }
    if missing:
        failures.append(f"检查1 覆盖率：缺失 {len(missing)} 张博客引用图 -> {missing}")

    # 2 加载 / 5 前缀（DOM 优先）
    if probe:
        bad_load = sorted(i["src"].split("/")[-1] for i in probe["imgs"] if not i["loaded"])
        bad_prefix = sorted(i["src"] for i in probe["imgs"] if not i["src"].startswith(f"../assets/paper-imgs/{name}/"))
        pages = probe["pages"]
        zh_violations = [i + 1 for i, z in enumerate(probe["zh"]) if z["has"] and z["zh"] < 20]
    else:
        report["page_count_source"] = "regex_fallback"
        pages = regex_page_count(html)
        srcs = re.findall(r'<img[^>]+src="([^"]+)"', html)
        img_srcs = [s for s in srcs if f"paper-imgs/{name}/" in s]
        bad_load = []  # 无 DOM 时无法判定加载，跳过并在报告标注
        bad_prefix = sorted(s for s in img_srcs if not s.startswith(f"../assets/paper-imgs/{name}/"))
        zh_violations = []
    report["checks"]["loaded"] = {"failed": bad_load, "skipped": probe is None}
    report["checks"]["prefix"] = {"bad": bad_prefix}
    report["checks"]["empty_guard"] = {"violations": zh_violations, "skipped": probe is None}
    if bad_load:
        failures.append(f"检查2 图片加载失败 -> {bad_load}")
    if bad_prefix:
        failures.append(f"检查5 路径前缀错误 -> {bad_prefix}")
    if zh_violations:
        failures.append(f"检查6 含图页中文过少（疑似空页）-> 页 {zh_violations}")

    # 3 / 4 页数
    report["checks"]["pages"] = {"pages": pages, "min": pmin, "max": pmax,
                                 "extra_allowed": a.allow_extra_pages}
    if pages < pmin:
        failures.append(f"检查3 页数不足：{pages} < min {pmin}")
    if pages > pmax:
        failures.append(f"检查4 页数超限：{pages} > max {pmax}")

    report["ok"] = not failures
    report["failures"] = failures

    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        c = report["checks"]
        print(f"[verify] {name}  pages={pages} (区间 [{pmin},{pmax}], 来源={report['page_count_source']})")
        print(f"[verify] 覆盖率 {c['coverage']['used']}/{c['coverage']['blog_refs']}"
              + (f"  豁免={c['coverage']['allowed_missing']}" if c["coverage"]["allowed_missing"] else ""))
        if probe is None:
            print("[verify] 警告：playwright 不可用，检查 2/6 跳过、页数用正则兜底（可信度较低）")
        if failures:
            print("\n[verify] 门禁未通过：")
            for f in failures:
                print("  -", f)
            print("\n[verify] 禁止登记 slides-manifest.json / 生成缩略图，请回到工作流第 6 步修补。")
        else:
            print("[verify] 六项检查全部通过。")

    sys.exit(0 if not failures else 1)


if __name__ == "__main__":
    main()
