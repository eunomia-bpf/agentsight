# Full Run and Result — RQ4 End-to-End Cost Accounting

**Timestamp:** 2026-07-23T22:30:52-07:00  
**Run status:** complete  
**Registered hypothesis:** supported for deterministic construction and replay;
A2 Agent-inference time remains unmeasured

## RQ and measured boundary

This experiment answers the measurable part of:

> **RQ4 — What is the cost of constructing a semantic profile?**

The common starting asset is a fixed normalized 405-session CodeTrace target.
A2 packet construction additionally opens the released raw archives to recover
source-native turns. The experiment measures:

```text
fixed target + raw archives
    -> A2 source packets
    -> [automatic Agent annotations: historical telemetry incomplete]
    -> deterministic assembly/root repair/name canonicalization
    -> stock-pprof-readable profile
```

Original task execution, live capture, raw-to-normalized target construction,
model download, and backend setup are outside the boundary.

## Host and population

- Host: Linux `6.15.11-061511-generic`;
- CPU: Intel Core Ultra 9 285K, 24 online CPUs;
- memory: 125 GiB;
- cache policy: one excluded real preflight, then three consecutive warm-cache
  full runs without flushing the filesystem cache;
- profiler: `agentpprof 0.2.37`, SHA-256
  `c560754b3e1c0496b914ce49ee0e17a4d8004e7702556cccaa5814f7e6843d9b`;
- population: 405 sessions, 17,148 source-native turns, 20,866 operations,
  and 494,862,929 provider-reported source tokens.

GNU `/usr/bin/time` recorded wall time and peak RSS. No component received an
explicit concurrency flag.

## Fresh deterministic component results

| Component | Role | Wall time, all runs (s) | Median (s) | Max RSS (KiB) |
|---|---|---:|---:|---:|
| A2 source-packet construction | A2-specific source recovery | 500.07 / 505.64 / 501.64 | **501.64** | 292,664 |
| A2 assembly/root repair/validation | post-annotation | 1.21 / 1.16 / 1.18 | **1.18** | 256,388 |
| A2 name canonicalization | post-annotation | 2.35 / 2.35 / 2.36 | **2.35** | 195,272 |
| Raw-action pprof | serialization control | 0.10 / 0.11 / 0.10 | **0.10** | 86,008 |
| Reference-corpus recurrence pprof | low-cost automatic alternative | 0.54 / 0.49 / 0.49 | **0.49** | 243,312 |
| A2 fixed-mark operation pprof | replay control | 1.17 / 1.17 / 1.19 | **1.17** | 320,540 |
| A2 fixed-mark token pprof | alternate-width replay control | 1.19 / 1.17 / 1.17 | **1.17** | 320,432 |

The matched sequential A2 postprocessing pairs take 3.56, 3.51, and 3.54
seconds, median **3.54 seconds**. The measured deterministic A2 components
therefore total about 506.35 seconds at their component medians before adding
the unavailable Agent-inference component. This subtotal is an accounting
convenience for one backend; it is not used to make a matched total against
raw action or recurrence, whose starting assets differ.

Interpretability rates:

- A2 source-packet construction: 1.239 seconds/session or 24.04 seconds per
  1,000 operations;
- deterministic postprocessing: 8.74 milliseconds/session or 0.170 seconds per
  1,000 operations;
- fixed-mark replay: 2.89 milliseconds/session or 0.056 seconds per 1,000
  operations.

## A2 automatic-annotation telemetry

The adopted A2 annotations were produced in two disjoint automatic-Agent
waves. Their filesystem times are:

| Wave | Start artifact | End artifact | Artifact-time span |
|---|---|---|---:|
| 41-session long horizon | packet manifest, `2026-07-22 13:59:35.601683 -0700` | final nonempty batch, `14:08:38.771011 -0700` | 543.17 s |
| 364-session complement | packet manifest, `2026-07-22 15:00:35.493726 -0700` | final nonempty batch, `15:45:54.215906 -0700` | 2,718.72 s |
| Sum of disjoint wave spans | — | — | **3,261.89 s (54.36 min)** |

Exact sources:

- `.agentsight/experiments/codex-agent-long-horizon-v1/packets/manifest.json`
  and `annotations/batch-{01,02,03}.json`;
- `.agentsight/experiments/codex-agent-remaining-v1/packets/manifest.json`
  and `annotations/batch-{01..12}.json`.

This is only a **historical artifact-time workflow envelope**. Mutable mtime
metadata does not distinguish model inference, dispatch, scheduling,
parallelism, idle time, or file writing. A search of retained Codex session
telemetry could not bind a complete disjoint set of model token counters and
task timers to these 15 output batches. Therefore:

- A2 model/provider inference wall time: **unavailable**;
- A2 prompt/completion tokens: **unavailable**;
- the 54.36-minute span is not called model time, is not a lower bound, and is
  not added to the fresh component timers.

## Determinism, coverage, and pprof validation

All three source-packet runs independently produce:

- 405 sessions;
- 17,148 turns;
- 20,866 operations;
- 12 balanced packet batches; and
- the same aggregate SHA-256 over named JSON artifacts:
  `0205298933ba555e1c737f6f31e649cd8a4ca60d67f58cda19a7887aa74bb2d6`.

All three deterministic postprocessing runs independently produce:

- 5,752 A2 temporal marks before display-name canonicalization;
- 5,537 pre-canonical semantic names;
- exact 20,866 operation and 494,862,929 token masses; and
- byte-identical adopted A2 outputs:
  - marks:
    `d8c78a552c5db9d3eb9735b15568d81b555740f7e419b7556f33323dae5d6d68`;
  - predictions:
    `a2e6162c7f97d6ccb0653fc38a2c48ee351a5281b7f60b18cc2a031ce5b18432`;
  - count input:
    `ab6cecc511d747c275f04a8c7106144495c86c23f19777c8832507ab0217005f`;
  - token input:
    `d9c181c0bff6a032311fbf96df0bd10a682270866b27ad646538751b70fa5a16`.

Every one of the 12 full `.pb.gz` outputs loads with stock `go tool pprof`.
Within each method, all three deterministic profiles are byte-identical.

| Method | Exact mass | Unique stacks | File size (bytes) | Profile SHA-256 |
|---|---:|---:|---:|---|
| Raw action | 20,866 operations | 9 | 11,225 | `479b703bfefb1abeeb9f617ca90e8f1a39e7cd0494615895c378307588aec1bb` |
| Recurrence | 20,866 operations | 534 | 21,804 | `f4aa4ca237fb4e8deca3ae4df877801207bffba7c06f4411ad0e41a3f2242197` |
| A2 operation | 20,866 operations | 19,874 | 789,333 | `e6789fb2e6e07575b65a46a1399cb5c14c81d00b4c59422fbcd43c66942f695b` |
| A2 tokens | 494,862,929 tokens | 19,874 | 852,435 | `e5d3d5ac714cff926003f21178c8215b401d19b9496203955fe8a0ac9b454f4a` |

The large A2 unique-stack count includes its source-evidence suffix
(`source_session`, prompt, call, and tool) below the semantic operation path.
It is not the number of semantic identities.

## Cost paired with already reviewed RQ3 quality

| Method | Cost role | Median profile construction | Ordinary B-cubed F1 | Exact-boundary F1 |
|---|---|---:|---:|---:|
| Coarse action | non-semantic control | 0.10 s | .473242 | .267524 |
| Label-free recurrence | automatic alternative | 0.49 s | .662740 | .265571 |
| Adopted A2 | fixed-mark replay only | 1.17 s | **.704113** | **.393916** |

The A2 row does not claim that automatic annotation costs 1.17 seconds. It
pairs adopted quality with the cost of replay after marks exist. Its measured
first-construction accounting additionally includes 501.64 seconds of A2
source-packet construction and 3.54 seconds of deterministic postprocessing,
plus an unavailable Agent-inference component.

The existing rejected local-model runs remain unmatched historical context:

- Qwen2.5-3B: 2,128.42 seconds, 26,266,725 recorded model tokens, B-cubed
  `.490861`, boundary `.261643`;
- Qwen3.6-27B recursive v4: 6,800,686 logical tokens and 3,070.96 seconds
  summed request time, B-cubed `.386034`, boundary `.090455`.

The 27B resumed wall was not a fresh full run, and neither rejected backend
supplies A2's missing cost.

## Registered decision

The registered deterministic hypothesis is supported:

1. source-packet construction and deterministic postprocessing reproduce the
   complete adopted A2 inputs;
2. all raw, recurrence, and A2 profiles are stock-pprof-readable and conserve
   exact mass; and
3. both fixed-mark widths have 1.17-second medians, below the registered
   two-second threshold.

RQ4 is materially stronger than the former fixed-input-only result: it now
separates the 8.36-minute source-packet reconstruction, 3.54-second
postprocessing, and 1.17-second replay. The remaining bounded gap is A2's
automatic-Agent inference telemetry. The paper may report the historical
54.36-minute workflow envelope only with the limitations above.
