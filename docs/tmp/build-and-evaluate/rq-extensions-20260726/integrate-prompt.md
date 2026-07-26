# Task: Integrate RQ-extension results into supplement (+ at most one line each in main)

Inputs: docs/tmp/build-and-evaluate/rq-extensions-20260726/result.md (and its CSVs/scripts) — dormant→revived transitions (RQ1 extension), rank-turnover/cooling curves (RQ3 extension), and two robustness spot-checks (encoded_claude_root dot risk; plausible_path_token filter impact).

Do:

1. Read the extensions result.md. If any robustness spot-check reports REAL corpus impact (it is instructed to flag prominently at the top), STOP and report that first — do not integrate; that requires a projection decision.
2. Otherwise: add a compact subsection per analysis to docs/paper/supplement.tex near the corresponding RQ section, using the "for the paper" paragraphs from result.md (edit for brevity; include the per-project table only if it earns its space).
3. In docs/paper/main.tex: at most ONE added sentence per analysis in the relevant RQ paragraph, pointing to the supplement. If the main is already at 6 pages and a sentence would push content past the limit, skip the main-text sentence for that analysis and say so.
4. Recompile main and supplement; verify main ≤9 pages with references-only trailing page(s), zero errors, no undefined refs.
5. No git commands.

Final message: what was integrated where, any spot-check flags, final page counts.
