# Blind Full-Paper Read and Attack Map

## Node record

- Completed: 2026-07-14T05:42:39-07:00
- Review object: complete active `docs/paper/`, read without editing
- Venue lens: AAAI 2027, cross-domain AI and systems
- Provisional verdict: **Weak Reject / incomplete but promising**

## Paper understood as written

The paper advances one large, simple thesis:

> **Agent observability needs profiling, not only debugging.**

Its core model contains exactly two abstractions: a weighted, fielded operation
and a query-time operation stack. AgentProf reconstructs operations, derives or
maps fields, projects them onto alternative hierarchies, folds additive
measures, and exports standard profiler outputs. The evaluation asks exactly
four fixed questions about attribution, problem correspondence, tag accuracy,
and profiling cost.

This is a worthwhile research direction. The paper challenges the assumption
that a run-local execution tree plus supplied metadata is sufficient for
population-level questions about recurring cost, failure, unsafe effects, and
wasted work. The thesis and four questions should not be narrowed or replaced.

## Strongest parts

1. The profiling-versus-debugging distinction is memorable and consequential.
2. Operations and operation stacks form a compact model rather than a stack of
   newly invented concepts.
3. The artifact covers real local trajectories, several independently released
   public workloads, standard pprof output, and a complete offline cost path.
4. RQ2 now contains cumulative evidence across three different public failure
   populations rather than one synthetic example.
5. Step 0006 adds a real held-out positive result to RQ3: all 287 eligible
   OSWorld-Human sessions are predicted out of fold, and the result passes an
   independent exact recomputation.

## Main attack map

### A1 — RQ1 construct validity is the dominant blocker

The current RQ1 experiment uses prompt tags to define task categories and then
measures how much those same categories remain mixed after grouping by the
tags. This demonstrates mass conservation, declared-category separation, and
association beyond session, but not independently correct resource
attribution. The paper itself says the experiment is conditional on declared
tags, while its closing sentence says RQ1 is answered.

The repository already contains the appropriate independent evidence source:
R114's fixed 20-task exact-lineage suite. The missing experiment is therefore
not a new research program. It is a current-AgentProf replay of existing
lineage truth through the operation/profile path.

### A2 — RQ2 needs a cumulative curve interpretation

RQ2 can reasonably be treated as positively answered; an old conjunctive gate
must not mechanically erase meaningful complete-curve evidence. The current
paper nevertheless presents AP, Work@80, and Work@50 without explaining the
common full-curve interpretation. REVIEW records this as a future WRITE task,
not authorization for another RQ2 benchmark or score variant and not a reason
to withdraw the question.

### A3 — RQ3 is a strong partial answer

Step 0006 supports boundary identity, not the complete task/phase/action/tag
hypothesis. The paper scopes this correctly. Later WRITE should make the
287-of-369 eligibility reason and the nine visible feature fields easy to find.
No further OSWorld boundary variant is justified.

### A4 — RQ4's boundary must remain explicit

RQ4 answers current-binary offline profile-construction cost. It does not
measure capture cost or complete semantic-field derivation cost. The separate
cache result comes from predecessor AgentFlame and is already labeled as such.

### A5 — Novelty rests on the least independently tested edge

Existing tools already offer cross-run dashboards, supplied-tag grouping, span
queries, and label-to-pseudo-frame operations. AgentProf's defensible novelty
is the combination of derived recurring semantic fields, exact propagation to
downstream measured effects, and query-time profiling hierarchies. Independent
cross-layer attribution evidence is therefore more valuable than another
category-separation plot.

## Blind verdict

The paper is not yet AAAI-ready, but the reason is a repairable evidence gap,
not a weak idea. Preserve the thesis, story, two-object model, and four RQs.
Close the RQ1 attribution edge with the already available R114 oracle before
opening any new dataset or mechanism.

