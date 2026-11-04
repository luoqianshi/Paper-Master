#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML PPT 质量核查器（Playwright 真实渲染度量）

配套标准：docs/html-ppt-quality-standard.md
用法（须用已装 playwright 的 PATH python，例如 Anaconda 3.11）：
    python scripts/audit_render.py --probe-only
    python scripts/audit_render.py --limit 3          # 小批验证
    python scripts/audit_render.py                   # 全量 62 份，支持断点续跑
    python scripts/audit_render.py --files "A.html,B.html" --force

输出：.cache/slides-audit/render_metrics.json、screens/、render_run.log（写盘，不依赖 stdout）
本脚本对 paper-slides/ 只读，不修改任何 HTML。
"""
import argparse
import asyncio
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SLIDES_DIR = BASE_DIR / "paper-slides"
CACHE_DIR = BASE_DIR / ".cache" / "slides-audit"
SCREENS_DIR = CACHE_DIR / "screens"
RENDER_JSON = CACHE_DIR / "render_metrics.json"
PROBE_JSON = CACHE_DIR / "probe_render.json"
LOG = CACHE_DIR / "render_run.log"

# ===== 关键参数（置顶，便于修改） =====
VIEWPORTS = [
    {"name": "1920x1080", "width": 1920, "height": 1080, "main": True},
    {"name": "1366x768", "width": 1366, "height": 768, "main": True},
    {"name": "1280x720", "width": 1280, "height": 720, "main": True, "interaction": True},
    {"name": "1024x768", "width": 1024, "height": 768, "aux": True},
    {"name": "900x700", "width": 900, "height": 700, "aux": True},
    {"name": "768x1024", "width": 768, "height": 1024, "aux": True},
]
GOTO_TIMEOUT_MS = 30000
SETTLE_MS = 300
VIEWPORT_SETTLE_MS = 120
KEY_SETTLE_MS = 150
MAX_SHOTS_PER_FILE = 2

PROBE_JS = r"""
() => {
  const slides = [...document.querySelectorAll('.slide')];
  const pages = slides.length;
  const overflow_pages = [], broken_imgs = [], wide_img_cramped = [];
  const small_text_pages = [], contrast_violations = [];
  let minFont = null;
  const parseRGB = (s) => {
    const m = String(s).match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const a = m[1].split(',').map(Number);
    return {r:a[0], g:a[1], b:a[2], a:a.length>3?a[3]:1};
  };
  const lin = (v) => { v = v/255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
  const lum = (c) => 0.2126*lin(c.r)+0.7152*lin(c.g)+0.0722*lin(c.b);
  const ratio = (a,b) => { const l1=lum(a), l2=lum(b); return (Math.max(l1,l2)+0.05)/(Math.min(l1,l2)+0.05); };
  const bgOf = (el) => {
    let p = el;
    while (p) {
      const c = parseRGB(getComputedStyle(p).backgroundColor);
      if (c && c.a > 0.05) return c;
      p = p.parentElement;
    }
    return {r:255,g:255,b:255,a:1};
  };
  const titleOf = (s) => {
    const h = s.querySelector('h2,.slide-label,.slide-title');
    return h ? h.textContent.trim().replace(/\s+/g,' ').slice(0,60) : '';
  };
  // 装饰性 .glow 是 absolute 定位且带 top/left/bottom/right 负偏移，
  // 会把 scrollHeight/scrollWidth 撑出固定 120/100px，导致"假溢出"。
  // 度量前临时隐藏（仅内存 DOM，不改文件），度量后恢复。
  const decorHidden = [];
  slides.forEach(s => {
    [...s.querySelectorAll('.glow, [class*="glow"]')].forEach(g => {
      decorHidden.push({el:g, display:g.style.display});
      g.style.display = 'none';
    });
  });
  slides.forEach((s, i) => {
    const n = i+1, ch = s.clientHeight, cw = s.clientWidth;
    const sh = s.scrollHeight, sw = s.scrollWidth;
    if (sh > ch+2 || sw > cw+2) {
      overflow_pages.push({page:n, page_title:titleOf(s), sh, ch, sw, cw});
    }
    [...s.querySelectorAll('img')].forEach(im => {
      const src = im.getAttribute('src') || '';
      if (!im.complete || im.naturalWidth === 0) {
        broken_imgs.push({page:n, page_title:titleOf(s), src, naturalWidth:im.naturalWidth});
      }
      const r = im.getBoundingClientRect();
      if (im.naturalWidth>0 && im.naturalHeight>0 && r.width>0) {
        const ar = im.naturalWidth/im.naturalHeight;
        if (ar > 2 && r.width < cw*0.45) {
          wide_img_cramped.push({page:n, src, width:Math.round(r.width), container:cw});
        }
      }
    });
    const textEls = [...s.querySelectorAll('p,li,h1,h2,h3,.body-text,.subtitle,.figure-caption,td,th')];
    textEls.forEach(el => {
      const t = el.textContent.trim();
      if (!t) return;
      const cs = getComputedStyle(el);
      const fs = parseFloat(cs.fontSize);
      if (fs > 0) {
        if (minFont === null || fs < minFont) minFont = fs;
        if (fs < 11 && small_text_pages.length < 20) {
          small_text_pages.push({page:n, size:fs, tag:el.tagName, text:t.slice(0,30)});
        }
      }
      const fg = parseRGB(cs.color), bg = bgOf(el);
      if (fg && contrast_violations.length < 20) {
        const isBody = /^(P|LI|TD|TH)$/.test(el.tagName)
          || el.classList.contains('body-text') || el.classList.contains('subtitle')
          || el.classList.contains('figure-caption');
        const threshold = isBody ? 4.5 : 3.0;
        const cr = ratio(fg, bg);
        if (cr < threshold - 0.05) {
          contrast_violations.push({page:n, tag:el.tagName,
            cls:String(el.className).slice(0,40), color:cs.color,
            bg:'rgb('+bg.r+','+bg.g+','+bg.b+')', ratio:Math.round(cr*100)/100,
            threshold:threshold, text:t.slice(0,30)});
        }
      }
    });
  });
  decorHidden.forEach(x => { x.el.style.display = x.display; });
  return {
    pages: pages, page_titles: slides.map(titleOf),
    overflow_pages: overflow_pages.slice(0,30),
    overflow_total: overflow_pages.length,
    broken_imgs: broken_imgs,
    wide_img_cramped: wide_img_cramped.slice(0,20),
    small_text_pages: small_text_pages,
    contrast_violations: contrast_violations,
    min_font_px: minFont
  };
}
"""

INTERACTION_JS = r"""
() => {
  const slides = [...document.querySelectorAll('.slide')];
  const activeIdx = () => slides.findIndex(s => s.classList.contains('active'));
  const page_visibility = slides.map(s => {
    const old = s.style.transition;
    const had = s.classList.contains('active');
    s.style.transition = 'none';
    s.classList.add('active');
    const cs = getComputedStyle(s);
    const ok = cs.visibility === 'visible' && parseFloat(cs.opacity) > 0.5;
    if (!had) s.classList.remove('active');
    s.style.transition = old;
    return ok;
  });
  const src = [...document.querySelectorAll('script')].map(x => x.textContent || '').join('\n');
  const docClick = /document\.addEventListener\(\s*['"]click/.test(src);
  const guarded = /closest\([^)]*(?:img|a\b|button)/.test(src)
    || /stopPropagation/.test(src) || /target\.tagName/.test(src);
  const prog = document.querySelector('.progress,.progress-bar');
  return {
    active_idx: activeIdx(),
    page_visibility: page_visibility,
    doc_click: docClick,
    click_misfire: docClick && !guarded,
    dots_count: document.querySelectorAll('.dot').length,
    progress_width: prog ? getComputedStyle(prog).width : '',
    counter_text: (document.querySelector('.counter,.page-counter') || {}).textContent || ''
  };
}
"""

ACTIVE_IDX_JS = "() => [...document.querySelectorAll('.slide')].findIndex(s => s.classList.contains('active'))"
PRINT_VISIBLE_JS = ("() => [...document.querySelectorAll('.slide')].filter(s => {"
                    "const c = getComputedStyle(s); return c.visibility === 'visible' && parseFloat(c.opacity) > 0.05;"
                    "}).length")
SET_ACTIVE_JS = ("(i) => { [...document.querySelectorAll('.slide')].forEach((s,j) => {"
                 "s.style.transition='none'; s.classList.toggle('active', j===i); }); }")


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(msg, buf):
    buf.append(str(msg))


async def probe_only():
    try:
        from playwright.async_api import async_playwright
    except Exception as e:
        PROBE_JSON.write_text(json.dumps({"available": False, "error": repr(e)}, ensure_ascii=False, indent=2), encoding="utf-8")
        return False
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            page = await browser.new_page(viewport={"width": 1280, "height": 720})
            await page.goto("about:blank")
            ver = browser.version
            await browser.close()
        PROBE_JSON.write_text(json.dumps({
            "available": True, "browser_version": ver, "python": sys.executable,
            "viewports": [v["name"] for v in VIEWPORTS], "checkedAt": now_iso(),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception as e:
        PROBE_JSON.write_text(json.dumps({"available": False, "error": repr(e)}, ensure_ascii=False, indent=2), encoding="utf-8")
        return False


async def render_one(browser, path, logbuf):
    """渲染单份 HTML；返回该文件的度量 dict。"""
    from playwright.async_api import TimeoutError as PWTimeout
    rec = {"ok": False, "viewports": {}, "interaction": {}, "error": None, "failed_requests": []}
    page = await browser.new_page(viewport={"width": 1280, "height": 720})
    try:
        failed = []

        def on_failed(req):
            u = req.url
            if "favicon" not in u.lower():
                failed.append({"url": u, "why": str(req.failure)})

        def on_response(resp):
            u = resp.url
            if resp.status >= 400 and "favicon" not in u.lower():
                failed.append({"url": u, "status": resp.status})

        page.on("requestfailed", on_failed)
        page.on("response", on_response)
        uri = path.resolve().as_uri()  # 中文/空格路径自动 percent-encode
        await page.goto(uri, wait_until="load", timeout=GOTO_TIMEOUT_MS)
        await page.wait_for_timeout(SETTLE_MS)

        for vp in VIEWPORTS:
            await page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
            await page.wait_for_timeout(VIEWPORT_SETTLE_MS)
            d = await page.evaluate(PROBE_JS)
            d["failed_requests"] = list(failed)
            rec["viewports"][vp["name"]] = d
            if vp.get("interaction"):
                inter = await page.evaluate(INTERACTION_JS)
                pages = d["pages"]
                # 真实键盘翻页：Home -> ArrowRight -> End -> ArrowRight（边界）
                await page.keyboard.press("Home")
                await page.wait_for_timeout(KEY_SETTLE_MS)
                i0 = await page.evaluate(ACTIVE_IDX_JS)
                await page.keyboard.press("ArrowRight")
                await page.wait_for_timeout(KEY_SETTLE_MS)
                i1 = await page.evaluate(ACTIVE_IDX_JS)
                await page.keyboard.press("End")
                await page.wait_for_timeout(KEY_SETTLE_MS)
                iend = await page.evaluate(ACTIVE_IDX_JS)
                await page.keyboard.press("ArrowRight")
                await page.wait_for_timeout(KEY_SETTLE_MS)
                ibound = await page.evaluate(ACTIVE_IDX_JS)
                inter["keyboard_ok"] = bool(pages > 1 and i1 == i0 + 1 and iend == pages - 1 and ibound == pages - 1)
                inter["keyboard_detail"] = {"i0": i0, "i1": i1, "end": iend, "bound": ibound, "pages": pages}
                await page.emulate_media(media="print")
                inter["print_visible_pages"] = await page.evaluate(PRINT_VISIBLE_JS)
                await page.emulate_media(media="screen")
                inter["pages"] = pages
                rec["interaction"] = inter

        rec["failed_requests"] = failed
        # 关键页截图：仅对有问题的文件，主档 1280x720，最多 2 张
        main = rec["viewports"].get("1280x720", {})
        problem_pages = [x["page"] for x in main.get("overflow_pages", [])]
        problem_pages += [x["page"] for x in main.get("broken_imgs", [])]
        if problem_pages:
            shots = [1, problem_pages[0]] if problem_pages[0] != 1 else [1, (problem_pages[1] if len(problem_pages) > 1 else 1)]
            await page.set_viewport_size({"width": 1280, "height": 720})
            outdir = SCREENS_DIR / path.stem
            outdir.mkdir(parents=True, exist_ok=True)
            for p in dict.fromkeys(shots[:MAX_SHOTS_PER_FILE]):
                await page.evaluate(SET_ACTIVE_JS, p - 1)
                await page.wait_for_timeout(60)
                await page.screenshot(path=str(outdir / f"1280x720_p{p}.png"))
            rec["screens"] = [f"screens/{path.stem}/1280x720_p{p}.png" for p in dict.fromkeys(shots[:MAX_SHOTS_PER_FILE])]
        rec["ok"] = True
    except PWTimeout as e:
        rec["error"] = "timeout: " + repr(e)
        log(f"  TIMEOUT {path.name}: {e}", logbuf)
    except Exception as e:
        rec["error"] = repr(e)
        log(f"  ERROR {path.name}: {e}\n{traceback.format_exc()[-600:]}", logbuf)
    finally:
        await page.close()
    return rec


async def run(args):
    from playwright.async_api import async_playwright
    files = sorted(SLIDES_DIR.glob("*.html"))
    if args.files:
        wanted = {x.strip() for x in args.files.split(",") if x.strip()}
        files = [f for f in files if f.name in wanted]
    if args.limit:
        files = files[:args.limit]

    existing = {}
    if RENDER_JSON.exists() and not args.force:
        try:
            existing = json.loads(RENDER_JSON.read_text(encoding="utf-8")).get("files", {})
        except Exception:
            existing = {}

    logbuf = [f"渲染开始 {now_iso()}，待处理 {len(files)} 份，断点续跑已跳过 {len(set(f.name for f in files) & set(existing))} 份"]
    out = {
        "generatedAt": now_iso(), "available": True, "python": sys.executable,
        "viewports": VIEWPORTS, "files": dict(existing),
    }
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        done = 0
        for i, f in enumerate(files, 1):
            if not args.force and f.name in existing and existing[f.name].get("ok"):
                continue
            log(f"[{i}/{len(files)}] {f.name}", logbuf)
            rec = await render_one(browser, f, logbuf)
            out["files"][f.name] = rec
            done += 1
            if done % 5 == 0:  # 每 5 份落盘一次，支持中断续跑
                RENDER_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        await browser.close()
    out["generatedAt"] = now_iso()
    out["completed"] = len([v for v in out["files"].values() if v.get("ok")])
    RENDER_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"渲染完成 {now_iso()}，本次处理 {done} 份，累计 ok {out['completed']} 份", logbuf)
    # 汇总便于人工复核（stdout 不回传，一律落盘）
    summary = [f"渲染结果汇总（共 {len(out['files'])} 份，ok {out['completed']}）", ""]
    for name, r in sorted(out["files"].items()):
        if r.get("error"):
            summary.append(f"ERROR  {name}: {r['error'][:120]}")
            continue
        main = r.get("viewports", {}).get("1280x720", {})
        brk = sum(len(d.get("broken_imgs", [])) for d in r.get("viewports", {}).values())
        ovf = sum(d.get("overflow_total", 0) for d in r.get("viewports", {}).values())
        kb = r.get("interaction", {}).get("keyboard_ok")
        summary.append(f"{name}: pages={main.get('pages')} broken={brk} overflow={ovf} minfont={main.get('min_font_px')} keyboard={kb} print={r.get('interaction',{}).get('print_visible_pages')}")
    (CACHE_DIR / "render_summary.txt").write_text("\n".join(summary), encoding="utf-8")
    LOG.write_text("\n".join(logbuf), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probe-only", action="store_true", help="探测 playwright/chromium 可用性")
    ap.add_argument("--files", help="逗号分隔的文件名，只渲染指定文件")
    ap.add_argument("--limit", type=int, help="只处理前 N 份（小批验证）")
    ap.add_argument("--force", action="store_true", help="忽略断点续跑，强制重渲染")
    a = ap.parse_args()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    SCREENS_DIR.mkdir(parents=True, exist_ok=True)
    if a.probe_only:
        ok = asyncio.run(probe_only())
        print("[probe] available =", ok)
        return
    try:
        import playwright  # noqa: F401
    except Exception as e:
        RENDER_JSON.write_text(json.dumps({"available": False, "error": repr(e), "files": {}}, ensure_ascii=False, indent=2), encoding="utf-8")
        LOG.write_text(f"playwright 不可用：{e!r}", encoding="utf-8")
        print("[render] playwright unavailable")
        return
    asyncio.run(run(a))


if __name__ == "__main__":
    main()
