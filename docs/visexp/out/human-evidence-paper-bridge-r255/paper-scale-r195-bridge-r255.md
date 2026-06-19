# R255 Paper-Scale R195 Bridge

Status: `passed`

R255 verifies that the R249 paper-scale blank response template can be
processed by R195 only when the R249 assignment file is supplied. It also
checks that using the older R142 assignment fails instead of silently
scoring the wrong study design.

## Gates

| Gate | Passed |
|---|---:|
| `r249_manifest_present` | `True` |
| `r249_has_12_participant_packets` | `True` |
| `r249_template_has_168_rows` | `True` |
| `paper_assignment_case_r195_ok` | `True` |
| `paper_assignment_case_scored_no_supported_gate` | `True` |
| `paper_assignment_r142_empty` | `True` |
| `paper_assignment_scorer_ok` | `True` |
| `paper_assignment_uses_r249_assignments` | `True` |
| `paper_assignment_c5_false` | `True` |
| `paper_assignment_blank_not_human_evidence` | `True` |
| `wrong_assignment_case_r195_ok` | `True` |
| `wrong_assignment_case_failed` | `True` |
| `wrong_assignment_scorer_rejected` | `True` |
| `wrong_assignment_uses_r142_assignments` | `True` |
| `wrong_assignment_c5_false` | `True` |

## Case Summary

- Paper assignment case: `scored_human_inputs_no_supported_gate`.
- Wrong assignment case: `scoring_failed`.

## Boundary

R255 proves only that the R249 paper-scale blank response template is wired to R195 when the R249 assignment file is supplied, and that the old R142 assignment is rejected. It records zero real participant responses and cannot support C5 or weak accept.
