# REVIEW 1/4 — Blind Full-Paper Read and Attack Map

**Started:** 2026-07-17T03:33:00-07:00
**Completed:** 2026-07-17T03:40:22-07:00
**Parent:** Step 0035, `REVIEW_GATE / milestone-review-001`
**Skill:** `iter-review-critique`
**Target:** AAAI 2027, genuinely cross-domain systems + AI/ML contribution

## Objective

Form a paper-only reviewer model before reading author intent, experiment
history, prior verdicts, or proposed fixes. Reconstruct the paper's principle,
mechanism, contribution and RQ claims; identify the strongest plausible reject
arguments; and enumerate the external questions that can confirm or refute
those attacks.

## Inputs and Provenance

A fresh subagent was created without conversation history. It fully read:

- `iter-review-critique/SKILL.md`;
- `research-taste.md`, `systems-review.md`, `ai-ml-review.md`, and
  `cross-domain-review.md`;
- the complete current `docs/paper/main.tex` and compiled nine-page PDF;
- every figure and table; and
- the annotation block of each cited bibliography entry.

It did not read `docs/evaluation.md`, `docs/idea-story.md`,
`docs/user-instruction.md`, `docs/tmp/`, old reviews, experiment reports, or
author proposals. It did not search the web, edit a file, run an experiment,
or use Git. The only unavoidable priming was the task's statement that the
format is AAAI 2027 and the contribution may be cross-domain.

## Paper-Only Reconstruction

### Problem and principle

The durable paper-level principle is:

> Agent observability should not stop at debugging individual traces. Causally
> joined system effects can be represented as weighted operations and folded
> across runs by stable semantic fields, enabling the aggregate responsibility
> and hotspot views that conventional profilers provide over code stacks.

The paper challenges the assumed dependence of profiling on stable code paths
and runtime call stacks. This is simple, important, memorable, and potentially
long-lived. The blind read could not yet determine whether this is a real
community belief or a strawman, because the paper itself does not compare the
full capabilities of cross-trace analytics, pprof label promotion, and
existing agent profilers.

### Mechanism and causal chain

```text
prompt / LLM call / tool action
-> capture or source adapter joins system effects to actions
-> uniform operation = string fields + additive measures
-> semantic field derivation by rules, mapping, local LLM, or clustering
-> selected field order or NPMI + k=2 transition segmentation
-> run-length-compressed action sequence becomes a frame
-> identical tuples fold with additive-weight conservation
-> pprof / flame graph / JSON
-> earlier or more reliable discovery of resource, failure, and safety hotspots
```

The evidence covers join counts, additive folding, several tag/partition
agreements, target-derived problem ranking, and core folding time. It does not
yet close the last edge from the profile to an unknown problem or developer
outcome.

### Contributions as perceived

1. A semantic operation-stack model: uniform weighted operations plus
   query-time stacks.
2. AgentProf: field derivation, stack construction, folding, and pprof export.
3. Evaluation evidence across attribution, localization, tag/group accuracy,
   and cost.

The reviewer treats item 3 as evidence rather than an independent scientific
contribution. Whether items 1 and 2 are distinct contributions depends on the
novelty boundary found by external search.

## RQ Reconstruction and Paper-Only Answers

| RQ | Paper answer | Blind assessment |
|---|---|---|
| RQ1, resource attribution | scoped join reaches 100% precision/96.6% recall; recurrence raises ordinary B-cubed F1 from 0.541 to 0.649 over raw action; mapped weight is conserved | Partial. Join correctness, partition agreement, and conservation are different constructs. B-cubed measures stage grouping, not causal resource responsibility; phase-only reaches 0.654. |
| RQ2, problem correspondence/localization | MAP improves over raw-action grouping on three target-bearing populations; a secondary fixed reader improves recall on 5/6 and precision on 4/6 tasks | Not yet sufficient for the large claim. The ranking score is itself constructed from benchmark judge votes/localizer hits, so the experiment may measure target-label smoothing by grouping rather than target-blind discovery. |
| RQ3, tag accuracy | positive task partition, task-family/action classification, and boundary/group results | Mixed tasks are combined under one RQ. Core recurrence results are development evidence and several literal-tag comparisons use only constant or majority controls. |
| RQ4, profiling cost | 27,765-operation core build in 1.17 s and 464.5 MiB, with 18.2% time and 1.3% memory over raw action | Only JSON parse, stack construction, folding, and serialization are measured. Capture, adaptation, field/tag derivation, recurrence fitting, and LLM inference are excluded; raw RSS is absent from the table. |

## Strong Evidence Already Present

