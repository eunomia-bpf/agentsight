# Step 0056 Report — Causal Exact Task-Identity Invariant

## Step Identity And Recovery

- started: 2026-07-20T11:06:19-07:00
- phase: BUILD_AND_EVALUATE
- current gate: REVIEW (complete)
- selected paper RQ: **RQ3 — How accurate are the tags?**
- branch at entry: `research/semantic-flamegraph-artifacts-v2`
- entry commit: `191187332925`
- parent: Step 0055 visible-profile-identity construct audit
- completed: 2026-07-20T12:19:56-07:00
- status: complete

### Recovery Node

Step 0055 independently establishes exact complete visible label path as the
profile identity and rejects the fixed online Qwen2.5-3B constructor against
multi-resolution recurrence. Its outer audit admits exactly one final causal
experiment in this online branch. The paper thesis remains exactly **“Agent
observability needs profiling, not only debugging.”** The four fixed RQs,
positive hypotheses, target hierarchy, system-field metadata boundary, paper,
and canonical submodule remain unchanged.

The sole intervention is:

```text
if proposed transition is push or replace
and proposed label == current active visible leaf label exactly:
    apply stay
else:
    apply the original proposed transition unchanged
```

No label normalization, fuzzy comparison, phase rule, contraction, pruning,
depth cap, added field, prompt change, model change, or second intervention is
permitted.

## EXPERIMENT Gate

### Causal-Replay Feasibility Node

The root inspected only the completed Step 0054 source-only caches. Exact same-
leaf proposals occur in 397/405 sessions. A causally faithful replay may reuse
2,876/17,148 responses through the first affected turn because those requests
remain byte-identical; 14,272 later turns require new inference at most. Eight
unaffected sessions can reuse every response. Reuse is keyed to the complete
request, not to labels or score, and stops after the first applied intervention
changes the visible stack.

The local fixed Qwen server is healthy. The admitted experiment plan is
`experiment-001/experiment-plan.md`.

### Experiment Plan Review Node

Because the in-process reviewer thread quota was exhausted by the immediately
preceding independent reviews, the root used a separate Claude agent process as
the plan reviewer. It completely read and explicitly applied
`research-experiment-design`, remained read-only for the research repository,
and returned `APPROVE` with zero must-fix. It confirmed the single intervention,
byte-exact identity, causal prefix reuse, exact visible output, standard metric,
complete population, branch stop rule, and claim boundary. The review is
`experiment-001/plan-review.md`.

### Real Preflight Node

The approved evaluator completed one invariant-triggering trajectory from every
source layout: 87 turns, 104 operations, 22 exact-request response reuses, 65
new model calls, and 34 applied invariants. All joins, transitions, state
changes, operation paths, and standard scores are valid. The small five-task
preflight candidate reaches B-cubed F1 0.677324 versus 0.586310 for Step 0055
and 0.685875 for recurrence; its adoption interval crosses zero. These are wiring
diagnostics only, and no experimental choice changed. The record is
`experiment-001/real-preflight.md`.

### Full Causal Run Node

The complete causal replay finished all 405 trajectories, 17,148 native turns,
and 20,866 operations. The exact identity invariant applies 6,731 times across
397 sessions and lowers new-frame rate to 0.350070. Exact-visible-path B-cubed
F1 improves from 0.567111 to 0.649878, but recurrence remains 0.662740. The
paired causal-minus-recurrence interval is [-0.027838,+0.002471], so the
registered adoption condition is not met. The fixed online Qwen2.5-3B branch
is closed without changing RQ3 or the intended hierarchy. Full evidence is in
`experiment-001/full-run.md`.

### Independent Result Review Node

A separate Claude Sonnet reviewer completely read and explicitly applied
`research-experiment-design`, remained read-only, and independently rebuilt
coverage, causal reuse, intervention counts, standard metrics, uncertainty,
framework slices, and behavior diagnostics from raw artifacts. It returned
`APPROVE` with zero must-fix. The record is
`experiment-001/result-review.md`.

## WRITE Gate

### Root Result-Disposition Node

The root accepts the independent result review. `docs/evaluation.md` records
the complete causal mechanism effect, failed adoption condition, and bounded
branch closure. `docs/design.md` records that identity continuity removes much
of the error but local online transitions still fail task exit and topology.
`docs/implementation.md` records the evaluator as development-only and not
integrated into the Rust CLI.

The frozen paper, `docs/idea-story.md`, thesis, four RQs, positive RQ3
hypothesis, and canonical `docs/agentpprof-paper` submodule remain unchanged.
The negative development result is not inserted into the positive paper story.
No writing or idea-refinement skill ran.

### Task-Semantic Visualization Node

The already tracked real AgentReward shape prototype is corrected to the full
user-fixed stack:

```text
concrete task -> subtask -> phase/strategy -> semantic action
              -> operation object -> result
```

Its 204 operations and 1,112,192 reported tokens come from four complete real
attempts at one WorkArena task. Agent/model/tool/target/status and diagnostic
labels are excluded from the stack; attempt/model remains an interactive
filter. The subtask and object classes are declared mappings, so the artifact
demonstrates the desired visual and query shape but is explicitly not evidence
of automatic task induction. Updated deterministic SVG, folded, HTML, PNG,
summary, and report artifacts are under
`docs/visexp/out/task-centric-flamegraph-prototype/`.

## REVIEW Gate

### Progress Diagnostic Node

`scripts/check_progress.py` reports four RQ identifiers, one heuristic open
TODO, zero open author questions, a current evaluation update, and five
historical post-BOOTSTRAP full-writing warnings. Step 0056 did not run a full
writing pass or modify the paper, so those historical warnings are diagnostic
and not a new violation.

### Outer Audit Node

A fresh separate Claude Sonnet agent completely read and explicitly applied
`auto-research-orchestrator`, then audited the complete EXPERIMENT, WRITE, and
REVIEW records, evaluator, current diff, canonical memory, paper, submodule,
user instructions, and generated prototype. It returned `APPROVE` with zero
must-fix. It confirms the exact thesis, four fixed RQs, six-level hierarchy,
system-field metadata boundary, declared-mapping disclosure, negative-result
paper exclusion, and bounded Qwen-branch closure. The report is
`outer-audit-20260720T121956-0700.md`.

### Scientific-Contract-Unchanged Audit

- thesis exactly unchanged: **“Agent observability needs profiling, not only
  debugging.”**
- four RQs and positive RQ3 hypothesis unchanged;
- no idea refinement or story rewrite occurred;
- `docs/paper/`, `docs/idea-story.md`, and `docs/agentpprof-paper` unchanged;
- no shared skill or repository instruction changed; and
- the next route preserves the ambitious task-semantic hierarchy.

## Step Disposition

Step 0056 closes the fixed local online Qwen2.5-3B task-transition branch after
one valid full causal experiment. The identity invariant is retained as a
useful mechanism principle, not adopted as the complete constructor. The next
state remains BUILD_AND_EVALUATE / EXPERIMENT_GATE for a non-equivalent global-
context task/subtask constructor. No human intervention is required.
