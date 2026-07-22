# AgentRewardBench collection differential pprof

The primary Case Study 2 artifact is
`agentreward-338-pairs-bad-minus-good.operations.pb.gz`. It aggregates every
bad-good pair in the complete Step 0063 population: 440 real sessions across
125 mixed-outcome tasks, forming 338 pairs. Positive samples are bad-side
excess and negative samples are good-side excess. This collection profile, not
one selected pair, is the case study.

```bash
go tool pprof -top \
  agentreward-338-pairs-bad-minus-good.operations.pb.gz
go tool pprof -top -focus='error|repeated|stopped' \
  agentreward-338-pairs-bad-minus-good.operations.pb.gz
go tool pprof -top -focus='terminal|conclusion|send_msg_to_user' \
  agentreward-338-pairs-bad-minus-good.operations.pb.gz
```

The two VisualWebArena-512 files are retained only as source-evidence
drilldowns for one path found in the aggregate collection. They are not a
standalone case study. In that pair, the candidate is an unsuccessful Qwen
2.5-VL-72B session and the base is a successful Claude 3.7 Sonnet session.

```bash
go tool pprof -top visualwebarena-512-bad-minus-good.operations.pb.gz
go tool pprof -top visualwebarena-512-bad-minus-good.tokens.pb.gz
go tool pprof -top -focus='error|repeated|stopped' \
  visualwebarena-512-bad-minus-good.tokens.pb.gz
go tool pprof -top -focus='conclusion' \
  visualwebarena-512-bad-minus-good.tokens.pb.gz
```

No custom frontend or rendered derivative is part of this artifact. Use any
pprof-compatible viewer for visualization and interactive drilldown.

SHA-256:

```text
cb7a9b6f63c6ad88d2c88dca35312d6463f33308391710e876d08f8db9b13ccc  agentreward-338-pairs-bad-minus-good.operations.pb.gz
ee56631f8eedcd60d86c541028a4ff5df60c26c013ca6bb74c594be3480db379  visualwebarena-512-bad-minus-good.operations.pb.gz
32d41cd7d0f30996962e1a6e3d2771558e26791ac92c5e047954a9d0c3c03eba  visualwebarena-512-bad-minus-good.tokens.pb.gz
```
