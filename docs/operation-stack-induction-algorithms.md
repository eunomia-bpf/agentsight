# Operation-Stack Induction：算法、实现与实验演进

**更新时间：** 2026-07-19

**状态：** 研究与实现记录；当前发布候选是 multi-resolution 跨运行
recurrence，递归 information gain 与 Qwen 3B semantic-stack 方案仅保留在 Git
历史和实验报告中

**所属问题：** RQ3（tag accuracy）中的 operation partition / boundary 子问题

## 1. 这份文档回答什么

AgentProf 已经完整实现和测试过两条不同的 operation-stack induction
路线：

1. **递归、资源加权的 information-gain 分割**：寻找一个切点，使切开后的
   operation 字段更“纯”；
2. **跨运行 action-transition recurrence**：寻找在其他 session 中反复共同
   出现的相邻 action，把强关联 transition 留在同一个 operation 中。

两者都把线性 operation 序列转换为可聚合的 operation identity，但优化的对象
不同。第一种在问“哪里切开能最大程度降低字段的不确定性”，第二种在问“哪些
相邻行为具有可复用的跨运行连续性”。后者不是前者增加一个 feature，也不是把
递归写得更复杂，而是根据完整实验暴露的目标错配而更换了学习原则。

这只是 RQ3 的一个组成部分。它不回答完整的 attribution、localization、tag
accuracy 或 cost RQ，也不改变论文的固定 thesis：

> **Agent observability needs profiling, not only debugging.**

## 2. 共同问题定义

### 2.1 输入

对每个 session，输入是按执行顺序排列的 operation：

```text
o_1, o_2, ..., o_n
```

每个 operation 至少有：

- `session`：序列边界；
- `action` 或其他可见字段：例如 `click`、`type`、`shell`；
- `value`：profiling 时可加的资源权重；
- 其他可见字段：由具体 trace adapter 提供。

人类 `group`、gold boundary、正确性和其他 oracle 字段只能用于最终评分，不能
进入默认构造器。可选的 supervised recurrence calibration 明确使用独立 grouped
reference operations；它与 label-free 默认模式分开报告。

### 2.2 输出

输出是每个 session 的连续分段：

```text
[o_1 ... o_j] [o_{j+1} ... o_k] ...
```

同一段中的 operation 获得同一个派生 `operation` frame，随后进入 AgentProf
既有的 operation-stack 投影和资源聚合路径。递归 information-gain 版本曾直接
产生 variable-depth 路径；当前 recurrence 版本先产生连续 operation segment，
再把 segment identity 作为 operation stack 中的一个 frame。两者都不是在恢复
CPU call stack。

### 2.3 两个主要指标

- **Boundary F1**：每个相邻 pair 是否被正确切开。它对边界位置很敏感。
- **B-cubed F1**：逐 operation 比较预测分组和人类分组的重合程度。它同时惩罚
  把一个真实 operation 切碎和把多个 operation 合并，对完整 partition 更直接。

因此 boundary F1 与 B-cubed F1 可能方向不同。当前研究把 B-cubed 作为 partition
质量的主要指标，boundary F1 作为解释 merge/fragmentation 的诊断；这不允许把
某一个指标的改善写成所有意义上的 tag accuracy 改善。

#### Boundary F1 具体算什么

一个含 `n` 个 operation 的 session 有 `n-1` 个相邻缝隙。对每个缝隙只问一个
二分类问题：“这里是不是人类 group 的边界？”

```text
boundary precision = 预测边界中真正正确的比例
boundary recall    = 人类边界中被找到的比例
boundary F1        = 2PR / (P+R)
```

它不是“有多少 operation 被正确分类”的 accuracy。`boundary F1 = 0.68` 也不能
单独说明是漏切少还是乱切少，必须同时看 precision、recall 和 group 数量。

#### B-cubed F1 具体算什么

对每个 operation `o`，比较“预测中与它同组的 operation 集合”与“人类标注中与
它同组的集合”：

```text
P_o = |Pred(o) ∩ Gold(o)| / |Pred(o)|
R_o = |Pred(o) ∩ Gold(o)| / |Gold(o)|
```

对所有 operation 平均得到 B-cubed precision/recall，再取 harmonic mean。把多个
真实 operation 粗暴合并会降低 precision；把一个真实 operation 切成许多小片会
降低 recall。

例如 gold 是：

```text
[inspect, edit, test] [inspect, edit]
```

预测成一个五步大组，虽然只少一个 boundary，但第一个组的 operation 都混入了
第二个组，B-cubed precision 会明显下降。预测成五个 singleton，则所有 boundary
recall 很高且每组很“纯”，但每个真实 operation 被切碎，B-cubed recall 会下降。

### 2.4 我们真正想知道的信息分四层

“operation-stack induction 好不好”不能只等同于一个 boundary 数字。最终希望从
低层 trace 得到四层信息：

1. **单次运行的 membership / boundary**：哪些相邻 operation 属于同一个人类
   可理解的工作单元，哪里开始下一个单元；
2. **跨运行的 stable identity**：不同 session 中哪些工作单元是同一种 recurring
   operation，从而可以累计资源和效果；
3. **可读 semantic name**：这个 identity 能否被稳定命名为正确 task、phase 或
   action，而不只是 `click-then-type` 形状；
4. **profiling usefulness**：按这些 identity 聚合后，分析者是否更容易完成论文
   要求的 attribution 和 problem localization。

当前 OSWorld 的 boundary/B-cubed 结果只直接评估第 1 层。recurrence 使用跨运行
统计来改善第 1 层，并产生可复用 motif，但这些分数本身没有证明第 2 层 identity
在跨运行语义上正确，更没有评估第 3 层名字或第 4 层诊断价值。因此这些数字是
必要的 constructor evidence，不是 AgentProf 整体价值的充分证据。

### 2.5 OSWorld-Human 到底标注了什么

OSWorld-Human 为每个 OSWorld task 人工维护两种成功参考轨迹：

- `single-action`：完成任务所需的最小、人类可理解的动作序列；
- `grouped-action`：把**可以从同一个视觉观察中连续正确执行**的相邻动作放在
  同一组。原论文把这解释为这些动作可能只需要一次 planning、judging 或
  reflection，而不是每个动作都重新调用一次大模型。

