# Cost Estimation Reference

## Token-to-Cost Conversion

Approximate costs per 1M tokens (June 2026 pricing, subject to change):

### Anthropic Claude

| Model | Input | Output | Cache Read | Cache Write |
|-------|-------|--------|------------|-------------|
| claude-opus-4 | $15.00 | $75.00 | $1.50 | $18.75 |
| claude-sonnet-4 | $3.00 | $15.00 | $0.30 | $3.75 |
| claude-haiku-3.5 | $0.80 | $4.00 | $0.08 | $1.00 |

### OpenAI

| Model | Input | Output | Cached Input |
|-------|-------|--------|--------------|
| gpt-4o | $2.50 | $10.00 | $1.25 |
| gpt-4o-mini | $0.15 | $0.60 | $0.075 |
| o1 | $15.00 | $60.00 | - |
| o1-mini | $3.00 | $12.00 | - |

### Google

| Model | Input | Output |
|-------|-------|--------|
| gemini-2.0-flash | $0.10 | $0.40 |
| gemini-2.5-pro | $1.25 | $5.00 |

## Cost Calculation

```python
def estimate_cost(model: str, input_tokens: int, output_tokens: int, 
                  cache_read_tokens: int = 0) -> float:
    """Estimate cost in USD for a single LLM call."""
    rates = get_model_rates(model)  # Returns dict with input/output/cache rates per 1M
    
    billable_input = input_tokens - cache_read_tokens
    
    cost = (
        (billable_input / 1_000_000) * rates['input'] +
        (output_tokens / 1_000_000) * rates['output'] +
        (cache_read_tokens / 1_000_000) * rates.get('cache_read', rates['input'] * 0.1)
    )
    return cost
```

## Session Cost Summary Query

```sql
SELECT 
  model,
  COUNT(*) as calls,
  SUM(input_tokens) as total_input,
  SUM(output_tokens) as total_output,
  SUM(cache_read_tokens) as total_cache_read,
  -- Approximate cost calculation (adjust rates per model)
  (SUM(input_tokens - cache_read_tokens) / 1000000.0 * 3.0 +
   SUM(output_tokens) / 1000000.0 * 15.0 +
   SUM(cache_read_tokens) / 1000000.0 * 0.3) as estimated_cost_usd
FROM llm_calls
WHERE session_id = :session_id
GROUP BY model;
```

## Cost Hotspot Detection

### Top 10 Most Expensive Calls

```sql
SELECT 
  id,
  model,
  input_tokens,
  output_tokens,
  (input_tokens / 1000000.0 * 3.0 + output_tokens / 1000000.0 * 15.0) as cost_usd
FROM llm_calls
ORDER BY cost_usd DESC
LIMIT 10;
```

### Cost Per Session

```sql
SELECT 
  s.id,
  s.command,
  COUNT(l.id) as calls,
  SUM(l.input_tokens + l.output_tokens) as total_tokens,
  SUM(l.input_tokens / 1000000.0 * 3.0 + l.output_tokens / 1000000.0 * 15.0) as cost_usd
FROM sessions s
JOIN llm_calls l ON l.session_id = s.id
GROUP BY s.id
ORDER BY cost_usd DESC;
```

## Cost Efficiency Metrics

### Tokens Per Successful Tool Call

Lower is better -- indicates efficient planning.

```sql
SELECT 
  SUM(input_tokens + output_tokens) * 1.0 / 
  (SELECT COUNT(*) FROM tool_calls WHERE status = 'success') as tokens_per_success
FROM llm_calls;
```

### Cache Efficiency

Higher is better -- indicates good prompt reuse.

```sql
SELECT 
  SUM(cache_read_tokens) * 100.0 / SUM(input_tokens) as cache_hit_percent
FROM llm_calls
WHERE input_tokens > 0;
```

### Output Ratio

Healthy range: 5-20% for typical coding tasks.

```sql
SELECT 
  SUM(output_tokens) * 100.0 / SUM(input_tokens) as output_ratio_percent
FROM llm_calls;
```

## Cost Anomaly Thresholds

| Metric | Warning | Alert |
|--------|---------|-------|
| Single call cost | > $0.50 | > $2.00 |
| Session cost | > $5.00 | > $20.00 |
| Cache hit rate | < 30% | < 10% |
| Cost per tool success | > $0.10 | > $0.50 |
| Output ratio | > 50% | > 80% |
