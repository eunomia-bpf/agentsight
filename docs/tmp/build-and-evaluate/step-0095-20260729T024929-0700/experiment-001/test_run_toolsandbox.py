"""Focused unit tests; no official scenario is played and no API is contacted."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path
from types import SimpleNamespace

from openai import NOT_GIVEN

import inventory_toolsandbox
from run_toolsandbox import (
    POLICY_SEPARATOR,
    LocalInstrumentedAgent,
    LocalInstrumentedUser,
    SamplingConfig,
    append_policy_to_system_input,
    derive_request_seed,
)


class FakeCompletions:
    def __init__(self, response: object | None = None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


class FakeClient:
    def __init__(self, completions: FakeCompletions):
        self.chat = SimpleNamespace(completions=completions)


def fake_response(tool_calls: int = 0) -> object:
    calls = [
        SimpleNamespace(
            id=f"call-{index}",
            function=SimpleNamespace(name="fake", arguments="{}"),
        )
        for index in range(tool_calls)
    ]
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=calls or None))],
        usage=SimpleNamespace(
            prompt_tokens=11,
            completion_tokens=7,
            total_tokens=18,
        ),
    )


class InstrumentationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sampling = SamplingConfig(
            temperature=0.0,
            top_p=1.0,
            max_tokens=128,
        )

    def test_policy_is_appended_to_copy_of_first_system_input(self) -> None:
        messages = [
            {"role": "system", "content": "official"},
            {"role": "user", "content": "hello"},
        ]
        original = copy.deepcopy(messages)
        modified = append_policy_to_system_input(messages, "Avoid duplicate calls.")
        self.assertEqual(messages, original)
        self.assertEqual(
            modified[0]["content"],
            "official" + POLICY_SEPARATOR + "Avoid duplicate calls.",
        )

    def test_agent_records_seed_sampling_usage_and_tool_calls(self) -> None:
        completions = FakeCompletions(fake_response(tool_calls=2))
        agent = LocalInstrumentedAgent(
            model_name="fake-model",
            base_url="http://invalid.local/v1",
            trial_seed=17,
            sampling=self.sampling,
            policy="Avoid duplicate calls.",
            client=FakeClient(completions),
        )
        messages = [{"role": "system", "content": "official"}]
        agent.model_inference(messages, NOT_GIVEN)

        self.assertEqual(len(completions.calls), 1)
        request = completions.calls[0]
        self.assertEqual(request["seed"], derive_request_seed(17, "agent", 0))
        self.assertEqual(request["temperature"], 0.0)
        self.assertEqual(request["top_p"], 1.0)
        self.assertEqual(request["max_tokens"], 128)
        self.assertEqual(messages, [{"role": "system", "content": "official"}])

        telemetry = agent.telemetry()
        self.assertEqual(telemetry["model_calls"], 1)
        self.assertEqual(telemetry["tool_calls"], 2)
        self.assertEqual(telemetry["usage"]["prompt_tokens"], 11)
        self.assertEqual(telemetry["usage"]["completion_tokens"], 7)
        self.assertEqual(telemetry["usage"]["total_tokens"], 18)
        self.assertEqual(telemetry["requests"][0]["status"], "ok")

    def test_user_has_separate_seed_and_never_receives_policy(self) -> None:
        completions = FakeCompletions(fake_response())
        user = LocalInstrumentedUser(
            model_name="fake-model",
            base_url="http://invalid.local/v1",
            trial_seed=17,
            sampling=self.sampling,
            client=FakeClient(completions),
        )
        messages = [{"role": "system", "content": "official user prompt"}]
        user.model_inference(messages, NOT_GIVEN)
        request = completions.calls[0]
        self.assertEqual(request["messages"], messages)
        self.assertNotIn(POLICY_SEPARATOR, request["messages"][0]["content"])
        self.assertEqual(request["seed"], derive_request_seed(17, "user", 0))
        self.assertNotEqual(
            request["seed"],
            derive_request_seed(17, "agent", 0),
        )

    def test_agent_exception_is_recorded_and_reraised(self) -> None:
        completions = FakeCompletions(error=ValueError("fake failure"))
        agent = LocalInstrumentedAgent(
            model_name="fake-model",
            base_url="http://invalid.local/v1",
            trial_seed=3,
            sampling=self.sampling,
            policy=None,
            client=FakeClient(completions),
        )
        with self.assertRaisesRegex(ValueError, "fake failure"):
            agent.model_inference(
                [{"role": "system", "content": "official"}],
                NOT_GIVEN,
            )
        telemetry = agent.telemetry()
        self.assertEqual(telemetry["model_calls"], 1)
        self.assertEqual(telemetry["requests"][0]["status"], "exception")
        self.assertEqual(
            telemetry["requests"][0]["exception"]["type"],
            "ValueError",
        )


class InventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.inventory = inventory_toolsandbox.build_inventory(
            inventory_toolsandbox.default_checkout()
        )

    def test_dependency_screen_is_37_to_32_without_outcomes(self) -> None:
        self.assertEqual(
            self.inventory["counts"],
            {
                "declared": 37,
                "offline": 32,
                "requires_rapidapi": 5,
                "outcome_after_preflight_removal": 31,
            },
        )
        self.assertFalse(self.inventory["screen"]["uses_outcomes"])
        self.assertEqual(
            self.inventory["rapidapi_scenarios"],
            [
                "convert_currency",
                "find_address_with_lat_lon",
                "find_current_city_low_battery_mode",
                "find_stock_symbol_with_company_name",
                "find_stock_symbol_with_company_name_low_battery_mode",
            ],
        )

    def test_holiday_tools_are_local_and_evaluator_mapping_is_official(self) -> None:
        rows = {row["name"]: row for row in self.inventory["scenarios"]}
        for name in (
            "find_days_till_holiday",
            "find_days_till_holiday_wifi_off",
            "find_thanksgiving_timestamp",
        ):
            self.assertEqual(rows[name]["availability"], "offline")
            search_holiday = [
                dependency
                for dependency in rows[name]["declared_tools"]
                if dependency["tool"] == "search_holiday"
            ]
            self.assertEqual(
                search_holiday[0]["module"],
                "tool_sandbox.tools.utilities",
            )
        mapping = self.inventory["evaluator_mapping"]
        self.assertEqual(
            mapping["entrypoint"],
            "tool_sandbox.common.scenario.Scenario.play_and_evaluate",
        )
        self.assertEqual(
            mapping["evaluator"],
            "tool_sandbox.common.evaluation.Evaluation.evaluate",
        )


if __name__ == "__main__":
    unittest.main()
