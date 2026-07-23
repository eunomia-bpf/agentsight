# AgentReward Annotation-Input Audit

## Source Boundary

- Dataset source: `.agentsight/external/agentreward-full`
- Eligible source-only session list: `.agentsight/experiments/agentreward-recursive-diff-v1/source-session-ids.json`
- Sessions: 440
- Operations: 7229
- Provider-reported tokens: 51904621
- Benchmark distribution: `{"assistantbench": 28, "visualwebarena": 153, "webarena": 175, "workarena": 84}`

The materializer opens only the session list and released `cleaned/` trajectory
JSON. It does not open `data/annotations.csv`, a pair file, an evaluation
summary, or any previous pprof.

## Model-Visible Fields

- session: `agent`, `benchmark`, `name`, `source_session`
- prompt: `name`, `text`
- LLM: `name`, `reasoning`, `state_preview`, `url`
- tool: `action`, `evidence_id`, `name`, `visible_error`
- additive measurements: `operations`, `tokens`

The adapter omits `summary_info` wholesale. It never emits expert success,
looping, side-effect, or optimality labels; reward; pair membership; pair side;
pair identifiers; or any derived target verdict.

## Literal Expert-Label Scan

Registered exact strings/aliases:
`Successful`, `Unsuccessful`, `Complete Failure`, `Suboptimal`,
`Somewhat Optimal`, `Yes`, and `No`.

- No model-visible field exactly equals a registered expert-label string.
