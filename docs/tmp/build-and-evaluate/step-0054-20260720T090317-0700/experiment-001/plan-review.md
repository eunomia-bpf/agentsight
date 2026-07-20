# Independent Experiment Plan Review

## Round 1

- reviewer: independent `review_step0053_plan` subagent, reused read-only for
  Step 0054
- required skill: `research-experiment-design`
- verdict: **NEEDS REVISION**
- scope: one RQ3 hypothesis, real assets, exact task-stack mechanism, standard
  metric, full population, and interpretation boundary

The reviewer found three must-fix issues and explicitly requested no additional
baseline, evaluator, freezing, or reproducibility infrastructure:

1. `stay/push/pop/pop-and-push` did not yet specify exact target depths, root
   lower bound, label structure, fresh instance identity, illegal-output
   handling, or the behavior if an unlimited stack cannot fit model context.
2. The strict task-frame rule was in the step report but not fully frozen in the
   plan. Transient phase/action/object/result and system/tool/file fields needed
   an explicit prohibition from creating persistent nodes.
3. Flat CodeTrace B-cubed validates only the active-leaf partition, not nested
   topology, depth, ancestor label meaning, or the lower suffix. The plan also
   used an undefined "framework-specific degeneracy" qualifier.

## Root-Agent Resolution

The plan now freezes four exact JSON/state transforms over an immutable root,
including legal target-depth ranges and fresh frame identity. It adds the
persistent-task versus transient-evidence rule, uses only the preceding result
for the next turn, invalidates rather than silently repairing illegal or
context-overflowing runs, and never truncates the active stack.

The positive authorization is narrowed only at the experiment level: a
positive standard score adopts the active-leaf/task-stack backend, while full
nested topology and the lower suffix remain unscored. The paper thesis, four
RQs, intended hierarchy, and positive story are unchanged. The undefined
per-framework veto was removed rather than replaced by a new conservative gate;
per-framework results are mandatory diagnostics, while the registered paired
task-cluster B-cubed interval remains the single adoption test.

## Round 2

The same independent reviewer reread the revised plan under
`research-experiment-design` and returned **APPROVE** with zero remaining
must-fix items. The EXPERIMENT gate may proceed to implementation and real
preflight without changing the registered prompt contract or interpretation
rule.
