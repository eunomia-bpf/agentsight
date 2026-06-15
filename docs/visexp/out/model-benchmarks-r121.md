# R121 Model Benchmark Smoke

Date: 2026-06-15

Command:

```bash
cargo run --manifest-path agentflame/Cargo.toml -- bench \
  --llama-server /home/yunwei37/workspace/llama.cpp-latest/build/bin/llama-server \
  --runs 3 \
  --load-timeout 240 \
  --request-timeout 60 \
  --out .agentsight/agentflame/model-benchmarks.json \
  --model 3b=/home/yunwei37/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf
```

Result:

| Model | Load ms | Runs | Ok | Failed | Latency ms | Tags |
|-------|---------|------|----|--------|------------|------|
| 3b | 1004 | 3 | 3 | 0 | 41, 17, 15 | render, debug, label |

Model discovery found one real model GGUF, `qwen2.5-3b-instruct-q4_k_m.gguf`.
The remaining 17 GGUF files in the local model directory are vocab fixtures, not
usable model weights for this benchmark. No 0.6B or 1B model path was available.

Interpretation:

- Supported: the 3B local llama.cpp benchmark path works and produced valid
  one-word tags in 3/3 runs.
- Not supported: 0.6B/1B feasibility, human adequacy, or tag stability.
- Design gap: current `agentflame bench` embeds the run index in the prompt, so
  repeated runs do not test identical-input stability.
