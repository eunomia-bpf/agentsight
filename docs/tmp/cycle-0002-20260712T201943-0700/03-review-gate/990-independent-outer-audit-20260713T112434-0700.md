# Cycle 0002 REVIEW Gate Independent Outer Audit

**Node:** `990-independent-outer-audit-20260713T112434-0700`  
**Started:** 2026-07-13T11:17:20-07:00  
**Completed:** 2026-07-13T11:24:34-07:00  
**Phase:** BUILD_AND_EVALUATE  
**Cycle:** `cycle-0002-20260712T201943-0700`  
**Gate:** REVIEW  
**Role:** fresh independent outer auditor; not review-001, not the meta-reviewer,
not the root router, and not an owner of the canonical-memory changes  
**Status:** **REPAIR CURRENT GATE**  
**Git operations:** none  
**Files changed by this audit:** this report only

## Executive Verdict

The scientific review itself is complete and its current-paper verdict is
well supported:

> **Reject / incomplete-but-promising for AAAI-27 in the current form.**

The four-stage inner review genuinely completed a blind full-paper read,
separate systems/AI/bridging searches, primary-source verification, a complete
post-search reread, and a final cycle audit. Its strongest objections are
anchored in the current paper rather than in internal development failures.
The review preserves the exact thesis, original AgentProf story, operations and
operation stacks, and all four author-fixed RQs. It does not authorize a
smaller story.

The gate cannot yet transition to EXPERIMENT, however, because the selected
AgentTelemetry localization experiment is already known to fail its own source
eligibility condition. Independent inspection of the accepted AIware paper and
the official Zenodo `v0.1.0-aiware2026` source snapshot found a fault-detection
benchmark with run/cell-level outcomes, not released official fault-bearing
span/step identities or first-anomaly labels. The benchmark's `FaultEvent`
records `fault_type`, timestamp, call index, and details, but not a target span
or step identifier; the released result rows contain aggregate fault-detection
statistics and no localization target. Inferring a target from a detector
predicate or authoring a mapping from injected attributes would be a new label
construction, not the official target required by the accepted route.

This is not a reason to weaken RQ2 or accept run-level triage. It is one bounded
route defect. Before leaving REVIEW, the root must replace the source with an
already verified official artifact that exposes span/step localization gold, or
link direct primary evidence that an official AgentTelemetry target artifact
exists. The same correction must be made in `docs/evaluation.md` and
`docs/background-related-work.md`. No additional story discussion, whole-paper
review, literature program, control protocol, or human decision is required.

## Prior-Verdict And Priming Disclosure

I was deliberately given, and then read, the existing verdict and proposed
route. I saw:

- review-001's **Reject / incomplete-but-promising** verdict;
- its proposal to route one RQ2 experiment to AgentTelemetry;
- the meta-review's two corrections: reject a run-level fallback and exclude
  RQ4 cold/warm cost from the RQ2 experiment; and
- the root's accepted AgentTelemetry route and canonical-memory update.

I did not treat those conclusions as evidence. I independently read the current
paper, checked the source claims against primary papers and official artifacts,
and tested whether the selected source actually supplies the localization target
required by the route. The route defect reported here is contrary to the prior
accepted routing decision and therefore does not merely repeat the expected
answer.

## Question And Scope

This audit asks whether the REVIEW gate resolved its declared high-value
question well enough to route the next action without invalid evidence,
scientific-contract drift, hidden paper edits, or prohibited process expansion.
It specifically checks:

1. whether the inner review completed the declared sequence rather than
   stopping after a paper-only impression;
2. whether the current rejection verdict is supported by the submitted paper
   and primary sources;
3. whether the exact thesis, original story, two core abstractions, and four
   fixed RQs remain intact;
4. whether the meta-review corrections are necessary and correctly reflected
   in canonical memory;
5. whether the next handoff is one scientifically eligible RQ2 experiment;
6. whether unresolved paper-wide objections were ranked rather than converted
   into current-gate ceremony; and
7. whether paper, submodule, skills, and code stayed untouched during REVIEW.

The audit does not re-review experiment raw data from cycle 0002; the completed
EXPERIMENT gate's independent audit already owns that scope. It checks the
EXPERIMENT and WRITE gate reports as handoff inputs to the current REVIEW.

## Inputs Read In Full

### REVIEW entry and inner-loop reports

