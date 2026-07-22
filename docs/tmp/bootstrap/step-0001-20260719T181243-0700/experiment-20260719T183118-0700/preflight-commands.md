# Real Preflight Commands

These commands freeze one goal episode and exercise the real annotation, diagnosis, audit,
and scoring path. They use source-native records and ordinary shell tools; they do not
define another Agent event schema.

## Versions And Paths

```bash
export RESEARCH=/home/yunwei37/workspace/agentsight-agent-nebula-research
export TARGET=/home/yunwei37/workspace/agentskill-observability-paper
export EXPERIMENT=$RESEARCH/docs/tmp/bootstrap/step-0001-20260719T181243-0700/experiment-20260719T183118-0700
export RUN=$EXPERIMENT/raw/preflight-agentskill-citations
export CLAUDE_PROJECT=/home/yunwei37/.claude/projects/-home-yunwei37-workspace-agentskill-observability-paper
export PARENT_ID=7b3e1535-05cf-4821-871b-d476feba6602
export START_ISO=2026-07-12T04:40:23.535Z
export END_ISO=2026-07-12T04:58:31.093Z
export START_MS=1783831223535
export END_MS=1783832311093
mkdir -p "$RUN"
claude --version
git -C "$RESEARCH" rev-parse HEAD
sha256sum "$RESEARCH/agentvis/src/repository.rs" \
  "$RESEARCH/agentvis/target/release/agentvis" > "$RUN/implementation.sha256"
```

Expected Claude CLI: `2.1.215`. Diagnosis model: `claude-sonnet-4-6`.

## Freeze The Goal Episode

Generate the existing direct repository trace, then retain only the parent citation-check
session, its three citation-search subagents, and actions before the next top-level goal.

```bash
"$RESEARCH/agentvis/target/release/agentvis" "$TARGET" -o "$RUN/full.html"
perl -0777 -ne \
  'if (/AgentVis\.initialize\((\{.*\})\)<\/script><\/body><\/html>\z/s) { print $1 }' \
  "$RUN/full.html" > "$RUN/full.json"
```

```bash
printf '%s\n' \
  "claude:$PARENT_ID" \
  'claude:agent-a324f2122f7a67f1a' \
  'claude:agent-a49e577379a2a3c78' \
  'claude:agent-a4b52863d2137c18c' > "$RUN/session-ids.txt"

printf '%s\n' \
  "$CLAUDE_PROJECT/$PARENT_ID.jsonl" \
  "$CLAUDE_PROJECT/$PARENT_ID/subagents/agent-a324f2122f7a67f1a.jsonl" \
  "$CLAUDE_PROJECT/$PARENT_ID/subagents/agent-a49e577379a2a3c78.jsonl" \
  "$CLAUDE_PROJECT/$PARENT_ID/subagents/agent-a4b52863d2137c18c.jsonl" \
  > "$RUN/original-source-paths.txt"

mkdir -p "$RUN/raw-slices"
: > "$RUN/source-paths.txt"
while IFS= read -r path; do
  test -f "$path"
  slice="$RUN/raw-slices/$(basename "$path")"
  jq -c --arg start "$START_ISO" --arg end "$END_ISO" \
    'select(.timestamp? >= $start and .timestamp? < $end)' \
    "$path" > "$slice"
  jq -se --arg start "$START_ISO" --arg end "$END_ISO" \
    'all(.timestamp? >= $start and .timestamp? < $end)' "$slice"
  printf '%s\n' "$slice" >> "$RUN/source-paths.txt"
done < "$RUN/original-source-paths.txt"
test "$(wc -l < "$RUN/source-paths.txt")" -eq 4
test "$(find "$RUN/raw-slices" -maxdepth 1 -type f -name '*.jsonl' | wc -l)" -eq 4
```

```bash
jq --argjson start "$START_MS" --argjson end "$END_MS" \
  --rawfile sessions "$RUN/session-ids.txt" '
    ($sessions | split("\n") | map(select(length > 0))) as $session_ids
    | .events |= [
        .[]
        | select(.ts_ms >= $start and .ts_ms < $end)
        | select(.session_id as $id | ($session_ids | index($id)) != null)
      ]
    | .commits = []
    | .meta.window_start_ms = $start
    | .meta.window_end_ms = $end
    | .meta.goal_episode = "check-paper-citations"
  ' "$RUN/full.json" > "$RUN/episode.json"
```

The following assertions fail if the event boundary or shared evidence namespace drifts:

```bash
jq -e '
  (.events | length) == 115 and
  ([.events[].session_id] | unique | length) == 4 and
  ([.events[].actions | length] | add) == 41 and
  ([.events[] | select(.source_call_id == null)] | length) == 0 and
  ([.events[] | (.session_id + "#" + .source_call_id)] | unique | length) == 115
' "$RUN/episode.json"
```

The parent record contains later goals, so it is never presented unbounded. Save the
boundary evidence for audit:

```bash
jq -r --arg start "$START_ISO" --arg end "$END_ISO" '
  select(.type == "user" and .timestamp >= $start and .timestamp <= $end)
  | .timestamp + "\t" +
    (.message.content |
      if type == "string" then .
      else [.[]? | select(.type == "text") | .text] | join(" ")
      end)
' "$CLAUDE_PROJECT/$PARENT_ID.jsonl" > "$RUN/goal-boundary.txt"
```

## Freeze The Native Final Report

Only assistant text inside the same half-open interval is eligible. Later messages from the
parent record cannot leak into this condition.

```bash
jq -s --arg start "$START_ISO" --arg end "$END_ISO" '
  [.[]
   | select(.type == "assistant" and .timestamp >= $start and .timestamp < $end)
   | .message.content[]?
   | select(.type == "text")
   | .text]
  | last // ""
' "$CLAUDE_PROJECT/$PARENT_ID.jsonl" > "$RUN/final-report.json"
jq -e 'type == "string" and length > 0' "$RUN/final-report.json"
```

## Condition Access And Evidence IDs

- **Raw-log retrieval:** read-only `rg`, `jq`, `sed`, and `wc` over the four frozen native
  slices in `source-paths.txt`, with every query bounded to 200 returned lines. The slices
  already enforce `[START_ISO, END_ISO)`; later parent actions are physically absent.
- **Workspace trajectory:** read-only `jq` over `episode.json`, plus bounded source lookup
  over the same four paths when exact semantic evidence is needed.
- **Native final report:** only `final-report.json` extracted above.
- **Counts control:** one frozen Markdown table derived from `episode.json` and the same
  outcome evidence.

All conditions cite an action as `<session_id>#<source_call_id>`. In the raw records,
`source_call_id` is the native Tool `id`; in `episode.json`, both fields are adjacent. No
condition receives generated semantic labels. Final artifact/outcome evidence is either
available to all compared conditions or omitted from all.

## Supervisor Invocations

Each condition differs only in its evidence-location paragraph. The common contract limits
the Agent to eight read-only evidence queries of at most 200 lines and requires one JSON
diagnosis. `stream-json --verbose` retains every tool call/result, elapsed time, and usage.

```bash
cp "$EXPERIMENT/prompt-workspace.md" "$RUN/"
cp "$EXPERIMENT/prompt-raw.md" "$RUN/"
cp "$EXPERIMENT/prompt-final-reports.md" "$RUN/"
jq -r . "$RUN/final-report.json" >> "$RUN/prompt-final-reports.md"
printf '\n%s\n' '--- END FROZEN FINAL REPORT ---' >> "$RUN/prompt-final-reports.md"

git -C "$RESEARCH" status --porcelain=v1 > "$RUN/research-status-before.txt"
git -C "$TARGET" status --porcelain=v1 > "$RUN/target-status-before.txt"
(
  sha256sum "$RUN/episode.json"
  find "$RUN/raw-slices" -maxdepth 1 -type f -name '*.jsonl' -print0 \
    | sort -z | xargs -0 sha256sum
) > "$RUN/evidence-before.sha256"
```

```bash
claude -p \
  --model claude-sonnet-4-6 \
  --safe-mode \
  --no-session-persistence \
  --permission-mode bypassPermissions \
  --tools "Bash,Read" \
  --max-budget-usd 0.50 \
  --output-format stream-json \
  --verbose \
  "$(cat "$RUN/prompt-workspace.md")" \
  > "$RUN/prediction-workspace-r1.jsonl"
```

The raw invocation substitutes `prompt-raw.md` and `prediction-raw-r1.jsonl`. The final-
report invocation substitutes `prompt-final-reports.md` and
`prediction-final-reports-r1.jsonl` and sets `--tools ""`. Any run that writes files,
exceeds eight evidence queries, returns more than 200 evidence lines in one query, reads
outside the frozen paths or interval, or fails to terminate is retained and marked invalid;
it is not repaired against ground truth.

## Tool-Call Audit

