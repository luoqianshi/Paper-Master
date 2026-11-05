# HTML 格式 PPT 全量核查报告

> 核查对象：`paper-slides/*.html` 共 **62 份** · 核查日期 2026-11-04 · 依据 [`docs/html-ppt-quality-standard.md`](./html-ppt-quality-standard.md) v1.1

---

## 1. 摘要

- **评级结果**：优秀 **31** 份 / 合格 **24** 份 / 待优化 **7** 份，合计 62 份。
- **待优化清单**：共 **77** 条，其中 **P0 4** / P1 71 / P2 2。P0 全部是「正文/图注对比度低于 3:1，投影下难以辨认」，直接损害内容理解，应最先处理。
- **图片可用性**：静态扫描 **542** 处 `<img src>`，磁盘缺失 **0** 处；Playwright 62 份 × 6 档渲染确认失效图 **0** 处。探索阶段怀疑的 `Conv2Former / psmf-yolo / YOLOv12n-RCL-Sunflower / DySample` 图片路径问题**全部驳回**（详见 §8）。
- **演示基本盘**：62 份键盘翻页均可用、逐页可见性正常、零外部 CDN/字体依赖；主屏（1920×1080 / 1366×768 / 1280×720）溢出仅 7 页次、集中在 2 份文件，经截图复核未裁切关键内容。
- **全库共性短板**：62 份均无 `@media print`（打印/导出 PDF 仅 1~3 页可见）、无 16:9 固定画布与缩放兜底、实验表格全为位图、无 References 章节。这些按标准 §3.3 标为 `G` 全局项，不参与逐份评分，统一在 §6 给出全库级改进建议。
- **本轮性质**：只读核查。**未修改任何现有 PPT**，也未改动 SKILL.md、manifest、index.html、README。

### 最需要优先处理的 4 项（P0）

1. **CityGrounding.html · 第 3、6、7、8、9 页 · 首见「从室内走向城市：任务没变，难度变了」**（T3.3）：正文/小字对比度不足 39 处，最低 2.97:1（投影下难以辨认）
1. **Dialogue_Director.html · 第 6、10 页 · 首见「相关工作」**（T3.3）：正文/小字对比度不足 60 处，最低 1.61:1（投影下难以辨认）
1. **YOLO26_Unified_Real-Time_Vision.html · 第 6、7、15 页 · 首见「YOLO26 架构设计」**（T3.3）：正文/小字对比度不足 33 处，最低 2.85:1（投影下难以辨认）
1. **smooth-tail_learning.html · 第 1、4、5、8 页 · 首见「Boosting Long-tailed Object Detection via Step-wise Learning」**（T3.3）：正文/小字对比度不足 21 处，最低 2.68:1（投影下难以辨认）

---

## 2. 核查范围与方法

| 项 | 说明 |
|---|---|
| 范围 | `paper-slides/*.html` 62 份本体；manifest / 缩略图 / 站点引用 / 孤立素材只作外围附注（§7），不参与评级 |
| 标准 | 6 大维度 41 条检查项（C 内容 25 / L 版式 18 / T 可读 17 / V 一致 12 / I 交互 14 / A 适配 14），含 7 条红线 |
| 静态 | `scripts/audit_slides.py --static`：页数（沿用 `verify_slides.py` 的 `PAGE_RE`）、图片存在性、CSS 变量、@media、外链、翻页状态机、页码、章节归一化 |
| 渲染 | `scripts/audit_render.py`：Playwright + Chromium，`file://` 单文件打开；6 档 viewport = 1920×1080 / 1366×768 / 1280×720 / 1024×768 / 900×700 / 768×1024 |
| 渲染完成 | 62/62 份成功，0 份报错；逐档采集 DOM 页数、溢出、图片 `naturalWidth`、计算字号、WCAG 对比度、键盘翻页、print 媒体可见页数 |
| 人工复核 | `.cache/slides-audit/human_review.json`：源码核对 + 1280×720 关键页截图，逐条确认/驳回疑似项 |
| 事实层边界 | 实验数值与 `pdf-papers/` 原文的一致性**未逐份核验**，按标准不作推断 |

### 2.1 阈值校准（v1.1，公开修订）

标准 §3.3 把 6 个 `G` 全局项从逐份评分剔除后，六维得分的分母变小，量表含义变为「排除全库共性缺陷后的相对质量」。首次全量实测 62 份得分落在 **91.5~99.0（中位数 97.9）**，v1.0 的绝对阈值 85 / 70 **从未被触发**，全部文件挤在同一档。故按量表实际分布把分档阈值校准为**优秀 ≥97 / 合格 93~97 / 待优化 <93（或命中红线）**，并把优秀档 C/L/T/A 四维门槛由 80 提到 85。**权重、检查项、红线清单、G 项剔除规则均未改动**；校准前分布为「优秀 32 / 合格 30 / 待优化 0、P0 0 条」，校准后为「优秀 31 / 合格 24 / 待优化 7、P0 4 条」。校准依据是量表变化与三档区分度，不是为了让某档凑数。

### 2.2 等级判定口径

红线一票否决（`R-F1` 失效图 / `R-F2` 翻页失效 / `R-F3` 溢出裁切 / `R-S1` 叙事断裂 / `R-S2` 页码误导 / `R-S3` 文字不可读 / `R-S4` 离线依赖失效）优先于分数；其余按六维加权总分分档。所有红线均须「静态疑似 → 渲染确认 → 人工复核」三级证据齐备，静态疑似不直接否决。

---

## 3. 62 份评级总表

按「优秀 → 合格 → 待优化」分组、组内文件名升序。`关键扣分点` 用标准条款编号引用；`G` 全局项不出现在本表（统一见 §6）。

