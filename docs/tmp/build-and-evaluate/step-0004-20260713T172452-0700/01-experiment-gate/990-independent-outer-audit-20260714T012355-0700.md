# Independent Outer Audit: Step 0004 EXPERIMENT_GATE

- Timestamp: `2026-07-14T01:23:55-07:00`
- Phase / step / gate: `BUILD_AND_EVALUATE / 0004 / EXPERIMENT`
- Audited loop: `loop-001-rq2-traceelephant`
- Verdict: **PASS — transition to WRITE; do not open another RQ2 scheme**

## Audit Scope And Prior Verdict Disclosure

The fresh auditor read the complete user instructions and idea story, every
TraceElephant plan, review, implementation, preflight, interruption, FULL, and
result-review report, sufficient terminal artifacts under
`.agentsight/experiments/traceelephant-rq2-v1/`, and the admitted cumulative RQ2
history in `docs/evaluation.md`.

The auditor saw but did not directly adopt the following prior verdicts: plan
review `MUST-FIX -> MUST-FIX -> PASS`; adapter review `MUST-FIX -> MUST-FIX ->
PASS`; preflight repair then `PASS`; scorer-repair proposal and implementation
`PASS`; FULL `VALID / COMPLETE / INCONCLUSIVE`; and independent result review
`PASS`. The audit independently sampled the full summary, compressed
permutation/bootstrap results, method index, population counts, primary curves,
target normalization, and scorer isolation.

## Completion And Validity

The inner loop is complete and valid:

- 220/220 official failures and 5,960/5,960 atomic steps;
- 220 terminal localizer outputs and 405 terminal tag batches;
- real `agentpprof 0.2.37` output for the AgentProf and source-native headline
  paths, plus declared controls;
- 200/200 matched semantic permutations and 10,000/10,000 paired bootstrap
  replicates;
- exact independent reconstruction of both headline profiles; and
- valid target mappings for all 220 failures.

The two non-canonical official step strings were normalized only inside the
scorer. Visible inputs, localizer and tagger output, operations, profiles,
permutations, and comparison budgets were unchanged. One source
agent/component inconsistency remains visible as a data diagnostic rather than
being silently relabeled. No defect requires a rerun or another control.

## Tested Hypothesis

The experiment-specific verdict remains:

```text
run status: VALID / COMPLETE
tested hypothesis: INCONCLUSIVE
research value: supporting
paper impact: additional RQ2 evidence, not a thesis challenge
```

At the predeclared 80% macro decisive-step-recall point, AgentProf requires
1.0000 work and raw action requires 0.7191. The AgentProf-minus-raw interval is
`[-0.0190, +0.4586]`, and the matched-permutation result is `p=1.0`. This does
not support the fixed 80% construction; because the interval crosses zero, it
also does not establish a reliable contradiction.

The complete curve nevertheless has a real positive region: AgentProf reaches
50% macro recall at 19.55% work versus 46.64% for raw action, and at about 20%
work reaches 52.57% macro recall versus 23.79%. The failure is concentrated in
the large high-recall tied tier, not an absence of correspondence throughout
the profile.

## Cumulative Paper-Level RQ2 Answer

The paper-level RQ asks whether profiler output corresponds to real problems;
it is not a requirement to win at every cutoff, workload, and secondary
conjunct. The cumulative evidence now supports a positive, accurate answer:

> Target-blind AgentProf profiles concentrate independently annotated real
> problems across multiple public workloads and expose them earlier at useful
> inspection budgets; very high-recall tail efficiency depends on the ranking
> signal and tie structure.

The load-bearing evidence is:

- AgentProcessBench mean-risk: semantic-minus-raw macro AP `+0.031522`, paired
  95% interval `[+0.015138, +0.053514]`, matched-refinement `p=0.009950`;
- AgentProcessBench Wilson: macro AP `+0.024515`, interval
  `[+0.016472, +0.051486]`, matched-refinement `p=0.004975`, with favorable AP
  and work point estimates in all four families; this reused observed targets
  and is supporting rather than an independent holdout;
- HINTBench: 80%-recall work 41.57% for AgentProf versus 46.29% for raw, with
  the raw comparison narrowly inconclusive rather than reversed; and
- TraceElephant: the independently verified early-curve advantage above,
  followed by the bounded high-recall tied-tier limitation.

These are different datasets, target definitions, and inspection regimes. The
cumulative result answers the core RQ2 correspondence/concentration question.
Continuing to change tags, scores, cutoffs, or benchmarks would mainly pursue
an unnecessarily universal local conjunct and has lower paper value than
testing another fixed RQ.

## Direction, Scope, And Transition

No story or scope drift occurred. The thesis remains exactly **“Agent
observability needs profiling, not only debugging.”** All four author-fixed RQs
remain intact, operations and operation stacks remain the only core
abstractions, and this local inconclusive result was not promoted to a thesis
challenge or used to weaken RQ2.

Two outer-state corrections are required: interpret 007's “no positive result”
as local to its 80%-recall tested hypothesis, and replace the stale
TraceElephant-next wording in `docs/evaluation.md` with the completed cumulative
RQ2 disposition. Those are ordinary canonical-memory updates, not inner-loop
repairs.

The gate passes to WRITE. WRITE should express the cumulative positive RQ2
answer from the strongest evidence without inserting intermediate failure
history or changing the canonical story. REVIEW then compares the remaining
fixed RQs and selects the next experiment; RQ3 is the leading candidate because
independent held-out tag accuracy and stability are now the clearest dependency
behind the RQ1/RQ2 interpretation.
