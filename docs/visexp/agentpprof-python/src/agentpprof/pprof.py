from __future__ import annotations

import gzip
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path


def _varint(value: int) -> bytes:
    if value < 0:
        value += 1 << 64
    out = bytearray()
    while value >= 0x80:
        out.append((value & 0x7F) | 0x80)
        value >>= 7
    out.append(value)
    return bytes(out)


def _key(field_number: int, wire_type: int) -> bytes:
    return _varint((field_number << 3) | wire_type)


def _int(field_number: int, value: int) -> bytes:
    return _key(field_number, 0) + _varint(value)


def _bool(field_number: int, value: bool) -> bytes:
    return _int(field_number, 1 if value else 0)


def _msg(field_number: int, payload: bytes) -> bytes:
    return _key(field_number, 2) + _varint(len(payload)) + payload


def _str(field_number: int, value: str) -> bytes:
    data = value.encode("utf-8", errors="replace")
    return _key(field_number, 2) + _varint(len(data)) + data


def _value_type(type_idx: int, unit_idx: int) -> bytes:
    return _int(1, type_idx) + _int(2, unit_idx)


def _function(function_id: int, name_idx: int, filename_idx: int) -> bytes:
    return (
        _int(1, function_id)
        + _int(2, name_idx)
        + _int(3, name_idx)
        + _int(4, filename_idx)
    )


def _line(function_id: int, line: int = 1) -> bytes:
    return _int(1, function_id) + _int(2, line)


def _location(location_id: int, function_id: int) -> bytes:
    return _int(1, location_id) + _msg(4, _line(function_id)) + _bool(5, True)


def _label(key_idx: int, str_idx: int | None = None, num: int | None = None, unit_idx: int | None = None) -> bytes:
    payload = _int(1, key_idx)
    if str_idx is not None:
        payload += _int(2, str_idx)
    if num is not None:
        payload += _int(3, num)
    if unit_idx is not None:
        payload += _int(4, unit_idx)
    return payload


def _sample(location_ids: list[int], value: int, labels: dict[str, str]) -> bytes:
    payload = b"".join(_int(1, location_id) for location_id in location_ids)
    payload += _int(2, value)
    for key, val in sorted(labels.items()):
        payload += _msg(3, _label(int(key), int(val)))
    return payload


@dataclass(frozen=True)
class SemanticSample:
    stack: tuple[str, ...]
    value: int
    labels: tuple[tuple[str, str], ...] = ()


@dataclass
class PprofProfile:
    sample_type: str
    sample_unit: str
    comments: list[str] = field(default_factory=list)
    _strings: list[str] = field(default_factory=lambda: [""])
    _string_ids: dict[str, int] = field(default_factory=lambda: {"": 0})
    _function_ids: dict[str, int] = field(default_factory=dict)
    _location_ids: dict[str, int] = field(default_factory=dict)
    _samples: dict[tuple[tuple[str, ...], tuple[tuple[str, str], ...]], int] = field(default_factory=lambda: defaultdict(int))

    def intern(self, value: str) -> int:
        if value not in self._string_ids:
            self._string_ids[value] = len(self._strings)
            self._strings.append(value)
        return self._string_ids[value]

    def add_sample(self, stack: list[str] | tuple[str, ...], value: int, labels: dict[str, str] | None = None) -> None:
        if value <= 0 or not stack:
            return
        clean_stack = tuple(frame or "unknown" for frame in stack)
        clean_labels = tuple(sorted((labels or {}).items()))
        self._samples[(clean_stack, clean_labels)] += int(value)

    def _function_id(self, frame: str) -> int:
        if frame not in self._function_ids:
            self._function_ids[frame] = len(self._function_ids) + 1
        return self._function_ids[frame]

    def _location_id(self, frame: str) -> int:
        if frame not in self._location_ids:
            self._location_ids[frame] = len(self._location_ids) + 1
            self._function_id(frame)
        return self._location_ids[frame]

    def to_bytes(self) -> bytes:
        filename_idx = self.intern("agentpprof://semantic-profile")
        sample_type = _value_type(self.intern(self.sample_type), self.intern(self.sample_unit))
        encoded_samples: list[bytes] = []
        label_string_ids: dict[tuple[str, str], tuple[int, int]] = {}
        for (stack, labels), value in sorted(self._samples.items()):
            # pprof stores leaf first; our logical stacks are root first.
            location_ids = [self._location_id(frame) for frame in reversed(stack)]
            label_indices: dict[str, str] = {}
            for key, val in labels:
                pair = (key, val)
                if pair not in label_string_ids:
                    label_string_ids[pair] = (self.intern(key), self.intern(val))
                key_idx, val_idx = label_string_ids[pair]
                label_indices[str(key_idx)] = str(val_idx)
            encoded_samples.append(_msg(2, _sample(location_ids, value, label_indices)))

        # Ensure all frame strings are interned before writing string_table.
        for frame in self._function_ids:
            self.intern(frame)
        for comment in self.comments:
            self.intern(comment)

        payload = _msg(1, sample_type)
        payload += b"".join(encoded_samples)
        for frame, function_id in sorted(self._function_ids.items(), key=lambda item: item[1]):
            payload += _msg(5, _function(function_id, self.intern(frame), filename_idx))
        for frame, location_id in sorted(self._location_ids.items(), key=lambda item: item[1]):
            payload += _msg(4, _location(location_id, self._function_id(frame)))
        for text in self._strings:
            payload += _str(6, text)
        payload += _int(9, int(time.time_ns()))
        for comment in self.comments:
            payload += _int(13, self._string_ids[comment])
        return gzip.compress(payload)

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.to_bytes())


def write_pprof(
    path: Path,
    sample_type: str,
    sample_unit: str,
    samples: list[SemanticSample],
    comments: list[str] | None = None,
) -> None:
    profile = PprofProfile(sample_type=sample_type, sample_unit=sample_unit, comments=comments or [])
    for sample in samples:
        profile.add_sample(list(sample.stack), sample.value, dict(sample.labels))
    profile.write(path)
