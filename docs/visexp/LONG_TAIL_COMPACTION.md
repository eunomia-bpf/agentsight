# Long-Tail Semantic Compaction

Last updated: 2026-06-15
Stage at update: design protocol plus R196/R201/R202/R203/R205/R209/R212/R213/R214/R215/R216/R217/R218
mechanism evidence
Completeness: partial; this document defines the mechanism and gates, not a
human-validated adequacy result.

## Problem

AgentFlame intentionally uses an open one-word vocabulary for session, prompt,
and LLM-call tags. That keeps repository-specific intent visible, but it also
creates a long tail: misspellings, overly specific project words, generic words,
and near-duplicates can fragment the same semantic task across many folded
stacks.

The goal of compaction is not to reduce labels at any cost. The goal is to
increase aggregation coverage while preserving the ability to audit every raw
tag and every system effect that flowed into the view.

## Non-Goals

- Do not replace the open vocabulary with a fixed ontology.
- Do not rewrite raw tags in session, prompt, or LLM-call records.
- Do not collapse rare tags into a single `other` bucket by default.
- Do not let a regenerated LLM tag become a display label without review.
- Do not treat syntax-valid, stable, or regenerated labels as human adequacy
  evidence.

## Data Model

The compaction layer is a display-time overlay:

```text
raw_tag -> governance_action -> optional regenerated_tag ->
promotion_review -> reviewed display-map diff -> canonical_tag
```

The raw tag is immutable. The canonical map is versioned. Re-rendering with a
new map can change the default folded view, but it must not mutate raw tags or
raw traces.

There are therefore two labels in the system, not one:

- `raw_tag`: the one-word output attached to a session, prompt, or LLM call.
  This is the auditable semantic observation.
- `display_tag`: the label used by default aggregation and flamegraph
  rendering. It is derived from the current canonical map plus any reviewed
  display-map diff.

Every rendered `display_tag` must have a drilldown back to its contributing
raw tags and support mass. A display label that cannot explain its raw
membership is invalid, even if it makes the flamegraph smaller.

Each candidate row should carry:

- `level`: `session`, `prompt`, or `llm`;
- `raw_tag` and current `canonical_tag`, if any;
- support counts and support mass;
- process/effect/path-domain profile summaries;
- neighboring session/prompt/LLM tags;
- proposed action and action rationale;
- optional regenerated one-word candidate;
- reviewer labels, adjudication status, and map-diff decision.

## Action Set

The action set is fixed even though the tag vocabulary is open:

| Action | Meaning | Default map effect |
|--------|---------|--------------------|
| `keep_head` | Supported semantic head; may span several system profiles. | Keep as canonical. |
| `keep_rare_distinct` | Rare but specific; not worth merging without evidence. | Keep raw tag visible. |
| `auto_canonicalize_existing` | Already accepted alias or reviewed merge. | Use existing canonical map. |
| `review_merge` | Plausible merge that needs human merge-risk review. | Pending; no map update. |
| `regenerate_candidate` | Raw tag is generic/noisy/over-specific enough to ask a small LLM for a better one-word candidate. | Candidate only. |
| `contextual_split_candidate` | Same raw tag appears to cover distinct contexts and may need split labels. | Candidate only. |
| `defer` | Evidence is insufficient or policy is uncertain. | Keep raw tag visible. |

This avoids a hidden `other` bucket. Long-tail rows are either preserved,
reviewed, or proposed for explicit promotion.

## Compaction Loop

Long-tail handling runs as an offline refinement loop over generated semantic
artifacts. It does not run on the critical path for every trace import.

```text
raw semantic artifacts
  -> profile extraction
  -> governance action
  -> candidate merge or regeneration packet
  -> review/promotion gate
  -> versioned display-map diff
  -> re-rendered folded stacks
```

The loop is triggered when the current map is no longer good enough for the
questions users ask. Suggested triggers are:

- long-tail support mass exceeds the configured budget;
- review-required support mass increases after new sessions are imported;
- top-K coverage drops below the paper's reporting threshold;
- a head label loses stability under the R201 sensitivity grid;
- users repeatedly expand the same raw-tail bucket in the UI;
- a new repository or agent family introduces many unknown raw tags.

This makes compaction incremental. A normal user opens an existing compact
view. A maintainer or researcher runs the refinement loop when the view becomes
too fragmented or when an evaluation needs a frozen map version.

The display loop also has a renderer-facing safety rule: pending candidates may
be shown as overlays, warnings, review queues, or drilldown alternatives, but
they must not change the active display membership. R215 compiles the frontend
TypeScript display-mode consumer and rejects negative fixtures where corrupted
drilldown membership or candidate labels are treated as active display rows.
R216 repeats the same contract in a headless-browser DOM harness, and R217
checks that the production React `AgentFlameView` can render the default
display-mode panel from the generated artifacts. R218 then exercises a reviewed
display-map update gate with synthetic review fixtures over real R209 pending
rows. These runs are mechanism smokes, not adequacy, merge-quality, or utility
claims.

## Merge Versus Regenerate

The policy deliberately separates two failure modes.

`review_merge` is for labels that look like aliases of an existing display
task. A merge candidate needs evidence that both labels live at the same level
and have compatible process/effect/path/context profiles. The output is a
merge-risk row, not a new tag.

`regenerate_candidate` is for labels that are generic, noisy, truncated, or too
repository-specific to be useful as a display name. The small LLM sees only a
bounded profile packet and proposes exactly one lowercase ASCII word. The
output is a candidate display name, not an accepted display name.

`contextual_split_candidate` is the opposite of merge: the same raw tag appears
to cover multiple behaviorally distinct tasks. The right output may be several
candidate display tags, but the source raw tag remains visible under each
reviewed split bucket.

The default action for uncertainty is `keep_rare_distinct`. This is important
for research integrity. A rare but meaningful project-specific word can be more
useful than a clean-looking generic label.

## Decision Policy

Compaction is level-aware and profile-aware.

Text similarity alone is insufficient. A merge candidate must be at the same
semantic level and have compatible support profiles over process, effect,
path/domain bucket, and neighboring semantic tags. For example, two tags tied to
`cargo test` and test-output effects are different from two tags tied to
`xelatex` and PDF outputs, even if both contain a failure-like word.

High-support semantic heads should be preserved by default. A tag such as
`refactor` can legitimately touch tests, formatting, file edits, and git reads.
Multi-peak behavior is not automatically evidence that the tag should split.
Generic or noisy tags are better regeneration candidates than broad but
meaningful heads.

The safe default is:

1. Apply only accepted deterministic aliases and reviewed merges to the default
   canonical map.
2. Route lexical/profile near-misses to a merge-risk packet.
3. Route generic, noisy, or over-specific rows to regeneration or contextual
   split review.
4. Keep rare but specific rows visible instead of hiding them in `other`.
5. Promote regenerated candidates only through paired/adjudicated review and a
   separate display-map diff.

## Candidate Construction

Candidate rows should be constructed from semantic and system provenance
together. A text-only embedding cluster is insufficient because it can merge
different user intents that happen to use similar words.

For each `(level, raw_tag)` row, compute a compact profile:

- support: rows, system-effect weight, event count, and token weight when
  available;
- system behavior: top processes, effect classes, path/domain buckets, and
  status distribution;
- semantic neighborhood: co-occurring session, prompt, and LLM-call tags;
- source diversity: agent family, model, subagent flag, and number of sessions;
- stability: whether the row remains a head, tail, or review candidate across
  the R201 threshold grid.

Two rows may become a merge candidate only if their profile distance is below
threshold and neither row is flagged as a likely contextual split. A row may
become a regeneration candidate only if its current label is generic/noisy,
over-specific, or unstable enough that a clearer one-word display name would
reduce fragmentation without hiding behavior.

The scoring output should remain diagnostic rather than authoritative:

