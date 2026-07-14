# Step 0018 Report — RQ3 Inducer Depth

## Metadata And Contract

- Started: 2026-07-14T16:01:53-07:00
- Phase: BUILD_AND_EVALUATE
- Gates: EXPERIMENT, targeted WRITE, whole-paper REVIEW, and outer audit
  complete
- Completed: 2026-07-14T16:41:41-07:00
- Status: complete
- Parent: Step 0017 principle-driven Rust operation-stack induction
- Active branch: `research/semantic-flamegraph-artifacts-v2`
- Read-only story source: `docs/agentpprof-paper` at
  `7f80c433c9555317a2aa45a78d0ff93518f4c12c`

The exact thesis remains **Agent observability needs profiling, not only
debugging.** The two core objects remain operations and operation stacks. The
four RQs remain resource attribution, problem correspondence, tag accuracy,
and profiling cost. This step tests one mechanism hypothesis within fixed RQ3;
no local mechanism result may rewrite the RQ or paper story.

Step 0017 closed in commit `c75c63c1` after recording the requested algorithm,
its complete first run, targeted WRITE, and independent outer audit. The normal
push failed with the existing large-object HTTP 500 backlog. No force push,
branch creation/switch, history rewrite, submodule edit, or shared-skill edit
occurred.

## EXPERIMENT Gate

### Selection

Step 0017's complete OSWorld-Human run showed that the single-objective Rust
inducer was substantially better than the old heuristic but remained below the
strongest simple controls. The arbitrary maximum depth of four was the only
materially binding implementation constraint exposed by the registered
diagnostics: 106/287 sessions and 488 terminal nodes reached it. The next
experiment was therefore restricted to one variable: remove that cap while
holding the complete mechanism, data, metrics, and scorer fixed.

The experiment was explicitly post-hoc because this population selected the
diagnostic. It could determine whether the cap caused under-segmentation but
could not serve as fresh independent confirmation. No other OSWorld-Human
depth, penalty, threshold, feature, model, score term, or benchmark was
admitted.

### Plan And Independent Review

The complete plan is
[`experiment-plan.md`](01-experiment-gate/loop-001-rq3-inducer-depth/experiment-plan.md).
It registered the unchanged RQ3, the single-variable hypothesis, same-binary
comparison, complete 287-session workload, existing metrics/controls, leakage
rules, real preflight, commands, validity checks, strongest degeneration
explanation, and terminal decisions.

One fresh independent reviewer returned `REVISE` because the first
`Contradicted` and `Mixed` descriptions overlapped. The root changed only the
outcome partition:

- supported means improve both metrics over depth four and clear both
  strongest simple controls;
- contradicted means improve neither metric or clear neither control; and
- mixed means every remaining valid outcome.

The same reviewer then returned `APPROVE`, confirming the categories were
mutually exclusive and collectively exhaustive. The two-round record is
[`plan-review.md`](01-experiment-gate/loop-001-rq3-inducer-depth/plan-review.md).

### Minimal Evaluator Reuse

The Rust induction algorithm did not change. The existing
`script/rq3_rust_inducer_fidelity_eval.py` was generalized rather than copied.
Its default old-heuristic path remains available. The added `depth-limit` mode:

- requires candidate depth 255 and baseline depth four;
- requires both paths to resolve to the same current release binary;
- uses method names `depth_unbounded` and `depth_four`;
- passes and verifies each declared depth;
- applies the existing scorer scrub, replay, mass, field, decision, metric,
  control, and complete-population checks; and
- compares every depth-four session row with Step 0017's candidate row.

Depth 255 is not a tuned intermediate choice. The complete population contains
at most 255 operations per session, so any nonempty recursive binary path has at
most 254 edges and this configuration is non-binding for the declared data.
Python compilation passed, the release binary rebuilt, two focused Rust
induction tests passed, and all six profile-spec CLI tests passed.

### Real Preflight And Repairs

The declared real preflight uses the 255-operation session
`236833a3-5704-47fc-888c-4f298f09f799`, selected because its Step 0017 run
recorded a cap stop. The first attempt ran the real profiler paths but raised a
Python `NameError` before artifact write because one stale `METHODS` reference
remained in pair-row composition. The only repair replaced it with the local
comparison-specific method tuple; the same command then passed.

The corrected preflight assigned and conserved all 255 operations, reproduced
the depth-four Step 0017 row, excluded oracle fields, consumed all decisions,
verified strict accepted gain, and confirmed the 255/4 configurations. Its
scientific observation was deliberately not treated as a result: four baseline
cap stops became intrinsic no-material-split stops and both configurations
emitted identical paths on that one session.

After the first complete execution, the root noticed a misleading legacy
summary key, `maximum_depth_four=true`, left over from the old comparison. The
actual method configuration was already reported correctly and the key did not
enter scoring. The key was removed and both identical commands were rerun; all
paths, counts, and metrics remained unchanged. The final raw directories contain
only corrected output. See
[`real-preflight.md`](01-experiment-gate/loop-001-rq3-inducer-depth/real-preflight.md).

### Complete Run

The final complete run executed both configurations for all 287 sessions: 574
real profiler invocations, 3,978 operations and mass per method, 3,691 adjacent
pairs, and 2,042 scorer-only human groups. All validity checks passed and every
depth-four row exactly reproduced Step 0017.

| Method | Boundary F1 | B-cubed F1 | Predicted groups |
|---|---:|---:|---:|
| Depth 255 | 0.4720 | 0.6720 | 1,939 |
| Depth 4 | 0.4231 | 0.6165 | 1,581 |
| Action change | 0.4771 | 0.6592 | 3,135 |
| Phase change | 0.3337 | 0.6655 | 1,355 |
| Always boundary | 0.6445 | 0.6784 | 3,978 |
| Supervised OOF comparator | 0.7388 | 0.8160 | 2,249 |

