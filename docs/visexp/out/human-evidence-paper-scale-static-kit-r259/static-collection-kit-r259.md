# R259 Paper-Scale Static Collection Kit

Status: `paper_scale_static_collection_kit_passed`

R259 generates static paper-scale collection forms and validates synthetic export shape only.

## Outputs

- Index: `docs/visexp/out/human-evidence-paper-scale-static-kit-r259/index.html`
- Synthetic export dir: `docs/visexp/out/human-evidence-paper-scale-static-kit-r259/synthetic-exports`
- Merged C5 smoke CSV: `docs/visexp/out/human-evidence-paper-scale-static-kit-r259/synthetic-exports/user-task-response-template-r249-paper.csv`
- Browser path: `/usr/bin/google-chrome`

## Checks

- `participant_form_count`: `True`
- `participant_export_count`: `True`
- `participant_rows_ok`: `True`
- `participant_fields_ok`: `True`
- `participant_json_ok`: `True`
- `merged_output_name_ok`: `True`
- `merged_fields_ok`: `True`
- `merged_rows_ok`: `True`
- `merged_participants_ok`: `True`
- `labeler_form_count`: `True`
- `labeler_export_count`: `True`
- `labeler_fields_ok`: `True`
- `labeler_rows_ok`: `True`
- `labeler_cells_blank`: `True`
- `browser_checks_ok`: `True`
- `leak_scan_ok`: `True`
- `no_outcome_evidence_added`: `True`
- `r249_ready_no_responses`: `True`
- `r252_ready_no_labels`: `True`
- `r258_bundle_ready_no_outcomes`: `True`

## Claim Gate

- weak_accept_supported: `False`
- c5_supported: `False`
- c6_supported: `False`
- outcome_evidence_added: `False`
