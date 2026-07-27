#!/usr/bin/env python3
"""Rerun the fixed 116-question v2 corpus with repaired source-direct semantics."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[5]
OUTPUT = Path(__file__).resolve().parents[1] / "heldout"
SOURCE = REPO / "docs/tmp/build-and-evaluate/rq7-heldout-20260726/v2"
SPEC = Path(__file__).resolve().parents[1] / "repair-corpus-v2-spec.md"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def remap_anchors(
    frozen: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        grouped[edge["artifact_id"]].append(edge)
    anchors = []
    for prior in frozen:
        candidates = [
            (identity, rows)
            for identity, rows in grouped.items()
            if rows[-1]["display_path"] == prior["path"]
            or any(row["path"] == prior["path"] for row in rows)
        ]
        if not candidates:
            raise RuntimeError(f"fixed anchor disappeared: {prior['path']}")
        candidates.sort(
            key=lambda pair: (
                -len({(row["session_id"], row["call_id"]) for row in pair[1]}),
                pair[0],
            )
        )
        identity, rows = candidates[0]
        anchors.append(
            {
                **prior,
                "artifact_id": identity,
                "path": rows[-1]["display_path"],
                "call_count": len(
                    {(row["session_id"], row["call_id"]) for row in rows}
                ),
            }
        )
    return anchors


def edge_tuple(row: dict[str, Any]) -> tuple[Any, ...]:
    fields = (
        "native_session_id",
        "source_stream_id",
        "source_tool_ordinal",
        "call_id",
        "event_ordinal",
        "action_ordinal",
        "artifact_id",
        "path",
        "display_path",
        "access",
        "previous_path",
        "status",
        "confirmed_effect",
        "session_ordinal",
    )
    return tuple(row.get(field) for field in fields)


def call_tuple(row: dict[str, Any]) -> tuple[Any, ...]:
    fields = (
        "native_session_id",
        "session_ordinal",
        "source_stream_id",
        "source_tool_ordinal",
        "call_id",
        "status",
        "atom",
    )
    return tuple(row.get(field) for field in fields)


def aggregate_metrics(
    rows: list[dict[str, Any]],
    ledger: str,
) -> dict[str, Any]:
    totals = {
        key: sum(int(row[ledger][key]) for row in rows)
        for key in ("expected", "actual", "matched", "missing", "extra")
    }
    totals["precision"] = (
        totals["matched"] / totals["actual"]
        if totals["actual"]
        else float(totals["expected"] == 0)
    )
    totals["recall"] = (
        totals["matched"] / totals["expected"]
        if totals["expected"]
        else float(totals["actual"] == 0)
    )
    precision = totals["precision"]
    recall = totals["recall"]
    totals["f1"] = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return totals


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    args = parser.parse_args()
    if OUTPUT.exists():
        raise RuntimeError(f"heldout output already exists: {OUTPUT}")
    binary = args.binary.resolve()
    if not binary.is_file():
        raise RuntimeError(f"agentvis binary does not exist: {binary}")

    measurement = load_module(
        "rq7_shell_repair_measurement",
        REPO / "agentvis/research/rq7_measurement.py",
    )
    checker = load_module(
        "rq7_shell_repair_checker",
        REPO / "agentvis/research/rq7_source_oracle_check.py",
    )
    prior = json.loads((SOURCE / "private/freeze.json").read_text())
    if measurement.SPEC_VERSION != checker.SPEC_VERSION:
        raise RuntimeError(
            "primary/independent specification version mismatch: "
            f"{measurement.SPEC_VERSION} != {checker.SPEC_VERSION}"
        )
    spec_sha256 = hashlib.sha256(SPEC.read_bytes()).hexdigest()
    expected_question_ids = {row["id"] for row in prior["questions"]}
    if (
        len(expected_question_ids) != 116
        or Counter(row["family"] for row in prior["questions"])
        != {"A": 29, "B": 29, "C": 29, "D": 29}
    ):
        raise RuntimeError("parent 116-question family contract changed")
    source_private = SOURCE / "private"
    projects = []
    questions = []
    independent = {}
    for frozen_project in prior["projects"]:
        project = dict(frozen_project)
        edges, sessions, calls = measurement.artifact_edges(
            project,
            project["sources"],
            source_private / "frozen-home",
        )
        atoms = measurement.direct_atoms(
            project["sources"],
            source_private / "frozen-home",
        )
        anchors = remap_anchors(project["anchors"], edges)
        derived = measurement.question_rows(
            project,
            atoms,
            edges,
            sessions,
            anchors,
            project["workspace"],
        )
        selected_ids = {row["id"] for row in project["questions"]}
        derived = [row for row in derived if row["id"] in selected_ids]
        project.update(
            {
                "direct_action_atoms": atoms,
                "oracle_edges": edges,
                "oracle_calls": calls,
                "sessions": sessions,
                "anchors": anchors,
                "questions": derived,
                "fixed_question_anchors": True,
            }
        )
        answers, independent_edges, independent_calls = checker.recompute_project(
            source_private,
            project,
        )
        if sorted(map(edge_tuple, edges)) != sorted(
            map(edge_tuple, independent_edges)
        ):
            raise RuntimeError(
                f"primary/independent edge mismatch: {project['project']}"
            )
        if sorted(map(call_tuple, calls)) != sorted(
            map(call_tuple, independent_calls)
        ):
            raise RuntimeError(
                f"primary/independent call mismatch: {project['project']}"
            )
        for question in derived:
            if answers[question["template"]] != question["answer"]:
                raise RuntimeError(
                    f"primary/independent answer mismatch: {question['id']}"
                )
        independent[project["project"]] = {
            "edges": len(independent_edges),
            "calls": len(independent_calls),
            "questions": len(derived),
        }
        projects.append(project)
        questions.extend(derived)

    freeze = {
        **prior,
        "spec_version": checker.SPEC_VERSION,
        "question_spec_sha256": spec_sha256,
        "parent_question_spec_sha256": prior["question_spec_sha256"],
        "question_selection": "fixed parent question IDs and P0-P4 paths",
        "projects": projects,
        "questions": questions,
        "repair_corpus_v2": True,
        "source_archive_parent_sha256": hashlib.sha256(
            (SOURCE / "private/freeze.json").read_bytes()
        ).hexdigest(),
    }
    runtime = OUTPUT / "runtime-private"
    runtime.mkdir(parents=True)
    os.symlink(source_private / "frozen-home", runtime / "frozen-home")
    os.symlink(source_private / "workspace", runtime / "workspace")
    write_json(runtime / "freeze.json", freeze)
    os.environ["RQ7_AGENTVIS_BINARY"] = str(binary)
    rows, _ = measurement.deterministic_methods(
        runtime,
        OUTPUT / "raw/deterministic",
        projection_output=OUTPUT / "projection",
    )
    conformance = json.loads(
        (OUTPUT / "raw/deterministic/projection-conformance.json").read_text()
    )
    trajectory = sorted(
        [row for row in rows if row["method"] == "trajectory"],
        key=lambda row: row["id"],
    )
    actual_question_ids = {row["id"] for row in trajectory}
    family_totals = Counter(row["family"] for row in trajectory)
    with (OUTPUT / "question-results.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(trajectory[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(trajectory)
    family_scores = []
    for family in "ABCD":
        selected = [row for row in trajectory if row["family"] == family]
        family_scores.append(
            {
                "family": family,
                "total": len(selected),
                "correct": sum(row["correct"] for row in selected),
                "wrong": sum(row["wrong"] for row in selected),
                "abstain": sum(row["status"] == "abstain" for row in selected),
            }
        )
    bc = [row for row in trajectory if row["family"] in {"B", "C"}]
    d_rows = [row for row in trajectory if row["family"] == "D"]
    ledgers = {
        ledger: aggregate_metrics(conformance, ledger)
        for ledger in (
            "session_order",
            "attempted_edges",
            "confirmed_effect_edges",
            "edge_call_statuses",
        )
    }
    exact_edges = all(
        metric["missing"] == 0 and metric["extra"] == 0
        for metric in ledgers.values()
    )
    strict_pass = (
        len(trajectory) == 116
        and actual_question_ids == expected_question_ids
        and family_totals == {"A": 29, "B": 29, "C": 29, "D": 29}
        and len(bc) == 58
        and len(d_rows) == 29
        and sum(row["correct"] for row in bc) == len(bc)
        and not any(row["status"] == "abstain" for row in bc)
        and sum(row["correct"] for row in d_rows) == len(d_rows)
        and not any(row["status"] == "abstain" for row in d_rows)
        and exact_edges
    )
    summary = {
        "status": "pass" if strict_pass else "fail",
        "run_status": "valid",
        "corpus": "repair-corpus-v2 (formerly held-out v2)",
        "generalization_boundary": (
            "This corpus was inspected to design the repair and is no longer "
            "held out. Any new generality claim requires a third independent corpus."
        ),
        "questions": len(trajectory),
        "binary": str(binary),
        "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "source_freeze_sha256": freeze["source_archive_parent_sha256"],
        "spec_version": checker.SPEC_VERSION,
        "question_spec_sha256": spec_sha256,
        "parent_question_spec_sha256": prior["question_spec_sha256"],
        "question_contract": {
            "ids_exact": actual_question_ids == expected_question_ids,
            "family_totals": dict(sorted(family_totals.items())),
        },
        "independent_oracle": independent,
        "family_scores": family_scores,
        "bc_gate": {
            "total": len(bc),
            "correct": sum(row["correct"] for row in bc),
            "wrong": sum(row["wrong"] for row in bc),
            "abstain": sum(row["status"] == "abstain" for row in bc),
        },
        "d_gate": {
            "total": len(d_rows),
            "correct": sum(row["correct"] for row in d_rows),
            "wrong": sum(row["wrong"] for row in d_rows),
            "abstain": sum(row["status"] == "abstain" for row in d_rows),
        },
        "edge_ledgers": ledgers,
        "strict_edge_conformance": exact_edges,
    }
    write_json(OUTPUT / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if strict_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
