// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use windows_sys::Win32::System::Diagnostics::Etw::{
    EVENT_HEADER_FLAG_32_BIT_HEADER, EVENT_HEADER_FLAG_64_BIT_HEADER, EVENT_TRACE_TYPE_DC_END,
    EVENT_TRACE_TYPE_DC_START, EVENT_TRACE_TYPE_END, EVENT_TRACE_TYPE_START,
    EVENT_TRACE_TYPE_TERMINATE,
};

const WINDOWS_EPOCH_DELTA_100NS: i64 = 116_444_736_000_000_000;

pub(super) fn event_pointer_size(flags: u16) -> usize {
    let flags = u32::from(flags);
    if size_of::<usize>() == 8
        && flags & EVENT_HEADER_FLAG_32_BIT_HEADER == EVENT_HEADER_FLAG_32_BIT_HEADER
    {
        4
    } else if size_of::<usize>() == 4
        && flags & EVENT_HEADER_FLAG_64_BIT_HEADER == EVENT_HEADER_FLAG_64_BIT_HEADER
    {
        8
    } else {
        size_of::<usize>()
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(super) enum EtwProcessPhase {
    Start,
    DCStart,
    End,
    DCEnd,
    Terminate,
    Unknown,
}

impl EtwProcessPhase {
    pub(super) fn from_opcode(opcode: u8) -> Self {
        match opcode {
            opcode if opcode == EVENT_TRACE_TYPE_START as u8 => Self::Start,
            opcode if opcode == EVENT_TRACE_TYPE_DC_START as u8 => Self::DCStart,
            opcode if opcode == EVENT_TRACE_TYPE_END as u8 => Self::End,
            opcode if opcode == EVENT_TRACE_TYPE_DC_END as u8 => Self::DCEnd,
            opcode if opcode == EVENT_TRACE_TYPE_TERMINATE as u8 => Self::Terminate,
            _ => Self::Unknown,
        }
    }

    pub(super) fn is_start(self) -> bool {
        matches!(self, Self::Start | Self::DCStart)
    }

    pub(super) fn is_existing(self) -> bool {
        matches!(self, Self::DCStart | Self::DCEnd)
    }

    pub(super) fn as_str(self) -> &'static str {
        match self {
            Self::Start => "Start",
            Self::DCStart => "DCStart",
            Self::End => "End",
            Self::DCEnd => "DCEnd",
            Self::Terminate => "Terminate",
            Self::Unknown => "Unknown",
        }
    }

    pub(super) fn event_name(self) -> &'static str {
        match self {
            Self::Start => "EXEC",
            Self::DCStart => "PROCESS_PRESENT",
            Self::End => "EXIT",
            Self::DCEnd => "PROCESS_PRESENT_AT_STOP",
            Self::Terminate => "EXIT",
            Self::Unknown => "PROCESS_UNKNOWN",
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
pub(super) struct ProcessEtwRecord {
    pub(super) pid: u32,
    pub(super) ppid: Option<u32>,
    pub(super) session_id: Option<u32>,
    pub(super) unique_process_key: Option<u64>,
    pub(super) exit_status: Option<i32>,
    pub(super) image_file_name: Option<String>,
    pub(super) command_line: Option<String>,
}

struct PayloadCursor<'a> {
    data: &'a [u8],
    position: usize,
}

impl<'a> PayloadCursor<'a> {
    fn new(data: &'a [u8]) -> Self {
        Self { data, position: 0 }
    }

    fn remaining(&self) -> usize {
        self.data.len().saturating_sub(self.position)
    }

    fn skip(&mut self, length: usize) -> bool {
        if self.remaining() < length {
            return false;
        }
        self.position += length;
        true
    }

    fn u32_le(&mut self) -> Option<u32> {
        let bytes = self.data.get(self.position..self.position + 4)?;
        let value = u32::from_le_bytes(bytes.try_into().ok()?);
        self.position += 4;
        Some(value)
    }

    fn peek_u32_le(&self) -> Option<u32> {
        let bytes = self.data.get(self.position..self.position + 4)?;
        Some(u32::from_le_bytes(bytes.try_into().ok()?))
    }

    fn u16_le(&mut self) -> Option<u16> {
        let bytes = self.data.get(self.position..self.position + 2)?;
        let value = u16::from_le_bytes(bytes.try_into().ok()?);
        self.position += 2;
        Some(value)
    }

    fn u8(&mut self) -> Option<u8> {
        let value = self.data.get(self.position).copied()?;
        self.position += 1;
        Some(value)
    }

    fn i32_le(&mut self) -> Option<i32> {
        self.u32_le().map(|value| value as i32)
    }

    fn pointer(&mut self, pointer_size: usize) -> Option<u64> {
        match pointer_size {
            4 => self.u32_le().map(u64::from),
            8 => {
                let bytes = self.data.get(self.position..self.position + 8)?;
                let value = u64::from_le_bytes(bytes.try_into().ok()?);
                self.position += 8;
                Some(value)
            }
            _ => None,
        }
    }

    fn null_terminated_bytes(&mut self) -> Option<String> {
        let start = self.position;
        let mut end = start;
        while end < self.data.len() {
            if self.data[end] == 0 {
                let value = String::from_utf8_lossy(&self.data[start..end]).into_owned();
                self.position = end + 1;
                return Some(value);
            }
            end += 1;
        }
        None
    }

    fn null_terminated_utf16(&mut self) -> Option<String> {
        let start = self.position;
        let mut end = start;
        while end + 1 < self.data.len() {
            if self.data[end] == 0 && self.data[end + 1] == 0 {
                let units = self.data[start..end]
                    .chunks_exact(2)
                    .map(|chunk| u16::from_le_bytes([chunk[0], chunk[1]]))
                    .collect::<Vec<_>>();
                self.position = end + 2;
                return Some(String::from_utf16_lossy(&units));
            }
            end += 2;
        }
        None
    }

    fn skip_user_sid(&mut self, pointer_size: usize) -> bool {
        if self.peek_u32_le() == Some(0) {
            return self.skip(4);
        }
        if self.pointer(pointer_size).is_none() || self.u32_le().is_none() {
            return false;
        }
        if pointer_size == 8 && self.u32_le().is_none() {
            return false;
        }
        let Some(revision) = self.u8() else {
            return false;
        };
        let Some(sub_authority_count) = self.u8() else {
            return false;
        };
        if revision != 1 || self.u16_le().is_none() || self.u32_le().is_none() {
            return false;
        }
        self.skip(4 * sub_authority_count as usize)
    }
}

pub(super) fn parse_process_start(
    data: &[u8],
    version: u8,
    pointer_size: usize,
) -> Option<ProcessEtwRecord> {
    if version > 4 {
        return None;
    }
    let mut cursor = PayloadCursor::new(data);

    let (unique_process_key, pid, ppid) = if version == 0 {
        (
            None,
            cursor.pointer(pointer_size)? as u32,
            cursor.pointer(pointer_size)? as u32,
        )
    } else {
        if version == 1 {
            cursor.pointer(pointer_size)?;
        }
        let unique_process_key = if version >= 2 {
            cursor.pointer(pointer_size)
        } else {
            None
        };
        (unique_process_key, cursor.u32_le()?, cursor.u32_le()?)
    };

    let (session_id, exit_status) = if version >= 1 {
        let session_id = cursor.u32_le()?;
        let exit_status = cursor.i32_le()?;
        (Some(session_id), Some(exit_status))
    } else {
        (None, None)
    };

    if version >= 3 && !cursor.skip(pointer_size) {
        return None;
    }
    if version >= 4 && !cursor.skip(4) {
        return None;
    }
    if !cursor.skip_user_sid(pointer_size) {
        return None;
    }
    let image_file_name = if version >= 1 {
        Some(cursor.null_terminated_bytes()?)
    } else {
        cursor.null_terminated_bytes()
    };
    let command_line = if version >= 2 {
        Some(cursor.null_terminated_utf16()?)
    } else {
        None
    };

    Some(ProcessEtwRecord {
        pid,
        ppid: Some(ppid),
        session_id,
        unique_process_key,
        exit_status,
        image_file_name,
        command_line,
    })
}

pub(super) fn parse_process_end(
    data: &[u8],
    version: u8,
    pointer_size: usize,
) -> Option<ProcessEtwRecord> {
    parse_process_start(data, version, pointer_size)
}

pub(super) fn parse_process_terminate(
    data: &[u8],
    _header_process_id: u32,
) -> Option<ProcessEtwRecord> {
    let pid = PayloadCursor::new(data).u32_le()?;
    Some(ProcessEtwRecord {
        pid,
        ppid: None,
        session_id: None,
        unique_process_key: None,
        exit_status: None,
        image_file_name: None,
        command_line: None,
    })
}

pub(super) fn filetime_to_unix_millis(filetime: i64) -> Option<u64> {
    let unix_100ns = filetime.checked_sub(WINDOWS_EPOCH_DELTA_100NS)?;
    if unix_100ns < 0 {
        return None;
    }
    u64::try_from(unix_100ns).ok()?.checked_div(10_000)
}

#[cfg(test)]
mod tests {
    use super::*;

    const TEST_EXIT_STATUS: i32 = -5;

    fn push_pointer(data: &mut Vec<u8>, pointer_size: usize, value: u64) {
        match pointer_size {
            4 => data.extend((value as u32).to_le_bytes()),
            8 => data.extend(value.to_le_bytes()),
            _ => panic!("unsupported pointer size"),
        }
    }

    fn push_sid(data: &mut Vec<u8>, pointer_size: usize) {
        push_pointer(data, pointer_size, 0x1234_5678);
        data.extend(0_u32.to_le_bytes());
        if pointer_size == 8 {
            data.extend(0_u32.to_le_bytes());
        }
        data.extend([1, 1, 0, 0]);
        data.extend(5_u32.to_le_bytes());
        data.extend(18_u32.to_le_bytes());
    }

    fn push_utf16_string(data: &mut Vec<u8>, value: &str) {
        data.extend(
            value
                .encode_utf16()
                .chain(std::iter::once(0))
                .flat_map(u16::to_le_bytes),
        );
    }

    fn process_start_payload(version: u8, pointer_size: usize) -> Vec<u8> {
        process_start_payload_with_options(version, pointer_size, false, true)
    }

    fn process_start_payload_with_options(
        version: u8,
        pointer_size: usize,
        null_sid: bool,
        include_package_strings: bool,
    ) -> Vec<u8> {
        let mut data = Vec::new();
        if version == 0 {
            push_pointer(&mut data, pointer_size, 100);
            push_pointer(&mut data, pointer_size, 50);
        } else {
            if version == 1 {
                push_pointer(&mut data, pointer_size, 0x1111_2222);
            }
            if version >= 2 {
                push_pointer(
                    &mut data,
                    pointer_size,
                    if pointer_size == 4 {
                        0x89ab_cdef
                    } else {
                        0x1234_5678_9abc_def0
                    },
                );
            }
            data.extend(100_u32.to_le_bytes());
            data.extend(50_u32.to_le_bytes());
        }
        if version >= 1 {
            data.extend(2_u32.to_le_bytes());
            data.extend(TEST_EXIT_STATUS.to_le_bytes());
        }
        if version >= 3 {
            push_pointer(&mut data, pointer_size, 0xdead_beef);
        }
        if version >= 4 {
            data.extend(4_u32.to_le_bytes());
        }
        if null_sid {
            data.extend(0_u32.to_le_bytes());
        } else {
            push_sid(&mut data, pointer_size);
        }
        data.extend(b"target.exe\0");
        if version >= 2 {
            push_utf16_string(&mut data, "target.exe --run");
        }
        if version >= 4 && include_package_strings {
            push_utf16_string(&mut data, "Contoso.Target_1.0.0.0_x64__abc");
            push_utf16_string(&mut data, "Target.App");
        }
        data
    }

    #[test]
    fn filetime_conversion_uses_checked_epoch_arithmetic() {
        assert_eq!(filetime_to_unix_millis(WINDOWS_EPOCH_DELTA_100NS), Some(0));
        assert_eq!(
            filetime_to_unix_millis(WINDOWS_EPOCH_DELTA_100NS + 12_345 * 10_000),
            Some(12_345)
        );
        assert_eq!(filetime_to_unix_millis(WINDOWS_EPOCH_DELTA_100NS - 1), None);
        assert_eq!(filetime_to_unix_millis(i64::MIN), None);
    }

    #[test]
    fn parses_supported_process_start_versions() {
        for version in 0..=4 {
            let payload = process_start_payload(version, 8);
            let record = parse_process_start(&payload, version, 8).unwrap();
            assert_eq!(record.pid, 100, "version {version}");
            assert_eq!(record.ppid, Some(50), "version {version}");
            assert_eq!(
                record.session_id,
                (version >= 1).then_some(2),
                "version {version}"
            );
            assert_eq!(
                record.unique_process_key,
                (version >= 2).then_some(0x1234_5678_9abc_def0),
                "version {version}"
            );
            assert_eq!(
                record.exit_status,
                (version >= 1).then_some(TEST_EXIT_STATUS),
                "version {version}"
            );
            assert_eq!(
                record.image_file_name.as_deref(),
                Some("target.exe"),
                "version {version}"
            );
            assert_eq!(
                record.command_line.as_deref(),
                (version >= 2).then_some("target.exe --run"),
                "version {version}"
            );
        }
    }

    #[test]
    fn parses_v4_x86_process_start() {
        let payload = process_start_payload(4, 4);
        let record = parse_process_start(&payload, 4, 4).unwrap();
        assert_eq!(record.pid, 100);
        assert_eq!(record.ppid, Some(50));
        assert_eq!(record.session_id, Some(2));
        assert_eq!(record.unique_process_key, Some(0x89ab_cdef));
        assert_eq!(record.exit_status, Some(TEST_EXIT_STATUS));
        assert_eq!(record.image_file_name.as_deref(), Some("target.exe"));
        assert_eq!(record.command_line.as_deref(), Some("target.exe --run"));
    }

    #[test]
    fn parses_v4_null_sid_followed_by_required_strings() {
        for pointer_size in [4_usize, 8] {
            let payload = process_start_payload_with_options(4, pointer_size, true, true);
            let record = parse_process_start(&payload, 4, pointer_size).unwrap();
            assert_eq!(record.pid, 100);
            assert_eq!(record.session_id, Some(2));
            assert_eq!(record.exit_status, Some(TEST_EXIT_STATUS));
            assert_eq!(record.image_file_name.as_deref(), Some("target.exe"));
            assert_eq!(record.command_line.as_deref(), Some("target.exe --run"));
        }
    }

    #[test]
    fn v4_package_and_application_strings_are_optional() {
        let payload = process_start_payload_with_options(4, 8, false, false);
        let record = parse_process_start(&payload, 4, 8).unwrap();
        assert_eq!(record.image_file_name.as_deref(), Some("target.exe"));
        assert_eq!(record.command_line.as_deref(), Some("target.exe --run"));
    }

    #[test]
    fn rejects_unterminated_required_process_strings() {
        for pointer_size in [4_usize, 8] {
            for version in 1..=4 {
                let mut payload =
                    process_start_payload_with_options(version, pointer_size, false, false);
                payload.pop();
                assert!(
                    parse_process_start(&payload, version, pointer_size).is_none(),
                    "version {version}, pointer size {pointer_size}"
                );
            }
        }
    }

    #[test]
    fn rejects_truncated_process_start() {
        let payload = process_start_payload(4, 8);
        let truncated = &payload[..25];
        assert!(parse_process_start(truncated, 4, 8).is_none());
    }

    #[test]
    fn rejects_unknown_process_event_versions() {
        let payload = process_start_payload(4, 8);
        assert!(parse_process_start(&payload, 5, 8).is_none());
        assert!(parse_process_end(&payload, 5, 8).is_none());
    }

    #[test]
    fn parses_v1_through_v4_process_end_with_exit_status() {
        for pointer_size in [4_usize, 8] {
            for version in 1..=4 {
                let payload = process_start_payload(version, pointer_size);
                let record = parse_process_end(&payload, version, pointer_size).unwrap();
                let expected_key = (version >= 2).then_some(if pointer_size == 4 {
                    0x89ab_cdef
                } else {
                    0x1234_5678_9abc_def0
                });
                assert_eq!(record.pid, 100, "version {version}");
                assert_eq!(record.ppid, Some(50), "version {version}");
                assert_eq!(record.session_id, Some(2), "version {version}");
                assert_eq!(record.unique_process_key, expected_key, "version {version}");
                assert_eq!(
                    record.exit_status,
                    Some(TEST_EXIT_STATUS),
                    "version {version}"
                );
                assert_eq!(
                    record.image_file_name.as_deref(),
                    Some("target.exe"),
                    "version {version}"
                );
                assert_eq!(
                    record.command_line.as_deref(),
                    (version >= 2).then_some("target.exe --run"),
                    "version {version}"
                );
            }
        }
    }

    #[test]
    fn v0_process_end_has_no_exit_status() {
        let payload = process_start_payload(0, 8);
        let record = parse_process_end(&payload, 0, 8).unwrap();
        assert_eq!(record.pid, 100);
        assert_eq!(record.ppid, Some(50));
        assert_eq!(record.exit_status, None);
    }

    #[test]
    fn process_terminate_uses_payload_pid_instead_of_header_pid() {
        let record = parse_process_terminate(&42_u32.to_le_bytes(), 100).unwrap();
        assert_eq!(record.pid, 42);
        assert_eq!(record.ppid, None);
        assert_eq!(record.session_id, None);
        assert_eq!(record.unique_process_key, None);
        assert_eq!(record.exit_status, None);
        assert_eq!(record.image_file_name, None);
        assert_eq!(record.command_line, None);
        assert_eq!(parse_process_terminate(&[0, 1, 2], 100), None);
    }

    #[test]
    fn event_pointer_size_uses_event_header_architecture() {
        assert_eq!(
            event_pointer_size(EVENT_HEADER_FLAG_32_BIT_HEADER as u16),
            4
        );
        assert_eq!(
            event_pointer_size(EVENT_HEADER_FLAG_64_BIT_HEADER as u16),
            8
        );
        assert_eq!(event_pointer_size(0), size_of::<usize>());
    }

    #[test]
    fn event_names_preserve_rundown_semantics() {
        assert_eq!(
            EtwProcessPhase::from_opcode(EVENT_TRACE_TYPE_TERMINATE as u8),
            EtwProcessPhase::Terminate
        );
        assert_eq!(EtwProcessPhase::Start.event_name(), "EXEC");
        assert_eq!(EtwProcessPhase::DCStart.event_name(), "PROCESS_PRESENT");
        assert_eq!(EtwProcessPhase::End.event_name(), "EXIT");
        assert_eq!(
            EtwProcessPhase::DCEnd.event_name(),
            "PROCESS_PRESENT_AT_STOP"
        );
        assert_eq!(EtwProcessPhase::Terminate.event_name(), "EXIT");
        assert_eq!(EtwProcessPhase::Terminate.as_str(), "Terminate");
    }
}
