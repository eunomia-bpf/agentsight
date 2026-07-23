# Plan Review — RQ2 Recursive Differential Operation Profile

## Verdict: REVISE

This is a promising, appropriately scoped supporting experiment: it retains
the paper's exact RQ2, uses the complete intended AgentRewardBench population,
names the fixed-chain profile as the one credible current-practice baseline,
and keeps the product output to standard signed pprof. Those are important
strengths. The verdict is nevertheless **REVISE** because the current plan
cannot yield a scientifically interpretable RQ2 result. Its stated primary
checks establish profile conservation and visual shape, not whether a recursive
profile corresponds to independently established real problems or is more
useful than the fixed-chain profile. In addition, its asserted outcome
separation and full-population/fair-baseline conditions are not yet executable
or auditable.

The required revisions below are limited to defects that would invalidate the
proposed scientific interpretation or prevent a complete run. They do **not**
ask for another benchmark, another main baseline, a custom frontend, a depth
target, or broader workload coverage.

## What is already sound

- The plan quotes RQ2 verbatim (plan lines 5--6) and keeps the proposed result
  as supporting RQ2 evidence rather than changing the RQ, thesis, or fixed
  positive program.
- A complete, real public population is the right unit of analysis. The stated
  440 trajectories, 125 mixed-outcome tasks, and 338 fixed pair occurrences
  are materially stronger than a hand-picked example. A pair occurrence may
  legitimately reuse a trajectory; the plan simply needs to make that
  population accounting explicit.
- The existing fixed six-field profile is a reasonable single main baseline:
  it represents the competing claim that the existing leaf-level fields already
  provide all useful localization. The leaf-only focus is correctly a control,
  not an additional main baseline.
- The plan correctly avoids making a prescribed stack depth an outcome. This
  conforms to the project boundary that a pprof artifact, not a bespoke
  visualizer, is the product output.

## Must-fix 1 — Register a claim-matched, outcome-independent RQ2 endpoint

Lines 103--112 define mass/path equality, hierarchy warnings, and open-ended
case questions as the only assessment. Mass equality is a necessary
correctness/control check. Variable depth, absence of unary/fan-out warnings,
and a root's reading of selected pprof views are not an RQ2 outcome and cannot
decide whether the recursive profile beats the fixed chain. In particular, a
bad-minus-good profile is *constructed* from outcome-side weights; observing
that its positive and negative lobes differ cannot by itself demonstrate that
it discovered a real problem rather than restated the supplied outcome label.

Before execution, state one predeclared primary effect, its uncertainty or
complete-population decision rule, and the positive/negative/mixed/
inconclusive thresholds. It must use an independent AgentRewardBench truth
source (for example, an official expert annotation that identifies the relevant
failure/problem or evidence span) that is unavailable to annotation and profile
construction. The plan must name the exact source field/artifact, the unit
scored (task, trajectory, or operation), the mapping from a pprof focus result
to that unit, and the standard metric and defining paper/official benchmark
protocol. If AgentRewardBench supplies only a terminal good/bad outcome and no
independent problem-localization truth, that fact must be recorded: this run can
validate an outcome-blind *product case* and provenance, but it cannot make the
claimed RQ2 localization/correspondence inference from its own signed weights.
It then needs to limit the paper conclusion accordingly rather than call visual
readability an RQ2 result.

The planned reader-facing case study may remain, but its focused subtrees must
be selected by a predeclared, outcome-blind rule and assessed against the same
declared source truth/protocol. “The root opens ... figures and answers every
case question” (lines 134--137) is an illustrative readback, not an
independent evaluator or primary measure. Source-ID recovery is useful
traceability validation; it is not evidence that the recovered responsibility
is the real problem.

## Must-fix 2 — Make outcome separation a demonstrated data-flow property

