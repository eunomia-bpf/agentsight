# Experiment Plan: End-to-End Automatic Annotation Cost

**Timestamp:** 2026-07-23T21:44:59-07:00  
**Status:** revised after independent plan review; approved for execution

## Research question and tested hypothesis

- Paper RQ, unchanged: **RQ4 — What is the cost of constructing a semantic
  profile?**
- Tested hypothesis: on the complete real CodeTrace population, the
  deterministic parts of first-profile construction and fixed-mark replay can
  be measured independently and complete with exact mass; after automatic
  marks exist, changing an additive width or replaying the profile is a
  low-single-second operation on the measured host.

This experiment answers the measured and currently observable cost of existing
backends. It does not select, train, or improve an annotation algorithm. The
adopted A2 model/provider inference time and usage were not instrumented and
remain unavailable.

## Offline pipeline under test

The measured endpoint begins with fixed normalized target operations plus the
released CodeTrace raw archives and ends with one stock-pprof-readable
`.pb.gz`:

1. join fixed normalized target operations to reconstructed source-native
   turns and emit source-only A2 packets;
2. produce semantic marks with one declared backend;
3. validate and fold those marks into pprof.

Live trace capture and the original agent task execution are excluded because
they occur before an exported trace exists. Model download is excluded from
steady-state construction; one-time model load is reported separately when a
local backend records it.

## Population

- all 405 retained CodeTraceBench sessions;
- 17,148 source-native turns;
- 20,866 operations;
- four agent frameworks;
- 494,862,929 provider-reported source tokens for the alternate-width replay.

Every method uses this complete population. No preflight subset or new
benchmark enters the result.

## Methods and baselines

### A. Adopted automatic Agent A2

Reuse the complete source-only automatic Agent output already adopted by RQ3.
The run occurred in two fixed waves:

1. the registered 41-session long-horizon collection; and
2. its disjoint 364-session complement.

For each wave, the packet manifest mtime is the beginning and the last
nonempty annotation-batch mtime is the end. Report the two intervals separately
and their sum only as a **historical artifact-time workflow envelope**. The
report must list the exact source paths, timestamps, batch counts, and session
coverage. These mutable filesystem timestamps include unknown dispatch,
scheduling, parallelism, idle time, and artifact writing; they are neither an
instrumented backend timer nor a lower bound on Agent inference. Provider/model
wall time and token usage are unavailable and must be reported as unavailable,
not estimated.

Freshly run the source-only packet exporter three times over all 405 sessions
to measure A2 packet construction from raw CodeTrace archives. Every full
deterministic run must reproduce the registered 405/17,148/20,866 population
and packet-session key set.

Freshly run the complete deterministic post-annotation path three times:
assemble both annotation waves, apply A2's root-only-prefix correction,
validate and join provider usage, materialize count/token inputs, then apply
the adopted action--object name canonicalizer. Compare every run with the
accepted A2 mark skeleton, prediction partition, and count/token masses. This
is A2 postprocessing, not Agent inference.

Reuse or rerun the current fixed A2 mark replay three times for operation and
token widths. Every output must load in stock pprof and conserve exact mass.

### B. Label-free recurrence: automatic non-Agent baseline

Run the current release binary three times on the same normalized
20,866-operation input with the already declared separate recurrence reference
corpus. Each invocation must directly emit one `.pb.gz`. Report median wall
time, all three wall times, largest peak RSS, output size, stock-pprof mass,
and ordinary RQ3 B-cubed/boundary quality from the already completed score.

This is the main low-cost automatic alternative. Its fixed reference corpus
is treated as a backend asset: target-time loading and inference are included,
while the historical cost of creating that reusable corpus is excluded, just
as model download and backend setup are excluded for A2. It does not receive
official stages or grouped calibration.

### C. Raw-action profile: serialization control

Run the current release binary three times over the same normalized operations
using the raw-action stack and no automatic semantic constructor. Report the
same system measurements and exact mass. This is a non-semantic lower-bound
control for parsing, folding, and serialization, not an annotation baseline.

The fixed-A2-mark runs are likewise replay/change-width controls, not another
automatic constructor.

### D. Existing local-model backends: cost--quality context

Do not rerun either complete local-model experiment:

- Qwen2.5-3B stateful transition backend: 405 sessions, 20,866 operations,
  26,266,725 recorded model tokens, 2,128.42 seconds complete inference wall,
  B-cubed F1 `.490861`, boundary F1 `.261643`;
