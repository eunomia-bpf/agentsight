# Step-0080 profile-guided reader: fine-grained decomposition

Data: step-0080 experiment-001 (profile-guided two-stage reader, 220 queries), step-0079 experiment-001 (full-trace direct reader), frozen `source_preserving_agent` group mapping (5,960 operations). Index hit = every target operation's frozen group was among the stage-1 selected groups. All cross-checks passed: direct-reader AP step-0080 vs step-0079 mismatches = 0, target-id mismatches = 0, group/op-count mismatches vs fixed-groups = 0.

## 1. Loss decomposition

**Headline: 154/220 index hits (70.0%); index misses account for 147.0% of the 0.0466 MAP gap to the direct reader — more than 100% because on hit queries the profile reader already beats the direct reader.**

- Overall MAP: profile_reader 0.4553, direct_reader 0.5020, local_agentprof 0.3255, local_only 0.2087.
- Profile-reader MAP conditional on index hit: **0.6180** (n=154); conditional on index miss: **0.0758** (n=66).
- Direct-reader MAP on the same subsets: hit 0.5867, miss 0.3042. On hit queries the profile reader is *above* the direct reader (0.6180 vs 0.5867, +0.0313) — reading only the right groups helps stage-2 ranking; misses are where the entire deficit sits.
- Counterfactual — every miss query scored with its step-0079 direct-reader AP instead: MAP = **0.5239** (+0.0685 over the actual 0.4553, and *above* the direct reader's 0.5020). This is the upper bound of perfectly fixing stage 1 (it recovers misses but leaves within-hit ranking untouched).
- Gap attribution (total gap = 0.502 - 0.455 = 0.0466):

  - from miss queries (stage-1 selection failures): 0.0685 = **147.0%** of the gap
  - from hit queries (within-budget stage-2 ranking differences): -0.0219 = **-47.0%** of the gap (negative: the profile reader wins within-hit, which offsets part of the miss damage)

## 2. Per-stratum table

**Headline: the profile reader loses most on Magentic-One/AssistantBench (gap +0.1653) and is closest to the direct reader on SWE-Agent/SWE-Bench (gap -0.0292).**

| Stratum | n | MAP profile | MAP direct | MAP local_agentprof | index-hit rate | mean content opened | gap (direct-profile) |
|---|---|---|---|---|---|---|---|
| Captain-Agent/AssistantBench | 12 | 0.4990 | 0.5153 | 0.2574 | 91.7% | 61.6% | +0.0162 |
| Captain-Agent/GAIA | 73 | 0.5368 | 0.5611 | 0.3437 | 84.9% | 62.8% | +0.0243 |
| Magentic-One/AssistantBench | 17 | 0.2604 | 0.4256 | 0.3176 | 41.2% | 46.4% | +0.1653 |
| Magentic-One/GAIA | 74 | 0.3483 | 0.4397 | 0.2665 | 52.7% | 47.4% | +0.0914 |
| SWE-Agent/SWE-Bench | 44 | 0.5636 | 0.5343 | 0.4161 | 79.5% | 46.5% | -0.0292 |

Strata where the profile reader ties or beats the direct reader: SWE-Agent/SWE-Bench: ties/wins (gap -0.0292).

## 3. Win/loss anatomy

**Headline: profile beats direct on 51 queries, ties on 91, loses on 78. Wins open only 51.9% of content on average (overall mean 53.0%): reading less can help.**

- Wins: mean AP gain +0.2047; mean content-opened fraction 0.5191; index-hit rate 88.2%.
- Losses: mean AP change -0.2654; mean content-opened fraction 0.4811; index-hit rate 26.9%.
- Ties: mean content-opened fraction 0.5783.

Largest 5 wins (profile AP minus direct AP):

| query_id | profile AP | direct AP | delta | index hit | #groups |
|---|---|---|---|---|---|
| magentic-runs-gaia/gaia_task_26_gpt_4o_jkl9y3fqfq2x | 1.0000 | 0.0370 | +0.9630 | hit | 21 |
| magentic-runs-gaia/gaia_task_115_gpt_4o_8mcggpso033m | 1.0000 | 0.2500 | +0.7500 | hit | 8 |
| swe-agent-runs-swe-bench/django__django-11265 | 1.0000 | 0.3333 | +0.6667 | hit | 16 |
| captain-runs-gaia/gaia_task_29_gpt-4o_3kd5m46uqqse | 1.0000 | 0.5000 | +0.5000 | hit | 11 |
| magentic-runs-gaia/gaia_task_103_gpt_4o_vhrphqy975qs | 1.0000 | 0.5000 | +0.5000 | hit | 10 |

Largest 5 losses:

| query_id | profile AP | direct AP | delta | index hit | #groups |
|---|---|---|---|---|---|
| magentic-runs-assistant-bench/assistant_bench_task_2_gpt_4o_iepkkrix9ql4 | 0.0213 | 1.0000 | -0.9787 | MISS | 20 |
| magentic-runs-gaia/gaia_task_67_gpt_4o_6l7z68qpnu9k | 0.0213 | 1.0000 | -0.9787 | MISS | 20 |
| magentic-runs-gaia/gaia_task_164_gpt_4o_qpqjd8n69kwy | 0.0357 | 1.0000 | -0.9643 | MISS | 23 |
| magentic-runs-assistant-bench/assistant_bench_task_6_gpt_4o_kxg2gwp1q09n | 0.0435 | 1.0000 | -0.9565 | MISS | 15 |
| magentic-runs-gaia/gaia_task_23_gpt_4o_5ckgk1np1fpi | 0.0625 | 1.0000 | -0.9375 | MISS | 27 |

## 4. Index difficulty correlates

**Headline: the strongest index-hit correlate is n_groups (Spearman rho -0.397, p=9.86e-10).**

| feature | rho vs index-hit (0/1) | p | rho vs profile AP | p |
|---|---|---|---|---|
| n_operations | -0.292 | 1.06e-05 | -0.403 | 5.23e-10 |
| n_groups | -0.397 | 9.86e-10 | -0.419 | 8.68e-11 |
| largest_group_size | -0.158 | 1.89e-02 | -0.311 | 2.53e-06 |
| target_group_size | +0.221 | 9.67e-04 | -0.111 | 1.00e-01 |
| content_opened_fraction | +0.360 | 3.91e-08 | +0.280 | 2.48e-05 |

Descriptive correlations only; no modeling. Negative rho vs index-hit means larger values of the feature make stage-1 selection failure more likely.

## 5. Budget sensitivity (descriptive)

**Headline: the stage-1 budget of 5 was saturated on 219/220 queries (99.5%); for miss queries the target group was absent from the model's ordered selection in 66/66 cases and ranked 6th-10th in 0/66.**

- Selected-group-count distribution (stored, capped at 5): 4 groups: 1, 5 groups: 219. The single sub-budget query has only 4 groups in total.
- Method note: the stored selection is the model's ordered stage-1 answer truncated at the first 5 valid groups (order preserved). I re-parsed the raw stage-1 responses without the cap (same normalization as the evaluator); the re-parse reproduced the stored capped selection for all 220 queries (validation failures: 0). So the ordered selection exists and its full length is observable.
- Uncapped selection-length distribution: length 4: 1, length 5: 219. The model listed more than 5 groups in 0 queries.
- For the 66 index-miss queries, rank the missed target group would have needed in the model's full ordered selection: absent: 66.
- Caveat (field limitation, stated rather than approximated): the stage-1 prompt instructed the model to "Select up to 5 groups", and no response ever listed more than 5. Ranks beyond 5 are therefore UNOBSERVABLE in this data — "absent" means the target group was not among the groups the model chose to list under an up-to-5 instruction, not proof that it would not have been the 6th-10th choice under a larger instructed budget. What the data does show: under the current budget the model used every slot and still displaced the target group entirely.

## Conclusion: what would most improve MAP

- Fixing stage-1 selection is the dominant lever the data shows: index misses carry 147.0% of the 0.0466 MAP gap (the share exceeds 100% because the profile reader already beats the direct reader within hits), and the perfect-stage-1 counterfactual lifts MAP from 0.4553 to 0.5239 — above the direct reader's 0.5020.
- Whether a larger stage-1 budget would help is not decidable from this data: the prompt instructed up to 5 groups and no response ever listed more, so post-budget ranks are unobservable. What is observable: the budget was saturated on 99.5% of queries and in all 66 miss queries the target group was displaced entirely (not merely ranked 6th), so the failure is group discrimination at stage 1, not stage-2 reading depth.
- Reading less is compatible with winning: the 51 wins open 51.9% of content on average, so the loss mechanism is which groups are opened, not how much is opened.
- Difficulty scales with trace size: n_groups is the strongest miss correlate (rho -0.397), consistent with stage 1 degrading on larger, more fragmented profiles.
