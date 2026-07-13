# HINTBench RQ2 FULL report

**Execution status:** VALID
**Tested-hypothesis verdict:** INCONCLUSIVE
**RQ:** RQ2 — Does Profiler Output Correspond to Real Problems?
**Paper role:** decisive RQ2 evidence (FULL only)

## Source and protocol

- validation: 80 records, SHA-256 `3e3cb4d692faccbf1ca7bc4826fddba9af5feeb6373b00b7f9c14802059e7449`
- test: 536 records, SHA-256 `87b33d3941be49cc40e6b38e1faec3cb420fd3483369eff68821e43a4db62e44`
- official evaluator SHA-256: `ab7bcfc70d6cb45fe91c8020a61754312c9fb7e6a8cb909fb260aab76236ab80`
- AgentProf: `agentpprof 0.2.37`
- model argument: `/home/yunwei37/workspace/models/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf`
- official prompt body + exact `[STEP_ID=<id>]` newline prefix: yes
- exact templated prompts tokenized: 616
- longest prompt tokens: 8497; output reserve: 1024; context: 32768
- localizer request: temperature 0, top-p 1, max_tokens 1024, reasoning disabled, constrained JSON
- HINTBench trajectories are official human-verified synthetic scenarios

## Validation selection

- selected field order: `action,environment,phase,status`
- validation work at >=80% macro recall: 2109 / 3050
- all 24 AgentProf/flat candidate identity checks: exact

## Test point estimates

| Method | Work | Work fraction | Macro recall | Micro recall | Safe work | Groups |
|---|---:|---:|---:|---:|---:|---:|
| agentprof | 5353 | 0.415702 | 0.802083 | 0.782516 | 1209 | 2294 |
| native | 7460 | 0.579327 | 0.800625 | 0.813433 | 266 | 12877 |
| independent_step | 12877 | 1.000000 | 0.997917 | 0.996802 | 3368 | 12877 |
| session | 7616 | 0.591442 | 0.815417 | 0.830490 | 266 | 536 |
| raw_action | 5961 | 0.462918 | 0.800000 | 0.784648 | 1423 | 412 |
| flat_exact | 5353 | 0.415702 | 0.802083 | 0.782516 | 1209 | 2294 |
| width_only | 11516 | 0.894308 | 0.827708 | 0.818763 | 2908 | 2294 |

## Identity and controls

- exact flat reconstruction equals AgentProf ranking tiers and work curve: yes
- mappable-target sensitivity completed: yes
- width-only control completed: yes
- count/shifted leaf, prefix, and global conservation: exact

## Paired trajectory-cluster uncertainty

- AgentProf − native: percentile 95% interval [-0.222392822319875, -0.10168222715963944]
- AgentProf − independent_step: percentile 95% interval [-0.6296752912154064, -0.5093042488561504]
- AgentProf − session: percentile 95% interval [-0.22539317726630984, -0.10460349352408767]
- AgentProf − raw_action: percentile 95% interval [-0.2937092281344291, 0.008566253766559]
- completed replicates: 10,000
- bootstrap seed: 20260713
- resampling: 400 risky + 136 safe complete trajectories with replacement
- flat identity exact in every replicate: yes

## Completion and interpretation boundary

- terminal localizer outputs: 616
- evaluated operations: 12877
- complete: True
- command: `script/hintbench_profile_localization_eval.py full --test-url https://anonymous.4open.science/api/repo/HINTBench-B841/file/data/hintbench.json --validation-url https://anonymous.4open.science/api/repo/HINTBench-B841/file/data/hintbench_val.json --agentpprof-bin agentpprof/target/release/agentpprof --base-url http://127.0.0.1:8012/v1 --model /home/yunwei37/workspace/models/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf --bootstrap 10000 --seed 20260713 --resume --out docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full`
- this one experiment is evidence toward fixed RQ2, not an answer to the entire RQ
- Wilson path-max is a predeclared downstream scorer, not an AgentProf built-in ranker
- an exact SQL/GROUP BY reconstruction is an algebraic identity control, not a claimed loss
