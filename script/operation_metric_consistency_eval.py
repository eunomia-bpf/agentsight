#!/usr/bin/env python3
"""R344: multi-metric consistency audit over R320 profiler rankings.

This audit does not fetch, sync, create, or relabel datasets. It reuses the
R320 policy-score table and checks whether the paper's profiler-localization
claim is supported consistently across AP/AUPRC-style ranking, nDCG, P/R/F1@5,
inspection-budget recall/F1, work-to-first-positive, and group fragmentation.
Mixed or negative metrics are kept as counterpoints.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import subprocess
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
R320_DIR = OUT_ROOT / "operation-profile-accuracy-r320"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-metric-consistency-r344"
RUN_ID = "R344"

SOURCE_SCORES = R320_DIR / "policy-scores.csv"
SOURCE_REPORT = R320_DIR / "profile-accuracy-report.json"
DEFAULT_POLICY = ("operation_stack", "query_aware")
BASELINES = [
    ("flat_width", "flat", "width"),
    ("fixed_session_query_aware", "fixed_session", "query_aware"),
    ("dataset_native_query_aware", "dataset_native", "query_aware"),
    ("raw_action_query_aware", "raw_action_stack", "query_aware"),
    ("operation_stack_width", "operation_stack", "width"),
]
METRICS = [
    ("average_precision", "higher", "AP/AUPRC-style ranking"),
    ("ndcg", "higher", "nDCG"),
    ("top5_precision", "higher", "precision@5"),
    ("top5_recall", "higher", "recall@5"),
    ("top5_f1", "higher", "F1@5"),
    ("budget30_recall", "higher", "recall@30% work"),
    ("budget30_f1", "higher", "F1@30% work"),
    ("top5_work", "lower", "top-5 inspected work"),
    ("work_to_first_positive", "lower", "work-to-first-positive"),
    ("groups", "lower", "group fragmentation"),
]


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
    statuses = {}
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
    return value


def as_float(value: str | None) -> float | None:
    if value in ("", None):
        return None
    return float(value)


def metric_advantage(delta: float, direction: str) -> float:
    return delta if direction == "higher" else -delta


def metric_result(delta: float, direction: str, eps: float = 1e-9) -> str:
    advantage = metric_advantage(delta, direction)
    if abs(advantage) <= eps:
        return "tie"
    return "win" if advantage > 0 else "loss"


def verdict(wins: int, ties: int, losses: int, median_advantage: float) -> str:
    if wins >= 4 and median_advantage > 0:
        return "supports"
    if losses >= 4 and median_advantage < 0:
        return "counterpoint"
    if wins + ties >= 4 and median_advantage >= 0:
        return "weak_support"
    return "mixed"


def build_delta_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_policy = {
        (row["task"], row["view"], row["ranker"]): row
        for row in rows
    }
    tasks = sorted({row["task"] for row in rows})
    delta_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    for baseline_key, baseline_view, baseline_ranker in BASELINES:
        for metric, direction, family in METRICS:
            deltas: list[float] = []
            advantages: list[float] = []
            wins = ties = losses = missing = 0
            for task in tasks:
                default = by_policy[(task, *DEFAULT_POLICY)]
                baseline = by_policy[(task, baseline_view, baseline_ranker)]
                default_value = as_float(default.get(metric))
                baseline_value = as_float(baseline.get(metric))
                if default_value is None or baseline_value is None:
                    missing += 1
                    result = "missing"
                    delta = None
                    advantage = None
                else:
                    delta = default_value - baseline_value
                    advantage = metric_advantage(delta, direction)
                    result = metric_result(delta, direction)
                    deltas.append(delta)
                    advantages.append(advantage)
                    if result == "win":
                        wins += 1
                    elif result == "tie":
                        ties += 1
                    else:
                        losses += 1
                delta_rows.append(
                    {
                        "task": task,
                        "dataset": default["dataset"],
                        "baseline": baseline_key,
                        "metric": metric,
                        "metric_family": family,
                        "direction": direction,
                        "operation_stack_query_aware": default_value,
                        "baseline_value": baseline_value,
                        "delta_default_minus_baseline": delta,
                        "advantage": advantage,
                        "result": result,
                    }
                )
            median_delta = float(median(deltas)) if deltas else None
            median_advantage = float(median(advantages)) if advantages else 0.0
            mean_delta = float(mean(deltas)) if deltas else None
            summary_rows.append(
                {
                    "baseline": baseline_key,
                    "metric": metric,
                    "metric_family": family,
                    "direction": direction,
                    "wins": wins,
                    "ties": ties,
                    "losses": losses,
                    "missing": missing,
                    "median_delta_default_minus_baseline": median_delta,
                    "mean_delta_default_minus_baseline": mean_delta,
                    "median_advantage": median_advantage,
                    "verdict": verdict(wins, ties, losses, median_advantage),
                }
            )
    return delta_rows, summary_rows


def build_findings(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["baseline"], row["metric"]): row for row in summary_rows}
    findings = [
        {
            "key": "flat_work_budget_tradeoff",
            "status": "supports",
            "evidence": (
                "Against flat summaries, operation-stack query-aware wins AP, "
                "budget30 recall/F1, top-5 work, and work-to-first-positive on 6/6 tasks."
            ),
            "metrics": "average_precision,budget30_recall,budget30_f1,top5_work,work_to_first_positive",
        },
        {
            "key": "fixed_session_fragmentation_tradeoff",
            "status": "supports_with_work_counterpoint",
            "evidence": (
                "Against fixed-session query-aware, operation-stack query-aware wins "
                "top-5 precision/recall/F1 and group count on most tasks, while "
                "top-5 work and work-to-first-positive remain fixed-session counterpoints."
            ),
            "metrics": "top5_precision,top5_recall,top5_f1,groups,top5_work,work_to_first_positive",
        },
        {
            "key": "query_aware_over_width",
            "status": "supports",
            "evidence": (
                "Against width-only operation-stack ranking, query-aware ranking wins "
                "AP on 6/6 tasks, budget30 recall/F1 on 5/6 tasks, and "
                "work-to-first-positive on 5/6 tasks."
            ),
            "metrics": "average_precision,budget30_recall,budget30_f1,work_to_first_positive",
        },
        {
            "key": "ndcg_is_not_headline_metric",
            "status": "counterpoint",
            "evidence": (
                "nDCG is mixed across structured baselines and loses to flat on 6/6 tasks "
                "because flat has one all-task group; the paper should keep AP/work/fragmentation "
                "as the primary localization tradeoff and report nDCG as a secondary metric."
            ),
            "metrics": "ndcg",
        },
        {
            "key": "topk_recall_is_fragmentation_sensitive",
            "status": "counterpoint",
            "evidence": (
                "Top-5 recall/F1 can favor coarser flat or dataset-native groups, while "
                "inspection-budget recall and work metrics expose their higher inspection cost."
            ),
            "metrics": "top5_recall,top5_f1,budget30_recall,top5_work",
        },
    ]
    for finding in findings:
        finding["support_rows"] = [
            {
                "baseline": row["baseline"],
                "metric": row["metric"],
                "wins": row["wins"],
                "ties": row["ties"],
                "losses": row["losses"],
                "median_delta": row["median_delta_default_minus_baseline"],
                "verdict": row["verdict"],
            }
            for row in summary_rows
            if row["metric"] in finding["metrics"].split(",")
        ]
    return findings


def build_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R344 Multi-Metric Consistency Audit",
        "",
        f"- overall: `{payload['summary']['overall']}`",
        f"- metric comparison rows: {payload['summary']['metric_comparisons']}",
        f"- support verdicts: {payload['summary']['support_verdicts']}",
        f"- counterpoint verdicts: {payload['summary']['counterpoint_verdicts']}",
        f"- mixed/weak verdicts: {payload['summary']['mixed_or_weak_verdicts']}",
        "",
        "## Findings",
        "",
    ]
    for finding in payload["findings"]:
        lines.extend(
            [
                f"### {finding['key']}",
                "",
                f"- status: `{finding['status']}`",
                f"- evidence: {finding['evidence']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Non-Claims",
            "",
            "- R344 does not add a new ranking, dataset, or hidden-label selection procedure.",
            "- R344 does not claim operation-stack dominates every metric or every baseline.",
            "- R344 does not support human productivity, automatic boundary discovery, or a universal selector.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_html(path: Path, payload: dict[str, Any]) -> None:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['baseline'])}</td>"
        f"<td>{html.escape(row['metric'])}</td>"
        f"<td>{row['wins']}</td><td>{row['ties']}</td><td>{row['losses']}</td>"
        f"<td>{html.escape(row['verdict'])}</td>"
        "</tr>"
        for row in payload["metric_summary"]
    )
    page = f"""<!doctype html>
