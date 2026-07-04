#!/usr/bin/env python3
"""R323: compare Rust operation-stack rank modes on existing labeled traces.

R322 showed that width-multiplied visible rank rules are still dominated by
large stack groups on some tasks. R323 keeps the same public, tracked R300
operation JSONL and the same visible rank rules, but compares the default
`width-boost` policy with a score-first `rule-score` policy in Rust JSON output.
Hidden labels are used only after ranking for scoring.
"""

from __future__ import annotations

import csv
import html
import json
import subprocess
import time
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-rank-mode-r323"
TOP_LIMIT = 20
TOP_K_VALUES = [5, 10]
RANK_MODES = ["width-boost", "rule-score"]

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_query_utility_eval as r300  # noqa: E402
import operation_rust_rank_rule_eval as r322  # noqa: E402


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_profile_spec(out_dir: Path, task: dict[str, Any], rank_mode: str) -> Path:
    spec_path = out_dir / f"{task['id']}-{rank_mode}-profile-spec.json"
    spec = {
        "output": f"{task['id']}-{rank_mode}.json",
        "format": "json",
        "view": "operations",
        "operation_files": [str(r322.SOURCE_OPERATIONS.resolve())],
        "stack": ",".join(task["semantic_stack"]),
        "where_rules": [f"analysis_task={task['id']}"],
        "rank_rules": r322.RANK_RULES[task["id"]],
        "rank_mode": rank_mode,
    }
    write_json(spec_path, spec)
    return spec_path


