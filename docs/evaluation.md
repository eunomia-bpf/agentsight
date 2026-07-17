# AgentProf Evaluation Frontier

## Purpose

This file records the current experiment frontier: paper-level RQs, admitted
results, raw artifact locations, and the next empirical decision. It is not a
gate registry, claim ledger, checker transcript, freeze protocol, or complete
history. The 360 KB pre-recovery version is preserved at
`docs/tmp/cycle-0001-20260711T164850-0700/03-review-gate/idea-regression-recovery-20260712T021723-0700/archive-pre-recovery/evaluation.md`.

The current RQs were restored after the three-round user-directed review. An
experiment receives one RQ verbatim and tests one hypothesis within it. A
failed mechanism may change the next mechanism, signal, workload, or protocol,
but it does not change the RQ or weaken the fixed positive hypothesis. Only a
later explicit user instruction may change the four author-fixed RQs.

## RQ Frontier

| RQ | Fixed question | Positive hypothesis | Next evidence need |
|---|---|---|---|
| RQ1 | Does Semantic Profiling Improve Resource Attribution? | Semantic operation stacks reunite recurring responsibility fragmented across executions and improve attribution of independently recorded additive resources while preserving source lineage and mass. | **Evidence-backed positive answer.** R114 establishes scoped source-lineage correctness under concurrent controls and lossless profile folding. Step 0035 adds a non-circular same-input comparison over the complete pre-existing 405-trajectory CodeTraceBench source-valid target: recurrence improves standard ordinary B-cubed F1 against human stages from 0.541 raw-action-key to 0.649, a +0.108 task-cluster effect with 95% interval [+0.087,+0.129]. Resource-weighted gains remain +0.076 to +0.085 under three shared-response allocations. Phase-only is statistically indistinguishable at 0.654, so the result supports semantic stage-aligned attribution over raw identity, not recurrence dominance over every semantic view. R170/R224/R251 remain descriptive declared-category and multi-weight evidence rather than an independent oracle. Do not reopen another RQ1 benchmark, metric, or constructor variant before WRITE/REVIEW. |
| RQ2 | Does Profiler Output Correspond to Real Problems? | A target-blind semantic profile concentrates independently annotated failures, unsafe effects, redundant work, or task boundaries and reduces analyst inspection without using target labels. | **Evidence-backed positive answer against matched raw-action organization, with an explicit atomic/local mechanism boundary.** Step 0036 rechecks all 1,756 trajectories and 27,346 operations using standard per-query AP/MAP as the primary metric and exact-budget Recall@20% only as secondary analysis: AgentProf-minus-raw intervals are positive for both measurements on AgentProcessBench, HINTBench, and TraceElephant. Atomic nevertheless wins both AgentProcessBench measurements, while the HINT/Trace atomic comparisons are mixed; HINT grouping also propagates nonzero support to 76.54% of clean operations versus 0.742% atomic. Step 0037 then adaptively preserves every strict local-score ordering and uses semantic recurrence only to break exact local-score ties. On the same observed populations it improves MAP over atomic and semantic-only ranking on all three workloads and over a matched local+raw tie-breaker on HINTBench and TraceElephant; AgentProcessBench is indistinguishable from local+raw. This supports a simple local-first semantic mechanism, not a universal replacement or untouched confirmation. The fixed-reader comparison separately improves selected-positive recall on 5/6 tasks and precision on 4/6 versus session. Collectively the evidence supports problem ranking and group prioritization, not universally lower work, human productivity, or dominance over every atomic/session view. No further score tuning on these populations is admitted. |
| RQ3 | How Accurate Are the Tags? | A target-blind fixed tagger or mapping assigns accurate and stable task, phase, action, and boundary identities on unseen agents and task families without materially corrupting attribution. | **Positive partial answer; Step 0024 remains the label-free default, Step 0030 adds optional grouped-reference evidence, Step 0031 adds literal task-family accuracy, and Step 0032 adds literal action accuracy for one named backend.** Step 0006 supports supervised group-boundary identity on 287 session-held-out OSWorld-Human tasks. Step 0008 adds target-blind task-partition evidence on Mind2Web and 100 ScienceWorld sessions, with V-measure 0.5565 and 0.8151 at full coverage versus 0 for a constant control. Step 0024 reaches 0.6799 boundary F1 and 0.7862 B-cubed F1 on OSWorld, and raises CodeTraceBench boundary F1 from 0.2685 to 0.2871 and B-cubed F1 from 0.4750 to 0.6492 on all 405 reused targets. Step 0030 fits one scalar on disjoint grouped references and raises B-cubed F1 to 0.8011 on OSWorld and 0.6666 on CodeTraceBench. Step 0031's fixed Qwen3.6-27B path reaches 0.695 task-family macro-F1 on all 1,012 AgentBoard goals. Step 0032 uses the complete 2,737-label ASE population and reaches 0.498 action macro-F1 versus 0.061 majority, a +0.437 trajectory-bootstrap effect with 95% interval [+0.380, +0.494], and exact two-run stability. Literal phase identity, unknown label sets, and uniform cross-framework accuracy remain outside current evidence. |
| RQ4 | What Is the Profiling Cost? | Complete profile construction has practical predictable scaling, and cached field derivation makes repeated profile queries substantially cheaper than initial construction and repeated raw-trace review. | **Evidence-backed paper-level construction-cost answer.** Current `agentpprof 0.2.37` completes the 27,765-operation semantic union in 1.17 s median with 464.49 MiB maximum RSS, with a monotonic near-linear measured scale curve. R160 separately supports the shared cache mechanism on one predecessor fixed-input pair. The paper now states both results with the binary boundary explicit; do not reopen another cost/cache variant. |

## Admitted RQ1 Mechanism Evidence

The retained RQ1 numbers come from the R170 local full-history corpus and two
deterministic analyses over that generated evidence:

- **Input and collection.** R170 scanned all discovered readable Codex/Claude
  histories under the configured 10,000-session/file caps, used a local
  llama.cpp-compatible Qwen2.5-3B tagger with a seeded cache, and produced 325
  sessions and 183,714 system-effect observations. The exact collection command
  and environment are recorded in `docs/visexp/EXPERIMENT_TRACKER.md` under
  R170; the committed summary is
  `docs/visexp/out/full-history-r170.json`.
- **Grouping ablation.** R224 ran
  `python3 docs/visexp/r131_semantic_ablation.py --input
  .agentsight/agentflame/r170-full-current --local-out
  .agentsight/agentflame/ablations-r224-r170/summary.json --out-dir
  docs/visexp/out/semantic-ablation-r224-r170`. Raw committed results are
  `docs/visexp/out/semantic-ablation-r224-r170/semantic-ablation-r131.json`
  with provenance in `r224-rerun-metadata.json`. It compares no-semantic,
  session-only, prompt-only, and session-plus-prompt projections over identical
  R170 observations. Every projection conserves 183,714 units; mixed-bucket
  weight is 90.402%, 84.407%, 36.722%, and 0% respectively, with the final row a
  construction check rather than independent semantic evidence. Stack counts
  are 11,967, 15,027, 24,703, and 26,829.
- **Association beyond session.** R251 ran
  `python3 docs/visexp/r251_behavior_tag_alignment.py` over the R170 folded
  stacks and 1,000 session-preserving prompt-tag permutations. Raw results are
  `docs/visexp/out/behavior-tag-alignment-r251/behavior-tag-alignment-r251.json`
  and `session-shuffle-null-r251.csv`. Prompt tags retain 8.419% weighted
  behavior information beyond session versus a 1.903% null p95
  (`p=0.0010`, permutation resolution 1/1001).
- **Measure sensitivity.** R225 reports the duration-versus-effect ranking
  comparison used in the paper at
  `docs/visexp/out/prompt-span-duration-r225/prompt-span-duration-r225.json`:
  top-10 overlap 7/10 and Spearman 0.623. Prompt spans may contain idle/user
  wait time and are not true active-runtime measurements.

These are admitted mechanism/accounting results. R170 records a dirty
working-tree provenance boundary; prompt tags define the declared grouping
reference; R251 has no human adequacy labels. The evidence supports mass
conservation, declared-category separation, and weighted association beyond
session membership. By itself it does not establish independent source
lineage; Step 0007 supplies that separate edge below.

## Admitted RQ1 Source-Lineage And Profile Evidence

Step 0007 reran R114's unchanged fixed 20-task real-Codex suite with its
existing capture-time process/tool scope, exact effect-lineage checker, and
concurrent wrapper controls. All 20 target tasks completed and all 20 controls
were observed. The scoped oracle contains 1,520 true positives, zero false
positives, and 54 false negatives, giving 100.000% precision and 96.569%
recall. None of 1,629 negative-control effects joined the target agent.

