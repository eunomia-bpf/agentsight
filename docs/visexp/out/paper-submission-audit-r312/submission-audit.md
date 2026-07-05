# Paper Submission Audit R312

R312 audits the current Chinese draft against the R310/R311/R320 evidence. It does not sync datasets or rerun profilers.

## Readiness

- Overall: scoped_claim_ready.
- Number alignment: pass.
- Two-abstraction boundary: pass.
- Must-not-claim guardrails: pass.
- Paper structure: pass.
- Position: The draft is scoped-claim ready for a profiling-paper argument: mechanism, two-abstraction boundary, guardrails, and the R320 hidden-label localization/ranking benchmark are aligned. It still must not claim human productivity, time-to-answer, or complete trace-ecosystem compatibility without separate evidence.

## Claim Alignment

| Claim | Status | Paper use | Remaining gap |
|---|---|---|---|
| C1 | scoped_ready | mechanism claim | Import a real external OpenTelemetry GenAI or Perfetto trace before claiming ecosystem compatibility. |
| C2 | scoped_ready | recursive stack-depth claim | Deeper sequence/subtask boundary evidence would expand the claim. |
| C3 | partial | extension-point claim only | Calibrated boundary backends and simple-baseline comparisons on another family. |
| C4 | hidden_label_profiler_accuracy_ready | profiler localization/ranking and actionability claim | Expand R320 to more oracle-rich tool/API and mobile GUI families; run a controlled human/agent analyst study only before user-productivity wording. |

## Number Checks

| Key | Expected text | Status | Lines |
|---|---|---|---|
| datasets | 4 | pass | 21, 30, 34, 49, 50, 55, 56, 59, 60, 61, 149, 150, 151, 152, 201, 224, 225, 238, 239, 249, 264, 265, 269, 271, 284, 285, 286, 287, 288, 289, 300, 312, 313, 320, 323, 328, 330, 332, 343, 349, 351, 356, 357, 359, 364, 365, 370, 373, 376, 395, 405, 420, 421, 422, 423, 424, 425, 438, 442, 443, 444, 445, 446, 447, 448, 462, 480, 485, 509, 557, 561, 567, 568, 572, 573 |
| tasks | 6 | pass | 3, 16, 17, 18, 30, 50, 54, 55, 59, 60, 61, 63, 64, 150, 151, 152, 174, 182, 225, 237, 238, 249, 261, 264, 269, 270, 277, 284, 286, 289, 298, 306, 310, 319, 320, 326, 330, 331, 332, 344, 349, 351, 355, 357, 358, 364, 365, 369, 375, 376, 381, 382, 383, 393, 395, 405, 419, 420, 421, 423, 425, 426, 442, 443, 444, 445, 446, 447, 448, 469, 497, 509, 535, 536, 537, 553, 559, 569, 575 |
| operations | 34,539 | pass | 59, 356, 446 |
| positives | 3,699 | pass | 59, 446 |
| more_selective_than_flat | 6/6 | pass | 59, 61, 64, 264, 269, 270, 446, 448 |
| positive_group_coverage | 6/6 | pass | 59, 61, 64, 264, 269, 270, 446, 448 |
| high_lift_coverage | 5/6 | pass | 59, 60, 63, 152, 264, 393, 405, 446, 447, 448, 537 |
| higher_recall_than_fixed | 5/6 | pass | 59, 60, 63, 152, 264, 393, 405, 446, 447, 448, 537 |
| lower_work_than_fixed | 2/6 | pass | 60, 264, 446 |
| fixed_lower_work_counterpoint | 4/6 | pass | 60, 61, 150, 151, 152, 269, 405, 448 |

## Guardrail Checks

| Key | Status | Occurrences | Unguarded |
|---|---|---|---|
| human_utility | pass | 5 | none |
| automatic_detection | pass | 13 | none |
| unsupervised_boundary | pass | 5 | none |
| fixed_session_dominance | pass | 2 | none |
| trace_ecosystem | pass | 1 | none |
