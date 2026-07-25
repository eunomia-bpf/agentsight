# Execution log — step 0081 experiment-001 (TraceElephant raw-action skeleton control)

Working directory: repository root
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`

Constraints observed: no git commands; no edits to existing repository files;
all new artifacts written under this experiment directory only.

## Frozen raw-action identity located

Exact identity used by step-0072 Direct+Raw+Evidence (`local_raw_evidence`) on
TraceElephant was reconstructed from:

1. **Raw leaf identity**
   ```text
   .agentsight/experiments/traceelephant-rq2-v1/profiles/method-index.json
   → methods["raw"]["operation_leaves"]
   ```
   - 5960 leaves, one per projection row in file order
   - Composite encoded string over fields
     `system;component;raw_action` (143 unique leaves)
   - **Not** `projection.raw_fields.raw_action` alone (that field is only one
     component of the composite leaf; 5960/5960 rows mismatch the leaf string)

2. **Information-matched path construction** (from
   `script/rq2_current_agent_local_first.py::construct_scores` /
   `load_trace_sources`):
   ```text
   (task_family.casefold(),
    "raw:" + leaf.strip().casefold(),
    *source_evidence_suffix)
   ```
   where `source_evidence_suffix` is the last three frames of
   `groups.source_preserving_agent` after the `automatic_agent` prefix, from:
   ```text
   .agentsight/experiments/rq2-canonical-tags-v2-current/trace/results/fixed-groups.jsonl
   ```

This is the group path used for stage-1/stage-2 skeletons (replacing step 0080's
`source_preserving_agent` semantic path). Documented also in `results.md`.

## Commands

### 1. Harness validation (≤3 queries; not a paper result)

```bash
python3 docs/tmp/build-and-evaluate/step-0081-20260725T012438-0700/experiment-001/raw_action_reader_eval.py \
  validate --workers 1 \
  2>&1 | tee docs/tmp/build-and-evaluate/step-0081-20260725T012438-0700/experiment-001/validate.stdout.log
```

- Wall time: **113.2 s**
- Queries: 3 (sorted query_id order)
- Outcome: all three stage-1 and stage-2 parses OK on first attempt
- Artifact: `validate-summary.json` (explicitly not a paper result)

### 2. Full population run (220 target-bearing queries)

```bash
python3 docs/tmp/build-and-evaluate/step-0081-20260725T012438-0700/experiment-001/raw_action_reader_eval.py \
  full --workers 6 \
  2>&1 | tee docs/tmp/build-and-evaluate/step-0081-20260725T012438-0700/experiment-001/full-run.stdout.log
```

- Harness wall: **2112.4 s** (~35.2 min wall clock with 6 workers)
- Sum of per-query grok walls (stage-1 + stage-2): **12307.26 s**
- Stage-1: 220/220 OK first attempt (0 largest-groups fallbacks)
- Stage-2: 219 OK first attempt, 1 OK after format retry, 0 original-order failures
- Final MAP raw_action_reader = **0.465129**
- Step-0080 profile_reader MAP = **0.455333** (reproduced from stored raw-results)
- Step-0079 direct_reader MAP = **0.501967** (reproduced)
- Mean content-opened fraction = **0.6501**
- Mean raw-action groups / trajectory = **9.82** (vs step 0080 mean **13.70**)
- Mean largest raw-action group size = **9.24**

## Reader CLI (fixed settings, identical to steps 0079–0080)

```text
grok -p <packet+instruction> --output-format plain --max-turns 3 \
  --tools '' --no-subagents --verbatim
# --prompt-file used when prompt exceeds ~100KB ARG_MAX headroom
```

## Bootstrap seeds (paired cluster resamples within strata; 10,000 draws)

| Baseline | Seed |
|---|---:|
| local_only | 20260923 |
| local_agentprof | 20260924 |
| direct_reader | 20260925 |
| profile_reader (step 0080) | 20260926 |

## Deliverables written (this directory only)

| Path | Role |
|---|---|
| `raw_action_reader_eval.py` | complete two-stage harness (copied/adapted from step 0080) |
| `packets-stage1/` | 220 stage-1 raw-action skeleton packets |
| `packets-stage2/` | 220 stage-2 focused-evidence packets |
| `raw-responses/` | 220 per-query response records |
| `raw-results.json` | per-query AP, selections, costs, summary |
| `summary.json` | aggregate MAP / bootstrap / cost / group stats |
| `bootstrap-deltas-vs-*.json` | 10k paired draws vs each baseline |
| `results.md` | reported tables + interpretation + raw-identity provenance |
| `execution-log.md` | this file |
| `validate-summary.json` | ≤3-query harness check (not a paper result) |

## Notes

- The three validation queries were reused from cache during the full run
  (response files already present; not re-queried).
- No existing repository files were modified. No git commands were run.
- Paper submodules and active paper paths were not touched.
