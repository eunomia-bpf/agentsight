# Real Preflight — Decoupled Responsibility Continuation

- completed: 2026-07-20
- state: **VALID / COMPLETE; full execution authorized**
- scope: one complete trajectory from each CodeTraceBench framework
- official stages opened: no
- scientific contract changed: no

## Complete Coverage

The registered two-stage implementation completed:

- mini-SWE-agent: 20 operations;
- OpenHands: 102 operations;
- SWE-agent: 32 operations;
- Terminus2: 60 operations;
- total: 4 trajectories and 214/214 operations.

It made 210 binary continuation calls and 28 exact-label calls, for 238 model
calls total. Every call returned a valid exact GBNF response. Maximum request
length was 5,951 tokens, below 8,192. Every retained source-evidence SHA-256
matched; no future operation, current result, human stage, numeric plan index,
stage instance, score, or official manifest was exposed.

Contract checks found:

- continuation calls containing the alternative-label list: 0;
- initialization/change decisions lacking a label call: 0;
- continue decisions with an unexpected label call: 0;
- missing or duplicate operations: 0.

## Source-Side Policy Diagnostic

Across 210 adjacent decisions, the candidate produced:

- learned `continue`: 186;
- `change`: 24;
- predicted adjacent boundary rate: `0.114286`;
- predicted temporal instances: 28;
- operation-triplet `A -> B -> A` alternations: 4;
- collapsed stage-sequence `A -> B -> A` alternations: 20;
- non-adjacent responsibility returns: 20;
- first-time responsibility changes: 4;
- responsibility types used: 8 of 25 available across the four trajectories.

Per framework:

| Framework | Operations | Changes | Continues | Types used |
|---|---:|---:|---:|---:|
| OpenHands | 102 | 11 | 90 | 2 |
| SWE-agent | 32 | 10 | 21 | 2 |
| Terminus2 | 60 | 0 | 59 | 1 |
| mini-SWE-agent | 20 | 3 | 16 | 3 |

This removes the Step0051 near-all-switch behavior on the same fixed preflight
selection. It does not establish gold fidelity: the Terminus2 trajectory also
shows that the policy can maintain one responsibility across a full session.
Both over- and undersegmentation remain possible until complete predictions are
fixed and scored.

## Decision

Preflight validates implementation, state transitions, input separation,
context, coverage, and isolation. It does not justify a prompt edit or early
claim. Proceed unchanged through all 405 trajectories and 20,866 operations,
then open the human stages once in the separate scorer.

Raw preflight root:
`.agentsight/experiments/rq3-decoupled-responsibility-continuation-v1/preflight/`.
