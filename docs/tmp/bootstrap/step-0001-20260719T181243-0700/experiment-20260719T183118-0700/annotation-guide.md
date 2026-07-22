# Annotation And Scoring Guide

This guide is frozen before any tested condition is generated. It defines the unit, labels, evidence, and scoring for the RQ1 pilot.

## Unit Of Diagnosis

One example is one **goal episode** in one persistent workspace. A goal episode begins at the first top-level user instruction that states a goal and ends at the last action before the next top-level instruction that changes the goal, or at the final recorded action if no new goal appears. Subagent sessions spawned by a top-level session belong to the parent's goal episode and are not independent examples.

Candidate blocks are first formed from complete repository-affiliated sessions separated by at least six hours of no recorded action. Two episode annotators then inspect only top-level user instructions and session-parent relations to split a block when the explicit goal changes. They do this before viewing or assigning pathology labels. Parallel sessions with distinct goals are separate episodes even when their times overlap. Episodes whose goal boundary cannot be resolved are marked `boundary_uncertain` and excluded before model-condition generation; their number and reason remain reported.

The supervisor sees the episode only up to its end and returns one episode-level diagnosis plus evidence actions and an earliest intervention recommendation. The pilot does not score every intermediate state.

## Diagnosis Labels

The primary output is multi-label over four pathology labels. An episode may have none, one, or several.

- **stagnation:** after at least one persistent artifact or evaluator improvement, the Agent continues acting through a coherent interval without further goal-relevant artifact/evaluator progress, or repeatedly returns to the same unresolved state. Mere duration or many actions is insufficient.
- **goal_drift:** a sustained action interval changes or investigates artifacts that do not support the explicit top-level goal, and the Agent does not return to a defensible goal-relevant dependency. Exploration that later supplies relevant evidence is not drift.
- **validation_gap:** the Agent creates or modifies an artifact required by its claimed result but finishes, hands off, or changes goal without an observed relevant validation action. A failing validation followed by a stated unresolved handoff is not “missing”; it is an explicit failure.
- **harness_waste:** an explicit skill, instruction, hook, orchestration rule, or repeated harness behavior causes actions that neither change goal-relevant artifacts nor produce validation/decision evidence, and source text ties the behavior to that harness requirement. General Agent inefficiency without a harness cause is not this label.

Two additional non-pathology states are recorded but not mixed into the multi-label vector:

- **healthy_progress:** none of the four pathologies applies and there is source-backed goal-relevant artifact or evaluator progress;
- **insufficient_evidence:** the full native trace or outcome evidence cannot support a confident label. These episodes are reported and excluded from the primary F1 denominator before condition generation.

## Intervention Ground Truth

Annotators record `intervention_recommended` when a reasonable supervisor should stop, redirect, or request clarification before episode end. They also record the earliest source action after which the pathology is both present and observable. On naturalistic episodes this is **expert recommendation agreement**, not intervention correctness. The paper may use “intervention correctness” only for separately reported controlled replay or known injected-defect cases where the recommended change produces the expected outcome change.

## Evidence Ground Truth

For every positive pathology, each annotator records a minimally sufficient set of native source action IDs and affected artifact paths. Evidence may contain several disjoint actions. Adjudication produces one gold set per label and an earliest observable action. Annotators must cite the raw native record and may use workspace/git outcome evidence, but cannot use Agent Nebula layout, tested trajectory queries, or any model prediction.

The canonical action identifier is `<session_id>#<source_call_id>`. For example,
`claude:7b3e1535-05cf-4821-871b-d476feba6602#toolu_011Ci5S7ZkgYtYP5H2xVnSnA`
identifies one native Tool call without relying on a trajectory-only ordinal. `agent-session`
already parses the native call ID; the workspace projection preserves it as
`source_call_id`, while the raw condition reads the same value from the native Tool record.
Every admitted episode must pass three pre-condition checks: no missing call IDs, unique
`session_id#source_call_id` pairs, and identical frozen session/time membership across
conditions. This ID is evidence bookkeeping only and exposes no lifecycle or diagnosis
feature to the raw condition.

## Annotation Process

1. Two independent annotators with Agent/software-engineering experience receive the exact source session paths, workspace revision/history, explicit goal, and evaluator or test evidence.
2. They independently determine episode boundaries from goals before assigning any pathology.
3. They independently assign labels, confidence, evidence actions/artifacts, and intervention recommendation.
4. Before adjudication, report Cohen's kappa per binary pathology and intervention recommendation; report boundary agreement and evidence-set Jaccard.
5. A third adjudicator resolves disagreements from the source evidence. The tested supervisor model is not used as an annotator or adjudicator.

## Prediction Format

Each supervisor answer must contain:

- four Boolean pathology decisions;
- `healthy_progress` or `insufficient_evidence` when applicable;
- evidence source action IDs and artifact paths for every positive label;
- intervention recommendation and earliest observable action ID;
- confidence in `[0,1]`;
- a short evidence-grounded explanation.

The answer is one JSON object. `evidence` maps each positive pathology to an object with
exactly two arrays: `action_ids` containing canonical identifiers in the format above and
`artifact_paths` containing repository-relative paths. Negative labels need no evidence
entry. `earliest_intervention_action_id` is either one canonical action identifier or
`null` when intervention is not recommended.

Malformed or missing fields count as incorrect/empty predictions; they are not repaired after seeing ground truth.

## Scoring

- **Headline metric:** macro F1 across the four pathology labels, computed per run and macro-averaged only over labels with at least four positive test episodes. Other labels remain descriptive.
- **Evidence metric:** micro precision, recall, and F1 over predicted versus gold source action IDs for correctly predicted positive labels. Artifact-path accuracy is reported separately.
- **Localization metric:** exact earliest-action accuracy and tolerant accuracy where the predicted action falls within the gold evidence set or within the immediately adjacent native action on either side. This follows the exact/tolerant localization distinction used by repository-trajectory diagnosis work; no wall-clock tolerance is introduced.
- **Intervention metric:** F1 against expert recommendation and exact/tolerant earliest-observable localization. It is explicitly not called intervention correctness on naturalistic data.
- **Uncertainty:** repetitions are averaged within episode/condition first. Paired episode bootstrap with 10,000 resamples gives 95% confidence intervals; episodes, not repetitions, are the sampling unit.

## Predeclared Decisions

The unique headline comparison is workspace trajectory versus matched raw-log retrieval on pathology macro F1.

- accuracy support requires a mean paired macro-F1 gain of at least 0.10 with a bootstrap 95% interval whose lower bound is above zero;
- accuracy equivalence uses a predeclared non-inferiority margin of -0.05 macro F1;
- an efficiency-only result requires trajectory accuracy to be non-inferior and median supervisor input-plus-output tokens to fall by at least 25%; this is reported as an efficiency claim, not an information-gain claim;
- evidence F1 is a veto: a headline accuracy gain with evidence F1 more than 0.05 below raw logs is not accepted as grounded diagnostic improvement;
- all other results are mixed or inconclusive rather than selected post hoc as success.
