# Plan Review Round 1 — R337 Reuse Audit

## Review metadata

- **Review date:** 2026-07-14
- **Plan reviewed:** `100-proposed-experiment-plan.md`
- **Review scope:** scientific question, baselines, metrics, public-data scope,
  hidden-label/leakage boundary, executable simplicity, and reuse of existing
  experiments.
- **Files checked:** Step 0013 REVIEW exit and full reread; the existing
  R320, R333, and R337 Markdown/JSON/CSV artifacts; and
  `operation_profile_accuracy_eval.py`,
  `operation_inspection_frontier_eval.py`,
  `operation_inspection_target_eval.py`,
  `operation_query_utility_eval.py`, and
  `operation_analyst_ranking_eval.py` where they define inputs, grouping,
  ranking, hidden fields, metrics, CLI arguments, and fixed upstream paths.
- **Edits performed by reviewer:** this report only. No plan, code, paper,
  skill, or Git change.

## Verdict

**BLOCK — three minimal fixes are required before execution.**

The experiment itself is scientifically appropriate and deliberately small.
It tests one bounded hypothesis inside the fixed RQ2, reuses a complete public
trace result, retains the existing 25% target and definitions, and does not
invent a new benchmark, partition, model, annotation, metric, interpolation,
or Pareto aggregate. The block is not a request for broader evaluation. It is
limited to making the already-proposed audit a real executable replay with an
adequate hidden-label boundary.

## What already passes

### 1. Scientific question and evidence role

The selected RQ is quoted verbatim: **“Does Profiler Output Correspond to Real
Problems?”** The tested hypothesis is narrower than the RQ and appropriately
limits the result to six existing tasks at one pre-existing recall point. A
supported result would add a bounded recurring-group compactness statement;
an inconclusive or contradictory replay would prevent that statement. The
plan explicitly forbids changing the RQ, thesis, story, target, or policy after
seeing the result. This is the correct evidence effect for a reuse audit.

The audit is supporting evidence recovery, not new independent evidence. The
plan's allowed-conclusion section states this boundary correctly. The eventual
result report should preserve that classification, but absence of a separate
`planned role: supporting` label is not itself a blocker.

### 2. Baselines and controls

`fixed_session:query_aware` is the strongest direct baseline for the tested
claim because it represents the competing execution/session hierarchy under
the same query-aware visible ranker. `raw_action_stack:query_aware` is a useful
simple-organization counterpoint and `flat:width` exposes the expected
one-group/full-work endpoint. These are sufficient for this bounded
hypothesis. No additional baseline is required.

The existing R337 rows are internally consistent with the planned comparison:
at 25% recall, operation-stack and fixed-session both reach 6/6 tasks;
operation-stack reports median work `0.2000` versus `0.2495` and median groups
`16.0` versus `50.0`; per-task work is 4/1/1 and group count is 5/0/1. Raw
action is mixed (work 3/1/2 and groups 2/0/4), while flat requires median work
`1.0000` and has the expected one-group compactness. These old numbers are
only expectations for the audit, not an advance PASS verdict.

`dataset_native:query_aware` and `operation_stack:width` can remain contextual
rows emitted by the existing scripts. They need not be promoted to main
baselines or used to enlarge the success rule.

### 3. Workloads and metrics

The plan reuses the existing four public operation sources and the exact six
task slices already defined by R320/R333/R337. It neither fetches nor creates
data. The expected scope—four source families, six tasks, 34,539 task-operation
instances, and 3,699 positives—matches the existing R320 artifact.

The metric design is coherent. Positive recall is fixed before inspection;
inspection work is operation mass; groups inspected is a separate
fragmentation quantity. Reporting work and group count side by side avoids a
new cross-metric score. The existing 25% target is the sole success point;
10% and 50% remain context. Median comparisons are supplemented by all six
per-task win/tie/loss rows, so the result cannot be manufactured by one pooled
aggregate.

### 4. Simplicity and reuse

The proposal is much simpler and more defensible than a new matched-cardinality
construction or a new intervention runner. It uses the official repository
scripts and their existing public-data conversions. There is no scientific
reason to add a benchmark, model call, human judgment, relabeling pass,
resampling scheme, cutoff sweep, or new analysis score.

## Blocking defects and minimal fixes

### Blocker 1 — the proposed preflight is not a REAL PREFLIGHT

The current preflight runs three scripts with `--help`, checks file
readability, inspects sample rows, and checks directory writability. Those
steps verify CLI/schema availability only. They do not execute the actual
grouping, ranking, recall-target extraction, baseline path, or raw-output
write, so they cannot demonstrate that the planned experiment runs end to end.