因此，官方 `grouped-action` 的 gold 语义首先是 **same-observation executable
group**，服务于 computer-use agent 的步骤和时延效率分析。它并没有直接标注：

- 高层 task / phase / action 的语义名称；
- 两个不同 session 的 group 是否是同一种 recurring operation；
- 哪个 group 是错误根因、产生了什么 measured effect；
- 每个 group 应归属多少 token、latency 或其他 profiling resource。

本项目 adapter 只保留 `single-action` 与 `grouped-action` 能够逐动作完全对齐的
session。每个 single action 成为一个 unit-weight operation；它所属的官方
group 成为 session-local `human_group`。相邻两个 action 的 `human_group` 不同，
才形成一个 gold boundary。由此得到的 287 个 session、3,978 个 operation 和
2,042 个 group，是官方 grouped trajectory 的连续 partition，不是我们另外人工
编写的 phase/action 标注。adapter 派生的 `phase`、`target`、`group_pattern` 等
字段都不是官方 gold，不能用来扩大 OSWorld 分数的含义。

这也解释了为什么 OSWorld 可以严谨评估“是否恢复 same-observation grouping”，
却不能单独证明 AgentProf 已经获得正确的跨运行 operation identity 或可读语义
tag。后两者必须由另外的独立标注或下游实验回答。

### 2.6 四组 OSWorld 数字到底表示什么

同一完整 OSWorld-Human population 有：

- 287 个 session；
- 3,978 个 operation；
- 3,691 个可判断的相邻缝隙；
- 2,042 个人类 group，因此 session 内共有 1,755 个真实 boundary。

完整 precision/recall 与预测粒度如下：

| 方法 | Boundary P | Boundary R | Boundary F1 | B³ P | B³ R | B³ F1 | 预测 group |
|---|---:|---:|---:|---:|---:|---:|---:|
| Information gain，depth 4 | 0.4985 | 0.3675 | 0.4231 | 0.4994 | 0.8054 | 0.6165 | 1,581 |
| Information gain，depth 255 | 0.4867 | 0.4581 | 0.4720 | 0.6066 | 0.7533 | 0.6720 | 1,939 |
| Label-free recurrence | 0.5918 | 0.7989 | 0.6799 | 0.8559 | 0.7270 | 0.7862 | 2,656 |
| Grouped-reference calibration | 0.6096 | 0.9219 | 0.7340 | 0.9170 | 0.7112 | 0.8011 | 2,941 |

这些行应这样读：

- **Depth 4 明显 under-segment。** 只预测 1,581 个 group，低于人类的 2,042；
  boundary recall 只有 0.3675，说明漏掉很多真实切点。B³ recall 高而 precision
  低也符合“把多个真实 operation 合成大组”。
- **去掉深度上限确实修了一部分 under-segmentation。** 预测 group 增到 1,939，
  boundary recall 从 0.3675 升到 0.4581，B³ precision 从 0.4994 升到 0.6066。
  但切点位置仍经常不对，所以不能把问题归因于 depth 4。
- **Recurrence 找回了更多真实 boundary，并且 partition 纯度大幅提高。**
  boundary recall 达到 0.7989，B³ precision 达到 0.8559。它同时预测 2,656 个
  group，高于人类 2,042，说明已经从 under-segmentation 转向一定程度的
  over-segmentation；B³ recall 0.7270 正在惩罚这种切碎。
- **Calibration 不是无代价地“全面更好”。** 它把 boundary recall 提到 0.9219、
  B³ precision 提到 0.9170，却预测 2,941 个 group，B³ recall 降到 0.7112。
  最终 B³ F1 只从 0.7862 增加约 0.0149。它更积极地切分，用更高的 group purity
  换取更多 fragmentation，而且需要独立 grouped reference labels。

因此，四组数最可靠的结论不是“0.8011 的算法绝对最好”，而是：

1. depth cap 是真实限制，但不是 information-gain 的主要失败原因；
2. cross-run recurrence 的 operation-continuity 目标比字段纯度更符合这套人类
   partition；
3. label-free recurrence 是当前更简单、信息预算更低的默认实现；
4. grouped-reference calibration 是有 annotation 时的可选粒度调整，它在该
   population 上小幅提高 partition F1，但更 over-segment，不能冒充免费提升。

### 2.7 怎么判断一个算法真正更好

在同一信息预算下，最低限度要一起看：

- **partition fidelity**：B-cubed precision/recall/F1；
- **boundary behavior**：boundary precision/recall 和预测 group 数，用来解释是
  merge 还是 fragmentation；
- **跨真实 workload 的方向一致性**：不能只在一个已经用于选择算法的 corpus
  上更高；
- **输入成本**：label-free、unlabeled cross-run reference、grouped labeled
  reference 不是同一种条件，必须分开比较；
- **最终 profiling usefulness**：好的 partition 应在独立的 attribution /
  localization 实验中帮助作出更好的 profiling 决策。

mass conservation、determinism、没有读取 target oracle 是实现有效性条件，不是
“算法科学上更好”的分数。相反，一个算法即使 B-cubed 更高，如果只靠更多标签、
明显过度切分，或不能改善下游 profiling decision，也不能自动成为整篇论文的
最好算法。

对**当前 OSWorld same-observation partition 子问题**，最简洁、合理的报告方式是：

1. 以 per-operation B-cubed F1 为主指标，因为目标是完整 partition membership，
   而不是给 group ID 做字符串分类；
2. 强制并列报告 B-cubed precision/recall、exact-boundary precision/recall/F1，
   以及 predicted/gold group count，明确区分 merge 与 fragmentation；
3. 把每个 task/session 等权的 macro 结果或 per-session 分布作为敏感性结果，避免
   少数长轨迹完全主导 pooled operation 平均；
4. label-free 与 grouped-reference 模式分开成不同信息预算，不能只因后者
   `0.8011 > 0.7862` 就宣称算法免费改善。

