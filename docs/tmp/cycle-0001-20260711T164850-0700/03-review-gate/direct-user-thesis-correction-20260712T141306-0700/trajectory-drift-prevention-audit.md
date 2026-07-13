# Thesis-Drift Prevention Audit

**Timestamp:** 2026-07-12T14:16:00-07:00  
**Decision:** determine why agents replace the AgentProf thesis and choose the
smallest durable prevention without modifying current shared skills  
**Verdict:** project rule applied; shared-skill candidate remains `observe`

## Evidence And Scope

This audit uses one interactive parent research task, its serial idea and
writing children, the direct user correction, the current
`auto-research-orchestrator`, `iter-refine-ideas`, `iter-refine-writing`, full
`docs/idea-story.md`, and project `AGENTS.md`/`CLAUDE.md`. Multiple children are
not counted as independent projects. The observed outcome is direct: the root
changed the submodule thesis into a narrower paraphrase, and the user corrected
it before the writing rounds proceeded.

## Observed Failure

The exact thesis, “Agent observability needs profiling, not only debugging,”
was first summarized as cross-run profiling of recurring behavior and measured
effects. The summary was then promoted into the Current Frontier, root idea
audit, WRITE entry report, abstract, and conclusion. No experiment or source
required this replacement. The behavior is `concept_churn` with secondary
`claim_evidence_drift` and `premature_downstream_work`.

The mechanism was specification drift during synthesis: the root treated
motivation and experimental operationalization as a more precise thesis. The
general anti-narrowing rules did not prevent this because no artifact marked the
original sentence as author-fixed and verbatim. Downstream writing correctly
propagated the wrong upstream disposition.

## Ownership

| Candidate owner | Evidence | Decision |
|---|---|---|
| Project `AGENTS.md` | Exact thesis and active paper path are stable facts of this repository. | Apply now. |
| `docs/idea-story.md` | Project narrative authority and evolution history. | E005 already applied. |
| Auto-research orchestrator | Could protect author-fixed exact theses across projects. | Observe only; one parent task is insufficient for shared promotion. |
| Idea/writing skills | Idea synthesis and prose can propagate a replacement. | Do not patch now; upstream project rule and root disposition own this case. |

## Applied Project Rule

Project `AGENTS.md` now identifies `docs/paper/` as the active paper, preserves
the exact thesis verbatim, classifies cross-run recurrence, measures, hierarchy,
and experiments as subordinate roles, and forbids automatic thesis replacement
from reviewer objections, neighbors, local negatives, evidence gaps, venue
preferences, or prose refinement. An explicit user instruction is required to
establish a different thesis.

## Shared-Skill Candidate And Evaluation

A future minimal orchestrator candidate could say: when the user designates an
exact thesis sentence, preserve it verbatim in `docs/idea-story.md`, pass it to
every specialist node, and reject a paper/story diff that replaces it with
motivation, mechanism, experimental scope, or a local conclusion. This must not
freeze provisional wording that the author did not designate as exact.

Promotion requires independent positive tasks in which an author fixes an exact
thesis, untriggered tasks with provisional or openly revisable theses, and
regression tasks where verified direct challenges legitimately reopen idea
discussion. Baseline and candidate must be compared without revealing the
expected verdict. No global skill file is changed from this single-project
evidence.

## Revisit Condition

Reopen the shared candidate when the same replacement appears in independent
parent tasks or repositories, or when the project rule fails to prevent a later
AgentProf writing/review round from altering the exact sentence.

## Independent Verification

A fresh read-only reviewer checked the project rule, complete idea story,
current paper, active paths, and the relevant orchestrator and writing skills.
It found the rule sufficient across review, experiment, idea synthesis, resume,
and writing, with one paper residue: “The central claim concerns profile
choice.” The root scoped that sentence to the tested RQ2 hypothesis. After this
repair, the exact thesis remains in the abstract, introduction, and conclusion,
and no must-fix rule defect remains.
