# Step 0027 — AAAI Milestone Review And Existing-Trajectory Routing

**Started:** 2026-07-15T06:52:07-07:00  
**Completed:** 2026-07-15T07:14:00-07:00  
**Phase:** BUILD_AND_EVALUATE  
**Outer gate:** REVIEW  
**Status:** Complete

## Fixed Contract

The exact thesis remains **“Agent observability needs profiling, not only
debugging.”** The four RQs remain attribution, localization/correspondence, tag
accuracy, and cost. The original AgentProf story remains authoritative.
`docs/agentpprof-paper` stayed read-only. No skill, KVM material, branch, or
global repository was changed.

## REVIEW Gate

The complete AAAI-format paper received a paper-only blind read, cross-domain
systems/AI attack map, primary-source closest-work search, full reread, and
cycle-change audit. Reports are under
[`milestone-review-001`](milestone-review-001/).

The current paper is a **4/10 weak reject**: the profiler model and RQ1/RQ4 are
credible, but RQ3 remains incomplete under its own hypothesis and RQ2 lacks a
decisive developer consequence. Official AAAI-27 format checks pass at seven
content pages plus two reference pages; the reproducibility checklist remains
unfilled.

External verification confirms that LangSmith Insights and Datadog Patterns
already provide cross-trace semantic hierarchies, and NVIDIA NeMo provides a
real agent workflow profiler. AgentProf's defensible distinction is therefore
source-linked additive cross-layer effects, selectable conserved operation
stacks, and pprof compatibility. The newly found Insights Generator preprint is
the strongest same-problem RQ2 threat because it reports downstream scaffold
improvement from corpus-level diagnostic reports.

## Gate Decision

The user's requested algorithm improvement can and should reuse the existing
complete trajectories. Step 0026 rules out another action-only local cutoff;
it does not rule out a target-label-withheld calibration learned from
independent reference annotations already present in the downloaded artifacts.

The unique next step is supporting RQ3 group-boundary work: retain the current action-transition NPMI and all
operation-stack construction after the cutoff, learn only the cutoff from
reference boundaries, and evaluate once on the same five OSWorld held-out folds
and same 405 CodeTraceBench reused development-target trajectories with target
labels withheld during fitting. This is a supervised mode, not a relabeling of
the label-free release result and not a complete RQ3 answer. Phase, action, and
literal-name accuracy remain open. No new dataset or paper edit is authorized
in this step.

## Outputs

- blind full-paper read and attack map;
- primary-source external search and novelty verification;
- full-paper reread assessment;
- cycle-change audit and final verdict;
- selected existing-trajectory RQ3 experiment for the next step.
