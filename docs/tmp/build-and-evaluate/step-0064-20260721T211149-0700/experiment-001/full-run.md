# Full run — AgentCap query-conditioned aggregation

Timestamp: 2026-07-21T21:16:00-07:00
Execution status: complete

## Inputs and execution

The run used four complete Codex sessions selected from the source-native full
corpus: R024, R025, R035, and R081. They are independent reviews of AgentCap
research changes and together contain 326 normalized operations.

The experiment adapter marked a small number of contiguous source-line
transitions and emitted AgentPProf's normalized operation input:

```bash
python3 script/agentcap_task_aggregation_case.py \
  --input /tmp/agentcap-selected-ops.jsonl \
  --output .agentsight/experiments/agentcap-query-aggregation-v1/operations.jsonl \
  --summary .agentsight/experiments/agentcap-query-aggregation-v1/summary.json

agentpprof/target/debug/agentpprof \
  --operation-file .agentsight/experiments/agentcap-query-aggregation-v1/operations.jsonl \
  --view operations \
  --stack task,action \
  --format pprof \
  --deterministic-output \
  --output docs/visexp/out/agentcap-query-aggregation-v1/agentcap-review-operations.pb.gz
```

The image was captured from `go tool pprof -http .../agentcap-review-operations.pb.gz`
at its standard `/ui/flamegraph` route. AgentPProf did not render an image or
emit an alternate product format.

## Coverage and conservation

| Trace | Operations |
|---|---:|
| R024 | 80 |
| R025 | 75 |
| R035 | 76 |
| R081 | 95 |
| **Total** | **326** |

All 326 input operations produced exactly one profile record and the summed
event weight remained 326. The task portion of the stack has two frames for
104 operations and three frames for 222 operations; no padding or depth cap was
used.

AgentPProf reported 326 samples and 66 unique `task → action` stacks. The
standard Go reader decoded the artifact. Focusing on
`task:review_agentcap_research_evidence` returns all 326 samples. The profile
SHA-256 is
`66775ebded43be9194f9bacbbe53acbd4c1744f098f49c976e2a8efbb77bbe08`.

## Aggregation result

| Shared responsibility | Operations | Contributing traces |
|---|---:|---:|
| Verify repairs | 95 | 4 |
| Audit experiment evidence | 72 | 3 |
| Establish review scope | 47 | 4 |
| Audit claims and documentation | 37 | 2 |
| Validate execution | 30 | 2 |
| Synthesize findings | 29 | 4 |
| Inspect implementation | 16 | 3 |

This is genuine aggregation rather than concatenation under run names: the
profile stores R024/R025/R035/R081 as `source_session` evidence labels, while
all four fold through the same `Review AgentCap research evidence` root and
shared responsibility frames.

The largest recurring responsibility is repair verification. Within it, the
profile separates rerunning validation (35 operations), inspecting repaired
implementation (34), and inspecting repaired evidence (26). Experiment-evidence
auditing similarly separates result-artifact inspection, official-evaluator
comparison, and statistical-semantics inspection.

## Validation

The adapter's four unit tests pass. They check inclusive transitions, variable
depth, the shared root/final resolution path, and correction of a known
source-native action label in these read-only reviews. `go tool pprof -tags`
reports the expected source totals of 80, 75, 76, and 95.

The source-native action `Update repository` was misleading for read-only
`git status`/`git diff` inspection. The case adapter renames it to `Inspect
repository state`; it does not change AgentPProf's product implementation.

## Limitations

- The responsibility vocabulary is query-conditioned and manually marked at
  session boundaries. This tests the interface and aggregation shape, not an
  automatic tagger's accuracy.
- Four deliberately varied complete sessions are sufficient for the prototype,
  but they do not represent every AgentCap task family.
- The overview omits raw command/file objects to avoid fragmenting the graph.
  Source-session and evidence-id labels retain a path back to the normalized
  operations.
- Width is operation count. Provider token fields in these source sessions are
  not used because several are cumulative accounting snapshots rather than
  clean per-operation increments.
