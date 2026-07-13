# Canonical Submodule Story Restoration

**Started:** 2026-07-12T19:42:00-07:00  
**Completed:** 2026-07-12T19:53:45-07:00  
**Cycle/gate:** cycle 0001 / WRITE re-entry  
**Status:** implementation complete; independent fidelity audit pending

## Question And Authority

Restore the active paper's scientific story directly from the untouched
submodule without changing the exact thesis or four RQs and without allowing
reviewer-derived hierarchy or intervention programs to replace the original
profiling story.

The user instruction is direct authority. The read-only source is
`docs/agentpprof-paper/main.tex`; the active destination is
`docs/paper/main.tex`.

## Restored Reader-facing Structure

- Restored the submodule title, **AgentProf: Semantic Profiling for AI
  Agents**.
- Rebuilt the Abstract from the submodule sequence: long-running agent stakes,
  quality/safety/cost questions, profiling precedent, tracing gap, semantic
  profiling challenge, two-object model, AgentProf, four-RQ evaluation.
- Restored the Introduction's seven roles and its direct distinction between
  debugging/tracing and profiling.
- Restored Background and Motivation subsections for agents, system profiling,
  the two challenges, and three design requirements.
- Restored Design around cross-layer resource projection, stable tags,
  hierarchical attribution, operations, operation stacks, intent attribution,
  stack construction, and the original compact pipeline figure.
- Restored Implementation to the submodule's concise Rust CLI, importer,
  pluggable-algorithm, and standard-output description.
- Removed the added Discussion section whose optimization-interface and
  intervention loop were not part of the submodule story.
- Restored the Conclusion to semantic operation-stack profiling and the four
  original evaluation questions.

The active paper retains AAAI formatting, current bibliography repairs, and
evidence-safe result status. Unsupported submodule result numbers were not
restored.

## Restored RQ2 Meaning

The exact RQ2 wording remains **Does Profiler Output Correspond to Real
Problems?** Its scientific meaning is again the submodule's target-blind
hidden-annotation localization question: do high-ranked groups concentrate
independently annotated failures, unsafe operations, redundant work, or task
boundaries while reducing inspection? The root removed the later paired
regression--intervention--held-out-rerun program from the paper and current
canonical frontier.

## Canonical Updates

- `docs/idea-story.md`: current RQ2 hypothesis and next evidence restored;
  E007 records the direct user decision and submodule story lock.
- `docs/evaluation.md`: RQ2 frontier and source criteria restored to public
  hidden annotations and target-blind baselines.
- `docs/background-related-work.md`: next RQ2 literature task restored.
- `docs/design.md` and `docs/implementation.md`: next experiment consequence
  restored.
- `AGENTS.md`: added one project-local rule naming the submodule as the
  read-only canonical story source.
- `docs/user-instruction.md`: appended only the user's three new verbatim
  prompts.

## Build Evidence

`make clean && make` completed in `docs/paper/`. The final PDF is 8 US-Letter
pages. The final LaTeX pass has no undefined citation, undefined reference,
LaTeX error, or emergency stop. Underfull-box messages remain formatting
warnings only.

## Scope And Next Action

The paper, project canonical docs, project AGENTS rule, active architecture
figure, and timestamped Markdown reports changed. The read-only submodule and
all shared skills remained unchanged. No Git command ran.

A fresh independent reviewer now compares the restored active paper and
canonical docs directly with the submodule. A PASS permits a new REVIEW gate
report; a REPAIR verdict permits only fidelity repairs, not another story.
