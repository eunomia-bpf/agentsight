# Cycle 0002 Report — Evidence Boundaries And Fresh RQ2 Route

**Started:** 2026-07-12T20:19:43-07:00  
**Completed:** 2026-07-13T12:15:54-07:00  
**Phase:** BUILD_AND_EVALUATE  
**Status:** COMPLETE  
**Next step:** one fixed-RQ2 HINTBench EXPERIMENT gate  

## Cycle Outcome

Cycle 0002 preserved the original AgentProf scientific contract, completed a
large but procedurally overlong RQ2 evidence branch, restored and verified the
active AAAI paper, ran the user-requested adversarial whole-paper review, and
selected a fresh external experiment after two independent source repairs.

The current paper is **not submission-ready**. Its AAAI-27 verdict is **Reject /
incomplete-but-promising**. The principle and story remain strong; the limiting
factor is missing evidence for the four causal links, especially matched-recall
real-problem localization, not an idea that should be narrowed.

The next action is exactly one experiment on the current official HINTBench
snapshot. It remains within fixed RQ2 and tests whether a target-blind AgentProf
semantic profile reduces atomic-step inspection at 80% macro recall relative
to the strongest same-information non-oracle comparator.

## Fixed Authority

The thesis remains exactly:

> **Agent observability needs profiling, not only debugging.**

The four RQs remain:

1. resource attribution;
2. real-problem localization;
3. tag accuracy; and
4. profiling cost.

The original submodule story remains the authority. The active paper under
`docs/paper/` is the current reader-facing narrative. The submodule itself was
not edited. Negative, invalid, and inconclusive development branches remain in
the audit trail and canonical evidence memory; they did not replace the
positive reader-facing story.

## Gate Reports

### EXPERIMENT

[`01-experiment-gate/999-gate-report-20260713T110626-0700.md`](01-experiment-gate/999-gate-report-20260713T110626-0700.md)

The gate completed five constructions under RQ2:

- CodeTraceBench: valid, mixed/inconclusive;
- ToolSafe: valid, contradicted for the tested construction;
- AgentNet: complete run, invalid intended comparison because the semantic key
  dropped the visible target/local leaf;
- AgentProcessBench mean risk: positive semantic AP interval, unresolved
  work-to-50 interval; and
- AgentProcessBench Wilson-shaped score: positive adaptive AP evidence,
  favorable work point estimates, unresolved work interval.

The same-target AgentProcessBench score branch is closed. No third variant is
allowed. The first outer audit found only stale canonical literature/search
memory; after a bounded archive/rewrite and fresh independent verification,
the gate passed without rerunning an experiment.

### WRITE

[`02-write-gate/999-gate-report-20260713T103942-0700.md`](02-write-gate/999-gate-report-20260713T103942-0700.md)

The active paper retained the exact thesis, original story, operations and
operation stacks, and exactly four RQ-organized Evaluation subsections. The
AAAI-27 artifact compiled within seven content pages plus two reference pages,
with improved structure, source fidelity, terminology, and result-boundary
wording.

The writing work did not make the paper scientifically complete. Its own
audits preserved open objections on attribution truth, matched localization,
actual prompt-tagger accuracy, full cold/warm cost, and closest-work novelty.

### REVIEW

[`03-review-gate/999-gate-report-20260713T121325-0700.md`](03-review-gate/999-gate-report-20260713T121325-0700.md)

The review completed:

- blind full-paper read and attack map;
- separate systems, AI/ML, and bridging source searches;
- primary-source verification;
- post-search whole-paper and all-figure/table reread;
- internal cycle-change and process audit;
- dedicated meta-review;
- independent outer audit;
- bounded fresh localization-source selection;
- independent target-accounting review and repair;
- canonical-memory propagation; and
- fresh outer repair verification.

Its current-paper verdict is Reject / incomplete-but-promising. No story or RQ
change was accepted.

## Generated Scientific Evidence

### CodeTraceBench

The complete real coding-agent run produced positive-looking point estimates,
but paired intervals crossed zero and the outcome-null control was not
rejected. It limits the tested task-held-out differential construction and is
not paper-authorized evidence.

### ToolSafe

The complete released-label run reversed the expected inspection-work and
unsafe-only directions. It contradicts that cross-family construction. This is
a mechanism boundary, not authority to weaken RQ2.

### AgentNet

The full run was mechanically complete, but the semantic key removed `target`
while the raw baseline retained it. The comparison therefore changed visible
information. The durable rule is to preserve the raw local leaf and match
information across baselines.

### AgentProcessBench mean-risk construction

