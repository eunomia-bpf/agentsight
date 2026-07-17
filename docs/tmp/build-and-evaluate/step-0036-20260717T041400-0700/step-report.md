# Step 0036 Report: Same-Signal Diagnostic Decomposition

- started: 2026-07-17T04:14:00-0700
- completed: 2026-07-17T05:32:59-0700
- outer gate: `EXPERIMENT_GATE`
- selected RQ: RQ2 — Does profiler output correspond to real problems?
- final run status: valid
- tested hypothesis: supported
- research value: mechanism/workload boundary
- paper impact: compact table after the selected algorithm-improvement decision

## Decision Entering The Step

The Step 0035 whole-paper review found that the existing RQ2 MAP table compared
only AgentProf with raw-action grouping. It did not isolate whether the gain
came from external signal quality, semantic organization, unequal work, or
support propagation. Step 0036 therefore held all existing diagnostic signals,
profiles, field orders, operations, and targets fixed and compared four matched
views at one exact operation budget over all retained complete workloads.

The step did not change the paper thesis, four RQs, story, localizer, model,
benchmark, or submodule.

## Approved Experiment

The reviewed plan is
[`experiment-plan.md`](01-experiment-gate/experiment-001/experiment-plan.md),
with all plan-review rounds in
[`plan-review.md`](01-experiment-gate/experiment-001/plan-review.md).

The full population was:

| Benchmark | Trajectories | Operations | Target-bearing | Clean |
|---|---:|---:|---:|---:|
| AgentProcessBench | 1,000 | 8,509 | 614 | 386 |
| HINTBench | 536 | 12,877 | 400 | 136 |
| TraceElephant | 220 | 5,960 | 220 | 0 |
| Total | 1,756 | 27,346 | 1,234 | 522 |

The proposed view was current AgentProf semantic organization. Raw action and
atomic were the two main baselines; session was a coarse control. The standard
primary ranking measurement was per-target-trajectory non-interpolated AP/MAP.
Expected Recall@20% used exactly `ceil(0.2n)` operations per trajectory and
analytic expectation inside a cutoff tie. Official/source-native signal
metrics were reported separately and never credited to AgentProf.

## Execution And Repairs

Real preflight exercised real target-bearing and clean data, all official
scorers, all views, AP, fixed-budget recall, and support controls. During
preflight, the released HINT test taxonomy was found to differ from the retained
official evaluator taxonomy. The reviewed repair kept the official binary
detector, used the HINT paper's no-type overlap protocol over released target
steps, and reported typed/strict metrics as N/A rather than inventing a type
map.

The first complete run was independently rejected because zero-hit Wilson
lower bounds sometimes produced floating residues near `1e-17`; the support
control treated those as positive. The correction canonicalized values within
`64 * ulp(1)` to exact zero, re-evaluated all 24 HINT validation field orders,
and added the planned unmapped-target sensitivity. The selected order remained
`action,environment,phase,status`.

A second independent reviewer reproduced every primary metric but found that
pooled AP still selected operations from the original uncorrected list. The
final repair changed only that list source to the already corrected operation
groups. Both invalid attempts, their hashes, affected numbers, and authorized
repairs are preserved in
[`superseded-run-review.md`](01-experiment-gate/experiment-001/superseded-run-review.md).

The final full invocation completed twice with byte-identical core artifacts.
The authoritative raw root is:

```text
.agentsight/experiments/rq2-same-signal-diagnostic-decomposition-v1/full/
```

Final core hashes are:

- `summary.json`: `fd8a7b24121b0957a3080fab8586ea8b72b3624c543afecc11a112df99b100c9`
- `per-query.jsonl`: `e4efaa62b4a7ace599309f2876adb17a9efe4333fa185b219f6996fd7f795af1`
- `bootstrap-deltas.json`: `625aad9e06443464eaa44ea00e8bacf11ccd37601be9e965938f79f2592a4f25`

## Reviewed Results

| Benchmark | View | MAP | Expected Recall@20% | Pooled AP |
|---|---|---:|---:|---:|
| AgentProcessBench | AgentProf | 0.7889 | 0.5628 | 0.6918 |
|  | Raw action | 0.7732 | 0.5443 | 0.6688 |
|  | Atomic | **0.8632** | **0.6512** | **0.8152** |
|  | Session | 0.4481 | 0.3167 | 0.6693 |
| HINTBench | AgentProf | **0.4524** | **0.5741** | 0.2494 |
|  | Raw action | 0.2812 | 0.4860 | 0.1804 |
|  | Atomic | 0.4106 | 0.5484 | **0.2662** |
|  | Session | 0.1112 | 0.2189 | 0.1039 |
| TraceElephant | AgentProf | **0.2302** | **0.4575** | 0.0776 |
|  | Raw action | 0.1213 | 0.3483 | 0.0528 |
|  | Atomic | 0.2087 | 0.3321 | **0.0795** |
|  | Session | 0.0590 | 0.2237 | 0.0480 |

AgentProf-minus-raw paired intervals were positive for both MAP and
Recall@20% on all three workloads:

| Benchmark | MAP interval | Recall@20% interval |
|---|---:|---:|
| AgentProcessBench | `[+0.004565,+0.027106]` | `[+0.005274,+0.032305]` |
| HINTBench | `[+0.153772,+0.188223]` | `[+0.068632,+0.107685]` |
| TraceElephant | `[+0.077026,+0.141857]` | `[+0.054357,+0.164569]` |

The atomic comparison exposes the important boundary:

- atomic decisively beats AgentProf on both AgentProcessBench primary metrics;
- AgentProf beats atomic on HINT MAP, while its Recall interval crosses zero;
- AgentProf beats atomic on TraceElephant Recall, while its MAP interval crosses
  zero; and
- HINT semantic/raw grouping spreads nonzero support to 100% of clean
  trajectories and 76.54% of clean operations, versus 9.56% and 0.742% for
  atomic.

HINT's three projection-absent targets produce only a small sensitivity:
AgentProf MAP/Recall become 0.451646/0.573067 and raw becomes
0.280573/0.485168 when those targets are counted as unrecovered.

Official signal quality is recorded once: AgentProcessBench median StepAcc
0.6678 and FirstErrAcc 0.4900 over 20 judges; HINT risk Macro-F1 0.8960,
step-set F1 0.4750, and no-type overlap F1 0.4974; TraceElephant official agent
accuracy 0.3500 and step accuracy 0.1636. These values qualify the inherited
signals and are not AgentProf wins.

The final independent reconstruction is
[`result-review.md`](01-experiment-gate/experiment-001/result-review.md).

## Interpretation

Step 0036 supports its narrow tested hypothesis: on these retained workloads,
with the same external signal and exact operation budget, semantic operation
stacks consistently improve problem ranking and fixed-budget recovery over the
matched raw-action organization without adding clean-support flags relative to
raw action.

It does not show universal superiority over direct operation-local evidence,
lower analyst work, human productivity, automatic diagnosis, or an entire
positive answer to RQ2. Atomic's AgentProcessBench win and HINT's absolute
propagation are real, reviewed mechanism boundaries.

## Next Outer Decision

The explicit user objective asks to improve the current algorithm using
already-run trajectories rather than replace the story or collect another
benchmark. The highest-value candidate is therefore one parameter-free
local-order-preserving refinement: retain every strict atomic/local-score
preference and use semantic recurrence only to split exact local-score ties.
That proposal is Step 0037. It is adaptive mechanism development on already
observed populations, not an untouched generalization test. It may change the
paper's diagnostic ordering only after its own plan review, complete full run,
and fresh result review.
