#!/usr/bin/env python3
"""Shared, non-destructive PDF asset inventory, extraction and review workflow."""
import argparse
import hashlib
import html
import json
import math
import os
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
VERSION = 1
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.svg'}
STATUSES = {'pending', 'needs_review', 'verified', 'excluded'}


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def paper_dir(paper, root=ROOT):
    if not paper or paper in {'.', '..'} or any(c in paper for c in '/\\:'):
        raise ValueError('paper 必须是单个目录名，不能包含路径分隔符')
    return Path(root) / 'assets' / 'paper-imgs' / paper


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def load_manifest(paper, root=ROOT):
    path = paper_dir(paper, root) / 'asset_manifest.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema_version') != VERSION or data.get('paper_id') != paper:
        raise ValueError(f'不支持的素材清单或 paper_id 不符：{path}')
    return data


def save_manifest(data, root=ROOT):
    write_json(paper_dir(data['paper_id'], root) / 'asset_manifest.json', data)


def asset_file(data, asset, root=ROOT):
    folder = paper_dir(data['paper_id'], root).resolve()
    filename = asset.get('file')
    if not filename:
        return None
    path = (folder / filename).resolve()
    if path.parent != folder:
        raise ValueError(f'素材文件必须直接位于论文目录内：{filename}')
    return path


def image_info(path):
    from PIL import Image
    if path.suffix.lower() == '.svg':
        import fitz
        with fitz.open(path) as doc:
            w, h = doc[0].rect.width, doc[0].rect.height
    else:
        with Image.open(path) as image:
            image.load()
            w, h = image.size
    return {'sha256': digest(path), 'width': int(w), 'height': int(h)}


def source_path(data, root=ROOT):
    value = data.get('pdf', {}).get('path')
    return (Path(root) / value).resolve() if value else None


def find_source(summary, root):
    value = summary.get('pdf_path')
    if value:
        path = Path(value)
        if not path.is_absolute():
            path = Path(root) / path
        if path.is_file():
            return path.resolve()
        # Old Windows paths also need to work when the repository is on Linux.
        name = value.replace('\\', '/').rsplit('/', 1)[-1]
        matches = list((Path(root) / 'pdf-papers').rglob(name))
        if len(matches) == 1:
            return matches[0].resolve()
    return None


def bind_source(data, pdf, root):
    import fitz
    pdf = Path(pdf).resolve()
    sha = digest(pdf)
    old_sha = data.get('pdf', {}).get('sha256')
    if old_sha and old_sha != sha:
        raise ValueError('PDF 指纹已变化；请为新版本使用新的 paper ID，避免混用旧图')
    for other in (Path(root) / 'assets/paper-imgs').glob('*/asset_manifest.json'):
        if other.parent.name == data['paper_id']:
            continue
        candidate = json.loads(other.read_text(encoding='utf-8'))
        if candidate.get('pdf', {}).get('sha256') == sha:
            raise ValueError(f"该 PDF 已登记为 {candidate['paper_id']}，请复用该 paper ID")
    with fitz.open(pdf) as doc:
        pages = len(doc)
    try:
        path = pdf.relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        path = str(pdf)
    data['pdf'] = {'path': path, 'sha256': sha, 'pages': pages}


def sync_disk(data, root=ROOT):
    """Register every file, including legacy orphan files; never silently bless it."""
    folder = paper_dir(data['paper_id'], root)
    by_file = {a['file']: a for a in data['assets'] if a.get('file')}
    changed = False
    for path in sorted(folder.iterdir()):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        asset = by_file.get(path.name)
        if asset is None:
            asset = {'id': 'legacy-' + hashlib.sha256(path.name.encode()).hexdigest()[:12],
                     'kind': 'unknown', 'number': None, 'page': None, 'bbox': None,
                     'caption': '', 'file': path.name, 'status': 'needs_review',
                     'method': 'legacy', 'reason': '未登记的历史图片，需对照原页核验'}
            data['assets'].append(asset)
            changed = True
        try:
            info = image_info(path)
            if asset.get('sha256') != info['sha256']:
                asset.update(status='needs_review', reason='新增或内容变化，需重新核验')
                asset.pop('review', None)
                changed = True
            asset.update(info)
        except Exception as exc:
            asset.update(status='pending', reason=f'图片无法读取：{exc}')
            changed = True
    for asset in data['assets']:
        path = asset_file(data, asset, root)
        if asset['status'] != 'excluded' and path and not path.is_file():
            asset.update(status='pending', reason='清单中的图片文件缺失')
            asset.pop('review', None)
            changed = True
    if changed:
        data['inventory'] = {'reviewed': False, 'note': '素材变化后需重新核对原文图表清单'}
    return data


