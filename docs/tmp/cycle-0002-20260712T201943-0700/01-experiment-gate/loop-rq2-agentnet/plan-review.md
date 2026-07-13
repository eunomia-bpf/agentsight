# Serial plan review: AgentNet cross-platform RQ2 experiment

The same independent subagent reviews revisions serially. Every round explicitly
applies `research-experiment-design`, reads the complete source report and
current plan, remains read-only, and returns `PASS` or `REVISE`. The root owns
all dispositions and plan edits.

## Round 1 — REVISE

**Reviewed:** Revision 1  
**Disposition:** accept all four must-fix categories; preserve the RQ, complete
population, cross-platform transfer, and positive hypothesis.

### Reviewer findings

1. The one scientific object needed sharper population wording, an explicit
   combined-label truth table, a complete risk-model feature/mapping list, an
   Ubuntu-development provenance statement, and a supporting-evidence role
   rather than an entire-RQ verdict.
2. Choosing the strongest grouped baseline inside each target bootstrap draw
   was a composite oracle and could choose different comparators by metric. The
   comparison needed fixed baselines.
3. Operation-work metrics require predicted-problem density/mean risk as the
   primary group score. Additive mass is a different per-group-opening objective
   and cannot break density ties. AgentProf's unsigned operation value also
   cannot silently represent arbitrary floating-point risk.
4. The plan needed a conditional paired-bootstrap definition, pooled
   operation-weighted resampling, missing-class handling and maximum attempts,
   exact commands, dependency/resource estimates, terminal checks, and separate
   execution versus scientific statuses.

### Revision 2 changes

- Fixed the truth table to positive=`incorrect OR redundant`,
  negative=`correct AND necessary`, otherwise unresolved after prediction.
- Enumerated every categorical/numeric feature and fixed the existing Ubuntu
  action/target/phase/repetition rules as development provenance.
- Fixed raw-action as the grouped primary alternative and ungrouped transferred
  risk as the localization baseline; removed all target-time comparator
  selection. Exact-repeat and other structures remain controls.
- Defined complete density tie blocks and moved additive mass to secondary
  analysis; AgentProf now validates count stacks while the scorer reconstructs
  full-precision risk by emitted stack key.
- Defined one model fit per fold, shared paired task draws, within-platform
  pooled resampling, 50,000 maximum attempts for 10,000 valid draws, and
  incomplete handling.
- Added exact commands, versions, source sizes, time/disk budget, completion
  checks, and separate execution and hypothesis statuses.

**Files modified by reviewer:** none.

## Round 2 — REVISE

**Reviewed:** Revision 2  
**Disposition:** accept both remaining must-fix items. The reviewer confirmed
that Round 1's baseline, density/tie, AgentProf integer-value, bootstrap-attempt,
command, and completion issues were closed.

### Reviewer findings

1. The plan named existing mapping rules but did not forbid the old
   `normalize_agentnet()` adapter, whose output includes the prohibited target
   labels, task-completion status, and post-hoc quality scores. A physical
   projection/reference-label/target-label dataflow and the exact pure helper
   boundary were required. The phase description also had to match the actual
   helper's `fail` and `system` possibilities.
2. Raw risk values from the Windows-trained and macOS-trained models are not
   necessarily cross-model calibrated, especially with balanced class weights.
   Concatenating steps into one pooled AP/ranking would make platform scale an
   arbitrary determinant. Verdicts must use separate within-fold paired effects
   or a fixed aggregation of within-fold differences.

### Revision 3 changes

- Restricted mapping reuse to the four pure action/target/phase/repetition
  helpers and explicitly prohibited `normalize_agentnet()` as predictor or
  AgentProf input.
- Defined `prepare` as the only raw reader, with one visible projection and two
  separate platform label files.
- Defined predictor subprocess inputs so raw data, source roots, and held-out
  labels are physically unavailable; predictions, group artifacts, risk sums,
  and task bootstrap draws must be saved before the scorer receives target
  labels.
- Corrected phase semantics to the exact helper output.
- Removed pooled cross-model ranking and intervals. Both held-out platforms must
  independently satisfy the complete support criterion; only an equal-weight
  mean of within-fold effects may appear as a secondary summary.

**Files modified by reviewer:** none.

## Round 3 — PASS

**Reviewed:** Revision 3
**Disposition:** approve implementation and REAL PREFLIGHT. No plan must-fix
remains.

### Reviewer confirmation

- The implementation boundary permits only the four pure visible-field helpers
  and prohibits the leaky legacy adapter.
- Raw source access, visible projection, reference labels, target labels,
  predictor inputs, label-blind group artifacts, bootstrap draws, and scorer
  inputs now form an explicit executable dataflow.
- Phase semantics match the helper, including uncommon `fail` and `system`
  values.
- Raw risks from independently fitted platform models are never pooled or
  ranked together; each held-out fold must independently satisfy its paired
  interval conditions.
- One RQ, one tested hypothesis, official source/provenance, fresh target,
  fixed baselines, density ranking, complete ties, AgentProf integer counts,
  bootstrap completion, commands, and execution/scientific status separation
  are mutually consistent.

### Preflight obligations retained

REAL PREFLIGHT must demonstrate subprocess label isolation, pure-helper use,
model convergence, exact AgentProf count conservation, and label-swap
invariance. These are implementation checks under the approved plan, not a
reason to add further protocol machinery.

**Files modified by reviewer:** none.

## Round 4 — PASS

**Reviewed:** Revision 4 source-schema amendment
**Disposition:** approve implementation and rerun source preparation; zero
must-fix.

The checksum-verified official Win/Mac JSONL contains 17,625 trajectory rows
for 17,532 unique task IDs. Ninety-three IDs each have two nonidentical,
non-prefix rows, every ID joins one metadata row, and the official viewer reads
all rows before a direct task-ID metadata merge. The reviewer found no official
or scientific basis for first, last, longest, or random one-row selection.

The approved primary therefore retains every released row, uses a deterministic
source-row `trajectory_id` for operation/session identity, and keeps original
`task_id` as the paired-bootstrap cluster. This preserves the complete
operation-weighted released-row population without pretending that two records
of one task are independent. It does not change the RQ, hypothesis, features,
baselines, metrics, verdict, or paper boundary.

Rejected alternatives were: discarding one row, concatenating two released
trajectories into a synthetic trajectory, independently bootstrapping duplicate
records, or changing the estimand to task-equal weighting.

**Files modified by reviewer:** none.
