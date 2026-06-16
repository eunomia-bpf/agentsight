# R205 Long-Tail Compaction Metrics

Status: `compaction_metrics_ready_no_quality_claims`

## Scope

- Reads generated R189/R190/R196/R201/R202/R203 artifacts only.
- Does not read or mutate raw Codex/Claude traces.
- Does not update the canonical tag map.
- Quantifies display compaction mechanics, not semantic adequacy or developer utility.

## Input Consistency

| check | value |
|---|---:|
| R189 rows | 1811 |
| R196 rows | 1811 |
| R189 duplicate keys | 0 |
| R196 rows missing from R189 | 0 |
| canonical mismatch rows | 0 |
| auto-canonicalize rows | 231 |
| auto-canonicalize rows from R189 merge | 231 |
| consistency passed | True |

## Overall Compaction

| metric | value |
|---|---:|
| raw unique tags | 1546 |
| canonical unique tags | 1364 |
| canonical unique reduction | 182 |
| canonical unique reduction pct | 11.772 |
| raw top-20 support coverage pct | 93.683 |
| canonical top-20 support coverage pct | 95.186 |
| top-20 coverage gain pct points | 1.503 |
| long-tail support pct | 1.746 |
| review-required support pct | 1.926 |

## Per-Dimension Metrics

| dimension | raw tags | canonical tags | top-20 raw pct | top-20 canonical pct | review support pct |
|---|---:|---:|---:|---:|---:|
| llm | 1423 | 1254 | 94.546 | 95.337 | 1.376 |
| prompt | 328 | 279 | 90.387 | 92.66 | 3.258 |
| session | 60 | 49 | 99.458 | 99.708 | 0.938 |

## Regeneration And Review Gates

- R202 attempted rows: `41`.
- Grammar-valid regenerated candidates: `41` / `41`.
- Changed valid candidates: `32`.
- R203 promotion packet rows: `41`.
- R203 final promotion labels: `0`.
- R203 paired label coverage pct: `0.0`.
- R190 overmerge rate pct: `n/a`.
- R190 undermerge rate pct: `n/a`.
- R201 baseline review-required support pct: `1.926`.
- R201 minimum head stability pct: `65.217`.

## Claim Boundary

R205 supports only the existence of a measurable semantic compaction mechanism over existing artifacts. It does not prove that canonical tags are semantically correct, that regenerated tags should be promoted, or that developers answer forensic questions faster or more accurately. Those claims still require the existing R124/R190/R203 human-label gates and the R142/R151 developer-task gates.
