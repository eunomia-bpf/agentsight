# WRITE report — condensation pass 3a (Evaluation tightening + appendix moves)

File edited: `docs/paper/main.tex` (only file touched). No git commands run.
Baseline: 13 pages, References ending on page 12. After: 12 pages, References
ending on page 11.

## Invariants verified

- Compile: clean. No LaTeX errors, **0** undefined refs/citations, **0**
  overfull hboxes.
- Unique `\cite` keys: **42 before = 42 after** (actonomy2026 … wilson1927).
- Thesis sentence ("Agent observability needs profiling, not only debugging.")
  present at all **3** locations (abstract, intro, conclusion).
- All four RQ subsection titles, all tables (`tab:rq2-localization`,
  `tab:rq3-codetrace`, `tab:rq3-boundary`, `tab:rq4-cost`), and all figures
  (`fig:architecture`, `fig:flamegraph`, `fig:agentreward-diff`) preserved.
- No claim or number deleted; moved sentences retain their Chinese comments,
  rewritten sentences got updated Chinese comments.

## Per-edit before/after source-line counts

### Move A — OSWorld-Human RQ3 sub-study prose
- Main-text intro block (setup + fold/recurrence + dev-evidence +
  reference-calibrated + controls): **27 → 4 lines**. Retained: 287-session
  population intro with added `(Appendix~\ref{app:osworld})`, Table
  `tab:rq3-boundary`, and one compressed results sentence.
- Results sentence: **6 → 6 lines** (wording compressed; all eight numbers
  kept verbatim: 0.739, 0.816, 0.645, 0.678, 0.680, 0.786, 0.734, 0.801).
- New appendix `\subsection{OSWorld-Human Boundary Study Detail}`
  (`\label{app:osworld}`): **+26 lines** receiving the five moved blocks.

### Move B — TF-IDF/V-measure paragraph
- Main text: **7 → 2 lines**. Replaced by one sentence keeping both V-measure
  numbers (0.557, 0.815) and both citations
  (`rosenberg-hirschberg-2007-v-measure`, `mind2web,scienceworld`), ending with
  `(Appendix~\ref{app:partition})`.
- New appendix `\subsection{Partition Backends Detail}`
  (`\label{app:partition}`): **+12 lines** receiving the full moved paragraph.

### Tighten C — Case Study 1 six-way control (RQ1)
- Two paragraphs ("As a post-hoc organization control…" + "Thus, the fixed
  hierarchy exposes…"): **20 → 11 English lines** (**−9**, target −8).
  Merged by collapsing the native/coarse finding clauses and dropping the
  restated "one fifth by count / nearly half by tokens" and "did not establish
  the requested terminal condition" clauses (those claims/numbers remain in the
  preceding paragraph: 21.47%/46.15% and the git@localhost terminal condition).
  Every retained number kept: 105, six coarse action kinds, 39.42%, 102/97.

### Tighten D — RQ2 protocol paragraph
- "The main test asks whether this profile adds information…": **15 → 10 lines**
  (**−5**, target −5). Merged topic + direct-diagnostic definition +
  TraceElephant-localizer disclosure; stated the lexicographic rule once; kept
  all four condition names (Direct+AgentProf, Direct-only, Direct+Raw+Evidence,
  AgentProf-only) and the information-matched raw-action suffix detail.

### Tighten E — Case Study 2 opening
- "We next aggregate the complete mixed-outcome population…": **8 → 4 English
  lines** (**−4**, target −4). Used slash-grouped per-dataset counts. All counts
  kept: 440, 125, 338, 24/102/144/68, 202/238; anti-cherry-picking claim and
  pair-occurrence-weighting conclusion retained.

## Moved-block inventory

To `\subsection{OSWorld-Human Boundary Study Detail}` (`app:osworld`):
1. Bernoulli Naive Bayes / session-held-out cross-validation setup sentences.
2. Fold / label-free recurrence-reference sentences (predicted boundaries →
   group field; five folds; coarse-arm fallback).
3. Development-evidence disclosure sentence (recurrence rule designed after
   inspection → development evidence, not independent confirmation).
4. Reference-calibrated-mode sentence (training ops + group annotations fit one
   NPMI cutoff).
5. Controls-description sentences (always-boundary / action-change / phase-change
   controls; per-operation B³ partition F1).

To `\subsection{Partition Backends Detail}` (`app:partition`):
6. Full target-blind TF-IDF/K-Means paragraph (V-measure over operation
   assignments; 100% coverage; constant-tag baseline).

Both appendix subsections placed after `A2 Reconstruction Cost Detail` and
before `Extended Scope and Limitations`. The `(Appendix~\ref{…})` refs render
consistently with the three pre-existing appendix refs already in the file
(`app:canonicalization`, `app:recurrence`, `app:a2-reconstruction`) — the
anonymous-submission style leaves appendix subsections unnumbered, so no `??`
appears.

## Page layout

| Item | Before | After |
|---|---|---|
| Total pages | 13 | **12** |
| References end page | 12 | **11** (target ≤ 11) |
| Figure 2 (`fig:flamegraph`) page | 5 | 5 (shares body text) |
| Figure 3 (`fig:agentreward-diff`) page | 8 | 8 (shares body text) |
| Technical Appendix start page | 13 | 12 |

## Compile result

`pdflatex` ×3 + `bibtex` clean: no errors, no undefined references/citations,
0 overfull hboxes. 42 unique cite keys and the thesis sentence at its three
locations confirmed after the pass.
