# Independent Step 0036 Result Review

## Verdict

The final pooled-AP repair is valid. A fresh reviewer independently
reconstructed the experiment from the three retained source roots without
editing files. The final artifacts were:

- `summary.json`: `fd8a7b24121b0957a3080fab8586ea8b72b3624c543afecc11a112df99b100c9`
- `per-query.jsonl`: `e4efaa62b4a7ace599309f2876adb17a9efe4333fa185b219f6996fd7f795af1`
- `bootstrap-deltas.json`: `625aad9e06443464eaa44ea00e8bacf11ccd37601be9e965938f79f2592a4f25`

## Completion And Populations

All planned populations and all four views were present:

| Benchmark | Trajectories | Operations | Target-bearing | Clean | Mapped / official targets |
|---|---:|---:|---:|---:|---:|
| AgentProcessBench | 1,000 | 8,509 | 614 | 386 | 2,710 / 2,710 |
| HINTBench | 536 | 12,877 | 400 | 136 | 935 / 938 |
| TraceElephant | 220 | 5,960 | 220 | 0 | 220 / 220 |
| Total | 1,756 | 27,346 | 1,234 | 522 | — |

All 1,234 target-query records were reconstructed field for field. AgentProf,
raw action, atomic, and session scores covered the same operation arrays.
HINT's absent targets were exactly `test:170` step 7, `test:233` step 9, and
`test:516` step 13. The unrecovered-target sensitivity was present and correct.

## AP, MAP, Pooled AP, And Fixed-Budget Recall

Independent scikit-learn AP recomputation reproduced every per-query AP and all
MAP values:

| Benchmark | View | MAP | Expected Recall@20% | Pooled AP |
|---|---|---:|---:|---:|
| AgentProcessBench | AgentProf | 0.7889194040 | 0.5627655974 | 0.6917790610 |
|  | Raw action | 0.7731699925 | 0.5443463472 | 0.6688114326 |
|  | Atomic | 0.8631711915 | 0.6511848942 | 0.8151576029 |
|  | Session | 0.4480756864 | 0.3166672941 | 0.6693432002 |
| HINTBench | AgentProf | 0.4523726620 | 0.5741087963 | 0.2494394333 |
|  | Raw action | 0.2812365482 | 0.4860327381 | 0.1803663657 |
|  | Atomic | 0.4105587754 | 0.5483936154 | 0.2661993430 |
|  | Session | 0.1112386002 | 0.2188575263 | 0.1039281827 |
| TraceElephant | AgentProf | 0.2301683213 | 0.4575294023 | 0.0775686024 |
|  | Raw action | 0.1212702780 | 0.3482703313 | 0.0527910958 |
|  | Atomic | 0.2087125567 | 0.3321285369 | 0.0794592408 |
|  | Session | 0.0590416594 | 0.2237194751 | 0.0479732794 |

The specifically reviewed HINT pooled AP values are exact:

- AgentProf: `0.24943943330738927`
- Raw action: `0.18036636574766293`
- Atomic: `0.2661993430480931`
- Session: `0.10392818270272557`

The repaired code constructs pooled AP from operations flattened from the
already canonicalized per-query groups. Per-query AP, Recall@20%, unmapped-
target sensitivity, clean support, pooled AP, and bootstraps now all descend
from those same corrected rows. The validation recheck canonicalizes
separately. Official-signal evaluation does not use organization scores. The
reviewer found no remaining path that bypasses canonicalization.

### Exact-K Tie Handling

Every query used `K = ceil(0.2n)`. The inspected numerators/denominators were:

- AgentProcessBench: `1,467 / 6,050`
- HINTBench: `2,060 / 9,509`
- TraceElephant: `1,281 / 5,960`

For every view and query, the reviewer reproduced the cutoff score, tier size,
tier targets, available slots, analytic expectation, attainable worst/best
recall, and source-order sensitivity. All obeyed
`worst <= expected <= best`, and exactly K operations were allocated.

Macro averages of the retained per-query bounds were:

