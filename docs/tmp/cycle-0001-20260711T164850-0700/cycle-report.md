# Cycle 0001 Report — Restored Agent Profiling Program

## Current Cycle Frontier — 2026-07-12T20:17:00-07:00

The current author-fixed thesis is exactly **“Agent observability needs
profiling, not only debugging.”** The active paper and canonical frontier use
exactly four RQs: resource attribution, correspondence to real problems, tag
accuracy, and profiling cost.

The author found that the untouched submodule still told a stronger story and
directed a complete restoration. The previous profile-to-intervention route is
superseded. `docs/agentpprof-paper/main.tex` is now the read-only canonical
story source, and the active AAAI paper again follows its direct sequence:
long-running quality/safety/cost stakes, debugging versus profiling, the
semantic profiling challenge, operations and operation stacks, AgentProf, and
the original attribution/localization/tag-accuracy/cost evaluation program.

The restoration covers the title, Abstract, Introduction, Background and
Motivation, Design, Implementation, contributions, RQ2 meaning, Related Work
emphasis, and Conclusion. It retains the AAAI template and evidence discipline
without copying unsupported historical result numbers. The paper builds cleanly
to seven pages; references begin on page six.

The next empirical route is the original RQ2 hidden-annotation localization
question:

1. select official public agent benchmarks with independently supplied failure,
   safety, redundancy, or task-boundary labels;
2. fix semantic tags and ranking without target labels;
3. compare flat, per-session, native, raw-action, and semantic grouping over the
   same visible operations, with hidden-label views only as oracle bounds;
4. complete every planned task and report localization quality plus analyst
   inspection work;
5. propagate only the completed positive result without changing the canonical
   story.

Current reports:

- `docs/tmp/cycle-0001-20260711T164850-0700/03-review-gate/idea-discussions-20260712T193851-0700/100-direct-user-disposition.md`;
- `docs/tmp/cycle-0001-20260711T164850-0700/02-write-gate/996-independent-canonical-story-reaudit-20260712T201100-0700.md`;
- `docs/tmp/cycle-0001-20260711T164850-0700/02-write-gate/999-gate-report-20260712T201130-0700.md`;
- `docs/tmp/cycle-0001-20260711T164850-0700/03-review-gate/000-gate-reentry-20260712T201619-0700.md`;
- `docs/tmp/cycle-0001-20260711T164850-0700/03-review-gate/100-idea-unchanged-skip-20260712T201619-0700.md`;
- `docs/tmp/cycle-0001-20260711T164850-0700/03-review-gate/900-meta-review-20260712T201700-0700.md`.

## Cycle-Level Direction, Efficiency, And Maintenance

- **Direction:** the submodule story is restored; hierarchy selection and the
  later intervention program are not the paper's center.
- **Efficiency:** do not run another broad story discussion or full writing
  refinement. Complete one original-RQ experiment at a time.
- **Maintenance:** E007, the RQ frontier, design/implementation/literature
  frontiers, user log, and project AGENTS rule now name the submodule as the
  canonical story source and restore RQ2 localization.
- **Capability learning:** the failure was a WRITE authority defect: exact
  thesis/RQ checks did not preserve section-level story. Shared skills remain
  unchanged pending human review; the project-local source lock prevents a
  recurrence here.

## Root Routing Response To Post-Restoration Meta-Review

Accept the meta-review's direction and efficiency findings. The old
intervention-oriented route is superseded. Do not run another idea or writing
loop before evidence. Enter EXPERIMENT with exact RQ2 and first perform one
bounded official-source/protocol/baseline refresh, followed by one complete
target-blind hidden-annotation localization experiment. Preserve every failed or
invalid run in history, but propagate only independently grounded completed
positive evidence into the canonical paper story.

## Historical Cycle-Entry Assessment

The remaining sections preserve the original cycle-entry venue and
source-fidelity assessment. They are historical evidence, not current
scientific authority. In particular, their hierarchy-centered framing,
leave-one-family-out RQ2 proposal, and pre-restoration evidence program have
been superseded by the current frontier above.

