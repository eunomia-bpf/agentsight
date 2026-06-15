# Research State

Current stage: experiment-design / analyze
Stage status: partial
Last updated: 2026-06-14
Active claim(s): C1, C2, C3, C4, C5, C6
Latest artifact: `docs/visexp/out/native-lineage-r112.json`, `.agentsight/agentflame/latest/agentflame.json`
Blocking gate: DB-persisted backfill lineage raw join is only 57.233%, capture-time ancestry is missing, and user/task benchmark is missing
Gate evidence: `docs/visexp/CLAIM_VERDICT.md`
Next action: reduce R112 orphan causes and move observed envelope materialization from explicit backfill to capture-time ancestry, then run B5 small-model/stability benchmark and B4 user-task pilot
Last handoff: local full-history AgentFlame run completed with 205 sessions and 0 final tag failures
