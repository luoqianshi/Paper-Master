# blog-to-slides PDF 增强改造设计

日期：2026-10-29
状态：待用户复核（尚未实施，SKILL.md 与脚本均未改动）
范围：`.qoder/skills/blog-to-slides/`

## 1. 背景与问题

`blog-to-slides` 从中文阅读笔记（`paper-blogs/*.md`）生成 HTML 幻灯片。实测发现生成的幻灯片大量丢弃博客里已有的论文截图，质量明显低于早期 `html-paper-slides` 直接从 PDF 生成的产物。

### 1.1 实测数据

对全库 53 份「既有博客又有幻灯片」的论文统计：

| 指标 | 实测值 |
| --- | --- |
| 已提取图片总数（`assets/paper-imgs/`） | 819 |
| 博客笔记引用的图片数 | 699 |
| 幻灯片实际使用的图片数 | 364 |
| **博客引用了却被幻灯片丢弃的图片数** | **335（占博客引用的 48%）** |

丢图最严重的样本：

| 论文 | 磁盘图片 | 博客引用 | 幻灯片使用 | 丢弃 |
| --- | --- | --- | --- | --- |
| RSO-YOLO | 27 | 27 | 6 | 21 |
| YOLOv12n-RCL-Sunflower | 33 | 20 | 3 | 17 |
| YOLO11n-EWL-Sugarcane-Bud | 21 | 21 | 5 | 16 |
| gcmd-yolo | 44 | 16 | 1 | 16 |
| DDMA-YOLO | 25 | 25 | 11 | 14 |

用户点名的 CARAFE 案例：

| 项 | 值 |
| --- | --- |
| `assets/paper-imgs/CARAFE/` 提取图片 | **14 张**（fig1–fig9 共 9 图 + table2/3/4/6/7 共 5 表） |
| `paper-blogs/CARAFE.md` 引用 | 11 张 |
| `paper-slides/CARAFE.html` 使用 | **6 张**（fig2、fig3、fig5、table2、table4、table6） |
| 丢弃的博客引用图 | **fig1、fig4、fig8、fig9、table7** |
| CARAFE.html 规模 | 12 页 / 343 行 |
| 对照组 FreqFusion.html（早期 PDF 直生） | 21 页 / 1170 行 / 20 图 |

> 值得注意：FreqFusion 虽是公认质量最好的参照物，但其博客引用 26 图、幻灯片只用 20 图 —— **早期的 PDF 直生流程同样没做到 100% 覆盖**。因此本设计的覆盖率要求是一个**高于两个现有技能的新标准**，而非 merely 回到旧水平。

### 1.2 根因分析

**根因一：铁律把 PDF 锁死了。** `SKILL.md` L42-45「⚠️ 铁律：笔记是唯一信息源」明确**禁止**凭论文原文补充笔记里没有的内容。而笔记是 15 页论文压成 152 行的有损摘要，生成器无料可扩，只能产出薄页；薄页装不下图，图就被丢弃。这是用户要求修改的核心条款。

**根因二：页数上限与图数在数学上冲突。** `SKILL.md` L111 限定 13~22 页，但 RSO-YOLO 博客引用了 27 张图。按一图一页根本放不下，丢弃成为必然。CARAFE 现有 12 页甚至低于其合理下限 13 页。

**根因三：技能从不读 `extraction_summary.json`。** 该文件已存有：原始 PDF 的绝对路径、每张图的 `type` / `number` / `label` / **完整原文 caption** / `page` / `bbox` / `width` / `height`。而 `SKILL.md` L109 只要求「列出目录下全部文件」，于是模型不知道 fig6、fig7、table3 画的是什么，不敢用；也不知道 fig2 是 786×368 的横长框架图，塞进窄栏必然显得单薄。

**根因四：没有任何覆盖率校验。** 生成完直接登记 manifest、截图缩略图，丢掉 48% 的图也不会报警。

**根因五：丢图不是随机的，而是整节被掏空 —— 且掏空的正是最有汇报价值的那节。** 把 CARAFE 被丢的 5 张图按博客章节归位：

| 博客章节 | 博客引用图 | 幻灯片保留 | 丢弃 |
| --- | --- | --- | --- |
| 可视化分析 | fig5、fig4、fig8、fig9 | **仅 fig5** | fig4、fig8、fig9（3/4） |
| 对比实验 | table2、table4、table7 | table2、table4 | table7 |
| 在主流架构中的集成 | fig3、fig1 | fig3 | fig1 |

被丢的 fig4（1403×413）、fig8（1403×1331）、fig9（1214×1444）恰好是论文定性结果对比图 —— 组会汇报里最抓眼球的素材。**「可视化分析」一节被砍掉 3/4**，这才是 CARAFE 观感远逊于 FreqFusion 的直接原因。

这说明：仅保证「全局用够 N 张图」不足够，模型完全可能用方法节的图凑满数量、同时把可视化节掏空。因此规划表必须**按章节归属图片**，校验报告必须**分节呈现覆盖分布**（见 §5.2、§8）。

### 1.3 复用 PDF 的可行性（已验证）

对 59 个 `assets/paper-imgs/*/` 目录统计（其中 58 个有对应博客、属本技能适用范围；第 59 个 `YOLOv5s-Mid-Tillage-Sugarcane` 既无博客也无幻灯片）：

