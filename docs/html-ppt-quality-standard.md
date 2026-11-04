# HTML 格式 PPT 质量核查标准

> 版本 v1.0 · 制定日期 2026-11-04 · 适用对象：`paper-slides/*.html`（当前 62 份）
> 本标准为「成品验收规范」，与 `skills/html-paper-slides/SKILL.md`、`skills/blog-to-slides/SKILL.md` 的「生成规范」配套使用。判定一律以本文件为准。

---

## 1. 适用范围与边界

| 项 | 约定 |
|---|---|
| 在范围内 | `paper-slides/` 顶层全部 `.html` 单文件演示文稿的**内容、版式、文字、视觉、交互、展示适配**六个维度 |
| 不在评级范围 | `slides-manifest.json` 登记状态、`assets/thumbnails/` 缩略图、`index.html` 画廊/iframe 引用、`assets/paper-imgs/` 与 `paper-slides/*_assets/` 的孤立素材、README 示例链接、抽取脚本的历史 JSON |
| 外围问题 | 统一列入核查报告「外围附注」章节，**只记录、不参与评级、不扣分** |
| 核查性质 | 只读核查。改进建议写入清单，由后续任务决定是否实施；本标准不包含自动修复动作 |
| 事实层边界 | 不逐份通读 `pdf-papers/` 原始 PDF 核对实验数值；此类一致性统一标注「事实层未逐份核验」，不作推断、不作结论 |

---

## 2. 术语与判定方法

**判定方法标记**

| 标记 | 含义 | 工具 |
|---|---|---|
| `S` | 静态扫描：源文件文本、正则、CSS 规则解析 | `scripts/audit_slides.py --static` |
| `R` | 真实渲染度量：浏览器 DOM、`getComputedStyle`、资源加载结果 | `scripts/audit_render.py` |
| `B` | 比对：磁盘文件集、基准色值表、博客/manifest、跨文件对照 | 扫描脚本 + 人工复核 |

**严重度**

| 级别 | 定义 | 后果 |
|---|---|---|
| `S0` 致命 | 破坏内容理解，或演示无法进行 | 命中即红线，直接「待优化」 |
| `S1` 严重 | 显著影响演示效果或导航正确性 | 红线或重扣（见 §5） |
| `S2` 一般 | 观感、适配或一致性缺陷，不阻断演示 | 扣分 + 进入待优化清单 |
| `S3` 轻微 | 次要偏差 | 轻扣或仅记录 |

**检查项类型**

| 类型 | 定义 |
|---|---|
| 核心项 | 参与六维得分折算，可触发红线 |
| 次要项 | 仅轻微扣分或记录，**不触发红线** |
| `G` 全局项 | 62 份同犯的历史遗留，**从逐份评分中剔除**（理由见 §3.3），改为在报告中单列 + 各写 1 条「全库」优化建议 |

---

## 3. 制定依据与既有规范空白

### 3.1 依据对照表

| 依据 | 关键条款 | 被本标准吸收为 |
|---|---|---|
| `skills/html-paper-slides/SKILL.md:35-59` | 配色 5 色值、系统字体栈、标题 700-800 / 正文 400-500、16:9 + `padding:5vh 7vw`、Grid/Flex、`clamp()` | V4.1、V4.2、T3.2、T3.5、L2.1、L2.3、L2.6 |
| `skills/html-paper-slides/SKILL.md:65-70` | 必需组件：Slide Engine / Progress Bar / Dots / Animations | V4.3、I5.6 |
| `skills/html-paper-slides/SKILL.md:99-130` | 13~22 页、8 段式结构、分页规划表 | C1.2 |
| `skills/html-paper-slides/SKILL.md:132-139` | 每页 3-5 要点、标题配色、glow 装饰、动画递增、封面 badge/cover-tag、保留左右键但不要显式控制器 | C1.4、V4.4、V4.5、I5.5、I5.6 |
| `skills/html-paper-slides/SKILL.md:141-154` | 已知问题 1（零外部依赖避免字体 404）、问题 2（`.slide.active` 三属性 `!important`、JS 禁 inline style） | T3.2、A6.5、I5.1 |
| `skills/blog-to-slides/SKILL.md:46-59` | L1 叙事层 / L2 事实层 / L3 素材层；「信息拿不到就省略，宁可少写，不可编造」 | C1.3、C1.9 |
| `skills/blog-to-slides/SKILL.md:162-183` | 动态页数预算 `min = 7 + ceil(N/2)`、`max = min(8+N, 30)` | C1.2（页数合理性参考，不作硬阈值） |
| `skills/blog-to-slides/SKILL.md:185-196` | 图注与结论不拆散、横长图排版、表格以图片为准 | C1.5、L2.4、T3.6 |
| `skills/blog-to-slides/SKILL.md:200-225` | 已知问题 1-5：字体、翻页空白、图片路径、丢图顽疾、双栏抽取 | T3.2、I5.1、C1.8 |
| `README.md:194-201` | 6 条质量清单：PDF 溯源、笔记门禁、配图归档、HTML 单文件打开/键盘翻页/视觉层级、manifest 全覆盖、缩略图 | C1.1、A6.5、I5.2、T3.5、外围附注 |
| `skills/blog-to-slides/scripts/verify_slides.py:7-16,31-34,42-71,121-129` | 六项门禁（图覆盖率、图片加载、页数上下限、src 前缀、含图页中文 ≥20）、`PAGE_RE` 精确页数正则、Playwright DOM 探测范式 | C1.7、C1.8、A6.1、附录 A |
| `docs/superpowers/specs/2026-10-29-blog-to-slides-pdf-augmented-design.md:420-431,527` | 十项验收标准；「1280×720 下 19 页全部无溢出」人工验证基线 | A6.1、L2.2 |

