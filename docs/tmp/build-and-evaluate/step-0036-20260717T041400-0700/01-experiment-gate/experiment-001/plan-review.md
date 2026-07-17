# Plan Review: RQ2 Same-Signal Diagnostic Decomposition

**Plan:** `experiment-plan.md`
**Skill:** `research-experiment-design`
**Review policy:** one independent reviewer plus at most two follow-ups; only a
scientific or executability defect that would invalidate the result blocks.

## Round 1 — Independent Scientific and Executability Review

**Reviewed:** 2026-07-17T04:24:00-07:00
**Reviewer:** independent subagent, read-only
**Verdict:** **REVISE**

### Scope and admission

The experiment is admitted. It tests one coherent hypothesis inside the fixed
RQ2: whether the same retained diagnostic signal becomes more useful under
operation-stack organization at fixed operation work, without unacceptable
propagation onto clean trajectories. The three complete workloads, same-signal
comparison, raw/atomic baselines, session control, and reuse-only execution are
scientifically coherent. Positive, contradictory, and mixed results produce
different paper decisions.

Official evaluator execution is feasible:

- AgentProcessBench and TraceElephant source evaluators can run directly over
  retained source/prediction files.
- HINTBench's downloaded file imports `vllm` at module load while the current
  analysis environment lacks that package, but the retained outputs can be
  scored by loading the unchanged pure scoring functions with the inference
  dependency stubbed, or by extracting and invoking those exact functions.
  This is an adapter issue, not a reason to rerun the model.

MAP is standard non-interpolated AP/MAP. Recall@20% is a standard ranking metric
at a project-selected operating point, and the plan already discloses that the
retained populations were previously inspected.

### Blocking defect 1 — Arbitrary cutoff-tie ordering

The first plan used immutable source order to truncate an equal-score tier at
the 20% operation budget. Several views produce very large ties, so this would
make the primary fixed-budget result depend on trajectory ordering rather than
the scoring method.

The reviewer measured the issue on retained artifacts:

- HINTBench atomic Recall@20% changes from approximately `0.4875` under source
  order to `0.5819` under reverse order;
- its uniform tie expectation is approximately `0.5484`; and
- TraceElephant raw/atomic results also move materially under tie reversal.

This can change the AgentProf-versus-atomic interpretation and therefore blocks
the original metric definition.

**Required minimal repair:** Use exact-K tie-averaged expected Recall@20% as the
primary value. Analytically allocate the remaining cutoff slots uniformly over
the intersected tier, and report the tier's attainable best/worst recall bounds
and size. Source-order Recall@20% may remain only as an operational sensitivity.

**Root disposition:** accepted and applied. The revised plan keeps exactly one
fixed-budget metric and does not add another workload or metric family.

### Blocking defect 2 — Clean thresholds mislabeled as official/native

The first plan called the clean thresholds native and called their outputs
false-positive rates:

- AgentProcessBench's official protocol evaluates 20 judge labelers separately;
  the retained harmful-vote fraction and `> 0.5` majority operating point are
  project aggregation choices, not an official benchmark predictor/threshold.
- HINTBench's `> 0` Wilson/nonzero-support operating point is also a project
  propagation threshold, not the official safe/unsafe decision rule.

The distinction is scientifically material. Under those project points, the
reviewer observed very broad propagation on the retained data (including clean
any-support rates of 1.0 for the inspected AgentProf cases), so these values
primarily diagnose how grouping spreads support. Calling them native benchmark
FPR would misattribute the construct.

**Required minimal repair:** Separate two layers:

1. external-signal clean error using each benchmark's official/source-native
   prediction semantics; and
2. project-defined clean support-propagation controls after organization at the
   predeclared project operating points.

Do not call the second layer official, native, or benchmark-defined FPR. For
AgentProcessBench, report the 20 constituent judges separately for official
signal quality rather than inventing a new plurality labeler.

**Root disposition:** accepted and applied. The revised plan keeps the existing
harmful-vote fraction for the already materialized comparison but labels its
majority point as project-defined. HINT's official confusion matrix and
project-defined nonzero propagation are also separated.

