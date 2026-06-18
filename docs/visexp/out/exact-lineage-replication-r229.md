# R229 Exact Lineage Replication

Last updated: 2026-06-18
Stage at update: execute/analyze
Source/command: `python3 docs/visexp/r229_exact_lineage_replication.py --out docs/visexp/out`
Completeness: ok

R229 reruns the R114 record/export/lineage oracle over a controlled
multi-workspace suite. It checks whether prompt/tool/process/effect
lineage remains clean across repo read, edit/test, shell fix, JSON write,
and typo-edit workloads while wrapper negative controls run concurrently.

Raw SQLite DBs, exported snapshots, and per-event lineage CSVs stay in
the local work dir and are not committed.

## Aggregate

- Tasks: 5 ({'lineage_precision_ok': 5})
- Workspaces: {'repo': 1, 'python_bug': 1, 'shell_fix': 1, 'json_write': 1, 'typo_repo': 1}
- Categories: {'repo-read': 1, 'edit-test': 2, 'write': 1, 'edit': 1}
- Record status: {'ok': 5}; target status: {'completed': 5}; lineage status: {'precision_ok': 5}
- Effects: joined=394 / 1080 = 36.481%
- Scope accounting: in_scope=394, out_of_scope=380
- Scoped oracle: true_positives=394, false_positives=0, false_negatives=0
- Precision/recall: precision=100.0%, recall=100.0%
- Negative controls: tasks_observed=5/5, observed=306, joined=0
- Broad smoke status: {'lineage_smoke_failed': 5}
- Join methods: {'none': 686, 'pid_family_time_window': 394}

The raw join rate is intentionally lower than scoped precision: wrapper,
out-of-scope, and negative-control effects should remain orphan instead of
being attributed to the target agent task. R229 therefore passes the scoped
precision/negative-control oracle even though the broad lineage smoke treats
those intentional orphans as failures.

## Per Task

| Task | Cat | Workspace | Target | Lineage | Effects | Joined | In scope | Out scope | Neg observed | Neg joined | Answer |
|------|-----|-----------|--------|---------|--------:|-------:|---------:|----------:|-------------:|-----------:|--------|
| `r229-repo-r191-read` | repo-read | repo | completed | precision_ok | 422 | 72 | 72 | 48 | 302 | 0 | r191_status=ok |
| `r229-python-fix` | edit-test | python_bug | completed | precision_ok | 182 | 86 | 86 | 95 | 1 | 0 | tests=passed |
| `r229-shell-fix` | edit-test | shell_fix | completed | precision_ok | 190 | 92 | 92 | 97 | 1 | 0 | check=passed |
| `r229-json-write` | write | json_write | completed | precision_ok | 146 | 72 | 72 | 73 | 1 | 0 | result_json=created |
| `r229-typo-edit` | edit | typo_repo | completed | precision_ok | 140 | 72 | 72 | 67 | 1 | 0 | typo_fixed=yes |

## Claim Boundary

R229 strengthens C4/RQ3 for the fixed command-mode scope by replicating the R114 exact-lineage oracle across multiple controlled workspaces and workload categories with zero negative-control joins. It does not prove full-history exact lineage, arbitrary prompt compliance, cross-repository generality, C5 developer utility, or C6 tag adequacy.
