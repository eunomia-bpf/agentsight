# Review 001 / Node 400 — Cycle Audit, Final Verdict, and Routing

**Started:** 2026-07-13 16:25:18 PDT
**Original scientific disposition completed:** 2026-07-13 16:28:26 PDT
**Lifecycle/provenance recovery addendum recorded:** 2026-07-13 16:57:50 PDT
**Parent:** [`300-full-paper-reread-and-scientific-assessment.md`](300-full-paper-reread-and-scientific-assessment.md)
**Node status:** complete pending independent outer audit
**Paper edit authority:** none

## Objective

Audit Cycle 0003 for user-intent, thesis, RQ, mechanism, experiment, and process
drift; compare two independent complete-paper reviews; settle the
TraceElephant-versus-Who&When source disagreement; issue one source-grounded
AAAI verdict; and select exactly one next experiment without modifying the
paper, submodule, or skills.

## Transparent recovery addendum

The scientific review, reviewer convergence, AAAI verdict, and TraceElephant
route were completed at 16:28:26. The repository initially omitted Markdown
copies of the two independent reviewer outputs, the mandatory experiment-level
outer audit, the BUILD_AND_EVALUATE scientific-contract-unchanged skip, and the
dedicated meta-review. A later strict audit found those lifecycle/provenance
defects.

The root subsequently added honestly timestamped recovery records and updated
the links and process wording in this file. Those later reports did not exist at
16:28:26 and are not presented as original Node 400 inputs. They verify and
document the already-issued scientific disposition; they do not retroactively
change its completion time, rerun HINTBench, or alter the next experiment.

The current file therefore has two temporal layers:

1. the original 16:28:26 scientific assessment and route; and
2. this 16:57:50 lifecycle/provenance addendum linking the later recovery
   artifacts required before the REVIEW gate can close.

## Inputs and provenance

This final review node synthesizes:

- [`100-blind-full-paper-read-and-attack-map.md`](100-blind-full-paper-read-and-attack-map.md);
- [`200-external-search-and-source-verification.md`](200-external-search-and-source-verification.md);
- [`300-full-paper-reread-and-scientific-assessment.md`](300-full-paper-reread-and-scientific-assessment.md);
- [`350-independent-reviewer-a-cross-domain-and-source-route.md`](350-independent-reviewer-a-cross-domain-and-source-route.md);
- [`360-independent-reviewer-b-authoritative-paper-review.md`](360-independent-reviewer-b-authoritative-paper-review.md);
- the complete Cycle 0003 HINTBench plan, preflight, full result, raw result
  summaries, and two independent exact result audits;
- two fresh cross-domain reviewers whose final dispositions are now preserved
  in linked detailed Markdown reports and that explicitly used the
  `iter-review-critique` skill and its systems/AI/cross-domain taste references;
- a targeted source-comparison follow-up after one reviewer initially omitted
  TraceElephant;
- root-level inspection of the AgentProf binary invocation, exact-flat control,
  implementation facts, active/submodule paper diff, PDF page boundary, and
  official AAAI-27 rules.

The reviewers did not edit files or use Git. The root writes this Markdown
disposition; no reviewer verdict is treated as scientific authority by itself.

## Independent-review convergence

### Reviewer A

Reviewer A classified the paper as cross-domain, gave a current AAAI verdict of
Reject / major experimental revision, preserved the exact thesis and four RQs,
and selected RQ2 as the highest-value evidence need. Its first route chose
Who&When. A bounded follow-up supplied the primary TraceElephant paper,
artifact, population, fields, and methods and asked for a direct comparison.
The reviewer then explicitly withdrew Who&When and selected TraceElephant.

Its reason was scientific rather than chronological: Who&When's output-side
logs cannot test a stack that depends on intent, tool/environment response, and
outcome status, whereas TraceElephant exposes those fields over a larger,
fresher, broader real-execution population.

### Reviewer B

Reviewer B independently read the paper and primary sources, gave the same
Reject / major experimental revision verdict, selected the same fixed RQ2, and
independently selected TraceElephant over Who&When. It emphasized full
observability, responsible-component plus decisive-step targets, three agent
systems, and the need to test information-equivalent flat and run-local
alternatives.

### Converged findings

