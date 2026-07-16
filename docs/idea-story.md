# AgentProf Idea Story

Read this file from the first line to the last before any idea-level decision
or paper-level story change. The Initial Narrative is the permanent baseline;
it must remain complete in this current file. The evolution entries record why
each accepted change occurred. The latest entry is not presumed better merely
because it is newer.

## Initial Narrative — Permanent Baseline

**Provenance.** This is the complete scientific narrative from which the
AgentProf project began, reconstructed from the untouched
`docs/agentpprof-paper/main.tex` baseline and the author's original intent. It
preserves the original idea, not every original empirical sentence. Claims
later shown invalid remain identified as original promises rather than current
evidence.

### Problem And Stakes

AI agents perform long, multi-step activities spanning prompts, model calls,
tools, processes, files, and networks. As teams accumulate many trajectories,
the important engineering questions become population-level questions:

- Which recurring kinds of work consume the token, time, or system budget?
- Where do failures and wasted effort concentrate across workflows?
- Which recurring behaviors are associated with unsafe system effects?
- What should a developer optimize, inspect, or constrain across many runs?

Per-run tracing and debugging explain what happened in one execution. They do
not by themselves provide the cross-run aggregation and attribution that
traditional profiling provides for software. The original problem statement
was therefore simple and consequential:

> **Agent observability needs profiling, not only debugging.**

### Challenged Belief

Traditional profilers attribute additive measures to stable code identities
and runtime call stacks. The original work challenged the belief that an
agent's emitted execution structure is sufficient as the only responsibility
hierarchy for questions about recurring work across heterogeneous runs.
Equivalent behavior may appear under different prompts, tools, sessions, or
runtime boundaries, while one execution tree can mix behavior with different
operational meaning.

The initial paper sometimes stated this too strongly as if agent traces had no
execution hierarchy. The durable challenge was not the absence or uselessness
of native trees. It was that execution occurrence and cross-run profiling
responsibility are different questions.

### Central Insight And Thesis

The fundamental profiling method can transfer from code to agent behavior:
record weighted activities and effects, then attribute the selected measure to
responsible recurring entities at the granularity needed by the question.
Agent trajectories should be treated as profiling samples from a population,
not only as isolated traces.

The original thesis was that a semantic profile can reorganize recorded
activity by reusable task, phase, action, execution, or effect meaning and thus
complement per-run tracing. It was intended to cover cost, regression, safety,
failure, and wasted-work questions rather than one narrow anomaly detector.

### Proposed Model And System

The original model intentionally contained two core abstractions:

1. **Operation:** a uniform, fielded observation of agent activity or effect
   with one or more additive measures.
2. **Operation stack:** an ordered, query-time path derived from operation
   fields and used to fold a selected measure into a hierarchical profile.

Changing selected fields and measures lets the same recorded operations be
viewed by task, phase, action, session, tool, system effect, token count, time,
or another declared dimension. Mappings, taggers, boundary methods, filters,
rankers, importers, pprof serialization, and flamegraph rendering are supporting
mechanisms rather than additional scientific contributions by default.

AgentProf was proposed as an offline profiler that ingests real agent histories
and AgentSight recordings, constructs operation stacks, folds additive
measures, and emits pprof-compatible, folded-stack, JSON, and visual outputs.

### Intended Contributions

The initial narrative promised three contributions:

1. identify the missing cross-run profiling problem in agent observability and
   introduce operations plus query-time operation stacks as a compact model;
2. implement the model in AgentProf with real trace ingestion and standard
   profiler outputs;
3. evaluate whether the profiles faithfully attribute recorded measures and
   help locate real cost, failure, safety, or wasted-work behavior across real
   trajectories and public benchmarks.

### Original Scope And Non-Claims

The ambition was broad across agents, tasks, and additive measures, but the
model was not meant to be a universal causal graph, complete execution ontology,
automatic failure detector, or replacement for per-run debugging. Profiling
and tracing were intended to be complementary. Semantic fields were hypotheses
about useful responsibility, not permission to manufacture signal absent from
the observations.

### Original Research Questions And Evaluation Promise

The first paper organized evaluation around four questions:

1. whether semantic profiling improves resource attribution;
2. whether profiler output corresponds to real annotated problems;
3. whether derived semantic tags agree with held-out annotations;
4. what profiling costs.

