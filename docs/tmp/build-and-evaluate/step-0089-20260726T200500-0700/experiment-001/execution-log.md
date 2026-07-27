# Execution log — step 0089 experiment-001 (hierarchical vs flat semantic skeleton)

Timestamp: 2026-07-26T20:05:00-07:00 (step entry); run completed 2026-07-26.

Working directory: repository root
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`

Constraints observed: no git commands; no edits to existing repository files; no
writes outside this experiment directory; `docs/agentpprof-paper/` and
`docs/paper/` untouched.

## Scientific question (fixed; do not change)

With the reader family held fixed, does the HIERARCHICAL semantic skeleton
direct a reader to responsible operations at least as well as a FLAT skeleton
of the same leaf tags, while opening less source content — i.e., does the
nesting itself carry navigation value beyond the names?

## What was reused from step 0080 (frozen, read-only)

Identical frozen TraceElephant inputs and provenance (no new groups invented):

- Source-only packets: `.agentsight/experiments/rq2-a0-v1/full/trace/packets`
  (220 sessions / 5960 operations).
- Operation projections / stable IDs:
  `.agentsight/experiments/traceelephant-rq2-v1/operations/projection.jsonl`.
- Annotated targets (`mistake_step`):
  `.agentsight/experiments/traceelephant-rq2-v1/scorer/targets.jsonl`.
- Stored Direct-only / Direct+AgentProf per-query AP:
  `.agentsight/experiments/rq2-current-agent-local-first-v1/full/per-query.jsonl`.
- Step 0079 direct_reader per-query AP / costs:
  `docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001/raw-results.json`.
- **Frozen Agent+Evidence group mapping** (step-0072 `source_preserving_agent`
  paths, target-blind):
  `.agentsight/experiments/rq2-canonical-tags-v2-current/trace/results/fixed-groups.jsonl`
  (key `source_preserving_agent`; 5960 ops / 220 sequences).

Reference-MAP invariants reproduced exactly: local_only=0.20871256,
local_agentprof=0.32550421, direct_reader=0.50196672.

## What changed relative to step 0080

- **Reader for BOTH arms** = `opencode run --pure "<prompt>"` (step-0083
  addendum-002 prescriptive recipe), executed via subprocess with
  `cwd=reader-jail` (fresh empty dir), `stdin=/dev/null`, no additional flags,
  default model **glm-5.2** (observed stderr banner `> build · glm-5.2`).
  Every packet instruction ends with the addendum-002 closing sentence
  ("Answer directly in strict JSON only. Do not use any tools…"). One format
  retry per call; FIRST JSON object in stdout parsed (balanced-brace scan,
  ANSI stripped). Reader family is held fixed across arms; it differs from
  step-0080's grok reader and is **not pooled** with it.
- **Arm H (hierarchical)**: stage-1 skeleton = full `source_preserving_agent`
  path grouped by full path (step-0080 style), select ≤5 groups.
- **Arm F (flat)**: stage-1 skeleton = the SAME operations grouped by **leaf
  tag only** (last path component), parent paths stripped, a pure flat tag
  list. Leaf-tag vocabulary = 5 tags
  (`blocked`, `failure`, `progress`, `success`, `unclear`), i.e. the
  operation outcome — the literal leaf of the frozen semantic path. Same
  ≤5-group budget; stage 2 identical to arm H.
- **Score**: sklearn non-interpolated AP → MAP over 220; content-opened
  fraction (stage-2 evidence chars / step-0079 full packet chars); paired
  10,000-draw trajectory-cluster bootstrap **H − F** (seed 20260989);
  content-delta seed 20260990; index-hit rate per arm.
- **PILOT**: 40 queries per arm; operational gate = parse-failure rate < 10%
  (not score-based, since both arms are new conditions).

## Commands

### 0. Recipe sanity (single opencode call from the jail)

```bash
opencode run --pure '...'   # cwd=reader-jail; returned clean JSON in ~4.5s
```

- Confirmed default model `glm-5.2` from the stderr banner.

### 1. Pilot — 40 queries/arm (operational gate; not a paper result)

```bash
python3 docs/tmp/build-and-evaluate/step-0089-20260726T200500-0700/experiment-001/hier_vs_flat_eval.py \
  pilot --workers 6 \
  2>&1 | tee docs/tmp/build-and-evaluate/step-0089-20260726T200500-0700/experiment-001/pilot.stdout.log
```

- Wall: **762.4 s** (~12.7 min) for 80 query-arm combos.
- Parse-failure rate: H = **0.000**, F = **0.000** → **gate PASS**
  (0 largest-groups fallbacks, 0 original-order failures either arm).
- Stage-1: H 36/40 OK first attempt + 4 after retry; F 40/40 OK first attempt.
- Stage-2: 40/40 OK (no original-order failures) both arms.
- Artifact: `pilot-summary.json` (explicitly not a paper result).

### 2. Full population run — 220 queries/arm (sequential arms with resume)

```bash
python3 docs/tmp/build-and-evaluate/step-0089-20260726T200500-0700/experiment-001/hier_vs_flat_eval.py \
  full --workers 6 \
  2>&1 | tee docs/tmp/build-and-evaluate/step-0089-20260726T200500-0700/experiment-001/full-run.stdout.log