The plan repeatedly says the annotation is outcome-blind (lines 31--34,
77--80, 95--97, and 158--159), but it does not identify what the workers can
actually read. The proposed source inputs include goals, reasoning, actions,
tool state, and LLM/tool evidence (lines 11, 75, and 127--130). Any of these
may contain terminal success/failure text, reward/verdict fields, task labels,
pair membership, or aliases that reveal the target. Merely omitting a column
named `outcome` from a three-file workspace does not establish separation.

Register the annotation-time input schema and actual worker prompt/configuration
before the full run. Enumerate every model-visible field and all exact
target-label strings/aliases in those fields, then document either their
exclusion/redaction or a sensitivity/exclusion result. The annotation input
must exclude success/failure/reward, pair side, pair identifiers, expert labels,
and direct/derived terminal target fields; outcome data may first join after
the complete annotations are persisted. Record the full-session/operation
coverage and the annotation-time audit alongside the raw result. This is the
project's required literal-taxonomy target-separation check and is necessary to
support the central "outcome-blind" premise, not extra provenance machinery.

## Must-fix 3 — Specify an executable complete-population, paired comparison

The numerical population is named, but the plan provides neither a source
revision/manifest nor a runnable command/configuration that reconstructs it.
“Already independently reconstructed in Step 0067” (lines 72--74) and a raw
directory (line 138) are not enough for a new full run. Similarly,
“independent Agent workers” and “automatic Agent annotation” leave the backend,
model/version, prompt, decoding/seed policy, worker count, timeout/failure
handling, and annotation command unspecified. A deterministic exporter replay
does not make an unspecified model annotation run deterministic.

Add one real preflight command and one full-run command (or a documented
official command sequence), with immutable input locations and versions, the
annotation configuration, output locations, and a terminal completion rule.
The plan must also include a population ledger that proves: all and only the
440 eligible trajectory IDs are annotated; all 125 task IDs and all 338
bad--good pair occurrences are present; every operation has exactly one
accepted annotation/projection or a recorded exclusion; and how reuse of a
trajectory across pair occurrences changes signed mass. State the expected
annotation cost/time and the recovery rule for a failed worker so the complete
run is feasible rather than an aspirational 440-session collection.

For fairness, regenerate the fixed-chain baseline from this exact frozen
operation and pair-occurrence manifest through the same signed-pair/pprof
emission path as the recursive candidate. Do not treat a previously rendered
fixed-chain `.pb.gz` as a sufficient baseline merely because its aggregate
numbers were once checked. The comparison record must show equality of source
operation IDs, occurrence multiplicities, weights/sign convention, sampling
unit, and pprof measure/labels before the stack projection changes. The existing
signed-mass check is then a necessary secondary veto, as intended, rather than
the headline result.

## Must-fix 4 — Replace visual-shape acceptance with a published protocol and
predeclared interpretation

Lines 68--71 name Differential Flame Graphs, AgentRewardBench, and Go pprof,
but do not cite a version/identifier or say which part of each protocol is
used. More importantly, “no degenerate-unary or flat-fan-out warning” (lines
106--108) and “compact signed overview plus two ... subtrees” (lines 152--154)
are visual acceptance criteria. They risk selecting hierarchy depth and
appearance after seeing the outcome instead of testing the competing
explanation in lines 57--60. The plan correctly says no depth is optimized, but
the warning condition still makes shape an undeclared acceptance gate.

Name the exact published/official artifacts and versions; predeclare the
signed pprof convention, focus query rule, and the mapping used by the primary
endpoint in Must-fix 1. Keep hierarchy diagnostics only as descriptive QA
reported for both candidate and baseline, not as pass/fail evidence. The
positive result must follow from the claim-matched endpoint plus the fairness
and label-separation controls; a visually deep or attractive flame graph must
not turn an otherwise unsupported result into RQ2 evidence.

## Plan-review criterion assessment

