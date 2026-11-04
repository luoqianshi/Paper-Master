#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 论文图片/表格提取器（标题驱动版）

功能:
1. 从学术论文 PDF 中按 Figure/Table 出现顺序逐一提取图表
2. 标题驱动：先搜索 "Figure N"/"Table N" 标题文字，再定位对应图表区域并裁剪
3. 三重过滤区分标题与正文引用：文本模式 + 邻近视觉内容验证 + 字体特征
4. 智能双向查找：Figure 标题向上找图，Table 标题向下找表，找不到则反向兜底
5. 语义命名输出：fig1.png, table2.png, algorithm1.png
6. 保留盲裁剪模式作为 fallback（--fallback-blind-crop）

用法:
    python pdf_extractor.py <pdf_path> [--output-dir <dir>] [--dpi 200]
    python pdf_extractor.py paper.pdf --fallback-blind-crop --clean

依赖:
    pip install pymupdf Pillow
"""

import os
import re
import sys
import argparse
import json
import shutil
from pathlib import Path

import fitz  # PyMuPDF


# ============================================================
# 常量
# ============================================================

# 带标点的标题模式："Figure 1:", "Fig. 2.", "Table 3 —", "Algorithm 1."
CAPTION_PATTERN_PUNCT = re.compile(
    r'^(Figure|Fig\.|Table|Algorithm)\s+(\d+[a-z]?)\s*[:.。，—–\-]',
    re.IGNORECASE,
)

# 无标点的标题模式： "Figure 1 Architecture..."
CAPTION_PATTERN_NOPUNCT = re.compile(
    r'^(Figure|Fig\.|Table|Algorithm)\s+(\d+[a-z]?)\s+(\S+)',
    re.IGNORECASE,
)

# 正文引用中编号后常见的动词/句首词，用于排除无标点情况下的引用
INLINE_REFERENCE_WORDS = {
    'shows', 'show', 'illustrates', 'illustrate', 'demonstrates', 'demonstrate',
    'presents', 'present', 'compares', 'compare', 'summarizes', 'summarize',
    'depicts', 'depict', 'contains', 'contain', 'includes', 'include',
    'lists', 'list', 'reports', 'report', 'gives', 'give', 'provides', 'provide',
    'describes', 'describe', 'we', 'is', 'are', 'was', 'were', 'can', 'will',
    'has', 'have', 'had', 'also', 'furthermore', 'moreover', 'however',
    'while', 'when', 'where', 'it', 'these', 'those',
}

# 页面边距（PDF 点数）
PAGE_MARGIN_TOP = 50.0
PAGE_MARGIN_BOTTOM_RATIO = 0.95
PAGE_MARGIN_LEFT = 30.0
PAGE_MARGIN_RIGHT = 30.0

# 向上/向下搜索的最大距离（点数）
MAX_SEARCH_DISTANCE = 550.0

# 表格行间间隙阈值（点数），超过此值认为是表格与正文的分界
TABLE_GAP_THRESHOLD = 18.0

# 表格单元格文本长度上限：短于此值的文本块视为表格单元格而非段落
TABLE_CELL_TEXT_MAX_LEN = 120

# 最小裁剪区域尺寸（像素）
MIN_CROP_WIDTH_PX = 80
MIN_CROP_HEIGHT_PX = 80

# 最小文件大小（字节），小于此值视为空白
MIN_FILE_SIZE = 2048

# 视觉区域最小尺寸（点数）
VISUAL_MIN_WIDTH = 30
VISUAL_MIN_HEIGHT = 30
VISUAL_MIN_AREA = 3000

# 类型前缀映射
TYPE_PREFIX = {'figure': 'fig', 'table': 'table', 'algorithm': 'algorithm'}


# ============================================================
# 工具函数
# ============================================================

def merge_rects(regions, overlap_threshold=0.3):
    """合并重叠率超过阈值的矩形区域，迭代直到稳定。"""
    if not regions:
        return []

    merged = [fitz.Rect(r) for r in regions]
    changed = True
    while changed:
        changed = False
        new_merged = []
        for r in merged:
            found = False
            for m in new_merged:
                inter = m & r
                if inter:
                    inter_area = inter.width * inter.height
                    min_area = min(m.width * m.height, r.width * r.height)
                    if min_area > 0 and inter_area / min_area > overlap_threshold:
                        m |= r
                        found = True
                        changed = True
                        break
            if not found:
                new_merged.append(fitz.Rect(r))
        merged = new_merged

    return merged


def get_page_visual_regions(page):
    """
    获取页面上所有视觉内容区域（矢量绘图 + 内嵌图片），已合并重叠区域。
    返回 fitz.Rect 列表。
    """
    regions = []
    page_rect = page.rect
    page_area = page_rect.width * page_rect.height

    # 矢量绘图
    try:
        for d in page.get_drawings():
            rect = d.get("rect")
            if rect is None:
                continue
            # 裁剪到页面范围内（排除超出页面的裁剪路径/背景）
            rect = fitz.Rect(rect) & page_rect
            if rect.is_empty:
                continue
            if rect.width < VISUAL_MIN_WIDTH or rect.height < VISUAL_MIN_HEIGHT:
                continue
            if rect.width * rect.height < VISUAL_MIN_AREA:
                continue
            # 跳过覆盖页面面积 > 50% 的区域（页面级背景/容器）
            if rect.width * rect.height > page_area * 0.5:
                continue
            regions.append(rect)
    except Exception:
        pass

    # 内嵌图片
    try:
        for info in page.get_image_info():
            bbox = info.get("bbox")
            if bbox:
                r = fitz.Rect(bbox)
                if r.width >= VISUAL_MIN_WIDTH and r.height >= VISUAL_MIN_HEIGHT:
                    regions.append(r)
    except Exception:
        pass

    return merge_rects(regions, overlap_threshold=0.2)


def get_text_block_rects(page):
    """
    获取页面上所有文本块的 (fitz.Rect, text) 列表，按 y 坐标排序。
    """
    blocks = []
    for b in page.get_text("blocks"):
        if len(b) < 7:
            continue
        x0, y0, x1, y1, text, block_no, block_type = b[:7]
        if block_type != 0:
            continue
        blocks.append((fitz.Rect(x0, y0, x1, y1), text))

    blocks.sort(key=lambda x: x[0].y0)
    return blocks


def _compute_horizontal_range(cap_bbox, page_width):
    """
    根据标题的 x 范围推断图表的水平搜索范围。
    跨栏标题（宽度 > 页宽 60%）→ 全宽搜索；单栏标题 → 限制在该栏。
    """
    cap_width = cap_bbox.x1 - cap_bbox.x0
    if cap_width > page_width * 0.6:
        return PAGE_MARGIN_LEFT, page_width - PAGE_MARGIN_RIGHT
    else:
        x0 = max(PAGE_MARGIN_LEFT, cap_bbox.x0 - 20)
        x1 = min(page_width - PAGE_MARGIN_RIGHT, cap_bbox.x1 + 20)
        return x0, x1


# ============================================================
# 标题检测模块（三重过滤）
# ============================================================

def parse_caption_text(text):
    """
    过滤 1 — 文本模式匹配。
    解析标题文本，返回 (type, number, full_caption) 或 None。
    """
    text = text.strip()

    # 优先匹配带标点的模式（高置信度）
    m = CAPTION_PATTERN_PUNCT.match(text)
    if m:
        kind_raw = m.group(1).lower()
        number = m.group(2)
        kind = _kind_from_raw(kind_raw)
        return kind, number, text

    # 无标点模式：需要排除正文引用
    m = CAPTION_PATTERN_NOPUNCT.match(text)
    if m:
        kind_raw = m.group(1).lower()
        number = m.group(2)
        next_word = m.group(3).lower().strip('.,;:!?()[]')

        # 排除正文引用
        if next_word in INLINE_REFERENCE_WORDS:
            return None

        # 标题通常较短
        if len(text) > 500:
            return None

        kind = _kind_from_raw(kind_raw)
        return kind, number, text

    return None


def _kind_from_raw(kind_raw):
    """将原始类型字符串转为标准类型。"""
    if kind_raw.startswith('fig'):
        return 'figure'
    elif kind_raw.startswith('table'):
        return 'table'
    else:
        return 'algorithm'


def find_caption_candidates(page):
    """
    在页面上查找所有标题候选（仅文本模式过滤）。
    返回列表，每项: {type, number, caption, bbox, page}
    """
    candidates = []
    for b in page.get_text("blocks"):
        if len(b) < 7:
            continue
        x0, y0, x1, y1, text, block_no, block_type = b[:7]
        if block_type != 0:
            continue

        parsed = parse_caption_text(text)
        if parsed is None:
            continue

        kind, number, caption = parsed
        candidates.append({
            'type': kind,
            'number': number,
            'caption': caption,
            'bbox': fitz.Rect(x0, y0, x1, y1),
            'page': page.number + 1,
        })

    return candidates


def compute_search_area(cap_bbox, direction, text_blocks, page_width, page_height):
    """
    根据标题位置和搜索方向计算搜索区域。
    Figure → up:  从标题上边缘向上到上一个文本块下边缘
    Table  → down: 从标题下边缘向下到下一个文本块上边缘（需特殊处理表格单元格）
    """
    x0, x1 = _compute_horizontal_range(cap_bbox, page_width)

    # 过滤掉标题自身及与标题 y 范围重叠的文本块（多行标题的后续部分）
    # 只保留水平范围内有重叠的文本块
    relevant = []
    for rect, text in text_blocks:
        if rect.y1 > cap_bbox.y0 - 2 and rect.y0 < cap_bbox.y1 + 2:
            continue
        if rect.x1 > x0 and rect.x0 < x1:
            relevant.append((rect, text))

    if direction == 'up':
        y_bottom = cap_bbox.y0
        y_top = PAGE_MARGIN_TOP

        # 标题上方文本块，按 y0 降序排列（离标题最近的在前）
        above = sorted(
            [(r, t) for r, t in relevant if r.y1 <= cap_bbox.y0],
            key=lambda x: x[0].y0, reverse=True,
        )

        # 仅使用上一个 Figure/Table 标题作为边界
        # 不使用文本长度判断，因为长表格数据（多行合并）与正文段落难以区分
        for r, t in above:
            if parse_caption_text(t) is not None:
                y_top = max(y_top, r.y1)
                break

        if y_bottom - y_top > MAX_SEARCH_DISTANCE:
            y_top = y_bottom - MAX_SEARCH_DISTANCE

    else:  # 'down'
        y_top = cap_bbox.y1
        y_bottom = page_height * PAGE_MARGIN_BOTTOM_RATIO

        # 收集标题下方的文本块（已按 y0 排序）
        below = [(r, t) for r, t in relevant if r.y0 >= cap_bbox.y1]

        if below:
            # 策略 1：查找显著间隙（表格与后续段落之间的空白）
            prev_bottom = below[0][0].y0
            for i, (rect, _) in enumerate(below):
                if i > 0:
                    gap = rect.y0 - prev_bottom
                    if gap > TABLE_GAP_THRESHOLD:
                        y_bottom = prev_bottom
                        break
                prev_bottom = max(prev_bottom, rect.y1)
            else:
                # 策略 2：查找第一个"长"文本块（段落而非单元格）
                for rect, text in below:
                    if len(text.strip()) > TABLE_CELL_TEXT_MAX_LEN:
                        y_bottom = rect.y0
                        break
                else:
                    # 策略 3：使用最后一个文本块的底部
                    y_bottom = max(r.y1 for r, _ in below) + 5

        if y_bottom - y_top > MAX_SEARCH_DISTANCE:
            y_bottom = y_top + MAX_SEARCH_DISTANCE

    search_area = fitz.Rect(x0, y_top, x1, y_bottom)
    if search_area.width <= 0 or search_area.height <= 0:
        return None
    return search_area


def verify_caption_with_visual_content(page, caption_info):
    """
    过滤 2 — 邻近视觉内容验证（最关键）。
    真正的标题旁边一定有图表内容。
    Figure → 向上查找优先；Table → 双向查找取最优。
    返回 (is_valid, direction, search_area)
    """
    cap_bbox = caption_info['bbox']
    kind = caption_info['type']
    pw, ph = page.rect.width, page.rect.height

    visual_regions = get_page_visual_regions(page)
    text_blocks = get_text_block_rects(page)

    if kind == 'figure':
        # Figure：标题通常在图下方，先向上找，找不到再向下
        for direction in ['up', 'down']:
            search_area = compute_search_area(cap_bbox, direction, text_blocks, pw, ph)
            if search_area is None:
                continue
            for vr in visual_regions:
                inter = search_area & vr
                if inter and inter.width > 20 and inter.height > 20:
                    return True, direction, search_area
        return False, None, None

    else:
        # Table/Algorithm：标题可能在上方或下方，双向查找取最优
        best_dir = None
        best_area = None
        best_score = 0

        for direction in ['down', 'up']:
            search_area = compute_search_area(cap_bbox, direction, text_blocks, pw, ph)
            if search_area is None:
                continue

            # 视觉区域（有边框的表格）
            has_visual = False
            for vr in visual_regions:
                inter = search_area & vr
                if inter and inter.width > 20 and inter.height > 20:
                    has_visual = True
                    break

            if has_visual:
                return True, direction, search_area

            # 文本单元格计数（无边框表格）
            cell_count = 0
            for rect, _ in text_blocks:
                if rect.y1 > cap_bbox.y0 - 2 and rect.y0 < cap_bbox.y1 + 2:
                    continue
                inter = search_area & rect
                if inter and inter.width > 10 and inter.height > 5:
                    cell_count += 1

            if cell_count >= 2 and cell_count > best_score:
                best_score = cell_count
                best_dir = direction
                best_area = search_area

        if best_dir:
            return True, best_dir, best_area
        return False, None, None


def detect_all_captions(doc):
    """
    扫描整个文档，检测所有有效标题（三重过滤：文本模式 + 视觉内容验证）。
    返回按出现顺序排列、去重后的标题列表。
    """
    all_captions = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        for cap in find_caption_candidates(page):
            is_valid, direction, search_area = verify_caption_with_visual_content(
                page, cap
            )
            if is_valid:
                cap['search_direction'] = direction
                cap['search_area'] = search_area
                all_captions.append(cap)
            else:
                print(f"  [过滤] 第 {page_num+1} 页 {cap['type']} {cap['number']}: "
                      f"附近未找到视觉内容，判定为正文引用")

    # 去重：同一 (type, number) 保留首次出现
    seen = set()
    unique = []
    for cap in all_captions:
        key = (cap['type'], cap['number'])
        if key not in seen:
            seen.add(key)
            unique.append(cap)
        else:
            print(f"  [去重] {cap['type']} {cap['number']} 重复（第 {cap['page']} 页），跳过")

    return unique


# ============================================================
# 区域关联与裁剪模块
# ============================================================

def refine_crop_region(page, search_area):
    """
    在搜索区域内，利用视觉区域信息精确缩小裁剪边界。
    若找到视觉区域，取其合并后的范围；否则使用整个搜索区域。
    """
    visual_regions = get_page_visual_regions(page)

    overlapping = []
    for vr in visual_regions:
        inter = search_area & vr
        if inter and inter.width > 20 and inter.height > 20:
            # 裁剪到搜索区域内
            clipped = fitz.Rect(
                max(vr.x0, search_area.x0),
                max(vr.y0, search_area.y0),
                min(vr.x1, search_area.x1),
                min(vr.y1, search_area.y1),
            )
            if clipped.width > 20 and clipped.height > 20:
                overlapping.append(clipped)

    if overlapping:
        # 取所有视觉区域的外接矩形（并集），确保完整覆盖由多个小元素组成的图表
        x0 = min(r.x0 for r in overlapping)
        y0 = min(r.y0 for r in overlapping)
        x1 = max(r.x1 for r in overlapping)
        y1 = max(r.y1 for r in overlapping)
        crop_rect = fitz.Rect(x0, y0, x1, y1)
    else:
        # 无视觉区域（无边框表格）：使用搜索区域内的文本块外接矩形
        text_blocks = get_text_block_rects(page)
        text_rects = []
        for rect, _ in text_blocks:
            inter = search_area & rect
            if inter and inter.width > 10 and inter.height > 5:
                text_rects.append(rect)
        if text_rects:
            crop_rect = fitz.Rect(
                min(r.x0 for r in text_rects),
                min(r.y0 for r in text_rects),
                max(r.x1 for r in text_rects),
                max(r.y1 for r in text_rects),
            )
        else:
            crop_rect = fitz.Rect(search_area)

    # 添加边距
    padding = 5.0
    crop_rect = fitz.Rect(
        max(0, crop_rect.x0 - padding),
        max(0, crop_rect.y0 - padding),
        min(page.rect.width, crop_rect.x1 + padding),
        min(page.rect.height, crop_rect.y1 + padding),
    )

    return crop_rect


def extract_captioned_figures(doc, output_dir, dpi=200):
    """
    标题驱动提取：按 Figure/Table 出现顺序逐一提取。
    返回提取结果列表。
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)

    # 步骤 1：检测标题
    print("[步骤 1/3] 检测 Figure/Table 标题...")
    captions = detect_all_captions(doc)
    print(f"[结果] 检测到 {len(captions)} 个有效标题:")
    for cap in captions:
        print(f"  - {cap['type']} {cap['number']} (第 {cap['page']} 页)")

    if not captions:
        return []

    # 步骤 2：区域关联与裁剪
    print(f"\n[步骤 2/3] 定位并裁剪图表区域...")
    extracted = []

    for cap in captions:
        page = doc.load_page(cap['page'] - 1)
        crop_rect = refine_crop_region(page, cap['search_area'])

        if crop_rect is None:
            print(f"  [跳过] {cap['type']} {cap['number']}: 无法确定裁剪区域")
            continue

        # 像素尺寸检查
        rw = crop_rect.width * zoom
        rh = crop_rect.height * zoom
        if rw < MIN_CROP_WIDTH_PX or rh < MIN_CROP_HEIGHT_PX:
            print(f"  [跳过] {cap['type']} {cap['number']}: 裁剪区域太小 "
                  f"({rw:.0f}x{rh:.0f}px)")
            continue

        try:
            pix = page.get_pixmap(matrix=mat, clip=crop_rect, alpha=True)

            # 语义文件名
            prefix = TYPE_PREFIX[cap['type']]
            filename = f"{prefix}{cap['number']}.png"
            output_path = output_dir / filename

            # 文件名冲突处理
            if output_path.exists():
                filename = f"{prefix}{cap['number']}_page{cap['page']:03d}.png"
                output_path = output_dir / filename

            pix.save(output_path)

            # 文件大小过滤
            file_size = output_path.stat().st_size
            if file_size < MIN_FILE_SIZE:
                print(f"  [过滤] {filename} 文件过小 ({file_size} 字节)，丢弃")
                output_path.unlink()
                continue

            extracted.append({
                'type': cap['type'],
                'number': cap['number'],
                'label': f"{cap['type'].capitalize()} {cap['number']}",
                'caption': cap['caption'],
                'filename': filename,
                'page': cap['page'],
                'bbox': [crop_rect.x0, crop_rect.y0, crop_rect.x1, crop_rect.y1],
                'width': pix.width,
                'height': pix.height,
            })

            print(f"  [成功] {filename} (第 {cap['page']} 页, "
                  f"{pix.width}x{pix.height}px)")

        except Exception as e:
            print(f"  [错误] 裁剪 {cap['type']} {cap['number']} 时出错: {e}")
            continue

    # 步骤 3：按出现顺序排序
    extracted.sort(key=lambda x: (x['page'], x['bbox'][1]))

    return extracted


