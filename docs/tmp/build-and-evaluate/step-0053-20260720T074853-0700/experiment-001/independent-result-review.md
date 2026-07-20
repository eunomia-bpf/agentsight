# Independent Result Review

## Verdict

**APPROVE.** The reviewer explicitly followed `research-experiment-design`,
remained read-only, and received no desired scientific verdict.

- must-fix issues: **0**
- run status: **valid / complete**
- tested hypothesis: **contradicted**
- research value: **decisive for rejecting this specific stage-boundary
  operator**
- paper impact: **mechanism/workload boundary, not a thesis challenge**
- next paper decision: **do not adopt this classifier or generate a positive
  task-semantic flamegraph from it**

## Independently Verified Population

- 405 sessions;
- 20,866 operations, all retained exactly once;
- 20,461 adjacent pairs;
- 2,948 official stages;
- 251 task clusters;
- framework operations: OpenHands 10,030, SWE-agent 1,460, Terminus2 7,201,
  and mini-SWE-agent 2,175.

All session-local steps are contiguous. Candidate groups change exactly when
cached decisions say `boundary`; scorer pair rows exactly match adjacent group
and official-stage changes.

## Source-Evidence Joins And Coverage

The reviewer rematerialized 15 sessions independently—three from each of the
five source layouts, covering 832 operations—and reproduced every stored prompt
and availability flag. The evaluator enforces source references/actions,
OpenHands event causes, exact OpenHands tool-call ids, and ordered Terminus2
command alignment before accepting an inference cache.

| Layout | Operations | Intent | Progress | Result |
|---|---:|---:|---:|---:|
| MiniSWE messages | 2,175 | 2,154 | 0 | 1,934 |
| OpenHands native events | 6,454 | 5,096 | 0 | 6,338 |
| OpenHands maximal history | 3,576 | 29 | 3,218 | 3,576 |
| SWE-agent trajectory | 1,460 | 825 | 0 | 1,295 |
| Terminus2 responses | 7,201 | 7,200 | 7,200 | 0 |
| **Total** | **20,866** | **15,304** | **10,418** | **13,143** |

The heterogeneous missingness is real and remains part of the interpretation.

## Inference, Cache, Model, And Leakage Audit

- 405 valid session caches and 20,461 completed model calls;
- 19,856 `continue`, 605 `boundary`, and zero retried calls;
- boundary rate `0.029568447290`;
- request sizes 284--6,740 tokens and 33,560,944 total prompt tokens;
- every request hash independently recomputes from the model hash, seed,
  temperature, system prompt, grammar, and user prompt;
- prompts contain only concrete task, native intent, native progress, source
  action, and result;
- phase/action-kind and agent/model/session/status are not projected;
- inference never opens the verified manifest or baseline assignments; and
- the active server and independent file hash both match the registered Qwen
  model SHA-256 `626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`.

## Independent Metric Reconstruction

| Method | B-cubed P | B-cubed R | B-cubed F1 | Groups |
|---|---:|---:|---:|---:|
| candidate | 0.253830439395 | 0.948234942500 | 0.400462230640 | 1,010 |
| multi-resolution recurrence | 0.782025634215 | 0.575028961707 | 0.662740305102 | 6,018 |

Candidate exact spans: TP 25 / 1,010 predicted / 2,948 gold, precision
0.024752475248, recall 0.008480325645, and F1 **0.012632642749**.

Candidate adjacent boundaries: TP 104, FP 501, FN 2,439, TN 17,417,
precision **0.171900826446**, recall **0.040896578844**, and F1
**0.066073697586**. The incumbent boundary F1 is **0.265571358509**.

The candidate's low B-cubed precision and high B-cubed recall are a real
over-merging signature. Boundary precision and boundary recall are both low:
605 predicted boundaries recover only 104 of 2,543 gold boundaries.

Per-framework B-cubed F1, candidate versus incumbent:

- OpenHands: 0.456257890 versus 0.676295271;
- SWE-agent: 0.350277691 versus 0.708892506;
- Terminus2: 0.239608644 versus 0.605471300; and
- mini-SWE-agent: 0.590726333 versus 0.691523317.

The candidate loses in every framework.

## Independent Bootstrap Reconstruction

The reviewer independently repeated the fixed 10,000-resample paired
task-cluster bootstrap and exactly matched the stored output:

- mean candidate-minus-incumbent: **-0.262087921980**;
- 95% interval: **[-0.286562354806, -0.236752466293]**; and
- positive fraction: **0.0000**.

## Authorized Conclusion

> On all 405 source-valid CodeTraceBench failed trajectories, the fixed
> Qwen2.5-3B memoryless adjacent-pair policy substantially under-segments human
> workflow stages and performs reliably worse than multi-resolution recurrence.

The result does not show that source-native task-progress evidence is generally
insufficient, that a contextual or stateful task constructor cannot work, that
nested task stacks are invalid, or that the paper thesis/RQ3 should change. No
positive task-semantic flamegraph may be rendered from these predictions.
