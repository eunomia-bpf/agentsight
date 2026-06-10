// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! OpenAI Chat Completions / Responses API wire protocol (also used by
//! Azure OpenAI deployments).

use super::{ProviderAdapter, UsageKeys};

pub(crate) static ADAPTER: ProviderAdapter = ProviderAdapter {
    label_for_host: |host| {
        if host.contains("openai.azure.com") {
            Some("azure.ai.openai")
        } else if host.contains("openai") {
            Some("openai")
        } else {
            None
        }
    },
    is_llm_path: |path| {
        path.contains("/chat/completions")
            || path.contains("/v1/responses")
            || path.ends_with("/v1/completions")
    },
    usage: UsageKeys {
        input: &["prompt_tokens"],
        output: &["completion_tokens"],
        output_summed: &[],
        cache_creation: &[],
        cache_read: &[],
        total: &[],
    },
    sse_usage_pointers: &["/usage"],
    sse_model_pointers: &["/model"],
};
