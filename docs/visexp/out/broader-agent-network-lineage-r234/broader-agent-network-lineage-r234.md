# R234 Controlled Agent/HTTP-Network Lineage

Last updated: 2026-06-18
Stage at update: execute/analyze
Source/command: `python3 docs/visexp/r234_broader_agent_network_lineage.py`
Completeness: ok

R234 extends the controlled exact-lineage oracle to another agent family
when available and to two Codex HTTP-family target-network probes: single GET
and repeated GET. It remains a
local controlled replication experiment, not user evidence.

## Aggregate

- Agent tasks: 1; agents: {'claude': 1}; statuses: {'ok': 1}.
- Network tasks: 2; agents: {'codex': 2}; probes: {'http': 1, 'http_repeat': 1}; statuses: {'ok': 2}.
- Combined scoped precision/recall: 100.0%/100.0%.
- Target network effects: 8/8 joined.
- Negative controls: observed=331, joined=0.
- Gates: agent_family=True, network=True, controlled_expansion=True.

## Agent Tasks

| Task | Agent | Status | Target | In scope | Neg observed | Neg joined | Precision/Recall | Answer |
|------|-------|--------|--------|---------:|-------------:|-----------:|------------------:|--------|
| `r234-claude-json-write` | claude | ok | completed | 34 | 6 | 0 | 100.0%/100.0% | result_json=created |

## Network Tasks

| Task | Agent | Status | Probe | Target network | Required actions | Neg joined | Precision/Recall | Answer |
|------|-------|--------|-------|---------------:|------------------|-----------:|------------------:|--------|
| `r234-codex-http` | codex | ok | http:ok | 4/4 | ok | 0 | 100.0%/100.0% | body=r234-http-probe bytes=15 ok=True |
| `r234-codex-http-repeat` | codex | ok | http_repeat:ok | 4/4 | ok | 0 | 100.0%/100.0% | body=r234-http-repeat\|r234-http-repeat bytes=33 ok=True |

## Claim Boundary

R234 supports C4/RQ3 for this controlled local expansion: at least one Claude command-mode run and all target network probe rows across the default HTTP target-network workloads join to the recorded agent task, with zero negative-control joins. It does not prove arbitrary agents, raw-socket or Claude-launched target-network workloads, HTTP payload/URL reconstruction, C5 user utility, or C6 tag adequacy.
