INSERT OR REPLACE INTO agent_sessions (
  id, agent_type, agent_name, pid, comm, start_timestamp_ms, end_timestamp_ms,
  status, model, input_tokens, output_tokens, total_tokens, adapter_id, confidence,
  attributes_json
)
SELECT
  'gemini-cli-pid-' || c.pid,
  'gemini-cli',
  'Gemini CLI',
  c.pid,
  c.comm,
  MIN(c.start_timestamp_ms),
  MAX(COALESCE(c.end_timestamp_ms, c.start_timestamp_ms)),
  'observed',
  MAX(c.model),
  COALESCE(SUM(t.input_tokens), 0),
  COALESCE(SUM(t.output_tokens), 0),
  COALESCE(SUM(t.total_tokens), 0),
  'gemini-cli',
  CASE
    WHEN c.path LIKE '%:generateContent%' OR c.path LIKE '%:streamGenerateContent%' THEN 0.90
    WHEN c.host LIKE '%googleapis%' THEN 0.75
    ELSE 0.50
  END,
  json_object('projection', 'gcp-gen-ai')
FROM llm_calls c
LEFT JOIN token_usage t ON t.llm_call_id = c.id
WHERE c.host LIKE '%cloudcode-pa.googleapis.com%'
   OR LOWER(COALESCE(c.request_body_json, '')) LIKE '%this is the gemini cli%'
   OR LOWER(COALESCE(c.request_body_json, '')) LIKE '%geminicli/%'
   OR LOWER(COALESCE(c.response_body_json, '')) LIKE '%geminicli/%'
GROUP BY c.pid, c.comm;

INSERT OR REPLACE INTO agent_sessions (
  id, agent_type, agent_name, pid, comm, start_timestamp_ms, end_timestamp_ms,
  status, model, input_tokens, output_tokens, total_tokens, adapter_id, confidence,
  attributes_json
)
SELECT
  'gemini-cli-pid-' || c.pid,
  'gemini-cli',
  'Gemini CLI',
  c.pid,
  c.comm,
  MIN(c.timestamp_ms),
  MAX(c.timestamp_ms),
  'observed',
  MAX(c.model),
  0,
  0,
  0,
  'gemini-cli',
  0.65,
  json_object('projection', 'request-only')
FROM canonical_events c
WHERE c.kind = 'llm.request'
  AND (
    c.host LIKE '%cloudcode-pa.googleapis.com%'
    OR LOWER(c.attributes_json) LIKE '%this is the gemini cli%'
    OR LOWER(c.attributes_json) LIKE '%geminicli/%'
  )
  AND NOT EXISTS (
    SELECT 1
    FROM llm_calls existing
    WHERE existing.pid = c.pid
      AND (
        existing.host LIKE '%cloudcode-pa.googleapis.com%'
        OR LOWER(COALESCE(existing.request_body_json, '')) LIKE '%this is the gemini cli%'
        OR LOWER(COALESCE(existing.request_body_json, '')) LIKE '%geminicli/%'
        OR LOWER(COALESCE(existing.response_body_json, '')) LIKE '%geminicli/%'
      )
  )
  AND NOT EXISTS (
    SELECT 1
    FROM token_usage cli_tokens
    WHERE cli_tokens.adapter_id = 'gemini-cli'
      AND cli_tokens.source = 'gemini_cli_stdout'
      AND ABS(cli_tokens.timestamp_ms - c.timestamp_ms) <= 300000
  )
GROUP BY c.pid, c.comm;

INSERT OR REPLACE INTO agent_sessions (
  id, agent_type, agent_name, pid, comm, start_timestamp_ms, end_timestamp_ms,
  status, model, input_tokens, output_tokens, total_tokens, adapter_id, confidence,
  attributes_json
)
SELECT
  'gemini-cli-pid-' || pid,
  'gemini-cli',
  'Gemini CLI',
  pid,
  comm,
  MIN(timestamp_ms),
  MAX(timestamp_ms),
  'observed',
  MAX(model),
  COALESCE(SUM(input_tokens), 0),
  COALESCE(SUM(output_tokens), 0),
  COALESCE(SUM(total_tokens), 0),
  'gemini-cli',
  0.95,
  json_object('projection', 'cli-output')
FROM token_usage
WHERE adapter_id = 'gemini-cli'
  AND source = 'gemini_cli_stdout'
GROUP BY pid, comm;

INSERT OR REPLACE INTO conversations (
  id, session_id, start_timestamp_ms, end_timestamp_ms, model,
  input_tokens, output_tokens, total_tokens, status, attributes_json
)
SELECT
  'gemini-conv-' || c.id,
  'gemini-cli-pid-' || c.pid,
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
WHERE c.host LIKE '%cloudcode-pa.googleapis.com%'
   OR LOWER(COALESCE(c.request_body_json, '')) LIKE '%this is the gemini cli%'
   OR LOWER(COALESCE(c.request_body_json, '')) LIKE '%geminicli/%'
   OR LOWER(COALESCE(c.response_body_json, '')) LIKE '%geminicli/%';
