# Experiment Plan: RQ3 Reference-Calibrated Recurrence

## Research Question

- **RQ exactly as written in the paper:** **RQ3: How accurate are the tags?**
- **Specific uncertainty tested here:** whether independent group-boundary
  annotations can calibrate the existing action-transition recurrence score
  more accurately than its label-free two-means cutoff on target-label-withheld
  sessions.
- **Why the answer matters:** the current operation-stack constructor has a
  simple recurrence mechanism but its CodeTraceBench calibration is post-hoc,
  slightly below the external phase-change B-cubed comparator, and action-only
  target outcomes cannot authorize another unsupervised cutoff tweak. A
  reference-supervised mode tests whether the problem is calibration rather
  than the recurrence score, without changing the operation model or adding a
  dataset.

This is one supporting group-boundary experiment inside fixed RQ3. It cannot
change, split, rename, narrow, or answer all of RQ3. Phase, action, and literal
tag-name accuracy remain open regardless of outcome. The exact thesis remains
**“Agent observability needs profiling, not only debugging.”** The four-RQ
architecture, original AgentProf story, contribution, and paper claim surface
remain fixed.

## Paper-Value Admission

- **Planned role:** supporting.
- **Largest credible paper story this experiment could unlock:** AgentProf can
  use the same recurrence statistic in two honest information regimes: a
  zero-annotation label-free constructor and a more accurate optional
  reference-calibrated constructor when independently grouped histories exist.
- **Strongest reviewer reject argument addressed:** the current constructor's
  cutoff is selected post hoc on reused targets, does not beat the strongest
  simple partition comparator on pooled CodeTraceBench B-cubed, and leaves the
  reader unable to tell whether recurrence or unsupervised calibration is the
  limiting component.
- **Independent evidence added beyond prior runs:** a target-label-withheld
  fit/apply protocol on the exact already-normalized trajectories. OSWorld
  withholds each target fold's labels; CodeTraceBench fits only on 483 solved
  verified references and applies once to the reused 405 failed development
  targets under a declared distribution shift.
- **Why the result is not tautological, already settled, or dominated:** target
  labels never select the cutoff. Step 0026 ruled out target-outcome-driven
  action-only rules but explicitly did not test an annotation-supervised
  information contract. Existing Step 0006 uses a richer nine-field Bernoulli
  predictor; it does not establish whether the current scalar recurrence score
  itself is calibratable.
- **Paper decision if positive:** retain the label-free release as the default,
  add the supervised scalar calibration as supporting group-boundary evidence,
  and report the annotation-availability tradeoff without calling it
  label-free, untouched, or a complete RQ3 answer.
- **Paper decision if contradictory, mixed, or inconclusive:** retain Step 0024
  unchanged; conclude only that reference-only scalar calibration does not
  transfer consistently across the declared sessions/distribution shift. Do
  not change the RQ, hypothesis, thesis, or story, and do not introduce a
  second cutoff rule.
- **Best alternative experiment:** a new phase/action/literal-tag benchmark
  would cover more of RQ3, and an end-to-end decision/repair study would have
  higher eventual RQ2 value. This experiment wins the immediate budget because
  the user explicitly requested improving the algorithm on already-run traces,
  all required reference annotations and targets already exist, and no new
  data collection or normalization is needed.

## Expected And Alternative Outcomes

- **Current expected answer:** reference-only calibration improves
  operation-weighted B-cubed F1 over the Step 0024 label-free constructor on
  both complete target populations, but remains supporting post-hoc evidence.
- **Strongest competing explanation:** action-transition NPMI aliases true
  operation boundaries so heavily that no scalar cutoff transfers, even when
  the cutoff is fit on independent reference labels.
- **Result that contradicts the expectation:** the candidate fails to improve
  B-cubed on CodeTraceBench or lowers B-cubed on OSWorld-Human.

## Published Precedent And Real Assets

