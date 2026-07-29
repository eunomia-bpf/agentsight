## 1. Run status: valid

All matched populations and registered analyses recompute correctly. The ordinal-118 normalization is documented, deterministic, oracle-blind, and does not change any of its 47 expanded semantic paths.

## 2. Tested hypothesis: inconclusive

Both hierarchy-minus-flat point estimates are positive, but both paired task-cluster 95% intervals cross zero.

## 3. Recomputed key numbers

| Metric | Hierarchy | Flat | Point Δ | Bootstrap mean Δ | 95% CI |
|---|---:|---:|---:|---:|---:|
| B³ F1 | 0.763539 | 0.753791 | +0.009747 | +0.009689 | [-0.003361, +0.023660] |
| Boundary F1 | 0.479952 | 0.468154 | +0.011798 | +0.011676 | [-0.007351, +0.031698] |

Additional checks:

- B³ hierarchy P/R: 0.793409 / 0.735836; flat: 0.698188 / 0.819017.
- Boundary hierarchy P/R: 0.389147 / 0.626032; flat: 0.431509 / 0.511600.
- Positive bootstrap fractions: 92.26% B³; 88.38% boundary.
- Population: 405 trajectories, 20,866 operations, 20,461 pairs, 2,948 stages, 251 task clusters.
- Hierarchy and flat operation/pair keys and oracle fields match exactly.

Ordinal 118 changed from five sparse marks to three by deleting starts 20 and 45. All expanded paths and the path-change vector remain identical. A naïve, invalid interpretation treating those redundant marks as new occurrence IDs would add two groups and two false-positive boundaries, slightly changing flat B³ F1 to 0.753946 and boundary F1 to 0.467986; importantly, the corresponding intervals still cross zero. Under the approved complete-path contract, those marks are not semantic transitions.

## 4. Blocking issue

None. The requested `bootstrap-*-f1.json` filenames are absent, but the registered 10,000 draws exist as `score/bootstrap-hierarchy-minus-flat-{bcubed,boundary}.jsonl` and reproduce exactly.

## 5. Paper-safe interpretation

On all 405 CodeTraceBench trajectories, variable-depth hierarchy produced small positive point estimates over the matched same-model flat partition, but neither registered improvement is statistically resolved. Therefore:

> Positive point estimates, but statistically inconclusive on both registered metrics.

Do not claim that variable depth explains the adopted result. This experiment evaluates leaf partitions and exact boundaries only—not nested-topology quality, semantic-name accuracy, cross-run identity, user utility, or generalization beyond CodeTraceBench.