// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::{Analyzer, AnalyzerError};
use crate::runners::EventStream;
use async_trait::async_trait;
use futures::stream::StreamExt;
use serde_json::Value;
use std::collections::BTreeMap;

/// Redaction strategy applied to detected secrets and PII in captured payloads.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum RedactionMode {
    /// Keep short non-sensitive prefixes/suffixes so operators can still debug.
    #[default]
    Preview,
    /// Replace every matched sensitive span with `[REDACTED:<rule>]`.
    Full,
    /// Leave captured content untouched.
    Disabled,
}

/// High-confidence secret and PII categories detected by [`ContentRedactor`].
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub enum RedactionRule {
    PrivateKey,
    AwsAccessKey,
    ProviderApiKey,
    Jwt,
    CredentialUri,
    KeyValueSecret,
    PaymentCard,
    NationalId,
    PhoneNumber,
}

impl RedactionRule {
    /// Stable lowercase identifier used in full redaction markers and stats.
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::PrivateKey => "private_key",
            Self::AwsAccessKey => "aws_access_key",
            Self::ProviderApiKey => "provider_api_key",
            Self::Jwt => "jwt",
            Self::CredentialUri => "credential_uri",
            Self::KeyValueSecret => "key_value_secret",
            Self::PaymentCard => "payment_card",
            Self::NationalId => "national_id",
            Self::PhoneNumber => "phone_number",
        }
    }

    const fn priority(self) -> u8 {
        match self {
            Self::PrivateKey => 9,
            Self::CredentialUri => 8,
            Self::AwsAccessKey => 7,
            Self::ProviderApiKey => 6,
            Self::Jwt => 5,
            Self::KeyValueSecret => 4,
            Self::PaymentCard => 3,
            Self::NationalId => 2,
            Self::PhoneNumber => 1,
        }
    }
}

/// Counts of redactions performed on a text or JSON payload.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct RedactionStats {
    total_redactions: usize,
    counts: BTreeMap<&'static str, usize>,
}

impl RedactionStats {
    /// Total number of redacted matches.
    pub fn total(&self) -> usize {
        self.total_redactions
    }

    /// Number of matches for a specific [`RedactionRule`].
    pub fn count(&self, rule: RedactionRule) -> usize {
        self.counts.get(rule.as_str()).copied().unwrap_or(0)
    }

    fn record(&mut self, rule: RedactionRule) {
        self.total_redactions += 1;
        *self.counts.entry(rule.as_str()).or_insert(0) += 1;
    }

    /// Merge another [`RedactionStats`] into `self`.
    pub fn merge(&mut self, other: &Self) {
        self.total_redactions += other.total_redactions;
        for (&rule, &count) in &other.counts {
            *self.counts.entry(rule).or_insert(0) += count;
        }
    }
}

/// Stream analyzer that redacts high-confidence secrets and PII from event payloads
/// before events are materialized, persisted to SQLite, exported over OTLP, or printed.
#[derive(Debug, Clone, Default)]
pub struct ContentRedactor {
    mode: RedactionMode,
}

impl ContentRedactor {
    /// Create a redactor using the default [`RedactionMode::Preview`] mode.
    pub fn new() -> Self {
        Self::default()
    }

    /// Create a redactor with an explicit [`RedactionMode`].
    pub fn with_mode(mode: RedactionMode) -> Self {
        Self { mode }
    }

    /// Configured redaction mode.
    pub fn mode(&self) -> RedactionMode {
        self.mode
    }
}

#[async_trait]
impl Analyzer for ContentRedactor {
    async fn process(&mut self, stream: EventStream) -> Result<EventStream, AnalyzerError> {
        let mode = self.mode;
        if mode == RedactionMode::Disabled {
            return Ok(stream);
        }

        let processed = stream.map(move |mut event| {
            let _ = redact_json_value(&mut event.data, mode);
            event
        });
        Ok(Box::pin(processed))
    }
}

/// Structured trace/HTTP metadata keys whose values should not be rewritten so
/// correlation, routing, and model attribution stay intact.
fn is_structural_metadata_key(key: &str) -> bool {
    matches!(
        key,
        "http_exchange_id"
            | "connection_id"
            | "request_id"
            | "response_id"
            | "session_id"
            | "conversation_id"
            | "trace_id"
            | "span_id"
            | "parent_span_id"
            | "process_instance_id"
            | "provider_guid"
            | "transport_handle"
            | "correlation_method"
            | "correlation_status"
            | "tls_library"
            | "message_type"
            | "event"
            | "phase"
            | "provider"
            | "model"
            | "finish_reason"
            | "stop_reason"
            | "content_type"
            | "content_encoding"
            | "transfer_encoding"
            | "method"
            | "version"
            | "protocol"
    )
}

/// Recursively redact string leaves inside a JSON [`Value`], skipping structural
/// correlation/protocol fields.
pub fn redact_json_value(value: &mut Value, mode: RedactionMode) -> RedactionStats {
    let mut stats = RedactionStats::default();
    if mode == RedactionMode::Disabled {
        return stats;
    }
    redact_json_inner(value, mode, &mut stats);
    stats
}

fn redact_json_inner(value: &mut Value, mode: RedactionMode, stats: &mut RedactionStats) {
    match value {
        Value::String(text) => {
            let (redacted, local) = redact_text(text, mode);
            if local.total() > 0 {
                *text = redacted;
                stats.merge(&local);
            }
        }
        Value::Array(items) => {
            for item in items {
                redact_json_inner(item, mode, stats);
            }
        }
        Value::Object(map) => {
            for (key, child) in map.iter_mut() {
                if is_structural_metadata_key(key) {
                    continue;
                }
                redact_json_inner(child, mode, stats);
            }
        }
        Value::Null | Value::Bool(_) | Value::Number(_) => {}
    }
}

#[derive(Debug, Clone)]
struct CandidateMatch {
    start: usize,
    end: usize,
    rule: RedactionRule,
    replacement: String,
}

/// Redact high-confidence secrets and PII in a UTF-8 string.
pub fn redact_text(input: &str, mode: RedactionMode) -> (String, RedactionStats) {
    let mut stats = RedactionStats::default();
    if mode == RedactionMode::Disabled || input.is_empty() {
        return (input.to_string(), stats);
    }

    let mut matches = Vec::new();
    collect_private_keys(input, mode, &mut matches);
    collect_credential_uris(input, mode, &mut matches);
    collect_aws_access_keys(input, mode, &mut matches);
    collect_provider_api_keys(input, mode, &mut matches);
    collect_jwts(input, mode, &mut matches);
    collect_key_value_secrets(input, mode, &mut matches);
    collect_payment_cards(input, mode, &mut matches);
    collect_national_ids(input, mode, &mut matches);
    collect_phone_numbers(input, mode, &mut matches);

    if matches.is_empty() {
        return (input.to_string(), stats);
    }

    // Prefer earlier starts; on identical starts, prefer higher rule priority
    // and then longer span so stronger/fuller detections win deterministically.
    matches.sort_by(|a, b| {
        a.start
            .cmp(&b.start)
            .then_with(|| b.rule.priority().cmp(&a.rule.priority()))
            .then_with(|| b.end.cmp(&a.end))
    });

    // Resolve overlaps: if a higher-priority match starts inside an already-selected
    // lower-priority match (e.g. a CredentialUri password inside a larger span),
    // keep the higher-priority one; otherwise keep non-overlapping matches in order.
    let mut selected: Vec<CandidateMatch> = Vec::with_capacity(matches.len());
    for candidate in matches {
        if let Some(last) = selected.last_mut()
            && candidate.start < last.end
        {
            if candidate.rule.priority() > last.rule.priority() {
                *last = candidate;
            }
            continue;
        }
        selected.push(candidate);
    }

    let mut out = String::with_capacity(input.len());
    let mut cursor = 0;
    for m in selected {
        if m.start < cursor
            || m.end > input.len()
            || !input.is_char_boundary(m.start)
            || !input.is_char_boundary(m.end)
        {
            continue;
        }
        out.push_str(&input[cursor..m.start]);
        out.push_str(&m.replacement);
        cursor = m.end;
        stats.record(m.rule);
    }
    out.push_str(&input[cursor..]);
    (out, stats)
}