| 情况 | 数量 | 处理 |
| --- | --- | --- |
| `extraction_summary.json` 中 `pdf_path` 当前有效 | 50 | 直接使用 |
| `pdf_path` 过期（FreqFusion 指向旧 `D:\trae_projects\`） | 1 | 文件名回搜恢复 |
| 无 `extraction_summary.json` | 8 | 按标题模糊匹配 |

无 summary 的 8 个：DySample、Dynamic-Head、Mona、Powerful-IoU、VarifocalNet、YOLO-PEFT、gcmd-yolo、psmf-yolo。

PDF 实际归档在 `pdf-papers/` 下的**多层主题子目录**中，文件名带年份前缀且与博客文件名不同（例：博客 `CARAFE.md` ↔ `pdf-papers/Improve YOLO12/UpSample Modules/2019 CARAFE_Content-Aware ReAssembly of FEatures.pdf`）。因此必须有可靠的定位机制，不能靠命名约定猜测。

依赖环境已确认可用：`fitz`/`pymupdf` 1.27.2.2、`PIL` 9.4.0、`playwright`。

## 2. 目标与非目标

### 2.1 目标

- **G1**：博客引用的图片 100% 出现在生成的幻灯片中，且**机械可验证**（非提示词自觉）。
- **G2**：引入原始 PDF 正文作为事实补充源；图片一律**不重新提取**，只复用 `assets/paper-imgs/`。
- **G3**：页数随图片数弹性伸缩，使产物厚度对齐早期 PDF 直生水平（CARAFE 目标 ≥13 页 / 11 图，即 §6 预算下限）。
- **G4**：以 CARAFE 为试点端到端验证，产出可量化的前后对比。

### 2.2 非目标

- 不修改 `html-paper-slides` 技能。
- 不批量重生成存量 53 份幻灯片（试点验收后另议）。
- 不做 OCR（扫描版 PDF 走降级路径）。
- 不改动幻灯片视觉风格、配色、模板组件（`templates/presentation.html` 不动）。
- 不修改 `lzk-paper-reading` 的笔记产出契约。

## 3. 用户已确认的设计决策

| 决策点 | 选定 |
| --- | --- |
| 图片覆盖策略与页数预算 | 弹性页数 + 博客引用图 100% 覆盖 |
| PDF 阅读深度 | 全文通读一次纯文本（不渲染页面、不裁图） |
| 笔记与 PDF 冲突时的优先级 | 叙事从笔记，事实从 PDF |
| 存量修复 | 先用 CARAFE 做试点验证 |

## 4. 架构：三层信息源 + 一道门禁

| 层 | 来源 | 权威范围 | 读写 |
| --- | --- | --- | --- |
| L1 叙事层 | `paper-blogs/<名>.md` | 章节顺序、中文措辞、图后解读句、个人观点 | 只读 |
| L2 事实层 | `pdf-papers/**/*.pdf` 纯文本 | 数值、数据集、实验设定、被笔记压缩掉的方法细节 | 只读 |
| L3 素材层 | `assets/paper-imgs/<名>/` + `extraction_summary.json` | 有哪些图、每张图画什么、尺寸、页码 | 只读图片；写账本 |

**冲突裁决规则**：叙事从 L1，事实从 L2。当 L2 的事实与 L1 的表述矛盾时，采用 L2 的数值/事实，但**必须在幻灯片或收尾说明中标注该分歧**，不得静默覆盖笔记作者的原意。

**门禁**：`verify_slides.py` 未通过时，禁止登记 `slides-manifest.json`、禁止运行 `generate-thumbnails.py`。

## 5. 组件设计

### 5.1 C1 — `scripts/build_asset_ledger.py`

```
python .qoder/skills/blog-to-slides/scripts/build_asset_ledger.py <论文名> [--pdf <路径>] [--emit-text] [--json]
```

`<论文名>` 即 `paper-blogs/<论文名>.md` 与 `assets/paper-imgs/<论文名>/` 共用的目录名。

**职责**

1. **定位 PDF**（三级兜底，见 §7.1），记录 `pdf_resolution`。
2. **抽取 PDF 纯文本（必须列感知，不可用裸 `get_text()`）**：不渲染页面、不提图。

   > ⚠️ **实测：双栏论文的裸抽取不可用。** 对 CARAFE 第 5 页：
   > - `page.get_text()` 先吐出图内标签汤（`C2 C3 C4 C5 P6 P5 P4 P3 P2`）再出图注，正文被打碎成平均 44 字的短行；
   > - `page.get_text(sort=True)` **更糟** —— 它把左右两栏合并到同一行，产出 `"P6 ... Partial Conv [23]. There are t"` 这种跨栏混排文本，平均行长 105 但内容是错的。
   >
   > 若照此喂给模型，L2 事实层本身就是乱的，反而会诱发误读数值 —— 正是本次改造要消除的失败模式。

   **采用列感知块抽取**：`page.get_text("blocks")` → 只留 `block_type == 0`（文本块）→ 以页面宽度中线把块分为左右两栏 → 各栏内按 y 坐标（量化到 ~6pt 容差）再按 x 排序 → 先左栏后右栏拼接。实测第 5 页可得到连贯正文（例：`"...mantic information of different levels in this task. UperNet is a strong baseline for semantic segmentation. It uses upsampling in the following three components, i.e., PPM, FPN, FUSE. We adopt CARAFE instead of their original..."`）。

   可选增强：用 `extraction_summary.json` 中该页的图 `bbox` 过滤掉落在图区内的文本块，进一步减少标签汤（**但保留图注**，图注是有用信息）。CARAFE 实测过滤后 49483 → 47156 字符。

   表格页会产出单元格碎片文本（如第 6 页的 `Method / AP / AP50 ...`）—— 这是预期行为；表格同时已作为图片存在于 `assets/paper-imgs/`，SKILL.md 须规定**表格数据以图片为准，不以碎片文本为准**。

   `--emit-text` 时输出到 stdout，否则仅统计字符数；始终写入 **`.cache/blog-to-slides/<名>/paper_text.txt`** 供 Read。

   > ⚠️ **不得写进 `assets/paper-imgs/`**：该目录被 `index.html` 直接引用，且仓库根有 `.nojekyll`，意味着整棵树会**原样发布到 GitHub Pages**（当前已 287 MB）。把论文全文抽取结果放进去，等于**公开发布 59 篇论文的正文文本** —— 对 Elsevier / ICCV 等有版权的论文，这比作者现有只发布图表切片的做法风险高得多。故全文与账本一律写入 gitignore 的 `.cache/`（见 §5.4）。

   **通读成本实测（50 个可解析 PDF）**：字符数 min 16072 / **中位 38956** / max 116118 / 均值 43226，约合 **中位 1.2 万 token、最坏 3.5 万 token**。因此用户选定的「全文通读一次纯文本」在成本上完全可行，无需退化为按章节定向读取。
3. **构建图片全集（磁盘优先，summary 仅作元数据）**：

   > ⚠️ **实测发现，此步不可颠倒**：`extraction_summary.json` 的 `items` 相对目录内容**存在单向缺失**。全库 767 处博客图片引用中，**216 处（28%）**的文件在磁盘上存在、却不在 summary 的 `items` 里。例：`assets/paper-imgs/Coordinate-Attention/` 磁盘有 13 张图（`fig1–fig4 + table1–table9`），而 summary 只列 10 项（`fig1 + table1–table9`），**漏掉 fig2/fig3/fig4**。
   >
   > （勘误：本段初稿曾称漂移为「双向」、并称 summary 含 `table8.png`/`table9.png` 幽灵条目 —— 该结论来自一次被截断的目录打印，**不成立**；实测 `stale_summary_entries` 在该目录为空。教训：取证输出不得截断。）
   >
   > 若以 summary 的 `items` 作为图片全集，覆盖率检查的基线就会缺掉 28% 的博客引用图，**门禁会在漏图的情况下报绿**。

   因此全集按此优先级合成：
   - **基准集 = 磁盘上实际存在的图片文件**（存在性的唯一权威）。扫描时**只取 `.png/.jpg/.jpeg` 扩展名**，并显式排除 `extraction_summary.json` 等非图片文件 —— 不加过滤会把 JSON 误计为图片（本次设计过程中即因此把 CARAFE 的 14 张图错记成 15 张）。账本与全文写在 `.cache/` 而非本目录（§5.4），故不存在自产物污染。
   - 用 summary 的 `items` 按 `filename` 尽力富化 `type`/`num`/`caption`/`page`；命中则 `caption_source="summary"`，未命中则 `caption_source="none"`。
   - **`w`/`h` 一律用 PIL 从图片文件实读**（PIL 9.4.0 已是本技能依赖），不采信 summary 的尺寸，保证 `aspect` 永远可算。
   - summary 中列出但磁盘不存在的条目，记入账本 `stale_summary_entries` 并在报告里提示，**不得**进入图片全集。
   - 博客引用了、但既不在磁盘也不在 summary 的文件 → 记入 `broken_blog_refs` 并报错退出（实测当前为 0，属未来防护）。
4. **解析博客**：提取每张图所属的 H2/H3 章节路径、`![alt]()` 中的中文图注、以及图后紧邻的解读句（lzk-paper-reading 契约要求每图配解读句）。

   实测鲁棒性（58 篇博客、767 处图片引用）：
   - **98%（755/767）**的图片后 3 行内有 ≥15 字正文，解读句抽取假设成立；剩余 2% 须容忍 `blog_note` 为空而不报错。
   - **58/767** 处 `alt` 为空，故 `blog_caption` 必须有兜底：`alt` 非空取 `alt`，否则取解读句首句（截断至 30 字），再否则取 `extraction_summary.json` 的 `caption` 首句。三者全空则置 `null`，不得抛异常。
   - 所有 58 篇博客都至少引用一张 `paper-imgs` 图，不存在「零图博客」分支。
5. **计算 `aspect`**：`wide`（w/h > 1.6）、`square`（0.8~1.6）、`tall`（< 0.8）。
6. **计算页数预算**（见 §6）。
7. **输出账本**：`.cache/blog-to-slides/<名>/asset_ledger.json`（机读）+ `asset_ledger.md`（人读表格，供模型逐行处理）。

**输出 schema**

```json
{
  "paper": "CARAFE",
  "generated_at": "2026-10-29T00:00:00",
  "pdf_path": "D:\\...\\2019 CARAFE_Content-Aware ReAssembly of FEatures.pdf",
  "pdf_resolution": "summary",
  "pdf_pages": 15,
  "pdf_text_chars": 62000,
  "page_budget": { "min": 13, "max": 19, "cap": 30 },
  "extracted_count": 14,
  "blog_ref_count": 11,
  "blog_sections": [
    { "section": "实验结果 > 可视化分析", "images": ["fig5.png", "fig4.png", "fig8.png", "fig9.png"] }
  ],
  "images": [
    {
      "file": "fig2.png",
      "type": "figure",
      "num": "2",
      "page": 3,
      "w": 786, "h": 368,
      "aspect": "wide",
      "caption": "Figure 2: The overall framework of CARAFE...",
      "caption_source": "summary",
      "in_blog": true,
      "blog_section": "本文方法 > 问题形式化与整体框架",
      "blog_caption": "CARAFE 整体框架",
      "blog_note": "图后解读句原文"
    }
  ],
  "unused_in_blog": ["fig6.png", "fig7.png", "table3.png"],
  "stale_summary_entries": [],
  "broken_blog_refs": []
}
```

`asset_ledger.md` 为同内容的表格视图，列：文件 / 类型 / 页 / 尺寸 / 形态 / 博客章节 / 中文图注 / 原文 caption（截断至 200 字）/ 是否被博客引用。

### 5.2 C2 — `scripts/verify_slides.py`

```
python .qoder/skills/blog-to-slides/scripts/verify_slides.py <论文名> [--allow-missing a.png b.png] [--allow-extra-pages 3] [--json]
```

**实现方式：在真实 DOM 上断言，不做纯正则**

复用 `playwright`（已是本技能 `generate-thumbnails.py` 的硬依赖，环境已确认可用），以 `file:///` 加载生成的 HTML 后取真实 DOM。这比正则强在两处：页数与幻灯片引擎的定义**完全一致**；图片是否**真的加载成功**可被证明（正则只能证明路径字符串在磁盘上存在）。