| 序号 | 文件 | 模板 | 页数(DOM/正则) | C | L | T | V | I | A | 总分 | 等级 | 命中红线 | 关键扣分点 | 校验状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ASF-YOLO.html | B | 13/13 | 95 | 100 | 100 | 100 | 92 | 100 | 97.7 | **优秀** | — | C1.7,I5.3 | 已验证 |
| 2 | ASFF.html | B | 12/12 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 3 | Attention_Is_All_You_Need.html | A | 15/15 | 95 | 100 | 92 | 100 | 99 | 100 | 97.3 | **优秀** | — | C1.4,I5.5,T3.3 | 已验证 |
| 4 | CSFC.html | B | 13/13 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 5 | Coordinate-Attention.html | B | 12/12 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 6 | EMA.html | B | 11/11 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 7 | EMCAD.html | B | 15/15 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 8 | Efficient-Deformable-ConvNets.html | B | 19/19 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 9 | FBRT-YOLO.html | B | 11/11 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 10 | FMA-YOLOv12.html | B | 11/11 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 11 | Focaler-IoU.html | B | 12/12 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 12 | Generalized-Focal-Loss.html | B | 12/12 | 95 | 100 | 100 | 100 | 92 | 100 | 97.7 | **优秀** | — | C1.7,I5.3 | 已验证 |
| 13 | Inner-IoU.html | B | 13/13 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 14 | Mona.html | B | 14/14 | 100 | 100 | 92 | 100 | 92 | 100 | 97.7 | **优秀** | — | I5.3,T3.3 | 已验证 |
| 15 | NWD.html | B | 13/13 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 16 | Pinwheel-Conv-Loss.html | B | 13/13 | 100 | 100 | 92 | 100 | 92 | 100 | 97.7 | **优秀** | — | I5.3,T3.3 | 已验证 |
| 17 | RSO-YOLO.html | B | 11/11 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 18 | Ratoon-Sugarcane-YOLOv5s.html | B | 15/15 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 19 | VarifocalNet.html | B | 11/11 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 20 | Wise-IoU.html | B | 10/10 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 21 | YOLO-FaceV2.html | B | 14/14 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 22 | YOLO-GESCW.html | B | 11/11 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 23 | YOLO-SFEP.html | B | 10/10 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 24 | YOLO-SSAR.html | B | 10/10 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 25 | YOLO-Sugarcane.html | B | 9/9 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 26 | YOLO11n-EWL-Sugarcane-Bud.html | B | 9/9 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 27 | YOLOv12-DMFA-Catenary.html | B | 11/11 | 100 | 90 | 100 | 100 | 92 | 100 | 97.2 | **优秀** | — | I5.3,L2.4 | 已验证 |
| 28 | YOLOv12n-RCL-Sunflower.html | B | 9/9 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 29 | YOLOv12n-VD-Furnace.html | B | 12/12 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 30 | YOLOv13.html | B | 15/15 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 31 | YOLOv7-Sugarcane-Seedling.html | B | 12/12 | 100 | 100 | 100 | 100 | 92 | 100 | 99.0 | **优秀** | — | I5.3 | 已验证 |
| 32 | CARAFE.html | B | 19/19 | 100 | 100 | 100 | 100 | 92 | 92 | 97.9 | **合格** | — | A6.2,I5.3 | 已验证 |
| 33 | Conv2Former.html | B | 23/23 | 100 | 100 | 100 | 100 | 92 | 92 | 97.9 | **合格** | — | A6.2,I5.3 | 已验证 |
| 34 | DDMA-YOLO.html | B | 30/30 | 100 | 100 | 100 | 100 | 92 | 92 | 97.9 | **合格** | — | A6.2,I5.3 | 已验证 |
| 35 | DFR-SN-YOLO.html | B | 22/22 | 100 | 100 | 100 | 100 | 92 | 92 | 97.9 | **合格** | — | A6.2,I5.3 | 已验证 |
| 36 | DilateFormer.html | B | 11/11 | 100 | 90 | 92 | 100 | 92 | 100 | 95.9 | **合格** | — | I5.3,L2.4,T3.3 | 已验证 |
| 37 | DySample_Learning_to_Upsample.html | B | 22/22 | 100 | 100 | 100 | 100 | 92 | 92 | 97.9 | **合格** | — | A6.2,I5.3 | 已验证 |
| 38 | Dynamic-Head.html | B | 21/21 | 100 | 100 | 100 | 100 | 92 | 92 | 97.9 | **合格** | — | A6.2,I5.3 | 已验证 |
| 39 | FADE.html | B | 19/19 | 95 | 100 | 100 | 100 | 92 | 92 | 96.7 | **合格** | — | A6.2,C1.7,I5.3 | 已验证 |
| 40 | FreqFusion.html | A | 21/21 | 100 | 100 | 92 | 100 | 92 | 92 | 96.5 | **合格** | — | A6.2,I5.4,I5.5,T3.3 | 已验证 |
| 41 | MAF-YOLO.html | B | 17/17 | 100 | 100 | 100 | 100 | 92 | 92 | 97.9 | **合格** | — | A6.2,I5.3 | 已验证 |
| 42 | MNBS-YOLOv12.html | B | 11/11 | 100 | 100 | 100 | 100 | 92 | 92 | 97.9 | **合格** | — | A6.2,I5.3 | 已验证 |
| 43 | ParameterNet.html | B | 10/10 | 100 | 100 | 92 | 100 | 92 | 92 | 96.6 | **合格** | — | A6.2,I5.3,T3.3 | 已验证 |
| 44 | Powerful-IoU.html | B | 21/21 | 100 | 100 | 100 | 100 | 92 | 92 | 97.9 | **合格** | — | A6.2,I5.3 | 已验证 |
| 45 | SimAM.html | B | 18/18 | 100 | 100 | 100 | 100 | 92 | 92 | 97.9 | **合格** | — | A6.2,I5.3 | 已验证 |
| 46 | TPH-YOLO.html | B | 14/14 | 100 | 100 | 92 | 100 | 92 | 92 | 96.6 | **合格** | — | A6.2,I5.3,T3.3 | 已验证 |
| 47 | YOLO-PEFT.html | A | 21/21 | 95 | 100 | 92 | 100 | 99 | 92 | 96.3 | **合格** | — | A6.2,C1.4,I5.5,T3.3 | 已验证 |
| 48 | YOLOv10n-Wheat-Seedling.html | B | 13/13 | 100 | 100 | 100 | 100 | 92 | 92 | 97.9 | **合格** | — | A6.2,I5.3 | 已验证 |
| 49 | YOLOv12-Safflower.html | B | 12/12 | 100 | 100 | 100 | 100 | 92 | 92 | 97.9 | **合格** | — | A6.2,I5.3 | 已验证 |
| 50 | YOLOv12-Water-Debris.html | B | 14/14 | 100 | 100 | 100 | 100 | 92 | 92 | 97.9 | **合格** | — | A6.2,I5.3 | 已验证 |
| 51 | YOLOv12_Attention-Centric.html | B | 21/21 | 95 | 100 | 92 | 100 | 92 | 92 | 95.4 | **合格** | — | A6.2,C1.4,I5.3,T3.3 | 已验证 |
| 52 | YOLOv12n-PCB.html | B | 16/16 | 100 | 100 | 100 | 100 | 92 | 92 | 97.9 | **合格** | — | A6.2,I5.3 | 已验证 |
| 53 | cbp-yolo.html | B | 19/19 | 100 | 100 | 100 | 100 | 92 | 92 | 97.9 | **合格** | — | A6.2,I5.3 | 已验证 |
| 54 | gcmd-yolo.html | B | 22/22 | 100 | 100 | 100 | 100 | 92 | 92 | 97.9 | **合格** | — | A6.2,I5.3 | 已验证 |
| 55 | psmf-yolo.html | B | 20/20 | 100 | 100 | 100 | 100 | 92 | 92 | 97.9 | **合格** | — | A6.2,I5.3 | 已验证 |
| 56 | CityGrounding.html | B | 22/22 | 100 | 90 | 78 | 100 | 92 | 92 | 92.3 | **待优化** | R-S3 | A6.2,I5.3,L2.3,T3.1,T3.3 | 已验证 |
| 57 | DETRs_Beat_YOLOs_on_Real-time_Object_Detection.html | A | 15/15 | 100 | 90 | 92 | 70 | 99 | 92 | 92.1 | **待优化** | — | A6.2,I5.5,L2.2,T3.3,V4.1 | 已验证 |
| 58 | Dialogue_Director.html | B | 19/19 | 95 | 100 | 85 | 70 | 100 | 92 | 91.5 | **待优化** | R-S3 | A6.2,C1.4,T3.3,V4.1 | 已验证 |
| 59 | GrapickNet.html | A | 22/22 | 95 | 90 | 100 | 70 | 100 | 92 | 92.3 | **待优化** | — | A6.2,C1.4,L2.4,V4.1 | 已验证 |
| 60 | YOLO-Master.html | A | 22/22 | 95 | 90 | 100 | 70 | 100 | 92 | 92.3 | **待优化** | — | A6.2,C1.4,L2.4,V4.1 | 已验证 |
| 61 | YOLO26_Unified_Real-Time_Vision.html | A | 21/21 | 95 | 90 | 85 | 100 | 92 | 92 | 92.2 | **待优化** | R-S3 | A6.2,C1.4,I5.4,I5.5,L2.4,T3.3 | 已验证 |
| 62 | smooth-tail_learning.html | A | 14/14 | 95 | 100 | 85 | 100 | 99 | 92 | 95.0 | **待优化** | R-S3 | A6.2,C1.4,I5.5,T3.3 | 已验证 |

**等级分布**：优秀 31 / 合格 24 / 待优化 7。

> `I5.3`（B 类整页点击误触）与 `I5.5`（A 类显式控制器）属模板级共性：仍逐份计入 I 维扣分，所以多数文件的「关键扣分点」里会出现它们；但在 §5 清单中合并为 1 条模板级建议，不重复 54 次。

### 3.1 文件名升序索引（便于检索）

