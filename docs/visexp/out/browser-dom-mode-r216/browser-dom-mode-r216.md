# R216 Browser DOM Display-Mode Smoke

Status: `browser_dom_mode_smoke_ready_no_quality_claims`

## Boundary

- Compiles `frontend/src/utils/agentflameDisplayModes.ts` as a browser ES module.
- Runs a temporary headless-browser DOM harness over R209 display-map/drilldown rows.
- Programmatically clicks raw/display/pending mode controls and verifies rendered DOM state.
- Saves a DOM dump and screenshot for visual inspection.
- Does not read or mutate raw Codex/Claude traces.
- Does not call an LLM or update the canonical display map.
- Does not exercise the production React `AgentFlameView` or any human task workflow.

## Mode Summary

| mode | buckets | support | candidates | review rows | review support | active merges | hidden other |
|---|---:|---:|---:|---:|---:|---:|---:|
| `raw` | 1811 | 482398 | 0 | 0 | 0 | 0 | 0 |
| `display` | 1748 | 482398 | 0 | 0 | 0 | 63 | 0 |
| `pending` | 1748 | 482398 | 209 | 323 | 9293 | 63 | 0 |

## DOM Checks

| check | observed | pass | reason |
|---|---|---|---|
| `click_raw` | raw | True | mode button updates rendered DOM mode |
| `click_display` | display | True | mode button updates rendered DOM mode |
| `click_pending` | pending | True | mode button updates rendered DOM mode |
| `membership_matches_display_map` | true | True | drilldown raw membership matches active display rows |
| `pending_membership_equals_display` | true | True | pending overlays do not change active membership |
| `wrong_drilldown_rejected` | true | True | corrupted raw membership is rejected |
| `candidate_promotion_rejected` | true | True | candidate display tags cannot become active membership without review |

## Claim Boundary

R216 supports a browser-DOM harness smoke for the frontend display-mode module: a real headless browser renders the raw/display/pending DOM, the mode controls update visible state, pending candidates remain an overlay, and corrupted membership fixtures are rejected. It does not support semantic adequacy, merge quality, developer utility, the production React view, or a visual drilldown/user-study claim.

TypeScript compile time: `447.717` ms. Browser run time: `25415.496` ms.
DOM dump bytes: `636503`. Screenshot bytes: `63374`.
