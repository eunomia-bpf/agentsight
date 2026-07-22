# Independent Plan Review

Reviewed: 2026-07-20
Scope: the current `plan.md` against `docs/design.md`, `docs/evaluation.md`,
`docs/background-related-work.md`, and the blocked result/result review in
`experiment-20260720T003908-0700/`.

## Verdict: BLOCK

The direction is scientifically appropriate: the two-condition comparison uses
one source store, gives Raw full-fidelity navigation, confines the proposed
condition to deterministic relations, includes both coding and non-coding work,
and explicitly limits this run to a two-episode mechanics preflight with no
effect claim. AgentTether, OCPM, DyG-RAG, and Full HTIR need not be executed in
this mechanics preflight; they have correctly scoped later roles.

Execution is nevertheless blocked by four result-invalidating defects. Fixing
them does not authorize a larger pilot. At most, the declared one coding and one
OR-Space supervisor episode may run after a revised plan passes review.

## Blocking findings

### 1. The proposed condition does not isolate persistent-workspace relations

`action_context` is available only to Trajectory (`plan.md:93-101`), but it is a
generic chronological neighborhood operation, not a persistent-workspace
relation. Raw already has ordered range reading. A gain could therefore come
from cheaper local chronology rather than artifact lifecycle, cross-goal state,
or action-to-effect structure, invalidating the declared treatment.

Move `action_context` into the shared Raw operation set or remove it. The
additional condition should contain only exact workspace-specific relations,
such as source-backed `effects`, `artifact_history`, and cross-goal artifact
continuity. Keep every optional recurrence, validation, importance, ranking,
and semantic helper absent from this preflight.

### 2. The plan asserts, but does not specify, the source/action ownership repair

The previous real preflight failed because non-CWD `dirfd` resolution was wrong,
many fast system effects could not be bound to native actions, and stdout
arrival time was not a valid action-start clock. The new plan says that syscall
result, decoded directory FD, time interval, call, session, goal, and scope must
all agree (`plan.md:40-48`), but it does not identify the source-native field or
instrumentation that supplies a stable call start/end interval or call identity
for the system record. A syscall does not acquire an Agent call ID merely by
being close in time.

Before capture, specify the executable ownership rule field by field: the
authoritative native start/end source, process-tree ownership, cwd/`dirfd`
resolution at syscall time, syscall return handling, concurrency rule, and the
exact fallback to `unknown`. If the native source cannot provide a stable call
interval/identity, do not infer it from sidecar arrival time; either add
source-native instrumentation or leave the effect unknown. The preflight cannot
repeat the previous ambiguous temporal join and call it a repaired source
contract.

### 3. Gold construction is not blinded and its sequence is internally impossible

The experts are explicitly shown hidden intervention provenance before labeling
(`plan.md:155-157`). That can reveal the intended pathology, evidence location,
and repair, making the reference answer circular. Neutral supervisor filenames
do not repair leakage into gold. In addition, step 3 verifies closure for
“every gold evidence action” before gold is created in step 5
(`plan.md:178-182`).

Experts must first label from the complete ordinary source store, boundaries,
goals, evaluator results, and worker-visible harness/specification bytes while
blinded to perturbation assignment, pair identity, repaired sibling, and hidden
intervention provenance. Freeze those labels, then reveal provenance only for a
separate manipulation/counterfactual check and adjudication rule declared in
advance. Reorder execution to: capture and build the complete store; create and
freeze blinded gold; verify closure over every gold action plus all
task-relevant successful effects and evaluator actions; then materialize the
paired interfaces and run supervisors.

The scorer is also under-specified. “A minimal accepted set” is insufficient
when multiple evidence sets or renamed paths can be equivalently sufficient.
Before inference, freeze the exact pathology, accepted-minimal-set evidence,
path, earliest-action, intervention, confidence/abstention scoring rules,
including alternate accepted sets and rename/path equivalence. Synthetic tests
alone do not define these metrics.

### 4. The comparison is not yet executable or frozen

The plan postpones all CLI syntax (`plan.md:234-240`) and names no supervisor
model/revision, context size, tokenizer/template, total returned-token limit,
total returned-byte limit, per-call result limit, search `k` ceiling, record
serialization, ROUGE-L tokenization/implementation, range bounds, timeout,
decoding values, or seed. Those choices determine Raw competence and can change
the outcome; freezing them later during implementation is tuning, not an
approved plan.

