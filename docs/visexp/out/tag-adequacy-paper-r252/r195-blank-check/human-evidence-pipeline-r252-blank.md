# R195 Human Evidence Pipeline

Status: `scored_human_inputs_no_supported_gate`
Input mode: `explicit_paths`
Human return content: `present_but_blank`

## Inputs

| input | exists | rows |
|---|---:|---:|
| `r124_labeler_1` | True | 300 |
| `r124_labeler_2` | True | 300 |
| `r190_labeler_1` | True | 160 |
| `r190_labeler_2` | True | 160 |
| `r203_labeler_1` | True | 41 |
| `r203_labeler_2` | True | 41 |
| `r142_responses` | False | None |

## Readiness

- R124 ready: `True`; missing: ``.
- R190 ready: `True`; missing: ``.
- R203 ready: `True`; missing: ``.
- R142 ready: `False`; missing: `r142_responses`.

## Claim Gates

- C5 supported: `False`.
- C6 adequacy supported: `False`.
- Canonicalization quality supported: `False`.
- Long-tail promotion review supported: `False`.
- Canonical map updated: `False`.

## Operations

- `r124`: `joined_not_ready_for_scoring`.
- `r190`: `human_labels_empty`.
- `r203`: `human_labels_empty`.

## Boundary

R195 is an ingestion/scoring pipeline. It does not create human labels or participant responses. Missing inputs keep C5/C6 unsupported; ready inputs are scored into an R195-specific directory without overwriting canonical gates. R203 promotion labels can support a promotion-review gate only; they do not update the canonical map or substitute for C5/C6 evidence.
