# Fresh Plan Review: Randomized Workspace-Trajectory Supervision on SWE-INTERACT

Reviewed: 2026-07-21
Round: 1 of at most 3
Reviewer role: fresh, read-only experiment-plan reviewer
Verdict: **BLOCK**

## Bottom line

The proposed truth contract is scientifically preferable to human or Agent
diagnostic gold.  The final DeepSWE/SWE-bench Pro executable reward can be the
sole primary outcome; the GPT simulated user is part of the stochastic task
environment, not an outcome judge.  A static inspection of the pinned release
also supports the prospective RF exclusion: the 25 RF final scripts contain
the model-rubric path, while the 50 selected DeepSWE/SWE-bench Pro final scripts
do not.  The task allocation matches the stated SHA-256 rule, has no duplicate
task, and the current arithmetic is internally correct: 24 x 2 x 4 = 192 RQ1
trials, of which 24 P1 No-op trials are currently reused, plus 8 excluded P0
trials.

The plan is nevertheless not executable or unbiased as written.  Two promised
paths are incompatible with the pinned code, the main-run engagement rule
creates post-randomization exclusion, P1 makes one arm run in a distinct time
period, and the one-session checkpoint may expose no substantive trajectory
relation at all.  These are result-validity defects, not optional polish.

## What is already acceptable

1. **No human/Agent gold is required.**  The official executable final reward
   is independent of Agent Nebula's own relation output.  The simulated user
   affects the trajectory but does not label success.
2. **The intervention point is structural.**  The boundary after `01_plan` is
   defined by SWE-INTERACT before outcomes and starts a fresh worker over a
   persistent workspace.
3. **Independent prefixes can estimate an average randomized effect.**  Exact
   checkpoint forking is not required.  With prospective arm assignment and
   balanced order, independent user/worker prefixes are randomized task
   variation.  The estimand must continue to be described as an average over
   independent official trials, never as a same-prefix counterfactual.
4. **Raw versus Trajectory can be information-fair.**  Giving Trajectory
   deterministic conveniences over exactly the same Raw membership is the
   intended mechanism, not extra evidence, provided membership hashes and all
   returned-byte/token limits are enforced.  Its additional tool-schema tokens
   should be reported rather than artificially refunded.
5. **RF exclusion is adequate for the primary claim.**  Retain a hash inventory
   of all 50 eligible final verifier scripts and the negative model-provider
   scan; do not generalize the result to RF.

## Round-1 mandatory repairs

### 1. Make main-run analysis intention-to-treat; never drop a block because a supervisor failed to engage

The current rule says a failed Generic/Raw/Trajectory engagement invalidates an
entire affected task-wave block.  Engagement is observed after assignment and
is partly caused by the assigned method.  Dropping all four outcomes when the
Trajectory supervisor fails to call a useful relation conditions the analysis
on treatment behavior and can turn method unreliability into favorable
missingness.

Repair:

- Keep strict family-specific engagement as a **P0 admission gate**.
- In the RQ1 matrix, analyze every assigned trial by intention to treat.  Freeze
  a continuation behavior now: an invalid/timeout/no-engagement supervisor
  produces no advice (or an empty neutral wrapper), the official worker still
  runs, and the final reward remains in the assigned arm.
- Report engagement/failure rates by arm.  An engaged-only analysis may be
  secondary and explicitly non-causal; it cannot replace the ITT result.
- Reserve retry/missingness only for failures outside the assigned mechanism,
  such as image transport or runner loss before any model execution.  A
  supervisor model/tool failure is not infrastructure missingness merely
  because it is inconvenient.

This repair also resolves the plan's contradiction: engagement failure cannot
both “reject H6” and make the experiment “inconclusive.”  P0 failure blocks the
experiment; main-run mechanism failure is part of the assigned method and can
make the method ineffective or the mechanism interpretation unsupported.

### 2. Separate headroom qualification from the randomized matrix, or remove it

P1 currently executes every wave-1 No-op before the other wave-1 arms and then
reuses those outcomes in the 192-trial matrix.  That makes time/order perfectly
correlated with No-op for half its observations.  Model service changes,
package drift, cache state, infrastructure load, and experimenter learning can
therefore contaminate every No-op comparison.  It also contradicts the promise
that execution order is randomized within each task-wave block.

Repair with one of these two choices:

1. Preferably remove P1 and justify headroom from the pinned benchmark/model
   evidence plus a prospective power calculation; or
