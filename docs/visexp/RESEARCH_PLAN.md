# AgentFlame Research Plan

Last updated: 2026-06-15
Stage at update: supplement / experiment-design plus completed full local-session characterization
Source/command: `cargo run --manifest-path agentflame/Cargo.toml -- run --project-root . --scan-files 10000 --max-sessions 10000 --llama-url http://127.0.0.1:18080 --model local --timeout 60 --out .agentsight/agentflame/latest`
Completeness: partial

## Thesis

AgentFlame's current proven contribution is semantic attribution and
aggregation of AI coding-agent system effects: it joins user-level semantic
intent with system-level provenance and flamegraph-style aggregation. The
stronger claim that this improves developer forensics remains a C5 hypothesis
until participant evidence exists.

```text
sessionTag;promptTag;llmcall/tool;process*;effect
```

The paper should not claim novelty as "flamegraphs for agents." Span-duration
flamegraphs already exist for ordinary distributed traces and have been shown
for multi-agent workflows. The claim must be narrower and stronger:

> Existing agent observability shows spans, tools, duration, prompts, costs, or
> logs. It does not directly answer which user-level intent caused which
> process/file/network effects, nor which repeated or heavy effects are
> semantically the same or different across sessions.

## Paper Type

- Type: systems-for-ML observability and measurement tooling.
- Target venue: OSDI/SOSP-style systems venue.
- Artifact status: Rust CLI prototype over real local Codex/Claude session
  histories; AgentSight exact-effect integration has harness and native-export
  smokes but is not yet the primary full-run input.
- Current maturity: stronger than a workshop demo for characterization and
  artifact-internal claims, but not OSDI weak-accept until live exact lineage and
  user/task benchmarks exist.
- Main reviewer risk: reviewers may see the work as a restyled trace UI unless
  the paper proves semantic attribution plus system provenance answers questions
  that span flamegraphs and flat process summaries cannot answer.

## Closest Baselines And Same-Claim Risk

The related-work risk is real:

- Datadog, SigNoz, New Relic, Honeycomb, Coralogix, Grafana/Pyroscope, and
  Sentry already visualize spans, traces, profiles, and duration-oriented
  flamegraphs.
- Inkeep + SigNoz publicly describes "Flamegraph for Debugging" for multi-agent
  workflows, where each horizontal bar is a span and width is proportional to
  duration. That view exposes sequential/parallel execution, error cascades,
  tool overhead, and sub-agent boundaries.
- LangSmith, Langfuse, Phoenix, and AgentOps expose agent/LLM/tool traces,
  trees, timelines, analytics, prompts, completions, and costs.

Therefore the novelty is not the visual idiom. The defensible novelty is the
specific attribution model and aggregation target:

- Small LLM labels only the semantic control plane: session, prompt, LLM call.
- Deterministic lineage supplies the system plane: tool call, shell, child
  process, file/network effect.
- Folded stacks aggregate repeated task-effect paths across sessions, rather
  than drawing one duration timeline per trace.

Same-claim risk: medium. The individual pieces exist; the combined
`semantic intent -> exact system effect -> aggregated folded stack` model appears
less common and is the paper's best contribution.

## Research Questions

### RQ1. Feasibility And Cost

Can a local small LLM tag all session, prompt, and LLM-call contexts for real
AI coding-agent histories with acceptable syntax validity, runtime, and cache
behavior?

Required evidence:

- Full local history run, not a cherry-picked sample.
- Session, prompt, and LLM-call tag counts.
- Invalid-output count and retry/failure behavior.
- Cache hit rate and uncached local llama.cpp calls.
- Model-size comparison for 0.6B, 1B, and 3B models.

Current evidence:

- Completed full local run on `.agentsight/agentflame/latest`.
- 205 readable repo-related sessions analyzed: `codex=78`, `claude=50`,
  `claude-subagent=77`.
- One unreadable root-owned Claude JSONL was skipped and recorded in
  `warnings`.
- 2,463 prompt rows, 303 unique prompt tags, 0 invalid prompt tags.
- 90,930 LLM events, 1,250 unique LLM-call tags, 0 invalid LLM-call tags.
- 93,598 tag requests, 64,297 cache hits, 29,302 llama.cpp HTTP calls, 29,301
  successful final tags, no final tag failures. The one-call difference is
  consistent with a retry that recovered before final failure.
- R121 started a real local llama.cpp server, repeated three fixed synthetic
  fragments three times each, and produced 9/9 valid 3B tags with 7-41 ms
  request latency after a 1002 ms load. Exact fixed-input stability was mixed:
  2/3 fragments were exact-stable and one coding fragment drifted from
  `refactor` to `test`.
- R122 sampled 300 real redacted fragments from 294 parsed local sessions:
  100 session summaries, 100 prompt fragments, and 100 LLM-call fragments.
