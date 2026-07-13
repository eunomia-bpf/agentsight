# Experiment Plan: RQ2 HINTBench Matched-Recall Localization

**Plan status:** approved after five serial plan-review rounds; Round 5 PASS
authorizes REAL PREFLIGHT  
**Experiment scope:** one RQ, one hypothesis, one official benchmark population  
**Paper-edit boundary:** this EXPERIMENT gate does not edit `docs/paper/`

## Research Question

- **RQ exactly as written in the paper:** **RQ2: Does Profiler Output
  Correspond to Real Problems?**
- **Specific uncertainty tested here:** Given one shared target-blind
  step-localization signal, does real AgentProf stack construction plus one
  validation-selected multiresolution prefix policy reduce the number of atomic
  HINTBench steps inspected to reach at least 80% macro recall of official
  risky-step targets, relative to native inspection, independent-step ranking,
  per-session grouping, and raw-action grouping? An ordinary `GROUP BY`
  implementation that exactly reconstructs the selected prefix policy is an
  algebraic identity control, not a competing representation expected to differ.
- **Why the answer matters:** The current paper's 9.4% work point has low recall
  and does not isolate grouping from target-informed ranking. A positive matched-
  recall result on a fresh external population would establish the original RQ2
  promise as an analyst-work advantage rather than a group-count or low-recall
  artifact.

The paper-level thesis remains exactly:

> **Agent observability needs profiling, not only debugging.**

This experiment tests one consequence of that thesis. It cannot change the
thesis, replace RQ2, narrow its positive hypothesis, or answer the entire RQ by
itself.

## Paper-Value Admission

- **Planned role:** decisive RQ2 evidence.
- **Largest credible paper story this experiment could unlock:** Across a new
  official, human-verified synthetic agent-trajectory benchmark, a semantic
  profile can turn the same target-blind audit signal into substantially less
  population-level inspection at the same high recall than per-run, per-step,
  per-session, or single-action alternatives, while an exact flat reconstruction
  independently verifies that the gain comes from the declared multiresolution
  profiling policy rather than an implementation discrepancy.
- **Strongest reviewer reject argument or load-bearing uncertainty addressed:**
  Existing localization gains may come entirely from a detector, target-guided
  configuration, low recall, or a simple debugging/grouping view rather than
  operation-stack profiling. A separate representation-specific advantage over
  an algebraically identical `GROUP BY` reconstruction is impossible and is not
  asserted.
- **Independent evidence added beyond existing runs and published results:**
  HINTBench contributes 536 currently released test trajectories, 12,877 raw
  steps, 400 risky trajectories, 136 safe controls, and 938 distinct official
  `(trajectory, target step)` pairs. None of these targets appeared in previous
  AgentProf experiments.
- **Why the result is not tautological, already settled, or dominated:** Official
  target fields are excluded from every adapter, localizer request, operation,
  profile, field selection, and rank score. They enter only after all method
  outputs exist. Every method receives the same raw trajectories, derived
  visible fields, and localizer outputs. Validation and test domains are
  disjoint, and no test target selects a method or parameter.
- **Paper decision if positive:** After independent result review and the outer
  EXPERIMENT audit, route to WRITE and replace only the current RQ2 result
  surface with the complete positive matched-recall result. Preserve the
  original story and all four RQs.
- **Paper decision if contradictory, mixed, or inconclusive:** Record the tested
  mechanism/workload boundary in the result report and canonical evidence
  memory, retain the fixed RQ2 hypothesis, and return to full-paper REVIEW to
  select a materially improved mechanism or another fixed RQ. Do not retune on
  HINTBench test targets and do not rewrite the thesis.
- **Best alternative experiment and why this one has higher decision value:**
  RQ1 independent attribution truth, RQ3 an actual prompt tagger, and RQ4 cold/
  warm end-to-end cost are all needed. RQ2 currently has the largest visible
  rejection risk, and HINTBench is the largest fresh official step-localization
  population already verified as executable.

## Expected And Alternative Outcomes

