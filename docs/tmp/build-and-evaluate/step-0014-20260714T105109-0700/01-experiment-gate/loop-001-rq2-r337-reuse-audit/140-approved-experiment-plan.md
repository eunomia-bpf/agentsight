# Approved Experiment Plan — R337 Reuse Audit

## Approval

- **Approved:** `2026-07-14T11:02:18-07:00`
- **Plan:** `100-proposed-experiment-plan.md`, as revised after round 1
- **Serial reviews:** round 1 BLOCK with three minimal fixes; round 2 PASS;
  round 3 PASS
- **Authorized next phase:** REAL PREFLIGHT

The approved node contains one RQ2 hypothesis and one complete fixed-input
equivalence audit. It uses the existing R333/R337 scripts, four public
operation sources, six task slices, existing visible policies, and the existing
25% recall point. It adds no dataset, benchmark, model, label, metric, policy,
partition, interpolation, resample, custom script, human dependency, or paper
claim.

The preflight runs the actual lightweight R337 summarizer. The full run first
replays R333 directly from the four public operation files and verifies all
claim-bearing CSVs and selected scientific report fields. Only after that
equivalence passes does it replay R337 over the fixed equivalent R333 inputs.
Visible-field derivation is checked in the existing converter code, with
oracle fields used only for offline scoring.

The result may authorize only a secondary compactness statement against
fixed-session fragmentation, with raw-action and flat counterpoints visible.
It cannot authorize matched-granularity optimality, universal dominance,
human utility, downstream intervention, a new story, or a changed RQ.