Semantic AP improved by `0.031522` with a positive paired interval and passed a
matched-refinement control. The work-to-50 interval
`[-0.022550, 0.074214]` crossed zero. The construction is valid and
inconclusive for the conjunctive RQ2 hypothesis.

### AgentProcessBench Wilson-shaped construction

Semantic AP improved by `0.024515`; all four family work point estimates were
favorable, but the work interval `[-0.026809, 0.080506]` crossed zero. Because
targets had already informed the branch, this is adaptive supporting evidence,
not fresh confirmation.

### Paper-visible implication

None of these results authorizes replacing the reader-facing RQ2 table with a
complete positive result. They improve mechanism knowledge and select a fresh
experiment. The strong RQ2 hypothesis remains unchanged.

## Whole-Paper Review Findings

The review found four load-bearing evidence gaps:

1. RQ1's category-separation result does not independently validate cross-layer
   resource responsibility, and the “over 90%” headline is not transparently
   derived from the displayed ablation.
2. RQ2's 9.4% inspection headline is coupled to 18.8% median top-five recall;
   operation-stack AP is below two non-oracle baselines, and configuration was
   adapted on the evaluated operations.
3. RQ3 evaluates structured-field remapping and partition agreement, not the
   actual prompt tagger's semantic correctness, coverage, OOS behavior, or
   stability.
4. RQ4's 1.6-second number measures cached projection/folding rather than the
   complete cold semantic-enrichment path.

Closest work also creates substantial novelty pressure. Data Cube, Pivot
Tracing, PerfettoSQL, pprof labels, Datadog Patterns, Langfuse/LangSmith,
aggregate traces, and AgentTelemetry cover important pieces of the stated
mechanism or product capability. The paper must isolate cross-layer semantic
responsibility and a decision outcome, not claim novelty from ordered grouping
or flame-graph rendering alone.

These findings strengthen the experiment program; they do not change the
thesis or make the story smaller.

## Source-Route Evolution

### Rejected first route: AgentTelemetry

Review initially selected AgentTelemetry because it is an accepted,
multi-framework agent fault-detection and OTel benchmark. Independent audit of
the accepted paper and Zenodo source snapshot found no released official
fault-bearing step/span target. Its data supports run/cell fault detection, not
the required RQ2 localization unit. AgentTelemetry remains a same-claim,
taxonomy, fault-detection, and baseline precedent, but not the selected source.

### Why AgentRx and TELBench are not fresh

Cycle 0001 already used all 73 released AgentRx target trajectories and all
1,000 TELBench target cases in FULL scoring. They remain strong protocol and
baseline precedents, but their labels have already informed mechanism
diagnosis and cannot become untouched confirmation again.

### Selected fresh route: HINTBench

The current paper-linked official HINTBench test snapshot contains:

| Property | Verified value |
|---|---:|
| Records | 536 |
| Risky / safe | 400 / 136 |
| Official annotations | 978 |
| Distinct target pairs | 938 |
| Distinct mappable targets | 935 |
| Official targets absent from released trajectories | 3 |

The paper/README describes 629 test records, but the current downloadable file
has 536. FULL is the entire current file. The three absent targets—record 170
step 7, record 233 step 9, and record 516 step 13—remain common terminal misses
for every method. They are never remapped, inferred, or dropped.

Who&When remains an eligible 184-trajectory reserve but is not part of the next
experiment.

## Next Experiment Handoff

### Fixed RQ and hypothesis

Fixed RQ2 asks whether profiler output corresponds to real problems. The one
tested hypothesis is:

> Across the complete current official HINTBench test snapshot, grouping
> target-blind atomic trajectory steps by stable semantic responsibility and
> ranking the resulting groups requires less atomic-step inspection to recover
> at least 80% of official risky-step targets than the strongest comparator
> that sees exactly the same raw steps and non-label fields.

### Primary metric

For each risky trajectory, the target set is the union of official step IDs.
The primary metric is the minimum atomic-step inspection fraction and count
needed to reach at least 80% macro recall across 400 risky trajectories. Support
requires a paired work-reduction interval excluding zero against the strongest
same-information non-oracle comparator while the recall target is met.

### Competing positions

- native sequential inspection: source order is sufficient;
- flat independent-step ranking: the target-blind score creates the benefit;
- flat same-information multidimensional aggregation: ordinary grouping over
  every field visible to AgentProf captures the benefit.

The experiment plan admits the smallest strong baseline set covering these
positions. They are comparisons inside one experiment, not separate research
programs.

### REAL PREFLIGHT and FULL

