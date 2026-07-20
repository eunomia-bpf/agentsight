# Full Causal Run

## Verdict

**VALID, NOT ADOPTED, ONLINE QWEN2.5-3B BRANCH CLOSED.** The exact
same-active-leaf invariant materially improves the fixed online constructor,
but its exact-visible-path B-cubed F1 does not exceed multi-resolution
recurrence with a wholly positive paired interval. The registered adoption
condition therefore fails. This closes this algorithm branch; it does not
change the paper thesis, RQ3, its positive hypothesis, or the intended
task-semantic hierarchy.

## Commands

```bash
python3 script/rq3_stateful_exact_leaf_invariant_eval.py infer full \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --raw-root .agentsight/experiments/codetracebench-rq2/hub \
  --original-cache-dir .agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/full/sessions \
  --llama-url http://127.0.0.1:18182 --workers 4 --timeout-seconds 600 \
  --out .agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/full

python3 script/rq3_stateful_exact_leaf_invariant_eval.py score \
  --predictions .agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/full/predictions.jsonl \
  --inference-summary .agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/full/inference-summary.json \
  --step0054-score-rows .agentsight/experiments/rq3-stateful-native-turn-task-stack-v1/score/operation-score-rows.jsonl \
  --step0055-score-rows .agentsight/experiments/rq3-stateful-visible-path-identity-v1/full/operation-score-rows.jsonl \
  --out .agentsight/experiments/rq3-stateful-exact-leaf-invariant-v1/full/score
```

## Complete Population And Isolation

- 405/405 trajectories, 17,148/17,148 source-native turns, and
  20,866/20,866 operations completed;
- all four frameworks and all five source layouts are represented;
- 251 task clusters, 2,948 verified session-local stage occurrences, and
  20,461 adjacent operation pairs enter scoring;
- the fixed Qwen2.5-3B-Instruct Q4_K_M model consumed 25,379,403 tokens in the
  complete causal sequence;
- 2,876 responses were reused only for byte-identical requests before state
  divergence, while 14,272 responses were newly inferred;
- official stage, recurrence assignment, phase/action tag, current-turn
  result, agent, model, session, and status remained invisible to inference;
- no operation was dropped, no active stack was truncated, and no depth cap,
  label normalization, phase filter, fuzzy equality, contraction, or second
  intervention was applied.

## Intervention Behavior

The model proposed 6,604 pushes, 6,130 replacements, 4,411 stays, and three
pops. Exact byte-equality with the active visible leaf converted 6,731 of those
push/replace proposals to `stay`. The applied sequence therefore contains
3,020 pushes, 2,983 replacements, 11,142 stays, and three pops across 397
affected sessions.

The intervention lowers the new-frame rate to 0.350070, but only three pure
pops remain. Maximum depth including the root is 28, median per-session maximum
depth is 5, p90 is 14, and 184 sessions never decrease depth. The model also
proposes 1,278 exact phase-like persistent labels. These are behavior
diagnostics, not additional adoption gates.

## Standard Accuracy Results

| Constructor / identity | B-cubed P | B-cubed R | B-cubed F1 | Boundary F1 | Exact-span F1 |
|---|---:|---:|---:|---:|---:|
| Step 0055 unmodified exact visible path | 0.822397 | 0.432771 | 0.567111 | 0.262350 | 0.034995 |
| **Causal exact visible path** | **0.735681** | **0.581999** | **0.649878** | **0.256606** | **0.049501** |
| Multi-resolution recurrence incumbent | 0.782026 | 0.575029 | 0.662740 | 0.265571 | 0.056435 |

The invariant exchanges precision for recall and recovers most of the large
over-segmentation gap. It improves B-cubed F1 by about 0.0828 over the
unmodified visible-path policy. It remains about 0.0129 below recurrence on the
complete population.

Adjacent-label contraction over the causal paths is a retrospective diagnostic
only and reaches B-cubed F1 0.645518. It is not AgentProf's actual visible path
identity and is not an additional proposed mechanism.

## Registered Paired Uncertainty

Both comparisons use the fixed 251-task, 10,000-resample paired cluster
bootstrap.

| Comparison | Mean B-cubed F1 delta | 95% interval | Positive fraction |
|---|---:|---:|---:|
| causal visible path minus Step 0055 | +0.082944 | [+0.066264, +0.100842] | 1.0000 |
| causal visible path minus recurrence | -0.013075 | [-0.027838, +0.002471] | 0.0496 |

The first interval supports the causal mechanism effect. The second crosses
zero and does not satisfy the registered rule requiring the candidate to
exceed recurrence with a wholly positive interval.

## Framework Diagnostics

| Framework | Step 0055 visible | Causal visible | Recurrence | Causal minus recurrence |
|---|---:|---:|---:|---:|
| OpenHands | 0.469636 | 0.612497 | 0.676295 | -0.063798 |
| SWE-agent | 0.550365 | 0.616250 | 0.708893 | -0.092643 |
| Terminus2 | 0.654087 | 0.687274 | 0.605471 | +0.081802 |
| mini-SWE-agent | 0.615879 | 0.672273 | 0.691523 | -0.019250 |

Terminus2 is a genuine positive slice, but selective framework performance is
not the registered adoption decision. OpenHands and SWE-agent retain the
largest deficit.

## Scientific Interpretation

The tested hypothesis is **partially supported at the mechanism level but does
not clear the adoption criterion**. Exact identity continuity is a useful and
simple principle: it eliminates a major source of redundant task frames and
nearly closes the ordinary B-cubed gap without depth limits or heuristic label
processing. It is not sufficient as a complete online constructor because the
fixed local policy still almost never exits tasks, promotes phase-like text to
persistent task frames, and permits excessive depth.

Per the approved plan, no additional prompt, model, threshold, normalization,
field, phase, depth, contraction, or benchmark variant is admitted in this
online Qwen2.5-3B branch. The next non-equivalent algorithm candidate must use
global trajectory context to infer concrete task/subtask structure, followed
by a transient `phase/strategy -> semantic action -> operation object ->
result` suffix. Agent/model/session/tool/command/path/status remain metadata or
source-linked evidence rather than main responsibility frames.

## Claim Boundary

This run evaluates one fixed online policy against session-local flat stage
occurrences. It does not validate cross-run semantic equivalence, recursive
ancestor topology, variable-depth meaning, generated label semantics, root
canonicalization, or the lower phase/action/object/result suffix. The negative
adoption result is development history and is not inserted into the positive
paper story. The thesis remains exactly **“Agent observability needs profiling,
not only debugging.”**
