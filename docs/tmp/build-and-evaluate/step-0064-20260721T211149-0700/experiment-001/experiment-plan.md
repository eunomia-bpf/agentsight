# Experiment plan — query-conditioned AgentCap task aggregation

Timestamp: 2026-07-21T21:11:49-07:00
Status: approved for execution

## User question and tested hypothesis

The user question is whether several real sessions from the same project/task
family can be labeled as a variable-depth task stack and then aggregated into
one useful flame graph. This is a product-shape prototype, not a claim that one
small hand-audited sample establishes paper-level semantic-tag accuracy.

Tested hypothesis: after replacing run-specific wording with a bounded set of
query-conditioned responsibilities, multiple AgentCap research-review traces
will share task frames while retaining source evidence and unequal path depth.
The resulting pprof should answer where review work accumulates and which
responsibilities recur across otherwise independent sessions.

## Real workload and bounded selection

Use four complete, real Codex review sessions already represented in the
source-native full run:

- R024 experiment/evaluator review;
- R025 experiment/evaluator review and repair verification;
- R035 artifact/document consistency review and repair verification;
- R081 paper-claim and top-conference evidence review.

Together they contain 326 source-native operations. They were selected because
they share the user-facing task family (review AgentCap research evidence and
changes) but exercise different review responsibilities. Inspecting every
AgentCap session is not required for this prototype. No operation in a selected
session may be sampled or dropped.

## Annotation policy

The shared root is `Review AgentCap research evidence`. Below it, use a small
canonical responsibility vocabulary derived from the user question and the
selected traces:

- establish review scope;
- inspect implementation;
- audit experiment evidence;
- validate execution;
- audit claims and documentation;
- synthesize findings;
- verify repairs.

An optional sub-responsibility is added only when the trace visibly performs a
more specific unit of work, such as comparing official evaluator semantics,
rerunning validation, or confirming resolution. Depth is therefore variable;
no fixed number of frames is required and missing levels are not padded.

Each session is labeled by contiguous source-line ranges. The annotator sees
the session's progress summaries and operations, then marks transition
positions. It does not invent one tag per operation. Adjacent operations inherit
the current path until a marked task transition. Every selected operation must
receive exactly one path.

Run and session identifiers are stored only as pprof evidence labels. They do
not enter the responsibility stack, because doing so would prevent aggregation.
The final stack projection is:

`task path (repeated, variable depth) → action → result`

This keeps the task hierarchy readable while retaining an evidence-oriented
lower level. Raw command/file objects remain in the normalized input for
inspection but are omitted from the first overview visualization.

## Artifact and checks

The prototype adapter may write intermediate normalized JSONL under ignored
`.agentsight/experiments/`. AgentPProf itself must emit only a standard
`.pb.gz` pprof artifact. Visualization must come from the existing Go pprof web
UI; no AgentPProf renderer or frontend is added.

Required checks:

1. all 326 selected operations are labeled exactly once;
2. event weight is conserved;
3. the task depth distribution contains more than one depth;
4. at least three canonical responsibilities aggregate operations from more
   than one session;
5. `go tool pprof` decodes the artifact and the shared root has cumulative
   value 326;
6. the captured flame graph is produced by the standard pprof UI.

The output is useful if a reader can see common review responsibilities and
drill back to distinct traces. It does not claim that this bounded vocabulary
generalizes to unrelated user queries without another first-pass taxonomy.