fn full_marker(rule: RedactionRule) -> String {
    format!("[REDACTED:{}]", rule.as_str())
}

/// 将字节偏移向下对齐到合法的 UTF-8 字符边界，避免切片落在多字节字符内部触发 panic。
fn floor_char_boundary(s: &str, mut idx: usize) -> usize {
    idx = idx.min(s.len());
    while idx > 0 && !s.is_char_boundary(idx) {
        idx -= 1;
    }
    idx
}

fn mask_token_preview(token: &str, keep_prefix: usize, keep_suffix: usize) -> String {
    // 按 Unicode 标量字符数截取，避免含多字节 UTF-8 字符的敏感值预览触发边界 panic。
    let char_count = token.chars().count();
    let (head_len, tail_len) = if char_count <= keep_prefix + keep_suffix {
        if char_count <= 4 {
            return "****".to_string();
        }
        (2, 2)
    } else {
        (keep_prefix, keep_suffix)
    };
    let head: String = token.chars().take(head_len).collect();
    let tail: String = token.chars().skip(char_count - tail_len).collect();
    format!("{head}****{tail}")
}

fn is_ascii_word_byte(b: u8) -> bool {
    b.is_ascii_alphanumeric() || b == b'_'
}

fn prev_byte(bytes: &[u8], idx: usize) -> Option<u8> {
    idx.checked_sub(1).map(|i| bytes[i])
}

fn next_byte(bytes: &[u8], idx: usize) -> Option<u8> {
    bytes.get(idx).copied()
}

fn has_non_word_boundaries(bytes: &[u8], start: usize, end: usize) -> bool {
    !prev_byte(bytes, start).is_some_and(is_ascii_word_byte)
        && !next_byte(bytes, end).is_some_and(is_ascii_word_byte)
}

fn is_token_boundary_free(bytes: &[u8], start: usize, end: usize) -> bool {
    let before_ok = !prev_byte(bytes, start).is_some_and(|b| is_ascii_word_byte(b) || b == b'-');
    let after_ok = !next_byte(bytes, end).is_some_and(|b| is_ascii_word_byte(b) || b == b'-');
    before_ok && after_ok
}

fn collect_private_keys(input: &str, mode: RedactionMode, out: &mut Vec<CandidateMatch>) {
    const BEGIN_PREFIX: &str = "-----BEGIN ";
    const PRIVATE_KEY_SUFFIX: &str = "PRIVATE KEY-----";
    const MAX_PEM_BYTES: usize = 64 * 1024;

    let mut search_from = 0;
    while let Some(rel_begin) = input[search_from..].find(BEGIN_PREFIX) {
        let begin = search_from + rel_begin;
        let header_body_start = begin + BEGIN_PREFIX.len();
        let search_limit = floor_char_boundary(input, header_body_start + 64);
        let Some(rel_hdr_end) = input[header_body_start..search_limit].find(PRIVATE_KEY_SUFFIX)
        else {
            search_from = header_body_start;
            continue;
        };
        let label = &input[header_body_start..header_body_start + rel_hdr_end];
        if !label
            .bytes()
            .all(|b| b.is_ascii_uppercase() || b.is_ascii_digit() || b == b' ' || b == b'-')
        {
            search_from = header_body_start;
            continue;
        }
        let header_end = header_body_start + rel_hdr_end + PRIVATE_KEY_SUFFIX.len();
        let begin_marker = &input[begin..header_end];
        let end_marker = format!("-----END {label}{PRIVATE_KEY_SUFFIX}");
        let body_limit = floor_char_boundary(input, header_end + MAX_PEM_BYTES);
        let Some(rel_end) = input[header_end..body_limit].find(&end_marker) else {
            search_from = header_end;
            continue;
        };
        let end = header_end + rel_end + end_marker.len();
        let replacement = match mode {
            RedactionMode::Preview => format!("{begin_marker}[REDACTED:private_key]{end_marker}"),
            RedactionMode::Full => full_marker(RedactionRule::PrivateKey),
            RedactionMode::Disabled => unreachable!(),
        };
        out.push(CandidateMatch {
            start: begin,
            end,
            rule: RedactionRule::PrivateKey,
            replacement,
        });
        search_from = end;
    }
}

fn collect_credential_uris(input: &str, mode: RedactionMode, out: &mut Vec<CandidateMatch>) {
    const SCHEMES: &[&str] = &[
        "postgresql",
        "postgres",
        "mongodb+srv",
        "mongodb",
        "mariadb",
        "clickhouse",
        "mysql",
        "rediss",
        "redis",
        "amqps",
        "amqp",
        "https",
        "http",
        "sftp",
        "ftp",
        "mssql",
        "nats",
    ];
    let bytes = input.as_bytes();
    let lower = input.to_ascii_lowercase();
    let lower_bytes = lower.as_bytes();
    let mut i = 0;
    while i < bytes.len() {
        let Some(rel_sep) = lower[i..].find("://") else {
            break;
        };
        let sep = i + rel_sep;
        let mut matched_scheme_start = None;
        for scheme in SCHEMES {
            // 使用字节切片比较 scheme，避免 `sep - scheme.len()` 落在前置多字节 UTF-8 字符内部。
            if sep >= scheme.len()
                && &lower_bytes[sep - scheme.len()..sep] == scheme.as_bytes()
            {
                let start = sep - scheme.len();
                let before_ok = !prev_byte(bytes, start)
                    .is_some_and(|b| b.is_ascii_alphanumeric() || matches!(b, b'+' | b'-' | b'.'));
                if before_ok {
                    matched_scheme_start = Some(start);
                    break;
                }
            }
        }
        let authority_start = sep + 3;
        if matched_scheme_start.is_none() || authority_start >= bytes.len() {
            i = authority_start;
            continue;
        }

        let mut authority_end = authority_start;
        let mut last_at = None;
        while authority_end < bytes.len() {
            let b = bytes[authority_end];
            if b.is_ascii_whitespace()
                || matches!(b, b'/' | b'?' | b'#' | b'"' | b'\'' | b'\\' | b'<' | b'>')
            {
                break;
            }
            if b == b'@' {
                last_at = Some(authority_end);
            }
            authority_end += 1;
        }

        if let Some(at_pos) = last_at
            && let Some(rel_colon) = input[authority_start..at_pos].find(':')
        {
            let user_end = authority_start + rel_colon;
            let pw_start = user_end + 1;
            let pw_end = at_pos;
            let host = &input[at_pos + 1..authority_end];
            let password = &input[pw_start..pw_end];
            if user_end > authority_start
                && !host.is_empty()
                && !password.is_empty()
                && !is_placeholder_secret(password)
            {
                let replacement = match mode {
                    RedactionMode::Preview => "****".to_string(),
                    RedactionMode::Full => full_marker(RedactionRule::CredentialUri),
                    RedactionMode::Disabled => unreachable!(),
                };
                out.push(CandidateMatch {
                    start: pw_start,
                    end: pw_end,
                    rule: RedactionRule::CredentialUri,
                    replacement,
                });
            }
        }
        i = authority_end.max(authority_start);
    }
}

