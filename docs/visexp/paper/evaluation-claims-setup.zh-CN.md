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
predicate、view 和 stack 字段进行递归折叠。这样同一段轨迹可以按 dataset、task、phase、
tool、action、human group、safety、looping 或 step quality 等不同深度分析。

## Claim Ledger

| Claim | 当前结论 | 证据 | 不能声称的内容 |
|---|---|---|---|
| C1：异构标注 agent 轨迹可以统一为 operation JSONL。 | supported | R279-R292 覆盖 15 个公开标注轨迹数据源。核心 R291 14 数据集有 42,590 operations；R292 补充 ScaleCUA 后有 47,590 operations。R293 用 profile spec 复现 R291 AgentNet 查询，不改 operation 输入。R294/R303 证明本地 Codex session 可导出为 exchange trace，再导入或转成 operation JSONL，并得到相同 folded stack。R306 进一步把同一 fixture 导出为 Chrome Trace Event JSON，再导入为 operation JSONL；direct trace、direct operation 和 Chrome-import operation 均为 6 samples / 5 stacks 且 folded 字节一致。R295 机械读取 tracked R282-R294 artifacts，把该 claim gate 为 supported。R296 将 C1 证据放入 reviewer evidence packet。R298 将异构 trace object model 问题映射到 15 数据集 / 47,590 operations 的证据。R307 在 R300-R306 之后刷新 claim gate，保持 C1 supported，但明确排除完整 Chrome/OpenTelemetry 生态兼容和第三 trace 抽象。 | 不能声称任意 agent 数据都可零成本转换，尤其是只有图片、无顺序、gated 或缺少 action label 的数据；R306/R307 也不是完整 OpenTelemetry/Chrome trace 生态兼容性评估。 |
| C2：operation stack 是可递归配置的，不应固定绑定 session/prompt。 | supported with scoped limits | R286 在同一 13,265 operations 上从 9 个 dataset stacks 展开到 57 个 phase stacks、226 个 tool/semantic stacks、455 个 action stacks 和 3,757 个 fixed-session stacks。R277 显示固定 demo/session 比 mapped stack 多 10.5x unique stacks。R293 在同一 16,741 个 AgentNet operations 上复现 608-stack 诊断视图，并用 CLI 覆盖 stack 得到 83-stack 粗粒度视图。R321 进一步把 profile-spec predicate 接到 Rust 路径：同一 R300 operation JSONL 上，mapping-derived `where_rules` 分别选出 729/729、714/714 和 4,285/4,285 个预期 operations 后再折叠。R295 gate 结论是 recursive stacks 支持 task/phase/action/human-group/safety/quality views，但不支持完美 intent recovery。R296 索引 11 个非 flamegraph/evidence-navigation entries，使这些结果可以按 claim 审计。R298 把 recursive depth、human/subtask boundaries、failure/safety/quality diagnostics 组织成真实问题证据块。 | 不能声称某一个默认 stack 对所有问题最优，也不能声称完整恢复所有真实意图边界。 |
| C3：mapping/tagging 可以作为一等字段派生机制。 | partially supported with supervised expansion probe | R281 生成 rules 复现手写 mapping；R282 held-out compression 为 19.091，no-map baseline 为 14.049；R285 leave-dataset-out 在 9 个 datasets 中 6 个减少 stacks，0 个负向回归。R295 将 paper wording 限定为 label-derived deterministic mappings improve semantic aggregation。R296 将 mapping reduction 和 negative controls 做成 reviewer-facing 指标。R297 在 OSWorld-Human held-out sessions 上训练 supervised adjacent-boundary backend，F1=0.7735，并把预测边界写成 `learned_group_pattern` 字段后由 Rust profiler 折叠。R298 把 unified field-derivation extension point 列为 novelty claim。R299 在现有 operation JSONL 上检查 7 个 boundary candidates，训练 4 个并做 calibration/simple-baseline comparison：OSWorld-Human F1=0.6916，AgentNet step-correct/redundant F1=0.3197/0.3361，AgentRewardBench looping learned F1=0.7833 但 `repeat_signal_change` baseline F1=1.0。 | 不能声称无监督或 LLM-backed boundary detector 已完成，也不能声称存在一个通用跨家族 boundary detector；每个标签家族都需要 suitability、calibration 和简单 baseline gate。 |
| C4：operation stacks 能恢复有意义的人工或标注边界。 | partially supported with strong OSWorld-Human evidence | R290 OSWorld-Human 覆盖 369 tasks 和 6,010 operations。Exact grouped oracle 覆盖 320 tasks、4,011 operations、2,075 groups。`group_pattern:human_group` boundary F1 为 0.627，precision 为 1.0。 | Recall 只有 0.456，不能声称完整恢复人工 subtask 边界。 |
| C5：profiler 能做 failure、safety 和 step-quality 诊断，而不只画 flamegraph。 | supported as hidden-label profiler accuracy benchmark, not human utility | R288--R291 把 looping、side-effect、安全、attack type、step correctness 和 redundancy 作为 ordinary operation fields。R300--R305 在 6 个 oracle-backed tasks / 34,539 operations 上比较 flat、fixed-session、operation-stack 和 label-drilldown views：operation-stack 相比 flat 的 median top-positive lift 为 5.726x；R305 中 operation-stack 的 median work/recall/lift 为 0.0937/0.188/1.6509，fixed-session 为 0.0163/0.0226/1.6615。R308/R309/R311 显示 operation-stack 在 6/6 tasks 上比 flat selective、6/6 含 positive group、5/6 有 high-lift evidence、5/6 selected recall 高于 fixed-session，但只有 2/6 selected work 低于 fixed-session。R313 的 162 个非 oracle frontier points 中，operation-stack 在 6/6 tasks 上进入 frontier，best lift 为 4/6，30% work 内 best recall 为 4/6，flat 和 fixed-session 也都是 6/6 frontier counterpoints。R320 进一步把 profiling output 当作 ranking/localization result，用 hidden labels 评分 144 个 view/ranker policies：operation-stack query-aware top-5 median work 为 0.0937，而 flat 为 1.0；相对 fixed-session query-aware，operation-stack top-5 recall 在 5/6 tasks 上更高，并把 median groups 从 285.0 降到 157.5；query-aware ranking 相比 width-only operation-stack ranking 在 6/6 tasks 上提高 AP；R320 还输出 task-level optimization insights，指出 safety 适合 environment/phase/action stack，looping 需要 prevalence-aware ranking，side-effect 和 human-boundary 需要不同 depth/ranker。R322 把 visible `rank_rules` 接到 Rust JSON profiler：同一 6 个 tasks 上 AP 相比 width 提升 4/6，top-5 lift 提升 3/6，但 SATraj 和 side-effect 反例说明二值 stack-text boost 不能替代 R320 的 group-feature query-aware ranker。R323 在同一 R300 operation JSONL 上比较 `rank_mode=width-boost` 和 `rank_mode=rule-score`：rule-score 相比 width-boost AP 提升 4/6、top-5 lift 提升 4/6、first-positive work 改善 3/6，并把 SATraj first-positive work 从 0.6376 降到 0.0842；side-effect 和 OSWorld-Human 仍是反例。R324 把 per-operation visible feature density 接到 Rust `rank_op_rules`，并先为 Rust 生成删除 oracle fields 的 visible-operation profiler input：semantic stack 上 AP 相比 width 提升 5/6、top-5 lift 提升 4/6、first-positive work 改善 5/6；coarse stack 上 AP 提升 4/6、first-positive work 改善 5/6，并显著减少 group 数；OSWorld-Human 仍说明 boundary 任务需要 boundary-derived fields。R325 在同一 Rust profile-spec 路径上做 leave-one-feature ablation：发现 7 个 critical feature instances 和 3 个 misleading feature instances；coarse stack 只在 2/6 tasks 上 AP 更好，但在 6/6 tasks 上减少 group 数。R326 继续复用 R324 scrubbed profiler input 和 R325 findings：global equal visible feature bank 在 semantic/coarse stack 上 AP 相比 width 分别赢 4/6 和 5/6 tasks，task-equal 在 8/12 task/depth variants 上与 weighted policy 的 AP 差距不超过 0.02，R325-guided repair 在 2/3 misleading-feature cases 上改善 AP、在 2/3 cases 上改善 first-positive work，其中 1/3 同时改善两者。R329 复用同一 scrubbed visible-operation profiler input 和 6 个 oracle-backed tasks，评估 96 个 policy/task/stack combinations，并在 leave-task 与 leave-dataset protocol 下只用非目标任务评分选择 policy；目标 hidden labels 只用于最终 scoring。两种 protocol 在 semantic/coarse stack 上 AP 均为 4/6 胜过 width，semantic first-positive work 均为 6/6 改善，7/12 variants 不低于 target-equal policy 超过 0.02 AP，平均 gap-to-oracle candidate 约 0.032 AP。R330 读取 tracked R320 report/CSV，对 6 个 task-family 的 paired deltas 做 10,000 次 bootstrap：相对 flat，operation-stack query-aware 的 AP、top-5 work、30% budget recall 和 work-to-first-positive 方向稳定；相对 fixed-session，top-5 recall、top-5 F1 和 groups 方向稳定；相对 width-only operation-stack，AP、top-5 work 和 work-to-first-positive 方向稳定；同时 flat top-5 recall、fixed-session work/WTFP/AP 和 raw-action mapping comparison 被保留为 mixed/counterpoint。R331 固定 visible policy 的 group/ranking order 并随机重分配 hidden positives 做 2,000 次 label-permutation null：operation-stack query-aware AP 在 6/6 tasks 超过 95% null，budget30 recall 在 5/6 tasks 超过 null；但 top-5 precision 只有 3/6，work-to-first-positive 为 0/6，fixed-session 和 raw-action AP 也都是 6/6 超过 null。R315/R316 仍保留为可选 controlled analyst-study protocol 和 scripted readout，不是主 claim 证据。 | 可以 claim profiler 本身在真实标注 trace 上有 localization/ranking fidelity、work/fragmentation tradeoff、prevalence/group-size negative-control evidence 和 actionability；不能声称这些 views 已经提升开发者/agent analyst 准确率、耗时或 productivity；不能声称 universal fixed-session 或 single-view dominance、automatic anomaly detection、完整 trace ecosystem 兼容、trace-platform feature parity、完整 intent-boundary discovery，或已部署的 label-free universal ranker；R330 也不是 per-operation independence claim，R331 也不支持所有 hot-group 指标。 |
| C6：ScaleCUA 是有用补充。 | supplemental only | R292 流式采样 5,000 Ubuntu navigation rows，131 sessions，最大 step 48。它证明 history-state/history-depth 可作为 operation fields。 | 该子集主要是 click/terminate，不能作为复杂 action taxonomy 或 boundary detector 的核心证据。 |
| C7：profile-spec 路径可复现并具有可报告的离线成本。 | supported as artifact/reproducibility evidence, not live overhead | R327 复用已提交的 R300/R324/R326 profile specs 和已提交 operation JSONL，不同步或下载数据集；76 个 specs 每个重复执行两次，形成 152 次 Rust `agentpprof --profile-spec` 调用。Semantic profile hash、samples 和 unique stacks 稳定为 76/76；median runtime 为 1.581s，p95 为 2.719s，max 为 4.273s；median output size 为 37,546 bytes，max unique stacks 为 2,012。默认 raw-byte hash 只有 4/76 稳定，因为 JSON profile 包含 `generated_at`。R328 在同一 76 个 specs / 152 次调用上启用 `--deterministic-output`，固定 JSON `generated_at` 和 pprof profile time，使 semantic 与 raw-byte determinism 均达到 76/76；该 run 的 median runtime 为 1.578s，p95 为 2.731s，max 为 4.298s，median output size 仍为 37,546 bytes，max unique stacks 仍为 2,012。 | 只能 claim 离线 profile-spec artifact reproducibility、opt-in byte-stable artifact mode 和本地执行成本；不能声称 live eBPF capture overhead、生产环境 overhead、人类效率提升或完整 trace ecosystem 兼容。 |

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
| R294/R303 | Agent-session trace exchange | public Codex fixture；1 trace session；6 operations；`trace_filesystem_portable=true`；trace import 和 operation import 都是 6 samples / 5 stacks；R303 用一条脚本复现 export/import/convert/equality check | 证明本地原生 session 可以导出、导入并桥接到 operation JSONL，且 trace 只是 exchange format，不是第三个 profiler 抽象；filesystem portability 不等于完整 preview 脱敏。 |
| R306 | Chrome/Perfetto trace exchange | public Codex fixture；6 Chrome complete events；6 direct operations；6 Chrome-import operations；direct trace、direct operation 和 Chrome-import operation 均为 6 samples / 5 stacks 且 folded 字节一致 | 证明标准 trace 可以作为 exchange container；导入后仍然进入 operation JSONL 和 operation-stack folding，不新增 profiler 抽象。 |
| R295 | Paper claim synthesis gate | 读取 R282-R294 tracked artifacts；输出 3 个 claim verdicts、6 个 evidence bundles 和 unsupported claims | 把论文 claim 从 artifact 机械回溯：C1 supported，C2 supported with scoped limits，C3 partial。 |
| R296 | Reviewer evidence packet | 读取 39 个 tracked/clean R282-R295 artifacts；输出 11 个非 flamegraph/evidence-navigation entries、4 个 reviewer questions 和 3 个 expansion gates | 把 claim、负结果、可视化和源路径组织成一个可审计 evidence packet。 |
| R297 | Supervised boundary backend | OSWorld-Human held-out：191 train sessions、96 test sessions、1,036 test adjacent pairs；learned F1=0.7735；Rust fold 1,132 ops / 74 stacks | 说明 boundary backend 的正确接口是写 operation fields，operation stack 仍由 profiler 按用户 stack 折叠。 |
| R298 | Paper value/novelty synthesis | 读取 R295/R296/R297 和 R288/R289/R291 diagnostic artifacts；输出 6 个 real-problem evidence blocks、4 个 novelty claims、must-not-claim gate 和 remaining level-4 gaps | 把“profiler 解决真实问题且有新意”的论证从 tracked artifacts 机械回溯，同时明确当前仍只是机制 claim 的 level-3 evidence、接近 level 4。 |
| R299 | Boundary-family calibration | 不同步新数据；检查 7 个 existing candidates；4 个通过 suitability/positive split；Rust fold 8,961 ops / 1,548 stacks | 证明 boundary backend 可以作为统一 field-derivation 接口复制到多个标签家族，但结果必须按家族校准；AgentNet 边界可学但低 precision，AgentReward looping 应优先用简单 `repeat_signal_change` 字段。 |
| R300 | Operation-query utility proxy | 6 个 oracle-backed tasks；34,539 ops；flat/fixed/operation/label stacks 为 6/2,012/944/318；operation-stack vs flat lift 5.726x，inspection fraction 0.2879；vs fixed-session group ratio 0.554、session-support ratio 5.5 | 把“真实问题价值”推进到自动化 task proxy：operation stack 比 flat 更能集中 positives，比 fixed-session 更能跨 session 聚合，但还不能 claim 人类效率。 |
| R301 | Width-ranked analyst task proxy | 复用 R300 的 6 个 tasks；输出 visible-task-packets 和 hidden answer-key；168 个 task/view/budget scores；30% operation budget 下 operation-stack recall 0.336 / 4.5 groups，fixed-session recall 0.284 / 25.5 groups；top-10 width-ranked groups 下 operation-stack recall 0.641，fixed-session 0.195 | 把 R300 的 oracle-sorted 上界推进到 label-hidden task packet：默认宽度排序下 operation stack 仍能跨 session 暴露更多 positives，但宽度排序不是 detector，仍不能 claim 人类效率。 |
| R302 | Label-hidden analyst ranking proxy | 复用 R300/R301 的 6 个 tasks；192 个 task/view/ranker/budget scores；top-10 query-aware operation-stack groups 检查 0.116 operation fraction、lift 1.587，width 检查 0.671、lift 1.079；30% budget 下 query-aware recall 0.390，width recall 0.340，但 groups 39.5 vs 4.5 | 证明 operation stack 不限于 flamegraph 宽度视图，也可以承载 query-aware/risk ranking policy；但 ranker 是可见字段 heuristic，不是 learned detector 或 human utility。 |
| R304 | Operation-stack case packet | 复用 R300/R302 的 6 个 tasks；30 个 top-5 query-aware case groups；visible-case-packet 和 hidden answer-key 分离；median work fraction 0.0937、recall 0.188、lift 1.6509 | 把自动化 proxy 推进到 reviewer 可审计 case evidence；visible packet 只展示 ordinary operation fields，但仍不是 human study 或 detector。 |
| R305 | Cross-view case-packet baseline | 复用同一 6 个 tasks；18 个 task-view case packets；flat work/recall 1.0/1.0；fixed work 0.0163、recall 0.0226、lift 1.6615；operation work 0.0937、recall 0.188、lift 1.6509；operation vs fixed recall ratio 3.63、lift ratio 1.268、work ratio 1.717 | 证明 operation stack 是 flat 和 fixed-session 之间的可配置分析折中，而不是无条件支配每个 baseline。 |
| R307 | Paper claim readiness refresh | 读取 R295/R298、R303 和 R300-R306 tracked artifacts；4 个 claim verdicts；C1 supported，C2 supported with scoped limits，C3 partial，C4 当时 supported as automated proxy only；analysis suite 为 6 tasks / 34,539 operations；当时的 next gate 是 controlled analyst study，但 R320 已把主门槛改为 profiler accuracy。 | 把 R300-R306 后的论文 claim 收敛为历史 scoped wording；当前主 claim 应以 R320 hidden-label profiler accuracy 为准，user-utility study 只支撑 productivity/time-to-answer。 |
| R308 | Analyst first-evidence proxy | 读取 R305 visible packets 和 hidden answer key；6 个 tasks / 18 个 task-view packets；operation-stack positive group coverage 为 6/6，high-lift coverage 为 5/6，median selected work/recall/top-group lift 为 0.0937/0.188/1.5739；fixed-session high-lift coverage 为 4/6 且 first-positive work 更低 | 把 user-utility gate 推近到可执行 protocol，但仍只是 automated first-evidence proxy，不是 human study。 |
| R309 | Problem-value synthesis | 读取 R298/R300/R302/R305/R308 tracked artifacts；6 个 problem cards；4 个 datasets；34,539 task-operations；operation-stack high-lift coverage 为 5/6；selected work/recall/top lift 为 0.0937/0.188/1.5739；top-10 query-aware work/lift 为 0.1163/1.5867，而 width ranking 为 0.6713/1.0795 | 把已有 proxy 结果按真实问题拆解：safety 是强 selective win，AgentNet quality 是低 recall 高 lift，looping 过于普遍而缺少 high-lift，side-effect 和 human-boundary 暴露 ranking-depth sensitivity。 |
| R310 | Paper evidence matrix | 读取 tracked/clean R307/R309 artifacts；输出 evidence-matrix JSON、Markdown、CSV、TeX 和 HTML；4 个 claim rows 中 C1、C2、C4 是 scoped paper-ready，C3 保持 partial；R309 的 4 datasets / 6 tasks / 34,539 operations / 3,699 positives、5/6 high-lift、6/6 比 flat 更 selective、5/6 selected recall 高于 fixed-session、4/6 fixed-session work 更低都进入 claim matrix。 | 把当前论文 claim、关键数字和 must-not-claim 边界压成可直接引用的表格/audit artifact；它不是新实验，也不是第三个 profiler 抽象。 |
| R311 | Paper robustness audit | 读取 tracked/clean R302/R305/R308/R309/R310 artifacts；输出 robustness-audit JSON、Markdown、CSV、TeX 和 HTML；operation-stack 比 flat selective 为 6/6，positive group 为 6/6，high-lift 为 5/6，selected recall 高于 fixed-session 为 5/6，但 selected work 低于 fixed-session 只有 2/6。 | 把 C4 的强证据和反例压成 reviewer-stress matrix：可以 claim inspectability tradeoff，不能 claim human utility、automatic detection 或 universal fixed-session dominance。 |
| R312 | Paper submission audit | 读取 tracked/clean R310/R311 artifacts、当前 R320 profiler-accuracy report 和当前中文 `main.tex`；输出 submission-audit JSON、Markdown、CSV、TeX 和 HTML；number alignment、two-abstraction boundary、must-not-claim guardrails 和 paper structure 均 pass，overall 为 `scoped_claim_ready`，C4 为 `hidden_label_profiler_accuracy_ready`。 | 把当前中文稿的 claim 安全性压成提交前 audit，并把 R320 作为主 profiler-accuracy gate 纳入检查；受控 analyst study 只作为 productivity/time-to-answer 的 human utility 扩展。 |
| R313 | Operation-view frontier | 读取 tracked/clean R300/R302/R305/R311 artifacts；输出 view-frontier JSON、Markdown、CSV 和 HTML；6 tasks / 4 datasets / 34,539 operations / 3,699 positives；162 个非 oracle candidate points；operation-stack frontier coverage 为 6/6，best lift 为 4/6，30% work 内 best recall 为 4/6；flat 和 fixed-session 也都是 6/6 frontier counterpoints。 | 把 C4 从 pairwise baseline comparison 推进到 configurable analysis-surface 证据：operation stack 是稳定 nondominated 视图，但不是唯一最优视图。 |
| R314 | Related-work novelty audit | 读取当前 related-work ledger、中文 paper、claim ledger、evaluation ledger 和 tracked R313 frontier；输出 related-work-audit JSON、Markdown、CSV 和 HTML；检查 classic flamegraph/pprof、pprof tag pseudo frames、Perfetto SQL/derived trace analysis、OpenTelemetry GenAI、OpenInference、LangSmith、Langfuse、Phoenix、AgentOps、公开标注轨迹、fixed-session/span-tree proxy baseline、R313 数字和 must-not-claim guardrails。 | 把 novelty 和 baseline grounding 变成可失败的 paper audit：已有系统已经有 trace/run/span/tree 和 agent artifact tracing，pprof 已有 sample tags/tag frames，Perfetto 已有 SQL trace analysis；本文只能把新意写成 agent-operation record model、recursive multi-field operation-stack projection 和 public labeled trajectory localization benchmark。 |
| R315 | Analyst-study protocol | 读取 tracked/clean R305 visible packets、R305 hidden answer key、R305/R308/R313 summaries；输出 study-protocol JSON、visible-study-packets JSON、hidden-scoring-key JSON、assignment CSV、Markdown 和 HTML；6 tasks、3 views、24 participants、144 trials；task-view cells balanced；visible-packet leakage check pass。 | 把 user-utility gate 从“未来需要 human/agent analyst study”推进到可直接执行的协议，但它不是 human study result，不能提升到 productivity、accuracy 或 time-to-answer claim。 |
| R316 | Analyst-study readout sensitivity | 读取 tracked/clean R315 study protocol、visible packets、hidden scoring key 和 assignment；输出 readout-report JSON、trial-scores CSV、Markdown 和 HTML；fixed visible-order top-3 scripted policy 下，operation-stack positive-hit/high-lift hit 为 1.0/0.8333，fixed-session 为 0.8333/0.6667，flat 为 1.0/0.0；operation-stack vs fixed-session 的 task-paired median recall/work delta 为 0.1333/0.0207。 | 证明 R315 protocol 能在真实 assignment 上读出已有 inspectability tradeoff，因此值得执行真实 analyst study；但它仍不是 human/agent analyst result，不能支持 accuracy、time-to-answer 或 productivity claim。 |
| R317 | Paper real-problem narrative | 读取 tracked/clean R309 problem cards、R313 frontier 和 R316 readout；输出 paper-narrative JSON、Markdown、CSV 和 HTML；6 task narratives across 4 datasets / 34,539 operations / 3,699 positives；operation-stack frontier coverage 为 6/6，high-lift coverage 为 5/6，higher selected recall vs fixed-session 为 5/6，lower selected work vs fixed-session 为 2/6。 | 把 safety、quality、looping、side-effect 和 human-boundary 的强结论与反例压成 reviewer-facing narrative；它不是新实证、人类实验、agent 实验、detector 或第三个 profiler 抽象。 |
| R318 | Reviewer acceptance closure | 读取当前中文 paper、claim setup、evaluation ledger、R312/R314/R317 artifacts；记录 4 个独立 subagent reviewers 的 final ACCEPT，其中 1 个 NEEDS_CHANGES round 已修复并复审 ACCEPT；检查 claim-centered result table、artifact-log phrase removal、paper-ready prose guidance、R312/R314/R317 guardrails。 | 关闭“subagent review until accept” gate，并证明本轮 blocker 是 paper presentation 而不是 claim evidence；它不是新实证、不是 human/agent analyst-task result，也不支持 productivity、accuracy 或 time-to-answer claim。 |
| R319 | Implementation/docs consistency audit | 读取当前 Rust CLI/profile/standard-trace 源码、canonical docs 和中文 paper；检查 `--profile-spec`、CLI override contract、standard trace import/export、standard-trace CLI test、implementation doc 状态、two-abstraction wording、third-abstraction guardrail 和 remaining-gate wording。 | 关闭“实现文档还像旧方案混用”的风险：profile spec 和 standard trace exchange 已经是当前 Rust operation/operation-stack 路径上的 wrapper/container，而剩余缺口是真实 analyst study、calibrated boundary backend 和 real producer trace import；它不是数据集同步、新实验或 human/agent study。 |
| R320 | Profiler accuracy/actionability benchmark | 读取 tracked/clean R288-R291/R300 operation JSONL，不同步或创建数据集；比较 flat、fixed-session、dataset-native、raw-action、operation-stack、label-drilldown，以及 width、visible-risk、query-aware、oracle-upper rankers；输出 profile-accuracy JSON、Markdown、HTML、policy scores、task accuracy 和 optimization insights。 | 把主 claim 从 analyst utility 改成 profiler fidelity：6 tasks / 4 datasets / 34,539 ops / 3,699 positives / 144 policy scores；operation-stack query-aware top-5 work 0.0937 vs flat 1.0；相对 fixed-session top-5 recall 高 5/6，median groups 157.5 vs 285.0；query-aware AP 高于 width-only 6/6；同时保留 dataset-native、raw-action、fixed-session 反例和 oracle upper-bound headroom。 |
| R321 | Query-time operation predicate probe | 读取 tracked R300 operation JSONL；写入带 `where_rules` 的 profile specs；运行 Rust `agentpprof --profile-spec`；输出 where-filter JSON、Markdown、CSV、HTML、folded stacks 和 agentpprof result JSON。 | 关闭实现层面的 predicate 缺口：`--where` 在 mapping/tagging 之后、stack folding 之前执行，profile spec 可以同时记录 operation source、mapping、predicate、stack 和 output；这支持 C1/C2 的 configurable query claim，不是新的 accuracy benchmark 或新数据集。 |
| R322 | Rust visible rank-rule probe | 读取 tracked R300 operation JSONL；写入带 `rank_rules` 的 profile specs；运行 Rust `agentpprof --profile-spec`；输出 Rust JSON ranked groups、summary CSV、Markdown 和 HTML；hidden labels 不传给 Rust，只用于 offline scoring。 | 关闭实现层面的 rank-policy surface 缺口：JSON profile 可以输出完整 ranked operation-stack groups；visible rules 只读 `action/environment/phase/repeat_signal/status`，AP 高于 width 为 4/6、top-5 recall 高于 width 为 2/6、top-5 lift 高于 width 为 3/6；它是 R320 的实现校准，不是 detector 或新数据集。 |
| R323 | Rust rank-mode probe | 读取 tracked R300 operation JSONL；写入 paired `rank_mode=width-boost` / `rank_mode=rule-score` profile specs；运行 Rust `agentpprof --profile-spec`；hidden labels 不传给 Rust，只用于 offline scoring。 | 证明 ranking policy 本身是 mechanism knob：rule-score 相比 width-boost AP 提升 4/6、top-5 lift 提升 4/6、first-positive work 改善 3/6，并把 SATraj first-positive work 从 0.6376 降到 0.0842；side-effect 和 OSWorld-Human 保留为反例；它不是新数据集、detector 或 human-utility 证据。 |
| R324 | Rust operation rank-feature probe | 读取 tracked R300 operation JSONL；为 Rust 写入删除 oracle fields 的 visible-operation profiler input；写入 semantic/coarse stack 两组 `rank_op_rules` profile specs；运行 Rust `agentpprof --profile-spec`；hidden labels 不传给 Rust，只用于 offline scoring。 | 把 R320 的 group-feature query-aware ranking 机制推进到 Rust：`rank_op_rules` 匹配 mapping/filtering 后的单个 visible `field=value` operation token，并在 folded stack group 内聚合 matched weight。semantic stack AP 提升 5/6、top-5 lift 提升 4/6、first-positive work 改善 5/6；coarse stack AP 提升 4/6、first-positive work 改善 5/6；它不是新数据集、detector 或 human-utility 证据。 |
| R325 | Rust operation rank-feature ablation | 复用 R324 的 scrubbed visible-operation profiler input；为 width、all-feature 和 leave-one-feature-out policies 写入 semantic/coarse stack profile specs；运行 Rust `agentpprof --profile-spec`；hidden labels 不传给 Rust，只用于 offline scoring。 | 把 R324 转成 actionability/mechanism-isolation 证据：7 个 critical feature instances 说明 `repeat_signal`、`write-action`、`status=success` 等字段确实驱动 localization；3 个 misleading feature instances 暴露 SATraj loop-like 和 OSWorld-Human input-phase 排序风险；coarse stack AP 只在 2/6 tasks 更好但 6/6 减少 groups，所以 stack depth 是成本/准确率旋钮，不是统一固定层级。 |
| R326 | Rust operation rank-feature robustness | 复用 R324 的 scrubbed visible-operation profiler input 和 R325 findings；为 width、task-weighted、task-equal、global-equal 和 R325-guided repaired policies 写入 semantic/coarse stack profile specs；运行 Rust `agentpprof --profile-spec`；hidden labels 不传给 Rust，只用于 offline scoring。 | 检查 R324/R325 是否过度依赖手调权重：global equal visible feature bank 在 semantic/coarse stack 上 AP 相比 width 分别赢 4/6 和 5/6 tasks；task-equal 在 8/12 variants 上与 weighted policy 的 AP 差距不超过 0.02；R325-guided repair 在 2/3 misleading-feature cases 上改善 AP、在 2/3 cases 上改善 first-positive work，其中 1/3 同时改善两者。Repair 是 post-hoc actionability check，不是 label-free deployment policy。 |
| R327 | Profile-spec cost/reproducibility probe | 复用 R300 的 4 个 view specs、R324 的 12 个 rank-feature specs 和 R326 的 60 个 robustness specs；每个 spec 重复运行两次 Rust `agentpprof --profile-spec`，共 152 次 profiler invocations；只读取 tracked/clean spec 和 operation JSONL。 | 76/76 specs 的 semantic profile hash、samples 和 unique stacks 稳定；median runtime 1.581s，p95 2.719s，max 4.273s；raw-byte determinism 4/76 是 JSON `generated_at` 时间戳导致的预期差异。该结果支持 artifact reproducibility/离线成本，不支持 live overhead、人类效用或 trace-platform compatibility。 |
| R328 | Deterministic profile-output probe | 复用 R327 的同一 76 个 R300/R324/R326 profile specs 和 tracked operation JSONL；每个 spec 重复运行两次 Rust `agentpprof --deterministic-output --profile-spec`，共 152 次 profiler invocations；不下载、同步或创建数据集。 | `--deterministic-output` 固定 JSON `generated_at` 和 pprof profile time 后，semantic determinism 和 raw-byte determinism 都达到 76/76；median runtime 1.578s，p95 2.731s，max 4.298s；median output size 37,546 bytes，max unique stacks 2,012。该结果关闭 raw artifact byte-stability 缺口，但不支持 live overhead、人类效用、性能提升或 trace-platform compatibility。 |
| R329 | Target-held-out rank-policy transfer | 复用 R324 scrubbed visible-operation profiler input 和 R300/R324/R326 的 6 个 oracle-backed tasks；候选 policy 为 global equal visible bank 加 6 个 source-task equal-weight policies；写入 deterministic profile specs 并运行 Rust `agentpprof --profile-spec`，共 96 个 policy/task/stack evaluations；leave-task 和 leave-dataset 选择只用非目标任务评分，目标 hidden labels 只用于最终 scoring。 | 两种 protocol 在 semantic/coarse stack 上 AP 都是 4/6 胜过 width，semantic first-positive work 都是 6/6 改善；7/12 variants 不低于 target-equal policy 超过 0.02 AP；mean AP gap-to-oracle candidate 为 0.0323/0.0319。该结果支持 target-label-held-out mechanism isolation 和 rank-policy transfer evidence；不能 claim label-free deployment ranker、human utility、universal detector 或新数据集。 |
| R330 | R320 paired-bootstrap uncertainty audit | 读取 tracked/clean R320 `profile-accuracy-report.json` 和 `policy-scores.csv`；不重新 profiling、不下载或创建数据；以 6 个 task families 为 bootstrap 单位，10,000 reps、seed 330。 | 10 个 metric checks 方向稳定，10 个是 mixed/counterpoint。稳定项包括：vs flat 的 AP mean delta 0.1219 CI [0.0406,0.2175]、top-5 work -0.8168 CI [-0.9653,-0.6568]、30% budget recall 0.4510 CI [0.3450,0.6143]、WTFP -0.9303 CI [-0.9855,-0.8650]；vs fixed-session 的 top-5 recall 0.1801 CI [0.0542,0.3127]、top-5 F1 0.1702 CI [0.0549,0.2870]、groups -178.0 CI [-340.0,-39.0]；vs width-only operation-stack 的 AP 0.0932 CI [0.0110,0.2184]、top-5 work -0.3101 CI [-0.4209,-0.1997]。该结果支持 task-family 层面的方向稳健性，不支持 per-operation independence、human utility 或 universal dominance。 |
| R331 | R320 label-permutation negative-control audit | 读取 tracked/clean R320 report/CSV 和同一 4 个 source operation JSONL；不重新 profiling、不下载或创建数据；对 6 个 task families 的 5 个 visible policies 固定 group/ranking order，并把同一任务的 hidden positives 随机重分配到同样大小的 groups；2,000 reps、seed 331。 | Operation-stack query-aware AP 在 6/6 tasks 超过 95% permutation null，median observed-minus-null AP 为 0.0759；30% budget recall 在 5/6 tasks 超过 null，median delta 为 0.0904。Top-5 precision 只有 3/6 tasks 超过 null，work-to-first-positive 为 0/6。Width-only operation-stack AP 为 5/6，fixed-session 和 raw-action AP 都为 6/6，说明 baselines 有真实 signal，不是 strawman。该结果支持 prevalence/group-size negative control 和 mechanism isolation，不支持所有 hot-group 指标、label-free ranker、human utility 或 single-view dominance。 |

