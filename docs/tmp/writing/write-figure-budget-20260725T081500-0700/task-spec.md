# WRITE task: condensation pass 2 — figure budget + enumerated dedup/trim

You are an autonomous writing agent working inside
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
You may edit EXACTLY ONE file: `docs/paper/main.tex`. No git commands ever.
Never touch `docs/agentpprof-paper/`. Keep the thesis sentence, RQ titles,
all tables, and all numbers intact except the one duplicate noted in Edit 3.
Bilingual convention: moved/kept sentences keep their Chinese comments;
any rewritten sentence gets an updated Chinese comment.

## Edit 1 — shrink the two flamegraph figures (keep ALL panels)

Both `figure*` floats currently monopolize dedicated float pages. Reduce
each `\includegraphics` in `fig:flamegraph` (three panels) and
`fig:agentreward-diff` (two panels) from `.97\linewidth` to
`.78\linewidth`, keeping `\centering`. Recompile; if either float still
lands on a page with no body text, reduce that float's panels to
`.70\linewidth` (hard floor `.65`). Do NOT remove any panel: the flame
graphs must stay in the paper.

## Edit 2 — RQ2 prefix-sentence dedup (one line)

In the matched-tie paragraph, delete the now-redundant sentence
"Separately, that prefix supplies the cross-run hierarchy and source
drilldown illustrated below." (its content is covered by the two mechanism
sentences added before it). Keep everything else, including the
"Because the local-first rule..." disclosure sentence.

## Edit 3 — RQ4 506.35 dedup

The number 506.35 now appears twice in RQ4. Keep the Move-4 summary
sentence; in the older paragraph ("...Thus 1.17\,s is replay latency, not
annotation latency; the measured deterministic first-construction
components total 506.35\,s, while model/provider inference remains outside
the instrumented timing."), rewrite to end at "...not annotation latency."
and delete the duplicated 506.35 clause, keeping the final clause about
model/provider inference attached to the envelope sentence if grammatical.
Update the Chinese comment accordingly.

## Edit 4 — Background light compression (~7 lines target)

In `\subsection{LLMs and AI Agents}`: merge the four sentences into two,
preserving citations and meaning (agents interleave intent-layer prompts/
LLM calls/tools with lower-layer process/file/network effects; teams
accumulate many trajectories). In `\subsection{System Profiling}`: merge
the flame-graph/pprof sentence and the Pivot Tracing sentence into one
sentence retaining ALL citations. Do not touch
`\subsection{Challenges for Agent Profiling}` or the design-requirements
list (story spine).

## Validation and deliverables

1. `latexmk -pdf -interaction=nonstopmode main.tex`: no errors, no
   undefined refs/citations; every citation previously present still
   present (diff the `\cite` keys before/after — zero lost).
2. Report: total pages, page where References ends, and the pages of both
   flamegraph floats plus whether they share pages with body text. Target:
   References ends on page 12 or earlier.
3. Write `write-report.md` in THIS directory with before/after for each
   edit and the page layout report.
