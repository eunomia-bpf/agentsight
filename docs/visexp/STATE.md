# Research State

Current stage: supplement / experiment-design
Stage status: partial
Last updated: 2026-06-15
Active claim(s): C1, C2, C3, C4, C5, C6
Latest artifact: `docs/visexp/out/live-record-r114.json`, `docs/visexp/out/live-record-r114-analysis.json`, `docs/visexp/out/model-benchmarks-r121.json`, `docs/visexp/out/model-benchmarks-r121.md`, `docs/visexp/FOLLOWUP_PLAN.md`, `.agentsight/agentflame/latest/agentflame.json`
Blocking gate: OSDI weak accept now primarily requires G3 tag adequacy/stability beyond the 3B smoke and G4 developer task utility; G2 passes for the fixed 20-task command-mode suite but still needs broader replication before broad claims
Gate evidence: `docs/visexp/FOLLOWUP_PLAN.md`, `docs/visexp/CLAIM_VERDICT.md`
Next action: prepare R122 adequacy labels, expand B5x to real redacted fragments and any added 0.6B/1B weights, then run R131 semantic-axis ablations and the B4 developer task pilot
Last handoff: full R114 completed over 20 real Codex tasks; 20/20 targets completed, 20/20 tasks observed negative controls, 1273/1273 in-scope effects joined, precision/recall were 100.0%/100.0%, 3170 negative-control effects were observed with 0 joined, child-depth/path/redaction analysis was generated, and raw join stayed 22.055% because out-of-scope effects remained orphaned. R121 then fixed the benchmark to repeat identical fragments and found 9/9 valid 3B tags, 2/3 exact-stable synthetic fragments, and no local 0.6B/1B model weights.
