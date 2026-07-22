# Entry Baseline

- Baseline object from `git stash create`: `a6f58cfe3d42634d059c727cebdc46da8793f6c5`
- Paper: `docs/paper/main.tex`
- Target venue: AAAI 2027 Main Technical Track / AI Alignment
- Entry compile: PASS (`latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex`)

## Frozen scientific contract

1. RQ1 tests objective intervention utility from byte-identical frozen
   checkpoints: Workspace Trajectory versus Full Raw, Generic, and No
   Intervention under matched budgets, with the official executable oracle.
2. RQ2 ablates deterministic relation families only after RQ1 is supported.
3. RQ3 tests held-out coding/scientific work, safety, abstention, and budgets.
4. Human labels, human adjudication, Agent substitute labels, and LLM-judge
   primary outcomes are excluded.
5. The current Harness run is dependency evidence only: zero treatment tool
   calls and a failed 3/6 headroom gate; no treatment effect was estimated.