| Criterion | Assessment |
|---|---|
| Exact RQ and meaningful hypothesis | The RQ is preserved, but the hypothesis currently mixes a visual/product property with correspondence to real problems. Must-fix 1 separates and tests the latter. |
| Admission and decision value | Sound in principle: a complete second product case can answer the fixed-chain-decoration objection. Its positive and negative paper decisions become decision-relevant only after a registered endpoint exists. |
| Baselines, workloads, metrics, and fairness | Workload scope and the minimal baseline set are appropriate. The paper-facing outcome/metric and its official definition are absent; baseline equivalence and outcome isolation are asserted rather than demonstrated. |
| Execution, completion, and interpretation | Raw paths and a real-data preflight are named, but no executable workflow, configuration, cost, complete-population ledger, or objective terminal interpretation is supplied. |

## Nonblocking suggestions

- Report the fixed-chain and recursive diagnostic shape summaries side by side,
  but do not use them to select a winner.
- Preserve focused pprof screenshots as explanatory case-study material only
  after the predeclared focus rule has selected them.

---

## Round 2 Follow-up Review

## Verdict: REVISE

Two of the four Round 1 blockers are resolved in the revised *design*, but
outcome-blind construction is still not executable on the stated command path.
This is a scientific and executability blocker, not a request for broader
evaluation.

### Resolution of Round 1 must-fixes

1. **Claim-matched RQ2 endpoint — resolved.** The plan now names the official
   consensus `trajectory_looping` label, fixes the scored unit to each unique
   trajectory, defines the outcome-blind recovery-path exposure score, uses
   ordinary non-interpolated AP, and predeclares a task-cluster bootstrap and
   outcome rules. The five consensus conflicts are retained in the product
   profile but excluded with a stated reason from the target-specific score.
   This distinguishes correspondence from the bad-minus-good weighting rather
   than treating a signed lobe as its own evidence.

2. **Outcome separation — not yet resolved.** The schema and literal-label
   audit in the plan are adequate requirements, but the proposed materialization
   command is not a valid implementation of them. The named
   `script/agentreward_diff_pprof_eval.py` accepts `--agentpprof` and
   `--aggregate-only`; it has no `--binary` or
   `--materialize-annotation-workspace` option. More critically, its current
   `main()` immediately calls `load_labels(dataset_root)`, which reads
   `data/annotations.csv` and parses both `trajectory_success` and
   `trajectory_looping`, before it materializes any source trajectory. Its
   aggregate path likewise uses those labels to form groups and pairs. Thus the
   only specified executable materialization route opens the outcome/expert
   labels before the workers have produced annotations, contrary to the plan's
   core premise.

   **Required repair:** replace the nonexistent command with an existing,
   target-blind source-workspace command, or make the plan explicitly include
   the necessary adapter implementation and its actual post-implementation
   command. That annotation-time path must accept a precomputed eligible
   trajectory-ID manifest and source files only, and must not open
   `annotations.csv`. A separate, post-annotation scorer/pairer may read that
   file. Re-run the literal-field audit against the actual emitted workspace.
   This is a small data-flow repair, not an additional control interface or
   experiment.

3. **Executable complete-population and fair paired comparison — not yet
   resolved.** The new ledger, worker policy, cost estimate, fresh-baseline
   requirement, and signed-mass equality conditions are sufficient on paper.
   However, the two supplied commands cannot produce the declared artifacts:
   the first uses unsupported flags, and the second invokes
   `--aggregate-only` with unsupported `--binary` and
   `--recursive-annotation` flags. The current script's aggregate function
   emits its own fixed-stack operations from source/labels; it does not consume
   `annotation.json`. Consequently, the stated commands neither construct the
   recursive candidate nor regenerate the candidate and fixed-chain profiles
   from one frozen operation/pair-occurrence manifest. Until the plan names a
   runnable candidate path and a runnable fresh fixed-chain path with that
   common manifest, completion and comparison fairness cannot be checked.

