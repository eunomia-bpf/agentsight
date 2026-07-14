# Step 0017 Report — Principle-Driven Rust Operation-Stack Induction

## Metadata And Current State

- Started: 2026-07-14T12:10:12-07:00
- Recovered for outer completion: 2026-07-14T15:24:33-07:00
- Phase: BUILD_AND_EVALUATE
- Gates: EXPERIMENT, targeted WRITE, REVIEW
- Parent: Step 0016 AAAI milestone full-paper review
- Completed: 2026-07-14T15:58:21-07:00
- Status: complete after independent outer audit and minimal repair
- Active branch: `research/semantic-flamegraph-artifacts-v2`
- Read-only story source: `docs/agentpprof-paper` at
  `7f80c433c9555317a2aa45a78d0ff93518f4c12c`

The paper's central position in plain language remains that developers need a
population-level way to attribute accumulated agent activity and effects, not
only tools for inspecting one failed execution. The exact thesis remains
**Agent observability needs profiling, not only debugging.** The two core
objects remain operations and operation stacks. The four fixed RQs remain
resource attribution, problem correspondence, tag accuracy, and profiling
cost.

## Recovery And Gate-Entry Audit

At recovery, the root read all of `docs/user-instruction.md`,
`docs/questions-for-author.md`, and `docs/idea-story.md`, then checked the
current paper, canonical evaluation/design/implementation files, experiment
reports, raw results, source, tests, Git state, and the untouched submodule.
There are no open author questions. The newest user objective and the request
to record the information-gain algorithm are preserved verbatim in
`docs/user-instruction.md`.

The worktree entered recovery with the complete Step 0017 algorithm and full
run already committed, but without a step report, targeted WRITE record, or
outer audit. The raw complete run exists under
`.agentsight/experiments/rq3-rust-inducer-fidelity-v1/full/`. The submodule was
and remains clean. The active branch was 74 commits ahead of its remote because
ordinary pushes encounter an existing large-object HTTP 500 backlog; no branch
was created or switched and no history was rewritten.

Two persistence deviations predate this report. Commit `fe0704f9` persisted the
algorithm, runner, tests, and experiment reports before the outer step closed;
commit `0d0a0cab` later persisted the user-requested algorithm note and
canonical mechanism description. The current orchestrator rule expects one
commit after the completed step. This report records the deviation rather than
rewriting published local history; the final closure will be one additional
coherent commit containing only the missing WRITE/REVIEW state.

## EXPERIMENT Gate

### Entry And Selection

Step 0016 had routed to an RQ2 fixed-reader experiment over 18 reused R315
packets. That proposal entered because it could test whether a fixed LLM reader
uses profile organization to make a better bounded prioritization decision.
The proposal and two plan-review rounds are preserved under
`01-experiment-gate/loop-001-rq2-r315-llm-reader/`.

Before preflight or any model call, the user redirected the step to the proposed
information-gain operation-stack induction algorithm and required it to be
recorded, implemented, and tested. The RQ2 proposal was therefore paused, not
executed, and contributes no scientific evidence. The redirect is recorded in
`01-experiment-gate/010-gate-redirect-20260714T152433-0700.md`.

The replacement experiment remained inside the fixed RQ3, **How accurate are
the tags?** Its specific tested hypothesis was that replacing the shipped
multi-term Rust heuristic with one resource-weighted normalized
information-gain objective would beat both the old binary and the strongest
simple controls on independently annotated human boundaries and partitions.
This experiment had higher immediate paper value than executing the paused RQ2
reader because the current paper described a shipped stack inducer while its
positive RQ3 numbers belonged to a separate supervised predictor.

### Node RQ3-RUST-INDUCER — Plan And Review

The complete Markdown plan is
[`experiment-plan.md`](01-experiment-gate/loop-002-rq3-rust-inducer-fidelity/experiment-plan.md).
It reuses the complete OSWorld-Human operation conversion, all 287 eligible
sessions, 3,978 operations, 3,691 adjacent pairs, 2,042 official human groups,
the existing boundary and operation-weighted B-cubed metrics, the frozen
pre-change Rust binary, and the existing action-change, phase-change, and
always-boundary controls. Official human-group fields are scorer-only.

The candidate was fixed before scored execution:

- candidate cuts occur only at adjacent changes in eligible visible fields;
- each informative field receives resource-weighted normalized categorical
  information gain;
