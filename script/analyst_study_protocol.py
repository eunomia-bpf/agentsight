#!/usr/bin/env python3
"""R315: build a controlled analyst-study protocol from existing case packets.

R315 does not fetch datasets, rerun profilers, or execute a human/agent study.
It turns the existing R305 visible packets and hidden answer key into a
reproducible study package: visible task packets, a hidden scoring key, a
balanced assignment table, and a reviewer-facing protocol. The purpose is to
make the remaining user-utility gate executable without claiming that the gate
has already passed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import subprocess
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "analyst-study-protocol-r315"
SOURCE_PATHS = {
    "r305_visible_packets": OUT_ROOT
    / "operation-case-baseline-r305"
    / "visible-case-packets.json",
    "r305_answer_key": OUT_ROOT / "operation-case-baseline-r305" / "answer-key.json",
    "r305_case_baseline": OUT_ROOT
    / "operation-case-baseline-r305"
    / "case-baseline-report.json",
    "r308_outcome": OUT_ROOT
    / "operation-analyst-outcome-r308"
    / "analyst-outcome-report.json",
    "r313_frontier": OUT_ROOT
    / "operation-view-frontier-r313"
    / "view-frontier-report.json",
}

VIEWS = ["flat", "fixed_session", "operation_stack"]
DEFAULT_PARTICIPANTS = 24
RANDOMIZATION_SEED = "agentsight-r315-v1"
WITHHELD_ORACLE_FIELDS = {
    "looping",
    "side_effect",
    "safety",
    "step_correct",
    "step_redundant",
    "human_group",
    "group_pattern",
    "group_position",
    "positive_operations",
    "positive_rate",
    "positive_recall",
    "positive_precision",
    "positive_lift",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--participants", type=int, default=DEFAULT_PARTICIPANTS)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SystemExit(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def git_check(description: str, args: list[str], path: Path) -> None:
    result = subprocess.run(
        ["git", *args, "--", rel(path)],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        suffix = f": {detail}" if detail else ""
        raise SystemExit(f"{rel(path)} failed source check: {description}{suffix}")


def ensure_sources_tracked_clean(paths: list[Path]) -> None:
    for path in paths:
        if not path.exists():
            raise SystemExit(f"missing source artifact {rel(path)}")
        git_check("source artifact is not git-tracked", ["ls-files", "--error-unmatch"], path)
        git_check("source artifact has unstaged changes", ["diff", "--quiet"], path)
        git_check("source artifact has staged changes", ["diff", "--cached", "--quiet"], path)


def compact_group(group: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "group_id",
        "rank",
        "operations",
        "sessions",
        "stack",
        "stack_frames",
        "visible_features",
        "field_examples",
        "operation_examples",
        "session_examples",
    }
    compact = {key: value for key, value in group.items() if key in allowed}
    compact["operation_examples"] = compact.get("operation_examples", [])[:3]
    compact["session_examples"] = compact.get("session_examples", [])[:3]
    return compact


def visible_packet_cases(visible: dict[str, Any]) -> list[dict[str, Any]]:
    cases = []
    for case in visible["cases"]:
        packet_id = f"{case['task']}::{case['view']}"
        cases.append(
            {
                "packet_id": packet_id,
                "task": case["task"],
                "view": case["view"],
                "dataset": case["dataset"],
                "query_family": case["query_family"],
                "problem": case["problem"],
                "ranker": case["ranker"],
                "response_prompt": (
                    "Rank up to three group_id values that most likely contain "
                    "the target phenomenon. For each selected group, give a "
                    "1-5 confidence score and cite visible fields that justify "
                    "the choice."
                ),
                "groups": [compact_group(group) for group in case["groups"]],
            }
        )
    return cases


def answer_cases(answer: dict[str, Any]) -> list[dict[str, Any]]:
    hidden = []
    for case in answer["cases"]:
        packet_id = f"{case['task']}::{case['view']}"
        hidden.append(
            {
                "packet_id": packet_id,
                "task": case["task"],
                "view": case["view"],
                "dataset": case["dataset"],
                "oracle_field": case["oracle_field"],
                "positive_values": case["positive_values"],
                "score": case["score"],
                "groups": case["groups"],
            }
        )
    return hidden


def sorted_tasks(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for case in cases:
        seen.setdefault(
            case["task"],
            {
                "task": case["task"],
                "dataset": case["dataset"],
                "query_family": case["query_family"],
                "problem": case["problem"],
            },
        )
    return [seen[key] for key in sorted(seen)]


def stable_task_order(participant_id: str, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(task: dict[str, Any]) -> str:
        text = f"{RANDOMIZATION_SEED}:{participant_id}:{task['task']}"
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    return sorted(tasks, key=key)


def build_assignments(tasks: list[dict[str, Any]], participants: int) -> list[dict[str, Any]]:
    if participants <= 0:
        raise SystemExit("--participants must be positive")
    if participants % len(VIEWS) != 0:
        raise SystemExit(
            f"--participants must be a multiple of {len(VIEWS)} to balance task-view cells"
        )
    assignments: list[dict[str, Any]] = []
    task_index = {task["task"]: index for index, task in enumerate(sorted(tasks, key=lambda row: row["task"]))}
    for participant_zero in range(participants):
        participant_id = f"P{participant_zero + 1:02d}"
        for order, task in enumerate(stable_task_order(participant_id, tasks), start=1):
            view = VIEWS[(task_index[task["task"]] + participant_zero) % len(VIEWS)]
            assignments.append(
                {
                    "participant_id": participant_id,
                    "trial_order": order,
                    "task": task["task"],
                    "view": view,
                    "packet_id": f"{task['task']}::{view}",
                    "dataset": task["dataset"],
                    "query_family": task["query_family"],
                    "problem": task["problem"],
                    "response_form": "rank_up_to_3_groups_with_confidence_and_visible_evidence",
                }
            )
    return sorted(assignments, key=lambda row: (row["participant_id"], row["trial_order"]))


def assignment_balance(assignments: list[dict[str, Any]]) -> dict[str, Any]:
    by_task_view: dict[str, dict[str, int]] = {}
    by_participant: dict[str, dict[str, int]] = {}
    for row in assignments:
        by_task_view.setdefault(row["task"], {view: 0 for view in VIEWS})
        by_task_view[row["task"]][row["view"]] += 1
        by_participant.setdefault(row["participant_id"], {view: 0 for view in VIEWS})
        by_participant[row["participant_id"]][row["view"]] += 1
    counts = [count for per_task in by_task_view.values() for count in per_task.values()]
    return {
        "participants": len(by_participant),
        "trials": len(assignments),
        "tasks": len(by_task_view),
        "views": VIEWS,
        "task_view_min_count": min(counts) if counts else 0,
        "task_view_max_count": max(counts) if counts else 0,
        "participant_view_counts": by_participant,
        "task_view_counts": by_task_view,
        "balanced": bool(counts) and min(counts) == max(counts),
    }


def leakage_checks(visible_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for case in visible_cases:
        group_key_hits: set[str] = set()
        group_text_hits: set[str] = set()
        for group in case["groups"]:
            group_key_hits.update(set(group) & WITHHELD_ORACLE_FIELDS)
            serialized = json.dumps(group, sort_keys=True).lower()
            for field in WITHHELD_ORACLE_FIELDS:
                if field.lower() in serialized:
                    group_text_hits.add(field)
        allowed_task_context = {"looping", "side_effect", "safety"}
        unallowed_text_hits = sorted(group_text_hits - allowed_task_context)
        rows.append(
            {
                "packet_id": case["packet_id"],
                "status": "pass" if not group_key_hits and not unallowed_text_hits else "fail",
                "oracle_key_hits": sorted(group_key_hits),
                "oracle_text_hits": unallowed_text_hits,
            }
        )
    return rows


def status_from_rows(rows: list[dict[str, Any]]) -> str:
    return "pass" if all(row["status"] == "pass" for row in rows) else "fail"


def study_protocol(
    visible_cases: list[dict[str, Any]],
    hidden_cases: list[dict[str, Any]],
    assignments: list[dict[str, Any]],
    r305: dict[str, Any],
    r308: dict[str, Any],
    r313: dict[str, Any],
) -> dict[str, Any]:
    tasks = sorted_tasks(visible_cases)
    leakage = leakage_checks(visible_cases)
    balance = assignment_balance(assignments)
    selected_work = [
        case["score"]["inspected_operation_fraction"]
        for case in hidden_cases
        if case["view"] == "operation_stack"
    ]
    return {
        "schema": "agentsight.analyst-study-protocol.v1",
        "run_id": "R315",
        "commit": git_output(["rev-parse", "HEAD"]),
        "input_policy": {
            "dataset_sync": "none",
            "profiler_rerun": "none",
            "source_artifacts": {key: rel(path) for key, path in SOURCE_PATHS.items()},
            "purpose": "controlled analyst-study protocol only; no human or agent analyst result",
        },
        "profiler_abstractions": ["operation", "operation stack"],
        "not_a_human_study_result": True,
        "study_design": {
            "design": "balanced within-subject task assignment with one view per task per participant",
            "participants": balance["participants"],
            "trials": balance["trials"],
            "tasks": len(tasks),
            "views": VIEWS,
            "randomization_seed": RANDOMIZATION_SEED,
            "randomization_unit": "participant x task",
            "task_repetition_policy": (
                "Each participant sees each problem once under one view; "
                "view assignment rotates across participants so each task-view "
                "cell has equal replication."
            ),
            "response_fields": [
                "selected_group_id_rank_1",
                "selected_group_id_rank_2",
                "selected_group_id_rank_3",
                "confidence_1_to_5",
                "visible_evidence_fields",
                "time_seconds",
            ],
            "primary_endpoint": "whether the analyst selects at least one hidden-positive or high-lift group before exhausting the visible packet",
            "secondary_endpoints": [
                "selected positive recall",
                "selected positive precision",
                "selected operation work fraction",
                "time to first accepted evidence",
                "confidence calibration against hidden positive rate",
            ],
            "analysis_plan": (
                "Compare flat, fixed-session, and operation-stack views with "
                "task and participant effects. Report per-task outcomes and "
                "retain counterexamples where fixed-session is cheaper or flat "
                "is complete but non-selective."
            ),
        },
        "tasks": tasks,
        "assignment_balance": balance,
        "leakage_checks": {
            "status": status_from_rows(leakage),
            "withheld_oracle_fields": sorted(WITHHELD_ORACLE_FIELDS),
            "packet_checks": leakage,
        },
        "expected_automated_context": {
            "r305_by_view": r305["summary"]["by_view"],
            "r308_by_view": r308["summary"]["by_view"],
            "r313_frontier_summary": r313["summary"],
            "operation_stack_median_selected_work": round(float(median(selected_work)), 4),
        },
        "claim_scope": {
            "supports_now": (
                "R315 supports readiness for a controlled human/agent analyst "
                "study over existing label-hidden packets."
            ),
            "does_not_support": [
                "developer productivity improvement",
                "time-to-answer improvement",
                "human accuracy improvement",
                "automatic anomaly detection",
                "single-view dominance",
            ],
            "promotion_gate": (
                "Only after analysts complete the visible packets and hidden "
                "answer-key scoring shows better accuracy/work/time tradeoffs "
                "can the paper promote C4 beyond automated inspectability."
            ),
        },
    }


def write_assignments_csv(path: Path, assignments: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "participant_id",
            "trial_order",
            "task",
            "view",
            "packet_id",
            "dataset",
            "query_family",
            "problem",
            "response_form",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(assignments)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    design = payload["study_design"]
    balance = payload["assignment_balance"]
    leakage = payload["leakage_checks"]
    claim = payload["claim_scope"]
    lines = [
        "# Analyst Study Protocol R315",
        "",
        "R315 packages the existing R305 visible case packets and hidden answer key into a controlled analyst-study protocol. It does not sync datasets, rerun profilers, or report human/agent analyst results.",
        "",
        "## Status",
        "",
        f"- Protocol status: ready_to_run.",
        f"- Participants in assignment table: {design['participants']}.",
        f"- Trials: {design['trials']}.",
        f"- Tasks: {design['tasks']}.",
        f"- Views: {', '.join(design['views'])}.",
        f"- Balanced task-view cells: {balance['balanced']} ({balance['task_view_min_count']} to {balance['task_view_max_count']} trials per task-view cell).",
        f"- Leakage check: {leakage['status']}.",
        "",
        "## Analyst Task",
        "",
        "For each visible packet, the analyst ranks up to three `group_id` values that appear most likely to contain the target phenomenon, assigns confidence, cites visible fields, and records time. The hidden answer key scores selected groups after the response is locked.",
        "",
        "## Endpoints",
        "",
        f"- Primary endpoint: {design['primary_endpoint']}.",
        "- Secondary endpoints: " + "; ".join(design["secondary_endpoints"]) + ".",
        "",
        "## Claim Scope",
        "",
        f"- Supports now: {claim['supports_now']}",
        "- Does not support: " + "; ".join(claim["does_not_support"]) + ".",
        f"- Promotion gate: {claim['promotion_gate']}",
        "",
        "## Tasks",
        "",
        "| Task | Dataset | Query family | Problem |",
        "|---|---|---|---|",
    ]
    for task in payload["tasks"]:
        lines.append(
            f"| {task['task']} | {task['dataset']} | {task['query_family']} | {task['problem']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    task_rows = "\n".join(
        "<tr>"
        f"<th>{html.escape(task['task'])}</th>"
        f"<td>{html.escape(task['dataset'])}</td>"
        f"<td>{html.escape(task['query_family'])}</td>"
        f"<td>{html.escape(task['problem'])}</td>"
        "</tr>"
        for task in payload["tasks"]
    )
    path.write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Analyst Study Protocol R315</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }
    table { border-collapse: collapse; margin-top: 1rem; max-width: 1100px; }
    th, td { border: 1px solid #d8dee9; padding: 0.55rem 0.75rem; text-align: left; vertical-align: top; }
    th { background: #f6f8fa; }
  </style>
</head>
<body>
  <h1>Analyst Study Protocol R315</h1>
  <p>R315 is a ready-to-run protocol over existing visible packets. It is not a human or agent analyst result.</p>
  <ul>
"""
        + f"    <li>Participants: {payload['study_design']['participants']}</li>\n"
        + f"    <li>Trials: {payload['study_design']['trials']}</li>\n"
        + f"    <li>Leakage check: {html.escape(payload['leakage_checks']['status'])}</li>\n"
        + "  </ul>\n"
        + "  <h2>Tasks</h2>\n"
        + "  <table><tr><th>Task</th><th>Dataset</th><th>Query family</th><th>Problem</th></tr>\n"
        + task_rows
        + "\n  </table>\n</body>\n</html>\n",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    ensure_sources_tracked_clean(list(SOURCE_PATHS.values()))

    visible = load_json(SOURCE_PATHS["r305_visible_packets"])
    answer = load_json(SOURCE_PATHS["r305_answer_key"])
    r305 = load_json(SOURCE_PATHS["r305_case_baseline"])
    r308 = load_json(SOURCE_PATHS["r308_outcome"])
    r313 = load_json(SOURCE_PATHS["r313_frontier"])

    visible_cases = visible_packet_cases(visible)
    hidden_cases = answer_cases(answer)
    tasks = sorted_tasks(visible_cases)
    assignments = build_assignments(tasks, args.participants)
    protocol = study_protocol(visible_cases, hidden_cases, assignments, r305, r308, r313)

    protocol_path = args.out_dir / "study-protocol.json"
    visible_path = args.out_dir / "visible-study-packets.json"
    hidden_path = args.out_dir / "hidden-scoring-key.json"
    assignment_path = args.out_dir / "assignment.csv"
    markdown_path = args.out_dir / "study-protocol.md"
    html_path = args.out_dir / "index.html"
    run_result_path = args.out_dir / "run-result.json"

    protocol["outputs"] = {
        "protocol": rel(protocol_path),
        "visible_packets": rel(visible_path),
        "hidden_scoring_key": rel(hidden_path),
        "assignment_csv": rel(assignment_path),
        "markdown": rel(markdown_path),
        "html": rel(html_path),
        "run_result": rel(run_result_path),
    }
    write_json(protocol_path, protocol)
    write_json(
        visible_path,
        {
            "schema": "agentsight.visible-analyst-study-packets.v1",
            "run_id": "R315",
            "visible_only": True,
            "source": rel(SOURCE_PATHS["r305_visible_packets"]),
            "withheld_field_policy": visible["withheld_field_policy"],
            "visible_fields": visible["visible_fields"],
            "cases": visible_cases,
        },
    )
    write_json(
        hidden_path,
        {
            "schema": "agentsight.hidden-analyst-study-key.v1",
            "run_id": "R315",
            "hidden": True,
            "source": rel(SOURCE_PATHS["r305_answer_key"]),
            "scoring_rule": "score selected group ids against hidden positive operation counts and positive lift",
            "cases": hidden_cases,
        },
    )
    write_assignments_csv(assignment_path, assignments)
    write_markdown(markdown_path, protocol)
    write_html(html_path, protocol)
    write_json(
        run_result_path,
        {
            "run_id": "R315",
            "status": "ok",
            "protocol_status": "ready_to_run",
            "not_a_human_study_result": True,
            "participants": protocol["study_design"]["participants"],
            "trials": protocol["study_design"]["trials"],
            "tasks": protocol["study_design"]["tasks"],
            "views": protocol["study_design"]["views"],
            "assignment_balanced": protocol["assignment_balance"]["balanced"],
            "leakage_status": protocol["leakage_checks"]["status"],
            "protocol": rel(protocol_path),
            "visible_packets": rel(visible_path),
            "hidden_scoring_key": rel(hidden_path),
            "assignment_csv": rel(assignment_path),
            "markdown": rel(markdown_path),
            "html": rel(html_path),
        },
    )
    print(json.dumps(load_json(run_result_path), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
