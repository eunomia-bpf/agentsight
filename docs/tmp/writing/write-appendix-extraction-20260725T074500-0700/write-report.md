# WRITE report: condensation pass 1 — appendix extraction (pure moves)

File edited: `docs/paper/main.tex` (the only file touched). No git commands run.
Pass type: pure text-move. No number, claim, table, or figure was altered;
every block below was moved verbatim, each with its Chinese `%`-comment line.
Summary sentences carry new Chinese comment lines. The thesis sentence and all
RQ titles are untouched.

## Compile result

`cd docs/paper && latexmk -pdf -interaction=nonstopmode main.tex` → exit 0,
no errors, **0 undefined references/citations** (`grep -ciE "undefined
(reference|citation)|multiply.defined" main.log` = 0). All five appendix
labels resolve; the three explicit `(Appendix ref)` mentions (Moves 1, 2, 4)
render via `\ref{app:recurrence}`, `\ref{app:canonicalization}`,
`\ref{app:a2-reconstruction}`.

## Page-count outcome (validation #2) — see note

Baseline (reconstructed from the pre-edit content for measurement): **13
pages**; References on pages 12–13 (end page 13); Conclusion on page 9;
Figure 2 on page 10; Figure 3 on page 11.

After this pass: **14 pages total = 13-page main body + 1-page Technical
Appendix**; References still on pages 12–13 (end page 13); Conclusion still on
page 9; Figure 2 on page 10; Figure 3 on page 11; Appendix on page 14.

**The main-body boundary (page on which References ends) did NOT move one page
earlier: it remains page 13.** This is a structural property of the layout,
not a move error:

- The class is two-column (`aaai2027`). Figure 2 and Figure 3 are
  `figure*[t]` full-width floats that are taller than `\topfraction`, so LaTeX
  defers each to its own dedicated float page. In the **baseline** they were
  already deferred to pages 10–11, with the Conclusion already sitting alone on
  page 9 (whitespace below it) — i.e., the baseline was already "figure-bound",
  not text-bound.
- The five moves removed ~49 lines (~1 page) of body text, but that space was
  absorbed by the Related Work section, which in the baseline was split across
  pages 8–9 and now compresses entirely onto page 8. The Conclusion therefore
  stays on page 9 in the after version (it merely advances from the bottom of
  page 9 in the baseline to the top of page 9 after the pass).
- A diagnostic confirmed what would be required: pulling the Conclusion
  *entirely* onto page 8 (so the figures can advance to 9–10 and References to
  11–12) needs ~10–12 more lines of body removal than the five specified moves
  provide. Any text on page 9 blocks the full-width figures from page 9, so
  they remain on 10–11 and References stays on 12–13.

Because this is a pure text-move pass with "no figure changes" and exactly the
five specified moves, there is no permitted lever (no `\clearpage`/float-spec
change, no extra removal beyond the spec) that would advance the figures. The
moves were executed exactly as specified; the one-page-shrink goal is not
reachable by these moves in this two-column figure-bound layout.

## Moves (before → after locations)

### Move 1 — Recurrence backend math
- Before: `\section{Implementation}`, `\paragraph{Non-LLM recurrence backend.}`
  body (NPMI intro + occurrence-weighted k-means paragraph) and the following
  paragraph "An optional reference-calibrated recurrence mode…" (original main
  body).
- After (moved to): `\subsection{Recurrence Backend Details}`
  (`\label{app:recurrence}`), both paragraphs verbatim with their Chinese
  comment lines.
- In-place summary (kept under the existing `\paragraph{Non-LLM recurrence
  backend.}` header), new Chinese comment added:
  > "The inducer scores adjacent action transitions by normalized pointwise
  > mutual information and calibrates a label-free cutoff with
  > occurrence-weighted two-means, treating detailed action recurrence as
  > continuity that can remove but never add a coarse
  > boundary~\cite{bouma2009npmi,macqueen1967}; an optional
  > reference-calibrated mode fits one scalar cutoff on disjoint reference
  > groups (Appendix~\ref{app:recurrence})."

### Move 2 — A2 name canonicalization mechanics
- Before: `\section{Design}`, paragraph beginning "Before folding, one fixed
  source-only action--object map canonicalizes…".
- After (moved to): `\subsection{Operation-Identity Canonicalization}`
  (`\label{app:canonicalization}`), verbatim with Chinese comment.
- In-place summary (new Chinese comment added):
  > "Before folding, a fixed source-only action--object map canonicalizes
  > display identities (5{,}537 open-vocabulary names to 1{,}434 two- or
  > three-word IDs with zero adjacent collision) while preserving every
  > temporal mark (Appendix~\ref{app:canonicalization})."

