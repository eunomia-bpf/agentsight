# Experiment plan: finite-evidence semantic ranking on AgentProcessBench

**Plan revision:** 1  
**Proposed:** 2026-07-13T06:05:24-07:00  
**Outer gate:** EXPERIMENT  
**Research question:** RQ2 — Does Profiler Output Correspond to Real Problems?

## One tested hypothesis

Across the complete four-family AgentProcessBench population, ranking both raw
and target-preserving semantic profiles with the same target-label-blind Wilson
lower score over released judge votes will let semantic context localize human-
annotated harmful steps with higher equal-family macro average precision and
lower work-to-50 than the raw profile, while the semantic AP gain exceeds a
group-size-matched shuffled refinement of that raw profile.

This is the second and final planned AgentProcessBench construction in this
cycle. It tests one positive construction hypothesis inside fixed RQ2. It does
not answer all of RQ2 and cannot change the paper thesis, canonical story, four
RQs, or positive RQ2 hypothesis.

## Decisive uncertainty

The first complete construction established a semantic-specific macro AP
increase but left work-to-50 uncertain. The remaining question is whether a
published, fixed finite-evidence ranking rule can stop small high-mean groups
from consuming the beginning of the inspection order, allowing the already
observed semantic concentration to reduce early inspection work reliably.

The strongest competing explanation is that the first AP gain comes from
semantic refinement but is not operationally useful: after accounting for
finite judge evidence, semantic groups may still require no less work than raw
groups to recover half of the harmful operations.

## Published construction and interpretation boundary

The construction combines three externally published principles documented in
`source-method-selection-report.md`:

1. rank by an external estimate of usefulness/harm under the Probability
   Ranking Principle;
2. evaluate the ranking by effort required to recover target events, following
   effort-aware inspection work;
3. use Wilson's fixed lower score to prefer harmful-vote rates supported by
   more released evidence.

The 20 released judges are not assumed independent. `score_g` is therefore a
deterministic finite-ensemble ranking score, not a calibrated 95% confidence
bound on human harmfulness. No result may claim nominal statistical coverage
for this group score. Statistical uncertainty about the semantic-versus-raw
effect comes only from the predeclared query-cluster bootstrap.

## Complete source and unit of analysis

- Official source: `RUCBM/AgentProcessBench`, commit
  `0a42606b178a8c69d40c5765dc05c342f921e578`.
- Population: all 1,000 released trajectories and all 8,509 assistant steps.
- Families: BFCL, GAIA dev, HotpotQA, and tau2; each has 50 tasks and five
  rollout trajectories per task.
- Operation: one released `role="assistant"` message, matching the benchmark
  step definition even when it contains multiple tool calls.
- Human harmful positive: official step label `-1`.
- Human non-harmful negative: official step label `0` or `+1`.
- Dependence unit: original `(family, query_index)`; all five task rollouts stay
  together in resampling.

No family, task, trajectory, operation, neutral label, or null released judge
prediction is silently discarded. Null predictions provide no vote but their
operations remain in every inspection metric.

## Fixed visible fields and two primary profiles

Reuse the exact converter and fields from the completed experiment:

- `intent`: existing AgentProf label-blind TF-IDF/K-Means tag over the 200 task
  descriptions, using its fixed silhouette selection over 5–25 clusters and
  seed 42;
- `phase`: `open`, `work`, `close`, or `no_tool` from tool-call position;
- `action`: `tool_call`, `final_answer`, or `reasoning`;
- `target`: sorted called-tool set, `final`, or `user`;
- `repeat_state`: the existing five-operation-window repeat feature.

The two primary profiles remain:

```text
raw:      action → target → repeat_state
semantic: intent → phase → action → target → repeat_state
```

Semantic retains the complete raw leaf. The converter may use task text,
message roles, tool calls, tool returns, and step order. It must not use human
step labels, final labels, answers, rewards, expert explanations, or fields
derived from them.

## Released-vote score

