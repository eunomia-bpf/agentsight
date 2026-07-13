# AgentNet FULL attempt 1 execution report

**Attempted:** 2026-07-13T03:55:30-07:00  
**Diagnosed and repaired:** 2026-07-13T03:59:36-07:00  
**Stage:** FULL, label-blind profile construction  
**Execution status:** `INVALID — REPAIRED, MUST RE-PREFLIGHT`  
**Scientific status:** `NOT_EVALUATED`

## Authorized command

```bash
python3 script/agentnet_cross_platform_eval.py full \
  --source docs/visexp/out/agentnet-rq2/source \
  --agentpprof-bin agentpprof/target/release/agentpprof \
  --out docs/visexp/out/agentnet-rq2/full \
  --bootstraps 10000 --max-bootstrap-attempts 50000 --seed 4204
```

FULL began only after independent REAL PREFLIGHT approval. It stopped during
the first predictor's real AgentProf count check, before either target-label
file reached a scorer and before any scientific metric or verdict existed.

## Exact failure

For the complete Darwin target, both the source expectation and real AgentProf
contained 99,295 raw-action operations and 2,220 groups, but their `Counter`
keys differed at one group:

| Side | Group key | Count |
|---|---|---:|
| converter expectation | `action:press;target:backspace-_;repeat_state:single` | 3 |
| AgentProf emitted | `action:press;target:backspace-;repeat_state:single` | 3 |

There were no other expected-only keys, observed-only keys, or count
differences. The fail-fast counter correctly prevented scoring.

## Root cause

AgentProf's public `safe_frame` encoding lowercases a frame, preserves its
allowed punctuation, replaces unsupported runs, and trims leading/trailing
underscores. The experiment's expected group key used the already-visible
source string without applying this final AgentProf emission rule.

The fixed preflight subset did not contain this edge value. The complete Darwin
population contains exactly three affected operations. This is an output-key
encoding boundary, not a source, label, feature, model, grouping, or metric
failure.

## Minimal repair

The converter now has one `agentprof_frame_value` function mirroring the public
AgentProf safe-frame encoding for visible profile fields. `method_key` uses this
value when constructing expected and saved emitted stack keys. AgentProf still
receives the original visible fields and remains the real profile constructor.

The repair does not change:

- any projection or risk-model feature value;
- the four pure AgentNet helpers;
- any prediction or label;
- which operations enter a profile;
- any profile field/depth, baseline, ranking, tie, metric, bootstrap, or
  verdict; or
- the RQ, hypothesis, paper, or story.

It only makes the scorer name a group exactly as AgentProf already names it.

## Verification after repair

The dedicated suite now passes 11/11 tests. Its real AgentProf integration
contains the trailing-underscore edge and confirms `backspace-_` is compared
against emitted `backspace-` without changing source features.

Two full-population, label-blind predictor/profile checks then completed:

| Direction | Reference operations | Target tasks | Target trajectories | Target operations | Model iterations | All AgentProf views exact |
|---|---:|---:|---:|---:|---:|---|
| Windows → Darwin | 239,710 | 5,168 | 5,198 | 99,295 | 18 / 1,000 | yes |
| Darwin → Windows | 99,295 | 12,364 | 12,427 | 239,710 | 12 / 1,000 | yes |

Complete view counts after repair:

| Target | Flat | Fixed session | Source native | Raw action | Semantic |
|---|---:|---:|---:|---:|---:|
| Darwin | 1 | 5,198 | 21,536 | 2,220 | 6,176 |
| Windows | 1 | 12,427 | 49,982 | 3,174 | 8,332 |

Every view reconstructs all target operations exactly. These checks used one
draw specification and no target scoring; they are implementation validation,
not partial scientific runs.

## Required transition

Because code changed after preflight, the previous FULL authorization is
consumed. An independent `research-experiment-design` implementation review
must approve the narrow repair, then the fixed REAL PREFLIGHT must rerun and be
reviewed before FULL restarts from clean outputs.
