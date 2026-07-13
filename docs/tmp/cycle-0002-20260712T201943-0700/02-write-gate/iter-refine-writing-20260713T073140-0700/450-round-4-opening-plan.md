# Round 4 Plan — Abstract and Introduction

- Planned: `2026-07-13T08:17:30-07:00`
- Governing skill: `rewrite-abstract-intro`
- Body source of truth: current `docs/paper/main.tex`
- Decision: proceed inside `iter-refine-writing` without pausing

## Current-to-target map

| Current block | Target role | Disposition |
|---|---|---|
| Abstract context | Background | Preserve interaction scale and add explicit accumulated-trajectory correspondence from Introduction. |
| Abstract developer questions | Problem | Preserve quality/safety/cost and make cross-run failure/waste concentration explicit. |
| Abstract profiling analogy | Thesis/insight | Move after structural cause and existing-work limitation. |
| Abstract tool gap | Existing approaches | Retain but avoid categorical “no aggregation” wording. |
| Abstract semantic/no-hierarchy sentence | Root cause | Distinguish native execution structure from reusable cross-run responsibility. |
| Abstract model/system/results | Insight, challenges, system, methodology, results | Derive in the same order from target Introduction roles. |
| Introduction paragraph 1 | Background | Preserve two layers, workload duration, interaction scale, accumulated trajectories. |
| Introduction paragraph 2 | Problem | Preserve concrete token/failure/waste/safety questions and inspection cost. Move profiling analogy out. |
| Introduction paragraph 3 | Existing approaches | Move after structural root cause; compare representation/decision limits without an absolute incapability claim. |
| Introduction paragraph 4 | Root cause + challenges | Split into structural cause and three implementation capabilities. |
| Introduction paragraph 5 | Insight/model | Begin with exact thesis; preserve operations and operation stacks as the only core abstractions. |
| Introduction paragraph 6 | System/method/results | Preserve AgentProf mechanisms, fixed four-RQ program, all current opening numbers, and evidence wording. |
| Flamegraph | System evidence preview | Move after the system paragraph; preserve asset/caption/label. |
| Contributions | Deliverables | Preserve three contributions, citations, and section pointers. |

## Optional-role decisions

- Root cause: required because the model answers a structural mismatch between code profiling and agent trajectories.
- Challenges: required because DR1–DR3 map directly to operations, intent attribution, and operation stacks.
- No additional paragraph, contribution, abstraction, or RQ is authorized.

## Source-fidelity rules for application

- Exact thesis appears verbatim in abstract and key-insight paragraph.
- Citation commands/keys remain 5/12 in Introduction; none are removed or added.
- Every opening number already appears in the current opening/body.
- All four RQs remain explicit and unchanged in meaning.
- Chinese source comments are regenerated after each new English sentence rather than left stale.
- No body section is edited in this round.

## Open evidence items intentionally not solved by prose

1. support for the “thousands to millions” range;
2. derivation of the “over 90%” statement;
3. target-visible RQ2 ranking despite hidden-construction wording;
4. correct interpretation of 9.4% as top-five inspected work rather than full recovery;
5. source-grounded current-product novelty boundary;
6. complete/cached/capture scope of RQ4 cost.

The opening retains existing positive claim targets. REVIEW/EXPERIMENT must repair their evidence rather than shrinking the thesis or changing the hypotheses.
