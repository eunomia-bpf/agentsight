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
| datasets | 4 | pass | 21, 30, 34, 48, 49, 54, 55, 58, 59, 60, 186, 209, 210, 223, 224, 234, 249, 250, 254, 256, 269, 270, 271, 272, 273, 274, 285, 297, 298, 305, 308, 313, 315, 317, 328, 334, 336, 341, 342, 344, 349, 350, 355, 358, 361, 378, 382, 383, 384, 385, 386, 387, 388, 402, 417, 421, 439, 487, 491, 497, 498 |
| tasks | 6 | pass | 3, 16, 17, 18, 30, 49, 53, 54, 58, 59, 60, 164, 210, 222, 223, 234, 246, 249, 254, 255, 262, 269, 271, 274, 283, 291, 295, 304, 305, 311, 315, 316, 317, 329, 334, 336, 340, 342, 343, 349, 350, 354, 360, 361, 366, 367, 368, 382, 383, 384, 385, 386, 387, 388, 409, 439, 440, 441, 467, 483, 489, 499 |
| operations | 34,539 | pass | 58, 341, 386 |
| positives | 3,699 | pass | 58, 386 |
| more_selective_than_flat | 6/6 | pass | 58, 60, 249, 254, 255, 386, 387 |
| positive_group_coverage | 6/6 | pass | 58, 60, 249, 254, 255, 386, 387 |
| high_lift_coverage | 5/6 | pass | 58, 59, 249, 386 |
| higher_recall_than_fixed | 5/6 | pass | 58, 59, 249, 386 |
| lower_work_than_fixed | 2/6 | pass | 59, 249, 386 |
| fixed_lower_work_counterpoint | 4/6 | pass | 59, 60, 254, 387 |

## Guardrail Checks

| Key | Status | Occurrences | Unguarded |
|---|---|---|---|
| human_utility | pass | 4 | none |
| automatic_detection | pass | 13 | none |
| unsupervised_boundary | pass | 5 | none |
| fixed_session_dominance | pass | 2 | none |
| trace_ecosystem | pass | 1 | none |
