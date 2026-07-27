# RQ2 cross-case result review

**Reviewed:** 2026-07-26  
**Verdict:** **VALID, WITH A NARROWER PAPER CLAIM**

本次复审从 final-HEAD 的三张权威 RQ2 raw CSV 独立重建
worktree lane、validation event、complete cycle、删失和主要汇总，没有把
`result.md` 的预设结论当作真值。运行和数字有效；它支持旧 plan
预声明的“cadence 与 mutation accumulation 不均匀”这一窄假设，但不支持
一个六案例共同的 success/failure-conditioned response。论文可以使用精确
cadence/长尾数字和异质性结果，但应把统计意义不明的
“strongly zero-inflated”改成描述性的“high zero mass / many zero-mutation
intervals”。

## 输入、完成度与可复算性

- 三个权威输入的 SHA-256 与脚本常量及 `input-manifest.csv` 完全一致：
  `rq2-trajectory.csv`
  `ec8065c8e2ce1f1d3e78d62d3522f5dae4293999238171bb039887371e482a61`，
  `rq2-cycles.csv`
  `dfd7504aab265035fc0872c05de0f03783490ced59e9869d1aa26d86079c13fe`，
  `rq2-coverage.csv`
  `1f8f0275dabe62037b5e270fa2513a0d0d46f146a71ae5af72517bfd2c4525ae`。
- 输入包含 180,180 个 worktree-lane rows、10 条 lane、176,288 个
  home-worktree-attributed actions。所有 lane 的 `action_rank` 连续，
  `(project, worktree, event_id)` 唯一，`event_index` 严格递增，
  `cumulative_mutation_rows` 逐行对账。
- 7,060 个 recognized validation events 的 outcome 为
  `5,948 ok / 656 fail / 456 observed`。逐项目 success 为
  `3288/2576/22/52/1/9`，与 coverage CSV 一致，因此 recognized-success
  coverage 确为 6/6；能形成 complete inter-success interval 的项目为
  5/6，含 fail 的项目为 4/6。
- 当前五张派生结果 CSV 均可由当前脚本在内存中逐行重建，字段和值完全
  相同。`output-manifest.csv` 中记录的六个输入/派生 CSV hash 也与文件
  一致。它没有固定脚本或 `result.md` 的 hash，这是非阻塞的 provenance
  缺口，意味着论文文字仍需像本次一样单独核数。

## Worktree 投影与 cycle 语义

- 对 final RQ1 mutation ledger 做独立连接后，13,906 条 mutation rows
  全部恰好出现在其 `FileAction.worktree_id` 指定的 trajectory lane；
  event 分组数、row 数和 artifact 集均无缺失、重复或额外项。其中
  **4,132** rows 是非 home/cross-worktree 投影，证明旧审查发现的漏投影
  问题在当前输入中已经修复；其余 9,774 rows 位于 home lane。
- 30 个 source events 没有 home worktree、只有显式 action-target
  worktree，因此进入 lane event-distance 但不进入 home-action 分母。
  回查 final-HEAD source events 后，这 30 个均不是 `effect=test`，所以
  不会改变本次 success/fail/observed coverage。论文中的 rate 分母仍应写
  `home-worktree-attributed actions`，不能泛称所有 lane events。
- 从 trajectory 独立重建得到 5,958 个 interval rows：
  **5,939 complete、9 left-censored、9 right-censored、1
  no-success-observed**，与 `rq2-cycles.csv` 每个边界和每个字段完全一致。
  Complete 数按项目为 `3285/2574/21/51/0/8`。所有 duration 非负；
  ending success 包含在 action length 中，但其同事件 mutation 不进入
  前一 complete interval。
- 同一 Tool event 的 mutation/validation 无可识别的事件内顺序。当前数据
  有 **61 个 success events、62 条 mutation rows** 属于这种 co-observation：
  agentsight `7/7`、ActPlane `47/48`、academic-writing-skills `7/7`
  （events/rows）。脚本将它们从相邻 interval accumulation 中排除，并通过
  `co_observed_mutation_rows`/`ending_co_observed_mutation_rows` 单列；把
  complete/censored rows 和这些 co-observed rows 相加后，各项目 mutation
  总数逐一恢复为 `6588/5849/283/739/196/251`。

## Cadence、删失、分位数与 response

项目和 lane 的 complete-cycle 数字均独立复算通过。Hyndman--Fan type 7
下，五个 eligible 项目的 zero-mutation 比例、median/p90/max 分别为：