Depth 255 improves boundary F1 by 0.0489 and B-cubed F1 by 0.0555 over depth
four. It changes paths in 60 sessions, stops intrinsically at maximum observed
depth 26, and does not degenerate to always boundary. It still clears neither
metric's strongest simple control. The mutually exclusive registered verdict
is therefore `CONTRADICTED`. The full report is
[`full-run.md`](01-experiment-gate/loop-001-rq3-inducer-depth/full-run.md), with
raw data under `.agentsight/experiments/rq3-rust-inducer-depth-v1/full/`.

### Independent Result Review

A fresh independent reviewer recomputed all pair confusion counts, F1 values,
B-cubed values, exact deltas, split/leaf/stop counts, changed sessions, mass,
and all 287 Step 0017 baseline matches. It audited the evaluator's same-binary,
depth-only, scrub, oracle-field, replay, and scoring boundaries. The result is
`VALID / CONTRADICTED / supporting post-hoc mechanism boundary`.

The largest admitted positive conclusion is that removing the arbitrary cap
materially improves the otherwise identical built-in inducer and lets the
intrinsic objective stop at depths up to 26, but is insufficient to close the
accuracy gap to simple controls. The review prohibits broad RQ3 validation,
superiority claims, generalization to another workload, or another
OSWorld-Human parameter search. See
[`result-review.md`](01-experiment-gate/loop-001-rq3-inducer-depth/result-review.md).

EXPERIMENT exits to targeted WRITE after one valid complete result and one
independent review.

## WRITE Gate

WRITE preserved the title, Abstract, Introduction, motivation, thesis,
contributions, four RQs, Design, Evaluation, Related Work, Conclusion, and
reader-facing result story. No negative Step 0018 number entered
`docs/paper/main.tex`, and no full writing skill ran.

The allowed canonical updates were limited to current implementation and
evidence state:

- `docs/design.md` records the cap-free mechanism boundary and prohibits
  further same-population tuning;
- `docs/implementation.md` records the minimal evaluator mode, the tested
  cap-free configuration, and the distinction from the unchanged product
  default;
- `docs/evaluation.md` records the full valid result, raw/report paths, and
  fixed RQ3 disposition; and
- `docs/idea-story.md` updates only the evidence frontier. It adds no narrative
  evolution because the problem, thesis, model, RQs, scope, contributions, and
  story did not change.

WRITE routes to a fresh whole-paper REVIEW rather than selecting another local
mechanism experiment.

## REVIEW Gate

A fresh AAAI/cross-domain reviewer read the complete paper and canonical state,
searched current external closest systems and scholarship, and returned
`4/10 — Weak Reject` with high confidence. The full report is
[`whole-paper-review.md`](02-review-gate/whole-paper-review.md).

The reviewer explicitly preserves the thesis and four RQs. Its two blockers
are evidence/identity alignment rather than story ambition: the paper's
cumulative positive RQ2 conclusion exceeds the mixed workload-specific
outcomes, and the .739/.816 supervised boundary result can be mistaken for
evidence about the built-in inducer. It also identifies missing closest systems,
partial RQ3 component coverage, offline-only RQ4 scope, private-data/artifact
detail, and a weaker AI method contribution than systems integration.

External search confirms that LangSmith Insights and Datadog Patterns already
derive cross-trace hierarchical categories and aggregate metrics, while AWS and
NVIDIA now explicitly describe agent profiling. Recent Agentic CLEAR,
AgentGraph, process-observability, AgentDiagnose, TraceProbe, TELBench, AgentRx,
and STRACE increase the novelty pressure. The paper must defend the combination
of source-linked cross-layer effects, conserved additive weights, selectable
responsibility projections, and pprof compatibility rather than claim that all
agent profiling or cross-trace aggregation is absent.

The reviewer recommends a shared-trace RQ2 comparison with NVIDIA NeMo Agent
Toolkit. Root feasibility review finds that the official NeMo profiler
instruments a running supported workflow through `nat eval` callbacks and
exports profiler traces; it does not document arbitrary AgentSight/OTel trace
import. Implementing the proposed comparison now would require a new workflow
adapter or second execution path and would not be a fair one-variable replay.
The scientific target is accepted but the exact experiment is not admitted.

The highest-value feasible next route is the paused fixed RQ2 reader experiment
over existing R315 packets. It compares AgentProf organization with native/raw
views under the same downstream decision and fixed reader, directly attacking
the current RQ2 utility objection without adding another benchmark or
reimplementing NeMo. The next plan must independently recheck that admission.
Before the abstract deadline, targeted WRITE must also identify the supervised
backend precisely and center novelty on the defensible combination above.

## Capability, Memory, And Persistence

- No shared skill, project `AGENTS.md`, or submodule file changed.
- The stale evaluator names were local implementation errors already captured
  by real preflight and root output inspection; no reusable skill change is
  warranted.
- The one-variable experiment and independent reviews prevented the negative
  local result from shrinking the paper story or spawning an unbounded heuristic
  search.
- The fresh independent outer audit returns `PASS` with no must-fix finding.
  It independently reproduces the raw experiment support, confirms all three
  gates and the root's bounded NeMo/R315 disposition, and finds the evaluator
  generalization proportionate. See
  [`outer-audit-20260714T164141-0700.md`](outer-audit-20260714T164141-0700.md).
- This complete step receives one closure commit. Normal push is best effort
  and independent of scientific completion.
