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
| RQ1 artifact consolidation/revival | Final survival for confirmed introductions, lineage reuse/revival, first/repeat-observed mutation and identity concentration. | Six-case reuse/repetition evidence complete. The 2026-07-25 HEAD recompute (after the projection hardening) lifts confirmed-create persistence from coverage-only 3/6 to 6/6; sessions are now counted as 551 native roots (2,049 source files before dedup). | Add dormant-to-revived state transitions without converting repeated activity into a progress score. |
| RQ2 validation response | Recognized success/failure cadence, mutation backlog and event-distance response around validation. | F5 evidence complete for 6/6 source-covered projects after the HEAD recompute (was 3/6); the cross-case stop is lifted and its re-review is open. | Re-review the cross-case response question over the six covered cases. |
| RQ3 workspace focus evolution | Artifact-class allocation, same-artifact/same-module/cross-module transitions, hotspot turnover and return gaps. | F8a/F8b complete; all six cases now carry return evidence (eunomia.dev cross-session repeat episodes 1 to 29 after session-join repair); pooled unknown-create births 790 to 0. | Add rank-turnover/cooling curves; keep action order distinct from time or internal attention. |
| RQ4 cross-session continuity | Native-root/source-stream structure, adjacent non-overlapping components, pre-mutation re-grounding and prior artifact/module overlap. | F7 is coverage/within-case evidence. Recomputed with corrected native-root/subagent identity: the four-project estimator gate still stops, now established as data-limited (3/6 projects reach 20 boundaries), not identity-limited. | Estimating continuity requires more eligible boundaries, not further identity repair. |
| RQ5 Skill/instruction footprints | Exact Skill name/arguments and source attribution blocked by native root session; separate instruction focal events. | Fresh six-case run and independent 2,063-stream checker pass. Five exact-context Skill strata qualify, but only one project supports a two-Skill comparison: same/different JSD 0.116/0.123, exact root-block p=0.750 over 12 admissible assignments. | Report source-attributed coverage and no supported repeatable Skill separation; make no fingerprint or causal harness claim. |
| RQ6 external boundary | Replicate compatible within-attempt relations separately in public coding and scientific-process traces; mark persistence/re-grounding N/A without persistent lineage. | Complete over 64 independent task instances per Open-SWE stratum (256 selections, 255 unique IDs across strata) and 64 IdeaTrail topics. All five strata pass the 64-unit gate and the independent checker reconciles 31,249 Tool calls and 22,113 transitions without mismatch. Cross-module movement is 18.0--30.0% publicly versus 2.1--20.2% locally; median intervening calls before module return are 2--3 versus 2--4. | Report path locality/return recurrence and the magnitude difference; keep persistent lineage, cross-session re-grounding, and Skill attribution N/A. |
| Separate measurement capability | Compare source-verifiable factual coverage and abstention for Final State, Counts, ProcGrep, bounded Raw-log reader and artifact-linked trajectories. | Repaired. On 2026-07-23 the frozen implementation scored 32/60 B+C against the frozen source-direct oracle. After root-cause repair (session join, failed-call effects, shell path extraction, event workdir) and oracle correction to v4, the current implementation scores B 30/30, C 30/30, D 30/30, A 12/30 against the corrected oracle: 60/60 B+C on this corpus. Raw remains N/A after a retrieval-engaged preflight boundary stop. No general exact-fact capability claim; the A gap is a deliberate grammar difference (trajectory preserves ProcGrep's action spine, v4 re-derives atoms source-direct). | Keep conformance as a standing gate for any future projection change. |

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

**Reviewed outcome.** As frozen on 2026-07-22, the authoritative cutoff admits
2,049 native session files and 206,249 Tool actions; 1,825 sessions and
175,850 actions are worktree-attributed. The extraction yields 7,154 observed
artifact identities and 13,152 confirmed mutation rows.

**Recomputed outcome (2026-07-25, after the projection hardening).** The same
cutoff and inclusion contract now admit 551 native root sessions (the 2,049
source files minus subagent/continuation duplicates; a counting-semantics
change, not data loss: attributed actions are stable at 175,619 versus
175,850, −0.13%) and 181,303 Tool actions. The extraction yields 5,792
observed artifact identities and 13,905 confirmed mutation rows (+5.7%, mostly
eunomia.dev's recovered Claude activity: 170 to 739). All six projects pass
the longitudinal gate. Later reuse is observed for 89.29--97.02% of eligible
mutations, and its descriptive association with action volume is Spearman rho
0.2000 (was 0.0857). All six projects now have an eligible confirmed create
and a recognized successful validation, so persistence and validation move
from 3/6 coverage-only to 6/6 qualified. The independent result audit
regenerated both figures byte-identically for the frozen run.

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

## Separate measurement-capability result

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

Step 0004 reuses the same 72 archived native session files and cutoff workspace
evidence as Step 0003 but rederives all questions after removing false
redirection/heredoc shell artifacts. A standalone Python checker imports
neither the primary experiment code nor `agent-session`; it reparses Claude,
Codex, and Gemini records, reconstructs 1,721 artifact edges, independently
derives cutoff state from archived index/presence evidence, and reproduces all
120 answers.

The completed deterministic matrix contains 480 rows. Exact outcomes of the
frozen implementation on 2026-07-23:

| Method | A action-only | B artifact-linked | C cross-session | D final-state |
|---|---:|---:|---:|---:|
| Final State | 0 correct, 30 abstain | 0 correct, 30 abstain | 0 correct, 30 abstain | 30/30 correct |
| Counts | 7 correct, 11 wrong, 12 abstain | 0 correct, 30 abstain | 0 correct, 30 abstain | 0 correct, 30 abstain |
| ProcGrep | 18 correct, 12 wrong | 0 correct, 30 abstain | 0 correct, 30 abstain | 0 correct, 30 abstain |
| Artifact trajectory | 18 correct, 12 wrong | 16 correct, 14 wrong | 16 correct, 14 wrong | 28 correct, 2 abstain |

Trajectory preserves ProcGrep's A answers exactly (30/30 identity). The
decisive frozen result is B+C: the frozen trajectory answers all 60 questions
but gets 28 wrong, with per-project conditional accuracy 1.000, 0.400, 0.700,
0.000, 0.600, and 0.500.

The follow-up audit
(`docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/`) classified the 28
errors: 14 deliberate broader shell/scope evidence, 14 genuine bugs (7
native-root session join, 4 failed-call effect drop, 3 shell path
extraction). The genuine classes plus one later event-workdir bug were fixed,
and the oracle was corrected to v4 (24 of 120 expected answers changed, all
justified per question). Outcomes of the current implementation against the
corrected v4 oracle:

| Method | A action-only | B artifact-linked | C cross-session | D final-state |
|---|---:|---:|---:|---:|
| Artifact trajectory | 12 correct, 18 wrong | 30/30 correct | 30/30 correct | 30/30 correct |

The A-family gap is a deliberate grammar difference, not a new defect: the
trajectory preserves ProcGrep's official action spine, while the v4 oracle
re-derives atom counts under the source-direct grammar. B+C is 60/60 on this
corpus; this is repair-corpus conformance, not a general exact-fact
capability claim.

The bounded Raw reader is N/A. The single registered Terra preflight made 11
local evidence calls and retrieved 117,184 bytes, but the frozen boundary
monitor stopped it when an original absolute path embedded in the evidence
appeared in a command. That stop exposes a harness/contract incompatibility,
not model performance. No Raw accuracy, token, cost, efficiency, or superiority
claim is made. The all-project deterministic preflight is reused as the final
480-row deterministic matrix; the planned 840-row integrated comparison is
incomplete because none of the 360 Raw rows ran. Likewise, deterministic timing
is not method-specific and is not compared.

The frozen negative result changed the measurement boundary for the local
empirical study, and the completed audit discharged it: the error taxonomy
separated deliberately broader shell/scope evidence from genuine path,
identity, and native-root join errors, all genuine bug classes were repaired,
and RQ1--RQ4 were recomputed at the repaired revision
(`docs/tmp/build-and-evaluate/rq1-rq4-recompute-20260725/`). RQ5 remains
protected by its separate 2,063-stream checker, and RQ6 by an independent
public-data reconstruction. Local projection quantities are now measurements
under the repaired projection, with B+C conformance at 60/60 against the
corrected source-direct oracle on this corpus.

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
- Corrected measurement-capability experiment and independent result review:
  `docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/experiment-001/`
- RQ7 error taxonomy, HEAD rerun, corrected v4 oracle, and workdir fix:
  `docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/`
- RQ1--RQ4 HEAD recompute and delta report:
  `docs/tmp/build-and-evaluate/rq1-rq4-recompute-20260725/`
- Corrected Skill/instruction footprint run:
  `docs/tmp/bootstrap/step-0002-20260722T182000-0700/experiment-rq5-skill-footprints/`
- RQ6 public external-boundary run:
  `docs/tmp/bootstrap/step-0002-20260722T182000-0700/experiment-rq6-external-boundary/full/`

Local RQ1--RQ5 have executable figures with the coverage notes above. The
corrected RQ5 result replaces the old exporter-induced source-coverage stop,
and RQ6 closes the compatible within-attempt external check without extending
it to longitudinal lineage. The separate tool experiment's frozen negative
result (32/60 B+C, 2026-07-23) is repaired at the current revision (60/60 B+C
against the corrected v4 oracle on this corpus), without a general exact-fact
capability claim; a Raw reader comparison remains N/A rather than open
evidence of either method.
