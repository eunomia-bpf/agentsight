# Experiment Plan: RQ6 External Relation Boundary

## Research question

Which process relations observed in the six selected natural workspaces are
also recoverable in independent public coding and scientific-process traces,
and which longitudinal cells remain unanswerable because the public data does
not preserve a persistent cross-session workspace lineage?

This is an external-boundary check, not a prevalence estimate. The two public
corpora are analyzed separately and are never pooled with each other or with
the six local cases.

## Fixed public sources and acquisition invariant

- `nvidia/Open-SWE-Traces` at Hugging Face revision
  `9c0e4579a4ee0effa3e5f7a552494a045f29377d`: 207,489 synthetic
  SWE-Bench-style trajectories across OpenHands/SWE-agent and
  Minimax-M2.5/Qwen3.5-122B. The release exposes chronological role streams,
  Tool calls, paths/commands when present, and task resolution status.
- `AliceKJ/IdeaTrail` at revision
  `56a26582c8723992ce1e9e289953e24e03977aa7`: 1,170
  reverse-synthesized scientific-ideation trajectories with chronological
  `View`, `WebSearch`, `Scraper`, `Write`, `Edit`, `Glob`, and `Grep` calls.

Both releases are CC BY 4.0. Their synthetic construction, harnesses, task
selection, and source limitations remain explicit threats to validity.

The Dataset Viewer `rows` endpoint is not revision-addressable. It is used
only as a transport after a hard precondition: immediately before metadata
enumeration and before and after every bounded fetch batch (at most 32 rows),
the Hub dataset API must report the exact commit above. A mismatch stops acquisition rather than silently
reading a later `main`. The acquisition record preserves the Hub response,
the complete Parquet-file manifest returned for that HEAD, the selected raw
row JSON, and SHA-256 digests. A cached, hash-matching raw row may be replayed
after HEAD moves; a missing row may not be refetched from a different HEAD.

## Frozen clustered sampling

The experiment projects only the identifier columns of the pinned Parquet
manifest to construct a sampling frame, then uses the Viewer rows API for the
selected full records. Selection is hash-ranked and does not inspect outcome,
grade, patch, reasoning, or Tool-call fields.

- Open-SWE-Traces: within each of the four fixed config/split strata, enumerate
  `(row offset, instance_id, trajectory_id)`. Rank unique `instance_id` values
  by SHA-256 of `rq6:20260722:<stratum>:<instance_id>` and retain 64 task
  instances. If an instance has several trajectories, retain exactly one: the
  minimum SHA-256-ranked `trajectory_id`. The task instance, not a trajectory
  row or adjacent row block, is the sampling and uncertainty unit within each
  stratum (256 stratum-specific selections total). Because the same benchmark
  instance may occur under two harness/model strata, cross-stratum unique IDs
  are also reported and are not described as 256 globally independent tasks.
- IdeaTrail: extract the release-defined topic identifier from each system
  prompt, reconcile the advertised 963 unique topics, rank topics by SHA-256
  of `rq6:20260722:ideatrail:<topic>`, retain 64 topics, and choose one
  SHA-256-ranked `sample_id` per topic. The topic is the sampling and
  uncertainty unit. `_src` is only a three-valued synthesis-batch field and is
  not treated as the topic.

Sixty-four was fixed as a **pre-analysis amendment** after acquisition had
started but before the relation metric table was computed or inspected. The
choice used the already declared deterministic hash prefix, the 50-unit gate,
and acquisition cost; it did not use any relation metric. It is the
smallest power-of-two sample above the 50-unit coverage gate; for a single
proportion its worst-case normal-approximation 95% half-width is 12.25
percentage points. This is adequate for the preregistered strong directional
boundary check and is not presented as a prevalence estimate. The original
256-unit-per-stratum hash-ranked candidate list remains in `selection-plan.csv`
so the prefix selection is auditable.
- Every selected row is retained. Parse failures, empty trajectories, unknown
  Tool calls, missing paths, and trajectories without mutations remain in the
  coverage denominator and become N/A only for the relation that requires the
  missing evidence.

The sample manifest records dataset revision, config, split, row offset,
instance/topic cluster ID, public row identifier, selection digest, and
SHA-256 of the exact row JSON. Raw rows remain under the ignored experiment
`raw/` directory and are the local replay source; the manifest, aggregate
tables, figures, and scripts are release-safe.

## Common action projection

The projection is deliberately smaller than `agent-session`; it adapts only
the two fixed public schemas and does not become a product IR.

Each source Tool call is one ordered action with zero or more of:

- `explore`: source-native View/Glob/Grep/WebSearch/Scraper, editor view, or a
  high-confidence shell read/search command;
- `mutate`: source-native Write/Edit/editor create or replace, or a
  high-confidence shell create/write/copy/move/delete command;
- `validate`: a shell command matching a declared test/check/build adapter;
- `target_path`: a normalized path explicitly present in Tool arguments or a
  high-confidence shell operand. URLs, prose, hidden reference patches, final
  model patches, and Tool observations never supply action paths.

One action may carry several categories or paths. Unknown calls remain actions
but contribute only to coverage. Path normalization removes the known
workspace prefix, rejects traversal and URLs, and derives a module from the
first remaining path component. The primary common estimand is deliberately a
**path-target** estimand: an editor `View` of a directory stays a directory
target and never masquerades as a file artifact. A proven-file-only sensitivity
is reported separately. No public adapter infers stable file identity or
rename lineage.

