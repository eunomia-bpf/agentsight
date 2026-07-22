# Experiment Plan: RQ1 Objective Continuation Utility

Created: 2026-07-21T02:14:26-07:00
Revised after independent review round 1: 2026-07-21
Status: independently reviewed and accepted for implementation; real P0 remains
blocked until `--prepare-only` passes
Gate: BOOTSTRAP / EXPERIMENT_GATE
Owner hypothesis: H6

## Research Question

- **RQ exactly as written in the current frontier:** Under fixed supervisor and
  continuation budgets, does Workspace Trajectory Retrieval produce
  interventions with higher objectively measured continuation utility than
  Full Raw Retrieval on persistent, multi-session benchmark tasks?
- **Specific uncertainty tested here:** whether direct access to ordered,
  source-linked artifact lifecycle and workspace transitions helps an automatic
  supervisor change a later worker's real outcome, beyond complete same-source
  Raw navigation, current workspace state, and an additional generic
  reflection/search pass.
- **Why the answer matters:** the previous label-based task could at best show
  agreement with a subjective diagnosis. This experiment asks whether the
  supervisor actually helps or harms a long-horizon Agent after the process has
  unfolded across sessions.

## Paper-Value Admission

- **Planned role:** decisive mechanism pilot. It can kill or justify scaling H6,
  but the six-task Harness Bench pilot alone cannot support a cross-domain AAAI
  generalization claim.
- **Largest credible paper story this experiment could unlock:** process-level
  scalable oversight for long-horizon Agents, evaluated through realized
  intervention utility rather than semantic judge labels.
- **Strongest reviewer reject argument addressed:** a trajectory interface may
  merely make another inference/search pass look useful, or may expose facts
  that the Raw baseline cannot retrieve. The plan therefore includes
  same-source Full Raw, generic current-state reflection/search, no intervention,
  executed continuation forks, exact resource ledgers, and official outcomes.
- **Independent evidence added:** actual counterfactual continuations from one
  frozen workspace checkpoint under alternative automatic interventions. No
  previous local run called a supervisor or changed a worker outcome.
- **Why not tautological or already settled:** selective reminders, harness
  optimization, trajectory reuse, and causal replay are prior art. The open
  question is the incremental realized utility of exact cross-session workspace
  evolution over a complete, equally budgeted Raw interface.
- **Paper decision if positive:** admit a separately reviewed coding plus
  scientific-work study using SWE Context Bench/SWE-Interact and CORE-Bench,
  retain automatic intervention utility as the central AAAI claim, and then
  test component ablations.
- **Paper decision if contradictory:** if Raw, generic reflection, or no
  intervention matches or beats Workspace Trajectory, reject the stronger
  representation claim. Retain only an efficiency claim if Trajectory ties Raw
  with materially lower retrieval cost and no extra harm.
- **Paper decision if inconclusive:** do not tune queries on inspected outcomes.
  Qualify a larger objective workload only if the pilot is variance- or
  power-limited and the mechanism checks pass.
- **Best alternative:** retrospective classification on public trajectories is
  cheaper, but it requires human or model labels and cannot establish that a
  recommendation changes the worker's outcome. The present experiment has
  higher decision value.

## Expected And Alternative Outcomes

- **Current expected answer:** Workspace Trajectory modestly improves official
  outcome over Full Raw at the same supervisor budget by making cross-session
  state changes and artifact continuity easier to retrieve; it also abstains
  safely when no supported advice is available.
- **Strongest competing explanation:** the current workspace and next official
  prompt already contain everything useful, so generic reflection performs as
  well; alternatively a capable Raw supervisor reconstructs the same relations.
- **Contradictory result:** Workspace Trajectory has no task-balanced outcome
  advantage over Raw, its gain does not exceed generic current-state reflection,
  or it raises the intervention harm rate.

## Published Precedent And Real Assets

- **Closest protocols:** REFLECT for intervention/replay;
  Remember When It Matters for a separate Agent that injects selective
  trajectory-grounded reminders; RHO for label-free harness improvement; and
  Rethinking Harness Evolution for matched search/feedback budgets and held-out
  evaluation.
- **Official benchmark:** Harness Bench
  `Qihoo360/harness-bench` revision
  `1025086a446653702b80cfb48babbeec35db6b2c`.
- **Official worker:** Codex CLI `0.144.6`, model `gpt-5.6-sol`,
  `model_reasoning_effort="medium"`, invoked through the benchmark's official
  Codex adapter. Every prompt round is a fresh `codex exec` over the same
  workspace.
