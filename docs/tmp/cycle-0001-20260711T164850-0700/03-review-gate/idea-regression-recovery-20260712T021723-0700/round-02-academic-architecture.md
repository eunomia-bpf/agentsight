# Round 2: Academic Architecture And System Direction

## Context

- **Completed:** 2026-07-12
- **Role:** fresh independent research discussant, read-only
- **Question:** If the restored position is correct, what academic architecture
  and system direction follow from it?
- **Sources:** complete current paper and canonical documents, verbatim user
  prompts, original read-only paper, and admitted RQ2 result.
- **Excluded:** prior idea-round reports, reviewer verdicts, and recovery plan.
- **File/Git actions by discussant:** none.

## Discussant's Central Finding

The paper has recovered the right abstraction but remains too centered on
failure localization, which is only one consumer. The valid negative RQ2 result
exposes a category mismatch: a hierarchy attributes a measured signal; it
cannot manufacture a failure signal absent from visible information. Classical
profiling begins with CPU time, allocations, cache misses, or another recorded
measure and explains where that measure accumulates. The failed experiment
asked semantic grouping to both create and attribute diagnostic signal.

The stronger position remains:

> An execution tree records how one run happened, but it is not necessarily the
> right index for profiling behavior that recurs across runs. Hierarchy choice,
> like measure choice, is part of profiling semantics.

## Derived Requirements

The discussant derived four solution-independent requirements:

1. **Evidence-preserving reprojection:** flat, native, and semantic views compare
   the same recorded population and retain source context.
2. **Comparable accounting:** each view declares population, measure, and
   hierarchy and conserves additive measure where accounting is claimed.
3. **Cross-run reuse:** a semantic projection folds recurring behavior without
   using the answer against which it is evaluated. Reuse is an empirical
   property, not an identity subsystem.
4. **Decision relevance:** the projection improves or materially changes a real
   analysis under matched information and analyst/model effort. A different
   flamegraph or purer declared categories are insufficient.

These requirements derive a small system:

```text
recorded events + preserved native relations
-> operations
-> declared or development-fitted field derivation
-> flat, native, or semantic operation stack
-> weighted profile
-> source drillback and optional profile comparison
```

Taggers, clusters, boundary induction, rank rules, pprof, and SVG remain
policies or outputs.

## Scientific Prediction

When a measured behavior recurs across incidental execution boundaries, a
semantic or differential profile may concentrate its change or effect more
usefully than flat or native views. When the behavior follows execution
structure, vocabulary shifts, semantic repetition is weak, or decisive context
is local order, the native hierarchy should win.

This predicts both successes and failures and makes task dependence a possible
scientific result rather than an escape clause.

## Recommended Three-RQ Architecture

- **RQ1 — Fidelity and comparability:** Can heterogeneous traces be represented
  and reprojected into flat, source-native, and semantic profiles while
  preserving the declared measure and independently verifiable source context?
- **RQ2 — Analytical value:** For real cross-run cost, regression, safety, or
  failure analyses, when does a semantic or differential operation-stack
  profile improve the decision over flat and source-native views under matched
  information and inspection effort?
- **RQ3 — Generality and limits:** Which workload, query, and projection
  properties predict whether the advantage transfers across agents and task
  families, and when are native structure or simpler grouping sufficient?

Construction, query, inspection, and downstream-model cost belong in RQ2's
matched budget and ordinary system performance reporting. A separate RQ4 is
premature until an analytical advantage exists.

## Unexpected Directions

### Differential semantic profiling

Compare profiles across agent versions, models, prompts, policies, or
success/failure cohorts. The observed change supplies the signal, while the
hierarchy determines whether it concentrates into reusable behavioral
categories. This is closer to traditional regression profiling than
outcome-free failure ranking and needs no new abstraction.

### Representation sensitivity

If a conclusion changes under reasonable flat, native, and semantic
projections, that instability is itself important. The profiler can report
which conclusions are stable and which depend on a structural assumption.

Cross-layer effect accountability remains a compatible third branch when a
recorded file, process, network, token, or time measure supplies the signal.

## Important Unasked Question

Who chooses the hierarchy, from what information, before seeing the answer?

Without a declared pre-answer choice, enough mappings and stack orders can turn
profiling into post-hoc storytelling. The project does not need a selector
subsystem. Each experiment must declare the analytical question, measure,
visible fields, mapping, and stack order before target outcomes, then compare
that frozen choice with native and flat alternatives. Ordering independent
fields into a stack defines a query, not recovered causal ancestry.

## Main-Agent Disposition

### Accepted

- Make recorded measure versus analytical hierarchy explicit.
- Treat the RQ2 negative result as evidence that semantic grouping cannot create
  missing diagnostic signal.
- Derive the system from evidence-preserving reprojection, comparable
  accounting, reuse, and decision relevance.
- Use three RQs and fold practical cost into matched analytical value.
- Make differential profiling the leading candidate for the next decisive
  experiment; keep representation sensitivity as a core secondary result.
- Preserve cross-layer accountability as a larger research branch.

### Revised

- RQ1 becomes broader fidelity/comparability rather than only lineage.
- RQ2 covers a recorded cost/regression/safety/failure signal and its decision
  value, not outcome-free leaf ranking as the representative task.
- RQ3 explains transfer and failure conditions, including simpler alternatives.
- Existing prompt-tag separation and mapping agreement remain proxy/fidelity
  evidence, not diagnostic success.

### Rejected or demoted

- A separate cost RQ before an advantage exists.
- Recursive temporal induction as the representative mechanism.
- Treating pprof, tagger choice, ranker policy, or stack mode as novelty.
- Escaping the negative result by changing datasets while keeping the same
  outcome-free ranking premise.

### Left open for Round 3

- Which real benchmark, system evolution, or paper supplies the strongest
  differential-profile precedent and changed-measure oracle.
- Whether differential profiling or projection sensitivity should be the
  primary empirical centerpiece after external-source review.
- Whether source-native lineage fidelity needs a full experiment or one RQ1
  validation cell.

## Planned Changes

The paper and canonical documents will adopt the three-RQ architecture, make
the recorded-signal distinction explicit, integrate current cost evidence into
RQ2, and identify differential profiling as the leading next experiment without
claiming it has run. After compilation, Round 3 will search verified literature
and decide the actual experimental direction.

## Applied Changes And Verification

The main agent applied the disposition to the paper, idea story, and evaluation
frontier:

- reduced the paper from four RQs to the three RQs above;
- added the recorded-signal versus hierarchy distinction to RQ2;
- made the next candidate a differential-profile comparison rather than another
  outcome-free leaf localizer;
- folded end-to-end construction/query/inspection/model cost into RQ2;
- converted the old RQ4 subsection into current performance evidence with no
  independent scientific claim;
- retained the AgentRx/TELBench negative table and all current cost numbers;
- updated English prose and bilingual semantic comments consistently.

The rebuilt paper remains 8 pages with zero overfull boxes, zero LaTeX warnings,
and zero undefined citations or references. Round 2 is complete.
