# Agent Trace Chrome Exchange R306

R306 verifies a standard trace exchange path for local agent sessions.
Chrome/Perfetto trace JSON is used only as an import/export format; after import, profiling continues over operation JSONL.

## Result

- Chrome trace valid: `True`
- Chrome events: 6
- Operations from direct trace conversion: 6
- Operations from Chrome trace import: 6
- Direct trace/import folded equality: `True`
- Chrome import folded equality: `True`
- Stack: `project,agent,op,phase,tool,status`

## Files

- `agent_trace_file`: `docs/visexp/out/agent-trace-chrome-exchange-r306/fixture-agent-trace.json`
- `chrome_trace_file`: `docs/visexp/out/agent-trace-chrome-exchange-r306/fixture-chrome-trace.json`
- `direct_operation_file`: `docs/visexp/out/agent-trace-chrome-exchange-r306/fixture-direct-operations.jsonl`
- `chrome_operation_file`: `docs/visexp/out/agent-trace-chrome-exchange-r306/fixture-chrome-operations.jsonl`
- `trace_folded`: `docs/visexp/out/agent-trace-chrome-exchange-r306/trace-import.folded`
- `direct_operation_folded`: `docs/visexp/out/agent-trace-chrome-exchange-r306/direct-operation-import.folded`
- `chrome_operation_folded`: `docs/visexp/out/agent-trace-chrome-exchange-r306/chrome-operation-import.folded`
- `report_json`: `docs/visexp/out/agent-trace-chrome-exchange-r306/chrome-exchange-report.json`
