#!/usr/bin/env python3
"""Validate all inventoried assets against visible slide images in an offline browser.

Exit codes: 0 verified, 1 content/asset failure, 2 environment or input unavailable.
No regex fallback may claim a rendered pass. Both PDF and blog workflows use this gate.
"""
import argparse
import asyncio
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

from paper_assets import ROOT, load_manifest, check, asset_file, blog_images

VIEWPORTS = [(1280, 720), (1920, 1080)]

# Inspect only actual <img> nodes inside the active slide. Resolve geometry through
# all clipping/hidden ancestors; HTML comments, off-slide and tiny images never count.
MEASURE = r"""(index) => {
  const slides = [...document.querySelectorAll('.slide')], s = slides[index];
  const clipRect = (r, q) => ({left:Math.max(r.left,q.left), top:Math.max(r.top,q.top),
    right:Math.min(r.right,q.right), bottom:Math.min(r.bottom,q.bottom)});
  const result = {active: s.classList.contains('active'), images: [],
    text: (s.innerText || '').trim(), overflow: false};
  const sr = s.getBoundingClientRect();
  result.overflow = s.scrollHeight > s.clientHeight + 3 || s.scrollWidth > s.clientWidth + 3;
  for (const im of s.querySelectorAll('img')) {
    const box = im.getBoundingClientRect(), cs = getComputedStyle(im);
    let r = {left:box.left,top:box.top,right:box.right,bottom:box.bottom};
    // Measure the actual contained bitmap, not merely a large CSS box.
    let w = box.width, h = box.height;
    if (cs.objectFit === 'contain' && im.naturalWidth && im.naturalHeight) {
      const scale = Math.min(w/im.naturalWidth, h/im.naturalHeight);
      w = im.naturalWidth*scale; h = im.naturalHeight*scale;
      r = {left:box.left+(box.width-w)/2,top:box.top+(box.height-h)/2,
           right:box.left+(box.width+w)/2,bottom:box.top+(box.height+h)/2};
    }
    let visible = true, opacity = 1, clipped = clipRect(r, {left:0,top:0,right:innerWidth,bottom:innerHeight});
    for (let el = im; el; el = el.parentElement) {
      const st = getComputedStyle(el);
      opacity *= Number(st.opacity);
      if (st.display === 'none' || st.visibility !== 'visible' || st.contentVisibility === 'hidden'
          || st.clipPath !== 'none' || st.clip !== 'auto') visible = false;
      if (el !== im && /(hidden|clip|scroll|auto)/.test(st.overflowX+' '+st.overflowY)) {
        clipped = clipRect(clipped, el.getBoundingClientRect());
      }
    }
    const area = Math.max(0,clipped.right-clipped.left)*Math.max(0,clipped.bottom-clipped.top);
    const loaded = im.complete && im.naturalWidth > 0 && im.naturalHeight > 0;
    const fit = cs.objectFit;
    const distorted = loaded && fit === 'fill' && Math.abs(box.width/box.height / (im.naturalWidth/im.naturalHeight)-1) > .08;
    const cropped = loaded && fit === 'cover' && Math.abs(box.width/box.height / (im.naturalWidth/im.naturalHeight)-1) > .02;
    const sizeOK = w >= Math.min(160,im.naturalWidth) && h >= Math.min(80,im.naturalHeight);
    const center = document.elementFromPoint((r.left+r.right)/2,(r.top+r.bottom)/2);
    const unobscured = center === im || (center && im.contains(center));
    result.images.push({src:im.getAttribute('src') || '', url:im.currentSrc || im.src,
      loaded, width:Math.round(w), height:Math.round(h), distorted, cropped,
      detail: im.dataset.assetDetail === 'true',
      visible: visible && opacity >= .95 && area >= w*h*.98 && sizeOK && !!unobscured && result.active});
  }
  return result;
}"""


