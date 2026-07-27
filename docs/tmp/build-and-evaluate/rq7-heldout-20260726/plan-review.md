# Independent Preregistration Review

## Initial review

**Verdict: BLOCK.**

The review was read-only.  It did not generate, open, or run any new
held-out answer, projection, or result.

Three defects block execution:

1. **There is no executable v4/6×12 path.**  The frozen
   `agentvis/research/rq7_measurement.py` still declares
   `native-root-conformance-v3` and hard-codes 6×6 sources, the earlier
   seed/cutoff, and exactly two exclusion hashes.  Its freeze would reject
   this protocol, while the v4 checker would reject a v3 freeze.  A v4 runner,
   authoritative commands/paths, hash, and append-only attempt ledger must be
   frozen before any held-out generation.
2. **The preflight rule can swallow a real negative result.**  Requiring
   one-project conformance before the six-project run, then labeling the
   missing full matrix incomplete, turns a genuine method failure into an
   inconclusive result and prevents the requested full ledger.  Preflight
   should gate only whether the real path executes and preserves integrity.
   A valid scientific failure must still proceed to the one full run.
3. **`display_path` is not gated.**  The declared ledger contains
   `display_path`, but the attempted-edge key omits it and no separate exact
   check covers it.  A rename/display-lineage defect could therefore pass.
   Add `display_path` to the exact multiset key or an equivalent mandatory
   derived-field equality gate.

The other core provisions pass review: 72 roots/12 per case, three historical
manifest exclusions by hash/root/call, no seed/project replacement, 120 new
instances without old rows/anchors/witnesses/answers, no pooling with the old
60/60, zero model calls for deterministic scoring, and the historically
matched independent model-audit role.

## Follow-up review

**Verdict: PASS.**

This review was strictly read-only. No runner command was executed, no file
was written, and no held-out answer, projection, or result was opened.

All prior blockers are closed:

- Runner SHA-256
  `6df7a7ee8bed4ce2a5b4320da9b10aac1f710976b7af88623d21bd002fd6c33e`
  matches the protocol and is runtime self-checked.
- The v4 primary materializer is independent; checker unwrap/atom/effect
  functions are used only in the four public v4 fixture controls. The
  standalone checker performs the post-freeze recomputation.
- Fixture completion is required before selection. Fixture and release-build
  artifacts use experiment-local Cargo targets, and Python bytecode writes
  are disabled.
- Empty production edge/call ledgers remain valid scientific negatives rather
  than mechanism failures.
- A completed scientific preflight failure does not block full execution.
- The fixed 120-question freeze and four deterministic methods per question,
  together with the 480-row full gate, ensure 120 trajectory question
  decisions.
- The 6×12 split, three exclusion manifests, append-only attempts, and exact
  `display_path` edge key remain enforced.

No remaining scientific-validity or executability blocker was found.
