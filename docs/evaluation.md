# Evaluation

Last updated: 2026-07-03
Stage at update: stage 3 design / stage 4 execute
Source/command: `script/agent_trace_datasets.py`, `script/operation_split.py`, `script/operation_leaveout_eval.py`, `script/operation_map_infer.py`, `script/operation_stack_depth_eval.py`, `agentpprof --operation-file`, `script/operation_stack_quality.py`, `cargo test --manifest-path agentpprof/Cargo.toml`
Completeness: partial

## Claim-To-Experiment Map

| Claim | Required evidence | Current status | Next experiment |
|---|---|---|---|
| C1: `agentpprof` profiles operations and operation stacks without privileging prompt/session boundaries. | A non-Codex/Claude labeled trajectory enters as operation JSONL and folds with arbitrary `--stack` frames. | Supported for deterministic projection by R279/R281/R282/R283/R284/R285/R286/R287/R288 across 11 external datasets and 15,554 operations, including held-out session, leave-dataset-out, recursive-depth, tool-agent-user, and expert trajectory-quality label tests. | Scale the best 3-4 datasets and add larger desktop/computer-use sources. |
| C2: Recursive operation stacks recover useful task/subtask/phase structure from linear agent trajectories. | Compare mapped-stack output against dataset-native boundaries and action/step labels. | Partially supported: R286 shows the same operation set can be folded from 9 dataset stacks to 57 phase stacks, 226 tool/semantic stacks, 455 action stacks, or 3,757 fixed-session stacks by changing only `--stack`; R288 AgentRewardBench has phase/action V-measure 0.784 and boundary F1 0.924 on expert-labeled web-agent trajectories. | Add sequence-level side-effect/looping and deeper subtask/step oracle scoring beyond action-level boundaries. |
| C3: Inferred boundary detection can replace hand-written stack rules. | Generated or model-inferred boundary backend compared with deterministic rule oracle. | Partially supported for deterministic learned-from-labeled-fields rule files, including held-out sessions and leave-dataset-out stress tests; R285 fixes the R284 API/tool negative cases by prioritizing a tool/API phase family before action-verb phase rules. Unsupported for unsupervised/model boundary detection. | Add leave-family-out validation and a non-rule boundary backend. |

## Dataset Matrix

