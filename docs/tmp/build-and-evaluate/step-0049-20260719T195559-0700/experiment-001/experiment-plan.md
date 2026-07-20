# Experiment Plan — Multi-Resolution Recurrence on Existing Trajectories

**Proposed:** 2026-07-19T19:55:59-07:00  
**State:** Proposed; implementation and candidate scoring are prohibited until
independent plan review approves this file  
**Paper RQ:** **RQ3 — How accurate are the tags?**  
**Scientific role:** post-hoc algorithm improvement on already-completed real
trajectories; not untouched confirmation of the whole RQ

## Fixed Scientific Contract

The exact thesis remains **“Agent observability needs profiling, not only
debugging.”** Attribution, localization, tag accuracy, and cost remain the
exact four RQs. The original AgentProf abstract, introduction, motivation,
system story, and positive RQ3 hypothesis are fixed. This experiment may change
only the operation-stack induction mechanism and the evidence directly owned by
that mechanism. It may not change, narrow, replace, or reinterpret the thesis,
RQ3, any other RQ, or the paper contribution.

## One Tested Hypothesis

> On the complete existing CodeTraceBench population, a recurrence constructor
> that treats either recurrent coarse action transitions or recurrent
> source-visible action-detail transitions as evidence of continuity improves
> standard ordinary per-operation B-cubed F1 over the current coarse-action-only
> constructor; on inputs without non-redundant action detail, it exactly falls
> back to the current result.

The experiment tests this one mechanism hypothesis. It does not answer all of
RQ3 and cannot revise the paper-level hypothesis from its outcome.

## Why This Experiment Is Admitted

The current constructor learns NPMI for adjacent coarse actions such as
`inspect`, `search`, and `test`. Retained complete-result analysis found that
ordered coarse action-pair identity has mixed official boundary labels for
99.7% of CodeTraceBench decisions. This is observational aliasing: `inspect`
can represent source-visible commands such as `ls`, `cat`, `sed`, or `read`,
while `test` can represent `pytest`, `cargo`, or another real command. Another
cutoff, support bucket, local window, or score combination cannot distinguish
those occurrences because each still sees the same coarse pair.

The already-produced CodeTraceBench operation records also retain
`raw_action_key`, a deterministic source-visible command/tool key extracted
before stage labels are loaded. It is not an oracle, target, stage, benchmark
identity, or learned label. It is already used by the matched raw-action
baseline and therefore introduces no new collection, model, benchmark, or
human annotation. The complete reference contains repeated concrete keys at
sufficient scale, while target trajectories remain disjoint from the reference.

This is the genuinely new observable discriminator required by Step 0026. The
scientific principle is simple: a coarse category pools evidence and remains
robust under sparsity; a recurring concrete transition supplies more specific
positive continuity evidence when available. Event-abstraction work explicitly
identifies mismatched event granularity as a central problem and treats fine and
coarse activity views as different levels of the same event stream
(van Zelst et al., 2021, DOI `10.1007/s41066-020-00226-2`; Li et al., 2021,
DOI `10.1109/ICPM53251.2021.9576868`). The proposed rule is not claimed to be
their algorithm; these papers motivate the multi-resolution problem.

OSWorld-Human's retained public adapter has no non-redundant detail field:
`target` is nearly a deterministic relabeling of `action` (for example,
`click -> ui`, `type -> text`, and `press -> key`). It must not be passed off as
new evidence. OSWorld therefore provides an exact fallback check, not a second
detail-bearing performance test.

## The Single Algorithm Change

The release constructor and its current coarse recurrence model remain intact.
When every operation in the reference and target also carries a non-empty
`action_detail`, construct a second visible signature
`(action, action_detail)` and learn the same directed adjacent-transition NPMI
and the same deterministic occurrence-weighted two-means calibration at that
resolution. The current global/cross-action monotone cutoff rule is reused
unchanged at both resolutions.

For a target edge, define:

- `coarse_continuity`: the current coarse pair is seen and its NPMI is at least
  its current applied cutoff;
- `detail_continuity`: the detailed pair is seen and its NPMI is at least its
  applied cutoff;
- final `boundary = not (coarse_continuity or detail_continuity)`.

Equivalently, a current coarse boundary is removed only when a recurring
source-visible detailed transition supplies positive continuity evidence. An
unseen or unavailable detail pair supplies no evidence and therefore falls back
to the current coarse decision. Detail may never add a boundary. This yields
three label-independent properties that implementation and raw output must
make directly auditable:

1. without an eligible detail field, every decision, segment, motif, and mass
   value is exactly current;
2. with detail, every candidate boundary is also a current coarse boundary;
3. candidate mass equals input mass and each operation belongs to exactly one
   contiguous segment.

The motif name remains the run-length-compressed coarse action sequence so that
the visible hierarchy does not expose raw commands or create a second naming
scheme. `action_detail` influences only boundary evidence.

No threshold, interpolation weight, support minimum, window, benchmark rule,
model, embedding, field combination, phase label, oracle group, or new
algorithm name is introduced. The implementation may add only one optional
input field and a second instance of the existing recurrence computation.

## Existing Inputs and Isolation