def register(paper, pdf=None, root=ROOT):
    folder = paper_dir(paper, root)
    folder.mkdir(parents=True, exist_ok=True)
    manifest = folder / 'asset_manifest.json'
    if manifest.exists():
        data = load_manifest(paper, root)
    else:
        data = {'schema_version': VERSION, 'paper_id': paper, 'pdf': {},
                'inventory': {'reviewed': False, 'note': '需逐页核对，标题检测不代表原文全集'},
                'assets': []}
        old = folder / 'extraction_summary.json'
        summary = json.loads(old.read_text(encoding='utf-8')) if old.exists() else {}
        for i, item in enumerate(summary.get('items', summary.get('images', []))):
            name = item.get('filename') or item.get('path', '').replace('\\', '/').rsplit('/', 1)[-1]
            if not name:
                continue
            if any(a.get('file') == name for a in data['assets']):
                continue
            data['assets'].append({
                'id': 'legacy-' + hashlib.sha256(name.encode()).hexdigest()[:12],
                'kind': item.get('type', 'unknown'), 'number': item.get('number'),
                'page': item.get('page'), 'bbox': item.get('bbox'),
                'caption': item.get('caption', ''), 'file': name,
                'status': 'needs_review', 'method': 'legacy', 'reason': '历史提取尚未核验',
            })
        pdf = pdf or find_source(summary, root)
    if pdf:
        bind_source(data, pdf, root)
    path = source_path(data, root)
    if path and path.is_file() and digest(path) != data['pdf'].get('sha256'):
        raise ValueError('源 PDF 已被替换，请为新版本使用新的 paper ID')
    sync_disk(data, root)
    save_manifest(data, root)
    return data


def blog_images(paper, root=ROOT):
    """Read Markdown and HTML image references, preserving missing-file evidence."""
    note = Path(root) / 'paper-blogs' / f'{paper}.md'
    if not note.is_file():
        return None
    class Images(HTMLParser):
        def __init__(self):
            super().__init__(); self.images = []
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == 'img' and attrs.get('src'):
                self.images.append((attrs.get('alt', ''), attrs['src']))
    result, section, fenced = [], None, False
    lines = note.read_text(encoding='utf-8').splitlines()
    for i, line in enumerate(lines):
        if line.lstrip().startswith(('```', '~~~')):
            fenced = not fenced
        if fenced:
            continue
        heading = re.match(r'^#{2,3}\s+(.+)', line)
        if heading:
            section = heading[1]
        parser = Images(); parser.feed(line)
        refs = list(parser.images)
        for m in re.finditer(r'!\[([^\]]*)\]\((?:<([^>]+)>|([^\n]+?))\)', line):
            src = m[2] or re.sub(r'\s+[\"\'].*[\"\']\s*$', '', m[3]).strip()
            refs.append((m[1], src))
        for alt, src in refs:
            url = urlsplit(src)
            if url.scheme or url.netloc:
                continue
            path = (note.parent / unquote(url.path)).resolve()
            after = next((x.strip() for x in lines[i+1:i+4] if x.strip()), '')
            result.append({'path': path, 'src': src, 'alt': alt, 'section': section, 'note': after})
    return result