| Dataset | Oracle fields | Access path | Current repository support | Evaluation use |
|---|---|---|---|---|
| WebLINX chat | demo id, turn, action, action history, utterances | HF Dataset Viewer: `McGill-NLP/WebLINX`, config `chat` | `script/agent_trace_datasets.py sample weblinx-chat` emits raw rows and operation JSONL. | First external smoke; action phase and demo/session folding. |
| WebShop expert | task name, reward, conversation actions | HF Dataset Viewer: `lclan/webshop_expert_trajectories` | `script/agent_trace_datasets.py sample webshop-expert` emits one operation per assistant action. | Long expert web trajectories; current top candidate. |
| API-Bank | gold API request, API domain | HF first-rows: `liminghao1630/API-Bank` | `script/agent_trace_datasets.py sample api-bank` emits one operation per gold API call; rows endpoint currently 500s after first rows. | Compact tool-call baseline. |
| AgentTrek | verified web GUI action tags | HF Dataset Viewer: `xlangai/AgentTrek` | `script/agent_trace_datasets.py sample agenttrek` emits one operation per action tag. | Large web GUI source; current top candidate if synthetic verified data is acceptable. |
| SWE-agent trajectories | issue instance, command trajectory, success target | HF Dataset Viewer: `nebius/SWE-agent-trajectories` | `script/agent_trace_datasets.py sample swe-agent-trajectories` emits one operation per command action. | Closest external software-agent source; current top candidate. |
| Mind2Web | task description, action sequence, website/domain, snapshots/traces | HF repo `osunlp/Mind2Web`; official raw dump | `script/agent_trace_datasets.py sample mind2web` downloads an HF repo JSON shard and emits operation JSONL; R274 sampled 9 tasks / 49 operations. | Cross-domain web operation-stack oracle. |
| AndroidControl | high-level goal, step instructions, screenshots, accessibility trees, JSON actions | Official Google Research TFRecord; HF mirror `smolagents/android-control` | `script/agent_trace_datasets.py sample android-control` emits one operation per UI action and strips screenshot payloads from saved raw rows; R278 sampled 2 episodes / 9 operations. | Step-instruction boundary oracle for recursive depth. |
| GUI-Odyssey | episode id, category, app combo, instruction, annotated step actions | HF Dataset Viewer: `OpenGVLab/GUI-Odyssey`, config `default`, split `all` | `script/agent_trace_datasets.py sample gui-odyssey` emits one operation per annotated GUI step; R279 sampled 500 episodes / 7,868 operations. | Best current large-scale mobile/cross-app trajectory source. |
| Android in the Wild | instruction, screen/action episodes | Official google-research release | Manifested; converter pending. | Large-scale robustness once mobile converter exists. |
| ToolBench | instruction, solution path, toolenv, API calls, reasoning traces | Official OpenBMB release plus HF mirror `tuandunghcmut/toolbench-v1` | `script/agent_trace_datasets.py sample toolbench` emits one operation per assistant tool action; R279 sampled 300 rows / 866 operations. | Tool/planner/API operation-stack oracle. |
| tau-bench trajectories | multi-turn user/assistant/tool messages, task domain, success/failure outcome, gold task actions | HF repo files: `AgentSuite/tau-bench-trajectories`, one JSONL per model | `script/agent_trace_datasets.py sample tau-bench-trajectories --repo-file gpt-4o-mini.jsonl` emits user prompt, assistant response, tool-call, and tool-observation operations; R287 sampled 50 episodes / 1,560 operations. | Best current tool-agent-user dialogue source; useful for dialogue/tool/observation phase stacks and outcome/failure analysis. |
| AgentRewardBench | expert success, side-effect, looping, optimality labels plus BrowserGym cleaned steps | HF Dataset Viewer annotations plus HF repo cleaned JSON: `McGill-NLP/agent-reward-bench` | `script/agent_trace_datasets.py sample agent-reward-bench` reads annotations, downloads matching `cleaned/<benchmark>/<model>/<experiment>/<task_id>.json`, and emits one browser-action operation per step; R288 sampled 38 trajectories / 729 operations across assistantbench, visualwebarena, webarena, and workarena. | Best current expert trajectory-quality oracle; useful for failure, side-effect, repetitive-action, and non-flamegraph diagnostics. |
| TRAIL | human-annotated reasoning/planning/execution errors | HF auto-gated dataset plus official benchmark repo | Manifested; gated access pending. | Best future failure-boundary oracle. |

## Run Tracker

