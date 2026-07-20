# Independent Plan Review

The reviewer explicitly read and used `research-experiment-design`, its plan
template, the fixed thesis and RQs, the complete idea history, the current RQ3
frontier, and the user's task-semantic stack instruction. The reviewer was
read-only and was told not to expand the experiment with additional baselines,
checkers, freeze protocols, or a second research question.

## Round 1 — REVISE

One must-fix remained. The plan named four frameworks but did not fix the
deterministic operation-to-evidence join across the five actual source layouts:

1. MiniSWE message trajectory;
2. SWE-agent trajectory elements;
3. Terminus2 command/response episodes;
4. OpenHands native events; and
5. OpenHands maximal tool history.

The reviewer found that count equality alone could silently associate an
intent or result with the neighboring operation. That would invalidate the
task-progress conclusion. The requested repair was narrow: define alignment by
the existing `source_ref` and source action, join OpenHands observations through
event `cause` or exact tool-call id, align Terminus2 commands to response
episodes, and preflight all five layouts. No new baseline or review layer was
requested.

The reviewer otherwise confirmed that the candidate uses source-native task
progress rather than system fields, ordinary B-cubed gives a fair decision on
the matched complete population, and the experiment changes neither thesis,
RQ, story, nor paper.

## Repair

The plan now defines all five joins, makes missing, duplicate, mismatched, or
incomplete mappings invalidate the run, and expands REAL PREFLIGHT to one
complete representative per layout. It also specifies that Terminus2 results
remain absent unless the archive uniquely attributes them to one command; a
later batch terminal context is not presented as a per-command result.

## Round 2 — APPROVE

- must-fix: **0**
- optional polish retained: report source-evidence availability by framework
  and layout; do not attribute a composite result to one field without an
  ablation; do not claim nested-depth or generated-label accuracy from a flat
  stage-partition experiment.
- final disposition: **approved for REAL PREFLIGHT**

The final review also recommended using the smallest complete representative
of each source layout for preflight. The plan adopts that recommendation.

## Implementation Readiness Review

The same independent reviewer then inspected the implemented evaluator against
the approved plan and exercised the source-only five-layout preflight path.
The first pass returned `REVISE` for three must-fix defects:

1. three MiniSWE/OpenHands helpers were referenced through the wrong imported
   module, making those layouts fail before model inference;
2. resume validation omitted model, seed, system prompt, and grammar from the
   cached request identity; and
3. OpenHands native events did not yet read the common model-response message
   in `tool_call_metadata`, omitting real source-native intent.

The evaluator now imports the helpers from their defining source module,
hashes the complete model/system/grammar/user request and validates all model
configuration on resume, and combines the OpenHands event thought with the
source model-response content without duplication.

On the second pass the reviewer returned **APPROVE, zero remaining must-fix**.
The reviewer actually reconstructed one smallest complete trajectory per
layout, 5/5 successfully:

- MiniSWE: 20 operations, intent on 20, result on 19;
- OpenHands native events: 20 operations, intent on 19, result on 19;
- OpenHands maximal tool history: 20 operations, progress on 20, result on 20;
- SWE-agent: 20 operations, intent on 1, result on 18; and
- Terminus2: 20 operations, intent/progress on 20 and result on 0, preserving
  the approved absent-result policy.

This was source-only readiness validation, not REAL PREFLIGHT and not a paper
result. The real model, grammar, persistence, and scorer path still had to run.
