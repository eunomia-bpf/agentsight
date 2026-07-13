# Experiment plan: AgentNet cross-platform step-quality localization

**Plan revision:** 3  
**Proposed:** 2026-07-13T02:46:31-07:00  
**Outer gate:** EXPERIMENT  
**Research question:** RQ2 — Does Profiler Output Correspond to Real Problems?  
**One tested hypothesis:** Across the complete scorable AgentNet Windows and
macOS held-out populations, a target-label-blind cross-run semantic AgentProf
profile will have higher operation-weighted localization AP than both a fixed
raw-action grouped profile and the ungrouped transferred-risk baseline, while
also improving recall@30 and work-to-50 over the raw-action grouped profile.

## Why this experiment has paper value

This directly supplies supporting RQ2 evidence for the original AgentProf
promise on a complete public
real-world dataset: many human desktop trajectories become profiling samples;
official semantic fields provide recurring responsibility; and independently
released step-quality annotations score whether hot groups correspond to real
quality problems. Windows and macOS differ in interfaces, applications, and
action distributions, so reciprocal held-out transfer tests whether the
profile survives a real platform shift instead of memorizing one benchmark
slice.

The experiment is materially different from ToolSafe. It studies long desktop
trajectories rather than isolated tool-safety calls, uses official step-quality
annotations rather than rule-generated safety labels, and transfers across
operating systems rather than benchmark families. It does not retune either
prior construction.

## Source and population

- Official dataset: `xlangai/AgentNet`, revision
  `d76ee50a63fad81cfdbe576416757d7c2091ed50`.
- Raw target file: `agentnet_win_mac_18k.jsonl`, expected 17,532 tasks.
- Semantic metadata: `meta_data_merged.jsonl`, expected 12,364 Windows and
  5,168 Darwin task IDs for the target file.
- Unit of observation: one released trajectory step with executable action
  code.
- Unit of dependence/bootstrap: task/trajectory, never individual steps.
- Full-run population: every raw Windows and macOS task that joins one-to-one
  to official metadata and has a nonempty trajectory. No sampling.
- Scorable population: after all predictions and profiles are saved, apply
  exactly this truth table: `incorrect OR redundant` is positive; `correct AND
  necessary` is negative; every other combination is unresolved. Exclude only
  unresolved steps, and report their count and source distribution. No label
  state participates in source conversion, prediction, profile construction,
  or group ranking.

The Ubuntu 1,000-task prefix previously used in R291 is development history,
not a target. No result from it enters the confirmatory metric.

## Reciprocal held-out folds

1. **Windows → macOS:** fit the fixed visible-feature step-risk model on all
   scorable Windows tasks; generate and save every macOS prediction and every
   AgentProf view before loading macOS labels into the scorer.
2. **macOS → Windows:** fit on all scorable macOS tasks; generate and save every
   Windows prediction and every AgentProf view before loading Windows labels
   into the scorer.

Reference-platform labels are training data for that fold. Held-out-platform
labels are scoring data only. The two folds are evaluated separately because
their independently fitted probability scales are not assumed calibrated to
one another. No pooled cross-model ranking participates in the verdict.

## Visible projection and prohibited information

The pre-label projection may contain only source identity, task ID, operating
system, official domain/application names, original action code, and the fixed
visible features below. Missing application names map to `none`. Raw source
case is preserved in the source projection; normalized predictor fields are
stored separately.

The complete risk-model feature list is fixed before Windows/macOS labels are
inspected:

- categorical: normalized domain, normalized sorted application-list string,
  action, target bucket, phase, repetition state, trajectory-level repetition
  signal, repetition-run bucket, previous action (`start` on step zero), and
  whether the action changed from the preceding step;
- numeric: zero-based step index divided by `max(1, trajectory_length - 1)` and
  `log1p(trajectory_length)`.

Action, target, phase, and repetition fields reuse only four pure helpers from
the already-published Ubuntu development rules in
`script/agent_trace_datasets.py`: `agentnet_code_action`,
`agentnet_action_target`, `agentnet_action_phase`, and
`repeat_features_for_signatures`. The experiment must not call
`normalize_agentnet()` or pass its output to either the predictor or AgentProf,
because that adapter also emits the forbidden step labels, task-completion
status, and post-hoc scores.

The four pure helpers are fixed without modification:

- action is the first `pyautogui.<function>` or `computer.<function>` name,
  normalized by the existing aliases (`write`/`typewrite`→`type`,
  `moveTo`→`move_to`, `dragTo`/`dragRel`→`drag`, and click aliases);
- target is the existing 100-pixel coordinate bucket for pointer actions, the
  first four exact key tokens for keyboard actions, `text` for typing,
  `scroll` for scrolling, `none` for observation/wait, or the explicit
  termination status;
- phase is exactly `agentnet_action_phase(action)`: `terminate` maps to
  `finish`; every other action uses the unmodified `osworld_action_phase`
  result, including its possible `input`, `navigate`, `observe`, `fail`,
  `system`, or `desktop-action` values;
