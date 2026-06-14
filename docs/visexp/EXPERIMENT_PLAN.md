# Experiment Plan: Semantic Tag Flamegraphs

Last updated: 2026-06-14
Stage at update: experiment-design plus prototype artifact audit
Source/command: `docs/visexp` prototype and generated local session artifacts

## Thesis

One-word local semantic tags are useful for agent observability because they let
users aggregate exact tool/system behavior by task intent, revealing repeated,
heavy, or divergent work that flat process logs, token dashboards, and trace
trees do not join to user requests.

## Paper Type

- Type: systems-for-ML observability and measurement tooling.
- Target venue: OSDI/SOSP-style systems venue.
- Artifact status: prototype over Codex/Claude session history; exact
  AgentSight system-effect input is planned but not yet the source of these
  artifacts.
- Main reviewer risk: the visualization may look like a restyled trace tree
  unless we prove semantic aggregation adds task-level information and improves
  user decisions.

## Claim Ledger

| ID | Claim | Scope | Metric/evidence needed | Status |
|----|-------|-------|------------------------|--------|
| C1 | Folded-stack aggregation is implemented. | Current `docs/visexp` artifacts. | Folded totals, unique stacks, repeated stack weights, verifier. | supported |
| C2 | One-word tags can be inserted into session/prompt/LLM stack frames. | Current local small-model/fallback tag path. | Tag grammar validity, provenance, prompt/session tag coverage. | supported |
| C3 | Semantic stacks add information beyond flat/nonsemantic baselines. | Current real session sample. | Mixed baseline buckets where nonsemantic grouping merges multiple prompt/session tags. | supported by artifact audit |
| C4 | Codex and Claude behavior differs in normalized stack space. | Observational local history. | Agent-normalized diff with top/subagent cohorts. | diagnostic only |
| C5 | Users answer repeated/heavy/divergent behavior questions better with semantic flamegraphs than with trace trees or process logs. | Human or task benchmark. | Time, accuracy, recall, false positives, confidence. | pilot packet and scorer ready; participant results missing |
| C6 | Exact AgentSight process/file/network effects preserve the same visualization value. | Integrated AgentSight effect stream. | Same grammar over exact effects, stack stability, richer path/network attribution. | fixture checker ready; live exact capture missing |
| C7 | Tags are stable and adequate. | Small local LLMs and fallback over representative prompts. | Repeated-run stability, human adequacy labels, generic-tag rate, conflict rate. | partially measured |

## Claim-To-Experiment Map

| Claim | Required evidence | Primary block | Falsifying result | Supported wording if partial |
|-------|-------------------|---------------|-------------------|------------------------------|
| C1 | Collapsed folded stacks with matching verifier totals. | B1 | Folded totals do not match `aggregation.json`, or no repeated stacks exist. | Prototype emits folded stack files but aggregation is weak on this workload. |
| C2 | One-word contract holds and tags are visible in stack grammar. | B1, B4 | Invalid tags appear in committed artifacts or tag provenance is missing. | Tags are syntactically usable but adequacy remains unproven. |
| C3 | Baseline buckets mix multiple prompt/session tags that semantic stacks separate. | B2 | Nonsemantic/flat baselines have no mixed buckets or mixed weight is negligible. | Semantic tags are available but do not add measurable grouping value on this workload. |
| C4 | Normalized cohort diff exists with caveat that samples are unpaired. | B2 | Diff is dominated by unmatched cohorts or missing one agent family. | Use only as inspection diagnostic, not benchmark. |
| C5 | Users solve realistic analysis tasks faster or more accurately. | B3 | Semantic view does not improve accuracy/time/confidence over baselines. | Semantic flamegraphs are an exploratory view, not proven user-value improvement. |
| C6 | Exact system-effect input produces comparable or more actionable stacks. | B6 | In-scope exact effects cannot be joined to prompt/session tags or produce unusable stack explosion. | Checker and stack grammar run on a fixture; current real-session artifact still uses agent-native logs. |
| C7 | Tags are stable enough and semantically adequate. | B4 | Repeated runs disagree heavily or human adequacy is low. | One-word tags are a lossy navigation aid, not a reliable ontology. |

