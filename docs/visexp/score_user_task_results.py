#!/usr/bin/env python3
"""Score C5 user-task responses against the committed answer key.

This script is the result pipeline for a pilot or paper user study. It does not
invent participant data. C5 remains unsupported until a real response CSV is
provided and scored.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_answer_key(path: Path) -> dict[str, dict[str, Any]]:
    answers = {}
    for row in read_csv_rows(path):
        task_id = row.get("task_id")
        if not task_id:
            continue
        answers[task_id] = json.loads(row.get("answer_json") or "{}")
    return answers


def required_fields_by_task(bundle: dict[str, Any]) -> dict[str, list[str]]:
    out = {}
    for task in bundle.get("tasks", []):
        scoring = task.get("scoring") or {}
        required = scoring.get("required_fields")
        if not required:
            required = sorted((task.get("oracle") or {}).keys())
        out[str(task["task_id"])] = list(required)
    return out


def parse_response_json(text: str) -> tuple[dict[str, Any], str | None]:
    try:
        value = json.loads(text or "{}")
    except json.JSONDecodeError as exc:
        return {}, f"invalid_json:{exc.msg}"
    if not isinstance(value, dict):
        return {}, "invalid_json:not_object"
    return value, None


def values_match(expected: Any, actual: Any) -> bool:
    if isinstance(expected, bool):
        if isinstance(actual, bool):
            return expected == actual
        if isinstance(actual, str):
            lowered = actual.strip().lower()
            if lowered in {"true", "false"}:
                return expected == (lowered == "true")
        return False
    if isinstance(expected, int) and not isinstance(expected, bool):
        try:
            return int(actual) == expected
        except (TypeError, ValueError):
            return False
    if isinstance(expected, float):
        try:
            return abs(float(actual) - expected) <= 1e-6
        except (TypeError, ValueError):
            return False
    return str(actual).strip() == str(expected).strip()


def parse_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def is_placeholder_response(row: dict[str, str]) -> bool:
    empty_response = row.get("response_json", "").strip() in {"", "{}"}
    no_measurements = not row.get("task_time_seconds", "").strip() and not row.get("confidence", "").strip()
    return empty_response and no_measurements


def score_response(
    row: dict[str, str],
    answer: dict[str, Any],
    required_fields: list[str],
) -> dict[str, Any]:
    response, parse_error = parse_response_json(row.get("response_json", ""))
    missing = []
    mismatched = []
    matched = []
    for field in required_fields:
        if field not in response:
            missing.append(field)
        elif values_match(answer.get(field), response[field]):
            matched.append(field)
        else:
            mismatched.append(field)
    extra_fields = sorted(set(response) - set(required_fields))
    false_positive_count = len(mismatched) + len(extra_fields)
    total = len(required_fields)
    accuracy = round(100.0 * len(matched) / total, 3) if total else 0.0
    exact = not parse_error and not missing and not mismatched and not extra_fields
    return {
        "participant_id": row.get("participant_id", ""),
        "packet_id": row.get("packet_id", ""),
        "task_id": row.get("task_id", ""),
        "condition": row.get("condition", ""),
        "task_time_seconds": parse_float(row.get("task_time_seconds", "")),
        "confidence": parse_float(row.get("confidence", "")),
        "exact": exact,
        "field_accuracy_pct": accuracy,
        "matched_fields": matched,
        "missing_fields": missing,
        "mismatched_fields": mismatched,
        "extra_fields": extra_fields,
        "false_positive_count": false_positive_count,
        "parse_error": parse_error or "",
    }


def mean(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 3) if values else None


def median(values: list[float]) -> float | None:
    return round(statistics.median(values), 3) if values else None


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_task_condition: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_condition[row["condition"]].append(row)
        by_task_condition[(row["task_id"], row["condition"])].append(row)

    def section(items: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "response_count": len(items),
            "exact_accuracy_pct": round(100.0 * sum(1 for item in items if item["exact"]) / len(items), 3) if items else None,
            "mean_field_accuracy_pct": mean([item["field_accuracy_pct"] for item in items]),
            "mean_time_seconds": mean([item["task_time_seconds"] for item in items]),
            "median_time_seconds": median([item["task_time_seconds"] for item in items]),
            "mean_confidence": mean([item["confidence"] for item in items]),
            "false_positive_count": sum(int(item["false_positive_count"]) for item in items) if items else None,
            "parse_error_count": sum(1 for item in items if item["parse_error"]) if items else None,
        }

    return {
        "overall": section(rows),
        "by_condition": {
            condition: section(items)
            for condition, items in sorted(by_condition.items())
        },
        "by_task_condition": {
            f"{task_id}/{condition}": section(items)
            for (task_id, condition), items in sorted(by_task_condition.items())
        },
        "condition_assignment_counts": dict(Counter(row["condition"] for row in rows)),
    }


def write_scored_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "participant_id",
        "packet_id",
        "task_id",
        "condition",
        "task_time_seconds",
        "confidence",
        "exact",
        "field_accuracy_pct",
        "false_positive_count",
        "parse_error",
        "missing_fields",
        "mismatched_fields",
        "extra_fields",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **{field: row.get(field, "") for field in fields},
                    "missing_fields": ";".join(row.get("missing_fields", [])),
                    "mismatched_fields": ";".join(row.get("mismatched_fields", [])),
                    "extra_fields": ";".join(row.get("extra_fields", [])),
                }
            )


def write_summary_md(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# User Task Results",
        "",
        "This report scores participant responses for C5 against the committed answer key.",
        "",
        "## Overall",
        "",
    ]
    overall = result["summary"]["overall"]
    lines.extend(
        [
            f"- Responses: {overall['response_count']}.",
            f"- Exact accuracy: {overall['exact_accuracy_pct'] if overall['exact_accuracy_pct'] is not None else 'n/a'}.",
            f"- Mean field accuracy: {overall['mean_field_accuracy_pct'] if overall['mean_field_accuracy_pct'] is not None else 'n/a'}.",
            f"- Mean time: {overall['mean_time_seconds'] if overall['mean_time_seconds'] is not None else 'n/a'} seconds.",
            f"- False positives: {overall['false_positive_count'] if overall['false_positive_count'] is not None else 'n/a'}.",
            "",
            "## Claim Boundary",
            "",
            "- This is scored evidence only when `source` points to a real participant-response file.",
            "- Pilot-scale results should guide task/instrument changes, not final user-utility claims.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle = read_json(Path(args.bundle))
    answers = load_answer_key(Path(args.answer_key))
    required = required_fields_by_task(bundle)
    response_rows = read_csv_rows(Path(args.responses))
    scorable_rows = [row for row in response_rows if not is_placeholder_response(row)]
    scored = []
    for row in scorable_rows:
        task_id = row.get("task_id", "")
        if task_id not in answers:
            raise AssertionError(f"response references unknown task_id {task_id!r}")
        scored.append(score_response(row, answers[task_id], required.get(task_id, sorted(answers[task_id]))))

    result = {
        "schema_version": 1,
        "claim": "C5",
        "status": "participant_results_scored" if scored else "participant_results_empty",
        "source": Path(args.responses).name,
        "template_row_count": len(response_rows),
        "ignored_placeholder_rows": len(response_rows) - len(scorable_rows),
        "participant_count": len({row["participant_id"] for row in scored if row["participant_id"]}),
        "response_count": len(scored),
        "task_count": len({row["task_id"] for row in scored}),
        "summary": summarize(scored),
        "scored_rows": scored,
        "claim_boundary": "C5 requires real participant responses and adequate sample size before becoming supported",
    }
    (out_dir / "user-task-results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_scored_csv(out_dir / "user-task-results.csv", scored)
    write_summary_md(out_dir / "user-task-results.md", result)
    print(json.dumps({key: result[key] for key in ("status", "participant_count", "response_count", "task_count")}, indent=2))
    return result


def build_parser() -> argparse.ArgumentParser:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--responses", required=True, help="CSV collected from user-task-response-template.csv")
    parser.add_argument("--bundle", default=str(here / "out" / "user-task-benchmark.json"))
    parser.add_argument("--answer-key", default=str(here / "out" / "user-task-answer-key.csv"))
    parser.add_argument("--out", default=str(here / "out"))
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