> **现状结论**：以上材料是「生成规范 + 流程清单 + 单流程门禁」，此前**没有**一份成文、统一、面向全部成品的核查标准，也未覆盖视觉一致性、打印导出、16:9 实现、缩放兜底、页码自洽、误触、投影适配等维度。

### 3.2 本次补齐的既有规范空白（11 项）

| 空白 | 落到条款 |
|---|---|
| 打印 / 导出 PDF（全库 `@media print` 0 命中，导出只剩当前 1 页或空白） | A6.4 `G` |
| 16:9 画布（规范有文字、实现全库为 `100vw/100vh`） | L2.1 `G` |
| 缩放兜底（无 `transform:scale()` / resize 逻辑） | L2.6 `G` |
| 字体加载与零外链依赖的机械判定 | T3.2、A6.5 |
| 图片可用性（磁盘存在 + 渲染 `naturalWidth>0`） | C1.8、A6.1 |
| 页码 / 进度 / dots 与实际页数自洽 | I5.4 |
| 键盘、触摸与整页点击误触 | I5.2、I5.3 |
| 投影 / 窄屏 / 竖屏适配 | A6.2、A6.3 |
| 学术出处 / References 章节 | C1.6 `G` |
| 表格位图不可检索、不可放大 | T3.6 `G` |
| 内容溢出裁切的运行时度量 | L2.2、A6.1 |

### 3.3 关键决策：`G` 全局项剔除逐份评分

62 份成品由两套历史生成器产出，`@media print` 缺失、16:9 画布未落实、无缩放兜底、表格位图、无 References、A/B 双模板差异是**全库同犯**的遗留问题。若把它们逐份计入扣分，L / A / T 三个维度会被普遍压到 70 分以下，**没有任何文件能达到「优秀」门槛，三档评级将失去区分度**，也无法回答「哪些文件更值得先改」。

因此：

1. `G` 项**不进入**逐份六维折算，不影响红线、不影响分档；
2. 在标准中仍完整成文（它们是必须补齐的规范条款）；
3. 在核查报告「共性问题」章节单列，每项给出**一条全库级**改进建议；
4. 在待优化清单中各写 **1 条「全库」条目**（放 P1 / P2 段），不重复 62 次；
5. 逐份评级只由文件自身可区分的差异决定：失效图片、内容溢出、章节缺失、页码错误、字号/对比度、交互误触、配色字体偏离等。

此决策须在核查报告 §6 同步说明，不得在评分时偷偷剔除其它非 `G` 项。

---

## 4. 六维核查条款

> 表中「达标判据」为脚本与人工复核共同遵守的口径；「依据」列引用 §3.1。

### 4.1 C 维 · 内容完整性与逻辑（权重 25）

