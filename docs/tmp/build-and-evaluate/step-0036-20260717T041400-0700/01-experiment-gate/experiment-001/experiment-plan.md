# Experiment Plan: RQ2 Same-Signal Diagnostic Decomposition

**Proposed:** 2026-07-17T04:14:00-07:00
**Outer gate:** `EXPERIMENT_GATE`
**Skill:** `research-experiment-design`
**Planned role:** decisive
**Mode:** reuse and reanalysis of complete retained artifacts

## Research Question

- **RQ exactly as written in the paper:** **RQ2: Does profiler output
  correspond to real problems?**
- **Fixed RQ2 hypothesis from project memory:** A fixed semantic profile should
  concentrate independently annotated failures, unsafe effects, redundant
  work, or task boundaries and reduce inspection versus flat, per-session,
  native, and raw-action views without using target labels.
- **Specific uncertainty tested here:** Holding each benchmark's already
  generated diagnostic signal fixed, does current AgentProf operation-stack
  organization recover independently annotated target operations at a fixed
  operation-inspection budget better than matched raw-action organization,
  without increasing alarm propagation on target-free trajectories?
- **Why the answer matters:** Existing MAP results show a consistent AgentProf
  advantage over raw-action grouping, but they omit official signal quality,
  fixed operation work, atomic/session controls in the paper table, and clean
  false positives. Without this decomposition, the gain can be explained by
  the external localizer, unequal work, or propagation of a hit across many
  clean operations rather than by useful semantic organization.

This experiment tests one hypothesis inside unchanged RQ2. It does not answer
the entire RQ, change the four RQs, or authorize a thesis or story rewrite.

## Paper-Value Admission

- **Planned role:** decisive.
- **Largest credible paper story this experiment could unlock:** Given exactly
  the same target-blind diagnostic evidence, an operation stack changes the
  developer's fixed-budget inspection decision by concentrating real failures
  in semantically responsible regions, rather than merely reformatting or
  smoothing the evidence.
- **Strongest reviewer reject argument addressed:** AgentProf is only a pprof
  converter/group-by layer over known components, and its RQ2 gain may arise
  from external signal quality, label spreading, or unequal inspection work.
- **Independent evidence beyond existing runs:** The complete raw predictions
  and grouping artifacts already exist, but the current paper does not report
  official source-task quality, standard Recall@fixed-budget, clean-trajectory
  false positives, or a same-table atomic/session decomposition. Consolidating
  them changes the scientific interpretation without collecting another model
  sample.
- **Why the result is not tautological or already settled:** Group averaging or
  Wilson scoring can either concentrate sparse true hits or spread false hits.
  Existing MAP on target-bearing queries cannot distinguish those mechanisms,
  and atomic scoring already beats AgentProf on AgentProcessBench MAP.
- **Paper decision if positive:** Retain the original thesis and RQ2, and make
  the fixed-information, fixed-work diagnostic consequence the main RQ2
  evidence and a central novelty discriminator.
- **Paper decision if contradictory:** Retain the thesis and RQ2, record that
  the current operation-stack mechanism does not improve this diagnostic
  decision, and route later mechanism improvement through the existing
  trajectories rather than claiming that current MAP closes RQ2.
- **Paper decision if mixed:** Report exactly which workloads benefit and
  whether the boundary is atomic-signal quality, grouping, fixed work, or clean
  propagation. Do not weaken the RQ or hide a losing baseline.
- **Best alternative experiment:** Add recurrence segmentation baselines or
  refine recurrence on OSWorld-Human/CodeTraceBench. That work remains
  necessary, but both populations already influenced constructor development;
  another constructor variant has less immediate probability of changing the
  current AAAI verdict than isolating the missing diagnostic consequence.

## Expected And Alternative Outcomes

- **Current expected answer:** AgentProf should outperform raw-action grouping
  on trajectory MAP and tie-averaged expected Recall@20%-of-operations across all three retained
  workloads. It may not beat the atomic signal on AgentProcessBench, where the
  existing atomic MAP is higher. Clean alarm/support propagation is genuinely
  unresolved and may make the overall result mixed.
- **Strongest competing explanation:** Semantic groups improve target-bearing
  MAP only by broadcasting a positive localizer/judge signal to more operations
  in the same group, increasing clean alarms or consuming more fixed-budget
  work; atomic or raw-action ranking is then the more useful decision rule.
- **Result that contradicts the expectation:** AgentProf fails to improve
  tie-averaged expected Recall@20% over raw action on at least two complete
  workloads, or its apparent recall benefit coincides with materially greater
  project-defined support propagation onto clean trajectories.
- **Paper-impact classification of a contradiction:** mechanism/workload
  boundary within RQ2, not a direct challenge to the profiling thesis.