不应把 boundary accuracy 当主指标，因为非边界通常更多，全部预测 continuity
也可能得到误导性高 accuracy；不应只报 boundary F1，因为它隐藏了完整 segment
的 merge/fragmentation；也不应只报 group 数，因为数量相同不代表切点正确。

对**论文声称的完整 operation-stack induction**，OSWorld B-cubed 只能是第一层
constructor metric，不能成为唯一 headline。完整证据至少还需要：

- 跨 session stable identity 的 label-invariant partition / pairwise P-R-F1；
- 固定 task/phase/action taxonomy 上的 macro-F1 与 accuracy；
- RQ1 attribution 和 RQ2 localization 中，在固定 inspection budget 下的实际
  profiling decision 改善。

这三类结果回答不同问题，不应压缩成一个自定义 composite score。算法选择先比较
相同输入信息预算，再看各层是否形成一致的 Pareto 改善；一项 proxy 的局部最高分
不能覆盖其他层没有被测量的事实。

## 3. 算法 A：递归、资源加权 information gain

### 3.1 直觉

假设一个区间内的 action、tool 或其他可见字段非常混杂，而某个切点左边主要是
一种取值、右边主要是另一种取值，那么这个切点降低了字段熵，可能是 operation
边界。

这是 decision-tree information gain 与 binary segmentation 的组合。它的优点是
只有一个清楚的目标，不需要把 Jaccard、balance、coverage、semantic shift、
child size 等许多 heuristic 加权相加。

### 3.2 候选字段与候选边界

对当前递归区间 `I`：

1. 排除 gold/oracle/label 字段、metadata、近似数值噪声、常量和过高基数字段；
2. 只考虑相邻 operation 至少有一个合格字段发生变化的位置；
3. 切点左右必须都非空。

这些是输入可用性约束，不是额外的打分 feature。

### 3.3 公式

对字段 `f`，令 `H_w(f, I)` 为按 operation resource weight 计算的 categorical
entropy，`L` 和 `R` 是候选切点 `b` 的两个子区间，`W_X` 是区间 `X` 的总权重：

```text
G_f(I,b) = [ H_w(f,I)
             - (W_L/W_I) H_w(f,L)
             - (W_R/W_I) H_w(f,R) ] / H_w(f,I)
```

除以 parent entropy 后，不同字段的 gain 落在可比较尺度上。边界总分是所有
informative 字段 normalized gain 的等权平均：

```text
G(I,b) = mean_f G_f(I,b)
```

对含 `n` 个 operation 的区间，历史实现使用固定 complexity penalty：

```text
P(I) = ln(n) / (2n)
```

选 `G(I,b)` 最大的切点，并且仅当 `G(I,b) > P(I)` 时切开。然后对左右区间递归。
每个 child frame 使用最能解释该边界的字段及其 dominant value，例如
`action=click`。

### 3.4 接近真实 Rust 的伪代码

```rust
fn split(interval):
    candidates = adjacent_visible_field_changes(interval)
    scored = candidates.map(|b| {
        field_gains = eligible_fields.map(|f| normalized_weighted_gain(f, b))
        score = mean(field_gains)
        (b, score, best_explanatory_field(field_gains))
    })

    best = argmax(scored, deterministic_ties)
    if best.score <= ln(interval.len()) / (2 * interval.len()):
        return one_leaf(interval)

    left, right = cut(interval, best.boundary)
    return node(label(best), split(left), split(right))
```

历史真实实现位于 commit `fe0704f9b` 的 `agentpprof/src/profile.rs`，核心函数为：

- `induce_operation_stack_recursive`；
- `choose_task_split`；
- `score_task_boundary_split`；
- `operation_stack_field_gain`；
- `weighted_value_counts` 与 `entropy`。

可直接读取当时完整代码：

```bash
git show fe0704f9b:agentpprof/src/profile.rs
```

固定深度四的完整协议、代码审查和结果在：

- `docs/tmp/build-and-evaluate/step-0017-20260714T121012-0700/01-experiment-gate/loop-002-rq3-rust-inducer-fidelity/`
- `docs/tmp/build-and-evaluate/step-0017-20260714T121012-0700/step-report.md`

去掉有效深度上限的完整实验在：

- `docs/tmp/build-and-evaluate/step-0018-20260714T160153-0700/`

当前 CLI 仍识别旧的 `--induce-max-depth`、`--induce-query-term` 等参数，以返回
明确的 legacy error；它们不再驱动当前 recurrence 实现。

### 3.5 一个能说明问题的例子

假设人类认为下面两轮各是一个完整 operation：

```text
[inspect, edit, test] [inspect, edit, test]
```

正确边界在两个 `test | inspect` 之间。但边界左右的 action 分布完全相同，都是
`inspect/edit/test` 各一次，所以这个正确切点的 action information gain 是零。
算法没有理由选择它。

反过来：

```text
[inspect, inspect, edit, edit]
```

如果人类把四步视为一个 operation，`inspect | edit` 仍会产生很高的字段纯度
提升，information gain 会偏好一个错误边界。

这说明问题不是实现 bug，也不主要是深度不足，而是“字段纯度”与“operation
连续性”不是同一个目标。

### 3.6 实际结果

完整 OSWorld-Human population 包含 287 个 session、3,978 个 operation、3,691
个相邻 decision 和 2,042 个官方人类 group。

| 版本 | Boundary F1 | B-cubed F1 | 结论 |
|---|---:|---:|---|
| 旧多项 heuristic | 0.0843 | 0.4653 | 被替换的早期实现 |
| Information gain，depth 4 | 0.4231 | 0.6165 | 大幅改善旧实现，但未超过最强 simple controls |
| Information gain，非约束 depth 255 | 0.4720 | 0.6720 | 深度限制确实有影响，但不是主要瓶颈 |
| Action-change control | 0.4771 | 0.6592 | 简单控制 |
| Always-boundary control | 0.6445 | 0.6784 | 简单控制 |

去掉深度上限把 B-cubed 从 `0.6165` 提高到 `0.6720`，说明 depth 4 会
under-segment；但 boundary F1 仍低于 action-change 和 always-boundary，B-cubed
也未同时越过最强控制。继续调 penalty 或深度不能修复上面的 objective mismatch。

### 3.7 优点

