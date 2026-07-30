# Experiment Plan: RQ2 real before/after profiling utility

## Research Question
- RQ exactly as written in the paper: Do AgentProf profiles correspond to real agent problems?
- Specific uncertainty tested here: Does applying the concrete repair derived from an AgentProf bad-minus-good profile improve an independently executed agent's official task outcome or reduce its cost?
- Why the answer matters: It closes the gap between diagnosing a plausible problem and demonstrating a useful change in a real agent run.

## Paper-Value Admission
- Planned role: decisive cross-dataset utility/transfer experiment for a
  profile-derived repair.
- Largest credible paper story this experiment could unlock: an agent can
  inspect AgentProf evidence, turn the dominant bad-run pattern into a small
  implementation change, and measurably improve later real executions.
- Strongest reviewer reject argument addressed: the profile finding may be descriptive only, and the proposed repair may not change agent behavior or benchmark outcomes.
- Independent evidence added: official ToolSandbox execution and evaluation on
  scenarios disjoint from the AgentReward traces that produced the profile.
  This does not test whether a profile is faster than raw review or uniquely
  necessary to discover the repair.
- Paper decision if positive: report the full diagnosis-to-change-to-outcome chain.
- Paper decision if contradictory, mixed, or inconclusive: retain the complete
  development record; do not run the confirmation population or make the
  profiling-utility claim.
- Best alternative: ask a human developer to repair an application. The author
  specified there is no human developer, while this agent compatibility-layer
  change is direct, runnable, and independently scored.

## Expected And Alternative Outcomes
- Current expected answer: decoupling an opaque assistant tool-call ID from
  the ToolSandbox executor's internal Python variable prevents a failed tool
  round and its recovery retry.
- Strongest competing explanation: the invalid-ID pattern is peculiar to the
  pilot seeds, or changing IDs breaks tool/result association.
- Contradiction: the converter does not eliminate invalid-ID failures, lowers
  official similarity, or increases agent tokens without an outcome gain.

## Published Precedent And Real Assets
- Initial diagnosis source: the existing standard pprof bad-minus-good
  AgentReward profile motivated the no-progress retry check. Its prompt-only
  transfer did not generalize and remains a development record.
- Final diagnosis source: the standard AgentPProf
  `before-profile.pb.gz` built from real ToolSandbox BEFORE pilot traces. It
  shows 5/21 invalid-call-ID tool operations and four corresponding exact
  recovery repeats. An independent agent with profile-only access selected the
  call-ID repair.
- Execution asset: clean official ToolSandbox checkout at commit `165848b9a78cead7ca7fe7c89c688b58e6501219`, its official `Scenario.play_and_evaluate` evaluator, and the existing instrumented local OpenAI runner.
- Agent/user backend: the already-running local Qwen3.6-27B server; agent and simulated-user usage are recorded separately.
- Necessary glue: an experiment-local paired-run manifest and result summarizer. The official checkout, scenario state, tools, and evaluator remain unchanged.

## Comparison
- BEFORE: official agent system input unchanged (`no-policy`).
- The initial AFTER policy was evaluated on the pilot and did not generalize;
  that development result is retained in `iteration-log.md`.
- The real BEFORE pilot was therefore converted into the one standard
  `before-profile.pb.gz`. It shows that 5/21 tool operations had invalid
  call IDs and that all four exact repeats were successful recovery from that
  fault. An independent profile-only analyst selected the narrower repair.
- A first ID-normalization pilot was not interpretable: BEFORE happened to draw
  19/19 valid raw IDs while AFTER drew and repaired 5/19 invalid IDs. The
  observed +51.5% token difference was dominated by unrelated simulated-user
  trajectory divergence, including one scenario where the repair never
  engaged. This result is retained and excluded from the final method.
- Final AFTER: identical no-policy agent input and original opaque protocol
  IDs, but the experiment-local converter derives a safe internal Python
  variable instead of interpolating the opaque ID into executable source.
  Before each later model call it restores the original ID in both the
  assistant call and matching tool response. Tool names, arguments, order,
  state, user, scenario, and evaluator are unchanged.
- Same scenario, model, sampling, scenario-construction seed, per-request seed
  derivation, tools, initial state, user model, and evaluator. The local server
  does not seed its opaque ID allocator, so IDs and resulting trajectories are
  stochastic nuisance variables rather than strict common-randomness pairs.
- Condition order is alternated across scenarios.
- The final development pilot uses three complete, prespecified seed blocks on
  every one of the eight development scenarios. It never stops based on
  observed ID validity. Confirmation uses the same three-repetition design on
  every one of the 23 untouched scenarios and does not permit another repair
  or metric change.

