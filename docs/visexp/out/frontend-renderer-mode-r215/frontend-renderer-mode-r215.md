# R215 Frontend Renderer-Mode Smoke

Status: `frontend_renderer_mode_smoke_ready_no_quality_claims`

## Boundary

- Compiles and runs `frontend/src/utils/agentflameDisplayModes.ts` under Node.
- Renders R209 display-map/drilldown rows and cross-checks R213/R214 summaries.
- Does not read or mutate raw Codex/Claude traces.
- Does not call an LLM or update the canonical display map.
- Does not exercise a browser DOM or visual click path.

## Mode Summary

| mode | buckets | support | candidates | review rows | review support | active merges | hidden other |
|---|---:|---:|---:|---:|---:|---:|---:|
| `raw` | 1811 | 482398 | 0 | 0 | 0 | 0 | 0 |
| `display` | 1748 | 482398 | 0 | 0 | 0 | 63 | 0 |
| `pending` | 1748 | 482398 | 209 | 323 | 9293 | 63 | 0 |

## Negative Fixtures

| case | observed | pass | reason |
|---|---|---|---|
| `wrong_drilldown_raw_membership` | rejected | True | raw_tags list must match active display-map membership |
| `candidate_display_tag_used_as_active_membership` | rejected | True | pending candidates must not change active display membership |

## Claim Boundary

R215 supports a frontend renderer-model smoke: the TypeScript display-mode consumer compiles, preserves R209 support and membership, keeps pending candidates from changing display membership, and rejects corrupted drilldown membership. It does not support semantic adequacy, merge quality, developer utility, or a browser/DOM renderer claim.

TypeScript compile time: `348.451` ms. Node harness time: `39.167` ms.
