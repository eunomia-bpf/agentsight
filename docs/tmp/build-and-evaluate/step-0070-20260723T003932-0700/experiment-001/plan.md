# Experiment Plan: RQ2 Canonical Operation Identity

## Research Question

- **RQ exactly as written in the paper:** Does profiler output correspond to
  real problems?
- **Specific uncertainty tested here:** Whether short, reusable action-first
  operation names improve the cross-session grouping used by the current
  source-preserving automatic Agent profile, without changing any operation
  boundary or source-evidence suffix.
- **Why the answer matters:** The paper's profiling claim depends on recurring
  responsibilities folding across runs. Task-specific prose fragments this
  identity; over-broad one-word verbs can instead merge unrelated work.

## Paper-Value Admission

- **Planned role:** adaptive supporting current-product replay for the paper's
  RQ2 automatic-backend row. These populations and their earlier results have
  already been observed; this is not untouched confirmation.
- **Largest credible paper story this experiment could unlock:** A simple
  operation identity—short action plus object—lets the same automatic marks
  aggregate recurring work across heterogeneous real agent traces and improve
  standard problem localization.
- **Strongest reviewer reject argument addressed:** The current automatic
  backend's apparent structure is open-vocabulary task paraphrase rather than a
  stable cross-run profiling identity.
- **Independent evidence added:** Complete replay on AgentProcessBench,
  HINTBench, and TraceElephant using the existing official target-independent
  localizer/judge signals and official problem targets.
- **Why it is not tautological:** Canonicalization is fixed without opening
  outcome or target files. It may improve, preserve, or degrade MAP depending
  on whether it unifies equivalent responsibilities or collapses distinct ones.
- **Paper decision if positive:** Replace the automatic-backend RQ2 row and
  profile figures with the canonical current algorithm and report the standard
  per-workload effect.
- **Paper decision if contradictory, mixed, or inconclusive:** Report all three
  workload effects and keep the fixed candidate unchanged. Do not select a
  different identity granularity after scores are opened. First-verb
  aggregation remains a query-time roll-up, not an alternative candidate.
- **Best alternative:** Another benchmark or another segmentation model would
  not repair the immediate mismatch between the current tag contract and the
  already complete paper matrix.

## Expected And Alternative Outcomes

- **Current expected answer:** Action-first `verb + object` identities improve
  HINTBench and TraceElephant, where open-vocabulary task phrases fragment
  cross-session grouping. AgentProcessBench may improve, remain unchanged, or
  decline because its source-native organization is already information-rich.
- **Strongest competing explanation:** Short names over-merge semantically
  different responsibilities and reduce the usefulness of group-level signals.
- **Contradictory result:** A workload's canonical-minus-current-Agent paired
  interval is wholly below zero. A mass, boundary, or evidence mismatch is an
  invalid run rather than a scientific contradiction.

## Published Precedent And Real Assets

- **Closest protocol:** Each workload's already admitted standard per-query
  average precision and mean average precision protocol.
- **Real assets:** Complete AgentProcessBench (1,000 sessions, 8,509
  operations), HINTBench (536 sessions, 12,877 operations), and TraceElephant
  (220 sessions, 5,960 operations) inputs and official targets.
- **Reused components:** Existing source-only packets, sparse marks, native and
  recurrence comparisons, source-evidence suffix, signals, targets, scorers,
  task-cluster uncertainty, and AgentPProf `.pb.gz` replay.
