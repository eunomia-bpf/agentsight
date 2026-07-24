# Experiment 001 plan: same-input attribution organization control

Timestamp: 2026-07-23T22:47:18-07:00
Status: PROPOSED
Research question: RQ1 — Does semantic profiling improve resource attribution?

## Scientific question

The current Git case shows that the shared `diagnose authentication` subtree
accounts for 105 of 489 operations and 2,103,587 of 4,558,192 tokens. The
missing comparison is whether the same raw evidence is directly organized as
one reusable responsibility in native trace and coarse action views.

This experiment asks one bounded explanatory question:

> Holding the three sessions, 489 operation samples, token weights, and source
> evidence fixed, how do native source, coarse action, and AgentProf semantic
> stacks organize the candidate-defined evidence belonging to the previously
> discovered SSH-authentication responsibility?

## Fixed input and tested hypothesis

The population is exactly the three real `git-multibranch` executions already
used by the paper:

- OpenHands with Claude Sonnet 4 Thinking;
- OpenHands with DeepSeek V3.2;
- Terminus2 with DeepSeek V3.2.

The count and token inputs are filtered from the already adopted complete A2
CodeTrace operation files by these three source-session identifiers. The
existing annotation workspace supplies the accepted semantic boundaries and
the source evidence IDs under `diagnose authentication`. No annotation is
changed or generated in this experiment.

This is a fixed post-hoc case projection, not an independent hypothesis test.
The task family and responsibility were selected after the prior semantic
result was observed. The explanatory expectation is that the accepted
AgentProf marks map these members to one cross-run semantic responsibility,
while:

1. native source organization partitions it by source session and call; and
2. coarse action organization distributes it over several generic action
   categories that do not identify the SSH-authentication responsibility.

## Compared organizations

All conditions use the same current `agentpprof 0.2.37` release binary and the
same 489 count/token samples. Every condition shares the outer prefix
`project,agent`, source-evidence labels, and the leaf suffix `call,tool`. Only
the middle organization differs.

1. **Native source hierarchy:**
   `project,agent,source_session,prompt,call,tool`.
   This is the source adapter's factual execution hierarchy and is a control,
   not a semantic competitor.
2. **Coarse action hierarchy:**
   `project,agent,action_kind,raw_action_key,call,tool`.
   This is a missing deterministic case-organization control, not the
   strongest automatic backend.
3. **AgentProf operation hierarchy:**
   `project,agent,operation,call,tool`, using the accepted semantic marks.

The adopted multi-resolution recurrence backend is the stronger existing
no-label comparison and is already evaluated on the complete CodeTrace
population in RQ3. This case does not rerun or replace that population
comparison.

The experiment will regenerate all six count/token profiles with the same
current binary and filtered rows. A mechanical representation adapter converts
the already accepted workspace paths into the CLI operation-mark format; it
does not infer, rename, or change a boundary.

## Procedure

1. Filter the complete adopted operation-count and token JSONL files to the
   three exact source-session IDs.
2. Assert equality of the complete
   `(source_session, evidence_id, value)` multiset across all conditions,
   489 rows in both files, and exact token mass 4,558,192.
3. Convert the accepted workspace paths to an equivalent operation-mark file.
   Verify every one of the 489 evidence IDs receives exactly its pre-existing
   path and that no boundary or name changes.
4. Construct native-source, coarse-action, and AgentProf `.pb.gz` profiles for
   both operation and token widths with deterministic output.
5. Open every profile with stock `go tool pprof` and verify exact additive
   mass.
6. Select the accepted `diagnose authentication` source-evidence set from the
   annotation workspace. Join only by stable evidence ID to the fixed
   operation rows.
7. Report how those 105 samples and 2,103,587 tokens are distributed across
   source sessions, source calls, coarse action kinds, and raw action keys.
8. Verify with stock pprof labels that the AgentProf semantic subtree retains
   the corresponding source-session evidence and reproduces the accepted
   responsibility's count/token mass.

## Authoritative execution

The fixed source-session IDs are:

```text
openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-git-multibranch-75c1745e
openhands-DeepSeek__DeepSeek-V3.2-git-multibranch-0bbc5d81
terminus2-DeepSeek__DeepSeek-V3.2-git-multibranch-c063fb97
```

The authoritative inputs and tools are:

```text
COUNT=.agentsight/experiments/a2-rootfix-v1/profile-inputs/operations-count.jsonl
TOKENS=.agentsight/experiments/a2-rootfix-v1/profile-inputs/operations-tokens.jsonl
TRACE=.agentsight/experiments/rq1-current-replay-v1/workspace/trace.jsonl
BINARY=agentpprof/target/release/agentpprof
OUT=.agentsight/experiments/rq1-matched-organization-v1
```

Create `OUT`, then filter both inputs with the same literal anchored regular
expression:

```bash
SESSION_RE='^(openhands-Anthropic__Claude-Sonnet-4-20250514-Thinking-git-multibranch-75c1745e|openhands-DeepSeek__DeepSeek-V3.2-git-multibranch-0bbc5d81|terminus2-DeepSeek__DeepSeek-V3.2-git-multibranch-c063fb97)$'
jq -c --arg re "$SESSION_RE" \
  'select(.fields.source_session | test($re))' "$COUNT" \
  > "$OUT/operations-count.jsonl"
jq -c --arg re "$SESSION_RE" \
  'select(.fields.source_session | test($re))' "$TOKENS" \
  > "$OUT/operations-tokens.jsonl"
```

The accepted workspace paths are mechanically converted to operation marks by
this fixed adapter. `operation:<display name>` is only a stable JSON ID; the
display name is unchanged.

```bash
jq -s '
  [ .[] | select(.kind == "tool") |
    (.id | capture("^tool:(?<sequence>.*):(?<step>[^:]+)$")) as $id |
    {sequence:$id.sequence,
     start_operation_id:($id.sequence + ":" + $id.step),
     path:.path}
  ] as $rows |
  ($rows | map(.sequence) | unique) as $sequences |
  {
    sequence_field:"source_session",
    id_field:"evidence_id",
    operation_names:
      ([ $rows[].path[] ] | unique |
       map({key:("operation:" + .), value:.}) | from_entries),
    marks:
      ([ $sequences[] as $sequence |
         (reduce ($rows[] | select(.sequence == $sequence)) as $row
           ({previous:null, emitted:[]};
            if .previous == $row.path then .
            else {previous:$row.path,
                  emitted:(.emitted + [{
                    sequence:$row.sequence,
                    start_operation_id:$row.start_operation_id,
                    operation_ids:[$row.path[] | ("operation:" + .)]
                  }])}
            end) | .emitted) ] | add)
  }' "$TRACE" > "$OUT/accepted-operation-marks.json"
```

Before the full run, a real preflight filters the first listed session from
`operations-count.jsonl`, filters `accepted-operation-marks.json` to the same
sequence, runs the semantic count command with the final binary and final
semantic stack string, and opens the result with `go tool pprof -top`. The
preflight is diagnostic only and contributes no paper number.

The complete run executes these three commands once on each of
`operations-count.jsonl`/`--view operations` and
`operations-tokens.jsonl`/`--view tokens`:

```bash
"$BINARY" --operation-file "$INPUT" --view "$VIEW" \
  --stack project,agent,source_session,prompt,call,tool \
  --deterministic-output -o "$OUT/native-$VIEW.pb.gz"

"$BINARY" --operation-file "$INPUT" --view "$VIEW" \
  --stack project,agent,action_kind,raw_action_key,call,tool \
  --deterministic-output -o "$OUT/coarse-$VIEW.pb.gz"

"$BINARY" --operation-file "$INPUT" --view "$VIEW" \
  --operation-mark-file "$OUT/accepted-operation-marks.json" \
  --stack project,agent,operation,call,tool \
  --deterministic-output -o "$OUT/semantic-$VIEW.pb.gz"
```

All six files are inspected with:

```bash
go tool pprof -top "$PROFILE"
go tool pprof -tags "$PROFILE"
```

Completion requires 489 unique evidence IDs per width, identical
`(source_session,evidence_id,value)` multisets across organizations, exact
total masses of 489 and 4,558,192, exact expansion of the accepted path for
all 489 rows, six stock-pprof-readable outputs, and reproduction of the fixed
105-operation/2,103,587-token responsibility membership and mass.

## Measurements

Primary evidence is standard pprof cumulative sample attribution:

- total operation and token mass;
- cumulative mass under the semantic responsibility;
- pprof source labels retained under the focused subtree.

Descriptive organization statistics are:

- unique stack count per view;
- source-session and source-call counts;
- the full distribution of the responsibility's mass over coarse action
  kinds and raw action keys.

These are topology and composition descriptions, not new accuracy metrics.
The experiment does not introduce a custom score, threshold, or statistical
significance test for a three-execution case study.

## Leakage and fairness

- All conditions receive the exact same filtered rows and full
  `(source_session, evidence_id, value)` multiset through the same
  `agentpprof 0.2.37` binary.
- The accepted semantic annotation is never used to construct either control.
- It is used only after construction to identify the same source-evidence set
  for explanatory projection across views.
- No outcome label, hidden benchmark key, or test oracle is used.
- The Git task family and SSH responsibility are post-hoc selections from the
  prior semantic case. Once selected, all three executions and every operation
  are retained; no row is dropped afterward.

## Acceptance and interpretation

The run is valid only if every profile opens in stock pprof, exactly conserves
its input mass, and the semantic replay reproduces the accepted responsibility
membership and count/token mass. The result will be reported as a descriptive
matched organization contrast, not as `supported`/`contradicted` evidence of
independent superiority. Any mismatch or weaker pattern must be reported
without changing the RQ or annotations.

The paper may use this as a matched control for the RQ1 case. It may not claim
universal diagnostic superiority, annotation correctness, or a population
effect from these three executions.

## Expected outputs

- filtered count and token operation inputs;
- six deterministic `.pb.gz` profiles;
- stock-pprof inspection output and exact-mass checks;
- the complete evidence projection table;
- one result report and one independent result review.
