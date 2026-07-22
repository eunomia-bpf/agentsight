# Round 3 — Whole-Paper Logic Flow

Started: 2026-07-19T19:48:59-07:00
Completed: 2026-07-19T19:57:57-07:00
Parent: BOOTSTRAP step 0001 / WRITE_GATE
Objective: make every promise no stronger than the current retrospective mechanism and make the fairness, scalability, validation, and ablation logic executable.

## Baseline and method

Round 3 began from `main.tex` SHA-256 `8b3b8de5c663e908e06683b83b1ae24be5ef99ebc9189bc6980ff10a2ffdb441`. A fresh read-only reviewer traced the full argument from scenario through conclusion, checking prerequisites, mechanism-to-RQ handoffs, causal language, comparison isolation, and conditional result wording. The root then applied the scientific-boundary repairs without adding an outcome.

## Findings

Must-fix findings were: offline diagnosis described with online-supervision language; `scalable oversight` lacking a success criterion; causal wording for observational harness attribution; no-generated-label language conflicting with derived validation links; imprecise fairness scope and drifting baseline names; and non-reproducible RQ2 confounds/ablations. Secondary findings concerned method versus evaluation-only control paths, undefined workspace transitions and goal boundaries, the short motivating walkthrough, source-record completeness wording, label-dependent sampling risk, and one editing typo.

## Applied fixes

1. Defined the current consumer as an offline automatic diagnoser/supervisor Agent over a completed goal episode. Earliest support and intervention recommendations are explicitly retrospective; online alarms remain future work.
2. Defined scalability as retained diagnosis quality across action/session/duration strata under fixed budget, or equal quality at lower retrieval cost. Added quality--cost curves, stratified measures, and a pre-run noninferiority/cost-margin placeholder.
3. Replaced causal harness-waste language with work traceable to an explicit harness requirement. RQ3 produces an evidence-backed attribution hypothesis; causal effect requires ablation or controlled intervention.
4. Defined validation links as deterministic candidates based on tool class, time, and artifact scope. They neither establish relevance/sufficiency nor add intent/pathology labels.
5. Separated the \system method path from its evaluation-only Raw Retrieval control in Figure 1 and prose.
6. Fixed five condition names: Workspace Trajectory, Raw Retrieval, Final State, Native Report, and Counts. Only Workspace Trajectory versus Raw Retrieval is a same-source primary contrast; the other three intentionally contain less process evidence.
7. Strengthened Raw Retrieval with pagination plus chronological, time-range, field, full-text, and source-ID search. Matched budgets now include query count, per-query output, total returned tokens/bytes, total context, stopping, and cost.
8. Defined label-independent episode inclusion and freezing; any label enrichment must report natural prevalence and sampling weights.
9. Defined top-level goal changes, clarifications, delegation inheritance, concurrent goals, and ambiguous-boundary exclusion.
10. Defined workspace regions and transition edges for multi-file, no-file, concurrent, and tie-broken actions while retaining the non-causal interpretation.
11. Made RQ2 ablations deterministic: reset session indexes, replace order with ID order, collapse lifecycle, suppress transition/churn/validation indexes, or remove direct provenance lookup. Exact source remains available under the same budget, so the mechanism tested is bounded accessibility/inductive bias, not new Shannon information.
12. Removed task difficulty as a privileged condition field. Only preregistered benchmark metadata may be used for split stratification and analysis, never inferred from gold labels.
13. Replaced `complete source evidence` with `all collected source-native records` and stated that the compact 18-minute case is descriptive, not outcome evidence.
14. Added `xspace` to the system macro, replaced blank section-number references with section names because AAAI sections are unnumbered, repaired the `The the` typo, and moved Table 1 to follow its narrative introduction.

## Preservation and claim audit

The central RQ remains whether workspace-centered organization improves automatic diagnosis over outcomes, reports, counts, and strong raw retrieval. The scope is narrower and more defensible: the present paper tests retrospective process oversight, not live intervention. The four pathologies and RQ1--RQ3 meanings are unchanged. Human usability remains excluded. No experiment was run and every result/threshold placeholder remains visible. Citation commands remain 20 over 12 verified entries.

## Validation

- Official-template `latexmk`: success after convergence.
- PDF: 8 total pages; main content ends on page 7 and references begin on page 8, satisfying AAAI-27's seven-main/nine-total constraint.
- No overfull box, negative label-width, undefined citation, or undefined reference warning.
- Visual text inspection confirms `Agent Nebula` spacing and nonblank contribution references.
- `git diff --check`: success.
- Exit `main.tex` SHA-256: `30a84ad697dd475a3aa3000a980543d63a82ff859cdb860b1bbb7c5fef13d29b`.

## Next node

Round 4 uses the dedicated abstract/Introduction rewriting workflow. It may improve the opening's compactness and correspondence but must preserve the retrospective boundary, the condition hierarchy, all citations, and the unanswered result slot.
