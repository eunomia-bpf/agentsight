INSERT OR REPLACE INTO tool_calls (
  id, session_id, conversation_id, timestamp_ms, tool_name, tool_call_id,
  status, input_json, output_json, related_pid, related_event_id, adapter_id,
  confidence
)
SELECT
  'claude-tool-' || c.id || '-' || COALESCE(json_extract(e.value, '$.parsed_data.content_block.id'), e.key),
  'claude-code-pid-' || c.pid,
  'claude-conv-' || c.id,
  COALESCE(c.end_timestamp_ms, c.start_timestamp_ms),
  json_extract(e.value, '$.parsed_data.content_block.name'),
  json_extract(e.value, '$.parsed_data.content_block.id'),
  'observed',
  COALESCE(json_extract(e.value, '$.parsed_data.content_block.input'), '{}'),
  NULL,
  c.pid,
  c.response_event_id,
  'claude-code',
  0.85
FROM llm_calls c,
     json_each(c.response_body_json, '$.sse_events') AS e
WHERE c.response_body_json IS NOT NULL
  AND json_extract(e.value, '$.parsed_data.content_block.type') = 'tool_use';

INSERT OR REPLACE INTO tool_calls (
  id, session_id, conversation_id, timestamp_ms, tool_name, tool_call_id,
  status, input_json, output_json, related_pid, related_event_id, adapter_id,
  confidence
)
WITH cli_messages AS (
  SELECT
    c.id AS event_id,
    c.timestamp_ms,
    c.pid,
    msg.value AS message_json
  FROM canonical_events c,
       json_each(c.attributes_json, '$.parsed_json') AS msg
  WHERE c.source = 'cli_output'
    AND json_extract(c.attributes_json, '$.program') = 'claude'
    AND json_type(c.attributes_json, '$.parsed_json') = 'array'

  UNION ALL

  SELECT
    c.id AS event_id,
    c.timestamp_ms,
    c.pid,
    json_extract(c.attributes_json, '$.parsed_json') AS message_json
  FROM canonical_events c
  WHERE c.source = 'cli_output'
    AND json_extract(c.attributes_json, '$.program') = 'claude'
    AND json_type(c.attributes_json, '$.parsed_json') = 'object'
)
SELECT
  'claude-tool-cli-' || event_id || '-' ||
    COALESCE(json_extract(block.value, '$.id'), block.key),
  'claude-code-pid-' || pid,
  'claude-conv-cli-' || event_id,
  timestamp_ms,
  json_extract(block.value, '$.name'),
  json_extract(block.value, '$.id'),
  'observed',
  '{"redacted":true}',
  NULL,
  pid,
  event_id,
  'claude-code',
  0.80
FROM cli_messages,
     json_each(message_json, '$.message.content') AS block
WHERE json_extract(message_json, '$.type') = 'assistant'
  AND json_extract(block.value, '$.type') = 'tool_use';
