#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
corpus_scan.py —— lzk 论文笔记语料 L0 机械预抽取

对 97 篇笔记做一次全量正则扫描，产出 per-note-index.jsonl。
这些字段 100% 可正则命中，不该消耗模型 token；语义层判断交给 Phase 2 的子代理。

用法:
    python corpus_scan.py <语料根目录> [输出 jsonl 路径]
"""
import json
import os
import re
import sys

# 图片引用行（无信息量，统计时保留计数，但不计入正文字数）
RE_IMG = re.compile(r'^!\[[^\]]*\]\([^)]*\)\s*$')
# Markdown 图片（任意位置）
RE_IMG_ANY = re.compile(r'!\[[^\]]*\]\([^)]*\)')
# LaTeX 行内 / 行间公式
RE_INLINE_MATH = re.compile(r'(?<!\$)\$(?!\$)([^$\n]+?)(?<!\$)\$(?!\$)')
RE_DISPLAY_MATH = re.compile(r'\$\$(.+?)\$\$', re.S)
# 表格行（以 | 开头结尾）
RE_TABLE_ROW = re.compile(r'^\s*\|.*\|\s*$')
# 标题
RE_H2 = re.compile(r'^##\s+(.+?)\s*$')
RE_H3 = re.compile(r'^###\s+(.+?)\s*$')
# frontmatter
RE_FM = re.compile(r'\A---\s*\n(.*?)\n---\s*\n', re.S)

# 图注衔接词（频次见全量统计）
GLUE_WORDS = ['如下表所示', '如下公式', '如下图所示', '下图展示了', '定义如下',
              '如上图所示', '如下表', '可见', '结果表明', '说明', '证明了', '可以看出']
# 论文概况表行标签
META_LABELS = ['标题', '作者', '发表期刊', '发表会议', '期刊等级', '会议等级',
               '发表年份', '会议年份', '论文代码', '论文影响', '作者单位', '原文链接']

DISCLAIMER = 'Paper Reading 是从个人角度进行的一些总结分享'


def split_sections(body_lines):
    """按 H2 切分正文，返回 [(h2标题, [行...]), ...]，H2 之前的归为 '_前言'。"""
    sections, cur, buf = [], '_前言', []
    for line in body_lines:
        m = RE_H2.match(line)
        if m:
            sections.append((cur, buf))
            cur, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    sections.append((cur, buf))
    return sections


def count_chinese_chars(text):
    """中文字符数 + 英文单词数，作为「正文字数」的近似。"""
    cn = len(re.findall(r'[\u4e00-\u9fff]', text))
    en = len(re.findall(r'[A-Za-z][A-Za-z0-9\-]*', text))
    return cn + en


def extract_meta_table(lines):
    """抽取开头的「| 论文概况 | 详细 |」表格，返回行标签列表。"""
    labels = []
    in_table = False
    for line in lines[:60]:
        if '|' not in line:
            if in_table and labels:
                break
            continue
        if '论文概况' in line:
            in_table = True
            continue
        if in_table:
            if re.match(r'^\s*\|[\s\-:|]+\|\s*$', line):  # 分隔行
                continue
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if cells and cells[0]:
                labels.append(cells[0])
    return labels


def extract_pros_items(lines):
    """抽取「优点和创新点」节的有序列表条目。"""
    items, in_pros = [], False
    for line in lines:
        if RE_H2.match(line) and '优点' in line:
            in_pros = True
            continue
        if in_pros and RE_H2.match(line):
            break
        if in_pros:
            m = re.match(r'^\s*\d+\.\s+(.+?)\s*$', line)
            if m:
                items.append(m.group(1).strip())
    return items


def first_sentence(lines):
    for line in lines:
        s = line.strip()
        if s and not s.startswith('|') and not s.startswith('!') and not s.startswith('#'):
            return s[:120]
    return ''


def scan_one(path, category):
    with open(path, 'r', encoding='utf-8') as f:
        raw = f.read()

    fm = {}
    m = RE_FM.match(raw)
    if m:
        for line in m.group(1).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip().strip('"').strip("'")
    body = raw[m.end():] if m else raw
    lines = body.splitlines()

    sections = split_sections(lines)
    h2_seq = [t for t, _ in sections if t != '_前言']

    text_wo_img = '\n'.join(l for l in lines if not RE_IMG.match(l))
    full_text = '\n'.join(lines)

    sec_map = {t: ls for t, ls in sections}
    pros_items = extract_pros_items(lines)
    meta_labels = extract_meta_table(lines)

    glue = {w: full_text.count(w) for w in GLUE_WORDS}
    has_disclaimer = DISCLAIMER in raw

    # 作者单位：概况表后的编号列表
    aff = 0
    for i, line in enumerate(lines[:80]):
        if re.match(r'^\s*作者单位\s*[:：]?\s*$', line):
            for l2 in lines[i + 1:i + 15]:
                if re.match(r'^\s*\d+\.\s+\S', l2):
                    aff += 1
                elif aff:
                    break
            break

    return {
        'file': os.path.basename(path),
        'path': path.replace('\\', '/'),
        'category': category,
        'fm_title': fm.get('title', ''),
        'fm_category': fm.get('category', ''),
        'fm_date': fm.get('date', ''),
        'fm_source_url': fm.get('source_url', ''),
        'h2_seq': h2_seq,
        'h3_titles': [RE_H3.match(l).group(1).strip() for l in lines if RE_H3.match(l)],
        'n_h3': sum(1 for l in lines if RE_H3.match(l)),
        'chars': count_chinese_chars(text_wo_img),
        'n_table_rows': sum(1 for l in lines if RE_TABLE_ROW.match(l)),
        'n_img': len(RE_IMG_ANY.findall(full_text)),
        'n_inline_math': len(RE_INLINE_MATH.findall(full_text)),
        'n_display_math': len(RE_DISPLAY_MATH.findall(full_text)),
        'meta_labels': meta_labels,
        'meta_venue': '会议' if '发表会议' in meta_labels else ('期刊' if '发表期刊' in meta_labels else '无'),
        'n_affiliation': aff,
        'has_disclaimer': has_disclaimer,
        'n_pros_items': len(pros_items),
        'pros_items': pros_items,
        'glue': glue,
        'n_qizhong': full_text.count('其中'),
        'motivation_first': first_sentence(sec_map.get('研究动机', [])),
        'contribution_first': first_sentence(sec_map.get('文章贡献', [])),
        'method_first': first_sentence(sec_map.get('本文方法', [])),
        'exper_first': first_sentence(sec_map.get('实验结果', sec_map.get('实验分析', []))),
    }


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else r'D:/Data/LQS_Skill/lzk_paper_reading'
    out = sys.argv[2] if len(sys.argv) > 2 else None
    if out is None:
        out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           'references', 'research', 'per-note-index.jsonl')

    skip_dirs = {'.git', '.workbuddy', '.cache', 'assets', 'scripts',
                 'references', '__pycache__'}
    records = []
    for entry in sorted(os.listdir(root)):
        d = os.path.join(root, entry)
        if not os.path.isdir(d) or entry in skip_dirs or entry.startswith('.'):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith('.md'):
                continue
            records.append(scan_one(os.path.join(d, fn), entry))

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    # 控制台摘要
    print('scanned: %d notes -> %s' % (len(records), out))
    from collections import Counter, defaultdict
    h2c = Counter(h for r in records for h in r['h2_seq'])
    print('\n[H2 频次 top12]')
    for h, c in h2c.most_common(12):
        print('  %-16s %3d  (%.1f%%)' % (h, c, 100.0 * c / len(records)))

    std = ['研究动机', '文章贡献', '本文方法', '实验结果', '优点和创新点']
    strict = sum(1 for r in records if r['h2_seq'] == std)
    flexible = sum(1 for r in records
                   if [h for h in r['h2_seq'] if h != '预备知识'] == std)
    print('\n严格标准骨架: %d/%d (%.1f%%)' % (strict, len(records), 100.0 * strict / len(records)))
    print('允许插入「预备知识」: %d/%d (%.1f%%)' % (flexible, len(records), 100.0 * flexible / len(records)))

    chars = sorted(r['chars'] for r in records)
    print('\n正文中位数: %d  (min %d / max %d)' % (chars[len(chars) // 2], chars[0], chars[-1]))

    bycat = defaultdict(list)
    for r in records:
        bycat[r['category']].append(r)
    print('\n[分类]  篇数  字数中位  H3  图  公式')
    for c in sorted(bycat, key=lambda x: -len(bycat[x])):
        rs = bycat[c]
        cs = sorted(x['chars'] for x in rs)
        print('  %-8s %3d  %6d  %4.1f  %4.1f  %5.1f' % (
            c, len(rs), cs[len(cs) // 2],
            sum(x['n_h3'] for x in rs) / len(rs),
            sum(x['n_img'] for x in rs) / len(rs),
            sum(x['n_inline_math'] + x['n_display_math'] for x in rs) / len(rs)))


if __name__ == '__main__':
    main()
