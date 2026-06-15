# R114 Smoke: Scoped Negative-Control Precision

Date: 2026-06-14

Command:

```bash
python3 docs/visexp/r114_live_record_suite.py \
  --task-limit 1 \
  --out /tmp/agentsight-r114-smoke-out5 \
  --work-dir /tmp/agentsight-r114-smoke-work5 \
  --timeout 240
```

Result:

| Tasks | Effects | Joined | Orphans | In scope | Out scope | Raw join | Precision | Recall | Negative observed | Negative joined |
|-------|--------:|-------:|--------:|---------:|----------:|---------:|----------:|-------:|------------------:|----------------:|
| 1 | 395 | 45 | 350 | 45 | 44 | 11.392% | 100.0% | 100.0% | 306 | 0 |

Interpretation:

- The collector now retargets the command-mode record envelope from the wrapper
  root to the real `codex` child process via `--agent-comm codex`.
- Raw join rate is intentionally low: wrapper bootstrap, sibling work, and
  negative-control effects are still observed, but they are not attributed to
  the agent process family.
- The scoped smoke gate now passes: 45/45 in-scope effects joined, 0 false
  positives, 0 false negatives, and 0/306 negative-control effects attributed.
- This unblocks the full 20-task R114 run. It does not by itself widen C4 beyond
  smoke evidence.
