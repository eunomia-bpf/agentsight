# R233 Prompt-Row Lineage Normalization

Status: `ok_normalized_semantic_lineage`

R233 reads generated R170/R231 artifacts only. It converts duplicate
prompt indexes from an implicit key bug into an explicit normalized
lineage contract.

## Summary

- Sessions/prompts: 325 sessions, 2859 prompt rows.
- Duplicate prompt-index rows: 12 across 5 sessions.
- Duplicate groups: 9 same-tag, 3 mixed-tag.
- Legacy field-index drift reproduced: tool 346 weight, LLM 93 events.
- Normalized semantic drift: tool 0 weight (0.0%), LLM 0 events (0.0%).
- Duplicate-index events: tool 1026 weight, LLM 577 events.
- Tag-disambiguated duplicate-index events: tool 451 weight, LLM 145 events.
- Same-tag duplicate row-identity ambiguity: tool 575 weight, LLM 432 events.

## Claim Gate

- Display projection matches event-local prompt tags: `True`.
- Normalized semantic prompt-row lineage supported: `True`.
- Strict prompt-row identity supported: `False`.
- Duplicate prompt indexes explicitly non-keyed: `True`.

## Boundary

R233 supports strict semantic prompt-row consistency for generated full-history artifacts after normalizing duplicate prompt indexes as non-keyed row identifiers. It does not prove strict prompt-row identity for same-tag duplicate rows, live eBPF provenance, arbitrary agents, C5 user utility, or C6 tag adequacy.
