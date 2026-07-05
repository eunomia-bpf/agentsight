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
| datasets | 4 | pass | 21, 30, 34, 49, 50, 55, 56, 59, 60, 61, 149, 150, 151, 152, 202, 225, 226, 239, 240, 250, 265, 266, 270, 272, 285, 286, 287, 288, 289, 290, 301, 313, 314, 321, 324, 329, 331, 333, 344, 350, 352, 357, 358, 360, 365, 366, 371, 374, 377, 396, 406, 423, 424, 425, 426, 427, 428, 441, 445, 446, 447, 448, 449, 450, 465, 483, 488, 512, 560, 564, 570, 571, 575, 576 |
| tasks | 6 | pass | 3, 16, 17, 18, 30, 50, 54, 55, 59, 60, 61, 63, 64, 150, 151, 152, 153, 175, 183, 226, 238, 239, 250, 262, 265, 270, 271, 278, 285, 287, 290, 299, 307, 311, 320, 321, 327, 331, 332, 333, 345, 350, 352, 356, 358, 359, 365, 366, 370, 376, 377, 382, 383, 384, 394, 396, 406, 422, 423, 424, 426, 428, 429, 445, 446, 447, 448, 449, 450, 451, 472, 500, 512, 538, 539, 540, 556, 562, 572, 578 |
| operations | 34,539 | pass | 59, 357, 449 |
| positives | 3,699 | pass | 59, 449 |
| more_selective_than_flat | 6/6 | pass | 59, 61, 64, 153, 265, 270, 271, 449, 451 |
| positive_group_coverage | 6/6 | pass | 59, 61, 64, 153, 265, 270, 271, 449, 451 |
| high_lift_coverage | 5/6 | pass | 59, 60, 63, 152, 265, 394, 406, 449, 450, 451, 540 |
| higher_recall_than_fixed | 5/6 | pass | 59, 60, 63, 152, 265, 394, 406, 449, 450, 451, 540 |
| lower_work_than_fixed | 2/6 | pass | 60, 153, 265, 449, 451 |
| fixed_lower_work_counterpoint | 4/6 | pass | 60, 61, 150, 151, 152, 270, 406 |

## Guardrail Checks

| Key | Status | Occurrences | Unguarded |
|---|---|---|---|
| human_utility | pass | 5 | none |
| automatic_detection | pass | 13 | none |
| unsupervised_boundary | pass | 5 | none |
| fixed_session_dominance | pass | 2 | none |
| trace_ecosystem | pass | 1 | none |