- **Closest published protocol:** CodeTracer/CodeTraceBench provides
  source-authored consecutive stage intervals across four code-agent
  frameworks; OSWorld-Human provides human action groups. The fitting pattern is
  ordinary supervised calibration with target labels withheld, not a new
  benchmark protocol.
- **Official assets already present:**
  - OSWorld-Human: all 287 eligible sessions, 3,978 operations, 3,691 adjacent
    pairs, and 2,042 human groups under the existing five session folds.
  - CodeTraceBench score reference: the exact Step 0024 target-disjoint 2,229
    sessions and 87,703 operations.
  - CodeTraceBench labeled calibration subset: exactly 483 solved verified
    references, 18,152 operations, and 2,886 official stages.
  - CodeTraceBench reused development target: exactly 405 failed trajectories,
    20,866 operations, 20,461 adjacent pairs, and 2,948 official stages.
- **Explicit exclusions:** 112 manifest non-target trajectories absent from the
  normalized reference artifact; every one of the 405 target IDs before NPMI or
  cutoff fitting; every target stage label until after candidate predictions
  are written.
- **Necessary custom glue:** extend the existing recurrence evaluators with one
  source adapter that writes calibration operations containing ordinary
  `session`, `action`, and `group` fields. Add one user-facing
  `--induce-calibration-operation-file PATH` input to the normal induction path.
  `agentpprof` itself fits the registered scalar cutoff from that file and the
  existing NPMI reference, then applies it to the target. This is a usable
  supervised constructor for any independently grouped reference history, not
  an experiment-supplied numeric cutoff or promotion/checker contract. When
  the option is omitted, Step 0024 label-free behavior must remain
  decision-for-decision and output-field compatible.

## The One Algorithm Change

The NPMI association table, one count per adjacent occurrence, visible
`session`/`action` fields, unseen-transition rule, segment construction,
run-length motif naming, operation-stack projection, and weight folding remain
exactly Step 0024.

For each target fold/population, replace only the label-free applied cutoff with
one scalar cutoff fitted from reference group labels:

1. score every adjacent reference pair using the unchanged Step 0024 NPMI
   association table;
2. enumerate the deterministic scalar decision partitions induced by a cutoff
   below the minimum score, every midpoint between consecutive distinct finite
   reference scores, and a cutoff above the maximum score;
3. keep unseen transitions as boundaries for every candidate;
4. compute operation-weighted B-cubed F1 against reference group/stage
   partitions only;
5. select the cutoff with maximum reference B-cubed F1; on an exact tie, select
   the numerically smallest cutoff, which yields no more boundaries than the
   tied larger cutoff;
6. apply that one cutoff unchanged to the target-label-withheld population.

This is the only fitting objective and the only tie rule. Boundary F1,
framework, benchmark identity, target metrics, current-result relation, and
paper preference cannot select the cutoff. There is no second cutoff,
same/cross-action condition, context window, feature, model, smoothing rule,
fallback, per-framework exception, or target-informed retry.

### OSWorld-Human Isolation

Use the unchanged five session folds. For target fold `f`, build the unchanged
Step 0024 NPMI association table from the other four folds, fit the scalar
cutoff only from those four folds' group annotations, write target predictions,
and only then load fold `f` human groups for scoring. Every eligible session is
a target exactly once.

### CodeTraceBench Isolation

1. Load target operation IDs without reading stages.
2. Remove all 405 target IDs from the broad reference operations before NPMI
   construction or calibration selection.
3. Reproduce the exact Step 0024 target-disjoint score reference: 2,229
   sessions / 87,703 operations.
4. Intersect that reference with the verified manifest and `solved=true` to
   obtain exactly 483 calibration sessions / 18,152 operations / 2,886 stages.
5. Confirm the 112 unavailable non-target manifest trajectories remain absent
   and excluded.
6. Fit the one cutoff on those 483 stages, apply it to all 405 target
   trajectories, persist predictions, and only then load the 405 target stage
   labels for scoring.