fn collect_aws_access_keys(input: &str, mode: RedactionMode, out: &mut Vec<CandidateMatch>) {
    const PREFIXES: &[&[u8; 4]] = &[b"AKIA", b"ASIA", b"ABIA", b"ACCA"];
    let bytes = input.as_bytes();
    let mut i = 0;
    while i + 20 <= bytes.len() {
        if PREFIXES.iter().any(|p| &bytes[i..i + 4] == *p)
            && has_non_word_boundaries(bytes, i, i + 20)
            && bytes[i + 4..i + 20]
                .iter()
                .all(|b| b.is_ascii_uppercase() || b.is_ascii_digit())
        {
            let Some(token) = input.get(i..i + 20) else {
                i += 1;
                continue;
            };
            let replacement = match mode {
                RedactionMode::Preview => mask_token_preview(token, 4, 4),
                RedactionMode::Full => full_marker(RedactionRule::AwsAccessKey),
                RedactionMode::Disabled => unreachable!(),
            };
            out.push(CandidateMatch {
                start: i,
                end: i + 20,
                rule: RedactionRule::AwsAccessKey,
                replacement,
            });
            i += 20;
            continue;
        }
        i += 1;
    }
}

fn collect_provider_api_keys(input: &str, mode: RedactionMode, out: &mut Vec<CandidateMatch>) {
    struct PrefixSpec {
        prefix: &'static str,
        min_len: usize,
        max_len: Option<usize>,
        allow_dash: bool,
        allow_underscore: bool,
        require_mixed_entropy: bool,
        preview_keep: usize,
    }

    const SPECS: &[PrefixSpec] = &[
        PrefixSpec {
            prefix: "sk-proj-",
            min_len: 20,
            max_len: None,
            allow_dash: true,
            allow_underscore: true,
            require_mixed_entropy: false,
            preview_keep: 8,
        },
        PrefixSpec {
            prefix: "sk-svcacct-",
            min_len: 20,
            max_len: None,
            allow_dash: true,
            allow_underscore: true,
            require_mixed_entropy: false,
            preview_keep: 8,
        },
        PrefixSpec {
            prefix: "sk-admin-",
            min_len: 20,
            max_len: None,
            allow_dash: true,
            allow_underscore: true,
            require_mixed_entropy: false,
            preview_keep: 8,
        },
        PrefixSpec {
            prefix: "sk-ant-",
            min_len: 20,
            max_len: None,
            allow_dash: true,
            allow_underscore: true,
            require_mixed_entropy: false,
            preview_keep: 7,
        },
        PrefixSpec {
            prefix: "sk-live-",
            min_len: 20,
            max_len: None,
            allow_dash: true,
            allow_underscore: true,
            require_mixed_entropy: false,
            preview_keep: 8,
        },
        PrefixSpec {
            prefix: "sk-test-",
            min_len: 20,
            max_len: None,
            allow_dash: true,
            allow_underscore: true,
            require_mixed_entropy: false,
            preview_keep: 8,
        },
        PrefixSpec {
            prefix: "github_pat_",
            min_len: 30,
            max_len: None,
            allow_dash: false,
            allow_underscore: true,
            require_mixed_entropy: false,
            preview_keep: 11,
        },
        PrefixSpec {
            prefix: "ghp_",
            min_len: 20,
            max_len: None,
            allow_dash: false,
            allow_underscore: true,
            require_mixed_entropy: false,
            preview_keep: 4,
        },
        PrefixSpec {
            prefix: "gho_",
            min_len: 20,
            max_len: None,
            allow_dash: false,
            allow_underscore: true,
            require_mixed_entropy: false,
            preview_keep: 4,
        },
        PrefixSpec {
            prefix: "ghu_",
            min_len: 20,
            max_len: None,
            allow_dash: false,
            allow_underscore: true,
            require_mixed_entropy: false,
            preview_keep: 4,
        },
        PrefixSpec {
            prefix: "ghs_",
            min_len: 20,
            max_len: None,
            allow_dash: false,
            allow_underscore: true,
            require_mixed_entropy: false,
            preview_keep: 4,
        },
        PrefixSpec {
            prefix: "ghr_",
            min_len: 20,
            max_len: None,
            allow_dash: false,
            allow_underscore: true,
            require_mixed_entropy: false,
            preview_keep: 4,
        },
        PrefixSpec {
            prefix: "AIza",
            min_len: 39,
            max_len: Some(39),
            allow_dash: true,
            allow_underscore: true,
            require_mixed_entropy: false,
            preview_keep: 6,
        },
        PrefixSpec {
            prefix: "xoxb-",
            min_len: 20,
            max_len: None,
            allow_dash: true,
            allow_underscore: false,
            require_mixed_entropy: false,
            preview_keep: 5,
        },
        PrefixSpec {
            prefix: "xoxp-",
            min_len: 20,
            max_len: None,
            allow_dash: true,
            allow_underscore: false,
            require_mixed_entropy: false,
            preview_keep: 5,
        },
        PrefixSpec {
            prefix: "xoxa-",
            min_len: 20,
            max_len: None,
            allow_dash: true,
            allow_underscore: false,
            require_mixed_entropy: false,
            preview_keep: 5,
        },
        PrefixSpec {
            prefix: "xoxr-",
            min_len: 20,
            max_len: None,
            allow_dash: true,
            allow_underscore: false,
            require_mixed_entropy: false,
            preview_keep: 5,
        },
        PrefixSpec {
            prefix: "xoxs-",
            min_len: 20,
            max_len: None,
            allow_dash: true,
            allow_underscore: false,
            require_mixed_entropy: false,
            preview_keep: 5,
        },
        PrefixSpec {
            prefix: "hf_",
            min_len: 23,
            max_len: None,
            allow_dash: false,
            allow_underscore: false,
            require_mixed_entropy: false,
            preview_keep: 5,
        },
        PrefixSpec {
            prefix: "LTAI",
            min_len: 20,
            max_len: Some(26),
            allow_dash: false,
            allow_underscore: false,
            require_mixed_entropy: true,
            preview_keep: 4,
        },
        PrefixSpec {
            prefix: "sk-",
            min_len: 24,
            max_len: None,
            allow_dash: true,
            allow_underscore: true,
            require_mixed_entropy: true,
            preview_keep: 5,
        },
    ];

    let bytes = input.as_bytes();
    let mut i = 0;
    while i < bytes.len() {
        let mut matched = None;
        for spec in SPECS {
            // 按字节前缀匹配，避免按字节步进的 `i` 落在多字节 UTF-8 字符内部时切片 panic。
            if bytes[i..].starts_with(spec.prefix.as_bytes()) {
                let mut end = i + spec.prefix.len();
                while end < bytes.len() {
                    let b = bytes[end];
                    let valid = b.is_ascii_alphanumeric()
                        || (spec.allow_dash && b == b'-')
                        || (spec.allow_underscore && b == b'_');
                    if !valid {
                        break;
                    }
                    end += 1;
                }
                let len = end - i;
                let max_ok = spec.max_len.is_none_or(|m| len <= m);
                if len >= spec.min_len
                    && max_ok
                    && is_token_boundary_free(bytes, i, end)
                    && (!spec.require_mixed_entropy
                        || (bytes[i + spec.prefix.len()..end]
                            .iter()
                            .any(|b| b.is_ascii_digit())
                            && bytes[i + spec.prefix.len()..end]
                                .iter()
                                .any(|b| b.is_ascii_alphabetic())))
                {
                    matched = Some((end, spec.preview_keep));
                    break;
                }
            }
        }

        if let Some((end, preview_keep)) = matched {
            let Some(token) = input.get(i..end) else {
                i = end;
                continue;
            };
            let replacement = match mode {
                RedactionMode::Preview => mask_token_preview(token, preview_keep, 4),
                RedactionMode::Full => full_marker(RedactionRule::ProviderApiKey),
                RedactionMode::Disabled => unreachable!(),
            };
            out.push(CandidateMatch {
                start: i,
                end,
                rule: RedactionRule::ProviderApiKey,
                replacement,
            });
            i = end;
            continue;
        }
        i += 1;
    }
}

