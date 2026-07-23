# Step 0068 Milestone Review — Independent Outer Audit

- **Timestamp:** 2026-07-22T23:07:00-07:00
- **Parent:** `step-0068-20260722T223854-0700/milestone-review-001`
- **Objective:** determine whether the four-node milestone review is complete,
  source-grounded, faithful to the fixed thesis and RQs, disciplined about new
  experiments, and correct about hierarchy-warning semantics
- **Verdict:** **REVISE**

## Scope and method

I read the complete `iter-review-critique` skill and its research-taste,
systems, AI/ML, and cross-domain references before auditing the review. I then
read, in full:

- the current 998-line `docs/paper/main.tex` and rendered ten-page paper,
  including all claim-bearing tables and figures;
- the complete `docs/idea-story.md` and `docs/user-instruction.md`;
- `reviewer-brief.md`, the complete Grok transcript, and the complete Claude
  review;
- `01-blind-full-read.md` through `04-cycle-audit-final-verdict.md`;
- the retained RQ2 result reviews and raw summaries needed to reconstruct
  Table 1; and
- the hierarchy-warning implementation and CLI/unit tests.

The paper-only reconstruction preceded reading the milestone verdicts. External
claims were independently checked against primary or official sources:
[LangSmith Insights](https://docs.langchain.com/langsmith/insights),
[Google pprof](https://github.com/google/pprof/blob/main/doc/README.md),
[OpenTelemetry Profiles](https://opentelemetry.io/docs/specs/otel/profiles/),
[Graphectory](https://arxiv.org/abs/2512.02393),
[TraceProbe](https://arxiv.org/abs/2607.06184),
[Hodoscope](https://arxiv.org/abs/2604.11072), and
[TraceGraph](https://arxiv.org/abs/2605.31308). I also verified the primary
pages for AgentProcessBench, HINTBench, TraceElephant, and CodeTracer /
CodeTraceBench.

No paper, skill, experiment, implementation, or canonical-memory file was
changed by this audit.

## Executive assessment

The review is strong in four important respects:

1. it recognizes the durable profiling principle and does not shrink the
   thesis to a pprof exporter;
2. its external-search conclusions are substantially source-grounded and its
   synthesis correctly narrows LangSmith Insights from “the same mechanism” to
   a trace/category-level closest capability;
3. it rejects several reviewer overclaims, including interpreting
   `1 - boundary F1` as a node error rate or treating a human study as the only
   admissible utility protocol; and
4. it keeps unary, flat-fan-out, and coarse-span warnings advisory and outside
   every scientific endpoint.

However, the final gate decision is not yet auditable enough to pass. It
misclassifies the `Sem.` column as an oracle, rounds away a small negative
automatic-versus-raw effect, overlooks a real RQ1 wording shrinkage already in
the paper, promotes a composite not-yet-designed experiment into a mandatory
route, and overstates the cleanliness of one blind review.

## Table 1 arithmetic and provenance

The printed three-decimal table is arithmetically consistent:

| Workload | Sem. | Raw | Agent+Evidence | Agent-only |
|---|---:|---:|---:|---:|
| AgentProcessBench | .789 | .773 | .773 | .730 |
| HINTBench | .452 | .281 | .414 | .284 |
| TraceElephant | .230 | .121 | .252 | .194 |

The more precise retained values give:

| Workload | `Sem − Raw` | `Agent+Evidence − Raw` | `Agent+Evidence − Agent-only` |
|---|---:|---:|---:|
| AgentProcessBench | +0.015749 | **−0.000665** | +0.042924 |
| HINTBench | +0.171136 | +0.132752 | +0.130310 |
| TraceElephant | +0.108898 | +0.130656 | +0.057832 |

Therefore:

- the paper's `+.016`, `+.171`, and `+.109` values are indeed `Sem − Raw`;
- the review's automatic deltas `.000`, `+.133`, and `+.131` are correct only
  after three-decimal rounding; AgentProcessBench is slightly negative in the
  exact point estimate, not exactly tied; and
- retained source evidence improves the automatic Agent-only organization on
  all three workloads, but that is a different contrast from either
  `Sem − Raw` or `Agent+Evidence − Raw`.

The milestone review is right that the paper must make these contrasts
impossible to confuse. It is not source-grounded in repeatedly calling
`Sem.` a “human-declared oracle.” The table calls it the **declared semantic
hierarchy**. The retained standard-MAP adapter reads already-fixed semantic
groups and constructs their scores before evaluator labels enter; the Step
0033 result review independently verifies that target separation. On
AgentProcessBench, the historical semantic grouping is even partition-equivalent
to the reconstructed source-native organization. These facts make `Sem.` a
target-blind declared/reference AgentProf organization, not a demonstrated
gold semantic oracle.

This distinction changes the WRITE repair:

- the abstract's bounded statement that *semantic grouping* improves MAP is
  supported by the declared-hierarchy comparison;
- the contribution sentence claiming **automatic** operation structure
  improves problem ranking over raw action is not supported on all three
  workloads;
- the RQ2 body must say which result belongs to the declared hierarchy and
  which belongs to the automatic Agent+Evidence configuration; and
- neither the declared result nor the automatic result should be relabeled as
  the other.

Calling the whole `Sem − Raw` result “oracle-driven” would replace one
attribution error with another.

## Thesis and RQ integrity

### Thesis: PASS

The paper and review retain the exact thesis:

> **Agent observability needs profiling, not only debugging.**

The review also retains operations and operation stacks as the two core
objects. Its terminology-cleanup advice is optional WRITE economy, not a new
model or a smaller thesis.

### Four-RQ audit: REVISE

The review says the four fixed RQs are preserved, but it misses one existing
paper-level narrowing:

- fixed memory asks **“Does Semantic Profiling Improve Resource
  Attribution?”**;
- current `main.tex` asks **“Does one semantic hierarchy expose different
  resource bottlenecks?”**

Exposing a rank shift under two measures is evidence within resource
attribution, but it is not the same question as improving attribution. The
current RQ1 case answers the narrower wording. No accepted narrative-evolution
entry or user instruction authorizes replacing the fixed RQ1 hypothesis.

RQ2 and RQ4 retain their intended meanings. RQ3's “automatic operation
structure” wording is consistent with accepted evolution E009, which preserves
the fixed tag question while matching literal tags, partitions, and boundaries
to their proper standard metrics. The review should therefore flag RQ1
specifically rather than claiming blanket four-RQ preservation or reopening
RQ3.

## External search and source grounding

### PASS with a minor provenance omission

The verified external claims are accurate:

- LangSmith Insights categorizes complete traces/threads into top-level and
  nested categories and aggregates error, latency, cost, feedback, and
  attributes. It is a close capability comparator, but its documented unit is
  not AgentProf's recursively bounded operation span inside a source tree.
- pprof already supports labels, aggregation/comparison, and `tagroot` /
  `tagleaf` pseudo-frames. Semantic frames alone are not novel.
- OpenTelemetry Profiles is pprof-compatible and requires correlation with
  traces where applicable; it supports the standard-output/source-linkage
  direction but does not supply agent-semantic responsibility.
- Graphectory, TraceProbe, Hodoscope, and TraceGraph establish strong
  process-centric, cross-run, human-review, and intervention precedents.
- The four benchmark families dismissed as “unverifiable” by one reviewer have
  real primary papers. The milestone synthesis correctly rejects that blanket
  objection while preserving field/target-separation as a narrower local
  audit question.

The search report records source families and how they change the attack map,
but not the literal search queries and detailed inclusion/exclusion log
required by the review skill. Because the primary sources are linked and the
load-bearing claims reproduce, this is a documentation omission rather than a
scientific blocker.

## Is another experiment mandatory?

### REVISE: high-value candidate, not yet an authorized composite gate

The closest-capability concern is legitimate and a same-input comparison may
be the highest-value next experiment. The review oversteps when `04` makes a
new head-to-head a mandatory step before another full review and says
acceptance depends on it.

The proposed run is described as jointly testing:

- multi-resource profiling value;
- differentiation from closest hierarchical/process work; and
- decision quality,

using AgentReward and/or long-horizon data. That spans RQ1, RQ2, novelty, and
utility without yet naming one fixed RQ, one hypothesis, one runnable baseline,
or one accepted metric. It conflicts with the recorded user rule that an
experiment plan starts from an explicit RQ and one experiment tests one claim.
The search report itself also says a paid LangSmith run is optional and may not
export operation-level output.

The correct review disposition is:

- keep the closest-capability gap as a major scientific risk and identify the
  same-input comparison as a high-value experiment candidate;
- do not make a commercial product, convenience-sample user study, or
  warning-free hierarchy run mandatory;
- let the EXPERIMENT gate select one explicit fixed RQ and one falsifiable
  claim after confirming a runnable, information-fair baseline; and
- do not claim that one future run simultaneously closes RQ1, RQ2, novelty,
  and end-user utility.

This does not shrink the thesis. It prevents reviewer pressure from becoming an
underspecified experiment obligation.

## Mechanical hierarchy warnings

### PASS: advisory semantics are preserved

The review matches the implementation:

- an optional non-session/non-prompt semantic region with exactly one direct
  child emits `degenerate unary refinement`;
- an optional semantic leaf covering at least eight tool calls emits
  `coarse unrefined span`;
- a region with at least eight direct semantic children and fewer than one
  quarter recursively refined emits `flat fan-out`.

The warnings are returned in successful CLI status. Tests explicitly verify
that a coarse-span warning is emitted while profile generation succeeds.
Zero-child semantic leaves remain legal; the hygiene expectation
`children ∈ {0} ∪ [2,∞)` is not a validity contract. Warning counts do not
enter MAP, AP, bootstrap, hierarchy accuracy, or gate acceptance. No
warning-free rerun or artificial depth target is required.

## Reviewer-context and audit provenance

One disclosure must be repaired. `reviewer-claude-opus.md` says it was blind to
project artifacts but later invokes “CLAUDE.md's own invariant.” Whether this
arrived through automatic repository context or another channel, it is
unavoidable contamination under the review skill and contradicts
`01-blind-full-read.md`'s claim that both reports are clean paper-only reads.
The arithmetic finding remains valid because it is independently reproducible;
the provenance claim does not.

The final review should identify Grok as the confirmed clean transcript and
Claude as a fresh-model review with repository-instruction contamination, then
state which conclusions were independently reconstructed. It must not count
model agreement as two clean blind votes.

## Ranked findings and minimum must-fix set

1. **Blocker — scientific attribution:** replace “oracle” with the actual
   declared/reference hierarchy provenance, record exact automatic-versus-raw
   arithmetic, and scope the paper repair to declared versus automatic claims.
   **Route: REVIEW report repair, then targeted WRITE.**
2. **Blocker — user-intent consistency:** acknowledge that current RQ1 wording
   narrows the fixed resource-attribution question; route restoration or a
   full-answer explanation without changing the thesis or other RQs.
   **Route: targeted WRITE.**
3. **Major — experiment authority:** downgrade the composite head-to-head from
   a mandatory gate to a high-value candidate, or reformulate it through the
   EXPERIMENT gate as one fixed RQ and one testable claim with a runnable fair
   baseline. **Route: review disposition / EXPERIMENT selection.**
4. **Major — reviewer provenance:** disclose Claude's repository-context
   contamination and stop describing both reviews as clean paper-only reads.
   **Route: review-report repair.**

The missing literal search-query log, terminology economy, print-size figure
legibility, annotation-perturbation sensitivity, and commercial-product
availability are advisory follow-ups, not additional must-fixes.

## Decision, search-tree update, and next node

The milestone review should remain **REVISE**, but for the corrected reasons
above. Its primary-source map, broad weak-reject judgment, thesis preservation,
and warning disposition are reusable. After the four bounded report/WRITE
repairs, the orchestrator should reassess the paper before treating any new
experiment as compulsory. If an EXPERIMENT is selected, it must begin from one
of the fixed RQs and one paper-level hypothesis rather than the current
three-purpose sketch.

No canonical project-memory update is authorized by this outer audit. The
durable candidate lessons for root disposition are: review arithmetic at full
precision; distinguish declared semantic profiles from automatic backends; and
never turn a closest-work objection directly into a composite mandatory
experiment.

## Completion and uncertainty

**Audit status: complete.** All specifically requested inputs were read and the
Table 1 arithmetic was independently reconstructed. The remaining uncertainty
is scientific rather than procedural: a well-designed same-input baseline
experiment may materially strengthen the paper, but the current review does
not yet establish that this particular new run is the only route to a
top-conference-quality answer.

## Bounded Re-Audit — PASS

- **Timestamp:** 2026-07-22T23:11:30-07:00
- **Scope:** Only the four must-fixes ranked above were re-audited; this check
  did not reopen the paper-level scientific verdict.

1. **PASS — Sem. provenance and arithmetic.** The reports now identify Sem. as
   the target-blind declared/reference hierarchy rather than a gold-label
   oracle, distinguish it from the automatic configurations, and record the
   full-precision automatic-versus-Raw deltas of `-0.000665`, `+0.132752`, and
   `+0.130656`.
2. **PASS — RQ1 wording.** The reports now state the fixed RQ1 verbatim,
   identify the current wording as an unauthorized narrowing, and route
   restoration or a full-answer repair to targeted WRITE.
3. **PASS — experiment authority.** The compound comparison is now a
   high-value candidate rather than a mandatory gate. EXPERIMENT admission is
   conditional on selecting one fixed RQ, one paper-level claim, a runnable
   fair baseline, and one metric.
4. **PASS — reviewer provenance.** Grok is the sole confirmed clean
   paper-only review; Claude's automatic repository-context exposure is
   disclosed and is no longer counted as a second clean blind vote.

All four bounded must-fixes are closed. The bundle may retain **REVISE** as its
paper-level REVIEW outcome because the targeted WRITE work remains outstanding;
the milestone review artifact itself now passes this outer audit. No advisory
item was promoted to a new must-fix.
