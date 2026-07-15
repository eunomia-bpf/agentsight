# Milestone Review 001 — Blind Full-Paper Read And Attack Map

**Completed:** 2026-07-15T07:08:00-07:00  
**Parent:** Step 0027, user-requested milestone review  
**Objective:** judge the current reader-facing paper before external search or
new experiment selection  
**Paper state:** `docs/paper/main.tex` and the freshly compiled nine-page PDF  
**Initial verdict:** **4/10, weak reject; incomplete but promising**

## Reviewer Context And Routing

The paper makes load-bearing systems and AI-evaluation claims and targets
AAAI-27. It is therefore reviewed as **cross-domain, AI-venue-facing** work:
systems standards apply to source lineage, attribution, invariants, artifact,
and cost; AI/ML standards apply to labels, public trajectory benchmarks,
generalization, selection, and downstream agent evaluation. The review uses the
research-taste, systems, AI/ML, and cross-domain references.

The root reviewer was unavoidably contaminated by the active project context
and the verbatim user instruction before this read. To reduce confirmation bias,
the attack map below was formed from the complete paper and rendered figures
without consulting prior review reports or proposed next experiments during
this node. A separately requested fresh paper-only reviewer is recorded when it
returns; the final verdict must not claim an uncontaminated root read.

A separate fresh reviewer subsequently read only `docs/paper/main.tex`, its
directly included figures/tables, and the compiled PDF. It independently scored
the paper **4/10 (weak reject)** and identified the same three leading risks:
semantic correctness is conditional or incomplete, the automatic constructor
lacks untouched cross-family confirmation, and RQ2 does not yet show stable
end-to-end decision value. It additionally flags Figure 1's truncated labels at
submission size and the risk that reviewers reduce the contribution to
hierarchical grouping over pprof labels. This corroboration did not use project
history, code, canonical docs, external sources, or proposed fixes.

## Paper-Only Reconstruction

### Problem, Belief Challenge, And Principle

The real problem is that production agent histories accumulate across tasks and
runs, while developers need aggregate answers about cost, failures, unsafe
effects, and responsible workflows. The challenged default is that agent
observability is adequately served by tracing, dashboards, and per-trajectory
debugging.

The paper's principle is simple and memorable:

> Aggregate additive agent effects by stable semantic responsibility across
> trajectories, just as a profiler aggregates resource use by call-stack
> responsibility.

That principle is stronger than “draw flame graphs for agents.” It predicts
that one source-linked operation population should support multiple conserved
resource views, that semantic aggregation should concentrate recurring
problems better than execution identity alone, and that the constructed
semantic fields must be accurate enough to carry attribution.

### Artifact And Causal Chain

AgentProf reconstructs uniform operations from agent histories and lower-level
effects, assigns or imports semantic fields, projects ordered fields into
operation stacks, folds additive weights, and exports pprof-compatible output.
The automatic constructor uses cross-session action-transition recurrence;
other paths use rules, mappings, a local LLM, or TF-IDF/K-Means.

The intended cross-domain causal chain is:

```text
heterogeneous repeated agent activity
-> source-linked uniform operations
-> stable semantic fields and operation-stack projections
-> conserved cross-run aggregates
-> earlier attribution/localization of cost, failure, and unsafe behavior
```

The paper has direct evidence for the middle mechanisms, but the last edge to
developer decisions is only partially supported.

### Claimed Contributions

1. A semantic operation-stack model that replaces execution nesting with
   query-time responsibility projections.
2. AgentProf, an offline pprof-compatible implementation with pluggable intent
   attribution and stack construction.
3. Evaluation over real Codex/Claude trajectories and public agent datasets for
   source attribution, problem correspondence, tag/group accuracy, and cost.

The contribution list is conceptually economical. “Semantic operation stack,”
“operation,” and “operation stack” earn their place; the reader does not need
additional named stages or taxonomies.

## Four-RQ Claim And Evidence Map

| RQ | Paper-level question | Apparent answer from the paper | Blind-read status |
|---|---|---|---|
| RQ1 | Does semantic profiling improve resource attribution? | Scoped lineage is 100.0% precision/96.6% recall on 20 real Codex tasks, rejects 1,629 concurrent controls, conserves 1,520 attributed effects, and produces multiple resource projections. | **Substantially answered in the declared offline scope**, though “improve” is not an end-to-end comparison with a strong agent observability baseline. |
| RQ2 | Does profiler output correspond to real problems? | AgentProcess AP improves over raw action; HINTBench improves; TraceElephant is favorable only at a descriptive point. A rank-hidden reader improves recall on 5/6 tasks and precision on 4/6, but work is higher on 4/6. | **Positive but not decisive.** It supports group prioritization, not reduced analyst work, human utility, or dominance over session/step views. |
| RQ3 | How accurate are the tags? | Held-out OSWorld group boundaries and Mind2Web/ScienceWorld task partitions are positive; the final recurrence calibration is post-hoc and loses slightly to phase change on CodeTraceBench B$^3$. The paper explicitly excludes phase, action, and literal tag names. | **Not fully answered under its own stated hypothesis.** The hypothesis covers task, phase, action, and group identities, but evidence covers only task partitions and group boundaries. |
| RQ4 | What is the profiling cost? | Offline parse–construct–fold–serialize reaches 27,765 operations in 1.17 s with 18.2% time and 1.3% memory overhead over raw action at the largest point. | **Answered for offline construction**, not live capture or online agent overhead. |

