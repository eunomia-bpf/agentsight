# Independent review — step 0081 raw-action skeleton control (RQ2)

Reviewer: independent, read-only. Repository:
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.
Experiment under review:
`docs/tmp/build-and-evaluate/step-0081-20260725T012438-0700/experiment-001/`.
Baseline for isolation/content comparisons:
`docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/experiment-001/`.

## Verdict: PASS

All six required checks pass. The experiment is complete, the scoring is
reproducible to full precision, the raw-identity provenance reconstructs
exactly from frozen step-0072 files, packets are leakage-free, the only
manipulated variable is the group path, and the decision-critical
content-efficiency test is significant in the expected direction.

## Check table

| # | Check | What I ran | Result |
|---|---|---|---|
| 1 | Completeness | counted `raw-responses/`, `packets-stage1/`, `packets-stage2/`; recomputed failure tallies from `raw-results.json` per_query + `stage*_attempts` counts in each response | PASS — 220/220/220; tallies match results.md exactly (stage1 fallback=0, ok=220, retry=0; stage2 orig_fail=0, ok=219, retry=1) |
| 2 | Scoring (AP + MAP) | recomputed AP from `completed_ranking` (score = n−index → descending) vs `target_operation_ids` via `sklearn.average_precision_score` on 8 random queries (seed 20260725); recomputed all 5 MAPs from per_query | PASS — 8/8 AP exact; all 5 MAPs exact to 1e-15 (raw_action 0.465129, profile 0.455333, direct 0.501967, agentprof 0.325504, only 0.208713) |
| 3 | Raw-identity provenance | reconstructed grouping for 3 trajectories from `method-index.json: methods.raw.operation_leaves` + `fixed-groups.jsonl` source_preserving_agent last-3-frame suffix, path = `(task_family.casefold(), "raw:"+leaf, *suffix)`; diffed against `packets-stage1/` | PASS — 3/3 group-path sets and member sets identical; confirmed composite `system;component;raw_action` leaf is used, NOT bare `raw_fields.raw_action` |
| 4 | Leakage | scanned 15 stage-1 + 15 stage-2 sampled packets for forbidden keys (target/outcome/judge/localizer/mistake/scorer/ground_truth/...); verified stage-1 carries no evidence payload | PASS — no forbidden keys; stage-1 has no source_summary/evidence |
| 5 | Manipulation isolation | compared stage-2 packet schema (top keys, group keys, evidence-item keys, task text, operations listing) between 0080 and 0081 over 3 sampled + 1 fixed query | PASS — all field sets identical; task text and operation list identical; only `group_path` content differs (semantic → raw) |
| 6 | Paired content-efficiency (DECISION) | 10,000-draw paired trajectory-cluster bootstrap within strata (seed 20260927) over 220 paired queries, delta = 0081(raw) − 0080(semantic); metrics: content_opened_fraction, stage2_evidence_chars, selected_evidence_operation_count | PASS — see numbers below; semantic skeleton opens significantly less content |

Bootstrap validation: I re-implemented the harness cluster bootstrap and
**exactly reproduced** the reported profile_reader MAP interval
`[-0.02076671, +0.04241655]` and nonpositive count `2822/10000` to full
precision (seed 20260926, 5 strata, 220 clusters). This confirms the
bootstrap machinery used for Check 6 is correct.

## Content-efficiency numbers with intervals

Direction: Δ = step0081(raw-action skeleton) − step0080(semantic skeleton).
Positive Δ ⇒ the **raw** skeleton opens **more** content (semantic opens
less). 10,000-draw paired cluster bootstrap within the 5 benchmark strata,
seed **20260927**.

| Metric | Mean 0081 (raw) | Mean 0080 (semantic) | Paired Δ | 95% interval | Nonpos. draws |
|---|---:|---:|---:|---:|---:|
| Content-opened fraction | 0.6501 | 0.5301 | **+0.1200** | **[+0.1034, +0.1367]** | 0 / 10000 |
| Stage-2 evidence chars | 25716.1 | 21527.0 | **+4189.2** | **[+2981.0, +5268.4]** | 0 / 10000 |
| Selected-evidence-operation count | 16.96 | 14.17 | **+2.80** | **[+1.96, +3.60]** | 0 / 10000 |

All three intervals lie entirely above zero (0/10000 nonpositive draws each).

### Does the semantic skeleton open significantly less content at the fixed 5-group budget?

**Yes.** At the fixed ≤5-group budget, the semantic profile skeleton (step
0080) opens a mean of **53.0%** of the full-packet character volume, versus
**65.0%** for the raw-action skeleton (step 0081). The paired difference is
**+0.120** (95% CI [+0.103, +0.137], 0/10000 nonpositive draws): the
raw-action skeleton opens ~12 percentage-points *more* content than the
semantic skeleton. The same direction and significance hold for absolute
stage-2 evidence characters (+4189 chars) and for the count of selected
evidence operations (+2.80 ops). Semantic naming concentrates attention on
materially less source content than grouping on raw-action identity.

## Additional corroborated facts

- Raw-identity field confirmed against frozen files:
  `methods["raw"]["operation_leaves"]` = 5960 leaves, 143 unique, composite
  `system;component;raw_action` (hex-encoded). The bare
  `projection.raw_fields.raw_action` (e.g. `response:stop`,
  `str_replace_editor:view`) is only one component and is NOT used as the
  identity — verified by direct field comparison.
- Grouping structure: mean 9.82 raw groups/trajectory (median 9.0) vs step
  0080's 13.70 mean semantic groups; mean largest group 9.24 (max 77).
  Matches summary.json and results.md.
- Failure tallies: only 1 stage-2 retry across the population (1 OK after
  retry), 0 fallbacks. No query scored via original-order fallback.
- The ≤3-query `validate-summary.json` is correctly excluded from results
  (results.md and execution-log.md label it "not a paper result").
- Bootstrap seeds documented and consistent between results.md, execution-log.md,
  and summary.json: local_only=20260923, local_agentprof=20260924,
  direct_reader=20260925, profile_reader=20260926.

## Discrepancies (expected vs actual)

None. Every reported number I independently recomputed matched. No
corrective action was taken (read-only review; none required).

## Note on MAP interpretation

For completeness: the raw-action reader MAP (0.4651) is numerically
*slightly above* the semantic profile reader MAP (0.4553), but the paired
difference (+0.0098, 95% CI [−0.0208, +0.0424], 2822/10000 nonpositive) is
not significant. So semantic naming does not significantly improve ranking
accuracy at this budget, but it does significantly reduce the volume of
source content the reader opens. Both effects are reported honestly in
results.md. This is consistent with the framing (semantic naming directs
attention concentration / content efficiency, here shown on the content
axis), and does not affect the PASS verdict.
