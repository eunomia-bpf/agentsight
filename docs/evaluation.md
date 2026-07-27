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
| RQ1 artifact consolidation/revival | Final survival for confirmed introductions, lineage reuse/revival, first/repeat-observed mutation and identity concentration. | **Complete at repaired v2 (2026-07-27).** The fixed corpus has 5,676 identities, 13,809 confirmed mutation rows, and 13,766 artifact-event episodes. Persistence and validation remain 6/6; reuse is 89.29--96.94% with action-volume Spearman rho 0.0286. Repeat-observed episodes are 74.9--91.8%. Action/time dormancy revival ranges are 8.3--47.6% and 0.0--39.4%. | Preserve these as six-case descriptive results; any population claim needs independently selected longitudinal projects. |
| RQ2 validation response | Recognized success/failure cadence, mutation backlog and event-distance response around validation. | **Complete at repaired v2.** Recognized success covers 6/6 projects, complete inter-success intervals 5/6, and recognized failures 4/6. Eligible lanes have 29.3--86.5% zero-mutation intervals with maxima of 1--817; outcome-conditioned response has no consistent cross-case direction. | Retain cadence and heterogeneity only; make no distribution-family, vendor-effect, or project-type-effect claim. |
| RQ3 workspace focus evolution | Artifact-class allocation, same-artifact/same-module/cross-module transitions, hotspot turnover and return gaps. | **Complete at repaired v2.** Case D paper/docs mutation share is 60.7% over all resolved statuses and 86.8% for `ok` only. Transitions span 25.6--82.6% same artifact, 17.4--68.0% same module, and 0.0--23.2% cross module. Five cases qualify for 2--4-call returns; AgentSkill has zero returns and is N/A. Turnover/cooling values are synchronized to the 3,367-window-pair v2 run. | Keep rank turnover/cooling in Agent action order; do not reinterpret them as elapsed time, attention, or forgetting. |
| RQ4 cross-session continuity | Native-root/source-stream structure, adjacent non-overlapping components, pre-mutation re-grounding and prior artifact/module overlap. | **Verified unchanged at repaired v2.** The projection still forms 121 components/111 boundaries with the same project breakdown and 3/6 projects reaching 20 boundaries. Conditional support changes to 65 boundaries with first mutation and 59 with defined overlap, but the four-project estimator gate still stops. | Estimating continuity requires more eligible boundaries, not further identity repair. |
| RQ5 Skill/instruction footprints | Exact Skill name/arguments and source attribution blocked by native root session; separate instruction focal events. | **Complete.** The independent 2,063-stream checker passes. Five exact-context Skill strata qualify, but only one project supports a two-Skill comparison: same/different JSD 0.116/0.123, exact root-block p=0.750 over 12 admissible assignments. | Retain source-attributed coverage and no supported repeatable Skill separation; make no fingerprint or causal harness claim. |
| RQ6 external boundary and invariance | Replicate compatible within-attempt relations in public coding/scientific traces; test local project×vendor stability; mark longitudinal facts N/A without lineage. | **Complete at repaired v2.** Public reconstruction still reconciles 31,249 Tool calls and 22,113 transitions. Local path locality is 76.8--100.0% versus public cross-module movement of 18.0--30.0%. Path locality is the sole invariant candidate (CV 0.088, LOO 1.0, all five public CIs positive); classification is 1 invariant / 8 vendor-shaped / 6 idiosyncratic / 0 project-shaped. No fitted tail supports a universal power law. | Replicate the invariant gate in additional independent organizations/vendors; keep vendor-shaped labels observational and lineage/Skill claims N/A publicly. |
| RQ7 tool-call workload and bounds | Composition, repetition, dependency, timing, and conservative prefetch/concurrency/speculation/event-driven opportunity estimands. | **Complete; v2 identity count synchronized.** Shell is 68.6% of 181,303 calls. Among 43,889 artifact-identity reads, 46.7% repeat; native overlap consumes 86.0% of logical-parallel edges, actionable prefetch precision is 21.75%, and the event-driven bound is 1,456 calls (0.81%). | Any performance claim requires replay or implementation; retain current quantities as structural observation/opportunity bounds. |
| Corpus human involvement | Source-native human messages, startup versus follow-up guidance, interruption response, and observable timing boundary. | **Complete (2026-07-26).** The 550 unique projected session IDs contain 7,804 substantive messages, one per 23.2 Agent actions; 63.3% of human-bearing sessions are startup-only. After explicit interruptions, 50.4% change exact tool and 49.6% tool family. Inactive gaps occupy 73.8% of the two-part envelope but do not measure attention. | Treat the cases as author-associated mixed-initiative traces; do not infer autonomy rates or causal guidance effects. |
| Separate measurement capability | Compare source-verifiable factual coverage and abstention for Final State, Counts, ProcGrep, bounded Raw-log reader and artifact-linked trajectories. | **Two repair cycles complete.** Frozen B+C was 32/60; first-cycle repair reaches 60/60. A material compound-shell audit then fixes six shape families with 18 action fixtures; original regression remains 60/60 and the inspected 116-question corpus reaches B+C 58/58 with zero missing/extra in attempted, confirmed-effect, and edge/status ledgers. It is `repair-corpus-v2`, not held-out evidence. The bounded Raw matrix is complete but mixed/inconclusive. | Keep conformance as a standing gate. A general exact-conformance claim requires a third independently selected corpus. |