- the cut score is the equal mean across informative fields;
- a cut is accepted only when its score is strictly greater than
  `ln(n)/(2n)`;
- the old score threshold, child-size, majority, balance, coverage,
  label-quality, semantic-shift, and candidate-subsampling terms and gates are
  removed;
- the dominant values of the most informative separating field produce
  `field=value` child frames;
- query relevance affects exact ties only;
- all operations receive one terminal path and all additive weight must be
  conserved; and
- the matched candidate and old binary both use the existing maximum depth of
  four.

The historical loop received three serial reviews under the experiment skill
version active when it began. The combined review record is
[`plan-review.md`](01-experiment-gate/loop-002-rq3-rust-inducer-fidelity/plan-review.md).
The final review approved the fixed formula, replay semantics, target-blind
field boundary, complete population, commands, and interpretation. No reviewer
changed the RQ, thesis, paper story, workload, or metrics.

### Real Preflight, Invalid Attempt, And Repair

The first real preflight/full path exposed a residual legacy
`redundant_segment_label` rejection gate. It triggered 16 times, so that run
did not implement the approved single-objective candidate and was preserved as
invalid in `real-preflight.md`, `full-run.md`, and the corresponding raw
`*-invalid-legacy-redundancy-gate` directories.

The gate was removed without changing the approved objective, fields, scorer,
population, baseline, or metrics. The corrected real preflight then ran both
actual release binaries on one real eligible 11-operation session. It consumed
every split decision, reconstructed all terminal paths, matched Rust profile
weights, conserved all 11 units, excluded oracle fields, and observed only the
declared `max_depth` and `no_material_split` stops. See
[`real-preflight-corrected.md`](01-experiment-gate/loop-002-rq3-rust-inducer-fidelity/real-preflight-corrected.md).

### Complete Run And Raw Evidence

The corrected full command completed every planned cell: 287 candidate runs
and 287 frozen-baseline runs. The authoritative report is
[`full-run-corrected.md`](01-experiment-gate/loop-002-rq3-rust-inducer-fidelity/full-run-corrected.md),
with raw summaries and per-session/per-pair rows under
`.agentsight/experiments/rq3-rust-inducer-fidelity-v1/full/`.

All validity checks passed: complete population, exact one-time terminal
assignment, exact mass conservation per session, complete decision replay,
reconstructed Rust stack-weight equality, oracle exclusion, strict
gain-versus-penalty acceptance, depth-four configuration, and normalized child
frame distinction.

| Method | Boundary F1 | B-cubed F1 |
|---|---:|---:|
| Revised information-gain Rust inducer | 0.4231 | 0.6165 |
| Frozen pre-change Rust heuristic | 0.0843 | 0.4653 |
| Action-change control | 0.4771 | 0.6592 |
| Phase-change control | 0.3337 | 0.6655 |
| Always-boundary control | 0.6445 | 0.6784 |
| Supervised out-of-fold comparator | 0.7388 | 0.8160 |

The revision improves the shipped mechanism by +0.3388 boundary F1 and +0.1511
B-cubed F1 and reduces no-split sessions from 204 to 4. It nevertheless fails
the registered requirement to beat the strongest simple controls on both
metrics. The fixed candidate hypothesis is therefore contradicted. This is a
mechanism boundary and supporting RQ3 evidence, not a conclusion about all of
RQ3 and not a direct thesis challenge.

### Independent Result And Code Reviews

The fresh result reviewer independently recomputed the corrected raw outputs,
matched all counts and metrics, and returned `VALID / CONTRADICTED /
SUPPORTING / mechanism boundary`. The review is
[`result-review.md`](01-experiment-gate/loop-002-rq3-rust-inducer-fidelity/result-review.md).

The independent code review checked the Rust implementation, CLI, direct replay
consumers, scorer, tests, and raw invariants. It found and resolved three issues:
the residual legacy gate above, stale repeated-frame replay consumers, and a
possible collision between distinct raw values after folded-frame
normalization. The final review reports PASS with no actionable issue in
[`code-review.md`](01-experiment-gate/loop-002-rq3-rust-inducer-fidelity/code-review.md).
At WRITE verification, `cargo fmt --check` and all 49 Rust tests pass again.

### Experiment Impact, Tree Update, And Transition