One replay adapter then consumed the process and tool identities that R114 had
already computed, selected exactly those 1,520 true-positive rows, converted
each once to a unit-weight operation, and invoked release `agentpprof 0.2.37`
once. AgentProf returned 1,520 samples with total mass 1,520. Per-category mass
was preserved exactly for dependency (121), edit (380), failure (39), read
(723), and test (257), producing 152 stacks. An independent read-only reviewer
reconstructed every task count, all selected rows, the complete operation
multiset, every profile stack, and all category masses with zero mismatch.

The lineage capture used the existing R114-compatible `agentsight 0.2.37`
research path because the PATH-installed 0.2.43 binary no longer exposes the
R114 `--agent-comm` interface. This result therefore does not validate
AgentSight 0.2.43 specifically. It does establish the tested integration edge:
scoped real-agent effects reject concurrent controls, and current AgentProf
folds the correctly attributed effects across runs without losing rows or
mass. Combined with R170/R224/R251, it supplies a positive cumulative RQ1
answer without claiming automatic task inference or unrestricted causal
coverage. Complete plans, preflight, full result, and independent recomputation
are under
[`loop-001-rq1-r114-current-profile`](tmp/build-and-evaluate/step-0007-20260714T054617-0700/01-experiment-gate/loop-001-rq1-r114-current-profile/),
with machine artifacts under
`.agentsight/experiments/rq1-r114-current-profile-v1/`.

## Admitted RQ1 Independent Stage And Token Evidence

Step 0035 reuses the complete pre-existing source-valid CodeTraceBench target
and the unchanged Step 0024 assignments. All 405 failed trajectories, 20,866
operations, 2,948 official human stage intervals, and 251 benchmark tasks are
scored; no new agent execution, label, partition, threshold, or algorithm is
introduced. Ordinary operation-level B-cubed is the standard primary partition
metric. Recurrence reaches precision 0.828579, recall 0.533630, and F1 0.649173,
versus 0.891296, 0.388437, and 0.541070 for the matched contiguous
source-native raw-action-key view. The `+0.108103` F1 effect has a paired
task-cluster-bootstrap 95% interval of `[+0.087091,+0.129132]`; all 10,000
resamples and all four framework effects are positive.

The source adapter maps 17,148 operation-producing provider responses and
494,862,929 prompt-plus-completion tokens. Token mass is conserved exactly.
For the 1,426 responses shared by 5,144 operations, token-weighted B-cubed
recurrence-minus-raw effects remain positive under equal, all-to-first, and
all-to-last allocation: `+0.084574`, `+0.075910`, and `+0.075671`. This
published weighted-B-cubed extension is a resource-sensitive secondary result,
not a community-standard token-attribution metric or a replacement for the
ordinary primary result. The mapped mass excludes provider calls that do not
produce an official operation and abandoned earlier SWE-agent attempts; it is
not every released trajectory's complete LLM cost.

Phase-only reaches 0.654445 ordinary B-cubed F1. A descriptive paired
task-cluster bootstrap for recurrence minus phase spans zero at
`[-0.017778,+0.008234]`, so neither view reliably dominates the other in this
experiment. This is a mechanism boundary, not a contradiction: Step 0035
supports semantic stage-aligned attribution over raw action identity, while the
separate OSWorld-Human RQ3 experiment supplies recurrence's stronger advantage
over phase-only. Because CodeTraceBench previously participated in selecting
the current constructor, this is post-hoc supporting evidence rather than
untouched independent algorithm confirmation.

The independent full-result reviewer reconstructed every join, metric,
allocation, and bootstrap result without calling the scorer and returned
`PASS`. Complete records are under
[`step-0035-20260716T191253-0700`](tmp/build-and-evaluate/step-0035-20260716T191253-0700/),
with machine artifacts under
`.agentsight/experiments/rq1-codetracebench-token-attribution-v1/`.

## Admitted RQ2 Evidence And Boundaries

The first complete AgentProcessBench experiment provides supporting RQ2
evidence without authorizing a paper result. On all 1,000 official
trajectories and 8,509 human-labeled assistant steps, the target-preserving
semantic profile improves equal-family macro AP over raw action by 0.031522
with a paired 95% interval of [0.015138, 0.053514]. The matched within-raw-leaf
shuffle control gives `p=0.009950`, so the AP gain exceeds pure refinement
granularity. The raw-minus-semantic work-to-50 point estimate is favorable at
0.016320, but its interval [-0.022550, 0.074214] crosses zero. The valid tested
construction is therefore `INCONCLUSIVE`, with positive AP specificity and an
unresolved inspection-work condition. Complete plan, implementation reviews,
preflight, full execution, and independent recalculation are under
`docs/tmp/cycle-0002-20260712T201943-0700/01-experiment-gate/loop-rq2-agentprocessbench/`.

The second complete construction reused published ranking/inspection
principles and a fixed Wilson-shaped finite-ensemble score without selecting
fields, constants, or thresholds from human-label values. Semantic again
improves equal-family macro AP, by 0.024515 with paired interval
[0.016472, 0.051486], and exceeds all 200 matched refinements
(`p=0.004975`). Its work-to-50 point effect is favorable in all four families
and improves the macro point estimate to 0.027651, but the paired task-cluster
interval [-0.026809, 0.080506] still crosses zero. The fixed conjunctive verdict
is therefore also `INCONCLUSIVE`, not `CONTRADICTED`. Complete source/method
selection, three serial plan reviews, implementation and review, REAL
PREFLIGHT and review, FULL result, and independent recalculation are under
`docs/tmp/cycle-0002-20260712T201943-0700/01-experiment-gate/loop-rq2-agentprocessbench-wilson/`.

Because project agents had already observed the benchmark's human targets, the
second run is supporting adaptive within-benchmark construction evidence, not
a fresh holdout. It shows that evidence-stabilized ranking improves the work
point estimate and makes every family favorable, but does not resolve the
cluster-level work uncertainty. The predeclared two-construction limit is now
reached: do not create a third AgentProcessBench score variant. Neither result
narrows RQ2 or the positive hypothesis, and neither unsupported conjunctive
construction is inserted into the paper.

Three other current-cycle constructions remain internal boundaries. The
CodeTraceBench comparison was valid but mixed, ToolSafe was valid but
contradicted for its tested cross-family construction, and the full AgentNet
comparison showed that dropping `target` from the semantic key invalidates the
intended comparison. Their reports remain under the corresponding
`loop-rq2-codetracebench/`, `loop-rq2-toolsafe/`, and `loop-rq2-agentnet/`
directories. None changes RQ2 or the positive hypothesis.

Two complete negative conditions remain auditable and constrain mechanism
reuse; neither changes RQ2 or belongs in the final paper's positive result
story.

- **Revision 0 — flattened induced leaves.** AgentRx AP was 0.02584 at 0.02236
  prevalence, and TELBench AP was 0.21487 at 0.21384 prevalence. The unchanged
  leaf inducer therefore supplies no positive RQ2 evidence. Full plan,
  execution, raw artifacts, and independent review are under
  `docs/tmp/cycle-0001-20260711T164850-0700/01-experiment-gate/loop-rq2-00/`.
- **Revision 2 — Hodoscope comparison.** The official density-gap/FPS bundle
  reached the published iQuest behavior at first-hit rank 2.9 +/- 0.3, while
  the tested 8/32/128 recursive stack reached 24.9 +/- 15.8. The tested
  recursive hierarchy had no stable advantage over its matched flat terminal
  partition or released turn-position grouping. This is a valid boundary for
  that sparse action-level signal, not evidence that flatness caused the gap or
  that RQ2 should shrink. Full artifacts and review are under
  `docs/tmp/cycle-0001-20260711T164850-0700/01-experiment-gate/loop-rq2-02/`.

The complete Cycle 0003 HINTBench experiment is a further mechanism boundary,
not a thesis challenge or reader-facing paper result. It used all 80 official
validation and 536 official test trajectories, 616/616 terminal local-model
outputs, the real AgentProf binary, all 24 validation field orders, and 10,000
trajectory-stratified paired bootstrap replicates. AgentProf reached 80% macro
recall at 41.5702% inspection work versus 46.2918% for the mandatory raw-action
baseline. The paired AgentProf-minus-raw-action interval was
[-0.293709, +0.008566], so the strict all-baseline criterion was
`INCONCLUSIVE`. Exact flat reconstruction matched AgentProf as the declared
algebraic identity control. Do not retune this test population. The plan,
preflight, full artifacts, and two independent exact result audits are under
`docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/`.

