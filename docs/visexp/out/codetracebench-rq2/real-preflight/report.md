# CodeTraceBench RQ2 REAL PREFLIGHT Report

**Status:** PASS

## End-To-End Boundary

The runner loaded 3316 full-manifest and 1000 verified safe-projection rows, extracted 1077/1328 candidate reference trajectories and 6/6 target trajectories, invoked release AgentProf for semantic/raw-action/phase reference and target views, computed task-held-out failed-minus-successful scores, and wrote predictions before the terminal label join.

Pre-label predictions: `docs/visexp/out/codetracebench-rq2/real-preflight/predictions-pre-label.md`

## Reference Support

| Fallback level | Targets |
|---|---:|
| `agent-model-difficulty-category` | 1 |
| `agent-model-category` | 4 |
| `agent-model` | 1 |

## Terminal Incorrect-Step Metrics

| Method | Pooled tie-aware AP | Recall @ 30% work | Work @ 50% recall | Steps | Incorrect steps | Tie blocks | Zero-positive targets |
|---|---:|---:|---:|---:|---:|---:|---:|
| semantic | 0.053306 | 0.083333 | 0.670370 | 270 | 12 | 39 | 3 |
| raw-action | 0.062097 | 0.083333 | 0.403704 | 270 | 12 | 38 | 3 |
| phase | 0.063779 | 0.166667 | 0.666667 | 270 | 12 | 11 | 3 |

## Source Exclusions

Target failures: 0. Reference failures: 251. Every exclusion is based on missing raw source, adapter failure, or public-count mismatch before label projection; no trajectory is truncated or padded.