def import_legacy(paper, legacy_dir, pdf=None, html_path=None, root=ROOT):
    """Copy legacy slide assets without deleting originals; optionally rewrite one deck."""
    legacy_dir = Path(legacy_dir).resolve()
    if not legacy_dir.is_dir():
        raise ValueError('legacy-dir 不存在')
    target = paper_dir(paper, root).resolve()
    if target == legacy_dir:
        raise ValueError('源目录已经是共享目录，使用 register 即可')
    old_path = legacy_dir / 'extraction_summary.json'
    summary = json.loads(old_path.read_text(encoding='utf-8')) if old_path.exists() else {}
    data = register(paper, pdf or find_source(summary, root), root)
    known_hashes = {a['sha256']: a['file'] for a in data['assets']
                    if a.get('sha256') and a.get('file') and asset_file(data, a, root).is_file()}
    mapping = {}
    legacy_items = {}
    for it in summary.get('items', summary.get('images', [])):
        name = it.get('filename') or it.get('path', '').replace('\\', '/').rsplit('/', 1)[-1]
        legacy_items[name] = it
    for source in sorted(legacy_dir.iterdir()):
        if not source.is_file() or source.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        sha = digest(source)
        filename = known_hashes.get(sha, source.name)
        destination = target / filename
        if destination.exists() and digest(destination) != sha:
            filename = f'legacy-{sha[:12]}-{source.name}'
            destination = target / filename
        if not destination.exists():
            shutil.copy2(source, destination)
        known_hashes[sha] = filename
        mapping[source.resolve()] = destination.resolve()
    sync_disk(data, root)
    for source, destination in mapping.items():
        item = legacy_items.get(source.name)
        if item:
            a = next(a for a in data['assets'] if a.get('file') == destination.name)
            if not a.get('page'):
                a.update(page=item.get('page'), bbox=item.get('bbox'),
                         kind=item.get('type', 'unknown'), number=item.get('number'),
                         caption=item.get('caption', ''))
    # A historical record without its image is still evidence of a missing asset.
    # Do not let copying only existing files silently shrink the required inventory.
    for name, item in legacy_items.items():
        if not name or (legacy_dir / name).resolve() in mapping:
            continue
        origin = str((legacy_dir / name).resolve())
        aid = 'legacy-missing-' + hashlib.sha256(origin.encode()).hexdigest()[:12]
        if any(a['id'] == aid for a in data['assets']):
            continue
        data['assets'].append({
            'id': aid, 'kind': item.get('type', 'unknown'), 'number': item.get('number'),
            'page': item.get('page'), 'bbox': item.get('bbox'),
            'caption': item.get('caption', ''), 'file': None, 'status': 'pending',
            'method': 'legacy-missing', 'legacy_source': origin,
            'reason': f'旧目录清单记录的图片缺失：{name}，需逐图补提',
        })
        data['inventory'] = {'reviewed': False, 'note': '旧目录存在缺失素材，需补提并核对'}
    save_manifest(data, root)
    if html_path:
        deck = Path(html_path).resolve()
        original = deck.read_text(encoding='utf-8')
        def replace_tag(match):
            def replace_src(m):
                url = urlsplit(m[3])
                if url.scheme or url.netloc:
                    return m[0]
                old = (deck.parent / unquote(url.path)).resolve()
                if old not in mapping:
                    return m[0]
                relative = quote(Path(os.path.relpath(mapping[old], deck.parent)).as_posix())
                return m[1] + m[2] + relative + m[2]
            return re.sub(r'(\bsrc\s*=\s*)([\"\'])(.*?)\2', replace_src, match[0], flags=re.I)
        updated = re.sub(r'<img\b[^>]*>', replace_tag, original, flags=re.I)
        if updated != original:
            backup = Path(root) / '.cache/paper-assets' / paper / 'revisions'
            backup.mkdir(parents=True, exist_ok=True)
            shutil.copy2(deck, backup / f'{digest(deck)[:16]}-{deck.name}')
            deck.write_text(updated, encoding='utf-8')
    return data


