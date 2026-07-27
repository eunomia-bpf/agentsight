# WRITE report: round-2 review fixes

Target file edited: `docs/paper/main.tex` (only file modified).
Validation: `latexmk -pdf` clean → `main.pdf` (15 pages), zero `^!` errors,
zero undefined-reference warnings, zero "Section ." artifacts in
`pdftotext` output. Thesis sentence "Agent observability needs profiling, not
only debugging." still appears 3× (lines 44, 144, 1146). RQ titles unchanged.
62 `\cite{...}` keys unchanged (none edited, no citation warnings).

## Edit 1 — Broken section refs

Replaced every `Section~\ref{sec:...}` (the class does not number sections, so
these rendered empty) with the section's name, and updated the matching
Chinese comment text.

| Location | Before | After |
| --- | --- | --- |
| Background ¶4 (line ~303) | `Section~\ref{sec:eval} measures this case` | `The Evaluation section measures this case` |
| Case Study 1 (line ~598) | `the case previewed in Section~\ref{sec:background}` | `the case previewed in the Background and Motivation section` |
| Case Study 1 results (line ~630) | `described in Section~\ref{sec:background}` | `described in the Background and Motivation section` |

Chinese comments on the same three lines: `第~\ref{sec:eval} 节` → `评估章节`,
`第~\ref{sec:background} 节预览` → `背景与动机章节预览`, `第~\ref{sec:background} 节描述` →
`背景与动机章节描述`. `rg "Section~\\ref\{sec"` on `main.tex` now returns no
matches; `pdftotext` no longer contains "Section ." or "Section ,".

## Edit 2 — Name consistency

`rg -n "AgentPProf" main.tex` originally returned exactly one prose/caption
hit (the `Figure~\ref{fig:flamegraph}` caption). Bibliography keys live in
`references.bib`, which was not touched.

| Location | Before | After |
| --- | --- | --- |
| Fig.2 caption (line ~612) | `AgentPProf emits only standard pprof` | `\sys emits only standard pprof` |

`rg "AgentPProf" main.tex` now returns zero matches.

## Edit 3 — Over-segmentation sentence (RQ3)

Replaced the clause exactly as specified, inside the existing boundary-error
sentence on lines 977–982, and updated the Chinese comment.

Before (clause):

> ... precision 0.389), the benign direction for profiling because extra
> splits subdivide work without merging unrelated responsibilities, as the
> 0.793 B$^3$ precision confirms. Thus the direct Agent backend is the ...

After (clause):

> ... precision 0.389), so the error therefore skews toward extra splits:
> predicted groups remain largely pure subsets of gold stages (B$^3$
> precision 0.793), so the dominant failure subdivides work rather than
> merging unrelated responsibilities. Thus the direct Agent backend is the ...

Chinese comment expanded to add: `残余 boundary 误差来自过分割而非漏分割（recall 0.626，precision 0.389），因此误差偏向额外 split：预测 group 仍是 gold stage 较纯净的子集（B$^3$ precision 0.793），主导失败是把工作细分而非合并无关责任。`

Numbers preserved: 0.764, 0.101, [0.087, 0.116], 0.480, 0.266, recall 0.626,
precision 0.389, B$^3$ precision 0.793, 20{,}866, 494{,}862{,}929.

## Edit 4 — Budget sentence (reader paragraph)

Extended the existing budget sentence in the TraceElephant reader paragraph
(lines 752–757) with the uncapped-reparse fact, verified against
`docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/analysis-001/analysis-report.md`
(§5, lines 76–82: "more than 5 groups in 0 queries"; "absent: 66/66").

Before:

> ... the five-group budget saturated on 99.5\% of queries, and every
> selection miss was an absence from the reader's ordered choices rather than
> a budget cutoff.

After (one sentence, joined by `---`):

