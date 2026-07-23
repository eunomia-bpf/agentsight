# Experiment Plan: RQ2 Recursive Differential Operation Profile

## Research Question

- **RQ exactly as written in the paper:** Does profiler output correspond to
  real problems?
- **Specific uncertainty tested here:** Can one outcome-blind automatic Agent
  annotation organize the complete AgentRewardBench mixed-outcome population
  into a shared recursive operation hierarchy whose recovery-path exposure
  corresponds to the benchmark's separately collected expert looping label,
  and whose signed bad-minus-good pprof localizes the responsible work while
  retaining source LLM/tool evidence?
- **Why the answer matters:** The retained differential profile covers the
  complete population but uses a fixed six-field classification chain. Its
  paper screenshots are wide, uniformly deep, and fragmented by concrete task
  strings. They expose aggregate counts but do not yet demonstrate the same
  task-decomposition and recursive drilldown that the long-horizon case now
  provides.

## Paper-Value Admission

- **Planned role:** supporting RQ2 evidence and the second end-to-end product
  case.
- **Largest credible paper story this experiment could unlock:** AgentPProf can
  compare hundreds of successful and failed executions of the same tasks as one
  conventional differential profile and expose where failed agents repeat work
  and where successful agents reach completion.
- **Strongest reject argument addressed:** The current differential result may
  be a post-hoc taxonomy table rendered as a flame graph rather than a useful
  profiler hierarchy.
- **Independent evidence added:** A source-only automatic Agent annotation over
  all 440 real trajectories, applied before any expert label enters the
  construction. The benchmark's consensus looping label is an independent
  trajectory-level RQ2 target. Success labels enter only afterward to form the
  already fixed 338 bad--good pair occurrences and their signed weights.
- **Why this is not tautological or settled:** The existing result fields
  mechanically identify exact repetition and terminal actions, but they do not
  establish that shared recursive task responsibilities can aggregate those
  events into a readable profile with source drilldown.
- **Paper decision if positive:** Use the independently validated recursive
  differential pprof and its focused views as Case Study 2; retain the existing
  aggregate counts as supporting measurements.
- **Paper decision if contradictory, mixed, or inconclusive:** Keep the valid
  signed aggregate result but do not claim a useful recursive task profile;
  repair the annotation or projection rather than changing RQ2 or the paper
  thesis.
- **Best alternative experiment:** Running another RQ2 benchmark score. It has
  lower decision value because three complete standard-MAP workloads already
  exist, while the second product case is visibly inconsistent with the new
  recursive workspace.

## Expected And Alternative Outcomes

- **Expected answer:** Exposure under the canonical operation
  `recover from failed or repeated interaction` will have average precision
  above expert-looping prevalence. In the signed profile, failed-side excess
  will concentrate under recurring navigation/search/recovery responsibilities
  and their repeated tool actions; successful-side excess will concentrate
  under verification, completion, and user-report responsibilities.
- **Strongest competing explanation:** The differential signal is fully
  explained by the leaf-level `repeated`, `terminal`, and `conclusion` fields;
  recursive semantic parents add no readable localization or cross-session
  aggregation.
- **Contradictory result:** Recovery-path exposure does not exceed expert-label
  prevalence, or the operation hierarchy remains dominated by concrete task
  strings, uniform field chains, or single-operation leaves and cannot locate a
  shared parent responsibility without reading hidden outcome.

## Published Precedent And Real Assets

- **Closest published protocol:** Differential Flame Graphs
  (SANER 2015, DOI `10.1109/SANER.2015.7081872`) for a signed
  candidate-minus-baseline profile; AgentRewardBench
  (COLM 2025, arXiv `2504.08942`) for expert-reviewed trajectory success and
  looping labels; ordinary non-interpolated average precision for the binary
  trajectory ranking, matching the paper's existing RQ2 AP/MAP protocol; and
  the installed Go pprof for focus and source-label drilldown.
