# R238 Direct-Only Repetition Summary

Last updated: 2026-06-19
Stage at update: audit supplement
Completeness: compact summary only

Source command:
`for i in 1 2 3 4 5; do python3 docs/visexp/r237_agent_execution_witness_network_capture.py --agentsight-bin collector/target/debug/agentsight --task-limit 2 --out-dir /tmp/agentsight-r238-ready-direct-smoke-$i; done`

This file summarizes five local direct-only JSON outputs. The raw DBs,
snapshots, and per-event CSVs remain local-only and are not committed.

## Result

All 5 repetitions passed the direct-readiness smoke:

- 10/10 direct-python tasks had `capture_status=captured_joined`.
- 10/10 runtime witnesses passed.
- 10/10 witness ports were observed and joined.
- 35/35 target network rows joined.
- 0 target network rows were orphaned.

Boundary: these repetitions did not include Codex/Claude-launched tasks and
observed 0 negative-control effects. They support the process-tracer readiness
stability claim for direct controls only. Negative-control precision and the
remaining Codex/Claude-launched boundary are supported or exposed by the
official R238 full-run artifact.
