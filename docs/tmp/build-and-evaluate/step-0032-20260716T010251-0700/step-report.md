# Step 0032 — Literal Phase/Action Identity Source Fidelity

**Entered:** 2026-07-16T01:02:51-07:00

**Phase:** `BUILD_AND_EVALUATE`

**Outer sequence:** `EXPERIMENT_GATE -> WRITE_GATE -> REVIEW_GATE`

**Current state:** complete; REVIEW gate and targeted follow-up PASS

**Fixed thesis:** **Agent observability needs profiling, not only debugging.**

**Selected paper question:** **RQ3 — How Accurate Are the Tags?**

## Entry Boundary And User Alignment

The root reread the complete `docs/idea-story.md`, `docs/user-instruction.md`,
`docs/questions-for-author.md`, the RQ frontier, Step 0031's reports and outer
audit, and the current paper. There are no open author questions. This step
must preserve exactly four RQs, the original submodule story, operations and
operation stacks as the two core abstractions, and the three contributions. It
may test or improve only a phase/action tagging mechanism inside fixed RQ3.

The user requires bold hypotheses with careful validation, real published
benchmarks and software, complete experiments, reuse of already-run
trajectories before new collection, no human wait, no branch change, no
submodule edit, and no story or hypothesis shrinkage after a local result. A
source whose target is copied into the visible input is rejected rather than
used for an easy score. A partition metric cannot stand in for literal label
accuracy.

Step 0031 is complete locally at `dbe9e1958d3e848216ddb404d2429d45ac8aaf96`.
Its normal push failed with remote HTTP 500 and sideband disconnect;
`ls-remote` shows the remote branch still at
`f2e878acbd5324806e05a698c34f727fb3d37cd6`. This push backlog is unrelated to
scientific admission and will be retried at this step boundary. No branch was
created or switched.

## EXPERIMENT_GATE

### Gate Entry And Fixed Evidence Need

RQ1, RQ2, and RQ4 have paper-level answers. RQ3 has positive evidence for task
partitions, one named backend's declared task-family labels, and operation
group boundaries, but not independent literal phase/action identity. The next
candidate must therefore answer one hypothesis about a fixed tagger or mapping
assigning a semantically comparable phase or action label while the official
target stays scorer-only.

Before writing an experiment plan, the gate screens already-held official
sources. The first candidate is CodeTraceBench because the repository already
contains all 1,000 verified manifest rows, official stage intervals, 2,634
reference sessions, 405 source-valid failed target sessions, normalized
operations, and current AgentProf outputs. The screen asks whether those
official stages carry a stable semantic vocabulary across trajectories or only
trajectory-local ordinal partition IDs. Only the former can support a literal
phase-label experiment.

Detailed source evidence and the next admission decision belong under this
step's single `literature-<timestamp>/source-screen.md`. No experiment plan is
created until a source passes non-circularity, semantic comparability,
coverage, and paper-value admission.

### Node 001 — CodeTraceBench Phase Gold Is Described But Not Published

The official CodeTracer paper defines five human workflow-phase labels shared
across trajectories: environment verification, dependency installation,
inspection/debugging, patching, and verification. This initially made the
already-held CodeTraceBench corpus the strongest candidate for literal phase
accuracy.

The current official release does not expose those labels. Its `stages` schema
contains only `stage_id`, `start_step_id`, and `end_step_id`; all 1,000 verified
rows number their spans exactly `1..k`, no row repeats an ID, and trajectories
may contain up to 67 stages. The Hub tree and the 3,291 downloaded raw artifact
archives contain no separate phase-label mapping. The released IDs are
therefore trajectory-local span ordinals, not the five semantic phase names.

**Disposition:** do not admit a CodeTrace literal phase experiment from the
current release and do not manufacture pseudo-gold from stage order or command
text. Preserve the already-completed CodeTrace boundary/B-cubed result exactly
as partition evidence. Continue the same source screen over already-held
families, then official published alternatives if necessary. The complete
source record is
[`literature-20260716T010251-0700/source-screen.md`](literature-20260716T010251-0700/source-screen.md).

