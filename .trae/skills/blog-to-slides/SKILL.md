---
name: blog-to-slides
description: 生成苹果风/Notion 风的论文阅读 HTML 演示文稿（PPT）。当用户提供 lzk-paper-reading 技能产出的中文阅读笔记（paper-blogs/*.md）并要求「把笔记做成PPT」「笔记转幻灯片」「组会汇报PPT」「HTML 演示文稿」「PPT风格页面」时使用。输入为阅读笔记 + assets/paper-imgs/ 已提取的论文图表（不重新提图），并按需通读原始 PDF 正文补充事实细节，产出单文件 HTML 幻灯片到 paper-slides/，嵌入论文原始图表，并登记 slides-manifest.json、生成首页截图缩略图。从论文 PDF 直接生成 PPT 请改用 html-paper-slides 技能；写阅读笔记请改用 lzk-paper-reading 技能。
---

# 博客笔记 → HTML 论文演示文稿生成器

生成苹果风/Notion 风的 HTML 演示文稿，用于 AI&CS 专业组会论文阅读汇报或内容展示。

与 html-paper-slides 技能的区别：**本技能的叙事输入不是论文 PDF，而是 lzk-paper-reading 技能产出的中文阅读笔记**（`paper-blogs/<论文名>.md`）及其配套论文图表（`assets/paper-imgs/<论文名>/`）。但**事实层仍会按需查阅原始 PDF 正文**（见下「三层信息源」）。产出物与 html-paper-slides 完全一致：单文件 HTML 幻灯片 + 首页截图缩略图 + slides-manifest.json 登记。

本技能的全部资源（脚本、模板）位于本技能目录内，以下所有命令均以项目根目录为工作目录执行。

## 项目约定（本仓库专属，必须遵循）

| 项 | 约定 |
| --- | --- |
| 笔记输入 | `paper-blogs/<论文名>.md`（lzk-paper-reading 产出，含 frontmatter + 五节骨架） |
| 图表输入 | `assets/paper-imgs/<论文名>/`（**不重新提取图片**，只复用已有文件） |
| 原始 PDF | 由 `build_asset_ledger.py` 三级兜底定位（`pdf-papers/**/*.pdf`），只读正文、不提图 |
| 素材账本 | `.cache/blog-to-slides/<论文名>/asset_ledger.{json,md}` + `paper_text.txt`（gitignore，不发布） |
| 幻灯片输出 | `paper-slides/<论文名>.html`（单文件 HTML，与现有幻灯片同级） |
| 图片引用 | HTML 内用相对路径 `../assets/paper-imgs/<论文名>/xxx.png` 直接引用，**不复制图片**到 paper-slides/ 下 |
| 缩略图 | `assets/thumbnails/<论文名>.png`，由脚本自动生成 |
| 清单登记 | 生成后必须在 `slides-manifest.json` 的 `slides` 数组末尾追加条目 |

> **图片路径说明**：`paper-blogs/` 与 `paper-slides/` 同为项目根目录下的一级目录，因此笔记正文里的相对路径 `../assets/paper-imgs/<论文名>/xx.png` 在幻灯片 HTML 中**同样有效，直接复用即可**，无需改写、无需复制图片（避免双份存储）。

> **中间产物不得写进 `assets/`**：`assets/paper-imgs/` 被 `index.html` 引用且仓库有 `.nojekyll`，整棵树会原样发布到 GitHub Pages。账本与 PDF 全文一律写入 gitignore 的 `.cache/blog-to-slides/<论文名>/`。

`slides-manifest.json` 条目格式：

```json
{
  "title": "论文标题",
  "file": "paper-slides/<论文名>.html",
  "description": "一句话中文描述：来源会议/期刊 + 聚焦的核心方法与贡献",
  "kind": "期刊/会议",
  "accent": "rgba(57,102,162,.18)",
  "thumbnail": "assets/thumbnails/<论文名>.png"
}
```

`title`、`kind` 等字段从笔记的论文概况表（标题 / 发表期刊或会议）中取，不得编造。

## ⚠️ 铁律：三层信息源与冲突裁决

> **L1 叙事层 = `paper-blogs/<论文名>.md`**（权威于：章节顺序、中文措辞、图后解读句、个人观点）
> **L2 事实层 = 原始 PDF 正文**（权威于：数值、数据集、实验设定、被笔记压缩掉的方法细节）
> **L3 素材层 = `assets/paper-imgs/<论文名>/` + `extraction_summary.json`**（权威于：有哪些图、每张图画什么、尺寸、页码；**只读，不重新提取**）

裁决规则：

1. **叙事从 L1**：幻灯片的章节顺序、中文表述、解读句以笔记为准，保住博客的个人风格。
2. **事实从 L2**：笔记没写的数值/数据集/实验设定，从 PDF 正文补；**禁止凭记忆编造**。
3. **冲突时**：采用 L2 的数值/事实，但**必须在收尾说明中标注该分歧**，不得静默覆盖笔记作者原意。
4. **素材从 L3**：图片全集以**磁盘实际文件**为准（`extraction_summary.json` 的 `items` 实测存在单向缺失，全库 216/767 博客引用图不在其中，只可作元数据）。
5. **表格数据以 L3 的表格图片为准**，不得采信 PDF 抽取出的单元格碎片文本。
6. 信息拿不到就省略该页或该要点，**宁可少写，不可编造**。

## 核心样式规范（必须严格遵循）

### 配色方案

| 用途 | 颜色值 | 说明 |
|------|--------|------|
| 主背景色 | `#ffffff` | 纯白色 |
| 主文字色 | `#000000` | 纯黑色 |
| 标题文字色 | `#3966A2` | 微深蓝色 |
| 强调文字色 | `#132843` | 深蓝色 |
| 次要文字色 | `#6191D3` | 浅蓝色 |