```text
candidate_type, proposed_display_tag, support, profile_similarity,
head_stability, review_reason, required_gate
```

The final authority is the promotion gate, not the score.

## Regeneration Prompt Contract

Regeneration should be cheap and local. The small model receives a bounded
profile packet, not the full raw trace:

```json
{
  "level": "prompt",
  "raw_tag": "update",
  "support": 193,
  "current_action": "regenerate_candidate",
  "neighbor_tags": ["paper", "latex", "review"],
  "top_processes": ["xelatex", "python3"],
  "top_effects": ["write", "process", "read"],
  "top_path_buckets": ["docs/visexp/paper", "docs/visexp/out"],
  "known_canonical_tags": ["paper", "test", "trace", "review", "build"]
}
```

The model must return exactly one lowercase ASCII word. Invalid output is
rejected. Valid output is still only a candidate.

The regeneration prompt should not include raw prompts, raw file contents, or
complete traces. It should include only bounded counts, top-k profile strings,
neighboring tags, and known display labels. This keeps the local small-model
path cheap enough for repository-scale offline refinement and reduces the risk
that regenerated labels memorize sensitive session content.

## Promotion Gate

A regenerated tag can enter the default canonical view only when all of the
following are true:

- raw tag and regenerated tag are both present in the promotion packet;
- two independent reviewers label every row or an adjudication sheet resolves
  disagreements;
- `unclear` rows are below the configured threshold;
- accepted rows are exported as a reviewed display-map diff;
- the map version changes only through that diff;
- raw tags remain drill-down-visible in the rendered view.

R203 implements the current empty promotion gate. Its default output has
0 final labels, `long_tail_promotion_review_supported=false`, and
`canonical_map_updated=false`.

## Visualization Behavior

The default flamegraph should use only accepted deterministic aliases and
reviewed display-map diffs because the user's first question is where work is
heavy, repeated, or mixed. The detail panel should show the raw rows under
every active display label:

```text
paper
  raw tags: paper, paperagentfl, docsupdate, latexpaper
  prompts: 27
  system weight: 1813
  top effects: xelatex/process, main.tex/write, figures/read
  map version: canonical-tag-map-r189 + pending R203 diff none
```

The tail view should show review burden rather than hide it:

```text
review required support: 1.926%
regenerate candidates: 39
contextual split candidates: 2
review merge rows: 114
kept rare distinct tags: 1241
```

This lets users use the compact view while still seeing how much unresolved
semantic uncertainty remains.

The renderer should expose at least three modes:

- `raw`: render original one-word tags with no display-map compaction. This is
  the audit baseline.
- `display`: render accepted canonical labels and reviewed display-map diffs.
  This is the default user view.
- `pending`: overlay candidates, review-required mass, and regenerated labels
  without changing stack membership. This is the maintainer/research view.

The flamegraph width semantics must be independent from the compaction mode.
Changing from `raw` to `display` may change stack grouping, but the total
effect weight, token weight, or duration weight for a selected filter must be
conserved.

## Adaptive Control Loop

Long-tail handling should be a budgeted control loop, not a one-time cleanup.
The system should continuously distinguish four cases:

- active deterministic aliases that may change default display membership;
- pending profile merges that look useful but need merge-risk review;
- pending regenerated or split candidates from the small LLM path;
- rare but specific raw tags that should stay visible.

The control loop should report both global and per-level budgets. In the current
R214 artifact, global review-required support is still below the default 2%
budget at 1.926%, but prompt-level review support is 3.258%, so prompt tags
should be prioritized for review before any prompt-level candidate is promoted.
The same run shows that raising tail thresholds would reduce head stability to
65.217%, so threshold changes cannot be automated just to make the graph look
cleaner.

R214 now also separates two user-facing control surfaces that should not be
confused. The default `display` view is the audited membership view. A
non-default rollup preview groups rows only by governance state: preserved
heads, preserved rare tags, active deterministic aliases, pending profile
merges, pending review-only merges, pending LLM regenerations, and pending
contextual splits. This preview exactly partitions all 1,811 raw-tag rows and
482,398 support, but it is not a canonical map and cannot be used as paper
evidence that the grouped tags are semantically equivalent.

