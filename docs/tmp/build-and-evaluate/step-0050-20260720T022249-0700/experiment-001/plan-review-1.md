# Experiment 001 Plan Review 1

- reviewed: 2026-07-20T02:34:44-07:00
- reviewer: independent subagent after reading `research-experiment-design`
- verdict: **REVISE**

## Blocking Findings

1. AgentBoard does not provide per-operation task-responsibility spans. Its
   AlfWorld evaluator independently detects completed subgoals and records
   cumulative progress; it does not label the subtask pursued by intermediate
   or unsuccessful actions. Intervals inferred between progress increases would
   therefore be project-authored pseudo-gold. AgentBoard may test completion
   localization, but cannot support the planned span-F1 claim.
2. The matched semantic baseline was underspecified. The plan must fix its
   model-visible evidence, decoder, context, output grammar, segment cardinality,
   transport retry behavior, and model-call difference. One-task and action-verb
   methods are controls, not the main semantic baseline.
3. The W&B HTML retains every turn but truncates observations longer than five
   lines. The plan incorrectly called those observations complete. Model-input
   isolation must be enforced by an explicit field whitelist rather than
   searching prompts for reward strings.
4. Ordinal subgoal identifiers are not semantic labels. Labeled span F1 is not
   justified unless predictions and gold share an independent label mapping.

## Required Repair

Use an asset with independent per-operation spans for span fidelity, or narrow
the AgentBoard construct to completion-point localization. Specify one matched
full-trajectory semantic baseline exactly, retain only standard metrics that
the annotations support, and state the exact public evidence projection.

## Root Response

Accepted. Revision 1 reuses the already materialized complete CodeTraceBench
target population, whose released manifest supplies human-verified contiguous
stage intervals for every scored operation. AgentBoard is removed from this
experiment rather than relabeled. The candidate and main baseline now share
the same goal, complete projected trajectory, Qwen model, deterministic decoder,
and per-operation assignment format; only the candidate receives a separately
generated stable goal plan. Unlabeled span F1 is primary, ordinary B-cubed and
adjacent-boundary F1 are secondary, and no labeled metric is claimed.
