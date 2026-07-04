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
| datasets | 4 | pass | 21, 30, 34, 49, 50, 55, 56, 59, 60, 61, 195, 218, 219, 232, 233, 243, 258, 259, 263, 265, 278, 279, 280, 281, 282, 283, 294, 306, 307, 314, 317, 322, 324, 326, 337, 343, 345, 350, 351, 353, 358, 359, 364, 367, 370, 389, 411, 412, 413, 414, 415, 416, 429, 433, 434, 435, 436, 437, 438, 453, 471, 476, 500, 548, 552, 558, 559, 563, 564 |
| tasks | 6 | pass | 3, 16, 17, 18, 30, 50, 54, 55, 59, 60, 61, 63, 64, 168, 176, 219, 231, 232, 243, 255, 258, 263, 264, 271, 278, 280, 283, 292, 300, 304, 313, 314, 320, 324, 325, 326, 338, 343, 345, 349, 351, 352, 358, 359, 363, 369, 370, 375, 376, 377, 387, 389, 410, 411, 412, 414, 416, 417, 433, 434, 435, 436, 437, 438, 439, 460, 488, 500, 526, 527, 528, 544, 550, 560, 566 |
| operations | 34,539 | pass | 59, 350, 437 |
| positives | 3,699 | pass | 59, 437 |
| more_selective_than_flat | 6/6 | pass | 59, 61, 64, 258, 263, 264, 437, 439 |
| positive_group_coverage | 6/6 | pass | 59, 61, 64, 258, 263, 264, 437, 439 |
| high_lift_coverage | 5/6 | pass | 59, 60, 63, 258, 387, 437, 438, 528 |
| higher_recall_than_fixed | 5/6 | pass | 59, 60, 63, 258, 387, 437, 438, 528 |
| lower_work_than_fixed | 2/6 | pass | 60, 258, 437, 439 |
| fixed_lower_work_counterpoint | 4/6 | pass | 60, 61, 263 |

## Guardrail Checks

| Key | Status | Occurrences | Unguarded |
|---|---|---|---|
| human_utility | pass | 5 | none |
| automatic_detection | pass | 13 | none |
| unsupervised_boundary | pass | 5 | none |
| fixed_session_dominance | pass | 2 | none |
| trace_ecosystem | pass | 1 | none |
