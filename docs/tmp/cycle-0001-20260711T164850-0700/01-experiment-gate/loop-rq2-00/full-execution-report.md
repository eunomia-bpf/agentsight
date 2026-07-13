# Full Execution Report — RQ2 Cross-Family Problem Localization

## Completion

The approved full matrix completed. This report records results for independent result review; it does not itself admit the claim into the paper.

- development tasks/seeds: `5` / `3`
- AgentRx trajectories/domains: `73` / `{'magentic': 44, 'tau': 29}`
- TELBench cases: `1000`
- confirmatory seeds: `3`
- deterministic ranker / point runs / bootstrap repetitions: `True` / `1` / `1000`
- matched controls per task and seed: `100`
- selected development configuration: `{'aggregation': 'mean', 'aggregation_candidates': {'depth-2:max': [0.14946753510268612, -0.5752458527863316, -1.0], 'depth-2:mean': [0.1749740643866431, -0.26697782963827305, -45.0], 'depth-3:max': [0.1500224223029515, -0.5752458527863316, -1.0], 'depth-3:mean': [0.17368674598622696, -0.2676779463243874, -46.0], 'depth-4:max': [0.1500224223029515, -0.5752458527863316, -1.0], 'depth-4:mean': [0.17368674598622696, -0.2676779463243874, -46.0]}, 'explicit_stack': 'explicit_action', 'fixed_sequential': 'fixed_sequential_w10', 'induced_depth_source': 'current approved family-held-out development selection over depths 2, 3, and 4', 'induced_max_depth': 2, 'sql': 'sql_role_action'}`

## Predeclared Decision Criteria

- positive RQ2 claim passes all criteria: **False**
### agentrx

- induced median metrics: `{'average_precision': 0.025841470451747395, 'groups_to_25_recall': 32.0, 'recall_at_30pct_work': 0.3424657534246575, 'work_to_25_recall': 0.20214395099540583}`
- strongest fixed/deployable baseline: `tag` `{'average_precision': 0.02833738122883822, 'groups_to_25_recall': 1.0, 'recall_at_30pct_work': 0.273972602739726, 'work_to_25_recall': 0.1460949464012251}`
- absolute correspondence: `False`
- relative tradeoff: `{'ap_gain': -0.002495910777090826, 'branches': {'ap': False, 'groups': False, 'work': False}, 'group_gain': -31.0, 'groups_worse': 31.0, 'paired_bootstrap_95': {'ap_gain': {'lower_95': -0.0091635410259856, 'median': -0.0021745100785339807, 'repetitions': 1000, 'upper_95': 0.006629768703669918}, 'group_gain_fraction': {'lower_95': -28.025, 'median': -12.0, 'repetitions': 1000, 'upper_95': -3.5}, 'work_gain_fraction': {'lower_95': -1.1643858885017422, 'median': -0.14404593086118672, 'repetitions': 1000, 'upper_95': 0.5530328836676293}}, 'pass': False, 'work_gain': -0.38364779874213845, 'work_worse': 0.38364779874213845}`
- matched null: `{'lower_95_delta': -0.03385145482388974, 'median_delta': -0.016539050535987754, 'pass': False, 'upper_95_delta': 0.02804747320061253}`

### telbench

- induced median metrics: `{'average_precision': 0.21487243275616558, 'groups_to_25_recall': 82.0, 'recall_at_30pct_work': 0.19004702194357367, 'work_to_25_recall': 0.6456343221049103}`
- strongest fixed/deployable baseline: `session` `{'average_precision': 0.2234207754102598, 'groups_to_25_recall': 268.0, 'recall_at_30pct_work': 0.30603448275862066, 'work_to_25_recall': 0.23604826546003016}`
- absolute correspondence: `False`
- relative tradeoff: `{'ap_gain': -0.00854834265409421, 'branches': {'ap': False, 'groups': False, 'work': False}, 'group_gain': 0.6940298507462687, 'groups_worse': -0.6940298507462687, 'paired_bootstrap_95': {'ap_gain': {'lower_95': -0.02018698331979879, 'median': -0.00605556524482391, 'repetitions': 1000, 'upper_95': 0.009371024610727901}, 'group_gain_fraction': {'lower_95': 0.5394014762516046, 'median': 0.6242424242424243, 'repetitions': 1000, 'upper_95': 0.7103902464171564}, 'work_gain_fraction': {'lower_95': -2.032683419791643, 'median': -1.6431534190149675, 'repetitions': 1000, 'upper_95': -0.9980243743602782}}, 'pass': False, 'work_gain': -1.7351792687255947, 'work_worse': 1.7351792687255947}`
- matched null: `{'lower_95_delta': -0.05082746773923241, 'median_delta': -0.03071057482822187, 'pass': False, 'upper_95_delta': 0.00022414948885537465}`

