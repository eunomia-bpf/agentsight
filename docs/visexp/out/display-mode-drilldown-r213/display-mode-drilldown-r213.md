# R213 Display-Mode Drilldown Smoke

Status: `display_mode_drilldown_smoke_ready_no_quality_claims`

## Boundary

- Reads generated R209 artifacts only.
- Does not read or mutate raw Codex/Claude traces.
- Does not call an LLM.
- Verifies display-mode data mechanics only; no frontend renderer, merge-quality, adequacy, or utility claim.

## Mode Summary

| mode | buckets | support | drilldown | candidate overlays | review rows | active merges |
|---|---:|---:|---|---:|---:|---:|
| `raw` | 1811 | 482398 | True | 0 | 0 | 0 |
| `display` | 1748 | 482398 | True | 0 | 0 | 63 |
| `pending` | 1748 | 482398 | True | 209 | 323 | 63 |

## Pending Queue

Pending/review queue rows: `323`.
Candidate overlay rows: `209`.
Review-required rows: `323`.
Review-required support: `9293`.

Top pending rows:

| dimension | raw tag | display tag | candidate | support | reason |
|---|---|---|---|---:|---|
| prompt | `ignored` | `ignored` | `refactor` | 1221 | pending regenerated-label promotion review |
| session | `uxdesign` | `uxdesign` | `design` | 1148 | pending lexical/profile merge review |
| prompt | `designcodex` | `designcodex` | `design` | 1074 | pending lexical/profile merge review |
| prompt | `testcodex` | `testcodex` | `test` | 982 | pending lexical/profile merge review |
| prompt | `codex` | `codex` | `codexnavigate` | 402 | pending regenerated-label promotion review |
| llm | `uxdesign` | `uxdesign` | `design` | 357 | pending lexical/profile merge review |
| llm | `check` | `check` | `review` | 294 | pending regenerated-label promotion review |
| prompt | `reviewbu` | `reviewbu` | `review` | 254 | pending lexical/profile merge review |
| session | `reviewbu` | `reviewbu` | `review` | 254 | pending lexical/profile merge review |
| prompt | `testcodexrun` | `testcodexrun` | `test` | 198 | pending lexical/profile merge review |
| prompt | `analyzesess` | `analyzesess` | `analyze` | 179 | pending lexical/profile merge review |
| prompt | `codexcheck` | `codexcheck` | `codexanalyze` | 176 | pending regenerated-label promotion review |

## Sample Panels

| mode | dimension | display tag | support | raw tag count | candidate rows | review rows |
|---|---|---|---:|---:|---:|---:|
| `raw` | session | `refactor` | 89914 | 1 | 0 | 0 |
| `raw` | prompt | `refactor` | 73162 | 1 | 0 | 0 |
| `raw` | llm | `refactor` | 41263 | 1 | 0 | 0 |
| `raw` | prompt | `review` | 33267 | 1 | 0 | 0 |
| `raw` | session | `review` | 29164 | 1 | 0 | 0 |
| `raw` | session | `design` | 25434 | 1 | 0 | 0 |
| `raw` | llm | `analyze` | 18712 | 1 | 0 | 0 |
| `raw` | prompt | `design` | 15705 | 1 | 0 | 0 |
| `raw` | session | `analyze` | 12433 | 1 | 0 | 0 |
| `raw` | session | `research` | 11891 | 1 | 0 | 0 |
| `raw` | prompt | `analyze` | 11457 | 1 | 0 | 0 |
| `raw` | llm | `design` | 9592 | 1 | 0 | 0 |
| `display` | llm | `analyze` | 18713 | 2 | 0 | 0 |
| `pending` | llm | `analyze` | 18713 | 2 | 0 | 0 |
| `display` | prompt | `design` | 16109 | 2 | 0 | 0 |
| `pending` | prompt | `design` | 16109 | 2 | 0 | 0 |
| `display` | prompt | `analyze` | 11460 | 2 | 0 | 0 |
| `pending` | prompt | `analyze` | 11460 | 2 | 0 | 0 |

## Claim Boundary

R213 supports a display-mode data-layer smoke only: raw/display/pending modes preserve support, pending mode does not change display membership, and the artifact has enough data to expose raw-tag drilldown and review burden. It does not exercise the frontend renderer and does not support semantic adequacy, merge quality, regenerated-label quality, or developer utility.
