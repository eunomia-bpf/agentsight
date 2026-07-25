# Execution log — step 0080 experiment-001 (TraceElephant profile-guided reader)

Working directory: repository root
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`

Constraints observed: no git commands; no edits to existing repository files;
all new artifacts written under this experiment directory only.

## Frozen group mapping located

Exact path used (step-0072 Agent+Evidence / `source_preserving_agent` on TraceElephant):

```text
.agentsight/experiments/rq2-canonical-tags-v2-current/trace/results/fixed-groups.jsonl
```

- 5960 operations / 220 sequences
- Path key: `source_preserving_agent`
- Provenance matches step-0072 experiment plan
  (`rq2-canonical-tags-v2-current` fixed source-only Agent+Evidence paths)

Also verified sibling artifacts under `rq2-a0-v1/full/trace/results/fixed-groups.jsonl`
(same op IDs; different path strings — not used; step 0072 references the
canonical-tags-v2-current mapping).

## Commands

### 1. Harness validation (≤3 queries; not a paper result)

```bash
python3 docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/experiment-001/profile_reader_eval.py \
  validate --workers 1 \
  2>&1 | tee docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/experiment-001/validate.stdout.log
```

- Wall time: **94.7 s**
- Queries: 3 (sorted query_id order)
- Outcome: all three stage-1 and stage-2 parses OK on first attempt
- Artifact: `validate-summary.json` (explicitly not a paper result)

### 2. Full population run (220 target-bearing queries)

```bash
python3 docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/experiment-001/profile_reader_eval.py \
  full --workers 6 \
  2>&1 | tee docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/experiment-001/full-run.stdout.log
```

- Harness wall: **1853.1 s** (~30.9 min wall clock with 6 workers)
- Sum of per-query grok walls (stage-1 + stage-2): **11047.12 s**
- Stage-1: 220/220 OK first attempt (0 largest-groups fallbacks)
- Stage-2: 219 OK first attempt, 1 OK after format retry, 0 original-order failures
- Final MAP profile_reader = **0.455333**; direct_reader (0079) = **0.501967**
- Mean content-opened fraction = **0.5301**

## Reader CLI (fixed settings, identical to step 0079)

```text
grok -p <packet+instruction> --output-format plain --max-turns 3 \
  --tools '' --no-subagents --verbatim
# --prompt-file used when prompt exceeds ~100KB ARG_MAX headroom
```

## Deliverables written (this directory only)

| Path | Role |
|---|---|
| `profile_reader_eval.py` | complete two-stage harness |
| `packets-stage1/` | 220 stage-1 skeleton packets |
| `packets-stage2/` | 220 stage-2 focused-evidence packets |
| `raw-responses/` | 220 per-query response records |
| `raw-results.json` | per-query AP, selections, costs, summary |
| `summary.json` | aggregate MAP / bootstrap / cost |
| `bootstrap-deltas-vs-*.json` | 10k paired draws vs each baseline |
| `results.md` | reported tables + interpretation |
| `execution-log.md` | this file |
| `validate-summary.json` | ≤3-query harness check (not a paper result) |

## Notes

- Reused the three validate response caches at the start of the full run
  (identical protocol; no force re-call for those three).
- No target / outcome / localizer fields appear in stage-1 or stage-2 packets
  (audited post-run).
- Mean two-stage total packet characters can exceed step-0079 single-packet
  size because stage 2 still carries the skeleton plus selected evidence; the
  primary content-reduction metric is stage-2 evidence chars / step-0079 full
  packet chars (mean 53.0%).
