# Research State

Current stage: supplement / experiment-design
Stage status: partial
Last updated: 2026-06-15
Active claim(s): C1, C2, C3, C4, C5, C6
Latest artifact: `docs/visexp/out/live-record-r114-smoke.json`, `docs/visexp/FOLLOWUP_PLAN.md`, `docs/visexp/out/model-benchmarks-r121.json`, `docs/visexp/out/live-record-r113.json`, `.agentsight/agentflame/latest/agentflame.json`
Blocking gate: OSDI weak accept requires G2 broader live exact lineage, G3 small-model/tag adequacy, and G4 developer task utility; only G1 full-history characterization currently passes
Gate evidence: `docs/visexp/FOLLOWUP_PLAN.md`, `docs/visexp/CLAIM_VERDICT.md`
Next action: fix or explicitly scope R114 wrapper/sibling false positives before running the 20-task exact-lineage suite
Last handoff: R114 suite implementation and 1-task smoke completed; raw join was 100.0% but precision was only 25.98% because wrapper negative-control effects were over-attributed
