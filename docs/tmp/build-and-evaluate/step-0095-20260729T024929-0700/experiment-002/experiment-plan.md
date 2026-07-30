# Experiment 002 plan: confirmatory profile-to-policy utility replication

Plan date: 2026-07-29
Gate: RQ2 profiling utility
Status: accepted after three independent review rounds; no experiment-002
analyst or ToolSandbox call may run before its stage-specific frozen contract

## Scientific continuity and disclosed adaptation

The fixed thesis remains **“Agent observability needs profiling, not only
debugging.”**

Experiment 001 was a valid negative at its preregistered analyst-efficiency
gate. All six diagnoses were valid and PROFILE had a 36.614-second median
answer time versus 52.547 seconds for information-matched RAW-OPERATIONS, but
PROFILE used 126,571 median provider tokens versus 126,066. Its literal rule
required lower time and no higher tokens, so the 505-token excess caused a
FAIL. No ToolSandbox preflight or outcome episode was run.

This new experiment does not reinterpret experiment 001, reuse its analyst
outputs as confirmatory observations, replace its policies, or silently relax
its rule. It is a prospectively frozen replication with 40 fresh analyst runs.
It corrects one design weakness exposed by experiment 001:

1. three unpaired runs per arm were too few to estimate stochastic analyst
   latency or resource use.

It does **not** correct the exact zero-token rule after observing its failure.
The confirmatory rule retains the original no-increase boundary. Alternative
10% time and 5% token materiality thresholds are sensitivity analyses only and
cannot determine admission.

The adaptation is fully disclosed. Experiment 001 remains visible beside any
experiment-002 result.

## Claim and causal chain

The experiment targets one bounded agent-analyst case study:

```text
real AgentReward development trajectories
  -> information-matched PROFILE or RAW-OPERATIONS evidence
  -> fresh agent analyst diagnosis and frozen policy
  -> held-out official ToolSandbox executions
  -> official success and measured agent-resource outcomes
```

It cannot establish human-developer speed or universal policy
generalization. It can support the narrower claim that, for this fixed analyst
model and development corpus, the standard AgentProf pprof representation
enables a valid actionable diagnosis faster than a lossless flat operation
representation, and that the preregistered profile-derived intervention has a
measurable held-out consequence.

## Development evidence and information identity

Use the same frozen AgentReward development population and preparation
adapter as experiment 001:

- 440 real trajectories and 338 bad/good pairs;
- one standard differential pprof;
- one lossless flat JSONL decode of the exact pprof sample tuples;
- exact equality of all 11,146 `(sample type, unit, signed value, ordered
  stack, labels)` tuples and positive, negative, net, and absolute mass.

Copy the packages and preparation records into experiment 002 and verify their
hashes and tuple equality independently. Do not expose experiment-001 analyst
outputs, timings, policies, reviews, or this plan's expected direction to the
fresh analysts.

## Fresh analyst experiment

### Model and task

Use `gpt-5.6-sol` through fresh ephemeral Codex executions. Every run receives:

- the same benchmark-agnostic task and JSON output schema;
- a read-only current directory containing only its evidence package;
- the same 900-second timeout;
- the same allowed local tools;
- no internet, repository, ToolSandbox, prior-output, or downstream access.

The only condition-dependent prompt text identifies the evidence format and
its stock inspection commands. Each analyst must identify exactly one
recurring bad-vs-good behavior, cite reproducible quantitative evidence, give
one executable benchmark-agnostic policy addition of at most 60 English words,
and state its mechanism/cost.

### Randomized paired-block schedule

Run 20 temporal blocks. Each block contains one PROFILE and one
RAW-OPERATIONS execution. Before any run:

1. assign opaque run identifiers;
2. randomly choose the within-block order, constrained to exactly ten
   PROFILE-first and ten RAW-first blocks;
3. hash the complete 40-run schedule, prompts, commands, packages, model,
   timeout, schema, and execution script; and
4. forbid interim summaries until all 40 terminal run records exist.

The paired temporal block controls service-load drift; the two calls remain
fresh independent model executions. Record command start, first/last/final
event receipt time, wall time, status, provider usage fields, model/tool calls,
actual command paths, and final JSON.

### Independent output validity review

After all 40 runs, but before arm-level efficiency or any ToolSandbox result is
computed, a fresh reviewer receives outputs, endpoint-redacted
execution-command logs, and read-only evidence snapshots under randomized run
names. The bundle contains no timing, usage, schedule position, within-arm
rank, replicate identity, arm map, desired verdict, experiment-001 output, or
downstream data. Evidence format may reveal arm and must be acknowledged.
Bundle hashes are checked before and after review.

