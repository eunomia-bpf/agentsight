# Plan Revision after Review Round 2

## Accepted Necessary Fixes

1. Model-visible group identifiers are now opaque aliases assigned only after lexicographic sorting of the visible original IDs. Original IDs, view labels, and rank fields are absent from the request; collection maps valid aliases back using a visible-only map. Preflight explicitly checks the serialized request for leakage.
2. Retry semantics are unified: transport, non-JSON, wrong-count, duplicate-alias, and invalid-alias responses all receive at most three identical attempts. Persistent failure invalidates the whole matrix.
3. The R316 control is frozen to `trial-scores.csv`. Scoring deduplicates `top_k=3` rows by packet, verifies repeated assignment rows are identical, and retains exactly 18 unique packet controls rather than treating assignment repetitions as data.

## Rejected Expansion

No model expansion, repeat decoding, new benchmark, extra baseline, prompt search, statistic, sealing, or other infrastructure was added. Alias substitution is a small presentation control over the existing visible packet, not a new profile or feature.

## Status

The revised plan is ready for serial review round 3. No implementation or experiment has started.
