#!/usr/bin/env python3
"""Prepare the R142 pilot launch package without collecting responses.

R187 is a logistics artifact: it packages the frozen R142 participant views into
per-participant files and a blank response CSV. It must not contain answer-key
rows, oracle fields, or any real participant responses, and it must not be used
as C5 outcome evidence.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_OUT = SCRIPT_DIR / "out" / "user-task-pilot-r142" / "launch"
PARTICIPANT_IDS = [f"P{idx:02d}" for idx in range(1, 6)]
EXPECTED_ASSIGNMENTS_PER_PARTICIPANT = 14
EXPECTED_ASSIGNMENT_ROWS = 70
EXPECTED_TASKS = 14

FORBIDDEN_LAUNCH_KEYS = {
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


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def scan_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    """Return dotted paths to launch payload keys that would leak study answers."""
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_LAUNCH_KEYS:
                hits.append(child_path)
            hits.extend(scan_forbidden_keys(child, child_path))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            hits.extend(scan_forbidden_keys(child, f"{path}[{idx}]"))
    return hits


def group_assignments(assignments: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in assignments:
        grouped[str(row.get("participant_id", ""))].append(row)
    return {
        participant_id: sorted(rows, key=lambda row: int(row.get("order_index") or 0))
        for participant_id, rows in sorted(grouped.items())
    }


def response_template_is_blank(rows: list[dict[str, str]]) -> bool:
    return all(
        row.get("response_json") == "{}"
        and not row.get("task_time_seconds")
        and not row.get("confidence")
        and not row.get("notes")
        for row in rows
    )


def validate_inputs(
    bundle: dict[str, Any],
    packets_obj: dict[str, Any],
    assignments: list[dict[str, str]],
    response_rows: list[dict[str, str]],
    prereg: dict[str, Any],
) -> tuple[dict[str, list[dict[str, str]]], dict[str, dict[str, Any]]]:
    errors = []
    if not str(bundle.get("run_id") or "").startswith("R142"):
        errors.append("bundle run_id must refer to R142")
    if not str(prereg.get("run_id") or "").startswith("R142"):
        errors.append("preregistration run_id must refer to R142")
    if prereg.get("status") != "frozen_before_collection":
        errors.append("R142 preregistration must be frozen before launch material generation")
    if len(assignments) != EXPECTED_ASSIGNMENT_ROWS:
        errors.append(f"assignment row count must be {EXPECTED_ASSIGNMENT_ROWS}")
    if len(response_rows) != len(assignments):
        errors.append("response template row count must match assignments")
    if not response_template_is_blank(response_rows):
        errors.append("response template must remain blank before launch")

    packets = packets_obj.get("packets") or []
    packet_by_id = {str(packet.get("packet_id")): packet for packet in packets if isinstance(packet, dict)}
    if len(packet_by_id) != len(packets):
        errors.append("participant packets must have unique packet_id values")
    if len(packet_by_id) != EXPECTED_ASSIGNMENT_ROWS:
        errors.append(f"participant packet count must be {EXPECTED_ASSIGNMENT_ROWS}")

    grouped = group_assignments(assignments)
    if sorted(grouped) != PARTICIPANT_IDS:
        errors.append(f"participants must be exactly {PARTICIPANT_IDS}")
    for participant_id in PARTICIPANT_IDS:
        rows = grouped.get(participant_id, [])
        if len(rows) != EXPECTED_ASSIGNMENTS_PER_PARTICIPANT:
            errors.append(f"{participant_id} must have {EXPECTED_ASSIGNMENTS_PER_PARTICIPANT} assignments")

    condition_order = list(bundle.get("condition_order") or [])
    task_ids = sorted({str(row.get("task_id")) for row in assignments})
    if len(task_ids) != EXPECTED_TASKS:
        errors.append(f"assignment task count must be {EXPECTED_TASKS}")
    for task_id in task_ids:
        task_conditions = sorted(str(row.get("condition")) for row in assignments if row.get("task_id") == task_id)
        if task_conditions != sorted(condition_order):
            errors.append(f"{task_id} must appear once in every condition")

    assignment_packet_ids = {row.get("packet_id") for row in assignments}
    response_packet_ids = {row.get("packet_id") for row in response_rows}
    if assignment_packet_ids != response_packet_ids:
        errors.append("response template packet IDs must match assignments")
    for row in assignments:
        packet = packet_by_id.get(str(row.get("packet_id")))
        if not packet:
            errors.append(f"missing packet for assignment {row.get('packet_id')}")
            continue
        for field in ("task_id", "condition"):
            if str(packet.get(field)) != str(row.get(field)):
                errors.append(f"packet {row.get('packet_id')} {field} does not match assignment")

    for packet in packets:
        hits = scan_forbidden_keys(packet)
        if hits:
            errors.append(f"participant packet leaks forbidden keys: {', '.join(hits[:5])}")
            break

    if errors:
        raise AssertionError("; ".join(errors))
    return grouped, packet_by_id


def participant_payload(
    participant_id: str,
    assignment_rows: list[dict[str, str]],
    packet_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    tasks = []
    for row in assignment_rows:
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
        "run_id": "R187",
        "source_protocol": "R142",
        "participant_id": participant_id,
        "assignment_count": len(tasks),
        "instructions": {
            "response_csv": "Fill exactly one row per task in responses/user-task-response-template-r142-pilot.csv.",
            "timing": "Record task_time_seconds from first reading the task until writing response_json.",
            "confidence": "Use an integer 1..5 confidence rating.",
            "answer_policy": "Do not use source repository files, answer keys, or external help while answering.",
        },
        "tasks": tasks,
    }
    hits = scan_forbidden_keys(payload)
    if hits:
        raise AssertionError(f"{participant_id} payload leaks forbidden keys: {', '.join(hits[:5])}")
    return payload


def participant_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# R142 Pilot Packet {payload['participant_id']}",
        "",
        "This packet contains blinded AgentFlame task views only. It contains no answer key.",
        "",
        "For each task, write a JSON object in the matching response_csv row, then record task_time_seconds and confidence.",
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
                task["question"],
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


def launch_readme(manifest: dict[str, Any]) -> str:
    participant_ids = ", ".join(manifest["participant_ids"])
    return f"""# R187 R142 Pilot Launch Package