| Benchmark | View | Worst | Expected | Best | Largest cutoff tier |
|---|---|---:|---:|---:|---:|
| AgentProcessBench | AgentProf | 0.5414 | 0.5628 | 0.6002 | 51 |
|  | Raw action | 0.5134 | 0.5443 | 0.5866 | 51 |
|  | Atomic | 0.6259 | 0.6512 | 0.6936 | 69 |
|  | Session | 0.0833 | 0.3167 | 0.7562 | 95 |
| HINTBench | AgentProf | 0.5373 | 0.5741 | 0.6094 | 9 |
|  | Raw action | 0.4006 | 0.4860 | 0.5652 | 10 |
|  | Atomic | 0.4460 | 0.5484 | 0.9542 | 42 |
|  | Session | 0.0000 | 0.2189 | 0.9942 | 42 |
| TraceElephant | AgentProf | 0.3227 | 0.4575 | 0.6955 | 78 |
|  | Raw action | 0.0773 | 0.3483 | 0.8000 | 93 |
|  | Atomic | 0.1591 | 0.3321 | 1.0000 | 94 |
|  | Session | 0.0000 | 0.2237 | 1.0000 | 94 |

Arbitrary source ordering therefore does not determine the primary fixed-
budget result.

## Numerical Correction And Validation Selection

The tolerance is `64 * ulp(1) = 1.4210854715202004e-14`.

Only HINT Wilson-zero residues were changed:

- AgentProf: 1,300 operation scores
- Raw action: 809
- Session: 1,674
- Atomic: 0

The largest corrected residue was `4.8683609171202235e-17`. The smallest
retained genuine positive HINT score was `0.0012018583516737803`. Even a
hypothetical one-hit Wilson score over all 27,346 operations is
`6.455253145158248e-06`, over 454 million times the tolerance. The correction
therefore cannot erase a genuine one-hit signal.

All 24 validation field-order candidates were independently reevaluated. Every
corrected candidate row matched the retained summary. The winner remained:

- order: `action,environment,phase,status`
- work: `2,109 / 3,050 = 0.6914754098`
- validation macro recall: `0.8`
- canonicalized selected-candidate leaf scores: 32
- affected selected-candidate operation assignments: 123

There was no post-repair field-order change or test-set reselection.

## Bootstrap Audit

All 12 retained arrays—120,000 draws total—were reproduced exactly from the
reconstructed query rows, including seeds, cluster/stratum sampling, medians,
nonpositive counts, and nearest-rank intervals.

| Benchmark | Effect | 95% interval |
|---|---|---:|
| AgentProcessBench | AP, AgentProf - raw | `[+0.004565, +0.027106]` |
|  | AP, AgentProf - atomic | `[-0.097185, -0.052333]` |
|  | Recall, AgentProf - raw | `[+0.005274, +0.032305]` |
|  | Recall, AgentProf - atomic | `[-0.114100, -0.063464]` |
| HINTBench | AP, AgentProf - raw | `[+0.153772, +0.188223]` |
|  | AP, AgentProf - atomic | `[+0.019483, +0.064043]` |
|  | Recall, AgentProf - raw | `[+0.068632, +0.107685]` |
|  | Recall, AgentProf - atomic | `[-0.000650, +0.052495]` |
| TraceElephant | AP, AgentProf - raw | `[+0.077026, +0.141857]` |
|  | AP, AgentProf - atomic | `[-0.027131, +0.069809]` |
|  | Recall, AgentProf - raw | `[+0.054357, +0.164569]` |
|  | Recall, AgentProf - atomic | `[+0.069466, +0.183924]` |

## Official-Signal Metrics

The official/source-native paths also reproduced:

- **AgentProcessBench:** all 20 judges over all four datasets. Median StepAcc
  was `0.6678223058`; median FirstErrAcc was `0.49`. Across judges, median
  clean-trajectory any-harmful rate was `0.1113989637`, and median clean-
  operation harmful rate was `0.0260268402`.
- **HINTBench:** all 536 raw outputs reparsed identically, including parse
  status and predicted step sets. Risk confusion was TP 369, TN 123, FP 13,
  FN 31; Macro-F1 `0.8960049387`; step-set F1 `0.4749721913`; published
  no-type overlap F1 `0.4974424552`. Typed and strict results are correctly N/A
  because the retained evaluator and test snapshot use incompatible
  taxonomies.