| 编号 | 检查项与达标判据 | 方法 | 严重度 | 类型 | 依据 |
|---|---|---|---|---|---|
| C1.1 | 封面须含论文标题 + 作者 + 期刊/会议或 arXiv/DOI/年份；`<title>` 与封面标题一致 | S+B | S1 | 核心 | SKILL.md:101-109、README:196 |
| C1.2 | **8 段式叙事链**：封面 → 摘要/概述 → 引言/动机 → 方法 → 实验 → (消融) → 总结与展望 → 结尾。**必需段**＝封面、方法、实验、总结；缺任一即不达标（R-S1）。等效标签：`Method/方法/架构/模块/Pipeline`、`Experiments/实验/Results/结果/Ablation/消融`、`Summary/总结/结论/Conclusion/致谢/感谢观看`；`Contributions` 视为概述段。实验段出现在方法段之前视为顺序错乱 | S+B | S1 | 核心 | SKILL.md:99-130、README:192 |
| C1.3 | 无 `TODO` / `Lorem` / 占位文案 / 公式乱码 / 明显编造数值 | S+R | S1 | 核心 | blog-to-slides:46-59 |
| C1.4 | 每页要点数（`li` / `.card` / `.step`）3-5 个；>8 记「信息过载」 | R | S2 | 核心 | SKILL.md:134 |
| C1.5 | 含图页须有图注或结论文字，图注与图同页 | S+B | S2 | 次要 | blog-to-slides:193 |
| C1.6 | 末页或页脚给出参考文献/出处章节；仅封面含 arXiv/DOI 视为「最低要求已满足、章节缺失」 | S | S3 | `G` | 本次补齐 |
| C1.7 | 无空页/重复页：含图页中文字符 ≥20；无正文且无图的页判空页 | S+R | S2 | 核心 | verify_slides.py:13,64-65 |
| **C1.8** | **每个 `<img src>` 指向磁盘实际存在文件，且渲染 `naturalWidth > 0`**。两套历史路径均允许：`../assets/paper-imgs/<论文名>/` 与 `paper-slides/<同名子目录>/`；指向不存在目录或命名不符文件即不达标 | S+R+B | **S0** | 核心 | blog-to-slides:57,212-215；verify_slides.py 检查 2/5 |
| C1.9 | 实验数值与 PDF/笔记一致（标注「事实层未逐份核验」，不作推断） | B | S3 | 次要 | blog-to-slides:46-59 |

### 4.2 L 维 · 版式布局（权重 18）

| 编号 | 检查项与达标判据 | 方法 | 严重度 | 类型 |
|---|---|---|---|---|
| L2.1 | 有 `aspect-ratio:16/9` 或等效固定纵横比画布 | S+R | S2 | `G` |
| **L2.2** | **无溢出裁切**：主档 1280×720 与 1920×1080 下，每页 `scrollHeight ≤ clientHeight + 2` 且 `scrollWidth ≤ clientWidth + 2`；`overflow:hidden` 不得吞掉标题、图注或结论文字 | R | **S0** | 核心 |
| L2.3 | `.slide` 使用 `padding:5vh 7vw`（或窄屏等价降级），布局用 Grid/Flex | S | S2 | 核心 |
| L2.4 | 横长图（渲染宽高比 >2）独占整页或半页宽度 ≥60%，不塞入窄栏；两图并排不互相挤压 | R | S2 | 核心 |
| L2.5 | 每页聚焦单一主题，图文分栏不失衡 | R | S3 | 次要 |
| L2.6 | 无 scale/resize 时须证明 `clamp()` 在 1280×720 与 1920×1080 均不溢出、不拉伸 | S+R | S2 | `G` |

### 4.3 T 维 · 文字可读性（权重 17）

| 编号 | 检查项与达标判据 | 方法 | 严重度 | 类型 |
|---|---|---|---|---|
| T3.1 | 1280×720 下正文计算字号 ≥13px、标题 ≥24px、次要说明 ≥11px；窄屏 900×700 下正文 ≥11px | R | S1 | 核心 |
| T3.2 | `font-family` 为统一系统栈；**零外部字体/样式/脚本依赖**（无 `@font-face`、`@import`、Google Fonts、CDN JS/CSS、MathJax、KaTeX）。判定时只检查 `src` / `href` / `url()` / `@import` / `@font-face` 的**属性值**，**排除** `<link rel="icon" href="../assets/favicon.png">` 本地相对路径与正文中的 DOI/arXiv 文本 | S+R | S1 | 核心 |
| T3.3 | 对比度（WCAG 相对亮度公式）：正文文字 ≥4.5:1、标题与大字 ≥3:1。判定时区分正文元素（`.body-text`、`li`、`p`）与装饰/标签元素（`.slide-label`、`.cover-tag`、`.badge`），后者按大字/非正文口径；重点核 `#6191D3`、`#888`、`#999` 在 `#ffffff` 上的实际使用位置 | S(算)+R | S2 | 核心 |
| T3.4 | 公式（手写 `<i>/<sub>/<sup>` 或图片）清晰无乱码、无破损实体，且不引入 CDN | S+R | S2 | 核心 |
| T3.5 | 标题 `font-weight` 700-800、正文 400-500、正文 `line-height ≥1.5` | S | S3 | 次要 |
| T3.6 | 表格以 `<img>` 呈现时须有 `alt` 或图注，且 1920×1080 下渲染宽度 ≥ 容器 60% | S+R | S2 | `G` |

