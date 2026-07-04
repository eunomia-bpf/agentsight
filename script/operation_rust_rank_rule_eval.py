#!/usr/bin/env python3
"""R322: verify Rust visible rank rules on existing labeled traces.

This is an implementation/reproducibility probe for the Rust profiler surface.
It reuses the tracked R300 operation JSONL, runs `agentpprof --profile-spec`
with task-specific visible `rank_rules`, and scores the resulting top groups
with hidden labels only after ranking.
"""

from __future__ import annotations

import csv
import html
import json
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
SOURCE_OPERATIONS = OUT_ROOT / "operation-query-utility-r300" / "query-utility-operations.jsonl"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-rust-rank-rule-r322"
TOP_LIMIT = 20
TOP_K_VALUES = [5, 10]

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_profile_accuracy_eval as r320  # noqa: E402
import operation_query_utility_eval as r300  # noqa: E402


RANK_RULES = {
    "agentreward_looping": [
        "loop-like:4=repeat_signal:loop-like",
        "failure:1.5=status:failure",
        "navigation:0.5=phase:navigate|action:click|action:goto",
    ],
    "agentreward_side_effect": [
        "write-action:4=action:fill|action:press|action:clear|action:select_option",
        "input-phase:2=phase:input",
        "failure:1=status:failure",
    ],
    "satraj_unsafe": [
        "risky-env:3=environment:account|environment:induced_text|environment:popup|environment:unknown_file",
        "write-action:2=action:type|action:key|action:left_click_drag|action:system_command",
        "input-phase:1.5=phase:input",
    ],
    "agentnet_incorrect_step": [
        "failure:4=status:failure|status:unknown",
        "loop-like:1.5=repeat_signal:loop-like",
        "error-env:1=environment:error_correction|environment:infeasible",
        "input-phase:0.5=phase:input",
    ],
    "agentnet_redundant_step": [
        "loop-like:4=repeat_signal:loop-like",
        "failure:1=status:failure|status:unknown",
        "navigation:0.5=phase:navigate|action:click|action:move_to",
    ],
    "osworld_group_start": [
        "input-phase:1.5=phase:input",
        "navigation:1=phase:navigate|action:click|action:move_to",
        "write-action:1=action:type|action:press|action:hotkey|action:drag",
    ],
}


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


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


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_rank_rules() -> dict[str, Any]:
    hidden = set(r320.HIDDEN_FIELDS)
    violations = []
    for task_id, rules in RANK_RULES.items():
        for rule in rules:
            _, pattern = rule.split("=", 1)
            for field in hidden:
                if f"{field}:" in pattern or f"{field}=" in pattern:
                    violations.append({"task": task_id, "rule": rule, "hidden_field": field})
    if violations:
        raise SystemExit(f"rank rules reference hidden fields: {violations}")
    return {
        "status": "pass",
        "hidden_fields": sorted(hidden),
        "rank_rule_fields": sorted(
            {
                chunk.split(":", 1)[0]
                for rules in RANK_RULES.values()
                for rule in rules
                for chunk in rule.split("=", 1)[1].replace("|", " ").split()
                if ":" in chunk
            }
        ),
        "violations": violations,
    }


def stack_label(fields: dict[str, str], stack: list[str]) -> str:
    return ";".join(f"{field}:{fields.get(field, 'unknown')}" for field in stack)