The same projection is frozen over the six local cases from the already frozen
source-action export before public relation metrics are computed: ordered Tool
calls, explicit current `path` targets (including directory-scope targets),
first-component modules, and native worktree lanes. The local-anchor CSV,
input SHA-256, projection version, and exact transition/return estimands are
written into this experiment directory. This path-compatible anchor is
separate from the stronger local lineage-identity analysis used by RQ1/RQ3.

## Relation cells and estimands

| Cell | Estimand | Open-SWE | IdeaTrail | Comparison status |
|---|---|---:|---:|---|
| E1 exploration before first mutation | calls and target-path reads/searches before first mutation; fraction with any prior exploration | yes | yes, but enforced by the released workflow | descriptive only |
| E2 mutation-to-validation response | recognized successful validation before the next mutation; action gap | only where call and observation expose attempt/status | N/A (no execution/validation tool) | analogous/descriptive; not RQ2 replication |
| E3 path-target/module transition | adjacent path-resolved Tool-call pairs: same normalized path, same first-component module, cross module | yes | yes | exact common projection; RQ3 path-compatible anchor |
| E4 module return after leaving | number of path-resolved Tool calls strictly between the previous visit and return to an earlier first-component module (`A,B,A` = 1) | yes | yes | exact common projection; RQ3 path-compatible anchor |
| E5 target concentration | per-trajectory top-target share and target HHI | yes | yes | analogous/descriptive; not artifact-identity replication |
| E6 staged path revision | mutated paths targeted before first mutation and mutated again later | yes | yes | analogous/descriptive; not lineage replication |
| L1 persistent artifact fate | survival/revival across independent native sessions | N/A | N/A | RQ1 |
| L2 cross-session re-grounding | prior-session read/overlap before a new-session mutation | N/A | N/A | RQ4 |
| L3 Skill/instruction footprint | exact source-native Skill attribution and instruction access | N/A | N/A | RQ5 |

The public traces can support E1--E6 only within one task attempt. They cannot
be used to turn L1--L3 into zeros or negative findings. E5/E6 use paths rather
than stable artifact identities and therefore cannot replicate lineage claims.

## Statistics and decision rules

- Report exact coverage and corpus/stratum-specific medians, interquartile
  ranges, and aggregate transition shares. Do not report one pooled rate.
- Use a deterministic cluster bootstrap with 2,000 resamples and seed 20260722
  for 95% percentile intervals. Open-SWE resamples selected `instance_id`
  units inside each of its four strata; IdeaTrail resamples selected topic
  units. Sequential calls within a trajectory are never resampled
  independently.
- The frozen path-compatible local anchor motivates two directional checks:
  (D1) same-path plus same-module transitions exceed cross-module transitions;
  and (D2) observed module returns are present, with a non-degenerate return-gap
  distribution. Report supported, contradicted, or N/A separately by public
  stratum. Do not test an exploration-before-mutation direction: IdeaTrail's
  system workflow explicitly requires `View` before `Write`/`Edit`, and both
  public corpora are harness-conditioned.
- E2, E5, and E6 remain descriptive external context; no arbitrary threshold
  turns them into confirmatory claims. Open-SWE `resolved` and IdeaTrail
  `_grade`/`value_tier` are retained only for sensitivity tables and do not
  define eligibility or the primary relation directions.
- No p-value, human label, expert adjudication, LLM judge, semantic embedding,
  or learned classifier is used.

## Outputs

- `sample-manifest.csv`, `sampling-frame-summary.csv`, `local-anchor.csv`, and
  `source-check.json`;
- `coverage.csv`, `trajectory-metrics.csv`, `relation-summary.csv`, and
  `na-map.csv`;
- one PDF/PNG figure with separate Open-SWE and IdeaTrail panels for E1--E6;
- one compatibility/N/A matrix for local RQ1--RQ5 relations;
- `result.md`, `commands.log`, a visual inspection record, and an independent
  read-only result review.

The figure is generated from the committed aggregate CSVs. It cannot use force
layout coordinates or Agent Nebula screenshots as empirical measurements.

## Gates and interpretation stop

1. Verify both Hub HEADs and Parquet manifests, freeze the local path-compatible
   anchor, then preflight one row from every stratum and four IdeaTrail rows. It must pair
   every Tool observation to the immediately preceding assistant Tool-call
   batch, because IdeaTrail call IDs can repeat inside one trajectory.
2. At least 95% of selected rows must parse and every source row hash and public
   identifier must reconcile. Otherwise stop.
3. A relation cell requires at least 50 eligible independent task/topic units
   in a public stratum; otherwise report N/A.
4. Run a second source checker that independently recounts selected rows,
   messages, calls, explicit paths, mutations, validations, and transition
   denominators from raw row JSON. Any mismatch blocks interpretation.
5. A positive direction supports only external recurrence of a within-attempt
   structural relation. It does not make the local six cases representative,
   validate Agent productivity, or establish a causal harness/model effect.
6. A contradiction narrows the local observation; it does not invalidate the
   trajectory representation. An N/A cell is a public-source capability
   boundary, not absence of the phenomenon.