It promised real local trajectories, public annotated datasets, hidden-label
problem localization, mapping transfer, and end-to-end profiling cost. The
initial paper reported strong positive numbers. Later audits found that several
positive interpretations were circular, target-guided, incomplete, or broader
than the evidence. Those numbers are historical claims, not current evidence.
The problem, stakes, two-object model, and broad evaluation promise remain the
permanent baseline against which every later story is compared.

## Current Frontier

### Restored Position

Agent traces record where activity occurred in individual runs. Agent profiling
asks which recurring behavior across many runs accounts for a measured cost,
regression, unsafe effect, failure, or wasted effort. AgentProf treats
trajectories as profiling samples and makes the attribution hierarchy explicit
through operations and operation stacks.

> **Agent observability needs profiling, not only debugging.**

This sentence is the paper-level thesis and must remain exactly the same as the
untouched submodule baseline. Cross-run recurring behavior and measured effects
explain why profiling is needed and how it is evaluated; they are not a narrower
replacement thesis. An execution or semantic hierarchy has no automatic
authority inside that profiling method, so the hierarchy used to attribute a
measure must be exposed and tested against the analyst's decision.

This restores the original consequential problem. Hierarchy and representation
choice are load-bearing parts of the model and evaluation, not the paper-level
thesis by themselves.

### Scientific Model

The two original abstractions remain the complete core model:

1. an **operation** is a weighted, fielded observation;
2. an **operation stack** is a query-time path used to aggregate a selected
   measure.

Flat summaries, genuine source-native paths, and semantic stacks are competing
projections over the same evidence. Mappings, tags, rankers, importers,
differential comparison, pprof output, and visualizations remain supporting
mechanisms.

### Positive Research Program

AgentProf transfers the profiling method from code execution to agent behavior:
it treats real trajectories as samples, records additive activity and effects as
operations, folds recurring responsibility through operation stacks, and uses
the resulting profile to decide what to optimize, inspect, or constrain.

The Rust artifact already implements operation ingestion, derived fields,
predicates, configurable stacks, weighted folding, multiple views, and standard
profile outputs. Existing real traces establish that the model can represent and
conserve measured activity. The open task is to complete strong positive,
independently grounded evidence for the four fixed questions below.

### Fixed Research Questions And Hypotheses

The paper keeps exactly four explicit RQs:

1. **RQ1 — Does Semantic Profiling Improve Resource Attribution?** Semantic
   operation stacks should reunite recurring responsibility fragmented across
   executions and improve attribution of independently recorded token, time,
   tool, process, file, network, or other additive measures while preserving
   source lineage and mass.
2. **RQ2 — Does Profiler Output Correspond to Real Problems?** A fixed semantic
   profile should concentrate independently annotated failures, unsafe effects,
   redundant work, or task boundaries and reduce inspection versus flat,
   per-session, native, and raw-action views without using target labels.
3. **RQ3 — How Accurate Are the Tags?** A target-blind fixed tagger or mapping
   should assign accurate, stable task/phase/action identities and boundaries on
   unseen agents and task families without materially corrupting attribution.
4. **RQ4 — What Is the Profiling Cost?** Complete profile construction should
   have practical predictable scaling, while cached field derivation makes
   repeated profile queries substantially cheaper than initial construction and
   repeated raw-trace review.

These hypotheses remain fixed unless an explicit later user instruction changes
them. Experiments may improve the mechanism, signal, workload, protocol, or
implementation; a current failure does not authorize rewriting the RQ or
weakening its hypothesis.

### Research-History Boundary

Failed induced-leaf and recursive-adapter studies remain linked in
`docs/evaluation.md` and timestamped result reports. They prevent reuse of those
unchanged mechanisms as positive evidence and teach that grouping needs a real
visible signal and that recursion alone is insufficient. They are development
history, not the current paper's result story and not a thesis challenge.

The final paper reports only results from materially improved methods and
complete experiments that answer the four fixed RQs. During the current
restoration, the original positive empirical sentences remain in the canonical
paper as the intended claim surface; their presence is not an internal
authorization verdict. Experiment records identify which numbers are verified,
superseded, or still require reruns. WRITE replaces a number only with complete
positive evidence for the same RQ and hypothesis, rather than turning local
negative development results into the paper's story.

