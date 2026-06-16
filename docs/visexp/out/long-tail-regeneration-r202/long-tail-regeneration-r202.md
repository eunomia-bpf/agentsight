# R202 Long-Tail Regeneration Smoke

Status: `long_tail_regeneration_smoke_passed`

## Scope

- Reads generated R170 AgentFlame and R189/R196-derived artifacts only.
- Starts or uses a llama.cpp-compatible server for bounded candidate regeneration.
- Does not read or mutate raw Codex/Claude traces.
- Does not update the canonical tag map.
- Does not prove tag adequacy, merge quality, developer utility, or community adoption.

## Result

- Attempted rows: `41`.
- Grammar-valid regenerated one-word candidates: `41`.
- Invalid rows: `0`.
- Valid rows that changed from the raw tag: `32`.
- Valid rows unchanged from the raw tag: `9`.
- Unique valid regenerated tags: `25`.

## Top Regenerated Tags

| tag | rows |
|---|---:|
| `analyze` | 7 |
| `refactor` | 5 |
| `review` | 5 |
| `sync` | 2 |
| `readagent` | 2 |
| `codexnavigate` | 1 |
| `codexanalyze` | 1 |
| `update` | 1 |
| `checkpoint` | 1 |
| `codexread` | 1 |
| `auditrewrite` | 1 |
| `query` | 1 |
| `syncdir` | 1 |
| `validate` | 1 |
| `read` | 1 |
| `search` | 1 |
| `releasecheck` | 1 |
| `estimate` | 1 |
| `refer` | 1 |
| `agentsightr` | 1 |

## Claim Boundary

R202 only proves that the optional llama.cpp regeneration path can produce grammar-valid candidate one-word labels for R196 review rows under the current local setup. Regenerated labels remain review candidates. They cannot support C5 user utility, C6 semantic adequacy, canonicalization quality, or community adoption without the existing human-evidence gates.
