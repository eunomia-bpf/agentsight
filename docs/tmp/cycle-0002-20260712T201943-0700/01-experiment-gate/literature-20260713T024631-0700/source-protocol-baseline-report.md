# RQ2 source, protocol, and baseline decision after ToolSafe

**Node:** bounded literature/source screen  
**Started:** 2026-07-13T02:46:31-07:00  
**Outer gate:** EXPERIMENT  
**Paper authority:** read-only `docs/agentpprof-paper/main.tex`; the active
AAAI workspace now carries its exact scientific body  
**Decision:** select the complete public AgentNet Windows/macOS trajectories
for one materially different cross-platform RQ2 experiment

## Decision context

The CodeTraceBench execution was valid but the tested construction was MIXED.
The subsequent ToolSafe execution was valid but the tested construction was
CONTRADICTED by a family reversal and an unsafe-only direction reversal. Those
are mechanism/workload results, not direct challenges to the paper thesis,
four RQs, or positive RQ2 hypothesis. The next experiment must therefore use a
different real problem, independent labels, and a materially different signal;
it must not tune the CodeTraceBench or ToolSafe tuple, ranker, threshold,
fallback, or family weighting.

RQ2 remains exactly: **Does Profiler Output Correspond to Real Problems?** The
positive hypothesis remains that a target-label-blind semantic profile can
concentrate independently annotated real problems and reduce inspection versus
flat, per-session, native, and raw-action views.

## Candidate screen

### RedundancyBench

[RedundancyBench](https://arxiv.org/abs/2605.29893) is the closest scientific
fit. It reports 200 successful Qwen-3.6-Plus tau2-bench trajectories, more than
8,000 steps, four redundancy types, multi-round annotation, trajectory- and
step-level metrics, and published LLM baselines. The paper points to an
anonymous artifact at
`https://anonymous.4open.science/r/RedundancyBench`, but that address currently
redirects to its file API and returns HTTP 401. No stable official mirror or
usable repository identifier was found in the bounded search.

**Disposition:** do not wait for human intervention and do not invent a local
replacement dataset. Record the source uncertainty and continue to the best
available complete public source. RedundancyBench remains a later replication
candidate when its authors publish a usable artifact.

### AgentNet / OpenCUA

[OpenCUA](https://arxiv.org/abs/2508.09123) was published as a NeurIPS 2025
Spotlight and introduces AgentNet, a large desktop computer-use trajectory
dataset. The paper reports 22,625 human demonstrations across Windows, macOS,
and Ubuntu, more than 200 applications/websites, and 18.6 steps per trajectory
on average. The current public
[AgentNet dataset](https://huggingface.co/datasets/xlangai/AgentNet) is MIT
licensed, ungated, and downloadable without credentials.

The exact public revision inspected here is
`d76ee50a63fad81cfdbe576416757d7c2091ed50`. It exposes:

- `agentnet_ubuntu_5k.jsonl`: 282,313,437 bytes, LFS SHA-256
  `8e24c5a5a1ef5a5113755b33ed12164fc37ce8fbbd35d1c7dba81bf950d53d00`;
- `agentnet_win_mac_18k.jsonl`: 1,400,605,632 bytes, LFS SHA-256
  `5c0d782cbf55af02835c3d6d9120072b87c06d24c5a8354c2544bd8d3568e72c`;
- `meta_data_merged.jsonl`: 22,532 unique task IDs with no missing `system`
  or `domains` values.

A complete metadata stream at that revision contains 12,364 Windows tasks,
5,168 Darwin/macOS tasks, and 5,000 Ubuntu tasks. Its official semantic fields
include operating system, domain, applications, websites, and original task
instruction. The raw trajectories contain the PyAutoGUI action code and
official `last_step_correct` and `last_step_redundant` fields.

### Label provenance and scientific boundary

The trajectories are human demonstrations, but the per-step correctness and
redundancy fields are not human ground truth. Section 3.1 of the OpenCUA paper
states that a reflector compares screenshots before and after an action,
checks the action code and generated reasoning, marks incorrect or redundant
steps, and elaborates a reason; the synthesis pipeline uses
`claude-3-7-sonnet-20250219`. The dataset card likewise lists these fields under
quality control.

Consequently the experiment may accurately call them **official independently
released reflector annotations** or an **official hidden step-quality oracle**.
It may not call them human step labels, causal ground truth, or universal
redundancy truth. Reflection text, generated thought, post-hoc reason,
task-completion summaries, alignment/efficiency scores, and complexity flags
must not enter the predictor because they can directly or indirectly reveal
the reflector decision.

### Prior-project-use boundary

R291 previously streamed only the first 1,000 rows of the Ubuntu file and
converted 16,741 operations. Later development scripts inspected and tuned
rules on its `step_correct` and `step_redundant` labels. That Ubuntu prefix is
development evidence and cannot serve as fresh confirmation.

The full Windows/macOS trajectory file and its 17,532 tasks have not been used
by those project experiments. They therefore supply a materially new target.
The new experiment will use all Windows and all macOS tasks in two reciprocal
platform-held-out folds. It will not report the old Ubuntu sample as a test
result.

## Baseline decision

AgentNet's published objective is computer-use model training rather than
profile-based problem localization, so it does not publish an AgentProf-like
group-ranking baseline. The strongest fair baselines are constructed from its
real source structure and the same target-blind step-risk signal:

1. ungrouped step-risk ordering;
2. exact visible repeat/action ordering;
3. flat aggregation;
4. per-trajectory/session aggregation;
5. source-native system/domain/application/session structure;
6. raw action/target/repetition grouping;
7. the tested cross-run semantic operation stack.

All learned risk is transferred from the other operating system. All views see
the same visible target operations and the same pre-label predictions. This
isolates the profile hierarchy from detector strength and avoids manufacturing
a favorable semantic-only predictor.

## Selection and next action

Select one complete AgentNet Windows↔macOS cross-platform step-quality
localization experiment under RQ2. The tested construction will use the
official full source, official semantic metadata, real AgentProf 0.2.37, a
simple fixed cross-platform risk model, and task-clustered uncertainty. It will
complete at least three serial plan reviews before implementation, then run a
real preflight and the full source rather than stopping after a smoke subset.

This decision changes no thesis, story, RQ, paper hypothesis, or paper text.
It changes only the next experimental branch.
