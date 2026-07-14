# Plan Review Round 1

**Verdict: REVISE**

The scientific design is valid and appropriately bounded: it tests H17 with six paired tasks, treats the 18 unique task-view packets rather than the 144 assignment rows as the evidence surface, uses fixed-session as the single claim-relevant baseline, keeps flat and R316 visible order as controls, separates collection from hidden-key scoring, and limits the claim to one frozen reader. Positive, mixed, and negative outcomes all change the RQ2 interpretation. Reusing R315/R316 is a better and simpler use of the budget than constructing a new counterfactual benchmark.

## Necessary fixes before preflight

1. Replace the abstract `collect` and `score` mode descriptions with the exact runnable command(s), runner path, arguments, and concrete raw/result output directory. Freeze the actual API `model` value, llama.cpp build/server configuration, and exact option that disables reasoning; the filesystem GGUF path alone does not fully specify the request path. The commands must show that collection receives only the visible-packet path and that scoring alone receives the hidden-key path.
2. Make the failed-cell rule unambiguous: after the fixed retries, any persistently invalid or missing cell makes the planned 18-cell run `INVALID`; do not drop a task, impute a response, or compute the paired verdict on a reduced matrix.

Do not add multiple models, decoding repeats, a new benchmark or dataset, extra baselines, or sealing/attestation infrastructure. None is required for validity, and each would weaken the plan's reuse and simplicity.
