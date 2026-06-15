# Results Summary: AgentFlame Semantic Effect Profiling

Last updated: 2026-06-15
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
regions that ordinary process summaries or nonsemantic folded stacks merge.
R131 further isolates which semantic axes matter: with the same system-effect
total preserved, no-semantic stacks mix 90.219% of full semantic weight,
session-only leaves 84.180%, prompt-only leaves 37.687%, and full
session+prompt semantics leaves 0.000% by construction. Its non-dominant
residual mixed weight drops from 44.639% with no semantic axis to 7.526% with
prompt-only. R114 adds fixed-suite live exact
lineage over 20 real Codex tasks with negative controls. The project still does
not prove broad cross-repo/full-history exact file/network lineage or user
utility.

## Completed Runs

| Run | Command/config | Result path | Status |
|-----|----------------|-------------|--------|
| R100 | Rust AgentFlame full local repo-related scan, 3B llama.cpp server, `tag_llm_calls=true` | `.agentsight/agentflame/latest/agentflame.json` | done |
| R101 | Rust unit/clippy verification after Unicode and unreadable-session fixes | `cargo test --manifest-path agentflame/Cargo.toml`; `cargo clippy --manifest-path agentflame/Cargo.toml -- -D warnings` | done |
| R110 | Live exact-lineage smoke over real AgentSight DB exports with harness-synthesized agent-run envelopes and llama.cpp root tags | `docs/visexp/out/live-lineage-r110.json` | partial |
| R111 | Native export exact-lineage smoke over the same real AgentSight DB exports after moving the envelope into `collector report export` | `docs/visexp/out/native-lineage-r111.json` | partial |
| R112 | DB-persisted backfill smoke over copies of the same real DB exports, then persisted-only export with observed projection disabled | `docs/visexp/out/native-lineage-r112.json` | partial |
| R113 | Capture-time `record -- <command>` session/tool envelope implementation smoke | `docs/visexp/out/capture-time-r113.json` | partial |
| R113-live | Five real read-only `codex exec` tasks wrapped with `agentsight record`, then exported and checked for lineage | `docs/visexp/out/live-record-r113.json` | partial |
| R114 | Twenty fixed Codex tasks under `agentsight record` with negative controls and scoped precision/recall analysis | `docs/visexp/out/live-record-r114.json`, `docs/visexp/out/live-record-r114-analysis.json` | done |
| R122 | Redacted human adequacy label packet over 100 session, 100 prompt, and 100 LLM-call fragments | `docs/visexp/out/tag-adequacy-label-packet-r122.json` | packet only |
| R123 | 3B llama.cpp real-fragment stability benchmark over the R122 packet | `docs/visexp/out/model-benchmarks-r123.json` | done |
| R124-scoring | Human tag-adequacy scorer over the current blank R122 packet | `docs/visexp/out/tag-adequacy-results-r124.json` | done/empty |
| R131 | Semantic-axis ablation over the same folded observations | `docs/visexp/out/semantic-ablation-r131.json` | done |
| R141-packet | Superseded deterministic C5 task benchmark draft over R114/R123/R131/full-run artifacts | historical `docs/visexp/out/user-task-benchmark.json` at commit `80fc9fc` | superseded by R142 |
| R142-packet | Same-event-slice C5 task benchmark packet and empty scorer check over R114/R123/R131/full-run artifacts | `docs/visexp/out/user-task-benchmark.json`, `docs/visexp/out/user-task-assignments.csv`, `docs/visexp/out/user-task-results.json` | packet only; no participants |
| R060 | legacy Python prototype pipeline over sampled sessions | `docs/visexp/out/pipeline-report.json` | legacy, superseded for headline scale |
| R020a | fixture exact-effect lineage checker | `docs/visexp/out/effect-lineage-smoke.json` | partial, fixture only |

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

R122/R123 add a real-fragment stability check over the same local trace corpus:
R122 sampled 300 redacted fragments from 294 parsed sessions (100 session, 100
prompt, 100 LLM-call), and R123 ran the local 3B llama.cpp server over those
fragments with three identical repeats each. R123 produced 900/900 valid tags,
285/300 exact-stable fragments (95.000%), p95 request latency 31 ms after a
1002 ms model load, and no committed fragment previews in the benchmark summary.
This supports 3B syntax/latency/stability, but not human adequacy.

