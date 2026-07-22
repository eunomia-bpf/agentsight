# Target-Goal Estimand Closure

Created: 2026-07-19T21:58:59-07:00
Parent: BOOTSTRAP Step 0001, outer-orchestrator return from terminal B7
Status: accepted scientific-contract decision; no experiment or model run

## Question

What exactly is one scientific outcome when the representation contains several
prior goals plus one selected target goal? In particular, may prior-goal labels
contribute positives, agreement, evidence, intervention, or baseline coverage to
the target-goal supervisor experiment?

## Options Considered

### A. Treat every included goal as an outcome

This would increase the apparent sample size but changes the paper's unit. Goals
within one interval share workspace state, prior history, Agent, harness, task
family, and often actions. It would require a hierarchical estimand, within-
interval correlation model, new power analysis, and rules for which earlier
goals become history for each later goal. The terminal plan did not define any
of these. This option is rejected for the next evidence program.

### B. Union all goal labels into one interval outcome

This asks whether *anything* pathological happened anywhere in the history, not
whether the supervisor correctly diagnoses the selected ongoing/target work.
Prior positives could approve a benchmark whose target goals contain no positive
cases. It also makes Full-History structurally advantaged by changing the label
scope. This option is rejected.

### C. One outcome vector for the selected target goal

The full history remains model input and explanatory evidence, but the outcome
is the target goal. This directly tests whether prior workspace process state
helps diagnose a later goal while keeping one observation per registered run.
It matches the Full-versus-Target representation contrast and preserves cluster-
aware independence. This option is accepted.

## Frozen Estimand

For each scientific workspace supervision interval $i$, let $g_i^*$ be the sole
target goal selected by the label-independent registry rule. The RQ1 outcome is:

\[
Y_i = (P_i, E_i, A_i, I_i, \tau_i, C_i),
\]

where all components refer to $g_i^*$ only:

- $P_i$: four target-goal pathology labels;
- $E_i$: minimal sufficient typed evidence IDs for each target label;
- $A_i$: affected target-goal artifact/state objects;
- $I_i$: target-goal retrospective intervention need and action;
- $\tau_i$: earliest action **inside the target goal** after which the
  intervention is supportable; and
- $C_i$: confidence/insufficient-evidence status for the target judgment.

Every positive pathology and every positive intervention evidence set must cite
at least one target-goal action/effect. Prior-goal evidence may additionally be
cited when it establishes recurrence, stale state, abandoned artifacts, or a
harness pattern, but prior evidence alone cannot make a target label positive.
If the target behavior never manifests the pathology, the target label is
negative even when an earlier goal was positive.

## Role Of Prior-Goal Truth

Human experts may annotate prior goals once, but those records are auxiliary:

- they establish whether a target pattern is new, recurring, or related;
- they let the study verify that Full-History evidence actually contains the
  earlier support claimed by a target diagnosis;
- they support descriptive H5 mechanism analysis and qualitative cases; and
- they remain hidden from all supervisor conditions and representation
  construction.

Prior-goal records never enter target prevalence, positive counts, pathology or
intervention agreement, evidence/earliest-action agreement, insufficient-
evidence rates, HTIR shared-label coverage, diagnosis metrics, power/sample-size
nuisance estimates, or the held-out denominator. They are not additional
samples.

## Representation And Comparison Consequences

- Full-History Raw and Full-History Trajectory see $H_0\rightarrow g_i^*$.
- Target-Only Raw and Target-Only Trajectory see only $g_i^*$ and its atomic
  boundary state.
- All four predict the identical $Y_i$.
- The longitudinal mechanism statistic is

  \[
  \Delta_{long} =
  (M_{Traj,full}-M_{Traj,target}) -
  (M_{Raw,full}-M_{Raw,target}),
  \]

  computed pairwise on the same target goals and cluster-resampled by frozen
  workspace/task family.
- A positive Full-History Trajectory result without positive
  $\Delta_{long}$ cannot support a distinct longitudinal-structure claim.

State Diff, Counts, Native Report, Session Local, OCPM, and Full HTIR also predict
the same target-only $Y_i$. Full HTIR shared-target coverage counts only
compatible intervals whose **target goal** is independently positive for
`validation_gap` or `harness_waste`.

## Admission Consequences

Every truth gate in a replacement feasibility plan is target-only:

- sufficient evidence;
- pathology prevalence and positive counts;
- raw agreement, AC1, kappa, and positive agreement;
- evidence/action/artifact and earliest-support agreement;
- intervention need/action/earliest agreement; and
- HTIR shared-target positive coverage.

Development cases remain excluded, and prior goals cannot rescue a failed target
gate. If target positives or agreement are insufficient in either domain, the
four-pathology/intervention claim fails and returns to the idea gate.

## Decision And Routing

The target-goal estimand is accepted as the only next-plan option. This is a
scientific-contract decision after the terminal plan return, not a fourth review
or retroactive approval of B7. A new experiment node must have a new identifier,
state this estimand at the top of its admission rules, preserve the reviewer-
confirmed atomic/Raw/Full-Target/cluster/OCPM/HTIR contracts, and receive a fresh
independent plan review before implementation or supervisor inference.
