# Evaluation Frontier

## Research contract

The active study asks whether a process representation can improve an automatic
supervisor's *real intervention outcome*. It does not ask a person or another
Agent to label what went wrong. One experimental unit is a frozen persistent-
workspace checkpoint immediately before a fresh worker session. Every condition
starts from byte-identical state, receives the same future task, and is graded by
the benchmark's unmodified executable oracle.

Human annotation, human adjudication, Agent-generated substitute labels, and an
LLM judge as primary truth are outside this experiment. Visual quality and human
log-reading speed are also outside the scientific claim.

## Open research questions

All paper-level RQs remain open. The Harness Bench run below established
mechanics and a stopping decision; it did not estimate a treatment effect.

| RQ | Evidence required | Current status | Decisive next action |
|---|---|---|---|
| RQ1 objective intervention utility | From the same frozen checkpoint, compare Workspace Trajectory Retrieval with Full Raw Retrieval, a generic matched control, and no intervention under the same supervisor, worker, prompt, tool, token, time, and continuation budgets. Execute every continuation and score its final workspace with the official oracle. | Open. Task-058 exercised checkpoint/fork/continue/oracle mechanics, but all three supervisors used zero evidence tools. The registered six-task headroom gate admitted only 3/6 tasks rather than the required 4/6. | Do not rerun or subset the inspected Harness tasks. Qualify a scientifically distinct objective workload with adequate headroom and mandatory, matched evidence-tool engagement. |
| RQ2 information contribution | After an RQ1 effect exists, remove `artifact_history`, `session_diff`, and `effects` one at a time and measure the change in realized continuation outcome. Test earlier-session source access separately by removing that scope identically from Raw and Trajectory. | Not admitted until RQ1 beats both Raw and the generic matched control. | Run query ablations and the matched source-scope contrast only after an admitted RQ1 result. |
| RQ3 generalization and safe supervision | Held-out task/workspace families across coding and scientific work, multiple workers/models, intervention harm, abstention, and budget curves. | Open. The current Harness configuration stopped at headroom. SWE Context Bench and CORE-Bench are candidate coding and scientific-work assets, subject to runner qualification. | Freeze structural eligibility before observing worker scores. Verify persistent lineage, a real fresh-session boundary, unchanged official evaluation, no-op headroom, and tool engagement separately in both domains. |

## Conditions and estimand

The prefix worker executes the official task until a preregistered structural
boundary. The harness freezes the workspace and source sessions, then creates
four forks:

1. **No intervention:** continue the next official worker session unchanged.
2. **Generic control:** add a budget-matched request to reflect, inspect, and
   validate, without exposing prior trajectory evidence.
3. **Full Raw Retrieval:** a supervisor may search and read the complete source
   records through a bounded interface and emit one intervention or `ABSTAIN`.
4. **Workspace Trajectory Retrieval:** the same Raw interface and budget plus
   deterministic, source-linked workspace relations; it emits the same output
   schema.

The bounded intervention is appended to the otherwise unchanged official next
prompt. The same worker configuration continues every fork. No model predicts a
counterfactual score: all four futures execute and the official oracle grades
the resulting workspaces.

The registered primary estimand is the paired official-outcome difference
Trajectory-minus-Raw. The mandatory competing contrast is
`Gain(Trajectory) - Gain(Generic)`, where each gain is measured relative to No
Intervention within the same checkpoint. No Intervention separately anchors
realized benefit and harm; it is not a third superiority estimand. A Raw tie
with lower cost supports only compression or retrieval efficiency, while a tie
on the mandatory Generic contrast rejects the stronger representation claim.

## Validity and parity rules

- Freeze the supervisor model, worker model, prompts, checkpoint, future task,
  tool schemas, token/byte/tool/time budgets, timeout, continuation budget, and
  official evaluator before condition execution.
- Split by complete workspace/task-family clusters. Related repositories,
  histories, task variants, and derived slices cannot cross held-out boundaries.
- Select workload eligibility and the structural checkpoint without using
  observed treatment scores. A failed headroom gate stops the complete matrix;
  it never licenses choosing only the lower-scoring tasks.
- Every Trajectory relation must cite source records retrievable by Full Raw.
  Both interfaces receive identical Raw membership and returned-byte,
  rendered-token, and tool-call ceilings.
- The matched engagement gate requires one successful condition-specific call:
  a current-workspace inspection for Generic, a Raw-history call for Full Raw,
  and a registered relation query for Workspace Trajectory. A relation response
  counts only if the returned payload exposes at least one registered source ID;
  an empty successful API response does not count. A condition that misses its
  family validates only infrastructure, not the treatment or matched control.
