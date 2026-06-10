// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Google Gemini (generativelanguage / Cloud Code) wire protocol.

use super::{ProviderAdapter, UsageKeys};

pub(crate) static ADAPTER: ProviderAdapter = ProviderAdapter {
    label_for_host: |host| {
        (host.contains("generativelanguage") || host.contains("googleapis"))
            .then_some("gcp.gen_ai")
    },
    is_llm_path: |path| path.contains(":generateContent") || path.contains(":streamGenerateContent"),
    usage: UsageKeys {
        input: &["promptTokenCount"],
        // Gemini reports visible output and thinking tokens separately.
        output: &[],
        output_summed: &["candidatesTokenCount", "thoughtsTokenCount"],
        cache_creation: &[],
        cache_read: &["cachedContentTokenCount"],
        total: &["totalTokenCount"],
    },
    sse_usage_pointers: &["/usageMetadata"],
    sse_model_pointers: &["/modelVersion"],
};
