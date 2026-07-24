# Blind Full-Paper Read and Attack Map

**Timestamp:** 2026-07-23T23:16:24-07:00
**Parent:** Step 0076 REVIEW gate, milestone review 001
**Objective:** Form a paper-only judgment before using current-cycle reports or
author explanations.

## Inputs and provenance

I read `docs/paper/main.tex` from title through bibliography invocation,
inspected the built 12-page `main.pdf`, and opened all five claim-bearing
flamegraph panels. I did not read Step 0072, 0075, or 0076 reports before
forming the attack map.

Unavoidable contamination is limited but real: this reviewer had previously
reviewed an earlier Step 0073 state and therefore knew that the project had an
automatic-annotation generalization concern. I did not use that prior result
to assign a current-paper finding until after the blind read.

## Venue and domain routing

- **Target:** AAAI 2027 Main Technical Track.
- **Contribution class:** genuinely cross-domain. The paper makes an AI claim
  about automatically recovering semantic agent-operation structure and a
  systems claim about conserved, source-linked, pprof-compatible profiling.
- **Review bars loaded:** research taste, systems, AI/ML, and cross-domain.
- **Ambiguity:** the artifact resembles a systems paper, but the stated target
  and the automatic semantic backend make AI soundness load-bearing. Neither
  community's bar can be substituted for the other.

## Paper-only reconstruction

### Problem and challenged belief

The paper argues that per-run traces do not answer population questions about
where agent failures, unsafe effects, or resource consumption recur. It
challenges the implicit belief that native execution nesting or raw action
identity is already the right responsibility hierarchy for profiling agents.

### Simple principle

> Treat trajectories as weighted profiling samples, assign recurring semantic
> responsibility over their native evidence, and fold equal responsibility
> paths across runs.

This principle is simple, important, and potentially durable. It is stronger
than the implementation detail that the output happens to be pprof.

### Mechanism and causal chain

```text
source trace tree
-> recursive semantic interval annotations
-> operation stacks with retained LLM/tool leaves
-> additive folding under count/token/time/effect measures
-> population-level attribution and diagnosis
```

The first four edges are specified clearly. The final edge—from a valid
profile to a better user decision—is the least completely established.

### Claimed contributions

1. A semantic operation-stack model.
2. AgentProf, a backend-neutral annotation workspace and pprof compiler.
3. Evidence that automatic structure agrees with annotations, profiles
   correspond to real problems, multi-resource views reveal bottlenecks, and
   fixed-mark construction is practical.

### Explicit RQs

| RQ | Paper question | Paper's stated answer |
|---|---|---|
| RQ1 | Does semantic profiling improve resource attribution? | One repeated real Git task folds an SSH-diagnosis responsibility across runs; it is 21.47% of operations but 46.15% of tokens. |
| RQ2 | Does profiler output correspond to real problems? | Direct+AgentProf improves MAP over Direct-only on three workloads, but is statistically indistinguishable from Direct+Raw+Evidence; a population case links recovery exposure to expert looping labels. |
| RQ3 | How accurately do automatic backends recover operation structure? | A2 reaches B³ F1 .704 and boundary F1 .394 on CodeTrace; other task/action/group backends have positive standard-metric results. |
| RQ4 | What is the cost of constructing a semantic profile? | Fixed-mark profile construction is 1.16–1.17 s; source-packet reconstruction is 501.64 s and deterministic postprocessing is 3.54 s; Agent inference is unmeasured. |

## Initial strengths

1. **Important problem.** Population-level agent behavior analysis is a real
   operational need, not a benchmark-only construction.
2. **Memorable thesis.** “Agent observability needs profiling, not only
   debugging” is a strong paper center.
3. **Coherent systems invariant.** Additive mass conservation and retained
   source evidence make the representation auditable.
4. **Real workloads.** The paper uses real long-horizon coding sessions,
   mixed-outcome web trajectories, and complete public benchmark populations.
5. **Honest local qualifications.** RQ1 calls its control post-hoc; RQ2
   discloses matched-raw parity; RQ4 states that 1.17 s is not annotation
   latency.
6. **Useful visual artifact.** The Git and AgentReward profiles visually show
   variable-depth responsibility with source-call leaves rather than a flat
   taxonomy alone.

