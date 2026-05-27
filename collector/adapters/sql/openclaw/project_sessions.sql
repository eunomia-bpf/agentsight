INSERT OR REPLACE INTO agent_sessions (
  id, agent_type, agent_name, pid, comm, start_timestamp_ms, end_timestamp_ms,
  status, model, input_tokens, output_tokens, total_tokens, adapter_id, confidence,
  attributes_json
)
SELECT
  'openclaw-pid-' || c.pid,
  'openclaw',
  'OpenClaw',
  c.pid,
  c.comm,
  MIN(c.start_timestamp_ms),
  MAX(COALESCE(c.end_timestamp_ms, c.start_timestamp_ms)),
  'observed',
  MAX(c.model),
  COALESCE(SUM(t.input_tokens), 0),
  COALESCE(SUM(t.output_tokens), 0),
  COALESCE(SUM(t.total_tokens), 0),
  'openclaw',
  0.90,
  json_object('projection', 'node-gateway')
FROM llm_calls c
LEFT JOIN token_usage t ON t.llm_call_id = c.id
WHERE instr(COALESCE(c.request_body_json, ''), 'OpenClaw gateway') > 0
   OR instr(COALESCE(c.request_body_json, ''), 'openclaw.mjs') > 0
   OR instr(COALESCE(c.response_body_json, ''), 'OpenClaw gateway') > 0
   OR instr(COALESCE(c.response_body_json, ''), 'openclaw.mjs') > 0
GROUP BY c.pid, c.comm;
