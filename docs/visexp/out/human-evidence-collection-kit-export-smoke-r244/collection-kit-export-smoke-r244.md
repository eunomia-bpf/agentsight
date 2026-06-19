# R244 Collection Kit Export Smoke

Status: `collection_kit_export_smoke_passed`

R244 validates static form loading and CSV export shape only. It is not human evidence.

## Checks

- `participant_export_count`: `5`
- `participant_rows_ok`: `True`
- `participant_fields_ok`: `True`
- `participant_json_ok`: `True`
- `merged_output_name_ok`: `True`
- `merged_fields_ok`: `True`
- `merged_rows_ok`: `True`
- `merged_participants_ok`: `True`
- `labeler_export_count`: `6`
- `labeler_fields_ok`: `True`
- `labeler_rows_ok`: `True`
- `labeler_cells_blank`: `True`
- `browser_checks_ok`: `True`
- `leak_scan_ok`: `True`

## Outputs

- Merged R142 smoke CSV: `docs/visexp/out/human-evidence-collection-kit-export-smoke-r244/synthetic-exports/r142-pilot-responses.csv`
- Browser path: `/usr/bin/google-chrome`

All synthetic exports stay under the R244 output directory and are not placed in the R195 inbox.
