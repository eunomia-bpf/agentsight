# R242 Human-Evidence Contract Smoke

Status: `passed`

R242 uses synthetic returned files to test the R195 contract. It is not C5/C6 outcome evidence.

## Cases

| case | status | purpose |
|---|---|---|
| synthetic-ready | `scored_human_inputs_no_supported_gate` | Complete synthetic files score end-to-end without claim support. |
| partial-r124 | `partial_human_inputs` | One missing labeler sheet is detected as partial input. |
| invalid-r142 | `scoring_failed` | Duplicate/incomplete response CSV is rejected. |
| no-input | `awaiting_human_inputs` | Empty inbox remains awaiting human inputs. |

## Checks

- `synthetic_ready_r195_command_passed`: `True`.
- `synthetic_ready_status_scored_no_supported_gate`: `True`.
- `synthetic_ready_all_operations_scored`: r124=True, r142=True, r190=True, r203=True.
- `synthetic_ready_claim_gates_remain_false`: not_c5_supported=True, not_c6_adequacy_supported=True, not_canonical_map_updated=True, not_canonicalization_quality_supported=True, not_long_tail_promotion_review_supported=True.
- `partial_r124_detected`: `True`.
- `invalid_r142_rejected`: `True`.
- `no_input_awaiting`: `True`.
- `canonical_empty_gates_preserved`: `True`.

## Boundary

R242 proves only the R195 ingestion/scoring contract. It uses synthetic returned files, does not count as C5 participant evidence, does not count as C6 human adequacy evidence, and must not be used to upgrade claim verdicts.