### 4.4 V 维 · 视觉一致性（权重 12）

| 编号 | 检查项与达标判据 | 方法 | 严重度 | 类型 |
|---|---|---|---|---|
| V4.1 | `:root` 配色与基准一致：`--bg:#ffffff`、`--text:#000000`、`--title:#3966A2`、`--accent:#132843`、`--dim:#6191D3`、`--card-bg:#f7f9fc`、`--border:#e2e8f0`、`--radius:12px`；A 类变量名不同但色值相同视为达标；统计偏离色值数 | S+B | S2 | 核心 |
| V4.2 | 字体栈跨 62 份一致（允许公式/代码元素使用等宽或 Math 字体） | S+B | S3 | 次要 |
| V4.3 | 必需组件齐备：Slide Engine、Progress Bar、Dots、Animations（B 类至少 progress + dots + 逐页动画） | S | S2 | 次要 |
| V4.4 | 封面 `.badge` / `.cover-tag`、章节 `.slide-label` 使用统一类名与样式 | S | S3 | 次要 |
| V4.5 | 卡片圆角、高亮条、glow 等组件参数与基准模板一致 | S+B | S3 | 次要 |
| V4.6 | A/B 双模板差异（控制条 + 硬编码页码 vs 极简整页 click 翻页）仅作一致性观察记录 | S+B | S3 | `G` |

### 4.5 I 维 · 交互效果（权重 14）

| 编号 | 检查项与达标判据 | 方法 | 严重度 | 类型 |
|---|---|---|---|---|
| **I5.1** | **翻页状态机正确**：`.slide.active` 的 `opacity` / `visibility` / `transform` 三属性均带 `!important`；JS 只用 `classList` 切换、无 `element.style.xxx =` 设置页面可见性；逐页翻页后每页 `visibility==='visible' && opacity==='1'` | S+R | **S0** | 核心 |
| I5.2 | 键盘 `←/→/空格/Home/End` 翻页可用，首尾边界不越界 | R | S1 | 核心 |
| I5.3 | 有 touchstart/touchend 或滑动翻页；B 类 `document` 级 click 翻页在点击 `img` / `a` / `.dot` 时**不得**误翻页 | S+R | S2 | 核心 |
| I5.4 | 页码 / 进度条 / dots 与实际页数自洽：硬编码 `NN / MM` 的 `MM` 须等于真实页数，或由 JS 动态写入。若 JS 明确覆盖（如 `counter.textContent = ... / total`），静态不自洽仅记 S2 扣分；若未覆盖且 `MM` 错误 → R-S2 红线 | S+R+B | S1 | 核心 |
| I5.5 | 不出现显式左右翻页控制器（A 类 `.controls` 记「与规范冲突」，S2 一般扣分，非红线） | S | S2 | 次要 |
| I5.6 | dots 可点击跳转、进度条随页更新、hint 自动隐藏、`.anim:nth-child(n)` 动画延迟递增 | S+R | S3 | 次要 |
| I5.7 | 全屏（F 键）等增强键存在与否仅记录 | S | S3 | 次要 |

### 4.6 A 维 · 不同屏幕下的展示适配（权重 14）