### Node 002 — Published Software-Engineering Action Gold Is Admitted

The official artifact for the ASE 2025 Distinguished Paper *Understanding
Software Engineering Agents: A Study of Thought-Action-Result Trajectories*
publishes one shared eight-class action taxonomy over 120 real repair and
issue-solving trajectories: 40 each from AutoCodeRover, OpenHands/CodeActAgent,
and RepairAgent. Its 2,737 publication-derived category rows are scorer-only,
while the same artifact separately publishes the corresponding thought/action
trace views. The source methodology maps known tools automatically and manually
resolves remaining actions; the experiment's operational definitions come from
the TraceView companion guide.

A direct iteration audit found visible trace content for all 120 trajectories
and 2,751 source iterations. The category files cover 2,737 of them (99.49%):
218/218 AutoCodeRover, 1,108/1,113 OpenHands, and 1,411/1,420 RepairAgent.
Every published category row maps to exactly one visible source iteration;
there are no duplicate or out-of-range gold IDs. The 14 visible but unlabeled
iterations remain outside accuracy scoring and enter only the reported
coverage denominator. No label is inferred for them.

All eight published categories occur: Explore 606, Locate 196, Search 364,
Reproduce 153, Generate Fix 883, Run tests 294, Refactor 23, and Explain 218.
The rare Refactor class makes operation-macro F1 the primary literal-label
metric; accuracy, per-class precision/recall/F1, confusion matrices,
per-agent macro-F1, exact output coverage, and repeated-output agreement are
secondary. Majority accuracy and macro-F1 are lower-bound controls, not
publication thresholds.

**Disposition:** admit this official artifact for one full RQ3 literal-action
experiment. The tested input will contain only the visible thought and action
for a source iteration plus the eight published label definitions. Category
CSV values remain scorer-only. This measures literal action identity and does
not replace the already-completed OSWorld/CodeTrace partition metrics or
change the paper's thesis, RQs, abstractions, contributions, or story.

### Node 003 — Complete Literal-Action Experiment And Independent Review

**Context and status.** This decisive RQ3 experiment completed on
2026-07-16 and passed fresh independent result review. Its child records are
the [approved plan](experiment-001/experiment-plan.md), [consolidated plan
review](experiment-001/plan-review.md), [real preflight](experiment-001/preflight-report.md),
[full result](experiment-001/result-report.md), and [independent result
review](experiment-001/result-review.md).

**Method and completion.** The fixed Qwen3.6-27B closed-taxonomy path read only
each current thought/action and the eight published action definitions. Both
complete repetitions classified all 2,737 published labels from all 120 ASE
trajectories. Each repetition produced 2,737 unique grammar-valid predictions;
all 5,474 requests succeeded on the first attempt. The category targets,
framework, trajectory, outcome, and class counts remained scorer-only. The 14
visible but unlabeled iterations were not guessed and affect only the reported
99.49% source coverage.

**Results.** The fixed tagger reaches macro-F1 `0.498425` and accuracy
`0.627695`, versus `0.060981` and `0.322616` for the fixed majority control.
The primary macro-F1 difference is `+0.437444`; a 10,000-replicate bootstrap
that resamples whole trajectories within each framework gives a 95% interval
of `[+0.380168, +0.494079]`. The two prediction vectors agree on every row.
The major boundaries are Explore versus Locate, Run tests versus Reproduce,
and OpenHands, whose framework macro-F1 is `0.399871`; the result therefore
supports the aggregate literal-action hypothesis without authorizing uniform
accuracy, phase accuracy, open-set transfer, tagger SOTA, or every backend.

