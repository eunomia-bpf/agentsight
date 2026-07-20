# Full Run — Three-Transition Well-Nested Task Stack

## Verdict

**VALID, INCONCLUSIVE, NOT ADOPTED.** The literal `stay / push-one / pop-one`
controller modestly improves the fixed Step 0056 online task path, but it does
not exceed the current multi-resolution recurrence constructor with a wholly
positive paired interval. It therefore does not replace the incumbent.

This is a result about one task-stack constructor. It does not change the paper
thesis, RQ3, positive research hypothesis, intended task-semantic hierarchy, or
the paper. Negative development evidence remains internal.

## Commands

```bash
python3 script/rq3_well_nested_task_stack_eval.py infer full \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --raw-root .agentsight/experiments/codetracebench-rq2/hub \
  --llama-url http://127.0.0.1:18181 --workers 8 --timeout-seconds 600 \
  --out .agentsight/experiments/rq3-well-nested-task-stack-v1/full

python3 script/rq3_well_nested_task_stack_eval.py score \
  --predictions .agentsight/experiments/rq3-well-nested-task-stack-v1/full/predictions.jsonl \
  --inference-summary .agentsight/experiments/rq3-well-nested-task-stack-v1/full/inference-summary.json \
  --step0056-score-rows .agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/full/score/operation-score-rows.jsonl \
  --out .agentsight/experiments/rq3-well-nested-task-stack-v1/full/score
```

## Complete Population And Isolation

- 405/405 real CodeTraceBench trajectories;
- 17,148/17,148 source-native turns;
- 20,866/20,866 uniquely assigned operations;
- 20,461 adjacent operation pairs;
- all four frameworks and all five source layouts;
- 2,948 verified session-local human stage occurrences and 251 task clusters;
- fixed Qwen2.5-3B-Instruct Q4_K_M artifact with SHA-256
  `626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`;
- temperature zero, seed `20260720`, 27,230,342 total model tokens, and
  2,010.24 seconds wall time; and
- no missing operation, invalid transition, path truncation, depth cap,
  threshold, label normalization, contraction, post-hoc pruning, alternate
  prompt, or alternate model.

Inference opened neither human stages nor recurrence assignments. Candidate
paths were fully materialized before the fixed Step 0056 score rows supplied
gold stages and comparison identities to the scorer.

## Controller Behavior

The model proposed 10,753 pushes, 6,267 stays, and only 128 pops. Exact
same-active-leaf identity converted 5,410 proposed pushes to stays. The applied
sequence therefore contains:

| Applied transition | Count | Fraction of turns |
|---|---:|---:|
| stay | 11,677 | 0.6810 |
| push one leaf | 5,343 | 0.3116 |
| pop one leaf | 128 | 0.0075 |

Only 71 of 405 sessions contain any pop; 334 sessions never decrease depth.
Median per-session maximum depth is 11, p90 is 28, and the maximum is 122
including the immutable root. The controller also proposes 1,106 exact
`phase-N`-like labels despite the task-only instruction.

The deepest trajectory has 200 turns, 122 pushes, and one pop. Its final path
contains recurring `explore ...`, `verify ...`, compile, edit, and test phrases
as nested responsibilities. This is not a malformed stack: it is direct
evidence that the fixed 3B transition policy treats many semantic actions as
new persistent tasks and rarely recognizes task completion.

These quantities explain the mechanism; they are not additional decision
gates.

## Registered Standard Metrics

| Constructor / identity | B-cubed P | B-cubed R | B-cubed F1 | Boundary F1 | Exact-span F1 |
|---|---:|---:|---:|---:|---:|
| Step 0056 contiguous task occurrence | 0.754887 | 0.577432 | 0.654342 | 0.256606 | 0.049501 |
| **Well-nested candidate task occurrence** | **0.708301** | **0.613398** | **0.657442** | **0.239777** | **0.040877** |
| Multi-resolution recurrence incumbent | 0.782026 | 0.575029 | 0.662740 | 0.265571 | 0.056435 |

Removing arbitrary path edits and requiring a real pop before a sibling shifts
the online constructor toward recall: candidate recall rises about 0.0360 over
Step 0056 while precision falls about 0.0466. B-cubed F1 rises by about 0.0031,
but boundary and exact-span F1 both fall. Relative to recurrence, candidate
recall is higher but precision is substantially lower, leaving B-cubed F1
about 0.0053 lower.

## Registered Paired Uncertainty

Both comparisons use the fixed 251-task, 10,000-resample paired task-cluster
bootstrap.

| Comparison | Mean B-cubed F1 delta | 95% interval | Positive fraction |
|---|---:|---:|---:|
| candidate minus Step 0056 | +0.003096 | [-0.005868, +0.012359] | 0.7445 |
| candidate minus recurrence | -0.005515 | [-0.020053, +0.010075] | 0.2381 |

The registered candidate-minus-recurrence interval crosses zero. The result is
therefore **inconclusive-not-adopted**, not contradicted and not supported.

## Scientific Interpretation

The experiment answers one precise mechanism question. A literal well-nested
stack is simpler and more faithful to the desired representation than an
unrestricted path editor, and it recovers some recall. Stack legality alone is
not sufficient: the tested Qwen2.5-3B policy lacks a reliable notion of task
completion, so it opens many frames and closes almost none. The remaining
bottleneck is the transition policy's semantic judgment, not stack data
structure validity.

The incumbent recurrence constructor remains the best validated automatic
task-occurrence partition on this workload. The desired main representation
remains unchanged:

```text
concrete task -> nested subtask* -> phase/strategy
              -> semantic action -> operation object -> result
```

This flat benchmark validates only the session-local task-occurrence partition.
It cannot establish ancestor topology, open-vocabulary label meaning, cross-run
semantic equality, root canonicalization, or the transient lower suffix. The
paper, thesis, story, and fixed RQs are therefore untouched.