**五项检查**（任一失败 → 退出码 1，并打印完整缺失清单）

| # | 检查 | 判定（基于真实 DOM） | 性质 |
| --- | --- | --- | --- |
| 1 | 博客引用图覆盖率 | 账本中 `in_blog=true` 的每个文件，必须出现在某个 `img[src]` 中；`--allow-missing` 显式豁免的不计入失败 | 门禁（主） |
| 2 | 图片真实加载 | 每个 `src` 含 `paper-imgs/` 的 `<img>`，`naturalWidth > 0`（已实测可行，根治现有「已知问题3」） | 门禁 |
| 3 | 页数达标 | `document.querySelectorAll('.slide').length` ≥ `page_budget.min` | 门禁 |
| 4 | 页数不超限 | 同上 ≤ `page_budget.max`（防止用空白页凑数） | 门禁 |
| 5 | 路径前缀正确 | `img.getAttribute('src')` 以 `../assets/paper-imgs/<名>/` 开头，不得为 `./assets/...` 或绝对路径 | 门禁 |
| 6 | 空页守卫 | 每个含 `paper-imgs` 图的 `.slide`，其 `textContent` 中文字符数 ≥ 20 | 门禁（弱） |

**为什么不设「图片密度」门禁（设计过程中曾加入，实测后删除）**