### Nonblocking observations

- The plan correctly states that official signal metrics are context and are
  not credited to AgentProf.
- Atomic scoring is a necessary strong baseline because it already wins on
  AgentProcessBench MAP; omitting it would bias the comparison.
- Session organization is appropriately a control rather than a third headline
  baseline.
- A single analysis adapter is acceptable because it only joins retained
  outputs and invokes standard/official scoring; no toy agent or synthetic
  benchmark replaces the real workloads.
- No additional Work@ thresholds, reader study, benchmark, localizer rerun, or
  hierarchy tuning is warranted.

### Round-1 completion

Both blockers were repaired in `experiment-plan.md`. The revised plan requires
follow-up review before preflight.

## Round 2 — Follow-Up Verification

**Reviewed:** 2026-07-17T04:35:00-07:00
**Reviewer:** same independent subagent, read-only follow-up
**Verdict:** **PASS**

The reviewer verified both Round-1 repairs:

- Recall@20 uses exact `K = ceil(0.20 * n)`, analytic tie-averaged expected
  recall, cutoff-tier size, and attainable best/worst bounds. Source order is a
  sensitivity only.
- Official/source-native clean errors are separated from explicitly project-
  defined support-propagation controls; the latter are no longer labeled
  official, native, or benchmark-defined FPRs.

No remaining result-invalidating scientific or executability defect was found.

Two nonblocking implementation notes remain:

1. interpret “material” clean propagation conservatively from the observed
   effect and uncertainty rather than inventing an unregistered pass threshold;
2. in real preflight, prove that the HINT adapter invokes the unchanged official
   scoring functions and reproduces their output on retained records.

The plan converged after one repair round and one follow-up. A third review is
unnecessary and would violate the instruction not to rereview an approved plan
without new evidence.

## Final Plan Verdict

**APPROVED FOR REAL PREFLIGHT.**

The approval covers exactly the experiment in `experiment-plan.md`: retained
predictions and profiles, three complete public workloads, official signal
metrics, standard MAP/AP, one tie-correct fixed-budget recall metric, and clean
support-propagation controls. It does not authorize a new model run, hierarchy
change, localizer redesign, algorithm change, or story/RQ change.

## Round 3 — Real-Preflight Deviation Review

**Reviewed:** 2026-07-17T04:44:28-07:00
**Reviewer:** same independent subagent, read-only follow-up
**New evidence requiring review:** the real preflight found that HINTBench's
downloaded evaluator reads `injected_risks` and an eleven-name taxonomy while
the released test records contain `risk_labels` from a five-constraint
snapshot. Directly applying the downloaded typed evaluator therefore produced
a spurious zero localization F1.
**Verdict:** **PASS**

The reviewer independently checked the repaired path against HINTBench's
published Appendix-B protocol and the retained artifacts:

- Binary risk detection keeps the released parser and source-native
  `is_risky` confusion logic.
- Standard step-set precision, recall, and F1 use the released `risk_labels`
  target steps. Maximum one-to-one overlap implements the paper's published
  no-type localization protocol, which ignores type and matches by step
  overlap.
- Typed localization and strict typed-set accuracy are correctly reported
  `N/A`; either would require an unsupported mapping between incompatible
  taxonomy snapshots.
- Parse status and predicted step sets match the retained outputs on all
  `536/536` records.
- AgentProcessBench completes all 20 judges across four datasets, and
  TraceElephant completes all 220 official evaluations. The full-population
  path and 10,000-bootstrap analysis remain executable.
- The repaired real preflight completed within the maximum of three attempts.

No result-invalidating scientific or executability defect remains. The repair
changes neither the RQ, tested hypothesis, retained predictions, profile
organization, baselines, nor metric meaning; it prevents an incompatible
released taxonomy snapshot from being misreported as a typed result.

## Final Plan Verdict After Real Preflight

**APPROVED FOR FULL RUN.**

Approval remains limited to the unchanged experiment plan and the documented
HINTBench no-type protocol repair. It does not authorize a new model run,
profile or hierarchy change, localizer redesign, algorithm change, or paper
story/RQ change.
