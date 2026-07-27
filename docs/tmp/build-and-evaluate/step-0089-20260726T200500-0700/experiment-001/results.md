# Results: hierarchical vs flat semantic skeleton (one reader family)

## Hypothesis (the review's "why hierarchy" question)

With the reader family held fixed, the HIERARCHICAL semantic skeleton
directs a reader to responsible operations at least as well as a FLAT
skeleton of the same leaf tags, while opening less source content — i.e.,
the nesting itself carries navigation value beyond the names.

## Verdict (arm F2 = corrected flat control): NOT SUPPORTED (flat F2 matches or beats hierarchical on MAP)

**Amendment note.** The flat control was rerun as arm F2 per the binding
step-0089 amendment. Arm F as originally executed grouped by the LAST path
component — the outcome status frame (5 tags: blocked/failure/progress/
success/unclear), an orchestrator spec error. Arm F2 groups by the DEEPEST
SEMANTIC frame: the path component immediately before the fixed three-frame
source-kind/call-tool/outcome suffix (i.e. `source_preserving_agent[-4]`),
the strongest fair flat projection of the same operations. Arm H is NOT
rerun; F2 is paired against the stored arm-H per-query results (same reader
family, flags, jail recipe). Bootstrap seeds: H−F2 = 20261089, H−F2 content = 20261090, H−F(status, superseded) = 20260989/20260990.
The superseded F(status) numbers are retained below, labeled as such.

## Population

- Workload: TraceElephant complete RQ2 collection
- Target-bearing queries scored: 220
- Operations: 5960

## Input provenance (read-only, frozen; reused from step 0080)

- Source-only packets: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/rq2-a0-v1/full/trace/packets`
- Operation projections / stable IDs: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/traceelephant-rq2-v1/operations/projection.jsonl`
- Annotated targets (mistake_step): `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/traceelephant-rq2-v1/scorer/targets.jsonl`
- Stored Direct-only / Direct+AgentProf per-query AP: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/rq2-current-agent-local-first-v1/full/per-query.jsonl`
- Step 0079 direct_reader per-query AP / costs: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001/raw-results.json`
- **Frozen Agent+Evidence group mapping**: `/home/yunwei37/workspace/agentsight-research-semantic-flamegraph/.agentsight/experiments/rq2-canonical-tags-v2-current/trace/results/fixed-groups.jsonl`
  (key `source_preserving_agent`; step-0072 source_preserving_agent paths)
- **Arm F2 grouping key**: `source_preserving_agent[-4]` — the deepest semantic frame; tag-vocabulary size = **42** (population-wide); mean groups/sequence = 8.00, median = 8.0, min = 3, max = 15.
- Arm F(status) grouping key (SUPERSEDED): last path component — 5 tags (blocked, failure, progress, success, unclear).
- Scoring: sklearn non-interpolated `average_precision_score`; arithmetic MAP
- Paired bootstrap: 10,000 resamples of trajectory clusters within strata
  (H−F2 seed 20261089; H−F2 content seed 20261090; H−F(status) seed 20260989/20260990)

## Arms (reader family held fixed)

- **Arm H (hierarchical)**: full source_preserving_agent path grouped by full path (step-0080 style).
- **Arm F2 (flat, corrected control)**: deepest semantic frame only — path component immediately before the fixed three-frame source-kind/call-tool/outcome suffix (path[-4]); parent paths stripped; grouped by that single semantic tag.
- Arm F (flat, SUPERSEDED): SUPERSEDED: last path component (outcome status frame) only; kept for labeled reference, not the authoritative flat control.
- Reader (BOTH arms): `opencode run --pure` from an empty jail, `stdin=/dev/null`, default model glm-5.2, no tools, one format retry, deterministic fallbacks. Same flags / same instruction text for both arms.

## MAP

| Arm / method | MAP |
|---|---:|
| **Arm H — hierarchical** | **0.425965** |
| **Arm F2 — flat (deepest semantic frame, corrected control)** | **0.476832** |
| Arm F — flat (outcome status; SUPERSEDED) | 0.366408 |
| Direct reader (step 0079, reference) | 0.501967 |
| Direct+AgentProf (stored, reference) | 0.325504 |
| Direct-only (stored, reference) | 0.208713 |

## Paired difference (H − F2) — authoritative flat control

| Metric | Point Δ | 95% interval | Nonpositive draws / 10000 |
|---|---:|---:|---:|
| MAP (H − F2) | -0.050867 | [-0.089755, -0.012493] | 9965 |
| content_opened_fraction (H − F2) | -0.203434 | [-0.222855, -0.184075] | 10000 |
| stage2_evidence_chars (H − F2) | -10770.1 | [-12430.9, -9242.6] | 10000 |
| selected_evidence_ops (H − F2) | -7.568 | [-8.736, -6.486] | 10000 |

