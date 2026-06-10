// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! LLM provider adapters. Each wire protocol (Anthropic, OpenAI, Gemini) is
//! described by one module exporting a `ProviderAdapter` descriptor; this
//! module owns the registry and is the single home of provider knowledge
//! (host labels, LLM endpoint paths, token-usage field names).
//!
//! Adding a provider = adding one module + one registry entry.

pub(crate) mod anthropic;
pub(crate) mod gemini;
pub(crate) mod openai;

use crate::semantic::TokenUsage;
use serde_json::Value;

/// Static description of one LLM wire protocol.
pub(crate) struct ProviderAdapter {
    /// Maps a request host to the provider label used in rows/spans
    /// (e.g. `gen_ai.system`). Returns None when the host is not this
    /// provider's.
    pub label_for_host: fn(&str) -> Option<&'static str>,
    /// Whether a URL path is one of this provider's LLM endpoints.
    pub is_llm_path: fn(&str) -> bool,
    /// Token usage field names in response bodies / SSE payloads.
    pub usage: UsageKeys,
    /// JSON pointers (relative to an SSE event's `parsed_data`) that may
    /// hold a usage object.
    pub sse_usage_pointers: &'static [&'static str],
    /// JSON pointers (relative to `parsed_data`) that may hold the model id.
    pub sse_model_pointers: &'static [&'static str],
}

pub(crate) struct UsageKeys {
    pub input: &'static [&'static str],
    pub output: &'static [&'static str],
    /// Output counters that are summed instead of taken individually
    /// (Gemini reports candidates and thoughts separately).
    pub output_summed: &'static [&'static str],
    pub cache_creation: &'static [&'static str],
    pub cache_read: &'static [&'static str],
    pub total: &'static [&'static str],
}

/// Registry order also defines extraction precedence for ambiguous payloads.
static PROVIDERS: &[&ProviderAdapter] =
    &[&anthropic::ADAPTER, &gemini::ADAPTER, &openai::ADAPTER];

/// Map a request host to a provider label; unknown hosts pass through
/// unchanged so non-LLM traffic stays identifiable.
pub(crate) fn provider_from_host(host: &str) -> String {
    let h = host.to_ascii_lowercase();
    for provider in PROVIDERS {
        if let Some(label) = (provider.label_for_host)(&h) {
            return label.to_string();
        }
    }
    if h.contains("bedrock") {
        return "aws.bedrock".to_string();
    }
    host.to_string()
}

pub(crate) fn is_llm_path(path: &str) -> bool {
    PROVIDERS
        .iter()
        .any(|provider| (provider.is_llm_path)(path))
}

/// Parse an event's `body` string field as JSON, once.
pub(crate) fn body_json(data: &Value) -> Option<Value> {
    let body = data.get("body").and_then(|v| v.as_str())?;
    serde_json::from_str(body).ok()
}

pub(crate) fn extract_model(body: &Value) -> Option<String> {
    body.get("model")
        .and_then(|v| v.as_str())
        .or_else(|| {
            body.get("response")
                .and_then(|v| v.get("model"))
                .and_then(|v| v.as_str())
        })
        .map(String::from)
}

/// Model id embedded in the URL path (`/models/<model>:generateContent`).
pub(crate) fn extract_model_from_path(path: &str) -> Option<String> {
    let marker = "/models/";
    let start = path.find(marker)? + marker.len();
    let rest = &path[start..];
    let end = rest
        .find(':')
        .or_else(|| rest.find('/'))
        .unwrap_or(rest.len());
    if end == 0 {
        None
    } else {
        Some(rest[..end].to_string())
    }
}

fn keys_int(usage: &Value, names: &[&str]) -> i64 {
    names
        .iter()
        .find_map(|name| usage.get(*name).and_then(|v| v.as_i64()))
        .unwrap_or(0)
}

fn keys_sum(usage: &Value, names: &[&str]) -> i64 {
    names
        .iter()
        .filter_map(|name| usage.get(*name).and_then(|v| v.as_i64()))
        .sum()
}

/// Merge one usage JSON object into `target`, taking the strongest signal
/// across providers (streamed responses repeat usage with growing counts).
fn merge_usage(target: &mut TokenUsage, usage: &Value) {
    for provider in PROVIDERS {
        let keys = &provider.usage;
        target.input_tokens = target.input_tokens.max(keys_int(usage, keys.input));
        let output = keys_int(usage, keys.output).max(keys_sum(usage, keys.output_summed));
        target.output_tokens = target.output_tokens.max(output);
        target.cache_creation_tokens = target
            .cache_creation_tokens
            .max(keys_int(usage, keys.cache_creation));
        target.cache_read_tokens = target.cache_read_tokens.max(keys_int(usage, keys.cache_read));
        let total = keys_int(usage, keys.total);
        if total > 0 {
            target.total_override = Some(target.total_override.unwrap_or(0).max(total));
        }
    }
}

