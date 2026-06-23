# OpenTelemetry GenAI Export

AgentSight can export the LLM calls it captures as **OpenTelemetry GenAI
semantic-convention** (`gen_ai.*`) spans, sent to any OpenTelemetry Collector
over **OTLP/HTTP**. Because AgentSight reconstructs the traffic from the kernel
(eBPF) side, you get standards-compliant GenAI telemetry for **any agent** —
including closed-source CLIs — with **zero in-process instrumentation**.

Spec: <https://opentelemetry.io/docs/specs/semconv/gen-ai/>

## Quick start

Point AgentSight at a running collector with `--otel`:

```bash
sudo ./agentsight debug trace --otel --otel-endpoint http://localhost:4318
```

Each LLM request/response pair becomes a `chat {model}` CLIENT span. By default
only metadata is exported; pass `--otel-capture-content` to also include the
prompt/completion text (off by default for privacy).

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--otel` | off | Enable GenAI span export. |
| `--otel-endpoint <URL>` | `$OTEL_EXPORTER_OTLP_ENDPOINT` or `http://localhost:4318` | OTLP/HTTP base endpoint. `/v1/traces` is appended. |
| `--otel-capture-content` | off | Include `gen_ai.input.messages` / `gen_ai.output.messages`. |

Standard OTel env vars are honored: `OTEL_EXPORTER_OTLP_ENDPOINT`,
`OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` (used as-is if set), and `OTEL_SERVICE_NAME`
(default `agentsight`).

## Run a collector

A minimal collector that prints received spans:

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: 0.0.0.0:4318
exporters:
  debug:
    verbosity: detailed
service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [debug]
```

```bash
docker run -d --name otelcol -p 4318:4318 \
  -v $(pwd)/otel-collector-config.yaml:/etc/otelcol/config.yaml \
  otel/opentelemetry-collector:latest
```

## Integrating with other tools

Because the export is plain OTLP, anything in the OpenTelemetry ecosystem can be
the backend — just change the collector's exporters:

- **Jaeger** — Jaeger accepts OTLP natively (ports 4317/4318); point AgentSight
  at Jaeger, or fan out from the collector with an `otlp` exporter.
- **Grafana Tempo** — add an `otlp` exporter targeting Tempo.
- **Vendors** (Datadog, Honeycomb, New Relic, …) — all consume the OTel GenAI
  conventions; add the vendor exporter to the collector pipeline.

Example collector pipeline forwarding to a vendor:

```yaml
exporters:
  otlphttp/vendor:
    endpoint: https://otlp.example-vendor.com
    headers: { "api-key": "${VENDOR_API_KEY}" }
service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [otlphttp/vendor]
```

## Emitted attributes

Per the GenAI agent/model span conventions:

| Attribute | Source |
|-----------|--------|
| `gen_ai.operation.name` | `chat` |
| `gen_ai.provider.name` | derived from the API host (`openai`, `anthropic`, `gcp.gen_ai`, `azure.ai.openai`, …) |
| `gen_ai.conversation.id` | real conversation/thread/session id from the provider request body when available; never synthesized |
| `gen_ai.request.model` | request body `model` |
| `gen_ai.request.max_tokens` / `temperature` / `top_p` | request body |
| `gen_ai.response.model` / `gen_ai.response.id` | response body |
| `gen_ai.usage.input_tokens` / `output_tokens` | response `usage` (OpenAI & Anthropic shapes) |
| `gen_ai.response.finish_reasons` | `choices[].finish_reason` or `stop_reason` |
| `http.response.status_code` | response status (≥400 marks the span ERROR) |
| `server.address` | API host |
| `gen_ai.input.messages` / `gen_ai.output.messages` | **opt-in** via `--otel-capture-content` |

The span's start/end times come from the captured request and response
timestamps, so latency is measured at the wire.

## How it works

```
agent → SSL_write/SSL_read (captured by eBPF sslsniff)
      → HTTPParser reconstructs request + response
      → OtelExporter pairs them by (pid, tid), maps to gen_ai.* attributes
      → POST OTLP/HTTP JSON to the collector's /v1/traces
```

Provider detection is host-based and falls back to the host name for
OpenAI-compatible endpoints (self-hosted vLLM, llama.cpp, …), so those still
produce useful spans. Streamed (SSE) responses whose body can't be reparsed as
JSON still emit a span with the request attributes and HTTP status.

## Notes & limitations

- OTLP/**HTTP** only (the standard collector receiver). For a remote collector
  behind TLS, run a local collector and let it forward upstream.
- Tool/workflow spans (`execute_tool`, `invoke_agent`, `invoke_workflow`,
  `plan`) are not emitted yet; native transcript tools may be only aggregated
  requests, and AgentSight-specific provenance stays in AgentSight rows.
- The GenAI conventions are still experimental; attribute names track the
  current spec.
