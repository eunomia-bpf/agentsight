# Source-Grounded Full-Paper Assessment

**Timestamp:** 2026-07-23T20:50:54-07:00
**Parent:** Step 0073 / REVIEW Gate / milestone review 001
**Status:** complete

## Objective

Reread the complete paper after primary-source verification, then assess Step
0073's full result and independent reconstruction against the paper's exact
thesis, four RQs, strongest claims, and current closest work.

## Inputs and provenance

This phase read in full:

- the active paper and bibliography a second time;
- `docs/user-instruction.md`;
- `docs/idea-story.md`, including the permanent initial narrative and every
  accepted evolution entry;
- `docs/evaluation.md`;
- Step 0073 entry, closest-work audit, experiment plan, all four plan reviews,
  preflight, full-run report, independent result review, and WRITE report; and
- the primary sources listed in the preceding report.

No paper, code, memory file, skill, or Git state was changed.

## Method

The assessment separates four decisions that must not be conflated:

1. Was the Step 0073 experiment valid?
2. What did it say about the tested A2 hypothesis?
3. Did it challenge the thesis, RQ3, or only the current backend?
4. Was preserving the paper while updating research memory the right WRITE
   decision?

## Step 0073 result

The complete manifest-defined follow-on contains:

- 364 sessions;
- 15,116 operations;
- 14,752 adjacent pairs;
- 238 task clusters;
- four CodeTrace frameworks; and
- no overlap with the initial 41 long-horizon sessions.

The independent reviewer reconstructed the subset from full-population rows
without importing the new scorer and reproduced every aggregate,
per-framework, and bootstrap result.

| Method | B³ P | B³ R | B³ F1 | Boundary F1 |
|---|---:|---:|---:|---:|
| Automatic Agent A2 | .910237 | .535911 | .674628 | **.402802** |
| Multi-resolution recurrence | .758227 | .627664 | **.686795** | .289023 |
| Native source tree | .977391 | .269893 | .422985 | .285869 |
| Source-native turn | .993477 | .196407 | .327974 | .251788 |

The registered A2-minus-recurrence B³ point difference is `-.012167`; the
task-cluster 95% interval is `[-.027266,+.003221]`. The approved positive
hypothesis is therefore **INCONCLUSIVE**.

The mechanism diagnosis is well supported:

- A2 has higher exact boundary F1 in all four frameworks;
- A2 has much higher B³ precision but lower recall than recurrence;
- A2 predicts 5,198 occurrences for 2,382 official stages; and
- 1,623 A2 occurrences, 31.2%, are singletons.

A2 detects many true stage transitions but inserts enough extra transitions to
fragment the broader, shorter follow-on trajectories.

## Validity assessment

### Run validity — PASS

The population is complete and manifest-defined; the initial and follow-on sets
are disjoint and union to all 405 sessions; all candidate and comparison rows
share the same operations and references; the standard metrics are correctly
computed; uncertainty uses the declared task-cluster resampling unit; and
independent reconstruction agrees.

### Tested hypothesis — INCONCLUSIVE

The point estimate favors recurrence and the interval crosses zero. Higher
secondary boundary F1 cannot convert that result into support.

### Research value — HIGH SUPPORTING VALUE

The result identifies a concrete failure mode rather than merely producing a
null:

> the current A2 policy recognizes transitions but over-fragments shorter and
> differently composed sessions.

The initial 41-session subset has an independently reconstructed A2-minus-
recurrence B³ delta of `+.139563`, the follow-on has `-.012167`, and the union
has `+.041373`. The pooled positive result is selection-sensitive. The split
also changes length and framework mix, so it does not isolate one cause.

## Does this challenge the paper's story or RQ?

No.

The exact thesis is about the need for profiling in addition to debugging. It
does not assert that one Codex-worker policy must dominate recurrence on every
batch. RQ3 asks how accurately automatic backends recover operation structure;
an inconclusive fixed-backend comparison is an answer about that backend and
population, not authorization to replace or narrow RQ3.

The permanent idea story explicitly requires:

- the original thesis sentence;
- four fixed RQs;
- operations and operation stacks as the two scientific abstractions;
- bold hypotheses with careful validation; and
- a direct thesis challenge before any story rewrite.

Step 0073 supplies no direct thesis challenge. It does not show that profiling
is unnecessary, that recurring responsibility cannot be represented, that
source measures cannot be conserved, or that every automatic backend fails.

## Was preserving the paper correct?

**Yes, for this cycle's result integration.**

The current paper already states that CodeTraceBench is the complete
development population and limits claims to named populations/protocols. The
sentence “strongest tested automatic constructor on this complete population”
is factually true for the 405-session union. Replacing the headline with the
follow-on negative or rewriting the contribution around fragmentation would
violate the user's positive-paper and story-preservation instructions.

The WRITE gate correctly:

- left the thesis, RQs, paper story, and contribution chain unchanged;
- withheld the planned unsupported follow-on-positive sentence;
- recorded the complete boundary in `docs/evaluation.md`; and
- recorded in `docs/idea-story.md` why it does not change the story.

Two qualifications remain for a later WRITE pass:

1. if no stronger fixed backend resolves the sensitivity, the paper must avoid
   implying A2 generalization beyond the full observed development population;
2. ACT*ONOMY must enter Related Work because Step 0073's search discovered a
   directly relevant semantic-profile neighbor.

Neither qualification requires inserting a negative development subsection
now.

## Ranked whole-paper findings

### Major 1 — pooled RQ3 superiority is selection-sensitive

The .704 versus .663 result remains valid on all 405 observed trajectories, but
the follow-on shows that it is not uniformly stable. The next backend
experiment should directly target fragmentation rather than switch benchmark
or retune on stages.

### Major 2 — automatic annotation is absent from RQ4

The paper's 1.16-second result remains correct for fixed marks. It does not
establish the end-to-end cost of automatic semantic profiling. This is now an
explicit user-requested evidence need.

### Major 3 — ACT*ONOMY is absent from the paper

The paper cites strong adjacent systems but not the closest fixed-taxonomy
automatic behavioral-profile work. This is a Related Work must-fix before
submission, not a reason to replace the contribution.

### Major 4 — paper-level consequence remains weaker than closest work

RQ2 establishes useful profile/evidence refinement and the case studies show
real aggregate differences. The information-matched raw baseline remains
indistinguishable, while Hodoscope and TraceGraph demonstrate review-effort or
intervention consequences. This is a paper-readiness issue already identified
before Step 0073; the current cycle neither worsens nor solves it.

### Submission blocker — length

The active PDF is 12 pages and requires a later format-compliant WRITE pass.
This is independent of Step 0073's scientific validity.

## Systems-lens verdict

The source-tree/annotation/pprof pipeline is coherent; conservation and standard
output are credible; the figures answer real profiling questions. The main
systems weakness is that the measured cost begins after semantic construction,
and the main causal weakness is that RQ1 changes width on one repeated task
rather than benchmarking attribution decisions broadly.

## AI/ML-lens verdict

Step 0073 is a strong adaptive sensitivity analysis: complete population,
standard metrics, strongest runnable baseline, correct uncertainty unit,
independent recomputation, and honest scope. It exposes A2's precision/recall
tradeoff. It is not untouched cross-family confirmation, and the 405-session
headline should not be described as such.

## Cross-domain verdict

The paper's durable novelty is the conjunction of recursive responsibility,
conserved additive measures, source evidence, and standard profiles. Neither
pprof output nor semantic hierarchy is independently new. The follow-on result
does not remove that conjunction; it shows the current automatic constructor
needs a better stopping/splitting policy.

## Single next experiment

Route to **EXPERIMENT / RQ3** for one complete run of the already-fixed
source-only recursive backend.

The tested hypothesis should be:

> Interval-wide recursive split/stop decisions reduce A2's observed
> fragmentation and improve ordinary B³ F1 over multi-resolution recurrence on
> the complete fixed population, without reading official stages.

The experiment should:

- keep the backend binary/model/prompt and source-only inputs fixed;
- use the complete population once;
- retain recurrence, native tree, and native turn as the minimal comparisons;
- keep ordinary B³ F1 primary and exact boundary F1 secondary;
- report B³ precision/recall, group count, and singleton fraction to diagnose
  fragmentation; and
- record wall time, model calls, and input/output tokens during this run for
  the subsequent RQ4 cost experiment, without allowing cost to change the RQ3
  verdict.

Do not introduce stage-driven contraction, another subset, a score sweep, a
depth target, or a new benchmark.

If this backend is adopted, the immediately following paper-value experiment
is RQ4 end-to-end automatic annotation cost against fixed-mark replay and
label-free recurrence on the same inputs. Measuring RQ4 first for a backend
that may be rejected would not characterize the paper's adopted system.

## Paper status

**Promising thesis and credible system, but not submission-ready; current
scientific rating: WEAK REJECT.**

Step 0073 itself is not the cause of the weak reject. It is a high-quality
boundary that prevents an overstated RQ3 generalization.

## Alternatives and decision

- **Rejected:** rewrite the thesis around hierarchy uncertainty.
- **Rejected:** delete or narrow RQ3.
- **Rejected:** hide or discard the follow-on result.
- **Rejected:** insert the negative development result as the paper's new
  narrative.
- **Accepted:** preserve the positive paper, record the complete boundary in
  memory, and test one mechanism that directly addresses fragmentation.

## Tree/search updates

- A2 fixed-instruction follow-on branch: closed, inconclusive, diagnostic.
- Recursive interval-wide constructor branch: selected next.
- End-to-end RQ4 branch: queued immediately after a reportable backend is fixed.
- Story/thesis/RQ branch: unchanged and closed.

## Project-memory updates

No edits were made. Existing Step 0073 updates to `docs/evaluation.md` and
`docs/idea-story.md` are correct and sufficient for this cycle.

## Completion assessment, uncertainty, and next node

The source-grounded full-paper assessment is complete. Remaining uncertainty is
whether the fixed recursive backend can turn A2's high boundary recall into
less fragmented partitions. **Next node: EXPERIMENT / RQ3 recursive backend.**