## Published Precedent And Real Assets

### AgentProcessBench

- **Official benchmark:** KDD 2026 AgentProcessBench, official repository commit
  `0a42606b178a8c69d40c5765dc05c342f921e578`.
- **Official metrics:** Step Accuracy (`StepAcc`) and first-error accuracy
  (`FirstErrAcc`) from `eval/compare.py`; the source evaluator's step-exact
  accuracy is secondary because the paper names StepAcc and FirstErrAcc as its
  two primary measures.
- **Retained population:** all 1,000 trajectories and 8,509 assistant-step
  operations across BFCL, GAIA-dev, HotpotQA, and Tau2; 614 trajectories contain
  at least one harmful target and 386 are clean.
- **Fixed signal:** all 20 released judge predictions, represented in the
  AgentProf comparison by the already retained fraction of harmful (`-1`) votes
  per operation. This fraction is an existing project aggregation, not an
  official AgentProcessBench predictor. The official evaluator will separately
  report the 20 constituent judges' official metrics; no new plurality labeler
  or model prediction will be invented.
- **Retained artifacts:** `docs/visexp/out/agentprocessbench-rq2/full/` and its
  downloaded official source repository.

### HINTBench

- **Official benchmark:** HINTBench test snapshot of 536 trajectories, SHA-256
  `87b33d3941be49cc40e6b38e1faec3cb420fd3483369eff68821e43a4db62e44`.
- **Official evaluator:** downloaded `evaluate.py`, SHA-256
  `ab7bcfc70d6cb45fe91c8020a61754312c9fb7e6a8cb909fb260aab76236ab80`.
- **Published metrics used:** risk-detection Accuracy/Macro-F1 (with Safe-F1
  and Unsafe-F1), standard risk-step set precision/recall/F1, and the paper's
  no-type one-to-one overlap localization recall/F1.
- **Retained population:** all 536 test trajectories and 12,877 scored agent
  operations; 400 trajectories contain mapped targets and 136 are clean.
- **Fixed signal:** the existing complete Qwen3.6-27B official-prompt outputs;
  no model inference or field-order selection is rerun.
- **Retained artifacts:**
  `docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full/`.

**Real-preflight asset deviation.** The downloaded 536-record test snapshot
stores gold localization under `risk_labels` using a five-constraint taxonomy,
while the downloaded evaluator with the recorded hash reads only
`injected_risks` and its retained prompt/parser uses eleven fine-grained names.
Calling it without adaptation therefore produces a spurious zero localization
score. The experiment uses the unchanged official function for binary
detection, then applies the paper's published no-type maximum one-to-one step-
overlap protocol directly to the released `risk_labels` steps. It does not
invent a cross-taxonomy type map and therefore reports typed localization and
strict typed-set accuracy as `N/A`. The adapter must reproduce all 536 retained
parse statuses and step sets before scoring.

### TraceElephant

- **Official benchmark/source:** TraceElephant repository commit
  `0ce8abb2855de9f454f27f6b0795a4b7e6c8d5fc`.
- **Official metrics:** agent accuracy and step accuracy from
  `code/trace_locate/evaluate.py`. Exact normalized joint agent-and-step
  accuracy is a declared secondary metric. No tolerance metric is added because
  the retained official evaluator does not define one.
- **Retained population:** all 220 released failure trajectories and 5,960
  operations across five agent-system/task cells. The benchmark has no clean
  population, so clean false positives are `N/A` rather than inferred.
- **Fixed signal:** existing Qwen3.6-27B All-at-Once localizer predictions. They
  are reference-assisted because the prompt may contain task answers or test
  outcomes, but they do not contain `mistake_agent` or `mistake_step` labels.
- **Retained artifacts:** `.agentsight/experiments/traceelephant-rq2-v1/`.

### Standard cross-benchmark protocol

- Non-interpolated AP per target-bearing trajectory and arithmetic MAP use
  `sklearn.metrics.average_precision_score`.
- Pooled operation AP remains a standard secondary result that includes clean
  operations, but does not replace the separate clean-signal and propagation
  controls.
- Recall@20% is the single fixed-budget metric: for each target-bearing
  trajectory, inspect exactly `ceil(0.20 * n_operations)` operations ordered by
  score. When the cutoff intersects an equal-score tier, the primary value is
  the analytic expected recall under a uniform ordering of that cutoff tier.
  Report the cutoff-tier size and its attainable best/worst recall bounds; an
  immutable source-order result is only an operational sensitivity. This
  prevents giant atomic/session ties from being decided by arbitrary row order
  while preserving exactly the same operation budget. Report macro mean target
  recall and the exact inspected-operation numerator/denominator. The 20%
  choice is predeclared for this consolidation, but the retained artifacts have
  been analyzed before; this is a transparent post-hoc reanalysis, not an
  untouched protocol.