## Paper-Ready Wording

可以写：

> We show that a two-object model, operations plus operation stacks, is
> sufficient to express profiling views over 15 public labeled agent
> trajectory sources. The same Rust profiler folds operations at dataset,
> task, phase, tool, action, human-group, safety, looping, and step-quality
> depths by changing mapping and stack specifications, not by adding
> prompt-, GUI-, or safety-specific profiler objects.
> Profile specs make these experiments replayable without changing the
> two-object model: they package operation files, mappings, predicates, view,
> stack, and output choices, while CLI flags can still override the stack query.
> Agent-session traces provide a replayable import/export format before the
> operation layer; converting them to operation JSONL preserves the same stack
> projection path. Chrome Trace Event JSON can be used as a standard exchange
> container, but imported traces still become operation JSONL before profiling.
> Supervised boundary backends remain outside the core profiler abstraction:
> they derive fields such as `learned_group_pattern`; the profiler still folds
> operations using a user-selected operation stack.
> On six oracle-backed analysis tasks, operation-stack views provide a
> hidden-label profiling accuracy surface: top groups localize task-relevant
> failures, safety problems, quality errors, and human-boundary positives with
> less inspection work than flat summaries and less fragmentation than
> fixed-session drilldown, which is the current span-tree proxy rather than
> a real OpenTelemetry/OpenInference/Phoenix span-tree import, while preserving
> flat, dataset-native, raw-action, fixed-session, and oracle-upper-bound
> policies as counterpoints.

