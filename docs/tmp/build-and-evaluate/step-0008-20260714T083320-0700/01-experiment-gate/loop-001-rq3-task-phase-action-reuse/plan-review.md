# Plan Review: RQ3 Task/Phase/Action Accuracy From Reused Public Traces

This file records serial independent reviews of the single current
[`plan.md`](plan.md). Reviewers do not edit the plan. The root records each
objection, response, and resulting revision here until scientific and
executability blockers converge.

## Round 1 — Reference Provenance And Executability

- Reviewer: fresh independent subagent using `research-experiment-design`
- Verdict: **REVISE**

### Blocking findings

1. The first plan incorrectly treated all nine adapters' task, phase, and action
   fields as independent native references. Only Mind2Web `row.domain` and
   WebShop `info.task_name` are independent task candidates. Seven task values
   are adapter constants. No corpus supplies an independent phase annotation.
   Only Mind2Web `operation.op`, AndroidControl `action.action_type`, and
   GUI-Odyssey `step.action` are independent structured action candidates.
2. `operation_map_infer.py` derives only task and phase, not action. Its task
   rules largely read dataset/tool/task and its phase rules largely read action;
   after the proposed scrub the first plan's generic workflow was not
   executable.
3. Eligibility depended on producing two predicted labels. That would hide a
   valid collapse failure. Existing alignment code also skips missing
   predictions, so unmatched rows had to become explicit labels inside the
   primary V-measure rather than merely lowering a separate coverage number.
4. A one-operation WebLINX preflight could not exercise an eligible reference
   path under the plan's own criteria.

### Root disposition and minimal revision

- Accepted all provenance and missing-prediction blockers.
- Fixed eligibility before prediction: two task cells, zero phase cells, three
  action cells. The other 22 cells are explicit unavailable results.
- Replaced the generic mapping claim with the actual existing backends: the
  repository's optional target-blind TF-IDF/K-Means task tagger and existing
  action normalization helpers. This adds no model family or metric.
- Made every eligible row scoreable by assigning explicit `unmatched` outputs;
  prediction collapse remains a valid result.
- Defined a small adapter command and changed preflight to a real Mind2Web path.
- Downgraded the historical 13,265 total from a gate to a recovery check.

### Non-blocking notes retained

- The constant-tag control is a simple null, not a main baseline.
- The primary aggregate is labeled operation-weighted; an equal-cell diagnostic
  prevents GUI-Odyssey size from being presented as family-wide generality.

## Round 2 — Independence, Interpretation, And Simplification

- Reviewer: second fresh independent subagent using
  `research-experiment-design`
- Verdict: **REVISE**

### Blocking findings

1. Mind2Web `action_reprs` contains the native operation as a serialized
   suffix. Keeping it leaks the gold action; removing it leaves text the
   existing `action_verb()` cannot parse. A new parser would violate the reuse
   constraint.
2. TF-IDF/K-Means plus V-measure evaluates partition alignment, not literal tag
   names. Repeating a task text for every operation would also let trajectory
   length influence fitting and automatic cluster selection.
3. Recovering five corpora with no eligible cell and maintaining a 27-cell
   availability matrix adds no scientific evidence.
4. The historical `webshop-expert` adapter currently points to an lclan mirror
   whose observed task metadata are ScienceWorld-style, and the converter does
   not yet emit the task text required by the plan.
5. AndroidControl and GUI-Odyssey visible action text require one source-field
   audit to exclude direct structured copies of their native gold labels.
6. One cross-axis operation-weighted mean would mix task and action questions
   and be dominated by GUI-Odyssey.

### Root disposition and minimal revision

- Removed Mind2Web action rather than adding a parser: four candidate cells
  remain.
- Defined task scores as partition fidelity, deduplicated clustering input by
  session, and retained operation-weighted scoring only inside each cell.
- Removed recovery and execution for the five sources with no independent
  cell, the 13,265-operation recovery check, the 27-cell matrix, and all cross-
  cell means.
- Named the lclan source by actual repository/task provenance and required one
  existing native question/user-task text per session. This is a small
  converter exposure, not a new tagger.
- Added one pre-inference field-level audit for AndroidControl and GUI-Odyssey.
  Direct structured gold serialization makes that cell unavailable; it does
  not authorize replacement work.
- Kept only per-cell V-measure/coverage, one constant control, and AgentProf
  mass conservation.

### Non-blocking notes retained

- The unchanged task backend's automatic range starts at five clusters, while
  a source may have fewer native classes. Over-partitioning is a real backend
  outcome, not a reason to tune cluster count from the gold labels.

## Round 3 — Final Scientific And Executability Audit

- Reviewer: third fresh independent subagent using
  `research-experiment-design`
- Verdict: **PASS**
- Blocking findings: none.

### Verified

- The plan contains two task-partition cells and two action-partition
  candidates, with no pseudo-independent phase result.
- Both task and action outcomes are interpreted as partition fidelity under the
  existing label-permutation-invariant V-measure.
- Session-level task deduplication, scorer-only references, literal
  `unmatched`, the constant control, and per-cell/union AgentProf conservation
  are executable with the narrowly authorized adapter.
- The lclan source has independent top-level `question` and `info.task_name`
  fields; exposing `question` under `--include-text` needs no parser.
- The Mind2Web source file currently supplies nine sessions. Those nine texts
  produce a nonempty existing TF-IDF feature space and exercise the automatic
  clustering path; GUI-Odyssey covers the action path in preflight.
- No new benchmark, model, metric, parser, cutoff, or parameter sweep remains.

### Non-blocking notes retained

- The current Mind2Web file returns nine rather than the requested ten or one
  hundred rows. The plan and later report record the observed complete prefix.
- The action source audit may mark a candidate unavailable if its visible text
  directly serializes the structured gold field. That is a predeclared valid
  availability result, not an invitation to substitute a dataset or parser.