def run_agentpprof(spec_path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "cargo",
            "run",
            "--quiet",
            "--manifest-path",
            "agentpprof/Cargo.toml",
            "--",
            "--profile-spec",
            r322.rel(spec_path),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise SystemExit(f"agentpprof failed for {r322.rel(spec_path)}:\n{result.stderr.strip()}")
    return json.loads(result.stdout)


def score_policy(
    order: list[str],
    groups: dict[str, dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "ap": r322.average_precision(order, groups, summary["positives"]),
        "ap_at_20": r322.average_precision(order, groups, summary["positives"], TOP_LIMIT),
        **r322.first_positive(order, groups, summary["operations"]),
    }
    for k in TOP_K_VALUES:
        metrics.update(r322.score_order(order, groups, summary, k))
    return r322.rounded(metrics)


def lower_work(left: Any, right: Any) -> bool:
    return left is not None and right is not None and left < right


def evaluate_task(out_dir: Path, task: dict[str, Any]) -> dict[str, Any]:
    groups, summary = r322.group_task(task)
    mode_profiles = {}
    mode_results = {}
    for rank_mode in RANK_MODES:
        spec_path = write_profile_spec(out_dir, task, rank_mode)
        mode_results[rank_mode] = run_agentpprof(spec_path)
        output = out_dir / f"{task['id']}-{rank_mode}.json"
        mode_profiles[rank_mode] = {
            "spec": r322.rel(spec_path),
            "output": r322.rel(output),
            "profile": json.loads(output.read_text(encoding="utf-8"))["profile"],
        }

    stacks = mode_profiles["width-boost"]["profile"]["stacks"]
    missing = sorted(set(stacks) ^ set(groups))
    mismatched_weights = [
        {"stack": stack, "rust": weight, "expected": groups[stack]["operations"]}
        for stack, weight in stacks.items()
        if stack in groups and int(weight) != groups[stack]["operations"]
    ]
    if missing or mismatched_weights:
        raise SystemExit(
            f"Rust stack output did not match expected task groups for {task['id']}: "
            f"missing_or_extra={missing[:3]} mismatched={mismatched_weights[:3]}"
        )

    orders = {
        "width": sorted(stacks, key=lambda stack: (-int(stacks[stack]), stack)),
        "width_boost": [
            row["stack"] for row in mode_profiles["width-boost"]["profile"]["ranking"]["top"]
        ],
        "rule_score": [
            row["stack"] for row in mode_profiles["rule-score"]["profile"]["ranking"]["top"]
        ],
    }
    scored = {policy: score_policy(order, groups, summary) for policy, order in orders.items()}
    rule = scored["rule_score"]
    boost = scored["width_boost"]
    width = scored["width"]
    return {
        "task": task["id"],
        "dataset": task["dataset"],
        "problem": task["problem"],
        "summary": summary,
        "rank_rules": r322.RANK_RULES[task["id"]],
        "profiles": {
            mode: {
                "profile_spec": data["spec"],
                "rust_json": data["output"],
                "agentpprof_result": mode_results[mode],
                "policy": data["profile"]["ranking"]["policy"],
            }
            for mode, data in mode_profiles.items()
        },
        "metrics": scored,
        "deltas": r322.rounded(
            {
                "rule_score_vs_width_boost_ap": rule["ap"] - boost["ap"],
                "rule_score_vs_width_boost_ap_at_20": rule["ap_at_20"] - boost["ap_at_20"],
                "rule_score_vs_width_boost_top5_recall": rule["top5_recall"]
                - boost["top5_recall"],
                "rule_score_vs_width_boost_top5_lift": rule["top5_lift"]
                - boost["top5_lift"],
                "rule_score_vs_width_boost_first_positive_work": (
                    None
                    if rule["first_positive_work"] is None
                    or boost["first_positive_work"] is None
                    else rule["first_positive_work"] - boost["first_positive_work"]
                ),
                "rule_score_vs_width_ap": rule["ap"] - width["ap"],
                "rule_score_vs_width_top5_lift": rule["top5_lift"] - width["top5_lift"],
            }
        ),
    }


def write_reports(
    out_dir: Path,
    rows: list[dict[str, Any]],
    leakage_check: dict[str, Any],
    elapsed_s: float,
) -> None:
    rule_ap_wins = sum(row["deltas"]["rule_score_vs_width_boost_ap"] > 0 for row in rows)
    rule_ap20_wins = sum(row["deltas"]["rule_score_vs_width_boost_ap_at_20"] > 0 for row in rows)
    rule_lift_wins = sum(row["deltas"]["rule_score_vs_width_boost_top5_lift"] > 0 for row in rows)
    rule_recall_wins = sum(
        row["deltas"]["rule_score_vs_width_boost_top5_recall"] > 0 for row in rows
    )
    rule_first_work_wins = sum(
        lower_work(
            row["metrics"]["rule_score"]["first_positive_work"],
            row["metrics"]["width_boost"]["first_positive_work"],
        )
        for row in rows
    )
    report = {
        "run_id": "R323",
        "status": "pass",
        "source_operations": r322.rel(r322.SOURCE_OPERATIONS),
        "commit": r322.git_output(["rev-parse", "HEAD"]),
        "elapsed_s": round(elapsed_s, 3),
        "tasks": len(rows),
        "rank_modes": RANK_MODES,
        "top_limit": TOP_LIMIT,
        "summary": {
            "rule_score_ap_improves_vs_width_boost_tasks": f"{rule_ap_wins}/{len(rows)}",
            "rule_score_ap_at_20_improves_vs_width_boost_tasks": f"{rule_ap20_wins}/{len(rows)}",
            "rule_score_top5_lift_improves_vs_width_boost_tasks": f"{rule_lift_wins}/{len(rows)}",
            "rule_score_top5_recall_improves_vs_width_boost_tasks": f"{rule_recall_wins}/{len(rows)}",
            "rule_score_first_positive_work_improves_vs_width_boost_tasks": f"{rule_first_work_wins}/{len(rows)}",
        },
        "leakage_check": leakage_check,
        "tasks_detail": rows,
        "claim": (
            "Rust agentpprof can expose rank-mode policy as a JSON projection over "
            "operation-stack groups, separating width-dominated ranking from "
            "score-first visible ranking without reading hidden labels."
        ),
        "non_claims": [
            "This does not replace the R320 profiler-accuracy benchmark.",
            "This does not create a learned detector or a human-utility result.",
            "This does not add a profiler abstraction beyond operation and operation stack.",
            "This does not download, sync, or create a new dataset.",
        ],
    }
    write_json(out_dir / "rank-mode-report.json", r322.rounded(report))
    write_json(
        out_dir / "run-result.json",
        {"status": "pass", "report": r322.rel(out_dir / "rank-mode-report.json")},
    )

    fieldnames = [
        "task",
        "dataset",
        "groups",
        "positives",
        "width_ap",
        "width_boost_ap",
        "rule_score_ap",
        "delta_rule_vs_boost_ap",
        "width_boost_top5_lift",
        "rule_score_top5_lift",
        "delta_rule_vs_boost_top5_lift",
        "width_boost_first_positive_work",
        "rule_score_first_positive_work",
        "delta_rule_vs_boost_first_positive_work",
    ]
    with (out_dir / "rank-mode-summary.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "task": row["task"],
                    "dataset": row["dataset"],
                    "groups": row["summary"]["groups"],
                    "positives": row["summary"]["positives"],
                    "width_ap": row["metrics"]["width"]["ap"],
                    "width_boost_ap": row["metrics"]["width_boost"]["ap"],
                    "rule_score_ap": row["metrics"]["rule_score"]["ap"],
                    "delta_rule_vs_boost_ap": row["deltas"]["rule_score_vs_width_boost_ap"],
                    "width_boost_top5_lift": row["metrics"]["width_boost"]["top5_lift"],
                    "rule_score_top5_lift": row["metrics"]["rule_score"]["top5_lift"],
                    "delta_rule_vs_boost_top5_lift": row["deltas"][
                        "rule_score_vs_width_boost_top5_lift"
                    ],
                    "width_boost_first_positive_work": row["metrics"]["width_boost"][
                        "first_positive_work"
                    ],
                    "rule_score_first_positive_work": row["metrics"]["rule_score"][
                        "first_positive_work"
                    ],
                    "delta_rule_vs_boost_first_positive_work": row["deltas"][
                        "rule_score_vs_width_boost_first_positive_work"
                    ],
                }
            )

    lines = [
        "# R323 Rust Rank-Mode Probe",
        "",
        f"- Source operations: `{r322.rel(r322.SOURCE_OPERATIONS)}`",
        f"- Tasks: {len(rows)}",
        f"- Rule-score AP wins vs width-boost: {rule_ap_wins}/{len(rows)}",
        f"- Rule-score AP@20 wins vs width-boost: {rule_ap20_wins}/{len(rows)}",
        f"- Rule-score top-5 lift wins vs width-boost: {rule_lift_wins}/{len(rows)}",
        "",
        "| Task | Width AP | Width-boost AP | Rule-score AP | Rule-score delta | Rule-score top-5 lift delta |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {task} | {width:.4f} | {boost:.4f} | {rule:.4f} | {delta:.4f} | {lift:.4f} |".format(
                task=row["task"],
                width=row["metrics"]["width"]["ap"],
                boost=row["metrics"]["width_boost"]["ap"],
                rule=row["metrics"]["rule_score"]["ap"],
                delta=row["deltas"]["rule_score_vs_width_boost_ap"],
                lift=row["deltas"]["rule_score_vs_width_boost_top5_lift"],
            )
        )
    lines.extend(
        [
            "",
            "This run is a rank-policy mechanism probe over existing operation-stack groups.",
            "It uses the same visible rank rules as R322 and scores hidden labels only after",
            "the Rust profiler has emitted the ranked JSON output.",
            "",
        ]
    )
    (out_dir / "rank-mode-report.md").write_text("\n".join(lines), encoding="utf-8")

    body = "\n".join(
        f"<tr><td>{html.escape(row['task'])}</td>"
        f"<td>{row['metrics']['width']['ap']:.4f}</td>"
        f"<td>{row['metrics']['width_boost']['ap']:.4f}</td>"
        f"<td>{row['metrics']['rule_score']['ap']:.4f}</td>"
        f"<td>{row['deltas']['rule_score_vs_width_boost_ap']:.4f}</td>"
        f"<td>{row['deltas']['rule_score_vs_width_boost_top5_lift']:.4f}</td></tr>"
        for row in rows
    )
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>R323 Rust Rank-Mode Probe</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #1f2937; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border-bottom: 1px solid #d1d5db; padding: 8px; text-align: right; }}
th:first-child, td:first-child {{ text-align: left; }}
code {{ background: #f3f4f6; padding: 1px 4px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>R323 Rust Rank-Mode Probe</h1>
<p>Source: <code>{html.escape(r322.rel(r322.SOURCE_OPERATIONS))}</code>. Hidden labels are used only after ranking.</p>
<table>
<thead><tr><th>Task</th><th>Width AP</th><th>Width-boost AP</th><th>Rule-score AP</th><th>Rule-score delta</th><th>Top-5 lift delta</th></tr></thead>
<tbody>{body}</tbody>
</table>
</body>
</html>
"""
    (out_dir / "index.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    start = time.perf_counter()
    out_dir = DEFAULT_OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    source_paths = sorted({r322.SOURCE_OPERATIONS, *(task["operation_file"] for task in r300.TASKS)})
    r322.ensure_sources_tracked_clean(source_paths)
    leakage_check = r322.validate_rank_rules()
    rows = [evaluate_task(out_dir, task) for task in r300.TASKS]
    write_reports(out_dir, rows, leakage_check, time.perf_counter() - start)


if __name__ == "__main__":
    main()
