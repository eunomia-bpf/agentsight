# Experiment Plan Review — Step 0058 Experiment 001

## Review Scope

An independent read-only reviewer applied `research-experiment-design` to the
complete plan in three serial rounds. The reviewer was asked to identify only
scientific must-fix issues and not add gates, metrics, checkers, reviewers, or
scope.

## Round 1 — Revise

The reviewer found the workload, RQ, baseline, standard metrics, hidden-label
discipline, and full-run requirement sound. Two corrections were required:

1. The 3B-to-27B comparison could not be described as a pure capacity control
   because model generation, training data, architecture, tokenizer, and
   checkpoint also change. The plan was reframed as a stronger-model
   sufficiency test whose result is specific to the tested checkpoints.
2. CodeTraceBench validates only the task-occurrence partition. The plan fixed
   the one available complete DevAI trajectory before candidate scoring and
   bounded the existing result review to a qualitative semantic-contract check
   of the full stack. No metric, checker, reviewer, or gate was added.

## Round 2 — Revise

The semantic-contract correction was approved. One residual phrase still
called Step 0057 an `exact capacity control`; it was replaced with
`same-interface small-model control`. No experiment behavior changed.

## Round 3 — Approve

The reviewer reread the complete revised plan and returned **APPROVE** with
zero remaining scientific must-fix. The experiment may proceed to real
preflight.

## Authorized Experiment

The approved intervention is one fixed comparison: reuse the Step 0057 global
interface and complete CodeTraceBench workload with the already-held
Qwen3.6-27B checkpoint, then score persistent task-path occurrences with the
registered standard metrics. The full task-responsibility stack remains:

```text
concrete task -> nested subtask* -> phase/strategy
              -> semantic action -> operation object -> result
```

The plan does not authorize prompt tuning, alternate thresholds, score
calibration, benchmark replacement, paper-story changes, RQ changes, or shared
skill changes.
