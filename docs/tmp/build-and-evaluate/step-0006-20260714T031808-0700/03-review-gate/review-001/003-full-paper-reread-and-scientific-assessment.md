# Full-Paper Reread and Scientific Assessment

## Node record

- Completed: 2026-07-14T05:42:39-07:00
- Read after: blind attack map and external primary-source search
- Paper verdict: **Weak Reject / incomplete but promising**
- Story verdict: preserve and strengthen; do not narrow

## RQ-by-RQ assessment

| RQ | Current scientific assessment | Required disposition |
|---|---|---|
| RQ1: attribution | Mechanism evidence is positive, but the headline answer lacks an independent attribution oracle. | Run one current-path R114 exact-lineage replay. |
| RQ2: problem correspondence | Cumulative evidence across three complete public workloads supports a positive answer. | No new experiment. Later WRITE should explain the full-curve synthesis instead of presenting disconnected favorable points. |
| RQ3: tag accuracy | Step 0006 gives a valid positive boundary-component answer. Task/phase/action fidelity remains broader future evidence. | No boundary variant now. Keep the broader hypothesis fixed. |
| RQ4: profiling cost | Current-binary offline construction cost is positively answered; predecessor cache evidence is separately bounded. | No new cost or cache run. |

## Step 0006 result assessment

The new numbers are supported:

- 287 eligible sessions, 3,978 operations, and 3,691 adjacent pairs;
- five session-blocked folds with each held-out session predicted once;
- learned confusion counts of 1,373 TP, 589 FP, 382 FN, and 1,347 TN;
- boundary F1 0.739 versus 0.645 for the strongest simple control;
- operation-weighted B-cubed F1 0.816 versus 0.678;
- a boundary-F1 win in every fold;
- current AgentProf folding of every predicted-group operation with exact mass
  conservation.

The model and fields were fixed before this full OOF rerun, but had previously
been developed on the same corpus. The result is a valid within-corpus
session-held-out estimate, not a fresh cross-family confirmation. The paper's
current boundary-component language is acceptable.

## Submission-level assessment

The central idea has top-conference potential because it turns accumulated
agent trajectories into a profiling population and makes responsibility
hierarchies explicit. The paper is not ready today because RQ1's declared-tag
separation is weaker than its paper-level attribution conclusion. The needed
repair is unusually favorable: R114 already supplies a complete, real,
negative-controlled exact-lineage experiment, so only current-profile-path
integration must be tested.

Non-experimental submission cleanup remains later work: add the closest
cross-run process-observability neighbors, clarify the cumulative RQ2 curve
interpretation, disclose RQ3 eligibility/features compactly, check AAAI's
source packaging rule for the input TikZ file, and remove the CID font before
submission. None changes the next empirical route.