## Initial Reject Hypotheses

### Blocker 1 — The paper submits an explicitly incomplete RQ3

Lines 814–833 define RQ3 over task, phase, action, literal tag identity, and
group boundaries, then state that phase, action, and literal tag names are
outside the evidence. The same gap reappears in Scope and Limitations. A full
empirical paper cannot simultaneously claim the broader positive hypothesis and
submit without evidence for load-bearing tag types. This routes to
`EXPERIMENT_GATE`, not claim deletion: use matched public annotations and fixed,
target-blind mappings/taggers to complete the promised RQ.

### Blocker 2 — RQ2 does not yet establish the headline decision consequence

The paper's motivating questions are about locating failures/unsafe effects and
finding budget concentration, but the strongest results are mixed across AP,
Work@50/80, and a fixed LLM reader. Session and step views beat AgentProf in
some cells; reader work worsens on 4/6 tasks. The result supports organization
and prioritization, but not yet that profiling yields better developer
decisions than strong tracing/dashboard views. A skeptical reviewer can call
the evidence proxy-driven unless a real, fixed decision protocol shows a
consistent consequence.

### Major 3 — The automatic constructor is visibly post-hoc and not the best
partition baseline on its cross-family development evidence

The abstract, introduction, RQ3, limitations, and conclusion repeatedly foreground
the 405-trajectory post-hoc CodeTraceBench calibration. It improves the prior
constructor, but the external phase-change baseline has slightly higher B$^3$
and wins on two of four frameworks. The OSWorld supervised comparator also
outperforms the label-free constructor. This is honest, but it makes an
implementation-selection result occupy scarce headline space without providing
independent confirmation of the mechanism.

### Major 4 — Closest-work separation is asserted, not experimentally isolated

Related Work distinguishes AgentProf from LangSmith Insights, Datadog Patterns,
NeMo Agent Toolkit, tracing systems, and CodeTracer by source-linked additive
effects, selectable conserved projections, and cross-trajectory folding. The
paper does not yet show the same-input end-to-end consequence of those
differences against the strongest feasible existing view/tool. External source
verification must determine whether the claimed gap is real and which baseline
is executable or only conceptually comparable.

### Major 5 — The joint systems-to-AI causal chain has weak end-to-end closure

RQ1 proves source association and conservation; RQ3 proves some semantic field
accuracy; RQ2 measures problem concentration. But few results hold the input,
information, and decision protocol fixed while tracing the complete path from
system effect through semantic aggregation to a correct developer decision.
Strong pieces in separate RQs do not automatically prove the joint claim.

### Minor And Submission Findings

- The title and thesis are strong and should not be narrowed.
- The abstract is dense with post-hoc implementation-selection details and
  gives little space to a decisive downstream consequence.
- Several result tables are readable but the rendered RQ2 table exposes mixed
  outcomes before the prose explains the intended claim boundary.
- The source builds cleanly with official `aaai2027` style, is anonymous, uses
  US Letter, and has seven pages of main content plus two reference-only pages.
- All fonts are embedded. Underfull boxes are cosmetic, not a blocker.
- `ReproducibilityChecklist.tex` is visibly an unfilled submission artifact and
  must be completed before submission.

## Load-Bearing External Verification Queue

The next review node must verify, from primary sources and official artifacts:

1. AAAI-27 page, anonymity, author-kit, checklist, and supplementary rules.
2. Whether LangSmith Insights, Datadog Patterns, Laminar Signals, NeMo Agent
   Toolkit, AgentOps, OpenInference/OpenTelemetry, and related agent profilers
   already provide the same-claim cross-run hierarchy, additive effect, or
   profiler projection.
3. What CodeTracer/CodeTraceBench labels actually mean and whether they support
   target-hidden phase/action evaluation rather than further tuning.
4. The official protocols and label provenance for OSWorld-Human,
   AgentProcessBench, HINTBench, TraceElephant, Mind2Web, and ScienceWorld.
5. Whether accepted agent-diagnosis work demonstrates a stronger downstream
   decision baseline or contradictory evidence against semantic grouping.

## Taste Judgment And Next Node

The work is **incomplete but promising**, not complicated-but-shallow. Its
durable simple principle and real systems artifact are credible; the problem is
that the evaluation does not yet close the broad tag-accuracy promise or the
last causal edge to developer decisions. The largest plausible claim remains
the original one: semantic profiling supplies the cross-run responsibility
plane that tracing lacks, spanning cost, quality, and safety without losing
source-linked effects.

Do not shrink that claim. External search must now determine the strongest
closest-work attack and whether the decisive next complete experiment should
finish RQ3's phase/action accuracy on existing public trajectories or strengthen
RQ2 with a fixed real decision protocol. No paper edit is authorized by this
initial read.
