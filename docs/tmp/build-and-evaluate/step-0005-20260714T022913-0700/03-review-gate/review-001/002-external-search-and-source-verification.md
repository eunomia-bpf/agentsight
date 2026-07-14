# External Search and Source Verification

## Node record

- Completed: 2026-07-14T03:09:18-07:00
- Scope: closest scientific work and profiler capability boundaries relevant
  to the complete paper
- Decision: related-work differentiation remains incomplete but does not
  invalidate the Step 0005 RQ4 result

## Closest branches to add in a later literature-owned WRITE pass

1. [Hodoscope](https://arxiv.org/abs/2604.11072) performs cross-run semantic
   behavior discovery and reports reduced inspection effort.
2. [Process-Centric Analysis of Agentic Software Systems](https://arxiv.org/abs/2512.02393)
   builds semantic and temporal trajectory structures over thousands of agent
   runs.
3. [Event abstraction for process mining](https://arxiv.org/abs/1606.07283)
   learns high-level semantic events and evaluates sequence abstraction.
4. [pprof tag support](https://github.com/google/pprof/blob/main/doc/README.md#tags)
   already provides tag breakdown and `tagroot`/`tagleaf` pseudo-frames.

## Defensible differentiation

The paper should not claim generic tag aggregation, hierarchy, or visualization
as unique. Its stronger joint capability is:

> derive recurring semantic responsibility fields from heterogeneous agent
> histories, propagate them to downstream process/file/network effects, and
> construct query-time profiler hierarchies over additive measures.

The current Introduction and status-quo wording already moved toward this
boundary. The Related Work section still needs a dedicated later update, but
the missing prose does not authorize changing the thesis or system story.
