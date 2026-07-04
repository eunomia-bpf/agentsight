#!/usr/bin/env python3
"""R313: compute the analysis-view Pareto frontier over existing task artifacts.

R313 does not fetch datasets or rerun profilers. It reads tracked R300, R302,
R305, and R311 artifacts, then asks whether operation stacks appear on the
non-oracle Pareto frontier of real labeled analysis tasks. The point is not to
prove that operation stacks dominate flat or fixed-session views. Instead, the
frontier makes the tradeoff explicit: work, recall, lift, and group count all
matter, and a useful profiler should expose view/ranker choices rather than
hard-code one hierarchy.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import subprocess
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-view-frontier-r313"
SOURCE_PATHS = {
    "r300_query_utility": OUT_ROOT
    / "operation-query-utility-r300"
    / "query-utility-report.json",
    "r302_ranking": OUT_ROOT
    / "operation-analyst-ranking-r302"
    / "ranking-report.json",
    "r305_case_baseline": OUT_ROOT
    / "operation-case-baseline-r305"
    / "case-baseline-report.json",
    "r311_robustness_audit": OUT_ROOT
    / "paper-robustness-audit-r311"
    / "robustness-audit.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


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


def round_value(value: Any) -> Any:
    if isinstance(value, float):
        if math.isinf(value):
            return "inf"
        return round(value, 4)
    if isinstance(value, dict):
        return {key: round_value(child) for key, child in value.items()}
    if isinstance(value, list):
        return [round_value(child) for child in value]
    return value


def median_or_zero(values: list[float]) -> float:
    return float(median(values)) if values else 0.0


def candidate_from_r302(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "task": row["task"],
        "dataset": row["dataset"],
        "view": row["view"],
        "ranker": row["ranker"],
        "budget": row["budget"],
        "source": "R302",
        "oracle": row["ranker"] == "oracle_upper_bound",
        "work": float(row["inspected_operation_fraction"]),
        "recall": float(row["positive_recall"]),
        "lift": float(row["positive_lift"]),
        "precision": float(row["positive_precision"]),
        "groups": int(row["groups_inspected"]),
        "inspected_operations": int(row["inspected_operations"]),
    }


def candidate_from_r305(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "task": row["task"],
        "dataset": row["dataset"],
        "view": row["view"],
        "ranker": "case_query_aware",
        "budget": "top_5_groups",
        "source": "R305",
        "oracle": False,
        "work": float(row["inspected_operation_fraction"]),
        "recall": float(row["positive_recall"]),
        "lift": float(row["positive_lift"]),
        "precision": float(row["positive_precision"]),
        "groups": int(row["groups"]),
        "inspected_operations": int(row["inspected_operations"]),
    }


def dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    eps = 1e-12
    at_least_as_good = (
        left["recall"] >= right["recall"] - eps
        and left["lift"] >= right["lift"] - eps
        and left["work"] <= right["work"] + eps
        and left["groups"] <= right["groups"] + eps
    )
    strictly_better = (
        left["recall"] > right["recall"] + eps
        or left["lift"] > right["lift"] + eps
        or left["work"] < right["work"] - eps
        or left["groups"] < right["groups"] - eps
    )
    return at_least_as_good and strictly_better


def pareto_frontier(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in candidates
        if not any(dominates(other, row) for other in candidates if other is not row)
    ]


def best_by_lift(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return max(candidates, key=lambda row: (row["lift"], row["recall"], -row["work"], -row["groups"]))


def best_recall_under_work(
    candidates: list[dict[str, Any]], max_work: float = 0.30
) -> dict[str, Any]:
    scoped = [row for row in candidates if row["work"] <= max_work + 1e-12]
    if not scoped:
        scoped = candidates
    return max(scoped, key=lambda row: (row["recall"], row["lift"], -row["work"], -row["groups"]))


def lowest_work_positive(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    positive = [row for row in candidates if row["recall"] > 0]
    if not positive:
        return None
    return min(positive, key=lambda row: (row["work"], -row["recall"], -row["lift"]))


def index_unique_tasks(r305: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tasks: dict[str, dict[str, Any]] = {}
    for row in r305["task_view_scores"]:
        tasks.setdefault(
            row["task"],
            {
                "task": row["task"],
                "dataset": row["dataset"],
                "query_family": row["query_family"],
                "problem": row["problem"],
                "operations": int(row["operations"]),
                "positives": int(row["positives"]),
            },
        )
    return tasks


def task_frontier_rows(
    candidates: list[dict[str, Any]], tasks: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    task_rows: list[dict[str, Any]] = []
    frontier_rows: list[dict[str, Any]] = []
    for task in sorted(tasks):
        task_candidates = [row for row in candidates if row["task"] == task and not row["oracle"]]
        frontier = sorted(
            pareto_frontier(task_candidates),
            key=lambda row: (row["work"], -row["recall"], -row["lift"], row["view"], row["ranker"]),
        )
        for row in frontier:
            frontier_rows.append({**row, "frontier": True})

        best_lift = best_by_lift(task_candidates)
        best_budget = best_recall_under_work(task_candidates, 0.30)
        first_positive = lowest_work_positive(task_candidates)
        views_on_frontier = sorted({row["view"] for row in frontier})
        operation_frontier = [row for row in frontier if row["view"] == "operation_stack"]
        fixed_frontier = [row for row in frontier if row["view"] == "fixed_session"]
        flat_frontier = [row for row in frontier if row["view"] == "flat"]
        task_rows.append(
            round_value(
                {
                    **tasks[task],
                    "frontier_candidates": len(frontier),
                    "views_on_frontier": views_on_frontier,
                    "operation_stack_frontier_candidates": len(operation_frontier),
                    "fixed_session_frontier_candidates": len(fixed_frontier),
                    "flat_frontier_candidates": len(flat_frontier),
                    "operation_stack_on_frontier": bool(operation_frontier),
                    "fixed_session_on_frontier": bool(fixed_frontier),
                    "flat_on_frontier": bool(flat_frontier),
                    "best_lift": compact_candidate(best_lift),
                    "best_recall_under_30pct_work": compact_candidate(best_budget),
                    "lowest_work_positive": compact_candidate(first_positive)
                    if first_positive
                    else None,
                    "interpretation": interpretation_for(task, frontier, best_lift, best_budget),
                }
            )
        )
    return task_rows, [round_value(row) for row in frontier_rows]


def compact_candidate(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "view": row["view"],
        "ranker": row["ranker"],
        "budget": row["budget"],
        "source": row["source"],
        "work": row["work"],
        "recall": row["recall"],
        "lift": row["lift"],
        "groups": row["groups"],
    }


def interpretation_for(
    task: str,
    frontier: list[dict[str, Any]],
    best_lift_row: dict[str, Any],
    best_budget_row: dict[str, Any],
) -> str:
    op_on_frontier = any(row["view"] == "operation_stack" for row in frontier)
    fixed_on_frontier = any(row["view"] == "fixed_session" for row in frontier)
    flat_on_frontier = any(row["view"] == "flat" for row in frontier)
    if op_on_frontier and fixed_on_frontier and flat_on_frontier:
        return (
            "operation-stack, fixed-session, and flat views are all nondominated, "
            "so this task needs a configurable view surface rather than a single hierarchy"
        )
    if op_on_frontier and best_lift_row["view"] == "operation_stack":
        return (
            "operation stacks provide the strongest non-oracle lift on this task while "
            "remaining one point in a broader tradeoff surface"
        )
    if op_on_frontier and best_budget_row["view"] == "operation_stack":
        return (
            "operation stacks provide the best recall under the 30 percent inspected-work "
            "budget, but other views remain useful counterpoints"
        )
    if op_on_frontier:
        return (
            "operation stacks remain nondominated, but another view is the best point for "
            "the chosen lift or work-budget objective"
        )
    return (
        f"{task} is a counterexample for operation-stack frontier coverage and should "
        "narrow the claim"
    )


def oracle_headroom_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in sorted({row["task"] for row in candidates}):
        task_candidates = [row for row in candidates if row["task"] == task]
        non_oracle = [row for row in task_candidates if not row["oracle"]]
        oracle = [row for row in task_candidates if row["oracle"]]
        if not oracle:
            continue
        best_non_oracle = best_by_lift(non_oracle)
        best_oracle = best_by_lift(oracle)
        rows.append(
            round_value(
                {
                    "task": task,
                    "best_non_oracle": compact_candidate(best_non_oracle),
                    "best_oracle_upper_bound": compact_candidate(best_oracle),
                    "oracle_lift_gap": best_oracle["lift"] - best_non_oracle["lift"],
                    "oracle_recall_gap": best_oracle["recall"] - best_non_oracle["recall"],
                    "interpretation": "remaining headroom for better visible-field ranking"
                    if best_oracle["lift"] > best_non_oracle["lift"]
                    else "best visible-field ranking matches or exceeds oracle lift on this metric",
                }
            )
        )
    return rows


def summarize(
    tasks: dict[str, dict[str, Any]],
    task_rows: list[dict[str, Any]],
    frontier_rows: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    r311: dict[str, Any],
) -> dict[str, Any]:
    task_count = len(task_rows)
    best_lift_operation = sum(
        1 for row in task_rows if row["best_lift"]["view"] == "operation_stack"
    )
    best_recall_operation = sum(
        1
        for row in task_rows
        if row["best_recall_under_30pct_work"]["view"] == "operation_stack"
    )
    best_lift_fixed = sum(1 for row in task_rows if row["best_lift"]["view"] == "fixed_session")
    best_recall_fixed = sum(
        1 for row in task_rows if row["best_recall_under_30pct_work"]["view"] == "fixed_session"
    )
    return round_value(
        {
            "tasks": task_count,
            "datasets": len({row["dataset"] for row in task_rows}),
            "operations": sum(row["operations"] for row in tasks.values()),
            "positive_operations": sum(row["positives"] for row in tasks.values()),
            "candidate_points": len([row for row in candidates if not row["oracle"]]),
            "oracle_upper_bound_points": len([row for row in candidates if row["oracle"]]),
            "frontier_points": len(frontier_rows),
            "median_frontier_points_per_task": median_or_zero(
                [float(row["frontier_candidates"]) for row in task_rows]
            ),
            "operation_stack_on_frontier": f"{sum(row['operation_stack_on_frontier'] for row in task_rows)}/{task_count}",
            "fixed_session_on_frontier": f"{sum(row['fixed_session_on_frontier'] for row in task_rows)}/{task_count}",
            "flat_on_frontier": f"{sum(row['flat_on_frontier'] for row in task_rows)}/{task_count}",
            "operation_stack_best_lift": f"{best_lift_operation}/{task_count}",
            "operation_stack_best_recall_under_30pct_work": f"{best_recall_operation}/{task_count}",
            "fixed_session_best_lift": f"{best_lift_fixed}/{task_count}",
            "fixed_session_best_recall_under_30pct_work": f"{best_recall_fixed}/{task_count}",
            "r311_counterpoint": r311["summary"],
            "paper_claim": (
                "R313 supports a configurable analysis-surface claim: operation stacks "
                "are consistently nondominated, but flat and fixed-session views remain "
                "real frontier counterpoints. This strengthens C4 as an inspectability "
                "tradeoff and weakens any single-view dominance wording."
            ),
        }
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "task",
        "dataset",
        "view",
        "ranker",
        "budget",
        "source",
        "work",
        "recall",
        "lift",
        "precision",
        "groups",
        "inspected_operations",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def candidate_label(candidate: dict[str, Any] | None) -> str:
    if not candidate:
        return "n/a"
    return (
        f"{candidate['view']}:{candidate['ranker']}:{candidate['budget']} "
        f"(work {candidate['work']}, recall {candidate['recall']}, lift {candidate['lift']})"
    )


def markdown_report(summary: dict[str, Any], task_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Operation View Frontier R313",
        "",
        "R313 reads existing R300/R302/R305/R311 artifacts only. It does not sync datasets or rerun profilers.",
        "",
        "## Summary",
        "",
        f"- Tasks: {summary['tasks']} across {summary['datasets']} datasets.",
        f"- Operations: {summary['operations']:,}; positives: {summary['positive_operations']:,}.",
        f"- Non-oracle candidate points: {summary['candidate_points']}; frontier points: {summary['frontier_points']}.",
        f"- Operation-stack on frontier: {summary['operation_stack_on_frontier']}.",
        f"- Fixed-session on frontier: {summary['fixed_session_on_frontier']}.",
        f"- Flat on frontier: {summary['flat_on_frontier']}.",
        f"- Operation-stack best lift: {summary['operation_stack_best_lift']}.",
        f"- Operation-stack best recall under 30% work: {summary['operation_stack_best_recall_under_30pct_work']}.",
        "",
        "Interpretation: operation stacks are consistently nondominated, but fixed-session and flat views remain real counterpoints. The paper should claim a configurable inspectability tradeoff, not single-view dominance.",
        "",
        "## Task Frontier Rows",
        "",
        "| Task | Frontier views | Best lift | Best recall under 30% work | Interpretation |",
        "|---|---|---|---|---|",
    ]
    for row in task_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["task"],
                    ", ".join(row["views_on_frontier"]),
                    candidate_label(row["best_lift"]),
                    candidate_label(row["best_recall_under_30pct_work"]),
                    row["interpretation"],
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def html_report(summary: dict[str, Any], task_rows: list[dict[str, Any]]) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['task'])}</td>"
        f"<td>{html.escape(', '.join(row['views_on_frontier']))}</td>"
        f"<td>{html.escape(candidate_label(row['best_lift']))}</td>"
        f"<td>{html.escape(candidate_label(row['best_recall_under_30pct_work']))}</td>"
        f"<td>{html.escape(row['interpretation'])}</td>"
        "</tr>"
        for row in task_rows
    )
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Operation View Frontier R313</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.4; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; }}
    th, td {{ border: 1px solid #ddd; padding: 0.45rem; vertical-align: top; }}
    th {{ background: #f5f5f5; text-align: left; }}
    code {{ background: #f6f8fa; padding: 0.1rem 0.25rem; border-radius: 3px; }}
  </style>
</head>
<body>
  <h1>Operation View Frontier R313</h1>
  <p>R313 reads existing tracked artifacts only. It does not sync datasets or rerun profilers.</p>
  <h2>Summary</h2>
  <ul>
    <li>Tasks: {summary['tasks']} across {summary['datasets']} datasets.</li>
    <li>Operations: {summary['operations']:,}; positives: {summary['positive_operations']:,}.</li>
    <li>Operation-stack on frontier: {summary['operation_stack_on_frontier']}.</li>
    <li>Fixed-session on frontier: {summary['fixed_session_on_frontier']}.</li>
    <li>Flat on frontier: {summary['flat_on_frontier']}.</li>
    <li>Operation-stack best lift: {summary['operation_stack_best_lift']}.</li>
    <li>Operation-stack best recall under 30% work: {summary['operation_stack_best_recall_under_30pct_work']}.</li>
  </ul>
  <p>The supported claim is a configurable inspectability tradeoff, not single-view dominance.</p>
  <h2>Task Frontier Rows</h2>
  <table>
    <thead>
      <tr><th>Task</th><th>Frontier views</th><th>Best lift</th><th>Best recall under 30% work</th><th>Interpretation</th></tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</body>
</html>
"""


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    ensure_sources_tracked_clean(list(SOURCE_PATHS.values()))
    out_dir.mkdir(parents=True, exist_ok=True)

    r300 = load_json(SOURCE_PATHS["r300_query_utility"])
    r302 = load_json(SOURCE_PATHS["r302_ranking"])
    r305 = load_json(SOURCE_PATHS["r305_case_baseline"])
    r311 = load_json(SOURCE_PATHS["r311_robustness_audit"])

    candidates = [candidate_from_r302(row) for row in r302["scores"]]
    candidates.extend(candidate_from_r305(row) for row in r305["task_view_scores"])
    tasks = index_unique_tasks(r305)
    task_rows, frontier_rows = task_frontier_rows(candidates, tasks)
    oracle_rows = oracle_headroom_rows(candidates)
    summary = summarize(tasks, task_rows, frontier_rows, candidates, r311)

    report = round_value(
        {
            "run_id": "R313",
            "purpose": "Pareto-frontier audit for configurable operation-stack analysis views",
            "input_policy": {
                "dataset_sync": "none",
                "profiler_rerun": "none",
                "source_artifacts": {key: rel(path) for key, path in SOURCE_PATHS.items()},
            },
            "frontier_metrics": {
                "maximize": ["positive_recall", "positive_lift"],
                "minimize": ["inspected_operation_fraction", "groups_inspected"],
            },
            "summary": summary,
            "task_frontiers": task_rows,
            "frontier_candidates": frontier_rows,
            "oracle_headroom": oracle_rows,
            "claim_scope": {
                "supported": "configurable inspectability tradeoff surface over existing labeled tasks",
                "not_supported": [
                    "operation-stack dominance over every flat or fixed-session point",
                    "human or agent analyst time improvement",
                    "automatic anomaly detection",
                    "oracle-free optimal ranking",
                ],
            },
            "commit": git_output(["rev-parse", "HEAD"]),
        }
    )

    json_path = out_dir / "view-frontier-report.json"
    md_path = out_dir / "view-frontier-report.md"
    csv_path = out_dir / "frontier-candidates.csv"
    html_path = out_dir / "index.html"
    run_path = out_dir / "run-result.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(markdown_report(summary, task_rows), encoding="utf-8")
    write_csv(csv_path, frontier_rows)
    html_path.write_text(html_report(summary, task_rows), encoding="utf-8")
    run_path.write_text(
        json.dumps(
            {
                "run_id": "R313",
                "status": "ok",
                "summary": summary,
                "json": rel(json_path),
                "markdown": rel(md_path),
                "csv": rel(csv_path),
                "html": rel(html_path),
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"run_id": "R313", "status": "ok", "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
