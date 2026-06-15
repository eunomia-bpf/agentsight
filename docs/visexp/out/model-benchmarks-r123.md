# R123 Model Benchmark

Date: 2026-06-15

Command:

```bash
cargo run --manifest-path agentflame/Cargo.toml -- bench --llama-server $HOME/workspace/llama.cpp-latest/build/bin/llama-server --runs 3 --load-timeout 240 --request-timeout 60 --fragment-file .agentsight/agentflame/r122-real-fragments.txt --out .agentsight/agentflame/model-benchmarks-r123.json --model 3b=$HOME/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf
```

Result:

| Model | Load ms | Runs | Ok | Failed | Valid run % | Stable fragments | Exact stability % | Latency ms | Tags |
|-------|---------|------|----|--------|-------------|------------------|-------------------|------------|------|
| 3b | 1002 | 900 | 900 | 0 | 100.000 | 282/300 | 94.000 | n=900, min=7, p50=11, p95=30, max=67 | review:241, refactor:195, test:37, docs:22, design:21, trace:21, debug:14, verify:13, cleanup:12, readdocs:12, audit:9, benchmarks:9 |

Model discovery found 1 real model GGUF(s).
The remaining 17 GGUF files in
`$HOME/workspace/llama.cpp-latest/models` are vocab fixtures or too small to be usable
model weights for this benchmark. Missing size classes:
0.6b, 1b.


### Model `3b` Fragments

| Fragment | Stable | Distinct | Modal | Tags | Preview |
|----------|--------|----------|-------|------|---------|
| f0 | yes | 1 | audit | audit, audit, audit | (omitted) |
| f1 | yes | 1 | refactor | refactor, refactor, refactor | (omitted) |
| f2 | yes | 1 | claimid | claimid, claimid, claimid | (omitted) |
| f3 | yes | 1 | benchmarks | benchmarks, benchmarks, benchmarks | (omitted) |
| f4 | yes | 1 | cmt | cmt, cmt, cmt | (omitted) |
| f5 | yes | 1 | readdocs | readdocs, readdocs, readdocs | (omitted) |
| f6 | yes | 1 | readdocs | readdocs, readdocs, readdocs | (omitted) |
| f7 | yes | 1 | refactor | refactor, refactor, refactor | (omitted) |
| f8 | yes | 1 | jsonokno | jsonokno, jsonokno, jsonokno | (omitted) |
| f9 | yes | 1 | countlines | countlines, countlines, countlines | (omitted) |
| f10 | yes | 1 | cmt | cmt, cmt, cmt | (omitted) |
| f11 | no | 2 | review | readdocs, review, review | (omitted) |
| f12 | yes | 1 | docsupdate | docsupdate, docsupdate, docsupdate | (omitted) |
| f13 | yes | 1 | claimid | claimid, claimid, claimid | (omitted) |
| f14 | yes | 1 | benchmarks | benchmarks, benchmarks, benchmarks | (omitted) |
| f15 | yes | 1 | cmt | cmt, cmt, cmt | (omitted) |
| f16 | yes | 1 | research | research, research, research | (omitted) |
| f17 | yes | 1 | docsupdate | docsupdate, docsupdate, docsupdate | (omitted) |
| f18 | yes | 1 | jsonokno | jsonokno, jsonokno, jsonokno | (omitted) |
| f19 | yes | 1 | countlines | countlines, countlines, countlines | (omitted) |
| f20 | no | 2 | review | readdocs, review, review | (omitted) |
| f21 | yes | 1 | rootpidcount | rootpidcount, rootpidcount, rootpidcount | (omitted) |
| f22 | yes | 1 | claimid | claimid, claimid, claimid | (omitted) |
| f23 | yes | 1 | benchmarks | benchmarks, benchmarks, benchmarks | (omitted) |
| f24 | yes | 1 | readdocs | readdocs, readdocs, readdocs | (omitted) |
| f25 | no | 2 | review | readdocs, review, review | (omitted) |
| f26 | yes | 1 | review | review, review, review | (omitted) |
| f27 | yes | 1 | count | count, count, count | (omitted) |
| f28 | yes | 1 | refactor | refactor, refactor, refactor | (omitted) |
| f29 | yes | 1 | count | count, count, count | (omitted) |

270 additional fragments are in the JSON artifact.

Interpretation:

- Supported: the 3B local llama.cpp benchmark path works and produced valid
  one-word tags in 900/900 runs.
- Mixed: fixed-input exact stability is 282/300 fragments (94.000%).
- Not supported: 0.6B/1B feasibility and human adequacy.
- Claim impact: C2 can cite 3B syntax/latency feasibility; C6 remains partial
  until human adequacy labels exist.