- **Necessary glue:** The deterministic
  `action-object-lexicon-v1` mapping in
  `script/rq2_canonical_tag_compare.py` plus the existing evaluator's ordinary
  input path. The mapping process reads only the pre-canonical semantic
  operation-name strings. It case-folds and tokenizes each string, applies the
  checked-in ordered verb/object/qualifier rules, and emits the same result on
  every occurrence and workload. Before writing the candidate, it checks
  adjacent old semantic paths. If two distinct old tags would erase an existing
  boundary by mapping to the same base tag, both are deterministically refined
  to `verb +` one normalized non-action head noun, or the first and last such
  nouns when two are needed. The same old tag still maps identically
  everywhere; unresolved
  collisions make the candidate invalid. There is no model call, manual
  mapping file, task-conditioned rule, or result-conditioned fallback.
  `script/test_rq2_canonical_tag_compare.py` fixes representative outputs and
  checks structural preservation and collision rejection.
  It may not read packets, source summaries, native outcome/result fields,
  benchmark targets, outcomes, expert labels, judge/localizer signals,
  per-query rows, MAP summaries, or old result reviews.

### Fixed canonical-name contract

One mapping is frozen before scoring and shared by all three workloads.
Every output is one to three whitespace-delimited words, starts with an action
verb, and contains no benchmark, task instance, agent, model, tool, repository,
file, or implementation name. The preferred form is `verb + object`; a
one-word verb is legal only when adding an object would not distinguish the
responsibility.

The common verb vocabulary is:
`understand`, `plan`, `search`, `locate`, `navigate`, `inspect`, `extract`,
`compare`, `reason`, `compute`, `diagnose`, `reproduce`, `test`, `edit`,
`build`, `configure`, `execute`, `verify`, `validate`, `recover`, `coordinate`,
`authenticate`, `update`, `create`, `remove`, `deploy`, `submit`, `escalate`,
`communicate`, `report`, `resolve`, `collect`, `repeat`, and `read`. `read`
remains distinct from `inspect` because reading a source and inspecting an
artifact are different reusable actions.

The common object vocabulary is:
`request`, `work`, `evidence`, `source`, `target`, `interface`, `data`,
`answer`, `result`, `cause`, `failure`, `hypothesis`, `artifact`, `service`,
`action`, `condition`, `workflow`, `interaction`, `user`, `record`, `resource`,
`deployment`, `change`, and `completion`. The implementation additionally
normalizes reusable resource-shaped nouns into these classes; it never retains
a benchmark, task instance, agent, model, tool, repository, file, or
implementation proper name.

The optional third word is used only by the fixed lexical qualifier rules or
the boundary-preserving head-noun refinement; it must still be reusable, such as
`external`, `local`, `remote`, `alternate`, or `final`. The mapping cannot be
changed after any candidate pprof, target, per-query AP, or MAP is opened.

## Comparison

- **Proposed method:** Current source-preserving automatic Agent paths with
  every semantic tag transformed by the single frozen mapping above.
- **Main baseline:** The current source-preserving automatic Agent paths before
  canonicalization. It isolates operation identity from boundaries and source
  evidence.
- **Strong native comparison:** The existing source-native/historical
  organization remains in the result table because it is the strongest
  current-practice grouping on these workloads.
- **Controls:** Current semantic-only Agent paths and multi-resolution
  recurrence retain their established roles; they are not renamed baselines.
- **Fairness:** Every method sees the same operations, fixed signal, target,
  and source-evidence suffix. Before scoring, a mechanical audit requires
  identical session/operation IDs, mark starts, mark counts, path depth,
  source-evidence suffix, and source mass. It also rejects adjacent marks within
  one session whose complete canonical paths become equal. The checked-in
  target-blind head-noun refinement described above is the only allowed repair;
  any remaining collision makes the fixed candidate invalid. There is no
  manual or score-informed repair. This prevents naming from silently deleting
  a fixed boundary.

## Workloads And Metrics

- **Workloads:** All three complete existing RQ2 workloads.
- **Primary metric:** Standard non-interpolated per-query AP, arithmetically
  averaged as MAP under the already admitted workload protocols.
- **Correctness:** Exact operation-ID coverage, sample mass, mark boundary,
  parent/next relation, evidence-ID coverage, and stock pprof readback.
- **Uncertainty:** Reuse the workload's existing paired task/query-cluster
  bootstrap structure for canonical minus current Agent and canonical minus
  native. Results are reported independently per workload; there is no omnibus
  verdict or cross-workload method selection.
