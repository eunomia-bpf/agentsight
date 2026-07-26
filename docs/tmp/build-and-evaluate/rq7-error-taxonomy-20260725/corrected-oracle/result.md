# RQ7 corrected-oracle conformance reassessment

## Outcome

The corrected `native-root-conformance-v4` oracle dissolves 7 of the 9
previous B+C mismatches. There are no new B+C mismatches. HEAD trajectory is
58/60 on artifact-linked and cross-session questions: B is 28/30 and C is
30/30.

The two residual rows are agentsight-B1 and agentsight-B2. Both arise from one
projection-side per-event cwd error. They are not an unresolved oracle
option-arity issue.

Across all 120 questions, trajectory answers 100 correctly:

| Family | Correct | Wrong | Abstain | Correct coverage | Conditional accuracy |
|---|---:|---:|---:|---:|---:|
| A action-only | 12 | 18 | 0 | 40.0% | 40.0% |
| B artifact-linked | 28 | 2 | 0 | 93.3% | 93.3% |
| C cross-session | 30 | 0 | 0 | 100.0% | 100.0% |
| D final-state | 30 | 0 | 0 | 100.0% | 100.0% |
| **All** | **100** | **20** | **0** | **83.3%** | **83.3%** |

## Reassessment method

The frozen experiment was not modified. Every frozen source is checked
against its recorded size and SHA-256. Because HEAD/native-root tooling cannot
read the v2 ledger directly, the script uses the same bridge as
`rerun-at-HEAD`: frozen source-file session IDs and ordinals, source hashes,
timestamps, record/call ordering, cutoffs, and immutable question paths are
preserved while v4 re-parses the native rows.

All 120 expected answers are in `corrected-answers.csv`; 24 change from the
v2 freeze. The complete rationale for every change is in
`change-justifications.md`. No B or D expected value changes. Seven C values
change. Seventeen A values change because v2 counted non-tool file-history
snapshots as edit actions and did not decode and edit-classify the current
exec/apply_patch wrappers.

Eight formerly correct trajectory rows become wrong under the corrected
answers: agentsight-A2; ActPlane-A2/A4/A5;
bpf-developer-tutorial-A5; eunomia.dev-A2;
agentskill-observability-paper-A2; and academic-writing-skills-A2. No
formerly correct B+C row becomes wrong.

## Final method totals

Each family has 30 questions.

| Method | A | B | C | D |
|---|---:|---:|---:|---:|
| FinalState | 0/30 (30 abstain) | 0/30 (30 abstain) | 0/30 (30 abstain) | 30/30 |
| Counts | 3/30 (12 abstain) | 0/30 (30 abstain) | 0/30 (30 abstain) | 0/30 (30 abstain) |
| ProcGrep | 12/30 | 0/30 (30 abstain) | 0/30 (30 abstain) | 0/30 (30 abstain) |
| Trajectory | 12/30 | 28/30 | 30/30 | 30/30 |

## B+C by project

Trajectory answers all ten B+C questions for every project, so conditional
accuracy and correct coverage are identical here.

| Project | Correct | Wrong | Conditional accuracy |
|---|---:|---:|---:|
| agentsight | 8/10 | 2 | 80.0% |
| ActPlane | 10/10 | 0 | 100.0% |
| bpf-developer-tutorial | 10/10 | 0 | 100.0% |
| eunomia.dev | 10/10 | 0 | 100.0% |
| agentskill-observability-paper | 10/10 | 0 | 100.0% |
| academic-writing-skills | 10/10 | 0 | 100.0% |
| **Total** | **58/60** | **2** | **96.7%** |

Trajectory minus ProcGrep B+C correct coverage is **+96.7 percentage
points**, with project-block bootstrap 95% CI **[+90.0, +100.0]**. This uses
the rerun method: six project blocks, 10,000 resamples, seed 20260722.
ProcGrep abstains on all 60 B+C questions.

## Disposition of the original nine mismatches

| Row | Corrected expected | HEAD trajectory | Disposition |
|---|---:|---:|---|
| ActPlane-C1 | 3 | 3 | dissolved by wrapped-patch recovery |
| ActPlane-C2 | 3 | 3 | dissolved by wrapped-patch recovery |
| ActPlane-C5 | 12 | 12 | dissolved by wrapped-patch recovery |
| bpf-developer-tutorial-C1 | 7 | 7 | dissolved by wrapped-patch recovery |
| bpf-developer-tutorial-C2 | 8 | 8 | dissolved by wrapped-patch recovery |
| bpf-developer-tutorial-C5 | 22 | 22 | dissolved by wrapped-patch recovery |
| academic-writing-skills-C2 | 8 | 8 | dissolved by inline-cd scoping |
| agentsight-B1 | 21 | 22 | remains: projection cwd scope |
| agentsight-B2 | 17 | 18 | remains: same extra projected read call |