曾计划以 `唯一用图数 / 页数 ≥ 0.6` 作为门禁，阈值取自 53 份幻灯片的实测分布（最低 0.09 gcmd-yolo、中位 0.50、最高 0.95 FreqFusion）。**该设计有两处缺陷，均已实测证伪**：

1. **密度把「论文图少」与「幻灯片注水」混为一谈。** 对 Focaler-IoU（博客仅引用 3 图），即便覆盖 100% 且页数取到上限 11，密度也只有 **0.27** —— 一个完全合格的产物会被判不合格。低 N 论文在数学上不可能达到 0.6。
2. **有了检查 1 + 检查 3 + 检查 4，密度已被自动约束，属冗余。** 覆盖 100% 时密度 = N / 页数 ≥ N / `max`。实测 52 篇的隐含密度下限随 N 单调上升（N=3 → 0.27，N=8 → 0.50，N=16 → 0.67，N=27 → 0.90），而 `min`/`max` 本身已能精准区分好坏产物：

| 幻灯片 | N | min | max | 实际页数 | 是否在区间内 | 覆盖率 |
| --- | --- | --- | --- | --- | --- | --- |
| FreqFusion（参照物） | 26 | 20 | 30 | 21 | ✓ | 20/26 |
| EMCAD | 16 | 15 | 24 | 15 | ✓ | 高 |
| DDMA-YOLO | 25 | 20 | 30 | **13** | ✗ | 11/25 |
| CARAFE | 11 | 13 | 19 | **12** | ✗ | 6/11 |

注意 DDMA-YOLO 的密度高达 0.85（曾被误当作优质样本），但覆盖率仅 44%、页数低于下限 —— **它其实是不合格的**。这进一步说明密度是误导性指标，覆盖率才是本质。

**检查 6 降级为弱守卫**：原设计想用中文字符数强制「图注与结论不拆散」，但实测 CARAFE 各页中文字符为 `[76,128,153,64,129,47,28,52,31,74,123,58]`，最小值 28 —— 阈值 20 在真实语料上**拦不住任何东西**。故仅保留为「空页/几乎空页」守卫，不再宣称它能保证图注不孤立；图注与结论同页由 §8 第 5 步规划表的「叙事来源」列在生成阶段保证。

**页数计数的陷阱（实测证据，必须规避）**：幻灯片引擎在 `templates/presentation.html:818` 用 `document.querySelectorAll('.slide')` 定义「一页」，容器是 `<section class="slide" ...>`。若用正则 `class="slide[^"]*"` 计数，会误吞 `class="slide-title"` 与 `class="slide-subtitle"` —— 实测 `paper-slides/smooth-tail_learning.html` 因此把真实的 **14 页数成 30**（14 个 `slide-title` + 2 个 `slide-subtitle` 被计入）。

因此：
- 首选走 playwright 取真实 DOM（检查 3）。
- 仅当 playwright 不可用时启用正则兜底，且必须**同时**满足：限定容器标签 `<div|section>`，并对 class 做 token 精确匹配 `class="(?:[^"]*\s)?slide(?:\s[^"]*)?"`。**禁止**使用 `class="slide[^"]*"`。
- 兜底生效时在报告中标注 `page_count_source: "regex_fallback"`，提示该数字可信度较低。

输出：人类可读报告 + `--json` 结构化结果。成功退出码 0；playwright 缺失且正则兜底也不可用时退出码 2。

**报告须按博客章节分组**，逐节列出「引用图 / 已用图 / 缺失图」，便于一眼看出是否有某节被掏空（§1.2 根因五）。此为信息性输出，**不设额外门禁** —— 检查 1 的全局 100% 覆盖已在数学上蕴含各节 100% 覆盖。

### 5.3 C3 — `SKILL.md` 改造点

| 位置 | 改造 |
| --- | --- |
| frontmatter `description`（L3） | 删除「（无需 PDF）」，改为「复用 `assets/paper-imgs/` 已提取图表 + 按需通读原始 PDF 正文补充事实（不重新提图）」 |
| 项目约定表（L16-25） | 新增两行：「原始 PDF」「素材账本」；把「无需再跑 pdf_extractor」改为「不重新提取图片，但需读 PDF 正文」 |
| 铁律节（L42-45） | **整节重写**为「三层信息源与冲突裁决」（§4） |
| 工作流（L101-144） | 8 步 → 11 步（§8） |
| 分页规划建议表（L146-157） | 页数列改为动态公式引用（§6） |
| 注意事项（L159-168） | 新增两条：① 横长图（`aspect=wide`）独占整页或半页，不得塞进窄栏；② **表格数据以 `assets/paper-imgs/` 中的表格图片为准，不得采信 PDF 抽取出的单元格碎片文本** |
| 已知问题3（L184-188） | 改为「由 `verify_slides.py` 检查 2 与 5 自动拦截」 |

### 5.4 中间产物目录与发布安全（C1/C2 共用）

账本与 PDF 全文一律写入 **`.cache/blog-to-slides/<论文名>/`**，并需**在 `.gitignore` 追加 `.cache/`**（现有 `.gitignore` 已有 `# private` 段，追加即可）。

**为什么不能放 `assets/paper-imgs/`（设计过程中曾如此规划，已修正）**：

| 事实 | 依据 |
| --- | --- |
| `assets/paper-imgs/` 被站点首页直接引用 | `index.html` 中出现 `assets/paper-imgs/` 路径 |
| 整棵树会原样发布到 GitHub Pages | 仓库根存在 `.nojekyll`，无任何构建过滤 |
| 该目录当前已 287 MB | `du -sh assets/paper-imgs` 实测 |
| 全文体量 | 50 个可解析 PDF 字符数中位 3.9 万、最坏 11.6 万，59 篇累计约 2.5 MB 纯文本 |

把论文正文抽取结果放进已发布目录，等于**公开分发 59 篇论文全文**，其中含 Elsevier（如 DDMA-YOLO 的 `doi.org/10.1016/j.compag...`）、ICCV/CVPR 等有版权来源。这比作者现有「只发布图表切片」的做法风险显著更高，属不可接受的副作用。

**同时解决的另一问题**：README 告知用户「开始制作自己的内容前，请先清空 `pdf-papers/`、`paper-blogs/`、`paper-slides/`、`assets/paper-imgs/`、`assets/thumbnails/` 这 5 个目录」。若账本写进 `assets/paper-imgs/`，清理流程会连带删掉账本且不在文档说明内；写入 `.cache/` 则与既有清理契约完全解耦，`.cache/` 可随时整体删除、按需重建。

