# Task: AAAI-format snapshot of the submodule paper + full comparison

Repository: /home/yunwei37/workspace/agentsight-research-semantic-flamegraph
ABSOLUTE RULE: docs/agentpprof-paper/ (submodule) is READ-ONLY. Copy from
it; never write, format, or run any tool inside it. No git commands.

## Part 1 — AAAI snapshot (text verbatim)

1. Create docs/tmp/agentpprof-paper-aaai-snapshot-20260726/.
2. Copy the submodule's main.tex body, its bibliography file(s), and any
   figures it includes into that directory.
3. Convert ONLY the wrapper to AAAI-27: \documentclass aaai2027 (copy
   aaai2027.sty/.bst from docs/paper/), anonymous submission author block,
   natbib + aaai2027 bibliography style, and a no-op \Description shim.
   The scientific body text must remain byte-identical: do not rewrite,
   reflow, or "fix" any body sentence. Where an ACM-only preamble command
   breaks compilation (\settopmatter, \citestyle, CCS/keywords blocks,
   etc.), neutralize with a shim or comment out THAT non-body line only,
   and list every such line in the report.
4. Compile with latexmk; record page count; fix only wrapper-level errors.

## Part 2 — comparison report

Write comparison-report.md in THIS directory comparing the snapshot
(submodule text) against the current docs/paper/main.tex:
- title, abstract content, thesis sentence placement;
- section/subsection structure (list side by side);
- the four RQ wordings;
- every headline number present in either version (table: number ->
  submodule value / current value / status: same, changed, added,
  removed);
- claims or experiments present only in the current paper (e.g., reader
  study, case studies 2/3, tau-b, direct backend) and anything present
  only in the submodule;
- figures/tables in each.
Factual comparison only; no quality judgments.
