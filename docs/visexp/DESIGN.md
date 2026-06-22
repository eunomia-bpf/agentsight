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
nodes, and audit events. R110 applies the same checker to live in-scope effects
from real AgentSight DB exports after a Python harness adds the missing
agent-run envelope; R111 moves that minimal envelope into native
`collector report export`; R112 persists the envelope into SQLite `sessions` and
`tool_calls` rows on DB copies and verifies persisted-only export.

## Semantic Contract

The semantic layer is deliberately small:

- one lowercase ASCII word per session, prompt, and LLM call;
- no fixed ontology;
- invalid model output is rejected; the Rust run fails if retry cannot produce a
  grammar-valid one-word tag;
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

## Canonical Tag Layer

The one-word tagger remains open vocabulary. It should not be converted into a
fixed taxonomy, because a repository will naturally introduce project-specific
verbs and nouns. However, raw one-word tags need a second, auditable display
layer:

```text
raw_tag -> canonical_tag -> optional parent_tag
```

The raw tag is never overwritten. The canonical tag is used only for aggregation
and visualization. R189 implements the first prototype of this layer over the
R170 full-history artifacts. It discovers high-support head tags per dimension
and separates three cases: dictionary aliases, lexical+behavior-profile merges,
and review-only suggestions. Behavior profiles include process histogram, effect
histogram, path buckets, co-occurring session/prompt tags, model/kind for
LLM-call tags, and support counts. Dictionary aliases are explicitly reported as
dictionary decisions; they are not evidence that the behavior-profile model
learned a semantic equivalence. Review suggestions are emitted but not applied.

This matters because labels such as `testcodex`, `docsupdate`,
`paperagentfl`, and `rootpidrefs` may fragment the same user-level task. R189
keeps them visible in `canonical-tag-map-r189.csv` while producing a candidate
canonical view with tags such as `test`, `docs`, `paper`, and `trace`. This is
vocabulary hygiene and tag-noise control, not human semantic adequacy evidence.
R190 then compares raw, alias-only, lexical-only, and profile-guarded variants
and exports a blank audit packet for high-risk over-merge and under-merge rows.
R190-score turns that packet into a two-labeler/adjudication protocol with four
labels: `acceptable`, `overmerge`, `undermerge`, and `unclear`. Its current
output is `human_labels_empty`; a merge-quality claim requires complete paired
labels, adjudicated disagreements, kappa >= 0.6, unclear <= 10%, over-merge <=
10%, and under-merge <= 20%. Until labels exist, it remains a protocol
artifact.

R196 adds a governance loop for the remaining long tail. It does not collapse
all rare tags into `other`. Instead it classifies every raw tag into an
auditable display action:

```text
raw_tag -> existing canonical merge | review merge | regenerate candidate |
           contextual split candidate | keep rare distinct | keep head
```

The rule is intentionally asymmetric. A high-support semantic head such as
`refactor` can be multi-peak across process/path profiles without being a bad
tag; it remains a head tag unless later human tasks show that it harms
navigation. Generic or noisy tags such as `codex`, `ignored`, or `update` are
the ones eligible for regeneration or contextual split. R196 over the R170/R189
artifacts emits 231 existing canonical merges, 114 review-merge rows, 39
regeneration candidates, 2 contextual-split candidates, 1,241 kept rare
distinct tags, and 184 kept head tags. Review-required support is 0.938% for
session tags, 3.258% for prompt tags, and 1.376% for LLM-call tags. This is a
governance mechanism and review packet, not semantic adequacy or merge-quality
evidence.

The operational design should keep semantic compaction as a separate,
versioned layer rather than rewriting labels in place. First, `raw_tag` stays
immutable in every session/prompt/LLM-call record. Second, a versioned
`canonical_tag_map` contains only accepted deterministic aliases and reviewed
merges; changing this map re-renders views but never rewrites source tags.
Third, a `pending_tag_actions` packet contains long-tail candidates with
profile evidence, support counts, proposed action, and reviewer fields. Fourth,
`regenerated_tag` is an optional candidate produced by a small LLM for rows
marked `regenerate_candidate` or `contextual_split_candidate`; it is not a
display label until R203-style paired/adjudicated promotion labels accept it.
Finally, a later reviewed display-map diff is the only artifact allowed to
update `canonical_tag_map`.