## Objective

Determine whether the current AgentProf paper is ready for a top conference,
evaluate AAAI-27 as the immediate target, establish a safe canonical paper
workspace without modifying the existing paper repository, and choose the next
decisive research experiment.

## User-Intent Check

The requested direction is ambitious: retain the central claim that agent
observability needs a profiling abstraction beyond individual traces, and seek
stronger evidence rather than shrinking the contribution for convenience. The
paper must use real agents, real trajectories, and public benchmarks. The
read-only English paper repository must not be modified. These constraints are
recorded in `docs/user-instruction.md` and remain binding for later cycles.

## Inputs Read

- English paper: `docs/agentpprof-paper/main.tex` and `references.bib` at the
  subproject's current commit `7f80c43`.
- Chinese paper: `docs/visexp/paper/main.tex` and its supporting files.
- Research ledgers: `docs/evaluation.md`, `docs/idea-story.md`, and selected
  reports under `docs/visexp/out/`.
- Official venue sources: AAAI-27 Main Technical Track CFP and AAAI-27 Author
  Kit.

The outer worktree already contained unrelated modifications to
`docs/evaluation.md`, `docs/idea-story.md`, and the `docs/agentpprof-paper`
gitlink. This cycle did not overwrite, reset, stage, or commit them.

## Venue Finding

AAAI-27 is a plausible but demanding target. The abstract deadline is
2026-07-21 and the full-paper deadline is 2026-07-28, both at 23:59 UTC-12. The
Main Track accepts seven pages of main content and a maximum of nine pages total,
with pages eight and nine reserved for references. Review criteria explicitly
include significance, novelty, soundness of claims, relevance to AI, clarity,
responsible research, and reproducibility.

At cycle entry, the work was judged to fit AAAI only if presented and validated
as a general method for analyzing AI-agent behavior, not merely as a pprof
renderer or an AgentSight feature. The report then promoted a query-time
semantic operation-stack comparison into the strongest AAAI-facing thesis.
That promotion is historical and superseded by the notice above.

## Current Paper Assessment

The paper has unusually substantial assets for an early draft:

- four explicit RQs;
- 325 real Codex/Claude trajectories and 183,714 system observations;
- 15 public trajectory families, with four oracle-rich datasets used for six
  localization tasks;
- an implemented Rust profiler, pprof-compatible output, multiple real views,
  ablations, cost numbers, and held-out mapping experiments;
- a concise seven-page ACM draft with a clear operation/operation-stack model.

It is nevertheless not yet top-conference ready. The main scientific risks are:

1. **Novelty under an equally informed baseline.** Query-time field projection
   can look like hierarchical `GROUP BY`, labels, or a configurable trace query.
   The paper needs a strong SQL/tag baseline and a fixed trace-tree baseline with
   the same visible fields and comparable tuning effort.
2. **RQ1 construct validity.** The mixed-weight metric is at least partly
   determined by fields also used for grouping. A separate semantic oracle is
   needed before treating separation as semantic correctness.
3. **RQ2 hidden-label integrity.** Runtime omission of labels is insufficient if
   rules, fields, or ranking choices were designed after observing the same task
   labels. A real held-out family protocol is needed.
4. **Headline comparison.** The current median AP for operation stacks (0.312)
   is below per-session (0.348) and native hierarchy (0.357). The interesting
   result is a Pareto tradeoff in inspection work, recall, and fragmentation,
   but the paper must demonstrate this prospectively rather than selecting the
   favorable axes after seeing the outcomes.
5. **Tag claim mismatch.** RQ3 evaluates mapping-derived phases against native
   actions; it does not directly validate the free-form prompt tagger that is
   prominent in the model and RQ1 narrative.
6. **External validity.** The large real corpus comes from one development
   project, while the public tasks use heterogeneous converters and annotations.
   A common held-out protocol across independent families is needed to justify
   generality.
7. **Cost claim.** The paper reports offline profiling and tag latency but lacks
   a clean scale curve with CPU/RSS and risks calling offline analysis “zero
   overhead” without separating capture cost.
