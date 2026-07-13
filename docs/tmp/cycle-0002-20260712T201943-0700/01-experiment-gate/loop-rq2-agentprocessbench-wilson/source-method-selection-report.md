# AgentProcessBench RQ2 ranking-method selection

**Recorded:** 2026-07-13T06:05:24-07:00  
**Outer gate:** EXPERIMENT  
**Paper RQ held fixed:** RQ2 — Does Profiler Output Correspond to Real Problems?  
**Selection boundary:** public literature, released AgentProcessBench judge
predictions, and visible group assignments only; no human target-label values
were read for method selection

## Decision

Use one fixed finite-evidence ranking construction for the second
AgentProcessBench experiment:

1. retain the exact raw and target-preserving semantic stacks from the first
   complete experiment;
2. pool the released non-null harmful/not-harmful votes inside each group;
3. rank the groups by a fixed Wilson-shaped lower score of their released
   harmful-vote proportion;
4. compare semantic and raw profiles under the same score on the complete
   four-family population.

This construction is simple, target-label blind, and directly addresses the
remaining uncertainty. The first full run showed that semantic grouping raises
average precision and passes a matched semantic-specificity control, while its
work-to-50 interval crosses zero. The new score keeps the positive hypothesis,
fields, benchmark, and target fixed and asks whether penalizing weakly supported
small groups turns that concentration into stable early inspection.

## Fixed prior observation

The completed mean-risk experiment remains immutable prior evidence:

| Quantity | Complete result |
|---|---:|
| Semantic minus raw macro AP | +0.031522 |
| 95% interval for AP effect | [+0.015138, +0.053514] |
| Raw minus semantic macro work-to-50 | +0.016320 |
| 95% interval for work effect | [-0.022550, +0.074214] |
| Matched-shuffle AP p-value | 0.009950 |
| Scientific verdict | `INCONCLUSIVE` |

That verdict is not recomputed or relabeled. The second experiment tests a new
ranking construction inside the same RQ; it does not revise the old result.

## External principles reused

### Probability ranking

Robertson's Probability Ranking Principle states that, under its assumptions,
items should be presented in decreasing probability of usefulness or relevance.
The applicable principle here is modest: rank profile groups by an external
estimate of harmfulness, then evaluate the order against independently supplied
human labels. The paper also warns that the document-by-document principle
depends on its assumptions, so this experiment does not claim that a released
judge vote is a calibrated human-harm probability.

- S. E. Robertson, “The Probability Ranking Principle in IR,” *Journal of
  Documentation*, 1977:
  <https://www.staff.city.ac.uk/~sbrp622/papers/ProbabilityRankingPrinciple.pdf>

### Effort-aware inspection

Effort-aware defect-prediction work treats diagnosis as a ranking problem: the
goal is to recover more defects while inspecting less code. That published
structure matches AgentProf's work-to-50 question even though the inspected
unit here is an operation rather than a line of code.

- Y. Yang et al., “Effort-aware just-in-time defect prediction: simple
  unsupervised models could be better than supervised models,” *FSE 2016*,
  DOI: <https://doi.org/10.1145/2950290.2950353>. The public artifact contains
  the real open-source data and scripts:
  <https://doi.org/10.5281/zenodo.1324170>.
- Y. Guo, M. Shepperd, and N. Li, “Improving classifier-based effort-aware
  software defect prediction by reducing ranking errors,” *EASE 2024*, DOI:
  <https://doi.org/10.1145/3661167.3661195>; author manuscript:
  <https://bura.brunel.ac.uk/bitstream/2438/29008/1/FullText.pdf>.

The second paper explicitly evaluates ranking with Recall@20% and Popt over 72
real-world datasets. Its EA-Z parameter is empirically selected and is therefore
not transplanted here: doing so would add an avoidable tuning choice after the
AgentProcessBench targets have already been observed.

### Fixed finite-evidence score

Wilson's score interval supplies a closed-form lower score for a binomial
proportion without a fitted parameter:

```text
               p + z²/(2n) - z sqrt(p(1-p)/n + z²/(4n²))
lower(p,n,z) = --------------------------------------------
                              1 + z²/n
```

The experiment fixes `z = 1.959963984540054`, the standard-normal 97.5th
percentile, before reading target labels.

- E. B. Wilson, “Probable Inference, the Law of Succession, and Statistical
  Inference,” *JASA* 22(158), 1927, DOI:
  <https://doi.org/10.1080/01621459.1927.10502953>.

The 20 AgentProcessBench judges are models trained or prompted in related ways,
not independent Bernoulli samples. Consequently, `lower` is used as a
Wilson-shaped deterministic finite-ensemble ranking score. Neither the
experiment report nor the paper may describe it as a calibrated 95% confidence
bound on human harm or as a previously published LLM-judge ranking protocol.
Human labels remain a separate final evaluation target.

## Source-only candidate screen