This gives each long-tail row an explicit lifecycle:

```text
raw tag -> governance action -> optional regenerated candidate ->
promotion review -> reviewed display-map diff -> canonical view
```

The merge/regenerate decision is level-aware and profile-aware. A text-similar
tag pair is only a safe merge candidate when it appears at the same semantic
level and has compatible process/effect/context profiles. A regenerated tag is
useful only when it shortens or clarifies an overly generic or over-specific
raw tag without hiding distinct system behavior.

This avoids the two common bad outcomes. It does not turn the open-vocabulary
tagger into a fixed taxonomy, which would hide project-specific work. It also
does not let long-tail fragmentation dominate the visualization, because
accepted canonical tags can be used at render time for folded-stack grouping,
while users can still drill down to the raw tags and review packet.

The current thresholds are engineering defaults, not learned constants. R201
therefore adds a sensitivity table over tail-support thresholds, split
thresholds, and the generic/noisy vocabulary: how many tags move between keep,
merge, regenerate, and split; what share of total system weight becomes
review-required; and whether high-support semantic heads remain stable. The
R201 grid keeps review-required support nearly unchanged at 1.926%-1.931%, but
the higher-tail-threshold variant drops baseline-head stability to 65.217%.
This supports a defensible governance mechanism and exposes threshold risk; it
does not make the policy optimized or prove tag adequacy.

R202 exercises the optional regeneration branch with the local llama.cpp server:
all 41 R196 regenerate/contextual-split candidates produce grammar-valid one-word
candidate tags, with 32 changed from the raw tag and 9 unchanged. This proves
the candidate path is executable, but it still does not update the canonical map
or bypass human review. The top-level R202 summary and attempts CSV are the
public-oriented outputs; the nested `r196-with-regeneration/` detail directory
is local-audit-only because it can contain path/profile buckets.

R203 makes the promotion step explicit: promotion is a separate human-gated
protocol, not a side effect of regeneration. It consumes only the
public-oriented R202 attempts CSV, emits a 41-row promotion packet plus two
blank reviewer sheets, and leaves `canonical_map_updated=false` until
paired/adjudicated labels and a separate reviewed display-map diff exist. R193
now packages those R203 sheets with the R124, R190, and R142 human-evidence
materials, while R194/R195 preflight and score the returned R203 sheets without
turning them into C5/C6 evidence.

The full long-tail compaction contract is specified in
`docs/visexp/LONG_TAIL_COMPACTION.md`. That document is now the design source
for the fixed action set, profile-aware merge policy, bounded local-LLM
regeneration packet, human promotion gate, canonical-map versioning rule, and
required metrics such as raw/canonical unique tags, top-K coverage, tail mass,
review-required support, head stability, and promotion acceptance rate.
R205 implements those metrics over the current generated artifacts: raw unique
tag strings 1,546 -> canonical unique tag strings 1,364, top-20 support
coverage 93.683% -> 95.186%, long-tail support 1.746%, and review-required
support 1.926%. It also verifies that R196's canonical overlay is consistent
with R189 for all 1,811 rows, with 0 canonical mismatches. R205 does not update
the canonical map or support adequacy.

R209 turns that policy into renderer-facing data: an active display-map CSV
with one row per R196 raw tag, a drilldown CSV that groups raw tags under active
display labels, and a reviewed-diff CSV that remains empty until R203 labels
exist. The current artifact covers 1,811/1,811 raw rows, exposes 1,509 active
display labels, applies only 63 deterministic alias rows as active display
merges, keeps 168 R189 lexical/profile merges as pending merge candidates,
keeps 41 regenerated tags as candidates, records 0 hidden `other` rows, and
still performs no canonical-map update.

