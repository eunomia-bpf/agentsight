# WRITE report: condensation pass 2 — figure budget + enumerated dedup/trim

Target file: `docs/paper/main.tex` (only file edited). No git commands run.
Build: `latexmk -pdf -interaction=nonstopmode main.tex` → 13 pages, no errors,
no undefined refs/citations.

## Validation summary

| Check | Before | After |
|---|---|---|
| Total pages | 14 | 13 |
| References ends on page | 13 | **12** (target ≤12 met) |
| Figure 2 (`fig:flamegraph`) page | 10, dedicated float (no body) | **5, shares with body text** |
| Figure 3 (`fig:agentreward-diff`) page | 11, dedicated float (no body) | **8, shares with body text** |
| Unique `\cite` keys | 42 | 42 (zero lost) |
| Panels in `fig:flamegraph` | 3 | 3 (all kept) |
| Panels in `fig:agentreward-diff` | 2 | 2 (all kept) |
| Thesis sentence ("Agent observability needs profiling, not only debugging.") | present | present (unchanged) |
| Undefined refs/citations | 0 | 0 |

`\includegraphics` count is still 5 (3 + 2), confirming no panel was removed.

## Edit 1 — shrink the two flamegraph figures (ALL panels kept)

Both `figure*` floats were reduced from `.97\linewidth` to `.78\linewidth`,
`\centering` retained. After recompile both floats now share their page with
body text, so the hard-floor `.70`/`.65` fallback did **not** need to be
applied.

Before (`fig:flamegraph`, three panels):
```latex
\includegraphics[width=.97\linewidth]{...git-multibranch.operations.png}\\[1pt]
\includegraphics[width=.97\linewidth]{...git-multibranch.tokens.png}\\[1pt]
\includegraphics[width=.97\linewidth]{...git-authentication.tokens.png}
```
After:
```latex
\includegraphics[width=.78\linewidth]{...git-multibranch.operations.png}\\[1pt]
\includegraphics[width=.78\linewidth]{...git-multibranch.tokens.png}\\[1pt]
\includegraphics[width=.78\linewidth]{...git-authentication.tokens.png}
```

Before (`fig:agentreward-diff`, two panels):
```latex
\includegraphics[width=.97\linewidth]{...agentreward-recovery-bad-excess.operations.png}\\[2pt]
\includegraphics[width=.97\linewidth]{...agentreward-completion-good-excess.operations.png}
```
After:
```latex
\includegraphics[width=.78\linewidth]{...agentreward-recovery-bad-excess.operations.png}\\[2pt]
\includegraphics[width=.78\linewidth]{...agentreward-completion-good-excess.operations.png}
```

Page-layout effect:
- `fig:flamegraph` moved from page 10 (dedicated float page, ~457 chars:
  caption only) to page 5 (2952 chars total, ~2804 chars of body text alongside
  the figure).
- `fig:agentreward-diff` moved from page 11 (dedicated float page, ~463 chars:
  caption only) to page 8 (4493 chars total, ~4333 chars of body text alongside
  the figure).

## Edit 2 — RQ2 prefix-sentence dedup