4. **Visual-shape acceptance and published protocol — resolved.** The plan now
   identifies the Differential Flame Graphs and AgentRewardBench sources,
   predeclares exact recovery/completion focus labels, makes AP rather than
   figure appearance the scientific decision, and explicitly relegates depth
   and fan-out warnings to descriptive QA. This addresses the no-depth/no-
   appearance concern without adding a metric or custom renderer.

### Blocking disposition

Do not run the preflight or full annotation through the current commands. Once
the plan names a working source-only workspace materializer plus a separate
post-annotation scoring/pairing command, and those commands implement the
stated common-manifest candidate/baseline replay, the remaining review issues
are resolved. No extra benchmark, baseline, or visual criterion is required.

---

## Round 3 Follow-up Review

## Verdict: APPROVE

This round rechecked only the two Round 2 blockers against the revised plan,
`backend-instruction.md`, the two named implementations, and their focused
tests. Both blockers are resolved. No additional benchmark, baseline,
reproducibility protocol, or visual acceptance condition is required for this
plan review.

### 1. Outcome-blind annotation boundary — resolved

The annotation-time path is now a separate, executable program:
`script/materialize_agentreward_annotation_workspace.py`. It accepts only
`--dataset-root`, a source-session list, and an output directory; it has no
argument, import, or code path for `data/annotations.csv`, pair rows, success,
pair side, or expert-looping labels. It reads only selected released
`cleaned/` trajectory JSON, omits `summary_info`, emits the declared visible
fields, and records an annotation-input audit including the literal target-label
scan.

The plan's source-ID list is flattened and deduplicated before materialization,
so it supplies no bad/good side to the worker. The reviewed backend instruction
likewise authorizes reading only assigned `trace.jsonl` source nodes and
explicitly forbids inferring or recording benchmark success/failure. The
workspace replay command is meaningful: `agentpprof --annotation-file` applies
the persisted annotations to sibling `trace.jsonl` and atomically writes the
resolved semantic paths before any post-annotation evaluator runs.

The focused materializer tests pass, including a source fixture whose
`summary_info` contains `trajectory_success=Successful` and
`trajectory_looping=No`; neither label appears in the emitted nodes. The test
run was:

```text
python3 -m pytest -q script/test_materialize_agentreward_annotation_workspace.py script/test_agentreward_recursive_diff_eval.py
6 passed
```

As a real-input structural check, the 338-pair file yields exactly 440 unique
source IDs, and all 440 resolve in the released `cleaned/` source index (zero
missing IDs). The post-annotation evaluator is the first reviewed program that
opens `annotations.csv`, and it does so only to compute the registered expert
looping endpoint.

### 2. Common-source recursive/fixed replay — resolved

`script/agentreward_recursive_diff_eval.py` consumes the already pair-expanded
bad and good operation files once. It derives recursive records by attaching
the applied semantic path to each exact source record, while the fixed-chain
records are copies of those same rows. Before either pprof invocation it
compares `Counter(source_session, evidence_id, value)` separately for the bad
and good sides and aborts on any mismatch. It then invokes AgentPProf for the
recursive and fixed stacks from those respectively matched files and verifies
that each emitted `.pb.gz` is nonempty and accepted by stock `go tool pprof`.

The evaluator's focused tests pass and cover source-key preservation,
pair-occurrence de-duplication for the unique-trajectory endpoint, consensus
label handling, and the registered AP decision path. The actual retained inputs
also have the declared 338 pair occurrences; their repeated source rows remain
as pair-occurrence multiplicities, which is precisely the signed-profile unit
the plan specifies. The implementation therefore changes the stack projection,
not the source operation population or signed weights.

### Scope of this approval

This approves execution with respect to the two previously blocking data-flow
and comparison-validity defects. It does not pre-judge the RQ2 result: the
registered AP/interval rule, source-multiset checks, and independent result
review still determine whether the completed run supports, contradicts, or
limits the hypothesis.
