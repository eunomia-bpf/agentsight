# Experiment Plan: RQ1 Independent Stage Attribution

**Proposed:** 2026-07-16T20:02:00-07:00

## Research Question

- **RQ exactly as written in the paper:** **RQ1 — Does Semantic Profiling
  Improve Resource Attribution?**
- **Specific uncertainty tested here:** Whether the unchanged current
  recurrence operation stack groups operations according to an independently
  human-defined stage partition more faithfully than a matched source-native
  raw-action view over exactly the same operations, and whether the same result
  holds when expensive operations receive their measured token weight.
- **Why the answer matters:** Existing R114 evidence proves source lineage and
  additive conservation, but not independent semantic responsibility. Existing
  R170 mixedness uses the grouping tag as its own reference. A positive result
  here supplies non-circular, same-input attribution evidence for the original
  profiling claim without changing the story or algorithm.

## Paper-Value Admission

- **Planned role:** decisive RQ1 evidence.
- **Largest credible paper story this experiment could unlock:** AgentProf's
  semantic operation stacks do not merely conserve resource counters; on real
  heterogeneous agent executions they place observed token consumption closer
  to independently human-verified units of work than a non-semantic operation
  view.
- **Strongest reviewer reject argument addressed:** Resource attribution is
  currently supported by lossless folding and a circular tag-based analysis,
  so the paper has not shown that its hierarchy assigns expensive work to the
  right semantic responsibility.
- **Independent evidence added:** Human-verified CodeTraceBench stage
  partitions, standard B-cubed agreement, and a secondary provider-token-
  weighted B-cubed analysis. None is produced by AgentProf's partition.
- **Why this is not tautological or already settled:** The recurrence
  constructor sees only reference operations and visible action fields. It
  never sees target stages or token weights. Step 0024 reports unit-operation
  stage fidelity, not the distribution of actual resource mass.
- **Paper decision if positive:** Add standard B-cubed as the main independent
  RQ1 attribution result; use token-weighted B-cubed only to show whether the
  structural result also covers expensive operations. Retain R114 as source-
  fidelity evidence and demote R170 to a descriptive diagnostic.
- **Paper decision if contradictory:** Preserve the fixed thesis and RQ, record
  that the current recurrence constructor does not improve token-mass
  attribution over raw actions on CodeTraceBench, and route the mechanism
  boundary to WRITE/REVIEW. Do not weaken or replace the hypothesis inside the
  experiment.
- **Paper decision if mixed or inconclusive:** Report which framework or
  resource component causes the difference and keep RQ1 only partially
  answered; do not select another benchmark merely to seek a positive row.
- **Best alternative:** New manual responsibility annotations on R114's 20
  Codex tasks. The current experiment has higher decision value because it uses
  an existing official human-verified benchmark, four real frameworks, the
  complete pre-existing 405-trajectory source-valid target, and recorded usage
  without inventing labels or rerunning agents.

## Tested Hypothesis And Outcomes

> **H-RQ1.** On the complete pre-existing 405-trajectory CodeTraceBench
> source-valid target population, the unchanged current recurrence operation
> stack achieves higher ordinary operation-level B-cubed F1 against the
> official human stage partition than the matched contiguous `raw_action_key`
> view over the same 20,866 operations.

- **Current expected answer:** unknown. The existing `0.473242` comparison is
  against normalized action-kind change, not the newly corrected source-native
  `raw_action_key` baseline, so it cannot pre-answer this hypothesis.
- **Strongest competing explanation:** Source-native action identity already
  captures the human stage partition, so recurrence adds no grouping advantage;
  alternatively, any ordinary improvement may exclude high-token operations.
- **Contradictory result:** recurrence's pooled ordinary B-cubed F1 is no higher
  than raw-action-key change on the complete measured target.
- **Inconclusive result:** the ordinary point delta is positive but the paired
  task-cluster-bootstrap 95% interval includes zero, or the validity/sensitivity
  checks cannot support a stable comparison.
- **Paper-impact scope:** A contradiction bounds this constructor and workload;
  it is not by itself a direct challenge to the fixed paper thesis or the whole
  RQ.

## Published Precedent And Real Assets

