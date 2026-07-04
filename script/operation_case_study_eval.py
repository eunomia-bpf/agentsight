#!/usr/bin/env python3
"""Build reviewer-facing case-study packets from existing labeled operations.

R304 turns the R300-R302 automated utility proxies into concrete cases. It
does not fetch data and it does not introduce a new profiler object: every case
is an operation-stack group ranked by a visible-field policy. Oracle labels are
kept in a separate answer key and used only for scoring after packet creation.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-case-study-r304"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_analyst_ranking_eval as r302  # noqa: E402
import operation_query_utility_eval as r300  # noqa: E402

CASE_GROUPS_PER_TASK = 5
EXAMPLES_PER_GROUP = 3

VISIBLE_OPERATION_FIELDS = [
    "dataset",
    "benchmark",
    "source",
    "agent",
    "environment",
    "app",
    "op",
    "phase",
    "action",
    "tool",
    "status",
    "repeat_signal",
    "repeat_state",
    "task",
    "step",
    "turn",
]

EXTRA_HIDDEN_FIELDS = {
    "attack",
    "attack_type",
    "reward",
    "alignment_score",
    "efficiency_score",
    "task_difficulty",
}
HIDDEN_FIELDS = set(r302.HIDDEN_FIELDS) | EXTRA_HIDDEN_FIELDS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--groups-per-task", type=int, default=CASE_GROUPS_PER_TASK)
    parser.add_argument("--examples-per-group", type=int, default=EXAMPLES_PER_GROUP)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def short_hash(text: str, length: int = 12) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:length]


def stack_frames(stack: str) -> list[dict[str, str]]:
    frames = []
    for frame in stack.split(";"):
        if ":" not in frame:
            continue
        field, value = frame.split(":", 1)
        frames.append({"field": field, "value": value})
    return frames


def group_task_operations(
    task: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    operations = r300.load_task_operations(task)
    stack = r300.stack_for_view(task, "operation_stack")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        grouped[r302.stack_label(operation["fields"], stack)].append(operation)

    groups = []
    total_ops = 0
    total_positive = 0
    for stack_key, rows in grouped.items():
        operations_in_group = sum(int(operation["value"]) for operation in rows)
        positives = sum(
            int(operation["value"])
            for operation in rows
            if operation["fields"].get("target_positive") == "positive"
        )
        sessions = sorted({operation["fields"].get("session", "unknown") for operation in rows})
        total_ops += operations_in_group
        total_positive += positives
        groups.append(
            {
                "stack": stack_key,
                "stack_frames": stack_frames(stack_key),
                "operations": operations_in_group,
                "positives": positives,
                "sessions": len(sessions),
                "session_examples": [short_hash(session) for session in sessions[:5]],
                "features": r302.visible_features(rows),
                "field_examples": visible_field_examples(rows),
                "operation_examples": visible_operation_examples(rows),
            }
        )
    summary = {
        "operations": total_ops,
        "positives": total_positive,
        "prevalence": total_positive / total_ops if total_ops else 0.0,
        "groups": len(groups),
    }
    return groups, summary


def visible_field_examples(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    counters: dict[str, Counter[str]] = {field: Counter() for field in VISIBLE_OPERATION_FIELDS}
    for operation in rows:
        fields = operation["fields"]
        weight = int(operation["value"])
        for field, counter in counters.items():
            value = fields.get(field)
            if value:
                counter[str(value)] += weight
    return {
        field: [{"value": value, "operations": count} for value, count in counter.most_common(3)]
        for field, counter in counters.items()
        if counter
    }


def visible_operation_examples(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples = []
    seen = set()
    for operation in sorted(rows, key=lambda row: row.get("_source_line", 0)):
        fields = operation["fields"]
        signature = tuple((field, fields.get(field, "")) for field in VISIBLE_OPERATION_FIELDS)
        if signature in seen:
            continue
        seen.add(signature)
        example = {
            field: fields[field]
            for field in VISIBLE_OPERATION_FIELDS
            if field in fields and field not in HIDDEN_FIELDS
        }
        session = fields.get("session")
        if session:
            example["session_hash"] = short_hash(session)
        examples.append(example)
        if len(examples) >= EXAMPLES_PER_GROUP:
            break
    return examples


def score_selected(
    selected: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    inspected_ops = sum(group["operations"] for group in selected)
    positives = sum(group["positives"] for group in selected)
    total_ops = summary["operations"]
    total_positive = summary["positives"]
    prevalence = summary["prevalence"]
    precision = positives / inspected_ops if inspected_ops else 0.0
    return {
        "groups": len(selected),
        "inspected_operations": inspected_ops,
        "inspected_operation_fraction": inspected_ops / total_ops if total_ops else 0.0,
        "positive_operations": positives,
        "positive_recall": positives / total_positive if total_positive else 0.0,
        "positive_precision": precision,
        "positive_lift": precision / prevalence if prevalence else 0.0,
    }


def visible_group(group: dict[str, Any], rank: int) -> dict[str, Any]:
    return {
        "rank": rank,
        "group_id": short_hash(group["stack"]),
        "stack": group["stack"],
        "stack_frames": group["stack_frames"],
        "operations": group["operations"],
        "sessions": group["sessions"],
        "session_examples": group["session_examples"],
        "visible_features": group["features"],
        "field_examples": group["field_examples"],
        "operation_examples": group["operation_examples"],
    }


def answer_group(group: dict[str, Any], rank: int) -> dict[str, Any]:
    operations = group["operations"]
    positives = group["positives"]
    return {
        "rank": rank,
        "group_id": short_hash(group["stack"]),
        "operations": operations,
        "positive_operations": positives,
        "positive_rate": positives / operations if operations else 0.0,
    }


def build_cases(groups_per_task: int) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    visible_cases = []
    answer_cases = []
    task_scores = []
    for task in r300.TASKS:
        groups, summary = group_task_operations(task)
        ranked = sorted(
            groups,
            key=lambda group: r302.rank_score(group, task, "query_aware"),
            reverse=True,
        )
        selected = ranked[:groups_per_task]
        score = score_selected(selected, summary)
        visible_cases.append(
            {
                "task": task["id"],
                "dataset": task["dataset"],
                "query_family": task["query_family"],
                "problem": task["problem"],
                "ranker": "query_aware",
                "groups": [visible_group(group, index) for index, group in enumerate(selected, 1)],
            }
        )
        answer_cases.append(
            {
                "task": task["id"],
                "dataset": task["dataset"],
                "oracle_field": task["oracle_field"],
                "positive_values": sorted(task["positive_values"]),
                "score": score,
                "groups": [answer_group(group, index) for index, group in enumerate(selected, 1)],
            }
        )
        task_scores.append(
            {
                "task": task["id"],
                "dataset": task["dataset"],
                "query_family": task["query_family"],
                "problem": task["problem"],
                "operation_stack_groups": summary["groups"],
                "operations": summary["operations"],
                "positives": summary["positives"],
                **{key: round(value, 4) if isinstance(value, float) else value for key, value in score.items()},
            }
        )

    summary = summarize_task_scores(task_scores)
    visible_packet = {
        "run_id": "R304",
        "purpose": "label-hidden reviewer case packet over operation-stack groups",
        "input_policy": "no dataset sync; reuses existing R300 task operations and R302 query-aware ranking",
        "visible_fields": VISIBLE_OPERATION_FIELDS,
        "withheld_field_policy": "oracle and scoring fields are omitted from the visible packet and kept in the answer key",
        "cases": visible_cases,
    }
    answer_key = {
        "run_id": "R304",
        "purpose": "hidden scoring for the R304 visible case packet",
        "cases": answer_cases,
    }
    report = {
        "run_id": "R304",
        "purpose": "turn operation-stack utility proxies into reviewer-facing case evidence",
        "case_policy": f"top {groups_per_task} query-aware operation-stack groups per task",
        "withheld_fields": sorted(HIDDEN_FIELDS),
        "tasks": len(task_scores),
        "cases": len(task_scores) * groups_per_task,
        "task_scores": task_scores,
        "summary": summary,
        "claim_scope": {
            "supported": "operation-stack groups can be shown as label-hidden case packets for real failure, safety, quality, and boundary questions",
            "narrowed": "case packets are automated evidence packets over existing labels, not a human study",
            "not_supported": "automatic anomaly detection or developer time reduction",
        },
        "headline": build_headline(summary),
    }
    return visible_packet, answer_key, report


def summarize_task_scores(task_scores: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "median_inspected_operation_fraction": round(
            median(row["inspected_operation_fraction"] for row in task_scores), 4
        ),
        "median_positive_recall": round(
            median(row["positive_recall"] for row in task_scores), 4
        ),
        "median_positive_precision": round(
            median(row["positive_precision"] for row in task_scores), 4
        ),
        "median_positive_lift": round(median(row["positive_lift"] for row in task_scores), 4),
        "total_case_groups": sum(row["groups"] for row in task_scores),
        "tasks_with_recall_ge_25pct": sum(row["positive_recall"] >= 0.25 for row in task_scores),
        "tasks_with_lift_ge_1": sum(row["positive_lift"] >= 1.0 for row in task_scores),
    }


def build_headline(summary: dict[str, Any]) -> str:
    return (
        "R304 converts the automated utility proxy into a label-hidden case packet. "
        f"Across six existing labeled tasks, the top-5 query-aware operation-stack cases inspect "
        f"a median {summary['median_inspected_operation_fraction'] * 100:.1f}% of operations, "
        f"recover {summary['median_positive_recall'] * 100:.1f}% of positives, and achieve "
        f"median lift {summary['median_positive_lift']:.3f}. "
        "The packet exposes only ordinary operation fields and keeps oracle labels in a separate answer key."
    )


def assert_visible_packet_has_no_hidden_fields(visible_packet: dict[str, Any]) -> None:
    def walk(value: Any, path: str = "$") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in HIDDEN_FIELDS:
                    raise SystemExit(f"hidden field {key!r} leaked at {path}")
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(visible_packet)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R304 Operation-Stack Case Packet",
        "",
        report["headline"],
        "",
        "## Task Scores",
        "",
        "| Task | Dataset | Groups | Work fraction | Recall | Precision | Lift |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in report["task_scores"]:
        lines.append(
            f"| {row['task']} | {row['dataset']} | {row['groups']} | {row['inspected_operation_fraction']} | {row['positive_recall']} | {row['positive_precision']} | {row['positive_lift']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Scope",
            "",
            "- Supports: operation-stack groups can become reviewer-auditable case packets for real labeled failure, safety, quality, and boundary questions.",
            "- Narrows: these packets are automated evidence over existing labels, not a detector or human productivity study.",
            "- Integrity: visible packet fields exclude hidden oracle labels; the answer key is separate.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['task'])}</td>"
        f"<td>{html.escape(row['dataset'])}</td>"
        f"<td>{row['groups']}</td>"
        f"<td>{row['inspected_operation_fraction']}</td>"
        f"<td>{row['positive_recall']}</td>"
        f"<td>{row['positive_precision']}</td>"
        f"<td>{row['positive_lift']}</td>"
        "</tr>"
        for row in report["task_scores"]
    )
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>R304 Operation-Stack Case Packet</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #202124; }}
p {{ max-width: 960px; line-height: 1.5; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 24px; font-size: 13px; }}
th, td {{ border-bottom: 1px solid #d7dce2; padding: 7px 8px; text-align: left; }}
th {{ background: #edf1f5; }}
</style>
<h1>R304 Operation-Stack Case Packet</h1>
<p>{html.escape(report['headline'])}</p>
<table>
<thead><tr><th>Task</th><th>Dataset</th><th>Groups</th><th>Work fraction</th><th>Recall</th><th>Precision</th><th>Lift</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</html>
"""


def main() -> None:
    args = parse_args()
    r302.validate_no_hidden_rank_features()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    visible_packet, answer_key, report = build_cases(args.groups_per_task)
    assert_visible_packet_has_no_hidden_fields(visible_packet)

    visible_path = out_dir / "visible-case-packet.json"
    answer_path = out_dir / "answer-key.json"
    report_path = out_dir / "case-study-report.json"
    markdown_path = out_dir / "case-study-report.md"
    html_path = out_dir / "index.html"
    visible_path.write_text(json.dumps(visible_packet, indent=2, sort_keys=True) + "\n")
    answer_path.write_text(json.dumps(answer_key, indent=2, sort_keys=True) + "\n")
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")

    run_result = {
        "status": "ok",
        "run_id": "R304",
        "tasks": report["tasks"],
        "case_groups": report["cases"],
        "json": rel(report_path),
        "visible_packet": rel(visible_path),
        "answer_key": rel(answer_path),
        "markdown": rel(markdown_path),
        "html": rel(html_path),
    }
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(run_result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
