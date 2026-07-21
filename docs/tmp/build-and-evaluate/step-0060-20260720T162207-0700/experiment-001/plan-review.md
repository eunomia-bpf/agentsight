# Independent Experiment-Plan Review

## Review Contract

The independent reviewer read and explicitly applied
`research-experiment-design`. The review was read-only and limited to the
scientific question, baselines, standard metrics, public data, basic leakage,
execution feasibility, and whether the intervention is a non-equivalent
mechanism test. It did not request Git/hash freezing, packets, manifests,
additional evaluators, model sweeps, thresholds, or new control protocols.

## Round 1 — REVISE

The reviewer agreed that persistent `done_when` memory and separate task-open
and task-close judgments directly target Step 0059's one-way stack growth. Two
must-fix issues remained:

1. CodeTrace's flat workflow-stage labels belong to phase/strategy, not the
   nested task/subtask structure under test. B-cubed against those stages
   could reward the exact phase-as-task error the representation forbids.
2. The proposed public completion evaluation was only a future paragraph and
   did not define a complete public trajectory population, causal visible
   fields, boundary construction, baselines, uncertainty, commands, or cost.

The plan was repaired by demoting CodeTrace B-cubed to partition compatibility
and making an external per-turn completion reference the primary decision.

## Round 2 — REVISE

The reviewer accepted the complete public TED/ToolSandbox condition and agreed
that official Apple `milestone_mapping` replay was not required for the
bounded question. The released LLM-judge progress curve is sufficient to test
whether CLOSE events align with externally evaluated subgoal-progress turns,
provided the result is not called manual temporal gold or full topology/label
validation.

Two must-fix issues remained:

1. Candidate CLOSE, Step 0059 pre-turn pop, and recurrence operation boundaries
   needed one shared turn-boundary time convention, same-turn deduplication,
   terminal behavior, and explicit pooled-micro computation.
2. Trial 0 exposed a strong trivial baseline: almost every trajectory made
   progress on the first turn. A registered first-turn-only control was needed
   so a high F1 would not be mistaken for learned completion timing. Commands,
   actual cost, and primary metric/data citations were also required.

The plan was expanded to the complete released ToolSandbox trial population,
registered exact boundary timing and pooled micro P/R/F1, added the zero-cost
first-turn control, and added commands/citations.

## Round 3 — REVISE

The reviewer independently recomputed the source population and confirmed:

- 96 released trial files;
- 12 model/persona conditions;
- 3,551 available trajectories;
- 9,485 observed turns;
- 3,867 eligible positive progress boundaries;
- five positive changes only in padded, unobserved suffix positions;
- zero observed monotonicity violations; and
- first-turn-only micro P/R/F1 of
  `0.667699240 / 0.613136799 / 0.639255864`.

The only remaining issue was one stale execution line that still said 296
trajectories. It was corrected to the complete 3,551-trajectory population.

## Round 4 — REVISE

The reviewer accepted the added root-CLOSE semantics: a single-level concrete
task can emit a result/completion event without removing the immutable root;
the latch prevents unchanged subsequent turns from duplicating that event and
new child work clears the latch. One earlier sentence still claimed every
complete event popped a frame. It was corrected to distinguish subtask pop
from latched root completion.

## Round 5 — APPROVE

**APPROVE — zero remaining must-fix.**

The approved plan tests one combined result-grounded OPEN/CLOSE controller,
uses a complete external public trajectory collection, registers fair timing
for all comparisons, includes the strong trivial control, keeps CodeTrace in
its valid compatibility role, and preserves the exact paper thesis, RQs,
hierarchy, and claim scope. It may proceed to real preflight and full runs.
