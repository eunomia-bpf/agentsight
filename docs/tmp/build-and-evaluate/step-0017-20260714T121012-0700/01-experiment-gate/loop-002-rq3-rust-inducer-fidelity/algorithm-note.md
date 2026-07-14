# Algorithm Note: Principle-Driven Operation-Stack Induction

## Status And Scope

This note records the algorithm idea requested during Step 0017. It is an
implementation-level proposal within the fixed RQ3, **How accurate are the
tags?** It does not change the authoritative thesis, **Agent observability needs
profiling, not only debugging**, the two core abstractions, any of the four RQs,
or the paper story inherited from the read-only submodule. The mechanism remains
named **operation-stack induction**; no additional algorithm name is needed.

The code and complete OSWorld-Human evaluation already exercise the fixed-depth
version of this proposal. That result establishes a large improvement over the
previous multi-term heuristic but does not yet establish superiority over the
strongest simple controls. The idea and its empirical status must therefore be
kept distinct: this is the precise candidate mechanism to test, not an already
authorized paper-level accuracy claim.

## Motivation

The previous inducer accumulated several independently motivated terms and
gates: token-set/Jaccard shift, visible-field change, semantic shift, balance,
coverage, label quality, small-child penalties, majority limits, fixed score
thresholds, and candidate subsampling. Even when each term was plausible, the
combined decision was difficult to explain, analyze, or attribute.

The replacement follows one principle: construct an operation stack by
recursively choosing the visible boundary that best reduces uncertainty about
resource-weighted operation fields, and stop when the improvement no longer
justifies the added partition complexity. The mechanism should have one
objective and a small set of input-admission rules, rather than a weighted soup
of proxy objectives.

## Inputs And Candidate Boundaries

The input is one ordered sequence of operations. Each operation has visible
string fields and an additive nonnegative profiling weight. Declared oracle or
scoring labels, metadata, noisy fields, session identifiers by default,
near-numeric fields, constants, and extremely high-cardinality fields are
excluded before scoring. These exclusions define the target-blind input schema;
they are not additional score terms.

A cut between two adjacent operations is a candidate only when at least one
eligible field changes across that adjacency. Both resulting children must be
nonempty.

## One Objective

For interval `I`, eligible field `f`, and candidate boundary `b`, let `L` and
`R` be the two children, `W_X` the sum of operation weights in interval `X`, and
`H_w(f, X)` the resource-weighted categorical entropy of field `f` in `X`.
For each field with positive parent entropy, compute

```text
G_f(I, b) = [H_w(f, I)
             - (W_L / W_I) H_w(f, L)
             - (W_R / W_I) H_w(f, R)] / H_w(f, I).
```

The boundary score `G(I, b)` is the equal mean of these normalized gains over
all informative eligible fields. Equal averaging prevents a field with a large
raw entropy scale from dominating merely because of its units or cardinality.
Resource weighting makes the partition objective match the additive quantity
that the profiler will aggregate.

For an interval containing `n` operations, use the fixed complexity penalty

```text
P(I) = ln(n) / (2n).
```

Select the candidate with the largest `G(I, b)` and split only when
`G(I, b) > P(I)`. Recurse on both children. The penalty is the algorithmic stop
condition; it replaces fixed score, child-size, balance, label-quality,
coverage, majority, and semantic-shift gates.

## Stack-Frame Construction And Ties

For an accepted boundary, choose the positive-gain field with the largest
`G_f(I, b)` whose dominant resource-weighted values differ between the two
children. Append `field=value` for each child's dominant value. Every accepted
split appends one frame, even when equivalent text appeared at an ancestor, so
each operation has one reconstructable leaf path. Distinct raw values that
normalize to the same folded frame receive a deterministic value-derived
suffix.

Query relevance never changes the numeric objective. It breaks only exact
field-gain and cut-score ties. Remaining ties use earlier boundary position and
then lexical field order, making output deterministic.

## Intended Properties

The implementation and tests should maintain these properties:

- target and oracle labels are never read by construction or ranking;
- every input operation belongs to exactly one terminal leaf;
- the sum of all leaf weights equals the input weight exactly;
- every accepted split improves the same explicit objective beyond its penalty;
- emitted child paths are distinct and reconstructable;
- deterministic input produces deterministic output;
- recursion terminates because every split creates two smaller nonempty
  intervals, with an optional runtime depth bound acting only as a safety limit.

These are useful correctness and interpretability properties, not evidence of
tag accuracy by themselves.

## Scientific Position

Information gain follows established decision-tree induction, and recursive
boundary selection follows binary-segmentation methods. Neither ingredient is
claimed as new. The paper-relevant candidate contribution is their combination
with agent-visible operation fields, resource-weighted additive profiling,
target-blind field admission, and stack frames that preserve accounting and
support profiling queries.

The fixed-depth-four complete run on 287 OSWorld-Human sessions improved
boundary F1 from `0.0843` to `0.4231` and B-cubed F1 from `0.4653` to `0.6165`
against the previous Rust heuristic. It still trailed the strongest simple
controls, and 106 sessions reached the depth limit. Therefore the next clean
test should change only the arbitrary hard depth cap, allowing the gain-versus-
penalty rule to serve as the actual stop condition while holding fields,
objective, penalty, labels, workloads, metrics, and tie rules fixed. A positive
post-hoc result on OSWorld-Human would still require confirmation on an
independent annotated workload before supporting a broad paper claim.

## References And Evidence

- Quinlan, *Induction of Decision Trees*, Machine Learning 1, 1986:
  <https://doi.org/10.1007/BF00116251>.
- Fryzlewicz, *Wild Binary Segmentation for Multiple Change-Point Detection*,
  Annals of Statistics 42(6), 2014: <https://arxiv.org/abs/1411.0858>.
- Exact fixed candidate and experiment protocol: `experiment-plan.md`.
- Corrected complete execution: `full-run-corrected.md`.
- Independent interpretation and next experiment: `result-review.md`.
- Code and invariant review: `code-review.md`.