The complete Step 0004 TraceElephant experiment adds a real-failure population
of all 220 released executions and 5,960 atomic steps. Every declared profile,
200 matched semantic permutations, and 10,000 paired bootstrap replicates
completed and passed an independent exact recalculation. At the predeclared
80% macro decisive-step-recall point, the fixed AgentProf construction needs
100.00% inspection work versus 71.91% for the source-native raw-action profile;
the AgentProf-minus-raw interval `[-1.90, +45.86]` percentage points crosses
zero, so that tested hypothesis is `VALID / INCONCLUSIVE`. The complete curve
also shows a strong early concentration signal: AgentProf reaches 50% macro
recall at 19.55% work versus 46.64% for raw action. The large final tied tier,
not an everywhere-flat curve, causes the strict 80% outcome. This result closes
the fixed propagation-and-ranking construction without changing the positive
RQ2 hypothesis or authorizing retuning on these labels. Full reports are under
[`loop-001-rq2-traceelephant`](tmp/build-and-evaluate/step-0004-20260713T172452-0700/01-experiment-gate/loop-001-rq2-traceelephant/),
with terminal metrics under
`.agentsight/experiments/traceelephant-rq2-v1/metrics/`.

Step 0011 then performed one complete read-only synthesis of the three full
experiments and their existing controls. AgentProcessBench contributes a
semantic-minus-raw AP interval of `[+0.015138,+0.053514]` and a matched-
refinement `p=0.009950`. HINTBench's prospective Work@80 comparison is positive
against native, independent-step, and session organization, while its raw-
action interval still crosses zero. TraceElephant's favorable Work@50 and
Recall@20 region remains descriptive because its prospective Work@80 result is
inconclusive. The explicit cumulative rule is supporting: two independent
workloads contain positive prospective components, AgentProcessBench supplies
the semantic-specific matched control, and no workload has a supported primary
contradiction. This is retrospective synthesis and reporting correction, not a
new confirmatory test or independent observation; all three original
conjunctive workload verdicts remain `INCONCLUSIVE`. Full plan, three serial
plan reviews, preflight, results, and fresh independent recomputation are under
[`loop-001-rq2-cumulative-baseline-synthesis`](tmp/build-and-evaluate/step-0011-20260714T095842-0700/01-experiment-gate/loop-001-rq2-cumulative-baseline-synthesis/).

Step 0013's complete paper review closed the idea of inventing a new
matched-granularity partition, interpolation, Pareto score, or another
localization benchmark. The only admitted next node is an audit and replay of
the already complete R337 fixed-recall result over six labeled tasks from four
public datasets. At the existing 25% recall target, the tracked report says the
operation-stack view reaches all six tasks with median work 0.2000 and median
16 inspected groups, versus 0.2495 work and 50 groups for fixed-session
organization. These are not yet admitted paper numbers: the current audit must
reconstruct the six task rows, scorer-only hidden-label use, source provenance,
and raw/flat counterpoints. The audit must not add a new metric, cutoff,
partition, resample, model, dataset, or human dependency, and it must not
rebrand R337 as a matched-granularity proof or downstream intervention.

Step 0014 completed that bounded audit. A fresh R333 run reconstructed all six
task groupings, visible rankings, and inspection curves from the four public
operation sources; all five emitted R333 CSV files were byte-identical to the
existing result. A fresh R337 replay then reproduced all four emitted R337 CSV
files byte-for-byte. Independent review directly recomputed six tasks, four
datasets, 34,539 task-operation instances, and 3,699 positives from the task
loader and operation files and verified that visible fields are derived from
actions, source metadata, and separate execution outcomes rather than the
target oracle.

At the existing 25% positive-recall point, operation stacks reach all six
tasks with median inspection work 0.2000 and median 16 groups, versus 0.2495
and 50 for fixed-session organization. Per-task work wins/ties/losses are
4/1/1 and group-count outcomes are 5/0/1. Against flat, operation stacks save
work on 6/6 tasks but necessarily inspect more than one group. Against raw
action, outcomes are mixed (work 3/1/2; groups 2/0/4), and raw has slightly
lower medians. The admitted conclusion is therefore bounded: recurring
operation-stack views reduce session fragmentation while retaining lower
typical work on these six tasks. This is supporting reconstruction of old
evidence, not a new independent observation, Pareto proof, universal semantic
victory, human-productivity result, or downstream intervention. Complete plan,
preflight, replay, and independent result review are under
[`loop-001-rq2-r337-reuse-audit`](tmp/build-and-evaluate/step-0014-20260714T105109-0700/01-experiment-gate/loop-001-rq2-r337-reuse-audit/).

Step 0019 adds a distinct downstream-decision result over the same six public-
data tasks without changing their profiles, labels, or existing rankers. A
fixed quantized Qwen3.6-27B reader saw each operation-stack and fixed-session
top-five packet with rank, view, and original group IDs hidden, selected exactly
three groups, and received all five cyclic group positions. All 66 planned
presentations completed on their first API attempt. Hidden benchmark positives
were loaded only after collection, and an independent reviewer exactly
recomputed every response and task row.

After averaging rotations within each task/view, operation stack improves
selected-positive operation recall on 5/6 tasks with median paired delta
`+0.080571` and precision on 4/6 with median delta `+0.035501`. Both
predeclared primary conditions pass, so the tested hypothesis is `VALID /
SUPPORTED`. Work fraction is higher on 4/6 tasks with median delta `+0.006302`,
including two large increases. The admitted value is therefore supporting RQ2
evidence for group prioritization at a fixed three-group budget, not lower
inspection work, reader-only causality, human productivity, remediation,
raw-action superiority, universal view dominance, or a stand-alone whole-RQ
answer. Plan, complete run, and independent review are under
[`experiment-001`](tmp/build-and-evaluate/step-0019-20260714T164922-0700/experiment-001/),
with raw artifacts under
`.agentsight/experiments/r315-llm-reader-rq2-v2/full/`.

Step 0033 resolves the remaining mixed-metric presentation problem without a
new benchmark, model call, profiler run, score, cutoff, or ranking method. It
reconstructs the fixed operation scores from all three completed public
localization workloads and applies one standard definition: each
target-bearing trajectory is a query, its operations are ranked items, and its
independently annotated problem operations are relevant items. Non-interpolated
AP is computed with scikit-learn and averaged across queries. AgentProcessBench
contributes 614 target-bearing queries, HINTBench 400, and TraceElephant 220.

The then-retained consolidation reported AgentProf trajectory MAP of
`0.788919` versus `0.773170` raw action on AgentProcessBench, `0.452852` versus
`0.281491` on HINTBench, and `0.230168` versus `0.121270` on TraceElephant. The
paired 10,000-draw intervals were `[+0.004727,+0.027081]`,
`[+0.154534,+0.188739]`, and `[+0.078010,+0.141302]`. AgentProcessBench
resamples all 200 released tasks
within family; HINTBench resamples target-bearing records within 44
environments; TraceElephant resamples traces within five cells. Pooled
operation AP retains the 386 AgentProcessBench and 136 HINTBench zero-positive
trajectories and has the same AgentProf-over-raw direction. Counting HINTBench's
three unmappable official targets as unretrieved also preserves the result.

That review reconstructed the planned populations, 1,234 query rows, target
coverage, and bootstrap intervals and initially returned `VALID / COMPLETE /
SUPPORTED`. Step 0036 subsequently discovered that mathematically zero HINT
Wilson lower bounds had been represented by floating residues and superseded
the Step 0033 HINT values after exact-zero canonicalization. The authoritative
current HINT MAP values are `0.452373` versus `0.281237`, with interval
`[+0.153772,+0.188223]`; Step 0036 and its fresh independent reconstruction are
the cited result. Step 0033 remains useful as the historical standard-MAP
consolidation, not as the current numerical authority. It does not claim human
debugging time or universal view dominance. Complete historical reports are under
[`step-0033-20260716T165119-0700`](tmp/build-and-evaluate/step-0033-20260716T165119-0700/),
with local raw artifacts under
`.agentsight/experiments/rq2-standard-map-existing-trajectories-v1/full/`.

Step 0036 then tests the strongest remaining whole-paper objection without a
new trajectory, model, localizer, profile, field order, or paper RQ: whether
the same-signal AgentProf-versus-raw MAP gain survives an exact fixed operation
budget and whether it merely spreads signal relative to direct atomic scoring.
The complete matrix covers AgentProcessBench (1,000 trajectories / 8,509
operations), HINTBench (536 / 12,877), and TraceElephant (220 / 5,960), with
all 1,234 target-bearing queries and all 522 clean trajectories retained.

