# Cost record

Current accounting phase: **full**

- backend: `codex-cli 0.145.0`, model `gpt-5.6-sol`;
- sessions selected/successful: 287/287;
- Codex calls: 288;
- format retries: 1;
- failures after retry: 0;
- summed backend wall: 2854.536 s;
- active backend wall across four-worker waves: 728.360 s;
- usage counters: `{"cache_write_input_tokens": 0, "cached_input_tokens": 3838464, "input_tokens": 5483576, "output_tokens": 64231, "reasoning_output_tokens": 40843}`.

The active-wall value is the union of recorded backend-call intervals; summed wall adds every individual call. Token counters are the Codex CLI turn-completion counters retained for every attempt.
