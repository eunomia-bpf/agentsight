# Analyst evidence package

This directory contains one standard pprof differential profile built from
338 same-task bad/good AgentReward pairs drawn from 440 source trajectories.
Its semantic stack is `task -> subtask -> strategy -> action -> object ->
result`.

The sample type is `operations/count`. Positive samples are operations from
the bad side of a pair and negative samples are operations from the good side.
The signed profile is bad minus good. Sample labels retain source lineage and
comparison metadata.

Inspect the profile with stock pprof, for example:

```bash
go tool pprof -top agentreward-338-pairs-bad-minus-good.operations.pb.gz
go tool pprof -tags agentreward-338-pairs-bad-minus-good.operations.pb.gz
go tool pprof -raw agentreward-338-pairs-bad-minus-good.operations.pb.gz
```

No aggregate result summary or rendered figure is included.
