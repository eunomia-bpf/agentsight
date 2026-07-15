# AgentProf Implementation

## Current Artifact

The implemented artifact is the Rust crate and CLI under `agentpprof/`, version
`0.2.37` in `agentpprof/Cargo.toml`. Its package description is a pprof-style
semantic profiler for local AI coding-agent sessions. It also accepts explicit
operation files and supported trace containers used by repository experiments.

This file records implemented reality. The exact pre-recovery implementation
history is archived at
`docs/tmp/cycle-0001-20260711T164850-0700/03-review-gate/idea-regression-recovery-20260712T021723-0700/archive-pre-recovery/implementation.md`.

## Source Layout

| Path | Role |
|---|---|
| `agentpprof/src/main.rs` | CLI, profile-spec loading, source selection, mapping/filter/rank options, output routing |
| `agentpprof/src/profile.rs` | operation records, operation-stack configuration, mappings, filters, folding, ranking, and stack induction |
| `agentpprof/src/session.rs` | local agent-session ingestion |
| `agentpprof/src/standard_trace.rs` | Chrome/Perfetto Trace Event import and export through operation records |
| `agentpprof/src/tagger.rs` | optional semantic tagging support |
| `agentpprof/tests/profile_spec_cli.rs` | CLI/profile-spec/mapping/filter/ranking/induction integration tests |
| `agentpprof/tests/standard_trace_cli.rs` | trace import/export integration tests |
| `agentpprof/backend/python/cluster_tagger.py` | optional Python tagging backend |
| `agentpprof/examples/` | public fixture and usage material |
| `script/hodoscope_representation_eval.py` | thin official-data adapter for the completed matched Hodoscope/flat/turn/recursive experiment; not a core AgentProf subsystem |
| `script/hintbench_profile_localization_eval.py` | thin official-data adapter, real-AgentProf runner, baseline scorer, and result reporter for the completed HINTBench experiment; not a core AgentProf subsystem |
| `script/r315_llm_reader_eval.py` | thin rank-hidden packet collector and post-collection scorer for the completed fixed-reader RQ2 experiment; not a core AgentProf subsystem |
| `script/rq3_recurrence_stack_induction_eval.py` | fixed five-fold Python development adapter and scorer for the completed recurrence-induction experiment |
| `script/rq3_recurrence_stack_rust_equivalence.py` | mechanical full-population verifier for Python/Rust boundary, segment, motif, and mass equivalence |

## Implemented Pipeline

The maintained Rust path implements:

```text
local Codex/Claude sessions, operation JSONL, or supported trace input
  -> operation records with string fields and weights
  -> inline/file-backed field mappings
  -> field predicates
  -> declared or induced operation stack
  -> weighted folding
  -> optional group ranking
  -> pprof, folded, JSON, or SVG output
```

The Rust inducer now constructs operation identities from cross-session action
recurrence. It counts adjacent action transitions in a reference population,
computes normalized pointwise mutual information (NPMI) with left and right
marginals from that same transition sample space, and separates low- from
high-association transitions with deterministic occurrence-weighted
one-dimensional two-means. An unseen transition or a score strictly below the
midpoint of the two centers starts a new segment; otherwise the current segment
continues. Each resulting frame is the run-length-compressed action
sequence of its segment, so the same recurring motif receives the same
cross-session identity.

Automatic induction requires exactly one nonempty `session` and one nonempty
`action` value per operation. It uses input order within each session and gives
each adjacent transition one count; operation weights remain additive profile
measures and do not alter motif learning. `--induce-reference-operation-file`
may supply a separate label-free reference corpus. Missing fields, a population
with no transitions, a degenerate score distribution, or failed two-means
separation is an explicit error rather than a fallback. The old information-
gain objective and its depth, query, and session options are not runtime
alternatives; supplying those legacy knobs with recurrence induction is
rejected. TF-IDF/K-Means belongs only to the optional Python rule-authoring
backend. The built-in time view weights a timestamped operation by elapsed time
to the next recorded event rather than by an independently recorded operation
duration.

Implemented CLI capabilities include:

- `--profile-spec` for repeatable source, view, mapping, filter, stack, ranking,
  tagging, and output choices;
- `--op-map` and `--op-map-file` for derived operation fields;
- `--where` for operation predicates after mapping and before folding;
- `--stack` and `--stack-rule` for declared stack construction;
- `--induce-operation-stack` for cross-session recurrence-based operation
  identity, with optional label-free reference operations from
  `--induce-reference-operation-file`;
