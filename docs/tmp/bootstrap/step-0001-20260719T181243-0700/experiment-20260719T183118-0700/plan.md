# Experiment Plan: RQ1 Matched-Budget Workspace Diagnosis

## Research Question

- **RQ exactly as written in the paper:** Under fixed model and budget, does a queryable workspace-centered action trajectory improve automatic or supervisor-agent classification of progress, stagnation, drift, missing validation, and intervention need, including localization of supporting action evidence, over final artifacts, session summaries, and linear logs?
- **Specific uncertainty tested here:** Whether a workspace-centered organization of the same native evidence makes cross-session process states more diagnosable to a fixed-budget supervisor Agent than competent retrieval over raw logs.
- **Why the answer matters:** Generic automatic trajectory diagnosis already exists. The remaining value is a testable oversight claim about inductive bias and bounded-compute accessibility, not a claim that deterministic projection creates new information.

## Paper-Value Admission

- **Planned role:** decisive pilot for RQ1.
- **Largest credible paper story this experiment could unlock:** process-level scalable oversight benefits from treating persistent workspace evolution as evidence, not only task outputs or textual execution traces.
- **Strongest reviewer reject argument or load-bearing uncertainty addressed:** a strong LLM with raw-log search can reconstruct everything; any gain comes from truncating or handicapping that baseline.
- **Independent evidence added beyond existing runs and published results:** matched diagnosis of cross-session, successful-but-pathological natural work using source-linked artifact effects, a setting not directly evaluated by AgentRx, TrajAudit, AgentForesight, or HarnessFix.
- **Why the result is not tautological, already settled, or dominated:** the trajectory is deterministic and contains no generated diagnosis labels; the raw-log Agent sees the same underlying actions and can search them. A null result is plausible and would remove the proposed representation as an accuracy contribution.
- **Paper decision if positive:** retain workspace evolution as the central mechanism and scale the corpus, including non-coding workspaces.
- **Paper decision if contradictory, mixed, or inconclusive:** if raw logs match, narrow to efficiency only if cost improves; if counts match, reject the central representation claim; if evidence is incomplete, prioritize system-evidence binding before diagnosis.
- **Best alternative experiment and why this one has higher decision value:** a larger visualization or behavior-correlation study is easier but cannot distinguish the proposed mechanism from existing trajectory metrics. This direct matched diagnostic comparison attacks the central uncertainty.

## Expected And Alternative Outcomes

- **Current expected answer:** trajectory access improves the unique headline metric, diagnosis macro F1, while keeping evidence localization grounded. Accuracy-equivalent cost reduction is a separately predeclared secondary efficiency outcome.
- **Strongest competing explanation:** raw logs with chronological search are sufficient; deterministic workspace structure merely exposes the answer in a more convenient format.
- **Result that would contradict the expectation:** raw logs or simple counts match the trajectory on held-out diagnosis/evidence metrics with comparable or lower cost.

## Published Precedent And Real Assets

- **Closest published protocol:** AgentRx for critical-step/category diagnosis; TrajAudit/RootSE for tool-using repository-trace investigation and exact/tolerant localization; Cross-Session Threats for session-local versus aggregate evidence under an information bottleneck.
- **Official system/model/data/benchmark/tool and version:** local source-native `agent-session`/`agentvis`, fingerprinted by Git HEAD plus SHA-256 hashes of the modified source and release binary in every raw run; Claude Code 2.1.215 with `claude-sonnet-4-6` for every diagnosis condition; RootSE/AgentRx cited as external precedents rather than forced onto incompatible success-with-pathology labels.
- **What is reused:** native trace parsing, repository effect projection, source logs, macro F1, evidence precision/recall, and exact/tolerant evidence localization.
- **Necessary deviations or custom glue:** shell commands extract one reviewed time interval from existing output and present either native logs or deterministic workspace events. `RepositoryEvent` now preserves the native `ToolEvent.call_id` as optional `source_call_id`; this is source provenance already parsed by `agent-session`, not a new event model or semantic label. A small `jq` scorer computes the frozen preflight metrics from adjudicated gold and unmodified model JSON.

