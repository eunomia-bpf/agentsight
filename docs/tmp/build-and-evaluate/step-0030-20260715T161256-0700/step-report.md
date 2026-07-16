# Step 0030: Reference-Calibrated Existing-Trajectory Recurrence

**Step entered:** 2026-07-15T16:12:56-07:00
**Report updated:** 2026-07-15T17:52:23-07:00
**Phase:** `BUILD_AND_EVALUATE`
**Outer sequence:** `EXPERIMENT_GATE -> WRITE_GATE -> REVIEW_GATE`
**Fixed paper-level RQ:** **RQ3: How accurate are the tags?**
**Fixed thesis:** **Agent observability needs profiling, not only debugging.**
**Current status:** complete; independent outer audit `APPROVE`, zero Step 0030
must-fix

## Step Entry And Direction

This step follows the user's direct request to improve the existing algorithm
on already completed trajectories rather than invent another constructor or
collecting another dataset. At entry, the root reread `docs/user-instruction.md`,
the complete `docs/idea-story.md`, `docs/evaluation.md`, the active
`docs/paper/main.tex`, and the Step 0024--0029 frontier. The selected work keeps:

- the exact thesis and original AgentProf story;
- the four fixed RQs and RQ3's meaning;
- Step 0024 action-transition NPMI and operation-stack construction;
- the complete retained OSWorld-Human and CodeTraceBench trajectories; and
- the label-free Step 0024 constructor as the default.

The only tested change is one optional information budget: independently
grouped reference operations select one scalar recurrence cutoff. The target
still exposes only session order and visible actions before predictions are
fixed. This is a bounded hypothesis about partition fidelity within RQ3, not an
answer to the complete RQ or permission to change the paper story.

## EXPERIMENT_GATE

### Gate Entry

The gate entered because RQ3 still had an implementation-level uncertainty:
whether the existing recurrence score's unsupervised two-means cutoff, rather
than the score itself, limited its operation partition fidelity. The candidate
was selected over a new benchmark, score, context window, grammar constructor,
or target-tuned threshold because it reuses the strongest current mechanism and
all existing real data. `research-experiment-design` owned admission, planning,
plan review, real preflight, full execution, result review, and return.

### Node E30.1 — Approved Scientific Plan

**Status:** complete
**Owner report:** [experiment-plan.md](experiment-001/experiment-plan.md)
**Independent review:** [plan-review.md](experiment-001/plan-review.md)

The plan retains the Step 0024 NPMI association table and unseen-transition
boundary rule. It enumerates a cutoff below the minimum observed reference
score, every midpoint between adjacent distinct scores, and a cutoff above the
maximum. It selects the scalar with the best per-operation B-cubed partition F1
on grouped reference operations; exact ties choose the smallest cutoff.

OSWorld-Human uses the existing five session-blocked folds. Each held-out fold
gets only the other folds' visible actions for the NPMI model and their group
annotations for cutoff fitting. CodeTraceBench builds the score table on 2,229
target-disjoint normalized sessions, fits the scalar on 483 solved grouped
sessions, and applies it unchanged to 405 failed target sessions. No target
group, boundary metric, framework identity, or target result enters selection.

The predeclared primary outcome is per-operation B-cubed F1 on both complete
target populations. Boundary precision/recall/F1 are diagnostics and invalidate
the result only if they expose a coverage, correctness, comparison, or exact-
claim defect. Step 0024 is the matched default baseline; the richer OSWorld
supervised predictor and CodeTrace phase-change partition are context
comparators with different information.

The fresh plan reviewer approved the plan with no must-fix. A separate
implementation review was performed before the project-local anti-review-bloat
rule existed; it found real target-label timing and population-identity defects.
This step records it as useful but non-default process, and the new rule now
requires future experiments to fold such checks into plan/result review unless
a concrete unresolved validity risk requires separation.

### Node E30.2 — Real Preflight And Execution Repairs

**Status:** complete after execution-only repair
**Reports:** [preflight-report.md](experiment-001/preflight-report.md),
[experiment-result.md](experiment-001/experiment-result.md)
**Scientific raw root:**
`.agentsight/experiments/rq3-reference-calibrated-existing-traces-v1/`

The real preflight contacted the actual OSWorld operations, Step 0024 score
path, grouped reference input, cutoff fitter, and output path. The first
terminal invocation left only the OSWorld portion; the unchanged rerun completed
the preflight. This established executability only and contributed no paper
metric.