## 6. 页数预算公式

```
N        = blog_ref_count
图页下限 = ceil(N / 2)        # 允许每页最多 2 图（仅限 square/tall）
结构页   = 7                  # 首页1 + 概述1 + 引言2 + 总结2 + 结尾1（不含可选背景综述）
全局封顶 = 30

page_budget.min = 结构页 + 图页下限
page_budget.max = min(结构页 + 1 + N, 30)
```

`min` 与 `max` 的实测区分力（详见 §5.2）：FreqFusion(21 页, 区间 [20,30]) ✓、EMCAD(15 页, [15,24]) ✓ 通过；DDMA-YOLO(13 页, [20,30]) ✗、CARAFE(12 页, [13,19]) ✗ 拦下。

实例：

| 论文 | N | min | max | 现有页数 | 现有覆盖 | 现状判定 |
| --- | --- | --- | --- | --- | --- | --- |
| CARAFE | 11 | 13 | 19 | 12 | 6/11 | 双项不合格 |
| FreqFusion（参照物） | 26 | 20 | 30 | 21 | 20/26 | 页数合格，覆盖仍缺 6 |
| DDMA-YOLO | 25 | 20 | 30 | 13 | 11/25 | 双项不合格 |
| RSO-YOLO | 27 | 21 | 30 | 11 | 6/27 | 双项不合格 |
| Focaler-IoU（低 N 样本） | 3 | 9 | 11 | — | — | 低 N 论文页数天然少，min 仍适用 |

可选的「背景综述」页（来自笔记预备知识节，2~3 页）**占用 `max` 预算内的额度，不得额外追加**，否则会与检查 4（页数 ≤ max）冲突。若笔记预备知识确实很多、`max` 装不下，用 `--allow-extra-pages <n>` 显式上调 `max`，并**必须在收尾说明中报告上调值与理由**；禁止静默放宽。

**图集页规则**：当 N 大到触及封顶（如 RSO-YOLO 27 图），超出部分必须放入 grid 图集页（每页 4~6 张缩略图 + 简短图注），**仍计入 100% 覆盖**。这样「100% 覆盖」与「页数可控」不再数学冲突。

**图集页的排除项**：博客「可视化分析 / 定性结果」章节的图**不得**降级进图集页 —— 它们是组会汇报的核心视觉素材（CARAFE 被丢的 fig4、fig8、fig9 正属此类，见 §1.2 根因五），必须独占整页或半页。图集页只用于承接消融表、附加对比表等次要素材。

`aspect=wide` 的图（如框架图、宽对比表）不参与「每页 2 图」的紧凑排布，须独占整页或半页。CARAFE 实测：14 张图中 8 张为 `wide`（r 最高达 3.73，如 table2/table3 为 948×254）、6 张 `square`（多为 1400×1300 级的定性结果大图）、0 张 `tall` —— 若不区分形态一律塞进同一 `.figure-box`，宽表会被压得无法阅读，大方图会被缩成一团。

## 7. 异常处理矩阵

### 7.1 PDF 定位三级兜底

| 级 | 方法 | 覆盖 | `pdf_resolution` |
| --- | --- | --- | --- |
| 1 | `extraction_summary.json` 的 `pdf_path` 且文件存在 | 49/58 | `summary` |
| 2 | 按 `pdf_path` 的**文件名**在 `pdf-papers/**/*.pdf` 递归搜索；无 summary 时按博客 frontmatter `title` 归一化后模糊匹配（见下方匹配规则） | 9/9（已实测） | `filename_search` |
| 3 | `--pdf <路径>` 人工指定 | — | `manual` |
| 失败 | 全部落空 | — | `none` |

**级 2 匹配规则（必须用 top-1 + 间距，不可用扁平阈值）**

归一化：转小写 → 去掉开头年份前缀（`^(19|20)\d{2}[\s_-]*`）→ 去掉 `.pdf` → 只保留 `[a-z0-9]`。对全部候选算 `difflib.SequenceMatcher` 比率后：

```
接受条件： top1 ≥ 0.85  且  (top1 - top2) ≥ 0.15
```

实测依据（9 个兜底样本，`pdf-papers/` 共 63 个 PDF 作为干扰项）：

| 论文 | top1 | top2 | 间距 | top1 是否正确 |
| --- | --- | --- | --- | --- |
| DySample | 1.00 | 0.45 | 0.55 | ✓ |
| Dynamic-Head | 1.00 | 0.47 | 0.53 | ✓ |
| Mona | 0.99 | 0.50 | 0.49 | ✓ |
| Powerful-IoU | 1.00 | **0.69**（Wise-IoU） | 0.31 | ✓ |
| VarifocalNet | 0.95 | 0.56 | 0.39 | ✓ |
| YOLO-PEFT | 1.00 | 0.41 | 0.59 | ✓ |
| gcmd-yolo | 1.00 | **0.67**（cbp-yolo） | 0.33 | ✓ |
| psmf-yolo | 1.00 | **0.67**（cbp-yolo） | 0.33 | ✓ |
| FreqFusion | 0.91 | 0.41 | 0.50 | ✓ |

**为什么不能用扁平阈值**：若取阈值 0.62，Powerful-IoU / gcmd-yolo / psmf-yolo 会各自多命中一个同族论文（Wise-IoU、cbp-yolo），产生歧义。9 个样本的最小间距是 0.31、最低 top1 是 0.91，因此 `top1 ≥ 0.85 且间距 ≥ 0.15` 能全部正确命中且零误报。不满足接受条件时落到级 3，**不得取 top1 硬用**。

`pdf_resolution=none` 时：**降级为纯笔记模式**（等价于改造前行为），账本仍产出（caption 从博客图注取），且**必须在收尾时明确告知用户「未找到 PDF，本次未能补充事实层」**。禁止静默降级。

### 7.2 其他异常