### 字体规范

```
系统字体栈: 'Inter', 'Noto Sans SC', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif
标题权重: 700-800
正文权重: 400-500
```

### 布局规范

- 页面比例: 16:9 (padding: 5vh 7vw)
- 使用 CSS Grid/Flexbox 弹性布局
- 字号使用 clamp() 响应式缩放

## HTML 模板

以本技能目录下 `templates/presentation.html` 为基础模板（先 Read 该文件再改写），包含：

### 必需组件

1. **Slide Engine** - 分页切换逻辑
2. **Progress Bar** - 顶部进度条
3. **Dots** - 右侧导航点
4. **Animations** - 淡入动画

### 可复用组件

| 组件 | 类名 | 用途 |
|------|------|------|
| 卡片 | `.card`, `.card-grid` | 内容块 |
| 徽章 | `.badge` | 标签/分类 |
| 高亮条 | `.highlight-bar` | 强调内容 |
| 对比栏 | `.vs-col .ppt-col / .html-col` | 对比展示 |
| 步骤流 | `.steps .step` | 流程展示 |
| 引用框 | `.quote-block` | 引言/金句 |
| 圆圈图 | `.ipo-circle` | IPO/I-P-O 流程 |
| 列表 | `.bullet-list li::before` | 要点列表 |
| 提示框 | `.prompt-box` | 提示词/公式展示 |
| 发光效果 | `.glow .glow-purple/.glow-yellow` | 装饰背景 |
| 封面元数据 | `.cover-tag` | 标签展示 |
| 图标 | `.icon` | 64x64 白色图标 |
| 双图并排 | `.fig-pair .cell` | 两张 square 图并排（可视化对比） |
| 图文分栏 | `.split .split-text` | 左文右图 |

## 工作流程（11 步）

1. **生成素材账本**：

   ```
   python .qoder/skills/blog-to-slides/scripts/build_asset_ledger.py <论文名>
   ```

   依赖 `pymupdf` 与 `Pillow`（缺失时 `pip install pymupdf Pillow`）。产出 `.cache/blog-to-slides/<论文名>/` 下的 `asset_ledger.json`、`asset_ledger.md`、`paper_text.txt`，并打印 PDF 定位结果与页数预算。PDF 定位三级兜底：`extraction_summary.json` 的 `pdf_path` → 文件名/标题模糊匹配（**top1 ≥ 0.85 且与次优差距 ≥ 0.15**，否则不采用）→ `--pdf <路径>` 人工指定。

