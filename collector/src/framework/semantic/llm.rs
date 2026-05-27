// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct TokenUsage {
    pub input_tokens: i64,
    pub output_tokens: i64,
    pub cache_creation_tokens: i64,
    pub cache_read_tokens: i64,
    pub total_override: Option<i64>,
}

impl TokenUsage {
    pub fn total_tokens(&self) -> i64 {
        self.total_override.unwrap_or(
            self.input_tokens
                + self.output_tokens
                + self.cache_creation_tokens
                + self.cache_read_tokens,
        )
    }

    pub fn is_empty(&self) -> bool {
        self.total_tokens() == 0
    }
}

pub fn provider_from_host(host: &str) -> String {
    let h = host.to_ascii_lowercase();
    if h.contains("openai.azure.com") {
        "azure.ai.openai".to_string()
    } else if h.contains("openai") {
        "openai".to_string()
    } else if h.contains("anthropic") {
        "anthropic".to_string()
    } else if h.contains("generativelanguage") || h.contains("googleapis") {
        "gcp.gen_ai".to_string()
    } else if h.contains("bedrock") {
        "aws.bedrock".to_string()
    } else {
        host.to_string()
    }
}

pub fn is_llm_path(path: &str) -> bool {
    path.contains("/chat/completions")
        || path.contains("/v1/messages")
        || path.contains("/v1/responses")
        || path.ends_with("/v1/completions")
        || path.contains(":generateContent")
        || path.contains(":streamGenerateContent")
}

pub fn body_json(data: &Value) -> Option<Value> {
    let body = data.get("body").and_then(|v| v.as_str())?;
    serde_json::from_str(body).ok()
}

pub fn extract_model(body: &Value) -> Option<String> {
    body.get("model")
        .and_then(|v| v.as_str())
        .or_else(|| {
            body.get("response")
                .and_then(|v| v.get("model"))
                .and_then(|v| v.as_str())
        })
        .map(String::from)
}

pub fn extract_model_from_path(path: &str) -> Option<String> {
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

fn usage_int(usage: &Value, names: &[&str]) -> i64 {
    names
        .iter()
        .find_map(|name| usage.get(*name).and_then(|v| v.as_i64()))
        .unwrap_or(0)
}

fn usage_sum(usage: &Value, names: &[&str]) -> i64 {
    names
        .iter()
        .filter_map(|name| usage.get(*name).and_then(|v| v.as_i64()))
        .sum()
}

fn usage_output_tokens(usage: &Value) -> i64 {
    let standard = usage_int(usage, &["output_tokens", "completion_tokens"]);
    let gemini = usage_sum(usage, &["candidatesTokenCount", "thoughtsTokenCount"]);
    standard.max(gemini)
}

fn merge_usage(target: &mut TokenUsage, usage: &Value) {
    target.input_tokens = target.input_tokens.max(usage_int(
        usage,
        &["input_tokens", "prompt_tokens", "promptTokenCount"],
    ));
    target.output_tokens = target.output_tokens.max(usage_output_tokens(usage));
    target.cache_creation_tokens = target.cache_creation_tokens.max(usage_int(
        usage,
        &["cache_creation_input_tokens", "cache_creation_tokens"],
    ));
    target.cache_read_tokens = target.cache_read_tokens.max(usage_int(
        usage,
        &[
            "cache_read_input_tokens",
            "cache_read_tokens",
            "cachedContentTokenCount",
        ],
    ));
    let total = usage_int(usage, &["totalTokenCount"]);
    if total > 0 {
        target.total_override = Some(target.total_override.unwrap_or(0).max(total));
    }
}

pub fn extract_token_usage(body: &Value) -> TokenUsage {
    let usage = match body.get("usage").or_else(|| body.get("usageMetadata")) {
        Some(usage) => usage,
        None => return TokenUsage::default(),
    };
    let total_override = usage_int(usage, &["totalTokenCount"]);
    TokenUsage {
        input_tokens: usage_int(
            usage,
            &["input_tokens", "prompt_tokens", "promptTokenCount"],
        ),
        output_tokens: usage_output_tokens(usage),
        cache_creation_tokens: usage_int(
            usage,
            &["cache_creation_input_tokens", "cache_creation_tokens"],
        ),
        cache_read_tokens: usage_int(
            usage,
            &[
                "cache_read_input_tokens",
                "cache_read_tokens",
                "cachedContentTokenCount",
            ],
        ),
        total_override: (total_override > 0).then_some(total_override),
    }
}

pub fn extract_token_usage_from_sse(data: &Value) -> TokenUsage {
    let mut usage = TokenUsage::default();
    let Some(events) = data.get("sse_events").and_then(|v| v.as_array()) else {
        return usage;
    };

    for event in events {
        let Some(parsed) = event.get("parsed_data") else {
            continue;
        };
        if let Some(message_usage) = parsed.get("message").and_then(|m| m.get("usage")) {
            merge_usage(&mut usage, message_usage);
        }
        if let Some(delta_usage) = parsed.get("usage") {
            merge_usage(&mut usage, delta_usage);
        }
        if let Some(gemini_usage) = parsed.get("usageMetadata") {
            merge_usage(&mut usage, gemini_usage);
        }
    }

    usage
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
}
