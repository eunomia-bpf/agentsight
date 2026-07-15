# Step 0029 Independent Outer Audit And Meta-Review

**Audited:** 2026-07-15T15:56:44-07:00
**Phase:** BUILD_AND_EVALUATE
**Scope:** Step 0029 EXPERIMENT, WRITE, and REVIEW handoff; raw-result validity;
candidate restoration; frozen story and RQ fidelity; paper-decision value;
efficiency, maintenance, capability learning, and next routing
**Skill used:** `auto-research-orchestrator`
**Experiment verdict:** **PASS — VALID / COMPLETE / CONTRADICTED**
**Outer-step record verdict:** **REVISE before closure**
**Paper change authorized:** none
**Another automatic algorithm experiment authorized:** **no**

Step 0029 resolves its registered question cleanly: the one multi-session
grammar constructor is worse than Step 0024 on both complete populations, the
candidate has been removed exactly, and the paper's scientific contract is
unchanged. The result is valid internal mechanism evidence, not a whole-RQ3
answer and not a reason to shrink or rewrite the AgentProf story.

The experiment does **not** create an obligation to rescue grammar induction or
to invent another operation-group constructor. The next research action must be
selected afresh by paper-level decision value against the remaining evaluation
promise. At present, direct phase/action/literal-tag accuracy is a more obvious
unfilled part of RQ3 than another constructor comparison; the bounded RQ2
decision-consequence gap is the next competing paper-level branch. This audit
does not preselect an implementation, benchmark, or algorithm for either one.

The outer step is not ready to close only because its own report still contains
stale status fields and an incomplete REVIEW handoff. These are Markdown
provenance defects, not experimental defects, and they must not reopen Step
0029 or trigger another run.

## Independence And Disclosure

I held no plan-authoring, implementation, evaluator-repair, experiment-
execution, result-review, restoration, writing, or Git role in Step 0029. The
only file written by this audit is this report. I did not edit the paper,
product, tests, scripts, skills, canonical documents, step report, branch, or
read-only paper submodule, and I performed no Git action.

This was not a blind review. The assignment and current step report exposed the
prior plan, implementation, result, and restoration verdicts, including the
expected Step 0024 disposition. I therefore treated every prior reviewer
finding as evidence rather than task authority and checked it against the raw
roots, current source tree, current paper, canonical frontier, and executable
test state.

I completely read `auto-research-orchestrator/SKILL.md` and its complete
`references/hierarchical-research-state-machine.md`. Project inputs included:

- the complete verbatim `docs/user-instruction.md` and current
  `docs/questions-for-author.md`;
- the complete `docs/idea-story.md` and `docs/evaluation.md`;
- every Step 0029 plan, plan-review, implementation-review, preflight, result,
  result-review, and step-report file;
- the current paper's thesis and four RQ headings;
- the three Step 0029 full-result roots and retained Step 0024 result roots;
- current product/test source, removed candidate-script paths, branch, HEAD,
  worktree diff, and submodule pointer; and
- a fresh restored-product test and Clippy run.

The orchestrator reference names `scripts/check_progress.py` as diagnostic
meta-review input. Neither that path nor a singular `script/check_progress.py`
exists in this worktree, so no such output was available. The reference makes
the diagnostic non-gating. Its absence is recorded under Maintenance and does
not invalidate this result or transition.

## User Intent, Scientific Contract, And Direction

The active instructions require the exact thesis, the original submodule
story, exactly four RQs, a large and attractive positive paper, real complete
experiments, reuse of already-run trajectories where possible, no narrowing in
response to a local failure, no current-skill changes, no submodule edits, and
no waiting for human judgment. The latest experiment instruction specifically
asked whether the existing algorithm could be improved on already-run traces
rather than by collecting another dataset.

Step 0029 stayed inside that request. It selected verbatim:

> **RQ3: How accurate are the tags?**

It tested one supporting operation-group constructor on complete existing
OSWorld-Human and CodeTraceBench populations. It did not rename, split, narrow,
or claim to answer all of RQ3. It used one published principle, ordinary terms,
and no new paper abstraction or branded mechanism. The exact paper position
remains:

> **Agent observability needs profiling, not only debugging.**

