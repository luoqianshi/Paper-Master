# Paper-Master

🌐 [中文](#) · [English](README.en.md)

> **「一篇 PDF 进,两份沉淀出:中文阅读笔记 + 可放映的 HTML PPT。」**
> *嵌入各类 AI 编程工具 / AI 办公工具的科研人 AI 原生论文知识库:喂给 AI 一篇论文,它同时替你写好博客笔记、做组会 PPT,并把知识长期攒成个人知识库。*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Pages](https://img.shields.io/badge/Demo-GitHub%20Pages-success)](https://luoqianshi.github.io/Paper-Master/)
[![Skills](https://img.shields.io/badge/Agent%20Skills-3-purple)](#-能力矩阵)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#-贡献)
[![Made with HTML](https://img.shields.io/badge/Made%20with-HTML5%20%2B%20Vanilla%20JS-orange)]()
---

## 致谢

- [html-presentation](https://github.com/juanjuanjie/html-presentation) —— 原始 HTML 幻灯片模板与播放引擎参考仓库
- [博客园「乌漆WhiteMoon」Paper Reading 专栏](https://www.cnblogs.com/linfangnan/p/17636482.html) —— `lzk-paper-reading` 笔记范式的蒸馏来源
- [Claude Code](https://claude.com/claude-code) · [TRAE](https://www.trae.cn/) · [CodeBuddy](https://www.codebuddy.cn/) —— AI Agent 平台
- 所有开源论文作者与开源社区

---

## 30 秒看懂

`Paper-Master` 是面向科研人的 **AI 原生论文知识库**,可嵌入 Claude Code / TRAE / CodeBuddy 等各类 AI 编程工具与 AI 办公工具:把「读一篇论文」这件事沉淀成两种可长期复用的产物——一篇结构化的**中文阅读笔记(博客)**,和一份能直接放映的**单文件 HTML PPT**。整个流程由 AI Agent 通过 3 个 SKILL 自动完成:你把 PDF 丢进 `pdf-papers/`,它替你写好笔记、做好 PPT——PPT 既可直接从 PDF 生成,也能用写好的阅读笔记一键转化——并把它们归档进一个可版本管理、可一键部署到 GitHub Pages 的电子书柜里。

- 想把论文读透、沉淀成博客笔记 → 用 `lzk-paper-reading`
- 手头有 PDF,想直接做成组会 / 答辩汇报 PPT → 用 `html-paper-slides`
- 已有阅读笔记,想把笔记快速转成汇报 PPT → 用 `blog-to-slides`

**和普通 PPT 工具的本质差异**:这里交付的不是"一次性幻灯片",而是**知识库里的两个可检索资产**——Markdown 笔记(可 diff、可全文搜索、可再加工)+ 离线单文件 HTML PPT(可 `file://` 放映、可嵌入个人主页)。读过的每一篇,都会在这个书柜里越攒越厚。

---

## 立即试用

```bash
git clone https://github.com/luoqianshi/Paper-Master.git
cd Paper-Master
```

用 Claude Code / TRAE / CodeBuddy 等任意支持 Skills 的 AI 编程工具 / AI 办公工具打开,然后把下面任意一句发给 Agent:

**产出中文阅读笔记:**

```markdown
请你使用 lzk-paper-reading 技能(skills\lzk-paper-reading\SKILL.md),
帮我为 ./pdf-papers/my-paper.pdf 写一篇中文论文阅读笔记,
最终 .md 文件存放在 paper-blogs 目录下,
提取的论文配图按论文标题归档到 assets/paper-imgs 目录下。
```

**产出 HTML 汇报 PPT:**

```markdown
请你使用 html-paper-slides 技能(skills\html-paper-slides\SKILL.md),
帮我为 ./pdf-papers/my-paper.pdf 制作一份 HTML 格式的论文汇报 PPT,
最终文件存放在 paper-slides 目录下。
```

**已有阅读笔记,转成 HTML 汇报 PPT(无需 PDF):**

```markdown
请你使用 blog-to-slides 技能(.trae\skills\blog-to-slides\SKILL.md),
帮我为 paper-blogs/my-paper.md 这篇中文阅读笔记制作一份 HTML 格式的
论文汇报 PPT,最终文件存放在 paper-slides 目录下。
```

几分钟后,`paper-blogs/` 下会出现一篇结构化中文阅读笔记,或 `paper-slides/` 下会出现一份可浏览器放映的单文件 HTML 演示文稿,后者还会通过 `index.html` 自动收录进电子书柜画廊。

---

## 能力矩阵

仓库内置 3 个 SKILL,覆盖「读论文」最核心的沉淀方式:

| SKILL | 典型场景 | 输入 | 交付物 | 典型耗时 |
|------|----------|------|--------|----------|
| [`lzk-paper-reading`](skills/lzk-paper-reading/SKILL.md) | 论文精读 · 博客笔记 · 知识沉淀 | 一篇 PDF / arXiv 链接 / 标题 | 结构化中文 Markdown 笔记(`paper-blogs/`)+ 配图库(`assets/paper-imgs/`) | 5–12 min |
| [`html-paper-slides`](skills/html-paper-slides/SKILL.md) | 组会汇报 · 答辩演练 · 研究进展展示 | 一篇 PDF 论文 | 单文件 HTML deck + 首屏缩略图 | 8–15 min |
| [`blog-to-slides`](.trae/skills/blog-to-slides/SKILL.md) | 笔记转 PPT · 组会汇报快速成稿 | 一份已产出的中文阅读笔记(`paper-blogs/*.md`)+ 已提取配图 | 单文件 HTML deck + 首屏缩略图 | 5–10 min |

- **`lzk-paper-reading`** 按固定五节骨架(研究动机 / 文章贡献 / 本文方法 / 实验结果 / 优点和创新点)+ 论文概况表 + 免责声明产出中文笔记,强制执行公式"铺垫句→LaTeX→其中解释"三段式、"2-3 句 + 1 图"实验节奏,并用 `scripts/new_note.py` 起稿、`scripts/check_note.py` 门禁验收。
- **`html-paper-slides`** 生成苹果风 / Notion 风的单文件 HTML 演示文稿:无外部依赖、可直接 `open file://` 播放、键盘翻页、淡入动画、CSS Grid 响应式排版,适合 GitHub Pages / Vercel / Netlify 一键部署。
- **`blog-to-slides`** 以 `lzk-paper-reading` 产出的中文阅读笔记为**唯一信息源**,复用 `assets/paper-imgs/` 已提取配图,无需 PDF:把五节骨架笔记映射为「首页 → 概述 → 引言 → 方法 → 实验 → 总结与讨论」的单文件 HTML deck,公式用 HTML/CSS 排版、图片以相对路径直接引用(不复制图片),保持 `file://` 协议下零外部依赖。

> `lzk-paper-reading` 与 `html-paper-slides` 共享同一套"论文理解"能力:先用 `pdf_extractor.py` 从 PDF 提取透明背景原图,按论文标题统一归档到 `assets/paper-imgs/<论文标题>/`,再分别喂给笔记流与 PPT 流;`blog-to-slides` 则补上第三条路径——直接以上一条流产出的笔记与配图为输入,把已有笔记快速转成 PPT,全程无需再读 PDF。同一篇论文,可以一次生成"笔记 + PPT"两份资产。

---

## Showcase · 真实论文 PPT 演示

下面 8 份演示文稿均使用 `html-paper-slides` 在 AI Agent 协助下完成,可直接点击预览:

<table>
  <tr>
    <td align="center" width="50%">
      <a href="paper-slides/Attention_Is_All_You_Need.html">
        <img src="assets/thumbnails/Attention_Is_All_You_Need.png" alt="Attention Is All You Need" width="100%">
      </a>
      <br><b>Attention Is All You Need</b>
      <br><sub>Transformer 经典论文 · 多头自注意力 · 机器翻译 SOTA</sub>
    </td>
    <td align="center" width="50%">
      <a href="paper-slides/DETRs_Beat_YOLOs_on_Real-time_Object_Detection.html">
        <img src="assets/thumbnails/DETRs_Beat_YOLOs_on_Real-time_Object_Detection.png" alt="RT-DETR" width="100%">
      </a>
      <br><b>DETRs Beat YOLOs on Real-time Object Detection</b>
      <br><sub>CVPR 2024 Oral · RT-DETR · 端到端实时检测</sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="paper-slides/YOLO-Master_Presentation.html">
        <img src="assets/thumbnails/YOLO-Master_Presentation.png" alt="YOLO-Master" width="100%">
      </a>
      <br><b>YOLO-Master: MoE-Accelerated YOLO</b>
      <br><sub>专业化解码器 · MoE 加速 · 实时检测</sub>
    </td>
    <td align="center" width="50%">
      <a href="paper-slides/YOLOv12_Attention-Centric.html">
        <img src="assets/thumbnails/YOLOv12_Attention-Centric.png" alt="YOLOv12" width="100%">
      </a>
      <br><b>YOLOv12: Attention-Centric Real-Time Detectors</b>
      <br><sub>Area Attention · R-ELAN · 注意力中心化</sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="paper-slides/YOLO26_Unified_Real-Time_Vision.html">
        <img src="assets/thumbnails/YOLO26_Unified_Real-Time_Vision.png" alt="YOLO26" width="100%">
      </a>
      <br><b>Ultralytics YOLO26: Unified Real-Time Vision</b>
      <br><sub>DFL-free · MuSGD · 多任务统一</sub>
    </td>
    <td align="center" width="50%">
      <a href="paper-slides/smooth-tail_learning.html">
        <img src="assets/thumbnails/smooth-tail_learning.png" alt="smooth-tail" width="100%">
      </a>
      <br><b>Boosting Long-tailed Object Detection</b>
      <br><sub>ICCV 2023 · 平滑尾部 · 逐步学习</sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="paper-slides/Dialogue_Director.html">
        <img src="assets/thumbnails/Dialogue_Director.png" alt="Dialogue Director" width="100%">
      </a>
      <br><b>Dialogue Director</b>
      <br><sub>对话可视化 · 三智能体 · 电影知识整合</sub>
    </td>
    <td align="center" width="50%">
      <a href="paper-slides/DySample_Learning_to_Upsample.html">
        <img src="assets/thumbnails/DySample_Learning_to_Upsample.png" alt="DySample" width="100%">
      </a>
      <br><b>DySample: Learning to Upsample by Learning to Sample</b>
      <br><sub>动态上采样 · 内容感知 · 即插即用</sub>
    </td>
  </tr>
</table>

> 在线画廊:https://luoqianshi.github.io/Paper-Master/

---

## 核心工作流:pdf-papers → paper-blogs → paper-slides

本仓库的差异化在于把"论文精读"统一到一条**可复现、可版本化**的三段式流水线上,一篇论文可同时产出"笔记"与"PPT"两种资产:

```
┌────────────┐    ┌────────────┐    ┌──────────────────────────┐
│ pdf-papers │ →  │   paper-blogs   │ →  │      paper-slides        │
│ 原始论文库 │    │ 中文MD笔记 │    │  ┌────────────────────┐  │
└────────────┘    └────────────┘    │  │ 单文件 HTML PPT    │  │
  仅存原始 PDF      五节骨架笔记     │  └────────────────────┘  │
  命名可追踪        配图统一入库      └──────────────────────────┘
                    assets/paper-imgs/<论文标题>/
```

### 1. `pdf-papers/` —— 原始论文 PDF 归档
只保存 PDF 格式的原始论文,不再存放补充材料、网页链接、临时摘录等其他素材。不追求排版,只要求来源清晰、文件命名可追踪(建议直接以论文标题命名),方便后续流程按标题建立配图目录。

### 2. `paper-blogs/` —— 中文阅读笔记(MD 博客)
`lzk-paper-reading` 技能的产出层:每篇 PDF 论文对应一份结构化中文 Markdown 阅读笔记(博客),按固定五节骨架 + 论文概况表 + 免责声明组织,提炼"研究问题与动机、核心贡献、方法框架、关键模块、实验设置、核心指标、消融结论、可视化证据、局限性与讲述主线"。笔记是知识库的"可检索文本资产",可 diff、可全文搜索、可二次加工。

论文配图统一入库:由 `pdf_extractor.py` 提取的重要截图,按**论文标题**创建文件夹,存入 `assets/paper-imgs/<论文标题>/`,供笔记与 PPT 两条流共用。

### 3. `paper-slides/` —— HTML 汇报 PPT
由 `html-paper-slides`(输入 PDF)或 `blog-to-slides`(输入 `paper-blogs/` 中同一篇论文的阅读笔记,无需 PDF)产出,单文件演示文稿,基于 `paper-blogs/` 中的阅读笔记与 `assets/paper-imgs/` 配图,按分页规划压缩成 13–22 页的讲述结构。章节流为**封面 → 摘要 → 引言 → 方法 → 实验 → 消融 → 结论与展望**,通过卡片、流程图、对比表、指标高亮、导航控件强化阅读节奏。成品入库后,**必须同步更新 `slides-manifest.json`**,确保 `index.html` 画廊可以正确展示标题、路径、简介、类型与主题色。随后运行 `python skills/html-paper-slides/scripts/generate-thumbnails.py` 生成首屏缩略图,画廊卡片便会直接展示真实幻灯片封面。

### 质量检查清单
在进入下一阶段前建议确认:
- `pdf-papers/` 是否可追溯到原始来源(仅 PDF、命名可追踪)
- `paper-blogs/` 笔记是否通过 `check_note.py` 门禁(骨架 / 空格 / 禁用词 / 优点节 / 无编造),并提炼出足够支撑 8–15 页汇报的主线
- 配图是否已按论文标题归档到 `assets/paper-imgs/<论文标题>/`
- HTML PPT 是否可以单文件打开、键盘翻页、视觉层级清晰
- `slides-manifest.json` 是否覆盖 `paper-slides/` 下的全部 HTML 文件
- `assets/thumbnails/` 是否已包含对应缩略图且 `thumbnail` 字段已正确写入 manifest

---

## 项目结构

```
Paper-Master/
├── index.html            # 单页门户:左侧导航栏(首页/幻灯片/博客) + 右侧内容区无刷新切换(由 GitHub Pages 自动部署)
├── pages/                # 独立功能页
│   └── note.html         #   阅读笔记全屏阅读深链(Markdown 渲染 + LaTeX 公式)
├── slides-manifest.json  # paper-slides 演示文稿清单(新增内容后运行 python scripts/generate_manifests.py 重新生成并提交)
├── blogs-manifest.json   # paper-blogs 阅读笔记清单(新增内容后运行 python scripts/generate_manifests.py 重新生成并提交)
├── scripts/
│   └── generate_manifests.py    # 本地重建两份清单(与 pages.yml 内联逻辑一致)
├── README.md             # 中文 README(默认)
├── README.en.md          # 英文 README
├── LICENSE               # MIT 协议
├── paper-slides/         # html-paper-slides 产出的 HTML PPT 成品 + 对应 _assets/ 配图
│   ├── Attention_Is_All_You_Need.html
│   ├── DETRs_Beat_YOLOs_on_Real-time_Object_Detection.html
│   └── ... (更多论文演示)
├── skills/               # 幻灯片 / 笔记制作技能、脚本与模板文档
│   ├── lzk-paper-reading/        # 论文精读 → 中文阅读笔记
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   ├── new_note.py        # 生成 frontmatter + 五节骨架
│   │   │   └── check_note.py      # 笔记门禁校验
│   │   └── references/            # 骨架变体、句式语料、领域迁移映射、典范样例
│   └── html-paper-slides/        # 论文精读 → HTML 汇报 PPT
│       ├── SKILL.md
│       ├── scripts/
│       │   ├── pdf_extractor.py   # 从论文 PDF 中提取核心配图(两条流共用)
│       │   └── generate-thumbnails.py  # 为 HTML 幻灯片生成首屏缩略图
│       └── templates/
│           └── presentation.html  # 论文汇报场景专用 HTML 幻灯片模板
├── .trae/skills/         # TRAE 技能目录:收录 lzk-paper-reading / html-paper-slides / blog-to-slides
│   └── blog-to-slides/           # 阅读笔记 → HTML 汇报 PPT(输入笔记,无需 PDF)
│       ├── SKILL.md
│       ├── scripts/
│       │   └── generate-thumbnails.py  # 为 HTML 幻灯片生成首屏缩略图
│       └── templates/
│           └── presentation.html  # 论文汇报场景专用 HTML 幻灯片模板
├── assets/               # 通用静态资源
│   ├── paper-imgs/       # 论文重要截图库:按论文标题分文件夹归档
│   │   └── <论文标题>/    # 每篇论文提取的重要配图
│   ├── thumbnails/       # HTML 幻灯片首屏缩略图(自动生成)
│   ├── design-prompts/   # 风格设计提示词集合
│   ├── accmulate-ppts.png
│   └── favicon.png
├── pdf-papers/           # 原始论文 PDF 归档(仅 PDF 格式,已 gitignore)
└── paper-blogs/               # lzk-paper-reading 产出的中文阅读笔记 .md 博客文件(已 gitignore)
```

---

## 快速开始

### 1. 准备环境

```bash
git clone https://github.com/luoqianshi/Paper-Master.git
cd Paper-Master
```

- 删除 `paper-slides/` 目录下的所有 `.html` 文件、`paper-blogs/` 下的笔记与 `assets/paper-imgs/` 下的配图(以上为作者个人知识库数据)
- 将 `slides-manifest.json` 文件中的 `slides` 数组清空
- (可选)安装缩略图生成依赖:`pip install playwright && playwright install chromium`
- (可选)安装 PDF 提取依赖:`pip install pymupdf Pillow`

### 2. 选择产出,启动 AI Agent

用 `Claude Code` / `TRAE` / `CodeBuddy` 等 AI 编程工具 / AI 办公工具打开当前项目。

**中文阅读笔记场景:**

```markdown
请你使用 lzk-paper-reading 技能(skills\lzk-paper-reading\SKILL.md),
帮我为 [给定你要阅读的 PDF 论文文件路径] 写一篇中文论文阅读笔记,
最终 .md 文件存放在 paper-blogs 目录下,
提取的论文配图按论文标题归档到 assets/paper-imgs 目录下。
```

**论文汇报 PPT 场景:**

```markdown
请你使用 html-paper-slides 技能(skills\html-paper-slides\SKILL.md),
帮我为 [给定你要制作的 PDF 格式的论文的文件路径] 制作一份
HTML 格式的 PPT,最终文件存放在 paper-slides 目录下。
```

**笔记转 PPT 场景(输入已有阅读笔记,无需 PDF):**

```markdown
请你使用 blog-to-slides 技能(.trae\skills\blog-to-slides\SKILL.md),
帮我为 [给定 paper-blogs 目录下中文阅读笔记的 .md 文件路径] 制作一份
HTML 格式的论文汇报 PPT,最终文件存放在 paper-slides 目录下。
```

> 同一篇论文,你可以先跑笔记流把内容读透,再跑 PPT 流生成汇报(`html-paper-slides` 直接读 PDF,`blog-to-slides` 直接读笔记),两条流共享 `paper-blogs/` 里的阅读笔记与 `assets/paper-imgs/` 里的配图。

### 3. 生成缩略图,自动收录到电子书柜

```bash
python skills/html-paper-slides/scripts/generate-thumbnails.py
```

完成后,新的 HTML PPT 会以**真实首屏封面**出现在 `index.html` 画廊中。推送至 GitHub 后,GitHub Actions 会自动部署至 GitHub Pages。

---

## 技术栈

- **HTML5 + CSS3** —— 演示文稿主体
- **Vanilla JavaScript** —— 分页引擎、键盘交互、淡入动画(无框架依赖)
- **CSS Grid / Flexbox** —— 16:9 响应式布局
- **CSS Variables** —— 主题色与字体变量化管理
- **Markdown + LaTeX** —— 阅读笔记载体(公式行内 `$...$`、独立 `$$...$$`)
- **PyMuPDF + Pillow** —— 从论文 PDF 提取透明背景配图
- **Playwright (Python)** —— 自动生成 HTML PPT 首屏缩略图
- **GitHub Actions** —— 自动部署 `index.html` 至 GitHub Pages

---

## Limitations · 当前局限

我们追求 80 分的稳定可用,而非 100 分的完美:

1. **PDF 配图存在冗余提取**:首版生成后建议手动删除冗余图片,后续会引入视觉语言模型做精选
2. **多模态模型效果更佳**:推荐使用 KIMI K2.6、Minimax M3 等原生多模态模型,纯文本模型会丢失论文配图
3. **当前版本为高质量初稿**:建议在初稿生成后与 Agent 进行多轮对话精修,例如"第 5 页方法图换成架构图" / "页脚加学校 logo"
4. **笔记范式有领域偏斜**:`lzk-paper-reading` 语料以表格数据 ML 为主,写视觉检测类论文时按 `references/research/domain-transfer.md` 切换实验节写法
5. **不直接从 LaTeX 源生成**:若需 LaTeX 高保真,请使用 Beamer;本仓库主打"用 PDF/Markdown 就能上手"
6. **缩略图依赖 Playwright**:首次运行需 `pip install playwright && playwright install chromium`,无图形环境(headless 服务器)需补 `--with-deps` 步骤

---

## 联系方式

欢迎 Star、Fork、提 Issue 与 PR。如希望交流研究生学习 / 论文阅读 / Agent 工作流,可通过以下渠道找到我:

| 平台 | 账号 / 链接 |
|------|------------|
| GitHub | [@luoqianshi](https://github.com/luoqianshi) |
| 在线画廊 | [luoqianshi.github.io/Paper-Master](https://luoqianshi.github.io/Paper-Master/) |

---

## Star History

如果这个仓库对你有帮助,欢迎点一个 Star 支持我们继续迭代:

<a href="https://star-history.com/#luoqianshi/Paper-Master&Date">
  <img src="https://api.star-history.com/svg?repos=luoqianshi/Paper-Master&type=Date" alt="Star History Chart" width="600">
</a>

---

*Last Updated: 2026-09-06 · v1.2 · 科研人的 AI 原生论文知识库 · 3 个 SKILL · 累计收录论文演示 8 份*
