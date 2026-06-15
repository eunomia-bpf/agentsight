# R124 Blinded Label Sheet

Date: 2026-06-15T09:44:08+00:00

This artifact is the participant-facing sheet for independent human adequacy
labels. It is derived from the R122 packet but hides model identity, model size,
stability metadata, source agent, fragment hash, and downstream result columns.

Rows: 300
Candidate tags: 300 (100.0%)

Visible fields:

- `row_id`
- `fragment_index`
- `fragment_level`
- `redacted_preview`
- `candidate_tag`
- `rubric`
- `label`
- `notes`

Hidden source fields:

- `adjudicated_label`
- `candidate_distinct_tags`
- `candidate_exact_stable`
- `candidate_model`
- `fragment_hash`
- `labeler_1`
- `labeler_2`
- `model`
- `source`
- `text_chars`

Label values:

- `adequate`
- `generic_noisy`
- `misleading`

Protocol:

1. Give a separate blank copy of `docs/visexp/out/tag-adequacy-blinded-label-sheet-r124.csv` to each
   labeler.
2. Ask labelers to fill only `label` and `notes`.
3. Freeze both completed sheets before joining labels back into the scoring
   packet.
4. Do not expose model identity, stability metadata, raw traces, or answer
   summaries during labeling.

Claim impact: this clears the R124 blinding protocol blocker, but C6 remains
partial until real labels are collected, adjudicated, and scored.
