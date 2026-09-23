# paper-blogs 低质量笔记重生成清单

> 生成日期：2026-09-23。审查口径：57 篇笔记全量跑 `check_note.py` 门禁（几乎全过）+ 图片资产逐篇对账 + 结构/契约审计 + 重点篇目人工通读。
> 门禁盲区（check_note.py 不报）：死链图、H2/H3 层级错乱、生成残留元数据、贡献节放图、提取素材未用。
> 验收标准统一为 lzk-paper-reading §6 质量清单 + 本文件各篇「修复要点」，另加：无死链图、无裸图、贡献节无图、正文无生成残留。

## 重生成范围与源 PDF 对照（A + B 共 11 篇，整篇重生成并替换旧文件）

### A 档 · 强烈建议重生成（6 篇，硬伤）

| # | 笔记 | 源 PDF（pdf-papers/Improve YOLO12/ 下） | 修复要点 |
| --- | --- | --- | --- |
| A1 | `paper-blogs/Ratoon-Sugarcane-YOLOv5s.md` | `YOLO_Sugarcane_Detection_and_Counting/2024 基于无人机RGB图像与改进YOLO+v5s的宿根蔗缺苗定位方法.pdf` | ①骨架塌陷：「实验结果」被写成 H3 且与「实验设置」同级，全篇仅 4 个 H2，须恢复五节骨架；②全篇 0 公式（iw、P2、DyHead、椭圆 DBSCAN 聚类全部没形式化）；③主对比表未提取（旧文自曝「原表为图片，此处描述关键数据」），消融用手写 Markdown 表顶替；④13/22 张提取图未用；⑤文末残留「字数统计/图片目录/文件路径」生成元数据；⑥实验节写局限性/未来工作（违反零负面，需删除或移入标注增补节）；⑦2870 字偏短（标准档 3200-4800） |
| A2 | `paper-blogs/cbp-yolo.md` | `YOLO_Crop_Detection_and_Counting/2026 基于CBP-YOLO的玉米田间草地贪夜蛾侵染痕迹检测与试验.pdf` | 55 张提取图只用 2 张且是 `page6_img7.jpeg` 类分页裁剪、alt 为空；fig1–9 精修图全部弃用；全文仅 2 图，主对比/消融结果靠文字描述数字；方法节 1072 字过薄 |
| A3 | `paper-blogs/gcmd-yolo.md` | `YOLO_Crop_Detection_and_Counting/2026 基于GCMD-YOLO的轻量化多尺度中药材检测方法.pdf` | 全文仅 1 张图（`page7_img11.jpeg` 空 alt 分页裁剪），28 张提取素材 27 张未用；「混淆试验/可视化分析/泛化能力验证/边缘部署」全为纯文字，「可视化分析」无任何可视化图；5324 字长文配 1 图；无语义收束句 |
| A4 | `paper-blogs/psmf-yolo.md` | `YOLO_Crop_Detection_and_Counting/2026 基于PSMF-YOLO的无人机遥感图像枇杷花蕾小目标检测方法.pdf` | 3 张图全为空 alt 分页裁剪，43 张提取素材 40 张未用；对比实验无表图；非标准「讨论」H2 通篇缺点与局限且未标注「此节为偏离语料的增补」（违反 §7，默认零负面） |
| A5 | `paper-blogs/YOLOv12n-RCL-Sunflower.md` | `YOLO_Crop_Detection_and_Counting/2026_基于无人机影像与YOLOv12n-RCL的向日葵成熟期盘腐病危害程度检测_李京谦.pdf` | 30 张提取图只用 3 张（27 张未用，含 fig1 架构图、检测效果图）；5656 字配 3 图严重失衡；「模型性能对比」无主对比表图；缺「可视化分析」H3 |
| A6 | `paper-blogs/YOLO-Sugarcane.md` | `YOLO_Sugarcane_Detection_and_Counting/2025 YOLO—Sugarcane_用于快速检测复杂背景下甘蔗植株的轻量级神经网络_张志鹏.pdf` | fig5/fig6 死链（从未提取到，需重跑 pdf_extractor 补提）；「主对比实验」无表图、只有一段复述结论（与贡献节末句几乎重复）；方法节 873 字、全文 2432 字双过薄；实验设置提到 YOLOv3/v4 对比却无对应图表 |