> ... the five-group budget saturated on 99.5\% of queries, and every
> selection miss was an absence from the reader's ordered choices rather than
> a budget cutoff---re-parsing the uncapped stage-one responses shows the
> reader proposed more than five groups on zero of 220 queries, and every
> missed target group was entirely absent from its ordered selection.

Chinese comment extended identically.

## Edit 5 — Complete workload wording (RQ2)

HINTBench is introduced in the RQ2 preamble (line ~674). The 536-of-629 fact
previously appeared only in Appendix `RQ2 Scoring Details` (line ~1197), and
the zero-positive exclusion appeared later in the same RQ2 subsection
(line ~695). Both facts are now unified into the one first-mention sentence:

Before:

> We run complete AgentProcessBench, HINTBench, and TraceElephant
> workloads~\cite{agentprocessbench,hintbench,traceelephant}.

After:

> We run complete AgentProcessBench, HINTBench (the complete released test
> snapshot, 536 of the paper-reported 629 trajectories), and TraceElephant
> workloads~\cite{agentprocessbench,hintbench,traceelephant}; all
> zero-positive trajectories are consumed for population coverage but
> excluded from MAP because AP is undefined without a relevant item.

Bibliography keys unchanged. The later paragraph at line ~695 ("All 522
zero-positive trajectories ...") and the appendix sentence at line ~1197 are
left intact (they remain accurate). Chinese comment added matching the
unified sentence.

## Edit 6 — Horizon distributions (data-classes paragraph)

Added one sentence at the end of the `We evaluate three data classes...`
paragraph (after `agentnet}.`, line ~576):

> Per-workload mean operations per trajectory are 8.5 (AgentProcessBench),
> 13.9 (OSWorld-Human), 24.0 (HINTBench), 27.1 (TraceElephant), and 51.5
> (CodeTraceBench), so benchmark trajectories are short-to-medium horizon
> while the 42-session workstation population---whose longest sessions span
> tens of hours---supplies the long-horizon regime.

Means computed from task-spec numerators/denominators: 20,866/405 = 51.5;
3,978/287 = 13.9; 8,509/1,000 = 8.5; 12,877/536 = 24.0; 5,960/220 = 27.1. The
"tens of hours" wording already exists at line ~871. Chinese comment added.

## Edit 7 — CS3 depth observation

Added one sentence immediately after the 70.4% sentence in Case Study 3
(line ~895):

> Most token mass staying at prompt depth reflects genuinely many-tasked
> development sessions under the fixed one-pass protocol; operation mass
> resolves deeper (43.9\% at depths three and four) exactly where repeated
> engineering work concentrates.

Wording is exactly as the spec prescribes. Chinese comment extended.

## Edit 8 — Privacy paragraph (end of Implementation)

Inserted a new `\paragraph{Privacy.}` immediately after the `Profile export.`
paragraph and before `\section{Evaluation}` (line ~543):

> \sys runs entirely offline on local histories; profiles carry only short
> semantic names, bounded text previews, and numeric measures as labels; no
> trajectory content leaves the machine unless the user shares the profile,
> and packet previews are truncated as disclosed in the appendix.

Chinese comment added. Wording matches the spec.

## Validation summary

- `latexmk -pdf main.tex`: succeeds, 15 pages, `main.pdf` 1,527,437 bytes.
- `rg "^!" main.log`: no matches (no TeX errors).
- `rg "Warning.*[Uu]ndefined" main.log`: no matches.
- `rg "AgentPProf" main.tex`: no matches.
- `rg "Section~\\ref\{sec" main.tex`: no matches.
- `pdftotext main.pdf - | rg "Section \.|Section ,"`: no matches.
- Thesis sentence count unchanged (3 occurrences at lines 44, 144, 1146).
- `\cite{...}` count unchanged (62); no new citation warnings in `main.log`.
- All eight edits visible in `pdftotext` output (lines 164, 355, 384, 402,
  413, 454, 530–531, 606–607, 674).

No files outside `docs/paper/main.tex` were modified. No git commands were
run.
