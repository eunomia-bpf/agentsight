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
| datasets | 4 | pass | 21, 30, 34, 49, 50, 55, 56, 59, 60, 61, 149, 150, 151, 200, 223, 224, 237, 238, 248, 263, 264, 268, 270, 283, 284, 285, 286, 287, 288, 299, 311, 312, 319, 322, 327, 329, 331, 342, 348, 350, 355, 356, 358, 363, 364, 369, 372, 375, 394, 418, 419, 420, 421, 422, 423, 436, 440, 441, 442, 443, 444, 445, 446, 460, 478, 483, 507, 555, 559, 565, 566, 570, 571 |
| tasks | 6 | pass | 3, 16, 17, 18, 30, 50, 54, 55, 59, 60, 61, 63, 64, 150, 151, 173, 181, 224, 236, 237, 248, 260, 263, 268, 269, 276, 283, 285, 288, 297, 305, 309, 318, 319, 325, 329, 330, 331, 343, 348, 350, 354, 356, 357, 363, 364, 368, 374, 375, 380, 381, 382, 392, 394, 417, 418, 419, 421, 423, 424, 440, 441, 442, 443, 444, 445, 446, 467, 495, 507, 533, 534, 535, 551, 557, 567, 573 |
| operations | 34,539 | pass | 59, 355, 444 |
| positives | 3,699 | pass | 59, 444 |
| more_selective_than_flat | 6/6 | pass | 59, 61, 64, 263, 268, 269, 444, 446 |
| positive_group_coverage | 6/6 | pass | 59, 61, 64, 263, 268, 269, 444, 446 |
| high_lift_coverage | 5/6 | pass | 59, 60, 63, 263, 392, 444, 445, 535 |
| higher_recall_than_fixed | 5/6 | pass | 59, 60, 63, 263, 392, 444, 445, 535 |
| lower_work_than_fixed | 2/6 | pass | 60, 263, 444, 446 |
| fixed_lower_work_counterpoint | 4/6 | pass | 60, 61, 150, 151, 268, 446 |

## Guardrail Checks

| Key | Status | Occurrences | Unguarded |
|---|---|---|---|
| human_utility | pass | 5 | none |
| automatic_detection | pass | 13 | none |
| unsupervised_boundary | pass | 5 | none |
| fixed_session_dominance | pass | 2 | none |
| trace_ecosystem | pass | 1 | none |
