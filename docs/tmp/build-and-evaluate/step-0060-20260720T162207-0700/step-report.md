# Step 0060 Report — Result-Grounded Task Stack

## Step Identity And Recovery

- started: 2026-07-20T16:22:07-07:00
- authoritative experiments completed: 2026-07-20T18:55:00-07:00
- phase: BUILD_AND_EVALUATE
- selected outer gate: EXPERIMENT
- selected paper RQ: **RQ3 — How Accurate Are the Tags?**
- branch throughout: `research/semantic-flamegraph-artifacts-v2`
- entry commit: `dde6e035ec3e`
- parent: Step 0059 literal well-nested online task stack
- status: complete

### Recovery Node

The fixed paper thesis remains exactly **“Agent observability needs profiling,
not only debugging.”** The paper title, four RQs—attribution, localization, tag
accuracy, and cost—positive hypotheses, original story, and paper files remain
unchanged.

The user's fixed main representation is:

```text
concrete task -> nested subtask* -> phase/strategy
              -> semantic action -> operation object -> result
```

Agent, model, session, prompt, tool, command, path, and status are evidence,
filters, colors, measures, or details; they are not persistent task frames.
Step 0059 proved that a legal variable-depth stack with `stay/push/pop` still
opens 5,343 children and closes only 128. Step 0060 therefore tests one
non-equivalent primitive: OPEN is grounded in visible intent, while CLOSE
checks a stored observable completion condition against the resulting outcome.

## EXPERIMENT Gate

### Public Source And Literature Node

The experiment reuses complete CodeTrace inputs and adds one complete public
completion-timing reference instead of a custom harness. Every released
ToolSandbox trial JSON from `SAP/agent-quality-inspect` was downloaded at the
fixed repository revision: 96 files, 12 model/persona conditions, 3,551
available trajectories, 37 official scenarios, and 9,485 observed turns. The
released monotone TED progress curves yield 3,867 eligible positive-progress
turn boundaries. Five positive changes in padded, unobserved suffixes are
excluded. One expected public sample is absent and was recorded rather than
fabricated.

Official ToolSandbox scenario names were checked against the Apple source.
Exact boundary P/R/F1 and ordinary B-cubed are standard metrics; the plan cites
the ToolSandbox and TED papers, Çöltekin's exact boundary definition, and Bagga
and Baldwin's B-cubed metric.

### Plan And Five-Round Review Node

`experiment-001/experiment-plan.md` registers one combined controller:

```text
OPEN(intent evidence) -> assign the turn -> CLOSE(outcome, done_when)
```

Each child stores only `(label, done_when)`. The root is immutable; depth is
variable and uncapped; each turn can open and close at most one leaf. No
threshold, score feature, contraction, lexical cleanup, post-hoc pruning,
prompt variant, model sweep, or depth rule is admitted.

An independent reviewer explicitly applied `research-experiment-design` for
five serial rounds. The review expanded the primary public population from a
partial condition to all 3,551 released trajectories, fixed one common timing
convention for candidate/Step0059/recurrence, registered the strong first-turn
control, separated flat CodeTrace compatibility from task completion, and
clarified root completion/latch semantics. Round 5 returned **APPROVE — zero
must-fix**. The record is `experiment-001/plan-review.md`.

### Implementation, Preflight, And Repair Nodes

The thin evaluator reuses existing source reconstruction, model client,
recurrence logic, standard metrics, score rows, and bootstrap code. Its causal
cache persists every complete turn and, on resume, replays input hashes,
request hashes, transition parsing, stack linkage, completion events, root
latch, and frame counters.

Initial independent implementation review corrected causal-field, target,
baseline, cache, CLI, and scorer defects, then approved r6. Real r6 preflights
passed. The first full r6 ToolSandbox candidate later failed independent raw
review because child CLOSE saw an internal `instance` containing the complete
model/persona/trial/scenario ID. Its exactly reproducible metrics are invalid
and excluded.

The minimal r7 repair projects both active stack and active leaf to semantic
`{label, done_when}`. It changes no model, prompt meaning, state transition,
metric, workload, or baseline. Candidate and baseline cache namespaces were
split, so the 3,551 valid r6 Step 0059 caches were replay-validated and reused
without 9,485 duplicate requests. Independent review approved distinct
`toolsandbox-full-r7` and `codetrace-full-r7` runs with zero must-fix.

A stale r6 CodeTrace executor survived the first foreground Ctrl-C; independent
process inspection found PID `2776171`, which was terminated before r7. One
late r7 CodeTrace OPEN response exhausted the 128-token output allowance; the
same request received one recorded 256-token malformed-I/O retry. No completed
session was repeated. Detailed records are `experiment-001/implementation-review.md`
and `experiment-001/real-preflight.md`.

### Complete ToolSandbox Node

The authoritative r7 run covers all 3,551 trajectories and all 9,485 observed
turns. Full prompt scanning over 4,907 real CLOSE calls finds zero internal IDs,
model/persona conditions, progress/key/subgoal fields, or future turns.

| Method | Precision | Recall | F1 |
|---|---:|---:|---:|
| result-grounded OPEN/CLOSE | 0.594318 | 0.752004 | 0.663927 |
| Step 0059 | 0.554208 | 0.189035 | 0.281913 |
| recurrence | 0.459012 | 0.990432 | 0.627303 |
| first-turn only | 0.667699 | 0.613137 | 0.639256 |

