# Addendum 001: reader change after kimi quota exhaustion

Timestamp: 2026-07-25T04:55:00-07:00
Author: root orchestrator

The kimi executor/reader hit its billing-cycle quota (403) at roughly
440/1,200 work items. No harness process survived; no fallback-contaminated
results were produced into scored outputs. This addendum modifies the task
spec as follows; everything not mentioned stands.

1. **Reader = `opencode` CLI** for ALL conditions on this workload.
   - Every reader call must run with its working directory set to a fresh
     EMPTY jail directory (as the kimi harness did with `kimi-cwd/`) so an
     agentic reader cannot browse the repository; the packet is the only
     input. The instruction must say to answer directly without using any
     tools. If opencode offers a tools-disabled or pure/chat mode, use it
     and document the exact flags.
   - After the run, sample 10 reader responses and confirm none references
     repository paths or target files (leakage spot-check recorded in
     results.md).
2. **Kimi partial responses are set aside, not scored and not deleted**:
   leave `raw-responses-*` from the kimi attempt in place, and write the
   opencode run into `raw-responses-<condition>-v2/` directories. Mixing
   readers within a workload is not permitted; only opencode responses are
   scored.
3. **Sequential conditions with per-condition completeness**: run the
   complete 400-query full-trace condition first, then the complete
   semantic-skeleton condition, then the complete raw-skeleton condition.
   If quota exhausts mid-study, a condition is reportable only if complete;
   partial conditions are set aside exactly like the kimi attempt.
4. **Resume support** per condition (skip already-answered queries on
   rerun) so an interrupted condition can be completed rather than
   restarted.
5. Executor may reuse `hint_index_study_eval.py` with the reader swap and
   the v2 response directories; document every change in execution-log.md.
