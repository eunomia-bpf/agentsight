# Round 03: Fresh Logic Flow

Reviewer mode: independent read-only subagent tracing the full claim chain

## Reviewer Findings

### Must-fix

1. The introduction did not confront RECAP's overlapping chat/edit join or
   acknowledge native logs' weaker edit ground truth.
2. Candidate path/time associations were described as committed, abandoned,
   verified, or missing-verification facts.
3. Line-level survival claims lacked an event-to-hunk-to-commit-to-current-line
   provenance chain.
4. RQ1 coverage and ambiguity metrics could not establish correctness without
   independent ground truth.
5. RQ1 did not test the full complementarity thesis or gate uncertain
   downstream claims.
6. RQ2 mixed process predictors with durable/survival outcomes and risked
   discovering and confirming patterns on the same histories.
7. RQ3 did not freeze its core views, tasks, answer keys, or scoring rubrics.
8. RQ3 confounded information content with interface coordination.
9. RQ4 conflated systems responsiveness with human interpretability.
10. Only a null RQ3 outcome had an explicit claim bound.

### Should-fix

The reviewer also requested “evidence layers” rather than independent sources,
vendor/schema-stratified coverage, mechanism ablations for stable layout and
semantic zoom, and explicit privacy/schema/lineage threats.

### Consider

The Git-answerable high-churn task can serve as a negative control, and the
RQ1-to-RQ4 dependency chain should be stated directly.

## Root Decisions And Applied Fixes

- Accepted every Must-fix. All path/time joins are now candidate associations;
  verification means only a recorded subsequent action. A line claim requires
  an explicit edit-to-hunk-to-commit-to-line chain, otherwise it remains at path
  granularity.
- RQ1 now uses controlled known-link histories plus a double-annotated
  naturalistic sample, reports accuracy/calibration by granularity and schema,
  includes a four-condition evidence ablation, and gates RQ2/RQ3.
- RQ2 separates process-only predictors from durable outcomes, predefines or
  discovers them on a split, and confirms them on held-out histories.
- RQ3 freezes a decision/evidence/view/task/ground-truth map and separates full-
  data tables from coordinated views to isolate interface effects. The Git-
  answerable survival task is an explicit negative control.
- RQ4 now has independent systems and interpretability tracks and bounds claims
  to real tested duration.
- Added the full RQ dependency and failure-bound logic, vendor/schema and
  lineage threats, privacy limits, and RECAP's favorable edit-ground-truth
  tradeoff.

## Meaning And Evidence Check

These edits narrow unsupported association language and strengthen evaluation
validity. They do not reduce the user's requested gallery scope. Instead, they
separate exploratory visual coverage from claims that require validated joins.
No empirical result was added.

## Verification

`make -C docs/paper` completed successfully and produced a five-page PDF. The
cumulative snapshot diff contains 370 insertions and 139 deletions. A targeted
search found no remaining uses of the rejected exclusive-state labels or of
the unsupported “unverified/abandoned” task language.
