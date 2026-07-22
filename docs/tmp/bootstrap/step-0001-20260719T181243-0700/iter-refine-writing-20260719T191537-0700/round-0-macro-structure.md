# Round 0 — Macro Structure

Started: 2026-07-19T19:15:37-07:00
Completed: 2026-07-19T19:29:21-07:00
Parent: BOOTSTRAP step 0001 / WRITE_GATE
Objective: make the draft submission-shaped at the section and evidence-block level without changing the fixed scientific contract or pretending that the closed experiment produced a result.

## Entry baseline

- Repository HEAD: `957675252011d9cf86d2b28b17414951684f3931`.
- Iteration entry tree: `519e805a80956870ad539b8ca3ffb47ca203dfa5`.
- Entry `main.tex` SHA-256: `e7fc93550ed28b00cb893408be46b30d1eb2c0fb3ddb5f1e250dbee7efad4e5b`.
- Entry PDF: 5 pages, 225,137 bytes.
- The fixed claim asks whether workspace-centered action trajectories improve automatic diagnosis or supervision under matched evidence and model budgets. Human-interface utility is out of scope.

## Files and sources read

- `docs/paper/main.tex`, `docs/paper/references.bib`.
- `docs/idea-story.md`, `docs/design.md`, `docs/implementation.md`, `docs/evaluation.md`, and the BOOTSTRAP step report.
- The closed experiment plan, data audit, and AgentSkill citation-check episode counts.
- Official AAAI-27 Author Kit and main-track call: the submission uses `aaai2027.sty`/`aaai2027.bst`; the call permits seven main-content pages and at most nine total pages, with pages beyond seven reserved for references.

## Review method

A fresh read-only reviewer applied the macro levels of `check-paper-structure-flow`: section order, motivation-to-requirements traceability, Design/Implementation separation, explicit RQ organization, and completeness of each evidence block. The root then implemented only structure-preserving fixes, rebuilt the official submission format, inspected the log, and checked the resulting page boundary.

## Raw findings

Must-fix findings were: the custom five-page article was not AAAI-shaped; Problem Formulation lacked a concrete motivating episode; Design lacked an overview and architecture figure; Implementation was a thin project-status paragraph; Evaluation did not enumerate RQ1--RQ3 or centralize shared setup; and the RQ blocks lacked explicit experiment/result/interpretation/required-evidence roles. Should-fix findings were: parallel RQ titles, evaluation-local limitations, a separate ethics section, a bounded Discussion, and demoting visual replay from a scientific mechanism to an auxiliary export.

## Applied fixes

1. Replaced the custom article layout with the official AAAI-27 submission style.
2. Added one real AgentSkill citation-check episode as a motivating case: four sessions, 351 source records, 115 tool actions, and 41 file effects. These are corpus-description facts from the data audit, not diagnosis outcomes.
3. Reorganized the problem section into `Problem Setting and Motivation`, with the concrete case followed by oversight target, four fixed pathologies, and six representation requirements.
4. Added a two-condition architecture figure that makes the same-source split, deterministic workspace indexes, bounded raw retrieval, matched budgets, shared supervisor, and model boundary explicit.
5. Added a Design overview and episode walkthrough before formal definitions.
6. Expanded Implementation into ingestion/episode construction, artifact-effect and provenance indexing, and query harness/exports. Visual replay is explicitly auxiliary and outside the evaluated consumer.
7. Enumerated fixed RQ1--RQ3 and factored shared episodes, labels, conditions, budgets, supervisor protocol, and metrics into `Experimental Setup`.
8. Gave every RQ an experiment/protocol, an unfilled result block, interpretation rules, and an explicit required-evidence statement.
9. Added bounded Discussion, Evaluation Limitations, and Ethical Considerations sections.
10. Replaced a warning-producing description list, narrowed the architecture figure, and split the artifact-effect equation to eliminate all overfull boxes and enum label-width warnings.

## Rejected or deferred changes

- No diagnosis run, result number, or effectiveness claim was added. The experiment proposal remains closed after its third BLOCK review.
- The motivating episode does not become a qualitative success case; it only demonstrates the information-organization problem.
- No human study, 30-second comprehension task, or visualization outcome was introduced.
- The paper was not padded to seven main pages. Missing space is reserved for real evidence and its analysis.

## Claim, number, and citation preservation

The central claim, evaluated consumer, four pathology labels, fixed RQ meanings, matched-budget requirement, and null-result interpretations are unchanged. New numbers are trace counts already established by the BOOTSTRAP data audit and are explicitly marked non-outcome evidence. The paper currently contains 20 citation commands backed by 12 verified bibliography entries; no reference was removed. All result placeholders remain visibly unanswered.

## Validation evidence

- Command: `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`.
- Result: success under the official AAAI-27 style; 7 pages and 240,007 bytes.
- Page inspection: main content ends on page 6 and references begin on page 7, within the official limit.
- Log inspection: no overfull box, negative label-width, undefined citation, or undefined reference warning remains. Non-blocking underfull boxes remain for later prose rounds.
- Exit `main.tex` SHA-256: `0c59534d10c3fa50e4fda30d1b984d5261cd55154f1e6d8c4495c6f530073845`.

## Alternatives considered

Keeping the five-page custom layout would preserve a compact research note but conceal missing AAAI evidence roles. Filling the seventh main page with related work would make the page count look mature without strengthening the claim. A single combined system/evaluation section would be shorter but would blur deterministic representation design, implementation facts, and unobserved empirical results.

## Tree changes

- Added the official `aaai2027.sty` and `aaai2027.bst` beside the paper.
- Reworked `docs/paper/main.tex` at section scale and regenerated local build products.
- Added this round report under the immutable iteration directory.

## Remaining concerns and next node

The draft is structurally submission-shaped but prose-level flow, section conventions, paragraph roles, terminology, and opening argument still require serial review. Implementation size and latency remain placeholders, and all RQ result blocks await an admitted experiment. Round 1 performs micro-structure review of paragraph roles and sentence-to-sentence flow; it must not change the scientific contract.
