# Post-Result Idea Discussion — Round 3: Novelty and Next Experiment

**Timestamp:** 2026-07-12T05:10:00-07:00  
**Method:** independent read-only `iter-refine-ideas` Round 3  
**Changes by discussant:** none; Git and skills untouched

## Bottom Line

The broad idea survives the Hodoscope result, but the next empirical test
should move closer to what a profiler intrinsically measures: additive work or
effects such as tool calls, repetitions, tokens, duration, and resource
operations.

The next action is a **source/data preflight**, not an approved full experiment.
No candidate checked in this round has yet verified all of:

1. a fully accessible official trace corpus;
2. two matched settings over the same tasks;
3. a faithful source-native hierarchy in both settings;
4. an additive profiling signal;
5. an independent step-level outcome for inspection;
6. a published protocol directly supporting flat/native/semantic comparison.

The strongest candidate is the official tau-bench historical corpus. It is
public and contains real benchmark data, two model cohorts, two domains,
repeated trials, rewards, and full message/tool trajectories. Its call identity
and step-level outcome linking must be audited before planning.

Primary sources:

- [tau-bench repository](https://github.com/sierra-research/tau-bench)
- [official historical trajectories](https://github.com/sierra-research/tau-bench/tree/main/historical_trajectories)
- [tau-bench paper](https://arxiv.org/abs/2406.12045)

## Verified Inventory

The official repository exposes:

- `gpt-4o-airline.json`;
- `gpt-4o-retail.json`;
- `sonnet-35-new-airline.json`;
- `sonnet-35-new-retail.json`.

The checked files contain `task_id`, `trial`, `reward`, benchmark metadata, and
role-ordered trajectories.

| File | Runs | Tasks | Trials | Successful | Assistant tool calls | Tool results |
|---|---:|---:|---|---:|---:|---:|
| GPT-4o airline | 200 | 50 | 0--3 | 84 | 1,164 | 1,164 |
| GPT-4o retail | 460 | 115 | 0--3 | 278 | 3,274 | 3,274 |
| Sonnet airline | 400 | 50 | 0--7 | 184 | 2,761 | 2,761 |
| Sonnet retail | 920 | 115 | 0--7 | 637 | 7,086 | 7,086 |

Trials 0--3 may provide a paired two-model subset over 50 airline and 115 retail
tasks. Exact cross-product completeness and duplicate-free matching are not yet
verified.

The trajectories contain system, user, assistant, and tool messages. GPT-4o
records expose assistant `tool_calls` and tool-result messages with
`tool_call_id`. Those identifiers are not globally unique: only 134 distinct
values occur among 1,164 GPT-4o airline calls. More seriously, one distinct ID
occurs across the 2,761 Sonnet airline calls and results. Matching call/result
counts do not establish faithful pairing.

A local source key based on trajectory, message index, and tool-call ordinal
may be faithful, but complete ordering and adjacency must establish it. The
repository also warns that these original tasks are outdated. They remain valid
as a historical published condition, not as current leaderboard evidence.

## Required Preflight

The preflight must produce one detailed Markdown report.

### 1. Version and coverage

- Pin the official revision and all four file hashes.
- Verify every `(domain, task_id, trial)` cell and whether trials 0--3 are an
  exact paired GPT-4o/Sonnet matrix.
- Report missing, duplicate, malformed, and incomplete trajectories.

### 2. Source-native structure

- Verify whether every assistant tool call has exactly one released result.
- Determine whether pairing follows a usable ID, strict adjacency, or another
  explicit source rule.
- Check for multiple calls in one assistant message.
- Define native structure only from released evidence, for example
  `trajectory -> assistant-message index -> tool ordinal -> result`.
- Reject the native comparison if material pairing requires semantic inference.

### 3. Additive measures

- Verify direct measures: tool-call count, message count, content length,
  recorded cost, duration, or tokens.
- Use tool-call count as the minimum guaranteed additive measure if richer
  measures are absent.
- If there is no explicit retry field, call identical invocations repeated
  calls, not retries.

### 4. Independent outcome

- Inspect `reward_info`, task actions, evaluator outputs, and executed calls.
- Determine whether an official failed action check links deterministically to
  a raw invocation.
- Keep final reward scoring-only.
- If only a final binary reward exists, do not invent a first-fault metric. The
  corpus may support accounting but not failure localization.

### 5. Semantic stack feasibility

- Test whether official policies and tool definitions support one plain,
  deterministic hierarchy such as
  `domain -> lookup/mutation/transfer -> API entity -> tool`.
- Fix mapping without target reward or failed-action labels.
- Require identical terminal calls in flat, native, and semantic views.

### 6. Leakage and matching

- Exclude reward, action-check verdicts, and success from mapping, construction,
  and ranking.
- Match calls, tasks, trials, and inspection accounting across views.
- Use model identity only to define a differential cohort, not as an outcome.

Proceed only if the audit verifies an exact paired subset, complete raw traces,
a common source-native path, one direct additive measure, one source-grounded
semantic stack, and an independent decision outcome. Otherwise return to source
search rather than creating a toy oracle.

## Conditional Full Experiment

If the preflight passes, the experiment answers only the existing RQ2:

> For paired real benchmark runs, can a semantic operation-stack differential
> profile identify where one agent setting incurs excess tool work or failed
> actions more efficiently than a flat tool summary or the released
> source-native conversation structure?

Primary measure is one unit per released assistant tool call. Tokens, duration,
or explicit retries are secondary only if complete and directly recorded.

Use matched GPT-4o and Sonnet trials 0--3 on one domain selected before outcome
analysis. A defensible split would develop on one domain and reserve the other
for later RQ3 transfer, but it must not be chosen after inspecting results.

The only views are:

1. flat terminal tool identity;
2. the preflight-validated source-native conversation/tool structure;
3. one fixed source-grounded semantic stack ending in the same terminal tools.

All conserve the same raw calls and measure. Do not add Hodoscope, clustering
suites, random trees, or policy tournaments.

If official failed-action checks link to calls, use raw calls inspected before
the first linked failure and paired task/trial differences. If they do not,
report paired excess tool-call mass under matched tasks and reward strata, and
do not claim failure localization or analyst-effort improvement.

Failure meanings are fixed:

- semantic equals flat: parents add no value beyond tool identity;
- native equals or wins: released order/context is sufficient here;
- reward-derived advantage: invalid leakage;
- unstable task/trial advantage: supports task dependence;
- compactness without an independent improved decision: accounting evidence,
  not diagnostic success;
- no faithful native path: invalid representation comparison;
- positive development-domain result failing unchanged on the other domain:
  conditional RQ2 evidence plus an RQ3 limit, not a narrower RQ.

## Rejected or Deferred Sources

### `cx-cmu/agent_trajectories`

The [release](https://huggingface.co/datasets/cx-cmu/agent_trajectories) is
public and attractive, with 8,653 trajectories across six benchmarks. Its tau2
subset is documented as 984 records with full messages, reward, evaluation
details, and tool fields. However, its README says source runs used a
distraction condition and distraction artifacts were later removed; a matched
clean setting is not documented. It is a processed secondary release, so it is
not yet a verified intervention comparison.

### SWE-bench experiments

The official [SWE-bench experiments repository](https://github.com/swe-bench/experiments)
provides real test outcomes, logs, and trajectories, but downloads require
configured AWS access, submission formats differ, and no common execution
hierarchy/tool schema has been verified. Keep it as a future source after a
matched pair passes structural preflight.

### General AgentBench

Do not depend on General AgentBench until access, compared settings, schema, and
task overlap are verified. Scientific attractiveness is not data availability.

## Larger Research Consequence

Profiling may be strongest when signal is already additive. Anomaly detection
asks a representation and scorer to discover a rare target; profiling asks a
hierarchy to attribute an observed measure. AgentProf's durable contribution
may be to show where excess calls, tokens, time, retries, or effects are
attributed when every view sees the same conserved mass.

Representation disagreement may itself be empirical evidence: if flat, native,
and semantic profiles assign the same mass to sharply different aggregates,
observability conclusions depend on an untested representation choice.

The important question is:

> What independently verifiable decision is unique to profiling rather than
> borrowed from anomaly detection or failure prediction?

Locating which recurring operation families account for a measured regression
is a strong candidate because it intrinsically requires cross-run,
multi-resolution, conserved attribution.

The next step preserves broad RQ2/RQ3, the Hodoscope negative result, the two
core abstractions, and the requirement to use public real evidence. It changes
the expected answer and evidence source, not the scientific problem.