| 编号 | 检查项与达标判据 | 方法 | 严重度 | 类型 |
|---|---|---|---|---|
| **A6.1** | **1920×1080 / 1366×768 / 1280×720** 三档逐页无溢出、图片 `naturalWidth>0` 且渲染宽高比不失真 | R | **S0** | 核心 |
| A6.2 | 1024×768 投影 / 900×700（触发 `max-width:900px`）/ 768×1024 竖屏下文字仍可读（正文 ≥11px）、不溢出裁切 | R | S1 | 核心 |
| A6.3 | 至少 1 条响应式降级 `@media` 且主档 / 窄屏渲染无溢出即达标；「是否覆盖超宽、横竖屏、超高 DPI」仅作观察记录，不扣分 | S | S2 | 核心 |
| A6.4 | 有 `@media print` 使全部 `.slide` 分页可见并隐藏控件；`emulateMedia('print')` 后可见页数应等于实际页数 | S+R | S2 | `G` |
| A6.5 | `file://` 单文件离线可打开：无 `requestfailed`、无 `status ≥400`，本地 favicon 存在；**排除 favicon 本地相对路径误报** | S+R | S1 | 核心 |
| A6.6 | 存在 `<meta name="viewport">` | S | S3 | 次要 |
| A6.7 | 浏览器缩放 125% / 150% 下不溢出（可选档，仅记录） | R | S3 | 次要 |

---

## 5. 红线清单（命中即「待优化」，覆盖分数）

| 编号 | 级别 | 触发条件 | 对应条款 | 为何影响内容理解或演示 |
|---|---|---|---|---|
| `R-F1` | 致命 | 图片加载失败 / 路径失效导致核心图表缺失 | C1.8、A6.1 | 方法框架图、实验表格是论文汇报的证据主体，缺图即无法理解结论 |
| `R-F2` | 致命 | 翻页状态机失效，存在永久不可见页 | I5.1 | 部分页面永远无法展示，演示直接中断 |
| `R-F3` | 致命 | 任一页内容溢出被裁切且无滚动兜底（需 ≥2 档渲染确认） | L2.2、A6.1 | 标题/图注/结论被 `overflow:hidden` 吞掉，观众看不到关键文字 |
| `R-S1` | 严重 | 必需章节缺失或顺序错乱致叙事断裂 | C1.2 | 缺方法/实验/总结即无法构成完整汇报逻辑 |
| `R-S2` | 严重 | 页码 / 进度与实际页数严重不符且 JS 未覆盖（如 `01 / 01`） | I5.4 | 导航信息误导，演讲者无法判断进度 |
| `R-S3` | 严重 | 关键页最小字号或对比度不足致不可读 | T3.1、T3.3 | 投影环境下文字不可辨认 |
| `R-S4` | 严重 | 外部字体 / 样式 / 脚本依赖在 `file://` 下 404，离线或投影不可用 | A6.5、T3.2 | 单文件离线打开失效，现场断网即演示失败 |

**证据门槛**：静态 `suspected` → 渲染确认 → 人工复核，三级齐备才定红线。静态疑似不直接否决（详见 §8）。

---

## 6. 评级规则（红线否决 + 六维加权）

### 6.1 权重

| 维度 | C 内容 | L 版式 | T 可读 | V 一致 | I 交互 | A 适配 | 合计 |
|---|---|---|---|---|---|---|---|
| 权重 | 25 | 18 | 17 | 12 | 14 | 14 | 100 |

C + L + T + A = 74，与「优先处理影响内容理解与演示效果」一致。

### 6.2 折算

```
每维得分 = 100 × (达标核心项权重和 / 核心项总权重) − 次要项罚分   ，clamp 到 [0,100]
核心项未达标扣分：S0 扣该维满分 / S1 扣 60% / S2 扣 30% / S3 扣 10%
次要项未达标：S3 轻扣（每维累计上限 5 分）或仅记录
G 全局项：不进入逐份折算
总分 = Σ(每维得分 × 权重) / 100
```

同一检查项在多个页面重复命中时，按「项」计一次扣分，但命中数量记入评级依据（如 `C1.8×13`），用于清单排序与优先级判断。

### 6.3 分档

| 等级 | 条件 |
|---|---|
| **优秀** | 总分 ≥85 且无红线、无 `S1` 级未达标核心项、C/L/T/A 四维均 ≥80 |
| **合格** | 70 ≤ 总分 <85 且无红线 |
| **待优化** | 总分 <70 **或**命中任一红线（红线优先，覆盖分数） |

- 边界值 85 / 70 取上档；命中红线但总分 ≥85 仍为「待优化」，依据栏写明「红线优先否决 + 红线编号」。
- 同分同档按文件名升序排列。
- **未验证降级**：渲染不可用时，相关维度标「未验证」，不扣分、不计达标，按剩余维权重归一化；该文件**最高只能评「合格」**，并在报告中说明原因。
- 三档若出现「全员一档」的坍缩，必须回到本标准调整阈值并写明理由，**不得**为迁就结果而临时增删检查项。

