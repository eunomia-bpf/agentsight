# Step 0020 — Improve Operation-Stack Induction On Existing RQ3 Trajectories

**Started:** 2026-07-15T00:14:04-07:00
**Phase:** BUILD_AND_EVALUATE
**Outer gate:** EXPERIMENT
**Status:** Complete
**Owner:** root orchestrator

## Fixed Scientific Contract

This step preserves the read-only canonical story in
`docs/agentpprof-paper/main.tex`, the exact thesis **“Agent observability needs
profiling, not only debugging.”**, the two core abstractions (operation and
operation stack), the three-contribution chain, and exactly four paper-level
research questions. The authoritative submodule is not edited. During
BUILD_AND_EVALUATE, title, abstract, introduction, motivation, contributions,
section structure, related-work story, and conclusion are frozen. This post-hoc
mechanism-development run cannot promote its quantitative OSWorld result into
the paper as fresh RQ3 evidence. A supported result routes only to minimal
implementation/port consideration and later independent confirmation.

The fixed input question is:

> **RQ3 — How Accurate Are the Tags?**

The fixed positive paper-level hypothesis remains that a target-blind fixed
tagger or mapping assigns accurate, stable task, phase, action, and boundary
identities on unseen agents and task families without materially corrupting
attribution. This step develops a better candidate mechanism on an already
observed population; it does not complete a missing component of that
hypothesis. It does not change the RQ or weaken the hypothesis in response to a
local result.

## EXPERIMENT Gate

### Node E001 — Entry And Resume Audit

At entry, the root inspected the active worktree, current branch, recent
research commits, authoritative paper-submodule pointer, prior step, and current
research frontier. The worktree was clean, the active branch remained
`research/semantic-flamegraph-artifacts-v2`, and the read-only paper submodule
was clean at `7f80c433c9555317a2aa45a78d0ff93518f4c12c`. The branch was 77
commits ahead of its remote because the prior normal push did not advance it;
this persistence backlog does not enter any scientific decision.

The root then read the complete current versions of:

- `docs/user-instruction.md`;
- `docs/questions-for-author.md`;
- `docs/idea-story.md`, from the permanent Initial Narrative through every
  accepted evolution entry and invariant;
- `docs/evaluation.md`;
- `docs/background-related-work.md`;
- the RQ3 method and result surface in `docs/paper/main.tex`;
- Step 0019's complete report and independent outer audit.

There are no open author questions. The author instructions require autonomous
continuation, real public data and published protocols where possible, one
complete experiment rather than smoke-only evidence, preservation of the four
RQs and ambitious original story, and reuse of existing mechanisms rather than
unnecessary experimental machinery.

### Node E002 — Current Evidence Boundary

The current paper has positive RQ3 evidence for two components:

1. a fixed supervised boundary tagger recovers session-held-out human operation
   groups on all 287 OSWorld-Human tasks (micro boundary F1 0.7388 and B-cubed
   F1 0.8160, above the registered simple controls); and
2. the existing target-blind TF-IDF/K-Means path recovers task partitions on
   the available Mind2Web and ScienceWorld sessions (operation-weighted
   V-measure 0.5565 and 0.8151 at full coverage versus zero for a constant
   control).

The built-in Rust operation-stack inducer is separately measured. Its
single-objective cap-free revision improves materially over the old and
depth-limited mechanisms but remains below strong simple controls on
OSWorld-Human. That mechanism result does not change RQ3, and this step will not
retune OSWorld-Human.

The explicit remaining paper gap is independent fidelity evidence for a
literal phase or action identity produced by a target-blind fixed mapping or
tagger. The next experiment must therefore use one independently annotated real
public trajectory family, one pre-specified fidelity hypothesis, the current
mechanism when possible, and no hidden-target feature construction. It must not
bundle phase, action, boundary, generalization, diagnosis, and cost into one
experiment.

### Node E003 — Public-Source Feasibility Screen (Stopped Before Experiment)

The root initially screened candidate sources for all of the following:

- real agent trajectories rather than a newly invented toy workload;
- independently authored phase, intent, or action annotations that can remain
  scorer-only;
- public executable access in the current environment without waiting for
  human approval;
- visible fields sufficient for one fixed target-blind AgentProf mapping or
  tagger;
- a complete population or a predeclared official split;
- direct relevance to the missing RQ3 component.

MLE-Traj was the leading semantic-label candidate because its published dataset
describes real human and agent Kaggle trajectories under an annotated
state/action/intent schema. TRAJEVAL is a leading large real code-agent source
with published search/read/edit stages. CodeTraceBench, AgentNet, and other
public trajectory collections are retained as fallbacks only if their released
labels directly support the missing RQ3 identity question rather than merely a
new boundary or problem-localization proxy.