- Clean behavior has two explicitly separate layers. First, report the fixed
  external signal's own official or source-native clean error: each of the 20
  AgentProcessBench judges is evaluated separately on human-clean trajectories,
  and HINTBench uses its official safe/unsafe confusion matrix. Second, report
  **project-defined support-propagation controls** after organization: the
  fraction of clean trajectories and clean operations that receive support
  above the predeclared project operating point. For the already retained
  AgentProcessBench harmful-vote fraction, the point is `> 0.5`; for HINTBench,
  nonzero atomic/Wilson support is `> 0`. These controls reveal propagation but
  are not called official, native, or benchmark-defined FPRs.

Necessary custom code is limited to a read-only analysis extension around the
existing `script/rq2_standard_localization_metrics.py`. Official evaluator
functions are invoked where available; the adapter performs joins, matched-view
ranking, bootstrapping, and report serialization only.

## Comparison

### Proposed method

- Current AgentProf operation-stack organization and its already materialized
  scores. No stack fields, score, cutoff, localizer, or tagger changes.

### Main baselines

1. **Raw-action grouping — strongest matched simple organization.** It tests
   the competing view that source-visible action identity is sufficient. A
   matched run is necessary because the same predictions must be redistributed
   over exactly the same operations.
2. **Atomic operation signal — strongest no-propagation alternative.** It tests
   whether semantic grouping adds value beyond directly sorting the external
   judge/localizer scores. It is already stronger on AgentProcessBench MAP and
   therefore cannot be omitted.

### Control

- **Whole-session grouping — coarse null/control.** It tests whether any
  within-trajectory discrimination is necessary. It is not counted as a main
  baseline or independent contribution.

### Decision if a baseline wins

- Raw action matching or winning means the semantic hierarchy has not improved
  this decision beyond visible action identity on that workload.
- Atomic matching or winning means the profile has not added value beyond the
  fixed diagnostic signal and may be diluting it through propagation.
- Session matching or winning means the workload/signal does not reward the
  claimed within-trajectory semantic localization mechanism.

### Fairness and leakage

- Every view receives the same per-operation retained signal and operation
  population.
- Human/benchmark targets are read only by the evaluator, not by group
  construction or scoring.
- HINT's validation-selected operation-stack field order remains unchanged.
- No benchmark, model, prompt, prediction, group, score, or cutoff is tuned in
  this analysis.
- Metrics are reported per complete benchmark; no favorable workload, agent
  family, clean trajectory, or tied score tier is removed.

## Workloads And Metrics

### Primary organizational metrics

For each benchmark and each view:

1. trajectory MAP over all target-bearing trajectories;
2. macro tie-averaged expected target Recall@20% operations, with cutoff-tier
   best/worst bounds.

The primary matched comparisons are AgentProf minus raw action and AgentProf
minus atomic. Session is a control. Each benchmark is interpreted separately;
the three workloads are not treated as three iid samples for a cross-benchmark
p-value.

### Clean-behavior controls

- external-signal clean error using each benchmark's official/source-native
  prediction semantics; and
- project-defined clean-trajectory support rate plus clean-operation support
  rate after each organization view at the predeclared operating points above.

These are necessary mechanism controls and may veto a broad “without extra
clean alarms” interpretation. They are not relabeled as official benchmark
metrics.

### External-signal metrics

- AgentProcessBench: official StepAcc and FirstErrAcc for each of the 20 fixed
  released judges; report distribution/summary without inventing an ensemble
  labeler.
- HINTBench: source-native risk Accuracy/Macro-F1/Safe-F1/Unsafe-F1, standard
  risk-step set F1, and published no-type overlap localization Recall/F1 for the
  retained localizer. Typed and strict metrics are `N/A` under the recorded
  official asset mismatch rather than reported as false zeros.
- TraceElephant: official agent accuracy and step accuracy, plus exact joint
  accuracy as secondary.

These metrics describe the fixed signal once. They are identical across
organization views and are not credited to AgentProf.

### Secondary metrics and checks

- pooled operation AP;
- source/mapped-target coverage sensitivity for HINTBench's three unmapped
  target steps;
- exact equality of source operations, labels, and retained scores across all
  methods;
- complete population counts and per-view score coverage; and
- 10,000 paired trajectory-cluster bootstrap draws for MAP and tie-averaged
  expected Recall@20% differences, with AgentProcessBench sampled by task within
  family and the other workloads by complete trajectory within published
  strata/cells.

No Work@50, Work@80, additional cutoff sweep, new reader study, new clustering
metric, or new localizer metric is admitted as a primary result.

## Planned Runs