## System-Under-Test Model

- Components: session ingesters, one-word annotator, folded-stack builder, SVG
  renderer, baseline/evaluation scripts.
- Durable state: committed sanitized artifacts under `docs/visexp/out`, tag cache
  excluded from git, and model/manifests recorded by checksum.
- Trust/failure boundaries: local raw session histories are sensitive and are
  not committed; committed artifacts must contain only hashes, tags, counts, and
  redacted previews.
- Consistency/safety/liveness guarantees: no production guarantees are claimed.
  The artifact guarantee is internal consistency between folded files,
  manifests, and summaries.
- Workloads: real local Codex and Claude sessions for the AgentSight repository,
  plus future paired tasks.
- Observability: session/tool/LLM events now; fixture-backed checker for exact
  AgentSight `tool_call -> shell -> child process -> file/network effect`
  lineage; live exact event input still planned.
- Assumptions: each tool event belongs to the active user request in its session
  parser; lower-level effects inherit the prompt/session tag through the
  collector join path.

## Experiment Matrix

| Block | Claim | Experiment | Baselines/variants | Metric(s) | Oracle | Figure/table | Priority |
|-------|-------|------------|--------------------|-----------|--------|--------------|----------|
| B1 | C1,C2 | Artifact consistency and provenance | None | Folded totals, tag validity, manifest hashes | `verify_artifacts.py` passes | Artifact table | must |
| B2 | C3,C4 | Semantic information gain audit | Nonsemantic stack, flat effect summary | Mixed bucket count/share, examples, normalized diff | `evaluate_artifacts.py` claim gates | Fig. semantic-vs-flat | must |
| B3 | C5 | User utility benchmark | Raw trace tree, flat process summary, token dashboard, nonsemantic folded, semantic folded | Time, accuracy, recall, confidence | Preregistered answer key and blinded task order | Main user-study table | must for paper |
| B4 | C2,C7 | Tag stability and adequacy | 3B Q4, smaller local model, fallback | Invalid rate, exact stability, NMI/ARI, human adequacy | Manual labels plus repeated-run agreement | Tag-quality table | must for paper |
| B5 | C4,C5 | Paired agent workload | Codex vs Claude on same tasks | Normalized stack divergence, task outcome, effect volume | Same prompt/task oracle | Agent comparison figure | should |
| B6 | C6 | Exact AgentSight effect integration | Agent-native input vs exact effect input | Stack stability, added path/network specificity, privacy leak rate | Event join checker and redaction verifier | Integration figure | must for paper |

## Experiment Blocks

### B1. Artifact Consistency

- Claim tested: C1 and C2.
- Hypothesis: folded stack files are internally consistent and all committed tags
  satisfy the one-word contract.
- Why this block exists: it prevents a visually plausible SVG from hiding
  accounting errors or prompt leaks.
- Workload: current `docs/visexp/out` generated from real local sessions.
- Compared systems: none.
- Metrics: folded line counts, total weights, tag invalid count, prompt redaction,
  manifest hash match.
- Setup/config: `python3 docs/visexp/verify_artifacts.py --out docs/visexp/out`.
- Run budget: every artifact update.
- Oracle: verifier exits 0.
- Success criterion: all checks pass.
- Failure interpretation: do not use the artifact as evidence.
- Figure/table target: artifact provenance table.
- Reproducibility artifacts: `aggregation.json`, `input-manifest.json`, folded
  files, verifier output.

### B2. Semantic Information Gain Audit

- Claim tested: C3 and observational C4.
- Hypothesis: nonsemantic and flat baselines merge multiple prompt/session
  regions that semantic stacks keep separable.
- Why this block exists: it directly addresses the objection that traditional
  process tools already show the same information.
