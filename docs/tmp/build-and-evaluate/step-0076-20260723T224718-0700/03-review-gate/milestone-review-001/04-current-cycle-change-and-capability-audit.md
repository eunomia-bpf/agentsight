# Current-Cycle Change and Capability Audit

**Timestamp:** 2026-07-23T23:16:24-07:00
**Parent:** Step 0076 REVIEW gate, milestone review 001
**Objective:** Audit Step 0076 and the current complete paper against user
intent, fixed story/RQs, scientific scope, and review-gate completion.

## Inputs and provenance

This audit read:

- all three preceding review reports in this milestone;
- complete `docs/user-instruction.md` and `docs/idea-story.md`;
- complete Step 0072 RQ2 plan/result/independent review and cycle reports;
- complete Step 0075 RQ4 plan/result/independent review and cycle reports;
- complete Step 0076 RQ1 plan/result/independent review and write/audit reports;
- current paper source, PDF, bibliography, figures, and build diagnostics.

No paper, code, skill, project memory, or Git state was changed by REVIEW.

## User-intent audit

### Preserved intent

- The exact thesis remains: **“Agent observability needs profiling, not only
  debugging.”**
- The four RQs remain attribution, problem correspondence, tag/structure
  accuracy, and cost.
- The paper remains ambitious across quality, safety, cost, failure, and
  wasted work; no contribution was silently narrowed.
- Experiments use real trajectories and complete public populations.
- Standard metrics are used for primary quantitative claims.
- AgentProf remains a CLI whose product output is pprof; no product frontend
  or alternative visual format was added.
- The paper keeps LLM/tool evidence leaves and variable depth without forcing
  a depth target.

### No unauthorized story change

Step 0076 is correctly recorded as an evidence-only change. It adds a
same-input organization control to the existing Git case; it does not change
the problem, thesis, RQ wording, system abstraction, or contribution chain.
The canonical submodule-derived story remains recognizable.

## Required four-part cycle audit

### 1. RQ1 post-hoc matched contrast

**Audit result:** scientifically valid and correctly bounded.

- Same 489 evidence IDs and both exact weights are used in all views.
- The accepted semantic members are joined only after native/coarse profiles
  are constructed.
- All three selected executions and all rows remain present.
- Paper text explicitly labels both task and responsibility as post-hoc.
- It does not claim discovery accuracy, a population effect, or universal
  superiority.

**Capability added:** direct proof that the reported 46.15% token focus is not
created by changing rows or weights and remains source-drillable.

**Remaining limit:** this is supporting RQ1 evidence, not a complete answer to
general attribution improvement.

### 2. RQ2 `Local` to `Direct` renaming

**Audit result:** correct clarification, no numerical or algorithmic change.

The underlying baseline was already a benchmark-native process judge or
trajectory localizer. Calling it `Direct` prevents readers from mistaking it
for a trivial local heuristic. The paper correctly explains that
Direct+AgentProf can refine only exact ties.

**Remaining limit:** the rename must not obscure that Direct+Raw+Evidence is
statistically tied with Direct+AgentProf. The abstract and conclusion still
give the weaker raw-action win more prominence than the matched result.

### 3. RQ3 baseline sufficiency

**Audit result:** adequate for a development-population mechanism comparison,
insufficient for final generalization.

Current baselines include:

- multi-resolution label-free recurrence;
- native source tree;
- source-native turn;
- raw-action grouping;
- simple boundary controls on OSWorld;
- supervised and reference-calibrated variants where their information
  requirements are explicit.

This is not a weak-baseline table. A2's complete-population gain over recurrence
has a positive task-cluster interval. However:

- A2 and recurrence do not have information/compute parity;
- CodeTrace is a development population;
- the 364-session follow-on is inconclusive on B³ against recurrence and shows
  over-fragmentation;
- one automatic annotation output does not establish stability;
- ACT*ONOMY is missing from the closest-work comparison;
- flat stage agreement does not validate recursive topology or literal
  cross-session identity.

The paper should not hide these limits behind the union aggregate.

### 4. RQ4 automatic annotation cost

**Audit result:** Step 0075 is a real improvement, but the end-to-end question
is still incomplete.

The 501.64 s source-packet reconstruction, 3.54 s deterministic postprocessing,
and 1.17 s replay values are independently verified and appropriately scoped.
The 54.36-minute artifact window is correctly not called model time.

Missing for the adopted A2 backend:

- instrumented annotation wall time;
- prompt/completion/total tokens;
- model and service version/configuration;
- number of calls/retries/failures;
- parallelism and throughput;
- repeated-run variability.

These are the distinguishing backend's cost, not optional bookkeeping.

## Cycle-change audit

| Area | Step 0076 change | Judgment |
|---|---|---|
| Paper thesis/RQs | None | Correct |
| RQ1 evidence | Adds post-hoc matched native/coarse controls | Valid supporting evidence |
| RQ2 | Renames `Local` to `Direct` and explains full-reader role | Correct clarification |
| RQ3 | No new evidence | Existing development/generalization gap remains |
| RQ4 | Inherited Step 0075 decomposition | Accurate but incomplete |
| Related work | No ACT*ONOMY or CHIEF addition | Must-fix remains |
| Format | 12-page PDF unchanged | Hard must-fix |