def group_task(task: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in r300.load_task_operations(task):
        grouped[stack_label(operation["fields"], list(task["semantic_stack"]))].append(operation)

    groups = {}
    total_ops = 0
    total_positive = 0
    for stack, rows in grouped.items():
        operations = sum(int(operation["value"]) for operation in rows)
        positives = sum(
            int(operation["value"])
            for operation in rows
            if operation["fields"].get("target_positive") == "positive"
        )
        total_ops += operations
        total_positive += positives
        groups[stack] = {
            "stack": stack,
            "operations": operations,
            "positives": positives,
            "positive_rate": positives / operations if operations else 0.0,
        }

    return groups, {
        "operations": total_ops,
        "positives": total_positive,
        "prevalence": total_positive / total_ops if total_ops else 0.0,
        "groups": len(groups),
    }


def write_profile_spec(out_dir: Path, task: dict[str, Any]) -> Path:
    spec_path = out_dir / f"{task['id']}-profile-spec.json"
    spec = {
        "output": f"{task['id']}-rust-ranked.json",
        "format": "json",
        "view": "operations",
        "operation_files": [str(SOURCE_OPERATIONS.resolve())],
        "stack": ",".join(task["semantic_stack"]),
        "where_rules": [f"analysis_task={task['id']}"],
        "rank_rules": RANK_RULES[task["id"]],
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
            rel(spec_path),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise SystemExit(f"agentpprof failed for {rel(spec_path)}:\n{result.stderr.strip()}")
    return json.loads(result.stdout)


def score_order(
    order: list[str],
    groups: dict[str, dict[str, Any]],
    summary: dict[str, Any],
    k: int,
) -> dict[str, Any]:
    selected = [groups[stack] for stack in order[:k] if stack in groups]
    inspected = sum(group["operations"] for group in selected)
    positives = sum(group["positives"] for group in selected)
    precision = positives / inspected if inspected else 0.0
    recall = positives / summary["positives"] if summary["positives"] else 0.0
    prevalence = summary["prevalence"]
    return {
        f"top{k}_groups": len(selected),
        f"top{k}_work": inspected / summary["operations"] if summary["operations"] else 0.0,
        f"top{k}_precision": precision,
        f"top{k}_recall": recall,
        f"top{k}_lift": precision / prevalence if prevalence else 0.0,
        f"top{k}_positive_operations": positives,
    }


def average_precision(
    order: list[str],
    groups: dict[str, dict[str, Any]],
    total_positive: int,
    limit: int | None = None,
) -> float:
    if total_positive <= 0:
        return 0.0
    cumulative_ops = 0
    cumulative_pos = 0
    weighted_precision = 0.0
    selected_order = order if limit is None else order[:limit]
    for stack in selected_order:
        group = groups.get(stack)
        if not group:
            continue
        cumulative_ops += group["operations"]
        cumulative_pos += group["positives"]
        if group["positives"]:
            weighted_precision += (cumulative_pos / cumulative_ops) * group["positives"]
    return weighted_precision / total_positive


def first_positive(order: list[str], groups: dict[str, dict[str, Any]], total_ops: int) -> dict[str, Any]:
    inspected = 0
    for index, stack in enumerate(order, 1):
        group = groups.get(stack)
        if not group:
            continue
        inspected += group["operations"]
        if group["positives"] > 0:
            return {
                "first_positive_rank": index,
                "first_positive_work": inspected / total_ops if total_ops else 0.0,
            }
    return {"first_positive_rank": None, "first_positive_work": None}


def rounded(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, dict):
        return {key: rounded(child) for key, child in value.items()}
    if isinstance(value, list):
        return [rounded(child) for child in value]
    return value


def evaluate_task(out_dir: Path, task: dict[str, Any]) -> dict[str, Any]:
    groups, summary = group_task(task)
    spec_path = write_profile_spec(out_dir, task)
    result = run_agentpprof(spec_path)
    output = out_dir / f"{task['id']}-rust-ranked.json"
    profile = json.loads(output.read_text(encoding="utf-8"))["profile"]
    stacks = profile["stacks"]
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

    width_order = sorted(stacks, key=lambda stack: (-int(stacks[stack]), stack))
    rust_rank_order = [row["stack"] for row in profile["ranking"]["top"]]
    policies = {
        "width": width_order,
        "rust_visible_rank_rule": rust_rank_order,
    }
    scored = {}
    for policy, order in policies.items():
        metrics: dict[str, Any] = {
            "ap": average_precision(order, groups, summary["positives"]),
            "ap_at_20": average_precision(order, groups, summary["positives"], TOP_LIMIT),
            **first_positive(order, groups, summary["operations"]),
        }
        for k in TOP_K_VALUES:
            metrics.update(score_order(order, groups, summary, k))
        scored[policy] = rounded(metrics)

    rank = scored["rust_visible_rank_rule"]
    width = scored["width"]
    return {
        "task": task["id"],
        "dataset": task["dataset"],
        "problem": task["problem"],
        "profile_spec": rel(spec_path),
        "rust_json": rel(output),
        "agentpprof_result": result,
        "rank_rules": RANK_RULES[task["id"]],
        "summary": summary,
        "metrics": scored,
        "deltas": rounded(
            {
                "ap": rank["ap"] - width["ap"],
                "ap_at_20": rank["ap_at_20"] - width["ap_at_20"],
                "top5_recall": rank["top5_recall"] - width["top5_recall"],
                "top5_lift": rank["top5_lift"] - width["top5_lift"],
                "top10_recall": rank["top10_recall"] - width["top10_recall"],
                "top10_lift": rank["top10_lift"] - width["top10_lift"],
            }
        ),
    }


def write_reports(out_dir: Path, rows: list[dict[str, Any]], leakage_check: dict[str, Any], elapsed_s: float) -> None:
    ap_wins = sum(row["deltas"]["ap"] > 0 for row in rows)
    ap20_wins = sum(row["deltas"]["ap_at_20"] > 0 for row in rows)
    top5_recall_wins = sum(row["deltas"]["top5_recall"] > 0 for row in rows)
    top5_lift_wins = sum(row["deltas"]["top5_lift"] > 0 for row in rows)
    report = {
        "run_id": "R322",
        "status": "pass",
        "source_operations": rel(SOURCE_OPERATIONS),
        "commit": git_output(["rev-parse", "HEAD"]),
        "elapsed_s": round(elapsed_s, 3),
        "tasks": len(rows),
        "top_limit": TOP_LIMIT,
        "summary": {
            "rust_rank_ap_improves_tasks": f"{ap_wins}/{len(rows)}",
            "rust_rank_ap_at_20_improves_tasks": f"{ap20_wins}/{len(rows)}",
            "rust_rank_top5_recall_improves_tasks": f"{top5_recall_wins}/{len(rows)}",
            "rust_rank_top5_lift_improves_tasks": f"{top5_lift_wins}/{len(rows)}",
        },
        "leakage_check": leakage_check,
        "tasks_detail": rows,
        "claim": (
            "Rust agentpprof can emit visible-rule ranked operation-stack groups "
            "that can be scored as localization outputs on existing labeled traces."
        ),
        "non_claims": [
            "This does not replace the full R320 profiler-accuracy benchmark.",
            "This does not claim human analyst productivity or complete boundary detection.",
            "This does not use hidden oracle labels inside rank_rules.",
            "This does not download, sync, or create a new dataset.",
        ],
    }
    write_json(out_dir / "rust-rank-rule-report.json", rounded(report))
    write_json(
        out_dir / "run-result.json",
        {"status": "pass", "report": rel(out_dir / "rust-rank-rule-report.json")},
    )

    with (out_dir / "rust-rank-rule-summary.csv").open("w", encoding="utf-8", newline="") as file:
        fieldnames = [
            "task",
            "dataset",
            "groups",
            "positives",
            "width_ap",
            "rank_ap",
            "delta_ap",
            "width_ap_at_20",
            "rank_ap_at_20",
            "delta_ap_at_20",
            "width_top5_recall",
            "rank_top5_recall",
            "delta_top5_recall",
            "width_top5_lift",
            "rank_top5_lift",
            "delta_top5_lift",
            "width_first_positive_work",
            "rank_first_positive_work",
        ]
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
                    "rank_ap": row["metrics"]["rust_visible_rank_rule"]["ap"],
                    "delta_ap": row["deltas"]["ap"],
                    "width_ap_at_20": row["metrics"]["width"]["ap_at_20"],
                    "rank_ap_at_20": row["metrics"]["rust_visible_rank_rule"]["ap_at_20"],
                    "delta_ap_at_20": row["deltas"]["ap_at_20"],
                    "width_top5_recall": row["metrics"]["width"]["top5_recall"],
                    "rank_top5_recall": row["metrics"]["rust_visible_rank_rule"]["top5_recall"],
                    "delta_top5_recall": row["deltas"]["top5_recall"],
                    "width_top5_lift": row["metrics"]["width"]["top5_lift"],
                    "rank_top5_lift": row["metrics"]["rust_visible_rank_rule"]["top5_lift"],
                    "delta_top5_lift": row["deltas"]["top5_lift"],
                    "width_first_positive_work": row["metrics"]["width"]["first_positive_work"],
                    "rank_first_positive_work": row["metrics"]["rust_visible_rank_rule"]["first_positive_work"],
                }
            )

    lines = [
        "# R322 Rust Visible Rank-Rule Probe",
        "",
        f"- Source operations: `{rel(SOURCE_OPERATIONS)}`",
        f"- Tasks: {len(rows)}",
        f"- AP wins: {ap_wins}/{len(rows)}",
        f"- AP@20 wins: {ap20_wins}/{len(rows)}",
        f"- Top-5 recall wins: {top5_recall_wins}/{len(rows)}",
        f"- Top-5 lift wins: {top5_lift_wins}/{len(rows)}",
        "",
        "| Task | AP width | AP rank | Delta | AP@20 delta | Top-5 recall delta | Top-5 lift delta |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {task} | {w:.4f} | {r:.4f} | {d:.4f} | {d20:.4f} | {dr:.4f} | {dl:.4f} |".format(
                task=row["task"],
                w=row["metrics"]["width"]["ap"],
                r=row["metrics"]["rust_visible_rank_rule"]["ap"],
                d=row["deltas"]["ap"],
                d20=row["deltas"]["ap_at_20"],
                dr=row["deltas"]["top5_recall"],
                dl=row["deltas"]["top5_lift"],
            )
        )
    lines.extend(
        [
            "",
            "This run is an implementation probe. It verifies that the Rust JSON profiler can emit",
            "operation-stack groups ranked by visible stack text, while hidden labels are used only",
            "for offline scoring.",
            "",
        ]
    )
    (out_dir / "rust-rank-rule-report.md").write_text("\n".join(lines), encoding="utf-8")

    body = "\n".join(
        f"<tr><td>{html.escape(row['task'])}</td>"
        f"<td>{row['metrics']['width']['ap']:.4f}</td>"
        f"<td>{row['metrics']['rust_visible_rank_rule']['ap']:.4f}</td>"
        f"<td>{row['deltas']['ap']:.4f}</td>"
        f"<td>{row['deltas']['ap_at_20']:.4f}</td>"
        f"<td>{row['deltas']['top5_recall']:.4f}</td>"
        f"<td>{row['deltas']['top5_lift']:.4f}</td></tr>"
        for row in rows
    )
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>R322 Rust Rank-Rule Probe</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #1f2937; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border-bottom: 1px solid #d1d5db; padding: 8px; text-align: right; }}
th:first-child, td:first-child {{ text-align: left; }}
code {{ background: #f3f4f6; padding: 1px 4px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>R322 Rust Visible Rank-Rule Probe</h1>
<p>Source: <code>{html.escape(rel(SOURCE_OPERATIONS))}</code>. Hidden labels are used only after ranking.</p>
<table>
<thead><tr><th>Task</th><th>AP width</th><th>AP rank</th><th>Delta</th><th>AP@20 delta</th><th>Top-5 recall delta</th><th>Top-5 lift delta</th></tr></thead>
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
    source_paths = sorted({SOURCE_OPERATIONS, *(task["operation_file"] for task in r300.TASKS)})
    ensure_sources_tracked_clean(source_paths)
    leakage_check = validate_rank_rules()
    rows = [evaluate_task(out_dir, task) for task in r300.TASKS]
    write_reports(out_dir, rows, leakage_check, time.perf_counter() - start)


if __name__ == "__main__":
    main()
