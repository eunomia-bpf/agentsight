// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::event::Event;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::BTreeSet;

const MAX_CAPTURE_TIDS: usize = 64;

/// Bounded provenance summary for events assembled from one or more capture events.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(default)]
pub(crate) struct CaptureMetadata {
    pub transport_handle: Option<String>,
    pub process_start_ns: Option<u64>,
    pub tls_library: Option<String>,
    pub capture_seq_start: Option<u64>,
    pub capture_seq_end: Option<u64>,
    pub capture_fragment_count: u64,
    pub capture_original_len: Option<u64>,
    pub capture_captured_len: Option<u64>,
    pub capture_truncated: Option<bool>,
    pub capture_bytes_lost: Option<u64>,
    pub ringbuf_reserve_failures_start: Option<u64>,
    pub ringbuf_reserve_failures_end: Option<u64>,
    pub ringbuf_reserve_failures_delta: Option<u64>,
    pub capture_tids: Vec<u64>,
    pub capture_tid_count: u64,
    pub capture_tids_truncated: bool,
    pub capture_identity_consistent: bool,
    pub capture_metadata_complete: bool,
}

impl Default for CaptureMetadata {
    fn default() -> Self {
        Self {
            transport_handle: None,
            process_start_ns: None,
            tls_library: None,
            capture_seq_start: None,
            capture_seq_end: None,
            capture_fragment_count: 0,
            capture_original_len: None,
            capture_captured_len: None,
            capture_truncated: None,
            capture_bytes_lost: None,
            ringbuf_reserve_failures_start: None,
            ringbuf_reserve_failures_end: None,
            ringbuf_reserve_failures_delta: None,
            capture_tids: Vec::new(),
            capture_tid_count: 0,
            capture_tids_truncated: false,
            capture_identity_consistent: true,
            capture_metadata_complete: false,
        }
    }
}

#[derive(Clone, Default)]
pub(crate) struct CaptureMetadataAccumulator {
    transport_handle: ConsistentValue<String>,
    process_start_ns: ConsistentValue<u64>,
    tls_library: ConsistentValue<String>,
    capture_seq_start: Option<u64>,
    capture_seq_end: Option<u64>,
    capture_seq_complete: bool,
    capture_fragment_count: u64,
    capture_original_len: Option<u64>,
    capture_captured_len: Option<u64>,
    capture_lengths_complete: bool,
    saw_truncated: bool,
    saw_unknown_truncation: bool,
    capture_bytes_lost: Option<u64>,
    capture_bytes_lost_complete: bool,
    ringbuf_reserve_failures_start: Option<u64>,
    ringbuf_reserve_failures_end: Option<u64>,
    capture_tids: BTreeSet<u64>,
    unlisted_tid_count: u64,
    capture_tids_truncated: bool,
    identity_consistent: bool,
    metadata_complete: bool,
}

#[derive(Clone, Default)]
struct ConsistentValue<T> {
    value: Option<T>,
    conflicted: bool,
}

impl<T: PartialEq> ConsistentValue<T> {
    fn observe(&mut self, value: Option<T>) {
        let Some(value) = value else {
            return;
        };
        match self.value.as_ref() {
            None => self.value = Some(value),
            Some(existing) if existing != &value => self.conflicted = true,
            Some(_) => {}
        }
    }

    fn invalidate(&mut self) {
        self.conflicted = true;
    }
}

impl<T: Clone> ConsistentValue<T> {
    fn result(&self) -> Option<T> {
        (!self.conflicted).then(|| self.value.clone()).flatten()
    }
}

impl CaptureMetadataAccumulator {
    pub(crate) fn observe_event(&mut self, event: &Event) {
        if event.data.get("capture_fragment_count").is_some() {
            self.observe_summary(&event.data);
        } else {
            self.observe_capture_fragment(&event.data);
        }
    }

