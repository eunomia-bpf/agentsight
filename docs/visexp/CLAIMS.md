# Claim Ledger

This ledger separates what the current `docs/visexp` artifact supports from what
an OSDI/SOSP paper would still need to prove.

## Supported By Current Artifact

### C1: Folded-stack aggregation is implemented.

Evidence:

- `semantic-system.folded.txt` contains repeated stack weights greater than 1.
- `aggregation.json` reports raw tool events, expanded stack observations,
  unique stacks, collapsed observations, and maximum stack reuse.
- `semantic_tag_flamegraph.py` builds `Counter` keys from complete stack frames
  before rendering SVG.
- `verify_artifacts.py` checks folded-line counts and summed weights against
  `aggregation.json`.

Status: supported.

### C2: One-word tags can be inserted into system and token stack grammars.

Evidence:

- `aggregation.json` records the tagger mode, model basename, llama call count,
  llama success count, fallback count, and one-word contract validity.
- `prompt-tags.csv` stores redacted prompt hashes and accepted tags.

Status: supported as a mechanism, not yet as a user-utility result.

### C3: Semantic folded stacks expose repeated behavior not visible in a flat command summary.

Evidence:

- `semantic-system.folded.txt` keeps `session:` and `prompt:` frames.
- `nonsemantic-system.folded.txt` removes those frames.
- `command-summary.csv` is the flat process/tool baseline.
- `evaluation.json` and `semantic-mixing.csv` measure baseline buckets where
  nonsemantic or flat grouping merges multiple session/prompt regions that
  semantic stacks keep separate.

Status: supported as an artifact-level partitioning claim. It still does not
prove user task accuracy or time; that remains C5.

## Diagnostic Only

### C4: Codex and Claude differ on normalized behavior stacks.

Evidence:

- `agent-diff.csv` removes the `agent:` frame, splits top-level and subagent
  cohorts, and reports per-1000-observation rates.

Limitation:

- The current sample is observational and unpaired. Different sessions may have
  different tasks. The result is a diagnostic for where to inspect divergence,
  not a causal or comparative benchmark.

Status: diagnostic only.

### C4b: Token flamegraphs are useful as source-local accounting only.

Evidence:

- Token stacks include `kind:input`, `kind:output`, `kind:cache`, or
  `kind:estimate`.
- `aggregation.json` reports `token_weight_by_kind`.

Limitation:

- The artifact must not be used for cross-agent cost claims until token
  collection is normalized.

Status: diagnostic only.

## Not Yet Supported

### C5: Semantic flamegraphs improve user outcomes over trace trees or process logs.

Needed:

- Head-to-head tasks against raw trace tree, flat process summary, token
  dashboard, nonsemantic folded stacks, and semantic folded stacks.
- Metrics: task time, answer accuracy, repeated-behavior recall, false positives,
  and subjective confidence.

Current partial setup:

- `user-task-benchmark.json` and `user-task-answer-key.csv` define six benchmark
  tasks and deterministic answer keys from the committed artifacts.
- `user-task-participant-packets.json` defines participant-facing condition
  packets without oracle fields or oracle-only sources such as
  `semantic-mixing.csv`.
- `user-task-response-template.csv` defines the response schema for participant
  collection.
- `score_user_task_results.py` scores response CSV files against the hidden
  answer key and reports time, exact accuracy, field accuracy, false positives,
  confidence, parse errors, and per-condition summaries.
- The task bundle is a protocol artifact only; it contains no participant
  responses, task times, or confidence scores.

Status: unsupported as a user-outcome claim. The benchmark and scorer are ready
to pilot, but C5 requires real scored participant responses before it can move
beyond unsupported.

### C6: AgentSight exact system effects preserve the same visualization value.

Needed:

- Replace agent-native tool records with AgentSight's precise
  tool -> shell -> child process -> file/network events.
- Re-run the same folded stack generation and compare stack stability,
  join coverage, and added target/process specificity.

Current partial setup:

- `effect-lineage-smoke.json` validates the checker over an AgentSight-shaped
  fixture with process, file, and network events.
- `effect-lineage.csv` exposes the row-level lineage from event -> process ->
  tool -> session -> prompt tag.
- `effect-lineage.folded.txt` proves the exact-effect stack grammar can collapse
  those joined events.
- The fixture is not evidence that live exact capture has been run on real
  sessions.

Status: unsupported as an exact-effect value claim. The checker is ready; C6
requires live AgentSight exact effects from real sessions to pass the same
lineage checker.

### C7: Tags are stable and semantically adequate across models and reruns.

Needed:

- Manual labels for a representative prompt/session sample.
- Repeated runs across the same 3B model, a smaller local model, and fallback.
- Metrics: one-word contract pass rate, exact-match stability, cluster purity,
  and human adequacy.

Current partial evidence:

- `evaluate_artifacts.py` checks tag grammar, generic-tag share, entropy, and
  same-prompt-hash conflicts inside the committed artifact.
- `tag-stability-smoke.json` runs repeated local annotation over hashed
  session/prompt/LLM fragments. In the current smoke, fallback and llama each
  have 100% exact repeated-run stability and 0 invalid outputs, but their modal
  tags do not match each other. That supports syntax/repeatability only, not
  semantic adequacy.

Status: partial. Current artifacts can detect obvious tag contract failures,
same-hash consistency failures, and small repeated-run instability. They do not
yet prove larger multi-model stability or human adequacy.