- [`000-gate-entry-20260713T103942-0700.md`](000-gate-entry-20260713T103942-0700.md)
- [`100-idea-unchanged-skip-20260713T103942-0700.md`](100-idea-unchanged-skip-20260713T103942-0700.md)
- [`review-001/100-blind-full-paper-read-and-attack-map.md`](review-001/100-blind-full-paper-read-and-attack-map.md)
- [`review-001/200-external-search-and-source-verification.md`](review-001/200-external-search-and-source-verification.md)
- [`review-001/300-full-paper-reread-and-scientific-assessment.md`](review-001/300-full-paper-reread-and-scientific-assessment.md)
- [`review-001/400-cycle-change-audit-final-verdict-and-routing.md`](review-001/400-cycle-change-audit-final-verdict-and-routing.md)
- [`800-meta-review-20260713T111135-0700.md`](800-meta-review-20260713T111135-0700.md)
- [`850-root-routing-and-memory-update-20260713T111625-0700.md`](850-root-routing-and-memory-update-20260713T111625-0700.md)

### Gate handoffs

- [`EXPERIMENT 999`](../01-experiment-gate/999-gate-report-20260713T110626-0700.md)
- [`WRITE 999`](../02-write-gate/999-gate-report-20260713T103942-0700.md)

### User intent and canonical memory

- [`docs/user-instruction.md`](../../../user-instruction.md)
- [`docs/idea-story.md`](../../../idea-story.md), including the complete Initial
  Narrative and E000--E008
- [`docs/evaluation.md`](../../../evaluation.md)
- [`docs/background-related-work.md`](../../../background-related-work.md)
- [`docs/questions-for-author.md`](../../../questions-for-author.md)

### Reader-facing paper

I read the complete current `docs/paper/main.tex`, including Abstract,
Introduction, Background and Motivation, Design, Implementation, all four RQ
subsections, Related Work, and Conclusion. I used the paper only to verify that
the review attacks the current reader-facing manuscript. I did not edit it.

### Orchestration rules

I read the complete `auto-research-orchestrator/SKILL.md` and the complete
`hierarchical-research-state-machine.md`, with particular attention to REVIEW
sequence, outer audit, gate exit, report requirements, evidence precedence,
canonical memory, and deferred paper-wide objections.

## Independent Method

The audit used evidence precedence in the required order:

1. primary papers, official documentation, and official released artifacts;
2. current paper claims and tables;
3. completed child reports and gate handoffs; and
4. canonical summaries.

For the external-source check, I opened the original paper or official artifact
rather than relying on search snippets. I inspected the official AgentTelemetry
accepted-source archive rather than accepting a repository README summary. I
also checked all relative Markdown links in the live canonical documents and
the root routing report. No local link is broken.

## Inner-Loop Completion Audit

### 1. Blind full-paper read: complete

Node 100 records a paper-only read before internal history and external source
search. It reconstructs the plain-language principle, causal chain, four-RQ
evidence map, strongest alternative explanation, blockers, major findings,
figure/table interpretation, and a provisional experiment target.

The report discloses limited contamination from unused files under
`docs/paper/figures/` after the main manuscript judgment was formed. Those
unused files were not used to support the verdict. This disclosure is adequate;
it does not invalidate the paper-only attack because the load-bearing findings
are directly reproducible from `main.tex` and the rendered table/figures.

### 2. Separate systems, AI/ML, and bridging search: complete

Node 200 uses separate query families and opens source-native papers,
documentation, repositories, datasets, and venue rules. It covers:

- systems mechanism and baseline lineage: Data Cube, Pivot Tracing, workflow-
  centric tracing, Perfetto, pprof, aggregate traces, and AgentSight;
- AI/ML diagnosis and tag evaluation: AgentRx, TELBench, V-measure,
  CLINC150, MASSIVE, and AgentTelemetry; and
- bridging/product capability: Datadog Patterns, Langfuse, LangSmith,
  OpenTelemetry GenAI, production workload evidence, and AAAI-27 rules.

The search does not merely collect supporting citations. Data Cube, Pivot
Tracing, pprof, Datadog Patterns, and AgentTelemetry are used to strengthen
novelty and baseline attacks; workflow-centric tracing is used as contradictory
evidence; AgentRx and TELBench raise the localization bar. This is real external
pressure rather than same-context reflection.

### 3. Primary-source verification: substantially complete

The decisive mechanism and venue claims survive independent verification. The
AgentTelemetry routing claim does not; that defect is treated separately below.

### 4. Post-search whole-paper reread: complete

