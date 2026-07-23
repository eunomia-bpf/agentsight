import importlib.util
import json
import sys
from pathlib import Path


SCRIPT = Path(__file__).with_name("agentreward_recursive_diff_eval.py")
SPEC = importlib.util.spec_from_file_location("agentreward_recursive_diff_eval", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def operation(session, step, result="progress"):
    evidence = f"{session}:step-{step:04d}"
    return {
        "value": 1,
        "fields": {
            "action": "click",
            "agent": "model",
            "evidence_id": evidence,
            "result": result,
            "source_session": session,
        },
    }


def test_recursive_records_preserve_source_and_add_concrete_call_leaf():
    record = operation("webarena__task-1__model", 3)
    evidence = record["fields"]["evidence_id"]
    path = [
        "complete a browser task",
        "complete a website task",
        "recover from failed or repeated interaction",
    ]

    recursive = MODULE.recursive_records([record], {evidence: path})

    assert MODULE.source_key(recursive[0]) == MODULE.source_key(record)
    assert recursive[0]["fields"]["operation"] == path
    assert recursive[0]["fields"]["call_id"] == evidence
    assert recursive[0]["fields"]["tool"] == "click"
    assert recursive[0]["fields"]["source_kind"] == "tool"


def test_unique_session_score_deduplicates_pair_occurrences():
    session = "webarena__task-1__model"
    repeated = operation(session, 0, result="repeated")
    progress = operation(session, 1)
    paths = {
        repeated["fields"]["evidence_id"]: [
            "complete a browser task",
            MODULE.RECOVERY_OPERATION,
        ],
        progress["fields"]["evidence_id"]: ["complete a browser task", "make progress"],
    }

    rows = MODULE.unique_session_rows(
        [repeated, progress, repeated],
        [repeated],
        paths,
    )

    assert rows[session]["operations"] == 2
    assert rows[session]["recursive_score"] == 0.5
    assert rows[session]["fixed_score"] == 0.5


def test_consensus_looping_marks_annotator_disagreement_unknown(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "annotations.csv").write_text(
        "\n".join(
            [
                "benchmark,task_id,model_name,exp_name,trajectory_looping",
                "webarena,webarena.1,model-a,exp-a,Yes",
                "webarena,webarena.1,model-a,exp-a,No",
                "webarena,webarena.2,model-a,exp-a,Yes",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    labels = MODULE.consensus_looping(tmp_path)

    assert labels[MODULE.source_session_id("webarena", "webarena.1", "model-a")] is None
    assert labels[MODULE.source_session_id("webarena", "webarena.2", "model-a")] is True


def test_ap_score_reports_supported_signal(monkeypatch):
    monkeypatch.setattr(MODULE, "BOOTSTRAP_DRAWS", 100)
    sessions = {
        "t1-good": {"recursive_score": 0.0, "fixed_score": 0.0},
        "t1-loop": {"recursive_score": 1.0, "fixed_score": 0.5},
        "t2-good": {"recursive_score": 0.1, "fixed_score": 0.0},
        "t2-loop": {"recursive_score": 0.9, "fixed_score": 0.5},
    }
    labels = {
        "t1-good": False,
        "t1-loop": True,
        "t2-good": False,
        "t2-loop": True,
    }
    tasks = {
        "t1-good": "task-1",
        "t1-loop": "task-1",
        "t2-good": "task-2",
        "t2-loop": "task-2",
    }

    score = MODULE.score_looping(sessions, labels, tasks)

    assert score["recursive_ap"] == 1.0
    assert score["tested_hypothesis"] == "supported"
