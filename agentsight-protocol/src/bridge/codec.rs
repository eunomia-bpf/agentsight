// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Frame codec: `u32` little-endian body length followed by a CBOR body.
//!
//! Transport-independent by design — callers hand in byte buffers, so the same
//! codec drives the tokio Unix-socket server and the synchronous client.

use super::BridgeMessage;

/// Bytes of length prefix in front of every frame body.
pub const FRAME_HEADER_BYTES: usize = 4;

/// Everything that can go wrong framing or parsing a bridge message.
#[derive(Debug)]
pub enum BridgeCodecError {
    /// The body exceeded the negotiated frame ceiling.
    FrameTooLarge { len: u64, max: u32 },
    /// The message could not be encoded to CBOR.
    Encode(String),
    /// The frame body was not a valid CBOR bridge message.
    Decode(String),
}

impl std::fmt::Display for BridgeCodecError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::FrameTooLarge { len, max } => {
                write!(
                    f,
                    "bridge frame of {len} bytes exceeds the {max} byte limit"
                )
            }
            Self::Encode(detail) => write!(f, "failed to encode bridge message: {detail}"),
            Self::Decode(detail) => write!(f, "failed to decode bridge message: {detail}"),
        }
    }
}

impl std::error::Error for BridgeCodecError {}

/// Encode a message body without the length prefix.
pub fn encode_body(message: &BridgeMessage) -> Result<Vec<u8>, BridgeCodecError> {
    let mut body = Vec::new();
    ciborium::into_writer(message, &mut body)
        .map_err(|error| BridgeCodecError::Encode(error.to_string()))?;
    Ok(body)
}

/// Decode a message body that has already been separated from its prefix.
pub fn decode_body(body: &[u8]) -> Result<BridgeMessage, BridgeCodecError> {
    ciborium::from_reader(body).map_err(|error| BridgeCodecError::Decode(error.to_string()))
}

/// Encode a complete frame: `u32` LE length prefix plus the CBOR body.
pub fn encode_frame(
    message: &BridgeMessage,
    max_frame_bytes: u32,
) -> Result<Vec<u8>, BridgeCodecError> {
    let body = encode_body(message)?;
    if body.len() as u64 > u64::from(max_frame_bytes) {
        return Err(BridgeCodecError::FrameTooLarge {
            len: body.len() as u64,
            max: max_frame_bytes,
        });
    }
    let mut frame = Vec::with_capacity(FRAME_HEADER_BYTES + body.len());
    frame.extend_from_slice(&(body.len() as u32).to_le_bytes());
    frame.extend_from_slice(&body);
    Ok(frame)
}

/// Try to read one frame from the front of `buffer`.
///
/// Returns `Ok(None)` when the buffer does not yet hold a complete frame, so a
/// reader can append more bytes and retry. On success the second tuple element
/// is the number of bytes consumed.
pub fn read_frame(
    buffer: &[u8],
    max_frame_bytes: u32,
) -> Result<Option<(BridgeMessage, usize)>, BridgeCodecError> {
    let Some(header) = buffer.get(..FRAME_HEADER_BYTES) else {
        return Ok(None);
    };
    let len = u32::from_le_bytes([header[0], header[1], header[2], header[3]]);
    if len > max_frame_bytes {
        return Err(BridgeCodecError::FrameTooLarge {
            len: u64::from(len),
            max: max_frame_bytes,
        });
    }
    let end = FRAME_HEADER_BYTES + len as usize;
    let Some(body) = buffer.get(FRAME_HEADER_BYTES..end) else {
        return Ok(None);
    };
    Ok(Some((decode_body(body)?, end)))
}

#[cfg(test)]
mod tests {
    use super::super::{BRIDGE_PROTOCOL_VERSION, BridgeHello, DisclosureMode, MAX_FRAME_BYTES};
    use super::*;

    fn hello() -> BridgeMessage {
        BridgeMessage::Hello(BridgeHello {
            supported_versions: vec![BRIDGE_PROTOCOL_VERSION],
            product: "aro".to_string(),
            product_version: "0.1.0".to_string(),
            max_frame_bytes: MAX_FRAME_BYTES,
            disclosure: DisclosureMode::MetadataOnly,
        })
    }

    #[test]
    fn frame_round_trips_and_reports_consumed_bytes() {
        let frame = encode_frame(&hello(), MAX_FRAME_BYTES).unwrap();
        let (message, consumed) = read_frame(&frame, MAX_FRAME_BYTES).unwrap().unwrap();
        assert_eq!(message, hello());
        assert_eq!(consumed, frame.len());
    }

    #[test]
    fn partial_frames_are_not_an_error() {
        let frame = encode_frame(&hello(), MAX_FRAME_BYTES).unwrap();
        assert!(read_frame(&frame[..2], MAX_FRAME_BYTES).unwrap().is_none());
        assert!(
            read_frame(&frame[..frame.len() - 1], MAX_FRAME_BYTES)
                .unwrap()
                .is_none()
        );
    }

    #[test]
    fn two_frames_are_read_one_at_a_time() {
        let mut buffer = encode_frame(&hello(), MAX_FRAME_BYTES).unwrap();
        buffer.extend(
            encode_frame(
                &BridgeMessage::Heartbeat { monotonic_ns: 7 },
                MAX_FRAME_BYTES,
            )
            .unwrap(),
        );
        let (first, consumed) = read_frame(&buffer, MAX_FRAME_BYTES).unwrap().unwrap();
        assert_eq!(first, hello());
        let (second, _) = read_frame(&buffer[consumed..], MAX_FRAME_BYTES)
            .unwrap()
            .unwrap();
        assert_eq!(second, BridgeMessage::Heartbeat { monotonic_ns: 7 });
    }

    #[test]
    fn oversize_frames_are_rejected_on_both_sides() {
        let error = encode_frame(&hello(), 4).unwrap_err();
        assert!(matches!(error, BridgeCodecError::FrameTooLarge { .. }));

        let mut buffer = 4_000_000u32.to_le_bytes().to_vec();
        buffer.extend_from_slice(&[0u8; 8]);
        let error = read_frame(&buffer, MAX_FRAME_BYTES).unwrap_err();
        assert!(matches!(
            error,
            BridgeCodecError::FrameTooLarge {
                len: 4_000_000,
                max: MAX_FRAME_BYTES
            }
        ));
    }

    #[test]
    fn garbage_bodies_are_decode_errors() {
        let body = [0xffu8, 0xff, 0xff, 0xff];
        let mut buffer = (body.len() as u32).to_le_bytes().to_vec();
        buffer.extend_from_slice(&body);
        let error = read_frame(&buffer, MAX_FRAME_BYTES).unwrap_err();
        assert!(matches!(error, BridgeCodecError::Decode(_)), "{error}");
    }

    #[test]
    fn truncated_cbor_body_is_a_decode_error_not_a_short_read() {
        let frame = encode_frame(&hello(), MAX_FRAME_BYTES).unwrap();
        let body = &frame[FRAME_HEADER_BYTES..];
        // Claim a shorter body than the message needs: the bytes are all
        // present, so this is malformed CBOR rather than an incomplete frame.
        let truncated = &body[..body.len() - 4];
        let mut buffer = (truncated.len() as u32).to_le_bytes().to_vec();
        buffer.extend_from_slice(truncated);
        let error = read_frame(&buffer, MAX_FRAME_BYTES).unwrap_err();
        assert!(matches!(error, BridgeCodecError::Decode(_)), "{error}");
    }
}