There are no newly mismatching B+C rows.

## Residual cause and evidence

Both residual answers differ by the same source call:
`toolu_01QdMaxMofN8AJdpWurjqbnR` in frozen source
`S000-007c5d5ec4`.

The source row's cwd is
`/home/yunwei37/workspace/agentsight/collector` and its command is
`cat -n collector/src/view/mod.rs`. The next native row reports exit code 1
and `No such file or directory`. The spec says to keep attempted calls but
resolve relative operands lexically. The source-direct path is therefore
`collector/collector/src/view/mod.rs`, outside P0's
`collector/src/view/mod.rs` identity.

HEAD projection emits the same call as a read of P0. Its parser only assigns
the accumulated cwd when it is initially absent
(`agent-session/src/parser.rs`, lines 300--306), then creates every later
tool event using that accumulated cwd (lines 373--379). It does not adopt the
later Claude row cwd. Thus it retains the repository-root cwd and projects
the operand to `collector/src/view/mod.rs`.

B1 counts attempted P0 calls and B2 counts attempted P0 reads regardless of
result status, so this one wrongly scoped projected action adds one to both
answers. The exact projection-only and oracle-only edge pair is recorded in
`oracle-edge-diff.json`. This is a projection-side cwd/scope bug; no remaining
oracle defect is needed to explain either row.

Broader exact edge conformance is also not established: projection-only /
oracle-only edge counts are 94/29 for ActPlane, 3/6 for
academic-writing-skills, 1/1 for agentsight, 1/1 for
agentskill-observability-paper, 0/0 for bpf-developer-tutorial, and 4/6 for
eunomia.dev. Those differences do not alter the other immutable question
answers, but they prevent treating 58/60 question accuracy as edge-level
equivalence.

## Anchor audit

The immutable questions supply their normalized P0--P4 paths, so those paths
remain the scored identities. A fresh v4 ranking would change ActPlane's
anchors substantially after recovering 482 patch edges; its top five become
`bpf/src/lib.rs`, `bpf/process.bpf.c`, `bpf/taint_engine.bpf.h`,
`script/test-kernel-5.10.sh`, and
`crates/actplane-runtime/src/runtime.rs`. Eunomia.dev's P4 also changes. A new
experiment freeze must regenerate anchors and expected answers under one
version-consistent v4 pipeline.

## Validity and capability judgment

The run is valid for reassessing the same immutable questions: inputs are
hash-checked, ordering/session identities follow the prior HEAD bridge, all
120 answers are materialized, and focused grammar plus production action
fixtures pass.

The result supports high B+C coverage relative to ProcGrep, but it does not
support an unqualified exact-fact capability claim. The direct blocker is the
demonstrated projection cwd bug (58/60, not 60/60). A second qualification is
that answer-level success is weaker than exact edge conformance. A defensible
claim today is limited to the measured 96.7% B+C correct coverage on this
frozen set. The action-only result is 40.0%, and overall conformance is 83.3%,
so neither supports a general conformance claim. The six-project bootstrap
describes uncertainty over these corpus blocks, not population
generalization. An exact claim requires fixing per-event cwd handling on the
projection side, regenerating a version-consistent v4 freeze/anchors, and
rechecking the full edge ledger and all questions.

The independent result review approved this same-question reassessment and
rated its research value high: it separates seven corrected oracle rows from
one real projection defect while exposing action-oracle drift. Its recommended
next experiment is a version-consistent v4 freeze after the cwd fix, with
regenerated anchors/questions, a full edge-ledger comparison, all-120 scoring,
and adversarial changing-cwd, failed-call, inline-cd, and wrapped-patch
fixtures. The full reviewer disposition is in `result-review.md`.

## Reproduction and validation

```bash
python3 docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/corrected-oracle/scripts/test_oracle_v4.py
python3 docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/corrected-oracle/scripts/reassess_corrected_oracle.py
python3 -m py_compile agentvis/research/rq7_source_oracle_check.py \
  docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/corrected-oracle/scripts/reassess_corrected_oracle.py \
  docs/tmp/build-and-evaluate/rq7-error-taxonomy-20260725/corrected-oracle/scripts/test_oracle_v4.py
python3 agentvis/research/rq7_measurement.py check-action-fixtures \
  --fixtures agent-session/tests/fixtures/strict-action-grammar.json
git diff --check
```

Observed: 6 focused v4 tests passed; 8 action, 4 lifecycle, and 5
native-root fixtures passed; Python compilation and `git diff --check`
passed.