For every output it reruns every cited command and scores:

1. recurring bad-vs-good diagnosis validity;
2. quantitative support;
3. executable benchmark-agnostic policy of at most 60 words;
4. absence of benchmark-specific answers or hidden-data references; and
5. absence of evidence reads outside the assigned package.

The reviewer locks all five decisions for all 40 opaque cases in a hashed
record before the private map is opened or arm-level endpoints are computed.

The preregistered downstream policies are rank 1 in each arm in the frozen
schedule, regardless of validity. They are fixed before execution and may not
be replaced by a later output. If either rank-1 output fails any validity
check, the downstream comparison stops without substitution. Ranks 2--20
estimate efficiency and robustness only.

## Confirmatory analyst-efficiency rule

### Endpoints

For block `b`, define:

```text
T_b = PROFILE final-answer seconds / RAW final-answer seconds
K_b = PROFILE provider-total tokens / RAW provider-total tokens
```

Provider-total tokens are frozen as `input_tokens + output_tokens`.
`cached_input_tokens` and `reasoning_output_tokens` are reported details and
are not double-counted. Invalid/timeout outputs are assigned 900 seconds for
the time analysis and remain invalid for the validity gate.

Every one of the 40 calls must have a positive provider-token total. Missing
usage is a hard infrastructure stop. Usage recorded for an invalid call
remains in `K_b`; it is never dropped. Every invalid or timed-out output is
assigned exactly 900 seconds in `T_b`.

The exact confirmatory estimator for endpoint `j` is:

```text
theta_j = median_b(log(ratio_j,b))
reported ratio_j = exp(theta_j)
```

Use a deterministic 100,000-resample paired bootstrap over whole temporal
blocks with NumPy `Generator(PCG64(2026072903))`. Each resample draws exactly
20 block indices with replacement and recomputes both `theta` values from the
same indices. For each endpoint, sort its 100,000 bootstrap `theta` values and
define `Q(p)` as the 1-indexed `ceil(p * 100000)` order statistic, with ties
retained and no interpolation. The simultaneous familywise-95% upper bounds
are Bonferroni one-sided 97.5% percentile bounds:

```text
U_T = exp(Q_T(0.975))
U_K = exp(Q_K(0.975))
```

Whole-block resampling preserves the temporal pairing. Freeze literal analysis
code and golden synthetic tests of block sampling, medians, quantiles, and
missing/invalid handling before calls. Also report all individual values,
ordinary point estimates, unadjusted 95% intervals, means, raw medians,
within-block order-stratified estimates, and validity. Do not substitute
another estimator after results.

### Materiality thresholds

The PROFILE efficiency gate passes only if all hold:

1. both arms have at least 18/20 independently valid outputs;
2. PROFILE valid count is no lower than RAW-OPERATIONS valid count;
3. `U_T < 1.00`; and
4. `U_K <= 1.00`.

For sensitivity only, report whether `U_T < 0.90` and `U_K <= 1.05`. These
thresholds are labeled post-experiment-001 adaptations and cannot make the
confirmatory gate or paper admission pass. No claim may ignore the
confirmatory zero-token boundary.

Failure of any clause is a valid negative. Do not describe a wall-time/token
tradeoff as faster.

## Held-out downstream system

Only after the analyst-efficiency gate and both selected policies pass:

- use the clean official ToolSandbox checkout at commit
  `165848b9a78cead7ca7fe7c89c688b58e6501219`;
- use the already-running local Qwen3.6-27B Q4_K_M llama.cpp endpoint with
  model file hash, server binary/build, command line, chat template, 32,768
  context, single slot, and reasoning-off state re-recorded;
- use only the 32 dependency-screened offline scenarios;
- use `turn_on_location_low_battery_mode` for three-condition infrastructure
  preflight and remove it from outcomes;
- run all remaining 31 scenarios, 8 registered trial seeds, and 3 interleaved
  conditions, totaling 744 official episodes;
- keep temperature 0.2, top-p 0.95, max tokens 2,048, zero penalties, paired
  role/request seeds, identical scenario construction, tools, starting state,
  user simulator, turn limits, and unchanged official evaluator.

Conditions:

1. NO-POLICY;
2. PROFILE-POLICY, using the exact selected experiment-002 PROFILE policy;
3. RAW-POLICY, using the exact selected experiment-002 RAW policy.

