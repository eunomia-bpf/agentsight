# Step 0094 Experiment 001: Independent Plan Review

## Round 1 — BLOCK

The independent reviewer rejected the original protocol before implementation.
The following are hard validity blockers, not optional polish.

### Oracle and causal action linkage

- The raw AgentReward records plausibly contain enough mechanical information
  for state-history reconstruction: the first-user full database state, ordered
  call IDs/names/arguments, tool results, and per-result database updates.
  Replay must nevertheless demonstrate faithfulness by flattening exact raw
  message order, pairing calls and results by call ID rather than list position,
  reconstructing tool traces only from reversible typed results, and reconciling
  every message, update, and snapshot count.
- The unchanged official `MilestoneMatcher` returns an optimized achievement
  mapping, not a causal action oracle. A persistent exact state at a later
  snapshot does not prove that the later action achieved the node.
- A separate, predeclared action-link predicate is required. State constraints
  need matcher-selected similarity 1, immediately prior similarity 0, a delta
  in the constrained namespace at that exact snapshot, and exactly one raw
  tool-result action producing that delta. Tool-trace constraints need exactly
  one call-ID-linked action at the selected snapshot.
- Initial-state, persistent-without-delta, response/user-selected, ambiguous
  parallel, non-reversible-result, and otherwise non-causal mappings must be
  excluded. The estimand must be named “exact action-linked official milestone
  occurrences.” A new first-achievement remapping must not be presented as the
  official matcher.

### Eligibility and item definition

- `similarity == 1` is not enough because ToolSandbox defaults include ROUGE,
  substring, tolerance, and other non-exact comparisons. Before annotation,
  enumerate each node's complete snapshot-function and effective column-
  comparator composition, freeze an exact/binary allowlist, and report
  exclusions by reason.
- Exclude any physical action carrying zero or more than one eligible milestone
  node from the primary clustering items. Duplicating one action into several
  gold items makes the prediction structurally unidentifiable by one active
  leaf.
- A primary gold cluster must have support in at least two distinct trajectories
  and preferably two conditions. The result is conditional on achieved,
  exactly linked occurrences; it is not milestone-detection recall.

### Scoring and baselines

- Population-global B-cubed over `(scenario, node)` is misaligned because
  reusable root-stripped semantic IDs should be allowed to recur across
  scenarios. Use unweighted scenario-macro B-cubed over repeated runs as the
  primary metric and bootstrap scenario IDs. Global B-cubed may be diagnostic
  only.
- Pair metrics must use different nodes within the same scenario as negatives;
  cross-scenario nodes are not a non-equivalence oracle.
- The original argument-key-only baseline is too weak. The main source-only
  baseline must be value/result aware: normalized tool name, canonical complete
  arguments, success/error class, and changed namespace/column set. Freeze this
  normalization before predictions and retain key-only/tool-only ablations.
- The Step 0087 contract marks only a packet turn's first operation. Existing
  ToolSandbox user turns contain several atomic actions, so the active leaf is
  constant within such turns. This construct mismatch must remain visible.
  Atomic exact-boundary F1 cannot be claimed, and action rows must not silently
  be atomized into turns while calling the protocol unchanged.

### Leakage, staging, and claim scope

- Audit literal opaque gold strings separately from official constraint
  features. Scenario IDs and node indices must have zero model-visible
  occurrences. Filtering already-seen actions after inference is not a leakage
  sensitivity; a cue-removal sensitivity must instead mask the cue before both
  inference and baseline construction.
- The balanced 444-trajectory screen is a futility screen. Reusing those
  selected observations in the confirmatory all-population gate creates
  optional-selection leakage. Freeze both manifests before calls and require
  the untouched 3,107-trajectory remainder to pass the confirmatory interval.
  The all-3,551 score is then descriptive.
- Enforce process/file separation: packet builder may open raw data and
  scenarios; annotator may open only opaque packets and schema; canonicalizer
  may open only operations and marks; scorer may open frozen predictions and
  gold. Scenario, source, condition, trial, outcome, and official-object
  information must not appear in annotator-visible IDs, filenames, working
  directory, prompts, or run metadata.

The strongest admissible claim after amendment is limited to repeated
ToolSandbox scenarios and exact one-to-one action-linked achieved official
milestones. It cannot establish global semantic equivalence, arbitrary-task
generalization, causal first achievement, or atomic boundary accuracy.

## Round 1 disposition

All blockers are accepted. `plan.md` is amended before implementation and will
receive a new independent review round.