- R123 ran the R122 fragment file through the local 3B llama.cpp server with
  3 identical repeats per fragment: 900/900 valid tags, 1002 ms load, p95
  request latency 31 ms, and 285/300 exact-stable fragments.

Remaining gap:

- The full run and B5x benchmark used only a 3B local model. No local 0.6B/1B
  real model GGUF was available. Paper-level C6 still needs human adequacy
  labels over the R122 packet.

### RQ2. Semantic Partitioning Beyond Traditional Tools

Do session and prompt semantic frames separate system-effect buckets that
duration trace trees, span flamegraphs, or flat process/file summaries would
merge, while LLM-call tags remain scoped to token/accounting views?

Required evidence:

- Semantic folded stacks and nonsemantic/flat baselines from the same input.
- Mixed-bucket metrics: count, whole-bucket mixed weight, non-dominant residual
  mixed weight, percent of observation weight, examples.
- Disaggregation examples that answer real developer questions such as "which
  semantic task caused repeated cargo test runs?"

Current evidence:

- 130,632 raw tool events and 90,930 raw LLM events.
- 167,005 system-effect observations collapsed into 24,295 unique semantic
  system stacks; compression ratio 6.874x; max stack reuse 6,004.
- Removing session/prompt frames yields 4,209 mixed nonsemantic buckets covering
  150,670 observations, 90.219% of system weight.
- Flat effect grouping yields 4,051 mixed buckets covering 151,590 observations,
  90.770% of system weight.
- Example mixed baselines include `git read`, `cargo test`, `python3 process`,
  `docker process`, and high-volume `tool write/process` stacks that split into
  different `refactor`, `review`, `design`, `research`, and `analyze` regions.
- R131 ran a semantic-axis ablation over the same folded observations without
  rescanning raw traces. All system and token projection totals were preserved,
  `agentflame.json` totals matched the folded inputs, and projected counters
  exactly matched the already generated nonsemantic/session/prompt folded files.
  For system effects, no-semantic projection mixed 90.219% of full semantic
  bucket weight with 44.639% non-dominant residual weight; session-only left
  84.180% bucket / 34.138% residual; prompt-only left 37.687% bucket / 7.526%
  residual. Full session+prompt semantics leaves 0.000% by construction. This
  isolates the contribution: prompt tags carry most of the system-effect
  separation, while session tags provide the remaining provenance context.

Remaining gap:

- Current metrics prove partitioning, not user benefit. They should support a
  mechanism claim, not the full usability claim.
- R131 also shows a boundary condition: token-accounting projections need the
  session axis. Prompt+LLM-call projection still mixed 95.765% of full
  session/prompt/LLM-call token weight, so LLM-call tags should be claimed as
  token-navigation labels, not as substitutes for session/prompt system-effect
  attribution.

### RQ3. Exact Semantic-Effect Lineage

Can AgentSight's exact provenance chain preserve ancestry from user intent to
tool calls, child processes, and file/network effects with low in-scope orphan
rate?

Required evidence:

- Live AgentSight capture, not only Codex/Claude session history.
- `tool_call -> shell -> process* -> effect` join coverage.
- In-scope orphan rate, path/domain specificity, and redaction checks.
- Comparison of agent-native proxy stacks versus exact-effect stacks.

Current evidence:

- The model and fixture checker exist in `docs/visexp/effect_lineage_smoke.py`.
- Current full run is still agent-native session-history input. It extracts
  commands, status, path groups, and effect classes, but it is not a kernel-level
  exact file/network stream.
- R110 live smoke on three real AgentSight DB exports covers and joins 182/318
  raw effects, for 57.233% raw coverage. Within the covered scope it validates
  182/182 effects with 0 orphans after adding a harness-synthesized agent-run
  envelope and llama.cpp root tags.
- R111 moves the minimal envelope into native `collector report export`; the
  exported snapshots contain 3 sessions/tools and the checker joins the same
  182/318 raw effects, leaving 136 orphans.
- R112 persists the minimal envelope into SQLite `sessions` and `tool_calls`
  tables on DB copies, exports with `--no-observed-projection`, and verifies the
  same 182/318 raw join from persisted-only snapshots.
- R113 implements capture-time `record -- <command>` session/tool rows with
  `view_source=record_capture_time_agent_envelope` and verifies the row shape in
  a temp SQLite DB.
- R113-live runs five real read-only `codex exec` tasks under `agentsight
  record`; all five create capture-time session/tool rows and join 508/508 raw
  effects with 0 orphans.
- R114-smoke runs the new precision suite for one task with wrapper negative
  controls. After `--agent-comm codex` retargeting and scoped oracle accounting,
  it joins 45/45 in-scope effects, reports 0 false positives and 0 false
  negatives, and attributes 0/306 observed negative-control effects. Raw join is
  only 11.392% because wrapper/sibling/out-of-scope effects remain orphaned.
