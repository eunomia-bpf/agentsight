INSERT OR REPLACE INTO agent_sessions (
  id, agent_type, agent_name, pid, comm, start_timestamp_ms, end_timestamp_ms,
  status, model, input_tokens, output_tokens, total_tokens, adapter_id, confidence,
  attributes_json
)
SELECT
  'claude-code-pid-' || c.pid,
  'claude-code',
  'Claude Code',
  c.pid,
  c.comm,
  MIN(c.start_timestamp_ms),
  MAX(COALESCE(c.end_timestamp_ms, c.start_timestamp_ms)),
  'observed',
  MAX(c.model),
  COALESCE(SUM(t.input_tokens), 0),
  COALESCE(SUM(t.output_tokens), 0),
  COALESCE(SUM(t.total_tokens), 0),
  'claude-code',
  CASE WHEN c.comm LIKE 'claude%' THEN 0.90 ELSE 0.60 END,
  json_object('projection', 'pid-window')
FROM llm_calls c
LEFT JOIN token_usage t ON t.llm_call_id = c.id
WHERE c.provider = 'anthropic'
  AND (c.comm LIKE 'claude%' OR c.request_body_json LIKE '%claude%' OR c.response_body_json LIKE '%claude%')
GROUP BY c.pid, c.comm;

INSERT OR REPLACE INTO agent_sessions (
  id, agent_type, agent_name, pid, comm, start_timestamp_ms, end_timestamp_ms,
  status, model, input_tokens, output_tokens, total_tokens, adapter_id, confidence,
  attributes_json
)
SELECT
  'claude-code-pid-' || pid,
  'claude-code',
  'Claude Code',
  pid,
  comm,
  MIN(timestamp_ms),
  MAX(timestamp_ms),
  'observed',
  MAX(model),
  COALESCE(SUM(input_tokens), 0),
  COALESCE(SUM(output_tokens), 0),
  COALESCE(SUM(total_tokens), 0),
  'claude-code',
  0.80,
  json_object('projection', 'telemetry')
FROM token_usage
WHERE adapter_id = 'claude-code'
  AND source IN (
    'claude_code_stdout_model_usage',
    'claude_telemetry',
    'claude_telemetry_fallback'
  )
GROUP BY pid, comm;

INSERT OR REPLACE INTO conversations (
  id, session_id, start_timestamp_ms, end_timestamp_ms, model,
  input_tokens, output_tokens, total_tokens, status, attributes_json
)
SELECT
  'claude-conv-' || c.id,
  'claude-code-pid-' || c.pid,
  c.start_timestamp_ms,
  c.end_timestamp_ms,
  c.model,
  COALESCE(t.input_tokens, 0),
  COALESCE(t.output_tokens, 0),
  COALESCE(t.total_tokens, 0),
  CASE WHEN c.status_code >= 400 THEN 'error' ELSE 'observed' END,
  json_object('llm_call_id', c.id)
FROM llm_calls c
LEFT JOIN token_usage t ON t.llm_call_id = c.id
WHERE c.provider = 'anthropic'
  AND (c.comm LIKE 'claude%' OR c.request_body_json LIKE '%claude%' OR c.response_body_json LIKE '%claude%');
