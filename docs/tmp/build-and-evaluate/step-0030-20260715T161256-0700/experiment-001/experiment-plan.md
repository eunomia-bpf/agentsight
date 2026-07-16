# Experiment Plan: Existing-Trajectory Calibration of Operation-Stack Induction

**Entered:** 2026-07-15T16:12:56-07:00
**Gate:** EXPERIMENT
**Selected RQ:** **RQ3: How accurate are the tags?**
**Scientific role:** supporting algorithm evidence
**Predecessor:** Step 0029 is complete; its grammar candidate is retired
**Reused scientific plan:** Step 0028 reference-calibrated recurrence, which
was approved but never reached candidate construction or metric computation

## Research Question And One Tested Hypothesis

This experiment asks one question inside the paper's unchanged RQ3:

> Can independent group annotations on already-normalized reference
> trajectories calibrate the existing action-transition NPMI recurrence score
> so that the same operation-stack induction algorithm recovers more accurate
> target partitions than its current label-free two-means cutoff?

The tested hypothesis is:

> A single scalar cutoff selected by operation-weighted B-cubed F1 on
> reference-only group annotations improves the current Step 0024 constructor's
> B-cubed F1 on both complete target populations, without changing the NPMI
> score, visible fields, unseen-transition behavior, segment construction, or
> motif naming.

This is an algorithm-calibration experiment, not a new algorithm family and
not a new benchmark. It keeps the exact thesis, **“Agent observability needs
profiling, not only debugging,”** the four paper RQs, the original AgentProf
story, and the operation/operation-stack contribution unchanged. A result can
support or bound this one calibration mechanism; it cannot rewrite the thesis,
the RQ, or the story.

## Why This Experiment Is Admitted

The user's current instruction is to improve the current algorithm directly on
the trajectories that have already run, rather than collect a new dataset or
invent another constructor. This experiment is the smallest complete test of
that request:

- it reuses all existing source-normalized trajectories and annotations;
- it changes only how the current NPMI score is calibrated;
- it does not introduce grammar rules, context windows, extra fields, a new
  score, a benchmark-specific branch, or a target-informed retry;
- positive and negative outcomes produce different paper decisions: a positive
  result establishes an optional reference-calibrated mode, while a negative
  result shows that the scalar recurrence score rather than its unsupervised
  cutoff is the limiting component; and
- Step 0028 already passed scientific plan review and implementation review,
  but its self-authored OSWorld loader stopped before fitting, product
  invocation, prediction, or any metric. Therefore no scientific result is
  being repeated or selectively rerun.

This use of the budget is stronger than another RQ2 reader variant, another
grammar candidate, or another benchmark. RQ2 already has a paper-level answer;
the grammar family has a complete contradictory result; and no new data are
needed to test the unresolved calibration question.

## Fixed Algorithm Change

The current Step 0024 method remains the base algorithm:

1. build the ordered visible-action transition table from target-disjoint
   reference sessions;
2. calculate NPMI for every observed adjacent action pair;
3. treat a transition absent from the reference table as a boundary;
4. compare every observed target transition's NPMI with one scalar cutoff;
5. form contiguous operation segments and name them with the unchanged
   run-length action motif.

The candidate replaces only the current label-free cutoff selection:

1. score all adjacent calibration-reference pairs with the unchanged NPMI
   table;
2. enumerate a cutoff below the minimum finite score, every midpoint between
   consecutive distinct scores, and a cutoff above the maximum score;
3. for each cutoff, keep unseen transitions as boundaries and construct the
   complete reference partition;
4. calculate operation-weighted B-cubed F1 against reference group annotations;
5. select the cutoff with maximum reference B-cubed F1; on an exact tie choose
   the numerically smallest cutoff; and
6. apply that scalar unchanged to target-label-withheld sessions.

No target label, target score, framework identity, boundary F1, paper result,
or comparison outcome can select the cutoff. There is one score and one fitted
scalar. The candidate may not change the RQ or tested hypothesis.

## Existing Real Assets And Isolation

### OSWorld-Human

- Source: the existing official/human-group-derived operation artifact used in
  Steps 0006, 0018, and 0024.
- Complete population: 287 eligible sessions, 3,978 operations, 3,691 adjacent
  pairs, and 2,042 human groups.
