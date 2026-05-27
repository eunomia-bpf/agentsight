INSERT OR IGNORE INTO token_usage (
  id, llm_call_id, timestamp_ms, pid, comm, provider, model,
  input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens,
  total_tokens, source, adapter_id, confidence
)
SELECT
  'token-' || id,
  id,
  COALESCE(end_timestamp_ms, start_timestamp_ms),
  pid,
  comm,
  provider,
  model,
  COALESCE(CAST(json_extract(response_body_json, '$.usage.input_tokens') AS INTEGER), 0),
  COALESCE(CAST(json_extract(response_body_json, '$.usage.output_tokens') AS INTEGER), 0),
  COALESCE(CAST(json_extract(response_body_json, '$.usage.cache_creation_input_tokens') AS INTEGER), 0),
  COALESCE(CAST(json_extract(response_body_json, '$.usage.cache_read_input_tokens') AS INTEGER), 0),
  COALESCE(CAST(json_extract(response_body_json, '$.usage.input_tokens') AS INTEGER), 0) +
    COALESCE(CAST(json_extract(response_body_json, '$.usage.output_tokens') AS INTEGER), 0) +
    COALESCE(CAST(json_extract(response_body_json, '$.usage.cache_creation_input_tokens') AS INTEGER), 0) +
    COALESCE(CAST(json_extract(response_body_json, '$.usage.cache_read_input_tokens') AS INTEGER), 0),
  'response_usage',
  'anthropic',
  0.95
FROM llm_calls
WHERE provider = 'anthropic'
  AND response_body_json IS NOT NULL
  AND (
    json_extract(response_body_json, '$.usage.input_tokens') IS NOT NULL OR
    json_extract(response_body_json, '$.usage.output_tokens') IS NOT NULL
  );
