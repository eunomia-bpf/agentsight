# Experiment Plan: RQ3 Same-Model Hierarchy-Depth Ablation

## Research Question

- RQ exactly as written in the paper: **RQ3 — How Accurate Are the Tags?**
- Specific uncertainty tested here: On all 405 CodeTraceBench trajectories,
  how much of Step 0087's adopted GPT-5.6 structural accuracy comes from
  variable-depth complete paths rather than a flat contiguous semantic
  partition produced by the same backend?
- Why the answer matters: A matched flat arm isolates the hierarchy-depth
  contract from model capacity, input evidence, naming format, request
  isolation, canonicalization, and scoring.

The four fixed RQs and the thesis **“Agent observability needs profiling, not
only debugging.”** remain unchanged.

## Paper-Value Admission

- Planned role: decisive mechanism ablation within RQ3.
- Largest credible paper story this experiment could unlock: variable-depth
  responsibility paths contribute measurable partition and boundary accuracy
  beyond same-model semantic segmentation.
- Strongest reviewer reject argument or load-bearing uncertainty addressed:
  Step 0087 may succeed only because GPT-5.6 finds good flat boundaries; the
  hierarchy may add no value.
- Independent evidence added: the first same-model, same-packet, same-request,
  complete-population flat-depth control for the adopted result.
- Why the result is not tautological or already settled: official stages define
  a flat occurrence partition, but neither metric definition nor Step 0087
  guarantees that a multi-level predicted path improves that partition over a
  same-model flat prediction.
- Paper decision if positive: report the matched hierarchy-depth effect as
  supporting the variable-depth constructor on this population.
- Paper decision if contradictory, mixed, or inconclusive: keep the complete
  result and bound or withhold the claim that hierarchy itself explains Step
  0087's gain; do not change RQ3 or the thesis.
- Best alternative experiment: rerunning a direct-hierarchy arm has lower
  decision value because the artifact audit proves Step 0087 already exactly
  implements it.

## Expected And Alternative Outcomes

- Current expected answer: direct hierarchy has higher B-cubed F1 and exact
  boundary F1 than the matched flat arm.
- Strongest competing explanation: complete-trajectory semantic boundary
  selection and GPT-5.6 capacity explain the result, while nested paths add no
  accuracy.
- Contradiction: a wholly negative paired interval on either primary metric
  contradicts the corresponding hierarchy-benefit prediction. Wholly positive
  intervals on both support it; all other combinations are mixed or
  inconclusive and are reported without tuning.

## Published Precedent And Real Assets

- Closest published protocol: CodeTracer/CodeTraceBench supplies the released
  405-trajectory population and 2,948 author stages. GUIDE is the closest
  full-trajectory LLM segmentation precedent.
- Metric precedent: B-cubed is the established per-item hard-partition metric
  of Bagga and Baldwin (ACL 1998); exact boundary precision/recall/F1 is the
  complementary discrete-transition measure already frozen for RQ3.
- Reused assets: exact Step 0087 source packets, direct-hierarchy operation and
  pair rows, frozen assembly/root repair, action-object canonicalization,
  official-stage loading order, correctness checks, and scorer.
- Necessary custom glue: a copy of the Step 0087 runner whose only semantic
  change is the flat-depth contract and whose validator requires exactly two
  labels per path; a paired hierarchy-minus-flat bootstrap/report adapter.

## Comparison

- Proposed method: adopted Step 0087 one-pass direct variable-depth hierarchy.
- Ablation: one-pass direct flat semantic partition from the exact same complete
  packet, with mandatory constant session root plus exactly one non-root
  action-first one-to-three-word interval name.
- Reused direct-hierarchy control: Step 0087, not rerun. The audit proves it is
  complete direct generation without an external STOP/SPLIT controller or
  iterative refinement.
- No recursive/refined-versus-direct comparison will be manufactured: no
  genuinely distinct refined arm exists in the audited adopted artifact.
- Information/tuning/compute fairness: exact `codex-cli 0.145.0`,
  `gpt-5.6-sol`, ignored user config, default reasoning/decoding, one source
  packet and one response per trajectory, read-only ephemeral isolation, four
  workers, 1,200-second timeout, and one format retry. No score-guided prompt,
  depth, canonicalization, scorer, oracle, exclusion, or bootstrap change.