- Eligibility is exactly the established source path: `group_alignment=exact`,
  all required visible fields, and at least two operations per session.
- Use the unchanged five deterministic session folds. For target fold `f`, the
  other four folds build the NPMI table and supply calibration groups. Fold
  `f` groups are loaded only after its predictions have been persisted.

### CodeTraceBench

- Score reference: existing target-disjoint normalized reference operations,
  2,229 sessions and 87,703 operations.
- Calibration subset: the already-present 483 solved verified reference
  sessions, 18,152 operations, and 2,886 official stages.
- Target: the existing 405 failed trajectories, 20,866 operations, 20,461
  adjacent pairs, and 2,948 official stages across OpenHands, SWE-agent,
  Terminus2, and mini-SWE-agent.
- All 405 target IDs are removed before score construction and calibration.
  Their stage annotations are loaded only after predictions are persisted.
- The solved-reference to failed-target distribution shift is part of the test,
  not an excuse for a target-specific repair.

No agent run, benchmark download, trace normalization, model call, or data
collection is planned. This is a complete reanalysis of existing trajectories.

## Comparisons And Metrics

The single main baseline is the current Step 0024 label-free recurrence
constructor under the same target inputs. Existing complete baseline output is
reused. Two previously completed comparators provide interpretation only:

- OSWorld-Human's richer nine-field supervised predictor, B-cubed F1 0.8160;
- CodeTraceBench's source-visible phase-change partition, B-cubed F1 0.6544.

The primary metric is operation-weighted B-cubed F1, reported separately for
the two complete populations. Diagnostics are B-cubed precision/recall,
boundary precision/recall/F1, fitted reference objective and cutoff, candidate
and tie counts, unseen transitions, predicted groups, per-fold/per-framework
results, and complete operation/pair/group coverage. The experiment is
deterministic and runs once.

The fixed interpretation is:

- **supported:** candidate B-cubed F1 is strictly higher than Step 0024 on both
  complete populations;
- **mixed:** it is strictly higher on exactly one population, or higher on one
  and lower on the other;
- **contradicted:** every other valid complete relation;
- **invalid/incomplete:** target annotations enter fitting, registered
  populations differ, predictions are incomplete, the NPMI score changes, or
  the candidate does not conserve one assignment per operation.

The external comparators constrain wording but do not change the tested-
hypothesis classification. No aggregate average may hide a population loss.

## Minimal Implementation And Execution

Step 0028 overbuilt this test by adding a product CLI, three evaluator modules,
and product/Python equivalence before learning whether the calibration works.
This execution uses one ordinary analysis script over the established raw
artifacts. It imports the existing OSWorld and CodeTrace loaders, NPMI scorer,
partition scorer, and fold definitions. The script writes ordinary JSON/JSONL
raw output and never modifies the release product. If and only if the complete
result is supported, the orchestrator may route a later implementation step to
port the one fitted-cutoff mode into `agentpprof`; product implementation is
not allowed to become evidence by itself.

Planned raw root:

```text
.agentsight/experiments/rq3-reference-calibrated-existing-traces-v1/
```

Planned commands:

```bash
python3 script/rq3_reference_calibrated_existing_traces_eval.py \
  --mode preflight \
  --out .agentsight/experiments/rq3-reference-calibrated-existing-traces-v1/preflight

python3 script/rq3_reference_calibrated_existing_traces_eval.py \
  --mode full \
  --out .agentsight/experiments/rq3-reference-calibrated-existing-traces-v1/full
```

Preflight uses one real OSWorld target fold and one real complete CodeTrace
target while retaining the full reference/calibration populations. It checks
only that the source path, fitting path, persistence path, and scorer execute;
its metric cannot modify the candidate. Full execution covers all five
OSWorld folds and all 405 CodeTrace targets to terminal status.

## Result And Paper Discipline

The experiment skill does not edit the paper, `docs/idea-story.md`, or
`docs/user-instruction.md`. It returns a complete result to the orchestrator.
No outcome can narrow the thesis, remove a contribution, change one of the four
RQs, or introduce a negative result into reader-facing prose automatically.
The authoritative paper submodule and all skills remain untouched.

The plan itself is ordinary Markdown. Git state, hashes, commits, pushes, and
publication success are unrelated to experiment validity.