    pub(crate) fn finish(&self) -> CaptureMetadata {
        let identity_consistent = self.identity_consistent
            && !self.transport_handle.conflicted
            && !self.process_start_ns.conflicted
            && !self.tls_library.conflicted;
        let capture_tids = self
            .capture_tids
            .iter()
            .take(MAX_CAPTURE_TIDS)
            .copied()
            .collect::<Vec<_>>();
        let capture_tid_count =
            (self.capture_tids.len() as u64).saturating_add(self.unlisted_tid_count);
        let capture_tids_truncated =
            self.capture_tids_truncated || capture_tid_count > capture_tids.len() as u64;
        let (capture_seq_start, capture_seq_end) = if self.capture_seq_complete {
            (self.capture_seq_start, self.capture_seq_end)
        } else {
            (None, None)
        };
        let (capture_original_len, capture_captured_len) = if self.capture_lengths_complete {
            (self.capture_original_len, self.capture_captured_len)
        } else {
            (None, None)
        };
        let capture_truncated = if self.saw_truncated {
            Some(true)
        } else if self.saw_unknown_truncation {
            None
        } else {
            Some(false)
        };
        let capture_bytes_lost = self
            .capture_bytes_lost_complete
            .then_some(self.capture_bytes_lost)
            .flatten();
        let ringbuf_reserve_failures_delta = self
            .ringbuf_reserve_failures_start
            .zip(self.ringbuf_reserve_failures_end)
            .map(|(start, end)| end.saturating_sub(start));

        CaptureMetadata {
            transport_handle: identity_consistent
                .then(|| self.transport_handle.result())
                .flatten(),
            process_start_ns: identity_consistent
                .then(|| self.process_start_ns.result())
                .flatten(),
            tls_library: identity_consistent
                .then(|| self.tls_library.result())
                .flatten(),
            capture_seq_start,
            capture_seq_end,
            capture_fragment_count: self.capture_fragment_count,
            capture_original_len,
            capture_captured_len,
            capture_truncated,
            capture_bytes_lost,
            ringbuf_reserve_failures_start: self.ringbuf_reserve_failures_start,
            ringbuf_reserve_failures_end: self.ringbuf_reserve_failures_end,
            ringbuf_reserve_failures_delta,
            capture_tids,
            capture_tid_count,
            capture_tids_truncated,
            capture_identity_consistent: identity_consistent,
            capture_metadata_complete: self.metadata_complete,
        }
    }

    fn observe_capture_fragment(&mut self, data: &Value) {
        let first = self.capture_fragment_count == 0;
        self.capture_fragment_count = self.capture_fragment_count.saturating_add(1);
        if first {
            self.capture_seq_complete = true;
            self.capture_lengths_complete = true;
            self.capture_bytes_lost_complete = true;
            self.identity_consistent = true;
            self.metadata_complete = true;
        }

        let transport_handle = value_as_string(data.get("transport_handle"));
        let process_start_ns = value_as_u64(data.get("process_start_ns"));
        let tls_library = value_as_string(data.get("tls_library"));
        self.transport_handle.observe(transport_handle.clone());
        self.process_start_ns.observe(process_start_ns);
        self.tls_library.observe(tls_library.clone());
        if transport_handle.is_none() || process_start_ns.is_none() || tls_library.is_none() {
            self.metadata_complete = false;
        }

        let capture_seq = value_as_u64(data.get("capture_seq"));
        if let Some(capture_seq) = capture_seq {
            self.capture_seq_start = Some(
                self.capture_seq_start
                    .map_or(capture_seq, |start| start.min(capture_seq)),
            );
            self.capture_seq_end = Some(
                self.capture_seq_end
                    .map_or(capture_seq, |end| end.max(capture_seq)),
            );
        } else {
            self.capture_seq_complete = false;
            self.metadata_complete = false;
        }

        self.add_lengths(
            value_as_u64(data.get("len")),
            value_as_u64(data.get("buf_size")),
        );
        self.observe_truncation(
            data.get("truncated").and_then(Value::as_bool),
            value_as_u64(data.get("bytes_lost")),
        );

        let failures = value_as_u64(data.get("ringbuf_reserve_failures"));
        if first {
            self.ringbuf_reserve_failures_start = failures;
        }
        self.ringbuf_reserve_failures_end = failures;
        if failures.is_none() {
            self.metadata_complete = false;
        }

        if let Some(tid) = value_as_u64(data.get("tid")) {
            self.capture_tids.insert(tid);
        } else {
            self.metadata_complete = false;
        }
    }

