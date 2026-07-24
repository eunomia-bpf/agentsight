# Independent Result Review

**Verdict:** PASS  
**Registered hypothesis:** PARTIAL SUPPORT

## Independent recomputation

The reviewer independently reconstructed the scoring inputs from benchmark
projections, fixed operation paths, and separate label sources without calling
the experiment script. The recomputation exactly matched:

- 1,756 complete trajectories and 27,346 operations;
- 1,234 target-bearing queries scored by AP/MAP;
- 522 zero-positive queries loaded only for coverage;
- all twelve workload/method MAP values;
- every per-query AP value;
- all six paired point differences;
- every stored bootstrap draw, interval, median, and nonpositive-draw count;
- all 1,234 Step 0071 AgentProf-only AP values, with maximum absolute
  difference zero.

## Scientific interpretation

Relative to local-only, Local+AgentProf improves MAP on every workload:

| Workload | MAP difference | 95% interval |
|---|---:|---:|
| AgentProcessBench | +.0311 | [+.0237, +.0393] |
| HINTBench | +.1069 | [+.0934, +.1204] |
| TraceElephant | +.1168 | [+.0876, +.1479] |

Relative to information-matched raw-action plus source evidence, all three
intervals contain zero and the HINTBench point estimate is slightly negative.
The registered `PARTIAL SUPPORT` verdict is therefore correct.

The admissible paper claim is:

> On three complete public workloads, a fixed AgentProf profile refines exact
> ties in a local diagnostic score and raises MAP over local-only by
> .031--.117. It does not establish superiority over a raw-action refinement
> that retains the same source evidence.

This is adaptive mechanism evidence on previously observed populations, not
untouched generalization or validation of one universal LLM backend.

## Leakage, fairness, and metric audit

- All rank vectors exist before labels are loaded.
- The rank constructor accepts no target or correctness field.
- Source packets contain no target-label fields.
- Both local-first methods preserve every strict local-score order and exact
  ties.
- Candidate and raw baseline retain the same three source-evidence suffix
  frames and use identical workload-specific aggregation.
- AP/MAP and paired stratified/clustered bootstrap match the approved plan.

## Report-only correction

The implementation derives comparison-specific seeds from base `20260723`.
The full-run report now states all six actual seeds. Recomputing with one shared
seed leaves every interval decision unchanged. No implementation change or
rerun is required.