2. keep the 24 P1 No-op trials as an **excluded qualification sample**, then
   run a fresh, fully order-randomized 192-trial RQ1 matrix.  The total becomes
   8 P0 + 24 P1 + 192 RQ1 = **224**, not 200.

If P1 remains, derive its threshold from the minimum effect the matrix is
powered to detect.  “At least 12 rewards below 1.0” is currently an arbitrary
cutoff.  A gate may stop an uninformative workload, but it may not select or
replace tasks, and its full fixed vector must still be reported.

### 3. Freeze an implementable randomization and concealment procedure

The design is unbiased in principle, but `allocation-manifest.json` contains
only task allocation.  It contains no arm/order seed, opaque-ID derivation, or
schedule commitment.  Also, because the arm is assigned before step 1 and only
revealed/activated later, this is more precisely **prospective randomization
with delayed activation**, not randomization performed after observing the
prefix.

Repair:

- Freeze one arm/order seed and exact permutation algorithm before P0.  Define
  `task_name` unambiguously as the dataset directory basename, which is what
  the current allocation actually hashes.
- Generate all task-wave opaque IDs, arm mappings, and within-block execution
  order before any corresponding block runs.  Store a commitment/hash in the
  experiment record and keep the mapping only in a host path unavailable to
  the task, worker, user-server, and supervisor.
- Ensure the decorator's `setup` and first `run` path are byte-for-byte
  condition-independent; it must not branch on the arm until the second
  top-level `run` call.  P0 should compare step-1 prompt, environment, network
  policy, worker version, tool configuration, and source-path inventory across
  arms.
- Freeze concurrency.  If the three supervisor arms share one local llama.cpp
  server, serialize those calls or use an explicitly balanced queue so arm is
  not confounded with contention or timeout.

No process checkpoint or encrypted control subsystem is needed; a small
host-only frozen mapping and a pre-run commitment are sufficient.

### 4. Prove that the one-session treatment contains a substantive relation, not merely a successful JSON response

The current pinned implementation cannot consume the planned checkpoint:

- `agentvis/src/research.rs:368-380` rejects a Harness-style store with fewer
  than two completed rounds.
- `research-supervisor --verify-only` indexes two scopes for `session_diff`.
- `agentvis/src/research.rs:926-983` deliberately assigns no effects to ordinary
  shell tools.  SWE-INTERACT step 1 explicitly forbids implementation edits
  (`01_plan/instruction.md:5-7`), while Codex normally explores with shell
  commands.  A step-1 store can therefore contain many Raw actions but zero
  observed action-to-file effects.
- The existing engagement counter only checks that a relation response exposed
  some registered source ID (`research_supervisor.rs:40-68`).  An `effects`
  response with zero effects but Raw IDs can satisfy that check.

Repair:

- Explicitly extend the existing store/broker to support exactly one completed
  scope; do not create another IR.  At this checkpoint, omit `session_diff`
  from the active tool schema or declare it an untested/unavailable component.
  An always-empty tool is not evidence that cross-session differencing helped.
- Define a non-empty relation semantically.  For this experiment it must expose
  at least one ordered, source-linked action-to-workspace-path relation (for
  example a non-empty `artifact_history.actions` or `effects.effects`), not
  merely a snapshot row, action Raw ID, or syntactically non-empty object.
- P0 must retain counts of actions, actions with path effects, unique affected
  paths, non-empty relation calls, and relation-returned source IDs.  Trajectory
  passes engagement only after using such a relation.  If it intervenes, at
  least one cited advice source ID must come from the substantive relation
  response.
- If neither frozen P0 planning trace has a substantive relation, stop.  Do not
  loosen the definition or add a command-semantic guesser after seeing this
  outcome.  Either preregister source-linked shell/system-effect capture before
  P0 or choose a later source-native boundary that still permits a worker to
  change the executable outcome.
- Bound the resulting claim honestly: this checkpoint tests one planning
  session's action/artifact relations transferred to a fresh implementation
  worker.  It does not test `session_diff` across a long accumulated history.

**Do not repair this by moving the sole intervention to after `03_handoff` and
before `04_write_tests`.**  That location supplies three completed sessions,
but the remaining productive worker is instructed to add tests, not repair the
implementation.  More importantly, the official final wrapper identifies
`HEAD~1` as the implementation commit, captures the test commit separately,
then resets to the implementation commit before running the canonical hidden
tests.  Advice based on a richer three-session trajectory would therefore
mostly affect Agent-authored tests and handoff compliance, not the production
implementation being scored.  Authorizing production fixes in step 4 or
changing the commit/reset protocol would alter the official workflow and
oracle.  A three-session intervention at that point would test a different,
much narrower claim and is a **BLOCKED substitution** for H6 as written.

