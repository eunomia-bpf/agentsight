// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Anthropic Messages API wire protocol.

use super::{ProviderAdapter, UsageKeys};

pub(crate) static ADAPTER: ProviderAdapter = ProviderAdapter {
    label_for_host: |host| host.contains("anthropic").then_some("anthropic"),
    is_llm_path: |path| path.contains("/v1/messages"),
    usage: UsageKeys {
        input: &["input_tokens"],
        output: &["output_tokens"],
        output_summed: &[],
        cache_creation: &["cache_creation_input_tokens", "cache_creation_tokens"],
        cache_read: &["cache_read_input_tokens", "cache_read_tokens"],
        total: &[],
    },
    // message_start carries usage under message.usage; deltas carry it at
    // the event's top level.
    sse_usage_pointers: &["/message/usage", "/usage"],
    sse_model_pointers: &["/message/model"],
};