The solved-reference to failed-target shift is part of the test. The outcome
cannot be called untouched or independent cross-family confirmation because
these 405 target labels were observed in earlier development steps.

## Comparison

- **Proposed method:** reference-calibrated scalar cutoff over unchanged
  action-transition NPMI.
- **Main baseline:** current Step 0024 label-free monotone two-means recurrence,
  representing a zero-annotation constructor. Existing complete raw outputs
  are reused and exact reproduction is asserted; no new baseline run ID is a
  contribution.
- **Strong existing comparator, OSWorld:** the Step 0006 nine-field supervised
  Bernoulli predictor (B-cubed F1 0.8160). It represents a richer supervised
  boundary model. It is cited from its existing complete run, not rerun.
- **Strong existing comparator, CodeTraceBench:** visible phase-change
  (B-cubed F1 0.6544). It represents a simple source-provided hierarchy and is
  reused from the existing full scorer.
- **Conclusion if a comparator wins:** improvement over Step 0024 can still
  support calibration of the existing score, but the candidate cannot be
  described as the best supervised boundary method or strongest partition
  view.
- **Information fairness:** the candidate alone consumes reference group
  labels and must be labeled supervised. No target label, target metric, or
  paper result enters fitting. Every method receives identical target actions
  and target sessions.

## Workloads And Metrics

- **Real workloads:** all 287 eligible OSWorld-Human sessions and all 405 fixed
  CodeTraceBench failed development targets; no prefix or task selection.
- **Primary metric:** operation-weighted B-cubed F1 separately for each complete
  population.
- **Diagnostics:** B-cubed precision/recall, boundary precision/recall/F1,
  selected reference-only cutoff/objective value, candidate count and tie
  count, segment/motif counts, unseen pairs, per-fold/per-framework results,
  coverage, source isolation, Rust/Python equivalence, and mass conservation.
- **Repetitions:** deterministic; one complete execution after preflight.
- **Cost:** local CPU execution over existing files; no model or API cost.

## Fixed Result Interpretation

- **Supported:** candidate B-cubed F1 is strictly higher than Step 0024 on both
  complete populations.
- **Mixed:** candidate is strictly higher on exactly one population, or higher
  on one and lower on the other.
- **Contradicted:** every other valid complete relation.
- **Invalid/incomplete:** target labels or IDs enter fitting; reference coverage
  differs; the fitting objective/tie rule changes; target rows are missing;
  Step 0024 score/post-cutoff construction changes; Rust/Python decisions
  disagree; or weight is not conserved.

External comparator wins do not alter this fixed tested-hypothesis verdict;
they constrain the paper interpretation. No aggregate mean can hide a
population regression. A local negative is a mechanism/calibration boundary,
not authorization to change RQ3 or the paper story.

## Planned Runs

| Run group | Role | Workload | System/method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| OSWorld full | proposed + current baseline | 287 sessions / five held-out folds | reference-calibrated NPMI + Step 0024 | 1 | candidate/current B-cubed relation and richer supervised comparator context |
| CodeTrace full | proposed + current baseline | 483 solved references -> 405 failed targets | reference-calibrated NPMI + Step 0024 | 1 | candidate/current B-cubed relation under declared shift and phase comparator context |
| equivalence | correctness | all target decisions above | Rust versus Python reference | 1 | validity only |

## Execution

- **Implementation scope:** existing recurrence evaluator(s), one supervised
  calibration-operation input on the normal `agentpprof` induction path,
  focused tests, and exact equivalence checks. The calibration file contains
  only ordinary `session`, `action`, and `group` fields; Rust fits the cutoff
  internally. No raw numeric cutoff input, paper, or canonical idea/user
  document is added or edited.
- **Implementation review:** a fresh read-only reviewer checks that omitted
  cutoff exactly reproduces Step 0024, supplied cutoff changes only the boundary
  comparison, target IDs/labels cannot enter fitting, and no hidden second rule
  exists.
