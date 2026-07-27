#!/usr/bin/env python3
"""Freeze the repaired final-HEAD path-local anchor used by RQ6."""

from __future__ import annotations

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / "agentvis" / "research"))

import freeze_rq6_local_anchor  # noqa: E402


freeze_rq6_local_anchor.EXPECTED_INPUT_SHA256 = (
    "372584e828f1f46b8ae68b5381fcf90042a28397383f8adfa74ec3f638268ab0"
)


if __name__ == "__main__":
    freeze_rq6_local_anchor.main()