Node 300 rereads the full paper after search, reconstructs the end-to-end causal
chain, updates the blocker map, checks every RQ, and separately audits all four
reader-facing figures/tables. Its strongest conclusions are tied to exact
paper numbers and mechanism text. It does not substitute internal experiment
history for what an AAAI reviewer can see.

### 5. Cycle-change and process audit: complete

Node 400 opens internal history only after the scientific verdict is fixed. It
checks story fidelity, current experiment authorization, process deviations,
canonical lag, and the next route. It correctly distinguishes process debt from
valid scientific evidence and does not demand reproducibility ceremony.

### Inner-loop conclusion

The review inner loop completed its declared scientific scope. It must not be
rerun merely because its final source choice needs a bounded correction.

## Current-Paper Verdict Audit

The **Reject / incomplete-but-promising** verdict is supported by the current
paper.

### RQ1: attribution is not independently validated

The paper scores whether groups mix `prompt_tag` categories and then adds
`prompt_tag` to the grouping key. The zero-mixing `session + prompt_tag`
condition is therefore a construction check, not independent responsibility
truth. The displayed prompt-only change is 90.4% to 36.7%, while Abstract,
Introduction, and Conclusion say AgentProf “separates over 90%.” The paper does
not give a numerator and denominator that reconciles that headline. It also
does not validate prompt-to-tool/process/file/network ownership under
concurrency, subprocesses, async work, missing events, or ambiguous parentage.

The review correctly treats this as missing RQ1 evidence, not permission to
delete RQ1 or change the thesis.

### RQ2: the displayed tradeoff is not a localization win

Table 1 reports operation-stack AP 0.312, below per-session 0.348 and native
hierarchy 0.357. The 9.4% work headline accompanies median top-five recall
0.188; at 30% inspection, recall is 0.390. The manuscript also states that
fields, mappings, ranking, and depth were changed and rerun on the same
operations. The review is therefore correct that the current result is a
tradeoff point with adaptation risk, not evidence of lower inspection at
matched localization recall.

### RQ3: a proxy mechanism is evaluated

The paper's load-bearing semantic mechanism includes regex and local-LLM prompt
tagging, but RQ3 maps structured dataset fields into `phase` and compares the
partition with native `action`. V-measure measures partition agreement; it does
not prove label-name semantics, prompt-tagger correctness, OOS behavior,
coverage, stability, or downstream inheritance. The review correctly identifies
this construct mismatch.

### RQ4: the cold semantic-enrichment path is excluded

The paper calls 1.6 seconds “complete profiling,” while separately reporting
35,136 llama.cpp calls without measuring the complete cold-path wall time or
resources. Cached folding/query timing is useful, but it is not the full RQ4
answer. The review's major objection is supported.

### Novelty and status-quo comparison

The formal operation-stack model is an ordered field projection followed by
additive aggregation. The paper's comparison to a one-tag flat `GROUP BY` is
too weak, and its characterization of current agent observability as primarily
per-execution or input-only is capability-inaccurate. Primary sources support
that attack. This does not make the broad profiling thesis uninteresting; it
means the empirical work must isolate the cross-layer semantic responsibility
and decision outcome from conventional aggregation.

### Research-taste conclusion

The direction retains a simple, memorable, consequential principle: treat many
agent runs as profiling samples and attribute additive measured effects to
recurring responsibility. The challenged belief remains important when stated
as application-level traces and dashboards being sufficient across prompt,
model, tool, process, and OS boundaries. The current failure is incomplete
mechanism and outcome evidence, not excessive idea complexity or a reason for
a smaller paper. The review's `incomplete-but-promising` classification is
appropriate.

## Independent Primary-Source Findings

