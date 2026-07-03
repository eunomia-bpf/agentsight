# Evaluation

Last updated: 2026-07-03
Stage at update: stage 3 design / stage 4 execute
Source/command: `script/agent_trace_datasets.py`, `agentpprof --operation-file`, `cargo test --manifest-path agentpprof/Cargo.toml`
Completeness: partial

## Claim-To-Experiment Map

| Claim | Required evidence | Current status | Next experiment |
|---|---|---|---|
| C1: `agentpprof` profiles operations and operation stacks without privileging prompt/session boundaries. | A non-Codex/Claude labeled trajectory enters as operation JSONL and folds with arbitrary `--stack` frames. | Supported for deterministic projection by R274 across 6 external datasets and 3,797 operations. | Add AndroidControl/ToolBench converters and larger Mind2Web shards. |
| C2: Recursive operation stacks recover useful task/subtask/phase structure from linear agent trajectories. | Compare mapped-stack output against dataset-native boundaries and action/step labels. | Partially supported by R274/R277: mapped task/phase stack keeps 103 unique stacks while fixed session stack explodes to 1,083. | Add boundary adequacy scoring against step/task oracles. |
| C3: Inferred boundary detection can replace hand-written stack rules. | Model/unsupervised boundary backend compared with deterministic rule oracle. | Unsupported; design only. | Implement inferred rule generation after deterministic dataset converters. |

## Dataset Matrix

| Dataset | Oracle fields | Access path | Current repository support | Evaluation use |
|---|---|---|---|---|
| WebLINX chat | demo id, turn, action, action history, utterances | HF Dataset Viewer: `McGill-NLP/WebLINX`, config `chat` | `script/agent_trace_datasets.py sample weblinx-chat` emits raw rows and operation JSONL. | First external smoke; action phase and demo/session folding. |
| WebShop expert | task name, reward, conversation actions | HF Dataset Viewer: `lclan/webshop_expert_trajectories` | `script/agent_trace_datasets.py sample webshop-expert` emits one operation per assistant action. | Long expert web trajectories; current top candidate. |
| API-Bank | gold API request, API domain | HF first-rows: `liminghao1630/API-Bank` | `script/agent_trace_datasets.py sample api-bank` emits one operation per gold API call; rows endpoint currently 500s after first rows. | Compact tool-call baseline. |
| AgentTrek | verified web GUI action tags | HF Dataset Viewer: `xlangai/AgentTrek` | `script/agent_trace_datasets.py sample agenttrek` emits one operation per action tag. | Large web GUI source; current top candidate if synthetic verified data is acceptable. |
| SWE-agent trajectories | issue instance, command trajectory, success target | HF Dataset Viewer: `nebius/SWE-agent-trajectories` | `script/agent_trace_datasets.py sample swe-agent-trajectories` emits one operation per command action. | Closest external software-agent source; current top candidate. |
| Mind2Web | task description, action sequence, website/domain, snapshots/traces | HF repo `osunlp/Mind2Web`; official raw dump | `script/agent_trace_datasets.py sample mind2web` downloads an HF repo JSON shard and emits operation JSONL; R274 sampled 9 tasks / 49 operations. | Cross-domain web operation-stack oracle. |
| AndroidControl | high-level goal, step instructions, screenshots, accessibility trees, JSON actions | Official Google Research TFRecord; HF mirrors | Manifested; converter pending. | Step-instruction boundary oracle for recursive depth. |
| Android in the Wild | instruction, screen/action episodes | Official google-research release | Manifested; converter pending. | Large-scale robustness once mobile converter exists. |
| ToolBench | instruction, solution path, toolenv, API calls, reasoning traces | Official OpenBMB release | Manifested; converter pending. | Tool/planner/API operation-stack oracle. |
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

## Candidate Selection

| Rank | Dataset | Current judgment | Why |
|---|---|---|---|
| 1 | WebShop expert | Keep as primary | Long expert trajectories, many operations per task, rewards, strong compression signal. |
| 2 | WebLINX chat | Keep as primary | Human/expert web demonstrations with clean action/demo/turn fields and multiple held-out splits. |
| 3 | SWE-agent trajectories | Keep as primary | Closest to coding-agent domain and has command/action trajectories plus success labels. |
| 4 | AgentTrek | Keep as secondary primary | Large verified GUI/web trajectory source; useful for scale, but synthetic provenance weakens human-oracle claims. |
| 5 | Mind2Web | Keep as primary after scaling | Strong cross-domain web oracle with task/domain/action labels; R274 only uses a small JSON shard. |
| 6 | API-Bank | Keep as baseline | Good tool-call oracle, but mostly single-step and less useful for recursive boundary depth. |

## Metrics And Oracles

| Metric | Definition | Oracle | Claim |
|---|---|---|---|
| Operation coverage | Fraction of dataset rows converted to operation JSONL without dropping required action fields. | Dataset row count and converter warnings. | C1 |
| Operation mapping coverage | Fraction of operations receiving derived fields such as `task` and `phase` under `--op-map`. | `agentpprof` JSON summary plus stack-analysis top-kind counts. | C1, C2 |
| Stack compression ratio | Total operation weight divided by unique folded stacks. | `agentpprof` JSON summary or folded stack count. | C2 |
| Fixed-boundary expansion factor | Unique stacks under fixed demo/session boundaries divided by unique stacks under mapped operation stacks. | R277 ablation on identical operation JSONL. | C1, C2 |
| Boundary adequacy | Agreement between inferred task/subtask/phase frames and dataset labels such as demo id, action type, step instruction, or solution path. | Dataset-native labels; manual adjudication for ambiguous cases. | C2, C3 |
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
| Flat/fixed/mapped stack ablation is tracked under R277. | done |
| Large dataset download/conversion commands are not yet implemented for AndroidControl, AITW, or ToolBench; Mind2Web still needs larger shard/raw-dump runs. | pending |
| Boundary adequacy scorer is not yet implemented. | pending |
