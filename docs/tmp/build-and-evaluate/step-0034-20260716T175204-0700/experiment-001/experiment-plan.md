# Experiment Plan: RQ3 Cross-Domain Calibration Of Existing Recurrence Scores

## Research Question

- **RQ exactly as written in the paper:** **RQ3: How accurate are the tags?**
- **Specific uncertainty tested here:** Whether a group-annotation budget from
  one trajectory domain can improve the unchanged recurrence constructor in a
  different target domain when NPMI scores are expressed as within-reference
  empirical percentiles, without target-domain group labels.
- **Why the answer matters:** The current label-free constructor is selected
  post-hoc on OSWorld-Human and CodeTraceBench, and Step 0030 improves it by
  fitting a different raw NPMI cutoff inside each domain. The raw selected
  cutoffs have incompatible scales. Transferable calibration would give the
  automatic constructor a simpler cross-domain result on the complete reused
  populations; failure would show that grouped calibration remains
  domain-specific.

## Paper-Value Admission

- **Planned role:** supporting RQ3 mechanism/generalization evidence.
- **Largest credible paper story this experiment could unlock:** The same
  recurrence principle can use grouped historical trajectories from one agent
  domain to construct better operation stacks in another domain after only an
  unlabeled distributional normalization, rather than requiring target-domain
  group labels or a benchmark-specific threshold.
- **Strongest reviewer reject argument or load-bearing uncertainty addressed:**
  Current automatic grouping may be only a post-hoc per-corpus calibration;
  NPMI cutoffs learned on existing domains differ from `-0.0982` to `0.4151`.
- **Independent evidence added beyond existing runs and published results:**
  Steps 0024/0030 use target-domain visible references and, for calibration,
  target-domain grouped references. This experiment transfers the calibration
  decision across OSWorld-Human and CodeTraceBench while withholding every
  target-domain group label until prediction is complete. Published work
  establishes the protocol class but not this AgentProf score or population.
- **Why the result is not tautological, already settled, or dominated:** A
  monotone percentile transform cannot improve in-domain threshold fitting;
  its only possible value is cross-domain scale comparability. Both transfer
  directions have complete existing populations and can fail independently.
- **Paper decision if positive:** Adopt percentile-scale calibration as the
  grouped-reference interface, implement it in the current recurrence path,
  and replace the per-domain calibration row with cross-domain RQ3 evidence.
- **Paper decision if contradictory, mixed, or inconclusive:** Keep the Step
  0024 label-free default and the Step 0030 per-domain optional calibration;
  record that grouped calibration does not transfer under this correction. Do
  not change RQ3, its positive hypothesis, the thesis, or the story, and do not
  try another normalization or target-specific threshold in this branch.
- **Best alternative experiment and why this one has higher decision value:**
  Another RQ2 grouping comparison is redundant after Step 0033; another
  task/action taxonomy cell does not improve the constructor; another
  action-pair feature or local cutoff is barred by Steps 0025--0026. This
  experiment directly attacks the current constructor's largest RQ3 limitation
  using the exact already-run trajectories requested by the user.

## Expected And Alternative Outcomes

- **Current expected answer:** Occurrence-weighted empirical percentiles make
  the existing recurrence cutoff more transferable than a raw NPMI scalar and
  improve or preserve target B-cubed F1 relative to label-free recurrence in
  both transfer directions.
- **Strongest competing explanation:** The two domains encode different group
  semantics, not merely different NPMI scales; no monotone score normalization
  can transfer the desired boundary policy.
- **Result that would contradict the expectation:** Percentile transfer lowers
  target B-cubed F1 below label-free recurrence on either complete target
  population, or fails to improve over direct raw-cutoff transfer.
- **Paper-impact boundary:** A contradiction bounds this calibration mechanism
  and these domains. It is not a direct challenge to the profiling thesis, the
  operation/operation-stack model, or the whole RQ3 hypothesis.

## Published Precedent And Real Assets

