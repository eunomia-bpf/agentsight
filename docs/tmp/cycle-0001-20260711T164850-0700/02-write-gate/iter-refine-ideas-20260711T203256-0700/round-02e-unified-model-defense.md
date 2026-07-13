# Iter-Refine-Ideas Round 2e — Unified Model Defense

## Unified scope-tree contract

The paper now defines a scope constructor `C` that maps every selected operation
to one finite, potentially variable-depth path.  The induced tree includes every
prefix and must satisfy:

- sibling membership partitions the parent;
- each operation belongs to exactly one terminal scope in a view;
- every node conserves the selected additive mass;
- nodes fold across runs only when the complete prefix consists of the same
  stable semantic identities.

Manual field projection is the fixed-depth constructor.  Recursive induction is
the variable-depth constructor whose segment labeler must be frozen on
development runs.  Trace-local IDs are explicitly classified as debugger-only
and cannot establish the cross-run claim.

## Implementation boundary

Inspection of the real Rust implementation showed that the current inducer uses
TF-IDF shift, visible-field changes, balance, query overlap, and dominant visible
values to label recursive segments.  It provides a partition and conserves
weight but has no admitted evidence that its labels are stable cross-run
identities.  The paper now states this limitation rather than claiming that a
derived local ID automatically satisfies the formal model’s transfer property.

## Distinctive navigation mechanism

The proposed navigator consumes any valid scope tree, closing the producer →
consumer chain for manual, native, fixed, and induced constructors.  Development
runs freeze:

- per-operation query risk `r_q(o)`;
- a cross-run diagnostic-yield prior `h_q(s)` for stable scope prefixes;
- the mixture parameter.

The priority is expected diagnostic yield per declared operation or token cost.
This makes stable cross-run folded identity and an interchangeable accounting
measure enter the search decision directly.  SDBL’s per-log LLM/expertise step
scope does not provide this mechanism, though an extended analytical system
could reproduce it.

## External target semantics

The method emits only whole candidate scopes under both budgets.  Success is not
defined by consuming its own leaf; it is external gold operation/span coverage
by the union of those whole emitted scopes.  Atomic ranking inside emitted
scopes remains a separate downstream metric.

## Contribution and RQ alignment

- Contribution 1 is now the stable-identity, recorded-correlation inheritance,
  mass-conserving scope-tree contract plus cost-normalized navigation.
- Contribution 2 explicitly identifies the implemented substrate and the still
  unimplemented stable induced identity/navigator.
- Contribution 3 reports admitted evidence, including the negative RQ2 result.
- RQ1 defines preservation as one-time assignment and exact additive mass, and
  records conservation of all `183,714` system-effect units.
- RQ2 owns diagnostic correspondence and the proposed navigator.
- RQ3 owns end-to-end practicality.

## Build evidence

The paper compiles successfully with all newly added primary citations.  No
undefined citation, undefined reference, or LaTeX error remains.  The PDF is
nine US-Letter pages, but body content still enters page eight; this remains a
mandatory writing/layout issue rather than an excuse to delete scientific
content during idea refinement.

## Next decision

Run another independent reattack.  Round 2 remains open until the idea is
classified `HARDENED` or the mechanism collapses.