Regeneration is likewise versioned rather than destructive. The candidate key
is:

```text
dimension;raw_tag;profile_hash;generator_version
```

Re-running the local model writes a new candidate version. It never overwrites
the raw tag, the existing canonical map, or an accepted display-map version.
The current R202/R214 path has 41 grammar-valid regenerated/split candidates,
32 changed from the raw tag, and 0 rows promotable without R203-style human
promotion labels.

This gives a concrete merge/regeneration policy:

1. Merge active labels only for deterministic aliases or reviewed display-map
   diffs.
2. Ask the small LLM to regenerate only bounded profile packets, not raw traces
   or full prompts.
3. Keep generated labels candidate-only until paired/adjudicated review.
4. Keep rare distinct tags visible instead of hiding them in `other`.
5. Fail the control gate when review mass, head instability, hidden `other`
   buckets, or drilldown mismatch exceed budget.

The output is not a new raw ontology. It is a reversible display policy whose
default state can be compact while its uncertainty remains visible.

## Evaluation Metrics

The compaction mechanism should report:

- raw unique tags and canonical unique tags per level;
- top-K coverage before and after canonical mapping;
- long-tail support mass;
- review-required support mass;
- head stability under threshold changes;
- regenerated candidate validity and change rate;
- promotion acceptance/rejection/split/unclear rates after human review;
- over-merge and under-merge rates from the R190 merge-risk packet;
- time and model-call cost for candidate regeneration;
- user-task impact in C5, especially tasks about repeated tests, repo-external
  reads, network effects, and mixed system behaviors.

The key OSDI-facing metric is not "fewer labels". The key metric is whether
compaction improves semantically grounded aggregation while preserving audit
coverage. Useful derived metrics are:

- effect-weight conservation across raw/display render modes;
- display-label drilldown completeness;
- ambiguity reduction in baseline-collapse examples;
- false-merge and missed-merge rate from human labels;
- task-answer time and accuracy for developer questions before/after display
  compaction.

## Current Evidence Boundary

Current local evidence supports the mechanism, not semantic correctness:

- R196 produced 1,811 raw tag rows: 231 existing canonical merges,
  114 review-merge rows, 39 regeneration candidates, 2 contextual-split
  candidates, 1,241 kept rare distinct tags, and 184 kept head tags.
- R201 tested seven policy variants. Baseline review-required support was
  1.926%; the worst variant was 1.931%. Raising tail thresholds reduced
  baseline-head stability to 65.217%, which is a real policy risk.
- R202 ran the optional llama.cpp regeneration path over all 41 regenerate/split
  rows: 41 grammar-valid one-word candidates, 32 changed from raw, 9 unchanged,
  and 25 unique generated tags.
- R203 converted those candidates into a paired-review promotion packet, but it
  has no human labels and does not update the canonical map.
- R205 turns the compaction contract into a measurable artifact. Over the
  current R196/R189 rows, raw unique tag strings are 1,546 and canonical unique
  tag strings are 1,364, an 11.772% display-vocabulary reduction. Top-20 support
  coverage moves from 93.683% raw to 95.186% canonical, while review-required
  support remains 1.926%. R205 also checks that all 1,811 R196 rows match R189
  by `(dimension, raw_tag)`, with 0 canonical mismatches and 231/231
  auto-canonicalize rows coming from R189 merge rows. These are
  compaction-readiness metrics only; R190 and R203 still have 0 final human
  labels.
- R209 materializes the reversible display-map data layer. It exports one active
  display row for each of the 1,811 R196 raw-tag rows, a 1,748-row raw drilldown
  index under 1,509 active display labels, and an empty reviewed display-map
  diff because R203 has 0 final labels. It applies only the 63 deterministic
  alias rows as active display merges; 168 R189 lexical/profile merges remain
  pending merge candidates and 41 regenerated labels remain candidate-only. It
  records 0 hidden `other` rows, complete raw coverage, preserved drilldown
  support, and no canonical-map update.