- 一个目标，数学表达清楚；
- 不读取 target oracle；
- 每个 operation 恰好进入一个 leaf；
- additive weight 守恒；
- 每个 accepted split 都改善同一个目标；
- deterministic tie rules，递归一定终止；
- 在目标 segment 本来就应字段同质的 change-point 问题上仍然合理。

### 3.8 不足

1. **核心目标错配。** 一个真实 agent operation 往往就是异质 action motif，纯度
   不是 continuity。
2. **相同分布的重复阶段不可见。** 两段字段分布相同但语义上是两次 operation
   时，information gain 接近零。
3. **会奖励内部 phase 切分。** `inspect -> edit -> test` 内部字段变化可能比两轮
   operation 之间更容易产生 gain。
4. **递归误差会累积。** 上层错误切点改变所有后续 child 的候选空间和路径。
5. **frame path 容易表达 partition 过程而非稳定的跨运行 identity。** 两个 session
   的局部树路径不一定可直接合并。
6. **复杂度 penalty 不是 operation 定义。** 它能控制树大小，不能告诉算法哪些
   action 应共同组成一个 operation。
7. **完整实验只支持“优于旧 heuristic”，不支持把它作为当前最强 constructor。**

## 4. 算法 B：跨运行 action-transition recurrence

### 4.1 直觉

如果 `inspect -> edit` 在许多其他运行中都以超出偶然的频率共同出现，它更像一
个可复用 operation 内部的连续 transition。反之，弱关联或从未见过的 transition
更可能是 operation 边界。

这里不要求一个 operation 内只有一种 action。`click -> type -> press` 可以作为
一个异质但反复出现的 motif 保持完整。这直接针对 information-gain 版本暴露的
目标错配。

### 4.2 NPMI recurrence score

从 reference sessions 的所有相邻 action pair 建立同一个 transition sample
space。对有向 pair `(a,b)`：

```text
p(a,b) = count(a -> b) / number_of_transitions
p_L(a) = count(a appears on left) / number_of_transitions
p_R(b) = count(b appears on right) / number_of_transitions

NPMI(a,b) = ln[p(a,b) / (p_L(a) p_R(b))] / -ln[p(a,b)]
```

- 接近 `1`：pair 强烈共同出现；
- 接近 `0`：接近独立；
- 小于 `0`：比独立预期更少共同出现；
- reference 中未见：没有分数，默认切开。

早期 exploratory 计算曾错误地把 operation-count marginal 与 transition-count
joint 混用，得到约 `0.732/0.797` 的有利诊断。plan review 发现 sample-space
不一致后，这组数被明确作废；当前实现使用上面一致的 left/right transition
marginal。

### 4.3 无标签 cutoff

把每次 transition occurrence 对应的 NPMI 分数放入一维 deterministic two-means：

```text
low cluster  <---- cutoff ----> high cluster
cutoff = (mean(low) + mean(high)) / 2
```

初始化为最小值与最大值；相同距离归入 low cluster；迭代到中心不再变化，最多
100 轮。它不搜索 gold labels。

当前 label-free 发布规则使用两个由同一 reference 得到的 cutoff：

```text
same action:      applied = global_cutoff
different action: applied = min(global_cutoff, cross_action_cutoff)
unseen pair:      boundary = true
seen pair:        boundary = NPMI(pair) < applied
```

为什么不同 action 取 `min`？因为 boundary 条件是 `score < cutoff`。降低 cutoff
只能把原先的 boundary 恢复为 continuity，不能新增 boundary。这是 Step 0024
针对 identity transition 淹没 global calibration 的最小单调修复。

### 4.4 Segment 与 motif 名称

确定所有边界后，每个连续 segment 的 action 序列做 run-length compression：

```text
click, click, type, type, press
    -> action=click-then-type-then-press
```

同样的 motif 在不同 session 中获得同一个 operation identity。若 folded frame
规范化后发生文本碰撞，则使用稳定 hash 后缀消歧。motif 名称描述可见 action
形状，不自动等同于人类 task/phase 语义。

### 4.5 当前 Rust 代码

当前实现位于 `agentpprof/src/profile.rs`：

- `induce_operation_stack`：应用模型、决定边界、生成 segment；
- `recurrence_groups`：按 session 组织序列；
- `recurrence_model`：计数并计算 NPMI；
- `recurrence_calibration` 与 `deterministic_recurrence_two_means`：无标签 cutoff；
- `recurrence_motif`：生成 run-length-compressed identity；
- `fit_supervised_recurrence_cutoff`：可选 grouped-reference scalar calibration；
- `recurrence_calibration_partition_metrics`：只在 calibration operations 上计算
  per-operation B-cubed。

决定边界的真实核心代码等价于：

```rust
let npmi = model.association.get(&(left_action, right_action));
let cutoff = if left_action == right_action {
    model.global.cutoff
} else {
    model.global.cutoff.min(model.cross_action.cutoff)
};
let boundary = npmi.is_none_or(|score| *score < cutoff);
```

关键实现提交：

| Commit | 作用 |
|---|---|
| `267244739` | 用 cross-session NPMI recurrence 替换 information-gain runtime |
| `6b1f0a799` | 加入 action-changing transition 的单调 `min` 规则 |
| `387070c48` | 加入可选 grouped-reference scalar calibration |

### 4.6 可选 supervised scalar calibration

默认 two-means 只观察 score distribution，不知道人类期望的 operation 粒度。若有
与 target session 分离的 grouped reference operations，可保持 NPMI score 不变，
只拟合一个 scalar cutoff：

1. 枚举最小 observed score 以下、相邻 distinct score 的 midpoint、最大 score
   以上；
2. 在 grouped reference 上计算每个 cutoff 的 per-operation B-cubed F1；
3. 选择 F1 最大者；exact tie 选择数值最小的 cutoff；
4. 把 cutoff 原样应用到 target；target group 不参与选择。

它是一个有额外 annotation budget 的可选模式，不能与 label-free 默认模式写成
equal-information comparison。

### 4.7 真实结果