### 6.4 评级依据的呈现

核查报告总表每份一行，字段：

`序号 | 文件 | 模板A/B | 页数(DOM/正则) | C | L | T | V | I | A | 总分 | 等级 | 命中红线 | 关键扣分点 | 校验状态`

「关键扣分点」用条款编号引用（例：`C1.8×13、I5.4(01/01)、T3.1`）；`G` 项在总表中不出现，统一写入 §6 共性问题。逐项明细存 `.cache/slides-audit/findings.json`。

---

## 7. 待优化清单规范

### 7.1 七字段定义

| 字段 | 定义 |
|---|---|
| ① 序号 | 排序后连续编号 |
| ② **文件及具体页面** | `<文件名> · 第 N 页 · 「页标题」`。页码取渲染 DOM 中 `.slide` NodeList 顺序（1-based），静态用 `PAGE_RE` 命中顺序兜底，冲突以 DOM 为准；页标题取该页 `h2` / `.slide-label` / `.slide-title` 文本，取不到写「（无标题，按序定位）」；封面写「第 1 页 · 封面」；全篇性问题写「全篇」，全库共性问题写「全库 / 不适用」 |
| ③ 问题描述 | 现象 + 证据（具体 `src`、行号、度量值，如 `naturalWidth=0`、`scrollHeight 812 > clientHeight 720`） |
| ④ 对应标准编号 | 可多条，如 `C1.8 / A6.1` |
| ⑤ 影响程度 | **高**＝破坏内容理解或演示不可进行（对应 S0/S1 红线）；**中**＝显著影响观感或适配但不阻断；**低**＝一致性 / 轻微偏差 |
| ⑥ 优化优先级 | **P0 / P1 / P2**：高→P0、中→P1、低→P2；例外须在条目中写明理由（如「演示高频」可上调） |
| ⑦ **具体改进建议** | 必须可执行、带文件路径或代码片段，禁止「建议优化排版」这类空话 |

### 7.2 排序规则

1. **P0 全段置顶**，并加「影响内容理解 / 演示效果」标记；
2. 段内按影响程度 `高 > 中 > 低`；
3. 再按维度权重 `C(25) > L(18) > T(17) > A(14) > I(14) > V(12)`（A 与 I 同权重时 A 优先，投影适配直接影响演示）；
4. 最后按文件名升序、页码升序；
5. 同一文件的多条页级条目聚合在该文件小节下，便于一次性修改；
6. `G` 类共性问题各只写 1 条「全库」条目，放 P1 / P2 段，不重复 62 次。

### 7.3 改进建议范式

- `把 Conv2Former.html 中约 13 处 ../assets/paper-imgs/Conv2Former/table*.png 改为该目录实际存在的 fig1~4.png 对应图，或补提缺失表格图；改后用 file:// 渲染确认 naturalWidth>0。`
- `把 DySample_Learning_to_Upsample.html 的 dysample_table2~9.png 改为实际文件名 dysample_fig2~9.png，或把 paper-slides/2023 Dysample ..._assets/table*.png 归档到 assets/paper-imgs/DySample/。`
- `把 YOLO26_Unified_Real-Time_Vision.html:1172 的 01 / 01 改为由 JS 写入 ${idx+1} / ${total}（先确认无 JS 覆盖），或静态改为 01 / 21。`
- `为全部 62 份的 <style> 补：@media print { .slide{position:relative;opacity:1!important;visibility:visible!important;transform:none!important;page-break-after:always} .controls,.dots,.progress,.hint{display:none!important} }，并用 emulateMedia('print') 验证可见页数 = 实际页数。`
- `B 类把 document 级 click 翻页改为仅绑定 .deck 空白区，或在点击 img / a / .dot 时 stopPropagation()，消除误触。`

---

## 8. 证据门槛与冲突裁决

