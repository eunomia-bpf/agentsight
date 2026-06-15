# R121 Model Benchmark

Date: 2026-06-15

Command:

```bash
cargo run --manifest-path agentflame/Cargo.toml -- bench --llama-server $HOME/workspace/llama.cpp-latest/build/bin/llama-server --runs 3 --load-timeout 240 --request-timeout 60 --include-fragment-previews --out .agentsight/agentflame/model-benchmarks.json --model 3b=$HOME/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf
```

Result:

| Model | Load ms | Runs | Ok | Failed | Valid run % | Stable fragments | Exact stability % | Latency ms | Tags |
|-------|---------|------|----|--------|-------------|------------------|-------------------|------------|------|
| 3b | 1002 | 9 | 9 | 0 | 100.000 | 2/3 | 66.667 | 41, 8, 8, 20, 14, 13, 15, 8, 7 | refactor, test, test, updateosdi, updateosdi, updateosdi, research, research, research |

Model discovery found 1 real model GGUF(s).
The remaining 17 GGUF files in
`$HOME/workspace/llama.cpp-latest/models` are vocab fixtures or too small to be usable
model weights for this benchmark. Missing size classes:
0.6b, 1b.


### Model `3b` Fragments

| Fragment | Stable | Distinct | Modal | Tags | Preview |
|----------|--------|----------|-------|------|---------|
| f0 | no | 2 | test | refactor, test, test | User asks the coding agent to fix a failing Rust unit test, edit source code, and rerun cargo test. |
| f1 | yes | 1 | updateosdi | updateosdi, updateosdi, updateosdi | User asks the agent to summarize research evidence and update an OSDI experiment plan without changing source code. |
| f2 | yes | 1 | research | research, research, research | An assistant LLM call compares span-duration traces with semantic system-effect attribution for a paper draft. |

Interpretation:

- Supported: the 3B local llama.cpp benchmark path works and produced valid
  one-word tags in 9/9 runs.
- Mixed: fixed-input exact stability is 2/3 fragments (66.667%).
- Not supported: 0.6B/1B feasibility and human adequacy.
- Claim impact: C2 can cite 3B syntax/latency feasibility; C6 remains partial
  until human adequacy labels exist.
