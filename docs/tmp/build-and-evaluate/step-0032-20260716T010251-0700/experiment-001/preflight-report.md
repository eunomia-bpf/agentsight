# Real Preflight: Published Literal Action Identity

**Completed:** 2026-07-16T02:02:00-07:00
**State:** **PASS — proceed unchanged to the full population**

## Question

Can the approved path parse official ASE thought/action views, keep category
gold outside model input, invoke the fixed Qwen3.6-27B backend with the exact
eight-value grammar, write durable predictions, and execute the planned
majority/scoring path on one real published row from each action class?

This preflight tests executability only. Its eight class-selected rows are not
a statistical sample, remain in the full run, and cannot change the prompt,
model, taxonomy, source fields, control, population, or metric.

## Fixed runtime and commands

The server is llama.cpp version 9870 (`2d973636e`) with binary SHA-256
`a02cd4c018e0b65dd1dbfcc89db010fbb40359971bc03c697b8133287099b701`.
The fixed Qwen3.6-27B Q4_K_M artifact has SHA-256
`8739a0cbb80036e5dbdced2085f142b8ba86e3235db8b8039b3769fe5fc70843`.

```bash
/home/yunwei37/workspace/llama.cpp-latest/build/bin/llama-server \
  -m /home/yunwei37/workspace/models/qwen3.6-27b-gguf/Qwen_Qwen3.6-27B-Q4_K_M.gguf \
  --alias qwen3.6-27b --host 127.0.0.1 --port 18083 -ngl 99 \
  --ctx-size 4096 --parallel 1 --jinja --reasoning off \
  --reasoning-budget 0 --cache-ram 0 --cache-reuse 0
```

The real model and scorer commands were:

```bash
python3 -B experiment-001/literal_action_identity.py run \
  --inputs .agentsight/experiments/rq3-literal-phase-action-source-v1/ase-action-identity/preflight/visible-inputs.jsonl \
  --output .agentsight/experiments/rq3-literal-phase-action-source-v1/ase-action-identity/preflight/predictions.jsonl \
  --url http://127.0.0.1:18083 --model qwen3.6-27b \
  --timeout 90 --attempts 3

python3 -B experiment-001/literal_action_identity.py score \
  --manifest .agentsight/experiments/rq3-literal-phase-action-source-v1/ase-action-identity/preflight/scorer-manifest.json \
  --predictions .agentsight/experiments/rq3-literal-phase-action-source-v1/ase-action-identity/preflight/predictions.jsonl \
  --output .agentsight/experiments/rq3-literal-phase-action-source-v1/ase-action-identity/preflight/score.json \
  --bootstrap-replicates 0
```

Paths are shown from the repository root; the executed script path included
the full current Step 0032 directory.

## Execution result

- `/v1/models` exposed alias `qwen3.6-27b`, GGUF Q4_K_M, context 4,096, and
  27,320,697,856 parameters.
- The visible preflight file contained exactly eight opaque rows and only
  `row_id`, normalized `source`, and `source_sha256` fields.
- The scorer manifest held one row from each of the eight published classes.
- All 8/8 requests completed on their first attempt in 2.19 seconds total.
- All 8/8 outputs belonged to the exact published grammar and joined one-to-one
  to the scorer manifest.
- The candidate path, majority control, eight-class macro-F1, accuracy,
  per-class metrics, and confusion matrix all executed to terminal output.

The connectivity sample produced macro-F1 0.2708 and accuracy 0.3750 versus
0.0278 and 0.1250 for the fixed `Generate Fix` control. These values have no
scientific role because the scorer intentionally selected one row per class
across only four trajectories. No bootstrap was run and no stability claim was
made.

Observed end-to-end request time implies roughly 12.5 minutes per 2,737-row
repetition and about 25 minutes for the approved two full repetitions, before
scoring.

## Artifact hashes

| Artifact | SHA-256 |
|---|---|
| visible inputs | `c5077a0da63c270c8ba36c135e1e8dce54cc5e1307e0c8f2f0d33d112b857f42` |
| scorer manifest | `0559f962215e0019058441e619146177fe0dbeec13b6ef1d7cc308363d01bbd6` |
| predictions | `ac7a708444daaefd454a5b03d39a218cb4a591d4a8c32fc1d5489f2e395194e3` |
| score | `d4d2482236407a05b4707223c921e5b4681e9ddf050e3bc657f2b9869572efe4` |

## Decision

REAL PREFLIGHT passes. Run two complete repetitions over all 2,737 published
labels using the identical source normalization, prompt, taxonomy, grammar,
model, server settings, and no prediction cache. Do not interpret or tune from
this preflight sample.