The final independently reconstructed result is `VALID / SUPPORTED`, with
boundary research value. AgentProf MAP / expected Recall@20% is
`0.788919 / 0.562766` versus raw `0.773170 / 0.544346` on
AgentProcessBench, `0.452373 / 0.574109` versus
`0.281237 / 0.486033` on HINTBench, and
`0.230168 / 0.457529` versus `0.121270 / 0.348270` on
TraceElephant. The six AgentProf-minus-raw intervals are wholly positive:
MAP `[+0.004565,+0.027106]`, `[+0.153772,+0.188223]`, and
`[+0.077026,+0.141857]`; Recall@20%
`[+0.005274,+0.032305]`, `[+0.068632,+0.107685]`, and
`[+0.054357,+0.164569]`.

Atomic scoring is the important counterpoint. It reaches
`0.863171 / 0.651185` on AgentProcessBench and decisively beats AgentProf on
both metrics. AgentProf beats atomic on HINT MAP but not conclusively on
Recall@20%; it beats atomic on TraceElephant Recall@20% but not conclusively on
MAP. HINT AgentProf and raw grouping both give nonzero support to all 136 clean
trajectories and 76.54% of their operations, versus 9.56% and 0.742% for
atomic. Thus the reviewed claim is the consistent matched raw-action advantage,
not universal semantic-propagation superiority. The external signals remain
bounded: AgentProcessBench median StepAcc is 0.6678, HINT no-type localization
F1 is 0.4974, and TraceElephant step accuracy is 0.1636.

Two superseded attempts and both numerical defects remain recorded rather than
hidden. The final HINT pooled AP values are AgentProf 0.249439, raw 0.180366,
atomic 0.266199, and session 0.103928; all 24 validation candidates retain the
same selected order after zero correction. Complete plans, invalid-attempt
audit, final step report, and independent review are under
[`step-0036-20260717T041400-0700`](tmp/build-and-evaluate/step-0036-20260717T041400-0700/),
with authoritative raw results under
`.agentsight/experiments/rq2-same-signal-diagnostic-decomposition-v1/full/`.

The earlier RQ2 score freeze was correct before this atomic/propagation
boundary was isolated. The user's later explicit request to improve the
current algorithm on already-run trajectories authorized one adaptive
mechanism candidate, not an open-ended score search. Step 0037 preserves every
strict operation-local ordering and lets the existing semantic recurrence
score refine only exact local-score ties. A matched local+raw candidate uses
the identical composition rule and differs only in its secondary key. No new
metric, cutoff, weight, model, hierarchy, benchmark, or trajectory is added.

The independently reconstructed full result covers the same 1,756
trajectories, 27,346 operations, 1,234 target-bearing queries, and 522 clean
trajectories. Standard per-query AP and workload MAP remain primary;
tie-averaged Recall@20% remains a secondary fixed-budget analysis rather than
an official benchmark metric. Local+semantic MAP is `0.895972`, `0.544906`,
and `0.321905` on AgentProcessBench, HINTBench, and TraceElephant. Relative to
atomic/local-only ranking, the paired MAP gains are `+0.032801`
`[+0.024421,+0.042081]`, `+0.134348`
`[+0.121196,+0.147153]`, and `+0.113192`
`[+0.086972,+0.141692]`. Relative to incumbent semantic-only ranking, the
gains are `+0.107052` `[+0.088462,+0.126437]`, `+0.092534`
`[+0.077050,+0.109587]`, and `+0.091736`
`[+0.058967,+0.126763]`.

The decisive matched secondary-key comparison establishes the workload
boundary. Local+semantic minus local+raw MAP is `+0.002900`
`[-0.000497,+0.006852]` on AgentProcessBench, `+0.038945`
`[+0.029118,+0.048908]` on HINTBench, and `+0.072552`
`[+0.049844,+0.097053]` on TraceElephant. The registered all-workload
intersection is therefore `INCONCLUSIVE`, not supported, although no
comparison is contradicted. Candidate support equals atomic support by
construction; this is an algorithm property, not a performance metric or
specificity result. The admitted conclusion is that preserving local evidence
and using semantic recurrence only for exact local-score ties improves over
atomic and incumbent semantic-only ranking on all three observed populations,
and beats raw-action tie refinement on HINTBench and TraceElephant while
AgentProcessBench does not distinguish the two refinements. Because the
candidate was chosen after Step 0036 target-dependent inspection, it is
post-hoc mechanism evidence, not untouched generalization. The candidate is
closed as a universal replacement, and no further score tuning on these same
populations is admitted. The approved plan, complete execution history, and
independent result review are under
[`step-0037-20260717T052237-0700`](tmp/build-and-evaluate/step-0037-20260717T052237-0700/),
with authoritative local raw results under
`.agentsight/experiments/rq2-local-first-semantic-ranking-v1/full/`.

The unexecuted revision-1 plan is superseded because it bundled roughly eleven
comparator types and several independent research programs. Its history remains
under
`docs/tmp/cycle-0001-20260711T164850-0700/01-experiment-gate/loop-rq2-01/`.

Older experiments remain under `docs/visexp/out/` with source scripts under
`docs/visexp/` and `script/`. A number returns to the paper only after its exact
input, oracle separation, baseline information, metric, and raw path are
rechecked; old readiness booleans are not evidence.

## Admitted RQ4 Evidence And Boundaries

Step 0005 ran release `agentpprof 0.2.37` over the four complete existing
public operation files and their exact union. The complete matrix contains five
natural input sizes, one fixed semantic construction, one raw-action cost
control, and three repetitions per cell: 30/30 invocations completed and passed
independent recomputation. Semantic median construction increases monotonically
from 40 ms for 729 operations to 1.17 s for the 27,765-operation union. The
descriptive fit has slope 0.042176 ms/operation and R-squared 0.999738. On the
union, throughput is 23,731 operations/s and maximum observed RSS is 464.49
MiB. Relative to the identical-input raw-action cost control, the semantic
hierarchy adds 180 ms median time (18.18%) and 1.29% maximum RSS.

R160 is reused only as bounded cache-mechanism evidence. Its one predecessor
AgentFlame fixed-input pair took 1.64 s clean with 60 LLM calls and 0.11 s
cached with 76/76 hits and zero calls, a 14.91x observed ratio. It is not
current-binary cache timing or a repeated estimate. Full Step 0005 plans,
reviews, preflight, results, and independent recomputation are under
[`loop-001-rq4-cost-scaling`](tmp/build-and-evaluate/step-0005-20260714T022913-0700/01-experiment-gate/loop-001-rq4-cost-scaling/),
with machine-readable results under
`.agentsight/experiments/rq4-cost-scaling-v1/`.

## Admitted RQ3 Evidence And Boundaries

Step 0006 completed the fixed OSWorld-Human human-action-boundary experiment
without adding a dataset, tagger family, feature design, or profiler mechanism.
The run reused all 287 eligible task-instance sessions, 3,978 unit-weight
operations, 3,691 adjacent pairs, and 2,042 official human groups. A fixed
R297 Bernoulli boundary tagger was trained and evaluated with five
session-blocked out-of-fold splits; each session supplied held-out predictions
exactly once. The tagger reaches 0.7388 micro boundary F1, compared with 0.6445
for the strongest simple control (`always_boundary`), an absolute gain of
0.0943. It exceeds that control in every fold.

The predicted groups reach 0.8160 operation-weighted B-cubed F1 against the
human partition, compared with 0.6784 for the strongest simple control, an
absolute gain of 0.1376. Release `agentpprof 0.2.37` consumes the learned group
field through the real operation-stack path and conserves all 3,978 operation
units in 2,249 stacks. An independent reviewer reconstructed every confusion
count, all four partitions, fold assignment and isolation, predictions, and
the complete stack-to-weight map from raw artifacts with zero mismatches.

This evidence supports one supervised boundary-identity component of RQ3 on
held-out OSWorld-Human task-instance sessions. It does not by itself establish
unsupervised tagging, cross-family generalization, or the paper-level task,
phase, and action identity components. Complete plans, three serial plan
reviews, preflight, full results, and independent recomputation are under
[`loop-001-rq3-osworld-boundary-fidelity`](tmp/build-and-evaluate/step-0006-20260714T031808-0700/01-experiment-gate/loop-001-rq3-osworld-boundary-fidelity/),
with raw machine artifacts under
`.agentsight/experiments/rq3-osworld-boundary-fidelity-v1/`.

Step 0008 completed the fixed task/action partition-fidelity experiment using
only four reused public-source prefixes with independently scoreable native
fields. The target-blind existing TF-IDF/K-Means backend received one task text
per session, without native task labels, and predictions were broadcast back
to operations for the predeclared operation-weighted V-measure. It reaches
0.5565 on all 9 currently available Mind2Web sessions / 49 operations and
0.8151 on 100 ScienceWorld sessions / 2,504 operations, both at full coverage;
the matched constant-tag control is 0 on each source.

