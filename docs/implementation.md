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

The Rust inducer now recursively partitions each contiguous operation interval
with one target-blind objective. Candidate boundaries occur only where adjacent
operations differ in an eligible visible field. For every informative field,
the implementation computes resource-weighted categorical entropy and its
normalized information gain at the boundary, then averages the field gains.
It accepts the best boundary only when the mean gain is strictly greater than
`ln(n)/(2n)` for the interval's `n` operations. Query relevance is only a
deterministic exact-tie breaker; it does not enter the score. The selected
field's dominant child values produce reconstructable `field=value` frames.
The current CLI retains an explicit maximum-depth bound, whose default is four.

The previous token-set/Jaccard, semantic-shift, balance, coverage, label-quality,
small-child, majority, and fixed-score terms and gates are not part of the
current candidate implementation. TF-IDF/K-Means belongs only to the optional
Python rule-authoring backend. The built-in time view weights a timestamped
operation by elapsed time to the next recorded event rather than by an
independently recorded operation duration.

Implemented CLI capabilities include:

- `--profile-spec` for repeatable source, view, mapping, filter, stack, ranking,
  tagging, and output choices;
- `--op-map` and `--op-map-file` for derived operation fields;
- `--where` for operation predicates after mapping and before folding;
- `--stack` and `--stack-rule` for declared stack construction;
- `--induce-operation-stack` for recursive visible-field stack induction;
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
- AgentSight evidence must first be converted into one of the supported inputs;
  the current CLI has no direct AgentSight-recording reader and does not claim
  verified trigger lineage.
- All serialized views should represent the same folded weighted paths for the
  same effective configuration.

## Known Scientific Gaps

The implementation is ahead of the admitted scientific evidence in breadth of
configuration. In particular:

1. operation-stack induction has mixed and recently negative held-out evidence;
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

## Implementation Policy For The Next Experiment

Do not add another score term, threshold, feature, model, dataset, or evaluator
for the next RQ3 mechanism test. Reuse the complete 287-session
OSWorld-Human operation population, the existing frozen depth-four result,
`script/rq3_rust_inducer_fidelity_eval.py`, and the same boundary and B-cubed
metrics. Change only the arbitrary hard depth limit so the registered
gain-versus-penalty rule controls termination. Keep oracle-field exclusion,
candidate fields, objective, complexity penalty, tie-breaking, stack labels,
workload, scorer, and controls unchanged. Because the depth diagnosis came from
this population, record the run as a post-hoc mechanism test rather than fresh
confirmation; if it succeeds, use an independent annotated workload for the
next confirmation instead of tuning another OSWorld constant.
