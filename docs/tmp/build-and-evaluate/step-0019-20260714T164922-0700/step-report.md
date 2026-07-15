# Step 0019 Report — RQ2 Fixed-Reader Prioritization

**Started:** 2026-07-14T16:49:22-07:00
**Phase:** BUILD_AND_EVALUATE
**Status:** Complete
**Completed:** 2026-07-15T00:07:20-07:00
**Outer sequence:** EXPERIMENT -> WRITE -> REVIEW

## Step Objective And Fixed Contract

This step tests one hypothesis inside the author-fixed RQ2: whether one fixed
AI reader can use an operation-stack profile to prioritize independently hidden
problem-bearing groups better than an execution-local fixed-session view under
the same selection budget.

The scientific contract is unchanged:

> **Agent observability needs profiling, not only debugging.**

The two core abstractions remain operations and operation stacks. The four RQs
remain attribution, problem correspondence, tag accuracy, and profiling cost.
The authoritative `docs/agentpprof-paper` submodule is read-only. This step may
improve RQ2 evidence and permitted result text; it may not replace the paper
story, RQs, problem, contribution chain, or evaluation promise.

## EXPERIMENT Gate

### Entry And Resume Audit

At gate entry the root read `docs/user-instruction.md`,
`docs/questions-for-author.md`, the complete `docs/idea-story.md`,
`docs/evaluation.md`, the RQ2 paper section, Step 0018's review/audit frontier,
and the paused Step 0017 R315 plan and reviews. There are no unanswered author
questions. The current branch remains
`research/semantic-flamegraph-artifacts-v2`; no branch was created or switched.
The authoritative submodule is clean at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`.

Step 0018 is complete and committed as `72185649`. Its normal push remains in
the existing HTTP-500 backlog. The only pre-step worktree change is a rebuilt
`docs/paper/main.pdf`; no paper source or submodule source differs.

### Node L001 — Bounded Protocol Source Screen

**Question and entry.** Before admitting another project-authored experimental
protocol, determine whether fixed-reader trajectory diagnosis has citable
precedent, which matched baseline is strongest, and which order-bias control is
necessary.

**Method and evidence.** The bounded search opened primary arXiv and ACL
Anthology sources for AgentRx, AgentDiagnose, LLM judge position bias, and the
new adjacent TraceProbe preprint. Full queries, source judgments, and baseline
handoff are in
[`literature-20260714T164922-0700/source-screen.md`](literature-20260714T164922-0700/source-screen.md).

**Result and decision.** AgentRx is direct precedent for an LLM localizing a
failure from structured trajectory evidence; AgentDiagnose establishes a
downstream-use evaluation pattern; accepted position-bias evidence requires
hiding the existing rank and identifiers. No official method consumes R315
packets, so a small adapter is unavoidable. The single matched main baseline is
the same reader on fixed-session packets; flat and R316 visible order are
controls. The experiment passes paper-value admission because it tests the
largest current RQ2 reject argument without adding a dataset, profile method,
score, cutoff, or human dependency.

### Node E001 — Paper-Value Admission And Proposal

**Question.** Does the existing operation-stack packet help the fixed
Qwen3.6-27B reader recover hidden problem-bearing operations more accurately
than the fixed-session packet at an identical three-group budget?

**Inputs and scope.** The experiment reuses six public-data tasks, all 18 unique
R315 packets, the hidden R315 key, the R316 visible-order control, and the
already running local model endpoint. The 144 human-assignment rows are not
executed or counted as observations.

**Plan and first review.** The complete Markdown plan is
[`experiment-001/experiment-plan.md`](experiment-001/experiment-plan.md). It
freezes the paired views, rank-hiding presentation, model/server, prompt output,
metrics, decision rule, completion rule, and raw paths. It explicitly retains
raw action as an existing paper-level counterpoint rather than claiming a
universal matched victory. The fresh reviewer returned `REVISE` with three
validity repairs: balance every non-flat group across prompt positions, make the
outcome partition mutually exclusive, and state the two-attempt REAL PREFLIGHT
limit. The root accepted those repairs and rejected any scope expansion. The
revised plan now uses five cyclic rotations for each of twelve non-flat packets,
one presentation for each flat packet, 66 total fixed presentations, within-
task/view aggregation before the six paired comparisons, and a disjoint
supported/mixed/contradicted rule.

**Follow-up and next action.** The same reviewer inspected the repaired plan and
returned `APPROVE`: all groups now occupy every prompt position once, request
construction uses an explicit visible-field allowlist, scoring aggregates
rotations before task pairing, the verdict partition is disjoint, and REAL
PREFLIGHT is bounded to two command attempts. No extra model, dataset, or
baseline is required. The root independently accepts the handoff and proceeds
to implement the thin adapter and run the first real five-rotation preflight.

### Node E002 — Thin Adapter And REAL PREFLIGHT

**Implementation.** `script/r315_llm_reader_eval.py` implements only two
reviewed paths: visible-only `collect` and post-collection `score`. It creates
five cyclic presentations for each non-flat packet, assigns aliases after
ordering, sends an explicit visible-field allowlist to the reader, persists
one raw row per presentation, and aggregates results only during scoring. It
contains no profiler, tagger, ranker, label construction, threshold search, or
Git operation. `python3 -m py_compile` passes.

**Real preflight.** Attempt 1 ran all five rotations of the real
`satraj_unsafe::operation_stack` packet through the live local Qwen3.6-27B
endpoint. All five calls succeeded on their first API attempt in 20.73 seconds;
each returned exactly three valid aliases and visible evidence. Every original
group occupied every alias position once, and a raw scan found zero original-ID
occurrences in model requests. The hidden key was absent from collection. The
complete record is
[`experiment-001/real-preflight.md`](experiment-001/real-preflight.md), with raw
artifacts under
`.agentsight/experiments/r315-llm-reader-rq2-v2/preflight/`.

**Decision and next action.** REAL PREFLIGHT passes on attempt 1. Execute the
complete 66-presentation collection before loading the hidden key or
interpreting any response.

### Node E003 — FULL RUN, Scoring, And RESULT REVIEW

**Question and execution.** The approved full command ran every planned
presentation through the same local Qwen3.6-27B endpoint. Collection completed
66/66 presentations over all 18 packets and six tasks in 517.65 seconds. All
responses succeeded on the first API attempt; none was dropped, imputed,
manually repaired, or reused from preflight. Only after collection completed
did the separate score command load the hidden R315 key and existing R316
control. Commands, counts, checks, task rows, and direct raw paths are recorded
in [`experiment-001/full-run.md`](experiment-001/full-run.md).

**Mechanical and independent checks.** The root found 66 unique success rows,
zero schema or alias-budget failures, zero original-ID or forbidden-key leaks,
and exact position balance: every group occupies every alias position once.
Six of twelve non-flat packets change their selected original-group set across
rotations, confirming that balancing was material. An independent shell
recalculation reproduced the emitted medians and win counts. The fresh result
reviewer then independently joined every response to the hidden key and
recomputed every presentation and task/view aggregate with maximum absolute
metric difference zero. Its complete audit is
[`experiment-001/result-review.md`](experiment-001/result-review.md).

**Result.** After averaging rotations within task/view, operation stack minus
fixed session has median selected-positive recall delta `+0.080571`, improving
5/6 tasks, and median precision delta `+0.035501`, improving 4/6. Both
predeclared primary conditions pass, so the tested hypothesis is
`VALID / SUPPORTED`. Work delta has median `+0.006302` and is higher on 4/6
tasks, including two large increases.

**Scientific impact and scope.** The independent reviewer overrides the
runner's generated `decisive` label and assigns **supporting** research value:
this is a non-redundant downstream decision over one reader and query-aware
top-five packets, but it is not a human study, an end-to-end raw-action
comparison, or a whole-RQ answer. Fixed session is fair for the bounded packet-
view comparison; the result cannot authorize lower inspection work, reader-
only causality, remediation, human productivity, cross-model generality, or
universal view dominance. No rerun or cosmetic prompt/model/cutoff variation is
admitted. The valid result returns to targeted WRITE.

### EXPERIMENT Gate Transition

The handoff passes independent orchestration review: the selected RQ is
verbatim, paper-value admission and two-round-bounded plan review completed,
REAL PREFLIGHT contacted the real system, all planned cells reached terminal
status, raw paths are linked, and RESULT REVIEW separately judged run validity,
hypothesis, research value, paper impact, and next decision. The fixed thesis,
two abstractions, four RQs, and positive RQ2 hypothesis are unchanged.

## WRITE Gate

### Entry And Phase-Permission Audit

At WRITE entry the root reread `docs/user-instruction.md`, the fixed contract,
the complete result review, and the current RQ2 paper subsection. Under
BUILD_AND_EVALUATE policy, this gate may update only the experiment protocol,
result table, local interpretation, supporting citation, and canonical evidence
frontier. Title, abstract, introduction, motivation, contributions, section
structure, related-work story, and conclusion remain unchanged.

### Node W001 — Targeted RQ2 Evidence Update

`docs/paper/main.tex` now identifies the fixed Qwen3.6-27B reader, query-aware
top-five candidate boundary, hidden rank/view/IDs, five cyclic positions,
post-collection label scoring, and 66-response matrix. A full-width compact
table exposes all six paired recall, precision, and work deltas plus their
medians. The local conclusion reports the registered 5/6 recall and 4/6
precision improvements while explicitly stating that work rises on 4/6 and
forbidding lower-work, reader-only, human-utility, or universal-dominance
promotion. The official Qwen model card is added as the exact model source.
No negative development attempt enters the reader-facing paper.

`docs/evaluation.md`, `docs/background-related-work.md`, `docs/implementation.md`,
and the current evidence frontier in `docs/idea-story.md` now record the valid
supporting result, raw paths, experiment boundary, adapter role, and no-repeat
condition. No narrative-evolution entry was added because no scientific
contract or story element changed. `docs/design.md` required no update because
the experiment changed no profiler mechanism.

### Node W002 — Paper And AAAI-27 Verification

The paper rebuilds with `make` and no undefined citation, LaTeX/package error,
or overfull box. Direct page rendering confirms that the six-task table is
legible and untruncated. `pdfinfo` reports nine US-Letter pages; Conclusion and
the first reference both end/start on page 7, and pages 8--9 contain references
only. `pdffonts` reports embedded Type 1 or TrueType fonts, and page 1 says
`Anonymous submission` with no affiliation. This matches the official
[AAAI-27 Main Track call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/)
limit of seven main-content pages and nine total pages and the
[submission instructions](https://aaai.org/conference/aaai/aaai-27/submission-instructions/)
for double-blind, US-Letter, official-style PDFs. The official deadlines remain
July 21, 2026 for the abstract, July 28 for the full paper, and July 31 for
supplementary material and code.

### Node W003 — Outer-Audit-Directed Local Repair

The first REVIEW pass returned two bounded repairs rather than an experiment
rerun. First, the paper sentence `Together these workloads answer RQ2
positively` exceeded the Step 0019 result review's classification of this run
as additional, not stand-alone whole-RQ, evidence. The root accepts the
claim-tone finding without weakening the positive RQ2 hypothesis: the sentence
now says that the complete workloads provide positive RQ2 evidence, followed
immediately by the registered recall/precision gains and higher-work boundary.
The thesis, RQ, contribution, result rows, and positive direction are unchanged.

Second, the score adapter mechanically assigned `research_value=decisive` when
the metric verdict passed. The root accepts that research value is a review
judgment rather than a metric. The adapter now emits `pending independent
review`; the same completed 66 responses were rescored without any model call,
and all task rows, medians, win counts, and the `SUPPORTED` metric verdict are
unchanged. The independent result review remains authoritative at
`supporting / additional RQ evidence`.

### WRITE Gate Transition

WRITE completes, re-enters once for the two outer-audit-directed local repairs,
and then completes again with the original ambitious position intact and one
additional reviewed RQ2 result. Every fixed RQ remains explicit and Evaluation
remains organized RQ1--RQ4. Advance to REVIEW for the
scientific-contract-unchanged audit, repair verification, meta-review, and next
highest-value routing.

## REVIEW Gate

### Entry And Scientific-Contract-Unchanged Audit

At REVIEW entry the root reread `docs/user-instruction.md`, confirmed there are
no open questions in `docs/questions-for-author.md`, compared the current diff
with the fixed contract and read-only submodule, and supplied the complete step
and raw links to a fresh reviewer with no execution role. The exact thesis,
four RQs, two core abstractions, evaluation promise, title, abstract,
introduction, motivation, contributions, section structure, related-work story,
and conclusion remain unchanged. No idea skill or root idea disposition ran.

### Node R001 — Independent Outer Audit And Repairs

The independent audit is
[`outer-audit-20260714T174516-0700.md`](outer-audit-20260714T174516-0700.md).
It independently checked the 66 response rows, aliases and request fields,
hidden-key separation, every emitted metric, fixed-session fairness, task-level
aggregation, paper diff, current PDF, official AAAI rules, and submodule state.
It returns `REPAIR`, while affirming that the run is valid, the registered
hypothesis is supported, the evidence is useful and supporting, and no model
rerun is required.

The root accepts the two must-fix findings and completed them in W003. Direct
inspection of the regenerated summary confirms `research_value=pending
independent review`; direct diff inspection confirms that the paper now says
`provide positive RQ2 evidence` rather than promoting this run to a stand-alone
whole-RQ authorization. The complete paper rebuild and format checks are rerun
after those repairs before step closure.

The root accepts the raw-persistence observation as a later supplement task,
not as a scientific blocker or an invitation to add integrity machinery. The
ignored local raw directory remains present and linked; the tracked adapter,
plan, exact commands, model/config description, and reviewed results are in the
step. The eventual AAAI code/data supplement must package the 66 responses and
score rows. The historical unregistered `tau-bench` gitlink is pre-existing and
unrelated; it is not repaired in this research step. No `AGENTS.md`, repo-local
skill, shared skill, or submodule change is warranted.

### Meta-Review And Route

- **Direction:** PASS after W003. The experiment tests a real downstream
  decision inside fixed RQ2 and preserves the ambitious thesis without a new
  concept or smaller story.
- **Efficiency:** PASS. It reuses all existing packets and labels, completes
  the entire matrix in one run, and closes this packet branch. Prompt, seed,
  model, cutoff, and reader repetitions are prohibited unless materially new
  evidence changes the decision.
- **Maintenance:** PASS after the adapter ownership fix. The absent
  `scripts/check_progress.py` remains a diagnostic repository fact, not a gate
  failure and not a reason to create control infrastructure in this step.

RQ1 and RQ4 have evidence-backed paper-level answers. Step 0019 strengthens and
closes the selected RQ2 packet branch. The highest-value remaining frozen
evaluation gap is RQ3's explicit phase/action or literal-tag component. The
next step enters EXPERIMENT on fixed RQ3 and selects one real independently
annotated public family and one pre-specified target-blind fidelity hypothesis;
it must reuse official data/protocols, avoid another OSWorld-Human tuning pass,
and must not bundle every remaining RQ3 component into one experiment.

### REVIEW Gate Transition

REVIEW passes after the two local repairs. Step 0019 is complete and proceeds
to its single Git persistence boundary, then Step 0020 begins at EXPERIMENT on
fixed RQ3. Push success or failure does not affect the scientific transition.

## Ranked Open Objections

1. RQ3 still lacks complete phase/action/literal-name validation. The next step
   tests one decisive missing component without changing RQ3.
2. Before submission WRITING, the abstract/introduction must make unmistakable
   that the 0.739/0.816 headline boundary result is from the optional supervised
   backend rather than the built-in Rust inducer.
3. Submission WRITING must add the verified closest production/research
   profiler positioning, including NeMo, AWS, AgentGraph, AgentDiagnose, and
   adjacent cross-trace systems, without changing the original thesis.
4. The eventual AAAI supplement must package the local ignored Step 0019 raw
   responses and score rows plus the fixed inputs and exact model/config; this
   is publication work, not an experiment gate or current evidence defect.
