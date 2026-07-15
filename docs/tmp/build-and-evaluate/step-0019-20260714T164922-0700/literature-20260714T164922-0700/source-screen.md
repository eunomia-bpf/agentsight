# RQ2 Fixed-Reader Protocol Source Screen

**Timestamp:** 2026-07-14T16:49:22-07:00
**Parent:** Step 0019 EXPERIMENT gate
**Status:** Complete

## Question And Coverage Boundary

This bounded search asks only three questions needed to admit the proposed RQ2
experiment:

1. Is using one fixed LLM to prioritize diagnostic evidence from an agent
   trajectory or derived diagnostic representation supported by prior work?
2. What is the strongest fair comparison for testing whether an operation-stack
   packet helps that fixed reader?
3. What presentation control is necessary to keep existing rank order from
   determining the result?

The fixed thesis, four RQs, operation/operation-stack model, and paper story are
read-only. The search does not attempt a comprehensive new related-work survey
and does not authorize a human-productivity, remediation, or universal-reader
claim.

## Name-Free Candidate Claim

For the same hidden-label diagnostic task and the same fixed reader, a
cross-run recurring-behavior profile helps the reader select problem-bearing
groups more accurately than an execution-local grouping under the same
three-group budget.

## Search Method

Searches were run on 2026-07-14 against arXiv, ACL Anthology, OpenReview, and
official project pages. Queries included:

- `LLM agent trajectory diagnosis root cause analysis trace benchmark`
- `LLM judge position bias order paper`
- `LLM profile inspection fault localization ranked groups experiment`
- `AI agent trace diagnosis root cause LLM evaluator`
- `AgentRx Diagnosing AI Agent Failures execution trajectories`
- `AgentDiagnose EMNLP 2025 trajectory diagnosis`

Discovery snippets were not treated as evidence. The primary paper or official
proceedings page was opened for every source used below.

## Verified Sources And Implications

### AgentRx

[AgentRx](https://arxiv.org/abs/2602.02475) releases 115 manually annotated
failed trajectories and uses an LLM judge over an evidence-bearing validation
log to localize the critical failure step and category. It is direct precedent
for asking a fixed LLM to make a bounded diagnostic selection from a structured
trajectory-derived representation. It is not a same-input runnable baseline
for the six existing R315 tasks: its method requires synthesized constraints,
tool schemas, and domain policy rather than importing profile packets.

**Experiment implication:** a fixed LLM reader is scientifically meaningful,
but the result must be scoped to that reader and packet population. AgentRx is
citation-only precedent rather than a matched numerical baseline.

### AgentDiagnose

[AgentDiagnose](https://aclanthology.org/2025.emnlp-demos.15/) is an accepted
EMNLP 2025 system demonstration that derives trajectory competency diagnostics,
validates them against human judgments, and uses diagnostic filtering in a
downstream training-data selection experiment. It establishes that trajectory
diagnostics should be evaluated through an externally scored decision rather
than visualization alone.

**Experiment implication:** the R315 hidden-key selection task is a useful
downstream decision test. It does not become a claim about intervention or
human utility because this experiment stops at group prioritization.

### Position Bias In LLM Evaluation

[Shi et al.](https://aclanthology.org/2025.ijcnlp-long.18/) evaluate position
bias in list-wise and pairwise LLM judging across 15 judges and more than
150,000 evaluation instances, finding that order can affect judgments.

**Experiment implication:** the existing query-aware rank must be hidden from
the fixed reader. Original group IDs and view labels are also hidden. Each
five-group packet is shown in all five cyclic rotations of one hidden-key-blind
base order, so every group occupies every position once, and each presentation
receives fresh opaque aliases. The existing visible-order R316 selection
remains a separate ranker control rather than leaking into the reader prompt.

### New Adjacent Work

[TraceProbe](https://arxiv.org/abs/2607.06184) reports corpus-level trajectory
diagnostics over 2,500 SWE-bench Verified trajectories from five production
settings and uses trajectory structure to localize inspection targets and
failed work. It is a July 2026 preprint, not an accepted experimental protocol,
but it increases the same-problem novelty pressure: corpus-level diagnostic
aggregation cannot itself be claimed as unique.

**Paper implication:** AgentProf's defensible distinction remains the
combination of source-linked additive effects, conserved measures, selectable
operation-stack projections, and profiler output. The fixed-reader experiment
tests one consequence of that representation rather than claiming first-ever
trajectory diagnosis.

## Baseline And Asset Handoff

| Role | Choice | Rationale |
|---|---|---|
| Main baseline | The same Qwen3.6-27B reader on fixed-session packets | Represents the strongest directly matched execution-local answer already present in R315; prompt, visible information categories, reader, five cyclic positions, decoding, and three-group budget are identical. |
| Lower-bound control | Flat one-group packet | Tests completeness without selectivity; it is not a granularity-matched accuracy competitor. |
| Order control | Existing R316 visible-order top-three readout | Measures what the pre-existing rank alone supplies; repeated human-assignment rows are deduplicated by packet. |
| Citation-only precedent | AgentRx and AgentDiagnose | They establish LLM-supported trajectory diagnosis and downstream diagnostic use but do not accept the same packet input. |
| Real assets | Six tasks from four public dataset families, 18 tracked R315 packets, hidden scoring key, local Qwen3.6-27B endpoint | Reuses the complete existing population without new labels, datasets, profile construction, or tuning. |

Raw-action grouping is already a strong static control in the existing six-task
evidence, but R315 contains no matched raw-action reader packet. Creating and
validating a fourth packet family would add a new protocol branch without
resolving the current downstream-use question. Therefore it remains a
paper-level counterpoint: a positive fixed-session comparison cannot authorize
universal view dominance or superiority to raw action.

## Coverage Review And Decision

The declared three questions are resolved:

- published work directly supports a fixed LLM making a diagnostic localization
  decision from structured trajectory evidence;
- fixed-session is the single strongest runnable matched baseline for the
  current R315 input, while flat and visible order have distinct control roles;
- primary evidence on LLM position bias requires hiding the existing order and
  identifiers and balancing every group across every prompt position.

No official system consumes the exact R315 profile packets, so a small
collection/scoring adapter is necessary glue. It must not construct a new
profile, tag, score, dataset, or control interface. The proposed experiment is
admitted to plan review because it tests a paper-level RQ2 decision that the
existing concentration metrics do not directly answer.

Residual uncertainty is explicit: one reader and six heterogeneous tasks do
not support a human, cross-model, or universal diagnostic claim. A contradictory
result bounds this packet/reader mechanism and sends RQ2 back to a stronger
profile signal or protocol; it does not change the RQ or thesis.
