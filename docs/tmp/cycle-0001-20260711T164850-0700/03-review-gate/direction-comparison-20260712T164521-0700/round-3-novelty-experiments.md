# Idea Discussion Round 3 — Novelty, Results, and Experiment

**Completed:** 2026-07-12T16:55:55-07:00  
**Mode:** fresh read-only `iter-refine-ideas` discussion  
**Files read:** project instructions, verbatim user log, complete idea story,
both complete papers, literature/evaluation frontiers, admitted RQ2 result
reviews, and Hodoscope paired summaries  
**External search:** none; only already verified sources were interpreted  
**Mutations:** none

## Precedent Map

Existing work fully precedes individual mechanisms: weighted profiling and
labels in pprof, stack visualization, query-derived aggregation in Perfetto,
causal grouping in Pivot Tracing, aggregate-trace comparison, domain-specific
hierarchies, and differential flame graphs. Hodoscope is the strongest same-
problem neighbor for semantic cross-run cohort discovery. ARIA,
AgentDiagnose, OTel/OpenInference, AgentRx, and TELBench are partial neighbors.

These precedents block novelty claims for aggregation, semantic dimensions,
hierarchy construction, cross-run comparison, visualization, or differential
comparison alone. The admitted map contains no verified full precedent for the
complete population-level agent-profiling direction; a fresh literature node
must test that conclusion before the next plan.

## Result Interpretation

AgentProf establishes conserved weighted profile construction and reprojection.
AgentRx/TELBench contradict the tested induced-leaf localization mechanism.
Hodoscope shows a decisive official-bundle advantage, while crossing-zero
flat/native-versus-recursive intervals prevent attributing the loss to
hierarchy alone. None directly challenges the paper thesis because none tests a
fair recurring additive profiling decision.

## Difference, Alternatives, and Question

The submodule is ambitious but undercontrolled; the immediately previous story
overcorrected toward hierarchy selection; the current direction restores the
broad thesis and treats representation as conditional. Two promising routes
are differential regression profiling and intervention-based evaluation. The
important unasked question is what concrete action changes after viewing a
profile and whether a held-out rerun improves.

## One Next Complete Experiment

Screen two pinned public SWE-agent revisions or configurations on official
SWE-bench Verified tasks, recorded through AgentSight. Admit a pair only when a
stable token or wall-time regression appears without a material outcome drop
and a real source-native hierarchy is available. Fix the semantic projection on
pilot tasks, then compare flat, native, and semantic views on held-out tasks
using identical operations and measures. The primary outcome is effort to
produce an intervention that recovers the regression without reducing official
success. Retain every task, failed intervention, and null result; never retune
on held-out outcomes.