| Population / 版本 | Boundary F1 | B-cubed F1 | 状态 |
|---|---:|---:|---|
| OSWorld，非约束 information gain | 0.4720 | 0.6720 | 被替换 |
| OSWorld，label-free recurrence | 0.679922 | 0.786170 | 当前默认机制的开发结果 |
| OSWorld，reference-calibrated recurrence | 0.733953 | 0.801087 | 可选 annotated-reference 模式 |
| CodeTrace，早期 global recurrence | 未作为当前 headline | 0.475008 | 被 Step 0024 修复 |
| CodeTrace，monotone recurrence | 0.287106 | 0.649173 | 当前默认机制 |
| CodeTrace，multi-resolution recurrence | 0.265571 | 0.662740 | 当前发布候选 |
| CodeTrace，reference-calibrated recurrence | 0.236176 | 0.666564 | partition 改善但 boundary tradeoff |

OSWorld 上 label-free recurrence 相对非约束 information gain 提升约 `+0.208`
boundary F1 和 `+0.114` B-cubed F1。CodeTrace 的 calibrated 版本把 6,897 个默认
group 合并到 5,331 个：B-cubed recall 的收益超过 precision 损失，但 boundary F1
下降。这是 merge/fragmentation 粒度取舍，不是所有指标一致改善。

### 4.8 优点

- 直接允许异质 action 构成一个 recurring motif；
- 产生可跨 session 合并的 reusable operation identity；
- 默认模式不读取 group/oracle label；
- score、cutoff、边界规则都短且可重算；
- 不需要递归深度、child-size 或多个 heuristic feature；
- 每个 operation 恰好进入一个连续 segment，profile resource mass 不变；
- action-changing 修复具有“只移除、不新增原规则边界”的单调性质。

### 4.9 不足

1. **recurrence 假设并非总成立。** operation 内 transition 必须比 operation 间
   transition 更稳定；精确重复循环中，真实边界 transition 也可能高频复现。
2. **稀有或新行为倾向被切开。** unseen pair 默认 boundary，对 novel operation
   可能 over-segment。
3. **只看 action pair 会发生 observational aliasing。** 相同 pair 在不同上下文
   可能一个是边界、一个不是。完整诊断显示 mixed-label pair 覆盖 OSWorld 91.2%
   和 CodeTrace 99.7% 的相邻 decision。
4. **pairwise score 看不到长程结构。** 局部相邻 recurrence 不能表达 plan state、
   object identity、goal progress 或远距离 dependency。
5. **reference 分布会影响结果。** session 数、action vocabulary 和工作负载变化会
   改变 NPMI 与 two-means cutoff。
6. **two-means 只是在 score 分布上找两团。** 它没有保证两团就对应人类的
   boundary/continuity；可选 calibration 能调整粒度，但需要额外 grouped data。
7. **motif 名称不等于 semantic tag accuracy。** `click-then-type` 是稳定形状，
   不是自动证明它叫“checkout”或“debug”。
8. **现有正结果主要是 development / reference-calibrated evidence。** 它支持
   bounded RQ3 mechanism claim，不等于完整 RQ3 已回答，更不等于最终诊断价值已
   证明。

### 4.10 Multi-resolution recurrence：当前发布候选

Step 0049 在不增加 score、cutoff 或新抽象的情况下加入第二个可见分辨率。粗状态
只包含 `action`；细状态包含完整的 `(action, action_detail)`。两个分辨率都使用
同一套 cross-session NPMI、deterministic two-means 和 signature-change
`min(global, change)` 规则。最终原则只有一句：

```text
continuity = coarse_continuity OR detail_continuity
boundary   = coarse_boundary AND NOT detail_continuity
```

因此细分辨率只能把一个粗边界恢复为 continuity，绝不新增粗算法没有的边界。
`action_detail` 缺失、不完整、reference 中未见或关联不足时都精确回退到粗算法；
visible motif 名称仍只由粗 `action` 构成。概念上这不是 feature soup，而是同一个
recurrence 原理在两种观察分辨率上的单调合取。

完整 CodeTraceBench population 上，它把 879 个粗边界恢复为 continuity，预测
group 从 6,897 降到 6,018，普通 B-cubed F1 从 `0.649173` 提高到 `0.662740`。
相对粗版本的 paired task-cluster bootstrap 95% 区间为
`[+0.008712,+0.018043]`，四个 framework 的 B-cubed F1 都提高。Boundary F1 从
`0.287106` 降到 `0.265571`，说明改善来自减少 fragmentation，而不是所有 boundary
指标一致提升。

OSWorld-Human 输入没有非冗余 `action_detail`。修改后的 Rust constructor 在五个
完整 fold 上与发布粗算法逐 decision、segment、motif、profile byte 完全一致，因而
保留 `0.679922` boundary F1 和 `0.786170` B-cubed F1。这是实测 fallback，不是
第二个性能增益。

完整 plan、preflight、raw run 与两次独立 review 位于：

```text
docs/tmp/build-and-evaluate/step-0049-20260719T195559-0700/experiment-001/
```

## 5. 已尝试但未保留的 recurrence 变体

### 5.1 早期 global-only cutoff

最初只对所有 transition 的 NPMI 做一个 global two-means。CodeTrace 的
identity transition 数量使 global cutoff 偏高，错误切开 recurring cross-action
continuity，B-cubed 只有 `0.475008`。Step 0024 的 `min(global,cross_action)` 修复
把它提高到 `0.649173`，同时保持“不能新增边界”的单调性质。

### 5.2 Immediate local raw-NPMI minimum

Step 0025 测过一个 sequence-local 变体：一个已满足 threshold 的 action-changing
boundary，只有当它的 raw NPMI 不大于左右相邻 transition 时才保留。其目的不是
再调 cutoff，而是只保留局部弱关联谷底。

完整结果：

- OSWorld B-cubed `0.786170 -> 0.746958`，boundary F1
  `0.679922 -> 0.547227`；
- CodeTrace B-cubed `0.649173 -> 0.671671`，boundary F1
  `0.287106 -> 0.272388`。

它对 CodeTrace 四个 framework 的 B-cubed 都有改善，但显著伤害 OSWorld，因此
没有进入发布代码；候选 Rust/Python/evaluator 改动已移除，完整算法和结果保留在：

