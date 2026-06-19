# R124 Label Join Protocol

Status: `ready_for_scoring`
Generated: 2026-06-19T08:18:09+00:00

## Inputs

- Source packet: `docs/visexp/out/tag-adequacy-label-packet-r122.csv`.
- Blinded sheet: `docs/visexp/out/tag-adequacy-blinded-label-sheet-r124.csv`.
- Labeler sheets: 2.

## Join Summary

- Rows: 300.
- Labeler 1 labels: 300.
- Labeler 2 labels: 300.
- Paired labels: 300.
- Agreements: 300.
- Disagreements: 0.
- Missing adjudications: 0.

## Protocol

1. Give two independent labelers separate copies of the blinded sheet.
2. Ask each labeler to fill only `label` and `notes`.
3. Run this join script with both frozen sheets.
4. If the status is `needs_adjudication`, fill the adjudication template and rerun.
5. Score the joined packet with `score_tag_adequacy.py --labels <joined csv>`.

Claim impact: this artifact is a protocol/scoring bridge only. C6 remains partial until scored human labels satisfy the gate.