- repetition state and run use the existing preceding-five-step signature
  rules over `(action,target)`; the trajectory signal is `loop-like` exactly
  when those fixed rules observe a same-signature run/window or repeated target
  at their existing thresholds.

These rules were developed on the old Ubuntu path and are therefore declared
development provenance. They cannot be changed after any Windows/macOS label or
metric is read.

### Physical label boundary

`prepare` is the only stage allowed to read the raw official trajectory file.
It writes one ordinary `projection.jsonl` containing only allowed visible
fields and two separate label files, `labels/windows.jsonl` and
`labels/darwin.jsonl`. It also writes a Markdown source/join report. The raw
file, source directory, and target-label path are not valid predictor inputs.

Each fold runs a predictor subprocess whose complete inputs are the visible
projection, exactly one reference-platform label file, the reference and target
platform names, fixed settings, and an output directory. It cannot receive the
raw file, source root, or target label. Before scoring, a label-blind stage
saves every target prediction, every view's group key, operation count and risk
sum, and all deterministic bootstrap task-ID draws. Only a later scorer
subprocess receives those saved artifacts plus the held-out platform label
file. The implementation test must demonstrate that swapping or withholding
the target-label path cannot change predictions, group artifacts, or draws.

The predictor and AgentProf input must exclude:

- `last_step_correct` and `last_step_redundant` on the held-out platform;
- reflection, thought, generated observation, and reflector explanations;
- task completion, reason, alignment score, efficiency score, and difficulty;
- synthesized `natural_language_task` and `actual_task`;
- metadata complexity flags, verification feedback, task-description scores,
  action entropy, and action-frequency summaries;
- any field, threshold, mapping, or feature selected after inspecting a
  held-out label or held-out metric.

The original task instruction is not needed by Revision 1 and remains excluded
to keep the tested construction simple. A later experiment may test learned
intent attribution, but this experiment tests the released semantic metadata
plus visible action structure.

## Fixed risk model

Use one standard scikit-learn pipeline and the exact feature list above in both
folds:

- categorical one-hot encoding with unknown categories ignored;
- numeric standardization for step-position and run-length features;
- logistic regression with fixed `C=1`, L2 penalty, class weighting balanced,
  deterministic seed 4204, and no hyperparameter search;
- exactly the same allowed feature list and settings in both directions.

The model is a shared target-blind signal, not a paper contribution. Its raw
held-out step AP is reported as a strong ungrouped baseline. No view receives a
different classifier or feature set.

## AgentProf views

Real `agentpprof 0.2.37` must construct every grouped view from the same
held-out visible operations and precomputed risk values. Independent counters
must match its operation and folded-weight totals.

1. **flat:** one target-platform group;
2. **fixed session:** one group per task/session;
3. **source native:** system → domain → application → session → action;
4. **raw action:** action → exact target bucket → repetition state;
5. **exact-repeat control:** individual steps ordered only by the fixed visible
   repeat indicator, with complete tie blocks;
6. **semantic operation stack (tested):** domain → application → phase → action
   → repetition state, explicitly omitting session so recurring work folds
   across trajectories;
7. **ungrouped transferred risk (fixed strongest localization baseline):**
   individual steps ordered by the shared transferred risk.

The fixed strongest grouped alternative is the raw-action view. Flat,
fixed-session, source-native, and exact-repeat are required controls; they are
never selected dynamically from target results.

For every grouped view, the primary group score is predicted problem density:
the sum of full-precision transferred step risks divided by operation count.
All groups with exactly equal density form one complete tie block in AP,
recall@30, and work-to-50; risk mass and group label may order display rows but
may not break a primary-metric tie. Additive risk-mass ranking is secondary and
answers only a per-group-opening cost question.

Because AgentProf operation values are unsigned integers, AgentProf constructs
and verifies the stack/count profiles only. The scorer aggregates saved
full-precision predictions by the exact emitted stack keys, verifies that every
operation belongs to one group and that total reconstructed risk equals the
saved prediction sum within floating-point tolerance, and then computes
density. The plan does not claim that AgentProf directly stores floating-point
risk values.

## Primary and secondary measurements

Primary metrics, computed with conservative tie handling over held-out steps:

- operation-weighted average precision after group ranking;
- recall at 30% inspected operations;
- operation work required to reach 50% of positives.

Secondary diagnostic measurements:

- groups and groups-to-50%-positives;
- sessions represented per hot group;
- raw step-risk AP and exact-repeat AP;
- annotation coverage and positive prevalence;
- per-domain results for domains with enough scorable tasks, reported only as
  disaggregation rather than separate verdicts;
- profile counter and predicted-risk mass conservation.

Fit each reciprocal-fold model once on the complete reference platform. Then
use 10,000 paired task-cluster bootstrap draws over that fold's held-out
platform; all views share the identical task draw. If a draw has no positive or
no negative, drop the entire paired draw. Attempt at most 50,000 deterministic
draws per fold to obtain 10,000 valid draws. Fewer than 10,000 valid draws in
either fold is an incomplete execution, not a scientific negative. Report
percentile 95% intervals separately for Windows→macOS and macOS→Windows; never
refresh the seed or draws in response to the result.