- **Supervisor:** Qwen3.6-27B Q4_K_M at Hugging Face snapshot
  `b19fa7e8538a1a5f66452eb3b3167e026177be1d`, blob SHA-256
  `f7da7eee0f1ffa280742a293f02052d1f58d3253c9e109c1be8fb0067eb1b3a9`,
  through llama.cpp revision
  `2d973636e292ee6f75fadcf08d29cb33511f509f`.
- **Reused unchanged:** task YAML, fixtures, hooks, official round prompts,
  official Codex adapter behavior, and `oracle_grade.outcome_score`.
- **Necessary thin glue:** one standard-library Python driver imports the pinned
  Harness Bench modules, snapshots the workspace after every prefix
  `after_round`, pauses before the final round, restores each condition into one
  stable execution slot, invokes a repaired Rust research broker, runs the final
  official adapter round, invokes the final hook/cleanup, and calls only the
  unmodified executable oracle. No new general event IR, benchmark schema,
  semantic scorer, or third-party dependency is allowed.

## Implementation Admission Contract

The current research-only Rust path is **not** conforming and cannot be used for
a real call yet: it has only Raw/Trajectory conditions, the superseded
pathology output, `goal_diff`, old two-scope capture inputs, and different
hard-locked budgets. Before P0, the existing `research-store` and
`research-supervisor` code is minimally refactored rather than wrapped in a
second abstraction:

1. `research-store` accepts an explicit Harness checkpoint directory containing
   sanitized prefix sessions, prior official prompts and worker-visible logs,
   plus one immutable workspace snapshot/manifest per completed round. It
   writes the existing Raw record/store representation with arbitrary
   round/session scopes; it does not introduce another IR.
2. `research-supervisor` accepts exactly `generic`, `raw`, or `trajectory`.
   Generic exposes current-workspace list/read/search only. Raw exposes the
   complete allowlisted source store. Trajectory adds only
   `artifact_history`, snapshot-derived `session_diff`, and native
   source-linked `effects` over the identical Raw membership.
3. The only admitted output is the `INTERVENE|ABSTAIN` JSON object in this plan.
   The old pathology schema and `goal_diff` are unavailable on this experiment
   path.
4. One shared frozen argument validator enforces the model, seed, context,
   evidence, tool-call, response, and timeout values in this plan for all three
   supervisor conditions.
5. `harnessbench_intervention.py --prepare-only` makes no model or benchmark
   call but must actually construct the store, validate every snapshot, render
   the final prompt, start and health-check all three broker configurations,
   issue deterministic schema/tool dry requests, and prove that the broker
   argv and hard locks match this plan. Hashing source files alone is not a
   successful prepare check.

Any failure in these five points blocks P0. This adapter is research-only and
thin: it translates pinned Harness Bench round artifacts directly into the
existing store and official runner/oracle calls.

## Experimental Unit And Checkpoint

One block is an independently generated prefix checkpoint for one official
multi-round task:

1. copy official fixtures and run every round before the last with the official
   Codex adapter;
2. immediately after **each** prefix `after_round`, store an immutable workspace
   snapshot. Its manifest records every relative path's `lstat` type, mode,
   `mtime_ns`, size, symlink target, and content SHA-256, including directory
   metadata and deleted paths relative to the prior snapshot;
3. after the penultimate `after_round`, freeze sanitized native Codex session
   files, prior prompt bytes, worker-visible adapter logs, model/config hashes,
   the immutable round snapshots, and benchmark task identity as the supervisor
   evidence checkpoint;
4. separately freeze the worker execution checkpoint. It contains the current
   workspace and a minimal sanitized `CODEX_HOME`, but no evidence database,
   benchmark checkout, ground truth, oracle, credentials copied into evidence,
   or sibling outcomes;
5. render but do not execute the unchanged final official prompt against one
   stable worker-visible path; assign four random opaque condition IDs whose
   mapping is retained outside every worker/supervisor-visible path.

Conditions execute sequentially in the same stable host slot. Before each
condition, the driver removes the prior slot, restores the exact frozen worker
checkpoint while preserving metadata, and verifies the complete manifest.
Inside the worker tool sandbox, the slot, sandbox, prompt and sanitized Codex
home are always `/workspace`, `/sandbox`, `/prompt`, and `/codex-home` (or one
equivalent frozen set proven byte-identical by P0). After a condition terminates,
its output is archived under an opaque external path and the stable slot is
restored for the next condition. Thus host fork-directory names never enter the
official prompt, argv, environment, tool output, or filesystem.

