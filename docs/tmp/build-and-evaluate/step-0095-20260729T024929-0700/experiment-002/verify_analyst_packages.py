#!/usr/bin/env python3
"""Independently verify the copied experiment-002 analyst evidence packages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import prepare_analyst_packages as adapter


EXPERIMENT = Path(__file__).resolve().parent
SOURCE_EXPERIMENT = EXPERIMENT.parent / "experiment-001"
PROFILE_NAME = "agentreward-338-pairs-bad-minus-good.operations.pb.gz"
PROFILE = EXPERIMENT / "analyst-packages" / "PROFILE" / PROFILE_NAME
RAW = EXPERIMENT / "analyst-packages" / "RAW-OPERATIONS" / "samples.jsonl"
SOURCE_RECORD = (
    EXPERIMENT
    / "source-records"
    / "experiment-001-preparation-report.json"
)
DEFAULT_REPORT = EXPERIMENT / "preparation-report.json"

EXPECTED_HASHES = {
    "prepare_analyst_packages.py": (
        "6c8c546fcd3876a707742ce16b837c75abf700772cc24bdbfb55223debadadce"
    ),
    "test_prepare_analyst_packages.py": (
        "8c70e4d88ef3f87336264196c117b4caa2356a0992626d56a9bd149fa5723f6d"
    ),
    "source-records/experiment-001-preparation-report.json": (
        "a964146917ba54ca75bfcf4546408e368be30d5ba008dd0d348bfd8eb9f24318"
    ),
    "analyst-packages/PROFILE/README.md": (
        "208a6debfc97ffae187e7996484b53374d800bd3840e95e8cf8a4ba3cc1ad52c"
    ),
    f"analyst-packages/PROFILE/{PROFILE_NAME}": (
        "0d6a7e80fbc805d374ad6bd4b668241584150a317049a45b4d0045f473b7495d"
    ),
    "analyst-packages/RAW-OPERATIONS/README.md": (
        "42b5c34b1ffea9b285eb8b8ebc4cd6431cafe35b9cff26a8383bc4bb7bfa7b70"
    ),
    "analyst-packages/RAW-OPERATIONS/samples.jsonl": (
        "127228f4c65b62f8c690dde0039ae210bbe68129cece03bd844f9e8022ef7519"
    ),
}
EXPECTED_TUPLE_COUNT = 11_146
EXPECTED_UNIQUE_TUPLE_COUNT = 7_229
EXPECTED_MASS = {
    "operations/count": {
        "positive": 7366,
        "negative": -3780,
        "negative_magnitude": 3780,
        "net": 3586,
        "absolute": 11146,
        "zero_sample_count": 0,
    }
}


class VerificationError(RuntimeError):
    """Raised when the copied evidence is not exactly the accepted evidence."""


def _assert_package_boundary() -> None:
    expected = {
        EXPERIMENT / "analyst-packages" / "PROFILE": {
            "README.md",
            PROFILE_NAME,
        },
        EXPERIMENT / "analyst-packages" / "RAW-OPERATIONS": {
            "README.md",
            "samples.jsonl",
        },
    }
    for directory, names in expected.items():
        if not directory.is_dir() or directory.is_symlink():
            raise VerificationError(f"invalid package directory: {directory}")
        actual = {entry.name for entry in directory.iterdir()}
        if actual != names:
            raise VerificationError(
                f"unexpected package contents in {directory}: {sorted(actual)}"
            )
        if any(entry.is_symlink() or not entry.is_file() for entry in directory.iterdir()):
            raise VerificationError(f"package contains a non-regular file: {directory}")


def verify_packages() -> dict[str, Any]:
    """Reparse both forms and compare exact tuple multisets and signed mass."""

    _assert_package_boundary()
    current_hashes: dict[str, str] = {}
    for relative, expected in EXPECTED_HASHES.items():
        path = EXPERIMENT / relative
        if not path.is_file() or path.is_symlink():
            raise VerificationError(f"missing or linked copied source: {relative}")
        actual = adapter.sha256_file(path)
        current_hashes[relative] = actual
        if actual != expected:
            raise VerificationError(
                f"copied source hash mismatch for {relative}: {actual}"
            )

    source_record = json.loads(SOURCE_RECORD.read_text(encoding="utf-8"))
    if source_record.get("status") != "PASS":
        raise VerificationError("copied experiment-001 preparation record is not PASS")
    if (
        source_record["tuple_equivalence"]["stock_raw_tuple_count"]
        != EXPECTED_TUPLE_COUNT
        or source_record["tuple_equivalence"]["stock_raw_unique_tuple_count"]
        != EXPECTED_UNIQUE_TUPLE_COUNT
        or source_record["mass_conservation"]["stock_raw"] != EXPECTED_MASS
    ):
        raise VerificationError("copied experiment-001 preparation semantics changed")

    raw_text, pprof_stderr = adapter.run_stock_pprof(PROFILE)
    profile_records = adapter.parse_stock_raw(raw_text)
    flat_records = adapter.read_jsonl(RAW)
    profile_multiset = adapter.tuple_multiset(profile_records)
    flat_multiset = adapter.tuple_multiset(flat_records)
    missing = profile_multiset - flat_multiset
    extra = flat_multiset - profile_multiset
    profile_mass = adapter.mass_inventory(profile_records)
    flat_mass = adapter.mass_inventory(flat_records)

    if (
        len(profile_records) != EXPECTED_TUPLE_COUNT
        or len(flat_records) != EXPECTED_TUPLE_COUNT
        or len(profile_multiset) != EXPECTED_UNIQUE_TUPLE_COUNT
        or len(flat_multiset) != EXPECTED_UNIQUE_TUPLE_COUNT
        or missing
        or extra
        or profile_mass != EXPECTED_MASS
        or flat_mass != EXPECTED_MASS
    ):
        raise VerificationError("PROFILE and RAW-OPERATIONS are not exactly identical")

    return {
        "schema": "agentsight.utility2.package-verification.v1",
        "status": "PASS",
        "source_experiment": str(SOURCE_EXPERIMENT.resolve()),
        "source_record": str(SOURCE_RECORD.resolve()),
        "copied_hashes": current_hashes,
        "tuple_equivalence": {
            "profile_tuple_count": len(profile_records),
            "raw_tuple_count": len(flat_records),
            "profile_unique_tuple_count": len(profile_multiset),
            "raw_unique_tuple_count": len(flat_multiset),
            "missing_tuple_count": sum(missing.values()),
            "extra_tuple_count": sum(extra.values()),
            "complete_multiset_equal": not missing and not extra,
        },
        "mass_conservation": {
            "profile": profile_mass,
            "raw": flat_mass,
            "equal": profile_mass == flat_mass,
        },
        "stock_pprof_stderr": pprof_stderr.strip(),
        "package_boundary": {
            "profile_files": ["README.md", PROFILE_NAME],
            "raw_files": ["README.md", "samples.jsonl"],
            "symlinks": 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    report = verify_packages()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
