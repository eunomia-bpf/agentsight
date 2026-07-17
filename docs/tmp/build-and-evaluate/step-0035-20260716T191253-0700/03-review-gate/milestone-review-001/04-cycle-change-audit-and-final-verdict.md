# REVIEW 4/4 — Cycle-Change Audit and Final Verdict

**Started:** 2026-07-17T04:03:00-07:00
**Completed:** 2026-07-17T04:09:52-07:00
**Parent:** Step 0035, `REVIEW_GATE / milestone-review-001`
**Skills:** `auto-research-orchestrator`, `iter-review-critique`
**Target venue:** AAAI 2027 Main Technical Track
**Paper artifact:** `docs/paper/main.tex` and compiled `docs/paper/main.pdf`
**Read-only story authority:** `docs/agentpprof-paper` at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`

## Purpose

This final REVIEW node audits what changed during Step 0035, distinguishes
accepted evidence from reviewer proposals, checks the changes against the
complete user-instruction and idea-story records, and selects the next outer
gate. It does not edit the paper, the shared skills, or the canonical paper
submodule.

The audit answers five questions:

1. Did Step 0035 preserve the authorized paper story?
2. Which new claims are actually supported?
3. Did any local result silently narrow or replace a fixed RQ or hypothesis?
4. Which reviewer findings require experiment rather than writing?
5. Which single experiment has the highest probability of changing the
   paper-level verdict while reusing complete artifacts?

## Inputs Read in Full

The root audit used:

- the complete `docs/user-instruction.md`;
- the complete `docs/idea-story.md`, including the permanent Initial Narrative,
  Current Frontier, all evolution entries, and future-story invariants;
- the complete current paper and compiled nine-page PDF;
- all Step 0035 EXPERIMENT and WRITE reports;
- REVIEW 1/4, the blind full-paper review;
- REVIEW 2/4, the external-search and source-verification report; and
- REVIEW 3/4, the source-grounded full-paper reread.

The audit also rechecked the active branch and the canonical submodule commit.
No branch was created or switched. Git state was not used as a scientific gate.

## Fixed Human Intent

The following constraints remain controlling:

- The exact thesis is **“Agent observability needs profiling, not only
  debugging.”**
- The paper retains exactly four RQs, in order: resource attribution, real-
  problem localization, tag accuracy, and profiling cost.
- The original submodule story is the read-only authority for the problem,
  motivation, two-abstraction model, contribution chain, and RQ meanings.
- A local failed or bounded experiment does not authorize narrowing the paper,
  replacing its hypothesis, or turning negative development evidence into the
  main story.
- Research should keep the largest faithful and interesting claim, then seek
  stronger evidence with real systems, public benchmarks, complete runs, and
  standard metrics.
- Existing complete trajectories and predictions should be reused whenever
  they can answer the RQ; a new model, benchmark, harness, or algorithm is not
  justified by default.
- The canonical `docs/agentpprof-paper` submodule must remain untouched.
- Writing and review do not perform Git operations. Git is independent of every
  scientific transition.
- The pipeline never waits for human intervention. Uncertainty is recorded and
  the most scientifically valuable in-scope option is selected.

## Story-Fidelity Audit

### Thesis

**Status: preserved.**

The exact thesis appears in the abstract, introduction, and conclusion. Step
0035 did not replace it with a hierarchy-only, recurrence-only, or diagnostic-
ranking thesis.

### Core abstractions

**Status: preserved.**

The paper retains only the two original core abstractions:

1. operation; and
2. operation stack.

Recurrence, mappings, taggers, rankers, reference calibration, pprof export,
and visualizations remain mechanisms or optional modes. None has been promoted
to a new paper-level abstraction.

### Research questions

**Status: preserved.**

All four RQ headings and their order are unchanged. Step 0035 adds evidence to
RQ1 but does not redefine attribution as clustering, remove resource ownership
from the question, or substitute a new RQ.

### Contribution and scope

**Status: preserved, with one ownership correction still required.**

The contribution chain remains profiling problem -> operation/operation-stack
model -> AgentProf artifact -> four-RQ evaluation. External verification shows
that AgentSight, rather than AgentProf, performs the causal process/effect-to-
action join. The paper must describe this input boundary accurately during the
next WRITE gate without weakening AgentProf's actual contribution: conservative
projection of heterogeneous additive operations through alternative semantic
responsibility hierarchies and standard profiler outputs.

### Idea-story update

**No update is authorized or required.**

Step 0035 changes evidence and exposes novelty pressure; it does not accept a
new thesis, problem, contribution, system direction, RQ, or narrative. The
Initial Narrative remains stronger and more faithful than a reviewer-driven
rewrite around hierarchy choice or fixed-budget localization. The selected
experiment tests a missing implication of the existing story; it does not
replace the story.

## Step 0035 Change Audit

### Accepted evidence

Step 0035 contributes a complete, reuse-only CodeTraceBench analysis over all
405 source-valid released trajectories, 20,866 operations, 2,948 human stages,
and 251 tasks:

- ordinary operation-level B-cubed precision/recall/F1 is the standard primary
  partition metric;
- recurrence reaches B-cubed F1 `0.649173` versus `0.541070` for matched raw-
  action identity;
- the paired task-clustered effect is `+0.108103`, with 95% interval
  `[+0.087091, +0.129132]`;
- the direction remains positive under three predeclared shared-response token
  allocations, with token-weighted B-cubed gains of approximately `+0.076` to
  `+0.085`;
- all mapped provider-token mass is conserved; and
- phase-only reaches `0.654445`, statistically indistinguishable from
  recurrence on this population.

The valid paper-level consequence is strong but bounded: semantic stage-aligned
organization improves partition agreement and resource-sensitive organization
over raw action identity. This experiment does not by itself establish that
recurrence dominates every semantic view or that human stages identify causal
resource owners.

The scoped AgentSight-to-AgentProf join evaluation also remains valid:

- capture/join precision is 100%;
- recall is 96.569%;
- all 1,629 negative controls are rejected; and
- AgentProf preserves all 1,520 joined effect rows.

The ownership boundary is essential: AgentSight supplies the join; AgentProf
preserves and reprojects the already joined additive observations.

### Writing changes

The 12-round WRITE loop integrated the authorized evidence, retained the exact
story and RQs, compiled a nine-page AAAI-style PDF, and kept technical content
within the first seven pages. Source verification found no literal claim that
the RQ2 test scorer gold was fed directly to the external localizers.

The writing loop did not solve the remaining scientific gaps. In particular,
it cannot prove diagnostic consequence, recurrence generalization, causal
resource ownership, or end-to-end cost merely by changing prose.

### Rejected interpretations

The audit rejects the following possible extrapolations:

- B-cubed stage agreement is not direct causal resource-owner accuracy.
- Token-weighted B-cubed is published and useful, but remains secondary to
  ordinary B-cubed rather than becoming a new headline metric.
- The fixed-reader six-task comparison does not prove lower operation-level
  inspection work.
- MAP over target-bearing trajectories does not measure clean-trajectory false
  positives.
- Recurrence and grouped-reference calibration are methods; Wilson lower bounds
  are a score; none is an evaluation metric.
- Work@50 and Work@80 are project-specific operational summaries and cannot
  replace official benchmark metrics or standard AP/MAP/recall/FPR.
- The current CodeTraceBench result is post-hoc support because the corpus
  influenced method development; it is not untouched confirmation.
- External products already perform cross-trace semantic aggregation, so the
  novelty cannot be stated as if all existing agent tools only display one
  trace at a time.

These interpretation limits do not narrow the thesis or remove any RQ. They
identify which evidence must be strengthened.

## Metric Audit

The next experiment and next WRITE gate must use a simple hierarchy of
evidence:

1. **Official benchmark metrics first.** These establish the quality and
   meaning of each fixed external signal on its source task.
2. **Standard cross-benchmark metrics second.** AP/MAP, recall at one fixed
   inspection budget, and false-positive rates isolate the organizational
   effect under matched information.
3. **Project-specific diagnostics last.** Work curves, Wilson group scores,
   tie behavior, and reader studies can explain mechanisms but cannot carry
   the primary claim.

For RQ3, exact boundary precision/recall/F1 and ordinary B-cubed are already
appropriate complementary standard metrics. Adding ARI, NMI, or several nearly
equivalent clustering scores would create metric volume without resolving the
scientific gap. The next recurrence experiment should improve baselines and
generalization rather than add more metrics.

## Whole-Paper Verdict

**Verdict: Weak Reject, confidence 0.84.**

**AAAI 2027 status:** format-plausible, scientifically incomplete.

The paper is not currently ready for a top-conference submission. Its strongest
assets are:

- a memorable and consequential thesis;
- a compact two-abstraction model;
- a working real system with standard profiler outputs;
- real local traces and several complete public benchmark populations;
- standard primary metrics for most reported tasks;
- explicit disclosure of post-hoc and scope boundaries; and
- a compiled AAAI-length artifact.

The largest remaining rejection pressure is the conjunction of known
components and missing decision consequence. The paper needs to demonstrate
that, with the underlying diagnostic evidence held fixed, semantic operation-
stack organization changes target-finding decisions at equal inspection cost
without simply spreading alarms across clean data. This is more immediately
verdict-changing than another recurrence threshold, field, or segmentation
variant on the two already inspected corpora.

## Next Outer Transition

**Transition:** `REVIEW_GATE -> EXPERIMENT_GATE`.

**Selected single experiment:** RQ2 same-signal diagnostic decomposition on
retained complete artifacts.

### Fixed experiment question

> Holding each benchmark's diagnostic signal fixed, does AgentProf's semantic
> operation-stack organization improve target finding at a fixed operation-
> inspection budget without increasing false positives on clean trajectories?

This question belongs to unchanged RQ2. It does not change the RQ, thesis,
hypothesis, hierarchy, localizer, or paper story.

### Required standard evidence

The experiment must report:

1. each fixed signal's official source-benchmark metrics:
   - AgentProcessBench step-level and first-error metrics;
   - HINTBench risk-detection, localization, and strict metrics;
   - TraceElephant agent, step, and available tolerance metrics;
2. the same retained predictions under atomic, raw-action, session, and current
   operation-stack organization;
3. standard trajectory MAP and pooled AP;
4. one predeclared recall-at-fixed-operation-budget result with actual inspected
   operation count;
5. clean-trajectory any-alert and false-positive-operation rates for the 386
   clean AgentProcessBench and 136 clean HINTBench trajectories; and
6. paired trajectory-level uncertainty where the metric admits pairing.

No localizer rerun, model change, hierarchy redesign, new benchmark, or new
algorithm is admitted in this experiment. A small analysis adapter may be used
only where the official evaluator cannot consume the retained artifact
directly; its output must be cross-checked against official code or stored raw
predictions.

### Baselines

The matched views are:

- atomic operation;
- raw-action grouping;
- whole-session grouping; and
- current AgentProf operation stack.

All receive exactly the same external per-operation predictions. This makes the
organizational consequence identifiable without pretending that AgentProf
created the diagnostic signal.

### Why this does not abandon algorithm improvement

The user's algorithm-improvement objective remains active. A later RQ3
experiment should compare or improve the existing recurrence constructor using
the already complete trajectories rather than invent an unrelated algorithm.
However, the existing OSWorld-Human and CodeTraceBench populations have already
informed several constructor decisions. Another cutoff, field, score, or depth
change on those same populations would add development evidence without
changing the current paper-level verdict.

Algorithm work is therefore sequenced after the selected RQ2 decomposition,
not removed. It will be admitted only if it changes a core recurrence mechanism
or supports a paper-level RQ answer, and it will retain standard exact-boundary
F1 and B-cubed F1 as the primary metrics.

## Capability and Project-Memory Audit

No new repository-local skill is justified by this cycle. The observed failure
was not a repeated missing mechanical capability; it was an evidence-selection
problem already handled by the outer REVIEW audit and experiment-design skill.
Creating another skill would add process complexity without changing the
experiment.

Durable evidence decisions are already represented in `docs/evaluation.md`.
The next EXPERIMENT report will update that document only after complete raw
results and result review. `docs/idea-story.md` remains unchanged because no
idea-level change was accepted.

## Completion of REVIEW Gate

The four REVIEW nodes are complete:

1. blind full-paper read;
2. external search and source verification;
3. source-grounded full-paper reread; and
4. cycle-change audit and final verdict.

The REVIEW gate does not require zero scientific objections. It has produced a
ranked, source-grounded verdict and selected one next experiment. The research
loop can therefore continue without human intervention.

**Next node:** `EXPERIMENT_GATE / RQ2 same-signal diagnostic decomposition`.