8. **Format.** The ACM source was not submissible to AAAI. The migrated PDF now
   occupies exactly seven content pages plus two reference pages, but figures
   still contain `Identity-H` embedded fonts and require a final font audit.

The independent source-fidelity audit found four concrete numerical/protocol
errors that must be corrected by evidence rather than prose polish:

- RQ1's 90.402% to 36.722% mixed-weight change is a projection/compression
  property. Its oracle is the same session/prompt key used in grouping, and the
  zero-mixing full view is explicitly “by construction”; it is not independent
  task-intent accuracy.
- RQ2's published table is produced by a hand-written ranker whose formula
  changes by task ID. It does not read hidden fields at runtime, but it is not a
  target-family-held-out method and therefore remains development evidence.
- RQ3's phase values come from a predefined action-to-phase taxonomy rather than
  a model trained on eight datasets. Only six datasets exceed 0.7 on both
  V-measure and applicable boundary F1; the paper's “7/9 on both” statement is
  false.
- RQ4 combines 35,136 fresh calls counted in R170 with a 31 ms p95 measured on a
  separate 900-request R123 benchmark. The 76-configuration timing study uses a
  debug binary, two distinct inputs, two repetitions, and no CPU/RSS scale curve.
  These numbers cannot be presented as one full-pipeline cost experiment.

## Actions Completed

1. Preserved the tracked Chinese paper in
   `docs/tmp/agentpprof-paper-zh-20260711/source/`.
2. Copied only Git-tracked files from the English paper repository at `7f80c43`
   into `docs/paper/`; the source repository was not modified.
3. Added the official AAAI-27 anonymous template, style, bibliography style, and
   reproducibility checklist to `docs/paper/`.
4. Converted `docs/paper/main.tex` from ACM `sigconf` to the official AAAI-27
   submission style and updated the build to run BibTeX.
5. Built a nine-page US-Letter PDF with embedded fonts and confirmed that main
   content ends on page seven and references occupy pages eight and nine.

## Gate Decision

- **EXPERIMENT:** not complete. The existing evidence is large but does not yet
  resolve the fair-baseline and held-out-label threats.
- **WRITE:** format canonicalization is complete, but scientific rewriting must
  follow the next decisive experiment so prose does not stabilize unsupported
  claims.
- **REVIEW:** initial full-paper review is in progress. Independent paper and
  experiment-asset reviews were requested and will be incorporated into the next
  node.

## Next Decisive Experiment

Run one complete experiment for the existing RQ2 without changing the RQ:

> **RQ2: Does profiler output correspond to real problems?**

Use leave-one-family-out evaluation across the current four oracle-rich public
families. For each held-out family, construct every method from visible fields
only, then compare AgentProf operation stacks with flat, per-session, native
hierarchy, raw-action, equally informed SQL/tag aggregation, and fixed trace-tree
baselines. Report AP/AUPRC, recall at a fixed inspection budget, work to fixed
recall, and groups to fixed recall as one Pareto surface, with per-family results
and bootstrap uncertainty. Run the full four-family matrix after a real preflight
on one family; a preflight cannot be reported as the experiment result.

The RQ is fixed. The experiment may change the supported conclusion: it can
support superiority, a Pareto advantage, or a negative result, but it may not
replace RQ2 with an easier question. If the experiment fails, the REVIEW and
WRITE loops must revisit the mechanism and propose a stronger operation-stack
construction or ranking method before rerunning a revised plan.

## Uncertainties to Carry Forward

- Whether existing RQ2 scripts already enforce family-level separation before
  rule/ranker construction, or only hide labels during scoring.
- Whether an equally informed SQL/tag and trace-tree baseline already exists in
  reusable form.
- Which figures introduce `Identity-H` fonts and whether their source scripts can
  regenerate them using AAAI-compliant fonts or outlined text.
- Whether AAAI Main Track is stronger than an AI-systems venue after the full
  fair-baseline result is known.
