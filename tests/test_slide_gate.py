import asyncio
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import fitz
import paper_assets as assets
import verify_slides as gate


class SlideGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'paper-slides').mkdir()
        pdf = self.root / 'paper.pdf'
        with fitz.open() as doc:
            p = doc.new_page(); p.insert_text((60, 100), 'Visible source content')
            doc.save(pdf)
        self.data = assets.register('paper', pdf, self.root)
        with fitz.open(pdf) as doc:
            for aid, kind in [('fig1', 'figure'), ('table1', 'table')]:
                a = {'id': aid, 'kind': kind, 'number': '1', 'page': 1,
                     'bbox': None, 'caption': kind, 'file': None, 'status': 'pending'}
                self.data['assets'].append(a)
                assets.crop(self.data, a, doc, self.root, bbox=[40, 60, 540, 300])
                assets.review_asset(self.data, aid, 'verified', 'Checked original', self.root)
        assets.confirm_inventory(self.data, 'All original pages checked', self.root)
        self.path = self.root / 'paper-slides/paper.html'
        self.template = (ROOT / 'templates/presentation.html').read_text(encoding='utf-8')

    def image(self, aid, style=''):
        return f'<img style="{style}" src="../assets/paper-imgs/paper/{aid}.png" alt="Original figure">'

    def write(self, content):
        section = f'<section class="slide"><h2>论文方法与实验结果</h2><p>这里是对原文图表的完整说明，用于验证图片与解释能够同时看到。</p>{content}</section>'
        self.path.write_text(self.template.replace('</div><!-- /deck -->', section + '</div><!-- /deck -->'), encoding='utf-8')

    def report(self):
        # A real browser is required: this suite deliberately does not mock DOM results.
        probe = asyncio.run(gate.dom_probe(self.path, [(1280, 720)]))
        return gate.assess(self.data, probe, self.root)

    def test_complete_figures_and_tables_pass(self):
        self.write('<div class="fig-pair">'+self.image('fig1')+self.image('table1')+'</div>')
        report = self.report()
        self.assertTrue(report['ok'], report)

    def test_comment_only_reference_does_not_count(self):
        self.write('<!-- '+self.image('fig1')+self.image('table1')+' -->')
        report = self.report()
        self.assertFalse(report['ok'])
        self.assertEqual(report['viewports']['1280x720']['used'], 0)

    def test_detail_image_cannot_replace_full_asset(self):
        detail = self.image('table1').replace('<img ', '<img data-asset-detail="true" ')
        self.write(self.image('fig1') + detail)
        self.assertIn('table1', self.report()['viewports']['1280x720']['missing'])

    def test_detail_thumbnail_allowed_alongside_full_asset(self):
        detail = self.image('table1', 'width:30px;height:20px;object-fit:cover').replace(
            '<img ', '<img data-asset-detail="true" ')
        self.write('<div class="fig-pair">'+self.image('fig1')+self.image('table1')+'</div>'+detail)
        report = self.report()
        self.assertTrue(report['ok'], report)

    def test_unreferenced_by_blog_table_is_still_required(self):
        self.write(self.image('fig1'))
        self.assertIn('table1', self.report()['viewports']['1280x720']['missing'])

    def test_hidden_tiny_clipped_and_outside_images_do_not_count(self):
        for css in ['display:none', 'opacity:0', 'width:1px;height:1px',
                    'position:absolute;left:-3000px', 'clip-path:inset(50%)']:
            with self.subTest(css=css):
                self.write(self.image('fig1')+self.image('table1', css))
                self.assertIn('table1', self.report()['viewports']['1280x720']['missing'])

    def test_non_slide_image_does_not_count(self):
        self.write(self.image('fig1'))
        self.path.write_text(self.path.read_text(encoding='utf-8').replace('</body>', self.image('table1')+'</body>'), encoding='utf-8')
        self.assertIn('table1', self.report()['viewports']['1280x720']['missing'])

    def test_mutated_asset_or_unreviewed_inventory_cannot_pass(self):
        self.write('<div class="fig-pair">'+self.image('fig1')+self.image('table1')+'</div>')
        self.data['inventory']['reviewed'] = False
        self.assertFalse(self.report()['ok'])

    def test_unavailable_browser_is_not_a_pass(self):
        self.write('')
        with patch.object(gate, 'dom_probe', side_effect=RuntimeError('Chromium unavailable')):
            with self.assertRaisesRegex(RuntimeError, 'Chromium unavailable'):
                gate.verify('paper', self.path, self.root)

    def test_broken_blog_reference_cannot_disappear_from_coverage(self):
        (self.root / 'paper-blogs').mkdir()
        (self.root / 'paper-blogs/paper.md').write_text('![Missing](../assets/paper-imgs/paper/missing.png)')
        self.write('<div class="fig-pair">'+self.image('fig1')+self.image('table1')+'</div>')
        report = self.report()
        self.assertFalse(report['ok'])
        self.assertIn('博客存在失效图片引用', '\n'.join(report['failures']))

    def test_template_keyboard_initial_counter_and_offline(self):
        self.write('<div class="fig-pair">'+self.image('fig1')+self.image('table1')+'</div>')
        extra = '<section class="slide"><h2>第二页</h2><p>用于验证翻页、页码和打印布局。</p></section>'
        self.path.write_text(self.path.read_text(encoding='utf-8').replace('</div><!-- /deck -->', extra+'</div><!-- /deck -->'), encoding='utf-8')
        async def inspect():
            from playwright.async_api import async_playwright
            async with async_playwright() as pw:
                browser = await pw.chromium.launch()
                page = await browser.new_page()
                errors, requests = [], []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.on('request', lambda r: requests.append(r.url))
                await page.goto(self.path.as_uri())
                self.assertEqual(await page.locator('#counter').inner_text(), '01 / 02')
                self.assertEqual(await page.locator('#prevBtn, #nextBtn').count(), 0)
                await page.keyboard.press('ArrowRight'); await page.wait_for_timeout(100)
                self.assertEqual(await page.locator('#counter').inner_text(), '02 / 02')
                await page.keyboard.press('Home'); await page.wait_for_timeout(100)
                self.assertEqual(await page.locator('#counter').inner_text(), '01 / 02')
                await page.emulate_media(media='print')
                self.assertEqual(await page.locator('.slide:visible').count(), 2)
                self.assertFalse(errors)
                self.assertFalse([r for r in requests if r.startswith('http')])
                await browser.close()
        asyncio.run(inspect())


if __name__ == '__main__':
    unittest.main()
