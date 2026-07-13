# ToolSafe Cross-Family AgentProf Result

**Execution status:** PASS
**AgentProf:** agentpprof 0.2.37
**Tested hypothesis:** NOT_EVALUATED_PREFLIGHT
**Bootstrap:** 200 attempts supplied; 10,000 valid paired replicates required in the full run (or the requested preflight count).

This experiment profiles the structured judgments of the published TS-Guard detector. It does not claim that AgentProf independently detects unsafe calls or discovers a causal hierarchy.

## Primary: Real Tool Operations, Strict Labels

| Method | AP | Recall @ 30% work | Work to 50% recall | Groups | R@5 groups | Work@5 | Max group share |
|---|---:|---:|---:|---:|---:|---:|---:|
| semantic | 0.855946 | 0.004065 | 0.380204 | 24 | 0.452575 | 0.332100 | 0.326549 |
| risk_tool | 0.917037 | 0.000000 | 0.455134 | 196 | 0.170732 | 0.121184 | 0.043478 |
| risk | 0.917688 | 0.000000 | 0.461610 | 9 | 0.714092 | 0.530065 | 0.329325 |
| exact_tool | 0.607579 | 0.138211 | 1.000000 | 121 | 0.067751 | 0.120259 | 0.073080 |
| causes | 0.727141 | 0.275068 | 1.000000 | 12 | 0.134146 | 0.098982 | 0.510638 |
| interaction | 0.917713 | 0.399729 | 0.385754 | 384 | 0.085366 | 0.058279 | 0.016651 |
| direct | 0.923806 | 0.000000 | 0.461610 | 1081 | 0.006775 | 0.004625 | 0.000925 |

## Paired AP Differences

| Baseline | Mean | 95% CI |
|---|---:|---:|
| semantic - risk_tool | -0.054947 | [-0.077534, -0.033240] |
| semantic - risk | -0.055807 | [-0.080206, -0.035614] |

## Family AP

| Family | Semantic | Risk + tool | Risk only |
|---|---:|---:|---:|
| agentharm | 0.894147 | 0.922491 | 0.922504 |
| asb | 0.962018 | 0.980008 | 0.980008 |
| agentdojo | 0.749704 | 0.746246 | 0.800951 |

## Interpretation Boundary

Strict mode treats controversial and unsafe calls as benchmark-positive triage targets. `metrics.json` also contains mandatory unsafe-only, complete-population, fallback, official-detector, group-size, family, and bootstrap results. Compression never overrides operation-level localization in the verdict.
