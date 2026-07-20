# Step 0048 Literature Refresh and Evaluation Review

**Timestamp:** 2026-07-19T18:57:09-07:00
**Parent:** Step 0048, targeted WRITING iteration before milestone review
**Status:** complete

## Question and coverage boundary

This node asks whether newly available work changes AgentProf's closest-work
positioning or supplies a materially better evaluation for one of the four
fixed RQs. The bounded search covered: multi-agent failure attribution,
process-level coding-agent evaluation, context-sensitive trajectory state,
responsible-agent/step localization, released datasets, official repositories,
and standard ranking metrics. It did not search for another operation-stack
constructor, because all four RQs are already answered and the current
algorithm-selection branch is closed.

The name-free claims under attack were:

1. aggregating recurring agent responsibility across runs is distinct from
   per-run tracing and failure localization;
2. a selectable responsibility hierarchy can organize independently defined
   problem evidence more usefully than raw action identity;
3. visible action identity alone is not always sufficient to represent
   context-dependent intent or process stage.

## Search and source verification

| Search branch | Primary source or artifact | Verified facts | Impact |
|---|---|---|---|
| Multi-perspective failure attribution | [MP-Bench paper](https://arxiv.org/abs/2603.25001), [official Adobe repository](https://github.com/adobe-research/multi-agent-eval-bench) | 289 failed executions, 121 multi-agent configurations, three independent expert annotations per instance; only 16.2% of annotated failure steps have three-expert consensus; evaluation uses nDCG@5 and nDCG@full with linear and exponential gains. The repository contains 867 annotation JSON files and upstream-log links, but no official model predictions or reusable localizer output. | Strongest new RQ2 protocol and a direct warning against treating failure responsibility as a single deterministic label. |
| Context-sensitive process stages | [AgentLens paper](https://arxiv.org/abs/2605.12925) | 2,614 OpenHands trajectories; a 1,815-trajectory evaluation subset; 10.7% of passing trajectories are reported as Lucky Passes; exploration/implementation/verification/orchestration labels depend on trajectory history rather than tool identity. The paper says release is planned; the linked GitHub repository returned not found on 2026-07-19. | Strong RQ3 construct precedent: action type is not identical to intent stage. Not executable now. |
| Process defects and control | [ProcBench paper](https://arxiv.org/abs/2605.20251) | 200 annotated trajectories over AndroidBench, TerminalBench, and SWE-bench Verified; evaluates process defects and control preservation with calibrated scorecards. | Supports process-level evaluation beyond outcome-only scoring, but is not a direct profile or partition benchmark and has no verified runnable artifact. |
| Responsible agent and decisive step | [AgentLocate paper](https://arxiv.org/abs/2607.07989) | Jointly predicts responsible agent and earliest decisive step; evaluates agent-level and tolerance-aware step localization on Who\&When and Aegis-Bench; no official runnable artifact was found in the bounded search. | Direct RQ2 neighbor and possible future fixed external signal, not an available baseline today. |
| Deterministic predecessor data | [Who\&When paper](https://arxiv.org/abs/2505.00212), [repository](https://github.com/ag2ai/Agents_Failure_Attribution) | Public responsible-agent and step annotations; upstream logs do not uniformly provide the rich action fields needed to apply the current stack constructor without a new adapter/semantic extraction path. | Useful citation and provenance source; does not by itself justify a new experiment. |
| Full-context failure evidence | [TraceElephant paper](https://arxiv.org/abs/2604.22708), [repository](https://github.com/TraceElephant/TraceElephant) | Full trajectory and architecture/tool/environment context materially improves localization over partial observation; already used in current RQ2. | Reinforces AgentProf's complete-evidence motivation and confirms the current benchmark choice remains relevant. |

Queries used materially different formulations around `multi-perspective failure
attribution benchmark`, `process-level coding agent trajectory evaluation`,
`context-sensitive intent stage`, `earliest decisive failure step`, and the
exact paper titles/arXiv identifiers. Every paper-level judgment above was
checked against the primary arXiv text; release claims were separately checked
against the official repository URL rather than inferred from the abstract.

## Novelty and positioning decision

The sources make generic process analysis, trajectory-quality evaluation, and
failure-step localization still higher-risk novelty claims. They do not provide
the same conjunction as AgentProf: source-linked heterogeneous effects,
conservation of arbitrary additive measures, and query-selected population
profiles over one operation corpus. No source supports replacing or narrowing
the fixed thesis, contributions, or four RQs.

The paper should cite MP-Bench because it changes the accepted interpretation
of RQ2 targets from one deterministic answer toward graded responsibility. The
canonical literature frontier should also retain AgentLens, ProcBench, and
AgentLocate. With a nine-page AAAI limit, citing all four in the paper displaced
the bibliography onto a tenth page. The final paper therefore swaps one less
decision-relevant cited neighbor (WebGraphEval) for MP-Bench, while retaining
all four in this source map and `docs/background-related-work.md`.

## Evaluation decision

The existing metric suite remains valid and standard:

- RQ1: precision/recall, concurrent controls, conservation, ordinary B-cubed;
- RQ2: per-query AP/MAP;
- RQ3: macro-F1/accuracy, V-measure/B-cubed, boundary precision/recall/F1;
- RQ4: elapsed time, throughput, and peak RSS.

The best *future* RQ2 addition is MP-Bench's graded multi-perspective protocol,
not another clustering score or arbitrary inspection cutoff. A valid experiment
would hold one target-blind per-step diagnostic signal fixed, compare raw-action
and semantic-stack organization, and report nDCG@5 plus nDCG@full under the
published gains over the complete 289-log population.

That experiment is not admitted now. MP-Bench releases gold expert annotations
and log links but no target-blind prediction. Ranking groups from the same gold
consensus being evaluated would measure a gold-conditioned organization, not a
new end-to-end diagnostic result. Implementing a new LLM localizer would change
more than the common bottleneck and introduce model/prompt effects. AgentLens
and AgentLocate likewise lack a verified runnable artifact. The reversible
default is therefore to preserve the current complete RQ2 evidence and reopen
only when a published localizer output or simple fixed external scorer becomes
available.

## Canonical updates and next action

- Updated `docs/background-related-work.md` with all four verified neighbors,
  the MP-Bench metric protocol, artifact availability, and the precise reopen
  condition.
- Added verified bibliography entries for all four sources; only MP-Bench is
  cited in the page-limited paper.
- Updated the paper's diagnosis paragraph to acknowledge expert-supported
  multi-perspective targets without changing its thesis, RQs, mechanism, or
  evidence claims.
- Compiled the official AAAI source successfully at nine pages with no
  undefined citation, multiply-defined label, or overfull-box error.

The next node is an independent, complete cross-domain milestone review by
Grok 4.5 and Claude Opus, followed by a root synthesis. A reviewer may identify
a genuine missing requirement, but the literature refresh alone does not
reopen any RQ or authorize algorithm/story change.
