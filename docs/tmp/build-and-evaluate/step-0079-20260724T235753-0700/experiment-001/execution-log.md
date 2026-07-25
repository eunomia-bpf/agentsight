# Execution log — step 0079 experiment-001 (TraceElephant direct reader)

Working directory: repository root
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`

Constraints observed: no git commands; no edits to existing repository files;
all new artifacts written under this experiment directory only.

## Commands

### 1. Harness validation (≤3 queries; not a paper result)

```bash
python3 docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001/direct_reader_eval.py \
  validate --workers 1
```

- Wall time: **85.9 s**
- Queries: 3 (sorted query_id order)
- Outcome: all three produced parseable rankings (2 first-attempt OK, 1 OK after format retry)
- Artifact: `validate-summary.json` (explicitly not a paper result)

### 2. Full population run (220 target-bearing queries)

```bash
python3 docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001/direct_reader_eval.py \
  full --workers 6 \
  2>&1 | tee docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001/full-run.stdout.log
```

- Harness wall (first pass): **1067.6 s** (~17.8 min wall clock with 6 workers)
- Sum of per-query grok walls after all retries: **~6574 s** (serial-equivalent model time)
- First pass: 214 OK / 6 ARG_MAX failures on the largest packets when delivered via `-p`

### 3. ARG_MAX recovery for 6 large packets

OS limit (`ARG_MAX` = 2 MiB, shared with environment) rejected
`grok -p <full-prompt>` for the largest SWE/GAIA packets. The harness was updated
to deliver identical prompt bytes via `--prompt-file` when the prompt exceeds
~100 KB, then those six response caches were deleted and the full scorer re-run:

```bash
# deleted only the 6 failure_original_order raw-response JSON files
python3 docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001/direct_reader_eval.py \
  full --workers 3 \
  2>&1 | tee -a .../full-run.stdout.log
```

- Wall: **123.2 s** (mostly cache hits; 5 large packets recovered via `--prompt-file`)
- Remaining failure: 1 query (`magentic-runs-gaia/gaia_task_85_gpt_4o_0ooijiwiru1k`)
  exited with `max turns reached` under `--max-turns 1` while the model tried an
  internal thinking step before emitting JSON.

### 4. Fixed decoding allowance for max-turns

Decoding fixed to `--max-turns 3` (still one CLI invocation per query; not
per-query prompt tuning). Re-ran the single remaining failure and re-scored:

```bash
rm -f .../raw-responses/magentic-runs-gaia_gaia_task_85_gpt_4o_0ooijiwiru1k.json
python3 .../direct_reader_eval.py full --workers 2
```

- Wall: **24.1 s**
- Outcome: that query OK; **0 original-order failures** in the final population

### 5. Final score-only regeneration (cached responses)

```bash
python3 docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001/direct_reader_eval.py \
  score-only --workers 1
```

- Wall: **1.3 s**
- Regenerated `raw-results.json`, `results.md`, `summary.json`, bootstrap draw files

## Reader CLI (fixed settings)

```text
grok -p <packet+instruction> --output-format plain --max-turns 3 \
  --tools '' --no-subagents --verbatim
# when prompt UTF-8 size > 100000 bytes:
grok --prompt-file <same-prompt-bytes> --output-format plain --max-turns 3 \
  --tools '' --no-subagents --verbatim
```

One optional format retry with a fixed reminder string; second failure would score
as original-order ranking (none remained after recovery).

## Inputs (read-only)

| Role | Path |
|---|---|
| Source-only packets (220 sessions) | `.agentsight/experiments/rq2-a0-v1/full/trace/packets/` |
| Operation projections / IDs | `.agentsight/experiments/traceelephant-rq2-v1/operations/projection.jsonl` |
| Annotated targets | `.agentsight/experiments/traceelephant-rq2-v1/scorer/targets.jsonl` |
| Stored Direct-only / Direct+AgentProf AP | `.agentsight/experiments/rq2-current-agent-local-first-v1/full/per-query.jsonl` |

Method name mapping (paper ↔ stored keys):

- Direct-only = `local_only` (MAP 0.208713)
- Direct+AgentProf = `local_agentprof` (MAP 0.325504)

Bootstrap seeds match step 0072 TraceElephant comparisons: `20260923` (vs Direct-only),
`20260924` (vs Direct+AgentProf); 10,000 cluster resamples within 5 strata.

## Final deliverables

| File | Description |
|---|---|
| `direct_reader_eval.py` | Complete harness |
| `packets/` | Exact reader packet per query (220 JSON files) |
| `raw-responses/` | Every raw reader response + parse metadata (220 JSON files) |
| `raw-results.json` | Per-query AP + paired deltas summary |
| `results.md` | Population, provenance, MAP, intervals, cost, interpretation |
| `summary.json` | Compact numeric summary |
| `bootstrap-deltas-vs-local_only.json` | 10k paired MAP-difference draws |
| `bootstrap-deltas-vs-local_agentprof.json` | 10k paired MAP-difference draws |
| `full-run.stdout.log` | Console log of full execution |
| `validate-summary.json` | 3-query harness check only |
| `execution-log.md` | This file |

## Final headline numbers

- Direct-reader MAP: **0.501967**
- Direct-only MAP: **0.208713**
- Direct+AgentProf MAP: **0.325504**
- Reader − Direct-only: **+0.293254** \[+0.236545, +0.349977\]
- Reader − Direct+AgentProf: **+0.176463** \[+0.129582, +0.224071\]
- Failures (original-order fallback): **0**
- Format retries used: **3**