fn is_base64url_byte(b: u8) -> bool {
    b.is_ascii_alphanumeric() || b == b'_' || b == b'-'
}

fn collect_jwts(input: &str, mode: RedactionMode, out: &mut Vec<CandidateMatch>) {
    let bytes = input.as_bytes();
    let mut i = 0;
    while i + 30 <= bytes.len() {
        if bytes[i..].starts_with(b"eyJ")
            && !prev_byte(bytes, i).is_some_and(|b| is_base64url_byte(b) || b == b'.')
        {
            let mut p = i + 3;
            while p < bytes.len() && is_base64url_byte(bytes[p]) {
                p += 1;
            }
            if p - i >= 11 && p < bytes.len() && bytes[p] == b'.' && bytes[p + 1..].starts_with(b"eyJ")
            {
                let payload_start = p + 1;
                let mut q = payload_start + 3;
                while q < bytes.len() && is_base64url_byte(bytes[q]) {
                    q += 1;
                }
                if q - payload_start >= 11 && q < bytes.len() && bytes[q] == b'.' {
                    let sig_start = q + 1;
                    let mut r = sig_start;
                    while r < bytes.len() && is_base64url_byte(bytes[r]) {
                        r += 1;
                    }
                    if r - sig_start >= 16
                        && !next_byte(bytes, r).is_some_and(|b| is_base64url_byte(b) || b == b'.')
                    {
                        let Some(token) = input.get(i..r) else {
                            i = r;
                            continue;
                        };
                        let replacement = match mode {
                            RedactionMode::Preview => mask_token_preview(token, 10, 4),
                            RedactionMode::Full => full_marker(RedactionRule::Jwt),
                            RedactionMode::Disabled => unreachable!(),
                        };
                        out.push(CandidateMatch {
                            start: i,
                            end: r,
                            rule: RedactionRule::Jwt,
                            replacement,
                        });
                        i = r;
                        continue;
                    }
                }
            }
        }
        i += 1;
    }
}

fn is_placeholder_secret(value: &str) -> bool {
    if value.is_empty()
        || value.contains("****")
        || value.contains("[REDACTED")
        || value.contains("...")
        || value.starts_with('$')
        || value.starts_with('<')
        || value.starts_with('{')
        || value.starts_with('[')
        || value.starts_with('*')
    {
        return true;
    }
    let lower = value.to_ascii_lowercase();
    matches!(
        lower.as_str(),
        "null"
            | "none"
            | "true"
            | "false"
            | "undefined"
            | "redacted"
            | "changeme"
            | "change_me"
            | "placeholder"
            | "example"
            | "sample"
            | "dummy"
            | "your_api_key"
            | "your-api-key"
            | "your_secret"
            | "your-secret"
    ) || lower.starts_with("your_")
        || lower.starts_with("your-")
        || lower.starts_with("<your")
        || lower.starts_with("example_")
        || value.bytes().all(|b| b == b'*' || b == b'.' || b == b'x' || b == b'X')
}

fn collect_key_value_secrets(input: &str, mode: RedactionMode, out: &mut Vec<CandidateMatch>) {
    collect_auth_scheme_secrets(input, mode, out);
    collect_named_key_secrets(input, mode, out);
}

fn collect_auth_scheme_secrets(input: &str, mode: RedactionMode, out: &mut Vec<CandidateMatch>) {
    const SCHEMES: &[&str] = &["bearer", "basic"];
    let bytes = input.as_bytes();
    let lower = input.to_ascii_lowercase();
    let lower_bytes = lower.as_bytes();
    let mut i = 0;
    while i < bytes.len() {
        let mut matched_len = None;
        for scheme in SCHEMES {
            // 按字节匹配认证方案前缀，避免 `i` 处于非字符边界时触发 panic。
            if lower_bytes[i..].starts_with(scheme.as_bytes()) {
                let before_ok = !prev_byte(bytes, i).is_some_and(is_ascii_word_byte);
                let after = i + scheme.len();
                if before_ok
                    && after < bytes.len()
                    && (bytes[after] == b' ' || bytes[after] == b'\t')
                {
                    matched_len = Some(scheme.len());
                    break;
                }
            }
        }
        let Some(scheme_len) = matched_len else {
            i += 1;
            continue;
        };
        let mut val_start = i + scheme_len;
        while val_start < bytes.len() && (bytes[val_start] == b' ' || bytes[val_start] == b'\t') {
            val_start += 1;
        }
        let mut val_end = val_start;
        while val_end < bytes.len() {
            let b = bytes[val_end];
            if b.is_ascii_whitespace()
                || matches!(
                    b,
                    b'"' | b'\'' | b'\\' | b',' | b';' | b'<' | b'>' | b'}' | b']' | b'(' | b')'
                )
            {
                break;
            }
            val_end += 1;
        }
        let Some(value) = input.get(val_start..val_end) else {
            i = val_end.max(i + scheme_len);
            continue;
        };
        if value.len() >= 16 && !is_placeholder_secret(value) {
            let replacement = match mode {
                RedactionMode::Preview => mask_token_preview(value, 4, 4),
                RedactionMode::Full => full_marker(RedactionRule::KeyValueSecret),
                RedactionMode::Disabled => unreachable!(),
            };
            out.push(CandidateMatch {
                start: val_start,
                end: val_end,
                rule: RedactionRule::KeyValueSecret,
                replacement,
            });
            i = val_end;
            continue;
        }
        i += scheme_len;
    }
}

