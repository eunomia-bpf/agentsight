# R231 Drift Root-Cause Audit

Status: `ok_drift_root_cause_localized`

R231 reads generated R170/R230 artifacts only. It separates the display
projection used by flamegraphs from raw prompt-row lineage joins.

## Summary

- Sessions/prompts: 325 sessions, 2859 prompt rows.
- Duplicate prompt-index rows: 12 across 5 sessions.
- Display projection: event-local prompt-tag weights 183714 vs folded prompt-frame weights 183714; exact match `True`.
- Field-index prompt-row drift: tool 346 weight (0.188%), LLM 93 events (0.081%).
- List-position prompt-row drift: tool 2048 weight (1.115%), LLM 1144 events (0.996%).
- Field-index drift in unique-index sessions: tool 0 weight, LLM 0 events.
- Field-index drift in duplicate-index sessions: tool 346 weight, LLM 93 events.

## Claim Gate

- Display projection matches event-local prompt tags: `True`.
- R230 field-index drift reproduced: `True`.
- Field-index drift localized to duplicate-index sessions: `True`.
- Strict prompt-row lineage supported: `False`.
- External cross-repo live lineage supported: `False`.

## Top Mismatch Pairs

| Kind | Semantics | Row tag | Event tag | Weight |
|------|-----------|---------|-----------|-------:|
| tool | field | `review` | `test` | 304 |
| tool | position | `review` | `test` | 304 |
| llm | position | `docs` | `refactor` | 303 |
| tool | position | `docs` | `refactor` | 261 |
| tool | position | `perfreview` | `docs` | 246 |
| llm | position | `deployed` | `commit` | 198 |
| tool | position | `refactor` | `workspace` | 180 |
| tool | position | `review` | `metrics` | 168 |
| tool | position | `review` | `deployed` | 165 |
| tool | position | `deployed` | `commit` | 165 |
| llm | position | `review` | `metrics` | 145 |
| llm | field | `review` | `test` | 89 |

## Boundary

R231 explains the R230 drift at the generated-artifact layer. The semantic flamegraph display projection exactly matches event-local tool prompt tags, but raw prompt-row lineage is not strict because a small set of Claude sessions contains duplicate prompt indexes and event-local tags can differ from prompt-row tags. R231 does not run fresh live eBPF capture, does not prove external cross-repo lineage, and does not provide C5/C6 human evidence.
