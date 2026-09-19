#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
new_note.py —— 按 lzk-paper-reading 范式生成一篇笔记的骨架

免责声明与论文概况表头是语料中 97/97 一字不差的固定件，也是最容易被写错的地方，
因此由脚本模板化，杜绝手写偏差。

用法:
    python new_note.py <输出路径.md> --title "论文英文标题" --category 分类
                       [--date 2026-08-30] [--url https://...] [--variant 标准|预备知识|survey|方法名]
                       [--venue 会议|期刊]

示例:
    python new_note.py ./yolov12-note.md --title "YOLOv12: Attention-Centric Real-Time Object Detectors" \
        --category 目标检测 --variant 预备知识
"""
import argparse
import os
import sys
from datetime import date

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

DISCLAIMER = ('Paper Reading 是从个人角度进行的一些总结分享，受到个人关注点的侧重和实力所限，'
              '可能有理解不到位的地方。具体的细节还需要以原文的内容为准，博客中的图表若未另外说明则均来自原文。')

PROS_OPENING = '个人认为，本文有如下一些优点和创新点可供参考学习：'

# 骨架变体 → H2 序列
VARIANTS = {
    '标准':     ['研究动机', '文章贡献', '本文方法', '实验结果', '优点和创新点'],
    '预备知识': ['研究动机', '文章贡献', '预备知识', '本文方法', '实验结果', '优点和创新点'],
    '方法名':   ['研究动机', '文章贡献', '<论文方法名>', '实验结果', '优点和创新点'],
    'survey':   ['<领域>问题', '本文目标和贡献', '基本概念和分类方法', '<逐类综述>', '实验研究'],
}

# 每节的写作提示（写进骨架，写作时替换为正文）
HINTS = {
    '研究动机': '【250-450 字，不设 H3】定义式起手（首句不带问号）→「但是/然而」转折 → '
                '局限用综述式铺陈逐层收窄（语料 67%）→ 收尾指认空白。不写本文方案、不出现公式。',
    '文章贡献': '【200-350 字，一整段散文，禁止分点】'
                '「针对<局限>，本文提出了<模型名>。其核心是……。首先……接着……最终……。实验表明……」',
    '预备知识': '【占全文 5%-17%，2-3 个 H3，必须配表】写清 A、B 两套体系的形式化定义，'
                '为方法节做符号与概念铺垫。',
    '本文方法': '【1500-2500 字，H3 6-12 个】先定 H3 划分逻辑（按模块 / 按流程步骤 / '
                '按定义-结构-变体，全篇只用一种）。每节：一句话定性 → 公式或图 → 2-4 句解释 → 与前后模块的关系。',
    '实验结果': '【600-1200 字】2-3 句文字 + 1 张图。骨架：设置表 → 主对比 → 消融 → 效率 → '
                '可解释性可视化。数值只点缀结论句，结果表用图片。',
    '优点和创新点': PROS_OPENING + '\n\n【2-4 条有序列表，3 条为主（57%），每条 40-90 字】'
                                   '动词或介词开头，结构为「做了什么 + 手段 + 达到的效果」。零负面。',
    '<论文方法名>': '【替换为论文的方法名】',
    '<领域>问题': '【survey】先讲清楚这个领域的问题是什么，以及为什么需要一篇综述。',
    '本文目标和贡献': '【survey】列 N 个裸数字编号的完整疑问句（不用 RQ 前缀），构成全文的研究问题。',
    '基本概念和分类方法': '【survey】建立分类体系（靠标题层级承载：H2 大类 → H3 二级 → 正文编号三级）。',
    '<逐类综述>': '【survey】每类：定义句 + 代表工作（加粗名 + 一句机制）+「该方法的优势是……局限在于……」+ 类末 H3「小结」。',
    '实验研究': '【survey】末 H3「经验总结」逐条回答前面的研究问题，严格一一对应；证据不足时答「影响尚不清楚」。',
}


def build(title, category, dt, url, variant, venue):
    h2s = VARIANTS[variant]
    lines = [
        '---',
        'title: "%s"' % title,
        'category: %s' % category,
        'date: %s' % dt,
        'source_url: %s' % url,
        '---',
        '',
        '# %s' % title,
        '',
        DISCLAIMER,
        '',
        '| 论文概况 | 详细 |',
        '| --- | --- |',
        '| 标题 | 《%s》 |' % title,
        '| 作者 | 未获取 |',
    ]
    if venue == '期刊':
        lines += ['| 发表期刊 | 未获取 |', '| 期刊等级 | 未获取 |']
    else:
        lines += ['| 发表会议 | 未获取 |', '| 会议等级 | 未获取 |']
    lines += [
        '| 发表年份 | 未获取 |',
        '| 论文代码 | 未获取 |',
        '',
        '作者单位：',
        '',
        '1. 未获取',
        '',
    ]
    for h in h2s:
        lines += ['## %s' % h, '', HINTS.get(h, ''), '']
    if variant == 'survey':
        lines += ['## 分析与展望', '', '【survey 收尾】立评估标准 → 重映射范式 → 逐项给局限与未来方向 → '
                                        '末段「N 个最具潜力的发展方向」。', '']
    return '\n'.join(lines) + '\n'


def main():
    ap = argparse.ArgumentParser(description='生成 lzk-paper-reading 笔记骨架')
    ap.add_argument('output', help='输出 .md 路径')
    ap.add_argument('--title', required=True, help='论文标题')
    ap.add_argument('--category', default='未分类', help='分类')
    ap.add_argument('--date', default=str(date.today()), help='日期 YYYY-MM-DD')
    ap.add_argument('--url', default='', help='原文链接')
    ap.add_argument('--variant', default='标准',
                    choices=list(VARIANTS), help='骨架变体')
    ap.add_argument('--venue', default='会议', choices=['会议', '期刊'], help='发表载体')
    a = ap.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    with open(a.output, 'w', encoding='utf-8') as f:
        f.write(build(a.title, a.category, a.date, a.url, a.variant, a.venue))

    print('已生成骨架: %s' % a.output)
    print('  变体: %s  →  %s' % (a.variant, ' → '.join(VARIANTS[a.variant])))
    print('  下一步: 按骨架内的【】提示逐节填写，完成后跑 check_note.py 验收。')


if __name__ == '__main__':
    main()