```

- Harness wall: **3862.2 s** (~64.4 min; 6 workers; sequential H then F).
- Reused the 40 cached pilot responses per arm (resume; no re-call).
- New reader calls: 180/arm (360 total).
- Stage-1: H 215 OK first + 5 after retry, 0 fallbacks; F 219 OK first + 1
  after retry, 0 fallbacks.
- Stage-2: H 213 OK first + 5 after retry, 2 original-order failures;
  F 218 OK first, 2 original-order failures. (All 4 failures tallied and
  scored as original-order per the frozen protocol.)
- argv-fallback (`bash -c cat prompt.txt`) never triggered: max stage-2
  prompt = 161,754 bytes < 900,000-byte threshold and well under ARG_MAX.
- Final: MAP **H = 0.425965**, **F = 0.366408** (ΔMAP H−F = +0.059556);
  mean content opened H = 0.4910, F = 0.7339.

## Reader CLI (fixed settings, identical for both arms)

```text
opencode run --pure "<instruction + JSON packet + closing sentence>"
# cwd = <this experiment-001>/reader-jail  (empty)
# stdin = /dev/null
# default model: glm-5.2  (no -m/--agent/--format flags; addendum-002 forbids them)
# parser: FIRST JSON object in stdout; one format retry; deterministic fallbacks
```

## Packet / no-leak audit (post-run)

- Stage-1 packets: no `source_summary`; only task text, operation IDs/ordinals,
  semantic paths (full for H, leaf tag for F), and group memberships.
- Stage-2 packets: `source_summary` appears **only** under
  `selected_evidence[*]` (members of selected groups); never under `operations`
  or `groups`.
- No `mistake_step` / `is_target` / `ground_truth` keys anywhere. The
  substrings "target"/"answer" that appear are legitimate content: "target" is
  the frozen semantic-path component `"verify target alternate"` (H); "answer"
  is inside the allowed stage-2 `source_summary` source text (F).
- `reader-jail/` is empty after the run (no stray files).

## Deliverables written (this directory only)

| Path | Role |
|---|---|
| `hier_vs_flat_eval.py` | complete two-arm two-stage harness |
| `packets-H-stage1/`, `packets-H-stage2/` | 220 hierarchical skeleton packets each |
| `packets-F-stage1/`, `packets-F-stage2/` | 220 flat (leaf-tag) skeleton packets each |
| `raw-responses-H/`, `raw-responses-F/` | 220 per-query response records each |
| `raw-results.json` | per-query AP (H, F, refs), selections, costs, index-hit |
| `summary.json` | aggregate MAP / paired bootstrap / cost / group stats |
| `bootstrap-deltas-H-minus-F.json` | 10k paired H−F MAP draws |
| `bootstrap-content-delta-*.json` | 10k content-efficiency draws |
| `results.md` | verdict + tables + honest interpretation |
| `execution-log.md` | this file |
| `pilot-summary.json` | 40/arm operational gate (not a paper result) |

## Result summary (complete population, n=220)

- MAP: **H (hierarchical) 0.4260 > F (flat) 0.3664**.
- Paired H − F ΔMAP = **+0.0596**, 95% interval **[+0.0139, +0.1047]**,
  55/10000 nonpositive draws → hierarchical ranks responsible operations
  significantly better, not merely "at least as well".
- Content opened: **H 49.1% < F 73.4%** of the step-0079 full-trace packet
  (Δ = −0.243, 95% [−0.274, −0.210], 10000/10000 nonpositive) → hierarchical
  opens materially less source content.
- Index-hit rate: H 65.0%, F 74.5% (flat selects fewer, larger groups and so
  covers more operations by construction, but at ~1.5× the content cost).
- **Hypothesis verdict: SUPPORTED** — the nesting carries navigation value
  beyond the leaf names for this reader family and workload.

## Caveats

- The flat arm's leaf tag is the operation outcome
  (success/progress/failure/blocked/unclear) — the literal last component of
  the frozen `source_preserving_agent` path. Arm F is therefore a deliberately
  coarse flat projection of the same operations; the experiment does not
  evaluate other flat projections (e.g., a mid-depth prefix), other readers,
  or other workloads.
- Reader model is opencode/glm-5.2 (differs from step-0080's grok); numbers
  here are not pooled with the TraceElephant grok-reader ladder.
- Only the complete 220-query run is reported as a result. The pilot is an
  operational gate and is not a paper result.