- **Cost:** Reanalysis of retained source artifacts; no new model inference or
  benchmark collection.

## Planned Runs

| Run group | Role | Workload | Method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| main | proposed | AgentProcessBench | canonical Agent+Evidence | complete once | current RQ2 row |
| main | proposed | HINTBench | canonical Agent+Evidence | complete once | current RQ2 row |
| main | proposed | TraceElephant | canonical Agent+Evidence | complete once | current RQ2 row |
| comparison | baseline/control | all three | current Agent+Evidence, native, recurrence | retained complete run | isolate naming effect |
| uncertainty | analysis | all three | paired canonical contrasts | registered bootstrap | effect scope |

## Execution

- **Canonical mapping and candidate directories:**
  `python3 script/rq2_canonical_tag_compare.py prepare --current-root
  .agentsight/experiments/rq2-a0-v1/full --mapping-out
  docs/tmp/build-and-evaluate/step-0070-20260723T003932-0700/experiment-001/raw/canonical-map.json
  --out .agentsight/experiments/rq2-canonical-tags-v1`. This validates the
  input boundary and collision policy before writing candidate annotations.
- **AgentProcessBench full command:**
  `python3 script/rq2_agent_segmentation_eval.py --benchmark agentprocess
  --root docs/visexp/out/agentprocessbench-rq2/full
  --packet-dir .agentsight/experiments/rq2-a0-v1/full/agentprocess/packets
  --annotation-dir .agentsight/experiments/rq2-canonical-tags-v1/agentprocess/annotations
  --binary agentpprof/target/release/agentpprof --mode full
  --out .agentsight/experiments/rq2-canonical-tags-v1/agentprocess/results`.
- **HINTBench full command:**
  `python3 script/rq2_agent_segmentation_eval.py --benchmark hint
  --root docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full
  --packet-dir .agentsight/experiments/rq2-a0-v1/full/hint/packets
  --annotation-dir .agentsight/experiments/rq2-canonical-tags-v1/hint/annotations
  --binary agentpprof/target/release/agentpprof --mode full
  --out .agentsight/experiments/rq2-canonical-tags-v1/hint/results`.
- **HINT current-baseline rerun under the identical corrected scorer:**
  `python3 script/rq2_agent_segmentation_eval.py --benchmark hint
  --root docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full
  --packet-dir .agentsight/experiments/rq2-a0-v1/full/hint/packets
  --annotation-dir .agentsight/experiments/rq2-a0-v1/full/hint/annotations
  --binary agentpprof/target/release/agentpprof --mode full
  --out .agentsight/experiments/rq2-canonical-tags-v1/hint-current-exact-zero/results`.
  `wilson_lower(0,n)` is exactly `0.0` for both current and candidate; neither
  side may reuse the superseded floating-residue rows.
- **TraceElephant full command:**
  `python3 script/rq2_agent_segmentation_eval.py --benchmark trace
  --root .agentsight/experiments/traceelephant-rq2-v1
  --packet-dir .agentsight/experiments/rq2-a0-v1/full/trace/packets
  --annotation-dir .agentsight/experiments/rq2-canonical-tags-v1/trace/annotations
  --binary agentpprof/target/release/agentpprof --mode full
  --out .agentsight/experiments/rq2-canonical-tags-v1/trace/results`.
