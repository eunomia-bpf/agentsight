# ToolSafe Source Preparation Report

**Status:** PASS — exact official joins and allowlisted projection complete.

The projection contains visible operation fields and published TS-Guard outputs only. Labels are stored in separate per-family files. No attack metadata or outcome-bearing source path is projected.

| Family | Records | Operations | Non-operations | Safe | Controversial | Unsafe |
|---|---:|---:|---:|---:|---:|---:|
| agentharm | 731 | 731 | 0 | 206 | 315 | 210 |
| asb | 5231 | 4835 | 396 | 2696 | 1466 | 1069 |
| agentdojo | 1220 | 1220 | 0 | 868 | 0 | 352 |

Total: 7182 records; 6786 real operations; 396 declared non-operations.

Exact checks: every `meta_sample` equals its released TS-Bench row; every `labels.json` value equals the row score; every published prediction equals the stored guard result.