- Workload: current `docs/visexp/out` generated from real sessions.
- Compared systems: semantic folded stack, nonsemantic folded stack without
  session/prompt frames, flat effect stack without project/agent/session/prompt
  frames, command summary.
- Metrics: mixed baseline buckets, mixed observation weight share, maximum
  semantic variants per baseline bucket, examples, claim-gate verdicts.
- Setup/config: `python3 docs/visexp/evaluate_artifacts.py --out docs/visexp/out`.
- Run budget: every artifact update.
- Oracle: baseline buckets that merge multiple session/prompt tags are listed in
  `semantic-mixing.csv`; C3 gate is supported only if such buckets exist.
- Success criterion: C3 claim gate is supported and examples are auditable.
- Failure interpretation: narrow the claim to "semantic labels are available"
  rather than "semantic labels add non-trivial information."
- Figure/table target: semantic-vs-flat mixing table and example flamegraph.
- Reproducibility artifacts: `evaluation.json`, `semantic-mixing.csv`,
  `claim-gates.csv`, `evaluation-summary.md`.

### B3. User Utility Benchmark

- Claim tested: C5.
- Hypothesis: users find repeated/heavy/divergent behavior faster and with fewer
  false positives using semantic flamegraphs.
- Why this block exists: C5 is the central user-value claim and cannot be proven
  by artifact statistics alone.
- Workload: 12-20 analysis tasks sampled from real sessions, each with a hidden
  answer key derived from exact event/provenance data.
- Compared systems: raw trace tree, flat process summary, token dashboard,
  nonsemantic folded stack, semantic folded stack.
- Metrics: task time, answer accuracy, repeated-behavior recall, false-positive
  rate, confidence, NASA-TLX-lite or short workload score.
- Setup/config: within-subject counterbalanced order; each participant sees each
  task once and each visualization family across matched tasks.
- Run budget: pilot with 4 users; paper run with 12-20 users.
- Oracle: prewritten answer key and blinded grading rubric.
- Success criterion: semantic flamegraph improves accuracy or time on at least
  repeated/heavy/divergent tasks without increasing false positives.
- Failure interpretation: keep semantic flamegraphs as expert exploratory views,
  not as a general usability improvement.
- Figure/table target: task-result table with confidence intervals.
- Reproducibility artifacts: task bundle, answer key, anonymized responses,
  analysis notebook/script.

### B4. Tag Stability And Adequacy

- Claim tested: C2 and C7.
- Hypothesis: one-word tags are stable enough for navigation and adequate enough
  for users to recognize task regions.
- Why this block exists: bad tags can make a correct flamegraph misleading.
- Workload: representative prompt/session/LLM fragments from the real session
  sample, with sensitive text kept local.
- Compared systems: 3B Q4 model, smaller local model, deterministic fallback,
  and optional larger reference model for offline labeling.
- Metrics: one-word invalid rate, exact-match stability, normalized mutual
  information, adjusted Rand index, generic-tag rate, human adequacy score.
- Setup/config: run each annotator 5 times at temperature 0 and once at a small
  nonzero temperature; manually label 100 prompt/session fragments.
- Run budget: smoke with 30 fragments; paper run with 100-200 fragments.
- Oracle: manual labels and repeated-run agreement thresholds.
- Success criterion: invalid rate is 0, same-fragment instability is low, and
  human adequacy median is acceptable for navigation.
- Failure interpretation: use tags only as lossy hints or introduce a constrained
  label repair stage.
- Figure/table target: tag stability/adequacy table.
- Reproducibility artifacts: local-only raw fragment IDs, sanitized label table,
  repeated-run outputs.

### B5. Paired Agent Workload

- Claim tested: C4 and part of C5.
- Hypothesis: semantic stack differences isolate real agent strategy differences
  when tasks are paired.
- Why this block exists: observational Codex-vs-Claude history is confounded by
  different user requests.
- Workload: fixed task suite over the same repository state.
- Compared systems: Codex and Claude, same prompts, same repo snapshot, same
  tool/effect collector.
