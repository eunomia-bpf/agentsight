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
| datasets | 4 | pass | 21, 30, 34, 49, 50, 55, 56, 59, 60, 61, 65, 150, 151, 152, 153, 155, 204, 227, 228, 241, 242, 252, 267, 268, 272, 274, 287, 288, 289, 290, 291, 292, 303, 315, 316, 323, 326, 331, 333, 335, 346, 352, 354, 359, 360, 362, 367, 368, 373, 376, 379, 398, 408, 410, 426, 427, 428, 429, 430, 431, 444, 448, 449, 450, 451, 452, 453, 454, 468, 486, 491, 515, 563, 567, 573, 574, 578, 579 |
| tasks | 6 | pass | 3, 16, 17, 18, 30, 50, 54, 55, 59, 60, 61, 63, 64, 65, 151, 152, 153, 154, 155, 177, 185, 228, 240, 241, 252, 264, 267, 272, 273, 280, 287, 289, 292, 301, 309, 313, 322, 323, 329, 333, 334, 335, 347, 352, 354, 358, 360, 361, 367, 368, 372, 378, 379, 384, 385, 386, 396, 398, 408, 410, 425, 426, 427, 429, 431, 432, 448, 449, 450, 451, 452, 453, 454, 475, 503, 515, 541, 542, 543, 559, 565, 575, 581 |
| operations | 34,539 | pass | 59, 359, 452 |
| positives | 3,699 | pass | 59, 452 |
| more_selective_than_flat | 6/6 | pass | 59, 61, 64, 154, 267, 272, 273, 452, 454 |
| positive_group_coverage | 6/6 | pass | 59, 61, 64, 154, 267, 272, 273, 452, 454 |
| high_lift_coverage | 5/6 | pass | 59, 60, 63, 65, 153, 155, 267, 396, 408, 410, 452, 453, 454, 543 |
| higher_recall_than_fixed | 5/6 | pass | 59, 60, 63, 65, 153, 155, 267, 396, 408, 410, 452, 453, 454, 543 |
| lower_work_than_fixed | 2/6 | pass | 60, 154, 267, 452 |
| fixed_lower_work_counterpoint | 4/6 | pass | 60, 61, 65, 151, 152, 153, 155, 272, 408, 410, 454 |

## Guardrail Checks

| Key | Status | Occurrences | Unguarded |
|---|---|---|---|
| human_utility | pass | 5 | none |
| automatic_detection | pass | 13 | none |
| unsupervised_boundary | pass | 5 | none |
| fixed_session_dominance | pass | 2 | none |
| trace_ecosystem | pass | 1 | none |