| Run ID | Claim | Purpose | Command/config | Commit | Machine | Seed/reps | Result path | Status |
|---|---|---|---|---|---|---|---|---|
| R272 | C1, C2 | WebLINX external operation-file smoke | See command below | worktree based on `1d0134b` before this commit | local | 25 rows, offset 0 | `docs/visexp/out/external-agent-trace-weblinx-r272/` | done |
| R273 | C1, C2 | Cross-dataset operation-stack smoke across 5 labeled sources | WebLINX 500, WebShop 100, API-Bank 48, AgentTrek 200, SWE-agent 20; `--view operations` | worktree after `9673a30` | local | 3,748 operations | `docs/visexp/out/external-agent-trace-cross-dataset-r273/` | done |
| R274 | C1, C2 | Six-dataset operation mapping smoke | WebLINX 500, WebShop 100, API-Bank 48, AgentTrek 200, SWE-agent 20, Mind2Web 9; `--view operations` + `--op-map` task/phase mapping | worktree after `8125c26` | local | 3,797 operations | `docs/visexp/out/external-agent-trace-mapped-r274/` | done |
| R275 | C1, C2 | AndroidControl step-boundary oracle | TFRecord/parquet converter to operation JSONL | todo | local | at least 100 episodes | `docs/visexp/out/external-agent-trace-androidcontrol-r275/` | todo |
| R276 | C1, C2 | ToolBench tool/API stack oracle | official data converter for instruction/answer/toolenv | todo | local | at least G1/G2/G3 samples | `docs/visexp/out/external-agent-trace-toolbench-r276/` | todo |
| R277 | C2 | Stack abstraction ablation | flat stack vs fixed demo/session stack vs mapped operation stack | worktree after `8125c26` | local | same 3,797 operations as R274 | `docs/visexp/out/operation-stack-ablation-r277/` | done |
| R278 | C1, C2 | Expanded 8-dataset mapped-stack smoke | R274 inputs + ToolBench 40 + AndroidControl 2; `--view operations` + `--op-map` task/phase mapping | worktree after `04169d7` | local | 3,932 operations | `docs/visexp/out/external-agent-trace-expanded-r278/` | done |
| R279 | C1, C2 | Scaled 9-dataset mapped-stack run | R278 inputs + GUI-Odyssey 500, ToolBench 300, Mind2Web train_0 100; `--view operations` + `--op-map` task/phase mapping | worktree after `2a2528d` | local | 13,265 operations | `docs/visexp/out/external-agent-trace-scaled-r279/` | done |
| R280 | C2 | Operation-stack quality scorer | R279 operation files; coverage, V-measure, and sequence boundary F1 via `script/operation_stack_quality.py` | worktree after `2a2528d` | local | same 13,265 operations as R279 | `docs/visexp/out/operation-stack-quality-r280/` | done |
| R281 | C1, C2, C3 | Learned-from-labels operation mapping baseline | R279 operation files; `script/operation_map_infer.py` generates `--op-map-file`, then `agentpprof --operation-file --op-map-file` and `script/operation_stack_quality.py --op-map-file` rerun the same stack | worktree after `74ff667` | local | same 13,265 operations as R279 | `docs/visexp/out/operation-map-infer-r281/` | done |
| R282 | C1, C2, C3 | Held-out generated mapping validation | `script/operation_split.py` splits R279 operations by `dataset,session` with dataset stratification; `script/operation_map_infer.py` trains on 9,275 train operations; `agentpprof` and quality scorer evaluate 3,990 held-out operations with learned `--op-map-file` and no-map baseline | worktree after `027c4f2` | local | 1 deterministic 70/30 group split, seed `r282` | `docs/visexp/out/operation-map-heldout-r282/` | done |
| R283 | C2, C3 | Leave-dataset-out generated mapping, raw-action stack | `script/operation_leaveout_eval.py`; each of 9 datasets held out in turn; train mappings on the other 8; evaluate stack `project,dataset,task,phase,op,tool,action,status` with mapped vs no-map baseline | worktree after `9f2c6c0` | local | 9 leave-out folds | `docs/visexp/out/operation-map-leaveout-r283/` | done |
| R284 | C2, C3 | Leave-dataset-out generated mapping, semantic stack | Same as R283 but stack is `project,dataset,task,phase,op,tool,status`, removing raw `action` as a leaf to test semantic aggregation view | worktree after `9f2c6c0` | local | 9 leave-out folds | `docs/visexp/out/operation-map-leaveout-semantic-r284/` | done |
| R285 | C2, C3 | Leave-dataset-out semantic stack with API/tool phase precedence | Same as R284 after updating learned rule inference to classify API/tool traces before generic action-verb phase rules, including a generic `op=tool.*domain=` API fallback | worktree after `63f1a06` | local | 9 leave-out folds | `docs/visexp/out/operation-map-leaveout-api-r285/` | done |
| R286 | C1, C2 | Recursive stack-depth sweep over the same operations | `script/operation_stack_depth_eval.py`; same 13,265 R279 operations and R286 inferred op-map; compare dataset/task/phase/op/tool/semantic/action/fixed-session stack shapes through Rust `agentpprof --operation-file --stack` | worktree after `0a645c7` | local | 8 stack depths over identical operations | `docs/visexp/out/operation-stack-depth-r286/` | done |
| R287 | C1, C2 | tau-bench tool-agent-user trajectory converter and smoke | `script/agent_trace_datasets.py sample tau-bench-trajectories --limit 50 --repo-file gpt-4o-mini.jsonl`; Rust `agentpprof --operation-file` over tau-bench alone and combined with the R279 9-dataset set | worktree after `5a3abaa` | local | 50 episodes, 1,560 tau-bench operations; 10-dataset combined smoke has 14,825 operations | `docs/visexp/out/external-agent-trace-taubench-r287/` | done |
| R288 | C1, C2 | AgentRewardBench expert trajectory-quality labels and 11-dataset smoke | `script/agent_trace_datasets.py sample agent-reward-bench` at offsets 0, 40, 700, and 800; Rust `agentpprof --operation-file` over AgentRewardBench alone and combined with the R287 10-dataset set; stack fields include `status`, `side_effect`, `looping`, and `optimality` | worktree after `891bac8` | local | 38 trajectories, 729 AgentRewardBench operations; 11-dataset combined smoke has 15,554 operations | `docs/visexp/out/external-agent-trace-agentreward-r288/` | done |