The unchanged action normalization path is mixed. It reaches 0.8601 V-measure
at full coverage on the small 2-session / 9-operation AndroidControl prefix,
but only 0.3000 V-measure and 17.2344% coverage on 500 GUI-Odyssey sessions /
7,868 operations. All 6,512 GUI unmatched rows remain inside scoring support.
Both source-field audits found zero structured gold-label copies. These action
rows are retained as a current-backend boundary; they do not change RQ3 or its
positive hypothesis and are not automatically inserted into the paper's
positive result story.

Release `agentpprof 0.2.37` conserves every operation and all weight in each
cell and their exact 10,430-operation union. A fresh independent reviewer
regenerated every operation from the official source prefix, reproduced every
prediction and metric, and matched every folded-stack multiset. The run is
`VALID`, with positive task-partition evidence, one small positive action cell,
and one complete negative action-backend boundary. Complete plans, three plan
reviews, two implementation reviews, real preflight, full results, and
independent recomputation are under
[`loop-001-rq3-task-phase-action-reuse`](tmp/build-and-evaluate/step-0008-20260714T083320-0700/01-experiment-gate/loop-001-rq3-task-phase-action-reuse/),
with raw machine artifacts under
`.agentsight/experiments/rq3-task-action-v1/`.

Step 0017 then tested the actual built-in Rust stack-induction path on the same
complete 287-session OSWorld-Human population used for boundary scoring. The
revised target-blind mechanism replaces the old multi-term score with one equal
mean of resource-weighted normalized per-field information gain and accepts a
split only above `ln(n)/(2n)`. Both the revised and frozen pre-change binaries
completed all 574 session-method executions; every operation received one
terminal path, all 3,978 units were conserved, scorer/oracle fields remained
excluded, and an independent reviewer recomputed all metrics.

The revision raises boundary F1 from 0.0843 to 0.4231 and operation-weighted
B-cubed F1 from 0.4653 to 0.6165, while reducing no-split sessions from 204 to
4. It nevertheless trails the strongest simple controls (0.6445 boundary F1
and 0.6784 B-cubed F1), so the fixed candidate hypothesis is contradicted. This
is supporting mechanism evidence, not an answer to all of RQ3 and not a thesis
challenge. The arbitrary depth-four limit is materially active in 106/287
sessions; the next post-hoc experiment therefore changes only that limit while
freezing the fields, objective, penalty, tie rules, population, metrics, and
scorer. Complete reports are under
[`loop-002-rq3-rust-inducer-fidelity`](tmp/build-and-evaluate/step-0017-20260714T121012-0700/01-experiment-gate/loop-002-rq3-rust-inducer-fidelity/),
with raw artifacts under
`.agentsight/experiments/rq3-rust-inducer-fidelity-v1/`.

Step 0018 changes only the registered depth bound in the same current binary.
The complete 287-session run reproduces every Step 0017 depth-four row, assigns
and conserves all 3,978 operations/units under both configurations, and keeps
scorer fields outside induction. Depth 255 improves boundary F1 from 0.4231 to
0.4720 and B-cubed F1 from 0.6165 to 0.6720; it stops intrinsically at maximum
observed depth 26 and changes paths in 60 sessions. It still clears neither
metric's strongest simple control (0.6445 and 0.6784), so the registered
sufficient-explanation hypothesis is contradicted. This is a valid post-hoc
mechanism boundary and a better implementation configuration, not a broad RQ3
answer. Complete reports are under
[`loop-001-rq3-inducer-depth`](tmp/build-and-evaluate/step-0018-20260714T160153-0700/01-experiment-gate/loop-001-rq3-inducer-depth/),
with raw artifacts under
`.agentsight/experiments/rq3-rust-inducer-depth-v1/`.

Step 0020 changes the mismatched objective rather than adding another depth,
field, cutoff, or score term. The replacement learns cross-session recurrence
from adjacent visible `action` transitions: coherent transition-space NPMI and
deterministic occurrence-weighted one-dimensional two-means separate weak or
unseen transitions from recurring motifs. On the same fixed five session folds,
287 sessions, 3,978 operations, and 3,691 adjacent pairs, it reaches boundary
F1 0.6799 and operation-weighted B-cubed F1 0.7862. These results clear the
registered strongest simple controls at 0.6445 and 0.6784 and improve over the
cap-free information-gain mechanism by 0.2080 and 0.1142 respectively.

The candidate uses only `session` to define sequences and `action` to learn
transition recurrence; human groups and all scorer fields remain outside
construction. The release Rust port exactly matches the fixed Python evaluator
on all 3,691 boundary decisions, 3,978 motif assignments, and 2,656 segments,
conserves all 3,978 units, and produces an identical report after hidden-field
mutation. Because the same population's labels had already exposed the old
mechanism's failure and informed this objective change, the result is supported
post-hoc mechanism-development evidence, not an untouched RQ3 confirmation,
motif-name validation, or cross-family generalization result. Complete reports
are under
[`step-0020-20260715T001404-0700`](tmp/build-and-evaluate/step-0020-20260715T001404-0700/),
with raw evaluator and port-equivalence artifacts under
`.agentsight/experiments/rq3-recurrence-inducer-v1/full/` and
`.agentsight/experiments/rq3-recurrence-rust-equivalence-v1/full/`.

Step 0021 then tests that unchanged Rust port on already-completed
CodeTraceBench artifacts rather than collecting or normalizing a new source.
The full target-disjoint run covers 405 failed trajectories, 20,866 operations,
20,461 adjacent pairs, and 2,948 complete official stage intervals across four
code-agent frameworks. All validity, coverage, leakage, and conservation
checks pass under independent raw-result reconstruction. Recurrence reaches
boundary F1 0.2685, barely above action-change 0.2675, while B-cubed F1 0.4750
trails external phase-change 0.6544. It equals action-change on 20,391/20,461
pair decisions; all 70 differences occur in Terminus2 and merge
`install -> other`.

The approved verdict is mixed and does not enter the paper as positive
cross-family confirmation. It is retained as mechanism-selection evidence:
the occurrence-weighted NPMI cutoff's high cluster is dominated by identical-
action repetitions, so the release constructor almost never recognizes
recurring continuity across an action change. The fixed RQ3 hypothesis and
paper story remain unchanged. The next experiment may change only this
calibration principle—same-action pairs stay continuous by identity and
two-means separates recurrence among actual action changes—then rerun the
existing OSWorld-Human and CodeTraceBench populations once without a feature,
threshold, or benchmark sweep. The reviewed step is
[`step-0021-20260715T023451-0700`](tmp/build-and-evaluate/step-0021-20260715T023451-0700/).

Step 0022 then tests that one minimal repair directly on both existing
trajectory populations: identical actions stay continuous by identity, while
the unchanged occurrence-weighted NPMI two-means cutoff is calibrated only on
action-changing transitions. It adds no benchmark, input field, parameter,
cutoff sweep, algorithm name, or second candidate. On complete OSWorld-Human,
boundary F1 falls from 0.6799 to 0.5427 and B-cubed F1 falls from 0.7862 to
0.7425. On complete CodeTraceBench, boundary F1 rises from 0.2685 to 0.2871 and
B-cubed F1 rises from 0.4750 to 0.6492; B-cubed improves in all four frameworks
but remains 0.0053 below phase-change in the pooled result.

The candidate Rust path exactly matches Python on all 3,691 OSWorld decisions,
3,978 assignments, 2,107 segments, 42 unique motifs, and all 3,978 units of
mass. Independent review classifies the experiment `VALID / COMPLETE / MIXED`.
The result shows that identity repetitions can dominate the old two-cluster
cutoff, but simply excluding them over-merges a different real population.
The candidate is therefore not adopted; only its Step 0022 code changes were
restored, leaving the current Step 0020 implementation and paper result intact.
This mechanism boundary does not change RQ3, its positive hypothesis, the
thesis, or the AgentProf story, and no second candidate is introduced in the
same experiment. Complete reports are under
[`step-0022-20260715T031526-0700`](tmp/build-and-evaluate/step-0022-20260715T031526-0700/),
with raw artifacts under
`.agentsight/experiments/rq3-cross-action-recurrence-v1/full/`,
`.agentsight/experiments/rq3-cross-action-rust-equivalence-v1/full/`, and
`.agentsight/experiments/rq3-cross-action-codetracebench-v1/full/`.

Step 0023 directly reuses those same completed trajectories to isolate the two
Step 0022 components. Same-action pairs retain the Step 0020 global NPMI
cutoff, while action-changing pairs use the Step 0022 cross-action cutoff. The
rule adds no trace, benchmark, visible field, NPMI term, clustering method,
parameter, or algorithm name. On complete OSWorld-Human, B-cubed F1 is 0.7846
versus current 0.7862 (delta -0.0016) and boundary F1 is 0.6781 versus 0.6799.
It adds 11 false-positive cross-action boundaries and 11 groups while retaining
identical TP, FN, and B-cubed precision. On complete CodeTraceBench, it exactly
retains the Step 0022 component result: B-cubed F1 0.6492 versus current 0.4750
and boundary F1 0.2871 versus 0.2685, with B-cubed improvement in all four
frameworks.

