#!/usr/bin/env python3
"""Measure induced task-stack depth sensitivity on existing labeled traces.

R404 reuses the tracked R300 operation JSONL and R320 scoring machinery. It
runs the maintained Rust `agentpprof --induce-task-stack` implementation with
several `--induce-max-depth` caps, reconstructs per-operation stack assignments
from Rust split decisions, and scores hidden labels only after profiling.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/visexp/out/operation-induced-depth-sensitivity-r404"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_induced_stack_scoring_eval as r403  # noqa: E402
import operation_profile_accuracy_eval as r320  # noqa: E402
import operation_query_utility_eval as r300  # noqa: E402
from operation_rust_task_stack_induction_eval import is_oracle_field  # noqa: E402


DEPTHS = [1, 2, 3, 4, 5]
RANKERS = ["width", "visible_risk", "query_aware", "oracle_upper_bound"]
VISIBLE_RANKER = "query_aware"
METRICS = r403.METRICS
LOWER_IS_BETTER = {"top5_work", "work_to_first_positive", "groups"}


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


def build_agentpprof() -> str:
    run(["cargo", "build", "--release", "--manifest-path", "agentpprof/Cargo.toml"])
    return "agentpprof/target/release/agentpprof"


def run_agentpprof(
    binary: str,
    task: dict[str, Any],
    max_depth: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    output = OUT / f"{task['id']}-depth{max_depth}.json"
    cmd = [
        binary,
        "--operation-file",
        rel(r403.SOURCE),
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
        "--induce-task-stack",
        "--induce-max-depth",
        str(max_depth),
        "--deterministic-output",
    ]
    for term in r403.TASK_TERMS[task["id"]]:
        cmd.extend(["--induce-query-term", term])
    completed = run(cmd)
    start = completed.stdout.find("{")
    status = json.loads(completed.stdout[start:]) if start >= 0 else {}
    profile = json.loads(output.read_text(encoding="utf-8"))
    status["command"] = cmd
    return status, profile


def numeric(row: dict[str, Any], key: str) -> float | None:
    value = row.get(key)
    if value in (None, ""):
        return None
    return float(value)


def median_metric(rows: list[dict[str, Any]], metric: str) -> float | None:
    values = [numeric(row, metric) for row in rows]
    values = [value for value in values if value is not None]
    return round(float(median(values)), 4) if values else None


def summarize_depth_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(int(row["max_depth"]), row["ranker"])].append(row)
    output = []
    for (max_depth, ranker), items in sorted(grouped.items()):
        output.append(
            {
                "max_depth": max_depth,
                "ranker": ranker,
                "tasks": len(items),
                "uses_hidden_fields": any(bool(row["uses_hidden_fields"]) for row in items),
                **{f"median_{metric}": median_metric(items, metric) for metric in METRICS},
            }
        )
    return output


def better(row: dict[str, Any], best: dict[str, Any] | None, metric: str) -> bool:
    if best is None:
        return True
    left = numeric(row, metric)
    right = numeric(best, metric)
    if left is None:
        return False
    if right is None:
        return True
    if metric in LOWER_IS_BETTER:
        return (left, -int(row["max_depth"])) < (right, -int(best["max_depth"]))
    return (left, -int(row["max_depth"])) > (right, -int(best["max_depth"]))


def best_depth_by_task(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    visible = [row for row in rows if row["ranker"] == VISIBLE_RANKER]
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in visible:
        by_task[row["task"]].append(row)
    output = []
    for task, items in sorted(by_task.items()):
        row: dict[str, Any] = {"task": task}
        default = next(item for item in items if int(item["max_depth"]) == 4)
        for metric in [
            "average_precision",
            "top5_work",
            "budget30_recall",
            "work_to_first_positive",
            "groups",
        ]:
            best = None
            for item in items:
                if better(item, best, metric):
                    best = item
            values = [numeric(item, metric) for item in items]
            values = [value for value in values if value is not None]
            assert best is not None
            row[f"best_{metric}_depth"] = best["max_depth"]
            row[f"best_{metric}"] = numeric(best, metric)
            row[f"default_depth4_{metric}"] = numeric(default, metric)
            row[f"{metric}_span"] = round(max(values) - min(values), 4) if values else ""
        output.append(row)
    return output


def compare_depths_to_default(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    visible = [row for row in rows if row["ranker"] == VISIBLE_RANKER]
    by_key = {(row["task"], int(row["max_depth"])): row for row in visible}
    output = []
    for task in sorted({row["task"] for row in visible}):
        default = by_key[(task, 4)]
        for max_depth in DEPTHS:
            item = by_key[(task, max_depth)]
            row = {"task": task, "max_depth": max_depth}
            for metric in METRICS:
                left = numeric(item, metric)
                right = numeric(default, metric)
                row[f"{metric}_value"] = left
                row[f"{metric}_vs_depth4"] = (
                    round(left - right, 6) if left is not None and right is not None else ""
                )
            output.append(row)
    return output


def source_status_rows() -> list[dict[str, str]]:
    paths = {
        "script": Path("script/operation_induced_depth_sensitivity_eval.py"),
        "R403 scoring helpers": Path("script/operation_induced_stack_scoring_eval.py"),
        "R300 operations": r403.SOURCE.relative_to(ROOT),
        "R320 policy scores": r403.BASELINE_SCORES.relative_to(ROOT),
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


def result_observations(score_rows: list[dict[str, Any]], best_rows: list[dict[str, Any]]) -> dict[str, Any]:
    visible = [row for row in score_rows if row["ranker"] == VISIBLE_RANKER]
    ap_best_depths = {int(row["best_average_precision_depth"]) for row in best_rows}
    work_best_depths = {int(row["best_top5_work_depth"]) for row in best_rows}
    task_objective_disagreements = [
        row["task"]
        for row in best_rows
        if row["best_average_precision_depth"] != row["best_top5_work_depth"]
    ]
    depth_to_groups: dict[str, list[float]] = defaultdict(list)
    for row in visible:
        depth_to_groups[str(row["max_depth"])].append(float(row["groups"]))
    return {
        "ap_best_depths": sorted(ap_best_depths),
        "top5_work_best_depths": sorted(work_best_depths),
        "tasks_where_ap_and_work_prefer_different_depths": task_objective_disagreements,
        "depth_changes_metric_surface": any(
            float(row.get("average_precision_span") or 0.0) > 0
            or float(row.get("top5_work_span") or 0.0) > 0
            for row in best_rows
        ),
        "depth_changes_fragmentation": len({tuple(values) for values in depth_to_groups.values()}) > 1,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R404 Induced Stack Depth Sensitivity",
        "",
        "This run varies Rust `--induce-max-depth` over the existing R300/R320 hidden-label tasks. It is an RQ3 mechanism/actionability ablation, not a new dataset and not an automatic selector.",
        "",
        "## Main Interpretation",
        "",
        f"- {report['interpretation']['summary']}",
        f"- {report['interpretation']['counterpoint']}",
        "",
        "## Depth Summary",
        "",
        "| Depth | Ranker | Tasks | Hidden | Median AP | Median work@5 | Median budget30 recall | Median groups |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["depth_summary"]:
        lines.append(
            f"| {row['max_depth']} | {row['ranker']} | {row['tasks']} | {row['uses_hidden_fields']} | {row['median_average_precision']} | {row['median_top5_work']} | {row['median_budget30_recall']} | {row['median_groups']} |"
        )
    lines.extend(["", "## Best Depths By Task", "", "| Task | Best AP depth | Best work@5 depth | Best budget30 recall depth | Best groups depth |", "|---|---:|---:|---:|---:|"])
    for row in report["best_depth_by_task"]:
        lines.append(
            f"| {row['task']} | {row['best_average_precision_depth']} | {row['best_top5_work_depth']} | {row['best_budget30_recall_depth']} | {row['best_groups_depth']} |"
        )
    lines.extend(["", "## Checks", ""])
    for name, passed in report["checks"].items():
        lines.append(f"- {name}: `{passed}`")
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any]) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{row['max_depth']}</td><td>{html.escape(row['ranker'])}</td>"
        f"<td>{row['median_average_precision']}</td>"
        f"<td>{row['median_top5_work']}</td>"
        f"<td>{row['median_budget30_recall']}</td>"
        f"<td>{row['median_groups']}</td>"
        "</tr>"
        for row in report["depth_summary"]
    )
    return f"""<!doctype html>