Deleted the redundant sentence
"Separately, that prefix supplies the cross-run hierarchy and source drilldown
illustrated below." Its content is covered by the two mechanism sentences
immediately before it ("The semantic prefix's distinct, separately measured
roles are cross-run attribution (RQ1) and directing a reader's attention…").

Before:
```latex
The semantic prefix's distinct, separately measured roles are cross-run
attribution (RQ1) and directing a reader's attention, which the following
study measures.
Separately, that prefix supplies the cross-run hierarchy and
source drilldown illustrated below. Because
the local-first rule and fixed source-only paths were developed on these
populations, this is adaptive mechanism evidence rather than untouched backend
generalization.
```
After:
```latex
The semantic prefix's distinct, separately measured roles are cross-run
attribution (RQ1) and directing a reader's attention, which the following
study measures.
Because
the local-first rule and fixed source-only paths were developed on these
populations, this is adaptive mechanism evidence rather than untouched backend
generalization.
```

The "Because the local-first rule…" disclosure sentence is retained as
required.

## Edit 3 — RQ4 506.35 dedup

The number 506.35 appeared twice in RQ4. The Move-4 summary sentence at the
start of the RQ4 results ("Deterministic A2 first-construction components
total 506.35\,s on all 405 sessions…") is kept. The later occurrence in the
older "two disjoint workflow waves" paragraph was rewritten to end at
"…not annotation latency." and the duplicated 506.35 clause was deleted,
with the model/provider-inference clause reattached to the envelope sentence.
Chinese comment updated accordingly. Verified: `506.35` now appears exactly
once in body text (line 1049) plus its matching Chinese comment.

Before:
```latex
…Thus 1.17\,s is replay latency,
not annotation latency; the measured deterministic first-construction
components total 506.35\,s, while model/provider inference remains outside the
instrumented timing.
% …因此 1.17 秒是 replay 而非 annotation latency，deterministic first-construction 组件合计 506.35 秒。
```
After:
```latex
…Thus 1.17\,s is replay latency,
not annotation latency, while model/provider inference remains outside the
instrumented timing.
% …因此 1.17 秒是 replay 而非 annotation latency，而 model/provider inference 仍在插桩计时之外。
```

## Edit 4 — Background light compression

### `\subsection{LLMs and AI Agents}`

Four sentences merged into two, preserving all citations
(`sweagent,codex,claudecode,agentsight` and `agentsight`) and meaning
(intent-layer prompts/LLM-calls/tools interleaved with lower-layer
process/file/network effects; teams accumulate many trajectories). Story
spine (Challenges subsection and design-requirements list) untouched.

Before (4 sentences):
```latex
A typical agent trajectory interleaves two layers of
activity~\cite{sweagent,codex,claudecode,agentsight}.
At the intent layer, an agent receives prompts, issues LLM calls, and invokes
tools for code execution, search, and file editing.
Tool invocations trigger lower-layer process, file, and network
effects~\cite{agentsight}. Trajectories repeat this cycle, and teams accumulate
many trajectories.
```
After (2 sentences):
```latex
A typical agent trajectory interleaves intent-layer activity (prompts, LLM
calls, and tool invocations for code execution, search, and file editing) with
lower-layer process, file, and network
effects~\cite{sweagent,codex,claudecode,agentsight}.
Trajectories repeat this cycle, and production teams accumulate many
trajectories~\cite{agentsight}.
```
(Chinese comments updated to match the rewritten sentences.)

### `\subsection{System Profiling}`

The flame-graph/pprof clause and the Pivot Tracing clause merged into one
tight sentence retaining ALL citations (`flamegraphs`, `pprof`, `pivottracing`).
Other sentences (the "Unlike single-execution debugging…" opener, the
"Traditional profilers sample execution…" sentence, the `tagroot`/`tagleaf`
sentence, and the "Agent profiles must instead…" closer) were not touched.

Before:
```latex
Flame graphs~\cite{flamegraphs} and pprof~\cite{pprof} call graphs visualize
aggregate cost by width or node size, while Pivot Tracing~\cite{pivottracing}
dynamically selects and groups measurements across causally related events.
```
After:
```latex
Flame graphs~\cite{flamegraphs} and pprof~\cite{pprof} call graphs visualize
aggregate cost by width or node size, and Pivot Tracing~\cite{pivottracing}
groups causally related measurements.
```
(Chinese comment updated.)

## Page-layout report (final)

- **Total pages:** 13 (was 14)
- **References starts:** page 10 (header appears at top of a column after the
  Related Work body text)
- **References ends:** page 12 (last entry: Zhong, Z.; Saxena, S.; and
  Raghunathan, A. 2026. Hodoscope… arXiv:2604.11072.) — meets the "≤12" target.
- **Figure 1 (`fig:architecture`):** page 4, shares page with body text
  (unchanged from baseline).
- **Figure 2 (`fig:flamegraph`):** page 5, shares page with body text
  (~2804 body chars alongside the three flamegraph panels). Previously a
  dedicated float page with no body text.
- **Figure 3 (`fig:agentreward-diff`):** page 8, shares page with body text
  (~4333 body chars alongside the two differential panels). Previously a
  dedicated float page with no body text.
- **Appendix (`\section{Technical Appendix}`):** starts page 13.

## Citations preserved

Diffed the set of `\cite` keys before/after: 42 unique keys both before and
after, identical set, zero lost.
