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
| RQ1 artifact consolidation/revival | Final survival for confirmed introductions, lineage reuse/revival, first/repeat-observed mutation and identity concentration. | Six-case reuse/repetition evidence complete; confirmed-create persistence remains coverage-only at 3/6. | Add dormant-to-revived state transitions without converting repeated activity into a progress score. |
| RQ2 validation response | Recognized success/failure cadence, mutation backlog and event-distance response around validation. | F5 complete for 3/6 source-covered projects; cross-case gate stopped. | Improve validation adapters before a six-case response claim. |
| RQ3 workspace focus evolution | Artifact-class allocation, same-artifact/same-module/cross-module transitions, hotspot turnover and return gaps. | F8a/F8b complete; five cases pass the return gate and one remains N/A. | Add rank-turnover/cooling curves; keep action order distinct from time or internal attention. |
| RQ4 cross-session continuity | Native-root/source-stream structure, adjacent non-overlapping components, pre-mutation re-grounding and prior artifact/module overlap. | F7 is coverage/within-case evidence; the four-project estimator gate stopped. | Recompute with corrected native root/subagent identity before estimating continuity. |
| RQ5 Skill/instruction footprints | Exact Skill name/arguments and source attribution blocked by native root session; separate instruction focal events. | Fresh six-case run and independent 2,063-stream checker pass. Five exact-context Skill strata qualify, but only one project supports a two-Skill comparison: same/different JSD 0.116/0.123, exact root-block p=0.750 over 12 admissible assignments. | Report source-attributed coverage and no supported repeatable Skill separation; make no fingerprint or causal harness claim. |
| RQ6 external boundary | Replicate compatible within-attempt relations separately in public coding and scientific-process traces; mark persistence/re-grounding N/A without persistent lineage. | Complete over 64 independent task instances per Open-SWE stratum (256 selections, 255 unique IDs across strata) and 64 IdeaTrail topics. All five strata pass the 64-unit gate and the independent checker reconciles 31,249 Tool calls and 22,113 transitions without mismatch. Cross-module movement is 18.0--30.0% publicly versus 2.1--20.2% locally; median intervening calls before module return are 2--3 versus 2--4. | Report path locality/return recurrence and the magnitude difference; keep persistent lineage, cross-session re-grounding, and Skill attribution N/A. |
| Separate measurement capability | Compare source-verifiable factual coverage, abstention and cost for Final State, Counts, ProcGrep, bounded Raw-log reader and artifact-linked trajectories. | Open. Step 0003 froze 72 complete sessions and a 120-question oracle, but the Raw child never started. | Resume only as a separate tool experiment; it is not required to close the descriptive RQs. |

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

Step 0003 prospectively froze 12 complete session files for each of six
projects and generated 120 source-witnessed questions, 30 in each of the four
families. A separate shell/jq checker reproduced every answer. Final State,
Counts, pinned ProcGrep and the artifact trajectory completed the final
preflight, but the Raw child resolved relative `--cd` and output paths against
its own relative cwd and exited before model startup. Because the three allowed
preflight attempts are exhausted, the corrected absolute-path runner has not
been executed. These artifacts establish a reusable corpus and an incomplete
execution path only; they provide no RQ7 accuracy, coverage or cost result.

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
- Current RQ7 plan and incomplete preflight record:
  `docs/tmp/build-and-evaluate/step-0003-20260722T142124-0700/`
- Corrected Skill/instruction footprint run:
  `docs/tmp/bootstrap/step-0002-20260722T182000-0700/experiment-rq5-skill-footprints/`
- RQ6 public external-boundary run:
  `docs/tmp/bootstrap/step-0002-20260722T182000-0700/experiment-rq6-external-boundary/full/`

Local RQ1--RQ5 have executable figures with the coverage stops above; the
corrected RQ5 result now replaces the old exporter-induced source-coverage
stop. RQ6 now closes the compatible within-attempt external check without
extending it to longitudinal lineage. F10 closes only the old freeze's
readiness audit; the separate capability experiment remains open until its Raw
baseline and independently scored matched run complete.