### B 档 · 建议重生成或重点补图（5 篇）

| # | 笔记 | 源 PDF | 修复要点 |
| --- | --- | --- | --- |
| B1 | `paper-blogs/YOLO-GESCW.md` | `YOLO_Crop_Detection_and_Counting/2026_基于YOLO-GESCW的盛花期红花轻量化检测方法.pdf` | 20 张提取图仅用 4 张（16 张未用）；无架构总览图、无定性检测效果图；5809 字配 4 图失衡；方法节 2702 字超 2500 上限 |
| B2 | `paper-blogs/DySample.md` | `UpSample Modules/2023 Dysample Learning_to_Upsample_by_Learning_to_Sample.pdf` | 贡献节内放图（§3.2 禁止）；同一张 `dysample_fig2` 被两个小节复用充当不同内容；「定量对比」无主表图；实验节仅 534 字过薄；文末增补节致门禁 FAIL（§7 与门禁冲突：重生成时把批判性内容移出正文或并入注记，保证优点节为末节） |
| B3 | `paper-blogs/Mona.md` | `- Lora and PEFT/2025 5gt100_Breaking_Performance_Shackles_of_Full_Fine-Tuning_on_Visual_Recognition_Tasks.pdf` | 6 张图无解读、alt 全是占位 `image`；贡献节内放图；方法节 967 字过薄（有公式但解释文字量不足） |
| B4 | `paper-blogs/Conv2Former.md` | `Attn Modules/2024 Conv2Former A Simple Transformer-Style ConvNet for Visual Recognition.pdf` | 12/17 张提取图未用（table1、table10–13 等关键表缺失，定量仅 1 张表）；全文 2997 字偏短；1 张裸图 |
| B5 | `paper-blogs/RSO-YOLO.md` | `YOLO Family/2025 RSO-YOLO A Real-Time Detector for Small and Occluded.pdf` | fig14/15/16 死链（引用了不存在的图，需重跑 pdf_extractor 补提或改用已有切片）；7/24 张未用 |

## C 档 · 可修补、不必整篇重做（本批不整篇重生成，顺手修补或下批处理）

- `MAF-YOLO`：fig5 一张图顶两个小节不同图注复用；table1/3/4/5 未进笔记；公式「其中」解释仅 1 处
- `YOLO26`：tab3/4/8/10/11 等 6 张消融分析表未用；全篇无语义收束句
- `YOLO-Master / EMCAD / FADE / YOLOv10n-Wheat-Seedling / YOLO-FaceV2`：5–12 张提取素材未引用（Wheat-Seedling 的 assets 混着 page1–5 整页截图未裁剪），对照原 PDF 补关键表图
- `FreqFusion / CSFC / DDMA-YOLO / TPH-YOLO`：个别图缺图后解读（FreqFusion 多为图注前置，问题轻微）
- `EMA / Focaler-IoU / Inner-IoU / VarifocalNet`：图偏少或篇幅踩下限（Focaler-IoU 的「未获取」处理规范，源论文可视化少，低优先）
- `YOLO-PEFT`：增补节插在优点节之前（§7 要求追加在末尾）

## 其它遗留问题

1. `assets/paper-imgs/YOLOv5s-Mid-Tillage-Sugarcane/` 有完整图库但无对应笔记（PDF 为 `YOLO_Sugarcane_Detection_and_Counting/2025 无人机图像中耕期甘蔗植株检测计数方法——基于改进YOLOv5s_李尚平.pdf`），待确认是否补写。
2. `assets/paper-imgs/DynamicHead/` 遗留 11 张 `dyhead_*` 旧切片（笔记使用的是 fig/table 另一套），可清理。

## 流程约定（每篇）

1. 通读源 PDF → 素材切片表（内部）→ `new_note.py` 起稿 → 按 §3–§5 填写 → 图表落盘 `assets/paper-imgs/<论文名>/`（死链/缺失图用 `pdf_extractor.py` 补提）→ `check_note.py` 门禁 + 人工 §6 清单 + 本文件修复要点逐条核销。
2. 铁律：公式/数值/数据集/实验结论均可溯源原文，未获取即标「未获取」。
3. 全部 11 篇完成后：刷新 `blogs-manifest.json`，复跑门禁与链接检查，提交并推送远程。