- **Current expected answer:** A semantic operation stack plus a predeclared
  downstream prefix-ranking policy should transfer a sparse but real target-
  blind risky-step signal across recurrent phase/action/outcome contexts and
  reach 80% macro target recall with less atomic-step work than all four main
  debugging/simple-grouping comparators. The exact flat reconstruction must tie
  AgentProf at every candidate and selected test result.
- **Strongest competing explanation:** The shared localizer alone, an execution
  boundary, or one raw action category determines the useful ordering. One of
  those simpler views matches or beats AgentProf, so multiresolution profiling
  adds no localization value.
- **Result that would contradict the expectation:** AgentProf fails to reach 80%
  macro recall, or its paired work reduction against any of the four
  predeclared main baselines is non-positive or has a 95% interval that includes
  zero. Any mismatch with the exact flat reconstruction invalidates the
  implementation rather than constituting a scientific win or loss.

## Published Precedent And Real Assets

- **Closest published protocol:** HINTBench's official whole-trajectory risk
  auditing and step-localization task, prompt, output schema, and risk-step
  interpretation from the paper and released evaluator:
  <https://arxiv.org/abs/2604.13954> and
  <https://anonymous.4open.science/r/HINTBench-B841>.
- **Official system/model/data/benchmark/tool and version:**
  - current paper-linked HINTBench 4open artifact `HINTBench-B841`, Apache-2.0;
  - current official test file `data/hintbench.json`, enumerating 536 records;
  - official validation file `data/hintbench_val.json`, enumerating 80 records;
  - official `eval/evaluate.py` prompt, formatter, JSON parsing, and risky-step
    union semantics;
  - AgentProf `0.2.37`, using its real `--operation-file`, operation-stack, JSON
    profile, and folded-stack paths;
  - the already running llama.cpp server at `http://127.0.0.1:8012/v1` with the local
    `Qwen_Qwen3.6-27B-Q4_K_M.gguf` model, 27.3B parameters, 32,768-token runtime
    context, temperature zero, and reasoning disabled.
- **What is reused:** Every released validation/test trajectory; the official
  full-trajectory audit prompt body; the official eleven risk names and JSON
  output shape; the official parsing semantics; the real AgentProf binary and
  profile representation; the published validation/test split.
- **Necessary deviations or custom glue:**
  1. The README advertises 629 test trajectories, but the current official file
     has 536; FULL means all 536 enumerable records.
  2. The current test file uses `risk_labels`, whereas the released evaluator
     expects the older `injected_risks` schema. A deterministic adapter reads
     `risk_origin_step` for injected entries and `step_id` for additional
     entries. It never infers a missing target.
  3. The official formatter does not visibly print an ID for every role, and
     current test `step_id` values are non-contiguous in 216 trajectories. The
     adapter preserves the official role/content rendering but prefixes every
     rendered item with one explicit display ID, as defined below. This is
     necessary to make predicted integers unambiguous.
  4. The current official evaluator (observed SHA-256
     `ab7bcfc70d6cb45fe91c8020a61754312c9fb7e6a8cb909fb260aab76236ab80`)
     passes each filled prompt directly to vLLM with temperature `0.1`, top-p
     `0.9`, maximum output 1,024 tokens, and unconstrained text parsing. The thin
     adapter uses llama.cpp, Qwen3.6-27B, temperature zero, top-p `1.0`, the same
     maximum output 1,024, one explicit chat-template envelope, and the exact
     constrained JSON schema below. These are disclosed serving, sampling,
     envelope, and decoding deviations; the task, risk names, trajectory
     evidence, and requested output meaning stay the same.
  5. A thin scorer converts target-blind localizer outputs and real AgentProf
     profiles into matched-recall work curves. No additional custom workload or
     hand-authored target is introduced.

HINTBench's scenarios are generated through the benchmark's synthesis pipeline
and manually verified. They are not described as naturally occurring or real
agent executions. The experiment uses a real official public benchmark, real
released software, a real local model, and the real AgentProf system; its
trajectory evidence is human-verified synthetic evidence.

## Source And Ground-Truth Boundary

### Primary test population

- Run all 536 current test records: 400 risky and 136 safe.
- Treat every released trajectory item, including system, user, agent, and
  environment items, as one atomic inspection step and one operation.
