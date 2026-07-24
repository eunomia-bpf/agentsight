# Experiment Plan: Separate Tool Question — Measurement Capability

## Research Question

- **RQ exactly as written in the paper:** Given the same frozen native evidence
  and an independent source-explicit oracle, which action-only,
  artifact-linked, cross-session, and final-state facts can Final State,
  Counts, ProcGrep, bounded raw-log model analysis, and artifact-linked
  trajectories answer correctly, and at what evidence and inference cost?
- **Specific uncertainty tested here:** Whether stable artifact identity and
  session lineage provide correct, source-verifiable process facts beyond an
  action-only procedure spine, and whether a fixed model can reconstruct the
  same facts directly from complete native records at comparable correctness
  and cost.
- **Why the answer matters:** The six-project study measures process phenomena,
  but the tool contribution requires evidence that another Agent can recover
  those facts without treating the trajectory implementation as its own truth.

## Paper-Value Admission

- **Planned role:** decisive for the narrow tool claim; independent of RQ1--RQ6.
- **Largest credible paper story:** workspace-linked trajectories preserve the
  action facts of an established action-only representation while adding
  independently checkable artifact and cross-session fact coverage.
- **Strongest reject argument addressed:** the method is a restatement of
  counts/ProcGrep, or a capable model can reconstruct the same process facts
  directly from native logs without a trajectory representation.
- **Independent evidence added:** a common 120-question denominator, two
  source-direct oracle implementations, official ProcGrep, and three complete
  raw-log model repetitions per project.
- **Why the result is not tautological:** questions and answers were frozen
  from native bytes and cutoff workspace state before any compared method ran;
  the trajectory output cannot select or label questions.
- **Paper decision if positive:** retain only the incremental artifact/session
  fact-coverage claim. Add an efficiency claim against Raw only if the
  predeclared accuracy-parity gate passes.
- **Paper decision if mixed or negative:** report the family boundary, an
  efficiency-only tie when warranted, or remove the tool claim. Descriptive
  RQ1--RQ6 results remain unchanged.
- **Best alternative:** another observational correlation over the six
  projects. It has lower decision value because it cannot answer whether the
  representation is useful to an automatic consumer.

## Expected And Alternative Outcomes

- **Current expected answer:** Counts and ProcGrep tie on eligible action facts,
  Final State answers cutoff-state facts, trajectories add artifact and
  cross-session coverage, and Raw is either less exact or more expensive.
- **Strongest competing explanation:** the model reconstructs all B/C facts
  from native records at comparable cost, leaving no need for the representation.
- **Contradictory result:** the trajectory fails its action-preservation or
  correctness veto, adds no B/C coverage over ProcGrep, or loses to Raw.

## Published Precedent And Real Assets

- **Closest published protocol:** ProcGrep's episodic-search comparison of
  deterministic structural queries and model readers over trajectory questions.
- **Source assets:** official ProcGrep commit
  `2e8277003dacaa774b5ef61ba150ae03a4f06693`; 72 complete Claude, Codex, and
  Gemini session files from six repositories and their workspace cutoff
  manifests; Codex CLI `0.145.0`; `gpt-5.6-terra`, medium reasoning. The exact
  source bytes and cutoff state are reused, but all questions are rederived
  after excluding redirect/heredoc shell segments.
- **Historical input:** the Step 0003 plan at
  `docs/tmp/build-and-evaluate/step-0003-20260722T142124-0700/experiment-001/plan.md`
  (SHA-256
  `1519eb2259d1dba22bb27679edd77bd76061ca2c707b05c285a17809c540e2f2`)
  supplies provenance only; its checker and post-review Raw transport are not
  treated as approved evidence.
- **Necessary glue:** a separate source-direct checker that imports neither the
  primary script nor `agent-session`, corrected shell-path exclusion, and a
  Bubblewrap filesystem boundary for Raw. No new production IR, database,
  frontend, semantic labeler, or human annotation is introduced.

## Comparison

- **Proposed method:** official ProcGrep atoms plus deterministic
  `agent-session` artifact effects, stable worktree/path identity, explicit
  rename lineage, source-session identity, and cutoff-state linkage.
- **Main baseline 1:** official pinned ProcGrep, representing the strongest
  action-only procedure account.
- **Main baseline 2:** bounded Raw-log model analysis, representing on-demand
  reconstruction from the complete same-source records.
- **Controls:** Final State and aggregate Counts.
- **Fairness:** all methods use the same selected sources, path bindings,
  question semantics, and 120 questions. Raw receives complete native records
  and the answer-free measurement specification, but no oracle answer,
  normalized rows, ProcGrep atoms, trajectory index, or outside access.
- **Compute contract:** one 20-question model call per project/repetition,
  three repetitions, medium reasoning, 64 local retrieval calls, 1 MiB returned
  tool bytes, 64 KiB output, and 15 minutes maximum per call. Bubblewrap mounts
  only system executables/libraries, a fresh temporary home containing the
  authentication file, the evidence directory at `/work`, and the result
  directory at `/out`; `--unshare-pid` replaces host `/proc`, `--clearenv`
  removes inherited variables, and repository parents and oracle files are
  absent.
- **Leakage rule:** any outside access, cap violation, malformed output, or
  timeout becomes a retained 20-question abstention cell; no retry or
  majority vote.

## Workloads And Metrics

