# Independent Plan Review

Plan: `plan.md`
Reviewer: `/root/rq1_plan_review`
Reviewer role: read-only; no plan-writing or implementation role

## Round 1 — 2026-07-20

**Verdict: BLOCK.** Paper-value admission passes, and Full-History Raw Retrieval
is the correct and sufficiently strong main baseline for this RQ1 pilot. State
Diff and Counts are correctly controls; OCPM, Full HTIR, and AgentRx need not be
added to this experiment. Five result-validity or executability defects block:

1. The plan makes both Full Trajectory over Full Raw and a positive
   Full-minus-Target difference-in-differences necessary for success. The first
   tests RQ1; the second is an RQ2/H5 mechanism question. A valid RQ1 result
   cannot be rejected because the separate RQ2 mechanism is negative.
2. The data-generation denominator is 24 perturbed/repaired pairs (48 worker
   episodes), while the supervisor denominator and cost use only 24 episodes.
   It is unclear whether repaired siblings are scored and whether clean
   negatives exist.
3. Gold/scoring is not executable: the intervention ontology, alternate
   sufficient evidence sets, path/rename equivalence, insufficient-evidence
   treatment, and annotator blinding order are unspecified. Evidence-ID F1 and
   recommendation F1 are project-defined rather than metrics defined by the
   cited papers; the plan must not attribute them to AgentRx/TrajAudit/REFLECT.
4. The source preflight may mark every decisive effect `unknown` and still pass,
   so the artifact-lifecycle mechanism need not engage. Task-relevant mutation,
   validation, and cross-goal lineage evidence needs a recomputable coverage
   veto; unsupported effects cannot enter gold or derived facts.
5. The plan contains no concrete task instances, perturbation/repair assets,
   condition constructor, output/scoring path, or runnable exact commands. The
   proposed Codex supervisor route also has no native tool/byte ceiling, so the
   claimed matched access is not currently enforceable without prohibited new
   control infrastructure.

**Minimum repair:** make Full Trajectory versus Full Raw the only RQ1 gate;
choose and apply one consistent 48- or 24-episode denominator; freeze the
discrete output/gold ontology, equivalence and scorer rules, metric roles, and
blinding; require complete engagement for all decisive effects; and name
source-native tasks, immutable assets, pinned supervisor/runtime, exact
commands, and a budget path that does not require a new broker.

**Non-blocking scope note:** Final State and Native Report may remain deferred
if this is explicitly a decisive pilot rather than RQ1 closure. OCPM belongs to
RQ2 and Full HTIR to RQ3; neither should be inserted here merely to increase the
baseline count. The pilot must not be generalized directly to multi-day work
without later scale evidence.

## Round 2 — 2026-07-20

**Verdict: BLOCK with two minimum repairs.** The revised plan closed the
48-episode denominator, executable gold/scoring contract, decisive-effect
coverage veto, concrete task/assets/commands, and no-broker full-context path.
Two remaining defects could still invalidate interpretation or budget parity:

1. Counts/State Diff parity still appeared in the negative RQ1 decision branch,
   so it could conflict with an otherwise positive Full Trajectory-versus-Full
   Raw result. These controls must remain non-gating mechanism interpretation.
2. The 65,536-token context bound reserved no space for the pinned 2,048-token
   generation budget. The executable invariant must apply to rendered prompt
   plus generation and forbid truncation or context shifting.

No new baseline, workload, or interface was requested.

## Round 3 — 2026-07-20

**Verdict: PASS.** The RQ1 gate is now only Full Trajectory versus Full Raw plus
the evidence-grounding veto; Full/Target, Counts, and State Diff are explicitly
non-gating. All 48 target episodes enter every condition; gold ontology,
blinding, alternate evidence sets, path/rename equivalence, abstention, output
schema, scorer, and metric roles are frozen. Every decisive effect must have
100% source-backed ownership coverage, while `unknown` effects cannot enter
derived or gold evidence. Finally, the pinned tokenizer must satisfy
`rendered_prompt_tokens + 2,048 <= 65,536`; an over-limit row is invalid and is
never truncated or context-shifted.

This PASS authorizes only the declared real preflight. It is not evidence that
the runner, source coverage, model path, or proposed diagnostic effect succeeds.
