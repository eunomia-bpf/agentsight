# Experiment plan: profile-to-policy utility on held-out ToolSandbox

Plan date: 2026-07-29
Gate: RQ2 profiling-utility experiment
Status: accepted after independent plan review; frozen-contract gate pending

## Paper-value admission

The fixed thesis remains **“Agent observability needs profiling, not only
debugging.”** Existing RQ2 evidence shows problem correspondence and bounded
inspection advantages, but it does not show that an analyst finds an
actionable problem and that the resulting modification improves a fresh run.
This experiment targets that missing causal link:

```text
real development trajectories
  -> AgentProf differential profile
  -> agent analyst diagnosis and policy
  -> frozen policy
  -> held-out real agent runs
  -> official success and resource outcomes
```

This is one RQ2 experiment, not a fifth RQ. It is admitted only as an
agent-analyst case study; it cannot establish human-developer productivity or
universal policy generalization.

## Hypotheses

### Primary utility hypothesis

An agent analyst using one standard AgentProf differential pprof will produce
a valid, benchmark-agnostic intervention from the same source evidence faster
or with fewer analyst tokens than an agent analyst reading information-matched
per-run operation rows.

### Downstream consequence hypothesis

When the profile-derived intervention is frozen and added to an otherwise
unchanged agent policy, it will either:

1. improve official ToolSandbox exact success / milestone similarity; or
2. reduce agent tool calls or agent-model tokens while preserving milestone
   similarity within the registered non-inferiority margin.

The raw-operation-derived policy is the strongest fair comparator. A no-policy
condition measures the absolute intervention effect.

## Development evidence

The development population is the already frozen AgentReward workload:

- 440 real trajectories from AssistantBench, WebArena, VisualWebArena, and
  WorkArena;
- 338 same-task bad/good pairs;
- fixed semantic stack
  `task,subtask,strategy,action,object,result`;
- standard profile:
  `docs/visexp/out/agentreward-diff-pprof-v1/agentreward-338-pairs-bad-minus-good.operations.pb.gz`.

ToolSandbox evidence, outcome summaries, scenario names, and prior
repeat-call statistics are forbidden during analyst runs. They may be opened
only after both analyst policies are frozen and hashed.

### Information-matched analyst packages

Both packages contain exactly the same pprof sample-type, ordered stack,
labels, and signed values from the same 338 bad/good pair population.

- **PROFILE:** the one standard bad-minus-good `.pb.gz`, stock
  `go tool pprof`, a neutral population/stack description, and no result
  report or rendered figure.
- **RAW-OPERATIONS:** a lossless flat JSONL decode of every pprof sample tuple:
  sample type/unit, signed value, ordered stack frames, and exactly the labels
  queryable from PROFILE. It contains no pair manifest, result summary,
  derived `repeat_rate`, `nonprogress_rate`, `error_rate`, profile path,
  README conclusion, or later report.

A deterministic preparation script will materialize both isolated packages
and enumerate every model-visible field and literal-value class in each
package. A preparation test must reconstruct and compare the complete
multiset of `(sample type, unit, signed value, ordered stack, labels)` tuples
between stock pprof raw output and RAW-OPERATIONS, with zero missing, extra,
or changed tuples and exact positive, negative, net, and absolute mass.
The raw package is allowed shell, `jq`, and Python so the comparator may
compute any aggregation itself. Neither analyst may read outside its isolated
package. If exact equality is not materializable, execution stops and the
comparison is called source-matched rather than information-matched.

## Analyst task

Use `gpt-5.6-sol` in an ephemeral Codex execution with identical sandbox,
prompt, 15-minute limit, and output schema. The only condition-dependent text
identifies the available evidence format and its inspection command.

The analyst must:

1. identify exactly one recurring behavior that is overrepresented in bad
   relative to good runs;
2. cite reproducible commands and quantitative evidence from its package;
3. write one benchmark- and domain-agnostic system-policy addition of at most
   60 English words;
