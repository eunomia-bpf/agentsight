# Full Python–Rust Equivalence Run

**Executed:** 2026-07-15T01:51:15-07:00
**Execution status:** **PASS; awaiting independent result review**
**Role:** mechanical port verification on existing post-hoc development data

## Build And Command

The current Rust port passed `cargo fmt`, `cargo clippy --all-targets -- -D
warnings`, 41 unit tests, 8 CLI/profile integration tests, and 3 standard-trace
tests. Release build completed as `agentpprof 0.2.37`.

```bash
python3 script/rq3_recurrence_stack_rust_equivalence.py \
  --out-dir .agentsight/experiments/rq3-recurrence-rust-equivalence-v1/full
```

The adapter reused the exact five approved OSWorld session folds. For each
fold, it wrote one label-free reference file from the other four folds and one
held-out target file. Every operation row contained only `session`, `action`,
and unit value. It then invoked the release Rust binary once per fold and
compared the full induction report to the approved Python implementation.

## Complete Result

The command exited successfully with:

- 3,691 of 3,691 adjacent boundary decisions exactly equal;
- 3,978 of 3,978 per-operation motif assignments exactly equal;
- 2,656 of 2,656 segment start/end/motif records exactly equal;
- all 44 unique motifs equal; and
- exact aggregate held-out profile mass 3,978.

Raw report cardinality and `(session,position)` uniqueness were checked before
mapping, so duplicate rows cannot be hidden by dictionary construction. Every
expected key and value was then checked. Fold centers and cutoffs matched to
absolute/relative tolerance `1e-12`; the largest visible differences are only
floating-point summation order and do not alter a decision. The five unseen
counts remain 10, 30, 14, 16, and 25, totaling 95.

All five release invocations returned success, wrote empty stderr, conserved
their complete held-out target mass, and reported the new recurrence policy.
Reference and target session sets were disjoint for each invocation.

## Interpretation

This run demonstrates that the existing Rust `--induce-operation-stack` path
implements the independently verified Python recurrence candidate exactly on
the complete existing development population. It is implementation evidence,
not another hypothesis test. It does not make OSWorld-Human fresh RQ3
confirmation, validate motif-name semantics, or establish cross-family
generalization.

## Artifacts

- `.agentsight/experiments/rq3-recurrence-rust-equivalence-v1/full/summary.json`
- `.agentsight/experiments/rq3-recurrence-rust-equivalence-v1/full/fold-0/`
- `.agentsight/experiments/rq3-recurrence-rust-equivalence-v1/full/fold-1/`
- `.agentsight/experiments/rq3-recurrence-rust-equivalence-v1/full/fold-2/`
- `.agentsight/experiments/rq3-recurrence-rust-equivalence-v1/full/fold-3/`
- `.agentsight/experiments/rq3-recurrence-rust-equivalence-v1/full/fold-4/`

The authoritative `docs/agentpprof-paper` submodule remained clean and
untouched.
