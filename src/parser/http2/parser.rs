//! HTTP/2 Frame Parser - stateless binary frame parser
//!
//! Parses HTTP/2 binary frames from raw SSL event data.
//! Handles the connection preface and extracts individual frames.

use super::frame::{Http2FrameType, ParsedHttp2Frame};
use crate::probes::sslsniff::SslEvent;
use std::rc::Rc;

/// HTTP/2 connection preface (RFC 7540 Section 3.5)
const HTTP2_PREFACE: &[u8] = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n";

/// HTTP/2 frame header size
const FRAME_HEADER_SIZE: usize = 9;

/// HTTP/2 frame parser (stateless)
#[derive(Debug, Default)]
pub struct Http2Parser;

impl Http2Parser {
    pub fn new() -> Self {
        Self
    }

    /// Parse all HTTP/2 frames from an SslEvent buffer
    pub fn parse(&self, event: Rc<SslEvent>) -> Vec<ParsedHttp2Frame> {
        let data_len = event.buf_size() as usize;
        let data = &event.buf[..data_len];

        let mut pos = 0;
        let mut frames = Vec::new();

        // Skip HTTP/2 connection preface if present
        if data.starts_with(HTTP2_PREFACE) {
            pos = HTTP2_PREFACE.len();
        }

        while pos + FRAME_HEADER_SIZE <= data.len() {
            // 3-byte big-endian length
            let length = ((data[pos] as usize) << 16)
                | ((data[pos + 1] as usize) << 8)
                | (data[pos + 2] as usize);

            let frame_type_byte = data[pos + 3];
            let flags = data[pos + 4];

            // 4-byte big-endian stream ID, mask reserved bit
            let stream_id = ((data[pos + 5] as u32 & 0x7F) << 24)
                | ((data[pos + 6] as u32) << 16)
                | ((data[pos + 7] as u32) << 8)
                | (data[pos + 8] as u32);

            let payload_offset = pos + FRAME_HEADER_SIZE;

            if payload_offset + length > data.len() {
                log::debug!(
                    "HTTP/2 frame @ {}: incomplete payload (need {} bytes, have {})",
                    pos,
                    length,
                    data.len() - payload_offset
                );
                break;
            }

            let frame = ParsedHttp2Frame {
                frame_type: Http2FrameType::from_u8(frame_type_byte),
                flags,
                stream_id,
                payload_offset,
                payload_len: length,
                source_event: Rc::clone(&event),
            };

            // Only keep DATA frames for API payload analysis
            if frame.is_data() {
                log::debug!(
                    "HTTP/2 DATA frame: stream={} flags={} len={}, payload={}",
                    stream_id,
                    frame.flags_description(),
                    length,
                    frame.body_str()
                );
                frames.push(frame);
            }


            pos = payload_offset + length;
        }

        frames
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_event(data: Vec<u8>) -> Rc<SslEvent> {
        Rc::new(SslEvent {
            source: 0,
            timestamp_ns: 1000,
            delta_ns: 0,
            pid: 1234,
            tid: 1,
            uid: 0,
            len: data.len() as u32,
            rw: 0,
            comm: "test".to_string(),
            buf: data,
            is_handshake: false,
            ssl_ptr: 0x1000,
        })
    }

    /// Build a raw HTTP/2 frame from parts
    fn build_frame(frame_type: u8, flags: u8, stream_id: u32, payload: &[u8]) -> Vec<u8> {
        let len = payload.len();
        let mut buf = Vec::with_capacity(9 + len);
        // 3-byte length
        buf.push(((len >> 16) & 0xFF) as u8);
        buf.push(((len >> 8) & 0xFF) as u8);
        buf.push((len & 0xFF) as u8);
        // type, flags
        buf.push(frame_type);
        buf.push(flags);
        // 4-byte stream ID
        buf.push(((stream_id >> 24) & 0x7F) as u8);
        buf.push(((stream_id >> 16) & 0xFF) as u8);
        buf.push(((stream_id >> 8) & 0xFF) as u8);
        buf.push((stream_id & 0xFF) as u8);
        // payload
        buf.extend_from_slice(payload);
        buf
    }

    #[test]
    fn test_parse_single_data_frame() {
        let payload = b"hello world";
        let raw = build_frame(0, 0x01, 1, payload); // DATA, END_STREAM, stream 1
        let event = create_test_event(raw);
        let parser = Http2Parser::new();
        let frames = parser.parse(event);

        assert_eq!(frames.len(), 1);
        let f = &frames[0];
        assert!(f.is_data());
        assert_eq!(f.stream_id, 1);
        assert!(f.has_end_stream());
        assert_eq!(f.payload(), b"hello world");
        assert_eq!(f.body_str(), "hello world");
    }

    #[test]
    fn test_parse_non_data_frames_filtered() {
        // SETTINGS frame should be filtered out
        let raw = build_frame(4, 0x01, 0, &[]);
        let event = create_test_event(raw);
        let parser = Http2Parser::new();
        let frames = parser.parse(event);
        assert_eq!(frames.len(), 0);

        // HEADERS frame should be filtered out
        let hpack_data = vec![0x82, 0x86, 0x84];
        let raw = build_frame(1, 0x05, 3, &hpack_data);
        let event = create_test_event(raw);
        let parser = Http2Parser::new();
        let frames = parser.parse(event);
        assert_eq!(frames.len(), 0);
    }

    #[test]
    fn test_parse_multiple_frames_only_data_kept() {
        let mut raw = build_frame(4, 0x00, 0, &[0x00, 0x03, 0x00, 0x00, 0x00, 0x64]); // SETTINGS
        raw.extend(build_frame(0, 0x01, 1, b"{\"ok\":true}")); // DATA END_STREAM
        let event = create_test_event(raw);
        let parser = Http2Parser::new();
        let frames = parser.parse(event);

        // Only DATA frame is kept
        assert_eq!(frames.len(), 1);
        assert!(frames[0].is_data());
        assert_eq!(frames[0].body_str(), "{\"ok\":true}");
    }

    #[test]
    fn test_parse_with_connection_preface() {
        let mut raw = b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n".to_vec();
        raw.extend(build_frame(0, 0x01, 1, b"data")); // DATA
        let event = create_test_event(raw);
        let parser = Http2Parser::new();
        let frames = parser.parse(event);

        assert_eq!(frames.len(), 1);
        assert!(frames[0].is_data());
    }

    #[test]
    fn test_parse_incomplete_frame() {
        // Valid header but truncated payload
        let mut raw = Vec::new();
        raw.push(0x00); raw.push(0x00); raw.push(0x20); // length = 32
        raw.push(0x00); // DATA
        raw.push(0x00); // no flags
        raw.extend(&[0x00, 0x00, 0x00, 0x01]); // stream 1
        raw.extend(b"short"); // only 5 bytes, not 32
        let event = create_test_event(raw);
        let parser = Http2Parser::new();
        let frames = parser.parse(event);

        assert_eq!(frames.len(), 0);
    }

    #[test]
    fn test_parse_empty_buffer() {
        let event = create_test_event(vec![0x01, 0x02, 0x03]); // less than 9 bytes
        let parser = Http2Parser::new();
        let frames = parser.parse(event);
        assert!(frames.is_empty());
    }

    #[test]
    fn test_data_frame_json_body() {
        let json_payload = br#"{"model":"qwen3.5-plus","messages":[{"role":"user","content":"hello"}]}"#;
        let raw = build_frame(0, 0x01, 5, json_payload);
        let event = create_test_event(raw);
        let parser = Http2Parser::new();
        let frames = parser.parse(event);

        assert_eq!(frames.len(), 1);
        let body = frames[0].json_body().unwrap();
        assert_eq!(body["model"], "qwen3.5-plus");
        assert_eq!(body["messages"][0]["role"], "user");
    }

    #[test]
    fn test_frame_flags() {
        // DATA without END_STREAM
        let raw = build_frame(0, 0x00, 1, b"data");
        let event = create_test_event(raw);
        let parser = Http2Parser::new();
        let frames = parser.parse(event);
        assert_eq!(frames.len(), 1);
        assert!(!frames[0].has_end_stream());
        assert!(!frames[0].has_end_headers());

        // DATA with END_STREAM
        let raw = build_frame(0, 0x01, 1, b"data");
        let event = create_test_event(raw);
        let frames = parser.parse(event);
        assert_eq!(frames.len(), 1);
        assert!(frames[0].has_end_stream());
    }

    #[test]
    fn test_sample_data_from_python_script() {
        // Test vector from scripts/http2_parser.py
        // Contains a HEADERS frame (len=83) and an incomplete DATA frame (len=16384, truncated)
        // Since we only keep DATA frames, and the DATA frame is truncated, result should be empty
        let sample_data: Vec<u8> = vec![
            0, 0, 83, 1, 4, 0, 0, 0, 171, 203, 131, 4, 153, 96, 135, 166,
            177, 164, 209, 208, 85, 169, 60, 133, 99, 184, 88, 36, 227, 75,
            4, 61, 53, 208, 84, 152, 245, 35, 135, 202, 201, 200, 199, 198,
            197, 196, 195, 194, 31, 8, 158, 186, 81, 216, 91, 20, 71, 85,
            156, 11, 196, 1, 28, 117, 240, 180, 86, 138, 208, 227, 145, 151,
            218, 142, 87, 136, 65, 133, 185, 25, 143, 193, 192, 191, 190, 15,
            13, 132, 117, 166, 94, 111, 0, 64, 0, 0, 0, 0, 0, 0, 171, 123,
            34, 109, 111, 100, 101, 108, 34, 58, 34, 113, 119, 101, 110, 51,
            46, 53, 45, 112, 108, 117, 115, 34, 44, 34, 109, 101, 115, 115,
            97, 103, 101, 115, 34, 58, 91, 123, 34, 114, 111, 108, 101, 34,
            58, 34, 115, 121, 115, 116, 101, 109, 34, 44, 34, 99, 111, 110,
            116, 101, 110, 116, 34, 58, 34, 89, 111, 117,
        ];
        let event = create_test_event(sample_data);
        let parser = Http2Parser::new();
        let frames = parser.parse(event);

        // HEADERS frame is filtered, DATA frame is truncated -> empty result
        assert_eq!(frames.len(), 0);
    }
}
