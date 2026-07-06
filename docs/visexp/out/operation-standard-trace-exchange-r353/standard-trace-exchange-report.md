# Operation Standard Trace Exchange R353

R353 verifies the Rust operation-file standard trace export/import path on
a deterministic prefix of an existing real labeled operation corpus.
It is an exchange/reproducibility smoke, not a new accuracy result.

## Result

- Status: `ok`
- Source operation file: `docs/visexp/out/operation-rank-feature-r324/visible-query-utility-operations.jsonl`
- Prefix rows: 512
- Standard trace events: 512
- Direct/imported folded equality: `True`
- Stack: `project,dataset,analysis_task,phase,op,action,status`

## Files

- `prefix_operation_file`: `docs/visexp/out/operation-standard-trace-exchange-r353/operation-prefix.jsonl`
- `standard_trace_file`: `docs/visexp/out/operation-standard-trace-exchange-r353/operation-prefix-chrome-trace.json`
- `direct_folded`: `docs/visexp/out/operation-standard-trace-exchange-r353/direct-operation.folded`
- `imported_folded`: `docs/visexp/out/operation-standard-trace-exchange-r353/standard-trace-import.folded`
- `report_json`: `docs/visexp/out/operation-standard-trace-exchange-r353/standard-trace-exchange-report.json`
- `index_html`: `docs/visexp/out/operation-standard-trace-exchange-r353/index.html`