/// Extract token usage from a plain (non-streamed) response body.
pub(crate) fn extract_token_usage(body: &Value) -> TokenUsage {
    let mut result = TokenUsage::default();
    let Some(usage) = body.get("usage").or_else(|| body.get("usageMetadata")) else {
        return result;
    };
    merge_usage(&mut result, usage);
    result
}

/// Extract token usage from an accumulated SSE stream (`sse_events` array).
pub(crate) fn extract_token_usage_from_sse(data: &Value) -> TokenUsage {
    let mut usage = TokenUsage::default();
    let Some(events) = data.get("sse_events").and_then(|v| v.as_array()) else {
        return usage;
    };

    for event in events {
        let Some(parsed) = event.get("parsed_data") else {
            continue;
        };
        for provider in PROVIDERS {
            for pointer in provider.sse_usage_pointers {
                if let Some(value) = parsed.pointer(pointer) {
                    merge_usage(&mut usage, value);
                }
            }
        }
    }

    usage
}

/// Extract the model id from an accumulated SSE stream.
pub(crate) fn extract_model_from_sse(data: &Value) -> Option<String> {
    let events = data.get("sse_events")?.as_array()?;
    for event in events {
        let Some(parsed) = event.get("parsed_data") else {
            continue;
        };
        for provider in PROVIDERS {
            for pointer in provider.sse_model_pointers {
                if let Some(model) = parsed.pointer(pointer).and_then(|v| v.as_str()) {
                    return Some(model.to_string());
                }
            }
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn extracts_usage_shapes() {
        let openai = json!({"usage":{"prompt_tokens": 3, "completion_tokens": 4}});
        assert_eq!(extract_token_usage(&openai).total_tokens(), 7);

        let anthropic =
            json!({"usage":{"input_tokens": 5, "output_tokens": 6, "cache_read_input_tokens": 2}});
        let usage = extract_token_usage(&anthropic);
        assert_eq!(usage.input_tokens, 5);
        assert_eq!(usage.output_tokens, 6);
        assert_eq!(usage.cache_read_tokens, 2);

        let gemini = json!({"usageMetadata":{"promptTokenCount": 11, "candidatesTokenCount": 4, "totalTokenCount": 15}});
        let usage = extract_token_usage(&gemini);
        assert_eq!(usage.input_tokens, 11);
        assert_eq!(usage.output_tokens, 4);
        assert_eq!(usage.total_tokens(), 15);

        let gemini_sse = json!({"sse_events":[{"parsed_data":{"usageMetadata":{"promptTokenCount":11,"candidatesTokenCount":4,"totalTokenCount":15}}}]});
        let usage = extract_token_usage_from_sse(&gemini_sse);
        assert_eq!(usage.input_tokens, 11);
        assert_eq!(usage.output_tokens, 4);
        assert_eq!(usage.total_tokens(), 15);

        let gemini_thinking = json!({"usageMetadata":{"promptTokenCount": 11, "candidatesTokenCount": 4, "thoughtsTokenCount": 5}});
        let usage = extract_token_usage(&gemini_thinking);
        assert_eq!(usage.output_tokens, 9);
        assert_eq!(usage.total_tokens(), 20);
    }

    #[test]
    fn extracts_gemini_model_from_path() {
        assert_eq!(
            extract_model_from_path("/v1beta/models/gemini-2.5-pro:generateContent").as_deref(),
            Some("gemini-2.5-pro")
        );
    }

    #[test]
    fn labels_known_hosts() {
        assert_eq!(provider_from_host("api.openai.com"), "openai");
        assert_eq!(provider_from_host("api.anthropic.com"), "anthropic");
        assert_eq!(
            provider_from_host("generativelanguage.googleapis.com"),
            "gcp.gen_ai"
        );
        assert_eq!(
            provider_from_host("my-resource.openai.azure.com"),
            "azure.ai.openai"
        );
        assert_eq!(provider_from_host("bedrock.us-east-1.amazonaws.com"), "aws.bedrock");
        assert_eq!(provider_from_host("localhost:8443"), "localhost:8443");
    }

    #[test]
    fn matches_llm_paths_across_providers() {
        assert!(is_llm_path("/v1/messages"));
        assert!(is_llm_path("/v1/chat/completions"));
        assert!(is_llm_path("/v1beta/models/gemini-2.5-pro:streamGenerateContent"));
        assert!(!is_llm_path("/v1/files"));
    }
}