def discover(data, doc):
    import pdf_regions as regions
    changed = False
    for page in doc:
        for cap in regions.find_caption_candidates(page):
            matches = [a for a in data['assets'] if a['kind'] == cap['type']
                       and str(a.get('number')).lower() == cap['number'].lower()
                       and a.get('page') == cap['page']]
            if matches:
                asset = matches[0]
                if asset.get('caption_bbox') is None:
                    asset['caption_bbox'] = list(cap['bbox'])
                continue
            base = f"{cap['type']}-{cap['number'].lower()}-p{cap['page']:03d}"
            asset_id = base
            suffix = 2
            while any(a['id'] == asset_id for a in data['assets']):
                asset_id = f'{base}-{suffix}'; suffix += 1
            data['assets'].append({'id': asset_id, 'kind': cap['type'],
                                  'number': cap['number'], 'page': cap['page'],
                                  'caption': cap['caption'], 'caption_bbox': list(cap['bbox']),
                                  'bbox': None, 'file': None, 'status': 'pending',
                                  'method': 'caption', 'reason': '待定位裁剪'})
            changed = True
    if changed:
        data['inventory'] = {'reviewed': False, 'note': '发现新标题，需逐页核对'}


def crop(data, asset, doc, root=ROOT, dpi=200, bbox=None, page=None, force=False):
    import fitz
    import pdf_regions as regions
    old = asset_file(data, asset, root)
    if not force and bbox is None and asset['status'] in {'verified', 'needs_review', 'excluded'}:
        if asset['status'] == 'excluded' or (old and old.is_file() and digest(old) == asset.get('sha256')):
            return
    page_number = page or asset.get('page')
    if not isinstance(page_number, int) or not 1 <= page_number <= len(doc):
        raise ValueError('请指定有效的 --page（从 1 开始）')
    source = doc[page_number - 1]
    if bbox is not None:
        rect = fitz.Rect(bbox)
        if rect.is_empty or rect.is_infinite or not source.rect.contains(rect):
            raise ValueError('bbox 必须是页面范围内的有效 PDF 点坐标 x0 y0 x1 y1')
        method = 'manual-bbox'
    else:
        cb = asset.get('caption_bbox')
        if not cb:
            asset.update(status='pending', reason='无图注坐标，请指定 --page 和 --bbox 逐图补提')
            return
        ok, direction, area = regions.verify_caption_with_visual_content(source, {
            'bbox': fitz.Rect(cb), 'type': asset['kind']})
        if not ok:
            # A failed item remains in the inventory even if other items succeeded.
            asset.update(status='pending', reason='自动定位失败，请查看原页并用 --bbox 补提，或核实为正文引用后排除')
            return
        rect = regions.refine_crop_region(source, area)
        if rect.is_empty:
            asset.update(status='pending', reason='裁剪区域无效，需指定 bbox')
            return
        method = 'caption-region'
    if dpi < 72 or dpi > 600:
        raise ValueError('dpi 必须在 72–600 之间')
    pix = source.get_pixmap(clip=rect, dpi=dpi, alpha=False)
    if min(pix.width, pix.height) < 20:
        raise ValueError('裁剪区域过小，请复核 bbox')
    folder = paper_dir(data['paper_id'], root)
    filename = asset.get('file') or f"{asset['id']}.png"
    if Path(filename).suffix.lower() == '.svg':
        raise ValueError('SVG 原图不能被位图静默替换；用新素材 ID 补提，再明确排除旧版本')
    dest = folder / filename
    if old and old.is_file():
        backup = Path(root) / '.cache/paper-assets' / data['paper_id'] / 'revisions'
        backup.mkdir(parents=True, exist_ok=True)
        shutil.copy2(old, backup / f'{digest(old)[:16]}-{old.name}')
    tmp = dest.with_name(dest.stem + '.tmp' + dest.suffix)
    pix.pil_save(tmp)
    tmp.replace(dest)
    asset.update(file=filename, page=page_number, bbox=list(rect), method=method,
                 status='needs_review', reason='已提取，需对照原页检查边缘、图例、表头和完整性',
                 dpi=dpi, **image_info(dest))
    asset.pop('review', None)
    data['inventory'] = {'reviewed': False, 'note': '裁剪更新后需重新确认完整性'}


