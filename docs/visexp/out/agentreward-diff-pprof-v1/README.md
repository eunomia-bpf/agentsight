# AgentRewardBench collection differential pprof

The primary Case Study 2 artifact is
`agentreward-338-pairs-recursive-bad-minus-good.operations.pb.gz`. It
aggregates every bad--good pair in the complete population: 440 real
trajectories across 125 mixed-outcome tasks, forming 338 pair occurrences.
Positive samples are bad-side excess and negative samples are good-side
excess. This collection profile, not one selected pair, is the case study.
Its stack contains the automatic Agent's recursive operations followed by
source LLM-call and tool-call leaves. Labels retain source session and step
identity for stock-tool drilldown.

```bash
go tool pprof -top \
  agentreward-338-pairs-recursive-bad-minus-good.operations.pb.gz
go tool pprof -top \
  -focus='recover_from_failed_or_repeated_interaction' \
  agentreward-338-pairs-recursive-bad-minus-good.operations.pb.gz
go tool pprof -top \
  -focus='verify_or_report_task_completion' \
  agentreward-338-pairs-recursive-bad-minus-good.operations.pb.gz
```

The automatic backend was outcome-blind. Only after all 440 trajectories were
annotated and independently audited did the evaluator open the task outcomes
and the independent expert `trajectory_looping` endpoint. The canonical
recovery-path score has AP 0.613735 versus prevalence 0.397701; its
10,000-draw task-cluster interval over prevalence is
`[+0.162023, +0.273910]`. The corresponding fixed-chain baseline has AP
0.655962, and the recursive-minus-fixed interval
`[-0.127370, +0.041557]` does not establish incremental superiority. The
result supports correspondence to a real problem, not universal dominance.

`agentreward-440-trajectories-recursive.operations.pb.gz` is the unsigned
population profile. It contains 7,229 operation samples and has observed
semantic depth four before the LLM-call and tool-call evidence leaves. The
workspace that generated it is `recursive-annotation-v1/`.

The earlier fixed-chain profile
`agentreward-338-pairs-bad-minus-good.operations.pb.gz` is retained as the
registered comparison, not as the primary recursive case figure. The two
VisualWebArena-512 files are retained only as source-evidence drilldowns for
one path found in the aggregate collection; they are not standalone case
studies.

```bash
go tool pprof -top visualwebarena-512-bad-minus-good.operations.pb.gz
go tool pprof -top visualwebarena-512-bad-minus-good.tokens.pb.gz
go tool pprof -top -focus='error|repeated|stopped' \
  visualwebarena-512-bad-minus-good.tokens.pb.gz
go tool pprof -top -focus='conclusion' \
  visualwebarena-512-bad-minus-good.tokens.pb.gz
```

`agentreward-recovery.recursive.stock-pprof.png` and
`agentreward-completion.recursive.stock-pprof.png` are screenshots of the
stock Go pprof `/ui/flamegraph` view under the two preregistered operation
focuses. They expose the recursive task hierarchy and the source call/tool
leaves. They are paper/inspection derivatives, not AgentPProf product outputs.
AgentPProf itself emits only standard `.pb` or `.pb.gz` profiles; use any
pprof-compatible viewer for interactive visualization and drilldown.

SHA-256:

```text
bcb8843bafd3fb5aa5bab0e0b7cc560c870382763a08cb781e85da23f277e2dc  agentreward-338-pairs-recursive-bad-minus-good.operations.pb.gz
fdb33f8c9554c40e76964923b02d50d399a543e61e5c84532d5b5fa747e04114  agentreward-440-trajectories-recursive.operations.pb.gz
0d6a7e80fbc805d374ad6bd4b668241584150a317049a45b4d0045f473b7495d  agentreward-338-pairs-bad-minus-good.operations.pb.gz
ee56631f8eedcd60d86c541028a4ff5df60c26c013ca6bb74c594be3480db379  visualwebarena-512-bad-minus-good.operations.pb.gz
32d41cd7d0f30996962e1a6e3d2771558e26791ac92c5e047954a9d0c3c03eba  visualwebarena-512-bad-minus-good.tokens.pb.gz
```