- The primary work denominator is all 12,877 released test steps. Safe-case
  steps count as work and prevent a method from obtaining a free false-positive
  budget.

### Official targets

- For each `risk_labels` entry, use `risk_origin_step` when present; otherwise
  use `step_id`.
- Deduplicate repeated annotations of the same `(record id, step id)` pair.
- The primary denominator contains all 938 distinct official pairs.
- Three official targets are absent from their released trajectories:
  record 170 step 7, record 233 step 9, and record 516 step 13. They remain
  unrecovered misses for every method. They are never remapped, inferred, or
  removed.
- A secondary sensitivity result may use the 935 mappable pairs, but it cannot
  replace the primary result.
- `is_risky`, every `risk_labels` field, and every validation/test target are
  forbidden from profiler and localizer inputs except that validation targets
  may score the predeclared development candidates described below.

### Validation split

- Use all 80 official validation trajectories only to select one fixed semantic
  field order. For every one of the 24 candidate orders, AgentProf and the flat
  exact-reconstruction control must independently produce identical prefix
  counts, scores, tiers, recall/work curves, and selection values.
- To match current-test target semantics, validation uses only each official
  `injected_risks[].risk_origin_step`, deduplicated per trajectory. It does not
  add `affected_steps`.
- The validation denominator is all 163 distinct `(record, origin ordinal)`
  pairs. Validation array index 39, task
  `digitalEvidenceBreachCounselHub_task_0009_risk_v3`, declares origin 35 for a
  33-item trajectory; that absent target remains an unrecovered miss for every
  candidate and both implementations. It is never dropped, remapped, inferred,
  or treated as a source error.
- For order selection, validation macro recall is the mean over exactly the 60
  trajectories containing official origins. The absent origin above remains in
  its trajectory's recall denominator. Validation work is the atomic-step count
  and fraction over all 3,050 released validation items, including every item in
  the 20 trajectories without official origins. Select the candidate with
  minimum work at least 80% validation macro recall; break an exact work tie
  only by the lexical field-order key.
- Test output is generated only after validation selection is complete. No
  test target may change an adapter, prompt, field, field order, score, tie
  rule, baseline, or metric.

### Prediction-step namespace

- **Validation:** validation items have no released `step_id`, so the display ID
  is the zero-based trajectory ordinal `0..len-1`.
- **Test:** the display ID is the item's released integer `step_id`.
- Before each model request, prefix **every** formatted system, user, agent, and
  environment item with the exact bytes `[STEP_ID=<display id>]\n`, followed
  immediately by the official formatter's role-specific text. Preserve that
  text byte-for-byte; in particular, an agent item's official rendering may
  also contain its original `[STEP_ID]: <id>` field and is not deduplicated.
- Require display IDs to be unique within each trajectory. A duplicate or
  missing test `step_id` invalidates that source record and stops preflight.
- A predicted integer maps only to the operation bearing the identical displayed
  ID. An integer outside the displayed set maps to no operation and is retained
  as an out-of-range prediction in raw output.
- This mapping is target-blind. It leaves records 170/233/516's absent official
  targets absent and unrecovered.

## Shared Target-Blind Signal

Run the official HINTBench whole-trajectory prompt body exactly once at
temperature zero for every validation and test record, with the explicit step-ID
rendering deviation above. Parse the first terminal response with the official
normalization rules. For operation `i`:

`localizer_hit(i) = 1` if `i` appears in the union of the model-predicted
`risk_steps`; otherwise `0`.

The signal is deliberately shared. It is not an AgentProf contribution. All
methods consume the same terminal predictions. A transport failure is retried
with the identical request. A syntactically terminal but invalid model response
is recorded as an official-style parse error with zero predicted steps; it is
not reprompted with different wording.

The localizer sees the raw trajectory but never `is_risky`, `risk_labels`, an
official target ID, a gold risk category, or another method's output.

### Exact llama.cpp request envelope

1. Fill the official `PROMPT_TEMPLATE` with the trajectory string produced by
   the exact formatter and step-ID rule above.