- **Real preflight:** one actual OSWorld target fold execution and the
  lexicographically first complete CodeTraceBench target through the release
  binary, real reference files, fitted cutoff, output path, and scorer path.
  Preflight establishes execution only; its target metric cannot alter the
  candidate.
- **Full completion:** 3,691 OSWorld decisions and 3,978 assignments across all
  five folds; 20,461 CodeTraceBench decisions and 20,866 assignments across all
  405 targets; exact Rust/Python equivalence and mass conservation.
- **Raw roots:**
  - `.agentsight/experiments/rq3-reference-calibrated-recurrence-v1/`
  - `.agentsight/experiments/rq3-reference-calibrated-codetracebench-v1/`
  - `.agentsight/experiments/rq3-reference-calibrated-rust-equivalence-v1/`
- **Recovery:** ordinary raw JSON/JSONL outputs under those roots; rerun an
  affected complete cell only for a systematic execution defect. No target
  feedback can revise the candidate.

The product command executed by both evaluators is:

```bash
agentpprof \
  --operation-file TARGET.jsonl \
  --induce-operation-stack \
  --induce-reference-operation-file SCORE_REFERENCE.jsonl \
  --induce-calibration-operation-file CALIBRATION_WITH_GROUP.jsonl \
  --view operations \
  --stack operation \
  --format json \
  --deterministic-output \
  --output PROFILE.json
```

The calibration file is session-disjoint from `TARGET.jsonl`. The target file
contains no `group` field. Omitting `--induce-calibration-operation-file`
executes the unchanged Step 0024 label-free calibration.

Approved real-preflight commands after implementation review:

```bash
python3 script/rq3_reference_calibrated_recurrence_eval.py \
  --mode preflight \
  --binary agentpprof/target/release/agentpprof \
  --operation-file docs/visexp/out/external-agent-trace-osworldhuman-r290/osworld-human-operations.jsonl \
  --out-dir .agentsight/experiments/rq3-reference-calibrated-recurrence-v1/preflight

python3 script/rq3_reference_calibrated_codetracebench_eval.py preflight \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --reference-operations docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --out .agentsight/experiments/rq3-reference-calibrated-codetracebench-v1/preflight
```

Approved full commands after both preflights succeed:

```bash
python3 script/rq3_reference_calibrated_recurrence_eval.py \
  --mode full \
  --binary agentpprof/target/release/agentpprof \
  --operation-file docs/visexp/out/external-agent-trace-osworldhuman-r290/osworld-human-operations.jsonl \
  --out-dir .agentsight/experiments/rq3-reference-calibrated-recurrence-v1/full

python3 script/rq3_reference_calibrated_codetracebench_eval.py full \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --reference-operations docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --verified-manifest .agentsight/experiments/codetracebench-rq2/manifests/verified.parquet \
  --out .agentsight/experiments/rq3-reference-calibrated-codetracebench-v1/full
```

Each evaluator performs the ordered isolation protocol before invoking the
product command, recomputes the Python reference decision path, compares every
Rust decision/segment/motif, and loads target labels only after writing
`PROFILE.json` and a target-prediction JSONL. Those files are the scorer input;
there is no separate target-aware fitting command.

## Reproducibility Notes

- Software remains `agentpprof 0.2.37` until the candidate is implemented.
- Existing fold seed, normalized operations, manifests, labels, scorers,
  metrics, and current summaries are fixed.
- The experiment is deterministic and has no random seed beyond the existing
  OSWorld fold assignment.
- CodeTraceBench is post-hoc reused development evidence with a
  solved-reference/failed-target shift; OSWorld folds are target-label-withheld
  but the corpus is also a previously observed development population.
- The authoritative `docs/agentpprof-paper` submodule, global skills, branch,
  exact thesis, RQs, and paper source remain unchanged during this experiment.