fn collect_named_key_secrets(input: &str, mode: RedactionMode, out: &mut Vec<CandidateMatch>) {
    // Ordered longest-first so compound keys win over short suffixes.
    const KEYS: &[(&str, usize)] = &[
        ("aws_secret_access_key", 8),
        ("database_password", 8),
        ("anthropic_api_key", 12),
        ("openrouter_api_key", 12),
        ("secret_access_key", 8),
        ("openai_api_key", 12),
        ("gemini_api_key", 12),
        ("google_api_key", 12),
        ("session_token", 12),
        ("refresh_token", 12),
        ("client_secret", 12),
        ("access_token", 12),
        ("db_password", 8),
        ("private_key", 12),
        ("api_secret", 12),
        ("secret_key", 12),
        ("auth_token", 12),
        ("password", 8),
        ("passwd", 8),
        ("secret", 12),
    ];

    let bytes = input.as_bytes();
    let lower = input.to_ascii_lowercase();
    let lower_bytes = lower.as_bytes();
    let mut i = 0;
    while i < bytes.len() {
        let mut matched_key: Option<(usize, usize)> = None;
        for &(key, min_val_len) in KEYS {
            // 按字节匹配键名，避免 `i` 处于多字节 UTF-8 字符内部时触发切片 panic。
            if lower_bytes[i..].starts_with(key.as_bytes())
                && !prev_byte(bytes, i).is_some_and(is_ascii_word_byte)
                && !next_byte(bytes, i + key.len()).is_some_and(is_ascii_word_byte)
            {
                matched_key = Some((key.len(), min_val_len));
                break;
            }
        }
        let Some((key_len, min_val_len)) = matched_key else {
            i += 1;
            continue;
        };

        let mut p = i + key_len;
        // Skip optional closing quote around the key (including JSON-escaped `\"`).
        if p < bytes.len() && bytes[p] == b'\\' && bytes.get(p + 1) == Some(&b'"') {
            p += 2;
        } else if p < bytes.len() && (bytes[p] == b'"' || bytes[p] == b'\'') {
            p += 1;
        }
        while p < bytes.len() && (bytes[p] == b' ' || bytes[p] == b'\t') {
            p += 1;
        }
        if p >= bytes.len() || (bytes[p] != b'=' && bytes[p] != b':') {
            i += key_len;
            continue;
        }
        p += 1; // consume '=' or ':'
        while p < bytes.len() && (bytes[p] == b' ' || bytes[p] == b'\t') {
            p += 1;
        }

        let mut quote: Option<u8> = None;
        if p < bytes.len() && bytes[p] == b'\\' && bytes.get(p + 1) == Some(&b'"') {
            quote = Some(b'"');
            p += 2;
        } else if p < bytes.len() && (bytes[p] == b'"' || bytes[p] == b'\'') {
            quote = Some(bytes[p]);
            p += 1;
        }

        let val_start = p;
        while p < bytes.len() {
            let b = bytes[p];
            if quote.is_some() {
                if Some(b) == quote || b == b'\\' || b == b'\n' || b == b'\r' {
                    break;
                }
            } else if b.is_ascii_whitespace()
                || matches!(
                    b,
                    b',' | b';' | b'&' | b'"' | b'\'' | b'\\' | b'<' | b'>' | b'}' | b']'
                )
            {
                break;
            }
            p += 1;
        }

        let val_end = p;
        let Some(value) = input.get(val_start..val_end) else {
            i = val_end.max(i + key_len);
            continue;
        };
        if value.len() >= min_val_len
            && !value.contains("://")
            && !is_placeholder_secret(value)
        {
            let replacement = match mode {
                RedactionMode::Preview => {
                    if value.len() >= 12 {
                        mask_token_preview(value, 3, 3)
                    } else {
                        mask_token_preview(value, 2, 2)
                    }
                }
                RedactionMode::Full => full_marker(RedactionRule::KeyValueSecret),
                RedactionMode::Disabled => unreachable!(),
            };
            out.push(CandidateMatch {
                start: val_start,
                end: val_end,
                rule: RedactionRule::KeyValueSecret,
                replacement,
            });
            i = val_end;
            continue;
        }
        i += key_len;
    }
}

fn luhn_valid(digits: &[u8]) -> bool {
    if digits.len() < 13 || digits.len() > 19 {
        return false;
    }
    let mut sum: u32 = 0;
    let mut double = false;
    for &d in digits.iter().rev() {
        let mut v = (d - b'0') as u32;
        if double {
            v *= 2;
            if v > 9 {
                v -= 9;
            }
        }
        sum += v;
        double = !double;
    }
    sum.is_multiple_of(10)
}

fn matches_card_iin(digits: &[u8]) -> bool {
    let len = digits.len();
    if digits[0] == b'4' && matches!(len, 13 | 16 | 19) {
        return true; // Visa
    }
    if len >= 2 {
        let p2 = (digits[0] - b'0') as u16 * 10 + (digits[1] - b'0') as u16;
        if (51..=55).contains(&p2) && len == 16 {
            return true; // Mastercard
        }
        if matches!(p2, 34 | 37) && len == 15 {
            return true; // Amex
        }
        if p2 == 62 && (16..=19).contains(&len) {
            return true; // UnionPay
        }
        if p2 == 65 && matches!(len, 16 | 19) {
            return true; // Discover
        }
    }
    if len >= 3 {
        let p3 = (digits[0] - b'0') as u16 * 100
            + (digits[1] - b'0') as u16 * 10
            + (digits[2] - b'0') as u16;
        if (644..=649).contains(&p3) && matches!(len, 16 | 19) {
            return true; // Discover
        }
    }
    if len >= 4 {
        let p4 = (digits[0] - b'0') as u16 * 1000
            + (digits[1] - b'0') as u16 * 100
            + (digits[2] - b'0') as u16 * 10
            + (digits[3] - b'0') as u16;
        if (2221..=2720).contains(&p4) && len == 16 {
            return true; // Mastercard 2-series
        }
        if p4 == 6011 && matches!(len, 16 | 19) {
            return true; // Discover
        }
        if (3528..=3589).contains(&p4) && (16..=19).contains(&len) {
            return true; // JCB
        }
    }
    false
}

fn is_numeric_token_boundary(b: u8) -> bool {
    b.is_ascii_alphanumeric() || matches!(b, b'.' | b'_' | b'#')
}

fn collect_payment_cards(input: &str, mode: RedactionMode, out: &mut Vec<CandidateMatch>) {
    let bytes = input.as_bytes();
    let mut i = 0;
    while i < bytes.len() {
        if !bytes[i].is_ascii_digit()
            || prev_byte(bytes, i).is_some_and(|b| is_numeric_token_boundary(b) || b == b'-')
        {
            i += 1;
            continue;
        }

        let mut digits: Vec<u8> = Vec::with_capacity(20);
        let mut sep: Option<u8> = None;
        let mut p = i;
        while p < bytes.len() && digits.len() <= 20 {
            let b = bytes[p];
            if b.is_ascii_digit() {
                digits.push(b);
                p += 1;
            } else if (b == b' ' || b == b'-')
                && p + 1 < bytes.len()
                && bytes[p + 1].is_ascii_digit()
                && sep.is_none_or(|s| s == b)
            {
                sep = Some(b);
                p += 1;
            } else {
                break;
            }
        }

        if (13..=19).contains(&digits.len())
            && !next_byte(bytes, p).is_some_and(|b| is_numeric_token_boundary(b) || b == b'-')
            && matches_card_iin(&digits)
            && luhn_valid(&digits)
        {
            let replacement = match mode {
                RedactionMode::Preview => {
                    let head = std::str::from_utf8(&digits[..4]).unwrap_or("");
                    let tail = std::str::from_utf8(&digits[digits.len() - 4..]).unwrap_or("");
                    format!("{head}****{tail}")
                }
                RedactionMode::Full => full_marker(RedactionRule::PaymentCard),
                RedactionMode::Disabled => unreachable!(),
            };
            out.push(CandidateMatch {
                start: i,
                end: p,
                rule: RedactionRule::PaymentCard,
                replacement,
            });
            i = p;
            continue;
        }
        i += 1;
    }
}