Before any supervisor call, all four logical forks must have identical complete
manifests, prompt bytes, argv, and environment allowlists. The next official
prompt is visible to every supervisor condition. Future prompts, benchmark
ground truth, oracle code/results, repaired siblings, and another condition's
advice or outcome are never visible.

## Proposed Method And Comparisons

### Main proposed condition: Workspace Trajectory Retrieval

The supervisor receives current workspace tools plus the same complete Raw
tools below and three deterministic, source-linked conveniences over prefix
sessions:

- `artifact_history(path)` for ordered reads/mutations/renames/deletion and
  supporting Raw IDs;
- `session_diff(from_session, to_session)` for exact added/removed/changed
  artifacts recomputed only from the two immutable post-round snapshots and
  their supporting Raw IDs; and
- `effects(action_id)` for native observed effects and explicit `unknown`
  effects.

There is no pathology, hotspot, importance, recurrence, validation, intent,
or generated summary query. Every returned relation cites Raw IDs.

### Strongest main baseline: Full Raw Retrieval

The supervisor receives the same current workspace tools and complete prefix
evidence through:

- `list_sources()` and exact metadata/path/time filters;
- frozen lexical `search(query, source_types, k)`;
- `read_record(raw_id, offset_bytes)`; and
- `read_range(source, start_raw_id, end_raw_id)`.

All sanitized native session JSONL, official prior prompts, worker-visible
adapter logs, and immutable round snapshot bytes/manifests belong to the Raw
universe. The allowlist excludes Codex auth tokens, credentials, user/global
config, MCP/plugin secrets, benchmark source, task internals, ground truth,
hooks, oracle, and any future or sibling artifact. No allowlisted record is
removed because it appears irrelevant. Raw responses expose the same stable
action IDs and snapshot IDs used by Trajectory.

Raw requires a matched run rather than citation because the claim is the
resource-bounded value of direct relations, not the existence of information.
If Raw matches or wins, the stronger epistemic claim fails.

### Controls

1. **Generic current-state reflection/search.** The same supervisor sees the
   next official prompt and exact checkpoint filesystem through list/read/search
   tools, but no prior session records or derived trajectory relations. It has
   the same model, system prompt, message schema, context/output limit, tool-call
   ceiling, timeout, and evidence-byte/token ceilings. This tests whether an
   additional planning/validation pass over current state explains the gain.
2. **No intervention.** The fork receives only the unmodified official final
   prompt and runs the same worker. It establishes realized benefit and harm.

Final State, Counts, State Diff, summaries, AgentTether, OCPM, and HTIR are not
additional main rows in this pilot. They are later compatible controls only if
the Raw-versus-Trajectory effect warrants mechanism study.

## Supervisor Output And Injection

All three supervisor conditions return exactly:

```json
{
  "decision": "INTERVENE or ABSTAIN",
  "message": "bounded worker-facing advice",
  "source_ids": ["zero or more retrieved source IDs"]
}
```

`message` is at most 512 model tokens and must not contain condition names,
benchmark paths, oracle language, or unverifiable claims. `ABSTAIN` requires an
empty message. Source IDs are a provenance constraint and are not scored as
semantic gold. Valid advice is appended verbatim inside a neutral
`<automatic_supervisor_advice>` block after the unchanged final official
prompt. The generic, Raw, and Trajectory conditions use the same wrapper. The
no-intervention fork has no wrapper.

## Information, Compute, And Leakage Fairness

- Generic, Raw, and Trajectory use the same supervisor weights, decoding,
  prompt, output schema, 65,536-token context, 2,048-token model-output cap,
  16,384 returned-evidence-token cap, 65,536 returned-evidence-byte cap,
  2,048-token/8,192-byte per-response cap, 24 tool-call ceiling, and 20-minute
  timeout. Tool schemas and envelopes consume the rendered context budget.
- Supervisor decoding is temperature 0, top-p 1, seed 20260721, and
  `enable_thinking=false`. Actual tokens, bytes, calls, and time are reported;
  no condition is credited for unused budget.
- Raw and Trajectory have identical source membership and current-workspace
  access. Trajectory's additional schemas consume its own context budget.
- The worker configuration, final prompt, fork bytes, environment, timeout,
  stable visible paths, and remaining round count are identical. Fork execution
  order is randomized within a frozen execution wave and the mapping is
  concealed from the worker.