The wrapper may only redirect the official OpenAI roles to the frozen local
endpoint, append the frozen policy to the agent system input, set and record
sampling/seeds, record telemetry/artifacts, and call unchanged
`Scenario.play_and_evaluate` and `Evaluation.evaluate`.

Preflight must reach the official evaluator without exception in all three
conditions, produce a valid OpenAI tool call and official termination, save
conversation/execution context, and record usage, policy hash, seed, wall
time, and official metrics. Preflight outcomes are not scientific.

## Downstream endpoints and admission

Confirmatory success endpoint:

- official combined similarity:
  `similarity = 1[minefield_similarity == 0] * milestone_similarity`.

Confirmatory cost endpoint:

- relative agent-total-token delta. Agent-total tokens are the sum of the
  local OpenAI response `usage.total_tokens` over every agent-role request in
  one episode, excluding user-simulator requests. Every response must also
  satisfy `total_tokens = prompt_tokens + completion_tokens`; missing or
  inconsistent usage is a hard stop.

For each of the 248 scenario/trial cells, pair PROFILE-POLICY with NO-POLICY.
The two point estimators are:

```text
Delta_S = mean over all 248 pairs(PROFILE similarity - NO-POLICY similarity)
Delta_K = sum(PROFILE agent tokens) / sum(NO-POLICY agent tokens) - 1
```

Use `Generator(PCG64(2026072904))` for 10,000 whole-scenario cluster
resamples. Each resample draws exactly 31 scenario names with replacement and
retains all eight seeds and all three conditions for every drawn scenario.
Recompute both estimators from the same sampled clusters. Sort each bootstrap
distribution and use the same no-interpolation order-statistic definition
`Q(p) = x_(ceil(p * 10000))`. Bonferroni one-sided 97.5% bounds give
familywise coverage of at least 95%:

```text
L_S = Q_Delta_S(0.025)
U_K = Q_Delta_K(0.975)
```

Freeze this literal analysis code and synthetic golden tests before preflight.
The PROFILE-POLICY result passes consequence only if:

1. `L_S` is above zero; or
2. `U_K` is at or below `-10%` and `L_S` exceeds the
   registered non-inferiority margin `-0.02`.

Report RAW-POLICY against both conditions regardless of direction, using the
same estimators for transparency. The confirmatory consequence claim is only:
“the selected PROFILE policy has a held-out consequence versus NO-POLICY.”
It does not establish PROFILE-policy superiority over RAW-POLICY unless a
separately frozen direct contrast supports it; no such superiority contrast is
registered here. Secondary diagnostics include exact success,
milestone/minefield similarity, agent tool calls/model calls/prompt and
completion tokens, wall time, duplicate same-tool/same-argument calls, tool
errors, official turns, user-simulator usage, and all exceptions. No secondary
endpoint supports the headline alone.

Paper eligibility requires:

1. accepted plan and frozen contracts;
2. exact package identity;
3. accepted analyst outputs and selected policies;
4. the complete experiment-002 analyst-efficiency gate above;
5. clean preflight and 744 registered terminal episodes without
   condition-dependent infrastructure failure;
6. one of the two downstream consequence branches above; and
7. a fresh independent result reviewer that recomputes every headline number
   from raw records and returns PASS.

Both experiment 001's negative gate result and experiment 002's disclosed
adaptation must remain visible in the research record and any paper report.

## Stop rules and artifact boundary

- No interim analyst or downstream result inspection.
- No rank-1 policy may be replaced. A documented execution defect established
  before unblinding may rerun the same rank-1 execution under the identical
  frozen contract; it may not select another output or policy.
- No scenario exclusion based on difficulty, baseline failure, or policy
  response.
- No fallback to the 372-episode pilot unless a concrete hardware/runtime
  blocker is documented before any downstream scientific outcome is viewed.
- Missing or changed hashes, dirty ToolSandbox checkout, server identity drift,
  malformed model tool calls, or incomplete telemetry is a hard stop.
- Research JSON/JSONL/Markdown records are audit artifacts. AgentPProf still
  has exactly one product artifact per profiled run: a standard pprof profile.
- Do not edit the paper until the final independent result review admits the
  evidence.

Before execution, materialize and independently review literal preparation,
40-run analyst, blind-review, policy-freeze, preflight, 744-episode full-run,
analysis, and result-review commands plus all file hashes in stage-specific
fail-closed contracts.
