# Step 0093 Experiment 001: Cross-Framework Same-Task Retrieval

## Decision context

- **Fixed paper RQ:** RQ3 — “How Accurate Are the Tags?”
- **Paper thesis preserved:** “Agent observability needs profiling, not only debugging.”
- **Specific uncertainty:** Across independently produced CodeTrace trajectories for
  the same benchmark task, does a session's complete AgentProf operation-path
  distribution retain more reproducible task-level structure than the source-native
  action organization?
- **Role:** retrospective, supporting RQ3 reanalysis of the already frozen Step 0087
  corpus. It is not a new tag-accuracy headline, not a test of individual-operation
  semantic equivalence, and not confirmatory evidence.

The exploratory question and several candidate metrics were inspected before this
plan was written. Consequently, all intervals and comparisons in this experiment
are descriptive retrospective estimates. No p-value or preregistration claim is
permitted.

## Paper-value decision

The experiment may support one bounded paper or appendix statement:

> Within CodeTrace, under repeated task-prompt exposure, non-root canonical
> operation-path distributions show retrospective cross-framework
> representational consistency beyond source-native action histograms.

That statement is admissible only if all of the following hold under the frozen
scoring implementation:

1. canonical full-path task-macro MAP exceeds each main source-native baseline;
2. the 95% complete-task bootstrap interval for canonical full path minus
   **each** main source-native baseline is wholly positive;
3. the interval for canonical full path minus canonical root-only is wholly
   positive;
4. canonical root-stripped full path exceeds both main source-native baselines,
   with a wholly positive interval against each;
5. after removing every generic canonical frame whose normalized label ends in
   ` work`, the root-stripped path still exceeds both main source-native
   baselines with a wholly positive interval against each;
6. canonical full path exceeds the phase-histogram and operation-count controls;
7. corpus/key/integrity checks pass and an independent reviewer reproduces the
   result without invoking the authoritative scorer.

Canonicalization itself may be credited only if the 95% complete-task bootstrap
interval for canonical minus pre-canonical full path is wholly positive. Otherwise,
the result can describe the final representation but cannot claim that
canonicalization caused the gain.

If the main gate fails or an independent reviewer finds leakage or a scoring
defect, this experiment is not admitted into the positive paper. It remains an
auditable negative/mixed experiment record, and the next RQ3 experiment must use an
external programmatic subgoal/operation oracle rather than another CodeTrace
task-retrieval reanalysis.

## Frozen inputs

Read-only Step 0087 artifacts:

- `../../step-0087-20260726T023000-0700/experiment-001/assembled/operations-count.jsonl`
- `../../step-0087-20260726T023000-0700/experiment-001/assembled/predictions.jsonl`
- `../../step-0087-20260726T023000-0700/experiment-001/canonical/predictions.jsonl`
- `../../step-0087-20260726T023000-0700/experiment-001/assembled/summary.json`
- `../../step-0087-20260726T023000-0700/experiment-001/canonical/canonicalization-report.json`

The scorer must record SHA-256 digests of every input. It must fail closed on
duplicate `(session, step_id)` rows, missing fields, non-unit operation counts,
different key sets between source rows and both prediction files, a session
whose source rows disagree on `prompt` or `agent`, or any assembled/canonical
prediction row for which `prediction.framework != source fields.agent`.

The benchmark task oracle is exactly `fields.prompt`; framework is exactly
`fields.agent`. Neither is an AgentProf prediction. `fields.prompt` is used only
to determine relevance during scoring and must never enter a representation.

## Population and retrieval protocol

1. Aggregate the 20,866 operation rows into one representation per session.
2. A query session is eligible only when at least one other session has the same
   `fields.prompt` and a different `fields.agent`.
3. Its candidate set is every other session whose `fields.agent` differs from
   the query's. Same-framework sessions are excluded, including same-task ones.
4. A candidate is relevant iff its `fields.prompt` exactly equals the query's.
5. Rank candidates by descending cosine similarity. Session IDs never break
   ties because all 405 frozen session IDs contain the task identifier. Metrics
   instead marginalize uniformly over all permutations within each exact-score
   tie group. Empty/zero vectors have cosine similarity zero.
6. Compute tie-aware expected average precision for every query. For a tie group
   of size `n` with `r` relevant items, starting after `a` ranked candidates and
   `b` relevant candidates, its expected AP numerator contribution is

   `sum(k=1..n) (r/n) * (b + 1 + (k-1)(r-1)/(n-1)) / (a+k)`

   for `n > 1`; for `n = 1`, use the ordinary precision contribution. Divide the
   total numerator by the query's total number of relevant candidates.
7. Average query AP within each task, then average those task means:
   **task-macro MAP is primary**. This prevents tasks with more framework
   replicas from dominating.

The scorer must print and save the number of sessions, task clusters, eligible
tasks, eligible queries, candidates per query, relevant items per query, and
framework pairs. No subsampling is allowed in the full run.

## Representations

All representations are sparse count vectors computed from the same operation
rows. They do not use task IDs or task text.

### Candidate method

- **Canonical full path:** join all normalized `semantic_stack[].label` values in
  order using ` / `; count that complete path once per operation row.

### Main source-native baselines

