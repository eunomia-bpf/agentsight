# Evaluation Frontier

## Current research contract

The active study asks whether days of Agent activity become durable,
reuse- and validation-associated artifact progress, how rework and continuity
evolve across session boundaries, and what additional source-verifiable facts
artifact identity and lineage make measurable. It does not require an
intervention to improve the Agent.

Event time from native Agent actions is authoritative. Git contributes final
state, tracked-file, optional content-survival, and milestone evidence; it does
not define the timeline. Human labels, expert adjudication, and an LLM judge as
truth remain excluded. The full Chinese study contract is
`docs/empirical-study.zh-CN.md`.

## Open research questions

| RQ | Evidence required | Status | Next decisive action |
|---|---|---|---|
| RQ1 activity to artifact progress | For all qualified sessions in six projects, relate actions and mutations to final artifact survival, later reuse, successful-validation distance, and their intersection; report source coverage and per-project distributions. | Open; literature grounded, extraction not yet run. | Complete a reviewed six-project extraction and RQ1 analysis. |
| RQ2 validation dynamics | Mutation bursts, successful/failed validation cadence, mutation-to-validation event/time distance, and unvalidated backlog by artifact type and project. | Open. | Use the same frozen trace corpus in a separately reviewed analysis after RQ1. |
| RQ3 rework and convergence | Artifact-level repeated mutation, read-write-validate sequences, validation-followed rework, delete/replace, and module switching with threshold sensitivity. | Open. | Freeze definitions after RQ1 coverage audit; do not invent one thrash cutoff. |
| RQ4 cross-session continuity | Actions before first mutation, prior-hotspot/artifact overlap, module continuation, and cross-session rework at every eligible session boundary. | Open. | Qualify true native session identity and parallel-session handling, then run boundary-aligned analysis. |
| RQ5 attention and artifact allocation | Action-time allocation across code, test, config, paper/docs, data/results and module transition/hotspot migration. | Open. | Freeze path classification with unknown retained; compare projects as cases, not independent population samples. |
| RQ6 skill/harness association | Source-visible skill/config invocation followed by action, artifact, validation, rework, and survival patterns, with coverage and confounds. | Open; causal claims prohibited for local cases. | Audit explicit skill/config coverage before admitting analysis. |
| RQ7 tool measurement | Stratified source-verifiable fact accuracy, coverage, evidence precision, abstention, tokens/bytes/latency for Final State, Counts, official ProcGrep, bounded Raw-log LLM, and artifact-linked trajectory. | Open; ProcGrep `2e8277003d...` qualified as strongest action-only baseline. | Build the fact set after RQ1 source coverage is known; include action-only questions where ProcGrep should tie or win. |

## RQ1 selected experiment

**Question.** Across the complete set of repository-direct Claude, Codex, and
Gemini sessions for AgentSight, ActPlane, bpf-developer-tutorial, eunomia.dev,
agentskill-observability-paper, and academic-writing-skills, how much action
volume is associated with artifact durability, later reuse, and subsequent
successful validation?

**Primary outputs are a vector, not a weighted score:**

1. source and field coverage by project, vendor, session, action and effect;
2. final tracked existence for observed creates and paths;
3. later read/write reuse and event/session distance;
4. mutation-to-next-successful-validation distance and unvalidated backlog;
5. the conjunction of observable durability, reuse, and validation association;
6. per-project and cross-case distributions, with sensitivity over complete
   horizons rather than one fixed event window.

The first run may retain fields needed by later RQs, but it cannot claim to
answer RQ2--RQ7. File-level survival is reported separately from content-level
survival. A successful validation is associated with preceding mutations; it
does not prove coverage or correctness of each change.

## Corpus and inclusion contract

| Project | Main role | Required identity evidence |
|---|---|---|
| AgentSight | systems/research | native cwd, worktree root, or matching Git remote |
| ActPlane | systems/research | same |
| bpf-developer-tutorial | tutorial/code/docs | same |
| eunomia.dev | content/software | same |
| agentskill-observability-paper | auto research | same |
| academic-writing-skills | skill/harness development | same |

Main analyses retain complete repository-direct sessions, including Tool
actions with no resolved path. Global path-search events are a separate
sensitivity source because their surrounding no-file actions are unavailable;
they cannot enter validation cadence or session-reset denominators.

All source-native failed calls remain activity records but contribute no
successful file effect. Missing timestamp, cwd, effect, status, or path is
reported in coverage rather than silently imputed. Artifacts under dependencies
and build caches excluded by the visualization path policy remain excluded and
are reported as such.

## RQ1 operational checks

- Artifact durability uses final tracked/existing state and explicit native
  lifecycle effects. Content survival is absent unless source diffs, snapshots,
  or Git line evidence can independently establish it.
- Reuse requires a later source-linked access to the same artifact lineage.
- Validation association uses `agent-session`'s source-native command effect
  plus successful status. Unknown status is not converted to success.
- Every statistic is recomputable from exported project rows and source IDs.
- Results remain separate by project. Any pooled summary weights projects
  explicitly and cannot treat actions as independent projects.
- Confidence intervals or bootstrap use session/project blocks only where the
  exchangeability assumption is defensible.

## RQ7 baseline contract

| Method | Competing position | Matched-run role |
|---|---|---|
| Final workspace/diff | Process history is unnecessary for the fact. | Lower-information control; expected to answer final-state facts only. |
| Aggregate Counts | Activity telemetry is an adequate process description. | Lower-information control; expected to answer count questions only. |
| ProcGrep official action spine | Canonical action procedures are sufficient for trajectory measurement. | Strongest external baseline; expected to tie/win action-only questions. |
| Bounded Raw-log LLM | A model can reconstruct the same facts on demand from source records. | Requested comparison; same source membership and fixed retrieval/context/output budget. |
| Artifact-linked trajectory | Stable artifact identity and cross-session lineage add factual coverage. | Proposed method; must cite the same underlying source universe. |

Ground truth consists only of independently generated source-verifiable facts
from native records and workspace/Git state. The method under test cannot define
its own truth. Correct abstention is scored when the sources do not establish a
fact.

## Superseded intervention program

The earlier H6 program compared No Intervention, Generic, Full Raw Retrieval,
and Workspace Trajectory Retrieval through executed benchmark continuations.
It is closed without a treatment inference because the author removed the
improvement question.

The completed Harness Bench dependency run remains valid mechanics evidence:
task 058 exercised checkpoint/fork/continue/oracle mechanics, but all
supervisors made zero evidence calls. The fixed six-task headroom gate admitted
only 3/6 tasks and stopped the matrix. A later SWE-INTERACT plan received a
blocking review and made no benchmark or model call. These artifacts are
historical evidence, not the active evaluation:

- `docs/tmp/bootstrap/step-0001-20260719T181243-0700/experiment-20260721T021426-0700/`
- `docs/tmp/bootstrap/step-0001-20260719T181243-0700/experiment-20260721T212000-0700/`

## Current evidence and reports

- Study design: `docs/empirical-study.zh-CN.md`
- Current literature boundary:
  `docs/tmp/bootstrap/step-0001-20260719T181243-0700/literature-20260721T235934-0700/literature-report.md`
- Active BOOTSTRAP step:
  `docs/tmp/bootstrap/step-0001-20260719T181243-0700/step-report.md`
- Visualization design: `docs/repository-nebula.zh-CN.md`

No RQ currently has a complete reviewed result. Missing values, distributions,
and figures remain hypotheses until a real full run and independent result
review complete.
