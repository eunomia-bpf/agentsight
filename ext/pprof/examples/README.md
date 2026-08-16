# agentpprof Public Fixture

This directory contains a small synthetic Codex JSONL session for smoke-testing
`agentpprof` without reading private `~/.codex` or `~/.claude` history.

```bash
agentpprof \
  --project-root . \
  --project-name agentsight-public-fixture \
  --session-file ext/pprof/examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl \
  --tagger regex \
  --no-cache \
  -o tasks.pb.gz

go tool pprof -top tasks.pb.gz
```

The fixture is intentionally tiny. It only verifies parser, projection, and
pprof readback behavior; it is not user-study or tag-quality evidence.