- **Workloads:** six fixed real repositories, 12 closed native sessions per
  repository, and 20 fixed questions per repository: five action-only (A),
  five artifact-linked (B), five cross-session (C), and five final-state (D).
- **Ground truth:** the primary source-only enumerator is checked by a separate
  standalone Python implementation that imports neither the primary script nor
  `agent-session`. It reopens all native records, rebuilds vendor tool calls,
  action atoms, paths, generations, session order, P0--P4 selection, and all
  A--C answers. For D, it derives tracked/untracked/absent from the archived
  index entry and presence bit, verifies the indexed path/stage and archived
  content blob hash, and never reads the primary `status` as truth. Any anchor
  or answer mismatch stops before a compared method runs.
- **Primary metric:** exact correct factual coverage on the common denominator.
- **Secondary metrics:** wrong, abstain, conditional exact accuracy, input and
  returned bytes, tokens, calls, wall time, and peak RSS.
- **Primary contrasts:** Trajectory minus ProcGrep B+C coverage; Trajectory
  minus mean Raw B+C coverage; Raw/Trajectory wall-time only under the frozen
  symmetric ±0.05 accuracy-parity gate.
- **Uncertainty:** 10,000 seeded project-block/hierarchical bootstrap draws
  over the six fixed cases; intervals are corpus sensitivity, not population
  estimates.

## Planned Runs

| Run group | Role | Workload | Method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| rederive | dependency | same archived 72 sessions and cutoff state | corrected primary + independent source-direct oracle | 1 | Any mismatch stops |
| preflight | real mechanism check | smallest-source project, all families | all five conditions | 1 | Must engage a real Raw retrieval |
| full | comparison | six projects × 20 questions | deterministic conditions | 1 | Exact common denominator |
| full | comparison | six projects × 20 questions | Raw model | 3 | Mean score; no vote |
| score | inference | all retained rows | frozen scorer | 1 | Applies predeclared vetoes |

## Execution

- **New experiment boundary:** Step 0003 remains closed and invalid for an RQ
  result. This step is a new experiment because it changes the oracle checker,
  removes false shell artifacts, rederives questions, reviews the retrieval
  Raw baseline, and isolates its filesystem. The three-attempt limit from the
  superseded experiment does not carry over.
- **Reader selection before answers:** the initially registered
  `gpt-5.6-sol` reader produced no final answer in three transport attempts:
  missing resolver mount, a monitor false positive on jq `//`, and then a
  900-second no-first-token timeout after DNS/network isolation checks passed.
  No attempt produced a scoreable answer. Before observing any Raw accuracy,
  the fixed reader is therefore changed once to `gpt-5.6-terra` at the same
  medium reasoning and budgets. One Terra mechanism preflight is allowed. A
  failure closes the model baseline as unavailable; no further model, effort,
  timeout, corpus, question, or budget substitution is allowed.
- **Rederivation:** run `rq7_measurement.py rederive-freeze` from the immutable
  Step 0003 source archive into this step's ignored private directory. It
  reuses the same 72 source files and cutoff workspace blobs, recomputes every
  action/relation/question, and stops if corrected P0--P4 require a different
  workspace cutoff.
- **Integrity:** verify the parent source-archive manifest before rederivation,
  then verify the new `private/audit-manifest.sha256` and source-direct
  `oracle-check.json`.
- **Preflight:** run `rq7_measurement.py preflight --model gpt-5.6-terra
  --reasoning medium` with this step's corrected private corpus and
  `preflight/` release path.
- **Full run:** run `rq7_measurement.py full` with three repetitions. The
  existing per-project/repetition `scored.json` checkpoint is the only resume
  mechanism.
- **Score:** run `rq7_measurement.py score`, writing sanitized CSV/JSON,
  `result.md`, and PDF/PNG figures into this experiment.
- **Completion rule:** 480 deterministic rows, 360 Raw rows, 24 cost rows,
  every terminal status retained, all source hashes valid, and an independent
  result review.
- **Private raw path:** this experiment's ignored
  `private/{preflight,full}/` directory.
- **Release path:** this experiment's `preflight/`, `raw/`, `figures/`, and
  `result.md`.

## Interpretation

- **Positive:** trajectory passes action and accuracy vetoes and its B+C lower
  interval over ProcGrep is above zero. Raw comparison is stated separately.
- **Negative:** failed veto, no incremental B+C coverage, or Raw win removes
  the capability claim.
- **Mixed:** family-specific or accuracy/cost trade-offs are reported without
  a scalar “understanding” score.
- **Target figure:** exact correct/wrong/abstain coverage by method and fact
  family, alongside measured per-question cost.

## Reproducibility Notes

- Repository HEAD before execution: `56fc7d6d8`.
- Parent script SHA-256 before the reviewed repairs:
  `7d19551bcc223db0dfdbc51ccbd8b8970cd2d23e2ecfa2ea52ea81e4a7f81b88`.
- Parent corpus SHA-256:
  `d5d6212d5820bb7383cd2b91427a038fdc55ee795aeac8156da18b8d90f73800`.
- Parent oracle-question SHA-256 (invalidated by shell-path correction):
  `fc8d1aabbc4e5c6fb9f4bde6dae3e77ae5dfc7d6d146f751c33ae5da1ecb58c6`.
- The reviewed preflight records final script, corrected corpus, checker, and
  question hashes. After preflight starts, no rederivation, re-freeze,
  question edit, or contract change is allowed; a defect stops rather than
  substituting data.
