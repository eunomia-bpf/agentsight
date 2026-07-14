# Independent Result Review: RQ3 Inducer Depth

## Verdict

- **Run status: VALID**
- **Registered outcome: CONTRADICTED**
- **Paper role: supporting, post-hoc mechanism/workload-boundary evidence**
- **Paper impact: local implementation/mechanism boundary; not headline,
  decisive, or a thesis challenge**

The reviewer saw the plan/full-run report's prior `VALID / CONTRADICTED`
self-verdict and treated it as non-authoritative.

## Independent Recalculation

Coverage is complete:

- 574 session rows: 287 per method
- 3,978 operations and 3,691 adjacent pairs per method
- 3,978 mass per method
- 3,691 pair-prediction rows
- 1,755 true boundaries and 1,936 true non-boundaries

| Method | TP | FP | FN | TN | Predicted boundaries | Boundary F1 | Predicted groups | B-cubed F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Depth 255 | 804 | 848 | 951 | 1,088 | 1,652 | 0.4719694746 | 1,939 | 0.6720062682 |
| Depth 4 | 645 | 649 | 1,110 | 1,287 | 1,294 | 0.4230895376 | 1,581 | 0.6164791921 |

Raw-pair reconstruction also reproduced:

- depth-255 boundary precision/recall: `0.4866828087 / 0.4581196581`;
- depth-four boundary precision/recall: `0.4984544049 / 0.3675213675`;
- depth-255 B-cubed precision/recall: `0.6065755280 / 0.7532596935`;
- depth-four B-cubed precision/recall: `0.4993621573 / 0.8053637867`; and
- 2,042 reconstructed oracle groups.

Exact candidate deltas:

- versus depth four: **+0.0488799371 boundary F1** and **+0.0555270762
  B-cubed F1**;
- versus always boundary: **-0.1725402573 boundary F1** and **-0.0063990474
  B-cubed F1**;
- versus action change: **-0.0051106905 boundary F1** and **+0.0128318058
  B-cubed F1**; and
- versus phase change: **+0.1382819082 boundary F1** and **+0.0065448848
  B-cubed F1**.

All summary confusion-matrix F1 values and all summary B-cubed F1 values
exactly satisfy their defining formulas.

Mechanism counts also reproduce:

- depth 255: 1,652 splits, maximum observed leaf depth 26, 1,939
  `no_material_split` leaves, and zero depth-cap stops;
- depth four: 1,294 splits, 488 `max_depth` leaves, 1,093
  `no_material_split` leaves, and 106 cap-hit sessions;
- paths changed in 60 sessions, all within those 106 cap-hit sessions; the
  other 46 were unchanged; and
- four sessions had no split under either method.

## Validity Audit

The depth-four rows match the Step 0017 candidate rows on all 287 sessions,
with zero missing, extra, or mismatching rows across sequence, operations,
pairs, policy, splits, maximum leaf depth, selected fields, stop reasons, paths,
stack weights, and mass.

The script supports the intended comparison:

- both methods must resolve to the same binary path;
- depth-limit mode hard-requires depths 255 and four;
- method policy, reconstruction, mass, decision consumption, and reported depth
  are checked identically;
- `human_group` and registered leakage fields are removed before profiler
  invocation;
- selected evidence fields are separately rejected if classified as oracle
  fields; and
- scoring labels are consulted only after profiler execution.

Thus the sole admitted configuration variable is maximum depth. The differing
selected-field aggregates arise from deeper accepted splits, not different
input configurations.

## Interpretation

The registered result is **CONTRADICTED**, not mixed: depth 255 improves both
metrics over depth four but clears neither metric's strongest simple control,
exactly satisfying the predeclared contradicted branch.

The largest admissible positive conclusion is:

> On the complete, post-hoc OSWorld-Human population, removing the arbitrary
> depth-four cap materially improves the otherwise identical built-in inducer
> and allows intrinsic stopping at depths up to 26; the cap was genuinely
> harmful, but its removal is insufficient to close the accuracy gap to simple
> segmentation controls.

Prohibited overclaims:

- do not label the registered hypothesis supported or mixed;
- do not claim the cap was the sufficient explanation for under-segmentation;
- do not claim broad RQ3 tag accuracy, independent confirmation, or thesis
  validation;
- do not claim superiority to simple controls or the supervised comparator;
- do not generalize this post-hoc same-population result to other workloads;
  and
- do not authorize another OSWorld-Human depth, penalty, threshold, or
  score-term search.

## WRITE Disposition

**WRITE: admit only as a bounded supporting/post-hoc negative diagnostic.**
Record the valid `CONTRADICTED` outcome and the exact same-algorithm
improvements. Cap-free induction may be described as the better current
implementation, but it cannot be promoted to the paper's validated automatic
method or broader RQ3 evidence.

**One next action:** route this bounded result to WRITE, with no further
OSWorld-Human tuning.