async def dom_probe(html_path, viewports=VIEWPORTS):
    from playwright.async_api import async_playwright
    report = {'viewports': {}, 'external_requests': [], 'page_errors': []}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        try:
            for width, height in viewports:
                page = await browser.new_page(viewport={'width': width, 'height': height})
                async def offline(route):
                    report['external_requests'].append(route.request.url)
                    await route.abort()
                await page.route('http://**/*', offline)
                await page.route('https://**/*', offline)
                page.on('pageerror', lambda e: report['page_errors'].append(str(e)))
                await page.goto(Path(html_path).resolve().as_uri(), wait_until='load', timeout=30000)
                count = await page.locator('.slide').count()
                await page.keyboard.press('Home')
                pages = []
                for i in range(count):
                    if i:
                        await page.keyboard.press('ArrowRight')
                    await page.wait_for_timeout(90)
                    await page.evaluate("""() => { for (const a of document.getAnimations()) {
                        if (Number.isFinite(a.effect.getComputedTiming().endTime)) { try { a.finish(); } catch {} }
                    }}""")
                    await page.evaluate("""async () => { await Promise.race([
                        Promise.all([...document.querySelectorAll('.slide.active img')].map(i=>i.decode().catch(()=>{}))),
                        new Promise(r=>setTimeout(r,3000))]); }""")
                    pages.append(await page.evaluate(MEASURE, i))
                report['viewports'][f'{width}x{height}'] = pages
                await page.close()
        finally:
            await browser.close()
    return report


def file_from_url(url):
    parsed = urlsplit(url)
    if parsed.scheme != 'file' or parsed.netloc not in {'', 'localhost'}:
        return None
    path = unquote(parsed.path)
    if len(path) > 2 and path[0] == '/' and path[2] == ':':
        path = path[1:]
    return Path(path).resolve()


def assess(data, probe, root=ROOT):
    asset_report = check(data, root)
    failures = list(asset_report['errors'])
    required = {a['id']: a for a in data['assets'] if a['status'] != 'excluded'}
    by_path = {asset_file(data, a, root): a['id'] for a in required.values() if a.get('file')}
    for ref in blog_images(data['paper_id'], root) or []:
        if not ref['path'].is_file():
            failures.append(f"博客存在失效图片引用：{ref['src']}")
        elif (Path(root) / 'assets/paper-imgs').resolve() in ref['path'].parents and ref['path'] not in by_path:
            failures.append(f"博客引用了未纳入当前清单的素材：{ref['src']}")
    reports = {}
    for vp, pages in probe['viewports'].items():
        used = set()
        issues = []
        if not pages:
            issues.append('没有实际 .slide 页面')
        for number, page in enumerate(pages, 1):
            if not page['active']:
                issues.append(f'第 {number} 页无法通过键盘激活')
            for im in page['images']:
                path = file_from_url(im['url'])
                aid = by_path.get(path)
                if not im['loaded']:
                    issues.append(f"第 {number} 页图片加载失败：{im['src']}")
                if aid and not im.get('detail') and im['loaded'] and im['visible'] and not im['distorted'] and not im['cropped']:
                    used.add(aid)
                elif aid and not im.get('detail'):
                    issues.append(f"第 {number} 页 {aid} 未完整可见或尺寸不足/变形：{im['width']}x{im['height']}")
                elif not aid and path and (Path(root) / 'assets/paper-imgs').resolve() in path.parents:
                    issues.append(f'第 {number} 页使用了非本清单的素材：{im["src"]}')
            if page['images'] and len(page['text']) < 20:
                issues.append(f'第 {number} 页图表缺少说明（可见文字少于 20 字符）')
        missing = sorted(set(required) - used)
        if missing:
            issues.append(f'未完整呈现的素材：{missing}')
        reports[vp] = {'pages': len(pages), 'required': len(required), 'used': len(used),
                       'missing': missing, 'issues': issues}
        failures.extend(f'{vp}: {issue}' for issue in issues)
    if not probe['viewports']:
        failures.append('未执行浏览器检查')
    if probe['external_requests']:
        failures.append('包含外部网络依赖：' + ', '.join(sorted(set(probe['external_requests']))))
    if probe['page_errors']:
        failures.extend(probe['page_errors'])
    return {'paper': data['paper_id'], 'ok': not failures, 'status': 'passed' if not failures else 'failed',
            'asset_check': asset_report, 'viewports': reports, 'failures': failures}


def verify(paper, html_path=None, root=ROOT):
    data = load_manifest(paper, root)
    target = Path(html_path) if html_path else Path(root) / 'paper-slides' / f'{paper}.html'
    if not target.is_file():
        raise FileNotFoundError(target)
    return assess(data, asyncio.run(dom_probe(target)), root)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('paper')
    ap.add_argument('--html')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    try:
        report = verify(args.paper, args.html)
        code = 0 if report['ok'] else 1
    except Exception as exc:
        report = {'paper': args.paper, 'ok': False, 'status': 'unverified',
                  'error': str(exc), 'hint': '检查素材清单、HTML 输入及 Playwright/Chromium；未验证不得登记交付。'}
        code = 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(code)


if __name__ == '__main__':
    main()
