# Independent Late-Recovery Outer Audit — Cycle 0003 EXPERIMENT

**Recorded:** 2026-07-13 16:51:03 PDT
**Independent auditor:** fresh experiment-gate auditor
**Verdict:** **PASS**
**Execution disposition:** `VALID`
**Tested-hypothesis disposition:** `INCONCLUSIVE`
**Correct original next gate:** `WRITE`
**Experiment rerun required:** no
**Scientific-contract change authorized:** no

## Recovery and chronology disclosure

This is a late recovery audit, performed after Cycle 0003 had already made the
incorrect direct transition `EXPERIMENT -> REVIEW`. The chronology was not
correct:

- `999-gate-exit-20260713T160631-0700.md` records `Next gate: REVIEW`;
- the experiment plan and result review also anticipated REVIEW for a mixed or
  inconclusive result;
- the governing orchestration rule requires every completed EXPERIMENT gate to
  transition to WRITE, including when an admitted result is valid but
  inconclusive; and
- the original gate transitioned without its required independent outer audit.

This audit repairs the missing audit requirement but does not pretend it
occurred before the transition. The original `999` remains preserved as
historical evidence. The later WRITE recovery reports honestly supersede only
its routing decision and record the required no-change WRITE skip before REVIEW
continues.

## Scope and evidence examined

The auditor explicitly used the `auto-research-orchestrator` and
`research-experiment-design` skills and read:

- the EXPERIMENT, handoff, outer-audit, and recovery state-machine provisions;
- `docs/user-instruction.md`;
- Cycle 0003 EXPERIMENT entry and exit;
- the complete HINTBench experiment plan;
- all five serial plan-review rounds and root repair responses;
- both REAL PREFLIGHT attempts and their independent reviews;
- the FULL report and `full-result-review.md`;
- validation, point-estimate, bootstrap, source, prompt, encoding, profile,
  operation, and localizer artifacts; and
- the adapter implementation controlling label isolation, AgentProf invocation,
  metrics, and bootstrap construction.

The auditor did not treat the previous `PASS / VALID / INCONCLUSIVE` verdict or
the proposed next mechanism as authority. It recomputed the exit decision from
the raw artifacts and governing return rules.

## Exit-criterion audit

| Criterion | Independent finding | Verdict |
|---|---|---|
| One fixed RQ | The experiment retains exact **RQ2: Does Profiler Output Correspond to Real Problems?** and does not split, merge, rename, or replace it. | PASS |
| One explicit hypothesis | It tests whether real AgentProf stack construction plus a validation-selected prefix policy reduces atomic-step inspection at at least 80% macro recall relative to four same-signal alternatives. It is one hypothesis inside RQ2, not the whole RQ. | PASS |
| Paper-value admission | It attacks the low-recall and ordinary-grouping reject argument using a fresh official target population; positive and inconclusive outcomes lead to different decisions. | PASS |
| Complete plan review | Five serial rounds checked source fidelity, IDs, label accounting, value semantics, flat fairness, tiers, bootstrap, visible fields, prompts, output limits, and commands. The final repaired plan received an independent PASS. | PASS |
| Real preflight | Attempt 1 contacted official sources and the live llama.cpp path, exposed a JSON-schema transport defect, and stopped before inference. Attempt 2 ran fixed risky/safe validation trajectories through the real 27B model, real AgentProf 0.2.37, all 24 candidates, baselines, controls, and reporting. | PASS |
| Complete FULL population | All 80 validation trajectories/3,050 operations and all 536 test trajectories/12,877 operations completed. All 616 model requests were terminal. | PASS |
| Planned cells and repetitions | All 24 validation orders, selected AgentProf test cell, four main baselines, exact-flat identity, width control, mappable-target sensitivity, and 10,000 paired bootstrap replicates completed. | PASS |
| Real AgentProf | Artifacts invoke `agentpprof 0.2.37`; count and shifted-value profiles recover exact localizer hits while working around documented zero coercion. Conservation checks pass. The downstream Wilson policy is not misrepresented as built-in AgentProf behavior. | PASS |
| Label isolation | Visible records exclude `is_risky`, risk annotations, and injected targets. Validation gold is loaded only after candidate outputs/profiles exist. Test gold is loaded only after terminal outputs, operations, and the fixed profile exist. | PASS |
| Baseline fairness | Native sequence, independent step, session, and raw action receive the same localizer output and visible operations. Flat same-projection code is correctly an identity control, not a baseline AgentProf must beat. | PASS |
| Target and denominator integrity | All 938 distinct test targets remain in the primary denominator; three released-data-absent targets remain common misses. Safe work is included and equal-score tiers are indivisible. | PASS |
| Raw artifact support | Source/prompt hashes, token counts, localizer rows, operation files, AgentProf profiles, validation selection, curves, bootstrap rows, and reports are present. FULL has 445 `ok_unsafe`, 171 `ok_safe`, no out-of-range prediction, and no FULL transport failure. | PASS |
| Two result audits | One reviewer matched all 616 requests and replayed AgentProf/raw-action replicates. A second implementation reconstructed selection, denominators, point estimates, and all four bootstrap distributions. | PASS |
| Frozen contract | Thesis, four RQs, positive RQ2 hypothesis, paper, and story remain unchanged. The mixed result stays in experiment history. | PASS |
| Correct handoff | The original REVIEW handoff was invalid; every valid admitted result returns to WRITE. The transparent later WRITE recovery implements the correct no-change action. | PASS after recovery |

## Arithmetic and scientific disposition

The stored point estimates are consistent with the 12,877-step denominator:

| Method | Work | Work fraction |
|---|---:|---:|
| AgentProf | 5,353 | 0.415702 |
| Native sequence | 7,460 | 0.579327 |
| Independent step | 12,877 | 1.000000 |
| Session | 7,616 | 0.591442 |
| Raw action | 5,961 | 0.462918 |

AgentProf reaches required macro recall at `0.802083`. Its
AgentProf-minus-baseline paired 95% intervals are:

| Comparison | 95% interval | Positive all-baseline threshold |
|---|---:|---|
| AgentProf - native | `[-0.222393, -0.101682]` | pass |
| AgentProf - independent step | `[-0.629675, -0.509304]` | pass |
| AgentProf - session | `[-0.225393, -0.104603]` | pass |
| AgentProf - raw action | `[-0.293709, +0.008566]` | **fail** |

The positive criterion required an upper endpoint below zero against all four
main baselines. The favorable point estimate cannot override the predeclared
uncertainty rule. Therefore:

- run status: `VALID`;
- tested hypothesis: `INCONCLUSIVE`;
- research value: informative mechanism/workload boundary;
- paper impact: no positive result authorization and no thesis challenge; and
- reuse policy: no HINTBench test retuning.

## Independent conclusion

The inner loop contacted a real official benchmark, a real local model service,
and the real AgentProf binary; completed its declared population and uncertainty
matrix; and did not overinterpret preflight, a proxy, or a favorable point
estimate. Raw action correctly determines the strict verdict.

No scientific or execution defect requires reopening EXPERIMENT. No story, RQ,
hypothesis, threshold, baseline, or HINTBench configuration may change in
response to the result.

**Final disposition: PASS.** Preserve the original erroneous route as history,
retain the transparent WRITE recovery, and let REVIEW complete from the
corrected lifecycle record.