## Official TELBench Native Results

### bare

- cases: `1000`
- macro P/R/F1: `0.2450` / `0.1257` / `0.1521`
- micro P/R/F1: `0.2400` / `0.1321` / `0.1704`
- first-error accuracy: `0.0900`
- usage: `{'call_count': 967, 'input_tokens': 4339609, 'output_tokens': 86979, 'total_tokens': 4426588}`
- official fallback cases: `51`; errors: `{"LLM call failed after retries: Expecting ',' delimiter: line 5 column 83 (char 173)": 1, 'LLM call failed after retries: HTTP Error 400: Bad Request': 27, 'LLM call failed after retries: HTTP Error 500: Internal Server Error': 23}`

### drift

- cases: `1000`
- macro P/R/F1: `0.4565` / `0.3756` / `0.3655`
- micro P/R/F1: `0.4466` / `0.3295` / `0.3793`
- first-error accuracy: `0.1270`
- usage: `{'call_count': 2867, 'input_tokens': 9438723, 'output_tokens': 797204, 'total_tokens': 10235927}`
- official fallback cases: `167`; errors: `{"LLM call failed after retries: Expecting ',' delimiter: line 100 column 6 (char 12939)": 1, "LLM call failed after retries: Expecting ',' delimiter: line 108 column 6 (char 15024)": 1, "LLM call failed after retries: Expecting ',' delimiter: line 34 column 6 (char 6099)": 1, "LLM call failed after retries: Expecting ',' delimiter: line 393 column 6 (char 13041)": 1, "LLM call failed after retries: Expecting ',' delimiter: line 64 column 6 (char 7491)": 1, 'LLM call failed after retries: HTTP Error 400: Bad Request': 27, 'LLM call failed after retries: HTTP Error 500: Internal Server Error': 134, 'LLM call failed after retries: Invalid control character at: line 15 column 241 (char 609)': 1}`

## Native Clean-Intersection Sensitivity

The same official evaluator was rerun on the `824` cases with no fallback in either setting. The all-1,000 rows above remain the primary completion result.

- bare: macro-F1 `0.1655`, micro-F1 `0.1834`, first-error accuracy `0.0959`
- drift: macro-F1 `0.3930`, micro-F1 `0.3962`, first-error accuracy `0.1359`

## Source and Runtime Disclosure

- SQL rollup prefixes are separate SQLite `GROUP BY` queries and are scored separately.
- llama-server observation: `{'models_response': {'data': [{'aliases': ['/home/yunwei37/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf'], 'created': 1783823465, 'id': '/home/yunwei37/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf', 'meta': {'ftype': 'Q4_K - Medium', 'n_ctx': 32768, 'n_ctx_train': 32768, 'n_embd': 2048, 'n_params': 3397103616, 'n_vocab': 151936, 'size': 2098976768, 'vocab_type': 2}, 'object': 'model', 'owned_by': 'llamacpp', 'tags': []}], 'models': [{'capabilities': ['completion'], 'description': '', 'details': {'families': [''], 'family': '', 'format': 'gguf', 'parameter_size': '', 'parent_model': '', 'quantization_level': ''}, 'digest': '', 'model': '/home/yunwei37/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf', 'modified_at': '', 'name': '/home/yunwei37/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf', 'parameters': '', 'size': '', 'tags': [''], 'type': 'model'}], 'object': 'list'}, 'server_processes': ['2381408 Sat Jul 11 17:06:51 2026 /home/yunwei37/workspace/llama.cpp-latest/build/bin/llama-server -m /home/yunwei37/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf --host 127.0.0.1 --port 18081 -c 32768 -ngl 99']}`
- every official native batch uses a label-free TELBench input; the official evaluator joins gold only after merged predictions exist.
- the 32K model cannot execute every TELBench prompt; fallback cases and errors are reported per setting and native aggregate results are contextual rather than claim-decision evidence.
- execution concurrency changed only at completed 100-case recovery boundaries (8, then 16, then 32 workers); model, prompt, data, and evaluator stayed unchanged.

## Next Action

Run an independent result review that recomputes the primary rows, tests every predeclared criterion, and decides whether the result is supportive, contradictory, or inconclusive before returning to WRITE.
