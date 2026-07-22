# Round 5 — Terminology, Information Flow, and Paper Consistency

Started: 2026-07-19T20:00:23-07:00
Completed: 2026-07-19T20:14:02-07:00
Parent: BOOTSTRAP step 0001 / WRITE_GATE
Scope: combined `check-terminology-infoflow` and paper-consistency audit

## Baseline and method

Round 5 began from `main.tex` SHA-256 `93de344201bf880e79f1c931fdec2337506d9b7a3d2c1ed4c443535361741505`. A fresh read-only reviewer built a concept inventory, ran compound-term and synonym audits, compared figure/table/body claims, and checked paper statements against the actual Rust artifact and `docs/implementation.md`. The root independently inspected `agentvis/src/repository.rs` and `agent-session/src/parser.rs` before changing any implementation claim.

## Verified artifact anchors

- Implemented: Claude/Codex/Gemini session parsing, repository affiliation, repository-scoped tool-action projection, native action-time ordering, HTML/SVG/PNG/GIF/MP4 export, optional `source_call_id`, `previous_path`, create/write/delete/rename parsing, and ignored dependency/build paths.
- Not implemented: stable supervisor query interface, goal-episode constructor, $W_0/W_T$ snapshotting, lifecycle/transition/candidate-validation indexes, labeled diagnosis corpus, or matched-budget runner.
- Motivating episode counts verified: four session files, 351 native records, 115 actions, 41 projected file effects, and an 18-minute interval. All 115 preflight composite IDs are present and unique, but the general Rust schema correctly remains optional.

## Concept inventory

The retained core concepts are: goal episode, workspace-centered action trajectory, artifact effect, evidence ID, observed lifecycle/workspace transition, and the fixed five evaluation conditions. Candidate validation is a deterministic low-level relation, not a diagnosis term. The four pathology display names are fixed as `stagnation`, `goal drift`, `validation gap`, and `harness waste`.

## Applied fixes

1. **Prototype versus planned mechanism.** The Abstract, Introduction, and Implementation now state that the frozen prototype implements ingestion, projection, provenance, and visual export. Goal episodes, snapshots, indexes, supervisor queries, and the runner are explicitly planned prerequisites to evaluation.
2. **Evidence architecture.** Removed embedded source record $r_i$ from $a_i$. Defined external read-only $R(id_i)$ over frozen native slices and replaced the fictitious self-contained object with an episode manifest plus $W_0$, $W_T$, and referenced slices.
3. **Effect epistemics.** Replaced `proven effects` with `projected` or `source-supported effects`; native-to-system coverage remains separate from diagnosis.
4. **Lifecycle state.** Defined observed lifecycle, the episode-start manifest $W_0$, the final snapshot $W_T$, and unknown pre-first-observation existence when $W_0$ is absent. Evaluation excludes episodes missing frozen snapshots.
5. **Transitions and queries.** Defined region sets $G_i$ and edges $G_i\times G_j$ for consecutive effect-bearing actions, added transition retrieval to Design and the planned API, and left zero-effect actions in chronology without edge endpoints.
6. **Candidate validation.** Defined $V(m,v)$ using a frozen tool set $\mathcal{C}_V$, time bound $\Delta_V$, scope overlap, and evidence-ID tie order; the relation asserts neither relevance nor sufficiency.
7. **Five-condition fairness.** All five receive the same goal, frozen $W_T$, outcome/evaluator evidence, model, and applicable budget. Workspace Trajectory versus Raw Retrieval is the same-source contrast; AgentRx/TrajAudit are an external subset and future system evidence is a separate experiment.
8. **Scalability.** Fixed the requirement count from three to four and made the largest-stratum comparison explicitly Workspace Trajectory versus Raw Retrieval.
9. **Vocabulary.** Unified pathology display names, `evidence micro-F1`, `evidence ID`, and the five condition names; removed `Raw Retrieval retrieval`, `counts-only`, and several unnecessary source/evidence compounds.
10. **Canonical IDs.** Scored-episode admission now requires every scorable action to have a present, unique composite ID; the paper no longer implies the optional Rust field is universally populated.
11. **Status placeholders.** Replaced `reviewed experiment` with `separately admitted and completed experiment` and added the validation-rule/veto parameters to the frozen setup placeholder.
12. **Motivating attribution.** Changed the metadata explanation to what the agent reported and attributed, rather than an independently established cause.

To regain the official seven-page main-content limit after adding necessary mechanism/status text, Related Work was tightened by synthesis rather than by deleting citations or scientific boundaries. All 20 citation commands remain.

## Deferred

- The planned mechanisms remain unimplemented; prose consistency does not close that gap.
- Exact $\mathcal{C}_V$, $\Delta_V$, scope, noninferiority, cost, and grounding-veto thresholds remain visible pre-run placeholders.
- Long source/evidence compounds that are core terms remain for later word-choice rounds; no global rename was performed without a real contradiction.

## Validation

- Official AAAI-27 `latexmk`: success.
- PDF: 8 total pages. Ethical Considerations and Conclusion end on page 7; References begin on page 8, satisfying the seven-main/nine-total rule.
- Abstract: 237 words by the conservative round count.
- No overfull box, negative label-width, undefined citation, or undefined reference warning.
- `git diff --check`: success.
- Exit `main.tex` SHA-256: `756f154482386aa22d9592fff8e6cbaff1056f6c9b7c7a4428c2d416ff6d57ba`.

## Next node

Round 6 performs sentence-structure review only. It may simplify syntax and paragraph rhythm but must not erase the implemented/planned boundary or any frozen evaluation control.
