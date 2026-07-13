#!/usr/bin/env python3
"""Focused offline tests for the approved HINTBench RQ2 adapter."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).with_name("hintbench_profile_localization_eval.py")
SPEC = importlib.util.spec_from_file_location("hintbench_profile_localization_eval", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot import {SCRIPT}")
hint = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = hint
SPEC.loader.exec_module(hint)


def visible_record(
    split: str = "validation",
    record_id: str = "0",
    task_id: str = "demoDomain_task_0001",
) -> dict:
    trajectory = [
        {"role": "system", "content": "profile"},
        {"role": "user", "content": "do it"},
        {
            "role": "agent",
            "thought": "act",
            "action": json.dumps({"name": "send_mail", "arguments": {"x": 1}}),
        },
        {"role": "environment", "content": '{"ok": false, "error": "timeout"}'},
        {"role": "agent", "content": "done"},
    ]
    display_ids = list(range(len(trajectory)))
    if split == "test":
        for item, step_id in zip(trajectory, display_ids, strict=True):
            item["step_id"] = step_id
    return {
        "split": split,
        "source_index": int(record_id),
        "record_id": record_id,
        "record_key": f"{split}:{record_id}",
        "task_id": task_id,
        "released_environment": None,
        "environment_present": False,
        "trajectory": trajectory,
        "display_ids": display_ids,
    }


def localizer_row(record: dict, steps: list[int]) -> dict:
    return {
        "record_key": record["record_key"],
        "mapped_predicted_steps": steps,
    }


class HintBenchAdapterTests(unittest.TestCase):
    def test_prompt_preserves_official_rendering_with_newline_step_prefix(self) -> None:
        record = visible_record()
        prompt = hint.prompt_for_record(record)
        self.assertIn("[STEP_ID=0]\n=== Agent Profile ===\nprofile\n", prompt)
        self.assertIn("[STEP_ID=1]\n[USER]: do it", prompt)
        self.assertIn("[STEP_ID=2]\n[AGENT]:\n[THOUGHT]: act", prompt)
        self.assertIn("[STEP_ID=3]\n[ENVIRONMENT]:", prompt)
        self.assertNotIn("is_risky", prompt)
        payload = hint.chat_request_payload(record, "model.gguf")
        self.assertEqual(payload["max_tokens"], 1024)
        self.assertEqual(payload["chat_template_kwargs"], {"enable_thinking": False})
        self.assertEqual(payload["reasoning_format"], "none")
        schema = hint.RESPONSE_SCHEMA
        self.assertEqual(schema["required"], ["verdict", "risks"])
        self.assertFalse(schema["additionalProperties"])
        self.assertNotIn("minItems", schema["properties"]["risks"])
        self.assertEqual(payload["grammar"], hint.RESPONSE_GBNF)
        self.assertNotIn("response_format", payload)
        for risk_name in hint.RISK_NAMES_11:
            self.assertIn(json.dumps(json.dumps(risk_name)), payload["grammar"])
        self.assertIn('integer ::= "-"? ("0" | [1-9] [0-9]*)', payload["grammar"])

    def test_official_style_response_normalization(self) -> None:
        verdict, risks, status = hint.parse_response(
            'prefix {"verdict":"unsafe","risks":[{"risk_name":"invalid tool call",'
            '"risk_steps":[4,4,2]}]} suffix'
        )
        self.assertEqual(verdict, "unsafe")
        self.assertEqual(status, "ok_unsafe")
        self.assertEqual(
            risks,
            [{"risk_name": "Invalid Tool Calls", "risk_steps": [2, 4]}],
        )
        self.assertEqual(hint.parse_response('{"verdict":"safe","risks":[{}]}')[1], [])
        self.assertEqual(hint.parse_response("not json"), ("error", [], "invalid_json"))

    def test_exact_field_derivation_and_hex_roundtrip(self) -> None:
        record = visible_record(task_id="döm_ain_task_0001")
        operations = hint.derive_operations([record], [localizer_row(record, [2, 99])])
        self.assertEqual(len(operations), 5)
        self.assertEqual(operations[0]["raw_fields"]["environment"], "döm_ain")
        self.assertEqual(operations[2]["raw_fields"]["phase"], "act")
        self.assertEqual(operations[2]["raw_fields"]["action"], "send_mail")
        self.assertEqual(operations[3]["raw_fields"]["action"], "send_mail")
        self.assertEqual(operations[4]["raw_fields"]["action"], "send_mail")
        self.assertEqual(operations[3]["raw_fields"]["status"], "error")
        self.assertEqual(operations[4]["raw_fields"]["status"], "error")
        self.assertEqual([row["localizer_hit"] for row in operations], [0, 0, 1, 0, 0])
        report = hint.verify_hex_roundtrip(operations)
        self.assertTrue(report["one_to_one"])
        encoded = hint.hex_encode("Döm;X")
        self.assertEqual(encoded, encoded.lower())
        self.assertEqual(hint.hex_decode(encoded), "Döm;X")

    def test_status_error_precedence_and_json_boundary(self) -> None:
        self.assertEqual(hint.classify_status('{"success":true,"error":"bad"}'), "error")
        self.assertEqual(hint.classify_status("Operation TIMED_OUT"), "error")
        self.assertEqual(hint.classify_status('{"status":"updated"}'), "success")
        self.assertEqual(hint.classify_status('"success"'), "unknown")

    def test_real_agentprof_count_shift_prefix_and_flat_identity(self) -> None:
        binary = SCRIPT.parents[1] / "agentpprof" / "target" / "release" / "agentpprof"
        if not binary.is_file():
            self.skipTest("release AgentProf binary is unavailable")
        first = visible_record(record_id="0")
        second = visible_record(record_id="1", task_id="other_task_0002")
        operations = hint.derive_operations(
            [first, second],
            [localizer_row(first, [2]), localizer_row(second, [3])],
        )
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            count, shifted = hint.write_operation_artifacts("validation", operations, out)
            candidate = hint.construct_profile_candidate(
                "validation",
                operations,
                count,
                shifted,
                binary,
                hint.STACK_FIELDS,
                out,
            )
            self.assertTrue(candidate["count_conservation_exact"])
            self.assertTrue(candidate["hit_conservation_exact"])
            self.assertTrue(candidate["flat_identity_scores_exact"])
            self.assertEqual(candidate["operations"], 10)

    def test_complete_equal_score_tier_is_indivisible(self) -> None:
        risky = visible_record(record_id="0")
        safe = visible_record(record_id="1")
        risky_operations = hint.derive_operations(
            [risky], [localizer_row(risky, [2])]
        )
        safe_operations = hint.derive_operations(
            [safe], [localizer_row(safe, [2])]
        )
        operations = [*risky_operations, *safe_operations]
        targets = hint.TargetBundle(
            "validation",
            {"validation:0": frozenset({2}), "validation:1": frozenset()},
            frozenset({"validation:0"}),
            frozenset({"validation:1"}),
            {"validation:0": frozenset({2}), "validation:1": frozenset()},
            (),
        )
        metric = hint.evaluate_units(
            "independent",
            operations,
            hint.independent_step_units(operations),
            targets,
        )
        self.assertTrue(metric["reached_80_macro_recall"])
        # Both predicted-hit steps share the same score and must be consumed.
        self.assertEqual(metric["selected"]["work_count"], 2)
        self.assertEqual(metric["selected"]["safe_work"], 1)

    def test_terminal_cache_requires_exact_request_and_prompt_usage(self) -> None:
        record = visible_record()
        payload = hint.chat_request_payload(record, "model")
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            hint.write_jsonl(
                out / "prompts" / "tokenization.jsonl",
                [{"split": "validation", "record_key": "validation:0", "prompt_tokens": 37}],
            )
            response = {
                "choices": [{"message": {"content": '{"verdict":"safe","risks":[]}'}}],
                "usage": {"prompt_tokens": 37},
            }
            with mock.patch.object(hint, "_post_json", return_value=response) as post:
                rows = hint.collect_localizer_outputs(
                    "validation", [record], "http://localhost/v1", "model", out,
                    False, 1.0, 1,
                )
            self.assertEqual(post.call_count, 1)
            self.assertEqual(rows[0]["request_body"], payload)
            self.assertEqual(rows[0]["response_schema"], hint.RESPONSE_SCHEMA)
            self.assertTrue(rows[0]["prompt_tokenization_exact"])
            with mock.patch.object(hint, "_post_json") as post:
                resumed = hint.collect_localizer_outputs(
                    "validation", [record], "http://localhost/v1", "model", out,
                    True, 1.0, 1,
                )
            post.assert_not_called()
            self.assertEqual(resumed[0]["request_sha256"], rows[0]["request_sha256"])

    def test_protocol_failure_retries_but_prompt_usage_mismatch_does_not(self) -> None:
        record = visible_record()
        good = {
            "choices": [{"message": {"content": '{"verdict":"safe","risks":[]}'}}],
            "usage": {"prompt_tokens": 19},
        }
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            hint.write_jsonl(
                out / "prompts" / "tokenization.jsonl",
                [{"split": "validation", "record_key": "validation:0", "prompt_tokens": 19}],
            )
            with mock.patch.object(hint, "_post_json", side_effect=[{"bad": True}, good]) as post:
                rows = hint.collect_localizer_outputs(
                    "validation", [record], "http://localhost/v1", "model", out,
                    False, 1.0, 2,
                )
            self.assertEqual(post.call_count, 2)
            self.assertEqual(rows[0]["transport_attempts"], 2)

        mismatched = {
            "choices": [{"message": {"content": '{"verdict":"safe","risks":[]}'}}],
            "usage": {"prompt_tokens": 20},
        }
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            hint.write_jsonl(
                out / "prompts" / "tokenization.jsonl",
                [{"split": "validation", "record_key": "validation:0", "prompt_tokens": 19}],
            )
            with mock.patch.object(hint, "_post_json", return_value=mismatched) as post:
                with self.assertRaises(hint.ExperimentError):
                    hint.collect_localizer_outputs(
                        "validation", [record], "http://localhost/v1", "model", out,
                        False, 1.0, 3,
                    )
            self.assertEqual(post.call_count, 1)

    def test_server_context_must_match_both_primary_surfaces(self) -> None:
        models = {"data": [{"meta": {"n_ctx": 32768}}]}
        props = {"default_generation_settings": {"n_ctx": 32768}}
        self.assertTrue(hint.validate_server_context(models, props)["exact"])
        with self.assertRaises(hint.ExperimentError):
            hint.validate_server_context(models, {"default_generation_settings": {"n_ctx": 8192}})

    def test_one_bootstrap_replicate_preserves_strata_and_identity(self) -> None:
        operations = []
        targets_by_record = {}
        risky = set()
        safe = set()
        mappable = {}
        for index in range(536):
            key = f"test:{index}"
            is_risky = index < 400
            if is_risky:
                risky.add(key)
                targets_by_record[key] = frozenset({0})
                mappable[key] = frozenset({0})
            else:
                safe.add(key)
                targets_by_record[key] = frozenset()
                mappable[key] = frozenset()
            raw_fields = {
                "environment": f"env{index % 7}",
                "phase": "act",
                "action": f"action{index % 5}",
                "status": "error" if index % 3 == 0 else "unknown",
            }
            encoded_fields = {field: hint.hex_encode(value) for field, value in raw_fields.items()}
            operations.append(
                {
                    "operation_id": f"{key}:0",
                    "record_key": key,
                    "display_id": 0,
                    "ordinal": 0,
                    "localizer_hit": 1 if index % 4 == 0 else 0,
                    "raw_fields": raw_fields,
                    "encoded_fields": encoded_fields,
                }
            )
        target_bundle = hint.TargetBundle(
            "test", targets_by_record, frozenset(risky), frozenset(safe), mappable, ()
        )
        leaves = [hint.stack_key(row, hint.STACK_FIELDS) for row in operations]
        candidate = {"order": list(hint.STACK_FIELDS), "operation_leaves": leaves}
        state = hint.prepare_bootstrap_state(operations, candidate, target_bundle)
        hint._BOOTSTRAP_STATE = state
        hint._BOOTSTRAP_SEED = 20260713
        row = hint._bootstrap_attempt(0)
        self.assertTrue(row["flat_identity_exact"])
        self.assertEqual(row["methods"]["agentprof"], row["methods"]["flat_exact"])
        self.assertEqual(set(row["paired_deltas"]), set(hint.MAIN_BASELINES))


if __name__ == "__main__":
    unittest.main()
