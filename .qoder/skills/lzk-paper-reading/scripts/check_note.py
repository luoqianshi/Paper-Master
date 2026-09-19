#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
check_note.py —— lzk-paper-reading 笔记验收门禁

把 §5 表达 DNA 与 §6 自检清单里的主观规范，变成可机器判定的硬门槛。

用法:
    python check_note.py <笔记.md> [--tier 短|标准|长]
退出码: 有 FAIL 为 1，仅 WARN 为 0。
"""
import argparse
import os
import re
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

DISCLAIMER = ('Paper Reading 是从个人角度进行的一些总结分享，受到个人关注点的侧重和实力所限，'
              '可能有理解不到位的地方。具体的细节还需要以原文的内容为准，博客中的图表若未另外说明则均来自原文。')
PROS_OPENING = '个人认为，本文有如下一些优点和创新点可供参考学习：'
BANNED = {'值得注意的是': '过渡腔，语料仅 2 次',
          '需要说明的是': '过渡腔，语料 0 次',
          '值得学习': '语料 0 次，正确说法是「可供参考学习」'}
# 领域术语：用于检测表格 ML 与视觉检测之间的术语串味
TABULAR_WORDS = ['SMOTE', '不平衡比', '过采样', '欠采样', '重采样', '少数类', '多数类',
                 '基分类器', 'UCI', '交叉验证', '特征选择', '基尼', '信息增益']
VISION_WORDS = ['mAP', 'AP50', 'AP_S', 'AP_M', 'AP_L', 'AP75', '检测框', 'anchor', 'Anchor',
                'NMS', 'IoU', 'FPS', '骨干', 'backbone', 'neck', '参数量', 'GFLOPs',
                '小目标', '目标检测', '推理延迟', '航拍', '遥感']
TIERS = {'短': (2000, 3000), '标准': (3200, 4800), '长': (5200, 7800)}

results = []


def add(level, name, msg):
    results.append((level, name, msg))


def strip_code(text):
    """剥离代码块、公式、链接、图片路径与 HTML 标签，避免误判中英文空格。

    HTML 标签必须剥离：语料里大量使用 `R<sup>{k×n}</sup>` 这类写法，
    标签与内容之间本就不该有空格。
    """
    t = re.sub(r'\$\$.*?\$\$', ' ', text, flags=re.S)
    t = re.sub(r'`[^`]*`', ' ', t)
    t = re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', t)
    t = re.sub(r'\[[^\]]*\]\([^)]*\)', ' ', t)
    t = re.sub(r'(?<!\$)\$(?!\$)[^$\n]*?\$', ' ', t)
    t = re.sub(r'https?://\S+', ' ', t)
    t = re.sub(r'<[^>]+>', ' ', t)
    return t


def count_chars(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text)) + len(re.findall(r'[A-Za-z][A-Za-z0-9\-]*', text))


def sections(body):
    out, cur, buf = [], '_前言', []
    for line in body.splitlines():
        m = re.match(r'^##\s+(.+?)\s*$', line)
        if m:
            out.append((cur, buf))
            cur, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    out.append((cur, buf))
    return out


def main():
    ap = argparse.ArgumentParser(description='lzk-paper-reading 笔记门禁校验')
    ap.add_argument('file')
    ap.add_argument('--tier', default='标准', choices=list(TIERS))
    ap.add_argument('--variant', default='auto', choices=['auto', '标准', 'survey'],
                    help='骨架变体；auto 会按 H2 序列自动识别 survey')
    a = ap.parse_args()

    if not os.path.exists(a.file):
        print('文件不存在: %s' % a.file)
        sys.exit(1)
    raw = open(a.file, 'r', encoding='utf-8').read()

    # ---------- A. 固定件 ----------
    fm = re.match(r'\A---\s*\n(.*?)\n---\s*\n', raw, re.S)
    if not fm:
        add('FAIL', 'frontmatter', '缺失 --- 包围的 frontmatter')
    else:
        keys = [l.split(':', 1)[0].strip() for l in fm.group(1).splitlines() if ':' in l]
        miss = [k for k in ('title', 'category', 'date', 'source_url') if k not in keys]
        add('PASS' if not miss else 'FAIL', 'frontmatter 四字段',
            '齐全' if not miss else '缺少: %s' % ', '.join(miss))

    body = raw[fm.end():] if fm else raw

    if DISCLAIMER in raw:
        add('PASS', '免责声明', '一字不差')
    else:
        add('FAIL', '免责声明', '未找到或已被改动，必须原样保留')

    if '| 论文概况 | 详细 |' in raw:
        add('PASS', '论文概况表头', '正确')
        head = raw[:raw.find('| 论文概况 | 详细 |') + 400]
        has_j, has_c = '发表期刊' in head, '发表会议' in head
        if has_j and has_c:
            add('FAIL', '期刊/会议互斥', '两者同时出现，应二选一')
        elif has_j or has_c:
            add('PASS', '期刊/会议互斥', '期刊' if has_j else '会议')
        else:
            add('FAIL', '期刊/会议互斥', '两者皆无')
    else:
        add('FAIL', '论文概况表头', '未找到 `| 论文概况 | 详细 |`')

    # ---------- B. 骨架 ----------
    secs = sections(body)
    names = [n for n, _ in secs if n != '_前言']

    # survey 骨架没有「研究动机/文章贡献/优点和创新点」，按语料实证改用另一套判据
    is_survey = a.variant == 'survey' or (
        a.variant == 'auto' and any(k in n for n in names for k in ('本文目标和贡献', '分析与展望')))

    if is_survey:
        add('INFO', '骨架模式', 'survey（已切换到 survey 判据）')
        add('PASS' if len(names) >= 4 else 'FAIL', 'survey·分类体系',
            '%d 节分类体系：%s' % (len(names), ' > '.join(names)))
        if not any('问题' in n for n in names[:1]):
            add('WARN', 'survey·首节', '首节应为领域问题定义，实际「%s」' % names[0])
        else:
            add('PASS', 'survey·首节', '领域问题定义')
        add('PASS' if any('目标和贡献' in n for n in names) else 'FAIL',
            'survey·研究问题', '含「本文目标和贡献」节' if any('目标和贡献' in n for n in names)
            else '缺「本文目标和贡献」节（survey 必须在此列 N 个裸数字编号的研究问题）')
        add('PASS' if any('展望' in n or '总结' in n for n in names) else 'WARN',
            'survey·收尾', '含分析与展望/经验总结' if any('展望' in n or '总结' in n for n in names)
            else '建议以「分析与展望」或「经验总结」收尾')
    else:
        for req in ('研究动机', '文章贡献'):
            add('PASS' if req in names[:2] else 'FAIL', '骨架·%s' % req,
                '位置正确' if req in names[:2] else '%s 必须在前两节，实际: %s' % (req, ' > '.join(names[:3])))
        if '优点和创新点' in names:
            add('PASS' if names[-1] == '优点和创新点' else 'FAIL', '骨架·优点和创新点',
                '末节' if names[-1] == '优点和创新点' else '必须是末节，实际末节是「%s」' % names[-1])
        else:
            add('WARN', '骨架·优点和创新点', '缺失（仅 survey 与短文可省略）')
    add('INFO', 'H2 序列', ' > '.join(names))

    smap = {n: '\n'.join(l) for n, l in secs}

    # ---------- C. 节内形态 ----------
    mot = smap.get('研究动机', '')
    mot_first = next((l.strip() for l in mot.splitlines()
                      if l.strip() and not l.strip().startswith(('|', '!', '#', '-'))), '')
    if mot:
        add('PASS' if mot_first and '？' not in mot_first and '?' not in mot_first else 'FAIL',
            '动机节首句', '非疑问句：%s……' % (mot_first[:36] if mot_first else '（未取到首句）'))
        if re.search(r'但是|然而|但 |却', mot):
            add('PASS', '动机节转折', '已切入局限')
        else:
            add('WARN', '动机节转折', '未检测到「但是/然而」转折')

    con = smap.get('文章贡献', '')
    if con:
        n_para = len([l for l in con.splitlines() if l.strip() and not l.strip().startswith(('#', '|', '!'))])
        n_item = len(re.findall(r'^\s*\d+\.\s+\S', con, re.M))
        if n_item:
            add('FAIL', '贡献节形式', '检测到 %d 个分点，贡献节必须是一整段散文（语料 96%）' % n_item)
        else:
            add('PASS', '贡献节形式', '散文整段（%d 行）' % n_para)

    meth_secs = [n for n in names if n in ('本文方法',) or '方法' in n or '算法' in n]
    meth = '\n'.join(smap.get(n, '') for n in meth_secs)
    n_h3 = len(re.findall(r'^###\s+', meth, re.M))
    if meth:
        add('PASS' if n_h3 >= 3 else 'WARN', '方法节 H3', '%d 个（建议 6-12）' % n_h3)

    # 公式三段式：只对独立公式块（$$...$$）检测铺垫句
    # 行内公式天然嵌在中文语境里，不参与判定，否则会大量误报。
    n_math = len(re.findall(r'(?<!\$)\$(?!\$)[^$\n]+?\$', raw))
    block_starts = [m.start() for m in re.finditer(r'\$\$(?!\$)', raw)][::2]
    n_block = len(block_starts)
    no_setup = []
    for p in block_starts:
        before = re.sub(r'\s+', '', raw[max(0, p - 150):p])
        if not (before.endswith(('：', ':', '。', '，')) or
                re.search(r'(如下|定义|表示|计算|更新|形式化|目标|损失)', before)):
            no_setup.append(p)
    if n_block == 0 and n_math == 0:
        add('WARN', '公式三段式', '全篇无公式（语料 18% 无公式，若论文确实有公式则不妥）')
    elif n_block == 0:
        add('PASS', '公式三段式', '仅 %d 处行内公式，无独立公式块' % n_math)
    else:
        add('PASS' if len(no_setup) <= n_block * 0.3 else 'WARN', '公式三段式',
            '%d 个独立公式块 + %d 处行内公式，%d 块缺铺垫句' % (n_block, n_math, len(no_setup)))
        if no_setup:
            add('INFO', '公式·缺铺垫位置', '字符偏移 %s（前 150 字内未见引导句）'
                % ', '.join(str(x) for x in no_setup[:5]))
    add('PASS' if '其中' in raw else 'WARN', '公式·「其中」解释',
        '出现 %d 次（语料最高频衔接词）' % raw.count('其中'))

    # 裸图
    lines = body.splitlines()
    bare = 0
    for i, l in enumerate(lines):
        if re.match(r'^!\[', l.strip()):
            after = [x.strip() for x in lines[i + 1:i + 4] if x.strip()]
            if not any(re.search(r'[\u4e00-\u9fff]', x) and not x.startswith('!') for x in after):
                bare += 1
    n_img = len(re.findall(r'!\[', body))
    add('PASS' if bare == 0 else 'FAIL', '无裸图',
        '%d 张图，%d 张后无解读文字' % (n_img, bare))

    # 优点节
    pros = smap.get('优点和创新点', '')
    if pros:
        if PROS_OPENING in pros:
            add('PASS', '优点节起手句', '一字不差')
        else:
            add('FAIL', '优点节起手句', '必须原样写「%s」' % PROS_OPENING)
        items = re.findall(r'^\s*\d+\.\s+(.+?)\s*$', pros, re.M)
        add('PASS' if 2 <= len(items) <= 4 else 'WARN', '优点节条数',
            '%d 条（3 条为主，占 57%%）' % len(items))
        lens = [len(x) for x in items]
        if lens:
            add('PASS' if all(30 <= x <= 120 for x in lens) else 'WARN', '优点条目长度',
                '%s 字（建议 40-90，语料中位 58）' % '/'.join(str(x) for x in lens))
        neg = [w for w in ('不足', '缺陷', '缺点', '未能', '局限') if w in pros]
        add('PASS' if not neg else 'WARN', '优点节零负面',
            '无负面词' if not neg else '检测到: %s（语料 255 条零负面）' % ', '.join(neg))

    # ---------- D. 表达 DNA ----------
    clean = strip_code(body)
    gaps = []
    # 「2022年12月」这类时间写法里，中文单位后紧跟数字是标准写法，同样剔除。
    for m in re.finditer(r'(?<=[\u4e00-\u9fff])(?=[A-Za-z0-9])', clean):
        # 匹配位置落在「中文|数字」之间，故向前取一个字符判断是不是时间单位
        if re.match(r'(年|月|日|号|时|分|秒)', clean[m.start() - 1:m.start()]):
            continue
        gaps.append((m.start(), '中→英'))
    # 数字后紧跟中文量词是标准写法，不该加空格（如「2022年」「3 倍」里的倍、
    # 「第 2 层」里的层）。按惯例这些位置不加空格，故从违规里剔除。
    for m in re.finditer(r'(?<=[A-Za-z0-9])(?=[\u4e00-\u9fff])', clean):
        if re.match(r'(年|月|日|号|时|分|秒|代|版|期|级|层|类|种|倍|成|折|维|度|元|万|亿|余|多)',
                    clean[m.start():m.start() + 1]):
            continue
        gaps.append((m.start(), '英→中'))
    if gaps:
        ctx = '；'.join('%s「%s」' % (d, clean[max(0, p - 6):p + 8].replace('\n', ' '))
                        for p, d in gaps[:5])
        add('FAIL', '中英文空格', '%d 处缺空格：%s' % (len(gaps), ctx))
    else:
        add('PASS', '中英文空格', '合规（语料 98.0%）')

    # 领域一致性：表格 ML 术语与视觉检测术语不应混用。
    # 语料 100% 是表格 ML，但使用者本行是视觉检测，术语串味是最典型的泛化失败。
    tab_hits = [w for w in TABULAR_WORDS if w in raw]
    vis_hits = [w for w in VISION_WORDS if w in raw]
    if len(vis_hits) >= 3 and tab_hits:
        add('WARN', '领域术语一致性',
            '视觉笔记混入 %d 个表格 ML 词：%s' % (len(tab_hits), '、'.join(tab_hits[:6])))
    elif len(vis_hits) >= 3:
        has_vis_h3 = bool(re.search(r'^#{3,4}\s+.*(可视化|效果图|定性|案例)', body, re.M))
        add('PASS' if has_vis_h3 else 'WARN', '领域术语一致性',
            '视觉类笔记（命中 %d 个视觉词）' % len(vis_hits) +
            ('，已含可视化/定性分析子节' if has_vis_h3 else '，建议补「可视化分析」H3'))
    elif tab_hits:
        add('INFO', '领域术语一致性', '表格 ML 类笔记（命中 %d 个词）' % len(tab_hits))

    hits = [(w, raw.count(w), why) for w, why in BANNED.items() if w in raw]
    add('PASS' if not hits else 'FAIL', '禁用词',
        '0 命中' if not hits else '；'.join('%s×%d（%s）' % h for h in hits))

    n_ben = raw.count('本文')
    add('INFO', '主语习惯', '本文 %d 次 / 作者 %d 次 / 论文 %d 次'
        % (n_ben, raw.count('作者'), raw.count('论文')))
    if n_ben < 3:
        add('WARN', '主语习惯', '「本文」仅 %d 次，语料篇均 9.5 次' % n_ben)

    # ---------- E. 篇幅 ----------
    n_chars = count_chars(strip_code(body))
    lo, hi = TIERS[a.tier]
    add('PASS' if lo <= n_chars <= hi else 'WARN', '篇幅（%s档）' % a.tier,
        '%d 字（区间 %d-%d，语料中位 3770）' % (n_chars, lo, hi))
    add('INFO', '素材密度', 'H3 %d / 图 %d / 表 %d / 公式 %d'
        % (len(re.findall(r'^###\s+', body, re.M)), n_img,
           len(re.findall(r'^\s*\|.*\|\s*$', body, re.M)), n_math))

    # ---------- 输出 ----------
    order = {'FAIL': 0, 'WARN': 1, 'PASS': 2, 'INFO': 3}
    icon = {'PASS': '[PASS]', 'WARN': '[WARN]', 'FAIL': '[FAIL]', 'INFO': '[INFO]'}
    results.sort(key=lambda r: (order[r[0]], r[1]))
    print('=' * 62)
    print('lzk-paper-reading 门禁报告: %s' % os.path.basename(a.file))
    print('=' * 62)
    for lv, name, msg in results:
        print('%-7s %-18s %s' % (icon[lv], name, msg))
    n_fail = sum(1 for r in results if r[0] == 'FAIL')
    n_warn = sum(1 for r in results if r[0] == 'WARN')
    print('-' * 62)
    print('FAIL %d / WARN %d' % (n_fail, n_warn))
    if n_fail:
        print('未通过：必须修掉全部 FAIL 项后再交付。')
    elif n_warn:
        print('通过（有 %d 项建议改进）。' % n_warn)
    else:
        print('全部通过。')
    sys.exit(1 if n_fail else 0)


if __name__ == '__main__':
    main()