- Trusted Codex controller/model transport remains available, but every
  model-generated tool runs with `--sandbox workspace-write`, strict sanitized
  config, no web-search feature, no MCP/plugins/hooks, and
  `sandbox_workspace_write.network_access=false`. The same policy is exercised
  directly through `codex sandbox --sandbox-state-disable-network` during P0.
  A surrounding mount namespace exposes only the stable workspace, sandbox,
  prompt, sanitized Codex home, and required system binaries/libraries. It does
  not mount Harness Bench source, task YAML, `ground_truth.json`, hooks, oracle,
  other conditions, or the evidence store.
- P0 must demonstrate from the **actual worker tool context**, under the exact
  production config, that DNS resolution, GitHub, raw GitHub, and an unrelated
  public endpoint are unreachable, while a real Codex model turn still succeeds
  and its tool can read/write the workspace. Controller transport is not treated
  as arbitrary Agent-tool egress.
- The supervisor has no shell or arbitrary-file tool; the broker exposes only
  the declared source store and current checkpoint.
- The official oracle runs outside the worker namespace after completion. Its
  numeric result is rerun once on the unchanged final fork; disagreement is a
  hard failure.
- Task 007 is excluded because it explicitly tests one conversation's memory.
  Tasks 008 and 013 and any task with nonzero `outcome_llm_weight` are excluded
  because an LLM judge would enter the primary outcome.
- The driver calls only Harness Bench's official `run_oracle`/
  `score_workspace` executable-outcome path. It never calls `compute_scoring`,
  a task/process rubric, or a rubric provider. P0 records zero rubric/provider
  requests and verifies `outcome_llm_weight == 0` for every selected task.

The fixed 16,384-token evidence point is a mechanism-pilot operating point, not
a robustness claim. A later headline experiment must include budget curves.

## Workloads And Metrics

### Development preflight

The first checkpoint is Harness Bench task
`058-multiday-project-state` after Day 2 and before Day 3. It has two completed
fresh Codex sessions, one persistent workspace, a third official continuation,
and a deterministic outcome with zero LLM blend.

To avoid admitting a ceiling-limited matrix, run exactly one no-intervention
development checkpoint for **each of the fixed six tasks**, in the listed order,
without generating or inspecting any intervention. The full four-condition
matrix is admitted only if at least four of six no-intervention scores are below
`0.95`. Otherwise Harness Bench is retained only as a mechanics/feasibility
asset and no superiority pilot is run. These six development checkpoints are
permanently excluded from effect estimates. Intervention outcomes are never
used to select the task list, headroom threshold, or retrieval queries.

### Conditional six-task pilot

If the reviewed preflight passes, run five independently generated prefix
blocks for each of exactly six tasks:

- `057-interruption-resume`
- `058-multiday-project-state`
- `059-event-update-replan`
- `060-task-cancellation-cleanup`
- `103-policy-update-replan-diff`
- `105-partial-batch-resume-ledger`

This yields 30 checkpoint blocks and 120 continuation forks. Five is a fixed
exploratory repetition count chosen to estimate within-task stochasticity at
bounded cost; it is not a powered population sample. No failed or ceiling task
is removed after outcomes are seen.

### Metrics

- **Primary:** task-balanced checkpoint-matched official outcome difference
  `mean_task(mean_block(Y_trajectory - Y_raw))`.
- **Mandatory competing contrast:** task-balanced
  `Gain(trajectory) - Gain(generic)`, where
  `Gain(x) = Y_x - Y_no_intervention` within the same block.
- **Safety:** harm rate and mean negative change versus no intervention for
  each supervisor condition.
- **Calibration:** realized gain for `INTERVENE` versus `ABSTAIN` blocks and
  abstention rate.
- **Efficiency:** supervisor/worker tokens, tool calls, returned bytes, latency,
  and total continuation wall time.
- **Uncertainty:** show every block and task. The estimand is only the
  equal-weight mean operational effect on these six fixed tasks. Report each
  task mean and its five prefix outcomes, then a task-stratified checkpoint
  bootstrap that resamples prefixes within each fixed task and re-averages the
  six task means. The interval does not support inference to a benchmark task
  population or another domain.

No pathology macro-F1, evidence-set F1, recommendation F1, human agreement, or
LLM-rubric score is computed.

## Planned Runs

