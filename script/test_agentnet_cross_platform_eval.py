#!/usr/bin/env python3
"""Regression tests for the AgentNet cross-platform RQ2 experiment."""

from __future__ import annotations

from contextlib import redirect_stderr
import importlib.util
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np


SCRIPT_PATH = Path(__file__).with_name("agentnet_cross_platform_eval.py")
AGENTPPROF = SCRIPT_PATH.parent.parent / "agentpprof" / "target" / "release" / "agentpprof"
sys.path.insert(0, str(SCRIPT_PATH.parent))
SPEC = importlib.util.spec_from_file_location("agentnet_cross_platform_eval", SCRIPT_PATH)
assert SPEC is not None
agentnet = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(agentnet)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def visible_rows(platform: str, tasks: int = 4, steps: int = 4) -> list[dict]:
    rows: list[dict] = []
    actions = ("click", "type", "scroll", "click")
    phases = ("navigate", "input", "navigate", "navigate")
    for task in range(tasks):
        task_id = f"{platform}-task-{task}"
        previous = "start"
        for step in range(steps):
            action = actions[step]
            target = "text" if action == "type" else f"x{task}-y{step}"
            if task == 0 and step == 0:
                target = "backspace-_"
            rows.append(
                {
                    "operation_id": f"{task_id}:{step}",
                    "task_id": task_id,
                    "trajectory_id": task_id,
                    "platform": platform,
                    "dataset": "agentnet",
                    "session": task_id,
                    "system": platform,
                    "domain": "productivity" if task % 2 else "office",
                    "application": "writer" if platform == "darwin" else "notepad",
                    "action_code": f"pyautogui.{action}()",
                    "action": action,
                    "target": target,
                    "phase": phases[step],
                    "repeat_state": "single",
                    "repeat_signal": "none",
                    "repeat_run": "1",
                    "previous_action": previous,
                    "action_changed": "yes" if action != previous else "no",
                    "step_fraction": step / (steps - 1),
                    "log_trajectory_length": math.log1p(steps),
                }
            )
            previous = action
    return rows


def label_rows(rows: list[dict], invert: bool = False) -> list[dict]:
    result: list[dict] = []
    for row in rows:
        step = int(row["operation_id"].rsplit(":", 1)[1])
        positive = (step % 2 == 0) ^ invert
        result.append(
            {
                "operation_id": row["operation_id"],
                "task_id": row["task_id"],
                "trajectory_id": row["trajectory_id"],
                "platform": row["platform"],
                "correct": not positive,
                "redundant": positive,
            }
        )
    return result


