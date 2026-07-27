# Evidence report for the PDF review

All paths below are repository-relative to
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`. The audit
covered the requested experiment records in `docs/tmp/build-and-evaluate/`
through Step 0087, `docs/visexp/out/`, `.agentsight/experiments/`, and
`docs/evaluation.md`. Where `docs/evaluation.md` points to the detailed
canonical record of an older completed experiment, that record is also cited.

## 1. Flat semantic grouping versus recursive hierarchy — FOUND

**Qualifying evidence.** The completed Hodoscope representation-choice
experiment is an exact matched flat-versus-recursive comparison:

- `docs/evaluation.md`
- `docs/tmp/cycle-0001-20260711T164850-0700/01-experiment-gate/loop-rq2-02/experiment-plan.md`
- `docs/tmp/cycle-0001-20260711T164850-0700/01-experiment-gate/loop-rq2-02/full-execution-report.md`
- `docs/tmp/cycle-0001-20260711T164850-0700/01-experiment-gate/loop-rq2-02/result-review.md`

The matched flat condition uses exactly the recursive condition's terminal
fine-cluster assignment with the coarse and middle parents removed. The
independent review verified identical terminal assignments for every action and
seed; the recursive condition adds three levels with at most 8/32/128 nodes.
Both conditions receive the same sampled actions, stored summaries, embeddings,
cohort labels, projection, and oracle isolation.

Exact results:

| Phase | Metric | Flat semantic | Recursive semantic |
|---|---|---:|---:|
| A, ten paired 50%-per-cohort seeds | First-hit rank | 55.4 +/- 95.7 | 24.9 +/- 15.8 |
| A | Characters inspected | 205,746.9 +/- 336,667.1 | 61,671.8 +/- 45,158.4 |
| A | Hits@20 | 0.6 +/- 0.66 | 0.5 +/- 0.67 |
| A | Post-shared-t-SNE runtime | 27.046 +/- 2.346 s | 25.971 +/- 3.359 s |
| B, complete 250-trajectory corpus, ten seeds | First-hit rank | 94.5 +/- 65.2 | 76.3 +/- 58.4 |
| B | Characters inspected | 322,554.8 +/- 225,430.0 | 203,676.4 +/- 159,633.3 |
| B | Hits@20 | 0.1 +/- 0.3 | 0.2 +/- 0.4 |
| B | Post-shared-t-SNE runtime | 32.910 +/- 1.731 s | 33.413 +/- 1.797 s |

For recursive rank minus flat rank, Phase A is `-30.5`, paired-bootstrap
95% interval `[-97.3025, 13.3]`, recursive win rate `0.5`; Phase B is `-18.2`,
interval `[-83.1, 44.3025]`, win rate `0.7`. Thus recursion has no stable
advantage over the matched flat terminal partition. For context, official
Hodoscope obtains first-hit rank `2.9 +/- 0.3` in Phase A and `3.0 +/- 0.0`
in Phase B.

**Case Study 2 does not qualify as a flat-semantic control.** Its registered
fixed-chain score is the fraction of operations whose raw `result` starts with
`error:` or equals `repeated`; it is a scalar raw-result projection, not a
flat semantic tagging/grouping of the same semantic identities. The exact
record is:

- `docs/tmp/build-and-evaluate/step-0085-20260725T200000-0700/experiment-001/results.md`
- `docs/visexp/out/agentreward-diff-pprof-v1/recursive-annotation-v1/`

On 435 consensus-labeled trajectories in 125 task clusters, recursive recovery
exposure has AP `0.6336880791837327`, the fixed repeated/error score has AP
`0.6559621177236952`, and prevalence is `0.3977011494252873`. The
recursive-minus-fixed 10,000-draw task-cluster interval is `[-0.107, 0.061]`
(seed `20260722`). This is a valid detector control, but it does not isolate
flat versus recursive semantic organization.

**Already in `docs/paper/main.tex`?** Partly. The paper reports the Case Study
2 fixed-chain comparison (AP `.634` versus `.656`, interval `[-.107,.061]`)
and cites Hodoscope in related work. It does not report the matched Hodoscope
flat-versus-recursive experiment, its exact numbers, or its negative conclusion.

**Recommendation — add-to-paper:** report the Hodoscope matched control, with
the explicit conclusion that the tested recursive parents did not stably beat
the identical flat terminal partition.

## 2. LLM-generated summary control — PARTIAL

**Usable but not a clean summary-versus-name ablation.** The Hodoscope
experiment reuses author-generated GPT-5.2 action summaries and Gemini
embeddings from the pinned dataset revision
`17c395e8c6ce8a4148251064079e31686c422390`. The same summaries and embeddings
drive the official Hodoscope condition and the matched flat, native, and
recursive conditions. No new API call or resummarization occurs:

- `docs/tmp/cycle-0001-20260711T164850-0700/01-experiment-gate/loop-rq2-02/experiment-plan.md`
- `docs/tmp/cycle-0001-20260711T164850-0700/01-experiment-gate/loop-rq2-02/full-execution-report.md`

The exact summary-driven ranking numbers are those in Item 1: in Phase A,
flat/recursive/Hodoscope first-hit ranks are `55.4 +/- 95.7`,
`24.9 +/- 15.8`, and `2.9 +/- 0.3`; in Phase B they are
`94.5 +/- 65.2`, `76.3 +/- 58.4`, and `3.0 +/- 0.0`. This proves that
LLM-generated summaries can be held fixed while grouping/ranking changes, but
it does not compare a summary-only view directly with AgentProf semantic
operation names under one reader or scorer.

Other apparent summary conditions do not close the gap:

- Steps 0079--0081 use a field called `source_summary` during source-evidence
  reading, but it is source-visible agent/task evidence rather than a separately
  generated equal-information summary control. See
  `docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/experiment-001/results.md`
  and its retained `packets/`.
- The old human-task instrument registers a `flat-summary` condition in
  `docs/visexp/out/user-task-preregistration-r142.md`, but it is a
  process/effect/path table excerpt rather than a documented LLM summary and it
  was never executed. `docs/visexp/out/user-task-paper-r249/scored/user-task-results.md`
  records `0` responses; `docs/visexp/out/evaluation-summary.md` marks
  participant results missing and C5 unsupported.
- Step 0019's reader sees existing visible feature summaries, but those are
  packet aggregates, not a registered LLM-generated-summary replacement for
  semantic operation names. See
  `docs/tmp/build-and-evaluate/step-0019-20260714T164922-0700/experiment-001/experiment-plan.md`.

**Already in `docs/paper/main.tex`?** No. The paper neither identifies the
Hodoscope summaries as a summary control nor reports a matched summary-only
reader/grouping condition.

**Recommendation — run-new-experiment:** compare equal-information generated
summaries directly with semantic operation names under the same grouping or
reader protocol; the Hodoscope record is useful preliminary evidence but does
not isolate this variable.

## 3. Frozen Agent backend on an independent population — MISSING

The only direct multi-level Agent backend scored against independent human
structure is the complete CodeTraceBench run:

- `docs/tmp/build-and-evaluate/step-0087-20260726T023000-0700/experiment-001/results.md`
- `docs/tmp/build-and-evaluate/step-0087-20260726T023000-0700/experiment-001/independent-result-review.md`

It covers 405 trajectories, 17,148 source-native turns, 20,866 operations,
2,948 official human stages, and 251 task clusters. Direct annotation obtains
B-cubed precision/recall/F1 `0.793409 / 0.735836 / 0.763539` and exact
boundary precision/recall/F1 `0.389147 / 0.626032 / 0.479952`.

None of the apparent alternatives is an independent-population confirmation:

- Step 0073 scores 364 later-annotated sessions after excluding the initial 41,
  but it explicitly remains the already observed CodeTrace family, not an
  untouched external family:
  `docs/tmp/build-and-evaluate/step-0073-20260723T201812-0700/000-step-entry.md`
  and
  `docs/tmp/build-and-evaluate/step-0073-20260723T201812-0700/experiment-001/plan-review-round-01.md`.
- The AgentRewardBench annotation covers 440 trajectories, 125 task clusters,
  and 338 bad--good pair occurrences, but its independent endpoint is the
  435-trajectory expert looping label, not human semantic groups, nested
  structure, or temporal boundaries:
  `docs/tmp/build-and-evaluate/step-0067-20260722T135005-0700/experiment-003/result-review.md`.
- The four-session AgentCap case has 326 operations and demonstrates
  construction/question answerability, not independent semantic accuracy:
  `docs/tmp/build-and-evaluate/step-0065-20260721T234809-0700/experiment-001/full-results.md`
  and `docs/tmp/build-and-evaluate/step-0065-20260721T234809-0700/outer-audit.md`.
- OSWorld-Human has independent human groups, but the evaluated methods there
  are supervised and recurrence boundary constructors, not the frozen
  direct/Agent annotation backend.

**Already in `docs/paper/main.tex`?** The CodeTrace result is present, and the
paper correctly says that CodeTraceBench is the Agent-assisted constructor's
development population. No independent non-CodeTrace direct-Agent structure
result is present.

**Recommendation — run-new-experiment:** freeze the Step 0087 direct backend
and score it once on a non-CodeTrace population with independent human
operation groups/boundaries (and nested spans if nested fidelity is claimed).

## 4. Reader budget / quality-cost curve — PARTIAL

Step 0080 contains a strong diagnosis of the fixed five-group point but no
observed multi-budget curve:

- `docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/analysis-001/analysis-report.md`
- `docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/experiment-001/results.md`

Exact fixed-point and saturation evidence over all 220 TraceElephant queries:

- stored selected-group counts are 5 for 219/220 queries and 4 for 1/220;
  the one four-group query has only four groups total, so the budget is
  saturated on `99.5%`;
- reparsing the uncapped raw answers gives the same distribution (4 once,
  5 for 219); no response lists more than five groups because the prompt says
  “Select up to 5 groups”;
- 154/220 queries are index hits (`70.0%`) and 66/220 are misses;
- for all 66 misses, the target group is absent from the complete response;
  ranks 6--10 are unobservable, not zero;
- profile-reader MAP is `0.4553` overall, `0.6180` on the 154 hits, and
  `0.0758` on the 66 misses;
- the direct reader is `0.5020` overall, `0.5867` on the same hits, and
  `0.3042` on the misses;
- replacing each miss with its direct-reader AP yields a counterfactual MAP
  of `0.5239`, versus actual `0.4553` and direct-reader `0.5020`;
- misses account for `147.0%` of the observed `0.0466` direct-minus-profile
  MAP gap, while hit-query ranking offsets `-47.0%`;
- the fixed point opens mean `53.01%` of source content and selects 14.17
  evidence operations from a mean 13.70 available groups.

The counterfactual is a failure decomposition, not an observed larger-budget
point. Because the model was instructed to return at most five groups, the
repository contains no quality, content, token, or latency measurements for
budgets 1/3/10/etc.

**Already in `docs/paper/main.tex`?** The paper reports the fixed five-group
TraceElephant point (MAP `.455`, `53.0%` content opened, raw skeleton `65.0%`)
but not the 99.5% saturation, 70.0% index-hit rate, miss decomposition, or the
fact that a budget curve is unidentifiable from the stored responses.

**Recommendation — run-new-experiment:** rerun the frozen reader/data/model
with several instructed budgets and report MAP, index-hit, opened content,
tokens, and latency at each point.

## 5. Second reader family — PARTIAL

There is a complete non-Grok reader study, but it is on HINTBench rather than
TraceElephant:

- `docs/tmp/build-and-evaluate/step-0083-20260725T024803-0700/experiment-001/results.md`
- `docs/tmp/build-and-evaluate/step-0083-20260725T024803-0700/experiment-001/execution-log-v2.md`

All three conditions use opencode `1.17.18` with its observed default model
`glm-5.2`. The run scores 400 target-bearing queries out of 536 trajectories
(136 zero-positive), covers 12,877 operations, completes 400/400 calls per
condition with zero terminal errors, and uses no Grok response. Exact MAP is:

| Condition | HINTBench MAP |
|---|---:|
| Full-trace GLM reader | 0.623466 |
| Raw-action skeleton | 0.554539 |
| Semantic skeleton | 0.527282 |
| Stored Direct+AgentProf | 0.517489 |
| Stored Direct-only | 0.410559 |

Semantic-minus-raw MAP is `-0.0273`, 95% interval
`[-0.0531, -0.0022]`. Semantic opens `0.2433` of content versus raw
`0.2576`; raw-minus-semantic content is `+0.0143`, interval
`[+0.0090, +0.0195]`. Thus the TraceElephant equal-MAP/content effect does
not replicate on this different workload/reader combination. The record
explicitly prohibits pooling the HINT and TraceElephant numbers because both
workload and reader family change.

Steps 0079--0081 execute the TraceElephant reader and both skeleton conditions
only with the Grok CLI:

- `docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001/execution-log.md`
- `docs/tmp/build-and-evaluate/step-0080-20260725T004136-0700/experiment-001/results.md`
- `docs/tmp/build-and-evaluate/step-0081-20260725T012438-0700/experiment-001/results.md`

No non-Grok reader was executed on the same frozen TraceElephant packets, so
Step 0083 cannot isolate reader-family robustness on that workload.

**Already in `docs/paper/main.tex`?** The paper reports only the Grok-family
TraceElephant study. It does not report the HINTBench GLM result or a
same-TraceElephant second-reader replication.

**Recommendation — run-new-experiment:** execute a second reader family on the
same frozen TraceElephant full/semantic/raw packets and budgets.

## 6. Native-hierarchy and raw-action reader controls — PARTIAL

**Raw-action skeleton: complete and usable.**

- `docs/tmp/build-and-evaluate/step-0081-20260725T012438-0700/experiment-001/results.md`
- `docs/tmp/build-and-evaluate/step-0081-20260725T012438-0700/independent-review.md`
- `docs/tmp/build-and-evaluate/step-0081-20260725T012438-0700/result-review.md`

On all 220 TraceElephant queries, the raw-action skeleton obtains MAP
`0.465129` versus semantic skeleton `0.455333`. Raw-minus-semantic is
`+0.009795`, 95% interval `[-0.020767, +0.042417]`; therefore ranking quality
is statistically indistinguishable. Raw opens mean `0.6501` of content versus
semantic `0.5301`; it exposes 16.96 versus 14.17 evidence operations and has
9.82 versus 13.70 groups per query. The independently reviewed paired content
difference is about `+0.1200`, interval `[+0.1034, +0.1367]`, with
0/10,000 nonpositive draws.

**Native-session/native-tree skeleton: missing for the reader study.** No
executed TraceElephant two-stage reader condition replaces the skeleton with
the source-native session/turn/call hierarchy. The following are not
substitutes:

- the Hodoscope experiment's native comparator is exact released `turn_id`
  grouping and a ranking experiment, not a reader skeleton (Phase A first-hit
  rank `36.8 +/- 31.8`);
- Step 0087's native-tree/native-turn rows are CodeTrace structure metrics, not
  a reader study;
- Step 0079's full-trace reader receives source evidence, but it does not first
  select groups from a native hierarchy under the same two-stage budget.

**Already in `docs/paper/main.tex`?** Yes for the raw skeleton: the paper
reports semantic/raw MAP equivalence and `53.0%` versus `65.0%` content opened.
No native-hierarchy reader control appears.

**Recommendation — run-new-experiment:** add the missing native
session/turn/call skeleton under the frozen TraceElephant two-stage protocol;
the raw-action control does not need rerunning.

## 7. Backend model/version/prompt/decoding disclosure — PARTIAL

Several central backends are reproducible from retained records, but the
repository does not contain sufficient identifiers/configuration for every
evaluated model-backed cell.

**Direct Agent and long-history automatic Agent: strong disclosure.**

- `docs/tmp/build-and-evaluate/step-0087-20260726T023000-0700/experiment-001/cost-record.md`
- `docs/tmp/build-and-evaluate/step-0087-20260726T023000-0700/experiment-001/task-spec.md`
- `docs/tmp/build-and-evaluate/step-0087-20260726T023000-0700/experiment-001/execution-log.md`
- `docs/tmp/build-and-evaluate/step-0086-20260725T213500-0700/experiment-001/cost-record.md`
- `docs/tmp/build-and-evaluate/step-0077-20260723T233616-0700/experiment-001/automatic-backend-instruction.md`

These identify `codex-cli 0.145.0`, model `gpt-5.6-sol`, sandboxed
noninteractive calls, exact fixed instructions/packet schemas, one call per
trajectory or batch, retry rules, and worker isolation. Step 0087 records 415
calls, 12,050,384 input tokens, 6,008,320 cached input tokens, 231,886 output
tokens, and 116,909 reasoning-output tokens. The paper describes decoding only
as the version-pinned CLI's “default decoding”; no numeric temperature/top-p
exists in the record.

**Qwen3.6-27B task/action backends: strong disclosure.**

- `docs/tmp/build-and-evaluate/step-0031-20260715T182253-0700/experiment-002/experiment-plan.md`
- `docs/tmp/build-and-evaluate/step-0032-20260716T010251-0700/experiment-001/preflight-report.md`

The records identify
`Qwen_Qwen3.6-27B-Q4_K_M.gguf`, size 17,984,872,960 bytes, SHA-256
`8739a0cbb80036e5dbdced2085f142b8ba86e3235db8b8039b3769fe5fc70843`,
llama.cpp server version 9870 commit `2d973636e`, binary SHA-256
`a02cd4c018e0b65dd1dbfcc89db010fbb40359971bc03c697b8133287099b701`,
GPU offload, Jinja, context 4096, parallelism 1, reasoning off/budget 0,
cache disabled, temperature 0, and output budget 8 tokens. Prompts, enumerated
grammars, commands, and three task-family/two action-label repetitions are
retained.

**Older fixed Qwen reader: strong disclosure.**

- `docs/tmp/build-and-evaluate/step-0019-20260714T164922-0700/experiment-001/experiment-plan.md`
- `docs/tmp/build-and-evaluate/step-0019-20260714T164922-0700/experiment-001/full-run.md`

It records the Qwen3.6-27B Q4_K_M path, llama.cpp command, context 65,536,
reasoning off, API model `qwen3.6-27b`, temperature 0, seed `20260714`,
maximum 1,024 output tokens, prompt allowlist, exact-three-group response
contract, and all 66 presentations.

**TraceElephant Grok reader: incomplete disclosure.**

- `docs/tmp/build-and-evaluate/step-0079-20260724T235753-0700/experiment-001/execution-log.md`

The exact CLI recipe is retained:
`--output-format plain --max-turns 3 --tools '' --no-subagents --verbatim`,
with exact packets, prompts, responses, retry string, and harness. The record
only says “grok”/“Grok-family”; it does not pin an exact model ID, CLI version,
provider snapshot, temperature, top-p, or seed.

**HINTBench GLM reader: incomplete disclosure.**

- `docs/tmp/build-and-evaluate/step-0083-20260725T024803-0700/experiment-001/execution-log-v2.md`

It pins opencode `1.17.18`, exact invocation `opencode run --pure`, exact
packet/prompt/parser rules, and the observed banner `glm-5.2`. The model is an
un-pinned default rather than an explicit model flag; provider revision and
numeric decoding settings are absent.

**Historical A2: insufficient disclosure.**

- `docs/tmp/build-and-evaluate/step-0067-20260722T135005-0700/experiment-001/a0-cost-supplement.md`
- `docs/tmp/build-and-evaluate/step-0067-20260722T135005-0700/experiment-001/rq2-trace-independent-review.md`
- `docs/tmp/build-and-evaluate/step-0075-20260723T214459-0700/experiment-001/full-run-and-result.md`

These records explicitly say raw backend outputs and model/provider/token
telemetry are unavailable. The 3,261.89-second A2 artifact-time envelope mixes
inference, scheduling, idle time, and writing and is not model time.

Deterministic recurrence, TF-IDF/K-Means, and Bernoulli Naive Bayes cells do not
need generative decoding parameters, but their code/data/software environment
still needs the normal artifact/version manifest.

**Already in `docs/paper/main.tex`?** Partly. The appendix names Codex CLI
`0.145.0`, `gpt-5.6-sol`, default decoding, retry, and worker isolation. It
names Qwen3.6-27B and high-level closed-label settings but omits the exact
artifact/runtime hashes and most numeric settings. The TraceElephant text says
only “Grok-family CLI reader.” The paper contains no reproducibility disclosure
for the HINT GLM run because that run is not reported.

**Recommendation — add-to-paper:** add a compact reproducibility table and
artifact pointer using the exact retained configurations, and explicitly mark
Grok/A2 fields as unavailable rather than implying that every evaluated backend
is fully reproducible.

## 8. Multiple-run variance for the direct backend — MISSING

Step 0087 contains one annotation per trajectory plus format repairs, not
independent repeated direct-backend runs:

- `docs/tmp/build-and-evaluate/step-0087-20260726T023000-0700/experiment-001/pilot-results.md`
- `docs/tmp/build-and-evaluate/step-0087-20260726T023000-0700/experiment-001/execution-log.md`
- `docs/tmp/build-and-evaluate/step-0087-20260726T023000-0700/experiment-001/independent-result-review.md`
- `docs/tmp/build-and-evaluate/step-0087-20260726T023000-0700/experiment-001/cost-record.md`

The 40-trajectory pilot obtains direct B-cubed F1 `0.752235` and boundary F1
`0.516616`, but the full command reuses those same 40 annotations; it is a
subset/gate, not a second draw. In the complete population, 396 trajectories
have one call, eight have two calls, and ordinal 53 has three calls, for 415
calls total. The ten calls after a trajectory's first are format/session-ID
repairs, not repeated observations. Interrupted valid outputs are also reused
after validation. Consequently there is no same-population, same-config
between-run variance or annotation stability estimate for direct B-cubed,
boundary F1, group count, names, cost, or latency.

The Qwen task-family and action-label backends do have three and two identical
complete runs, respectively, but those repetitions do not answer variance for
the direct `gpt-5.6-sol` structure backend.

**Already in `docs/paper/main.tex`?** No direct-backend variance is reported.
The paper reports identical Qwen literal-label assignments across repetitions,
which is a different backend and output construct.

**Recommendation — run-new-experiment:** run at least two additional complete
direct-backend annotation draws under the frozen configuration and report
run-level metrics plus per-trajectory partition/boundary/name stability.

## 9. Boundary-F1 context for the 0.480 direct result — PARTIAL

The retained review gives confusion counts and a fragmentation diagnosis, but
no near-miss distance or off-by-one analysis:

- `docs/tmp/build-and-evaluate/step-0087-20260726T023000-0700/experiment-001/independent-result-review.md`
- `docs/tmp/build-and-evaluate/step-0087-20260726T023000-0700/experiment-001/score/summary.json`
- `docs/tmp/build-and-evaluate/step-0087-20260726T023000-0700/experiment-001/results.md`

Across 20,461 adjacent pairs, direct annotation has TP `1,592`, FP `2,499`,
FN `951`, and TN `15,419`, yielding precision `0.3891469078464923`, recall
`0.6260322453794731`, and F1 `0.47995176364184505`. It emits 4,496 predicted
leaf groups for 2,948 official stages. The review therefore establishes that
the gain is not indiscriminate contraction—both precision and recall improve
over A2 (`0.290630 / 0.611089 / 0.393916`) and recurrence
(`0.192945 / 0.425875 / 0.265571`)—while absolute precision remains low and the
output remains over-fragmented.

Per-framework direct boundary F1 in the machine-readable summary is:
OpenHands `0.489832`, SWE-agent `0.443418`, Terminus2 `0.447795`, and
mini-SWE-agent `0.519174`. This shows that the 0.480 result is not caused by a
single framework.

No retained analysis measures the signed or absolute operation distance from
each FP/FN to the nearest gold/predicted boundary, tolerance-aware F1 at
`+/-1`, `+/-2`, etc., start-versus-end asymmetry, boundary type, group-length
dependence, or representative near-miss cases. Exact adjacency alone cannot
distinguish an off-by-one semantic transition from an unrelated split.

**Already in `docs/paper/main.tex`?** The paper reports direct boundary F1
`0.480` and recurrence `0.266`, but not direct boundary precision/recall,
confusion counts, predicted-versus-official group counts, framework
heterogeneity, or near-miss analysis.

**Recommendation — run-new-experiment:** perform a deterministic post-hoc
boundary-error analysis over the retained pair/operation rows, then add its
exact/tolerance-aware results and examples to the paper.

## 10. Structured closest-work comparison — FOUND

There is sufficient source-grounded material for a claim-by-claim capability
matrix:

- `docs/background-related-work.md`
- `docs/tmp/build-and-evaluate/step-0072-20260723T193258-0700/01-experiment-gate/baseline-and-closest-work-audit.md`
- `docs/tmp/build-and-evaluate/step-0072-20260723T193258-0700/03-review-gate/milestone-review-001/03-source-grounded-full-paper-assessment.md`
- `docs/tmp/build-and-evaluate/step-0072-20260723T193258-0700/03-review-gate/milestone-review-001/04-current-cycle-change-and-capability-audit.md`
- `docs/tmp/build-and-evaluate/step-0073-20260723T201812-0700/01-experiment-gate/closest-work-and-baseline-audit.md`

The records already identify the appropriate comparison dimensions:
cross-run representation, recursive/variable-depth versus fixed hierarchy,
source/native drilldown, conserved arbitrary additive measures, cross-layer
attribution, cohort comparison, native diagnosis/intervention outcome,
query-time selectable projections, and standard pprof output. They also state
which systems cannot fairly be forced through AgentProf's per-operation MAP or
boundary scorer.

Usable rows and exact scale/details recorded in these files include:

- Hodoscope: 250 trajectories and 11,855 actions in the reproduced corpus;
  LLM summaries/embeddings, cohort density contrast, and human-inspection
  ordering, but no matched AgentProf operation-score contract.
- TraceProbe: 2,500 coding-agent trajectories across five SWE-bench Verified
  settings; canonical actions, deterministic effect labels, process profiles,
  resources, and anti-patterns, but not general cross-layer conserved
  responsibilities or pprof projection.
- Graphectory/OOPSLA 2026: 4,000 SWE-agent/OpenHands trajectories and
  process-centric graph metrics/strategies/intervention; the retained
  distinction is source-linked agent plus OS effects, arbitrary additive
  conservation, and query-selected pprof stacks.
- ACT*ONOMY: a fixed three-level taxonomy with 10 actions, 46 subactions, and
  120 leaves; it is the closest fixed hierarchical behavior-profile comparator,
  but it does not publish compatible complete CodeTrace operation-boundary
  predictions.
- CHIEF: hierarchical task/subtask causal graphs and counterfactual failure
  attribution; it explicitly warns that hierarchy alone is insufficient.
- TraceGraph: shared action-observation decision landscapes with a downstream
  recovery intervention, a stronger consequence claim than visualization
  alone.
- NeMo Agent Toolkit Profiler: the closest named agent profiler for instrumented
  workflows; the recorded residual distinction is heterogeneous completed
  histories, source-linked conserved agent/system effects, and selectable
  pprof-compatible semantic projections.
- Datadog Patterns and LangSmith Insights: production hierarchical
  categorization, metric rollups, search/drilldown, and annotation/dataset
  workflows; generic hierarchical population grouping is therefore not novel.
- GUIDE: 932 industrial e-commerce, 1,302 AgentRewardBench, and 480
  AndroidBench trajectories; task/subtask/diagnosis/result decomposition and
  99.4% model-rated usable descriptions, but not human temporal/nested
  structure gold.
- CodeTracer/CodeTraceBench: 405 trajectories with author stages and
  hierarchical state reconstruction; AgentProf's comparison must be
  cross-trajectory additive profiling rather than first hierarchical trace
  reconstruction.

The Step 0072 audits explicitly recommend native-outcome comparisons or a
capability matrix instead of fabricated numerical adapters. The full-paper
assessment calls the missing claim-by-claim matrix a blocker.

**Already in `docs/paper/main.tex`?** Partly. Related Work contains short
narrative paragraphs naming TraceProbe, Graphectory, ACT*ONOMY, CHIEF,
Hodoscope, TraceGraph, pprof, Pivot Tracing, and observability products. It
does not contain a structured matrix, evidence scale, native outcome, or
claim-by-claim distinction.

**Recommendation — add-to-paper:** turn the existing source-grounded notes into
a compact capability/claim matrix and keep incompatible native outputs as
native-outcome or capability comparisons rather than inventing numerical rows.