Rust and Python agree on all 3,691 OSWorld decisions, 3,978 assignments, 2,667
segments, 44 motifs, both cutoffs, selected calibration strata, and all 3,978
units of mass. Independent review classifies the experiment
`VALID / COMPLETE / MIXED`: the candidate is strictly lower on one population
and higher on the other, so it fails the fixed exact-Pareto replacement rule.
Only Step 0023 candidate code was restored, leaving the Step 0020 release
constructor and paper result unchanged. This establishes that conditioning
nearly removes Step 0022's OSWorld regression while preserving the cross-family
gain, but raising the cross-action cutoff above the current cutoff can introduce
new false boundaries. It does not change RQ3, its positive hypothesis, the
thesis, or the AgentProf story. Complete reports are under
[`step-0023-20260715T035513-0700`](tmp/build-and-evaluate/step-0023-20260715T035513-0700/),
with raw artifacts under
`.agentsight/experiments/rq3-conditioned-recurrence-v1/full/`,
`.agentsight/experiments/rq3-conditioned-recurrence-rust-equivalence-v1/full/`,
and `.agentsight/experiments/rq3-conditioned-recurrence-codetracebench-v1/full/`.

Step 0024 applies the single directional constraint exposed by Step 0023:
same-action pairs retain the global cutoff, while action-changing pairs use
`min(global_cutoff, cross_action_cutoff)`. NPMI, occurrence weighting,
two-means, unseen-pair handling, segment construction, motifs, fields, and both
complete trajectory populations remain unchanged. The rule is monotone with
respect to the Step 0020 constructor: it can remove a current boundary but
cannot add one.

The complete OSWorld-Human result is exactly unchanged on every one of 3,691
decisions: boundary F1 0.679922 and B-cubed F1 0.786170, with zero removed and
zero added current boundaries. On complete CodeTraceBench, the rule removes
5,974 current boundaries and adds zero; boundary F1 rises from 0.268506 to
0.287106 and B-cubed F1 from 0.475008 to 0.649173. B-cubed improves in
OpenHands, SWE-agent, Terminus2, and mini-SWE-agent relative to the prior
global constructor. Against the external phase-change baseline, the final
constructor has higher boundary F1 (0.287106 versus 0.225425) and slightly
lower B-cubed F1 (0.649173 versus 0.654445), with per-framework B-cubed wins on
two of four frameworks. This CodeTraceBench population is the existing 405
source-valid failed trajectories from the verified split. The release Rust
path matches Python on all 3,691 OSWorld decisions, 3,978 assignments, 2,656
segments, 44 motifs, and all mass.

Independent raw review classifies Step 0024 `VALID / COMPLETE / SUPPORTED`:
B-cubed is no lower on both complete populations and strictly higher on one.
The monotone candidate therefore replaces the Step 0020 runtime path. This is
supporting post-hoc implementation-selection evidence because both populations
were reused after mechanism diagnosis; it is not untouched confirmation,
literal motif-name validation, or a complete RQ3 answer. Complete reports are
under
[`step-0024-20260715T042557-0700`](tmp/build-and-evaluate/step-0024-20260715T042557-0700/),
with raw artifacts under
`.agentsight/experiments/rq3-monotone-recurrence-v1/full/`,
`.agentsight/experiments/rq3-monotone-recurrence-rust-equivalence-v1/full/`, and
`.agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/full/`.

At the user's direct request, Step 0025 reopens only one bounded refinement on
those same retained trajectories. It keeps Step 0024's threshold decisions but
retains an action-changing boundary only at a sequence-local raw-NPMI minimum.
The complete candidate is `VALID / COMPLETE / MIXED`: CodeTraceBench B-cubed
F1 rises from 0.649173 to 0.671671 across all four frameworks, but
OSWorld-Human falls from 0.786170 to 0.746958 and boundary F1 falls on both
populations. The rejected candidate is therefore removed exactly; the Step
0024 implementation remains the release constructor. This result records a
mechanism boundary, not a new algorithm, smaller RQ, changed hypothesis, or
paper-story revision. Complete reports are under
[`step-0025-20260715T054105-0700`](tmp/build-and-evaluate/step-0025-20260715T054105-0700/).

Step 0026 audits whether the retained decisions authorize another direct
improvement. They do not under the current action-pair/small-window flat-
segmentation contract. The same visible pair has mixed labels for 91.2% of
OSWorld-Human decisions and 99.7% of CodeTraceBench decisions; Step 0025's
suppression removes mostly true OSWorld boundaries but mostly false
CodeTraceBench boundaries. Score, support, cutoff sign, and session length do
not identify a common direction. Independent raw review therefore closes this
existing-trajectory refinement branch with no candidate and no paper change.
This is a scoped paper-value decision, not a claim that every future sequence
model is impossible. Reports are under
[`step-0026-20260715T063827-0700`](tmp/build-and-evaluate/step-0026-20260715T063827-0700/).

Step 0027's whole-paper REVIEW later identified a different information
contract rather than reopening Step 0026's target-outcome-driven tuning space:
fit one scalar cutoff from independently grouped reference trajectories while
keeping the Step 0024 NPMI score and post-cutoff construction unchanged. Step
0028 admitted that supporting RQ3 hypothesis on the same existing
OSWorld-Human and CodeTraceBench trajectories. The plan and implementation
reviews passed, but both permitted REAL PREFLIGHT attempts stopped inside the
self-authored OSWorld adapter before NPMI construction, cutoff fitting,
`agentpprof` invocation, prediction persistence, target-label loading, or any
candidate metric. The raw OSWorld root contains only an empty `preflight/`
directory; the CodeTrace and equivalence roots do not exist.

Step 0028 is therefore `INVALID / hypothesis not tested / dependency-only`,
not supported, mixed, contradicted, negative, or scientifically inconclusive.
The unvalidated calibration product/evaluator code was removed after
independent result review, while the complete Markdown record remains under
[`step-0028-20260715T072000-0700`](tmp/build-and-evaluate/step-0028-20260715T072000-0700/).
Step 0024 remains the current constructor solely on its prior valid evidence.
The Step 0028 reference-calibration protocol is permanently closed after two
self-authored harness failures: fixing singleton eligibility, changing a run
tag, or renaming the protocol cannot be represented as a fresh or third
attempt. This invalid closure changes no RQ, positive hypothesis, claim, paper
story, or reader-facing result.

At the user's direct request to improve the algorithm on already-run
trajectories, Step 0029 tests one target-blind multi-session grammar
constructor on the same complete OSWorld-Human and CodeTraceBench populations.
It learns recurring adjacent-symbol replacements from reference sessions and
applies each learned rule once in creation order to target sessions. The run is
independently reviewed `APPROVE / VALID / COMPLETE / CONTRADICTED`.

On OSWorld-Human, the grammar candidate reaches B-cubed F1 0.717803 versus
Step 0024's 0.786170 (delta -0.068367), with 1,492 rather than 2,656 predicted
groups. On CodeTraceBench, it reaches 0.633931 versus 0.649173 (delta
-0.015242), with 5,187 rather than 6,897 groups. The candidate is lower on both
registered complete populations and over-merges relative to the current
constructor. Independent review reconstructs all metrics and populations,
replays all 621 OSWorld and 2,453 CodeTrace rules and target applications, and
confirms exact Rust/Python equivalence and prediction-before-oracle timing.

The Step 0029 candidate product and evaluator code is therefore removed exactly
and the Step 0024 constructor remains current. The complete negative mechanism
record remains under
[`step-0029-20260715T083007-0700`](tmp/build-and-evaluate/step-0029-20260715T083007-0700/)
and the raw experiment roots. This result does not enter the reader-facing
paper, change RQ3, narrow its positive hypothesis, or alter the AgentProf story.
It only establishes that recurring multi-action compression alone is not a
better proxy for the two retained operation partitions than Step 0024.

Step 0030 returns to the existing Step 0024 recurrence score and tests one
different information budget on the same retained trajectories: independently
grouped reference operations select a single scalar cutoff by per-operation
B-cubed F1, while target groups remain unavailable until
predictions are fixed. The label-free Step 0024 constructor stays the default;
the candidate is an optional supervised calibration path rather than a new
algorithm, score, benchmark-specific rule, or target-tuned numeric interface.