2. **逐行过账本**：Read `asset_ledger.md`，把**全部**图片行（含 `unused_in_blog`）过一遍，确认每张图的形态（wide/square/tall）、博客章节与解读句。

3. **通读 PDF 正文**：Read `paper_text.txt`（L2 事实层）。正文为列感知抽取结果；表格页的碎片文本不可信，表格以图片为准。

4. **通读笔记**：Read `paper-blogs/<论文名>.md` 全文（L1 叙事层）。

5. **产出规划表**（写 HTML 前必须完成）：`页码 | 主题 | 用哪张图 | 图的博客章节归属 | 事实来源(PDF页码) | 叙事来源(笔记章节)`。硬约束：
   - 每个 `in_blog=true` 的图必须落在某一行；
   - 章节归属须与账本 `blog_sections` 一致 —— **禁止用方法节的图凑满总数而把可视化节掏空**；
   - 「可视化分析 / 定性结果」章节的图不得降级进图集页，必须独占整页或半页；
   - `aspect=wide` 的图独占整页或半页，不得塞进窄栏。

6. **填充内容**：按规划表用 Write 工具将 HTML 保存到 `paper-slides/<论文名>.html`（单文件，图片用相对路径 `../assets/paper-imgs/<论文名>/xxx.png` 引用）。页数须落在账本 `page_budget` 的 `[min, max]` 区间内。

   **公式排版规则**（笔记是 LaTeX 源，幻灯片是 HTML）：
   - 简单公式（上下标、分式、希腊字母）用 HTML/CSS 排版：`<sup>`/`<sub>`、斜体 `<i>`、Unicode 符号（α β γ λ ∂ ∑ √ ≤ ≥ ×）。
   - 复杂公式优先引用 `assets/paper-imgs/` 中的论文原图（若有对应公式图）。
   - **不引入 MathJax/KaTeX 等 CDN 依赖**，保持 `file://` 协议下零外部依赖可打开。

7. **跑门禁**：

   ```
   python .qoder/skills/blog-to-slides/scripts/verify_slides.py <论文名>
   ```

   **不通过则回到第 6 步修补，禁止跳过、禁止进入第 8 步。** 豁免须显式：`--allow-missing <图>` / `--allow-extra-pages <n>`，并在收尾说明豁免理由。

8. **登记清单**：按上方格式在 `slides-manifest.json` 追加条目。

9. **生成缩略图**：运行 `python .qoder/skills/blog-to-slides/scripts/generate-thumbnails.py` 为新生成的 HTML 幻灯片截取首屏封面，输出到 `assets/thumbnails/`，并自动更新 `slides-manifest.json` 中的 `thumbnail` 字段。依赖 `playwright`（缺失时 `pip install playwright && playwright install chromium`）。注意该脚本会遍历全部 HTML，若只想更新单篇请确认副作用可接受。

10. **人工浏览复核**：逐页翻看，确认无溢出、无图片变形、图注与结论同页。

11. **收尾说明**：报告页数 / 用图数 / 覆盖率、`pdf_resolution`、任何降级（PDF 未找到、扫描版）或豁免。

## 分页规划建议（动态页数）

```
N        = 博客引用图数（账本 blog_ref_count）
图页下限 = ceil(N / 2)        # 允许每页最多 2 图（仅限 square/tall）
结构页   = 7                  # 首页1 + 概述1 + 引言2 + 总结2 + 结尾1
page_budget.min = 7 + ceil(N / 2)
page_budget.max = min(8 + N, 30)
```

