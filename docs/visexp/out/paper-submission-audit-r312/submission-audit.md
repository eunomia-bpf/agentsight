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
| datasets | 4 | pass | 21, 30, 34, 49, 50, 55, 56, 59, 60, 61, 149, 150, 199, 222, 223, 236, 237, 247, 262, 263, 267, 269, 282, 283, 284, 285, 286, 287, 298, 310, 311, 318, 321, 326, 328, 330, 341, 347, 349, 354, 355, 357, 362, 363, 368, 371, 374, 393, 416, 417, 418, 419, 420, 421, 434, 438, 439, 440, 441, 442, 443, 444, 458, 476, 481, 505, 553, 557, 563, 564, 568, 569 |
| tasks | 6 | pass | 3, 16, 17, 18, 30, 50, 54, 55, 59, 60, 61, 63, 64, 150, 172, 180, 223, 235, 236, 247, 259, 262, 267, 268, 275, 282, 284, 287, 296, 304, 308, 317, 318, 324, 328, 329, 330, 342, 347, 349, 353, 355, 356, 362, 363, 367, 373, 374, 379, 380, 381, 391, 393, 415, 416, 417, 419, 421, 422, 438, 439, 440, 441, 442, 443, 444, 465, 493, 505, 531, 532, 533, 549, 555, 565, 571 |
| operations | 34,539 | pass | 59, 354, 442 |
| positives | 3,699 | pass | 59, 442 |
| more_selective_than_flat | 6/6 | pass | 59, 61, 64, 262, 267, 268, 442, 444 |
| positive_group_coverage | 6/6 | pass | 59, 61, 64, 262, 267, 268, 442, 444 |
| high_lift_coverage | 5/6 | pass | 59, 60, 63, 262, 391, 442, 443, 533 |
| higher_recall_than_fixed | 5/6 | pass | 59, 60, 63, 262, 391, 442, 443, 533 |
| lower_work_than_fixed | 2/6 | pass | 60, 262, 442, 444 |
| fixed_lower_work_counterpoint | 4/6 | pass | 60, 61, 150, 267, 444 |

## Guardrail Checks

| Key | Status | Occurrences | Unguarded |
|---|---|---|---|
| human_utility | pass | 5 | none |
| automatic_detection | pass | 13 | none |
| unsupervised_boundary | pass | 5 | none |
| fixed_session_dominance | pass | 2 | none |
| trace_ecosystem | pass | 1 | none |
