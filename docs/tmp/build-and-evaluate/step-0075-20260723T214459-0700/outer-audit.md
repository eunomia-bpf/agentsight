# Step 0075 Outer Audit

**Timestamp:** 2026-07-23T22:42:00-07:00  
**Transition:** EXPERIMENT → WRITE

## Inner completion

- proposed plan received an independent `research-experiment-design` review;
- two minimal revision rounds closed all plan blockers;
- the real 41-session preflight exercised every command path;
- three complete full repetitions finished for every deterministic component;
- an independent reviewer recomputed the complete result and verified the sole
  reporting correction.

## Scientific audit

The experiment tests one fixed RQ4 hypothesis and does not change the thesis,
four RQs, operation abstraction, A2 backend, or paper contribution surface.
Real public CodeTrace data and standard wall/RSS/pprof measurements are used.
No new benchmark, model, frontend, metric, or annotation algorithm was added.

The strongest admissible result is:

> On the complete 405-session input, A2 source-packet construction takes
> 501.64 seconds median, deterministic postprocessing takes 3.54 seconds, and
> current operation/token replay takes 1.17/1.17 seconds with exact mass.

Automatic-Agent inference wall time and token usage remain unavailable. The
54.36-minute artifact chronology is context only.

## Memory and story audit

`docs/evaluation.md` records the new frontier and exact evidence boundary.
`docs/idea-story.md` records why Step 0075 strengthens cost evidence without
authorizing a story or RQ change. User instructions and the canonical
submodule-derived story remain unchanged.

## Transition decision

Step 0075 passes. WRITE may update only RQ4 evidence and adjacent factual
summary text, preserving the authoritative AgentProf story. Git state is
irrelevant to the scientific transition.