| Run group | Role | Workload | Method/view | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| official-signal | context | AgentProcessBench | 20 retained released judges, official evaluator | deterministic | Establish signal quality; not an AgentProf comparison |
| official-signal | context | HINTBench | retained Qwen output, source-native detector plus published no-type overlap protocol | deterministic | Establish risk/localization quality and clean verdict behavior without inventing a taxonomy map |
| official-signal | context | TraceElephant | retained Qwen output, official evaluator | deterministic | Establish agent/step localization quality |
| matched-main | proposed | all three | current operation stack | deterministic + 10,000 bootstrap draws | Test fixed-signal semantic organization |
| matched-main | baseline | all three | raw action | deterministic + paired draws | Test visible-action sufficiency |
| matched-main | baseline | all three | atomic | deterministic + paired draws | Test no-propagation sufficiency |
| matched-control | control | all three | session | deterministic | Test coarse no-localization behavior |

## Execution

- **Authoritative workflow:** Reuse the three complete artifact roots and call
  the downloaded official evaluators where their source fields match. For the
  recorded HINT localization mismatch, reuse the paper's published no-type
  overlap definition over released target steps. Extend the existing standard-
  metric script only for this necessary adapter plus the missing matched fixed-
  budget and clean analyses.
- **Real preflight case:** Run the complete adapter and official-metric path on
  one real target-bearing and one real clean AgentProcessBench trajectory, one
  real target-bearing and one real clean HINTBench trajectory, and one real
  TraceElephant trajectory. This is one end-to-end preflight invocation, not a
  scientific result.
- **Planned command:**

  ```bash
  python script/rq2_same_signal_diagnostic_decomposition.py full \
    --agentprocess-root docs/visexp/out/agentprocessbench-rq2/full \
    --hint-root docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full \
    --trace-root .agentsight/experiments/traceelephant-rq2-v1 \
    --bootstraps 10000 --seed 20260717 \
    --out .agentsight/experiments/rq2-same-signal-diagnostic-decomposition-v1/full
  ```

- **Full completion rule:** All 1,756 trajectories and 27,346 operations are
  terminal; all four views have exact score coverage; official signal metrics,
  per-query MAP and tie-averaged expected Recall@20% with cutoff-tier bounds,
  clean-signal and propagation controls where applicable, and all 10,000 paired
  draws are present; no planned workload or negative/clean row is omitted.
- **Raw-result path:**
  `.agentsight/experiments/rq2-same-signal-diagnostic-decomposition-v1/full/`.
- **Preflight path:**
  `.agentsight/experiments/rq2-same-signal-diagnostic-decomposition-v1/preflight/`.
- **Recovery:** Inputs are immutable retained outputs; the deterministic
  analysis can restart from them. Bootstrap draws use fixed seed `20260717`.

## Interpretation

### Positive

AgentProf improves MAP and tie-averaged expected Recall@20% relative to raw
action with positive paired effects on the complete workloads, and the clean
support-propagation controls do not reveal a material alarm-spreading cost.
Atomic comparison shows where semantic propagation adds or loses value. This
supplies direct additional RQ2 evidence and a fixed-information, fixed-work
decision consequence.

### Contradictory

AgentProf loses fixed-budget recall on most workloads or produces materially
more clean alerts. The result remains valid and bounds the current grouping/
scoring mechanism. It does not change the thesis, RQ2, or original story; the
orchestrator decides whether an existing-trajectory mechanism improvement now
outranks other paper work.

### Mixed or inconclusive

Report all workloads and separate: external signal quality, target-bearing
ranking, fixed-budget recall, clean alarm propagation, and atomic/raw/session
comparisons. Do not collapse a mixed mechanism result into a broad positive or
negative RQ answer.

### Target paper artifact

One compact RQ2 table that reports, per benchmark, official signal quality once
and the standard matched organization results for AgentProf, raw action,
atomic, and session. If page pressure prevents all cells in the main paper,
retain official primary metrics, AgentProf/raw/atomic fixed-budget results, and
clean behavior in the seven-page body; move only secondary pooled AP and full
interval details to supplementary material.

## Reproducibility Notes

- AgentProcessBench source commit:
  `0a42606b178a8c69d40c5765dc05c342f921e578`.
- TraceElephant source commit:
  `0ce8abb2855de9f454f27f6b0795a4b7e6c8d5fc`.
- HINTBench test/evaluator hashes are recorded above.
- Existing profile artifacts use `agentpprof 0.2.37` where recorded; no
  profiling command is rerun.
- Standard MAP/AP use the installed scikit-learn implementation already used
  by the complete Step 0033 reanalysis.
- Fixed seed: `20260717`; paired bootstrap repetitions: `10,000`.
- Known limitation: all three populations and their existing curves have been
  inspected previously. This is a complete matched reanalysis, not an untouched
  generalization test.