The defensible choices are: (a) retain the `01_plan`→`02_implement` boundary,
prove that its one-session action/artifact relations are substantive, and
narrow the claim accordingly; or (b) choose a different source-native
multi-stage benchmark in which several completed sessions precede a later
stage that is still authorized to change the scored artifact.  Session count
alone is not useful if the intervention no longer has a causal path to the
official outcome.

The current plan also requests 8,192 evidence tokens, 32,768 evidence bytes,
and 16 tool calls, while the pinned broker hard-rejects anything other than
16,384, 65,536, and 24 (`research_supervisor.rs:861-897`).  Choose one budget
set in the reviewed plan and make the broker's frozen validation agree before
P0.

### 5. Freeze the evidence allowlist and correct Generic current-state parity

For DeepSWE, the official current plan is `/tmp/plan.md`, outside `/app`;
SWE-bench Pro stores it at `/app/plan.md`.  Full Raw currently receives the
DeepSWE plan explicitly, while Generic only receives “the current workspace.”
That makes Generic systematically less informed in one family for a reason
unrelated to history or trajectory.

Repair:

- Treat the official plan artifact as current state in **all three supervisor
  arms**, regardless of its task-family path.
- Freeze one explicit source allowlist.  Current state should be extracted from
  the worker-visible repository plus the official plan artifact.  Historical
  Raw may add only the step-1 native Agent records, worker-visible step-1
  prompt/responses, `ask_user` questions/replies, and worker-visible timing/log
  metadata.
- Export only the user-facing `ask-user.jsonl` content.  Do not ingest the
  simulated user's private persona, private repository-tool calls/results, or
  event log.  The pinned user server explicitly keeps a private persona and
  private inspection tools (`server.py:37-49`).
- Never scan or mount the benchmark checkout itself: it contains `solution/`
  and `tests/`.  Exclude `.git`, `/tests`, task `solution/`, user-server private
  state, future step files, sibling outcomes, and credentials by construction,
  then audit the registered source paths and hashes in P0.
- Continue requiring identical Raw membership hashes for Raw and Trajectory.

This is not a privacy-redaction layer; it is the minimum experimental
information boundary needed to prevent oracle leakage and make the baseline
comparison interpretable.

### 6. Remove the impossible duplicate-regrade requirement and define terminal outcomes

P0 requires “a second official regrade” of an unchanged trial.  The pinned
Harbor documentation says regrade requires a completed single-step source and
that multi-step trials are unsupported (`docs/.../regrade.mdx:51-61`); the
implementation rejects any source trial containing `steps/`
(`src/harbor/trial/regrade.py:278-288`).  This requirement cannot pass.

Repair:

- Remove the duplicate official regrade criterion.  Retain the one official
  final result payload, the pinned verifier/task hashes, final artifact
  manifest, and reward-extraction path.  Do not patch Harbor or duplicate the
  canonical test inside the task merely to manufacture an “official regrade.”
- If deterministic replay is later needed, qualify it as a separate verifier
  capability on a benchmark that officially supports replay; it is not needed
  to answer H6 here.
- Define `Y` for every protocol-terminal trial before execution.  In
  particular, state how Harbor `None`/missing final reward caused by an Agent or
  simulator failure maps to the benchmark outcome (normally zero under the
  benchmark job metric), while genuine pre-execution infrastructure loss stays
  missing and follows the registered retry rule.  This must not be decided by
  arm after results are visible.

### 7. Add a prospective power/cost analysis and use repository-aware uncertainty

The plan has 24 tasks, two waves, two simultaneous directional requirements,
and a bootstrap-lower-bound requirement, but no minimum detectable effect,
power calculation, dollar/token estimate, or wall-time/concurrency budget.  A
rough worst-case calculation illustrates the risk: with binary independent arm
outcomes, two waves give at most approximately
`SE = sqrt(0.25 / 24) = 0.102` for a paired task-level contrast.  Requiring a
two-sided 95% lower bound above zero yields an approximately 0.29 absolute
effect for 80% power before accounting for the second required contrast.  A
plausible 5--15 point effect would be underpowered.

Repair:

- Before P0, simulate the exact blocked design under frozen baseline pass-rate,
  task/repository heterogeneity, two waves, the two registered contrasts, and
  the actual support rule.  State the smallest effect worth detecting and show
  at least 80% power for it, or change tasks/waves/support criteria before any
  outcome is observed.
- Report estimated worker calls, simulated-user calls, supervisor calls,
  tokens, dollar cost, wall time, and concurrency.  The current matrix implies
  960 worker sessions for RQ1 alone, plus simulated-user and supervisor calls.
- The sentence “task-balanced means so repeated repositories do not dominate”
  is false.  The frozen 24 tasks include repeated FastAPI, qutebrowser,
  OpenLibrary, and Teleport repositories.  Keep a task-population estimand if
  desired, but use repository-cluster uncertainty (with family retained) or
  explicitly limit inference to the finite frozen tasks.  Do not use a
  task-cluster bootstrap to claim repository-level generalization.
- Replace the task-hash v1 split with a **repository-disjoint v2 allocation**
  before any run.  Hash canonical repository identity first, assign whole
  repository groups to P0, RQ1, or holdout, and only then deterministically
  select tasks inside an assigned repository if a cap is required.  No
  repository may cross P0/RQ1/holdout.  The current split puts the P0
  OpenLibrary task in the same repository as multiple RQ1 tasks and also
  distributes repeated repositories across RQ1 and the advertised “untouched”
  holdout.  That permits repository-specific debugging/exposure to leak into
  later cells and makes the holdout an invalid independent confirmation set.
  Exact 12/12 task counts are less important than group-disjoint assignment;
  record any family/task imbalance and keep the primary estimator
  repository-aware.
- Bootstrap whole repositories, with both waves and all tasks from a sampled
  repository retained together.  A task bootstrap is not repaired merely by
  reporting repository names descriptively.
- Explain why the one-sided randomization test plus the 95% interval is the
  frozen decision rule.  Requiring both contrasts is an intersection-union
  claim and does not automatically require a multiplicity penalty, but the
  power analysis must evaluate the joint rule actually used.

### 8. Pin the worker binary and describe the real implementation delta

The official shell config pins the model name but not the Codex CLI.  At the
pinned Harbor revision, an unspecified version accepts any already-installed
Codex or installs `@latest` (`src/harbor/agents/installed/codex.py:93-130`).
Recording the observed version after a run does not prevent version drift
across 200+ long trials.

Repair:

- Pin the exact Codex CLI version in Harbor's agent configuration before P0 and
  require that version in every trial.  Also freeze the supervisor seed,
  llama.cpp/server argv, model hash, task image identifiers, and simulated-user
  configuration.  The user server has unseeded in-memory conversation state;
  require a fresh user-server process per trial and retain its user-facing
  transcript, while treating its randomness as part of the randomized trial.
- Replace “one decorator below 500 lines” with an honest implementation plan.
  The current store rejects one scope, the broker's frozen budgets disagree,
  the official plan artifact needs cross-family normalization, and the wrapper
  must capture step-1 logs before Harbor archives/resets them.  Fewer than 500
  changed source lines may still be possible, but it is a maintainability
  target, not a validity invariant.  Count all adapter and store/broker changes
  plus tests; do not hide required logic outside the count or build a second
  experiment-control framework to satisfy the number.
- Add one concrete end-to-end command and the expected output paths for P0 and
  the full matrix.  The plan currently describes components but not a runnable
  invocation or a cost-bounded execution schedule.

## Required plan revision before follow-up review

A follow-up can be accepted only if the same `plan.md` and manifest are revised
in one repair round to include:

1. ITT handling for main-run supervisor/engagement failures;
2. an excluded or removed P1, with corrected counts and a power-derived gate;
3. frozen arm/order seed, concealment path, concurrency, and schedule;
4. an executable one-scope store/broker contract and substantive-relation P0
   gate;
5. a source allowlist with the official plan visible to Generic and no private
   user/solution/test inputs;
6. removal of multi-step regrade plus a total terminal-outcome mapping;
7. prospective power, repository-aware uncertainty, and cost estimates; and
8. exact worker/runtime pins and one runnable command.

The revised allocation manifest must be a v2 repository-group allocation; the
current task-hash v1 manifest is not acceptable for an experiment that reserves
and later interprets a holdout.

No real benchmark or model call should begin before these repairs are reviewed.
No human or Agent annotation should be reintroduced: the executable benchmark
outcome remains the correct primary truth source.