For both tool-using conditions, extract every native Tool call and its matched result-line
count from the retained stream. This command fails the mechanical query-count, tool-name,
and result-size limits:

```bash
for condition in workspace raw; do
  jq -s '
    def text:
      if type == "string" then .
      elif type == "array" then
        map(if type == "string" then .
            elif type == "object" and has("text") then .text
            else tostring end) | join("\n")
      elif . == null then ""
      else tostring end;
    [.[]
     | select(.type == "assistant")
     | .message.content[]?
     | select(.type == "tool_use")
     | {id, name, input}] as $calls
    | [.[]
       | select(.type == "user")
       | .message.content[]?
       | select(.type == "tool_result")
       | {id: .tool_use_id,
          result_lines: (.content | text | split("\n") | length)}] as $results
    | {calls: [$calls[] as $call
        | ($results | map(select(.id == $call.id)) | first) as $result
        | $call + {result_lines: ($result.result_lines // 0)}]}
  ' "$RUN/prediction-$condition-r1.jsonl" > "$RUN/tool-audit-$condition.json"

  jq -e '
    (.calls | length) <= 8 and
    (.calls | all(.name == "Bash" or .name == "Read")) and
    (.calls | all(.result_lines <= 200))
  ' "$RUN/tool-audit-$condition.json"

  jq -r '.calls[]
    | [.id, .name, (.result_lines | tostring), (.input | tojson)]
    | @tsv' "$RUN/tool-audit-$condition.json" > "$RUN/tool-audit-$condition.tsv"
done
```

Verify that the Agent did not mutate the evidence or either repository:

```bash
git -C "$RESEARCH" status --porcelain=v1 > "$RUN/research-status-after.txt"
git -C "$TARGET" status --porcelain=v1 > "$RUN/target-status-after.txt"
diff -u "$RUN/research-status-before.txt" "$RUN/research-status-after.txt"
diff -u "$RUN/target-status-before.txt" "$RUN/target-status-after.txt"
(
  sha256sum "$RUN/episode.json"
  find "$RUN/raw-slices" -maxdepth 1 -type f -name '*.jsonl' -print0 \
    | sort -z | xargs -0 sha256sum
) > "$RUN/evidence-after.sha256"
diff -u "$RUN/evidence-before.sha256" "$RUN/evidence-after.sha256"
```

Finally, an auditor reads both `tool-audit-*.tsv` files and records PASS/FAIL plus the
offending call ID, if any, in `tool-audit-review.md`. PASS requires every Bash command to
use only `jq`, `rg`, `sed`, or `wc`; every Read/Bash path to remain under the run directory;
no redirection, mutation command, network command, subprocess, or access to the original
unbounded parent file; and exact correspondence between Tool calls and retained results.
This manual path/command check is required because string matching cannot soundly prove that
an arbitrary shell command is read-only. The signed audit artifact is part of preflight
completion, not optional prose.

## Parse And Score

Two independent full-source annotations and their adjudication produce `annotation-a.json`,
`annotation-b.json`, and `gold.json` in the run directory using the prediction schema from
`annotation-guide.md`. These annotations are dependency evidence only, not paper results.
Extract the model result without editing it:

```bash
for condition in workspace raw final-reports; do
  jq -rs -r '[.[] | select(.type == "result")] | last.result' \
    "$RUN/prediction-$condition-r1.jsonl" \
    | jq -e . > "$RUN/prediction-$condition-r1.json"
done
```

Validate the required fields before scoring:

```bash
for prediction in "$RUN"/prediction-*-r1.json; do
  jq -e '
    ([.stagnation, .goal_drift, .validation_gap, .harness_waste,
      .healthy_progress, .insufficient_evidence] | all(type == "boolean")) and
    (.evidence | type == "object") and
    (.intervention_recommended | type == "boolean") and
    (.confidence | type == "number" and . >= 0 and . <= 1)
  ' "$prediction"
done
```

Run the executable preflight scorer against the frozen adjudicated gold:

```bash
for condition in workspace raw final-reports; do
  jq -n \
    --slurpfile gold "$RUN/gold.json" \
    --slurpfile pred "$RUN/prediction-$condition-r1.json" \
    -f "$EXPERIMENT/score-preflight.jq" \
    > "$RUN/metrics-$condition-r1.json"
done
```

Preflight completes only when the boundary assertions pass, two independent annotations
have been adjudicated, all three diagnosis runs terminate with retained raw streams, the
tool-call audit passes, and the scorer produces metrics from raw predictions. A preflight
result is dependency evidence and is not entered as a paper result.
