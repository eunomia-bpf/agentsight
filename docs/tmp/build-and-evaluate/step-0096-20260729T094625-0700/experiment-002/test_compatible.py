import unittest

from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
from types import SimpleNamespace
from tool_sandbox.common.execution_context import RoleType
from tool_sandbox.common.message_conversion import Message, to_openai_messages

from run_toolsandbox_compatible import (
    count_invalid_response_tool_call_ids,
    normalize_response_tool_call_ids,
    protocol_tool_call_id_mismatches,
    restore_protocol_tool_call_ids,
    safe_tool_call_id,
    safe_execution_python_code,
    system_first,
)


class CompatibleTest(unittest.TestCase):
    def test_system_messages_are_merged_first(self) -> None:
        messages = [
            {"role": "system", "content": "one"},
            {"role": "user", "content": "u"},
            {"role": "system", "content": "two"},
            {"role": "assistant", "content": "a"},
        ]
        result = system_first(messages)
        self.assertEqual(result[0], {"role": "system", "content": "one\n\ntwo"})
        self.assertEqual([row["role"] for row in result], ["system", "user", "assistant"])

    def test_no_system_preserves_order(self) -> None:
        messages = [
            {"role": "user", "content": "u"},
            {"role": "assistant", "content": "a"},
        ]
        self.assertEqual(system_first(messages), messages)

    def test_invalid_tool_call_id_is_replaced(self) -> None:
        self.assertEqual(safe_tool_call_id("valid_id_1"), "valid_id_1")
        normalized = safe_tool_call_id("0bad")
        self.assertTrue(normalized.startswith("call_"))
        self.assertEqual(normalized, safe_tool_call_id("0bad"))
        call = SimpleNamespace(id="0bad")
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=[call]))]
        )
        self.assertEqual(count_invalid_response_tool_call_ids(response), 1)
        self.assertEqual(normalize_response_tool_call_ids(response), 1)
        self.assertEqual(call.id, normalized)
        self.assertEqual(count_invalid_response_tool_call_ids(response), 0)

    def test_execution_variable_is_safe_but_protocol_id_can_be_restored(self) -> None:
        call = ChatCompletionMessageToolCall(
            id="5bad",
            type="function",
            function=Function(name="sample_tool", arguments='{"value": 1}'),
        )
        code = safe_execution_python_code(
            call,
            {"sample_tool"},
            "sample_tool",
            0,
        )
        compile(code, "<test>", "exec")
        self.assertNotIn("5bad_parameters", code)
        self.assertEqual(call.id, "5bad")
        restored = restore_protocol_tool_call_ids(
            [
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{"id": "call_safe_0", "function": {}}],
                },
                {"role": "tool", "tool_call_id": "5bad", "content": "result"},
            ]
        )
        self.assertEqual(restored[0]["tool_calls"][0]["id"], "5bad")
        self.assertEqual(protocol_tool_call_id_mismatches(restored), 0)

    def test_official_history_conversion_restores_opaque_protocol_id(self) -> None:
        call = ChatCompletionMessageToolCall(
            id="5bad",
            type="function",
            function=Function(name="sample_tool", arguments='{"value": 1}'),
        )
        code = safe_execution_python_code(
            call,
            {"sample_tool"},
            "sample_tool",
            0,
        )
        converted, _ = to_openai_messages(
            [
                Message(
                    sender=RoleType.USER,
                    recipient=RoleType.AGENT,
                    content="run it",
                ),
                Message(
                    sender=RoleType.AGENT,
                    recipient=RoleType.EXECUTION_ENVIRONMENT,
                    content=code,
                    openai_tool_call_id="5bad",
                    openai_function_name="sample_tool",
                ),
                Message(
                    sender=RoleType.EXECUTION_ENVIRONMENT,
                    recipient=RoleType.AGENT,
                    content="ok",
                    openai_tool_call_id="5bad",
                    openai_function_name="sample_tool",
                ),
            ]
        )
        self.assertNotEqual(converted[1]["tool_calls"][0]["id"], "5bad")
        restored = restore_protocol_tool_call_ids(converted)
        self.assertEqual(restored[1]["tool_calls"][0]["id"], "5bad")
        self.assertEqual(restored[2]["tool_call_id"], "5bad")
        self.assertEqual(protocol_tool_call_id_mismatches(restored), 0)


if __name__ == "__main__":
    unittest.main()
