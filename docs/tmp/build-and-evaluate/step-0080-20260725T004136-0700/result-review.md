# Step 0080 result review

Timestamp: 2026-07-25T01:15:00-07:00
Reviewer: root orchestrator session
Verdict: ACCEPTED as valid; registered hypothesis PARTIALLY supported

## Verification performed

- Completeness: 220/220 queries; stage-1 zero fallbacks; stage-2 one retry,
  zero original-order failures.
- Scoring: independently recomputed AP for 5 random queries from stored
  `completed_ranking`; all match exactly. All four MAPs recomputed over the
  full population match `results.md` (profile 0.455333, direct 0.501967,
  local_agentprof 0.325504, local_only 0.208713); the stored baselines equal
  the step-0072/0079 values.
- Leakage: stage-1 packet contains no mistake/gold fields (checked); groups
  come from the frozen step-0072 `source_preserving_agent` mapping
  (`rq2-canonical-tags-v2-current/trace/results/fixed-groups.jsonl`), which
  is target-blind by construction. No new grouping was built.

## Admissible result

Profile-guided two-stage reading reaches MAP 0.455: significantly below the
full-trace reader (-0.047 [-0.083, -0.012]) and far above Direct+AgentProf
(+0.130 [+0.080, +0.179]). The reader opened a mean 53.0% of the full-trace
source content (evidence-only stage-2 payload) and its stage-1 group
selections were never fallback-generated.

## Hypothesis disposition (registered in 000-step-entry.md)

- "Retains at least Direct+AgentProf's MAP" — SUPPORTED (0.455 vs 0.326,
  interval wholly positive).
- "Substantially fewer packet characters than the full-trace reader" — NOT
  SUPPORTED for total transmission: mean 46.5K vs 44.6K chars, because the
  skeleton is transmitted in both stages and the second call adds overhead;
  wall time is higher (50.2 s vs 29.9 s two-call total).
- Attention-concentration reading — SUPPORTED: 53% of source content opened
  retains 91% of the full reader's MAP (0.455/0.502), and the profile index
  alone (stage 1, zero source content) directed those selections.

## Interpretation boundary for any paper use

- The index works as an attention concentrator: half the evidence, ~91% of
  the quality. The cost claim must be stated in terms of source content
  opened, not total request characters, and the two-call latency overhead
  must be disclosed alongside it.
- In this single-query-per-trajectory benchmark the skeleton cannot amortize.
  Any amortization claim (skeleton reused across queries/measures) is an
  argument about the setting, not a measurement from this run; do not state
  it as measured.
- Model family and single-workload scope carry over from step 0079's review.

## Supplement: exact logical token accounting (added 2026-07-25)

Exact `tiktoken o200k_base` counts over the stored packets:
full-trace 12,615 mean input tokens/query; two-stage profile-guided
4,837 (stage 1) + 11,154 (stage 2) = 15,991/query, i.e. 1.27x the
full-trace input. The two-stage implementation is therefore strictly more
expensive per single query in logical input tokens; the only measured cost
reduction is source evidence opened (53%). Any paper cost sentence must use
these token numbers, not character counts. Legitimate framings that remain:
skeleton reuse across queries via prompt caching (argument, not measured
here), human reading volume, and the context-window feasibility bound —
full-trace reading is impossible for populations like the 4.56M-token Git
case, where profile-guided drilldown is the only strong-reader access path.

## Status of the three-condition ladder now measured on TraceElephant

Direct-only 0.209 < Direct+AgentProf 0.326 < profile-guided reader 0.455 <
full-trace reader 0.502. Each paired interval excludes zero. This ladder is
the cleanest available statement of what the profile contributes to
localization and what a full read still buys on top.
