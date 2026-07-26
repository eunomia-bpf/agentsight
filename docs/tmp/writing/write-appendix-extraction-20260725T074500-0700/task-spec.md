# WRITE task: condensation pass 1 — appendix extraction (pure moves)

You are an autonomous writing agent working inside
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
You may edit EXACTLY ONE file: `docs/paper/main.tex`. No git commands ever.
Never touch `docs/agentpprof-paper/`. This pass MOVES text; it must not
change, add, or delete any number, claim, table, or figure. Every sentence
you move keeps its Chinese `%`-comment line with it. Every summary sentence
you write gets a new Chinese comment line. The thesis sentence and all RQ
titles stay untouched.

Goal: AAAI-27 allows 7 pages of main content; the main body must shrink.
Create a technical appendix at the end of the document:
after the bibliography command block, add
`\clearpage \appendix \section{Technical Appendix}` with the subsections
below, and move the enumerated blocks there verbatim.

## Moves (enumerated; keep order)

1. **Recurrence backend math** (Implementation, paragraph "Non-LLM
   recurrence backend" and the following paragraph "An optional
   reference-calibrated recurrence mode..."): move BOTH paragraphs to
   appendix subsection `\subsection{Recurrence Backend Details}`. Replace
   in place with two sentences: the inducer scores adjacent action
   transitions by normalized pointwise mutual information and calibrates a
   label-free cutoff with occurrence-weighted two-means, treating detailed
   action recurrence as continuity that can remove but never add a coarse
   boundary~\cite{bouma2009npmi,macqueen1967}; an optional
   reference-calibrated mode fits one scalar cutoff on disjoint reference
   groups (Appendix ref).
2. **A2 name canonicalization mechanics** (Design, paragraph beginning
   "Before folding, one fixed source-only action--object map
   canonicalizes..."): move the whole paragraph to appendix subsection
   `\subsection{Operation-Identity Canonicalization}`. Replace with one
   sentence: a fixed source-only action--object map canonicalizes display
   identities (5{,}537 open-vocabulary names to 1{,}434 two- or three-word
   IDs with zero adjacent collision) while preserving every temporal mark
   (Appendix ref).
3. **RQ2 scoring mechanics** (Evaluation RQ2): move the sentence pair about
   HINTBench's released snapshot and validation field-order selection, and
   the sentences describing the Wilson lower bound scoring
   ("AgentProcessBench averages judge votes... maximum score over prefixes
   containing it.") to appendix subsection `\subsection{RQ2 Scoring
   Details}`. Replace with one sentence: group scores aggregate frozen
   benchmark-judge predictions per operation group (Wilson lower bound for
   HINTBench/TraceElephant; vote averaging for
   AgentProcessBench)~\cite{wilson1927}, with snapshot details in the
   appendix.
4. **RQ4 A2 reconstruction detail** (RQ4, paragraph "We then reconstruct
   the adopted A2 path three times..."): move the full paragraph to
   appendix subsection `\subsection{A2 Reconstruction Cost Detail}`;
   replace with one sentence keeping only: deterministic A2
   first-construction components total 506.35\,s on all 405 sessions, and
   both profile widths replay in 1.17\,s median with byte-identical
   artifacts (Appendix ref).
5. **Scope and Limitations**: keep the first sentence and the RQ4
   exclusions sentence; move the rest verbatim to appendix subsection
   `\subsection{Extended Scope and Limitations}`.

Use `\ref{...}` with labels you add on the appendix subsections for every
"(Appendix ref)" mention.

## Validation and deliverables

1. `cd docs/paper && latexmk -pdf -interaction=nonstopmode main.tex` — no
   errors, no undefined references/citations.
2. Report page count of the PDF and, separately, the page on which the
   References section ends (the main-body boundary). The main body must
   end at least one page earlier than before the pass (baseline: 13 total).
3. Verify: every moved number appears exactly once in the document (moved,
   not duplicated or lost) — spot-check 5,537/1,434, 506.35, Wilson, NPMI.
4. Write `write-report.md` in THIS directory: list of moves with
   before/after locations, the summary sentences inserted, page numbers,
   compile result.
