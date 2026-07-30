import json
import unittest

from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)
from tool_sandbox.common.execution_context import ExecutionContext
from tool_sandbox.common.message_conversion import (
    openai_tool_call_to_python_code,
)

import replay_converter_mechanism as replay
from run_toolsandbox_compatible import safe_execution_python_code


class ConverterReplayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rows = replay.load_profile_rows()
        cls.fields = rows[0]["fields"]
        cls.context_path = replay.episode_context_path(
            cls.fields["source_session"], cls.fields["scenario"]
        )
        cls.serialized = json.loads(cls.context_path.read_text(encoding="utf-8"))
        cls.agent_row = next(
            row
            for row in cls.serialized["_dbs"]["SANDBOX"]
            if row.get("sender") == "AGENT"
            and row.get("recipient") == "EXECUTION_ENVIRONMENT"
            and row.get("openai_function_name")
        )
        cls.call_record = replay.conversation_calls(cls.context_path)[0]

    def test_trim_retains_operation_but_excludes_recorded_response(self) -> None:
        operation_index = int(self.agent_row["sandbox_message_index"])
        trimmed = replay.trim_serialized_context(
            self.serialized, operation_index
        )
        sandbox = trimmed["_dbs"]["SANDBOX"]
        self.assertTrue(
            any(
                row.get("openai_tool_call_id")
                == self.agent_row["openai_tool_call_id"]
                and row.get("sender") == "AGENT"
                for row in sandbox
            )
        )
        self.assertFalse(
            any(
                row.get("openai_tool_call_id")
                == self.agent_row["openai_tool_call_id"]
                and row.get("sender") == "EXECUTION_ENVIRONMENT"
                for row in sandbox
            )
        )
        for rows in trimmed["_dbs"].values():
            self.assertTrue(
                all(int(row["sandbox_message_index"]) <= operation_index for row in rows)
            )

    def test_current_converter_changes_only_internal_code_id(self) -> None:
        call = ChatCompletionMessageToolCall(**self.call_record["call"])
        operation_index = int(self.agent_row["sandbox_message_index"])
        context = ExecutionContext.from_dict(
            replay.trim_serialized_context(self.serialized, operation_index)
        )
        names = set(context.get_available_tools(scrambling_allowed=True))
        execution_name = context.get_execution_facing_tool_name(call.function.name)
        before = openai_tool_call_to_python_code(
            call,
            names,
            execution_facing_tool_name=execution_name,
        )
        after = safe_execution_python_code(
            call,
            names,
            execution_name,
            self.call_record["call_index"],
        )
        self.assertEqual(before, self.agent_row["content"])
        with self.assertRaises(SyntaxError):
            compile(before, "<before>", "exec")
        compile(after, "<after>", "exec")
        self.assertEqual(call.id, self.agent_row["openai_tool_call_id"])
        self.assertNotIn(f"{call.id}_parameters", after)

    def test_profile_population_is_exactly_5_invalid_and_16_valid(self) -> None:
        rows = replay.load_profile_rows()
        classes = [row["fields"]["call_id"] for row in rows]
        self.assertEqual(len(classes), 21)
        self.assertEqual(classes.count("invalid"), 5)
        self.assertEqual(classes.count("valid"), 16)


if __name__ == "__main__":
    unittest.main()
