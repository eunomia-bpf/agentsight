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
| RQ1 | Does Semantic Profiling Improve Resource Attribution? | Semantic operation stacks reunite recurring responsibility fragmented across executions and improve attribution of independently recorded additive resources while preserving source lineage and mass. | Compare flat, source-native, and one fixed semantic profile against independent tool/span/process resource identities on real traces. |
| RQ2 | Does Profiler Output Correspond to Real Problems? | A target-blind semantic profile concentrates independently annotated failures, unsafe effects, redundant work, or task boundaries and reduces analyst inspection without using target labels. | REVIEW selected one HINTBench experiment over the current official 536-record snapshot: compare a plan-defined AgentProf profile with the strongest same-information non-oracle baseline at 80% macro recall of official risky-step targets. |
| RQ3 | How Accurate Are the Tags? | A target-blind fixed tagger or mapping assigns accurate and stable task, phase, action, and boundary identities on unseen agents and task families without materially corrupting attribution. | Evaluate one approved fixed tagger or mapping on held-out real families with independent labels and downstream attribution sensitivity. |
| RQ4 | What Is the Profiling Cost? | Complete profile construction has practical predictable scaling, and cached field derivation makes repeated profile queries substantially cheaper than initial construction and repeated raw-trace review. | Measure end-to-end construction, memory, output size, and repeated-query cost across complete real workloads and scaling points. |

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

These are admitted mechanism/accounting results only. R170 records a dirty
working-tree provenance boundary; prompt tags define the declared grouping
reference; R251 has no human adequacy labels. The evidence supports mass
conservation, declared-category separation, and weighted association beyond
session membership. It does not establish correct semantic intent, causal
lineage, developer utility, or the final RQ1 answer.

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

The unexecuted revision-1 plan is superseded because it bundled roughly eleven
comparator types and several independent research programs. Its history remains
under
`docs/tmp/cycle-0001-20260711T164850-0700/01-experiment-gate/loop-rq2-01/`.

Older experiments remain under `docs/visexp/out/` with source scripts under
`docs/visexp/` and `script/`. A number returns to the paper only after its exact
input, oracle separation, baseline information, metric, and raw path are
rechecked; old readiness booleans are not evidence.

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

The AgentProcessBench score-selection frontier is closed. The completed WRITE
gate and user-requested whole-paper REVIEW are recorded in
[`WRITE 999`](tmp/cycle-0002-20260712T201943-0700/02-write-gate/999-gate-report-20260713T103942-0700.md)
and
[`review-001`](tmp/cycle-0002-20260712T201943-0700/03-review-gate/review-001/400-cycle-change-audit-final-verdict-and-routing.md).
The dedicated
[`meta-review`](tmp/cycle-0002-20260712T201943-0700/03-review-gate/800-meta-review-20260713T111135-0700.md)
retained one RQ2 experiment and corrected its RQ boundary. The first selected
source, AgentTelemetry, was rejected by the
[`outer audit`](tmp/cycle-0002-20260712T201943-0700/03-review-gate/990-independent-outer-audit-20260713T112434-0700.md)
because its accepted artifact has run/cell fault-detection outcomes but no
official step/span localization gold. A bounded
[`source repair`](tmp/cycle-0002-20260712T201943-0700/03-review-gate/review-002/200-bounded-fresh-localization-source-selection-20260713T114636-0700.md)
selected HINTBench and received an independent
[`PASS`](tmp/cycle-0002-20260712T201943-0700/03-review-gate/review-002/400-independent-source-repair-verification-20260713T120251-0700.md).

The next outer state is EXPERIMENT for fixed RQ2. Use the official
HINTBench artifact and current 536-record test snapshot: 400 risky and 136 safe
trajectories. The ordinary Markdown plan defines one target-blind profile, the
strongest same-information non-oracle comparison, and one primary decision:
atomic-step inspection work needed to reach 80% macro recall over each risky
trajectory's union of official target step IDs. Support requires a paired
work-reduction interval excluding zero while the recall target is met.

REAL PREFLIGHT must reproduce 978 annotations, 938 distinct target pairs, 935
mappable pairs, and the three absent official targets in records 170, 233, and
516. Those three remain common terminal misses for every method and are never
remapped or dropped. FULL is every current record/method/repetition cell, not
the paper/README's unavailable 629-record population. Do not add cold/warm
profiling cost or tagger-accuracy programs; whatever the sign, close this one
experiment before another paper-level choice.

## Experiment History Policy

Detailed plans, reviews, commands, results, and failures live in timestamped
cycle reports. This file keeps only the current RQ table, admitted results, and
next decision. Superseded plans stay linkable but never regain authority merely
because a resumed agent finds them first.
