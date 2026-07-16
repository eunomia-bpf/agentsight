# Experiment Plan: 27B Backend for Declared AgentBoard Task Identity

**Proposed:** 2026-07-15T21:01:34-07:00
**State:** proposed; requires independent plan approval before any request
**Paper question:** **RQ3 — How Accurate Are the Tags?**

## Tested Hypothesis

> On the same complete official AgentBoard test population, the already-used
> local Qwen3.6-27B model running the unchanged AgentProf declared-taxonomy
> path assigns goals to the user-declared official task-family taxonomy with at
> least 0.80 macro-F1 and 0.80 micro accuracy, above the majority control,
> while retaining stable grammar-valid identities across repetitions.

This is one fixed-model-backend hypothesis for the same literal task-identity
component of fixed RQ3. It changes neither RQ3 nor the declared-taxonomy
algorithm. Greater capacity motivates the substitution, but Qwen2.5-3B and
Qwen3.6-27B also differ in generation, training, and architecture; the
experiment does not identify parameter count as the cause of any difference.
It cannot answer phase identity, action identity, boundary identity, or all of
RQ3.

## Why This Is The Smallest Valid Follow-Up

Experiment 001 completed every registered row and independently established
that Qwen2.5-3B plus the fixed declared-taxonomy bundle is syntactically valid
and deterministic but semantically inadequate: 0.3943 accuracy and 0.1912
macro-F1. The failure is an assignment collapse, not a grammar, cache, adapter,
or stability failure.

No independent AgentBoard training/reference split exists in the official
release. Adding rules, examples, label descriptions, or prototypes based on
the observed 1,012 test answers would contaminate the evidence. The repository
already contains and has used Qwen3.6-27B Q4_K_M as the fixed reader in the
complete Step 0019 experiment. Replacing only the fixed model backend therefore
tests the most direct remaining implementation alternative without changing
the benchmark, task taxonomy, prompt, grammar, product path, scorer, or paper
story. Greater capacity is one plausible explanation for a difference, not the
isolated intervention.

This is not presented as a new tagging algorithm or a model-scaling law. It is
a direct test of whether the existing optional declared-taxonomy mechanism can
produce accurate identities when backed by a substantially more capable local
model.

## Frozen Reused Population And Scorer Boundary

The experiment reuses byte-for-byte the completed Experiment 001 artifacts:

- full portable trace:
  `.agentsight/experiments/step-0031-agentboard-task-identity/agentboard-full.trace.json`,
  SHA-256
  `f02ffbe334c067a2325504f33068f585872f2dbf71a4fcd97c536c1482eb4a81`;
- nine-row connectivity trace:
  `.agentsight/experiments/step-0031-agentboard-task-identity/agentboard-preflight.trace.json`;
- scorer manifest:
  `.agentsight/experiments/step-0031-agentboard-task-identity/scorer-manifest.json`,
  SHA-256
  `59a584e9e6ac8139e6f314065345136afa450bfbb03fe2e569642ba88fef63d2`.

Population remains all 1,012 source-ordered rows. Predictor input remains only
the natural-language `goal`. Official task, filename, ID, subgoals,
difficulty, and additional fields remain scorer-only. No row is sampled,
filtered, deduplicated, trained on, supplied as an example, or used for prompt
selection. Unknown public-data exposure during foundation pretraining remains
an explicit limitation.

## Single Changed Variable

| Component | Experiment 001 | Experiment 002 |
|---|---|---|
| Model | Qwen2.5-3B-Instruct Q4_K_M | Qwen3.6-27B Q4_K_M |
| AgentProf Rust path | shared raw + declared path | unchanged |
| Nine labels/descriptions | fixed approved values | byte-identical |
| Prompt and system instruction | fixed approved values | byte-identical |
| Enumerated grammar | fixed approved values | byte-identical |
| Temperature/output budget | 0 / 8 tokens | unchanged |
| Input/scorer/population | complete AgentBoard | byte-identical |
| Cache | disabled | disabled |
| Repetitions | 3 | 3 |

Candidate model artifact:

- path:
  `/home/yunwei37/workspace/models/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf`;
- size: 17,984,872,960 bytes;
- SHA-256:
  `8739a0cbb80036e5dbdced2085f142b8ba86e3235db8b8039b3769fe5fc70843`;
- runtime: llama.cpp server version 9870 (`2d973636e`), GPU offload,
  Jinja chat template, reasoning disabled.

No AgentProf source change is permitted for Experiment 002. It exercises the
same release Rust binary and product fields already tested in Experiment 001.

## Fixed Declared Taxonomy

The exact same emitted tags and descriptions are passed in the same order:

1. `alfworld=embodied household-object tasks`
2. `babyai=grid-world instruction and navigation tasks`
3. `jericho=interactive text-adventure game tasks`
4. `pddl=symbolic condition-satisfaction planning tasks`
5. `scienceworld=interactive science-environment tasks`
6. `toolop=tasks that operate on an application through tools`
7. `toolquery=tasks that answer a query through information tools`
8. `webbrowse=website browsing and interaction tasks`
9. `webshop=product search and shopping tasks`