## Paired difference (H − F status) — SUPERSEDED, retained for continuity

| Metric | Point Δ | 95% interval | Nonpositive draws / 10000 |
|---|---:|---:|---:|
| MAP (H − F status) | +0.059556 | [+0.013879, +0.104702] | 55 |

## Index-hit rate (target operation inside a selected group)

| Arm | Index-hit rate | Hits / 220 | Mean groups | Median groups | Largest group (mean) |
|---|---:|---:|---:|---:|---:|
| H (hierarchical) | 0.6500 | 143 | 13.70 | 12.00 | 6.04 |
| F2 (flat, corrected) | 0.8182 | 180 | 8.00 | 8.00 | 10.85 |
| F (flat, SUPERSEDED) | 0.7455 | 164 | 2.34 | 2.00 | 17.21 |

## Content opened (stage-2 evidence chars / step-0079 full packet chars)

| Arm | Mean opened | Median opened | Mean selected evidence ops |
|---|---:|---:|---:|
| H (hierarchical) | 0.4910 | 0.4970 | 13.16 |
| F2 (flat, corrected) | 0.6945 | 0.7116 | 20.73 |
| F (flat, SUPERSEDED) | 0.7339 | 0.9077 | 20.27 |

## Failure tally

| Tally | H | F2 | F (SUPERSEDED) |
|---|---:|---:|---:|
| Stage-1 OK first attempt | 215 | 220 | 219 |
| Stage-1 OK after retry | 5 | 0 | 1 |
| Stage-1 largest-groups fallback | 0 | 0 | 0 |
| Stage-2 OK first attempt | 213 | 216 | 218 |
| Stage-2 OK after retry | 5 | 0 | 0 |
| Stage-2 original-order failures | 2 | 4 | 2 |

## Cost (per query)

| Metric | H | F2 | F (SUPERSEDED) | Direct reader (0079) |
|---|---:|---:|---:|---:|
| Mean total chars | 44704.7 | 44542.5 | 43161.3 | 44589.2 |
| Median total chars | 37039.0 | 35660.0 | 34684.0 | — |
| Mean wall seconds | 65.22 | 59.90 | 51.01 | 29.88 |
| Median wall seconds | 53.05 | 48.11 | 42.95 | 25.68 |
| Mean prompt tokens (o200k) | 13624 | 13052 | 13062 | — |

## F2 tag vocabulary (population-wide)

Grouping key = `source_preserving_agent[-4]` (deepest semantic frame, immediately before the source-kind/call-tool/outcome suffix). Unique tags = **42**.

Top tags by operation count: `search work external` (568), `inspect artifact` (519), `navigate evidence alternate` (420), `inspect evidence` (397), `validate evidence` (353), `report evidence` (333), `verify target alternate` (302), `read evidence alternate` (275), `edit change` (197), `execute artifact` (187).

## Honest interpretation

On the complete TraceElephant population (n=220), with the opencode/glm-5.2 reader family held fixed, using the corrected flat control F2 (deepest semantic frame, not the outcome status tag):
- Hierarchical MAP = 0.4260; Flat F2 MAP = 0.4768; superseded F(status) MAP = 0.3664.
- Paired H − F2 ΔMAP = -0.0509, 95% interval [-0.0898, -0.0125], 9965/10000 nonpositive draws.
- Mean content opened: H = 49.1%, F2 = 69.4% of the step-0079 full-trace packet volume.
- Index-hit rate: H = 65.0%, F2 = 81.8%.
- F2 flat tag vocabulary = 42 semantic tags (vs. 5 outcome tags for the superseded F(status) arm).

**Verdict (F2 authoritative): NOT SUPPORTED (flat F2 matches or beats hierarchical on MAP).**

Caveats: F2 is the strongest single-frame flat projection of the same operations (the deepest semantic frame, with 42 tags), but it is still a one-component flat projection — the hierarchical arm keeps the full multi-component path. This measures whether the nesting carries navigation value beyond the single deepest semantic name for THIS reader family and workload. It does not evaluate other readers or other workloads, and it is not pooled with the step-0080 grok-reader result. The superseded F(status) arm grouped by the outcome tag (5 tags) and is retained only for continuity.

This file reports the complete 220-query run. The 40-per-arm pilot is an operational gate (parse-failure rate < 10%), recorded in `execution-log.md`, and is not a paper result.
