# Claim Verdict: Semantic Tag Flamegraphs

Last updated: 2026-06-14
Stage at update: claim-gate
Source/command: `docs/visexp/out/evaluation.json`, `docs/visexp/out/pipeline-report.json`
Completeness: partial

| Claim | Verdict | Evidence | Supported wording | Missing evidence |
|-------|---------|----------|-------------------|------------------|
| C1 folded aggregation | supported | 5312 observations collapse to 2270 semantic system stacks; verifier passes. | The prototype emits internally consistent folded stack artifacts over real local sessions. | Broader workloads and live exact-effect input. |
| C2 one-word tags in stack grammar | supported | 38 unique prompt tags, 0 invalid prompt tags, 0 same-hash conflicts; 30 uncached local Qwen tag calls succeeded and the remaining requests hit cache. | One-word local tags can be inserted into session, prompt, and LLM-call stack frames. | Manual adequacy labels and larger uncached model comparison. |
| C3 semantic stacks add information beyond baselines | supported | Nonsemantic mixed observation share is 68.505%; flat mixed observation share is 74.473%. | Semantic frames partition task/session mixtures hidden by ordinary folded or flat process/effect summaries in this local workload. | User task validation and more repositories. |
| C4 normalized agent differences | diagnostic | Agent-diff rows exist across Codex/Claude and top/subagent cohorts. | Normalized stack diff is useful as an exploratory diagnostic in local histories. | Paired same-task Codex-vs-Claude benchmark. |
| C5 user utility over trace/process logs | unsupported | Task bundle, answer key, participant packets, response template, and scorer exist. No participant responses. | No user-utility improvement claim should be made yet. | Scored participant CSV with time, accuracy, confidence, false positives. |
| C6 exact AgentSight effect stream preserves value | unsupported | Fixture lineage checker joins 4/4 effects and emits exact-effect folded stacks. | The exact-effect checker and stack grammar work on an AgentSight-shaped fixture. | Live AgentSight snapshots from real sessions with tool/process/file/network events. |
| C7 tag stability and adequacy | partial | Repeated-run smoke stability passes and invalid rate is 0; generic prompt share is 35.987%. | Current tags are syntactically stable navigation hints, not a validated task ontology. | Manual adequacy labels, larger model comparison, lower generic rate. |

## Paper Wording Rule

The current paper draft may claim C1-C3 as artifact-level results and C4 as a
diagnostic. It must present C5 and C6 as planned or partial evidence, not as
completed proof. If the draft uses words such as "proves user utility" or "live
exact capture", it violates this verdict.