### Competing Explanations

1. Recurring semantic responsibility is the useful cross-run index for some
   measured changes.
2. Any apparent gain comes from extra visible fields or a stronger ranker.
3. Arbitrary or simple grouping supplies the same benefit.
4. Native execution hierarchy is sufficient for the relevant decisions.
5. Different signal shapes and decisions favor different projections.

Step 0006 supports the boundary part of the fixed RQ3 hypothesis: a fixed
target-blind boundary tagger recovers independently annotated human
action-group boundaries on held-out sessions and preserves the corresponding
group partition better than simple visible-field rules. Step 0007 now supports
the load-bearing RQ1 integration edge: the complete fixed R114 suite attributes
1,520 scoped real-Codex effects at 100.000% precision and 96.569% recall,
rejects all 1,629 concurrent-control effects, and current AgentProf preserves
every selected row and the mass of all five known task categories.

Step 0017 tests the current built-in target-blind Rust operation-stack inducer
instead of conflating it with the separate supervised boundary predictor. The
single-objective information-gain revision substantially improves the old Rust
heuristic, but at fixed depth four it remains below the strongest simple
controls. This is a contradicted mechanism hypothesis within RQ3, not a reason
to narrow RQ3, replace the thesis, or change the paper story. The exact
algorithm, properties, complete OSWorld-Human result, and evidence boundary are
recorded in Step 0017's `algorithm-note.md` and result reports.

Step 0018 removes only the arbitrary depth-four cap from that same algorithm.
On the complete post-hoc population, intrinsic stopping reaches depth 26 and
improves boundary F1 from 0.4231 to 0.4720 and B-cubed F1 from 0.6165 to
0.6720. The result remains below the strongest simple controls and therefore
contradicts the registered sufficient-explanation hypothesis. It establishes a
better implementation configuration and a mechanism boundary, not a smaller
RQ3, a new thesis, or a reason to replace the original story.

Step 0020 follows the user's explicit instruction to improve the mechanism on
those same completed trajectories rather than switch benchmarks. Diagnosis
showed that recursive information gain rewards categorical purity even though a
human operation commonly contains a heterogeneous action motif. The replacement
uses one paper-aligned principle: adjacent actions that recur together across
other sessions continue the same operation, while weak or unseen transitions
start a new one. Coherent transition-space NPMI and deterministic weighted
two-means implement that principle without a label-tuned cutoff. On the fixed
post-hoc population it reaches boundary F1 0.6799 and B-cubed F1 0.7862, above
the registered strongest simple controls, and the release Rust port exactly
matches every evaluated boundary, motif, segment, and conserved unit. This is a
mechanism/frontier update on already observed labels, not a new narrative,
thesis, contribution, RQ, or untouched cross-family confirmation.

Step 0024 completes that implementation branch without changing the principle
or story. It constrains action-changing decisions to the smaller of the global
and cross-action recurrence cutoffs, so the refinement can recover continuity
but cannot add a global-rule boundary. On the two already-complete development
populations, it leaves every OSWorld-Human decision and the 0.7862 B-cubed F1
unchanged, while raising CodeTraceBench B-cubed F1 from 0.4750 to 0.6492 across
all four frameworks. The fixed equal-plus-higher rule supports adoption as the
release constructor. This is a mechanism/frontier update on reused evidence,
not a new narrative, thesis, contribution, RQ, or untouched confirmation.

Step 0025 records one direct user-requested attempt to improve that same
algorithm on the same completed trajectories. A sequence-local raw-NPMI
minimum rule improves CodeTraceBench B-cubed F1 in all four frameworks but
reduces OSWorld-Human B-cubed F1 and boundary F1 on both populations. The fixed
cross-population decision therefore rejects it and restores Step 0024 exactly.
This is a rejected mechanism refinement in the evidence history; it is not an
accepted narrative change, a smaller hypothesis, or a reason to alter the
thesis, four RQs, contributions, or original AgentProf story.

