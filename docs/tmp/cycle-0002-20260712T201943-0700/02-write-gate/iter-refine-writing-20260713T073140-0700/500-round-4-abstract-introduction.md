# Round 4 — Abstract and Introduction

- Completed: `2026-07-13T08:39:00-07:00`
- Governing skills: `iter-refine-writing`, `rewrite-abstract-intro`
- Edited source: `docs/paper/main.tex`
- Scientific authority: user-selected original AgentProf manuscript and the read-only `docs/agentpprof-paper/main.tex`
- Decision: `PASS`

## Scope and locks

This round edited only the abstract and Introduction. It did not alter the
fixed thesis, the four RQs, their meanings, the evaluation numbers, the
contribution boundary, the bibliography, or any body section. The exact thesis
remains:

> Agent observability needs profiling, not only debugging.

It now appears verbatim in the abstract and Introduction, and remains verbatim
in the Conclusion. The paper continues to ask exactly four questions about
attribution, real-problem localization, tag accuracy, and profiling cost.

## Independent read-only diagnosis

Before editing, an independent read-only reviewer rebuilt the opening from the
current paper body. The reviewer found that the original content was present
but its argumentative order diluted the main insight: the profiling analogy
appeared before the structural obstacle, the two agent-specific failure modes
were separated from the thesis, and the system/evidence paragraph did not state
the fixed evaluation program. The reviewer recommended a role-complete opening
without adding an abstraction, RQ, contribution, citation, or scientific claim.

## Applied abstract structure

The abstract now has nine sentences in this order:

1. scale and accumulated trajectories;
2. the quality, safety, and cost decisions that require population analysis;
3. the structural mismatch between semantic responsibility and code paths;
4. the decision boundary of existing debugging, tracing, and input-clustering
   views;
5. the exact thesis;
6. the three capabilities an agent profiler must recover;
7. the semantic operation stack model and AgentProf implementation;
8. the real and public evaluation populations; and
9. the existing positive RQ1--RQ3 results.

The resulting abstract contains 260 words and nine sentences. Each English
sentence has a regenerated Chinese source comment immediately after it.

## Applied Introduction structure

The Introduction now follows the same argument at full length:

1. **Background.** It introduces the intent and system-effect layers, then
   establishes the hours-to-days, thousands-to-millions, and accumulated-run
   setting.
2. **Problem.** It states the concrete population-level questions about token
   budget, failures and wasted work, and unsafe effects, plus the scaling cost
   of manual or per-trajectory evaluation.
3. **Structural cause.** It contrasts stable code paths and runtime nesting
   with semantic responsibility, natural-language identifiers, and the absence
   of a reusable cross-run attribution hierarchy.
4. **Existing approaches.** It distinguishes per-execution diagnosis and
   input-level distribution summaries from downstream, population-level
   resource attribution without claiming that products perform no aggregation
   at all.
5. **Thesis and insight.** It states the exact thesis and introduces only the
   original two core abstractions: uniform operations and query-time operation
   stacks.
6. **Challenges.** It names cross-layer resource projection, stable
   low-cardinality intent attribution, and hierarchical stack construction.
7. **System and evidence.** It introduces AgentProf, states all four fixed RQs,
   and preserves the current real/public dataset counts and positive results.
8. **Visual preview and contributions.** It moves the unchanged flamegraph
   figure after the system paragraph and preserves the original three
   contributions.

Every newly written English sentence has an updated Chinese source comment.
The Introduction retains exactly five live citation commands containing the
same twelve citation keys:

`sweagent`, `claudecode`, `osworld`, `agentatlas`,
`agentrewardbench`, `llm-as-judge`, `langsmith`, `langfuse`, `phoenix`, `otel`,
`datadog-llmobs`, and `laminar-signals`.

## Fidelity audit

- Exact thesis count in live LaTeX: 3 (abstract, Introduction, Conclusion).
- Abstract length: 260 words, 9 sentences.
- Introduction citations: 5 commands, 12 unchanged keys.
- RQs in opening: RQ1 attribution, RQ2 real-problem correspondence, RQ3 tag
  transfer accuracy, RQ4 complete profiling cost.
- Core abstractions: operations and operation stacks only.
- Contributions: model, system, evaluation; unchanged in count and meaning.
- Bibliography SHA-256: `f044ea5eb5a5e3dba7aee2bbb8e634cad484b60428ae379e10cf48eca70c3`.
- Revised `main.tex` SHA-256:
  `65b507295d08a3e17dcc3f516297fc3321d9b0c1b3804bbd17ed6c80d683c580`.

## Build and visual audit

`make` completed the full `pdflatex -> bibtex -> pdflatex -> pdflatex`
sequence successfully.

- Output: 9-page US-letter PDF.
- Main text and Conclusion end on page 7; pages 8--9 contain references only.
- No unresolved citation or reference warning remains.
- No overfull box is reported; remaining warnings are existing underfull boxes.
- Every embedded font reported by `pdffonts` is Type 1.
- Visual inspection of pages 1--3 confirmed that the abstract and Introduction
  fit cleanly, contribution items do not split incoherently, and the unchanged
  wide flamegraph remains readable before Design.
- Revised `main.pdf` SHA-256:
  `623ca5c9c035e8c42d04178ee552225baa676d2df5ad74838a8ed214d156a998`.

## Evidence obligations carried forward

Writing did not hide or resolve evidence questions by weakening the story.
Whole-paper REVIEW and subsequent EXPERIMENT work must still audit:

1. a source or direct dataset derivation for the “thousands to millions” scale;
2. the exact derivation of the “over 90%” statement;
3. whether RQ2 ranking uses target-visible information despite the stated
   hidden-annotation protocol;
4. whether 9.4% is consistently described as top-five inspected work rather
   than full recovery;
5. the source-grounded novelty boundary relative to current observability
   products; and
6. the complete/cached/capture scope of the RQ4 cost claim.

These are evidence-repair targets. They do not authorize narrowing the thesis,
changing an RQ, withdrawing a hypothesis, or replacing the original story.
