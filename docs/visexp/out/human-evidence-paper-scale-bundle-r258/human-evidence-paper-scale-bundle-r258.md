# R258 Paper-Scale Human Evidence Bundle

Status: `paper_scale_human_evidence_bundle_ready_no_outcomes`

R258 packages the R249 C5 paper-scale participant materials and R252 C6 labeler
materials into one sendable tarball. It does not create or score outcome data.

## Package

- path: `docs/visexp/out/human-evidence-paper-scale-bundle-r258/agentflame-paper-scale-human-evidence-r258.tar.gz`
- sha256: `db654cdb78a93d00657e6fe134d22870241424ca5df9f19782606ed8b4e3e961`
- bytes: `160835`
- members: `43`

## Collection Inputs

- C5 participant packets: `12`
- C5 response rows: `168`
- C6 labeler packets: `2`
- C6 rows per labeler: `501`
- C6 required independent decisions: `1002`

## Return Files

| File | Package path | Rows | Required gate |
|------|--------------|------|---------------|
| `user-task-response-template-r249-paper.csv` | `c5/user-task-response-template-r249-paper.csv` | 168 | `yes` |
| `user-task-assignments-r249-paper.csv` | `c5/user-task-assignments-r249-paper.csv` | 168 | `yes` |
| `r124-labeler-1.csv` | `c6/L01/r124-labeler-1.csv` | 300 | `yes` |
| `r124-labeler-2.csv` | `c6/L02/r124-labeler-2.csv` | 300 | `yes` |
| `r190-labeler-1.csv` | `c6/L01/r190-labeler-1.csv` | 160 | `if claiming merge quality` |
| `r190-labeler-2.csv` | `c6/L02/r190-labeler-2.csv` | 160 | `if claiming merge quality` |
| `r203-labeler-1.csv` | `c6/L01/r203-labeler-1.csv` | 41 | `if claiming regenerated-tag promotion` |
| `r203-labeler-2.csv` | `c6/L02/r203-labeler-2.csv` | 41 | `if claiming regenerated-tag promotion` |
| `r195-inbox-template/*` | `r195-inbox-template/` | 1002 | `template only` |

## Checks

| Check | Passed |
|-------|--------|
| `r249_ready_no_responses` | `True` |
| `r252_ready_no_labels` | `True` |
| `r255_bridge_passed_no_outcomes` | `True` |
| `r257_review_gate_passed_no_outcomes` | `True` |
| `participant_packet_count` | `True` |
| `c5_response_template_rows` | `True` |
| `c5_assignment_rows` | `True` |
| `c6_packet_rows` | `True` |
| `c6_inbox_template_rows` | `True` |
| `return_checklist_rows` | `True` |
| `source_leak_scan_passed` | `True` |
| `tar_member_count_matches` | `True` |
| `tar_leak_scan_passed` | `True` |
| `no_outcome_evidence_added` | `True` |

## Claim Gate

- weak_accept_supported: `False`
- c5_supported: `False`
- c6_supported: `False`
- c6_adequacy_supported: `False`
- canonicalization_quality_supported: `False`
- long_tail_promotion_review_supported: `False`
- outcome_evidence_added: `False`