R272 command:

```bash
python3 script/agent_trace_datasets.py sample weblinx-chat --limit 25 --offset 0

cargo run --manifest-path agentpprof/Cargo.toml -- \
  --project-root . \
  --project-name external-agent-traces \
  --operation-file .agentsight/datasets/agent-traces/weblinx-chat/chat-validation/operations-0-25.jsonl \
  --view files \
  --format folded \
  -o docs/visexp/out/external-agent-trace-weblinx-r272/weblinx.folded \
  --stack 'project,agent,dataset,task,session,phase,op,action,target,status' \
  --stack-rule 'task:authenticate=(target=login|target=email|action=type)' \
  --stack-rule 'task:navigate=(action=click|action=load|action=say)' \
  --stack-rule 'phase:select=(action=click)' \
  --stack-rule 'phase:input=(action=type)' \
  --stack-rule 'phase:open=(action=load)' \
  --stack-rule 'phase:dialogue=(action=say)'
```

## Result Summary

| Run | Result | Interpretation | Limitations |
|---|---|---|---|
| R272 | 25 WebLINX gold action operations produced 18 folded stacks with no prompt frame. Output: `docs/visexp/out/external-agent-trace-weblinx-r272/weblinx.folded`. | Confirms third-party labeled trajectories can enter as operation JSONL and use arbitrary recursive operation stacks. | Small sample; action-type rules only; no boundary adequacy metric yet. |
| R273 | 5 external datasets produced 3,748 operations and 100 folded stacks under `--view operations`; compression ratio 37.48. Outputs: `cross-dataset.folded`, `stack-analysis.json`, `stack-analysis.html`. | Confirms the same operation/operation-stack path works across web navigation, shopping, API calls, GUI replay, and software-engineering commands. | API-Bank is limited to first rows via Dataset Viewer; no Mind2Web/AndroidControl/ToolBench full converters yet. |
| R274 | 6 external datasets produced 3,797 operations and 103 folded stacks under `--view operations`; compression ratio 36.864. Outputs: `mapped.folded`, `agentpprof-result.json`, `stack-analysis.json`, `stack-analysis.html`. | Confirms `--op-map` derives reusable task/phase operation fields before `--stack` without adding a third abstraction or binding stacks to prompt/session boundaries. | Mind2Web sample is a small shard; mappings are deterministic and hand-written. |
| R277 | On the same 3,797 operations, flat stack produced 103 unique stacks, fixed session/demo stack produced 1,083 unique stacks, and mapped stack produced 103 unique stacks with added task/phase frames. | Directly tests the prompt/session-boundary objection: fixed boundaries fragment aggregation by 10.5x, while mapped operation stacks keep aggregation and add semantic depth. | Boundary adequacy is still structural/compression-based; no gold span scorer yet. |
| R278 | 8 external datasets produced 3,932 operations and 190 folded stacks; compression ratio 20.695. Outputs: `expanded.folded`, `agentpprof-result.json`, `stack-analysis.json`, `stack-analysis.html`. | Adds mobile UI and tool/API traces without changing the profiler abstraction; ToolBench intentionally increases stack diversity through long-tail API names. | AndroidControl is only a 2-episode smoke because row download includes screenshot payloads; ToolBench uses an HF mirror for lightweight sampling. |
| R279 | 9 external datasets produced 13,265 operations and 455 folded stacks; compression ratio 29.154. Outputs: `scaled.folded`, `agentpprof-result.json`, `stack-analysis.json`, `stack-analysis.html`. | Scaling GUI-Odyssey, ToolBench, and Mind2Web preserves aggregation and broadens the claim to cross-app mobile, web, software, and API/tool traces. | Still deterministic mapping; GUI-Odyssey dominates operation count and should be balanced in final figures. |
| R280 | On R279 operations, mapped fields have 100% coverage for stack fields; phase/action V-measure is 0.765; phase/action boundary precision is 1.0, recall 0.6862, F1 0.8139; task/dataset V-measure is 0.862. | First reusable quality scorer for operation-stack adequacy beyond flamegraphs. It shows deterministic mappings are conservative: they avoid false positive action-boundary changes but miss some fine-grained action changes. | Action labels are a proxy oracle for phase boundaries; deeper task/subtask adequacy still needs step-instruction or solution-path scoring. |
| R281 | `script/operation_map_infer.py` inferred 10 operation-field mapping rules from the 13,265 labeled operations. The resulting `learned.folded` is byte-identical to R279's hand-mapped `scaled.folded`; quality metrics reproduce R280: phase/action V-measure 0.765 and boundary F1 0.8139. | Confirms rule files can be generated from dataset labels and consumed by the same operation/operation-stack path; mapping rules are no longer tied to ad hoc CLI invocations. | This is a seeded deterministic taxonomy over observed labels, not a full unsupervised boundary detector. Held-out split validation is still required before a stronger C3 claim. |
| R282 | A deterministic group split produced 9,275 train operations and 3,990 held-out test operations across all 9 datasets. Train-only rules produce 209 held-out stacks (compression 19.091), versus 284 no-map stacks (compression 14.049). Held-out task/dataset V-measure improves from 0.8374 no-map to 0.8531 mapped; phase/action boundary F1 is 0.7774 mapped versus 0.9677 no-map because no-map leaves `phase` nearly identical to the fine-grained action label. | Shows generated mappings generalize across held-out sessions and improve semantic aggregation on unseen trajectories. It also clarifies the intended tradeoff: operation stacks deliberately coarsen low-level actions into reusable task/phase frames, so action-boundary F1 is not the only success metric. | Still not leave-dataset-out or unsupervised; action labels remain a proxy for phase boundaries. Need step-instruction and solution-path scoring for deeper recursive adequacy. |
| R283 | Leave-dataset-out with the R279-compatible stack (`...phase,op,tool,action,status`) is mostly neutral: only Mind2Web reduces unique stacks (9 to 3); aggregate summary reports 1/9 positive stack-reduction datasets, 0 negative. | This is an important stack-shape ablation: when raw `action` remains a leaf frame, phase/task mappings can improve interpretability without changing the number of folded stacks. It validates that users can preserve low-level action detail when they want exact action drilldown. | This view underestimates semantic aggregation because action labels still fragment stacks below the mapped phase. |
| R284 | Leave-dataset-out with semantic stack (`project,dataset,task,phase,op,tool,status`) reduces unique stacks on 6/9 datasets: AgentTrek 9→7, AndroidControl 5→3, GUI-Odyssey 6→5, Mind2Web 9→3, SWE-agent 20→16, WebLINX 7→6. ToolBench regresses 173→179, API-Bank regresses 1→3, WebShop is neutral at 119. | Shows the same operation sequence can be folded at a different semantic depth by changing only `--stack`. It also surfaces where the current mapping taxonomy is weak: API and ToolBench need a tool/API-family layer rather than action-verb phase rules. | Still deterministic and taxonomy-seeded; leave-family-out and deeper step/solution-path oracles remain open. |
| R285 | Re-running the R284 semantic stack after API/tool phase precedence removes all negative leave-out regressions. Aggregate summary: 6/9 positive stack-reduction datasets, 0 negative, weighted stack reduction 1162.005 per 1k operations. API-Bank is neutral at 1→1 and ToolBench is neutral at 173→173; the six positive datasets remain AgentTrek, AndroidControl, GUI-Odyssey, Mind2Web, SWE-agent, and WebLINX. | Confirms that phase mapping must respect operation-family boundaries before action verbs. Tool/API traces are still operations, but their phase should be derived from tool/API structure rather than lexical verbs like `search`, `show`, or `create`. | This is still deterministic taxonomy-seeded mapping. It validates the two-abstraction design path, not unsupervised discovery; deeper task/subtask adequacy and leave-family-out validation remain open. |
| R286 | A recursive stack-depth sweep over the same 13,265 operations produced 9 dataset stacks, 11 task stacks, 57 phase stacks, 57 op stacks, 226 tool stacks, 226 semantic stacks, 455 action stacks, and 3,757 fixed-session stacks. Phase/action V-measure is 0.7638 and phase/action boundary F1 is 0.8095 under the shared R286 mapping. | Directly validates the design requirement that operation stacks are user-selected recursive projections rather than fixed prompt/session boundaries. Adding `session` causes an 8.26x expansion relative to action depth and 417.44x relative to dataset depth, which explains why session should be optional drilldown, not the default abstraction. | This is a stack-shape and boundary-proxy result; it does not yet prove unsupervised boundary discovery or deeper step-instruction/solution-path adequacy. |
| R287 | tau-bench adds 50 multi-turn tool-agent-user episodes and 1,560 operations: 414 user prompt ops, 364 assistant LLM response ops, 391 tool-call ops, and 391 tool-observation ops. The tau-only stack produces 68 unique stacks and compression 22.941; phase/action V-measure is 0.7868 and phase/action boundary F1 is 0.699 with precision 1.0. Combined with R279, the 10-dataset smoke covers 14,825 operations and 509 stacks; tau-bench becomes the third-largest source by operation count. | Confirms the same operation/operation-stack path handles dialogue, tool calls, and tool observations without adding a new abstraction. tau-bench is a stronger future oracle than ToolBench for user-agent-tool phase analysis because it includes outcomes and expected task actions. | Current run samples one model file (`gpt-4o-mini.jsonl`) and 50 episodes; larger multi-model tau-bench runs and outcome-specific analysis remain pending. |
| R288 | AgentRewardBench adds 38 expert-reviewed web-agent trajectories and 729 operations across assistantbench, visualwebarena, webarena, and workarena. The AgentRewardBench-only label stack produces 78 unique stacks; phase/action V-measure is 0.784 and phase/action boundary F1 is 0.9236 with precision 1.0. The 11-dataset combined smoke covers 15,554 operations and 553 stacks; task/dataset V-measure is 0.8593 and phase/action V-measure is 0.7791. | Confirms expert trajectory-quality labels can be carried as operation fields and folded recursively without a new failure/label abstraction. It also adds a non-flamegraph diagnostic target: success, side-effect, looping, and optimality can be projected as stack frames or scored in HTML/JSON reports. | The sample is intentionally lightweight because cleaned BrowserGym JSON files are large. Single-step `step_error` is a poor proxy for looping, and benchmark alone only weakly predicts side effects; final claims need sequence-level repeated-action/side-effect mappings. |