R124-scoring adds the missing scorer path for human adequacy labels without
inventing labels. On the current blank R122 packet it reports
`human_labels_empty`, 300 packet rows, 300 candidate tags, 0 final labels, no
adequacy percentage, and `adequacy_supported=false`. This keeps C6 partial while
making the next human-label run mechanically auditable.

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

R111 removes the Python harness from the export path. `collector report export`
now emits export-derived session/tool envelope rows from observed local prompts
and root process events. Running the same checker on the full exported snapshots
gives the same aggregate raw join, but with native exported sessions/tools:

| Run | Sessions | Tool calls | Raw effects | Joined | Orphans | Raw join |
|-----|---------:|-----------:|------------:|-------:|--------:|---------:|
| codex-local | 1 | 1 | 90 | 48 | 42 | 53.333% |
| codex-attach | 1 | 1 | 168 | 86 | 82 | 51.190% |
| debug-ssl-auto | 1 | 1 | 60 | 48 | 12 | 80.000% |
| aggregate | 3 | 3 | 318 | 182 | 136 | 57.233% |

R111 is still partial. It proves that native export can carry the minimal
session/tool ancestry needed by the checker, but it also exposes the remaining
coverage problem: 136 raw effects are still orphaned.

R112 adds a DB persistence smoke. It copies the same three real SQLite DBs,
runs `collector report materialize-observed`, verifies that SQLite contains 3
`sessions` rows and 3 `tool_calls` rows with
`view_source=sqlite_observed_agent_envelope`, and then exports with
`--no-observed-projection` so the snapshot must read persisted DB rows:

| Run | DB session rows | DB tool rows | Raw effects | Joined | Orphans | Raw join |
|-----|----------------:|-------------:|------------:|-------:|--------:|---------:|
| codex-local | 1 | 1 | 90 | 48 | 42 | 53.333% |
| codex-attach | 1 | 1 | 168 | 86 | 82 | 51.190% |
| debug-ssl-auto | 1 | 1 | 60 | 48 | 12 | 80.000% |
| aggregate | 3 | 3 | 318 | 182 | 136 | 57.233% |

R112 improves the artifact boundary from export-derived rows to DB-persisted
backfill rows. It does not improve the C4 verdict because raw join remains
182/318, and the session/tool rows are still produced by explicit backfill
rather than capture-time instrumentation.

R113 adds capture-time instrumentation for the command-recording path. When
`agentsight record -- <command>` starts a target child, the collector now writes
a SQLite `sessions` row and matching `tool_calls` row with
`view_source=record_capture_time_agent_envelope`, `tool_name=agent-run`, and
`related_pid=<target child pid>` before the child is continued. On target exit,
the same row ids are updated with end time, duration, status, and exit code.
The unit smoke verifies 1 session and 1 tool row in a temp SQLite DB. This fixes
the narrow "no capture-time row" objection for command-mode `record`; R113-live
below adds the fresh eBPF rerun.

R113-live adds the missing fresh live rerun. The harness runs five real
read-only `codex exec` tasks in this repository under `agentsight record`, then
exports each SQLite DB and runs the exact-lineage checker:

| Metric | Value |
|--------|------:|
| Codex tasks | 5 |
| Capture-time record sessions/tools | 5 / 5 |
| Process nodes | 243 |
| Raw effects | 508 |
| Joined effects | 508 |
| Orphan effects | 0 |
| Raw join | 100.0% |

All tasks succeeded and all five DBs contained
`record_capture_time_agent_envelope` session/tool rows. The important systems
change is session-scoped root-pid propagation in the capture path: 258 effects
joined through the observed process family, and 250 effects joined through
`root_pid_time_window`, covering short-lived helper processes whose intermediate
fork nodes do not appear as process nodes.

R114 scales this command-mode path to a fixed 20-task Codex suite with negative
controls. The suite includes read-only, edit, test/debug, dependency,
failure/retry, and disposable-workspace write tasks. The analysis scopes recall
to the retargeted agent process family and uses per-task negative-control
bursts to catch over-attribution:

| Metric | Value |
|--------|------:|
| Target tasks completed | 20 / 20 |
| Tasks with observed negative controls | 20 / 20 |
| In-scope effect events | 1,273 |
| Joined in-scope effect events | 1,273 |
| False positives | 0 |
| False negatives | 0 |
| Precision | 100.0% |
| Recall | 100.0% |
| Observed negative-control effects | 3,170 |
| Negative-control effects joined | 0 |
| Raw join | 22.055% |