- The problem-to-principle transition is clear and avoids a feature-list story.
- The formal view `(predicate, ordered fields, additive weight)` is compact.
- The 20-task real capture suite includes concurrent negative controls and
  separates join correctness from lossless AgentProf folding.
- The CodeTraceBench comparison holds operations, stages, and resources fixed
  and uses standard ordinary B-cubed as primary, with token-weighted B-cubed
  explicitly secondary.
- The paper exposes counterevidence instead of hiding it: phase-only is
  statistically indistinguishable in RQ1, and both recurrence corpora are
  described as post-hoc/development evidence.
- RQ2 uses complete input populations, a separate HINT validation snapshot,
  standard AP/MAP, and paired uncertainty.
- Headline numbers agree across prose, tables, and figures.

## Ranked Attack Map

### Blocker B1 — RQ2 may use target labels to create the ranking it evaluates

**Anchor:** RQ2 protocol beginning “Within each workload, AgentProf and
raw-action grouping use identical operations…” and the Wilson prefix scoring
rule.

AgentProcessBench group scores average benchmark judge votes. HINTBench and
TraceElephant prefix scores are functions of member target hits. This can show
that one grouping propagates known problem labels more usefully than another,
but it does not show that a deployed profile identifies an unknown problem.
Queries also exclude target-free trajectories, so false alarms over clean runs
are not measured.

**Strongest alternative explanation:** target-derived smoothing, group size,
or field order creates the MAP improvement; the operation-stack principle
does not expose failures by itself.

**Required verification:** official benchmark protocols, available inference
signals, clean populations, train/validation/test boundaries, native/strong
localizers, and standard inspection-budget metrics. If the attack holds, route
to one end-to-end EXPERIMENT using an inference-time signal fixed independently
of test targets.

### Blocker B2 — The abstraction may be known group-by plus pseudo-frames

**Anchor:** Background acknowledgement that pprof promotes labels via
`tagroot`/`tagleaf`; the formal operation/view definition; Related Work.

An operation resembles a standard event row; an operation stack resembles an
ordered categorical tuple; folding resembles weighted group-by; AgentSight
already supplies the cross-layer join. Existing products reportedly aggregate
cross-trace categories and measures. The current paper does not yet establish
a new invariant, an otherwise inexpressible query, or a prediction that a
known tag/grouping interface cannot support.

**Required verification:** primary documentation and papers for LangSmith
Insights, Datadog Patterns, NeMo Agent Toolkit profiler, pprof labels,
Perfetto/OTel/OpenInference, trajectory/process mining, and semantic trace
clustering. This is an external-search question before it is an experiment or
writing task.

### Blocker B3 — Both headline recurrence results lack untouched confirmation

**Anchor:** CodeTraceBench post-hoc qualifier and OSWorld-Human development
qualifier.

CodeTraceBench influenced constructor selection; the OSWorld rule was designed
after early corpus results. Session-held-out folds prevent direct parameter
access but not corpus-level method-selection overfitting. Table 1 also shows
phase-only at 0.654 versus recurrence at 0.649.

**Required experiment if the mechanism remains load-bearing:** freeze the
existing constructor and evaluate it, without redesign, on a genuinely new
family or split unit; include strong change-point/process-mining/embedding
sequence baselines and per-family uncertainty. Reuse already available complete
trajectories if a valid held-out population exists.

### Major M1 — RQ1 metric construct does not directly measure responsibility

Ordinary and token-weighted B-cubed measure partition agreement. Conservation
is algebraic. Neither alone establishes that a token, file effect, or process
effect was assigned to the semantically responsible unit. External search must
confirm the accepted interpretation of weighted B-cubed; any repair should add
responsibility ground truth or an intervention, not replace the standard
partition metric with another custom score.

### Major M2 — The critical provenance join is under-specified and may belong to prior AgentSight

The paper does not define the oracle behind 1,574 in-scope and 1,629 control
effects, effect strata, per-task variance, async/child-process behavior, or the
54 missed effects. External verification must determine what the AgentSight
paper already contributed and what AgentProf adds.

### Major M3 — RQ3 mixes four prediction constructs and weak controls

Task partition, literal task-family classification, literal action
classification, and sequential boundary prediction do not share one output or
baseline. V-measure is compared with a constant partition; classification is
compared with majority; boundary results use simple action/phase controls. The
0.498 action macro-F1 lacks a competitive classifier, error taxonomy, or OOD
stress test. Strong public baselines and official splits must be verified.

### Major M4 — RQ4 is core construction cost, not end-to-end profiling cost

