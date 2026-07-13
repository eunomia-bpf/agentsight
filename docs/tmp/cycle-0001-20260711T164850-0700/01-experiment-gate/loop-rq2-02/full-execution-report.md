# Full Execution Report: RQ2 Hodoscope Representation Choice

**Timestamp:** 2026-07-12  
**Approved plan:** `experiment-plan.md`  
**Plan review:** three serial rounds, final PASS  
**Independent result review:** valid run; expected answer contradicted

## Completed Matrix

Every planned workload reached terminal status:

| Run group | Completed work | Cells | Status |
|---|---|---:|---|
| Preflight | One real paired seed, all four views | 4 | PASS |
| A1 | Official Hodoscope Table 2, all three testbeds, ten seeds | official full script | COMPLETE |
| A2--A4 | iQuest 50%-per-cohort paired protocol, four views, ten seeds | 40 | COMPLETE |
| B1 | All 11,855 actions, four views, ten full-corpus seeds | 40 | COMPLETE |

There were no missing seeds, no no-hit rows, no excluded metrics, and no early
stop. The complete A/B comparison command exited 0 after 31:06.28 wall-clock,
using 37,922.76 user CPU seconds and 1,515,200KiB maximum RSS. The CPU figure
comes from the launch transcript rather than a preserved raw `/usr/bin/time`
log; the RSS is present in saved metrics and the wall time agrees with artifact
timestamps. The unmodified
official Table 2 command exited 0 after 26:27.46, using 20,850.93 user CPU
seconds and 4,753,704KiB maximum RSS. The official data occupy about 6.9GB and
the comparative raw outputs about 193MB. No model API call or monetary API cost
was used.

## Commands

Matched comparison:

```bash
<venv>/python script/hodoscope_representation_eval.py \
  --mode all \
  --paper-root <official-paper-root> \
  --data-root <official-data-root> \
  --out-dir <loop>/raw \
  --seeds 10 \
  --bootstrap-seed 20260712
```

Official reproduction:

```bash
<venv>/python experiments/run_table2.py --seeds 10
```

The complete official stdout/stderr and `/usr/bin/time -v` report are preserved
at `raw/official-table2.log`.

## Official Reproduction

The author script reproduced the expected scale and relative ordering:

| Testbed | Density-contrast rank | Target fraction | Characters fraction |
|---|---:|---:|---:|
| Commit0 | 1.0 ± 0.0 | 0.11% | 0.151% |
| ImpossibleBench | 3.3 ± 1.3 | 0.01% | 0.006% |
| iQuest/SWE-bench | 2.9 ± 0.3 | 0.07% | 0.059% |

For iQuest the official run used 4,006 target actions and 132 published oracle
positives. The paired comparison's Hodoscope row independently produced the
same 2.9 ± 0.3 first-hit rank in Phase A.

The official percentages use the complete 4,006-action iQuest target corpus as
their denominator even though one seed samples 2,003 target actions. The
matched Phase A fractions use 2,003. They are not interchangeable percentages.

The official script emitted HDBSCAN warnings for swept cluster sizes that
produce no clusters. They were retained in the raw log and handled by the
author's existing code. They do not alter the density-contrast Hodoscope row.

## Phase A: Published 50% Paired Protocol

Each seed used the same official 50%-per-cohort subsample and t-SNE seed for all
four views. Means and population standard deviations over ten seeds:

| View | First-hit rank | Characters inspected | Hits@20 | Method runtime after shared t-SNE |
|---|---:|---:|---:|---:|
| Hodoscope | 2.9 ± 0.3 | 6,403 ± 3,857 | 1.2 ± 0.4 | 1.003 ± 0.153s |
| Flat semantic | 55.4 ± 95.7 | 205,747 ± 336,667 | 0.6 ± 0.66 | 27.046 ± 2.346s |
| Native turn | 36.8 ± 31.8 | 88,563 ± 75,584 | 0.5 ± 0.67 | 0.290 ± 0.038s |
| Recursive semantic | 24.9 ± 15.8 | 61,672 ± 45,158 | 0.5 ± 0.67 | 25.971 ± 3.359s |

Prespecified paired recursive deltas (`recursive rank - baseline rank`):

| Baseline | Mean delta | 95% paired-bootstrap interval | Recursive win rate | Positive rule |
|---|---:|---:|---:|---|
| Hodoscope | +22.0 | [12.3, 31.8] | 0.0 | FAIL |
| Flat semantic | -30.5 | [-97.3, 13.3] | 0.5 | FAIL |
| Native turn | -11.9 | [-36.5, 9.0] | 0.5 | FAIL |

