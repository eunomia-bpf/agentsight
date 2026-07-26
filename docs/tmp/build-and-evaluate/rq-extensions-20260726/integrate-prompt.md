# Task: Integrate RQ-extension results into supplement (+ at most one line each in main)

Inputs: docs/tmp/build-and-evaluate/rq-extensions-20260726/ — NOTE: result.md was never written; work directly from the committed artifacts: rq1-dormancy-summary.csv (dormant→revived, both thresholds), rq3-turnover-summary.csv / rq3-cooling-pooled.csv (rank-turnover/cooling), robustness-summary.json (both spot-checks CLEAN: corpus_impact=false and zero file-edge impact — state each in ONE sentence), rq-summary.json, and the analysis scripts. Write the supplement prose yourself from these numbers: dormant→revived RQ1 extension, rank-turnover/cooling RQ3 extension, and the two robustness spot-checks.

Do:

1. Robustness: both spot-checks are clean — no projection decision needed; report each in one sentence in the supplement (and nothing in main text).
2. Add a compact subsection per analysis to docs/paper/supplement.tex near the corresponding RQ section (dormant→revived near RQ1; turnover/cooling near RQ3; spot-checks near the conformance/measurement section). Keep prose tight; include the per-project dormancy table (both thresholds) — it earns its space.
3. In docs/paper/main.tex: at most ONE added sentence per analysis in the relevant RQ paragraph, pointing to the supplement. If the main is already at 6 pages and a sentence would push content past the limit, skip the main-text sentence for that analysis and say so.
4. Recompile main and supplement; verify main ≤9 pages with references-only trailing page(s), zero errors, no undefined refs.
5. No git commands.

Final message: what was integrated where, any spot-check flags, final page counts.
