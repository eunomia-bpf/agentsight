# Results Summary: AgentFlame Semantic Effect Profiling

Last updated: 2026-06-14
Stage at update: analyze
Source/command: `cargo run --manifest-path agentflame/Cargo.toml -- run --project-root . --scan-files 10000 --max-sessions 10000 --llama-url http://127.0.0.1:18080 --model local --timeout 60 --out .agentsight/agentflame/latest`
Completeness: partial

## Headline Result

The current strongest evidence is a full local-session characterization over
real AgentSight-related Codex and Claude histories on this machine. AgentFlame
used a real local llama.cpp 3B model to assign one-word tags to session, prompt,
and LLM-call contexts, then folded tool/system behavior into semantic stacks.

The run analyzed 205 readable sessions, 130,632 raw tool events, and 90,930 LLM
events. It produced 167,005 system-effect observations and collapsed them into
24,295 unique semantic system stacks, for a 6.874x compression ratio. Removing
session/prompt semantics causes heavy mixing: nonsemantic stacks mix multiple
semantic regions for 90.219% of observation weight, and flat effect buckets mix
90.770%.

This supports the mechanism claim that semantic frames separate system-effect
regions that ordinary process summaries or nonsemantic folded stacks merge. R110
adds a live in-scope exact-lineage smoke, but the project does not yet prove
native full-run exact file/network lineage or user utility.

## Completed Runs

| Run | Command/config | Result path | Status |
|-----|----------------|-------------|--------|
| R100 | Rust AgentFlame full local repo-related scan, 3B llama.cpp server, `tag_llm_calls=true` | `.agentsight/agentflame/latest/agentflame.json` | done |
| R101 | Rust unit/clippy verification after Unicode and unreadable-session fixes | `cargo test --manifest-path agentflame/Cargo.toml`; `cargo clippy --manifest-path agentflame/Cargo.toml -- -D warnings` | done |
| R110 | Live exact-lineage smoke over real AgentSight DB exports with harness-synthesized agent-run envelopes and llama.cpp root tags | `docs/visexp/out/live-lineage-r110.json` | partial |
| R060 | legacy Python prototype pipeline over sampled sessions | `docs/visexp/out/pipeline-report.json` | legacy, superseded for headline scale |
| R020a | fixture exact-effect lineage checker | `docs/visexp/out/effect-lineage-smoke.json` | partial, fixture only |
| R025 | user-task benchmark packet generation | `docs/visexp/out/user-task-benchmark.json` | protocol only |

## Current Full-Run Metrics

| Metric | Value |
|--------|-------|
| Generated at | 2026-06-14T21:02:43Z |
| Readable sessions analyzed | 205 |
| Source cohorts | `codex=78`, `claude=50`, `claude-subagent=77` |
| Skipped sessions | 1 unreadable root-owned Claude JSONL, recorded in `warnings` |
| Raw tool events | 130,632 |
| Raw LLM events | 90,930 |
| Prompt rows | 2,463 |
| Unique prompt tags | 303 |
| Invalid prompt tags | 0 |
| LLM-call tags | 90,930 |
| Unique LLM-call tags | 1,250 |
| Invalid LLM-call tags | 0 |
| System observations | 167,005 |
| Unique semantic system stacks | 24,295 |
| Semantic system compression | 6.874x |
| Max system stack reuse | 6,004 |
| Nonsemantic mixed buckets | 4,209 |
| Nonsemantic mixed weight | 150,670 / 167,005 = 90.219% |
| Flat mixed buckets | 4,051 |
| Flat mixed weight | 151,590 / 167,005 = 90.770% |

## Tagger Result

| Metric | Value |
|--------|-------|
| LLM backend | llama.cpp HTTP server |
| Model | `qwen2.5-3b-instruct-q4_k_m.gguf` |
| Tag requests | 93,598 |
| Cache hits | 64,297 |
| llama.cpp HTTP calls | 29,302 |
| Successful final tags | 29,301 |
| Final failures | 0 |
| Tag cache entries after run | 29,342 |

The one-call difference between HTTP calls and final successes is consistent
with a retry after one invalid intermediate output; no final tag failed. This is
important for RQ1: syntax validity is strong in the completed run, while
semantic adequacy still needs human labels.

Top prompt tags:

| Tag | Count |
|-----|------:|
| `refactor` | 883 |
| `review` | 408 |
| `docs` | 113 |
| `test` | 112 |
| `analyze` | 108 |
| `design` | 103 |
| `research` | 66 |
| `trace` | 38 |
| `debug` | 20 |
| `validate` | 17 |

Top LLM-call tags:

| Tag | Count |
|-----|------:|
| `refactor` | 40,099 |
| `test` | 8,379 |
| `design` | 7,722 |
| `tokenize` | 7,037 |
| `analyze` | 5,848 |
| `report` | 3,998 |
| `review` | 3,922 |
| `docs` | 3,030 |
| `debug` | 1,609 |
| `build` | 1,262 |

