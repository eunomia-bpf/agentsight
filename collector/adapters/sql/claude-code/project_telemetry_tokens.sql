INSERT OR REPLACE INTO token_usage (
  id, llm_call_id, timestamp_ms, pid, comm, provider, model,
  input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens,
  total_tokens, source, adapter_id, confidence
)
WITH telemetry AS (
  SELECT
    c.id,
    c.timestamp_ms,
    c.pid,
    c.comm,
    COALESCE(json_extract(e.value, '$.provider'), 'anthropic') AS provider,
    json_extract(e.value, '$.model') AS model,
    COALESCE(CAST(json_extract(e.value, '$.input_tokens') AS INTEGER), 0) AS input_tokens,
    COALESCE(CAST(json_extract(e.value, '$.output_tokens') AS INTEGER), 0) AS output_tokens,
    COALESCE(CAST(json_extract(e.value, '$.cache_creation_input_tokens') AS INTEGER), 0) AS cache_creation_tokens,
    COALESCE(CAST(json_extract(e.value, '$.cached_input_tokens') AS INTEGER), 0) AS cache_read_tokens,
    e.key AS event_index
  FROM canonical_events c,
       json_each(json_extract(c.attributes_json, '$.body')) AS e
  WHERE c.kind = 'http.request'
    AND c.host LIKE '%datadoghq.com'
    AND json_valid(json_extract(c.attributes_json, '$.body'))
    AND json_extract(e.value, '$.message') = 'tengu_api_success'
)
SELECT
  'claude-telemetry-token-' || t.id || '-' || t.event_index,
  NULL,
  t.timestamp_ms,
  t.pid,
  t.comm,
  t.provider,
  t.model,
  t.input_tokens,
  t.output_tokens,
  t.cache_creation_tokens,
  t.cache_read_tokens,
  t.input_tokens + t.output_tokens + t.cache_creation_tokens + t.cache_read_tokens,
  'claude_telemetry',
  'claude-code',
  0.80
FROM telemetry t
WHERE (t.input_tokens > 0 OR t.output_tokens > 0 OR t.cache_read_tokens > 0)
  AND NOT EXISTS (
    SELECT 1
    FROM token_usage existing
    WHERE (
        existing.adapter_id = 'generic'
        OR (
          existing.adapter_id = 'claude-code'
          AND existing.source = 'claude_code_stdout_model_usage'
        )
      )
      AND existing.pid = t.pid
      AND existing.input_tokens = t.input_tokens
      AND existing.cache_creation_tokens = t.cache_creation_tokens
      AND existing.cache_read_tokens = t.cache_read_tokens
      AND ABS(existing.output_tokens - t.output_tokens) <= 20
      AND ABS(existing.timestamp_ms - t.timestamp_ms) <= 60000
  );

INSERT OR REPLACE INTO token_usage (
  id, llm_call_id, timestamp_ms, pid, comm, provider, model,
  input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens,
  total_tokens, source, adapter_id, confidence
)
WITH telemetry AS (
  SELECT
    c.id,
    c.timestamp_ms,
    c.pid,
    c.comm,
    json_extract(c.attributes_json, '$.body') AS body
  FROM canonical_events c
  WHERE c.kind = 'http.request'
    AND c.host LIKE '%datadoghq.com'
    AND NOT json_valid(json_extract(c.attributes_json, '$.body'))
    AND json_extract(c.attributes_json, '$.body') LIKE '%tengu_api_success%'
  UNION ALL
  SELECT
    c.id,
    c.timestamp_ms,
    c.pid,
    c.comm,
    json_extract(c.attributes_json, '$.data') AS body
  FROM canonical_events c
  WHERE c.source = 'ssl'
    AND json_extract(c.attributes_json, '$.data') LIKE '%tengu_api_success%'
),
parsed AS (
  SELECT
    id,
    timestamp_ms,
    pid,
    comm,
    'anthropic' AS provider,
    'unknown' AS model,
    CASE WHEN instr(body, '"input_tokens":') > 0
      THEN CAST(substr(body, instr(body, '"input_tokens":') + length('"input_tokens":')) AS INTEGER)
      ELSE 0 END AS input_tokens,
    CASE WHEN instr(body, '"output_tokens":') > 0
      THEN CAST(substr(body, instr(body, '"output_tokens":') + length('"output_tokens":')) AS INTEGER)
      ELSE 0 END AS output_tokens,
    0 AS cache_creation_tokens,
    CASE WHEN instr(body, '"cached_input_tokens":') > 0
      THEN CAST(substr(body, instr(body, '"cached_input_tokens":') + length('"cached_input_tokens":')) AS INTEGER)
      ELSE 0 END AS cache_read_tokens
  FROM telemetry
)
SELECT
  'claude-telemetry-token-fallback-' || p.id,
  NULL,
  p.timestamp_ms,
  p.pid,
  p.comm,
  p.provider,
  p.model,
  p.input_tokens,
  p.output_tokens,
  p.cache_creation_tokens,
  p.cache_read_tokens,
  p.input_tokens + p.output_tokens + p.cache_creation_tokens + p.cache_read_tokens,
  'claude_telemetry_fallback',
  'claude-code',
  0.55
FROM parsed p
WHERE (p.input_tokens > 0 OR p.output_tokens > 0 OR p.cache_read_tokens > 0)
  AND NOT EXISTS (
    SELECT 1
    FROM token_usage existing
    WHERE (
        existing.adapter_id = 'generic'
        OR (
          existing.adapter_id = 'claude-code'
          AND existing.source = 'claude_code_stdout_model_usage'
        )
      )
      AND existing.pid = p.pid
      AND existing.input_tokens = p.input_tokens
      AND existing.cache_creation_tokens = p.cache_creation_tokens
      AND existing.cache_read_tokens = p.cache_read_tokens
      AND ABS(existing.output_tokens - p.output_tokens) <= 20
      AND ABS(existing.timestamp_ms - p.timestamp_ms) <= 60000
  );