For each operation, load the same 20 official blind-judge prediction slots used
by the first construction. Give every judge equal weight. For each profile
group `g`:

```text
h_g = number of non-null released predictions equal to -1 in g
n_g = number of all non-null released predictions in g
p_g = h_g / n_g
z   = 1.959963984540054

score_g = (p_g + z²/(2n_g)
           - z * sqrt(p_g(1-p_g)/n_g + z²/(4n_g²)))
          / (1 + z²/n_g)
```

If `n_g = 0`, assign `score_g = 0.5` and report the group and operations. All
operations in a group receive `score_g`. There is no fitted parameter, model
selection, judge weighting, human-label threshold, parent smoothing, or
family-specific rule.

The score must be materialized for every profile before human-label values are
loaded. The implementation must independently verify the per-group operation,
harmful-vote, and available-vote totals that feed the score.

## Fixed views and fair baselines

Real `agentpprof 0.2.37` constructs all group assignments. Apply the same
Wilson score to:

1. **flat:** one group;
2. **per session:** one group per trajectory;
3. **raw action:** `action → target → repeat_state`;
4. **semantic operation stack:**
   `intent → phase → action → target → repeat_state`;
5. **ungrouped vote score:** one operation per group.

The co-primary comparison is semantic versus raw under the Wilson score. The
completed mean-risk raw and semantic point estimates are retained as a fixed
historical diagnostic and may be recomputed only to verify implementation
equivalence; they are not an alternative pass condition. Flat, session, and
ungrouped views explain the frontier but do not add gates.

## Group-size-matched semantic control

Repeat the fixed 200-permutation control with seed 4204. Within every
`(family, action, target, repeat_state)` raw leaf, jointly shuffle observed
`(intent, phase)` pairs among operations. Preserve the exact pair multiset and
the semantic subgroup-size multiset inside every raw leaf.

For each shuffled profile, pool released votes inside the shuffled groups,
compute the same Wilson score, and calculate all metrics with complete equal-
score tiers. Human labels do not influence a shuffle. The AP specificity test
remains predeclared and directly comparable to the first construction.
Work-to-50 shuffle effects are recorded as a supporting mechanism check, not a
post-hoc fourth pass condition.

## Primary and supporting measurements

The two co-primary measurements use human labels only in the final scorer:

- operation-weighted average precision over operations assigned their complete
  group score;
- fraction of all operations inspected to recover 50% of human harmful steps
  (`work-to-50`, lower is better).

Groups and equal scores are atomic. AP cannot order operations inside a group
or use human label, operation ID, individual risk, or another score to break a
tie. Work-to-50 opens the complete equal-score tier that crosses 50%.

Supporting measurements are:

- recall after inspecting 30% of operations;
- adapted FirstErrAcc using the first operation whose group score is greater
  than `0.5`, with “no predicted error” if none exists;
- binary harmful-step accuracy at the same fixed threshold;
- group count, groups-to-50, top-five work and recall;
- raw and semantic mean-risk metrics reproduced from the prior construction;
- per-family results and equal-family macro summaries;
- operation, non-null-vote, harmful-vote, assignment, and score accounting;
- the complete 200-row AP and work-to-50 shuffle distributions.

Supporting measurements cannot silently become new pass conditions.

## Paired uncertainty

Retain 10,000 valid paired query-cluster bootstrap draws with seed 4204. Within
each family, sample its 50 query IDs with replacement and keep all five
rollouts for a sampled task. Recompute group vote totals, Wilson scores, and
metrics from the resampled operation multiset. Use the same draw for raw and
semantic and combine families with equal weight.

Discard a four-family draw only if any family has no human harmful positive.
Examine at most 50,000 deterministic draws to retain 10,000 valid draws.
Fewer than 10,000 valid draws makes the FULL run `INCOMPLETE` and produces no
scientific verdict. Report percentile 95% intervals, examined/discarded counts,
and all family point estimates.