```text
docs/tmp/build-and-evaluate/step-0025-20260715T054105-0700/
```

失败原因不是实现错误，而是两个 population 的 annotation granularity 不同，局部
suppression 在 OSWorld 删除了大量真实 boundary，却在 CodeTrace 主要删除
fragmentation。Step 0026 进一步确认，仅靠 pair identity、短 local context、
margin、support、cutoff sign 或 session length 没有一个共同可见规则能区分这些
occurrence。

### 5.3 继续微调 pair rule 为什么停止

Step 0026 的诊断不是宣称 recurrence 数学上最优，而是说明：在已经看过 labels
的两个 development population 上继续选择 cutoff、window、support bucket 或
benchmark-specific fallback，会变成事后选择粒度，而不是发现一个共同机制。
因此下一步若继续改算法，需要新的可观察 discriminator，或者独立 evidence；不应
再把同一 pair score 换一种局部排列当成新原则。

### 5.4 Qwen 3B variable-depth semantic task stack

Step 0049 也完整测试了用户提出的另一条原则：由本地 Qwen2.5-3B-Instruct 逐步
维护当前 semantic task stack。每个 operation 只能执行四类等价 transition：
保持、push 一个子任务、pop 任意多个已结束任务、或 pop 后 push 一个 sibling。
GBNF 保证输出是合法非空 JSON；总深度没有上限。模型只看到公开 task identity、
当前 stack、前一个 observation 和当前 action，不读取人工 stage。

真实 preflight 和完整 405-trajectory / 20,866-operation 推理都通过执行校验，raw
stack 深度自然达到 1--6。但 `new_frame_rate = 0.999569`：3B policy 几乎给每个
operation 创建一个新 leaf。为检验“短暂 leaf 可丢弃”这一简单修复，实验在打开
stage 前加入不可删除的 task root，并只保留 active-path support 至少为两个
operation 的生成 frame。这个规则不限制深度，也不调参；它把 20,857 个 raw leaf
收缩为 1,690 个 effective leaf。

完整标准评分表明，raw stack 是严重 over-segmentation（B-cubed F1 `0.247572`），
收缩后又变成高 recall、低 precision 的 under-segmentation（precision `0.290890`、
recall `0.853010`、F1 `0.433835`、boundary F1 `0.109949`）。相对当前
multi-resolution recurrence 的 task-cluster bootstrap 95% 区间为
`[-0.246012,-0.210910]`，四个 framework 都下降。

这个结果只否定“固定 3B transition policy + 最小 temporal-support contraction”是
更好的 CodeTrace partition；它不否定 variable-depth semantic stack、论文 RQ3
或 thesis。失败机制很清楚：合法 stack discipline 不能替代正确的 transition
policy，而 frame 是否存活两个 operation 也不足以确定 human operation continuity。
因此该方案保留在研究历史，不进入 release 或论文结果。

这次实验还澄清了目标语义。主 stack 不应只是把系统字段换一个排列顺序，而应表示
`具体任务 → 子任务 → 阶段/策略 → 语义动作 → 操作对象 → 结果`。Agent、model、
session、tool 和 status 是颜色、筛选或详情维度；command、file 和 call 是叶端证据；
事件数、时间和 token 是可加宽度。由此，正确的 semantic operation 必须回答哪个
子任务消耗资源、哪里反复尝试、是否产生有效结果、哪些子任务失败或被放弃，以及
不同 agent 如何分解同一类任务。当前 Qwen policy 只自由生成一个未分型 frame，
因此即便 label 比 raw command 更可读，也没有强制恢复上述责任层次。

为了把这个区别变成可检查的观察，Experiment 004 从固定预测中绘制了一条 95-operation
轨迹的四栏时间加权 flame graph：raw Qwen active stack、support contraction、
multi-resolution recurrence 与评分时才打开的 human stage。图显示 variable depth
确实达到六个生成层，但大量 singleton leaf 与过宽的早期祖先同时存在；contraction
删除前者却不能恢复 human stage。生成脚本与图位于
`script/plot_qwen_semantic_stack_flamegraph.py` 和 Experiment 004 的 `figures/`。

完整 plan、cache audit、full inference、score 和 Grok raw-result reconstruction
位于：

```text
docs/tmp/build-and-evaluate/step-0049-20260719T195559-0700/experiment-003/
docs/tmp/build-and-evaluate/step-0049-20260719T195559-0700/experiment-004/
```

### 5.5 Task-rooted responsibility plan 与 numeric-index confound

Step 0050 测试了一个比自由生成 stack 更稳定的中间机制。Qwen 先只根据具体任务
生成一次可复用 responsibility plan；随后每个 operation 只在固定 plan 中选择一个
active responsibility。相同选择的连续 run 是一个 workflow-stage instance，离开后
再次返回同一 responsibility type 会创建新的 temporal instance。这个设计复用完整
CodeTraceBench 405 条轨迹、20,866 个 operation 和 2,948 个人工 stage，不改变 thesis、
四个 RQ 或 task-semantic 目标。

完整推理有效，但固定 numeric-index aligner 的主假设被否定。Exact unlabeled span F1
为 `0.011574`，虽然略高于几乎逐 operation 切换的 matched plan-free Qwen
(`0.008542`)，但显著低于 multi-resolution recurrence (`0.056435`)；配对
task-cluster bootstrap 的 candidate-minus-multires 95% 区间为
`[-0.054570,-0.035973]`。修正 temporal-instance scorer 后，普通 B-cubed F1 为
`0.585237`，仍低于 recurrence 的 `0.662740`。

失败原因不是一般性的“语义 plan 不工作”，而是输出接口没有隔离语义判断和数字
顺序偏置：397/405 条轨迹第一次输出 `plan_index=1`；index 0 只覆盖
180/20,866 个 operation；5,114 次切换中有 4,384 次 (`85.73%`) 恰好是 index
加一。最长轨迹先输出 `1,2,3,4,5`，随后把 271/275 个 operation 全部归到最后的
`test deployment`。因此当前结果只否定 numeric-index causal aligner，不能否定
task-derived responsibility、variable-depth hierarchy 或完整 semantic-stack 方向。

