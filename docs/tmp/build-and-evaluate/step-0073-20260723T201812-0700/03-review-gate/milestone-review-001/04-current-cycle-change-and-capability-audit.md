# Current-Cycle Change and Capability Audit

**Timestamp:** 2026-07-23T20:50:54-07:00
**Parent:** Step 0073 / REVIEW Gate / milestone review 001
**Status:** complete

## Objective

Audit Step 0073 against the complete user-intent log, permanent idea story,
evaluation memory, experiment contract, paper claims, and actual capability.
Decide whether the cycle passes, whether any story/RQ drift occurred, and which
single gate runs next.

## Audited artifacts

- `000-step-entry.md`
- `01-experiment-gate/closest-work-and-baseline-audit.md`
- `experiment-001/experiment-plan.md`
- `experiment-001/plan-review-round-01.md`
- `experiment-001/plan-review-round-02.md`
- `experiment-001/plan-review-round-03.md`
- `experiment-001/plan-review-round-04.md`
- `experiment-001/preflight-report.md`
- `experiment-001/full-run-report.md`
- `experiment-001/independent-result-review.md`
- `02-write-gate/write-report.md`
- current `docs/evaluation.md`
- current `docs/idea-story.md`
- current paper

## Cycle objective versus actual output

| Intended output | Actual output | Audit |
|---|---|---|
| Test A2 on the 364-session fixed-instruction complement | Complete 364-session, 15,116-operation run | PASS |
| Exclude the 41 initial long-horizon sessions | Zero overlap; union exactly 405 | PASS |
| Use standard B³ as the primary metric | Ordinary item-level B³ used | PASS |
| Compare with strongest runnable recurrence | Same-input multi-resolution recurrence | PASS |
| Quantify task-cluster uncertainty | 10,000 paired resamples, independently reproduced | PASS |
| Judge only the tested hypothesis | Correctly marked INCONCLUSIVE | PASS |
| Record heterogeneity and fragmentation | All four frameworks, group counts, singleton count | PASS |
| Independently reconstruct result | Complete reconstruction without importing scorer | PASS |
| Integrate without story drift | Evaluation and idea memory updated; paper preserved | PASS |

## User-instruction audit

### Preserve the largest story — PASS

The cycle retains the exact thesis:

> **Agent observability needs profiling, not only debugging.**

It does not replace the profiling problem with “A2 over-fragments” or
“hierarchies have no authority.” It keeps the broad cost, quality, safety, and
population-analysis motivation.

### Keep four fixed RQs — PASS

The experiment receives RQ3 and tests one hypothesis inside it. It does not
rename, merge, remove, or narrow any RQ.

### Experiments judge tested hypotheses, not whole RQs — PASS

The full report explicitly marks the A2-over-recurrence follow-on hypothesis
inconclusive and does not call RQ3 contradicted.

### Bold hypothesis, careful validation — PASS

The plan asks for a positive follow-on effect, runs the complete population,
uses standard metrics and a strong baseline, and accepts the unfavorable point
estimate without changing the question.

### Real data and complete runs — PASS

All manifest-defined sessions, operations, pairs, frameworks, and bootstrap
draws complete. The experiment reuses a real public benchmark family and does
not stop at smoke tests.

### Avoid unnecessary experimental machinery — PASS with one workflow nit

The final design contains one scorer, one primary metric, one decisive
baseline, two diagnostics, one preflight, one full run, and one independent
review. No packet seal, hash-bound claim contract, custom score, or extra
benchmark was introduced.

Four plan-review files were produced even though the project intended fewer
follow-ups. Round 04 only confirmed removal of an unnecessary draw-equivalence
requirement and did not alter science. This is a process nit, not a reason to
invalidate or repeat the experiment.

### Do not wait for human intervention — PASS

The cycle records uncertainty, chooses a reasonable interpretation, and
continues.

### Do not silently change the story — PASS

The idea-story update is explicitly labeled evidence-only and states why the
result is not a thesis challenge. The original narrative remains complete.

### Keep negative development evidence out of the positive paper — PASS

The paper is not rewritten around the inconclusive follow-on. The full evidence
remains auditable in timestamped Markdown and current evaluation memory.

### Use standard metrics with citations — PASS

Ordinary B³ is the primary partition metric; exact boundary F1 is transparently
identified as the paper's registered protocol, not a CodeTrace leaderboard
metric.

### Automatic annotation end-to-end cost — OPEN, not a Step 0073 failure

The latest user instruction correctly identifies this as missing. Step 0073 is
an RQ3 fidelity experiment and cannot answer RQ4 by adding timing as a second
verdict. The next automatic-backend run should preserve cost telemetry so a
separate RQ4 experiment can follow without rerunning work.

## Story and RQ drift audit

No accepted story element changed:

- **Problem:** unchanged.
- **Thesis:** unchanged, exact canonical sentence retained.
- **Two scientific abstractions:** operation and operation stack remain the
  conceptual center.
- **Contribution chain:** problem/model, AgentProf system, four-RQ evaluation
  unchanged.
