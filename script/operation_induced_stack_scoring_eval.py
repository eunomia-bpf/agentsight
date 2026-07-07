#!/usr/bin/env python3
"""Score Rust-induced operation stacks against existing hidden labels.

R403 reuses the tracked R300 operation JSONL and R320 scoring machinery. It runs
the maintained Rust `agentpprof --induce-operation-stack` implementation, reconstructs
per-operation induced stack assignments from the Rust split decisions, and then
scores the resulting ranked groups with hidden labels only after profiling.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/visexp/out/operation-induced-stack-scoring-r403"
SOURCE = ROOT / "docs/visexp/out/operation-query-utility-r300/query-utility-operations.jsonl"
BASELINE_SCORES = ROOT / "docs/visexp/out/operation-profile-accuracy-r320/policy-scores.csv"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_profile_accuracy_eval as r320  # noqa: E402
import operation_analyst_ranking_eval as r302  # noqa: E402
import operation_query_utility_eval as r300  # noqa: E402
from operation_rust_task_stack_induction_eval import (  # noqa: E402
    is_oracle_field,
    operation_stack_induction_report,
)


TASK_TERMS = {
    "agentreward_looping": ["loop", "repeat"],
    "agentreward_side_effect": ["side", "effect", "write"],
    "satraj_unsafe": ["unsafe", "safety", "risk"],
    "agentnet_incorrect_step": ["incorrect", "error", "failure"],
    "agentnet_redundant_step": ["redundant", "repeat"],
    "osworld_group_start": ["group", "start", "boundary"],
}
INDUCED_VIEWS = {
    "induced_operation_stack": {"allow_session": False},
}
RANKERS = ["width", "visible_risk", "query_aware", "oracle_upper_bound"]
VISIBLE_POLICY = ("induced_operation_stack", "query_aware")
BASELINE_POLICIES = [
    ("flat", "width"),
    ("fixed_session", "query_aware"),
    ("dataset_native", "query_aware"),
    ("raw_action_stack", "query_aware"),
    ("operation_stack", "width"),
    ("operation_stack", "query_aware"),
    ("operation_stack", "oracle_upper_bound"),
]
METRICS = [
    "average_precision",
    "ndcg",
    "top5_precision",
    "top5_recall",
    "top5_f1",
    "top5_work",
    "budget30_recall",
    "budget30_f1",
    "work_to_first_positive",
    "groups",
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def clean_output_dir() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in OUT.iterdir():
        if path.is_file():
            path.unlink()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def stack_hash(label: str) -> str:
    return hashlib.sha1(label.encode("utf-8")).hexdigest()[:12]


def safe_frame(text: str, prefix: str | None = None) -> str:
    output = []
    for char in text.lower():
        if char.isascii() and (char.isalnum() or char in "._:/+-"):
            output.append(char)
        elif not output or output[-1] != "_":
            output.append("_")
    value = "".join(output).strip("_;") or "unknown"
    return f"{prefix}:{value}" if prefix else value


def load_task_operations(task: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    with SOURCE.open(encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            row = json.loads(line)
            fields = r300.normalize_fields(row.get("fields") or {})
            if fields.get("analysis_task") != task["id"] or fields.get("dataset") != task["dataset"]:
                continue
            rows.append({"fields": fields, "value": int(row.get("value") or 1)})
    if not rows:
        raise SystemExit(f"no R300 operations found for {task['id']}")
    return rows


def build_agentpprof() -> str:
    run(["cargo", "build", "--release", "--manifest-path", "agentpprof/Cargo.toml"])
    return "agentpprof/target/release/agentpprof"


def run_agentpprof(
    binary: str,
    task: dict[str, Any],
    view: str,
    allow_session: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    output = OUT / f"{task['id']}-{view}.json"
    cmd = [
        binary,
        "--operation-file",
        rel(SOURCE),
        "--view",
        "operations",
        "--format",
        "json",
        "--output",
        rel(output),
        "--where",
        f"analysis_task={task['id']}",
        "--where",
        f"dataset={task['dataset']}",
        "--induce-operation-stack",
        "--deterministic-output",
    ]
    if allow_session:
        cmd.append("--induce-allow-session")
    for term in TASK_TERMS[task["id"]]:
        cmd.extend(["--induce-query-term", term])
    completed = run(cmd)
    start = completed.stdout.find("{")
    status = json.loads(completed.stdout[start:]) if start >= 0 else {}
    profile = json.loads(output.read_text(encoding="utf-8"))
    status["command"] = cmd
    return status, profile


def push_path(path: list[str], label: str) -> list[str]:
    child = list(path)
    if label not in child:
        child.append(label)
    return child


def reconstruct_paths(operations: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> list[list[str]]:
    paths: list[list[str] | None] = [None] * len(operations)
    cursor = 0

    def visit(indices: list[int], path: list[str]) -> None:
        nonlocal cursor
        node_weight = sum(operations[index]["value"] for index in indices)
        if (
            cursor < len(decisions)
            and decisions[cursor]["path"] == path
            and int(decisions[cursor]["node_weight"]) == node_weight
        ):
            decision = decisions[cursor]
            cursor += 1
            score = decision["selected_score"]
            cut_after = int(score["cut_after"])
            left = indices[:cut_after]
            right = indices[cut_after:]
            if not left or not right:
                raise SystemExit(f"empty split while replaying decision {decision}")
            visit(left, push_path(path, score["left_label"]))
            visit(right, push_path(path, score["right_label"]))
            return
        final_path = path or ["all"]
        for index in indices:
            paths[index] = list(final_path)

    visit(list(range(len(operations))), [])
    if cursor != len(decisions):
        raise SystemExit(f"unconsumed Rust split decisions: {len(decisions) - cursor}")
    if any(path is None for path in paths):
        raise SystemExit("incomplete induced operation-stack path reconstruction")
    return [path or ["all"] for path in paths]


def stack_from_path(path: list[str]) -> str:
    return ";".join(safe_frame(label, "operation") for label in path)


def stack_frames(label: str) -> list[dict[str, str]]:
    frames = []
    for part in label.split(";"):
        if ":" in part:
            field, value = part.split(":", 1)
        else:
            field, value = "frame", part
        frames.append({"field": field, "value": value})
    return frames


def stack_depth(label: str) -> int:
    if not label:
        return 0
    return label.count(";") + 1


def induced_groups(
    task: dict[str, Any],
    view: str,
    operations: list[dict[str, Any]],
    profile_doc: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    profile = profile_doc["profile"]
    induction = operation_stack_induction_report(profile)
    paths = reconstruct_paths(operations, induction["split_decisions"])
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation, path in zip(operations, paths):
        grouped[stack_from_path(path)].append(operation)

    reconstructed = Counter(
        {
            stack: sum(operation["value"] for operation in rows)
            for stack, rows in grouped.items()
        }
    )
    rust_stacks = Counter({stack: int(weight) for stack, weight in profile["stacks"].items()})
    rust_match = reconstructed == rust_stacks
    depth_histogram = dict(sorted(Counter(stack_depth(stack) for stack in grouped).items()))
    depths = sorted(depth_histogram)

    groups = []
    total_ops = 0
    total_positive = 0
    for label, rows in grouped.items():
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
                "group_id": stack_hash(f"{view}:{label}"),
                "stack": label,
                "stack_frames": stack_frames(label),
                "operations": operations_in_group,
                "positives": positives,
                "positive_rate": positives / operations_in_group if operations_in_group else 0.0,
                "sessions": len(sessions),
                "session_examples": [stack_hash(session) for session in sessions[:5]],
                "features": r302.visible_features(rows),
            }
        )

    summary = {
        "operations": total_ops,
        "positives": total_positive,
        "prevalence": total_positive / total_ops if total_ops else 0.0,
        "groups": len(groups),
        "positive_groups": sum(1 for group in groups if group["positives"] > 0),
        "stack": ["operation"],
        "rust_stack_weight_match": rust_match,
        "selected_evidence_fields": induction.get("selected_evidence_fields")
        or induction["selected_source_fields"],
        "selected_source_fields": induction.get("selected_evidence_fields")
        or induction["selected_source_fields"],
        "split_decisions": len(induction["split_decisions"]),
        "stop_reasons": induction["stop_reasons"],
        "depth_histogram": depth_histogram,
        "min_depth": depths[0] if depths else 0,
        "max_depth": depths[-1] if depths else 0,
        "variable_depth": len(depths) > 1,
    }
    return groups, summary


def load_baseline_rows() -> list[dict[str, Any]]:
    rows = []
    with BASELINE_SCORES.open(encoding="utf-8") as file:
        for row in csv.DictReader(file):
            if (row["view"], row["ranker"]) in BASELINE_POLICIES:
                row = dict(row)
                row["uses_hidden_fields"] = row["uses_hidden_fields"] == "True"
                rows.append(row)
    return rows


def numeric(row: dict[str, Any], key: str) -> float | None:
    value = row.get(key)
    if value in (None, ""):
        return None
    return float(value)


def median_metric(rows: list[dict[str, Any]], metric: str) -> float | None:
    values = [numeric(row, metric) for row in rows]
    values = [value for value in values if value is not None]
    return round(float(median(values)), 4) if values else None


def summarize_policy_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_policy[(row["view"], row["ranker"])].append(row)
    output = []
    for (view, ranker), items in sorted(by_policy.items()):
        output.append(
            {
                "view": view,
                "ranker": ranker,
                "tasks": len(items),
                "uses_hidden_fields": any(bool(row["uses_hidden_fields"]) for row in items),
                **{f"median_{metric}": median_metric(items, metric) for metric in METRICS},
            }
        )
    return output


def safe_ratio(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    if right == 0:
        return None if left == 0 else float("inf")
    return left / right


def compare_against_baselines(induced_rows: list[dict[str, Any]], baseline_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    all_rows = induced_rows + baseline_rows
    by_key = {(row["task"], row["view"], row["ranker"]): row for row in all_rows}
    comparison_rows = []
    for task in sorted({row["task"] for row in induced_rows}):
        for induced_key in [VISIBLE_POLICY]:
            induced = by_key[(task, *induced_key)]
            for baseline in BASELINE_POLICIES:
                other = by_key.get((task, *baseline))
                if other is None:
                    continue
                row = {
                    "task": task,
                    "induced_policy": f"{induced_key[0]}:{induced_key[1]}",
                    "baseline_policy": f"{baseline[0]}:{baseline[1]}",
                }
                for metric in METRICS:
                    left = numeric(induced, metric)
                    right = numeric(other, metric)
                    delta = left - right if left is not None and right is not None else None
                    row[f"{metric}_induced"] = left
                    row[f"{metric}_baseline"] = right
                    row[f"{metric}_delta"] = delta
                    row[f"{metric}_ratio"] = safe_ratio(left, right)
                comparison_rows.append(row)
    return comparison_rows


def summarize_comparisons(comparisons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_pair: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in comparisons:
        by_pair[(row["induced_policy"], row["baseline_policy"])].append(row)
    output = []
    lower_is_better = {"top5_work", "work_to_first_positive", "groups"}
    for (induced, baseline), rows in sorted(by_pair.items()):
        item = {"induced_policy": induced, "baseline_policy": baseline, "tasks": len(rows)}
        for metric in METRICS:
            deltas = [row[f"{metric}_delta"] for row in rows if row[f"{metric}_delta"] is not None]
            if metric in lower_is_better:
                wins = sum(1 for delta in deltas if delta < 0)
            else:
                wins = sum(1 for delta in deltas if delta > 0)
            item[f"{metric}_wins"] = wins
            item[f"{metric}_median_delta"] = round(float(median(deltas)), 4) if deltas else None
        output.append(item)
    return output


def source_status_rows() -> list[dict[str, str]]:
    paths = {
        "script": Path("script/operation_induced_stack_scoring_eval.py"),
        "R300 operations": SOURCE.relative_to(ROOT),
        "R320 policy scores": BASELINE_SCORES.relative_to(ROOT),
    }
    rows = []
    for name, rel_path in paths.items():
        path = ROOT / rel_path
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "missing"
        status_result = subprocess.run(
            ["git", "status", "--short", "--", str(rel_path)],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        rows.append(
            {
                "source": name,
                "path": str(rel_path),
                "status": status_result.stdout.strip() or "tracked_clean",
                "sha256": digest,
            }
        )
    return rows


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R403 Induced Stack Scoring",
        "",
        "This run scores Rust-induced operation stacks on the existing R300/R320 hidden-label tasks. It is a mechanism ablation for E2/E3, not a new dataset and not a human-utility study.",
        "",
        "## Policy Summary",
        "",
        "| Policy | Tasks | Hidden | Median AP | Median R@5 | Median work@5 | Median budget30 recall | Median groups |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["policy_summary"]:
        policy = f"{row['view']}:{row['ranker']}"
        lines.append(
            f"| {policy} | {row['tasks']} | {row['uses_hidden_fields']} | {row['median_average_precision']} | {row['median_top5_recall']} | {row['median_top5_work']} | {row['median_budget30_recall']} | {row['median_groups']} |"
        )
    lines.extend(
        [
            "",
            "## Main Interpretation",
            "",
            f"- {report['interpretation']['summary']}",
            f"- {report['interpretation']['counterpoint']}",
            "",
            "## Checks",
            "",
        ]
    )
    for name, passed in report["checks"].items():
        lines.append(f"- {name}: `{passed}`")
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any]) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['view'] + ':' + row['ranker'])}</td>"
        f"<td>{row['tasks']}</td>"
        f"<td>{row['uses_hidden_fields']}</td>"
        f"<td>{row['median_average_precision']}</td>"
        f"<td>{row['median_top5_recall']}</td>"
        f"<td>{row['median_top5_work']}</td>"
        f"<td>{row['median_budget30_recall']}</td>"
        f"<td>{row['median_groups']}</td>"
        "</tr>"
        for row in report["policy_summary"]
    )
    return f"""<!doctype html>