这次还暴露并修正了一个 scorer 区分：`responsibility_type` 是可跨时间复用的语义
类型；`stage_instance` 是一次连续访问。普通 B-cubed 和 span score 必须比较后者，
不能把非连续访问按同一 plan index 合并。旧 scorer attempt 保留在 raw artifact
中，修正不改变 prediction、主 span score、boundary score、bootstrap 或 verdict。

下一次最小机制不是增加 feature、threshold 或 benchmark，而是复用已经生成的 405
个 plans 和全部 operation evidence，把 transition 改为显式 `stay` 或
`switch` 到一个 exact responsibility string。模型只看当前/候选 responsibility
文本，不见也不输出 numeric index 或 instance number。这个实验只检验 ordinal
confound 是否解释当前 stage-alignment 失败；即使成功，也不能单独验证 nested
subtask、strategy、semantic action、object 或 result 的完整 hierarchy。

完整 plan、preflight、run、scorer correction 与独立复算位于：

```text
docs/tmp/build-and-evaluate/step-0050-20260720T022249-0700/experiment-001/
```

### 5.6 Index-free semantic transition 仍退化为 near-singleton

Step 0051 完整执行了 5.5 注册的最小后续机制。它逐字复用 Step0050 的 405 个
task-rooted responsibility plans、20,866 个 causal operation evidence、Qwen2.5-3B、
recurrence comparators 和标准 scorer，只把 numeric-index 选择替换为显式
`stay` 或 `switch` 到一个 exact responsibility string。模型不见也不输出 numeric
index 或 temporal-instance id；相同 label 的一次连续访问仍是独立 stage instance。

这个接口没有恢复 temporal continuity。20,866 次决定中有 20,465 次是 `switch`，
只有 401 次 `stay`；去掉每条轨迹必须建立初始状态的第一次选择后，相邻边界率仍为
`0.980402`。Preflight 中观察到的 exact-label 交替因而不是四条轨迹的偶然现象，而是
完整 population 上的 policy degeneration。

完整标准评分为：

- exact unlabeled span F1 `0.008201`，低于 numeric predecessor 的 `0.011574`、
  current recurrence 的 `0.068055` 和 multi-resolution recurrence 的 `0.056435`；
- ordinary B-cubed F1 `0.264371`，其 precision `0.992830`、recall `0.152488`，
  符合 near-singleton partition；
- exact adjacent-boundary F1 `0.221740`，recall `0.985450` 但 precision 只有
  `0.124925`，产生 17,554 个 false boundaries。

Candidate-minus-current 的 task-cluster bootstrap 95% 区间是
`[-0.071057,-0.050050]`，candidate-minus-multires 是
`[-0.057653,-0.039826]`，candidate-minus-numeric 是
`[-0.006583,-0.000418]`。因此注册假设被明确否定，接口不进入发布实现或论文结果。

这个结果不能解释成“numeric tokens 是唯一原因”，因为 Step0051 同时改变了表示和
transition form。它能支持的机制判断是：把 continuation 判断和 exact-label 选择塞进
同一个竞争 grammar branch，会让当前 3B policy 几乎总选 `switch`；去掉 ordinal
tokens、保留 semantic text 和保证合法输出仍不足以恢复 human workflow-stage spans。
这是否来自 grammar branch 的生成偏置、模型的局部语义判断，或两者共同作用，当前
实验没有进一步拆分。

该失败仍不否定用户定义的主结构：
`具体任务 → 嵌套子任务 → 阶段/策略 → 语义动作 → 操作对象 → 结果`。它只淘汰一个
flat-stage transition interface。若继续，最小的新机制应先独立判断当前 operation
是否延续 active responsibility，只有判定发生变化后才选择 label；不应增加系统字段、
feature soup、深度限制或事后 contraction。

完整 plan、三次串行审查、preflight、full run 和标准 score 位于：

```text
docs/tmp/build-and-evaluate/step-0051-20260720T052839-0700/experiment-001/
```

### 5.7 两阶段 continuation/label factorization 修复 degeneration，但仍错位

Step 0052 继续复用相同 405 个 task-rooted plans、20,866 个 operations、Qwen2.5-3B、
标准 scorer 和 recurrence comparators。它不再让 `continue` 与所有 exact labels 在
同一个 grammar 里竞争。对每个后续 operation，第一阶段只根据 public task、causal
evidence 和 active responsibility 输出 `continue` 或 `change`；只有 `change` 后的
第二阶段才注入 unordered responsibility inventory 并选择 exact label。选出的 label
仍成为后续状态，所以这是 same-operation factorization，不是 causal independence。

完整 source-only 推理有效。20,313 个 continuation calls 产生 3,954 次 change 和
16,359 次 learned continue；五个 one-item plans 另有 148 次 forced continue。
预测 instance 从 Step0051 的 20,465 降为 4,359，boundary rate 从 `0.980402` 降到
`0.193246`。这证明两阶段接口消除了 near-all-switch degeneration。

标准 gold score 也实质改善，但未达到 adoption comparator：

- exact unlabeled span F1 `0.020802`，高于 Step0051 joint interface 的 `0.008201`，
  paired task-cluster interval `[+0.007819,+0.017686]`；
- ordinary B-cubed F1 `0.622385`，高于 joint 的 `0.264371`，但仍低于 current
  recurrence `0.649173` 和 multi-resolution recurrence `0.662740`；
- exact span 相对 current 的 interval 为 `[-0.059199,-0.036636]`，相对 multires
  为 `[-0.045914,-0.026248]`；四个 framework 的 exact-span F1 都更低；
- boundary precision/recall/F1 为 `0.126201/0.196225/0.153609`，漏掉 2,044 个
  human boundaries 并增加 3,455 个 false boundaries。

因此注册假设被否定，candidate 不进入发布或正面论文。它解决的是 transition-form
degeneration，不是 human-stage placement。

