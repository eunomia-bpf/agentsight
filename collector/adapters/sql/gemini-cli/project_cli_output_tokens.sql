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
    json_extract(c.attributes_json, '$.parsed_json.stats.models') AS models
  FROM canonical_events c
  WHERE c.source = 'cli_output'
    AND json_extract(c.attributes_json, '$.stream') = 'stdout'
    AND LOWER(c.attributes_json) LIKE '%gemini%'
    AND json_type(c.attributes_json, '$.parsed_json.stats.models') = 'object'
),
model_usage AS (
  SELECT
    cli.id,
    cli.timestamp_ms,
    cli.pid,
    cli.comm,
    model.key AS model,
    COALESCE(CAST(json_extract(model.value, '$.tokens.input') AS INTEGER),
             CAST(json_extract(model.value, '$.tokens.prompt') AS INTEGER), 0) AS input_tokens,
    COALESCE(CAST(json_extract(model.value, '$.tokens.candidates') AS INTEGER), 0) +
      COALESCE(CAST(json_extract(model.value, '$.tokens.thoughts') AS INTEGER), 0) AS output_tokens,
    0 AS cache_creation_tokens,
    COALESCE(CAST(json_extract(model.value, '$.tokens.cached') AS INTEGER), 0) AS cache_read_tokens,
    COALESCE(CAST(json_extract(model.value, '$.tokens.total') AS INTEGER), 0) AS total_tokens
  FROM cli, json_each(cli.models) AS model
)
SELECT
  'gemini-cli-output-token-' || id || '-' ||
    replace(replace(replace(model, '/', '_'), '[', '_'), ']', '_'),
  NULL,
  timestamp_ms,
  pid,
  comm,
  'gcp.gen_ai',
  model,
  input_tokens,
  output_tokens,
  cache_creation_tokens,
  cache_read_tokens,
  CASE
    WHEN total_tokens > 0 THEN total_tokens
    ELSE input_tokens + output_tokens + cache_creation_tokens + cache_read_tokens
  END,
  'gemini_cli_stdout',
  'gemini-cli',
  0.95
FROM model_usage
WHERE (input_tokens > 0 OR output_tokens > 0 OR total_tokens > 0)
  AND NOT EXISTS (
    SELECT 1
    FROM token_usage existing
    WHERE existing.adapter_id = 'generic'
      AND existing.source = 'response_usage'
      AND COALESCE(existing.model, '') = COALESCE(model_usage.model, '')
      AND existing.total_tokens = CASE
        WHEN model_usage.total_tokens > 0 THEN model_usage.total_tokens
        ELSE model_usage.input_tokens + model_usage.output_tokens +
          model_usage.cache_creation_tokens + model_usage.cache_read_tokens
      END
      AND ABS(existing.timestamp_ms - model_usage.timestamp_ms) <= 300000
  );
