# R191 Target Network Lineage

Last updated: 2026-06-18
Stage at update: execute/analyze
Source/command: `python3 docs/visexp/r191_target_network_lineage.py --out docs/visexp/out`
Completeness: ok

R191 runs a fixed Codex task whose only useful answer is produced by a
pre-created local Python network probe. It checks target-process network
rows, not low-level Codex HTTP client rows.

## Aggregate

- Tasks: 1 ({'ok': 1})
- Record status: {'ok': 1}; target status: {'completed': 1}
- Target network effects: 4 / 4 joined (100.0%)
- Negative controls: observed=310, joined=0
- Scoped precision/recall: 100.0% / 100.0%
- Target network targets: {'127.0.0.1:0': 1, 'fd=3': 1, 'family=1': 1, '127.0.0.1:36299': 1}
- Target network actions: {'NET_BIND': 1, 'NET_LISTEN': 1, 'NET_CONNECT': 2}
- Target process commands: {'python3': 4}
- Network process commands: {'codex': 15, 'python3': 4}
- Broad lineage smoke: 1 task(s) returned non-zero; R191 status is scoped to the target-network oracle, while wrapper/out-of-scope effects may remain orphaned.


## Per Task

| Task | Status | Probe | Target network | Negative joined | Precision/Recall | Answer |
|------|--------|-------|---------------:|----------------:|------------------:|--------|
| `r191-codex-http` | ok | http:ok | 4/4 | 0 | 100.0%/100.0% | {"body": "r191-http-probe", "bytes": 15, "elapsed_ms": 511, "port": 36299, "probe": "http", "status": "ok"} |

## Claim Boundary

R191 supports C4 for a fixed command-mode Codex task that executes a local Python network probe: target-process bind/listen/connect rows are observed and joined, while wrapper negative-control effects remain unattributed. It does not prove arbitrary prompt compliance, full-history exact lineage, HTTP URL reconstruction, or C5/C6 user/tag evidence.