- Metrics: normalized stack divergence, task success, effect volume, repeated
  command/path/domain patterns.
- Setup/config: 10-20 tasks, at least 3 repetitions per agent where feasible.
- Run budget: paper run after exact effect integration.
- Oracle: task-specific correctness checks and event collector invariants.
- Success criterion: differences remain visible after pairing and normalization.
- Failure interpretation: keep agent diff as a local diagnostic, not a benchmark.
- Figure/table target: paired-agent divergence figure.
- Reproducibility artifacts: prompts, repo snapshot, event traces, result table.

### B6. Exact AgentSight Effect Integration

- Claim tested: C6.
- Hypothesis: replacing agent-native tool records with exact system effects keeps
  the same semantic stack grammar while adding precise process/file/network
  attribution.
- Why this block exists: the paper's unique systems contribution depends on the
  exact effect chain, not just session JSON parsing.
- Workload: sessions run under AgentSight collection.
- Compared systems: agent-native effect proxy versus exact AgentSight effect
  stream.
- Metrics: join coverage, unjoined in-scope event rate, stack stability, added
  path/domain/process specificity, privacy redaction failures.
- Setup/config: run selected sessions with collector enabled; inherit semantic
  tags by prompt/tool_call ID.
- Run budget: smoke with 3 sessions; paper run with paired benchmark sessions.
- Oracle: collector join checker proves each in-scope child process/file/network
  event has a tool_call and prompt ancestry. Any unjoined in-scope event fails
  the gate and is treated as a collector or join bug.
- Success criterion: high join coverage and no committed sensitive text.
- Failure interpretation: scope the prototype to session-native observability.
- Figure/table target: exact-effect lineage figure and orphan-rate table.
- Reproducibility artifacts: sanitized exact-effect folded stacks, join report,
  redaction verifier.

## Run Order

| Run ID | Stage | Purpose | Config | Seed/reps | Decision gate | Cost | Risk |
|--------|-------|---------|--------|-----------|---------------|------|------|
| R001 | sanity | Generate current real-session artifacts. | `semantic_tag_flamegraph.py --model ... --llama-limit 60 --out docs/visexp/out` | deterministic cache/model provenance | Artifacts written and redacted. | local CPU | raw session privacy |
| R002 | sanity | Verify accounting and redaction. | `verify_artifacts.py --out docs/visexp/out` | 1 run per artifact update | Exit 0. | low | verifier blind spots |
| R003 | sanity | Audit semantic partitioning against flat/nonsemantic baselines. | `evaluate_artifacts.py --out docs/visexp/out` | 1 run per artifact update | C3 gate supported or claim narrowed. | low | proxy metric overclaims |
| R010 | decision | Run tag stability smoke. | B4 smoke, 30 fragments, 3 reruns | 3 repeats | Low same-fragment conflict and invalid rate 0. | medium | raw fragment handling |
| R020a | sanity | Run exact-effect lineage fixture checker. | `effect_lineage_smoke.py --fixture --out docs/visexp/out` | 1 deterministic fixture | 100% fixture join rate and folded exact-effect stacks exist. | low | fixture representativeness |
| R020 | decision | Run live exact effect smoke. | B6 smoke, 3 sessions | 3 sessions | Join report has zero in-scope orphan events. | medium | collector integration |
| R025 | sanity | Generate C5 task bundle, answer key, participant condition packets, and response template. | `user_task_benchmark.py --out docs/visexp/out` | 1 deterministic run | Six tasks, answer key, oracle-free participant packets, and response template exist. | low | task validity |
| R026 | sanity | Verify C5 scorer pipeline. | `python3 -m unittest docs/visexp/test_semantic_tag_flamegraph.py` | unit fixture | Scorer detects exact answers, mismatches, extra fields, and per-condition summaries. | low | scoring metric validity |
| R030 | main | Run user utility pilot. | B3 pilot, 4 users | counterbalanced | Detect task/instrument issues. | medium | participant availability |
| R040 | main | Run paired agent benchmark. | B5, fixed tasks | 3 reps/task/agent | Task success and stack divergence recorded. | high | cost and tool parity |
| R050 | paper | Final user utility run. | B3 paper run | 12-20 users | C5 supported or narrowed. | high | human-study variance |

