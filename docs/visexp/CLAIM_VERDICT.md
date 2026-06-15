# Claim Verdict: AgentFlame

Last updated: 2026-06-15
Stage at update: claim-gate
Source/command: `.agentsight/agentflame/latest/agentflame.json`
Completeness: partial

| Claim | Verdict | Evidence | Supported wording | Missing evidence |
|-------|---------|----------|-------------------|------------------|
| C1 semantic folded stacks over real histories | supported | 205 readable sessions; 130,632 raw tool events; 167,005 system observations; 24,295 unique semantic stacks; generated dashboard/folded/SVG artifacts. | AgentFlame emits semantic folded-stack artifacts over real local Codex/Claude histories for this repository. | More repositories and one-command artifact package. |
| C2 local one-word tagging feasibility | supported for 3B syntax and real-fragment latency; partial for model-size coverage/adequacy | 93,598 tag requests; 64,297 cache hits; 29,302 llama.cpp HTTP calls; 0 final tag failures; 0 invalid prompt or LLM-call tags. R123 used the local 3B llama.cpp server over 300 real redacted fragments, 3 identical repeats each: 900/900 valid tags, 1002 ms load, request latency min/p50/p95/max = 7/11/30/67 ms. | A local 3B llama.cpp model can produce syntactically valid one-word session/prompt/LLM-call tags at full-history scale and low per-fragment latency on a 300-fragment real redacted sample. | Real 0.6B/1B weights were not available locally; human adequacy labels remain missing. |
| C3 semantic partitioning beyond baselines | supported | Nonsemantic mixed weight 90.219%; flat mixed weight 90.770%; examples include `git`, `cargo`, `python3`, `docker`, and tool write/process buckets split by semantic tags. R131 preserved totals, matched `agentflame.json` report totals, and exactly matched already generated folded projections. In R131, no-semantic system stacks mix 90.219% of full semantic bucket weight with 44.639% residual; session-only leaves 84.180% / 34.138%; prompt-only leaves 37.687% / 7.526%. Full session+prompt leaves 0.000% by construction. | Semantic frames partition system-effect buckets that nonsemantic folded stacks and flat summaries merge in this local workload; prompt tags carry most of the system-effect separation, while session tags add remaining provenance context. | User-task benchmark and stronger case studies. |
| D1 Codex/Claude behavior comparison | diagnostic | Cohort summaries exist for Codex, Claude, and Claude subagents. | The full run can characterize local histories by cohort. | Paired same-task benchmark before making comparative claims. |
| D2 token flamegraphs | diagnostic | Token projections exist and preserve total token weights. | Token views provide source-local accounting. | Token normalization across agents/models. |
| C4 exact AgentSight effect lineage | supported for fixed command-mode suite; partial broadly | R110 live smoke over 3 real AgentSight DB exports: 8 detected agent roots, 8 synthetic sessions/tools, 318 raw effects, 182 covered and joined, 136 out of scope, 57.233% raw coverage, 182/182 in-scope join, 0 in-scope orphans. R111 moves the envelope into native `collector report export`: 3 exported sessions/tools, 182/318 raw effects joined, 136 orphans, 57.233% raw join. R112 persists those envelopes into SQLite `sessions`/`tool_calls` rows on DB copies and verifies persisted-only export: 3 DB sessions/tools, 182/318 raw effects joined, 136 orphans, 57.233% raw join. R113 implements capture-time `record -- <command>` session/tool rows and verifies 1 session + 1 tool row in a temp SQLite DB. R113-live runs 5 real `codex exec` tasks under `agentsight record`: 5/5 capture-time sessions/tools, 508 raw effects, 508 joined, 0 orphans, 100.0% raw join. Initial R114-smoke exposed the precision flaw: 302/302 wrapper negative-control effects were attributed. After `--agent-comm codex`, missing-root child fallback, per-task negative marker bursts, and scoped oracle accounting, full R114 ran 20 real Codex tasks: 20/20 targets completed, 20/20 tasks observed negative controls, 1273/1273 in-scope effects joined, 100.0% precision, 100.0% recall, 3170 negative-control effects observed with 0 joined, child-depth/path/redaction analysis generated, and raw join remained 22.055% because out-of-scope effects stayed orphaned. | AgentFlame can validate exact semantic-effect lineage for a fixed command-mode Codex suite by linking prompt/tool ancestry to the actual agent process family while rejecting concurrent negative controls. | Cross-repo/full-history exact integration, more agent types, network-effect cases, and user-task evidence. |
| C5 developer utility | unsupported | Task packet/scorer prototypes exist; no participant responses. | No user-outcome claim should be made yet. | Scored task benchmark with preregistered effect-size thresholds, time, accuracy, false positives, confidence, and paired or mixed-effects analysis. |
| C6 tag adequacy/stability | partial | 0 malformed tags in the full 3B run; noisy tags remain. R122 created a redacted 300-fragment label packet. R123 found 282/300 exact-stable real redacted fragments (94.000%) over 3 identical repeats with 0 invalid outputs. | For the available 3B model, one-word tags are syntactically valid and mostly stable on this real redacted fragment sample. | Human adequacy labels with explicit adequate/generic/misleading rubric, smaller-model comparison, and agreement thresholds. |

## Current OSDI Readiness

Verdict: promising but not OSDI weak accept yet.

The work has a credible mechanism and a real full-history characterization, but
two central systems-paper gaps remain:

1. The strongest system novelty, exact semantic-effect lineage, now has a
   passing fixed command-mode suite with negative controls, but not a
   full-history or cross-repo benchmark.
2. Semantic-axis ablation now supports the mechanism story, but the strongest
   user-value claim has no scored user/task benchmark, and tag
   adequacy/stability is still incomplete.

## Paper Wording Rule

The paper may claim C1-C3 as current mechanism results, D1-D2 as diagnostics,
and C4 for the fixed command-mode suite. It must present C5-C6 as unsupported
or partial. Any draft wording that claims broad native exact capture, user
utility, or semantic correctness is too strong for the current evidence.
