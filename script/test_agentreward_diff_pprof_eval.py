import importlib.util
import sys
from pathlib import Path


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
