# R114 Smoke: Negative-Control Precision

Date: 2026-06-15

Command:

```bash
python3 docs/visexp/r114_live_record_suite.py \
  --task-limit 1 \
  --out /tmp/agentsight-r114-smoke-out2 \
  --work-dir /tmp/agentsight-r114-smoke-work2 \
  --timeout 240
```

Result:

| Tasks | Effects | Joined | Orphans | Raw join | Precision | Recall | Negative observed | Negative joined |
|-------|--------:|-------:|--------:|---------:|----------:|-------:|------------------:|----------------:|
| 1 | 408 | 408 | 0 | 100.0% | 25.98% | 100.0% | 302 | 302 |

Interpretation:

- The R114 suite path works end to end for one real `codex exec` task.
- Raw join rate is insufficient: all 408 effects joined, but all 302 wrapper
  negative-control effects were also attributed to the agent-run tool.
- C4 remains partial. The next implementation step is to fix or explicitly
  scope wrapper/sibling false positives before running the 20-task suite.