The current machine has no Hugging Face authentication, while MLE-Traj requires
acceptance of a gated contact-sharing condition. TRAJEVAL exposes its analysis
code and precomputed paper outputs, but its authors explicitly omit roughly
63 GB of raw trajectories. No candidate data was downloaded, converted, or
used in an experiment. The user then explicitly redirected this step to improve
the algorithm on the already completed trajectories rather than introduce a new
dataset. That direct instruction supersedes this source-selection route; the
pipeline does not wait for gated access.

### Node E004 — User-Directed Route Change

At 2026-07-15T00:23:59-07:00, the user asked first whether the algorithm could
be improved and then required that improvement to reuse the trajectories that
had already run rather than create a new experiment source. The root accepts
this as an experiment-route change inside fixed RQ3, not as a thesis, RQ,
contribution, or paper-story change.

Step 0020 therefore reuses the complete OSWorld-Human population already
scored in Steps 0006, 0017, and 0018: 287 real human-demonstration sessions,
3,978 operations, 3,691 adjacent pairs, and 2,042 independently supplied human
groups. It does not collect another trajectory, add an annotation, change a
paper RQ, or rerun the current information-gain baseline merely to regenerate
identical evidence.

This is explicitly a post-hoc mechanism-development round. The same hidden
labels that exposed the current information-gain failure are available to the
final scorer, so even a large improvement cannot be presented as fresh
cross-family confirmation. It may justify replacing the implementation and
recording a stronger algorithm candidate; independent generalization remains a
later paper-evidence question.

### Node E005 — Failure Diagnosis And Candidate Principle

The current recursive information-gain objective minimizes categorical
uncertainty inside each segment. That objective is mismatched to the existing
human groups: a correct operation group frequently contains heterogeneous
actions such as `click -> type -> press`, while adjacent one-action groups may
share the same `click` value. Cap-free recursion improves the old mechanism but
cannot repair this objective mismatch; its complete result remains boundary F1
0.4720 and B-cubed F1 0.6720.

The replacement candidate uses one directly paper-aligned principle: operations
that recur together across sessions should form the same reusable operation
identity. For the visible action sequence, it estimates the normalized
pointwise mutual information of adjacent action pairs from other sessions. A
deterministic one-dimensional two-means split separates low-association from
high-association transitions without a label-tuned cutoff. Low-association or
previously unseen transitions start a new operation; high-association
transitions continue the current one. A run-length-compressed action sequence
names the resulting operation frame, so identical recurring motifs receive the
same cross-session identity.

A first read-only exploratory diagnosis using the already visible full
population reported boundary F1 about 0.732 and B-cubed F1 about 0.797. The
independent plan reviewer found that this first calculation mixed the
operation-count sample space for action marginals with the adjacent-pair sample
space for the joint probability, so it was not mathematically standard NPMI.
The root rejected those diagnostic numbers rather than preserving a favorable
but incorrectly named score.

The corrected diagnostic uses left and right transition marginals over the same
pair population. On the exact five existing session folds it produces boundary
F1 about 0.680 and B-cubed F1 about 0.786. It remains above the current cap-free
information-gain mechanism and the strongest simple controls on both metrics,
so the principle remains worth one complete reproducible run. Both diagnostic
calculations were observed before final plan approval and are design evidence,
not confirmatory results. The revised registered plan fixes the corrected
algorithm exactly and prohibits cutoff, field, fold, or metric search.

### Node E006 — Independent Plan Review And Repair

The fresh plan review is recorded in
`experiment-001/plan-review-round-1.md`. It returned `REVISE` with four bounded
repairs: use coherent transition marginals for NPMI; state the post-hoc paper
role unambiguously; restrict the scored object to session-local segmentation
and partition fidelity; and disclose that the candidate uses cross-session
unlabeled recurrence statistics whereas the existing Rust baseline is
per-session. The root accepts all four findings. No new dataset, baseline,
metric, threshold, ablation, or uncertainty machinery is added.

### Node E007 — Approved Plan, Implementation, And Real Preflight

The repaired plan fixes one construction and one full run. It uses the exact
existing `r290` operation file, existing five session-blocked folds, same
human-group scorer, Step 0018 cap-free information-gain output, and registered
always-boundary strongest simple control. The implementation is
`script/rq3_recurrence_stack_induction_eval.py`; it validates exact pair keys,
recomputes labels from the current source, and checks every imported baseline
decision against its adjacent session-path change.

The independent implementation review first found that the Step 0018 loader
trusted summary metadata and row counts too broadly. The root repaired it to
validate the full/depth-255/nonbinding configuration, reject duplicate,
missing, or unexpected pair keys, recompute every scorer label, and verify
per-session policy, depth, counts, mass, and stop conditions. Final review
passed.

REAL PREFLIGHT ran the fixed candidate on fold 0 only: 45 test sessions, 521
operations, and 476 adjacent pairs. It conserved all 521 units and completed
end to end. Boundary F1 0.4948 and B-cubed F1 0.6992 were recorded only as
preflight evidence and did not change any plan choice. A fresh independent
reviewer checked source coverage, isolation, output structure, and conservation
and returned `PASS`.

### Node E008 — Complete Run And Independent Result Review

