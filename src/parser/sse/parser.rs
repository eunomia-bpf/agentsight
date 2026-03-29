use crate::probes::sslsniff::SslEvent;
use super::event::{ParsedSseEvent, SSEEvent, SSEEvents};
use std::rc::Rc;

/// SSE Parser - parses SSE stream data into events (legacy version)
pub struct SSEParser;

impl SSEParser {
    /// Parse SSE stream buffer and extract complete events
    /// Returns SSEEvents container with parsed events and unconsumed data
    pub fn parse_stream(buffer: &str) -> SSEEvents {
        let mut result = SSEEvents::new();
        let mut current_event = SSEEvent::new("");
        let mut data_lines: Vec<String> = Vec::new();
        let mut lines = buffer.lines().peekable();
        let mut consumed_len = 0;

        while let Some(line) = lines.next() {
            consumed_len += line.len() + 1; // +1 for newline

            if line.is_empty() {
                // Empty line terminates the event
                if current_event.id.is_some()
                    || current_event.event.is_some()
                    || current_event.retry.is_some()
                    || !data_lines.is_empty()
                {
                    current_event.data = data_lines.join("\n");
                    result.events.push(current_event);
                    current_event = SSEEvent::new("");
                    data_lines.clear();
                }
            } else if line.starts_with(':') {
                // Comment line - ignore per spec
                continue;
            } else if let Some((field, value)) = line.split_once(':') {
                // Field with optional value (strip leading space if present)
                let value = value.strip_prefix(' ').unwrap_or(value);
                match field {
                    "id" => current_event.id = Some(value.to_string()),
                    "event" => current_event.event = Some(value.to_string()),
                    "data" => data_lines.push(value.to_string()),
                    "retry" => current_event.retry = value.parse().ok(),
                    _ => {} // Unknown field, ignore per spec
                }
            } else {
                // Field without colon, entire line is field name with empty value
                match line {
                    "id" => current_event.id = Some(String::new()),
                    "event" => current_event.event = Some(String::new()),
                    "data" => data_lines.push(String::new()),
                    "retry" => current_event.retry = Some(0),
                    _ => {} // Unknown field, ignore per spec
                }
            }
        }

        // Check if we have a complete event at the end (ends with double newline)
        result.remaining = if buffer.ends_with("\n\n") || buffer.ends_with("\r\n\r\n") {
            String::new()
        } else {
            // Return unconsumed data
            buffer[consumed_len.saturating_sub(1)..].to_string()
        };
        result.consumed_bytes = consumed_len;

        result
    }
}

/// SseParser - new version with zero-copy ParsedSseEvent
#[derive(Debug, Default)]
pub struct SseParser;

impl SseParser {
    /// Create a new SseParser
    pub fn new() -> Self {
        Self
    }