这次还澄清了 prompt isolation 的精确定义。Continuation call 没有注入 alternative-
label inventory，但 public task/evidence 自然包含其他 retained responsibility exact
string 的情况有 1,138/20,313 (`5.60%`)；因此不能把比较解释成 label visibility 的
单因素消融。Operation-triplet `A→B→A` 为 1,605，collapsed stage-sequence
`A→B→A` 为 2,808。3,954 次 change 中，3,348 次返回此前用过的 responsibility，
606 次首次进入新 responsibility。这说明 fixed plan 的大部分 change 是在少数
responsibility types 间复访，而不是逐步发现完整层次。

Step 0052 仍只评分 flat stage partition，没有验证 nested subtask、phase/strategy、
semantic action、object、result 或生成 label 的正确性。它不支持继续微调同一局部
prompt；若继续 task-semantic 方向，需要新的、可观察的 task-continuity 信息，而非
增加系统字段、阈值、depth cap 或 post-hoc contraction。

完整 plan、三次串行审查、preflight、full run、独立复算与修正位于：

```text
docs/tmp/build-and-evaluate/step-0052-20260720T064136-0700/experiment-001/
```

## 6. 两个算法最本质的差别

| 问题 | Information gain | Cross-run recurrence |
|---|---|---|
| 学习目标 | 切后字段更纯 | 相邻行为跨运行更稳定地共同出现 |
| 基本对象 | 一个 session 内的 interval/cut | 多个 session 中的 directed action pair |
| 输出结构 | 递归 variable-depth partition path | 连续 segment + reusable motif identity |
| 能否容纳异质 action | 容易错误拆开 | 可以，只要 transition recurrent |
| 是否需要其他运行 | 不需要 | 需要 reference sessions；也可用当前选中 corpus 做 reference |
| 主要自由度 | eligible fields、penalty、depth | action representation、reference、cutoff policy |
| 主要失败模式 | purity 与 operation continuity 错配 | pair recurrence 与真实 context/granularity 错配 |
| 当前状态 | 历史实现，已被完整结果替换 | multi-resolution 为当前发布候选；calibration 为可选模式 |

一句话概括：

> Information gain 把 operation 当成“字段分布相对同质的区间”；recurrence 把
> operation 当成“跨运行可重复出现的行为片段”。现有 annotation 更支持后一个
> 定义，但尚未证明它覆盖所有 agent、所有 operation 粒度或完整语义命名。

## 7. 当前研究结论与下一证据边界

当前选择 recurrence，不是因为 information gain 不够“复杂”，而是因为完整实验
表明后者优化了错误的 proxy。当前发布候选保持同一个简单原则：在 coarse 与
detail 两个可见分辨率分别判断 recurrence，任一分辨率支持 continuity 就不切；
随后连续分段并生成 coarse motif identity。可选 grouped-reference 模式只拟合同
一个 scalar cutoff。

已有结果支持：

- 相对旧 heuristic 和 cap-free information gain，cross-run recurrence 更接近
  OSWorld 的人类 operation partition；
- monotone cross-action 规则能在不新增原边界的前提下修复 CodeTrace 的一类
  fragmentation；
- multi-resolution recurrence 能在不新增粗边界、且对 detail-free 输入精确回退
  的前提下进一步减少 CodeTrace fragmentation；
- 独立 grouped reference 可以在两个现有 population 上提高 B-cubed partition
  fidelity。

已有结果不支持：

- operation motif 名称已经等同于正确 task/phase/action semantic tag；
- 所有 workload 上 boundary F1 都改善；
- recurrence 自动降低诊断者的检查量；
- 一个 RQ3 component 的成功已经回答完整 RQ3；
- 算法本身已经证明论文最终的 attribution/localization/diagnostic-value claim。

如果继续算法研究，最有价值的方向不是再加一个 cutoff，而是检验一个能打破
pair-level observational aliasing 的真实可见信号，同时保持论文原始 story、四个
RQ 和 operation/operation-stack 模型不变。

## 8. 代码与证据索引

| 内容 | 位置 |
|---|---|
| 当前 recurrence Rust 实现 | `agentpprof/src/profile.rs` |
| 当前 CLI 参数与 legacy rejection | `agentpprof/src/main.rs` |
| Information-gain 完整历史代码 | `git show fe0704f9b:agentpprof/src/profile.rs` |
| Information-gain 算法原始说明 | `docs/tmp/build-and-evaluate/step-0017-20260714T121012-0700/01-experiment-gate/loop-002-rq3-rust-inducer-fidelity/algorithm-note.md` |
| Fixed-depth 完整实验 | `docs/tmp/build-and-evaluate/step-0017-20260714T121012-0700/` |
| Cap-free 完整实验 | `docs/tmp/build-and-evaluate/step-0018-20260714T160153-0700/` |
| Recurrence 选择、完整 OSWorld 与 Rust port | `docs/tmp/build-and-evaluate/step-0020-20260715T001404-0700/` |
| Monotone cross-action 修复 | `docs/tmp/build-and-evaluate/step-0024-20260715T042557-0700/` |
| 被拒绝的 local-minimum 变体 | `docs/tmp/build-and-evaluate/step-0025-20260715T054105-0700/` |
| Pair/context aliasing 诊断 | `docs/tmp/build-and-evaluate/step-0026-20260715T063827-0700/` |
| Grouped-reference calibration 与完整 replay | `docs/tmp/build-and-evaluate/step-0030-20260715T161256-0700/` |
| Multi-resolution recurrence 与完整 replay | `docs/tmp/build-and-evaluate/step-0049-20260719T195559-0700/experiment-001/` |
| Qwen 3B semantic-stack 与 contraction | `docs/tmp/build-and-evaluate/step-0049-20260719T195559-0700/experiment-003/` 和 `experiment-004/` |
| Task-rooted plan 与 numeric-index confound | `docs/tmp/build-and-evaluate/step-0050-20260720T022249-0700/experiment-001/` |
| Index-free semantic transition interface | `docs/tmp/build-and-evaluate/step-0051-20260720T052839-0700/experiment-001/` |
| Decoupled responsibility continuation | `docs/tmp/build-and-evaluate/step-0052-20260720T064136-0700/experiment-001/` |

历史与当前源代码共同构成可审计记录：失败实现不留在 release runtime，但不从
Git 或 experiment reports 中删除；当前实现不冒充先前算法，也不把开发结果扩大
成整篇论文的最终结论。