- Full R114 runs 20 real Codex tasks, including read-only, edit, test/debug,
  dependency, failure/retry, and disposable-workspace write tasks. After
  missing-root child fallback and disposable-workspace `--skip-git-repo-check`,
  20/20 targets complete, 20/20 tasks observe negative controls, 1273/1273
  in-scope effects join, precision and recall are both 100.0%, 3170
  negative-control effects are observed with 0 joined, and child-depth/path/
  redaction analysis passes.

Remaining gap:

- The strongest exact-lineage evidence now covers a fixed 20-task command-mode
  suite with negative controls. C4 still should not be stated as a broad
  cross-repo/full-history claim until the artifact covers more repositories,
  agent types, and user-task outcomes.

### RQ4. Developer Utility

Do developers answer forensic questions faster or more accurately with semantic
effect flamegraphs than with trace trees, span-duration flamegraphs, or flat
process/file/network summaries?

Required evidence:

- Task benchmark with preregistered answer key.
- Baselines: raw trace/tree, span-duration flamegraph or comparable trace UI,
  flat process/file/network summary, nonsemantic folded stack, semantic folded
  stack.
- Metrics: accuracy, time, confidence, false positives, repeated-effect recall.

Current evidence:

- R142-packet generated a current pilot packet from R114/R123/R131/full-run artifacts:
  14 questions, 8 primary utility tasks, 6 limitation/comprehension tasks, five
  conditions (`trace-tree`, `span-duration`, `flat-summary`,
  `nonsemantic-stack`, `semantic-stack`), 70 leak-checked blinded participant
  packets, a P01-P05 counterbalanced assignment template, a hidden answer key,
  manifests, a scorer output marked `participant_results_empty`, response
  contract checks, a paper-scale C5 support gate, and per-task
  same-event-slice `slice_id` checks across all five conditions.
- No real participant responses are available.

Remaining gap:

- Without participant responses, the paper can claim improved information
  organization but not improved user outcomes.

### RQ5. Robustness Of One-Word Tags

Are one-word semantic tags stable and adequate enough for navigation across
models, sessions, and prompt distributions?

Required evidence:

- 0.6B/1B/3B local model comparison.
- Repeated-run stability at temperature 0 and at a small nonzero temperature.
- Human adequacy labels over session/prompt/LLM-call fragments.
- Generic-tag and malformed-tag rates.

Current evidence:

- The full 3B run has 0 malformed prompt and LLM-call tags.
- R124-scoring now reads the R122 human-label packet and emits an auditable
  empty result when no labels exist: 300 packet rows, 300 candidate tags, 0
  final labels, `human_labels_empty`, and `adequacy_supported=false`. This
  prepares the gate but does not support adequacy.
- Some tags are clearly useful (`refactor`, `review`, `test`, `analyze`,
  `design`, `research`), but some are noisy or over-specific
  (`agentsightsm`, `testcodex`, `designcodex`, `bashoutput`).

Remaining gap:

- The one-word grammar is solved; semantic adequacy is not solved.

### RQ6. Open-Source Developer Usefulness

Can a community developer run AgentFlame on a local agent-history workspace and
obtain the three paper views without learning the internal experiment harness?

Required evidence:

- Fresh-clone or clean-worktree smoke using documented commands.
- One command that either starts or connects to a llama.cpp-compatible server
  and writes `.agentsight/agentflame/latest`.
- Generated artifacts for the three core views: attribution model evidence,
  semantic flamegraph, and baseline-failure comparison.
- Runtime/resource/cost summary for local use, including cache behavior.
- Artifact hygiene: no committed raw traces, no writes outside the project
  output directory, and explicit warnings for unreadable/skipped traces.

Current evidence:

- The Rust CLI can generate `.agentsight/agentflame/latest/agentflame.json`,
  folded stacks, SVGs, and dashboard artifacts over the local AgentSight
  history.
- `docs/visexp/verify_artifacts.py` checks committed evaluation artifacts, C5
  response-contract fields, R124 tag-adequacy boundaries, and folded totals.
- Raw local traces are not committed. The full run records skipped unreadable
  files instead of requiring elevated privileges.

Remaining gap:

- There is no fresh-clone artifact smoke that a community developer could
  rerun end-to-end with clear expected runtime and outputs. This is not a core
  scientific result, but it is important for turning the research prototype
  into a credible open-source project.

## Claim Ledger Snapshot

