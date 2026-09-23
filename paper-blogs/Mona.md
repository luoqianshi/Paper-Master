---
title: "5%>100%: Breaking Performance Shackles of Full Fine-Tuning on Visual Recognition Tasks"
category: 模型微调
date: 2026-09-02
source_url: https://github.com/Leiyi-Hu/mona
---

# 5%>100%: Breaking Performance Shackles of Full Fine-Tuning on Visual Recognition Tasks

Paper Reading 是从个人角度进行的一些总结分享，受到个人关注点的侧重和实力所限，可能有理解不到位的地方。具体的细节还需要以原文的内容为准，博客中的图表若未另外说明则均来自原文。

| 论文概况 | 详细 |
| --- | --- |
| 标题 | 《5%>100%: Breaking Performance Shackles of Full Fine-Tuning on Visual Recognition Tasks》 |
| 作者 | Dongshuo Yin, Leiyi Hu, Bin Li, Youqun Zhang, Xue Yang |
| 发表会议 | IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) |
| 会议等级 | CCF-A |
| 发表年份 | 2025 |
| 论文代码 | [https://github.com/Leiyi-Hu/mona](https://github.com/Leiyi-Hu/mona) |

作者单位：

1. Department of Automation, Shanghai Jiao Tong University
2. BNRist, Department of Computer Science and Technology, Tsinghua University
3. University of Chinese Academy of Sciences
4. Alibaba Group

## 研究动机

预训练 + 全微调是视觉识别任务的标准迁移范式：骨干先在 ImageNet-22k 等大规模数据集上预训练，再以全部参数参与梯度更新的方式适配到目标检测、实例分割、语义分割等下游任务，目前大多数视觉任务的性能记录都由这一范式保持。然而，随着视觉基础模型的规模不断攀升，全微调需要为每个下游任务存储一整套骨干参数，存储受限的终端设备难以承受这样的成本，以更小的参数开销完成高质量迁移逐渐成为视觉迁移学习的关键问题。delta-tuning（参数高效微调，PEFT）为此提供了一条可行路径：它固定预训练骨干的大部分参数，只更新少量新增参数或原有参数的子集，按照更新对象可分为固定部分层并微调其余参数、对原参数做低秩重参数化、固定骨干并新增可训练结构三类。视觉侧的 delta-tuning 自 VPT、AdaptFormer、LoRand 等工作以来已在分类任务上逼近全微调，但现有视觉适配器仍存在两个层面的局限：一是 Adapter、AdaptFormer 等方法的内部结构沿用 NLP 的线性滤波器（下投影、非线性激活、上投影与跳连），并未针对视觉信号的二维结构做适配；二是上游固定层无法随新任务调整其输出分布，偏置会被直接传入适配器，而单一线性压缩层会把不同尺度的视觉信息压进同一个语义空间，缺乏多认知视角的处理。因此，视觉识别领域仍缺少一种面向视觉信号设计、能够在稠密预测任务上系统超越全微调的适配方案。

## 文章贡献

针对视觉 delta-tuning 在稠密预测任务上无法突破全微调性能上限这一局限，本文提出了多认知视觉适配器（Multi-cognitive Visual Adapter，Mona）调优范式。其核心是把面向自然语言的线性适配器改造为面向视觉信号的多认知卷积适配器，并在适配器入口做输入优化。首先，本文在每个 SwinBlock 的 MSA 与 MLP 之后各接入一个 Mona 模块，固定预训练骨干，只更新 Mona 与下游任务头；同时，在 Mona 顶端用 LayerNorm 与两个可学习缩放因子调整固定层输出的分布与占比；接着，以 $3 \times 3$、$5 \times 5$、$7 \times 7$ 三路深度可分离卷积从多认知视角处理特征、取平均后由 $1 \times 1$ 卷积聚合；最终经 GeLU 与上投影还原并以残差输出。实验表明，Mona 以低于骨干 5% 的可训练参数，在 COCO 实例分割、ADE20K 语义分割、Pascal VOC 目标检测、DOTA 与 STAR 有向目标检测以及三个分类数据集上均超越全微调，是唯一在所有代表性视觉任务上全面超越全微调的适配器类方法。

## 本文方法

Mona-tuning 建立在 adapter-tuning 范式之上，整体思路是把面向语言的线性适配器改造成面向视觉信号的多认知适配器。针对典型线性适配器在视觉任务上的两个问题——固定层传入的特征分布存在偏置、线性滤波器对视觉知识的迁移效率不高——本文分别进行输入优化与多认知视觉滤波器设计，再配合参数量受控的投影结构组成完整的 Mona 模块，以下按数据流顺序展开。

### 适配器微调的优化目标

这一小节先把全微调与适配器微调的差异形式化，明确两种范式各自优化的参数集合。给定数据集 $D = \{(x_i, y_i)\}_{i=1}^{N}$，全微调与适配器微调的优化过程分别定义为：

$$\theta \leftarrow \arg\min_{\theta} \mathrm{loss}(D, \theta)$$

$$\omega \leftarrow \arg\min_{\omega} \mathrm{loss}(D, \theta_F, \omega)$$

其中，相关符号的含义如下表所示：

| 符号 | 含义 |
| --- | --- |
| $\mathrm{loss}$ | 训练损失 |
| $\theta$ | 整个框架的参数 |
| $\theta_F$ | 适配器微调中被固定的预训练参数 |
| $\omega$ | 适配器微调中实际更新的参数，含适配器内部与骨干之外的部分 |

全微调更新整个框架的 $\theta$，而适配器微调固定 $\theta_F$、只更新 $\omega$。这等价于把两种范式的差异归到「固定哪些参数」这一选择上，Mona 的全部可训练结构都包含在 $\omega$ 之中，是后续输入优化、多认知滤波与参数量分析共同的优化前提。

### 输入优化：缩放层归一化

该模块的目标是调整从固定层传入 Mona 的输入分布与占比。原文指出归一化有助于稳定前向的输入分布与反向传播的梯度，本文因此在 Mona 顶端加入一个归一化层与两个可学习权重 $s_1$、$s_2$，把原始输入 $x_0$ 调整为：

$$x_{\mathrm{norm}} = s_1 \cdot |x_0|_{\mathrm{LN}} + s_2 \cdot x_0$$

其中 $|\cdot|_{\mathrm{LN}}$ 表示 LayerNorm 操作。两个权重分别控制归一化分支与原始分支的占比：前者提供分布稳定的输入，后者保留固定层输出的原始信息；原文在实践中发现 LayerNorm 优于 BatchNorm，因此采用 LN。固定层无法随新任务调整其分布，若把其输出直接送入下投影，偏置会被带进后续滤波器，这一设计正是针对该问题。其输出 $x_{\mathrm{norm}}$ 直接送入下投影，作为多认知视觉滤波器的输入。

### 多认知视觉滤波器

该模块用于从多个认知视角处理下投影压缩后的低维特征，对应人眼从不同尺度处理并整合视觉信号的机制。上游特征经下投影压缩后，被并行送入三路深度可分离卷积（DWConv），卷积核分别为 $3 \times 3$、$5 \times 5$、$7 \times 7$，其中三路卷积的权重记作 $\omega_{\mathrm{dw}}^{i}$（$i \in \{1, 2, 3\}$），聚合用的逐点卷积（PWConv）权重记作 $\omega_{\mathrm{pw}}$，两个卷积步骤均带跳连，其计算形式化为：

$$f_{\mathrm{dw}} = x + \mathrm{avg}\!\left(\sum_{i=1}^{3} \omega_{\mathrm{dw}}^{i} \,\hat{\otimes}\, x\right)$$

$$f_{\mathrm{pw}} = x + \omega_{\mathrm{pw}} \otimes x$$

其中 $\hat{\otimes}$ 与 $\otimes$ 分别表示深度可分离卷积与逐点卷积。相比标准卷积，DWConv 按通道独立计算，可把新增参数量压到最低；多尺度并联对应「不同滤波尺度下模型对特征具有不同认知」这一动机，三路响应先取平均再由 $1 \times 1$ 卷积聚合，可以融合三个尺度上的局部上下文。直观上，两处跳连使滤波器只需学习对输入特征的增量修正。该模块接收下投影输出的低维特征，其输出送入 GeLU 激活与上投影完成维度还原。

### Mona 的整体计算流程

把输入优化、多认知滤波与投影还原串联起来，就是单个 Mona 模块的完整数据流。设第 $l$ 个适配器的下投影与上投影分别为 $D^l$ 与 $U^l$，GeLU 激活记作 $\sigma$，Mona 从输入到输出的整体计算过程形式化为：

$$x = x_0 + U^l \,\sigma\!\left(f_{\mathrm{pw}}\!\left(f_{\mathrm{dw}}\!\left(D^l(x_{\mathrm{norm}})\right)\right)\right)$$

其中 $x_0$ 为 Mona 的原始输入，$x_{\mathrm{norm}}$ 为缩放归一化后的输入。数据流上，$x_0$ 先经缩放归一化得到 $x_{\mathrm{norm}}$，由 $D^l$ 压缩到低维空间，经多认知滤波器聚合后由 $\sigma$ 非线性化，再由 $U^l$ 还原维度。直观上，还原结果以残差形式加回原输入，输出可表示为「原始表征 + 适配增量」。这一输出直接汇入 SwinBlock 的主干表征流，原始表征能力被完整保留，下游任务头接收的是增强后的特征。

### 在 SwinBlock 中的插入方式

Mona 以「子层后置 + 残差汇入」的方式插入 SwinBlock，即在 MSA 与 MLP 之后各放置一个 Mona 模块。整体插入位置与 Mona 内部结构如下图所示：

![SwinBlock 中 Mona 的插入位置与 Mona 内部结构](../assets/paper-imgs/Mona/mona_fig2_arch.png)

左图给出插入位置，每个 SwinBlock 的 W/SW-MSA 与 Feed-Forward 子层之后各接一个 Mona Layer；右图给出 Mona 内部细节，自底向上依次为 scaled LayerNorm、Down Projection、$3 \times 3$/$5 \times 5$/$7 \times 7$ 三路 DW 卷积、平均、$1 \times 1$ Conv、GeLU 与 Up Projection，原文在 Mona 内部共加入四处跳连以强化适配能力。后置插入使 Mona 能够直接修正每个子层的输出，训练阶段固定预训练层与原 MSA/MLP 参数，仅更新 Mona 与下游检测/分割/分类头，可训练参数因此控制在骨干参数的 5% 以内。

### 参数量分析

该小节统计每个 Mona 模块的可训练参数构成。设适配器输入维度为 $m$、下投影后的中间维度为 $n$，各组件的参数量如下表所示：

| 组件 | 参数量 |
| --- | --- |
| LayerNorm 与缩放因子 | $2m + 2$ |
| 下投影与上投影 | $2mn + m + n$ |
| 三路深度可分离卷积 | $(3^2 + 5^2 + 7^2)n = 83n$ |
| $1 \times 1$ 卷积 | $n^2$ |

把各组件的贡献相加，每个 Mona 模块的参数总量为：

$$(2n + 3)m + n^2 + 84n + 2$$

其中 $m$ 为适配器输入维度，$n$ 为下投影后的中间维度。直观上，参数量对 $m$ 只有线性依赖、对 $n$ 是二次依赖，控制 $n$ 即可控制新增参数规模。由于每个 SwinBlock 在 MSA 与 MLP 之后各插入一个 Mona，单个 Block 的 Mona 参数为 $2 \times \left[(2n + 3)m + n^2 + 84n + 2\right]$，原文将 $n$ 固定为 64 以控制参数规模；这一参数构成直接对应实验部分各主结果表中报告的可训练参数百分比。

## 实验结果

### 实验设置

本文在五类代表性视觉任务上系统评估 Mona-tuning，覆盖稠密预测与图像分类等多种难度，骨干统一采用 ImageNet-22k 预训练的 Swin Transformer 系列。出于显存占用的考虑，COCO、DOTA 与 STAR 使用 Swin-B，其余任务使用 Swin-L；基线包含不引入额外结构的 FULL、FIXED、BitFit、NormTuning、Partial-1 与引入额外结构的 Adapter、LoRA、AdaptFormer、LoRand，各适配器类方法的中间维度统一取 64。数据集、框架与指标配置如下表所示，验证基于 MMDetection、MMSegmentation、MMRotate 与 MMClassification 工具链完成。

| 数据集 | 任务 | 骨干 | 框架 | 指标 |
| --- | --- | --- | --- | --- |
| MS COCO | 实例分割 | Swin-B | Cascade Mask R-CNN | APBox、APMask |
| Pascal VOC 0712 | 目标检测 | Swin-L | RetinaNet | APBox |
| ADE20K | 语义分割 | Swin-L | UperNet | mIoU |
| DOTA-v1.0、STAR | 有向目标检测 | Swin-B | Oriented R-CNN、KLD、H2RBox-v2 | APBox |
| Flowers102、OxfordPets、VOC2007 | 图像分类 | Swin-L | 未获取 | top-1、top-5 |

### COCO 实例分割结果

COCO 实例分割是本文最具挑战性的任务之一，各方法在 Cascade Mask R-CNN 框架下的对比如下表所示，Mona 与九种基线同台比较。

![COCO 实例分割主结果对比表](../assets/paper-imgs/Mona/mona_tab1_coco.png)

可见 Mona 仅用占骨干 4.67% 的可训练参数便取得 APBox 53.40% 与 APMask 46.00%，较全微调提升 1.00% 与 0.90%，是表中唯一超过全微调的方法。表中可训练参数最多的 Partial-1（14.53%）性能反而低于参数更少的 LoRand（5.23%）与 Mona，表明 delta-tuning 的性能与新增参数规模并无直接关系，模块设计本身比参数占比更关键。

### 目标检测与语义分割结果

在 Pascal VOC 目标检测与 ADE20K 语义分割上，各方法统一采用 Swin-L 骨干，结果如下表所示，这两组实验分别检验稀疏预测与逐像素预测上的迁移效果。

![Pascal VOC 与 ADE20K 主结果对比表](../assets/paper-imgs/Mona/mona_tab2_voc_ade.png)

可见 Mona 以 2.56% 的可训练参数取得 VOC 上 APBox 87.30%（较全微调 +3.60%）与 ADE20K 上 mIoU 51.36%（+0.18%），两项指标均为表中最高。VOC 上包括 FIXED 在内的所有基线都超过全微调，原文将其解释为低资源场景下全微调 198 M 的 Swin-L 易于过拟合，而固定大部分预训练参数的调优方式更不易发生性能崩溃。

### 有向目标检测结果

有向目标检测在标注与推理中考虑角度信息，比水平框检测更具挑战性。本文在 DOTA-v1.0 与实例更多、类别更丰富的 STAR 数据集上，跨 Oriented R-CNN、KLD、H2RBox-v2 三类检测框架进行对比，结果如下表所示。

![DOTA 与 STAR 有向目标检测主结果对比表](../assets/paper-imgs/Mona/mona_tab4_dota_star.png)

可见 Mona 在四组设置中全部取得最高 APBox：DOTA-v1.0 上达 78.44%，STAR 上 Oriented R-CNN 达 39.45%（较全微调 +0.82%）、H2RBox-v2 达 31.34%（+1.05%），表明 Mona-tuning 的适配能力不依赖具体检测头，对旋转框表示与角度回归同样有效。

### 图像分类结果

分类任务相对简单，三个数据集上的 top-1 与 top-5 结果如下表所示，这组实验用于观察简单任务上不同调优方式的差距。

![三个分类数据集上的主结果对比表](../assets/paper-imgs/Mona/mona_tab3_cls.png)

可见 Mona 在 Flowers102 与 OxfordPets 上取得最高 top-1，并以平均 top-1 94.0413%、top-5 99.7592% 领先所有基线；所有 delta-tuning 方法的平均 top-1 均超过全微调，验证了先前「简单任务上 delta-tuning 已接近全微调」的结论，也说明稠密预测任务才能更明显地区分不同调优方式的优劣。

### 可视化分析

下图展示了各方法在 ADE20K mIoU 与 COCO mAP 两个代表任务上的总体分布，其中横轴为 ADE20K mIoU，纵轴为 COCO mAP，蓝色虚线标记全微调在两个任务上的性能水平。

![各方法在代表任务上的性能分布对比](../assets/paper-imgs/Mona/mona_fig1_comparison.png)

可见代表 Mona 的红星位于蓝色虚线的右上方（51.36, 53.4），其余 PEFT 基线全部落在虚线的左下方，说明 Mona 是唯一同时突破两个代表任务全微调上限的方法，适配器范式具备替代全微调的可行性。

下图给出了 Pascal VOC 上 Mona 与五个代表基线的训练损失曲线，右侧虚线框放大了训练中后段的细节。

![各方法在 Pascal VOC 上的训练损失曲线](../assets/paper-imgs/Mona/mona_fig3_loss.png)

可见 Mona 的损失收敛最快且最终损失最低，在放大区域内明显低于全微调与 Adapter、LoRA、AdaptFormer 等基线，表明多认知视觉滤波器能帮助模型更快地学到稳定的视觉表征，与其精度上的优势相互印证。

### 消融实验

原文的全部消融实验均在 Pascal VOC 上进行，分别考察中间维度、骨干尺寸与结构细节三个因素。中间维度消融的结果如下表所示，候选维度为 32、64 与 128，其余设置保持固定。

![中间维度消融结果表](../assets/paper-imgs/Mona/mona_tab5_dim.png)

可见 64 维取得 87.3% 的 APBox，高于 32 维的 86.8% 与 128 维的 87.1%，说明适配器容量与性能并不呈正比，这与 AdaptFormer 在分类任务上的结论一致。

骨干尺寸消融覆盖 Swin-T、Swin-B 与 Swin-L 三个规模，结果如下表所示，同时报告 Mona 的参数占比随骨干规模的变化。

![骨干尺寸消融结果表](../assets/paper-imgs/Mona/mona_tab6_modelsize.png)

可见 Mona 在三个尺寸上均超过全微调，且骨干越大 Mona 的参数占比越小（Swin-T 上 4.87% 降至 Swin-L 上 2.56%）；从 Swin-T 到 Swin-L，全微调带来 3.6% 的提升而 Mona 带来 3.8%，表明模型规模越大，Mona 相对全微调的增益越明显。

结构细节消融对比缩放归一化的开关与多种卷积核组合，结果如下表所示，每种核组合取其各路卷积结果的平均。

![Mona 结构细节消融结果表](../assets/paper-imgs/Mona/mona_tab7_design.png)

可见打开缩放归一化后 APBox 从 86.9% 升至 87.3%；核组合中 [3,5,7] 取得最高的 87.3%，单纯使用大核（[7] 为 86.7%）或堆叠同尺度核（[3,3,3] 为 86.8%）都更差，验证了缩放归一化与多尺度核组合设计的合理性与必要性。

### 跨框架扩展性

为检验上述设计是否绑定于 Swin 架构，本文把 Mona 迁移到 PVT-Large 骨干上，结果如下表所示。

![PVT 骨干上的扩展结果表](../assets/paper-imgs/Mona/mona_tab8_pvt.png)

可见 Mona 达到 80.3% 的 APBox，超过全微调的 76.1% 与 AdaptFormer（79.2%）、LoRand（79.3%）等基线，说明该适配器设计对金字塔 ViT 类骨干同样有效，具有跨框架的通用性。

## 优点和创新点

个人认为，本文有如下一些优点和创新点可供参考学习：

1. 将面向语言的线性适配器改造为多尺度深度可分离卷积的多认知视觉滤波器，三路并联取平均再聚合的结构兼顾多认知视角与轻量化，令人耳目一新；
2. 在适配器入口引入 LayerNorm 与可学习缩放因子的输入优化设计，兼顾输入分布的稳定与原始信息的保留，可作为视觉适配器的通用前置模块复用；
3. 在实例分割、语义分割、目标检测、有向目标检测与图像分类五类任务上系统对照九种基线，以极少的可训练参数全面超越全微调，实验数据丰富有力，说服力强；
4. 消融覆盖中间维度、骨干尺寸、结构细节与跨框架扩展四个层面，揭示了适配器容量与性能不呈正比等经验规律，为适配器结构设计提供了可供参考的依据。
