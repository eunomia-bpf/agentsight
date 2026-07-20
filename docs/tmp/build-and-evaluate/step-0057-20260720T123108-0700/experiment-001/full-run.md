# Full Run — Global Task-Semantic Segmentation

## Verdict

**VALID, CONTRADICTED, NOT ADOPTED.** The final fixed global
Qwen2.5-3B constructor completed every trajectory but collapsed every one into
a single interval. It can emit a variable-depth textual path for a completed
trajectory; it cannot recover how that trajectory decomposes, advances,
repeats, fails, or changes strategy. The global small-model segmentation branch
is therefore closed without another prompt or schema variant.

This result rejects only the tested constructor. It does not change the fixed
paper thesis, four RQs, positive RQ3 hypothesis, or required main stack:

```text
concrete task -> nested subtask* -> phase/strategy
              -> semantic action -> operation object -> result
```

Agent, model, session, tool, command, path, and status remain metadata,
filters, colors, measures, or source-linked evidence. The negative result is
development history and is not inserted into the positive paper story.

## Commands

```bash
python3 script/rq3_global_task_semantic_segmentation_eval.py infer full \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --source-cache-dir .agentsight/experiments/rq3-source-native-task-progress-boundary-v1/full/sessions \
  --turn-assignments .agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/full/predictions.jsonl \
  --llama-url http://127.0.0.1:18183 --workers 1 --timeout-seconds 1200 \
  --out .agentsight/experiments/rq3-global-task-semantic-segmentation-v1/full

python3 script/rq3_global_task_semantic_segmentation_eval.py score \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --predictions .agentsight/experiments/rq3-global-task-semantic-segmentation-v1/full/predictions.jsonl \
  --inference-summary .agentsight/experiments/rq3-global-task-semantic-segmentation-v1/full/inference-summary.json \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --multires-assignments .agentsight/experiments/rq3-multiresolution-recurrence-v1/full/codetrace/operation-assignments.jsonl \
  --causal-score-rows .agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/full/score/operation-score-rows.jsonl \
  --out .agentsight/experiments/rq3-global-task-semantic-segmentation-v1/full/score
```

## Complete Population And Isolation

- all 405 preselected reconstructable failed trajectories from the 1,000-row
  CodeTraceBench manifest, 17,148/17,148 native turns, and 20,866/20,866
  operations completed;
- all four frameworks, 251 task clusters, and 2,948 independent human stage
  occurrences enter scoring;
- the fixed local Qwen2.5-3B-Instruct Q4_K_M model processed 2,887,288 tokens
  in 405 whole-trajectory calls;
- the largest projected prompt used 27,621 tokens and the largest actual chat
  prompt used 27,634 tokens under the native 32,768-token context;
- all human stages and scores remained unavailable until every candidate
  assignment was materialized;
- every generated segment covers ordered turns and operations exactly once;
  and
- no explicit subtask-frame-count cap was applied; the serialized path had a
  384-character cap that 67/405 outputs reached.

## Behavioral Result

The candidate emits exactly 405 segments: minimum, mean, and maximum are all
one per trajectory. Its generated `subtask_path` has depth zero through 39,
with mean 4.98, but all frames span 100% of their trajectory. Representative
raw outputs include repeated sequential steps, repeated identical phrases,
`none` frames, clipped fragments, and command primitives placed in the
semantic-action slot. Independent output-shape reconstruction finds 67/405
paths exactly at the 384-character serialization cap, 94/405 with a repeated
frame, 81/405 with an adjacent repeated frame, 31/405 whose multi-frame path is
one repeated label, and 92/405 command-primitive-shaped semantic actions. Thus
variable serialized depth is not evidence of nested task responsibility. The
exact reserved-word grammar check passes, but the qualitative responsibility-
frame contract fails.

The rendered maximum-operation representative contains one 275-operation-wide
stack with 17 subtask frames and no horizontal transition. It is a visual
counterexample to adoption: it looks deep but cannot answer which subtask
consumed work, where the agent retried, or which stage produced a conclusion.
Independent review also found that the first historical rendering used an
incorrect escaped character class and deleted ordinary `r`, `n`, and `t`
letters. The renderer was repaired and the figure regenerated from the fixed
predictions without rerunning inference. Neither version is paper evidence;
the repaired version remains only a faithful visualization of the failed
candidate.

## Standard Accuracy Results

| Constructor | B-cubed P | B-cubed R | B-cubed F1 | Boundary F1 | Exact-span F1 |
|---|---:|---:|---:|---:|---:|
| **Global Qwen candidate** | **0.173563** | **1.000000** | **0.295788** | **0.000000** | **0.000000** |
| Causal online Qwen control | 0.735681 | 0.581999 | 0.649878 | 0.256606 | 0.049501 |
| Multi-resolution recurrence | 0.782026 | 0.575029 | 0.662740 | 0.265571 | 0.056435 |

The candidate's recall of one is the trivial consequence of assigning every
operation in a trajectory to one predicted group. Its low precision and zero
boundary/span scores establish complete under-segmentation.

## Registered Uncertainty

Paired 10,000-resample task-cluster bootstrap intervals are wholly negative:

| Comparison | Mean B-cubed F1 delta | 95% interval | Positive fraction |
|---|---:|---:|---:|
| candidate minus recurrence | -0.366599 | [-0.381647, -0.350845] | 0.0000 |
| candidate minus causal Qwen | -0.353524 | [-0.373469, -0.332215] | 0.0000 |

The registered contradiction condition is met. No favorable framework slice
or qualitative path can override it.

## Mechanism Interpretation And Next Route

The failure separates two responsibilities that the one-call method conflated:

1. **where persistent work changes**, a segmentation problem; and
2. **what each interval means**, a task-path and outcome labeling problem.

Qwen2.5-3B generated a whole-trajectory summary instead of boundaries, even
after the one admitted interface revision. The next non-equivalent candidate
will test preserving the already effective, source-only
multi-resolution recurrence intervals and ask a semantic model only to label
each fixed interval as `nested subtask path -> phase/strategy -> semantic
action -> operation object -> result`. It must not claim that CodeTrace's flat
stage gold validates nested topology or open-vocabulary label meaning. The
incumbent boundaries retain their established ordinary B-cubed result; semantic
quality needs a separate real annotation or published label-bearing benchmark,
not another boundary score disguised as label validation.