## Candidate Selection

| Rank | Dataset | Current judgment | Why |
|---|---|---|---|
| 1 | GUI-Odyssey | Keep as primary | Large cross-app mobile episodes, clean step/action labels, easy HF sampling, strong scale signal in R279. |
| 2 | WebShop expert | Keep as primary | Long expert trajectories, many operations per task, rewards, strong compression signal. |
| 3 | tau-bench trajectories | Keep as primary | Best current user-agent-tool dialogue source; has multi-turn messages, tool calls, observations, outcomes, and gold task actions. |
| 4 | AgentRewardBench | Keep as primary failure/quality oracle | Best current expert-labeled outcome, side-effect, looping, and optimality source; R288 shows it folds through the same operation-stack path. |
| 5 | ToolBench | Keep as primary | Best current long-tail API source; R279 exposes API-domain stack diversity. |
| 6 | WebLINX chat | Keep as primary | Human/expert web demonstrations with clean action/demo/turn fields and multiple held-out splits. |
| 7 | Mind2Web | Keep as secondary primary | Strong cross-domain web oracle with task/domain/action labels; train_0 shard scales to 100 rows / 774 ops. |
| 8 | SWE-agent trajectories | Keep as domain bridge | Closest to coding-agent domain and has command/action trajectories plus success labels, but sampled rows are smaller than GUI/web sources. |
| 9 | AgentTrek | Keep as scale supplement | Large verified GUI/web trajectory source; useful for scale, but synthetic provenance weakens human-oracle claims. |
| 10 | AndroidControl | Keep as boundary oracle after heavier sampling | Step instructions provide a stronger subtask oracle than action type, but screenshot payloads make sampling heavier. |
| 11 | API-Bank | Keep as baseline | Good compact tool-call oracle, but mostly single-step and less useful for recursive boundary depth. |

