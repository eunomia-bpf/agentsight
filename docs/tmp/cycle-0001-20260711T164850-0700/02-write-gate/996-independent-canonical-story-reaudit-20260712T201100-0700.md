# Independent Canonical Story Fidelity Re-audit

**Completed:** 2026-07-12T20:11:00-07:00  
**Reviewer:** new fresh read-only subagent  
**Verdict:** **PASS**

## M1 — RQ-specific controls

PASS. The Evaluation setup assigns distinct controls to RQ1--RQ4 and limits
reference annotations to scoring or explicit oracle bounds. It no longer
globally requires three attribution structures. Design's projection examples
describe supported functionality rather than a hierarchy-comparison thesis.

## M2 — AgentSight ingestion

PASS. The paper says AgentSight recordings enter after conversion to a
supported operation or trace input, matching `docs/implementation.md` and the
absence of a direct AgentSight-recording reader.

## M3 — RQ3 historical numbers

PASS. The paper contains the clean target-blind held-out protocol but none of
the historical 7/9, 6/7, 4/5, threshold, or transfer-result claims. It states
that historical mapping and boundary scores remain omitted pending
revalidation. No RQ3 result figure remains.

## M4 — RQ1 provenance

PASS. `docs/evaluation.md` now records R170 collection/configuration and path,
the exact R224 command and raw/metadata paths, identical-input baselines,
conservation and grouping metrics, R251 permutation protocol and raw paths,
R225 measure-sensitivity path, and the dirty-provenance/circularity boundaries.
This is adequate provenance for the retained narrowly interpreted numbers.

## M5 — Zero weights

PASS. The paper states that admitted results use positive integer weights,
imported zero is currently normalized to one, and no faithful-zero claim is
made. This matches the implementation frontier.

## Canonical Story Integrity

The repairs changed evidence and implementation boundaries only. They did not
change the canonical problem, exact thesis, two-object model, three-contribution
chain, exact four RQs, or conclusion. The active paper remains faithful to the
read-only submodule and the direct user disposition.
