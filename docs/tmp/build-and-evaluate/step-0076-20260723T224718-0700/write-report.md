# Step 0076 WRITE report

Timestamp: 2026-07-23T23:24:00-07:00
Outer gate: WRITE
Status: complete

## Accepted experimental evidence

The WRITE pass used the independently reviewed Step 0076 result:

- exactly three selected real Git-deployment executions;
- 489 unique operation/evidence IDs and 4,558,192 provider-reported tokens;
- identical rows, weights, current binary, outer prefix, and call/tool leaves
  for native-source, coarse-action, and semantic organizations;
- 79 sparse tool-path transitions expanding to all 489 accepted workspace
  paths with zero mismatch or missing assignment;
- six stock-pprof-readable, exactly mass-conserving profiles;
- fixed SSH-responsibility projection of 105 operations and 2,103,587 tokens;
- 105 native source calls and six coarse action-kind branches, whose largest
  contains 39.42% of the responsibility's token mass;
- a generic `run` key containing 102 responsibility members and 97 unrelated
  operations.

The independent reviewer judged the run VALID, the descriptive matched
contrast ESTABLISHED, research value supporting, and must-fix none.

## Paper changes

### RQ1

The paper now reports the same-input control immediately after the existing
Git case. It states that only the registered middle organization differs,
reports the native-call and coarse-action fragmentation, and explains the
specific additional responsibility axis supplied by the accepted semantic
path.

The text explicitly says the case and responsibility are post-hoc selections.
It does not claim independent discovery accuracy, a population effect, or
universal interface superiority.

### RQ2 direct-reader baseline

The user's question exposed a presentation defect rather than a missing full
experiment. The former `Local` baseline already consists of benchmark-native
process judges or trajectory localizers:

- AgentProcessBench supplies released process-judge risk units;
- HINTBench supplies trajectory-localizer decisions;
- TraceElephant's localizer reads the complete trace and reference answer
  before predicting the responsible agent and decisive step.

The paper now calls this condition `Direct` and explains that
Direct+AgentProf may only refine exact ties; it cannot override a strict
ordering made by the direct reader. The numerical result is unchanged:
AgentProf adds .031/.107/.117 MAP over Direct-only, while remaining
statistically tied with Direct+Raw+Evidence.

This clarification does not turn the matched raw result into a semantic-prefix
win. It makes the existing strong Agent-reader baseline visible and preserves
the exact admissible RQ2 conclusion.

## Memory and user alignment

- `docs/evaluation.md` now records the Step 0076 RQ1 result and identifies the
  RQ2 direct reader.
- `docs/idea-story.md` records both updates as evidence-only changes that do
  not alter the original thesis or four RQs.
- `docs/user-instruction.md` preserves the user's exact baseline question.

## Build

`make` in `docs/paper/` completes successfully and produces a 12-page PDF.
There are no LaTeX errors or undefined references. Only underfull-box
diagnostics remain.