fn is_valid_cn_province(prefix: &[u8]) -> bool {
    matches!(
        prefix,
        b"11"
            | b"12"
            | b"13"
            | b"14"
            | b"15"
            | b"21"
            | b"22"
            | b"23"
            | b"31"
            | b"32"
            | b"33"
            | b"34"
            | b"35"
            | b"36"
            | b"37"
            | b"41"
            | b"42"
            | b"43"
            | b"44"
            | b"45"
            | b"46"
            | b"50"
            | b"51"
            | b"52"
            | b"53"
            | b"54"
            | b"61"
            | b"62"
            | b"63"
            | b"64"
            | b"65"
            | b"71"
            | b"81"
            | b"82"
    )
}

fn is_valid_yyyymmdd(bytes: &[u8]) -> bool {
    if bytes.len() != 8 || !bytes.iter().all(|b| b.is_ascii_digit()) {
        return false;
    }
    let parse2 = |a: u8, b: u8| -> u32 { ((a - b'0') as u32) * 10 + ((b - b'0') as u32) };
    let year = parse2(bytes[0], bytes[1]) * 100 + parse2(bytes[2], bytes[3]);
    let month = parse2(bytes[4], bytes[5]);
    let day = parse2(bytes[6], bytes[7]);
    if !(1900..=2099).contains(&year) || !(1..=12).contains(&month) || day == 0 {
        return false;
    }
    let leap = year.is_multiple_of(400) || (year.is_multiple_of(4) && !year.is_multiple_of(100));
    let max_day = match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 if leap => 29,
        2 => 28,
        _ => return false,
    };
    day <= max_day
}

fn cn_resident_id_checksum_valid(bytes: &[u8]) -> bool {
    const WEIGHTS: [u32; 17] = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2];
    const CHECK_CODES: &[u8; 11] = b"10X98765432";
    if bytes.len() != 18 || !bytes[..17].iter().all(|b| b.is_ascii_digit()) {
        return false;
    }
    let sum: u32 = bytes[..17]
        .iter()
        .zip(WEIGHTS.iter())
        .map(|(&d, &w)| ((d - b'0') as u32) * w)
        .sum();
    let expected = CHECK_CODES[(sum % 11) as usize];
    bytes[17].to_ascii_uppercase() == expected
}

fn collect_national_ids(input: &str, mode: RedactionMode, out: &mut Vec<CandidateMatch>) {
    let bytes = input.as_bytes();
    let mut i = 0;
    while i < bytes.len() {
        // 1. China 18-digit Resident ID (GB 11643-1999)
        if i + 18 <= bytes.len()
            && !prev_byte(bytes, i).is_some_and(is_numeric_token_boundary)
            && !next_byte(bytes, i + 18).is_some_and(is_numeric_token_boundary)
            && is_valid_cn_province(&bytes[i..i + 2])
            && is_valid_yyyymmdd(&bytes[i + 6..i + 14])
            && cn_resident_id_checksum_valid(&bytes[i..i + 18])
        {
            let id = &input[i..i + 18];
            let replacement = match mode {
                RedactionMode::Preview => mask_token_preview(id, 3, 4),
                RedactionMode::Full => full_marker(RedactionRule::NationalId),
                RedactionMode::Disabled => unreachable!(),
            };
            out.push(CandidateMatch {
                start: i,
                end: i + 18,
                rule: RedactionRule::NationalId,
                replacement,
            });
            i += 18;
            continue;
        }

        // 2. US SSN (`AAA-GG-SSSS`)
        if i + 11 <= bytes.len()
            && bytes[i + 3] == b'-'
            && bytes[i + 6] == b'-'
            && !prev_byte(bytes, i).is_some_and(|b| is_numeric_token_boundary(b) || b == b'-')
            && !next_byte(bytes, i + 11).is_some_and(|b| is_numeric_token_boundary(b) || b == b'-')
            && bytes[i..i + 3].iter().all(|b| b.is_ascii_digit())
            && bytes[i + 4..i + 6].iter().all(|b| b.is_ascii_digit())
            && bytes[i + 7..i + 11].iter().all(|b| b.is_ascii_digit())
        {
            let area = &input[i..i + 3];
            let group = &input[i + 4..i + 6];
            let serial = &input[i + 7..i + 11];
            let area_num: u16 = area.parse().unwrap_or(0);
            if area_num != 0 && area_num != 666 && area_num < 900 && group != "00" && serial != "0000"
            {
                let replacement = match mode {
                    RedactionMode::Preview => format!("{area}-**-{serial}"),
                    RedactionMode::Full => full_marker(RedactionRule::NationalId),
                    RedactionMode::Disabled => unreachable!(),
                };
                out.push(CandidateMatch {
                    start: i,
                    end: i + 11,
                    rule: RedactionRule::NationalId,
                    replacement,
                });
                i += 11;
                continue;
            }
        }

        i += 1;
    }
}

