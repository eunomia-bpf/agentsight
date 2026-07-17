# Step 0033 Experiment Plan Review

plan status: REVISE

Trajectory-as-query MAP is a standard and scientifically appropriate primary
ranking metric for the declared problem-step question. The plan correctly uses
non-interpolated scikit-learn AP, preserves score ties, excludes queries with no
relevant item from MAP while retaining them in pooled AP, uses raw action as the
main matched baseline, loads all three complete populations, and keeps the
fixed thesis and RQ unchanged. The stored pipelines also support the claimed
target-blind reconstruction: AgentProcessBench loads risks before human labels,
HINTBench constructs test scores before `load_targets`, and TraceElephant stores
operation scores separately from scorer targets. Three blocking details remain.

## Ranked must-fix items

1. **Bootstrap AgentProcessBench at its released task cluster, not as 614
   independent target-bearing trajectories.** The plan currently resamples
   target-bearing trajectories within family
   ([experiment-plan.md:111](experiment-plan.md#L111)), but the source contains
   five trajectories per task and explicitly records `task_id`
   ([agentprocessbench_profile_eval.py:683](../../../../../../script/agentprocessbench_profile_eval.py#L683)).
   Its existing uncertainty path therefore resamples tasks within family and
   carries every trajectory in the sampled task together
   ([agentprocessbench_profile_eval.py:993](../../../../../../script/agentprocessbench_profile_eval.py#L993)).
   Independent trajectory resampling would understate uncertainty when the five
   executions of one task are correlated. Revise only this workload's rule to a
   paired task-cluster bootstrap; HINT records within environment and
   TraceElephant traces within cell can remain the query-level resampling units.

2. **Remove HINT `native` from the scalar-MAP method matrix.** The plan promises
   that equal scalar scores stay tied and no ordinal/file-order tie break enters
   AP ([experiment-plan.md:106](experiment-plan.md#L106)), but HINT's native
   view is defined as the session score plus an explicit operation ordinal
   ([hintbench_profile_localization_eval.py:1511](../../../../../../script/hintbench_profile_localization_eval.py#L1511)).
   Passing only its score to `average_precision_score` collapses it to the
   session control; encoding the ordinal into a score would violate the plan's
   tie policy. Keep the already reviewed native Work result as a linked
   secondary diagnostic, but do not claim a native MAP row. The TraceElephant
   `source_native` control is unaffected because it has ordinary stored scalar
   leaf scores.

3. **Replace the qualitative verdict words with one exact predeclared rule.**
   “Uncertainty does not reveal a material opposing benchmark” and “materially
   wins” are undefined
   ([experiment-plan.md:162](experiment-plan.md#L162)). State exactly how the
   three point effects and their paired 95% intervals map to supported,
   mixed/inconclusive, or contradicted. This is necessary because the full run
   is a retrospective standard-metric reanalysis whose paper decision depends
   on that classification; the rule must be executable without choosing a
   meaning for `material` after the intervals are visible.

## Follow-up 1

plan status: REVISE

The task-cluster bootstrap and HINT native fixes are complete, and the final
Interpretation section now gives an executable point-sign rule. One stale
sentence still conflicts with that rule: the earlier “Contradictory result”
definition retains “or a material paired effect favors raw action”
([experiment-plan.md:53](experiment-plan.md#L53)), which could label one
negative workload contradictory even though the final rule requires raw action
to win on at least two workloads. Delete that qualitative alternative or
replace the whole sentence with the exact final rule. No other must-fix remains.

## Follow-up 2

plan status: PASS

The stale contradiction clause now matches the final two-of-three sign rule.
All three original must-fix items are closed, and no scientific or executability
blocker remains for REAL PREFLIGHT.