| Population | Trajectory | Reason |
|---|---|---|
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-audio-synth-stft-peaks-c05fb8b4` | miniswe-agent-log-markers emitted 10 operations; public step_count is 18 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-cancel-async-tasks-c4880238` | miniswe-agent-log-markers emitted 0 operations; public step_count is 13 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-cartpole-rl-training-77f68671` | miniswe-agent-log-markers emitted 25 operations; public step_count is 17 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-catch-me-if-you-can-24c22254` | miniswe-agent-log-markers emitted 20 operations; public step_count is 15 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-compile-compcert-997ae681` | miniswe-agent-log-markers emitted 72 operations; public step_count is 73 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-configure-git-webserver-03fd1e23` | miniswe-agent-log-markers emitted 0 operations; public step_count is 17 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-cpp-compatibility-5fc09a00` | miniswe-agent-log-markers emitted 0 operations; public step_count is 13 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-cron-broken-network-e82a5c2f` | miniswe-agent-log-markers emitted 0 operations; public step_count is 37 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-custom-memory-heap-crash-af9a130a` | MiniSWE archive has neither sessions/agent.log nor .traj.json |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-dna-insert-3d3baf3a` | miniswe-agent-log-markers emitted 8 operations; public step_count is 23 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-download-youtube-1e1335c3` | miniswe-agent-log-markers emitted 0 operations; public step_count is 23 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-feal-differential-cryptanalysis-c6a0e7f0` | miniswe-agent-log-markers emitted 18 operations; public step_count is 35 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-financial-document-processor-7fa7444b` | miniswe-agent-log-markers emitted 14 operations; public step_count is 15 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-hf-model-inference-f200d460` | miniswe-agent-log-markers emitted 27 operations; public step_count is 34 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-hf-train-lora-adapter-2d013ce9` | miniswe-agent-log-markers emitted 0 operations; public step_count is 29 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-interactive-maze-game-2077ac78` | miniswe-agent-log-markers emitted 0 operations; public step_count is 18 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-jupyter-notebook-server-f7fce821` | miniswe-agent-log-markers emitted 37 operations; public step_count is 27 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-large-scale-text-editing-e70ac842` | miniswe-agent-log-markers emitted 18 operations; public step_count is 21 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-llm-inference-batching-scheduler-8929b713` | miniswe-agent-log-markers emitted 0 operations; public step_count is 31 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-llm-spec-decoding-b474b28b` | miniswe-agent-log-markers emitted 0 operations; public step_count is 23 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-mlflow-register-60a717c0` | miniswe-agent-log-markers emitted 0 operations; public step_count is 21 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-nginx-request-logging-d25b5dd9` | miniswe-agent-log-markers emitted 15 operations; public step_count is 22 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-oom-7dcdc1ab` | miniswe-agent-log-markers emitted 18 operations; public step_count is 15 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-organization-json-generator-3639b4e1` | miniswe-agent-log-markers emitted 0 operations; public step_count is 12 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-parallel-particle-simulator-1f9b1eea` | miniswe-agent-log-markers emitted 17 operations; public step_count is 19 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-password-recovery-65e3232c` | miniswe-agent-log-markers emitted 29 operations; public step_count is 17 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-play-zork-34879dd5` | miniswe-agent-log-markers emitted 13 operations; public step_count is 17 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-play-zork-easy-8c77a548` | miniswe-agent-log-markers emitted 14 operations; public step_count is 33 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-pytorch-model-cli-1a764f1f` | miniswe-agent-log-markers emitted 39 operations; public step_count is 21 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-pytorch-model-recovery-fbf3001a` | miniswe-agent-log-markers emitted 0 operations; public step_count is 20 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-query-optimize-8cb16f94` | miniswe-agent-log-markers emitted 0 operations; public step_count is 17 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-regex-log-c987e17b` | miniswe-agent-log-markers emitted 0 operations; public step_count is 21 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-schemelike-metacircular-eval-1494da6d` | miniswe-agent-log-markers emitted 0 operations; public step_count is 64 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-security-celery-redis-rce-1b5605f8` | miniswe-agent-log-markers emitted 0 operations; public step_count is 34 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-simple-sheets-put-f60a0568` | MiniSWE archive has neither sessions/agent.log nor .traj.json |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-solana-data-72de38cf` | miniswe-agent-log-markers emitted 0 operations; public step_count is 35 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-sql-injection-attack-dc0ecfcf` | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-stable-parallel-kmeans-a1318efd` | miniswe-agent-log-markers emitted 4 operations; public step_count is 32 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-tmux-advanced-workflow-04e67d90` | miniswe-agent-log-markers emitted 1 operations; public step_count is 33 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-torch-pipeline-parallelism-78788704` | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-triton-interpret-5d494583` | miniswe-agent-log-markers emitted 37 operations; public step_count is 17 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-vulnerable-secret-d6426d57` | miniswe-agent-log-markers emitted 0 operations; public step_count is 25 |
| reference | `miniswe-Anthropic__Claude-Sonnet-4-20250514-Thinking-weighted-max-sat-solver-93a49e03` | miniswe-agent-log-markers emitted 16 operations; public step_count is 15 |
| reference | `miniswe-OpenAI__GPT-5-3d-model-format-legacy-4d59305e` | miniswe-agent-log-markers emitted 24 operations; public step_count is 28 |
| reference | `miniswe-OpenAI__GPT-5-build-cython-ext-64eba0f3` | miniswe-agent-log-markers emitted 0 operations; public step_count is 13 |
| reference | `miniswe-OpenAI__GPT-5-build-pmars-0e21302e` | miniswe-agent-log-markers emitted 3 operations; public step_count is 14 |
| reference | `miniswe-OpenAI__GPT-5-build-stp-c74e1e89` | miniswe-agent-log-markers emitted 3 operations; public step_count is 20 |
| reference | `miniswe-OpenAI__GPT-5-cron-broken-network-ab2690b8` | miniswe-agent-log-markers emitted 0 operations; public step_count is 15 |
| reference | `miniswe-OpenAI__GPT-5-fix-code-vulnerability-1ae3c58d` | miniswe-agent-log-markers emitted 0 operations; public step_count is 16 |
| reference | `miniswe-OpenAI__GPT-5-intrusion-detection-316f5769` | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| reference | `miniswe-OpenAI__GPT-5-logistic-regression-divergence-d858448d` | miniswe-agent-log-markers emitted 0 operations; public step_count is 12 |
| reference | `miniswe-OpenAI__GPT-5-mailman-439bccbe` | miniswe-agent-log-markers emitted 16 operations; public step_count is 18 |
| reference | `miniswe-OpenAI__GPT-5-nginx-request-logging-2196edde` | miniswe-agent-log-markers emitted 0 operations; public step_count is 11 |
| reference | `miniswe-OpenAI__GPT-5-npm-conflict-resolution-a4afc1de` | miniswe-agent-log-markers emitted 0 operations; public step_count is 18 |
| reference | `miniswe-OpenAI__GPT-5-parallelize-graph-2ab0330f` | miniswe-message-trajectory emitted 22 operations; public step_count is 21 |
| reference | `miniswe-OpenAI__GPT-5-path-tracing-7cb4317a` | miniswe-agent-log-markers emitted 17 operations; public step_count is 12 |
| reference | `miniswe-OpenAI__GPT-5-port-compressor-715a5f28` | miniswe-message-trajectory emitted 23 operations; public step_count is 21 |
| reference | `miniswe-OpenAI__GPT-5-reshard-c4-data-85bfb6a3` | MiniSWE archive has neither sessions/agent.log nor .traj.json |
| reference | `miniswe-OpenAI__GPT-5-reverse-engineering-1ba94fc1` | miniswe-message-trajectory emitted 23 operations; public step_count is 22 |
| reference | `miniswe-OpenAI__GPT-5-security-celery-redis-rce-292b9ce2` | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| reference | `miniswe-OpenAI__GPT-5-solve-sudoku-b6addaec` | miniswe-agent-log-markers emitted 0 operations; public step_count is 14 |
| reference | `miniswe-OpenAI__GPT-5-spinning-up-rl-1d6a252e` | MiniSWE archive has neither sessions/agent.log nor .traj.json |
| reference | `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-chem-rf-271f890f` | openhands-agent-actions emitted 59 operations; public step_count is 31 |
| reference | `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-hf-model-inference-1520e16b` | openhands-agent-actions emitted 46 operations; public step_count is 35 |
| reference | `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-lean4-proof-c2cf74ba` | openhands-agent-actions emitted 91 operations; public step_count is 82 |
| reference | `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-mteb-eval-09ae8a74` | openhands-agent-actions emitted 38 operations; public step_count is 30 |
| reference | `openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-train-fasttext-b326259b` | openhands-agent-actions emitted 57 operations; public step_count is 47 |
| reference | `openhands-OpenAI__GPT-5-adaptive-rejection-sampler-3e6787e7` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-add-benchmark-lm-eval-harness-aa036803` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-ancient-puzzle-afac6b18` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-audio-synth-stft-peaks-4679a79f` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-break-filter-js-from-html-7aa94ae8` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-build-cython-ext-fbe9fd86` | openhands-agent-actions emitted 46 operations; public step_count is 35 |
| reference | `openhands-OpenAI__GPT-5-build-linux-kernel-qemu-aa2f8bd3` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-build-pov-ray-6faae954` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-build-stp-768a3759` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-causal-inference-r-5f30a1f0` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-chem-property-targeting-c8be58a4` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-circuit-fibsqrt-b4830ef5` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-cobol-modernization-3f9244bd` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-code-from-image-8044dcd2` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-conda-env-conflict-resolution-1a0646a6` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-configure-git-webserver-6a62b5f7` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-cross-entropy-method-b6ad3b99` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-custom-memory-heap-crash-ccb1ba42` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-db-wal-recovery-1d244aa6` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-deterministic-tarball-9832ca54` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-dna-insert-070be780` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-enemy-grid-escape-83f149ee` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-feal-linear-cryptanalysis-35e4e30d` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-filter-js-from-html-766374ea` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-financial-document-processor-6e957148` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-find-official-code-1be1e012` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-find-restaurant-fd9ef9a6` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-fix-code-vulnerability-5864dfed` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-fix-git-45ee3a9f` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-fix-permissions-2bbc8e2d` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-form-filling-1ff403d3` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-gcc-compiler-optimization-c66f179c` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-get-bitcoin-nodes-596dd62a` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-git-multibranch-b9a7c2ce` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-git-workflow-hack-d7ab1c99` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-hdfs-deployment-2d36343d` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-hf-lora-adapter-74d2d66e` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-hf-model-inference-58d4c9f2` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-hf-train-lora-adapter-c7ba9feb` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-home-server-https-af791665` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-html-finance-verify-d79ce44a` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-implement-eigenvectors-from-eigenvalues-research-paper-54d1ccc6` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-incompatible-python-fasttext-a448fdd0` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-install-klee-minimal-f4977da9` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-install-windows-3.11-5f5c52fe` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-install-windows-xp-be27fb42` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-intrusion-detection-a9adab04` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-kv-store-grpc-fce0d6c4` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-largest-eigenval-02947cc3` | openhands-agent-actions emitted 24 operations; public step_count is 23 |
| reference | `openhands-OpenAI__GPT-5-leelachess0-pytorch-conversion-fbd9590c` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-llm-inference-batching-scheduler-838051ac` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-mailman-17fed2a9` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-mcmc-sampling-stan-463cb85c` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-merge-diff-arc-agi-task-d91f31a2` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-mlflow-register-bdcf25a8` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-modernize-scientific-stack-979d4b60` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-mteb-eval-e68b82bd` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-multi-source-data-merger-5f49c785` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-openssl-selfsigned-cert-813c84fe` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-optimal-transport-aea98f31` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-overfull-hbox-be8933f3` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-parallel-particle-simulator-bd802119` | openhands-agent-actions emitted 36 operations; public step_count is 35 |
| reference | `openhands-OpenAI__GPT-5-parallelize-graph-60d7a7b7` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-password-recovery-2b0e8478` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-path-tracing-6f1a1bf0` | openhands-agent-actions emitted 42 operations; public step_count is 35 |
| reference | `openhands-OpenAI__GPT-5-play-lord-7413c06b` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-polyglot-c-py-5a74e7ac` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-port-compressor-53a2b666` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-portfolio-optimization-bfc4d5e4` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-predicate-pushdown-bench-77410ef2` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-processing-pipeline-a1543eaf` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-puzzle-solver-3ddc78ab` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-pypi-server-5533ac61` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-pytorch-model-cli-5792944d` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-pytorch-model-recovery-bb63ee33` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-query-optimize-ce2e43d2` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-raman-fitting-5b6353cd` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-rare-mineral-allocation-9033b1c9` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-regex-chess-c9013ba7` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-reverse-engineering-41949138` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-run-pdp11-code-40544045` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-sam-cell-seg-0ae8c161` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-sanitize-git-repo-fa8206db` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-schedule-vacation-dc56b91c` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-schemelike-metacircular-eval-e9641b96` | openhands-agent-actions emitted 42 operations; public step_count is 35 |
| reference | `openhands-OpenAI__GPT-5-security-celery-redis-rce-999b4f07` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-security-vulhub-minio-33fe9f01` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-setup-custom-dev-env-d6e32c59` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-simple-sheets-put-28d34f12` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-solana-data-6c481541` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-solve-sudoku-5ecea83b` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-speech-to-text-a2b56c6f` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-spinning-up-rl-8a313a1d` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-sqlite-db-truncate-28e7900e` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-stable-parallel-kmeans-ed192a60` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-swe-bench-fsspec-74ae74e1` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-swe-bench-langcodes-9dc7a598` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-tmux-advanced-workflow-4c53ca67` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-tree-directory-parser-738da939` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-triton-interpret-4ac0c33a` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-vertex-solver-7e1773f4` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-video-processing-d61fabc4` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-vul-flask-21e213ae` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-vulnerable-secret-e1393875` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-winning-avg-corewars-61f3a2b9` | OpenHands archive has neither call records nor session events |
| reference | `openhands-OpenAI__GPT-5-word2vec-from-scratch-998fdd92` | OpenHands archive has neither call records nor session events |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-3d-model-format-legacy-5eb709af` | terminus2-commands-txt-strings emitted 95 operations; public step_count is 94 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-add-benchmark-lm-eval-harness-11987c87` | terminus2-commands-txt-strings emitted 208 operations; public step_count is 206 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-audio-synth-stft-peaks-e07e3ef5` | terminus2-commands-txt-strings emitted 38 operations; public step_count is 37 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-blind-maze-explorer-5x5-dc477a42` | terminus2-commands-txt-strings emitted 47 operations; public step_count is 46 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-blind-maze-explorer-algorithm-e5814a22` | terminus2-commands-txt-strings emitted 48 operations; public step_count is 47 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-break-filter-js-from-html-4096e492` | terminus2-commands-txt-strings emitted 90 operations; public step_count is 89 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-broken-python-02d55149` | terminus2-commands-txt-strings emitted 34 operations; public step_count is 30 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-cython-ext-a7e47d56` | terminus2-commands-txt-strings emitted 56 operations; public step_count is 53 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-build-stp-56801309` | terminus2-commands-txt-strings emitted 41 operations; public step_count is 40 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-catch-me-if-you-can-d89cfe9a` | terminus2-commands-txt-strings emitted 69 operations; public step_count is 68 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-causal-inference-r-887a15bd` | terminus2-commands-txt-strings emitted 54 operations; public step_count is 53 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-chem-property-targeting-32a06e96` | terminus2-commands-txt-strings emitted 16 operations; public step_count is 15 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-chess-best-move-b049f713` | Terminus2 archive has no commands.txt |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-code-from-image-14a45388` | terminus2-commands-txt-strings emitted 28 operations; public step_count is 27 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-count-dataset-tokens-ad1d3494` | terminus2-commands-txt-strings emitted 41 operations; public step_count is 40 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-cron-broken-network-5669e672` | terminus2-commands-txt-strings emitted 64 operations; public step_count is 63 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-cross-entropy-method-378af4b8` | terminus2-commands-txt-strings emitted 18 operations; public step_count is 17 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-db-wal-recovery-6792ef3f` | terminus2-commands-txt-strings emitted 30 operations; public step_count is 29 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-deterministic-tarball-6396449f` | terminus2-commands-txt-strings emitted 32 operations; public step_count is 30 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-feal-differential-cryptanalysis-d54aba6a` | terminus2-commands-txt-strings emitted 39 operations; public step_count is 38 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-feal-linear-cryptanalysis-675ff900` | terminus2-commands-txt-strings emitted 53 operations; public step_count is 52 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-filter-js-from-html-61cd1fd1` | terminus2-commands-txt-strings emitted 21 operations; public step_count is 20 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-find-official-code-83933bf6` | terminus2-commands-txt-strings emitted 14 operations; public step_count is 13 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-fix-git-81e6eaff` | terminus2-commands-txt-strings emitted 15 operations; public step_count is 14 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-fix-ocaml-gc-5784d704` | terminus2-commands-txt-strings emitted 328 operations; public step_count is 327 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-form-filling-6907bd11` | terminus2-commands-txt-strings emitted 23 operations; public step_count is 22 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-gcode-to-text-04074693` | terminus2-commands-txt-strings emitted 13 operations; public step_count is 12 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-git-leak-recovery-02eec3b6` | terminus2-commands-txt-strings emitted 18 operations; public step_count is 17 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-html-finance-verify-ecd6dfd7` | terminus2-commands-txt-strings emitted 17 operations; public step_count is 16 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-huarong-dao-solver-bf643dc7` | terminus2-commands-txt-strings emitted 17 operations; public step_count is 16 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-hydra-debug-slurm-mode-837c94b0` | terminus2-commands-txt-strings emitted 27 operations; public step_count is 26 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-incompatible-python-fasttext-64f07e3f` | terminus2-commands-txt-strings emitted 28 operations; public step_count is 26 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-install-klee-minimal-57ed56f5` | terminus2-commands-txt-strings emitted 104 operations; public step_count is 100 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-jq-data-processing-0f26000b` | terminus2-commands-txt-strings emitted 12 operations; public step_count is 11 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-largest-eigenval-eb9cc4f2` | terminus2-commands-txt-strings emitted 58 operations; public step_count is 57 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-lean4-proof-33ef0bfe` | terminus2-commands-txt-strings emitted 104 operations; public step_count is 103 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-leelachess0-pytorch-conversion-4b4c022f` | terminus2-commands-txt-strings emitted 30 operations; public step_count is 29 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-llm-inference-batching-scheduler-36976180` | terminus2-commands-txt-strings emitted 34 operations; public step_count is 33 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-llm-spec-decoding-a5cda7d7` | terminus2-commands-txt-strings emitted 24 operations; public step_count is 23 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-logistic-regression-divergence-0b8df7b3` | terminus2-commands-txt-strings emitted 28 operations; public step_count is 27 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-mailman-3540eeca` | Terminus2 archive has no commands.txt |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-make-mips-interpreter-35ea4c65` | terminus2-commands-txt-strings emitted 62 operations; public step_count is 61 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-npm-conflict-resolution-1fb2a796` | terminus2-commands-txt-strings emitted 38 operations; public step_count is 37 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-optimal-transport-63f97042` | terminus2-commands-txt-strings emitted 18 operations; public step_count is 17 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-organization-json-generator-c7de58b7` | terminus2-commands-txt-strings emitted 13 operations; public step_count is 12 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-overfull-hbox-70f3acfa` | Terminus2 archive has no commands.txt |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-parallelize-compute-squares-eb552139` | terminus2-commands-txt-strings emitted 18 operations; public step_count is 17 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-parallelize-graph-619aaf8f` | terminus2-commands-txt-strings emitted 48 operations; public step_count is 47 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-path-tracing-reverse-f5f5b8bf` | terminus2-commands-txt-strings emitted 60 operations; public step_count is 59 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-play-zork-c2eb2245` | terminus2-commands-txt-strings emitted 200 operations; public step_count is 199 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-port-compressor-b12aa2b9` | terminus2-commands-txt-strings emitted 106 operations; public step_count is 105 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-portfolio-optimization-bdd2ad8f` | terminus2-commands-txt-strings emitted 16 operations; public step_count is 15 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-processing-pipeline-b359442c` | terminus2-commands-txt-strings emitted 23 operations; public step_count is 22 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-protein-assembly-dfa5f8b4` | terminus2-commands-txt-strings emitted 36 operations; public step_count is 35 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-protocol-analysis-rs-7c5f5525` | terminus2-commands-txt-strings emitted 63 operations; public step_count is 62 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-pytorch-model-recovery-d836c842` | terminus2-commands-txt-strings emitted 15 operations; public step_count is 14 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-query-optimize-9b7a8831` | terminus2-commands-txt-strings emitted 16 operations; public step_count is 15 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-reverse-engineering-d69939cc` | terminus2-commands-txt-strings emitted 202 operations; public step_count is 201 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-rstan-to-pystan-6adcbc5e` | terminus2-commands-txt-strings emitted 39 operations; public step_count is 38 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-schedule-vacation-9e1a63a1` | terminus2-commands-txt-strings emitted 19 operations; public step_count is 18 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-solve-sudoku-5b91640a` | terminus2-commands-txt-strings emitted 34 operations; public step_count is 33 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-sqlite-db-truncate-e979013b` | terminus2-commands-txt-strings emitted 16 operations; public step_count is 15 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-swe-bench-astropy-1-6b5580a5` | terminus2-commands-txt-strings emitted 27 operations; public step_count is 26 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-train-bpe-tokenizer-b8dfe7d6` | terminus2-commands-txt-strings emitted 38 operations; public step_count is 37 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-triton-interpret-13f3a750` | terminus2-commands-txt-strings emitted 37 operations; public step_count is 36 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-tune-mjcf-b120ae1e` | terminus2-commands-txt-strings emitted 56 operations; public step_count is 55 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-vul-flask-77e6f39e` | terminus2-commands-txt-strings emitted 20 operations; public step_count is 19 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-vul-flink-220ab971` | terminus2-commands-txt-strings emitted 43 operations; public step_count is 41 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-vulnerable-secret-472cc6f6` | terminus2-commands-txt-strings emitted 37 operations; public step_count is 36 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-wasm-pipeline-1db8244f` | terminus2-commands-txt-strings emitted 46 operations; public step_count is 45 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-weighted-max-sat-solver-39519774` | terminus2-commands-txt-strings emitted 16 operations; public step_count is 15 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-word2vec-from-scratch-ea1b146f` | terminus2-commands-txt-strings emitted 44 operations; public step_count is 43 |
| reference | `terminus2-Anthropic__Claude-Sonnet-4-20250514-Thinking-write-compressor-cce26430` | terminus2-commands-txt-strings emitted 47 operations; public step_count is 46 |
| reference | `sweagent-OpenAI__GPT-5-keras-team__keras-19775-5d529dfd` | sweagent-trajectory-elements emitted 48 operations; public step_count is 26 |
| reference | `sweagent-OpenAI__GPT-5-mui__material-ui-11451-c1ca3d8a` | sweagent-trajectory-elements emitted 94 operations; public step_count is 54 |
| reference | `sweagent-OpenAI__GPT-5-microsoft__vscode-153857-9567d425` | sweagent-trajectory-elements emitted 36 operations; public step_count is 1 |
| reference | `sweagent-OpenAI__GPT-5-mui__material-ui-28186-2ac683f2` | sweagent-trajectory-elements emitted 30 operations; public step_count is 6 |
| reference | `sweagent-OpenAI__GPT-5-prettier__prettier-12930-05aa8eba` | sweagent-trajectory-elements emitted 18 operations; public step_count is 10 |

## Decision

REAL PREFLIGHT is complete when status is PASS: the actual real-input, source alignment, AgentProf, matching, scoring, prediction, terminal-label, and metric path all ran. Metric sign is not a preflight gate. Independent review is still required before the full run.
