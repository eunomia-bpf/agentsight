# agentpprof 语义剖析论文评估说明

Last updated: 2026-07-04

本文档是中文论文 `main.tex` 的 claim ledger 和实验边界说明。旧的
AgentFlame 本机 session/prompt 语义系统效应稿件已经不再是当前主线。当前主线
只保留两个核心抽象：`operation` 和 `operation stack`。Prompt、session、tool
call、process、syscall、GUI action、plan、subagent、安全标签和质量标签都只是
operation 的形态或字段。

## Thesis

Agent 轨迹剖析不应该绑定到固定 prompt/session/span 边界。一个更小的模型是：
把所有可观测事件归一化为带字段和权重的 operations，再由用户指定 mapping、
view 和 stack 字段进行递归折叠。这样同一段轨迹可以按 dataset、task、phase、
tool、action、human group、safety、looping 或 step quality 等不同深度分析。

## Claim Ledger

| Claim | 当前结论 | 证据 | 不能声称的内容 |
|---|---|---|---|
| C1：异构标注 agent 轨迹可以统一为 operation JSONL。 | supported | R279-R292 覆盖 15 个公开标注轨迹数据源。核心 R291 14 数据集有 42,590 operations；R292 补充 ScaleCUA 后有 47,590 operations。R293 用 profile spec 复现 R291 AgentNet 查询，不改 operation 输入。R294 证明本地 Codex session 可导出为标准 trace，再导入或转成 operation JSONL，并得到相同 folded stack。R295 机械读取 tracked R282-R294 artifacts，把该 claim gate 为 supported。R296 将 C1 证据放入 reviewer evidence packet。R298 将异构 trace object model 问题映射到 15 数据集 / 47,590 operations 的证据。 | 不能声称任意 agent 数据都可零成本转换，尤其是只有图片、无顺序、gated 或缺少 action label 的数据。 |
| C2：operation stack 是可递归配置的，不应固定绑定 session/prompt。 | supported with scoped limits | R286 在同一 13,265 operations 上从 9 个 dataset stacks 展开到 57 个 phase stacks、226 个 tool/semantic stacks、455 个 action stacks 和 3,757 个 fixed-session stacks。R277 显示固定 demo/session 比 mapped stack 多 10.5x unique stacks。R293 在同一 16,741 个 AgentNet operations 上复现 608-stack 诊断视图，并用 CLI 覆盖 stack 得到 83-stack 粗粒度视图。R295 gate 结论是 recursive stacks 支持 task/phase/action/human-group/safety/quality views，但不支持完美 intent recovery。R296 索引 11 个非 flamegraph/evidence-navigation entries，使这些结果可以按 claim 审计。R298 把 recursive depth、human/subtask boundaries、failure/safety/quality diagnostics 组织成真实问题证据块。 | 不能声称某一个默认 stack 对所有问题最优，也不能声称完整恢复所有真实意图边界。 |
| C3：mapping/tagging 可以作为一等字段派生机制。 | partially supported with supervised expansion probe | R281 生成 rules 复现手写 mapping；R282 held-out compression 为 19.091，no-map baseline 为 14.049；R285 leave-dataset-out 在 9 个 datasets 中 6 个减少 stacks，0 个负向回归。R295 将 paper wording 限定为 label-derived deterministic mappings improve semantic aggregation。R296 将 mapping reduction 和 negative controls 做成 reviewer-facing 指标。R297 在 OSWorld-Human held-out sessions 上训练 supervised adjacent-boundary backend，F1=0.7735，并把预测边界写成 `learned_group_pattern` 字段后由 Rust profiler 折叠。R298 把 unified field-derivation extension point 列为 novelty claim。 | 不能声称无监督或 LLM-backed boundary detector 已完成，也不能声称该 backend 已泛化到所有 agent 轨迹。 |
| C4：operation stacks 能恢复有意义的人工或标注边界。 | partially supported with strong OSWorld-Human evidence | R290 OSWorld-Human 覆盖 369 tasks 和 6,010 operations。Exact grouped oracle 覆盖 320 tasks、4,011 operations、2,075 groups。`group_pattern:human_group` boundary F1 为 0.627，precision 为 1.0。 | Recall 只有 0.456，不能声称完整恢复人工 subtask 边界。 |
| C5：profiler 能做 failure、safety 和 step-quality 诊断，而不只画 flamegraph。 | supported as mechanism, not user utility | R288 AgentRewardBench 显示 repeat signal 对 looping 的 V-measure 为 0.378，而 step-error baseline 为 0.011。R289 SATraj-OS 带 622 unsafe operations 和 5 类 attack type。R291 AgentNet 带 16,741 operations 的 step correctness/redundancy 字段。 | 不能声称这些 views 已经提升开发者任务准确率或耗时。 |
| C6：ScaleCUA 是有用补充。 | supplemental only | R292 流式采样 5,000 Ubuntu navigation rows，131 sessions，最大 step 48。它证明 history-state/history-depth 可作为 operation fields。 | 该子集主要是 click/terminate，不能作为复杂 action taxonomy 或 boundary detector 的核心证据。 |

