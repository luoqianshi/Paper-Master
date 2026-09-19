---
name: blog-to-slides
description: 生成苹果风/Notion 风的论文阅读 HTML 演示文稿（PPT）。当用户提供 lzk-paper-reading 技能产出的中文阅读笔记（paper-blogs/*.md）并要求「把笔记做成PPT」「笔记转幻灯片」「组会汇报PPT」「HTML 演示文稿」「PPT风格页面」时使用。输入为阅读笔记 + assets/paper-imgs/ 已提取的论文图表（无需 PDF），产出单文件 HTML 幻灯片到 paper-slides/，嵌入论文原始图表，并登记 slides-manifest.json、生成首页截图缩略图。从论文 PDF 直接生成 PPT 请改用 html-paper-slides 技能；写阅读笔记请改用 lzk-paper-reading 技能。
---

# 博客笔记 → HTML 论文演示文稿生成器

生成苹果风/Notion 风的 HTML 演示文稿，用于 AI&CS 专业组会论文阅读汇报或内容展示。

与 html-paper-slides 技能的区别：**本技能的输入不是论文 PDF，而是 lzk-paper-reading 技能产出的中文阅读笔记**（`paper-blogs/<论文名>.md`）及其配套论文图表（`assets/paper-imgs/<论文名>/`）。产出物与 html-paper-slides 完全一致：单文件 HTML 幻灯片 + 首页截图缩略图 + slides-manifest.json 登记。

本技能的全部资源（脚本、模板）位于本技能目录内，以下所有命令均以项目根目录为工作目录执行。

## 项目约定（本仓库专属，必须遵循）

| 项 | 约定 |
| --- | --- |
| 笔记输入 | `paper-blogs/<论文名>.md`（lzk-paper-reading 产出，含 frontmatter + 五节骨架） |
| 图表输入 | `assets/paper-imgs/<论文名>/`（已提取好的论文图表，无需再跑 pdf_extractor） |
| 幻灯片输出 | `paper-slides/<论文名>.html`（单文件 HTML，与现有幻灯片同级） |
| 图片引用 | HTML 内用相对路径 `../assets/paper-imgs/<论文名>/xxx.png` 直接引用，**不复制图片**到 paper-slides/ 下 |
| 缩略图 | `assets/thumbnails/<论文名>.png`，由脚本自动生成 |
| 清单登记 | 生成后必须在 `slides-manifest.json` 的 `slides` 数组末尾追加条目 |

> **图片路径说明**：`paper-blogs/` 与 `paper-slides/` 同为项目根目录下的一级目录，因此笔记正文里的相对路径 `../assets/paper-imgs/<论文名>/xx.png` 在幻灯片 HTML 中**同样有效，直接复用即可**，无需改写、无需复制图片（避免双份存储）。

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

## ⚠️ 铁律：笔记是唯一信息源

> **幻灯片中的每一个公式、数值、数据集名称、实验结论，都必须能在输入笔记中找到出处。**
> 笔记已通过 lzk-paper-reading 的 check_note.py 验证，可直接信任；但**禁止**凭记忆从论文原文「补充」笔记里没有的内容（例如摘要原文、笔记未提及的实验）。信息拿不到就省略该页或该要点，宁可少写，不可编造。

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
| 提示框 | `.prompt-box` | 提示词展示 |
| 发光效果 | `.glow .glow-purple/.glow-yellow` | 装饰背景 |
| 封面元数据 | `.cover-tag` | 标签展示 |
| 图标 | `.icon` | 64x64 白色图标 |

## 工作流程

1. **解析笔记**：Read `paper-blogs/<论文名>.md`，提取：
   - frontmatter：`title / category / date / source_url`
   - 论文概况表：标题 / 作者 / 发表期刊（或会议）+ 等级 / 发表年份 / 论文代码
   - 作者单位（表后编号列表）
   - 五节正文：研究动机 / 文章贡献 / 本文方法 / 实验结果 / 优点和创新点（若笔记含预备知识、理论分析、XX 分析等变体节，一并保留）

2. **盘点图片**：列出 `assets/paper-imgs/<论文名>/` 下全部文件，与笔记中 `![](../assets/paper-imgs/...)` 引用一一对应。幻灯片优先使用笔记已引用的图片；笔记未引用但与页面主题强相关的图（如消融表、可视化结果）也可取用。图片不存在时不得虚构引用。

3. **内容规划**：将笔记内容拆分为 13~22 页，每页聚焦单一主题。章节映射：

   | 笔记章节 | 幻灯片对应 |
   | --- | --- |
   | 论文概况表 + frontmatter | 首页（标题 + 作者 + 作者单位 + 发表期刊/会议） |
   | 文章贡献 | 概述页（替代原技能的「摘要」页，用贡献段散文拆成要点） |
   | 研究动机 | 引言：现有研究不足 + 本文切入点 |
   | 预备知识（如有） | 相关工作/背景综述页（可选） |
   | 本文方法 | 方法：框架总述 + 按 H3 逐模块分述 |
   | 实验结果 | 实验设置 + 主对比 + 消融 + 可视化 |
   | 优点和创新点 | 总结与讨论（优点条目直接转为总结要点） |

4. **结构设计**：
   - 首页（标题 + 作者 + 作者单位 + 发表期刊）
   - 概述（核心贡献要点）
   - 引言（现有研究不足 + 本文主要贡献）
   - 背景综述（可选，来自预备知识节）
   - 方法
   - 实验结果
   - 总结与讨论
   - 结尾

5. **填充内容**：根据模板组件填充具体内容，用 Write 工具将 HTML 保存到 `paper-slides/<论文名>.html`（单文件，图片用相对路径 `../assets/paper-imgs/<论文名>/xxx.png` 引用）。

   **公式排版规则**（笔记是 LaTeX 源，幻灯片是 HTML）：
   - 简单公式（上下标、分式、希腊字母）用 HTML/CSS 排版：`<sup>`/`<sub>`、斜体 `<i>`、Unicode 符号（α β γ λ ∂ ∑ √ ≤ ≥ ×）。
   - 复杂公式优先引用 `assets/paper-imgs/` 中的论文原图（若有对应公式图）。
   - **不引入 MathJax/KaTeX 等 CDN 依赖**，保持 `file://` 协议下零外部依赖可打开。

6. **预览调整**：生成后检查效果并微调。

7. **登记清单**：按上方格式在 `slides-manifest.json` 追加条目。

8. **生成缩略图**：运行 `python .qoder/skills/blog-to-slides/scripts/generate-thumbnails.py` 为新生成的 HTML 幻灯片截取首屏封面，输出到 `assets/thumbnails/`，并自动更新 `slides-manifest.json` 中的 `thumbnail` 字段，使电子书柜首页（index.html）的卡片能展示真实的幻灯片封面而非默认示意图。依赖 `playwright`（缺失时 `pip install playwright && playwright install chromium`）。

## 分页规划建议

| 位置 | 内容 | 页数 |
|------|------|------|
| 首页 | 标题 + 作者 + 作者单位 + 发表期刊 | 1页 |
| 概述 | 核心贡献要点（来自文章贡献节） | 1页 |
| 引言 | 现有研究不足 + 本文切入点（来自研究动机节） | 2页 |
| 背景综述（可选） | 预备知识 / 相关概念（如有） | 2~3页 |
| 方法 | 框架总述 + 关键要点分述（按笔记方法节 H3 组织） | 3~5页 |
| 实验结果 | 实验设置 + 主对比 + 消融 + 可视化（实验节图片为主） | 3~5页 |
| 总结与讨论 | 优点和创新点条目 + 局限与展望（如有） | 2~3页 |
| 结尾 | 简要结束页面 | 1页 |

## 注意事项

1. 每页内容控制在 3-5 个要点以内，避免信息过载
2. 标题使用微深蓝色 (#3966A2)，关键词使用深蓝色 (#132843) 强调
3. 添加 `.glow` 装饰元素增加视觉层次
4. 动画延迟使用 `.anim:nth-child(n)` 递增
5. 封面页使用 `.badge` 和 `.cover-tag` 增加专业感（`category`、发表年份、期刊/会议等级都可做封面标签）
6. 保留左右键前后翻页的功能，但是不要出现显式的左右翻页的控制器
7. 笔记中每张图后都配有解读句——把「图 + 解读结论」一起搬到幻灯片，图注与结论不要拆散
8. 优点和创新点节的有序条目直接作为总结页要点，起手句「个人认为…」可省略，但条目措辞保持原意

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

- **原因**：`generate-thumbnails.py` 通过 `file:///` 绝对 URL 加载 HTML，`../assets/...` 相对路径以 HTML 文件自身位置为基准解析，正常可加载；若空白多为路径笔误（如把 `../assets` 写成 `./assets` 或图片名抄错）
- **解决**：生成后核对每张图片的文件名与 `assets/paper-imgs/<论文名>/` 实际文件一一对应；manifest 登记的 `file` 字段必须是 `paper-slides/<论文名>.html`