- Qwen3.6-27B recursive v4: 405 sessions, 20,866 operations, 6,800,686 logical
  tokens, 3,070.96 seconds summed request time, B-cubed F1 `.386034`,
  boundary F1 `.090455`.

For recursive v4, the 1,762.63-second resumed wall time contains 256 cache hits
and is not a fresh 405-session latency. The sum of stored request timers spans
two executions and is not a directly observed end-to-end wall time. Both facts
must remain explicit. These rejected, unmatched backends are historical
cost--quality context only. They do not enter the hypothesis, decision, or
headline table and are not required paper rows.

## Common measurement boundary and controls

The paper-facing boundary is **offline post-export profile construction from
fixed normalized target operations**. A2 packet construction additionally
opens the released raw archives to recover source-native turns. Original task
execution, live capture, raw-to-normalized target construction, model download,
and one-time backend setup are excluded.

- A2 source adaptation includes raw-archive reconstruction and Agent packet
  construction because packets are specific to that backend.
- A2 deterministic postprocessing begins with completed annotation batches.
- Recurrence begins with the same normalized target operations and its fixed
  reference-corpus asset.
- Raw action begins with the same normalized target operations.
- Fixed-mark replay begins with the adopted normalized A2 operations and
  marks.

These rows expose component costs and control roles; they are not added into a
false rectangular "total" when their backend-specific starting assets differ.

## Measurements

Use ordinary systems measurements:

- wall-clock seconds;
- peak resident CPU memory where `/usr/bin/time` supplies it;
- model prompt, completion, and total tokens when supplied by the backend;
- complete sessions, turns, operations, and model-call counts;
- pprof output bytes and exact additive mass;
- per-session and per-1,000-operation rates derived only for interpretability.

No new scientific metric, custom score, budget cutoff, or compound scalar is
introduced. RQ3 quality values are copied from independently reviewed complete
runs and never recomputed or optimized inside RQ4.

## Repetitions and execution

- expensive automatic annotation: one already complete population run per
  backend;
- A2 packet construction from raw archives: three fresh complete deterministic
  runs;
- A2 deterministic assembly/root repair/canonicalization: three fresh complete
  runs;
- raw-action, recurrence, and fixed-mark pprof construction: three complete
  repetitions each;
- stock pprof readback and exact-mass verification: every output.

The implementation may use one small measurement script to invoke existing
commands, read existing summaries and filesystem timestamps, validate
population equality, and write JSON/Markdown results. It must not implement
another annotation algorithm.

## Fixed commands and host conditions

Working directory:
`/home/yunwei37/workspace/agentsight-research-semantic-flamegraph`.

Measured host: Linux `6.15.11-061511-generic`, Intel Core Ultra 9 285K,
24 online CPUs, 125 GiB RAM. No program-level concurrency flag is supplied.
The filesystem cache is not flushed; run one real 41-session source-adapter
preflight, exclude it from results, then execute three consecutive full runs
under the same warm-cache policy. Record GNU `/usr/bin/time` wall seconds and
peak RSS for every fresh command.

Release binary: `agentpprof 0.2.37`, SHA-256
`c560754b3e1c0496b914ce49ee0e17a4d8004e7702556cccaa5814f7e6843d9b`.

The A2 source-packet full command is:

```bash
python3 script/export_agent_operation_annotation_packets.py \
  --target-operations .agentsight/experiments/a2-canonical-v1/profile-inputs/operations-count.jsonl \
  --raw-root .agentsight/experiments/codetracebench-rq2/hub \
  --selection all --batches 12 --out OUT
```

The deterministic postprocessing command pair is:

```bash
python3 script/assemble_agent_operation_profile.py \
  --target-operations docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl \
  --operation-usage .agentsight/experiments/rq1-codetracebench-token-attribution-v1/full/operation-usage.jsonl \
  --packet-dir .agentsight/experiments/codex-agent-long-horizon-v1/packets \
  --packet-dir .agentsight/experiments/codex-agent-remaining-v1/packets \
  --annotation-dir .agentsight/experiments/codex-agent-long-horizon-v1/annotations \
  --annotation-dir .agentsight/experiments/codex-agent-remaining-v1/annotations \
  --contract-root-only-prefix \
  --canonical-names docs/tmp/build-and-evaluate/step-0067-20260722T135005-0700/experiment-001/canonical-names.json \
  --mode full --out ASSEMBLED_OUT
python3 script/canonicalize_operation_marks.py \
  --operation-marks ASSEMBLED_OUT/operation-marks.json \
  --operations ASSEMBLED_OUT/operations-count.jsonl \
  --reference-predictions ASSEMBLED_OUT/predictions.jsonl \
  --out-dir CANONICAL_OUT
```