- **RQ3 meaning:** unchanged; the current backend result is bounded.
- **RQ4 meaning:** unchanged, but its current evidence is still incomplete
  end to end.

The memory phrase “motivates completing the already fixed source-only recursive
constructor” is a mechanism route, not a new paper contribution or abstraction.

## Claim and paper-change audit

### Correctly withheld claim

The plan's supported-only sentence—A2 remains more faithful than recurrence on
the complete follow-on—was not written because the result does not support it.

### Correctly preserved current claims

The paper's `.704 versus .663` statement is a valid aggregate description of
the complete 405-session development population. The paper already limits its
scope to named populations and calls CodeTraceBench development evidence.

### Future claim discipline

If a later backend does not resolve the follow-on sensitivity, a submission
must not imply that A2 generalizes uniformly across frameworks, lengths, or
annotation batches. That can be handled by accurate scope wording without
making the negative branch the paper's story.

### Related Work debt

Step 0073's ACT*ONOMY discovery is material and must reach a later paper WRITE.
Its absence does not invalidate the experiment, but the paper cannot be called
submission-ready while the closest semantic-profile work remains uncited.

## Capability audit

### What the current automatic A2 backend demonstrably does

- covers all 405 CodeTrace sessions;
- produces valid sparse temporal marks;
- places exact adjacent boundaries better than recurrence in the full
  population and every follow-on framework;
- creates a variable-depth visible hierarchy;
- supports canonical short names and pprof folding;
- preserves operation and token mass after marks are fixed; and
- produces real, source-drillable case-study profiles.

### What Step 0073 newly shows it does not yet do reliably

- maintain the pooled B³ advantage on the 364-session complement;
- avoid excessive short/singleton occurrences on shorter, broader sessions; or
- demonstrate one stable effect across all framework/length mixtures.

### What remains unvalidated

- gold recursive ancestor topology;
- cross-session semantic name equivalence as an external identity task;
- human diagnosis time or repair benefit;
- untouched cross-family automatic-constructor generalization; and
- end-to-end automatic annotation cost.

These are capability boundaries, not evidence that the product or thesis is
invalid.

## Root-cause assessment

The Step 0073 pattern is not “A2 cannot see transitions.” A2's boundary recall
is .684 versus recurrence's .414, and its boundary F1 is higher in all four
frameworks. The problem is the decision to split too often:

- B³ precision is high;
- B³ recall is low;
- predicted occurrence count is more than twice the official stage count; and
- nearly one third of predicted occurrences are singletons.

Therefore, a next mechanism that only finds more candidate boundaries is
misdirected. The scientific target is a context-aware stop/split decision that
preserves true transitions while declining unnecessary splits.

## Single next gate

**EXPERIMENT / RQ3 — fixed source-only recursive split/stop backend.**

One complete experiment should test one hypothesis: interval-wide context and
an explicit stop decision reduce fragmentation enough to beat recurrence on
ordinary B³ without stage access.

Minimal required outputs:

- aggregate and per-framework ordinary B³ P/R/F1;
- exact boundary P/R/F1;
- predicted groups, official groups, and singleton fraction;
- task-cluster interval for candidate minus recurrence;
- complete population/coverage checks; and
- raw annotation wall time, model-call count, input/output tokens, and resource
  telemetry retained for the immediately subsequent RQ4 cost experiment.

Cost telemetry is observation during this run, not a second RQ3 success
criterion.

## Paper status

The paper remains **promising but not submission-ready / WEAK REJECT** because
automatic-backend generalization, end-to-end annotation cost, closest-work
coverage, downstream consequence, and page length remain incomplete. Step 0073
improves scientific honesty and search direction; it does not weaken the thesis.

## Alternatives and decision

- Do not tune A2 with official stages.
- Do not contract singleton groups post hoc.
- Do not select Terminus2 or the initial long sessions as the “real” result.
- Do not switch to another benchmark before testing the already-fixed
  context-aware mechanism.
- Do not combine RQ3 quality and RQ4 cost into one pass/fail rule.
- Do retain cost telemetry so the later RQ4 experiment can reuse the same
  complete run.

## Tree/search updates

- `A2 follow-on sensitivity`: complete, closed, inconclusive.
- `A2 fragmentation diagnosis`: complete, supported.
- `recursive split/stop backend`: selected next.
- `automatic annotation end-to-end cost`: queued after a reportable backend is
  fixed.
- `story/RQ rewrite`: rejected.
- `ACT*ONOMY Related Work`: mandatory future WRITE item.

## Project-memory updates

The current evaluation and idea-story updates are consistent and sufficient.
No additional memory or paper edit is made by this review.

## Completion assessment, uncertainty, and final verdict

The review read the complete paper twice, verified primary closest work, read
the complete user/idea/evaluation memory, and independently audited every Step
0073 artifact.

**Cycle verdict: PASS.**
**Paper status: WEAK REJECT / not submission-ready, with a strong thesis worth
continuing.**
**Next gate: EXPERIMENT / RQ3 fixed recursive split/stop backend; then RQ4
end-to-end automatic annotation cost.**
