# Step 0050 Independent Outer Audit

- auditor: independent read-only subagent
- audit scope: source fidelity, gate completion, user semantic contract,
  thesis/RQ/story preservation, scorer correction, figure honesty, mutation
  scope, and next routing
- final verdict: **PASS**
- remaining must-fix: **none**
- route: close Step0050 and enter one index-free RQ3 EXPERIMENT

## Source Fidelity

The auditor independently matched the complete report, corrected score, and
raw outputs:

- 405 trajectories, 20,866 operations, 2,948 stages, 251 tasks, and 20,461
  adjacent pairs;
- exact-span, ordinary B-cubed, boundary, and both 10,000-row task-cluster
  bootstrap results;
- complete inference caches and comparator assignments.

The `full-run.md` statement that independent review was pending is retained as
that node's historical state. The later `independent-result-review.md` and
`step-report.md` close it explicitly, so it is not stale final status.

## Scorer Correction

PASS. The current implementation distinguishes:

- `candidate_responsibility`: reusable semantic responsibility type;
- `candidate-run-*`: one contiguous temporal stage instance.

Non-contiguous returns no longer merge into one B-cubed cluster. Corrected
candidate B-cubed is `0.585236749086`; prediction, primary exact spans,
boundaries, bootstrap deltas, and contradicted verdict are unchanged. The
first attempt remains archived.

## Semantic Contract And Story

PASS. Final records preserve the target:

```text
concrete task -> subtask (possibly nested) -> phase/strategy
              -> semantic action -> operation object -> result
```

Agent, model, session, tool, command, path, and status remain metadata,
filters, colors, side details, or bottom-level evidence. Current evidence is
explicitly limited to flat workflow-stage alignment and does not claim to
validate the full hierarchy.

The thesis remains exactly **“Agent observability needs profiling, not only
debugging.”** The four RQs are unchanged. The contradicted numeric-index
candidate is a mechanism boundary only; it does not narrow contributions,
rewrite the story, or enter the paper as a negative result.

## Mutation Scope

PASS.

- no `docs/paper/` paper text was changed;
- the canonical `docs/agentpprof-paper/` submodule is clean and untouched;
- no project or shared skill was edited;
- no branch was created or switched.

The shared skill repository has a pre-existing dirty
`paper-writing-style/SKILL.md` change outside this step. It remains untouched
and must not be reverted or absorbed into this work.

## Figure And Label Language

PASS. The rendered diagnostic now states `FAILED numeric-index mechanism
diagnostic`, says the registered exact-span test contradicted the candidate,
and labels lower frames runtime-derived evidence. The visible 271/275 collapse
to `test deployment` is diagnostic rather than hidden. The figure cannot be a
positive paper hierarchy result.

Human-facing result files call 182/1,247 counts registered lexical-rule hits
and explicitly deny that they are human-validated semantic error rates. Raw
schema and historical-plan names remain unchanged for source compatibility.

## Next Route

PASS. Exactly one next experiment is authorized:

- reuse the 405 normalized task plans, all operations, matched plan-free
  predictions, recurrence comparators, and standard scorer;
- rerun only the candidate causal decisions;
- expose and emit semantic responsibility text without numeric indices;
- choose explicit `stay` or `switch` to an exact retained responsibility;
- keep reusable `responsibility_type` separate from contiguous
  `stage_instance`.

This experiment tests the observed ordinal-interface confound and still only
answers workflow-stage alignment. Nested hierarchy, open-vocabulary label
accuracy, and a more complex append/pop/suspend stack controller remain out of
scope.

## Process Deviation

Nine plan reviews and seven preflight attempts exceeded the intended lean
experiment loop. They repaired real pre-score implementation defects and do
not invalidate the complete result, but they are not a template. The next
experiment should use one plan, no more than the required three serial
scientific reviews, one real-preflight path unless a concrete implementation
defect requires a narrowly recorded repair, one complete run, and one
independent result reconstruction.

## Final Disposition

All Step0050 must-fix items are closed. The numeric-index mechanism is rejected,
the paper and semantic target remain unchanged, and the next state is the
single minimal index-free experiment.

A final delta audit also passed
`docs/operation-stack-induction-algorithms.md` section 5.5: every metric and
ordinal-bias count matches raw evidence, responsibility type and temporal
instance remain distinct, the result is confined to algorithm history, and the
index-free route does not claim complete-hierarchy authorization.
