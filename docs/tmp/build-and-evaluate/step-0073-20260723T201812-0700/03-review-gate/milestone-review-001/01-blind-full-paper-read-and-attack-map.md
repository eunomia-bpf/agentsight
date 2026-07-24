# Blind Full-Paper Read and Attack Map

**Timestamp:** 2026-07-23T20:50:54-07:00
**Parent:** Step 0073 / REVIEW Gate / milestone review 001
**Reviewer role:** unprimed cross-domain reviewer
**Venue lens:** AAAI main track, with systems-profiler and AI/agent-evaluation
expectations applied together
**Status:** complete

## Objective

Read the complete active paper before consulting Step 0073's experiment result
or project interpretation, identify the strongest accept and reject cases, and
record the paper-only attack map against which the current cycle will later be
audited.

## Inputs and provenance

This phase read:

- `docs/paper/main.tex` from the first through the last line;
- the complete generated `docs/paper/main.bbl`;
- the architecture source in `docs/paper/figures/fig-architecture.tex`;
- the four claim-bearing case-study renderings for Git operation count, Git
  token width, bad-side recovery, and good-side completion; and
- the active 12-page `docs/paper/main.pdf` metadata.

It deliberately did **not** read Step 0073's plan, result, review, project
memory, or user-intent log before forming the following paper-only assessment.

## Method

The paper was read linearly from title through references, then the abstract,
introduction claims, four RQ answers, contribution list, scope paragraph,
figures, and conclusion were cross-checked. The review used three lenses:

1. **Systems:** attribution model, information conservation, source lineage,
   standard-tool interoperability, cost scope, and fair baselines.
2. **AI/ML:** annotation protocol, label leakage, construct validity, complete
   populations, uncertainty, model/backend disclosure, and generalization.
3. **Cross-domain:** whether the semantic constructor is the same scientific
   object across the model, case studies, RQ2, RQ3, and RQ4.

## Paper-only summary

The paper's plain principle is strong:

> **Agent observability needs profiling, not only debugging.**

The concrete proposal is also understandable. A source adapter retains native
session/prompt/LLM/tool structure and additive measures; a backend marks nested
semantic intervals; AgentProf composes semantic responsibility with native
evidence and emits one standard pprof profile. The strongest product idea is
that the same semantic hierarchy can be replayed with operation count, tokens,
time, or system effects while retaining source drilldown.

The evaluation then claims:

- a repeated real Git task changes its apparent bottleneck when width changes
  from operation count to tokens;
- a profile refines operation-local problem scores on three complete
  localization workloads;
- automatic backends recover several kinds of literal labels, flat partitions,
  and adjacent boundaries; and
- fixed-mark parsing, folding, and pprof serialization are fast.

## Strongest accept case

The paper is more than another trace viewer. It connects a familiar systems
principle—weighted stack aggregation—to a real agent problem: recurring work
does not share stable code identity across runs. The two case studies are
population analyses rather than favorable single traces. Their pprof stacks
retain enough hierarchy and evidence to support concrete readings:

- the repeated SSH-diagnosis responsibility is only 21.47% of operations but
  46.15% of tokens; and
- failed web-agent runs contain much more recovery work, while successful runs
  contain more completion work.

The artifact contract is unusually disciplined: one pprof output, no custom
frontend, source identifiers as drilldown labels rather than high-cardinality
frames, and explicit additive-mass conservation. This gives the work a coherent
systems identity even though its annotation backends are AI methods.

The paper is also materially more honest than many agent-evaluation papers:
RQ2 reports the information-matched raw-action parity; OSWorld is called
development evidence; the action tagger discloses visible target strings; and
RQ4 explicitly states that annotation is excluded.

## Strongest reject case

The paper's strongest automatic-structure claim rests on one observed
development family and one pooled comparison:

> A2 reaches B³ F1 .704 versus .663 for recurrence on all 405
> CodeTraceBench trajectories.

Nothing in the paper-only presentation shows whether that effect is stable
across collection batches, trajectory lengths, or the four frameworks. The
single pooled interval therefore supports “strongest on this complete observed
population,” not a general automatic-constructor claim. This matters because
the automatic hierarchy is the mechanism that distinguishes AgentProf from
ordinary pprof labels and product-level semantic grouping.

The rest of RQ3 does not repair that concern. It combines different outputs:

- flat CodeTrace stage partitions and boundaries;
- OSWorld same-observation action groups;
- task-family and action closed-label classification; and
- TF-IDF/K-Means task partitions.

Each row can be valid, but together they do not validate recursive
cross-session semantic responsibility or canonical name equivalence. The paper
correctly calls the outputs complementary, yet the abstract and contribution
language invite the reader to treat them as one end-to-end semantic-operation
result.