R213 through R218 make the display policy auditable after R209. R213 checks the
raw/display/pending data-layer modes over R209 artifacts, preserving 482,398
support and confirming that drilldown membership matches the active display map.
R214 then turns the same long-tail policy into a control loop: 63 deterministic
aliases are active, 168 profile-merge candidates and 41 regenerated/split
candidates stay pending, 323 rows require review, and the current prompt-review
and high-tail-stability gates fail. It also emits a non-default seven-bucket
rollup preview that partitions all 1,811 raw-tag rows by governance state
without changing membership, plus a regeneration version policy keyed by
`dimension;raw_tag;profile_hash;generator_version`. The current regeneration
branch has 41 grammar-valid candidates but 0 promotable rows without human
promotion labels. R215 compiles the frontend TypeScript
display-mode consumer and runs it under a Node harness, preserving the same
membership and rejecting corrupted drilldown plus candidate-as-active fixtures.
R216 compiles the same module as browser ES modules and runs a headless-browser
DOM harness that clicks raw/display/pending controls, verifies visible counts,
and saves a screenshot plus DOM dump. R217 builds the real Next frontend and
checks that production `AgentFlameView` renders the default display panel from
R209 artifacts. R218 then applies synthetic review fixtures over real R209
pending rows to a preview display-map diff, accepting only final
consensus/adjudicated promotion rows and rejecting unclear, weak, hidden-`other`,
and missing-source rows.
Together these runs prevent automatic long-tail cleanup from silently rewriting
the graph, while still stopping short of visual drilldown, merge-quality,
semantic-adequacy, or user-utility claims.

The long-tail mechanism is therefore a reversible display overlay, not a second
tagger that rewrites history. Normal imports keep raw session/prompt/LLM-call
tags intact. Offline refinement extracts behavior profiles, routes rows to
merge, regenerate, split, or keep actions, and only updates the default
flamegraph after a reviewed display-map diff is accepted. The same folded
weights must be conserved across `raw`, `display`, and `pending` render modes:
compaction may regroup stacks, but it cannot hide effect mass or remove the raw
tag drilldown. This gives the UI a compact default view without turning rare
repository-specific labels into an opaque `other` bucket.

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
R110 adds live in-scope smoke evidence over three real DB exports using
`live_lineage_harness.py`. R111 moves the envelope into native export. The
denominator is split intentionally: 182/318 raw effects joined, while 136 raw
effects remain orphaned. R112 persists the same envelope into SQLite and exports
with observed projection disabled. This is enough to prove DB-persisted backfill
rows can carry session/tool ancestry, but not enough to claim complete
capture-time exact provenance.

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

The exact-effect checker currently has fixture evidence, R110 harness evidence,
R111 native-export smoke evidence, R112 DB-persisted backfill evidence, R113
capture-time record-command row evidence, and R113-live real Codex task
evidence. It proves that the join rules and stack grammar can connect detected
agent-root process families to prompt/session ancestry when the process family
or capture-time root PID is preserved. R113-live shows that root-pid propagation
recovers short-lived helper processes whose intermediate fork nodes do not
appear as process nodes. For in-scope live AgentSight events, an unjoined
process/file/network effect is a collector or join bug, not an acceptable
"unknown prompt" category.

The local model is invoked once per uncached tag, so this is a reproducible
offline experiment, not a collector hot-path architecture. The current full run
already uses a resident `llama-server`; a production path should add batching and
periodic cache flush for recovery.

Some one-word tags remain noisy or over-specific. The research claim should
evaluate tag stability, adequacy, and canonicalization separately from
flamegraph aggregation.

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
- canonicalization: whether a raw open-vocabulary tag layer can be consolidated
  into a smaller auditable display vocabulary without mutating raw tags;
- exact-effect lineage: live AgentSight process/file/network effects all join to
  session/tool/prompt ancestry, preserve the same stack grammar, and add
  actionable target/process specificity.
