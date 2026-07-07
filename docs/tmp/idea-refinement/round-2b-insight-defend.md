# Round 2b — Insight Defend (two passes)

**Date:** 2026-07-07

## Defense strategy

Counter the "just pprof with labels" attack by establishing a structural difference: agent traces have no inherent call stack (pprof tagroot augments an existing execution stack; there is none here).

## Pass 1 changes

1. **¶5 insight paragraph:** Rewrote to lead with "there is no inherent call stack to fold" as the structural difference. Added interdependence argument — three elements (records, stacks, labels) are jointly necessary; any two without the third falls back to GROUP BY or fixed-hierarchy.
2. **Contribution #1:** Changed from "reduces to two abstractions" to "reduces to two abstractions plus intent recognition" with joint-necessity framing.
3. **§2.3:** Added explicit pprof tagroot/tagleaf distinction — "adds frames to an existing execution stack, but agent traces have no execution stack to augment."
4. **Related work:** Sharpened "domain" distinction to "structural" distinction.

## Pass 2 changes (after Round 2c re-attack)

1. **¶5 interdependence:** Grounded with concrete RQ1 data — "without intent recognition, 90% of weight is mixed across intents."
2. **Contribution #3:** Elevated from "Evaluation" to "Evaluation via hidden-label localization" — explicitly frames the evaluation methodology as a contribution, not just "we ran experiments."

## Remaining weakness

The insight is "correctly stated but borderline obvious." The hidden-label evaluation methodology is the strongest novelty differentiator and is now elevated in the contribution list.
