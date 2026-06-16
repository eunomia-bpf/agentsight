# R217 Production React Display-Mode Smoke

Status: `production_react_display_mode_smoke_ready_no_click_or_quality_claims`

## Boundary

- Builds the real Next static frontend.
- Serves a minimal AgentFlame API fixture with R209 display-map and drilldown artifacts.
- Opens `/agentflame` in headless Chrome and checks the production `AgentFlameView` DOM.
- Verifies that the optional display-mode panel renders and preserves the default display-mode support.
- Does not click the production controls, exercise visual drilldown, call an LLM, read raw traces, or update the canonical map.

## DOM Summary

| field | value |
|---|---:|
| default mode | `display` |
| mode buttons | 3 |
| visible buckets | 1748 |
| visible support | 482398 |
| visible candidate overlays | 0 |
| visible review rows | 0 |
| membership matches | True |

## Claim Boundary

R217 supports a production React rendering smoke for the optional display-mode panel in `AgentFlameView`. It does not support click-path interaction, visual drilldown, merge quality, semantic adequacy, developer utility, community adoption, or canonical-map updates.

Frontend build time: `6568.629` ms. Browser run time: `25533.249` ms.
DOM dump bytes: `20644`. Screenshot bytes: `137846`.