2. Send that complete filled prompt as the content of exactly one message:
   `{"role":"user","content":<filled prompt>}`. Use
   `/v1/chat/completions`, not raw `/completion`, with `stream=false`, the exact
   model path from the command, `temperature=0`, `top_p=1.0`,
   `max_tokens=1024`, `reasoning_format="none"`, and
   `chat_template_kwargs={"enable_thinking":false}`. The Qwen chat template is
   an explicit deviation from the official evaluator's raw vLLM prompt.
3. Use `response_format.type="json_schema"` with this exact schema. The root is
   an object with required fields `verdict` and `risks` and
   `additionalProperties=false`. `verdict` is a string enum of `safe` and
   `unsafe`. `risks` is an array whose item is an object with required fields
   `risk_name` and `risk_steps` and `additionalProperties=false`; `risk_name`
   is a string enum of the official eleven names, and `risk_steps` is an array
   of integers. Neither array has `minItems`, and the schema adds no conditional
   relationship between verdict and risks. Safe/unsafe consistency, empty
   risks, duplicate integers, and invalid semantic content remain governed by
   the official parser semantics rather than extra grammar constraints.
   The enum is exactly, in the official order: `Execute Ambiguous Instructions
   Without Confirmation`, `Unauthorized or Out-of-Scope Execution`,
   `Fabrication or Unsupported Claims`, `Result Tampering`,
   `Capability/Permission Misjudgment`, `Invalid Tool Calls`, `Missing
   Validation or Confirmation`, `Missing Exception Handling`, `Wrong Execution
   Order`, `False Completion or False Success`, and `State Misjudgment or
   Duplicate Execution`.
4. Persist the exact schema and canonical complete request body with each raw
   response. A resume entry is reusable only when split, record key, and the
   complete canonical request body agree. HTTP-success parse errors and
   out-of-range predictions are terminal zero-hit outputs; only transport,
   non-2xx, or missing-choice failures may retry, always with the identical
   request.

## Visible Operation Mapping

The adapter creates exactly one operation per released step with `value = 1`
and the following target-blind fields:

- `operation_id`: split + record id + displayed step id, used only for lineage;
- `session`: split + record id;
- `environment`: for test, use the exact released `env` when it is a nonempty
  string; when `env` is absent or an empty string, use the substring of the
  nonempty `task_id` before its first literal `_task_`. A present non-string
  `env`, missing/empty `task_id`, missing delimiter, or empty prefix is a source
  error that stops preflight. Validation always uses that same `task_id` prefix
  rule. The current test snapshot has 382 string-`env` records and 154 records
  with `env` absent; all 154 satisfy the fallback, and all 536 are retained.
- `phase`: `system` for role `system`; `instruction` for role `user`; `observe`
  for role `environment`; `act` for role `agent` with a nonempty `action`; and
  `report` for every other role `agent`. Any other role is a source error.
- `action`: parse every nonempty agent `action` as a JSON object and read its
  nonempty string `name`; a malformed object becomes the literal
  `malformed_action`. An environment item inherits the tool name only when the
  immediately preceding item is an agent action. An agent report inherits the
  linked tool name only when the immediately preceding item is such an
  environment response. Every other item uses `none`.
- `status`: classify an environment item's own `content` with the exact rule
  below. An immediately following agent report inherits that environment
  status. Every other item uses `unknown`.
- `localizer_hit`: the shared model signal, encoded only for ranking and never
  as a stack field.

Status classification lowercases strings and applies **error before success**:

1. Parse `content` as JSON when possible. Classify `error` when top-level
   `success` or `ok` is boolean false; top-level `error` or `errors` is a
   nonempty string/list/object; or top-level string `status` contains one of the
   literal case-insensitive markers `error`, `fail`, `timeout`, `timed_out`,
   `invalid`, `reject`, `denied`, `blocked`, `unresponsive`, `out_of_service`,
   or `unknown`.
2. Classify `success` when top-level `success` or `ok` is boolean true, or
   top-level string `status` contains one of `success`, `succeed`, `complete`,
   `sent`, `delivered`, `published`, `created`, `signed`, `issued`, `processed`,
   `approved`, `executed`, `confirmed`, `released`, `scheduled`, `activated`,
   `verified`, `received`, `transmitted`, `submitted`, `broadcasted`, or
   `updated`.
