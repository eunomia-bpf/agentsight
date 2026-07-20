# Independent Result Review — Global Task-Semantic Segmentation

## Verdict

**APPROVE after reporting repair — must-fix resolved.** The run is valid, the
tested hypothesis is contradicted, and the constructor must not be adopted.
The independent reviewer explicitly read and applied
`research-experiment-design`, remained read-only, and did not execute model
inference, edit files, or use the repository scorer as its source of truth.

The first review verdict was `REVISE` because the root correctly rejected the
partition but initially described generated path depth too favorably, reported
only an exact forbidden-word check as a semantic contract, called the selected
405 trajectories the whole CodeTraceBench population, and retained a renderer
whose escape bug corrupted labels. The root repaired all four reporting defects
without changing a model output or metric.

## Independent Population And Isolation Reconstruction

The reviewer joined raw per-session caches, predictions, the fixed target
universe, both comparison assignments, and the verified manifest:

- 405/405 preselected reconstructable failed trajectories from the 1,000-row
  manifest;
- 17,148 complete source-native turns and 20,866 operations;
- OpenHands 213, Terminus2 93, mini-SWE-agent 71, and SWE-agent 28;
- every operation key appears exactly once in every method;
- every session covers native turn indices `0..input_turns-1` exactly;
- 2,948 human stage occurrences and 251 task clusters reconstructed only after
  predictions were fixed; and
- no stage/manifest input or score leakage into inference.

The maximum actual prompt is 27,634 tokens; the maximum actual prompt plus its
completion allocation is 32,269, below the native 32,768-token context. The
maximum completion is only 238 tokens, so neither context nor output truncation
explains the one-segment collapse.

## Independent Metric Reconstruction

The reviewer independently recomputed every primary and secondary score:

| Method | B-cubed P | B-cubed R | B-cubed F1 | Boundary F1 | Span F1 |
|---|---:|---:|---:|---:|---:|
| candidate | 0.173563 | 1.000000 | 0.295788 | 0.000000 | 0.000000 |
| multi-resolution recurrence | 0.782026 | 0.575029 | 0.662740 | 0.265571 | 0.056435 |
| causal Qwen control | 0.735681 | 0.581999 | 0.649878 | 0.256606 | 0.049501 |

Across 20,461 adjacent operation pairs, the candidate predicts no boundary:
TP 0, FP 0, FN 2,543, and TN 17,918. A separately implemented 10,000-resample
paired bootstrap over the 251 task clusters exactly reproduces candidate minus
recurrence mean B-cubed F1 -0.366599, interval
[-0.381647,-0.350845], and positive fraction zero.

## Independent Semantic-Output Audit

All 405 trajectories have one segment. Generated `>` depth is therefore a
static string property rather than observed push/pop or task-path transition.
The reviewer reconstructed the following directly from raw responses:

- 67/405 paths exactly equal the 384-character schema limit;
- 74/405 are at least 380 characters;
- 94/405 contain a repeated case-folded frame;
- 81/405 contain an adjacent repeated frame;
- 31/405 multi-frame paths repeat one identical frame throughout; and
- 92/405 semantic-action fields are conservatively shaped as a direct command
  or `run`/`execute` plus a known executable.

Examples include repeated `READING`, repeated `Optimal Transport`, a sequential
installation plan represented as ancestry, and actions such as `ls -la`,
`grep`, `cat`, and `qemu-img`. The parser's exact reserved-word check is true,
but the qualitative task-responsibility contract is false.

## Repairs And Final Disposition

The root made only reporting and rendering repairs:

1. scorer output now separates structural coverage, exact reserved-word
   exclusion, task-progress failure, and qualitative responsibility failure;
2. the reproducible output diagnostic reports cap hits, repeated frames, and
   command-primitive-shaped actions;
3. Step 0057 records call the workload the preselected 405 reconstructable
   failed trajectories, not all 1,000 manifest rows; and
4. `safe_frame()` now removes actual delimiters/control characters rather than
   ordinary `r`, `n`, and `t`; the failed-candidate figure was regenerated from
   unchanged predictions.

The corrected interpretation is decisive: reject the global Qwen2.5-3B
constructor, do not update the paper, thesis, four RQs, positive hypothesis, or
current recurrence implementation, and route the next mechanism toward a
separation between interval induction and semantic labeling.