## Comparison

- **Proposed system or method:** supervisor Agent with read-only `jq`/source retrieval over an ordered, cross-session workspace event file containing artifact create/read/write/rename/delete effects and source action IDs.
- **Main baseline 1 — matched raw-log retrieval:** same supervisor Agent with direct access to the complete native session files plus `rg`, `jq`, and chronological listing. It represents the strongest competing position that structure adds no information beyond retrieval.
- **Main baseline 2 — native session final reports:** same supervisor Agent sees the last top-level assistant report from each parent session, with timestamps and session IDs. This deterministic, source-native condition represents current handoff/status-report practice without a separate summarizer model.
- **Why matched runs are required:** published work does not compare these representations on the same cross-session natural work, labels, model, and budget.
- **Controls:** final artifact/outcome only; the same supervisor Agent reading deterministic counts of actions, tokens, sessions, artifacts, statuses, duration, agent/model, and outcome. Counts cannot support evidence localization, so they are scored only on pathology labels. Component ablations move to the later RQ2 experiment rather than being conditionally run here.
- **Conclusion if a baseline matches or wins:** raw-log parity rejects an accuracy claim but may leave a cost claim; summary parity rejects the need for fine-grained trajectory access; count parity rejects the structural mechanism.
- **Information, tuning, and compute fairness:** raw and trajectory conditions cover the identical frozen session IDs, time range, semantic source text, tool results, and workspace outcome evidence. Both may retrieve native source records and cite the same canonical `<session_id>#<source_call_id>` identifiers. The trajectory additionally exposes only the tested deterministic artifact lifecycle/index. Both use `claude-sonnet-4-6`, the same prompt, a `$0.50` per-run cap, read-only tools, an instruction limit of eight evidence queries, and the same stopping rule. Actual tokens, tool calls, bytes returned, failures, and latency are recorded from `stream-json`; a run exceeding eight evidence queries is invalid for both conditions. Preprocessing uses no LLM. One query may return at most 200 lines in either condition so a structured query cannot hide unbounded retrieval.
- **Split or leakage rule:** `annotation-guide.md` freezes goal episodes, labels, and scoring. Goal boundaries are decided before pathologies. The exact cohort is selected without labels by hashing the recorded workspace/start/session-ID tuple. Prompt development uses four separate development episodes; the 40 test episodes remain unread by prompt authors until prompts are frozen. Annotation Agents do not serve as the tested supervisor model.

## Workloads And Metrics

- **Real workloads or tasks:** real preflight on one strictly bounded AgentSkill `/check-paper-citations` episode. It starts at the top-level skill invocation (`2026-07-12T04:40:23.535Z`) and ends immediately before the next top-level user goal (`2026-07-12T04:58:31.093Z`). It contains one parent and three spawned subagent records, 115 Tool actions, and 41 file effects. No later paper-ideation or skill-editing action is admitted. The coding pilot has exactly 40 held-out goal episodes: 20 each from complete AgentSight and ActPlane direct sessions, selected by the lowest SHA-256 values after the goal-boundary and minimum-evidence rules in `annotation-guide.md`. Four additional episodes, two per workspace, are selected by the next hash values for prompt development. Non-code generalization is explicitly deferred to RQ3 and is not a success condition for this RQ1 pilot.
- **Primary metrics:** the unique headline metric is pathology macro F1 for trajectory versus matched raw-log retrieval. Evidence F1 is a grounding veto. Exact/tolerant action localization, intervention-recommendation agreement, cost, and latency are secondary as defined in `annotation-guide.md`.
- **Correctness check or ground truth:** two independent annotators inspect complete native traces, workspace history, and task outcomes without tested-condition outputs, then report pre-adjudication agreement and adjudicate. Naturalistic intervention labels are recommendation agreement, not correctness; outcome-backed correctness is reserved for later replay/injection cases.
- **Repetitions, seeds, and uncertainty:** three diagnosis repetitions per condition; repetitions are averaged within episode before paired 10,000-sample episode bootstrap confidence intervals. The hosted CLI exposes no seed, so model/version and all raw outputs are retained.
- **Cost estimate when material:** preflight is capped at two annotation passes and three diagnosis conditions on one episode; the full run's cost is measured from preflight before expansion.