- `--rank-rule`, `--rank-op-rule`, and `--rank-mode` for JSON group ordering;
- Chrome/Perfetto Trace Event import and export through operations;
- pprof-compatible profiles plus folded-stack, JSON, and SVG renderings.

The exact CLI remains authoritative; use `cargo run --manifest-path
agentpprof/Cargo.toml -- --help` before copying a command into a paper or
experiment plan.

## What Is Not Implemented

The current artifact does not implement the reviewer-generated mechanism stack
from the pre-recovery paper, universal unsupervised intent/failure discovery, or
automated repair and analyst recommendation. Detailed discarded mechanism names
and specifications remain only in the timestamped recovery archive.

These must not appear as achieved system contributions. Existing mapping,
ranking, and stack-induction options may serve as experimental policies, but
their presence does not establish diagnostic value.

## Build And Test

From the repository root:

```bash
cargo build --manifest-path agentpprof/Cargo.toml --locked
cargo test --manifest-path agentpprof/Cargo.toml --locked
cargo run --manifest-path agentpprof/Cargo.toml -- --help
```

Public-fixture smoke and package/install scripts exist under `docs/visexp/`.
They are useful artifact checks, not substitutes for the paper's full real
experiment.

## Input And Output Boundaries

- Private raw local histories remain outside committed public artifacts.
- Experiments should use explicit, source-documented inputs and record the
  command, versions, mapping/profile specification, and raw output path.
- Public benchmark outcome labels remain outside target-time construction and
  ranking unless a baseline explicitly uses them as an oracle upper bound.
- Trace containers are normalized into operations before profiling.
- Automatic operation-stack induction requires exactly one nonempty `session`
  and `action` value per operation and returns an explicit error when its
  recurrence model cannot be learned.
- AgentSight evidence must first be converted into one of the supported inputs;
  the current CLI has no direct AgentSight-recording reader and does not claim
  verified trigger lineage.
- All serialized views should represent the same folded weighted paths for the
  same effective configuration.

## Known Scientific Gaps

The implementation is ahead of the admitted scientific evidence in breadth of
configuration. In particular:

1. recurrence induction clears the registered simple controls on the same
   post-hoc OSWorld-Human development population, but still lacks an independent
   cross-family confirmation of phase/action identity;
2. many mapping and rank rules were developed on datasets later used for
   analysis, so unchanged transfer needs a genuinely untouched family;
3. profile-group ranking can improve because of visible fields or rank policy
   rather than semantic hierarchy;
4. current trace exchange is not complete OpenTelemetry/OpenInference/Phoenix
   compatibility;
5. offline replay cost does not establish end-to-end diagnostic efficiency;
6. correct semantic or causal lineage needs an independent source-native oracle.
7. the tested fixed 8/32/128 recursive adapter has no stable first-hit advantage
   on Hodoscope iQuest, and the official density-gap/FPS bundle is substantially
   stronger on its published task.
8. imported zero values are currently normalized to one; existing admitted
   experiments use positive integer weights, but zero-valued measures require
   an artifact correction before use.
9. the complete HINTBench profile has a favorable inspection-work point estimate
   but does not separate from raw action under its predeclared paired interval;
   it is a scoped boundary within the cumulative three-benchmark RQ2 answer.
10. the fixed-reader result is limited to one local model and each view's
    query-aware top-five packet; it adds group-prioritization evidence but does
    not establish lower work, reader-only causality, human utility, or raw-action
    superiority.

## Implementation Policy After The Recurrence Port

The Step 0017--0018 information-gain results remain frozen experiment artifacts
and historical baselines; that mechanism is no longer the Rust runtime path.
Step 0020 changes the objective rather than adding a feature, depth, threshold,
or score term. On the same already-observed 287-session development population,
recurrence induction reaches boundary F1 0.6799 and operation-weighted B-cubed
F1 0.7862, above the strongest registered simple controls at 0.6445 and 0.6784.
Because the labels had already informed mechanism diagnosis, these numbers are
post-hoc implementation-development evidence rather than fresh RQ3
confirmation.

The release Rust port exactly matches the fixed Python evaluator on all 3,691
adjacent decisions, 3,978 motif assignments, and 2,656 segments across the five
existing folds, while conserving all 3,978 profile units. Mutating scorer-only
fields leaves the complete induction report unchanged. This closes the current
OSWorld-Human mechanism-development round. Do not add another field, cutoff,
depth, or objective variant on this population; if the paper requires broader
algorithm evidence, use the unchanged port on an independent annotated family.
