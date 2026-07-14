# Independent Result Review

## Verdict

- Run status: **VALID**
- Tested candidate hypothesis: **CONTRADICTED**
- Research value: **SUPPORTING mechanism evidence**
- Direct thesis challenge: **NO**
- RQ/story consequence: does not answer all of RQ3 and does not change the
  thesis, two-object model, four RQs, or paper story.

The reviewer independently recomputed the corrected raw outputs and matched all
reported counts and metrics. The candidate failed the strongest simple control
on both registered metrics, so `contradicted` is the required verdict. The
runner's earlier combined `mixed_or_contradicted` value was a reporting bug; it
has been corrected without changing predictions or metrics.

## Scientifically Usable Result

The matched old-to-new mechanism comparison is usable as an internal ablation:

- boundary F1: 0.0843 to 0.4231, +0.3388;
- B-cubed F1: 0.4653 to 0.6165, +0.1511;
- no-split sessions: 204 to 4.

This improvement cannot be attributed to information gain alone because the
revision also removed old acceptance gates, candidate subsampling, and label
de-duplication. It also cannot support a claim that the candidate already
recovers human groups accurately, because it remains below simple controls.

## Highest-Value Follow-Up

Depth four is a materially binding but not yet causally established bottleneck:

- 106/287 sessions reach the cap, with 488 `max_depth` terminal nodes;
- binary depth four can express at most 16 leaves;
- 22 sessions have more than 16 official groups and 15 of them hit the cap;
- the 36 sessions of length at least 20 produce 293 candidate groups versus
  984 official groups and only 0.217 boundary F1.

The highest-value next experiment changes only this arbitrary hard cap so the
registered gain/penalty rule becomes the actual stopping principle. All fields,
objective, penalty, tie-breaks, population, metrics, and scorer remain fixed.
Because this direction was selected after inspecting OSWorld-Human diagnostics,
it must be labeled a post-hoc mechanism follow-up; it cannot silently tune a new
depth or penalty. A positive accuracy claim should then be checked on an
independent annotated workload not used to choose this follow-up.

## Paper Boundary

The current paper correctly says the 0.739/0.816 RQ3 result belongs to the
supervised predictor rather than the Rust inducer. This experiment must not
replace those numbers. The Implementation section still describes the old
Jaccard/multi-term heuristic and is now a stale pointer, but WRITE should update
it only after the mechanism iteration is settled; no negative-result paragraph
or story rewrite is authorized here.
