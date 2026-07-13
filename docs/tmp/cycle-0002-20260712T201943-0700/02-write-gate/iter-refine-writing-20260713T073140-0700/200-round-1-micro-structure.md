# Round 1 — Micro Structure

- Reviewer completed: `2026-07-13T07:45:33-07:00`
- Root edits completed: `2026-07-13T07:49:20-07:00`
- Reviewer skill: `check-paper-structure-flow`
- Verdict: `REVISE`
- Post-round paper SHA-256: `7dd247c128718b4a331200f10f8c122def3c570e59c2af1059c545c8be64f4f3`

## Reviewer findings

The reviewer read the complete 829-line current paper, bibliography, full user instructions and idea history, WRITE/idea dispositions, Round 0 report, and micro-structure guidance.

Three must-fixes were found:

1. RQ1 contains four experiments—semantic-axis separation, field selection, weight selection, and automatic induction—but lacks visible internal roles and ends on an orphan figure callout rather than an RQ answer.
2. RQ2 presents its inspection-tradeoff interpretation before statistical validation and stack-sensitivity evidence, then ends on tuning instead of answering the RQ.
3. The central operation-stack paragraph combines definition, call-stack analogy, query-time distinction, debug/profile consequence, formal view triple, and built-in examples.

Should-fix items included separating the Design requirement mapping from the four-stage pipeline; separating Implementation outputs from tagging; separating neutral profiling background from the motivating constraint; splitting RQ4 scope/result/cache roles; and routing introduction/related-work restructuring to later dedicated rounds.

## Applied changes

- Split the Design opening between DR mapping and the four-stage pipeline.
- Split the operation-stack material into definition/projection, query-time consequences, and formal view/weight paragraphs, without rewriting its model.
- Split Implementation into tagging backends and profile outputs.
- Split neutral system-profiling background from the stable-name/runtime-stack constraint.
- Added four ordinary RQ1 signposts and moved the flamegraph callout into the weight-function evidence block.
- Added a direct RQ1 synthesis containing only conclusions already made by the four evidence blocks.
- Split RQ2 benchmark data from baselines.
- Added RQ2 signposts for results, statistics, stack sensitivity, inspection tradeoffs, and answer.
- Reordered existing RQ2 paragraphs to evidence-before-interpretation: setup → baselines → results → statistical validation → sensitivity → tradeoff → answer.
- Did not alter the text or values of any RQ2 result, bootstrap, permutation, depth, tuning, or comparison claim.
- Split RQ4 into scope, end-to-end construction, and intent-cache roles and added a direct synthesis of its existing observations.

## Deferred findings

- Introduction’s delayed two-challenge framing and dense system/results preview: Round 4.
- Related Work thematic comparisons: Round 5 and Round 10, when source accuracy is checked.
- RQ subsection-title convention: Round 2, with fixed RQ wording preserved.
- Abstract/Conclusion four-RQ closure: Round 4 and the final prose pass.

## Lock audit

- Thesis unchanged verbatim.
- Four RQs unchanged in order, wording, and meaning.
- No result number, dataset, baseline, metric, statistical condition, evidence status, or citation changed.
- No negative internal result added.
- No new core abstraction, named layer, or fifth RQ added.
- No paper content or citation was deleted; only existing RQ2 paragraphs were reordered.
- No shared skill, idea history, user instruction, or submodule file changed.
- No Git operation occurred.

## Build verification

`cd docs/paper && make` completed successfully.

- PDF pages: 8;
- PDF bytes: 1,582,559;
- page 8: references only;
- bibliography SHA unchanged;
- no unresolved citation/reference or undefined-control-sequence warning.

The extra run-in signposts did not force main content onto page 8 and did not require formatting changes.