3. If JSON parsing fails, apply the same marker lists to the entire raw string,
   again with error precedence.
4. Otherwise classify `unknown`.

Marker matching is literal substring matching on lowercase text. No rule is
added, removed, or reordered after validation scoring.

The four semantic stack fields are therefore `environment`, `phase`, `action`,
and `status`. The adapter emits the same raw values to every method. Before a
value is written into an AgentProf operation file, encode its UTF-8 bytes as the
literal `hex:` followed by lowercase hexadecimal digits, including the empty
string as `hex:`. This encoding is injective and remains unchanged by
AgentProf's ASCII-lowercasing frame sanitizer. Preflight must decode every
encoded value back to the exact raw value, verify a one-to-one raw/encoded map
over both splits, and abort on any mismatch or collision. Scoring maps emitted
frames back through that verified table. No truncation, lossy replacement,
benchmark label, risk description, manual semantic category, or test-informed
regex is allowed.

## Comparison

### Proposed method: AgentProf hierarchical prefix ranking

1. Run the real AgentProf binary over all operation rows with one ordering of
   the four semantic fields.
2. Run a count profile with every operation value `1`. Run a shifted-signal
   profile with value `1 + localizer_hit`, because AgentProf 0.2.37 converts a
   zero operation value to one.
3. For every emitted leaf, subtract count weight from shifted weight to recover
   exact hit count. Accumulate count and shifted weights independently at each
   non-root prefix and subtract there to recover prefix `n` and `h`. Require
   every leaf and prefix to equal an independent calculation from operation
   assignments, and require exact global count/hit conservation.
4. Score each leaf by the maximum 95% Wilson lower bound of `h/n` along its own
   prefix path. This shares evidence at the most informative available
   granularity while keeping final inspection units disjoint leaves.
5. Rank disjoint leaves by path score. A score value defines one indivisible
   tier; every leaf with that score is inspected before recall is tested.
   Hit mass, smaller width, and lexical stack key are display-only ordering
   within the tier and never permit threshold stopping. Inspecting a leaf incurs
   all atomic steps assigned to it.

All 24 permutations of the same four fields are evaluated on validation.
Select the one with minimum work at 80% validation macro recall under the exact
validation population and work denominator above, using only lexical field
order as the deterministic tie-breaker.
Run exactly that one order on test.

Ordered stacks and their prefixes are genuine AgentProf output. The maximum
Wilson lower hit-density score over a path is a predeclared downstream scorer,
not an AgentProf 0.2.37 built-in ranker. The result is described as **real
AgentProf stack construction plus a fixed prefix-ranking policy**. Wilson
scoring is existing project machinery already used in the complete
AgentProcessBench evaluation; here it consumes only the independent HINTBench
localizer signal. Gold targets never contribute to `h`.

### Main baselines

1. **Native sequential inspection.** Rank trajectories by their Wilson
   predicted-hit density, then inspect steps within each trajectory in released
   order. Its score tier is the exact pair `(trajectory Wilson score, released
   ordinal)`, so evaluation may stop after a source-order position but never
   choose among steps at the same score/ordinal using gold. Competing position:
   a per-run debugger plus the same auditor is sufficient.
2. **Flat independent-step ranking.** Treat every operation as a singleton and
   rank predicted hits before non-hits. Competing position: the localizer alone
   creates all useful work reduction.
3. **Per-session grouping.** Treat each released trajectory as one group and
   rank groups by the same Wilson hit-density score. Competing position: fixed
   execution boundaries are the correct responsibility unit.
4. **Raw-action grouping.** Group only by parsed raw `action` and rank by the
   same Wilson score. Competing position: a simple visible action category is
   sufficient.

### Algebraic identity control

**Flat exact reconstruction.** For each of the same 24 field orders, ordinary
flat code performs four `GROUP BY` projections corresponding exactly to that
order's cumulative prefixes, assigns each full four-field leaf the maximum of
the same four Wilson scores, and applies the identical tier/work rules. It uses
the same validation objective and deterministic tie-breakers to select an
order. Before test execution, every candidate's prefix `n/h`, leaf score, tier,
curve, selection objective, and selected order must equal the independently
constructed AgentProf result exactly. On test, the selected control must again
produce the identical ranking tiers and work curve. A mismatch stops execution
as an implementation error. An exact tie is expected and is reported as an
identity check, not counted as a main-baseline comparison and not used to claim
that stack serialization is more accurate than equivalent SQL.