The recursive-positive rule failed against every required baseline. Hodoscope
found an oracle-positive action earlier on all ten paired seeds.

## Phase B: Complete 250-Trajectory Corpus

Every seed used all 7,849 reference and 4,006 target actions; only clustering,
t-SNE, and FPS seed varied. The runner used seeds 1 through 10 rather than the
plan's literal 0 through 9; this predetermined range is disclosed below.

| View | First-hit rank | Characters inspected | Hits@20 | Method runtime after shared t-SNE |
|---|---:|---:|---:|---:|
| Hodoscope | 3.0 ± 0.0 | 5,313 ± 136 | 1.0 ± 0.0 | 3.058 ± 0.037s |
| Flat semantic | 94.5 ± 65.2 | 322,555 ± 225,430 | 0.1 ± 0.3 | 32.910 ± 1.731s |
| Native turn | 71.3 ± 14.3 | 144,819 ± 31,432 | 0.0 ± 0.0 | 0.981 ± 0.040s |
| Recursive semantic | 76.3 ± 58.4 | 203,676 ± 159,633 | 0.2 ± 0.4 | 33.413 ± 1.797s |

Prespecified paired recursive deltas:

| Baseline | Mean delta | 95% paired-bootstrap interval | Recursive win rate | Positive rule |
|---|---:|---:|---:|---|
| Hodoscope | +73.3 | [40.5, 112.0] | 0.0 | FAIL |
| Flat semantic | -18.2 | [-83.1, 44.3] | 0.7 | FAIL |
| Native turn | +5.0 | [-26.3, 39.7] | 0.5 | FAIL |

The all-data extension reinforces the Phase A result against Hodoscope and
does not establish a stable recursive advantage over flat or native views.

## Mechanical Validation

An independent local recomputation before result review established:

- 10 Phase A and 10 Phase B seed directories;
- 40 terminal method rows per phase;
- 2,003 unique target action keys per Phase A permutation and 4,006 per Phase B
  permutation;
- identical target action sets across all four methods in each paired seed;
- no oracle field in any unscored ranking;
- scored copies written only after full unscored permutations;
- every first-hit rank recomputed exactly from the saved permutation and oracle;
- flat and recursive views use identical terminal fine-cluster assignments in
  every seed;
- no no-hit or missing result;
- Hodoscope first hits remain in its unchanged official top-500 prefix.

## Deviations And Failures

One preflight installation defect was repaired and rerun: PyPI Hodoscope 0.2.4
incorrectly resolves an optional PaCMAP dependency to a Python-incompatible
llvmlite. The exact pinned Hodoscope source was used with only dependencies
exercised by t-SNE/Table 2. This did not change data, oracle, projection,
Hodoscope scoring, or any comparison rule.

One full-run seed-range deviation occurred: the plan names Phase B seeds 0--9,
whereas the runner's mechanically predetermined range was 1--10. No seed was
selected after inspecting its result. This does not change run validity, but a
claim of literal 0--9 execution would require replacing seed 10 with seed 0.
The observed negative/mixed rows were not repaired, excluded, or used to retune
the hierarchy.

The saved Hodoscope ranking rows contain `contrast: 0.0` because the official
API returned ranks without exporting its normalized per-action density-gap
score and the adapter encoded the absent score as zero. The zero is not an
observed contrast and is not used for ordering or scoring. The runner now emits
`null` for future Hodoscope rows. Existing ranks and metrics require no rerun.

## Raw Paths

- Inventory: `raw/inventory.json`.
- Phase A rankings and metrics: `raw/phase-a/seed-*/` and
  `raw/phase-a/paired-summary.json`.
- Phase B rankings and metrics: `raw/phase-b/seed-*/` and
  `raw/phase-b/paired-summary.json`.
- Aggregated metric rows: `raw/metrics.jsonl`.
- Official reproduction log: `raw/official-table2.log`.
- Runner: `script/hodoscope_representation_eval.py`.

## Reviewed Interpretation

The independent result review finds the run valid and the expected answer
contradicted. Official Hodoscope's complete density-gap/FPS bundle is decisively
earlier, while the recursive stack does not show a stable paired improvement
over its matched flat terminal partition or the native turn-position grouping.

This does not authorize narrowing RQ2 or the paper's large representation-choice
question. It establishes that adding the tested 8/32/128 recursive parents does
not provide stable value in this condition. Because Hodoscope also changes its
continuous KDE scoring and normalization, this run does not establish that
flatness or continuous geometry caused its advantage. The native comparator is
exact released `turn_id`/turn-position grouping across trajectories, not every
possible source-native execution tree. Per-method runtime covers construction
and ranking after shared t-SNE, not full end-to-end cost.