Step 0026 asks whether that mixed result exposes another common correction on
the same trajectories. It does not: identical action pairs and small action
windows remain label-ambiguous, while suppression, score, support, cutoff sign,
and session length have opposed or population-confounded effects. Independent
review therefore admits no further flat-segmentation tweak and keeps Step 0024
as the release. This closes an implementation-selection branch; it does not
change the narrative or claim that all future sequence models are impossible.

Step 0019 tests a different consequence inside unchanged RQ2. A fixed
rank-hidden Qwen3.6-27B reader selects three of each view's query-aware top five
groups across six public-data tasks and all five cyclic positions. The complete
66-presentation result improves selected-positive recall on 5/6 tasks and
precision on 4/6 relative to fixed-session packets under the predeclared rule.
This is supporting group-prioritization evidence; higher work on 4/6 tasks and
the absence of a matched raw-action packet prevent lower-work, human, or
universal-view promotion. It strengthens the original positive program without
changing the thesis, RQs, contributions, or two-object model.

### Next Decisive Evidence

The user has restored the untouched submodule as the canonical story source.
RQ1 has strong scoped source-lineage and lossless-folding evidence, RQ4 has a
complete positive construction-cost answer, and Steps 0006/0008 supply positive
boundary/task-partition evidence within RQ3. Steps 0020--0024 close the bounded
recurrence implementation investigation by replacing the mismatched
information-gain objective, isolating its calibration failure on existing
CodeTraceBench trajectories, and adopting the monotone cross-action rule. The
final constructor preserves the complete OSWorld result and improves the
complete CodeTraceBench partition result without adding a current-relative
boundary. The result remains post-hoc implementation selection rather than
independent confirmation. No further OSWorld-Human or CodeTraceBench depth,
field, penalty, threshold, or score-term search is admitted.

The Step 0018 whole-paper review preserved the thesis and four RQs but disputed
the current cumulative positive RQ2 authorization because its three workload
outcomes used different metrics/points and did not isolate downstream decision
value. Step 0019 has now completed the selected fixed-reader comparison and
adds the bounded downstream evidence above. The targeted WRITE sync for the
adopted recurrence implementation is complete. The independent whole-paper
re-review and outer audit both PASS and do not find broader automatic identity
fidelity evidence load-bearing. Step 0025's one user-requested local refinement
is mixed and rejected, and Step 0026 finds no common small correction in those
same action-only decisions. Step 0024 remains the current constructor. This is
an evidence-frontier update, not a narrative evolution or change to the thesis,
four RQs, or two-object model.

Steps 0031--0032 add standalone named-backend measurements for declared task
families and action labels without changing the constructor or story. Step 0032
scores all 2,737 publication-derived ASE action labels and retains a positive
macro-F1 effect after excluding 39 rows whose visible action is exactly the gold
literal `Locate`. The ASE labels combine automatic known-tool mappings with
manual resolution of remaining actions; the prompt's operational definitions
come from the TraceView companion guide. This is additional RQ3 evidence, not
an integrated AgentProf CLI feature, literal phase evidence, a new abstraction,
or a narrative evolution. The next experiment is selected for paper-level
value; it is not automatically another taxonomy cell.

## Narrative Evolution — Accepted Changes Only

### E000 — Initial profiling narrative

**Before/after:** project inception; the complete baseline above was the
starting narrative.  
**Reason:** cross-run agent development raised cost, failure, safety, and wasted
work questions that per-run debugging did not aggregate.  
**Root disposition:** accepted as the project objective and two-object system
direction.  
**Comparison:** no prior narrative; it defines the permanent baseline.  
**Revisit:** never remove the baseline; only evidence and current conclusions
may evolve.

### E001 — Evidence-fidelity correction

**Before:** semantic separation, hidden-annotation ranking, mapping agreement,
and offline timing were presented as broad proof that AgentProf improved
attribution and diagnosis.  
**After:** conservation, declared-category separation, independent lineage,
diagnostic correspondence, causality, and end-to-end decision value became
distinct evidence levels; unsupported positive claims were withdrawn.  
**Reason/evidence:** source audits found prompt-derived or hidden-label
circularity, target-time tuning, weak native baselines, and incomplete cost and
lineage evidence.  
**Root disposition:** accept the evidence correction; reject shrinking the
underlying profiling problem.  
**Initial/previous/chosen comparison:** the initial story remained more
important and simpler, while the chosen version became scientifically honest;
the correction improved claim authorization without replacing the thesis.  
**Detail:** [trajectory audit and recovery plan](tmp/cycle-0001-20260711T164850-0700/03-review-gate/idea-regression-recovery-20260712T021723-0700/trajectory-audit-and-recovery-plan.md).  
**Revisit:** restore a positive result only through a clean real experiment.