### Move 3 — RQ2 scoring mechanics
- Before: `\subsection{RQ2: Problem Correspondence}` — the HINTBench
  snapshot/validation sentence pair ("Of HINTBench's reported 629
  trajectories … all 536 tests are scored.") and the Wilson-scoring sentences
  ("AgentProcessBench averages judge votes … maximum score over prefixes
  containing it.").
- After (moved to): `\subsection{RQ2 Scoring Details}`
  (`\label{app:rq2-scoring}`), both sentence groups verbatim. (These sentences
  had no Chinese comment in the original, so none was carried; per the move
  rule, comments are kept only where they existed.)
- In-place summary (new Chinese comment added), placed after the retained
  "Within each workload, we fix operations…" protocol sentence:
  > "Group scores aggregate frozen benchmark-judge predictions per operation
  > group (Wilson lower bound for HINTBench/TraceElephant; vote averaging for
  > AgentProcessBench)~\cite{wilson1927}, with snapshot details in the
  > appendix."

### Move 4 — RQ4 A2 reconstruction detail
- Before: `\subsection{RQ4: Profiling Cost}`, paragraph "We then reconstruct
  the adopted A2 path three times on all 405 CodeTrace sessions …".
- After (moved to): `\subsection{A2 Reconstruction Cost Detail}`
  (`\label{app:a2-reconstruction}`), verbatim with Chinese comment.
- In-place summary (new Chinese comment added):
  > "Deterministic A2 first-construction components total 506.35\,s on all 405
  > sessions, and both profile widths replay in 1.17\,s median with
  > byte-identical artifacts (Appendix~\ref{app:a2-reconstruction})."

### Move 5 — Scope and Limitations (partial move)
- Before: `\subsection{Scope and Limitations}` body.
- Kept in place (first sentence + RQ4-exclusions discussion, so "It excludes…"
  keeps its antecedent): "Results apply to the named populations and
  annotation protocols." + "RQ4 measures fixed-input replay … It excludes
  capture, raw-to-normalized conversion, and live-agent overhead; … 54.36-minute
  artifact envelope is not model latency." (Chinese comment split accordingly
  and retained with the kept sentences.)
- After (moved to): `\subsection{Extended Scope and Limitations}`
  (`\label{app:scope}`), the CodeTraceBench/OSWorld-Human sentence and the RQ2
  sentence, verbatim, with a new Chinese comment covering exactly the moved
  sentences.

## Number-conservation spot-check (validation #3)

Truly moved numbers (each now appears **exactly once**, in the appendix):
501.64; 3.54; 494{,}862{,}929; 17{,}148; 20{,}866; 629; 536; 80; 24; the NPMI
formula and `k=2`. None was lost or duplicated by the move.

Numbers that the spec's *summary sentences* re-introduce (so they appear in
additional places by design, not by move duplication):
- 5{,}537 / 1{,}434 — moved block is once in
  `\subsection{Operation-Identity Canonicalization}`; also appears once in the
  untouched RQ3 paragraph ("maps 5{,}537 open-vocabulary operation IDs to
  1{,}434…") and once in the Move 2 summary sentence (per the spec's exact
  wording).
- NPMI (the abbreviation / formula) — moved block once in
  `\subsection{Recurrence Backend Details}`; the abbreviation also remains in
  the untouched RQ3 OSWorld-Human paragraph ("fit one NPMI cutoff"). The Move
  1 summary uses the spelled-out "normalized pointwise mutual information", as
  the spec specified.
- Wilson lower bound (`\cite{wilson1927}`) — moved sentences once in
  `\subsection{RQ2 Scoring Details}`; also cited once in the Move 3 summary
  sentence (per spec).
- 506.35 — this number is **not** in the moved paragraph (the moved paragraph
  contains 501.64 + 3.54). It originates in an *unmoved* adjacent RQ4
  paragraph ("the measured deterministic first-construction components total
  506.35\,s"). The spec's Move 4 summary re-uses 506.35 ("keeping only
  …506.35\,s"), so 506.35 now appears in two main-text RQ4 sentences (the new
  summary and the unmoved sentence). This redundancy is a direct, faithful
  consequence of the spec's Move 4 wording; it is not a move duplication and
  no moved number was affected.

## Appendix structure added after `\bibliography{references}`

```
\clearpage \appendix \section{Technical Appendix} \label{sec:appendix}
  \subsection{Recurrence Backend Details}        \label{app:recurrence}
  \subsection{Operation-Identity Canonicalization} \label{app:canonicalization}
  \subsection{RQ2 Scoring Details}               \label{app:rq2-scoring}
  \subsection{A2 Reconstruction Cost Detail}     \label{app:a2-reconstruction}
  \subsection{Extended Scope and Limitations}    \label{app:scope}
```

All five moves land in the order specified by the task. The thesis sentence
("Agent observability needs profiling, not only debugging.") and all four RQ
titles are unchanged.