The old heuristic branch is superseded for implementation quality. The fixed
depth-four information-gain candidate remains a completed contradicted branch,
not positive paper evidence. Post-run diagnostics expose one materially binding
arbitrary mechanism constraint: 106/287 sessions hit the depth-four cap, 488
terminal nodes stop there, and long sessions remain under-segmented. Binary
depth four can express at most 16 leaves, while 22 official sessions contain
more than 16 human groups.

The highest-value next branch changes only the hard depth cap so the registered
gain-versus-penalty rule becomes the actual stop. Fields, objective, penalty,
ties, child labels, population, metrics, scorer, old binary, and controls stay
fixed. Because this direction was selected after inspecting OSWorld-Human, it
is explicitly post-hoc. It may test whether the cap caused the observed
under-segmentation; it cannot serve as fresh independent confirmation. A
positive result would next require one independent annotated workload rather
than another OSWorld constant search.

EXPERIMENT exits to targeted WRITE because the valid result has a clear
mechanism and paper disposition.

## WRITE Gate

### Entry And Permission Boundary

WRITE reread current user intent and the BUILD_AND_EVALUATE phase policy. It
was permitted to update implementation/method facts and canonical experiment
state only. It was not permitted to change the title, abstract, introduction,
motivation, thesis, insight, design goals, contributions, section structure,
related work, conclusion, four RQs, or the submodule story.

No full writing skill ran. No intermediate negative result entered the
reader-facing paper. The paper's positive 0.739/0.816 RQ3 result remains
correctly attributed to the supervised out-of-fold predictor, not the Rust
inducer.

### Targeted Canonical And Paper Update

The user-requested algorithm record is
[`algorithm-note.md`](01-experiment-gate/loop-002-rq3-rust-inducer-fidelity/algorithm-note.md).
It records the principle, formula, field admission, deterministic frame
construction, invariants, established information-gain/binary-segmentation
precedent, current empirical boundary, and next single-variable test without
introducing a new branded mechanism.

`docs/design.md`, `docs/implementation.md`, and `docs/evaluation.md` now reflect
the current algorithm, exact complete result, evidence scope, and next
mechanism branch. After the outer audit, `docs/idea-story.md` received an
evidence-frontier refresh recording the contradicted fixed-depth mechanism and
post-hoc cap-only route; no narrative-evolution entry was added because no
problem, thesis, contribution, scope, system direction, RQ, or paper story
changed. `docs/background-related-work.md` was intentionally unchanged because
this step produced no new literature claim or source family.

The sole scientific-body edit in `docs/paper/main.tex` replaces the stale
Jaccard/multi-term Implementation paragraph with a compact factual description
of the current resource-weighted normalized information-gain inducer. A stale
unsupported claim that rule refinement typically takes 5--10 rounds was also
replaced by the implemented observation that users inspect unmatched
operations. Abstract, Introduction, Background and Motivation, Design,
Evaluation results, Related Work, Conclusion, and all four RQs were left
unchanged. `docs/paper/README.md` now records the verified current deadline,
page, anonymity, font, and separate-checklist requirements; it changes no paper
claim.

### Full Paper Verification

A forced clean-equivalent AAAI build completes with no undefined citation,
undefined reference, LaTeX warning, overfull box, or error. The PDF is nine
letter-size pages; all main content, including the complete Conclusion, ends on
page seven and References begins on page eight. The local wrapper uses
`aaai2027.sty` in anonymous submission mode. The rendered page limit was
rechecked after shortening the Implementation wording; an earlier draft had
spilled one Conclusion line onto page eight and was not accepted.

