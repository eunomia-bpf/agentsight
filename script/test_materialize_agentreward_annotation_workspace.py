import importlib.util
import json
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("materialize_agentreward_annotation_workspace.py")
SPEC = importlib.util.spec_from_file_location(
    "materialize_agentreward_annotation_workspace", SCRIPT
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_materializer_uses_cleaned_source_without_expert_annotation(tmp_path):
    dataset = tmp_path / "dataset"
    source = (
        dataset
        / "cleaned"
        / "webarena"
        / "model-a"
        / "experiment-a"
        / "webarena.1.json"
    )
    source.parent.mkdir(parents=True)
    source.write_text(
        json.dumps(
            {
                "goal": "Post the requested comment.",
                "summary_info": {
                    "trajectory_success": "Successful",
                    "trajectory_looping": "No",
                },
                "steps": [
                    {
                        "reasoning": "I need to open the discussion.",
                        "action": "click('17')",
                        "url": "https://example.test/discussion",
                        "axtree": "[17] link Discussion",
                        "last_action_error": "",
                        "stats": {"input_tokens": 11, "output_tokens": 7},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    session = MODULE.source_session_id("webarena", "webarena.1", "model-a")

    nodes, annotations, summary = MODULE.materialize(dataset, [session])

    assert summary == {
        "sessions": 1,
        "operations": 1,
        "tokens": 18,
        "by_benchmark": {"webarena": 1},
    }
    assert [node["kind"] for node in nodes] == ["session", "prompt", "llm", "tool"]
    serialized = json.dumps(nodes)
    assert "Successful" not in serialized
    assert "trajectory_looping" not in serialized
    assert annotations[f"session:{session}"]["tag"] == "complete a browser task"
    assert annotations[f"prompt:{session}"]["tag"] == "complete a website task"
    assert MODULE.annotation_input_matches(nodes) == []
    assert nodes[2]["data"]["reasoning"] == "I need to open the discussion."
    assert nodes[3]["data"]["action"] == "click('17')"


def test_session_list_rejects_duplicate_source_ids(tmp_path):
    path = tmp_path / "sessions.json"
    path.write_text(json.dumps({"sessions": ["s1", "s1"]}), encoding="utf-8")

    try:
        MODULE.load_session_list(path)
    except RuntimeError as error:
        assert "duplicates" in str(error)
    else:
        raise AssertionError("duplicate session list should fail")
