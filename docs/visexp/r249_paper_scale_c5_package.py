#!/usr/bin/env python3
"""R249: build a paper-scale C5 participant-packet launch package.

R187/R247 make the five-participant pilot sendable, but the C5 scorer requires
at least twelve real participants before paper-scale utility can be claimed.
R249 reuses the frozen R142 task packets and creates a separate twelve-slot
assignment package. It records zero responses and cannot support C5 by itself.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUT_DIR = SCRIPT_DIR / "out"
DEFAULT_OUT = OUT_DIR / "user-task-paper-r249"

RUN_ID = "R249"
PARTICIPANT_COUNT = 12
EXPECTED_TASKS = 14
CONDITION_ORDER = [
    "trace-tree",
    "event-count-proxy",
    "flat-summary",
    "nonsemantic-stack",
    "semantic-stack",
]
RESPONSE_FIELDS = [
    "participant_id",
    "order_index",
    "packet_id",
    "task_id",
    "condition",
    "response_json",
    "task_time_seconds",
    "confidence",
    "notes",
]
FORBIDDEN_KEYS = {
    "answer_format",
    "answer_json",
    "answer_key",
    "baseline_contrast",
    "oracle",
    "oracle_sources",
    "projected_stack_hash",
    "scoring",
    "skill",
    "top_full_semantic_variants",
    "top_semantic_variants",
    "full_semantic_variant_count",
    "semantic_variant_count",
    "variant_count",
    "mixing_against_full_semantics",
    "projection",
}
FORBIDDEN_TEXT = [
    "user-task-answer-key.csv",
    "answer_json",
    "oracle_sources",
    "score_user_task_results.py",
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def scan_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_KEYS:
                hits.append(child_path)
            hits.extend(scan_forbidden_keys(child, child_path))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            hits.extend(scan_forbidden_keys(child, f"{path}[{idx}]"))
    return hits


def build_assignments(tasks: list[dict[str, Any]], participant_count: int) -> list[dict[str, Any]]:
    task_ids = [str(task["task_id"]) for task in tasks]
    rows: list[dict[str, Any]] = []
    for participant_index in range(participant_count):
        participant_id = f"P{participant_index + 1:02d}"
        for order_index in range(len(task_ids)):
            task_index = (order_index + participant_index) % len(task_ids)
            task_id = task_ids[task_index]
            condition = CONDITION_ORDER[(task_index + participant_index) % len(CONDITION_ORDER)]
            rows.append(
                {
                    "participant_id": participant_id,
                    "order_index": order_index + 1,
                    "task_id": task_id,
                    "condition": condition,
                    "packet_id": f"{task_id}-{condition}",
                }
            )
    return rows


def response_rows(assignments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **row,
            "response_json": "{}",
            "task_time_seconds": "",
            "confidence": "",
            "notes": "",
        }
        for row in assignments
    ]


def participant_payload(
    participant_id: str,
    assignment_rows: list[dict[str, Any]],
    packet_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    tasks = []
    for row in sorted(assignment_rows, key=lambda item: int(item["order_index"])):
        packet = packet_by_id[str(row["packet_id"])]
        tasks.append(
            {
                "order_index": int(row["order_index"]),
                "packet_id": row["packet_id"],
                "task_id": row["task_id"],
                "condition": row["condition"],
                "title": packet.get("title"),
                "claim": packet.get("claim"),
                "question": packet.get("question"),
                "views": packet.get("views") or [],
                "view_excerpt": packet.get("view_excerpt") or [],
            }
        )
    payload = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "source_protocol": "R142",
        "participant_id": participant_id,
        "assignment_count": len(tasks),
        "instructions": {
            "response_csv": (
                "Fill exactly one row per task in the coordinator-provided private "
                "completed-response CSV copied from responses/user-task-response-template-r249-paper.csv."
            ),
            "timing": "Record task_time_seconds from first reading the task until writing response_json.",
            "confidence": "Use an integer 1..5 confidence rating.",
            "answer_policy": "Do not use source repository files, answer keys, or external help while answering.",
        },
        "tasks": tasks,
    }
    hits = scan_forbidden_keys(payload)
    if hits:
        raise AssertionError(f"{participant_id} payload leaks forbidden keys: {hits[:5]}")
    return payload


def participant_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# R249 Paper-Scale Packet {payload['participant_id']}",
        "",
        "This packet contains blinded AgentFlame task views only. It contains no answer key.",
        "",
        "For each task, write a JSON object in the matching response CSV row, then record task_time_seconds and confidence.",
        "",
    ]
    for task in payload["tasks"]:
        lines.extend(
            [
                f"## {task['order_index']}. {task['packet_id']}",
                "",
                f"- Task: {task['task_id']}",
                f"- Condition: {task['condition']}",
                f"- Title: {task['title']}",
                "",
                str(task["question"]),
                "",
                "Views:",
            ]
        )
        for view in task.get("views") or []:
            lines.append(f"- {view}")
        lines.extend(
            [
                "",
                "Excerpt:",
                "",
                "```json",
                json.dumps(task.get("view_excerpt") or [], indent=2, sort_keys=True),
                "```",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def assignment_metrics(assignments: list[dict[str, Any]]) -> dict[str, Any]:
    by_participant = Counter(str(row["participant_id"]) for row in assignments)
    by_task_condition = Counter((str(row["task_id"]), str(row["condition"])) for row in assignments)
    per_task_counts: dict[str, dict[str, int]] = defaultdict(dict)
    for (task_id, condition), count in sorted(by_task_condition.items()):
        per_task_counts[task_id][condition] = count
    all_counts = list(by_task_condition.values())
    return {
        "participant_packet_count": len(by_participant),
        "assignment_count": len(assignments),
        "assignments_per_participant_packet": dict(sorted(by_participant.items())),
        "min_task_condition_replicates": min(all_counts) if all_counts else 0,
        "max_task_condition_replicates": max(all_counts) if all_counts else 0,
        "task_condition_replicates": per_task_counts,
    }


def leak_scan(paths: list[Path]) -> dict[str, Any]:
    hits: list[dict[str, str]] = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for needle in FORBIDDEN_TEXT:
            if needle in text:
                hits.append({"path": rel(path), "needle": needle})
    return {
        "forbidden_text": FORBIDDEN_TEXT,
        "hits": hits,
        "passed": not hits,
    }


def write_readme(path: Path, manifest: dict[str, Any]) -> None:
    participants = ", ".join(manifest["participant_packet_ids"])
    path.write_text(
        f"""# R249 Paper-Scale C5 Collection Package