<meta charset="utf-8">
<title>R403 Induced Stack Scoring</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #17202a; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
th, td {{ border-bottom: 1px solid #d5dde5; padding: 7px 8px; text-align: left; }}
th {{ background: #edf2f7; }}
.note {{ max-width: 900px; line-height: 1.5; }}
</style>
<h1>R403 Induced Stack Scoring</h1>
<p class="note">Rust-induced operation stacks are scored against existing hidden labels after profiling. The run uses tracked R300/R320 artifacts only.</p>
<p class="note">{html.escape(report['interpretation']['summary'])}</p>
<p class="note">{html.escape(report['interpretation']['counterpoint'])}</p>
<table>
<thead><tr><th>Policy</th><th>Tasks</th><th>Hidden</th><th>Median AP</th><th>Median R@5</th><th>Median work@5</th><th>Median budget30 recall</th><th>Median groups</th></tr></thead>
<tbody>{rows}</tbody>
</table>
"""


def main() -> None:
    start = time.time()
    clean_output_dir()
    induced_rows: list[dict[str, Any]] = []
    view_summaries = []
    binary = build_agentpprof()
    for task in r300.TASKS:
        operations = load_task_operations(task)
        for view, spec in INDUCED_VIEWS.items():
            status, profile_doc = run_agentpprof(binary, task, view, spec["allow_session"])
            groups, summary = induced_groups(task, view, operations, profile_doc)
            selected_source_fields = summary["selected_source_fields"]
            view_summaries.append(
                {
                    "task": task["id"],
                    "view": view,
                    "operations": summary["operations"],
                    "positives": summary["positives"],
                    "groups": summary["groups"],
                    "selected_source_fields": selected_source_fields,
                    "oracle_source_field_overlap": [
                        field for field in selected_source_fields if is_oracle_field(field)
                    ],
                    "split_decisions": summary["split_decisions"],
                    "stop_reasons": summary["stop_reasons"],
                    "depth_histogram": summary["depth_histogram"],
                    "min_depth": summary["min_depth"],
                    "max_depth": summary["max_depth"],
                    "variable_depth": summary["variable_depth"],
                    "rust_stack_weight_match": summary["rust_stack_weight_match"],
                    "status": status,
                }
            )
            for ranker in RANKERS:
                induced_rows.append(
                    r320.score_policy(
                        task,
                        view,
                        ranker,
                        groups,
                        summary,
                        r320.HIGH_LIFT_THRESHOLD,
                    )
                )

    baseline_rows = load_baseline_rows()
    comparisons = compare_against_baselines(induced_rows, baseline_rows)
    comparison_summary = summarize_comparisons(comparisons)
    policy_summary = summarize_policy_rows(induced_rows + baseline_rows)
    by_policy = {
        (row["view"], row["ranker"]): row
        for row in policy_summary
    }
    induced_visible = by_policy[VISIBLE_POLICY]
    fixed_session = by_policy[("fixed_session", "query_aware")]
    flat = by_policy[("flat", "width")]
    operation_stack = by_policy[("operation_stack", "query_aware")]
    variable_tasks = sum(1 for row in view_summaries if row["variable_depth"])
    stopped_tasks = [
        row["task"]
        for row in view_summaries
        if not row["variable_depth"] and "no_material_split" in row["stop_reasons"]
    ]
    interpretation = {
        "summary": (
            "The induced operation-stack view gives a label-scored automatic-boundary probe: "
            f"median top-5 work is {induced_visible['median_top5_work']} versus "
            f"{flat['median_top5_work']} for flat summaries, with median groups "
            f"{induced_visible['median_groups']} versus {fixed_session['median_groups']} "
            "for fixed-session drilldown. "
            f"{variable_tasks}/6 real-trace tasks produce variable-depth recursive stacks; "
            f"{len(stopped_tasks)}/6 stop at one induced operation segment because visible "
            "evidence does not support a material split."
        ),
        "counterpoint": (
            "The hand-configured operation stack remains the stronger main E2 policy when "
            f"median AP is compared ({operation_stack['median_average_precision']} versus "
            f"{induced_visible['median_average_precision']}), so induction is evidence for "
            "configurable recursive folding rather than a replacement for task-specific profile specs."
        ),
    }
    checks = {
        "uses_tracked_r300_source": SOURCE.exists(),
        "uses_tracked_r320_baselines": BASELINE_SCORES.exists(),
        "covers_all_six_tasks": len({row["task"] for row in induced_rows}) == 6,
        "all_rust_profiles_use_induction": all(row["status"].get("induce_operation_stack") for row in view_summaries),
        "rust_stack_reconstruction_matches": all(row["rust_stack_weight_match"] for row in view_summaries),
        "no_oracle_source_fields_selected": all(not row["oracle_source_field_overlap"] for row in view_summaries),
        "variable_or_materially_stopped_induced_stacks": all(
            row["variable_depth"]
            or (row["groups"] == 1 and "no_material_split" in row["stop_reasons"])
            for row in view_summaries
        ),
        "hidden_labels_used_only_for_scoring": all(
            not row["uses_hidden_fields"]
            for row in induced_rows
            if row["ranker"] != "oracle_upper_bound"
        ),
        "contains_visible_and_oracle_rows": {
            row["ranker"] for row in induced_rows
        } == set(RANKERS),
    }
    report = {
        "run_id": "R403",
        "status": "pass" if all(checks.values()) else "fail",
        "purpose": "Score Rust-induced recursive operation stacks as an E2/E3 mechanism ablation on existing real labeled traces.",
        "input_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "source_operations": rel(SOURCE),
            "baseline_scores": rel(BASELINE_SCORES),
            "hidden_label_use": "hidden labels are used only after Rust profiling, except oracle_upper_bound ranker rows marked as hidden upper bounds",
        },
        "views": view_summaries,
        "policy_summary": policy_summary,
        "comparison_summary": comparison_summary,
        "interpretation": interpretation,
        "checks": checks,
        "source_status": source_status_rows(),
        "elapsed_s": round(time.time() - start, 3),
    }

    write_json(OUT / "induced-stack-scoring-report.json", report)
    induced_fields = [
        "task",
        "dataset",
        "query_family",
        "view",
        "ranker",
        "uses_hidden_fields",
        "operations",
        "positives",
        "prevalence",
        "groups",
        "positive_groups",
        "average_precision",
        "ndcg",
        "top5_precision",
        "top5_recall",
        "top5_f1",
        "top5_work",
        "budget30_recall",
        "budget30_f1",
        "budget30_work",
        "work_to_first_positive",
        "groups_to_50pct_recall",
        "work_to_50pct_recall",
    ]
    write_csv(OUT / "induced-policy-scores.csv", induced_rows, induced_fields)
    write_csv(
        OUT / "policy-summary.csv",
        policy_summary,
        ["view", "ranker", "tasks", "uses_hidden_fields"]
        + [f"median_{metric}" for metric in METRICS],
    )
    comparison_fields = ["task", "induced_policy", "baseline_policy"]
    for metric in METRICS:
        comparison_fields.extend(
            [
                f"{metric}_induced",
                f"{metric}_baseline",
                f"{metric}_delta",
                f"{metric}_ratio",
            ]
        )
    write_csv(OUT / "baseline-comparisons.csv", comparisons, comparison_fields)
    summary_fields = ["induced_policy", "baseline_policy", "tasks"]
    for metric in METRICS:
        summary_fields.extend([f"{metric}_wins", f"{metric}_median_delta"])
    write_csv(OUT / "comparison-summary.csv", comparison_summary, summary_fields)
    write_csv(
        OUT / "view-summary.csv",
        view_summaries,
        [
            "task",
            "view",
            "operations",
            "positives",
            "groups",
            "selected_source_fields",
            "oracle_source_field_overlap",
            "split_decisions",
            "stop_reasons",
            "depth_histogram",
            "min_depth",
            "max_depth",
            "variable_depth",
            "rust_stack_weight_match",
        ],
    )
    write_csv(OUT / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_csv(
        OUT / "induced-stack-scoring-checks.csv",
        [{"check": key, "passed": value} for key, value in checks.items()],
        ["check", "passed"],
    )
    (OUT / "induced-stack-scoring-report.md").write_text(render_markdown(report), encoding="utf-8")
    (OUT / "index.html").write_text(render_html(report), encoding="utf-8")
    run_result = {
        "run_id": "R403",
        "status": report["status"],
        "checks": {
            "checks_passed": sum(1 for value in checks.values() if value),
            "checks_total": len(checks),
        },
        "out_dir": rel(OUT),
        "elapsed_s": report["elapsed_s"],
    }
    write_json(OUT / "run-result.json", run_result)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
