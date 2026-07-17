# Independent Result Review: Local-Evidence-Preserving Semantic Ranking

**Reviewed:** 2026-07-17
**Selected RQ:** RQ2 — Does profiler output correspond to real problems?
**Reviewer role:** fresh read-only result reviewer with no execution role
**Final raw root:** `.agentsight/experiments/rq2-local-first-semantic-ranking-v1/full/`

## Formal Judgment

- **run status:** `valid`
- **tested hypothesis:** `inconclusive`
- **research value:** `supporting`
- **paper impact:** `mechanism or workload boundary`
- **next paper decision:** retain the Step 0036 RQ2 evidence boundary, close
  this parameter-free candidate as an all-workload replacement, and do not
  alter the thesis, four RQs, or story. Step 0037 may appear only as explicitly
  post-hoc adaptive mechanism evidence; it must not replace the confirmatory
  RQ2 result or motivate more score tuning on these same populations.

The exact registered classification is:

- AgentProcessBench: `INCONCLUSIVE`
- HINTBench: `SUPPORTED`
- TraceElephant: `SUPPORTED`
- overall intersection: `INCONCLUSIVE`

AgentProcessBench misses the support condition because candidate-minus-
local-plus-raw MAP has interval `[-0.000497,+0.006852]`. No primary comparison
has an upper bound below zero, so the result is not contradicted.

## Independent Reconstruction And Completion

The reviewer reconstructed the result from all three source roots and the
reviewed Step 0036 artifacts instead of accepting `summary.json` or
`report.md`:

- all 1,756 trajectories and 27,346 operations are present;
- all 1,234 target-bearing trajectories have per-query AP and Recall records;
- all 522 clean trajectories participate in the support check;
- all 27,346 target-free rank-key rows and all four rankings are present;
- atomic and incumbent semantic AP and Recall reproduce Step 0036 exactly,
  per query and in aggregate; and
- all 18 × 10,000 = 180,000 bootstrap draws reproduce the stored arrays
  element-for-element.

| Workload | Trajectories | Operations | Target-bearing | Clean | Mapped / official targets | Target-query operations / inspected K |
|---|---:|---:|---:|---:|---:|---:|
| AgentProcessBench | 1,000 | 8,509 | 614 | 386 | 2,710 / 2,710 | 6,050 / 1,467 |
| HINTBench | 536 | 12,877 | 400 | 136 | 935 / 938 | 9,509 / 2,060 |
| TraceElephant | 220 | 5,960 | 220 | 0 | 220 / 220 | 5,960 / 1,281 |
| **Total** | **1,756** | **27,346** | **1,234** | **522** | — | — |

HINT's three projection-absent targets are exactly `test:170` step 7,
`test:233` step 9, and `test:516` step 13.

Final artifact hashes are:

| Artifact | SHA-256 |
|---|---|
| `summary.json` | `b1b85841dc90ee0d89e43899f94d15e6a140ef169d04f6d876344ea5c58c7ae6` |
| `per-query.jsonl` | `a8d42c1a86cc703e658a90232a6b0d5bc2301380b61af2acf3b45cd5326a58b6` |
| `rank-keys.jsonl` | `7f852a01f5d4697d5121f06ca7bfc8fcaffe0208a324eff5208ec7e8f3d90b63` |
| `rank-key-mappings.json` | `c86cf02e4dd089934bb10edaa8f0edbaa94596c8ae423b66e0068e1d654e4405` |
| `bootstrap-deltas.json` | `e0e5671b8f1eef0e60c2850e8d8b59492d6081e1994bb37728c9b7389be84447` |
| `report.md` | `4b81f364b9f4c3f4fe83d35466291b29e09779b1f88e1dcf8dbc98586954c57c` |

## Rank Construction And Leakage

`construct_rank_keys(score_rows)` accepts only `local`, `semantic`, and
`raw_action`. It cannot accept labels, target IDs, gold annotations, or
correctness fields. Persisted rank-key rows contain none of those fields.

| Workload | `(a,s)` tiers | `(a,r)` tiers | `a` tiers | `s` tiers |
|---|---:|---:|---:|---:|
| AgentProcessBench | 2,183 | 1,539 | 50 | 312 |
| HINTBench | 383 | 348 | 2 | 235 |
| TraceElephant | 66 | 24 | 2 | 37 |

The reviewer reconstructed every component, tuple, and ordinal. Larger `a`
always receives a higher ordinal regardless of the secondary key; identical
tuples share one ordinal; equal pairs remain tied for both AP and fixed-budget
Recall; source row order does not determine the primary result.

Rank construction is label-free, but candidate selection is not: `(a,s)` was
chosen after inspection of target-dependent Step 0036 results on these same
populations. This is adaptive development rather than untouched evaluation.

## AP, MAP, And Exact-Budget Recall