Both independent reviewers agree that:

1. the original thesis is large, simple, principled, and worth preserving;
2. no story, contribution, or RQ replacement is authorized;
3. current RQ2 reader-facing ranking is target-informed and cannot support the
   headline localization claim;
4. current RQ1 separation is not independent responsibility truth;
5. current RQ3 does not test the claimed natural-language taggers;
6. current RQ4 does not measure complete cold/warm end-to-end cost;
7. HINTBench is a valid mechanism boundary, not positive paper evidence and
   not a thesis challenge;
8. the next gate must be one experiment, fixed RQ2, complete TraceElephant;
9. Who&When remains closest work and partial-observability context; and
10. paper, submodule, and skills must remain unchanged during this route.

## Root disposition on reviewer overreach

Two Reviewer B statements are not accepted as written.

### HINTBench used the real AgentProf artifact

The HINTBench adapter did not replace AgentProf. It invoked the reviewed release
binary `agentpprof/target/release/agentpprof` for every candidate profile,
verified conservation, and retained raw profiles. Custom Python was thin
source adaptation, local-model inference, baseline construction, scoring,
bootstrap, and reporting glue required by the official HINTBench schema.

The experiment can still be criticized as a hybrid diagnosis protocol rather
than a complete paper answer, but not as a fake AgentProf implementation.

### Exact flat reconstruction was an identity control

The plan explicitly declared that a relational reconstruction of the same
ordered prefix projection must match AgentProf exactly. It was not a baseline
AgentProf was supposed to outperform. Its exact tie proves algebraic execution
correctness and exposes the expressivity boundary honestly.

This control does sharpen the novelty burden: operation stacks cannot claim
that SQL or flat relational code is unable to reproduce an equivalent
projection. The paper contribution must instead be the agent-specific
responsibility model, its standard profiling representation, cross-layer
field semantics, and resulting decision value. The correct control result does
not invalidate the HINTBench execution.

## Cycle 0003 scientific audit

### Fixed scientific contract

The entire cycle retained:

> **Agent observability needs profiling, not only debugging.**

and exactly:

1. resource attribution;
2. real-problem localization;
3. tag accuracy; and
4. profiling cost.

The HINTBench experiment tested one hypothesis inside RQ2. It never claimed to
answer the entire RQ.

### Completed scope

- 80/80 official validation trajectories;
- 536/536 official test trajectories;
- 3,050 validation and 12,877 test steps;
- 616/616 terminal local-model requests;
- all 24 validation field orders;
- real AgentProf profiles plus native, independent-step, per-session, and
  raw-action baselines;
- exact flat and width controls;
- 10,000/10,000 paired complete-trajectory bootstrap replicates;
- two independent result reconstructions.

### Scientific result

AgentProf reached 80% macro recall at `41.5702%` inspection work. Raw action
reached the same recall at `46.2918%`, but the paired AgentProf-minus-raw-action
interval was `[-0.293709, +0.008566]`. The strict predeclared positive
criterion required an upper endpoint below zero against every main baseline.
It therefore returned **INCONCLUSIVE**.

This is the correct verdict. Reusing HINTBench test to adjust fields, prompts,
scores, thresholds, or metrics is prohibited. The result remains in experiment
history and mechanism memory, not the reader-facing positive story.

### Story and authority audit

| Check | Result |
|---|---|
| User-selected attachment equals submodule paper after newline normalization | pass |
| Active paper scientific body equals submodule authority | pass |
| Exact thesis retained | pass |
| Exactly four RQs retained | pass |
| Abstract/introduction/background/design replaced | no |
| Contribution narrowed | no |
| HINTBench mixed result inserted into paper | no |
| Submodule modified | no |
| Cycle 0003 skill edits | no; the shared skills repo acquired separately staged concurrent changes outside this cycle and is not modified or reverted here |

### Process findings

The experiment itself completed one RQ, one hypothesis, one source, one plan,
one real preflight, one full run, and one result review sequence. Five serial
plan reviews were justified by material source, baseline, metric, and transport
defects; no further review is needed for that closed experiment.

