# 04 — Cycle-Change Audit and Final Verdict

- **Timestamp:** 2026-07-22T23:05:00-07:00
- **Parent:** `step-0068-20260722T223854-0700/milestone-review-001`
- **Objective:** audit the completed EXPERIMENT→WRITE→REVIEW cycle against the
  paper, idea story, user instructions, implementation, and next-gate choice

## Audited inputs

- `docs/idea-story.md`, read from the permanent initial narrative through the
  current frontier
- `docs/user-instruction.md`
- `docs/evaluation.md`
- current `docs/paper/main.tex` and `main.pdf`
- Step 0067 experiment, independent result review, WRITE report, and
  consistency review
- both fresh-model full-paper reviews and verified primary sources
- AgentPProf hierarchy-warning implementation and tests

## Intent and story audit

### Preserved

- The thesis remains exactly: **“Agent observability needs profiling, not only
  debugging.”**
- The core model remains two objects: operation and operation stack.
- RQ2, RQ3, and RQ4 retain their accepted meanings.
- New case-study evidence strengthens the original broad story instead of
  replacing it with an anomaly detector, a recursive-segmentation paper, or a
  pprof-export paper.
- Real systems, complete public populations, standard metrics, and stock pprof
  tools remain the evidence basis.
- No branch was created or switched.

### Not preserved strongly enough

The RQ2 prose violates source-fidelity by describing declared/reference
hierarchy gains without naming that configuration, allowing them to be read as
automatic-backend gains. `Sem.` is target-blind and is not a gold-label oracle.
The two AgentProf configurations must be separated explicitly.

The fixed RQ1 asks whether semantic profiling improves resource attribution;
the paper currently asks the narrower question of whether one hierarchy exposes
different bottlenecks. This wording drift is not authorized by the idea story
or user instructions.

## Cycle evidence audit

### EXPERIMENT gate

Step 0067 completed its registered real-population AgentReward experiment:
440 trajectories, 125 mixed-outcome tasks, 338 bad--good pair occurrences,
2,131 automatic annotations over 7,229 source operations, independent AP and
bootstrap recomputation, and valid pprof outputs. The result supports
problem-correspondence and source-drillable differential explanation; it does
not establish detector superiority over the registered fixed chain.

### WRITE gate

The paper added two complete-population cases, corrected direct-versus-
cumulative long-horizon widths, documented warning semantics, rebuilt a
10-page PDF, and passed a focused consistency review. The subsequent full-paper
review found the older Table 1/prose attribution defect, showing why local
consistency review cannot substitute for complete-paper skeptical review.

### REVIEW gate

Grok 4.5 and Claude Opus classified the paper as incomplete-but-promising and
preserved the ambitious thesis. Grok is the confirmed clean paper-only
transcript; Claude is a fresh-model review with disclosed repository-context
contamination. Primary-source search confirms a crowded product/research
neighborhood. A closest-capability comparison is a high-value candidate, not an
automatic new gate.

## Gate decision

**REVIEW outcome: REVISE.**

The next outer action is:

1. **targeted WRITE:** separate RQ2 declared/reference and automatic results at
   full precision, and restore the fixed RQ1 attribution wording, without
   changing the thesis, other RQs, abstract/intro architecture, or table
   values;
2. **reassess:** decide whether the corrected paper already has an authorized
   next experiment under one fixed RQ and one claim;
3. **EXPERIMENT, if selected:** plan one runnable information-fair comparison;
4. **WRITE/REVIEW:** integrate only a complete result and repeat the
   full-paper audit.

The WRITE correction comes first because experiment selection should start from
the paper's correct current state. The review does not pre-authorize a composite
multi-RQ experiment.

## Experiment-selection boundary

Admit a new experiment only if it changes the paper-level answer to RQ1/RQ2 or
directly resolves the closest-work objection. Do not admit:

- another benchmark solely to increase count;
- another annotation backend with no new decision;
- another cutoff, score, or heuristic variant;
- a human study that blocks autonomous progress;
- a warning-free-depth optimization;
- a new visualization frontend.

Prefer existing real inputs, complete runs, published or official baselines,
and standard metrics appropriate to the one selected RQ.

## Memory and search-tree update

Record as durable:

- Full-paper arithmetic review caught a claim-source error missed by local
  consistency review.
- External hierarchy products operate at trace/category level; AgentProf must
  empirically earn the value of within-trace operation spans, replayed resource
  measures, and evidence drilldown.
- Mechanical hierarchy warnings are useful product QA but neither proof of
  semantic quality nor an experiment gate.
- The current paper should grow by stronger evidence, not by more terminology
  or more backend variants.

## Final verdict

**Not submission-ready; 4–5/10 today.** The project is materially ahead of the
original submodule in implementation, complete experiments, automatic
structure evaluation, source-drillable case studies, and cost measurement.
The scientific idea remains large enough for AAAI/NeurIPS-level consideration.
The immediate blockers are source-faithful RQ2 configuration attribution and
restoring the fixed RQ1 question. A decisive same-input comparison may be the
highest-value subsequent experiment, but this review does not establish it as
the only route to acceptance.

## Completion and uncertainty

**Status: complete.** The REVIEW gate is closed with a concrete route. No paper
or skill file was edited during this review. Commercial-baseline availability
is uncertain and nonblocking; the next experiment plan must select the most
scientifically faithful runnable alternative and continue.
