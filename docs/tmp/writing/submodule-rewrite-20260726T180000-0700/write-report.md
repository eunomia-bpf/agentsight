# Write Report

## 1. Main issues

The submodule's Design and Algorithms described the earlier flat-operation,
query-time projection model rather than the current ordered source tree,
recursive semantic annotation, retained evidence, and weighted pprof stack.
Its Implementation omitted the annotation workspace and recurrence backend and
claimed obsolete non-pprof export formats. Its Evaluation predated the current
RQ protocols, three case studies, results, tables, figures, and appendix
details.

## 2. Revision strategy

Content was transplanted from `../paper/main.tex`, preserving the paired
English sentences and Chinese `%` comments:

- Replaced the complete `Design` section, including the three-object design,
  `Semantic Operation Stack Model`, `Recursive Operation Annotation`, the
  DIRECT annotation protocol, deterministic root-prefix repair, and
  canonicalization replay summary.
- Replaced the complete `Implementation` section because the old text
  contradicted the transplanted design. The replacement includes `Input
  reconstruction`, `Annotation workspace`, `Non-LLM recurrence backend`, and
  `Profile export`.
- Replaced the complete `Evaluation` section, including the research-question
  paragraph, data classes, RQ1--RQ4 with their question titles, all three case
  studies, tables, and figure blocks.
- Appended `\clearpage\appendix` and the complete `Technical Appendix`, with
  these subsections: `Recurrence Backend Details`, `Operation-Identity
  Canonicalization`, `RQ2 Scoring Details`, `Agent-Mark Reconstruction Cost
  Detail`, `Cost Scaling Table`, `OSWorld-Human Boundary Study Detail`,
  `Partition Backends Detail`, `Literal-Label Backend Detail`, and `Extended
  Scope and Limitations`.
- Renamed only the transplanted RQ1 figure label from `fig:flamegraph` to
  `fig:rq1-flamegraph`, including its English and Chinese references, because
  the untouched Background already owns `fig:flamegraph`.

The abstract, Introduction, Background and Motivation, Related Work,
Conclusion, title, author block, and preamble were left unchanged.

## 3. Revised LaTeX and bibliography

The resulting authorized section outline in `main.tex` is:

```latex
\section{Design}
\subsection{Semantic Operation Stack Model}
\subsection{Recursive Operation Annotation}
\section{Implementation}
\section{Evaluation}
\subsection{RQ1: Does Semantic Profiling Improve Resource Attribution?}
\subsection{RQ2: Does Profiler Output Correspond to Real Problems?}
\subsection{Case Study 2: Differential Profiling at Scale}
\subsection{Case Study 3: Profiling the Agents that Built This Profiler}
\subsection{RQ3: How Accurate Are the Tags?}
\subsection{RQ4: What Is the Profiling Cost?}
\clearpage
\appendix
\section{Technical Appendix}
```

The following 20 missing bibliography entries were copied verbatim from
`../paper/references.bib` into `references.bib`:

- `agentprocessbench`
- `hintbench`
- `traceelephant`
- `bagga-baldwin-1998-entity-based`
- `rosenberg-hirschberg-2007-v-measure`
- `macqueen1967`
- `wilson1927`
- `kendall1938`
- `spearman1904`
- `mccallum-nigam-1998`
- `scienceworld`
- `qwen36`
- `agentboard`
- `bouzenia-pradel-2025-trajectories`
- `traceview-2026`
- `li2026codetracer`
- `bouma2009npmi`
- `robertson2008ap`
- `lewis2004rcv1`
- `ruokolainen2016segmentation`

Validation command:

```sh
latexmk -gg -pdf -interaction=nonstopmode main.tex
```

Validation passed with exit status 0, 0 LaTeX errors, 0 undefined citations,
0 undefined references, and 0 duplicate labels. The required thesis sentence
and all four RQ question titles are present. The generated PDF has 13 pages.

## 4. Remaining TODOs or risks

No task-blocking TODOs remain. The build reports only non-fatal underfull and
overfull box warnings. No git command was run; all source changes remain
uncommitted.
