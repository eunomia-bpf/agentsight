# R265 Human Adjudication Workflow Smoke

Status: `passed`

R265 uses synthetic disagreement fixtures to test the R195 adjudication path. It is not human evidence.

## Cases

| case | R195 status | operation statuses |
|---|---|---|
| `unresolved_disagreements` | `needs_adjudication` | `r124=joined_not_ready_for_scoring, r190=needs_adjudication, r203=needs_adjudication` |
| `adjudicated_synthetic` | `scored_human_inputs_no_supported_gate` | `r124=human_labels_scored, r190=human_labels_scored, r203=human_labels_scored` |

## Checks

- `unresolved_r195_command_passed`: `True`.
- `unresolved_top_level_needs_adjudication`: `True`.
- `unresolved_operation_statuses`: r124=True, r190=True, r203=True.
- `unresolved_adjudication_templates_match_disagreements`: r124=True, r190=True, r203=True.
- `unresolved_claim_gates_false`: `True`.
- `adjudicated_r195_command_passed`: `True`.
- `adjudicated_runs_without_support`: `True`.
- `adjudicated_claim_gates_false`: `True`.

## Boundary

R265 proves only that R195 surfaces unresolved C6 disagreements and accepts explicit adjudication files. All rows are synthetic controls, so C5, C6, canonicalization, promotion, and weak-accept gates must remain false.