## Tracker Handoff

- Update path: `docs/visexp/EXPERIMENT_TRACKER.md`
- Result path convention: `docs/visexp/out/<run-id>-<artifact>.*` for future
  noncommitted raw results, with sanitized summaries committed when safe.
- Required tracker columns: Run ID, Claim, Block, Purpose, Command/config,
  Commit, Machine, Seed/reps, Oracle, Decision gate, Result path, Status.
- Next rows to add: R020 live exact effect smoke, R030 user utility pilot, and
  R050 final user utility run after the pilot.

## Baseline Fairness

- Named baselines: flat command summary, nonsemantic folded stack, token
  flamegraph, raw trace tree/session timeline, and exact process/file/network
  effect table once integrated.
- Tuning policy: every baseline receives the same input sessions and redaction
  constraints; only semantic stack variants receive session/prompt/LLM tags.
- What each baseline proves: flat command/process summaries test the "ordinary
  tools already show it" objection; nonsemantic folded stacks test whether
  flamegraph aggregation alone is enough; token dashboards test whether cost
  views answer the same questions; raw trace trees test chronological replay.
- Baselines intentionally omitted and why: production APM tools are omitted until
  exact AgentSight effect traces are available in a compatible format.

## Reproducibility

- Hardware/software versions: recorded in `input-manifest.json` where available;
  future paper runs should record CPU, RAM, OS, Python, llama.cpp commit, model
  checksum, and AgentSight collector version.
- Seeds/repetitions: current generation is deterministic except for selected
  local model output; future tag stability runs repeat each annotator.
- Workload generation: current workload is latest local real sessions selected
  by scan/max-session config; paired benchmark will use fixed prompts and repo
  commits.
- Data/traces: raw sessions stay local; committed artifacts contain redacted
  prompt previews, hashes, tags, counts, checksums, and summaries.
- Scripts/configs: `semantic_tag_flamegraph.py`, `verify_artifacts.py`, and
  `evaluate_artifacts.py`.
- Result file paths: `docs/visexp/out`.

## Residual Uncertainty

- Current artifact audit does not prove user utility, causal agent differences,
  or exact AgentSight effect integration.
- This is acceptable only for a mechanism/provenance prototype claim.
- A paper claim must wait for B3, B4, B5, and B6 or use narrower wording.

## Claim Gate After Results

| Claim | Evidence file(s) | Verdict | Supported wording |
|-------|------------------|---------|-------------------|
| C1 | `aggregation.json`, folded files, verifier output | supported | The prototype emits internally consistent folded stack artifacts. |
| C2 | `prompt-tags.csv`, `aggregation.json`, `claim-gates.csv` | supported | Local one-word tags can populate stack frames with grammar checks. |
| C3 | `evaluation.json`, `semantic-mixing.csv` | supported by current artifact audit | Semantic frames separate prompt/session regions that flat baselines merge. |
| C4 | `agent-diff.csv` | diagnostic | Normalized observational differences identify where to inspect. |
| C5 | `user-task-benchmark.json`, `user-task-answer-key.csv`, `user-task-participant-packets.json`, `user-task-response-template.csv`, `score_user_task_results.py` | unsupported | The pilot packet and scorer are ready, but user utility is not established without real participant results. |
| C6 | `effect-lineage-smoke.json`, `effect-lineage.csv`, `effect-lineage.folded.txt` | unsupported | The lineage checker and exact-effect stack grammar pass on a fixture; live AgentSight exact-effect integration is not established. |
| C7 | `evaluation.json`, `tag-stability-smoke.json` | partial | Current artifacts check syntax, same-hash conflicts, and repeated-run smoke stability; manual adequacy and larger multi-model runs remain future work. |