| 情况 | 判定 | 处理 |
| --- | --- | --- |
| 扫描版 PDF | `pdf_text_chars < 3000` 且 `pdf_pages > 8` | **实测现有 63 个 PDF 中 0 个命中**，故不建独立降级分支（YAGNI）：账本照常记录 `pdf_text_chars`，脚本仅在命中时打印一行警告提示正文可能不可用，不做 OCR、不改流程 |
| 无 `extraction_summary.json` | 8 个目录 | `caption_source="none"`，靠博客图注 + PDF 正文推断图的用途；账本仍完整产出 |
| `extraction_summary.json` 相对磁盘单向缺失 | 实测 216/767 博客引用图不在 summary 中（如 Coordinate-Attention 漏 fig2/3/4） | 以磁盘为存在性权威（§5.1 第 3 步）；summary 只作元数据；若出现 summary 有而磁盘无的条目，进 `stale_summary_entries` 并提示、不阻断（实测当前全库为空） |
| 博客引用了磁盘上不存在的图 | 实测当前 0 处 | 记入 `broken_blog_refs` 并**报错退出**（笔记本身有断链，属上游数据问题，不得静默忽略） |
| `pymupdf` 缺失 | ImportError | 打印 `pip install pymupdf Pillow`（与现有脚本风格一致），退出码 2 |
| 博客不存在 | — | 直接报错退出（本技能输入前提） |
| `--allow-missing` 被使用 | — | 收尾说明必须列出豁免了哪张、为什么 |

## 8. 工作流（11 步）

1. 运行 `build_asset_ledger.py <名>` → 得账本、PDF 路径、页数预算。
2. Read `.cache/blog-to-slides/<名>/asset_ledger.md`，**逐行过一遍全部图片**（含 `unused_in_blog`）。
3. Read `.cache/blog-to-slides/<名>/paper_text.txt` 通读 PDF 正文（L2 事实层）。
4. Read `paper-blogs/<名>.md` 全文（L1 叙事层）。
5. **产出规划表**：`页码 | 主题 | 用哪张图 | 图的博客章节归属 | 事实来源(PDF页码) | 叙事来源(笔记章节)`。硬约束：每个 `in_blog=true` 的图必须落在某一行，且章节归属须与账本 `blog_sections` 一致 —— 这防止用方法节的图凑满总数、同时把可视化节掏空（§1.2 根因五）。
6. 按规划表写 HTML → `paper-slides/<名>.html`（图片用 `../assets/paper-imgs/<名>/xxx.png`）。
7. 运行 `verify_slides.py <名>` → **不通过则回到第 6 步修补，禁止跳过**。
8. 登记 `slides-manifest.json`。
9. 运行 `generate-thumbnails.py`。
10. 人工浏览复核。
11. 收尾说明：报告页数/用图数/覆盖率、`pdf_resolution`、任何降级或豁免。

第 5 步是本次改造的核心机制：**漏图的真实成因是边写边想**，模型线性生成 HTML 到后半程乏力就丢图。先产出规划表可堵死该路径。

## 9. 测试计划

| 类型 | 用例 | 断言 |
| --- | --- | --- |
| 账本正例 | CARAFE | `blog_ref_count=11`、`extracted_count=14`、`pdf_resolution="summary"`、`unused_in_blog=[fig6,fig7,table3]`、`stale_summary_entries=[]`、`broken_blog_refs=[]`、`page_budget={min:13,max:19}`（全部已实测，见 §13） |
| 兜底路径 | FreqFusion | `pdf_resolution="filename_search"`（其 `pdf_path` 指向已不存在的 `D:\trae_projects\`） |
| 兜底路径 | Mona、DySample、VarifocalNet、YOLO-PEFT、gcmd-yolo、psmf-yolo、Dynamic-Head | 全部 `pdf_resolution="filename_search"` 且指向正确 PDF |
| **误报回归** | **Powerful-IoU** | **必须匹配 Powerful-IoU 的 PDF，不得匹配 Wise-IoU（比率 0.69 的同族干扰项）** |
| **误报回归** | **gcmd-yolo / psmf-yolo** | **不得匹配 cbp-yolo（比率 0.67 的同族干扰项）** |
| 无 summary | Mona | 不崩溃、`caption_source="none"`、账本字段完整 |
| **校验器负例** | **试点前的 CARAFE.html（12 页/6 图；试点后已不在工作区，取 `git show <试点前提交>:paper-slides/CARAFE.html`）** | **退出码 1，精确列出缺失的 fig1、fig4、fig8、fig9、table7** |
| 校验器正例 | 试点后的 CARAFE.html（19 页/11 图） | 退出码 0（已人工按六项检查实测通过，见 §13.3） |
| **页数计数回归** | **`smooth-tail_learning.html`** | **页数必须为 14，不得为 30（防 `slide-title`/`slide-subtitle` 被误计）** |
| 页数计数回归 | `Attention_Is_All_You_Need.html`(15)、`YOLO-Master_Presentation.html`(16) | 与容器标签计数一致 |
| 博客解析鲁棒性 | 全部 58 篇博客 | 账本构建不抛异常；767 处图片引用中允许 `blog_note`/`blog_caption` 为空但字段必须存在 |
| 章节归属 | 全部 58 篇博客 | 767 处图片引用 **100% 可归属到某个 H2/H3**（已实测，无未归属项） |
| **summary 单向缺失** | **Coordinate-Attention** | **账本必须含磁盘上而 summary 未列的 fig2/fig3/fig4（`extracted_count=13`、`blog_ref_count=11`），且 `stale_summary_entries=[]`（实测无幽灵条目）** |
| summary 缺失全量 | 有博客的 58 个目录 | 账本图片全集 == 磁盘实际文件集；`broken_blog_refs` 全库为空（实测 216 处孤儿全部在磁盘上，0 处真缺文件）；`stale_summary_entries` 全库为空 |
| 页数区间 | FreqFusion(21, [20,30])、EMCAD(15, [15,24]) / DDMA-YOLO(13, [20,30])、CARAFE(12, [13,19]) | 前两者检查 3、4 通过；后两者被拦下 |
| 低 N 不误伤 | Focaler-IoU（N=3，区间 [9,11]） | 页数天然少但 min 仍适用；**不得因密度低而判不合格**（密度门禁已删除，见 §5.2） |
| DOM 机制 | CARAFE.html | playwright 在 `file://` 下取到 `pages=12, imgs=6, loaded=6, failed=[]`（已实测通过，验证 C2 机制可行） |
| **列感知抽取** | **CARAFE 第 5 页** | **输出含连贯正文（如 `UperNet is a strong baseline for semantic segmentation`），且不得出现 `sort=True` 那种左右栏混排到同一行的文本** |
| 通读成本 | 50 个可解析 PDF | 字符数中位 ≈3.9 万、最坏 ≈11.6 万（约 1.2 万 / 3.5 万 token），确认全文通读成本可接受 |
| 端到端 | CARAFE 重生成 | 页数 ≥13、用图 =11、门禁通过、缩略图正常 |

