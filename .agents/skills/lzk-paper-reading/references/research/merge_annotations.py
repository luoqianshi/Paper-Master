#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
merge_annotations.py —— 合并 14 批次标注 + L0 机器索引，产出逐篇骨架标注表与聚合统计

用法:
    python merge_annotations.py <skill目录>
"""
import csv
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

FIELDS = ['file', 'skeleton_variant', 'deviation_reason', 'h3_logic', 'motivation_pattern',
          'contribution_form', 'formula_style', 'table_types', 'pros_themes', 'transferable']


def parse_batch(path):
    """从 batch-Bxx.md 中抽取 CSV 数据行。

    子代理实际输出有两个不规则之处，在此统一吸收：
      1) 文件名常被简写（如 `02-controlburn` 而非 `02-controlburn-feature-....md`）
      2) 字段内部的竖线用 `\\|` 转义（如 `组件对应表（节点划分策略\\|说明）`）
    因此先把转义竖线换成全角斜杠，再切分；字段数超过 10 时，多余部分并入 deviation_reason
    （它是唯一天然可能含竖线的字段），保证后续列不错位。
    """
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            s = line.strip().strip('`').strip()
            if s.count('|') < 8 or s.startswith('---'):
                continue
            if s.startswith('file|'):          # 表头
                continue
            cells = [c.strip() for c in s.replace('\\|', '／').split('|')]
            if not cells[0] or cells[0] == 'file':
                continue
            # 部分批次首字段带分类前缀（如 `回归/01-smote-regression`），去掉
            cells[0] = cells[0].split('/')[-1]
            # 首字段必须是类似文件名的编号形式（01-xxx / 22-xxx）
            if not re.match(r'^\d{2}-[a-z0-9\-]', cells[0]):
                continue
            if len(cells) > 10:                # 多余列并入 deviation_reason
                cells = [cells[0], cells[1], '／'.join(cells[2:len(cells) - 7])] + cells[len(cells) - 7:]
            rows.append(cells[:10] + [''] * (10 - len(cells)))
    return rows


def resolve_name(short, pool):
    """把简写文件名匹配回全名：精确 → 前缀 → 编号。"""
    if short in pool:
        return short
    cands = [p for p in pool if p.startswith(short)]
    if len(cands) == 1:
        return cands[0]
    if cands:                                   # 多个前缀命中时取最长公共匹配失败则取第一个
        return sorted(cands, key=len)[0]
    num = short.split('-')[0]
    cands = [p for p in pool if p.startswith(num + '-')]
    return cands[0] if len(cands) == 1 else None


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rdir = os.path.join(root, 'references', 'research')

    # L0 索引
    l0 = {}
    with open(os.path.join(rdir, 'per-note-index.jsonl'), 'r', encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            l0[r['file']] = r

    # 合并 14 批
    rows = []
    for p in sorted(glob.glob(os.path.join(rdir, 'batch-B*.md'))):
        rows.extend(parse_batch(p))

    # 去重 + 补全 L0 字段
    seen, merged, unresolved = set(), [], []
    for r in rows:
        d = dict(zip(FIELDS, r))
        full = resolve_name(d['file'], l0)
        if full is None:
            unresolved.append(d['file'])
            continue
        if full in seen:
            continue
        seen.add(full)
        d['file'] = full
        meta = l0.get(full, {})
        d['category'] = meta.get('category', '')
        d['date'] = meta.get('fm_date', '')
        d['chars'] = meta.get('chars', 0)
        d['n_h3'] = meta.get('n_h3', 0)
        d['n_img'] = meta.get('n_img', 0)
        d['n_math'] = meta.get('n_inline_math', 0) + meta.get('n_display_math', 0)
        d['n_pros'] = meta.get('n_pros_items', 0)
        d['h2_seq'] = ' > '.join(meta.get('h2_seq', []))
        merged.append(d)

    out_csv = os.path.join(rdir, 'skeleton-annotations.csv')
    cols = FIELDS + ['category', 'date', 'chars', 'n_h3', 'n_img', 'n_math', 'n_pros', 'h2_seq']
    with open(out_csv, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for d in merged:
            w.writerow(d)

    print('merged %d notes (L0 has %d) -> %s' % (len(merged), len(l0), out_csv))
    if unresolved:
        print('!! 无法匹配文件名: %s' % ', '.join(unresolved))
    missing = set(l0) - seen
    if missing:
        print('!! 未标注 (%d): %s' % (len(missing), ', '.join(sorted(missing))))

    def dist(key, top=None):
        c = Counter(d[key] or '(空)' for d in merged)
        items = c.most_common(top) if top else c.most_common()
        return ', '.join('%s %d(%.0f%%)' % (k, v, 100.0 * v / len(merged)) for k, v in items)

    print('\n=== 骨架变体 ===\n' + dist('skeleton_variant'))
    print('\n=== H3 划分逻辑 ===\n' + dist('h3_logic'))
    print('\n=== 动机局限组织法 ===\n' + dist('motivation_pattern'))
    print('\n=== 贡献段形式 ===\n' + dist('contribution_form'))
    print('\n=== 公式三段式 ===\n' + dist('formula_style'))
    print('\n=== 可迁移到视觉检测 ===')
    c = Counter('Y' if (d['transferable'] or '').startswith('Y') else
                ('N' if (d['transferable'] or '').startswith('N') else '?') for d in merged)
    print(', '.join('%s %d(%.0f%%)' % (k, v, 100.0 * v / len(merged)) for k, v in c.most_common()))

    print('\n=== 优点主题标签频次 ===')
    tc = Counter()
    for d in merged:
        for t in re.split(r'[/+＋、,，\s]+', d['pros_themes'] or ''):
            t = t.strip()
            if t and t != '(空)':
                tc[t] += 1
    for t, v in tc.most_common(14):
        print('  %-10s %3d' % (t, v))

    print('\n=== 变体 x 篇幅 ===')
    byv = defaultdict(list)
    for d in merged:
        byv[d['skeleton_variant']].append(d)
    for v in sorted(byv, key=lambda x: -len(byv[x])):
        rs = byv[v]
        print('  %-12s n=%2d  字数中位 %5d  H3 %.1f  图 %.1f  公式 %.1f' % (
            v, len(rs), sorted(x['chars'] for x in rs)[len(rs) // 2],
            sum(x['n_h3'] for x in rs) / len(rs),
            sum(x['n_img'] for x in rs) / len(rs),
            sum(x['n_math'] for x in rs) / len(rs)))

    print('\n=== 篇幅分档（供 SKILL.md 锚点）===')
    cs = sorted(d['chars'] for d in merged)
    n = len(cs)
    for p, lab in [(10, 'P10'), (25, 'P25'), (50, '中位'), (75, 'P75'), (90, 'P90')]:
        print('  %-5s %6d 字' % (lab, cs[int(n * p / 100)]))
    print('  均值 %d 字' % (sum(cs) / n))

    print('\n=== 优点条目数分布 ===')
    pc = Counter(d['n_pros'] for d in merged)
    for k in sorted(pc):
        print('  %d 条: %2d 篇' % (k, pc[k]))


if __name__ == '__main__':
    main()