These are fixed project-authored operational glosses of official AgentBoard
families, not per-row annotations. No description may change after plan
approval.

## Comparisons And Metrics

Candidate: Qwen3.6-27B declared `task_tag` from the first complete repetition.

Controls/context:

- fixed majority `webshop` control, recomputed on the same manifest;
- completed Qwen2.5-3B Experiment 001 result as a backend context row; and
- Qwen3.6-27B raw open-vocabulary exact match as context, not a fair generic
  classifier baseline.

Primary outcome: nine-class macro-F1. Secondary outcomes: micro accuracy,
per-family precision/recall/F1, complete confusion matrix, three-call exact
stability, grammar validity, and coverage.

The hypothesis is supported only if the 27B candidate:

- scores all 1,012 rows;
- reaches macro-F1 at least 0.80;
- reaches micro accuracy at least 0.80;
- exceeds the majority control on both metrics; and
- produces 3,036/3,036 grammar-valid declared outputs.

No threshold, family exclusion, alias, label merge, prompt, model setting, or
prediction cleanup is selected from observed answers. Stability and per-family
results scope a positive answer but do not replace either absolute accuracy
bar.

## Real Preflight And Complete Run

After independent plan approval:

1. Start the existing llama.cpp server on a dedicated port with the exact 27B
   artifact, `--jinja`, and reasoning disabled.
2. Verify `/v1/models` exposes the expected alias and artifact.
3. Run the unchanged nine-row preflight trace through all raw, declared,
   profile, and JSON paths. It is connectivity evidence only; its labels are
   not scored or used to change the experiment.
4. Run the full trace three times from the start with cache disabled. Each
   repetition must report exactly 1,012 sessions and samples.
5. Stop the server after durable outputs.
6. Use the existing thin scorer only to join stored session IDs to the scorer
   manifest and calculate the already declared metrics.
7. Have a fresh result reviewer independently recompute the registered metrics
   from raw profiles and manifest before any WRITE decision.

The dedicated server command is:

```bash
/home/yunwei37/workspace/llama.cpp-latest/build/bin/llama-server \
  -m /home/yunwei37/workspace/models/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf \
  --alias qwen3.6-27b --host 127.0.0.1 --port 18082 -ngl 99 \
  --ctx-size 4096 --parallel 1 --jinja --reasoning off --reasoning-budget 0
```

The preflight and each full repetition use this unchanged AgentProf shape; only
the input trace and output filename differ between preflight and full runs:

```bash
./agentpprof/target/release/agentpprof \
  --project-root . --project-name agentboard \
  --trace-file .agentsight/experiments/step-0031-agentboard-task-identity/agentboard-full.trace.json \
  --view operations --stack session,task,prompt --format json \
  --output .agentsight/experiments/step-0031-agentboard-task-identity/27b/full-profile-r1.json \
  --include-previews --tagger llm --llama-url http://127.0.0.1:18082 \
  --model qwen3.6-27b --timeout 60 --no-cache \
  --task-choice 'alfworld=embodied household-object tasks' \
  --task-choice 'babyai=grid-world instruction and navigation tasks' \
  --task-choice 'jericho=interactive text-adventure game tasks' \
  --task-choice 'pddl=symbolic condition-satisfaction planning tasks' \
  --task-choice 'scienceworld=interactive science-environment tasks' \
  --task-choice 'toolop=tasks that operate on an application through tools' \
  --task-choice 'toolquery=tasks that answer a query through information tools' \
  --task-choice 'webbrowse=website browsing and interaction tasks' \
  --task-choice 'webshop=product search and shopping tasks'
```

Preflight writes
`.agentsight/experiments/step-0031-agentboard-task-identity/27b/preflight-profile.json`
from `agentboard-preflight.trace.json`. Full repetitions write
`27b/full-profile-r1.json`, `27b/full-profile-r2.json`, and
`27b/full-profile-r3.json`. The existing scorer reads those three named files
plus the unchanged parent `scorer-manifest.json` and writes
`27b/scored-results.json`. These paths are distinct from every Experiment 001
3B artifact and are the only raw inputs to the later result review.

A server or process interruption is repaired and the same fixed repetition is
rerun from the start; partial output is never scored. Any model, prompt,
taxonomy, grammar, product-code, population, visible-field, or metric change
requires returning to plan review.

## Paper And Story Boundary

A passing result may add one concise literal AgentBoard task-family assignment
cell to RQ3 alongside existing independent boundary evidence. It must name the
27B local model and preserve the exact thesis, four RQs, two-object model,
contributions, recurrence algorithm, and all admitted RQ1/RQ2/RQ4 results.

Even a passing result does not establish open-vocabulary semantic-name
adequacy, phase/action literal identity, undeclared-family generalization,
system-effect attribution, or a universal benefit from larger models. A
failing result remains internal experiment history and cannot weaken RQ3,
replace the story, or motivate an easier benchmark.