The first full invocation completed all five OSWorld folds but stopped in
native PyArrow filtering before CodeTrace target predictions or metrics. A
multiprocessing variant stopped in the same native path after producing
calibration output. Neither failure altered the candidate, candidate set,
information boundary, metric, population, or interpretation. The final repair
moved exact-ID manifest extraction into a short-lived subprocess with no output
channel for unselected rows. The parent fitting/prediction process receives only
selected calibration stages before target predictions and selected target
stages only after predictions persist. The final invocation recomputed the full
OSWorld and CodeTrace matrix from the approved plan.

This execution history also demonstrates a defect in the then-current shared
experiment skill: Step 0028 had permanently closed the same scientifically
untested protocol after two self-authored adapter failures. The failures were
about the harness, not the hypothesis. Under the user's later direct
instruction, the shared skill patch removes the arbitrary attempt count and
closes only when execution would require changing the approved experiment or
continued repair is no longer the highest-paper-value action. The skill change
is unstaged in its own human-review repository and is not part of this
repository's publication.

### Node E30.3 — Complete Scientific Result

**Status:** `VALID / SUPPORTED / SUPPORTING / ADDITIONAL RQ EVIDENCE`
**Independent raw review:** [result-review.md](experiment-001/result-review.md)

The final complete target populations are:

| Population | Sessions | Operations | Adjacent decisions | Oracle groups/stages |
|---|---:|---:|---:|---:|
| OSWorld-Human | 287 | 3,978 | 3,691 | 2,042 |
| CodeTraceBench failed target | 405 | 20,866 | 20,461 | 2,948 |

The independently reconstructed primary results are:

| Population | Step 0024 B-cubed F1 | Calibrated B-cubed F1 | Delta |
|---|---:|---:|---:|
| OSWorld-Human | 0.786169543748 | 0.801087216271 | +0.014917672522 |
| CodeTraceBench | 0.649173103932 | 0.666563572806 | +0.017390468874 |

OSWorld boundary F1 also rises from 0.679922 to 0.733953. CodeTrace boundary
F1 falls from 0.287106 to 0.236176 as the candidate merges 6,897 label-free
groups into 5,331; B-cubed precision falls and recall rises enough to improve
the predeclared partition objective. This is a genuine fragmentation/merging
tradeoff. It forbids claims of universal boundary improvement or all-metric
dominance but does not invalidate the tested partition-fidelity hypothesis.

The fresh result reviewer reimplemented NPMI, candidate enumeration, B-cubed,
fold assignment, and CodeTrace stage expansion without importing the new
evaluator. It reconstructed every target set, selected cutoff, prediction,
segment, and metric. All five OSWorld cutoffs and the CodeTrace cutoff are
unique optima in the scientific populations. No target labels reach fitting or
prediction.

The evidence supports an optional grouped-reference calibration mode. It does
not establish equal-information superiority over the label-free default,
literal motif-name correctness, phase/action identity, untouched cross-family
generalization, or a complete RQ3 answer. The thesis, four RQs, positive RQ3
hypothesis, and paper story remain unchanged.

### Node E30.4 — Exact Product Port And Product Review

**Status:** complete; independent product verdict `APPROVE`, zero must-fix
**Plan:** [product-port-plan.md](product-port-plan.md)
**Review:** [product-port-review.md](product-port-review.md)
**Equivalence raw root:**
`.agentsight/experiments/rq3-reference-calibrated-rust-equivalence-v1/full/`

The Rust port adds one optional repeated input,
`--induce-calibration-operation-file`, available through CLI and profile spec.
It requires a separate score-reference corpus, grouped calibration operations,
and calibration/target session disjointness. It adds no numeric cutoff flag,
benchmark identity, framework rule, score term, context window, algorithm name,
or target metric. Omitting calibration retains Step 0024 behavior and omits the
supervised-only report fields.

The first independent product review preserved the scientific verdict but
requested changes because Rust initially weighted B-cubed by each operation's
profile resource `value`, while the tested Python objective gives each operation
one vote. Unit-valued scientific trajectories masked the difference. The port
was reduced to per-operation counts; profile values remain additive outputs but
cannot select the cutoff. Regression tests now prove that changing only
calibration resource values leaves the complete induction report unchanged.

