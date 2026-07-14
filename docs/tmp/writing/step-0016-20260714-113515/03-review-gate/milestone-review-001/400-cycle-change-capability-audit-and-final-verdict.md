# Cycle-Change and Capability Audit with Final Verdict

**Review target:** complete `docs/paper/` manuscript after Step 0015
**Venue lens:** AAAI-27 main technical track, cross-domain systems/AI
**Review sequence:** blind read → primary-source search → source-informed reread → root routing audit

## Executive Verdict

**Current recommendation: weak reject, approximately 4/10.** The paper has a coherent, potentially important thesis and substantial real/public evidence, but one acceptance-critical question remains insufficiently consequential for an AI audience: RQ2 currently shows that profiles concentrate independently defined problem signals and reduce inspection work, yet it does not directly show that the resulting view helps an AI analyst make a better diagnosis or prioritization decision.

This verdict does **not** authorize a smaller thesis, a replacement story, a fifth RQ, or another benchmark merely for coverage. RQ1, RQ3, and RQ4 have bounded positive answers adequate for the current iteration. The next action stays inside RQ2 and tests one narrow consequence of the existing profile.

## What the Four-Round Review Established

### Stable strengths

1. The thesis remains distinctive and attractive: agent observability needs profiling, not only debugging.
2. The system preserves source-linked, additive measurements across intent, tool, and downstream system effects rather than offering only a renamed trace grouping.
3. The evaluation uses public, real-world agent traces and independently supplied labels across several problem families.
4. RQ1 has scoped attribution evidence, RQ3 has partial but positive tag evidence, and RQ4 has a direct cost characterization.
5. The paper satisfies the AAAI-27 page boundary: seven content pages followed by references-only pages.

### Remaining acceptance blocker

The strongest external alternatives already aggregate traces and agent behavior: pprof exposes selectable tag dimensions; Perfetto supports SQL aggregation and metrics; LangSmith and Datadog expose cross-trace categories; recent agent work turns recurring trajectory features into diagnoses or interventions. Against that context, compactness alone is not enough. The paper should demonstrate a simple decision consequence using the profile it already built.

### Non-blocking limitations

- The generic projection/hierarchy operation is not itself novel; novelty must remain attached to the source-linked cross-layer responsibility model and its measured use.
- Current end-to-end source ingestion is demonstrated on supported agent sources rather than every benchmark format.
- RQ3 evaluates the current tag surface under bounded conditions rather than claiming universal semantic inference.
- Broader human-developer productivity and deployment scale remain future extensions, not prerequisites for the present paper.

## Audit of the Proposed TraceElephant Counterfactual Experiment

The source-informed reviewer proposed replaying one counterfactual probe on all 220 TraceElephant failures. The root audit rejects that proposal for this iteration.

The official repository provides static localization evaluation and releases runnable code for three separate agent systems, but it does not provide a ready-made, benchmark-wide counterfactual replay API. Implementing the proposal would require coordinating Captain-Agent, Magentic-One, and SWE-agent environments, browser or container dependencies, model/API access, replay-point plumbing, and a new intervention/scoring protocol. That is a new experiment platform, not a simple reuse of the completed TraceElephant evidence. Its complexity and validity risk are disproportionate to the single remaining question.

This rejection is scientific routing, not conservative claim reduction: the larger thesis and RQ2 remain fixed while the experiment is changed to a simpler direct test.

## Selected Next Evidence Action

Run one compact **LLM analyst decision experiment** by reusing the already completed R315 materials:

- the existing six public-data tasks;
- the existing 18 visible, label-hidden packets;
- the existing balanced assignment table;
- the existing hidden scoring key;
- the already-running local Qwen3.6-27B model endpoint; and
- the existing three views: flat, fixed-session, and operation stack.

The tested hypothesis is: **under the same label-hidden analyst task and a fixed top-three selection budget, an LLM analyst using operation-stack profiles achieves higher selected-positive recall and precision than the execution-local fixed-session view, with inspected work reported alongside the decision result and flat retained as a non-selective lower bound.**

The next EXPERIMENT gate must review the exact prompt, isolated contexts, response schema, ranker control, and scoring before any full run. The minimum complete matrix is the 18 unique task-view packets: six paired task units under flat, fixed-session, and operation-stack views, with one deterministic model call in a fresh context per packet. The 144-row human assignment repeats those packets and must not be treated as 144 independent LLM trials; repeated decodes are optional sensitivity checks only. The experiment must not add a dataset, profiler run, new grouping method, new cutoff sweep, or human study. If the preflight shows that packet semantics or model output cannot support valid hidden-key scoring, the experiment returns that finding rather than expanding into a new infrastructure project.

## Cycle-Change Audit

### Files changed during REVIEW

- Added step and gate entry Markdown reports.
- Added the blind full-paper report.
- Added the external-search and source-verification report.
- Added the source-informed full-paper reread.
- Added this final verdict and routing report.

### Files deliberately unchanged

- `docs/paper/`
- `docs/evaluation.md`
- `docs/idea-story.md`
- `docs/user-instruction.md`
- all implementation and experiment artifacts
- `docs/agentpprof-paper/`
- shared skills

### Intent and drift check

- Thesis: unchanged.
- Four RQs: unchanged.
- Story scope: not narrowed or replaced.
- Negative or mixed evidence: retained with its proper tested-hypothesis boundary.
- Next action: remains within RQ2 and aims to strengthen, not reduce, the main story.

## Capability / Skill Audit

No repository-local skill or shared-skill change is warranted in this cycle. The existing experiment-design guidance already says to reuse valid evidence, prefer real/public artifacts, reject redundant work, and keep a single experiment tied to one tested hypothesis. The TraceElephant proposal was caught by applying those existing rules at routing time. Adding another mechanism or gate would duplicate policy and make the loop harder to operate.

## Gate Routing

**REVIEW → EXPERIMENT.** The paper is not yet submission-ready. Run exactly one reused-artifact R315 LLM analyst experiment, then return its reviewed result to WRITE and conduct another complete-paper REVIEW. Do not run another profiling compactness replay, another dataset substitution, or the proposed three-system TraceElephant counterfactual platform in this cycle.