### CodeTraceBench detail-bearing population

- Reuse the same target-disjoint reference: 2,229 sessions and 87,703
  operations selected from existing solved trajectories.
- Reuse all 405 existing source-valid failed targets, 20,866 operations,
  20,461 adjacent decisions, 2,948 official stages, 251 tasks, and four agent
  frameworks.
- Candidate input contains only unit weight, `session`, coarse `action_kind`
  as `action`, and existing `raw_action_key` as `action_detail`.
- The verified manifest and official stages remain scorer-only and load after
  all candidate decisions are materialized.
- No source download, trace rerun, target selection, parser change, or
  relabeling is permitted.

### OSWorld-Human fallback population

- Reuse all 287 sessions, 3,978 operations, 3,691 adjacent decisions, 2,042
  official human groups, and the same five session-disjoint folds.
- Pass only the current unit weight, `session`, and `action` input. Do not map
  redundant `target`, derived `phase`, repeat fields, or any human-group field
  to `action_detail`.
- The candidate must reproduce all current release decisions and standard
  metrics exactly. Any difference invalidates the implementation.

## Comparisons and Metrics

The main baseline is the release label-free coarse recurrence constructor from
Step 0024. Existing contiguous `raw_action_key_change`, `phase_change`,
`action_change`, always-boundary, and one-session partitions remain descriptive
controls; no new baseline family is added.

- **Primary paper metric:** ordinary unweighted per-operation B-cubed
  precision, recall, and F1 against complete official partitions, reported
  separately for CodeTraceBench and OSWorld-Human. B-cubed is the standard
  hard-partition metric already cited by the paper.
- **Uncertainty:** paired task-cluster bootstrap of the CodeTraceBench
  candidate-minus-current B-cubed F1 difference, using all 251 tasks and the
  already-used deterministic 10,000-resample protocol.
- **Mechanism diagnostics:** exact adjacent-boundary precision/recall/F1;
  current-relative removed and added boundaries; seen/unseen detailed pairs;
  coarse-versus-detail rescue counts; predicted group count; per-framework
  B-cubed; complete operation/decision coverage; reference-target disjointness;
  and mass conservation.
- Token-weighted B-cubed, inspection-budget cutoffs, fixed-reader scores, and
  custom nonstandard metrics are outside this experiment.

## Fixed Interpretation

- **Supported:** the complete CodeTraceBench ordinary B-cubed F1 point estimate
  is higher than current and the paired task-cluster bootstrap 95% interval for
  the delta is wholly positive; the OSWorld fallback is exactly identical; all
  validity properties pass.
- **Promising but not established:** the complete CodeTraceBench point estimate
  is higher but the interval includes zero, or the pooled gain is positive with
  materially heterogeneous framework effects. The result may be retained as
  exploratory evidence but does not replace the release algorithm in this
  step.
- **Contradicted:** the complete CodeTraceBench point estimate is not higher.
- **Invalid/incomplete:** input isolation, source identity, disjointness,
  fallback identity, boundary-subset behavior, coverage, execution, scorer
  separation, or conservation fails.

A supported result authorizes replacement of the release mechanism and a
bounded update of design, implementation, algorithm history, evaluation, and
the active paper. Every other valid outcome keeps the current release. No
outcome authorizes another candidate inside this experiment or any change to
the thesis, RQs, story, or positive paper-level hypothesis.

## Execution Sequence

1. Independent plan review must inspect the scientific mechanism, field
   provenance, leakage boundary, standard metric, complete populations,
   uncertainty unit, fixed interpretation, and scope.
2. After approval, minimally extend the existing Rust constructor and existing
   CodeTrace/OSWorld evaluation paths. Historical default behavior must remain
   unchanged when `action_detail` is absent.
3. Run formatting, focused Rust tests, current regression tests, Python syntax
   checks, release build, and one independent implementation audit.
4. Run REAL PREFLIGHT once on OSWorld fold 0 and one complete CodeTraceBench
   target. Preflight checks execution and isolation only; its metric cannot
   alter the rule.
5. With no post-preflight algorithm change, run all five OSWorld folds and all
   405 CodeTraceBench targets once.
6. Retain raw reference/target inputs, commands, stdout/stderr, profiles,
   boundary decisions, assignments, summaries, and task-bootstrap draws under
   `.agentsight/experiments/rq3-multiresolution-recurrence-v1/`.
7. A fresh read-only reviewer reconstructs every primary metric and validity
   property from retained raw output before the root decides adoption.

## Paper and Review Discipline

If and only if the result is supported, WRITE may update the directly owned
algorithm and result text. Before editing, the root must read the complete
`docs/idea-story.md` and preserve its original baseline. The active paper must
continue to state exactly four RQs and the fixed thesis. The read-only
`docs/agentpprof-paper/` submodule remains untouched.

After any authorized paper sync, the user-requested milestone REVIEW must use
at least two genuinely different model families, including Grok, to read the
entire paper, inspect the relevant evidence, search primary closest work, and
return independent full-paper verdicts. Review objections are recorded and
fixed only within the scientific contract; they cannot rewrite the story or
change an RQ.
