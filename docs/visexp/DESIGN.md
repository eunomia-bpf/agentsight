# AgentFlame Design

## Question

The experiment asks a narrower question than general agent observability:

> Can one-word semantic labels connect AI-agent session intent to aggregated
> process/file/network behavior that ordinary traces, span flamegraphs, process
> logs, and token dashboards do not connect?

The intended user is not trying to replay a session line by line. They want to
see where an agent is heavy, repetitive, divergent from another agent, or
semantically concentrated.

## Input

The current Rust prototype reads local Codex and Claude JSONL sessions for this
repository.
It extracts:

- session metadata: source, model, cwd, subagent status;
- user prompts: hashed and redacted in committed artifacts;
- LLM calls: model and token usage when available;
- tool calls: shell/read/edit/network/subagent categories, command basename,
  effect class, status, path/domain group when safely inferable.

The current full run is agent-native history, not yet the full live AgentSight
tool -> shell -> child process -> file/network stream. The stack grammar already
has slots for those lower-level effects. `effect_lineage_smoke.py` exercises the
expected AgentSight materialized-view shape with sessions, tool calls, process
nodes, and audit events, and R110 applies the same checker to live in-scope
effects from real AgentSight DB exports after a harness adds the missing
agent-run envelope.

## Semantic Contract

The semantic layer is deliberately small:

- one lowercase ASCII word per session, prompt, and LLM call;
- no fixed ontology;
- invalid model output is rejected; the Rust run fails if retry cannot produce a
  valid one-word tag;
- committed artifacts store only tags, hashes, counts, and redacted prompt rows.

The current full run uses a resident `llama.cpp` HTTP server with
`qwen2.5-3b-instruct-q4_k_m.gguf`. It does not use the legacy deterministic
fallback path. The completed run issued 93,598 tag requests, including 29,302
real llama.cpp HTTP calls and 64,297 cache hits, with 0 final tag failures.

The model does not classify file or network events. The model only names the
session/prompt/LLM context. Exact system events inherit that one-word tag through
structured lineage: tool call ID where available, otherwise process-instance
ancestry, child-process family, and timestamp containment. PID-only matches are
not sufficient because live traces can reuse process IDs.

## Folded Stacks

The system footprint stack is:

```text
project;agent;session;prompt;call:tool/<kind>;process*;effect;path/domain;status
```

The token footprint stack is:

```text
project;agent;session;prompt;call:llm/<tag>;model;kind
```

The exact-effect footprint stack used by the C4 checker is:

```text
project;session-tag;prompt-tag;tool;process;effect;target;status
```

These are collapsed before rendering. If the same path occurs 167 times, the
folded file has one line with weight `167`, not 167 SVG rectangles. This is the
core distinction from a trace tree.

## Views

`system-flamegraph.svg` answers: which semantic prompt/session regions produce
the most repeated system/tool behavior?

`token-flamegraph.svg` answers: which semantic regions consume token mass within
the available source accounting. Token stacks are split by provenance kind:
`input`, `output`, `cache`, and `estimate`. This avoids presenting Claude cache
tokens and Codex estimated response tokens as the same measurement.

`nonsemantic-system.folded.txt` answers: what would remain if the same tool
stream were folded without session and prompt semantics?

`command-summary.csv` answers: what would a traditional flat tool/process
summary show?

`agent-diff.csv` answers: after removing the agent frame and normalizing by
cohort totals, which system stacks are Codex-heavy or Claude-heavy diagnostics?

`agentflame.json` is the current Rust audit receipt. It records input roots,
tagger stats, warnings, per-session redacted summaries, folded-stack summaries,
command/effect summaries, and baseline-mixing examples.

Legacy `docs/visexp/out/aggregation.json` remains useful for the older Python
prototype, but it is no longer the headline evidence.

The Rust full run is checked by parsing `agentflame.json` and verifying folded
totals against `.agentsight/agentflame/latest/*.folded.txt`. The legacy
`verify_artifacts.py` still checks the Python artifact package.

`input-manifest.json` records exact argv, selected session content hashes, script
hash, model checksum, and local llama.cpp provenance where available.

The current OSDI-facing audit is recorded in `RESEARCH_PLAN.md`,
`RESULTS_SUMMARY.md`, `CLAIMS.md`, and `CLAIM_VERDICT.md`. The core metric is
whether nonsemantic or flat baselines merge multiple prompt/session regions that
the semantic stack separates.

`effect_lineage_smoke.py` is the exact-effect join checker. On the committed
fixture it joins every process/file/network event to a process node, tool call,
session, and prompt tag, then writes `effect-lineage.csv` and
`effect-lineage.folded.txt`. Failed joins remain visible with an
`orphan_reason`; the checker does not fall back to out-of-window processes.
R110 adds live in-scope smoke evidence over three real DB exports, but still
uses `live_lineage_harness.py` to synthesize the session/tool envelope because
the current export does not materialize those rows natively.

## What Is New Here

Traditional process tools can tell that `git`, `gh`, `sed`, or `cargo` ran.
Trace UIs can show tool calls in chronological order. Token dashboards can show
which model spent the most.

This experiment joins those observations to one-word semantic labels and exact
lineage, then aggregates across sessions and agents. The useful unit becomes:

```text
paper prompt -> gh process behavior, Claude-heavy
session prompt -> git read behavior, Codex-heavy
debug prompt -> rustc child-process file reads
```

That is not visible from a process list, a span tree, or a token chart alone.

## Current Limits

The path/domain extraction from shell commands is conservative and lossy in the
agent-native artifact. It is only a placeholder for AgentSight's precise
system-effect stream.

The exact-effect checker currently has fixture evidence plus R110 live in-scope
smoke evidence. It proves that the join rules and stack grammar can connect
detected agent-root process families to prompt/session tags, not that native
collector export already preserves complete process/file/network attribution.
For in-scope live AgentSight events, an unjoined process/file/network effect is a
collector or join bug, not an acceptable "unknown prompt" category.

The local model is invoked once per uncached tag, so this is a reproducible
offline experiment, not a collector hot-path architecture. The current full run
already uses a resident `llama-server`; a production path should add batching and
periodic cache flush for recovery.

Some one-word tags remain noisy or over-specific. The research claim should
evaluate tag stability and adequacy separately from flamegraph aggregation.

The behavior diff is a first-order comparison, not a causal claim. It reports
that two agents differ on normalized stack-observation rate; it does not prove
why. Paired workloads are required before making benchmark claims.

The token flamegraph is source-local/proxy accounting. Cross-agent cost claims
require comparable token accounting and should not be made from this artifact.

## Evaluation Hooks

The next OSDI-level evaluation should measure:

- contract validity: accepted tags satisfy the one-word grammar;
- aggregation strength: raw events per unique stack and repeated-stack reuse;
- semantic partitioning: baseline buckets whose mixed prompt/session tags are
  only separable with semantic frames;
- human utility: users find repeated/different behavior faster than with raw
  trace trees, flat process summaries, token dashboards, and non-semantic folded
  baselines;
- stability: tag variance across reruns and small models;
- exact-effect lineage: live AgentSight process/file/network effects all join to
  session/tool/prompt ancestry, preserve the same stack grammar, and add
  actionable target/process specificity.