| 文件 | 等级 | 总分 | 文件 | 等级 | 总分 |
|---|---|---|---|---|---|
| ASF-YOLO.html | 优秀 | 97.7 | ASFF.html | 优秀 | 99.0 |
| Attention_Is_All_You_Need.html | 优秀 | 97.3 | CARAFE.html | 合格 | 97.9 |
| cbp-yolo.html | 合格 | 97.9 | CityGrounding.html | 待优化 | 92.3 |
| Conv2Former.html | 合格 | 97.9 | Coordinate-Attention.html | 优秀 | 99.0 |
| CSFC.html | 优秀 | 99.0 | DDMA-YOLO.html | 合格 | 97.9 |
| DETRs_Beat_YOLOs_on_Real-time_Object_Detection.html | 待优化 | 92.1 | DFR-SN-YOLO.html | 合格 | 97.9 |
| Dialogue_Director.html | 待优化 | 91.5 | DilateFormer.html | 合格 | 95.9 |
| Dynamic-Head.html | 合格 | 97.9 | DySample_Learning_to_Upsample.html | 合格 | 97.9 |
| Efficient-Deformable-ConvNets.html | 优秀 | 99.0 | EMA.html | 优秀 | 99.0 |
| EMCAD.html | 优秀 | 99.0 | FADE.html | 合格 | 96.7 |
| FBRT-YOLO.html | 优秀 | 99.0 | FMA-YOLOv12.html | 优秀 | 99.0 |
| Focaler-IoU.html | 优秀 | 99.0 | FreqFusion.html | 合格 | 96.5 |
| gcmd-yolo.html | 合格 | 97.9 | Generalized-Focal-Loss.html | 优秀 | 97.7 |
| GrapickNet.html | 待优化 | 92.3 | Inner-IoU.html | 优秀 | 99.0 |
| MAF-YOLO.html | 合格 | 97.9 | MNBS-YOLOv12.html | 合格 | 97.9 |
| Mona.html | 优秀 | 97.7 | NWD.html | 优秀 | 99.0 |
| ParameterNet.html | 合格 | 96.6 | Pinwheel-Conv-Loss.html | 优秀 | 97.7 |
| Powerful-IoU.html | 合格 | 97.9 | psmf-yolo.html | 合格 | 97.9 |
| Ratoon-Sugarcane-YOLOv5s.html | 优秀 | 99.0 | RSO-YOLO.html | 优秀 | 99.0 |
| SimAM.html | 合格 | 97.9 | smooth-tail_learning.html | 待优化 | 95.0 |
| TPH-YOLO.html | 合格 | 96.6 | VarifocalNet.html | 优秀 | 99.0 |
| Wise-IoU.html | 优秀 | 99.0 | YOLO-FaceV2.html | 优秀 | 99.0 |
| YOLO-GESCW.html | 优秀 | 99.0 | YOLO-Master.html | 待优化 | 92.3 |
| YOLO-PEFT.html | 合格 | 96.3 | YOLO-SFEP.html | 优秀 | 99.0 |
| YOLO-SSAR.html | 优秀 | 99.0 | YOLO-Sugarcane.html | 优秀 | 99.0 |
| YOLO11n-EWL-Sugarcane-Bud.html | 优秀 | 99.0 | YOLO26_Unified_Real-Time_Vision.html | 待优化 | 92.2 |
| YOLOv10n-Wheat-Seedling.html | 合格 | 97.9 | YOLOv12-DMFA-Catenary.html | 优秀 | 97.2 |
| YOLOv12-Safflower.html | 合格 | 97.9 | YOLOv12-Water-Debris.html | 合格 | 97.9 |
| YOLOv12_Attention-Centric.html | 合格 | 95.4 | YOLOv12n-PCB.html | 合格 | 97.9 |
| YOLOv12n-RCL-Sunflower.html | 优秀 | 99.0 | YOLOv12n-VD-Furnace.html | 优秀 | 99.0 |
| YOLOv13.html | 优秀 | 99.0 | YOLOv7-Sugarcane-Seedling.html | 优秀 | 99.0 |

---

## 4. 评级依据说明

### 4.1 扣分点按维度汇总

| 维度 | 主要不达标条款 | 清单条目数 | 典型表现 |
|---|---|---|---|
| C | C1.4 信息过载 / C1.7 含图页文字过少 | 11 条 | 8 份文件单页要点 >8 个；3 份含图页中文不足 20 字 |
| L | L2.2 主屏溢出 / L2.3 padding / L2.4 宽图过窄 | 7 条 | DETRs 第 10 页 +59px；CityGrounding padding 为 4.5vh 6.5vw；5 份宽图不足容器 25% |
| T | T3.1 图注小字 / T3.3 对比度 | 15 条 | 14 份存在低对比度正文或图注；CityGrounding 图注 9.73px |
| V | V4.1 配色偏离 | 4 条 | 4 份 `--card-bg` / `--radius` 与基准不同（A 类模板自定义） |
| I | I5.3 整页点击误触 / I5.4 页码 / I5.5 显式控制器 / I5.6 | 2 条 | 模板级共性已合并；仅 2 份页码静态不自洽 |
| A | A6.2 投影/窄屏/竖屏适配 | 30 条 | 30 份在 1024×768 / 900×700 / 768×1024 下溢出或小字；主屏均正常 |

### 4.2 红线命中文件（4 份，均为 `R-S3` 文字不可读）

| 文件 | 总分 | 红线证据 | 其他扣分点 |
|---|---|---|---|
| CityGrounding.html | 92.3 | 图注 `rgb(138,151,168)` 白底 2.97:1，13~39 处；另图注 9.73px | A6.2,I5.3,L2.3,T3.1,T3.3 |
| Dialogue_Director.html | 91.5 | `.body-text` `rgb(153,153,153)` 浅底 2.67:1（全档最低 1.61:1） | A6.2,C1.4,T3.3,V4.1 |
| smooth-tail_learning.html | 95.0 | 封面副标题/作者 `rgb(97,145,211)` 白底 3.23:1（全档最低 2.68:1） | A6.2,C1.4,I5.5,T3.3 |
| YOLO26_Unified_Real-Time_Vision.html | 92.2 | `.figure-caption` `rgb(153,153,153)` 白底 2.85:1 | A6.2,C1.4,I5.4,I5.5,L2.4,T3.3 |

另有 **3 份因总分低于 93 判「待优化」但未命中红线**：`DETRs_Beat_YOLOs_on_Real-time_Object_Detection.html`(92.1)、`GrapickNet.html`(92.3)、`YOLO-Master.html`(92.3)。三者共同点是多项 P1 问题叠加（小屏适配 A6.2 + 宽图 L2.4 + 配色 V4.1 / 信息过载 C1.4），无单一致命缺陷，按 §5 的 P1 清单逐条清理即可回到合格。

> 上述 4 份红线文件的主体内容与演示流程均完整，问题集中在**浅灰/浅蓝小字在投影下不可辨认**，属于最容易修、收益最高的一类：只需调整若干 CSS 颜色值即可解除红线。

### 4.3 未命中红线的原因（避免误读为「未检查」）

- `R-F1` 失效图：542 处引用全部存在且渲染 `naturalWidth>0`，0 命中。
- `R-F2` 翻页失效：62 份 `.slide.active` 三属性均带 `!important`、无 inline style 改可见性，逐页可见性全为 true。
- `R-F3` 溢出裁切：主屏 7 页次溢出经截图复核未裁切关键内容，人工复核 `overflow_visible=false`。
- `R-S1` 叙事断裂：62 份均具备封面/方法/实验/总结必需段。
- `R-S2` 页码误导：8 处硬编码页码均由 JS 动态覆盖，2 处静态不自洽按 S2 计。
- `R-S4` 离线依赖：零外链、零 CDN、`file://` 无失败请求。

---

## 5. 待优化清单

共 **77** 条，按 **P0 → P1 → P2** 排序；同段内按影响程度、维度权重 `C(25) > L(18) > T(17) > A(14) > I(14) > V(12)`、文件名、页码排序。七字段：序号 / 优先级 / 影响程度 / 文件及具体页面 / 对应标准 / 问题描述 / 具体改进建议。

> **页码口径**：取渲染 DOM 中 `.slide` NodeList 顺序（1-based），与 `verify_slides.py` 的 `slides.length` 同源；页标题取该页 `<h2>` 或 `.slide-label`；全篇性问题写「全篇」，全库/模板级写「全库 / 不适用」。

### P0 · 立即处理（影响内容理解与演示效果）

共 **4** 条。全部为投影下文字不可辨认，建议先改 CSS 颜色值再复测对比度。

