# R230 Full-History Projection-Lineage Audit

Status: `partial_projection_indexed_with_semantic_drift`

R230 reads generated R170/R225 AgentFlame artifacts only. It checks the
full-history projection/indexing layer; it does not claim live exact
provenance or human evidence.

## Summary

- Sessions/prompts: 325 sessions, 2859 prompt rows, 2847 unique per-session prompt indexes.
- Duplicate prompt-index rows: 12 across 5 sessions.
- System folded stacks: 26829 unique stacks, 183714 total weight.
- Required folded frames missing weight: 0.
- Raw system observation weight from tool events: 183714.
- Tool prompt-index coverage: 183714/183714 weight = 100.0%.
- Tool ambiguous prompt-index weight: 1026 (0.558%).
- Tool prompt-tag drift: 346 weight (0.188%) across 261 events.
- LLM prompt-index coverage: 114837/114837 events = 100.0%.
- LLM prompt-tag drift: 93 events (0.081%).

## Claim Gate

- System-effect history projection supported: `True`.
- Strict prompt-tag consistency supported: `False`.
- Strict full-history semantic lineage supported: `False`.
- Live exact provenance supported: `False`.

## Boundary

R230 audits generated full-history AgentFlame artifacts, not raw agent sessions and not live eBPF provenance. It can support the weaker claim that folded system effects carry semantic session/prompt tag frames, call/effect frames, and match the R170 report totals. Raw event indexes are audited separately. Because prompt indexes can be duplicated and event-local prompt tags can drift from prompt-row tags, and because this is not a live negative-control run, it does not prove strict full-history exact semantic lineage, C5 developer utility, or C6 tag adequacy.
