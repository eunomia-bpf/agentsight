# R385 RQ Section Contract Focus Gate

Status: **pass**

Each RQ/E section opens as a claim-facing experiment contract rather than an R-numbered provenance paragraph.

## Section Openings

| RQ | English first line | Chinese first line | Claim tests |
|---|---|---|---:|
| RQ1/E1 | Experiment contract: claim, the operation/operation stack model covers | 实验契约：RQ1/E1 的 claim 是两抽象模型能覆盖异构 agent traces 且不把 prompt/session/tool 边界写死；oracle 是 public dataset labels、native trajectory fields、OSWorld-Human human boundary 和 AgentNet quality labels；baseline 包括 dataset-native stacks、no-map folding、fixed-session stacks、profile-spec replay 和 trace round trip；metric 包括 operation coverage、unique-stack range、mapping compression、boundary F1/V-measure 和 replay equality；counterpoint 是这只能支持 configurable operation stack folding，不能支持完整生态兼容或自动恢复所有 latent intent。Prompt、tool、process 和 syscall 可以是 operation records 或 fields；session/span 是字段、容器或 baseline shape，not new profiler objects。 | True |
| RQ2/E2 | Experiment contract: claim, operation-stack profiling localizes and ranks real | 实验契约：RQ2/E2 的 claim 是 operation-stack profiling 能在真实 labeled traces 上 faithful localization 和 ranking；oracle 是 6 个 oracle-backed tasks 中 34,539 个 operations 和 3,699 个 hidden positives；baseline 包括 flat summary、fixed-session drilldown、dataset-native hierarchy、raw-action stack、operation-stack width、operation-stack query-aware、label-drilldown 和 oracle upper bound；metric 包括 precision@k、recall、F1、AUPRC-style AP、nDCG、recall/F1@work budget、work-to-first-positive 和 group count；counterpoint 是 flat 和 dataset-native 可以赢 broad-recall 或 nDCG 目标，所以主 claim 是 Pareto tradeoff，不是 metric dominance。 | True |
| RQ3/E3 | Experiment contract: claim, the profiler exposes actionable knobs in stack | 实验契约：RQ3/E3 的 claim 是 profiler 通过 stack fields、mapping/tagging rules、ranking policies、profile specs 和 boundary-derived operation fields 暴露 actionable optimization knobs；oracle 是 hidden labels only after profiling，R358 还用 held-out OSWorld-Human boundary positives 评分；baseline 包括 default semantic-width specs、patched specs、visible feature rankers、transfer policies、learned-boundary stacks、fixed-session 和 semantic-width stacks；metric 包括 accepted patches、AP delta、top-5 lift delta、first-positive-work delta、group reduction 和 top-5 work counterpoint；counterpoint 是 OSWorld-Human 需要 boundary-derived fields，因此这是 actionable mechanism evidence，not automatic boundary discovery、not automatic patch selection。 | True |
| RQ4/E4 | Experiment contract: claim, the offline profiler path is replayable over tracked | 实验契约：RQ4/E4 的 claim 是 offline profiler path 可以在 tracked inputs 上低成本 replay；oracle 是 tracked profile specs、tracked operation inputs、repeated profile outputs、runtime logs 和 source-status rows；baseline 包括 default output versus deterministic-output replay、semantic profile hashes versus raw-byte profile hashes；metric 包括 deterministic spec pass rate、profiler invocations、median/p95 runtime、sample equality、stack equality 和 raw-byte output equality；counterpoint 是 not live eBPF overhead、not human utility、not complete ecosystem compatibility、not universal selector。Claim-integrity、rubric 和 reviewer-style checks 是 artifact hygiene，不是 empirical evidence。 | True |

## Checks

| Check | Passed | Detail |
|---|---:|---|
| english_uses_experiment_contracts | True | English RQ/E sections use four reviewer-facing experiment contracts. |
| chinese_uses_experiment_contracts | True | Chinese RQ/E sections use four experiment contracts and no R361-led section openings. |
| section_openings_are_contracts | True | The first content line after every RQ/E subsection is the experiment contract. |
| claim_tests_present | True | Every RQ/E subsection still states a claim test. |
| ledger_records_r385_as_focus_gate_when_present | True | If R385 is present in the ledger, it is a paper-focus gate, not a profiler experiment. |
| no_data_or_profiler_rerun | True | Runtime commands=['<dynamic>', 'git ls-files --error-unmatch -- <dynamic>', 'git diff --quiet -- <dynamic>', 'git diff --cached --quiet -- <dynamic>']; forbidden hits=[] |

## Sources

| Source | Status | Path |
|---|---:|---|
| generator script | tracked_dirty_allowed | `script/paper_rq_contract_focus_r385.py` |
| English paper | tracked_clean | `docs/agentpprof-paper/main.tex` |
| Chinese paper | tracked_dirty_allowed | `docs/visexp/paper/main.tex` |
| evaluation ledger | tracked_dirty_allowed | `docs/evaluation.md` |
| English paper submodule gitlink | tracked_dirty_allowed | `docs/agentpprof-paper` |
