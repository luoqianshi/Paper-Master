#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Caption candidates and crop-region heuristics shared by paper_assets.

Heuristics propose crops; paper_assets retains failed candidates and requires
per-asset review plus a page-by-page inventory before declaring completeness.
"""
import re

import fitz  # PyMuPDF


# ============================================================
# 常量
# ============================================================

# 带标点的标题模式："Figure 1:", "Fig. 2.", "Table 3 —", "Algorithm 1."
CAPTION_LABEL = r'(Figure|Fig\.?|Table|Tab\.?|Algorithm|图|表|算法)'
CAPTION_NUMBER = r'((?:[A-Z]\.?\d+|\d+)(?:[.\-]\d+)*(?:[a-z]|\([a-z]\))?|[IVXLCDM]+)'
CAPTION_PATTERN_PUNCT = re.compile(
    rf'^{CAPTION_LABEL}\s*{CAPTION_NUMBER}\s*[:.。，—–\-]',
    re.IGNORECASE,
)

# 无标点的标题模式： "Figure 1 Architecture..."
CAPTION_PATTERN_NOPUNCT = re.compile(
    rf'^{CAPTION_LABEL}\s*{CAPTION_NUMBER}\s+(\S+)',
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
        # A short caption does not imply a narrow figure. Search its whole column;
        # centered captions crossing the gutter may belong to a full-width figure.
        mid = page_width / 2
        if cap_bbox.x0 < mid < cap_bbox.x1:
            return PAGE_MARGIN_LEFT, page_width - PAGE_MARGIN_RIGHT
        x0, x1 = ((PAGE_MARGIN_LEFT, mid - 4) if cap_bbox.x1 <= mid
                  else (mid + 4, page_width - PAGE_MARGIN_RIGHT))
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
    if kind_raw.startswith('fig') or kind_raw == '图':
        return 'figure'
    elif kind_raw.startswith('tab') or kind_raw == '表':
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
    扫描整个文档，检测有效标题（文本模式 + 视觉内容验证）。
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

    # Keep continued tables / repeated numbering on different pages.
    seen = set()
    unique = []
    for cap in all_captions:
        key = (cap['type'], cap['number'], cap['page'], tuple(cap['bbox']))
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