def prepare(paper, pdf=None, root=ROOT, dpi=200):
    import fitz
    data = register(paper, pdf, root)
    path = source_path(data, root)
    if not path or not path.is_file():
        raise ValueError('未定位源 PDF，请通过 --pdf 指定')
    with fitz.open(path) as doc:
        discover(data, doc)
        for asset in data['assets']:
            if asset['status'] == 'pending' and asset.get('caption_bbox'):
                try:
                    crop(data, asset, doc, root, dpi)
                except Exception as exc:
                    asset.update(status='pending', reason=str(exc))
    save_manifest(data, root)
    return data


def check(data, root=ROOT, require_inventory=True):
    errors = []
    if not data.get('pdf', {}).get('sha256'):
        errors.append('缺少源 PDF 指纹，请 prepare --pdf')
    source = source_path(data, root)
    if source and source.is_file() and digest(source) != data['pdf'].get('sha256'):
        errors.append('源 PDF 指纹不符')
    if require_inventory and not data.get('inventory', {}).get('reviewed'):
        errors.append('原文图表清单未逐页核验（review-inventory）')
    if data.get('inventory', {}).get('reviewed') and (
            data['inventory'].get('pdf_sha256') != data.get('pdf', {}).get('sha256')
            or data['inventory'].get('asset_fingerprint') != inventory_fingerprint(data)
            or not data['inventory'].get('note')):
        errors.append('原文清单核验记录与 PDF 不匹配或缺少核验说明')
    ids, files = set(), set()
    for a in data['assets']:
        if a['id'] in ids:
            errors.append(f"重复素材 ID：{a['id']}")
        ids.add(a['id'])
        if a.get('status') not in STATUSES:
            errors.append(f"{a['id']}: 未知状态")
        if a['status'] == 'excluded':
            if not a.get('review', {}).get('note'):
                errors.append(f"{a['id']}: 排除项缺少理由")
            if a.get('file'):
                files.add(a['file'])
                path = asset_file(data, a, root)
                if path.is_file() and digest(path) != a.get('sha256'):
                    errors.append(f"{a['id']}: 排除项图片已变化，需要重新确认排除理由")
            continue
        if a['status'] != 'verified':
            errors.append(f"{a['id']}: {a['status']} — {a.get('reason', '')}")
        path = asset_file(data, a, root)
        if a.get('file') in files:
            errors.append(f"重复文件关联：{a.get('file')}")
        if a.get('file'):
            files.add(a['file'])
        if not path or not path.is_file():
            errors.append(f"{a['id']}: 文件缺失")
        elif digest(path) != a.get('sha256'):
            errors.append(f"{a['id']}: 图片内容变化，需要重新核验")
        if a['status'] == 'verified':
            review = a.get('review', {})
            if (review.get('sha256') != a.get('sha256') or not review.get('note')
                    or review.get('pdf_sha256') != data.get('pdf', {}).get('sha256')
                    or review.get('page') != a.get('page') or review.get('bbox') != a.get('bbox')):
                errors.append(f"{a['id']}: 缺少有效的核验记录")
            box = a.get('bbox')
            if (not isinstance(a.get('page'), int) or not 1 <= a['page'] <= data.get('pdf', {}).get('pages', 0)
                    or not isinstance(box, list) or len(box) != 4
                    or not all(isinstance(x, (int, float)) and math.isfinite(x) for x in box)
                    or box[0] >= box[2] or box[1] >= box[3]):
                errors.append(f"{a['id']}: 缺少来源页码或裁剪坐标")
    folder = paper_dir(data['paper_id'], root)
    untracked = sorted(p.name for p in folder.iterdir() if p.is_file()
                       and p.suffix.lower() in IMAGE_EXTENSIONS and p.name not in files)
    if untracked:
        errors.append(f'存在未登记图片：{untracked}；先运行 register')
    return {'ok': not errors, 'errors': errors,
            'required': [a['id'] for a in data['assets'] if a['status'] != 'excluded'],
            'excluded': [{'id': a['id'], 'reason': a.get('review', {}).get('note')}
                         for a in data['assets'] if a['status'] == 'excluded']}


