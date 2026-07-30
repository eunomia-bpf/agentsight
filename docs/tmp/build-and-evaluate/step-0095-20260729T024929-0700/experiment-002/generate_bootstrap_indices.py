#!/usr/bin/env python3
"""Generate the preregistered PCG64 bootstrap-index artifact only."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path

import numpy as np


SEED = 2026072903
SHAPE = (100_000, 20)


def generate(output: Path) -> dict[str, object]:
    if output.exists() or output.is_symlink():
        raise RuntimeError("refusing to overwrite bootstrap-index artifact")
    indices = np.random.Generator(np.random.PCG64(SEED)).integers(
        0, 20, size=SHAPE, dtype=np.int64
    )
    payload = indices.astype("<i8", copy=False).tobytes(order="C")
    descriptor = os.open(
        output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444
    )
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    return {
        "status": "PASS",
        "seed": SEED,
        "shape": list(SHAPE),
        "dtype": "little-endian-int64",
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "analysis_inputs_read": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(generate(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