class AgentNetCrossPlatformTests(unittest.TestCase):
    def test_truth_table(self) -> None:
        self.assertEqual(1, agentnet.label_value(False, False))
        self.assertEqual(1, agentnet.label_value(False, True))
        self.assertEqual(1, agentnet.label_value(True, True))
        self.assertEqual(0, agentnet.label_value(True, False))
        self.assertIsNone(agentnet.label_value(None, False))
        self.assertIsNone(agentnet.label_value(True, None))

    def test_complete_tie_block_metrics(self) -> None:
        metric = agentnet.metric_from_blocks(
            np.asarray([3.0, 1.0]), np.asarray([1.0, 1.0])
        )
        self.assertAlmostEqual(5.0 / 12.0, metric["average_precision"])
        self.assertEqual(0.0, metric["recall_at_30"])
        self.assertEqual(0.75, metric["work_to_50"])

    def test_agentprof_frame_encoding_trims_trailing_separator(self) -> None:
        self.assertEqual("backspace-", agentnet.agentprof_frame_value("backspace-_"))
        self.assertEqual("unknown", agentnet.agentprof_frame_value("_"))

    def test_prepare_projection_separates_forbidden_labels(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            raw = root / "raw.jsonl"
            out = root / "prepared"
            metadata = {
                "win": {
                    "task_id": "win",
                    "platform": "windows",
                    "source_domain": "Office",
                    "source_applications": ["Notepad"],
                    "domain": "office",
                    "application": "notepad",
                },
                "mac": {
                    "task_id": "mac",
                    "platform": "darwin",
                    "source_domain": "Office",
                    "source_applications": ["Writer"],
                    "domain": "office",
                    "application": "writer",
                },
            }
            raw_rows = []
            for task_id in ("win", "mac"):
                raw_rows.append(
                    {
                        "task_id": task_id,
                        "traj": [
                            {
                                "value": {
                                    "code": "pyautogui.click(10, 20)",
                                    "last_step_correct": False,
                                    "last_step_redundant": True,
                                    "reflection": "forbidden",
                                }
                            }
                        ],
                    }
                )
            write_jsonl(raw, raw_rows)

            with mock.patch.object(
                agentnet, "EXPECTED_TASKS", {"windows": 1, "darwin": 1}
            ):
                status = agentnet.projection_and_labels(raw, metadata, out)

            projection = read_jsonl(out / "projection.jsonl")
            windows_labels = read_jsonl(out / "labels" / "windows.jsonl")
            self.assertEqual({"windows": 1, "darwin": 1}, status["task_counts"])
            self.assertFalse(agentnet.FORBIDDEN_PROJECTION_FIELDS & set(projection[0]))
            self.assertNotIn("correct", projection[0])
            self.assertNotIn("redundant", projection[0])
            self.assertEqual("Office", projection[0]["source_domain"])
            self.assertEqual(False, windows_labels[0]["correct"])
            self.assertEqual(True, windows_labels[0]["redundant"])

    def test_projection_keeps_released_duplicate_trajectories_in_one_task(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            raw = root / "raw.jsonl"
            out = root / "prepared"
            metadata = {
                "win": {
                    "task_id": "win",
                    "platform": "windows",
                    "source_domain": "Office",
                    "source_applications": ["Notepad"],
                    "domain": "office",
                    "application": "notepad",
                },
                "mac": {
                    "task_id": "mac",
                    "platform": "darwin",
                    "source_domain": "Office",
                    "source_applications": ["Writer"],
                    "domain": "office",
                    "application": "writer",
                },
            }
            write_jsonl(
                raw,
                [
                    {
                        "task_id": "win",
                        "traj": [{"value": {"code": "pyautogui.click(10, 20)"}}],
                    },
                    {
                        "task_id": "mac",
                        "traj": [{"value": {"code": "pyautogui.click(30, 40)"}}],
                    },
                    {
                        "task_id": "win",
                        "traj": [{"value": {"code": "pyautogui.write('later')"}}],
                    },
                ],
            )
            with mock.patch.object(
                agentnet, "EXPECTED_TASKS", {"windows": 1, "darwin": 1}
            ):
                status = agentnet.projection_and_labels(raw, metadata, out)

            projection = read_jsonl(out / "projection.jsonl")
            windows = [row for row in projection if row["platform"] == "windows"]
            self.assertEqual({"windows": 1, "darwin": 1}, status["task_counts"])
            self.assertEqual({"windows": 2, "darwin": 1}, status["trajectory_counts"])
            self.assertEqual({"windows": 1, "darwin": 0}, status["repeated_task_counts"])
            self.assertEqual(2, len(windows))
            self.assertEqual({"win"}, {row["task_id"] for row in windows})
            self.assertEqual(2, len({row["trajectory_id"] for row in windows}))
            self.assertEqual(2, len({row["operation_id"] for row in windows}))
            self.assertEqual(2, len({row["session"] for row in windows}))

    def test_predictor_cli_has_no_target_label_input(self) -> None:
        parser = agentnet.build_parser()
        arguments = [
            "predict-fold",
            "--projection", "projection.jsonl",
            "--reference-label", "windows.jsonl",
            "--reference-platform", "windows",
            "--target-platform", "darwin",
            "--target-label", "darwin.jsonl",
            "--agentpprof-bin", "agentpprof",
            "--out", "out",
            "--attempts", "10",
            "--seed", "4204",
        ]
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(arguments)

    def test_full_cli_rejects_task_subset(self) -> None:
        parser = agentnet.build_parser()
        arguments = [
            "full",
            "--source", "source",
            "--agentpprof-bin", "agentpprof",
            "--out", "out",
            "--bootstraps", "10000",
            "--max-bootstrap-attempts", "50000",
            "--seed", "4204",
            "--tasks-per-platform", "4",
        ]
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parser.parse_args(arguments)

    def test_full_source_rejects_truncated_population(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            source = Path(raw_tmp)
            windows = visible_rows("windows", tasks=1)
            darwin = visible_rows("darwin", tasks=1)
            write_jsonl(source / "projection.jsonl", windows + darwin)
            write_jsonl(source / "labels" / "windows.jsonl", label_rows(windows))
            write_jsonl(source / "labels" / "darwin.jsonl", label_rows(darwin))
            (source / "prepare-status.json").write_text(
                json.dumps(
                    {"status": "VALID", "revision": agentnet.REVISION}, sort_keys=True
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(agentnet.ExperimentError, "expected 12364 tasks"):
                agentnet.validate_full_source(source)

    def test_full_rejects_noncontract_bootstrap_settings(self) -> None:
        arguments = SimpleNamespace(
            source=Path("source"),
            out=Path("out"),
            agentpprof_bin=AGENTPPROF,
            bootstraps=20,
            max_bootstrap_attempts=100,
            seed=1,
            jobs=1,
        )
        with self.assertRaisesRegex(agentnet.ExperimentError, "10000 valid draws"):
            agentnet.coordinator(arguments, "full")

    def test_agentprof_version_must_match_exactly(self) -> None:
        with mock.patch.object(
            agentnet.subprocess,
            "run",
            return_value=SimpleNamespace(stdout="agentpprof 0.2.38\n"),
        ):
            with self.assertRaisesRegex(agentnet.ExperimentError, "0.2.37"):
                agentnet.agentprof_version(Path("agentpprof"))

    @unittest.skipUnless(AGENTPPROF.is_file(), "release AgentProf binary is unavailable")
    def test_synthetic_preflight_uses_real_agentprof_and_preserves_label_blind_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            source = root / "source"
            out = root / "preflight"
            windows = visible_rows("windows")
            darwin = visible_rows("darwin")
            write_jsonl(source / "projection.jsonl", windows + darwin)
            write_jsonl(source / "labels" / "windows.jsonl", label_rows(windows))
            write_jsonl(source / "labels" / "darwin.jsonl", label_rows(darwin, invert=True))

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "preflight",
                    "--source", str(source),
                    "--agentpprof-bin", str(AGENTPPROF),
                    "--out", str(out),
                    "--bootstraps", "20",
                    "--max-bootstrap-attempts", "100",
                    "--seed", "4204",
                    "--jobs", "1",
                    "--tasks-per-platform", "4",
                ],
                check=True,
                text=True,
                capture_output=True,
            )
            status = json.loads(completed.stdout)

            self.assertEqual("VALID", status["status"])
            self.assertEqual("NOT_EVALUATED_PREFLIGHT", status["scientific_verdict"])
            self.assertFalse(status["tested_hypothesis_only"])
            self.assertFalse(status["cross_model_pooled_ranking"])
            for target, reference in (("windows", "darwin"), ("darwin", "windows")):
                fold = out / "folds" / f"{reference}-to-{target}"
                model = json.loads((fold / "model-report.json").read_text(encoding="utf-8"))
                before = json.loads(
                    (fold / "label-blind-digests.json").read_text(encoding="utf-8")
                )
                after = agentnet.fold_artifact_digests(fold)
                self.assertIsNone(model["target_label_input"])
                self.assertEqual(before, after)
                self.assertTrue(
                    status["label_boundary"][target]["unchanged_after_target_scoring"]
                )
                profile = json.loads(
                    (fold / "profile-report.json").read_text(encoding="utf-8")
                )
                self.assertEqual("agentpprof 0.2.37", profile["agentprof_version"])
                self.assertTrue(all(view["exact"] for view in profile["views"].values()))

            fold = out / "folds" / "windows-to-darwin"
            baseline_digests = agentnet.fold_artifact_digests(fold)
            alternate_labels = root / "alternate-darwin-labels.jsonl"
            write_jsonl(alternate_labels, label_rows(darwin, invert=False))
            alternate_score = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "score-fold",
                    "--fold-dir", str(fold),
                    "--target-label", str(alternate_labels),
                    "--out", str(root / "alternate-score"),
                    "--required-valid", "20",
                    "--jobs", "1",
                ],
                check=True,
                text=True,
                capture_output=True,
            )
            alternate_status = json.loads(alternate_score.stdout)
            self.assertIn("secondary_diagnostics", alternate_status)
            mass = alternate_status["secondary_diagnostics"][
                "additive_risk_mass_group_opening"
            ]["semantic"]
            self.assertEqual("mass", mass["ranking"])
            self.assertIn("groups_to_50_percent_positives", mass)
            self.assertNotIn("average_precision", mass)
            self.assertEqual(baseline_digests, agentnet.fold_artifact_digests(fold))

            for unavailable_label in (
                source / "labels" / "windows.jsonl",
                root / "withheld-target-label.jsonl",
            ):
                failed_score = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPT_PATH),
                        "score-fold",
                        "--fold-dir", str(fold),
                        "--target-label", str(unavailable_label),
                        "--out", str(root / f"failed-{unavailable_label.stem}"),
                        "--required-valid", "20",
                        "--jobs", "1",
                    ],
                    check=False,
                    text=True,
                    capture_output=True,
                )
                self.assertNotEqual(0, failed_score.returncode)
                self.assertEqual(baseline_digests, agentnet.fold_artifact_digests(fold))


if __name__ == "__main__":
    unittest.main()