| Run group | Role | Workload | System/method | Repetitions | Decision consequence |
|---|---|---|---|---:|---|
| P0 | isolation/mechanics preflight | task 058 checkpoint after Day 2 | opaque four-fork driver, parser, broker, official oracle | 1 block | Blocks all model inference if checkpoint, leakage, parity, or grading checks fail. |
| P1 | non-ceiling development check | one fixed checkpoint for each of the six tasks | no intervention only; no supervisor conditions generated | 6 blocks | Admit the effect matrix only if at least 4/6 scores are below 0.95; otherwise stop at feasibility. |
| H0 | natural control | six fixed tasks | no intervention | 5/task | Realized baseline and harm reference. |
| H1 | matched extra-inference control | six fixed tasks | generic current-state reflection/search | 5/task | If it matches Trajectory, process history adds no demonstrated value. |
| H2 | strongest main baseline | six fixed tasks | complete Full Raw Retrieval | 5/task | If it matches/wins, reject the stronger representation claim. |
| H3 | proposed | six fixed tasks | Workspace Trajectory Retrieval | 5/task | Only a gain beyond H1 and H2 justifies scaling H6. |

## Execution

### Preparation and immutable benchmark

```bash
git clone https://github.com/Qihoo360/harness-bench \
  docs/tmp/bootstrap/step-0001-20260719T181243-0700/experiment-20260721T021426-0700/raw/benchmark/harness-bench
git -C docs/tmp/bootstrap/step-0001-20260719T181243-0700/experiment-20260721T021426-0700/raw/benchmark/harness-bench \
  checkout --detach 1025086a446653702b80cfb48babbeec35db6b2c

cargo test --manifest-path agent-session/Cargo.toml
cargo test --manifest-path agentvis/Cargo.toml
```

The driver must first support `--prepare-only`; this performs no model or
benchmark call. It writes benchmark, executable, model, task, prompt, fixture,
hook, oracle, wrapper, and source-code hashes plus the exact argv/environment
allowlist. It also constructs a non-model fixture store with the same schema,
validates all per-round snapshots/manifests, renders the exact final prompt,
starts and health-checks Generic/Raw/Trajectory brokers, makes deterministic
dry tool/schema requests, and proves the planned hard-locked arguments. Merely
printing hashes does not pass preparation.

### Supervisor server

```bash
/home/yunwei37/workspace/llama.cpp-latest/build/bin/llama-server \
  --model /home/yunwei37/.cache/huggingface/hub/models--DevQuasar--Qwen.Qwen3.6-27B-GGUF/snapshots/b19fa7e8538a1a5f66452eb3b3167e026177be1d/Qwen.Qwen3.6-27B.f16.gguf.Q4_K_M.gguf \
  --ctx-size 65536 --n-gpu-layers 99 --host 127.0.0.1 --port 8013 --jinja
```

### Authoritative experiment driver

After the reviewed thin adapter exists, the real preflight command is:

```bash
python3 agentvis/research/harnessbench_intervention.py \
  --benchmark docs/tmp/bootstrap/step-0001-20260719T181243-0700/experiment-20260721T021426-0700/raw/benchmark/harness-bench \
  --task 058-multiday-project-state --checkpoint-before-final-round \
  --conditions no-intervention,generic,raw,trajectory --repetitions 1 \
  --worker-model gpt-5.6-sol --worker-reasoning-effort medium \
  --supervisor-url http://127.0.0.1:8013/v1 \
  --supervisor-seed 20260721 --supervisor-evidence-tokens 16384 \
  --supervisor-evidence-bytes 65536 --supervisor-max-tool-calls 24 \
  --output docs/tmp/bootstrap/step-0001-20260719T181243-0700/experiment-20260721T021426-0700/raw/preflight
```

The conditional full command differs only by using the frozen six-task list,
five repetitions, and `raw/full` output. The driver prints progress, session
paths, block/fork hashes, condition completion, official outcome, token/call
ledger, and elapsed time to stdout while retaining machine-readable raw logs.

### Preflight completion rule

P0 passes only if all of the following hold:

1. two distinct prefix Codex session files parse through `agent-session`;
2. an immutable complete snapshot/manifest exists after every prefix
   `after_round`; the penultimate hook has completed and the final prompt has
   not run;
3. all logical fork manifests, prompt bytes, worker-visible argv, stable paths,
   and environment allowlists are identical before advice injection;
4. the exact worker tool sandbox cannot resolve DNS or reach GitHub, raw GitHub,
   or a general public endpoint and cannot read benchmark source, ground truth,
   hooks, oracle, evidence store, credentials, or sibling output; nevertheless
   a real Codex controller turn succeeds and its tool can operate on workspace;