现有坏产物即现成的失败测试用例，无需另造夹具。

## 10. 验收标准

- [ ] `build_asset_ledger.py` 对**有对应博客的 58 个目录**全部不崩溃，PDF 定位成功率 **58/58**（49 走级 1 + 9 走级 2，级 2 的 9 例已实测全部 top-1 正确）。第 59 个图片目录 `YOLOv5s-Mid-Tillage-Sugarcane` 既无博客也无幻灯片，技能不适用，脚本按设计报错退出。
- [ ] `verify_slides.py` 对现有 `paper-slides/CARAFE.html` 报出精确的 5 张缺失图。
- [ ] CARAFE 重生成后：博客引用 11 张图 100% 出现，页数 ≥13，门禁退出码 0。
- [ ] CARAFE「可视化分析」节的 4 张图（fig5、fig4、fig8、fig9）全部保留且各占整页或半页，**未被降级进图集页**（直接针对 §1.2 根因五）。
- [ ] `verify_slides.py` 对 `smooth-tail_learning.html` 报出 14 页而非 30 页。
- [ ] 账本图片全集在有博客的 58 个目录上均等于磁盘实际文件集；Coordinate-Attention 的 fig2/fig3/fig4 入账（`extracted_count=13`），`stale_summary_entries` 全库为空。
- [ ] CARAFE 重生成后页数落在 `[13, 19]` 区间（现状 12），且「可视化分析」节 4 图齐全。
- [ ] `SKILL.md` 不再含「笔记是唯一信息源」铁律与「无需 PDF」表述。
- [ ] `.gitignore` 含 `.cache/`；`git status` 确认账本与 `paper_text.txt` **未被跟踪**，`assets/paper-imgs/` 下**没有新增任何非图片文件**（发布安全，§5.4）。
- [ ] 人工浏览确认 CARAFE 新幻灯片观感不劣于 FreqFusion。

## 11. 方案降级开关

若不接受完整方案 C，可按下表缩减（C ⊃ B ⊃ A）：

| 方案 | 含 C1 账本 | 含 C2 门禁 | SKILL.md 改造 | 能否保证 G1 |
| --- | --- | --- | --- | --- |
| A | ✗ | ✗ | ✓ | ✗（仅改善，无机械保证） |
| B | ✓ | ✗ | ✓ | ✗（有清单无拦截） |
| **C（推荐）** | ✓ | ✓ | ✓ | ✓ |

推荐 C 的理由：用户已选定「博客引用图 100% 覆盖」这一**硬不变量**，而硬不变量必须由门禁保证。方案 A 所代表的「靠提示词自觉」正是产出当前 48% 丢图率的原因。

## 12. 未决问题

1. ~~`paper_text.txt` 与 `asset_ledger.*` 是否纳入 git？~~ **已解决**（§5.4）：一律写入 gitignore 的 `.cache/blog-to-slides/<名>/`，不入库、不发布，可随时删除重建。
2. 试点通过后，存量 53 份的批量重生成是否立项、以何优先级排序（建议按丢图数降序：RSO-YOLO 21 → YOLOv12n-RCL-Sunflower 17 → …）。
3. 门禁是否也回填到 `html-paper-slides`（当前列为非目标）。

## 13. 附录：CARAFE 干跑验证（设计可执行性证据）

在不写任何实现代码的前提下，用只读脚本按 §5.1 的规则手工合成了 CARAFE 的账本，验证 §8 工作流确实可执行。

### 13.1 账本干跑输出

```
pdf_resolution = summary      pdf_pages = 15
disk_imgs = 14                blog_refs = 11
stale_summary_entries = []    broken_blog_refs = []
unused_in_blog = [fig6.png, fig7.png, table3.png]
page_budget = { min: 13, max: 19 }
```

| 文件 | PDF页 | 尺寸 | 形态 | 博客引用 | 博客章节 |
| --- | --- | --- | --- | --- | --- |
| fig1.png | 1 | 617×559 | square | ✓ | 在主流架构中的集成 |
| fig2.png | 3 | 786×368 | wide | ✓ | 问题形式化与整体框架 |
| fig3.png | 5 | 681×335 | wide | ✓ | 在主流架构中的集成 |
| fig4.png | 7 | 1403×413 | wide | ✓ | 可视化分析 |
| fig5.png | 8 | 1464×466 | wide | ✓ | 可视化分析 |
| fig6.png | 12 | 1403×1411 | square | ✗ | —（附录图，可作图集页候选） |
| fig7.png | 13 | 1402×1525 | square | ✗ | —（附录图） |
| fig8.png | 14 | 1403×1331 | square | ✓ | 可视化分析 |
| fig9.png | 15 | 1214×1444 | square | ✓ | 可视化分析 |
| table2.png | 6 | 948×254 | wide | ✓ | 对比实验 |
| table3.png | 6 | 948×254 | wide | ✗ | —（Table 3，可作图集页候选） |
| table4.png | 6 | 658×317 | wide | ✓ | 对比实验 |
| table6.png | 7 | 388×283 | square | ✓ | 消融实验 |
| table7.png | 7 | 526×192 | wide | ✓ | 对比实验 |

每张博客引用图的解读句都带有可直接上幻灯片的硬数据，例：`table2` → 「bbox AP 36.9→38.1，Mask R-CNN 37.8→38.8」；`table6` → 「单独替换 PPM/FPN/FUSE 得 40.85/40.79/41.06（基线 40.44），三者全换 42.23」；`table7` → 「PSNR 19.58→20.71 dB（+1.1）、20.78→20.98 dB」。

### 13.2 由账本推出的 19 页规划表