Candidate-minus-Step0059 has a paired scenario-cluster interval of
`[+0.319003,+0.445484]`. Intervals against recurrence
`[-0.017832,+0.093897]` and first-turn `[-0.003955,+0.057665]` cross zero. The
registered verdict is **inconclusive-not-adopted**.

The behavioral explanation is decisive. Real model CLOSE judgments are 4,893
`complete` and 14 `keep`; 3,546/3,551 trajectories predict turn-zero
completion; 1,149/1,153 children last one turn; maximum depth is three; 68
labels copy tool names; and seven completion conditions are literally
`done_when`. Synthetic root-latch keeps are reported separately.

An independent result reviewer recomputed every metric and 10,000 bootstrap
draws to floating-point equality, validated every candidate and reused baseline
cache, rescanned leakage, and returned **VALID / INCONCLUSIVE / zero
must-fix**.

### Complete CodeTrace Compatibility Node

The authoritative r7 compatibility run covers 405 sessions, 17,148 turns,
20,866 operations, 2,948 human stage occurrences, 251 task clusters, all four
frameworks, and all five source adapters. Full scanning over 13,604 real CLOSE
prompts finds zero internal-frame or complete-sequence-ID leakage.

| Constructor | B³ P | B³ R | B³ F1 | Boundary F1 | Exact-span F1 |
|---|---:|---:|---:|---:|---:|
| result-grounded OPEN/CLOSE | 0.772212 | 0.515752 | 0.618449 | 0.246022 | 0.027945 |
| Step 0059 | 0.708301 | 0.613398 | 0.657442 | 0.239777 | 0.040877 |
| recurrence | 0.782026 | 0.575029 | 0.662740 | 0.265571 | 0.056435 |

Candidate-minus-recurrence B-cubed F1 has a paired 251-task interval of
`[-0.063739,-0.025923]`; candidate-minus-Step0059 is
`[-0.056416,-0.023798]`. The candidate significantly underperforms both.
Boundary recall rises, but precision falls to `0.160005`, false positives reach
7,103, and predicted occurrences reach 8,861. Of 13,604 real model CLOSE calls,
13,590 are `complete`; maximum depth is three; 1,678 labels are phase-like,
1,494 are commandish, and 1,410 hit the 64-character label limit.

CodeTrace stages remain a compatibility reference only. They do not authorize
task topology, task labels, completion timing, cross-run equality, or the lower
semantic suffix.

The detailed results are in `experiment-001/full-run.md`.

## WRITE Gate

### Result-Disposition Node

The tested policy is not adopted. Recurrence remains the current automatic
constructor. This is a negative/inconclusive mechanism-development result, so
it does not enter `docs/paper/`, change a positive hypothesis, replace a claim,
shrink an RQ, or alter the original story. No writing or idea-refinement skill
ran, and no paper file or paper submodule changed.

Project memory only was synchronized:

- `docs/design.md` records that an explicit completion condition is useful
  state but literal 3B completion checking is insufficient;
- `docs/evaluation.md` records both complete standard results and the evidence
  boundary; and
- `docs/implementation.md` records the evaluation-only adapter, r6 leakage,
  authoritative r7 correction, and non-integration.

## REVIEW Gate

### Scientific-Contract Audit Node

- Thesis, title, four RQs, positive hypotheses, hierarchy, and contribution
  scope are unchanged.
- The result rejects one fixed Qwen2.5-3B OPEN/CLOSE policy, not the task-stack
  abstraction or RQ3.
- No negative development result enters the positive paper.
- System identity fields remain outside the valid r7 task frames.
- Standard metrics and complete real/public populations are used; diagnostics
  explain behavior but do not create hidden gates.
- No branch was created or switched.
- Step 0060 changed no shared skill, repository instruction, or production
  implementation. Concurrent changes outside this research repository are not
  attributed to this step and were not touched.
- Git operations remain independent of scientific validity.

### Efficiency And Next-State Node

This step reuses the existing CodeTrace population, all existing scorers, the
fixed local model, recurrence, Step 0059 score rows, and the complete validated
r6 baseline cache. It adds one public source collection and one controller. It
does not add a custom benchmark, score feature, cutoff, sweep, evaluator model,
or cleanup stage.

The bottleneck is no longer ambiguous: OPEN/CLOSE separation fixes under-
closing mechanically, but the 3B result checker almost always answers complete
and fails to maintain meaningful nested task structure. Another prompt phrase,
label filter, depth rule, or completion threshold would be the same failed
mechanism family. Step 0060 therefore closes this fixed 3B controller branch.

The next outer state is full-paper REVIEW with primary-source search and
different reviewer models, as already requested. That review may choose the
next paper-level evidence need; it may not rewrite the thesis/RQs/story from
this bounded negative result.

## Step Disposition

Step 0060 is scientifically complete. Both independent result reviews have
zero must-fix findings, and the independent outer audit returns **APPROVE —
zero remaining must-fix**. Its detailed record is
`outer-audit-20260720T191519-0700.md`. The authoritative r7 candidate is not
adopted; recurrence remains current; the paper remains unchanged.