## Planned Runs

| Run group | Role | Workload | System/method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| preflight-label | correctness dependency | one AgentSkill citation-verification goal episode | two independent full-evidence annotators plus adjudication | 1 pair | Confirms a label/evidence path; not a paper result. |
| preflight-main | proposed/baseline | same episode | workspace trajectory; raw-log retrieval; session summaries | 1 each | Verifies real end-to-end execution and mechanism engagement. |
| pilot-main | proposed/baseline | 40 frozen test goal episodes | workspace trajectory; raw-log retrieval; native session final reports | 3 each | Decisive comparison for RQ1. |
| pilot-controls | control | same 40 episodes | same supervisor over final/outcome evidence or deterministic counts | 3 each | Tests whether outcome or volume explains pathology classification. |

## Execution

- **Authoritative workflow:** from the research worktree, run the exact preflight commands in `preflight-commands.md`. They generate direct-session HTML using the existing `agentvis`, extract the embedded event object with a fixed `perl` expression, create the frozen AgentSkill goal interval with `jq`, and invoke Claude Code 2.1.215 with `claude-sonnet-4-6` in read-only mode. Raw logs are addressed by four exact session paths; trajectory queries use `jq` over the identical session/time subset and may follow canonical source IDs back to those paths. `stream-json --verbose` retains all tool calls and usage for budget auditing, and `score-preflight.jq` is the executable scoring endpoint.
- **Real preflight case:** the 2026-07-12 AgentSkill `/check-paper-citations` episode, containing the parent record and exactly the three citation-search subagents spawned before the next user goal.
- **Full completion rule:** every frozen episode has ground truth; every planned condition/repetition terminates or is retained with failure reason; metrics are recomputed from raw predictions; no partial prefix is reported as the pilot.
- **Raw-result path:** `docs/tmp/bootstrap/step-0001-20260719T181243-0700/experiment-20260719T183118-0700/raw/` for lightweight prompts, predictions, and metrics; large native traces remain at their source paths and are referenced rather than copied.
- **Checkpoint or recovery approach:** one output file per episode/condition/repetition; completed outputs are immutable for analysis, and systematic runner changes rerun all affected cells.

## Interpretation

- **Positive result:** the trajectory-minus-raw macro-F1 gain is at least 0.10, its paired bootstrap lower bound exceeds zero, and evidence F1 is no more than 0.05 below raw. Proceed to the broader AAAI evidence program.
- **Negative or contradictory result:** raw logs or counts match/win. Remove the diagnostic-accuracy claim. Retain only the predeclared efficiency result if macro F1 is non-inferior within -0.05 and median model tokens fall by at least 25%; otherwise stop this mechanism direction.
- **Mixed or inconclusive result:** report domain/pathology boundaries; do not average away coding versus auto-research or failed versus successful-but-pathological differences.
- **Target paper figure or table:** paired condition table for diagnosis/evidence/cost plus an ablation plot of incremental workspace components.

## Reproducibility Notes

- **Software and data versions:** repository revision and exact native session paths recorded with each episode; hosted model identifier recorded verbatim.
- **Config and seed notes:** prompts and output shape frozen before full run; hosted-model stochasticity handled by repetitions rather than claiming a hidden seed.
- **Known deviations:** the preflight is a single local goal and is dependency evidence only; the RQ1 pilot is coding-only, with non-code generalization assigned to RQ3; `--global` line-selected sessions are excluded.