The raw join stays low by design because wrapper, sibling, and out-of-scope
effects remain orphaned rather than being attributed to the agent. This is the
right evidence for the paper's exact-lineage claim only within the fixed
command-mode suite; it is not yet broad full-history provenance.

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

R131 turns these projections into a mechanism ablation by grouping each
projection against the full semantic key. It checks total-weight equality,
matches `agentflame.json` report totals against folded inputs, and verifies
that generated folded files exactly match the script projections. Mixed bucket
weight counts the whole projected bucket if it contains more than one full
semantic key; residual mixed weight counts only the non-dominant variants
inside such buckets.

| Family | Variant | Total | Unique stacks | Mixed bucket weight | Residual mixed weight |
|--------|---------|------:|--------------:|--------------------:|----------------------:|
| system | no semantic | 167,005 | 10,641 | 90.219% | 44.639% |
| system | session only | 167,005 | 13,328 | 84.180% | 34.138% |
| system | prompt only | 167,005 | 22,341 | 37.687% | 7.526% |
| system | session + prompt | 167,005 | 24,295 | 0.000% | 0.000% |
| token | no semantic | 28,486,605,753,818 | 32 | 100.000% | 34.344% |
| token | prompt + LLM-call | 28,486,605,753,818 | 6,802 | 95.765% | 0.027% |
| token | session + prompt + LLM-call | 28,486,605,753,818 | 7,902 | 0.000% | 0.000% |

The system-effect result supports the paper's mechanism claim: prompt tags
carry most of the system-effect partitioning, while session tags add remaining
provenance context. The full 0.000% rows are construction checks, not
independent evidence of user value. The token result is narrower: LLM-call tags
help token navigation, but they do not replace the session axis for full token
provenance.

## Negative And Mixed Evidence

- C4 exact AgentSight lineage is supported for the fixed command-mode suite but
  partial broadly. R114 joins 1,273/1,273 scoped in-scope effects and rejects
  3,170 observed negative-control effects, but it is still not a full-history
  or cross-repo benchmark.
- C5 user utility remains unsupported. Task packets and scoring scripts exist,
  and R142-packet now provides 14 tasks, 8 primary utility tasks, 6
  limitation/comprehension tasks, 5 conditions, 70 leak-checked blinded packets,
  a P01-P05 assignment template, a hidden answer key, manifests, and an empty
  scorer output with null aggregate metrics. All five condition excerpts for
  each task share one `slice_id`, so the packet clears the same-event-slice
  fairness check. No real participant responses have been collected.
- C6 semantic adequacy is partial. The grammar is strong, but labels such as
  `agentsightsm`, `testcodex`, and `bashoutput` show that one-word tags need
  human adequacy measurement and possibly prompt repair. R124-scoring exists
  and currently records `human_labels_empty`; it is protocol evidence, not
  adequacy evidence.
- R131 is a mechanism ablation, not a usability result. It supports C3 and
  figure design, but not the C5 developer-utility claim.
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
- `docs/visexp/out/native-lineage-r111.json` for native export C4 smoke status
- `docs/visexp/out/native-lineage-r112.json` for DB-persisted backfill C4 smoke status
- `docs/visexp/out/capture-time-r113.json` for capture-time record-command implementation status
- `docs/visexp/out/live-record-r113.json` for fresh live Codex record lineage status
- `docs/visexp/out/live-record-r114.json` and `docs/visexp/out/live-record-r114-analysis.json` for fixed-suite live exact lineage
- `docs/visexp/out/tag-adequacy-label-packet-r122.json` for the redacted adequacy-label packet
- `docs/visexp/out/tag-adequacy-results-r124.json` for the empty human-label scorer gate
- `docs/visexp/out/model-benchmarks-r123.json` for real-fragment stability
- `docs/visexp/out/semantic-ablation-r131.json` for semantic-axis ablation
- `docs/visexp/out/user-task-benchmark.json`, `docs/visexp/out/user-task-participant-packets.json`, `docs/visexp/out/user-task-assignments.csv`, `docs/visexp/out/user-task-manifest.json`, and `docs/visexp/out/user-task-results.json` for the R142-packet C5 benchmark bundle
