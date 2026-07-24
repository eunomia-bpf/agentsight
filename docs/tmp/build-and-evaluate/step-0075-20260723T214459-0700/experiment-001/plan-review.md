# Independent Plan Review — Step 0075 RQ4 End-to-End Accounting

**Review round:** 1  
**Method:** `research-experiment-design` PLAN REVIEW  
**Verdict:** **REVISE**

## Overall judgment

This is the right next RQ4 experiment and, after a small revision, is the
simplest useful way to close the paper's main cost-accounting gap. Measuring
the post-export path

`source adaptation -> annotation -> pprof materialization`

is scientifically meaningful, provided it is consistently called **offline
post-export first-profile construction**, not unqualified end-to-end profiling.
Excluding the original agent execution is correct. Excluding live capture is
also defensible for this experiment, but the paper must continue to say that
capture overhead is outside the measured boundary.

The shared real 405-session/20,866-operation population, current release
binary, stock-pprof readback, exact mass checks, and reuse of already completed
expensive inference are all appropriate. No new model, benchmark, frontend, or
algorithm is needed.

The plan is not yet executable as written because its A2 timing evidence cannot
support the proposed dominance decision, and the system-cost comparison lacks
the exact execution controls needed for a fair matched measurement.

## Blocking findings and must-fix revisions

### 1. Do not treat filesystem mtime as observed A2 annotation wall time

The current files have plausible historical timestamps:

- 41-session manifest: `2026-07-22 13:59:35 -0700`; final annotation batch:
  `14:08:38`;
- 364-session manifest: `2026-07-22 15:00:35 -0700`; final annotation batch:
  `15:45:54`.

Their manifest-to-last-batch spans sum to about 54 minutes. This is useful
historical provenance, but it is not an instrumented backend timer. Filesystem
mtime can be changed or preserved by copying, checkout, restoration, or
rewriting; the interval includes packet-to-worker dispatch, scheduling,
concurrency, idle time, and artifact writing; and it provides neither model
compute time nor provider usage. The two waves also produced A0 annotations,
whereas adopted A2 additionally applies the later deterministic root-prefix
repair and assembly. The proposed end timestamp therefore does not even cover
the complete adopted-A2 construction path.

Minimal repair:

1. Rename this quantity **historical artifact-time workflow envelope**.
2. Report each wave separately before summing, list all timestamp sources, and
   state that the timestamps are mutable filesystem metadata rather than an
   execution log.
3. Do not add this value to fresh `/usr/bin/time` components as though all were
   homogeneous stopwatch measurements.
4. Freshly time the deterministic annotation assembly, A2 root-prefix repair,
   validation, and mark materialization that occur after batch production.
5. Report A2 model/provider inference wall time and usage as **unavailable**.

The envelope may appear as bounded historical context. It cannot establish
that annotation was the largest measured component: a large upper envelope is
not a lower bound on annotation runtime. Therefore remove envelope-based
condition 3 from the support rule. If no immutable execution timestamps exist,
the honest result is: “A2 inference cost was not instrumented; the artifact
timeline spans X, including unknown orchestration and idle time.”

### 2. Pin one fair cost boundary for all methods

The comparison currently mixes:

- A2 packet export plus historical orchestration plus fixed-mark replay;
- recurrence applied with an already constructed reference corpus;
- raw action with no semantic constructor.

These are useful rows, but they are not interchangeable baselines.

Revise the roles and totals as follows:

- **A2** is the adopted automatic backend whose offline first-profile cost is
  being accounted for.
- **Recurrence** is the main low-cost automatic alternative. State explicitly
  that its reference corpus is a fixed backend asset: target-time loading and
  inference are included, while original reference-corpus creation is
  excluded. This must match the exclusion of model download/backend setup.
- **Raw action** is a serialization/folding lower-bound **control**, not a main
  semantic baseline.
- **Fixed A2 marks** are a replay/change-width **control**, not another
  automatic annotation baseline.

Define method totals from the same exported raw archives. Distinguish common
normalization from A2-only packet construction if the exporter performs extra
work for Agent packets. Do not charge an A2-specific packet cost to raw or
recurrence merely to make the table rectangular.

The 3B and 27B rows are not matched cost baselines: they use different
backends, timing semantics, and possibly hardware, and both were rejected on
quality. Keep them in a short “historical cost-quality context” paragraph or
appendix only. They must not enter the hypothesis, decision rule, or headline
table. No additional local-model run is needed.

### 3. Make the fresh measurements reproducible and sufficiently repeated

One source-adaptation run is insufficient for a paper-facing wall-time
measurement because deterministic output does not remove operating-system
timing variation. Run source adaptation three complete times, just like raw,
recurrence, and A2 replay, and report all observations plus median wall time
and maximum RSS. Three repetitions are adequate here; more are not required.
The single historical A2 annotation execution may remain a single observation
because rerunning it would change both cost and backend output.

Before execution, add:

- exact authoritative commands for source adaptation, raw action, recurrence,
  A2 assembly/repair, and fixed-mark replay;
- release version/binary hash, machine/CPU/RAM/OS, concurrency/thread settings,
  `/usr/bin/time` invocation, and cache/warm-up policy;
- exact raw-output directory and a completion rule requiring 405 sessions,
  17,148 turns, 20,866 operations, successful stock-pprof readback, and exact
  operation/token mass;
