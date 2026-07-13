# Real Preflight — RQ2 Cross-Family Problem Localization

## Verdict

**PASS**. This is executability evidence only; it is not admitted paper evidence and does not score confirmatory AgentRx or TELBench labels.

## Scope Executed

- development target: `agentreward_looping` (729 operations, 29 trajectories)
- ranker training family: `satraj_unsafe`
- AgentRx unlabeled trajectory: `2` (32 operations)
- TELBench unlabeled case: `0006` (20 spans)
- official TELBench native rows: bare=1, drift=1

## Development Sanity Metrics

These values only prove that materialized scores, independent grouping views, matched partitions, and post-ranking label joins execute end to end.

| View | AP | Work@25% recall | Groups@25% recall | Total groups |
|---|---:|---:|---:|---:|
| flat | 0.6914 | 1.0000 | 1 | 1 |
| session | 0.6238 | 0.3841 | 7 | 29 |
| raw_action | 0.6971 | 0.8189 | 6 | 18 |
| tag | 0.6538 | 0.3813 | 2 | 3 |
| induced | 0.6188 | 0.3621 | 11 | 46 |
| sql_role | 0.6914 | 1.0000 | 1 | 1 |
| sql_role_action | 0.6974 | 0.8217 | 4 | 12 |
| sql_role_action_status | 0.6971 | 0.8189 | 6 | 18 |
| matched_partition | 0.6125 | 0.3827 | 9 | 46 |

## Leakage and Execution Checks

- profiler visible-field allowlist passed: `True`
- confirmatory labels joined or scored: `False`
- induction invocation granularity: `one Rust invocation per trajectory`
- cross-trajectory semantic-path aggregation retained: `True`
- global matched group-size multiset exact: `True`
- every per-trajectory matched size multiset exact: `True`
- development selected Rust fields: `['action', 'phase', 'repeat_signal', 'repeat_state', 'tool_status']`
- AgentRx selected Rust fields: `['content', 'length_bucket', 'query_overlap', 'role']`
- TELBench selected Rust fields: `['action', 'content', 'query_overlap', 'tool_status']`
- the common risk score was materialized before any grouping; hidden development labels entered only in the final metric function.
- risk-tag thresholds were selected on the separate training family: `[0.33566267777129133, 0.48372536558051615, 0.485798722977424]`
- development visible-field provenance: `{'role': 'constant operation actor role; no outcome source', 'tool': 'source trajectory step tool name', 'action': 'source trajectory step action verb', 'phase': 'deterministic action-to-phase mapping in script/agent_trace_datasets.py', 'op': 'constant normalized operation type', 'repeat_signal': 'deterministic adjacent action-sequence feature in script/agent_trace_datasets.py', 'repeat_state': 'deterministic adjacent action-sequence feature in script/agent_trace_datasets.py', 'tool_status': 'presence of event-native trajectory.steps[].last_action_error'}`
- SQL rollup prefixes are implemented as three separate SQLite `GROUP BY` queries (`role`, `role/action`, and `role/action/tool_status`) and scored separately; SQLite has no native `ROLLUP` operator.
- the official DRIFT model input contains only `id`, `source_id`, `question`, and ordered `spans[{id,raw}]`.

## Official Sources

- Microsoft AgentRx commit: `f228165bfec60a801fd5fedd9d8ffe0f9de0c69d`
- NJU-LINK DRIFT commit: `1280b373b5af1954bf0577bf6d58b38e1bce341e`
- TELBench decrypted rows: `1000`
- TELBench decrypted SHA-256: `9f10b1cb12b1b0b065311e2c943a4d4fe899058cf4d210b0ebff75bd75a21082`
- observed llama-server process: `['2381408 Sat Jul 11 17:06:51 2026 /home/yunwei37/workspace/llama.cpp-latest/build/bin/llama-server -m /home/yunwei37/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf --host 127.0.0.1 --port 18081 -c 32768 -ngl 99']`
- observed llama-server model response: `{'models': [{'name': '/home/yunwei37/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf', 'model': '/home/yunwei37/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf', 'modified_at': '', 'size': '', 'digest': '', 'type': 'model', 'description': '', 'tags': [''], 'capabilities': ['completion'], 'parameters': '', 'details': {'parent_model': '', 'format': 'gguf', 'family': '', 'families': [''], 'parameter_size': '', 'quantization_level': ''}}], 'object': 'list', 'data': [{'id': '/home/yunwei37/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf', 'aliases': ['/home/yunwei37/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf'], 'tags': [], 'object': 'model', 'created': 1783816649, 'owned_by': 'llamacpp', 'meta': {'vocab_type': 2, 'n_vocab': 151936, 'n_ctx': 32768, 'n_ctx_train': 32768, 'n_embd': 2048, 'n_params': 3397103616, 'size': 2098976768, 'ftype': 'Q4_K - Medium'}}]}`

## Next Action

Independently review this preflight and its raw outputs. If it passes, extend the same driver to the approved development-selection and complete AgentRx/TELBench full matrix; do not interpret this one-case prefix.
