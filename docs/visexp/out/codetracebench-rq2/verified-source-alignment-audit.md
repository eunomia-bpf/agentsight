# CodeTraceBench Verified-Source Alignment Audit

**Status:** PARTIAL PASS — the complete verified population was inspected; 911/992 available raw archives align exactly, and 89 rows are excluded from label-aligned scoring rather than count-fitted.

## Information Boundary

The audit loads only the runner's safe manifest projection: trajectory identity, framework/model/task/cohort fields, outcome, public step count, and raw-artifact paths. It does not project or read stages, incorrect/unuseful step IDs, labels, annotation paths, or annotation reasoning. Adapter rules are source-structural. The public step count is used only as an assertion; the runner never truncates, pads, synthesizes, or selects a branch to make a count match.

## Complete Verified-Population Result

| Framework | Source layout | Verified rows | Raw available | Exact | Mismatch | Error | Missing | Adapter |
|---|---|---:|---:|---:|---:|---:|---:|---|
| OpenHands | native | 207 | 199 | 185 | 14 | 0 | 8 | openhands-agent-actions |
| OpenHands | swe_raw | 313 | 313 | 313 | 0 | 0 | 0 | openhands-maximal-visible-action-context |
| SWE-agent | swe_raw | 108 | 108 | 106 | 2 | 0 | 0 | sweagent-trajectory-elements |
| Terminus2 | native | 222 | 222 | 174 | 46 | 2 | 0 | terminus2-commands-txt-strings |
| mini-SWE-agent | native | 82 | 82 | 65 | 17 | 0 | 0 | miniswe-agent-log-markers, miniswe-message-trajectory |
| mini-SWE-agent | swe_raw | 68 | 68 | 68 | 0 | 0 | 0 | miniswe-message-trajectory |

## OpenHands SWE-Raw Lineage Audit

All 313 verified OpenHands SWE-raw archives were inspected. The maximum-visible-assistant-tool-history rule aligns exactly for 313/313 rows. 57 rows contain at least one chronological context decrease (restart or compaction), and 137 rows have more than one request at the maximum visible-tool count, across 14070 request records. Selection maximizes assistant tool-call history and breaks ties by timestamp/path; it never uses the manifest step count or response content.

This establishes a complete source-only structural result for the released SWE-raw OpenHands population. It does not by itself prove the eventual differential scorer or label join.

## Invalid Or Unresolved Rows

Rows below remain visible as source-quality exclusions. They are not silently repaired and cannot enter label-aligned target metrics until a published or independently source-grounded normalization rule resolves them.

