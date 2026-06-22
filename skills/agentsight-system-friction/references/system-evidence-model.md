# System Evidence Model

Normalize AgentSight evidence into these records. Keep exact join keys internally for correlation; render reader-facing reports with category labels unless private-debug output is requested.

## SessionProcess

- `session_id`, `agent`, `project`, `time_range`
- `pid`, `ppid`, `process_name`, `command_summary`
- `start_time`, `end_time`, `duration`, `exit_status`

## CommandEffect

- `session_id`, `pid`, `command_summary`
- `cwd_summary`, `exit_code`, `duration`, `status`
- `stdout_summary`, `stderr_summary` when safe

## FileEffect

- `session_id`, `pid`, `path_pattern`
- `operation`: read, write, create, delete, rename, chmod, unknown
- `workspace_relation`: inside workspace, outside workspace, home, system, unknown

## NetworkEffect

- `session_id`, `pid`, `host`, `port`, `protocol`
- `direction`, `request_class`, `status`
- never include raw auth headers or full HTTP bodies by default

## ResourceEffect

- `session_id`, `pid`, `cpu`, `rss`, `io`, `duration`
- sample window and aggregation method when available

## Join Keys

Preserve available `session_id`, `trace_id`, timestamps, pid, command hash/summary, and source row ids in working notes or machine-readable private-debug output when correlation is needed. For HTML reports, convert them to reader-safe labels such as session category, time window, command category, path category, host category, or resource window category.