| ID | Claim | Current Status | Evidence Needed For OSDI |
|----|-------|----------------|--------------------------|
| C1 | AgentFlame can generate semantic folded stacks and dashboards over real local agent histories. | supported | verifier for full run and reproducibility script |
| C2 | Local one-word LLM tagging is feasible for session/prompt/LLM-call contexts. | supported for 3B syntax/latency; partial for size/adequacy | 0.6B/1B evidence if claimed and adequacy labels |
| C3 | Semantic frames expose task-effect mixtures hidden by nonsemantic and flat summaries. | supported as mechanism | stronger examples and task benchmark |
| C4 | Exact AgentSight lineage connects semantic intent to process/file/network effects. | supported for fixed command-mode suite; partial broadly | cross-repo/full-history exact integration and user-task outcomes |
| C5 | Developers answer debugging/audit questions better with semantic effect flamegraphs. | unsupported; R142 packet/scorer exists | user/task benchmark responses with valid response contract passing the Holm-corrected paper-scale C5 gate |
| C6 | One-word tags are stable and adequate enough for navigation. | partial; R124 scorer exists but labels are empty | human adequacy labels with thresholds and 0.6B/1B evidence if claimed |
| C7 | The approach is practical as an open-source developer tool. | partial | one-command install/run, runtime/cost, docs, artifact hygiene |

## Experiment Matrix

| Block | RQ | Experiment | Baselines/Variants | Metrics | Oracle | Priority |
|-------|----|------------|--------------------|---------|--------|----------|
| B1 | RQ1 | Full local-session characterization | 3B local llama.cpp, cache on/off where feasible | sessions, tags, invalids, runtime, cache hit rate | tag grammar checker and complete report | done, must repeat after changes |
| B2 | RQ2 | Semantic partitioning audit | semantic, nonsemantic, flat process/effect summary | mixed buckets, mixed weight, entropy, examples | deterministic stack comparison | done |
| B3 | RQ3 | Live exact AgentSight lineage | agent-native proxy vs exact effect stream plus negative controls | recall, precision, orphan rate, path/domain specificity | lineage checker with false-positive controls | fixed command-mode suite passed; broader replication should |
| B4 | RQ4 | Developer task benchmark | trace tree, span flamegraph, flat summary, nonsemantic stack, semantic stack | time, accuracy, false positives, confidence | hidden answer key plus preregistered thresholds | packet done; participant run must |
| B5 | RQ5 | Small-model and tag-stability benchmark | 0.6B, 1B, 3B, optional larger reference | latency, invalid rate, identical-input stability, adequacy | repeated run + human labels | must |
| B6 | RQ2 | Ablations | no semantic, session-only, prompt-only, prompt+LLM-call, full | information gain, stack explosion; noisy-tag burden and B4 task accuracy/time deferred | same observations, total-weight equality, report/folded cross-checks | done for C3 mechanism; C6/B4 deferred |
| B7 | RQ6 | Open-source usability smoke | fresh clone, install, run, view dashboard | setup time, commands, failure modes | artifact checklist | should |

## Baseline Fairness

- Span-duration flamegraph baseline should be represented by an OpenTelemetry
  trace flamegraph or faithful local reconstruction: bars/spans ordered by
  timing, width by duration, no semantic inheritance into file/network effects.
- Trace tree baseline should show the same session/tool/LLM-call sequence but no
  cross-session folded aggregation.
- Flat summary baseline should show process/effect/path/domain counts without
  session or prompt tags.
- Nonsemantic folded baseline should preserve stack aggregation but remove
  session/prompt frames. This isolates the contribution of semantic frames from
  flamegraph folding itself.

## Figure Plan

1. Attribution Model: `sessionTag/promptTag/llmcall` generated by small LLM;
   `tool -> process* -> effect` inherited deterministically.
2. Semantic Flamegraph: same `cargo`, `git`, `rg`, or `docker` effects split by
   `refactor`, `review`, `design`, `research`, and `analyze`.
3. Baseline Failure: span-duration trace shows order/duration; flat process
   summary shows heavy commands; neither answers which semantic task caused the
   repeated side effects.
4. Evaluation Table: full-run scale, tag validity, mixing, live lineage join
   coverage, user-task results.

## Next Gate

Current OSDI review posture: weak reject / promising measurement-tooling idea.

The canonical follow-up artifact is `docs/visexp/FOLLOWUP_PLAN.md`. It freezes
the weak-accept gate as four requirements: G1 full-history semantic
characterization, G2 broader live exact lineage, G3 small-model/tag adequacy,
and G4 developer task utility.

The fastest route to weak accept is now a gate-ordered plan:

1. Collect and adjudicate R124 human adequacy labels over the R122 packet. This
   is the smallest remaining local/manual step that can turn C6 from partial
   syntax/stability evidence into adequacy evidence without changing the system.
2. Run a small but real B4x user/task benchmark using the generated R142 answer
   keys and blinded condition packets.
3. Add an R160 fresh-clone/open-source usability smoke for RQ6, after the core
   claims stop moving.
4. Rewrite the paper around "semantic attribution of agent system effects," not
   around "agent flamegraph UI," and keep C5/C6 limitations explicit unless the
   new results pass their gates.