## Workloads And Metrics

- Workload: all 405 fixed CodeTraceBench trajectories, 17,148 source turns,
  20,866 operations, 20,461 adjacent pairs, 2,948 official stages, and 251
  task clusters across four frameworks.
- Primary metrics: ordinary operation-level B-cubed precision/recall/F1 and
  exact adjacent-boundary precision/recall/F1.
- Correctness: all source packets validate; all trajectories reach terminal
  annotation status; predictions cover all operations; operation/token masses
  are conserved; canonicalization retains the temporal partition and zero
  adjacent display-path collisions; official stages are opened only after
  predictions are fixed; stock pprof loads both profiles.
- Uncertainty: 10,000 paired task-cluster bootstrap resamples for
  hierarchy-minus-flat on each metric, using the frozen Step 0087 seeds:
  `20260720` for B-cubed F1 and `20260722` for boundary F1.
- Secondary reporting: group/mark counts, raw and canonical name counts, raw
  and assembled depth distributions, format failures/retries, calls,
  input/cached-input/output/reasoning tokens, summed and union-active request
  time, and end-to-end wall time.
- Cost estimate: approximately 405--810 Codex calls and the Step 0087 order of
  12 million input tokens; no new direct-hierarchy calls.

## Planned Runs

| Run group | Role | Workload | System/method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| preflight | operational control | smallest real Step 0087 packet | GPT-5.6 flat arm plus frozen pipeline | 1 | proves the real path only |
| direct hierarchy | reused control | complete 405 | frozen Step 0087 | 1 complete retained population | supplies matched comparator |
| flat | hierarchy-depth ablation | complete 405 | GPT-5.6 direct flat partition | 1 request policy per trajectory | isolates hierarchy-depth effect |

## Execution

- Authoritative workflow:
  `flat_annotation/annotate.py prepare`, then `preflight`, then
  `flat_annotation/postprocess.py preflight`; after a valid preflight,
  `flat_annotation/annotate.py full --workers 4 --timeout-seconds 1200`,
  `flat_annotation/annotate.py package`, and
  `flat_annotation/postprocess.py full`.
- Real preflight: the minimum-turn real trajectory selected from the exact
  sorted Step 0087 packet population, using the real GPT-5.6 backend and actual
  frozen pipeline/scorer.
- Full completion: all 405 trajectories have terminal valid flat annotations
  under the declared retry policy and every correctness check passes before any
  complete-population interpretation.
- Raw path: this `experiment-001` directory, including per-attempt Codex JSONL
  and stderr, per-trajectory marks, run records, assembled/canonical artifacts,
  profiles, score rows, bootstrap draws, and reports.
- Recovery: validate and reuse only already-complete per-trajectory outputs;
  never interpret a partial prefix. A recorded mechanical repair may replace
  an otherwise-valid exact session ID or delete a transition mark whose
  complete path is identical to the preceding mark. The latter is accepted
  only when expanding both responses proves every operation path unchanged.
  Other terminal errors leave the arm incomplete and forbid partial scoring.

## Interpretation

- Positive: both hierarchy-minus-flat 95% intervals are wholly positive.
- Contradictory: either primary interval is wholly negative for its claimed
  effect; report the metric-specific contradiction and overall mixed result if
  the other metric differs.
- Mixed/inconclusive: intervals cross zero or metric directions disagree.
- Target paper table: direct hierarchy and flat rows with P/R/F1, counts,
  depths, paired deltas/intervals, and cost; no paper edit in this experiment.

## Reproducibility Notes

- Software/data: installed standalone
  `/home/yunwei37/.codex/packages/standalone/releases/0.145.0-x86_64-unknown-linux-musl/bin/codex`,
  `gpt-5.6-sol`, exact Step 0087 source packets and downstream scripts.
- Configuration: no user config, no decoding or reasoning override, four
  workers, 1,200-second request timeout, one ordinary format retry, bootstrap
  seeds `20260720` (B-cubed) and `20260722` (boundary).
- Known deviation: the currently selected `codex` executable is 0.146.0, so
  this experiment explicitly invokes the retained 0.145.0 binary used by Step
  0087. The direct hierarchy is reused rather than rerun.
