# Experiment Plan: RQ3 CodeTraceBench Stage Fidelity

## Research Question

- **RQ exactly as written in the paper:** **RQ3: How accurate are the tags?**
- **Specific uncertainty tested here:** Does the unchanged label-free
  recurrence constructor recover independently annotated stage boundaries and
  partitions on real code-agent trajectories outside its OSWorld-Human
  development corpus?
- **Why the answer matters:** The release implementation currently has strong
  same-corpus mechanism evidence but no untouched cross-family confirmation.

## Paper-Value Admission

- **Planned role:** decisive.
- **Largest credible paper story this experiment could unlock:** one simple
  recurrence principle constructs useful operation groups across both GUI and
  code-agent trajectories without target labels or per-family tuning.
- **Strongest reviewer reject argument addressed:** the current constructor may
  merely fit OSWorld-Human's grouping convention after its failures were seen.
- **Independent evidence added:** complete source-authored CodeTraceBench stage
  partitions on 405 source-valid failed trajectories from four frameworks;
  these stages were not used to design the recurrence objective.
- **Why it is not tautological or already settled:** the constructor sees only
  session order and the existing nine-way visible `action_kind`; official
  stage intervals remain scorer-only. Unlike the rejected AndroidControl and
  GUI-Odyssey action cells, the scored stage partition is not the input field.
- **Paper decision if positive:** report CodeTraceBench as independent
  cross-family stage-partition confirmation for the unchanged release
  recurrence path, without changing the thesis or RQs.
- **Paper decision if contradictory, mixed, or inconclusive:** retain the fixed
  RQ3 hypothesis and record a code-agent stage boundary for this constructor;
  do not tune CodeTraceBench or rewrite the story from one result.
- **Best alternative:** a new annotated family could test the same gap, but
  CodeTraceBench has higher decision value because the official data, stage
  annotations, source-exact operations, four-framework population, and real
  full-run artifacts are already present.

## Expected And Alternative Outcomes

- **Current expected answer:** recurrence exceeds the strongest simple control
  on both pooled boundary F1 and operation-weighted B-cubed partition F1.
- **Strongest competing explanation:** source-authored stages reflect long
  task-progress regions whose boundaries are better represented by a direct
  action-change or external phase-change rule than by recurring local motifs.
- **Contradictory result:** recurrence matches or trails the best control on
  both primary metrics. Improvement on only one primary metric is mixed.

## Published Precedent And Real Assets

- **Closest published protocol:** CodeTraceBench's official consecutive
  stage-interval annotations and CodeTracer's released target-blind two-way
  `phase` classification; partition agreement uses B-cubed
  precision/recall/F1 as in the already cited Bagga--Baldwin protocol.
- **Official assets:** `NJU-LINK/CodeTraceBench` manifests already stored under
  `.agentsight/experiments/codetracebench-rq2/manifests/`; CodeTracer checkout
  `2d302191dd07e7c0c2da6f7a5e9451c7cbb62d34`; existing source-exact operation
  files under `docs/visexp/out/codetracebench-rq2/full/`.
- **What is reused:** all normalized reference and target operations, the
  existing source-alignment audit, official stage intervals, the release Rust
  recurrence implementation, and the Step 0020 boundary/B-cubed scorer
  definitions.
- **Necessary custom glue:** one adapter/scorer renames `traj_id` to `session`
  and the pre-existing project-derived `action_kind` to `action`, removes
  target sessions from the label-free reference population, invokes the
  existing Rust path, and joins official stages only after predictions exist.
  `action_kind` is the fixed nine-way deterministic mapping in
  `script/codetracebench_agentprof_eval.py`, not CodeTracer's released
  classifier. The adapter writes only unit `value` plus
  `fields.{session,action}` into both Rust input files; `phase`,
  `raw_action_key`, and official `stages` are all absent. It does not implement
  a new constructor.

## Comparison

- **Proposed method:** unchanged release `--induce-operation-stack` recurrence
  using 2,229 disjoint reference sessions / 87,703 operations and all 405
  target sessions / 20,866 operations.
- **Main baseline:** CodeTracer phase-change, representing the released
  external target-blind two-phase classifier already computed on exactly these
  operations. A matched run is needed because published CodeTracer results do
  not report agreement with CodeTraceBench stage partitions.
