# 三个技能共用的论文素材工作流

适用于 Codex、TRAE、Qoder。所有命令均在项目根目录运行，Python 3.11+，依赖 `pymupdf Pillow playwright` 和 Playwright Chromium。

```bash
python -m pip install pymupdf Pillow playwright
python -m playwright install chromium
```

## 1. 唯一目录和清单

所有流程共用 `assets/paper-imgs/<论文ID>/`，规范清单是其中的 `asset_manifest.json`。不要再创建 `paper-slides/*_assets/`。HTML 图片路径为 `../assets/paper-imgs/<论文ID>/<文件名>`。

论文 ID 沿用已有目录名，新的论文使用稳定短名。同一 PDF 指纹已登记到其他 ID 时，工具会指出已有 ID；请复用。PDF 内容变化必须另设版本 ID，防止新旧图表混用。

`extraction_summary.json` 是只读的历史迁移输入，不再是活跃清单。规范清单包含 PDF 指纹、素材 ID、类型、图表编号、页码、PDF 点坐标 bbox、原文图注、文件指纹、尺寸和核验记录。历史孤立图片也会登记，缺文件的记录会保留为待处理项。

已有共享目录可用 `python scripts/paper_assets.py register --paper "my-paper" --pdf "pdf-papers/my-paper.pdf"` 登记，无需重新裁剪。旧 PPT 私有目录用下面的命令迁入共享库；同内容文件复用，同名不同内容文件另命名，原目录保留，指定 HTML 的旧版本备份到 `.cache/`：

```bash
python scripts/paper_assets.py import-legacy --paper "my-paper" --legacy-dir "paper-slides/my-paper_assets" --html "paper-slides/my-paper.html" --pdf "pdf-papers/my-paper.pdf"
```

仅处理素材时省略 `--html`。迁移不会自动标为已核验，后续仍按下列流程核对。

状态只允许：`pending`（缺失/定位失败）、`needs_review`（已有图待核验）、`verified`（对照原页核验通过）、`excluded`（明确排除且记录原因）。自动提取不会自动变成 `verified`。

## 2. 准备与逐页核对

以下例子中的论文 ID、PDF 路径、素材 ID 和坐标必须替换为实际值。

```bash
python scripts/paper_assets.py prepare --paper "my-paper" --pdf "pdf-papers/my-paper.pdf"
python scripts/paper_assets.py review-sheet --paper "my-paper"
```

打开命令输出的 `.cache/paper-assets/my-paper/review/index.html`。它显示**全部原页**及当前裁剪框、图片、图注和状态，包括没有检测到标题的页面。核对图表全集、中文/罗马数字/附录编号、跨页续表、子图、坐标轴、图例、表头和脚注。自动标题识别不是完整性证明。

重复 `prepare` 会复用文件指纹一致的已有图片，不产生 `_pageXXX` 重复文件；部分成功不会吞掉失败项。待处理项持续列在清单中。

## 3. 逐图补提、重提和排除

对已有素材指定页码和 bbox 补提，坐标单位为 PDF 点，顺序为 `x0 y0 x1 y1`，页码从 1 开始：

```bash
python scripts/paper_assets.py extract --paper "my-paper" --asset "table-i-p004" --page 4 --bbox 40 100 550 360
```

对标题检测完全漏掉的图表，指定新 ID、类型、图注和坐标：

```bash
python scripts/paper_assets.py extract --paper "my-paper" --asset "table-s1-p012" --kind table --caption "Table S1: Additional results" --page 12 --bbox 40 100 550 500
```

跨页续表分别使用不同的 ID / 页码；保留编号和原文图注以便关联。不要把第二页判作重复图片。已有自动定位项可用 `extract --asset ID --force` 重跑自动定位；指定 bbox 时直接按该框重提。

重提会将旧图片备份到 `.cache/paper-assets/<论文ID>/revisions/`，并重置其核验状态。禁止清空共享目录，旧 `--clean` 参数会被拒绝。

查看更新后的对照页，再逐项记录结果：

```bash
python scripts/paper_assets.py review --paper "my-paper" --asset "table-i-p004" --status verified --note "已对照第4页：表头、全部行列和脚注完整，无相邻正文污染"
python scripts/paper_assets.py review --paper "my-paper" --asset "figure-2-p005" --status excluded --note "核对原页后确认为正文引用，不是图注"
```

`excluded` 只能用于确认的重复素材、正文误检或非论文素材。不能为了省页数排除图表。坐标或来源不明的历史图片，先通过补提建立来源再核验；不批量宣称已核验。

## 4. 确认原文全集

全部原页看完，发现的漏项已经补登记，所有素材都已核验或明确排除后：

```bash
python scripts/paper_assets.py review-inventory --paper "my-paper" --note "逐页检查12页，正文与附录图表、续表均已登记，无未解决漏项"
python scripts/paper_assets.py check --paper "my-paper"
```

`check` 非零退出表示仍有未解决问题。文件内容改变、新增图片、PDF 指纹变化或核验记录失效都会阻止交付。对原文确实无图表的论文，也必须逐页核对并在说明中记录。

PDF 页面预览、修复备份、PDF 全文放在被 Git 忽略的 `.cache/`，不写入公开图片目录。

## 5. 三条产出路径

- PDF → 博客：`lzk-paper-reading` 复用上述图片和图注，运行自己的笔记检查，同时要求素材 `check` 通过。
- PDF → PPT：运行 `python scripts/build_asset_ledger.py "my-paper" --no-blog`，按全部非排除素材规划。
- 博客 → PPT：运行 `python scripts/build_asset_ledger.py "my-paper"`，把博客叙事与共享素材结合；博客未引用的图表也必须安排在主讲或附录中。

两条 PPT 流程统一执行：

```bash
python scripts/verify_slides.py "my-paper" --html "paper-slides/my-paper.html" --json
```

验证器在 1280×720 和 1920×1080 下通过键盘逐页激活，检查真实 `<img>`、资源路径、加载、可见性、裁切、最小显示尺寸、比例与外部依赖。完整图表必须在某一页可读呈现；局部放大不能替代原图。`data-asset-id` 用来辅助维护，覆盖率仍以实际文件和显示结果为准。

局部放大或导航缩略图使用 `data-asset-detail="true"`，这些辅助图片不计入完整图表覆盖率；同一素材仍须有未标记 detail 的完整呈现。

退出码：`0` 通过；`1` 素材或页面失败；`2` 输入/浏览器环境不可用，状态为 `unverified`。禁止通过注释、隐藏图、页外图或 `--allow-missing` 绕过覆盖检查。失败或未验证不得登记成品、生成交付缩略图。

该检查提供机械质量门禁，不能自动证明表格小字均可读或论文结论正确。交付前仍需逐页视觉复核，密集表格增加放大页。

## 6. 维护

公共实现位于 `scripts/paper_assets.py`、`scripts/pdf_regions.py`、`scripts/build_asset_ledger.py`、`scripts/verify_slides.py`；模板源文件为 `templates/presentation.html`。三个平台的原命令入口保留，转发到同一实现。

修改 `.agents/skills/*/SKILL.md` 或公共模板后运行：

```bash
python scripts/sync_skill_resources.py
python scripts/sync_skill_resources.py --check
python -m unittest discover -s tests -v
```

同步器只分发技能说明、公共脚本入口和模板，不修改各技能的笔记脚本及语料资料。