## 2026-07-26--27 analysis and repair wave

| Analysis directory | Core result | Paper status |
|---|---|---|
| `docs/tmp/build-and-evaluate/shell-boundary-audit-20260726/` and `shell-boundary-repair-20260726/` | Compound shell/wrapper exposure is material for RQ1/RQ3. Six shape families and 18 action fixtures close the known defects; original B+C remains 60/60, repair-corpus-v2 reaches 58/58, and all strict edge ledgers have zero missing/extra. | Integrated as the second standing-gate repair cycle. The former held-out corpus is explicitly downgraded; third-corpus generality remains open. |
| `docs/tmp/build-and-evaluate/rq1-rq4-recompute-v2-20260727/` | Repaired v2 corpus: 5,676 identities, 13,809 mutation rows, 13,766 episodes; RQ1 rho 0.0286 and reuse 89.29--96.94%; RQ2 29.3--86.5%; RQ3 Case D 60.7/86.8%; RQ6 local anchor 76.8--100.0%; RQ4 121/111 unchanged. | Fully synchronized into both paper entries and all seven affected result figures. |
| `docs/tmp/build-and-evaluate/user-questions-v2-20260727/` | Created-document no-revisit/reread 30.4%/62.4%; source--test order remains 0 test-first, 7 code-first, 21 same-event; confirmed read paper/code 43.5%/43.0% and write 70.2%/16.2%; 0/16 repeat-test blocks have zero code episodes. | Integrated as four v2 supplement answers with the repaired cross-path compound-episode contract. |
| `docs/tmp/build-and-evaluate/invariance-v2-20260727/` | Path locality remains the sole invariant candidate (CV 0.088, LOO 1.0, public five-stratum direction replicated); classification becomes 1 invariant / 8 vendor-shaped / 6 idiosyncratic / 0 project-shaped. | Integrated into RQ6 with observational-vendor and no-universal-power-law boundaries. |
| `docs/tmp/build-and-evaluate/human-involvement-20260726/` | 7,804 messages, 23.2 actions/message, 63.3% startup-only, about 50% immediate tool redirection after explicit interruption, and 73.8% inactive-gap share with an attention-time non-identifiability boundary. | Integrated as the mixed-initiative corpus limitation in main and a new supplement subsection. |
| `docs/tmp/build-and-evaluate/rq2-crosscase-20260726/` | Success coverage 6/6, complete inter-success coverage 5/6, failure coverage 4/6; the v2 recompute updates eligible-lane zero-mutation fraction to 29.3--86.5%, maxima 1--817, with no consistent outcome-conditioned response. | Integrated into the main-paper RQ2 paragraph and supplement; descriptive cadence and heterogeneity only. |
| `docs/tmp/build-and-evaluate/session-dynamics-20260726/` | Supported strata show +16.7--28.9 pp late reread; ten-call extended startup median/p90 20%/60%; strict-gross harness-shaped footprint 6.48%; strict failure-chain burden 0.0320%. | Integrated in the supplement as late-session re-grounding, startup distribution, stratified footprint, and rare strict chains; no degradation, waste, or causal-overhead claim. |
| `docs/tmp/build-and-evaluate/toolcall-behavior-20260726/` | Shell 68.6% of 181,303 calls; artifact-identity repeated reads 46.7%, of which 76.2% have no observed intervening mutation; 33.2% of calls occur in reconstructed multi-call batches. | Integrated into the supplement as descriptive workload mix and repetition, not inefficiency. |
| `docs/tmp/build-and-evaluate/toolcall-profile-20260726/` | 24.76% of adjacent edges already overlap and 2.98% are remaining sequential local-read candidates; actionable prefetch precision 21.75%; last-test match 26.22% versus 80.36% eager-test waste; event-driven bound 1,456 calls (0.81%). | Integrated into the supplement as conservative execution/roundtrip upper bounds, not replayed or causal speedups. |
| `docs/tmp/build-and-evaluate/toolcall-survey-20260726/` | Seven narrower empirical gaps confirmed; broad novelty claims about tool distributions, retries, speculation, caching, concurrency, or provenance are ruled out. | Used only to position the descriptive workload characterization; no new `\cite` command or bibliography entry added in this wave. |

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
2,049 native session files and 206,249 Tool actions; 1,825 sessions are
worktree-attributed. The extraction yields 7,154 observed
artifact identities and 13,152 confirmed mutation rows.