| 位置 | 内容 | 页数 |
|------|------|------|
| 首页 | 标题 + 作者 + 作者单位 + 发表期刊 | 1页 |
| 概述 | 核心贡献要点（来自文章贡献节） | 1页 |
| 引言 | 现有研究不足 + 本文切入点（来自研究动机节） | 1~2页 |
| 背景综述（可选） | 预备知识 / 相关概念（如有）；**占用 max 预算内额度** | 0~3页 |
| 方法 | 形式化 + 框架总述 + 按 H3 逐模块分述 | 3~6页 |
| 实验结果 | 实验设置 + 主对比 + 横向对比 + 消融 + 可视化（实验节图片为主） | 4~8页 |
| 总结与讨论 | 优点和创新点条目 + 局限与展望（如有） | 1~2页 |
| 结尾 | 简要结束页面（可与总结合并） | 0~1页 |

当 N 大到触及 30 页封顶时，超出部分放入 grid 图集页（每页 4~6 张缩略图 + 简短图注），**仍计入 100% 覆盖**；但「可视化分析」节的图除外（见工作流第 5 步）。

## 注意事项

1. 每页内容控制在 3-5 个要点以内，避免信息过载
2. 标题使用微深蓝色 (#3966A2)，关键词使用深蓝色 (#132843) 强调
3. 添加 `.glow` 装饰元素增加视觉层次
4. 动画延迟使用 `.anim:nth-child(n)` 递增
5. 封面页使用 `.badge` 和 `.cover-tag` 增加专业感（`category`、发表年份、期刊/会议等级都可做封面标签）
6. 保留左右键前后翻页的功能，但是不要出现显式的左右翻页的控制器
7. 笔记中每张图后都配有解读句——把「图 + 解读结论」一起搬到幻灯片，图注与结论不要拆散
8. 优点和创新点节的有序条目直接作为总结页要点，起手句「个人认为…」可省略，但条目措辞保持原意
9. **横长图（`aspect=wide`，如框架图、宽对比表）独占整页或半页，不得塞进窄栏**；两张 square 图并排用 `.fig-pair`
10. **表格数据以 `assets/paper-imgs/` 中的表格图片为准**，不得采信 PDF 抽取出的单元格碎片文本

## ⚠️ 已知问题 & 解决方案（必须遵循）

### 问题1：字体无法加载（404）

- **原因**：`<link>` 标签加载 Google Fonts，在 `file://` 协议下被浏览器安全策略拦截
- **解决**：使用纯系统字体 `font-family: 'Inter', 'Noto Sans SC', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif`，零外部依赖

### 问题2：翻页后内容空白

- **原因**：JS 用 `element.style.xxx = '...'` 设置 inline style 切换页面，但这些 inline style 无法被 CSS 正确覆盖，导致新页面保持 `opacity: 0`
- **解决**：
  1. CSS 的 `.slide.active` 三个关键属性必须加 `!important`：`opacity`、`visibility`、`transform`
  2. JS 翻页函数**禁止使用 inline style**，只操作 `classList.add/remove('active')` 和 `classList.add('exit-up')`，完全由 CSS transition 处理动画

### 问题3：相对路径图片在缩略图截屏中空白

- **原因**：路径笔误（如把 `../assets` 写成 `./assets` 或图片名抄错）
- **解决**：**由 `verify_slides.py` 的检查 2（`naturalWidth > 0`，证明图片真实加载）与检查 5（src 前缀必须为 `../assets/paper-imgs/<名>/`）自动拦截**，无需人工核对

### 问题4：幻灯片丢弃博客已有截图（本技能的历史顽疾）

- **原因**：旧版把笔记当唯一信息源且限死 13~22 页，模型边写边想、写到后半程乏力就丢图；实测全库 699 张博客引用图只用了 364 张（丢 48%），且丢图集中在「可视化分析」节
- **解决**：工作流第 5 步「规划表先行」+ 第 7 步「覆盖率门禁」。`verify_slides.py` 检查 1 要求博客引用图 100% 出现，缺失即非零退出并列出清单

### 问题5：双栏论文 PDF 正文抽取错乱

- **原因**：裸 `page.get_text()` 先吐图内标签汤；`get_text(sort=True)` 会把左右两栏合并到同一行
- **解决**：`build_asset_ledger.py` 使用列感知块抽取（按页面中线分栏、栏内按 y 排序），并用 `extraction_summary.json` 的图 bbox 过滤图区文本块