## Workloads And Metrics
- Preflight: `turn_on_location_low_battery_mode`, one paired execution plus
  five fixed mechanism-validation pairs; all are excluded from outcomes.
- Pilot: 8 dependency-screened offline scenarios selected by name/category
  without reading outcomes, each run under three new seed blocks.
- Confirmation: the remaining 23 offline outcome scenarios not used in the
  pilot, each run under three fixed seed blocks.
- Primary outcome: official `EvaluationResult.similarity`.
- Secondary outcomes: exact success (`similarity == 1`), milestone similarity, minefield similarity, agent total tokens, agent model calls, tool calls, turn count, and unchanged-repeat incidence reconstructed from official execution logs.
- Interpretation order is fixed: first test whether the scenario-cluster
  official-similarity after-minus-before interval is above zero. If it is not,
  the efficiency branch is supported only when the scenario-cluster
  agent-token ratio upper bound is below 1 and the official-similarity
  after-minus-before interval lower bound is at least -0.05. Exact success is
  supporting rather than an alternative primary gate.
- Pilot and confirmation uncertainty: bootstrap whole scenario clusters, each
  retaining all three repetitions, plus raw per-cell outcomes. All cells are
  analyzed intention-to-treat; raw-invalid ID counts explain mechanism
  engagement but never select observations. Exceptions count as failed cells
  rather than disappearing.

## Planned Runs

| Run group | Role | Workload | Method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| preflight | validity | 1 excluded official scenario | BEFORE + CONVERTER-FIX | 1 execution pair plus 5 fixed mechanism pairs | Verify real execution, evaluator, both-arm fault exposure, ID handling, and telemetry |
| pilot | final repair check | 8 official scenarios | BEFORE + CONVERTER-FIX | 3 runs per scenario and arm | Decide whether the profile-derived repair is valid |
| confirmation | paper evidence | 23 untouched scenarios | BEFORE + CONVERTER-FIX | 3 runs per scenario and arm | Decide profiling-utility support |

## Execution
- Verify the ToolSandbox checkout is clean and the local endpoint is healthy.
- Final converter-fix real preflight command, from this directory:
  `python run_converter_pairs.py preflight && python summarize_converter.py preflight`,
  using trial seed `202607800` and raw output under
  `episodes-converter/{before,converter-fix}/seed-202607800/`. The local
  Qwen compatibility adapter merges official system messages in source order
  at position zero in both conditions; it does not alter tools, state, policy,
  or evaluator.
- Mechanism-validation preflight is fixed at seeds `202607801` through
  `202607805` on the same excluded scenario:
  `python run_converter_pairs.py preflight-mechanism` followed by
  `python summarize_converter.py preflight-mechanism`. All five pairs run
  regardless of observed ID validity. It passes only if BEFORE contains at
  least one invalid-ID syntax failure, CONVERTER-FIX generates at least one
  raw-invalid ID, and CONVERTER-FIX has zero such syntax failures.
- Final development pilot command:
  `python run_converter_pairs.py pilot` followed by
  `python summarize_converter.py pilot`. Its 24/24 cells must be valid, both
  arms must engage the stochastic fault, and one of the two interval-based
  outcome/efficiency branches must pass.
- Use the experiment's Python 3.10 environment and local compatibility
  adapter; do not edit the official checkout.
- Execute conditions one at a time because the local server has one inference slot.
- Preserve each `episode.json`, official evaluator output, agent/user telemetry, and execution log.
- Run a summarizer over all expected paired cells. Missing or exception cells
  remain in the table with official outcome zero and all tokens already
  recorded by the runner; they never disappear from denominators.

## Interpretation
- Positive: the same profile-derived change improves official outcomes or reduces cost without harming similarity.
- Negative: the converter fix does not engage or worsens results; stop this
  utility claim rather than change confirmation.
- Mixed: identify whether the gain is outcome, token, or task-category specific; do not overclaim general developer productivity.
- Target paper artifact: one end-to-end case plus a paired before/after table over confirmation scenarios.

## Reproducibility Notes
- AgentReward motivated the initial hypothesis; the final concrete defect and
  repair are derived from the ToolSandbox BEFORE pprof. The redownloadable
  29 GB AgentReward raw cache may be absent because its earlier profile evidence
  is already materialized.
- ToolSandbox uses its unchanged official evaluator.
- ToolSandbox has been observed elsewhere in the project; this experiment uses
  a prospective pilot/confirmation separation for this repair, not an
  untouched benchmark claim.
- This measures an autonomous agent applying a profile-derived repair, not a human time study.