**Raw evidence and review.** The orchestrator rechecked the six recorded
SHA-256 values, both 2,737-line prediction files, scorer population, point
metrics, bootstrap interval, stability, and untouched submodule. The fresh
reviewer independently reconstructed the population and all metrics before
opening the stored score or result report and found zero result-invalidating
must-fix items. Its two documentation findings were resolved by removing the
overstrong claim that output received no post-inference normalization and by
recording the exact full-run and scoring commands. No rerun, prompt change,
metric change, or additional checker was needed.

The fresh outer audit then found a non-invalidating input exposure missed by
the first review: 39 AutoCodeRover action fields are exactly the gold literal
`Locate`. Excluding them from the durable predictions leaves 2,698 rows and
macro-F1 `0.490445` versus majority `0.061645`; no inference rerun is needed.
The result is therefore recorded as a standalone named-backend measurement,
not blanket semantic target separation or an integrated AgentProf CLI feature.

**Scientific impact and transition.** The run is valid, the tested hypothesis
is supported, its research value is decisive for the previously missing
literal-action cell, and its paper impact is additional RQ3 evidence. It does
not answer all of RQ3 or change the exact thesis, four RQs, two abstractions,
three contributions, submodule story, recurrence constructor, or another RQ.
The EXPERIMENT gate therefore exits to a targeted WRITE gate that may update
only RQ3 implementation/evaluation facts, the local scope/limitations sentence,
the verified citation, and canonical evidence memory.

## WRITE_GATE

### Gate Entry And Permitted Scope

The root reread `docs/user-instruction.md`, the complete `docs/idea-story.md`,
and `docs/questions-for-author.md` at entry. The write is a
`BUILD_AND_EVALUATE` targeted pass, not a full writing or idea-refinement pass.
It may add the reviewed action-label evidence and remove the now-stale statement
that action identity lacks direct evidence. It may not edit the title,
abstract, introduction, motivation, central insight, contributions, section
structure, related-work position, conclusion, exact four RQs, or the read-only
paper submodule. The paper will retain the result's material class/framework
boundary in the internal result report without importing negative development
details into the reader narrative.

### Node 004 — Targeted RQ3 Paper And Memory Sync

**Context and status.** The targeted pass completed at
2026-07-16T16:12:12-07:00. It changed only the active paper's RQ3 scope,
literal-action result paragraph, local limitations sentence, one verified ASE
source plus its TraceView companion citation, the paper workspace build status,
and the current RQ3 evidence/search frontiers in `docs/evaluation.md` and
`docs/background-related-work.md`.

**Paper result.** The reader-facing RQ3 section now reports the complete
2,737-label/120-trajectory population, macro-F1 `0.498`, accuracy `0.628`,
majority `0.061/0.323`, macro-F1 effect `+0.437` with whole-trajectory 95%
interval `[+0.380,+0.494]`, and exact two-run agreement. It replaces only the
stale statement that literal action identity had no direct evidence. The
reader-facing negative class/framework sentence identified by the outer audit
was removed under the user's explicit paper-story instruction; the internal
result report retains the complete error analysis. Literal phase labels and
unknown label sets remain explicitly outside the result. The paper does not
claim tagger SOTA, uniform accuracy, open-set transfer, phase accuracy,
all-backend validity, or a complete answer to RQ3.

**Citation and source fidelity.** The new bibliography entry identifies Islem
Bouzenia and Michael Pradel's ASE 2025 paper, pages 2846--2857 and DOI
`10.1109/ASE63991.2025.00234`. The official ASE program confirms the authors,
track, award, and preprint; the official paper and artifact supply the released
population and targets. A separate verified TraceView citation attributes the
companion operational definitions. No pseudo-label or unpublished CodeTrace
phase name entered the paper.

**Verification.** `make -B` rebuilt the active paper after BibTeX and two final
LaTeX passes with no undefined citation, LaTeX error, or overfull box. The PDF
has nine US-letter pages; all main content ends on page seven, References begin
at the bottom of page seven, and pages eight and nine contain references only.
Every embedded font is Type 1. The source remains anonymous. The diff touches
no abstract, introduction, motivation, design, implementation, title,
contribution, section structure, conclusion, or submodule line. The read-only
submodule remains clean at
`7f80c433c9555317a2aa45a78d0ff93518f4c12c`.

