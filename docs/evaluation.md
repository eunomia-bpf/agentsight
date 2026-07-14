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
| RQ1 | Does Semantic Profiling Improve Resource Attribution? | Semantic operation stacks reunite recurring responsibility fragmented across executions and improve attribution of independently recorded additive resources while preserving source lineage and mass. | **Evidence-backed paper-level answer.** R114 supplies scoped source-lineage correctness under concurrent controls; current AgentProf preserves every selected row and the mass of all five known task categories. R170/R224/R251 supply cross-run semantic separation, multi-weight, and beyond-session evidence. Do not run another RQ1 lineage or grouping variant; WRITE the cumulative positive answer and let REVIEW select the next fixed RQ. |
| RQ2 | Does Profiler Output Correspond to Real Problems? | A target-blind semantic profile concentrates independently annotated failures, unsafe effects, redundant work, or task boundaries and reduces analyst inspection without using target labels. | **Evidence-backed paper-level answer.** AgentProcessBench provides significant target-blind AP concentration beyond matched refinement; HINTBench and TraceElephant add favorable inspection regions on independent public workloads. High-recall tail efficiency depends on ranking and tie structure. Do not open another RQ2 score or benchmark variant; WRITE the cumulative positive answer and let REVIEW select another fixed RQ. |
| RQ3 | How Accurate Are the Tags? | A target-blind fixed tagger or mapping assigns accurate and stable task, phase, action, and boundary identities on unseen agents and task families without materially corrupting attribution. | **Positive partial answer, strengthened.** Step 0006 supports supervised group-boundary identity on 287 session-held-out OSWorld-Human tasks. Step 0008 adds target-blind task-partition evidence on Mind2Web and 100 ScienceWorld sessions, with V-measure 0.5565 and 0.8151 at full coverage versus 0 for a constant control. Action evidence is mixed across a tiny AndroidControl prefix and complete GUI-Odyssey prefix; phase and broad action stability remain open. WRITE the positive task result; REVIEW must preserve the fixed hypothesis and select only a materially better next mechanism if more RQ3 evidence is needed. |
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

## Experiment History Policy

Detailed plans, reviews, commands, results, and failures live in timestamped
cycle reports. This file keeps only the current RQ table, admitted results, and
next decision. Superseded plans stay linkable but never regain authority merely
because a resumed agent finds them first.
