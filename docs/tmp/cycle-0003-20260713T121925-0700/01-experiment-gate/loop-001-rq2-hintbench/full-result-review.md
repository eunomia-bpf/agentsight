# RQ2 HINTBench FULL Result Review

## Review status

Two independent result reviews have converged.  The experiment review is
**PASS**, execution validity is **VALID**, and the predeclared tested-hypothesis
verdict is **INCONCLUSIVE**.  This report is experiment memory, not paper text,
and it does not authorize a thesis, story, RQ, or hypothesis change.

## Fixed question and tested hypothesis

The fixed paper RQ is **RQ2: Does Profiler Output Correspond to Real
Problems?**  This one experiment tested whether the same target-blind
step-localization signal, organized by the real AgentProf stack plus a
validation-selected multiresolution prefix policy, requires less atomic-step
inspection to reach at least 80% macro recall than native inspection,
independent-step ranking, per-session grouping, and raw-action grouping.

The paper thesis remains exactly:

> **Agent observability needs profiling, not only debugging.**

## Execution completion

**Execution status:** VALID

- Official validation population: 80/80 trajectories and 3,050 steps.
- Official test population: 536/536 trajectories and 12,877 steps.
- Terminal model outputs: 616/616; 445 `ok_unsafe`, 171 `ok_safe`, and zero
  out-of-range predicted steps.
- Transport failures: zero during FULL.
- Validation candidates: 24/24 field orders through real
  `agentpprof 0.2.37`.
- Selected validation-only order: `action,environment,phase,status`.
- Declared test methods and controls: all terminal.
- Bootstrap: 10,000/10,000 complete trajectory-cluster replicates, seed
  `20260713`, preserving 400 risky and 136 safe draws per replicate.
- Flat reconstruction identity: exact in the point estimate and all 10,000
  replicates.
- End-to-end runtime: 5,863.55 seconds; post-localizer AgentProf work took 3.64
  seconds.

## Test point estimates at at least 80% macro recall

| Method | Atomic work | Work fraction | Macro recall | Safe work |
|---|---:|---:|---:|---:|
| AgentProf | 5,353 | 0.415702 | 0.802083 | 1,209 |
| Native sequence | 7,460 | 0.579327 | 0.800625 | 266 |
| Independent step | 12,877 | 1.000000 | 0.997917 | 3,368 |
| Session | 7,616 | 0.591442 | 0.815417 | 266 |
| Raw action | 5,961 | 0.462918 | 0.800000 | 1,423 |
| Exact flat identity control | 5,353 | 0.415702 | 0.802083 | 1,209 |
| Width-only control | 11,516 | 0.894308 | 0.827708 | 2,908 |

AgentProf's point work reduction is 16.36 percentage points versus native,
58.43 points versus independent step, 17.57 points versus session, and 4.72
points versus raw action.

## Paired trajectory-cluster uncertainty

The predeclared AgentProf-minus-baseline 95% percentile intervals are:

| Baseline | 95% interval |
|---|---:|
| Native sequence | [-0.222393, -0.101682] |
| Independent step | [-0.629675, -0.509304] |
| Session | [-0.225393, -0.104603] |
| Raw action | [-0.293709, 0.008566] |

AgentProf reaches the target recall and is decisively lower-work than three
main baselines.  The raw-action point estimate favors AgentProf, but its paired
interval includes zero by 0.008566.  Because the approved positive threshold
required the upper endpoint to be below zero against all four baselines, the
correct predeclared tested-hypothesis verdict is **INCONCLUSIVE**, not positive.

## Interpretation boundary

- The exact flat tie is an algebraic implementation control and is expected.
- The Wilson prefix score is a declared downstream policy, not an AgentProf
  built-in ranker.
- HINTBench is an official human-verified synthetic benchmark, not a real
  execution trace.
- This experiment tests one consequence of RQ2.  It does not answer the whole
  RQ2 and cannot replace or narrow the paper thesis, four RQs, story, or fixed
  positive hypothesis.
- No test-target retuning is allowed.  The nearly positive raw-action interval
  is not permission to change the bootstrap, field order, recall target, or
  baseline after seeing the result.
- The mixed result stays in experiment memory and must not be inserted as a
  negative paper result.  The next action must be chosen by independent result
  review and the outer research loop: repair a genuine implementation defect
  if one exists, otherwise design a materially stronger complete experiment or
  mechanism that continues to test the fixed ambitious hypothesis.

## Independent result audits

### Complete scientific result review

The fresh reviewer independently matched all 616 request bodies, hashes, token
usage values, model responses, parser outputs, and terminal cache rows.  It
confirmed that test gold did not participate in representation construction,
field-order selection, ranking, or parameter choice; all 24 candidate orders
were selected only on validation; and test used only the selected
`action,environment,phase,status` order.

All four main baselines, the exact flat control, width-only control, mappable
sensitivity, complete-tier semantics, and the 10,000-replicate bootstrap were
independently checked.  The reviewer replayed every AgentProf/raw-action
replicate and matched the stored rows.  It found 578 positive raw-action deltas,
13 exact zeros, and the same `+0.008566` upper endpoint.  The final verdict was
**PASS / VALID / INCONCLUSIVE**.

### Independent bootstrap and denominator audit

A second reviewer independently reconstructed the unique validation selection,
all five main point estimates, target/work denominators, selected tier sizes,
and real AgentProf count/shifted totals.  It then used a separate bootstrap
implementation to regenerate every replicate for AgentProf and all four
baselines.  All 10,000 rows and all four NumPy linear intervals matched exactly.
It confirmed that each draw preserves a complete trajectory, risky/safe strata,
absent targets, safe work, group n/h recomputation, and the resampled global
work denominator.  Its final verdict was also **PASS**, with
**INCONCLUSIVE** as the only correct predeclared scientific verdict.

## Outer-loop route

This is a mechanism/workload boundary, not a direct thesis challenge.  The
experiment gate closes without editing `docs/paper/`.

1. Do not adjust HINTBench field order, threshold, baseline, metric, or
   representation after seeing test results.
2. Preserve the exact thesis, all four RQs, the RQ2 wording, the positive RQ2
   hypothesis, and the authoritative paper story.
3. Route to a complete-paper REVIEW to select the next highest-paper-value
   experiment.
4. A subsequent RQ2 experiment should use a fresh official held-out benchmark,
   keep raw action as a mandatory baseline, and define a stronger target-blind
   mechanism on separate development evidence before the complete test run.
   The principled mechanism direction is to combine action with preceding
   intent, observed environment response, and outcome state so cross-trajectory
   context supplies distinctions unavailable to raw action alone.
5. Keep this mixed result in research history and REVIEW input.  Do not insert
   it into the paper as a negative result and do not use it to weaken the claim.