| 序号 | 影响 | 文件及具体页面 | 对应标准 | 问题描述 | 具体改进建议 |
|---|---|---|---|---|---|
| 1 | 高 | CityGrounding.html · 第 3、6、7、8、9 页 · 首见「从室内走向城市：任务没变，难度变了」 | T3.3 | [T3.3] 正文/小字对比度不足 39 处，最低 2.97:1（投影下难以辨认） | 把 CityGrounding.html 的 .body-text / .small-text / .figure-caption / .authors 中 #6191D3、#999、#888、#8A97A8 等浅色改为 #334155 或 #475569，使正文对比度≥4.5:1；改后用渲染器复算 getComputedStyle(color) 与背景的 WCAG 比值。 |
| 2 | 高 | Dialogue_Director.html · 第 6、10 页 · 首见「相关工作」 | T3.3 | [T3.3] 正文/小字对比度不足 60 处，最低 1.61:1（投影下难以辨认） | 把 Dialogue_Director.html 的 .body-text / .small-text / .figure-caption / .authors 中 #6191D3、#999、#888、#8A97A8 等浅色改为 #334155 或 #475569，使正文对比度≥4.5:1；改后用渲染器复算 getComputedStyle(color) 与背景的 WCAG 比值。 |
| 3 | 高 | YOLO26_Unified_Real-Time_Vision.html · 第 6、7、15 页 · 首见「YOLO26 架构设计」 | T3.3 | [T3.3] 正文/小字对比度不足 33 处，最低 2.85:1（投影下难以辨认） | 把 YOLO26_Unified_Real-Time_Vision.html 的 .body-text / .small-text / .figure-caption / .authors 中 #6191D3、#999、#888、#8A97A8 等浅色改为 #334155 或 #475569，使正文对比度≥4.5:1；改后用渲染器复算 getComputedStyle(color) 与背景的 WCAG 比值。 |
| 4 | 高 | smooth-tail_learning.html · 第 1、4、5、8 页 · 首见「Boosting Long-tailed Object Detection via Step-wise Learning」 | T3.3 | [T3.3] 正文/小字对比度不足 21 处，最低 2.68:1（投影下难以辨认） | 把 smooth-tail_learning.html 的 .body-text / .small-text / .figure-caption / .authors 中 #6191D3、#999、#888、#8A97A8 等浅色改为 #334155 或 #475569，使正文对比度≥4.5:1；改后用渲染器复算 getComputedStyle(color) 与背景的 WCAG 比值。 |

### P1 · 计划处理（显著影响观感与适配，不阻断演示）

共 **71** 条。以小屏适配、对比度、信息过载、宽图放大、模板级共性为主。