def inventory_fingerprint(data):
    fields = ('id', 'kind', 'number', 'page', 'bbox', 'file', 'sha256', 'status')
    value = [{k: a.get(k) for k in fields} for a in sorted(data['assets'], key=lambda a: a['id'])]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def confirm_inventory(data, note, root=ROOT):
    if not note.strip():
        raise ValueError('需要记录逐页核对结果')
    report = check(data, root, require_inventory=False)
    if not report['ok']:
        raise ValueError('\n'.join(report['errors']))
    data['inventory'] = {'reviewed': True, 'note': note.strip(),
                         'pdf_sha256': data['pdf']['sha256'],
                         'asset_fingerprint': inventory_fingerprint(data)}
    save_manifest(data, root)


def review_asset(data, asset_id, status, note, root=ROOT):
    if status not in {'verified', 'excluded'} or not note.strip():
        raise ValueError('核验须选择 verified/excluded 并提供具体 --note')
    asset = next((a for a in data['assets'] if a['id'] == asset_id), None)
    if asset is None:
        raise ValueError(f'清单中不存在素材 ID：{asset_id}；请指定有效的 --asset')
    path = asset_file(data, asset, root)
    if status == 'verified':
        if not path or not path.is_file() or not asset.get('page') or not asset.get('bbox'):
            raise ValueError('缺少图片、页码或 bbox；请先逐图补提')
        if digest(path) != asset.get('sha256'):
            raise ValueError('文件已变化；先 register 刷新后重新查看')
        if not data.get('pdf', {}).get('sha256'):
            raise ValueError('缺少 PDF 指纹；请先 prepare --pdf')
    asset.update(status=status, reason=note.strip())
    asset['review'] = {'note': note.strip(), 'sha256': asset.get('sha256'),
                       'pdf_sha256': data.get('pdf', {}).get('sha256'),
                       'page': asset.get('page'), 'bbox': asset.get('bbox')}
    data['inventory']['reviewed'] = False
    save_manifest(data, root)


