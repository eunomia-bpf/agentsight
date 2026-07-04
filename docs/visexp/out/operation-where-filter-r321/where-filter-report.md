# R321 Operation Predicate Reproducibility

Status: `pass`.

R321 verifies that `--where`/`where_rules` acts as a query predicate over
operations after mapping/tagging and before recursive stack folding.

| Probe | Predicate | Expected samples | Folded samples | Unique stacks |
|---|---:|---:|---:|---:|
| looping_dynamic_task | `task_family=where_probe_loop` | 729 | 729 | 40 |
| looping_dynamic_task_without_success | `task_family=where_probe_loop && status!=success` | 714 | 714 | 37 |
| safety_dynamic_task | `task_family=where_probe_safety` | 4285 | 4285 | 89 |

Interpretation: profile specs now carry the full operation-stack query:
operation source, field mappings, query predicate, stack projection, and output.
This makes the implementation closer to the paper's model where views are
query evaluations over operations, not fixed prompt/session trees.
