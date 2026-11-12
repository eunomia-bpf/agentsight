// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Media evidence derived from explicit HTTP and JSON metadata. This does not
//! inspect binary payloads or infer a media type from a URL or filename.

use crate::model::{AuditEventRow, ViewResult};
use crate::view::{CanonicalEvent, EventKind, MaterializedView};
use serde_json::{Value, json};

const MAX_JSON_NODES: usize = 512;
const MAX_JSON_DEPTH: usize = 16;

#[derive(Debug, Clone, PartialEq, Eq)]
struct MediaEvidence {
    kind: &'static str,
    mime_type: Option<String>,
    source: &'static str,
}

impl MaterializedView {
    pub(super) fn ingest_media_event(&mut self, event: &CanonicalEvent) -> ViewResult<()> {
        if event.source != "http_parser" && event.source != "sse_processor" {
            return Ok(());
        }
        let action = match event.kind {
            EventKind::HttpRequest | EventKind::LlmRequest => "request",
            EventKind::HttpResponse | EventKind::LlmResponse | EventKind::LlmError => "response",
            _ if event.source == "sse_processor" => "response",
            _ => return Ok(()),
        };
        for evidence in extract_media(&event.attributes) {
            self.emit_audit_event(AuditEventRow {
                id: format!("audit-media-{}-{}", event.event_id, evidence.kind),
                timestamp_ms: event.timestamp_ms,
                audit_type: "media".to_string(),
                pid: event.pid,
                comm: event.comm.clone(),
                subject: event.comm.clone(),
                action: Some(action.to_string()),
                target: event.host.clone(),
                status: Some("observed".to_string()),
                summary: Some(format!("{} media observed", evidence.kind)),
                details: json!({
                    "media_kind": evidence.kind,
                    "mime_type": evidence.mime_type,
                    "source": evidence.source,
                }),
                view_source: "view".to_string(),
                confidence: event.confidence,
            })?;
        }
        Ok(())
    }
}

fn extract_media(data: &Value) -> Vec<MediaEvidence> {
    let mut found = Vec::new();
    if let Some(headers) = data.get("headers").and_then(Value::as_object) {
        for (name, value) in headers {
            if name.eq_ignore_ascii_case("content-type") {
                if let Some(mime) = value.as_str() {
                    add_mime(&mut found, mime, "http_content_type");
                }
                break;
            }
        }
    }

    let body = data
        .get("body")
        .or_else(|| data.get("json_content"))
        .and_then(Value::as_str)
        .and_then(|text| serde_json::from_str::<Value>(text).ok());
    if let Some(body) = body.as_ref() {
        extract_json_media(body, &mut found);
    }
    found
}

fn extract_json_media(body: &Value, found: &mut Vec<MediaEvidence>) {
    let mut pending = vec![(body, 0usize)];
    let mut visited = 0;
    while let Some((value, depth)) = pending.pop() {
        visited += 1;
        if visited > MAX_JSON_NODES {
            break;
        }
        match value {
            Value::Object(fields) => {
                for (key, value) in fields {
                    let normalized = key.to_ascii_lowercase();
                    if matches!(
                        normalized.as_str(),
                        "mime_type" | "mimetype" | "mediatype" | "media_type" | "content_type"
                    ) {
                        if let Some(mime) = value.as_str() {
                            add_mime(found, mime, "json_mime_type");
                        }
                    } else if normalized == "type" {
                        if let Some(kind) = value.as_str().and_then(block_kind) {
                            add_evidence(
                                found,
                                MediaEvidence {
                                    kind,
                                    mime_type: None,
                                    source: "json_block_type",
                                },
                            );
                        }
                    }
                    if depth < MAX_JSON_DEPTH {
                        pending.push((value, depth + 1));
                    }
                }
            }
            Value::Array(items) if depth < MAX_JSON_DEPTH => {
                pending.extend(items.iter().map(|item| (item, depth + 1)));
            }
            Value::String(text) => {
                if let Some(mime) = text
                    .strip_prefix("data:")
                    .and_then(|rest| rest.split(',').next())
                {
                    add_mime(found, mime, "data_url");
                }
            }
            _ => {}
        }
    }
}

fn block_kind(value: &str) -> Option<&'static str> {
    match value.to_ascii_lowercase().as_str() {
        "image" | "image_url" | "input_image" | "output_image" => Some("image"),
        "audio" | "audio_url" | "input_audio" | "output_audio" => Some("audio"),
        "document" | "input_document" | "output_document" => Some("document"),
        _ => None,
    }
}

