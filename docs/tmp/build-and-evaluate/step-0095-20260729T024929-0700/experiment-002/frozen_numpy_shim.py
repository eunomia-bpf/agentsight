#!/usr/bin/env python3
"""Pure-stdlib NumPy subset for the frozen experiment-002 analyzer."""

from __future__ import annotations

from array import array
import builtins
import math
import struct
import sys
from typing import Any, Iterable


EXPECTED_SEED = 2026072903
EXPECTED_SHAPE = (100_000, 20)
EXPECTED_LOW = 0
EXPECTED_HIGH = 20
float64 = float
int64 = int
_indices: "Array | None" = None


class Array:
    def __init__(
        self,
        values: Iterable[Any] | array,
        *,
        shape: tuple[int, ...] | None = None,
        raw_little_endian_int64: bytes | None = None,
    ):
        self._values = (
            values if isinstance(values, array) else list(values)
        )
        self._shape = shape or (len(self._values),)
        self._raw_little_endian_int64 = raw_little_endian_int64

    @property
    def ndim(self) -> int:
        return len(self._shape)

    @property
    def size(self) -> int:
        result = 1
        for dimension in self._shape:
            result *= dimension
        return result

    @property
    def shape(self) -> tuple[int, ...]:
        return self._shape

    def __len__(self) -> int:
        return self._shape[0]

    def __iter__(self):
        if self.ndim != 1:
            raise TypeError("iteration is supported only for one-dimensional arrays")
        return iter(self._values)

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, Array):
            if self.ndim != 1 or key.shape != EXPECTED_SHAPE:
                raise ValueError("frozen indexed gather shape changed")
            return GatheredRows(self, key)
        if self.ndim == 1:
            return self._values[key]
        if isinstance(key, int):
            width = self._shape[1]
            start = key * width
            return list(self._values[start : start + width])
        raise TypeError("unsupported frozen array index")

    def _binary(self, other: Any, operation) -> "Array":
        if isinstance(other, Array):
            if self.shape != other.shape or self.ndim != 1:
                raise ValueError("array shape mismatch")
            return Array(
                operation(left, right)
                for left, right in zip(self._values, other._values)
            )
        if self.ndim != 1:
            raise ValueError("scalar operation requires a one-dimensional array")
        return Array(operation(value, other) for value in self._values)

    def __truediv__(self, other: Any) -> "Array":
        return self._binary(other, lambda left, right: left / right)

    def __le__(self, other: Any) -> "Array":
        return self._binary(other, lambda left, right: left <= right)

    def astype(self, dtype: Any, copy: bool = True) -> "Array":
        if dtype not in (int, int64, "<i8"):
            raise ValueError("only frozen little-endian int64 conversion is allowed")
        if not copy:
            return self
        return Array(
            (int(value) for value in self._values),
            shape=self.shape,
            raw_little_endian_int64=self._raw_little_endian_int64,
        )

    def tobytes(self, order: str = "C") -> bytes:
        if order != "C" or self.shape != EXPECTED_SHAPE:
            raise ValueError("only the frozen C-order index bytes are available")
        if self._raw_little_endian_int64 is not None:
            return self._raw_little_endian_int64
        return b"".join(struct.pack("<q", int(value)) for value in self._values)


class GatheredRows:
    def __init__(self, source: Array, indices: Array):
        self.source = source
        self.indices = indices
        self.shape = indices.shape


class PCG64:
    def __init__(self, seed: int):
        if seed != EXPECTED_SEED:
            raise ValueError("PCG64 seed differs from the frozen plan")
        self.seed = seed


class Generator:
    def __init__(self, bit_generator: PCG64):
        if not isinstance(bit_generator, PCG64):
            raise TypeError("only the frozen PCG64 descriptor is allowed")
        self.bit_generator = bit_generator

    def integers(
        self,
        low: int,
        high: int,
        *,
        size: tuple[int, int],
        dtype: Any,
    ) -> Array:
        if (
            low != EXPECTED_LOW
            or high != EXPECTED_HIGH
            or size != EXPECTED_SHAPE
            or dtype not in (int64, int)
            or _indices is None
        ):
            raise ValueError("bootstrap draw differs from the frozen artifact")
        return _indices


class _RandomNamespace:
    Generator = Generator
    PCG64 = PCG64


random = _RandomNamespace()
ndarray = Array


def configure_indices(payload: bytes) -> None:
    global _indices
    expected_size = EXPECTED_SHAPE[0] * EXPECTED_SHAPE[1] * 8
    if len(payload) != expected_size:
        raise ValueError("frozen bootstrap-index byte count changed")
    values = array("q")
    values.frombytes(payload)
    if sys.byteorder != "little":
        values.byteswap()
    if len(values) != EXPECTED_SHAPE[0] * EXPECTED_SHAPE[1]:
        raise ValueError("frozen bootstrap-index shape changed")
    if any(value < EXPECTED_LOW or value >= EXPECTED_HIGH for value in values):
        raise ValueError("frozen bootstrap index is out of range")
    _indices = Array(
        values,
        shape=EXPECTED_SHAPE,
        raw_little_endian_int64=payload,
    )


def asarray(values: Any, dtype: Any = None) -> Array:
    if isinstance(values, Array):
        return values
    converted = list(values)
    if dtype in (float, float64):
        converted = [float(value) for value in converted]
    return Array(converted)


def isfinite(values: Array) -> Array:
    return Array(math.isfinite(float(value)) for value in values)


def all(values: Array) -> bool:
    return builtins.all(bool(value) for value in values)


def any(values: Array) -> bool:
    return builtins.any(bool(value) for value in values)


def sort(values: Array, kind: str = "stable") -> Array:
    if values.ndim != 1 or kind != "stable":
        raise ValueError("only stable one-dimensional sort is allowed")
    return Array(sorted(values))


def median(values: Any, axis: int | None = None) -> Any:
    if isinstance(values, GatheredRows):
        if axis != 1:
            raise ValueError("frozen gathered rows require axis=1")
        width = values.indices.shape[1]
        result = []
        for row_index in range(values.indices.shape[0]):
            positions = values.indices[row_index]
            row = sorted(values.source[position] for position in positions)
            middle = width // 2
            result.append((row[middle - 1] + row[middle]) / 2.0)
        return Array(result)
    if axis is not None:
        raise ValueError("axis is unsupported for one-dimensional median")
    data = sorted(float(value) for value in values)
    if not data:
        raise ValueError("median requires data")
    middle = len(data) // 2
    return (
        data[middle]
        if len(data) % 2
        else (data[middle - 1] + data[middle]) / 2.0
    )


def mean(values: Array) -> float:
    data = [float(value) for value in values]
    if not data:
        raise ValueError("mean requires data")
    return sum(data) / len(data)


def log(values: Array) -> Array:
    return Array(math.log(float(value)) for value in values)


def exp(value: float) -> float:
    return math.exp(float(value))
