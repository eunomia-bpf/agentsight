# Experiment Plan: RQ2 Standard Localization Metrics

## Research Question

- **RQ exactly as written in the paper:** Does profiler output correspond to
  real problems?
- **Specific uncertainty tested here:** Do the fixed AgentProf operation-stack
  scores rank independently annotated problem steps above the matched
  raw-action view under standard query-level mean average precision on all
  three already-complete public RQ2 workloads?
- **Why the answer matters:** The current paper mixes AP with custom Work@80
  and Work@50 points. A common standard ranking metric would let reviewers
  compare the three workloads directly without discarding the existing
  inspection-work evidence.

## Paper-Value Admission

- **Planned role:** decisive evidence clarification within RQ2.
- **Largest credible paper story unlocked:** AgentProf improves standard
  problem-step ranking over raw-action organization on three complete public
  benchmarks, while workload-specific work curves separately quantify the
  inspection tradeoff.
- **Strongest reject argument addressed:** the current positive RQ2 synthesis
  combines unlike metrics and may therefore reflect selected operating points
  rather than consistent localization quality.
- **Independent evidence added:** a standard MAP reconstruction from every
  target-bearing trajectory and every fixed score, with paired query bootstrap
  uncertainty. It adds no new observation or model output; its value is a
  common, source-grounded analysis of the complete existing evidence.
- **Why it is not tautological or already settled:** group scores are fixed
  without target labels; the scorer opens independent annotations only after
  scores exist. Raw-action, session/native, and atomic-score controls can match
  or beat AgentProf. The current paper has no trajectory-level MAP result.
- **Paper decision if positive:** use MAP as the primary RQ2 metric across the
  three workloads, retain AP/work points as secondary sensitivities, and avoid
  another RQ2 benchmark or model run.
- **Paper decision if contradictory, mixed, or inconclusive:** keep each
  workload's currently reviewed bounded result, do not claim common MAP
  improvement, and do not change RQ2 or its positive hypothesis.
- **Best alternative:** another localization benchmark or score revision would
  add a new information contract after three complete populations already
  exist. Reanalysis has higher decision value and follows the user's explicit
  reuse instruction.

## Expected And Alternative Outcomes

- **Current expected answer:** AgentProf MAP exceeds raw-action MAP on all
  three workloads because recurring semantic groups transfer problem evidence
  across trajectories without using scorer targets.
- **Strongest competing explanation:** the gain is only a consequence of the
  underlying atomic localizer/judge score or of a selected work cutoff, and
  semantic grouping offers no consistent query-level ranking benefit.
- **Contradictory result:** AgentProf MAP is below raw-action MAP on two or
  more complete workloads.
- **Paper-impact boundary:** a contradictory or mixed result bounds this fixed
  ranking construction. It is not a direct challenge to the paper-level thesis
  and does not authorize changing RQ2.

## Published Precedent And Real Assets

- **Metric precedent:** NIST TREC's ranked-list evaluation defines AP for one
  topic and MAP as the arithmetic mean across topics:
  <https://trec.nist.gov/presentations/TREC9/overview/tsld014.htm>.
- **Official metric tool:** `sklearn.metrics.average_precision_score` computes
  non-interpolated AP as recall increments weighted by precision at score
  thresholds:
  <https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html>.
- **Public benchmarks:** AgentProcessBench, HINTBench, and TraceElephant, using
  the exact complete artifacts already reviewed for the current paper.
- **Reused artifacts:** 1,000 AgentProcessBench trajectories / 8,509 labeled
  steps; 536 HINTBench test trajectories / 12,877 steps / 938 official targets
  (935 mapped); and 220 TraceElephant failed trajectories / 5,960 steps / 220
  mapped mistakes.
- **Necessary custom glue:** one read-only analysis command that reconstructs
  fixed per-operation scores from the existing result files, calls the official
  scikit-learn AP implementation per query, performs a paired trajectory
  bootstrap, and writes ordinary raw JSON plus a Markdown report. It invokes no
  model, profiler, tagger, localizer, benchmark generator, or new ranker.

## Comparison

- **Proposed method:** the exact fixed AgentProf operation-stack score already
  used in each complete workload.
- **Main baseline:** the exact matched raw-action grouping and score from the
  same workload. It represents the competing position that visible atomic
  action identity is sufficient and semantic operation stacks add no useful
  recurrence.
- **Why a matched comparison is required:** published results do not report
  these AgentProf scores on these exact operations and annotations; all inputs
  and score signals must be shared for a fair grouping comparison.
- **Controls:** flat/session/source-native organization where available, plus
  the ungrouped atomic localizer or judge-risk score. The atomic control is an
  information/granularity upper control, not a main profile baseline; if it
  wins, the result must say that aggregation improves over raw organization but
  does not dominate direct atomic ranking.
- **Fairness:** within each workload every view uses identical operations,
  fixed visible score signal, scorer labels, and query population. No field,
  score, cutoff, target, or workload is selected from the new MAP result.