## Best Dataset Families

当前最适合论文主结论的不是所有数据源，而是能提供顺序和 oracle 的数据源。

| 优先级 | 数据源 | 为什么适合 |
|---|---|---|
| 1 | OSWorld-Human | 同时有 single-action 和 grouped-action，可以直接评价递归边界。 |
| 2 | AgentNet | 大规模 human desktop 轨迹，带 task outcome、step correctness 和 redundancy。 |
| 3 | AgentRewardBench + SATraj-OS | 提供 failure、looping、side-effect、安全和 attack-type 诊断，支撑 profiler 不限于 flamegraph 的机制性 claim。 |
| 4 | GUI-Odyssey + tau-bench + ToolBench | 覆盖 mobile GUI、tool-agent-user dialogue 和 API/tool traces，证明 abstraction 跨域。 |
| 补充 | ScaleCUA | 流式公开 annotation JSONL，适合验证 GUI history-depth 字段，但 action 类型过窄。 |

## Experiment-To-Claim Map

| Run | 作用 | 关键数值 | 论文中使用方式 |
|---|---|---|---|
| R277 | 固定 session/demo 边界消融 | mapped/flat 103 stacks；fixed session/demo 1,083 stacks | 说明 session 是 drilldown field，不是默认边界。 |
| R280 | operation-stack quality scorer | R279 13,265 ops；phase/action V=0.765；boundary F1=0.814 | 建立非 flamegraph quality report。 |
| R282 | held-out mapping validation | 3,990 held-out ops；mapped compression 19.091 vs no-map 14.049 | 证明 mapping rules 不只是 hand-written visualization。 |
| R285 | leave-dataset-out mapping validation | 6/9 positive stack reduction；0 negative；1162.005 weighted stack reduction per 1k ops | 支持 operation-family precedence 和跨数据集泛化。 |
| R286 | recursive stack-depth sweep | 9 dataset stacks 到 3,757 fixed-session stacks | 主证明：同一 operations 可任意深度递归折叠。 |
| R288 | AgentRewardBench failure diagnostics | repeat-signal/looping V=0.378；step-error/looping V=0.011 | 证明 sequence-derived operation fields 有诊断价值。 |
| R289 | SATraj-OS safety diagnostics | 4,285 ops；622 unsafe；5 attack types | 证明 safety/attack labels 是普通 operation fields。 |
| R290 | OSWorld-Human grouped boundary | group boundary F1=0.627，precision=1.0 | 最强人工边界 oracle。 |
| R291 | AgentNet desktop step quality | 16,741 ops；step correctness/redundancy 100% field coverage | 最大 human desktop step-quality oracle。 |
| R292 | ScaleCUA supplement | 5,000 ops；131 sessions；max step 48 | 补充 GUI history-depth，不作为主 claim。 |
| R293 | Profile-spec reproducibility | 同一 16,741 AgentNet ops；spec 复现 608 stacks；CLI override 得到 83 stacks | 证明 operation-stack query 可配置、可提交、可覆盖，不是固定 prompt/session hierarchy。 |
| R294 | Agent-session trace exchange | public Codex fixture；1 trace session；6 operations；trace import 和 operation import 都是 6 samples / 5 stacks | 证明本地原生 session 可以导出、导入并桥接到 operation JSONL。 |
| R295 | Paper claim synthesis gate | 读取 R282-R294 tracked artifacts；输出 3 个 claim verdicts、6 个 evidence bundles 和 unsupported claims | 把论文 claim 从 artifact 机械回溯：C1 supported，C2 supported with scoped limits，C3 partial。 |
| R296 | Reviewer evidence packet | 读取 39 个 tracked/clean R282-R295 artifacts；输出 11 个非 flamegraph/evidence-navigation entries、4 个 reviewer questions 和 3 个 expansion gates | 把 claim、负结果、可视化和源路径组织成一个可审计 evidence packet。 |
| R297 | Supervised boundary backend | OSWorld-Human held-out：191 train sessions、96 test sessions、1,036 test adjacent pairs；learned F1=0.7735；Rust fold 1,132 ops / 74 stacks | 说明 boundary backend 的正确接口是写 operation fields，operation stack 仍由 profiler 按用户 stack 折叠。 |
| R298 | Paper value/novelty synthesis | 读取 R295/R296/R297 和 R288/R289/R291 diagnostic artifacts；输出 6 个 real-problem evidence blocks、4 个 novelty claims、must-not-claim gate 和 remaining level-4 gaps | 把“profiler 解决真实问题且有新意”的论证从 tracked artifacts 机械回溯，同时明确当前仍只是机制 claim 的 level-3 evidence、接近 level 4。 |

