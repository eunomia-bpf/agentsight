# R232 External Cross-Repo Lineage

Last updated: 2026-06-18
Stage at update: execute/analyze
Source/command: `python3 docs/visexp/r232_external_crossrepo_lineage.py`
Completeness: ok

R232 reruns controlled Codex command-mode lineage tasks outside the
AgentSight repository. Non-network workloads use fresh external git
repositories; the network workload uses a local Python HTTP probe.

Raw DBs, snapshots, external workspaces, and per-event lineage CSVs stay
in the local work directory and are not committed.

## Aggregate

- Normal tasks: 4; network tasks: 1.
- Combined scoped precision/recall: 100.0%/100.0%.
- Normal in-scope effects: 353; negative joins: 0/242.
- Target network effects: 4/4 joined; negative joins: 0/238.
- External workload categories: {'repo-read': 1, 'edit-test': 2, 'write': 1, 'network': 1}.
- External workspace kinds: {'external_read': 1, 'external_python_bug': 1, 'external_json_write': 1, 'external_shell_fix': 1, 'r232-ext-http-probe': 1}.
- Gates: normal=True, network=True, external_crossrepo=True.

## Normal Tasks

| Task | Cat | Workspace | Target | Lineage | In scope | Neg observed | Neg joined | Answer |
|------|-----|-----------|--------|---------|---------:|-------------:|-----------:|--------|
| `r232-ext-read` | repo-read | external_read | completed | precision_ok | 20 | 1 | 0 | project=external-r232-read |
| `r232-ext-python-fix` | edit-test | external_python_bug | completed | precision_ok | 110 | 1 | 0 | tests=passed |
| `r232-ext-json-write` | write | external_json_write | completed | precision_ok | 139 | 235 | 0 | result_json=created |
| `r232-ext-shell-fix` | edit-test | external_shell_fix | completed | precision_ok | 84 | 5 | 0 | check=passed |

## Network Tasks

| Task | Status | Probe | Target network | Neg joined | Precision/Recall | Answer |
|------|--------|-------|---------------:|-----------:|------------------:|--------|
| `r232-ext-http-probe` | ok | http:ok | 4/4 | 0 | 100.0%/100.0% | {"body": "r232-http-probe", "bytes": 15, "elapsed_ms": 512, "port": 41769, "probe": "http", "status": "ok"} |

## Claim Boundary

R232 supports C4/RQ3 beyond the AgentSight repository for this controlled external-repo workload: scoped effects and target network rows join to the target Codex task, while negative controls remain unattributed. It does not prove arbitrary repositories, arbitrary network workloads, strict full-history prompt-row lineage, C5 developer utility, or C6 tag adequacy.