- one smallest real preflight invocation. Its timing is diagnostic and excluded
  from the full-run result.

These are normal reproducibility details, not a new harness or control
protocol. One small measurement wrapper remains acceptable.

### 4. Replace the vague and currently untestable decision rule

“Substantially smaller” is undefined, and “every component ... measured or
explicitly bounded” is too permissive to support the current hypothesis.

Use a claim matched to available evidence:

- primary result: a component table for post-export construction with
  independently timed source adaptation, deterministic A2 postprocessing,
  raw/recurrence construction, and A2 fixed-mark replay;
- supported replay claim: predeclare a numeric ratio, or simply test the
  directional statement that the median fixed-mark replay time is lower than
  the median fresh recurrence construction time and every measured
  deterministic first-construction component it is compared against;
- A2 annotation inference: explicitly **unmeasured**, with the artifact-time
  envelope reported only as historical workflow context.

If the intended claim specifically requires proving that A2 inference
dominates first-construction cost, this plan must be inconclusive because it
lacks a trustworthy A2 timer. Do not convert an upper envelope into that proof.
This limitation bounds only RQ4's adopted-backend timing evidence; it does not
challenge A2 quality or the paper thesis.

## Nonblocking observations

- Wall time, peak RSS, backend-reported token counts, output bytes, throughput,
  and exact additive mass are appropriate standard systems measurements. No
  custom scalar or new scientific metric is needed.
- Reusing independently reviewed RQ3 quality values is correct. Copy exact
  provenance, but do not recompute or optimize quality in this RQ4 run.
- The full CodeTrace population is sufficient. Do not add another benchmark,
  hardware matrix, pricing analysis, live-capture study, stability study, or
  new backend.
- The target paper artifact should be one compact component-and-quality table,
  not several independent experiments.

## Verdict

**REVISE.** The experiment is admitted as supporting, high-value RQ4 evidence,
but execution should wait until the plan (1) demotes mtime to a historical
artifact-time envelope, (2) times the missing deterministic A2 postprocessing,
(3) gives source adaptation three repetitions and pins exact commands/system
conditions, (4) labels recurrence, raw action, and fixed marks by their proper
roles, and (5) removes the unsupported inference-dominance decision. These are
minimal scope-preserving repairs; no new model run or broader experiment is
required.

---

# Round 2 — Convergence Review

**Verdict:** **REVISE**

Round 1's scientific issues are otherwise closed: mtime is now only a
historical artifact-time workflow envelope; A2 inference time and usage remain
unavailable; deterministic A2 postprocessing is measured separately;
recurrence is the main fixed-asset automatic alternative; raw action and fixed
marks are correctly controls; fresh deterministic components use three
repetitions under a declared host/cache policy; and the decision no longer
claims annotation-cost dominance.

Only the following blocking corrections remain:

1. **Make the declared start boundary match the source-adapter command.** The
   exporter does not begin from raw archives alone: it requires both
   `--raw-root` and the already normalized
   `a2-canonical-v1/profile-inputs/operations-count.jsonl`, then reconstructs
   source packets. Either include the authoritative raw-to-normalized operation
   command and its cost, or, as the minimal repair, rename the measured boundary
   to start from **fixed normalized target operations plus released raw
   archives**. Do not call the current exporter measurement complete
   raw-archive source adaptation.

2. **Complete the executable command matrix.** Add the missing fixed-mark token
   replay command using `operations-tokens.jsonl` and `--view tokens`; otherwise
   the required 494,862,929-token completion check has no planned producer.
   Also replace the source-adapter-only preflight with one real measurement
   preflight that exercises the fresh source-adapter, A2
   assembly/canonicalization, raw, recurrence, and fixed-mark command paths.
   It may use the already registered 41-session subset and remains excluded
   from paper timing.

3. **Keep the paper authorization consistent with the revised evidence.** The
   plan correctly says A2 annotation inference is unmeasured, but still
   authorizes WRITE to “replace the current statement that RQ4 excludes source
   adaptation and automatic annotation.” Change this to authorize measured
   source-packet adaptation, deterministic A2 postprocessing, and replay while
   continuing to state that A2 model/provider inference timing is excluded and
   only an artifact-time workflow envelope is available.

No new backend, workload, repetition, metric, hardware matrix, or model rerun
is needed. After these three textual/command corrections, the plan is ready
for execution.

---

# Round 3 — Final Convergence Check

**Verdict:** **APPROVE**

All Round 2 blocking issues are closed:

1. The measured boundary now honestly begins with fixed normalized target
   operations plus released raw archives, and explicitly excludes
   raw-to-normalized construction.
2. The fixed-mark token-width command is present, and the excluded 41-session
   real preflight exercises source-packet export, A2
   assembly/canonicalization, raw action, recurrence, and both fixed-mark
   replay widths with stock-pprof and mass checks.
3. WRITE authorization now covers only measured packet adaptation,
   deterministic postprocessing, and replay, while retaining the explicit
   exclusion of A2 model/provider inference timing and usage.

The fixed commands, paths, host/cache policy, three-repetition matrix,
completion checks, baseline/control roles, and decision rule are executable
and scientifically aligned with the declared offline post-export boundary.
No blocking issue remains. The plan is approved for real preflight and full
execution.
