# Failure Taxonomy

Assign one primary category and optional secondary categories. Record direct evidence separately from the inferred mechanism.

| Category | Observable signature | Typical owner | Do not confuse with |
|---|---|---|---|
| `source_fidelity` | Missing roots, duplicate IDs, collapsed lineage, unsupported records | Collector/parser | Agent reasoning failure |
| `metric_invalidity` | Counter semantics are wrong, labels uncalibrated, saturated checker | Evaluator/analysis | Real improvement or regression |
| `task_misrouting` | Wrong skill or stage runs for the request | Trigger/orchestrator | Poor execution inside the correct skill |
| `concept_churn` | Core definition or abstraction repeatedly changes after downstream work | Startup/idea gate | Healthy wording cleanup |
| `claim_evidence_drift` | Claims grow, qualifiers disappear, or experiments do not test the claim | Idea/evaluation gate | Sentence style issue |
| `premature_downstream_work` | Prose, figures, or implementation advance before upstream claims stabilize | Orchestrator/gate | Necessary parallel exploration |
| `review_priming` | Reviewer sees “fixed,” prior verdict, expected gate ID, or requested `accept/pass` | Review protocol | Independent verification |
| `checker_theater` | Many re-reviews or exact verdicts without new external evidence | Review/evaluator | Productive falsification |
| `correction_churn` | User repeatedly redirects scope, fact, method, or decision | Owning skill/agent | Simple clarification |
| `literal_retry` | Same or near-identical action repeats without state change | Agent/tool policy | Intentional repeated trials |
| `tool_error_recovery` | Nonzero exits or malformed calls recur without diagnosis or strategy change | Tool-use guidance | Expected flaky retries |
| `stale_state_edit` | Edit targets outdated content, wrong worktree, or changed precondition | Repository workflow | Concurrent authorized changes handled correctly |
| `workflow_duplication` | Same multi-step procedure is reconstructed across independent tasks | Missing shared/project skill | Similar tasks with materially different constraints |
| `overgeneralized_memory` | Project fact or anecdote is promoted as a global rule | Skill design | General procedure supported across contexts |
| `skill_bloat` | Added text does not alter observable decisions and increases conflicts/context | Skill maintainer | Necessary reference detail |
| `workload_leakage` | Benchmark/replay/evaluator examples enter behavior conclusions or held-out evals | Analysis/eval harness | Legitimate training set with explicit split |
| `outcome_blindness` | Analysis optimizes prompt patterns while ignoring artifact/test/user outcomes | Evaluation design | Transcript analysis paired with outcomes |

## Evidence Thresholds

Use these defaults unless the domain justifies stricter rules:

- One case: document as an anecdote or regression fixture, not a global skill rule.
- Repeated cases from one parent task: evidence of within-task friction, not cross-task generality.
- Independent cases across tasks or repositories: candidate for a shared procedure.
- Controlled baseline/candidate improvement on held-out tasks: candidate for promotion.

Independence must be checked across parent task, repository, data-generating process, and prompt/template lineage. Multiple child reviewers, replays, or clones of one setup are repeated trials, not automatically independent cases.

## Causal Language

Use “observed,” “associated with,” or “consistent with” for trajectory correlations. Use “caused” or “reduced” only when a controlled comparison isolates the candidate change sufficiently.

## Owning-Skill Rule

Patch the skill that owned the failed decision:

- Bad problem framing belongs to startup/idea skills.
- Bad claim-to-experiment mapping belongs to experiment design.
- Bad routing or gate timing belongs to the orchestrator.
- Bad source identity belongs to the observability implementation.
- Bad prose belongs to writing skills only when the idea, claim, and evidence were already stable.

This prevents downstream writing skills from accumulating guards for upstream research failures.

When several owners are plausible, use a small ownership matrix with rows for observed failures and columns for candidate owners. Select one mechanism and one primary owner per promotion experiment; leave other repairs as separate candidates.