- **Official/real assets:** All 440 eligible real AgentRewardBench trajectories,
  125 mixed-outcome tasks, and the fixed 338 bad--good pair occurrences already
  independently reconstructed in Step 0067.
- **Reused:** Original goals, reasoning, actions, tool state, token counts,
  source IDs, pair population, and signed operation-count weighting.
- **Necessary custom glue:** A source adapter materializes the three-file
  annotation workspace and converts its CLI-derived paths into the existing
  normalized operation/difference input. It does not infer semantic boundaries
  or read outcome labels during annotation.

## Comparison

- **Proposed method:** Outcome-blind automatic Agent annotations using the
  shared `tag/parent/next` workspace, followed by the existing signed pprof
  construction.
- **Main baseline:** A fresh replay of the current fixed
  `task -> subtask -> strategy -> action -> object -> result` profile over the
  identical 338 pair occurrences.
- **Controls:** (1) the expert-looping prevalence lower bound; (2) the existing
  exact repeated/error leaf exposure per trajectory, scored by the same average
  precision protocol; and (3) a leaf-only result/action focus over the same
  signed samples, testing whether recursive parents add localization beyond the
  already visible repetition and terminal fields.
- **Conclusion if the baseline matches or wins:** Preserve its quantitative
  counts and reject the recursive figure as decoration.
- **Fairness:** Both views contain the same pair occurrences, source sessions,
  operation counts, outcome-side weights, and evidence IDs. The annotation
  backend never receives success, failure, pair side, or expert labels.

## Workloads And Metrics

- **Real workload:** Complete fixed AgentRewardBench mixed-outcome population:
  440 trajectories, 125 tasks, 338 bad--good pair occurrences.
- **Independent RQ2 target:** The consensus expert
  `trajectory_looping` value from the official annotation CSV. Of the fixed 440
  trajectories, 435 have a consensus `Yes`/`No` looping label (173 positive,
  262 negative); the five conflicts are retained in the product profile but
  excluded from this target-specific score with the reason recorded.
- **Primary paper-facing metric:** Ordinary non-interpolated trajectory-level
  average precision. Each trajectory's candidate score is the fraction of its
  source operations whose CLI-derived semantic path contains the exact
  outcome-blind canonical operation
  `recover from failed or repeated interaction`. The fixed-chain control score
  is the fraction whose source-derived result is exact repetition or a visible
  tool error. The unit is one unique trajectory, never a pair occurrence.
- **Uncertainty and decision rule:** Use a paired 10,000-draw bootstrap over the
  125 task IDs. The correspondence hypothesis is supported only when the
  candidate AP-minus-prevalence interval is wholly positive. Candidate versus
  fixed-chain AP is reported separately: a wholly positive interval supports
  incremental problem correspondence; an interval crossing zero supports
  retained correspondence but not superiority; a wholly negative interval
  limits the recursive hierarchy to contextualization and rejects an improved
  detector claim.
- **Correctness checks:** Exact signed mass and previously verified path totals
  must be preserved; the recursive and fixed-chain profiles must operate on the
  same source operation multiset.
- **Hierarchy diagnostics:** Observed depth, unary warnings, and flat-fan-out
  warnings are reported descriptively for candidate and baseline. They never
  decide scientific support and no depth is required or optimized.
- **Case questions:** Which shared responsibilities have failed-side excess?
  Which have successful-side excess? Which concrete repeated actions account
  for the former? Can stock pprof labels recover the contributing sessions and
  source steps?
- **Repetitions:** Deterministic replay once after the complete annotation,
  followed by independent source and pprof recomputation.

## Planned Runs