The source-only screen used
`docs/visexp/out/agentprocessbench-rq2/full/group-assignments.jsonl`. This file
contains operation IDs, visible group assignments, and released judge counts;
it contains no human labels. The screen asked only whether a candidate score
would concentrate its own released risk earlier. It was a method-selection
diagnostic, not a scientific result.

All candidates used the same complete source population and the same raw and
semantic group assignments:

| Candidate | Extra choice | Decision |
|---|---|---|
| Group mean operation risk | none | completed construction; work uncertainty remains |
| Parent smoothing toward raw | smoothing strength | reject: introduces a tuning parameter and did not improve the source-only frontier |
| Operation-count Wilson | treats operations as Bernoulli trials | reject: discards the released 20-judge evidence structure |
| Beta pseudocount score | prior parameters | reject: avoidable prior choice |
| EA-Z transplant | lower-bound parameter | reject: published value was empirically studied on another domain |
| Pooled-vote Wilson-shaped score | fixed `z`, actual non-null votes | select: simple, no fitted threshold, and directly penalizes small weakly supported groups |

The selected score's source-risk-only work-to-50 diagnostic was favorable in
all four families:

| Family | Raw score order | Semantic score order | Raw minus semantic |
|---|---:|---:|---:|
| BFCL | 0.275290 | 0.230116 | +0.045174 |
| GAIA dev | 0.280713 | 0.263514 | +0.017199 |
| HotpotQA | 0.348774 | 0.340599 | +0.008174 |
| tau2 | 0.230250 | 0.174585 | +0.055665 |
| Equal-family macro | — | — | +0.031553 |

These numbers recover half of the *released-risk mass*, not half of the human
harmful labels. They cannot support RQ2 and will not be reported as a paper
result. Their only role was choosing one target-blind construction before the
new scorer is implemented.

## Exact score semantics

Every group identity is family-local: `g = (family, AgentProf stack key)`. No
vote or operation pools across families, even when two stack keys have the same
text. Let `h_g` be the number of non-null released predictions equal to `-1`
across every operation in `g`, and let `n_g` be the number of all non-null
released predictions in `g`. Then:

```text
p_g = h_g / n_g
score_g = lower(p_g, n_g, 1.959963984540054)
```

All 20 released judges have equal weight. Published judge accuracy does not
select or weight models. Null predictions contribute no harmful or non-harmful
vote. If a group has `n_g = 0`, it receives `score_g = 0`, placing a completely
unsupported group at the bottom rather than ahead of groups with observed
harmful-vote evidence. This path must be reported if observed. Every operation
still counts in inspection work and receives its group's score.

The score is applied identically to raw, semantic, session, flat, and
individual-operation reference views. It does not use the number or value of
human harmful labels. Equal scores remain one atomic tier.

## Why this is not target retuning

Human labels from the first complete run are known to the project, so the
second experiment is not represented as a pristine first use of
AgentProcessBench. The protection is narrower and auditable:

- the method comes from published ranking/statistical principles;
- its only constant is the conventional two-sided 95% `z` value;
- the source-only candidate table was computed without target-label values;
- no field, family, subgroup, score threshold, or verdict threshold was chosen
  from human-label performance;
- every operation and all four families remain in the full run;
- the human-label loader must still run only after fixed AgentProf group
  assignments and group scores have been materialized.

This makes the run a transparent second construction on a reused benchmark,
not a hidden-label holdout claim. Its planned paper role is **supporting adaptive
within-benchmark construction evidence**. A later fresh benchmark can
strengthen external validity, but lack of a fresh source does not justify
changing RQ2 or shrinking the positive hypothesis.

## Rejected fresh-source alternatives

The bounded search did not find a stronger immediately executable public
source than AgentProcessBench:

- ToolPRMBench provides 445 action-pair preference cases and released model
  outputs, but not complete cross-run trajectories suitable for profile-group
  inspection.
- AgentErrorBench/AgentDebug provides 200 failed trajectories, but no released
  target-blind step-risk ensemble comparable across all operations.
- AgentRx has 115 failed trajectories and had already been screened in the
  prior research history.
- CodeTraceBench is complete and public but was already used in this cycle and
  supplies a mixed rather than decisive RQ2 construction.

The next fresh-source search should resume only after this one complete
construction is reviewed. Continuing to enumerate benchmarks now would avoid
the decisive experiment rather than improve it.

## Required disposition

Write one new experiment plan for the selected score. It must keep the exact
paper thesis, four RQs, RQ2 wording, semantic stack, raw stack, complete source
population, metrics, cluster bootstrap, and matched shuffle principle. It may
change only the group-ranking calculation and the implementation paths needed
to materialize it.

Before REAL PREFLIGHT, the plan must pass at least three serial independent
reviews using `research-experiment-design`. A reviewer may revise scientific
details, but may not respond to uncertainty by narrowing the RQ, dropping
work-to-50, changing the positive hypothesis, removing a family, or editing the
paper.

No paper, submodule, shared skill, thesis, RQ, or hypothesis was changed in
this selection node.
