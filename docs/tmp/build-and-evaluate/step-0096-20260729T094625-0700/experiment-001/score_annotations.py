#!/usr/bin/env python3
"""Package, assemble, canonicalize, profile, and score one annotation group."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time
from typing import Any

import run_annotation


HERE = Path(__file__).resolve().parent
REPO = run_annotation.REPO
TARGET_OPERATIONS = (
    REPO / "docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl"
)
OPERATION_USAGE = run_annotation.OPERATION_USAGE
FIXED_CANONICAL_NAMES = (
    REPO
    / "docs/tmp/build-and-evaluate/step-0067-20260722T135005-0700"
    / "experiment-001/canonical-names.json"
)
VERIFIED_MANIFEST = (
    REPO / ".agentsight/experiments/codetracebench-rq2/manifests/verified.parquet"
)
MULTIRES_ASSIGNMENTS = (
    REPO
    / ".agentsight/experiments/rq3-multiresolution-recurrence-v1"
    / "full/codetrace/operation-assignments.jsonl"
)
AGENTPPROF = REPO / "agentpprof/target/release/agentpprof"
PIPELINE_RECORDS = HERE / "pipeline-records.jsonl"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def run(name: str, command: list[str]) -> None:
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=REPO,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    record = {
        "name": name,
        "command": command,
        "returncode": result.returncode,
        "wall_seconds": time.monotonic() - started,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    with PIPELINE_RECORDS.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    if result.returncode:
        raise RuntimeError(
            f"{name} failed ({result.returncode}): {result.stderr[-3000:]}"
        )


def filtered_canonical_names(sessions: set[str], output: Path) -> None:
    fixed = read_json(FIXED_CANONICAL_NAMES)
    task_names = set()
    with OPERATION_USAGE.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if str(row["session"]) in sessions:
                task_names.add(str(row["task_name"]))
    write_json(
        output,
        {
            "task_roots": {
                key: value
                for key, value in fixed["task_roots"].items()
                if key in task_names
            },
            "semantic_labels": fixed["semantic_labels"],
        },
    )


def package(group: str, condition: str, root: Path) -> list[dict[str, Any]]:
    packets = run_annotation.selected_packets(group)
    annotations = []
    for packet in packets:
        path = run_annotation.cell_path(group, condition, str(packet["session"]))
        if not path.is_file():
            raise FileNotFoundError(f"missing annotation: {path}")
        annotations.append(read_json(path))
    packet_dir = root / "packets"
    annotation_dir = root / "annotations"
    write_json(
        packet_dir / "batch-01.json",
        {
            "schema": "agentsight.agent-operation-annotation-packet.v1",
            "sessions": packets,
        },
    )
    write_json(
        packet_dir / "manifest.json",
        {
            "schema": "agentsight.agent-operation-annotation-packet.manifest.v1",
            "selection": f"step0096 {group} {condition}",
            "sessions": len(packets),
            "turns": sum(int(row["turn_count"]) for row in packets),
            "operations": sum(int(row["operation_count"]) for row in packets),
            "batches": [
                {
                    "file": "batch-01.json",
                    "sessions": len(packets),
                    "turns": sum(int(row["turn_count"]) for row in packets),
                    "operations": sum(int(row["operation_count"]) for row in packets),
                    "session_ids": [row["session"] for row in packets],
                }
            ],
        },
    )
    write_json(
        annotation_dir / "batch-01.json",
        {"batch": "batch-01", "sessions": annotations},
    )
    return packets


def score(group: str, condition: str) -> dict[str, Any]:
    root = HERE / "pipeline" / group / condition
    packets = package(group, condition, root)
    sessions = {str(row["session"]) for row in packets}
    canonical_names = root / "canonical-names.json"
    filtered_canonical_names(sessions, canonical_names)
    assembled = root / "assembled"
    canonical = root / "canonical"
    profile = root / "profile" / "agent.pb.gz"
    score_dir = root / "score"
    run(
        f"{group}-{condition}-assemble",
        [
            "python3",
            str(REPO / "script/assemble_agent_operation_profile.py"),
            "--target-operations",
            str(TARGET_OPERATIONS),
            "--operation-usage",
            str(OPERATION_USAGE),
            "--packet-dir",
            str(root / "packets"),
            "--annotation-dir",
            str(root / "annotations"),
            "--contract-root-only-prefix",
            "--canonical-names",
            str(canonical_names),
            "--mode",
            "preflight",
            "--out",
            str(assembled),
        ],
    )
    inference = read_json(assembled / "inference-summary.json")
    inference.update(
        {
            "algorithm_version": f"step0096-{condition}-v1",
            "annotation_backend": (
                "one complete-session direct call"
                if condition == "full"
                else "one direct call over deterministic selected source evidence"
            ),
            "official_manifest_opened": False,
            "official_stages_opened": False,
        }
    )
    write_json(assembled / "inference-summary.json", inference)
    run(
        f"{group}-{condition}-canonicalize",
        [
            "python3",
            str(REPO / "script/canonicalize_operation_marks.py"),
            "--operation-marks",
            str(assembled / "operation-marks.json"),
            "--operations",
            str(assembled / "operations-count.jsonl"),
            "--reference-predictions",
            str(assembled / "predictions.jsonl"),
            "--out-dir",
            str(canonical),
        ],
    )
    profile.parent.mkdir(parents=True, exist_ok=True)
    run(
        f"{group}-{condition}-profile",
        [
            str(AGENTPPROF),
            "--operation-file",
            str(assembled / "operations-count.jsonl"),
            "--operation-mark-file",
            str(canonical / "operation-marks.json"),
            "--view",
            "operations",
            "--deterministic-output",
            "--output",
            str(profile),
        ],
    )
    run(
        f"{group}-{condition}-pprof-readback",
        ["go", "tool", "pprof", "-top", str(profile)],
    )
    run(
        f"{group}-{condition}-score",
        [
            "python3",
            str(REPO / "script/rq3_recursive_operation_segmentation_eval.py"),
            "score",
            "--target-operations",
            str(TARGET_OPERATIONS),
            "--predictions",
            str(canonical / "predictions.jsonl"),
            "--inference-summary",
            str(assembled / "inference-summary.json"),
            "--verified-manifest",
            str(VERIFIED_MANIFEST),
            "--multires-assignments",
            str(MULTIRES_ASSIGNMENTS),
            "--out",
            str(score_dir),
        ],
    )
    summary = {
        "group": group,
        "evaluation_role": group,
        "scorer_cli_mode_note": (
            "The unchanged scorer names every selected partial population "
            "`preflight`; this wrapper's evaluation_role is authoritative for "
            "pilot versus confirmation interpretation."
        ),
        "condition": condition,
        "sessions": len(packets),
        "turns": sum(int(row["turn_count"]) for row in packets),
        "operations": sum(int(row["operation_count"]) for row in packets),
        "profile": str(profile.relative_to(HERE)),
        "score": read_json(score_dir / "summary.json"),
        "assembly": read_json(assembled / "summary.json"),
        "canonicalization": read_json(canonical / "canonicalization-report.json"),
    }
    write_json(root / "pipeline-summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group", choices=("preflight", "pilot", "confirmation"))
    parser.add_argument("condition", choices=("full", "split", "both"))
    args = parser.parse_args()
    conditions = ("full", "split") if args.condition == "both" else (args.condition,)
    for condition in conditions:
        summary = score(args.group, condition)
        candidate = summary["score"]["metrics"]["candidate"]
        print(
            json.dumps(
                {
                    "group": args.group,
                    "condition": condition,
                    "sessions": summary["sessions"],
                    "operations": summary["operations"],
                    "bcubed_f1": candidate["bcubed"]["f1"],
                    "boundary_f1": candidate["boundary"]["f1"],
                    "profile": summary["profile"],
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