The abstract's 1.17 s headline is accurate for the stated core boundary, but
the tagger, recurrence fitting, adapter, join, and capture may dominate. The
natural-workload slope confounds workload and size. A later experiment should
measure stages separately and use controlled scaling; it must not discard the
existing core result.

### Major M5 — Ordered fields do not automatically imply causal ancestry

A runtime stack's parent relation is dynamic ancestry, whereas
`project -> agent -> task -> phase -> op -> tool -> status` is a selected
categorical order. The paper needs either a responsibility/dependency invariant
or a precise argument that the contribution is ordered multidimensional
aggregation. HINT's selection among 24 field orders makes this distinction
load-bearing.

### Major M6 — Breadth is dominated by schema compatibility, not independent end-to-end confirmation

Many families demonstrate that mapping rules can populate the schema. The
automatic constructor's strongest evidence comes from development corpora, and
the 325 private histories mostly support descriptive flame graphs. A frozen,
public, cross-project population is the main missing real-world anchor.

### Major M7 — Core experimental decisions are not reconstructable from the paper alone

The paper omits mapping rules, fold assignments, reference sampling, 24 field
orders, LLM prompts/decoding, and several bootstrap details. External AAAI
guidance and the repository artifact must be checked before deciding whether
the repair is paper text, appendix, or artifact documentation.

## Figure and Table Attack

- **Figure 1:** demonstrates selectable weights/fields but is difficult to read
  and does not show a diagnosed hotspot or decision consequence.
- **Figure 2:** shows the uniform-operation pipeline but omits the provenance
  join, recurrence reference path, and downstream user outcome.
- **Table 1:** honestly shows phase-only is not worse than recurrence on the
  post-hoc CodeTraceBench population.
- **Table 2:** reports clear MAP gains, but its target-derived scoring is the
  central construct-validity attack.
- **Table 3:** supervised and calibrated methods are stronger than default
  label-free recurrence; the latter remains development evidence.
- **Table 4:** demonstrates practical core runtime, but lacks raw RSS and
  end-to-end stage costs.

## Research-Taste Assessment

**Paper-only classification:** `incomplete-but-promising`.

The principle is large enough and should not be narrowed to “pprof export.” It
is not yet `simple-but-deep` because the challenged belief, novelty boundary,
and end-to-end consequence are unverified. It is not yet proven
`complicated-but-shallow` because cross-run weighted profiling for agents is a
real, reusable principle. If existing products already implement the same
semantic hierarchy and aggregation, the classification will fall to
integration-heavy incremental work.

The largest claim worth defending is:

> Causally joined agent effects can be folded into cross-run semantic profiles
> that let developers find resource, failure, and safety hotspots more reliably
> at a fixed inspection budget than trace-first observability.

The paper has not yet supplied the decisive end-to-end experiment for that
claim.

## Concept Consolidation Candidates

These are reviewer proposals, not automatic edits:

- merge selectable view/profile/flame-graph view terminology;
- treat intent attribution, field derivation, and mapping as semantic field
  derivation unless intent is specifically predicted;
- treat recurrence/automatic stack construction/boundary construction as one
  transition segmenter;
- treat ingestion/projection/AgentSight adapter as one provenance-join stage;
- reconsider whether D3 is an independent mechanism or a presentation of D2;
- do not call Evaluation a scientific contribution;
- keep literal-tag fidelity distinct from structural segmentation inside RQ3.

No consolidation is authorized until external search and root disposition; it
must not silently replace the thesis or fixed four RQs.

## Provisional Verdict and Uncertainty

**Paper-only verdict:** `Weak-to-Moderate Reject`, confidence approximately
0.75.

The dominant uncertainty is external: whether same-claim product/academic work
already provides the abstraction, whether RQ2 signals are legitimate
inference-time inputs, and whether a genuinely untouched existing trajectory
population can test recurrence. The blind read does not authorize paper edits
or a new experiment.

## Search-Tree Update and Next Node

Prioritize external search in this order:

1. RQ2 benchmark protocols, labels, inference signals, clean populations, and
   strongest native baselines;
2. existing product and academic semantic/cross-trace profiling capabilities;
3. AgentSight's prior contribution boundary;
4. CodeTraceBench/OSWorld split and annotation semantics plus standard sequence
   segmentation baselines;
5. weighted B-cubed construct validity;
6. RQ3 standard classification baselines and splits;
7. AAAI 2027 format/reproducibility/artifact rules;
8. end-to-end profiler cost protocols.

**Project-memory update:** none before the final cycle-change audit.
**Completion assessment:** blind-read node complete; REVIEW gate remains open.
**Next node:** `02-external-search-and-source-verification.md`.
