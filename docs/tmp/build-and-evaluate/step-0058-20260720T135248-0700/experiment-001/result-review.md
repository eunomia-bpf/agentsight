# Independent Result Review — Step 0058 Experiment 001

## Verdict

**APPROVE — 0 must-fix.**

- Run status: **valid**
- Tested hypothesis: **contradicted**
- Research value: **decisive for rejecting this constructor**
- Paper impact: **mechanism/workload boundary**
- Next decision: reject the fixed global one-shot interface; do not change the
  thesis, four RQs, or paper.

The independent reviewer explicitly applied `research-experiment-design` and
worked read-only from raw inputs rather than trusting the generated summary.

## Independent Quantitative Recalculation

The reviewer rebuilt the tested population from the target JSONL, verified
Parquet manifest, raw session responses, candidate predictions, recurrence
assignments, and causal assignments.

Recomputed coverage exactly matched:

- 405 sessions;
- 17,148 turns;
- 20,866 operations;
- 2,948 human stages;
- 251 task clusters.

All 405 raw model responses contained exactly one segment. Reconstructing
maximal contiguous equal task/subtask paths independently therefore produced
exactly one task occurrence per session, and every reconstructed occurrence
instance matched the saved predictions.

The independently recomputed standard metrics were:

- candidate B³ precision/recall/F1:
  `0.173563 / 1.000000 / 0.295788`;
- boundary F1: `0`, with `TP=0` and `FN=2543`;
- exact-span F1: `0`, with zero of 405 predicted spans matching 2,948 human
  spans;
- 10,000-resample paired task-cluster interval versus recurrence:
  `[-0.381647, -0.350845]`, positive fraction `0`.

The independently generated bootstrap draws matched the saved draws exactly,
with maximum absolute difference zero. The model artifact SHA-256 also
independently matched
`f7da7eee0f1ffa280742a293f02052d1f58d3253c9e109c1be8fb0067eb1b3a9`.

## Registered Qualitative Semantic-Contract Review

The qualitative responsibility-frame contract **FAILS**, consistently with
the quantitative non-adoption.

The mechanical schema shape is valid: across 405 unique stacks the reviewer
found no empty labels, repeated subtask paths, command-primitive actions, or
frame-order violations. The semantic interval assignment nevertheless fails:

- 93 task roots contain `Current terminal state` or terminal-screen material,
  so system context enters a responsibility frame through source task text.
- The representative 275-operation profile assigns one `Initial Setup and
  Package Installation` stack to the complete trajectory.
- Raw later turns configure Nginx and SSL, build deployment hooks, repeatedly
  diagnose SSH failures, change ports, and finish with a degraded outcome.
  The emitted phase/action/object/result therefore describe only the early
  prefix, not their assigned full interval.

The pre-fixed DevAI reference contains seven concrete requirements with
prerequisite structure. Its 34-step OpenHands trajectory visibly moves through
data loading and feature selection, model implementation, training and
evaluation, execution repair, artifact inspection, and report generation. It
confirms that meaningful task-level responsibilities exist and that one
whole-trajectory stack erases them. It remains a qualitative reference rather
than temporal gold.

## Final Disposition

The result is scientifically complete and trustworthy. It rejects the fixed
global one-shot constructor on the complete declared CodeTrace workload. It
does not authorize changing the semantic-flamegraph thesis, paper story, four
RQs, or intended task-responsibility hierarchy.