| 环节 | 规则 |
|---|---|
| 静态疑似 | 脚本只输出 `suspected`，**不得**直接定红线或写入清单 |
| 渲染确认 | 图片看 `naturalWidth`/`complete`；溢出看 `scrollHeight/clientHeight`；字号看 `getComputedStyle().fontSize`；翻页看逐页 `visibility/opacity` |
| 人工复核 | 读 `.cache/slides-audit/human_review.json`，逐条标 `confirmed` / `dismissed` / `unverified + 原因`；截图复核视觉可见性 |
| 静态 vs 渲染冲突 | **以渲染为准**：图片静态「不存在」但 `naturalWidth>0` → 驳回；`PAGE_RE` 页数 vs DOM 页数 → 以 DOM 为准 |
| 硬编码页码 | 以人工复核「JS 是否动态覆盖」为准（§4.5 I5.4） |
| 无法判定 | 一律标「未验证 + 原因」，不计达标、不扣分、不写「通过 / 失败」、不臆测 |
| 事实层 | 实验数值不逐份比对 PDF，统一标注「事实层未逐份核验」 |
| 差异留痕 | 所有被驳回的疑似项、静态/渲染差异，列入核查报告 §8 |

---

## 附录 A · 检查项 ↔ 度量字段 ↔ 脚本函数映射

| 检查项 | 度量字段（`static_metrics.json` / `render_metrics.json`） | 脚本位置 |
|---|---|---|
| C1.1 / C1.2 / C1.3 / C1.7 | `sections`, `page_titles`, `cover_meta`, `placeholders`, `zh_per_page` | `audit_slides.py: scan_file()` |
| C1.8 | `imgs[].exists`, `suspected_broken`, `render.broken_imgs`, `human_review.broken_confirmed` | 两脚本 + `human_review.json` |
| L2.1 / L2.3 / L2.6 | `has_aspect_ratio`, `has_scale`, `has_resize`, `padding_rule` | `audit_slides.py` |
| L2.2 / A6.1 / A6.2 | `viewports[].overflow_pages`, `scroll_*` | `audit_render.py: probe_viewport()` |
| T3.1 / T3.3 / T3.4 | `viewports[].min_font_px`, `contrast_violations`, `formula_entities` | `audit_render.py` |
| T3.2 / A6.5 | `external_deps`, `favicon_exists`, `failed_requests` | 两脚本 |
| V4.1 ~ V4.6 | `css_vars`, `font_families`, `components`, `template_class` | `audit_slides.py` |
| I5.1 ~ I5.7 | `active_important`, `js_inline_style_hits`, `events`, `page_labels`, `render.keyboard_ok`, `render.click_misfire`, `render.page_visibility` | 两脚本 |
| A6.3 / A6.4 / A6.6 | `media_queries`, `has_print`, `viewport_meta`, `render.print_visible_pages` | 两脚本 |

**复现命令**（Windows PowerShell，须用已装 playwright 的 PATH `python`）：

```powershell
python scripts/audit_slides.py --static
python scripts/audit_render.py --probe-only
python scripts/audit_render.py
python scripts/audit_slides.py --score
```

中间产物：`.cache/slides-audit/`（`static_metrics.json`、`render_metrics.json`、`human_review.json`、`findings.json`、`report_tables.md`、`screens/`），已被 `.gitignore:9` 忽略，不纳入交付。

## 附录 B · 检查项编号速查

| 维度 | 编号 |
|---|---|
| C 内容完整性与逻辑 | C1.1 封面溯源 · C1.2 叙事链 · C1.3 无占位 · C1.4 要点量 · C1.5 图注 · C1.6 出处(G) · C1.7 空页 · C1.8 图片可用 · C1.9 事实层 |
| L 版式布局 | L2.1 16:9(G) · L2.2 溢出 · L2.3 padding/弹性 · L2.4 宽图 · L2.5 单主题 · L2.6 缩放兜底(G) |
| T 文字可读性 | T3.1 字号 · T3.2 字体/零外链 · T3.3 对比度 · T3.4 公式 · T3.5 字重行高 · T3.6 表格位图(G) |
| V 视觉一致性 | V4.1 配色 · V4.2 字体栈 · V4.3 必需组件 · V4.4 封面/章节样式 · V4.5 组件参数 · V4.6 双模板(G) |
| I 交互效果 | I5.1 状态机 · I5.2 键盘 · I5.3 触摸/误触 · I5.4 页码自洽 · I5.5 显式控制器 · I5.6 dots/进度 · I5.7 全屏 |
| A 展示适配 | A6.1 三档主屏 · A6.2 投影/窄屏/竖屏 · A6.3 响应式 · A6.4 打印(G) · A6.5 离线单文件 · A6.6 viewport · A6.7 缩放 |
