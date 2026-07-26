# WRITE task: condensation pass 3a — Evaluation tightening + appendix moves

You are an autonomous writing agent working inside
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
Edit EXACTLY ONE file: `docs/paper/main.tex`. No git commands. Never touch
`docs/agentpprof-paper/`. Rules: keep the thesis sentence, all four RQ
titles, all tables, all figures, every number, and every `\cite` key (42
unique keys before must equal after). You may compress wording and move
enumerated blocks to the existing Technical Appendix; you may not delete
claims or evidence. Bilingual convention: rewritten sentences get updated
Chinese comments; moved sentences keep theirs.

## Move A — OSWorld-Human RQ3 sub-study prose

Keep in main text: the first sentence introducing the 287-session
population, Table `tab:rq3-boundary`, and ONE results sentence (the
"supervised predictor reaches 0.739... label-free recurrence reaches
0.680/0.786..." sentence, compressed to keep all numbers).
Move to a new appendix `\subsection{OSWorld-Human Boundary Study Detail}`
(`\label{app:osworld}`): the Bernoulli-Naive-Bayes/cross-validation setup
sentences, the fold/recurrence-reference sentences, the development-evidence
disclosure sentence, the reference-calibrated-mode sentence, and the
controls-description sentences. Add "(Appendix~\ref{app:osworld})" to the
retained intro sentence.

## Move B — TF-IDF/V-measure paragraph

Move the whole "For target-blind TF-IDF/K-Means..." paragraph to appendix
`\subsection{Partition Backends Detail}` (`\label{app:partition}`),
replaced by one sentence retaining the two V-measure numbers (0.557,
0.815) and citations, ending with "(Appendix~\ref{app:partition})".

## Tighten C — Case Study 1 prose (RQ1)

Compress the two long paragraphs around the six-way organization control
("As a post-hoc organization control, we replay..." and "Thus, the fixed
hierarchy exposes...") by merging overlapping clauses. Every number stays
(105, six kinds, 39.42%, 102/97, 21.47%, 46.15%). Target: -8 lines across
the two paragraphs.

## Tighten D — RQ2 protocol paragraphs

Compress the paragraph beginning "The main test asks whether this profile
adds information..." by removing restatement (e.g., the lexicographic rule
is stated once, not twice) while keeping the direct-diagnostic definition,
the TraceElephant-localizer disclosure, and all condition names. Target:
-5 lines.

## Tighten E — Case Study 2 opening

Compress the population-description paragraph ("We next aggregate the
complete mixed-outcome population...") keeping all counts (440, 125, 338,
24/102/144/68, 202/238). Target: -4 lines.

## Validation and deliverables

1. Compile: no errors, no undefined refs/citations; 42 unique cite keys
   preserved; thesis sentence at its three locations.
2. Report: total pages, References end page, both figure pages still
   sharing with body text. Target: References ends on page 11 or earlier.
3. `write-report.md` in THIS directory: per-edit before/after line counts,
   moved-block inventory, page layout, compile result.
