# Source/Data Preflight: Official tau-bench Historical Trajectories

**Timestamp:** 2026-07-12T06:03:00-07:00  
**RQ:** RQ2, unchanged  
**Status:** source partially passes; proposed inspection experiment not approved  
**Decision:** return to source search; do not invent a step oracle

## Purpose

This is a source/data preflight, not an experiment result. It checks whether the
official tau-bench historical release can support one real additive-regression
comparison over flat, genuine source-native, and semantic views.

Acceptance required all of:

1. a complete matched task/trial-index matrix;
2. source-native call/result structure for every observed prefix and explicit
   accounting for non-terminated episodes;
3. a directly recorded additive measure;
4. a source-grounded semantic stack;
5. an independent operation-linked outcome for a real inspection decision.

## Pinned Source

- Repository: `https://github.com/sierra-research/tau-bench`
- Commit: `59a200c6d575d595120f1cb70fea53cef0632f6b`
- Official repository warning: these airline/retail tasks are historical and
  outdated; results must not be called current leaderboard evidence.

Files and SHA-256:

| File | Bytes | SHA-256 |
|---|---:|---|
| `gpt-4o-airline.json` | 4,114,038 | `e9e6c0297660c537f83d4fd9c476ce7a9a86ecd2784874b7bfc13be598e37bfa` |
| `gpt-4o-retail.json` | 10,813,408 | `df01707894836168ff0ec9616b0bf08f66c7e5afcf313e5fe4f7a2f5c2ec938b` |
| `sonnet-35-new-airline.json` | 10,888,682 | `fe62fcd514b855b36f156dd4c3c7748597b392b006aff739b53337a9f3ba94d1` |
| `sonnet-35-new-retail.json` | 26,544,890 | `0df526398e9d2720c32d340815cffb04fe8c4f8a61b1f4f84bf3bb558f760131` |

## Inventory And Pairing

| File | Runs | Tasks | Trials | Successful | Calls | Tool results |
|---|---:|---:|---|---:|---:|---:|
| GPT-4o airline | 200 | 50 | 0--3 | 84 | 1,164 | 1,164 |
| GPT-4o retail | 460 | 115 | 0--3 | 278 | 3,274 | 3,274 |
| Sonnet airline | 400 | 50 | 0--7 | 184 | 2,761 | 2,761 |
| Sonnet retail | 920 | 115 | 0--7 | 637 | 7,086 | 7,086 |

Every file has zero duplicate `(task_id, trial)` key. Restricting Sonnet to
trials 0--3 yields complete matched task/trial-index matrices:

- airline: 200/200 keys intersect, zero model-only or missing key;
- retail: 460/460 keys intersect, zero model-only or missing key.

The proposed source therefore has 660 matched `(task_id, trial ordinal)` cells
per model. This does not establish identical simulated-user transcripts,
random-number streams, or common-random-number pairing between models.

Fourteen trajectories reach the 30-step limit without termination and have 62
messages but no `reward_info` or `user_cost`: 5 GPT-4o airline, 2 GPT-4o retail,
6 Sonnet airline, and 1 Sonnet retail. Ten remain in the proposed trials-0--3
comparison (7 GPT-4o and 3 Sonnet). Their observed prefixes and tool calls are
available, but the release is not a set of universally complete terminated
episodes.

## Source-Native Structure

All files contain ordered system, user, assistant, and tool messages. Across
every trajectory:

- every assistant tool-call message contains exactly one call;
- it is immediately followed by exactly one tool-result message;
- total call and result counts match;
- exact call-ID multisets match results within trajectories.

Raw IDs are not suitable global identities. There are 73 and 85 within-run ID
reuses in GPT-4o airline/retail and 2,362 and 6,167 in Sonnet airline/retail.
This does not destroy source structure because the released sequence is strict
and one-call/one-result adjacent. A faithful native key is mechanically:

```text
model/domain/task_id/trial
  -> assistant message index
  -> sole tool-call ordinal
  -> immediately following tool result
```

No semantic inference is required. Source-native structure therefore passes.

## Direct Measures

The minimum complete additive measure is one unit per assistant tool call.
Message count and content characters are also directly available. The release
does not contain complete agent token, duration, latency, or agent-cost fields.
`info.user_cost` is the simulated user's cost and must not be presented as
agent execution cost.

There is no explicit retry field. Identical repeated tool/argument calls can be
measured as repeated calls, but their intent cannot be called a retry or waste
without independent evidence.

## Official Outcome Semantics

`tau_bench/envs/base.py::calculate_reward` first computes action reward by
replaying expected mutation actions and comparing the final database hash. For
every task with required outputs, it then checks response substrings. Final
reward is their conjunction, but the output branch overwrites diagnostic
`info`, so the release generally does not expose both `r_actions` and
`r_outputs`. Four airline output tasks all also have mutation actions; 37 of 38
retail output tasks also have mutations, leaving only one output-only task. The
release stores:

- final binary reward;
- expected task actions;
- `r_actions` plus the expected final-state hash, or required output checks.

This is a real official task-level outcome, but it is not an operation-linked
failure oracle. It cannot determine which raw call first caused failure:

- several call sequences can reach the same final state;
- lookup calls are legitimate but absent from expected mutation actions;
- a missing expected action has no raw call to rank;
- extra, wrong, or later-corrected calls are not labeled individually;
- final output checks likewise do not label one tool call.

The repository's `auto_error_identification.py` asks an LLM to assign fault type
and explicitly warns that labels may be inaccurate. It is not an independent
published step oracle and cannot repair this gap.

## Semantic Stack Feasibility

The official policies, task definitions, and API tool names can support a plain
source-grounded stack such as:

```text
domain -> lookup/mutation/transfer -> API entity -> terminal tool
```

This mapping can be fixed without reward labels, and all views can end in the
same terminal calls. Semantic construction therefore appears feasible. It was
not implemented because the outcome requirement failed first.

## Decision

| Requirement | Verdict |
|---|---|
| Public pinned official data | PASS |
| Complete matched task/trial-index matrix | PASS; not common-random pairing |
| Complete terminated episodes | PARTIAL/FAIL (14 truncated; 10 in matched cells) |
| Observed call/result prefixes | PASS |
| Genuine source-native path | PASS |
| Direct additive measure | PASS (tool calls) |
| Source-grounded semantic stack | PASS in principle |
| Independent operation-linked outcome | **FAIL** |

The approved first-fault/raw-call inspection experiment must not proceed on this
source. Using expected mutation actions to label all lookups as errors would be
scientifically invalid; using final reward to assign one failing call would be
fabricated supervision.

The corpus may later support an accounting-only study of excess call mass, but
compactness or interpretability alone would not close the present RQ2 decision-
value gap. The full-paper reviewer explicitly requires an independently
verifiable decision, so this weaker study is not substituted now.

## Next Action

Return to literature/data search for a fully public corpus that combines:

- matched real settings or a real intervention;
- complete source-native parent-child traces;
- per-operation additive token/time/effect measures;
- an independently known changed component or operation-linked outcome.

An OpenTelemetry agent-trace release with matched framework variants and direct
token usage is the next candidate to preflight. If it also lacks an independent
decision target, record that rejection rather than designing a toy oracle.
