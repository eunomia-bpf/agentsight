# TraceElephant source-preserving operation profile

Timestamp: 2026-07-22T17:00:00-07:00

## Artifact

`traceelephant-a1.operations.pb.gz` is a standard pprof containing all 5,960
operations from 220 real failed TraceElephant trajectories. It was produced by
the release AgentPProf CLI from the fixed automatic-Agent marks. The product
emitted no image or custom visualization. The two PNG files in this directory
are screenshots of Go pprof's stock `/ui/flamegraph` view and are retained only
as inspected case-study derivatives.

The visible stack is:

```text
project -> agent -> semantic operation... -> tool
```

Dataset/task-family context and unique source session, call, and operation IDs
remain pprof labels rather than semantic operations. This lets
equal responsibilities aggregate across sessions while preserving evidence
drilldown. The 5,960 samples have naturally unequal total depths of 5--7 and
exact operation-count mass.

## Complete-population view

`traceelephant-all.flamegraph.png` shows the five complete agent/benchmark
populations. The largest top-level responsibilities are evidence-backed answer
construction (4,409 operations) and software-regression repair (1,551). The
source leaves retain the actual orchestrator, WebSurfer, editor, shell, and
specialist calls instead of replacing them with semantic labels.

## SWE-Agent case study

`swe-agent-44-sessions.flamegraph.png` focuses all 44 SWE-Agent/SWE-Bench
trajectories and all 1,551 of their operations, rather than one selected run.
The aggregate decomposition is:

- understand issue: 580 operations;
- reproduce issue: 418;
- change implementation: 312;
- verify repair: 111; and
- submit repair: 76.

The reproduction subtree is actionable. It separates 187 actual reproducer
runs from 150 operations spent repairing the reproducer harness, 49 inspecting
the reproducer, and 32 creating it. Harness repair occurs in 33 of 44 sessions
and in 112 separate episodes; 135 of its operations are editor calls and 14
are shell calls. Thus a maintainer can identify that a large fraction of the
failed population is cycling on diagnostic infrastructure rather than only on
the target implementation, then use `source_session` and `evidence_id` labels
to inspect the responsible traces.

The strongest single instance is `django__django-11299`: 57 of its 94
operations repair the reproducer harness and 32 run the reproducer. The trace
ends without a completed repair. The population flamegraph identifies the
recurring problem; that source trace provides the concrete evidence. This is a
localization and workload-decomposition conclusion, not a causal claim that
harness work alone caused every failure.

## Standard localization result

On the unchanged TraceElephant per-trajectory AP/MAP protocol, the same
source-preserving hierarchy scores 0.251926 MAP, compared with 0.230168 for the
source-native tree, 0.194094 for semantic-only Agent paths, and 0.129695 for
label-free recurrence. This result is reported separately from the visual case
and does not substitute for inspection of the profile.
