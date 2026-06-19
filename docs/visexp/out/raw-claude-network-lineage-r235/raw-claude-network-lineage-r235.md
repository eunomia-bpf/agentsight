# R235 Raw/Claude Target-Network Lineage

Last updated: 2026-06-18
Stage at update: execute/analyze
Source/command: `python3 docs/visexp/r235_raw_claude_network_lineage.py`
Completeness: partial

R235 tests raw TCP, multiprocess TCP, and Claude-launched target-network probes.
It is a controlled local replication experiment, not user evidence.

## Aggregate

- Tasks: 4; ok tasks: 1.
- Agents: {'codex': 2, 'claude': 2}; probes: {'tcp': 2, 'multiprocess_tcp': 1, 'http': 1}.
- Probe by agent: {'codex:tcp': 1, 'codex:multiprocess_tcp': 1, 'claude:http': 1, 'claude:tcp': 1}.
- Target network effects: 3/3 joined.
- Required-action task gate: 1/4 tasks produced the required target network actions.
- Target rows were observed only for 1/4 tasks; 3 probe-ok tasks produced zero target rows.
- Negative controls: observed=305, joined=0.
- Precision/recall over observed scoped rows: 100.0%/100.0%.
- Gates: raw_socket=False, claude_launched_network=False, aggregate=False.
- Interpret 0/0 target rows on partial tasks as a capture failure, not as lineage success.

## Tasks

| Task | Agent | Status | Probe | Target network | Required actions | Neg joined | Observed-row precision/recall | Result |
|------|-------|--------|-------|---------------:|------------------|-----------:|------------------:|--------|
| `r235-codex-tcp` | codex | ok | tcp:ok | 3/3 | ok | 0 | 100.0%/100.0% | body=R235-TCP-PROBE bytes=14 ok=True |
| `r235-codex-multiprocess-tcp` | codex | partial | multiprocess_tcp:ok | 0/0 | NET_BIND,NET_LISTEN,NET_CONNECT | 0 | 100.0%/100.0% | body=corpitlum-532r bytes=14 ok=True |
| `r235-claude-http` | claude | partial | http:ok | 0/0 | NET_BIND,NET_LISTEN,NET_CONNECT | 0 | 100.0%/100.0% | body=r235-http-probe bytes=15 ok=True |
| `r235-claude-tcp` | claude | partial | tcp:ok | 0/0 | NET_BIND,NET_LISTEN,NET_CONNECT | 0 | 100.0%/100.0% | body=R235-TCP-PROBE bytes=14 ok=True |

## Claim Boundary

R235 is partial: at least one raw-socket, Claude-launched-network, or negative-control gate did not pass.