## Ranked blind attack map

### A1 — The semantic hierarchy has not yet shown an information-matched
downstream advantage

**Severity:** blocker candidate; evidence/evaluation.

The strongest RQ2 control reaches `.893/.518/.324`, versus
`.894/.517/.326` for Direct+AgentProf, with all candidate-minus-control
intervals including zero. The paper therefore demonstrates that adding grouped
source evidence helps Direct-only, but not that the semantic-operation prefix
causes the improvement.

The abstract, introduction, contribution list, and conclusion nevertheless
foreground improvements “over raw action.” A skeptical reader can reasonably
infer a semantic-prefix win that the strongest comparison does not establish.

### A2 — RQ1 is a valid case demonstration, not yet a general attribution
answer

**Severity:** major; evidence/evaluation.

All three views conserve the same mass, and the semantic view directly names a
selected cross-run responsibility. However, the task family and responsibility
were selected from the earlier semantic result. The control proves an
organization difference, not independent discovery, user benefit, or
population-wide attribution improvement.

### A3 — RQ3 combines heterogeneous constructs and development evidence

**Severity:** major; AI/ML evidence.

CodeTrace stages, OSWorld same-observation action groups, task-family labels,
action labels, partitions, and adjacent boundaries are distinct constructs.
The paper is commendably explicit about their metrics, but their aggregate
does not by itself validate one general recursive semantic-responsibility
backend. The default A2 result is on a declared development population, and
the paper reports one output rather than annotation stability across repeated
automatic runs.

### A4 — RQ4 excludes the dominant automatic component

**Severity:** major; systems/AI cross-layer evidence.

The deterministic numbers are credible, but the default backend's inference
time, model calls, prompt/completion tokens, failure rate, and repeated-run
variation are unavailable. A 54.36-minute filesystem envelope cannot answer
automatic annotation cost. The result supports cheap replay after marks, not
end-to-end automatic profiling practicality.

### A5 — Novelty depends on an unverified combination

**Severity:** blocker candidate; novelty.

The paper itself acknowledges products with hierarchical grouping and metric
rollups, academic work with canonical actions and shared cross-run graphs, and
standards with profile/trace linkage. Its remaining novelty is the combination
of recursive within-trace responsibility intervals, arbitrary additive
conservation, source evidence, backend-neutral replay, and pprof output. That
combination may be substantive, but the paper needs a direct closest-work
comparison rather than a list of individually missing features.

### A6 — The current PDF is not an AAAI-length submission

**Severity:** formal blocker.

The built PDF has 12 pages; references begin on page 11. This is visibly much
longer than a standard AAAI main-track submission and cannot be treated as
submission-ready without a major compression pass.

## Load-bearing claims requiring external verification

- Whether products already create nested cross-trace behavior categories,
  aggregate cost/error/latency, and retain drilldown.
- Whether prior research already builds hierarchical action taxonomies or
  subtask intervals and calls the result a behavior profile.
- Whether prior work measures review effort, localization, or recovery from
  cross-run structure.
- What CodeTrace “stages,” OSWorld-Human “groups,” and the three RQ2 benchmark
  targets officially mean.
- Whether MAP is an official benchmark protocol or a new repurposed task.
- Whether pprof/OTel already supply labels, pseudo-frames, and trace linkage.
- AAAI-27 page and review requirements.

## Research-taste judgment before search

- **Principle:** coherent and simple.
- **Belief challenge:** plausible, but external evidence must show it is not a
  strawman.
- **Strongest alternative explanation:** canonical grouping plus retained
  source evidence is sufficient; recursive semantic ancestry is primarily a
  presentation choice.
- **Largest claim worth defending:** semantic responsibility stacks make
  population attribution directly inspectable while conserving and retaining
  the same source evidence.
- **Classification:** incomplete-but-promising, not complicated-but-shallow.
  The central idea is good; the evidence has not yet closed every causal edge.

## Initial paper-only verdict

**Scientific verdict:** **WEAK REJECT.**
**Current AAAI submission status:** **REJECT / noncompliant until reformatted.**

## Completion assessment and next node

The blind phase is complete. The next node is targeted primary-source search
against the attack map, followed by a complete paper reread.