**Minimal fix:** replace the `--help` preflight with one actual invocation of
the existing lightweight R337 script into a temporary preflight directory,
using its real tracked R333/R336 inputs and real metric/output path. Verify
that its output contains all six tasks, the 25% target, and the four required
policies. Because R337 is a local summarizer, this is inexpensive and adds no
new experiment design. `--help` and file/schema checks may remain optional
setup checks, but they cannot be the preflight.

### Blocker 2 — the stated replay chain is not the chain the scripts execute

Both R333 and R337 accept only `--out-dir`; neither accepts an upstream replay
directory. R333 directly reruns the R320 folding/scoring implementation over
the four operation sources, while its fixed R320 report/CSV paths are only
checked as tracked references. R337 always reads the repository's fixed
`docs/visexp/out/operation-inspection-frontier-r333/` artifacts (and fixed R336
recommendations). Therefore a temporary `r320-replay/` is not consumed by the
temporary R333 run, and a temporary `r333-replay/` is not consumed by the
temporary R337 run. As written, steps 1--3 could be described as an end-to-end
temporary reconstruction even though they are three disconnected output
destinations.

The plan also gives prose steps but no exact runnable commands or exact
comparison files. This matters because whole-report byte equality is not
appropriate: reports contain elapsed-time and commit/provenance fields, while
the scientific CSV rows should be deterministic.

**Minimal fix:** describe the run truthfully as an **equivalence audit**, not a
directly piped temporary chain, and add exact commands and comparisons. The
simplest valid route is:

1. remove the separate R320 replay, because R333 already reruns the R320
   grouping/scoring code from the public operation sources for the required
   visible policies;
2. run R333 once with `--out-dir` under the experiment directory;
3. compare its complete claim-bearing `core-policy-scores.csv` and
   `task-policy-curves.csv`, plus task/dataset/operation/leakage fields, against
   the existing R333 artifacts;
4. only if those scientific inputs are identical, run R337 with `--out-dir`
   under the experiment directory and treat its use of the fixed R333 path as
   an equivalent-input reconstruction; and
5. compare the complete R337 `inspection-targets.csv`,
   `policy-target-summary.csv`, and `default-target-comparisons.csv` scientific
   rows against the existing result, excluding runtime/provenance metadata
   from equality.

This requires no code change, no copied source tree, and no custom analysis
script. If the author insists on retaining the R320 replay, the plan must state
that it is a redundant cross-check and not an upstream input; removing it is
preferable under the explicit simplicity requirement.

### Blocker 3 — the hidden-label audit checks field names but not field origin

The existing direct-access boundary is sound as far as it goes:
`operation_profile_accuracy_eval.py` marks oracle fields hidden, the visible
ranker computes features only from `status`, `repeat_signal`, `phase`,
`action`, and `environment`, and labels are summed after groups are formed and
ranked. However, checking only that visible field names do not overlap the
hidden-field set would miss a visible field that had itself been derived from
the target oracle upstream.

This is especially material for the AgentReward looping task, where
`repeat_signal` is intentionally predictive of the expert looping label. The
converter appears to derive it independently from repeated action signatures,
not from `trajectory_looping`; that is scientifically acceptable, but the
audit plan must verify and record this source-derivation fact rather than infer
it from a set-intersection check. The same check should cover the other target
families: safety, step correctness/redundancy, and human group starts.

**Minimal fix:** add one source-lineage check to the existing hidden-label
audit: for each of the four public source converters, record the target oracle
field and confirm from the converter code that the five allowed visible fields
are derived from actions/system outcomes/source metadata rather than copied or
computed from that target oracle. Also record the distinct public source
identifiers present in the operation rows. This is a read-only provenance
check, not a new metric, relabeling pass, or statistical test.

## Explicit non-requirements

The next plan revision should **not** add any of the following:

- another dataset, benchmark, agent run, model, or human study;
- matched-cardinality partitions, interpolation, a Pareto aggregate, or a new
  recall target;
- more baselines than the fixed-session main comparison and the existing
  raw/flat counterpoints;
- new runner code, a custom analysis script, resampling, or repeated stochastic
  trials; or
- Git hashes, commit state, old `pass` booleans, or readiness metadata as
  scientific evidence.

## Re-review condition

Round 2 can PASS once the plan makes only the three changes above: one real
R337 preflight, exact commands plus an honest fixed-input equivalence topology
with redundant R320 replay removed or explicitly demoted, and one
source-derivation leakage check. No broader experiment redesign is warranted.