def review_sheet(data, root=ROOT):
    """Render every original page, not only pages with detected captions."""
    import fitz
    path = source_path(data, root)
    if not path or not path.is_file():
        raise ValueError('生成对照页需要源 PDF')
    out = Path(root) / '.cache/paper-assets' / data['paper_id'] / 'review'
    out.mkdir(parents=True, exist_ok=True)
    esc = html.escape
    body = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>图表核验</title>',
            '<style>body{font:16px sans-serif;margin:24px;background:#eee}section{background:white;padding:20px;margin:20px 0}img{max-width:100%;height:auto}.asset{display:inline-block;vertical-align:top;width:46%;margin:1%;overflow-wrap:anywhere}.page{max-width:850px}p{white-space:pre-wrap}</style>',
            f'<h1>{esc(data["paper_id"])}：原页与素材逐项核验</h1>',
            '<p>逐页检查遗漏标题、跨页续表、子图、坐标轴和图例。红框是当前裁剪边界，不代表已核验。发现漏项用 extract --asset 新ID --page 页码 --bbox 坐标登记。先逐图 review，最后 review-inventory。</p>']
    with fitz.open(path) as doc:
        for i, page in enumerate(doc, 1):
            members = [a for a in data['assets'] if a.get('page') == i]
            for a in members:
                if a.get('bbox'):
                    page.draw_rect(fitz.Rect(a['bbox']), color=(1, 0, 0), width=1)
            name = f'page-{i:03d}.png'
            page.get_pixmap(dpi=110, alpha=False).save(out / name)
            body.extend([f'<section><h2>PDF 第 {i} 页</h2><img class="page" src="{name}">'])
            for a in members:
                body.append(f'<div class="asset"><h3>{esc(a["id"])} · {esc(a["status"])}</h3>')
                image = asset_file(data, a, root)
                if image and image.is_file():
                    rel = quote(Path(os.path.relpath(image, out)).as_posix())
                    body.append(f'<img src="{rel}">')
                body.append(f'<p>{esc(a.get("caption", ""))}\n{esc(a.get("reason", ""))}</p></div>')
            body.append('</section>')
    unresolved = [a['id'] for a in data['assets'] if not a.get('page')]
    body.append('<h2>尚无来源页码的历史素材</h2><pre>' + esc('\n'.join(unresolved)) + '</pre></html>')
    result = out / 'index.html'
    result.write_text('\n'.join(body), encoding='utf-8')
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=['register', 'import-legacy', 'prepare', 'extract', 'review-sheet', 'review', 'review-inventory', 'check'])
    ap.add_argument('--paper', required=True)
    ap.add_argument('--pdf')
    ap.add_argument('--legacy-dir')
    ap.add_argument('--html', help='import-legacy 可选：只改写指定 HTML 的图片路径，保留备份')
    ap.add_argument('--asset')
    ap.add_argument('--page', type=int)
    ap.add_argument('--bbox', nargs=4, type=float)
    ap.add_argument('--kind', choices=['figure', 'table', 'algorithm', 'unknown'], default='figure')
    ap.add_argument('--caption', default='')
    ap.add_argument('--status', choices=['verified', 'excluded'])
    ap.add_argument('--note', default='')
    ap.add_argument('--dpi', type=int, default=200)
    ap.add_argument('--force', action='store_true', help='只重提指定 asset，备份旧图后重置核验状态')
    args = ap.parse_args()
    try:
        if args.action == 'import-legacy':
            if not args.legacy_dir:
                raise ValueError('import-legacy 需要 --legacy-dir')
            data = import_legacy(args.paper, args.legacy_dir, args.pdf, args.html)
        elif args.action == 'prepare':
            data = prepare(args.paper, args.pdf, dpi=args.dpi)
        elif args.action == 'register':
            data = register(args.paper, args.pdf)
        else:
            data = load_manifest(args.paper)
        if args.action == 'extract':
            import fitz
            if not args.asset or not re.fullmatch(r'[a-zA-Z0-9_.()-]+', args.asset):
                raise ValueError('--asset 必须为安全的英文/数字 ID')
            asset = next((a for a in data['assets'] if a['id'] == args.asset), None)
            if asset is None:
                if not args.bbox or not args.page or not args.caption:
                    raise ValueError('补登记新素材需要 --page、--bbox、--caption')
                asset = {'id': args.asset, 'kind': args.kind, 'number': None,
                         'page': args.page, 'bbox': None, 'caption': args.caption,
                         'file': None, 'status': 'pending', 'method': 'manual', 'reason': ''}
                data['assets'].append(asset)
            path = source_path(data)
            if not path or digest(path) != data['pdf'].get('sha256'):
                raise ValueError('源 PDF 缺失或指纹不符')
            with fitz.open(path) as doc:
                crop(data, asset, doc, dpi=args.dpi, bbox=args.bbox, page=args.page, force=args.force)
            save_manifest(data)
        elif args.action == 'review':
            review_asset(data, args.asset, args.status, args.note)
        elif args.action == 'review-inventory':
            confirm_inventory(data, args.note)
        elif args.action == 'review-sheet':
            print(review_sheet(data))
            return
        report = check(data)
        print(json.dumps({'paper': args.paper, **report}, ensure_ascii=False, indent=2))
        # prepare/register/extract produce a review queue, never claim success of QA.
        if args.action == 'check' and not report['ok']:
            sys.exit(1)
    except (ValueError, OSError, KeyError, StopIteration) as exc:
        print(f'[assets] {exc}', file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