### Why matched execution is necessary

Published HINTBench scores measure localizer accuracy, not inspection work after
the same signal is organized by these methods. Every comparator therefore
needs a matched run on the same 536 records. Citation-only numbers cannot answer
the profiling comparison.

### Controls, not main claims

- **Mappable-target sensitivity:** repeat scoring with the three absent targets
  removed.
- **Flat exact reconstruction:** the mandatory identity control above proves
  that AgentProf's selected prefix policy has been implemented and attributed
  correctly; it is not a positive comparison.
- **Signal-free ordering:** rank AgentProf leaf groups by atomic operation width
  in descending order and consume the complete equal-width tier before testing
  recall. This checks whether compression alone explains an apparent gain; it
  is not a second experiment or a positive baseline.

No oracle row, second model, second benchmark, prompt sweep, extra grouping
vocabulary, or test-target retuning is admitted.

### Information, tuning, and compute fairness

- All methods share one model response per record and exactly the same visible
  operation rows.
- AgentProf and the flat exact-reconstruction control each implement all 24
  candidate prefix chains independently, receive the identical validation
  objective and tie-breakers, and must agree exactly before test. The four main
  baselines have no selectable semantic-field order.
- All score formulas, tie rules, target semantics, and positive criteria are
  fixed before test execution.
- Model inference is not repeated per method; compute differences after the
  shared localizer are measured but do not affect scientific eligibility.

## Workloads And Metrics

- **Real workloads:** all 80 official HINTBench validation trajectories for
  development, followed by all 536 current official test trajectories for the
  result.
- **Primary metric:** minimum atomic-step count and fraction required to reach
  at least 80% macro recall across the 400 risky test trajectories. Macro recall
  is the mean, over risky trajectories, of recovered distinct official target
  pairs divided by all official target pairs for that trajectory, including any
  absent released target.
- **Primary comparisons:** four predeclared paired differences,
  `AgentProf work fraction - baseline work fraction`, one for every main
  baseline. No baseline is selected after seeing test point estimates.
- **Correctness/ground truth:** the 938 official distinct target pairs; all
  official labels are loaded only in the scoring stage after terminal method
  outputs exist.
- **Tie handling:** for every method, the primary numerical score alone defines
  a tier. Consume every atomic step/group/leaf in the complete equal-score tier
  before testing the recall threshold. Secondary ordering is display-only. For
  native inspection, an exact `(trajectory Wilson score, released ordinal)` pair
  defines a tier and all steps sharing that pair are consumed;
  independent-step tiers are `localizer_hit=1` and `0`; session, action,
  AgentProf, and its exact reconstruction tiers are equal Wilson-derived scores.
- **Uncertainty:** 10,000 paired stratified trajectory-cluster bootstrap
  resamples. In each replicate, sample 400 complete risky trajectories and 136
  complete safe trajectories with replacement within strata; preserve each
  sampled trajectory's full steps, targets, and multiplicity; recompute every
  group's `n/h`, score tier, macro recall, and global work denominator; and keep
  the validation-selected AgentProf order fixed. Do not rerun inference or
  reselect structure. Report NumPy percentile 95% intervals with explicit
  `method="linear"` for every work fraction and all four paired differences.
  The flat reconstruction is checked for exact
  equality within every bootstrap replicate but has no zero-difference interval
  interpreted as evidence.
- **Positive decision threshold:** AgentProf reaches at least 80% primary macro
  recall and the upper endpoint of the paired 95% interval is below zero against
  **each** of the four main baselines, and the exact flat reconstruction agrees
  at every required identity check. Merely having fewer groups, a better point
  estimate, higher AP, or lower work at lower recall is insufficient.
- **Secondary metrics:** mappable-target sensitivity, micro target recall at the
  selected work point, safe-case work, distinct group count, profile signal/
  operation conservation, and end-to-end/post-localizer runtime. These explain
  the primary result but cannot overturn it.