1. **Action-kind histogram:** count `fields.action_kind`.
2. **Raw-action-key histogram:** count `fields.raw_action_key`.

These are the two main baselines. The stronger one by point task-macro MAP is the
frozen comparator for the primary delta.

### Component ablation

- **Pre-canonical full path:** construct the complete path identically from
  `assembled/predictions.jsonl`.
- **Canonical root-only:** count only the first canonical path label.
- **Canonical root-stripped full path:** remove the first frame from each
  canonical path before joining the remaining labels; use `<empty>` only for
  originally single-frame paths.

### Negative controls and sensitivities

- **Phase histogram:** count `fields.phase`.
- **Operation count only:** rank by
  `-abs(log1p(query_count) - log1p(candidate_count))`; larger is more similar.
- **Random ranking:** deterministic per-query pseudo-random scores with seed
  `20260729`, with no task field in the seed.
- **Canonical leaf:** count only the last canonical path label.
- **Generic-work removal:** remove each canonical stack frame whose
  whitespace-normalized, lower-cased label ends in ` work`; use `<empty>` only
  when no frame remains. Report both the ordinary full-path and root-stripped
  versions. For the latter, strip the original root first and then remove
  generic-work frames.
- **Binary-presence sensitivity:** repeat the candidate method and both main
  baselines with each feature value clipped to one per session.
- **TF-IDF sensitivity:** repeat the candidate method and both main baselines
  using session-level inverse document frequency
  `log((1 + N) / (1 + df)) + 1`.

The primary representation remains raw count vectors. Controls and sensitivities
cannot replace it after results are known.

## Metrics

### Primary

- Task-macro cross-framework MAP.
- Paired canonical-minus-baseline task delta with a 95% percentile bootstrap
  interval over complete eligible task clusters.

### Secondary

- Query-micro MAP.
- Tie-aware expected top-1 accuracy: the relevant fraction `r/n` in the
  highest-score tie group.
- Tie-aware expected reciprocal rank of the first relevant candidate. For the
  first tie group containing relevant items, use
  `sum(k=1..n-r+1) [C(n-k,r-1)/C(n,r)] / (a+k)`, where `a` is the number of
  candidates in earlier score groups.
- Pairwise AUROC over all eligible query-candidate pairs.
- Mean same-task and different-task cosine similarity.
- Task-macro MAP and paired deltas for every ablation/control/sensitivity.

Pairwise AUROC is explicitly secondary because tasks with many candidates create
many more pairs. A method may have higher AUROC but lower retrieval MAP; the
primary admission decision follows task-macro MAP.

## Bootstrap

- Seed: `20260729`.
- Replicates: 10,000.
- Resampling unit: complete eligible benchmark task cluster.
- Within each replicate, sample eligible tasks with replacement and average their
  already computed per-task paired deltas.
- Report point delta and percentile `[2.5%, 97.5%]`.
- Never resample operations, candidate pairs, or queries independently.
- These are conditional, fixed-candidate-library topic/task resampling
  intervals over the eligible CodeTrace tasks. They do not estimate performance
  for a general population of new tasks.

## Prompt-exposure confound and claim boundary

The Step 0087 annotator packets expose the concrete benchmark task instruction.
The same task instruction is repeated across frameworks. Moreover, the frozen
corpus has 251 task identifiers but only 45 canonical root labels, and all 405
session IDs contain the scorer task identifier. Therefore this experiment asks
only whether the generated non-root representation *retains* cross-framework
task structure after explicit root and tie controls; it does not establish
task-blind discovery, individual operation identity, or semantic equivalence.
The task oracle `fields.prompt` is scorer-only, but prompt exposure in the
upstream model input remains a construct limitation and must accompany any
reported result.

Other forbidden inferences:

- no causal optimization or resource-saving claim;
- no generalization beyond CodeTrace software-engineering trajectories;
- no claim that recurrent names denote equivalent individual operations;
- no claim that canonicalization helps unless its paired interval passes;
- no presentation as an independent tag-accuracy estimate;
- no inference outside CodeTrace or outside prompt-conditioned annotations;
- no replacement or narrowing of fixed RQ3.

## Execution and artifacts

1. Independent plan review must return `APPROVE` before scorer implementation or
   execution.
2. Implement one authoritative standard-library Python scorer in `score.py`.
3. Run `python3 score.py preflight`, which uses the first eligible query but
   executes every representation and integrity check.
4. Inspect the preflight record; then run `python3 score.py full`.
5. Save:
   - `input-manifest.json`
   - `preflight.json`
   - `raw-results.json`
   - `per-query.jsonl`
   - `per-task.jsonl`
   - `bootstrap-summary.json`
   - `execution-log.md`
   - `results.md`
6. A new read-only subagent must independently parse the frozen inputs, recompute
   the primary point estimates and bootstrap intervals without importing or
   invoking `score.py`, audit leakage/ties/units, and issue a paper-admission
   verdict.
7. Iterate only on concrete reviewer-identified validity defects. Any scoring
   change after seeing full results must be documented, rerun from the unchanged
   frozen inputs, and sent back for independent review.
8. Only after an accepted review may the outcome be summarized in
   `docs/evaluation.md`. This experiment does not edit the paper.
