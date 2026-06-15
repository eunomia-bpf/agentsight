# Research State

Current stage: supplement / experiment-design
Stage status: partial
Last updated: 2026-06-15
Active claim(s): C1, C2, C3, C4, C5, C6
Latest artifact: `docs/visexp/out/live-record-r114.json`, `docs/visexp/out/live-record-r114-analysis.json`, `docs/visexp/out/tag-adequacy-label-packet-r122.json`, `docs/visexp/out/model-benchmarks-r123.json`, `docs/visexp/out/semantic-ablation-r131.json`, `docs/visexp/FOLLOWUP_PLAN.md`, `.agentsight/agentflame/latest/agentflame.json`
Blocking gate: OSDI weak accept now primarily requires G3 human tag adequacy and G4 developer task utility; G2 passes for the fixed 20-task command-mode suite and R131 passes for mechanism ablation, but broader replication remains required before broad claims
Gate evidence: `docs/visexp/FOLLOWUP_PLAN.md`, `docs/visexp/CLAIM_VERDICT.md`
Next action: collect/adjudicate R124 human adequacy labels over the R122 packet, then run the B4 developer task pilot
Last handoff: full R114 completed over 20 real Codex tasks; 20/20 targets completed, 20/20 tasks observed negative controls, 1273/1273 in-scope effects joined, precision/recall were 100.0%/100.0%, 3170 negative-control effects were observed with 0 joined, child-depth/path/redaction analysis was generated, and raw join stayed 22.055% because out-of-scope effects remained orphaned. R122 generated a redacted 300-fragment session/prompt/LLM-call label packet from 290 parsed sessions. R123 ran the same 300 redacted fragments through the 3B llama.cpp server for 3 identical repeats each: 900/900 valid tags, p95 30 ms after load, and 282/300 exact-stable fragments. R131 projected the same full folded artifacts into no/session/prompt/full system variants and no/session/prompt/LLM/prompt+LLM/full token variants; all totals were preserved, `agentflame.json` totals matched folded inputs, and already generated folded projections matched exactly. For system effects, no-semantic mixed 90.219% bucket / 44.639% residual full semantic weight, session-only left 84.180% / 34.138%, prompt-only left 37.687% / 7.526%, and full session+prompt left 0.000% by construction.