### E002 — Revert reviewer-driven mechanism expansion

**Before:** repeated reviewer attacks had promoted stable identity, semantic
scope trees, navigators, bundle emulation, cost contracts, and large comparator
programs over the original operation/operation-stack center.  
**After:** the accepted story returned to operations and operation stacks as the
only core abstractions; the added mechanisms were demoted to optional techniques
unless later implementation and evidence justified one independently.  
**Reason/evidence:** each objection was treated as a mechanism obligation rather
than classified as a fatal defect, evidence need, optional control, alternative,
or future work.  
**Root disposition:** reject the expanded mechanism-centered narrative and
accept the reversion; retain only independently implemented or experimentally
necessary pieces as supporting techniques.  
**Initial/previous/chosen comparison:** the initial narrative had the clearer
two-object center; the immediately previous expanded version was more defensive
but less simple, less implemented, and less faithful; the chosen reversion was
therefore stronger than the previous version and restored the initial strength
without restoring unsupported empirical claims.  
**Detail:** [trajectory audit and recovery plan](tmp/cycle-0001-20260711T164850-0700/03-review-gate/idea-regression-recovery-20260712T021723-0700/trajectory-audit-and-recovery-plan.md).  
**Revisit:** only if a decisive experiment requires one mechanism and the
artifact plus evidence justify it independently.

### E003 — Representation-choice narrative after valid negative results

**Before:** the restored center was cross-run semantic profiling as a complement
to tracing.  
**After:** the paper increasingly centered on flat, native, and recursive
hierarchies as competing profiling indices and on the absence of automatic
hierarchy authority.  
**Reason/evidence:** AgentRx/TELBench and Hodoscope contradicted expected
semantic-leaf and recursive advantages; the project correctly preserved native
baselines and separated signal from grouping.  
**Root disposition at the time:** accept hierarchy choice and signal shape as
important scientific boundaries.  
**Initial/previous/chosen comparison:** this version improved fairness,
closest-work honesty, and negative-result interpretation, but lost the initial
problem's scale by making a supporting comparison the headline. It is retained
as the immediately previous narrative, not the current thesis.  
**Detail:** [post-result full-paper review](tmp/cycle-0001-20260711T164850-0700/03-review-gate/post-result-full-paper-review-20260712T054200-0700.md).  
**Revisit:** representation sensitivity may become central only after repeated
complete matched experiments directly challenge the profiling thesis or show
no useful regime.

### E004 — Restore profiling as the paper-level thesis

**Before:** representation/hierarchy choice occupied the center; the original
profiling problem was present but subordinate.  
**After:** agent observability again needs profiling across recurring behavior
and measured effects, while hierarchy choice remains a falsifiable property of
that profiling model. All valid negative evidence and novelty limits remain.  
**Reason/evidence:** the user's explicit correction and three independent
read-only idea discussions found that local method/workload negatives were not
direct thesis challenges and that the submodule's problem framing had greater
scientific potential.  
**Root disposition:** accept the combined restoration; reject restoring
unsupported old results; defer paper changes to WRITE.  
**Initial/previous/chosen comparison:** the initial story supplies importance,
simplicity, and ambition; the previous story supplies scientific discipline;
the chosen story combines both and is therefore stronger and more faithful than
either alone.  
**Idea audit:** [root disposition](tmp/cycle-0001-20260711T164850-0700/03-review-gate/idea-story-restoration-20260712T134029-0700/500-idea-audit-20260712T140000-0700.md).  
**Revisit:** only a direct thesis challenge—not one local negative result,
reviewer objection, or unavailable dataset—can reopen the paper-level center.

### E005 — Restore the exact original thesis sentence