| 序号 | 影响 | 文件及具体页面 | 对应标准 | 问题描述 | 具体改进建议 |
|---|---|---|---|---|---|
| 5 | 中 | ASF-YOLO.html · 第 9 页 · 「DSB2018 与 BCC 定量结果」 | C1.7 | [C1.7] 含图页中文不足 20 字：[9] | 为 ASF-YOLO.html 第 9 页的图表补充至少 20 字中文解读（图注 + 一句结论），避免含图页只有图没有说明；参考 verify_slides.py 检查 6 的中文字符弱守卫。 |
| 6 | 中 | Attention_Is_All_You_Need.html · 第 11、14 页 · 首见「实验设置」 | C1.4 | [C1.4] 信息过载页：[11, 14] | 把 Attention_Is_All_You_Need.html 第 11、14 页的要点从 9 个以上压缩到 3-5 个，或拆成两页；参考 html-paper-slides/SKILL.md 的「每页 3-5 个要点」。 |
| 7 | 中 | Dialogue_Director.html · 第 12、18 页 · 首见「实验设置」 | C1.4 | [C1.4] 信息过载页：[12, 18] | 把 Dialogue_Director.html 第 12、18 页的要点从 9 个以上压缩到 3-5 个，或拆成两页；参考 html-paper-slides/SKILL.md 的「每页 3-5 个要点」。 |
| 8 | 中 | FADE.html · 第 12 页 · 「ADE20K 分割与 Composition-1K 抠图」 | C1.7 | [C1.7] 含图页中文不足 20 字：[12] | 为 FADE.html 第 12 页的图表补充至少 20 字中文解读（图注 + 一句结论），避免含图页只有图没有说明；参考 verify_slides.py 检查 6 的中文字符弱守卫。 |
| 9 | 中 | Generalized-Focal-Loss.html · 第 10 页 · 「COCO test-dev：45.0% AP 超越同期 SOTA」 | C1.7 | [C1.7] 含图页中文不足 20 字：[10] | 为 Generalized-Focal-Loss.html 第 10 页的图表补充至少 20 字中文解读（图注 + 一句结论），避免含图页只有图没有说明；参考 verify_slides.py 检查 6 的中文字符弱守卫。 |
| 10 | 中 | GrapickNet.html · 第 4 页 · 「从分离式检测到 GrapickNet」 | C1.4 | [C1.4] 信息过载页：[4] | 把 GrapickNet.html 第 4 页的要点从 9 个以上压缩到 3-5 个，或拆成两页；参考 html-paper-slides/SKILL.md 的「每页 3-5 个要点」。 |
| 11 | 中 | YOLO-Master.html · 第 5、12 页 · 首见「三条脉络，一个共同缺口」 | C1.4 | [C1.4] 信息过载页：[5, 12] | 把 YOLO-Master.html 第 5、12 页的要点从 9 个以上压缩到 3-5 个，或拆成两页；参考 html-paper-slides/SKILL.md 的「每页 3-5 个要点」。 |
| 12 | 中 | YOLO-PEFT.html · 第 13 页 · 「实验设置：官方 VOC 协议 · 五种异构架构」 | C1.4 | [C1.4] 信息过载页：[13] | 把 YOLO-PEFT.html 第 13 页的要点从 9 个以上压缩到 3-5 个，或拆成两页；参考 html-paper-slides/SKILL.md 的「每页 3-5 个要点」。 |
| 13 | 中 | YOLO26_Unified_Real-Time_Vision.html · 第 8 页 · 「DFL移除与双头设计」 | C1.4 | [C1.4] 信息过载页：[8] | 把 YOLO26_Unified_Real-Time_Vision.html 第 8 页的要点从 9 个以上压缩到 3-5 个，或拆成两页；参考 html-paper-slides/SKILL.md 的「每页 3-5 个要点」。 |
| 14 | 中 | YOLOv12_Attention-Centric.html · 第 7 页 · 「Method 02 / R-ELAN」 | C1.4 | [C1.4] 信息过载页：[7] | 把 YOLOv12_Attention-Centric.html 第 7 页的要点从 9 个以上压缩到 3-5 个，或拆成两页；参考 html-paper-slides/SKILL.md 的「每页 3-5 个要点」。 |
| 15 | 中 | smooth-tail_learning.html · 第 3、4、5、6、7、9 等 页 · 首见「研究背景与动机」 | C1.4 | [C1.4] 信息过载页：[3, 4, 5, 6, 7, 9, 13] | 把 smooth-tail_learning.html 第 3、4、5、6、7、9、13 页的要点从 9 个以上压缩到 3-5 个，或拆成两页；参考 html-paper-slides/SKILL.md 的「每页 3-5 个要点」。 |
| 16 | 中 | CityGrounding.html · 全篇 / 不适用 | L2.3 | [L2.3] 缺 padding:5vh 7vw | 把 CityGrounding.html 的 .slide padding 统一为 5vh 7vw，并用 Grid/Flex 布局。 |
| 17 | 中 | DETRs_Beat_YOLOs_on_Real-time_Object_Detection.html · 第 10 页 · 「主实验结果：与SOTA对比」 | L2.2 | [L2.2] 主档最大 59px 溢出；人工复核未裁切关键内容，但版式偏紧需收紧 | 为 DETRs_Beat_YOLOs_on_Real-time_Object_Detection.html 第 10 页增加高度溢出兜底：下调该页 padding 与 clamp() 字号下限、给 .slide 加 overflow-y:auto，或拆分该页内容；在 1280×720 与 1920×1080 复测 scrollHeight<=clientHeight。 |
| 18 | 中 | DilateFormer.html · 第 5 页 · 「MSDA：多尺度空洞注意力」 | L2.4 | [L2.4] 横长图渲染宽度不足容器 25%，1 处难以辨认 | 把 DilateFormer.html 中的横长框架图/宽表改为独占整页（宽度≥60%），或拆成上下两半页，避免挤在窄栏。 |
| 19 | 中 | GrapickNet.html · 第 15 页 · 「主流模型定量对比」 | L2.4 | [L2.4] 横长图渲染宽度不足容器 25%，1 处难以辨认 | 把 GrapickNet.html 中的横长框架图/宽表改为独占整页（宽度≥60%），或拆成上下两半页，避免挤在窄栏。 |
| 20 | 中 | YOLO-Master.html · 第 13 页 · 「五个基准全面领先同尺度对手」 | L2.4 | [L2.4] 横长图渲染宽度不足容器 25%，1 处难以辨认 | 把 YOLO-Master.html 中的横长框架图/宽表改为独占整页（宽度≥60%），或拆成上下两半页，避免挤在窄栏。 |
| 21 | 中 | YOLO26_Unified_Real-Time_Vision.html · 第 15、16 页 · 首见「消融补充（一）：DFL 移除 · MuSGD · 分割原型」 | L2.4 | [L2.4] 横长图渲染宽度不足容器 25%，4 处难以辨认 | 把 YOLO26_Unified_Real-Time_Vision.html 中的横长框架图/宽表改为独占整页（宽度≥60%），或拆成上下两半页，避免挤在窄栏。 |
| 22 | 中 | YOLOv12-DMFA-Catenary.html · 第 5 页 · 「SFAR-Net：空频双分支 + FFTSA 频域自注意力」 | L2.4 | [L2.4] 横长图渲染宽度不足容器 25%，1 处难以辨认 | 把 YOLOv12-DMFA-Catenary.html 中的横长框架图/宽表改为独占整页（宽度≥60%），或拆成上下两半页，避免挤在窄栏。 |
| 23 | 中 | 全库（62 份） · 全库 / 不适用 | L2.1 / L2.6 | 规范写明 16:9，但实现全库为 .deck{width:100vw;height:100vh}，无 aspect-ratio、无 transform:scale()/resize 缩放兜底，不同宽高比投影下版式漂移。 | 统一由模板层为 .deck 增加 aspect-ratio:16/9 与基于 Math.min(innerWidth/1280, innerHeight/720) 的 scale 缩放，或补 @media (max-aspect-ratio:16/9) 下调 padding 与 clamp 下限。 |
| 24 | 中 | 全库（62 份） · 全库 / 不适用 | L2.4（模板级） | 横长表格/框架图普遍只占容器约 39% 宽度（411 处记录的中位数 0.392），双栏半页布局下表格文字偏小；仅不足 25% 的少数记录已按文件级列入清单。 | 统一把关键横长表格图提升为独占整页（宽度≥60%），或提供点击放大/高清原图入口；同时保留 alt 与图注。 |
| 25 | 中 | Attention_Is_All_You_Need.html · 第 1、5、7 页 · 首见「封面」 | T3.3 | [T3.3] 正文/小字对比度不足 36 处，最低 3.06:1 | 把 Attention_Is_All_You_Need.html 的 .body-text / .small-text / .figure-caption / .authors 中 #6191D3、#999、#888、#8A97A8 等浅色改为 #334155 或 #475569，使正文对比度≥4.5:1；改后用渲染器复算 getComputedStyle(color) 与背景的 WCAG 比值。 |
| 26 | 中 | CityGrounding.html · 第 3、6、7、8、9、14 等 页 · 首见「从室内走向城市：任务没变，难度变了」 | T3.1 | [T3.1] 最小字号 9.73px（低于 11px；经复核为图注/装饰性小字，正文主体可读） | 把 CityGrounding.html 中 figure-caption / 装饰性小字的 clamp() 下限从约 9.7px 提到 11px，并确认 1280×720 下正文≥13px、标题≥24px；图注不宜远小于正文下限。 |
| 27 | 中 | DETRs_Beat_YOLOs_on_Real-time_Object_Detection.html · 第 12 页 · 「消融实验：验证各组件贡献」 | T3.3 | [T3.3] 正文/小字对比度不足 12 处，最低 3.3:1 | 把 DETRs_Beat_YOLOs_on_Real-time_Object_Detection.html 的 .body-text / .small-text / .figure-caption / .authors 中 #6191D3、#999、#888、#8A97A8 等浅色改为 #334155 或 #475569，使正文对比度≥4.5:1；改后用渲染器复算 getComputedStyle(color) 与背景的 WCAG 比值。 |
| 28 | 中 | DilateFormer.html · 第 9 页 · 「消融：SWDA 在各项对比中均最优」 | T3.3 | [T3.3] 正文/小字对比度不足 12 处，最低 4.25:1 | 把 DilateFormer.html 的 .body-text / .small-text / .figure-caption / .authors 中 #6191D3、#999、#888、#8A97A8 等浅色改为 #334155 或 #475569，使正文对比度≥4.5:1；改后用渲染器复算 getComputedStyle(color) 与背景的 WCAG 比值。 |
| 29 | 中 | FreqFusion.html · 第 3、4、5、6、7 页 · 首见「研究动机：标准特征融合的两大缺陷」 | T3.3 | [T3.3] 正文/小字对比度不足 60 处，最低 3.07:1 | 把 FreqFusion.html 的 .body-text / .small-text / .figure-caption / .authors 中 #6191D3、#999、#888、#8A97A8 等浅色改为 #334155 或 #475569，使正文对比度≥4.5:1；改后用渲染器复算 getComputedStyle(color) 与背景的 WCAG 比值。 |
| 30 | 中 | Mona.html · 第 11 页 · 「消融实验：容量与结构设计的规律」 | T3.3 | [T3.3] 正文/小字对比度不足 12 处，最低 4.25:1 | 把 Mona.html 的 .body-text / .small-text / .figure-caption / .authors 中 #6191D3、#999、#888、#8A97A8 等浅色改为 #334155 或 #475569，使正文对比度≥4.5:1；改后用渲染器复算 getComputedStyle(color) 与背景的 WCAG 比值。 |
| 31 | 中 | ParameterNet.html · 第 5 页 · 「复杂度分析：参数翻倍、FLOPs 不变」 | T3.3 | [T3.3] 正文/小字对比度不足 12 处，最低 4.25:1 | 把 ParameterNet.html 的 .body-text / .small-text / .figure-caption / .authors 中 #6191D3、#999、#888、#8A97A8 等浅色改为 #334155 或 #475569，使正文对比度≥4.5:1；改后用渲染器复算 getComputedStyle(color) 与背景的 WCAG 比值。 |
| 32 | 中 | Pinwheel-Conv-Loss.html · 第 5 页 · 「感受野与参数量的量化对比」 | T3.3 | [T3.3] 正文/小字对比度不足 9 处，最低 4.25:1 | 把 Pinwheel-Conv-Loss.html 的 .body-text / .small-text / .figure-caption / .authors 中 #6191D3、#999、#888、#8A97A8 等浅色改为 #334155 或 #475569，使正文对比度≥4.5:1；改后用渲染器复算 getComputedStyle(color) 与背景的 WCAG 比值。 |
| 33 | 中 | TPH-YOLO.html · 第 8 页 · 「迁移学习训练策略」 | T3.3 | [T3.3] 正文/小字对比度不足 9 处，最低 4.25:1 | 把 TPH-YOLO.html 的 .body-text / .small-text / .figure-caption / .authors 中 #6191D3、#999、#888、#8A97A8 等浅色改为 #334155 或 #475569，使正文对比度≥4.5:1；改后用渲染器复算 getComputedStyle(color) 与背景的 WCAG 比值。 |
| 34 | 中 | YOLO-PEFT.html · 第 5、8、9 页 · 首见「四阶段流水线：解析 → 规划 → 训练 → 部署」 | T3.3 | [T3.3] 正文/小字对比度不足 36 处，最低 3.07:1 | 把 YOLO-PEFT.html 的 .body-text / .small-text / .figure-caption / .authors 中 #6191D3、#999、#888、#8A97A8 等浅色改为 #334155 或 #475569，使正文对比度≥4.5:1；改后用渲染器复算 getComputedStyle(color) 与背景的 WCAG 比值。 |
| 35 | 中 | YOLOv12_Attention-Centric.html · 第 8 页 · 「Method 03 / Architecture」 | T3.3 | [T3.3] 正文/小字对比度不足 15 处，最低 4.25:1 | 把 YOLOv12_Attention-Centric.html 的 .body-text / .small-text / .figure-caption / .authors 中 #6191D3、#999、#888、#8A97A8 等浅色改为 #334155 或 #475569，使正文对比度≥4.5:1；改后用渲染器复算 getComputedStyle(color) 与背景的 WCAG 比值。 |
| 36 | 中 | 全库（62 份） · 全库 / 不适用 | T3.6 | 实验数据表全部为 PNG 位图（少数缺 alt），不可检索、不可放大、屏幕阅读器不可读。 | 关键对比表改为语义化 <table>（保留 PNG 作为兜底），并为所有 <img> 补 alt 与图注。 |
| 37 | 中 | CARAFE.html · 第 18 页 · 「语义分割与图像修复的定性对比」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 2 页次（主屏正常） | 为 CARAFE.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 38 | 中 | CityGrounding.html · 全篇 / 不适用 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 16、溢出 0 页次（主屏正常） | 为 CityGrounding.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 39 | 中 | Conv2Former.html · 第 4、7、18、19 页 · 首见「从自注意力到卷积调制：只替换权重生成」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 4 页次（主屏正常） | 为 Conv2Former.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 40 | 中 | DDMA-YOLO.html · 第 6、13、16、17、19 页 · 首见「RCAN：残差中的残差 + 通道注意力」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 8 页次（主屏正常） | 为 DDMA-YOLO.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 41 | 中 | DETRs_Beat_YOLOs_on_Real-time_Object_Detection.html · 第 5、12、13 页 · 首见「RT-DETR 架构总览」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 3 页次（主屏正常） | 为 DETRs_Beat_YOLOs_on_Real-time_Object_Detection.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 42 | 中 | DFR-SN-YOLO.html · 第 5、6、11、21 页 · 首见「整体架构：以 YOLOv5s 为基准的四段式网络」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 15、溢出 4 页次（主屏正常） | 为 DFR-SN-YOLO.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 43 | 中 | Dialogue_Director.html · 第 7 页 · 「Dialogue Director 总体框架」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 1 页次（主屏正常） | 为 Dialogue_Director.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 44 | 中 | DySample_Learning_to_Upsample.html · 第 2、3、5、10、11 页 · 首见「核心贡献：从「生成核」改为「生成采样位置」」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 8 页次（主屏正常） | 为 DySample_Learning_to_Upsample.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 45 | 中 | Dynamic-Head.html · 第 10、14、16 页 · 首见「同一套块，如何接进一阶段与两阶段检测器」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 24、溢出 4 页次（主屏正常） | 为 Dynamic-Head.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 46 | 中 | FADE.html · 第 6 页 · 「朴素实现：显式插值对齐的代价」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 1 页次（主屏正常） | 为 FADE.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 47 | 中 | FreqFusion.html · 第 4、5、9、10、11 页 · 首见「特征相似性分析：把缺陷变成标尺」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 20、溢出 10 页次（主屏正常） | 为 FreqFusion.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 48 | 中 | GrapickNet.html · 第 4、7、10、11、14 页 · 首见「从分离式检测到 GrapickNet」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 11 页次（主屏正常） | 为 GrapickNet.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 49 | 中 | MAF-YOLO.html · 第 8 页 · 「RepHDWConv：训练并行、推理合并」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 1 页次（主屏正常） | 为 MAF-YOLO.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 50 | 中 | MNBS-YOLOv12.html · 第 2 页 · 「四处改进对应四类核心挑战」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 1 页次（主屏正常） | 为 MNBS-YOLOv12.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 51 | 中 | ParameterNet.html · 第 5 页 · 「复杂度分析：参数翻倍、FLOPs 不变」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 1 页次（主屏正常） | 为 ParameterNet.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 52 | 中 | Powerful-IoU.html · 第 5、7、8、11、12 页 · 首见「现有 IoU 系损失的通用形式」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 6 页次（主屏正常） | 为 Powerful-IoU.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 53 | 中 | SimAM.html · 第 10、12、14、15 页 · 首见「模块实现与插入位置」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 5 页次（主屏正常） | 为 SimAM.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 54 | 中 | TPH-YOLO.html · 第 4、8 页 · 首见「Retinex 图像增强：削弱光照不均匀影响」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 2 页次（主屏正常） | 为 TPH-YOLO.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 55 | 中 | YOLO-Master.html · 第 5、7、9、12、19 页 · 首见「三条脉络，一个共同缺口」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 5、溢出 5 页次（主屏正常） | 为 YOLO-Master.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 56 | 中 | YOLO-PEFT.html · 第 2、4、5、9、12 页 · 首见「核心贡献」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 9、溢出 8 页次（主屏正常） | 为 YOLO-PEFT.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 57 | 中 | YOLO26_Unified_Real-Time_Vision.html · 第 7、9、11、14、17 页 · 首见「训练管线：三大核心组件」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 20、溢出 6 页次（主屏正常） | 为 YOLO26_Unified_Real-Time_Vision.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 58 | 中 | YOLOv10n-Wheat-Seedling.html · 第 6、7 页 · 首见「SDI 语义细节融合模块」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 2 页次（主屏正常） | 为 YOLOv10n-Wheat-Seedling.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 59 | 中 | YOLOv12-Safflower.html · 第 2 页 · 「四模块协同：边缘纹理 + 多维融合 + 保细节下采样 + 轻量头」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 1 页次（主屏正常） | 为 YOLOv12-Safflower.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 60 | 中 | YOLOv12-Water-Debris.html · 第 6 页 · 「C3k2_DynamicConv：动态卷积增强特征捕捉」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 1 页次（主屏正常） | 为 YOLOv12-Water-Debris.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 61 | 中 | YOLOv12_Attention-Centric.html · 第 7、8、9、13、17 页 · 首见「Method 02 / R-ELAN」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 5 页次（主屏正常） | 为 YOLOv12_Attention-Centric.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 62 | 中 | YOLOv12n-PCB.html · 第 7、8 页 · 首见「FFF：特征聚焦融合模块」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 2 页次（主屏正常） | 为 YOLOv12n-PCB.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 63 | 中 | cbp-yolo.html · 第 8 页 · 「C2f-CA：把通道注意力拆成两个方向的一维编码」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 2、溢出 1 页次（主屏正常） | 为 cbp-yolo.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 64 | 中 | gcmd-yolo.html · 第 6、9、17 页 · 首见「GL-ODConv：全局-局部双通路动态卷积」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 3 页次（主屏正常） | 为 gcmd-yolo.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 65 | 中 | psmf-yolo.html · 第 4、6、7、10、15 页 · 首见「PSMF-YOLO 整体网络架构」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 7 页次（主屏正常） | 为 psmf-yolo.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 66 | 中 | smooth-tail_learning.html · 第 3、4、5、6、7 页 · 首见「研究背景与动机」 | A6.2 | [A6.2] 投影/窄屏/竖屏：小字页 0、溢出 14 页次（主屏正常） | 为 smooth-tail_learning.html 增加按屏幕高度/宽度的响应式降级：补 @media (max-height: 768px) 与 (max-width: 900px) 下调 .slide padding 与 clamp() 字号下限、压缩图注；在 1024×768 / 900×700 / 768×1024 三档复测 scrollHeight<=clientHeight 且正文≥11px。 |
| 67 | 中 | 全库（62 份） · 全库 / 不适用 | A6.4 | 全库 62 份均无 @media print，.slide 默认 opacity:0/visibility:hidden，打印或导出 PDF 只能得到当前 1 页或空白。 | 为全部 62 份 <style> 补：@media print { .slide{position:relative;opacity:1!important;visibility:visible!important;transform:none!important;page-break-after:always} .controls,.dots,.progress,.hint{display:none!important} }，并用 emulateMedia('print') 验证可见页数 = 实际页数。 |
| 68 | 中 | FreqFusion.html · 全篇 / 不适用 | I5.4 | [I5.4] 硬编码页码 01 / 19 与实际 21 页不符（JS 动态覆盖 / 控件 display:none，仅静态源码不自洽） | 把 FreqFusion.html:1077 的静态初始值 01 / 19 直接改为 01 / 21，或在首屏初始化时立即调用一次 counter.textContent = pad(1) + ' / ' + pad(total)；若 .controls 为 display:none，请一并确认是否需要显示页码。 |
| 69 | 中 | YOLO26_Unified_Real-Time_Vision.html · 全篇 / 不适用 | I5.4 | [I5.4] 硬编码页码 01 / 01 与实际 21 页不符（JS 动态覆盖 / 控件 display:none，仅静态源码不自洽） | 把 YOLO26_Unified_Real-Time_Vision.html:1172 的静态初始值 01 / 01 直接改为 01 / 21，或在首屏初始化时立即调用一次 counter.textContent = pad(1) + ' / ' + pad(total)；若 .controls 为 display:none，请一并确认是否需要显示页码。 |
| 70 | 中 | 全库（A 类 6 份） · 全篇 / 模板级 | I5.5 | A 类模板 6 份含 .controls 显式左右翻页按钮，与 html-paper-slides/SKILL.md「不要出现显式的左右翻页控制器」冲突。 | 移除 .controls 显式按钮（或统一两套模板并同步更新规范条款），保留键盘翻页。 |
| 71 | 中 | 全库（B 类 53 份） · 全篇 / 模板级 | I5.3 | B 类模板 53 份使用 document 级 click 整页翻页且仅排除 .dot：点击图片、正文或链接都会误翻页；叠加全库 user-select:none，正文既不可选中也无法点链接。 | 统一把 document 级 click 翻页改为仅绑定 .deck 空白区，或在 img / a / .dot 的点击处理里 stopPropagation()；保留 touchstart/touchend 滑动翻页。 |
| 72 | 中 | DETRs_Beat_YOLOs_on_Real-time_Object_Detection.html · 全篇 / 不适用 | V4.1 | [V4.1] 偏离基准 2 项 | 把 DETRs_Beat_YOLOs_on_Real-time_Object_Detection.html 的 :root 配色对齐基准：{'--bg': '#ffffff', '--text': '#000000', '--title': '#3966A2', '--accent': '#132843', '--dim': '#6191D3', '--card-bg': '#f7f9fc', '--border': '#e2e8f0', '--radius': '12px'}。 |
| 73 | 中 | Dialogue_Director.html · 全篇 / 不适用 | V4.1 | [V4.1] 偏离基准 2 项 | 把 Dialogue_Director.html 的 :root 配色对齐基准：{'--bg': '#ffffff', '--text': '#000000', '--title': '#3966A2', '--accent': '#132843', '--dim': '#6191D3', '--card-bg': '#f7f9fc', '--border': '#e2e8f0', '--radius': '12px'}。 |
| 74 | 中 | GrapickNet.html · 全篇 / 不适用 | V4.1 | [V4.1] 偏离基准 1 项 | 把 GrapickNet.html 的 :root 配色对齐基准：{'--bg': '#ffffff', '--text': '#000000', '--title': '#3966A2', '--accent': '#132843', '--dim': '#6191D3', '--card-bg': '#f7f9fc', '--border': '#e2e8f0', '--radius': '12px'}。 |
| 75 | 中 | YOLO-Master.html · 全篇 / 不适用 | V4.1 | [V4.1] 偏离基准 1 项 | 把 YOLO-Master.html 的 :root 配色对齐基准：{'--bg': '#ffffff', '--text': '#000000', '--title': '#3966A2', '--accent': '#132843', '--dim': '#6191D3', '--card-bg': '#f7f9fc', '--border': '#e2e8f0', '--radius': '12px'}。 |