中文论文中应写成：

> 本文的贡献不是又画一种 agent flamegraph，而是把 agent 轨迹 profiling 的边界选择
> 从固定 prompt/session/span 层级中释放出来。所有对象都先成为 operations，mapping
> 和 tagging 只派生字段，operation stack 再根据用户问题递归折叠。
> Profile spec 只是把 operation 文件、mapping、predicate、view、stack 和输出路径记录成可复现
> 配置；它不增加第三个抽象，命令行仍可覆盖 stack 以回答不同问题。
> R327 已经把这条路径变成可重复的 artifact gate：76 个已提交 profile specs 在重复运行中保持
> semantic profile hash、samples 和 unique stacks 稳定，median runtime 为 1.581s，但这只是离线成本，
> 不是 live capture overhead。
> R328 进一步把 deterministic artifact mode 接入同一路径：`--deterministic-output` 固定输出时间戳后，
> 同一 76 个 specs 的 semantic 与 raw-byte determinism 均为 76/76；这支持 byte-stable artifact claim，
> 不支持性能提升或生产 overhead claim。
> R329 再把 rank-policy selection 从目标任务 oracle 中分离出来：leave-task 和 leave-dataset
> protocol 只用非目标任务评分选择 policy，目标 hidden labels 只用于最终 scoring。
> 结果是 semantic/coarse AP 均为 4/6 胜过 width，semantic first-positive work 为 6/6 改善，
> 平均 gap-to-oracle candidate 约 0.032 AP。它支持 operation-level rank features 和
> source-task policies 的可迁移机制证据，但 selection 仍使用其他标注任务，所以不能写成
> label-free deployment ranker。
> R330 再把 R320 的主比较做成 task-paired uncertainty audit：相对 flat，operation-stack
> query-aware 的 AP、top-5 work、30% budget recall 和 work-to-first-positive 方向稳定；
> 相对 fixed-session，top-5 recall、top-5 F1 和 group count 方向稳定；相对 width-only
> operation-stack，AP、top-5 work 和 work-to-first-positive 方向稳定。它同时保留 flat
> top-5 recall、fixed-session work/WTFP/AP 和 raw-action mapping comparison 反例，所以只能
> 支持 task-family 层面的稳健 tradeoff，不支持单一 hierarchy 支配所有指标。
> R331 再固定 visible ranking 顺序做 label-permutation negative control：operation-stack
> query-aware AP 在 6/6 tasks 超过 95% null，30% budget recall 在 5/6 tasks 超过 null；
> 但 top-5 precision 只有 3/6、work-to-first-positive 为 0/6。这个结果说明主 AP/预算召回
> 信号不能被 prevalence/group-size 单独解释，同时保留 fixed-session 和 raw-action 作为有真实
> signal 的 counterpoints。
> Agent-session trace 是 session 交换格式，不是 profiler 抽象；导入后仍然要转成
> operations，再由 operation stack 折叠。Chrome/Perfetto-style trace 也是同样的
> exchange container；它不绕过 operation JSONL，也不新增第三个抽象。
> Boundary backend 也不是第三个抽象；它只派生 `learned_group_pattern` 等字段，
> 之后仍由 operation stack 做递归折叠。当前 boundary-family calibration 支持
> “统一 field-derivation extension point” 这个机制 claim，但不支持通用 intent
> detector。AgentRewardBench looping 被简单 repetition field 完全解释，因此更强
> backend claim 需要先胜过 simple baseline。
> 真实问题结果应按任务讲，而不是按 artifact 编号讲。在 4 个数据集、6 个
> oracle-backed tasks、34,539 个 operations 和 3,699 个 positives 上，
> operation-stack 比 flat 更 selective 的任务为 6/6，含 high-lift evidence 的任务为
> 5/6，selected recall 高于 fixed-session 的任务为 5/6。反例同样重要：selected work
> 低于 fixed-session 只有 2/6，flat 和 fixed-session 在 Pareto frontier 上也都是
> 6/6 counterpoints。
> R320 应作为主 profiling-paper 结果写入论文：把 hot stack/top group 当作 ranked
> localization output，用 hidden labels 计算 precision@k、recall@budget、F1、AP、
> nDCG 和 work-to-first-positive。结果是 operation-stack query-aware top-5 只检查
> 0.0937 work，flat 需要 1.0；operation-stack 相比 fixed-session 在 5/6 tasks 上提高
> top-5 recall，并把 median groups 从 285.0 降到 157.5。Query-aware ranking 相比
> width-only operation-stack ranking 在 6/6 tasks 上提高 AP，但 top-5 F1 和 work 仍有
> prevalence、side-effect、boundary-depth 反例。
> 因此论文应该写成 configurable inspectability surface：SATraj safety 是最强
> selective win，AgentNet quality 是 high-lift but low-recall，AgentRewardBench
> looping 更像 prevalence aggregation，side-effect 和 OSWorld-Human boundary 对
> ranker/depth 敏感。当前 protocol 已经把 visible packets、hidden answer key、
> balanced assignment 和 scripted readout 准备好，但在真实 analysts 完成前仍不能
> 写 human/agent accuracy、time-to-answer 或 productivity。
> Related work 应把 classic flamegraph/pprof、pprof tag pseudo frames、Perfetto
> SQL/derived trace analysis、OpenTelemetry GenAI、OpenInference、LangSmith、
> Langfuse、Phoenix、AgentOps 和公开标注轨迹都当成 same-problem threat。
> 本文的新意不是替代 trace systems 的功能，而是把 trace/session/span 写成 exchange
> container 或 baseline，并把 profiling 的核心边界收敛为 operation fields 与
> operation-stack queries。更准确地说，新意不是 query-time aggregation 本身，
> 而是 agent-operation record model、recursive multi-field operation-stack
> projection 和 hidden-label cross-dataset localization benchmark 的组合；同一批
> operations 因 stack shape 不同而形成不同的可定位、可排序、可检查 aggregation units。

不能写：

> agentpprof 已经自动发现所有真实意图边界。

也不能写：

> 这些可视化已经证明能提升开发者效率。

## Next Gates

1. Boundary detector gate：在 R299 的 suitability/calibration 结果上继续加入更强
   sequence 或 model-backed backend，并只在胜过简单 derived-field baseline 后提升 claim。
2. Accuracy expansion gate：把 R320 的 hidden-label profiler accuracy benchmark 扩展到更多 oracle-rich tool/API、mobile GUI 和 full AgentNet shards，同时保持不创建测试集、不同步图片归档。
3. User-utility optional gate：如果要 claim analyst productivity，再执行 R315/R316/R317 固化的 controlled human/agent analyst study、hidden-key readout 和 task-level claim matrix。
4. Scale gate：对 AgentNet full Ubuntu/Windows/macOS 或 OSWorld-Verified 做更大流式
   sampling，但仍不保存完整源数据或图片归档。
5. Paper hygiene gate：所有数字必须能追到 `docs/visexp/out/*/*.json`，所有外部数据只
   以 redacted operations 和 tracked reports 进入仓库。
