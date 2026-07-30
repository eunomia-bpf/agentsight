#!/usr/bin/env python3
"""Focused tests for the fail-closed blinded review-bundle builder."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest

import prepare_review_bundle as bundle
import run_analysts


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def make_writable(root: Path) -> None:
    if not root.exists():
        return
    for path in root.rglob("*"):
        if path.is_dir():
            os.chmod(path, 0o755)
        elif path.is_file():
            os.chmod(path, 0o644)
    os.chmod(root, 0o755)


class PrepareReviewBundleTests(unittest.TestCase):
    def fixture(
        self,
        root: Path,
        *,
        omit_final_for_last: bool = False,
        last_status: str = "ok",
    ) -> tuple[Path, dict[str, Path], Path]:
        analyst = root / "analyst"
        rows = run_analysts.registered_runs()
        write_json(analyst / "order.json", {"runs": rows})
        write_json(
            analyst / "review-alias-map.private.json",
            run_analysts.review_alias_assignment(rows),
        )
        aliases = run_analysts.review_alias_assignment(rows)
        case_by_run = {
            case["run_id"]: case["case_id"] for case in aliases["cases"]
        }
        write_json(
            analyst / "review-output.schema.json",
            run_analysts.review_output_schema(
                [
                    case["case_id"]
                    for case in run_analysts.review_alias_assignment(rows)[
                        "cases"
                    ]
                ]
            ),
        )
        packages = {
            "PROFILE": root / "packages" / "profile",
            "RAW-OPERATIONS": root / "packages" / "raw",
        }
        for arm, package in packages.items():
            package.mkdir(parents=True)
            (package / "README.md").write_text(
                f"neutral {arm} instructions", encoding="utf-8"
            )
            (package / ("evidence.pb.gz" if arm == "PROFILE" else "samples.jsonl")).write_bytes(
                f"evidence-{arm}".encode("utf-8")
            )
        for index, row in enumerate(rows):
            run_dir = analyst / "runs" / row["run_id"]
            other_arm = (
                "RAW-OPERATIONS"
                if row["arm"] == "PROFILE"
                else "PROFILE"
            )
            other_row = rows[(index + 1) % len(rows)]
            write_json(
                run_dir / "run.json",
                {
                    "status": (
                        last_status if index == len(rows) - 1 else "ok"
                    ),
                    "run": {
                        "run_id": row["run_id"],
                        "arm": row["arm"],
                    },
                    "actual_tool_commands": [
                        {
                            "event_index": 3,
                            "type": "command_execution",
                            "command": (
                                f"cd {packages[row['arm']].resolve()} && "
                                "jq -s length samples.jsonl && "
                                f"ls {packages[other_arm].resolve()} && "
                                "curl https://private.example/v1 && "
                                f"echo {row['run_id']} {other_row['run_id']} "
                                f"{row['block_id']} {other_row['block_id']} "
                                f"{case_by_run[row['run_id']]} "
                                f"{case_by_run[other_row['run_id']]} "
                                "localhost:18185 127.0.0.1:9000 "
                                "../order.json "
                                f"{(analyst / 'runs' / row['run_id']).resolve()} "
                                "review-alias-map.private.json"
                            ),
                        },
                        {
                            "event_index": 4,
                            "type": "mcp_tool_call",
                            "command": None,
                        },
                    ],
                    "wall_seconds": 12.5,
                    "provider_usage_totals": {
                        "input_tokens": 100,
                        "output_tokens": 10,
                    },
                },
            )
            if not (omit_final_for_last and index == len(rows) - 1):
                write_json(
                    run_dir / "final.json",
                    {
                        "diagnosis": (
                            f"one behavior {row['run_id']} {row['block_id']} "
                            f"{case_by_run[row['run_id']]} localhost:18185 "
                            "../order.json "
                            f"{(analyst / 'runs' / row['run_id']).resolve()}"
                        ),
                        "quantitative_evidence": [
                            {
                                "command": "jq -s length samples.jsonl",
                                "finding": "40",
                            }
                        ],
                        "policy_text": "Observe before retrying.",
                        "expected_mechanism": "Avoids repetition.",
                    },
                )
        return analyst, packages, root / "review-bundle"

    def test_refuses_incomplete_runs_without_creating_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            analyst, packages, output = self.fixture(
                Path(directory), omit_final_for_last=True
            )
            with self.assertRaises(bundle.BundleError):
                bundle.build_bundle(output, analyst, packages)
            self.assertFalse(output.exists())

    def test_builds_40_opaque_read_only_cases_and_strips_private_metadata(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            analyst, packages, output = self.fixture(Path(directory))
            try:
                result = bundle.build_bundle(output, analyst, packages)
                self.assertEqual(result["status"], "PASS")
                self.assertEqual(result["case_count"], 40)
                manifest = json.loads(
                    (output / "manifest.json").read_text(encoding="utf-8")
                )
                self.assertEqual(len(manifest["cases"]), 40)
                self.assertEqual(
                    manifest["decision_schema_path"],
                    "review-output.schema.json",
                )
                self.assertEqual(
                    set(manifest["files"]),
                    {"review-output.schema.json"},
                )
                self.assertEqual(
                    set(path.name for path in output.iterdir()),
                    {"cases", "manifest.json", "review-output.schema.json"},
                )
                self.assertEqual(
                    bundle.sha256_file(output / "review-output.schema.json"),
                    manifest["files"]["review-output.schema.json"],
                )
                self.assertFalse(
                    (output / "review-output.schema.json").stat().st_mode
                    & 0o222
                )
                self.assertNotIn("run_id", json.dumps(manifest))
                for case in manifest["cases"]:
                    self.assertEqual(
                        set(case), {"case_id", "path", "files"}
                    )
                    case_dir = output / case["path"]
                    self.assertFalse(case_dir.stat().st_mode & 0o222)
                    execution = json.loads(
                        (case_dir / "execution.json").read_text(encoding="utf-8")
                    )
                    output_document = json.loads(
                        (case_dir / "output.json").read_text(encoding="utf-8")
                    )
                    self.assertEqual(
                        set(execution), {"schema", "tool_calls"}
                    )
                    self.assertEqual(
                        execution["tool_calls"][0],
                        {
                            "type": "command_execution",
                            "literal": (
                                "cd $EVIDENCE && jq -s length samples.jsonl "
                                "&& ls $OUTSIDE_EVIDENCE_PACKAGE && "
                                "curl $ENDPOINT && echo $RUN_ID $RUN_ID "
                                "$BLOCK_ID $BLOCK_ID $CASE_ID $OTHER_CASE_ID "
                                "$ENDPOINT $ENDPOINT "
                                "$OUTSIDE_SCHEDULE_METADATA "
                                "$OUTSIDE_PATH "
                                "$OUTSIDE_SCHEDULE_METADATA"
                            ),
                        },
                    )
                    self.assertEqual(
                        execution["tool_calls"][1],
                        {"type": "mcp_tool_call"},
                    )
                    serialized = json.dumps(execution)
                    for forbidden in (
                        "run_id",
                        "wall_seconds",
                        "input_tokens",
                        "arm_rank",
                        "block_id",
                        str(packages["PROFILE"].resolve()),
                        str(packages["RAW-OPERATIONS"].resolve()),
                    ):
                        self.assertNotIn(forbidden, serialized)
                    for private_id in {
                        row["run_id"]
                        for row in run_analysts.registered_runs()
                    } | {
                        row["block_id"]
                        for row in run_analysts.registered_runs()
                    }:
                        self.assertNotIn(private_id, serialized)
                    self.assertNotIn("localhost", serialized)
                    self.assertNotIn("127.0.0.1", serialized)
                    self.assertNotIn("../order.json", serialized)
                    self.assertNotIn(
                        "review-alias-map.private.json", serialized
                    )
                    output_serialized = json.dumps(output_document)
                    self.assertIn("$RUN_ID", output_serialized)
                    self.assertIn("$BLOCK_ID", output_serialized)
                    self.assertIn("$CASE_ID", output_serialized)
                    self.assertIn("$ENDPOINT", output_serialized)
                    self.assertIn(
                        "$OUTSIDE_SCHEDULE_METADATA", output_serialized
                    )
                    self.assertNotIn("../order.json", output_serialized)
                    self.assertNotIn(str(analyst.resolve()), output_serialized)
                    for alias in json.loads(
                        (
                            analyst / "review-alias-map.private.json"
                        ).read_text(encoding="utf-8")
                    )["cases"]:
                        self.assertNotIn(
                            alias["case_id"], output_serialized
                        )
                with self.assertRaises(bundle.BundleError):
                    bundle.build_bundle(output, analyst, packages)
            finally:
                make_writable(output)

    def test_terminal_failure_without_final_gets_blind_failure_marker(
        self,
    ) -> None:
        for status in ("failed", "timeout"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                analyst, packages, output = self.fixture(
                    Path(directory),
                    omit_final_for_last=True,
                    last_status=status,
                )
                try:
                    result = bundle.build_bundle(output, analyst, packages)
                    self.assertEqual(result["status"], "PASS")
                    aliases = json.loads(
                        (analyst / "review-alias-map.private.json").read_text(
                            encoding="utf-8"
                        )
                    )
                    last_run = run_analysts.registered_runs()[-1]["run_id"]
                    case_id = next(
                        case["case_id"]
                        for case in aliases["cases"]
                        if case["run_id"] == last_run
                    )
                    marker = json.loads(
                        (
                            output / "cases" / case_id / "output.json"
                        ).read_text(encoding="utf-8")
                    )
                    self.assertEqual(
                        marker,
                        {
                            "schema": (
                                "agentsight.utility2.blind-output-unavailable.v1"
                            ),
                            "output_available": False,
                            "terminal_without_final": True,
                        },
                    )
                    serialized = json.dumps(marker)
                    self.assertNotIn(status, serialized)
                    self.assertNotIn("run_id", serialized)
                finally:
                    make_writable(output)

    def test_terminal_failure_with_leaky_residual_final_still_gets_marker(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            analyst, packages, output = self.fixture(
                Path(directory), last_status="failed"
            )
            rows = run_analysts.registered_runs()
            last_run = rows[-1]["run_id"]
            residual = analyst / "runs" / last_run / "final.json"
            residual.write_text(
                json.dumps(
                    {
                        "run_id": last_run,
                        "private": str(analyst / "review-alias-map.private.json"),
                    }
                ),
                encoding="utf-8",
            )
            try:
                bundle.build_bundle(output, analyst, packages)
                aliases = json.loads(
                    (analyst / "review-alias-map.private.json").read_text(
                        encoding="utf-8"
                    )
                )
                case_id = next(
                    case["case_id"]
                    for case in aliases["cases"]
                    if case["run_id"] == last_run
                )
                marker = json.loads(
                    (output / "cases" / case_id / "output.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(marker, bundle.UNAVAILABLE_OUTPUT)
                self.assertNotIn(last_run, json.dumps(marker))
            finally:
                make_writable(output)

    def test_ok_final_rejects_extra_or_nested_forbidden_keys(self) -> None:
        for mutation in ("top-level", "nested", "policy-over-60"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                analyst, packages, output = self.fixture(Path(directory))
                run_id = run_analysts.registered_runs()[0]["run_id"]
                final_path = analyst / "runs" / run_id / "final.json"
                document = json.loads(final_path.read_text(encoding="utf-8"))
                if mutation == "top-level":
                    document["run_id"] = run_id
                else:
                    if mutation == "nested":
                        document["quantitative_evidence"][0]["usage"] = {
                            "input_tokens": 1
                        }
                    else:
                        document["policy_text"] = "word " * 61
                final_path.write_text(json.dumps(document), encoding="utf-8")
                with self.assertRaises(bundle.BundleError):
                    bundle.build_bundle(output, analyst, packages)
                self.assertFalse(output.exists())

    def test_verify_rejects_shape_tamper_even_if_manifest_hash_is_updated(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            analyst, packages, output = self.fixture(Path(directory))
            try:
                bundle.build_bundle(output, analyst, packages)
                manifest_path = output / "manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                first_case = manifest["cases"][0]
                output_path = (
                    output / first_case["path"] / "output.json"
                )
                os.chmod(output, 0o755)
                os.chmod(output / "cases", 0o755)
                os.chmod(output / first_case["path"], 0o755)
                os.chmod(output_path, 0o644)
                tampered = {
                    "diagnosis": "valid-looking",
                    "quantitative_evidence": [
                        {
                            "command": "jq . evidence/samples.jsonl",
                            "finding": "one",
                            "run_id": "hidden",
                        }
                    ],
                    "policy_text": "Observe before retrying.",
                    "expected_mechanism": "Avoids retries.",
                }
                output_path.write_text(json.dumps(tampered), encoding="utf-8")
                first_case["files"]["output.json"] = bundle.sha256_file(
                    output_path
                )
                os.chmod(manifest_path, 0o644)
                manifest_path.write_text(
                    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                os.chmod(output_path, 0o444)
                os.chmod(manifest_path, 0o444)
                os.chmod(output / first_case["path"], 0o555)
                os.chmod(output / "cases", 0o555)
                os.chmod(output, 0o555)
                aliases = json.loads(
                    (analyst / "review-alias-map.private.json").read_text(
                        encoding="utf-8"
                    )
                )
                with self.assertRaises(bundle.BundleError):
                    bundle.verify_bundle(
                        output,
                        {case["case_id"] for case in aliases["cases"]},
                    )
            finally:
                make_writable(output)

    def test_manifest_hash_verification_detects_corruption(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            analyst, packages, output = self.fixture(Path(directory))
            try:
                bundle.build_bundle(output, analyst, packages)
                aliases = json.loads(
                    (analyst / "review-alias-map.private.json").read_text(
                        encoding="utf-8"
                    )
                )
                case_ids = {case["case_id"] for case in aliases["cases"]}
                first = output / "cases" / next(iter(case_ids)) / "output.json"
                os.chmod(first, 0o644)
                first.write_text("{}", encoding="utf-8")
                with self.assertRaises(bundle.BundleError):
                    bundle.verify_bundle(output, case_ids)
            finally:
                make_writable(output)

    def test_rejects_nonbijective_alias_map(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            analyst, packages, output = self.fixture(Path(directory))
            aliases_path = analyst / "review-alias-map.private.json"
            aliases = json.loads(aliases_path.read_text(encoding="utf-8"))
            aliases["cases"][1]["run_id"] = aliases["cases"][0]["run_id"]
            write_json(aliases_path, aliases)
            with self.assertRaises(bundle.BundleError):
                bundle.build_bundle(output, analyst, packages)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