### P2 · 低优先级（一致性与轻微偏差）

共 **2** 条。统一规范或下次重生成时一并处理。

| 序号 | 影响 | 文件及具体页面 | 对应标准 | 问题描述 | 具体改进建议 |
|---|---|---|---|---|---|
| 76 | 低 | 全库（62 份） · 全库 / 不适用 | C1.6 | 全库无「参考文献 / References」章节，仅封面标注 arXiv/DOI。 | 在结尾页前增加「出处与参考文献」页，列出论文标题、作者、 venue、DOI/arXiv 链接。 |
| 77 | 低 | 全库（62 份） · 全库 / 不适用 | V4.6 | A/B 两套生成器模板并存：A 类有 .controls 与硬编码页码，B 类整页 click 翻页无页码，控制组件与章节命名体系不一致。 | 统一到一套模板组件（导航、页码、章节标签），历史文件在下次重生成时一并迁移。 |

---

## 6. 共性问题（`G` 全局项与模板级共性，不参与逐份评分）

### 6.1 为什么剔除逐份评分

以下问题是 62 份同犯的历史模板遗留。若逐份扣分，L / A / T 三维会被普遍压低，**没有任何文件能达到「优秀」门槛，三档评级失去区分度**，也无法回答「哪些文件更值得先改」。因此标准 §3.3 规定：这些项完整成文、不进入逐份折算、在报告中单列、各写 1 条全库级建议。逐份评级只由文件自身可区分的差异决定。

