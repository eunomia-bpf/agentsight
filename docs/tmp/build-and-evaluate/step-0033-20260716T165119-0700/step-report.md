# Step 0033 — Standard RQ2 Localization Metrics On Existing Trajectories

**Entered:** 2026-07-16T16:51:19-07:00

**Phase:** `BUILD_AND_EVALUATE`

**Outer sequence:** `EXPERIMENT_GATE -> WRITE_GATE -> REVIEW_GATE`

**Current state:** complete; EXPERIMENT, WRITE, and REVIEW passed

**Fixed thesis:** **Agent observability needs profiling, not only debugging.**

**Selected paper question:** **RQ2 — Does Profiler Output Correspond to Real Problems?**

## Entry Boundary And User Alignment

The root reread all of `docs/user-instruction.md`, `docs/idea-story.md`,
`docs/questions-for-author.md`, `docs/evaluation.md`, the Step 0032 report and
follow-up audit, the current RQ2 paper section, and the raw artifacts from the
three complete public localization workloads. There are no open author
questions. The read-only paper submodule remains outside scope.

The user requires standard metrics, reuse of already-run trajectories, simple
complete experiments, no hypothesis or story shrinkage, no branch change, and
no human wait. This step therefore does not collect a new benchmark, invoke a
model, alter a score, tune a cutoff, or change an operation stack. It asks
whether the existing 27,346 labeled operations support a clearer standard
information-retrieval evaluation than the current mixture of AP, Work@80, and
Work@50.

The exact thesis, four RQs, two core abstractions, three contributions, and
submodule-derived story remain unchanged. RQ2 keeps its positive hypothesis:
a target-blind semantic profile should concentrate independently annotated
problems and reduce inspection relative to flat, per-session, native, and
raw-action organization.

## EXPERIMENT_GATE

### Gate Entry And Paper-Value Admission

The current RQ2 table is difficult to assess because AgentProcessBench reports
AP while HINTBench and TraceElephant report workload-specific recall/work
points. Those work points remain useful secondary decision diagnostics, but
they do not provide one standard primary comparison across the three complete
workloads. This is a load-bearing AAAI review risk already identified by the
whole-paper review.

The existing raw outputs are sufficient for a direct reanalysis. Each
target-bearing trajectory can be treated as one ranked-retrieval query, each
atomic step as an item, and each independently annotated problem step as a
relevant item. NIST TREC defines AP per query and MAP as its arithmetic mean
over queries. The official scikit-learn implementation supplies
non-interpolated AP with score ties handled at thresholds, so no arbitrary
operation-ID ordering is introduced.

Exploratory read-only reconstruction established feasibility without creating
an experiment result: all three source adapters expose fixed per-operation
scores and scorer-only targets, and all three complete populations can be
scored without rerunning inference. The exploratory values are not admitted
until the approved plan completes, the full command writes fresh results, and
an independent reviewer recomputes them from the raw artifacts.

**Admission:** decisive RQ2 evidence clarification. A positive result would
replace the mixed primary metric presentation with standard MAP on three real
public workloads while retaining Work@80/Work@50 only as secondary inspection
diagnostics. A mixed or contradictory result would keep the current bounded
work curves and prevent a unified MAP claim; it would not alter RQ2, the
hypothesis, or the story. Reanalyzing the complete existing populations has
higher paper value than another benchmark, score, cutoff, model, or packet
study.

### Node 001 — Standard-Metric Experiment Proposed

**Context and status.** On 2026-07-16T16:51:19-07:00, the root proposed one
complete existing-trajectory experiment under unchanged RQ2. The formal plan
is [`experiment-001/experiment-plan.md`](experiment-001/experiment-plan.md).

**Inputs and method.** The experiment reuses the already reviewed
AgentProcessBench, HINTBench, and TraceElephant operations, fixed group scores,
and independent annotations. MAP over target-bearing trajectories is primary;
pooled operation AP is a standard secondary sensitivity that retains all
nonrelevant steps, including safe HINTBench trajectories. Previously reported
work-recall points remain secondary and are not averaged with MAP. The matched
raw-action view is the main baseline. Session/source-native views and the
atomic localizer or judge score are controls that bound what grouping adds.

