# WRITE report: Evaluation prose squeeze (round 2)

Task: `task-spec.md` in this directory. Edited exactly one file,
`docs/paper/main.tex`. No git commands. No writes outside the repository.
Thesis ×3 verbatim, RQ titles, all tables, all figure panels, every number,
and every cite key preserved. Rewritten sentences carry updated Chinese
%-comments. Wording compressed only.

## Validation

- Build: `cd docs/paper && latexmk -pdf -interaction=nonstopmode main.tex` —
  no errors, no undefined references, stable (no rerun requested).
- Unique cite keys: 60 before, 60 after (equal).
  Multi-line-aware count via
  `python3 -c "import re;s=open('main.tex').read();print(len(set(k for m in re.finditer(r'\\\\cite\{([^}]*)\}',s) for k in m.group(1).split(','))))"`.
- Total pages: 12 (unchanged from baseline).
- Body ends (before References): page 9 (Conclusion + References heading both
  on p9).
- References end page: 11 (appendix begins on p12).
- Total source lines: 1204 → 1198 (−6).

## Per-edit line deltas (source lines in main.tex)

| # | Edit | Before | After | Δ | Notes |
|---|------|-------:|------:|---:|-------|
| 1 | Data-classes paragraph | 13 | 11 | −2 | Four sentences fused into one semicolon-delimited sentence; all counts (41, 440, 15, 405, 20{,}866, 27{,}346, 27{,}765) and all 18 cite keys kept. |
| 2 | RQ1 opening paragraph | 10 | 10 | 0 | Five population sentences fused into two; every number kept (41, 3{,}146, 5{,}750, three, 735, 96, five, 27). Wrapped line count unchanged because the fused sentence reflows to the same ~80-char lines. |
| 3 | RQ1 tau-b paragraph | 15 | 15 | 0 | Two reading sentences ("One fixed hierarchy therefore replays…" + "The agreement is not perfect…") fused into one with "though"; all statistics (0.886, [0.857,0.915], 0.935, [0.917,0.953], 0.929, 10/77, 0.7) and both citations (\cite{kendall1938}, \cite{spearman1904}) kept. Wrapped line count unchanged. |
| 4 | Profile-guided reading paragraph | 9 | 7 | −2 | First two sentences (reader setup + full-trace baseline) fused with a semicolon; all numbers kept (220, .502, .209, .326, 12{,}615); the two corresponding Chinese %-comments merged into one. Query-specific disclosure sentence at paragraph end kept verbatim. |
| 5a | Case Study 2 population | 6 | 6 | 0 | Benchmark-count sentence fused with pair-weighting sentence ("…WorkArena), with the 202 successful and 238 unsuccessful sessions reusing…"); all numbers kept (440, 125, 338, 24/102/144/68, 202, 238). |
| 5b | Case Study 2 recovery/completion | 7 | 7 | 0 | Recovery/completion percentage sentence fused with the drilldown sentence ("…(completion: 1.8\% and 5.1\%), and the recursive recovery focus…"); count sentence ("The aggregate contains 7{,}366…3{,}780…") kept; all numbers kept (7{,}366, 3{,}780, 44.6, 12.0, 1.8, 5.1). |
| 6 | RQ3 CodeTraceBench canonicalization | 7 | 7 | 0 | Two canonicalization sentences ("The current name replay then maps…" + "It independently re-expands…") merged into one; all numbers kept (5{,}537, 1{,}434). The 5{,}752-mark count is stated once in English (with the depth breakdown 51/5{,}608/93); verified it appears exactly once in the English source, so no second occurrence needed removal. |
| 7 | RQ4 scaling-slope sentences | 4 | 4 | 0 | Two sentences ("Both time curves are monotonic…" + "The semantic curve has a descriptive slope…") fused with ", and"; slope (0.0418), R² (0.9997), throughput (23{,}935), and all overhead numbers in the following sentence (1.16, 465.2, 190, 19.6\%, 5.25, 1.14\%) kept. |
| 8a | fig:flamegraph caption | 7 | 6 | −1 | Removed restatement clause "and exposes its recursively nested hypotheses, controls, LLM calls, and tool leaves"; kept panel identification (top=count, middle=tokens, bottom=diagnose-authentication focus) and the standard-pprof clause verbatim. |
| 8b | fig:agentreward-diff caption | 7 | 6 | −1 | Removed restatement sentence "Each path descends from shared responsibilities to contributing LLM and tool calls."; kept panel identification (top: recover interaction 3{,}286/455; bottom: report completion 135/191) and the "aggregate diagnostic differences, not causal effects" disclaimer. No standard-pprof clause exists in this caption. |
| — | Architecture caption | — | — | 0 | Kept as is, per spec. |

Net source-line delta: **−6** (1204 → 1198).

## Interpretation notes

- Edits 2, 3, 5a, 5b, 6, and 7 fuse sentences but show Δ=0 source lines because
  the fused sentence reflows to occupy the same number of ~80-character wrapped
  lines. The compression is in sentence count and word count (and in removed
  restatement clauses for the captions), which is what "compress WORDING only"
  targets; source-line reduction is a secondary effect that appears only where
  it also removes a whole wrapped line (edits 1, 4, 8a, 8b).
- Total page count is unchanged (12). The squeeze created slack within pages
  rather than collapsing a page, which is consistent with a wording-only pass.
- For edit 1 ("at most 4 source lines of English"): the four original sentences
  were fused into a single semicolon-delisted sentence. The English prose
  itself is now one sentence, but it still wraps across more than four source
  lines because the mandatory inline citation list (18 keys across three
  \cite groups) forces line breaks; cutting it to literally four source lines
  is impossible without dropping or moving citations, which the spec forbids
  ("all counts and citations kept").
- For edit 4 ("first two setup sentences"): interpreted as the first two
  sentences of the paragraph (reader setup + full-trace baseline), which
  together establish the baseline; the later two-stage-variant setup sentence
  was left in place to keep its result sentence ("It reaches MAP .455…")
  adjacent to its antecedent.
