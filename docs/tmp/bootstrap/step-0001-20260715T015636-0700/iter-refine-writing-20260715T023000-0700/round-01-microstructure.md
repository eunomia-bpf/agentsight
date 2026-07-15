# Round 01: Microstructure

Skill: `check-paper-structure-flow`, Levels 2 and 3
Reviewer mode: independent read-only subagent

## Reviewer Findings

### Must-fix

1. The abstract skipped a distinct complementary-evidence thesis and did not
   mirror the introduction's paragraph roles.
2. The Evidence Model described survival as one of four exclusive outcomes
   even though survival is orthogonal to the observed/committed relation.
3. Visualization paragraphs opened with encodings and mixed several view
   families instead of following review need, encoding, rationale, and outcome.

### Should-fix

The reviewer identified an undefined artifact identity, an ambiguous “both
assumptions” referent, mixed roles in Background, unnamed/nonparallel goals, a
walkthrough that jumped to global UI state, weak design-to-implementation
mapping, nonparallel RQ blocks, mixed limitation classes, and three unrelated
Discussion roles in one paragraph.

### Consider

The reviewer suggested moving this paper's comparison action out of the
existing-solutions paragraph, replacing two unexplained supporting-view names,
and bridging evidence limitations to the historical visualization families.

## Root Decisions And Applied Fixes

- Accepted all Must-fix items. The abstract now states the three-source thesis.
  The representation uses a three-way observed/committed relation and a
  separate survival projection. Each visualization paragraph is decision-led,
  and unrelated view families have separate paragraphs.
- Accepted all Should-fix items. The introduction defines the exporter and
  suite on AgentSight's `agent-session` representation, challenged assumptions
  are explicit, Background retains only background claims, goals are labeled
  G1--G4, the walkthrough is split, Implementation opens with its design map,
  every RQ block restates its question, and validity classes are separated.
- Accepted the useful Consider items. The historical bridge is explicit, and
  supporting comparisons are defined by evidence inputs rather than the
  unexplained “ghost” label.

## Meaning And Evidence Check

The correction that survival is an orthogonal projection changes the schema
description but not the scientific thesis. It removes a logical error and
prevents future code from encoding nonexclusive states as a single enum. No
empirical answer or implemented capability was asserted.

## Verification

`make -C docs/paper` completed successfully and produced a four-page PDF. The
cumulative snapshot diff contains 253 insertions and 120 deletions. The root
re-read all changed paragraphs and confirmed that survival is now consistently
orthogonal to the observed/committed relation.
