# Plan review — query-conditioned AgentCap task aggregation

Timestamp: 2026-07-21T21:18:00-07:00
Decision: PASS

## Scientific and product value

The plan directly tests the requested interaction: an analyst supplies a task
family, AgentPProf-compatible preprocessing marks a bounded number of task
transitions, and independent runs aggregate because run identity is not a stack
frame. Four complete traces are enough to test the product shape without
pretending to be a broad accuracy benchmark.

## Data, leakage, and executability

The sessions are real Codex trajectories and all operations in each selected
trace are retained. The labels intentionally use the review request and visible
trajectory content; this is query-conditioned analysis, not a blinded predictor
of review outcome. Therefore the prototype must not report the annotation as
semantic-tag accuracy. Source line ranges make every transition auditable.

The existing normalized operation records and AgentPProf operation-file path
are sufficient. No new backend, UI, model call, custom metric, or rendering
code is needed.

## Scope check

The design does not require reading every AgentCap session. It avoids fixed
depth, per-operation LLM labeling, session frames, and a taxonomy large enough
to fragment aggregation. The acceptance checks are limited to coverage,
resource conservation, variable depth, cross-session aggregation, and standard
pprof readability.
