# Agent Trace Exchange R303

This reproducer keeps local agent sessions as an exchange format, not a profiler object.
The direct trace import and converted operation JSONL import must produce byte-identical folded stacks under the same operation stack.

## Result

- Trace schema: `agentsight.agent-session.trace.v1`
- Sessions exported: 1
- Operations converted: 6
- Trace import: 6 samples / 5 stacks
- Operation import: 6 samples / 5 stacks
- Folded outputs identical: `True`
- Trace filesystem portable: `True`

## Files

- `trace_file`: `docs/visexp/out/agent-trace-exchange-r303/fixture-trace.json`
- `operation_file`: `docs/visexp/out/agent-trace-exchange-r303/fixture-operations.jsonl`
- `trace_folded`: `docs/visexp/out/agent-trace-exchange-r303/trace-import.folded`
- `operation_folded`: `docs/visexp/out/agent-trace-exchange-r303/operation-import.folded`
- `report_json`: `docs/visexp/out/agent-trace-exchange-r303/exchange-report.json`