## Metrics And Oracles

| Metric | Definition | Oracle | Claim |
|---|---|---|---|
| Operation coverage | Fraction of dataset rows converted to operation JSONL without dropping required action fields. | Dataset row count and converter warnings. | C1 |
| Operation mapping coverage | Fraction of operations receiving derived fields such as `task` and `phase` under `--op-map`. | `agentpprof` JSON summary plus stack-analysis top-kind counts. | C1, C2 |
| Stack compression ratio | Total operation weight divided by unique folded stacks. | `agentpprof` JSON summary or folded stack count. | C2 |
| Fixed-boundary expansion factor | Unique stacks under fixed demo/session boundaries divided by unique stacks under mapped operation stacks. | R277 ablation on identical operation JSONL. | C1, C2 |
| Boundary adequacy | Agreement between inferred task/subtask/phase frames and dataset labels such as demo id, action type, step instruction, or solution path. | Dataset-native labels; manual adjudication for ambiguous cases. | C2, C3 |
| Phase/action V-measure | Homogeneity/completeness between mapped phase labels and dataset action labels. | `operation_stack_quality.py --oracle-pair phase:action`. | C2 |
| Sequence boundary F1 | Precision/recall of mapped phase changes against action-label changes within each session. | `operation_stack_quality.py --boundary-pair phase:action`. | C2 |
| Tool-agent role alignment | Homogeneity/completeness between normalized operation kind and message role. | R287 `operation_stack_quality.py --oracle-pair op:role`. | C1, C2 |
| Trajectory-quality label coverage | Fraction of operations with expert `status`, `side_effect`, `looping`, and `optimality` labels. | R288 AgentRewardBench operation JSONL and `operation_stack_quality.py --coverage-field`. | C1, C2 |
| Failure/looping/side-effect diagnostics | Alignment between stack frames, sequence boundaries, and expert trajectory-quality labels. | R288 `operation_stack_quality.py --oracle-pair step_error:looping --oracle-pair benchmark:side_effect`; future sequence-level mappings should replace these weak proxies. | C2 |
| Held-out mapping compression delta | Unique stack reduction and compression improvement when train-derived op-map rules are applied to unseen sessions. | R282 mapped vs no-map folded stacks on identical held-out operation JSONL. | C2, C3 |
| Leave-dataset-out stack reduction | Unique stack change when one full dataset is held out from mapping-rule generation. | R283/R284 mapped vs no-map folded stacks, one held-out dataset per fold. | C2, C3 |
| Recursive stack-depth expansion | Unique stack count and compression change as the same operations are folded with progressively deeper `--stack` specs. | R286 depth sweep over identical R279 operations and one R286 op-map. | C1, C2 |
| Abstraction ablation delta | Difference in compression and boundary adequacy between flat, fixed-boundary, and recursive stacks. | Same operation JSONL under different `--stack` configs. | C1, C2 |
| Transition concentration | Top weighted parent-child stack transitions from `operation_stack_analysis.py`. | Folded stack transition table. | C2 |