4. state the expected success/cost mechanism; and
5. stop without opening any benchmark or repository data outside the package.

Run three fresh analyst replicates per condition. Before execution,
pre-generate, freeze, and hash a randomized balanced order containing exactly
three PROFILE and three RAW-OPERATIONS runs. Use a fresh isolated ephemeral
execution for every run. Record command start, first/last event time, exit
status, provider usage fields, tool calls, final JSON, and wall time.
Replicate 1 in the frozen per-arm order is pre-registered as the downstream
policy; replicates 2--3 estimate timing/output robustness and may not replace
it.

Before ToolSandbox execution, a fresh reviewer receives the six output JSON
files and read-only snapshots of their corresponding evidence packages under
randomized arm/replicate names. The reviewer may rerun every cited command.
Because the evidence format can reveal the arm, the reviewer is blinded to the
desired verdict and all downstream outcomes, not claimed to be blinded to
format. It scores:

- valid recurring bad-vs-good diagnosis;
- quantitative evidence actually supported by the package;
- executable, benchmark-agnostic policy;
- no benchmark-specific answer or hidden-data reference.

Both replicate-1 outputs must pass all four checks before the three-condition
downstream run. If either is invalid, do not run or interpret
RAW-POLICY versus PROFILE-POLICY. Repair is allowed only for a documented
execution defect, before any ToolSandbox outcome is viewed; otherwise the
analyst comparison is inconclusive. Policies are frozen verbatim and SHA-256
hashed before any ToolSandbox scenario/result is opened.

### Analyst outcomes

- Primary descriptive outcomes: valid diagnosis rate, time to a valid answer,
  total provider tokens.
- Secondary: model/tool call count and whether independently scored diagnosis
  categories agree across replicates.
- With only three replicates per arm, report individual values and medians;
  do not claim statistical significance.

Time to answer is command start through receipt of an independently accepted
final diagnosis. A timeout or rejected output is right-censored at 900
seconds. The “faster” claim requires at least two valid outputs per arm,
PROFILE validity no lower than RAW, lower PROFILE median time to valid answer,
and no higher PROFILE median provider tokens among valid outputs. Otherwise
report no faster finding; a wall-time/token tradeoff cannot support the
headline. If both conditions find the same policy, the only possible
profiling claim is efficiency, while downstream efficacy belongs to the
shared intervention.

## Held-out downstream system

Use the official ToolSandbox checkout at its frozen local commit. Do not edit
the checkout or evaluator. The serving model is the already-running local
Qwen3.6-27B Q4_K_M llama.cpp endpoint at
`http://127.0.0.1:18185/v1`; record `/models`, `/props`, model path/hash when
available, server command line, context size, and tool-call capabilities.

The registered 37-scenario subset is screened before outcomes by declared
dependencies only. Source-level tool-module inspection identifies exactly
five scenarios requiring unavailable RapidAPI services; freeze and hash the
remaining 32-scenario list. No
scenario is excluded for baseline failure, difficulty, or intervention
response.

An experiment-local wrapper may only:

1. subclass the official `OpenAIAPIAgent` and `OpenAIAPIUser`;
2. point their OpenAI clients to the frozen local endpoint/model;
3. add the frozen policy to the agent model's system input only;
4. set and record trial/model-call seeds and sampling parameters;
5. record API usage, model-call count, tool-call count, exceptions, and wall
   time; and
6. call the unchanged official `Scenario.play_and_evaluate` and evaluator.

It may not change tools, starting databases, user messages, turn limits,
milestones, minefields, evaluator code, or conversation termination logic.
User-simulator prompts are identical across conditions. User-model usage is
recorded separately and excluded from agent-cost claims.

## Conditions and run protocol

1. **NO-POLICY:** unchanged local Qwen agent.
2. **PROFILE-POLICY:** exact PROFILE replicate-1 policy.
3. **RAW-POLICY:** exact RAW-OPERATIONS replicate-1 policy.