## Workloads And Metrics

- **Query:** one trajectory containing at least one independently annotated
  relevant step. Each operation in that trajectory is a ranked item.
- **Relevant item:** AgentProcessBench human label `-1`; mapped HINTBench
  official risk step; or TraceElephant official mistake step.
- **Primary metric:** MAP, the unweighted mean of scikit-learn non-interpolated
  AP over target-bearing trajectories. Equal score values remain tied; no ID,
  timestamp, or file-order tie break enters AP.
- **Primary effect:** paired per-trajectory `AgentProf AP - raw-action AP`,
  reported separately for every benchmark.
- **Uncertainty:** 10,000 paired bootstrap resamples, seed `20260716`, with
  nearest-rank 95% intervals. AgentProcessBench resamples released `task_id`
  clusters within family and carries all target-bearing trajectories of each
  sampled task together; HINTBench resamples target-bearing records within
  environment; TraceElephant resamples traces within cell.
- **Standard secondary metric:** pooled operation AP per benchmark over all
  scoreable operations; this retains nonrelevant steps from zero-target/safe
  trajectories and exposes any query-conditioning advantage.
- **Existing secondary diagnostics:** the already reviewed Work@80/Work@50 and
  Recall-at-work values remain linked but are neither recomputed nor averaged
  with MAP.
- **HINT target coverage:** primary sklearn MAP uses all 935 mapped relevant
  steps across all 400 risky trajectories. A TREC-style sensitivity counts the
  three official but unmappable targets as unretrieved relevant items with zero
  precision contribution. All 136 safe trajectories remain in pooled AP and
  the existing inspection-work result.
- **No-positive queries:** 386 AgentProcessBench trajectories and 136 safe
  HINTBench trajectories have no relevant item, so AP is undefined for them;
  they are excluded from MAP, counted explicitly, and retained in pooled AP.

## Planned Runs

| Run group | Role | Workload | Method matrix | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| preflight | real path | one target-bearing trajectory from each benchmark | AgentProf + raw | 1 | proves all three stored score/target paths execute |
| full | primary | AgentProcessBench | semantic, raw, session, flat, atomic | all 1,000 trajectories | standard MAP/AP evidence |
| full | primary | HINTBench test | AgentProf, raw, session, flat identity, atomic | all 536 trajectories | standard MAP/AP evidence; native remains Work-only because it uses ordinal ordering |
| full | primary | TraceElephant | AgentProf, raw, session, source-native, flat, atomic | all 220 trajectories | standard MAP/AP evidence |
| uncertainty | paired bootstrap | all three complete workloads | AgentProf minus raw | 10,000 per workload | paired 95% intervals |

## Execution

- **Authoritative inputs:**
  - `docs/visexp/out/agentprocessbench-rq2/full/`
  - `docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full/`
  - `.agentsight/experiments/traceelephant-rq2-v1/`
- **Metric implementation:** installed scikit-learn `1.4.1.post1`.
- **Real preflight:** run the same analysis entrypoint in `preflight` mode; it
  must load one real target-bearing trajectory and both fixed scores from each
  of the three artifact families and produce six finite AP values.
- **Full completion:** exactly 1,756 source trajectories and 27,346 operations
  are loaded; MAP covers exactly 614 AgentProcessBench, 400 HINTBench, and 220
  TraceElephant target-bearing queries; every planned view has one AP per
  admitted query; all three pooled AP rows and 30,000 paired bootstrap draws
  finish.
- **Raw-result path:**
  `.agentsight/experiments/rq2-standard-map-existing-trajectories-v1/`.
- **Reports:** this experiment directory keeps one result report and one fresh
  result review; no additional checker, packet, implementation review, or
  control contract is created.

## Interpretation

- **Supported:** the complete-population `AgentProf MAP - raw-action MAP` point
  estimate is greater than zero on all three workloads.
- **Mixed/inconclusive:** one or more point estimates equal zero, or the signs
  are split without raw action winning on at least two workloads.
- **Contradicted:** the point estimate is below zero on at least two of the
  three workloads. This rejects the fixed ranking construction only.
- **Role of intervals:** paired 95% intervals quantify sampling uncertainty
  and are reported beside every effect, but do not override the exact sign rule
  for these three complete released populations. Do not invent a cross-metric
  or cross-benchmark composite score.
- **Target paper table:** one RQ2 table with MAP as the common primary column,
  pooled AP or existing work point as a compact secondary column, and explicit
  atomic-control boundaries. The table enters the paper only after full result
  review.

## Reproducibility Notes

- The source operations, scores, and labels are immutable only in the ordinary
  historical sense that this plan reads the existing completed artifacts; no
  hash binding or freeze protocol is introduced.
- The new command must be read-only with respect to all three source roots and
  may write only its result root plus this step's Markdown reports.
- The paper submodule is never read as an experiment input and is not modified.
