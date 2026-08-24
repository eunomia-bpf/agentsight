// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use serde_json::Value;

pub(crate) fn i64_field(value: &Value, key: &str) -> i64 {
    value
        .get(key)
        .and_then(|value| value.as_i64().or_else(|| value.as_u64().map(|v| v as i64)))
        .unwrap_or_default()
}

pub(crate) fn parse_value(text: &str) -> Value {
    serde_json::from_str(text).unwrap_or_else(|_| Value::String(text.to_string()))
}

pub(crate) fn parse_optional_value(text: Option<&str>) -> Value {
    text.map(parse_value).unwrap_or(Value::Null)
}