The complete result is independently reviewed `VALID / SUPPORTED /
SUPPORTING / ADDITIONAL RQ EVIDENCE`. On all 287 OSWorld-Human sessions under
the same five held-out folds, B-cubed F1 rises from 0.786170 to 0.801087 and
boundary F1 from 0.679922 to 0.733953. On 405 CodeTraceBench failed sessions,
one cutoff fitted from 483 disjoint solved sessions raises B-cubed F1 from
0.649173 to 0.666564. Boundary F1 falls from 0.287106 to 0.236176 as predicted
groups fall from 6,897 to 5,331, so the result supports the predeclared
partition objective but not universal boundary improvement. All five OSWorld
cutoffs and the CodeTrace cutoff are unique optima under the fixed smallest-
cutoff tie rule.

An independent reviewer reimplemented NPMI, cutoff enumeration, weighted
B-cubed, fold assignment, and stage expansion from the raw inputs and reproduced
every population, cutoff, prediction, segment, and metric. The release Rust
port then matches the Python experiment exactly on all 3,691 OSWorld and 20,461
CodeTrace adjacent-pair decisions, selected cutoffs, label-free decisions,
segments, motifs, and pooled metrics. The result uses already observed
development populations and additional group annotations, so it remains
supporting implementation evidence rather than untouched cross-family
confirmation or a complete answer to literal task/phase/action tag accuracy.
Complete reports are under
[`step-0030-20260715T161256-0700`](tmp/build-and-evaluate/step-0030-20260715T161256-0700/),
with raw artifacts under
`.agentsight/experiments/rq3-reference-calibrated-existing-traces-v1/` and
`.agentsight/experiments/rq3-reference-calibrated-rust-equivalence-v1/`.

Step 0030 also demonstrates that Step 0028's terminal disposition was caused by
the experiment skill's fixed preflight-attempt counter rather than scientific
evidence: Step 0028 never executed the hypothesis, whereas the same scientific
plan completes after ordinary adapter repair without changing its RQ,
hypothesis, score, information boundary, populations, or interpretation. This
is recorded as a skill/execution deviation, not as an additional experiment
result or a reason to alter the paper story.

Step 0031 evaluates the product's declared task-label path on all 1,012 released
AgentBoard goals from nine official families. The fixed Qwen3.6-27B backend
receives only each goal and the nine family descriptions. Across three complete
no-cache runs, it reaches `742/1,012 = 0.733202` accuracy and `0.695127`
macro-F1, versus `0.248024` and `0.044163` for the majority control, with
identical predictions in all runs. The registered strong `0.80` accuracy and
macro-F1 hypothesis is contradicted, but the complete result is valid bounded
support for literal task-family labeling by the named backend. It does not
establish open-vocabulary naming, phase/action labels, unknown-family transfer,
or a capacity causal effect. The independent raw recomputation is
[`experiment-002/result-review.md`](tmp/build-and-evaluate/step-0031-20260715T182253-0700/experiment-002/result-review.md),
with complete experiment records under
[`step-0031-20260715T182253-0700`](tmp/build-and-evaluate/step-0031-20260715T182253-0700/).

Step 0032 adds the previously missing direct literal-action measurement without
changing RQ3 or the paper story. The official ASE 2025 trajectory-study
artifact supplies 2,737 published action labels over all 120 released
AutoCodeRover, OpenHands, and RepairAgent trajectories. The fixed Qwen3.6-27B
closed-taxonomy backend is evaluated standalone through a llama.cpp adapter; it
reads only the current thought/action and eight declared definitions, and is not
an integrated AgentProf CLI path. The ASE source obtains categories by mapping
known tools and manually resolving the remaining actions, while the operational
prompt definitions come from the TraceView companion guide. Across two complete
runs the backend reaches `0.498425` macro-F1 and
`0.627695` accuracy versus majority `0.060981` and `0.322616`; the macro-F1
effect is `+0.437444` with a whole-trajectory 95% bootstrap interval of
`[+0.380168, +0.494079]`, and every prediction repeats exactly. Independent
review reconstructed the full population, metrics, confusion, framework
results, hashes, and 10,000-replicate bootstrap with zero invalidating finding.
An outer source audit subsequently found 39 visible action fields exactly equal
to their `Locate` target; excluding them from the durable predictions leaves
macro-F1 `0.490445` versus majority `0.061645`, so the positive result persists
without authorizing a blanket target-separation claim.
The result is decisive additional RQ3 evidence for one declared eight-action
taxonomy, not phase identity, open-set transfer, uniform framework accuracy,
tagger SOTA, or every backend. Complete reports are under
[`step-0032-20260716T010251-0700`](tmp/build-and-evaluate/step-0032-20260716T010251-0700/),
with raw artifacts under
`.agentsight/experiments/rq3-literal-phase-action-source-v1/ase-action-identity/`.

Step 0034 tests one nonredundant improvement to the existing Step 0024
recurrence constructor on the already-complete trajectories. It keeps the
action-transition NPMI score and unseen-pair rule unchanged, fits one grouped-
source cutoff on an occurrence-weighted empirical-CDF scale, and transfers that
percentile bidirectionally between OSWorld-Human and CodeTraceBench. Current
label-free recurrence is the main baseline; direct raw-NPMI cutoff transfer is
the equal-information scale ablation. The approved plan uses operation-weighted
B-cubed F1 as the primary standard partition metric and exact boundary F1 as a
secondary standard transition metric.

The complete experiment is independently reviewed `VALID / CONTRADICTED /
SUPPORTING / MECHANISM OR WORKLOAD BOUNDARY`. CodeTrace-to-OSWorld percentile
transfer reaches B-cubed F1 `0.677607` versus label-free `0.786170` (delta
`-0.108562`, paired session-bootstrap 95% interval
`[-0.138246, -0.078428]`). OSWorld-to-CodeTrace reaches `0.473242` versus
`0.649173` (delta `-0.175931`, interval
`[-0.189732, -0.161417]`). The candidate over-merges OSWorld into 1,316 groups
and over-fragments CodeTrace into 12,941, so the registered cross-domain
calibration hypothesis is contradicted on both complete target populations.

Percentile transfer still beats direct raw-cutoff transfer on OSWorld by
`+0.037077` and CodeTrace by `+0.074719`, with wholly positive paired
intervals. The normalization therefore corrects numerical score-scale mismatch
but cannot transfer the two domains' desired grouping semantics. The fresh
reviewer independently reconstructs all 24,844 operation assignments, 24,152
pair decisions, NPMI/CDF values, source cutoffs, standard metrics, and 20,000
stored bootstrap draws. The review also confirms that no target group identity
or boundary reaches prediction, while recording that the OSWorld eligibility
loader necessarily parses label-bearing rows before returning only actions.
The source fitter's midpoint representation lies in empty target-percentile
intervals and changes no decision.

This result closes only cross-domain transfer of one scalar recurrence cutoff.
It does not alter RQ3, its positive hypothesis, the operation-stack model, the
paper story, or the profiling thesis. Step 0024 remains the label-free default,
Step 0030 remains the optional per-domain grouped-reference calibration, and no
Rust port or reader-facing negative row is admitted. Complete records are under
[`step-0034-20260716T175204-0700`](tmp/build-and-evaluate/step-0034-20260716T175204-0700/),
with raw artifacts under
`.agentsight/experiments/rq3-cross-domain-percentile-calibration-v1/`.

## Requirements For The Next Experiment

The next experiment follows one bounded literature/source screen and must
satisfy these project-local controls:

1. answer one paper-level RQ and one decisive uncertainty;
2. state one primary outcome and the strongest competing explanation;
3. reuse a published protocol, official benchmark, real agent system, or public
   trace source whenever possible;
4. compare the method with the smallest set of strongest fair baselines;
5. match visible information, tuning opportunity, and evaluation budget;
6. run a real end-to-end preflight, then every planned cell and repetition to
   terminal status;
7. retain negative, invalid, and inconclusive rows;
8. separate run validity from the scientific answer;
9. keep the assigned RQ and positive hypothesis fixed; improve the mechanism,
   signal, workload, or protocol when a tested construction fails;
10. reject optional reviewer robustness that would turn the experiment into a
    second research program.
11. before literal-taxonomy inference, enumerate exact target-label strings in
    every model-visible field and record an exclusion or sensitivity result.

## Next Evidence Selection

Step 0004 completed the selected TraceElephant experiment and its independent
result and outer reviews. The experiment-specific 80%-recall hypothesis is
`VALID / INCONCLUSIVE`, but the outer audit synthesizes it with the significant
AgentProcessBench AP result and the independent HINTBench and TraceElephant work
curves. The paper-level RQ2 correspondence/concentration question now has an
evidence-backed positive answer; another tag, score, cutoff, or benchmark
variant has lower paper value than testing a different fixed RQ.