## System-Effect Results

Top flat command/effect rows show why a semantic join is needed:

| Agent | Cohort | Tool | Command | Effect | Status | Count |
|-------|--------|------|---------|--------|--------|------:|
| codex | top | shell | sed | read | ok | 25,755 |
| codex | top | shell | rg | read | ok | 15,336 |
| codex | top | tool | write | process | ok | 12,824 |
| codex | top | shell | git | read | ok | 8,549 |
| codex | top | shell | nl | read | ok | 6,354 |
| codex | top | shell | cargo | test | ok | 2,903 |
| codex | top | shell | python3 | process | ok | 2,880 |
| codex | top | shell | docker | process | ok | 1,561 |

Flat rows reveal heavy behavior, but not why it happened. AgentFlame's semantic
stacks split those rows by session and prompt labels, for example separating
`cargo test` into `review`, `refactor`, `research`, `design`, and `test`
regions.

## Live Exact-Lineage Smoke

R110 moves C4 beyond fixture-only evidence, but only as a scoped smoke. Current
SQLite exports contain process/file/network effects but do not materialize
session/tool ancestry, so `docs/visexp/live_lineage_harness.py` adds a minimal
agent-run envelope around detected Codex/Claude root processes and tags those
roots with the local llama.cpp 3B model. It does not synthesize low-level
effects.

Across three real AgentSight DB exports, the checker covered and joined 182 of
318 raw effects. This is 57.233% raw coverage and 100.0% join within the covered
scope, not 100.0% coverage of all raw effects:

| Run | Roots | Synthetic sessions/tools | Raw effects | In-scope effects | Raw coverage | Joined | Orphans | In-scope join |
|-----|------:|------------------------:|------------:|-----------------:|-------------:|-------:|--------:|--------------:|
| codex-local | 2 | 2 / 2 | 90 | 48 | 53.333% | 48 | 0 | 100.0% |
| codex-attach | 2 | 2 / 2 | 168 | 86 | 51.190% | 86 | 0 | 100.0% |
| debug-ssl-auto | 4 | 4 / 4 | 60 | 48 | 80.000% | 48 | 0 | 100.0% |
| aggregate | 8 | 8 / 8 | 318 | 182 | 57.233% | 182 | 0 | 100.0% |

The aggregate join methods are `related_event_id=8` for root effects and
`pid_family_time_window=174` for descendant process-family effects.

This supports the lineage checker and process-family attribution path for
in-scope live effects. It does not yet prove native AgentSight export because
136 raw effects were outside detected agent roots and session/tool envelopes are
harness-generated.

## Dimension Projection Results

| View | Unique stacks | Total weight | Compression | Max reuse |
|------|--------------:|-------------:|------------:|----------:|
| `semantic-system` | 24,295 | 167,005 | 6.874x | 6,004 |
| `nonsemantic-system` | 10,641 | 167,005 | 15.694x | not primary |
| `prompt-system` | 22,341 | 167,005 | 7.475x | 6,291 |
| `session-system` | 13,328 | 167,005 | 12.530x | 10,130 |
| `semantic-token` | 7,902 | 28,486,605,753,818 | 3,605,492,628.674x | not primary |
| `llm-token` | 2,379 | 28,486,605,753,818 | 11,974,193,255.073x | 25,366,042,700,314 |

Token views are useful for source-local accounting but should not be used for
cross-agent cost claims until token normalization is audited.

## Negative And Mixed Evidence

- C4 exact AgentSight lineage is partial. R110 covers 57.233% of raw live
  effects and validates 100.0% join only within that covered scope; it does not
  prove native collector export of session/tool ancestry.
- C5 user utility remains unsupported. Task packets and scoring scripts exist,
  but no real participant responses have been collected.
- C6 semantic adequacy is partial. The grammar is strong, but labels such as
  `agentsightsm`, `testcodex`, and `bashoutput` show that one-word tags need
  human adequacy measurement and possibly prompt repair.
- One root-owned Claude session could not be read. The run records this as a
  warning rather than claiming perfect trace coverage.

## Result Files Used

- `.agentsight/agentflame/latest/agentflame.json`
- `.agentsight/agentflame/latest/tags.json`
- `.agentsight/agentflame/latest/semantic-system.folded.txt`
- `.agentsight/agentflame/latest/nonsemantic-system.folded.txt`
- `.agentsight/agentflame/latest/session-system.folded.txt`
- `.agentsight/agentflame/latest/prompt-system.folded.txt`
- `.agentsight/agentflame/latest/llm-token.folded.txt`
- `docs/visexp/out/effect-lineage-smoke.json` for fixture checker status
- `docs/visexp/out/live-lineage-r110.json` for live in-scope C4 smoke status
