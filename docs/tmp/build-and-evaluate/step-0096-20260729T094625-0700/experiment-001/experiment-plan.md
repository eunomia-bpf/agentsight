# Experiment Plan: RQ4 split annotation cost

## Research Question
- RQ exactly as written in the paper: What is AgentProf's profiling cost?
- Specific uncertainty tested here: Can a skeleton-first, selectively refined annotation pass reduce real provider tokens relative to reading the complete session in one call without materially reducing tag accuracy?
- Why the answer matters: It tests whether semantic profiling can avoid paying full-session model cost for every annotation.

## Paper-Value Admission
- Planned role: supporting result for RQ4 and the practical annotation design.
- Largest credible paper story this experiment could unlock: AgentProf retains useful semantic accuracy while sending substantially less trace evidence to the annotation model.
- Strongest reviewer reject argument addressed: any token saving might come from weaker output, omitted operations, a different model, or accounting only successful calls.
- Independent evidence added: matched, contemporaneous calls with provider token telemetry and the existing ground-truth CodeTraceBench scorer.
- Paper decision if positive: report the paired token saving together with B³ and boundary non-inferiority.
- Paper decision if contradictory, mixed, or inconclusive: keep the result in experiment records, simplify or revise selection on pilot task families, and do not make the paper claim.
- Best alternative: repeated local revision. Existing real runs show that reading the full trace first and then revising costs more, so first-pass selective evidence has greater decision value.

## Expected And Alternative Outcomes
- Current expected answer: most turns can be understood from compact intent/action/progress fields; full visible results are needed only near uncertain transitions.
- Strongest competing explanation: two model calls and overlapping windows erase the input saving, or omitted results degrade boundary accuracy.
- Contradiction: selective refinement uses no fewer provider tokens, loses operation coverage, or lowers ordinary B³/boundary F1 by more than 0.03.

## Published Precedent And Real Assets
- Official data: the existing 405 source-only CodeTraceBench packets and official 2,948-stage scorer.
- Backend: `codex exec`, `gpt-5.6-sol`, structured JSON output and provider `turn.completed.usage`.
- Reused implementation: Step 0087 direct annotation prompt, schema validation, retry accounting, root repair, canonicalization, and scorer.
- Necessary glue: one small adapter that builds a source-only skeleton,
  mechanically selects high-information result turns, and makes one direct
  annotation call.

## Comparison
- FULL: one model call sees every source-visible field of a complete session and returns all sparse semantic marks.
- SPLIT skeleton fields are exactly `session`, `framework`, `task`,
  `turn_count`, `operation_count`, and for every turn: `turn`,
  `first_operation_id`, `intent`, `planned_action`, and `progress`.
- A deterministic source-only selector ranks turns using result length,
  explicit error/pass/timeout words, verification/build/test actions, and
  source progress changes. It selects
  `min(10, ceil(0.15 * turn_count))` turns with a minimum of two. It reads no
  target stage, annotation, score, reward, or prior model result.
- The one SPLIT annotation call sees the complete skeleton plus full
  `visible_result` only on the selected turns, and directly returns complete
  sparse marks in the same schema as FULL. There is no model router, stitch, or
  second model call.
- Both arms use the same session set, model, annotation rules, output contract, retry limit, and operation population. Every call, retry, and overlap token is counted.
- The selector does not read scorer fields. It may be revised only after pilot
  evidence. Confirmation exact `task_name` clusters are not opened until the
  pilot choice is complete, and are not used for another revision.
- Official stages, outcomes, scores, rewards, and label columns are scorer-only. Before execution, enumerate every model-visible field and check that official stage strings are absent.

## Workloads And Metrics
- Preflight: one medium-long real trajectory.
- Pilot: 12 trajectories from 12 exact `task_name` clusters, balanced across
  the four frameworks and short/long traces.
- Confirmation: 32 different exact `task_name` clusters, selected before
  opening their scores; run both arms once.
- Primary cost: sum over all attempts of provider token volume,
  `input_tokens + output_tokens`; this is not presented as dollar cost.
- Supporting cost: cached input, uncached input, reasoning output, call count, retries, and wall time.
- Quality: ordinary B³ F1, exact adjacent-boundary F1, and 100% operation coverage.
- Pilot continuation target: SPLIT uses fewer paired provider tokens; B³ and boundary deltas are each at least -0.03; coverage is complete.
- Confirmation support requires the task-cluster bootstrap upper bound for the
  SPLIT/FULL provider-token ratio to be below 1, both quality-delta lower bounds
  to be at least -0.03, and operation coverage to be 100%.

## Planned Runs

| Run group | Role | Workload | Method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| preflight | validity | 1 medium-long session | FULL + SPLIT | 1 paired | Verify requests, telemetry, stitch, and scoring |
| pilot | algorithm choice | 12 exact task-name clusters | FULL + SPLIT | 1 paired | Keep or revise the simple selector |
| confirmation | paper evidence | 32 different exact task-name clusters | FULL + SPLIT | 1 paired | Decide whether the token-saving claim is supported |

## Execution
- Construct an explicit session manifest from packet metadata only.
- Real preflight command:
  `python3 run_annotation.py prepare && python3 audit_inputs.py && python3 run_annotation.py preflight --workers 2 && python3 score_annotations.py preflight both`.
- Raw preflight outputs:
  `cells/preflight/{full,split}/<session>/`, `run-records.jsonl`, and
  `input-audit.json`.
- Interleave FULL and SPLIT calls to limit service-time drift.
- Store raw Codex events, final marks, per-attempt telemetry, selected windows, and scorer outputs under this experiment.
- Package both arms through the unchanged downstream pipeline and score only after both complete.
- Resume only missing cells; never discard failed calls from cost totals.

## Interpretation
- Positive: lower paired provider tokens with quality within the -0.03 margins and complete coverage.
- Negative: no saving or quality outside a margin; revise only using pilot task families or stop the claim.
- Mixed: report the exact tradeoff internally and do not use a headline efficiency claim.
- Target paper artifact: a compact table of paired token ratio, B³ delta, boundary delta, calls, and wall time.

## Reproducibility Notes
- CodeTraceBench packets and scorer are existing repository artifacts; no new dataset download is required.
- The same Codex model/version is used contemporaneously for both conditions.
- This evaluates prospective exact-task-name-cluster confirmation within a
  historically studied benchmark, not project-level independence or a
  never-seen external benchmark.
