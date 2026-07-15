# Minimal Rust Port Plan — Existing Operation-Stack Induction Path

**State:** proposed after independently verified `SUPPORTED` result
**Role:** mechanical implementation and equivalence work, not a new scientific
experiment

## Objective

Replace the current heuristic-heavy recursive information-gain implementation
behind the existing `--induce-operation-stack` path with the supported simple
principle: recurring adjacent visible `action` transitions define operation
continuity across sessions. This changes neither the paper thesis nor RQ3 and
does not add another benchmark, scorer, metric, or learned feature.

## Minimal Product Behavior

The existing induction flag remains the entry point. The Rust implementation
will:

1. group a label-free reference corpus by visible `session` in input order;
2. estimate action-transition NPMI with coherent left/right transition
   marginals;
3. derive one deterministic occurrence-weighted two-means cutoff;
4. split each target session at unseen or below-cutoff transitions;
5. assign each group a run-length-compressed `action=...-then-...` operation
   identity; and
6. report reference counts, centers, cutoff, unseen count, segments, motifs,
   and excluded scorer fields.

When no external reference is supplied, the current selected corpus is the
reference. This mode is admitted only when every row has exactly one nonempty
visible `session` and exactly one nonempty visible `action`. Session-local
record order is the transition order, and every adjacent occurrence contributes
once regardless of resource/sample weight. Missing or multivalued keys, a
zero-transition reference, fewer than two distinct finite NPMI values, empty
two-means clusters, or non-convergence are explicit errors; the implementation
never falls back to the old objective or silently emits singleton groups. Local
session inputs that do not expose this contract must first derive valid
operation fields or omit automatic induction.

Add one optional general input, `--induce-reference-operation-file`, so a caller can learn recurrence
from a separate label-free corpus. This is required for exact held-out
Python-versus-Rust verification and is also a clean deployment interface for a
previous corpus. It is not a second induction policy or a benchmark-specific
flag.

Distinct raw motifs that normalize to the same folded-frame spelling receive a
stable hash suffix. This preserves recurring identity without collision and
does not change any current OSWorld prediction because its 44 motifs already
normalize uniquely.

## Scope Removal

The recurrence policy has no depth, information-gain penalty, field search,
query tie-break, or session-as-split option. Existing legacy CLI/profile-spec
arguments remain parseable for compatibility, but an explicit
`--induce-max-depth`, `--induce-query-term`, or `--induce-allow-session` setting
is a clear error whenever recurrence induction is enabled.
`--induce-task-stack` remains only a deprecated alias to the same recurrence
implementation. The old information-gain objective is neither a default nor a
fallback, and no legacy parameter is silently ignored.

## Exact Equivalence Check

Reuse the same five OSWorld session folds. For each fold, materialize only the
already loaded scrubbed visible training rows and held-out rows, invoke the
release Rust binary with the training file as the reference corpus, and read
the reported held-out boundary decisions and segments. The report exposes one
record for each `(session,input-position)` adjacency with NPMI or unseen state
and the resulting decision, plus every segment's start, end, and motif. Require
exact equality with the approved Python candidate for every one of 3,691
boundary decisions, every one of 3,978 motif assignments, all 2,656 groups, all
44 motifs, and all fold centers/cutoffs up to documented floating-point
tolerance. Also require 3,978 total sample/profile mass across the five
held-out profiles.

Focused tests mutate or add `human_group`, label/oracle/target, and related
scorer fields while holding `session` and `action` fixed, then require the
complete induction report to remain byte-for-byte equivalent. The induction
implementation may read only those two admitted visible fields; reporting the
standard exclusion list is not accepted as proof by itself.

This check is mechanical implementation evidence. It does not rerun hypothesis
selection, change the registered result, or turn OSWorld into fresh paper
confirmation.

## Files In Scope

- `agentpprof/src/profile.rs`: recurrence implementation and report;
- `agentpprof/src/main.rs`: one optional reference-corpus input and updated
  help/status;
- focused Rust unit/CLI tests;
- the existing Step 0020 adapter or one focused equivalence adapter;
- implementation/design/evaluation records after equivalence passes.

The authoritative `docs/agentpprof-paper` submodule remains read-only. No paper
story, thesis, contribution, or RQ edit is authorized by the port.
