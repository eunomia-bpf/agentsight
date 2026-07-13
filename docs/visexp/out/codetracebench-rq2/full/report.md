# CodeTraceBench RQ2 Complete Experiment Report

**Status:** PASS

## Population And Execution

- Full manifest rows with terminal source status: 3316
- Source-valid full trajectories: 2717
- Explicit source exclusions: 599
- Source-valid failed verified targets: 405
- Target steps: 20866
- Source-valid outcome-bearing references: 2634
- Runtime: 3580.755 seconds

Coverage ledger: `docs/visexp/out/codetracebench-rq2/full/full-source-coverage.md`
Pre-label predictions: `docs/visexp/out/codetracebench-rq2/full/predictions-pre-label.md`
Pre-label partition selection: `docs/visexp/out/codetracebench-rq2/full/frequency-partitions-pre-label.md`
Frequency-partition metrics: `docs/visexp/out/codetracebench-rq2/full/frequency-partition-results.md`

## Primary Incorrect-Step Result

| Method | Pooled tie-aware AP | Recall @ 30% work | Work @ 50% recall | First-positive work | Steps | Incorrect steps | Zero-positive targets |
|---|---:|---:|---:|---:|---:|---:|---:|
| semantic | 0.052290 | 0.307323 | 0.434343 | 0.000863 | 20866 | 833 | 206 |
| raw-action | 0.042936 | 0.310924 | 0.500144 | 0.000240 | 20866 | 833 | 206 |
| phase | 0.048382 | 0.310924 | 0.517588 | 0.001677 | 20866 | 833 | 206 |

## CodeTracer-Compatible Per-Trajectory Metrics

Only trajectories with at least one incorrect step enter macro P/R/F1. Zero-positive burden is reported separately.

| Method | Eligible | Macro P | Macro R | Macro F1 | Zero-positive targets | Pooled zero-positive burden | Macro zero-positive burden | Unique groups |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| semantic | 199 | 0.111408 | 0.214760 | 0.123887 | 206 | 0.144058 | 0.159913 | 17 |
| raw-action | 199 | 0.137331 | 0.241040 | 0.149540 | 206 | 0.151049 | 0.139679 | 400 |
| phase | 199 | 0.065952 | 0.099133 | 0.069887 | 206 | 0.030701 | 0.029122 | 2 |

## Secondary Label Families

These use the frozen pre-label scores and cannot select the primary method.

| Label family | Method | AP | Recall @ 30% | Work @ 50% | Positive steps |
|---|---|---:|---:|---:|---:|
| unuseful | semantic | 0.005726 | 0.234848 | 0.522525 | 132 |
| unuseful | raw-action | 0.005466 | 0.174242 | 0.500144 | 132 |
| unuseful | phase | 0.005759 | 0.181818 | 0.490798 | 132 |
| union | semantic | 0.056492 | 0.297409 | 0.466117 | 965 |
| union | raw-action | 0.047659 | 0.292228 | 0.500144 | 965 |
| union | phase | 0.052479 | 0.293264 | 0.510927 | 965 |

## Framework Breakdown

| Framework | Method | Targets | AP | Recall @ 30% | Work @ 50% |
|---|---|---:|---:|---:|---:|
| OpenHands | semantic | 213 | 0.043697 | 0.375740 | 0.379362 |
| OpenHands | raw-action | 213 | 0.052215 | 0.414201 | 0.379860 |
| OpenHands | phase | 213 | 0.031938 | 0.295858 | 0.521735 |
| SWE-agent | semantic | 28 | 0.023227 | 0.018519 | 0.883562 |
| SWE-agent | raw-action | 28 | 0.023597 | 0.000000 | 0.818493 |
| SWE-agent | phase | 28 | 0.062766 | 0.518519 | 0.279452 |
| Terminus2 | semantic | 93 | 0.075917 | 0.493562 | 0.321622 |
| Terminus2 | raw-action | 93 | 0.029395 | 0.240343 | 0.533398 |
| Terminus2 | phase | 93 | 0.060169 | 0.373391 | 0.546868 |
| mini-SWE-agent | semantic | 71 | 0.101729 | 0.264423 | 0.466207 |
| mini-SWE-agent | raw-action | 71 | 0.086119 | 0.216346 | 0.567356 |
| mini-SWE-agent | phase | 71 | 0.097428 | 0.278846 | 0.502069 |

## Controls

| Control | AP | Recall @ 30% | Work @ 50% |
|---|---:|---:|---:|
| flat/session-one-block | 0.039921 | 0.000000 | 1.000000 |
| absolute-semantic | 0.031853 | 0.159664 | 0.674063 |
| absolute-raw-action | 0.034041 | 0.186074 | 0.563884 |
| absolute-phase | 0.034064 | 0.228091 | 0.780744 |

Flat and per-session one-block controls are merged because neither defines an outcome-informed recurrent ordering. Framework-native operation identity is the public step unit already consumed by the raw-action baseline. The official CodeTracer tree remains a navigation reference, while its target-blind phase classifier is the matched scored baseline above.

### Frequency-Matched Non-Semantic Partitions

Evaluated partitions: 200. AP median 0.042294, 2.5--97.5% range [0.036177, 0.048459]. Semantic-minus-best-partition AP: 0.001309; semantic-minus-median AP: 0.009996.

## Outcome Null

| Method | Trials | Null mean AP | Null 2.5% | Null 97.5% | One-sided empirical p (null AP >= observed) |
|---|---:|---:|---:|---:|---:|
| semantic | 2000 | 0.052879 | 0.046228 | 0.061516 | 0.531234 |
| raw-action | 2000 | 0.042962 | 0.035635 | 0.052205 | 0.474763 |
| phase | 2000 | 0.047809 | 0.038868 | 0.061968 | 0.402799 |

## Task-Clustered Bootstrap

Valid replicates: 10000; sampling attempts: 10007.

| Method | Metric | Bootstrap mean | 95% percentile interval |
|---|---|---:|---:|
| semantic | average_precision | 0.051878 | [0.035123, 0.080336] |
| semantic | recall_at_30_work | 0.308542 | [0.197903, 0.422223] |
| semantic | work_at_50_recall | 0.464596 | [0.367957, 0.567259] |
| raw-action | average_precision | 0.042435 | [0.032214, 0.058362] |
| raw-action | recall_at_30_work | 0.285416 | [0.184331, 0.393034] |
| raw-action | work_at_50_recall | 0.508223 | [0.403857, 0.604721] |
| phase | average_precision | 0.053426 | [0.032816, 0.089904] |
| phase | recall_at_30_work | 0.322645 | [0.193798, 0.455777] |
| phase | work_at_50_recall | 0.507264 | [0.343645, 0.662091] |

| Paired AP difference | Mean | 95% percentile interval |
|---|---:|---:|
| semantic - raw-action | 0.009443 | [-0.008322, 0.036855] |
| semantic - phase | -0.001548 | [-0.031736, 0.021013] |

## Completion Audit

- Frequency candidates/retained: 10000/200 (required 10,000/200).
- Outcome-null trials: 2000 (required 2,000).
- Task-bootstrap replicates: 10000 (required 10,000).
- Source coverage: 3316/3316 terminal rows.

The report is PASS only when the approved full counts and every component above complete. Git state does not affect this status.

## Result-Review Handoff

This report records the completed tested-hypothesis result. It does not answer the entire RQ, rewrite the hypothesis, or authorize a paper-story change. The next node is independent scientific result review.