- **Repetitions and seeds:** one deterministic model response per record;
  bootstrap seed `20260713`; no stochastic model sweep.
- **Cost estimate:** 616 complete local model requests (80 validation + 536
  test), 15,927 released steps, one validation structural sweep, and one fixed
  test matrix. REAL PREFLIGHT records observed request latency and projects the
  completion time; FULL continues to all terminal records regardless of the
  projection.

## Planned Runs

| Run group | Role | Workload | System/method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| real preflight | executability | 1 risky + 1 safe validation trajectory | official prompt + local Qwen + real AgentProf + every scorer path | 1 | authorize implementation path only |
| validation localizer | development | all 80 official validation trajectories | one shared official-protocol localizer output | 1 | supplies target-blind signal |
| validation structure | development | all 3,050 validation steps | 24 AgentProf field orders + 24 independently reconstructed flat prefix chains + baselines | 1 | require exact identity and select their one common order |
| test localizer | shared input | all 536 current test trajectories | one shared official-protocol localizer output | 1 | supplies terminal target-blind signal |
| test main | proposed | all 12,877 test steps | fixed AgentProf hierarchical prefix ranking | 1 | primary RQ2 result |
| test main | baselines | all 12,877 test steps | native, independent-step, per-session, raw-action | 1 each over shared outputs | test every competing position |
| test identity | correctness control | all 12,877 test steps | flat exact reconstruction of the selected prefix policy | 1 | must exactly match AgentProf |
| test control | control | all 12,877 test steps | AgentProf width-only ordering | 1 | compression-only explanation |
| result uncertainty | scoring | complete terminal test outputs | 10,000 paired stratified bootstraps | fixed seed | positive/contradictory/mixed decision |

## Execution

- **Authoritative workflow:** Implement one thin
  `script/hintbench_profile_localization_eval.py` adapter/scorer with explicit
  `preflight` and `full` commands. It downloads or reads the official files,
  formats the official prompt, calls the existing local endpoint, writes one
  operation per official step, invokes
  `agentpprof/target/release/agentpprof`, verifies conservation, and emits raw
  results plus a detailed Markdown report.
- **Concrete REAL PREFLIGHT command:**
  `python3 script/hintbench_profile_localization_eval.py preflight --test-url https://anonymous.4open.science/api/repo/HINTBench-B841/file/data/hintbench.json --validation-url https://anonymous.4open.science/api/repo/HINTBench-B841/file/data/hintbench_val.json --agentpprof-bin agentpprof/target/release/agentpprof --base-url http://127.0.0.1:8012/v1 --model /home/yunwei37/workspace/models/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf --out docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/preflight`.
- **Concrete FULL command:**
  `python3 script/hintbench_profile_localization_eval.py full --test-url https://anonymous.4open.science/api/repo/HINTBench-B841/file/data/hintbench.json --validation-url https://anonymous.4open.science/api/repo/HINTBench-B841/file/data/hintbench_val.json --agentpprof-bin agentpprof/target/release/agentpprof --base-url http://127.0.0.1:8012/v1 --model /home/yunwei37/workspace/models/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf --bootstrap 10000 --seed 20260713 --resume --out docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full`.
- **Real preflight case:** Use the first risky and first safe validation records
  in released order. Exercise the real 27B model endpoint, official prompt and
  parser, current schemas, actual AgentProf binary, all group/rank paths, target-
  blind operation construction, score calculation, and report generation.
  Preflight may repair implementation errors but may not choose a result or
  inspect test targets. Before inference, render all 616 planned requests. For
  each, call llama.cpp `/apply-template` with the exact one-message envelope and
  `chat_template_kwargs`, then `/tokenize` the returned prompt with
  `add_special=true` and `parse_special=true`. Prove that the exact input-token
  count plus the 1,024-token output allowance fits the 32,768-token runtime
  context without truncation. On the first real request, require the response's
  `usage.prompt_tokens` to equal the precomputed count; a mismatch is an
  implementation error, not permission to change the prompt.
