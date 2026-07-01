# Example Patterns

Use these examples as field-shape hints.

## Long-Running Process

Input:

```json
{"session_id":"s1","pid":1234,"process":"npm run dev","duration_minutes":127,"still_running":true}
```

Finding:

- `severity`: medium, or high if it blocks ports/resources
- `claim`: agent left a process running after the task window
- `evidence`: session category, command category, duration; keep exact ids/pids internal unless private-debug is requested
- `next_action`: give the service a lease and shutdown hook; preserve a short owner/log summary if it stays active

## File Scope Risk

Input:

```json
{"session_id":"s2","operation":"read","path":"/home/user/.aws/credentials"}
```

Finding:

- `severity`: high
- `claim`: agent accessed secret-adjacent material outside the workspace
- `evidence`: path pattern only, not file contents
- `next_action`: mask secret-adjacent paths by default and emit a rotation recommendation if exposure is confirmed; correlate with interaction intent

## Resource Waste

Input:

```json
{"session_id":"s3","command":"cargo test","exit_code":101,"count":5,"wall_minutes":28}
```

Finding:

- `severity`: medium
- `claim`: repeated failing command consumed time without a successful system result
- `evidence`: command summary, exit code, repeat count, duration
- `next_action`: inspect the first failure, rerun the narrowest relevant command, and stop repeated full reruns after the retry budget is spent

## Correlate With Interaction Findings

Output a redacted correlation summary instead of reading transcripts:

```json
{"severity":"medium","time_range":"10:22-10:39","command_category":"test command","result":"failed"}
```

The interaction skill can use this summary to compare against user goals or final claims.

## User-Facing System Report

Input:

```json
{"reader":"agent owner","decision":"decide what to change before the next agent run","finding":"resource peaks, long-running services, network listeners, and state file growth appear in monitor evidence"}
```

Output:

- Lead with the 3-5 concrete workflow changes most likely to improve the next run.
- Explain resource pressure, service lifecycle, network exposure, cleanup, and capture confidence in plain operator language before showing tables.
- Put technical source details in a short appendix.