## Capability and recurring-workflow audit

No new project-local skill is justified by this cycle alone. The work reused
existing experiment and review workflows successfully. The recurring failure
is not missing automation; it is headline drift toward weaker favorable
comparisons after stronger matched controls are added. This should be routed
as a paper consistency/WRITE issue, not solved by adding another abstraction
or checker.

The experiment process also still lacks retained telemetry for expensive
automatic Agent annotation. Future automatic runs should record ordinary
wall time, model identity, call count, token usage, retries, and output
coverage at execution time. This is a project capability need, not a reason to
modify a global skill during REVIEW.

## Final must-fixes

Only issues that block a credible AAAI-27 submission are listed.

### Must-fix 1 — Make the paper venue-compliant

Reduce the main content from 10 pages to at most 7 and the total from 12 to at
most 9 using the official AAAI format. Critical evidence must remain in the
main body. This is a formal submission blocker.

**Route:** WRITE_GATE after scientific results stabilize.

### Must-fix 2 — Add and distinguish the two missing closest works

Compare AgentProf directly with ACT*ONOMY and CHIEF at the claim/mechanism/
evidence level. Explain why variable-depth source-linked conserved profiling
is not merely a fixed action taxonomy or a hierarchy-assisted localizer.
Use a numerical baseline only if the released artifact can be applied
faithfully.

**Route:** literature/WRITE; no new benchmark is automatically required.

### Must-fix 3 — Align all headline claims with the strongest matched RQ2 result

The abstract, Introduction results, contribution list, and Conclusion must
state that the complete profile improves over Direct-only but does not
establish a semantic-prefix ranking advantage over Direct+Raw+Evidence.
Older raw-action wins may remain as component results but cannot carry the
causal headline.

**Route:** WRITE_GATE.

### Must-fix 4 — Close A2 generalization/stability and annotation-cost evidence

Use one fixed automatic instruction on an untouched complete annotated family,
record model/config, repeated output stability, calls, tokens, wall time,
failures, and parallelism, and compare with recurrence/native/raw controls on
standard construct-matched metrics. Cost telemetry is recorded as an ordinary
system measurement; it need not become a second optimization objective.

This single controlled run addresses the two coupled uncertainties: whether
the core automatic constructor generalizes and what it actually costs.

**Route:** EXPERIMENT_GATE.

### Must-fix 5 — Give RQ1 one independent consequential test

Predeclare a population-level resource/risk responsibility and show that the
semantic view improves a real selection, inspection, or attribution outcome
over native/raw/recurrence views under identical evidence. Preserve the broad
RQ; do not replace it with the current case-study capability claim.

**Route:** EXPERIMENT_GATE.

## Non-must-fix scientific objections

These are legitimate reviewer concerns but should not block the current cycle:

- update TraceElephant bibliography metadata from arXiv to ACL 2026;
- explain OSWorld groups as same-observation batching rather than general
  semantic responsibility;
- simplify `source node`/`source tree`/`source-native hierarchy` terminology;
- distinguish automatic Agent, Agent-assisted backend, and Agent+Evidence
  consistently;
- report official benchmark metrics alongside MAP if space permits.

They should not trigger new experiments unless they materially alter an RQ
answer.

## Final verdict

**Cycle verdict:** **PASS.**

Step 0076 did exactly what it claimed: it added a valid bounded RQ1
organization control, clarified the RQ2 Direct reader, preserved the canonical
story, and introduced no invalid claim. No Step 0076 result must be reverted.

**Paper verdict:** **REJECT** for AAAI-27 in its current form.

The rejection is driven by real blockers—venue noncompliance, missing closest
work, headline mismatch with the strongest RQ2 control, incomplete A2
generalization/cost, and a still-post-hoc RQ1 answer—not by a demand for zero
scientific objections.

**Paper status:** strong thesis and credible system, but not submission-ready.

**Next gate:** **EXPERIMENT**, beginning with the fixed, instrumented
untouched-family A2 confirmation. Then perform the independent RQ1
consequential test, followed by one substantial AAAI-length WRITE and final
whole-paper review.

## Project-memory and tree updates

REVIEW itself does not edit canonical memory. The orchestrator should record:

1. Step 0076 cycle PASS and bounded RQ1 scope;
2. the five true must-fixes above;
3. ACT*ONOMY/CHIEF as mandatory closest-work branches;
4. EXPERIMENT as the next outer gate.

## Uncertainty

ACT*ONOMY, CHIEF, Hodoscope, TraceGraph, and TraceProbe are recent 2026 works;
some are preprints rather than archival publications. Their technical overlap
is still relevant to novelty even when publication status is qualified.
Whether an ACT*ONOMY artifact can support a fair numerical comparison requires
artifact inspection and should not be assumed from the paper page alone.

## Completion assessment

All four required review phases are complete. The cycle may transition, but
the paper should not be submitted in the current form.