Use the same model, context, sampling parameters, scenario, trial seed, user
simulator, tool backend, and maximum messages. Run one server slot serially
and interleave conditions within each scenario/trial using a pre-generated
condition order. Record the order before results.

Frozen sampling is temperature `0.2`, top-p `0.95`, maximum completion tokens
`2048`, and zero frequency/presence penalties. Per-request seeds are derived
from the registered trial seed, role, and model-call index. Nonzero temperature
ensures that the eight registered trial seeds are meaningful while shared seed
derivation keeps conditions matched.

### Real preflight

After plan acceptance, run all three conditions once on the same one offline
scenario, `turn_on_location_low_battery_mode`. This scenario is
infrastructure-only and is removed from the full outcome set.

Preflight passes only if:

- llama.cpp returns a valid OpenAI `tool_calls` object used by the official
  execution environment;
- the user simulator can terminate through the official mechanism;
- all three executions reach the unchanged evaluator without exception;
- conversation and execution-context artifacts are saved; and
- usage, tool calls, wall time, policy digest, seed, and official metrics are
  present.

Do not interpret the three preflight outcomes scientifically.

### Full run

If preflight passes, run the remaining 31 offline scenarios with eight
pre-registered trial seeds and all three conditions:

```text
31 scenarios x 8 trials x 3 conditions = 744 official episodes
```

The lower-cost fallback, permitted only for a concrete runtime/resource
blocker recorded before looking at condition outcomes, is four seeds
(372 episodes) and must be reported as a pilot rather than full evidence.

## Metrics and analysis

Confirmatory success endpoint:

- official combined-similarity delta
  (`EvaluationResult.similarity = 1[minefield_similarity == 0] *
  milestone_similarity`).

Confirmatory cost endpoint:

- relative agent-total-token delta.

Secondary diagnostics:

- exact success (`official similarity == 1`);
- official milestone similarity;
- official minefield similarity;
- agent tool calls;
- agent prompt and completion tokens;
- agent model calls;
- episode wall time;
- duplicate same-tool/same-argument calls computed after policy freezing;
- tool-error count;
- official turn count;
- user-simulator tokens and calls;
- per-scenario exceptions.

Analyze paired condition deltas on identical scenario/trial seeds. Report raw
counts, per-scenario aggregates, mean/median differences, and a 10,000-resample
paired bootstrap clustered by scenario. Use a pre-registered simultaneous 95%
clustered-bootstrap procedure across the two confirmatory endpoints.
Exact-success intervals use paired scenario bootstrap and Wilson intervals per
arm but remain secondary.

Registered official combined-similarity non-inferiority margin:

```text
PROFILE-POLICY minus NO-POLICY >= -0.02
```

The non-inferiority claim requires the lower bound of the clustered 95%
bootstrap interval to exceed `-0.02`.

## Admission rule

The result is eligible for the paper only if all of the following hold:

1. independent analyst-output review accepts PROFILE replicate 1;
2. preparation identities and profile mass conservation pass;
3. preflight and all registered full episodes use the unchanged official
   evaluator with no condition-dependent infrastructure failures;
4. PROFILE analyst efficiency satisfies the bounded rule above against
   information-matched RAW-OPERATIONS; and
5. PROFILE-POLICY either:
   - has a simultaneous 95% lower bound for official combined-similarity delta above
     zero; or
   - has a simultaneous 95% upper bound for relative agent-total-token delta
     at or below `-10%` and the official combined-similarity non-inferiority lower
     bound above `-0.02`.

RAW-POLICY remains visible regardless of outcome. If it matches or exceeds
PROFILE-POLICY, report that boundary. If analyst efficiency or downstream
consequence fails, preserve the negative result and do not place a utility
claim in the paper.

No secondary endpoint alone supports the headline claim.

## Frozen execution contract

Before plan acceptance, populate and independently check:

- ToolSandbox checkout:
  `.agentsight/external/ToolSandbox`, Git commit
  `165848b9a78cead7ca7fe7c89c688b58e6501219`;
- dependency source SHA-256:
  `1374abe6c850da500a4f64534456b25cb029eb6dc1c0e3c3f78431949a2e5ad0`
  for the checkout's `pyproject.toml`; resolved lock path
  `runtime/requirements.lock`;
- exact 32-scenario dependency-screened list and SHA-256, plus the 31-scenario
  outcome list after removing the preflight scenario;
- official evaluator
  `tool_sandbox.common.scenario.Scenario.play_and_evaluate` calling
  `tool_sandbox.common.evaluation.Evaluation.evaluate`; raw fields
  `EvaluationResult.similarity`, `milestone_similarity`,
  `minefield_similarity`, and `turn_count`; exact success is
  `similarity == 1`;
- literal preparation, analyst, review, preflight, full-run, and analysis
  commands;
- scripts `prepare_analyst_packages.py`, `run_analysts.py`,
  `run_toolsandbox.py`, and `analyze_results.py`, whose hashes are recorded in
  `frozen-execution-contract.json`;
- raw output directory `toolsandbox/raw/`;
- analyst-order, episode-order, and seed file paths/hashes; and
- an expected episode manifest containing every registered cell.

Completion requires one terminal raw record for every expected full-run cell:
744 episodes for the full experiment or 372 for the predeclared pilot, with
no missing cell and no condition-dependent exception. Agent tokens and tool
calls are experiment-measured resource outcomes, not official ToolSandbox
metrics.

Frozen local inference endpoint:

- base URL: `http://127.0.0.1:18185/v1`;
- model:
  `/home/yunwei37/.cache/huggingface/hub/models--DevQuasar--Qwen.Qwen3.6-27B-GGUF/snapshots/b19fa7e8538a1a5f66452eb3b3167e026177be1d/Qwen.Qwen3.6-27B.f16.gguf.Q4_K_M.gguf`;
- llama.cpp reports 26,895,998,464 parameters, Q4_K_M quantization, and a
  32,768-token serving context;
- endpoint metadata and server command are re-recorded and hashed immediately
  before preflight and full execution.

Literal commands, run-order files, scenario hashes, dependency versions, and
script hashes are materialized in two stage-specific contracts:
`frozen-contract-analyst.json` before any analyst call and
`frozen-contract-toolsandbox.json` after both policies and their independent
review are frozen but before any ToolSandbox episode. Both are checked by
`verify_frozen_contract.py`; a missing or changed field is a hard stop.

## Validity and claim boundaries

- This tests an agent analyst, not a human developer.
- AgentReward supplies development evidence; ToolSandbox is a disjoint,
  held-out benchmark, so no ToolSandbox result may tune the policy.
- The profile and raw-operation packages contain the same normalized semantic
  evidence but different organization. The result measures the utility of
  profiling that evidence, not the utility of semantic annotation versus raw
  natural-language trajectories.
- A system prompt is a real agent modification but not a code patch.
- Local quantized Qwen results do not generalize automatically to proprietary
  models.
- The profile is one standard pprof product artifact. Markdown, JSONL, usage
  records, and official benchmark outputs are research audit records, not
  additional AgentProf products.
- No paper, thesis, story, or user-instruction file is edited during this
  experiment.

## Required records

Retain:

- preparation script/tests, sanitized manifests, digests, and conservation
  report;
- isolated analyst prompts, JSONL event logs, final JSON, usage, timings, and
  randomized blind-review mapping;
- frozen policy files and hashes;
- wrapper source/tests and frozen dependency/scenario inventory;
- preflight/full commands, seeds, condition order, server metadata, official
  conversations/execution contexts/results, and raw usage;
- aggregate result report and an independent result review.

Result review must independently recompute headline numbers from raw episode
records and issue one verdict: `VALID PAPER EVIDENCE`, `VALID NEGATIVE`, or
`INVALID`.
