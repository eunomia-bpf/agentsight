# Round 8 — Terminology and Claim Tone

- Reviewer: independent subagent, read-only
- Reviewer method: complete-paper terminology, jargon, naming, abbreviation, and evidence-tone review using `check-terminology-infoflow` plus `paper-writing-style`
- Scope contract: preserve exact thesis, four RQs, positive story, all evidence, and strongest evidence-faithful claims

## Independent verdict

MUST-FIX LOCALLY. Core concept count, system/component naming, thesis, RQs, positive framing, and quantitative claims were sound. Two load-bearing terms were undefined or broader than the exact measurement.

## Must-fix actions

1. **Defined `raw action`.**
   - RQ2 now states that the raw-action baseline uses the released action as its sole grouping field while retaining the same step signal, ranking procedure, and scorer.
   - RQ4 now states that the raw-action cost control uses action as its sole stack field while holding the input and full parsing/folding/serialization path constant.
   - All existing positive AP, inspection-work, time, and memory comparisons remain unchanged.
2. **Replaced `mass/lossless` with the exact strong measurement.**
   - Headline text now says \sys preserves all 1,520 effects and the total weight of each of five manifest-defined task categories.
   - RQ1 uses `total weight`, `input weight`, and `all attributed weight`.
   - Removed `lossless semantic folding`, which could imply preservation beyond the tested effect counts and weights, and replaced it with `semantic folding that preserves all attributed weight`.

## Should-fix actions

- Recast the current-tool contrast in terms of standard interfaces, run-local structure, application-supplied tags, recurring semantic categories, linked effects, and query-time profile hierarchies. The contrast remains direct and strong.
- Standardized the manipulated RQ1 experiment as `tag-axis ablation`.
- Reserved `tag` for \sys-produced fields and `annotation`/`evaluation target` for benchmark truth; used `pprof label` for the native pprof mechanism.
- Defined `target-blind` at RQ2 entry and replaced its earlier Introduction use with `constructed without access to evaluation targets`.
- Replaced one-off phrases with `benchmark's original step order`, `path with scoped source lineage`, and responsibility views at multiple granularities/weight functions.
- Kept claim tone strong but exact:
  - the $p=0.001$ test `rejects random prompt-tag assignment as an explanation`;
  - the $p=0.00995$ test `rejects subgroup count alone as an explanation`;
  - multi-weight evidence exposes `distinct resource hotspots` rather than an undefined generic bottleneck.
- Restored full benchmark names in the RQ2/RQ4 tables. The RQ2 caption explicitly defines Work@80 and Work@50 to fit the single-column table.
- Standardized `fixed suite of 20 real Codex tasks`.
- Expanded extended Berkeley Packet Filter (eBPF) for the cross-domain audience.

## Consider disposition

- Expanded command-line interface (CLI).
- Defined JSONL as line-delimited JSON at first figure-caption use.
- Removed uninformative `ordinary` from group fields.
- Standardized attributive `system-effect layer`; plural `system effects` remains the event noun.
- Retained the compact `B$^3$ F1` table header because the immediately preceding caption defines the full `operation-weighted B$^3$ partition F1` name and the compact header avoids table-width pressure.

## Preservation audit

- Exact thesis and four RQs unchanged.
- RQ1 remains a positive cumulative answer.
- No claim was narrowed or retracted.
- No number, comparison, dataset, metric, baseline outcome, mechanism, or experimental condition changed.
- Real/public workloads and external annotations remain explicit.
- Citation commands remain 52.

## Build verification

- `git diff --check`: clean.
- `make` and final `pdflatex` completed.
- PDF: 9 pages total (7 content plus 2 references).
- Abstract: 244 prose words and eight role-mapped sentences.
- Undefined citations/references: 0.
- Overfull boxes: 0 in final pass.
- Exit `main.tex` SHA-256: `8bb4205446f34a9d717ad9fc9b3ac37717bc5cea942a729e576db16fb5510de6`.
- Exit `main.pdf` SHA-256: `e258bf2af87f9e85ef393d858f6456f4fb1b309c935cb623cc9d9206e6ed2232`.

## Round decision

PASS after local fixes. Proceed serially to the final flow-and-polish round.
