#!/usr/bin/env python3
"""Focused deterministic tests for analyst-package preparation."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import prepare_analyst_packages as prep


class PrepareAnalystPackagesTests(unittest.TestCase):
    def test_stock_parser_preserves_signed_duplicate_tuples(self) -> None:
        raw = """PeriodType:
Period: 0
Samples:
operations/count
          1: 1 2
                arm:[bad] evidence_id:[e-1]
         -1: 3 2
                arm:[good] evidence_id:[e-2]
          1: 1 2
                arm:[bad] evidence_id:[e-1]
Locations
     1: 0x0 M=1 result:repeat agentpprof:0 s=0
     2: 0x0 M=1 task:example agentpprof:0 s=0
     3: 0x0 M=1 result:finish agentpprof:0 s=0
Mappings
1: 0x0/0x0/0x0
"""
        records = prep.parse_stock_raw(raw)
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0]["stack_frames"], ["result:repeat", "task:example"])
        self.assertEqual(records[1]["value"], -1)
        self.assertEqual(records[1]["labels"]["evidence_id"], ["e-2"])
        multiset = prep.tuple_multiset(records)
        self.assertEqual(multiset[prep.tuple_key(records[0])], 2)
        self.assertEqual(
            prep.mass_inventory(records)["operations/count"],
            {
                "positive": 2,
                "negative": -1,
                "negative_magnitude": 1,
                "net": 1,
                "absolute": 3,
                "zero_sample_count": 0,
            },
        )

    def test_fixed_profile_end_to_end_is_lossless_and_isolated(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".package-test-", dir=prep.SCRIPT_DIR) as tmp:
            tmp_path = Path(tmp)
            output_root = tmp_path / "packages"
            report_path = tmp_path / "preparation-report.json"
            report = prep.prepare_packages(
                prep.DEFAULT_SOURCE,
                output_root,
                report_path,
            )

            self.assertEqual(report["status"], "PASS")
            self.assertTrue(
                report["tuple_equivalence"]["complete_multiset_equal"]
            )
            self.assertTrue(report["mass_conservation"]["equal"])
            self.assertTrue(report["sha256_checks"]["profile_copy_equal"])
            self.assertEqual(
                {path.name for path in (output_root / prep.PROFILE_DIRNAME).iterdir()},
                {prep.DEFAULT_SOURCE.name, "README.md"},
            )
            self.assertEqual(
                {path.name for path in (output_root / prep.RAW_DIRNAME).iterdir()},
                {prep.RAW_FILENAME, "README.md"},
            )

            first_line = (
                output_root / prep.RAW_DIRNAME / prep.RAW_FILENAME
            ).read_text(encoding="utf-8").splitlines()[0]
            self.assertEqual(
                set(json.loads(first_line)),
                {"sample_type", "unit", "value", "stack_frames", "labels"},
            )
            raw_readme = (
                output_root / prep.RAW_DIRNAME / "README.md"
            ).read_text(encoding="utf-8")
            self.assertNotIn(str(prep.DEFAULT_SOURCE), raw_readme)

    def test_package_generation_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory(prefix=".determinism-test-", dir=prep.SCRIPT_DIR) as tmp:
            tmp_path = Path(tmp)
            output_root = tmp_path / "packages"
            first = prep.prepare_packages(
                prep.DEFAULT_SOURCE,
                output_root,
                tmp_path / "report-1.json",
            )
            second = prep.prepare_packages(
                prep.DEFAULT_SOURCE,
                output_root,
                tmp_path / "report-2.json",
            )
            self.assertEqual(
                first["sha256_checks"]["raw_jsonl"],
                second["sha256_checks"]["raw_jsonl"],
            )
            self.assertEqual(first["field_inventory"], second["field_inventory"])


if __name__ == "__main__":
    unittest.main()