| 标准编号 | 共性问题 | 影响 | 优先级 | 统一改进建议 |
|---|---|---|---|---|
| L2.1 / L2.6 | 规范写明 16:9，但实现全库为 .deck{width:100vw;height:100vh}，无 aspect-ratio、无 transform:scale()/resize 缩放兜底，不同宽高比投影下版式漂移。 | 中 | P1 | 统一由模板层为 .deck 增加 aspect-ratio:16/9 与基于 Math.min(innerWidth/1280, innerHeight/720) 的 scale 缩放，或补 @media (max-aspect-ratio:16/9) 下调 padding 与 clamp 下限。 |
| L2.4（模板级） | 横长表格/框架图普遍只占容器约 39% 宽度（411 处记录的中位数 0.392），双栏半页布局下表格文字偏小；仅不足 25% 的少数记录已按文件级列入清单。 | 中 | P1 | 统一把关键横长表格图提升为独占整页（宽度≥60%），或提供点击放大/高清原图入口；同时保留 alt 与图注。 |
| T3.6 | 实验数据表全部为 PNG 位图（少数缺 alt），不可检索、不可放大、屏幕阅读器不可读。 | 中 | P1 | 关键对比表改为语义化 <table>（保留 PNG 作为兜底），并为所有 <img> 补 alt 与图注。 |
| A6.4 | 全库 62 份均无 @media print，.slide 默认 opacity:0/visibility:hidden，打印或导出 PDF 只能得到当前 1 页或空白。 | 中 | P1 | 为全部 62 份 <style> 补：@media print { .slide{position:relative;opacity:1!important;visibility:visible!important;transform:none!important;page-break-after:always} .controls,.dots,.progress,.hint{display:none!important} }，并用 emulateMedia('print') 验证可见页数 = 实际页数。 |
| I5.5 | A 类模板 6 份含 .controls 显式左右翻页按钮，与 html-paper-slides/SKILL.md「不要出现显式的左右翻页控制器」冲突。 | 中 | P1 | 移除 .controls 显式按钮（或统一两套模板并同步更新规范条款），保留键盘翻页。 |
| I5.3 | B 类模板 53 份使用 document 级 click 整页翻页且仅排除 .dot：点击图片、正文或链接都会误翻页；叠加全库 user-select:none，正文既不可选中也无法点链接。 | 中 | P1 | 统一把 document 级 click 翻页改为仅绑定 .deck 空白区，或在 img / a / .dot 的点击处理里 stopPropagation()；保留 touchstart/touchend 滑动翻页。 |
| C1.6 | 全库无「参考文献 / References」章节，仅封面标注 arXiv/DOI。 | 低 | P2 | 在结尾页前增加「出处与参考文献」页，列出论文标题、作者、 venue、DOI/arXiv 链接。 |
| V4.6 | A/B 两套生成器模板并存：A 类有 .controls 与硬编码页码，B 类整页 click 翻页无页码，控制组件与章节命名体系不一致。 | 低 | P2 | 统一到一套模板组件（导航、页码、章节标签），历史文件在下次重生成时一并迁移。 |

### 6.2 补充观察（不计分、仅记录）

- **打印可见页数**：`emulateMedia('print')` 后 62 份仅 1~3 页可见（`.slide` 默认 `opacity:0; visibility:hidden`），印证 A6.4 的判断：直接打印/导出 PDF 只能得到当前页或空白。
- **A/B 双模板**：A 类 8 份（展开式，含 `.controls` 与硬编码页码、章节贴近论文本体），B 类 54 份（压缩式，整页 click 翻页、固定 `Contributions/Motivation/Method 0x` 章节名）。两者配色、字体栈、`clamp()` 字号体系一致，差异集中在控制组件与资源目录组织。
- **横长图占比**：411 处宽图记录的中位数为容器宽度的 39.2%，属双栏半页布局常态；本次仅把不足 25% 的少数记录判为文件级问题，其余作为模板级优化建议。

---

## 7. 外围附注（不参与评级、不扣分）

| 位置 | 现象 | 说明 |
|---|---|---|
| `index.html:883,890` | `embeddedDecks` 里 `paper-slides/maize_tassels_presentation.html`、`paper-slides/sugarcane_thesis_presentation.html` 两条路径磁盘不存在 | 仅在 manifest 与目录发现双双失败时才触发的兜底数据，正常路径不生效 |
| `README.md` / `README.en.md:124` | Showcase 链接指向 `paper-slides/YOLO-Master_Presentation.html`，实际为 `YOLO-Master.html` | 文档断链 |
| `paper-slides/2023 Dysample ..._assets/` | 18 张 PNG + 1 个 JSON 无任何 HTML 引用 | DySample 幻灯片实际引用 `assets/paper-imgs/DySample/`，该目录为孤立素材 |
| `paper-slides/*/extraction_summary.json` | 仅 2 个素材目录有清单，且 schema 不同（`images`/`cropped_regions` vs `items`/`total_figures`），`pdf_path` 硬编码旧绝对路径 | 抽取流水线存在两个版本，路径已失效 |
| `slides-manifest.json` | 62 条 1:1 覆盖全部 HTML，但末尾 `GrapickNet`、`CityGrounding` 为后补未重排；多数 `description` 为模板占位文案；`accent` 62 条全同 | 无质量/状态字段，不能用于判断单篇完成度 |
| `assets/thumbnails/` | 62 张缩略图与 62 份 HTML 严格 1:1 | 登记完整，本次不扣分 |
| `assets/design-prompts/organic.md` | 定义 Organic/Natural 门户风格，与 62 份 PPT 的蓝色苹果风/Notion 风互不影响 | 两套风格各有适用范围，非缺陷 |

