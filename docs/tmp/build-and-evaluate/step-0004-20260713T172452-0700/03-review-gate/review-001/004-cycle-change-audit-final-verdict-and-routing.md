# Cycle-Change Audit, Final Verdict, and Routing

## Node record

- **Completed:** 2026-07-14T02:04:20-07:00
- **Parent reports:** `001-blind-full-paper-read-and-attack-map.md`, `002-external-search-and-source-verification.md`, and `003-full-paper-reread-and-scientific-assessment.md`
- **Objective:** audit Step 0004 against author intent, issue the whole-paper verdict, and select exactly one next experiment.
- **Reviewer:** independent `iter-review-critique` subagent; root materialized reports 003/004 from its completed assessment after the agent was instructed to stop further expansion.

## Final verdict

**Reject in current form — promising but scientifically incomplete.**

This verdict does not challenge the thesis or fixed RQs. RQ2 is now supported, but the active paper is globally inconsistent with that evidence; RQ1 remains mechanism evidence, RQ3's current proxy is construct-invalid as tag accuracy, and RQ4 lacks a natural scaling/cold-warm experiment.

Gate routing:

```text
REVIEW
-> minimal factual WRITE correction
-> independent correction audit
-> close Step 0004
-> Step 0005 EXPERIMENT: RQ4 cost and scaling
```

## Cycle-change audit

### Changes that advanced the paper

- Completed a real full-population TraceElephant experiment over 220/220 failures and 5,960 steps.
- Independently recomputed all headline tiers, permutations, and bootstrap results.
- Performed the missing cumulative RQ2 synthesis rather than selecting another score or benchmark.
- Replaced the stale RQ2 subsection with three complete public workloads and verified primary citations.
- Corrected the HINTBench development-selection/test-holdout boundary after an independent WRITE audit caught the overstatement.
- Preserved the exact thesis, four RQs, canonical story, and read-only paper submodule.

### Repeated errors caught in this cycle

- A local tested hypothesis was initially treated as if it controlled the whole RQ; cumulative paper-level evidence corrected that interpretation.
- Target-isolation language was initially too absolute; HINTBench development selection had to be stated explicitly.
- Replacing one evaluation subsection without synchronizing introduction/setup/conclusion created cross-paper stale claims.
- Historical RQ3 numbers survived despite a construct mismatch and arithmetic inconsistency.

These findings should inform normal execution judgment. They do not justify adding a new gate, manifest, frozen packet, or complex state-machine rule.

## Required minimal WRITE disposition

Before Step 0005, update only factual result/status locations:

1. replace old RQ2 headline numbers in Introduction/contributions/Conclusion with the current three-workload positive answer;
2. update the public-data setup to include the current RQ2 workloads and explain HINT's 536-test/629-total split;
3. detach the historical six-task induction result from current RQ2;
4. remove the invalid current RQ3 7/9 completion claim and figure/result prose, while retaining the full positive RQ3 question and noting it as the next required independent tag-accuracy evidence after RQ4;
5. calibrate only the directly false categorical status-quo statements that conflict with official products/pprof; preserve the large profiling thesis and defer the full related-work rewrite to its owning writing/literature pass.

No abstract/intro problem reformulation, contribution narrowing, new RQ, or system-design change is authorized.

## Exactly one next experiment

### RQ and tested hypothesis

**RQ4 — What Is the Profiling Cost?**

Tested hypothesis:

> Complete AgentProf profile construction has practical and predictable scaling on complete real public workloads, and cached field derivation makes a repeated semantic profile materially faster than the corresponding first construction.

The experiment tests this hypothesis only. It does not change RQ4 or add a new paper claim.

### Reused assets

- existing R327 cost runner and its 76 profile specifications;
- the four complete existing public-workload inputs used by R327 and their union;
- R328 deterministic-output checks;
- R160 fixed eight-session real Codex input, tag cache, and llama.cpp path;
- current release `agentpprof` binary;
- existing timing/report parsing code.

### Complete but lean matrix

Public path:

- four complete public workloads plus their complete union: five natural input sizes;
- one fixed semantic profile and one information-matched raw-action profile per size;
- three complete repetitions per cell;
- total: 5 sizes x 2 profiles x 3 repetitions = 30 profiler invocations.

Tag-cache path:

- R160's fixed eight-session input;
- three paired clean-cache and warm-cache runs;
- total: 6 invocations.

Do not rerun all 76 specifications, add another benchmark, build a new harness, or add bootstrap/permutation machinery. Run every declared cell to completion.

### Metrics and baselines

- **Primary metric:** end-to-end wall-clock time across operation count, with milliseconds per operation and the paired warm/cold time ratio.
- **Necessary descriptive metrics:** peak RSS, operations/second, output bytes, tag calls, and cache hits.
- **Baselines:** information-matched raw-action profile on the same public input; clean-cache construction versus warm-cache repeat query on the same fixed real input.
- **Interpretation:** report the complete scale curve, per-operation rate, and paired warm/cold speedup. Do not invent a pass threshold after seeing results; decide whether the curve supports practical predictable scaling from the complete observed effect and uncertainty across the three repetitions.

### Why this experiment is next

RQ4 maximizes paper value per new mechanism. All important assets already exist. RQ3 currently requires new construct-valid semantic labels, and RQ1 requires an independent responsibility oracle. Forcing either now would violate the user's reuse/simplicity instruction or produce another proxy. RQ4 can provide a complete fixed-RQ answer without a new model, ontology, benchmark, or experimental framework.

## Capability and memory decisions

- No new repository skill is necessary for this step; the cost runner is an existing repeatable workflow.
- No change to shared auto-research skills is authorized in this project turn.
- Record the user's reuse/simplicity instruction in `docs/user-instruction.md` (completed).
- Preserve all experiment/review history in timestamped Markdown; the paper remains the current reader-facing state.

## Completion assessment

The four required REVIEW reports now exist. The review inner loop is complete. The REVIEW gate remains open only for the minimal factual WRITE correction and its independent audit; after that, Step 0004 can close and Step 0005 can begin the declared RQ4 experiment.
