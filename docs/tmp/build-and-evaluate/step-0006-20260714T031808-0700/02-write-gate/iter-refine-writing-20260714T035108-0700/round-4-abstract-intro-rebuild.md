# Round 4 — Abstract/Introduction Rebuild

- **Timestamp:** 2026-07-14 04:19:37 -0700
- **Skill:** `rewrite-abstract-intro`
- **Target:** `docs/paper/main.tex`
- **Mode:** main-agent structural pass; no reviewer subagent and no Git operation
- **Disposition:** PASS

## Scope and authority

This round was limited to abstract/introduction structure and correspondence.
It did not alter the paper thesis, the four RQs, the system design, any result,
or the canonical paper submodule. The exact thesis remains:

> Agent observability needs profiling, not only debugging.

The current seven-paragraph introduction already carries the intended original
story. Reordering or replacing those paragraphs would create unnecessary story
drift, so this round retained their order and made only a compact abstract
repair.

## Pre-edit role map

### Abstract

The pre-edit abstract expressed the right content but spread eight annotated
roles across twelve prose sentences:

1. context;
2. developer need;
3. traditional profiling;
4. existing-tool gap;
5. agent-specific challenge;
6. thesis;
7. model, split across two sentences;
8. system;
9. results, split across three sentences.

The separate traditional-profiling and tool-gap sentences repeated the same
contrast already stated in Introduction paragraphs 2–3. The result block also
used three short sentences where two roles—scientific result and cost—were
sufficient.

### Introduction

The current introduction has a complete seven-paragraph argument:

1. **Context:** agent activities span intent and system effects, and production
   accumulates many long trajectories.
2. **Problem and need:** developers need cross-trajectory attribution;
   traditional profiling supplies aggregation rather than run-local debugging.
3. **Existing solutions and gap:** current tools provide traces, metadata, and
   dashboards but not recurring semantic responsibility propagated to effects.
4. **Root challenge:** agent responsibility is semantic and trajectories lack
   stable identifiers and runtime call-stack hierarchy.
5. **Thesis and model:** profiling transfers through operations and operation
   stacks; the exact thesis appears verbatim.
6. **System and evidence:** AgentProf, its two pluggable frameworks, and the
   admitted RQ1–RQ4 evidence.
7. **Contributions:** model, implementation, and evaluation.

This order is coherent: it states the desired capability, identifies the
observable gap in current tools, explains the technical reason for that gap,
and then introduces the insight. Moving paragraph 4 before paragraph 3 would
not improve the logic enough to justify changing the established story.

## Reorganization plan

1. Preserve all seven introduction paragraphs and their order.
2. Preserve the exact thesis and every admitted number.
3. Compress the abstract to nine sentences, with one explicit role per
   sentence.
4. Combine traditional profiling and the existing-tool gap into one contrast
   that matches Introduction paragraphs 2–3.
5. Combine the qualitative RQ1/RQ2 result and quantitative RQ3 result into one
   scientific-evidence sentence; keep RQ4 cost separate.
6. Derive the resulting abstract exclusively from the already-stable
   introduction, not the reverse.

## Applied edits

- Corrected “quality ... of AI agent” to “agent quality ...”.
- Replaced the two-sentence traditional-profiling/tool-gap contrast with one
  sentence grounded in the introduction's more precise description of
  run-local structure and application-supplied fields.
- Kept the exact thesis as its own sentence.
- Combined model introduction and definition into one model sentence without
  changing either model component.
- Combined qualitative attribution/problem-concentration evidence with the
  admitted OSWorld-Human boundary evidence.
- Kept the release-profiler cost as a separate final sentence.
- Updated adjacent Chinese comments to match the edited English text.

The resulting abstract has nine sentences with the following roles:

1. context;
2. developer need;
3. traditional profiling plus existing-tool gap;
4. agent-specific root challenge;
5. thesis;
6. model;
7. system;
8. RQ1/RQ2 qualitative evidence plus RQ3 quantitative evidence;
9. RQ4 cost evidence.

## Abstract–introduction correspondence

| Abstract role | Introduction anchor | Status |
|---|---|---|
| Long, multi-step agent activity | ¶1 | matched |
| Quality/safety/cost questions | ¶2 | matched |
| Aggregation vs. run-local observability gap | ¶2–¶3 | matched |
| Semantic responsibility and missing hierarchy | ¶4 | matched |
| Exact profiling thesis | ¶5 | verbatim match |
| Operations and operation stacks | ¶5 | matched |
| AgentProf and its pluggable algorithms | ¶6 | matched |
| Attribution, concentration, boundary fidelity | ¶6 | matched; same scope and numbers |
| Profiling cost | ¶6 | matched; same operation count and time |

No abstract-only claim remains. The introduction provides more detailed
evidence than the abstract, as intended.

## Conservation ledger

- **Thesis:** unchanged.
- **RQs:** unchanged; exactly four.
- **RQ1 evidence:** unchanged.
- **RQ2 evidence:** unchanged.
- **RQ3 evidence:** unchanged: 287 task instances, 0.739 vs. 0.645 boundary
  F1, 0.816 vs. 0.678 B-cubed F1.
- **RQ4 evidence:** unchanged: 27,765 operations in 1.17 s.
- **Mechanisms:** uniform operations, operation stacks, intent attribution,
  stack construction, and pprof compilation all preserved.
- **Citations:** no citation command removed or changed.
- **Canonical submodule:** untouched.

## Validation

- `make -C docs/paper`: PASS
- PDF length: 8 pages
- Undefined citations/references: none
- Overfull boxes: none
- Citation commands: 49, unchanged
- Only underfull layout warnings remain

## Remaining scientific boundary

This writing pass does not make the full RQ3 complete. It reports the admitted
boundary-tagging evidence at its precise scope and leaves task/phase/action tag
accuracy for a later experiment. Resolving that scientific frontier belongs to
the EXPERIMENT gate, not to abstract rewriting.
