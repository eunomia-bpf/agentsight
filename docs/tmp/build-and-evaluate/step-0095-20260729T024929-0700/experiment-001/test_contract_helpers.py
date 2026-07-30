from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ContractHelperTests(unittest.TestCase):
    def test_analyst_order_is_balanced_and_deterministic(self) -> None:
        module = load("run_analysts")
        first = module.registered_runs()
        second = module.registered_runs()
        self.assertEqual(first, second)
        self.assertEqual(len(first), 6)
        self.assertEqual(sum(x["arm"] == "PROFILE" for x in first), 3)
        self.assertEqual(sum(x["arm"] == "RAW-OPERATIONS" for x in first), 3)

    def test_prompt_differs_only_by_format_hint(self) -> None:
        module = load("run_analysts")
        profile = module.prompt_for("PROFILE")
        raw = module.prompt_for("RAW-OPERATIONS")
        self.assertIn(module.COMMON_TASK, profile)
        self.assertIn(module.COMMON_TASK, raw)
        self.assertNotEqual(profile, raw)
        self.assertNotIn("ToolSandbox", profile)
        self.assertNotIn("ToolSandbox", raw)

    def test_manifest_constants(self) -> None:
        module = load("prepare_episode_manifest")
        self.assertEqual(len(module.TRIAL_SEEDS), 8)
        self.assertEqual(len(module.CONDITIONS), 3)
        self.assertEqual(module.SAMPLING["temperature"], 0.2)

    def test_gate_rejects_nonpass(self) -> None:
        module = load("run_analysts")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "verification.json"
            path.write_text(
                json.dumps({"status": "FAIL", "stage": "analyst"}),
                encoding="utf-8",
            )
            with self.assertRaises(RuntimeError):
                module.verify_execution_gate(path)

    def test_frozen_commands_match_dynamic_commands(self) -> None:
        module = load("run_analysts")
        if not (module.ANALYST_DIR / "commands.json").is_file():
            module.prepare()
        for run in module.registered_runs():
            self.assertEqual(
                module.command_for(run),
                module.frozen_command_for(run["run_id"]),
            )

    def test_frozen_order_rejects_skipping_and_accepts_terminal_predecessor(self) -> None:
        module = load("run_analysts")
        with tempfile.TemporaryDirectory() as directory:
            analyst_dir = Path(directory)
            order = {"runs": [
                {"run_id": "first", "position": 1},
                {"run_id": "second", "position": 2},
            ]}
            (analyst_dir / "order.json").write_text(
                json.dumps(order), encoding="utf-8"
            )
            with self.assertRaises(RuntimeError):
                module.enforce_frozen_order("second", analyst_dir)
            first = analyst_dir / "runs" / "first"
            first.mkdir(parents=True)
            (first / "run.json").write_text(
                json.dumps({"status": "ok"}), encoding="utf-8"
            )
            module.enforce_frozen_order("second", analyst_dir)

    def test_event_summary_and_usage_totals(self) -> None:
        module = load("run_analysts")
        event = {
            "type": "item.completed",
            "item": {"type": "command_execution"},
            "usage": {"input_tokens": 10},
        }
        self.assertEqual(
            module.event_summary(event),
            ("item.completed", {"input_tokens": 10}, "command_execution"),
        )
        self.assertEqual(
            module.sum_numeric_dicts(
                [{"input_tokens": 10}, {"input_tokens": 2, "output_tokens": 3}]
            ),
            {"input_tokens": 12, "output_tokens": 3},
        )


if __name__ == "__main__":
    unittest.main()
