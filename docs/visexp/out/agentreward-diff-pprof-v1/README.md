# AgentRewardBench differential pprof case

These are the standard pprof outputs for the source-verified
VisualWebArena 512 case in step 0063. The candidate is the unsuccessful Qwen
2.5-VL-72B trace; the base is the successful Claude 3.7 Sonnet trace. Positive
samples are candidate excess and negative samples are base excess.

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
ee56631f8eedcd60d86c541028a4ff5df60c26c013ca6bb74c594be3480db379  visualwebarena-512-bad-minus-good.operations.pb.gz
32d41cd7d0f30996962e1a6e3d2771558e26791ac92c5e047954a9d0c3c03eba  visualwebarena-512-bad-minus-good.tokens.pb.gz
```