The root also rechecked the current official
[AAAI-27 Main Technical Track CFP](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/)
and [submission instructions](https://aaai.org/conference/aaai/aaai-27/submission-instructions/)
on 2026-07-14. They require at most seven pages of main content and nine pages
total, reserve every page after seven exclusively for references, require an
anonymous US-letter high-resolution PDF with embedded Type 1 or TrueType fonts,
and require a separately uploaded reproducibility checklist. The current PDF
is anonymous, letter size, uses embedded Type 1/TrueType fonts, and meets the
7+2 page boundary. The repository's `ReproducibilityChecklist.tex` remains the
unfilled official template and is a later submission task, not an experiment
gate. Official deadlines are 2026-07-21 for the abstract, 2026-07-28 for the
paper, and 2026-07-31 for supplement/code, all 23:59 UTC-12.

The exact thesis sentence appears in the Abstract/Introduction/Conclusion
chain, Evaluation still contains the four fixed explicit RQs, and every RQ has
an evidence-backed current answer or scoped positive partial answer. No Step
0017 negative number entered the paper. `docs/agentpprof-paper` remains clean
and unchanged.

WRITE exits to REVIEW.

## REVIEW Gate

### Scientific-Contract-Unchanged Audit

This BUILD_AND_EVALUATE step changed an implementation algorithm and gathered
one complete mechanism result. It did not invoke idea refinement or accept a
new problem, thesis, claim, contribution, scope, design goal, paper structure,
or RQ. The exact thesis, two-object model, submodule-derived narrative, positive
four-RQ program, and user prohibition on story shrinkage remain intact.

The tested candidate's contradiction cannot authorize a smaller thesis or RQ.
It redirects only the algorithm-detail search. Conversely, the large
old-to-new improvement cannot be presented as accurate human-group recovery
because the strongest simple controls still win. The selected cap-only test is
the strongest simple next mechanism experiment supported by the diagnostics;
it avoids both story shrinkage and indefinite heuristic search.

### Ranked Open Objections Before Outer Audit

1. The built-in target-blind inducer still lacks a positive accuracy result
   against the strongest simple controls; this is the next experiment's direct
   question.
2. The selected cap-only experiment is post-hoc on OSWorld-Human; a positive
   result still needs independent annotated confirmation before a broad
   paper-level constructor claim.
3. The paper's current positive RQ3 result validates a supervised predictor and
   task partitions, not the built-in inducer. The paper states this correctly,
   but reviewers may still view the shipped-mechanism/evidence split as a major
   weakness until the next branch succeeds.
4. Step 0016's whole-paper review judged the current paper weak reject rather
   than submission-ready. A new milestone review must reassess this only after
   the next mechanism result and permitted paper update; repeated review of an
   unchanged paper would add no evidence.
5. The official AAAI-27 reproducibility checklist is still blank. It should be
   completed from the final paper and artifact after the open experiment, not
   guessed while the method and evidence frontier are still changing.

### Outer Audit And Routing

A fresh reviewer with no execution role independently checked the raw outputs,
source, diff, paper, canonical memory, and current official AAAI-27 rules. The
auditor returned `REPAIR` with `Direction — PASS`; the full report is
[`outer-audit-20260714T155821-0700.md`](outer-audit-20260714T155821-0700.md).
It independently reproduced the population, mass, confusion counts, metrics,
stop counts, strongest-control comparison, paper-edit boundary, story/RQ
fidelity, and 7+2 AAAI format. It required no rerun, algorithm change,
paper-story change, or Git-history rewrite.

The required repair is complete: `docs/idea-story.md` now records the current
Step 0017 evidence frontier and the explicitly post-hoc cap-only route without
creating a narrative-evolution entry. The audit also recommended archiving
detail from the canonical design and evaluation files based on their length.
The root does not treat line count alone as a correctness defect and declines
an unrelated high-churn reorganization during this algorithm step: the current
sections are accurate, auditable, and already link their dedicated reports.
Future compaction is appropriate only when a concrete stale statement or exact
duplication can be removed without losing canonical context.

Step 0017 closes and routes to a new BUILD_AND_EVALUATE step entering EXPERIMENT
on fixed RQ3. Completion requires one approved cap-only plan, one real
preflight, the complete 287-session run, and one independent result review.

## Canonical Memory, Capability Learning, And Persistence

- Updated: `docs/user-instruction.md`, `docs/idea-story.md`,
  `docs/evaluation.md`, `docs/design.md`, `docs/implementation.md`,
  `docs/paper/README.md`, and the Implementation paragraph in
  `docs/paper/main.tex`.
- Unchanged by design: `docs/background-related-work.md`,
  `docs/questions-for-author.md`, project `AGENTS.md`, all shared skills, and
  `docs/agentpprof-paper`.
- No new repository rule or skill is warranted. The only invalid run arose
  from a one-off residual legacy gate and was already caught by the existing
  plan/code/result review path. The cap-only follow-up is a transient research
  branch, not a reusable workflow.
- Git is operational only. No branch was created or switched. The ordinary
  push backlog remains non-blocking and no force push or history rewrite is
  authorized.

The independent audit disposition and root response are recorded above. The
resulting closure commit and best-effort push outcome are reported to the user
rather than amended back into this report.