Cycle 0003 originally transitioned directly from EXPERIMENT to REVIEW without
the mandatory independent EXPERIMENT outer audit or no-change WRITE gate. The
scientific action was correctly “do not edit,” but the lifecycle record was
wrong. The root preserved that original record and added an honestly late
[`independent EXPERIMENT audit`](../../01-experiment-gate/990-independent-outer-audit-recovery-20260713T165103-0700.md)
plus the actual-time
[`WRITE recovery entry`](../../02-write-gate/000-recovery-entry-20260713T162826-0700.md),
skip node, and gate report. The recovery does not fabricate chronology or claim
that a writing skill ran before REVIEW.

### Capability-learning audit

No new skill, project rule, or AGENTS change is justified. Existing skills
already require:

- one experiment and one fixed RQ;
- complete official populations;
- target-blind evidence construction;
- real preflight followed by full run;
- no thesis/RQ shrinkage;
- report-only REVIEW; and
- independent transition audit.

The observed defect is an orchestration application error, not a missing
capability. Record it in this cycle and execute the existing WRITE-skip rule.

## Final scientific verdict

**AAAI-27 Main Track today: Reject / major experimental revision.**

The paper is page-compliant and has a top-venue-level problem and principle.
It is not submission-ready because its reader-facing RQ2 uses target-informed
ranking, its RQ1 construct does not independently validate responsibility, its
RQ3 proxy does not test the claimed taggers, and its RQ4 excludes complete
cold-path cost. These are evidence obligations, not permission to make the
paper smaller.

The largest claim worth defending remains:

> AgentProf turns heterogeneous agent executions into population profiles that
> correctly attribute additive costs and effects to recurring semantic
> responsibility and concentrate real problems in substantially less analyst
> inspection work.

## Exactly one next experiment

### Identity

**Name:** TraceElephant target-blind cross-run problem localization
**Fixed RQ:** **RQ2: Does Profiler Output Correspond to Real Problems?**
**Experiment count:** one
**Test population:** all 220 official annotated TraceElephant failures

### One tested hypothesis

> On the complete official TraceElephant failure population, one fixed
> target-blind AgentProf semantic profile that combines component role,
> preceding intent/subgoal, action or tool, observed environment response, and
> outcome status reaches at least 80% macro recall of official decisive failure
> steps with less atomic-step inspection work than every main same-information
> non-oracle profiling baseline.

This is one consequence of RQ2, not a replacement definition of RQ2.

### Why TraceElephant

- 220 failures from 380 real executions rather than synthetic risk stories;
- Captain-Agent, Magentic-One, and SWE-Agent;
- GAIA, AssistantBench, and SWE-Bench;
- full inputs, outputs, inter-agent messages, tools, environment logs,
  configuration, and architecture metadata;
- independent responsible-component and decisive-step annotations;
- official static and dynamic diagnosis protocols;
- fresh external population not previously used to choose an AgentProf test
  policy; and
- enough cross-run context to test the mechanism beyond raw action.

Who&When remains a valuable output-only/partial-observability closest-work
source. It is not chosen because its visible fields cannot support the richer
intent/response/status mechanism and risk another action-dominated experiment.

### Source and holdout policy

- Treat all 220 TraceElephant failures as one fresh external **test-only**
  population unless a plan review proves that a learned component is essential.
- Do not manufacture a random train/test split merely to tune on the new
  benchmark.
- Inspect source schema and unlabeled fields during source preflight, but do
  not load `mistake_agent`, `mistake_step`, explanations, or equivalent target
  fields into representation, tag, rank, threshold, fallback, or model
  selection.
- Fix any learned behavior on non-TraceElephant development evidence. If a
  learned component cannot be defined without TraceElephant labels, reject that
  component rather than consume the fresh holdout.
- Score every trace once under the approved fixed policy.

### Mechanism to send to PROPOSE

Use the real AgentProf binary to profile operations derived from visible
TraceElephant fields. The candidate stack is intentionally simple:

```text
system-or-scaffold
-> component-role
-> intent-or-subgoal
-> action-or-tool
-> observed-response-or-status
```

The plan must define causal propagation conservatively from an input-side
intent to its downstream response/tool operations. It must define one
target-blind group score before scoring labels. It may use the official static
full-trace prompt as a common signal source, but the same signal and information
budget must feed all matched aggregation baselines.