Step 0006 completed that selected RQ3 held-out human-boundary experiment. The
fixed tagger beats the strongest simple control on both predeclared outcomes,
the full current-profiler path conserves all mass, and EXPERIMENT, WRITE, and
whole-paper REVIEW all pass their assigned scopes. REVIEW selects RQ1 as the
next decisive experiment because the current declared-tag separation does not
independently validate operation-to-effect attribution, while the repository
already contains R114's complete real exact-lineage design and controls.

Step 0007 completed the selected R114 replay. The unchanged 20-task suite passes
its aggregate attribution thresholds at 100.000% precision and 96.569% recall,
rejects all 1,629 concurrent-control effects, and current AgentProf preserves
all 1,520 attributed rows and all five known task-category masses. This closes
the selected RQ1 integration experiment. Do not open another RQ1 lineage,
grouping, score, or benchmark variant; WRITE the cumulative positive answer and
let the next whole-paper REVIEW choose the next fixed-RQ evidence need.

Step 0008 then completed the selected RQ3 task/action experiment without a new
benchmark, model, metric, parser, cutoff, or sweep. The existing task backend
provides positive evidence on both independently scoreable public sources; the
existing action normalizer is positive on the tiny AndroidControl prefix and
does not robustly cover GUI-Odyssey. Current AgentProf conserves the complete
10,430-operation union. The EXPERIMENT gate is complete and routes to WRITE for
the positive task-partition result, followed by whole-paper REVIEW. Neither the
mixed action result nor the absence of a phase oracle authorizes changing the
fixed RQ, hypothesis, thesis, or four-RQ structure.

Step 0010's blind whole-paper review and mandatory external search found that
the strongest fixable RQ2 objection is mostly a presentation gap: the completed
full runs already contain native, independent-step, session, flat, width-only,
raw-action, ungrouped-risk, matched-permutation, and oracle references. Step
0011 therefore admits one supporting read-only synthesis inside unchanged RQ2.
Its approved plan preserves every original workload verdict and metric, gives
prospective results priority over descriptive curve regions, forbids a
cross-metric aggregate, and uses only the three existing full-run summaries
and reviews. The complete plan passed three serial independent reviews after
adding an explicit cumulative verdict rule and exact executable input paths.
The full synthesis is now `VALID / COMPLETE`, and its fresh result review
recomputed every reported number with zero must-fix findings after two
interpretation corrections. It routes to WRITE; no new RQ2 benchmark, model,
metric, threshold, resample, or human experiment is needed first.

Step 0017 paused the unexecuted RQ2 reader proposal after explicit user
redirection and completed the higher-value built-in RQ3 mechanism test above.
Step 0018 removed the active depth cap, but could not repair the information-
gain objective's mismatch to heterogeneous operation groups. Steps 0020--0024
then replace that objective with recurrence, diagnose its identity-dominated
calibration on existing CodeTraceBench trajectories, and adopt the monotone
cross-action rule. The final constructor clears the registered OSWorld controls,
preserves every current OSWorld decision, improves B-cubed on all four
CodeTraceBench frameworks, and exactly matches the fixed evaluator. This closes
the bounded recurrence implementation branch. Step 0025 then tests one direct
user-requested sequence-local refinement on the same retained trajectories,
rejects it under the fixed cross-population rule, and restores the Step 0024
release exactly. Step 0026 finds no benchmark-independent small correction in
those retained action-only decisions and closes further tuning of them. Do not
reinterpret either post-hoc result as an untouched answer to all of RQ3. The
paper story and four RQs remain unchanged. Step 0027 subsequently admitted one
different supervised-reference information contract, but Step 0028 exhausted
its two REAL PREFLIGHT attempts in the source adapter before constructing a
candidate or metric. That protocol is closed invalid, its candidate code is
gone, and it supplies no paper or RQ3 evidence. The next step must select a
different experiment by paper-level decision value; it may reuse existing
evidence but may not repair, retag, or rename Step 0028 as another attempt.

The earlier Step 0018 AAAI/cross-domain whole-paper review scored the
then-current paper 4/10 (weak reject). It preserved the thesis and four RQs but identified
RQ2's cross-workload positive synthesis and the missing closest-profiler
comparison as the two largest scientific risks. NVIDIA NeMo Agent Toolkit must
enter Related Work, but its official profiler instruments a running
NeMo-supported workflow and exports profiler traces; it does not provide the
same-input importer required for a fair replay of current AgentSight/public
artifacts. Step 0019 has now completed the selected fixed R315 reader
comparison under a fresh single-RQ plan and independent result review. The
complete 66-presentation run supports its registered recall and precision
hypothesis against fixed-session packets, while the work rows and absent
matched raw-action packet preserve the stated boundary. Do not repeat this
packet study with a cosmetic prompt, model, cutoff, or seed. Its admitted result
has already entered the paper; the Step 0024 whole-paper/outer REVIEW direction
governed the next paper-level decision. Step 0025 changes only the recurrence
implementation frontier described above; it does not reopen this RQ2 packet
study or authorize a paper-story change.

Step 0034 completes the bidirectional percentile-calibration experiment on the
existing OSWorld-Human and CodeTraceBench populations. Operation-weighted
B-cubed precision/recall/F1 is an established hard-partition metric, and exact
boundary precision/recall/F1 is an ordinary discrete-boundary metric; the
contradiction is therefore not a metric failure. Percentile normalization
beats direct raw-cutoff transfer but loses to the current label-free recurrence
on both complete targets. This closes scalar cross-domain cutoff transfer and
all further recurrence calibration on these two observed populations.

The Step 0034 milestone review proposed reopening RQ1. Reviewer preference
alone has no such authority, but the root accepts one directly checkable
evidence finding: R114 tests source lineage and lossless folding, whereas the
R170 mixedness result uses declared prompt tags as both grouping input and
separation reference. The next candidate is therefore one fixed-RQ RQ1
same-input attribution comparison that first reuses the complete existing real
trajectories and source-linked effects, keeps target responsibility unavailable
to construction, and compares against the smallest information-equivalent
source-native and established labeled-profiler/trace-query alternatives. Its
primary outcome must be an independently defined responsible category or
decision, not another conservation, mixedness, cutoff, or presentation metric.
If the existing artifacts cannot supply that independent target, the bounded
source screen must choose an official real external asset rather than invent a
small custom harness. This evidence-status correction does not alter the thesis,
four RQs, positive RQ1 hypothesis, or reader-facing story.

Step 0035 completes that selected RQ1 comparison on the full pre-existing
CodeTraceBench source-valid target. The standard ordinary B-cubed hypothesis is
supported, the paired task-cluster interval is wholly positive, and the
resource-weighted direction is stable under all three predeclared
multi-operation token allocations. Independent review passes the result and
routes directly to WRITE. Phase-only and recurrence are statistically
indistinguishable on this stage target, so WRITE must claim semantic
stage-aligned attribution over raw action identity and rely on the separate
OSWorld result for recurrence's algorithm-specific advantage. Do not run
another RQ1 benchmark, metric, allocation, or recurrence variant before the
complete paper REVIEW chooses a genuinely different paper-level need.

Step 0036 answers the resulting RQ2 same-signal objection over all 1,756
existing trajectories and 27,346 operations. Standard per-query AP/MAP and the
secondary exact-budget Recall@20% both favor semantic organization over matched
raw action on AgentProcessBench, HINTBench, and TraceElephant, while the atomic
comparison exposes that grouping must not override stronger operation-local
evidence. Step 0037 performs the one explicitly authorized adaptive follow-up:
preserve every strict local ordering and use semantic recurrence only to refine
exact ties. It improves MAP over local-only and semantic-only ranking on all
three observed populations and over matched local-plus-raw refinement on HINT
and Trace; AgentProcessBench does not distinguish the two refinements. The
registered universal hypothesis is therefore inconclusive, but the result
supports the local-first semantic mechanism and closes all further RQ2 score,
metric, cutoff, or benchmark tuning on these populations.

The Step 0037 full-paper outer audit passes the completed experiment and write
integration but does not grant submission readiness. RQ3 is the remaining
paper-level evidence gap: the fixed hypothesis names task, phase, action, and
boundary identities, while current complete evidence lacks a literal
phase-tag measurement. The next step selects exactly one RQ3 experiment using
an existing official annotated public corpus, its complete released
population, one appropriate standard metric, and a small fair baseline set.
It may improve the mechanism or adapter but may not change the RQ, thesis,
story, or contributions. Once RQ3 closes, the paper returns to a genuinely
unprimed milestone review with primary-source novelty search.

## Experiment History Policy

Detailed plans, reviews, commands, results, and failures live in timestamped
cycle reports. This file keeps only the current RQ table, admitted results, and
next decision. Superseded plans stay linkable but never regain authority merely
because a resumed agent finds them first.