**Scientific impact and next action.** No scientific conclusion is admitted at
proposal time. A fresh reviewer must verify that trajectory-as-query is the
right standard unit, that zero-positive trajectories and three unmappable HINT
targets are handled explicitly, that fixed scores remain target-blind, and
that the plan does not turn a metric change into a new result by relabeling old
evidence. If the plan passes, REAL PREFLIGHT will exercise one real
target-bearing trajectory from each workload before the complete 1,756-
trajectory reanalysis.

### Node 002 — Full Standard-Metric Reanalysis Completed

**Context and status.** The independent plan review first returned `REVISE`
for task-cluster uncertainty, HINT native ordinal ordering, and an undefined
qualitative verdict. The plan changed only those three items and passed after
two focused follow-ups. REAL PREFLIGHT loaded one real target-bearing
trajectory from each workload and produced six finite AgentProf/raw AP values
without making a scientific decision.

**Complete result.** The same entrypoint then processed all 1,756 trajectories
and 27,346 operations. Standard trajectory MAP is 0.7889 versus 0.7732 raw on
614 AgentProcessBench queries, 0.4529 versus 0.2815 on 400 HINTBench queries,
and 0.2302 versus 0.1213 on 220 TraceElephant queries. The paired intervals are
[0.0047, 0.0271], [0.1545, 0.1887], and [0.0780, 0.1413]. Pooled operation AP,
which retains zero-positive operations, has the same direction on all three
workloads. A fresh result reviewer independently reconstructed the source
populations, fixed score paths, every query row, HINT 935/938 sensitivity, and
30,000 bootstrap draws and returned `result status: PASS` with no must-fix.

**Decision.** The exact registered sign rule yields `VALID / COMPLETE /
SUPPORTED`. This answers the tested RQ2 ranking hypothesis; it does not claim
universal dominance, human debugging time, or lower work at every recall point.
The experiment record is under `experiment-001/`, and local raw output is under
`.agentsight/experiments/rq2-standard-map-existing-trajectories-v1/`.

## WRITE_GATE

Complete after focused repair. The targeted write replaces the mixed primary RQ2 AP/Work
presentation with one standard trajectory-MAP protocol and table across the
three complete workloads. It retains Work curves and the fixed-reader result as
secondary diagnostics and records pooled AP plus the atomic-control boundary.
The first outer review required explicit denominator wording and page economy;
both are now repaired. The Introduction and caption distinguish all 27,346
scored operations from the 614/400/220 target-bearing MAP queries. The paper
builds as nine US-letter pages, with technical content ending on page 7 and
References beginning on page 8, and has no undefined reference, overfull box,
or build failure. The exact changes and invariant audit are in `write-report.md`.

## REVIEW_GATE

Complete. The first independent outer review completed its full-paper read, external
search, source verification, cycle audit, and returned `REPAIR WRITE` for two
focused defects only. EXPERIMENT remains PASS. A focused read-only follow-up
verified the repaired denominator language, rendered page boundary, and meaning
preservation without rerunning the experiment or reopening external search. It
returned `outer review status: PASS` with no repair-created blocker.

## Closed Objections And Next-Cycle Boundary

1. The common MAP table now exposes the target-bearing query population while
   retaining pooled AP, Work, and reader evidence as secondary boundaries.
2. The atomic-score control remains explicit: it wins on AgentProcessBench and
   loses on HINTBench and TraceElephant; no story churn followed.
3. Introduction, evaluation table, evaluation prose, and internal frontier use
   the same standardized RQ2 answer.
4. Step 0033 closes the RQ2 metric-variant branch. A later outer cycle may study
   a closest product/diagnosis alternative or a paper-level decision, but must
   not reopen another RQ2 metric, cutoff, score, or benchmark variant.

## Current Transition

Close Step 0033. The next outer cycle must select a new highest-paper-value
question under the unchanged thesis and four RQs; it must not reopen the closed
RQ2 metric-variant branch.
