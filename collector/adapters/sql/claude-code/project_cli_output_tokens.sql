INSERT OR REPLACE INTO token_usage (
  id, llm_call_id, timestamp_ms, pid, comm, provider, model,
  input_tokens, output_tokens, cache_creation_tokens, cache_read_tokens,
  total_tokens, source, adapter_id, confidence
)
WITH cli AS (
  SELECT
    c.id,
    c.timestamp_ms,
    c.pid,
    c.comm,
    json_extract(c.attributes_json, '$.parsed_json') AS parsed
  FROM canonical_events c
  WHERE c.source = 'cli_output'
    AND json_extract(c.attributes_json, '$.stream') = 'stdout'
    AND LOWER(c.attributes_json) LIKE '%claude%'
    AND json_extract(c.attributes_json, '$.parsed_json') IS NOT NULL
),
result_events AS (
  SELECT
    cli.id,
    cli.timestamp_ms,
    cli.pid,
    cli.comm,
    event.value AS result_json
  FROM cli, json_each(cli.parsed) AS event
  WHERE json_type(cli.parsed) = 'array'
    AND json_extract(event.value, '$.type') = 'result'
  UNION ALL
  SELECT
    cli.id,
    cli.timestamp_ms,
    cli.pid,
    cli.comm,
    cli.parsed AS result_json
  FROM cli
  WHERE json_type(cli.parsed) = 'object'
    AND json_extract(cli.parsed, '$.modelUsage') IS NOT NULL
),
model_usage AS (
  SELECT
    result_events.id,
    result_events.timestamp_ms,
    result_events.pid,
    result_events.comm,
    model.key AS model,
    COALESCE(CAST(json_extract(model.value, '$.inputTokens') AS INTEGER), 0) AS input_tokens,
    COALESCE(CAST(json_extract(model.value, '$.outputTokens') AS INTEGER), 0) AS output_tokens,
    COALESCE(CAST(json_extract(model.value, '$.cacheCreationInputTokens') AS INTEGER), 0) AS cache_creation_tokens,
    COALESCE(CAST(json_extract(model.value, '$.cacheReadInputTokens') AS INTEGER), 0) AS cache_read_tokens
  FROM result_events, json_each(json_extract(result_events.result_json, '$.modelUsage')) AS model
)
SELECT
  'claude-code-output-token-' || id || '-' ||
    replace(replace(replace(model, '/', '_'), '[', '_'), ']', '_'),
  NULL,
  timestamp_ms,
  pid,
  comm,
  'anthropic',
  model,
  input_tokens,
  output_tokens,
  cache_creation_tokens,
  cache_read_tokens,
  input_tokens + output_tokens + cache_creation_tokens + cache_read_tokens,
  'claude_code_stdout_model_usage',
  'claude-code',
  0.95
FROM model_usage
WHERE (input_tokens > 0 OR output_tokens > 0 OR cache_creation_tokens > 0 OR cache_read_tokens > 0)
  AND NOT EXISTS (
    SELECT 1
    FROM token_usage existing
    WHERE existing.adapter_id = 'generic'
      AND existing.source = 'response_usage'
      AND existing.provider = 'anthropic'
      AND (
        COALESCE(model_usage.model, '') = COALESCE(existing.model, '')
        OR model_usage.model LIKE COALESCE(existing.model, '') || '%'
        OR COALESCE(existing.model, '') LIKE model_usage.model || '%'
      )
      AND existing.input_tokens = model_usage.input_tokens
      AND existing.cache_creation_tokens = model_usage.cache_creation_tokens
      AND existing.cache_read_tokens = model_usage.cache_read_tokens
      AND ABS(existing.output_tokens - model_usage.output_tokens) <= 20
      AND ABS(existing.timestamp_ms - model_usage.timestamp_ms) <= 300000
  );
