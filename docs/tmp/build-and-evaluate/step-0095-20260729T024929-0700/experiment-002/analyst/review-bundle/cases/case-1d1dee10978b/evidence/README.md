# Analyst evidence package

This directory contains flat JSONL sample tuples for 338 same-task bad/good
AgentReward pairs drawn from 440 source trajectories. The semantic stack is
`task -> subtask -> strategy -> action -> object -> result`.

Each line in `samples.jsonl` has exactly these fields:

- `sample_type`: pprof sample type;
- `unit`: pprof sample unit;
- `value`: signed sample value, with positive for the bad side and negative
  for the good side;
- `stack_frames`: ordered pprof frame names in leaf-to-root order; and
- `labels`: the exact pprof string labels, represented as key-to-value-list.

The file preserves duplicate tuples and source order. It contains no derived
rates, pair manifest, aggregate result summary, or rendered figure.

Basic inspection examples:

```bash
head -n 1 samples.jsonl | jq .
jq -c 'select(.value > 0)' samples.jsonl
jq -c 'select(.value < 0)' samples.jsonl
```
