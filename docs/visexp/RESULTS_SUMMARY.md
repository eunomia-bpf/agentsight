# Results Summary: Semantic Tag Flamegraphs

Last updated: 2026-06-14
Stage at update: analyze
Source/command: `python3 docs/visexp/run_pipeline.py --out docs/visexp/out`
Completeness: partial

## Headline Result

The current local artifact is a reproducible prototype over real Codex and
Claude session histories for this repository. The one-command pipeline completed
8 steps in 86.606 seconds and produced semantic flamegraphs, dimension
projections, tag-stability smoke results, C5 task packets, C6 fixture lineage
checks, evaluation summaries, and verifier output.

The strongest supported result is not user utility yet. It is artifact-level
partitioning: semantic stack frames separate session/prompt regions that
ordinary folded stacks and flat process/effect summaries merge. In the current
run, nonsemantic buckets mix 68.505% of observation weight and flat effect
buckets mix 74.473% of observation weight.

## Completed Runs

| Run | Command/config | Result path | Status |
|-----|----------------|-------------|--------|
| R060 | `python3 docs/visexp/run_pipeline.py --out docs/visexp/out` | `docs/visexp/out/pipeline-report.json` | done |
| R001 | semantic flamegraphs over local sessions, default local Qwen GGUF if available | `docs/visexp/out/aggregation.json` | done |
| R020a | fixture exact-effect lineage checker | `docs/visexp/out/effect-lineage-smoke.json` | done |
| R010 | tag stability smoke over 24 fragments, 2 repeats | `docs/visexp/out/tag-stability-smoke.json` | done |
| R025 | user-task benchmark packet generation | `docs/visexp/out/user-task-benchmark.json` | done |
| R003 | artifact evaluation and claim gates | `docs/visexp/out/evaluation.json` | done |
| R002 | artifact verifier | `docs/visexp/out/pipeline-report.json` | done |

## Current Artifact Metrics

| Metric | Value |
|--------|-------|
| Sessions | 36 |
| Source cohorts | `codex-subagent=12`, `codex=6`, `claude=13`, `claude-subagent=5` |
| Raw tool events | 4031 |
| Expanded system observations | 5312 |
| Unique semantic system stacks | 2270 |
| Collapsed system observations | 3042 |
| Semantic system compression | 2.34x |
| Prompt tags | 38 unique |
| Invalid prompt tags | 0 |
| Same-hash prompt tag conflicts | 0 |
| Generic prompt row share | 35.987% |
| Nonsemantic mixed observation share | 68.505% |
| Flat mixed observation share | 74.473% |
| Fixture-only exact-effect join rate | 100.0% |

## Tagger Result

The one-command run selected `qwen2.5-3b-instruct-q4_k_m.gguf` through
`llama.cpp`. The current run had 3243 tag requests, 3213 cache hits, 30
successful uncached local-model calls, and 0 fallback uses. The model path is
therefore exercised, but the current artifact still has a generic prompt-tag
rate of 35.987% and no manual adequacy labels.

## Dimension Projection Results

| View | Source | Unique stacks | Compression | Max reuse |
|------|--------|---------------|-------------|-----------|
| `prompt-system` | system | 2170 | 2.448x | 81 |
| `session-system` | system | 1603 | 3.314x | 193 |
| `llm-token` | token | 109 | 1456795.55x | 130435313 |
| `prompt-token` | token | 96 | 1654069.948x | 57989935 |
| `session-token` | token | 30 | 5293023.833x | 132357027 |

The system projections show that session tags compress more than prompt tags
because many prompts within a session share command/effect patterns. The token
projections compress heavily because token weights are aggregated rather than
event counts; they are source-local accounting, not a cross-agent cost claim.

## Negative And Mixed Evidence

- C5 remains unsupported. The task packet and scorer exist, but no real
  participant response CSV exists.
- C6 remains unsupported as a live-system claim. The checker passes on a fixture
  with 4/4 joined effects, but no live AgentSight exact-effect capture from real
  sessions has been run through the same checker in this artifact.
- C7 remains partial. Repeated-run smoke stability and grammar checks pass, but
  manual adequacy labels and larger multi-model stability are missing.
- The current parser still uses agent-native session history for the main
  system flamegraph; shell path/domain extraction is conservative and lossy.

## Figure Candidates

- `docs/visexp/paper/figures/fig-model.pdf`: semantic lineage model.
- `docs/visexp/paper/figures/fig-results.pdf`: aggregation, mixing, lineage,
  and generic-tag summary.
- `docs/visexp/paper/figures/fig-dimensions.pdf`: dimension projection
  compression.
- `docs/visexp/paper/figures/fig-flame-excerpt.pdf`: top semantic stack excerpt.

## Result Files Used

- `docs/visexp/out/pipeline-report.json`
- `docs/visexp/out/aggregation.json`
- `docs/visexp/out/evaluation.json`
- `docs/visexp/out/tag-dimensions.json`
- `docs/visexp/out/effect-lineage-smoke.json`
- `docs/visexp/out/tag-stability-smoke.json`
- `docs/visexp/out/user-task-benchmark.json`
