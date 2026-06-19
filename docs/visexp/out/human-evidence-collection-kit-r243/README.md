# R243 Static Human-Evidence Collection Kit

Status: `collection_kit_ready_no_outcomes`

Open `index.html` directly in a browser. The pages are static HTML files and need no server.

## Scope

- Wraps existing blinded R142/R124/R190/R203 materials in local forms.
- Exports CSV files that match the R195 inbox naming contract.
- Does not create participant responses, human labels, or claim support.

## Participant Collection

Send each participant only their matching form:

- `P01`: `participants/P01.html` exports `r142-pilot-responses-P01.csv`
- `P02`: `participants/P02.html` exports `r142-pilot-responses-P02.csv`
- `P03`: `participants/P03.html` exports `r142-pilot-responses-P03.csv`
- `P04`: `participants/P04.html` exports `r142-pilot-responses-P04.csv`
- `P05`: `participants/P05.html` exports `r142-pilot-responses-P05.csv`

After all five participant exports return, open the coordinator merge page and export one `r142-pilot-responses.csv`:

- `coordinator/r142-merge.html` exports `r142-pilot-responses.csv`

Place the merged file in `docs/visexp/out/human-evidence-r195/inbox/`.

## Label Collection

Send paired labeler sheets independently:

- `labelers/r124-labeler-1.html` exports `r124-labeler-1.csv`
- `labelers/r124-labeler-2.html` exports `r124-labeler-2.csv`
- `labelers/r190-labeler-1.html` exports `r190-labeler-1.csv`
- `labelers/r190-labeler-2.html` exports `r190-labeler-2.csv`
- `labelers/r203-labeler-1.html` exports `r203-labeler-1.csv`
- `labelers/r203-labeler-2.html` exports `r203-labeler-2.csv`

Place completed labeler exports in `docs/visexp/out/human-evidence-r195/inbox/` using the exported filenames.

## Scoring

After returns are frozen, run:

```bash
python3 docs/visexp/r195_human_evidence_pipeline.py
```

R243 itself is not outcome evidence. C5/C6 remain unsupported until real completed files score through R195.
