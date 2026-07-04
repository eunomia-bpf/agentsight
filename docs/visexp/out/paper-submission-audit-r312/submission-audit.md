# Paper Submission Audit R312

R312 audits the current Chinese draft against the R310/R311 evidence. It does not sync datasets or rerun profilers.

## Readiness

- Overall: scoped_claim_ready.
- Number alignment: pass.
- Two-abstraction boundary: pass.
- Must-not-claim guardrails: pass.
- Paper structure: pass.
- Position: The scoped mechanism and automated inspectability claims are aligned with R310/R311 evidence, but the draft should not be treated as a full OSDI/NeurIPS submission until paper-structure polish and the controlled analyst-study gap are addressed.

## Claim Alignment

| Claim | Status | Paper use | Remaining gap |
|---|---|---|---|
| C1 | scoped_ready | mechanism claim | Import a real external OpenTelemetry GenAI or Perfetto trace before claiming ecosystem compatibility. |
| C2 | scoped_ready | recursive stack-depth claim | Deeper sequence/subtask boundary evidence would expand the claim. |
| C3 | partial | extension-point claim only | Calibrated boundary backends and simple-baseline comparisons on another family. |
| C4 | automated_proxy_ready | inspectability-tradeoff claim | Controlled human/agent analyst study before user-utility wording. |

## Number Checks

| Key | Expected text | Status | Lines |
|---|---|---|---|
| datasets | 4 | pass | 21, 30, 34, 48, 49, 54, 55, 58, 59, 60, 185, 208, 209, 222, 223, 233, 239, 244, 245, 250, 251, 255, 257, 270, 271, 272, 273, 274, 275, 286, 298, 299, 306, 309, 314, 316, 318, 329, 335, 337, 342, 343, 345, 350, 351, 356, 359, 362, 383, 384, 385, 386, 387, 388, 390, 391, 392, 393, 394, 395, 396, 397, 398, 400, 401, 402, 403, 404, 405, 406, 420, 435, 439, 456, 457, 466, 483, 500, 504, 510, 511 |
| tasks | 6 | pass | 3, 16, 17, 18, 30, 49, 53, 54, 58, 59, 60, 163, 209, 221, 222, 233, 239, 243, 247, 250, 255, 256, 263, 270, 272, 275, 284, 292, 296, 305, 306, 312, 316, 317, 318, 330, 335, 337, 341, 343, 344, 350, 351, 355, 361, 362, 367, 368, 369, 376, 383, 384, 385, 386, 387, 388, 389, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402, 403, 404, 406, 427, 457, 482, 496, 502, 512 |
| operations | 34,539 | pass | 58, 342, 395, 400, 402 |
| positives | 3,699 | pass | 58, 402 |
| more_selective_than_flat | 6/6 | pass | 58, 60, 250, 255, 256, 401, 402, 403, 404 |
| positive_group_coverage | 6/6 | pass | 58, 60, 250, 255, 256, 401, 402, 403, 404 |
| high_lift_coverage | 5/6 | pass | 58, 59, 250, 401, 402, 403 |
| higher_recall_than_fixed | 5/6 | pass | 58, 59, 250, 401, 402, 403 |
| lower_work_than_fixed | 2/6 | pass | 59, 250, 403 |
| fixed_lower_work_counterpoint | 4/6 | pass | 59, 60, 255, 401, 402, 404 |

## Guardrail Checks

| Key | Status | Occurrences | Unguarded |
|---|---|---|---|
| human_utility | pass | 6 | none |
| automatic_detection | pass | 16 | none |
| unsupervised_boundary | pass | 6 | none |
| fixed_session_dominance | pass | 3 | none |
| trace_ecosystem | pass | 1 | none |