## Reproducibility Checklist

| Item | Status |
|---|---|
| Raw external samples are kept under `.agentsight/`, which is gitignored. | done |
| Normalized operation JSONL omits raw task text by default. | done |
| First external smoke output is tracked under `docs/visexp/out/`. | done |
| Cross-dataset non-flamegraph analysis emits tree, top-kind bars, and transition tables. | done |
| Rust unit tests cover operation JSONL input. | done |
| Rust unit tests cover `--op-map` operation field mapping before stacking. | done |
| Mind2Web HF repo JSON shard sampling is implemented. | done |
| ToolBench HF mirror conversation sampling is implemented. | done |
| AndroidControl lightweight sampling is implemented with screenshot redaction for saved raw rows. | done |
| GUI-Odyssey lightweight sampling is implemented. | done |
| tau-bench trajectory JSONL sampling is implemented and tracked under R287. | done |
| AgentRewardBench annotation-plus-cleaned-trajectory sampling is implemented and tracked under R288. | done |
| Flat/fixed/mapped stack ablation is tracked under R277. | done |
| Operation-stack quality scorer is implemented and tracked under R280. | done |
| Learned-from-labeled-fields op-map generation is implemented and tracked under R281. | done |
| Held-out split validation for generated op-map rules is implemented and tracked under R282. | done |
| Leave-dataset-out validation for generated op-map rules is implemented and tracked under R283/R284. | done |
| Recursive stack-depth sweep over identical operations is implemented and tracked under R286. | done |
| Large full-dataset conversion commands are not yet implemented for AndroidControl, AITW, official ToolBench, or AgentRewardBench; Mind2Web still needs larger shard/raw-dump runs. | pending |
| Deeper subtask/step/sequence-level failure adequacy scorer is not yet implemented. | pending |
| Leave-family-out validation across broader dataset families is not yet implemented. | pending |
