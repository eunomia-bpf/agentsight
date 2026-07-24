# Plan Review Round 02 — Fixed-Instruction Follow-On Structure Fidelity

**Reviewer role:** independent read-only experiment-plan reviewer
**Verdict:** **PASS**

All five Round-01 must-fix issues are resolved:

1. The step and plan now describe the analysis as manifest-defined,
   post-design, and post-aggregate follow-on evidence, explicitly excluding
   untouched external generalization.
2. The plan names one scorer, provides exact preflight and full commands, fixes
   the task-cluster order, resampling unit, multiplicity behavior, PRNG, draw
   count, seed, paired delta, and percentile interval.
3. B-cubed is tied to Bagga and Baldwin's defining partition metric, while
   exact boundary F1 is honestly identified as the paper's registered protocol
   derived from CodeTraceBench's released human stages rather than an official
   leaderboard metric.
4. The proposed claim now says “over the complete 364-session population” and
   requires exact metrics and heterogeneity, avoiding an unsupported
   per-session-dominance claim.
5. Preflight now verifies exactly 238 task-name clusters in addition to the
   session, operation, pair, exclusion, assignment, and framework counts.

The experiment remains a simple, scientifically useful supporting RQ3
analysis. The candidate, recurrence baseline, native-tree comparison, and
native-turn diagnostic use the same fixed rows and official reference.
ACT*ONOMY is appropriately handled as cited closest work rather than an
incompatible manufactured numerical row. No additional baseline, benchmark,
model run, custom metric, or review machinery is required before real
preflight.