<meta charset="utf-8">
<title>R404 Induced Stack Depth Sensitivity</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #17202a; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
th, td {{ border-bottom: 1px solid #d5dde5; padding: 7px 8px; text-align: left; }}
th {{ background: #edf2f7; }}
.note {{ max-width: 920px; line-height: 1.5; }}
</style>
<h1>R404 Induced Stack Depth Sensitivity</h1>
<p class="note">{html.escape(report['interpretation']['summary'])}</p>
<p class="note">{html.escape(report['interpretation']['counterpoint'])}</p>
<table>
<thead><tr><th>Depth</th><th>Ranker</th><th>Median AP</th><th>Median work@5</th><th>Median budget30 recall</th><th>Median groups</th></tr></thead>
<tbody>{rows}</tbody>
</table>
"""


def main() -> None:
    start = time.time()
    clean_output_dir()
    binary = build_agentpprof()
    score_rows: list[dict[str, Any]] = []
    view_summaries: list[dict[str, Any]] = []
    for task in r300.TASKS:
        operations = r403.load_task_operations(task)
        for max_depth in DEPTHS:
            view = f"induced_depth_{max_depth}"
            status, profile_doc = run_agentpprof(binary, task, max_depth)
            groups, summary = r403.induced_groups(task, view, operations, profile_doc)
            selected_source_fields = summary["selected_source_fields"]
            view_summaries.append(
                {
                    "task": task["id"],
                    "max_depth": max_depth,
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
                    "min_observed_depth": summary["min_depth"],
                    "max_observed_depth": summary["max_depth"],
                    "variable_depth": summary["variable_depth"],
                    "rust_stack_weight_match": summary["rust_stack_weight_match"],
                    "status": status,
                }
            )
            for ranker in RANKERS:
                row = r320.score_policy(
                    task,
                    view,
                    ranker,
                    groups,
                    summary,
                    r320.HIGH_LIFT_THRESHOLD,
                )
                row["max_depth"] = max_depth
                score_rows.append(row)

    depth_summary = summarize_depth_rows(score_rows)
    best_rows = best_depth_by_task(score_rows)
    depth_comparisons = compare_depths_to_default(score_rows)
    observations = result_observations(score_rows, best_rows)
    visible_summary = {
        row["max_depth"]: row
        for row in depth_summary
        if row["ranker"] == VISIBLE_RANKER
    }
    best_median_ap = max(
        visible_summary.values(),
        key=lambda row: float(row["median_average_precision"]),
    )
    lowest_median_work = min(
        visible_summary.values(),
        key=lambda row: float(row["median_top5_work"]),
    )
    interpretation = {
        "summary": (
            "Induced stack depth is a real profile-configuration knob: sweeping "
            f"depths {DEPTHS} changes hidden-label fidelity, inspection work, "
            "and fragmentation on the same six real labeled tasks without "
            "syncing new data or using hidden labels during profiling."
        ),
        "counterpoint": (
            "The sweep is a post-hoc mechanism analysis, not an automatic depth "
            "selector. The median-AP best depth is "
            f"{best_median_ap['max_depth']} (AP {best_median_ap['median_average_precision']}), "
            "while the lowest median work@5 depth is "
            f"{lowest_median_work['max_depth']} (work {lowest_median_work['median_top5_work']})."
        ),
    }
    checks = {
        "uses_tracked_r300_source": r403.SOURCE.exists(),
        "uses_tracked_r320_baselines": r403.BASELINE_SCORES.exists(),
        "covers_all_six_tasks": len({row["task"] for row in score_rows}) == 6,
        "covers_all_depths": {int(row["max_depth"]) for row in score_rows} == set(DEPTHS),
        "all_rust_profiles_use_induction": all(row["status"].get("induce_task_stack") for row in view_summaries),
        "all_rust_depth_caps_match": all(int(row["status"].get("induce_max_depth")) == row["max_depth"] for row in view_summaries),
        "rust_stack_reconstruction_matches": all(row["rust_stack_weight_match"] for row in view_summaries),
        "no_oracle_source_fields_selected": all(not row["oracle_source_field_overlap"] for row in view_summaries),
        "hidden_labels_used_only_for_visible_rows": all(
            not row["uses_hidden_fields"]
            for row in score_rows
            if row["ranker"] != "oracle_upper_bound"
        ),
    }
    report = {
        "run_id": "R404",
        "status": "pass" if all(checks.values()) else "fail",
        "purpose": "Measure recursive induced-stack depth sensitivity as an RQ3 mechanism/actionability ablation on existing real labeled traces.",
        "input_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "source_operations": rel(r403.SOURCE),
            "baseline_scores": rel(r403.BASELINE_SCORES),
            "hidden_label_use": "hidden labels are used only after Rust profiling, except oracle_upper_bound ranker rows marked as hidden upper bounds",
            "depths": DEPTHS,
        },
        "depth_summary": depth_summary,
        "best_depth_by_task": best_rows,
        "depth_comparisons_to_depth4": depth_comparisons,
        "views": view_summaries,
        "observations": observations,
        "interpretation": interpretation,
        "checks": checks,
        "source_status": source_status_rows(),
        "elapsed_s": round(time.time() - start, 3),
    }
    write_json(OUT / "depth-sensitivity-report.json", report)
    score_fields = [
        "task",
        "dataset",
        "query_family",
        "view",
        "max_depth",
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
    write_csv(OUT / "depth-policy-scores.csv", score_rows, score_fields)
    write_csv(
        OUT / "depth-summary.csv",
        depth_summary,
        ["max_depth", "ranker", "tasks", "uses_hidden_fields"]
        + [f"median_{metric}" for metric in METRICS],
    )
    write_csv(
        OUT / "best-depth-by-task.csv",
        best_rows,
        [
            "task",
            "best_average_precision_depth",
            "best_average_precision",
            "default_depth4_average_precision",
            "average_precision_span",
            "best_top5_work_depth",
            "best_top5_work",
            "default_depth4_top5_work",
            "top5_work_span",
            "best_budget30_recall_depth",
            "best_budget30_recall",
            "default_depth4_budget30_recall",
            "budget30_recall_span",
            "best_work_to_first_positive_depth",
            "best_work_to_first_positive",
            "default_depth4_work_to_first_positive",
            "work_to_first_positive_span",
            "best_groups_depth",
            "best_groups",
            "default_depth4_groups",
            "groups_span",
        ],
    )
    comparison_fields = ["task", "max_depth"]
    for metric in METRICS:
        comparison_fields.extend([f"{metric}_value", f"{metric}_vs_depth4"])
    write_csv(OUT / "depth-comparisons-to-depth4.csv", depth_comparisons, comparison_fields)
    write_csv(
        OUT / "view-summary.csv",
        view_summaries,
        [
            "task",
            "max_depth",
            "operations",
            "positives",
            "groups",
            "selected_source_fields",
            "oracle_source_field_overlap",
            "split_decisions",
            "stop_reasons",
            "depth_histogram",
            "min_observed_depth",
            "max_observed_depth",
            "variable_depth",
            "rust_stack_weight_match",
        ],
    )
    write_csv(OUT / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_csv(
        OUT / "depth-sensitivity-checks.csv",
        [{"check": key, "passed": value} for key, value in checks.items()],
        ["check", "passed"],
    )
    (OUT / "depth-sensitivity-report.md").write_text(render_markdown(report), encoding="utf-8")
    (OUT / "index.html").write_text(render_html(report), encoding="utf-8")
    run_result = {
        "run_id": "R404",
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