The following aggregate values reproduce independently and are numerically
admissible only with the adaptive-population scope stated above.

| Workload | Ranking | MAP | Expected Recall@20% |
|---|---|---:|---:|
| AgentProcessBench | local + semantic | 0.895972 | 0.661047 |
|  | local + raw action | 0.893071 | 0.660402 |
|  | atomic/local only | 0.863171 | 0.651185 |
|  | semantic only | 0.788919 | 0.562766 |
| HINTBench | local + semantic | 0.544906 | 0.628065 |
|  | local + raw action | 0.505961 | 0.615060 |
|  | atomic/local only | 0.410559 | 0.548394 |
|  | semantic only | 0.452373 | 0.574109 |
| TraceElephant | local + semantic | 0.321905 | 0.495422 |
|  | local + raw action | 0.249353 | 0.415774 |
|  | atomic/local only | 0.208713 | 0.332129 |
|  | semantic only | 0.230168 | 0.457529 |

### Primary MAP Comparisons

| Workload | Candidate minus | Effect | 95% nearest-rank interval | Seed |
|---|---|---:|---:|---:|
| AgentProcessBench | local + raw | +0.002900 | [-0.000497,+0.006852] | 20260717 |
|  | atomic | +0.032801 | [+0.024421,+0.042081] | 20260718 |
|  | semantic | +0.107052 | [+0.088462,+0.126437] | 20260719 |
| HINTBench | local + raw | +0.038945 | [+0.029118,+0.048908] | 20260817 |
|  | atomic | +0.134348 | [+0.121196,+0.147153] | 20260818 |
|  | semantic | +0.092534 | [+0.077050,+0.109587] | 20260819 |
| TraceElephant | local + raw | +0.072552 | [+0.049844,+0.097053] | 20260917 |
|  | atomic | +0.113192 | [+0.086972,+0.141692] | 20260918 |
|  | semantic | +0.091736 | [+0.058967,+0.126763] | 20260919 |

### Secondary Recall@20% Comparisons

| Workload | Candidate minus | Effect | 95% nearest-rank interval | Seed |
|---|---|---:|---:|---:|
| AgentProcessBench | local + raw | +0.000645 | [-0.004547,+0.006027] | 20260727 |
|  | atomic | +0.009862 | [+0.001341,+0.019216] | 20260728 |
|  | semantic | +0.098281 | [+0.075337,+0.122443] | 20260729 |
| HINTBench | local + raw | +0.013005 | [+0.001004,+0.025156] | 20260827 |
|  | atomic | +0.079671 | [+0.060041,+0.099787] | 20260828 |
|  | semantic | +0.053956 | [+0.037185,+0.071838] | 20260829 |
| TraceElephant | local + raw | +0.079648 | [+0.029337,+0.130447] | 20260927 |
|  | atomic | +0.163293 | [+0.114302,+0.212062] | 20260928 |
|  | semantic | +0.037892 | [+0.015912,+0.062292] | 20260929 |

Recall cannot promote the primary verdict. No Recall interval is wholly
negative, but the AgentProcessBench local-plus-raw interval also crosses zero.

Each query uses `K = ceil(0.2n)`. Independently reconstructed macro
worst/expected/best bounds are:

| Workload | Ranking | Worst | Expected | Best | Largest cutoff tier |
|---|---|---:|---:|---:|---:|
| AgentProcessBench | local + semantic | 0.657939 | 0.661047 | 0.666666 | 50 |
|  | local + raw | 0.656446 | 0.660402 | 0.665987 | 50 |
|  | atomic | 0.625937 | 0.651185 | 0.693617 | 69 |
|  | semantic | 0.541389 | 0.562766 | 0.600249 | 51 |
| HINTBench | local + semantic | 0.606667 | 0.628065 | 0.650208 | 9 |
|  | local + raw | 0.575208 | 0.615060 | 0.656667 | 9 |
|  | atomic | 0.446042 | 0.548394 | 0.954167 | 42 |
|  | semantic | 0.537292 | 0.574109 | 0.609375 | 9 |
| TraceElephant | local + semantic | 0.381818 | 0.495422 | 0.713636 | 77 |
|  | local + raw | 0.209091 | 0.415774 | 0.800000 | 93 |
|  | atomic | 0.159091 | 0.332129 | 1.000000 | 94 |
|  | semantic | 0.322727 | 0.457529 | 0.695455 | 78 |

## HINT Target Sensitivity

Treating the three absent official targets as unrecovered yields:

| Ranking | Sensitivity MAP | Sensitivity Recall@20% |
|---|---:|---:|
| local + semantic | 0.543919 | 0.626815 |
| local + raw | 0.504934 | 0.613775 |
| atomic | 0.409762 | 0.547397 |
| semantic | 0.451646 | 0.573067 |

The sensitivity does not change the workload classification.