- **Primary partition metric:** Bagga and Baldwin's established
  [B-cubed](https://aclanthology.org/P98-1012/) precision/recall/F1 with one
  uniform unit per operation.
- **Resource-weighted extension:** the published
  [weighted B-cubed](https://pmc.ncbi.nlm.nih.gov/articles/PMC5103821/)
  formulation, instantiated with measured token counts instead of contig
  length. Uniform operation weights must reduce to ordinary B-cubed.
- **Official benchmark:**
  [NJU-LINK/CodeTraceBench](https://huggingface.co/datasets/NJU-LINK/CodeTraceBench)
  and the [CodeTracer paper](https://arxiv.org/abs/2604.11641).
- **Reused local assets:** verified manifest and raw archives under
  `.agentsight/experiments/codetracebench-rq2/`; 20,866 target operations under
  `docs/visexp/out/codetracebench-rq2/full/`; unchanged Step 0024 assignments
  under `.agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/full/`.
- **Necessary custom glue:** one read-only adapter joins released usage records
  to official operations and one scorer computes ordinary and published
  weighted B-cubed. It does not infer stages, change partitions, tune a cutoff,
  or execute an agent.

## Comparison

- **Proposed method:** current Step 0024 `recurrence` operation-stack
  assignments, unchanged.
- **Main baseline:** a matched contiguous partition whose boundary fires when
  the already-materialized source-native `raw_action_key` changes. It represents
  the competing claim that ordinary operation identity is enough to attribute
  work.
- **Controls:** `session_one_block` (no within-run hierarchy) and
  `always_boundary` (one operation per block) bound over- and under-segmentation.
- **Ablations:** the existing `action_change` assignment is reported accurately
  as normalized **action-kind change**, and `phase_change` measures whether one
  visible phase field explains the result. Neither replaces the predeclared
  recurrence-versus-raw-action-key test.
- **If the raw-action-key baseline matches or wins:** The experiment contradicts H-RQ1 and the
  current constructor cannot support the claimed improvement on this workload.
- **If the phase ablation wins:** Semantic profiling may still outperform raw
  action, but recurrence adds no RQ1 attribution advantage over phase-only on
  this population; WRITE must state that mechanism boundary.
- **Fairness:** Every row uses identical session/step IDs, provider usage,
  official stages, and no tuning. Token weights and stages are loaded only for
  scoring; the materialized recurrence assignments remain the already-complete
  Step 0024 output.

## Workloads And Metrics

- **Population:** the complete pre-existing 405-trajectory source-valid target,
  selected before this token analysis from 468 failed released trajectories:
  213 OpenHands, 93 Terminus2, 71 mini-SWE-agent, and 28 SWE-agent; 20,866
  operations, 2,948 official stages, and 251 distinct benchmark tasks. The 63
  excluded trajectories are described in the asset screen and are not rebuilt.
- **Primary metric:** pooled ordinary operation-level B-cubed precision, recall,
  and F1. The hypothesis is decided by F1; precision and recall explain mixing
  versus fragmentation.
- **Resource-sensitive secondary metric:** pooled total-token-weighted B-cubed
  precision, recall, and F1. It tests whether the standard structural result
  also holds for expensive operations. It cannot rescue a failed primary
  result; a nonpositive allocation-stable weighted direction makes an otherwise
  positive structural result mixed rather than positive resource-attribution
  evidence.
- **Reproduction check:** the recurrence, phase-change, action-kind-change,
  always-boundary, and session-block ordinary B-cubed values must reproduce the
  existing Step 0024 summary within `1e-12`; raw-action-key is newly scored from
  the same already-materialized operation field.
- **Ground truth:** official session-qualified human stage membership. Stages
  are never treated as a shared named taxonomy.
- **Correctness:** exactly 405 sessions and 20,866 unique `(session, step_id)`
  joins; positive usage for every operation; provider call totals conserved
  when a response is shared or retries are aggregated; no target stage or token
  field reaches construction.
- **Selection audit:** report 405/468 coverage and the already-measured included
  versus excluded framework and step-count summary; do not reconstruct excluded
  data.
- **Multi-operation validity:** report the number and token mass of responses
  shared by multiple operations and whether those operations cross gold,
  recurrence, or raw-action-key partitions. If crossings exist, recompute the
  weighted secondary analysis under equal, all-to-first, and all-to-last
  allocation; allocation-dependent conclusions are inconclusive.
- **Uncertainty:** deterministic paired task-cluster bootstrap with 10,000
  resamples and seed `20260716`; resample the 251 distinct tasks and retain all
  of each task's trajectories, qualifying duplicated cluster identities within
  a replicate. Recompute the pooled ordinary B-cubed F1 delta for recurrence
  minus raw-action-key change. This is analysis of the measured population, not
  repeated agent execution.
- **Secondary breakdowns:** the same weighted B-cubed rows by framework and by
  prompt-token versus completion-token weights. They explain heterogeneity and
  do not replace the predeclared ordinary B-cubed primary result.
- **Cost:** no model/API/agent execution; local parsing and scoring only.

## Planned Runs

| Run group | Role | Workload | Method/view | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| preflight | real path check | one real target from each of the six source forms | all existing views | 1 deterministic pass | establish that official raw usage, assignments, stages, and weighted B-cubed run end to end |
| full main | proposed | complete source-valid 405 / 20,866 | recurrence | 1 deterministic pass | primary ordinary B-cubed H-RQ1 value |
| full matched | main baseline | same complete population | raw-action-key change | 1 deterministic pass | decide H-RQ1 delta |
| full controls | controls | same complete population | session block; always boundary | 1 deterministic pass | bound degenerate partitions |
| full ablations | ablations | same complete population | action-kind change; phase change | 1 deterministic pass | identify whether recurrence adds beyond individual visible semantic fields |
| paired uncertainty | inference | same complete population | recurrence minus raw-action-key change | 10,000 task-cluster resamples | 95% interval for the primary ordinary B-cubed delta |

## Execution

- **Authoritative workflow:** reuse the official raw archives and already-
  materialized Step 0024 assignments; add only
  `script/rq1_codetracebench_token_attribution_eval.py` as the necessary source
  adapter and scorer.
- **Real preflight command:**

  ```bash
  python3 script/rq1_codetracebench_token_attribution_eval.py \
    --mode preflight \
    --output .agentsight/experiments/rq1-codetracebench-token-attribution-v1/preflight
  ```

- **Full command:**

  ```bash
  python3 script/rq1_codetracebench_token_attribution_eval.py \
    --mode full \
    --output .agentsight/experiments/rq1-codetracebench-token-attribution-v1/full
  ```

- **Full completion rule:** both commands exit zero; the full output covers all
  declared sessions/operations/stages and every planned view, resource
  component, framework breakdown, task-cluster bootstrap resample, selection
  audit, and multi-operation allocation audit; raw operation usage, per-session
  sufficient statistics, `summary.json`, and `report.md` are present.
- **Raw-result path:**
  `.agentsight/experiments/rq1-codetracebench-token-attribution-v1/{preflight,full}/`.
- **Recovery:** source archives and Step 0024 assignments are reused without
  modification. Parsing is deterministic and cheap enough to rerun the affected
  command after a defect; no checkpoint or freezing system is added.

## Interpretation

- **Supported:** recurrence ordinary operation-level B-cubed F1 is higher than
  raw-action-key change and the paired task-cluster-bootstrap 95% interval for
  the delta is strictly above zero, with complete valid joins and reproduction.
  This supports the intended RQ1 resource-attribution statement only when the
  allocation-stable total-token-weighted B-cubed F1 delta is also positive.
- **Contradicted:** recurrence ordinary B-cubed F1 is no higher than raw-action-
  key change on the complete measured target while the run remains valid.
- **Mixed:** the ordinary-primary result is supported, but the allocation-
  stable token-weighted F1 delta is nonpositive. This may be written as improved
  stage structure, not as improved token/resource attribution.
- **Inconclusive:** the ordinary point delta is positive but its interval
  includes zero; or source/usage coverage, unit-weight reproduction, mass
  conservation, allocation sensitivity, or comparison fairness fails and
  cannot be repaired without changing this plan.
- **Target paper table:** one compact RQ1 table with recurrence, raw-action-key,
  action-kind and phase ablations, and the two controls; ordinary B-cubed
  P/R/F1 as the main columns and token-weighted B-cubed F1 as the resource-
  sensitive secondary column. Framework and token-component breakdowns remain
  appendix/internal unless needed to explain the result.

## Reproducibility Notes

- Current repository commit at proposal: `26ed64d3c48a606516977ab696894fba8c0744bf`.
- Existing assignments report `agentpprof 0.2.37` and the complete Step 0024
  population.
- Official dataset contents are the already-downloaded CodeTraceBench release
  referenced by the verified manifest; no source is modified.
- Bootstrap seed is fixed only for repeatability; no model or algorithm seed is
  involved.
- The read-only `docs/agentpprof-paper` submodule is outside the experiment and
  remains untouched.
