# R180 Model Benchmark

Date: 2026-06-15

Command:

```bash
cargo run --manifest-path agentflame/Cargo.toml -- bench --llama-server $HOME/workspace/llama.cpp-latest/build/bin/llama-server --server-arg=--reasoning --server-arg=off --server-arg=--ctx-size --server-arg=2048 --runs 3 --load-timeout 240 --request-timeout 60 --fragment-file .agentsight/agentflame/r122-real-fragments.txt --out .agentsight/agentflame/model-benchmarks-r180.json --model 0.6b=$HOME/workspace/gpu/xpu-perf/test/qwen3.cu/Qwen3-0.6B-FP32.gguf --model 1.1b=$HOME/workspace/gpu/gpu_ext/workloads/llama.cpp/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf --model 3b=$HOME/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf
```

Result:

| Model | Load ms | Runs | Ok | Failed | Valid run % | Stable fragments | Exact stability % | Latency ms | Tags |
|-------|---------|------|----|--------|-------------|------------------|-------------------|------------|------|
| 0.6b | 2529 | 900 | 900 | 0 | 100.000 | 299/300 | 99.667 | n=900, min=8, p50=9, p95=23, max=106 | debug:472, docs:78, review:54, render:51, build:39, research:24, root:12, trace:12, repo:9, run:9, agent:6, baseline:6 |
| 1.1b | 1002 | 900 | 900 | 0 | 100.000 | 279/300 | 93.000 | n=900, min=10, p50=11, p95=18, max=36 | localization:642, localized:228, localsession:18, fragmentkind:9, localizedai:3 |
| 3b | 1003 | 900 | 900 | 0 | 100.000 | 285/300 | 95.000 | n=900, min=7, p50=10, p95=32, max=66 | review:229, refactor:168, test:57, design:34, docs:17, trace:15, verify:15, analyze:12, readdocs:12, build:11, benchmarks:9, claimid:9 |

Model discovery found 1 real model GGUF(s).
The remaining 17 GGUF files in
`$HOME/workspace/llama.cpp-latest/models` are vocab fixtures or too small to be usable
model weights for this benchmark. Bench model classes:
0.6b->0.6b, 1.1b->1b, 3b->3b.

Missing size classes:
none.


### Model `0.6b` Fragments

| Fragment | Stable | Distinct | Modal | Tags | Preview |
|----------|--------|----------|-------|------|---------|
| f0 | yes | 1 | review | review, review, review | (omitted) |
| f1 | yes | 1 | debug | debug, debug, debug | (omitted) |
| f2 | yes | 1 | root | root, root, root | (omitted) |
| f3 | yes | 1 | debug | debug, debug, debug | (omitted) |
| f4 | yes | 1 | paper | paper, paper, paper | (omitted) |
| f5 | yes | 1 | docs | docs, docs, docs | (omitted) |
| f6 | yes | 1 | span | span, span, span | (omitted) |
| f7 | yes | 1 | debug | debug, debug, debug | (omitted) |
| f8 | yes | 1 | root | root, root, root | (omitted) |
| f9 | yes | 1 | docs | docs, docs, docs | (omitted) |
| f10 | yes | 1 | debug | debug, debug, debug | (omitted) |
| f11 | yes | 1 | docs | docs, docs, docs | (omitted) |
| f12 | yes | 1 | debug | debug, debug, debug | (omitted) |
| f13 | yes | 1 | root | root, root, root | (omitted) |
| f14 | yes | 1 | docs | docs, docs, docs | (omitted) |
| f15 | yes | 1 | debug | debug, debug, debug | (omitted) |
| f16 | yes | 1 | docs | docs, docs, docs | (omitted) |
| f17 | yes | 1 | debug | debug, debug, debug | (omitted) |
| f18 | yes | 1 | docs | docs, docs, docs | (omitted) |
| f19 | yes | 1 | json | json, json, json | (omitted) |

280 additional fragments are in the JSON artifact.

### Model `1.1b` Fragments

| Fragment | Stable | Distinct | Modal | Tags | Preview |
|----------|--------|----------|-------|------|---------|
| f0 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f1 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f2 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f3 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f4 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f5 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f6 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f7 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f8 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f9 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f10 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f11 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f12 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f13 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f14 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f15 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f16 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f17 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f18 | yes | 1 | localization | localization, localization, localization | (omitted) |
| f19 | yes | 1 | localization | localization, localization, localization | (omitted) |

280 additional fragments are in the JSON artifact.

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

280 additional fragments are in the JSON artifact.

Interpretation:

- Local llama.cpp benchmark paths produced syntactically valid one-word tags for 0.6b, 1.1b, 3b.
- Fixed-input exact stability over 300 redacted R122 session/prompt/LLM-call fragments: 0.6b 299/300, 1.1b 279/300, 3b 285/300.
- The compared GGUFs are locally available models with different families or quantization paths; use this as a deployment-cost smoke, not a controlled model-family scaling result.
- This run does not measure human adequacy; R124 remains required before C6 can become stronger than partial.

Claim impact: C2 can cite only the model classes that actually ran. C6 remains
partial until human adequacy labels exist.
