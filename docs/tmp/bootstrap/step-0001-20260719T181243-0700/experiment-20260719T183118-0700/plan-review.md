# Experiment Plan Review

## Round 1

Reviewed: 2026-07-19
Reviewer: fresh read-only research Agent
Verdict: **BLOCK**

### Raw Findings

The reviewer found seven blocking defects:

1. the diagnosis unit, multi-label semantics, normal/unknown cases, interval matching, and intervention ground truth were undefined;
2. the plan conflated deterministic representation with new information rather than bounded-budget accessibility and inductive bias;
3. the 24–40 episode cohort, boundaries, inclusion rules, and dev/test split were not frozen;
4. model, inputs, extraction, prompts, budgets, and scorer lacked real executable commands;
5. raw and trajectory source retrieval and per-query information volume were not auditable for fairness;
6. the headline result and thresholds allowed post-hoc choice between accuracy and cost;
7. the counts control did not specify how counts produce a diagnosis.

Should-fix findings requested clarity on a bounded-memory raw-log alternative, native summary generation, a future compatible failure subset for AgentRx/TrajAudit, hierarchical treatment of repetitions, and whether ablations belong in this experiment.

### Applied Repairs

- Added `annotation-guide.md` with one goal-episode prediction unit, four explicit multi-label pathology definitions, healthy/insufficient states, expert-recommendation wording, minimally sufficient source evidence, independent annotation/agreement/adjudication, exact prediction fields, and frozen scoring rules.
- Reframed the claim as making same-source evidence more accessible under bounded supervision. Only future system evidence can add observations absent from native logs.
- Fixed the test cohort at 40 coding goal episodes, 20 each from AgentSight and ActPlane, selected by label-independent SHA-256 after goal-boundary checks; fixed four separate prompt-development episodes; moved non-code generalization to RQ3.
- Pinned Claude Code 2.1.215 and `claude-sonnet-4-6`, added `$0.50` per-run cap, eight-query/200-line limits, exact input paths, output paths, prompt files, and executable commands in `preflight-commands.md`.
- Gave raw and trajectory conditions identical source sessions, time ranges, semantic source retrieval, and outcome availability. The tested difference is the deterministic workspace index. Both record actual returned bytes, tool calls, tokens, failures, and latency.
- Made trajectory-versus-raw pathology macro F1 the unique headline effect. Predeclared a +0.10 practical effect, bootstrap lower bound above zero, evidence-F1 veto, -0.05 non-inferiority margin, and 25% token reduction for a separate efficiency-only result.
- Defined counts as a same-supervisor control over a frozen table including task/agent/model/duration/outcome covariates; it is not scored for evidence localization.
- Replaced generated session summaries with source-native top-level final assistant reports.
- Removed conditional ablations from RQ1 and assigned them to RQ2.

### Remaining Follow-Up Questions

The same reviewer must now determine whether the operational definitions, cohort selection, real command path, and fairness protocol are executable enough for a one-episode preflight. No model run starts while the plan remains blocked.

## Round 2

Reviewed: 2026-07-19
Reviewer: same read-only research Agent
Verdict: **BLOCK**

### Raw Findings

The repaired plan resolved the first-round scientific-contract issues, but the reviewer
found four remaining execution blockers:

1. the proposed AgentCap trace contained several later top-level user goals, while all 337
   actions were treated as one goal episode;
2. trajectory evidence used `claude:<session-file>:<ordinal>` IDs while native Claude logs
   exposed `toolu_*` IDs, so the raw condition could not return the scored namespace;
3. the diagnosis invocation needed retained native tool-call and usage records to make the
   eight-query/200-line budget auditable;
4. the plan named metrics but did not provide a command that scored unmodified predictions
   against adjudicated gold.

### Applied Repairs

- Replaced AgentCap with the strictly bounded AgentSkill `/check-paper-citations` episode.
  Its half-open interval starts at `2026-07-12T04:40:23.535Z` and ends before the next
  top-level goal at `2026-07-12T04:58:31.093Z`. Exact membership is one parent plus three
  spawned citation-search subagents, 115 Tool actions, and 41 file effects; commands assert
  every count and exclude all later actions.
- Preserved the already parsed native `ToolEvent.call_id` in `RepositoryEvent` as optional
  `source_call_id`. Both conditions now cite the composite
  `<session_id>#<source_call_id>`; corpus audits found no missing IDs and no duplicate
  composites in 117,333 current AgentSight events or 65,699 ActPlane events.
- Froze `--output-format stream-json --verbose` for every tool-using diagnosis run. Invalid
  path, interval, query-count, line-count, or write behavior is retained rather than
  silently repaired.
- Added `score-preflight.jq` and exact parse, schema-validation, and scoring commands. The
  scorer consumes adjudicated `gold.json` and the unedited final model result and emits
  label, evidence, and intervention metrics.

### Remaining Follow-Up Question

The same reviewer gets one final plan-review pass. It must confirm that the replacement
episode, shared provenance identifier, invocation audit, and scoring endpoint are executable
before any diagnosis model is run.

## Round 3

Reviewed: 2026-07-19
Reviewer: same read-only research Agent
Verdict: **BLOCK**

### Raw Findings

The reviewer confirmed that the scientific comparison, exact goal episode, canonical
evidence namespace, retained stream, and prediction-to-gold scorer path were now present.
Three mechanical blockers remained:

1. the command generated `final-report.json` with `jq -rs`, whose `-r` emitted bare text;
   the later `jq -r .` command therefore failed;
2. retaining `stream-json` was not yet an executable audit of query count, returned lines,
   legal paths, or absence of writes;
3. the scorer derived F1 from nullable precision and recall, so a positive gold label with
   an all-negative prediction returned `null` rather than standard F1 `0`.

The reviewer separately confirmed that the four-session, 115-action, 41-file-effect
boundary and all 115 canonical IDs were valid.

### Post-Review Repairs And Verification

- Changed final-report extraction to `jq -s`, added a non-empty JSON-string assertion, and
  regenerated the artifact. `jq -e .` now passes and the frozen report contains only text
  before the next goal.
- Physically sliced all four native logs to the half-open episode interval and made both
  conditions read only those slices. Added executable stream extraction, query/tool/result
  assertions, before/after repository and evidence hashes, plus a mandatory signed manual
  path/command audit artifact.
- Replaced the F1 calculation with `2TP/(2TP+FP+FN)`. A reproduced gold-positive/all-
  negative fixture now returns `TP=0`, `FP=0`, `FN=1`, and `F1=0`.

### Protocol Disposition

**CLOSED AND RETURNED TO THE OUTER ORCHESTRATOR WITHOUT A MODEL RUN.** The
`research-experiment-design` protocol allows one fresh review plus at most two follow-ups;
Round 3 still returned BLOCK, so the proposal cannot gain another review or proceed to real
preflight inside this invocation. The post-review repairs preserve an auditable record and
remove known defects, but they are not retroactively treated as reviewer approval. No
diagnostic prediction from this proposal is paper evidence.