The same repair adds one actual exact-tie case (three candidates, two best ties,
smallest cutoff selected), calibration-without-induction and missing-group CLI
errors, and profile-spec coverage. After repair:

- 44 Rust unit tests pass;
- 10 CLI/profile-spec integration tests pass;
- 3 standard-trace CLI tests pass;
- formatting, Clippy with warnings denied, and release build pass; and
- the release binary again matches Python on all 3,691 OSWorld and 20,461
  CodeTrace target decisions, all six cutoffs, label-free decisions, NPMI
  values, segments, motifs, and pooled metrics.

The same independent product reviewer then reread the repaired fitter, report,
CLI/profile-spec path, tests, and complete equivalence artifacts. It confirmed
that calibration resource values cannot affect fitting, the exact-tie and
invalid-input cases exercise the intended contracts, and the release binary is
newer than the repaired source. Its follow-up verdict is `APPROVE` with no
remaining must-fix; the scientific verdict remains `VALID / SUPPORTED`.

### Experiment Gate Transition

The experiment is complete and scientifically valid. It returns one supported
local hypothesis and an exact optional product path to WRITE. It does not
automatically close RQ3 or authorize another candidate. The gate transitions to
targeted `WRITE_GATE` with the exact annotation advantage and CodeTrace
partition/boundary tradeoff as required qualifications.

## WRITE_GATE

### Gate Entry And Scope

BUILD_AND_EVALUATE permits only evidence and implementation updates without
changing the scientific contract. The root reread the complete paper and
updated only the boundary-construction mechanism, the RQ3 protocol/table/result
paragraphs, focused design/implementation/evaluation summaries, and local
format-driven prose. Title, abstract, introduction, motivation, four RQs,
contributions, and original story remain unchanged.

### Node W30.1 — Canonical Evidence And Artifact Update

