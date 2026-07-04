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
| datasets | 4 | pass | 21, 30, 34, 48, 49, 54, 55, 58, 59, 60, 186, 209, 210, 223, 224, 234, 240, 245, 246, 251, 252, 256, 258, 271, 272, 273, 274, 275, 276, 287, 299, 300, 307, 310, 315, 317, 319, 330, 336, 338, 343, 344, 346, 351, 352, 357, 360, 363, 384, 385, 386, 387, 388, 389, 391, 392, 393, 394, 395, 396, 397, 398, 399, 401, 402, 403, 404, 405, 406, 407, 421, 436, 440, 458, 506, 510, 516, 517 |
| tasks | 6 | pass | 3, 16, 17, 18, 30, 49, 53, 54, 58, 59, 60, 164, 210, 222, 223, 234, 240, 244, 248, 251, 256, 257, 264, 271, 273, 276, 285, 293, 297, 306, 307, 313, 317, 318, 319, 331, 336, 338, 342, 344, 345, 351, 352, 356, 362, 363, 368, 369, 370, 377, 384, 385, 386, 387, 388, 389, 390, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402, 403, 404, 405, 407, 428, 458, 459, 460, 486, 502, 508, 518 |
| operations | 34,539 | pass | 58, 343, 396, 401, 403, 407 |
| positives | 3,699 | pass | 58, 403, 407 |
| more_selective_than_flat | 6/6 | pass | 58, 60, 251, 256, 257, 402, 403, 404, 405, 407 |
| positive_group_coverage | 6/6 | pass | 58, 60, 251, 256, 257, 402, 403, 404, 405, 407 |
| high_lift_coverage | 5/6 | pass | 58, 59, 251, 402, 403, 404, 407 |
| higher_recall_than_fixed | 5/6 | pass | 58, 59, 251, 402, 403, 404, 407 |
| lower_work_than_fixed | 2/6 | pass | 59, 251, 404, 407 |
| fixed_lower_work_counterpoint | 4/6 | pass | 59, 60, 256, 402, 403, 405 |

## Guardrail Checks

| Key | Status | Occurrences | Unguarded |
|---|---|---|---|
| human_utility | pass | 6 | none |
| automatic_detection | pass | 18 | none |
| unsupervised_boundary | pass | 6 | none |
| fixed_session_dominance | pass | 3 | none |
| trace_ecosystem | pass | 1 | none |
