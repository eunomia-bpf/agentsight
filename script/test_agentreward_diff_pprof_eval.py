import importlib.util
import json
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).with_name("agentreward_diff_pprof_eval.py")
SPEC = importlib.util.spec_from_file_location("agentreward_diff_pprof_eval", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_canonical_task_groups_resized_visualwebarena_variants():
    assert MODULE.canonical_task_id("visualwebarena.resized.512") == "visualwebarena.512"
    assert MODULE.canonical_task_id("webarena.24") == "webarena.24"


def test_auc_uses_standard_tie_half_credit():
    assert MODULE.auc([True, False], [2.0, 1.0]) == 1.0
    assert MODULE.auc([True, False], [1.0, 1.0]) == 0.5
    assert MODULE.auc([True, False], [0.0, 1.0]) == 0.0


def test_stack_derivation_uses_visible_trace_fields_without_outcome_labels():
    action, args = MODULE.parse_action("fill('147', 'agent profiling')")
    assert action == "fill"
    assert args == ["147", "agent profiling"]
    step = {
        "url": "https://duckduckgo.com/",
        "axtree": "[147] combobox 'Search with DuckDuckGo', focused",
    }
    object_name = MODULE.action_object(action, args, step)
    assert object_name == "search: agent profiling"
    assert MODULE.strategy_for(action, "I need to find relevant work.", object_name) == "search"
    subtask = MODULE.purpose_phrase(
        "I need to find relevant work. I will search now.",
        "search",
        object_name,
        "",
    )
    assert subtask == "find relevant work"
    assert "success" not in subtask
    assert "loop" not in subtask


def test_repeat_signature_requires_exact_native_action_and_visible_state():
    first = MODULE.exact_action_state_signature(
        "click('101')", "https://example.com/list", "[101] button 'Upvote'"
    )
    same = MODULE.exact_action_state_signature(
        "click('101')", "https://example.com/list", "[101] button 'Upvote'"
    )
    different_target = MODULE.exact_action_state_signature(
        "click('202')", "https://example.com/list", "[202] button 'Upvote'"
    )
    changed_state = MODULE.exact_action_state_signature(
        "click('101')", "https://example.com/list", "[101] button 'Upvote', pressed"
    )
    assert first == same
    assert first != different_target
    assert first != changed_state


def test_load_annotated_trace_preserves_operations_tokens_and_evidence(tmp_path):
    trace = tmp_path / "trace.jsonl"
    nodes = [
        {
            "id": "session:s1",
            "parent": None,
            "kind": "session",
            "data": {"agent": "agent-a", "source_session": "s1"},
            "metrics": {},
            "path": ["repair regression"],
        },
        {
            "id": "prompt:s1",
            "parent": "session:s1",
            "kind": "prompt",
            "data": {"name": "user request"},
            "metrics": {},
            "path": ["repair regression", "reproduce issue"],
        },
        {
            "id": "llm:s1:0",
            "parent": "prompt:s1",
            "kind": "llm",
            "data": {"name": "step 22"},
            "metrics": {"tokens": 123},
            "path": ["repair regression", "reproduce issue", "run reproducer"],
        },
        {
            "id": "tool:s1:0",
            "parent": "llm:s1:0",
            "kind": "tool",
            "data": {"name": "bash", "evidence_id": "ev-1"},
            "metrics": {"operations": 1},
            "path": ["repair regression", "reproduce issue", "run reproducer"],
        },
    ]
    trace.write_text(
        "".join(json.dumps(node) + "\n" for node in nodes),
        encoding="utf-8",
    )

    projected, stack = MODULE.load_annotated_trace(trace)

    assert stack == "agent,operation_1,operation_2,operation_3,llm,tool"
    assert projected["s1"]["tokens"] == [
        {
            "value": 123,
            "fields": {
                "agent": "agent-a",
                "source_session": "s1",
                "source_kind": "llm",
                "evidence_id": "llm:s1:0",
                "operation_1": "repair regression",
                "operation_2": "reproduce issue",
                "operation_3": "run reproducer",
                "llm": "call",
            },
        }
    ]
    assert projected["s1"]["operations"] == [
        {
            "value": 1,
            "fields": {
                "agent": "agent-a",
                "source_session": "s1",
                "source_kind": "tool",
                "evidence_id": "ev-1",
                "operation_1": "repair regression",
                "operation_2": "reproduce issue",
                "operation_3": "run reproducer",
                "llm": "call",
                "tool": "bash",
            },
        }
    ]


def test_load_annotated_trace_rejects_duplicate_ids_and_unapplied_metric_nodes(tmp_path):
    duplicate = tmp_path / "duplicate.jsonl"
    root = {
        "id": "session:s1",
        "parent": None,
        "kind": "session",
        "data": {"source_session": "s1"},
        "metrics": {},
        "path": ["repair regression"],
    }
    duplicate.write_text(
        json.dumps(root) + "\n" + json.dumps(root) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="duplicate source node IDs"):
        MODULE.load_annotated_trace(duplicate)

    missing_path = tmp_path / "missing-path.jsonl"
    llm = {
        "id": "llm:s1:0",
        "parent": "session:s1",
        "kind": "llm",
        "data": {"name": "step 0"},
        "metrics": {"tokens": 10},
        "path": [],
    }
    missing_path.write_text(
        json.dumps(root) + "\n" + json.dumps(llm) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="has no applied operation path"):
        MODULE.load_annotated_trace(missing_path)


def test_apply_annotated_records_rejects_mass_mismatch():
    label = MODULE.Label(
        benchmark="bench",
        task_id="task",
        canonical_task="task",
        model="model",
        experiment="experiment",
        success=False,
        looping=None,
        source=Path("/unused"),
    )
    summary = MODULE.TraceSummary(
        label=label,
        goal="goal",
        operation_records=[],
        token_records=[],
        steps=2,
        tokens=20,
        errors=0,
        repeats=0,
        nonprogress=0,
        finished=False,
        evidence=[],
    )
    records = {
        "operations": [{"value": 1, "fields": {}}],
        "tokens": [{"value": 20, "fields": {}}],
    }
    with pytest.raises(RuntimeError, match="operation mass mismatch"):
        MODULE.apply_annotated_records(summary, records)

    records["operations"] = [{"value": 2, "fields": {}}]
    records["tokens"] = [{"value": 19, "fields": {}}]
    with pytest.raises(RuntimeError, match="token mass mismatch"):
        MODULE.apply_annotated_records(summary, records)
