#!/usr/bin/env python3
"""Freeze the R142/R151 C5 user-task preregistration artifact.

The preregistration is intentionally derived from the generated task bundle,
assignment template, answer key, and scorer constants. This keeps the protocol
auditable and prevents the paper text from drifting away from the executable
claim gate.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from score_user_task_results import REQUIRED_RESPONSE_FIELDS, claim_thresholds


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_BUNDLE = SCRIPT_DIR / "out" / "user-task-benchmark.json"
DEFAULT_ASSIGNMENTS = SCRIPT_DIR / "out" / "user-task-assignments.csv"
DEFAULT_ANSWER_KEY = SCRIPT_DIR / "out" / "user-task-answer-key.csv"
DEFAULT_RESPONSE_TEMPLATE = SCRIPT_DIR / "out" / "user-task-response-template.csv"
DEFAULT_OUT_JSON = SCRIPT_DIR / "out" / "user-task-preregistration-r142.json"
DEFAULT_OUT_MD = SCRIPT_DIR / "out" / "user-task-preregistration-r142.md"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def task_summary(bundle: dict[str, Any]) -> dict[str, Any]:
    tasks = bundle.get("tasks", [])
    roles = Counter(str(task.get("analysis_role") or "") for task in tasks)
    primary_ids = [str(task["task_id"]) for task in tasks if task.get("analysis_role") == "primary_utility"]
    limitation_ids = [str(task["task_id"]) for task in tasks if task.get("analysis_role") != "primary_utility"]
    return {
        "task_count": len(tasks),
        "primary_utility_task_count": len(primary_ids),
        "limitation_or_comprehension_task_count": len(limitation_ids),
        "analysis_role_counts": dict(sorted(roles.items())),
        "primary_task_ids": primary_ids,
        "nonprimary_task_ids": limitation_ids,
        "all_task_ids": [str(task["task_id"]) for task in tasks],
    }


def assignment_summary(assignments: list[dict[str, str]], condition_order: list[str]) -> dict[str, Any]:
    rows_by_participant: dict[str, int] = Counter(row["participant_id"] for row in assignments)
    conditions_by_task: dict[str, set[str]] = defaultdict(set)
    rows_by_task: dict[str, int] = Counter()
    order_indices_by_participant: dict[str, list[int]] = defaultdict(list)
    for row in assignments:
        task_id = row["task_id"]
        participant_id = row["participant_id"]
        rows_by_task[task_id] += 1
        conditions_by_task[task_id].add(row["condition"])
        try:
            order_indices_by_participant[participant_id].append(int(row["order_index"]))
        except ValueError:
            order_indices_by_participant[participant_id].append(-1)

    expected_conditions = set(condition_order)
    complete_task_condition_coverage = all(
        conditions == expected_conditions
        for conditions in conditions_by_task.values()
    )
    contiguous_order_indices = all(
        sorted(indices) == list(range(1, len(indices) + 1))
        for indices in order_indices_by_participant.values()
    )
    return {
        "assignment_row_count": len(assignments),
        "participant_ids": sorted(rows_by_participant),
        "participant_count": len(rows_by_participant),
        "rows_per_participant": dict(sorted(rows_by_participant.items())),
        "rows_per_task": dict(sorted(rows_by_task.items())),
        "complete_task_condition_coverage": complete_task_condition_coverage,
        "conditions_per_task": {
            task_id: sorted(conditions)
            for task_id, conditions in sorted(conditions_by_task.items())
        },
        "contiguous_order_indices_per_participant": contiguous_order_indices,
    }


def validate_preregistration(
    bundle: dict[str, Any],
    assignments: list[dict[str, str]],
    answer_rows: list[dict[str, str]],
    response_rows: list[dict[str, str]],
    response_fields: list[str],
) -> list[str]:
    errors = []
    thresholds = claim_thresholds()
    condition_order = list(bundle.get("condition_order") or [])
    task_ids = {str(task["task_id"]) for task in bundle.get("tasks", [])}
    assignment_task_ids = {row.get("task_id", "") for row in assignments}
    answer_task_ids = {row.get("task_id", "") for row in answer_rows}
    response_task_ids = {row.get("task_id", "") for row in response_rows}
    expected_conditions = set([thresholds["semantic_condition"], *thresholds["baseline_conditions"]])
    if set(condition_order) != expected_conditions:
        errors.append("bundle condition_order does not match scorer threshold conditions")
    if "event-count-proxy" not in condition_order:
        errors.append("R142 preregistration must include event-count-proxy")
    if "span-duration" in condition_order:
        errors.append("R142 preregistration must not call the event-count proxy span-duration")
    missing_response_fields = sorted(REQUIRED_RESPONSE_FIELDS - set(response_fields))
    if missing_response_fields:
        errors.append(f"response template is missing required fields: {missing_response_fields}")
    if assignment_task_ids != task_ids:
        errors.append("assignment task ids do not match bundle task ids")
    if answer_task_ids != task_ids:
        errors.append("answer-key task ids do not match bundle task ids")
    if response_task_ids != task_ids:
        errors.append("response-template task ids do not match bundle task ids")
    if len(response_rows) != len(assignments):
        errors.append("response-template row count does not match assignment row count")
    summary = task_summary(bundle)
    if summary["primary_utility_task_count"] < thresholds["min_task_pairs_for_claim"]:
        errors.append("primary utility task count is below the scorer's claim threshold")
    assignment = assignment_summary(assignments, condition_order)
    if not assignment["complete_task_condition_coverage"]:
        errors.append("assignments do not cover every condition once per task")
    if not assignment["contiguous_order_indices_per_participant"]:
        errors.append("assignment order indices are not contiguous per participant")
    if assignment["participant_count"] < thresholds["pilot_min_participants"]:
        errors.append("pilot assignment template has too few participants")
    return errors


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    bundle = read_json(args.bundle)
    assignments, assignment_fields = read_csv_rows(args.assignments)
    answer_rows, answer_fields = read_csv_rows(args.answer_key)
    response_rows, response_fields = read_csv_rows(args.response_template)
    thresholds = claim_thresholds()
    condition_order = list(bundle.get("condition_order") or [])
    tasks = task_summary(bundle)
    assignments_summary = assignment_summary(assignments, condition_order)
    validation_errors = validate_preregistration(bundle, assignments, answer_rows, response_rows, response_fields)
    status = "frozen_before_collection" if not validation_errors else "invalid"
    return {
        "schema_version": 1,
        "run_id": "R142-preregistration",
        "claim": "C5",
        "status": status,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source_files": {
            "bundle": {"path": rel(args.bundle), "sha256": file_sha256(args.bundle)},
            "assignments": {"path": rel(args.assignments), "sha256": file_sha256(args.assignments)},
            "answer_key": {"path": rel(args.answer_key), "sha256": file_sha256(args.answer_key)},
            "response_template": {"path": rel(args.response_template), "sha256": file_sha256(args.response_template)},
            "scorer": {"path": rel(SCRIPT_DIR / "score_user_task_results.py"), "sha256": file_sha256(SCRIPT_DIR / "score_user_task_results.py")},
        },
        "tasks": tasks,
        "conditions": {
            "semantic_condition": thresholds["semantic_condition"],
            "baseline_conditions": thresholds["baseline_conditions"],
            "condition_order": condition_order,
            "baseline_boundary": (
                "event-count-proxy is an event/count-weight view, not a span-duration baseline; "
                "a true span-duration baseline requires measured timestamp/duration reconstruction."
            ),
        },
        "response_unit": "one participant x task x condition row",
        "response_schema": {
            "required_fields": sorted(REQUIRED_RESPONSE_FIELDS),
            "template_fields": response_fields,
            "confidence_range": [1, 5],
            "task_time_seconds": "finite positive seconds",
            "response_json": "JSON object containing each task's required answer fields",
        },
        "assignment_design": assignments_summary,
        "analysis_plan": {
            "primary_task_role": thresholds["primary_role"],
            "primary_task_ids": tasks["primary_task_ids"],
            "pilot_min_participants": thresholds["pilot_min_participants"],
            "paper_min_participants": thresholds["min_participants_for_claim"],
            "minimum_primary_pairs_per_baseline": thresholds["min_task_pairs_for_claim"],
            "primary_endpoints": ["exact_accuracy_pct", "log_time_seconds"],
            "secondary_metrics": ["field_accuracy_pct", "confidence"],
            "guardrail": "false_positive_response_share_pct",
            "diagnostic_test": thresholds["diagnostic_test"],
            "paper_scale_test": thresholds["paper_scale_test"],
            "holm_family": thresholds["holm_correction_family"],
            "monte_carlo_permutations": thresholds["monte_carlo_permutations"],
            "success_rule": (
                "Semantic-stack must beat every baseline on primary utility tasks by >=10 pp exact accuracy "
                "or >=20% median task-time reduction, with Holm-corrected p<=0.05 and no >5 pp "
                "false-positive increase."
            ),
        },
        "exclusion_rules": [
            "Reject a response CSV with missing required columns.",
            "Reject duplicate participant/task/condition/packet assignment rows.",
            "Reject rows outside the committed assignment file when assignments are provided.",
            "Reject partial real-response files once any assigned row is scorable.",
            "Reject nonpositive or non-finite task_time_seconds.",
            "Reject confidence values outside 1..5.",
            "Do not drop tasks or participants after seeing outcomes unless the exclusion is documented before scoring.",
        ],
        "claim_boundaries": [
            "Pilot results can validate task wording and instrumentation but cannot support paper-scale C5.",
            "C5 remains unsupported while user-task-results.json is participant_results_empty.",
            "Subagent, LLM, or author-filled mock responses do not count as participant evidence.",
            "A true span-duration comparison must be registered as a new condition if reconstructed later.",
        ],
        "validation": {
            "status": "ok" if not validation_errors else "fail",
            "errors": validation_errors,
            "answer_key_row_count": len(answer_rows),
            "answer_key_fields": answer_fields,
            "assignment_fields": assignment_fields,
            "response_template_row_count": len(response_rows),
        },
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": file_sha256(Path(__file__).resolve()),
        },
    }


def write_json(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def write_markdown(path: Path, manifest: dict[str, Any]) -> None:
    conditions = manifest["conditions"]
    plan = manifest["analysis_plan"]
    validation = manifest["validation"]
    lines = [
        "# R142 User-Task Preregistration",
        "",
        f"Status: `{manifest['status']}`",
        f"Generated: {manifest['generated_at']}",
        "",
        "## Frozen Inputs",
        "",
    ]
    for name, info in manifest["source_files"].items():
        lines.append(f"- `{name}`: `{info['path']}` (`{info['sha256'][:12]}`)")
    lines.extend(
        [
            "",
            "## Conditions",
            "",
            f"- Semantic condition: `{conditions['semantic_condition']}`.",
            f"- Baselines: {', '.join(f'`{item}`' for item in conditions['baseline_conditions'])}.",
            f"- Order in packets: {', '.join(f'`{item}`' for item in conditions['condition_order'])}.",
            f"- Boundary: {conditions['baseline_boundary']}",
            "",
            "## Tasks And Assignment",
            "",
            f"- Tasks: {manifest['tasks']['task_count']}.",
            f"- Primary utility tasks: {manifest['tasks']['primary_utility_task_count']} ({', '.join(manifest['tasks']['primary_task_ids'])}).",
            f"- Pilot participants in assignment template: {manifest['assignment_design']['participant_count']}.",
            f"- Assignment rows: {manifest['assignment_design']['assignment_row_count']}.",
            f"- Complete task-condition coverage: {manifest['assignment_design']['complete_task_condition_coverage']}.",
            "",
            "## Analysis Plan",
            "",
            f"- Response unit: {manifest['response_unit']}.",
            f"- Pilot minimum participants: {plan['pilot_min_participants']}.",
            f"- Paper minimum participants: {plan['paper_min_participants']}.",
            f"- Minimum primary pairs per baseline: {plan['minimum_primary_pairs_per_baseline']}.",
            f"- Primary endpoints: {', '.join(f'`{item}`' for item in plan['primary_endpoints'])}.",
            f"- Guardrail: `{plan['guardrail']}`.",
            f"- Diagnostic test: {plan['diagnostic_test']}.",
            f"- Paper-scale test: {plan['paper_scale_test']}.",
            f"- Holm family: {plan['holm_family']}.",
            f"- Success rule: {plan['success_rule']}",
            "",
            "## Exclusion Rules",
            "",
        ]
    )
    lines.extend(f"- {rule}" for rule in manifest["exclusion_rules"])
    lines.extend(
        [
            "",
            "## Claim Boundaries",
            "",
        ]
    )
    lines.extend(f"- {rule}" for rule in manifest["claim_boundaries"])
    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- Status: `{validation['status']}`.",
            f"- Errors: {validation['errors'] if validation['errors'] else 'none'}.",
            f"- Answer-key rows: {validation['answer_key_row_count']}.",
            f"- Response-template rows: {validation['response_template_row_count']}.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    manifest = build_manifest(args)
    write_json(args.out_json, manifest)
    write_markdown(args.out_md, manifest)
    if manifest["validation"]["status"] != "ok":
        raise AssertionError(f"invalid preregistration: {manifest['validation']['errors']}")
    print(json.dumps({"status": manifest["status"], "tasks": manifest["tasks"]["task_count"], "conditions": manifest["conditions"]["condition_order"]}, indent=2))
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--assignments", type=Path, default=DEFAULT_ASSIGNMENTS)
    parser.add_argument("--answer-key", type=Path, default=DEFAULT_ANSWER_KEY)
    parser.add_argument("--response-template", type=Path, default=DEFAULT_RESPONSE_TEMPLATE)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
