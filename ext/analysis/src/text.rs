// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use serde_json::Value;

pub fn sanitize_ascii_identifier(value: &str) -> String {
    value
        .chars()
        .map(|c| if c.is_ascii_alphanumeric() { c } else { '-' })
        .collect()
}

pub fn truncate_text(text: &str, max: usize) -> String {
    if text.chars().count() <= max {
        text.to_string()
    } else {
        text.chars().take(max.saturating_sub(1)).collect()
    }
}

pub fn truncate_with_ellipsis(text: &str, max: usize) -> String {
    if text.chars().count() <= max {
        text.to_string()
    } else {
        format!(
            "{}...",
            text.chars().take(max.saturating_sub(3)).collect::<String>()
        )
    }
}

pub fn clean_prompt_text(text: &str) -> Option<String> {
    let text = text.split_whitespace().collect::<Vec<_>>().join(" ");
    let text = text
        .strip_prefix("<session>")
        .and_then(|text| text.strip_suffix("</session>"))
        .unwrap_or(&text)
        .trim();
    (!text.is_empty()).then(|| text.to_string())
}

pub fn extract_prompt_text(value: &Value) -> Option<String> {
    if let Some(prompt) = value.get("prompt").and_then(Value::as_str) {
        return clean_prompt_text(prompt);
    }
    let mut parts = Vec::new();
    for key in ["messages", "contents", "input"] {
        if let Some(items) = value.get(key).and_then(Value::as_array) {
            for item in items {
                collect_content_text(item.get("content").unwrap_or(item), &mut parts);
            }
        }
    }
    clean_prompt_text(&parts.join(" "))
}

fn collect_content_text(value: &Value, out: &mut Vec<String>) {
    match value {
        Value::String(text) => out.push(text.clone()),
        Value::Array(items) => items
            .iter()
            .for_each(|item| collect_content_text(item, out)),
        Value::Object(obj) => {
            for key in ["text", "content", "parts"] {
                if let Some(value) = obj.get(key) {
                    collect_content_text(value, out);
                }
            }
        }
        _ => {}
    }
}

#[cfg(test)]
mod tests {
    use super::extract_prompt_text;
    use serde_json::json;

    #[test]
    fn extracts_openai_responses_input_text() {
        let request = json!({
            "model": "gpt-agentsight-mock",
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "agentsight mock prompt collect this exact text"}
                    ]
                }
            ]
        });

        assert_eq!(
            extract_prompt_text(&request).as_deref(),
            Some("agentsight mock prompt collect this exact text")
        );
    }
}
