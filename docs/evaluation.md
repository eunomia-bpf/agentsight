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

## Research questions and current evidence

| RQ | Evidence required | Status | Next decisive action |
|---|---|---|---|
| RQ1 activity to artifact progress | For all qualified sessions in six projects, relate actions and mutations to final artifact survival, later reuse, successful-validation distance, and their intersection; report source coverage and per-project distributions. | Reviewed six-project run complete. Reuse is measurable in 6/6; persistence and recognized validation are coverage-only at 3/6. | Preserve reviewed F3/F4 while extending the frozen corpus to later RQs. |
| RQ2 validation dynamics | Recognized successful/failed validation cadence and complete worktree-local inter-success mutation intervals. | Independently reviewed F5 complete for 3/6 source-covered projects; cross-case gate stopped. | Improve validation adapters before making a six-case cadence claim. |
| RQ3 repeated-mutation structure | First/repeat-observed mutation episodes, per-identity load, exact concentration, and action-atomic prefix evolution. | Independently reviewed F6 complete for all six cases. | Keep convergence, validation-followed revision, module switching, failure and waste interpretations open. |
| RQ4 source-session continuity | Adjacent non-overlapping concurrency components, mutation-observed prefixes, artifact/module overlap and first-mutation state. | Independently reviewed F7 complete as coverage/within-case evidence; every four-project estimator gate stopped. | Capture portable source-session roles before estimating reset/resumption effects. |
| RQ5 workspace activity allocation/migration | Path-resolved action/call allocation, same-artifact/same-module/cross-module transitions and return gaps. | Independently reviewed F8a/F8b complete; five cases pass the return gate and one remains N/A. | Preserve status sensitivity; do not reinterpret action order as attention or duration. |
| RQ6 skill/instruction source coverage | Exact Skill Tool and instruction-file source signals by session, vendor, status and action-order bin. | Independently reviewed F9 complete; missing exposure-defining fields stop every association/effect analysis. | Capture Skill name/arguments, model/config, external instructions and actual non-exposure prospectively. |
| RQ7 matched-comparison readiness | Immutable normalized/native source universes, cutoff worktree state, pinned method interfaces and an independent oracle contract. | Independently reviewed F10 complete: 12 present, 0 partial and 24 N/A source-contract cells; matched comparison stopped before questions or method calls. | Prospectively freeze the missing contracts before attempting the separate capability comparison. |

## RQ1 selected experiment

**Question.** Across the complete set of repository-direct Claude, Codex, and
Gemini sessions for AgentSight, ActPlane, bpf-developer-tutorial, eunomia.dev,
agentskill-observability-paper, and academic-writing-skills, how much action
volume is associated with introduced-artifact persistence, later reuse, and
adapter-recognized validation before supersession?

**Primary outputs are a vector, not a weighted score:**

1. source and field coverage by project, vendor, session, worktree, action and
   effect, separating admitted from worktree-attributed activity;
2. final tracked existence for observation-born artifact introductions;
3. later read/write reuse and event/session distance;
4. mutation-to-recognized-validation distance before the same artifact's next
   mutation/delete, with competing outcomes and censoring explicit;
5. the conjunction for eligible observation-born introduction episodes;
6. per-project and cross-case distributions, with sensitivity over complete
   horizons rather than one fixed event window.

The first run may retain fields needed by later RQs, but it cannot claim to
answer RQ2--RQ7. Existing-file writes have unknown content durability and do
not enter the persistence numerator. A recognized successful validation is
associated with a preceding mutation only when it occurs before that artifact
is superseded; it does not prove coverage or correctness of the change.

**Reviewed outcome.** The authoritative cutoff admits 2,049 native sessions and
206,249 Tool actions; 1,825 sessions and 175,850 actions are worktree-attributed.
The extraction yields 7,154 observed artifact identities and 13,152 confirmed
mutation rows. All six projects pass the longitudinal gate. Later reuse is
observed for 89.80--97.26% of eligible mutations, while its descriptive
association with action volume is Spearman rho 0.0857. Only three projects have
an eligible confirmed create and recognized successful validation, so the
preregistered gate stops cross-case persistence and validation interpretation.
The independent result audit regenerated both figures byte-identically.

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

All failed calls remain activity records but contribute no confirmed-success
file effect. Missing timestamp, cwd, effect, status, or path is
reported in coverage rather than silently imputed. Artifacts under dependencies
and build caches excluded by the visualization path policy remain excluded and
are reported as such.

## RQ1 operational checks

- Introduced-artifact persistence uses final tracked/existing state only for
  observation-born introductions in the same worktree. Existing-file writes
  have unknown content durability unless source diffs, snapshots, or Git line
  evidence independently establish it. Missing or unqueryable worktrees yield
  unknown final state and are excluded rather than counted as absent.
- Reuse requires a later source-linked access to the same artifact lineage.
- Validation association uses `agent-session`'s adapter-derived recognized test
  effect plus `status == ok`, before the same artifact's next mutation/delete.
  Unknown status or unrecognized validation is not converted to failure or
  success.
- Every statistic is recomputable from exported project rows and source IDs.
- Results remain separate by project. Any pooled summary weights projects
  explicitly and cannot treat actions as independent projects.
- Confidence intervals or bootstrap use session/project blocks only where the
  exchangeability assumption is defensible.

## RQ7 baseline contract and current stop

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

The existing RQ1 freeze contains normalized event spines and artifact tables,
but not immutable admitted native prefixes, a per-worktree cutoff revision
manifest, or an untracked-state disposition. It also has no pinned three-vendor
ProcGrep preflight or frozen Raw-log LLM retrieval/model budget. Consequently,
the current F10 is a benchmark-readiness/source-contract audit and explicitly
states `MATCHED COMPARISON STOPPED`; it reports no accuracy, advantage,
evidence, latency, token, or cost value. This dependency result cannot close
the separate capability/superiority question; it does close the paper's
matched-comparison readiness RQ.

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

RQ1--RQ6 now have independently reviewed figures with the coverage stops above.
RQ7's readiness question is closed by F10: the matched run cannot start from
this freeze.  The separate capability/superiority question remains open and
requires a future immutable source contract plus an independently scored run.