**Before:** the restored thesis was paraphrased as a need for cross-run
profiling of recurring behavior and measured effects rather than tracing
individual executions.  
**After:** the paper-level thesis is exactly **“Agent observability needs
profiling, not only debugging.”** Cross-run recurrence, measures, tracing, and
hierarchy validation are motivation, mechanism, or evaluation detail.  
**Reason/evidence:** the user explicitly required the current thesis to match
the untouched submodule rather than the narrower paraphrase. The complete
Initial Narrative confirms that the original sentence carries the broader
quality, safety, cost, failure, and long-running-agent ambition.  
**Root disposition:** accept the direct correction immediately; do not ask a
writing round or local experimental result to reinterpret it.  
**Initial/previous/chosen comparison:** the initial sentence is simpler and
broader than the immediately previous paraphrase. The paraphrase usefully
explained the experimental setting but incorrectly promoted those details into
the thesis. The chosen exact sentence is therefore both more faithful and more
ambitious.  
**Idea audit:** [direct user thesis correction](tmp/cycle-0001-20260711T164850-0700/03-review-gate/direct-user-thesis-correction-20260712T141306-0700/500-root-disposition.md).  
**Revisit:** change this exact thesis only when a later explicit user
instruction establishes a different thesis. A direct scientific challenge
reopens evidence collection and idea discussion but does not itself authorize
replacement.

### E006 — Restore four fixed RQs and the positive paper program

**Before:** the paper retained the exact thesis but organized Evaluation around
three replacement RQs—fidelity/comparability, analytical value, and
generality/limits—folded cost into RQ2, removed tag accuracy as an independent
question, and foregrounded failed intermediate mechanisms.  
**After:** the current frontier and following WRITE gate restore exactly four
RQs—resource attribution, real-problem localization, tag accuracy, and profiling
cost—with a positive falsifiable hypothesis for each. Failed intermediate
experiments remain auditable research history but no longer define the final
paper story. Experiment and mechanism design change before a viable hypothesis
or claim changes.  
**Reason/evidence:** the user explicitly fixed the four RQs, required a stronger
and more attractive story, excluded negative intermediate results from the
paper, and prohibited weakening a viable hypothesis because a current experiment
failed. Three fresh read-only discussions independently found that the original
four-RQ architecture is the strongest academic structure and that later controls
should discipline experiments rather than become the contribution.  
**Root disposition:** accept the four-RQ restoration and positive program;
reject the three-RQ/negative-story organization; defer all paper edits to WRITE.  
**Initial/previous/chosen comparison:** the Initial Narrative remains strongest
in importance, simplicity, and the complete attribution-localization-tag-cost
chain; the immediately previous version remains strongest in experimental
discipline but is smaller and less attractive; the chosen direction combines the
initial architecture with later controls and is therefore stronger and more
faithful than both.  
**Idea audit:** [root disposition](tmp/cycle-0001-20260711T164850-0700/03-review-gate/user-rq-restoration-20260712T171629-0700/500-root-disposition-20260712T173400-0700.md).  
**Revisit:** only a later explicit user instruction may change the four RQs. A
direct experimental challenge changes the mechanism and evidence branch first;
it never silently authorizes a smaller question set.

### E007 — Restore the submodule as the canonical story source

**Before:** the post-E006 paper kept the exact thesis, two abstractions, and four
RQ headings, but its abstract, introduction, background, design, discussion,
and RQ2 program had been rebuilt around responsibility hierarchies, matched
projections, and a profile-to-intervention rerun. This was a different story
despite preserving the headline identifiers.  
**After:** the untouched submodule again supplies the complete scientific
spine: long-running agents create quality, safety, and cost questions across
many trajectories; tracing/debugging is per execution whereas profiling
aggregates responsible entities; semantic operations and operation stacks
adapt profiling to agents; AgentProf implements the model; and the four RQs are
resource attribution, real-problem localization, tag accuracy, and profiling
cost. Evidence controls remain in Evaluation and history rather than becoming
the paper's center.  
**Reason/evidence:** the user explicitly judged the submodule story better,
ordered direct restoration, prohibited arbitrary story changes, and specified
that the abstract, introduction, system design, background, and motivation all
start from the submodule. Execution-history audit showed that the root had
accepted reviewer-driven reframings and then rebuilt these sections during
WRITE without authorization to replace the story.  
**Root disposition:** accept direct restoration; cancel further story invention;
retain the AAAI format and verified evidence, but do not mechanically restore
unsupported historical result numbers.  
**Initial/previous/chosen comparison:** the Initial Narrative and submodule are
simpler, more consequential, and more memorable; the immediately previous
version improved evidence discipline but promoted experiment controls into the
scientific narrative. The chosen version restores the original story and keeps
only the later evidence discipline, making it both stronger and more faithful.  
**Idea audit:** [direct user disposition](tmp/cycle-0001-20260711T164850-0700/03-review-gate/idea-discussions-20260712T193851-0700/100-direct-user-disposition.md).  
**Revisit:** the submodule story remains the project-level baseline until a
later explicit user instruction changes it. Reviewer objections, venue advice,
local negative results, and writing improvements cannot replace it.