5. Generic, Raw, and Trajectory share model/prompt/output/budget configuration,
   and the implementation's hard locks equal the registered values;
6. Raw and Trajectory have identical Raw-ID membership. For every response from
   `artifact_history`, `session_diff`, and `effects`, an independent verifier
   recomputes every returned field directly from cited allowlisted Raw bytes and
   snapshots; ID existence without field equality fails;
7. no source store, prompt, visible path, advice, environment, or metadata leaks
   condition identity, future prompt data, oracle terms, or hidden benchmark
   files;
8. each supervisor output validates or explicitly abstains, and each advice is
   within the 512-token injection cap;
9. all four final worker sessions complete or time out under the same rule;
10. the driver calls only the official executable oracle; all six task configs
    have zero LLM outcome weight, rubric/provider request count is zero, every
    score is finite in `[0,1]`, and repeated grading is byte-for-byte identical;
11. all process exits, hashes, resource ledgers, raw broker transcripts, native
    worker sessions, final workspaces, and oracle details are retained; and
12. `--prepare-only` has passed the complete implementation-admission contract
    without making a model or benchmark call.

Any failure blocks before the six-task matrix. A repair that changes condition
information, model/prompt/budget, task selection, output, or estimator requires
new plan review. A narrow correctness repair may receive at most two reviewer
follow-ups under the parent workflow.

### Full completion rule

The experiment is complete only after P0/P1 pass, all 30 registered blocks have
four terminal continuations, no task/fork is silently dropped, the estimator is
computed from immutable raw outcomes, and a fresh independent result reviewer
checks protocol conformance, leakage, resource parity, official grading, and
the paper interpretation. Conditions in a block execute within one frozen
execution wave. If any condition suffers an infrastructure failure, the entire
four-condition block is rerun from the same retained prefix with the same
randomized order seed, while every old attempt is retained and labeled. A
single failed cell is never filled later in isolation, and a more favorable
prefix is never regenerated.

- **Raw-result path:**
  `docs/tmp/bootstrap/step-0001-20260719T181243-0700/experiment-20260721T021426-0700/raw/`
- **Derived result:** `result.md` plus deterministic CSV/JSON under `derived/`.
- **Recovery:** each block is content-addressed by benchmark/task/prefix manifest
  and session hashes; terminal condition markers permit idempotent resume.

## Interpretation

- **Positive scaling decision, not a population claim:** the 95% fixed-task
  stratified-bootstrap lower bounds are greater than zero for both registered
  contrasts, `Trajectory - Raw` and
  `Gain(Trajectory) - Gain(Generic)`; at least four of six task means have the
  same positive sign for each contrast; and the observed Trajectory harm count
  is no greater than either Raw or Generic. This admits but does not replace a
  held-out coding/scientific-work expansion.
- **Negative/contradictory:** the 95% upper bound is at most zero for either
  required contrast, or Trajectory's observed harm count exceeds both Raw and
  Generic. Reject H6's stronger representation claim and do not add learned
  retrieval or tune queries to rescue it.
- **Mixed/inconclusive:** every other result, including a positive point
  estimate with an interval crossing zero. Report task/prefix variation but
  make no superiority claim; design a next workload only if the variation
  yields a preregisterable mechanism.
- **Target paper artifact:** a checkpoint-matched outcome plot by task with Raw,
  Generic, and Trajectory gains over no intervention; a companion cost/harm
  table. No visualization screenshot is an RQ result.

## Reproducibility Notes

- Pin all software, model, benchmark, prompt, fixture, hook, oracle, and
  executable hashes before the first call.
- Codex currently exposes no experimental sampling seed; independent prefix
  blocks and randomized fork order estimate operational stochasticity. Call
  comparisons **checkpoint-matched**, never seed-controlled or paired decoding.
  Freeze and report the randomization seed and execution wave for each block.
- The local RTX 5090 (32 GB) can host the pinned Qwen supervisor; worker calls
  use the configured Codex service. Record API model labels and reject silent
  model substitution.
- Harness Bench's process LLM rubric is never invoked. Only the official
  executable `run_oracle`/`score_workspace` result with verified
  `outcome_llm_weight == 0` enters metrics; zero rubric/provider requests is a
  protocol invariant.
- The pilot has six task families and five prefixes per task. Repetitions do not
  create 30 independent task families; all uncertainty and claims must respect
  that clustering.
- No human or Agent semantic annotation is created at any stage.