    /// Parse SslEvent and extract SSE events
    /// Returns Vec of ParsedSseEvent
    /// 
    /// Note: For multi-line data fields, data is concatenated with '\n' separators.
    /// The data_offset points to the first data line, data_len covers all data content
    /// including internal newlines.
    pub fn parse(&self, event: Rc<SslEvent>) -> Vec<ParsedSseEvent> {
        let buf_len = event.buf_size() as usize;
        let buf = &event.buf[..buf_len];
        let text = String::from_utf8_lossy(buf);

        let mut events = Vec::new();
        let mut current_id: Option<String> = None;
        let mut current_event: Option<String> = None;
        let mut current_retry: Option<u64> = None;
        let mut data_parts: Vec<String> = Vec::new();
        let mut data_start: Option<usize> = None;

        let mut byte_offset = 0;

        // Use split_inclusive to properly track byte offsets with \r\n line endings
        let lines_iter = text.split_inclusive('\n');
        
        for line_with_end in lines_iter {
            // Remove trailing \r\n or \n for parsing, but keep track of original length
            let line = line_with_end.trim_end_matches('\n').trim_end_matches('\r');
            let line_with_end_len = line_with_end.len();
            let line_start = byte_offset;

            if line.is_empty() {
                // Empty line terminates the event
                if current_id.is_some()
                    || current_event.is_some()
                    || current_retry.is_some()
                    || !data_parts.is_empty()
                {
                    // For zero-copy design, we only record the first data line
                    // Multi-line data concatenation is not supported in zero-copy mode
                    // Users needing full multi-line data should use the legacy SSEParser
                    let (data_offset, data_len) = if !data_parts.is_empty() {
                        // Only use first data line for zero-copy access
                        // Use the actual byte length from original buffer, not UTF-8 string length
                        let first_line_bytes = data_parts[0].as_bytes();
                        let first_line_byte_len = first_line_bytes.len();
                        // Account for \r if present in original data
                        let has_crlf = data_parts[0].ends_with('\r');
                        let adjusted_len = if has_crlf { first_line_byte_len - 1 } else { first_line_byte_len };
                        (data_start.unwrap_or(0), adjusted_len)
                    } else {
                        (0, 0)
                    };

                    events.push(ParsedSseEvent::new(
                        current_id.clone(),
                        current_event.clone(),
                        current_retry,
                        data_offset,
                        data_len,
                        Rc::clone(&event),
                    ));

                    // Reset for next event
                    current_id = None;
                    current_event = None;
                    current_retry = None;
                    data_parts.clear();
                    data_start = None;
                }
            } else if line.starts_with(':') {
                // Comment line - ignore per spec
            } else if let Some((field, value)) = line.split_once(':') {
                // Field with optional value (strip leading space if present per SSE spec)
                // SSE spec: "If line starts with a U+003A COLON character (':'), ignore the line."
                // "If the line contains a U+003A COLON character (':'), collect the characters
                // on the line before the first U+003A COLON character (':'), and let field be that string.
                // Collect the characters on the line after the first U+003A COLON character (':'),
                // and let value be that string. If value starts with a U+0020 SPACE character, 
                // remove it from value."
                let has_space_after_colon = value.starts_with(' ');
                let value_stripped = value.strip_prefix(' ').unwrap_or(value);
                
                // Calculate value_start in the original buffer
                // line_start: start of line in buffer
                // field.len() + 1: skip field and colon
                // +1 if there was a space after colon
                let value_start = line_start + field.len() + 1 + if has_space_after_colon { 1 } else { 0 };
                
                match field {
                    "id" => current_id = Some(value_stripped.to_string()),
                    "event" => current_event = Some(value_stripped.to_string()),
                    "data" => {
                        if data_start.is_none() {
                            data_start = Some(value_start);
                        }
                        // Store the value without \r for consistency
                        data_parts.push(value_stripped.to_string());
                    }
                    "retry" => current_retry = value_stripped.parse().ok(),
                    _ => {} // Unknown field, ignore per spec
                }
            } else {
                // Field without colon, entire line is field name with empty value
                match line {
                    "id" => current_id = Some(String::new()),
                    "event" => current_event = Some(String::new()),
                    "data" => {
                        if data_start.is_none() {
                            data_start = Some(line_start + 5); // "data" + 0 chars
                        }
                        data_parts.push(String::new());
                    }
                    "retry" => current_retry = Some(0),
                    _ => {} // Unknown field, ignore per spec
                }
            }

            byte_offset += line_with_end_len;
        }

        // Handle event at end without double newline
        if current_id.is_some()
            || current_event.is_some()
            || current_retry.is_some()
            || !data_parts.is_empty()
        {
            let (data_offset, data_len) = if !data_parts.is_empty() {
                // Only use first data line for zero-copy access
                let first_line_len = data_parts[0].len();
                (data_start.unwrap_or(0), first_line_len)
            } else {
                (0, 0)
            };

            events.push(ParsedSseEvent::new(
                current_id,
                current_event,
                current_retry,
                data_offset,
                data_len,
                Rc::clone(&event),
            ));
        }

        events
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_event(data: Vec<u8>) -> Rc<SslEvent> {
        let len = data.len();

        Rc::new(SslEvent {
            source: 1,
            timestamp_ns: 0,
            delta_ns: 0,
            pid: 1234,
            tid: 1234,
            uid: 0,
            len: len as u32,
            rw: 0,
            comm: String::new(),
            buf: data,
            is_handshake: false,
            ssl_ptr: 0x1000,
        })
    }

    #[test]
    fn test_parse_simple_sse_event() {
        let parser = SseParser::new();
        let data = b"data: hello world\n\n".to_vec();
        let event = create_test_event(data);

        let events = parser.parse(event);
        assert_eq!(events.len(), 1);
        
        let evt = &events[0];
        assert_eq!(evt.id, None);
        assert_eq!(evt.event, None);
        assert_eq!(evt.data(), b"hello world");
        assert!(!evt.is_done());
    }

    #[test]
    fn test_parse_sse_with_id_and_event() {
        let parser = SseParser::new();
        let data = b"id: 123\nevent: message\ndata: hello\n\n".to_vec();
        let event = create_test_event(data);

        let events = parser.parse(event);
        assert_eq!(events.len(), 1);
        
        let evt = &events[0];
        assert_eq!(evt.id, Some("123".to_string()));
        assert_eq!(evt.event, Some("message".to_string()));
        assert_eq!(evt.data(), b"hello");
    }

    #[test]
    fn test_parse_multiple_events() {
        let parser = SseParser::new();
        let data = b"data: first\n\ndata: second\n\n".to_vec();
        let event = create_test_event(data);

        let events = parser.parse(event);
        assert_eq!(events.len(), 2);
        
        assert_eq!(events[0].data(), b"first");
        assert_eq!(events[1].data(), b"second");
    }

    #[test]
    fn test_parse_done_marker() {
        let parser = SseParser::new();
        let data = b"event: done\ndata: [DONE]\n\n".to_vec();
        let event = create_test_event(data);

        let events = parser.parse(event);
        assert_eq!(events.len(), 1);
        
        let evt = &events[0];
        assert!(evt.is_done());
    }

    #[test]
    fn test_parse_multiline_data() {
        let parser = SseParser::new();
        let data = b"data: line1\ndata: line2\n\n".to_vec();
        let event = create_test_event(data);

        let events = parser.parse(event);
        assert_eq!(events.len(), 1);
        
        let evt = &events[0];
        // Multi-line data: offset points to first line "line1"
        // data_len is the length of first line only (5)
        // Full multi-line concatenation is not implemented in zero-copy mode
        assert_eq!(evt.data(), b"line1");
        assert_eq!(evt.data_len(), 5);
    }

    #[test]
    fn test_parse_comment_ignored() {
        let parser = SseParser::new();
        let data = b": this is a comment\ndata: hello\n\n".to_vec();
        let event = create_test_event(data);

        let events = parser.parse(event);
        assert_eq!(events.len(), 1);
        
        let evt = &events[0];
        assert_eq!(evt.data(), b"hello");
    }
}