| Trajectory | Framework/layout | Expected | Observed | Status | Adapter | Detail |
|---|---|---:|---:|---|---|---|
| `sweagent-OpenAI__GPT-5-keras-team__keras-19775-5d529dfd` | SWE-agent/swe_raw | 26 | 48 | step mismatch | sweagent-trajectory-elements | source operation count differs from public step_count |
| `sweagent-OpenAI__GPT-5-mui__material-ui-11451-c1ca3d8a` | SWE-agent/swe_raw | 54 | 94 | step mismatch | sweagent-trajectory-elements | source operation count differs from public step_count |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-chem-rf-271f890f` | OpenHands/native | 31 | 59 | step mismatch | openhands-agent-actions | source operation count differs from public step_count |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-lean4-proof-c2cf74ba` | OpenHands/native | 82 | 91 | step mismatch | openhands-agent-actions | source operation count differs from public step_count |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-mteb-eval-09ae8a74` | OpenHands/native | 30 | 38 | step mismatch | openhands-agent-actions | source operation count differs from public step_count |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-train-fasttext-b326259b` | OpenHands/native | 47 | 57 | step mismatch | openhands-agent-actions | source operation count differs from public step_count |
| `openhands-DeepSeek__DeepSeek-V3.2-3d-model-format-legacy-109d1beb` | OpenHands/native | 73 | 75 | step mismatch | openhands-agent-actions | source operation count differs from public step_count |
| `openhands-DeepSeek__DeepSeek-V3.2-adaptive-rejection-sampler-5191debf` | OpenHands/native | 47 | 49 | step mismatch | openhands-agent-actions | source operation count differs from public step_count |
| `openhands-DeepSeek__DeepSeek-V3.2-add-benchmark-lm-eval-harness-f672ceba` | OpenHands/native | 85 | 86 | step mismatch | openhands-agent-actions | source operation count differs from public step_count |
| `openhands-DeepSeek__DeepSeek-V3.2-break-filter-js-from-html-eb19b6bc` | OpenHands/native | 100 | - | missing archive | - | artifact_path absent or archive unavailable |
| `openhands-DeepSeek__DeepSeek-V3.2-caffe-cifar-10-f7852850` | OpenHands/native | 35 | 46 | step mismatch | openhands-agent-actions | source operation count differs from public step_count |
| `openhands-DeepSeek__DeepSeek-V3.2-cross-entropy-method-5d3f18d2` | OpenHands/native | 35 | 39 | step mismatch | openhands-agent-actions | source operation count differs from public step_count |
| `openhands-DeepSeek__DeepSeek-V3.2-db-wal-recovery-2063f818` | OpenHands/native | 85 | - | missing archive | - | artifact_path absent or archive unavailable |
| `openhands-DeepSeek__DeepSeek-V3.2-dna-assembly-1d47c200` | OpenHands/native | 35 | 40 | step mismatch | openhands-agent-actions | source operation count differs from public step_count |
| `openhands-DeepSeek__DeepSeek-V3.2-feal-differential-cryptanalysis-5a64f808` | OpenHands/native | 35 | 47 | step mismatch | openhands-agent-actions | source operation count differs from public step_count |
| `openhands-DeepSeek__DeepSeek-V3.2-fibonacci-server-b246383b` | OpenHands/native | 43 | - | missing archive | - | artifact_path absent or archive unavailable |
| `openhands-DeepSeek__DeepSeek-V3.2-filter-js-from-html-0661aa2d` | OpenHands/native | 54 | - | missing archive | - | artifact_path absent or archive unavailable |
| `openhands-DeepSeek__DeepSeek-V3.2-get-bitcoin-nodes-4cb80bf9` | OpenHands/native | 89 | - | missing archive | - | artifact_path absent or archive unavailable |
| `openhands-DeepSeek__DeepSeek-V3.2-install-windows-3.11-17800883` | OpenHands/native | 75 | - | missing archive | - | artifact_path absent or archive unavailable |
| `openhands-DeepSeek__DeepSeek-V3.2-largest-eigenval-d5360284` | OpenHands/native | 85 | - | missing archive | - | artifact_path absent or archive unavailable |
| `openhands-DeepSeek__DeepSeek-V3.2-lean4-proof-313ecb3f` | OpenHands/native | 73 | 83 | step mismatch | openhands-agent-actions | source operation count differs from public step_count |
| `openhands-DeepSeek__DeepSeek-V3.2-llm-inference-batching-scheduler-bb7aecc5` | OpenHands/native | 48 | 51 | step mismatch | openhands-agent-actions | source operation count differs from public step_count |
| `openhands-DeepSeek__DeepSeek-V3.2-make-mips-interpreter-45083164` | OpenHands/native | 60 | 68 | step mismatch | openhands-agent-actions | source operation count differs from public step_count |
| `openhands-DeepSeek__DeepSeek-V3.2-neuron-to-jaxley-conversion-e342c3ae` | OpenHands/native | 52 | - | missing archive | - | artifact_path absent or archive unavailable |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-compile-compcert-997ae681` | mini-SWE-agent/native | 73 | 72 | step mismatch | miniswe-agent-log-markers | source operation count differs from public step_count |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-cron-broken-network-e82a5c2f` | mini-SWE-agent/native | 37 | 0 | step mismatch | miniswe-agent-log-markers | source operation count differs from public step_count |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-dna-insert-3d3baf3a` | mini-SWE-agent/native | 23 | 8 | step mismatch | miniswe-agent-log-markers | source operation count differs from public step_count |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-feal-differential-cryptanalysis-c6a0e7f0` | mini-SWE-agent/native | 35 | 18 | step mismatch | miniswe-agent-log-markers | source operation count differs from public step_count |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-hf-model-inference-f200d460` | mini-SWE-agent/native | 34 | 27 | step mismatch | miniswe-agent-log-markers | source operation count differs from public step_count |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-jupyter-notebook-server-f7fce821` | mini-SWE-agent/native | 27 | 37 | step mismatch | miniswe-agent-log-markers | source operation count differs from public step_count |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-large-scale-text-editing-e70ac842` | mini-SWE-agent/native | 21 | 18 | step mismatch | miniswe-agent-log-markers | source operation count differs from public step_count |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-mlflow-register-60a717c0` | mini-SWE-agent/native | 21 | 0 | step mismatch | miniswe-agent-log-markers | source operation count differs from public step_count |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-play-zork-easy-8c77a548` | mini-SWE-agent/native | 33 | 14 | step mismatch | miniswe-agent-log-markers | source operation count differs from public step_count |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-pytorch-model-cli-1a764f1f` | mini-SWE-agent/native | 21 | 39 | step mismatch | miniswe-agent-log-markers | source operation count differs from public step_count |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-schemelike-metacircular-eval-1494da6d` | mini-SWE-agent/native | 64 | 0 | step mismatch | miniswe-agent-log-markers | source operation count differs from public step_count |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-solana-data-72de38cf` | mini-SWE-agent/native | 35 | 0 | step mismatch | miniswe-agent-log-markers | source operation count differs from public step_count |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-stable-parallel-kmeans-a1318efd` | mini-SWE-agent/native | 32 | 4 | step mismatch | miniswe-agent-log-markers | source operation count differs from public step_count |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-tmux-advanced-workflow-04e67d90` | mini-SWE-agent/native | 33 | 1 | step mismatch | miniswe-agent-log-markers | source operation count differs from public step_count |
| `miniswe-DeepSeek__DeepSeek-V3.2-hf-lora-adapter-ff04189f` | mini-SWE-agent/native | 32 | 20 | step mismatch | miniswe-message-trajectory | source operation count differs from public step_count |
| `miniswe-DeepSeek__DeepSeek-V3.2-interactive-maze-game-40d2a8b0` | mini-SWE-agent/native | 22 | 33 | step mismatch | miniswe-message-trajectory | source operation count differs from public step_count |
| `miniswe-DeepSeek__DeepSeek-V3.2-pytorch-model-recovery-4cbae484` | mini-SWE-agent/native | 26 | 37 | step mismatch | miniswe-message-trajectory | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-3d-model-format-legacy-5eb709af` | Terminus2/native | 94 | 95 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-add-benchmark-lm-eval-harness-11987c87` | Terminus2/native | 206 | 208 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-audio-synth-stft-peaks-e07e3ef5` | Terminus2/native | 37 | 38 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-blind-maze-explorer-5x5-dc477a42` | Terminus2/native | 46 | 47 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-blind-maze-explorer-algorithm-e5814a22` | Terminus2/native | 47 | 48 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-broken-python-02d55149` | Terminus2/native | 30 | 34 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-cython-ext-a7e47d56` | Terminus2/native | 53 | 56 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-stp-56801309` | Terminus2/native | 40 | 41 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-catch-me-if-you-can-d89cfe9a` | Terminus2/native | 68 | 69 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-causal-inference-r-887a15bd` | Terminus2/native | 53 | 54 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-chess-best-move-b049f713` | Terminus2/native | 34 | - | adapter error | - | Terminus2 archive has no commands.txt |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-code-from-image-14a45388` | Terminus2/native | 27 | 28 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-count-dataset-tokens-ad1d3494` | Terminus2/native | 40 | 41 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-cron-broken-network-5669e672` | Terminus2/native | 63 | 64 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-db-wal-recovery-6792ef3f` | Terminus2/native | 29 | 30 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-filter-js-from-html-61cd1fd1` | Terminus2/native | 20 | 21 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-fix-ocaml-gc-5784d704` | Terminus2/native | 327 | 328 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-form-filling-6907bd11` | Terminus2/native | 22 | 23 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-hydra-debug-slurm-mode-837c94b0` | Terminus2/native | 26 | 27 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-install-klee-minimal-57ed56f5` | Terminus2/native | 100 | 104 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-largest-eigenval-eb9cc4f2` | Terminus2/native | 57 | 58 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-leelachess0-pytorch-conversion-4b4c022f` | Terminus2/native | 29 | 30 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-llm-inference-batching-scheduler-36976180` | Terminus2/native | 33 | 34 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-llm-spec-decoding-a5cda7d7` | Terminus2/native | 23 | 24 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-logistic-regression-divergence-0b8df7b3` | Terminus2/native | 27 | 28 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-mailman-3540eeca` | Terminus2/native | 44 | - | adapter error | - | Terminus2 archive has no commands.txt |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-make-mips-interpreter-35ea4c65` | Terminus2/native | 61 | 62 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-npm-conflict-resolution-1fb2a796` | Terminus2/native | 37 | 38 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-parallelize-graph-619aaf8f` | Terminus2/native | 47 | 48 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-path-tracing-reverse-f5f5b8bf` | Terminus2/native | 59 | 60 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-play-zork-c2eb2245` | Terminus2/native | 199 | 200 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-port-compressor-b12aa2b9` | Terminus2/native | 105 | 106 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-processing-pipeline-b359442c` | Terminus2/native | 22 | 23 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-protein-assembly-dfa5f8b4` | Terminus2/native | 35 | 36 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-protocol-analysis-rs-7c5f5525` | Terminus2/native | 62 | 63 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-reshard-c4-data-14835550` | Terminus2/native | 37 | 38 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-rstan-to-pystan-6adcbc5e` | Terminus2/native | 38 | 39 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-stable-parallel-kmeans-9f16d721` | Terminus2/native | 37 | 38 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-swe-bench-astropy-1-6b5580a5` | Terminus2/native | 26 | 27 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-triton-interpret-13f3a750` | Terminus2/native | 36 | 37 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-vul-flink-220ab971` | Terminus2/native | 41 | 43 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-wasm-pipeline-1db8244f` | Terminus2/native | 45 | 46 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-DeepSeek__DeepSeek-V3.2-3d-model-format-legacy-5276d859` | Terminus2/native | 282 | 277 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-DeepSeek__DeepSeek-V3.2-caffe-cifar-10-04955e02` | Terminus2/native | 160 | 159 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-DeepSeek__DeepSeek-V3.2-compile-compcert-4c8013f9` | Terminus2/native | 186 | 185 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-DeepSeek__DeepSeek-V3.2-install-windows-3.11-9b3a3ca5` | Terminus2/native | 202 | 199 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-DeepSeek__DeepSeek-V3.2-leelachess0-pytorch-conversion-a0b986ad` | Terminus2/native | 200 | 198 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |
| `terminus2-DeepSeek__DeepSeek-V3.2-mcmc-sampling-stan-db249f0b` | Terminus2/native | 81 | 78 | step mismatch | terminus2-commands-txt-strings | source operation count differs from public step_count |

## Decision

Use only exact, source-valid failed verified trajectories for step-localization metrics. Keep auditing every full-manifest archive for reference-profile coverage. This is an experiment-plan repair caused by released source/normalization drift; it does not change RQ2, the tested hypothesis, the thesis, or the paper story.