- **Full completion rule:** Every one of the 80 validation and 536 test model
  requests has a terminal output; the proposed method, all four main baselines,
  the exact-reconstruction identity control, and width-only control reach a
  terminal score over all 536 records; all 12,877 test operations are conserved by
  every AgentProf profile; and the complete 10,000-bootstrap result exists.
  A smoke run, successful prefix, or partial model cache is not a result.
- **Raw-result path:**
  `docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/`
  with raw source metadata, localizer responses, operation JSONL, AgentProf JSON
  profiles, group assignments, metric JSON, and Markdown reports.
- **Checkpoint/recovery approach:** Write one terminal localizer response per
  record and resume only missing/transport-failed records with the identical
  request. Preserve completed outputs. If scoring or profile construction fails,
  repair that stage and recompute it from the same terminal responses. This is
  execution recovery, not a scientific gate or immutable protocol.

## Interpretation

- **Positive result:** The primary decision threshold passes against every one
  of the four main baselines and all identity checks pass. Interpret this as
  decisive evidence that, for HINTBench's official human-verified synthetic
  intrinsic-risk localization task, AgentProf's multiresolution operation-stack
  profile adds population-level inspection value beyond the shared auditor,
  per-run debugging, singleton ranking, session grouping, and raw-action
  grouping. The exact flat tie establishes the algebraic boundary: equivalent
  `GROUP BY` code can reproduce the chosen profile, not that a different result
  exists. This supports RQ2 but does not alone prove all agent profiling tasks.
- **Negative or contradictory result:** A strong baseline matches/wins or
  AgentProf cannot reach 80% recall. Record which competing position wins and
  stop this HINTBench branch. Do not modify RQ2 or hide the result in the paper;
  route the evidence to REVIEW, while the reader-facing paper remains unchanged
  until a WRITE decision.
- **Mixed or inconclusive result:** A point gain without interval separation,
  improvement only in the mappable sensitivity, or baseline-dependent crossing
  curves is not positive. Record the exact boundary and return to REVIEW.
- **Target paper figure or table:** One RQ2 work-versus-macro-recall curve with
  the 80% vertical decision line, plus one compact table containing work count,
  work fraction, interval, paired delta, and group count for the proposed method
  and four main baselines, plus one explicit exact-reconstruction identity row.

## Reproducibility Notes

- **Software and data versions:** Record AgentProf `--version`, llama.cpp model
  metadata returned by `/v1/models`, the official HINTBench URLs and observed
  record counts, and the final adapter command in the result Markdown. Git
  identity is not a scientific input or gate.
- **Config and seed notes:** Temperature zero; top-p `1.0`; reasoning disabled;
  maximum output 1,024; 32,768-token context; official prompt body plus explicit
  display IDs and one user-message Qwen chat envelope; the exact constrained
  JSON schema above; bootstrap seed `20260713`; NumPy linear percentiles.
- **Known deviations:** Current 536-record test snapshot rather than the README's
  unavailable 629; current `risk_labels` normalization; explicit display IDs for
  every role; llama.cpp chat completion instead of the official evaluator's raw
  vLLM prompt; Qwen3.6-27B rather than the evaluator example's placeholder
  Llama-3.2-3B path; deterministic constrained decoding rather than
  temperature-0.1/top-p-0.9 unconstrained parsing; only released origin/
  additional target IDs count in the primary test. Both use `max_tokens=1024`.

## Plan Review Questions

Serial reviewers must answer these questions without expanding the experiment:

1. Is the target-blind localizer genuinely shared, or can any method see more
   information?
2. Does hierarchical prefix ranking test a real operation-stack property rather
   than re-label a generic detector?
3. Does the independently implemented flat control exactly reconstruct all 24
   AgentProf prefix candidates, selection, and test curves, so no gain can be
   attributed to unequal policy tuning or stack serialization alone?
4. Is the 80% macro-recall work metric correct, including safe controls, tied
   tiers, duplicate annotations, and the three absent targets?
5. Can REAL PREFLIGHT and FULL execute every declared cell with the current
   official artifacts and real AgentProf path?
6. Is any row redundant, weak, target-informed, or outside this one RQ2
   experiment?