- **Controls:** action-change, always-boundary, and session-one-block. They
  represent direct visible-field segmentation and the fragmentation/merging
  extremes; they are not presented as competing systems.
- **Conclusion if the main baseline wins:** transition recurrence does not add
  stage-partition fidelity beyond the external phase classifier on this family.
- **Fairness:** every method receives the same target order and unit weights,
  and no method sees or tunes on official target stages. The recurrence input
  is only the compressed nine-way project-derived `action_kind`, while the
  external phase-change baseline was previously classified from the richer raw
  action text by CodeTracer. This conservative information asymmetry favors
  the baseline rather than recurrence. The 405 target IDs are absent from
  recurrence reference statistics.

## Workloads And Metrics

- **Real workload:** all 405 source-valid failed CodeTraceBench target
  trajectories already used by the completed full RQ2 run, spanning
  OpenHands, SWE-agent, Terminus2, and mini-SWE-agent.
- **Primary metrics:** pooled boundary precision/recall/F1 and
  operation-weighted B-cubed partition F1 over all 20,866 operations.
- **Correctness ground truth:** official `stages` intervals from the verified
  manifest; each interval set must exactly cover steps `1..step_count` before
  scoring.
- **Secondary diagnostics:** per-framework primary metrics, predicted segment
  count, motif count, unseen transition count, and exact operation-weight
  conservation. These cannot change the primary verdict.
- **Repetitions and uncertainty:** deterministic complete-population run; no
  stochastic seed or sampling interval is needed. Framework breakdown exposes
  concentration without becoming four separate experiments.
- **Cost:** local CPU only; the existing operations avoid model calls and raw
  trajectory reprocessing.

## Planned Runs

| Run group | Role | Workload | Method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| preflight | path check | one real target session plus disjoint real reference | recurrence + all controls + official-stage scorer | 1 deterministic | establishes only that the real path executes |
| full | proposed | all 405 targets | unchanged Rust recurrence | 1 deterministic | tests the declared hypothesis |
| full | baseline/control | identical targets | phase-change, action-change, always-boundary, session-one-block | 1 deterministic each | determines whether recurrence adds stage fidelity |

## Execution

- **Authoritative workflow:**

  ```bash
  python3 script/rq3_codetracebench_stage_fidelity_eval.py preflight \
    --agentpprof-bin agentpprof/target/release/agentpprof \
    --reference-operations docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl \
    --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
    --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
    --out .agentsight/experiments/rq3-recurrence-codetracebench-v1/preflight

  python3 script/rq3_codetracebench_stage_fidelity_eval.py full \
    --agentpprof-bin agentpprof/target/release/agentpprof \
    --reference-operations docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl \
    --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
    --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
    --out .agentsight/experiments/rq3-recurrence-codetracebench-v1/full
  ```
- **Real preflight:** the lexicographically first target session, scored against
  its complete official stages, while learning from the complete target-
  disjoint reference population.
- **Full completion rule:** exactly 405 target sessions and 20,866 operations;
  every target step is scored once; all five methods complete; reference/target
  IDs are disjoint; official stages cover every target operation; all 20,866
  units are conserved; raw decisions and summary are written.
- **Raw-result path:**
  `.agentsight/experiments/rq3-recurrence-codetracebench-v1/`.
- **Recovery:** deterministic rerun of the affected mode; no checkpoint or
  experiment-control layer is needed.

## Interpretation

- **Positive:** recurrence has strictly higher boundary F1 and B-cubed F1 than
  every baseline/control on the complete population.
- **Negative:** it matches or trails the best alternative on both metrics.
- **Mixed:** a valid complete run improves exactly one primary metric.
- **Invalid or incomplete:** a source, coverage, execution, or conservation
  defect prevents the declared complete population from being scored.
- **Target paper table:** one compact cross-family constructor row or table
  extension, added only after valid independent result review.

## Reproducibility Notes

- Software and data versions are the current release Rust binary, CodeTracer
  commit above, and the already-downloaded CodeTraceBench manifests and
  operation files.
- The recurrence algorithm, tie rule, cutoff, and feature are exactly those in
  Step 0020; no seed or search exists.
- The only deviation from the prior RQ2 files is scientifically required:
  target IDs are removed from the label-free recurrence reference population.
