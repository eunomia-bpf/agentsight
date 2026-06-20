# R195 Human Evidence Pipeline

Status: `awaiting_human_inputs`
Input mode: `default_inbox`
Human return content: `awaiting_inputs`

## Inputs

| input | exists | rows |
|---|---:|---:|
| `r124_labeler_1` | False | None |
| `r124_labeler_2` | False | None |
| `r190_labeler_1` | False | None |
| `r190_labeler_2` | False | None |
| `r203_labeler_1` | False | None |
| `r203_labeler_2` | False | None |
| `r142_responses` | False | None |

## Readiness

- R124 ready: `False`; missing: `r124_labeler_1, r124_labeler_2`.
- R190 ready: `False`; missing: `r190_labeler_1, r190_labeler_2`.
- R203 ready: `False`; missing: `r203_labeler_1, r203_labeler_2`.
- R142 ready: `False`; missing: `r142_responses`.
- Safety status: `passed`.

## Claim Gates

- C5 supported: `False`.
- C6 adequacy supported: `False`.
- Canonicalization quality supported: `False`.
- Long-tail promotion review supported: `False`.
- Canonical map updated: `False`.

## Operations

No scorers ran because no complete input group was present.

## Boundary

R195 is an ingestion/scoring pipeline. It does not create human labels or participant responses. Missing inputs keep C5/C6 unsupported; ready inputs are scored into an R195-specific directory without overwriting canonical gates. Known synthetic export markers are rejected before any scorer runs. R203 promotion labels can support a promotion-review gate only; they do not update the canonical map or substitute for C5/C6 evidence.