- **Closest published protocol:** Perini, Vercruyssen, and Davis, AAAI 2022,
  transfer a threshold-related contamination quantity from a labeled source to
  an unlabeled target using score-distribution shape
  (<https://doi.org/10.1609/aaai.v36i4.20331>). Sedova and Roth, ACL 2023,
  treat limited-label threshold calibration as an explicit information budget
  (<https://aclanthology.org/2023.acl-short.158/>). Huang et al., EMNLP 2024,
  motivate rank-based comparison for differently scaled scores
  (<https://aclanthology.org/2024.emnlp-main.18/>).
- **Official system/data/tool and version:** AgentProf `0.2.37`; all 287
  OSWorld-Human sessions from the public OSWorld-Human artifact; the existing
  CodeTraceBench extraction containing 2,229 score-reference sessions, 483
  disjoint solved calibration sessions, and 405 failed target sessions across
  four frameworks; standard B-cubed and boundary F1 definitions.
- **What is reused:** Existing operation JSONL, stage/group annotations,
  source-valid selection, current NPMI function, current label-free predictions,
  Step 0030 per-domain calibration results, fold assignments, and standard
  metric code.
- **Necessary deviations or custom glue:** One thin Python adapter imports the
  existing loaders and scorer, adds an occurrence-weighted empirical-CDF map,
  performs the two source-to-target transfers, and writes ordinary JSON/JSONL
  plus Markdown. It does not collect data, invoke a model, create labels,
  change NPMI, or tune on target metrics. If and only if the registered positive
  rule passes, the same percentile transform is added to the existing Rust
  grouped-reference calibration path and replayed on the complete matrix.

## Comparison

- **Proposed method:** Keep the current action-transition NPMI association.
  For domain `D`, let `R_D` be every transition occurrence in its unlabeled
  score-reference sessions and `s_D(a,b)` the current NPMI score. Define
  `F_D(x) = |R_D|^{-1} sum_{r in R_D} 1[s_D(r) <= x]`. Source grouped
  operations select one threshold `q` over the finite observed `F_D` values by
  maximum operation-weighted source B-cubed F1, with the existing smallest-
  threshold tie rule. In the target domain, an observed transition continues
  its group iff `F_target(s_target) >= q`; unseen transitions remain boundaries.
- **Main baseline:** Current Step 0024 label-free recurrence on the identical
  target folds/population. It represents the competing position that each
  target's unlabeled score distribution is sufficient and grouped source data
  adds no transferable value.
- **Why a matched run is needed:** Published results cannot determine how the
  same AgentProf recurrence score behaves under the two target reference
  distributions; the exact target operations and fold/reference rules must be
  held identical.
- **Normalization ablation:** Transfer the source-selected raw NPMI cutoff
  directly to the target association, with all other information unchanged.
  This isolates whether the empirical-CDF scale correction matters.
- **Upper-bound control:** Existing Step 0030 per-domain grouped-reference
  calibration. It spends target-domain annotations and is not an equal-
  information main baseline.
- **Context-only controls:** Existing action-change, phase-change,
  always-boundary, and supervised-predictor rows are not rerun because they do
  not test calibration transfer.
- **Conclusion if the main baseline matches or wins:** Cross-domain grouped
  calibration adds no usable information under the candidate correction; keep
  label-free recurrence as the default.
- **Information, tuning, and compute fairness:** Candidate and raw-transfer
  ablation use the same source labels, target visible actions, target unlabeled
  score reference, target sessions, and one scalar decision. The target oracle
  is unavailable to both until all predictions are persisted. Label-free uses
  no source labels and is therefore the lower-information operational default;
  the upper-bound control is explicitly higher-information.
- **Split and leakage rule:**
  - OSWorld -> CodeTraceBench fits source thresholds using all grouped OSWorld
    sessions, computes target CDF values only from the existing 2,229
    CodeTraceBench score-reference sessions, predicts all 405 failed sessions,
    persists predictions, and only then loads failed-session stages.
  - CodeTraceBench -> OSWorld fits source thresholds from the existing 2,229
    score-reference plus 483 disjoint solved grouped sessions. Each OSWorld
    target fold computes its CDF from the other four folds' visible action
    transitions, predicts its held-out sessions once, persists predictions, and
    only then loads that fold's human groups.

## Workloads And Metrics

- **Real workloads:** Complete OSWorld-Human (287 sessions, 3,978 operations,
  3,691 adjacent pairs, 2,042 human groups) and complete source-valid failed
  CodeTraceBench target (405 sessions, 20,866 operations, 20,461 adjacent pairs,
  2,948 stages), with the existing solved/reference populations above.
- **Primary metric:** Operation-weighted B-cubed partition F1 on each complete
  target population. No cross-dataset composite is formed.
- **Secondary metrics:** Boundary precision/recall/F1, predicted group count,
  unseen-pair rate, and the percentile/raw cutoff values. Secondary metrics
  describe merging and fragmentation and do not override the primary partition
  claim unless they expose invalid execution or information leakage.
- **Correctness checks:** Exact expected population counts; every target
  operation assigned once; every target pair predicted once; target labels
  loaded only after prediction persistence; finite monotone CDF values in
  `[0,1]`; identical target rows across candidate/baselines; all additive units
  conserved when a supported candidate is replayed through AgentProf.
- **Uncertainty:** 10,000 paired target-session bootstrap draws, stratified by
  the five OSWorld folds and four CodeTraceBench frameworks, seed `20260716`.
  Each interval is the empirical 2.5th--97.5th percentile interval of the
  paired B-cubed F1 deltas. Intervals are reported for candidate-minus-label-
  free and candidate-minus-raw-transfer B-cubed F1. Full-population values
  remain the primary effect estimates, while the intervals determine whether
  their ordering is supported or inconclusive under the rules below.
- **Cost estimate:** No collection or model inference. Preflight should finish
  in seconds; the complete Python analysis and bootstrap should finish within
  minutes. The conditional Rust port/replay is bounded to the same two complete
  populations.

## Planned Runs

| Run group | Role | Target workload | Source calibration | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| OS->CT | proposed | 405 CodeTraceBench failed sessions | all grouped OSWorld-Human sessions | complete population + 10k bootstrap | Tests cross-domain percentile transfer into four code-agent frameworks |
| OS->CT | ablation | same | raw OSWorld NPMI cutoff | same | Isolates percentile normalization |
| OS->CT | main baseline | same | none; current target label-free recurrence | same | Tests whether source groups add target value |
| CT->OS | proposed | all five held-out OSWorld folds | grouped CodeTraceBench solved sessions | complete population + 10k bootstrap | Tests reverse transfer into GUI-agent tasks |
| CT->OS | ablation | same | raw CodeTraceBench NPMI cutoff | same | Isolates percentile normalization |
| CT->OS | main baseline | same | none; current target label-free recurrence | same | Tests whether source groups add target value |
| both | upper-bound control | both targets | existing target-domain grouped calibration | existing complete result | Bounds attainable gain with target-domain annotations |

## Execution

- **Authoritative workflow:**
  `python3 script/rq3_cross_domain_percentile_calibration_eval.py --mode
  {preflight,full} --out
  .agentsight/experiments/rq3-cross-domain-percentile-calibration-v1/{preflight,full}`.
- **Real preflight case:** One real OSWorld target fold/session and one real
  CodeTraceBench failed target session, using the full source calibration and
  target-reference paths, must emit candidate, raw-transfer, and label-free
  predictions plus finite B-cubed inputs. It makes no scientific decision.
- **Full completion rule:** Both transfer directions process the exact complete
  target populations; every planned method and 20,000 total paired bootstrap
  draws complete; all correctness checks pass; `summary.json`, per-operation
  assignments, per-pair decisions, bootstrap draws, and `report.md` exist. A
  supported candidate additionally completes the conditional current-Rust-path
  implementation, focused tests, and exact complete-population replay before
  result review. A mixed/contradicted candidate completes without a Rust port.
- **Raw-result path:**
  `.agentsight/experiments/rq3-cross-domain-percentile-calibration-v1/`.
- **Checkpoint or recovery:** Deterministic source extraction and prediction
  files are written before bootstrap. A failed bootstrap may resume from those
  persisted ordinary artifacts; no research-control interface is added.

## Interpretation

- **Positive result:** All complete-population candidate-minus-label-free
  B-cubed F1 deltas are nonnegative and at least one is positive; both
  candidate-minus-raw-transfer deltas are positive; the 95% paired-bootstrap
  lower bounds are nonnegative against label-free and strictly positive against
  raw transfer in both targets; and no correctness/leakage check fails. Adopt
  only after the conditional Rust replay passes.
- **Negative or contradictory result:** After applying the positive and mixed
  rules first, the claim-critical complete-population ordering fails
  consistently across both targets: the candidate does not improve either
  target over label-free, or percentile transfer does not beat raw transfer in
  either target. Reject the candidate and close this scale-transfer branch.
- **Mixed result:** After the positive rule fails, either the candidate-minus-
  label-free point-delta signs or the candidate-minus-raw-transfer point-delta
  signs differ across the two targets. Keep the existing modes and close this
  scale-transfer branch.
- **Inconclusive result:** The complete-population point ordering satisfies the
  positive rule, but at least one required paired-bootstrap interval crosses
  the claim-relevant zero boundary. Keep the existing modes and close this
  scale-transfer branch without trying another normalization or target-specific
  threshold on these labels.
- **Target paper figure or table:** If supported, replace the current RQ3
  calibration presentation with a compact table reporting the two cross-domain
  target B-cubed F1 comparisons and retain boundary F1 as a scoped secondary
  row. If unsupported, no negative development row enters the reader-facing
  paper; the complete boundary remains in evaluation history.

## Reproducibility Notes

- **Software/data versions:** AgentProf `0.2.37`; current repository source;
  official OSWorld-Human and CodeTraceBench-derived operation artifacts already
  independently audited in Steps 0006, 0024, and 0030.
- **Config and seed:** Exact current NPMI, occurrence weighting, unseen-pair
  boundary rule, smallest-threshold tie rule, five OSWorld folds, solved/failed
  CodeTrace split, and bootstrap seed `20260716`.
- **Known deviations:** Both target datasets have been seen during prior
  mechanism development. This is a predeclared reuse/cross-domain transfer
  experiment, not untouched independent confirmation. No target metric may be
  used to revise the CDF definition, source fit, positive rule, or matrix.
