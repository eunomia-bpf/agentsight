# R207 Human Evidence Launch Readiness

Status: `launch_ready_no_outcomes`

## Scope

- Reads R187/R193/R195 generated artifacts only.
- Does not read raw agent traces.
- Does not fill labels or participant responses.
- Does not support C5/C6 outcome claims.

## Checks

| check | value |
|---|---:|
| source_files_ok | True |
| sheet_rows_blank_and_valid | True |
| response_template_blank_and_valid | True |
| participant_packets_ready | True |
| readmes_ok | True |
| r195_awaiting_inputs | True |

## Launch Units

- R142 participant packets: `5`.
- R142 response template rows: `70`.
- R124 labeler rows: `300` per sheet.
- R190 labeler rows: `160` per sheet.
- R203 labeler rows: `41` per sheet.

## Return File Plan

| R195 key | group | human file | R195 inbox name |
|---|---|---|---|
| `r142_responses` | r142 | completed copy of user-task-response-template-r142-pilot.csv | `r142-pilot-responses.csv` |
| `r124_labeler_1` | r124 | completed r124-tag-adequacy-labeler-1.csv | `r124-labeler-1.csv` |
| `r124_labeler_2` | r124 | completed r124-tag-adequacy-labeler-2.csv | `r124-labeler-2.csv` |
| `r190_labeler_1` | r190 | completed r190-merge-risk-labeler-1.csv | `r190-labeler-1.csv` |
| `r190_labeler_2` | r190 | completed r190-merge-risk-labeler-2.csv | `r190-labeler-2.csv` |
| `r203_labeler_1` | r203 | completed r203-long-tail-promotion-labeler-1.csv | `r203-labeler-1.csv` |
| `r203_labeler_2` | r203 | completed r203-long-tail-promotion-labeler-2.csv | `r203-labeler-2.csv` |

## Claim Boundary

R207 audits whether human-evidence collection files are sendable and whether returned files have an unambiguous R195 inbox mapping. It does not collect, infer, or score participant responses or human labels.

Next action: Distribute P01-P05 R142 packets and the R124/R190/R203 paired sheets; place completed returns into docs/visexp/out/human-evidence-r195/inbox using the R207 return_file_plan names, then run python3 docs/visexp/r195_human_evidence_pipeline.py.