- Every fork begins from a byte-identical checkpoint. Supervisor input excludes
  future prompts, hidden fixtures, evaluator implementation/results, repaired
  siblings, and outputs from other conditions.
- Run the official evaluator twice on each completed workspace and retain both
  payloads plus their joint hash. Disagreement invalidates that unit.
- Required outputs are a bounded intervention or `ABSTAIN`, source IDs for any
  evidence used, and complete supervisor/worker token, byte, tool, latency, and
  cost accounting.
- Primary truth is the unmodified executable outcome. An Agent Nebula output,
  summary, semantic tag, or visualization cannot define success.

## Measures

Primary measures are checkpoint-matched official outcome, paired outcome
difference, and harm rate relative to no intervention. Secondary measures are
abstention utility, supervisor and continuation tokens, returned bytes, tool
calls, latency, and total inference cost. Report task-level results and paired
uncertainty; do not treat repeated continuations from one task family as
independent benchmark instances.

For stochastic workers, repeat all conditions from the same checkpoint with a
preregistered seed/run schedule and randomize condition order within each
checkpoint. A positive claim must survive the generic control and a matched
total inference-budget comparison.

## Completed Harness Bench dependency check

The implementation and no-model preparation gate passed on Harness Bench
revision `1025086a446653702b80cfb48babbeec35db6b2c`. The strict P0 used task
`058-multiday-project-state` at its Day-2/Day-3 boundary. Two prefix Codex
sessions produced 133 Raw records and seven normalized actions. Immutable
snapshots, fork manifests, stable argv/environment, worker network denial,
hidden-source denial, and duplicate executable oracle evaluation passed.

The three supervisor conditions shared one source/model/budget identity, but
each made zero retrieval calls and therefore exposed no source IDs. Official
scores were 0.8594 for No Intervention, Raw, and Workspace Trajectory, and
0.9219 for Generic. This is a mechanism result only: it gives no evidence that
Trajectory relations were used or helped.

The registered no-op headroom screen then ran once on six fixed tasks in this
order:

| Task | Official score |
|---|---:|
| `057-interruption-resume` | 0.6154 |
| `058-multiday-project-state` | 0.8594 |
| `059-event-update-replan` | 1.0000 |
| `060-task-cancellation-cleanup` | 1.0000 |
| `103-policy-update-replan-diff` | 1.0000 |
| `105-partial-batch-resume-ledger` | 0.4994 |

The preregistered gate required at least four of six scores below 0.95. Only
three qualified, so `full_matrix_admitted=false`. The full comparison did not
run, and the observed low-score subset must not be reused as if it had been
selected prospectively.

The authoritative current artifacts are:

- `docs/tmp/bootstrap/step-0001-20260719T181243-0700/experiment-20260721T021426-0700/plan.md`
- `docs/tmp/bootstrap/step-0001-20260719T181243-0700/experiment-20260721T021426-0700/plan-review.md`
- `docs/tmp/bootstrap/step-0001-20260719T181243-0700/experiment-20260721T021426-0700/result.md`
- `docs/tmp/bootstrap/step-0001-20260719T181243-0700/experiment-20260721T021426-0700/result-review.md`

## Next objective workload qualification

The next experiment is not a rerun of the inspected Harness slice. Before any
effect matrix, a small preregistered qualification checks two candidate domains:

- **Coding:** SWE Context Bench only if related-task sequences preserve one
  persistent workspace lineage across a real fresh-session boundary; otherwise
  use SWE-Interact or another objective persistent-workspace workload.
- **Scientific work:** CORE-Bench only if the official runner can pause at a
  structural boundary, resume in a fresh worker session, and apply its unchanged
  executable evaluator after continuation.

For each domain, freeze structural eligibility before no-op execution. Then run
a separate no-op headroom gate and a mandatory evidence-tool-engagement P0. Both
must pass before No Intervention, Generic, Raw, and Trajectory are compared.

## Raw evidence and reports

- Active BOOTSTRAP step: `docs/tmp/bootstrap/step-0001-20260719T181243-0700/step-report.md`
- Current experiment directory: `docs/tmp/bootstrap/step-0001-20260719T181243-0700/experiment-20260721T021426-0700/`
- Current implementation examples: `agentvis/examples/`
- Visualization design: `docs/repository-nebula.zh-CN.md`