- **TraceElephant:** all 220 predictions were present. The official substring
  evaluator produced agent accuracy `0.35` and step accuracy `0.1636363636`;
  the exact-normalized secondary result was step accuracy `0.1590909091` and
  joint accuracy `0.15`.

The recorded repository commits and HINT hashes matched the plan.

## Clean Support And Baseline Fairness

Clean support was recomputed independently:

| Benchmark | View | Clean-trajectory support | Clean-operation support |
|---|---|---:|---:|
| AgentProcessBench | AgentProf | 0.005181 | 0.000813 |
|  | Raw action | 0.005181 | 0.000813 |
|  | Atomic | 0.018135 | 0.003253 |
|  | Session | 0 | 0 |
| HINTBench | AgentProf | 1.0 | 0.765439 |
|  | Raw action | 1.0 | 0.765439 |
|  | Atomic | 0.095588 | 0.007423 |
|  | Session | 0.095588 | 0.106888 |

AgentProf and raw action had identical per-operation clean-support flags on
both clean-capable workloads, not merely equal aggregate rates. AgentProf
therefore did not add clean support relative to the declared raw-action
comparator. However, HINT reveals a severe absolute propagation boundary: both
grouped views spread nonzero support to every clean trajectory and 76.5% of
clean operations, versus 9.56% and 0.74% for atomic scoring.

Both main baselines genuinely engaged. AgentProf scores differed from raw
action on 5,946 AgentProcessBench, 3,406 HINT, and 2,809 TraceElephant
operations; they differed from atomic on 8,246, 10,569, and 5,960 operations
respectively. Hundreds of per-query AP and recall values changed. No baseline
suffered missing coverage, an interface failure, unequal K, or a different
diagnostic signal.

## Leakage And Omissions

The reviewer found no result-invalidating leakage:

- AgentProcessBench materialized external risks and all profiles before
  loading human labels.
- HINT prompts contain visible trajectories, not `risk_labels` or
  `injected_risks`. Test localizer/profile outputs are built before test
  targets are loaded. Validation targets select the field order, which is
  disclosed and was not changed during this rerun.
- TraceElephant's visible projection strips `mistake_agent`, `mistake_step`,
  and `mistake_reason`; request construction precedes the isolated scoring
  process. Its localizer is reference-assisted through task outcomes/ground
  truth, but does not receive scorer labels, matching the declared limitation.
- Targets enter the current adapter only to form evaluation labels and
  sensitivity denominators. Scores, groups, cutoffs, and the HINT order were
  not retuned.

No planned population, negative comparator, clean row, official metric, target
sensitivity, bootstrap array, or tie-bound record was omitted. TraceElephant
clean behavior is correctly N/A. HINT typed metrics are correctly N/A rather
than false zeros. The report rounds values, but the full-precision summary and
per-query bounds are retained.

## Scientific Interpretation

The narrow Step 0036 hypothesis is supported:

- AgentProf beats raw action on both MAP and expected Recall@20% on all three
  workloads.
- Every paired raw-action interval is positive.
- It uses the same operation budget and fixed external signal.
- It adds no clean-support flags relative to raw action on the two workloads
  with clean trajectories.

This does not establish that semantic propagation is universally better than
directly inspecting the external signal:

- Atomic decisively beats AgentProf on both AgentProcessBench metrics.
- HINT AgentProf beats atomic on MAP, but its Recall@20% interval crosses zero
  and its clean propagation is dramatically worse.
- TraceElephant AgentProf beats atomic on Recall@20%, while the AP interval
  crosses zero.
- The TraceElephant localizer is weak and reference-assisted, and all retained
  populations were previously inspected.

The result therefore supports the local raw-action comparison while
establishing an important mechanism/workload boundary. It is evidence toward
RQ2, not an answer to “Does profiler output correspond to real problems?” as a
whole. The defensible paper claim is that operation-stack organization
improves fixed-budget recovery over matched raw-action grouping on these
retained workloads; the paper must separately report the atomic losses and
HINT clean-propagation cost.

run status: valid
tested hypothesis: supported
research value: boundary
paper impact: table
next paper decision: Add the compact same-signal RQ2 table, claim only the
consistent advantage over raw-action grouping, disclose the AgentProcessBench
atomic loss and HINT clean-support propagation, and do not present Step 0036 as
resolving RQ2.
