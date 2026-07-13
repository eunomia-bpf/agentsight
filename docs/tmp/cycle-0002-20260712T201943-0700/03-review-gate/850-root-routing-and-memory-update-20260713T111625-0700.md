# Root Routing And Canonical-Memory Update

**Node:** `850-root-routing-and-memory-update-20260713T111625-0700`  
**Timestamp:** 2026-07-13T11:16:25-07:00  
**Phase:** BUILD_AND_EVALUATE  
**Cycle:** `cycle-0002-20260712T201943-0700`  
**Gate:** REVIEW  
**Role:** owning root disposition after whole-paper review and meta-review  
**Status:** COMPLETE; pending independent REVIEW outer audit  

## Decision

The root accepts the whole-paper review's current-paper verdict and its
selection of one next RQ2 experiment, subject to the two boundary corrections
from the dedicated meta-review.

- Current AAAI-27 verdict: **Reject / incomplete-but-promising**.
- Exact thesis retained: **“Agent observability needs profiling, not only
  debugging.”**
- Original AgentProf story retained.
- Operations and operation stacks remain the two core abstractions.
- The four fixed RQs remain resource attribution, real-problem localization,
  tag accuracy, and profiling cost.
- No idea change is accepted, so `docs/idea-story.md` receives no new entry.
- No paper edit is authorized in this REVIEW gate.
- No skill, AGENTS, state-machine, code, or Git action is authorized.

The next state is one EXPERIMENT gate for fixed RQ2 using the official
AgentTelemetry artifact. The experiment exists to earn the strong localization
claim, not to replace it with an easier task.

## Inputs

This disposition reads and accepts the routing relationship among:

1. the user-requested whole-paper review's
   [`final verdict and routing`](review-001/400-cycle-change-audit-final-verdict-and-routing.md);
2. the dedicated fresh
   [`meta-review`](800-meta-review-20260713T111135-0700.md);
3. the completed
   [`EXPERIMENT gate report`](../01-experiment-gate/999-gate-report-20260713T110626-0700.md);
4. the completed
   [`WRITE gate report`](../02-write-gate/999-gate-report-20260713T103942-0700.md);
5. the fixed user intent in [`docs/user-instruction.md`](../../../user-instruction.md);
6. the current experiment frontier in
   [`docs/evaluation.md`](../../../evaluation.md); and
7. the current literature/search frontier in
   [`docs/background-related-work.md`](../../../background-related-work.md).

The scientific verdict remains subject to the separate independent REVIEW
outer audit, which must inspect the four review nodes and their primary-source
coverage rather than treating this root disposition as evidence.

## Accepted Scientific Routing

### Fixed RQ

**RQ2: Does Profiler Output Correspond to Real Problems?**

### One tested hypothesis

On disjoint held-out AgentTelemetry fault families and agent frameworks, a
target-blind AgentProf semantic operation profile reduces the fraction and
weighted amount of official fault-bearing operations inspected to reach 80%
macro recall, relative to the strongest same-information non-oracle baseline,
while meeting the same recall threshold.

This hypothesis is inside RQ2. It does not change the thesis, story, RQ, RQ3,
or RQ4.

### Source eligibility

The next gate uses the official AgentTelemetry package/repository and published
protocol. REAL PREFLIGHT must verify that the official artifact exposes
span/step fault targets or first-anomaly identities at the localization unit
claimed by the experiment.

If it exposes only run-level fault labels, that source is **ineligible for this
selected experiment**. The gate records the ineligibility and returns to
REVIEW. It may not silently downgrade RQ2 to run triage, wait for a human, or
manufacture new labels.

### Approved-plan boundary

One ordinary Markdown plan defines before held-out target scoring:

- development and held-out fault families and frameworks;
- visible fields and target-blind tag/mapping path;
- operation-stack order and ranker;
- 80% macro-recall inspection metric;
- strongest same-information non-oracle baselines;
- complete fault-by-framework matrix; and
- one success condition for RQ2.

This is ordinary scientific experimental discipline, not a freeze protocol.
No Git hash, seal, packet, manifest, attestation, key, immutable registry, or
executable finalizer is required.

### Smallest strong comparison

The plan-review loop must select the smallest set that includes:

- native trace or per-session inspection;
- the strongest equal-information conventional multidimensional aggregation
  over every field available to AgentProf; and
- AgentTelemetry's strongest applicable non-oracle analysis.

An oracle is optional only as an upper bound. AgentProf may not receive extra
target identity, fields, tuning, or evaluation budget.

### Primary outcome and completion

The primary decision is operations/spans and weighted work inspected to reach
80% macro recall of official fault targets. The tested hypothesis is supported
only if the paired uncertainty interval for work reduction excludes zero
against the strongest same-information non-oracle baseline while the recall
target is met.

