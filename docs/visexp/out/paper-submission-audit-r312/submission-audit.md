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
| datasets | 4 | pass | 21, 30, 34, 48, 49, 54, 55, 58, 59, 184, 207, 208, 221, 222, 232, 238, 243, 244, 249, 250, 263, 264, 265, 266, 267, 268, 279, 291, 292, 299, 302, 307, 309, 311, 322, 328, 330, 335, 336, 338, 343, 344, 349, 352, 355, 376, 377, 378, 379, 380, 381, 383, 384, 385, 386, 387, 388, 389, 390, 391, 393, 394, 395, 396, 398, 412, 483, 487 |
| tasks | 6 | pass | 3, 16, 17, 18, 30, 49, 53, 54, 58, 59, 162, 208, 220, 221, 232, 238, 242, 246, 249, 256, 263, 265, 268, 277, 285, 289, 298, 299, 305, 309, 310, 311, 323, 328, 330, 334, 336, 337, 343, 344, 348, 354, 355, 360, 361, 362, 369, 376, 377, 378, 379, 380, 381, 382, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 397, 398, 467, 479, 485 |
| operations | 34,539 | pass | 58, 335, 388, 393, 395 |
| positives | 3,699 | pass | 58, 395 |
| more_selective_than_flat | 6/6 | pass | 58, 249, 394, 395, 397 |
| positive_group_coverage | 6/6 | pass | 58, 249, 394, 395, 397 |
| high_lift_coverage | 5/6 | pass | 58, 59, 249, 394, 395, 397 |
| higher_recall_than_fixed | 5/6 | pass | 58, 59, 249, 394, 395, 397 |
| lower_work_than_fixed | 2/6 | pass | 59, 249, 397 |
| fixed_lower_work_counterpoint | 4/6 | pass | 59, 394, 395 |

## Guardrail Checks

| Key | Status | Occurrences | Unguarded |
|---|---|---|---|
| human_utility | pass | 6 | none |
| automatic_detection | pass | 16 | none |
| unsupervised_boundary | pass | 6 | none |
| fixed_session_dominance | pass | 3 | none |
| trace_ecosystem | pass | 1 | none |
