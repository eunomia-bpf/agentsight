# CodeTraceBench Full Source Coverage

**Status:** COMPLETE — all 3316 full-manifest trajectories have a terminal source status.

This ledger was produced from the safe manifest projection and public raw archives. It does not load step annotations. Source-invalid rows are excluded rather than truncated, padded, synthesized, or count-fitted.

## Summary

| Framework | Source-valid | Excluded |
|---|---:|---:|
| OpenHands | 1045 | 197 |
| SWE-agent | 122 | 5 |
| Terminus2 | 765 | 158 |
| mini-SWE-agent | 785 | 239 |

Overall: 2717 source-valid; 599 excluded.

## Terminal Ledger

| Trajectory | Framework | Outcome | Declared steps | Status | Adapter/reason |
|---|---|---|---:|---|---|
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-add-benchmark-lm-eval-harness-54ac67f0` | mini-SWE-agent | false | 47 | source-valid | miniswe-message-trajectory; 47 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-analyze-access-logs-a7f4d66a` | mini-SWE-agent | true | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-ancient-puzzle-e86cea24` | mini-SWE-agent | true | 17 | source-valid | miniswe-agent-log-markers; 17 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-assign-seats-7a2e6bf6` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-attention-mil-5da3063a` | mini-SWE-agent | true | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-audio-synth-stft-peaks-c05fb8b4` | mini-SWE-agent | false | 18 | excluded | miniswe-agent-log-markers emitted 10 operations; public step_count is 18 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-bank-trans-filter-e5ea2b10` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-blind-maze-explorer-5x5-fd963f2b` | mini-SWE-agent | false | 15 | source-valid | miniswe-agent-log-markers; 15 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-blind-maze-explorer-algorithm-aef5e7ed` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-bn-fit-modify-3a7f7d1e` | mini-SWE-agent | true | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-break-filter-js-from-html-2393609c` | mini-SWE-agent | false | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-broken-python-05edf5bc` | mini-SWE-agent | true | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-cython-ext-d15c5d03` | mini-SWE-agent | false | 36 | source-valid | miniswe-message-trajectory; 36 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-initramfs-qemu-4d6aad60` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-linux-kernel-qemu-504a7c57` | mini-SWE-agent | false | 36 | source-valid | miniswe-message-trajectory; 36 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-pmars-23413a0e` | mini-SWE-agent | false | 44 | source-valid | miniswe-message-trajectory; 44 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-pov-ray-c1e2e1b8` | mini-SWE-agent | false | 57 | source-valid | miniswe-message-trajectory; 57 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-stp-23b2a67b` | mini-SWE-agent | false | 51 | source-valid | miniswe-message-trajectory; 51 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-tcc-qemu-3a1b805e` | mini-SWE-agent | false | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-cancel-async-tasks-c4880238` | mini-SWE-agent | false | 13 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 13 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-cartpole-rl-training-77f68671` | mini-SWE-agent | false | 17 | excluded | miniswe-agent-log-markers emitted 25 operations; public step_count is 17 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-catch-me-if-you-can-24c22254` | mini-SWE-agent | true | 15 | excluded | miniswe-agent-log-markers emitted 20 operations; public step_count is 15 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-causal-inference-r-7355552e` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-chem-property-targeting-8ff9ebfd` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-chem-rf-2e80b543` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-chess-best-move-07c1b01e` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-circuit-fibsqrt-8e83f40c` | mini-SWE-agent | false | 54 | source-valid | miniswe-message-trajectory; 54 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-cobol-modernization-0459679d` | mini-SWE-agent | false | 28 | source-valid | miniswe-message-trajectory; 28 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-compile-compcert-997ae681` | mini-SWE-agent | false | 73 | excluded | miniswe-agent-log-markers emitted 72 operations; public step_count is 73 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-configure-git-webserver-03fd1e23` | mini-SWE-agent | true | 17 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 17 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-constraints-scheduling-856bd634` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-count-dataset-tokens-14c570cd` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-cpp-compatibility-5fc09a00` | mini-SWE-agent | true | 13 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 13 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-crack-7z-hash-6657a30e` | mini-SWE-agent | true | 44 | source-valid | miniswe-message-trajectory; 44 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-create-bucket-d914eff2` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-cron-broken-network-e82a5c2f` | mini-SWE-agent | false | 37 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 37 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-cross-entropy-method-85748a7e` | mini-SWE-agent | true | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-custom-memory-heap-crash-af9a130a` | mini-SWE-agent | true | 14 | excluded | MiniSWE archive has neither sessions/agent.log nor .traj.json |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-db-wal-recovery-34e05b5b` | mini-SWE-agent | false | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-deterministic-tarball-1853a607` | mini-SWE-agent | true | 41 | source-valid | miniswe-message-trajectory; 41 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-distribution-search-faea2e28` | mini-SWE-agent | false | 27 | source-valid | miniswe-message-trajectory; 27 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-dna-insert-3d3baf3a` | mini-SWE-agent | false | 23 | excluded | miniswe-agent-log-markers emitted 8 operations; public step_count is 23 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-download-youtube-1e1335c3` | mini-SWE-agent | false | 23 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 23 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-extract-elf-447def22` | mini-SWE-agent | false | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-extract-moves-from-video-0327731c` | mini-SWE-agent | false | 28 | source-valid | miniswe-message-trajectory; 28 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-feal-differential-cryptanalysis-c6a0e7f0` | mini-SWE-agent | false | 35 | excluded | miniswe-agent-log-markers emitted 18 operations; public step_count is 35 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-fibonacci-server-2eb157ec` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-filter-js-from-html-3fefcec2` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-financial-document-processor-7fa7444b` | mini-SWE-agent | false | 15 | excluded | miniswe-agent-log-markers emitted 14 operations; public step_count is 15 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-find-official-code-cb546a81` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-find-restaurant-ad045946` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-fix-code-vulnerability-c2cb504b` | mini-SWE-agent | false | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-fix-git-8c82be40` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-fix-ocaml-gc-29624b4f` | mini-SWE-agent | false | 49 | source-valid | miniswe-message-trajectory; 49 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-flood-monitoring-basic-fd61692c` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-form-filling-05ac2124` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-gcc-compiler-optimization-1be92c65` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-gcode-to-text-62d201cd` | mini-SWE-agent | false | 14 | source-valid | miniswe-agent-log-markers; 14 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-get-bitcoin-nodes-8cc01e86` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-git-leak-recovery-8d7ea135` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-git-multibranch-10cdb210` | mini-SWE-agent | true | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-git-workflow-hack-15e07e43` | mini-SWE-agent | true | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-gpt2-codegolf-cf06bae2` | mini-SWE-agent | false | 32 | source-valid | miniswe-message-trajectory; 32 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-grid-pattern-transform-5f5e8f62` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-hf-lora-adapter-019612de` | mini-SWE-agent | false | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-hf-model-inference-f200d460` | mini-SWE-agent | true | 34 | excluded | miniswe-agent-log-markers emitted 27 operations; public step_count is 34 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-hf-train-lora-adapter-2d013ce9` | mini-SWE-agent | false | 29 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 29 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-home-server-https-230d4efc` | mini-SWE-agent | true | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-implement-eigenvectors-from-eigenvalues-research-paper-7ecc5fed` | mini-SWE-agent | false | 28 | source-valid | miniswe-message-trajectory; 28 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-install-windows-3.11-cfba53a2` | mini-SWE-agent | false | 38 | source-valid | miniswe-message-trajectory; 38 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-install-windows-xp-edd35096` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-interactive-maze-game-2077ac78` | mini-SWE-agent | false | 18 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 18 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-intrusion-detection-e9ebbc2c` | mini-SWE-agent | true | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-jq-data-processing-fb41cd0f` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-jupyter-notebook-server-f7fce821` | mini-SWE-agent | true | 27 | excluded | miniswe-agent-log-markers emitted 37 operations; public step_count is 27 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-kv-store-grpc-3ae7fe67` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-large-scale-text-editing-e70ac842` | mini-SWE-agent | false | 21 | excluded | miniswe-agent-log-markers emitted 18 operations; public step_count is 21 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-largest-eigenval-394d5897` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-leelachess0-pytorch-conversion-48a26c7a` | mini-SWE-agent | false | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-llm-inference-batching-scheduler-8929b713` | mini-SWE-agent | false | 31 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 31 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-llm-spec-decoding-b474b28b` | mini-SWE-agent | false | 23 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 23 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-mahjong-winninghand-3d297863` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-mcmc-sampling-stan-acd7e20e` | mini-SWE-agent | false | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-merge-diff-arc-agi-task-dab7c1f1` | mini-SWE-agent | false | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-mlflow-register-60a717c0` | mini-SWE-agent | true | 21 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 21 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-modernize-fortran-build-9f3882bb` | mini-SWE-agent | true | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-modernize-scientific-stack-65a4bc62` | mini-SWE-agent | true | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-movie-helper-3545dfb4` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-mteb-eval-d047e655` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-mteb-leaderboard-f8e86695` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-mteb-retrieve-6b8a886b` | mini-SWE-agent | false | 31 | source-valid | miniswe-message-trajectory; 31 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-multi-source-data-merger-282f4ff4` | mini-SWE-agent | true | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-multistep-definite-integral-59af2836` | mini-SWE-agent | true | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-neuron-to-jaxley-conversion-87200f19` | mini-SWE-agent | false | 26 | source-valid | miniswe-message-trajectory; 26 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-nginx-request-logging-d25b5dd9` | mini-SWE-agent | false | 22 | excluded | miniswe-agent-log-markers emitted 15 operations; public step_count is 22 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-npm-conflict-resolution-f2c511db` | mini-SWE-agent | false | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-ode-solver-rk4-65104b3b` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-oom-7dcdc1ab` | mini-SWE-agent | false | 15 | excluded | miniswe-agent-log-markers emitted 18 operations; public step_count is 15 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-openssl-selfsigned-cert-066836cb` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-optimal-transport-c1899dad` | mini-SWE-agent | true | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-organization-json-generator-3639b4e1` | mini-SWE-agent | true | 12 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 12 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-pandas-etl-656e1fab` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-parallel-particle-simulator-1f9b1eea` | mini-SWE-agent | false | 19 | excluded | miniswe-agent-log-markers emitted 17 operations; public step_count is 19 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-parallelize-compute-squares-307af33e` | mini-SWE-agent | true | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-parallelize-graph-41ae5c93` | mini-SWE-agent | true | 30 | source-valid | miniswe-message-trajectory; 30 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-password-recovery-65e3232c` | mini-SWE-agent | true | 17 | excluded | miniswe-agent-log-markers emitted 29 operations; public step_count is 17 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-path-tracing-79ade2b0` | mini-SWE-agent | false | 47 | source-valid | miniswe-message-trajectory; 47 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-path-tracing-reverse-039912bf` | mini-SWE-agent | false | 35 | source-valid | miniswe-message-trajectory; 35 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-play-lord-bc34dde4` | mini-SWE-agent | true | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-play-zork-34879dd5` | mini-SWE-agent | false | 17 | excluded | miniswe-agent-log-markers emitted 13 operations; public step_count is 17 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-play-zork-easy-8c77a548` | mini-SWE-agent | false | 33 | excluded | miniswe-agent-log-markers emitted 14 operations; public step_count is 33 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-portfolio-optimization-8f1e8fb0` | mini-SWE-agent | true | 26 | source-valid | miniswe-message-trajectory; 26 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-postgres-csv-clean-f7b1415b` | mini-SWE-agent | false | 32 | source-valid | miniswe-message-trajectory; 32 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-processing-pipeline-f1d685ac` | mini-SWE-agent | true | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-protein-assembly-c3a439fa` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-prove-plus-comm-b9caeff2` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-puzzle-solver-fd69ee4f` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-pytorch-model-cli-1a764f1f` | mini-SWE-agent | false | 21 | excluded | miniswe-agent-log-markers emitted 39 operations; public step_count is 21 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-pytorch-model-recovery-fbf3001a` | mini-SWE-agent | false | 20 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 20 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-query-optimize-8cb16f94` | mini-SWE-agent | true | 17 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 17 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-raman-fitting-a50296e9` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-rare-mineral-allocation-e2a39388` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-recover-obfuscated-files-341e38ed` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-regex-chess-a83c78d9` | mini-SWE-agent | false | 39 | source-valid | miniswe-message-trajectory; 39 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-regex-log-c987e17b` | mini-SWE-agent | true | 21 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 21 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-reshard-c4-data-f4ff7301` | mini-SWE-agent | true | 43 | source-valid | miniswe-message-trajectory; 43 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-reverse-engineering-770973e3` | mini-SWE-agent | false | 38 | source-valid | miniswe-message-trajectory; 38 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-rstan-to-pystan-6bdccdda` | mini-SWE-agent | false | 38 | source-valid | miniswe-message-trajectory; 38 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-run-pdp11-code-ba499e4b` | mini-SWE-agent | false | 31 | source-valid | miniswe-message-trajectory; 31 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-sam-cell-seg-93dae667` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-sanitize-git-repo-8cc3539b` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-schedule-vacation-1881b46f` | mini-SWE-agent | true | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-schemelike-metacircular-eval-1494da6d` | mini-SWE-agent | false | 64 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 64 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-security-celery-redis-rce-1b5605f8` | mini-SWE-agent | true | 34 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 34 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-setup-custom-dev-env-534cdad2` | mini-SWE-agent | true | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-simple-sheets-put-f60a0568` | mini-SWE-agent | false | 15 | excluded | MiniSWE archive has neither sessions/agent.log nor .traj.json |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-solana-data-72de38cf` | mini-SWE-agent | false | 35 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 35 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-solve-maze-challenge-db1ffbff` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-solve-sudoku-e694862a` | mini-SWE-agent | false | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-sparql-university-c611d3af` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-speech-to-text-52bfba5b` | mini-SWE-agent | false | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-spinning-up-rl-c435941e` | mini-SWE-agent | false | 64 | source-valid | miniswe-message-trajectory; 64 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-sql-injection-attack-dc0ecfcf` | mini-SWE-agent | true | 14 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-sqlite-db-truncate-05cee64c` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-stable-parallel-kmeans-a1318efd` | mini-SWE-agent | true | 32 | excluded | miniswe-agent-log-markers emitted 4 operations; public step_count is 32 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-tmux-advanced-workflow-04e67d90` | mini-SWE-agent | false | 33 | excluded | miniswe-agent-log-markers emitted 1 operations; public step_count is 33 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-torch-pipeline-parallelism-78788704` | mini-SWE-agent | false | 14 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-torch-tensor-parallelism-b913e37a` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-train-bpe-tokenizer-2df9c860` | mini-SWE-agent | true | 28 | source-valid | miniswe-message-trajectory; 28 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-train-fasttext-36447b26` | mini-SWE-agent | false | 28 | source-valid | miniswe-message-trajectory; 28 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-tree-directory-parser-ff5d17ce` | mini-SWE-agent | true | 41 | source-valid | miniswe-message-trajectory; 41 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-triton-interpret-5d494583` | mini-SWE-agent | false | 17 | excluded | miniswe-agent-log-markers emitted 37 operations; public step_count is 17 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-vertex-solver-52cbd37b` | mini-SWE-agent | false | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-video-processing-cb1c1f14` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-vimscript-vim-quine-48a8120f` | mini-SWE-agent | true | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-vul-flask-4946dda9` | mini-SWE-agent | false | 36 | source-valid | miniswe-message-trajectory; 36 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-vul-flink-4cffe0d9` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-vulnerable-secret-d6426d57` | mini-SWE-agent | true | 25 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 25 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-weighted-max-sat-solver-93a49e03` | mini-SWE-agent | false | 15 | excluded | miniswe-agent-log-markers emitted 16 operations; public step_count is 15 |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-winning-avg-corewars-8c43afa1` | mini-SWE-agent | false | 66 | source-valid | miniswe-message-trajectory; 66 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-word2vec-from-scratch-7aab3a5c` | mini-SWE-agent | false | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-write-compressor-9fff4fee` | mini-SWE-agent | false | 44 | source-valid | miniswe-message-trajectory; 44 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-add-benchmark-lm-eval-harness-35a0aaae` | mini-SWE-agent | false | 16 | excluded | miniswe-message-trajectory emitted 19 operations; public step_count is 16 |
| `miniswe-DeepSeek__DeepSeek-V3.2-add-benchmark-lm-eval-harness-c3da1ca5` | mini-SWE-agent | false | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-ancient-puzzle-b9a801ee` | mini-SWE-agent | true | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-ancient-puzzle-c925a84b` | mini-SWE-agent | true | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-audio-synth-stft-peaks-3191db3b` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-audio-synth-stft-peaks-b418dbb8` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-blind-maze-explorer-5x5-0395a331` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-blind-maze-explorer-5x5-735bcb5e` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-blind-maze-explorer-algorithm-87efaf15` | mini-SWE-agent | false | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-blind-maze-explorer-algorithm-dde55ea2` | mini-SWE-agent | false | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-break-filter-js-from-html-99347335` | mini-SWE-agent | false | 17 | excluded | miniswe-message-trajectory emitted 13 operations; public step_count is 17 |
| `miniswe-DeepSeek__DeepSeek-V3.2-break-filter-js-from-html-df091bd8` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-build-cython-ext-3334a181` | mini-SWE-agent | false | 28 | source-valid | miniswe-message-trajectory; 28 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-build-cython-ext-72d231f6` | mini-SWE-agent | false | 28 | source-valid | miniswe-message-trajectory; 28 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-build-initramfs-qemu-da062aa5` | mini-SWE-agent | false | 35 | source-valid | miniswe-message-trajectory; 35 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-build-linux-kernel-qemu-df926afe` | mini-SWE-agent | false | 14 | excluded | miniswe-message-trajectory emitted 31 operations; public step_count is 14 |
| `miniswe-DeepSeek__DeepSeek-V3.2-build-linux-kernel-qemu-ea803cf1` | mini-SWE-agent | false | 31 | source-valid | miniswe-message-trajectory; 31 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-build-pmars-7018dca2` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-build-pov-ray-2cc77232` | mini-SWE-agent | false | 29 | source-valid | miniswe-message-trajectory; 29 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-build-pov-ray-66191bae` | mini-SWE-agent | false | 14 | excluded | miniswe-message-trajectory emitted 29 operations; public step_count is 14 |
| `miniswe-DeepSeek__DeepSeek-V3.2-build-tcc-qemu-ac321de2` | mini-SWE-agent | false | 12 | excluded | miniswe-agent-log-markers emitted 23 operations; public step_count is 12 |
| `miniswe-DeepSeek__DeepSeek-V3.2-build-tcc-qemu-d23b9a67` | mini-SWE-agent | false | 12 | excluded | miniswe-agent-log-markers emitted 23 operations; public step_count is 12 |
| `miniswe-DeepSeek__DeepSeek-V3.2-caffe-cifar-10-348f97db` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-caffe-cifar-10-79411964` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-cancel-async-tasks-0e4b232f` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-cartpole-rl-training-74a92a16` | mini-SWE-agent | false | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-cartpole-rl-training-fec5f97e` | mini-SWE-agent | false | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-catch-me-if-you-can-31060225` | mini-SWE-agent | false | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-catch-me-if-you-can-a37bf129` | mini-SWE-agent | false | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-causal-inference-r-6f75c277` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-causal-inference-r-f74c0978` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-chem-rf-4d66ae93` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-chess-best-move-835ae9c2` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-circuit-fibsqrt-3ae54c86` | mini-SWE-agent | false | 32 | excluded | miniswe-message-trajectory emitted 47 operations; public step_count is 32 |
| `miniswe-DeepSeek__DeepSeek-V3.2-circuit-fibsqrt-3dd7855d` | mini-SWE-agent | false | 47 | source-valid | miniswe-message-trajectory; 47 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-cobol-modernization-2a74ac55` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-cobol-modernization-cf4612ec` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-code-from-image-5149720a` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-conda-env-conflict-resolution-9f616e70` | mini-SWE-agent | false | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-configure-git-webserver-957822b2` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-count-dataset-tokens-10dd91da` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-count-dataset-tokens-fe2023df` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-cpp-compatibility-e83cff9f` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-crack-7z-hash-4808f20e` | mini-SWE-agent | true | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-cron-broken-network-c02d5c8b` | mini-SWE-agent | false | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-cross-entropy-method-19fbcf2e` | mini-SWE-agent | false | 13 | excluded | miniswe-message-trajectory emitted 28 operations; public step_count is 13 |
| `miniswe-DeepSeek__DeepSeek-V3.2-cross-entropy-method-2b0ae0fc` | mini-SWE-agent | true | 28 | source-valid | miniswe-message-trajectory; 28 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-custom-memory-heap-crash-06a7b754` | mini-SWE-agent | false | 33 | source-valid | miniswe-message-trajectory; 33 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-custom-memory-heap-crash-b8226b63` | mini-SWE-agent | false | 11 | excluded | miniswe-message-trajectory emitted 33 operations; public step_count is 11 |
| `miniswe-DeepSeek__DeepSeek-V3.2-db-wal-recovery-24490912` | mini-SWE-agent | false | 11 | excluded | miniswe-message-trajectory emitted 37 operations; public step_count is 11 |
| `miniswe-DeepSeek__DeepSeek-V3.2-db-wal-recovery-92bbb058` | mini-SWE-agent | false | 37 | source-valid | miniswe-message-trajectory; 37 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-debug-long-program-999b9a02` | mini-SWE-agent | true | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-debug-long-program-f9874650` | mini-SWE-agent | true | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-distribution-search-76ea481c` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-distribution-search-b39e2f10` | mini-SWE-agent | false | 13 | excluded | miniswe-message-trajectory emitted 14 operations; public step_count is 13 |
| `miniswe-DeepSeek__DeepSeek-V3.2-dna-assembly-28aeea16` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-dna-insert-b5c6c010` | mini-SWE-agent | false | 14 | excluded | miniswe-message-trajectory emitted 13 operations; public step_count is 14 |
| `miniswe-DeepSeek__DeepSeek-V3.2-dna-insert-f99cc644` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-download-youtube-10de49b9` | mini-SWE-agent | true | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-extract-elf-437a4569` | mini-SWE-agent | true | 39 | source-valid | miniswe-message-trajectory; 39 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-extract-moves-from-video-1ac54a42` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-extract-safely-62b333e7` | mini-SWE-agent | true | 11 | excluded | miniswe-message-trajectory emitted 4 operations; public step_count is 11 |
| `miniswe-DeepSeek__DeepSeek-V3.2-feal-linear-cryptanalysis-a513025a` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-feal-linear-cryptanalysis-dc150fab` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-find-restaurant-c33e1a55` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-find-restaurant-f6481263` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-fix-code-vulnerability-8ba292b0` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-fix-code-vulnerability-d8277a33` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-fix-git-24be3f2d` | mini-SWE-agent | true | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-fix-ocaml-gc-2299ab4a` | mini-SWE-agent | false | 72 | source-valid | miniswe-message-trajectory; 72 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-fix-ocaml-gc-286cffb1` | mini-SWE-agent | false | 34 | excluded | miniswe-message-trajectory emitted 72 operations; public step_count is 34 |
| `miniswe-DeepSeek__DeepSeek-V3.2-fmri-encoding-r-8ae60b03` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-fmri-encoding-r-bf25d6d8` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-form-filling-14555c66` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-form-filling-7d2a7344` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-gcc-compiler-optimization-edc0a195` | mini-SWE-agent | true | 12 | excluded | miniswe-message-trajectory emitted 10 operations; public step_count is 12 |
| `miniswe-DeepSeek__DeepSeek-V3.2-get-bitcoin-nodes-0b298dee` | mini-SWE-agent | false | 27 | source-valid | miniswe-message-trajectory; 27 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-get-bitcoin-nodes-6004dfc9` | mini-SWE-agent | false | 27 | source-valid | miniswe-message-trajectory; 27 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-git-multibranch-a21225e1` | mini-SWE-agent | true | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-git-workflow-hack-e602a230` | mini-SWE-agent | true | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-git-workflow-hack-e9ae971f` | mini-SWE-agent | false | 16 | excluded | miniswe-message-trajectory emitted 25 operations; public step_count is 16 |
| `miniswe-DeepSeek__DeepSeek-V3.2-gomoku-planner-138c71cb` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-gpt2-codegolf-0218a6f5` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-heterogeneous-dates-09b219cb` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-hf-lora-adapter-f46ef20a` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-hf-lora-adapter-ff04189f` | mini-SWE-agent | false | 32 | excluded | miniswe-message-trajectory emitted 20 operations; public step_count is 32 |
| `miniswe-DeepSeek__DeepSeek-V3.2-hf-train-lora-adapter-e5fc2c36` | mini-SWE-agent | false | 13 | excluded | miniswe-message-trajectory emitted 18 operations; public step_count is 13 |
| `miniswe-DeepSeek__DeepSeek-V3.2-hf-train-lora-adapter-fc66ca6d` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-home-server-https-0171b2b6` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-html-finance-verify-e48d958c` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-implement-eigenvectors-from-eigenvalues-research-paper-6c3600d7` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-implement-eigenvectors-from-eigenvalues-research-paper-cd53ceef` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-incompatible-python-fasttext-c6dc9898` | mini-SWE-agent | false | 12 | excluded | miniswe-message-trajectory emitted 10 operations; public step_count is 12 |
| `miniswe-DeepSeek__DeepSeek-V3.2-install-klee-minimal-4b8b99db` | mini-SWE-agent | true | 29 | source-valid | miniswe-message-trajectory; 29 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-install-klee-minimal-776b2140` | mini-SWE-agent | true | 29 | source-valid | miniswe-message-trajectory; 29 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-install-windows-3.11-464e6a23` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-install-windows-xp-6bd7645b` | mini-SWE-agent | false | 49 | source-valid | miniswe-message-trajectory; 49 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-interactive-maze-game-40d2a8b0` | mini-SWE-agent | false | 22 | excluded | miniswe-message-trajectory emitted 33 operations; public step_count is 22 |
| `miniswe-DeepSeek__DeepSeek-V3.2-interactive-maze-game-c2f429d0` | mini-SWE-agent | false | 33 | source-valid | miniswe-message-trajectory; 33 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-intrusion-detection-26134c3b` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-jupyter-notebook-server-f573deb2` | mini-SWE-agent | true | 35 | source-valid | miniswe-message-trajectory; 35 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-large-scale-text-editing-3f4a448a` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-large-scale-text-editing-e839c8f8` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-largest-eigenval-09316b7f` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-largest-eigenval-fdc3317b` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-lean4-proof-55ec9946` | mini-SWE-agent | false | 24 | excluded | miniswe-message-trajectory emitted 42 operations; public step_count is 24 |
| `miniswe-DeepSeek__DeepSeek-V3.2-lean4-proof-bd0e040f` | mini-SWE-agent | false | 42 | source-valid | miniswe-message-trajectory; 42 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-leelachess0-pytorch-conversion-108347f0` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-llm-inference-batching-scheduler-17e7232c` | mini-SWE-agent | false | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-llm-inference-batching-scheduler-66dad47d` | mini-SWE-agent | false | 15 | excluded | miniswe-message-trajectory emitted 25 operations; public step_count is 15 |
| `miniswe-DeepSeek__DeepSeek-V3.2-llm-spec-decoding-2c5a97c1` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-llm-spec-decoding-bd4e753d` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-log-summary-date-ranges-4ccdcaf1` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-mailman-18d98d50` | mini-SWE-agent | false | 36 | source-valid | miniswe-message-trajectory; 36 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-mailman-e88b3f02` | mini-SWE-agent | false | 30 | excluded | miniswe-message-trajectory emitted 36 operations; public step_count is 30 |
| `miniswe-DeepSeek__DeepSeek-V3.2-make-doom-for-mips-07db6de2` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-make-doom-for-mips-c4c20893` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-mcmc-sampling-stan-12431b52` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-mcmc-sampling-stan-512b09d6` | mini-SWE-agent | false | 13 | excluded | miniswe-message-trajectory emitted 20 operations; public step_count is 13 |
| `miniswe-DeepSeek__DeepSeek-V3.2-merge-diff-arc-agi-task-cb5aafdd` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-mlflow-register-0c3275c5` | mini-SWE-agent | false | 15 | excluded | miniswe-message-trajectory emitted 16 operations; public step_count is 15 |
| `miniswe-DeepSeek__DeepSeek-V3.2-mlflow-register-c17092a7` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-modernize-fortran-build-ce869de7` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-modernize-fortran-build-d3685a74` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-mteb-eval-a8cfc25f` | mini-SWE-agent | false | 23 | excluded | miniswe-message-trajectory emitted 24 operations; public step_count is 23 |
| `miniswe-DeepSeek__DeepSeek-V3.2-mteb-eval-de672501` | mini-SWE-agent | true | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-mteb-retrieve-994e0231` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-multi-source-data-merger-a6bc938c` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-multi-source-data-merger-f6193723` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-neuron-to-jaxley-conversion-7edc2e4f` | mini-SWE-agent | true | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-overfull-hbox-0b8f1875` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-overfull-hbox-80c597cc` | mini-SWE-agent | false | 13 | excluded | miniswe-message-trajectory emitted 14 operations; public step_count is 13 |
| `miniswe-DeepSeek__DeepSeek-V3.2-pandas-etl-bbcc3081` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-parallelize-compute-squares-6f4e431f` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-parallelize-graph-0bb5d5f1` | mini-SWE-agent | false | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-path-tracing-710cd772` | mini-SWE-agent | false | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-path-tracing-reverse-ec1b121a` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-play-lord-81efdc14` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-play-zork-c1cce947` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-play-zork-easy-484c4ce0` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-play-zork-easy-e5b382f3` | mini-SWE-agent | false | 19 | excluded | miniswe-message-trajectory emitted 16 operations; public step_count is 19 |
| `miniswe-DeepSeek__DeepSeek-V3.2-polyglot-rust-c-8d29970f` | mini-SWE-agent | false | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-polyglot-rust-c-f689845d` | mini-SWE-agent | false | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-port-compressor-4652dd99` | mini-SWE-agent | false | 68 | source-valid | miniswe-message-trajectory; 68 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-port-compressor-7ecd816a` | mini-SWE-agent | false | 26 | excluded | miniswe-message-trajectory emitted 68 operations; public step_count is 26 |
| `miniswe-DeepSeek__DeepSeek-V3.2-portfolio-optimization-c32c1a67` | mini-SWE-agent | true | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-portfolio-optimization-f0e6028e` | mini-SWE-agent | true | 12 | excluded | miniswe-message-trajectory emitted 21 operations; public step_count is 12 |
| `miniswe-DeepSeek__DeepSeek-V3.2-postgres-csv-clean-139bdc60` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-postgres-csv-clean-c5e20a68` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-predicate-pushdown-bench-9fa028c7` | mini-SWE-agent | false | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-processing-pipeline-805b0064` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-protein-assembly-472264a0` | mini-SWE-agent | false | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-puzzle-solver-db66bc18` | mini-SWE-agent | false | 17 | excluded | miniswe-message-trajectory emitted 12 operations; public step_count is 17 |
| `miniswe-DeepSeek__DeepSeek-V3.2-puzzle-solver-f531c139` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-pypi-server-790757c5` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-pypi-server-bedb7a8b` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-pytorch-model-cli-9d963d43` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-pytorch-model-cli-adb454c3` | mini-SWE-agent | false | 16 | excluded | miniswe-message-trajectory emitted 20 operations; public step_count is 16 |
| `miniswe-DeepSeek__DeepSeek-V3.2-pytorch-model-recovery-3c1cb101` | mini-SWE-agent | false | 37 | source-valid | miniswe-message-trajectory; 37 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-pytorch-model-recovery-4cbae484` | mini-SWE-agent | false | 26 | excluded | miniswe-message-trajectory emitted 37 operations; public step_count is 26 |
| `miniswe-DeepSeek__DeepSeek-V3.2-query-optimize-3b3e2297` | mini-SWE-agent | false | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-rare-mineral-allocation-159016d0` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-regex-chess-964f9582` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-regex-chess-f5b6bc44` | mini-SWE-agent | false | 22 | excluded | miniswe-message-trajectory emitted 14 operations; public step_count is 22 |
| `miniswe-DeepSeek__DeepSeek-V3.2-reshard-c4-data-7ddf0b5f` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-reverse-engineering-7a944da0` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-reverse-engineering-8a9af33e` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-rstan-to-pystan-593b26ef` | mini-SWE-agent | false | 19 | excluded | miniswe-message-trajectory emitted 55 operations; public step_count is 19 |
| `miniswe-DeepSeek__DeepSeek-V3.2-rstan-to-pystan-cdb0a9f8` | mini-SWE-agent | false | 55 | source-valid | miniswe-message-trajectory; 55 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-run-pdp11-code-e8ca5615` | mini-SWE-agent | false | 27 | source-valid | miniswe-message-trajectory; 27 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-sam-cell-seg-d2bb380f` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-schedule-vacation-bc933dc6` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-schemelike-metacircular-eval-e73a741e` | mini-SWE-agent | false | 49 | source-valid | miniswe-message-trajectory; 49 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-security-celery-redis-rce-2d0c8f4c` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-security-celery-redis-rce-e36630c2` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-setup-custom-dev-env-04d1e098` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-setup-custom-dev-env-7316d97b` | mini-SWE-agent | false | 14 | excluded | miniswe-message-trajectory emitted 18 operations; public step_count is 14 |
| `miniswe-DeepSeek__DeepSeek-V3.2-simple-sheets-put-919e5529` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-solve-maze-challenge-9087c485` | mini-SWE-agent | false | 34 | source-valid | miniswe-message-trajectory; 34 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-sparql-professors-universities-b89f4939` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-speech-to-text-311ea63c` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-speech-to-text-3b6a07af` | mini-SWE-agent | false | 19 | excluded | miniswe-message-trajectory emitted 15 operations; public step_count is 19 |
| `miniswe-DeepSeek__DeepSeek-V3.2-spinning-up-rl-9fc001cf` | mini-SWE-agent | false | 29 | excluded | miniswe-message-trajectory emitted 48 operations; public step_count is 29 |
| `miniswe-DeepSeek__DeepSeek-V3.2-spinning-up-rl-cce36699` | mini-SWE-agent | false | 48 | source-valid | miniswe-message-trajectory; 48 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-spring-messaging-vul-07893fe0` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-spring-messaging-vul-9b880632` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-sql-injection-attack-3bd43d11` | mini-SWE-agent | true | 14 | excluded | miniswe-message-trajectory emitted 19 operations; public step_count is 14 |
| `miniswe-DeepSeek__DeepSeek-V3.2-sql-injection-attack-ca76548b` | mini-SWE-agent | true | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-sqlite-db-truncate-d4d8ae16` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-stable-parallel-kmeans-ca8f909a` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-tmux-advanced-workflow-56032728` | mini-SWE-agent | true | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-torch-pipeline-parallelism-e1425d5e` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-torch-tensor-parallelism-7b49577e` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-train-bpe-tokenizer-725ff31b` | mini-SWE-agent | false | 12 | excluded | miniswe-message-trajectory emitted 7 operations; public step_count is 12 |
| `miniswe-DeepSeek__DeepSeek-V3.2-train-fasttext-160a16df` | mini-SWE-agent | false | 31 | source-valid | miniswe-message-trajectory; 31 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-tree-directory-parser-2c40f814` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-tree-directory-parser-57804268` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-triton-interpret-52a96054` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-vertex-solver-90d6a09d` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-vul-flask-3411c879` | mini-SWE-agent | false | 11 | excluded | miniswe-message-trajectory emitted 46 operations; public step_count is 11 |
| `miniswe-DeepSeek__DeepSeek-V3.2-vul-flask-a496d591` | mini-SWE-agent | false | 46 | source-valid | miniswe-message-trajectory; 46 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-vul-flink-066a2f4f` | mini-SWE-agent | false | 33 | source-valid | miniswe-message-trajectory; 33 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-vul-flink-fc131438` | mini-SWE-agent | false | 16 | excluded | miniswe-message-trajectory emitted 33 operations; public step_count is 16 |
| `miniswe-DeepSeek__DeepSeek-V3.2-vulnerable-secret-90d9e078` | mini-SWE-agent | true | 26 | source-valid | miniswe-message-trajectory; 26 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-weighted-max-sat-solver-a8cdf6de` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-winning-avg-corewars-a6552416` | mini-SWE-agent | false | 45 | source-valid | miniswe-message-trajectory; 45 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-winning-avg-corewars-f27ed260` | mini-SWE-agent | false | 21 | excluded | miniswe-message-trajectory emitted 45 operations; public step_count is 21 |
| `miniswe-DeepSeek__DeepSeek-V3.2-word2vec-from-scratch-75c0627c` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-DeepSeek__DeepSeek-V3.2-word2vec-from-scratch-dcff4c0c` | mini-SWE-agent | false | 21 | excluded | miniswe-message-trajectory emitted 15 operations; public step_count is 21 |
| `miniswe-DeepSeek__DeepSeek-V3.2-write-compressor-e9841d77` | mini-SWE-agent | false | 34 | source-valid | miniswe-message-trajectory; 34 operations |
| `miniswe-DeepSeek__DeepSeekChat-add-benchmark-lm-eval-harness-e3e165f0` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-DeepSeek__DeepSeekChat-ancient-puzzle-3dba054d` | mini-SWE-agent | true | 21 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 21 |
| `miniswe-DeepSeek__DeepSeekChat-ancient-puzzle-c173e669` | mini-SWE-agent | true | 21 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 21 |
| `miniswe-DeepSeek__DeepSeekChat-blind-maze-explorer-5x5-9dc87864` | mini-SWE-agent | false | 15 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 15 |
| `miniswe-DeepSeek__DeepSeekChat-blind-maze-explorer-5x5-ab3f279a` | mini-SWE-agent | false | 15 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 15 |
| `miniswe-DeepSeek__DeepSeekChat-blind-maze-explorer-algorithm-04e49465` | mini-SWE-agent | false | 22 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 22 |
| `miniswe-DeepSeek__DeepSeekChat-blind-maze-explorer-algorithm-3e876d5a` | mini-SWE-agent | false | 22 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 22 |
| `miniswe-DeepSeek__DeepSeekChat-break-filter-js-from-html-a8b91090` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-DeepSeek__DeepSeekChat-build-linux-kernel-qemu-74b06aac` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeekChat-build-pov-ray-b4b15e7b` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeekChat-build-tcc-qemu-2a538e85` | mini-SWE-agent | false | 12 | excluded | miniswe-agent-log-markers emitted 11 operations; public step_count is 12 |
| `miniswe-DeepSeek__DeepSeekChat-caffe-cifar-10-7c7e1b74` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeekChat-caffe-cifar-10-fa2c11de` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeekChat-cartpole-rl-training-2a8bad58` | mini-SWE-agent | false | 24 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 24 |
| `miniswe-DeepSeek__DeepSeekChat-cartpole-rl-training-9b589fe6` | mini-SWE-agent | false | 24 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 24 |
| `miniswe-DeepSeek__DeepSeekChat-catch-me-if-you-can-25943bc2` | mini-SWE-agent | false | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-DeepSeek__DeepSeekChat-catch-me-if-you-can-c2f596b5` | mini-SWE-agent | false | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-DeepSeek__DeepSeekChat-causal-inference-r-494a4bc2` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-DeepSeek__DeepSeekChat-causal-inference-r-77fcb803` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-DeepSeek__DeepSeekChat-circuit-fibsqrt-953b70e2` | mini-SWE-agent | false | 32 | source-valid | miniswe-message-trajectory; 32 operations |
| `miniswe-DeepSeek__DeepSeekChat-cobol-modernization-142e251d` | mini-SWE-agent | false | 12 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 12 |
| `miniswe-DeepSeek__DeepSeekChat-cobol-modernization-efb71f66` | mini-SWE-agent | false | 12 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 12 |
| `miniswe-DeepSeek__DeepSeekChat-cross-entropy-method-987b21c4` | mini-SWE-agent | false | 13 | excluded | miniswe-agent-log-markers emitted 9 operations; public step_count is 13 |
| `miniswe-DeepSeek__DeepSeekChat-custom-memory-heap-crash-2c9afcbe` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-DeepSeek__DeepSeekChat-db-wal-recovery-e643e6f2` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-DeepSeek__DeepSeekChat-debug-long-program-a52871bc` | mini-SWE-agent | true | 13 | excluded | miniswe-agent-log-markers emitted 25 operations; public step_count is 13 |
| `miniswe-DeepSeek__DeepSeekChat-debug-long-program-d7fe2717` | mini-SWE-agent | true | 13 | excluded | miniswe-agent-log-markers emitted 25 operations; public step_count is 13 |
| `miniswe-DeepSeek__DeepSeekChat-distribution-search-f66ab8a4` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-DeepSeek__DeepSeekChat-dna-insert-df6dbf9c` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeekChat-extract-safely-02c0f9f1` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-DeepSeek__DeepSeekChat-feal-linear-cryptanalysis-59116f41` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-DeepSeek__DeepSeekChat-feal-linear-cryptanalysis-d77c94c6` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-DeepSeek__DeepSeekChat-find-restaurant-7a8a0211` | mini-SWE-agent | false | 14 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| `miniswe-DeepSeek__DeepSeekChat-find-restaurant-91dd9c38` | mini-SWE-agent | false | 14 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| `miniswe-DeepSeek__DeepSeekChat-fix-code-vulnerability-b4a58358` | mini-SWE-agent | false | 14 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| `miniswe-DeepSeek__DeepSeekChat-fix-code-vulnerability-d05efcab` | mini-SWE-agent | false | 14 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| `miniswe-DeepSeek__DeepSeekChat-fix-ocaml-gc-c786c6e9` | mini-SWE-agent | false | 34 | source-valid | miniswe-message-trajectory; 34 operations |
| `miniswe-DeepSeek__DeepSeekChat-fmri-encoding-r-20d4adc5` | mini-SWE-agent | false | 16 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 16 |
| `miniswe-DeepSeek__DeepSeekChat-fmri-encoding-r-52a7fd94` | mini-SWE-agent | false | 16 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 16 |
| `miniswe-DeepSeek__DeepSeekChat-form-filling-02dfa512` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-DeepSeek__DeepSeekChat-form-filling-23d4b717` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-DeepSeek__DeepSeekChat-gcc-compiler-optimization-59e94daa` | mini-SWE-agent | true | 12 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 12 |
| `miniswe-DeepSeek__DeepSeekChat-get-bitcoin-nodes-6f60903f` | mini-SWE-agent | false | 27 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 27 |
| `miniswe-DeepSeek__DeepSeekChat-get-bitcoin-nodes-77201508` | mini-SWE-agent | false | 27 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 27 |
| `miniswe-DeepSeek__DeepSeekChat-git-workflow-hack-dafabade` | mini-SWE-agent | false | 16 | excluded | miniswe-agent-log-markers emitted 1 operations; public step_count is 16 |
| `miniswe-DeepSeek__DeepSeekChat-hf-lora-adapter-4fb847a0` | mini-SWE-agent | false | 32 | source-valid | miniswe-message-trajectory; 32 operations |
| `miniswe-DeepSeek__DeepSeekChat-hf-train-lora-adapter-8e9b2571` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-DeepSeek__DeepSeekChat-implement-eigenvectors-from-eigenvalues-research-paper-152a90ed` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeekChat-implement-eigenvectors-from-eigenvalues-research-paper-d49d5d1a` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeekChat-incompatible-python-fasttext-a5cba243` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-DeepSeek__DeepSeekChat-install-klee-minimal-225e6a40` | mini-SWE-agent | true | 29 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 29 |
| `miniswe-DeepSeek__DeepSeekChat-install-klee-minimal-aad4e3ec` | mini-SWE-agent | true | 29 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 29 |
| `miniswe-DeepSeek__DeepSeekChat-interactive-maze-game-cf200f70` | mini-SWE-agent | false | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-DeepSeek__DeepSeekChat-jupyter-notebook-server-de388ec1` | mini-SWE-agent | true | 35 | excluded | miniswe-agent-log-markers emitted 1 operations; public step_count is 35 |
| `miniswe-DeepSeek__DeepSeekChat-large-scale-text-editing-10d7a5e4` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-DeepSeek__DeepSeekChat-large-scale-text-editing-5f472528` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-DeepSeek__DeepSeekChat-largest-eigenval-e23abef2` | mini-SWE-agent | false | 15 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 15 |
| `miniswe-DeepSeek__DeepSeekChat-largest-eigenval-ed827f6e` | mini-SWE-agent | false | 15 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 15 |
| `miniswe-DeepSeek__DeepSeekChat-lean4-proof-18a37ae2` | mini-SWE-agent | false | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-DeepSeek__DeepSeekChat-llm-inference-batching-scheduler-bed49200` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-DeepSeek__DeepSeekChat-llm-spec-decoding-a00c0e63` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-DeepSeek__DeepSeekChat-llm-spec-decoding-a85a2dd6` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-DeepSeek__DeepSeekChat-mailman-5cd1406d` | mini-SWE-agent | false | 30 | source-valid | miniswe-message-trajectory; 30 operations |
| `miniswe-DeepSeek__DeepSeekChat-make-doom-for-mips-4d05c361` | mini-SWE-agent | false | 18 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 18 |
| `miniswe-DeepSeek__DeepSeekChat-make-doom-for-mips-b5da9484` | mini-SWE-agent | false | 18 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 18 |
| `miniswe-DeepSeek__DeepSeekChat-mcmc-sampling-stan-8f7e5f5f` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-DeepSeek__DeepSeekChat-mlflow-register-25d31337` | mini-SWE-agent | false | 15 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 15 |
| `miniswe-DeepSeek__DeepSeekChat-mteb-eval-5fa7d823` | mini-SWE-agent | false | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-DeepSeek__DeepSeekChat-multi-source-data-merger-49678a65` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-DeepSeek__DeepSeekChat-overfull-hbox-4525b1ce` | mini-SWE-agent | false | 13 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 13 |
| `miniswe-DeepSeek__DeepSeekChat-play-zork-easy-2500707c` | mini-SWE-agent | false | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-DeepSeek__DeepSeekChat-polyglot-rust-c-91adfd30` | mini-SWE-agent | false | 23 | excluded | miniswe-agent-log-markers emitted 13 operations; public step_count is 23 |
| `miniswe-DeepSeek__DeepSeekChat-polyglot-rust-c-a4e6aa34` | mini-SWE-agent | false | 23 | excluded | miniswe-agent-log-markers emitted 13 operations; public step_count is 23 |
| `miniswe-DeepSeek__DeepSeekChat-port-compressor-c2412e3e` | mini-SWE-agent | false | 26 | source-valid | miniswe-message-trajectory; 26 operations |
| `miniswe-DeepSeek__DeepSeekChat-portfolio-optimization-de743bf9` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-DeepSeek__DeepSeekChat-postgres-csv-clean-09c82bf0` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-DeepSeek__DeepSeekChat-postgres-csv-clean-71428465` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-DeepSeek__DeepSeekChat-puzzle-solver-d305021c` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-DeepSeek__DeepSeekChat-pypi-server-4160641e` | mini-SWE-agent | false | 17 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 17 |
| `miniswe-DeepSeek__DeepSeekChat-pypi-server-b34f9661` | mini-SWE-agent | false | 17 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 17 |
| `miniswe-DeepSeek__DeepSeekChat-pytorch-model-cli-da3c268e` | mini-SWE-agent | false | 16 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 16 |
| `miniswe-DeepSeek__DeepSeekChat-pytorch-model-recovery-a152df9c` | mini-SWE-agent | false | 26 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 26 |
| `miniswe-DeepSeek__DeepSeekChat-regex-chess-057b06ba` | mini-SWE-agent | false | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-DeepSeek__DeepSeekChat-reverse-engineering-7544c06a` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-DeepSeek__DeepSeekChat-reverse-engineering-aa874141` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-DeepSeek__DeepSeekChat-rstan-to-pystan-1af47fcc` | mini-SWE-agent | false | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-DeepSeek__DeepSeekChat-security-celery-redis-rce-742366d3` | mini-SWE-agent | false | 13 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 13 |
| `miniswe-DeepSeek__DeepSeekChat-security-celery-redis-rce-b27381fd` | mini-SWE-agent | false | 13 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 13 |
| `miniswe-DeepSeek__DeepSeekChat-setup-custom-dev-env-e622ae5d` | mini-SWE-agent | false | 14 | excluded | miniswe-agent-log-markers emitted 25 operations; public step_count is 14 |
| `miniswe-DeepSeek__DeepSeekChat-simple-sheets-put-b4688b28` | mini-SWE-agent | false | 13 | excluded | MiniSWE archive has neither sessions/agent.log nor .traj.json |
| `miniswe-DeepSeek__DeepSeekChat-speech-to-text-915f6dfd` | mini-SWE-agent | false | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-DeepSeek__DeepSeekChat-spinning-up-rl-d5b13d86` | mini-SWE-agent | false | 29 | source-valid | miniswe-message-trajectory; 29 operations |
| `miniswe-DeepSeek__DeepSeekChat-spring-messaging-vul-6f155596` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeekChat-spring-messaging-vul-a4b7972f` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeekChat-sql-injection-attack-f0ab13fb` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-DeepSeek__DeepSeekChat-train-bpe-tokenizer-5f5fcd07` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-DeepSeek__DeepSeekChat-tree-directory-parser-55122583` | mini-SWE-agent | false | 17 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 17 |
| `miniswe-DeepSeek__DeepSeekChat-tree-directory-parser-d5952170` | mini-SWE-agent | false | 17 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 17 |
| `miniswe-DeepSeek__DeepSeekChat-vul-flask-852cec9a` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-DeepSeek__DeepSeekChat-vul-flink-eb6644e6` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-DeepSeek__DeepSeekChat-winning-avg-corewars-1bdb4b74` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-DeepSeek__DeepSeekChat-word2vec-from-scratch-17419983` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-Moonshot__Kimi-K2-250905-3d-model-format-legacy-84388bf1` | mini-SWE-agent | false | 78 | source-valid | miniswe-message-trajectory; 78 operations |
| `miniswe-Moonshot__Kimi-K2-250905-acl-permissions-inheritance-1b7c8724` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-Moonshot__Kimi-K2-250905-add-benchmark-lm-eval-harness-186cb670` | mini-SWE-agent | false | 56 | source-valid | miniswe-message-trajectory; 56 operations |
| `miniswe-Moonshot__Kimi-K2-250905-ancient-puzzle-ae4ad8ca` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-Moonshot__Kimi-K2-250905-assign-seats-d7217704` | mini-SWE-agent | true | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-Moonshot__Kimi-K2-250905-audio-synth-stft-peaks-75682a5f` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-Moonshot__Kimi-K2-250905-blind-maze-explorer-5x5-b9f24989` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-Moonshot__Kimi-K2-250905-blind-maze-explorer-algorithm-ba0320e9` | mini-SWE-agent | true | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-Moonshot__Kimi-K2-250905-bn-fit-modify-80f31587` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-Moonshot__Kimi-K2-250905-broken-python-e6824c92` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-Moonshot__Kimi-K2-250905-build-cython-ext-42be434d` | mini-SWE-agent | false | 39 | source-valid | miniswe-message-trajectory; 39 operations |
| `miniswe-Moonshot__Kimi-K2-250905-build-initramfs-qemu-5440bfe7` | mini-SWE-agent | false | 36 | source-valid | miniswe-message-trajectory; 36 operations |
| `miniswe-Moonshot__Kimi-K2-250905-build-linux-kernel-qemu-50b50af1` | mini-SWE-agent | false | 34 | source-valid | miniswe-message-trajectory; 34 operations |
| `miniswe-Moonshot__Kimi-K2-250905-build-pmars-c2e55c08` | mini-SWE-agent | false | 26 | source-valid | miniswe-message-trajectory; 26 operations |
| `miniswe-Moonshot__Kimi-K2-250905-build-pov-ray-dddf443d` | mini-SWE-agent | true | 51 | source-valid | miniswe-message-trajectory; 51 operations |
| `miniswe-Moonshot__Kimi-K2-250905-build-stp-3c69a58a` | mini-SWE-agent | false | 53 | source-valid | miniswe-message-trajectory; 53 operations |
| `miniswe-Moonshot__Kimi-K2-250905-build-tcc-qemu-f8d19d11` | mini-SWE-agent | true | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-Moonshot__Kimi-K2-250905-cartpole-rl-training-20931ada` | mini-SWE-agent | false | 29 | source-valid | miniswe-message-trajectory; 29 operations |
| `miniswe-Moonshot__Kimi-K2-250905-catch-me-if-you-can-9285e554` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-Moonshot__Kimi-K2-250905-chem-property-targeting-7eb5eb43` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-Moonshot__Kimi-K2-250905-chem-rf-ff3187e8` | mini-SWE-agent | false | 57 | source-valid | miniswe-message-trajectory; 57 operations |
| `miniswe-Moonshot__Kimi-K2-250905-chess-best-move-568f0163` | mini-SWE-agent | false | 34 | source-valid | miniswe-message-trajectory; 34 operations |
| `miniswe-Moonshot__Kimi-K2-250905-circuit-fibsqrt-ef2274df` | mini-SWE-agent | false | 38 | source-valid | miniswe-message-trajectory; 38 operations |
| `miniswe-Moonshot__Kimi-K2-250905-cobol-modernization-82bc29b1` | mini-SWE-agent | true | 50 | source-valid | miniswe-message-trajectory; 50 operations |
| `miniswe-Moonshot__Kimi-K2-250905-code-from-image-ef718bfa` | mini-SWE-agent | false | 39 | source-valid | miniswe-message-trajectory; 39 operations |
| `miniswe-Moonshot__Kimi-K2-250905-configure-git-webserver-a65d8a3c` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-Moonshot__Kimi-K2-250905-constraints-scheduling-c7e39449` | mini-SWE-agent | true | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-Moonshot__Kimi-K2-250905-count-dataset-tokens-478464d4` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-Moonshot__Kimi-K2-250905-countdown-game-5334a405` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-Moonshot__Kimi-K2-250905-crack-7z-hash-42c097be` | mini-SWE-agent | true | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-Moonshot__Kimi-K2-250905-cross-entropy-method-fd16274e` | mini-SWE-agent | true | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-Moonshot__Kimi-K2-250905-csv-to-parquet-51b1f829` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-Moonshot__Kimi-K2-250905-custom-memory-heap-crash-ddf56ecd` | mini-SWE-agent | false | 43 | source-valid | miniswe-message-trajectory; 43 operations |
| `miniswe-Moonshot__Kimi-K2-250905-db-wal-recovery-adbbc843` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-Moonshot__Kimi-K2-250905-debug-long-program-f606b9e8` | mini-SWE-agent | true | 52 | source-valid | miniswe-message-trajectory; 52 operations |
| `miniswe-Moonshot__Kimi-K2-250905-decommissioning-service-with-sensitive-data-469bd3fb` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-Moonshot__Kimi-K2-250905-deterministic-tarball-f846b618` | mini-SWE-agent | false | 36 | source-valid | miniswe-message-trajectory; 36 operations |
| `miniswe-Moonshot__Kimi-K2-250905-distribution-search-12a73755` | mini-SWE-agent | false | 33 | source-valid | miniswe-message-trajectory; 33 operations |
| `miniswe-Moonshot__Kimi-K2-250905-dna-assembly-ca024316` | mini-SWE-agent | false | 27 | source-valid | miniswe-message-trajectory; 27 operations |
| `miniswe-Moonshot__Kimi-K2-250905-dna-insert-edfbedc8` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Moonshot__Kimi-K2-250905-download-youtube-af03c29c` | mini-SWE-agent | false | 26 | source-valid | miniswe-message-trajectory; 26 operations |
| `miniswe-Moonshot__Kimi-K2-250905-extract-elf-a98fdd4a` | mini-SWE-agent | true | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-Moonshot__Kimi-K2-250905-extract-moves-from-video-684b7690` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-Moonshot__Kimi-K2-250905-feal-differential-cryptanalysis-56fd73be` | mini-SWE-agent | false | 38 | source-valid | miniswe-message-trajectory; 38 operations |
| `miniswe-Moonshot__Kimi-K2-250905-feal-linear-cryptanalysis-0b30dfe2` | mini-SWE-agent | false | 45 | source-valid | miniswe-message-trajectory; 45 operations |
| `miniswe-Moonshot__Kimi-K2-250905-fibonacci-server-8e0cf485` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-Moonshot__Kimi-K2-250905-filter-js-from-html-cbd52961` | mini-SWE-agent | false | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-Moonshot__Kimi-K2-250905-financial-document-processor-91e9fd8f` | mini-SWE-agent | false | 40 | source-valid | miniswe-message-trajectory; 40 operations |
| `miniswe-Moonshot__Kimi-K2-250905-find-official-code-19fc1890` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-Moonshot__Kimi-K2-250905-find-restaurant-7c805a31` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Moonshot__Kimi-K2-250905-fix-code-vulnerability-64898122` | mini-SWE-agent | false | 34 | source-valid | miniswe-message-trajectory; 34 operations |
| `miniswe-Moonshot__Kimi-K2-250905-fix-git-92ea1ddc` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-Moonshot__Kimi-K2-250905-fix-ocaml-gc-dc1ed0f7` | mini-SWE-agent | false | 133 | source-valid | miniswe-message-trajectory; 133 operations |
| `miniswe-Moonshot__Kimi-K2-250905-flood-monitoring-basic-df41248c` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-Moonshot__Kimi-K2-250905-fmri-encoding-r-afcf1517` | mini-SWE-agent | false | 29 | excluded | miniswe-message-trajectory emitted 30 operations; public step_count is 29 |
| `miniswe-Moonshot__Kimi-K2-250905-form-filling-b5964792` | mini-SWE-agent | true | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-Moonshot__Kimi-K2-250905-gcode-to-text-8ebcd8f4` | mini-SWE-agent | false | 26 | source-valid | miniswe-message-trajectory; 26 operations |
| `miniswe-Moonshot__Kimi-K2-250905-get-bitcoin-nodes-2323be07` | mini-SWE-agent | true | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-Moonshot__Kimi-K2-250905-git-multibranch-78e8d858` | mini-SWE-agent | true | 38 | source-valid | miniswe-message-trajectory; 38 operations |
| `miniswe-Moonshot__Kimi-K2-250905-git-workflow-hack-fb28d976` | mini-SWE-agent | true | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-Moonshot__Kimi-K2-250905-gpt2-codegolf-754fcd9b` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-Moonshot__Kimi-K2-250905-hf-lora-adapter-6cd384b1` | mini-SWE-agent | false | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-Moonshot__Kimi-K2-250905-hf-model-inference-75bbd025` | mini-SWE-agent | false | 28 | source-valid | miniswe-message-trajectory; 28 operations |
| `miniswe-Moonshot__Kimi-K2-250905-hf-train-lora-adapter-59d1dee1` | mini-SWE-agent | false | 35 | source-valid | miniswe-message-trajectory; 35 operations |
| `miniswe-Moonshot__Kimi-K2-250905-home-server-https-0299f8af` | mini-SWE-agent | true | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-Moonshot__Kimi-K2-250905-html-finance-verify-cd4a1e5a` | mini-SWE-agent | false | 28 | source-valid | miniswe-message-trajectory; 28 operations |
| `miniswe-Moonshot__Kimi-K2-250905-huarong-dao-solver-7bfd30dc` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-Moonshot__Kimi-K2-250905-hydra-debug-slurm-mode-7df59455` | mini-SWE-agent | false | 37 | source-valid | miniswe-message-trajectory; 37 operations |
| `miniswe-Moonshot__Kimi-K2-250905-implement-eigenvectors-from-eigenvalues-research-paper-ddd348f1` | mini-SWE-agent | false | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-Moonshot__Kimi-K2-250905-incompatible-python-fasttext-8b0e83e6` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-Moonshot__Kimi-K2-250905-install-windows-3.11-650a0459` | mini-SWE-agent | false | 34 | source-valid | miniswe-message-trajectory; 34 operations |
| `miniswe-Moonshot__Kimi-K2-250905-install-windows-xp-f324660c` | mini-SWE-agent | false | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-Moonshot__Kimi-K2-250905-intrusion-detection-31ee8aed` | mini-SWE-agent | true | 27 | source-valid | miniswe-message-trajectory; 27 operations |
| `miniswe-Moonshot__Kimi-K2-250905-jq-data-processing-f1f17a82` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-Moonshot__Kimi-K2-250905-jupyter-notebook-server-895f256e` | mini-SWE-agent | false | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-Moonshot__Kimi-K2-250905-kv-store-grpc-472a441b` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-Moonshot__Kimi-K2-250905-largest-eigenval-1a93ac7c` | mini-SWE-agent | true | 29 | source-valid | miniswe-message-trajectory; 29 operations |
| `miniswe-Moonshot__Kimi-K2-250905-lean4-proof-32a8d219` | mini-SWE-agent | false | 47 | source-valid | miniswe-message-trajectory; 47 operations |
| `miniswe-Moonshot__Kimi-K2-250905-leelachess0-pytorch-conversion-5375f476` | mini-SWE-agent | false | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-Moonshot__Kimi-K2-250905-llm-inference-batching-scheduler-5e3e40ea` | mini-SWE-agent | false | 59 | source-valid | miniswe-message-trajectory; 59 operations |
| `miniswe-Moonshot__Kimi-K2-250905-llm-spec-decoding-69e87713` | mini-SWE-agent | false | 29 | source-valid | miniswe-message-trajectory; 29 operations |
| `miniswe-Moonshot__Kimi-K2-250905-mailman-a1f9f1f0` | mini-SWE-agent | false | 41 | source-valid | miniswe-message-trajectory; 41 operations |
| `miniswe-Moonshot__Kimi-K2-250905-make-mips-interpreter-e7925059` | mini-SWE-agent | false | 27 | source-valid | miniswe-message-trajectory; 27 operations |
| `miniswe-Moonshot__Kimi-K2-250905-matlab-python-conversion-1c489d43` | mini-SWE-agent | false | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-Moonshot__Kimi-K2-250905-mcmc-sampling-stan-9cd6ecb2` | mini-SWE-agent | false | 26 | source-valid | miniswe-message-trajectory; 26 operations |
| `miniswe-Moonshot__Kimi-K2-250905-merge-diff-arc-agi-task-9e1ec0b0` | mini-SWE-agent | false | 34 | source-valid | miniswe-message-trajectory; 34 operations |
| `miniswe-Moonshot__Kimi-K2-250905-mlflow-register-a4b3e846` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Moonshot__Kimi-K2-250905-mnist-learning-fix-44eee6b4` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-Moonshot__Kimi-K2-250905-modernize-fortran-build-afb506d4` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-Moonshot__Kimi-K2-250905-modernize-scientific-stack-b14fd212` | mini-SWE-agent | true | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-Moonshot__Kimi-K2-250905-movie-helper-c4c5011b` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-Moonshot__Kimi-K2-250905-mteb-eval-ca450264` | mini-SWE-agent | true | 79 | source-valid | miniswe-message-trajectory; 79 operations |
| `miniswe-Moonshot__Kimi-K2-250905-mteb-retrieve-b81a34e9` | mini-SWE-agent | false | 46 | source-valid | miniswe-message-trajectory; 46 operations |
| `miniswe-Moonshot__Kimi-K2-250905-multi-source-data-merger-2020d4b8` | mini-SWE-agent | false | 28 | source-valid | miniswe-message-trajectory; 28 operations |
| `miniswe-Moonshot__Kimi-K2-250905-neuron-to-jaxley-conversion-a7ab811d` | mini-SWE-agent | false | 37 | source-valid | miniswe-message-trajectory; 37 operations |
| `miniswe-Moonshot__Kimi-K2-250905-nginx-request-logging-c1115f24` | mini-SWE-agent | true | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-Moonshot__Kimi-K2-250905-npm-conflict-resolution-4c6d2c64` | mini-SWE-agent | false | 47 | source-valid | miniswe-message-trajectory; 47 operations |
| `miniswe-Moonshot__Kimi-K2-250905-ode-solver-rk4-52fb9781` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Moonshot__Kimi-K2-250905-oom-6c9fee51` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Moonshot__Kimi-K2-250905-openssl-selfsigned-cert-c40810f7` | mini-SWE-agent | false | 29 | source-valid | miniswe-message-trajectory; 29 operations |
| `miniswe-Moonshot__Kimi-K2-250905-optimal-transport-609a4aa9` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-Moonshot__Kimi-K2-250905-organization-json-generator-b2a0e723` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-Moonshot__Kimi-K2-250905-overfull-hbox-b4805d16` | mini-SWE-agent | false | 34 | source-valid | miniswe-message-trajectory; 34 operations |
| `miniswe-Moonshot__Kimi-K2-250905-pandas-etl-011a2175` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-Moonshot__Kimi-K2-250905-parallel-particle-simulator-25117e51` | mini-SWE-agent | false | 56 | source-valid | miniswe-message-trajectory; 56 operations |
| `miniswe-Moonshot__Kimi-K2-250905-parallelize-compute-squares-3fcf38b5` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-Moonshot__Kimi-K2-250905-parallelize-graph-37fa127e` | mini-SWE-agent | true | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-Moonshot__Kimi-K2-250905-password-recovery-58db6f52` | mini-SWE-agent | false | 46 | source-valid | miniswe-message-trajectory; 46 operations |
| `miniswe-Moonshot__Kimi-K2-250905-path-tracing-729a5d57` | mini-SWE-agent | false | 32 | source-valid | miniswe-message-trajectory; 32 operations |
| `miniswe-Moonshot__Kimi-K2-250905-path-tracing-reverse-027b6456` | mini-SWE-agent | false | 39 | source-valid | miniswe-message-trajectory; 39 operations |
| `miniswe-Moonshot__Kimi-K2-250905-play-lord-356c5b19` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-Moonshot__Kimi-K2-250905-play-zork-easy-52ae7d97` | mini-SWE-agent | false | 44 | source-valid | miniswe-message-trajectory; 44 operations |
| `miniswe-Moonshot__Kimi-K2-250905-port-compressor-af6f1e58` | mini-SWE-agent | false | 70 | source-valid | miniswe-message-trajectory; 70 operations |
| `miniswe-Moonshot__Kimi-K2-250905-portfolio-optimization-9fd09295` | mini-SWE-agent | true | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-Moonshot__Kimi-K2-250905-postgres-csv-clean-8526831b` | mini-SWE-agent | false | 47 | source-valid | miniswe-message-trajectory; 47 operations |
| `miniswe-Moonshot__Kimi-K2-250905-predict-customer-churn-7a8c6a7d` | mini-SWE-agent | true | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-Moonshot__Kimi-K2-250905-processing-pipeline-1402b15e` | mini-SWE-agent | true | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Moonshot__Kimi-K2-250905-protein-assembly-71ca164d` | mini-SWE-agent | false | 31 | source-valid | miniswe-message-trajectory; 31 operations |
| `miniswe-Moonshot__Kimi-K2-250905-puzzle-solver-e4a2f2e7` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Moonshot__Kimi-K2-250905-pypi-server-7f2e2c6b` | mini-SWE-agent | true | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-Moonshot__Kimi-K2-250905-pytorch-model-cli-36b1c247` | mini-SWE-agent | false | 27 | source-valid | miniswe-message-trajectory; 27 operations |
| `miniswe-Moonshot__Kimi-K2-250905-pytorch-model-recovery-42be9d97` | mini-SWE-agent | false | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-Moonshot__Kimi-K2-250905-query-optimize-30a7f304` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-Moonshot__Kimi-K2-250905-raman-fitting-a59eb945` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-Moonshot__Kimi-K2-250905-rare-mineral-allocation-a7c63ce3` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Moonshot__Kimi-K2-250905-recover-obfuscated-files-ce6523cd` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-Moonshot__Kimi-K2-250905-regex-chess-16b9e7f2` | mini-SWE-agent | false | 53 | source-valid | miniswe-message-trajectory; 53 operations |
| `miniswe-Moonshot__Kimi-K2-250905-regex-log-54923fe3` | mini-SWE-agent | true | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-Moonshot__Kimi-K2-250905-reshard-c4-data-fc0beaee` | mini-SWE-agent | false | 39 | source-valid | miniswe-message-trajectory; 39 operations |
| `miniswe-Moonshot__Kimi-K2-250905-rstan-to-pystan-fa237be9` | mini-SWE-agent | false | 28 | source-valid | miniswe-message-trajectory; 28 operations |
| `miniswe-Moonshot__Kimi-K2-250905-run-pdp11-code-0dbcd4b8` | mini-SWE-agent | false | 59 | source-valid | miniswe-message-trajectory; 59 operations |
| `miniswe-Moonshot__Kimi-K2-250905-sam-cell-seg-571ce000` | mini-SWE-agent | false | 40 | source-valid | miniswe-message-trajectory; 40 operations |
| `miniswe-Moonshot__Kimi-K2-250905-schedule-vacation-8f59eb15` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-Moonshot__Kimi-K2-250905-security-celery-redis-rce-55fcf87a` | mini-SWE-agent | false | 36 | source-valid | miniswe-message-trajectory; 36 operations |
| `miniswe-Moonshot__Kimi-K2-250905-security-vulhub-minio-a6701a54` | mini-SWE-agent | false | 36 | source-valid | miniswe-message-trajectory; 36 operations |
| `miniswe-Moonshot__Kimi-K2-250905-setup-custom-dev-env-2c3623e5` | mini-SWE-agent | true | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-Moonshot__Kimi-K2-250905-solana-data-70b9a7dd` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-Moonshot__Kimi-K2-250905-solve-maze-challenge-774e8d94` | mini-SWE-agent | false | 26 | source-valid | miniswe-message-trajectory; 26 operations |
| `miniswe-Moonshot__Kimi-K2-250905-solve-sudoku-ddc9b014` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-Moonshot__Kimi-K2-250905-sparql-university-4205410e` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-Moonshot__Kimi-K2-250905-speech-to-text-f9a8cc86` | mini-SWE-agent | false | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-Moonshot__Kimi-K2-250905-spinning-up-rl-fbf101e5` | mini-SWE-agent | false | 63 | source-valid | miniswe-message-trajectory; 63 operations |
| `miniswe-Moonshot__Kimi-K2-250905-spring-messaging-vul-8cd643e4` | mini-SWE-agent | false | 57 | source-valid | miniswe-message-trajectory; 57 operations |
| `miniswe-Moonshot__Kimi-K2-250905-sql-injection-attack-dcb22a2f` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-Moonshot__Kimi-K2-250905-sqlite-db-truncate-f4d090d4` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-Moonshot__Kimi-K2-250905-sqlite-with-gcov-f77cae20` | mini-SWE-agent | true | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-Moonshot__Kimi-K2-250905-stable-parallel-kmeans-cee201ac` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-Moonshot__Kimi-K2-250905-tmux-advanced-workflow-130f6bdf` | mini-SWE-agent | true | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-Moonshot__Kimi-K2-250905-torch-tensor-parallelism-7551ffae` | mini-SWE-agent | false | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-Moonshot__Kimi-K2-250905-train-bpe-tokenizer-52c9457c` | mini-SWE-agent | false | 36 | source-valid | miniswe-message-trajectory; 36 operations |
| `miniswe-Moonshot__Kimi-K2-250905-train-fasttext-0423d020` | mini-SWE-agent | false | 59 | source-valid | miniswe-message-trajectory; 59 operations |
| `miniswe-Moonshot__Kimi-K2-250905-tree-directory-parser-b75ab3ce` | mini-SWE-agent | false | 26 | source-valid | miniswe-message-trajectory; 26 operations |
| `miniswe-Moonshot__Kimi-K2-250905-triton-interpret-ec04c7f7` | mini-SWE-agent | false | 34 | source-valid | miniswe-message-trajectory; 34 operations |
| `miniswe-Moonshot__Kimi-K2-250905-vertex-solver-2dea2c34` | mini-SWE-agent | true | 42 | source-valid | miniswe-message-trajectory; 42 operations |
| `miniswe-Moonshot__Kimi-K2-250905-video-processing-8b01bb03` | mini-SWE-agent | false | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-Moonshot__Kimi-K2-250905-vimscript-vim-quine-acaa340c` | mini-SWE-agent | false | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-Moonshot__Kimi-K2-250905-vul-flask-3e238e90` | mini-SWE-agent | false | 43 | source-valid | miniswe-message-trajectory; 43 operations |
| `miniswe-Moonshot__Kimi-K2-250905-vul-flink-b146c55d` | mini-SWE-agent | false | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-Moonshot__Kimi-K2-250905-vulnerable-secret-f783e599` | mini-SWE-agent | false | 29 | source-valid | miniswe-message-trajectory; 29 operations |
| `miniswe-Moonshot__Kimi-K2-250905-winning-avg-corewars-5bdf9bb3` | mini-SWE-agent | false | 60 | source-valid | miniswe-message-trajectory; 60 operations |
| `miniswe-Moonshot__Kimi-K2-250905-word2vec-from-scratch-6a85bde1` | mini-SWE-agent | false | 27 | source-valid | miniswe-message-trajectory; 27 operations |
| `miniswe-Moonshot__Kimi-K2-250905-write-compressor-de55338b` | mini-SWE-agent | false | 37 | source-valid | miniswe-message-trajectory; 37 operations |
| `miniswe-OpenAI__GPT-5-3d-model-format-legacy-4d59305e` | mini-SWE-agent | false | 28 | excluded | miniswe-agent-log-markers emitted 24 operations; public step_count is 28 |
| `miniswe-OpenAI__GPT-5-add-benchmark-lm-eval-harness-c2b03ec1` | mini-SWE-agent | false | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-OpenAI__GPT-5-alibaba__fastjson2-2559-af974c9d` | mini-SWE-agent | true | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-OpenAI__GPT-5-alibaba__fastjson2-2775-d1dc0295` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-OpenAI__GPT-5-astropy__astropy-14598-416c95db` | mini-SWE-agent | false | 26 | source-valid | miniswe-message-trajectory; 26 operations |
| `miniswe-OpenAI__GPT-5-build-cython-ext-64eba0f3` | mini-SWE-agent | false | 13 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 13 |
| `miniswe-OpenAI__GPT-5-build-linux-kernel-qemu-36d9f9cd` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-OpenAI__GPT-5-build-pmars-0e21302e` | mini-SWE-agent | true | 14 | excluded | miniswe-agent-log-markers emitted 3 operations; public step_count is 14 |
| `miniswe-OpenAI__GPT-5-build-pov-ray-46cb3d00` | mini-SWE-agent | false | 28 | source-valid | miniswe-message-trajectory; 28 operations |
| `miniswe-OpenAI__GPT-5-build-stp-c74e1e89` | mini-SWE-agent | false | 20 | excluded | miniswe-agent-log-markers emitted 3 operations; public step_count is 20 |
| `miniswe-OpenAI__GPT-5-catchorg__Catch2-1608-bfc6d70b` | mini-SWE-agent | true | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-OpenAI__GPT-5-clap-rs__clap-2501-1c7ee8f3` | mini-SWE-agent | true | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-OpenAI__GPT-5-clap-rs__clap-2529-0505b282` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-OpenAI__GPT-5-clap-rs__clap-2534-42faa8a1` | mini-SWE-agent | true | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-OpenAI__GPT-5-clap-rs__clap-2758-8f87bc0d` | mini-SWE-agent | true | 41 | source-valid | miniswe-message-trajectory; 41 operations |
| `miniswe-OpenAI__GPT-5-clap-rs__clap-2895-928269b9` | mini-SWE-agent | true | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-OpenAI__GPT-5-clap-rs__clap-3179-107b6c1d` | mini-SWE-agent | true | 37 | source-valid | miniswe-message-trajectory; 37 operations |
| `miniswe-OpenAI__GPT-5-clap-rs__clap-3420-3b52d5f9` | mini-SWE-agent | true | 10 | source-valid | miniswe-message-trajectory; 10 operations |
| `miniswe-OpenAI__GPT-5-clap-rs__clap-3421-8c92021d` | mini-SWE-agent | true | 35 | source-valid | miniswe-message-trajectory; 35 operations |
| `miniswe-OpenAI__GPT-5-clap-rs__clap-3684-d6409bb2` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-OpenAI__GPT-5-clap-rs__clap-3975-5f1af46d` | mini-SWE-agent | true | 40 | source-valid | miniswe-message-trajectory; 40 operations |
| `miniswe-OpenAI__GPT-5-clap-rs__clap-4248-85bd7a43` | mini-SWE-agent | true | 35 | source-valid | miniswe-message-trajectory; 35 operations |
| `miniswe-OpenAI__GPT-5-clap-rs__clap-4474-24518f22` | mini-SWE-agent | true | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-OpenAI__GPT-5-cli__cli-5019-a9eeca4d` | mini-SWE-agent | true | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-OpenAI__GPT-5-cli__cli-6706-4715bbb3` | mini-SWE-agent | true | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-OpenAI__GPT-5-code-from-image-a4ac6d9e` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-cron-broken-network-ab2690b8` | mini-SWE-agent | false | 15 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 15 |
| `miniswe-OpenAI__GPT-5-darkreader__darkreader-7241-c1fc66d3` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-db-wal-recovery-785110a8` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-django__django-14999-5d6ca542` | mini-SWE-agent | true | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-OpenAI__GPT-5-django__django-16032-a1ba93e9` | mini-SWE-agent | true | 29 | source-valid | miniswe-message-trajectory; 29 operations |
| `miniswe-OpenAI__GPT-5-facebook__zstd-1105-72b3ec65` | mini-SWE-agent | true | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-OpenAI__GPT-5-facebook__zstd-1390-eb0039de` | mini-SWE-agent | true | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-OpenAI__GPT-5-facebook__zstd-1532-f4d50598` | mini-SWE-agent | true | 9 | source-valid | miniswe-message-trajectory; 9 operations |
| `miniswe-OpenAI__GPT-5-facebook__zstd-1733-786102c1` | mini-SWE-agent | true | 44 | source-valid | miniswe-message-trajectory; 44 operations |
| `miniswe-OpenAI__GPT-5-facebook__zstd-2094-7f31a0cb` | mini-SWE-agent | true | 28 | source-valid | miniswe-message-trajectory; 28 operations |
| `miniswe-OpenAI__GPT-5-facebook__zstd-637-296cd1bd` | mini-SWE-agent | true | 10 | source-valid | miniswe-message-trajectory; 10 operations |
| `miniswe-OpenAI__GPT-5-fasterxml__jackson-core-1016-b13d452d` | mini-SWE-agent | true | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-OpenAI__GPT-5-fasterxml__jackson-core-183-06989053` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-OpenAI__GPT-5-fasterxml__jackson-databind-3701-1d7205f1` | mini-SWE-agent | true | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-OpenAI__GPT-5-fasterxml__jackson-databind-4050-6e9b6e5b` | mini-SWE-agent | true | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-OpenAI__GPT-5-fasterxml__jackson-databind-4469-782eb6df` | mini-SWE-agent | true | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-OpenAI__GPT-5-fasterxml__jackson-databind-4641-989d1554` | mini-SWE-agent | true | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-OpenAI__GPT-5-fasterxml__jackson-dataformat-xml-638-5311424b` | mini-SWE-agent | true | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-OpenAI__GPT-5-fix-code-vulnerability-1ae3c58d` | mini-SWE-agent | true | 16 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 16 |
| `miniswe-OpenAI__GPT-5-fix-ocaml-gc-c3957105` | mini-SWE-agent | true | 27 | source-valid | miniswe-message-trajectory; 27 operations |
| `miniswe-OpenAI__GPT-5-fmtlib__fmt-1663-96a4eb1d` | mini-SWE-agent | true | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-OpenAI__GPT-5-fmtlib__fmt-2394-ff03c422` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-OpenAI__GPT-5-fmtlib__fmt-4286-f5dcb102` | mini-SWE-agent | true | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-OpenAI__GPT-5-hf-lora-adapter-b8a4d07e` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-12981-2b6ebb35` | mini-SWE-agent | true | 5 | source-valid | miniswe-message-trajectory; 5 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-13693-5082a335` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-13865-e5274811` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-15158-216b2d6c` | mini-SWE-agent | true | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-15795-e799e83b` | mini-SWE-agent | true | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-16198-ba2a9922` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-19590-662e24c9` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-20136-e547c8dd` | mini-SWE-agent | false | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-21768-cbe176af` | mini-SWE-agent | true | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-22458-52eaee42` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-22920-5fed04f7` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-23126-0442d3e7` | mini-SWE-agent | true | 6 | source-valid | miniswe-message-trajectory; 6 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-23223-8f2625a5` | mini-SWE-agent | false | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-24238-8660dac8` | mini-SWE-agent | true | 7 | source-valid | miniswe-message-trajectory; 7 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-27463-c5d46c40` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-28517-798d4cd4` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-28535-a642a1b8` | mini-SWE-agent | true | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-29311-63722215` | mini-SWE-agent | true | 8 | source-valid | miniswe-message-trajectory; 8 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-29449-fc2c725c` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-30556-2c3469e4` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-3716-d27085c5` | mini-SWE-agent | true | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-5122-64560889` | mini-SWE-agent | true | 9 | source-valid | miniswe-message-trajectory; 9 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-6098-292b69fe` | mini-SWE-agent | true | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-7078-8ce01d5c` | mini-SWE-agent | true | 9 | source-valid | miniswe-message-trajectory; 9 operations |
| `miniswe-OpenAI__GPT-5-huggingface__transformers-8624-93528c38` | mini-SWE-agent | true | 6 | source-valid | miniswe-message-trajectory; 6 operations |
| `miniswe-OpenAI__GPT-5-iamkun__dayjs-1319-06155f38` | mini-SWE-agent | true | 9 | source-valid | miniswe-message-trajectory; 9 operations |
| `miniswe-OpenAI__GPT-5-iamkun__dayjs-1414-de572c92` | mini-SWE-agent | true | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-OpenAI__GPT-5-iamkun__dayjs-1611-bd8d1607` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-OpenAI__GPT-5-iamkun__dayjs-1725-daa7ec2d` | mini-SWE-agent | true | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-0fd88717c953b92ed8a50495d55e630eb5d59166-vba6da65a0f3baefda7a058ebbd0a8dcafb8512f5-09135d56` | mini-SWE-agent | true | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-1a4644ff15355fd696ac5b9d074a566a80fe7ca3-v30a923fb5c164d6cd18280c02422f75e611e8fb2-e1edb594` | mini-SWE-agent | true | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-1b70260d5aa2f6c9782fd2b848e8d16566e50d85-vba6da65a0f3baefda7a058ebbd0a8dcafb8512f5-0b674c2a` | mini-SWE-agent | false | 38 | source-valid | miniswe-message-trajectory; 38 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-4c5ce5a1a9e79a845aff4978cfeb72a0d4ecf7d6-v1055803c3a812189a1133297f7f5468579283f86-6e5a7eaa` | mini-SWE-agent | false | 30 | source-valid | miniswe-message-trajectory; 30 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-5260527c4a71bfed99d803e687dd19619423b134-vba6da65a0f3baefda7a058ebbd0a8dcafb8512f5-e1678ee2` | mini-SWE-agent | true | 10 | source-valid | miniswe-message-trajectory; 10 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-5640093f1ca63fd6af231cc8a7fb7d40e1907b8c-vba6da65a0f3baefda7a058ebbd0a8dcafb8512f5-21500546` | mini-SWE-agent | true | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-622a493ae03bd5e5cf517d336fc426e9d12208c7-v906c969b551b346ef54a2c0b41e04f632b7b73c2-96d6006e` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-6cc97447aac5816745278f3735af128afb255c81-v0f01c69f1e2528b935359cfe578530722bca2c59-3e4c6fd8` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-709484969c8a4ffd74b839a673431a8c5caa6457-vba6da65a0f3baefda7a058ebbd0a8dcafb8512f5-c1a50830` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-77658704217d5f166404fc67997203c25381cb6e-v390e508d27db7a51eece36bb6d9698b63a5b638a-da19e289` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-7e1a347695c7987ae56ef1b6919156d9254010ad-v390e508d27db7a51eece36bb6d9698b63a5b638a-f7c2004c` | mini-SWE-agent | false | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-8127abbc298cabf04aaa89a478fc5e5e3432a6fc-v30a923fb5c164d6cd18280c02422f75e611e8fb2-6def99c2` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-83909bfa22573777e3db5688773bda59721962ad-vba6da65a0f3baefda7a058ebbd0a8dcafb8512f5-af8515d3` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-9142be2f6cabbe6597c9254c5bb9186d17036d55-v0f01c69f1e2528b935359cfe578530722bca2c59-48b421ba` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-942424e10b2095a173dbd78e7128f52f7995849b-v30a923fb5c164d6cd18280c02422f75e611e8fb2-f0eb08e8` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-949c503f2ef4b2c5d668af0492a5c0db1ab86140-v0f01c69f1e2528b935359cfe578530722bca2c59-3a45c2a2` | mini-SWE-agent | false | 27 | source-valid | miniswe-message-trajectory; 27 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-a7d2a4e03209cff1e97e59fd54bb2b05fdbdbec6-v0f01c69f1e2528b935359cfe578530722bca2c59-bb4a3364` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-b2a289dcbb702003377221e25f62c8a3608f0e89-v173091e2e36d38c978002990795f66cfc0af30ad-e1675391` | mini-SWE-agent | false | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-b5e0293645570f3f404ad1dbbe5f006956ada0df-v0f01c69f1e2528b935359cfe578530722bca2c59-a402f2d3` | mini-SWE-agent | false | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-bec27fb4c0a40c5f8bbcf26a475704227d65ee73-v30a923fb5c164d6cd18280c02422f75e611e8fb2-1af9d682` | mini-SWE-agent | false | 36 | source-valid | miniswe-message-trajectory; 36 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-bf98f031f3f5af31a2d78dc2f0a58fe92ebae0bb-v1055803c3a812189a1133297f7f5468579283f86-7568ee74` | mini-SWE-agent | false | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-cb94c0cc550df9e98f1247bc71d8c2b861c75049-v1055803c3a812189a1133297f7f5468579283f86-6c8d52c0` | mini-SWE-agent | false | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad-825c738f` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-e9e6001263f51103e96e58ad382660df0f3d0e39-v30a923fb5c164d6cd18280c02422f75e611e8fb2-4af2bfdc` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-f8ef34672b961a95ec7282643679492862c688ec-vba6da65a0f3baefda7a058ebbd0a8dcafb8512f5-f91ad040` | mini-SWE-agent | true | 36 | source-valid | miniswe-message-trajectory; 36 operations |
| `miniswe-OpenAI__GPT-5-instance_ansible__ansible-fb144c44144f8bd3542e71f5db62b6d322c7bd85-vba6da65a0f3baefda7a058ebbd0a8dcafb8512f5-e4f54351` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-OpenAI__GPT-5-instance_element-hq__element-web-5dfde12c1c1c0b6e48f17e3405468593e39d9492-vnan-15dbf87c` | mini-SWE-agent | true | 33 | source-valid | miniswe-message-trajectory; 33 operations |
| `miniswe-OpenAI__GPT-5-instance_element-hq__element-web-aeabf3b18896ac1eb7ae9757e66ce886120f8309-vnan-dc9947f9` | mini-SWE-agent | true | 30 | source-valid | miniswe-message-trajectory; 30 operations |
| `miniswe-OpenAI__GPT-5-instance_element-hq__element-web-fe14847bb9bb07cab1b9c6c54335ff22ca5e516a-vnan-ca34b75e` | mini-SWE-agent | true | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-OpenAI__GPT-5-instance_future-architect__vuls-b8db2e0b74f60cb7d45f710f255e061f054b6afc-9bd52c2f` | mini-SWE-agent | true | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-OpenAI__GPT-5-instance_internetarchive__openlibrary-60725705782832a2cb22e17c49697948a42a9d03-v298a7a812ceed28c4c18355a091f1b268fe56d86-0bbf1adc` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-OpenAI__GPT-5-instance_internetarchive__openlibrary-757fcf46c70530739c150c57b37d6375f155dc97-ve8c8d62a2b60610a3c4631f5f23ed866bada9818-3649aa96` | mini-SWE-agent | true | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-OpenAI__GPT-5-instance_internetarchive__openlibrary-bb152d23c004f3d68986877143bb0f83531fe401-ve8c8d62a2b60610a3c4631f5f23ed866bada9818-78872a1e` | mini-SWE-agent | false | 30 | source-valid | miniswe-message-trajectory; 30 operations |
| `miniswe-OpenAI__GPT-5-instance_internetarchive__openlibrary-e1e502986a3b003899a8347ac8a7ff7b08cbfc39-v08d8e8889ec945ab821fb156c04c7d2e2810debb-b569c8f6` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-OpenAI__GPT-5-instance_qutebrowser__qutebrowser-2dd8966fdcf11972062c540b7a787e4d0de8d372-v363c8a7e5ccdf6968fc7ab84a2053ac78036691d-f8adf46a` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-OpenAI__GPT-5-instance_qutebrowser__qutebrowser-473a15f7908f2bb6d670b0e908ab34a28d8cf7e2-v363c8a7e5ccdf6968fc7ab84a2053ac78036691d-442534db` | mini-SWE-agent | false | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-OpenAI__GPT-5-instance_qutebrowser__qutebrowser-bedc9f7fadf93f83d8dee95feeecb9922b6f063f-v2ef375ac784985212b1805e1d0431dc8f1b3c171-0d0f35a6` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-OpenAI__GPT-5-instance_qutebrowser__qutebrowser-de4a1c1a2839b5b49c3d4ce21d39de48d24e2091-v2ef375ac784985212b1805e1d0431dc8f1b3c171-3f38b09b` | mini-SWE-agent | true | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-OpenAI__GPT-5-instance_qutebrowser__qutebrowser-f8e7fea0becae25ae20606f1422068137189fe9e-b08f9fd3` | mini-SWE-agent | false | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-OpenAI__GPT-5-intrusion-detection-316f5769` | mini-SWE-agent | true | 14 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| `miniswe-OpenAI__GPT-5-jqlang__jq-1793-cb6f2ea9` | mini-SWE-agent | true | 9 | source-valid | miniswe-message-trajectory; 9 operations |
| `miniswe-OpenAI__GPT-5-jqlang__jq-2654-2d9cf62c` | mini-SWE-agent | true | 10 | source-valid | miniswe-message-trajectory; 10 operations |
| `miniswe-OpenAI__GPT-5-jqlang__jq-2919-60dfcb4e` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-OpenAI__GPT-5-keras-team__keras-18553-ebd8df40` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-keras-team__keras-18871-e57260c2` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-keras-team__keras-19484-2bd0f0db` | mini-SWE-agent | true | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-OpenAI__GPT-5-keras-team__keras-19636-0123c279` | mini-SWE-agent | true | 27 | source-valid | miniswe-message-trajectory; 27 operations |
| `miniswe-OpenAI__GPT-5-keras-team__keras-19775-c1607884` | mini-SWE-agent | true | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-OpenAI__GPT-5-keras-team__keras-19863-027f911c` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-OpenAI__GPT-5-keras-team__keras-19924-ef73c04c` | mini-SWE-agent | true | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-OpenAI__GPT-5-langchain-ai__langchain-4009-937e743b` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-lean4-proof-796d3acf` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-logistic-regression-divergence-d858448d` | mini-SWE-agent | false | 12 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 12 |
| `miniswe-OpenAI__GPT-5-mailman-439bccbe` | mini-SWE-agent | false | 18 | excluded | miniswe-agent-log-markers emitted 16 operations; public step_count is 18 |
| `miniswe-OpenAI__GPT-5-matplotlib__matplotlib-23299-3c79bc6c` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-OpenAI__GPT-5-matplotlib__matplotlib-24627-ee685446` | mini-SWE-agent | true | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-OpenAI__GPT-5-matplotlib__matplotlib-26208-deec0657` | mini-SWE-agent | false | 26 | source-valid | miniswe-message-trajectory; 26 operations |
| `miniswe-OpenAI__GPT-5-microsoft__vscode-153857-20b3f0ba` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-microsoft__vscode-160342-47c0eefc` | mini-SWE-agent | true | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-OpenAI__GPT-5-mockito__mockito-3220-ce8a6968` | mini-SWE-agent | true | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-OpenAI__GPT-5-mteb-eval-83bdc3ef` | mini-SWE-agent | true | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-OpenAI__GPT-5-mui__material-ui-11451-f7fcbfa4` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-OpenAI__GPT-5-mui__material-ui-13778-53cfb60b` | mini-SWE-agent | true | 10 | source-valid | miniswe-message-trajectory; 10 operations |
| `miniswe-OpenAI__GPT-5-mui__material-ui-15359-d89c9600` | mini-SWE-agent | true | 8 | source-valid | miniswe-message-trajectory; 8 operations |
| `miniswe-OpenAI__GPT-5-mui__material-ui-18141-1b169883` | mini-SWE-agent | true | 10 | source-valid | miniswe-message-trajectory; 10 operations |
| `miniswe-OpenAI__GPT-5-mui__material-ui-18257-232f25a7` | mini-SWE-agent | true | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-OpenAI__GPT-5-mui__material-ui-19121-4c211ac5` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-OpenAI__GPT-5-mui__material-ui-19849-148e3cb5` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-OpenAI__GPT-5-mui__material-ui-26061-9677fc38` | mini-SWE-agent | true | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-OpenAI__GPT-5-mui__material-ui-26807-578d2101` | mini-SWE-agent | true | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-OpenAI__GPT-5-mui__material-ui-28186-0b5e3162` | mini-SWE-agent | true | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-OpenAI__GPT-5-mui__material-ui-28813-6b2d6b46` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-mui__material-ui-29023-4ce9bfb3` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-OpenAI__GPT-5-mui__material-ui-34610-9e552319` | mini-SWE-agent | true | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-OpenAI__GPT-5-nginx-request-logging-2196edde` | mini-SWE-agent | false | 11 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 11 |
| `miniswe-OpenAI__GPT-5-nlohmann__json-2225-773823db` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-nlohmann__json-2989-7b6a8ad4` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-nlohmann__json-3601-f95bc590` | mini-SWE-agent | true | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-OpenAI__GPT-5-nlohmann__json-4512-d2025eb0` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-npm-conflict-resolution-a4afc1de` | mini-SWE-agent | false | 18 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 18 |
| `miniswe-OpenAI__GPT-5-nushell__nushell-13357-4bd10bdc` | mini-SWE-agent | true | 31 | source-valid | miniswe-message-trajectory; 31 operations |
| `miniswe-OpenAI__GPT-5-parallelize-graph-2ab0330f` | mini-SWE-agent | true | 21 | excluded | miniswe-message-trajectory emitted 22 operations; public step_count is 21 |
| `miniswe-OpenAI__GPT-5-path-tracing-7cb4317a` | mini-SWE-agent | false | 12 | excluded | miniswe-agent-log-markers emitted 17 operations; public step_count is 12 |
| `miniswe-OpenAI__GPT-5-path-tracing-reverse-f05115b6` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-OpenAI__GPT-5-play-zork-24640f46` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-OpenAI__GPT-5-play-zork-easy-bf4f58f7` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-OpenAI__GPT-5-ponylang__ponyc-1057-56b583ae` | mini-SWE-agent | true | 57 | source-valid | miniswe-message-trajectory; 57 operations |
| `miniswe-OpenAI__GPT-5-ponylang__ponyc-1124-51615fdf` | mini-SWE-agent | true | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-OpenAI__GPT-5-ponylang__ponyc-1486-89d3a53e` | mini-SWE-agent | true | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-OpenAI__GPT-5-ponylang__ponyc-2168-5a83fe3d` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-OpenAI__GPT-5-ponylang__ponyc-2201-68449536` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-ponylang__ponyc-2205-2a662253` | mini-SWE-agent | true | 32 | source-valid | miniswe-message-trajectory; 32 operations |
| `miniswe-OpenAI__GPT-5-ponylang__ponyc-2247-a9fb6037` | mini-SWE-agent | true | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-OpenAI__GPT-5-ponylang__ponyc-2261-ca3954c0` | mini-SWE-agent | true | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-OpenAI__GPT-5-ponylang__ponyc-2532-98ccc9cb` | mini-SWE-agent | true | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-OpenAI__GPT-5-ponylang__ponyc-2586-ec0e231d` | mini-SWE-agent | true | 10 | source-valid | miniswe-message-trajectory; 10 operations |
| `miniswe-OpenAI__GPT-5-ponylang__ponyc-3962-c196cc7a` | mini-SWE-agent | true | 10 | source-valid | miniswe-message-trajectory; 10 operations |
| `miniswe-OpenAI__GPT-5-ponylang__ponyc-3973-6087c41b` | mini-SWE-agent | true | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-OpenAI__GPT-5-ponylang__ponyc-4595-4331ac69` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-OpenAI__GPT-5-port-compressor-715a5f28` | mini-SWE-agent | false | 21 | excluded | miniswe-message-trajectory emitted 23 operations; public step_count is 21 |
| `miniswe-OpenAI__GPT-5-portfolio-optimization-b52351ca` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-postgres-csv-clean-d504749f` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-OpenAI__GPT-5-prettier__prettier-12930-d76c2178` | mini-SWE-agent | true | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-OpenAI__GPT-5-prettier__prettier-14400-477c8cff` | mini-SWE-agent | true | 26 | source-valid | miniswe-message-trajectory; 26 operations |
| `miniswe-OpenAI__GPT-5-prettier__prettier-3515-5f0f61f5` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-OpenAI__GPT-5-prettier__prettier-361-399b1e50` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-prettier__prettier-3723-fb6a6cf9` | mini-SWE-agent | true | 9 | source-valid | miniswe-message-trajectory; 9 operations |
| `miniswe-OpenAI__GPT-5-prettier__prettier-8046-f3da19b8` | mini-SWE-agent | true | 10 | source-valid | miniswe-message-trajectory; 10 operations |
| `miniswe-OpenAI__GPT-5-pydata__xarray-6599-7db3a931` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-OpenAI__GPT-5-rayon-rs__rayon-986-c6ab9981` | mini-SWE-agent | true | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-reshard-c4-data-85bfb6a3` | mini-SWE-agent | false | 19 | excluded | MiniSWE archive has neither sessions/agent.log nor .traj.json |
| `miniswe-OpenAI__GPT-5-reverse-engineering-1ba94fc1` | mini-SWE-agent | true | 22 | excluded | miniswe-message-trajectory emitted 23 operations; public step_count is 22 |
| `miniswe-OpenAI__GPT-5-rstan-to-pystan-84f7d548` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-OpenAI__GPT-5-schemelike-metacircular-eval-454bc353` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-OpenAI__GPT-5-security-celery-redis-rce-292b9ce2` | mini-SWE-agent | false | 14 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| `miniswe-OpenAI__GPT-5-serverless__serverless-2576-ba3bde3b` | mini-SWE-agent | true | 8 | source-valid | miniswe-message-trajectory; 8 operations |
| `miniswe-OpenAI__GPT-5-serverless__serverless-3457-79a67299` | mini-SWE-agent | true | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-OpenAI__GPT-5-simdjson__simdjson-1695-aa26a89a` | mini-SWE-agent | true | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-OpenAI__GPT-5-simdjson__simdjson-2016-953561fe` | mini-SWE-agent | true | 41 | source-valid | miniswe-message-trajectory; 41 operations |
| `miniswe-OpenAI__GPT-5-solve-sudoku-b6addaec` | mini-SWE-agent | false | 14 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| `miniswe-OpenAI__GPT-5-sphinx-doc__sphinx-11445-fa910280` | mini-SWE-agent | false | 26 | source-valid | miniswe-message-trajectory; 26 operations |
| `miniswe-OpenAI__GPT-5-sphinx-doc__sphinx-8638-0bbaf886` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-OpenAI__GPT-5-sphinx-doc__sphinx-9461-b131876c` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-OpenAI__GPT-5-sphinx-doc__sphinx-9602-27a680bd` | mini-SWE-agent | false | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-OpenAI__GPT-5-spinning-up-rl-1d6a252e` | mini-SWE-agent | false | 30 | excluded | MiniSWE archive has neither sessions/agent.log nor .traj.json |
| `miniswe-OpenAI__GPT-5-sudo-llvm-ir-069a840f` | mini-SWE-agent | false | 20 | source-valid | miniswe-agent-log-markers; 20 operations |
| `miniswe-OpenAI__GPT-5-sveltejs__svelte-10608-2fe6d098` | mini-SWE-agent | true | 29 | source-valid | miniswe-message-trajectory; 29 operations |
| `miniswe-OpenAI__GPT-5-sveltejs__svelte-11913-1fe8a1b7` | mini-SWE-agent | true | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-OpenAI__GPT-5-sveltejs__svelte-12098-d4ffb92e` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-OpenAI__GPT-5-sveltejs__svelte-12649-2e0c7be4` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-OpenAI__GPT-5-sveltejs__svelte-13097-f6faf669` | mini-SWE-agent | true | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-OpenAI__GPT-5-sveltejs__svelte-14007-456a5cec` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-OpenAI__GPT-5-sveltejs__svelte-14276-bf3c86c2` | mini-SWE-agent | true | 9 | source-valid | miniswe-message-trajectory; 9 operations |
| `miniswe-OpenAI__GPT-5-sveltejs__svelte-14629-d2fadd8b` | mini-SWE-agent | true | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-OpenAI__GPT-5-sveltejs__svelte-14935-f4b5056d` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-OpenAI__GPT-5-sveltejs__svelte-9962-571c4e95` | mini-SWE-agent | true | 27 | source-valid | miniswe-message-trajectory; 27 operations |
| `miniswe-OpenAI__GPT-5-sympy__sympy-12419-4a50ba40` | mini-SWE-agent | true | 34 | source-valid | miniswe-message-trajectory; 34 operations |
| `miniswe-OpenAI__GPT-5-sympy__sympy-15976-80927487` | mini-SWE-agent | false | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-OpenAI__GPT-5-sympy__sympy-20428-5f09fe17` | mini-SWE-agent | false | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-OpenAI__GPT-5-tokio-rs__bytes-721-2d0792a3` | mini-SWE-agent | true | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-OpenAI__GPT-5-train-fasttext-883f7b5c` | mini-SWE-agent | false | 31 | source-valid | miniswe-message-trajectory; 31 operations |
| `miniswe-OpenAI__GPT-5-vuejs__core-10027-45422d8d` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-OpenAI__GPT-5-vuejs__core-10250-b8dcafce` | mini-SWE-agent | true | 9 | source-valid | miniswe-message-trajectory; 9 operations |
| `miniswe-OpenAI__GPT-5-vuejs__core-10289-aaf22431` | mini-SWE-agent | true | 10 | source-valid | miniswe-message-trajectory; 10 operations |
| `miniswe-OpenAI__GPT-5-vuejs__core-11201-36c51aa0` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-OpenAI__GPT-5-vuejs__core-11338-7f817d77` | mini-SWE-agent | true | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-OpenAI__GPT-5-vuejs__core-9213-5aade8e3` | mini-SWE-agent | true | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-OpenAI__GPT-5-vul-flink-d4672ead` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-OpenAI__GPT-5-winning-avg-corewars-265678c3` | mini-SWE-agent | false | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-OpenAI__GPT-5-yt-dlp__yt-dlp-5933-19aaec30` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-OpenAI__GPT-5-yt-dlp__yt-dlp-9862-7eb32cb4` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-add-benchmark-lm-eval-harness-712cb8da` | mini-SWE-agent | false | 47 | source-valid | miniswe-message-trajectory; 47 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-ancient-puzzle-bd12f9d4` | mini-SWE-agent | true | 19 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 19 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-assign-seats-ffbf621c` | mini-SWE-agent | true | 12 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 12 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-attention-mil-4a901b19` | mini-SWE-agent | true | 20 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 20 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-audio-synth-stft-peaks-ab611fde` | mini-SWE-agent | false | 27 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 27 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-bank-trans-filter-d5f59c3e` | mini-SWE-agent | true | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-blind-maze-explorer-5x5-9d533210` | mini-SWE-agent | false | 27 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 27 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-blind-maze-explorer-algorithm-42e8413e` | mini-SWE-agent | false | 37 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 37 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-bn-fit-modify-8ca50db9` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-break-filter-js-from-html-49b4df08` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-broken-python-68eb438d` | mini-SWE-agent | false | 12 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 12 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-cython-ext-4c117a87` | mini-SWE-agent | false | 45 | excluded | miniswe-agent-log-markers emitted 25 operations; public step_count is 45 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-initramfs-qemu-99f83ff2` | mini-SWE-agent | false | 29 | excluded | miniswe-agent-log-markers emitted 17 operations; public step_count is 29 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-linux-kernel-qemu-16fa6bbe` | mini-SWE-agent | false | 35 | excluded | miniswe-agent-log-markers emitted 34 operations; public step_count is 35 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-pmars-4c751c25` | mini-SWE-agent | true | 26 | source-valid | miniswe-message-trajectory; 26 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-pov-ray-0b1a2968` | mini-SWE-agent | false | 56 | source-valid | miniswe-message-trajectory; 56 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-stp-bb8f2fde` | mini-SWE-agent | true | 36 | excluded | miniswe-agent-log-markers emitted 4 operations; public step_count is 36 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-tcc-qemu-ec96ab54` | mini-SWE-agent | false | 47 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 47 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-cancel-async-tasks-06c26097` | mini-SWE-agent | false | 33 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 33 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-cartpole-rl-training-e9049168` | mini-SWE-agent | false | 28 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 28 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-causal-inference-r-2dc0e1a4` | mini-SWE-agent | false | 30 | source-valid | miniswe-message-trajectory; 30 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-chem-property-targeting-199ae4a8` | mini-SWE-agent | false | 17 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 17 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-chem-rf-3148c407` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-chess-best-move-1ead3998` | mini-SWE-agent | false | 12 | source-valid | miniswe-message-trajectory; 12 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-cobol-modernization-2d1ceb60` | mini-SWE-agent | false | 67 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 67 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-code-from-image-eb1b2c24` | mini-SWE-agent | false | 27 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 27 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-compile-compcert-be5980ec` | mini-SWE-agent | false | 101 | source-valid | miniswe-message-trajectory; 101 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-configure-git-webserver-02215862` | mini-SWE-agent | true | 22 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 22 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-constraints-scheduling-d5cd1b6f` | mini-SWE-agent | true | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-count-dataset-tokens-110ff6a1` | mini-SWE-agent | false | 18 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 18 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-crack-7z-hash-a1d5ae77` | mini-SWE-agent | true | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-create-bucket-0a913a23` | mini-SWE-agent | false | 16 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 16 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-cron-broken-network-4bf73a21` | mini-SWE-agent | false | 66 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 66 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-cross-entropy-method-8c5e17f1` | mini-SWE-agent | true | 37 | source-valid | miniswe-message-trajectory; 37 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-custom-memory-heap-crash-002b6324` | mini-SWE-agent | true | 35 | source-valid | miniswe-message-trajectory; 35 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-db-wal-recovery-1d773ca9` | mini-SWE-agent | false | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-deterministic-tarball-6f98b923` | mini-SWE-agent | false | 37 | source-valid | miniswe-message-trajectory; 37 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-distribution-search-52eec60a` | mini-SWE-agent | false | 31 | source-valid | miniswe-message-trajectory; 31 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-dna-assembly-dbef8c04` | mini-SWE-agent | false | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-dna-insert-bf1c909b` | mini-SWE-agent | false | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-download-youtube-f5d0bb30` | mini-SWE-agent | false | 55 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 55 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-extract-elf-1d989ea7` | mini-SWE-agent | false | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-extract-moves-from-video-cfa1eaa8` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-feal-differential-cryptanalysis-c64cbfb7` | mini-SWE-agent | false | 39 | source-valid | miniswe-message-trajectory; 39 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-feal-linear-cryptanalysis-01554082` | mini-SWE-agent | false | 38 | source-valid | miniswe-message-trajectory; 38 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-filter-js-from-html-72dea13b` | mini-SWE-agent | false | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-financial-document-processor-0d6f43a0` | mini-SWE-agent | false | 25 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 25 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-find-official-code-36141fc3` | mini-SWE-agent | false | 20 | source-valid | miniswe-message-trajectory; 20 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-find-restaurant-f1810e99` | mini-SWE-agent | false | 27 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 27 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-fix-code-vulnerability-b81b7c21` | mini-SWE-agent | true | 28 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 28 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-fix-git-3204497d` | mini-SWE-agent | true | 20 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 20 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-fix-ocaml-gc-593f7d4d` | mini-SWE-agent | false | 57 | source-valid | miniswe-message-trajectory; 57 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-flood-monitoring-basic-c02cf511` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-form-filling-ce9fda4b` | mini-SWE-agent | true | 26 | source-valid | miniswe-message-trajectory; 26 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-gcc-compiler-optimization-36e207db` | mini-SWE-agent | false | 12 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 12 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-get-bitcoin-nodes-1759a3a6` | mini-SWE-agent | false | 31 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 31 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-git-leak-recovery-020e7455` | mini-SWE-agent | true | 14 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-git-multibranch-e2fa8acd` | mini-SWE-agent | false | 71 | source-valid | miniswe-message-trajectory; 71 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-git-workflow-hack-bfdc815b` | mini-SWE-agent | true | 23 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 23 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-gpt2-codegolf-a45f0491` | mini-SWE-agent | false | 20 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 20 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-grid-pattern-transform-7fdf43cd` | mini-SWE-agent | true | 13 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 13 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-hf-lora-adapter-fb92a979` | mini-SWE-agent | true | 31 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 31 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-hf-model-inference-08550b89` | mini-SWE-agent | false | 49 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 49 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-hf-train-lora-adapter-6c392546` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-home-server-https-f65d0c33` | mini-SWE-agent | true | 21 | source-valid | miniswe-message-trajectory; 21 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-implement-eigenvectors-from-eigenvalues-research-paper-c660a258` | mini-SWE-agent | false | 24 | excluded | miniswe-agent-log-markers emitted 20 operations; public step_count is 24 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-incompatible-python-fasttext-25fc2c1b` | mini-SWE-agent | false | 13 | source-valid | miniswe-message-trajectory; 13 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-install-windows-3.11-161e2118` | mini-SWE-agent | false | 64 | source-valid | miniswe-message-trajectory; 64 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-install-windows-xp-0c5af86d` | mini-SWE-agent | false | 22 | source-valid | miniswe-message-trajectory; 22 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-interactive-maze-game-4fea1d0d` | mini-SWE-agent | false | 13 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 13 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-intrusion-detection-4f7d2c3e` | mini-SWE-agent | false | 26 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 26 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-jq-data-processing-89efbbc6` | mini-SWE-agent | true | 14 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-jupyter-notebook-server-8a2dfe35` | mini-SWE-agent | true | 21 | excluded | miniswe-agent-log-markers emitted 23 operations; public step_count is 21 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-kv-store-grpc-11d37ef8` | mini-SWE-agent | false | 13 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 13 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-large-scale-text-editing-b9ba73da` | mini-SWE-agent | false | 15 | excluded | miniswe-agent-log-markers emitted 36 operations; public step_count is 15 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-largest-eigenval-ad802628` | mini-SWE-agent | false | 30 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 30 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-lean4-proof-06704755` | mini-SWE-agent | false | 77 | excluded | miniswe-agent-log-markers emitted 55 operations; public step_count is 77 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-leelachess0-pytorch-conversion-83112391` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-llm-inference-batching-scheduler-ef87b315` | mini-SWE-agent | false | 36 | excluded | miniswe-agent-log-markers emitted 32 operations; public step_count is 36 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-llm-spec-decoding-ae5dfebf` | mini-SWE-agent | false | 19 | source-valid | miniswe-message-trajectory; 19 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-log-summary-date-ranges-77de9e87` | mini-SWE-agent | false | 13 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 13 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-mahjong-winninghand-74a4ae76` | mini-SWE-agent | true | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-mailman-c45b6c8c` | mini-SWE-agent | false | 38 | excluded | miniswe-agent-log-markers emitted 75 operations; public step_count is 38 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-make-mips-interpreter-2789cd11` | mini-SWE-agent | false | 40 | excluded | miniswe-agent-log-markers emitted 28 operations; public step_count is 40 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-matlab-python-conversion-c0b9af5f` | mini-SWE-agent | false | 23 | excluded | miniswe-agent-log-markers emitted 14 operations; public step_count is 23 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-mcmc-sampling-stan-d8e97bde` | mini-SWE-agent | false | 35 | source-valid | miniswe-message-trajectory; 35 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-merge-diff-arc-agi-task-218b2cb5` | mini-SWE-agent | true | 21 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 21 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-mlflow-register-201f01b6` | mini-SWE-agent | false | 18 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 18 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-mnist-learning-fix-f10d2179` | mini-SWE-agent | false | 11 | excluded | miniswe-agent-log-markers emitted 2 operations; public step_count is 11 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-modernize-fortran-build-5b0228e3` | mini-SWE-agent | false | 12 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 12 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-modernize-scientific-stack-b241aa8d` | mini-SWE-agent | true | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-movie-helper-785aeaea` | mini-SWE-agent | false | 14 | source-valid | miniswe-message-trajectory; 14 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-mteb-eval-2a3d7eed` | mini-SWE-agent | true | 28 | source-valid | miniswe-message-trajectory; 28 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-mteb-retrieve-5e57faf8` | mini-SWE-agent | false | 35 | source-valid | miniswe-message-trajectory; 35 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-multi-source-data-merger-f2a9c694` | mini-SWE-agent | true | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-neuron-to-jaxley-conversion-7e5bdc97` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-nginx-request-logging-c24b5493` | mini-SWE-agent | true | 14 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-npm-conflict-resolution-18e65e6f` | mini-SWE-agent | false | 30 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 30 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-oom-eb82d9be` | mini-SWE-agent | false | 59 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 59 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-optimal-transport-51dd01da` | mini-SWE-agent | false | 26 | excluded | miniswe-agent-log-markers emitted 6 operations; public step_count is 26 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-organization-json-generator-26e78e8f` | mini-SWE-agent | true | 13 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 13 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-overfull-hbox-50d677a0` | mini-SWE-agent | false | 42 | excluded | miniswe-agent-log-markers emitted 28 operations; public step_count is 42 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-parallelize-compute-squares-f5e8d692` | mini-SWE-agent | true | 27 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 27 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-parallelize-graph-75796577` | mini-SWE-agent | false | 39 | source-valid | miniswe-message-trajectory; 39 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-password-recovery-3f06a142` | mini-SWE-agent | false | 29 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 29 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-path-tracing-a559409e` | mini-SWE-agent | false | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-path-tracing-reverse-14afb007` | mini-SWE-agent | false | 43 | excluded | miniswe-agent-log-markers emitted 40 operations; public step_count is 43 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-play-lord-53d1f0a7` | mini-SWE-agent | true | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-play-zork-6665d696` | mini-SWE-agent | false | 37 | source-valid | miniswe-message-trajectory; 37 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-play-zork-easy-a2e46e48` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-polyglot-c-py-42e51e25` | mini-SWE-agent | false | 83 | excluded | miniswe-agent-log-markers emitted 22 operations; public step_count is 83 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-polyglot-rust-c-20cc77a5` | mini-SWE-agent | false | 61 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 61 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-port-compressor-b025b7a7` | mini-SWE-agent | false | 117 | source-valid | miniswe-message-trajectory; 117 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-portfolio-optimization-7632e578` | mini-SWE-agent | true | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-postgres-csv-clean-e22cf4c8` | mini-SWE-agent | true | 14 | excluded | MiniSWE archive has neither sessions/agent.log nor .traj.json |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-protein-assembly-6441f13c` | mini-SWE-agent | false | 27 | source-valid | miniswe-message-trajectory; 27 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-puzzle-solver-00e0eac6` | mini-SWE-agent | false | 17 | source-valid | miniswe-message-trajectory; 17 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-pypi-server-24d7c501` | mini-SWE-agent | false | 48 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 48 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-pytorch-model-cli-c88dbb1b` | mini-SWE-agent | false | 29 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 29 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-pytorch-model-recovery-81427dc2` | mini-SWE-agent | false | 27 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 27 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-query-optimize-75f46f15` | mini-SWE-agent | false | 13 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 13 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-raman-fitting-b700ead8` | mini-SWE-agent | false | 14 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-rare-mineral-allocation-2c6edd65` | mini-SWE-agent | false | 16 | source-valid | miniswe-message-trajectory; 16 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-recover-obfuscated-files-9c9c0518` | mini-SWE-agent | true | 13 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 13 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-regex-chess-a64080d8` | mini-SWE-agent | false | 26 | source-valid | miniswe-message-trajectory; 26 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-reshard-c4-data-1c76bad2` | mini-SWE-agent | false | 44 | source-valid | miniswe-message-trajectory; 44 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-run-pdp11-code-43ec227b` | mini-SWE-agent | false | 85 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 85 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-sam-cell-seg-e93c2148` | mini-SWE-agent | false | 46 | source-valid | miniswe-message-trajectory; 46 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-sanitize-git-repo-7f6f65ba` | mini-SWE-agent | false | 25 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 25 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-schedule-vacation-b433dc37` | mini-SWE-agent | false | 15 | source-valid | miniswe-message-trajectory; 15 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-schemelike-metacircular-eval-83783b1b` | mini-SWE-agent | true | 58 | excluded | miniswe-agent-log-markers emitted 44 operations; public step_count is 58 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-security-celery-redis-rce-1745608a` | mini-SWE-agent | false | 18 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 18 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-setup-custom-dev-env-d2762300` | mini-SWE-agent | false | 31 | source-valid | miniswe-message-trajectory; 31 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-simple-sheets-put-be972826` | mini-SWE-agent | true | 25 | excluded | MiniSWE archive has neither sessions/agent.log nor .traj.json |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-solve-maze-challenge-0345b3b2` | mini-SWE-agent | false | 23 | source-valid | miniswe-message-trajectory; 23 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-solve-sudoku-e1fdbd0f` | mini-SWE-agent | false | 19 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 19 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-speech-to-text-a01463b4` | mini-SWE-agent | false | 35 | source-valid | miniswe-message-trajectory; 35 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-spinning-up-rl-4854ffa1` | mini-SWE-agent | true | 80 | excluded | miniswe-agent-log-markers emitted 123 operations; public step_count is 80 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-spring-messaging-vul-f4a09301` | mini-SWE-agent | false | 56 | excluded | miniswe-agent-log-markers emitted 32 operations; public step_count is 56 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-sql-injection-attack-5374e3bc` | mini-SWE-agent | true | 18 | source-valid | miniswe-message-trajectory; 18 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-sqlite-db-truncate-950bd36a` | mini-SWE-agent | false | 16 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 16 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-sqlite-with-gcov-5159b6b5` | mini-SWE-agent | false | 20 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 20 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-stable-parallel-kmeans-51f6bfde` | mini-SWE-agent | true | 27 | excluded | miniswe-agent-log-markers emitted 21 operations; public step_count is 27 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-sudo-llvm-ir-bd180d2d` | mini-SWE-agent | false | 49 | source-valid | miniswe-message-trajectory; 49 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-tmux-advanced-workflow-1eb47742` | mini-SWE-agent | true | 27 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 27 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-train-bpe-tokenizer-72f6b2bc` | mini-SWE-agent | true | 25 | source-valid | miniswe-message-trajectory; 25 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-train-fasttext-26f08c39` | mini-SWE-agent | false | 67 | source-valid | miniswe-message-trajectory; 67 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-tree-directory-parser-0290206a` | mini-SWE-agent | true | 13 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 13 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-triton-interpret-d8c76e46` | mini-SWE-agent | false | 29 | source-valid | miniswe-message-trajectory; 29 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-vertex-solver-80a7c040` | mini-SWE-agent | true | 24 | source-valid | miniswe-message-trajectory; 24 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-video-processing-b6a18b58` | mini-SWE-agent | false | 11 | source-valid | miniswe-message-trajectory; 11 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-vimscript-vim-quine-0cf13694` | mini-SWE-agent | false | 14 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-vul-flask-c7d1826d` | mini-SWE-agent | false | 41 | source-valid | miniswe-message-trajectory; 41 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-vul-flink-c97b8e23` | mini-SWE-agent | false | 47 | excluded | miniswe-agent-log-markers emitted 59 operations; public step_count is 47 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-weighted-max-sat-solver-6770c333` | mini-SWE-agent | false | 41 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 41 |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-winning-avg-corewars-702d0bfb` | mini-SWE-agent | false | 81 | source-valid | miniswe-message-trajectory; 81 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-word2vec-from-scratch-15c4b1f3` | mini-SWE-agent | false | 36 | source-valid | miniswe-message-trajectory; 36 operations |
| `miniswe-Qwen__Qwen3-Coder-480B-A35B-Instruct-write-compressor-f8cc3a8d` | mini-SWE-agent | false | 34 | excluded | miniswe-agent-log-markers emitted 0 operations; public step_count is 34 |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-3d-model-format-legacy-7498555b` | OpenHands | false | 95 | source-valid | openhands-agent-actions; 95 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-adaptive-rejection-sampler-749f8ad5` | OpenHands | false | 41 | source-valid | openhands-agent-actions; 41 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-add-benchmark-lm-eval-harness-9f75877e` | OpenHands | false | 80 | source-valid | openhands-agent-actions; 80 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-aimo-airline-departures-56d18bbc` | OpenHands | true | 15 | source-valid | openhands-agent-actions; 15 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-amuse-install-6b0697f5` | OpenHands | true | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-assign-seats-b9ac798d` | OpenHands | true | 15 | source-valid | openhands-agent-actions; 15 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-attention-mil-5bba2487` | OpenHands | false | 26 | source-valid | openhands-agent-actions; 26 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-audio-synth-stft-peaks-a7283b5d` | OpenHands | false | 24 | source-valid | openhands-agent-actions; 24 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-bank-trans-filter-88c6e5b2` | OpenHands | true | 12 | source-valid | openhands-agent-actions; 12 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-blind-maze-explorer-5x5-db993968` | OpenHands | false | 123 | source-valid | openhands-agent-actions; 123 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-blind-maze-explorer-algorithm-b6ce7393` | OpenHands | false | 72 | source-valid | openhands-agent-actions; 72 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-break-filter-js-from-html-05ef5f96` | OpenHands | false | 142 | source-valid | openhands-agent-actions; 142 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-cython-ext-c00c8af1` | OpenHands | false | 62 | source-valid | openhands-agent-actions; 62 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-initramfs-qemu-45e922c2` | OpenHands | false | 107 | source-valid | openhands-agent-actions; 107 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-linux-kernel-qemu-5128bb1f` | OpenHands | true | 35 | source-valid | openhands-agent-actions; 35 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-pmars-78f839aa` | OpenHands | false | 38 | source-valid | openhands-agent-actions; 38 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-pov-ray-aa2667f5` | OpenHands | false | 55 | source-valid | openhands-agent-actions; 55 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-stp-9be5a852` | OpenHands | true | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-tcc-qemu-4f52dea7` | OpenHands | false | 32 | source-valid | openhands-agent-actions; 32 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-caffe-cifar-10-11a22d9a` | OpenHands | false | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-cancel-async-tasks-7deaf6ad` | OpenHands | true | 11 | source-valid | openhands-agent-actions; 11 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-cartpole-rl-training-089b3013` | OpenHands | true | 40 | source-valid | openhands-agent-actions; 40 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-catch-me-if-you-can-c2d2330e` | OpenHands | false | 74 | source-valid | openhands-agent-actions; 74 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-causal-inference-r-02b24f07` | OpenHands | false | 32 | source-valid | openhands-agent-actions; 32 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-chem-property-targeting-db8bf4bf` | OpenHands | false | 27 | source-valid | openhands-agent-actions; 27 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-chem-rf-271f890f` | OpenHands | false | 31 | excluded | openhands-agent-actions emitted 59 operations; public step_count is 31 |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-chess-best-move-ae2da0e2` | OpenHands | false | 21 | source-valid | openhands-agent-actions; 21 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-circuit-fibsqrt-7639d534` | OpenHands | false | 69 | source-valid | openhands-agent-actions; 69 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-cobol-modernization-8c5ddff7` | OpenHands | true | 65 | source-valid | openhands-agent-actions; 65 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-code-from-image-daf9d1a8` | OpenHands | true | 25 | source-valid | openhands-agent-actions; 25 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-compile-compcert-e48a0f89` | OpenHands | false | 34 | source-valid | openhands-agent-actions; 34 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-conda-env-conflict-resolution-4a146c72` | OpenHands | false | 16 | source-valid | openhands-agent-actions; 16 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-configure-git-webserver-e1c8949e` | OpenHands | false | 17 | source-valid | openhands-agent-actions; 17 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-count-call-stack-54540f32` | OpenHands | false | 26 | source-valid | openhands-agent-actions; 26 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-count-dataset-tokens-c353100a` | OpenHands | false | 32 | source-valid | openhands-agent-actions; 32 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-cprofiling-python-591d66e2` | OpenHands | true | 30 | source-valid | openhands-agent-actions; 30 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-cron-broken-network-890c63e8` | OpenHands | false | 57 | source-valid | openhands-agent-actions; 57 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-cross-entropy-method-490edaee` | OpenHands | true | 38 | source-valid | openhands-agent-actions; 38 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-csv-to-parquet-e48180a3` | OpenHands | true | 24 | source-valid | openhands-agent-actions; 24 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-db-wal-recovery-644b805f` | OpenHands | false | 48 | source-valid | openhands-agent-actions; 48 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-decommissioning-service-with-sensitive-data-2acf97b7` | OpenHands | true | 12 | source-valid | openhands-agent-actions; 12 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-deterministic-tarball-860410c3` | OpenHands | false | 36 | source-valid | openhands-agent-actions; 36 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-distribution-search-b2092e02` | OpenHands | false | 37 | source-valid | openhands-agent-actions; 37 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-dna-assembly-0b52e274` | OpenHands | false | 39 | source-valid | openhands-agent-actions; 39 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-download-youtube-37bde7e4` | OpenHands | false | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-extract-elf-9337b07a` | OpenHands | false | 30 | source-valid | openhands-agent-actions; 30 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-extract-moves-from-video-4521cfe7` | OpenHands | false | 25 | source-valid | openhands-agent-actions; 25 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-feal-differential-cryptanalysis-631ccdce` | OpenHands | false | 43 | source-valid | openhands-agent-actions; 43 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-feal-linear-cryptanalysis-00bae408` | OpenHands | false | 60 | source-valid | openhands-agent-actions; 60 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-fibonacci-server-89ec6d06` | OpenHands | true | 41 | source-valid | openhands-agent-actions; 41 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-filter-js-from-html-a48842a8` | OpenHands | false | 36 | source-valid | openhands-agent-actions; 36 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-financial-document-processor-0aab1705` | OpenHands | false | 16 | source-valid | openhands-agent-actions; 16 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-find-official-code-1f9dd1a4` | OpenHands | false | 12 | source-valid | openhands-agent-actions; 12 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-fix-code-vulnerability-c1f4aa0b` | OpenHands | false | 51 | source-valid | openhands-agent-actions; 51 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-fix-git-3cb3d618` | OpenHands | true | 13 | source-valid | openhands-agent-actions; 13 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-fix-ocaml-gc-b3da4a79` | OpenHands | false | 97 | source-valid | openhands-agent-actions; 97 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-fix-pandas-version-f8e90ad6` | OpenHands | false | 25 | source-valid | openhands-agent-actions; 25 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-flood-monitoring-basic-4dd77334` | OpenHands | false | 14 | source-valid | openhands-agent-actions; 14 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-fmri-encoding-r-d8f8477a` | OpenHands | true | 21 | source-valid | openhands-agent-actions; 21 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-form-filling-00dc9b74` | OpenHands | true | 23 | source-valid | openhands-agent-actions; 23 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-gcc-compiler-optimization-e14676ee` | OpenHands | true | 14 | source-valid | openhands-agent-actions; 14 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-gcode-to-text-e94d907b` | OpenHands | false | 21 | source-valid | openhands-agent-actions; 21 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-get-bitcoin-nodes-a2fb108c` | OpenHands | false | 60 | source-valid | openhands-agent-actions; 60 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-git-leak-recovery-7e949936` | OpenHands | true | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-git-multibranch-75c1745e` | OpenHands | false | 119 | source-valid | openhands-agent-actions; 119 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-git-workflow-hack-81c64754` | OpenHands | true | 27 | source-valid | openhands-agent-actions; 27 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-gomoku-planner-2d5aae74` | OpenHands | true | 12 | source-valid | openhands-agent-actions; 12 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-gpt2-codegolf-4bd1b818` | OpenHands | false | 36 | source-valid | openhands-agent-actions; 36 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-grid-pattern-transform-d6878f19` | OpenHands | true | 16 | source-valid | openhands-agent-actions; 16 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-hdfs-deployment-16c47cdd` | OpenHands | true | 37 | source-valid | openhands-agent-actions; 37 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-hf-lora-adapter-c90d9524` | OpenHands | false | 26 | source-valid | openhands-agent-actions; 26 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-hf-model-inference-1520e16b` | OpenHands | false | 35 | excluded | openhands-agent-actions emitted 46 operations; public step_count is 35 |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-hf-train-lora-adapter-63f46819` | OpenHands | false | 45 | source-valid | openhands-agent-actions; 45 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-html-finance-verify-6045e4db` | OpenHands | false | 42 | source-valid | openhands-agent-actions; 42 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-huarong-dao-solver-001e407c` | OpenHands | false | 33 | source-valid | openhands-agent-actions; 33 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-hydra-debug-slurm-mode-a14c39ed` | OpenHands | false | 32 | source-valid | openhands-agent-actions; 32 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-implement-eigenvectors-from-eigenvalues-research-paper-2d980901` | OpenHands | false | 44 | source-valid | openhands-agent-actions; 44 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-incompatible-python-fasttext-ef5ae6b9` | OpenHands | false | 23 | source-valid | openhands-agent-actions; 23 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-install-klee-minimal-49bd58d7` | OpenHands | true | 59 | source-valid | openhands-agent-actions; 59 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-install-windows-3.11-2007e72c` | OpenHands | false | 62 | source-valid | openhands-agent-actions; 62 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-install-windows-xp-25f19d60` | OpenHands | false | 51 | source-valid | openhands-agent-actions; 51 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-intrusion-detection-a847d6de` | OpenHands | false | 56 | source-valid | openhands-agent-actions; 56 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-jq-data-processing-b86ee954` | OpenHands | true | 22 | source-valid | openhands-agent-actions; 22 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-jupyter-notebook-server-aa893107` | OpenHands | true | 18 | source-valid | openhands-agent-actions; 18 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-kv-store-grpc-f18b6169` | OpenHands | true | 40 | source-valid | openhands-agent-actions; 40 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-large-scale-text-editing-796163f1` | OpenHands | true | 34 | source-valid | openhands-agent-actions; 34 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-largest-eigenval-739899c6` | OpenHands | false | 44 | source-valid | openhands-agent-actions; 44 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-lean4-proof-c2cf74ba` | OpenHands | false | 82 | excluded | openhands-agent-actions emitted 91 operations; public step_count is 82 |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-leelachess0-pytorch-conversion-46d95888` | OpenHands | false | 41 | source-valid | openhands-agent-actions; 41 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-llm-inference-batching-scheduler-d547af08` | OpenHands | false | 35 | source-valid | openhands-agent-actions; 35 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-llm-spec-decoding-8e6aad94` | OpenHands | false | 22 | source-valid | openhands-agent-actions; 22 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-log-summary-a4fdafa1` | OpenHands | true | 11 | source-valid | openhands-agent-actions; 11 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-logistic-regression-divergence-2a351393` | OpenHands | true | 37 | source-valid | openhands-agent-actions; 37 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-magsac-install-67eb3320` | OpenHands | false | 87 | source-valid | openhands-agent-actions; 87 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-mahjong-winninghand-60b3cef0` | OpenHands | true | 16 | source-valid | openhands-agent-actions; 16 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-mailman-80c30dc0` | OpenHands | true | 98 | source-valid | openhands-agent-actions; 98 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-make-doom-for-mips-3a56a80c` | OpenHands | false | 61 | source-valid | openhands-agent-actions; 61 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-mcmc-sampling-stan-d086f33d` | OpenHands | false | 26 | source-valid | openhands-agent-actions; 26 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-merge-diff-arc-agi-task-30935034` | OpenHands | true | 25 | source-valid | openhands-agent-actions; 25 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-mixed-integer-programming-2ccf7a76` | OpenHands | true | 22 | source-valid | openhands-agent-actions; 22 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-mlflow-register-f7452f92` | OpenHands | true | 33 | source-valid | openhands-agent-actions; 33 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-model-extraction-relu-logits-168c2ca5` | OpenHands | true | 29 | source-valid | openhands-agent-actions; 29 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-modernize-fortran-build-dba8e93d` | OpenHands | true | 11 | source-valid | openhands-agent-actions; 11 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-modernize-scientific-stack-2c3ae44d` | OpenHands | true | 11 | source-valid | openhands-agent-actions; 11 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-movie-helper-c4c70540` | OpenHands | false | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-mteb-eval-09ae8a74` | OpenHands | true | 30 | excluded | openhands-agent-actions emitted 38 operations; public step_count is 30 |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-mteb-retrieve-c75bcebb` | OpenHands | false | 25 | source-valid | openhands-agent-actions; 25 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-multi-source-data-merger-aaaf1d1f` | OpenHands | true | 45 | source-valid | openhands-agent-actions; 45 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-multistep-definite-integral-eec0af1c` | OpenHands | true | 15 | source-valid | openhands-agent-actions; 15 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-neuron-to-jaxley-conversion-5b6349c2` | OpenHands | false | 74 | source-valid | openhands-agent-actions; 74 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-new-encrypt-command-f27fdcce` | OpenHands | true | 12 | source-valid | openhands-agent-actions; 12 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-nginx-request-logging-770d4eda` | OpenHands | false | 33 | source-valid | openhands-agent-actions; 33 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-npm-conflict-resolution-bf7ddbf7` | OpenHands | false | 27 | source-valid | openhands-agent-actions; 27 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-ode-solver-rk4-891baea7` | OpenHands | true | 18 | source-valid | openhands-agent-actions; 18 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-oom-5c9a3c78` | OpenHands | true | 34 | source-valid | openhands-agent-actions; 34 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-openssl-selfsigned-cert-88ccb830` | OpenHands | false | 13 | source-valid | openhands-agent-actions; 13 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-optimal-transport-f0661450` | OpenHands | true | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-organization-json-generator-cc6ad1c4` | OpenHands | true | 14 | source-valid | openhands-agent-actions; 14 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-overfull-hbox-a29d9401` | OpenHands | false | 56 | source-valid | openhands-agent-actions; 56 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-pandas-sql-query-32787288` | OpenHands | true | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-parallel-particle-simulator-6cd5c6fc` | OpenHands | false | 45 | source-valid | openhands-agent-actions; 45 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-parallelize-compute-squares-b6750975` | OpenHands | true | 22 | source-valid | openhands-agent-actions; 22 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-parallelize-graph-b2e64469` | OpenHands | true | 70 | source-valid | openhands-agent-actions; 70 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-password-recovery-fc298505` | OpenHands | false | 59 | source-valid | openhands-agent-actions; 59 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-path-tracing-8cc10d94` | OpenHands | false | 47 | source-valid | openhands-agent-actions; 47 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-pcap-to-netflow-d8c1ec6c` | OpenHands | false | 66 | source-valid | openhands-agent-actions; 66 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-play-zork-8f01e62d` | OpenHands | false | 85 | source-valid | openhands-agent-actions; 85 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-play-zork-easy-8fb6fd55` | OpenHands | false | 74 | source-valid | openhands-agent-actions; 74 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-polyglot-c-py-44493e80` | OpenHands | false | 67 | source-valid | openhands-agent-actions; 67 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-polyglot-rust-c-4df91451` | OpenHands | false | 379 | source-valid | openhands-agent-actions; 379 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-port-compressor-7b89f014` | OpenHands | false | 89 | source-valid | openhands-agent-actions; 89 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-portfolio-optimization-ce11b5df` | OpenHands | false | 58 | source-valid | openhands-agent-actions; 58 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-predicate-pushdown-bench-d779a890` | OpenHands | false | 42 | source-valid | openhands-agent-actions; 42 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-predict-customer-churn-d58fa4e0` | OpenHands | false | 25 | source-valid | openhands-agent-actions; 25 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-processing-pipeline-75a87f10` | OpenHands | true | 23 | source-valid | openhands-agent-actions; 23 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-protein-assembly-82a1e09e` | OpenHands | false | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-protocol-analysis-rs-64c566cd` | OpenHands | false | 86 | source-valid | openhands-agent-actions; 86 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-prove-plus-comm-4b1a67fa` | OpenHands | true | 17 | source-valid | openhands-agent-actions; 17 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-puzzle-solver-a3fa8891` | OpenHands | false | 26 | source-valid | openhands-agent-actions; 26 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-pypi-server-b0e415c9` | OpenHands | false | 34 | source-valid | openhands-agent-actions; 34 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-pytorch-model-cli-812bb06f` | OpenHands | false | 56 | source-valid | openhands-agent-actions; 56 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-pytorch-model-recovery-de100977` | OpenHands | false | 17 | source-valid | openhands-agent-actions; 17 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-query-optimize-40b60713` | OpenHands | true | 15 | source-valid | openhands-agent-actions; 15 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-raman-fitting-87e0e128` | OpenHands | false | 23 | source-valid | openhands-agent-actions; 23 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-rare-mineral-allocation-0ca2144e` | OpenHands | false | 22 | source-valid | openhands-agent-actions; 22 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-recover-accuracy-log-746a7615` | OpenHands | true | 17 | source-valid | openhands-agent-actions; 17 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-recover-obfuscated-files-155a474f` | OpenHands | true | 14 | source-valid | openhands-agent-actions; 14 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-regex-chess-270779f5` | OpenHands | false | 55 | source-valid | openhands-agent-actions; 55 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-reshard-c4-data-7e4ba322` | OpenHands | false | 29 | source-valid | openhands-agent-actions; 29 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-reverse-engineering-bbdd57de` | OpenHands | false | 217 | source-valid | openhands-agent-actions; 217 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-rstan-to-pystan-c34299ab` | OpenHands | false | 17 | source-valid | openhands-agent-actions; 17 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-run-pdp11-code-75d04a72` | OpenHands | false | 49 | source-valid | openhands-agent-actions; 49 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-sam-cell-seg-d845cb97` | OpenHands | false | 49 | source-valid | openhands-agent-actions; 49 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-schedule-vacation-862edca6` | OpenHands | true | 21 | source-valid | openhands-agent-actions; 21 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-schemelike-metacircular-eval-b2756460` | OpenHands | false | 62 | source-valid | openhands-agent-actions; 62 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-setup-custom-dev-env-db035eef` | OpenHands | true | 53 | source-valid | openhands-agent-actions; 53 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-solana-data-c854dc09` | OpenHands | false | 52 | source-valid | openhands-agent-actions; 52 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-solve-maze-challenge-d691577e` | OpenHands | false | 64 | source-valid | openhands-agent-actions; 64 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-solve-sudoku-4d89f6c5` | OpenHands | false | 29 | source-valid | openhands-agent-actions; 29 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-sparql-university-b03ba08d` | OpenHands | false | 11 | source-valid | openhands-agent-actions; 11 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-speech-to-text-2c3cbfec` | OpenHands | true | 23 | source-valid | openhands-agent-actions; 23 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-spinning-up-rl-0f12c5b3` | OpenHands | false | 54 | source-valid | openhands-agent-actions; 54 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-sqlite-db-truncate-3b6f6b3d` | OpenHands | false | 17 | source-valid | openhands-agent-actions; 17 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-sqlite-with-gcov-7e98b551` | OpenHands | false | 19 | source-valid | openhands-agent-actions; 19 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-stable-parallel-kmeans-e1b5afd5` | OpenHands | true | 39 | source-valid | openhands-agent-actions; 39 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-sudo-llvm-ir-ae15d02f` | OpenHands | false | 110 | source-valid | openhands-agent-actions; 110 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-swe-bench-astropy-1-dd62e491` | OpenHands | true | 42 | source-valid | openhands-agent-actions; 42 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-swe-bench-astropy-2-0487a214` | OpenHands | false | 37 | source-valid | openhands-agent-actions; 37 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-swe-bench-fsspec-41aac8af` | OpenHands | true | 66 | source-valid | openhands-agent-actions; 66 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-swe-bench-langcodes-3d08d6ec` | OpenHands | true | 30 | source-valid | openhands-agent-actions; 30 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-tmux-advanced-workflow-90785e8a` | OpenHands | true | 26 | source-valid | openhands-agent-actions; 26 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-torch-pipeline-parallelism-53c3a1e6` | OpenHands | false | 40 | source-valid | openhands-agent-actions; 40 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-torch-tensor-parallelism-94051bef` | OpenHands | false | 23 | source-valid | openhands-agent-actions; 23 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-train-fasttext-b326259b` | OpenHands | false | 47 | excluded | openhands-agent-actions emitted 57 operations; public step_count is 47 |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-tree-directory-parser-005b0d76` | OpenHands | true | 38 | source-valid | openhands-agent-actions; 38 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-triton-interpret-1cede581` | OpenHands | false | 61 | source-valid | openhands-agent-actions; 61 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-tune-mjcf-9828b85f` | OpenHands | false | 191 | source-valid | openhands-agent-actions; 191 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-vertex-solver-19ac64da` | OpenHands | true | 14 | source-valid | openhands-agent-actions; 14 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-video-processing-ad7a8d55` | OpenHands | false | 39 | source-valid | openhands-agent-actions; 39 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-vimscript-vim-quine-cfb81b83` | OpenHands | false | 15 | source-valid | openhands-agent-actions; 15 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-vul-flask-742d72cc` | OpenHands | false | 46 | source-valid | openhands-agent-actions; 46 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-vul-flink-5f12417a` | OpenHands | false | 45 | source-valid | openhands-agent-actions; 45 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-vulnerable-secret-dac67572` | OpenHands | false | 95 | source-valid | openhands-agent-actions; 95 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-wasm-pipeline-cab89c8b` | OpenHands | false | 29 | source-valid | openhands-agent-actions; 29 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-weighted-max-sat-solver-812d2c67` | OpenHands | false | 30 | source-valid | openhands-agent-actions; 30 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-winning-avg-corewars-b5abf62e` | OpenHands | false | 113 | source-valid | openhands-agent-actions; 113 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-word2vec-from-scratch-fcdb2b0a` | OpenHands | false | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-write-compressor-7f8784b2` | OpenHands | false | 47 | source-valid | openhands-agent-actions; 47 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-3d-model-format-legacy-109d1beb` | OpenHands | false | 73 | excluded | openhands-agent-actions emitted 75 operations; public step_count is 73 |
| `openhands-DeepSeek__DeepSeek-V3.2-acl-permissions-inheritance-2ec77e08` | OpenHands | false | 34 | source-valid | openhands-agent-actions; 34 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-adaptive-rejection-sampler-5191debf` | OpenHands | false | 47 | excluded | openhands-agent-actions emitted 49 operations; public step_count is 47 |
| `openhands-DeepSeek__DeepSeek-V3.2-add-benchmark-lm-eval-harness-f672ceba` | OpenHands | false | 85 | excluded | openhands-agent-actions emitted 86 operations; public step_count is 85 |
| `openhands-DeepSeek__DeepSeek-V3.2-aimo-airline-departures-031d1188` | OpenHands | true | 23 | source-valid | openhands-agent-actions; 23 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-amuse-install-4d9725f6` | OpenHands | true | 28 | source-valid | openhands-agent-actions; 28 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-analyze-access-logs-bd67be51` | OpenHands | true | 15 | source-valid | openhands-agent-actions; 15 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-assign-seats-d8334616` | OpenHands | true | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-attention-mil-85c42ee5` | OpenHands | false | 52 | source-valid | openhands-agent-actions; 52 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-audio-synth-stft-peaks-ea5040fb` | OpenHands | false | 57 | excluded | missing archive |
| `openhands-DeepSeek__DeepSeek-V3.2-bank-trans-filter-68aa2b21` | OpenHands | true | 37 | source-valid | openhands-agent-actions; 37 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-blind-maze-explorer-5x5-3f7ee417` | OpenHands | true | 55 | source-valid | openhands-agent-actions; 55 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-blind-maze-explorer-algorithm-8e1e19bd` | OpenHands | true | 52 | source-valid | openhands-agent-actions; 52 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-break-filter-js-from-html-eb19b6bc` | OpenHands | false | 100 | excluded | missing archive |
| `openhands-DeepSeek__DeepSeek-V3.2-broken-python-89e8484d` | OpenHands | true | 34 | source-valid | openhands-agent-actions; 34 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-build-cython-ext-0851201d` | OpenHands | false | 105 | source-valid | openhands-agent-actions; 105 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-build-initramfs-qemu-f6d2392d` | OpenHands | false | 45 | source-valid | openhands-agent-actions; 45 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-build-linux-kernel-qemu-338ec29e` | OpenHands | true | 41 | source-valid | openhands-agent-actions; 41 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-build-pmars-fa5a7cae` | OpenHands | true | 40 | source-valid | openhands-agent-actions; 40 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-build-pov-ray-daac7d7c` | OpenHands | false | 69 | source-valid | openhands-agent-actions; 69 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-build-stp-4cb58bcf` | OpenHands | true | 29 | source-valid | openhands-agent-actions; 29 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-build-tcc-qemu-0af21736` | OpenHands | false | 55 | source-valid | openhands-agent-actions; 55 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-caffe-cifar-10-f7852850` | OpenHands | false | 35 | excluded | openhands-agent-actions emitted 46 operations; public step_count is 35 |
| `openhands-DeepSeek__DeepSeek-V3.2-cancel-async-tasks-fd464cf2` | OpenHands | false | 25 | source-valid | openhands-agent-actions; 25 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-cartpole-rl-training-ce5a478b` | OpenHands | true | 63 | source-valid | openhands-agent-actions; 63 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-catch-me-if-you-can-1fed6f6f` | OpenHands | false | 102 | source-valid | openhands-agent-actions; 102 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-causal-inference-r-7fe0b56f` | OpenHands | false | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-chem-property-targeting-a5c0ce17` | OpenHands | true | 34 | source-valid | openhands-agent-actions; 34 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-chem-rf-43d5d989` | OpenHands | false | 56 | source-valid | openhands-agent-actions; 56 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-chess-best-move-c23a9213` | OpenHands | false | 62 | source-valid | openhands-agent-actions; 62 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-circuit-fibsqrt-40e6477a` | OpenHands | false | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-classifier-debug-0b0fdb32` | OpenHands | true | 38 | source-valid | openhands-agent-actions; 38 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-cobol-modernization-80c586a8` | OpenHands | true | 64 | source-valid | openhands-agent-actions; 64 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-code-from-image-f40ccecb` | OpenHands | true | 27 | source-valid | openhands-agent-actions; 27 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-compile-compcert-94fdfa2e` | OpenHands | true | 77 | source-valid | openhands-agent-actions; 77 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-conda-env-conflict-resolution-1e3d7b6a` | OpenHands | true | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-configure-git-webserver-c8053c61` | OpenHands | true | 28 | source-valid | openhands-agent-actions; 28 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-constraints-scheduling-da7103f2` | OpenHands | true | 18 | source-valid | openhands-agent-actions; 18 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-count-call-stack-6c3a9f8a` | OpenHands | false | 27 | source-valid | openhands-agent-actions; 27 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-count-dataset-tokens-19cd9829` | OpenHands | true | 41 | source-valid | openhands-agent-actions; 41 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-cpp-compatibility-a40d907c` | OpenHands | true | 52 | source-valid | openhands-agent-actions; 52 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-cprofiling-python-0f4c8b60` | OpenHands | false | 76 | source-valid | openhands-agent-actions; 76 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-create-bucket-692a44f3` | OpenHands | true | 19 | source-valid | openhands-agent-actions; 19 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-cron-broken-network-e939fef2` | OpenHands | false | 88 | source-valid | openhands-agent-actions; 88 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-cross-entropy-method-5d3f18d2` | OpenHands | true | 35 | excluded | openhands-agent-actions emitted 39 operations; public step_count is 35 |
| `openhands-DeepSeek__DeepSeek-V3.2-csv-to-parquet-0249f56f` | OpenHands | true | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-db-wal-recovery-2063f818` | OpenHands | false | 85 | excluded | missing archive |
| `openhands-DeepSeek__DeepSeek-V3.2-debug-long-program-588031ea` | OpenHands | false | 62 | source-valid | openhands-agent-actions; 62 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-decommissioning-service-with-sensitive-data-8980b612` | OpenHands | true | 21 | source-valid | openhands-agent-actions; 21 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-deterministic-tarball-2c88c6f7` | OpenHands | false | 35 | source-valid | openhands-agent-actions; 35 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-distribution-search-5fcbf135` | OpenHands | false | 64 | source-valid | openhands-agent-actions; 64 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-dna-assembly-1d47c200` | OpenHands | false | 35 | excluded | openhands-agent-actions emitted 40 operations; public step_count is 35 |
| `openhands-DeepSeek__DeepSeek-V3.2-dna-insert-61172a8a` | OpenHands | false | 37 | source-valid | openhands-agent-actions; 37 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-download-youtube-ccc7101d` | OpenHands | false | 39 | source-valid | openhands-agent-actions; 39 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-enemy-grid-escape-5bab34b9` | OpenHands | false | 48 | excluded | openhands-agent-actions emitted 56 operations; public step_count is 48 |
| `openhands-DeepSeek__DeepSeek-V3.2-extract-elf-bf701930` | OpenHands | true | 46 | source-valid | openhands-agent-actions; 46 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-extract-moves-from-video-00609d24` | OpenHands | false | 32 | source-valid | openhands-agent-actions; 32 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-feal-differential-cryptanalysis-5a64f808` | OpenHands | false | 35 | excluded | openhands-agent-actions emitted 47 operations; public step_count is 35 |
| `openhands-DeepSeek__DeepSeek-V3.2-feal-linear-cryptanalysis-14fb24e5` | OpenHands | true | 39 | source-valid | openhands-agent-actions; 39 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-fibonacci-server-b246383b` | OpenHands | true | 43 | excluded | missing archive |
| `openhands-DeepSeek__DeepSeek-V3.2-filter-js-from-html-0661aa2d` | OpenHands | false | 54 | excluded | missing archive |
| `openhands-DeepSeek__DeepSeek-V3.2-financial-document-processor-39cf7cca` | OpenHands | false | 54 | source-valid | openhands-agent-actions; 54 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-find-official-code-cc5bd45a` | OpenHands | false | 45 | source-valid | openhands-agent-actions; 45 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-fix-code-vulnerability-10de86e2` | OpenHands | false | 60 | source-valid | openhands-agent-actions; 60 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-fix-git-5818b546` | OpenHands | true | 25 | source-valid | openhands-agent-actions; 25 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-fix-ocaml-gc-a1db547c` | OpenHands | false | 71 | source-valid | openhands-agent-actions; 71 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-fix-pandas-version-d18fcc58` | OpenHands | false | 47 | source-valid | openhands-agent-actions; 47 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-fix-permissions-8e0b6dc2` | OpenHands | true | 18 | source-valid | openhands-agent-actions; 18 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-flood-monitoring-basic-d6133d9e` | OpenHands | true | 26 | source-valid | openhands-agent-actions; 26 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-fmri-encoding-r-cbdd13da` | OpenHands | true | 17 | source-valid | openhands-agent-actions; 17 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-form-filling-be6eb257` | OpenHands | true | 60 | source-valid | openhands-agent-actions; 60 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-gcc-compiler-optimization-70df4da5` | OpenHands | true | 25 | source-valid | openhands-agent-actions; 25 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-gcode-to-text-84e524b7` | OpenHands | false | 37 | source-valid | openhands-agent-actions; 37 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-get-bitcoin-nodes-4cb80bf9` | OpenHands | false | 89 | excluded | missing archive |
| `openhands-DeepSeek__DeepSeek-V3.2-git-leak-recovery-76a8fe75` | OpenHands | true | 58 | source-valid | openhands-agent-actions; 58 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-git-multibranch-0bbc5d81` | OpenHands | false | 95 | source-valid | openhands-agent-actions; 95 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-git-workflow-hack-4b497bc9` | OpenHands | true | 45 | source-valid | openhands-agent-actions; 45 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-gomoku-planner-debdd5d9` | OpenHands | true | 18 | source-valid | openhands-agent-actions; 18 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-gpt2-codegolf-f44fab2d` | OpenHands | false | 54 | source-valid | openhands-agent-actions; 54 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-grid-pattern-transform-ce641a42` | OpenHands | true | 35 | excluded | missing archive |
| `openhands-DeepSeek__DeepSeek-V3.2-hdfs-deployment-d6129d1c` | OpenHands | true | 51 | source-valid | openhands-agent-actions; 51 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-hf-lora-adapter-2634042d` | OpenHands | false | 34 | source-valid | openhands-agent-actions; 34 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-hf-model-inference-a01a8182` | OpenHands | true | 36 | source-valid | openhands-agent-actions; 36 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-hf-train-lora-adapter-4d4034d9` | OpenHands | false | 45 | source-valid | openhands-agent-actions; 45 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-html-finance-verify-9909b60b` | OpenHands | false | 73 | source-valid | openhands-agent-actions; 73 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-huarong-dao-solver-7243dd2b` | OpenHands | true | 43 | source-valid | openhands-agent-actions; 43 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-hydra-debug-slurm-mode-86671449` | OpenHands | true | 52 | source-valid | openhands-agent-actions; 52 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-ilp-solver-bb0fa0b9` | OpenHands | true | 28 | source-valid | openhands-agent-actions; 28 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-implement-eigenvectors-from-eigenvalues-research-paper-9e960b82` | OpenHands | false | 68 | source-valid | openhands-agent-actions; 68 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-incompatible-python-fasttext-2e2b3c4d` | OpenHands | false | 30 | source-valid | openhands-agent-actions; 30 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-install-klee-minimal-810f8e5e` | OpenHands | true | 47 | source-valid | openhands-agent-actions; 47 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-install-windows-3.11-17800883` | OpenHands | false | 75 | excluded | missing archive |
| `openhands-DeepSeek__DeepSeek-V3.2-install-windows-xp-6370aa03` | OpenHands | false | 88 | source-valid | openhands-agent-actions; 88 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-interactive-maze-game-bd99931a` | OpenHands | false | 49 | source-valid | openhands-agent-actions; 49 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-intrusion-detection-58145a06` | OpenHands | false | 97 | source-valid | openhands-agent-actions; 97 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-jq-data-processing-b272154e` | OpenHands | true | 27 | source-valid | openhands-agent-actions; 27 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-jsonl-aggregator-8dc0c28a` | OpenHands | true | 14 | source-valid | openhands-agent-actions; 14 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-jupyter-notebook-server-fce0f43e` | OpenHands | true | 49 | source-valid | openhands-agent-actions; 49 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-kv-store-grpc-4ab61c80` | OpenHands | false | 57 | source-valid | openhands-agent-actions; 57 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-large-scale-text-editing-ada47367` | OpenHands | true | 41 | source-valid | openhands-agent-actions; 41 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-largest-eigenval-d5360284` | OpenHands | false | 85 | excluded | missing archive |
| `openhands-DeepSeek__DeepSeek-V3.2-lean4-proof-313ecb3f` | OpenHands | false | 73 | excluded | openhands-agent-actions emitted 83 operations; public step_count is 73 |
| `openhands-DeepSeek__DeepSeek-V3.2-leelachess0-pytorch-conversion-1f4ed487` | OpenHands | false | 60 | excluded | openhands-agent-actions emitted 70 operations; public step_count is 60 |
| `openhands-DeepSeek__DeepSeek-V3.2-llm-inference-batching-scheduler-bb7aecc5` | OpenHands | false | 48 | excluded | openhands-agent-actions emitted 51 operations; public step_count is 48 |
| `openhands-DeepSeek__DeepSeek-V3.2-llm-spec-decoding-d2946505` | OpenHands | false | 49 | source-valid | openhands-agent-actions; 49 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-log-summary-date-ranges-8edecc55` | OpenHands | true | 13 | source-valid | openhands-agent-actions; 13 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-log-summary-f91a5f53` | OpenHands | true | 18 | source-valid | openhands-agent-actions; 18 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-logistic-regression-divergence-dfdc4fb6` | OpenHands | false | 23 | excluded | openhands-agent-actions emitted 30 operations; public step_count is 23 |
| `openhands-DeepSeek__DeepSeek-V3.2-magsac-install-63c12ff1` | OpenHands | false | 73 | excluded | openhands-agent-actions emitted 76 operations; public step_count is 73 |
| `openhands-DeepSeek__DeepSeek-V3.2-mahjong-winninghand-b5fcc74f` | OpenHands | true | 33 | source-valid | openhands-agent-actions; 33 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-mailman-889bf402` | OpenHands | true | 86 | source-valid | openhands-agent-actions; 86 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-make-doom-for-mips-9ce00f74` | OpenHands | false | 89 | source-valid | openhands-agent-actions; 89 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-make-mips-interpreter-45083164` | OpenHands | false | 60 | excluded | openhands-agent-actions emitted 68 operations; public step_count is 60 |
| `openhands-DeepSeek__DeepSeek-V3.2-mcmc-sampling-stan-93a53355` | OpenHands | true | 39 | source-valid | openhands-agent-actions; 39 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-merge-diff-arc-agi-task-dc402527` | OpenHands | true | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-mixed-integer-programming-b8149b32` | OpenHands | true | 52 | source-valid | openhands-agent-actions; 52 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-mlflow-register-cc51beb4` | OpenHands | false | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-modernize-fortran-build-34213634` | OpenHands | false | 22 | source-valid | openhands-agent-actions; 22 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-modernize-scientific-stack-dcec1eaa` | OpenHands | true | 22 | source-valid | openhands-agent-actions; 22 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-movie-helper-cfd11baf` | OpenHands | false | 38 | source-valid | openhands-agent-actions; 38 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-mteb-eval-a8094d7c` | OpenHands | false | 35 | source-valid | openhands-agent-actions; 35 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-mteb-leaderboard-04977425` | OpenHands | false | 34 | source-valid | openhands-agent-actions; 34 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-mteb-retrieve-d890d889` | OpenHands | false | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-multi-source-data-merger-250e898f` | OpenHands | true | 46 | source-valid | openhands-agent-actions; 46 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-multistep-definite-integral-4b48247b` | OpenHands | true | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-neuron-to-jaxley-conversion-e342c3ae` | OpenHands | false | 52 | excluded | missing archive |
| `openhands-DeepSeek__DeepSeek-V3.2-new-encrypt-command-513a5055` | OpenHands | true | 17 | source-valid | openhands-agent-actions; 17 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-nginx-request-logging-c6da64fc` | OpenHands | true | 32 | source-valid | openhands-agent-actions; 32 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-npm-conflict-resolution-3a6cd2bb` | OpenHands | false | 72 | source-valid | openhands-agent-actions; 72 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-ode-solver-rk4-3eef1f0e` | OpenHands | false | 55 | source-valid | openhands-agent-actions; 55 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-oom-1a6e501d` | OpenHands | false | 38 | source-valid | openhands-agent-actions; 38 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-openssl-selfsigned-cert-67f987d1` | OpenHands | true | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-optimal-transport-e287e0a0` | OpenHands | false | 52 | source-valid | openhands-agent-actions; 52 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-organization-json-generator-0236afb5` | OpenHands | false | 19 | source-valid | openhands-agent-actions; 19 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-overfull-hbox-26e815c8` | OpenHands | true | 84 | excluded | missing archive |
| `openhands-DeepSeek__DeepSeek-V3.2-pandas-etl-522639f1` | OpenHands | true | 28 | source-valid | openhands-agent-actions; 28 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-pandas-sql-query-1be1f11a` | OpenHands | true | 30 | source-valid | openhands-agent-actions; 30 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-parallel-particle-simulator-6a0dabf8` | OpenHands | false | 60 | excluded | openhands-agent-actions emitted 62 operations; public step_count is 60 |
| `openhands-DeepSeek__DeepSeek-V3.2-parallelize-compute-squares-f695ba2e` | OpenHands | true | 51 | source-valid | openhands-agent-actions; 51 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-parallelize-graph-e8b97f46` | OpenHands | false | 85 | source-valid | openhands-agent-actions; 85 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-password-recovery-f656121c` | OpenHands | false | 111 | source-valid | openhands-agent-actions; 111 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-path-tracing-6bbc7853` | OpenHands | false | 65 | source-valid | openhands-agent-actions; 65 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-path-tracing-reverse-cdfec6de` | OpenHands | false | 73 | excluded | openhands-agent-actions emitted 78 operations; public step_count is 73 |
| `openhands-DeepSeek__DeepSeek-V3.2-pcap-to-netflow-1d9c8838` | OpenHands | false | 78 | source-valid | openhands-agent-actions; 78 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-play-zork-cdaf1bff` | OpenHands | false | 110 | excluded | openhands-agent-actions emitted 118 operations; public step_count is 110 |
| `openhands-DeepSeek__DeepSeek-V3.2-play-zork-easy-9d1ea91f` | OpenHands | false | 98 | excluded | openhands-agent-actions emitted 105 operations; public step_count is 98 |
| `openhands-DeepSeek__DeepSeek-V3.2-png-generation-42db12a0` | OpenHands | true | 16 | source-valid | openhands-agent-actions; 16 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-polyglot-c-py-7481ec14` | OpenHands | true | 24 | source-valid | openhands-agent-actions; 24 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-polyglot-rust-c-b6e38d59` | OpenHands | false | 71 | source-valid | openhands-agent-actions; 71 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-port-compressor-da910f6c` | OpenHands | false | 73 | excluded | openhands-agent-actions emitted 76 operations; public step_count is 73 |
| `openhands-DeepSeek__DeepSeek-V3.2-portfolio-optimization-7a38c37f` | OpenHands | true | 43 | source-valid | openhands-agent-actions; 43 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-predicate-pushdown-bench-b25e07ed` | OpenHands | false | 55 | source-valid | openhands-agent-actions; 55 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-predict-customer-churn-0b225be8` | OpenHands | false | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-processing-pipeline-a305dd39` | OpenHands | false | 30 | source-valid | openhands-agent-actions; 30 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-protein-assembly-696ccd0c` | OpenHands | false | 65 | source-valid | openhands-agent-actions; 65 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-protocol-analysis-rs-51c301b9` | OpenHands | false | 103 | source-valid | openhands-agent-actions; 103 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-prove-plus-comm-c45ffb06` | OpenHands | true | 17 | source-valid | openhands-agent-actions; 17 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-puzzle-solver-6dcbb9b7` | OpenHands | false | 27 | excluded | missing archive |
| `openhands-DeepSeek__DeepSeek-V3.2-pypi-server-4c95afe9` | OpenHands | true | 28 | source-valid | openhands-agent-actions; 28 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-pytorch-model-cli-005135c0` | OpenHands | false | 53 | source-valid | openhands-agent-actions; 53 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-pytorch-model-recovery-f273db0d` | OpenHands | true | 36 | source-valid | openhands-agent-actions; 36 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-query-optimize-4edf4cf2` | OpenHands | false | 56 | source-valid | openhands-agent-actions; 56 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-raman-fitting-e8884911` | OpenHands | false | 48 | source-valid | openhands-agent-actions; 48 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-rare-mineral-allocation-226bd136` | OpenHands | false | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-recover-accuracy-log-40125a0c` | OpenHands | true | 30 | source-valid | openhands-agent-actions; 30 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-recover-obfuscated-files-37757918` | OpenHands | true | 28 | source-valid | openhands-agent-actions; 28 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-regex-chess-a52cbe81` | OpenHands | false | 44 | source-valid | openhands-agent-actions; 44 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-regex-log-0294974c` | OpenHands | true | 18 | source-valid | openhands-agent-actions; 18 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-reshard-c4-data-f79d63b6` | OpenHands | false | 63 | source-valid | openhands-agent-actions; 63 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-reverse-engineering-338fcc16` | OpenHands | true | 45 | source-valid | openhands-agent-actions; 45 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-rstan-to-pystan-43aae8ad` | OpenHands | false | 35 | excluded | openhands-agent-actions emitted 44 operations; public step_count is 35 |
| `openhands-DeepSeek__DeepSeek-V3.2-run-pdp11-code-3648e703` | OpenHands | false | 55 | source-valid | openhands-agent-actions; 55 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-sam-cell-seg-14acaa1d` | OpenHands | false | 49 | excluded | missing archive |
| `openhands-DeepSeek__DeepSeek-V3.2-schedule-vacation-d12bebf4` | OpenHands | true | 30 | source-valid | openhands-agent-actions; 30 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-schemelike-metacircular-eval-fdbf5d24` | OpenHands | false | 73 | excluded | openhands-agent-actions emitted 76 operations; public step_count is 73 |
| `openhands-DeepSeek__DeepSeek-V3.2-security-vulhub-minio-4c82b58c` | OpenHands | false | 92 | source-valid | openhands-agent-actions; 92 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-setup-custom-dev-env-cc3e1111` | OpenHands | true | 64 | source-valid | openhands-agent-actions; 64 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-sha-puzzle-3b107dd6` | OpenHands | true | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-simple-sheets-put-d8b3f14e` | OpenHands | false | 25 | source-valid | openhands-agent-actions; 25 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-solana-data-3071ee5d` | OpenHands | false | 85 | excluded | openhands-agent-actions emitted 87 operations; public step_count is 85 |
| `openhands-DeepSeek__DeepSeek-V3.2-solve-maze-challenge-d859dc0b` | OpenHands | false | 57 | source-valid | openhands-agent-actions; 57 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-solve-sudoku-950c80a1` | OpenHands | false | 44 | source-valid | openhands-agent-actions; 44 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-sparql-professors-universities-558cf290` | OpenHands | true | 22 | source-valid | openhands-agent-actions; 22 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-sparql-university-d5e5f596` | OpenHands | false | 45 | source-valid | openhands-agent-actions; 45 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-speech-to-text-0f63cf2b` | OpenHands | false | 44 | source-valid | openhands-agent-actions; 44 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-spinning-up-rl-de40485f` | OpenHands | false | 60 | excluded | openhands-agent-actions emitted 70 operations; public step_count is 60 |
| `openhands-DeepSeek__DeepSeek-V3.2-spring-messaging-vul-b9d38a1e` | OpenHands | false | 60 | excluded | openhands-agent-actions emitted 63 operations; public step_count is 60 |
| `openhands-DeepSeek__DeepSeek-V3.2-sql-injection-attack-0a04c77a` | OpenHands | false | 74 | source-valid | openhands-agent-actions; 74 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-sqlite-db-truncate-046e2d43` | OpenHands | false | 47 | excluded | missing archive |
| `openhands-DeepSeek__DeepSeek-V3.2-sqlite-with-gcov-c12b5be1` | OpenHands | true | 34 | source-valid | openhands-agent-actions; 34 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-stable-parallel-kmeans-84eef4a4` | OpenHands | false | 59 | source-valid | openhands-agent-actions; 59 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-sudo-llvm-ir-8f7b32b2` | OpenHands | false | 82 | source-valid | openhands-agent-actions; 82 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-swe-bench-astropy-1-85847b1e` | OpenHands | false | 11 | source-valid | openhands-agent-actions; 11 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-swe-bench-astropy-2-91bd9b05` | OpenHands | true | 66 | source-valid | openhands-agent-actions; 66 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-swe-bench-fsspec-ac37d72c` | OpenHands | true | 33 | source-valid | openhands-agent-actions; 33 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-swe-bench-langcodes-09de3259` | OpenHands | false | 17 | source-valid | openhands-agent-actions; 17 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-tmux-advanced-workflow-13264032` | OpenHands | true | 29 | source-valid | openhands-agent-actions; 29 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-torch-pipeline-parallelism-b82f2d21` | OpenHands | false | 48 | source-valid | openhands-agent-actions; 48 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-torch-tensor-parallelism-7b0df27c` | OpenHands | false | 57 | source-valid | openhands-agent-actions; 57 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-train-fasttext-172eea3b` | OpenHands | false | 28 | source-valid | openhands-agent-actions; 28 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-tree-directory-parser-232e498c` | OpenHands | true | 28 | source-valid | openhands-agent-actions; 28 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-triton-interpret-8f137054` | OpenHands | false | 48 | excluded | openhands-agent-actions emitted 58 operations; public step_count is 48 |
| `openhands-DeepSeek__DeepSeek-V3.2-tune-mjcf-b3e66af6` | OpenHands | false | 28 | source-valid | openhands-agent-actions; 28 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-vertex-solver-fc602c6f` | OpenHands | true | 30 | source-valid | openhands-agent-actions; 30 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-video-processing-083ce194` | OpenHands | false | 76 | source-valid | openhands-agent-actions; 76 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-vimscript-vim-quine-da007b60` | OpenHands | true | 45 | source-valid | openhands-agent-actions; 45 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-vul-flask-c6cefb07` | OpenHands | false | 82 | excluded | missing archive |
| `openhands-DeepSeek__DeepSeek-V3.2-vul-flink-43c3214d` | OpenHands | false | 59 | source-valid | openhands-agent-actions; 59 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-vulnerable-secret-14bc7b5c` | OpenHands | true | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-wasm-pipeline-c75df817` | OpenHands | false | 47 | source-valid | openhands-agent-actions; 47 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-weighted-max-sat-solver-d39be220` | OpenHands | false | 56 | source-valid | openhands-agent-actions; 56 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-winning-avg-corewars-c4f2b383` | OpenHands | false | 89 | source-valid | openhands-agent-actions; 89 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-word2vec-from-scratch-4c72b202` | OpenHands | false | 49 | source-valid | openhands-agent-actions; 49 operations |
| `openhands-DeepSeek__DeepSeek-V3.2-write-compressor-c9944f23` | OpenHands | false | 60 | source-valid | openhands-agent-actions; 60 operations |
| `openhands-Moonshot__Kimi-K2-250905-3d-model-format-legacy-8cee6696` | OpenHands | false | 260 | excluded | openhands-agent-actions emitted 268 operations; public step_count is 260 |
| `openhands-Moonshot__Kimi-K2-250905-acl-permissions-inheritance-3dbb23c0` | OpenHands | false | 29 | source-valid | openhands-agent-actions; 29 operations |
| `openhands-Moonshot__Kimi-K2-250905-adaptive-rejection-sampler-4b727247` | OpenHands | false | 60 | source-valid | openhands-agent-actions; 60 operations |
| `openhands-Moonshot__Kimi-K2-250905-add-benchmark-lm-eval-harness-14b0850e` | OpenHands | false | 35 | excluded | openhands-agent-actions emitted 43 operations; public step_count is 35 |
| `openhands-Moonshot__Kimi-K2-250905-amuse-install-abea8f7f` | OpenHands | true | 33 | source-valid | openhands-agent-actions; 33 operations |
| `openhands-Moonshot__Kimi-K2-250905-assign-seats-5484d845` | OpenHands | true | 13 | source-valid | openhands-agent-actions; 13 operations |
| `openhands-Moonshot__Kimi-K2-250905-attention-mil-9909fe2c` | OpenHands | false | 53 | source-valid | openhands-agent-actions; 53 operations |
| `openhands-Moonshot__Kimi-K2-250905-audio-synth-stft-peaks-ce78e073` | OpenHands | false | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-Moonshot__Kimi-K2-250905-blind-maze-explorer-5x5-ab952fb6` | OpenHands | false | 83 | source-valid | openhands-agent-actions; 83 operations |
| `openhands-Moonshot__Kimi-K2-250905-blind-maze-explorer-algorithm-1fa0742b` | OpenHands | false | 45 | source-valid | openhands-agent-actions; 45 operations |
| `openhands-Moonshot__Kimi-K2-250905-break-filter-js-from-html-04b01b5d` | OpenHands | false | 195 | source-valid | openhands-agent-actions; 195 operations |
| `openhands-Moonshot__Kimi-K2-250905-build-cython-ext-d0da0288` | OpenHands | false | 101 | source-valid | openhands-agent-actions; 101 operations |
| `openhands-Moonshot__Kimi-K2-250905-build-initramfs-qemu-f2562b06` | OpenHands | false | 38 | source-valid | openhands-agent-actions; 38 operations |
| `openhands-Moonshot__Kimi-K2-250905-build-linux-kernel-qemu-ce0bb8a7` | OpenHands | true | 46 | source-valid | openhands-agent-actions; 46 operations |
| `openhands-Moonshot__Kimi-K2-250905-build-pmars-0a4d7803` | OpenHands | true | 34 | source-valid | openhands-agent-actions; 34 operations |
| `openhands-Moonshot__Kimi-K2-250905-build-pov-ray-58bf9503` | OpenHands | false | 58 | source-valid | openhands-agent-actions; 58 operations |
| `openhands-Moonshot__Kimi-K2-250905-build-stp-dfe2a210` | OpenHands | true | 60 | source-valid | openhands-agent-actions; 60 operations |
| `openhands-Moonshot__Kimi-K2-250905-build-tcc-qemu-38a41db3` | OpenHands | false | 157 | source-valid | openhands-agent-actions; 157 operations |
| `openhands-Moonshot__Kimi-K2-250905-caffe-cifar-10-05568f6f` | OpenHands | false | 35 | excluded | openhands-agent-actions emitted 40 operations; public step_count is 35 |
| `openhands-Moonshot__Kimi-K2-250905-cartpole-rl-training-db78c31e` | OpenHands | false | 61 | source-valid | openhands-agent-actions; 61 operations |
| `openhands-Moonshot__Kimi-K2-250905-catch-me-if-you-can-50ecf039` | OpenHands | false | 38 | source-valid | openhands-agent-actions; 38 operations |
| `openhands-Moonshot__Kimi-K2-250905-causal-inference-r-48c04167` | OpenHands | false | 12 | source-valid | openhands-agent-actions; 12 operations |
| `openhands-Moonshot__Kimi-K2-250905-chem-property-targeting-e6ec12ed` | OpenHands | false | 43 | source-valid | openhands-agent-actions; 43 operations |
| `openhands-Moonshot__Kimi-K2-250905-chem-rf-2a302639` | OpenHands | false | 46 | source-valid | openhands-agent-actions; 46 operations |
| `openhands-Moonshot__Kimi-K2-250905-chess-best-move-f550c233` | OpenHands | false | 38 | source-valid | openhands-agent-actions; 38 operations |
| `openhands-Moonshot__Kimi-K2-250905-circuit-fibsqrt-e9718d53` | OpenHands | false | 80 | source-valid | openhands-agent-actions; 80 operations |
| `openhands-Moonshot__Kimi-K2-250905-cobol-modernization-f3fe45f2` | OpenHands | false | 257 | source-valid | openhands-agent-actions; 257 operations |
| `openhands-Moonshot__Kimi-K2-250905-code-from-image-68f9bc9d` | OpenHands | true | 33 | source-valid | openhands-agent-actions; 33 operations |
| `openhands-Moonshot__Kimi-K2-250905-compile-compcert-9455a9e9` | OpenHands | false | 23 | excluded | openhands-agent-actions emitted 32 operations; public step_count is 23 |
| `openhands-Moonshot__Kimi-K2-250905-conda-env-conflict-resolution-54757c2b` | OpenHands | false | 35 | excluded | openhands-agent-actions emitted 45 operations; public step_count is 35 |
| `openhands-Moonshot__Kimi-K2-250905-configure-git-webserver-63b0f5ba` | OpenHands | true | 23 | source-valid | openhands-agent-actions; 23 operations |
| `openhands-Moonshot__Kimi-K2-250905-constraints-scheduling-fc102566` | OpenHands | true | 11 | source-valid | openhands-agent-actions; 11 operations |
| `openhands-Moonshot__Kimi-K2-250905-count-call-stack-d6feae82` | OpenHands | false | 12 | source-valid | openhands-agent-actions; 12 operations |
| `openhands-Moonshot__Kimi-K2-250905-count-dataset-tokens-d049667e` | OpenHands | false | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-Moonshot__Kimi-K2-250905-cpp-compatibility-68f3c0ae` | OpenHands | false | 14 | source-valid | openhands-agent-actions; 14 operations |
| `openhands-Moonshot__Kimi-K2-250905-cprofiling-python-8dce79c6` | OpenHands | false | 93 | source-valid | openhands-agent-actions; 93 operations |
| `openhands-Moonshot__Kimi-K2-250905-cron-broken-network-b391ff8f` | OpenHands | false | 136 | source-valid | openhands-agent-actions; 136 operations |
| `openhands-Moonshot__Kimi-K2-250905-cross-entropy-method-fb77e75f` | OpenHands | true | 54 | source-valid | openhands-agent-actions; 54 operations |
| `openhands-Moonshot__Kimi-K2-250905-csv-to-parquet-2f3c7de5` | OpenHands | true | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-Moonshot__Kimi-K2-250905-custom-memory-heap-crash-7f1d897b` | OpenHands | false | 153 | source-valid | openhands-agent-actions; 153 operations |
| `openhands-Moonshot__Kimi-K2-250905-db-wal-recovery-26e8c823` | OpenHands | false | 42 | source-valid | openhands-agent-actions; 42 operations |
| `openhands-Moonshot__Kimi-K2-250905-debug-long-program-93c1739f` | OpenHands | false | 50 | source-valid | openhands-agent-actions; 50 operations |
| `openhands-Moonshot__Kimi-K2-250905-decommissioning-service-with-sensitive-data-248e2725` | OpenHands | true | 18 | source-valid | openhands-agent-actions; 18 operations |
| `openhands-Moonshot__Kimi-K2-250905-deterministic-tarball-f4e52e30` | OpenHands | false | 50 | source-valid | openhands-agent-actions; 50 operations |
| `openhands-Moonshot__Kimi-K2-250905-distribution-search-3ba37d7b` | OpenHands | true | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-Moonshot__Kimi-K2-250905-dna-assembly-d757ac9d` | OpenHands | false | 23 | source-valid | openhands-agent-actions; 23 operations |
| `openhands-Moonshot__Kimi-K2-250905-dna-insert-9f8ed5b4` | OpenHands | false | 17 | source-valid | openhands-agent-actions; 17 operations |
| `openhands-Moonshot__Kimi-K2-250905-download-youtube-ad534f0d` | OpenHands | false | 41 | excluded | missing archive |
| `openhands-Moonshot__Kimi-K2-250905-enemy-grid-escape-907d1022` | OpenHands | false | 34 | source-valid | openhands-agent-actions; 34 operations |
| `openhands-Moonshot__Kimi-K2-250905-extract-elf-2ba48b9b` | OpenHands | false | 32 | source-valid | openhands-agent-actions; 32 operations |
| `openhands-Moonshot__Kimi-K2-250905-extract-moves-from-video-be28bc78` | OpenHands | false | 21 | source-valid | openhands-agent-actions; 21 operations |
| `openhands-Moonshot__Kimi-K2-250905-feal-differential-cryptanalysis-2beac25b` | OpenHands | false | 90 | excluded | missing archive |
| `openhands-Moonshot__Kimi-K2-250905-feal-linear-cryptanalysis-0e0a65b8` | OpenHands | false | 85 | excluded | openhands-agent-actions emitted 90 operations; public step_count is 85 |
| `openhands-Moonshot__Kimi-K2-250905-fibonacci-server-072737c4` | OpenHands | true | 16 | source-valid | openhands-agent-actions; 16 operations |
| `openhands-Moonshot__Kimi-K2-250905-filter-js-from-html-1193385c` | OpenHands | false | 47 | source-valid | openhands-agent-actions; 47 operations |
| `openhands-Moonshot__Kimi-K2-250905-financial-document-processor-8616868d` | OpenHands | false | 36 | source-valid | openhands-agent-actions; 36 operations |
| `openhands-Moonshot__Kimi-K2-250905-find-official-code-8976c4bf` | OpenHands | false | 11 | source-valid | openhands-agent-actions; 11 operations |
| `openhands-Moonshot__Kimi-K2-250905-fix-code-vulnerability-da397198` | OpenHands | false | 77 | source-valid | openhands-agent-actions; 77 operations |
| `openhands-Moonshot__Kimi-K2-250905-fix-git-a061c401` | OpenHands | true | 29 | source-valid | openhands-agent-actions; 29 operations |
| `openhands-Moonshot__Kimi-K2-250905-fix-ocaml-gc-bea33042` | OpenHands | false | 109 | source-valid | openhands-agent-actions; 109 operations |
| `openhands-Moonshot__Kimi-K2-250905-fix-pandas-version-f793b7dd` | OpenHands | false | 48 | source-valid | openhands-agent-actions; 48 operations |
| `openhands-Moonshot__Kimi-K2-250905-flood-monitoring-basic-34086c3d` | OpenHands | true | 13 | source-valid | openhands-agent-actions; 13 operations |
| `openhands-Moonshot__Kimi-K2-250905-fmri-encoding-r-34355299` | OpenHands | false | 29 | source-valid | openhands-agent-actions; 29 operations |
| `openhands-Moonshot__Kimi-K2-250905-form-filling-0b9fd9f1` | OpenHands | false | 36 | source-valid | openhands-agent-actions; 36 operations |
| `openhands-Moonshot__Kimi-K2-250905-gcc-compiler-optimization-27777ac1` | OpenHands | false | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-Moonshot__Kimi-K2-250905-gcode-to-text-76669219` | OpenHands | false | 16 | source-valid | openhands-agent-actions; 16 operations |
| `openhands-Moonshot__Kimi-K2-250905-get-bitcoin-nodes-2cc4d249` | OpenHands | false | 57 | source-valid | openhands-agent-actions; 57 operations |
| `openhands-Moonshot__Kimi-K2-250905-git-leak-recovery-91bdc6bb` | OpenHands | true | 18 | source-valid | openhands-agent-actions; 18 operations |
| `openhands-Moonshot__Kimi-K2-250905-git-multibranch-fa531f79` | OpenHands | false | 154 | source-valid | openhands-agent-actions; 154 operations |
| `openhands-Moonshot__Kimi-K2-250905-git-workflow-hack-81db091e` | OpenHands | true | 29 | source-valid | openhands-agent-actions; 29 operations |
| `openhands-Moonshot__Kimi-K2-250905-gomoku-planner-620c7f5a` | OpenHands | false | 24 | source-valid | openhands-agent-actions; 24 operations |
| `openhands-Moonshot__Kimi-K2-250905-gpt2-codegolf-bbea1ba6` | OpenHands | false | 55 | source-valid | openhands-agent-actions; 55 operations |
| `openhands-Moonshot__Kimi-K2-250905-hf-lora-adapter-00f08787` | OpenHands | false | 27 | excluded | missing archive |
| `openhands-Moonshot__Kimi-K2-250905-hf-model-inference-04bf9c8f` | OpenHands | false | 49 | source-valid | openhands-agent-actions; 49 operations |
| `openhands-Moonshot__Kimi-K2-250905-hf-train-lora-adapter-a5a96470` | OpenHands | false | 48 | source-valid | openhands-agent-actions; 48 operations |
| `openhands-Moonshot__Kimi-K2-250905-html-finance-verify-0d851774` | OpenHands | false | 55 | source-valid | openhands-agent-actions; 55 operations |
| `openhands-Moonshot__Kimi-K2-250905-huarong-dao-solver-6f32435d` | OpenHands | false | 85 | excluded | openhands-agent-actions emitted 92 operations; public step_count is 85 |
| `openhands-Moonshot__Kimi-K2-250905-hydra-debug-slurm-mode-0ff757cb` | OpenHands | false | 44 | source-valid | openhands-agent-actions; 44 operations |
| `openhands-Moonshot__Kimi-K2-250905-ilp-solver-73ad79cc` | OpenHands | false | 15 | source-valid | openhands-agent-actions; 15 operations |
| `openhands-Moonshot__Kimi-K2-250905-implement-eigenvectors-from-eigenvalues-research-paper-e7f81953` | OpenHands | false | 46 | source-valid | openhands-agent-actions; 46 operations |
| `openhands-Moonshot__Kimi-K2-250905-incompatible-python-fasttext-b0ac1f18` | OpenHands | false | 26 | source-valid | openhands-agent-actions; 26 operations |
| `openhands-Moonshot__Kimi-K2-250905-install-klee-minimal-3f449579` | OpenHands | false | 14 | source-valid | openhands-agent-actions; 14 operations |
| `openhands-Moonshot__Kimi-K2-250905-install-windows-3.11-ec6cd938` | OpenHands | false | 63 | excluded | missing archive |
| `openhands-Moonshot__Kimi-K2-250905-install-windows-xp-8f7eb364` | OpenHands | false | 60 | source-valid | openhands-agent-actions; 60 operations |
| `openhands-Moonshot__Kimi-K2-250905-interactive-maze-game-cf7192bf` | OpenHands | false | 42 | source-valid | openhands-agent-actions; 42 operations |
| `openhands-Moonshot__Kimi-K2-250905-intrusion-detection-a548fbc2` | OpenHands | false | 92 | source-valid | openhands-agent-actions; 92 operations |
| `openhands-Moonshot__Kimi-K2-250905-jq-data-processing-e2cde66f` | OpenHands | false | 22 | source-valid | openhands-agent-actions; 22 operations |
| `openhands-Moonshot__Kimi-K2-250905-jsonl-aggregator-4c7d6378` | OpenHands | true | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-Moonshot__Kimi-K2-250905-jupyter-notebook-server-37b847fc` | OpenHands | false | 26 | source-valid | openhands-agent-actions; 26 operations |
| `openhands-Moonshot__Kimi-K2-250905-kv-store-grpc-57f8679b` | OpenHands | false | 38 | source-valid | openhands-agent-actions; 38 operations |
| `openhands-Moonshot__Kimi-K2-250905-large-scale-text-editing-4dd11c68` | OpenHands | false | 72 | source-valid | openhands-agent-actions; 72 operations |
| `openhands-Moonshot__Kimi-K2-250905-largest-eigenval-65185d75` | OpenHands | false | 57 | source-valid | openhands-agent-actions; 57 operations |
| `openhands-Moonshot__Kimi-K2-250905-lean4-proof-b7ef5749` | OpenHands | false | 73 | excluded | openhands-agent-actions emitted 77 operations; public step_count is 73 |
| `openhands-Moonshot__Kimi-K2-250905-leelachess0-pytorch-conversion-01063c32` | OpenHands | false | 61 | source-valid | openhands-agent-actions; 61 operations |
| `openhands-Moonshot__Kimi-K2-250905-llm-inference-batching-scheduler-29734a52` | OpenHands | false | 50 | source-valid | openhands-agent-actions; 50 operations |
| `openhands-Moonshot__Kimi-K2-250905-llm-spec-decoding-866574d3` | OpenHands | false | 38 | source-valid | openhands-agent-actions; 38 operations |
| `openhands-Moonshot__Kimi-K2-250905-log-summary-42158d85` | OpenHands | true | 11 | source-valid | openhands-agent-actions; 11 operations |
| `openhands-Moonshot__Kimi-K2-250905-log-summary-date-ranges-aa695097` | OpenHands | true | 13 | source-valid | openhands-agent-actions; 13 operations |
| `openhands-Moonshot__Kimi-K2-250905-logistic-regression-divergence-6917eae3` | OpenHands | false | 98 | excluded | openhands-agent-actions emitted 105 operations; public step_count is 98 |
| `openhands-Moonshot__Kimi-K2-250905-magsac-install-23ee7167` | OpenHands | false | 85 | excluded | openhands-agent-actions emitted 86 operations; public step_count is 85 |
| `openhands-Moonshot__Kimi-K2-250905-mahjong-winninghand-1fa8579f` | OpenHands | true | 22 | source-valid | openhands-agent-actions; 22 operations |
| `openhands-Moonshot__Kimi-K2-250905-mailman-32b8d23f` | OpenHands | true | 88 | source-valid | openhands-agent-actions; 88 operations |
| `openhands-Moonshot__Kimi-K2-250905-make-doom-for-mips-9755ce1d` | OpenHands | false | 187 | excluded | openhands-agent-actions emitted 269 operations; public step_count is 187 |
| `openhands-Moonshot__Kimi-K2-250905-make-mips-interpreter-0e01ec6e` | OpenHands | false | 123 | excluded | openhands-agent-actions emitted 134 operations; public step_count is 123 |
| `openhands-Moonshot__Kimi-K2-250905-mcmc-sampling-stan-35a20796` | OpenHands | true | 21 | excluded | missing archive |
| `openhands-Moonshot__Kimi-K2-250905-merge-diff-arc-agi-task-7ab382f6` | OpenHands | true | 42 | source-valid | openhands-agent-actions; 42 operations |
| `openhands-Moonshot__Kimi-K2-250905-mixed-integer-programming-478c0c05` | OpenHands | false | 27 | source-valid | openhands-agent-actions; 27 operations |
| `openhands-Moonshot__Kimi-K2-250905-mlflow-register-fbcdad28` | OpenHands | false | 19 | source-valid | openhands-agent-actions; 19 operations |
| `openhands-Moonshot__Kimi-K2-250905-model-extraction-relu-logits-21a8f220` | OpenHands | false | 19 | source-valid | openhands-agent-actions; 19 operations |
| `openhands-Moonshot__Kimi-K2-250905-modernize-fortran-build-56ecb968` | OpenHands | true | 15 | source-valid | openhands-agent-actions; 15 operations |
| `openhands-Moonshot__Kimi-K2-250905-modernize-scientific-stack-2ff28bd1` | OpenHands | false | 17 | source-valid | openhands-agent-actions; 17 operations |
| `openhands-Moonshot__Kimi-K2-250905-movie-helper-879c6c28` | OpenHands | false | 21 | source-valid | openhands-agent-actions; 21 operations |
| `openhands-Moonshot__Kimi-K2-250905-mteb-eval-6f7882e2` | OpenHands | true | 28 | source-valid | openhands-agent-actions; 28 operations |
| `openhands-Moonshot__Kimi-K2-250905-mteb-leaderboard-1cf7362b` | OpenHands | false | 11 | source-valid | openhands-agent-actions; 11 operations |
| `openhands-Moonshot__Kimi-K2-250905-mteb-retrieve-e0068f78` | OpenHands | false | 38 | source-valid | openhands-agent-actions; 38 operations |
| `openhands-Moonshot__Kimi-K2-250905-multi-source-data-merger-ec919320` | OpenHands | false | 48 | source-valid | openhands-agent-actions; 48 operations |
| `openhands-Moonshot__Kimi-K2-250905-multistep-definite-integral-1a11edcb` | OpenHands | true | 12 | source-valid | openhands-agent-actions; 12 operations |
| `openhands-Moonshot__Kimi-K2-250905-neuron-to-jaxley-conversion-0e8fa084` | OpenHands | false | 82 | source-valid | openhands-agent-actions; 82 operations |
| `openhands-Moonshot__Kimi-K2-250905-new-encrypt-command-1b7deff9` | OpenHands | true | 21 | source-valid | openhands-agent-actions; 21 operations |
| `openhands-Moonshot__Kimi-K2-250905-nginx-request-logging-729178f2` | OpenHands | true | 16 | source-valid | openhands-agent-actions; 16 operations |
| `openhands-Moonshot__Kimi-K2-250905-npm-conflict-resolution-b44368e5` | OpenHands | false | 32 | source-valid | openhands-agent-actions; 32 operations |
| `openhands-Moonshot__Kimi-K2-250905-ode-solver-rk4-de178174` | OpenHands | true | 25 | source-valid | openhands-agent-actions; 25 operations |
| `openhands-Moonshot__Kimi-K2-250905-oom-152184ac` | OpenHands | false | 49 | source-valid | openhands-agent-actions; 49 operations |
| `openhands-Moonshot__Kimi-K2-250905-openssl-selfsigned-cert-7d255d5a` | OpenHands | false | 12 | source-valid | openhands-agent-actions; 12 operations |
| `openhands-Moonshot__Kimi-K2-250905-optimal-transport-5118fb98` | OpenHands | false | 32 | source-valid | openhands-agent-actions; 32 operations |
| `openhands-Moonshot__Kimi-K2-250905-organization-json-generator-69688ce5` | OpenHands | false | 15 | source-valid | openhands-agent-actions; 15 operations |
| `openhands-Moonshot__Kimi-K2-250905-overfull-hbox-2d4198eb` | OpenHands | false | 65 | source-valid | openhands-agent-actions; 65 operations |
| `openhands-Moonshot__Kimi-K2-250905-pandas-etl-d9c79890` | OpenHands | true | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-Moonshot__Kimi-K2-250905-pandas-sql-query-ddd7a8cf` | OpenHands | true | 30 | source-valid | openhands-agent-actions; 30 operations |
| `openhands-Moonshot__Kimi-K2-250905-parallel-particle-simulator-1b9ef61a` | OpenHands | false | 78 | source-valid | openhands-agent-actions; 78 operations |
| `openhands-Moonshot__Kimi-K2-250905-parallelize-compute-squares-8e35dc1c` | OpenHands | true | 37 | source-valid | openhands-agent-actions; 37 operations |
| `openhands-Moonshot__Kimi-K2-250905-parallelize-graph-c2bef235` | OpenHands | false | 50 | source-valid | openhands-agent-actions; 50 operations |
| `openhands-Moonshot__Kimi-K2-250905-password-recovery-58ec01b2` | OpenHands | false | 42 | source-valid | openhands-agent-actions; 42 operations |
| `openhands-Moonshot__Kimi-K2-250905-path-tracing-42dec5a4` | OpenHands | false | 62 | source-valid | openhands-agent-actions; 62 operations |
| `openhands-Moonshot__Kimi-K2-250905-path-tracing-reverse-f2408189` | OpenHands | false | 90 | source-valid | openhands-agent-actions; 90 operations |
| `openhands-Moonshot__Kimi-K2-250905-pcap-to-netflow-c4fa3880` | OpenHands | false | 32 | source-valid | openhands-agent-actions; 32 operations |
| `openhands-Moonshot__Kimi-K2-250905-play-zork-3c19a377` | OpenHands | false | 109 | source-valid | openhands-agent-actions; 109 operations |
| `openhands-Moonshot__Kimi-K2-250905-play-zork-easy-c6142a90` | OpenHands | false | 100 | source-valid | openhands-agent-actions; 100 operations |
| `openhands-Moonshot__Kimi-K2-250905-polyglot-c-py-2465723f` | OpenHands | false | 89 | source-valid | openhands-agent-actions; 89 operations |
| `openhands-Moonshot__Kimi-K2-250905-polyglot-rust-c-63399bd5` | OpenHands | false | 98 | excluded | openhands-agent-actions emitted 102 operations; public step_count is 98 |
| `openhands-Moonshot__Kimi-K2-250905-port-compressor-110db557` | OpenHands | false | 207 | source-valid | openhands-agent-actions; 207 operations |
| `openhands-Moonshot__Kimi-K2-250905-portfolio-optimization-9c2fce19` | OpenHands | false | 132 | source-valid | openhands-agent-actions; 132 operations |
| `openhands-Moonshot__Kimi-K2-250905-predicate-pushdown-bench-8c00810f` | OpenHands | false | 53 | source-valid | openhands-agent-actions; 53 operations |
| `openhands-Moonshot__Kimi-K2-250905-predict-customer-churn-18887671` | OpenHands | false | 67 | source-valid | openhands-agent-actions; 67 operations |
| `openhands-Moonshot__Kimi-K2-250905-processing-pipeline-7dd37d34` | OpenHands | true | 25 | source-valid | openhands-agent-actions; 25 operations |
| `openhands-Moonshot__Kimi-K2-250905-protein-assembly-d9e81bcc` | OpenHands | false | 19 | source-valid | openhands-agent-actions; 19 operations |
| `openhands-Moonshot__Kimi-K2-250905-protocol-analysis-rs-3718d929` | OpenHands | false | 110 | source-valid | openhands-agent-actions; 110 operations |
| `openhands-Moonshot__Kimi-K2-250905-prove-plus-comm-5c2eb1a9` | OpenHands | true | 24 | source-valid | openhands-agent-actions; 24 operations |
| `openhands-Moonshot__Kimi-K2-250905-puzzle-solver-e0839801` | OpenHands | false | 33 | source-valid | openhands-agent-actions; 33 operations |
| `openhands-Moonshot__Kimi-K2-250905-pypi-server-303aedd8` | OpenHands | false | 34 | source-valid | openhands-agent-actions; 34 operations |
| `openhands-Moonshot__Kimi-K2-250905-pytorch-model-cli-f3cdfe31` | OpenHands | false | 23 | source-valid | openhands-agent-actions; 23 operations |
| `openhands-Moonshot__Kimi-K2-250905-pytorch-model-recovery-52e3f631` | OpenHands | false | 47 | excluded | openhands-agent-actions emitted 57 operations; public step_count is 47 |
| `openhands-Moonshot__Kimi-K2-250905-query-optimize-f3de83c1` | OpenHands | false | 19 | source-valid | openhands-agent-actions; 19 operations |
| `openhands-Moonshot__Kimi-K2-250905-raman-fitting-d18a717a` | OpenHands | false | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-Moonshot__Kimi-K2-250905-rare-mineral-allocation-0a4a217a` | OpenHands | false | 18 | source-valid | openhands-agent-actions; 18 operations |
| `openhands-Moonshot__Kimi-K2-250905-recover-accuracy-log-695c2e74` | OpenHands | true | 15 | source-valid | openhands-agent-actions; 15 operations |
| `openhands-Moonshot__Kimi-K2-250905-recover-obfuscated-files-f05642dd` | OpenHands | true | 12 | source-valid | openhands-agent-actions; 12 operations |
| `openhands-Moonshot__Kimi-K2-250905-regex-chess-bf85fda5` | OpenHands | false | 50 | excluded | missing archive |
| `openhands-Moonshot__Kimi-K2-250905-reshard-c4-data-eef216ac` | OpenHands | false | 48 | source-valid | openhands-agent-actions; 48 operations |
| `openhands-Moonshot__Kimi-K2-250905-reverse-engineering-968e1980` | OpenHands | false | 248 | excluded | openhands-agent-actions emitted 258 operations; public step_count is 248 |
| `openhands-Moonshot__Kimi-K2-250905-rstan-to-pystan-992ddd72` | OpenHands | false | 33 | excluded | missing archive |
| `openhands-Moonshot__Kimi-K2-250905-run-pdp11-code-7aac1bc9` | OpenHands | false | 76 | source-valid | openhands-agent-actions; 76 operations |
| `openhands-Moonshot__Kimi-K2-250905-sam-cell-seg-505b04a1` | OpenHands | false | 35 | source-valid | openhands-agent-actions; 35 operations |
| `openhands-Moonshot__Kimi-K2-250905-schedule-vacation-b23b802c` | OpenHands | true | 18 | source-valid | openhands-agent-actions; 18 operations |
| `openhands-Moonshot__Kimi-K2-250905-schemelike-metacircular-eval-fbb09864` | OpenHands | false | 210 | excluded | openhands-agent-actions emitted 216 operations; public step_count is 210 |
| `openhands-Moonshot__Kimi-K2-250905-security-vulhub-minio-8c5ae687` | OpenHands | false | 82 | source-valid | openhands-agent-actions; 82 operations |
| `openhands-Moonshot__Kimi-K2-250905-setup-custom-dev-env-887d5177` | OpenHands | true | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-Moonshot__Kimi-K2-250905-simple-sheets-put-e968770f` | OpenHands | false | 12 | source-valid | openhands-agent-actions; 12 operations |
| `openhands-Moonshot__Kimi-K2-250905-solana-data-fdfe13f6` | OpenHands | false | 109 | source-valid | openhands-agent-actions; 109 operations |
| `openhands-Moonshot__Kimi-K2-250905-solve-maze-challenge-ca1f3ee8` | OpenHands | false | 95 | source-valid | openhands-agent-actions; 95 operations |
| `openhands-Moonshot__Kimi-K2-250905-solve-sudoku-170b7d41` | OpenHands | false | 29 | source-valid | openhands-agent-actions; 29 operations |
| `openhands-Moonshot__Kimi-K2-250905-sparql-professors-universities-14b4a1f3` | OpenHands | true | 19 | source-valid | openhands-agent-actions; 19 operations |
| `openhands-Moonshot__Kimi-K2-250905-speech-to-text-4c243a23` | OpenHands | false | 32 | excluded | missing archive |
| `openhands-Moonshot__Kimi-K2-250905-spinning-up-rl-f5b41876` | OpenHands | false | 97 | excluded | missing archive |
| `openhands-Moonshot__Kimi-K2-250905-spring-messaging-vul-9f1766df` | OpenHands | false | 47 | excluded | openhands-agent-actions emitted 54 operations; public step_count is 47 |
| `openhands-Moonshot__Kimi-K2-250905-sql-injection-attack-db120198` | OpenHands | false | 74 | source-valid | openhands-agent-actions; 74 operations |
| `openhands-Moonshot__Kimi-K2-250905-sqlite-db-truncate-a1e69b03` | OpenHands | false | 11 | source-valid | openhands-agent-actions; 11 operations |
| `openhands-Moonshot__Kimi-K2-250905-sqlite-with-gcov-c16894fc` | OpenHands | true | 33 | source-valid | openhands-agent-actions; 33 operations |
| `openhands-Moonshot__Kimi-K2-250905-stable-parallel-kmeans-ad4e6b11` | OpenHands | false | 46 | source-valid | openhands-agent-actions; 46 operations |
| `openhands-Moonshot__Kimi-K2-250905-sudo-llvm-ir-f15bca89` | OpenHands | false | 44 | source-valid | openhands-agent-actions; 44 operations |
| `openhands-Moonshot__Kimi-K2-250905-swe-bench-astropy-2-dfbb5c4c` | OpenHands | false | 14 | source-valid | openhands-agent-actions; 14 operations |
| `openhands-Moonshot__Kimi-K2-250905-swe-bench-fsspec-9e2586a1` | OpenHands | true | 66 | source-valid | openhands-agent-actions; 66 operations |
| `openhands-Moonshot__Kimi-K2-250905-swe-bench-langcodes-e85adcea` | OpenHands | true | 27 | source-valid | openhands-agent-actions; 27 operations |
| `openhands-Moonshot__Kimi-K2-250905-tmux-advanced-workflow-c8ee5499` | OpenHands | true | 30 | source-valid | openhands-agent-actions; 30 operations |
| `openhands-Moonshot__Kimi-K2-250905-torch-pipeline-parallelism-db92e966` | OpenHands | false | 33 | source-valid | openhands-agent-actions; 33 operations |
| `openhands-Moonshot__Kimi-K2-250905-torch-tensor-parallelism-75375021` | OpenHands | false | 61 | source-valid | openhands-agent-actions; 61 operations |
| `openhands-Moonshot__Kimi-K2-250905-train-fasttext-874713a4` | OpenHands | true | 33 | excluded | missing archive |
| `openhands-Moonshot__Kimi-K2-250905-tree-directory-parser-d3e08630` | OpenHands | false | 63 | source-valid | openhands-agent-actions; 63 operations |
| `openhands-Moonshot__Kimi-K2-250905-triton-interpret-d1a2b5b2` | OpenHands | false | 65 | source-valid | openhands-agent-actions; 65 operations |
| `openhands-Moonshot__Kimi-K2-250905-tune-mjcf-b6e240cd` | OpenHands | false | 310 | excluded | openhands-agent-actions emitted 313 operations; public step_count is 310 |
| `openhands-Moonshot__Kimi-K2-250905-vertex-solver-16392279` | OpenHands | true | 16 | source-valid | openhands-agent-actions; 16 operations |
| `openhands-Moonshot__Kimi-K2-250905-video-processing-ea0e463d` | OpenHands | false | 49 | source-valid | openhands-agent-actions; 49 operations |
| `openhands-Moonshot__Kimi-K2-250905-vul-flask-a1f83477` | OpenHands | true | 181 | source-valid | openhands-agent-actions; 181 operations |
| `openhands-Moonshot__Kimi-K2-250905-vul-flink-78a8470e` | OpenHands | false | 50 | source-valid | openhands-agent-actions; 50 operations |
| `openhands-Moonshot__Kimi-K2-250905-vulnerable-secret-e5db04a0` | OpenHands | true | 35 | source-valid | openhands-agent-actions; 35 operations |
| `openhands-Moonshot__Kimi-K2-250905-wasm-pipeline-c2b52e47` | OpenHands | false | 51 | source-valid | openhands-agent-actions; 51 operations |
| `openhands-Moonshot__Kimi-K2-250905-winning-avg-corewars-8eb3b663` | OpenHands | false | 82 | source-valid | openhands-agent-actions; 82 operations |
| `openhands-Moonshot__Kimi-K2-250905-word2vec-from-scratch-dc5052d8` | OpenHands | false | 47 | excluded | openhands-agent-actions emitted 56 operations; public step_count is 47 |
| `openhands-Moonshot__Kimi-K2-250905-write-compressor-0aa4dacc` | OpenHands | false | 114 | source-valid | openhands-agent-actions; 114 operations |
| `openhands-OpenAI__GPT-5-adaptive-rejection-sampler-3e6787e7` | OpenHands | true | 32 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-add-benchmark-lm-eval-harness-aa036803` | OpenHands | false | 27 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-ancient-puzzle-afac6b18` | OpenHands | false | 17 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-astropy__astropy-12907-f99e6267` | OpenHands | true | 23 | source-valid | openhands-maximal-visible-action-context; 23 operations |
| `openhands-OpenAI__GPT-5-astropy__astropy-13398-3106f9b1` | OpenHands | false | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-astropy__astropy-13579-5642ba76` | OpenHands | true | 17 | source-valid | openhands-maximal-visible-action-context; 17 operations |
| `openhands-OpenAI__GPT-5-astropy__astropy-14096-dbeb6acd` | OpenHands | true | 32 | source-valid | openhands-maximal-visible-action-context; 32 operations |
| `openhands-OpenAI__GPT-5-astropy__astropy-14309-f1105f6a` | OpenHands | true | 10 | source-valid | openhands-maximal-visible-action-context; 10 operations |
| `openhands-OpenAI__GPT-5-astropy__astropy-14369-0fb54358` | OpenHands | false | 33 | source-valid | openhands-maximal-visible-action-context; 33 operations |
| `openhands-OpenAI__GPT-5-astropy__astropy-14539-ab9134cc` | OpenHands | true | 24 | source-valid | openhands-maximal-visible-action-context; 24 operations |
| `openhands-OpenAI__GPT-5-astropy__astropy-14598-36c01790` | OpenHands | false | 34 | source-valid | openhands-maximal-visible-action-context; 34 operations |
| `openhands-OpenAI__GPT-5-astropy__astropy-14995-e541781d` | OpenHands | true | 28 | source-valid | openhands-maximal-visible-action-context; 28 operations |
| `openhands-OpenAI__GPT-5-astropy__astropy-7606-fed58415` | OpenHands | false | 17 | source-valid | openhands-maximal-visible-action-context; 17 operations |
| `openhands-OpenAI__GPT-5-audio-synth-stft-peaks-4679a79f` | OpenHands | false | 19 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-break-filter-js-from-html-7aa94ae8` | OpenHands | false | 14 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-build-cython-ext-fbe9fd86` | OpenHands | false | 35 | excluded | openhands-agent-actions emitted 46 operations; public step_count is 35 |
| `openhands-OpenAI__GPT-5-build-linux-kernel-qemu-aa2f8bd3` | OpenHands | true | 25 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-build-pmars-b20e15d6` | OpenHands | true | 36 | source-valid | openhands-agent-actions; 36 operations |
| `openhands-OpenAI__GPT-5-build-pov-ray-6faae954` | OpenHands | false | 25 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-build-stp-768a3759` | OpenHands | true | 11 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-causal-inference-r-5f30a1f0` | OpenHands | true | 21 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-chem-property-targeting-c8be58a4` | OpenHands | false | 13 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-circuit-fibsqrt-b4830ef5` | OpenHands | true | 31 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-cobol-modernization-3f9244bd` | OpenHands | true | 21 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-code-from-image-8044dcd2` | OpenHands | true | 14 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-conda-env-conflict-resolution-1a0646a6` | OpenHands | true | 22 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-configure-git-webserver-6a62b5f7` | OpenHands | true | 12 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-cross-entropy-method-b6ad3b99` | OpenHands | true | 17 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-custom-memory-heap-crash-ccb1ba42` | OpenHands | true | 16 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-db-wal-recovery-1d244aa6` | OpenHands | false | 25 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-deterministic-tarball-9832ca54` | OpenHands | true | 11 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-django__django-10880-70bbaa14` | OpenHands | true | 34 | source-valid | openhands-maximal-visible-action-context; 34 operations |
| `openhands-OpenAI__GPT-5-django__django-11095-991bf268` | OpenHands | true | 34 | source-valid | openhands-maximal-visible-action-context; 34 operations |
| `openhands-OpenAI__GPT-5-django__django-11099-c6998918` | OpenHands | true | 33 | source-valid | openhands-maximal-visible-action-context; 33 operations |
| `openhands-OpenAI__GPT-5-django__django-11133-5e845215` | OpenHands | true | 31 | source-valid | openhands-maximal-visible-action-context; 31 operations |
| `openhands-OpenAI__GPT-5-django__django-11163-0e408098` | OpenHands | true | 26 | source-valid | openhands-maximal-visible-action-context; 26 operations |
| `openhands-OpenAI__GPT-5-django__django-11179-4a42f87b` | OpenHands | true | 32 | source-valid | openhands-maximal-visible-action-context; 32 operations |
| `openhands-OpenAI__GPT-5-django__django-11206-3eaa47a7` | OpenHands | true | 27 | source-valid | openhands-maximal-visible-action-context; 27 operations |
| `openhands-OpenAI__GPT-5-django__django-11333-10687a03` | OpenHands | true | 31 | source-valid | openhands-maximal-visible-action-context; 31 operations |
| `openhands-OpenAI__GPT-5-django__django-11400-9d308b38` | OpenHands | false | 33 | source-valid | openhands-maximal-visible-action-context; 33 operations |
| `openhands-OpenAI__GPT-5-django__django-11433-a1e8e3a8` | OpenHands | true | 37 | source-valid | openhands-maximal-visible-action-context; 37 operations |
| `openhands-OpenAI__GPT-5-django__django-11451-8cce118d` | OpenHands | true | 25 | source-valid | openhands-maximal-visible-action-context; 25 operations |
| `openhands-OpenAI__GPT-5-django__django-11555-a1f1a268` | OpenHands | true | 30 | source-valid | openhands-maximal-visible-action-context; 30 operations |
| `openhands-OpenAI__GPT-5-django__django-11603-c7fd0824` | OpenHands | true | 45 | source-valid | openhands-maximal-visible-action-context; 45 operations |
| `openhands-OpenAI__GPT-5-django__django-11749-24e171f6` | OpenHands | true | 30 | source-valid | openhands-maximal-visible-action-context; 30 operations |
| `openhands-OpenAI__GPT-5-django__django-11790-6f214212` | OpenHands | false | 40 | source-valid | openhands-maximal-visible-action-context; 40 operations |
| `openhands-OpenAI__GPT-5-django__django-11815-5d01671e` | OpenHands | true | 28 | source-valid | openhands-maximal-visible-action-context; 28 operations |
| `openhands-OpenAI__GPT-5-django__django-11820-628d9793` | OpenHands | false | 38 | source-valid | openhands-maximal-visible-action-context; 38 operations |
| `openhands-OpenAI__GPT-5-django__django-11848-227c856d` | OpenHands | false | 20 | source-valid | openhands-maximal-visible-action-context; 20 operations |
| `openhands-OpenAI__GPT-5-django__django-11999-e5bbeaf0` | OpenHands | true | 31 | source-valid | openhands-maximal-visible-action-context; 31 operations |
| `openhands-OpenAI__GPT-5-django__django-12039-99ff4f8b` | OpenHands | true | 39 | source-valid | openhands-maximal-visible-action-context; 39 operations |
| `openhands-OpenAI__GPT-5-django__django-12050-ab113e49` | OpenHands | true | 28 | source-valid | openhands-maximal-visible-action-context; 28 operations |
| `openhands-OpenAI__GPT-5-django__django-12125-737fa0e8` | OpenHands | true | 44 | source-valid | openhands-maximal-visible-action-context; 44 operations |
| `openhands-OpenAI__GPT-5-django__django-12143-d3ae8e5d` | OpenHands | true | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-django__django-12155-0d6da542` | OpenHands | true | 27 | source-valid | openhands-maximal-visible-action-context; 27 operations |
| `openhands-OpenAI__GPT-5-django__django-12193-417f2e5e` | OpenHands | true | 29 | source-valid | openhands-maximal-visible-action-context; 29 operations |
| `openhands-OpenAI__GPT-5-django__django-12262-41e946b2` | OpenHands | true | 26 | source-valid | openhands-maximal-visible-action-context; 26 operations |
| `openhands-OpenAI__GPT-5-django__django-12273-1b422a26` | OpenHands | false | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-django__django-12276-800efa61` | OpenHands | true | 44 | source-valid | openhands-maximal-visible-action-context; 44 operations |
| `openhands-OpenAI__GPT-5-django__django-12304-cc2965e3` | OpenHands | false | 28 | source-valid | openhands-maximal-visible-action-context; 28 operations |
| `openhands-OpenAI__GPT-5-django__django-12406-31e1b541` | OpenHands | false | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-django__django-12419-2511c632` | OpenHands | true | 22 | source-valid | openhands-maximal-visible-action-context; 22 operations |
| `openhands-OpenAI__GPT-5-django__django-12663-bd7310c4` | OpenHands | true | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-django__django-12858-d5428d4f` | OpenHands | true | 37 | source-valid | openhands-maximal-visible-action-context; 37 operations |
| `openhands-OpenAI__GPT-5-django__django-13012-5c9c6d0d` | OpenHands | true | 41 | source-valid | openhands-maximal-visible-action-context; 41 operations |
| `openhands-OpenAI__GPT-5-django__django-13023-8e73db95` | OpenHands | false | 41 | source-valid | openhands-maximal-visible-action-context; 41 operations |
| `openhands-OpenAI__GPT-5-django__django-13028-da573811` | OpenHands | true | 39 | source-valid | openhands-maximal-visible-action-context; 39 operations |
| `openhands-OpenAI__GPT-5-django__django-13109-f3ebc647` | OpenHands | true | 44 | source-valid | openhands-maximal-visible-action-context; 44 operations |
| `openhands-OpenAI__GPT-5-django__django-13158-2005ee30` | OpenHands | true | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-django__django-13195-cbb7a0ba` | OpenHands | false | 36 | source-valid | openhands-maximal-visible-action-context; 36 operations |
| `openhands-OpenAI__GPT-5-django__django-13279-1ee67b92` | OpenHands | true | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-django__django-13343-70b942cf` | OpenHands | true | 36 | source-valid | openhands-maximal-visible-action-context; 36 operations |
| `openhands-OpenAI__GPT-5-django__django-13417-b9cf6b23` | OpenHands | true | 42 | source-valid | openhands-maximal-visible-action-context; 42 operations |
| `openhands-OpenAI__GPT-5-django__django-13449-d4928e17` | OpenHands | true | 46 | source-valid | openhands-maximal-visible-action-context; 46 operations |
| `openhands-OpenAI__GPT-5-django__django-13516-0b062160` | OpenHands | true | 31 | source-valid | openhands-maximal-visible-action-context; 31 operations |
| `openhands-OpenAI__GPT-5-django__django-13551-37eed156` | OpenHands | true | 46 | source-valid | openhands-maximal-visible-action-context; 46 operations |
| `openhands-OpenAI__GPT-5-django__django-13670-b062ecad` | OpenHands | true | 38 | source-valid | openhands-maximal-visible-action-context; 38 operations |
| `openhands-OpenAI__GPT-5-django__django-13809-9b66eaec` | OpenHands | true | 30 | source-valid | openhands-maximal-visible-action-context; 30 operations |
| `openhands-OpenAI__GPT-5-django__django-13820-836691f8` | OpenHands | true | 43 | source-valid | openhands-maximal-visible-action-context; 43 operations |
| `openhands-OpenAI__GPT-5-django__django-13925-2f10aef5` | OpenHands | true | 38 | source-valid | openhands-maximal-visible-action-context; 38 operations |
| `openhands-OpenAI__GPT-5-django__django-14089-7cc2152c` | OpenHands | true | 32 | source-valid | openhands-maximal-visible-action-context; 32 operations |
| `openhands-OpenAI__GPT-5-django__django-14140-193e0ceb` | OpenHands | true | 29 | source-valid | openhands-maximal-visible-action-context; 29 operations |
| `openhands-OpenAI__GPT-5-django__django-14311-5d70c3a7` | OpenHands | true | 34 | source-valid | openhands-maximal-visible-action-context; 34 operations |
| `openhands-OpenAI__GPT-5-django__django-14349-2d317299` | OpenHands | true | 30 | source-valid | openhands-maximal-visible-action-context; 30 operations |
| `openhands-OpenAI__GPT-5-django__django-14351-058e4e93` | OpenHands | false | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-django__django-14404-25e14391` | OpenHands | true | 35 | source-valid | openhands-maximal-visible-action-context; 35 operations |
| `openhands-OpenAI__GPT-5-django__django-14434-9f5a43d6` | OpenHands | true | 31 | source-valid | openhands-maximal-visible-action-context; 31 operations |
| `openhands-OpenAI__GPT-5-django__django-14500-bc22e241` | OpenHands | true | 30 | source-valid | openhands-maximal-visible-action-context; 30 operations |
| `openhands-OpenAI__GPT-5-django__django-14539-fdad2178` | OpenHands | true | 36 | source-valid | openhands-maximal-visible-action-context; 36 operations |
| `openhands-OpenAI__GPT-5-django__django-14765-924f3ce4` | OpenHands | true | 37 | source-valid | openhands-maximal-visible-action-context; 37 operations |
| `openhands-OpenAI__GPT-5-django__django-14787-477bbfba` | OpenHands | true | 15 | source-valid | openhands-maximal-visible-action-context; 15 operations |
| `openhands-OpenAI__GPT-5-django__django-14915-c39021a7` | OpenHands | true | 18 | source-valid | openhands-maximal-visible-action-context; 18 operations |
| `openhands-OpenAI__GPT-5-django__django-14999-fb59f194` | OpenHands | true | 30 | source-valid | openhands-maximal-visible-action-context; 30 operations |
| `openhands-OpenAI__GPT-5-django__django-15022-484c1b35` | OpenHands | true | 22 | source-valid | openhands-maximal-visible-action-context; 22 operations |
| `openhands-OpenAI__GPT-5-django__django-15103-8f250680` | OpenHands | true | 26 | source-valid | openhands-maximal-visible-action-context; 26 operations |
| `openhands-OpenAI__GPT-5-django__django-15104-148b1e60` | OpenHands | true | 31 | source-valid | openhands-maximal-visible-action-context; 31 operations |
| `openhands-OpenAI__GPT-5-django__django-15278-f285d65e` | OpenHands | true | 24 | source-valid | openhands-maximal-visible-action-context; 24 operations |
| `openhands-OpenAI__GPT-5-django__django-15368-d7c3d139` | OpenHands | true | 44 | source-valid | openhands-maximal-visible-action-context; 44 operations |
| `openhands-OpenAI__GPT-5-django__django-15380-e8b3a566` | OpenHands | true | 36 | source-valid | openhands-maximal-visible-action-context; 36 operations |
| `openhands-OpenAI__GPT-5-django__django-15382-b02d3059` | OpenHands | true | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-django__django-15467-da5dc0ae` | OpenHands | true | 31 | source-valid | openhands-maximal-visible-action-context; 31 operations |
| `openhands-OpenAI__GPT-5-django__django-15499-ac92f001` | OpenHands | true | 32 | source-valid | openhands-maximal-visible-action-context; 32 operations |
| `openhands-OpenAI__GPT-5-django__django-15503-d939f22a` | OpenHands | false | 24 | source-valid | openhands-maximal-visible-action-context; 24 operations |
| `openhands-OpenAI__GPT-5-django__django-15563-19924064` | OpenHands | false | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-django__django-15569-62054620` | OpenHands | true | 43 | source-valid | openhands-maximal-visible-action-context; 43 operations |
| `openhands-OpenAI__GPT-5-django__django-15732-4b352587` | OpenHands | false | 46 | source-valid | openhands-maximal-visible-action-context; 46 operations |
| `openhands-OpenAI__GPT-5-django__django-15741-d7b75d95` | OpenHands | false | 24 | source-valid | openhands-maximal-visible-action-context; 24 operations |
| `openhands-OpenAI__GPT-5-django__django-15814-08049bd6` | OpenHands | true | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-django__django-15863-816738f2` | OpenHands | true | 23 | source-valid | openhands-maximal-visible-action-context; 23 operations |
| `openhands-OpenAI__GPT-5-django__django-15930-f153f9fc` | OpenHands | true | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-django__django-15957-a39a6ef5` | OpenHands | true | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-django__django-15987-d0ca733a` | OpenHands | true | 39 | source-valid | openhands-maximal-visible-action-context; 39 operations |
| `openhands-OpenAI__GPT-5-django__django-16032-20a5e8c7` | OpenHands | true | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-django__django-16429-66fad31a` | OpenHands | true | 21 | source-valid | openhands-maximal-visible-action-context; 21 operations |
| `openhands-OpenAI__GPT-5-django__django-16454-7ceddd3b` | OpenHands | true | 40 | source-valid | openhands-maximal-visible-action-context; 40 operations |
| `openhands-OpenAI__GPT-5-django__django-16485-3e4d6956` | OpenHands | true | 23 | source-valid | openhands-maximal-visible-action-context; 23 operations |
| `openhands-OpenAI__GPT-5-django__django-16527-28b1af01` | OpenHands | true | 19 | source-valid | openhands-maximal-visible-action-context; 19 operations |
| `openhands-OpenAI__GPT-5-django__django-16631-025f3fd2` | OpenHands | false | 46 | source-valid | openhands-maximal-visible-action-context; 46 operations |
| `openhands-OpenAI__GPT-5-django__django-16661-6655407b` | OpenHands | true | 21 | source-valid | openhands-maximal-visible-action-context; 21 operations |
| `openhands-OpenAI__GPT-5-django__django-16819-bf405b1f` | OpenHands | true | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-django__django-17029-3798d1c6` | OpenHands | true | 34 | source-valid | openhands-maximal-visible-action-context; 34 operations |
| `openhands-OpenAI__GPT-5-django__django-17087-fa8d1e0f` | OpenHands | true | 44 | source-valid | openhands-maximal-visible-action-context; 44 operations |
| `openhands-OpenAI__GPT-5-django__django-7530-638247b7` | OpenHands | true | 33 | source-valid | openhands-maximal-visible-action-context; 33 operations |
| `openhands-OpenAI__GPT-5-dna-insert-070be780` | OpenHands | false | 14 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-enemy-grid-escape-83f149ee` | OpenHands | true | 32 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-feal-linear-cryptanalysis-35e4e30d` | OpenHands | true | 12 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-fibonacci-server-292fc147` | OpenHands | true | 14 | source-valid | openhands-agent-actions; 14 operations |
| `openhands-OpenAI__GPT-5-filter-js-from-html-766374ea` | OpenHands | false | 31 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-financial-document-processor-6e957148` | OpenHands | false | 12 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-find-official-code-1be1e012` | OpenHands | false | 20 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-find-restaurant-fd9ef9a6` | OpenHands | false | 22 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-fix-code-vulnerability-5864dfed` | OpenHands | true | 23 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-fix-git-45ee3a9f` | OpenHands | true | 14 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-fix-ocaml-gc-186b97d9` | OpenHands | true | 24 | source-valid | openhands-agent-actions; 24 operations |
| `openhands-OpenAI__GPT-5-fix-permissions-2bbc8e2d` | OpenHands | true | 13 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-fmri-encoding-r-dccb7053` | OpenHands | true | 17 | source-valid | openhands-agent-actions; 17 operations |
| `openhands-OpenAI__GPT-5-form-filling-1ff403d3` | OpenHands | true | 32 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-gcc-compiler-optimization-c66f179c` | OpenHands | true | 14 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-get-bitcoin-nodes-596dd62a` | OpenHands | false | 23 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-git-multibranch-b9a7c2ce` | OpenHands | false | 33 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-git-workflow-hack-d7ab1c99` | OpenHands | true | 34 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-hdfs-deployment-2d36343d` | OpenHands | true | 21 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-hf-lora-adapter-74d2d66e` | OpenHands | true | 23 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-hf-model-inference-58d4c9f2` | OpenHands | true | 21 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-hf-train-lora-adapter-c7ba9feb` | OpenHands | false | 28 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-home-server-https-af791665` | OpenHands | false | 14 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-html-finance-verify-d79ce44a` | OpenHands | false | 14 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-huggingface__transformers-12981-bb6ea81f` | OpenHands | true | 21 | source-valid | openhands-maximal-visible-action-context; 21 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-13693-22a78bfd` | OpenHands | true | 41 | source-valid | openhands-maximal-visible-action-context; 41 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-13865-a6eb1183` | OpenHands | true | 23 | source-valid | openhands-maximal-visible-action-context; 23 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-13989-6ebe445f` | OpenHands | true | 51 | source-valid | openhands-maximal-visible-action-context; 51 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-15158-f2e4f9e6` | OpenHands | true | 42 | source-valid | openhands-maximal-visible-action-context; 42 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-15795-743fd3d3` | OpenHands | true | 41 | source-valid | openhands-maximal-visible-action-context; 41 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-16198-298e0a94` | OpenHands | true | 46 | source-valid | openhands-maximal-visible-action-context; 46 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-17082-8d986335` | OpenHands | true | 27 | source-valid | openhands-maximal-visible-action-context; 27 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-19590-8adf6ec7` | OpenHands | true | 43 | source-valid | openhands-maximal-visible-action-context; 43 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-20136-9ef8b462` | OpenHands | false | 54 | source-valid | openhands-maximal-visible-action-context; 54 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-21768-3d7857a2` | OpenHands | true | 31 | source-valid | openhands-maximal-visible-action-context; 31 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-21969-9e70f015` | OpenHands | true | 30 | source-valid | openhands-maximal-visible-action-context; 30 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-22458-ebb9ca50` | OpenHands | true | 26 | source-valid | openhands-maximal-visible-action-context; 26 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-22920-0188fcc0` | OpenHands | true | 20 | source-valid | openhands-maximal-visible-action-context; 20 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-23126-d6300910` | OpenHands | true | 35 | source-valid | openhands-maximal-visible-action-context; 35 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-23223-bf8abbe6` | OpenHands | true | 40 | source-valid | openhands-maximal-visible-action-context; 40 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-24238-2d178ce3` | OpenHands | true | 34 | source-valid | openhands-maximal-visible-action-context; 34 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-27463-9129234e` | OpenHands | true | 85 | source-valid | openhands-maximal-visible-action-context; 85 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-28535-2ccf9291` | OpenHands | true | 45 | source-valid | openhands-maximal-visible-action-context; 45 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-29311-edd5529b` | OpenHands | true | 42 | source-valid | openhands-maximal-visible-action-context; 42 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-29449-febb45eb` | OpenHands | true | 31 | source-valid | openhands-maximal-visible-action-context; 31 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-30556-fb7d24c5` | OpenHands | true | 26 | source-valid | openhands-maximal-visible-action-context; 26 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-3716-b90a1926` | OpenHands | true | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-5122-27a9c664` | OpenHands | true | 43 | source-valid | openhands-maximal-visible-action-context; 43 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-6098-6fbefef7` | OpenHands | true | 56 | source-valid | openhands-maximal-visible-action-context; 56 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-7078-c48fab49` | OpenHands | true | 35 | source-valid | openhands-maximal-visible-action-context; 35 operations |
| `openhands-OpenAI__GPT-5-huggingface__transformers-8624-ec8fe9b3` | OpenHands | true | 28 | source-valid | openhands-maximal-visible-action-context; 28 operations |
| `openhands-OpenAI__GPT-5-hydra-debug-slurm-mode-29a7e848` | OpenHands | false | 23 | source-valid | openhands-agent-actions; 23 operations |
| `openhands-OpenAI__GPT-5-implement-eigenvectors-from-eigenvalues-research-paper-54d1ccc6` | OpenHands | false | 30 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-incompatible-python-fasttext-a448fdd0` | OpenHands | false | 13 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-install-klee-minimal-f4977da9` | OpenHands | false | 16 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-install-windows-3.11-5f5c52fe` | OpenHands | false | 23 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-install-windows-xp-be27fb42` | OpenHands | false | 22 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-0fd88717c953b92ed8a50495d55e630eb5d59166-vba6da65a0f3baefda7a058ebbd0a8dcafb8512f5-5b83347a` | OpenHands | false | 33 | source-valid | openhands-maximal-visible-action-context; 33 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-1a4644ff15355fd696ac5b9d074a566a80fe7ca3-v30a923fb5c164d6cd18280c02422f75e611e8fb2-e6e185ca` | OpenHands | false | 26 | source-valid | openhands-maximal-visible-action-context; 26 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-1b70260d5aa2f6c9782fd2b848e8d16566e50d85-vba6da65a0f3baefda7a058ebbd0a8dcafb8512f5-e20126a5` | OpenHands | false | 40 | source-valid | openhands-maximal-visible-action-context; 40 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-4c5ce5a1a9e79a845aff4978cfeb72a0d4ecf7d6-v1055803c3a812189a1133297f7f5468579283f86-28be7ce9` | OpenHands | false | 55 | source-valid | openhands-maximal-visible-action-context; 55 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-5260527c4a71bfed99d803e687dd19619423b134-vba6da65a0f3baefda7a058ebbd0a8dcafb8512f5-f32bf751` | OpenHands | false | 40 | source-valid | openhands-maximal-visible-action-context; 40 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-5640093f1ca63fd6af231cc8a7fb7d40e1907b8c-vba6da65a0f3baefda7a058ebbd0a8dcafb8512f5-b3954c1c` | OpenHands | false | 41 | source-valid | openhands-maximal-visible-action-context; 41 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-6cc97447aac5816745278f3735af128afb255c81-v0f01c69f1e2528b935359cfe578530722bca2c59-83adb675` | OpenHands | false | 60 | source-valid | openhands-maximal-visible-action-context; 60 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-709484969c8a4ffd74b839a673431a8c5caa6457-vba6da65a0f3baefda7a058ebbd0a8dcafb8512f5-fa9c1fc1` | OpenHands | false | 33 | source-valid | openhands-maximal-visible-action-context; 33 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-77658704217d5f166404fc67997203c25381cb6e-v390e508d27db7a51eece36bb6d9698b63a5b638a-b30050fb` | OpenHands | false | 38 | source-valid | openhands-maximal-visible-action-context; 38 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-8127abbc298cabf04aaa89a478fc5e5e3432a6fc-v30a923fb5c164d6cd18280c02422f75e611e8fb2-b2c3dcef` | OpenHands | false | 31 | source-valid | openhands-maximal-visible-action-context; 31 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-83909bfa22573777e3db5688773bda59721962ad-vba6da65a0f3baefda7a058ebbd0a8dcafb8512f5-dda94ca0` | OpenHands | false | 43 | source-valid | openhands-maximal-visible-action-context; 43 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-9142be2f6cabbe6597c9254c5bb9186d17036d55-v0f01c69f1e2528b935359cfe578530722bca2c59-6f557e16` | OpenHands | false | 34 | source-valid | openhands-maximal-visible-action-context; 34 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-942424e10b2095a173dbd78e7128f52f7995849b-v30a923fb5c164d6cd18280c02422f75e611e8fb2-83422c29` | OpenHands | false | 37 | source-valid | openhands-maximal-visible-action-context; 37 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-949c503f2ef4b2c5d668af0492a5c0db1ab86140-v0f01c69f1e2528b935359cfe578530722bca2c59-9a3f4648` | OpenHands | false | 34 | source-valid | openhands-maximal-visible-action-context; 34 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-a7d2a4e03209cff1e97e59fd54bb2b05fdbdbec6-v0f01c69f1e2528b935359cfe578530722bca2c59-1c0382c3` | OpenHands | false | 35 | source-valid | openhands-maximal-visible-action-context; 35 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-b2a289dcbb702003377221e25f62c8a3608f0e89-v173091e2e36d38c978002990795f66cfc0af30ad-733b07ca` | OpenHands | false | 37 | source-valid | openhands-maximal-visible-action-context; 37 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-b5e0293645570f3f404ad1dbbe5f006956ada0df-v0f01c69f1e2528b935359cfe578530722bca2c59-9cc4c3d7` | OpenHands | false | 28 | source-valid | openhands-maximal-visible-action-context; 28 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-bec27fb4c0a40c5f8bbcf26a475704227d65ee73-v30a923fb5c164d6cd18280c02422f75e611e8fb2-9aee5e69` | OpenHands | false | 37 | source-valid | openhands-maximal-visible-action-context; 37 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-bf98f031f3f5af31a2d78dc2f0a58fe92ebae0bb-v1055803c3a812189a1133297f7f5468579283f86-c62b0ad0` | OpenHands | false | 64 | source-valid | openhands-maximal-visible-action-context; 64 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-cb94c0cc550df9e98f1247bc71d8c2b861c75049-v1055803c3a812189a1133297f7f5468579283f86-6e13d2fc` | OpenHands | false | 44 | source-valid | openhands-maximal-visible-action-context; 44 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad-51499bc6` | OpenHands | false | 51 | source-valid | openhands-maximal-visible-action-context; 51 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-e9e6001263f51103e96e58ad382660df0f3d0e39-v30a923fb5c164d6cd18280c02422f75e611e8fb2-a2edf697` | OpenHands | false | 18 | source-valid | openhands-maximal-visible-action-context; 18 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-f8ef34672b961a95ec7282643679492862c688ec-vba6da65a0f3baefda7a058ebbd0a8dcafb8512f5-9a7ccdd2` | OpenHands | false | 43 | source-valid | openhands-maximal-visible-action-context; 43 operations |
| `openhands-OpenAI__GPT-5-instance_ansible__ansible-fb144c44144f8bd3542e71f5db62b6d322c7bd85-vba6da65a0f3baefda7a058ebbd0a8dcafb8512f5-57b35ea6` | OpenHands | false | 41 | source-valid | openhands-maximal-visible-action-context; 41 operations |
| `openhands-OpenAI__GPT-5-instance_element-hq__element-web-5dfde12c1c1c0b6e48f17e3405468593e39d9492-vnan-c55fbc3d` | OpenHands | true | 66 | source-valid | openhands-maximal-visible-action-context; 66 operations |
| `openhands-OpenAI__GPT-5-instance_element-hq__element-web-aeabf3b18896ac1eb7ae9757e66ce886120f8309-vnan-11132852` | OpenHands | true | 65 | source-valid | openhands-maximal-visible-action-context; 65 operations |
| `openhands-OpenAI__GPT-5-instance_element-hq__element-web-fe14847bb9bb07cab1b9c6c54335ff22ca5e516a-vnan-450efae7` | OpenHands | true | 72 | source-valid | openhands-maximal-visible-action-context; 72 operations |
| `openhands-OpenAI__GPT-5-instance_internetarchive__openlibrary-60725705782832a2cb22e17c49697948a42a9d03-v298a7a812ceed28c4c18355a091f1b268fe56d86-ae669a0a` | OpenHands | false | 34 | source-valid | openhands-maximal-visible-action-context; 34 operations |
| `openhands-OpenAI__GPT-5-instance_internetarchive__openlibrary-bb152d23c004f3d68986877143bb0f83531fe401-ve8c8d62a2b60610a3c4631f5f23ed866bada9818-75152ca2` | OpenHands | false | 39 | source-valid | openhands-maximal-visible-action-context; 39 operations |
| `openhands-OpenAI__GPT-5-instance_internetarchive__openlibrary-e1e502986a3b003899a8347ac8a7ff7b08cbfc39-v08d8e8889ec945ab821fb156c04c7d2e2810debb-98f1fc71` | OpenHands | false | 44 | source-valid | openhands-maximal-visible-action-context; 44 operations |
| `openhands-OpenAI__GPT-5-instance_qutebrowser__qutebrowser-2dd8966fdcf11972062c540b7a787e4d0de8d372-v363c8a7e5ccdf6968fc7ab84a2053ac78036691d-a9fc6e37` | OpenHands | false | 62 | source-valid | openhands-maximal-visible-action-context; 62 operations |
| `openhands-OpenAI__GPT-5-instance_qutebrowser__qutebrowser-473a15f7908f2bb6d670b0e908ab34a28d8cf7e2-v363c8a7e5ccdf6968fc7ab84a2053ac78036691d-3f5c4067` | OpenHands | false | 69 | source-valid | openhands-maximal-visible-action-context; 69 operations |
| `openhands-OpenAI__GPT-5-instance_qutebrowser__qutebrowser-bedc9f7fadf93f83d8dee95feeecb9922b6f063f-v2ef375ac784985212b1805e1d0431dc8f1b3c171-974761f6` | OpenHands | false | 31 | source-valid | openhands-maximal-visible-action-context; 31 operations |
| `openhands-OpenAI__GPT-5-instance_qutebrowser__qutebrowser-de4a1c1a2839b5b49c3d4ce21d39de48d24e2091-v2ef375ac784985212b1805e1d0431dc8f1b3c171-6735e9d7` | OpenHands | true | 37 | source-valid | openhands-maximal-visible-action-context; 37 operations |
| `openhands-OpenAI__GPT-5-instance_qutebrowser__qutebrowser-f8e7fea0becae25ae20606f1422068137189fe9e-7348b67b` | OpenHands | false | 43 | source-valid | openhands-maximal-visible-action-context; 43 operations |
| `openhands-OpenAI__GPT-5-intrusion-detection-a9adab04` | OpenHands | false | 13 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-keras-team__keras-18553-96879c97` | OpenHands | true | 25 | source-valid | openhands-maximal-visible-action-context; 25 operations |
| `openhands-OpenAI__GPT-5-keras-team__keras-18871-9b44c674` | OpenHands | true | 42 | source-valid | openhands-maximal-visible-action-context; 42 operations |
| `openhands-OpenAI__GPT-5-keras-team__keras-19201-78909bc7` | OpenHands | true | 31 | source-valid | openhands-maximal-visible-action-context; 31 operations |
| `openhands-OpenAI__GPT-5-keras-team__keras-19484-74f5c884` | OpenHands | true | 33 | source-valid | openhands-maximal-visible-action-context; 33 operations |
| `openhands-OpenAI__GPT-5-keras-team__keras-19636-c39cfb90` | OpenHands | true | 41 | source-valid | openhands-maximal-visible-action-context; 41 operations |
| `openhands-OpenAI__GPT-5-keras-team__keras-19775-44ebc402` | OpenHands | true | 26 | source-valid | openhands-maximal-visible-action-context; 26 operations |
| `openhands-OpenAI__GPT-5-keras-team__keras-19838-9f7e7a04` | OpenHands | true | 44 | source-valid | openhands-maximal-visible-action-context; 44 operations |
| `openhands-OpenAI__GPT-5-keras-team__keras-19844-006a5734` | OpenHands | true | 45 | source-valid | openhands-maximal-visible-action-context; 45 operations |
| `openhands-OpenAI__GPT-5-keras-team__keras-19863-31ae5ddf` | OpenHands | true | 41 | source-valid | openhands-maximal-visible-action-context; 41 operations |
| `openhands-OpenAI__GPT-5-keras-team__keras-19924-22577cfd` | OpenHands | true | 29 | source-valid | openhands-maximal-visible-action-context; 29 operations |
| `openhands-OpenAI__GPT-5-keras-team__keras-19973-1562718f` | OpenHands | true | 30 | source-valid | openhands-maximal-visible-action-context; 30 operations |
| `openhands-OpenAI__GPT-5-kv-store-grpc-fce0d6c4` | OpenHands | false | 19 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-langchain-ai__langchain-19331-4460742e` | OpenHands | true | 64 | source-valid | openhands-maximal-visible-action-context; 64 operations |
| `openhands-OpenAI__GPT-5-langchain-ai__langchain-4009-6c1ad563` | OpenHands | true | 32 | source-valid | openhands-maximal-visible-action-context; 32 operations |
| `openhands-OpenAI__GPT-5-langchain-ai__langchain-5609-4096132f` | OpenHands | true | 34 | source-valid | openhands-maximal-visible-action-context; 34 operations |
| `openhands-OpenAI__GPT-5-largest-eigenval-02947cc3` | OpenHands | false | 23 | excluded | openhands-agent-actions emitted 24 operations; public step_count is 23 |
| `openhands-OpenAI__GPT-5-leelachess0-pytorch-conversion-fbd9590c` | OpenHands | false | 12 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-llm-inference-batching-scheduler-838051ac` | OpenHands | false | 21 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-llm-spec-decoding-3166a2e9` | OpenHands | false | 14 | source-valid | openhands-agent-actions; 14 operations |
| `openhands-OpenAI__GPT-5-mailman-17fed2a9` | OpenHands | false | 15 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-14623-8f9f7df9` | OpenHands | true | 46 | source-valid | openhands-maximal-visible-action-context; 46 operations |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-20676-6de044eb` | OpenHands | false | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-20826-a8689b03` | OpenHands | false | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-22719-3a0e9135` | OpenHands | true | 38 | source-valid | openhands-maximal-visible-action-context; 38 operations |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-22865-993404bc` | OpenHands | false | 26 | source-valid | openhands-maximal-visible-action-context; 26 operations |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-22871-6809a417` | OpenHands | true | 29 | source-valid | openhands-maximal-visible-action-context; 29 operations |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-23299-b99579d0` | OpenHands | false | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-23314-a839906b` | OpenHands | true | 32 | source-valid | openhands-maximal-visible-action-context; 32 operations |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-24149-6cb0332a` | OpenHands | true | 13 | source-valid | openhands-maximal-visible-action-context; 13 operations |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-24570-8e729dfb` | OpenHands | false | 28 | source-valid | openhands-maximal-visible-action-context; 28 operations |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-24627-6dc008f4` | OpenHands | true | 45 | source-valid | openhands-maximal-visible-action-context; 45 operations |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-25122-eaeaac2b` | OpenHands | true | 32 | source-valid | openhands-maximal-visible-action-context; 32 operations |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-25311-b8a88259` | OpenHands | false | 44 | source-valid | openhands-maximal-visible-action-context; 44 operations |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-25332-e85f2eff` | OpenHands | false | 36 | source-valid | openhands-maximal-visible-action-context; 36 operations |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-25479-fcab7ab1` | OpenHands | false | 34 | source-valid | openhands-maximal-visible-action-context; 34 operations |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-25775-154f8978` | OpenHands | true | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-26113-3e60723a` | OpenHands | true | 33 | source-valid | openhands-maximal-visible-action-context; 33 operations |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-26208-7d6b7705` | OpenHands | false | 47 | source-valid | openhands-maximal-visible-action-context; 47 operations |
| `openhands-OpenAI__GPT-5-matplotlib__matplotlib-26342-77c050b8` | OpenHands | true | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-mcmc-sampling-stan-463cb85c` | OpenHands | false | 37 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-merge-diff-arc-agi-task-d91f31a2` | OpenHands | true | 14 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-microsoft__vscode-109750-0071ea66` | OpenHands | true | 34 | source-valid | openhands-maximal-visible-action-context; 34 operations |
| `openhands-OpenAI__GPT-5-microsoft__vscode-110094-a10dde1e` | OpenHands | true | 43 | source-valid | openhands-maximal-visible-action-context; 43 operations |
| `openhands-OpenAI__GPT-5-microsoft__vscode-135197-309ff193` | OpenHands | true | 38 | source-valid | openhands-maximal-visible-action-context; 38 operations |
| `openhands-OpenAI__GPT-5-microsoft__vscode-153121-9abfbc86` | OpenHands | true | 34 | source-valid | openhands-maximal-visible-action-context; 34 operations |
| `openhands-OpenAI__GPT-5-microsoft__vscode-153857-2ba91a64` | OpenHands | true | 69 | source-valid | openhands-maximal-visible-action-context; 69 operations |
| `openhands-OpenAI__GPT-5-microsoft__vscode-160342-be2f227f` | OpenHands | true | 39 | source-valid | openhands-maximal-visible-action-context; 39 operations |
| `openhands-OpenAI__GPT-5-microsoft__vscode-177084-3281322c` | OpenHands | true | 37 | source-valid | openhands-maximal-visible-action-context; 37 operations |
| `openhands-OpenAI__GPT-5-mlflow-register-bdcf25a8` | OpenHands | true | 17 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-modernize-scientific-stack-979d4b60` | OpenHands | true | 13 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-mteb-eval-e68b82bd` | OpenHands | true | 12 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-mui__material-ui-11451-bfbf6f73` | OpenHands | true | 28 | source-valid | openhands-maximal-visible-action-context; 28 operations |
| `openhands-OpenAI__GPT-5-mui__material-ui-11987-55b4bbe6` | OpenHands | true | 27 | source-valid | openhands-maximal-visible-action-context; 27 operations |
| `openhands-OpenAI__GPT-5-mui__material-ui-12236-867e02cd` | OpenHands | true | 63 | source-valid | openhands-maximal-visible-action-context; 63 operations |
| `openhands-OpenAI__GPT-5-mui__material-ui-13534-53934742` | OpenHands | true | 30 | source-valid | openhands-maximal-visible-action-context; 30 operations |
| `openhands-OpenAI__GPT-5-mui__material-ui-13778-83d0b364` | OpenHands | true | 20 | source-valid | openhands-maximal-visible-action-context; 20 operations |
| `openhands-OpenAI__GPT-5-mui__material-ui-15359-ef60852f` | OpenHands | true | 37 | source-valid | openhands-maximal-visible-action-context; 37 operations |
| `openhands-OpenAI__GPT-5-mui__material-ui-18141-f3954aea` | OpenHands | true | 24 | source-valid | openhands-maximal-visible-action-context; 24 operations |
| `openhands-OpenAI__GPT-5-mui__material-ui-18257-2e939e36` | OpenHands | true | 33 | source-valid | openhands-maximal-visible-action-context; 33 operations |
| `openhands-OpenAI__GPT-5-mui__material-ui-18683-5753f295` | OpenHands | true | 22 | source-valid | openhands-maximal-visible-action-context; 22 operations |
| `openhands-OpenAI__GPT-5-mui__material-ui-19072-fca4d8ee` | OpenHands | true | 37 | source-valid | openhands-maximal-visible-action-context; 37 operations |
| `openhands-OpenAI__GPT-5-mui__material-ui-19121-ef420de9` | OpenHands | true | 33 | source-valid | openhands-maximal-visible-action-context; 33 operations |
| `openhands-OpenAI__GPT-5-mui__material-ui-23229-7eece48c` | OpenHands | true | 24 | source-valid | openhands-maximal-visible-action-context; 24 operations |
| `openhands-OpenAI__GPT-5-mui__material-ui-26061-eb46fa1b` | OpenHands | true | 44 | source-valid | openhands-maximal-visible-action-context; 44 operations |
| `openhands-OpenAI__GPT-5-mui__material-ui-26807-24b87c4a` | OpenHands | true | 58 | source-valid | openhands-maximal-visible-action-context; 58 operations |
| `openhands-OpenAI__GPT-5-mui__material-ui-28186-58517160` | OpenHands | true | 22 | source-valid | openhands-maximal-visible-action-context; 22 operations |
| `openhands-OpenAI__GPT-5-mui__material-ui-28813-3ba6cc10` | OpenHands | true | 39 | source-valid | openhands-maximal-visible-action-context; 39 operations |
| `openhands-OpenAI__GPT-5-mui__material-ui-29023-15b3f749` | OpenHands | true | 33 | source-valid | openhands-maximal-visible-action-context; 33 operations |
| `openhands-OpenAI__GPT-5-mui__material-ui-34610-216c0048` | OpenHands | true | 46 | source-valid | openhands-maximal-visible-action-context; 46 operations |
| `openhands-OpenAI__GPT-5-mui__material-ui-42412-077fc45c` | OpenHands | true | 33 | source-valid | openhands-maximal-visible-action-context; 33 operations |
| `openhands-OpenAI__GPT-5-multi-source-data-merger-5f49c785` | OpenHands | true | 18 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-npm-conflict-resolution-52c3b8b8` | OpenHands | true | 19 | source-valid | openhands-agent-actions; 19 operations |
| `openhands-OpenAI__GPT-5-openssl-selfsigned-cert-813c84fe` | OpenHands | false | 19 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-optimal-transport-aea98f31` | OpenHands | false | 12 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-overfull-hbox-be8933f3` | OpenHands | false | 16 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-pallets__flask-5014-6bf53d93` | OpenHands | true | 34 | source-valid | openhands-maximal-visible-action-context; 34 operations |
| `openhands-OpenAI__GPT-5-parallel-particle-simulator-bd802119` | OpenHands | false | 35 | excluded | openhands-agent-actions emitted 36 operations; public step_count is 35 |
| `openhands-OpenAI__GPT-5-parallelize-compute-squares-00aba5bb` | OpenHands | true | 14 | source-valid | openhands-agent-actions; 14 operations |
| `openhands-OpenAI__GPT-5-parallelize-graph-60d7a7b7` | OpenHands | true | 27 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-password-recovery-2b0e8478` | OpenHands | true | 31 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-path-tracing-6f1a1bf0` | OpenHands | false | 35 | excluded | openhands-agent-actions emitted 42 operations; public step_count is 35 |
| `openhands-OpenAI__GPT-5-path-tracing-reverse-5375e7d0` | OpenHands | false | 28 | source-valid | openhands-agent-actions; 28 operations |
| `openhands-OpenAI__GPT-5-play-lord-7413c06b` | OpenHands | false | 25 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-play-zork-easy-e7f220b6` | OpenHands | false | 12 | source-valid | openhands-agent-actions; 12 operations |
| `openhands-OpenAI__GPT-5-polyglot-c-py-5a74e7ac` | OpenHands | false | 16 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-port-compressor-53a2b666` | OpenHands | false | 105 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-portfolio-optimization-bfc4d5e4` | OpenHands | false | 17 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-predicate-pushdown-bench-77410ef2` | OpenHands | false | 19 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-predict-customer-churn-6360db1d` | OpenHands | false | 12 | source-valid | openhands-agent-actions; 12 operations |
| `openhands-OpenAI__GPT-5-prettier__prettier-12930-5da56ae8` | OpenHands | true | 30 | source-valid | openhands-maximal-visible-action-context; 30 operations |
| `openhands-OpenAI__GPT-5-prettier__prettier-14400-9207921a` | OpenHands | true | 33 | source-valid | openhands-maximal-visible-action-context; 33 operations |
| `openhands-OpenAI__GPT-5-prettier__prettier-3515-0d82b41d` | OpenHands | true | 35 | source-valid | openhands-maximal-visible-action-context; 35 operations |
| `openhands-OpenAI__GPT-5-prettier__prettier-361-7d8d70b7` | OpenHands | true | 30 | source-valid | openhands-maximal-visible-action-context; 30 operations |
| `openhands-OpenAI__GPT-5-prettier__prettier-3723-0d4bb0b6` | OpenHands | true | 39 | source-valid | openhands-maximal-visible-action-context; 39 operations |
| `openhands-OpenAI__GPT-5-prettier__prettier-459-d812ee52` | OpenHands | true | 35 | source-valid | openhands-maximal-visible-action-context; 35 operations |
| `openhands-OpenAI__GPT-5-prettier__prettier-6604-f6c47d03` | OpenHands | true | 65 | source-valid | openhands-maximal-visible-action-context; 65 operations |
| `openhands-OpenAI__GPT-5-prettier__prettier-8046-0bb849c5` | OpenHands | true | 45 | source-valid | openhands-maximal-visible-action-context; 45 operations |
| `openhands-OpenAI__GPT-5-processing-pipeline-a1543eaf` | OpenHands | true | 19 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-psf__requests-6028-1508a463` | OpenHands | false | 40 | source-valid | openhands-maximal-visible-action-context; 40 operations |
| `openhands-OpenAI__GPT-5-puzzle-solver-3ddc78ab` | OpenHands | true | 13 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-pydata__xarray-2905-6eb6cd67` | OpenHands | true | 23 | source-valid | openhands-maximal-visible-action-context; 23 operations |
| `openhands-OpenAI__GPT-5-pydata__xarray-4075-6aab4c69` | OpenHands | true | 30 | source-valid | openhands-maximal-visible-action-context; 30 operations |
| `openhands-OpenAI__GPT-5-pydata__xarray-4695-759c8995` | OpenHands | true | 25 | source-valid | openhands-maximal-visible-action-context; 25 operations |
| `openhands-OpenAI__GPT-5-pydata__xarray-4966-a48c05ba` | OpenHands | true | 23 | source-valid | openhands-maximal-visible-action-context; 23 operations |
| `openhands-OpenAI__GPT-5-pydata__xarray-6461-050b4d36` | OpenHands | true | 40 | source-valid | openhands-maximal-visible-action-context; 40 operations |
| `openhands-OpenAI__GPT-5-pydata__xarray-6599-8f177c3f` | OpenHands | true | 30 | source-valid | openhands-maximal-visible-action-context; 30 operations |
| `openhands-OpenAI__GPT-5-pydata__xarray-6721-6c1f0e24` | OpenHands | true | 40 | source-valid | openhands-maximal-visible-action-context; 40 operations |
| `openhands-OpenAI__GPT-5-pydata__xarray-7229-fd493310` | OpenHands | false | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-pydata__xarray-7233-3861baee` | OpenHands | true | 19 | source-valid | openhands-maximal-visible-action-context; 19 operations |
| `openhands-OpenAI__GPT-5-pylint-dev__pylint-4604-4102688b` | OpenHands | false | 47 | source-valid | openhands-maximal-visible-action-context; 47 operations |
| `openhands-OpenAI__GPT-5-pylint-dev__pylint-4970-a70c1ebe` | OpenHands | false | 32 | source-valid | openhands-maximal-visible-action-context; 32 operations |
| `openhands-OpenAI__GPT-5-pylint-dev__pylint-8898-2e57fc74` | OpenHands | false | 34 | source-valid | openhands-maximal-visible-action-context; 34 operations |
| `openhands-OpenAI__GPT-5-pypi-server-5533ac61` | OpenHands | false | 22 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-pytest-dev__pytest-10081-e80cbf24` | OpenHands | true | 20 | source-valid | openhands-maximal-visible-action-context; 20 operations |
| `openhands-OpenAI__GPT-5-pytest-dev__pytest-10356-178189eb` | OpenHands | false | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-pytest-dev__pytest-5262-96194eee` | OpenHands | true | 33 | source-valid | openhands-maximal-visible-action-context; 33 operations |
| `openhands-OpenAI__GPT-5-pytest-dev__pytest-5631-b90dbe02` | OpenHands | true | 26 | source-valid | openhands-maximal-visible-action-context; 26 operations |
| `openhands-OpenAI__GPT-5-pytest-dev__pytest-5809-af0c5e4a` | OpenHands | true | 27 | source-valid | openhands-maximal-visible-action-context; 27 operations |
| `openhands-OpenAI__GPT-5-pytest-dev__pytest-7205-282aadca` | OpenHands | false | 39 | source-valid | openhands-maximal-visible-action-context; 39 operations |
| `openhands-OpenAI__GPT-5-pytest-dev__pytest-7236-8ee7fd31` | OpenHands | true | 23 | source-valid | openhands-maximal-visible-action-context; 23 operations |
| `openhands-OpenAI__GPT-5-pytest-dev__pytest-7324-b33c996d` | OpenHands | true | 38 | source-valid | openhands-maximal-visible-action-context; 38 operations |
| `openhands-OpenAI__GPT-5-pytest-dev__pytest-7432-e4da5e95` | OpenHands | true | 27 | source-valid | openhands-maximal-visible-action-context; 27 operations |
| `openhands-OpenAI__GPT-5-pytorch-model-cli-5792944d` | OpenHands | false | 12 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-pytorch-model-recovery-bb63ee33` | OpenHands | false | 13 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-query-optimize-ce2e43d2` | OpenHands | false | 13 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-raman-fitting-5b6353cd` | OpenHands | false | 15 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-rare-mineral-allocation-9033b1c9` | OpenHands | false | 11 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-regex-chess-c9013ba7` | OpenHands | false | 16 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-reshard-c4-data-9ab884ac` | OpenHands | false | 21 | source-valid | openhands-agent-actions; 21 operations |
| `openhands-OpenAI__GPT-5-reverse-engineering-41949138` | OpenHands | true | 34 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-rstan-to-pystan-35166526` | OpenHands | true | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-OpenAI__GPT-5-run-pdp11-code-40544045` | OpenHands | false | 25 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-sam-cell-seg-0ae8c161` | OpenHands | false | 20 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-sanitize-git-repo-fa8206db` | OpenHands | true | 25 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-schedule-vacation-dc56b91c` | OpenHands | true | 20 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-schemelike-metacircular-eval-e9641b96` | OpenHands | false | 35 | excluded | openhands-agent-actions emitted 42 operations; public step_count is 35 |
| `openhands-OpenAI__GPT-5-scikit-learn__scikit-learn-11310-952013b4` | OpenHands | true | 46 | source-valid | openhands-maximal-visible-action-context; 46 operations |
| `openhands-OpenAI__GPT-5-scikit-learn__scikit-learn-12973-35ea9547` | OpenHands | true | 24 | source-valid | openhands-maximal-visible-action-context; 24 operations |
| `openhands-OpenAI__GPT-5-scikit-learn__scikit-learn-13142-ff36aa97` | OpenHands | true | 27 | source-valid | openhands-maximal-visible-action-context; 27 operations |
| `openhands-OpenAI__GPT-5-scikit-learn__scikit-learn-13439-b8455ed5` | OpenHands | true | 18 | source-valid | openhands-maximal-visible-action-context; 18 operations |
| `openhands-OpenAI__GPT-5-scikit-learn__scikit-learn-14141-261f75af` | OpenHands | true | 19 | source-valid | openhands-maximal-visible-action-context; 19 operations |
| `openhands-OpenAI__GPT-5-scikit-learn__scikit-learn-14894-70e56c10` | OpenHands | true | 22 | source-valid | openhands-maximal-visible-action-context; 22 operations |
| `openhands-OpenAI__GPT-5-scikit-learn__scikit-learn-14983-00a17867` | OpenHands | false | 35 | source-valid | openhands-maximal-visible-action-context; 35 operations |
| `openhands-OpenAI__GPT-5-scikit-learn__scikit-learn-15100-17d231ff` | OpenHands | true | 18 | source-valid | openhands-maximal-visible-action-context; 18 operations |
| `openhands-OpenAI__GPT-5-scikit-learn__scikit-learn-25232-3a0749ba` | OpenHands | true | 29 | source-valid | openhands-maximal-visible-action-context; 29 operations |
| `openhands-OpenAI__GPT-5-scikit-learn__scikit-learn-25747-66b09602` | OpenHands | false | 26 | source-valid | openhands-maximal-visible-action-context; 26 operations |
| `openhands-OpenAI__GPT-5-scikit-learn__scikit-learn-25931-cdaff695` | OpenHands | true | 25 | source-valid | openhands-maximal-visible-action-context; 25 operations |
| `openhands-OpenAI__GPT-5-scikit-learn__scikit-learn-25973-f3c53bd1` | OpenHands | true | 33 | source-valid | openhands-maximal-visible-action-context; 33 operations |
| `openhands-OpenAI__GPT-5-scikit-learn__scikit-learn-26323-2c2c571b` | OpenHands | true | 22 | source-valid | openhands-maximal-visible-action-context; 22 operations |
| `openhands-OpenAI__GPT-5-scikit-learn__scikit-learn-9288-933bb686` | OpenHands | true | 17 | source-valid | openhands-maximal-visible-action-context; 17 operations |
| `openhands-OpenAI__GPT-5-security-celery-redis-rce-999b4f07` | OpenHands | true | 25 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-security-vulhub-minio-33fe9f01` | OpenHands | false | 13 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-serverless__serverless-2576-370c7644` | OpenHands | true | 28 | source-valid | openhands-maximal-visible-action-context; 28 operations |
| `openhands-OpenAI__GPT-5-serverless__serverless-2945-1c469acc` | OpenHands | true | 34 | source-valid | openhands-maximal-visible-action-context; 34 operations |
| `openhands-OpenAI__GPT-5-serverless__serverless-3457-9fc6d45a` | OpenHands | true | 28 | source-valid | openhands-maximal-visible-action-context; 28 operations |
| `openhands-OpenAI__GPT-5-serverless__serverless-7374-19778028` | OpenHands | true | 45 | source-valid | openhands-maximal-visible-action-context; 45 operations |
| `openhands-OpenAI__GPT-5-setup-custom-dev-env-d6e32c59` | OpenHands | true | 24 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-simple-sheets-put-28d34f12` | OpenHands | true | 11 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-solana-data-6c481541` | OpenHands | true | 21 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-solve-sudoku-5ecea83b` | OpenHands | false | 21 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-speech-to-text-a2b56c6f` | OpenHands | true | 27 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-10449-05e1a89c` | OpenHands | false | 32 | source-valid | openhands-maximal-visible-action-context; 32 operations |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-10466-cc5abeef` | OpenHands | false | 22 | source-valid | openhands-maximal-visible-action-context; 22 operations |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-10614-34b85a5c` | OpenHands | false | 26 | source-valid | openhands-maximal-visible-action-context; 26 operations |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-11445-6f9d933b` | OpenHands | false | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-11510-a1d5f441` | OpenHands | false | 40 | source-valid | openhands-maximal-visible-action-context; 40 operations |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-7462-016dd538` | OpenHands | false | 23 | source-valid | openhands-maximal-visible-action-context; 23 operations |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-7757-7d0865d6` | OpenHands | false | 27 | source-valid | openhands-maximal-visible-action-context; 27 operations |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-7910-bd976fac` | OpenHands | false | 29 | source-valid | openhands-maximal-visible-action-context; 29 operations |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-8120-08ef8931` | OpenHands | false | 32 | source-valid | openhands-maximal-visible-action-context; 32 operations |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-8265-f92e7569` | OpenHands | false | 26 | source-valid | openhands-maximal-visible-action-context; 26 operations |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-8551-41e5e5f0` | OpenHands | false | 25 | source-valid | openhands-maximal-visible-action-context; 25 operations |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-8595-632717ba` | OpenHands | false | 35 | source-valid | openhands-maximal-visible-action-context; 35 operations |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-8621-b27cbcfa` | OpenHands | false | 26 | source-valid | openhands-maximal-visible-action-context; 26 operations |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-8638-a4ab3472` | OpenHands | false | 33 | source-valid | openhands-maximal-visible-action-context; 33 operations |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-9281-ed84e737` | OpenHands | false | 36 | source-valid | openhands-maximal-visible-action-context; 36 operations |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-9367-8dde1fee` | OpenHands | false | 28 | source-valid | openhands-maximal-visible-action-context; 28 operations |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-9461-6aa30bf2` | OpenHands | false | 37 | source-valid | openhands-maximal-visible-action-context; 37 operations |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-9602-8d033150` | OpenHands | false | 33 | source-valid | openhands-maximal-visible-action-context; 33 operations |
| `openhands-OpenAI__GPT-5-sphinx-doc__sphinx-9698-006ed41f` | OpenHands | false | 31 | source-valid | openhands-maximal-visible-action-context; 31 operations |
| `openhands-OpenAI__GPT-5-spinning-up-rl-8a313a1d` | OpenHands | true | 29 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-sqlite-db-truncate-28e7900e` | OpenHands | true | 17 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-stable-parallel-kmeans-ed192a60` | OpenHands | true | 12 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-sudo-llvm-ir-8bbb4e38` | OpenHands | true | 18 | source-valid | openhands-agent-actions; 18 operations |
| `openhands-OpenAI__GPT-5-swe-bench-fsspec-74ae74e1` | OpenHands | false | 49 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-swe-bench-langcodes-9dc7a598` | OpenHands | true | 36 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-sympy__sympy-12419-8dd07e79` | OpenHands | true | 32 | source-valid | openhands-maximal-visible-action-context; 32 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-12489-79c94620` | OpenHands | true | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-13372-ce1ad32b` | OpenHands | true | 28 | source-valid | openhands-maximal-visible-action-context; 28 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-13551-63e267c0` | OpenHands | true | 40 | source-valid | openhands-maximal-visible-action-context; 40 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-13615-ad7739f0` | OpenHands | true | 22 | source-valid | openhands-maximal-visible-action-context; 22 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-13647-61fd1639` | OpenHands | true | 28 | source-valid | openhands-maximal-visible-action-context; 28 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-13852-1ded1568` | OpenHands | false | 24 | source-valid | openhands-maximal-visible-action-context; 24 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-14976-a089d82e` | OpenHands | true | 21 | source-valid | openhands-maximal-visible-action-context; 21 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-15017-9641c826` | OpenHands | false | 32 | source-valid | openhands-maximal-visible-action-context; 32 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-15599-e177c7b0` | OpenHands | true | 23 | source-valid | openhands-maximal-visible-action-context; 23 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-15809-a80dd4e3` | OpenHands | true | 24 | source-valid | openhands-maximal-visible-action-context; 24 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-15976-9e6bc719` | OpenHands | false | 42 | source-valid | openhands-maximal-visible-action-context; 42 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-16597-fdf109a2` | OpenHands | false | 34 | source-valid | openhands-maximal-visible-action-context; 34 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-16886-e79072fe` | OpenHands | true | 21 | source-valid | openhands-maximal-visible-action-context; 21 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-17318-8d1c8af1` | OpenHands | false | 26 | source-valid | openhands-maximal-visible-action-context; 26 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-17630-fbbfeb9e` | OpenHands | false | 21 | source-valid | openhands-maximal-visible-action-context; 21 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-18211-ca7a3c16` | OpenHands | true | 33 | source-valid | openhands-maximal-visible-action-context; 33 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-19954-c947e93d` | OpenHands | true | 26 | source-valid | openhands-maximal-visible-action-context; 26 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-20428-37b735e3` | OpenHands | false | 45 | source-valid | openhands-maximal-visible-action-context; 45 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-20590-d2e851e8` | OpenHands | true | 30 | source-valid | openhands-maximal-visible-action-context; 30 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-20801-9aaa527b` | OpenHands | true | 36 | source-valid | openhands-maximal-visible-action-context; 36 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-21612-53350494` | OpenHands | true | 37 | source-valid | openhands-maximal-visible-action-context; 37 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-21847-ac120eb6` | OpenHands | true | 29 | source-valid | openhands-maximal-visible-action-context; 29 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-21930-9cf36182` | OpenHands | false | 39 | source-valid | openhands-maximal-visible-action-context; 39 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-22080-28be9927` | OpenHands | false | 32 | source-valid | openhands-maximal-visible-action-context; 32 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-22456-5de916b9` | OpenHands | true | 24 | source-valid | openhands-maximal-visible-action-context; 24 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-22714-c0148acc` | OpenHands | true | 32 | source-valid | openhands-maximal-visible-action-context; 32 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-22914-bfa0d42d` | OpenHands | true | 23 | source-valid | openhands-maximal-visible-action-context; 23 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-23262-ed66febb` | OpenHands | true | 41 | source-valid | openhands-maximal-visible-action-context; 41 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-23413-767fb95b` | OpenHands | true | 48 | source-valid | openhands-maximal-visible-action-context; 48 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-23534-93d4ba22` | OpenHands | true | 22 | source-valid | openhands-maximal-visible-action-context; 22 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-23824-509bb914` | OpenHands | true | 17 | source-valid | openhands-maximal-visible-action-context; 17 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-24066-4e6e5ad3` | OpenHands | true | 29 | source-valid | openhands-maximal-visible-action-context; 29 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-24213-9b588ba7` | OpenHands | true | 19 | source-valid | openhands-maximal-visible-action-context; 19 operations |
| `openhands-OpenAI__GPT-5-sympy__sympy-24539-ff71090d` | OpenHands | true | 22 | source-valid | openhands-maximal-visible-action-context; 22 operations |
| `openhands-OpenAI__GPT-5-tmux-advanced-workflow-4c53ca67` | OpenHands | true | 15 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-tree-directory-parser-738da939` | OpenHands | true | 18 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-triton-interpret-4ac0c33a` | OpenHands | true | 24 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-vertex-solver-7e1773f4` | OpenHands | true | 11 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-video-processing-d61fabc4` | OpenHands | false | 13 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-vul-flask-21e213ae` | OpenHands | true | 29 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-vulnerable-secret-e1393875` | OpenHands | true | 22 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-weighted-max-sat-solver-95ebb626` | OpenHands | true | 18 | source-valid | openhands-agent-actions; 18 operations |
| `openhands-OpenAI__GPT-5-winning-avg-corewars-61f3a2b9` | OpenHands | false | 77 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-word2vec-from-scratch-998fdd92` | OpenHands | true | 20 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-OpenAI__GPT-5-yt-dlp__yt-dlp-5933-e15ee7cf` | OpenHands | true | 34 | source-valid | openhands-maximal-visible-action-context; 34 operations |
| `openhands-OpenAI__GPT-5-yt-dlp__yt-dlp-9862-378895f4` | OpenHands | true | 36 | source-valid | openhands-maximal-visible-action-context; 36 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-3d-model-format-legacy-42539d71` | OpenHands | false | 262 | source-valid | openhands-agent-actions; 262 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-acl-permissions-inheritance-f2169177` | OpenHands | false | 21 | source-valid | openhands-agent-actions; 21 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-adaptive-rejection-sampler-6f7061bd` | OpenHands | true | 28 | source-valid | openhands-agent-actions; 28 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-add-benchmark-lm-eval-harness-662e157c` | OpenHands | false | 156 | source-valid | openhands-agent-actions; 156 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-aimo-airline-departures-39d66bf8` | OpenHands | false | 11 | source-valid | openhands-agent-actions; 11 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-analyze-access-logs-c85e4ea2` | OpenHands | true | 23 | source-valid | openhands-agent-actions; 23 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-assign-seats-1bf0cd69` | OpenHands | true | 16 | source-valid | openhands-agent-actions; 16 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-attention-mil-bc067b27` | OpenHands | false | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-audio-synth-stft-peaks-a10362c1` | OpenHands | false | 41 | source-valid | openhands-agent-actions; 41 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-blind-maze-explorer-5x5-824eeb44` | OpenHands | false | 67 | source-valid | openhands-agent-actions; 67 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-blind-maze-explorer-algorithm-dc43dff2` | OpenHands | false | 170 | source-valid | openhands-agent-actions; 170 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-break-filter-js-from-html-f7463fc2` | OpenHands | false | 64 | source-valid | openhands-agent-actions; 64 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-broken-python-29415d0a` | OpenHands | false | 11 | source-valid | openhands-agent-actions; 11 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-cython-ext-0d2909ac` | OpenHands | false | 68 | source-valid | openhands-agent-actions; 68 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-initramfs-qemu-b5e3fbb2` | OpenHands | false | 15 | source-valid | openhands-agent-actions; 15 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-linux-kernel-qemu-ac78e1d7` | OpenHands | false | 135 | excluded | openhands-agent-actions emitted 145 operations; public step_count is 135 |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-pmars-96107e4e` | OpenHands | false | 27 | source-valid | openhands-agent-actions; 27 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-pov-ray-58213dd5` | OpenHands | false | 34 | source-valid | openhands-agent-actions; 34 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-stp-faad538e` | OpenHands | false | 33 | source-valid | openhands-agent-actions; 33 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-tcc-qemu-493c2900` | OpenHands | false | 32 | source-valid | openhands-agent-actions; 32 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-caffe-cifar-10-8ed6ed1c` | OpenHands | false | 83 | source-valid | openhands-agent-actions; 83 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-cartpole-rl-training-392a50ec` | OpenHands | true | 30 | source-valid | openhands-agent-actions; 30 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-catch-me-if-you-can-9f481165` | OpenHands | true | 20 | excluded | openhands-agent-actions emitted 373 operations; public step_count is 20 |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-causal-inference-r-261beedb` | OpenHands | true | 40 | source-valid | openhands-agent-actions; 40 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-chem-property-targeting-9825872f` | OpenHands | false | 44 | source-valid | openhands-agent-actions; 44 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-chem-rf-119058e3` | OpenHands | false | 48 | source-valid | openhands-agent-actions; 48 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-chess-best-move-40384bcb` | OpenHands | false | 21 | source-valid | openhands-agent-actions; 21 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-circuit-fibsqrt-dae78473` | OpenHands | false | 79 | source-valid | openhands-agent-actions; 79 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-cobol-modernization-440c9689` | OpenHands | true | 54 | source-valid | openhands-agent-actions; 54 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-code-from-image-a422d67d` | OpenHands | false | 49 | source-valid | openhands-agent-actions; 49 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-compile-compcert-fc762a12` | OpenHands | false | 297 | excluded | openhands-agent-actions emitted 300 operations; public step_count is 297 |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-conda-env-conflict-resolution-e623c38a` | OpenHands | false | 29 | source-valid | openhands-agent-actions; 29 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-configure-git-webserver-d6b1afb1` | OpenHands | true | 39 | source-valid | openhands-agent-actions; 39 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-constraints-scheduling-12f4e16a` | OpenHands | true | 17 | excluded | OpenHands archive has neither call records nor session events |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-count-call-stack-4681a8d0` | OpenHands | false | 15 | source-valid | openhands-agent-actions; 15 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-count-dataset-tokens-3b4100df` | OpenHands | false | 74 | source-valid | openhands-agent-actions; 74 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-cprofiling-python-d7211fdb` | OpenHands | false | 133 | source-valid | openhands-agent-actions; 133 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-cron-broken-network-e46a0d83` | OpenHands | false | 95 | source-valid | openhands-agent-actions; 95 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-cross-entropy-method-b6c84f15` | OpenHands | true | 48 | source-valid | openhands-agent-actions; 48 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-csv-to-parquet-2e8dd825` | OpenHands | true | 15 | source-valid | openhands-agent-actions; 15 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-db-wal-recovery-f0e919d9` | OpenHands | false | 52 | source-valid | openhands-agent-actions; 52 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-decommissioning-service-with-sensitive-data-b374b8e3` | OpenHands | true | 13 | source-valid | openhands-agent-actions; 13 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-deterministic-tarball-44b6efbf` | OpenHands | false | 96 | source-valid | openhands-agent-actions; 96 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-distribution-search-8ce260e5` | OpenHands | false | 48 | source-valid | openhands-agent-actions; 48 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-dna-assembly-11538a9b` | OpenHands | false | 50 | source-valid | openhands-agent-actions; 50 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-dna-insert-d9e1d393` | OpenHands | false | 21 | source-valid | openhands-agent-actions; 21 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-download-youtube-9c7a4aca` | OpenHands | false | 50 | source-valid | openhands-agent-actions; 50 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-enemy-grid-escape-e1b16479` | OpenHands | false | 62 | source-valid | openhands-agent-actions; 62 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-extract-elf-e929e4f9` | OpenHands | false | 33 | source-valid | openhands-agent-actions; 33 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-extract-moves-from-video-da64aed0` | OpenHands | false | 146 | source-valid | openhands-agent-actions; 146 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-feal-differential-cryptanalysis-9e94bcab` | OpenHands | false | 117 | source-valid | openhands-agent-actions; 117 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-feal-linear-cryptanalysis-a0347850` | OpenHands | false | 62 | source-valid | openhands-agent-actions; 62 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-fibonacci-server-ee141a1e` | OpenHands | false | 13 | source-valid | openhands-agent-actions; 13 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-financial-document-processor-85861c3c` | OpenHands | false | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-find-official-code-1ed2b3ac` | OpenHands | false | 36 | source-valid | openhands-agent-actions; 36 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-fix-code-vulnerability-a03edef9` | OpenHands | true | 68 | source-valid | openhands-agent-actions; 68 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-fix-git-b6aab0d4` | OpenHands | true | 27 | source-valid | openhands-agent-actions; 27 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-fix-ocaml-gc-96d6a796` | OpenHands | false | 335 | excluded | openhands-agent-actions emitted 343 operations; public step_count is 335 |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-fix-pandas-version-bcd10c56` | OpenHands | true | 28 | source-valid | openhands-agent-actions; 28 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-flood-monitoring-basic-944f9afb` | OpenHands | true | 11 | source-valid | openhands-agent-actions; 11 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-fmri-encoding-r-c991109b` | OpenHands | false | 42 | source-valid | openhands-agent-actions; 42 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-form-filling-5dd94316` | OpenHands | true | 78 | source-valid | openhands-agent-actions; 78 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-gcc-compiler-optimization-aacc0fdd` | OpenHands | true | 21 | source-valid | openhands-agent-actions; 21 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-get-bitcoin-nodes-e9f4bafc` | OpenHands | false | 88 | source-valid | openhands-agent-actions; 88 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-git-leak-recovery-40c54ddb` | OpenHands | true | 17 | source-valid | openhands-agent-actions; 17 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-git-multibranch-e3f8ba1c` | OpenHands | true | 64 | excluded | openhands-agent-actions emitted 28 operations; public step_count is 64 |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-git-workflow-hack-9329fc79` | OpenHands | true | 29 | source-valid | openhands-agent-actions; 29 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-gomoku-planner-ce862f51` | OpenHands | true | 27 | source-valid | openhands-agent-actions; 27 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-gpt2-codegolf-d2336e2f` | OpenHands | false | 42 | source-valid | openhands-agent-actions; 42 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-hdfs-deployment-173ed2ca` | OpenHands | false | 173 | excluded | openhands-agent-actions emitted 176 operations; public step_count is 173 |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-heterogeneous-dates-7ae7a86e` | OpenHands | true | 13 | source-valid | openhands-agent-actions; 13 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-hf-lora-adapter-139f6d8e` | OpenHands | false | 28 | excluded | openhands-agent-actions emitted 102 operations; public step_count is 28 |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-hf-model-inference-702e3933` | OpenHands | true | 81 | source-valid | openhands-agent-actions; 81 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-hf-train-lora-adapter-ca95404f` | OpenHands | false | 64 | source-valid | openhands-agent-actions; 64 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-html-finance-verify-7b90f5fa` | OpenHands | false | 25 | source-valid | openhands-agent-actions; 25 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-huarong-dao-solver-0535a1eb` | OpenHands | false | 42 | source-valid | openhands-agent-actions; 42 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-hydra-debug-slurm-mode-f66720a5` | OpenHands | true | 21 | source-valid | openhands-agent-actions; 21 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-ilp-solver-23cbc01a` | OpenHands | true | 16 | source-valid | openhands-agent-actions; 16 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-implement-eigenvectors-from-eigenvalues-research-paper-1d26bf96` | OpenHands | true | 43 | source-valid | openhands-agent-actions; 43 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-incompatible-python-fasttext-6be59cbf` | OpenHands | false | 30 | source-valid | openhands-agent-actions; 30 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-install-klee-minimal-76b6be68` | OpenHands | false | 60 | source-valid | openhands-agent-actions; 60 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-install-windows-3.11-06a0aa1b` | OpenHands | false | 146 | source-valid | openhands-agent-actions; 146 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-install-windows-xp-59eebb7a` | OpenHands | false | 30 | source-valid | openhands-agent-actions; 30 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-intrusion-detection-e9bc92b9` | OpenHands | false | 186 | source-valid | openhands-agent-actions; 186 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-jq-data-processing-f36babea` | OpenHands | true | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-jsonl-aggregator-bfcc85e0` | OpenHands | true | 12 | source-valid | openhands-agent-actions; 12 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-jupyter-notebook-server-b3011bbf` | OpenHands | true | 18 | source-valid | openhands-agent-actions; 18 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-kv-store-grpc-1375e147` | OpenHands | false | 56 | source-valid | openhands-agent-actions; 56 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-large-scale-text-editing-0585ebd0` | OpenHands | false | 241 | source-valid | openhands-agent-actions; 241 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-largest-eigenval-50b07645` | OpenHands | false | 57 | source-valid | openhands-agent-actions; 57 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-lean4-proof-413fb307` | OpenHands | false | 298 | excluded | openhands-agent-actions emitted 310 operations; public step_count is 298 |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-leelachess0-pytorch-conversion-d4e85a4c` | OpenHands | false | 145 | source-valid | openhands-agent-actions; 145 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-llm-inference-batching-scheduler-c7a02fa2` | OpenHands | false | 90 | source-valid | openhands-agent-actions; 90 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-llm-spec-decoding-d778b3b3` | OpenHands | false | 28 | source-valid | openhands-agent-actions; 28 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-logistic-regression-divergence-43ed1121` | OpenHands | false | 77 | source-valid | openhands-agent-actions; 77 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-magsac-install-f292ed52` | OpenHands | false | 185 | excluded | openhands-agent-actions emitted 193 operations; public step_count is 185 |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-mahjong-winninghand-9239c03c` | OpenHands | true | 23 | source-valid | openhands-agent-actions; 23 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-mailman-bc053ee4` | OpenHands | false | 425 | source-valid | openhands-agent-actions; 425 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-make-doom-for-mips-1944840c` | OpenHands | false | 209 | source-valid | openhands-agent-actions; 209 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-make-mips-interpreter-3ff6d5bb` | OpenHands | false | 54 | source-valid | openhands-agent-actions; 54 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-mcmc-sampling-stan-3f082b25` | OpenHands | false | 43 | source-valid | openhands-agent-actions; 43 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-merge-diff-arc-agi-task-40f29e74` | OpenHands | true | 44 | source-valid | openhands-agent-actions; 44 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-mixed-integer-programming-cc18f0ca` | OpenHands | true | 11 | source-valid | openhands-agent-actions; 11 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-mlflow-register-ce48a6a0` | OpenHands | false | 14 | source-valid | openhands-agent-actions; 14 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-model-extraction-relu-logits-64642e0e` | OpenHands | false | 58 | source-valid | openhands-agent-actions; 58 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-modernize-fortran-build-344aa980` | OpenHands | true | 19 | source-valid | openhands-agent-actions; 19 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-modernize-scientific-stack-7247d333` | OpenHands | true | 11 | source-valid | openhands-agent-actions; 11 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-movie-helper-607aafdc` | OpenHands | false | 27 | source-valid | openhands-agent-actions; 27 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-mteb-eval-bc4307ef` | OpenHands | true | 35 | source-valid | openhands-agent-actions; 35 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-mteb-retrieve-492fbecc` | OpenHands | false | 85 | source-valid | openhands-agent-actions; 85 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-multi-source-data-merger-4fb50e65` | OpenHands | true | 30 | source-valid | openhands-agent-actions; 30 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-multistep-definite-integral-ad402068` | OpenHands | true | 14 | source-valid | openhands-agent-actions; 14 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-neuron-to-jaxley-conversion-2c0b1f9c` | OpenHands | false | 120 | source-valid | openhands-agent-actions; 120 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-new-encrypt-command-b43af6ee` | OpenHands | true | 22 | source-valid | openhands-agent-actions; 22 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-nginx-request-logging-5a25d0f7` | OpenHands | true | 18 | source-valid | openhands-agent-actions; 18 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-npm-conflict-resolution-b6d04718` | OpenHands | false | 37 | source-valid | openhands-agent-actions; 37 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-oom-1309e395` | OpenHands | false | 32 | source-valid | openhands-agent-actions; 32 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-optimal-transport-ad4b5ea6` | OpenHands | false | 43 | source-valid | openhands-agent-actions; 43 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-organization-json-generator-8718641f` | OpenHands | true | 15 | source-valid | openhands-agent-actions; 15 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-overfull-hbox-ea068f9e` | OpenHands | false | 27 | source-valid | openhands-agent-actions; 27 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-pandas-etl-3318de4e` | OpenHands | false | 22 | source-valid | openhands-agent-actions; 22 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-pandas-sql-query-2d42d24c` | OpenHands | true | 31 | source-valid | openhands-agent-actions; 31 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-parallel-particle-simulator-c3d7fc01` | OpenHands | false | 67 | source-valid | openhands-agent-actions; 67 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-parallelize-compute-squares-46f77480` | OpenHands | true | 37 | source-valid | openhands-agent-actions; 37 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-parallelize-graph-63e4e1ad` | OpenHands | false | 50 | source-valid | openhands-agent-actions; 50 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-password-recovery-737c6dfd` | OpenHands | false | 13 | source-valid | openhands-agent-actions; 13 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-path-tracing-d2d8e4e4` | OpenHands | false | 161 | source-valid | openhands-agent-actions; 161 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-path-tracing-reverse-d141c9d1` | OpenHands | false | 80 | source-valid | openhands-agent-actions; 80 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-pcap-to-netflow-7f02ce63` | OpenHands | false | 34 | source-valid | openhands-agent-actions; 34 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-play-zork-998f6266` | OpenHands | false | 43 | excluded | openhands-agent-actions emitted 104 operations; public step_count is 43 |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-play-zork-easy-c5543c01` | OpenHands | false | 45 | excluded | openhands-agent-actions emitted 100 operations; public step_count is 45 |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-polyglot-c-py-88cfc4c5` | OpenHands | false | 92 | source-valid | openhands-agent-actions; 92 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-polyglot-rust-c-423ddc67` | OpenHands | false | 31 | excluded | openhands-agent-actions emitted 33 operations; public step_count is 31 |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-port-compressor-109ac245` | OpenHands | false | 75 | source-valid | openhands-agent-actions; 75 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-portfolio-optimization-5c78c878` | OpenHands | false | 123 | source-valid | openhands-agent-actions; 123 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-predicate-pushdown-bench-70fc709b` | OpenHands | true | 138 | source-valid | openhands-agent-actions; 138 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-predict-customer-churn-034a5e7e` | OpenHands | false | 25 | source-valid | openhands-agent-actions; 25 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-processing-pipeline-54e02dea` | OpenHands | false | 27 | source-valid | openhands-agent-actions; 27 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-protein-assembly-7e18a0b7` | OpenHands | false | 28 | source-valid | openhands-agent-actions; 28 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-protocol-analysis-rs-0160e7da` | OpenHands | false | 500 | source-valid | openhands-agent-actions; 500 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-prove-plus-comm-da989e5a` | OpenHands | true | 15 | source-valid | openhands-agent-actions; 15 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-puzzle-solver-a6d4cde8` | OpenHands | false | 22 | source-valid | openhands-agent-actions; 22 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-pypi-server-770bfe1d` | OpenHands | true | 22 | source-valid | openhands-agent-actions; 22 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-pytorch-model-cli-eff3bdee` | OpenHands | false | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-pytorch-model-recovery-829de3e5` | OpenHands | true | 19 | source-valid | openhands-agent-actions; 19 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-query-optimize-7642c4fa` | OpenHands | false | 51 | source-valid | openhands-agent-actions; 51 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-raman-fitting-82d8e72c` | OpenHands | false | 41 | source-valid | openhands-agent-actions; 41 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-rare-mineral-allocation-9daf6126` | OpenHands | false | 30 | source-valid | openhands-agent-actions; 30 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-recover-obfuscated-files-d275a9a1` | OpenHands | true | 17 | source-valid | openhands-agent-actions; 17 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-regex-chess-92e3c2d2` | OpenHands | false | 67 | source-valid | openhands-agent-actions; 67 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-regex-log-974164b9` | OpenHands | true | 16 | source-valid | openhands-agent-actions; 16 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-reshard-c4-data-eb40ee00` | OpenHands | false | 135 | source-valid | openhands-agent-actions; 135 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-reverse-engineering-885a06d5` | OpenHands | false | 333 | source-valid | openhands-agent-actions; 333 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-rstan-to-pystan-da6bf25b` | OpenHands | true | 120 | source-valid | openhands-agent-actions; 120 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-run-pdp11-code-6ea859af` | OpenHands | false | 80 | source-valid | openhands-agent-actions; 80 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-sam-cell-seg-a36ffcc5` | OpenHands | false | 52 | excluded | openhands-agent-actions emitted 202 operations; public step_count is 52 |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-schedule-vacation-83baceb3` | OpenHands | true | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-schemelike-metacircular-eval-6b87c8fa` | OpenHands | false | 426 | source-valid | openhands-agent-actions; 426 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-setup-custom-dev-env-5f709086` | OpenHands | true | 49 | source-valid | openhands-agent-actions; 49 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-sha-puzzle-1452a6f6` | OpenHands | false | 20 | source-valid | openhands-agent-actions; 20 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-solana-data-d00f264d` | OpenHands | false | 35 | excluded | openhands-agent-actions emitted 42 operations; public step_count is 35 |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-solve-maze-challenge-357fdd84` | OpenHands | false | 66 | source-valid | openhands-agent-actions; 66 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-solve-sudoku-b2af6f2f` | OpenHands | false | 24 | source-valid | openhands-agent-actions; 24 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-sparql-university-6927d1eb` | OpenHands | false | 16 | source-valid | openhands-agent-actions; 16 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-speech-to-text-7f4442d3` | OpenHands | true | 67 | source-valid | openhands-agent-actions; 67 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-spinning-up-rl-820a5300` | OpenHands | false | 110 | excluded | openhands-agent-actions emitted 112 operations; public step_count is 110 |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-sqlite-db-truncate-69eb0769` | OpenHands | false | 94 | source-valid | openhands-agent-actions; 94 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-sqlite-with-gcov-97f543c5` | OpenHands | true | 22 | source-valid | openhands-agent-actions; 22 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-stable-parallel-kmeans-4fd9c36d` | OpenHands | false | 42 | source-valid | openhands-agent-actions; 42 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-sudo-llvm-ir-c429fecd` | OpenHands | false | 500 | source-valid | openhands-agent-actions; 500 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-swe-bench-astropy-1-b8c5d66d` | OpenHands | true | 335 | excluded | openhands-agent-actions emitted 336 operations; public step_count is 335 |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-swe-bench-astropy-2-42006b98` | OpenHands | false | 150 | source-valid | openhands-agent-actions; 150 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-swe-bench-fsspec-7470aab4` | OpenHands | false | 92 | source-valid | openhands-agent-actions; 92 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-swe-bench-langcodes-ed59da58` | OpenHands | true | 40 | source-valid | openhands-agent-actions; 40 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-tmux-advanced-workflow-b89f0c8a` | OpenHands | true | 49 | source-valid | openhands-agent-actions; 49 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-torch-pipeline-parallelism-96476ab0` | OpenHands | false | 43 | source-valid | openhands-agent-actions; 43 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-torch-tensor-parallelism-253f4b40` | OpenHands | false | 56 | source-valid | openhands-agent-actions; 56 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-train-fasttext-613e5fb8` | OpenHands | false | 148 | source-valid | openhands-agent-actions; 148 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-tree-directory-parser-3ab73e47` | OpenHands | false | 125 | source-valid | openhands-agent-actions; 125 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-triton-interpret-81f40917` | OpenHands | false | 86 | source-valid | openhands-agent-actions; 86 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-tune-mjcf-595d12d4` | OpenHands | true | 79 | source-valid | openhands-agent-actions; 79 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-vertex-solver-e0ce0dc4` | OpenHands | true | 19 | source-valid | openhands-agent-actions; 19 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-video-processing-c392adff` | OpenHands | false | 38 | source-valid | openhands-agent-actions; 38 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-vimscript-vim-quine-b2b4d301` | OpenHands | false | 109 | source-valid | openhands-agent-actions; 109 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-vul-flask-53577c6e` | OpenHands | false | 70 | source-valid | openhands-agent-actions; 70 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-vul-flink-87560dcf` | OpenHands | false | 38 | source-valid | openhands-agent-actions; 38 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-vulnerable-secret-473b1d94` | OpenHands | true | 33 | source-valid | openhands-agent-actions; 33 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-wasm-pipeline-f95fc2fb` | OpenHands | false | 36 | source-valid | openhands-agent-actions; 36 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-weighted-max-sat-solver-50633d4c` | OpenHands | true | 39 | source-valid | openhands-agent-actions; 39 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-winning-avg-corewars-6b7e7e77` | OpenHands | false | 48 | source-valid | openhands-agent-actions; 48 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-word2vec-from-scratch-059125e9` | OpenHands | false | 95 | source-valid | openhands-agent-actions; 95 operations |
| `openhands-Qwen__Qwen3-Coder-480B-A35B-Instruct-write-compressor-c01be630` | OpenHands | false | 192 | source-valid | openhands-agent-actions; 192 operations |
| `sweagent-OpenAI__GPT-5-Significant-Gravitas__AutoGPT-4652-b968024b` | SWE-agent | false | 32 | source-valid | sweagent-trajectory-elements; 32 operations |
| `sweagent-OpenAI__GPT-5-clap-rs__clap-2534-8e1e1407` | SWE-agent | true | 14 | source-valid | sweagent-trajectory-elements; 14 operations |
| `sweagent-OpenAI__GPT-5-clap-rs__clap-2758-594e09d1` | SWE-agent | true | 30 | source-valid | sweagent-trajectory-elements; 30 operations |
| `sweagent-OpenAI__GPT-5-clap-rs__clap-3179-c9a2bc9d` | SWE-agent | true | 18 | source-valid | sweagent-trajectory-elements; 18 operations |
| `sweagent-OpenAI__GPT-5-cli__cli-5019-51dee7c3` | SWE-agent | true | 54 | source-valid | sweagent-trajectory-elements; 54 operations |
| `sweagent-OpenAI__GPT-5-cli__cli-6706-b74f46a9` | SWE-agent | true | 59 | source-valid | sweagent-trajectory-elements; 59 operations |
| `sweagent-OpenAI__GPT-5-expressjs__express-3870-7594bfc0` | SWE-agent | true | 27 | source-valid | sweagent-trajectory-elements; 27 operations |
| `sweagent-OpenAI__GPT-5-facebook__zstd-1243-1c933b6d` | SWE-agent | true | 46 | source-valid | sweagent-trajectory-elements; 46 operations |
| `sweagent-OpenAI__GPT-5-facebook__zstd-1390-2ca70e40` | SWE-agent | true | 20 | source-valid | sweagent-trajectory-elements; 20 operations |
| `sweagent-OpenAI__GPT-5-facebook__zstd-1532-6f816f49` | SWE-agent | true | 33 | source-valid | sweagent-trajectory-elements; 33 operations |
| `sweagent-OpenAI__GPT-5-facebook__zstd-1733-0515ef9c` | SWE-agent | true | 18 | source-valid | sweagent-trajectory-elements; 18 operations |
| `sweagent-OpenAI__GPT-5-facebook__zstd-637-94afe4df` | SWE-agent | true | 47 | source-valid | sweagent-trajectory-elements; 47 operations |
| `sweagent-OpenAI__GPT-5-fasterxml__jackson-core-964-ab40902f` | SWE-agent | true | 38 | source-valid | sweagent-trajectory-elements; 38 operations |
| `sweagent-OpenAI__GPT-5-fasterxml__jackson-databind-3701-a6428790` | SWE-agent | true | 12 | source-valid | sweagent-trajectory-elements; 12 operations |
| `sweagent-OpenAI__GPT-5-fasterxml__jackson-databind-4050-31d6dd30` | SWE-agent | true | 19 | source-valid | sweagent-trajectory-elements; 19 operations |
| `sweagent-OpenAI__GPT-5-fmtlib__fmt-2394-5f39d316` | SWE-agent | true | 20 | source-valid | sweagent-trajectory-elements; 20 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-12981-3eb4db52` | SWE-agent | true | 17 | source-valid | sweagent-trajectory-elements; 17 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-13693-ee32c741` | SWE-agent | true | 34 | source-valid | sweagent-trajectory-elements; 34 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-13865-44d517cd` | SWE-agent | false | 48 | source-valid | sweagent-trajectory-elements; 48 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-13989-f41dae7b` | SWE-agent | false | 123 | source-valid | sweagent-trajectory-elements; 123 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-15158-25e0c0d7` | SWE-agent | true | 35 | source-valid | sweagent-trajectory-elements; 35 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-15795-03c8539f` | SWE-agent | true | 16 | source-valid | sweagent-trajectory-elements; 16 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-16198-1bb854f7` | SWE-agent | true | 43 | source-valid | sweagent-trajectory-elements; 43 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-19590-6ee9899a` | SWE-agent | false | 39 | source-valid | sweagent-trajectory-elements; 39 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-20136-2b7c0524` | SWE-agent | false | 93 | source-valid | sweagent-trajectory-elements; 93 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-21768-91cf46b0` | SWE-agent | true | 30 | source-valid | sweagent-trajectory-elements; 30 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-22458-ce29b23d` | SWE-agent | false | 24 | source-valid | sweagent-trajectory-elements; 24 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-22920-27c55020` | SWE-agent | false | 21 | source-valid | sweagent-trajectory-elements; 21 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-23126-684431b2` | SWE-agent | true | 25 | source-valid | sweagent-trajectory-elements; 25 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-23223-ba60b3d2` | SWE-agent | false | 41 | source-valid | sweagent-trajectory-elements; 41 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-24238-963711c1` | SWE-agent | true | 24 | source-valid | sweagent-trajectory-elements; 24 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-27463-1b3f334c` | SWE-agent | true | 53 | source-valid | sweagent-trajectory-elements; 53 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-28517-9f0c9e72` | SWE-agent | true | 41 | source-valid | sweagent-trajectory-elements; 41 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-28535-e28436fb` | SWE-agent | true | 26 | source-valid | sweagent-trajectory-elements; 26 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-29311-5bbe74e8` | SWE-agent | true | 34 | source-valid | sweagent-trajectory-elements; 34 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-29449-deaa19e6` | SWE-agent | true | 27 | source-valid | sweagent-trajectory-elements; 27 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-30556-071b39f7` | SWE-agent | true | 15 | source-valid | sweagent-trajectory-elements; 15 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-3716-5872d333` | SWE-agent | false | 41 | source-valid | sweagent-trajectory-elements; 41 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-5122-72b5eb40` | SWE-agent | true | 15 | source-valid | sweagent-trajectory-elements; 15 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-6098-aea35e9a` | SWE-agent | true | 37 | source-valid | sweagent-trajectory-elements; 37 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-7078-090b230e` | SWE-agent | true | 33 | source-valid | sweagent-trajectory-elements; 33 operations |
| `sweagent-OpenAI__GPT-5-huggingface__transformers-8624-b9dc0bc1` | SWE-agent | true | 36 | source-valid | sweagent-trajectory-elements; 36 operations |
| `sweagent-OpenAI__GPT-5-iamkun__dayjs-1319-1ad50ca6` | SWE-agent | true | 45 | source-valid | sweagent-trajectory-elements; 45 operations |
| `sweagent-OpenAI__GPT-5-iamkun__dayjs-1414-7722295d` | SWE-agent | true | 68 | source-valid | sweagent-trajectory-elements; 68 operations |
| `sweagent-OpenAI__GPT-5-iamkun__dayjs-1725-4fa6a2e1` | SWE-agent | true | 35 | source-valid | sweagent-trajectory-elements; 35 operations |
| `sweagent-OpenAI__GPT-5-instance_NodeBB__NodeBB-767973717be700f46f06f3e7f4fc550c63509046-vnan-556a7837` | SWE-agent | true | 33 | source-valid | sweagent-trajectory-elements; 33 operations |
| `sweagent-OpenAI__GPT-5-instance_ansible__ansible-1a4644ff15355fd696ac5b9d074a566a80fe7ca3-v30a923fb5c164d6cd18280c02422f75e611e8fb2-3f41fa59` | SWE-agent | true | 26 | source-valid | sweagent-trajectory-elements; 26 operations |
| `sweagent-OpenAI__GPT-5-instance_ansible__ansible-622a493ae03bd5e5cf517d336fc426e9d12208c7-v906c969b551b346ef54a2c0b41e04f632b7b73c2-3e1660fe` | SWE-agent | true | 23 | source-valid | sweagent-trajectory-elements; 23 operations |
| `sweagent-OpenAI__GPT-5-instance_ansible__ansible-6cc97447aac5816745278f3735af128afb255c81-v0f01c69f1e2528b935359cfe578530722bca2c59-1c989b98` | SWE-agent | false | 89 | source-valid | sweagent-trajectory-elements; 89 operations |
| `sweagent-OpenAI__GPT-5-instance_ansible__ansible-77658704217d5f166404fc67997203c25381cb6e-v390e508d27db7a51eece36bb6d9698b63a5b638a-3b3b7d5d` | SWE-agent | true | 20 | source-valid | sweagent-trajectory-elements; 20 operations |
| `sweagent-OpenAI__GPT-5-instance_ansible__ansible-7e1a347695c7987ae56ef1b6919156d9254010ad-v390e508d27db7a51eece36bb6d9698b63a5b638a-853de2e9` | SWE-agent | false | 31 | source-valid | sweagent-trajectory-elements; 31 operations |
| `sweagent-OpenAI__GPT-5-instance_ansible__ansible-8127abbc298cabf04aaa89a478fc5e5e3432a6fc-v30a923fb5c164d6cd18280c02422f75e611e8fb2-79f7945f` | SWE-agent | false | 90 | source-valid | sweagent-trajectory-elements; 90 operations |
| `sweagent-OpenAI__GPT-5-instance_ansible__ansible-9142be2f6cabbe6597c9254c5bb9186d17036d55-v0f01c69f1e2528b935359cfe578530722bca2c59-9bfb3524` | SWE-agent | true | 34 | source-valid | sweagent-trajectory-elements; 34 operations |
| `sweagent-OpenAI__GPT-5-instance_ansible__ansible-942424e10b2095a173dbd78e7128f52f7995849b-v30a923fb5c164d6cd18280c02422f75e611e8fb2-0761ffc8` | SWE-agent | true | 50 | source-valid | sweagent-trajectory-elements; 50 operations |
| `sweagent-OpenAI__GPT-5-instance_ansible__ansible-949c503f2ef4b2c5d668af0492a5c0db1ab86140-v0f01c69f1e2528b935359cfe578530722bca2c59-16808561` | SWE-agent | false | 80 | source-valid | sweagent-trajectory-elements; 80 operations |
| `sweagent-OpenAI__GPT-5-instance_ansible__ansible-a7d2a4e03209cff1e97e59fd54bb2b05fdbdbec6-v0f01c69f1e2528b935359cfe578530722bca2c59-6b53fdb8` | SWE-agent | true | 37 | source-valid | sweagent-trajectory-elements; 37 operations |
| `sweagent-OpenAI__GPT-5-instance_ansible__ansible-b2a289dcbb702003377221e25f62c8a3608f0e89-v173091e2e36d38c978002990795f66cfc0af30ad-7e516d53` | SWE-agent | false | 63 | source-valid | sweagent-trajectory-elements; 63 operations |
| `sweagent-OpenAI__GPT-5-instance_ansible__ansible-b5e0293645570f3f404ad1dbbe5f006956ada0df-v0f01c69f1e2528b935359cfe578530722bca2c59-8f74ece3` | SWE-agent | false | 22 | source-valid | sweagent-trajectory-elements; 22 operations |
| `sweagent-OpenAI__GPT-5-instance_ansible__ansible-bec27fb4c0a40c5f8bbcf26a475704227d65ee73-v30a923fb5c164d6cd18280c02422f75e611e8fb2-ab0b8f1f` | SWE-agent | false | 53 | source-valid | sweagent-trajectory-elements; 53 operations |
| `sweagent-OpenAI__GPT-5-instance_ansible__ansible-d58e69c82d7edd0583dd8e78d76b075c33c3151e-v173091e2e36d38c978002990795f66cfc0af30ad-32930979` | SWE-agent | false | 75 | source-valid | sweagent-trajectory-elements; 75 operations |
| `sweagent-OpenAI__GPT-5-instance_ansible__ansible-e9e6001263f51103e96e58ad382660df0f3d0e39-v30a923fb5c164d6cd18280c02422f75e611e8fb2-44b42789` | SWE-agent | true | 22 | source-valid | sweagent-trajectory-elements; 22 operations |
| `sweagent-OpenAI__GPT-5-instance_flipt-io__flipt-3d5a345f94c2adc8a0eaa102c189c08ad4c0f8e8-479591a7` | SWE-agent | true | 62 | source-valid | sweagent-trajectory-elements; 62 operations |
| `sweagent-OpenAI__GPT-5-instance_flipt-io__flipt-756f00f79ba8abf9fe53f3c6c818123b42eb7355-74bc5f38` | SWE-agent | true | 59 | source-valid | sweagent-trajectory-elements; 59 operations |
| `sweagent-OpenAI__GPT-5-instance_future-architect__vuls-b8db2e0b74f60cb7d45f710f255e061f054b6afc-e3bc6a2f` | SWE-agent | true | 42 | source-valid | sweagent-trajectory-elements; 42 operations |
| `sweagent-OpenAI__GPT-5-instance_internetarchive__openlibrary-60725705782832a2cb22e17c49697948a42a9d03-v298a7a812ceed28c4c18355a091f1b268fe56d86-0036e996` | SWE-agent | true | 24 | source-valid | sweagent-trajectory-elements; 24 operations |
| `sweagent-OpenAI__GPT-5-instance_internetarchive__openlibrary-757fcf46c70530739c150c57b37d6375f155dc97-ve8c8d62a2b60610a3c4631f5f23ed866bada9818-f2b0c13d` | SWE-agent | true | 44 | source-valid | sweagent-trajectory-elements; 44 operations |
| `sweagent-OpenAI__GPT-5-instance_internetarchive__openlibrary-77c16d530b4d5c0f33d68bead2c6b329aee9b996-ve8c8d62a2b60610a3c4631f5f23ed866bada9818-904f86da` | SWE-agent | false | 50 | source-valid | sweagent-trajectory-elements; 50 operations |
| `sweagent-OpenAI__GPT-5-instance_internetarchive__openlibrary-8a5a63af6e0be406aa6c8c9b6d5f28b2f1b6af5a-v0f5aece3601a5b4419f7ccec1dbda2071be28ee4-0e380383` | SWE-agent | true | 31 | source-valid | sweagent-trajectory-elements; 31 operations |
| `sweagent-OpenAI__GPT-5-instance_internetarchive__openlibrary-910b08570210509f3bcfebf35c093a48243fe754-v0f5aece3601a5b4419f7ccec1dbda2071be28ee4-084561f5` | SWE-agent | false | 57 | source-valid | sweagent-trajectory-elements; 57 operations |
| `sweagent-OpenAI__GPT-5-instance_internetarchive__openlibrary-bb152d23c004f3d68986877143bb0f83531fe401-ve8c8d62a2b60610a3c4631f5f23ed866bada9818-767f3550` | SWE-agent | false | 46 | source-valid | sweagent-trajectory-elements; 46 operations |
| `sweagent-OpenAI__GPT-5-instance_internetarchive__openlibrary-d109cc7e6e161170391f98f9a6fa1d02534c18e4-ve8c8d62a2b60610a3c4631f5f23ed866bada9818-54010cb4` | SWE-agent | false | 121 | source-valid | sweagent-trajectory-elements; 121 operations |
| `sweagent-OpenAI__GPT-5-instance_internetarchive__openlibrary-e1e502986a3b003899a8347ac8a7ff7b08cbfc39-v08d8e8889ec945ab821fb156c04c7d2e2810debb-1e80cfac` | SWE-agent | false | 22 | source-valid | sweagent-trajectory-elements; 22 operations |
| `sweagent-OpenAI__GPT-5-instance_qutebrowser__qutebrowser-2dd8966fdcf11972062c540b7a787e4d0de8d372-v363c8a7e5ccdf6968fc7ab84a2053ac78036691d-9d1c92b0` | SWE-agent | true | 94 | source-valid | sweagent-trajectory-elements; 94 operations |
| `sweagent-OpenAI__GPT-5-instance_qutebrowser__qutebrowser-473a15f7908f2bb6d670b0e908ab34a28d8cf7e2-v363c8a7e5ccdf6968fc7ab84a2053ac78036691d-d3f257e7` | SWE-agent | false | 35 | source-valid | sweagent-trajectory-elements; 35 operations |
| `sweagent-OpenAI__GPT-5-instance_qutebrowser__qutebrowser-f8e7fea0becae25ae20606f1422068137189fe9e-f1d1d09d` | SWE-agent | true | 50 | source-valid | sweagent-trajectory-elements; 50 operations |
| `sweagent-OpenAI__GPT-5-jqlang__jq-1793-6f5470b0` | SWE-agent | true | 52 | source-valid | sweagent-trajectory-elements; 52 operations |
| `sweagent-OpenAI__GPT-5-jqlang__jq-2654-6603ae02` | SWE-agent | true | 25 | source-valid | sweagent-trajectory-elements; 25 operations |
| `sweagent-OpenAI__GPT-5-jqlang__jq-2919-93f075bf` | SWE-agent | true | 33 | source-valid | sweagent-trajectory-elements; 33 operations |
| `sweagent-OpenAI__GPT-5-keras-team__keras-18553-468c06f3` | SWE-agent | false | 38 | source-valid | sweagent-trajectory-elements; 38 operations |
| `sweagent-OpenAI__GPT-5-keras-team__keras-18871-85aa3499` | SWE-agent | false | 20 | source-valid | sweagent-trajectory-elements; 20 operations |
| `sweagent-OpenAI__GPT-5-keras-team__keras-19201-a9b06a76` | SWE-agent | true | 39 | source-valid | sweagent-trajectory-elements; 39 operations |
| `sweagent-OpenAI__GPT-5-keras-team__keras-19484-e97d97d4` | SWE-agent | true | 28 | source-valid | sweagent-trajectory-elements; 28 operations |
| `sweagent-OpenAI__GPT-5-keras-team__keras-19636-be8c419a` | SWE-agent | true | 33 | source-valid | sweagent-trajectory-elements; 33 operations |
| `sweagent-OpenAI__GPT-5-keras-team__keras-19775-5d529dfd` | SWE-agent | true | 26 | excluded | sweagent-trajectory-elements emitted 48 operations; public step_count is 26 |
| `sweagent-OpenAI__GPT-5-keras-team__keras-19838-040f1c90` | SWE-agent | true | 26 | source-valid | sweagent-trajectory-elements; 26 operations |
| `sweagent-OpenAI__GPT-5-keras-team__keras-19844-ca79bed1` | SWE-agent | true | 63 | source-valid | sweagent-trajectory-elements; 63 operations |
| `sweagent-OpenAI__GPT-5-keras-team__keras-19863-d4ec1df3` | SWE-agent | false | 46 | source-valid | sweagent-trajectory-elements; 46 operations |
| `sweagent-OpenAI__GPT-5-keras-team__keras-19924-dc8be29c` | SWE-agent | true | 44 | source-valid | sweagent-trajectory-elements; 44 operations |
| `sweagent-OpenAI__GPT-5-langchain-ai__langchain-4009-0a56c80f` | SWE-agent | false | 23 | source-valid | sweagent-trajectory-elements; 23 operations |
| `sweagent-OpenAI__GPT-5-langchain-ai__langchain-5609-c3440b94` | SWE-agent | true | 28 | source-valid | sweagent-trajectory-elements; 28 operations |
| `sweagent-OpenAI__GPT-5-microsoft__vscode-135197-4a0fddee` | SWE-agent | true | 72 | source-valid | sweagent-trajectory-elements; 72 operations |
| `sweagent-OpenAI__GPT-5-microsoft__vscode-153857-9567d425` | SWE-agent | true | 1 | excluded | sweagent-trajectory-elements emitted 36 operations; public step_count is 1 |
| `sweagent-OpenAI__GPT-5-microsoft__vscode-160342-b846798e` | SWE-agent | true | 23 | source-valid | sweagent-trajectory-elements; 23 operations |
| `sweagent-OpenAI__GPT-5-microsoft__vscode-177084-ddcf304b` | SWE-agent | true | 27 | source-valid | sweagent-trajectory-elements; 27 operations |
| `sweagent-OpenAI__GPT-5-mockito__mockito-3220-fcaf052e` | SWE-agent | true | 19 | source-valid | sweagent-trajectory-elements; 19 operations |
| `sweagent-OpenAI__GPT-5-mui__material-ui-11451-c1ca3d8a` | SWE-agent | true | 54 | excluded | sweagent-trajectory-elements emitted 94 operations; public step_count is 54 |
| `sweagent-OpenAI__GPT-5-mui__material-ui-13778-d70b6204` | SWE-agent | true | 25 | source-valid | sweagent-trajectory-elements; 25 operations |
| `sweagent-OpenAI__GPT-5-mui__material-ui-15359-31082364` | SWE-agent | true | 43 | source-valid | sweagent-trajectory-elements; 43 operations |
| `sweagent-OpenAI__GPT-5-mui__material-ui-18141-c7612a1f` | SWE-agent | true | 28 | source-valid | sweagent-trajectory-elements; 28 operations |
| `sweagent-OpenAI__GPT-5-mui__material-ui-18257-ecfae4b2` | SWE-agent | true | 23 | source-valid | sweagent-trajectory-elements; 23 operations |
| `sweagent-OpenAI__GPT-5-mui__material-ui-18683-2bd64ee3` | SWE-agent | true | 22 | source-valid | sweagent-trajectory-elements; 22 operations |
| `sweagent-OpenAI__GPT-5-mui__material-ui-19121-fef02978` | SWE-agent | true | 19 | source-valid | sweagent-trajectory-elements; 19 operations |
| `sweagent-OpenAI__GPT-5-mui__material-ui-19849-4ff77a47` | SWE-agent | true | 39 | source-valid | sweagent-trajectory-elements; 39 operations |
| `sweagent-OpenAI__GPT-5-mui__material-ui-20252-99dc0124` | SWE-agent | true | 25 | source-valid | sweagent-trajectory-elements; 25 operations |
| `sweagent-OpenAI__GPT-5-mui__material-ui-26061-b6ecdd74` | SWE-agent | true | 31 | source-valid | sweagent-trajectory-elements; 31 operations |
| `sweagent-OpenAI__GPT-5-mui__material-ui-26807-0de9c978` | SWE-agent | true | 58 | source-valid | sweagent-trajectory-elements; 58 operations |
| `sweagent-OpenAI__GPT-5-mui__material-ui-28186-2ac683f2` | SWE-agent | true | 6 | excluded | sweagent-trajectory-elements emitted 30 operations; public step_count is 6 |
| `sweagent-OpenAI__GPT-5-mui__material-ui-28813-77bdd20a` | SWE-agent | true | 38 | source-valid | sweagent-trajectory-elements; 38 operations |
| `sweagent-OpenAI__GPT-5-mui__material-ui-29023-06898477` | SWE-agent | true | 59 | source-valid | sweagent-trajectory-elements; 59 operations |
| `sweagent-OpenAI__GPT-5-mui__material-ui-34610-d8f4d813` | SWE-agent | true | 42 | source-valid | sweagent-trajectory-elements; 42 operations |
| `sweagent-OpenAI__GPT-5-mui__material-ui-42412-73b8be1c` | SWE-agent | true | 28 | source-valid | sweagent-trajectory-elements; 28 operations |
| `sweagent-OpenAI__GPT-5-nlohmann__json-2989-de7a03b5` | SWE-agent | true | 52 | source-valid | sweagent-trajectory-elements; 52 operations |
| `sweagent-OpenAI__GPT-5-nlohmann__json-3601-631e40a6` | SWE-agent | true | 14 | source-valid | sweagent-trajectory-elements; 14 operations |
| `sweagent-OpenAI__GPT-5-nlohmann__json-4512-8b6ac7dd` | SWE-agent | true | 18 | source-valid | sweagent-trajectory-elements; 18 operations |
| `sweagent-OpenAI__GPT-5-ponylang__ponyc-1057-f7b52e61` | SWE-agent | true | 20 | source-valid | sweagent-trajectory-elements; 20 operations |
| `sweagent-OpenAI__GPT-5-ponylang__ponyc-2201-8c684fea` | SWE-agent | true | 6 | source-valid | sweagent-trajectory-elements; 6 operations |
| `sweagent-OpenAI__GPT-5-prettier__prettier-12930-05aa8eba` | SWE-agent | true | 10 | excluded | sweagent-trajectory-elements emitted 18 operations; public step_count is 10 |
| `sweagent-OpenAI__GPT-5-prettier__prettier-14400-0ecd6642` | SWE-agent | true | 14 | source-valid | sweagent-trajectory-elements; 14 operations |
| `sweagent-OpenAI__GPT-5-prettier__prettier-3515-d2f26ed0` | SWE-agent | true | 29 | source-valid | sweagent-trajectory-elements; 29 operations |
| `sweagent-OpenAI__GPT-5-prettier__prettier-361-0e842b35` | SWE-agent | true | 24 | source-valid | sweagent-trajectory-elements; 24 operations |
| `sweagent-OpenAI__GPT-5-prettier__prettier-8046-6c1254db` | SWE-agent | true | 26 | source-valid | sweagent-trajectory-elements; 26 operations |
| `sweagent-OpenAI__GPT-5-serverless__serverless-2576-80a1d381` | SWE-agent | true | 62 | source-valid | sweagent-trajectory-elements; 62 operations |
| `sweagent-OpenAI__GPT-5-serverless__serverless-3457-5ad91382` | SWE-agent | true | 29 | source-valid | sweagent-trajectory-elements; 29 operations |
| `sweagent-OpenAI__GPT-5-serverless__serverless-7374-2a246c8b` | SWE-agent | true | 34 | source-valid | sweagent-trajectory-elements; 34 operations |
| `sweagent-OpenAI__GPT-5-tokio-rs__bytes-721-79d282f7` | SWE-agent | true | 12 | source-valid | sweagent-trajectory-elements; 12 operations |
| `sweagent-OpenAI__GPT-5-yt-dlp__yt-dlp-5933-2584b464` | SWE-agent | false | 37 | source-valid | sweagent-trajectory-elements; 37 operations |
| `sweagent-OpenAI__GPT-5-yt-dlp__yt-dlp-9862-841baea5` | SWE-agent | true | 29 | source-valid | sweagent-trajectory-elements; 29 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-3d-model-format-legacy-5eb709af` | Terminus2 | false | 94 | excluded | terminus2-commands-txt-strings emitted 95 operations; public step_count is 94 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-accelerate-maximal-square-eca249fc` | Terminus2 | false | 22 | source-valid | terminus2-commands-txt-strings; 22 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-acl-permissions-inheritance-a058e2e5` | Terminus2 | false | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-add-benchmark-lm-eval-harness-11987c87` | Terminus2 | false | 206 | excluded | terminus2-commands-txt-strings emitted 208 operations; public step_count is 206 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-aimo-airline-departures-904eb38f` | Terminus2 | false | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-amuse-install-ad1597ab` | Terminus2 | true | 49 | source-valid | terminus2-commands-txt-strings; 49 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-assign-seats-287735a2` | Terminus2 | true | 13 | source-valid | terminus2-commands-txt-strings; 13 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-audio-synth-stft-peaks-e07e3ef5` | Terminus2 | false | 37 | excluded | terminus2-commands-txt-strings emitted 38 operations; public step_count is 37 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-blind-maze-explorer-5x5-dc477a42` | Terminus2 | false | 46 | excluded | terminus2-commands-txt-strings emitted 47 operations; public step_count is 46 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-blind-maze-explorer-algorithm-e5814a22` | Terminus2 | true | 47 | excluded | terminus2-commands-txt-strings emitted 48 operations; public step_count is 47 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-bn-fit-modify-e23f783a` | Terminus2 | true | 36 | source-valid | terminus2-commands-txt-strings; 36 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-break-filter-js-from-html-4096e492` | Terminus2 | false | 89 | excluded | terminus2-commands-txt-strings emitted 90 operations; public step_count is 89 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-broken-networking-f38159e0` | Terminus2 | missing | 44 | source-valid | terminus2-commands-txt-strings; 44 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-broken-python-02d55149` | Terminus2 | true | 30 | excluded | terminus2-commands-txt-strings emitted 34 operations; public step_count is 30 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-cython-ext-a7e47d56` | Terminus2 | false | 53 | excluded | terminus2-commands-txt-strings emitted 56 operations; public step_count is 53 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-initramfs-qemu-bc2e999c` | Terminus2 | missing | 28 | source-valid | terminus2-commands-txt-strings; 28 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-linux-kernel-qemu-7699e895` | Terminus2 | false | 81 | source-valid | terminus2-commands-txt-strings; 81 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-pmars-6fe094bc` | Terminus2 | true | 34 | source-valid | terminus2-commands-txt-strings; 34 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-pov-ray-0022ddb2` | Terminus2 | false | 51 | source-valid | terminus2-commands-txt-strings; 51 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-stp-56801309` | Terminus2 | false | 40 | excluded | terminus2-commands-txt-strings emitted 41 operations; public step_count is 40 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-tcc-qemu-fba34809` | Terminus2 | false | 25 | source-valid | terminus2-commands-txt-strings; 25 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-caffe-cifar-10-f86162d9` | Terminus2 | false | 99 | source-valid | terminus2-commands-txt-strings; 99 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-cartpole-rl-training-569c9449` | Terminus2 | missing | 13 | source-valid | terminus2-commands-txt-strings; 13 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-catch-me-if-you-can-d89cfe9a` | Terminus2 | false | 68 | excluded | terminus2-commands-txt-strings emitted 69 operations; public step_count is 68 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-causal-inference-r-887a15bd` | Terminus2 | false | 53 | excluded | terminus2-commands-txt-strings emitted 54 operations; public step_count is 53 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-chem-property-targeting-32a06e96` | Terminus2 | false | 15 | excluded | terminus2-commands-txt-strings emitted 16 operations; public step_count is 15 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-chem-rf-2ba0f88d` | Terminus2 | false | 59 | source-valid | terminus2-commands-txt-strings; 59 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-chess-best-move-b049f713` | Terminus2 | false | 34 | excluded | Terminus2 archive has no commands.txt |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-circuit-fibsqrt-2c6a2717` | Terminus2 | false | 92 | source-valid | terminus2-commands-txt-strings; 92 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-cobol-modernization-9f2753a3` | Terminus2 | false | 35 | source-valid | terminus2-commands-txt-strings; 35 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-code-from-image-14a45388` | Terminus2 | true | 27 | excluded | terminus2-commands-txt-strings emitted 28 operations; public step_count is 27 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-compile-compcert-cff31022` | Terminus2 | missing | 130 | source-valid | terminus2-commands-txt-strings; 130 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-conda-env-conflict-resolution-a9c17f07` | Terminus2 | false | 49 | source-valid | terminus2-commands-txt-strings; 49 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-configure-git-webserver-9b659867` | Terminus2 | false | 30 | source-valid | terminus2-commands-txt-strings; 30 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-count-dataset-tokens-ad1d3494` | Terminus2 | false | 40 | excluded | terminus2-commands-txt-strings emitted 41 operations; public step_count is 40 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-countdown-game-e91abf59` | Terminus2 | true | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-cprofiling-python-85226a53` | Terminus2 | true | 21 | source-valid | terminus2-commands-txt-strings; 21 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-cron-broken-network-5669e672` | Terminus2 | false | 63 | excluded | terminus2-commands-txt-strings emitted 64 operations; public step_count is 63 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-cross-entropy-method-378af4b8` | Terminus2 | true | 17 | excluded | terminus2-commands-txt-strings emitted 18 operations; public step_count is 17 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-csv-to-parquet-04eeffa1` | Terminus2 | true | 44 | source-valid | terminus2-commands-txt-strings; 44 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-db-wal-recovery-6792ef3f` | Terminus2 | false | 29 | excluded | terminus2-commands-txt-strings emitted 30 operations; public step_count is 29 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-decommissioning-service-with-sensitive-data-915140e1` | Terminus2 | true | 26 | source-valid | terminus2-commands-txt-strings; 26 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-deterministic-tarball-6396449f` | Terminus2 | false | 30 | excluded | terminus2-commands-txt-strings emitted 32 operations; public step_count is 30 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-distribution-search-3b7177d8` | Terminus2 | false | 30 | source-valid | terminus2-commands-txt-strings; 30 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-dna-assembly-ccf5c523` | Terminus2 | false | 29 | source-valid | terminus2-commands-txt-strings; 29 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-dna-insert-cf42cdc2` | Terminus2 | false | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-download-youtube-402af613` | Terminus2 | false | 35 | source-valid | terminus2-commands-txt-strings; 35 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-enemy-grid-escape-6c9bd59b` | Terminus2 | false | 602 | source-valid | terminus2-commands-txt-strings; 602 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-extract-elf-a67df0f2` | Terminus2 | false | 19 | source-valid | terminus2-commands-txt-strings; 19 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-extract-moves-from-video-3ade39b3` | Terminus2 | false | 44 | source-valid | terminus2-commands-txt-strings; 44 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-feal-differential-cryptanalysis-d54aba6a` | Terminus2 | false | 38 | excluded | terminus2-commands-txt-strings emitted 39 operations; public step_count is 38 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-feal-linear-cryptanalysis-675ff900` | Terminus2 | false | 52 | excluded | terminus2-commands-txt-strings emitted 53 operations; public step_count is 52 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-fibonacci-server-be04cdbc` | Terminus2 | true | 12 | source-valid | terminus2-commands-txt-strings; 12 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-filter-js-from-html-61cd1fd1` | Terminus2 | false | 20 | excluded | terminus2-commands-txt-strings emitted 21 operations; public step_count is 20 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-financial-document-processor-cc145e6b` | Terminus2 | false | 33 | source-valid | terminus2-commands-txt-strings; 33 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-find-official-code-83933bf6` | Terminus2 | false | 13 | excluded | terminus2-commands-txt-strings emitted 14 operations; public step_count is 13 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-fix-code-vulnerability-3a3bc00e` | Terminus2 | true | 77 | source-valid | terminus2-commands-txt-strings; 77 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-fix-git-81e6eaff` | Terminus2 | true | 14 | excluded | terminus2-commands-txt-strings emitted 15 operations; public step_count is 14 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-fix-ocaml-gc-5784d704` | Terminus2 | false | 327 | excluded | terminus2-commands-txt-strings emitted 328 operations; public step_count is 327 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-fix-pandas-version-44855256` | Terminus2 | true | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-flood-monitoring-basic-c101ca63` | Terminus2 | true | 19 | source-valid | terminus2-commands-txt-strings; 19 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-fmri-encoding-r-8e4f9489` | Terminus2 | true | 50 | source-valid | terminus2-commands-txt-strings; 50 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-form-filling-6907bd11` | Terminus2 | true | 22 | excluded | terminus2-commands-txt-strings emitted 23 operations; public step_count is 22 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-gcc-compiler-optimization-419e5468` | Terminus2 | true | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-gcode-to-text-04074693` | Terminus2 | false | 12 | excluded | terminus2-commands-txt-strings emitted 13 operations; public step_count is 12 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-get-bitcoin-nodes-34b1eb45` | Terminus2 | false | 21 | source-valid | terminus2-commands-txt-strings; 21 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-git-leak-recovery-02eec3b6` | Terminus2 | true | 17 | excluded | terminus2-commands-txt-strings emitted 18 operations; public step_count is 17 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-git-workflow-hack-db1a1fd0` | Terminus2 | true | 43 | source-valid | terminus2-commands-txt-strings; 43 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-gomoku-planner-2719fd49` | Terminus2 | true | 13 | source-valid | terminus2-commands-txt-strings; 13 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-gpt2-codegolf-a0d3636a` | Terminus2 | false | 28 | source-valid | terminus2-commands-txt-strings; 28 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-hdfs-deployment-2f1fc6b6` | Terminus2 | true | 53 | source-valid | terminus2-commands-txt-strings; 53 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-heterogeneous-dates-671734f6` | Terminus2 | true | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-hf-lora-adapter-4b86f64e` | Terminus2 | false | 38 | source-valid | terminus2-commands-txt-strings; 38 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-hf-model-inference-2d97482b` | Terminus2 | false | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-hf-train-lora-adapter-0f6aa9d1` | Terminus2 | missing | 48 | source-valid | terminus2-commands-txt-strings; 48 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-html-finance-verify-ecd6dfd7` | Terminus2 | false | 16 | excluded | terminus2-commands-txt-strings emitted 17 operations; public step_count is 16 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-huarong-dao-solver-bf643dc7` | Terminus2 | false | 16 | excluded | terminus2-commands-txt-strings emitted 17 operations; public step_count is 16 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-hydra-debug-slurm-mode-837c94b0` | Terminus2 | true | 26 | excluded | terminus2-commands-txt-strings emitted 27 operations; public step_count is 26 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-implement-eigenvectors-from-eigenvalues-research-paper-25778eae` | Terminus2 | false | 31 | source-valid | terminus2-commands-txt-strings; 31 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-incompatible-python-fasttext-64f07e3f` | Terminus2 | true | 26 | excluded | terminus2-commands-txt-strings emitted 28 operations; public step_count is 26 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-install-klee-minimal-57ed56f5` | Terminus2 | true | 100 | excluded | terminus2-commands-txt-strings emitted 104 operations; public step_count is 100 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-install-windows-xp-4ceed7d6` | Terminus2 | false | 147 | source-valid | terminus2-commands-txt-strings; 147 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-intrusion-detection-9d78e545` | Terminus2 | true | 29 | source-valid | terminus2-commands-txt-strings; 29 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-jq-data-processing-0f26000b` | Terminus2 | true | 11 | excluded | terminus2-commands-txt-strings emitted 12 operations; public step_count is 11 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-jupyter-notebook-server-0bc07c40` | Terminus2 | true | 40 | source-valid | terminus2-commands-txt-strings; 40 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-large-scale-text-editing-54f81458` | Terminus2 | false | 72 | source-valid | terminus2-commands-txt-strings; 72 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-largest-eigenval-eb9cc4f2` | Terminus2 | false | 57 | excluded | terminus2-commands-txt-strings emitted 58 operations; public step_count is 57 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-lean4-proof-33ef0bfe` | Terminus2 | false | 103 | excluded | terminus2-commands-txt-strings emitted 104 operations; public step_count is 103 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-leelachess0-pytorch-conversion-4b4c022f` | Terminus2 | false | 29 | excluded | terminus2-commands-txt-strings emitted 30 operations; public step_count is 29 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-llm-inference-batching-scheduler-36976180` | Terminus2 | false | 33 | excluded | terminus2-commands-txt-strings emitted 34 operations; public step_count is 33 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-llm-spec-decoding-a5cda7d7` | Terminus2 | true | 23 | excluded | terminus2-commands-txt-strings emitted 24 operations; public step_count is 23 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-log-summary-58c21025` | Terminus2 | true | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-log-summary-date-ranges-f03b8f15` | Terminus2 | true | 12 | source-valid | terminus2-commands-txt-strings; 12 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-logistic-regression-divergence-0b8df7b3` | Terminus2 | false | 27 | excluded | terminus2-commands-txt-strings emitted 28 operations; public step_count is 27 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-magsac-install-4c7fd435` | Terminus2 | false | 113 | source-valid | terminus2-commands-txt-strings; 113 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-mailman-3540eeca` | Terminus2 | true | 44 | excluded | Terminus2 archive has no commands.txt |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-make-doom-for-mips-cc5c8770` | Terminus2 | false | 200 | source-valid | terminus2-commands-txt-strings; 200 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-make-mips-interpreter-35ea4c65` | Terminus2 | false | 61 | excluded | terminus2-commands-txt-strings emitted 62 operations; public step_count is 61 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-mcmc-sampling-stan-93d7bf48` | Terminus2 | true | 34 | source-valid | terminus2-commands-txt-strings; 34 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-merge-diff-arc-agi-task-7227955c` | Terminus2 | false | 49 | source-valid | terminus2-commands-txt-strings; 49 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-mixed-integer-programming-2323e94b` | Terminus2 | true | 29 | source-valid | terminus2-commands-txt-strings; 29 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-model-extraction-relu-logits-71be80df` | Terminus2 | false | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-modernize-fortran-build-3ff6fdb7` | Terminus2 | true | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-modernize-scientific-stack-2675c3fd` | Terminus2 | true | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-movie-helper-83959fe7` | Terminus2 | false | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-mteb-eval-03df9a5d` | Terminus2 | true | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-mteb-leaderboard-d9697907` | Terminus2 | false | 28 | source-valid | terminus2-commands-txt-strings; 28 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-multi-source-data-merger-12393f86` | Terminus2 | true | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-neuron-to-jaxley-conversion-d784f8de` | Terminus2 | false | 31 | source-valid | terminus2-commands-txt-strings; 31 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-nginx-request-logging-15fdb884` | Terminus2 | true | 37 | source-valid | terminus2-commands-txt-strings; 37 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-npm-conflict-resolution-1fb2a796` | Terminus2 | false | 37 | excluded | terminus2-commands-txt-strings emitted 38 operations; public step_count is 37 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-openssl-selfsigned-cert-f401edbf` | Terminus2 | true | 35 | source-valid | terminus2-commands-txt-strings; 35 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-optimal-transport-63f97042` | Terminus2 | false | 17 | excluded | terminus2-commands-txt-strings emitted 18 operations; public step_count is 17 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-organization-json-generator-c7de58b7` | Terminus2 | true | 12 | excluded | terminus2-commands-txt-strings emitted 13 operations; public step_count is 12 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-overfull-hbox-70f3acfa` | Terminus2 | true | 61 | excluded | Terminus2 archive has no commands.txt |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-pandas-sql-query-7a8e84e0` | Terminus2 | true | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-parallel-particle-simulator-56d1327d` | Terminus2 | false | 107 | source-valid | terminus2-commands-txt-strings; 107 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-parallelize-compute-squares-eb552139` | Terminus2 | true | 17 | excluded | terminus2-commands-txt-strings emitted 18 operations; public step_count is 17 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-parallelize-graph-619aaf8f` | Terminus2 | false | 47 | excluded | terminus2-commands-txt-strings emitted 48 operations; public step_count is 47 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-password-recovery-0d7e8446` | Terminus2 | false | 55 | source-valid | terminus2-commands-txt-strings; 55 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-path-tracing-10ed6f44` | Terminus2 | false | 33 | source-valid | terminus2-commands-txt-strings; 33 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-path-tracing-reverse-f5f5b8bf` | Terminus2 | false | 59 | excluded | terminus2-commands-txt-strings emitted 60 operations; public step_count is 59 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-pcap-to-netflow-83901276` | Terminus2 | false | 100 | source-valid | terminus2-commands-txt-strings; 100 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-play-zork-c2eb2245` | Terminus2 | false | 199 | excluded | terminus2-commands-txt-strings emitted 200 operations; public step_count is 199 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-play-zork-easy-9e809eb3` | Terminus2 | false | 568 | source-valid | terminus2-commands-txt-strings; 568 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-polyglot-c-py-00eee45b` | Terminus2 | false | 38 | source-valid | terminus2-commands-txt-strings; 38 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-polyglot-rust-c-626afe73` | Terminus2 | false | 106 | source-valid | terminus2-commands-txt-strings; 106 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-port-compressor-b12aa2b9` | Terminus2 | false | 105 | excluded | terminus2-commands-txt-strings emitted 106 operations; public step_count is 105 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-portfolio-optimization-bdd2ad8f` | Terminus2 | true | 15 | excluded | terminus2-commands-txt-strings emitted 16 operations; public step_count is 15 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-predicate-pushdown-bench-ce270ec8` | Terminus2 | missing | 52 | source-valid | terminus2-commands-txt-strings; 52 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-predict-customer-churn-0d553487` | Terminus2 | false | 13 | source-valid | terminus2-commands-txt-strings; 13 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-processing-pipeline-b359442c` | Terminus2 | true | 22 | excluded | terminus2-commands-txt-strings emitted 23 operations; public step_count is 22 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-protein-assembly-dfa5f8b4` | Terminus2 | false | 35 | excluded | terminus2-commands-txt-strings emitted 36 operations; public step_count is 35 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-protocol-analysis-rs-7c5f5525` | Terminus2 | false | 62 | excluded | terminus2-commands-txt-strings emitted 63 operations; public step_count is 62 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-puzzle-solver-b02de9a4` | Terminus2 | false | 23 | source-valid | terminus2-commands-txt-strings; 23 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-pypi-server-302bbb1f` | Terminus2 | true | 49 | source-valid | terminus2-commands-txt-strings; 49 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-pytorch-model-cli-3c920ed8` | Terminus2 | false | 20 | source-valid | terminus2-commands-txt-strings; 20 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-pytorch-model-recovery-d836c842` | Terminus2 | true | 14 | excluded | terminus2-commands-txt-strings emitted 15 operations; public step_count is 14 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-query-optimize-9b7a8831` | Terminus2 | false | 15 | excluded | terminus2-commands-txt-strings emitted 16 operations; public step_count is 15 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-rare-mineral-allocation-602eddc4` | Terminus2 | false | 13 | source-valid | terminus2-commands-txt-strings; 13 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-recover-accuracy-log-e3a7a027` | Terminus2 | true | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-recover-obfuscated-files-c0a5a7f9` | Terminus2 | true | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-regex-chess-f6300f5d` | Terminus2 | false | 69 | source-valid | terminus2-commands-txt-strings; 69 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-reshard-c4-data-14835550` | Terminus2 | missing | 37 | excluded | terminus2-commands-txt-strings emitted 38 operations; public step_count is 37 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-reverse-engineering-d69939cc` | Terminus2 | false | 201 | excluded | terminus2-commands-txt-strings emitted 202 operations; public step_count is 201 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-rstan-to-pystan-6adcbc5e` | Terminus2 | true | 38 | excluded | terminus2-commands-txt-strings emitted 39 operations; public step_count is 38 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-run-pdp11-code-3639962f` | Terminus2 | false | 40 | source-valid | terminus2-commands-txt-strings; 40 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-sam-cell-seg-af70dbfb` | Terminus2 | false | 39 | source-valid | terminus2-commands-txt-strings; 39 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-schedule-vacation-9e1a63a1` | Terminus2 | true | 18 | excluded | terminus2-commands-txt-strings emitted 19 operations; public step_count is 18 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-schemelike-metacircular-eval-ea12ff59` | Terminus2 | false | 89 | source-valid | terminus2-commands-txt-strings; 89 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-setup-custom-dev-env-0dcc0f56` | Terminus2 | true | 39 | source-valid | terminus2-commands-txt-strings; 39 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-solana-data-11b5885e` | Terminus2 | true | 66 | source-valid | terminus2-commands-txt-strings; 66 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-solve-maze-challenge-27b84da7` | Terminus2 | missing | 67 | source-valid | terminus2-commands-txt-strings; 67 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-solve-sudoku-5b91640a` | Terminus2 | false | 33 | excluded | terminus2-commands-txt-strings emitted 34 operations; public step_count is 33 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-sparql-university-2b5e8083` | Terminus2 | false | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-speech-to-text-6c0c82dd` | Terminus2 | true | 36 | source-valid | terminus2-commands-txt-strings; 36 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-sqlite-db-truncate-e979013b` | Terminus2 | false | 15 | excluded | terminus2-commands-txt-strings emitted 16 operations; public step_count is 15 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-sqlite-with-gcov-e63a97d2` | Terminus2 | true | 32 | source-valid | terminus2-commands-txt-strings; 32 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-stable-parallel-kmeans-9f16d721` | Terminus2 | missing | 37 | excluded | terminus2-commands-txt-strings emitted 38 operations; public step_count is 37 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-sudo-llvm-ir-cccd6dc7` | Terminus2 | false | 96 | source-valid | terminus2-commands-txt-strings; 96 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-swe-bench-astropy-1-6b5580a5` | Terminus2 | true | 26 | excluded | terminus2-commands-txt-strings emitted 27 operations; public step_count is 26 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-swe-bench-astropy-2-041d9809` | Terminus2 | false | 28 | source-valid | terminus2-commands-txt-strings; 28 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-swe-bench-fsspec-db93a185` | Terminus2 | true | 29 | source-valid | terminus2-commands-txt-strings; 29 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-swe-bench-langcodes-8ded73f8` | Terminus2 | true | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-tmux-advanced-workflow-025b91fb` | Terminus2 | true | 164 | source-valid | terminus2-commands-txt-strings; 164 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-torch-pipeline-parallelism-1984746e` | Terminus2 | false | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-train-bpe-tokenizer-b8dfe7d6` | Terminus2 | true | 37 | excluded | terminus2-commands-txt-strings emitted 38 operations; public step_count is 37 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-train-fasttext-f617ba1c` | Terminus2 | false | 50 | source-valid | terminus2-commands-txt-strings; 50 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-tree-directory-parser-6c88f322` | Terminus2 | false | 76 | source-valid | terminus2-commands-txt-strings; 76 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-triton-interpret-13f3a750` | Terminus2 | false | 36 | excluded | terminus2-commands-txt-strings emitted 37 operations; public step_count is 36 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-tune-mjcf-b120ae1e` | Terminus2 | false | 55 | excluded | terminus2-commands-txt-strings emitted 56 operations; public step_count is 55 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-vertex-solver-120d947b` | Terminus2 | true | 12 | source-valid | terminus2-commands-txt-strings; 12 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-video-processing-cda5b6b4` | Terminus2 | false | 20 | source-valid | terminus2-commands-txt-strings; 20 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-vul-flask-77e6f39e` | Terminus2 | true | 19 | excluded | terminus2-commands-txt-strings emitted 20 operations; public step_count is 19 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-vul-flink-220ab971` | Terminus2 | false | 41 | excluded | terminus2-commands-txt-strings emitted 43 operations; public step_count is 41 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-vulnerable-secret-472cc6f6` | Terminus2 | true | 36 | excluded | terminus2-commands-txt-strings emitted 37 operations; public step_count is 36 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-wasm-pipeline-1db8244f` | Terminus2 | true | 45 | excluded | terminus2-commands-txt-strings emitted 46 operations; public step_count is 45 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-weighted-max-sat-solver-39519774` | Terminus2 | false | 15 | excluded | terminus2-commands-txt-strings emitted 16 operations; public step_count is 15 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-winning-avg-corewars-ecabbdb8` | Terminus2 | false | 50 | source-valid | terminus2-commands-txt-strings; 50 operations |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-word2vec-from-scratch-ea1b146f` | Terminus2 | false | 43 | excluded | terminus2-commands-txt-strings emitted 44 operations; public step_count is 43 |
| `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-write-compressor-cce26430` | Terminus2 | false | 46 | excluded | terminus2-commands-txt-strings emitted 47 operations; public step_count is 46 |
| `terminus2-DeepSeek__DeepSeek-V3.2-3d-model-format-legacy-5276d859` | Terminus2 | false | 282 | excluded | terminus2-commands-txt-strings emitted 277 operations; public step_count is 282 |
| `terminus2-DeepSeek__DeepSeek-V3.2-accelerate-maximal-square-450eddf0` | Terminus2 | true | 30 | source-valid | terminus2-commands-txt-strings; 30 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-acl-permissions-inheritance-f606d59c` | Terminus2 | false | 81 | source-valid | terminus2-commands-txt-strings; 81 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-adaptive-rejection-sampler-63290128` | Terminus2 | false | 99 | source-valid | terminus2-commands-txt-strings; 99 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-add-benchmark-lm-eval-harness-5dd94492` | Terminus2 | missing | 102 | source-valid | terminus2-commands-txt-strings; 102 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-aimo-airline-departures-7c3f82be` | Terminus2 | false | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-amuse-install-f391120f` | Terminus2 | false | 25 | source-valid | terminus2-commands-txt-strings; 25 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-analyze-access-logs-037ce402` | Terminus2 | true | 20 | source-valid | terminus2-commands-txt-strings; 20 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-assign-seats-168044e8` | Terminus2 | true | 23 | source-valid | terminus2-commands-txt-strings; 23 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-attention-mil-60e11f03` | Terminus2 | false | 27 | source-valid | terminus2-commands-txt-strings; 27 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-audio-synth-stft-peaks-41d83aaf` | Terminus2 | false | 74 | source-valid | terminus2-commands-txt-strings; 74 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-bank-trans-filter-991f9d5d` | Terminus2 | false | 24 | source-valid | terminus2-commands-txt-strings; 24 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-blind-maze-explorer-5x5-6a297c50` | Terminus2 | false | 37 | source-valid | terminus2-commands-txt-strings; 37 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-blind-maze-explorer-algorithm-8bd59838` | Terminus2 | true | 41 | source-valid | terminus2-commands-txt-strings; 41 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-break-filter-js-from-html-99b435eb` | Terminus2 | false | 78 | source-valid | terminus2-commands-txt-strings; 78 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-broken-networking-b9d5687a` | Terminus2 | missing | 116 | source-valid | terminus2-commands-txt-strings; 116 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-broken-python-81c4a6fd` | Terminus2 | true | 52 | source-valid | terminus2-commands-txt-strings; 52 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-build-cython-ext-af034763` | Terminus2 | false | 81 | source-valid | terminus2-commands-txt-strings; 81 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-build-initramfs-qemu-57cab4f9` | Terminus2 | missing | 48 | source-valid | terminus2-commands-txt-strings; 48 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-build-linux-kernel-qemu-34643748` | Terminus2 | true | 79 | source-valid | terminus2-commands-txt-strings; 79 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-build-pmars-d503acad` | Terminus2 | true | 59 | source-valid | terminus2-commands-txt-strings; 59 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-build-pov-ray-4a3cb2c6` | Terminus2 | missing | 197 | source-valid | terminus2-commands-txt-strings; 197 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-build-tcc-qemu-cf22cb92` | Terminus2 | true | 65 | source-valid | terminus2-commands-txt-strings; 65 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-caffe-cifar-10-04955e02` | Terminus2 | false | 160 | excluded | terminus2-commands-txt-strings emitted 159 operations; public step_count is 160 |
| `terminus2-DeepSeek__DeepSeek-V3.2-cancel-async-tasks-6e86fa61` | Terminus2 | false | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-cartpole-rl-training-97d1bbde` | Terminus2 | missing | 63 | source-valid | terminus2-commands-txt-strings; 63 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-catch-me-if-you-can-7f73ac9f` | Terminus2 | false | 194 | source-valid | terminus2-commands-txt-strings; 194 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-causal-inference-r-04374216` | Terminus2 | true | 71 | source-valid | terminus2-commands-txt-strings; 71 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-chem-property-targeting-7fdc8deb` | Terminus2 | false | 19 | source-valid | terminus2-commands-txt-strings; 19 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-chem-rf-3771ad99` | Terminus2 | missing | 90 | source-valid | terminus2-commands-txt-strings; 90 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-chess-best-move-241232d1` | Terminus2 | false | 69 | source-valid | terminus2-commands-txt-strings; 69 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-circuit-fibsqrt-657c8c21` | Terminus2 | false | 63 | source-valid | terminus2-commands-txt-strings; 63 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-classifier-debug-911be8f6` | Terminus2 | true | 48 | source-valid | terminus2-commands-txt-strings; 48 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-cobol-modernization-9a3a9e4f` | Terminus2 | true | 99 | source-valid | terminus2-commands-txt-strings; 99 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-code-from-image-5f4fd632` | Terminus2 | true | 38 | source-valid | terminus2-commands-txt-strings; 38 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-compile-compcert-4c8013f9` | Terminus2 | missing | 186 | excluded | terminus2-commands-txt-strings emitted 185 operations; public step_count is 186 |
| `terminus2-DeepSeek__DeepSeek-V3.2-conda-env-conflict-resolution-c8664885` | Terminus2 | true | 68 | source-valid | terminus2-commands-txt-strings; 68 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-configure-git-webserver-e5f0c90d` | Terminus2 | true | 95 | source-valid | terminus2-commands-txt-strings; 95 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-constraints-scheduling-acbf53dc` | Terminus2 | missing | 28 | source-valid | terminus2-commands-txt-strings; 28 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-count-call-stack-2683044f` | Terminus2 | false | 23 | source-valid | terminus2-commands-txt-strings; 23 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-count-dataset-tokens-fbcd552b` | Terminus2 | true | 49 | source-valid | terminus2-commands-txt-strings; 49 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-cpp-compatibility-b0a7abff` | Terminus2 | true | 15 | source-valid | terminus2-commands-txt-strings; 15 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-cprofiling-python-22345a01` | Terminus2 | true | 59 | source-valid | terminus2-commands-txt-strings; 59 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-create-bucket-3dae80e7` | Terminus2 | true | 42 | source-valid | terminus2-commands-txt-strings; 42 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-cron-broken-network-a4e4c43d` | Terminus2 | false | 240 | source-valid | terminus2-commands-txt-strings; 240 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-cross-entropy-method-3ab6a31c` | Terminus2 | true | 57 | source-valid | terminus2-commands-txt-strings; 57 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-csv-to-parquet-06969a1d` | Terminus2 | true | 48 | source-valid | terminus2-commands-txt-strings; 48 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-db-wal-recovery-5f90b39b` | Terminus2 | false | 106 | source-valid | terminus2-commands-txt-strings; 106 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-debug-long-program-f9835d4e` | Terminus2 | false | 103 | source-valid | terminus2-commands-txt-strings; 103 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-decommissioning-service-with-sensitive-data-a5bb5af7` | Terminus2 | true | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-deterministic-tarball-981c62fd` | Terminus2 | true | 103 | source-valid | terminus2-commands-txt-strings; 103 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-distribution-search-e3c1580b` | Terminus2 | true | 21 | source-valid | terminus2-commands-txt-strings; 21 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-dna-assembly-b8b8c2b3` | Terminus2 | false | 43 | source-valid | terminus2-commands-txt-strings; 43 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-dna-insert-520c18b9` | Terminus2 | false | 45 | source-valid | terminus2-commands-txt-strings; 45 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-download-youtube-c5956283` | Terminus2 | false | 102 | source-valid | terminus2-commands-txt-strings; 102 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-enemy-grid-escape-96becfdb` | Terminus2 | true | 112 | source-valid | terminus2-commands-txt-strings; 112 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-extract-elf-fcc24924` | Terminus2 | true | 36 | source-valid | terminus2-commands-txt-strings; 36 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-extract-moves-from-video-c4679471` | Terminus2 | false | 166 | source-valid | terminus2-commands-txt-strings; 166 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-extract-safely-6429619b` | Terminus2 | true | 12 | source-valid | terminus2-commands-txt-strings; 12 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-feal-differential-cryptanalysis-88fe47dc` | Terminus2 | false | 56 | source-valid | terminus2-commands-txt-strings; 56 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-feal-linear-cryptanalysis-9406e62f` | Terminus2 | false | 45 | source-valid | terminus2-commands-txt-strings; 45 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-fibonacci-server-b27e6f1b` | Terminus2 | false | 38 | source-valid | terminus2-commands-txt-strings; 38 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-filter-js-from-html-05d9157a` | Terminus2 | false | 67 | source-valid | terminus2-commands-txt-strings; 67 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-financial-document-processor-3b9d0eb2` | Terminus2 | false | 23 | source-valid | terminus2-commands-txt-strings; 23 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-find-official-code-2fd14897` | Terminus2 | false | 96 | source-valid | terminus2-commands-txt-strings; 96 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-fix-code-vulnerability-f01ce98e` | Terminus2 | true | 52 | source-valid | terminus2-commands-txt-strings; 52 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-fix-git-bbd1fcbd` | Terminus2 | true | 49 | source-valid | terminus2-commands-txt-strings; 49 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-fix-ocaml-gc-ad192ae0` | Terminus2 | missing | 179 | source-valid | terminus2-commands-txt-strings; 179 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-fix-pandas-version-fff0e20c` | Terminus2 | true | 36 | source-valid | terminus2-commands-txt-strings; 36 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-flood-monitoring-basic-7e99cbe4` | Terminus2 | true | 26 | source-valid | terminus2-commands-txt-strings; 26 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-fmri-encoding-r-fbcf46e9` | Terminus2 | true | 79 | source-valid | terminus2-commands-txt-strings; 79 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-form-filling-94a84989` | Terminus2 | true | 38 | source-valid | terminus2-commands-txt-strings; 38 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-gcc-compiler-optimization-0991d14d` | Terminus2 | true | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-gcode-to-text-e2dcaa50` | Terminus2 | false | 27 | source-valid | terminus2-commands-txt-strings; 27 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-get-bitcoin-nodes-081db50d` | Terminus2 | true | 136 | source-valid | terminus2-commands-txt-strings; 136 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-git-leak-recovery-f01aa7ee` | Terminus2 | true | 33 | source-valid | terminus2-commands-txt-strings; 33 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-git-multibranch-c063fb97` | Terminus2 | false | 275 | source-valid | terminus2-commands-txt-strings; 275 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-git-workflow-hack-c47e456a` | Terminus2 | true | 42 | source-valid | terminus2-commands-txt-strings; 42 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-gomoku-planner-b93dc45b` | Terminus2 | true | 39 | source-valid | terminus2-commands-txt-strings; 39 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-gpt2-codegolf-9bbae1e0` | Terminus2 | false | 135 | source-valid | terminus2-commands-txt-strings; 135 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-grid-pattern-transform-9596577c` | Terminus2 | false | 66 | source-valid | terminus2-commands-txt-strings; 66 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-hdfs-deployment-2b9d1ad2` | Terminus2 | false | 101 | source-valid | terminus2-commands-txt-strings; 101 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-heterogeneous-dates-e6acbd3f` | Terminus2 | false | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-hf-lora-adapter-0d1d8d57` | Terminus2 | missing | 54 | source-valid | terminus2-commands-txt-strings; 54 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-hf-model-inference-ddf6d620` | Terminus2 | true | 39 | source-valid | terminus2-commands-txt-strings; 39 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-hf-train-lora-adapter-629e2817` | Terminus2 | missing | 127 | source-valid | terminus2-commands-txt-strings; 127 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-html-finance-verify-2f784bbe` | Terminus2 | false | 65 | source-valid | terminus2-commands-txt-strings; 65 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-huarong-dao-solver-6e8536d1` | Terminus2 | true | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-hydra-debug-slurm-mode-bf8cf33d` | Terminus2 | false | 29 | source-valid | terminus2-commands-txt-strings; 29 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-implement-eigenvectors-from-eigenvalues-research-paper-9e885ac9` | Terminus2 | false | 51 | source-valid | terminus2-commands-txt-strings; 51 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-incompatible-python-fasttext-2bfc6f1b` | Terminus2 | true | 47 | source-valid | terminus2-commands-txt-strings; 47 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-install-klee-minimal-8742bfec` | Terminus2 | true | 218 | source-valid | terminus2-commands-txt-strings; 218 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-install-windows-3.11-9b3a3ca5` | Terminus2 | missing | 202 | excluded | terminus2-commands-txt-strings emitted 199 operations; public step_count is 202 |
| `terminus2-DeepSeek__DeepSeek-V3.2-install-windows-xp-55ea3c45` | Terminus2 | missing | 144 | source-valid | terminus2-commands-txt-strings; 144 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-interactive-maze-game-117358f3` | Terminus2 | false | 166 | source-valid | terminus2-commands-txt-strings; 166 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-intrusion-detection-ce2c11f5` | Terminus2 | false | 47 | source-valid | terminus2-commands-txt-strings; 47 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-jq-data-processing-bff78f3a` | Terminus2 | true | 38 | source-valid | terminus2-commands-txt-strings; 38 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-jsonl-aggregator-c1466677` | Terminus2 | true | 13 | source-valid | terminus2-commands-txt-strings; 13 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-jupyter-notebook-server-4f1636a3` | Terminus2 | true | 70 | source-valid | terminus2-commands-txt-strings; 70 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-kv-store-grpc-2aa6a056` | Terminus2 | false | 22 | source-valid | terminus2-commands-txt-strings; 22 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-large-scale-text-editing-c4819db5` | Terminus2 | false | 151 | source-valid | terminus2-commands-txt-strings; 151 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-largest-eigenval-e3f6e113` | Terminus2 | false | 82 | source-valid | terminus2-commands-txt-strings; 82 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-lean4-proof-0dd8d068` | Terminus2 | missing | 265 | source-valid | terminus2-commands-txt-strings; 265 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-leelachess0-pytorch-conversion-a0b986ad` | Terminus2 | missing | 200 | excluded | terminus2-commands-txt-strings emitted 198 operations; public step_count is 200 |
| `terminus2-DeepSeek__DeepSeek-V3.2-llm-inference-batching-scheduler-f9069cf0` | Terminus2 | true | 31 | source-valid | terminus2-commands-txt-strings; 31 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-llm-spec-decoding-755ae030` | Terminus2 | missing | 25 | source-valid | terminus2-commands-txt-strings; 25 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-log-summary-a07220b7` | Terminus2 | true | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-log-summary-date-ranges-f5d622ea` | Terminus2 | true | 29 | source-valid | terminus2-commands-txt-strings; 29 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-logistic-regression-divergence-f217bcf4` | Terminus2 | false | 40 | source-valid | terminus2-commands-txt-strings; 40 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-magsac-install-d45062d7` | Terminus2 | false | 125 | source-valid | terminus2-commands-txt-strings; 125 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-mahjong-winninghand-fcfb78fe` | Terminus2 | missing | 30 | source-valid | terminus2-commands-txt-strings; 30 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-mailman-b5f781e9` | Terminus2 | false | 201 | source-valid | terminus2-commands-txt-strings; 201 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-make-doom-for-mips-43aa2a6f` | Terminus2 | false | 177 | source-valid | terminus2-commands-txt-strings; 177 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-make-mips-interpreter-b36e6a0a` | Terminus2 | false | 149 | source-valid | terminus2-commands-txt-strings; 149 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-mcmc-sampling-stan-db249f0b` | Terminus2 | false | 81 | excluded | terminus2-commands-txt-strings emitted 78 operations; public step_count is 81 |
| `terminus2-DeepSeek__DeepSeek-V3.2-merge-diff-arc-agi-task-5c78cf22` | Terminus2 | true | 45 | source-valid | terminus2-commands-txt-strings; 45 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-mixed-integer-programming-0294aabb` | Terminus2 | true | 43 | source-valid | terminus2-commands-txt-strings; 43 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-mlflow-register-14b18ee0` | Terminus2 | true | 42 | source-valid | terminus2-commands-txt-strings; 42 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-model-extraction-relu-logits-e2e85d60` | Terminus2 | false | 26 | source-valid | terminus2-commands-txt-strings; 26 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-modernize-fortran-build-f05d8fb6` | Terminus2 | true | 27 | source-valid | terminus2-commands-txt-strings; 27 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-modernize-scientific-stack-b58929f7` | Terminus2 | true | 25 | source-valid | terminus2-commands-txt-strings; 25 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-movie-helper-111f0d1e` | Terminus2 | false | 24 | source-valid | terminus2-commands-txt-strings; 24 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-mteb-eval-e1515008` | Terminus2 | true | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-mteb-leaderboard-6de890d1` | Terminus2 | false | 168 | excluded | Terminus2 archive has no commands.txt |
| `terminus2-DeepSeek__DeepSeek-V3.2-mteb-retrieve-48d3ce0c` | Terminus2 | missing | 36 | source-valid | terminus2-commands-txt-strings; 36 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-multi-source-data-merger-5ac42476` | Terminus2 | missing | 23 | source-valid | terminus2-commands-txt-strings; 23 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-multistep-definite-integral-29178d22` | Terminus2 | true | 26 | source-valid | terminus2-commands-txt-strings; 26 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-neuron-to-jaxley-conversion-7e70f59f` | Terminus2 | false | 95 | source-valid | terminus2-commands-txt-strings; 95 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-new-encrypt-command-1cb37cb6` | Terminus2 | true | 35 | source-valid | terminus2-commands-txt-strings; 35 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-nginx-request-logging-a9eb00db` | Terminus2 | true | 41 | source-valid | terminus2-commands-txt-strings; 41 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-npm-conflict-resolution-d780cb31` | Terminus2 | true | 63 | source-valid | terminus2-commands-txt-strings; 63 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-ode-solver-rk4-033634f2` | Terminus2 | true | 28 | source-valid | terminus2-commands-txt-strings; 28 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-oom-8607cdc9` | Terminus2 | false | 32 | source-valid | terminus2-commands-txt-strings; 32 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-openssl-selfsigned-cert-9312d845` | Terminus2 | true | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-optimal-transport-48c68c2d` | Terminus2 | false | 60 | source-valid | terminus2-commands-txt-strings; 60 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-organization-json-generator-30fb23d8` | Terminus2 | false | 20 | source-valid | terminus2-commands-txt-strings; 20 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-overfull-hbox-c11dbef0` | Terminus2 | false | 191 | source-valid | terminus2-commands-txt-strings; 191 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-pandas-etl-50d8969f` | Terminus2 | true | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-pandas-sql-query-8088d1d7` | Terminus2 | true | 13 | source-valid | terminus2-commands-txt-strings; 13 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-parallel-particle-simulator-5438faec` | Terminus2 | false | 168 | source-valid | terminus2-commands-txt-strings; 168 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-parallelize-compute-squares-fb90f58e` | Terminus2 | true | 79 | source-valid | terminus2-commands-txt-strings; 79 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-parallelize-graph-ed247a15` | Terminus2 | false | 152 | source-valid | terminus2-commands-txt-strings; 152 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-password-recovery-cbec8a16` | Terminus2 | true | 158 | source-valid | terminus2-commands-txt-strings; 158 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-path-tracing-661f78e5` | Terminus2 | false | 86 | source-valid | terminus2-commands-txt-strings; 86 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-path-tracing-reverse-56141d64` | Terminus2 | false | 118 | source-valid | terminus2-commands-txt-strings; 118 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-pcap-to-netflow-36c619e9` | Terminus2 | false | 54 | source-valid | terminus2-commands-txt-strings; 54 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-play-zork-822e54b8` | Terminus2 | false | 568 | source-valid | terminus2-commands-txt-strings; 568 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-play-zork-easy-537bae18` | Terminus2 | false | 290 | excluded | terminus2-commands-txt-strings emitted 287 operations; public step_count is 290 |
| `terminus2-DeepSeek__DeepSeek-V3.2-png-generation-2d05e83f` | Terminus2 | missing | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-polyglot-c-py-79de5b2b` | Terminus2 | false | 46 | source-valid | terminus2-commands-txt-strings; 46 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-polyglot-rust-c-9477650d` | Terminus2 | false | 136 | source-valid | terminus2-commands-txt-strings; 136 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-port-compressor-bebcee08` | Terminus2 | missing | 85 | source-valid | terminus2-commands-txt-strings; 85 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-portfolio-optimization-50bb4503` | Terminus2 | missing | 31 | source-valid | terminus2-commands-txt-strings; 31 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-predicate-pushdown-bench-0225294a` | Terminus2 | missing | 63 | source-valid | terminus2-commands-txt-strings; 63 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-predict-customer-churn-11dfe933` | Terminus2 | true | 27 | source-valid | terminus2-commands-txt-strings; 27 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-processing-pipeline-c08102fa` | Terminus2 | true | 36 | source-valid | terminus2-commands-txt-strings; 36 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-protein-assembly-b1adf132` | Terminus2 | false | 73 | source-valid | terminus2-commands-txt-strings; 73 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-protocol-analysis-rs-f24dfce5` | Terminus2 | false | 229 | source-valid | terminus2-commands-txt-strings; 229 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-prove-plus-comm-f2c374dd` | Terminus2 | true | 13 | source-valid | terminus2-commands-txt-strings; 13 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-puzzle-solver-4d1d76be` | Terminus2 | missing | 32 | source-valid | terminus2-commands-txt-strings; 32 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-pypi-server-d98b6803` | Terminus2 | true | 44 | source-valid | terminus2-commands-txt-strings; 44 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-pytorch-model-cli-3c4c751f` | Terminus2 | false | 42 | source-valid | terminus2-commands-txt-strings; 42 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-pytorch-model-recovery-d2e66795` | Terminus2 | missing | 54 | source-valid | terminus2-commands-txt-strings; 54 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-qemu-startup-979bf626` | Terminus2 | true | 40 | source-valid | terminus2-commands-txt-strings; 40 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-query-optimize-f6c63ff2` | Terminus2 | false | 94 | source-valid | terminus2-commands-txt-strings; 94 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-raman-fitting-9552f6c3` | Terminus2 | false | 41 | source-valid | terminus2-commands-txt-strings; 41 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-rare-mineral-allocation-fa8951d0` | Terminus2 | false | 59 | source-valid | terminus2-commands-txt-strings; 59 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-recover-accuracy-log-a302beb5` | Terminus2 | true | 34 | source-valid | terminus2-commands-txt-strings; 34 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-recover-obfuscated-files-6b617f21` | Terminus2 | true | 21 | source-valid | terminus2-commands-txt-strings; 21 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-regex-chess-bffde5d9` | Terminus2 | false | 60 | source-valid | terminus2-commands-txt-strings; 60 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-regex-log-92110854` | Terminus2 | true | 29 | source-valid | terminus2-commands-txt-strings; 29 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-reshard-c4-data-7124880c` | Terminus2 | missing | 126 | source-valid | terminus2-commands-txt-strings; 126 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-reverse-engineering-4a16ea4f` | Terminus2 | true | 54 | source-valid | terminus2-commands-txt-strings; 54 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-rstan-to-pystan-394402f8` | Terminus2 | false | 130 | source-valid | terminus2-commands-txt-strings; 130 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-run-pdp11-code-413e993c` | Terminus2 | false | 164 | source-valid | terminus2-commands-txt-strings; 164 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-sam-cell-seg-bd8110d9` | Terminus2 | missing | 103 | source-valid | terminus2-commands-txt-strings; 103 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-schedule-vacation-ea3a1cd1` | Terminus2 | true | 23 | source-valid | terminus2-commands-txt-strings; 23 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-schemelike-metacircular-eval-507c4cf9` | Terminus2 | missing | 93 | source-valid | terminus2-commands-txt-strings; 93 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-security-vulhub-minio-cd6f0d36` | Terminus2 | false | 124 | source-valid | terminus2-commands-txt-strings; 124 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-setup-custom-dev-env-a9aa1e2d` | Terminus2 | true | 59 | source-valid | terminus2-commands-txt-strings; 59 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-simple-sheets-put-71b52390` | Terminus2 | false | 112 | source-valid | terminus2-commands-txt-strings; 112 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-solana-data-a4e29809` | Terminus2 | false | 154 | source-valid | terminus2-commands-txt-strings; 154 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-solve-maze-challenge-8395a2f7` | Terminus2 | false | 52 | source-valid | terminus2-commands-txt-strings; 52 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-solve-sudoku-31c3f7eb` | Terminus2 | false | 26 | source-valid | terminus2-commands-txt-strings; 26 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-sparql-professors-universities-277310e8` | Terminus2 | true | 23 | source-valid | terminus2-commands-txt-strings; 23 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-sparql-university-13e05e62` | Terminus2 | false | 37 | source-valid | terminus2-commands-txt-strings; 37 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-speech-to-text-076d8b58` | Terminus2 | missing | 193 | excluded | terminus2-commands-txt-strings emitted 192 operations; public step_count is 193 |
| `terminus2-DeepSeek__DeepSeek-V3.2-spinning-up-rl-e724511e` | Terminus2 | false | 172 | source-valid | terminus2-commands-txt-strings; 172 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-spring-messaging-vul-9e01530d` | Terminus2 | false | 187 | source-valid | terminus2-commands-txt-strings; 187 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-sql-injection-attack-e049afe0` | Terminus2 | missing | 50 | source-valid | terminus2-commands-txt-strings; 50 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-sqlite-db-truncate-58823d99` | Terminus2 | true | 48 | source-valid | terminus2-commands-txt-strings; 48 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-sqlite-with-gcov-89bbd942` | Terminus2 | true | 37 | source-valid | terminus2-commands-txt-strings; 37 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-stable-parallel-kmeans-7b991b9f` | Terminus2 | true | 51 | source-valid | terminus2-commands-txt-strings; 51 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-sudo-llvm-ir-685c1670` | Terminus2 | false | 145 | source-valid | terminus2-commands-txt-strings; 145 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-swe-bench-astropy-1-1ded46fd` | Terminus2 | missing | 111 | source-valid | terminus2-commands-txt-strings; 111 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-swe-bench-astropy-2-6f0aa073` | Terminus2 | false | 257 | source-valid | terminus2-commands-txt-strings; 257 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-swe-bench-fsspec-5836db00` | Terminus2 | false | 67 | source-valid | terminus2-commands-txt-strings; 67 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-swe-bench-langcodes-7cf57135` | Terminus2 | true | 36 | source-valid | terminus2-commands-txt-strings; 36 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-tmux-advanced-workflow-7fd8b1fa` | Terminus2 | true | 146 | source-valid | terminus2-commands-txt-strings; 146 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-torch-pipeline-parallelism-d9d96435` | Terminus2 | missing | 20 | source-valid | terminus2-commands-txt-strings; 20 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-torch-tensor-parallelism-fb2bf6f8` | Terminus2 | missing | 41 | source-valid | terminus2-commands-txt-strings; 41 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-train-bpe-tokenizer-40d660d2` | Terminus2 | false | 52 | source-valid | terminus2-commands-txt-strings; 52 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-train-fasttext-23c944b2` | Terminus2 | missing | 160 | excluded | terminus2-commands-txt-strings emitted 159 operations; public step_count is 160 |
| `terminus2-DeepSeek__DeepSeek-V3.2-tree-directory-parser-6fa54378` | Terminus2 | true | 62 | source-valid | terminus2-commands-txt-strings; 62 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-triton-interpret-41df7471` | Terminus2 | missing | 60 | source-valid | terminus2-commands-txt-strings; 60 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-tune-mjcf-e2090cff` | Terminus2 | true | 84 | source-valid | terminus2-commands-txt-strings; 84 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-vertex-solver-bb48bd68` | Terminus2 | false | 98 | source-valid | terminus2-commands-txt-strings; 98 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-video-processing-b276bcd2` | Terminus2 | missing | 44 | source-valid | terminus2-commands-txt-strings; 44 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-vimscript-vim-quine-445eba2c` | Terminus2 | false | 183 | source-valid | terminus2-commands-txt-strings; 183 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-vul-flask-024c7749` | Terminus2 | false | 110 | source-valid | terminus2-commands-txt-strings; 110 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-vul-flink-b2aed5a1` | Terminus2 | false | 48 | source-valid | terminus2-commands-txt-strings; 48 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-vulnerable-secret-6651c0dd` | Terminus2 | true | 22 | source-valid | terminus2-commands-txt-strings; 22 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-wasm-pipeline-0d31d36b` | Terminus2 | true | 111 | source-valid | terminus2-commands-txt-strings; 111 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-weighted-max-sat-solver-5f6e2475` | Terminus2 | false | 115 | source-valid | terminus2-commands-txt-strings; 115 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-winning-avg-corewars-092b4dd9` | Terminus2 | missing | 105 | source-valid | terminus2-commands-txt-strings; 105 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-word2vec-from-scratch-bfc40501` | Terminus2 | false | 42 | source-valid | terminus2-commands-txt-strings; 42 operations |
| `terminus2-DeepSeek__DeepSeek-V3.2-write-compressor-267a69ea` | Terminus2 | false | 15 | source-valid | terminus2-commands-txt-strings; 15 operations |
| `terminus2-Moonshot__Kimi-K2-250905-3d-model-format-legacy-c62ad45d` | Terminus2 | false | 151 | excluded | terminus2-commands-txt-strings emitted 150 operations; public step_count is 151 |
| `terminus2-Moonshot__Kimi-K2-250905-accelerate-maximal-square-dd6b65b8` | Terminus2 | false | 40 | source-valid | terminus2-commands-txt-strings; 40 operations |
| `terminus2-Moonshot__Kimi-K2-250905-acl-permissions-inheritance-fb9896e9` | Terminus2 | false | 15 | source-valid | terminus2-commands-txt-strings; 15 operations |
| `terminus2-Moonshot__Kimi-K2-250905-adaptive-rejection-sampler-6e0886a2` | Terminus2 | false | 51 | source-valid | terminus2-commands-txt-strings; 51 operations |
| `terminus2-Moonshot__Kimi-K2-250905-add-benchmark-lm-eval-harness-bf21da27` | Terminus2 | missing | 99 | source-valid | terminus2-commands-txt-strings; 99 operations |
| `terminus2-Moonshot__Kimi-K2-250905-amuse-install-0cbf4317` | Terminus2 | true | 77 | source-valid | terminus2-commands-txt-strings; 77 operations |
| `terminus2-Moonshot__Kimi-K2-250905-assign-seats-49bd5d69` | Terminus2 | true | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-Moonshot__Kimi-K2-250905-attention-mil-f4bf2a81` | Terminus2 | false | 13 | source-valid | terminus2-commands-txt-strings; 13 operations |
| `terminus2-Moonshot__Kimi-K2-250905-audio-synth-stft-peaks-a5e7b2e0` | Terminus2 | false | 39 | source-valid | terminus2-commands-txt-strings; 39 operations |
| `terminus2-Moonshot__Kimi-K2-250905-blind-maze-explorer-5x5-bbb3c3ab` | Terminus2 | false | 200 | source-valid | terminus2-commands-txt-strings; 200 operations |
| `terminus2-Moonshot__Kimi-K2-250905-blind-maze-explorer-algorithm-5b6c31d4` | Terminus2 | false | 62 | source-valid | terminus2-commands-txt-strings; 62 operations |
| `terminus2-Moonshot__Kimi-K2-250905-bn-fit-modify-0cadd3b8` | Terminus2 | false | 50 | source-valid | terminus2-commands-txt-strings; 50 operations |
| `terminus2-Moonshot__Kimi-K2-250905-break-filter-js-from-html-5f7ce491` | Terminus2 | false | 212 | source-valid | terminus2-commands-txt-strings; 212 operations |
| `terminus2-Moonshot__Kimi-K2-250905-broken-networking-a1a8bf4e` | Terminus2 | missing | 60 | source-valid | terminus2-commands-txt-strings; 60 operations |
| `terminus2-Moonshot__Kimi-K2-250905-broken-python-05bc4f76` | Terminus2 | true | 42 | source-valid | terminus2-commands-txt-strings; 42 operations |
| `terminus2-Moonshot__Kimi-K2-250905-build-initramfs-qemu-0876bbad` | Terminus2 | missing | 52 | source-valid | terminus2-commands-txt-strings; 52 operations |
| `terminus2-Moonshot__Kimi-K2-250905-build-linux-kernel-qemu-39190522` | Terminus2 | false | 72 | source-valid | terminus2-commands-txt-strings; 72 operations |
| `terminus2-Moonshot__Kimi-K2-250905-build-pmars-0a98b2dd` | Terminus2 | true | 50 | source-valid | terminus2-commands-txt-strings; 50 operations |
| `terminus2-Moonshot__Kimi-K2-250905-build-pov-ray-c1a15901` | Terminus2 | false | 39 | source-valid | terminus2-commands-txt-strings; 39 operations |
| `terminus2-Moonshot__Kimi-K2-250905-build-stp-fe0060d5` | Terminus2 | true | 42 | excluded | terminus2-commands-txt-strings emitted 43 operations; public step_count is 42 |
| `terminus2-Moonshot__Kimi-K2-250905-build-tcc-qemu-eedb659d` | Terminus2 | false | 31 | source-valid | terminus2-commands-txt-strings; 31 operations |
| `terminus2-Moonshot__Kimi-K2-250905-caffe-cifar-10-367151bb` | Terminus2 | false | 105 | source-valid | terminus2-commands-txt-strings; 105 operations |
| `terminus2-Moonshot__Kimi-K2-250905-cartpole-rl-training-79872c0a` | Terminus2 | missing | 59 | source-valid | terminus2-commands-txt-strings; 59 operations |
| `terminus2-Moonshot__Kimi-K2-250905-catch-me-if-you-can-6afb040c` | Terminus2 | false | 115 | source-valid | terminus2-commands-txt-strings; 115 operations |
| `terminus2-Moonshot__Kimi-K2-250905-chem-property-targeting-d56fd9ec` | Terminus2 | false | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-Moonshot__Kimi-K2-250905-chem-rf-fc47fca4` | Terminus2 | false | 70 | source-valid | terminus2-commands-txt-strings; 70 operations |
| `terminus2-Moonshot__Kimi-K2-250905-chess-best-move-6930a50b` | Terminus2 | false | 47 | source-valid | terminus2-commands-txt-strings; 47 operations |
| `terminus2-Moonshot__Kimi-K2-250905-circuit-fibsqrt-8b9ce751` | Terminus2 | false | 46 | source-valid | terminus2-commands-txt-strings; 46 operations |
| `terminus2-Moonshot__Kimi-K2-250905-classifier-debug-61623948` | Terminus2 | true | 52 | excluded | terminus2-commands-txt-strings emitted 53 operations; public step_count is 52 |
| `terminus2-Moonshot__Kimi-K2-250905-cobol-modernization-6f9e5d88` | Terminus2 | true | 66 | source-valid | terminus2-commands-txt-strings; 66 operations |
| `terminus2-Moonshot__Kimi-K2-250905-code-from-image-0aeb4622` | Terminus2 | true | 37 | excluded | terminus2-commands-txt-strings emitted 38 operations; public step_count is 37 |
| `terminus2-Moonshot__Kimi-K2-250905-compile-compcert-c2b5a336` | Terminus2 | missing | 161 | source-valid | terminus2-commands-txt-strings; 161 operations |
| `terminus2-Moonshot__Kimi-K2-250905-conda-env-conflict-resolution-54e78499` | Terminus2 | false | 88 | source-valid | terminus2-commands-txt-strings; 88 operations |
| `terminus2-Moonshot__Kimi-K2-250905-configure-git-webserver-6b3af8be` | Terminus2 | true | 65 | source-valid | terminus2-commands-txt-strings; 65 operations |
| `terminus2-Moonshot__Kimi-K2-250905-count-call-stack-2ca7d6be` | Terminus2 | false | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-Moonshot__Kimi-K2-250905-crack-7z-hash-e369888d` | Terminus2 | true | 86 | source-valid | terminus2-commands-txt-strings; 86 operations |
| `terminus2-Moonshot__Kimi-K2-250905-create-bucket-3557ce9a` | Terminus2 | true | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-Moonshot__Kimi-K2-250905-cron-broken-network-b148498d` | Terminus2 | missing | 69 | source-valid | terminus2-commands-txt-strings; 69 operations |
| `terminus2-Moonshot__Kimi-K2-250905-cross-entropy-method-81bcda77` | Terminus2 | true | 99 | excluded | terminus2-commands-txt-strings emitted 100 operations; public step_count is 99 |
| `terminus2-Moonshot__Kimi-K2-250905-csv-to-parquet-00d6e92e` | Terminus2 | true | 22 | source-valid | terminus2-commands-txt-strings; 22 operations |
| `terminus2-Moonshot__Kimi-K2-250905-db-wal-recovery-34a3ab74` | Terminus2 | false | 30 | source-valid | terminus2-commands-txt-strings; 30 operations |
| `terminus2-Moonshot__Kimi-K2-250905-decommissioning-service-with-sensitive-data-3fc7fe0e` | Terminus2 | true | 24 | source-valid | terminus2-commands-txt-strings; 24 operations |
| `terminus2-Moonshot__Kimi-K2-250905-deterministic-tarball-3b6179ea` | Terminus2 | false | 44 | source-valid | terminus2-commands-txt-strings; 44 operations |
| `terminus2-Moonshot__Kimi-K2-250905-distribution-search-1a5ef560` | Terminus2 | false | 27 | source-valid | terminus2-commands-txt-strings; 27 operations |
| `terminus2-Moonshot__Kimi-K2-250905-dna-assembly-9110ce04` | Terminus2 | false | 28 | source-valid | terminus2-commands-txt-strings; 28 operations |
| `terminus2-Moonshot__Kimi-K2-250905-dna-insert-0751f813` | Terminus2 | false | 46 | excluded | terminus2-commands-txt-strings emitted 47 operations; public step_count is 46 |
| `terminus2-Moonshot__Kimi-K2-250905-download-youtube-cabab87d` | Terminus2 | false | 19 | source-valid | terminus2-commands-txt-strings; 19 operations |
| `terminus2-Moonshot__Kimi-K2-250905-enemy-grid-escape-6d798aa2` | Terminus2 | false | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-Moonshot__Kimi-K2-250905-extract-elf-da69e120` | Terminus2 | false | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-Moonshot__Kimi-K2-250905-extract-moves-from-video-48479971` | Terminus2 | false | 26 | source-valid | terminus2-commands-txt-strings; 26 operations |
| `terminus2-Moonshot__Kimi-K2-250905-feal-differential-cryptanalysis-6e1db4e5` | Terminus2 | false | 55 | excluded | terminus2-commands-txt-strings emitted 54 operations; public step_count is 55 |
| `terminus2-Moonshot__Kimi-K2-250905-feal-linear-cryptanalysis-684a0b99` | Terminus2 | false | 23 | source-valid | terminus2-commands-txt-strings; 23 operations |
| `terminus2-Moonshot__Kimi-K2-250905-fibonacci-server-971e58f0` | Terminus2 | true | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-Moonshot__Kimi-K2-250905-financial-document-processor-cf73d5d3` | Terminus2 | false | 44 | source-valid | terminus2-commands-txt-strings; 44 operations |
| `terminus2-Moonshot__Kimi-K2-250905-find-official-code-ccb74ed5` | Terminus2 | false | 23 | excluded | terminus2-commands-txt-strings emitted 24 operations; public step_count is 23 |
| `terminus2-Moonshot__Kimi-K2-250905-fix-code-vulnerability-f097e6e0` | Terminus2 | false | 33 | excluded | Terminus2 archive has no commands.txt |
| `terminus2-Moonshot__Kimi-K2-250905-fix-git-5fd52eea` | Terminus2 | true | 20 | source-valid | terminus2-commands-txt-strings; 20 operations |
| `terminus2-Moonshot__Kimi-K2-250905-fix-ocaml-gc-8e2d8321` | Terminus2 | false | 69 | source-valid | terminus2-commands-txt-strings; 69 operations |
| `terminus2-Moonshot__Kimi-K2-250905-fix-pandas-version-7b5df2c2` | Terminus2 | true | 52 | source-valid | terminus2-commands-txt-strings; 52 operations |
| `terminus2-Moonshot__Kimi-K2-250905-flood-monitoring-basic-74b7c427` | Terminus2 | false | 23 | source-valid | terminus2-commands-txt-strings; 23 operations |
| `terminus2-Moonshot__Kimi-K2-250905-fmri-encoding-r-cdb7131f` | Terminus2 | false | 74 | source-valid | terminus2-commands-txt-strings; 74 operations |
| `terminus2-Moonshot__Kimi-K2-250905-form-filling-2d5188b1` | Terminus2 | false | 40 | excluded | terminus2-commands-txt-strings emitted 41 operations; public step_count is 40 |
| `terminus2-Moonshot__Kimi-K2-250905-gcc-compiler-optimization-ac6901e3` | Terminus2 | true | 19 | source-valid | terminus2-commands-txt-strings; 19 operations |
| `terminus2-Moonshot__Kimi-K2-250905-gcode-to-text-01b949d0` | Terminus2 | false | 20 | excluded | terminus2-commands-txt-strings emitted 21 operations; public step_count is 20 |
| `terminus2-Moonshot__Kimi-K2-250905-get-bitcoin-nodes-725467e5` | Terminus2 | false | 31 | source-valid | terminus2-commands-txt-strings; 31 operations |
| `terminus2-Moonshot__Kimi-K2-250905-git-leak-recovery-63a2a6ec` | Terminus2 | true | 19 | source-valid | terminus2-commands-txt-strings; 19 operations |
| `terminus2-Moonshot__Kimi-K2-250905-git-multibranch-28cc8513` | Terminus2 | false | 66 | source-valid | terminus2-commands-txt-strings; 66 operations |
| `terminus2-Moonshot__Kimi-K2-250905-git-workflow-hack-25af4246` | Terminus2 | true | 15 | source-valid | terminus2-commands-txt-strings; 15 operations |
| `terminus2-Moonshot__Kimi-K2-250905-gpt2-codegolf-bed0db0f` | Terminus2 | false | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-Moonshot__Kimi-K2-250905-hdfs-deployment-cba42afc` | Terminus2 | true | 52 | source-valid | terminus2-commands-txt-strings; 52 operations |
| `terminus2-Moonshot__Kimi-K2-250905-heterogeneous-dates-191a45e9` | Terminus2 | true | 12 | source-valid | terminus2-commands-txt-strings; 12 operations |
| `terminus2-Moonshot__Kimi-K2-250905-hf-lora-adapter-1dd68f18` | Terminus2 | true | 23 | source-valid | terminus2-commands-txt-strings; 23 operations |
| `terminus2-Moonshot__Kimi-K2-250905-hf-model-inference-94d10ab7` | Terminus2 | false | 42 | source-valid | terminus2-commands-txt-strings; 42 operations |
| `terminus2-Moonshot__Kimi-K2-250905-hf-train-lora-adapter-685faf4d` | Terminus2 | false | 59 | excluded | terminus2-commands-txt-strings emitted 8 operations; public step_count is 59 |
| `terminus2-Moonshot__Kimi-K2-250905-html-finance-verify-d3ae4d12` | Terminus2 | false | 62 | source-valid | terminus2-commands-txt-strings; 62 operations |
| `terminus2-Moonshot__Kimi-K2-250905-huarong-dao-solver-f1ef0729` | Terminus2 | false | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-Moonshot__Kimi-K2-250905-hydra-debug-slurm-mode-497e70ea` | Terminus2 | false | 37 | source-valid | terminus2-commands-txt-strings; 37 operations |
| `terminus2-Moonshot__Kimi-K2-250905-implement-eigenvectors-from-eigenvalues-research-paper-99d757c1` | Terminus2 | missing | 58 | excluded | terminus2-commands-txt-strings emitted 59 operations; public step_count is 58 |
| `terminus2-Moonshot__Kimi-K2-250905-incompatible-python-fasttext-bbc70e16` | Terminus2 | true | 19 | source-valid | terminus2-commands-txt-strings; 19 operations |
| `terminus2-Moonshot__Kimi-K2-250905-install-klee-minimal-5b6493fb` | Terminus2 | true | 160 | excluded | terminus2-commands-txt-strings emitted 163 operations; public step_count is 160 |
| `terminus2-Moonshot__Kimi-K2-250905-install-windows-3.11-ff50da45` | Terminus2 | false | 31 | source-valid | terminus2-commands-txt-strings; 31 operations |
| `terminus2-Moonshot__Kimi-K2-250905-install-windows-xp-cdc225aa` | Terminus2 | false | 28 | source-valid | terminus2-commands-txt-strings; 28 operations |
| `terminus2-Moonshot__Kimi-K2-250905-intrusion-detection-8011682f` | Terminus2 | false | 34 | excluded | terminus2-commands-txt-strings emitted 35 operations; public step_count is 34 |
| `terminus2-Moonshot__Kimi-K2-250905-jq-data-processing-7724b9fb` | Terminus2 | true | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-Moonshot__Kimi-K2-250905-jupyter-notebook-server-5678781d` | Terminus2 | false | 76 | source-valid | terminus2-commands-txt-strings; 76 operations |
| `terminus2-Moonshot__Kimi-K2-250905-kv-store-grpc-6bdedb1d` | Terminus2 | true | 23 | source-valid | terminus2-commands-txt-strings; 23 operations |
| `terminus2-Moonshot__Kimi-K2-250905-large-scale-text-editing-9252da70` | Terminus2 | false | 58 | excluded | terminus2-commands-txt-strings emitted 59 operations; public step_count is 58 |
| `terminus2-Moonshot__Kimi-K2-250905-largest-eigenval-36880c30` | Terminus2 | true | 49 | source-valid | terminus2-commands-txt-strings; 49 operations |
| `terminus2-Moonshot__Kimi-K2-250905-lean4-proof-e3d03875` | Terminus2 | false | 118 | source-valid | terminus2-commands-txt-strings; 118 operations |
| `terminus2-Moonshot__Kimi-K2-250905-leelachess0-pytorch-conversion-03450562` | Terminus2 | missing | 26 | excluded | terminus2-commands-txt-strings emitted 27 operations; public step_count is 26 |
| `terminus2-Moonshot__Kimi-K2-250905-llm-inference-batching-scheduler-efc7e497` | Terminus2 | false | 56 | source-valid | terminus2-commands-txt-strings; 56 operations |
| `terminus2-Moonshot__Kimi-K2-250905-llm-spec-decoding-9cf51534` | Terminus2 | missing | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-Moonshot__Kimi-K2-250905-log-summary-date-ranges-5b2ed268` | Terminus2 | true | 15 | excluded | terminus2-commands-txt-strings emitted 16 operations; public step_count is 15 |
| `terminus2-Moonshot__Kimi-K2-250905-logistic-regression-divergence-894ef7a3` | Terminus2 | false | 59 | excluded | terminus2-commands-txt-strings emitted 60 operations; public step_count is 59 |
| `terminus2-Moonshot__Kimi-K2-250905-magsac-install-e06a86d0` | Terminus2 | false | 151 | source-valid | terminus2-commands-txt-strings; 151 operations |
| `terminus2-Moonshot__Kimi-K2-250905-mailman-1741bfa2` | Terminus2 | true | 90 | excluded | terminus2-commands-txt-strings emitted 91 operations; public step_count is 90 |
| `terminus2-Moonshot__Kimi-K2-250905-make-doom-for-mips-40679baa` | Terminus2 | false | 95 | source-valid | terminus2-commands-txt-strings; 95 operations |
| `terminus2-Moonshot__Kimi-K2-250905-make-mips-interpreter-81dcd438` | Terminus2 | false | 84 | excluded | terminus2-commands-txt-strings emitted 83 operations; public step_count is 84 |
| `terminus2-Moonshot__Kimi-K2-250905-mcmc-sampling-stan-9a92b09c` | Terminus2 | false | 50 | source-valid | terminus2-commands-txt-strings; 50 operations |
| `terminus2-Moonshot__Kimi-K2-250905-merge-diff-arc-agi-task-3165089f` | Terminus2 | false | 59 | source-valid | terminus2-commands-txt-strings; 59 operations |
| `terminus2-Moonshot__Kimi-K2-250905-mixed-integer-programming-9520f07c` | Terminus2 | true | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-Moonshot__Kimi-K2-250905-modernize-fortran-build-251ed765` | Terminus2 | true | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-Moonshot__Kimi-K2-250905-modernize-scientific-stack-8ee67756` | Terminus2 | true | 12 | source-valid | terminus2-commands-txt-strings; 12 operations |
| `terminus2-Moonshot__Kimi-K2-250905-movie-helper-d8bc947f` | Terminus2 | false | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-Moonshot__Kimi-K2-250905-mteb-eval-409fba19` | Terminus2 | true | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-Moonshot__Kimi-K2-250905-mteb-leaderboard-d2a45eac` | Terminus2 | false | 12 | source-valid | terminus2-commands-txt-strings; 12 operations |
| `terminus2-Moonshot__Kimi-K2-250905-multi-source-data-merger-68ab53f7` | Terminus2 | true | 21 | source-valid | terminus2-commands-txt-strings; 21 operations |
| `terminus2-Moonshot__Kimi-K2-250905-neuron-to-jaxley-conversion-781cf24e` | Terminus2 | true | 141 | source-valid | terminus2-commands-txt-strings; 141 operations |
| `terminus2-Moonshot__Kimi-K2-250905-new-encrypt-command-84a7bcf4` | Terminus2 | true | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-Moonshot__Kimi-K2-250905-npm-conflict-resolution-6de89771` | Terminus2 | false | 57 | source-valid | terminus2-commands-txt-strings; 57 operations |
| `terminus2-Moonshot__Kimi-K2-250905-oom-bdec488e` | Terminus2 | false | 28 | source-valid | terminus2-commands-txt-strings; 28 operations |
| `terminus2-Moonshot__Kimi-K2-250905-openssl-selfsigned-cert-f9ae5f6e` | Terminus2 | true | 23 | source-valid | terminus2-commands-txt-strings; 23 operations |
| `terminus2-Moonshot__Kimi-K2-250905-optimal-transport-db1b0b14` | Terminus2 | false | 20 | source-valid | terminus2-commands-txt-strings; 20 operations |
| `terminus2-Moonshot__Kimi-K2-250905-organization-json-generator-8aa93097` | Terminus2 | false | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-Moonshot__Kimi-K2-250905-overfull-hbox-8846a0d0` | Terminus2 | false | 54 | excluded | terminus2-commands-txt-strings emitted 55 operations; public step_count is 54 |
| `terminus2-Moonshot__Kimi-K2-250905-pandas-sql-query-d22c1370` | Terminus2 | true | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-Moonshot__Kimi-K2-250905-parallel-particle-simulator-1523584c` | Terminus2 | false | 97 | source-valid | terminus2-commands-txt-strings; 97 operations |
| `terminus2-Moonshot__Kimi-K2-250905-parallelize-compute-squares-6179f24a` | Terminus2 | true | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-Moonshot__Kimi-K2-250905-parallelize-graph-18c98a82` | Terminus2 | false | 67 | source-valid | terminus2-commands-txt-strings; 67 operations |
| `terminus2-Moonshot__Kimi-K2-250905-password-recovery-a2c66893` | Terminus2 | false | 63 | source-valid | terminus2-commands-txt-strings; 63 operations |
| `terminus2-Moonshot__Kimi-K2-250905-path-tracing-5942eae3` | Terminus2 | false | 88 | excluded | terminus2-commands-txt-strings emitted 87 operations; public step_count is 88 |
| `terminus2-Moonshot__Kimi-K2-250905-path-tracing-reverse-f78cf38e` | Terminus2 | false | 38 | source-valid | terminus2-commands-txt-strings; 38 operations |
| `terminus2-Moonshot__Kimi-K2-250905-pcap-to-netflow-b28f0938` | Terminus2 | false | 41 | excluded | terminus2-commands-txt-strings emitted 42 operations; public step_count is 41 |
| `terminus2-Moonshot__Kimi-K2-250905-play-zork-644b5500` | Terminus2 | false | 413 | source-valid | terminus2-commands-txt-strings; 413 operations |
| `terminus2-Moonshot__Kimi-K2-250905-play-zork-easy-358053ca` | Terminus2 | false | 200 | source-valid | terminus2-commands-txt-strings; 200 operations |
| `terminus2-Moonshot__Kimi-K2-250905-polyglot-c-py-9c93ff32` | Terminus2 | false | 158 | excluded | terminus2-commands-txt-strings emitted 157 operations; public step_count is 158 |
| `terminus2-Moonshot__Kimi-K2-250905-polyglot-rust-c-aa8e370f` | Terminus2 | false | 58 | source-valid | terminus2-commands-txt-strings; 58 operations |
| `terminus2-Moonshot__Kimi-K2-250905-port-compressor-31ab9ffb` | Terminus2 | false | 200 | source-valid | terminus2-commands-txt-strings; 200 operations |
| `terminus2-Moonshot__Kimi-K2-250905-portfolio-optimization-1765fd2a` | Terminus2 | true | 15 | source-valid | terminus2-commands-txt-strings; 15 operations |
| `terminus2-Moonshot__Kimi-K2-250905-predicate-pushdown-bench-2aa9facf` | Terminus2 | true | 49 | source-valid | terminus2-commands-txt-strings; 49 operations |
| `terminus2-Moonshot__Kimi-K2-250905-predict-customer-churn-44d2e24c` | Terminus2 | true | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-Moonshot__Kimi-K2-250905-processing-pipeline-31bd85aa` | Terminus2 | true | 22 | source-valid | terminus2-commands-txt-strings; 22 operations |
| `terminus2-Moonshot__Kimi-K2-250905-protein-assembly-7e2e1d91` | Terminus2 | false | 36 | source-valid | terminus2-commands-txt-strings; 36 operations |
| `terminus2-Moonshot__Kimi-K2-250905-protocol-analysis-rs-01b7db71` | Terminus2 | false | 406 | excluded | terminus2-commands-txt-strings emitted 393 operations; public step_count is 406 |
| `terminus2-Moonshot__Kimi-K2-250905-puzzle-solver-cf28c22d` | Terminus2 | false | 19 | source-valid | terminus2-commands-txt-strings; 19 operations |
| `terminus2-Moonshot__Kimi-K2-250905-pypi-server-e6e9af37` | Terminus2 | true | 59 | source-valid | terminus2-commands-txt-strings; 59 operations |
| `terminus2-Moonshot__Kimi-K2-250905-pytorch-model-cli-f1a67c3b` | Terminus2 | missing | 74 | source-valid | terminus2-commands-txt-strings; 74 operations |
| `terminus2-Moonshot__Kimi-K2-250905-pytorch-model-recovery-407d9a23` | Terminus2 | missing | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-Moonshot__Kimi-K2-250905-qemu-alpine-ssh-66675c46` | Terminus2 | false | 197 | excluded | terminus2-commands-txt-strings emitted 196 operations; public step_count is 197 |
| `terminus2-Moonshot__Kimi-K2-250905-qemu-startup-ab8e3734` | Terminus2 | false | 61 | source-valid | terminus2-commands-txt-strings; 61 operations |
| `terminus2-Moonshot__Kimi-K2-250905-query-optimize-0d628417` | Terminus2 | false | 18 | excluded | terminus2-commands-txt-strings emitted 19 operations; public step_count is 18 |
| `terminus2-Moonshot__Kimi-K2-250905-raman-fitting-bb47b585` | Terminus2 | false | 18 | excluded | terminus2-commands-txt-strings emitted 19 operations; public step_count is 18 |
| `terminus2-Moonshot__Kimi-K2-250905-rare-mineral-allocation-d66e5983` | Terminus2 | false | 19 | source-valid | terminus2-commands-txt-strings; 19 operations |
| `terminus2-Moonshot__Kimi-K2-250905-recover-accuracy-log-a344676f` | Terminus2 | true | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-Moonshot__Kimi-K2-250905-recover-obfuscated-files-f12d548a` | Terminus2 | true | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-Moonshot__Kimi-K2-250905-regex-chess-b4088ccb` | Terminus2 | false | 94 | source-valid | terminus2-commands-txt-strings; 94 operations |
| `terminus2-Moonshot__Kimi-K2-250905-reshard-c4-data-b77be535` | Terminus2 | missing | 30 | excluded | terminus2-commands-txt-strings emitted 31 operations; public step_count is 30 |
| `terminus2-Moonshot__Kimi-K2-250905-reverse-engineering-5fbdede6` | Terminus2 | false | 55 | source-valid | terminus2-commands-txt-strings; 55 operations |
| `terminus2-Moonshot__Kimi-K2-250905-rstan-to-pystan-7a6b6f3a` | Terminus2 | false | 60 | source-valid | terminus2-commands-txt-strings; 60 operations |
| `terminus2-Moonshot__Kimi-K2-250905-run-pdp11-code-dc20ce86` | Terminus2 | false | 37 | source-valid | terminus2-commands-txt-strings; 37 operations |
| `terminus2-Moonshot__Kimi-K2-250905-sam-cell-seg-1fd130e5` | Terminus2 | false | 58 | excluded | terminus2-commands-txt-strings emitted 59 operations; public step_count is 58 |
| `terminus2-Moonshot__Kimi-K2-250905-sanitize-git-repo-dbeb32c8` | Terminus2 | false | 20 | source-valid | terminus2-commands-txt-strings; 20 operations |
| `terminus2-Moonshot__Kimi-K2-250905-schedule-vacation-7c2221c2` | Terminus2 | true | 19 | source-valid | terminus2-commands-txt-strings; 19 operations |
| `terminus2-Moonshot__Kimi-K2-250905-schemelike-metacircular-eval-27616930` | Terminus2 | false | 166 | excluded | terminus2-commands-txt-strings emitted 165 operations; public step_count is 166 |
| `terminus2-Moonshot__Kimi-K2-250905-setup-custom-dev-env-82915d71` | Terminus2 | true | 44 | source-valid | terminus2-commands-txt-strings; 44 operations |
| `terminus2-Moonshot__Kimi-K2-250905-solana-data-308d44d7` | Terminus2 | false | 61 | source-valid | terminus2-commands-txt-strings; 61 operations |
| `terminus2-Moonshot__Kimi-K2-250905-solve-maze-challenge-ec789dd9` | Terminus2 | missing | 79 | source-valid | terminus2-commands-txt-strings; 79 operations |
| `terminus2-Moonshot__Kimi-K2-250905-solve-sudoku-823912f3` | Terminus2 | false | 40 | source-valid | terminus2-commands-txt-strings; 40 operations |
| `terminus2-Moonshot__Kimi-K2-250905-sparql-university-1ca3815c` | Terminus2 | false | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-Moonshot__Kimi-K2-250905-speech-to-text-59432027` | Terminus2 | false | 40 | source-valid | terminus2-commands-txt-strings; 40 operations |
| `terminus2-Moonshot__Kimi-K2-250905-sqlite-db-truncate-8e7ee438` | Terminus2 | false | 23 | source-valid | terminus2-commands-txt-strings; 23 operations |
| `terminus2-Moonshot__Kimi-K2-250905-sqlite-with-gcov-75bd0158` | Terminus2 | false | 31 | source-valid | terminus2-commands-txt-strings; 31 operations |
| `terminus2-Moonshot__Kimi-K2-250905-stable-parallel-kmeans-64261e12` | Terminus2 | missing | 56 | source-valid | terminus2-commands-txt-strings; 56 operations |
| `terminus2-Moonshot__Kimi-K2-250905-sudo-llvm-ir-9be34bb0` | Terminus2 | false | 55 | source-valid | terminus2-commands-txt-strings; 55 operations |
| `terminus2-Moonshot__Kimi-K2-250905-swe-bench-astropy-1-8e43006f` | Terminus2 | true | 38 | source-valid | terminus2-commands-txt-strings; 38 operations |
| `terminus2-Moonshot__Kimi-K2-250905-swe-bench-astropy-2-08f901ac` | Terminus2 | false | 70 | source-valid | terminus2-commands-txt-strings; 70 operations |
| `terminus2-Moonshot__Kimi-K2-250905-swe-bench-fsspec-71e46e65` | Terminus2 | true | 36 | source-valid | terminus2-commands-txt-strings; 36 operations |
| `terminus2-Moonshot__Kimi-K2-250905-swe-bench-langcodes-3c623524` | Terminus2 | true | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-Moonshot__Kimi-K2-250905-tmux-advanced-workflow-f9ea8221` | Terminus2 | false | 53 | source-valid | terminus2-commands-txt-strings; 53 operations |
| `terminus2-Moonshot__Kimi-K2-250905-torch-tensor-parallelism-2a7f1618` | Terminus2 | false | 26 | excluded | terminus2-commands-txt-strings emitted 27 operations; public step_count is 26 |
| `terminus2-Moonshot__Kimi-K2-250905-train-bpe-tokenizer-f317d056` | Terminus2 | false | 48 | source-valid | terminus2-commands-txt-strings; 48 operations |
| `terminus2-Moonshot__Kimi-K2-250905-train-fasttext-2c4d4859` | Terminus2 | false | 58 | source-valid | terminus2-commands-txt-strings; 58 operations |
| `terminus2-Moonshot__Kimi-K2-250905-tree-directory-parser-d4440915` | Terminus2 | true | 39 | excluded | terminus2-commands-txt-strings emitted 40 operations; public step_count is 39 |
| `terminus2-Moonshot__Kimi-K2-250905-triton-interpret-a70ba6c3` | Terminus2 | false | 56 | source-valid | terminus2-commands-txt-strings; 56 operations |
| `terminus2-Moonshot__Kimi-K2-250905-tune-mjcf-e393f8d1` | Terminus2 | false | 138 | source-valid | terminus2-commands-txt-strings; 138 operations |
| `terminus2-Moonshot__Kimi-K2-250905-vertex-solver-dbbce86e` | Terminus2 | true | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-Moonshot__Kimi-K2-250905-video-processing-0f1ba551` | Terminus2 | false | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-Moonshot__Kimi-K2-250905-vul-flask-2aa7a1ff` | Terminus2 | false | 69 | source-valid | terminus2-commands-txt-strings; 69 operations |
| `terminus2-Moonshot__Kimi-K2-250905-vul-flink-95cbaf0b` | Terminus2 | false | 64 | source-valid | terminus2-commands-txt-strings; 64 operations |
| `terminus2-Moonshot__Kimi-K2-250905-vulnerable-secret-6ff3da33` | Terminus2 | true | 29 | source-valid | terminus2-commands-txt-strings; 29 operations |
| `terminus2-Moonshot__Kimi-K2-250905-wasm-pipeline-760064ae` | Terminus2 | true | 44 | source-valid | terminus2-commands-txt-strings; 44 operations |
| `terminus2-Moonshot__Kimi-K2-250905-weighted-max-sat-solver-4702206d` | Terminus2 | false | 56 | source-valid | terminus2-commands-txt-strings; 56 operations |
| `terminus2-Moonshot__Kimi-K2-250905-winning-avg-corewars-561a4dc4` | Terminus2 | false | 50 | source-valid | terminus2-commands-txt-strings; 50 operations |
| `terminus2-Moonshot__Kimi-K2-250905-word2vec-from-scratch-4658db2e` | Terminus2 | false | 31 | excluded | terminus2-commands-txt-strings emitted 32 operations; public step_count is 31 |
| `terminus2-Moonshot__Kimi-K2-250905-write-compressor-7bf0e32b` | Terminus2 | false | 92 | source-valid | terminus2-commands-txt-strings; 92 operations |
| `terminus2-OpenAI__GPT-5-3d-model-format-legacy-79cf6d53` | Terminus2 | false | 521 | excluded | terminus2-commands-txt-strings emitted 511 operations; public step_count is 521 |
| `terminus2-OpenAI__GPT-5-adaptive-rejection-sampler-219b78b0` | Terminus2 | false | 104 | source-valid | terminus2-commands-txt-strings; 104 operations |
| `terminus2-OpenAI__GPT-5-add-benchmark-lm-eval-harness-1f231d3c` | Terminus2 | missing | 554 | excluded | terminus2-commands-txt-strings emitted 548 operations; public step_count is 554 |
| `terminus2-OpenAI__GPT-5-amuse-install-334d9e4f` | Terminus2 | true | 28 | source-valid | terminus2-commands-txt-strings; 28 operations |
| `terminus2-OpenAI__GPT-5-assign-seats-107778be` | Terminus2 | true | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-OpenAI__GPT-5-attention-mil-f14dec0c` | Terminus2 | false | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-OpenAI__GPT-5-audio-synth-stft-peaks-b006a383` | Terminus2 | false | 33 | source-valid | terminus2-commands-txt-strings; 33 operations |
| `terminus2-OpenAI__GPT-5-bank-trans-filter-b792f6a2` | Terminus2 | false | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-OpenAI__GPT-5-blind-maze-explorer-5x5-b6100f1b` | Terminus2 | true | 21 | source-valid | terminus2-commands-txt-strings; 21 operations |
| `terminus2-OpenAI__GPT-5-blind-maze-explorer-algorithm-e8be9918` | Terminus2 | true | 48 | source-valid | terminus2-commands-txt-strings; 48 operations |
| `terminus2-OpenAI__GPT-5-break-filter-js-from-html-62f02c6a` | Terminus2 | false | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-OpenAI__GPT-5-broken-networking-8d326da1` | Terminus2 | missing | 75 | source-valid | terminus2-commands-txt-strings; 75 operations |
| `terminus2-OpenAI__GPT-5-broken-python-3b13a1e6` | Terminus2 | true | 46 | source-valid | terminus2-commands-txt-strings; 46 operations |
| `terminus2-OpenAI__GPT-5-build-cython-ext-e6947c7e` | Terminus2 | true | 56 | source-valid | terminus2-commands-txt-strings; 56 operations |
| `terminus2-OpenAI__GPT-5-build-initramfs-qemu-b10ea365` | Terminus2 | missing | 25 | source-valid | terminus2-commands-txt-strings; 25 operations |
| `terminus2-OpenAI__GPT-5-build-linux-kernel-qemu-fab2938e` | Terminus2 | true | 94 | source-valid | terminus2-commands-txt-strings; 94 operations |
| `terminus2-OpenAI__GPT-5-build-pmars-b132c470` | Terminus2 | true | 72 | source-valid | terminus2-commands-txt-strings; 72 operations |
| `terminus2-OpenAI__GPT-5-build-pov-ray-27805b8f` | Terminus2 | missing | 131 | source-valid | terminus2-commands-txt-strings; 131 operations |
| `terminus2-OpenAI__GPT-5-build-stp-a0512054` | Terminus2 | false | 69 | source-valid | terminus2-commands-txt-strings; 69 operations |
| `terminus2-OpenAI__GPT-5-build-tcc-qemu-480c8187` | Terminus2 | false | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-OpenAI__GPT-5-caffe-cifar-10-84b99a60` | Terminus2 | false | 190 | excluded | terminus2-commands-txt-strings emitted 188 operations; public step_count is 190 |
| `terminus2-OpenAI__GPT-5-cartpole-rl-training-1cedc812` | Terminus2 | missing | 82 | source-valid | terminus2-commands-txt-strings; 82 operations |
| `terminus2-OpenAI__GPT-5-catch-me-if-you-can-3363c52f` | Terminus2 | false | 160 | source-valid | terminus2-commands-txt-strings; 160 operations |
| `terminus2-OpenAI__GPT-5-causal-inference-r-e75f4b45` | Terminus2 | true | 126 | source-valid | terminus2-commands-txt-strings; 126 operations |
| `terminus2-OpenAI__GPT-5-chem-property-targeting-d6dbbd36` | Terminus2 | true | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-OpenAI__GPT-5-chem-rf-a320b9ce` | Terminus2 | missing | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-OpenAI__GPT-5-chess-best-move-118fd5fc` | Terminus2 | false | 40 | source-valid | terminus2-commands-txt-strings; 40 operations |
| `terminus2-OpenAI__GPT-5-circuit-fibsqrt-6e68cca7` | Terminus2 | missing | 164 | excluded | terminus2-commands-txt-strings emitted 158 operations; public step_count is 164 |
| `terminus2-OpenAI__GPT-5-cobol-modernization-93376b69` | Terminus2 | true | 28 | source-valid | terminus2-commands-txt-strings; 28 operations |
| `terminus2-OpenAI__GPT-5-code-from-image-39bac00c` | Terminus2 | true | 37 | source-valid | terminus2-commands-txt-strings; 37 operations |
| `terminus2-OpenAI__GPT-5-compile-compcert-3a9b187f` | Terminus2 | missing | 180 | excluded | terminus2-commands-txt-strings emitted 171 operations; public step_count is 180 |
| `terminus2-OpenAI__GPT-5-conda-env-conflict-resolution-69130ead` | Terminus2 | true | 59 | source-valid | terminus2-commands-txt-strings; 59 operations |
| `terminus2-OpenAI__GPT-5-configure-git-webserver-304d41dd` | Terminus2 | false | 34 | source-valid | terminus2-commands-txt-strings; 34 operations |
| `terminus2-OpenAI__GPT-5-count-call-stack-6a40fc6a` | Terminus2 | false | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-OpenAI__GPT-5-count-dataset-tokens-ae042f29` | Terminus2 | false | 31 | source-valid | terminus2-commands-txt-strings; 31 operations |
| `terminus2-OpenAI__GPT-5-create-bucket-6a4ce21c` | Terminus2 | false | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-OpenAI__GPT-5-cron-broken-network-6617c90e` | Terminus2 | missing | 71 | source-valid | terminus2-commands-txt-strings; 71 operations |
| `terminus2-OpenAI__GPT-5-cross-entropy-method-ff12e6cc` | Terminus2 | true | 120 | source-valid | terminus2-commands-txt-strings; 120 operations |
| `terminus2-OpenAI__GPT-5-csv-to-parquet-df36680a` | Terminus2 | true | 40 | source-valid | terminus2-commands-txt-strings; 40 operations |
| `terminus2-OpenAI__GPT-5-db-wal-recovery-6d82bb72` | Terminus2 | false | 133 | source-valid | terminus2-commands-txt-strings; 133 operations |
| `terminus2-OpenAI__GPT-5-debug-long-program-d1544f2c` | Terminus2 | false | 84 | source-valid | terminus2-commands-txt-strings; 84 operations |
| `terminus2-OpenAI__GPT-5-decommissioning-service-with-sensitive-data-98b43c07` | Terminus2 | true | 19 | source-valid | terminus2-commands-txt-strings; 19 operations |
| `terminus2-OpenAI__GPT-5-dna-assembly-9c62739f` | Terminus2 | false | 46 | source-valid | terminus2-commands-txt-strings; 46 operations |
| `terminus2-OpenAI__GPT-5-dna-insert-003cbe7d` | Terminus2 | false | 364 | excluded | terminus2-commands-txt-strings emitted 351 operations; public step_count is 364 |
| `terminus2-OpenAI__GPT-5-download-youtube-fbfb0678` | Terminus2 | true | 49 | source-valid | terminus2-commands-txt-strings; 49 operations |
| `terminus2-OpenAI__GPT-5-enemy-grid-escape-8c8fc9a6` | Terminus2 | false | 141 | source-valid | terminus2-commands-txt-strings; 141 operations |
| `terminus2-OpenAI__GPT-5-extract-moves-from-video-03f60cbd` | Terminus2 | false | 125 | excluded | terminus2-commands-txt-strings emitted 123 operations; public step_count is 125 |
| `terminus2-OpenAI__GPT-5-feal-differential-cryptanalysis-95a5e56c` | Terminus2 | false | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-OpenAI__GPT-5-feal-linear-cryptanalysis-caceb72b` | Terminus2 | true | 44 | source-valid | terminus2-commands-txt-strings; 44 operations |
| `terminus2-OpenAI__GPT-5-financial-document-processor-7b127c0a` | Terminus2 | false | 41 | source-valid | terminus2-commands-txt-strings; 41 operations |
| `terminus2-OpenAI__GPT-5-find-official-code-b6a24499` | Terminus2 | false | 79 | source-valid | terminus2-commands-txt-strings; 79 operations |
| `terminus2-OpenAI__GPT-5-fix-code-vulnerability-474654ea` | Terminus2 | true | 160 | source-valid | terminus2-commands-txt-strings; 160 operations |
| `terminus2-OpenAI__GPT-5-fix-git-e2937b4c` | Terminus2 | true | 31 | source-valid | terminus2-commands-txt-strings; 31 operations |
| `terminus2-OpenAI__GPT-5-fix-ocaml-gc-6c5fe76e` | Terminus2 | missing | 297 | source-valid | terminus2-commands-txt-strings; 297 operations |
| `terminus2-OpenAI__GPT-5-fix-pandas-version-39d498ea` | Terminus2 | true | 15 | source-valid | terminus2-commands-txt-strings; 15 operations |
| `terminus2-OpenAI__GPT-5-fmri-encoding-r-d0b895fe` | Terminus2 | true | 34 | source-valid | terminus2-commands-txt-strings; 34 operations |
| `terminus2-OpenAI__GPT-5-form-filling-f2ab3787` | Terminus2 | true | 37 | source-valid | terminus2-commands-txt-strings; 37 operations |
| `terminus2-OpenAI__GPT-5-gcc-compiler-optimization-57d17ce9` | Terminus2 | true | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-OpenAI__GPT-5-get-bitcoin-nodes-7fc1016c` | Terminus2 | false | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-OpenAI__GPT-5-git-leak-recovery-8156e2df` | Terminus2 | false | 63 | source-valid | terminus2-commands-txt-strings; 63 operations |
| `terminus2-OpenAI__GPT-5-git-multibranch-26832189` | Terminus2 | false | 21 | source-valid | terminus2-commands-txt-strings; 21 operations |
| `terminus2-OpenAI__GPT-5-git-workflow-hack-403daef8` | Terminus2 | false | 40 | source-valid | terminus2-commands-txt-strings; 40 operations |
| `terminus2-OpenAI__GPT-5-hdfs-deployment-4e32dabb` | Terminus2 | false | 99 | source-valid | terminus2-commands-txt-strings; 99 operations |
| `terminus2-OpenAI__GPT-5-heterogeneous-dates-d1c6d845` | Terminus2 | true | 19 | source-valid | terminus2-commands-txt-strings; 19 operations |
| `terminus2-OpenAI__GPT-5-hf-lora-adapter-48cb9533` | Terminus2 | missing | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-OpenAI__GPT-5-hf-model-inference-91ce3a7b` | Terminus2 | true | 24 | source-valid | terminus2-commands-txt-strings; 24 operations |
| `terminus2-OpenAI__GPT-5-hf-train-lora-adapter-06426738` | Terminus2 | missing | 111 | excluded | terminus2-commands-txt-strings emitted 106 operations; public step_count is 111 |
| `terminus2-OpenAI__GPT-5-html-finance-verify-36bea99b` | Terminus2 | false | 54 | source-valid | terminus2-commands-txt-strings; 54 operations |
| `terminus2-OpenAI__GPT-5-hydra-debug-slurm-mode-586f5d66` | Terminus2 | false | 34 | source-valid | terminus2-commands-txt-strings; 34 operations |
| `terminus2-OpenAI__GPT-5-implement-eigenvectors-from-eigenvalues-research-paper-45e4bf57` | Terminus2 | false | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-OpenAI__GPT-5-incompatible-python-fasttext-6ce6a6e7` | Terminus2 | false | 15 | source-valid | terminus2-commands-txt-strings; 15 operations |
| `terminus2-OpenAI__GPT-5-install-klee-minimal-aa89117f` | Terminus2 | false | 195 | excluded | terminus2-commands-txt-strings emitted 186 operations; public step_count is 195 |
| `terminus2-OpenAI__GPT-5-install-windows-3.11-078ffbc7` | Terminus2 | missing | 485 | excluded | terminus2-commands-txt-strings emitted 463 operations; public step_count is 485 |
| `terminus2-OpenAI__GPT-5-install-windows-xp-434e3888` | Terminus2 | missing | 337 | excluded | terminus2-commands-txt-strings emitted 334 operations; public step_count is 337 |
| `terminus2-OpenAI__GPT-5-interactive-maze-game-e7653411` | Terminus2 | false | 53 | source-valid | terminus2-commands-txt-strings; 53 operations |
| `terminus2-OpenAI__GPT-5-intrusion-detection-47a5a59d` | Terminus2 | true | 53 | source-valid | terminus2-commands-txt-strings; 53 operations |
| `terminus2-OpenAI__GPT-5-jq-data-processing-960cc779` | Terminus2 | true | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-OpenAI__GPT-5-jupyter-notebook-server-5af30514` | Terminus2 | true | 77 | source-valid | terminus2-commands-txt-strings; 77 operations |
| `terminus2-OpenAI__GPT-5-kv-store-grpc-792dff2f` | Terminus2 | true | 20 | source-valid | terminus2-commands-txt-strings; 20 operations |
| `terminus2-OpenAI__GPT-5-large-scale-text-editing-16f58e14` | Terminus2 | false | 46 | source-valid | terminus2-commands-txt-strings; 46 operations |
| `terminus2-OpenAI__GPT-5-largest-eigenval-bfea72e4` | Terminus2 | false | 39 | source-valid | terminus2-commands-txt-strings; 39 operations |
| `terminus2-OpenAI__GPT-5-lean4-proof-ab14660a` | Terminus2 | missing | 368 | excluded | terminus2-commands-txt-strings emitted 367 operations; public step_count is 368 |
| `terminus2-OpenAI__GPT-5-leelachess0-pytorch-conversion-c887eab4` | Terminus2 | missing | 29 | source-valid | terminus2-commands-txt-strings; 29 operations |
| `terminus2-OpenAI__GPT-5-llm-inference-batching-scheduler-252354f4` | Terminus2 | false | 31 | source-valid | terminus2-commands-txt-strings; 31 operations |
| `terminus2-OpenAI__GPT-5-logistic-regression-divergence-f686eb09` | Terminus2 | true | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-OpenAI__GPT-5-magsac-install-f319dd3c` | Terminus2 | false | 171 | excluded | terminus2-commands-txt-strings emitted 149 operations; public step_count is 171 |
| `terminus2-OpenAI__GPT-5-mailman-0e0fb896` | Terminus2 | false | 279 | excluded | terminus2-commands-txt-strings emitted 272 operations; public step_count is 279 |
| `terminus2-OpenAI__GPT-5-make-doom-for-mips-cb17b1b0` | Terminus2 | false | 277 | excluded | terminus2-commands-txt-strings emitted 274 operations; public step_count is 277 |
| `terminus2-OpenAI__GPT-5-make-mips-interpreter-23f3d8c0` | Terminus2 | false | 141 | excluded | terminus2-commands-txt-strings emitted 138 operations; public step_count is 141 |
| `terminus2-OpenAI__GPT-5-mcmc-sampling-stan-6cf23f40` | Terminus2 | false | 85 | excluded | terminus2-commands-txt-strings emitted 80 operations; public step_count is 85 |
| `terminus2-OpenAI__GPT-5-merge-diff-arc-agi-task-bad65132` | Terminus2 | true | 108 | source-valid | terminus2-commands-txt-strings; 108 operations |
| `terminus2-OpenAI__GPT-5-mixed-integer-programming-2df867eb` | Terminus2 | false | 213 | excluded | terminus2-commands-txt-strings emitted 210 operations; public step_count is 213 |
| `terminus2-OpenAI__GPT-5-mlflow-register-e0a290b8` | Terminus2 | true | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-OpenAI__GPT-5-modernize-fortran-build-92c028af` | Terminus2 | false | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-OpenAI__GPT-5-modernize-scientific-stack-0639773e` | Terminus2 | true | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-OpenAI__GPT-5-mteb-eval-79850bf0` | Terminus2 | true | 13 | source-valid | terminus2-commands-txt-strings; 13 operations |
| `terminus2-OpenAI__GPT-5-mteb-leaderboard-deb29660` | Terminus2 | false | 190 | excluded | Terminus2 archive has no commands.txt |
| `terminus2-OpenAI__GPT-5-neuron-to-jaxley-conversion-75b171a0` | Terminus2 | false | 47 | source-valid | terminus2-commands-txt-strings; 47 operations |
| `terminus2-OpenAI__GPT-5-new-encrypt-command-83ba7d0a` | Terminus2 | true | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-OpenAI__GPT-5-npm-conflict-resolution-24396422` | Terminus2 | false | 56 | source-valid | terminus2-commands-txt-strings; 56 operations |
| `terminus2-OpenAI__GPT-5-oom-dba45d30` | Terminus2 | true | 15 | source-valid | terminus2-commands-txt-strings; 15 operations |
| `terminus2-OpenAI__GPT-5-optimal-transport-c3068d1d` | Terminus2 | false | 28 | source-valid | terminus2-commands-txt-strings; 28 operations |
| `terminus2-OpenAI__GPT-5-organization-json-generator-614b3c59` | Terminus2 | false | 21 | source-valid | terminus2-commands-txt-strings; 21 operations |
| `terminus2-OpenAI__GPT-5-overfull-hbox-44b99a95` | Terminus2 | false | 35 | source-valid | terminus2-commands-txt-strings; 35 operations |
| `terminus2-OpenAI__GPT-5-pandas-etl-d51c3346` | Terminus2 | true | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-OpenAI__GPT-5-parallel-particle-simulator-a1d4d80e` | Terminus2 | missing | 506 | excluded | terminus2-commands-txt-strings emitted 499 operations; public step_count is 506 |
| `terminus2-OpenAI__GPT-5-parallelize-compute-squares-33a66edf` | Terminus2 | false | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-OpenAI__GPT-5-parallelize-graph-86819125` | Terminus2 | true | 224 | source-valid | terminus2-commands-txt-strings; 224 operations |
| `terminus2-OpenAI__GPT-5-password-recovery-0fe399f8` | Terminus2 | true | 56 | source-valid | terminus2-commands-txt-strings; 56 operations |
| `terminus2-OpenAI__GPT-5-path-tracing-e519b39f` | Terminus2 | false | 50 | source-valid | terminus2-commands-txt-strings; 50 operations |
| `terminus2-OpenAI__GPT-5-path-tracing-reverse-49da1f1a` | Terminus2 | false | 51 | source-valid | terminus2-commands-txt-strings; 51 operations |
| `terminus2-OpenAI__GPT-5-play-zork-5c2b9e8f` | Terminus2 | false | 455 | excluded | terminus2-commands-txt-strings emitted 1294 operations; public step_count is 455 |
| `terminus2-OpenAI__GPT-5-play-zork-easy-ed6be1b5` | Terminus2 | false | 45 | source-valid | terminus2-commands-txt-strings; 45 operations |
| `terminus2-OpenAI__GPT-5-polyglot-rust-c-78cc0af0` | Terminus2 | false | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-OpenAI__GPT-5-port-compressor-a916ad03` | Terminus2 | missing | 605 | excluded | terminus2-commands-txt-strings emitted 595 operations; public step_count is 605 |
| `terminus2-OpenAI__GPT-5-portfolio-optimization-48bb1b7a` | Terminus2 | true | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-OpenAI__GPT-5-predicate-pushdown-bench-d8a3c127` | Terminus2 | missing | 150 | source-valid | terminus2-commands-txt-strings; 150 operations |
| `terminus2-OpenAI__GPT-5-processing-pipeline-8cbac326` | Terminus2 | false | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-OpenAI__GPT-5-protein-assembly-c309a103` | Terminus2 | false | 55 | source-valid | terminus2-commands-txt-strings; 55 operations |
| `terminus2-OpenAI__GPT-5-protocol-analysis-rs-5e36dbac` | Terminus2 | false | 413 | excluded | terminus2-commands-txt-strings emitted 621 operations; public step_count is 413 |
| `terminus2-OpenAI__GPT-5-puzzle-solver-b49a4eec` | Terminus2 | missing | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-OpenAI__GPT-5-pypi-server-0c924f18` | Terminus2 | true | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-OpenAI__GPT-5-pytorch-model-cli-6f695675` | Terminus2 | missing | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-OpenAI__GPT-5-pytorch-model-recovery-bc062f23` | Terminus2 | missing | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-OpenAI__GPT-5-query-optimize-2101d65d` | Terminus2 | false | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-OpenAI__GPT-5-raman-fitting-9f4c0c9d` | Terminus2 | false | 12 | source-valid | terminus2-commands-txt-strings; 12 operations |
| `terminus2-OpenAI__GPT-5-recover-accuracy-log-623d65ae` | Terminus2 | true | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-OpenAI__GPT-5-recover-obfuscated-files-d11b85e7` | Terminus2 | true | 13 | source-valid | terminus2-commands-txt-strings; 13 operations |
| `terminus2-OpenAI__GPT-5-reshard-c4-data-0c3cfb79` | Terminus2 | missing | 107 | source-valid | terminus2-commands-txt-strings; 107 operations |
| `terminus2-OpenAI__GPT-5-reverse-engineering-72042e7e` | Terminus2 | true | 38 | source-valid | terminus2-commands-txt-strings; 38 operations |
| `terminus2-OpenAI__GPT-5-rstan-to-pystan-4cb4ec4f` | Terminus2 | false | 172 | excluded | terminus2-commands-txt-strings emitted 168 operations; public step_count is 172 |
| `terminus2-OpenAI__GPT-5-run-pdp11-code-fe9bd73c` | Terminus2 | false | 25 | source-valid | terminus2-commands-txt-strings; 25 operations |
| `terminus2-OpenAI__GPT-5-schedule-vacation-b0ad80c0` | Terminus2 | false | 71 | source-valid | terminus2-commands-txt-strings; 71 operations |
| `terminus2-OpenAI__GPT-5-schemelike-metacircular-eval-f6897b34` | Terminus2 | missing | 310 | excluded | terminus2-commands-txt-strings emitted 304 operations; public step_count is 310 |
| `terminus2-OpenAI__GPT-5-security-vulhub-minio-ac922eec` | Terminus2 | false | 130 | source-valid | terminus2-commands-txt-strings; 130 operations |
| `terminus2-OpenAI__GPT-5-setup-custom-dev-env-1eb5c45f` | Terminus2 | true | 48 | source-valid | terminus2-commands-txt-strings; 48 operations |
| `terminus2-OpenAI__GPT-5-simple-sheets-put-2b43d8e2` | Terminus2 | false | 97 | source-valid | terminus2-commands-txt-strings; 97 operations |
| `terminus2-OpenAI__GPT-5-solana-data-e5980a09` | Terminus2 | false | 666 | source-valid | terminus2-commands-txt-strings; 666 operations |
| `terminus2-OpenAI__GPT-5-solve-maze-challenge-62f1e19e` | Terminus2 | missing | 303 | source-valid | terminus2-commands-txt-strings; 303 operations |
| `terminus2-OpenAI__GPT-5-solve-sudoku-0352744b` | Terminus2 | true | 100 | source-valid | terminus2-commands-txt-strings; 100 operations |
| `terminus2-OpenAI__GPT-5-sparql-professors-universities-0ca63a91` | Terminus2 | true | 12 | source-valid | terminus2-commands-txt-strings; 12 operations |
| `terminus2-OpenAI__GPT-5-speech-to-text-f39b2ff2` | Terminus2 | missing | 108 | excluded | terminus2-commands-txt-strings emitted 106 operations; public step_count is 108 |
| `terminus2-OpenAI__GPT-5-spinning-up-rl-e5437c9e` | Terminus2 | false | 137 | excluded | terminus2-commands-txt-strings emitted 136 operations; public step_count is 137 |
| `terminus2-OpenAI__GPT-5-sql-injection-attack-38a2efc1` | Terminus2 | missing | 77 | source-valid | terminus2-commands-txt-strings; 77 operations |
| `terminus2-OpenAI__GPT-5-sqlite-db-truncate-2e925a3b` | Terminus2 | false | 33 | source-valid | terminus2-commands-txt-strings; 33 operations |
| `terminus2-OpenAI__GPT-5-sqlite-with-gcov-8de3b3f7` | Terminus2 | false | 75 | source-valid | terminus2-commands-txt-strings; 75 operations |
| `terminus2-OpenAI__GPT-5-sudo-llvm-ir-cc8165b2` | Terminus2 | false | 19 | source-valid | terminus2-commands-txt-strings; 19 operations |
| `terminus2-OpenAI__GPT-5-swe-bench-astropy-1-68f567df` | Terminus2 | false | 528 | excluded | terminus2-commands-txt-strings emitted 519 operations; public step_count is 528 |
| `terminus2-OpenAI__GPT-5-swe-bench-astropy-2-9ccd8ff8` | Terminus2 | false | 68 | source-valid | terminus2-commands-txt-strings; 68 operations |
| `terminus2-OpenAI__GPT-5-swe-bench-fsspec-be694dc2` | Terminus2 | false | 72 | source-valid | terminus2-commands-txt-strings; 72 operations |
| `terminus2-OpenAI__GPT-5-swe-bench-langcodes-79fea234` | Terminus2 | true | 13 | source-valid | terminus2-commands-txt-strings; 13 operations |
| `terminus2-OpenAI__GPT-5-tmux-advanced-workflow-37d31ecc` | Terminus2 | true | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-OpenAI__GPT-5-torch-pipeline-parallelism-1f8e06a3` | Terminus2 | missing | 24 | source-valid | terminus2-commands-txt-strings; 24 operations |
| `terminus2-OpenAI__GPT-5-train-bpe-tokenizer-0b4c79ef` | Terminus2 | true | 28 | source-valid | terminus2-commands-txt-strings; 28 operations |
| `terminus2-OpenAI__GPT-5-train-fasttext-500d8273` | Terminus2 | missing | 163 | excluded | terminus2-commands-txt-strings emitted 158 operations; public step_count is 163 |
| `terminus2-OpenAI__GPT-5-tree-directory-parser-6040fed9` | Terminus2 | true | 21 | source-valid | terminus2-commands-txt-strings; 21 operations |
| `terminus2-OpenAI__GPT-5-triton-interpret-53d5e687` | Terminus2 | missing | 56 | source-valid | terminus2-commands-txt-strings; 56 operations |
| `terminus2-OpenAI__GPT-5-tune-mjcf-9f7ffcf3` | Terminus2 | true | 56 | source-valid | terminus2-commands-txt-strings; 56 operations |
| `terminus2-OpenAI__GPT-5-unprivileged-headless-pyrender-8a025991` | Terminus2 | false | 11 | excluded | terminus2-commands-txt-strings emitted 0 operations; public step_count is 11 |
| `terminus2-OpenAI__GPT-5-vul-flask-ca8de816` | Terminus2 | false | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-OpenAI__GPT-5-vul-flink-70c10ebb` | Terminus2 | false | 171 | source-valid | terminus2-commands-txt-strings; 171 operations |
| `terminus2-OpenAI__GPT-5-vulnerable-secret-852451bf` | Terminus2 | true | 63 | source-valid | terminus2-commands-txt-strings; 63 operations |
| `terminus2-OpenAI__GPT-5-wasm-pipeline-129bb600` | Terminus2 | true | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-OpenAI__GPT-5-weighted-max-sat-solver-33c2852b` | Terminus2 | false | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-OpenAI__GPT-5-winning-avg-corewars-e1e7fca6` | Terminus2 | missing | 223 | excluded | terminus2-commands-txt-strings emitted 217 operations; public step_count is 223 |
| `terminus2-OpenAI__GPT-5-word2vec-from-scratch-ceb20246` | Terminus2 | false | 13 | source-valid | terminus2-commands-txt-strings; 13 operations |
| `terminus2-OpenAI__GPT-5-write-compressor-cba10836` | Terminus2 | false | 134 | excluded | terminus2-commands-txt-strings emitted 127 operations; public step_count is 134 |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-3d-model-format-legacy-583c75ae` | Terminus2 | false | 234 | source-valid | terminus2-commands-txt-strings; 234 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-accelerate-maximal-square-a98e4616` | Terminus2 | true | 19 | source-valid | terminus2-commands-txt-strings; 19 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-acl-permissions-inheritance-78f010c7` | Terminus2 | false | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-adaptive-rejection-sampler-0333030c` | Terminus2 | false | 49 | source-valid | terminus2-commands-txt-strings; 49 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-add-benchmark-lm-eval-harness-a32c4edc` | Terminus2 | missing | 85 | source-valid | terminus2-commands-txt-strings; 85 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-aimo-airline-departures-3870a28d` | Terminus2 | false | 20 | source-valid | terminus2-commands-txt-strings; 20 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-analyze-access-logs-51b7bfa0` | Terminus2 | true | 13 | source-valid | terminus2-commands-txt-strings; 13 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-assign-seats-be1d06f8` | Terminus2 | true | 38 | source-valid | terminus2-commands-txt-strings; 38 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-attention-mil-15402492` | Terminus2 | false | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-audio-synth-stft-peaks-01c294a7` | Terminus2 | false | 39 | source-valid | terminus2-commands-txt-strings; 39 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-bank-trans-filter-8fd63839` | Terminus2 | false | 32 | source-valid | terminus2-commands-txt-strings; 32 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-blind-maze-explorer-5x5-fce9efd5` | Terminus2 | false | 51 | source-valid | terminus2-commands-txt-strings; 51 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-blind-maze-explorer-algorithm-042d2cb6` | Terminus2 | false | 26 | source-valid | terminus2-commands-txt-strings; 26 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-bn-fit-modify-edc93192` | Terminus2 | false | 70 | source-valid | terminus2-commands-txt-strings; 70 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-break-filter-js-from-html-6ebad22c` | Terminus2 | false | 200 | source-valid | terminus2-commands-txt-strings; 200 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-broken-networking-0c932cd2` | Terminus2 | missing | 59 | source-valid | terminus2-commands-txt-strings; 59 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-broken-python-2359dbaa` | Terminus2 | missing | 26 | source-valid | terminus2-commands-txt-strings; 26 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-cython-ext-232abaef` | Terminus2 | false | 46 | source-valid | terminus2-commands-txt-strings; 46 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-initramfs-qemu-35e1bbae` | Terminus2 | missing | 119 | source-valid | terminus2-commands-txt-strings; 119 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-linux-kernel-qemu-dfc83c88` | Terminus2 | false | 114 | source-valid | terminus2-commands-txt-strings; 114 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-pmars-42985926` | Terminus2 | false | 40 | source-valid | terminus2-commands-txt-strings; 40 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-pov-ray-61c2b4e4` | Terminus2 | false | 54 | source-valid | terminus2-commands-txt-strings; 54 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-build-stp-ccc5e9ee` | Terminus2 | false | 38 | source-valid | terminus2-commands-txt-strings; 38 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-caffe-cifar-10-f21fb025` | Terminus2 | false | 116 | excluded | terminus2-commands-txt-strings emitted 115 operations; public step_count is 116 |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-cancel-async-tasks-2130309b` | Terminus2 | true | 37 | source-valid | terminus2-commands-txt-strings; 37 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-cartpole-rl-training-990cf2de` | Terminus2 | true | 34 | source-valid | terminus2-commands-txt-strings; 34 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-catch-me-if-you-can-3fc8d1af` | Terminus2 | false | 83 | source-valid | terminus2-commands-txt-strings; 83 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-causal-inference-r-529ff59b` | Terminus2 | false | 81 | source-valid | terminus2-commands-txt-strings; 81 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-chem-property-targeting-239861eb` | Terminus2 | false | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-chem-rf-07ec41dc` | Terminus2 | missing | 80 | source-valid | terminus2-commands-txt-strings; 80 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-chess-best-move-6f546afe` | Terminus2 | false | 49 | source-valid | terminus2-commands-txt-strings; 49 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-circuit-fibsqrt-00590b3a` | Terminus2 | false | 48 | source-valid | terminus2-commands-txt-strings; 48 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-code-from-image-5ad96f6d` | Terminus2 | false | 75 | source-valid | terminus2-commands-txt-strings; 75 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-compile-compcert-c7b6cab6` | Terminus2 | missing | 171 | source-valid | terminus2-commands-txt-strings; 171 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-conda-env-conflict-resolution-61914e0a` | Terminus2 | false | 36 | source-valid | terminus2-commands-txt-strings; 36 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-configure-git-webserver-9223d53c` | Terminus2 | true | 43 | source-valid | terminus2-commands-txt-strings; 43 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-constraints-scheduling-a3af63c4` | Terminus2 | true | 144 | source-valid | terminus2-commands-txt-strings; 144 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-count-call-stack-6515a46c` | Terminus2 | false | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-count-dataset-tokens-827b2a3b` | Terminus2 | false | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-countdown-game-89478efb` | Terminus2 | false | 31 | source-valid | terminus2-commands-txt-strings; 31 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-cprofiling-python-39f7b4bd` | Terminus2 | true | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-cron-broken-network-647f9ad3` | Terminus2 | missing | 65 | source-valid | terminus2-commands-txt-strings; 65 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-cross-entropy-method-fe9e95b3` | Terminus2 | true | 38 | source-valid | terminus2-commands-txt-strings; 38 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-csv-to-parquet-7da5f12e` | Terminus2 | true | 29 | source-valid | terminus2-commands-txt-strings; 29 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-db-wal-recovery-865c917a` | Terminus2 | false | 24 | source-valid | terminus2-commands-txt-strings; 24 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-decommissioning-service-with-sensitive-data-f3e1332e` | Terminus2 | true | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-deterministic-tarball-6abceb70` | Terminus2 | false | 42 | source-valid | terminus2-commands-txt-strings; 42 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-distribution-search-c24bf0f5` | Terminus2 | false | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-dna-assembly-bffc7ef2` | Terminus2 | false | 47 | source-valid | terminus2-commands-txt-strings; 47 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-dna-insert-56752dd2` | Terminus2 | false | 53 | source-valid | terminus2-commands-txt-strings; 53 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-download-youtube-043820f0` | Terminus2 | false | 26 | source-valid | terminus2-commands-txt-strings; 26 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-enemy-grid-escape-b570ff10` | Terminus2 | false | 32 | source-valid | terminus2-commands-txt-strings; 32 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-extract-elf-266055a2` | Terminus2 | false | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-extract-moves-from-video-56c793ed` | Terminus2 | false | 61 | source-valid | terminus2-commands-txt-strings; 61 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-feal-differential-cryptanalysis-cf0c6108` | Terminus2 | false | 38 | source-valid | terminus2-commands-txt-strings; 38 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-feal-linear-cryptanalysis-36e03d68` | Terminus2 | false | 39 | source-valid | terminus2-commands-txt-strings; 39 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-fibonacci-server-e7401ea2` | Terminus2 | true | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-filter-js-from-html-a4b67224` | Terminus2 | false | 12 | source-valid | terminus2-commands-txt-strings; 12 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-financial-document-processor-a81ca517` | Terminus2 | false | 20 | source-valid | terminus2-commands-txt-strings; 20 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-find-official-code-5c90092a` | Terminus2 | false | 24 | source-valid | terminus2-commands-txt-strings; 24 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-fix-code-vulnerability-f8cd3e78` | Terminus2 | true | 69 | source-valid | terminus2-commands-txt-strings; 69 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-fix-git-c9c18563` | Terminus2 | true | 26 | source-valid | terminus2-commands-txt-strings; 26 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-fix-ocaml-gc-6eedd2ee` | Terminus2 | false | 60 | source-valid | terminus2-commands-txt-strings; 60 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-fmri-encoding-r-db797903` | Terminus2 | true | 21 | source-valid | terminus2-commands-txt-strings; 21 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-form-filling-93ce5c9a` | Terminus2 | false | 199 | source-valid | terminus2-commands-txt-strings; 199 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-gcc-compiler-optimization-b298a939` | Terminus2 | true | 15 | source-valid | terminus2-commands-txt-strings; 15 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-gcode-to-text-c948d3f6` | Terminus2 | false | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-get-bitcoin-nodes-5b817512` | Terminus2 | false | 19 | source-valid | terminus2-commands-txt-strings; 19 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-git-leak-recovery-8bb6df64` | Terminus2 | true | 13 | source-valid | terminus2-commands-txt-strings; 13 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-git-multibranch-b5a98f03` | Terminus2 | false | 82 | source-valid | terminus2-commands-txt-strings; 82 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-git-workflow-hack-e10ec50a` | Terminus2 | true | 32 | source-valid | terminus2-commands-txt-strings; 32 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-gpt2-codegolf-5e61981b` | Terminus2 | false | 20 | source-valid | terminus2-commands-txt-strings; 20 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-hdfs-deployment-d9815dde` | Terminus2 | true | 67 | source-valid | terminus2-commands-txt-strings; 67 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-heterogeneous-dates-77f7b938` | Terminus2 | false | 29 | source-valid | terminus2-commands-txt-strings; 29 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-hf-lora-adapter-3c6042ea` | Terminus2 | missing | 30 | source-valid | terminus2-commands-txt-strings; 30 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-hf-model-inference-402eaf22` | Terminus2 | true | 40 | source-valid | terminus2-commands-txt-strings; 40 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-hf-train-lora-adapter-7eabc203` | Terminus2 | missing | 88 | source-valid | terminus2-commands-txt-strings; 88 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-huarong-dao-solver-75ec2043` | Terminus2 | false | 30 | excluded | terminus2-commands-txt-strings emitted 29 operations; public step_count is 30 |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-ilp-solver-cac49c1f` | Terminus2 | true | 28 | source-valid | terminus2-commands-txt-strings; 28 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-implement-eigenvectors-from-eigenvalues-research-paper-afb93cfc` | Terminus2 | true | 32 | source-valid | terminus2-commands-txt-strings; 32 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-incompatible-python-fasttext-fc6b964d` | Terminus2 | true | 22 | source-valid | terminus2-commands-txt-strings; 22 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-install-windows-3.11-34e1451e` | Terminus2 | false | 42 | source-valid | terminus2-commands-txt-strings; 42 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-install-windows-xp-b1d1b8db` | Terminus2 | false | 35 | source-valid | terminus2-commands-txt-strings; 35 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-intrusion-detection-38bb0273` | Terminus2 | false | 24 | source-valid | terminus2-commands-txt-strings; 24 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-jq-data-processing-2948f82f` | Terminus2 | true | 22 | source-valid | terminus2-commands-txt-strings; 22 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-jupyter-notebook-server-e3992708` | Terminus2 | false | 34 | source-valid | terminus2-commands-txt-strings; 34 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-kv-store-grpc-d797816c` | Terminus2 | false | 12 | source-valid | terminus2-commands-txt-strings; 12 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-large-scale-text-editing-70af623a` | Terminus2 | missing | 56 | source-valid | terminus2-commands-txt-strings; 56 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-lean4-proof-01db781c` | Terminus2 | false | 62 | excluded | terminus2-commands-txt-strings emitted 61 operations; public step_count is 62 |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-leelachess0-pytorch-conversion-47905d20` | Terminus2 | missing | 34 | source-valid | terminus2-commands-txt-strings; 34 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-llm-inference-batching-scheduler-b69dbff4` | Terminus2 | false | 47 | source-valid | terminus2-commands-txt-strings; 47 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-llm-spec-decoding-c921863e` | Terminus2 | missing | 17 | source-valid | terminus2-commands-txt-strings; 17 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-log-summary-71af6949` | Terminus2 | true | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-log-summary-date-ranges-57369bce` | Terminus2 | false | 12 | source-valid | terminus2-commands-txt-strings; 12 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-logistic-regression-divergence-bfe86e20` | Terminus2 | false | 28 | source-valid | terminus2-commands-txt-strings; 28 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-magsac-install-e7fadb5e` | Terminus2 | false | 128 | source-valid | terminus2-commands-txt-strings; 128 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-mahjong-winninghand-2730cce2` | Terminus2 | true | 21 | source-valid | terminus2-commands-txt-strings; 21 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-mailman-d5ae62e3` | Terminus2 | false | 61 | source-valid | terminus2-commands-txt-strings; 61 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-make-doom-for-mips-867bcd9d` | Terminus2 | false | 200 | source-valid | terminus2-commands-txt-strings; 200 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-make-mips-interpreter-5707ff69` | Terminus2 | false | 199 | source-valid | terminus2-commands-txt-strings; 199 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-mcmc-sampling-stan-8da87350` | Terminus2 | false | 40 | source-valid | terminus2-commands-txt-strings; 40 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-model-extraction-relu-logits-f7f42dd0` | Terminus2 | true | 13 | source-valid | terminus2-commands-txt-strings; 13 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-modernize-fortran-build-ab6e4811` | Terminus2 | true | 51 | source-valid | terminus2-commands-txt-strings; 51 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-movie-helper-8c36e5cf` | Terminus2 | false | 12 | source-valid | terminus2-commands-txt-strings; 12 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-mteb-leaderboard-8d12f51c` | Terminus2 | false | 20 | source-valid | terminus2-commands-txt-strings; 20 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-mteb-retrieve-6a2ca9e6` | Terminus2 | false | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-multi-source-data-merger-097903db` | Terminus2 | true | 21 | source-valid | terminus2-commands-txt-strings; 21 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-neuron-to-jaxley-conversion-6b35cfee` | Terminus2 | false | 31 | source-valid | terminus2-commands-txt-strings; 31 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-new-encrypt-command-6a3b0e88` | Terminus2 | true | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-nginx-request-logging-393d8070` | Terminus2 | false | 27 | excluded | terminus2-commands-txt-strings emitted 26 operations; public step_count is 27 |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-npm-conflict-resolution-6361b716` | Terminus2 | false | 92 | source-valid | terminus2-commands-txt-strings; 92 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-openssl-selfsigned-cert-c7b86221` | Terminus2 | true | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-optimal-transport-e4ee31f6` | Terminus2 | false | 16 | source-valid | terminus2-commands-txt-strings; 16 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-organization-json-generator-e8fe9a9b` | Terminus2 | true | 22 | source-valid | terminus2-commands-txt-strings; 22 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-pandas-etl-5f6313a7` | Terminus2 | false | 34 | source-valid | terminus2-commands-txt-strings; 34 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-parallel-particle-simulator-9837586a` | Terminus2 | false | 79 | source-valid | terminus2-commands-txt-strings; 79 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-parallelize-graph-67a2792a` | Terminus2 | false | 94 | source-valid | terminus2-commands-txt-strings; 94 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-password-recovery-996227b3` | Terminus2 | false | 47 | source-valid | terminus2-commands-txt-strings; 47 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-path-tracing-reverse-dd80f2f2` | Terminus2 | false | 30 | source-valid | terminus2-commands-txt-strings; 30 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-pcap-to-netflow-ab94ba4e` | Terminus2 | false | 50 | source-valid | terminus2-commands-txt-strings; 50 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-play-zork-028c67f5` | Terminus2 | false | 200 | excluded | terminus2-commands-txt-strings emitted 199 operations; public step_count is 200 |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-play-zork-easy-8712eef7` | Terminus2 | false | 123 | excluded | terminus2-commands-txt-strings emitted 122 operations; public step_count is 123 |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-polyglot-c-py-9a5ae981` | Terminus2 | false | 200 | source-valid | terminus2-commands-txt-strings; 200 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-polyglot-rust-c-b96fa888` | Terminus2 | false | 199 | source-valid | terminus2-commands-txt-strings; 199 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-port-compressor-2a6b1e67` | Terminus2 | false | 200 | source-valid | terminus2-commands-txt-strings; 200 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-portfolio-optimization-cb630fb9` | Terminus2 | true | 25 | source-valid | terminus2-commands-txt-strings; 25 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-predicate-pushdown-bench-945d2a67` | Terminus2 | missing | 36 | source-valid | terminus2-commands-txt-strings; 36 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-processing-pipeline-11753b0d` | Terminus2 | true | 24 | source-valid | terminus2-commands-txt-strings; 24 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-protein-assembly-3ce00f26` | Terminus2 | false | 54 | source-valid | terminus2-commands-txt-strings; 54 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-protocol-analysis-rs-2cdb040e` | Terminus2 | false | 136 | source-valid | terminus2-commands-txt-strings; 136 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-puzzle-solver-cb79c3c4` | Terminus2 | false | 27 | source-valid | terminus2-commands-txt-strings; 27 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-pypi-server-03e4faa2` | Terminus2 | true | 85 | source-valid | terminus2-commands-txt-strings; 85 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-pytorch-model-cli-803ca59d` | Terminus2 | false | 25 | source-valid | terminus2-commands-txt-strings; 25 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-raman-fitting-c32a90ea` | Terminus2 | false | 20 | source-valid | terminus2-commands-txt-strings; 20 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-rare-mineral-allocation-9fbbfd98` | Terminus2 | false | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-recover-accuracy-log-9b4c6eae` | Terminus2 | true | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-recover-obfuscated-files-57656e13` | Terminus2 | true | 11 | source-valid | terminus2-commands-txt-strings; 11 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-regex-chess-9c03ffe3` | Terminus2 | false | 28 | source-valid | terminus2-commands-txt-strings; 28 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-reshard-c4-data-b10bdec5` | Terminus2 | false | 36 | source-valid | terminus2-commands-txt-strings; 36 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-reverse-engineering-e3dfd250` | Terminus2 | false | 199 | source-valid | terminus2-commands-txt-strings; 199 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-rstan-to-pystan-49157fed` | Terminus2 | true | 60 | source-valid | terminus2-commands-txt-strings; 60 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-run-pdp11-code-6d1a7c27` | Terminus2 | false | 39 | source-valid | terminus2-commands-txt-strings; 39 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-sam-cell-seg-bac826c2` | Terminus2 | false | 42 | source-valid | terminus2-commands-txt-strings; 42 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-schedule-vacation-4f59e21a` | Terminus2 | true | 28 | source-valid | terminus2-commands-txt-strings; 28 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-schemelike-metacircular-eval-16696516` | Terminus2 | false | 54 | source-valid | terminus2-commands-txt-strings; 54 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-setup-custom-dev-env-c17752fc` | Terminus2 | false | 29 | source-valid | terminus2-commands-txt-strings; 29 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-solve-maze-challenge-9dc4216e` | Terminus2 | missing | 42 | source-valid | terminus2-commands-txt-strings; 42 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-solve-sudoku-818e88f2` | Terminus2 | false | 14 | source-valid | terminus2-commands-txt-strings; 14 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-sparql-university-1d2b57b8` | Terminus2 | false | 12 | source-valid | terminus2-commands-txt-strings; 12 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-speech-to-text-81da51f1` | Terminus2 | missing | 57 | source-valid | terminus2-commands-txt-strings; 57 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-spinning-up-rl-c96db893` | Terminus2 | false | 68 | source-valid | terminus2-commands-txt-strings; 68 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-sqlite-db-truncate-98abceea` | Terminus2 | false | 21 | source-valid | terminus2-commands-txt-strings; 21 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-sqlite-with-gcov-cf1f3d6f` | Terminus2 | true | 32 | source-valid | terminus2-commands-txt-strings; 32 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-stable-parallel-kmeans-ac0505a8` | Terminus2 | true | 39 | source-valid | terminus2-commands-txt-strings; 39 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-sudo-llvm-ir-c5a3939b` | Terminus2 | false | 55 | source-valid | terminus2-commands-txt-strings; 55 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-swe-bench-astropy-1-4af8da5a` | Terminus2 | false | 29 | source-valid | terminus2-commands-txt-strings; 29 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-swe-bench-astropy-2-bd14f76c` | Terminus2 | false | 53 | source-valid | terminus2-commands-txt-strings; 53 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-swe-bench-fsspec-e4e11e48` | Terminus2 | false | 197 | source-valid | terminus2-commands-txt-strings; 197 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-swe-bench-langcodes-1c0d117d` | Terminus2 | true | 23 | source-valid | terminus2-commands-txt-strings; 23 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-tmux-advanced-workflow-4a518f0f` | Terminus2 | false | 18 | source-valid | terminus2-commands-txt-strings; 18 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-train-bpe-tokenizer-c0838325` | Terminus2 | false | 112 | source-valid | terminus2-commands-txt-strings; 112 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-train-fasttext-4e1099ff` | Terminus2 | false | 74 | source-valid | terminus2-commands-txt-strings; 74 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-tree-directory-parser-be0ef31b` | Terminus2 | true | 59 | source-valid | terminus2-commands-txt-strings; 59 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-triton-interpret-04b4472c` | Terminus2 | false | 200 | source-valid | terminus2-commands-txt-strings; 200 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-vertex-solver-d6f0f84b` | Terminus2 | true | 40 | source-valid | terminus2-commands-txt-strings; 40 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-vimscript-vim-quine-221cbd12` | Terminus2 | false | 23 | source-valid | terminus2-commands-txt-strings; 23 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-vul-flask-a1188e13` | Terminus2 | false | 20 | source-valid | terminus2-commands-txt-strings; 20 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-vul-flink-c44290cf` | Terminus2 | false | 45 | source-valid | terminus2-commands-txt-strings; 45 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-wasm-pipeline-f07d0051` | Terminus2 | true | 33 | source-valid | terminus2-commands-txt-strings; 33 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-weighted-max-sat-solver-f8731c73` | Terminus2 | false | 40 | source-valid | terminus2-commands-txt-strings; 40 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-winning-avg-corewars-5925b4c5` | Terminus2 | false | 192 | source-valid | terminus2-commands-txt-strings; 192 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-word2vec-from-scratch-94d20de4` | Terminus2 | false | 85 | source-valid | terminus2-commands-txt-strings; 85 operations |
| `terminus2-Qwen__Qwen3-Coder-480B-A35B-Instruct-write-compressor-1ed41eae` | Terminus2 | false | 35 | source-valid | terminus2-commands-txt-strings; 35 operations |