## Predeclared comparison and verdict

Define:

```text
delta_ap_observed   = macro_AP_semantic - macro_AP_raw
delta_ap_shuffle_j  = macro_AP_shuffle_j - macro_AP_raw
p_shuffle_ap        = (1 + count(delta_ap_shuffle_j >= delta_ap_observed)) / 201
```

- **SUPPORTED:** the paired 95% interval is entirely favorable for both
  semantic-minus-raw AP and raw-minus-semantic work-to-50, and
  `p_shuffle_ap <= 0.05`.
- **CONTRADICTED:** the FULL execution is valid and either paired macro interval
  is entirely adverse.
- **INCONCLUSIVE:** every other complete valid outcome.

The verdict applies only to this tested ranking construction. It does not
change the paper-level thesis, story, RQs, or positive RQ2 hypothesis. Because
this is the second AgentProcessBench construction, any non-supporting result
returns to the outer WRITE/REVIEW decision with both complete records; it does
not trigger a third target-reused ranking variant.

## REAL PREFLIGHT, FULL run, and independent review

After at least three serial independent reviews approve this Markdown plan:

1. extend the existing converter/scorer without changing the prior result;
2. run focused tests for the Wilson formula, null-vote handling, atomic ties,
   label-after-score sequencing, vote accounting, shuffles, and bootstrap;
3. run a REAL PREFLIGHT on the first 10 query IDs in every family through real
   AgentProf, score materialization, and final scoring;
4. independently review validity; preflight values cannot answer the tested
   hypothesis or select a different rule;
5. run all 1,000 trajectories and 8,509 operations to completion;
6. independently recalculate every full result and write a detailed Markdown
   result review.

Planned paths:

```text
source:
  docs/visexp/out/agentprocessbench-rq2/source/official-repo
implementation:
  script/agentprocessbench_wilson_eval.py
focused tests:
  script/test_agentprocessbench_wilson_eval.py
preflight artifacts:
  docs/visexp/out/agentprocessbench-rq2-wilson/preflight/
full artifacts:
  docs/visexp/out/agentprocessbench-rq2-wilson/full/
```

Planned commands:

```bash
python3 script/agentprocessbench_wilson_eval.py preflight \
  --source docs/visexp/out/agentprocessbench-rq2/source/official-repo \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --out docs/visexp/out/agentprocessbench-rq2-wilson/preflight \
  --query-limit 10 --permutations 200 --bootstraps 1000 \
  --max-bootstrap-attempts 5000 --seed 4204

python3 script/agentprocessbench_wilson_eval.py full \
  --source docs/visexp/out/agentprocessbench-rq2/source/official-repo \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --out docs/visexp/out/agentprocessbench-rq2-wilson/full \
  --permutations 200 --bootstraps 10000 \
  --max-bootstrap-attempts 50000 --seed 4204
```

The FULL run is complete only when it accounts for exactly four families,
1,000 trajectories, 8,509 operations, 20 released judge slots per operation,
all five views, 200 matched shuffles, and 10,000 valid paired cluster-bootstrap
draws within 50,000 attempts. Each operation must have one assignment in every
view and later exactly one human label. The report must state all null-vote
paths actually taken.

## Plan review protocol

Run at least three reviews serially, not in parallel. Each reviewer must read
this complete plan, `source-method-selection-report.md`, the completed first
experiment plan and result, and the `research-experiment-design` skill. Each
review returns `PASS` or `REVISE` with concrete must-fix items. Revise the
Markdown plan after each `REVISE`; the next reviewer reads the new complete
revision. REAL PREFLIGHT is forbidden until the third serial review and zero
must-fix convergence.

No review may resolve uncertainty by changing the thesis, rewriting RQ2,
dropping work-to-50, removing a family, using human labels to choose a score,
or editing `docs/paper/` or `docs/agentpprof-paper/`.

No paper, submodule, shared skill, thesis, RQ, or hypothesis is modified by
this plan.