    fn observe_summary(&mut self, data: &Value) {
        let first = self.capture_fragment_count == 0;
        let fragment_count = value_as_u64(data.get("capture_fragment_count"));
        self.capture_fragment_count = self
            .capture_fragment_count
            .saturating_add(fragment_count.unwrap_or(1));
        if first {
            self.capture_seq_complete = true;
            self.capture_lengths_complete = true;
            self.capture_bytes_lost_complete = true;
            self.identity_consistent = true;
            self.metadata_complete = true;
        }
        if fragment_count.is_none() {
            self.metadata_complete = false;
        }

        self.transport_handle
            .observe(value_as_string(data.get("transport_handle")));
        self.process_start_ns
            .observe(value_as_u64(data.get("process_start_ns")));
        self.tls_library
            .observe(value_as_string(data.get("tls_library")));
        if data
            .get("capture_identity_consistent")
            .and_then(Value::as_bool)
            != Some(true)
        {
            self.identity_consistent = false;
            self.transport_handle.invalidate();
            self.process_start_ns.invalidate();
            self.tls_library.invalidate();
        }

        let seq_start = value_as_u64(data.get("capture_seq_start"));
        let seq_end = value_as_u64(data.get("capture_seq_end"));
        if let (Some(start), Some(end)) = (seq_start, seq_end) {
            self.capture_seq_start = Some(
                self.capture_seq_start
                    .map_or(start, |existing| existing.min(start)),
            );
            self.capture_seq_end = Some(
                self.capture_seq_end
                    .map_or(end, |existing| existing.max(end)),
            );
        } else {
            self.capture_seq_complete = false;
        }

        self.add_lengths(
            value_as_u64(data.get("capture_original_len")),
            value_as_u64(data.get("capture_captured_len")),
        );
        self.observe_truncation(
            data.get("capture_truncated").and_then(Value::as_bool),
            value_as_u64(data.get("capture_bytes_lost")),
        );

        if first {
            self.ringbuf_reserve_failures_start =
                value_as_u64(data.get("ringbuf_reserve_failures_start"));
        }
        self.ringbuf_reserve_failures_end = value_as_u64(data.get("ringbuf_reserve_failures_end"));

        let tids = data
            .get("capture_tids")
            .and_then(Value::as_array)
            .map(|values| {
                values
                    .iter()
                    .filter_map(|value| value_as_u64(Some(value)))
                    .collect::<Vec<_>>()
            })
            .unwrap_or_default();
        for tid in &tids {
            self.capture_tids.insert(*tid);
        }
        let reported_tid_count =
            value_as_u64(data.get("capture_tid_count")).unwrap_or(tids.len() as u64);
        self.unlisted_tid_count = self
            .unlisted_tid_count
            .max(reported_tid_count.saturating_sub(tids.len() as u64));
        self.capture_tids_truncated |= data
            .get("capture_tids_truncated")
            .and_then(Value::as_bool)
            .unwrap_or(false);

        if data
            .get("capture_metadata_complete")
            .and_then(Value::as_bool)
            != Some(true)
        {
            self.metadata_complete = false;
        }
    }

    fn add_lengths(&mut self, original_len: Option<u64>, captured_len: Option<u64>) {
        if let (Some(original_len), Some(captured_len)) = (original_len, captured_len) {
            self.capture_original_len = checked_sum(self.capture_original_len, original_len);
            self.capture_captured_len = checked_sum(self.capture_captured_len, captured_len);
            if self.capture_original_len.is_none() || self.capture_captured_len.is_none() {
                self.capture_lengths_complete = false;
                self.metadata_complete = false;
            }
        } else {
            self.capture_lengths_complete = false;
            self.metadata_complete = false;
        }
    }

    fn observe_truncation(&mut self, truncated: Option<bool>, bytes_lost: Option<u64>) {
        match truncated {
            Some(true) => {
                self.saw_truncated = true;
                if let Some(bytes_lost) = bytes_lost {
                    self.capture_bytes_lost = checked_sum(self.capture_bytes_lost, bytes_lost);
                    if self.capture_bytes_lost.is_none() {
                        self.capture_bytes_lost_complete = false;
                        self.metadata_complete = false;
                    }
                } else {
                    self.capture_bytes_lost_complete = false;
                    self.metadata_complete = false;
                }
            }
            Some(false) => {
                self.capture_bytes_lost = checked_sum(self.capture_bytes_lost, 0);
            }
            None => {
                self.saw_unknown_truncation = true;
                self.capture_bytes_lost_complete = false;
                self.metadata_complete = false;
            }
        }
    }
}

fn checked_sum(current: Option<u64>, value: u64) -> Option<u64> {
    current.unwrap_or(0).checked_add(value)
}

fn value_as_u64(value: Option<&Value>) -> Option<u64> {
    value.and_then(|value| {
        value
            .as_u64()
            .or_else(|| value.as_str().and_then(|value| value.parse().ok()))
    })
}