## Ranked attack map

### Major 1 — automatic structure is not independently generalized

The paper evaluates A2 only on a development family whose stages and aggregate
results have participated in a long mechanism-development process. A
batch/framework/length sensitivity analysis could materially change the
interpretation of the .704 versus .663 headline.

**Routing:** EXPERIMENT if a fixed, non-retuned population or manifest-defined
follow-on already exists; otherwise claim-scope clarification in WRITE.

### Major 2 — RQ2 validates profile refinement, not semantic-prefix advantage

Local+AgentProf beats Local on all three workloads, but it is statistically
indistinguishable from Local+Raw+Evidence. The profile is useful as a
group/evidence refinement; this experiment does not show that recursive
semantic ancestry is the reason.

**Routing:** no score retuning. A future hierarchy-dependent user decision
would have higher value than another MAP variant.

### Major 3 — RQ4 excludes the expensive differentiating step

The reported 1.16 seconds starts after marks are fixed. Parsing and pprof
materialization are credible, but the automatic annotation step that creates
the semantic hierarchy is outside the measured system. The conclusion's
“making population profiling practical” language is therefore only about the
profiling core.

**Routing:** a separate end-to-end automatic-annotation cost experiment after
the automatic backend to be reported is fixed.

### Major 4 — RQ1 is a compelling motivation/capability case, not broad proof

RQ1 uses three repetitions of one Git deployment task within a 41-session
population. It proves that one shared hierarchy plus two additive measures
reveals a different bottleneck. It does not compare attribution decisions
against a source-native, fixed-taxonomy, or product hierarchy on multiple task
families.

**Routing:** keep it as a real case study unless a small, independently
grounded same-input attribution comparison is already available.

### Minor 1 — core-object wording has drifted

The paper calls source tree, annotation, and pprof stack “three explicit
objects,” while its simplest scientific center is operations plus operation
stacks. The three implementation artifacts are reasonable, but they should not
silently become three new scientific abstractions.

**Routing:** terminology/structure WRITE, not an experiment.

### Minor 2 — submission format is not finished

The active PDF has 12 pages. Independent of scientific merit, it is not a
finished AAAI submission under the repository's stated page target.

**Routing:** final WRITE after evidence stabilizes.

## Research-taste assessment

- **Simple principle:** yes; profiling aggregates responsible recurring work.
- **Challenged belief:** yes; runtime occurrence hierarchy is not automatically
  the right cross-run responsibility hierarchy.
- **Non-obvious consequence:** yes; changing only additive width can reverse
  the bottleneck.
- **Real systems/data:** strong; public benchmarks, real long-horizon sessions,
  real web-agent trajectories, pprof.
- **Risk of jargon accumulation:** moderate. “semantic responsibility,”
  “operation,” “annotation,” “source tree,” and “operation stack” are enough;
  additional mechanism names should stay implementation detail.
- **Largest faithful claim:** agents need population profiling over recurring
  responsibility in addition to per-run debugging.
- **Most decisive open question:** whether a fixed automatic constructor
  remains structurally faithful outside the most visibly developed portion of
  its development population.

## Sources and artifacts

- `docs/paper/main.tex`
- `docs/paper/main.bbl`
- `docs/paper/figures/fig-architecture.tex`
- `docs/visexp/out/r221-pprof-renderer-v1/*.png`
- `docs/paper/main.pdf`

## Paper/claim impact

No paper edit is authorized from a blind review. The paper-only verdict is that
the thesis and system idea are worth defending, but the automatic-structure
headline needs a sensitivity or follow-on test before it can carry a
top-conference generalization implication.

## Alternatives and decision

The bad response would be to replace the profiling thesis with a narrower
segmentation paper. The scientifically stronger response is to preserve the
paper and test the current automatic backend under a fixed complementary
population. A local negative should change the backend diagnosis before it
changes the problem, four RQs, or contribution chain.

## Tree/search updates

- Opened one RQ3 branch: fixed-instruction follow-on fidelity and
  fragmentation.
- Retained RQ4 end-to-end automatic cost as a separate later branch.
- Did not reopen RQ2 score tuning or RQ1 benchmark search.

## Project-memory updates

None. This phase is read-only.

## Completion assessment, uncertainty, and next node

Blind review is complete. The paper-only provisional verdict is **WEAK
REJECT / promising but not submission-ready**. The main uncertainty is whether
the pooled A2 result survives a fixed follow-on subset. The next node is
primary-source closest-work verification followed by a full paper reread and
Step 0073 result audit.
