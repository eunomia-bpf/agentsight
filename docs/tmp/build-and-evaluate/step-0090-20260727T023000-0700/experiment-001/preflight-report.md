# Real preflight report

Status: **PASS**

The independently approved adapter was exercised on real frozen artifacts
before the full profiles were admitted.

| Path | Real input | Required check | Result |
|---|---|---|---|
| Git time | all 119 fixed OpenHands/Claude evidence rows and its 25 fixed mark transitions | every call mapped to one retained ISO action timestamp; unchanged fixed marks; positive values; current binary; stock pprof | pass |
| Created file | first successful retained Step-0086 `Add File` target | accepted semantic path -> parent LLM -> exact `apply_patch` evidence -> exact created target | pass |
| R114 system | all 39 retained `r114-failure-retry` rows | exactly one recorded wrapper-tool ID; current binary; stock pprof | pass |

All three preflight profiles loaded through `go tool pprof -top` and
`go tool pprof -traces`. Producer stdout reported `status=ok`, no warnings,
and exact input/profile mass.

The first Git preflight invocation correctly failed closed because the complete
three-session mark file referred to two sequences absent from the one-session
subset. A deterministic preflight-only projection retained the unchanged
66-name dictionary and the 25 fixed transitions for the selected sequence.
The rerun passed. The full run uses the original complete mark file unchanged.

Preflight artifacts are prefixed `preflight.` in this directory. They are
sanity artifacts only and do not contribute a separately reported scientific
result.
