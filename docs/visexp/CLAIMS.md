# Claim Ledger: AgentFlame

Last updated: 2026-06-14
Stage at update: claims
Source/command: `.agentsight/agentflame/latest/agentflame.json`
Completeness: partial

This ledger separates current evidence from OSDI-level claims. The paper should
present AgentFlame as semantic attribution of agent system effects, not as a
generic agent flamegraph.

## Supported By Current Full Run

### C1: AgentFlame generates semantic folded stacks over real local agent histories.

Scope:

- Local AgentSight repository history on this machine.
- Codex and Claude JSONL sessions readable by the current user.
- Agent-native tool/system reconstruction, not live kernel-level exact effects.

Evidence:

- 205 sessions analyzed: `codex=78`, `claude=50`, `claude-subagent=77`.
- 130,632 raw tool events and 90,930 raw LLM events.
- 167,005 system observations collapsed into 24,295 unique semantic system
  stacks.
- Folded totals match summary totals for semantic, nonsemantic, prompt, session,
  and LLM-token projections.
- Dashboard, SVGs, folded stacks, and redacted `agentflame.json` were generated
  under `.agentsight/agentflame/latest`.

Status: supported as a local-history artifact claim.

### C2: Local one-word LLM tagging is syntactically feasible for session, prompt, and LLM-call frames.

Scope:

- 3B Qwen2.5 Instruct Q4_K_M through llama.cpp HTTP.
- Temperature 0, one-word grammar, retry-on-invalid.

Evidence:

- 93,598 tag requests.
- 64,297 cache hits.
- 29,302 llama.cpp HTTP calls.
- 29,301 successful final tags.
- 0 final tag failures.
- 2,463 prompt rows, 303 unique prompt tags, 0 invalid prompt tags.
- 90,930 LLM-call tags, 1,250 unique LLM-call tags, 0 invalid LLM-call tags.

Status: supported for syntax and feasibility; partial for cost and adequacy.

### C3: Semantic frames expose task-effect mixtures hidden by nonsemantic and flat summaries.

Scope:

- Same full local-history workload as C1.
- Mechanism-level information gain, not user-outcome proof.

Evidence:

- Nonsemantic folded stacks, with session/prompt frames removed, produce 4,209
  mixed buckets covering 150,670 observations, 90.219% of system weight.
- Flat effect buckets produce 4,051 mixed buckets covering 151,590 observations,
  90.770% of system weight.
- High-volume examples include `git read`, `cargo test`, `python3 process`,
  `docker process`, and `tool write/process` effects that split across
  `refactor`, `review`, `design`, `research`, `analyze`, and `test` regions.

Status: supported as a partitioning claim.

## Diagnostic Only

### D1: Semantic stacks characterize local Codex/Claude behavior differences.

Evidence:

- Full run includes Codex and Claude/Claude-subagent cohorts.
- Command summary and semantic stacks reveal different tool/effect distributions.

Limitation:

- The histories are observational and unpaired. They are not the same tasks on
  the same repository state. This cannot support a causal "Codex vs Claude"
  benchmark.

Status: diagnostic only.

### D2: Token projections help local accounting.

Evidence:

- `semantic-token`, `session-token`, `prompt-token`, and `llm-token` views are
  generated and total weights match their source totals.

Limitation:

- Codex and Claude token fields are heterogeneous. Some token weights are
  estimates. Token projections should not be used for cross-agent cost claims
  until normalization is audited.

Status: diagnostic only.

## Not Yet Supported

### C4: AgentSight exact system effects preserve semantic attribution value.

Needed:

- Live AgentSight snapshots from real sessions.
- Exact `tool_call -> shell -> child process -> file/network effect` ancestry.
- Join coverage and in-scope orphan-rate metrics.
- Comparison against agent-native proxy stacks.

Current partial setup:

- `docs/visexp/effect_lineage_smoke.py` validates the checker over an
  AgentSight-shaped fixture.
- The full Rust AgentFlame run still uses agent-native session histories.

Status: unsupported as a live exact-effect claim.

### C5: Semantic effect flamegraphs improve developer task outcomes.

Needed:

- Head-to-head task benchmark against trace tree/span flamegraph, flat summary,
  nonsemantic folded stack, and semantic folded stack.
- Metrics: answer accuracy, task time, false positives, confidence, and
  repeated-effect recall.

Current partial setup:

- Legacy `docs/visexp/out` includes task packet and scorer prototypes.
- No real participant responses exist.

Status: unsupported as a user-outcome claim.

### C6: One-word tags are semantically adequate across models and reruns.

Needed:

- 0.6B/1B/3B model comparison over the same fragments.
- Repeated-run stability.
- Human adequacy labels.
- Generic/noisy-tag rate.

Current partial evidence:

- Full 3B run has 0 malformed tags.
- Some noisy tags exist, such as `agentsightsm`, `testcodex`, and
  `bashoutput`.

Status: partial. Syntax is strong; adequacy is unproven.

## Paper Wording Rule

Allowed current wording:

- "AgentFlame can generate semantic folded stacks over real local Codex/Claude
  histories."
- "In our local full-history run, removing semantic frames causes more than 90%
  of system observation weight to fall into mixed semantic buckets."
- "Local one-word tagging is syntactically feasible with a 3B llama.cpp model."

Disallowed current wording:

- "AgentFlame proves developers debug faster."
- "AgentFlame has validated live exact file/network provenance."
- "One-word tags are semantically correct."
- "AgentFlame is the first flamegraph for agents."
