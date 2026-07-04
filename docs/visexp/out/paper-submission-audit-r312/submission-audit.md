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
| datasets | 4 | pass | 21, 30, 34, 49, 50, 55, 56, 59, 60, 61, 149, 198, 221, 222, 235, 236, 246, 261, 262, 266, 268, 281, 282, 283, 284, 285, 286, 297, 309, 310, 317, 320, 325, 327, 329, 340, 346, 348, 353, 354, 356, 361, 362, 367, 370, 373, 392, 414, 415, 416, 417, 418, 419, 432, 436, 437, 438, 439, 440, 441, 456, 474, 479, 503, 551, 555, 561, 562, 566, 567 |
| tasks | 6 | pass | 3, 16, 17, 18, 30, 50, 54, 55, 59, 60, 61, 63, 64, 171, 179, 222, 234, 235, 246, 258, 261, 266, 267, 274, 281, 283, 286, 295, 303, 307, 316, 317, 323, 327, 328, 329, 341, 346, 348, 352, 354, 355, 361, 362, 366, 372, 373, 378, 379, 380, 390, 392, 413, 414, 415, 417, 419, 420, 436, 437, 438, 439, 440, 441, 442, 463, 491, 503, 529, 530, 531, 547, 553, 563, 569 |
| operations | 34,539 | pass | 59, 353, 440 |
| positives | 3,699 | pass | 59, 440 |
| more_selective_than_flat | 6/6 | pass | 59, 61, 64, 261, 266, 267, 440, 442 |
| positive_group_coverage | 6/6 | pass | 59, 61, 64, 261, 266, 267, 440, 442 |
| high_lift_coverage | 5/6 | pass | 59, 60, 63, 261, 390, 440, 441, 531 |
| higher_recall_than_fixed | 5/6 | pass | 59, 60, 63, 261, 390, 440, 441, 531 |
| lower_work_than_fixed | 2/6 | pass | 60, 261, 440, 442 |
| fixed_lower_work_counterpoint | 4/6 | pass | 60, 61, 266 |

## Guardrail Checks

| Key | Status | Occurrences | Unguarded |
|---|---|---|---|
| human_utility | pass | 5 | none |
| automatic_detection | pass | 13 | none |
| unsupervised_boundary | pass | 5 | none |
| fixed_session_dominance | pass | 2 | none |
| trace_ecosystem | pass | 1 | none |
