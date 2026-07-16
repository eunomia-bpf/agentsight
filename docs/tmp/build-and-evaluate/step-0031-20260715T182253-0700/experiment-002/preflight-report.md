# Experiment 002 Real Preflight

**Completed:** 2026-07-15T21:08:28-07:00

**Recovered and recorded:** 2026-07-15T21:28:12-07:00

**State:** PASS; connectivity and product-path evidence only

## Question

Does the approved Qwen3.6-27B backend execute the unchanged AgentProf raw-tag,
declared-task-tag, profile, and JSON path on one real official AgentBoard row
from each of the nine task families, using the fixed model settings and
distinct Experiment 002 output directory?

**Post-audit correction.** The preflight did execute the intended declared
task-tag, construction, and JSON paths. Its auxiliary raw `session_tag` field
was separate but did not preserve the pre-existing session request semantics;
the step-level outer audit found and the release implementation repaired that
product-contract defect. The registered scorer never reads `session_tag`, and
the declared request remained unchanged, so this correction does not alter the
preflight's executability conclusion or any completed `task_tag` result.

This preflight does not test the accuracy hypothesis. Its outputs are not
scored, are not used to change the taxonomy, descriptions, prompt, model
settings, or plan, and cannot enter the paper.

## Real Inputs And Commands

The dedicated server used:

```bash
/home/yunwei37/workspace/llama.cpp-latest/build/bin/llama-server \
  -m /home/yunwei37/workspace/models/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf \
  --alias qwen3.6-27b --host 127.0.0.1 --port 18082 -ngl 99 \
  --ctx-size 4096 --parallel 1 --jinja --reasoning off --reasoning-budget 0
```

`/v1/models` was retained at
`.agentsight/experiments/step-0031-agentboard-task-identity/27b/models.json`.
It reported alias `qwen3.6-27b`, GGUF Q4_K_M, context 4,096, and
27,320,697,856 parameters. The file SHA-256 is
`17e5ad70fb599d11c704dabe183acf1aef47743dae49576b73addd068e5abba7`.

The real preflight ran the plan's unchanged AgentProf command shape against
`.agentsight/experiments/step-0031-agentboard-task-identity/agentboard-preflight.trace.json`,
with all nine fixed `--task-choice` values, cache disabled, model alias
`qwen3.6-27b`, and output:

```text
.agentsight/experiments/step-0031-agentboard-task-identity/27b/preflight-profile.json
```

Its SHA-256 is
`62f07ea65d390051c4de85bd39e95b46953d4ddf4fc5259366a63c20a0d7963a`.

## Results

- exactly nine real sessions were emitted, one source-selected row per official
  task family;
- all nine retained distinct source session IDs;
- all nine raw `session_tag` values were nonempty;
- all nine declared `task_tag` values were nonempty and belonged to the fixed
  nine-tag grammar;
- the operation profile used view `operations` and stack
  `session,task,prompt`;
- the profile contained nine unique stacks with total additive weight nine;
- the raw and declared fields remained separately visible in both the session
  JSON and folded stack text; and
- the output remained inside the distinct `27b/` directory and did not
  overwrite any Experiment 001 artifact.

Observed declared outputs were two `alfworld`, one `babyai`, one `jericho`, one
`pddl`, three `toolquery`, and one `webshop`. They are recorded only to prove
that the grammar and fields engaged. They were not joined to source labels or
used to judge accuracy, choose a setting, or revise the approved experiment.

## Decision

REAL PREFLIGHT passes. The full experiment must run the complete 1,012-row
trace three times from the start with the identical source, product path,
model, taxonomy, prompt, grammar, and no-cache setting. Only the three complete
profiles and unchanged scorer manifest may enter RESULT REVIEW.