- **Current comparison inputs:** TraceElephant uses the retained Step 0067
  current-Agent rows at
  `.agentsight/experiments/rq2-a0-v1/full/trace/results/per-query.jsonl`.
  HINTBench uses the just-described corrected current rerun. Independent
  result review found that the retained AgentProcess rows had a different
  source-evidence depth, so the preceding names were rerun without changing
  the candidate at
  `.agentsight/experiments/rq2-canonical-tags-v1/agentprocess-current-same-evidence/results/per-query.jsonl`.
  Candidate rows are
  `.agentsight/experiments/rq2-canonical-tags-v1/<workload>/results/per-query.jsonl`.
  `python3 script/rq2_canonical_tag_compare.py score` joins them by the
  workload's existing query ID, independently recomputes candidate MAP, and
  applies the same registered paired bootstrap structure: AgentProcessBench
  uses 10,000 family-stratified task-cluster draws with seed 20260716;
  HINTBench uses 100,000 environment-stratified query draws with seed 20260722;
  TraceElephant uses 100,000 five-cell-stratified trace draws with seed
  20260713. The exact commands are:
  `python3 script/rq2_canonical_tag_compare.py score --benchmark agentprocess
  --root docs/visexp/out/agentprocessbench-rq2/full
  --current-results .agentsight/experiments/rq2-canonical-tags-v1/agentprocess-current-same-evidence/results/per-query.jsonl
  --candidate-results .agentsight/experiments/rq2-canonical-tags-v1/agentprocess/results/per-query.jsonl
  --out .agentsight/experiments/rq2-canonical-tags-v1/agentprocess/comparison.json`;
  `python3 script/rq2_canonical_tag_compare.py score --benchmark hint
  --root docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full
  --current-results .agentsight/experiments/rq2-canonical-tags-v1/hint-current-exact-zero/results/per-query.jsonl
  --candidate-results .agentsight/experiments/rq2-canonical-tags-v1/hint/results/per-query.jsonl
  --out .agentsight/experiments/rq2-canonical-tags-v1/hint/comparison.json`;
  and
  `python3 script/rq2_canonical_tag_compare.py score --benchmark trace
  --root .agentsight/experiments/traceelephant-rq2-v1
  --current-results .agentsight/experiments/rq2-a0-v1/full/trace/results/per-query.jsonl
  --candidate-results .agentsight/experiments/rq2-canonical-tags-v1/trace/results/per-query.jsonl
  --out .agentsight/experiments/rq2-canonical-tags-v1/trace/comparison.json`.
  `historical_agentprof` is the declared/reference hierarchy and is never
  substituted for the current Agent+Evidence baseline.
- **Real preflight:** One complete source packet from each workload through the
  same fixed mapping, AgentPProf replay, source-label readback, and MAP scoring
  using `--mode preflight`; no mapping change follows a valid preflight.
  The first preparation attempt, before any candidate profile or score existed,
  correctly rejected 153 base-tag collisions. It is an implementation
  preflight failure, not a scientific result. The deterministic
  boundary-preserving refinement was then added and reviewed before candidate
  generation. Its first implementation left four collisions because it merged
  `read` into `inspect` and retained the last two nouns; before any score was
  opened, the rule was finalized to preserve `read` and use the first and last
  nouns. Any remaining collision invalidates the candidate.
- **Completion:** All 1,756 sessions and 27,346 operations are replayed;
  current and canonical boundaries and evidence IDs match exactly; all three
  MAP rows and paired intervals are present.
- **Raw results:** `.agentsight/experiments/rq2-canonical-tags-v1/`.
- **Recovery:** Per-workload outputs are independent and may be rerun without
  changing another workload.

## Interpretation

- **Valid result:** Report each workload's canonical-minus-current-Agent and
  canonical-minus-native MAP delta with its paired interval, regardless of
  sign. A correctness mismatch is `INVALID`, not a scientific result.
- **Positive workload:** The canonical-minus-current interval is wholly above
  zero.
- **Negative workload:** The interval is wholly below zero.
- **Inconclusive workload:** The interval crosses zero.
- **Mixed outcome:** Preserve all three rows and do not switch candidate
  granularity. Verb-only aggregation remains a query-time roll-up.
- **Target paper artifacts:** RQ2 MAP table and one collection-scale signed
  flame graph with source drilldown.

## Reproducibility Notes

- Existing benchmark versions, source packets, signals, and target files remain
  unchanged.
- Tag generation is target-blind but occurs after earlier method results exist;
  the result is a user-directed current-product replay, not an untouched
  confirmatory benchmark.
- The paper will not describe post-hoc canonicalization as preregistered.
