# Independent Result Review

## Verdict

**APPROVE.** The independent reviewer explicitly used
`research-experiment-design`, remained read-only, and independently reconstructed
the run from raw caches, predictions, public sources, baseline assignments, and
the verified scorer-only stages.

- must-fix after correction: **0**
- run status: **valid**
- tested hypothesis: **contradicted**
- research value: **decisive mechanism evidence**
- paper impact: **mechanism boundary only**
- next decision: do not adopt this fixed Qwen2.5-3B transition policy; preserve
  the thesis, RQ3, and intended task-semantic hierarchy

## Independently Recomputed Coverage And Validity

- 405 trajectories and valid session caches
- 17,148 source-native turns and first-attempt model calls
- 20,866 operations, each retained exactly once
- 20,461 adjacent pairs
- 2,948 verified stages
- 251 task clusters
- prompt-token range 376--6,236; total 26,006,567

Terminus2 contributes 7,201 operations in 3,483 turns, including 1,426
multi-operation turns and a maximum of 22 operations per turn. Exactly
167/2,543 gold boundaries lie inside a native turn, all in Terminus2.

All request hashes, legal transitions, state transforms, prompts, and operation
assignments recompute. The registered model SHA-256 matches the running Qwen
artifact. Direct source reconstruction over 15 sessions across all five layouts
reproduced 832 operations, 587 turns, their turn identities, step membership,
prompts, and preceding-result flow.

Inference has no manifest or baseline input and completed before gold opened.
Prompts expose only concrete task, complete label-only stack, native
intent/progress, planned source action, and preceding-turn result. Current-turn
result, human stage, recurrence assignment, phase/action-kind, and
agent/model/session/status are excluded.

## Independently Recomputed Stack Behavior

- `stay`: 4,363
- `push`: 6,534
- `replace`: 6,249
- `pop`: 2
- fresh frames: 12,783; new-frame rate 0.745451364591
- operation depth including root: 1--69; mean 6.491948624557
- median and 90th-percentile per-session maximum depth: 7 and 34
- sessions with no depth decrease: 101/405

The same-label evidence also matches exactly:

- 6,246 fresh frames repeat the previous leaf label: 3,216 pushes and 3,030
  replacements;
- 2,732 replacements leave the complete visible label path unchanged and alter
  only hidden instance identity; and
- 1,182 generated labels are exact `phaseN` or `phase-N` forms: 724
  unhyphenated and 458 hyphenated.

Identity churn is therefore a prominent directly testable failure, but Step
0054 does not establish it as the primary cause of the complete B-cubed gap.

## Independently Recomputed Standard Metrics

| Method | B³ P | B³ R | B³ F1 | Span F1 | Boundary F1 |
|---|---:|---:|---:|---:|---:|
| candidate | 0.931957503008 | 0.333171009262 | 0.490861155772 | 0.032768432243 | 0.261642843027 |
| multi-resolution recurrence | 0.782025634215 | 0.575028961707 | 0.662740305102 | 0.056435422708 | 0.265571358509 |
| prior raw stack | 0.999568676316 | 0.141282469088 | 0.247572229177 | 0.008062484253 | 0.221091984003 |
| native-turn singleton | 0.983154097226 | 0.221199218347 | 0.361144715606 | 0.019705414013 | 0.246396349684 |

The candidate produces 13,041 groups. Its boundary sufficient statistics are
TP 1,986, FP 10,652, FN 557, and TN 7,266. Exact-span TP is 262 of 13,043
predicted intervals. It materially improves both prior stack controls but
remains substantially behind the registered incumbent.

The independently repeated 10,000-resample, 251-task bootstrap gives mean
candidate-minus-incumbent B-cubed F1 -0.172257970385, 95% interval
[-0.206653175584, -0.136663378862], and positive fraction 0.0000.

Per-framework candidate-minus-incumbent B-cubed F1 is -0.298377 on OpenHands,
-0.437175 on SWE-agent, +0.022431 on Terminus2, and -0.134873 on MiniSWE.
The Terminus2 improvement is genuine diagnostic heterogeneity, not grounds for
selective adoption.

## Claim Boundary And Next Mechanism

The experiment scores only the flat active-leaf instance partition. It does not
validate ancestor topology, semantic correctness of variable depth, nested
label meaning, generated task-name accuracy, the lower
`phase/strategy -> semantic action -> object -> result` suffix, the paper
thesis, or the complete RQ3 answer.

The reviewer agrees that the smallest next mechanism experiment is:

> When `replace` leaves the complete visible label path unchanged, preserve the
> existing frame instance rather than create a fresh one.

This reanalysis is causally clean for exactly 2,732 transitions because prompts
contain labels but not instance IDs; the future prompt, depth, grammar, and
model decision remain unchanged. It must exclude 3,216 same-label pushes and
298 same-leaf replacements that change the visible path. It requires a new
reviewed experiment and cannot be applied retroactively as a rescue score.
