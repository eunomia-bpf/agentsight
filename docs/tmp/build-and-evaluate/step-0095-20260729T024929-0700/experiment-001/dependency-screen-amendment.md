# Dependency-screen amendment

Date: 2026-07-29
Timing: before analyst calls and before ToolSandbox outcomes

The feasibility audit initially reported seven RapidAPI-dependent scenarios
among the registered 37. Direct source inspection against the frozen
ToolSandbox checkout found only five:

- `convert_currency` -> `rapid_api_search_tools.convert_currency`
- `find_address_with_lat_lon` -> `rapid_api_search_tools.search_lat_lon`
- `find_current_city_low_battery_mode` ->
  `rapid_api_search_tools.search_lat_lon`
- `find_stock_symbol_with_company_name` ->
  `rapid_api_search_tools.search_stock`
- `find_stock_symbol_with_company_name_low_battery_mode` ->
  `rapid_api_search_tools.search_stock`

The two holiday scenarios use local
`tool_sandbox.tools.utilities.search_holiday` backed by the pinned `holidays`
package; they do not require RapidAPI. The eligible offline population is
therefore 32, not 30. Removing the one infrastructure-only preflight scenario
leaves 31 outcome scenarios, so the full manifest is
`31 x 8 x 3 = 744` episodes.

This amendment uses declared tool implementations only. No model was called
and no scenario outcome was opened.