| Source | Independently verified fact | Effect on review |
|---|---|---|
| [Data Cube](https://arxiv.org/pdf/cs/0701155) | Defines multidimensional aggregation and explicitly generalizes group-by, cross-tab, roll-up, drill-down, histogram, and subtotals. | Confirms that query-time multi-resolution grouping alone is not a novel abstraction. |
| [Pivot Tracing](https://cs.brown.edu/~rfonseca/pubs/mace15pivot.pdf) | Uses causal metadata propagation and a happened-before join so metrics at one point can be selected, filtered, and grouped by fields from causally preceding events across components. | Confirms the closest systems-mechanism pressure and the need to validate AgentProf's distinct responsibility reconstruction. |
| [PerfettoSQL](https://perfetto.dev/docs/analysis/perfetto-sql-getting-started) | Queries traces as databases, supports derived metrics and programmatic/batch analysis, and reuses queries across trace datasets. | Confirms that flat/session-only trace baselines are not the strongest information-equivalent alternative. |
| [pprof official README](https://github.com/google/pprof/blob/main/doc/README.md) | Treats tags as additional dimensions and supports `tagroot`/`tagleaf` pseudo stack frames. | Confirms that label-derived stack positions are existing infrastructure, though not automatic agent semantics. |
| [Datadog Patterns](https://docs.datadoghq.com/llm_observability/monitoring/patterns/) | Automatically clusters production interactions, builds topic hierarchies, reports cost/tokens/errors/latency/evals by topic, supports drilldown, and can analyze failed-evaluation traffic. | Directly contradicts the paper's input-clustering-only characterization and confirms a strong product baseline. |
| [AgentTelemetry AIware paper](https://doi.org/10.1145/3805760.3814931) and [official accepted snapshot](https://doi.org/10.5281/zenodo.20129006) | Defines 14 fault types, 5 observability conditions, 7 frameworks, 490 detection cells, and 2,940 raw configurations across six mock-LLM model/seed settings. The released task is fault detection and reports FDR; it does not release official target span/step IDs. | Confirms same-claim pressure and OTel baselines, but invalidates the selected localization-source handoff as currently written. |
| [AgentRx](https://github.com/microsoft/AgentRx) and its [paper](https://arxiv.org/abs/2602.02475) | Releases 115 failed trajectories with manually annotated critical failure steps and a ten-category taxonomy; reports exact and ±1/±3/±5 step accuracy and distance. | Confirms that official step-level RQ2 targets exist in a source already examined by the review. |
| [TELBench/DRIFT](https://github.com/NJU-LINK/DRIFT) and its [paper](https://arxiv.org/abs/2606.02060) | Builds a 2,790-trajectory annotated corpus and a verified 1,000-instance benchmark with official semantic-span error labels; reports macro P/R/F1 and first-error accuracy. | Confirms a second already verified source family with the target granularity required by RQ2. |
| [AAAI-27 Main Track call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/) | Limits main content to 7 pages with references only through page 9, requires a reproducibility checklist, welcomes bridge work, and evaluates significance/novelty, empirical soundness, AI relevance, and clarity. | Confirms that the current nine-page shape can fit but the paper is not scientifically or procedurally submission-ready. |

### Source-fidelity qualifications

Two Node-200 details need correction but do not invalidate the scientific
rejection verdict:

1. The report links `github.com/agenttelemetry/agenttelemetry`, which does not
   identify the released repository. The official PyPI metadata, paper, and
   Zenodo snapshot point to
   `github.com/Krishnachaitanyakc/AgentTelemetry`.
2. The AIware 2,940 count is 490 fault-detection cells enumerated across six
   mock-LLM model/seed configurations, not six generic repeated trials.

The accepted paper and Zenodo snapshot remain real and source the capability
claims. These two details are source-description repairs, not grounds for a new
literature review.

## AgentTelemetry Target-Granularity Finding

This is the gate's single transition-invalidating defect.

### What the accepted artifact contains

- `benchmarks/faults/injector.py` defines `FaultEvent` with `fault_type`,
  timestamp, call index, and details.
- `benchmarks/run_benchmarks.py` records one `BenchmarkResult` per cell with
  fault type, condition, FDR, time-to-root-cause computation time, precision,
  span sufficiency, span counts, token/cost counts, and injected/detected fault
  counts.
- `benchmarks/results.tsv`, ablation results, and statistical outputs contain
  run/cell-level detection outcomes.
- the accepted snapshot contains no released target-span/target-step annotation
  table and no raw trace corpus with an official fault-bearing span ID.
- the paper's primary RQ is whether a telemetry condition detects each injected
  fault, not where the first fault-bearing span occurs.

### Why detector predicates are not official localization targets

Several faults are encoded through attributes on a particular kind of span,
and others are generated by repeated events. A new evaluation could derive a
candidate fault span from those attributes or thresholds. That would be an
author-defined target construction and in some cases would make the same
detector rule define both ground truth and success. Multi-event faults such as
loops, token growth, and delegation cycles also do not have a unique first
fault-bearing span independent of the chosen threshold.

The current route correctly forbids handmade labels and run-level fallback.
Therefore it cannot simultaneously treat those derived predicates as the
required official span/step gold.

### Consequence

The source eligibility question is no longer an unknown that should be deferred
to the next EXPERIMENT preflight. The accepted source snapshot is available and
has been inspected now. Entering EXPERIMENT with an already ineligible source
would manufacture a known no-run gate and fail the outer controller's
high-value selection rule.

## Scientific-Contract And Story Audit

### Exact thesis and core abstractions

The exact thesis remains:

> **Agent observability needs profiling, not only debugging.**

It appears in the current paper's Abstract, Introduction, and Conclusion; in
the permanent Initial Narrative and restored frontier; and in the literature
frontier. Operations and operation stacks remain the only core abstractions.

### Four fixed RQs

The current paper contains exactly these four Evaluation subsections:

1. RQ1: Resource Attribution;
2. RQ2: Real-Problem Localization;
3. RQ3: Tag Accuracy; and
4. RQ4: Profiling Cost.

The review attacks their evidence without renaming, merging, deleting, or
narrowing them. The selected tested hypothesis stays inside RQ2. The route
repair required by this audit must change only the external source/protocol,
not the RQ or positive hypothesis.

### Idea history and story change

`docs/idea-story.md` retains the complete Initial Narrative and E000--E008.
E008 remains the last accepted evolution entry and records materialization of
the submodule story into the AAAI workspace. REVIEW created no E009 entry,
accepted no new thesis or contribution, and did not promote “semantic
continuation of causal tracing” into the paper or current idea frontier.

The BUILD_AND_EVALUATE idea-unchanged skip is therefore correct. No idea
discussion or root idea disposition belonged in this gate.

## Meta-Review Correction Audit

Both meta-review corrections are necessary and scientifically correct.

### Correction 1: run-level triage is not localization

RQ2 is fixed as correspondence to real problems through localization and
reduced inspection. Replacing span/step localization with classification of
already fault-labelled runs would be an easier task and would silently narrow
the user's intent. The meta-review correctly rejects this fallback.

### Correction 2: RQ4 cost does not belong inside the RQ2 experiment

Cold/warm end-to-end profiling cost is its own author-fixed RQ4. Making it an
outcome program inside the selected RQ2 experiment would violate the
one-RQ/one-experiment boundary. Ordinary run-resource facts may be recorded for
execution validity, but the experiment must not claim an RQ4 answer. The
meta-review correctly removes it.

### Canonical propagation

The two corrections are accurately written into both live frontiers:

- `docs/evaluation.md` rejects run-level-only labels, requires official
  span/step or first-anomaly identities, excludes RQ3/RQ4 subprograms, and names
  one fixed RQ2 decision; and
- `docs/background-related-work.md` carries the same eligibility boundary,
  preserves RQ1/RQ3/RQ4 as siblings, and prevents a run-level substitute.

All relative links in both files resolve. The memory update is internally
consistent with the meta-review, but its selected source is now invalidated by
the direct artifact inspection above. Both canonical files therefore require
the same bounded source-route correction before gate exit.

## Process-Simplicity Audit

The accepted root route does not inflate an ordinary experiment plan into the
prohibited control machinery. It explicitly requires one Markdown plan and
forbids Git hashes, seals, packets, manifests, attestations, keys, immutable
registries, and executable finalizers. It treats target blindness, split,
visible fields, metrics, and success criteria as ordinary scientific validity,
not as an integrity ceremony.

The review does use “freeze” informally in some scientific prose to mean that a
policy is fixed before held-out scoring. The final root handoff replaces that
with plan-defined/approved-plan language and creates no non-Markdown contract.
No freeze protocol exists.

Paper-wide reproducibility, novelty, RQ1, RQ3, and RQ4 objections remain
important, but none invalidates the REVIEW node's ability to decide the next
experiment. They must not be turned into new current-gate checkers or demanded
as a zero-objection condition.

## Memory, Artifact, And Ownership Audit

- `docs/questions-for-author.md` contains no open question. The route repair
  does not require human judgment.
- `scripts/check_progress.py` is absent. The meta-review correctly records the
  absence as diagnostic only and invents no output.
- The current paper files predate REVIEW entry and still match the WRITE-gate
  handoff snapshot. REVIEW did not edit `docs/paper/`.
- The submodule paper file predates this cycle and was not changed.
- No file under the shared skills repository was changed after REVIEW entry.
- No source-code or experiment-result file was changed during REVIEW.
- After REVIEW entry, repository changes are limited to REVIEW reports, the
  historical EXPERIMENT closeout/verification reports, the archived literature
  frontier, and the two declared canonical frontier updates.
- This audit performed no Git operation and did not inspect or change branches.

The root routing report accurately states that only `docs/evaluation.md` and
`docs/background-related-work.md` changed as live canonical memory in that
node. No paper, idea-story, user-instruction, question, skill, AGENTS, code,
result, or submodule change is hidden.

## Tree And Search-Strategy Audit

The review correctly stops the exhausted AgentProcessBench score family,
retains CodeTraceBench/ToolSafe/AgentNet as typed boundaries, and moves away
from repeated same-target ranking variants. It also opens the right external
communities: multidimensional data analysis, causal systems tracing,
agent-observability products, and direct trajectory localization.

The tree error is only at the final source-selection edge:

```text
AgentTelemetry accepted artifact
  -- supports --> same-claim fault-detection and OTel baseline pressure
  -- does not supply --> official span/step localization gold
  -- therefore cannot currently motivate --> selected RQ2 localization run
```

AgentRx and TELBench are already verified sibling nodes with official
step/span targets. The bounded repair should choose the highest-paper-value
eligible source from evidence already collected, rather than reopen source
search or invent a custom target.

## Current-Gate Must-Fix

Only the following defect blocks REVIEW exit:

1. **Replace or substantiate the selected source.** Revise the root route so
   the one RQ2 experiment uses an official artifact with released span/step or
   first-error gold already verified by this review, or link direct primary
   evidence for an official AgentTelemetry target artifact absent from the
   accepted paper and Zenodo snapshot. Do not accept run-level triage, derive
   handmade labels, or change RQ2.
2. **Propagate that same one-source route into the two live frontiers.** Update
   only the AgentTelemetry selection/next-action passages in
   `docs/evaluation.md` and `docs/background-related-work.md`; preserve all
   completed branch history, exact thesis, four RQs, and meta-review RQ
   boundaries.

This is a bounded routing and memory repair. It does **not** require:

- another whole-paper review or literature search;
- another reviewer, checker, packet, or reproducibility audit;
- a paper, idea-story, skill, AGENTS, code, experiment, or submodule edit;
- a new branch or any Git operation;
- a smaller thesis, claim, contribution, or RQ; or
- human intervention.

## Ranked Deferred Paper-Wide Objections

These remain real but do not invalidate the completed review or the bounded
route repair:

1. **RQ2 positive evidence remains missing.** The current paper's low-work
   headline is coupled to low recall and adaptive configuration; the next
   eligible external localization experiment is still the highest-value
   evidence action.
2. **RQ1 responsibility truth is missing.** Category separation does not prove
   causal or correct cross-layer ownership, and the “over 90%” headline lacks a
   transparent derivation.
3. **Closest-work novelty remains unresolved.** Data Cube, Pivot Tracing,
   Perfetto, pprof, and Datadog Patterns explain much of the stated query and
   hierarchy capability; AgentProf must earn its distinct cross-layer semantic
   responsibility outcome.
4. **RQ3 does not test the actual prompt tagger.** Structured phase/action
   partition agreement cannot authorize natural-language tag accuracy.
5. **RQ4 lacks complete cold/warm cost.** Cached projection/folding timing does
   not measure the full semantic-enrichment path.
6. **AAAI submission reproducibility remains incomplete.** The required
   checklist and prompts/models/hardware/splits are not ready.
7. **The current paper contains unsupported quantitative result surfaces.**
   They remain ambitious positive targets during BUILD_AND_EVALUATE, not
   submission-authorized results.

None of these objections authorizes story shrinkage. Each should be routed to
later evidence or targeted writing in the existing four-RQ program.

## Transition Decision

**Current transition: REVIEW -> REVIEW repair.**

The gate may not yet enter EXPERIMENT because its selected source cannot
provide the required official localization unit. Once the bounded source-route
and canonical-memory repair is complete, the intended transition remains:

```text
REVIEW
  -> one fixed-RQ2 eligible external localization experiment
  -> ordinary Markdown plan
  -> real preflight
  -> complete approved run
  -> result review and outer audit
  -> REVIEW regardless of sign
```

The exact thesis, original AgentProf story, operations and operation stacks,
and four fixed RQs remain unchanged. The repair seeks a source capable of
testing the strong positive RQ2 hypothesis; it does not make that hypothesis
smaller.

**Final outer-audit verdict: REPAIR CURRENT GATE.**