## Support Identity

Candidate support equals atomic support operation-by-operation under the
registered local predicates:

| Workload | Supported clean trajectories | Supported clean operations |
|---|---:|---:|
| AgentProcessBench | 7 / 386 = 1.8135% | 8 / 2,459 = 0.3253% |
| HINTBench | 13 / 136 = 9.5588% | 25 / 3,368 = 0.7423% |
| TraceElephant | N/A | N/A |

This is a construction property, not empirical proof of improved specificity.
It is not a new performance metric or independent candidate win.

## Baseline Fairness And Mechanism Engagement

All comparisons are valid. Local-plus-raw receives the same operations, local
score, composition rule, and budget. Atomic is the strongest no-grouping
alternative. Semantic-only is the exact incumbent. All have complete finite
coverage and identical per-query K. Atomic and semantic reproduce Step 0036
with maximum absolute difference `0.0`.

| Workload | Semantic split tiers / affected ops / engaged queries | Raw split tiers / affected ops / engaged queries |
|---|---:|---:|
| AgentProcessBench | 1,462 / 6,641 / 802 | 1,465 / 6,648 / 802 |
| HINTBench | 714 / 12,634 / 535 | 696 / 12,597 / 533 |
| TraceElephant | 217 / 5,829 / 217 | 182 / 5,065 / 182 |

The AgentProcessBench null against local-plus-raw is genuine uncertainty, not
baseline non-engagement. The semantic secondary score aggregates the same
local signal over peers; it is not an independent diagnostic evidence source.

## Bootstrap Audit

All arrays use base seed `20260717` and the registered formula. Universes are:

- AgentProcessBench: four strata, 178 target-bearing task clusters;
- HINTBench: 44 strata, 400 trajectory clusters; and
- TraceElephant: five strata, 220 trajectory clusters.

Nearest-rank endpoints are draws 250 and 9,750 in one-based sorted order. Raw
arrays, medians, nonpositive counts, seeds, strata, clusters, and intervals all
reproduce.

## Negative Evidence And Omissions

Per-query loss/tie/win counts for candidate minus baseline are retained:

| Workload | Baseline | AP loss / tie / win | Recall loss / tie / win |
|---|---|---:|---:|
| AgentProcessBench | local + raw | 38 / 542 / 34 | 4 / 605 / 5 |
|  | atomic | 46 / 413 / 155 | 30 / 549 / 35 |
|  | semantic | 39 / 296 / 279 | 20 / 429 / 165 |
| HINTBench | local + raw | 71 / 199 / 130 | 34 / 317 / 49 |
|  | atomic | 19 / 79 / 302 | 150 / 94 / 156 |
|  | semantic | 23 / 221 / 156 | 14 / 318 / 68 |
| TraceElephant | local + raw | 34 / 106 / 80 | 61 / 86 / 73 |
|  | atomic | 0 / 120 / 100 | 95 / 37 / 88 |
|  | semantic | 10 / 182 / 28 | 8 / 198 / 14 |

Positive macro effects therefore do not mean every trajectory improved.
`report.md` omits secondary intervals, HINT sensitivity, support values,
engagement counts, per-query negative evidence, and the full adaptive boundary;
the raw files retain them, so the run remains valid, but WRITE must not rely on
that report alone.

## Execution History And Contamination Check

The first full invocation exited without result files and left only an empty
output directory. A `/tmp/rq2-local-first-debug` diagnostic subsequently
completed with ten bootstrap draws. It confirmed full-path execution only and
is not a result.

The six final files were created later in the declared full root and contain
18 arrays of 10,000 draws. They have different inodes from the diagnostic;
deterministic per-query and rank-key bytes agree as expected, whereas the
bootstrap-dependent files differ. The diagnostic's coarse `SUPPORTED` verdict
did not contaminate the final run and must never be cited. The final verdict is
`INCONCLUSIVE`.

## Authorized And Unauthorized Claims

The defensible conclusion is:

> On these previously observed complete populations, preserving local order
> and using semantic recurrence only for exact local-score ties clearly
> improves over atomic and incumbent semantic-only rankings, and beats matched
> raw-action tie refinement on HINTBench and TraceElephant; AgentProcessBench
> does not distinguish semantic from raw-action tie refinement.

The paper may not claim that the complete Step 0037 hypothesis is supported;
that the candidate beats local-plus-raw on AgentProcessBench or dominates all
baselines on all workloads; that it was selected without target feedback; that
the result is untouched or new-population generalization; that bootstrap
removes selection bias; that support identity proves specificity; that the
candidate reduces human work or improves interventions; that every trajectory
improves; that the workloads form iid samples; that TraceElephant is fully
reference-independent; that Step 0037 answers the whole RQ2 or challenges the
thesis; or that the candidate replaces the incumbent under the registered
decision rule.