The claim that 100 calls is “AggAgent's published evaluation ceiling” also
needs correction. AggAgent supplies the full-fidelity search/segment interface
precedent and uses a rollout-level tool-call cap; that is not evidence that 100
is the uniquely fair query budget for this diagnosis task. Pin the exact
official precedent and adaptation, then state every numerical value and one
real command for store construction/verification, either condition, and
scoring. Raw search must freeze the searchable record unit, text
serialization, ROUGE-L variant/tokenization, tie-breaking, maximum `k`, and
response truncation/continuation behavior. `read_record` and `read_range` must
have deterministic bounded behavior so an avoidable oversize request does not
make Raw artificially incompetent.

Use the source-native model/tool execution path plus the smallest necessary
adapter. Do not turn hashes, ledgers, synthetic gates, or a project-authored
budget-control framework into a separate research artifact. They are only
correctness machinery for this comparison.

## Baseline and scope judgment

AggAgent-style Full Raw Retrieval is the correct strongest main baseline for
this preflight if the competency details above are fixed: it represents the
credible competing position that complete evidence plus bounded on-demand
navigation is sufficient and no workspace projection is needed. Every
bottom-level fact returned by Trajectory must remain retrievable byte-for-byte
through Raw under identical source membership and model-visible budgets.

State Diff and Counts are correctly deferred controls for a later effect pilot.
AgentTether is a later structured diagnosis comparison on compatible failed-run
cases; OCPM is a later established lifecycle/process alternative; Full HTIR is
required for compatible harness-diagnosis claims; DyG-RAG is a closest-mechanism
citation/optional retrieval comparison, not a mandatory mechanics row. Adding
them now would not repair any of the four blockers above.

## Admission boundary after repair

A revised plan may admit only the declared mechanics path:

- one excluded SWE-bench Verified development episode;
- one excluded OR-Space development episode;
- one Raw and one Trajectory supervisor run per domain;
- repaired siblings used only for the predeclared post-label manipulation check;
- reproducible interface, scoring, source-closure, leakage, and budget checks;
- no accuracy, superiority, generalization, diagnosis, or paper-level effect
  claim from these two episodes.

No model run is admitted under the current plan.

## Independent Review Round 2

Reviewed: 2026-07-20
Verdict: **BLOCK**

Three Round 1 blockers are closed at the plan level: `action_context` has been
removed from the proposed-only interface; the native interval,
process-subtree, CWD/`dirfd`, syscall-success, ambiguity, `no_effect`, and
`unknown` rules are explicit; and the supervisor model, source/search
serialization, ROUGE-L rule, token/byte/call/response budgets, decoding,
timeout, continuation behavior, and executable commands are frozen. The gold
sequence and scoring definitions are also otherwise complete.

One decision-critical contradiction remains. The Development Workloads section
still says each repaired sibling is “available to gold experts,” while the
Independent Gold section requires those same experts and adjudicator to be
blinded to the repaired sibling until gold is immutable. Both cannot be true,
and showing the sibling before label freeze would reveal the intended repair
and can circularly determine pathology, evidence, and intervention truth.

Replace the former statement with an unambiguous ownership rule: repaired
siblings and hidden provenance are unavailable to both labeling experts and the
adjudicator, and become available only to the separate manipulation auditor
after immutable gold is frozen. With that single textual contradiction removed,
no Round 1 decision-critical blocker remains, and only the declared two-episode
mechanics preflight—not an effect pilot or scientific claim—would be admissible.

## Independent Review Round 3 — Final

Reviewed: 2026-07-20
Verdict: **PASS**

The remaining Round 2 contradiction is closed. The current plan states that the
counterfactual repaired sibling is retained only for the post-gold manipulation
auditor; both labeling experts and the adjudicator remain blinded to sibling,
assignment, and hidden provenance until gold is immutable. This agrees with the
preflight sequence and prevents repair information from defining the labels.

No blocker from Rounds 1–2 remains. This PASS admits only the frozen
two-development-episode mechanics preflight: one SWE-bench Verified episode and
one OR-Space episode, each run once through Raw and Trajectory under the stated
source, model, budget, scoring, blinding, and veto rules. It does not admit a
larger pilot and cannot support an effect, superiority, generalization, or
paper-level scientific claim.