The plan review may simplify fields or scoring if official schema inspection
shows one field is not source-stable. It may not change RQ2, the positive
hypothesis, the complete population, or the matched-recall metric.

### Baseline families

The smallest defensible main set is:

1. native component/execution hierarchy;
2. independent-step target-blind ranking;
3. per-trajectory/session grouping;
4. raw action/tool grouping, mandatory;
5. flat same-information aggregation;
6. the fixed AgentProf semantic operation stack; and
7. exact relational reconstruction of the AgentProf projection as an identity
   control, not a superiority baseline.

Official full-trace diagnosis comparisons are required when runnable with
matched information:

- All-at-Once;
- Static Agentic if the official executable path is actually released;
- Step-by-Step and Binary Search as source-native search controls when their
  output can be mapped to the inspection metric.

Dynamic Agentic receives replay/intervention information that offline
AgentProf does not. It is an upper-bound/context row, not a main baseline
AgentProf must beat. AgentRx may be included only if its official method adapts
without becoming a second custom research program. Unreleased methods are
reported as unavailable, not weakly reimplemented.

### Primary metric and complete-run rule

- **Primary outcome:** minimum atomic-step count and fraction required to reach
  at least 80% macro recall of official decisive failure steps.
- Equal-score tiers remain indivisible.
- Report paired trajectory-level 95% bootstrap intervals, stratified by the
  five official system-task cells.
- Secondary outcomes: responsible-component accuracy, exact and declared
  tolerant decisive-step accuracy, AP, recall-at-k, group count, and
  fragmentation.
- FULL means all 220 traces, every admitted baseline/control, every declared
  model request, and every bootstrap replicate reach terminal status.
- Preflight proves real parser, model, AgentProf, baseline, and scorer
  engagement but is not paper evidence.

### Positive decision rule

The experiment is positive only if:

1. the complete run is valid and target-blind;
2. AgentProf reaches at least 80% macro recall;
3. the upper 95% endpoint of AgentProf-minus-baseline inspection work is below
   zero against every declared main non-oracle profiling baseline; and
4. conservation and exact reconstruction controls pass.

Official per-run diagnosis methods are reported on aligned metrics and used as
strong external context. Whether they are a main work-reduction gate baseline
depends on whether their released outputs define a complete inspection order;
the experiment plan must settle that before FULL.

Whatever the sign, the experiment closes after one complete result and returns
through WRITE (possibly a no-change skip) to whole-paper REVIEW. It does not
start a second source or alter the paper hypothesis.

## Alternatives and decision

- **Who&When:** rejected as the sole next source after direct primary-source
  comparison; retains related-work value.
- **RQ1 next:** central but lacks an equally mature external responsibility
  oracle and could drift into a custom microbenchmark.
- **RQ3 next:** necessary but does not yet decide whether a profile improves a
  real analyst outcome.
- **RQ4 next:** feasible but not the current scientific-validity blocker.
- **WRITE next:** rejected as the substantive route; prose cannot repair
  target-informed evidence. Only the missing formal no-change WRITE node is
  recovered before closing this cycle.

## Search/tree updates

- mark HINTBench closed to retuning and retain it as `mechanism boundary`;
- supersede Who&When as the next test source, retaining it as closest work;
- open TraceElephant as one test-only RQ2 branch;
- require full-context source-native fields and a mandatory raw-action
  comparator;
- keep RQ1 responsibility truth, RQ3 actual tagger validity, and RQ4 cold/warm
  cost as later sibling blockers.

## Project-memory updates requested from the root

After independent outer audit, update current-frontier pointers in:

- `docs/evaluation.md`;
- `docs/design.md`;
- `docs/implementation.md`;
- `docs/idea-story.md`; and
- `docs/background-related-work.md` only if its pre-existing user change can be
  preserved without overlap.

These updates must record HINTBench as complete/inconclusive, TraceElephant as
the selected next source, and the exact unchanged thesis/RQs. They must not
rewrite the Initial Narrative or paper story.

## Completion assessment and next node

The complete-paper review is scientifically complete and converged on one
route. Before transition, a fresh outer auditor must check these four reports,
the actual HINTBench evidence, the user instruction, the exact paper authority,
and the proposed TraceElephant source. REVIEW itself performs no Git operation.
