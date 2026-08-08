# Report export snapshot schema

`agentsight report export -o snapshot.json` writes a JSON snapshot of the
materialized view. The same shape is returned by `GET /api/v1/snapshot`.
This document describes schema version 1.

## Compatibility

Consumers should check `schema_version` before reading the rest of the
snapshot and reject versions they do not support. New fields may be added to an
existing version, so consumers should ignore unknown fields. Removing or
renaming a field, changing its JSON type, or changing its meaning
incompatibly requires a schema-version bump.

Every field listed below is emitted. A nullable field is emitted as `null`
when AgentSight does not have a value; arrays are emitted as empty arrays.
`generated_at` is an RFC 3339 UTC timestamp.

| Top-level field | Type | May contain captured content? | Meaning |
| --- | --- | --- | --- |
| `schema_version` | integer | No | Snapshot schema version; currently `1`. |
| `generated_at` | string | No | Time at which AgentSight generated the export. |
| `summary` | object | No | Aggregate counts and the covered time range. |
| `token_summary` | array | Metadata | Token totals grouped by model. |
| `network_targets` | array | Yes | Observed network destinations and request paths. |
| `process_nodes` | array | Yes | Observed process metadata and command lines. |
| `audit_events` | array | Yes | Bounded event history; see `summary.audit_limit`. |
| `resource_samples` | array | Metadata | Process CPU and memory samples. |
| `sessions` | array | Yes | Agent-session summaries and source attributes. |
| `tool_calls` | array | Yes | Observed tool calls, including inputs and outputs when available. |

The export does not include the full `llm_calls` or token-usage row sets.
Their totals are available through `summary` and `token_summary`.

## `summary`

| Field | Type | Nullable | Meaning |
| --- | --- | --- | --- |
| `source` | string | No | View source, such as `materialized_view` or `agent_native_session`. |
| `view_events` | integer | No | Total materialized rows counted by the view. |
| `llm_calls` | integer | No | Number of observed LLM calls. |
| `token_usage_rows` | integer | No | Number of token-usage rows used for aggregation. |
| `audit_events` | integer | No | Total audit-event count before export limiting. |
| `sessions` | integer | No | Number of observed sessions. |
| `input_tokens` | integer | No | Aggregated input tokens. |
| `output_tokens` | integer | No | Aggregated output tokens. |
| `total_tokens` | integer | No | Aggregated total tokens. |
| `start_timestamp_ms` | integer | Yes | Earliest covered Unix timestamp in milliseconds. |
| `end_timestamp_ms` | integer | Yes | Latest covered Unix timestamp in milliseconds. |
| `audit_limit` | integer | No | Maximum number of recent audit rows included in `audit_events`. |

## `token_summary[]`

| Field | Type | Nullable | May contain captured content? |
| --- | --- | --- | --- |
| `group` | string | No | Model or grouping identifier; metadata only. |
| `input_tokens` | integer | No | No. |
| `output_tokens` | integer | No | No. |
| `cache_creation_tokens` | integer | No | No. |
| `cache_read_tokens` | integer | No | No. |
| `total_tokens` | integer | No | No. |
| `calls` | integer | No | No. |
| `sessions` | integer | No | No. |

## `network_targets[]`

| Field | Type | Nullable | May contain captured content? |
| --- | --- | --- | --- |
| `pid` | integer | Yes | No. |
| `comm` | string | Yes | Process metadata. |
| `host` | string | No | Yes; observed destination host. |
| `path` | string | Yes | **Yes.** Raw observed request path; not generally normalized or redacted. |
| `count` | integer | No | No. |
| `error_count` | integer | No | No. |
| `first_timestamp_ms` | integer | Yes | No. |
| `last_timestamp_ms` | integer | Yes | No. |

## `process_nodes[]`

| Field | Type | Nullable | May contain captured content? |
| --- | --- | --- | --- |
| `id` | string | No | Identifier metadata. |
| `pid` | integer | No | No. |
| `ppid` | integer | Yes | No. |
| `root_pid` | integer | Yes | No. |
| `start_timestamp_ms` | integer | Yes | No. |
| `end_timestamp_ms` | integer | Yes | No. |
| `comm` | string | Yes | Process metadata. |
| `command` | string | Yes | Yes; may contain the executable or command text. |
| `argv` | array of strings | No | **Yes; may include user data, paths, tokens, or secrets.** |
| `cwd` | string | Yes | Yes; may expose user names and filesystem layout. |
| `exit_code` | integer | Yes | No. |
| `status` | string | Yes | No. |
| `view_source` | string | No | No. |
| `confidence` | number | Yes | No. |

