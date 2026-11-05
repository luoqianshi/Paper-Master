import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import fitz
from PIL import Image
import paper_assets as assets
import pdf_regions


class AssetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'pdf-papers').mkdir()
        self.pdf = self.root / 'pdf-papers/paper.pdf'
        with fitz.open() as doc:
            page = doc.new_page()
            page.draw_rect(fitz.Rect(50, 150, 500, 400), color=(0, 0, 1), fill=(.8, .9, 1))
            page.insert_text((50, 450), 'Figure 1: Framework with all modules.', fontsize=12)
            page = doc.new_page()
            page.insert_text((50, 100), 'Table S1: Additional results.', fontsize=12)
            doc.save(self.pdf)

    def prepared(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return assets.prepare('paper', self.pdf, self.root)

    def complete(self, data):
        for a in data['assets']:
            if a['status'] == 'pending':
                with fitz.open(self.pdf) as doc:
                    assets.crop(data, a, doc, self.root, page=a['page'], bbox=[40, 80, 540, 400])
            assets.review_asset(data, a['id'], 'verified', 'Compared original page and full crop', self.root)
        assets.confirm_inventory(data, 'All pages checked', self.root)
        return data

    def test_common_caption_numbering(self):
        for caption in ['Figure 1: Example', 'Fig. 2. Example', 'Table I: Results',
                        'Table S1: Appendix', 'Figure A.1: Appendix', '图 1 网络结构', '表 2 消融实验']:
            with self.subTest(caption=caption):
                self.assertIsNotNone(pdf_regions.parse_caption_text(caption))
        self.assertIsNone(pdf_regions.parse_caption_text('Figure 1 shows the results.'))

    def test_partial_success_retains_missing_item_and_is_idempotent(self):
        data = self.prepared()
        self.assertEqual(len(data['assets']), 2)
        self.assertEqual({a['status'] for a in data['assets']}, {'pending', 'needs_review'})
        self.assertEqual(data, self.prepared())
        self.assertEqual(len(list(assets.paper_dir('paper', self.root).glob('*.png'))), 1)
        self.assertFalse(assets.check(data, self.root)['ok'])

    def test_manual_repair_review_and_inventory_gate(self):
        data = self.complete(self.prepared())
        self.assertTrue(assets.check(data, self.root)['ok'])
        self.assertEqual(data, self.prepared())
        target = assets.asset_file(data, data['assets'][0], self.root)
        Image.new('RGB', (300, 200), 'red').save(target)
        self.assertFalse(assets.check(data, self.root)['ok'])
        refreshed = assets.register('paper', root=self.root)
        self.assertFalse(refreshed['inventory']['reviewed'])
        self.assertEqual(refreshed['assets'][0]['status'], 'needs_review')

    def test_refuse_different_pdf_or_duplicate_paper_id(self):
        self.prepared()
        with self.assertRaisesRegex(ValueError, '已登记'):
            assets.register('other-name', self.pdf, self.root)
        other = self.root / 'other.pdf'
        with fitz.open() as doc:
            doc.new_page(); doc.save(other)
        with self.assertRaisesRegex(ValueError, '指纹'):
            assets.register('paper', other, self.root)

    def test_legacy_orphans_and_missing_records_are_not_verified(self):
        folder = assets.paper_dir('paper', self.root); folder.mkdir(parents=True)
        Image.new('RGB', (400, 200), 'white').save(folder / 'orphan.png')
        (folder / 'extraction_summary.json').write_text(json.dumps({
            'items': [{'filename': 'missing.png', 'type': 'table', 'number': 'I', 'page': 2}]
        }))
        data = assets.register('paper', self.pdf, self.root)
        self.assertEqual(len(data['assets']), 2)
        self.assertEqual({a['status'] for a in data['assets']}, {'pending', 'needs_review'})
        self.assertFalse(assets.check(data, self.root)['ok'])

    def test_recrop_preserves_id_and_backups_and_requires_review(self):
        data = self.complete(self.prepared())
        a = data['assets'][0]; old_file = a['file']; old_id = a['id']
        with fitz.open(self.pdf) as doc:
            assets.crop(data, a, doc, self.root, bbox=[40, 100, 520, 430])
        self.assertEqual(a['id'], old_id); self.assertEqual(a['file'], old_file)
        self.assertEqual(a['status'], 'needs_review')
        self.assertTrue(list((self.root / '.cache/paper-assets/paper/revisions').glob('*')))
        self.assertFalse(assets.check(data, self.root)['ok'])

    def test_invalid_path_and_bbox_do_not_touch_assets(self):
        with self.assertRaises(ValueError): assets.paper_dir('../escape', self.root)
        data = self.prepared(); a = data['assets'][0]; before = a.copy()
        with fitz.open(self.pdf) as doc:
            with self.assertRaises(ValueError):
                assets.crop(data, a, doc, self.root, bbox=[-100, 0, 200, 200])
        self.assertEqual(a, before)

    def test_review_sheet_includes_pages_without_successful_crops(self):
        data = self.prepared()
        result = assets.review_sheet(data, self.root)
        self.assertEqual(len(list(result.parent.glob('page-*.png'))), 2)
        self.assertIn('table-s1-p002', result.read_text(encoding='utf-8'))

    def test_unknown_asset_and_unexplained_exclusion_fail_closed(self):
        data = self.complete(self.prepared())
        data['assets'][0]['status'] = 'excluded'
        data['assets'][0]['review'] = {}
        self.assertFalse(assets.check(data, self.root)['ok'])
        Image.new('RGB', (300, 200), 'white').save(assets.paper_dir('paper', self.root) / 'new.png')
        self.assertIn('未登记', '\n'.join(assets.check(data, self.root)['errors']))

    def test_missing_inventory_entry_cannot_keep_reviewed_status(self):
        data = self.complete(self.prepared())
        removed = data['assets'].pop()
        assets.asset_file(data, removed, self.root).unlink()
        self.assertFalse(assets.check(data, self.root)['ok'])

    def test_legacy_import_collision_reuse_and_reference_rewrite(self):
        folder = assets.paper_dir('paper', self.root); folder.mkdir(parents=True)
        Image.new('RGB', (400, 200), 'blue').save(folder / 'fig.png')
        legacy = self.root / 'paper-slides/paper_assets'; legacy.mkdir(parents=True)
        Image.new('RGB', (400, 200), 'red').save(legacy / 'fig.png')
        deck = legacy.parent / 'paper.html'
        deck.write_text('<img src="paper_assets/fig.png">')
        data = assets.import_legacy('paper', legacy, self.pdf, deck, self.root)
        self.assertEqual(len(data['assets']), 2)
        self.assertTrue((legacy / 'fig.png').exists())
        self.assertIn('../assets/paper-imgs/paper/legacy-', deck.read_text())
        repeated = assets.import_legacy('paper', legacy, self.pdf, deck, self.root)
        self.assertEqual(len(repeated['assets']), 2)

    def test_legacy_import_preserves_missing_records_without_duplicates(self):
        legacy = self.root / 'paper-slides/paper_assets'; legacy.mkdir(parents=True)
        (legacy / 'extraction_summary.json').write_text(json.dumps({
            'items': [{'filename': 'missing.png', 'type': 'table', 'number': 'S1', 'page': 2}]
        }))
        data = assets.import_legacy('paper', legacy, self.pdf, root=self.root)
        self.assertEqual(len(data['assets']), 1)
        self.assertEqual(data['assets'][0]['status'], 'pending')
        self.assertEqual(data['assets'][0]['kind'], 'table')
        self.assertFalse(assets.check(data, self.root)['ok'])
        repeated = assets.import_legacy('paper', legacy, self.pdf, root=self.root)
        self.assertEqual(data, repeated)


if __name__ == '__main__':
    unittest.main()
