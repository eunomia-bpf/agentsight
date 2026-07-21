# Result-Grounded Task Stack — Complete Full Run

## Authority And Provenance

- authoritative candidate revision: `semantic-close-projection-r7`
- authoritative ToolSandbox output: private
  `.agentsight/experiments/rq3-result-grounded-task-stack-v1/toolsandbox-full-r7/`
- authoritative CodeTrace output: private
  `.agentsight/experiments/rq3-result-grounded-task-stack-v1/codetrace-full-r7/`
- reused valid baseline revision: `fresh-causal-source-r6`
- invalid historical candidate output:
  `.agentsight/experiments/rq3-result-grounded-task-stack-v1/toolsandbox-full/`
- fixed model: Qwen2.5-3B-Instruct Q4_K_M,
  SHA-256 `626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`
- seed: `20260720`; temperature: zero

The invalid r6 candidate contained model/persona/session identity in 1,137
child CLOSE prompts and is excluded from every authoritative result below.

## Complete Public ToolSandbox Result

Coverage is complete for the released population:

- 96 public trial files;
- 12 model/persona conditions;
- 3,551 available trajectories;
- 37 official scenarios;
- 9,485 observed turns; and
- 3,867 eligible external positive-progress boundaries.

All 3,551 r7 candidate caches and all 3,551 reused r6 Step 0059 caches pass
current input-hash, request-hash, and state-linkage replay. The 14,392 candidate
requests succeeded on their first attempt. A full scan of 4,907 real CLOSE
prompts finds zero internal `instance` keys, complete sequence IDs,
model/persona condition strings, progress/key/subgoal fields, or future turns.

### Exact turn-boundary metrics

| Method | Precision | Recall | F1 | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| result-grounded OPEN/CLOSE | 0.594318 | 0.752004 | 0.663927 | 2,908 | 1,985 | 959 |
| Step 0059 stay/push/pop | 0.554208 | 0.189035 | 0.281913 | 731 | 588 | 3,136 |
| recurrence | 0.459012 | 0.990432 | 0.627303 | 3,830 | 4,514 | 37 |
| first-turn only | 0.667699 | 0.613137 | 0.639256 | 2,371 | 1,180 | 1,496 |

Candidate-minus-baseline 10,000-resample paired scenario-cluster F1 intervals
are:

- Step 0059: `[+0.319003,+0.445484]`;
- recurrence: `[-0.017832,+0.093897]`; and
- first-turn only: `[-0.003955,+0.057665]`.

The registered result is **inconclusive-not-adopted** because the recurrence
and first-turn intervals cross zero.

### Policy-collapse diagnostics

The point estimate must not be separated from the policy behavior:

- 4,907 real model CLOSE calls contain 4,893 `complete` and 14 `keep` outputs,
  or 99.715% complete;
- 4,578 additional `keep` records are synthetic latch skips, not model
  judgments;
- 3,546/3,551 trajectories predict completion at turn zero;
- all 1,153 opened children close; 1,149 last one turn, two last two turns, and
  two last four turns;
- only two turns reach root plus two children; both lack a visible outcome and
  are false positives;
- maximum depth is three including the root;
- 68 child labels exactly copy tool names; and
- seven completion contracts are the literal string `done_when`.

OPEN/CLOSE separation repairs Step 0059's severe under-closing but replaces it
with an almost-always-complete policy. It does not demonstrate reliable
variable-depth task completion.

## Complete CodeTrace Compatibility Result

Coverage is complete:

- 405 sessions;
- 17,148 source-native turns;
- 20,866 operations;
- 20,461 adjacent pairs;
- 2,948 human stage occurrences;
- 251 task clusters;
- four frameworks; and
- five source adapters.

All 405 r7 caches validate. A full scan of 13,604 real CLOSE prompts finds zero
internal-instance or complete-sequence-ID leakage. One truncated JSON response
received the recorded malformed-I/O retry described in the implementation
review.

| Constructor | B³ P | B³ R | B³ F1 | Boundary F1 | Exact-span F1 | Predicted groups |
|---|---:|---:|---:|---:|---:|---:|
| result-grounded OPEN/CLOSE | 0.772212 | 0.515752 | 0.618449 | 0.246022 | 0.027945 | 8,861 |
| Step 0059 | 0.708301 | 0.613398 | 0.657442 | 0.239777 | 0.040877 | 5,761 |
| recurrence | 0.782026 | 0.575029 | 0.662740 | 0.265571 | 0.056435 | 6,018 |

Candidate-minus-recurrence B-cubed F1 has a 10,000-resample 251-task interval
of `[-0.063739,-0.025923]`. Candidate-minus-Step0059 is
`[-0.056416,-0.023798]`. The candidate is significantly worse than both on
ordinary B-cubed compatibility.

Its higher boundary recall (`0.532049`) comes with precision `0.160005`, 7,103
false-positive boundaries, 8,861 predicted groups, and lower exact-span F1.
Behavior again collapses: among 13,604 real model CLOSE calls, 13,590 return
`complete` and 14 return `keep`; maximum depth is three; 1,678 proposed labels
are phase-like, 1,494 are commandish, and 1,410 hit the 64-character label
limit.

CodeTrace's flat stages test partition compatibility only. They do not validate
task names, ancestor topology, cross-run task equivalence, completion timing,
or the event-local phase/action/object/result suffix.

## Scientific Disposition

The tested combined OPEN/CLOSE Qwen2.5-3B policy is not adopted. Recurrence
remains the current automatic constructor. The result rejects neither the
task-stack abstraction nor the fixed positive RQ3 hypothesis; it identifies a
specific mechanism boundary: a small local model with an explicit completion
contract can mechanically close tasks, but does not reliably discriminate
completion or maintain useful nested task structure.

Step 0060 changed no paper, thesis, RQ, story, shared skill, production
implementation, or branch. Concurrent changes outside this research repository
are outside this step's provenance and were not touched.