---

## 8. 静态/渲染差异与人工复核结论

本节记录所有被驳回的疑似项，避免把探索阶段或静态扫描的误判写进评级。完整复核表见 `.cache/slides-audit/human_review.json`。

| # | 疑似问题（来源） | 复核结论 | 依据 |
|---|---|---|---|
| 1 | `Conv2Former` 约 13 处 `table*.png`、`psmf-yolo` 13 处、`YOLOv12n-RCL-Sunflower` 3 处、`DySample` 8 处 `dysample_table*.png` 目录/命名不存在（探索阶段静态比对） | **全部驳回** | `Glob` 结果被 `limit` 截断造成误判；磁盘实际存在 `Conv2Former/table1~13.png`、`psmf-yolo/figXX_*.png`、`YOLOv12n-RCL-Sunflower/fig8,tab3,fig12.png`、`DySample/dysample_table2~9.png`；542 处引用全部存在、渲染 `naturalWidth>0` |
| 2 | 62 份普遍「内容溢出」 | **大部分驳回** | 装饰性 `.glow` 为 absolute 负偏移，把 `scrollHeight/scrollWidth` 撑出固定 120/100px；隐藏后主屏假溢出归零，仅剩 7 页次真实溢出 |
| 3 | 页码硬编码 11 处、含 `25 / 26`、`1 / 9` | **收敛为 8 处** | 正文实验数据被宽泛正则误判；改用仅匹配 `.counter` / `.page-counter` 元素后，真实页码 8 处；其中 2 处静态值与实际页数不符 |
| 4 | `YOLO26_Unified_Real-Time_Vision.html:1172` `01 / 01`、`FreqFusion.html:1077` `01 / 19` 导航误导 | **降级为 S2，不触发 `R-S2`** | 两者 JS 均 `counter.textContent = pad(current+1)+' / '+pad(total)` 动态覆盖；YOLO26 的 `.controls` 还是 `display:none`，静态源码不自洽但运行时无影响 |
| 5 | `smooth-tail_learning.html`、`YOLO-PEFT.html` 键盘翻页失效 | **驳回** | 源码均有完整 ArrowLeft/Right/Home/End 绑定；`keyboard_ok=False` 源于 0.6s 过渡 / `requestAnimationFrame` 切页瞬间采样（`i1=-1`、`end=1`），smooth-tail 另有 650ms `isTransitioning` 动画锁 |
| 6 | 29 份因「叙事链缺失/顺序错乱」应判 `R-S1` | **全部驳回** | 章节归一化先取中文 `<h2>`，漏掉 `Method 01` 等 `.slide-label`；改为标签前缀优先 + 中文回退后，62 份必需段齐备、顺序正常 |
| 7 | 3 份封面「缺作者」（`CityGrounding` / `DETRs` / `Dialogue_Director`） | **驳回** | A 类封面不用 `.contributors/.author` 类名，作者直接写在文本中；补文本判据后 62 份封面信息齐全 |
| 8 | 大量「黑字在深蓝底对比度 3.6:1」告警 | **驳回** | `rgba(57,102,162,0.06)` 半透明背景被当作不透明纯色；改为按 alpha 与白底合成后消失。剩余 14 份为真实低对比度灰/蓝小字 |
| 9 | `DETRs` 第 10 页 +59px 溢出应判 `R-F3` | **驳回** | 1280×720 截图确认表格、图注、右侧三张卡片均完整可见，未裁切关键内容；保留为 P1「版式偏紧」建议 |
| 10 | `CityGrounding` 9.73px 小字应判 `R-S3` | **字号的红线降级为 P1** | 该字号属于 `figure-caption` 图注，正文主体可读；按标准 T3.1 记 S2。注意该文件最终仍命中 `R-S3`，但证据来自 T3.3 的 2.97:1 对比度，不是字号 |

> 人工复核共记录 9 条结论、8 份文件的逐项确认。

---

## 9. 未验证项与降级说明

- **渲染可用性**：Playwright + Chromium 可用，62/62 份完成 6 档渲染，**未发生降级**，所有文件的渲染类检查项均已验证。
- **事实层**：实验数值、数据集规模、指标与 `pdf-papers/` 原文的一致性未逐份比对，按标准 C1.9 标注「事实层未逐份核验」，不作通过/失败结论。
- **可选档 A6.7**：浏览器缩放 125% / 150% 未纳入本次 6 档 viewport，仅记录不判分。
- **顺序合理性**：章节顺序的静态提示已人工复核，未发现真实错乱。
- **冲突裁决**：图片存在性、页数以渲染 DOM 为准；硬编码页码以人工复核「JS 是否覆盖」为准；溢出是否裁切以截图为准。

---

## 附录 A · 度量字段与复现命令

中间产物位于 `.cache/slides-audit/`（已被 `.gitignore:9` 忽略，不纳入交付）：

| 文件 | 内容 |
|---|---|
| `static_metrics.json` | 62 份静态扫描结果（页数、章节、图片、CSS 变量、@media、外链、页码、事件） |
| `render_metrics.json` | 62 × 6 档渲染度量（溢出、`naturalWidth`、计算字号、对比度、键盘、print） |
| `human_review.json` | 人工复核结论与逐项确认 |
| `findings.json` | 62 份评级、77 条已排序清单、红线与共性项 |
| `report_tables.md` | 自动生成的评级总表与清单表格片段 |
| `screens/` | 1280×720 关键页复核截图；用于结论的是 `DETRs.../1280x720_p10.png` 与 `smooth-tail_learning/1280x720_p5.png`，另有 3 份小批验证期的早期截图未用于判定 |

复现（Windows PowerShell，须用已装 playwright 的 PATH `python`，本项目为 Anaconda 3.11）：

```powershell
python scripts/audit_slides.py --static
python scripts/audit_render.py --probe-only
python scripts/audit_render.py
python scripts/audit_slides.py --init-review   # 仅首次；之后人工编辑 human_review.json
python scripts/audit_slides.py --score
```

> PowerShell 的 stdout 在本机不被可靠捕获，脚本一律把结论落盘为 JSON/TXT，再用 Read 工具读取；不要以控制台输出作为判定依据。

## 附录 B · 检查项编号速查

完整条款、判定方法、严重度与对齐依据见 [`docs/html-ppt-quality-standard.md`](./html-ppt-quality-standard.md) §4 与附录 B。

| 维度 | 编号 |
|---|---|
| C 内容完整性与逻辑 | C1.1 封面溯源 · C1.2 叙事链 · C1.3 无占位 · C1.4 要点量 · C1.5 图注 · C1.6 出处(G) · C1.7 空页 · C1.8 图片可用 · C1.9 事实层 |
| L 版式布局 | L2.1 16:9(G) · L2.2 溢出 · L2.3 padding/弹性 · L2.4 宽图 · L2.5 单主题 · L2.6 缩放兜底(G) |
| T 文字可读性 | T3.1 字号 · T3.2 字体/零外链 · T3.3 对比度 · T3.4 公式 · T3.5 字重行高 · T3.6 表格位图(G) |
| V 视觉一致性 | V4.1 配色 · V4.2 字体栈 · V4.3 必需组件 · V4.4 封面/章节样式 · V4.5 组件参数 · V4.6 双模板(G) |
| I 交互效果 | I5.1 状态机 · I5.2 键盘 · I5.3 触摸/误触 · I5.4 页码自洽 · I5.5 显式控制器 · I5.6 dots/进度 · I5.7 全屏 |
| A 展示适配 | A6.1 三档主屏 · A6.2 投影/窄屏/竖屏 · A6.3 响应式 · A6.4 打印(G) · A6.5 离线单文件 · A6.6 viewport · A6.7 缩放 |