## Paper-Ready Wording

可以写：

> We show that a two-object model, operations plus operation stacks, is
> sufficient to express profiling views over 15 public labeled agent
> trajectory sources. The same Rust profiler folds operations at dataset,
> task, phase, tool, action, human-group, safety, looping, and step-quality
> depths by changing mapping and stack specifications, not by adding
> prompt-, GUI-, or safety-specific profiler objects.
> Profile specs make these experiments replayable without changing the
> two-object model: they package operation files, mappings, view, stack, and
> output choices, while CLI flags can still override the stack query.
> Agent-session traces provide a replayable import/export format before the
> operation layer; converting them to operation JSONL preserves the same stack
> projection path.
> A reviewer evidence packet links claim verdicts to depth sweeps, stack trees,
> transition/top-field reports, quality reports, grouped-boundary reports,
> history-depth reports, and negative controls.
> Supervised boundary backends remain outside the core profiler abstraction:
> they derive fields such as `learned_group_pattern`; the profiler still folds
> operations using a user-selected operation stack.

中文论文中应写成：

> 本文的贡献不是又画一种 agent flamegraph，而是把 agent 轨迹 profiling 的边界选择
> 从固定 prompt/session/span 层级中释放出来。所有对象都先成为 operations，mapping
> 和 tagging 只派生字段，operation stack 再根据用户问题递归折叠。
> Profile spec 只是把 operation 文件、mapping、view、stack 和输出路径记录成可复现
> 配置；它不增加第三个抽象，命令行仍可覆盖 stack 以回答不同问题。
> Agent-session trace 是 session 交换格式，不是 profiler 抽象；导入后仍然要转成
> operations，再由 operation stack 折叠。
> Reviewer evidence packet 只是证据导航层，不是第三个抽象；它把 claim gate、
> 多视图报告、负结果和 source path 放在一起，方便审稿人从论文表述追到 artifact。
> Boundary backend 也不是第三个抽象；它只派生 `learned_group_pattern` 等字段，
> 之后仍由 operation stack 做递归折叠。
> Paper value/novelty synthesis 也不是新实证结果；它把 heterogeneous trace objects、
> recursive depth choice、field derivation、human/subtask boundaries、
> failure/safety diagnostics 和 artifact auditability 映射到 tracked artifacts，
> 并保留 unsupervised intent discovery、developer productivity 等不能声称的边界。

不能写：

> agentpprof 已经自动发现所有真实意图边界。

也不能写：

> 这些可视化已经证明能提升开发者效率。

## Next Gates

1. Boundary detector gate：在 OSWorld-Human 和 AgentNet 上加入非规则或 model-backed
   mapping backend，并与 current deterministic mapping 比较。
2. User-utility gate：用 OSWorld-Human/AgentRewardBench/SATraj 生成真实 debugging tasks，
   比较 flat trace、fixed session stack 和 operation-stack views 的正确率与耗时。
3. Scale gate：对 AgentNet full Ubuntu/Windows/macOS 或 OSWorld-Verified 做更大流式
   sampling，但仍不保存完整源数据或图片归档。
4. Paper hygiene gate：所有数字必须能追到 `docs/visexp/out/*/*.json`，所有外部数据只
   以 redacted operations 和 tracked reports 进入仓库。
