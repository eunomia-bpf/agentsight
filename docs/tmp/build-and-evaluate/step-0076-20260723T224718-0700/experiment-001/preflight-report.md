# Real preflight report

Timestamp: 2026-07-23T23:03:00-07:00
Status: PASS

## Scope

The preflight used the first approved Git-deployment source session:

```text
openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-git-multibranch-75c1745e
```

It exercised the final data path rather than a synthetic fixture:

1. filter the adopted count input by the literal session ID;
2. convert the accepted annotation-workspace paths to operation marks;
3. retain only the selected session's sparse marks;
4. replay them with the current release binary and the approved
   `project,agent,operation,call,tool` stack;
5. open the resulting `.pb.gz` with stock `go tool pprof -top`.

## Observations

- source operations: 119;
- unique evidence IDs: 119;
- emitted profile mass: 119;
- stock-pprof readback: PASS;
- CLI exit status: zero;
- final binary path:
  `agentpprof/target/release/agentpprof`;
- diagnostic output:
  `.agentsight/experiments/rq1-matched-organization-v1/preflight/`.

The full three-session filter was also materialized before the preflight:

- count rows: 489;
- token rows: 489;
- unique evidence IDs: 489;
- token mass: 4,558,192;
- tool-level sparse path-transition marks: 79.

The 79 transitions are a mechanical compression of the accepted paths, not a
change to the workspace's 96 mixed-level annotations. Exact expansion over all
489 operations is a full-run completion check.

## Decision

The real input, accepted-path adapter, operation-mark contract, current
binary, final semantic stack, pprof serialization, and stock reader all work
end to end. Proceed to the complete six-profile run without changing the
plan.

