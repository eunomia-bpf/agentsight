# Agent-readable trajectory diagnosis: novelty checkpoint

Date: 2026-07-23

## User decision

The exact-fact benchmark is retained only as a measurement conformance suite.
The immediate goal is to make the trajectory tool useful on real persistent
workspaces: exact code computes process evidence and an Agent reads the compact
evidence to diagnose patterns. Paper-scale comparisons come after the tool
finds consequential patterns in natural long-running work.

## Search

Primary-source searches covered long-horizon Agent diagnosis, Agent-readable
trajectory distillation, runtime graph repair, process mining with an LLM
analyst, harness diagnosis, and workspace-centered traces.

| Work | Primary source | What it occupies |
|---|---|---|
| Agentic Harness Engineering | https://arxiv.org/abs/2604.25850 | “Experience observability”: raw trajectory tokens become layered evidence consumed by an evolving Agent; component- and decision-level harness observability. |
| AgentTether | https://arxiv.org/abs/2607.06273 | Runtime repair using Transition Units, a Critical Transition Graph, normal-behavior modelling, detection, and repair memory. |
| AgentRx | https://arxiv.org/abs/2602.02475 | Failure localization over 115 human-annotated Agent trajectories, with constraint checks and an LLM judge. |
| HORIZON | https://arxiv.org/abs/2604.11978 | More than 3,100 long-horizon trajectories and trajectory-grounded LLM-as-judge diagnosis with human validation. |
| PMAx | https://arxiv.org/abs/2603.15351 | An Agent generates local scripts that compute exact process metrics; a separate Analyst interprets the resulting artifacts. |
| Process Mining to Generate AI Agents from SE Process Records | https://arxiv.org/abs/2607.04948 | Object-centric and declarative/imperative process mining over software-repository records to discover project-specific Agent roles. |
| AgentTrails | https://arxiv.org/abs/2607.18816 | Post-hoc action–artifact provenance, exact and semantic dependency candidates, joined graphs across executions, pattern extraction, skill abstraction, and an LLM copilot. |

Local PDFs were retained as
`docs/reference/2026-agentic-harness-engineering.pdf`,
`docs/reference/2026-zhao-agenttether.pdf`,
`docs/reference/2026-barke-agentrx.pdf`, and
`docs/reference/2026-antonov-pmax.pdf`. The later 2026-07-21 AgentTrails paper is
retained as `docs/reference/2026-agenttrails.pdf`.

## Claim decisions

The following are not defensible novelty claims:

- an LLM can read a trajectory and diagnose a failure;
- a trajectory graph enables detection or intervention;
- raw trajectories can be compressed into Agent-readable evidence;
- observed experience can be used to optimize a harness;
- process mining plus an Agent can produce a process report.
- action–artifact provenance, multi-trace graph alignment, pattern extraction,
  or an LLM provenance copilot are new by themselves.

The surviving, narrower opportunity is **persistent-workspace process
diagnosis**:

> Compute source-linked, cross-session episodes that explain how an Agent
> repeatedly forms, validates, abandons, and resumes persistent artifacts and
> modules, then let an Agent interpret those exact episodes.

The persistent artifact/workspace, not one model call, one task attempt, or one
native session, is the longitudinal object. This distinction still requires
empirical support; it is a development hypothesis, not yet a paper claim.

AgentTrails makes the remaining distinction narrower than this report's first
version. Its exact dependency rule links an entity produced earlier in one
trace to a later action that references it, and its joined graph aligns
multiple trace graphs. The current paper does not center one durable
workspace's artifact state, inspect–mutate–validate strategy, and unresolved
change handoff across independent native sessions. Exact-path access by Agents
rooted in other workspaces remains a useful descriptive relation, but it is not
automatically independent consumption: delegated subagents can both read and
mutate the target workspace. The current highest-value exploratory angle is
therefore persistent-workspace process continuity, not a generic provenance
graph or production–consumption claim.

## Tool design implied by the literature

PMAx provides the right division of labour:

1. deterministic local code computes counts, transitions, intervals, coverage,
   and evidence references;
2. a compact Markdown/JSON brief exposes those facts and candidate episodes;
3. an Agent interprets the evidence, states uncertainty, and proposes the next
   inspection or intervention.

The Agent must not estimate counts or reconstruct path identity from raw text.
Candidate high-value cross-session episodes are:

- inspect–mutate–validate transition structure and mutation bursts;
- mutation state carried across a native-session boundary, with its later
  validation, supersession, or open endpoint;
- pre-mutation inspection by non-overlapping native roots, without calling
  wall-clock span or one long-lived root a restart cost;
- hotspot and module migration between sessions;
- mutations superseded before successful validation;
- repeated modification of one artifact across sessions;
- created or modified artifacts that are never revisited;
- instruction/document writes with little later reuse;
- repeated validation without intervening repository mutation;
- repeated search/read phases with no repository effect;
- return to an old module after a gap;
- temporal association between explicit Skill/instruction use and process
  overhead, without causal language.

Thresholds should be trajectory-relative (rank, quantile, median/MAD, or
change-point evidence), not fixed event counts such as “24 steps.” Every
episode must cite source session/tool identifiers and expose the applicable
coverage denominator.

## Baseline decision

The user-proposed baseline is necessary and strong:

> Give the same fixed Agent the admitted raw native logs and let it retrieve,
> read, and diagnose them directly.

This baseline was exercised on the academic-writing-skills and ActPlane
histories. The Raw Agent recovered semantic phases, user corrections, and
failure context that deterministic counts cannot infer, but required manual
candidate discovery and deep reading of selected multi-gigabyte native stores.
A brief-first Agent reached action-order, cross-session handoff, and hotspot
anchors substantially faster, then used the raw records for interpretation. It
also caught parser and presentation defects. The result is complementary, not
a win claim: the brief contributes exhaustive joins and retrieval anchors; Raw
contributes intent and causal context.

Future comparisons should retain final workspace/Git state, native session
summaries, and aggregate counts. Agent output is not ground truth. Evaluation
must use process conditions known by construction, executable outcomes, or
exact source predicates; a prospective takeover should test whether an Agent
actually reads and acts on the handoff queue.
