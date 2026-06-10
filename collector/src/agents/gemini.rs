// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Gemini CLI (Node.js). Node statically links OpenSSL; `record -- gemini`
//! resolves the Node binary automatically. No native session logs —
//! attribution is self-reported: the CLI prints cumulative per-model token
//! stats on stdout, decoded below with the live pid already attached.

use super::{AgentAdapter, Attribution, Discover};
use crate::event::Event;
use crate::json::i64_field as json_i64;
use crate::semantic::{Observations, ObservedUsage, TokenUsage};
use crate::text::sanitize_ascii_identifier as sanitize_id;
use serde_json::Value;

pub(crate) static ADAPTER: AgentAdapter = AgentAdapter {
    name: "gemini",
    exec_names: &["gemini", "gemini-cli"],
    exec_name_prefixes: &[],
    package_path_markers: &["@google/gemini-cli", "/gemini-cli/"],
    discover: Some(Discover {
        id: "gemini-cli",
        display_name: "Gemini CLI",
        command: "gemini",
        recommended_capture: "agentsight record --db record.db -- gemini --prompt 'hello' --json",
    }),
    native_sessions: None,
    attribution: Attribution::SelfReported,
    decode_observations: Some(decode_stdout_stats),
};

fn decode_stdout_stats(event: &Event, event_id: &str, _host: Option<&str>, out: &mut Observations) {
    if !matches!(event.source.as_str(), "stdio" | "stdiocap") {
        return;
    }
    let Some(payload) = event.data.get("data").and_then(Value::as_str) else {
        return;
    };
    let Ok(obj) = serde_json::from_str::<Value>(payload) else {
        return;
    };
    let Some(models) = obj.pointer("/stats/models").and_then(Value::as_object) else {
        return;
    };
    for (model, stats) in models {
        let tokens = stats.get("tokens").unwrap_or(stats);
        let input = json_i64(tokens, "prompt").max(json_i64(tokens, "input"));
        let output =
            json_i64(tokens, "candidates") + json_i64(tokens, "thoughts") + json_i64(tokens, "tool");
        let cache = json_i64(tokens, "cached");
        let total = json_i64(tokens, "total").max(input + output + cache);
        if total <= 0 {
            continue;
        }
        out.token_usage.push(ObservedUsage {
            llm_call_id: format!("gemini-stdout-{}-{}", event_id, sanitize_id(model)),
            provider: "gcp.gen_ai",
            model: model.clone(),
            usage: TokenUsage {
                input_tokens: input,
                output_tokens: output,
                cache_read_tokens: cache,
                total_override: Some(total),
                ..Default::default()
            },
            source: "gemini_cli_stdout_stats",
            confidence: 0.85,
        });
    }
}