After one real preflight establishes eligibility, run every approved held-out
fault-by-framework cell to terminal status. A smoke or prefix is not a result.
Whatever the sign, close this one experiment before the next paper-level
choice.

### Explicit exclusions

- No third AgentProcessBench score or threshold variant.
- No run-level fallback task.
- No handmade fault labels.
- No RQ3 tag-accuracy program inside this experiment.
- No RQ4 cold/warm profiling-cost program inside this experiment.
- No idea refinement or full writing loop in BUILD_AND_EVALUATE.
- No second experiment inside the same gate.

## Meta-Review Disposition

### Direction

Accepted. The exact thesis, original story, contribution chain, two core
abstractions, and four RQs show no post-freeze drift. The reviewer's speculative
“semantic continuation of causal tracing” phrase remains an experiment-design
motivation only; it is not copied into the paper, contribution list, or idea
history.

The evidence deficit is not a story-change trigger. The next experiment seeks
stronger evidence for the existing positive hypothesis rather than narrowing
it or inserting internal negative results into the reader-facing paper.

### Efficiency

Accepted. Cycle 0002 stayed inside RQ2 too long by running five constructions
before returning to whole-paper prioritization. The next EXPERIMENT gate runs
one experiment, completes it, receives result review and outer audit, closes,
and returns to REVIEW whatever the sign.

The next WRITE gate is targeted and phase-permitted. It either integrates newly
authorized evidence into the affected surfaces or records a detailed no-paper-
change node. It does not invoke idea refinement or the full writing loop.

### Maintenance

Accepted. Existing rules already cover the observed failures; no new skill or
AGENTS rule is warranted, and the user currently forbids skill changes.
`scripts/check_progress.py` is absent, so no progress output is invented. The
absence is diagnostic only and does not block routing.

`docs/questions-for-author.md` has no open question. The source-granularity
uncertainty is resolved autonomously by REAL PREFLIGHT, not by a new human
question.

## Canonical-Memory Changes

Only two live canonical frontier files were changed.

### `docs/evaluation.md`

- Replaced the stale RQ2 “WRITE then future REVIEW selects” text with the
  completed-review selection.
- Named the one AgentTelemetry RQ2 experiment and its 80% macro-recall
  inspection-work decision.
- Recorded the official span/step or first-anomaly eligibility boundary.
- Recorded autonomous source-ineligible behavior for run-level-only labels.
- Excluded RQ3 and RQ4 subprograms from the RQ2 experiment.
- Replaced “frozen tagger” with the simpler “approved fixed tagger” wording for
  the still-open RQ3 frontier.

The file is 197 lines and all local Markdown links resolve.

### `docs/background-related-work.md`

- Replaced the stale “current REVIEW is selecting” state with the completed
  AgentTelemetry selection.
- Retained the prior closest-work and five completed RQ2 branch boundaries.
- Replaced “frozen semantic profile/fields” terminology with ordinary
  plan-defined/approved-plan language.
- Added the official localization-target eligibility boundary.
- Kept RQ1, RQ3, and RQ4 as later sibling branches rather than bundling them
  into this experiment.

The file is 183 lines and all local Markdown links resolve.

No paper, idea-story, user-instruction, question, source code, result artifact,
skill, AGENTS file, or submodule file changed in this node.

## Historical Process Findings Retained

The root accepts the review/meta-review's record that cycle 0002 had material
process defects:

1. five experiments ran inside one EXPERIMENT gate;
2. idea/full-writing loops ran during BUILD_AND_EVALUATE;
3. WRITE entered before EXPERIMENT's outer audit and `999` closeout;
4. writing/review reports used Git checks and per-node hashes despite the user
   prohibition;
5. chronology and reviewer freshness were overstated in some reports; and
6. repeated control prose consumed effort without improving the scientific
   discriminator.

The later EXPERIMENT `999` repairs the missing closeout artifact but does not
erase the historical ordering violation. No result rerun or history rewrite is
needed. The correction is to follow the existing simpler loop next time.

## Exact Handoff Pending Outer Audit

If the independent REVIEW outer audit passes, close this gate and enter exactly
one EXPERIMENT gate with:

- fixed RQ2;
- the AgentTelemetry official source;
- the one hypothesis above;
- source eligibility inside REAL PREFLIGHT;
- three to five serial plan reviews as required by the experiment workflow;
- complete FULL execution if eligible;
- result review and independent outer audit; and
- return to REVIEW whatever the sign.

If the outer audit finds a material review/source/routing defect, repair this
REVIEW gate before transition. Do not wait for human judgment and do not use a
repair finding to change the thesis or RQs.