The pprof commands use:

```bash
# raw-action serialization control
./agentpprof/target/release/agentpprof \
  --operation-file .agentsight/experiments/rq3-multiresolution-recurrence-v1/full/codetrace/target-input.jsonl \
  --view operations --stack action --deterministic-output -o RAW.pb.gz

# label-free recurrence alternative
./agentpprof/target/release/agentpprof \
  --operation-file .agentsight/experiments/rq3-multiresolution-recurrence-v1/full/codetrace/target-input.jsonl \
  --view operations --induce-operation-stack \
  --induce-reference-operation-file .agentsight/experiments/rq3-multiresolution-recurrence-v1/full/codetrace/reference-input.jsonl \
  --deterministic-output -o RECURRENCE.pb.gz

# fixed-mark replay control
./agentpprof/target/release/agentpprof \
  --operation-file .agentsight/experiments/a2-canonical-v1/profile-inputs/operations-count.jsonl \
  --operation-mark-file .agentsight/experiments/a2-canonical-v1/profile-inputs/operation-marks.json \
  --view operations --deterministic-output -o A2.pb.gz

# fixed-mark alternate-width replay control
./agentpprof/target/release/agentpprof \
  --operation-file .agentsight/experiments/a2-canonical-v1/profile-inputs/operations-tokens.jsonl \
  --operation-mark-file .agentsight/experiments/a2-canonical-v1/profile-inputs/operation-marks.json \
  --view tokens --deterministic-output -o A2-TOKENS.pb.gz
```

Every command writes to
`.agentsight/experiments/rq4-end-to-end-cost-v1/`. Completion requires all 405
sessions, 17,148 turns, and 20,866 operations; three successful observations
per deterministic component; stock-pprof readback for every profile; exact
20,866-operation mass; and exact 494,862,929-token mass for A2 token replay.

Before timing the full population, run one excluded real preflight over the
registered 41-session long-horizon subset. It must exercise all command paths:

1. export the 41 source-packet sessions from raw archives with
   `--selection long-horizon`;
2. assemble those packets with the matching 41-session annotation directory,
   `--contract-root-only-prefix`, and `--mode preflight`, then run the same name
   canonicalizer;
3. filter the normalized recurrence target by the 41 manifest session IDs and
   run raw-action and recurrence pprof construction with the unchanged
   reference asset; and
4. run operation- and token-width fixed-mark pprof construction on the
   preflight assembly output.

The preflight must reproduce 41 sessions and 5,750 operations, load all four
profiles in stock pprof, and conserve the corresponding operation/token mass.
Its times are diagnostic and excluded from the paper result.

## Decision and interpretation

The tested hypothesis is supported if:

1. source adaptation and deterministic A2 postprocessing reproduce the
   complete accepted population and marks;
2. the complete raw, recurrence, and A2 pprof outputs are valid and conserve
   exact mass;
3. median fixed-mark operation and token replays each remain at most 2 seconds
   on the measured host.

The A2 annotation inference component remains unmeasured. The historical
artifact-time envelope supplies workflow context only and cannot prove
annotation-cost dominance or be arithmetically combined with fresh stopwatch
measurements. A new A2 model run is not authorized because its nondeterministic
output would be a new backend-quality experiment, not a cost replay.

## Paper authorization

After independent review, WRITE may:

- replace the current fixed-input-only statement with the measured A2
  source-packet adaptation, deterministic postprocessing, and replay
  decomposition;
- distinguish first construction from fixed-mark replay;
- report the A2 historical artifact-time envelope, source-adapter time,
  deterministic postprocessing time, and current pprof replay time with their
  exact provenance;
- retain recurrence and raw action as low-cost baselines;
- state unavailable A2 provider usage plainly.
- continue to state that A2 model/provider inference timing is excluded and
  that only a historical artifact-time workflow envelope is available.

WRITE may not:

- call the resumed recursive-v4 wall time a fresh full run;
- call the historical mtime envelope Agent inference time or combine it with
  fresh component timers;
- call another backend's model tokens A2 usage;
- present rejected 3B/27B quality as a positive result;
- claim live capture overhead, online latency, pricing, or universal hardware
  scaling.
