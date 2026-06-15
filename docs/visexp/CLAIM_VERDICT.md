# Claim Verdict: AgentFlame

Last updated: 2026-06-14
Stage at update: claim-gate
Source/command: `.agentsight/agentflame/latest/agentflame.json`
Completeness: partial

| Claim | Verdict | Evidence | Supported wording | Missing evidence |
|-------|---------|----------|-------------------|------------------|
| C1 semantic folded stacks over real histories | supported | 205 readable sessions; 130,632 raw tool events; 167,005 system observations; 24,295 unique semantic stacks; generated dashboard/folded/SVG artifacts. | AgentFlame emits semantic folded-stack artifacts over real local Codex/Claude histories for this repository. | More repositories and one-command artifact package. |
| C2 local one-word tagging feasibility | supported for syntax; partial for adequacy | 93,598 tag requests; 64,297 cache hits; 29,302 llama.cpp HTTP calls; 0 final tag failures; 0 invalid prompt or LLM-call tags. | A local 3B llama.cpp model can produce syntactically valid one-word session/prompt/LLM-call tags at full-history scale. | 0.6B/1B/3B comparison, latency table, human adequacy labels. |
| C3 semantic partitioning beyond baselines | supported | Nonsemantic mixed weight 90.219%; flat mixed weight 90.770%; examples include `git`, `cargo`, `python3`, `docker`, and tool write/process buckets split by semantic tags. | Semantic frames partition system-effect buckets that nonsemantic folded stacks and flat summaries merge in this local workload. | User-task benchmark and stronger case studies. |
| D1 Codex/Claude behavior comparison | diagnostic | Cohort summaries exist for Codex, Claude, and Claude subagents. | The full run can characterize local histories by cohort. | Paired same-task benchmark before making comparative claims. |
| D2 token flamegraphs | diagnostic | Token projections exist and preserve total token weights. | Token views provide source-local accounting. | Token normalization across agents/models. |
| C4 exact AgentSight effect lineage | partial | R110 live smoke over 3 real AgentSight DB exports: 8 detected agent roots, 8 synthetic sessions/tools, 318 raw effects, 182 covered and joined, 136 out of scope, 57.233% raw coverage, 182/182 in-scope join, 0 orphans. R111 moves the envelope into native `collector report export`: 3 exported sessions/tools, 182/318 raw effects joined, 136 orphans, 57.233% raw join. R112 persists those envelopes into SQLite `sessions`/`tool_calls` rows on DB copies and verifies persisted-only export: 3 DB sessions/tools, 182/318 raw effects joined, 136 orphans, 57.233% raw join. R113 implements capture-time `record -- <command>` session/tool rows and verifies 1 session + 1 tool row in a temp SQLite DB. | AgentFlame's C4 checker can validate live AgentSight effects when an agent-run envelope links root processes to prompt ancestry; native export, DB-persisted backfill, and capture-time record-command rows now carry that envelope shape. | Fresh live R113 tasks, lower orphan share, child-depth/path/domain/redaction analysis, per-effect direct ancestry ids. |
| C5 developer utility | unsupported | Task packet/scorer prototypes exist; no participant responses. | No user-outcome claim should be made yet. | Scored task benchmark with time, accuracy, false positives, and confidence. |
| C6 tag adequacy/stability | partial | 0 malformed tags in the full 3B run; noisy tags remain. | One-word tags are usable as syntactic navigation frames. | Human adequacy labels, repeated-run stability, and smaller-model comparison. |

## Current OSDI Readiness

Verdict: promising but not OSDI weak accept yet.

The work has a credible mechanism and a real full-history characterization, but
two central systems-paper gaps remain:

1. The strongest system novelty, exact semantic-effect lineage, is still only
   shown as smoke evidence: R113 implements capture-time record-command rows,
   but the latest live join remains R112's 57.233% raw join with 136 orphans.
2. The strongest user-value claim has no scored user/task benchmark.

## Paper Wording Rule

The paper may claim C1-C3 as current mechanism results, D1-D2 as diagnostics,
and C4 as a partial live smoke. It must present C5-C6 as unsupported or partial.
Any draft wording that claims native exact capture, user utility, or semantic
correctness is too strong for the current evidence.