`docs/evaluation.md` now records Step 0030's complete populations, primary and
diagnostic metrics, independent reconstruction, exact Rust/Python replay, honest
information advantage, and the Step 0028 skill/execution deviation.
`docs/design.md` and `docs/implementation.md` define the optional scalar path,
per-operation B-cubed meaning, CLI/profile-spec boundary, default compatibility,
and supporting evidence. `CLAUDE.md` (`AGENTS.md`'s symlink target) now carries
one project-local rule: implementation validity belongs in the consolidated
plan/result reviews unless a concrete unresolved validity risk justifies a
separate review, evaluator, checker, or equivalence workflow. Counts of files,
checkers, and reviews are not progress.

### Node W30.2 — Targeted RQ3 Paper Update

The active AAAI paper under `docs/paper/` adds:

- the optional single-scalar mechanism and target-label boundary;
- a calibrated recurrence row on the same five held-out OSWorld folds;
- OSWorld B-cubed 0.801 and boundary F1 0.734;
- CodeTrace B-cubed 0.649 to 0.667 using 483 solved reference sessions and 405
  disjoint failed target sessions; and
- the explicit CodeTrace boundary-F1 tradeoff and annotation advantage.

The paper does not claim equal-information superiority, literal tag-name
accuracy, universal boundary improvement, untouched confirmation, or complete
RQ3 closure. Intermediate failed runs and rejected candidates remain internal.

### Node W30.3 — AAAI-27 Format Verification

The official AAAI-27 Main Technical Track page states a seven-page main-content
limit and nine-page total limit, with pages after seven reserved exclusively for
references: <https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/>.
The paper uses `\usepackage[submission]{aaai2027}`, letter paper, anonymous
author metadata, and the 2027 template marker.

The new RQ3 row initially pushed Conclusion onto page eight. Using
`tighten-prose-systems-latex`, the root removed repetition in the RQ3 result and
Related Work without deleting a result, caveat, mechanism, citation, or
scientific distinction. The conclusion now ends with the exact fixed thesis.
The resulting PDF is nine pages: all main content including Conclusion ends on
page seven, and pages eight and nine contain References only. `pdflatex`
reports no overfull box, undefined reference, multiply defined reference, or
fatal LaTeX warning. It reports only nonfatal underfull box diagnostics; all
fonts are embedded, and the page is US letter. This local format-driven
tightening follows the user's direct AAAI format instruction and changes no
scientific meaning.

AAAI-27 also requires a separate reproducibility-checklist upload. The official
blank `ReproducibilityChecklist.tex` is present, but it is intentionally not
claimed complete while research iteration continues. This does not change PDF
page compliance, but it remains a submission-package action before declaring
the paper submission-ready.

### Write Gate Verification And Transition

The paper compiles, preserves the exact thesis and four RQs, organizes
Evaluation by RQ, includes only independently reviewed Step 0030 numbers, states
the information advantage and tradeoff, and remains within the official page
allocation. The paper submodule `docs/agentpprof-paper` remains untouched at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`. WRITE transitions to REVIEW.

## REVIEW_GATE

### Scientific-Contract Audit

The independent outer audit confirms that Step 0030 modifies one optional
implementation detail and adds supporting RQ3 partition evidence. It does not
change the problem, thesis, insight, scope, motivation, contribution structure,
RQ count/meaning, baseline families, workload coverage, or evaluation metric
meaning. The exact thesis remains visible in Abstract, Introduction, and
Conclusion; the paper still states exactly the four fixed RQs.

### Outer Audit And Meta-Review

**Independent report:**
[outer-audit-20260715T174840-0700.md](outer-audit-20260715T174840-0700.md)
**Final verdict:** `APPROVE`

The fresh auditor first formed a blind whole-paper attack map, then inspected
the complete idea history, user instructions, child reports, raw scientific
and equivalence roots, product source/tests, canonical docs, paper source/PDF,
official AAAI call, current diff, and clean submodule. It found no Step 0030
must-fix. It independently confirms complete target coverage, the scoped B3
improvement on both populations, the real CodeTrace boundary tradeoff, the
per-operation Rust repair, label-free default compatibility, exact thesis and
four-RQ preservation, and AAAI main-paper format compliance.

The meta-review accepts the current project-local anti-review-bloat rule as the
smallest sufficient process correction. The historical extra reviews remain
because they found concrete timing and resource-weight defects, but future
steps must not copy that structure by default. The audit also identified one
stale resumability issue: the top RQ3 frontier row mentioned only Step 0024.
The root updated that existing row with Step 0030's optional annotation-budget
result and boundary tradeoff; it added no new document, gate, or mechanism.

Paper-wide objections remain explicit rather than treated as Step 0030
failures: RQ3 does not yet establish phase/action/literal identity, development
populations informed mechanism selection, familiar components create novelty
pressure, RQ2 supports prioritization rather than universal work reduction,
and the separate reproducibility checklist is blank. Canonical-document length
is maintenance debt, not authority to start a compaction loop now.

The next outer cycle remains `BUILD_AND_EVALUATE`. Its EXPERIMENT gate must
first compare cumulative evidence synthesis with a bounded search for genuine
held-out phase/action/identity evidence. It may admit one experiment only if it
can change the paper-level RQ3 answer using a real published or official source;
otherwise it records the skip and continues. It must not restart calibration,
invent a constructor, vary a cosmetic cutoff/metric/dataset, add another
checker, shrink RQ3, or wait for human judgment.

## Ranked Remaining Objections After Outer Audit

1. RQ3's complete positive hypothesis includes task, phase, action, and group
   boundary accuracy; Step 0030 adds partition evidence only and does not itself
   validate literal names or phase/action identity.
2. Step 0030 reuses development populations and spends grouped reference
   annotations, so it is supporting implementation evidence rather than
   untouched generalization.
3. The complete paper has not yet received a new milestone acceptance review;
   run it only after every fixed RQ has an evidence-backed answer.
4. The separate AAAI reproducibility checklist remains unfilled and must be
   completed against the final paper and artifact before submission readiness.

None of these objections changes the thesis or invalidates the completed Step
0030 result. The independent audit retains them as paper-wide or submission
work and approves transition to the next outer cycle's EXPERIMENT admission
decision.

## Git And Publication State

No child skill or gate ran Git publication. The root staged only the coherent
Step 0030 repository changes and committed them on the existing
`research/semantic-flamegraph-artifacts-v2` branch without creating or
switching a branch. A normal push was attempted and failed with remote HTTP 500
and an unexpected sideband disconnect; `ls-remote` confirmed that the remote
branch remained at `f2e878acbd5324806e05a698c34f727fb3d37cd6`, 88 commits
behind the local branch after this step. No force push or alternate publication
path was attempted. The paper submodule was neither staged nor modified. The
shared skills repository remains unstaged and uncommitted for human review
under its own `AGENTS.md` policy.