## `audit_events[]`

| Field | Type | Nullable | May contain captured content? |
| --- | --- | --- | --- |
| `id` | string | No | Identifier metadata. |
| `timestamp_ms` | integer | No | No. |
| `audit_type` | string | No | No. |
| `pid` | integer | Yes | No. |
| `comm` | string | Yes | Process metadata. |
| `subject` | string | Yes | Yes; source-dependent subject. |
| `action` | string | Yes | Usually categorical metadata. |
| `target` | string | Yes | **Yes; commonly a file, process, or network target.** |
| `status` | string | Yes | Usually categorical metadata. |
| `summary` | string | Yes | Yes; source-derived event summary. |
| `details` | any JSON value | No | **Yes; arbitrary source event details.** |
| `view_source` | string | No | No; identifies captured, reconstructed, agent-native, or legacy-unknown provenance. |
| `confidence` | number | Yes | No; source-specific confidence in the row correlation or reconstruction. |

`view_source` describes the lineage of each row, not the identity of the logical
operation. Its values are `view` for rows emitted directly from captured events,
`sqlite` for rows reconstructed from normalized persisted rows,
`agent_native_session` for rows parsed from native session files, and `unknown`
for legacy or otherwise unclassified evidence. One logical LLM call can therefore
have a directly captured `call` row and a reconstructed `request` row with different
sources. `confidence` is likewise row-specific: captured rows reflect event-correlation
confidence, while reconstructed rows reflect extraction and lineage confidence. It
must not be compared across sources as a global probability.

## `resource_samples[]`

| Field | Type | Nullable | May contain captured content? |
| --- | --- | --- | --- |
| `timestamp_ms` | integer | No | No. |
| `pid` | integer | Yes | No. |
| `comm` | string | Yes | Process metadata. |
| `cpu_percent` | number | Yes | No. |
| `rss_mb` | integer | Yes | No. |

## `sessions[]`

| Field | Type | Nullable | May contain captured content? |
| --- | --- | --- | --- |
| `id` | string | No | Session identifier metadata. |
| `agent_type` | string | No | No. |
| `start_timestamp_ms` | integer | No | No. |
| `end_timestamp_ms` | integer | Yes | No. |
| `status` | string | No | No. |
| `model` | string | Yes | Model identifier metadata. |
| `input_tokens` | integer | No | No. |
| `output_tokens` | integer | No | No. |
| `total_tokens` | integer | No | No. |
| `view_source` | string | No | No. |
| `confidence` | number | Yes | No. |
| `attributes` | any JSON value | No | **Yes; arbitrary source-specific session attributes.** |

## `tool_calls[]`

| Field | Type | Nullable | May contain captured content? |
| --- | --- | --- | --- |
| `id` | string | No | Identifier metadata. |
| `session_id` | string | Yes | Session identifier metadata. |
| `conversation_id` | string | Yes | Conversation identifier metadata. |
| `timestamp_ms` | integer | No | No. |
| `tool_name` | string | Yes | Tool-name metadata. |
| `tool_call_id` | string | Yes | Tool-call identifier metadata. |
| `start_timestamp_ms` | integer | Yes | No. |
| `end_timestamp_ms` | integer | Yes | No. |
| `duration_ms` | integer | Yes | No. |
| `status` | string | Yes | Usually categorical metadata. |
| `input` | any JSON value | No | **Yes; captured tool arguments or request content.** |
| `output` | any JSON value | No | **Yes; captured tool results or response content.** |
| `related_pid` | integer | Yes | No. |
| `related_event_id` | string | Yes | Identifier metadata. |
| `view_source` | string | No | No. |
| `confidence` | number | Yes | No. |

## Handling exported snapshots safely

Snapshots are observability artifacts, not sanitized reports. Treat them as
sensitive by default and do not publish them without review. In particular:

- redact or remove request paths, command lines, working directories, audit
  targets/details, session attributes, and tool inputs/outputs;
- review identifiers and destination hosts when they could expose tenant,
  project, repository, or account names;
- store only the fields needed by the downstream consumer and apply its normal
  retention and access controls.

The sample in [`docs/sample-snapshot.json`](sample-snapshot.json) is an
example payload, not an additional compatibility contract. It predates the additive
audit provenance fields, so consumers should treat missing audit `view_source` and
`confidence` values as `unknown` and `null`, respectively.