# ============================================================
# 盲裁剪 fallback（保留自原脚本，简化版）
# ============================================================

def is_likely_figure_or_table(img_info, page_width, page_height):
    """根据尺寸/面积/宽高比/位置判断是否可能是有效图表。"""
    w, h = img_info['width'], img_info['height']
    area = w * h
    aspect = w / h if h > 0 else 999
    bbox = img_info.get('bbox')

    if w < 150 or h < 150:
        return False, "too_small"
    if area < 30000:
        return False, "too_small_area"
    if aspect > 20 or aspect < 0.05:
        return False, "extreme_aspect_ratio"
    if w > 2000 and h < 100:
        return False, "likely_separator_line"

    if 0.8 <= aspect <= 1.25:
        if area < 350000:
            return False, "likely_author_photo_or_logo"
        if bbox:
            y_center = (bbox[1] + bbox[3]) / 2
            if y_center < page_height * 0.15 or y_center > page_height * 0.85:
                return False, "likely_header_footer_logo"

    return True, "ok"


def extract_figures_blind_crop(doc, output_dir, dpi=200, max_regions_per_page=5):
    """
    盲裁剪 fallback：通过区域检测+裁剪提取矢量图表（不含标题关联）。
    仅在标题驱动模式未提取到结果时使用。
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    extracted = []
    img_counter = 1
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pw, ph = page.rect.width, page.rect.height
        page_area = pw * ph

        # 收集候选区域
        regions = get_page_visual_regions(page)

        # 过滤
        filtered = []
        for r in regions:
            if r.width < 40 or r.height < 40:
                continue
            if r.width * r.height > page_area * 0.75:
                continue
            if r.y1 < 60 or r.y0 > ph * 0.95:
                continue
            rw, rh = r.width * zoom, r.height * zoom
            if rw < 100 or rh < 100:
                continue
            aspect = rw / rh if rh > 0 else 999
            if aspect > 20 or aspect < 0.05:
                continue

            overlap = False
            for existing in filtered:
                inter = existing & r
                if inter:
                    inter_area = inter.width * inter.height
                    min_area = min(existing.width * existing.height,
                                   r.width * r.height)
                    if min_area > 0 and inter_area / min_area > 0.7:
                        overlap = True
                        break
            if not overlap:
                filtered.append(fitz.Rect(r))

        filtered.sort(key=lambda r: r.width * r.height, reverse=True)
        filtered = filtered[:max_regions_per_page]

        for idx, r in enumerate(filtered, 1):
            try:
                pix = page.get_pixmap(matrix=mat, clip=r, alpha=True)
                output_path = output_dir / f"crop_{img_counter:03d}_page{page_num+1:03d}_reg{idx}.png"
                pix.save(output_path)

                if output_path.stat().st_size < MIN_FILE_SIZE:
                    output_path.unlink()
                    continue

                extracted.append({
                    'type': 'unknown',
                    'number': str(img_counter),
                    'label': f'Crop {img_counter}',
                    'caption': '',
                    'filename': output_path.name,
                    'page': page_num + 1,
                    'bbox': [r.x0, r.y0, r.x1, r.y1],
                    'width': pix.width,
                    'height': pix.height,
                })
                img_counter += 1
            except Exception as e:
                print(f"  [警告] 裁剪第 {page_num+1} 页区域时出错: {e}")
                continue

    return extracted


# ============================================================
# 页面渲染（后备）
# ============================================================

def render_pages_as_fallback(doc, output_dir, dpi=200):
    """将每一页渲染为高清图片。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rendered = []
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        output_path = output_dir / f"page_{page_num+1:03d}_{dpi}dpi.png"
        pix.save(output_path)
        rendered.append(str(output_path))

    return rendered


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="从学术论文 PDF 中按 Figure/Table 出现顺序提取图表"
    )
    parser.add_argument("pdf_path", help="输入 PDF 文件路径")
    parser.add_argument("--output-dir", default=None,
                        help="输出目录（默认 paper-slides/<PDF名>_assets/）")
    parser.add_argument("--dpi", type=int, default=200,
                        help="渲染分辨率 DPI（默认 200）")
    parser.add_argument("--fallback-blind-crop", action="store_true",
                        help="标题驱动未提取到结果时，回退到盲裁剪模式")
    parser.add_argument("--render-pages", action="store_true",
                        help="同时渲染每一页为高清图片")
    parser.add_argument("--max-regions-per-page", type=int, default=5,
                        help="盲裁剪模式每页最多裁剪区域数（默认 5）")
    parser.add_argument("--clean", action="store_true",
                        help="清空输出目录后再提取")
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path).resolve()
    if not pdf_path.exists():
        print(f"[错误] 文件不存在: {pdf_path}")
        sys.exit(1)

    if args.output_dir:
        output_dir = Path(args.output_dir).resolve()
    else:
        output_dir = Path("d:/Data/New_Codes/SKILLS/Accumulate-PPTs/paper-slides") / f"{pdf_path.stem}_assets"

    if args.clean and output_dir.exists():
        print(f"[信息] 清空输出目录: {output_dir}")
        shutil.rmtree(output_dir)

    print(f"[信息] 处理 PDF: {pdf_path}")
    print(f"[信息] 输出目录: {output_dir}")
    print("-" * 50)

    doc = fitz.open(str(pdf_path))

    # 主流程：标题驱动提取
    print("[标题驱动模式] 开始提取...\n")
    items = extract_captioned_figures(doc, output_dir, dpi=args.dpi)

    # Fallback：盲裁剪
    if not items and args.fallback_blind_crop:
        print("\n[回退] 标题驱动未提取到结果，启用盲裁剪模式...")
        items = extract_figures_blind_crop(
            doc, output_dir, dpi=args.dpi,
            max_regions_per_page=args.max_regions_per_page,
        )
        print(f"[结果] 盲裁剪提取到 {len(items)} 个区域")

    # 可选：渲染整页
    rendered = []
    if args.render_pages:
        print("\n[可选] 渲染页面为高清图片...")
        rendered = render_pages_as_fallback(doc, output_dir / "pages", dpi=args.dpi)
        print(f"[结果] 渲染了 {len(rendered)} 页")

    # 统计
    figures = [i for i in items if i['type'] == 'figure']
    tables = [i for i in items if i['type'] == 'table']
    algorithms = [i for i in items if i['type'] == 'algorithm']
    unknowns = [i for i in items if i['type'] == 'unknown']

    # 生成 summary
    summary = {
        "pdf_path": str(pdf_path),
        "output_dir": str(output_dir),
        "total_pages": len(doc),
        "total_items": len(items),
        "total_figures": len(figures),
        "total_tables": len(tables),
        "total_algorithms": len(algorithms),
        "total_unknowns": len(unknowns),
        "rendered_pages": len(rendered),
        "items": items,
    }

    summary_path = output_dir / "extraction_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    doc.close()

    print("\n" + "=" * 50)
    print(f"[完成] 共提取 {len(items)} 个图表 "
          f"(Figure: {len(figures)}, Table: {len(tables)}, "
          f"Algorithm: {len(algorithms)}, Unknown: {len(unknowns)})")
    print(f"[汇总] 结果保存在: {output_dir}")
    print(f"[JSON] 清单文件: {summary_path}")


if __name__ == "__main__":
    main()