An equal-weight mean of the two within-fold metric differences may be reported
as a secondary stratified summary. Raw predictions from the two independently
trained models are never concatenated and ranked together, and no pooled
interval participates in `SUPPORTED`, `CONTRADICTED`, or `MIXED`.

## Predeclared comparison and verdict

There are exactly two fixed primary comparisons:

1. semantic operation stack versus raw-action grouped profile, which tests
   whether semantic cross-run responsibility improves on a non-semantic
   grouping under the same predictor;
2. semantic operation stack versus ungrouped transferred risk, which tests
   whether grouping adds localization value rather than merely visualizing a
   classifier.

Flat, fixed-session, source-native, and exact-repeat results are mandatory
controls and disaggregations. No target metric chooses a comparator.

- **SUPPORTED:** in each of the two held-out folds independently,
  semantic-minus-raw-action AP and recall@30 intervals are entirely above zero,
  raw-action-minus-semantic work-to-50 is entirely above zero, and
  semantic-minus-ungrouped-risk AP is entirely above zero.
- **CONTRADICTED:** execution is complete and valid, and either (a) both held-out
  platforms favor raw action on AP and work-to-50, or (b) one platform has a
  confidence interval excluding zero in the adverse direction for semantic AP
  against raw action or ungrouped transferred risk.
- **MIXED:** every other valid result, including a useful compression/accuracy
  tradeoff without the full predeclared localization win.

Execution status is reported separately. A source identity, one-to-one join,
label-separation, feature-exclusion, full-population, counter-conservation, or
bootstrap failure makes the execution `INVALID` or `INCOMPLETE`; it cannot
produce a `CONTRADICTED` scientific verdict.

The verdict answers only this tested construction. It cannot change RQ2, the
paper thesis, the four-RQ architecture, or the canonical story. A valid
non-supporting result remains internal and routes to a materially different
experiment; it does not authorize tuning on held-out Windows/macOS labels.

## Serial review, real preflight, and full execution

1. Review this plan serially at least three and at most five times with an
   independent subagent explicitly applying `research-experiment-design`.
2. Each review checks scientific question, real source, label provenance,
   strongest baseline, metric/uncertainty, leakage, executability, and whether
   the experiment is large and simple enough to affect the paper.
3. Revise after every `REVISE`; approval requires a final `PASS`, not zero
   possible objections.
4. Implement only after plan approval.
5. REAL PREFLIGHT runs the entire end-to-end pipeline on a fixed small set of
   reference tasks plus a fixed small held-out subset, solely to find schema,
   runtime, label-separation, and counter bugs. It cannot authorize a scientific
   result or tune a feature.
6. An independent preflight review must authorize the full run.
7. FULL RUN downloads/streams and processes every planned Windows/macOS task,
   completes all profiles and 10,000 bootstrap draws, and does not stop after a
   successful smoke or favorable partial result.
8. Independent result review recomputes the primary comparison from saved
   outputs and routes the next experiment without editing the paper.

The complete commands are predeclared as:

```bash
python3 script/agentnet_cross_platform_eval.py prepare \
  --revision d76ee50a63fad81cfdbe576416757d7c2091ed50 \
  --out docs/visexp/out/agentnet-rq2/source

python3 script/agentnet_cross_platform_eval.py preflight \
  --source docs/visexp/out/agentnet-rq2/source \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --out docs/visexp/out/agentnet-rq2/preflight \
  --bootstraps 200 --max-bootstrap-attempts 1000 --seed 4204

python3 script/agentnet_cross_platform_eval.py full \
  --source docs/visexp/out/agentnet-rq2/source \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --out docs/visexp/out/agentnet-rq2/full \
  --bootstraps 10000 --max-bootstrap-attempts 50000 --seed 4204
```

Expected environment is Python 3.12, scikit-learn 1.4.1, NumPy 1.26.4,
SciPy 1.11.4, and AgentProf 0.2.37. The full source is 1.42 GB; reserve at
least 20 GB free disk and six wall-clock hours. Terminal completion requires:
the two official source checksums; exactly 12,364 Windows and 5,168 Darwin
metadata tasks; one-to-one raw/metadata task IDs; saved predictions for every
held-out operation before held-out label access; exact AgentProf/source counts
for every view; risk-mass reconstruction; 10,000 valid paired draws; both fold
reports; optional stratified-effect report; and no stale partial-run status.

## Expected artifacts

- source metadata and checksums under `docs/visexp/out/agentnet-rq2/source/`;
- preflight outputs under `docs/visexp/out/agentnet-rq2/preflight/`;
- complete outputs under `docs/visexp/out/agentnet-rq2/full/`;
- one orchestration/scoring driver under `script/`, with real AgentProf,
  scikit-learn, and official dataset files doing the scientific work;
- detailed Markdown plan reviews, preflight report/review, full-run report, and
  result review under this loop directory.

No paper file, submodule file, shared skill, RQ, thesis, or story is modified by
this experiment loop.
