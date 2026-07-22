# Result review — AgentCap query-conditioned aggregation

Timestamp: 2026-07-21T21:20:00-07:00
Decision: PASS for the requested product prototype

## What the run establishes

The tested hypothesis is supported. Four independent real sessions aggregate
under one user-facing task root, every high-level responsibility is shared by
at least two traces, and the task hierarchy retains two- and three-frame paths.
The standard pprof view makes the largest recurring responsibility immediately
visible: verifying repairs occupies 95/326 operations, followed by experiment
evidence auditing at 72/326.

The result also clarifies the desired interface. The annotator need not return
a new record for every operation or inspect every project session. It can first
choose a bounded vocabulary from enough task-family context, then return sparse
transition positions. Existing operations inherit the active path. Aggregation
works when canonical responsibility names enter the stack and trace identity
stays in labels.

## Checks against misleading success

The graph does not aggregate merely because all samples share a synthetic root.
Seven distinct high-level responsibilities receive contributions from two to
four independent traces, and their sub-responsibilities retain different
widths. Conversely, putting run IDs or full result text in the stack was
rejected because it produced concatenated or fragmented paths rather than a
useful overview.

No semantic accuracy number is reported. There is no independent gold task
stack for these sessions, and the range annotations used visible review
content. The evidence supports a usable representation and workflow, not a
general automatic induction claim.

## Product consequence

The promising design is:

1. accept a user query or task-family focus;
2. inspect enough summaries/trajectories to propose a small canonical task
   vocabulary;
3. mark sparse transition positions per selected session;
4. inherit labels between transitions and permit recursive subtask marking;
5. fold the resulting repeated task values with AgentPProf;
6. preserve run identity and evidence hashes as pprof labels, not frames.

The next product iteration should generalize this adapter into an input
interface for externally supplied sparse task-boundary annotations. It should
not yet add an always-on per-operation LLM tagger or a new renderer.