Status: `{manifest["status"]}`

This directory is ready to send to real R142 pilot participants. It contains
per-participant blinded task packets, a blank response CSV, and a manifest. It
does not contain the R142 answer key or any participant responses.

Participant IDs: {participant_ids}

Coordinator steps:

1. Send each participant only their matching `participants/Pxx.md` or `participants/Pxx.json`.
2. Collect exactly one completed response row for every assignment in `responses/user-task-response-template-r142-pilot.csv`.
3. Keep `docs/visexp/out/user-task-answer-key.csv` hidden from participants.
4. Score the completed CSV with `docs/visexp/score_user_task_results.py`.

Response fields:

- `response_json`: JSON object matching the task question.
- `task_time_seconds`: elapsed seconds for the task.
- `confidence`: integer 1..5.
- `notes`: optional participant notes.

Claim boundary:

R187 is launch material only. It records zero real responses and cannot support
C5. C5 remains unsupported until real participant responses are collected and
scored under the frozen R142 preregistration.
"""


def response_readme() -> str:
    return """# R142 Pilot Responses

The CSV template in this directory is intentionally blank. Complete it only with
real participant responses from P01-P05.

Do not commit filled response rows unless the participants have approved the
research data handling plan. After collection, score a copy with:

```sh
python3 docs/visexp/score_user_task_results.py \\
  --responses <completed-pilot-response.csv> \\
  --bundle docs/visexp/out/user-task-benchmark.json \\
  --answer-key docs/visexp/out/user-task-answer-key.csv \\
  --assignments docs/visexp/out/user-task-assignments.csv \\
  --out docs/visexp/out/user-task-pilot-r142
```
"""


def source_summary(paths: dict[str, Path]) -> dict[str, dict[str, str]]:
    return {
        name: {
            "path": rel(path),
            "sha256": sha256_file(path),
        }
        for name, path in sorted(paths.items())
    }


def build_launch(out_dir: Path) -> dict[str, Any]:
    source_paths = {
        "bundle": SCRIPT_DIR / "out" / "user-task-benchmark.json",
        "participant_packets": SCRIPT_DIR / "out" / "user-task-participant-packets.json",
        "assignments": SCRIPT_DIR / "out" / "user-task-assignments.csv",
        "response_template": SCRIPT_DIR / "out" / "user-task-response-template.csv",
        "preregistration": SCRIPT_DIR / "out" / "user-task-preregistration-r142.json",
    }
    bundle = read_json(source_paths["bundle"])
    packets_obj = read_json(source_paths["participant_packets"])
    assignments = read_csv_rows(source_paths["assignments"])
    response_rows = read_csv_rows(source_paths["response_template"])
    prereg = read_json(source_paths["preregistration"])
    grouped, packet_by_id = validate_inputs(bundle, packets_obj, assignments, response_rows, prereg)

    participants_dir = out_dir / "participants"
    responses_dir = out_dir / "responses"
    participant_files: dict[str, dict[str, str]] = {}
    forbidden_hits: list[str] = []
    for participant_id in PARTICIPANT_IDS:
        payload = participant_payload(participant_id, grouped[participant_id], packet_by_id)
        json_path = participants_dir / f"{participant_id}.json"
        md_path = participants_dir / f"{participant_id}.md"
        write_json(json_path, payload)
        md_path.write_text(participant_markdown(payload), encoding="utf-8")
        forbidden_hits.extend(scan_forbidden_keys(payload))
        participant_files[participant_id] = {
            "json": rel(json_path),
            "md": rel(md_path),
            "json_sha256": sha256_file(json_path),
            "md_sha256": sha256_file(md_path),
        }

    response_template_path = responses_dir / "user-task-response-template-r142-pilot.csv"
    write_csv_rows(response_template_path, response_rows, RESPONSE_FIELDS)
    (responses_dir / "README.md").write_text(response_readme(), encoding="utf-8")

    answer_key_included = any(path.name == "user-task-answer-key.csv" for path in out_dir.rglob("*") if path.is_file())
    manifest = {
        "schema_version": 1,
        "run_id": "R187",
        "source_protocol": "R142",
        "claim": "C5 developer utility",
        "status": "pilot_launch_ready_no_responses",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_artifacts": source_summary(source_paths),
        "participant_count": len(PARTICIPANT_IDS),
        "participant_ids": PARTICIPANT_IDS,
        "task_count": EXPECTED_TASKS,
        "packet_count": len(packet_by_id),
        "assignment_count": len(assignments),
        "assignments_per_participant": EXPECTED_ASSIGNMENTS_PER_PARTICIPANT,
        "condition_order": list(bundle.get("condition_order") or []),
        "response_template_rows": len(response_rows),
        "real_response_count": 0,
        "launch_files": {
            "readme": rel(out_dir / "README.md"),
            "manifest": rel(out_dir / "manifest.json"),
            "response_template": rel(response_template_path),
            "response_readme": rel(responses_dir / "README.md"),
            "participants": participant_files,
        },
        "leak_scan": {
            "status": "ok" if not forbidden_hits and not answer_key_included else "failed",
            "forbidden_key_hits": sorted(set(forbidden_hits)),
            "answer_key_included": answer_key_included,
        },
        "claim_gate": {
            "launch_ready": True,
            "pilot_ready": False,
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
            "R187 packages frozen R142 launch materials only. It records zero real participant "
            "responses and cannot support C5 until real responses are scored."
        ),
    }
    if manifest["leak_scan"]["status"] != "ok":
        raise AssertionError("launch package leak scan failed")
    write_json(out_dir / "manifest.json", manifest)
    (out_dir / "README.md").write_text(launch_readme(manifest), encoding="utf-8")
    (out_dir / "manifest.md").write_text(manifest_markdown(manifest), encoding="utf-8")
    return manifest


def manifest_markdown(manifest: dict[str, Any]) -> str:
    return f"""# R187 Manifest

Status: `{manifest["status"]}`

- Participants: {manifest["participant_count"]}
- Assignments: {manifest["assignment_count"]}
- Tasks: {manifest["task_count"]}
- Conditions: {", ".join(manifest["condition_order"])}
- Real responses: {manifest["real_response_count"]}
- Answer key included: {manifest["leak_scan"]["answer_key_included"]}
- Forbidden launch keys: {len(manifest["leak_scan"]["forbidden_key_hits"])}

Claim boundary: {manifest["claim_boundary"]}
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    result = build_launch(Path(args.out))
    print(json.dumps(result, indent=2, sort_keys=True))
