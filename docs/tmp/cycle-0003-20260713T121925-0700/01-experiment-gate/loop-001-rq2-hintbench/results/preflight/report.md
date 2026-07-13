# HINTBench RQ2 PREFLIGHT report

**Execution status:** VALID
**Tested-hypothesis verdict:** PREFLIGHT_ONLY
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
- preflight scorer-path work (not a scientific selection): 60 / 60
- all 24 AgentProf/flat candidate identity checks: exact

## Preflight point estimates

| Method | Work | Work fraction | Macro recall | Micro recall | Safe work | Groups |
|---|---:|---:|---:|---:|---:|---:|
| agentprof | 60 | 1.000000 | 1.000000 | 1.000000 | 25 | 33 |
| native | 35 | 0.583333 | 1.000000 | 1.000000 | 0 | 60 |
| independent_step | 60 | 1.000000 | 1.000000 | 1.000000 | 25 | 60 |
| session | 35 | 0.583333 | 1.000000 | 1.000000 | 0 | 2 |
| raw_action | 60 | 1.000000 | 1.000000 | 1.000000 | 25 | 13 |
| flat_exact | 60 | 1.000000 | 1.000000 | 1.000000 | 25 | 33 |
| width_only | 60 | 1.000000 | 1.000000 | 1.000000 | 25 | 33 |

## Identity and controls

- exact flat reconstruction equals AgentProf ranking tiers and work curve: yes
- mappable-target sensitivity completed: yes
- width-only control completed: yes
- count/shifted leaf, prefix, and global conservation: exact

## Completion and interpretation boundary

- terminal localizer outputs: 2
- evaluated operations: 60
- complete: True
- command: `script/hintbench_profile_localization_eval.py preflight --test-url https://anonymous.4open.science/api/repo/HINTBench-B841/file/data/hintbench.json --validation-url https://anonymous.4open.science/api/repo/HINTBench-B841/file/data/hintbench_val.json --agentpprof-bin agentpprof/target/release/agentpprof --base-url http://127.0.0.1:8012/v1 --model /home/yunwei37/workspace/models/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf --out docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/preflight`
- this one experiment is evidence toward fixed RQ2, not an answer to the entire RQ
- Wilson path-max is a predeclared downstream scorer, not an AgentProf built-in ranker
- an exact SQL/GROUP BY reconstruction is an algebraic identity control, not a claimed loss