- R212 compares four session/prompt display policies over the generated R170
  system folded stacks: raw, alias-only, profile-guarded-candidate-applied, and
  R209 conservative display. All variants conserve 183,714 system-effect
  weight. Raw rendering has 26,829 stacks; alias-only and R209 conservative
  display have 26,612; the
  hypothetical profile-guarded-candidate-applied view has 26,067 but would
  activate unreviewed profile merges over 2.532% of total effect weight. This
  supports the conservative R209 rule: only deterministic aliases are active by
  default, while profile/lexical and regenerated labels stay candidate-only
  until reviewed. R212 does not yet cover LLM/token display compaction.
- R213 verifies the display-mode data layer that consumes R209: raw mode has
  1,811 buckets, display mode has 1,748 buckets, and pending mode keeps the same
  1,748 buckets while overlaying 209 candidate rows and 323 review-required
  rows. All three modes preserve 482,398 support, pending membership is
  unchanged, drilldown membership matches the active display map, and hidden
  `other` buckets remain 0. This proves the display data contract is auditable,
  not that any pending merge or regenerated label is correct, and not that the
  browser DOM or visual drilldown path has been exercised.
- R214 converts the long-tail design into a control-loop artifact. The current
  policy keeps 63 deterministic aliases active, keeps 168 profile-merge
  candidates and 41 regenerated/split candidates pending, exposes 323
  review-required rows, and keeps 0 active candidate merges. It now also emits
  a seven-row rollup preview: 184 preserved head rows with 464,133 support,
  1,241 preserved rare rows with 6,025 support, 63 active alias rows with 2,947
  support, 168 pending profile-merge rows with 5,697 support, 114 pending
  review-only merge rows with 560 support, 39 pending LLM-regeneration rows with
  1,413 support, and 2 pending contextual-split rows with 1,623 support. It
  fails `prompt_review_budget` because prompt-level review support is 3.258%,
  and it fails `head_stability_under_high_tail_threshold` because head stability
  drops to 65.217% under higher tail thresholds. This is evidence for a
  conservative display policy and control surface, not quality evidence.
- R215 compiles the frontend TypeScript display-mode consumer and runs it under
  a Node harness that renders R209 display-map/drilldown rows and cross-checks
  R213/R214 summary counts. It preserves raw/display/pending support and
  membership, keeps candidates as pending overlays, and rejects corrupted
  drilldown plus candidate-as-active fixtures.
  This is renderer-model evidence only; browser UI, visual click path, adequacy,
  merge quality, and user utility remain unsupported.
- R216 compiles the same display-mode consumer as browser ES modules, serves a
  temporary DOM harness in headless Chrome, clicks raw/display/pending controls,
  preserves the same 482,398 support, and rejects corrupted drilldown plus
  candidate-as-active fixtures. This is a browser DOM harness smoke, not the
  production React view or visual drilldown.
- R217 builds the real Next static frontend, serves a minimal AgentFlame API
  fixture with R209 artifacts, opens `/agentflame` in headless Chrome, and
  verifies that production `AgentFlameView` renders the default display panel:
  mode `display`, 1,748 buckets, 482,398 support, 3 mode buttons, and matching
  raw membership. It does not click the controls or exercise visual drilldown.
- R218 uses synthetic review fixtures over real R209 pending rows to preview a
  reviewed display-map diff. It accepts 2 final consensus/adjudicated promotion
  rows, rejects 4 unsafe rows, keeps preview support at 482,398, preserves
  1,811 raw keys, creates 0 hidden `other` buckets, and does not update the
  canonical map. This proves update-gate mechanics only, not promotion quality.

Therefore the defensible claim today is: AgentFlame has a versioned,
auditable semantic compaction mechanism that preserves raw tags and routes
long-tail uncertainty into explicit review. It cannot yet claim that the
compacted tags are semantically adequate or useful to developers.
