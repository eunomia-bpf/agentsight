# Step 0034 Literature And Source Screen — Transferable Recurrence Calibration

**Timestamp:** 2026-07-16T17:52:04-07:00

**Parent:** Step 0034 / EXPERIMENT_GATE / Node 001

## Objective And Declared Coverage Boundary

The fixed paper question is **RQ3 — How Accurate Are the Tags?** The candidate
plain claim is: a cutoff learned from grouped trajectories in one domain can be
applied to the unchanged recurrence score in another domain after expressing
scores by their position in each domain's unlabeled reference distribution.

The screen covers four decision threats:

1. whether source-to-target threshold transfer is an established scientific
   problem rather than an AgentProf-invented protocol;
2. whether rank or empirical-CDF normalization is a credible response to
   incomparable score scales;
3. whether the current public trajectory artifacts can implement a fair
   source-label/target-label separation;
4. whether this experiment adds information beyond Steps 0024, 0030, and 0033.

Coverage ends when primary sources and local raw artifacts are sufficient to
accept or reject one experiment design. It does not reopen the paper's novelty
map, search for a new benchmark, or claim that calibration itself is novel.

## Claim Questions And Search Strategy

The source loop used materially different query branches:

- `cross-domain threshold calibration anomaly score source target`;
- `empirical CDF normalization anomaly scores across datasets`;
- `quantile normalization scores across domains calibration`;
- official AAAI, ACL Anthology, and JMLR/domain-host searches for threshold
  transfer, cold-start calibration, and rank calibration.

Secondary and recent leads were used only to discover primary sources. Novelty
and protocol decisions rely on official proceedings pages and the local raw
experiment artifacts.

## Primary-Source Verification

### Cross-domain threshold transfer

Perini, Vercruyssen, and Davis, *Transferring the Contamination Factor between
Anomaly Detection Domains by Shape Similarity*, AAAI 2022,
<https://doi.org/10.1609/aaai.v36i4.20331>, explicitly studies learning a
threshold-related quantity in a labeled source domain and transferring it to a
related target domain without labeled target data by using the target score
distribution. The paper provides direct AAAI precedent for the problem shape,
not for AgentProf's recurrence score or operation partitions.

### Limited-label threshold calibration

Sedova and Roth, *ACTC: Active Threshold Calibration for Cold-Start Knowledge
Graph Completion*, ACL 2023,
<https://aclanthology.org/2023.acl-short.158/>, treats threshold calibration from
limited annotated tuples as a distinct problem and evaluates the downstream
prediction effect. It supports treating grouped reference trajectories as an
explicit information budget rather than silently mixing their labels into an
unsupervised method.

### Rank-scale comparability

Huang et al., *Uncertainty in Language Models: Assessment through
Rank-Calibration*, EMNLP 2024,
<https://aclanthology.org/2024.emnlp-main.18/>, motivates rank-based comparison
when raw uncertainty measures occupy different scales. Its metric is not reused;
the absorbable principle is that ordering can be comparable when raw numerical
scales are not.

### Existing AgentProf evidence

Step 0024 fixes the current recurrence score and label-free two-means cutoff.
Step 0030 fits a separate raw-NPMI cutoff from grouped references in each
domain. It reaches B-cubed F1 `0.8011` on OSWorld-Human and `0.6666` on
CodeTraceBench, but the learned raw cutoffs have visibly different scales:
CodeTraceBench selects `-0.0982466`, whereas the five OSWorld folds select
`0.274483`, `0.326138`, `0.250125`, `0.415066`, and `0.282964`. This makes
direct raw-cutoff transfer a meaningful competing explanation and makes a
within-reference percentile the smallest scale correction worth testing.

The complete local assets already exist:

- all 287 OSWorld-Human sessions, 3,978 operations, and 2,042 groups;
- 2,229 CodeTraceBench score-reference sessions and 87,703 operations;
- 483 disjoint solved calibration sessions with 2,886 stages;
- 405 failed target sessions with 20,866 operations and 2,948 stages;
- current label-free and per-domain calibrated predictions and standard
  boundary/B-cubed scorers.

## Closest-Work And Novelty Judgment

Threshold transfer and rank normalization have high same-mechanism precedent;
they are not an AgentProf contribution. The AgentProf-specific uncertainty is
empirical: whether one calibration decision transfers across heterogeneous
agent operation populations while the recurrence score, visible fields, and
target labels stay fixed and separate.

The experiment therefore cannot support a novelty claim about empirical CDFs,
quantiles, calibration, or transfer learning. Its value is to strengthen or
bound the existing operation-stack constructor under RQ3. The broad thesis and
two-object model remain unchanged.

## Baseline And Experiment Handoff

The competing scientific positions and smallest fair matrix are:

1. **Current label-free recurrence — main baseline.** Each target domain can
   set its own cutoff from the unlabeled score distribution; source group labels
   add no transferable value.
2. **Cross-domain raw-cutoff transfer — normalization ablation.** One numerical
   NPMI cutoff is already comparable across domains; empirical-CDF conversion is
   unnecessary. The published/local evidence suggests this is unlikely but it
   directly isolates the proposed scale correction.
3. **Per-domain grouped calibration — upper-bound control.** Target-domain group
   annotations can improve the current score when available. It is not an
   equal-information main baseline and cannot be used to claim the candidate is
   annotation-free.

Simple action-change, phase-change, always-boundary, and supervised-predictor
rows are already complete and remain citation/result-table context. Rerunning
them cannot distinguish the transfer mechanism and is unnecessary.

The candidate uses the same NPMI table and boundary rule as the current
constructor. For each unlabeled reference population, observed transition
scores are mapped to an occurrence-weighted empirical CDF percentile. A source
domain's grouped operations select one percentile threshold by source B-cubed
F1; that percentile is applied unchanged to the target domain before target
labels are read. Unseen target transitions remain boundaries. The complete
matrix runs both OSWorld-to-CodeTraceBench and CodeTraceBench-to-OSWorld
directions.

Primary metric is operation-weighted B-cubed F1, matching the partition claim
and Step 0030. Boundary F1 is secondary and cannot veto a supported partition
claim unless the implementation or population is invalid. The strongest
positive decision requires the candidate to be no lower than label-free
recurrence on both target populations and strictly higher on at least one.

## Alternatives, Search-Tree Update, And Residual Uncertainty

Another RQ2 score/grouping experiment was rejected because Step 0033 already
holds the underlying diagnostic signals fixed and compares semantic grouping
with raw action on three complete workloads. Another literal taxonomy dataset
would add a cell without improving the automatic constructor. Another raw
NPMI feature, cutoff, local-window rule, or target-specific sweep is barred by
the closed Steps 0025--0026 branch.

The search tree moves from per-domain raw calibration to one distribution-
normalized transfer edge. The main uncertainty is whether OSWorld and
CodeTraceBench group semantics are similar enough for any single percentile to
transfer. This uncertainty is the point of the experiment, not a reason to
weaken the hypothesis or inspect target metrics before plan review.

**Coverage decision:** sufficient for one formal experiment plan. No additional
paper, system, benchmark, or metric search is needed before plan review.