Status: `{manifest["status"]}`

This package derives a twelve-packet paper-scale C5 launch package from
the frozen R142 task packets. It contains blinded participant packets, a blank
paper-scale response CSV, and assignments for scoring. It contains no answer
key and no participant responses.

Participant packet IDs: {participants}

Coordinator steps:

1. Send each participant only their matching `participants/Pxx.md` or `participants/Pxx.json`.
2. Copy `responses/user-task-response-template-r249-paper.csv` to a private completed-response CSV outside the committed artifact tree, then fill that private copy with real participant responses.
3. Score the private completed-response CSV with:

```bash
python3 docs/visexp/score_user_task_results.py \\
  --responses <completed-response.csv> \\
  --bundle docs/visexp/out/user-task-benchmark.json \\
  --answer-key docs/visexp/out/user-task-answer-key.csv \\
  --assignments docs/visexp/out/user-task-paper-r249/user-task-assignments-r249-paper.csv \\
  --out docs/visexp/out/user-task-paper-r249/scored
```

Claim boundary: {manifest["claim_boundary"]}
""",
        encoding="utf-8",
    )


def validate(bundle: dict[str, Any], packets: list[dict[str, Any]], assignments: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    task_ids = [str(task["task_id"]) for task in bundle.get("tasks", [])]
    packet_by_id = {str(packet["packet_id"]): packet for packet in packets}
    if len(task_ids) != EXPECTED_TASKS:
        errors.append(f"expected {EXPECTED_TASKS} tasks, saw {len(task_ids)}")
    if sorted(set(task_ids)) != sorted({str(packet["task_id"]) for packet in packets}):
        errors.append("packet task IDs do not match bundle task IDs")
    for row in assignments:
        packet = packet_by_id.get(str(row["packet_id"]))
        if not packet:
            errors.append(f"missing packet {row['packet_id']}")
            continue
        if str(packet.get("task_id")) != str(row["task_id"]):
            errors.append(f"packet task mismatch for {row['packet_id']}")
        if str(packet.get("condition")) != str(row["condition"]):
            errors.append(f"packet condition mismatch for {row['packet_id']}")
    metrics = assignment_metrics(assignments)
    if metrics["participant_packet_count"] != PARTICIPANT_COUNT:
        errors.append(f"expected {PARTICIPANT_COUNT} participant packets")
    if any(count != EXPECTED_TASKS for count in metrics["assignments_per_participant_packet"].values()):
        errors.append("each participant packet must have one assignment per task")
    if metrics["min_task_condition_replicates"] < 2:
        errors.append("paper-scale package should give every task-condition at least two replicates")
    if errors:
        raise AssertionError("; ".join(errors))
    return metrics


def run(args: argparse.Namespace) -> dict[str, Any]:
    source_commit = git(["rev-parse", "HEAD"])
    source_dirty = bool(git(["status", "--short"]))
    out_dir = Path(args.out).resolve()
    shutil.rmtree(out_dir, ignore_errors=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    bundle_path = OUT_DIR / "user-task-benchmark.json"
    packets_path = OUT_DIR / "user-task-participant-packets.json"
    prereg_path = OUT_DIR / "user-task-preregistration-r142.json"
    bundle = read_json(bundle_path)
    packets_obj = read_json(packets_path)
    prereg = read_json(prereg_path)
    packets = list(packets_obj.get("packets") or [])
    assignments = build_assignments(bundle.get("tasks") or [], PARTICIPANT_COUNT)
    metrics = validate(bundle, packets, assignments)
    packet_by_id = {str(packet["packet_id"]): packet for packet in packets}

    assignments_path = out_dir / "user-task-assignments-r249-paper.csv"
    response_template_path = out_dir / "responses" / "user-task-response-template-r249-paper.csv"
    write_csv(assignments_path, assignments, ["participant_id", "order_index", "task_id", "condition", "packet_id"])
    write_csv(response_template_path, response_rows(assignments), RESPONSE_FIELDS)

    participant_ids = [f"P{idx:02d}" for idx in range(1, PARTICIPANT_COUNT + 1)]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in assignments:
        grouped[str(row["participant_id"])].append(row)

    participant_files: dict[str, dict[str, str]] = {}
    payload_paths: list[Path] = []
    for participant_id in participant_ids:
        payload = participant_payload(participant_id, grouped[participant_id], packet_by_id)
        json_path = out_dir / "participants" / f"{participant_id}.json"
        md_path = out_dir / "participants" / f"{participant_id}.md"
        write_json(json_path, payload)
        md_path.write_text(participant_markdown(payload), encoding="utf-8")
        payload_paths.extend([json_path, md_path])
        participant_files[participant_id] = {
            "json": rel(json_path),
            "md": rel(md_path),
            "json_sha256": sha256_file(json_path),
            "md_sha256": sha256_file(md_path),
        }

    scan = leak_scan(payload_paths)
    manifest = {
        "schema_version": 1,
        "run_id": RUN_ID,
        "claim": "C5 developer utility",
        "status": "paper_scale_launch_ready_no_responses" if scan["passed"] else "failed",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_artifacts": {
            "bundle": {"path": rel(bundle_path), "sha256": sha256_file(bundle_path)},
            "participant_packets": {"path": rel(packets_path), "sha256": sha256_file(packets_path)},
            "preregistration": {"path": rel(prereg_path), "sha256": sha256_file(prereg_path)},
        },
        "preregistration_status": prereg.get("status"),
        "participant_packet_count": PARTICIPANT_COUNT,
        "participant_packet_ids": participant_ids,
        "actual_participant_response_count": 0,
        "task_count": EXPECTED_TASKS,
        "condition_order": CONDITION_ORDER,
        "assignment_metrics": metrics,
        "response_template": {
            "path": rel(response_template_path),
            "rows": len(assignments),
            "sha256": sha256_file(response_template_path),
            "blank": True,
        },
        "assignments": {
            "path": rel(assignments_path),
            "rows": len(assignments),
            "sha256": sha256_file(assignments_path),
        },
        "participant_files": participant_files,
        "leak_scan": scan,
        "real_response_count": 0,
        "blank_template_check_command": [
            "python3",
            "docs/visexp/score_user_task_results.py",
            "--responses",
            rel(response_template_path),
            "--bundle",
            "docs/visexp/out/user-task-benchmark.json",
            "--answer-key",
            "docs/visexp/out/user-task-answer-key.csv",
            "--assignments",
            rel(assignments_path),
            "--out",
            rel(out_dir / "scored"),
        ],
        "real_response_scoring_command": [
            "python3",
            "docs/visexp/score_user_task_results.py",
            "--responses",
            "<completed-response.csv>",
            "--bundle",
            "docs/visexp/out/user-task-benchmark.json",
            "--answer-key",
            "docs/visexp/out/user-task-answer-key.csv",
            "--assignments",
            rel(assignments_path),
            "--out",
            rel(out_dir / "scored"),
        ],
        "claim_gate": {
            "paper_scale_collection_ready": scan["passed"],
            "participant_packet_count_meets_claim_floor": PARTICIPANT_COUNT >= 12,
            "c5_supported": False,
            "requires_real_participants": True,
            "disallowed_evidence": [
                "blank response template",
                "author-filled mock responses",
                "subagent review",
                "LLM-filled responses",
            ],
        },
        "claim_boundary": (
            "R249 fixes the paper-scale launch logistics for C5, but records zero real "
            "participant responses. C5 remains unsupported until completed paper-scale "
            "responses are scored with the frozen answer key and nondefault R249 assignment file."
        ),
        "provenance": {
            "repo_commit": source_commit,
            "repo_dirty": source_dirty,
            "script": rel(Path(__file__).resolve()),
            "human_responses_added": 0,
            "llm_called": False,
            "raw_trace_read": False,
        },
    }
    if manifest["status"] == "failed":
        raise AssertionError(f"R249 leak scan failed: {scan['hits']}")
    write_json(out_dir / "manifest.json", manifest)
    write_readme(out_dir / "README.md", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()
    result = run(args)
    print(
        json.dumps(
            {
                "run_id": result["run_id"],
                "status": result["status"],
                "participant_packet_count": result["participant_packet_count"],
                "assignment_count": result["assignment_metrics"]["assignment_count"],
                "c5_supported": result["claim_gate"]["c5_supported"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