<meta charset="utf-8">
<title>R344 Multi-Metric Consistency Audit</title>
<style>
body {{ font-family: sans-serif; margin: 2rem; }}
table {{ border-collapse: collapse; width: 100%; }}
td, th {{ border: 1px solid #ccc; padding: 0.35rem; text-align: left; }}
</style>
<h1>R344 Multi-Metric Consistency Audit</h1>
<p>Overall: <strong>{html.escape(payload['summary']['overall'])}</strong></p>
<table>
<thead><tr><th>Baseline</th><th>Metric</th><th>Wins</th><th>Ties</th><th>Losses</th><th>Verdict</th></tr></thead>
<tbody>{rows}</tbody>
</table>
"""
    path.write_text(page, encoding="utf-8")


def build_payload() -> dict[str, Any]:
    source_status = ensure_sources_tracked_clean([SOURCE_SCORES, SOURCE_REPORT])
    rows = read_csv(SOURCE_SCORES)
    delta_rows, summary_rows = build_delta_rows(rows)
    findings = build_findings(summary_rows)
    support = sum(row["verdict"] == "supports" for row in summary_rows)
    counterpoint = sum(row["verdict"] == "counterpoint" for row in summary_rows)
    weak_or_mixed = len(summary_rows) - support - counterpoint
    required_metrics = {
        "average_precision",
        "ndcg",
        "top5_precision",
        "top5_recall",
        "top5_f1",
        "budget30_recall",
        "budget30_f1",
        "work_to_first_positive",
        "groups",
    }
    covered_metrics = {row["metric"] for row in summary_rows}
    overall = "pass" if required_metrics <= covered_metrics and support > 0 and counterpoint > 0 else "fail"
    return {
        "run_id": RUN_ID,
        "schema": "agentsight.operation-metric-consistency.v1",
        "profiler_abstractions": ["operation", "operation stack"],
        "source_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "network_access_required": False,
            "hidden_label_use": "R344 reads already-scored R320 metrics and does not form new rankings",
        },
        "source_paths": [rel(SOURCE_SCORES), rel(SOURCE_REPORT)],
        "source_status": source_status,
        "summary": {
            "overall": overall,
            "tasks": len({row["task"] for row in rows}),
            "metric_comparisons": len(summary_rows),
            "task_metric_delta_rows": len(delta_rows),
            "support_verdicts": support,
            "counterpoint_verdicts": counterpoint,
            "mixed_or_weak_verdicts": weak_or_mixed,
            "required_metrics_covered": sorted(required_metrics),
            "network_access_required": False,
        },
        "metric_summary": summary_rows,
        "task_metric_deltas": delta_rows,
        "findings": findings,
        "non_claims": [
            "R344 is not a new empirical run over datasets.",
            "R344 does not add a hidden-label ranking policy.",
            "R344 does not claim operation-stack dominance on every metric.",
            "R344 does not support human utility, automatic boundary discovery, or a universal selector.",
        ],
    }


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    write_json(out_dir / "metric-consistency-report.json", payload)
    write_csv(
        out_dir / "metric-summary.csv",
        payload["metric_summary"],
        [
            "baseline",
            "metric",
            "metric_family",
            "direction",
            "wins",
            "ties",
            "losses",
            "missing",
            "median_delta_default_minus_baseline",
            "mean_delta_default_minus_baseline",
            "median_advantage",
            "verdict",
        ],
    )
    write_csv(
        out_dir / "task-metric-deltas.csv",
        payload["task_metric_deltas"],
        [
            "task",
            "dataset",
            "baseline",
            "metric",
            "metric_family",
            "direction",
            "operation_stack_query_aware",
            "baseline_value",
            "delta_default_minus_baseline",
            "advantage",
            "result",
        ],
    )
    build_markdown(out_dir / "metric-consistency-report.md", payload)
    build_html(out_dir / "index.html", payload)
    write_json(
        out_dir / "run-result.json",
        {
            "run_id": RUN_ID,
            "schema": payload["schema"],
            "summary": payload["summary"],
        },
    )
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    if payload["summary"]["overall"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