fn add_mime(found: &mut Vec<MediaEvidence>, value: &str, source: &'static str) {
    let mime = value
        .split(';')
        .next()
        .unwrap_or("")
        .trim()
        .to_ascii_lowercase();
    if mime.is_empty() || mime.len() > 127 || !mime.is_ascii() {
        return;
    }
    let kind = if mime.starts_with("image/") {
        "image"
    } else if mime.starts_with("audio/") {
        "audio"
    } else if matches!(
        mime.as_str(),
        "application/pdf"
            | "application/msword"
            | "application/rtf"
            | "application/epub+zip"
            | "application/xml"
            | "text/plain"
            | "text/markdown"
            | "text/csv"
            | "text/html"
            | "text/rtf"
    ) || mime.starts_with("application/vnd.openxmlformats-officedocument.")
        || mime.starts_with("application/vnd.oasis.opendocument.")
    {
        "document"
    } else {
        return;
    };
    add_evidence(
        found,
        MediaEvidence {
            kind,
            mime_type: Some(mime),
            source,
        },
    );
}

fn add_evidence(found: &mut Vec<MediaEvidence>, evidence: MediaEvidence) {
    if let Some(existing) = found.iter_mut().find(|item| item.kind == evidence.kind) {
        if existing.mime_type.is_none() && evidence.mime_type.is_some() {
            *existing = evidence;
        }
    } else {
        found.push(evidence);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::event::Event;

    #[test]
    fn extracts_header_mime_with_parameters_and_case() {
        let found = extract_media(&json!({
            "headers": { "Content-Type": "Image/PNG; charset=binary" },
            "body": "not JSON"
        }));
        assert_eq!(
            found,
            vec![MediaEvidence {
                kind: "image",
                mime_type: Some("image/png".to_string()),
                source: "http_content_type",
            }]
        );
    }

    #[test]
    fn extracts_all_kinds_from_json_without_payloads() {
        let found = extract_media(&json!({
            "headers": { "content-type": "application/json" },
            "body": json!({"content": [
                {"type": "image_url", "image_url": {"url": "data:image/webp;base64,SECRET"}},
                {"type": "input_audio", "mime_type": "audio/wav", "data": "SECRET"},
                {"type": "document", "source": {"media_type": "application/pdf", "data": "SECRET"}}
            ]}).to_string()
        }));
        assert_eq!(found.len(), 3);
        assert_eq!(
            found
                .iter()
                .find(|item| item.kind == "image")
                .unwrap()
                .mime_type
                .as_deref(),
            Some("image/webp")
        );
        assert_eq!(
            found
                .iter()
                .find(|item| item.kind == "audio")
                .unwrap()
                .mime_type
                .as_deref(),
            Some("audio/wav")
        );
        assert_eq!(
            found
                .iter()
                .find(|item| item.kind == "document")
                .unwrap()
                .mime_type
                .as_deref(),
            Some("application/pdf")
        );
    }

    #[test]
    fn leaves_opaque_payloads_unclassified() {
        assert!(
            extract_media(&json!({
                "headers": { "content-type": "application/octet-stream" },
                "body": json!({"url": "https://example.test/photo.png", "type": "file"}).to_string()
            }))
            .is_empty()
        );
    }

    #[test]
    fn materializes_metadata_without_copying_media_payload() {
        let event = Event::new_with_timestamp(
            1_000,
            "http_parser".to_string(),
            42,
            "agent".to_string(),
            json!({
                "tid": 7,
                "message_type": "request",
                "method": "POST",
                "path": "/v1/messages",
                "headers": { "host": "api.example.test", "content-type": "application/json" },
                "body": "{\"content\":[{\"type\":\"image\",\"mime_type\":\"image/png\",\"data\":\"SECRET\"}]}"
            }),
        );
        let mut view = MaterializedView::new();
        view.ingest_event(&event).unwrap();
        let rows = view.audit_rows(Some("media"), 10);
        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].action.as_deref(), Some("request"));
        assert_eq!(
            rows[0].details,
            json!({
                "media_kind": "image",
                "mime_type": "image/png",
                "source": "json_mime_type"
            })
        );
        assert!(!rows[0].details.to_string().contains("SECRET"));
    }
}
