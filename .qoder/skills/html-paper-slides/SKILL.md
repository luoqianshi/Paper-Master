---
name: html-paper-slides
description: 生成苹果风/Notion 风的论文阅读 HTML 演示文稿（PPT）。当用户提供论文 PDF（通常在 pdf-papers/ 目录）并要求「做论文阅读PPT」「组会汇报PPT」「论文精读幻灯片」「HTML 演示文稿」「PPT风格页面」时使用。产出单文件 HTML 幻灯片到 paper-slides/，嵌入论文原始图表，并登记 slides-manifest.json。写阅读笔记请改用 lzk-paper-reading 技能。
---

# HTML 论文演示文稿生成器

生成苹果风/Notion 风的 HTML 演示文稿，用于 AI&CS 专业组会论文阅读汇报或内容展示。

本技能的全部资源（脚本、模板）位于本技能目录内，以下所有命令均以项目根目录为工作目录执行。

## 项目约定（本仓库专属，必须遵循）

| 项 | 约定 |
| --- | --- |
| 幻灯片输出 | `paper-slides/<论文名>.html`（单文件 HTML，与现有幻灯片同级） |
| 论文图表素材 | 提取到 `paper-slides/<论文名>_assets/`，HTML 内用相对路径 `<论文名>_assets/xxx.png` 引用 |
| 论文 PDF 输入 | 用户通常放在 `pdf-papers/`，也可能给出任意路径或 arXiv 链接 |
| 缩略图 | `assets/thumbnails/<论文名>.png`，由脚本自动生成 |
| 清单登记 | 生成后必须在 `slides-manifest.json` 的 `slides` 数组末尾追加条目 |

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

1. **理解论文**：先通读论文内容，然后运行提取脚本获取论文原始图表（透明背景裁剪）：

   ```
   python .qoder/skills/html-paper-slides/scripts/pdf_extractor.py <pdf路径> --output-dir paper-slides/<论文名>_assets
   ```

   依赖 `pymupdf` 与 `Pillow`（缺失时先 `pip install pymupdf Pillow`）。脚本按 Figure/Table 出现顺序逐一提取，输出 `crop_XXX_pageYYY_regZ.png` 语义化命名；提取效果不佳时可加 `--fallback-blind-crop --clean` 盲裁剪兜底。按分页规划建议各部分结构提取论文内容。

2. **内容规划**：将内容拆分为 13~22 页，每页聚焦单一主题。

3. **结构设计**：
   - 首页（标题 + 作者 + 作者单位 + 发表期刊）
   - 摘要（标题 + 摘要原文）
   - 引言（现有研究不足 + 本文主要贡献）
   - 相关工作综述（可选）
   - 方法
   - 实验结果
   - 总结与讨论
   - 结尾

4. **填充内容**：根据模板组件填充具体内容，用 Write 工具将 HTML 保存到 `paper-slides/<论文名>.html`（单文件，图片用相对路径引用 `<论文名>_assets/` 内的图表）。

5. **预览调整**：生成后检查效果并微调。

6. **登记清单**：按上方格式在 `slides-manifest.json` 追加条目。

7. **生成缩略图**：运行 `python .qoder/skills/html-paper-slides/scripts/generate-thumbnails.py` 为新生成的 HTML 幻灯片截取首屏封面，输出到 `assets/thumbnails/`，并自动更新 `slides-manifest.json` 中的 `thumbnail` 字段，使电子书柜首页（index.html）的卡片能展示真实的幻灯片封面而非默认示意图。依赖 `playwright`（缺失时 `pip install playwright && playwright install chromium`）。

## 分页规划建议

| 位置 | 内容 | 页数 |
|------|------|------|
| 首页 | 标题 + 作者 + 作者单位 + 发表期刊 | 1页 |
| 摘要 | 标题 + 摘要原文 | 1页 |
| 引言 | 现有研究不足 + 本文主要贡献 | 2页 |
| 相关工作综述（可选） | 按并列/倒金字塔型叙述逻辑阐述（如有） | 2~3页 |
| 方法 | 主要方法框架图总述 + 关键要点分述 | 3~5页 |
| 实验结果 | 实验设置 + 实验结果（表格+分析） + 消融实验（如有） + 结果可视化（如有） | 3~5页 |
| 总结与讨论 | 实验结论阐述 + 局限（如有） + 未来展望 | 2~3页 |
| 结尾 | 简要结束页面 | 1页 |

## 注意事项

1. 每页内容控制在 3-5 个要点以内，避免信息过载
2. 标题使用微深蓝色 (#3966A2)，关键词使用深蓝色 (#132843) 强调
3. 添加 `.glow` 装饰元素增加视觉层次
4. 动画延迟使用 `.anim:nth-child(n)` 递增
5. 封面页使用 `.badge` 和 `.cover-tag` 增加专业感
6. 保留左右键前后翻页的功能，但是不要出现显式的左右翻页的控制器

## ⚠️ 已知问题 & 解决方案（必须遵循）

### 问题1：字体无法加载（404）

- **原因**：`<link>` 标签加载 Google Fonts，在 `file://` 协议下被浏览器安全策略拦截
- **解决**：使用纯系统字体 `font-family: 'Inter', 'Noto Sans SC', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif`，零外部依赖

### 问题2：翻页后内容空白

- **原因**：JS 用 `element.style.xxx = '...'` 设置 inline style 切换页面，但这些 inline style 无法被 CSS 正确覆盖，导致新页面保持 `opacity: 0`
- **解决**：
  1. CSS 的 `.slide.active` 三个关键属性必须加 `!important`：`opacity`、`visibility`、`transform`
  2. JS 翻页函数**禁止使用 inline style**，只操作 `classList.add/remove('active')` 和 `classList.add('exit-up')`，完全由 CSS transition 处理动画
