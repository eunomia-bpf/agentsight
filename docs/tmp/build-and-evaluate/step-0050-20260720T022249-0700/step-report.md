# Step 0050 Detailed Report

- step: `step-0050-20260720T022249-0700`
- outer state entered: EXPERIMENT
- gate completed: EXPERIMENT
- final route: EXPERIMENT
- paper thesis: **Agent observability needs profiling, not only debugging.**
- fixed RQs: attribution, localization/problem correspondence, tag accuracy,
  and cost
- paper mutation: none

## Objective

Test one bounded mechanism inside RQ3: whether deriving a stable task-rooted
responsibility plan and causally aligning every real operation to it recovers
human workflow-stage spans better than a matched plan-free Qwen segmenter and
the strongest current recurrence constructor.

The paper-level semantic contract remained:

```text
concrete task -> subtask (possibly nested) -> phase/strategy
              -> semantic action -> operation object -> result
```

Agent, model, session, tool, command, path, and status remained metadata or
bottom-level evidence. The experiment scored only the one flat stage level
available from CodeTraceBench and never treated that score as validation of the
complete hierarchy.

## Plan And Preflight

The plan fixed one hypothesis, the complete real CodeTraceBench population,
source-only causal evidence, Qwen2.5-3B, exact standard span/B-cubed/boundary
metrics, matched comparators, and a task-cluster bootstrap. Nine serial plan
reviews eventually approved revision 8.

Real preflight exercised one complete trajectory from every framework without
opening human stages. Seven documented attempts repaired concrete
implementation defects in source extraction, Python scope, semantic-label
handling, planner grammar, and duplicate normalization. The final preflight
covered 161/161 operations and demonstrated that a fixed plan prevented the
prior one-new-frame-per-operation degeneration.

This was scientifically traceable, but operationally excessive. Nine plan
reviews and seven preflight attempts are a process deviation; the next
experiment must not repeat review or contract inflation.

## Complete Execution

The fixed inference completed:

- 405/405 real trajectories;
- 20,866/20,866 operations;
- 42,137 model calls;
- 43,620,419 total model tokens;
- maximum actual input 5,991 tokens below the 8,192-token limit;
- 71.96 minutes wall time;
- no missing operation, malformed retained response, context overflow, or
  gold-field leakage.

The task planner produced 2,568 normalized responsibility types. The candidate
made 5,114 temporal switches (boundary rate 0.249939), while the matched
plan-free policy made 19,357 (0.946044).

## Complete Result

| Method | Exact-span F1 | Ordinary B-cubed F1 | Boundary F1 |
|---|---:|---:|---:|
| Task-rooted numeric-index candidate | **0.011574** | 0.585237 | 0.158025 |
| Matched plan-free Qwen | 0.008542 | 0.283892 | 0.219543 |
| Multi-resolution recurrence | **0.056435** | **0.662740** | **0.265571** |

The paired task-cluster 95% interval is slightly positive against plan-free
Qwen (`[+0.000002,+0.006316]`) but wholly negative against multi-resolution
recurrence (`[-0.054570,-0.035973]`). The registered result is therefore
**CONTRADICTED**.

An independent read-only reviewer reconstructed all population counts, cache
coverage, source isolation, exact spans, corrected B-cubed, boundaries, and
every bootstrap delta. It returned PASS for run validity and COMPLETE for
coverage while confirming the contradicted hypothesis.

## Scorer Correction

The first score incorrectly used reusable plan indices as B-cubed cluster IDs,
merging separate temporal visits to one responsibility. The scorer now creates
a unique candidate instance for every contiguous run and retains the semantic
plan index separately. The old attempt is archived. This correction changed
only candidate B-cubed, not prediction, primary exact-span, boundary,
bootstrap, or scientific verdict.

## Mechanism Diagnosis

The failure is more specific than generic small-model weakness:

- 397/405 trajectories start at numeric index 1;
- index 0 owns only 180/20,866 operations;
- 4,384/5,114 switches (`85.73%`) are exactly `index + 1`;
- 638 switches return from a larger index to index 1;
- the representative 275-operation trajectory walks `1,2,3,4,5`, then assigns
  271 operations total to `test deployment`.

The model treated numeric indices like one-based ordinal positions or a next-
item counter. This confounded semantic alignment and produced both initial
plan marching and a final overwide responsibility.

The rendered flamegraph is retained only as a failed-mechanism diagnostic. Its
candidate adds one flat responsibility frame, while phase, action, object, and
result remain runtime-derived. It is not a recovered task-semantic hierarchy
and is not paper-positive evidence.

The registered label rule produced 182 candidate and 1,247 plan-free lexical
hits. These are deterministic lexical diagnostics, not semantic error rates;
the rule also matches legitimate task-object language.

## Scientific Disposition

The numeric-index aligner is not adopted. The contradiction changes no thesis,
RQ, contribution, scope, or paper story, and no negative result enters the
paper. Shared skills and the canonical paper submodule were untouched.

The minimal next experiment reuses the 405 plans, complete operation evidence,
baselines, and standard scorer. It reruns only candidate decisions through an
index-free interface:

```json
{"decision":"stay","responsibility":null}
```

or an exact retained responsibility string on `switch`. The model sees and
chooses semantic text, never numeric index or instance number. Reusable
`responsibility_type` is kept separate from each contiguous `stage_instance`.

This next test isolates the observed ordinal bias. It still answers only
workflow-stage alignment and cannot by itself validate nested hierarchy or
open-vocabulary tag accuracy. More complex stack-state modeling is deferred
until this smaller causal explanation is tested.

## Evidence Index

- plan and nine reviews: `experiment-001/experiment-plan.md` and
  `experiment-001/plan-review-*.md`;
- implementation-repair history: `experiment-001/real-preflight-attempts.md`;
- final real preflight: `experiment-001/real-preflight.md`;
- complete execution and interpretation: `experiment-001/full-run.md`;
- independent reconstruction: `experiment-001/independent-result-review.md`;
- raw predictions and caches:
  `.agentsight/experiments/rq3-task-rooted-stage-alignment-v1/full/`;
- corrected score:
  `.agentsight/experiments/rq3-task-rooted-stage-alignment-v1/score/`;
- archived first score:
  `.agentsight/experiments/rq3-task-rooted-stage-alignment-v1/score-attempt-1-plan-index-bcubed/`.
