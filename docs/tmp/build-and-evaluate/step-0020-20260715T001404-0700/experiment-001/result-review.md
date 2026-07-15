# Independent Result Review — Recurrence-Based Operation-Stack Induction

**Verdict:** **PASS**
**Run status:** valid
**Tested hypothesis:** supported
**Research value:** supporting post-hoc mechanism-development evidence
**Paper impact:** mechanism/workload boundary, not fresh RQ3 confirmation

## Independence

The fresh reviewer was told the expected result, then independently rebuilt the
complete population, folds, action-transition statistics, candidate decisions,
partitions, baselines, metrics, profiler invariants, and registered verdict
from the original source and raw outputs. It did not edit files, port Rust, or
rely on the generated summary as authority.

## Exact Recomputed Results

| Method | Boundary F1 | B-cubed F1 |
|---|---:|---:|
| Current cap-free information gain | 0.4719694746110948 | 0.6720062682173661 |
| Always boundary | 0.6445097319133308 | 0.6784053156146130 |
| Recurrence candidate | **0.6799224054316197** | **0.7861695437481895** |
| Supervised OOF comparator | 0.7387678235135863 | 0.8160191831297375 |

The candidate confusion matrix is TP=1,402, FP=967, FN=353, and TN=969,
giving precision 0.5918 and recall 0.7989. Independent B-cubed recomputation
gave precision approximately 0.855871535450824, recall approximately
0.726965621631135, and F1 approximately 0.786169543748189; its negligible
difference from the recorded value is only floating-point summation order.

The independently recomputed improvements are:

- versus current information gain: +0.207952930820525 boundary F1 and
  +0.114163275530823 B-cubed F1;
- versus strongest simple control: +0.035412673518289 boundary F1 and
  +0.107764228133576 B-cubed F1.

These satisfy both registered success conditions, so `SUPPORTED` is correct.

## Validity Checks

The reviewer confirmed exact coverage of 287 sessions, 3,978 operations, 3,691
pairs, and 2,042 human groups. The five held-out folds cover 45/55/60/62/65
sessions and 476/582/1,270/572/791 pairs. Training and held-out session sets are
disjoint and every pair receives one prediction.

Starting from original action sequences, the reviewer reproduced every NPMI,
two-means center, cutoff, all 95 unseen-transition decisions, all pair
predictions, 2,656 predicted groups, and 44 motif identities. It also proved
exact alignment of all Step 0018 pairs, current-source labels, depth-255 session
paths, and pair/path boundary decisions.

Candidate induction uses only visible `action`. No `human_group`, group,
learned, oracle, target-derived, or other scorer field survives in candidate
operations. A source `target` metadata field remains because it is neither read
by induction nor present in the profile stack; the reviewer confirmed it does
not constitute target leakage.

Real `agentpprof 0.2.37` processed all 3,978 samples, produced 44 stacks, wrote
no stderr, and conserved exact total weight 3,978.

## Required Interpretation Boundary

This result supports a minimal Rust port and Python-versus-Rust equivalence
check. It establishes that cross-session label-free-at-prediction transition
association is the better development candidate on this already observed
OSWorld-Human population. Because these labels influenced failure diagnosis
and candidate selection, the result is not new RQ3 confirmation. It does not
validate literal motif names, phase/action semantic identity, cross-family
generalization, or the whole RQ3 hypothesis. Any new paper-level RQ3 evidence
requires independent confirmation data.
