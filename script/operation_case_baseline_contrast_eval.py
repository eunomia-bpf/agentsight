#!/usr/bin/env python3
"""R347: case-level baseline contrast over existing labeled agent traces.

This audit does not fetch, sync, create, or relabel datasets. It reuses the
existing public labeled operation JSONL plus the tracked R346 diagnostic
casebook, ranks only visible view/ranker policies, and scores the resulting
top-case groups against hidden labels after ranking.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
R346_DIR = OUT_ROOT / "operation-diagnostic-casebook-r346"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-case-baseline-contrast-r347"
RUN_ID = "R347"

R346_REPORT = R346_DIR / "diagnostic-casebook-report.json"
R346_TASK_CARDS = R346_DIR / "task-diagnostic-case-cards.csv"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_profile_accuracy_eval as r320  # noqa: E402
import operation_query_utility_eval as r300  # noqa: E402

POLICIES = [
    ("flat", "width"),
    ("fixed_session", "query_aware"),
    ("dataset_native", "query_aware"),
    ("raw_action_stack", "query_aware"),
    ("operation_stack", "query_aware"),
]
DEFAULT_POLICY = "operation_stack:query_aware"
TOP_K = 5
HIGH_LIFT_THRESHOLD = 1.5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def git_check(description: str, path: Path, args: list[str]) -> None:
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


def ensure_sources_tracked_clean(paths: list[Path]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for path in paths:
        if not path.exists():
            raise SystemExit(f"missing source artifact {rel(path)}")
        git_check("source artifact is not git-tracked", path, ["ls-files", "--error-unmatch"])
        git_check("source artifact has unstaged changes", path, ["diff", "--quiet"])
        git_check("source artifact has staged changes", path, ["diff", "--cached", "--quiet"])
        statuses[rel(path)] = "tracked_clean"
    return statuses


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_value(row.get(field)) for field in fields})


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(round_value(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def round_value(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if math.isinf(value):
            return "inf"
        return round(value, 4)
    if isinstance(value, dict):
        return {key: round_value(child) for key, child in value.items()}
    if isinstance(value, list):
        return [round_value(child) for child in value]
    return value


def format_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        if math.isinf(value):
            return "inf"
        return round(value, 6)
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(round_value(value), sort_keys=True)
    return value


def policy_name(view: str, ranker: str) -> str:
    return f"{view}:{ranker}"


def score_view(task: dict[str, Any], view: str, ranker: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    groups, summary = r320.group_task_view(task, view)
    ranked = r320.rank_groups(task, groups, ranker)
    selected = ranked[:TOP_K]
    top5 = r320.score_selection(selected, summary, "top5")
    first = r320.first_relevant_metrics(ranked, summary, HIGH_LIFT_THRESHOLD)
    recall50 = r320.recall_target_metrics(ranked, summary, 0.50)
    ap = r320.average_precision(ranked, summary["positives"])
    ndcg = r320.ndcg_at_all(ranked)
    top1 = selected[0] if selected else None
    positive_groups = sum(1 for group in selected if group["positives"] > 0)
    row = {
        "task": task["id"],
        "dataset": task["dataset"],
        "query_family": task["query_family"],
        "view": view,
        "ranker": ranker,
        "policy": policy_name(view, ranker),
        "operations": summary["operations"],
        "positives": summary["positives"],
        "prevalence": summary["prevalence"],
        "groups": summary["groups"],
        "positive_groups": summary["positive_groups"],
        "average_precision": ap,
        "ndcg": ndcg,
        "top1_positive": bool(top1 and top1["positives"] > 0),
        "top1_positive_rate": top1["positive_rate"] if top1 else 0.0,
        "top1_lift": (top1["positive_rate"] / summary["prevalence"])
        if top1 and summary["prevalence"]
        else 0.0,
        "top5_positive_groups": positive_groups,
        "top5_group_precision": positive_groups / len(selected) if selected else 0.0,
        "top5_recall": top5["top5_recall"],
        "top5_precision": top5["top5_precision"],
        "top5_f1": top5["top5_f1"],
        "top5_lift": top5["top5_lift"],
        "top5_work": top5["top5_work"],
        "work_to_first_positive": first["work_to_first_positive"],
        "rank_to_first_positive": first["rank_to_first_positive"],
        "groups_to_50pct_recall": recall50["groups_to_recall"],
        "work_to_50pct_recall": recall50["work_to_recall"],
    }
    top_groups = [
        {
            "task": task["id"],
            "dataset": task["dataset"],
            "view": view,
            "ranker": ranker,
            "rank": index,
            "group_id": group["group_id"],
            "stack": group["stack"],
            "operations": group["operations"],
            "positive_operations": group["positives"],
            "positive_rate": group["positive_rate"],
            "sessions": group["sessions"],
        }
        for index, group in enumerate(selected, 1)
    ]
    return row, top_groups


def direction(metric: str) -> str:
    return "lower" if metric in {"top5_work", "work_to_first_positive", "groups", "groups_to_50pct_recall"} else "higher"


def better(left: float | int | None, right: float | int | None, metric: str) -> bool:
    if left is None or right is None:
        return False
    if direction(metric) == "lower":
        return float(left) < float(right)
    return float(left) > float(right)


def best_visible_policy(rows: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    reverse = direction(metric) == "higher"
    return sorted(
        rows,
        key=lambda row: (
            row[metric] is not None,
            float(row[metric]) if row[metric] is not None else (-1e18 if reverse else 1e18),
        ),
        reverse=reverse,
    )[0]


def build_task_cards(view_rows: list[dict[str, Any]], r346_cards: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in view_rows:
        by_task[row["task"]].append(row)

    cards = []
    for task, rows in sorted(by_task.items()):
        default = next(row for row in rows if row["policy"] == DEFAULT_POLICY)
        flat = next(row for row in rows if row["policy"] == "flat:width")
        fixed = next(row for row in rows if row["policy"] == "fixed_session:query_aware")
        dataset_native = next(row for row in rows if row["policy"] == "dataset_native:query_aware")
        raw_action = next(row for row in rows if row["policy"] == "raw_action_stack:query_aware")
        best_recall = best_visible_policy(rows, "top5_recall")
        best_lift = best_visible_policy(rows, "top5_lift")
        best_work = best_visible_policy(rows, "top5_work")
        best_first = best_visible_policy(rows, "work_to_first_positive")
        counterpoints = []
        if best_recall["policy"] != DEFAULT_POLICY:
            counterpoints.append(f"top5_recall->{best_recall['policy']}")
        if best_lift["policy"] != DEFAULT_POLICY:
            counterpoints.append(f"top5_lift->{best_lift['policy']}")
        if best_first["policy"] != DEFAULT_POLICY:
            counterpoints.append(f"first_positive->{best_first['policy']}")
        if default["top5_work"] < flat["top5_work"]:
            work_takeaway = "operation-stack reduces flat-summary inspection work"
        else:
            work_takeaway = "flat-summary work remains a counterpoint"
        card = r346_cards[task]
        cards.append(
            {
                "task": task,
                "dataset": default["dataset"],
                "query_family": default["query_family"],
                "operation_stack_top5_recall": default["top5_recall"],
                "operation_stack_top5_work": default["top5_work"],
                "operation_stack_top5_lift": default["top5_lift"],
                "operation_stack_top1_positive": default["top1_positive"],
                "flat_top5_work": flat["top5_work"],
                "fixed_session_top5_recall": fixed["top5_recall"],
                "fixed_session_work_to_first_positive": fixed["work_to_first_positive"],
                "dataset_native_top5_recall": dataset_native["top5_recall"],
                "raw_action_top5_recall": raw_action["top5_recall"],
                "best_top5_recall_policy": best_recall["policy"],
                "best_top5_lift_policy": best_lift["policy"],
                "best_top5_work_policy": best_work["policy"],
                "best_first_positive_policy": best_first["policy"],
                "operation_stack_beats_flat_work": default["top5_work"] < flat["top5_work"],
                "operation_stack_beats_fixed_recall": default["top5_recall"] > fixed["top5_recall"],
                "operation_stack_has_fewer_groups_than_fixed": default["groups"] < fixed["groups"],
                "counterpoints": counterpoints,
                "work_takeaway": work_takeaway,
                "optimization_action": card["optimization_action"],
            }
        )
    return cards


def build_pair_rows(view_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_task_policy = {(row["task"], row["policy"]): row for row in view_rows}
    tasks = sorted({row["task"] for row in view_rows})
    baselines = [
        "flat:width",
        "fixed_session:query_aware",
        "dataset_native:query_aware",
        "raw_action_stack:query_aware",
    ]
    metrics = [
        "top5_recall",
        "top5_precision",
        "top5_lift",
        "top5_work",
        "work_to_first_positive",
        "groups",
    ]
    rows = []
    for baseline in baselines:
        for metric in metrics:
            wins = 0
            losses = 0
            ties = 0
            deltas = []
            for task in tasks:
                default = by_task_policy[(task, DEFAULT_POLICY)]
                other = by_task_policy[(task, baseline)]
                left = default[metric]
                right = other[metric]
                if left is None or right is None:
                    continue
                delta = float(left) - float(right)
                deltas.append(delta)
                if better(left, right, metric):
                    wins += 1
                elif better(right, left, metric):
                    losses += 1
                else:
                    ties += 1
            rows.append(
                {
                    "baseline": baseline,
                    "metric": metric,
                    "direction": direction(metric),
                    "operation_stack_wins": wins,
                    "operation_stack_losses": losses,
                    "ties": ties,
                    "median_delta": median(deltas) if deltas else None,
                }
            )
    return rows


def build_summary(task_cards: list[dict[str, Any]], view_rows: list[dict[str, Any]]) -> dict[str, Any]:
    default_rows = [row for row in view_rows if row["policy"] == DEFAULT_POLICY]
    return {
        "overall": "pass",
        "network_access_required": False,
        "tasks": len(task_cards),
        "datasets": len({row["dataset"] for row in task_cards}),
        "visible_views": len(POLICIES),
        "view_task_rows": len(view_rows),
        "top_groups_per_view": TOP_K,
        "operation_stack_top5_positive_tasks": sum(row["top5_recall"] > 0 for row in default_rows),
        "operation_stack_top1_positive_tasks": sum(row["top1_positive"] for row in default_rows),
        "operation_stack_median_top5_recall": median(row["top5_recall"] for row in default_rows),
        "operation_stack_median_top5_lift": median(row["top5_lift"] for row in default_rows),
        "operation_stack_median_top5_work": median(row["top5_work"] for row in default_rows),
        "operation_stack_median_first_positive_work": median(
            row["work_to_first_positive"] for row in default_rows if row["work_to_first_positive"] is not None
        ),
        "wins_vs_flat_top5_work": sum(row["operation_stack_beats_flat_work"] for row in task_cards),
        "wins_vs_fixed_top5_recall": sum(row["operation_stack_beats_fixed_recall"] for row in task_cards),
        "wins_vs_fixed_group_count": sum(row["operation_stack_has_fewer_groups_than_fixed"] for row in task_cards),
        "tasks_with_counterpoints": sum(bool(row["counterpoints"]) for row in task_cards),
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# R347 Case-Level Baseline Contrast",
        "",
        "R347 compares top-ranked visible case groups across operation-stack, fixed-session, flat, dataset-native, and raw-action views on the same labeled operations.",
        "",
        "## Summary",
        "",
        f"- Overall: {summary['overall']}.",
        f"- Tasks / datasets / visible views: {summary['tasks']} / {summary['datasets']} / {summary['visible_views']}.",
        f"- Operation-stack top-5 positives: {summary['operation_stack_top5_positive_tasks']}/{summary['tasks']}; top-1 positives: {summary['operation_stack_top1_positive_tasks']}/{summary['tasks']}.",
        f"- Operation-stack median top-5 recall / lift / work: {summary['operation_stack_median_top5_recall']:.4f} / {summary['operation_stack_median_top5_lift']:.4f} / {summary['operation_stack_median_top5_work']:.4f}.",
        f"- Wins vs flat top-5 work: {summary['wins_vs_flat_top5_work']}/{summary['tasks']}.",
        f"- Wins vs fixed-session top-5 recall / group count: {summary['wins_vs_fixed_top5_recall']}/{summary['tasks']} / {summary['wins_vs_fixed_group_count']}/{summary['tasks']}.",
        f"- Tasks with explicit counterpoints: {summary['tasks_with_counterpoints']}/{summary['tasks']}.",
        "",
        "## Task Cards",
        "",
        "| Task | OS recall | OS work | Fixed recall | Best recall policy | Best first-positive policy | Counterpoints |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for row in report["task_cards"]:
        lines.append(
            f"| {row['task']} | {row['operation_stack_top5_recall']:.4f} | {row['operation_stack_top5_work']:.4f} | {row['fixed_session_top5_recall']:.4f} | {row['best_top5_recall_policy']} | {row['best_first_positive_policy']} | {'; '.join(row['counterpoints'])} |"
        )
    lines.extend(
        [
            "",
            "## Claim Scope",
            "",
            "- Supports: case-level baseline tradeoff evidence over real labeled traces.",
            "- Narrows: operation-stack is not the best view for every objective or task.",
            "- Excludes: human productivity, automatic boundary discovery, ecosystem compatibility, and universal selector claims.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_html(report: dict[str, Any]) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['task'])}</td>"
        f"<td>{row['operation_stack_top5_recall']:.4f}</td>"
        f"<td>{row['operation_stack_top5_work']:.4f}</td>"
        f"<td>{row['fixed_session_top5_recall']:.4f}</td>"
        f"<td>{html.escape(row['best_top5_recall_policy'])}</td>"
        f"<td>{html.escape(row['best_first_positive_policy'])}</td>"
        f"<td>{html.escape('; '.join(row['counterpoints']))}</td>"
        "</tr>"
        for row in report["task_cards"]
    )
    summary = report["summary"]
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>R347 Case-Level Baseline Contrast</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #202124; }}
p {{ max-width: 980px; line-height: 1.5; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 24px; font-size: 13px; }}
th, td {{ border-bottom: 1px solid #d7dce2; padding: 7px 8px; text-align: left; vertical-align: top; }}
th {{ background: #edf1f5; }}
</style>
<h1>R347 Case-Level Baseline Contrast</h1>
<p>Overall: {html.escape(summary['overall'])}. Operation-stack top-5 positives on {summary['operation_stack_top5_positive_tasks']}/{summary['tasks']} tasks, top-1 positives on {summary['operation_stack_top1_positive_tasks']}/{summary['tasks']} tasks, median top-5 work {summary['operation_stack_median_top5_work']:.4f}.</p>
<table>
<thead><tr><th>Task</th><th>OS recall</th><th>OS work</th><th>Fixed recall</th><th>Best recall</th><th>Best first positive</th><th>Counterpoints</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</html>
"""


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    operation_files = sorted({Path(task["operation_file"]) for task in r300.TASKS})
    source_status = ensure_sources_tracked_clean([R346_REPORT, R346_TASK_CARDS, *operation_files])
    r346_cards = {row["task"]: row for row in read_csv(R346_TASK_CARDS)}

    view_rows: list[dict[str, Any]] = []
    top_group_rows: list[dict[str, Any]] = []
    for task in r300.TASKS:
        for view, ranker in POLICIES:
            row, top_groups = score_view(task, view, ranker)
            view_rows.append(row)
            top_group_rows.extend(top_groups)

    task_cards = build_task_cards(view_rows, r346_cards)
    pair_rows = build_pair_rows(view_rows)
    report = {
        "run_id": RUN_ID,
        "schema": "agentsight.case-baseline-contrast.v1",
        "profiler_abstractions": ["operation", "operation stack"],
        "input_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "hidden_label_use": "hidden labels score already-ranked visible view outputs only",
            "network_access_required": False,
        },
        "source_status": source_status,
        "summary": build_summary(task_cards, view_rows),
        "task_cards": task_cards,
        "pair_summary": pair_rows,
        "view_rows": view_rows,
        "top_group_rows": top_group_rows,
        "claim_scope": {
            "supported": "operation-stack case groups can be compared directly against flat, fixed-session, dataset-native, and raw-action views on the same labeled operations",
            "narrowed": "operation-stack is a tradeoff point and not a universal best view",
            "not_supported": "human utility, automatic boundary discovery, or complete trace-ecosystem compatibility",
        },
    }

    write_json(out_dir / "case-baseline-contrast-report.json", report)
    write_csv(
        out_dir / "view-case-metrics.csv",
        view_rows,
        [
            "task",
            "dataset",
            "query_family",
            "view",
            "ranker",
            "policy",
            "operations",
            "positives",
            "prevalence",
            "groups",
            "positive_groups",
            "average_precision",
            "ndcg",
            "top1_positive",
            "top1_positive_rate",
            "top1_lift",
            "top5_positive_groups",
            "top5_group_precision",
            "top5_recall",
            "top5_precision",
            "top5_f1",
            "top5_lift",
            "top5_work",
            "work_to_first_positive",
            "rank_to_first_positive",
            "groups_to_50pct_recall",
            "work_to_50pct_recall",
        ],
    )
    write_csv(
        out_dir / "task-baseline-contrast-cards.csv",
        task_cards,
        [
            "task",
            "dataset",
            "query_family",
            "operation_stack_top5_recall",
            "operation_stack_top5_work",
            "operation_stack_top5_lift",
            "operation_stack_top1_positive",
            "flat_top5_work",
            "fixed_session_top5_recall",
            "fixed_session_work_to_first_positive",
            "dataset_native_top5_recall",
            "raw_action_top5_recall",
            "best_top5_recall_policy",
            "best_top5_lift_policy",
            "best_top5_work_policy",
            "best_first_positive_policy",
            "operation_stack_beats_flat_work",
            "operation_stack_beats_fixed_recall",
            "operation_stack_has_fewer_groups_than_fixed",
            "counterpoints",
            "work_takeaway",
            "optimization_action",
        ],
    )
    write_csv(
        out_dir / "baseline-pair-summary.csv",
        pair_rows,
        [
            "baseline",
            "metric",
            "direction",
            "operation_stack_wins",
            "operation_stack_losses",
            "ties",
            "median_delta",
        ],
    )
    write_csv(
        out_dir / "top-group-contrast.csv",
        top_group_rows,
        [
            "task",
            "dataset",
            "view",
            "ranker",
            "rank",
            "group_id",
            "stack",
            "operations",
            "positive_operations",
            "positive_rate",
            "sessions",
        ],
    )
    (out_dir / "case-baseline-contrast-report.md").write_text(render_markdown(report), encoding="utf-8")
    (out_dir / "index.html").write_text(render_html(report), encoding="utf-8")

    run_result = {
        "run_id": RUN_ID,
        "schema": "agentsight.case-baseline-contrast-run.v1",
        "status": "ok",
        "summary": report["summary"],
        "json": rel(out_dir / "case-baseline-contrast-report.json"),
        "markdown": rel(out_dir / "case-baseline-contrast-report.md"),
        "html": rel(out_dir / "index.html"),
    }
    write_json(out_dir / "run-result.json", run_result)
    print(json.dumps(round_value(run_result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