| Project | Complete | Zero | Median / p90 / max |
|---|---:|---:|---:|
| agentsight | 3,285 | 74.7% | 0 / 4 / 291 |
| ActPlane | 2,574 | 84.4% | 0 / 1 / 817 |
| bpf-developer-tutorial | 21 | 47.6% | 2 / 43 / 69 |
| eunomia.dev | 51 | 56.9% | 0 / 21 / 361 |
| academic-writing-skills | 8 | 62.5% | 0 / 49 / 140 |

七条 eligible lane 的 zero fraction 确为 29.3%--86.1%，max 确为
1--817。它们足以支持“零值常见且有长尾 burst”的描述，但
`zero-inflated` 是相对于某个 count model 的术语；当前分析没有拟合或检验
这样的参照分布，故不能声称“strongly zero-inflated”。此外 BPF、eunomia
和 Writing skills 分别只有 21、51、8 个 complete intervals，项目也不是
总体的随机样本。

Event-order 比较正确地只使用下一 mutation 与下一 validation 都观察到且
不 co-observed 的事件。Success 的 mutation-first 比例和分母为
agentsight `814/3285=24.8%`、ActPlane `374/2571=14.5%`、BPF
`11/21=52.4%`、eunomia `17/51=33.3%`、Writing skills
`3/3=100%`；AgentSkill paper 的唯一 success 不可比。Fail 对应为
agentsight `16/373=4.3%`、ActPlane `20/277=7.2%`、eunomia
`0/3=0%`、AgentSkill paper `3/3=100%`。其余两项目无 fail。

Success ordering 中另有 8 个 future co-observation（ActPlane 3、Writing
skills 5）和 9 个 lane-terminal right-censored events；它们没有被塞进
mutation-first 分母。大项目的删失很少，但稀疏项目的 `3/3` 和 `3/3`
比例仍只能是案例描述。前后相邻 validation interval 的 paired
`post-pre` 计数也与 CSV 一致：两个大项目和 eunomia 没有共同增减方向；
AgentSkill paper 的 `2/2` fail 上升来自总共 3 次 fail，不能形成跨案例
效应。所有这些 event 都共享项目、session 和相邻 interval，分析未提供
可辩护的独立性或置信区间，因此不能把数千 event 当成数千独立复现。

## Vendor、项目类型与 paper-facing claim

Vendor action/attempt 原始比率均对账。`systems/research` 的两个案例同时是
Codex-dominant、规模最大且 cadence 最高；其他项目类型各只有一个案例。
同为 Codex-dominant 的 eunomia cadence 明显较低且 unknown outcome 占
63.3%，两个 pure-Claude 案例也呈相反的稀疏模式，BPF 的项目内 vendor
rate 方向又与两个 systems 项目相反。因此 `result.md` 把这些只解释为
同现和 confounding 是正确的；不能写 vendor effect、project-type effect
或 population replication。

`result.md` 中的 6/6、5/6、4/6 分母、attempt rate、S/F/O、gap、
complete-cycle、pre/post、event-order 以及 vendor 数字均通过复算。需要
收窄的只有解释层：

1. 将 paper 当前的 “strongly zero-inflated” 改为精确的 zero fraction
   和 long-tail max，不给未检验的分布族命名。
2. 在 cadence 结论之外加入主要负结果：六案例不存在同方向的
   outcome-conditioned response；三个较高事件量的 success+fail 案例中
   fail 后通常先再次 validation，而 3-fail 的 AgentSkill paper 相反。
3. 同时报告 `success coverage 6/6`、`complete-cycle coverage 5/6`、
   `fail coverage 4/6`，并注明 61 个 same-event success/62 mutation rows
   与 terminal censor 的处理。
4. 当前 paper RQ2 段落中的 validation-before-supersession fractions 是
   RQ1 的 artifact-level 指标，不由本 cross-case run 验证；不要把它们
   当作本次 success/failure response 的证据。

## 分离判断

```text
run status: valid
tested hypothesis: supported for the preregistered uneven-cadence/mutation-accumulation expectation; the stronger common six-case outcome-conditioned response is contradicted
research value: supporting
paper impact: additional RQ2 evidence plus a workload/outcome-coverage boundary; no direct thesis challenge
next paper decision: admit the exact cadence, censoring, and heterogeneous-response numbers; replace “strongly zero-inflated” with descriptive zero-mass/long-tail wording, add the 6/6, 5/6, and 4/6 denominators, and make no vendor or project-type effect claim
```
