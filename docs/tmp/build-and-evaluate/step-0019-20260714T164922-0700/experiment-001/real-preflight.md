# Real Preflight — R315 Fixed Reader

**Timestamp:** 2026-07-14T17:07:00-07:00
**Attempt:** 1 of at most 2
**Status:** PASS

## Scope

The preflight ran the actual local Qwen3.6-27B endpoint on all five reviewed
cyclic presentations of the real
`satraj_unsafe::operation_stack` R315 packet. It used the production collection
path, visible packet input, model request, response parser, alias mapping, and
raw output path planned for the full run. It did not load the hidden scoring
key and is not scientific evidence.

## Command

```bash
python3 script/r315_llm_reader_eval.py collect \
  --visible-packets docs/visexp/out/analyst-study-protocol-r315/visible-study-packets.json \
  --base-url http://127.0.0.1:8012/v1 --model qwen3.6-27b \
  --out-dir .agentsight/experiments/r315-llm-reader-rq2-v2/preflight \
  --packet-id satraj_unsafe::operation_stack \
  --order-scheme cyclic-5 \
  --temperature 0 --seed 20260714 --max-tokens 1024 --attempts 2
```

## Real Path And Results

- `/v1/models` exposed the exact API ID `qwen3.6-27b` and a 65,536-token
  context for the running Q4_K_M 27B model.
- All five cyclic presentations completed in 20.73 seconds.
- Every presentation succeeded on its first API attempt.
- Every response was a valid JSON object with exactly three distinct in-packet
  aliases and non-empty visible evidence.
- Rotations 0--4 were each present once.
- Every one of the five original visible groups appeared once at each alias
  position `G01` through `G05` across the rotations.
- A direct raw-request scan found zero occurrences of any original group ID.
- The collector constructed model input only from the reviewed allowlist. The
  hidden key was neither an argument nor an imported source in collection.
- Raw request, response, alias map, selected aliases, and selected original IDs
  were preserved in
  `.agentsight/experiments/r315-llm-reader-rq2-v2/preflight/responses.jsonl`.

The five responses selected three different original-group sets across the
rotations, confirming that position balancing is engaged rather than a no-op.
That variation is not interpreted as a result; it only shows why averaging the
five fixed presentations is necessary.

## Decision

The reviewed real endpoint and complete per-packet presentation path run
without repair. REAL PREFLIGHT passes on attempt 1. The full run is authorized
to execute all 66 fixed presentations once, with at most three identical
transport/schema attempts per presentation and no cell dropping or scoring
before collection completes.