The current paper still contains that sentence and its four headings remain
resource attribution, problem correspondence, tag accuracy, and profiling
cost. `docs/paper/` has no worktree diff. `docs/agentpprof-paper` remains at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`, with no pointer or content diff.
No Step 0029 grammar result or terminology appears in the paper. No idea-level
change occurred, so leaving `docs/idea-story.md` unchanged is correct.

**Direction conclusion: PASS.** Step 0029 preserved the ambitious original
problem and treated a local mechanism failure as a local mechanism boundary.
It neither converted a negative result into the paper's story nor used it to
weaken the fixed positive RQ3 hypothesis.

## EXPERIMENT Gate Audit

### Paper-value admission and source grounding

The experiment was admissible as one bounded response to the user's direct
algorithm-improvement request. It compared a materially different variable-
length sequence constructor against the strongest retained same-information
Step 0024 baseline, reused real complete public-data populations, registered
different product decisions for positive and negative outcomes, and prohibited
a second grammar candidate. It was not a hidden third Step 0028 cutoff attempt
or another Step 0025 local-score/window rule.

The source grounding was adequate for a bounded attempt but weak as a forecast
of success. The screen established that long action sequences recur across
sessions and cited the original Re-Pair principle. It did **not** establish
that compression units should correspond to human/source-authored operation
partitions. Indeed, the plan's strongest competing explanation said that a
coarse action vocabulary could alias whole motifs. The final over-merging result
realized that explanation. Therefore this was a legitimate high-risk test under
the direct user request, not positive evidence that recurring motifs were the
most likely route to a paper-level RQ3 answer.

That distinction matters for routing: recurrence existence was enough to run
this one decisive test, but it is not a renewable admission token for another
constructor after the registered contradiction.

### Plan and implementation review

The two-round plan review repaired three material defects before code:
algorithm identity and total ordering, an executable product/evaluator path,
and honest separation of execution-time label isolation from adaptive method-
family selection. The two-round implementation review then found three real
validity defects: labels loaded before OSWorld prediction, incomplete and
under-bound baseline/control rows, and partial report/equivalence coverage.
The focused repairs did not change the algorithm or add a candidate.

These reviews were not merely objection-count reduction. Without the first
implementation repair, a later claim of prediction-before-oracle isolation
would have been false; without baseline binding and complete comparator rows,
the main product relation would have been ambiguous. Their scientific value is
the trusted final result, not the number of checks or review rounds.

The process was nevertheless expensive relative to the paper decision. The
Step 0029 Markdown child files plus step report exceed three thousand lines,
and three custom evaluators were built for one deterministic candidate whose
full runs completed in minutes. Future work should reuse established loaders,
scorers, and result paths directly and keep only checks capable of changing
validity or the paper decision. Step 0029 correctly removed its transient
candidate evaluators instead of turning them into permanent audit
infrastructure.

### Real preflight, full execution, and raw evidence

Both registered real preflights passed on their first attempt. FULL then
completed every planned target:

- OSWorld-Human: five folds, 287 target sessions, 3,978 operations, 3,691
  adjacent decisions, and 2,042 official groups;
- CodeTraceBench: 2,229 target-disjoint reference sessions with 87,703
  operations, 405 target sessions with 20,866 operations, 20,461 adjacent
  decisions, and 2,948 official stages across four frameworks; and
- independent product/evaluator agreement for every rule, target segment,
  operation assignment, and additive unit.

The raw roots and independent review support the reported primary relations:

| Population | Grammar candidate B-cubed F1 | Step 0024 B-cubed F1 | Delta |
|---|---:|---:|---:|
| OSWorld-Human | 0.717803 | 0.786170 | -0.068367 |
| CodeTraceBench | 0.633931 | 0.649173 | -0.015242 |

The candidate produced 1,492 rather than 2,656 OSWorld groups and 5,187 rather
than 6,897 CodeTrace groups. Its higher OSWorld recall did not offset its
precision loss; its single Terminus2 framework win did not override the lower
complete-population result. Under the predeclared relation, the only correct
verdict is **VALID / COMPLETE / CONTRADICTED**.

The result reviewer independently reconstructed both populations, all retained
baseline/control rows, every grammar rule and tie choice, every target
application, all assignments, mass, and prediction-before-oracle timing. The
three full summary roots exist and are internally consistent. This audit also
found no missing planned population or partial-prefix interpretation.

### Candidate restoration

The predeclared negative disposition is complete and exact:

- `agentpprof/src/main.rs`, `agentpprof/src/profile.rs`, and
  `agentpprof/tests/profile_spec_cli.rs` have no diff against Step 0029 entry
  `HEAD`;
- all three Step 0029 grammar evaluator scripts are absent;
- a fresh restored-product run passes 42 unit tests, 8 profile CLI tests, and 3
  standard-trace CLI tests;
- `cargo clippy --all-targets -- -D warnings` passes; and
- current tracked work is limited to the Step 0029 Markdown record and the
  intended `docs/evaluation.md` frontier update.

The restoration removed no unrelated user work and retained every raw and
Markdown result. Step 0024 remains the current constructor because of its prior
positive evidence, not because Step 0029 was hidden or relabeled.

## WRITE Gate Audit

The no-paper-change disposition is scientifically and phase correct. A removed
contradicted development candidate supplies no new positive paper value and
does not bound the current Step 0024 claim. The paper, figures, thesis, four RQ
meanings, abstract, introduction, motivation, design, contributions, and
conclusion therefore remain untouched. `docs/evaluation.md` correctly keeps
the complete internal mechanism result and states that it does not enter the
reader-facing paper.

No writing or idea skill was needed. Invoking one would have risked expression
churn without a scientific disposition to apply.

The step report must still make the WRITE gate auditable by adding its entry
time and parent, naming the required reread of `docs/user-instruction.md` and
`docs/questions-for-author.md`, and recording the full-paper verification
facts above. This is a report repair only; it authorizes no paper edit.

## Meta-Review

### Direction

**PASS.** The step solved the intended bounded question, preserved the frozen
scientific contract, used real complete evidence, and retained the simple
operation/operation-stack center. The contradiction closes this constructor;
it does not challenge the thesis or fixed RQ3 hypothesis.

### Efficiency

The step produced one real product decision: keep Step 0024 and retire this
multi-session grammar constructor on both retained development populations. It
also supplied a useful mechanism diagnosis—compression of recurring action
motifs over-merges the official operation partitions. That is narrower than a
paper result but more than dependency-only activity.

The expensive part was not strict outcome interpretation. The fixed two-
population rule is simple and appropriate for replacing the current release
constructor. The expensive part was admitting and qualifying a candidate whose
source screen showed recurrence but supplied no positive reason that
compression units matched the target operation semantics. The plan made this
risk explicit, and the user's direct request justified one attempt. Repeating
the same pattern automatically would become low-value constructor churn.

Accordingly:

- do not relax the valid/complete/contradicted verdict;
- do not retry with a support threshold, grammar cap, different pair order,
  alternative compression grammar, or target-informed anti-overmerge rule;
- do not demand another algorithm merely because the candidate failed; and
- select the next node by the paper's unfilled evaluation promise, not by sunk
  implementation effort or a desire to make Step 0029 positive.

### Maintenance And Capability Learning

The Step 0029 update to `docs/evaluation.md` is accurate and sufficient for the
current mechanism frontier. No update to `docs/design.md` or
`docs/implementation.md` is justified because the candidate product was
removed. No idea-story entry is justified because no scientific narrative
changed. No paper or submodule maintenance is justified.

Two canonical files are substantially above the orchestrator's soft one-to-two
hundred-line frontier budget: `docs/idea-story.md` is 576 lines and
`docs/evaluation.md` is 726 lines. The complete Initial Narrative and compact
idea-change index must remain in `docs/idea-story.md`, but repeated Step 0020--
0029 mechanism detail in the current-frontier prose can be shortened to links
to the existing step reports during a later housekeeping action.
`docs/evaluation.md` likewise describes itself as a frontier but carries long
experiment history. This is a readability/maintenance issue, not a condition
for accepting Step 0029, and cleanup must preserve every linked history record.

The missing `scripts/check_progress.py` is a capability mismatch with the
orchestrator reference. It did not block this audit and should not be invented
inside this step. If unattended monitoring remains desired, the root can later
decide whether the repository needs the diagnostic using the normal
capability-learning ladder.

The repeated constructor attempts in Steps 0020--0029 are evidence of a
project-level routing risk: method novelty or a different mechanism family can
be mistaken for paper-level value after the current product is already good
enough for the paper's bounded claim. The smallest current owner is the
paper-value admission and outer routing decision, not writing, result review,
or a new AgentProf product skill. If this trajectory is considered for shared-
skill evolution, the candidate owner is `research-experiment-design`'s
PAPER-VALUE ADMISSION and the orchestrator's experiment-selection wording—not
the strict scientific verdict or writing skills. Because these attempts belong
to one parent research trajectory rather than independent projects, this audit
supports an `observe`/`propose` record, not direct promotion of a global skill
rule. It does not authorize a skill edit.

No new project `AGENTS.md` rule or repo-local skill is justified. Existing
canonical evidence already records the closed constructors and reuse
conditions, and the transient grammar evaluators do not constitute a repeated
stable workflow worth packaging.

## Outer-Step Provenance Findings

The experimental evidence can close, but the current `step-report.md` needs the
following minimum repairs before the outer step is complete:

1. Replace the stale top-level status “complete experiment awaiting independent
   result review” with the reviewed contradicted verdict, completed restoration,
   no paper change, and current REVIEW/route state.
2. Change Node E003 from “In progress” to its completed implementation-review
   disposition. The later paragraphs already contain the final APPROVE; the
   status line must agree.
3. Add EXPERIMENT gate-entry alignment explicitly naming the reads of
   `docs/user-instruction.md` and `docs/questions-for-author.md` and how the
   chosen loop respected them.
4. Complete the WRITE gate record with entry/exit time, parent, instruction
   reread, paper verification, and transition to REVIEW. Do not add a writing
   skill or paper edit.
5. Complete REVIEW with this audit's direction, efficiency, maintenance,
   ranked objections, root response, and exact next route. Record the absence
   of `scripts/check_progress.py` as non-gating.

`docs/evaluation.md` already contains the required Step 0029 frontier and raw
links. No other canonical scientific update is required for closure.

## Ranked Open Paper-Level Objections

1. **RQ3 coverage remains partial.** Current positive evidence covers task
   partitions and operation boundaries, while the paper itself says direct
   phase/action and literal-name accuracy on unseen agents/task families is not
   complete. Step 0029 does not fill that gap.
2. **RQ2's strongest remaining scope is downstream consequence.** The fixed
   reader result supports group prioritization but does not show lower work,
   human productivity, remediation, or universal view superiority. A future
   experiment is admitted only if it can change the bounded paper answer, not
   merely add another dataset or ranker.
3. **Adaptive RQ3 evidence must remain scoped.** Step 0024 is post-hoc
   implementation-selection evidence on reused populations. Step 0029 does not
   convert it into untouched confirmation and does not weaken its valid bounded
   role.

None of these objections invalidates Step 0029 or requires a new grammar
candidate. They are paper-level selection inputs for later steps.

## Routing And Exit Decision

After the five Markdown repairs above, close Step 0029 with:

```text
EXPERIMENT: VALID / COMPLETE / CONTRADICTED; grammar candidate retired
WRITE: complete; no paper change
REVIEW: scientific contract intact; outer audit complete
```

Then return to `EXPERIMENT_GATE -> research-experiment-design PAPER-VALUE
ADMISSION` only because the fixed paper still has an explicitly open evidence
gap—not because Step 0029 failed. The next selection should compare at least:

- direct target-blind phase/action/literal-tag accuracy under RQ3; and
- a genuine paper-level downstream decision consequence under RQ2.

Choose the one most likely to change the paper's current bounded answer using
real published/official assets and the smallest fair complete experiment. Reuse
existing traces and scorers where they actually answer that question. Do not
repair or rename Step 0029, do not add a second grammar, do not reopen closed
cutoff/window branches, and do not wait for human judgment.

The current outer state therefore has no scientific blocker and one narrow
documentation blocker: finish the step report, then select the next paper-value
branch. No algorithm rescue is part of the transition.

## Follow-Up Verdict — 2026-07-15T16:01:34-07:00

**Scope:** only the five provenance repairs required above
**Verdict:** **PASS**
**Remaining must-fix findings:** none

The repaired `step-report.md` resolves all five findings without reopening the
experiment or changing scientific meaning:

1. its top-level status now records the reviewed contradicted result, exact
   Step 0024 restoration, no-paper-change WRITE outcome, and no automatic
   algorithm retry;
2. Node E003 now has a completion time and the final focused implementation
   `APPROVE` status;
3. EXPERIMENT gate entry explicitly records the complete reread of
   `docs/user-instruction.md` and `docs/questions-for-author.md` and explains
   how the one-constructor, existing-trajectory loop followed them;
4. WRITE now records its parent, bounded timing, instruction reread, full-paper
   and repository verification, no-skill/no-paper action, and transition to
   REVIEW; and
5. REVIEW now records this audit's Direction, Efficiency, and Maintenance
   findings, ranked paper-level objections, root disposition, missing progress
   diagnostic as non-gating, and the exact paper-value route.

The repair added provenance and routing only. The research worktree still has
no diff under `docs/paper/`, `docs/agentpprof-paper`, `agentpprof/`, or the
removed Step 0029 script paths. The only canonical scientific diff remains the
already audited 25-line Step 0029 history entry in `docs/evaluation.md`; it
does not alter an RQ, hypothesis, claim, thesis, story, or reader-facing result.
The separate shared skill checkout has pre-existing/concurrent dirty state in
`iter-refine-writing/SKILL.md` and one `analysis/` retrospective, but the
Step 0029 report repair neither edits nor claims either file; they remain
outside this step and its publication scope.

Step 0029 is therefore closed consistently as:

```text
EXPERIMENT: VALID / COMPLETE / CONTRADICTED; candidate retired
WRITE: complete; no paper change
REVIEW: PASS; scientific contract intact; no automatic algorithm retry
```

No further Step 0029 repair, rerun, writing action, skill change, or follow-up
audit is required. No Git action was performed.
