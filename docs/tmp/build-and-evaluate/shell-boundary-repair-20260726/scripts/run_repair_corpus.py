#!/usr/bin/env python3
"""Rerun the original 120-question repair corpus with the repaired projection."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import types
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[5]
OUTPUT = Path(__file__).resolve().parents[1] / "repair-corpus"
SOURCE = (
    REPO
    / "docs/tmp/build-and-evaluate/"
    "step-0004-20260723T181008-0700/experiment-001"
)
EXPECTED = (
    REPO
    / "docs/tmp/build-and-evaluate/"
    "rq7-error-taxonomy-20260725/corrected-oracle/corrected-answers.csv"
)
ANSWER_LAYER_REVISION = "7e5464eca650428ba238ea3d2c20052bedbbe272"


def load_module(name: str, path: Path) -> Any:
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_answer_layer() -> Any:
    completed = subprocess.run(
        [
            "git",
            "show",
            f"{ANSWER_LAYER_REVISION}:agentvis/research/rq7_measurement.py",
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr)
    module = types.ModuleType("rq7_repair_answer_layer")
    exec(
        compile(
            completed.stdout,
            f"{ANSWER_LAYER_REVISION}:rq7_measurement.py",
            "exec",
        ),
        module.__dict__,
    )
    return module


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    args = parser.parse_args()
    if OUTPUT.exists():
        raise RuntimeError(f"repair-corpus output already exists: {OUTPUT}")
    binary = args.binary.resolve()
    if not binary.is_file():
        raise RuntimeError(f"agentvis binary does not exist: {binary}")

    measurement = load_module(
        "rq7_shell_repair_measurement",
        REPO / "agentvis/research/rq7_measurement.py",
    )
    answer_layer = load_answer_layer()
    freeze = json.loads((SOURCE / "private/freeze.json").read_text())
    projection, _ = measurement.build_agent_session_projection(
        SOURCE / "private",
        OUTPUT / "projection",
        binary_override=binary,
    )
    expected: dict[str, str] = {}
    with EXPECTED.open() as handle:
        for row in csv.DictReader(handle):
            expected[row["id"]] = row["corrected_expected"]

    rows: list[dict[str, Any]] = []
    join_diagnostics: dict[str, dict[str, int]] = {}
    frozen_home = SOURCE / "private/frozen-home"
    for project in freeze["projects"]:
        root = Path(project["worktree"])
        target_worktree = answer_layer.worktree_id(root)
        session_order = {
            row["session_id"]: row["session_ordinal"]
            for row in project["sessions"]
        }
        calls = answer_layer.source_call_ids(project, frozen_home)
        sessions_by_call: dict[str, list[str]] = defaultdict(list)
        for session_id, call_ids in calls.items():
            for call_id in call_ids:
                sessions_by_call[call_id].append(session_id)

        tracker = answer_layer.ArtifactTracker(root)
        projected_edges: list[dict[str, Any]] = []
        diagnostics: Counter[str] = Counter()
        trace = projection[project["project"]]
        for event_ordinal, event in enumerate(trace.get("events") or []):
            actions = [
                action
                for action in event.get("actions") or []
                if action.get("worktree_id") == target_worktree
                and not action.get("scope")
            ]
            if not actions:
                continue
            call_id = str(event.get("source_call_id") or "")
            candidates = sessions_by_call.get(call_id, [])
            if not candidates:
                diagnostics["unmapped"] += 1
                continue
            session_id = (
                candidates[0]
                if len(candidates) == 1
                else min(candidates, key=session_order.__getitem__)
            )
            for action in actions:
                path = str(action.get("path") or "")
                if not path:
                    continue
                access = str(action.get("access") or "write")
                previous = str(action.get("previous_path") or "") or None
                identity = tracker.identity(path, access, previous)
                projected_edges.append(
                    {
                        "session_id": session_id,
                        "session_ordinal": session_order[session_id],
                        "call_id": call_id,
                        "event_ordinal": event_ordinal,
                        "artifact_id": identity,
                        "path": path,
                        "access": access,
                        "action_class": "read" if access == "read" else "mutate",
                    }
                )
        for edge in projected_edges:
            edge["display_path"] = tracker.display[edge["artifact_id"]]
        join_diagnostics[project["project"]] = dict(diagnostics)

        p0_path = project["anchors"][0]["path"]
        identities = {
            edge["artifact_id"]
            for edge in projected_edges
            if edge["path"] == p0_path or edge["display_path"] == p0_path
        }
        p0 = (
            max(
                identities,
                key=lambda identity: sum(
                    edge["artifact_id"] == identity for edge in projected_edges
                ),
            )
            if identities
            else None
        )
        relations = (
            answer_layer.relation_values(
                projected_edges,
                len(project["sessions"]),
                p0,
            )
            if p0
            else None
        )
        official = project["procgrep_action_atoms"]
        action_values = {
            "A1": str(sum(sequence.count("read_file") for sequence in official.values())),
            "A2": str(sum(sequence.count("edit") for sequence in official.values())),
            "A3": str(sum(sequence.count("run_test") for sequence in official.values())),
            "A4": str(answer_layer.pattern_count(official, r"read_file (?:[a-z_]+ )*edit ")),
            "A5": str(answer_layer.pattern_count(official, r"edit (?:[a-z_]+ )*run_test ")),
        }
        final_values = {
            f"D{index}": row["status"]
            for index, row in enumerate(project["workspace"]["paths"], start=1)
        }
        projected_paths = {
            edge["display_path"] for edge in projected_edges
        } | {edge["path"] for edge in projected_edges}
        for question in project["questions"]:
            template = question["template"]
            family = question["family"]
            if family == "A":
                status, value = "answer", action_values[template]
            elif family in {"B", "C"} and relations is not None:
                status, value = "answer", relations[template]
            elif family == "D":
                path = project["workspace"]["paths"][int(template[1:]) - 1]["path"]
                status = "answer" if path in projected_paths else "abstain"
                value = final_values[template] if status == "answer" else ""
            else:
                status, value = "abstain", ""
            expected_value = expected[question["id"]]
            rows.append(
                {
                    "id": question["id"],
                    "project": project["project"],
                    "family": family,
                    "template": template,
                    "status": status,
                    "answer": value,
                    "expected": expected_value,
                    "correct": int(status == "answer" and value == expected_value),
                    "wrong": int(status == "answer" and value != expected_value),
                }
            )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "question-results.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    family_scores = []
    for family in "ABCD":
        selected = [row for row in rows if row["family"] == family]
        family_scores.append(
            {
                "family": family,
                "total": len(selected),
                "correct": sum(row["correct"] for row in selected),
                "wrong": sum(row["wrong"] for row in selected),
                "abstain": sum(row["status"] == "abstain" for row in selected),
            }
        )
    bc = [row for row in rows if row["family"] in {"B", "C"}]
    summary = {
        "status": "pass"
        if len(bc) == 60
        and sum(row["correct"] for row in bc) == 60
        and not any(row["status"] == "abstain" for row in bc)
        else "fail",
        "corpus": "original 72-file repair corpus / 120 questions",
        "binary": str(binary),
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "answer_layer_revision": ANSWER_LAYER_REVISION,
        "family_scores": family_scores,
        "bc_gate": {
            "total": len(bc),
            "correct": sum(row["correct"] for row in bc),
            "wrong": sum(row["wrong"] for row in bc),
            "abstain": sum(row["status"] == "abstain" for row in bc),
        },
        "join_diagnostics": join_diagnostics,
    }
    write_json(OUTPUT / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
