# R123 Model Benchmark

Date: 2026-06-15

Command:

```bash
cargo run --manifest-path agentflame/Cargo.toml -- bench --llama-server $HOME/workspace/llama.cpp-latest/build/bin/llama-server --runs 3 --load-timeout 240 --request-timeout 60 --include-fragment-previews --out .agentsight/agentflame/model-benchmarks.json --model 3b=$HOME/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf
```

Result:

| Model | Load ms | Runs | Ok | Failed | Valid run % | Stable fragments | Exact stability % | Latency ms | Tags |
|-------|---------|------|----|--------|-------------|------------------|-------------------|------------|------|
| 3b | 1002 | 900 | 900 | 0 | 100.000 | 285/300 | 95.000 | n=900, min=8, p50=11, p95=31, max=71 | review:229, refactor:168, test:57, design:34, docs:17, trace:15, verify:15, analyze:12, readdocs:12, build:11, benchmarks:9, claimid:9 |

Model discovery found 1 real model GGUF(s).
The remaining 17 GGUF files in
`$HOME/workspace/llama.cpp-latest/models` are vocab fixtures or too small to be usable
model weights for this benchmark. Missing size classes:
0.6b, 1b.


### Model `3b` Fragments

| Fragment | Stable | Distinct | Modal | Tags | Preview |
|----------|--------|----------|-------|------|---------|
| f0 | yes | 1 | review | review, review, review | (omitted) |
| f1 | yes | 1 | review | review, review, review | (omitted) |
| f2 | no | 2 | rootpidcount | rootpidrefsc, rootpidcount, rootpidcount | (omitted) |
| f3 | yes | 1 | refactor | refactor, refactor, refactor | (omitted) |
| f4 | yes | 1 | paperagentfl | paperagentfl, paperagentfl, paperagentfl | (omitted) |
| f5 | yes | 1 | readdocs | readdocs, readdocs, readdocs | (omitted) |
| f6 | yes | 1 | countlines | countlines, countlines, countlines | (omitted) |
| f7 | yes | 1 | cmt | cmt, cmt, cmt | (omitted) |
| f8 | no | 2 | rootpidcount | rootpidrefsc, rootpidcount, rootpidcount | (omitted) |
| f9 | yes | 1 | claimid | claimid, claimid, claimid | (omitted) |
| f10 | yes | 1 | benchmarks | benchmarks, benchmarks, benchmarks | (omitted) |
| f11 | yes | 1 | readdocs | readdocs, readdocs, readdocs | (omitted) |
| f12 | yes | 1 | cmt | cmt, cmt, cmt | (omitted) |
| f13 | no | 2 | rootpidcount | rootpidrefsc, rootpidcount, rootpidcount | (omitted) |
| f14 | yes | 1 | claimid | claimid, claimid, claimid | (omitted) |
| f15 | yes | 1 | benchmarks | benchmarks, benchmarks, benchmarks | (omitted) |
| f16 | yes | 1 | readdocs | readdocs, readdocs, readdocs | (omitted) |
| f17 | yes | 1 | review | review, review, review | (omitted) |
| f18 | yes | 1 | refactor | refactor, refactor, refactor | (omitted) |
| f19 | yes | 1 | jsonok | jsonok, jsonok, jsonok | (omitted) |
| f20 | yes | 1 | benchmarks | benchmarks, benchmarks, benchmarks | (omitted) |
| f21 | yes | 1 | cmt | cmt, cmt, cmt | (omitted) |
| f22 | no | 2 | rootpidcount | rootpidrefsc, rootpidcount, rootpidcount | (omitted) |
| f23 | yes | 1 | claimid | claimid, claimid, claimid | (omitted) |
| f24 | yes | 1 | paperagentfl | paperagentfl, paperagentfl, paperagentfl | (omitted) |
| f25 | yes | 1 | readdocs | readdocs, readdocs, readdocs | (omitted) |
| f26 | yes | 1 | nextaction | nextaction, nextaction, nextaction | (omitted) |
| f27 | yes | 1 | nextaction | nextaction, nextaction, nextaction | (omitted) |
| f28 | yes | 1 | review | review, review, review | (omitted) |
| f29 | yes | 1 | refactor | refactor, refactor, refactor | (omitted) |
| f30 | yes | 1 | count | count, count, count | (omitted) |
| f31 | yes | 1 | rdocboundary | rdocboundary, rdocboundary, rdocboundary | (omitted) |
| f32 | no | 2 | criterion | ccept, criterion, criterion | (omitted) |
| f33 | yes | 1 | rdocboundary | rdocboundary, rdocboundary, rdocboundary | (omitted) |
| f34 | no | 2 | criterion | ccept, criterion, criterion | (omitted) |
| f35 | yes | 1 | review | review, review, review | (omitted) |
| f36 | yes | 1 | count | count, count, count | (omitted) |
| f37 | yes | 1 | refactor | refactor, refactor, refactor | (omitted) |
| f38 | yes | 1 | review | review, review, review | (omitted) |
| f39 | yes | 1 | review | review, review, review | (omitted) |
| f40 | yes | 1 | review | review, review, review | (omitted) |
| f41 | yes | 1 | review | review, review, review | (omitted) |
| f42 | yes | 1 | review | review, review, review | (omitted) |
| f43 | yes | 1 | refactor | refactor, refactor, refactor | (omitted) |
| f44 | yes | 1 | cli | cli, cli, cli | (omitted) |
| f45 | yes | 1 | agentsight | agentsight, agentsight, agentsight | (omitted) |
| f46 | yes | 1 | rawsslok | rawsslok, rawsslok, rawsslok | (omitted) |
| f47 | yes | 1 | review | review, review, review | (omitted) |
| f48 | yes | 1 | confirmed | confirmed, confirmed, confirmed | (omitted) |
| f49 | yes | 1 | review | review, review, review | (omitted) |

250 additional fragments are in the JSON artifact.

Interpretation:

- Supported: the 3B local llama.cpp benchmark path works and produced valid
  one-word tags in 900/900 runs.
- Mixed: fixed-input exact stability is 285/300 fragments (95.000%).
- Not supported: 0.6B/1B feasibility and human adequacy.
- Claim impact: C2 can cite 3B syntax/latency feasibility; C6 remains partial
  until human adequacy labels exist.