**Scientific impact and transition.** This WRITE expresses reviewed evidence;
it creates no scientific-contract or mechanism change. The exact thesis,
original submodule story, four RQs, operations and operation stacks, three
contributions, recurrence constructor, and existing RQ1/RQ2/RQ4 answers remain
unchanged. Canonical memory now records Step 0032 as decisive additional RQ3
action evidence and retains literal phase identity as the remaining declared
cell. WRITE exits to REVIEW for the single fresh outer audit and meta-review.

## REVIEW_GATE

### Gate Entry And Contract-Unchanged Audit

The root reread `docs/user-instruction.md`, the complete `docs/idea-story.md`,
`docs/questions-for-author.md`, this step report, the five experiment child
reports, raw result summary, targeted paper diff, canonical frontiers, and build
evidence. No paper-story or idea change occurred, so BUILD_AND_EVALUATE records
a scientific-contract-unchanged audit rather than an idea disposition. The
fresh reviewer must audit EXPERIMENT and WRITE together, explicitly conclude
Direction, Efficiency, and Maintenance, and route the remaining fixed-RQ
frontier without demanding another constructor tweak, another benchmark for
activity volume, or a story change.

### Node 005 — Fresh Outer Audit, Targeted Repair, And PASS

**Initial audit.** The fresh independent outer reviewer audited EXPERIMENT and
WRITE together and found the experiment valid, complete, and appropriately
bounded. It found no thesis, four-RQ, two-abstraction, three-contribution,
submodule-story, or AAAI-format drift. It nevertheless failed the first WRITE
because the reader paragraph foregrounded negative class/framework results,
the source provenance did not distinguish automatic tool mappings from manual
resolution, the TraceView origin of the operational definitions was not
explicit, the standalone adapter could be mistaken for a current CLI feature,
and 39 visible `Action: Locate` rows had escaped the first source audit. The
complete report is
[`outer-audit-20260716T162748-0700.md`](outer-audit-20260716T162748-0700.md).

**Targeted repair.** The root removed only the reader-facing negative sentence,
retained the full error analysis internally, corrected ASE/TraceView provenance,
described the action result as a standalone named-backend measurement, and
recomputed a sensitivity result over the 2,698 rows excluding the exact-label
exposure. Macro-F1 remains `0.490445` versus majority `0.061645`; inference,
prompt, taxonomy, primary full-population result, RQ, and story did not change.
The repository research instructions now require exact target-label scans for
future literal-taxonomy experiments. This is a learned source-fidelity rule,
not a new skill or audit framework.

**Follow-up verdict.** The same reviewer inspected only the requested repairs
and returned **PASS with no remaining must-fix**. The follow-up is
[`outer-audit-follow-up-20260716T163735-0700.md`](outer-audit-follow-up-20260716T163735-0700.md).

**Direction.** Step 0032 materially strengthens the fixed RQ3 answer with a
complete public literal-action measurement while preserving the larger
AgentProf thesis and story. It is additional component evidence, not a new
contribution or automatic authority to open another taxonomy experiment.

**Efficiency.** The source screen rejected unavailable CodeTrace phase gold
before execution, the admitted experiment used the full released population,
and the sensitivity repair reused durable predictions. No model sweep,
additional run, new benchmark, or checker was added.

**Maintenance.** Canonical evaluation, related-work, implementation, idea
history, paper workspace status, source screen, result report, and repository
instruction are synchronized. The absent `scripts/check_progress.py` diagnostic
remains nonblocking and no replacement audit infrastructure was created.

**Final route.** Step 0032 closes as complete. The outer state returns to
`BUILD_AND_EVALUATE / EXPERIMENT_GATE`, which must choose the next
highest-paper-value uncertainty from the complete paper. Literal phase identity
remains an evidence gap but is not automatically selected; no pseudo-gold is
permitted if no admissible public source exists.