fn value_as_string(value: Option<&Value>) -> Option<String> {
    value.and_then(|value| match value {
        Value::String(value) => Some(value.clone()),
        Value::Number(value) => Some(value.to_string()),
        _ => None,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn capture_event(data: Value) -> Event {
        Event::new_with_timestamp(1, "ssl".to_string(), 10, "test".to_string(), data)
    }

    #[test]
    fn aggregates_lengths_ranges_loss_and_unique_tids() {
        let mut accumulator = CaptureMetadataAccumulator::default();
        accumulator.observe_event(&capture_event(json!({
            "transport_handle": "0xa",
            "process_start_ns": 11,
            "tls_library": "openssl",
            "capture_seq": 20,
            "len": 100,
            "buf_size": 90,
            "truncated": true,
            "bytes_lost": 10,
            "ringbuf_reserve_failures": 2,
            "tid": 100
        })));
        accumulator.observe_event(&capture_event(json!({
            "transport_handle": "0xa",
            "process_start_ns": 11,
            "tls_library": "openssl",
            "capture_seq": 21,
            "len": 50,
            "buf_size": 50,
            "truncated": false,
            "ringbuf_reserve_failures": 5,
            "tid": 200
        })));

        let metadata = accumulator.finish();
        assert_eq!(metadata.transport_handle.as_deref(), Some("0xa"));
        assert_eq!(metadata.capture_seq_start, Some(20));
        assert_eq!(metadata.capture_seq_end, Some(21));
        assert_eq!(metadata.capture_fragment_count, 2);
        assert_eq!(metadata.capture_original_len, Some(150));
        assert_eq!(metadata.capture_captured_len, Some(140));
        assert_eq!(metadata.capture_truncated, Some(true));
        assert_eq!(metadata.capture_bytes_lost, Some(10));
        assert_eq!(metadata.ringbuf_reserve_failures_delta, Some(3));
        assert_eq!(metadata.capture_tids, vec![100, 200]);
        assert!(metadata.capture_identity_consistent);
        assert!(metadata.capture_metadata_complete);
    }

    #[test]
    fn conflicts_clear_identity_and_missing_lengths_are_not_partial_totals() {
        let mut accumulator = CaptureMetadataAccumulator::default();
        accumulator.observe_event(&capture_event(json!({
            "transport_handle": "0xa", "process_start_ns": 11,
            "tls_library": "openssl", "capture_seq": 20,
            "len": 100, "buf_size": 100, "truncated": false,
            "ringbuf_reserve_failures": 0, "tid": 100
        })));
        accumulator.observe_event(&capture_event(json!({
            "transport_handle": "0xb", "process_start_ns": 11,
            "tls_library": "openssl", "capture_seq": 21,
            "truncated": false, "ringbuf_reserve_failures": 0, "tid": 100
        })));

        let metadata = accumulator.finish();
        assert_eq!(metadata.transport_handle, None);
        assert_eq!(metadata.process_start_ns, None);
        assert_eq!(metadata.tls_library, None);
        assert!(!metadata.capture_identity_consistent);
        assert_eq!(metadata.capture_original_len, None);
        assert_eq!(metadata.capture_captured_len, None);
        assert!(!metadata.capture_metadata_complete);
    }

    #[test]
    fn limits_serialized_tid_list_but_keeps_unique_count() {
        let mut accumulator = CaptureMetadataAccumulator::default();
        for tid in 0..70 {
            accumulator.observe_event(&capture_event(json!({
                "transport_handle": "0xa", "process_start_ns": 11,
                "tls_library": "openssl", "capture_seq": tid,
                "len": 1, "buf_size": 1, "truncated": false,
                "ringbuf_reserve_failures": 0, "tid": tid
            })));
        }
        let metadata = accumulator.finish();
        assert_eq!(metadata.capture_tids.len(), MAX_CAPTURE_TIDS);
        assert_eq!(metadata.capture_tid_count, 70);
        assert!(metadata.capture_tids_truncated);
    }

    #[test]
    fn legacy_fragment_remains_compatible_and_marks_metadata_incomplete() {
        let mut accumulator = CaptureMetadataAccumulator::default();
        accumulator.observe_event(&capture_event(json!({
            "data": "legacy", "function": "READ/RECV", "tid": 100
        })));

        let metadata = accumulator.finish();
        assert_eq!(metadata.capture_fragment_count, 1);
        assert_eq!(metadata.transport_handle, None);
        assert_eq!(metadata.capture_original_len, None);
        assert_eq!(metadata.capture_truncated, None);
        assert_eq!(metadata.capture_tids, vec![100]);
        assert!(metadata.capture_identity_consistent);
        assert!(!metadata.capture_metadata_complete);
    }

    #[test]
    fn missing_serialized_fields_deserialize_to_nullable_legacy_defaults() {
        let metadata: CaptureMetadata = serde_json::from_value(json!({})).unwrap();

        assert_eq!(metadata.transport_handle, None);
        assert_eq!(metadata.capture_fragment_count, 0);
        assert!(metadata.capture_identity_consistent);
        assert!(!metadata.capture_metadata_complete);
    }
}