The full fixed run completed all five folds over 287 sessions, 3,978
operations, and 3,691 adjacent pairs. Recurrence induction reaches boundary F1
0.6799224054 and operation-weighted B-cubed F1 0.7861695437. Relative to the
Step 0018 cap-free information-gain baseline, the gains are +0.2079529308 and
+0.1141632755. Relative to the strongest registered always-boundary control,
the gains are +0.0354126735 and +0.1077642281. The candidate produces 2,656
segments across 44 recurring motifs and conserves all 3,978 AgentProf units.

The scientific verdict is `SUPPORTED` for the bounded mechanism-development
hypothesis. The result does not establish fresh RQ3 generalization because this
population's hidden groups had already exposed the old mechanism's failure. It
also does not validate motif names or all task, phase, and action identities. A
fresh reviewer reconstructed the source, folds, decisions, confusion counts,
B-cubed terms, controls, and deltas directly from raw output and hidden key and
returned `PASS`.

### Node E009 — Minimal Rust Port And Review

The approved port replaces the runtime information-gain implementation behind
the existing `--induce-operation-stack` interface; it does not create a second
algorithm name. Optional `--induce-reference-operation-file` supplies the
label-free learning population. Each target and reference operation must have
exactly one nonempty `session` and `action`; input order defines the sequence,
and each adjacent transition contributes one count. Invalid or degenerate input
returns an explicit error without a heuristic fallback.

The Rust report exposes every session-local boundary decision and every
segment's start, end, and recurring motif. Legacy depth, query, and session
knobs are rejected under recurrence induction; the old task-stack flag remains
only as a deprecated alias to the same path. Unit and CLI tests cover
determinism, unseen transitions, motif folding, mass conservation, reference
isolation, errors, legacy-option rejection, and exact hidden-field invariance.

The first independent code review found one bounded defect: a profile spec with
explicit `"induce_allow_session": false` was silently accepted because only
the boolean value, not option presence, was checked. The root repaired the
guard and added a regression test. Final review returned `PASS`; formatting,
clippy with warnings denied, all unit/integration tests, release build, and diff
whitespace checks pass.

### Node E010 — Rust/Python Equivalence

`script/rq3_recurrence_stack_rust_equivalence.py` replays the release Rust CLI
on the same five folds with inputs restricted to unit weight plus `session` and
`action`. An independent pre-execution review found a duplicate-row blind spot
in an adapter dictionary; raw-cardinality and explicit duplicate-key checks
were added before the full run.

The completed equivalence run matches 3,691/3,691 boundary decisions,
3,978/3,978 motif assignments, and 2,656/2,656 segments exactly. All learned
centers and cutoffs match within `1e-12`, all 44 motifs agree, all 3,978 profile
units are conserved, train/test folds are disjoint, and each Rust invocation
exits successfully with empty stderr. A fresh reviewer independently rebuilt
the folds, NPMI scores, two-means centers, segments, motifs, and masses and
returned `PASS`.

## WRITE Gate

Completed after EXPERIMENT. The current implementation, design, evaluation
frontier, literature frontier, idea history, and AAAI paper now describe the
recurrence runtime while preserving the exact thesis, four RQs, contribution
chain, and read-only canonical submodule. The paper leads with the released
recurrence mechanism, marks the supervised predictor as an extra-information
comparator, and keeps the already-observed OSWorld numbers as development
evidence rather than fresh cross-family proof.

The paper removed stale automatic-induction AP/work numbers belonging to the
former runtime, added the current NPMI/two-means contract and recurrence result,
and repaired segment terminology and RQ2 headline scope. It remains seven pages
of main content plus two pages of references.

## REVIEW Gate

Completed. The first outer pass found four paper attribution/authorization
defects: implicit rather than opt-in induction wording, a supervised stack count
placed after recurrence, an RQ3 summary that swept development evidence into
confirmation, and an unnecessarily mechanism-specific Intro edit. All four
were repaired; the re-audit returned `PASS`.

The whole-paper reviewer then found current-system headline, segment
terminology, algorithm-contract, RQ2 headline, page-limit, font, package, and
caption issues. Targeted repairs made the release mechanism the headline,
specified the compact mathematical contract, restored evidence boundaries,
put all main content within page seven, removed forbidden font/package usage,
and moved table captions below their tables. Final consistency, whole-paper,
and format re-reviews all returned `PASS` for Step 0020.

The broader AAAI submission remains `REPAIR`: one independent real-family RQ3
confirmation and the separate reproducibility checklist are still outstanding.
Neither gap authorizes another OSWorld variant or a change to the thesis, story,
contributions, or four RQs.

## Git Persistence Boundary

At closure, the root persists the complete Step 0020 implementation, reports,
paper sync, and format repair in one normal commit and attempts a normal push on
the existing branch. Git operations remain decoupled from the scientific state
machine: no branch is created or switched, no force push is used, and no commit
or push result enters an EXPERIMENT, WRITE, or REVIEW verdict.