### E008 — Materialize the canonical paper in the AAAI workspace

**Before:** `docs/agentpprof-paper/main.tex` was declared authoritative, but
`docs/paper/main.tex` still contained the shorter reviewer-driven rewrite. The
two files differed across 1,142 lines, so the repository's active paper did not
actually implement E007.
**After:** the complete submodule scientific body—from abstract through
conclusion—and its bibliography and figures now occupy `docs/paper/`. The only
changes are the official AAAI-27 anonymous-submission wrapper, author
anonymization, bibliography invocation, and a no-op compatibility definition
for ACM's accessibility-description command. The prior active draft is
archived under
`docs/tmp/agentpprof-paper-pre-canonical-restore-20260713T023645-0700/`.
**Reason/evidence:** the user identified the attached/submodule LaTeX as the
exact desired version after a normalized byte comparison proved they were
identical, then reaffirmed that this version is the authority. A mechanical
content comparison now proves the active scientific body is exact.
**Root disposition:** accept the material restoration; preserve every original
story section and four RQs; treat original numerical sentences as positive
targets that still require complete experimental authorization.
**Initial/previous/chosen comparison:** the chosen paper is the Initial
Narrative itself, not a new story. The superseded active draft remains useful
for possible citations and formatting but is smaller and unauthorized as a
replacement narrative.
**Detail:** [pre-restoration archive and provenance report](tmp/agentpprof-paper-pre-canonical-restore-20260713T023645-0700/README.md).

**Subsequent enforcement.** Cycle 0002 writing later rewrote the restored body
while retaining its headline thesis and RQ names. The author rejected that
rewrite and identified the complete attached/submodule paper as the authority
again. The root archived the rewritten workspace under
[`docs/tmp/agentpprof-paper-pre-authoritative-rerestore-20260713T122602-0700/`](tmp/agentpprof-paper-pre-authoritative-rerestore-20260713T122602-0700/README.md)
and restored the already verified AAAI conversion from `eb5f332e`. A fresh
normalized comparison found zero differences between the restored scientific
body and `docs/agentpprof-paper/main.tex`. This is enforcement of E007/E008,
not a new narrative.

**Revisit:** future WRITE passes may improve expression and replace empirical
values with stronger complete evidence, but they must begin by comparing
against this exact restored body and may not silently reinvent the story.

## Invariants For Every Future Story Decision

- Read this entire file, including the Initial Narrative and every evolution
  entry, before deciding.
- Compare the initial, immediately previous, and proposed narratives explicitly;
  recency is not evidence.
- Preserve the largest faithful problem and use bold hypotheses with careful
  validation. Negative results change tested answers or search branches before
  they change the paper-level objective.
- Keep operations and operation stacks as the only core abstractions unless
  implementation and decisive evidence justify a genuine new abstraction.
- Treat `docs/agentpprof-paper/main.tex` as the read-only canonical AgentProf
  story source. A WRITE pass may update evidence and wording but may not replace
  its problem, gap, insight, system direction, contribution chain, or four-RQ
  meaning without a later explicit user instruction.
- Prefer one simple, non-obvious principle over stacked terminology.
- Use real papers, benchmarks, systems, datasets, and complete experiments.
- Record every accepted problem, thesis, contribution, system-direction, scope,
  or RQ change here with before/after meaning, reason, evidence, root
  disposition, comparison, report link, and revisit condition.
- `iter-refine-ideas` proposes; the root records a disposition; the WRITE gate
  alone changes the paper.