fn collect_phone_numbers(input: &str, mode: RedactionMode, out: &mut Vec<CandidateMatch>) {
    let bytes = input.as_bytes();
    let mut i = 0;
    while i < bytes.len() {
        // 1. Optional +86 Chinese mainland mobile (`(+86[ -]?)?1[3-9]\d{9}`)
        if bytes[i..].starts_with(b"+86")
            && !prev_byte(bytes, i).is_some_and(|b| is_numeric_token_boundary(b) || b == b'+')
        {
            let mut p = i + 3;
            let sep = if p < bytes.len() && (bytes[p] == b' ' || bytes[p] == b'-') {
                let s = bytes[p] as char;
                p += 1;
                Some(s)
            } else {
                None
            };
            if p + 11 <= bytes.len()
                && bytes[p] == b'1'
                && (b'3'..=b'9').contains(&bytes[p + 1])
                && bytes[p + 2..p + 11].iter().all(|b| b.is_ascii_digit())
                && !next_byte(bytes, p + 11).is_some_and(is_numeric_token_boundary)
            {
                let head = &input[p..p + 3];
                let tail = &input[p + 7..p + 11];
                let replacement = match mode {
                    RedactionMode::Preview => match sep {
                        Some(s) => format!("+86{s}{head}****{tail}"),
                        None => format!("+86{head}****{tail}"),
                    },
                    RedactionMode::Full => full_marker(RedactionRule::PhoneNumber),
                    RedactionMode::Disabled => unreachable!(),
                };
                out.push(CandidateMatch {
                    start: i,
                    end: p + 11,
                    rule: RedactionRule::PhoneNumber,
                    replacement,
                });
                i = p + 11;
                continue;
            }
        }

        // Bare 11-digit Chinese mobile (`1[3-9]\d{9}`)
        if i + 11 <= bytes.len()
            && bytes[i] == b'1'
            && (b'3'..=b'9').contains(&bytes[i + 1])
            && bytes[i + 2..i + 11].iter().all(|b| b.is_ascii_digit())
            && !prev_byte(bytes, i)
                .is_some_and(|b| is_numeric_token_boundary(b) || b == b'+' || b == b'-')
            && !next_byte(bytes, i + 11)
                .is_some_and(|b| is_numeric_token_boundary(b) || b == b'-')
        {
            let head = &input[i..i + 3];
            let tail = &input[i + 7..i + 11];
            let replacement = match mode {
                RedactionMode::Preview => format!("{head}****{tail}"),
                RedactionMode::Full => full_marker(RedactionRule::PhoneNumber),
                RedactionMode::Disabled => unreachable!(),
            };
            out.push(CandidateMatch {
                start: i,
                end: i + 11,
                rule: RedactionRule::PhoneNumber,
                replacement,
            });
            i += 11;
            continue;
        }

        // 2. Formatted international E.164 (`+<cc><sep><groups>`, 10-15 digits, >=1 separator)
        if bytes[i] == b'+'
            && i + 10 <= bytes.len()
            && !prev_byte(bytes, i)
                .is_some_and(|b| is_numeric_token_boundary(b) || b == b'+' || b == b'-')
            && (b'1'..=b'9').contains(&bytes[i + 1])
        {
            let mut cc_end = i + 1;
            while cc_end < bytes.len() && cc_end - (i + 1) < 3 && bytes[cc_end].is_ascii_digit() {
                cc_end += 1;
            }
            if cc_end < bytes.len() && (bytes[cc_end] == b' ' || bytes[cc_end] == b'-') {
                let cc = &input[i + 1..cc_end];
                let mut digits: Vec<u8> = cc.as_bytes().to_vec();
                let mut p = cc_end + 1;
                let mut sep_count = 1usize;
                let valid = p < bytes.len() && bytes[p].is_ascii_digit();
                while valid && p < bytes.len() && digits.len() <= 15 {
                    let b = bytes[p];
                    if b.is_ascii_digit() {
                        digits.push(b);
                        p += 1;
                    } else if (b == b' ' || b == b'-')
                        && p + 1 < bytes.len()
                        && bytes[p + 1].is_ascii_digit()
                    {
                        sep_count += 1;
                        p += 1;
                    } else {
                        break;
                    }
                }
                if valid
                    && sep_count >= 1
                    && (10..=15).contains(&digits.len())
                    && !next_byte(bytes, p)
                        .is_some_and(|b| is_numeric_token_boundary(b) || b == b'-')
                {
                    let tail = std::str::from_utf8(&digits[digits.len() - 4..]).unwrap_or("");
                    let replacement = match mode {
                        RedactionMode::Preview => format!("+{cc} ****{tail}"),
                        RedactionMode::Full => full_marker(RedactionRule::PhoneNumber),
                        RedactionMode::Disabled => unreachable!(),
                    };
                    out.push(CandidateMatch {
                        start: i,
                        end: p,
                        rule: RedactionRule::PhoneNumber,
                        replacement,
                    });
                    i = p;
                    continue;
                }
            }
        }

        i += 1;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::event::Event;
    use serde_json::json;

    #[test]
    fn redacts_all_nine_high_confidence_categories_in_preview_and_full_modes() {
        let pem_header = format!("-----BEGIN {}-----", "RSA PRIVATE KEY");
        let pem_footer = format!("-----END {}-----", "RSA PRIVATE KEY");
        let pem = format!("{pem_header}\nMIIEowIBAAKCAQEAtestpayload1234567890\n{pem_footer}");
        let aws = ["AKIA", "IOSFODNN7EXAMPLE"].concat();
        let openai = ["sk-proj-", "abc1234567890XYZ9876543210"].concat();
        let github = ["ghp_", "1234567890abcdefghijklmnopqr"].concat();
        let jwt = [
            "eyJhbGciOiJIUzI1NiJ9",
            "eyJzdWIiOiIxMjM0NTY3ODkwIn0",
            "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        ]
        .join(".");
        let uri_pw = ["SuperSecret", "Pw99"].concat();
        let uri = format!("postgres://alice:{uri_pw}@db.internal:5432/prod");
        let kv_secret = ["my_super_secret", "_value_1234"].concat();
        let kv = format!("client_secret={kv_secret}");
        let card = "4111 1111 1111 1111";
        let cn_id = "11010519491231002X";
        let ssn = "123-45-6789";
        let phone = "13812345678";
        let intl_phone = "+1-415-555-0199";

        let sample = format!(
            "pem={pem} aws={aws} openai={openai} gh={github} jwt={jwt} uri={uri} {kv} card={card} cn={cn_id} ssn={ssn} tel={phone} intl={intl_phone}"
        );

        let (preview, preview_stats) = redact_text(&sample, RedactionMode::Preview);
        assert!(preview.contains(&format!("{pem_header}[REDACTED:private_key]{pem_footer}")));
        assert!(!preview.contains("MIIEowIBAAKCAQEAtestpayload"));
        assert!(preview.contains("AKIA****MPLE"));
        assert!(preview.contains("sk-proj-****3210"));
        assert!(preview.contains("ghp_****opqr"));
        assert!(preview.contains("eyJhbGciOi****sw5c"));
        assert!(preview.contains("postgres://alice:****@db.internal:5432/prod"));
        assert!(preview.contains("client_secret=my_****234"));
        assert!(preview.contains("4111****1111"));
        assert!(preview.contains("110****002X"));
        assert!(preview.contains("123-**-6789"));
        assert!(preview.contains("138****5678"));
        assert!(preview.contains("+1 ****0199"));
        assert_eq!(preview_stats.count(RedactionRule::PrivateKey), 1);
        assert_eq!(preview_stats.count(RedactionRule::AwsAccessKey), 1);
        assert_eq!(preview_stats.count(RedactionRule::ProviderApiKey), 2);
        assert_eq!(preview_stats.count(RedactionRule::Jwt), 1);
        assert_eq!(preview_stats.count(RedactionRule::CredentialUri), 1);
        assert_eq!(preview_stats.count(RedactionRule::KeyValueSecret), 1);
        assert_eq!(preview_stats.count(RedactionRule::PaymentCard), 1);
        assert_eq!(preview_stats.count(RedactionRule::NationalId), 2);
        assert_eq!(preview_stats.count(RedactionRule::PhoneNumber), 2);
        assert_eq!(preview_stats.total(), 12);

        let (full, full_stats) = redact_text(&sample, RedactionMode::Full);
        assert_eq!(full_stats, preview_stats);
        assert!(full.contains("[REDACTED:private_key]"));
        assert!(full.contains("[REDACTED:aws_access_key]"));
        assert!(full.contains("[REDACTED:provider_api_key]"));
        assert!(full.contains("[REDACTED:jwt]"));
        assert!(full.contains("postgres://alice:[REDACTED:credential_uri]@db.internal:5432/prod"));
        assert!(full.contains("client_secret=[REDACTED:key_value_secret]"));
        assert!(full.contains("[REDACTED:payment_card]"));
        assert!(full.contains("[REDACTED:national_id]"));
        assert!(full.contains("[REDACTED:phone_number]"));
        assert!(!full.contains(&aws));
        assert!(!full.contains(&uri_pw));

        let (disabled, disabled_stats) = redact_text(&sample, RedactionMode::Disabled);
        assert_eq!(disabled, sample);
        assert_eq!(disabled_stats.total(), 0);
    }

    #[test]
    fn avoids_false_positives_on_orders_luhn_failures_ips_versions_and_placeholders() {
        let benign = concat!(
            "order=4111111111111112 ", // fails Luhn
            "bad_bin=9111111111111111 ", // unsupported BIN prefix
            "long_order=1381234567890 ", // 13 digits, not phone or valid card
            "bad_cn_id=110105194912310021 ", // fails MOD 11-2 checksum
            "bad_cn_date=110105199902300028 ", // invalid Feb 30
            "bad_ssn=900-12-3456 ", // area >= 900 invalid SSN
            "ip=192.168.1.100 ",
            "ver=1.38.12345678 ",
            "kebab=sk-some-harmless-kebab-case-identifier ", // no digits
            "env_ref=password=${DB_PASSWORD} ",
            "placeholder=api_secret=changeme ",
            "already_masked=AKIA****MPLE ",
            "short_test=Bearer agentsight-test",
        );

        let (out, stats) = redact_text(benign, RedactionMode::Preview);
        assert_eq!(out, benign);
        assert_eq!(stats.total(), 0);
    }

    #[test]
    fn redacts_json_body_strings_without_breaking_json_parsing_or_structural_ids() {
        let aws = ["AKIA", "IOSFODNN7EXAMPLE"].concat();
        let api_secret = ["my_secret_", "value_1234"].concat();
        let pem_header = format!("-----BEGIN {}-----", "PRIVATE KEY");
        let pem_footer = format!("-----END {}-----", "PRIVATE KEY");
        let pem = format!("{pem_header}\nabc123\n{pem_footer}");
        let raw_body = serde_json::json!({
            "model": "gpt-4o",
            "messages": [{
                "role": "user",
                "content": format!("Deploy with {aws} and api_secret=\"{api_secret}\" and {pem}")
            }]
        })
        .to_string();

        let bearer_token = ["super_secret_", "token_987654"].concat();
        let mut payload = json!({
            "message_type": "request",
            "http_exchange_id": "conn-1-h1-1",
            "connection_id": "conn-1",
            "model": "gpt-4o",
            "body": raw_body,
            "headers": {
                "x-custom": format!("Bearer {bearer_token}")
            }
        });

        let stats = redact_json_value(&mut payload, RedactionMode::Preview);
        assert_eq!(stats.total(), 4);
        assert_eq!(payload["http_exchange_id"], "conn-1-h1-1");
        assert_eq!(payload["connection_id"], "conn-1");
        assert_eq!(payload["headers"]["x-custom"], "Bearer supe****7654");

        let parsed_body: Value = serde_json::from_str(
            payload["body"]
                .as_str()
                .expect("redacted HTTP body remains a string"),
        )
        .expect("redacted HTTP JSON body must remain valid JSON");
        let content = parsed_body["messages"][0]["content"].as_str().unwrap();
        assert!(content.contains("AKIA****MPLE"));
        assert!(content.contains("api_secret=\"my_****234\""));
        assert!(content.contains(&format!("{pem_header}[REDACTED:private_key]{pem_footer}")));
        assert!(!content.contains(&aws));
        assert!(!content.contains(&api_secret));
        assert!(!content.contains("abc123"));
    }

    #[tokio::test]
    async fn analyzer_stream_redacts_events_when_enabled_and_skips_when_disabled() {
        let openai = ["sk-proj-", "abc1234567890XYZ9876543210"].concat();
        let raw_body = serde_json::json!({
            "messages": [{ "content": format!("token={openai}") }]
        })
        .to_string();
        let event = Event::new_with_timestamp(
            1_000,
            "http_parser".to_string(),
            42,
            "claude".to_string(),
            json!({
                "message_type": "request",
                "body": raw_body
            }),
        );

        let mut preview_redactor = ContentRedactor::new();
        let stream: EventStream = Box::pin(futures::stream::iter(vec![event.clone()]));
        let out: Vec<_> = preview_redactor
            .process(stream)
            .await
            .unwrap()
            .collect()
            .await;
        assert_eq!(out.len(), 1);
        let body = out[0].data["body"].as_str().unwrap();
        assert!(body.contains("sk-proj-****3210"));
        assert!(!body.contains(&openai));

        let mut disabled_redactor = ContentRedactor::with_mode(RedactionMode::Disabled);
        let stream: EventStream = Box::pin(futures::stream::iter(vec![event]));
        let out: Vec<_> = disabled_redactor
            .process(stream)
            .await
            .unwrap()
            .collect()
            .await;
        assert!(out[0].data["body"].as_str().unwrap().contains(&openai));
    }

    #[test]
    fn redacts_secrets_surrounded_by_multibyte_utf8_without_panicking() {
        let openai = ["sk-proj-", "abc1234567890XYZ9876543210"].concat();
        let sk_key = ["sk-", "mixed1234567890abcdef9999"].concat();
        let aws = ["AKIA", "IOSFODNN7EXAMPLE"].concat();
        let jwt = [
            "eyJhbGciOiJIUzI1NiJ9",
            "eyJzdWIiOiIxMjM0NTY3ODkwIn0",
            "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        ]
        .join(".");
        let bearer_token = ["utf8_bearer_", "token_987654321"].concat();
        let client_secret = ["utf8_client_", "secret_556677"].concat();
        let utf8_password = ["中文密码", "很长的密码", "1234"].concat();
        let uri_pw = ["密码Secret", "Pw99"].concat();
        let uri = format!("postgres://alice:{uri_pw}@db.local/app");
        let pem_header_probe = format!("-----BEGIN {}’ trailing", "A".repeat(63));

        let sample = format!(
            "ő ≤ ’{openai}’ ≥ 🔐中文 {sk_key} 中文前缀 {aws} ő {jwt} \
             Bearer {bearer_token} client_secret={client_secret} \
             password={utf8_password} 中文://host {uri} {pem_header_probe}"
        );

        let (preview, preview_stats) = redact_text(&sample, RedactionMode::Preview);
        assert!(preview.contains("’sk-proj-****3210’"));
        assert!(preview.contains("sk-mi****9999"));
        assert!(preview.contains("AKIA****MPLE"));
        assert!(preview.contains("eyJhbGciOi****sw5c"));
        assert!(preview.contains("Bearer utf8****4321"));
        assert!(preview.contains("client_secret=utf****677"));
        assert!(preview.contains("password=中文密****234"));
        assert!(preview.contains("postgres://alice:****@db.local/app"));
        assert!(preview.contains("ő ≤ "));
        assert!(preview.contains("中文://host"));
        assert!(preview.contains(&pem_header_probe));
        assert!(!preview.contains(&openai));
        assert!(!preview.contains(&sk_key));
        assert!(!preview.contains(&aws));
        assert!(!preview.contains(&jwt));
        assert!(!preview.contains(&bearer_token));
        assert!(!preview.contains(&client_secret));
        assert!(!preview.contains(&utf8_password));
        assert!(!preview.contains(&uri_pw));
        assert_eq!(preview_stats.count(RedactionRule::ProviderApiKey), 2);
        assert_eq!(preview_stats.count(RedactionRule::AwsAccessKey), 1);
        assert_eq!(preview_stats.count(RedactionRule::Jwt), 1);
        assert_eq!(preview_stats.count(RedactionRule::KeyValueSecret), 3);
        assert_eq!(preview_stats.count(RedactionRule::CredentialUri), 1);
        assert_eq!(preview_stats.total(), 8);

        let (full, full_stats) = redact_text(&sample, RedactionMode::Full);
        assert_eq!(full_stats, preview_stats);
        assert!(full.contains("’[REDACTED:provider_api_key]’"));
        assert!(full.contains("password=[REDACTED:key_value_secret]"));
        assert!(full.contains("postgres://alice:[REDACTED:credential_uri]@db.local/app"));
    }

    #[test]
    fn preserves_plain_multibyte_utf8_transcript_text_without_panicking() {
        let benign = "用户提问：为什么 x ≤ y 且 y ≥ z？It’s working — ő, 🔐, 中文://example, sk-not-a-secret-token";
        let (out, stats) = redact_text(benign, RedactionMode::Preview);
        assert_eq!(out, benign);
        assert_eq!(stats.total(), 0);
    }
}