| 页 | 主题 | 用图 | 形态处理 | 叙事来源 | 事实来源（PDF） |
| --- | --- | --- | --- | --- | --- |
| 1 | 首页 | — | — | 概况表 + frontmatter | p.1 标题/作者 |
| 2 | 核心贡献 | — | — | 文章贡献 | p.1 Abstract/Contributions |
| 3 | 现有上采样算子的不足 | — | — | 研究动机 | p.1-2 Introduction |
| 4 | 本文切入点：内容感知重组 | — | — | 研究动机 | p.2 |
| 5 | 问题形式化与整体框架 | **fig2** | wide，整页 | 方法 > 整体框架 | p.3 §3.1 |
| 6 | 通道压缩器 + 内容编码器 | — | 公式 HTML 排版 | 方法 H3 ×2 | p.3 §3.2 |
| 7 | 核归一化器 + 内容感知重组 | — | 公式 HTML 排版 | 方法 H3 ×2 | p.3-4 §3.2 |
| 8 | 与已有算子的关系 + 计算复杂度 | — | — | 方法 H3 ×2 | p.4-5 |
| 9 | 集成进 FPN | **fig3** | wide，整页 | 在主流架构中的集成 | p.5 |
| 10 | 自顶向下路径中的工作机制 | **fig1** | square，半页 + 解读 | 在主流架构中的集成 | p.1/p.5 |
| 11 | 实验设置 | — | — | 实验设置 | p.5 Datasets & Metrics |
| 12 | COCO test-dev 检测与实例分割 | **table2** | wide，整页 | 对比实验 | p.6 Table 1 |
| 13 | FPN vs mask head 分别接入 | **table4** | wide，整页 | 对比实验 | p.6 Table 4 |
| 14 | Places 图像修复 | **table7** | wide，整页 | 对比实验 | p.7 Table 7 |
| 15 | UperNet 组件消融 | **table6** | square，半页 + 解读 | 消融实验 | p.7 Table 6 |
| 16 | 可视化：重组过程 | **fig5** | wide，整页 | 可视化分析 | p.8 |
| 17 | 可视化：实例分割对比 | **fig4** | wide，整页 | 可视化分析 | p.7 |
| 18 | 可视化：语义分割 + 图像修复 | **fig8 + fig9** | 两张 square 并排 | 可视化分析 | p.14-15 |
| 19 | 总结与讨论 + 结尾 | — | — | 优点和创新点 | — |

**校验预期**：19 页 ∈ [13, 19] ✓；11/11 博客引用图 100% 覆盖 ✓；「可视化分析」节 4 图（fig5、fig4、fig8、fig9）全部保留且未被降级进图集页 ✓（直接修复 §1.2 根因五）；对比现状 12 页 / 6 图，页数 +58%、用图 +83%。

若需把「总结」与「结尾」拆成两页，可将第 8 页「与已有算子的关系」并入第 7 页，仍保持 19 页上限。

### 13.3 干跑结论与试点实测

设计可执行，无需返工。同时干跑暴露并已修正一处设计缺陷：原「图片密度 ≥0.6」门禁会误判本篇（19 页 / 11 图 → 0.58）以及所有低 N 论文，已在 §5.2 删除并给出实测证伪依据。

**试点已执行（2026-10-29）**：按 §13.2 规划表重写了 `paper-slides/CARAFE.html`（旧版 12 页/6 图在 git 历史中保留，可作 §9 校验器负例夹具），并按 §5.2 的六项检查在真实 DOM 上验证：

| 检查 | 结果 |
| --- | --- |
| 1 覆盖率 | **11/11 = 100%**（旧版 6/11 = 54%）；missing/extra/broken 均为空 |
| 2 图片真实加载 | 11 张 `naturalWidth > 0`，0 张失败 |
| 3/4 页数区间 | **19 ∈ [13, 19]** PASS（旧版 12 ∉ [13, 19]） |
| 5 路径前缀 | 11 个 `<img>` 全部为 `../assets/paper-imgs/CARAFE/`，无坏前缀 |
| 6 空页守卫 | 各页中文字符 min = 56 ≥ 20，无违规 |
| 分节覆盖 | 可视化分析 4/4、对比实验 3/3、在主流架构中的集成 2/2、其余各节 1/1，**无节被掏空** |
| 形态排版 | 11 张图显示宽高比与原图一致（误差 ≤0.01），wide 图未被压窄 |
| 溢出 | 1280×720 下 19 页全部无溢出，最紧页（第 13 页）仍有 68px 余量 |

前后对比：页数 12 → 19（+58%）、用图 6 → 11（+83%）、行数 343 → 538、密度 0.50 → 0.58。新增内容含：问题形式化两公式、四子模块分述、与动态滤波/空间注意力/STN/可变形卷积（24× 计算量）的对比、FLOPs 公式、UperNet 三组件与修复 U-Net 集成细节、完整实验设置、Table 2/3/8/9/10 全部数字、以及被旧版丢弃的 fig1/fig4/fig8/fig9/table7 五张图。

**未执行的收尾步骤（需用户决定）**：`generate-thumbnails.py` 会遍历全部 53 份 HTML 重截缩略图，副作用过大，试点未运行；CARAFE 封面视觉基本未变，现有缩略图仍可用。

## 14. 实施状态（2026-10-29）

方案 C 已实施完毕，测试全绿：

| 交付物 | 状态 | 测试证据 |
| --- | --- | --- |
| `scripts/build_asset_ledger.py` | 已实现 | 58/58 有博客目录不崩溃；resolution = summary 49 + filename_search 9；`broken_blog_refs` 全库为空 |
| `scripts/verify_slides.py` | 已实现 | 正例（新 CARAFE）exit 0；负例（git 中的试点前版本，`--html` 指定）exit 1 且精确列出 fig1/fig4/fig8/fig9/table7 与页数 12<13 |
| `SKILL.md` | 已重写 | 铁律改三层信息源；工作流 11 步含门禁；分页改动态公式；新增已知问题 4（丢图顽疾）与 5（双栏抽取错乱） |
| `.gitignore` | 已追加 `.cache/*` | `git status` 不再显示 `.cache/` |
| `paper-slides/CARAFE.html` | 试点重生成 | 见 §13.3 |
| 页数正则回归 | 通过 | smooth-tail_learning=14（naive 会得 30）、Attention=15（naive 16）、YOLO-Master=16（naive 17）、CARAFE=19 |

**勘误记录**（设计过程中自我推翻的结论，保留以供复核）：
1. 「图片密度 ≥0.6 门禁」—— 被低 N 论文证伪，已删除（§5.2）。
2. 「summary 与磁盘双向漂移 / table8、table9 幽灵条目」—— 源自一次被截断的目录打印，实为单向缺失，已更正（§5.1）。
3. 「PDF 定位 59/59」—— 第 59 个图片目录无博客、技能不适用，应为 58/58（§7.1、§10）。
