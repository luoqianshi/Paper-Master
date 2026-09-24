---
title: "VarifocalNet: An IoU-aware Dense Object Detector"
category: 损失函数
date: 2026-09-02
source_url: https://github.com/hyz-xmaster/VarifocalNet
---

# VarifocalNet: An IoU-aware Dense Object Detector

Paper Reading 是从个人角度进行的一些总结分享，受到个人关注点的侧重和实力所限，可能有理解不到位的地方。具体的细节还需要以原文的内容为准，博客中的图表若未另外说明则均来自原文。

| 论文概况 | 详细 |
| --- | --- |
| 标题 | 《VarifocalNet: An IoU-aware Dense Object Detector》 |
| 作者 | Haoyang Zhang, Ying Wang, Feras Dayoub, Niko Sünderhauf |
| 发表会议 | IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) |
| 会议等级 | CCF-A |
| 发表年份 | 2021 |
| 论文代码 | [https://github.com/hyz-xmaster/VarifocalNet](https://github.com/hyz-xmaster/VarifocalNet) |

作者单位：

1. Australian Centre for Robotic Vision, Queensland University of Technology
2. University of Queensland

## 研究动机

目标检测中，密集检测器通常先用前背景二分类生成大量候选框，再以非极大抑制（NMS）按分数排序去重。然而，使用分类分数排序存在错位风险：分类置信度高的候选框未必定位精准，而定位精准的候选框也可能因分类分数偏低在 NMS 中被误删，导致整体性能下降。

为缓解这一错位，现有方案通常引入一个额外的定位质量分支，例如 IoU-Net 预测一个 IoU 分数，或 FCOS 预测一个 centerness 分数，再将其与分类分数相乘作为 NMS 排序依据。但是这类乘积式启发策略存在三点局限：第一，两个不完美预测的乘积未必优于任一单独预测；第二，新增分支会引入额外计算开销；第三，分类与定位两类信号被分离学习，难以端到端协同优化。

自然地，问题的关键转向：能否让分类分数本身同时反映定位精度？暂未有工作将这一目标表示为可微学习信号并以单一分数替代 NMS 的两段式打分。本文即围绕该问题展开。

## 文章贡献

针对上述「分类分数与定位精度分离」的局限，本文提出了 VarifocalNet（VFNet），其核心是直接学习一个 IoU 感知的分类分数（IACS），把候选框的存在置信度与定位精度融合进同一度量。首先，本文以受 Focal Loss 启发的 Varifocal Loss 作为非对称加权训练目标，使正样本按 IoU 强度参与损失计算、负样本仍以聚焦因子降权。其次，本文以星形 9 点可变形卷积特征表示候选框的几何与上下文，并在 FCOS+ATSS 之上加入残差式边界框精调分支，构成完整检测头。最终，VFNet 在 MS COCO test-dev 上相对强基线 ATSS 稳定提升约 2.0 AP，最佳模型在 1800×1200 单尺度推理下达 55.1 AP。

## 本文方法

### IACS——IoU 感知分类分数的定义

IACS 的目标是让分类分数天然携带定位精度信息。具体地，对任一候选框，其分类分数向量在真实类别位置上的值被定义为预测框与真值框的 IoU，其他类别位置置零。直观上，IACS 把「存在置信度」与「定位精度」压成同一标量；NMS 直接以该标量排序时，定位精准的候选框不必再借额外 IoU 或 centerness 分支修正。下图所示的对比即可说明这一差异：图 (a) 让网络学习硬类别标签，得到的「Person:0.73」未必定位准确；图 (b) 让网络直接回归 IACS，分数天然反映定位质量。

![](../assets/paper-imgs/VarifocalNet/vfnet_fig1_iacs.png)

本文后续用到的核心符号汇总如下：

| 符号 | 含义 |
| --- | --- |
| $p$ | 模型对前景类别的预测概率 |
| $q$ | IACS 的训练目标（前景点取 IoU，背景点取 0） |
| $\alpha$ | 负样本损失的缩放因子，平衡正负样本 |
| $\gamma$ | 聚焦因子，下调易分负样本的损失 |
| $(l', t', r', b')$ | 初始回归框到采样点的四向距离 |
| $(\Delta l, \Delta t, \Delta r, \Delta b)$ | 精调分支输出的距离缩放因子 |

把定位精度写进分类分数，直接动机是 oracle 实验显示候选池并不缺少定位精准的框，缺的是能把这些框排到前面的分数；IACS 因此成为贯穿全文的中心量，它既是 Varifocal Loss 的回归目标，也是推理阶段 NMS 的排序依据。

### Varifocal Loss

Focal Loss 是为缓解密集检测器训练中正负样本极度不平衡而提出的动态缩放二元交叉熵，其定义为：

$$
\text{FL}(p, y) = \begin{cases} -\alpha(1-p)^\gamma \log(p), & y = 1, \\ -(1-\alpha) p^\gamma \log(1-p), & \text{otherwise}, \end{cases}
$$

其中 $y \in \{\pm 1\}$ 是类别真值，$p$ 是前景预测概率。调制项 $(1-p)^\gamma$ 与 $p^\gamma$ 抑制了易分样本的损失贡献，让检测器聚焦于难分样本。

Varifocal Loss 受此启发，但处理正负样本时是非对称的：它仅对负样本用 $p^\gamma$ 降权，正样本不做相同降权，而是用目标 $q$ 自身做加权。形式化定义如下：

$$
\text{VFL}(p, q) = \begin{cases} -q \left( q \log(p) + (1-q) \log(1-p) \right), & q > 0, \\ -\alpha p^\gamma \log(1-p), & q = 0, \end{cases}
$$

其中 $p$ 是预测的 IACS，$q$ 是目标分数：前景点在其真值类别位置取预测框与真值框的 IoU，背景点所有类别位置取 0。两个细节使该损失具备优势：第一，$q>0$ 时不引入 $(1-p)^\gamma$ 这类对称降权，保留本就稀缺的正样本学习信号；第二，正样本损失被 $q$ 加权，意味着高 IoU 候选框对损失的贡献更大，训练注意力更集中于高质量正例。$\alpha$ 的引入仅用于在正负之间再平衡。直观上，这等价于让网络同时被「分类对不对」与「定位准不准」联合监督，但权重分配偏向后者主导的样本。正样本不做降权的原因是它相对负样本本就稀缺，降权会进一步削弱其学习信号；以目标 $q$ 加权的思路则借鉴了 PISA 的样本重加权视角。与同期的 GFL 相比，二者虽然都把定位质量并入分类分数，但 GFL 对正负样本同等对待，而 Varifocal Loss 对二者反向加权，这一非对称性是它与 GFL 的分水岭。

### 星形边界框特征表示

现有密集检测器一般以采样点的单点特征描述一个候选框，效率高但缺乏几何与上下文信息；HSD、RepPoints 等方案用可学习语义点配可变形卷积，又缺乏强监督且增加额外预测负担。本文设计了星形 9 点采样方案：给定采样位置 $(x, y)$，先用 $3\times 3$ 卷积回归出初始距离向量 $(l', t', r', b')$，然后依其在四个边方向上偏移出 9 个采样点 $(x, y), (x-l', y), (x, y-t'), \ldots, (x+r', y+b')$，把它们的相对偏移作为可变形卷积的偏移量，卷积输出即作为候选框的描述向量。

这一表示的优势在于：9 个点位置由几何规则直接确定，不需要学习也不增加额外预测；可变形卷积又能让 9 个点的感受野自适应框体几何与附近上下文。9 个点恰好覆盖框体的几何骨架：中心点描述目标本体，四边中点刻画范围，四角点界定边界，它们到投影点的相对偏移共同编码了预测框与真值框之间的错位，这正是回归 IACS 与精调所依赖的信息。后续的 IACS 预测和边界框精调都基于这一特征表示。它向上承接初始框回归，输出送入两个并行的子网：IACS 预测与精调。

### 边界框精调

基于星形特征，进一步以残差方式学习 4 个距离缩放因子 $(\Delta l, \Delta t, \Delta r, \Delta b)$，将初始距离向量逐项相乘得到精调后距离：

$$
(l, t, r, b) = (\Delta l \cdot l', \Delta t \cdot t', \Delta r \cdot r', \Delta b \cdot b').
$$

其中 $(l', t', r', b')$ 是初始距离向量，$(\Delta l, \Delta t, \Delta r, \Delta b)$ 是四个距离缩放因子，二者逐项相乘得到精调后的四向距离。该步骤把两阶段检测器常见的 cascade 思路引入一阶段框架中，关键在于星形特征提供了高效的框体描述，使精调能在不付出 ROI Pooling 代价的前提下完成。精调长期未在一阶段检测器中普及，原因是缺少高效且有判别力的框描述子；星形表示补上这一环后，精调才得以在一阶段框架内低成本落地。该精调分支接收星形表示，输出最终定位结果。

### VFNet 网络结构

如下图所示，VFNet 在 FCOS+ATSS 上去掉 centerness 分支，将头部分为两个并行子网。定位子网用三层 3×3 卷积+ReLU 将 FPN 各层特征升到 256 通道后，一路卷积出初始距离向量 $(l', t', r', b')$，另一路把星形表示与初始框送入星形可变形卷积，输出 4 个缩放因子，与初始距离相乘即得精调框。分类子网结构与精调分支同源，但输出 $C$ 维的 IACS 向量。

![](../assets/paper-imgs/VarifocalNet/vfnet_fig3_arch.png)

该网络向上承接 FPN 输出的多尺度特征图 $P_3$–$P_7$，向下输出初始框、精调框与 IACS 三组结果，分别送入下一步的总损失。去掉 centerness 分支是因为其定位质量估计职能已由 IACS 承担，保留它反而回到乘积式排序的老路。两个子网在结构上完全对称，因此新增的精调分支并不会为分类分支带来额外的延迟或显存开销，整套头部仍可在单尺度训练下端到端收敛，后续在多种骨干网络上的对比实验也沿用同一套头部配置。

### 损失函数与推理

训练总损失定义为：

$$
\text{Loss} = \frac{1}{N_{\text{pos}}} \sum_i \sum_c \text{VFL}(p_{c,i}, q_{c,i}) + \frac{\lambda_0}{N_{\text{pos}}} \sum_i q^*_{c,i} \mathcal{L}_{\text{bbox}}(b'_i, b^*_i) + \frac{\lambda_1}{N_{\text{pos}}} \sum_i q^*_{c,i} \mathcal{L}_{\text{bbox}}(b_i, b^*_i),
$$

其中 $p_{c,i}$ 与 $q_{c,i}$ 分别是位置 $i$ 上类别 $c$ 的预测 IACS 与目标 IACS；$\mathcal{L}_{\text{bbox}}$ 为 GIoU Loss；$b'_i, b_i, b^*_i$ 分别是初始框、精调框与真值框；$q^*_{c,i}$ 在前景点取 IoU、背景点取 0，遵循 FCOS 用作 GIoU 损失权重的做法；$\lambda_0, \lambda_1$ 在本文中经验取为 1.5 与 2.0；$N_{\text{pos}}$ 是前景点总数，用于归一化。前景与背景的划分沿用 ATSS 机制。直观上，三项分别监督 IACS 分类、初始框粗定位与精调框细定位，$q^*$ 加权把两个定位损失也集中到高质量正样本上，与 VFL 的加权方向保持一致。推理阶段先剔除 $p_{\max} \le 0.05$ 的候选框、每层保留至多 1k 个高分检测，合并后执行阈值 0.6 的 NMS 即得最终结果。

## 实验结果

### 实验设置

| 项目 | 设置 |
| --- | --- |
| 数据集 | MS COCO 2017（train2017 训练，val2017 消融，test-dev 对比） |
| 指标 | COCO 风格 AP，含 AP、AP50、AP75、APS、APM、APL |
| 框架 | MMDetection |
| 训练卡数 | 8 张 V100，batch size 16（每卡 2 张） |
| 消融训练 | ResNet-50 骨干、1× 12 epoch，输入最大 1333×800，仅随机水平翻转 |
| 对比训练 | 多种骨干（含 Res2Net-101-DCN），2× 24 epoch + 多尺度训练 |
| 推理 | 输入最大 1333×800，NMS 阈值 0.6，每层最多保留 1k 检测 |

### IACS 排序效果与可视化分析

为定位 FCOS+ATSS 性能瓶颈，本文以 oracle 实验替换前背景/centerness 分数的真值，统计其对 COCO val2017 的影响，结果如下表所示。

| 配置 | AP |
| --- | --- |
| FCOS+ATSS 原始 | 39.2 |
| + 真值 centerness | 41.1（仅 +1.9） |
| + 用 gt IoU 替换 centerness | 43.5 |
| + 真值边界框 + 真值 centerness | 56.1 |
| + 真值边界框 + 类别分置 1（含/不含 centerness） | 43.1 / 58.1 |
| + 真值 IoU 作为分类分 | 74.7 |

![](../assets/paper-imgs/VarifocalNet/vfnet_tab1_oracle.png)

同一表中可以观察到一个关键现象：把分类分数在真值类别位置替换为 IoU 后，无 centerness 分数也能达 74.7 AP，显著高于任何乘积式方案。可见密集检测器候选池中已存在大量定位精准的框，关键在于排序度量能否区分高质量检测；IACS 是最直接的解决方案。

下图进一步给出 FCOS 头在同一对象上输出的若干候选框及其分类分、centerness 分数，可以观察到「分类分高但定位差」与「分类分高且定位好」并存的情况：

![](../assets/paper-imgs/VarifocalNet/vfnet_fig2_fcoshead.png)

定性可视化表明，单纯依赖 centerness 抑制并不能充分识别定位精准的框，需要在分数层面直接编码定位精度，而 IACS 恰好满足这一需求。

### 消融实验

Varifocal Loss 对 $\alpha, \gamma$ 与正例加权 $q$ 的消融如下表所示。

![](../assets/paper-imgs/VarifocalNet/vfnet_tab2_hyperparam.png)

可见 $\alpha=0.75, \gamma=2.0$ 配 $q$ 加权取得 41.6 AP 的最优组合；正例不加 $q$ 加权时降至 41.2 AP，验证 $q$ 加权必要。三模块的逐项贡献如下表所示。

![](../assets/paper-imgs/VarifocalNet/vfnet_tab3_component.png)

从去掉 centerness 分支、用 Focal Loss 训练的原始 VFNet（39.0 AP）为起点，换用 VFL 后升到 40.1 AP，再加星形表示与精调后达到 40.7 与 41.6 AP，可以看出三模块均为正贡献；FCOS+ATSS 基线为 39.2 AP。

### 与主流检测器的对比

在 COCO test-dev 上单模型单尺度结果如下表所示。

![](../assets/paper-imgs/VarifocalNet/vfnet_tab4_sota.png)

在多个骨干上 VFNet 相对 ATSS 稳定提升约 2.0 AP；最佳模型 VFNet-X-1200 配 Res2Net-101-DCN 在 1800×1200 推理下达 55.1 AP，超越同期同尺度单模型。

### VFNet-X 的扩展配置

在原版 VFNet 之上，本文给出扩展版 VFNet-X：换用 PAFPN 并在其中加入可变形卷积与组归一化，头部卷积从 3 层加到 4 层、通道从 256 加宽到 384，训练中加入 RandomCrop 与 Cutout 数据增强、更宽的多尺度训练范围与更长的 41 epoch 日程，最后用 SWA 平均 18 个检查点。上述配置中 SWA 单项增益最大（+1.2 AP）；完整配置的 VFNet-X-800 在 test-dev 上以 1333×800 与 soft-NMS 取得 53.7 AP，仅把推理尺度放大到 1800×1200 后 VFNet-X-1200 即达到 55.1 AP，验证了各扩展项的叠加收益。

### 损失函数的通用性与优越性

将 Varifocal Loss 替换 RetinaNet、FoveaBox、RepPoints、ATSS 的损失函数后，AP 普遍提升 0.9–1.4，结果如下表所示，验证 VFL 不依赖具体检测头即具有可移植性。

![](../assets/paper-imgs/VarifocalNet/vfnet_tab5_vfl.png)

与同期 GFL 的对比中，VFL 在所有基线上一致优于 GFL，佐证了非对称加权设计的有效性。

### 速度-精度权衡

由 Table 4 的 FPS 列可知，VFNet-R-50 在 19.3 FPS 下取得 44.8 AP，相较同骨干 ATSS 仅增加少量计算即获得约 2.0 AP 提升；与 R-101-DCN 骨干配合时 12.6 FPS 下达到 49.2 AP。整体上 VFNet 在精度增益与速度开销之间具有较好的折中，相较同期 EfficientDet-D7（3.8 FPS 达 52.2 AP），VFNet-X-1200 以接近的精度换来了显著更高的吞吐，更适合实际部署中的实时检测场景。同时，模型的额外开销主要来自星形可变形卷积与精调分支的几条 3×3 卷积，没有引入 ROI Pooling 或额外的特征采样，整体推理路径保持了一阶段检测器的简洁性。

## 优点和创新点

个人认为，本文有如下一些优点和创新点可供参考学习：

1. 本文将「分类置信度」与「定位精度」合并为单一可微的 IACS 训练目标，以一个标量同时承担 NMS 排序与置信度输出，从根本上消除了乘积式方案中两类信号难以协同优化的痛点；
2. Varifocal Loss 对正负样本非对称加权，正样本以 $q$ 自身加权而非 $(1-p)^\gamma$ 降权，聚焦高 IoU 正例；该损失在 COCO 上超越 Focal Loss 与 GFL，可即插即用到多个主流检测器；
3. 提出的星形 9 点可变形卷积特征表示既捕获了候选框的几何与上下文，又不需要学习额外的语义点；在一阶段框架上叠加残差式精调分支，引入稳定的二次定位步骤，方法迁移性较好；
4. 实验说服力强，VFNet 在多骨干上稳定提升约 2.0 AP，最佳模型达到 55.1 AP 的同期新 SOTA，并通过 oracle 实验与多损失对比充分论证了 IACS 与 Varifocal Loss 的独立价值。
