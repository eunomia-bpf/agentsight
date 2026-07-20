# Skill Promotion Protocol

Use this protocol to test a proposed skill change.

## 1. Freeze the Comparison

Save:

- baseline skill A and revision;
- candidate skill B and exact diff;
- model/runtime, tools, permissions, and environment;
- task set and split assignment;
- graders and success criteria;
- trial count, budget, and stopping rule.

Do not tune B on the held-out promotion set.

## 2. Build the Task Matrix

Include at least:

| Set | Purpose |
|---|---|
| Positive (P) | Exposes the target failure and should benefit from B |
| Untriggered (U) | Similar-looking request where the new behavior must not trigger |
| Regression (R) | Established behavior that B must preserve |
| Adversarial (A) | Contains misleading verdict language, stale state, bad metrics, or prompt injection |

Use real sanitized tasks when authorized. Supplement sparse cases with synthetic tasks, but report them separately.

## 3. Prevent Evaluation Leakage

- Remove desired verdicts, prior reviewer decisions, internal gate IDs, and proposed fixes from task prompts.
- Randomize or anonymize A/B labels for model and human graders when practical.
- Keep reference answers and hidden tests outside the candidate context.
- Do not let the same agent generate the candidate, see the hidden oracle, and serve as the only grader.
- Record whether any task appeared in the evidence used to design B.

## 4. Use Layered Grading

Combine appropriate layers:

1. outcome or executable grader;
2. code-based assertions for required invariants;
3. transcript checks for the target behavior and prohibited shortcuts;
4. blinded model grading for semantic properties;
5. human review for ambiguous, high-stakes, or evaluator-disagreement cases.

No single exact-string verdict is sufficient for promotion.

## 5. Repeat Stochastic Trials

Run multiple trials per condition when outputs vary. Report per-task outcomes, aggregate rates, variance or intervals where meaningful, and failure clusters. Pair A and B trials on the same tasks and comparable environments.

## 6. Predeclare the Decision Rule

Before running the held-out comparison, define:

- minimum target-task improvement;
- maximum allowed regression;
- guard invariants;
- cost/latency limits if validly measurable;
- minimum independent task and trial counts;
- how ties, flaky results, and grader disagreement are handled.

If no defensible threshold exists yet, use `pilot`, not `promote`.

## 7. Inspect Transcripts and Outcomes

Sample successes and failures from both A and B. Verify that the score reflects the intended mechanism, not task leakage, grader exploitation, excessive tool use, or a new failure hidden by aggregate metrics.

## 8. Decide and Archive

- `promote` only when B meets the predeclared rule and all guards.
- `pilot` when the direction is promising but evidence is limited.
- `reject` when benefit is absent or regressions exceed limits.
- `rollback` if later production evidence contradicts the promotion assumptions.

Archive the baseline, candidate, task manifest, raw results, sampled trajectories, grader versions, verdict, and rationale. Keep rejected candidates as negative knowledge so future agents do not rediscover them without a changed hypothesis.

## Minimal Promotion Report

```markdown
# Skill promotion: A -> B

## Target failure
## Baseline and candidate diff
## Task matrix and leakage controls
## Environment and trials
## Outcome results
## Transcript findings
## Regressions and cost
## Verdict
## Rollback trigger
```
