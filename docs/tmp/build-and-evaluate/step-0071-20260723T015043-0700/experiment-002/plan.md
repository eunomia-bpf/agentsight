# Experiment 002 plan: current-binary RQ4 replay

Timestamp: 2026-07-23T01:50:43-07:00
Outer gate: EXPERIMENT
Research question: RQ4 — What is the cost of constructing a semantic profile?

## Why this experiment is necessary

The paper currently cites a complete four-workload scaling matrix and an A2
fixed-input supplement, both produced before the latest operation-name replay.
RQ4 must report measurements from the current checked-out release binary and
the current accepted inputs rather than treating old measurements as current.

## Fixed RQ and tested hypothesis

RQ4 and its scope remain unchanged:

> After operation annotations are fixed, the current AgentPProf binary
> constructs complete semantic pprof profiles with practical and predictable
> cost across the four public workloads and their union, and can replay the
> latest complete A2 CodeTrace input at both operation and token widths while
> exactly conserving additive mass.

This measures fixed-input parsing, mark replay, folding, and pprof
serialization. It does not measure capture, source adaptation, or automatic
Agent inference.

## Inputs

1. The same four complete normalized public operation files used by the
   accepted scaling matrix:
   AgentRewardBench, Satraj, OSWorld-Human, and AgentNet.
2. Their exact union.
3. The latest canonical A2 complete CodeTrace marks and operation/token input
   produced by Experiment 001.
4. The release binary built from the current source tree.

## Method

1. Build the release binary once.
2. Run the existing `script/rq4_profile_cost_scaling_eval.py` full matrix with
   three repetitions for semantic and matched raw-action profiles.
3. Run the same current binary three times for latest A2 operation-count and
   token-count profiles.
4. Load generated protobuf profiles with stock `go tool pprof`.
5. Check exact operation/token mass and report wall time and maximum RSS.

The current binary is built with:

```bash
cargo build --manifest-path agentpprof/Cargo.toml --release
git rev-parse HEAD
agentpprof/target/release/agentpprof --version
sha256sum agentpprof/target/release/agentpprof
```

The complete public matrix is:

```bash
python3 script/rq4_profile_cost_scaling_eval.py \
  --binary agentpprof/target/release/agentpprof \
  --out-dir .agentsight/experiments/rq4-cost-scaling-v2-current \
  --reps 3
```

The latest-A2 supplement invokes the same binary with
`--operation-mark-file
.agentsight/experiments/a2-canonical-v1/profile-inputs/operation-marks.json`,
once for the unchanged count and token operation files under
`.agentsight/experiments/a2-rootfix-v1/profile-inputs/`, three times each. For
each `rep` in `1 2 3`, the exact operation command is:

```bash
/usr/bin/time \
  -f '{"wall_s":%e,"max_rss_kb":%M,"exit_status":%x}' \
  -o .agentsight/experiments/a2-canonical-v1/cost/operations-rep-${rep}.time.json \
  agentpprof/target/release/agentpprof \
  --operation-file .agentsight/experiments/a2-rootfix-v1/profile-inputs/operations-count.jsonl \
  --operation-mark-file .agentsight/experiments/a2-canonical-v1/profile-inputs/operation-marks.json \
  --view operations --stack project,agent,operation --deterministic-output \
  -o .agentsight/experiments/a2-canonical-v1/cost/operations-rep-${rep}.pb.gz
```

The token command changes the operation file to
`operations-tokens.jsonl`, the view to `tokens`, and every output stem to
`tokens-rep-${rep}`.

## Current-binary currency replays outside RQ4 timing

These compatibility runs are not included in any RQ4 timing cell.

RQ1 copies the fixed Git annotation workspace to
`.agentsight/experiments/rq1-current-replay-v1/workspace/`, then runs:

```bash
agentpprof/target/release/agentpprof \
  --annotation-file .agentsight/experiments/rq1-current-replay-v1/workspace/annotation.json \
  --view operations --deterministic-output \
  -o .agentsight/experiments/rq1-current-replay-v1/profiles/git.operations.pb.gz
agentpprof/target/release/agentpprof \
  --annotation-file .agentsight/experiments/rq1-current-replay-v1/workspace/annotation.json \
  --view tokens --deterministic-output \
  -o .agentsight/experiments/rq1-current-replay-v1/profiles/git.tokens.pb.gz
```

RQ2 reruns the three Step 0070 candidate commands with the current binary and
unchanged canonical annotations:

```bash
python3 script/rq2_agent_segmentation_eval.py --benchmark agentprocess \
  --root docs/visexp/out/agentprocessbench-rq2/full \
  --packet-dir .agentsight/experiments/rq2-a0-v1/full/agentprocess/packets \
  --annotation-dir .agentsight/experiments/rq2-canonical-tags-v1/agentprocess/annotations \
  --binary agentpprof/target/release/agentpprof --mode full \
  --out .agentsight/experiments/rq2-canonical-tags-v2-current/agentprocess/results
python3 script/rq2_agent_segmentation_eval.py --benchmark hint \
  --root docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/loop-001-rq2-hintbench/results/full \
  --packet-dir .agentsight/experiments/rq2-a0-v1/full/hint/packets \
  --annotation-dir .agentsight/experiments/rq2-canonical-tags-v1/hint/annotations \
  --binary agentpprof/target/release/agentpprof --mode full \
  --out .agentsight/experiments/rq2-canonical-tags-v2-current/hint/results
python3 script/rq2_agent_segmentation_eval.py --benchmark trace \
  --root .agentsight/experiments/traceelephant-rq2-v1 \
  --packet-dir .agentsight/experiments/rq2-a0-v1/full/trace/packets \
  --annotation-dir .agentsight/experiments/rq2-canonical-tags-v1/trace/annotations \
  --binary agentpprof/target/release/agentpprof --mode full \
  --out .agentsight/experiments/rq2-canonical-tags-v2-current/trace/results
```

Completion requires both RQ1 profiles to be byte-identical to the paper figure
inputs and all three RQ2 per-query rows and summaries to be byte-identical to
Step 0070.

## Metrics

- Wall-clock construction time in seconds; three-run median is primary.
- Maximum resident set size in MiB.
- Complete input rows and exact additive output mass.
- Relative semantic-versus-raw overhead on the same union input.
- Operations/second, milliseconds/operation, monotonicity, linear-fit slope and
  R-squared, output size, stock-pprof readability, and the existing bounded
  R160 cache-mechanism observation.

## Success and interpretation

All 30 public-matrix invocations and all six A2 invocations must complete and
conserve mass. RSS is reported as the largest observation in each cell, not a
median. The result is a measured current-binary cost, not a universal
asymptotic claim. No particular speedup is required. Regressions are reported
honestly and diagnosed before paper synchronization; no workload or repetition
may be dropped.

## Outputs

- Complete current-binary scaling directory with all repetitions.
- Complete latest-A2 operation/token replay directory.
- Current Git commit, binary version, and binary SHA-256.
- Result review, comparison to the superseded measurements, and final RQ4
  paper numbers.
