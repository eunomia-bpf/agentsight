# R182 Network Lineage Supplement

Last updated: 2026-06-15
Stage at update: execute/analyze
Source/command: `python3 docs/visexp/r182_network_record_suite.py --out docs/visexp/out`
Completeness: partial

This supplement wraps real `codex exec` tasks with `agentsight record` and
asks the agent to create loopback HTTP traffic in disposable workspaces. It
checks whether network effect rows inherit prompt/tool/process ancestry while
the R114 negative-control precision accounting still rejects concurrent noise.

Raw SQLite DBs and exported snapshots stay in the local work dir and are not committed.

## Aggregate

- Tasks: 2 ({'lineage_precision_ok': 2})
- Record status: {'ok': 2}; target status: {'completed': 2}; lineage status: {'precision_ok': 2}
- Overall precision/recall: precision=100.0%, recall=100.0%
- Negative controls: tasks_observed=2/2, observed=604, joined=0
- Network effects: joined=35 / 35 = 100.0%
- Target-specific network effects: joined=0 / 0 = 0.0%
- Network tasks: observed=2/2, joined=2/2
- Network targets: {'0.0.0.0:0': 7, '172.64.155.209:65535': 7, '104.18.32.47:65535': 7, '172.64.155.209:443': 7, 'family=10': 7}
- Target-specific network targets: {}
- Network process commands: {'codex': 35}
- Network actions: {'NET_BIND': 7, 'NET_CONNECT': 28}
- Network join methods: {'pid_family_time_window': 35}

## Per Task

| Task | Target | Lineage | Network | Joined | Target-specific | Targets | Process comms | Answer |
|------|--------|---------|--------:|-------:|----------------:|---------|---------------|--------|
| `r182-loopback-python` | completed | precision_ok | 15 | 15 | 0 | {'0.0.0.0:0': 3, '172.64.155.209:65535': 3, '104.18.32.47:65535': 3, '172.64.155.209:443': 3, 'family=10': 3} | {'codex': 15} | loopback_status=200 bytes=19 |
| `r182-http-server` | completed | precision_ok | 20 | 20 | 0 | {'104.18.32.47:65535': 4, '172.64.155.209:65535': 4, 'family=10': 4, '0.0.0.0:0': 4, '172.64.155.209:443': 4} | {'codex': 20} | server_status=ok bytes=15 |

## Claim Boundary

R182 is partial: it records the network lineage outcome for loopback-task runs, but C4 network-workload coverage should not be widened unless target-specific loopback or expected child-process network rows are observed, joined, and negative-control precision remains clean. Low-level agent-process network rows alone are implementation evidence for record-mode `--trace-net`, not proof of child-process loopback network capture. It does not provide C5 or C6 evidence.
