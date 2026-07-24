# RQ3 Return-Distance Correction Review

**Reviewer:** independent read-only research subagent

**Date:** 2026-07-23

**Verdict:** **PASS**

The corrected estimator counts only path-resolved calls strictly between two
module visits (`A,B,A = 1`). The synthetic assertion encodes that definition.
An independent rerun from the frozen inputs reproduced eight CSVs, two PNGs,
and `result.md` byte for byte. It retains 71,238 adjacent transitions and
10,959 observed returns; qualified per-project medians are 3, 4, 4, 3, and 2,
while the AgentSkill paper remains N/A at three returns.

All 18 hashes in `commands.log` match the current RQ4 input, three committed
gzip archives, eight CSVs, four figures, result, and script. The correction
changes the numerical distance by one but not transition counts, return counts,
eligibility gates, or the bounded path-locality/short-return finding.

The paper, result, and figure now say `strictly between visits`; no duration,
internal attention, productivity, population, or causal interpretation is
introduced.
