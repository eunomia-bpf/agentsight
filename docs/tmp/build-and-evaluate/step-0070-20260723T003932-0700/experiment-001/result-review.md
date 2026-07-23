# Independent Result Review

## Review History

The reviewer performed three serial read-only result reviews.

### Review 1 — INVALID

The first AgentProcess naming comparison violated the plan's fixed-evidence
invariant. Its retained current profile had a two-frame source suffix
`(source_kind, source_call)`, while the candidate had a three-frame suffix
`(source_kind, source_call, outcome)`. The favorable `+.018` result was
rejected. HINT and Trace remained locally valid.

The reviewer independently diagnosed the confound by holding each suffix
version fixed. Neither fair AgentProcess contrast supported a naming gain.
This review caused the preceding names—not the candidate—to be rerun through
the same three-frame evaluator.

### Review 2 — REVISE

The repaired artifacts were valid and their MAP/bootstrap results reproduced,
but the scorer checked only byte-identical source rows. It did not mechanically
verify the fixed-group path decomposition. The reviewer required:

- fixed-group operation, sequence, and family coverage;
- identical native and recurrence paths;
- identical automatic path depth;
- each source-preserving path to extend its corresponding automatic path; and
- identical remaining evidence suffix.

It also required the plan and authoritative paper/evaluation text to stop
pointing to the rejected AgentProcess comparison.

### Review 3 — PASS

**Final verdict: PASS — VALID / COMPLETE.**

The scorer now enforces every listed invariant in
`require_fair_group_inputs`. A negative unit test holds source JSONL fixed
while changing the fixed-group evidence suffix and confirms rejection. All
seven canonical-comparison tests pass. The three comparison artifacts were
rerun without changing their results.

## Independently Recomputed Results

| Workload | Current | Canonical | Delta | 95% interval | Verdict |
|---|---:|---:|---:|---:|---|
| AgentProcessBench | 0.794635 | 0.790615 | -0.004020 | [-0.011363, 0.002817] | Inconclusive |
| HINTBench | 0.424437 | 0.432392 | +0.007955 | [0.002436, 0.013734] | Positive |
| TraceElephant | 0.260070 | 0.259313 | -0.000758 | [-0.002273, 0] | Inconclusive |

Independent per-query AP/MAP recomputation agrees with stored rows within
`3.3e-16`. Registered bootstrap seeds, strata, clusters, intervals, medians,
and nonpositive-draw counts reproduce exactly.

For every workload:

- current and candidate `source-operations.jsonl` are byte-identical;
- operation/sequence/family, native, recurrence, and semantic depth align;
- source-preserving paths extend their automatic paths;
- three-frame evidence suffixes match;
- pprof sample mass and unique evidence-ID coverage are complete; and
- stock pprof readback succeeds.

## Paper-Safe Interpretation

Holding marks and source evidence fixed, canonical operation names improve
HINTBench MAP from 0.424 to 0.432. AgentProcess changes from 0.795 to 0.791 and
Trace from 0.260 to 0.259; both paired intervals include zero. The benefit is
therefore workload-dependent. The unified identity is retained for readability
and cross-session aggregation, not because it improves every localization
score.

The final absolute MAP values `0.791/0.432/0.259` and evidence-versus-agent-only
effects `+0.056/+0.151/+0.065` remain valid. The paper must not claim an
AgentProcess naming gain or formal equivalence on the two inconclusive
workloads.