REAL PREFLIGHT must contact the current official source, real AgentProf path,
every admitted method, and scorer; reproduce all population/target counts; and
use released `trajectory[].step_id` rather than array position. If source facts
differ, return to REVIEW rather than inventing a label.

FULL covers every `(536 current records, approved method, planned repetition)`
cell to terminal status. Smoke runs and successful prefixes are not results.
Whatever the sign, result review and outer audit close the experiment and
return to REVIEW.

### Exclusions

The next gate does not add AgentTelemetry run triage, a third AgentProcessBench
score, reused AgentRx/TELBench confirmation, Who&When, handmade labels, RQ3,
RQ4, idea refinement, a full writing loop, or Git/hash/seal/packet control
machinery.

## Paper And Story Changes

The WRITE gate made source-fidelity, structure, terminology, result-boundary,
and formatting changes recorded in its `999` report. The REVIEW gate made no
paper edit. The exact thesis and fixed-RQ organization remain visible.

No cycle 0002 result authorized a new story, and no negative development branch
entered the reader-facing positive narrative. `docs/idea-story.md` retains its
Initial Narrative and E000--E008; no E009 was added.

## Canonical Memory And Housekeeping

- `docs/evaluation.md` is a 202-line current frontier with the HINTBench route,
  target-accounting rule, matched-recall decision, and prior evidence
  boundaries.
- `docs/background-related-work.md` is a 191-line current novelty/source
  frontier. It keeps AgentTelemetry as precedent and HINTBench as the selected
  localization source.
- The pre-repair literature frontier remains archived in this cycle directory.
- `docs/questions-for-author.md` contains no open question.
- `scripts/check_progress.py` is absent; no output was invented, and the
  absence did not block research.
- No skill, AGENTS file, plugin, KVM workflow, or new checker was created or
  modified.

## Scientific-Contract Integrity

No gate changed:

- the exact thesis;
- the original problem and motivation;
- operations or operation stacks;
- the four RQs;
- the positive RQ2 hypothesis; or
- the broad quality, safety, cost, failure, and wasted-work stakes.

Experiment outcomes changed mechanisms, source choice, target accounting, and
search strategy. They did not become authority to shrink the claim.

## Process Deviations And Repeated Agent Failures

Cycle 0002 exposed six repeated process failures:

1. five experiments ran under one EXPERIMENT gate instead of returning to
   paper-level review after one result;
2. idea refinement and a full writing loop ran during BUILD_AND_EVALUATE;
3. WRITE entered before the EXPERIMENT outer audit and `999` closeout;
4. historical writing/review nodes ran Git checks and recorded per-node hashes
   despite the user prohibition;
5. chronology and reviewer freshness were overstated in some reports; and
6. repeated control/provenance prose consumed effort without improving the
   scientific discriminator.

The existing rules already prohibit these failures. The response is to apply
the simpler loop next step, not add or modify a skill, AGENTS rule, machine-
readable contract, checker, freeze protocol, or integrity artifact.

## Meta-Review And Root Routing

### Direction

No drift. Preserve the exact thesis, original story, two core abstractions, and
four RQs. The paper is evidence-incomplete, not idea-invalid.

### Efficiency

Run one HINTBench experiment, close its EXPERIMENT gate whatever the sign, and
return to REVIEW. Any subsequent WRITE is targeted and evidence-driven; do not
run idea refinement or full writing in BUILD_AND_EVALUATE.

### Maintenance

Canonical frontiers are current; no open human question exists; no new
capability is justified. The absent progress diagnostic is non-blocking.

## Ranked Deferred Objections

1. RQ2 still lacks a positive external matched-recall result.
2. RQ1 lacks independent responsibility truth and a transparent headline
   derivation.
3. Novelty over standard aggregation and current semantic observability tools
   remains unresolved.
4. RQ3 does not evaluate the actual prompt tagger.
5. RQ4 lacks full cold/warm end-to-end cost.
6. AAAI reproducibility material and checklist remain incomplete.
7. Current quantitative paper surfaces are not yet submission-authorized.

These are later-step obligations, not reasons to block the current handoff or
change the story.

## Final Cycle Decision

Cycle 0002 is complete. The next outer step is:

```text
fixed RQ2
-> one HINTBench experiment
-> one ordinary Markdown plan with 3--5 serial scientific reviews
-> REAL PREFLIGHT on the current official source and real AgentProf path
-> complete FULL run across every approved 536-record cell
-> result review
-> independent outer audit
-> REVIEW whatever the sign
```

No human wait, branch change, second experiment, paper edit, story rewrite, or
skill modification is authorized by this transition.