| Run group | Role | Workload | Method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| preflight | dependency | 10 complete trajectories from multiple tasks | annotation workspace | 1 | verify source hierarchy, label exclusion, shared marks, signed replay, and drilldown |
| full-recursive | proposed | all 440 trajectories / 338 pairs | automatic Agent annotation | 1 deterministic | test the complete case |
| fixed-chain | baseline | identical pair population | fresh six-field replay | 1 deterministic | distinguish hierarchy value from the known leaf signal |
| looping-score | primary RQ2 endpoint | 435 consensus-labeled trajectories | recovery exposure and fixed-chain control | 10,000 task-cluster draws | test correspondence to independent expert looping labels |
| focused-readback | control | repeated and completion subtrees | stock pprof focus/tags | 1 | verify source-supported user conclusions |

## Execution

- **Annotation-time visible schema:** Session nodes expose only benchmark,
  source ID without pair side, agent model, and goal. Prompt nodes expose the
  goal. LLM nodes expose reasoning, URL, and a bounded accessibility-tree
  preview. Tool nodes expose the original action, visible tool error, and
  additive token/operation measurements. The adapter drops `summary_info` and
  never exposes annotations CSV rows, success/failure, reward, expert looping,
  side effect, optimality, pair membership, pair IDs, or derived
  terminal-success targets.
- **Target-label audit:** Before preflight, enumerate every model-visible key
  and scan values for the annotation strings and aliases `Successful`,
  `Unsuccessful`, `Complete Failure`, `Suboptimal`, `Somewhat Optimal`, `Yes`,
  and `No`. Any match is removed or explained as unrelated source prose before
  workers run. The literal schema, scan result, and worker prompt are recorded
  in `annotation-input-audit.md`.
- **Automatic backend:** Three disjoint Codex subagent workers use fixed
  `gpt-5.6-sol` or `gpt-5.6-terra` configurations and emit only annotation
  fragments. They receive the same outcome-blind instruction and two shared
  canonical names when source evidence supports them:
  `recover from failed or repeated interaction` and
  `verify or report task completion`. Other task/subtask names remain
  source-derived. The root Agent merges disjoint fragments and reconciles
  synonymous shared names before any outcome file is opened. No seed or
  temperature control is exposed by this backend; this is one fixed complete
  automatic run, not a determinism claim.
- **Materialization command:**
  First derive the source-ID-only population list:
  `jq '[.[] | .bad, .good] | unique | {sessions: .}'
  .agentsight/experiments/agentreward-diff-pprof-v1/aggregate-evidence-release-v2/pairs.json
  > .agentsight/experiments/agentreward-recursive-diff-v1/source-session-ids.json`.
  Then run the outcome-blind adapter:
  `python3 script/materialize_agentreward_annotation_workspace.py
  --dataset-root .agentsight/external/agentreward-full
  --session-list
  .agentsight/experiments/agentreward-recursive-diff-v1/source-session-ids.json
  --out
  docs/visexp/out/agentreward-diff-pprof-v1/recursive-annotation-v1`.
  This adapter has no argument or code path for `annotations.csv`, pairs,
  outcomes, or expert labels. Its focused unit tests are
  `python3 -m pytest -q
  script/test_materialize_agentreward_annotation_workspace.py`.
- **Annotation command sequence:** The three Codex subagents receive the
  recorded instructions in
  `experiment-003/backend-instruction.md`, the source-only `trace.jsonl`, and
  disjoint source-session lists for WebArena, VisualWebArena, and the remaining
  WorkArena/AssistantBench sessions. They write disjoint JSON annotation
  fragments under the raw-result directory. The root merges those fragments
  with the materializer's mandatory session/prompt entries into the workspace
  `annotation.json` before opening an outcome file. This is the automatic
  backend run; there is no hand annotation, rule script, or hidden result join.
- **Workspace replay command:**
  `agentpprof/target/release/agentpprof --annotation-file
  docs/visexp/out/agentreward-diff-pprof-v1/recursive-annotation-v1/annotation.json
  --view operations --deterministic-output --output
  .agentsight/experiments/agentreward-recursive-diff-v1/population.operations.pb.gz`.