**Final v2 recomputed outcome (2026-07-27, after compound-shell repair).** The
same cutoff and inclusion contract admit 551 native root sessions (the 2,049
source files minus subagent/continuation duplicates) and 181,303 Tool actions;
all 551 roots and 176,288 actions are worktree-attributed. The extraction
yields 5,676 observed artifact identities, 13,809 confirmed mutation rows,
2,318 mutated identities, and 13,766 artifact-event mutation episodes. All six
projects pass the longitudinal gate. Later reuse is observed for
89.29--96.94% of eligible mutations, and its descriptive association with
action volume is Spearman rho 0.0286. BPF tutorial at 91.13% now narrowly
exceeds AgentSight at 90.95%, reversing their adjacent pre-v2 order. All six
projects retain an eligible confirmed create and a recognized successful
validation, so persistence and validation remain 6/6 qualified. The v2 CSV
rows regenerate every affected RQ1--RQ4 publication figure.

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

The bounded Raw reader later completed under the fixed-reader protocol. It
obtains 191/360 (53.1%) overall exact coverage and 94/180 (52.2%) B+C coverage,
with 260/360 scoreable rows and 191/260 (73.5%) exact accuracy among scoreable
rows; 5/18 cells hit the registered 1 MiB return limit. This mixed result
supports no trajectory superiority, necessity, speed, or cost claim.

A second materiality audit found that compound shell/wrapper admission could
move published RQ1/RQ3 quantities. Six audited shape families were repaired
and frozen in 18 action fixtures shared as a specification across production
and two separately implemented source-direct oracles. The original B+C
regression remains 60/60. The fixed 116-question corpus reaches B+C 58/58 and
D 29/29, while attempted (2,000), confirmed-effect (1,848), and
edge/call-status (1,843) ledgers have zero missing and zero extra rows.
Because that corpus was inspected during repair, it is `repair-corpus-v2`, not
held-out generalization evidence. A third independently selected corpus is
required for any general exact-conformance statement.

The two negative findings changed the measurement boundary for the local
empirical study. Each repair had to preserve the 60/60 regression; the second
also had to close all strict ledgers before RQ1--RQ4, extensions, local anchor,
user questions, invariance, and the RQ7 identity-dependent read count were
recomputed from repaired v2 rows
(`docs/tmp/build-and-evaluate/rq1-rq4-recompute-v2-20260727/`). RQ5 remains
protected by its separate 2,063-stream checker, and public RQ6 by an
independent reconstruction. This is conformance as a standing gate, not a
one-time validation claim.

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
- Compound-shell materiality audit and repair-corpus-v2 closure:
  `docs/tmp/build-and-evaluate/shell-boundary-audit-20260726/` and
  `docs/tmp/build-and-evaluate/shell-boundary-repair-20260726/`
- Final RQ1--RQ4 repaired-v2 recompute and delta report:
  `docs/tmp/build-and-evaluate/rq1-rq4-recompute-v2-20260727/`
- Final user-question v2 recompute:
  `docs/tmp/build-and-evaluate/user-questions-v2-20260727/`
- Cross-stratum invariance v2 recompute:
  `docs/tmp/build-and-evaluate/invariance-v2-20260727/`
- Human-involvement profile:
  `docs/tmp/build-and-evaluate/human-involvement-20260726/`
- Corrected Skill/instruction footprint run:
  `docs/tmp/bootstrap/step-0002-20260722T182000-0700/experiment-rq5-skill-footprints/`
- RQ6 public external-boundary run:
  `docs/tmp/bootstrap/step-0002-20260722T182000-0700/experiment-rq6-external-boundary/full/`

Local RQ1--RQ5 have executable figures with the coverage notes above. The
corrected RQ5 result replaces the old exporter-induced source-coverage stop,
and RQ6 closes the compatible within-attempt external check without extending
it to longitudinal lineage. The invariant grid identifies only path locality
as a cross-project/vendor/public candidate and supports no universal power-law
claim. The separate tool experiment's frozen 32/60 B+C result is repaired to
60/60; the second cycle preserves that gate and closes repair-corpus-v2 at
58/58 with exact ledgers. The bounded Raw comparison is complete but
mixed/inconclusive. None of these repair-corpus results supports a general
exact-fact capability claim.
