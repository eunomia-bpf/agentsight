# R302 Label-Hidden Analyst Ranking

Query-aware ranking changes the analysis tradeoff without reading oracle labels. On operation stacks, top-10 query-aware groups inspect 11.6% of operations with lift 1.587, compared with 67.1% and lift 1.079 for width ranking. At a 30% operation budget, query-aware ranking raises median recall from 34.0% to 39.0%, but it inspects 39.5 groups instead of 4.5, so the result supports configurable analysis policies rather than automatic detection.

## Median Scores

| View | Ranker | Budget | Median recall | Median lift | Work fraction | Groups |
|---|---|---|---:|---:|---:|---:|
| fixed_session | oracle_upper_bound | budget_10pct_operations | 0.2222 | 2.2241 | 0.0999 | 47.0 |
| fixed_session | oracle_upper_bound | budget_20pct_operations | 0.4592 | 2.3011 | 0.1997 | 79.5 |
| fixed_session | oracle_upper_bound | budget_30pct_operations | 0.6092 | 2.0314 | 0.2998 | 99.0 |
| fixed_session | oracle_upper_bound | top_10_groups | 0.1722 | 2.9083 | 0.0286 | 10.0 |
| fixed_session | query_aware | budget_10pct_operations | 0.1319 | 1.3194 | 0.0998 | 44.0 |
| fixed_session | query_aware | budget_20pct_operations | 0.2442 | 1.2214 | 0.1999 | 65.5 |
| fixed_session | query_aware | budget_30pct_operations | 0.3566 | 1.1908 | 0.2999 | 88.0 |
| fixed_session | query_aware | top_10_groups | 0.0645 | 1.6348 | 0.0226 | 10.0 |
| fixed_session | visible_risk | budget_10pct_operations | 0.1178 | 1.1868 | 0.0998 | 17.0 |
| fixed_session | visible_risk | budget_20pct_operations | 0.2168 | 1.0879 | 0.1998 | 27.0 |
| fixed_session | visible_risk | budget_30pct_operations | 0.3274 | 1.0914 | 0.2999 | 38.5 |
| fixed_session | visible_risk | top_10_groups | 0.0244 | 1.404 | 0.0445 | 10.0 |
| fixed_session | width | budget_10pct_operations | 0.0912 | 0.9131 | 0.0999 | 9.0 |
| fixed_session | width | budget_20pct_operations | 0.1879 | 0.9395 | 0.2 | 17.0 |
| fixed_session | width | budget_30pct_operations | 0.281 | 0.9369 | 0.2999 | 25.5 |
| fixed_session | width | top_10_groups | 0.1957 | 0.9068 | 0.2124 | 10.0 |
| operation_stack | oracle_upper_bound | budget_10pct_operations | 0.2584 | 2.5855 | 0.0999 | 18.5 |
| operation_stack | oracle_upper_bound | budget_20pct_operations | 0.4127 | 2.0694 | 0.2 | 33.0 |
| operation_stack | oracle_upper_bound | budget_30pct_operations | 0.564 | 1.8804 | 0.2999 | 36.5 |
| operation_stack | oracle_upper_bound | top_10_groups | 0.4287 | 5.1827 | 0.074 | 10.0 |
| operation_stack | query_aware | budget_10pct_operations | 0.1315 | 1.3239 | 0.0999 | 18.0 |
| operation_stack | query_aware | budget_20pct_operations | 0.277 | 1.3853 | 0.2 | 25.5 |
| operation_stack | query_aware | budget_30pct_operations | 0.39 | 1.3042 | 0.2999 | 39.5 |
| operation_stack | query_aware | top_10_groups | 0.2474 | 1.5867 | 0.1163 | 10.0 |
| operation_stack | visible_risk | budget_10pct_operations | 0.1056 | 1.0687 | 0.0999 | 26.0 |
| operation_stack | visible_risk | budget_20pct_operations | 0.2522 | 1.2681 | 0.2 | 35.0 |
| operation_stack | visible_risk | budget_30pct_operations | 0.312 | 1.0415 | 0.2999 | 35.5 |
| operation_stack | visible_risk | top_10_groups | 0.1228 | 1.1406 | 0.1462 | 10.0 |
| operation_stack | width | budget_10pct_operations | 0.1224 | 1.231 | 0.0999 | 3.0 |
| operation_stack | width | budget_20pct_operations | 0.2414 | 1.2073 | 0.2 | 4.0 |
| operation_stack | width | budget_30pct_operations | 0.3401 | 1.1337 | 0.2999 | 4.5 |
| operation_stack | width | top_10_groups | 0.648 | 1.0795 | 0.6713 | 10.0 |

## Claim Scope

- Supports: operation stacks can be paired with label-hidden ranking policies to trade recall, precision, and inspection work without adding a new profiler abstraction.
- Narrows: query-aware ranking is a heuristic over visible operation fields, not a detector or human-study result.
- Upper bound: `oracle_upper_bound` is included only to show remaining headroom and never appears as a visible policy.