- **Signed replay and fresh baseline command:**
  `python3 script/agentreward_recursive_diff_eval.py
  --dataset-root .agentsight/external/agentreward-full
  --workspace
  docs/visexp/out/agentreward-diff-pprof-v1/recursive-annotation-v1
  --pair-file
  .agentsight/experiments/agentreward-diff-pprof-v1/aggregate-evidence-release-v2/pairs.json
  --bad-operations
  .agentsight/experiments/agentreward-diff-pprof-v1/aggregate-evidence-release-v2/aggregate/bad.operations.jsonl
  --good-operations
  .agentsight/experiments/agentreward-diff-pprof-v1/aggregate-evidence-release-v2/aggregate/good.operations.jsonl
  --agentpprof agentpprof/target/release/agentpprof
  --out .agentsight/experiments/agentreward-recursive-diff-v1/full-result`.
  This separate post-annotation program is the first stage allowed to open
  `annotations.csv` or the bad/good pair data. It regenerates both signed
  profiles from the same pair-expanded source rows and tests source-multiset
  equality before projection. Its focused unit tests are
  `python3 -m pytest -q script/test_agentreward_recursive_diff_eval.py`.
- **Input snapshot:** The official AgentRewardBench files currently materialized
  under `.agentsight/external/agentreward-full/`, downloaded 2026-07-21, plus
  the fixed Step 0067 pair population. Version identity is recorded as source
  path, official paper/repository URL, counts, and download date rather than a
  research gate.
- **Real preflight:** Ten real trajectories spanning at least two benchmarks and
  both short and long executions.
- **Population ledger and completion:** Before outcomes are opened, the
  workspace must contain all and only the 440 eligible trajectory IDs, all
  source operations must have exactly one CLI-derived path, and every worker
  batch must reach terminal status. After annotation, the fixed pair list must
  contain all 125 tasks and 338 bad--good pair occurrences. Candidate and
  baseline ledgers must match source operation IDs, pair-occurrence
  multiplicities, signs, weights, sample units, and pprof labels exactly.
  Reused trajectories contribute once per registered pair occurrence, which
  explains the difference between unique-trajectory and signed-profile mass.
  Both profiles must load in stock Go pprof and the root must open the
  predeclared focus views.
- **Worker failure and cost:** Workers process disjoint checkpointed batches.
  One failed batch is resumed once with the same input and prompt; a second
  failure reassigns that unchanged batch to another worker. Expected wall time
  is one to three hours with three workers. Available elapsed/model-usage data
  are reported, but their absence does not change the scientific result.
- **Raw-result path:** `.agentsight/experiments/agentreward-recursive-diff-v1/`.
- **Paper artifact path:**
  `docs/visexp/out/agentreward-diff-pprof-v1/recursive-annotation-v1/`.

## Interpretation

- **Positive:** Recovery exposure corresponds to independent expert looping
  labels under the registered AP rule; shared recursive parents organize the
  already verified signed leaf signal, expose failed-side repetition and
  successful-side completion at useful responsibility granularity, and retain
  exact source drilldown.
- **Negative:** The hierarchy adds no readable parent localization, fragments
  equivalent work, or requires outcome-aware naming.
- **Mixed:** One focused subtree is useful but the complete population remains
  fragmented; report the supported subtree only and keep the general
  aggregation limitation explicit.
- **Predeclared focus rule:** Generate one focus for the exact canonical
  recovery operation and one for the exact canonical completion operation.
  Do not choose subtrees by largest observed signed effect after outcomes join.
- **Target paper figure:** One compact signed overview plus those two
  pprof-focused recursive subtrees, rendered with an existing
  pprof-compatible tool. Figure appearance is product QA and explanation, not
  scientific support. The product artifact remains the signed `.pb.gz`.

## Reproducibility Notes

- Keep the released AgentRewardBench source and current pair population fixed.
- Store no success/failure/outcome field in the annotation workspace.
- Preserve all backend outputs even when their hierarchy is rejected.
- Do not introduce a custom renderer, frontend, metric, task-depth target, or
  another benchmark.
