# Semantic Tag Flamegraph Experiment

This directory contains a runnable experiment for the one-word semantic tag
design. It reads real local Codex and Claude JSONL sessions for this repository,
assigns one lowercase word to each session, user prompt, and LLM call, then emits
folded stacks and static SVG flamegraphs.

See [DESIGN.md](DESIGN.md) for the experiment contract, stack grammar, and
OSDI-facing interpretation. See [CLAIMS.md](CLAIMS.md) for which claims are
currently supported and which still require paired workloads or user studies.
See [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) and
[EXPERIMENT_TRACKER.md](EXPERIMENT_TRACKER.md) for the OSDI-facing evaluation
plan.

The important invariant is aggregation:

```text
project:agentsight;agent:codex;session:design;prompt:flamegraph;tool:shell;cmd:rg;effect:read;path:docs/design;status:ok 7
```

The line above means seven raw tool/effect observations collapsed into one stack.
The SVG is a rendering of the folded stack file, not a per-session trace tree.

## Run

One-command local reproduction, using a local GGUF automatically if the default
`../llama.cpp-latest` paths exist and otherwise falling back to deterministic
tags:

```bash
python3 docs/visexp/run_pipeline.py --out docs/visexp/out
```

Fallback tagger, no model calls:

```bash
python3 docs/visexp/semantic_tag_flamegraph.py --out docs/visexp/out
```

llama.cpp annotation with a local GGUF:

```bash
python3 docs/visexp/semantic_tag_flamegraph.py \
  --model /path/to/model.Q4_K_M.gguf \
  --llama-cli ../llama.cpp-latest/build/bin/llama-cli \
  --llama-limit 200 \
  --out docs/visexp/out
```

The model prompt has a strict contract: return exactly one lowercase English
word. Invalid model output falls back to the deterministic local tagger.

## Outputs

- `out/index.html`: static report page.
- `out/visual-summary.html`: compact visual progress gallery.
- `out/system-flamegraph.svg`: system/tool footprint flamegraph.
- `out/token-flamegraph.svg`: token footprint flamegraph.
- `out/session-system.svg`: system footprint projected by session tag.
- `out/prompt-system.svg`: system footprint projected by prompt tag.
- `out/session-token.svg`: token footprint projected by session tag.
- `out/prompt-token.svg`: token footprint projected by prompt tag.
- `out/llm-token.svg`: token footprint projected by LLM-call tag.
- `out/claim-gates.svg`: current claim-readiness chart.
- `out/semantic-mixing.svg`: semantic aggregation and baseline-mixing chart.
- `out/effect-lineage.svg`: C6 exact-effect lineage readiness chart.
- `out/semantic-system.folded.txt`: collapsed system stacks.
- `out/nonsemantic-system.folded.txt`: baseline folded stacks with session and
  prompt tags removed.
- `out/semantic-token.folded.txt`: collapsed token stacks.
- `out/tag-dimensions.json`: machine-readable summaries for each dimension
  projection.
- `out/tag-dimensions.csv`: compact table for dimension projections.
- `out/pipeline-report.json`: one-command pipeline step report.
- `out/pipeline-summary.md`: human-readable one-command pipeline summary.
- `out/aggregation.json`: proof that raw events were collapsed into fewer
  unique stacks, with repeated stack examples.
- `out/input-manifest.json`: exact argv, selected session hashes, script hash,
  llama.cpp commit when available, and model checksum.
- `out/agent-diff.csv`: Codex-vs-Claude comparison after removing the agent
  frame from each normalized system stack, split by top/subagent cohort and
  normalized per 1000 observations.
- `out/command-summary.csv`: flat process/tool baseline.
- `out/evaluation.json`: artifact-level evaluation of aggregation strength,
  semantic-vs-nonsemantic mixing, tag quality proxies, and claim gates.
- `out/semantic-mixing.csv`: examples where nonsemantic or flat baselines merge
  multiple session/prompt tags that semantic stacks separate.
- `out/claim-gates.csv`: machine-readable claim verdicts for current artifacts.
- `out/evaluation-summary.md`: human-readable artifact audit.
- `out/effect-lineage-smoke.json`: fixture-backed C6 checker summary for
  joining process/file/network events to session/tool/prompt ancestry.
- `out/effect-lineage.csv`: per-event exact-effect lineage rows, including
  orphan reasons for failed joins.
- `out/effect-lineage.folded.txt`: exact-effect folded stack output from the
  lineage checker.
- `out/effect-lineage-summary.md`: human-readable C6 smoke summary.
- `out/tag-stability-smoke.json`: local-only repeated-run tag stability smoke
  summary over hashed session/prompt/LLM fragments.
- `out/tag-stability-smoke.csv`: sanitized per-fragment tag outputs.
- `out/tag-stability-summary.md`: human-readable C7 smoke summary.
- `out/user-task-benchmark.json`: C5 user-task benchmark bundle with sanitized
  tasks and source-view references.
- `out/user-task-answer-key.csv`: machine-readable answer key for the C5 tasks.
- `out/user-task-benchmark.md`: human-readable C5 task bundle summary.
- `out/user-task-participant-packets.json`: participant-facing C5 condition
  packets with no oracle fields.
- `out/user-task-participant-packets.md`: human-readable participant packet
  summary.
- `out/user-task-response-template.csv`: response CSV schema for collecting C5
  participant answers.
- `out/user-task-results.json`: scored C5 participant results after running
  `score_user_task_results.py` on a real response CSV.
- `out/user-task-results.csv`: per-response scored C5 rows.
- `out/user-task-results.md`: human-readable C5 scoring summary.
- `out/prompt-tags.csv`: sanitized prompt hashes, previews, and one-word tags.
- `out/sessions.json`: per-session counts and tag summaries.

## What It Can And Cannot Show

It can show where sessions spend their work semantically, which prompt tags drive
repeated shell/edit/network/tool patterns, how much semantic tags add beyond a
non-semantic folded baseline, and where Codex and Claude differ on normalized
behavior diagnostics.

It cannot yet prove live precise file/network side effects from real sessions.
`effect_lineage_smoke.py` proves the checker and folded-stack grammar over an
AgentSight-shaped fixture, where every in-scope system event must inherit a
session/tool/prompt tag. C6 still requires live AgentSight
tool -> shell -> child process -> file/network events from real sessions.

## Test

```bash
python3 docs/visexp/run_pipeline.py --out docs/visexp/out
python3 -m unittest docs/visexp/test_semantic_tag_flamegraph.py
python3 docs/visexp/effect_lineage_smoke.py --fixture --out docs/visexp/out
python3 docs/visexp/verify_artifacts.py --out docs/visexp/out
python3 docs/visexp/tag_stability_smoke.py --out docs/visexp/out
python3 docs/visexp/user_task_benchmark.py --out docs/visexp/out
python3 docs/visexp/evaluate_artifacts.py --out docs/visexp/out
python3 docs/visexp/visual_summary.py --out docs/visexp/out
```

After collecting real C5 response rows:

```bash
python3 docs/visexp/score_user_task_results.py \
  --responses path/to/responses.csv \
  --out docs/visexp/out
```
