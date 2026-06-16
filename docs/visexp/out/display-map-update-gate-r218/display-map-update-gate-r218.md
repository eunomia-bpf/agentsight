# R218 Display-Map Update Gate

Status: `display_map_update_gate_ready_synthetic_review_only`

## Boundary

- Reads generated R209 display-map artifacts only.
- Uses synthetic review fixtures over real R209 candidate rows.
- Previews a reviewed display-map diff but does not update the canonical map.
- Rejects unclear, weak, hidden-`other`, and missing-source promotion rows.
- Does not prove merge quality, regenerated-label quality, semantic adequacy, developer utility, or community adoption.

## Summary

| field | value |
|---|---:|
| fixture rows | 6 |
| accepted diff rows | 2 |
| rejected rows | 4 |
| preview changed rows | 2 |
| support preserved | True |
| raw key coverage preserved | True |
| hidden other rows | 0 |

## Accepted Preview Diff

| case | dimension | raw tag | from | to | support |
|---|---|---|---|---|---:|
| accept_reviewed_profile_merge | llm | `analyzedocs` | `analyzedocs` | `analyze` | 1 |
| accept_reviewed_llm_regeneration | llm | `bpfanalyze` | `bpfanalyze` | `analyze` | 6 |

## Rejected Rows

| case | reason |
|---|---|
| reject_unclear_profile_merge | review_not_final_consensus_or_adjudicated_promote |
| reject_single_label_regeneration | review_not_final_consensus_or_adjudicated_promote |
| reject_hidden_other_bucket | invalid_or_forbidden_display_tag |
| reject_missing_source_row | missing_source_row |

## Claim Boundary

R218 supports a reviewed display-map update gate: active display membership can change only in a preview diff when promotion rows are final and reviewed, while unsafe rows remain pending. It does not support any claim that the accepted fixture labels are semantically correct.
