# ToolSafe Cross-Family AgentProf Result

**Execution status:** PASS
**AgentProf:** agentpprof 0.2.37
**Tested hypothesis:** CONTRADICTED
**Bootstrap:** 10000 attempts supplied; 10,000 valid paired replicates required in the full run (or the requested preflight count).

This experiment profiles the structured judgments of the published TS-Guard detector. It does not claim that AgentProf independently detects unsafe calls or discovers a causal hierarchy.

## Primary: Real Tool Operations, Strict Labels

| Method | AP | Recall @ 30% work | Work to 50% recall | Groups | R@5 groups | Work@5 | Max group share |
|---|---:|---:|---:|---:|---:|---:|---:|
| semantic | 0.930871 | 0.233705 | 0.321839 | 30 | 0.192601 | 0.097554 | 0.314618 |
| risk_tool | 0.892672 | 0.534645 | 0.282051 | 826 | 0.034058 | 0.018126 | 0.039051 |
| risk | 0.891822 | 0.241926 | 0.304892 | 9 | 0.557839 | 0.304892 | 0.350722 |
| exact_tool | 0.486844 | 0.242220 | 0.989979 | 525 | 0.069583 | 0.041261 | 0.041114 |
| causes | 0.850515 | 0.094245 | 0.322281 | 12 | 0.615678 | 0.322281 | 0.319187 |
| interaction | 0.758938 | 0.323547 | 0.391394 | 3326 | 0.018790 | 0.009431 | 0.002653 |
| direct | 0.920246 | 0.467704 | 0.506631 | 6786 | 0.001468 | 0.000737 | 0.000147 |

## Paired AP Differences

| Baseline | Mean | 95% CI |
|---|---:|---:|
| semantic - risk_tool | 0.029228 | [-0.005450, 0.058494] |
| semantic - risk | 0.030343 | [-0.004953, 0.060037] |

## Family AP

| Family | Semantic | Risk + tool | Risk only |
|---|---:|---:|---:|
| agentharm | 0.865998 | 0.864149 | 0.867093 |
| asb | 0.949481 | 0.950302 | 0.950302 |
| agentdojo | 0.904165 | 0.812525 | 0.844164 |

## Interpretation Boundary

Strict mode treats controversial and unsafe calls as benchmark-positive triage targets. `metrics.json` also contains mandatory unsafe-only, complete-population, fallback, official-detector, group-size, family, and bootstrap results. Compression never overrides operation-level localization in the verdict.
