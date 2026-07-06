#!/usr/bin/env python3
"""R354: executable profile-spec patch audit on real labeled agent traces.

This audit turns profiler actionability into a concrete before/after loop:
generate a default operation-stack profile spec, generate a profile-guided
patched spec, run the maintained Rust `agentpprof --profile-spec` path for both,
and score the emitted ranked operation-stack groups with hidden labels only
after profiling.

It does not fetch, sync, create, or relabel datasets. It reuses the tracked R324
visible operation file and R348 action cards. The patch plans are explicit
profile-spec edits, not an automatic deployment selector.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import subprocess
import time
from pathlib import Path
from statistics import median
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
R324_DIR = OUT_ROOT / "operation-rank-feature-r324"
R348_DIR = OUT_ROOT / "operation-action-counterfactual-r348"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-profile-patch-r354"
RUN_ID = "R354"
TOP_K = 5

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_query_utility_eval as r300  # noqa: E402
import operation_rank_feature_eval as r324  # noqa: E402
import operation_rust_rank_rule_eval as r322  # noqa: E402


PATCH_PLANS: dict[str, dict[str, Any]] = {
    "agentreward_looping": {
        "patched_stack_kind": "semantic",
        "patch_steps": [
            "keep repeat_signal in the recursive stack",
            "rank loop-like and failure operations before width",
        ],
        "expected_role": "improve_failure_localization",
    },
    "agentreward_side_effect": {
        "patched_stack_kind": "coarse",
        "patch_steps": [
            "coarsen the stack to benchmark and phase before ranking",
            "rank write/input/failure operations before width",
        ],
        "expected_role": "reduce_side_effect_fragmentation",
    },
    "satraj_unsafe": {
        "patched_stack_kind": "coarse",
        "patch_steps": [
            "coarsen the stack to environment and phase",
            "rank risky environment and write operations before width",
        ],
        "expected_role": "prioritize_safety_relevant_operations",
    },
    "agentnet_incorrect_step": {
        "patched_stack_kind": "semantic",
        "patch_steps": [
            "keep desktop environment, phase, action, repeat_signal, and status frames",
            "rank failure, loop-like, risky-environment, and input operations before width",
        ],
        "expected_role": "prioritize_low_prevalence_quality_errors",
    },
    "agentnet_redundant_step": {
        "patched_stack_kind": "semantic",
        "patch_steps": [
            "keep repeat_signal and action frames",
            "rank loop-like operations before width",
        ],
        "expected_role": "prioritize_redundancy_signals",
    },
    "osworld_group_start": {
        "patched_stack_kind": "semantic",
        "patch_steps": [
            "try visible phase/action rank features without boundary-derived fields",
            "reject this patch if hidden-label scoring shows it does not improve grouping",
        ],
        "expected_role": "negative_control_needs_boundary_backend",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


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
    status: dict[str, str] = {}
    for path in sorted(set(paths)):
        if not path.exists():
            raise SystemExit(f"missing source artifact {rel(path)}")
        git_check("source artifact is not git-tracked", path, ["ls-files", "--error-unmatch"])
        git_check("source artifact has unstaged changes", path, ["diff", "--quiet"])
        git_check("source artifact has staged changes", path, ["diff", "--cached", "--quiet"])
        status[rel(path)] = "tracked_clean"
    return status


def task_by_id() -> dict[str, dict[str, Any]]:
    return {task["id"]: task for task in r300.TASKS}


def stack_for(task: dict[str, Any], stack_kind: str) -> list[str]:
    if stack_kind == "semantic":
        return list(task["semantic_stack"])
    if stack_kind == "coarse":
        return r324.coarse_stack(task)
    raise ValueError(f"unsupported stack kind {stack_kind}")


def write_profile_spec(
    out_dir: Path,
    task: dict[str, Any],
    variant: str,
    stack_kind: str,
    stack: list[str],
    operation_file: Path,
    rank_op_rules: list[str],
) -> Path:
    spec_path = out_dir / f"{task['id']}-{variant}-profile-spec.json"
    spec: dict[str, Any] = {
        "output": f"{task['id']}-{variant}.json",
        "format": "json",
        "view": "operations",
        "operation_files": [str(operation_file.resolve())],
        "stack": ",".join(stack),
        "where_rules": [f"analysis_task={task['id']}"],
    }
    if rank_op_rules:
        spec["rank_op_rules"] = rank_op_rules
        spec["rank_mode"] = "rule-score"
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


def load_profile_output(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    try:
        return payload["profile"]
    except KeyError as exc:
        raise SystemExit(f"{rel(path)} is missing profile output") from exc


def score_profile(task: dict[str, Any], stack: list[str], profile: dict[str, Any]) -> dict[str, Any]:
    groups, summary = r324.group_task_for_stack(task, stack)
    stacks = profile["stacks"]
    missing = sorted(set(stacks) ^ set(groups))
    mismatched_weights = [
        {"stack": stack_label, "rust": weight, "expected": groups[stack_label]["operations"]}
        for stack_label, weight in stacks.items()
        if stack_label in groups and int(weight) != groups[stack_label]["operations"]
    ]
    if missing or mismatched_weights:
        raise SystemExit(
            f"Rust stack output did not match hidden-label scorer for {task['id']}: "
            f"missing_or_extra={missing[:3]} mismatched={mismatched_weights[:3]}"
        )

    ranking = profile.get("ranking") or {}
    top_rows = ranking.get("top") or []
    if top_rows:
        order = [row["stack"] for row in top_rows]
    else:
        order = sorted(stacks, key=lambda stack_label: (-int(stacks[stack_label]), stack_label))
    metrics = {
        "ap": r322.average_precision(order, groups, summary["positives"]),
        "ap_at_20": r322.average_precision(order, groups, summary["positives"], 20),
        **r322.score_order(order, groups, summary, TOP_K),
        **r322.first_positive(order, groups, summary["operations"]),
    }
    return {
        "summary": summary,
        "metrics": r322.rounded(metrics),
        "top_stacks": [
            {
                "rank": index + 1,
                "stack": stack_label,
                "operations": groups[stack_label]["operations"],
                "positives": groups[stack_label]["positives"],
                "positive_rate": groups[stack_label]["positive_rate"],
            }
            for index, stack_label in enumerate(order[:TOP_K])
            if stack_label in groups
        ],
        "ranking_policy": ranking.get("policy", "width"),
    }


def metric_delta(patched: dict[str, Any], default: dict[str, Any], metric: str) -> float | None:
    left = patched["metrics"].get(metric)
    right = default["metrics"].get(metric)
    if left is None or right is None:
        return None
    return float(left) - float(right)


def classify_patch(row: dict[str, Any]) -> str:
    improves_ap = row["delta_ap"] is not None and row["delta_ap"] > 0
    improves_first_positive = (
        row["delta_first_positive_work"] is not None and row["delta_first_positive_work"] < 0
    )
    improves_top5_lift = row["delta_top5_lift"] is not None and row["delta_top5_lift"] > 0
    if improves_ap and (improves_first_positive or improves_top5_lift):
        return "accept_patch"
    if improves_ap:
        return "accept_patch_ap_only"
    return "reject_patch_or_needs_new_mapping"


def evaluate_task(
    out_dir: Path,
    task: dict[str, Any],
    action_card: dict[str, str],
    operation_file: Path,
) -> dict[str, Any]:
    plan = PATCH_PLANS[task["id"]]
    default_stack = stack_for(task, "semantic")
    patched_stack_kind = plan["patched_stack_kind"]
    patched_stack = stack_for(task, patched_stack_kind)
    default_spec = write_profile_spec(
        out_dir,
        task,
        "default-semantic-width",
        "semantic",
        default_stack,
        operation_file,
        [],
    )
    patched_spec = write_profile_spec(
        out_dir,
        task,
        f"patched-{patched_stack_kind}-op-features",
        patched_stack_kind,
        patched_stack,
        operation_file,
        r324.OP_RANK_RULES[task["id"]],
    )
    default_result = run_agentpprof(default_spec)
    patched_result = run_agentpprof(patched_spec)
    default_profile = load_profile_output(out_dir / f"{task['id']}-default-semantic-width.json")
    patched_profile = load_profile_output(out_dir / f"{task['id']}-patched-{patched_stack_kind}-op-features.json")
    default_score = score_profile(task, default_stack, default_profile)
    patched_score = score_profile(task, patched_stack, patched_profile)
    row = {
        "task": task["id"],
        "dataset": task["dataset"],
        "query_family": task["query_family"],
        "default_stack_kind": "semantic",
        "patched_stack_kind": patched_stack_kind,
        "default_groups": default_score["summary"]["groups"],
        "patched_groups": patched_score["summary"]["groups"],
        "default_ap": default_score["metrics"]["ap"],
        "patched_ap": patched_score["metrics"]["ap"],
        "delta_ap": metric_delta(patched_score, default_score, "ap"),
        "default_top5_lift": default_score["metrics"][f"top{TOP_K}_lift"],
        "patched_top5_lift": patched_score["metrics"][f"top{TOP_K}_lift"],
        "delta_top5_lift": metric_delta(patched_score, default_score, f"top{TOP_K}_lift"),
        "default_top5_work": default_score["metrics"][f"top{TOP_K}_work"],
        "patched_top5_work": patched_score["metrics"][f"top{TOP_K}_work"],
        "delta_top5_work": metric_delta(patched_score, default_score, f"top{TOP_K}_work"),
        "default_first_positive_work": default_score["metrics"]["first_positive_work"],
        "patched_first_positive_work": patched_score["metrics"]["first_positive_work"],
        "delta_first_positive_work": metric_delta(
            patched_score, default_score, "first_positive_work"
        ),
        "default_profile_spec": rel(default_spec),
        "patched_profile_spec": rel(patched_spec),
        "default_rust_json": rel(out_dir / f"{task['id']}-default-semantic-width.json"),
        "patched_rust_json": rel(out_dir / f"{task['id']}-patched-{patched_stack_kind}-op-features.json"),
        "patch_steps": plan["patch_steps"],
        "expected_role": plan["expected_role"],
        "r348_optimization_action": action_card.get("optimization_action", ""),
        "r348_counterpoints": action_card.get("case_counterpoints", ""),
        "default_agentpprof_result": default_result,
        "patched_agentpprof_result": patched_result,
        "default_top_stacks": default_score["top_stacks"],
        "patched_top_stacks": patched_score["top_stacks"],
    }
    row["patch_verdict"] = classify_patch(row)
    return row


def summarize(rows: list[dict[str, Any]], elapsed_s: float, source_status: dict[str, str]) -> dict[str, Any]:
    accepted = [row for row in rows if row["patch_verdict"].startswith("accept")]
    rejected = [row for row in rows if row["patch_verdict"].startswith("reject")]
    ap_deltas = [row["delta_ap"] for row in rows if row["delta_ap"] is not None]
    lift_deltas = [row["delta_top5_lift"] for row in rows if row["delta_top5_lift"] is not None]
    fp_deltas = [
        row["delta_first_positive_work"]
        for row in rows
        if row["delta_first_positive_work"] is not None
    ]
    group_reductions = [
        1 - (row["patched_groups"] / row["default_groups"])
        for row in rows
        if row["default_groups"]
    ]
    return {
        "run_id": RUN_ID,
        "status": "pass",
        "commit": r322.git_output(["rev-parse", "HEAD"]),
        "elapsed_s": round(elapsed_s, 3),
        "tasks": len(rows),
        "datasets": len({row["dataset"] for row in rows}),
        "source_status": source_status,
        "profiler_input": rel(R324_DIR / "visible-query-utility-operations.jsonl"),
        "summary": {
            "accepted_patches": f"{len(accepted)}/{len(rows)}",
            "rejected_or_needs_mapping": f"{len(rejected)}/{len(rows)}",
            "ap_improved_tasks": f"{sum(delta > 0 for delta in ap_deltas)}/{len(rows)}",
            "top5_lift_improved_tasks": f"{sum(delta > 0 for delta in lift_deltas)}/{len(rows)}",
            "first_positive_work_improved_tasks": f"{sum(delta < 0 for delta in fp_deltas)}/{len(rows)}",
            "groups_reduced_tasks": f"{sum(delta > 0 for delta in group_reductions)}/{len(rows)}",
            "median_delta_ap": median(ap_deltas) if ap_deltas else 0.0,
            "median_delta_top5_lift": median(lift_deltas) if lift_deltas else 0.0,
            "median_delta_first_positive_work": median(fp_deltas) if fp_deltas else 0.0,
            "median_group_reduction": median(group_reductions) if group_reductions else 0.0,
        },
        "tasks_detail": rows,
        "claim": (
            "Profile-guided changes can be materialized as executable profile-spec "
            "patches over the same operation file; hidden labels score the before/after "
            "profiles after Rust profiling."
        ),
        "non_claims": [
            "This is not a human or agent analyst study.",
            "This is not an automatic label-free patch selector.",
            "Rejected patches remain evidence of where a new mapping or boundary backend is needed.",
            "The only profiler objects are operations and operation stacks; profile specs are reproducibility wrappers.",
        ],
    }


def write_reports(out_dir: Path, report: dict[str, Any]) -> None:
    rows = report["tasks_detail"]
    write_json(out_dir / "profile-patch-report.json", report)
    write_json(
        out_dir / "run-result.json",
        {"status": "pass", "report": rel(out_dir / "profile-patch-report.json")},
    )
    csv_fields = [
        "task",
        "dataset",
        "query_family",
        "default_stack_kind",
        "patched_stack_kind",
        "default_groups",
        "patched_groups",
        "default_ap",
        "patched_ap",
        "delta_ap",
        "default_top5_lift",
        "patched_top5_lift",
        "delta_top5_lift",
        "default_top5_work",
        "patched_top5_work",
        "delta_top5_work",
        "default_first_positive_work",
        "patched_first_positive_work",
        "delta_first_positive_work",
        "patch_verdict",
        "expected_role",
        "r348_optimization_action",
        "r348_counterpoints",
        "default_profile_spec",
        "patched_profile_spec",
    ]
    write_csv(out_dir / "profile-patch-summary.csv", rows, csv_fields)

    lines = [
        "# R354 Profile-Guided Patch Audit",
        "",
        f"- Overall: {report['status']}.",
        f"- Accepted patches: {report['summary']['accepted_patches']}.",
        f"- AP improved tasks: {report['summary']['ap_improved_tasks']}.",
        f"- Top-5 lift improved tasks: {report['summary']['top5_lift_improved_tasks']}.",
        f"- First-positive work improved tasks: {report['summary']['first_positive_work_improved_tasks']}.",
        f"- Median delta AP: {report['summary']['median_delta_ap']:.4f}.",
        f"- Median group reduction: {report['summary']['median_group_reduction']:.4f}.",
        "",
        "| Task | Patch | AP delta | Top-5 lift delta | First-positive work delta | Verdict |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {task} | {default_stack_kind}->{patched_stack_kind} | {delta_ap:.4f} | {delta_lift:.4f} | {delta_fp:.4f} | {verdict} |".format(
                task=row["task"],
                default_stack_kind=row["default_stack_kind"],
                patched_stack_kind=row["patched_stack_kind"],
                delta_ap=row["delta_ap"] or 0.0,
                delta_lift=row["delta_top5_lift"] or 0.0,
                delta_fp=row["delta_first_positive_work"] or 0.0,
                verdict=row["patch_verdict"],
            )
        )
    lines.extend(
        [
            "",
            "Hidden labels are used only after both profile specs have been executed by Rust.",
            "The OSWorld-Human row is intentionally allowed to reject the visible rank-feature patch; it points to boundary-derived fields rather than a universal ranker.",
            "",
        ]
    )
    (out_dir / "profile-patch-report.md").write_text("\n".join(lines), encoding="utf-8")

    table_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['task'])}</td>"
        f"<td>{html.escape(row['default_stack_kind'])}->{html.escape(row['patched_stack_kind'])}</td>"
        f"<td>{row['default_ap']:.4f}</td>"
        f"<td>{row['patched_ap']:.4f}</td>"
        f"<td>{row['delta_ap']:.4f}</td>"
        f"<td>{row['delta_top5_lift']:.4f}</td>"
        f"<td>{row['delta_first_positive_work']:.4f}</td>"
        f"<td>{html.escape(row['patch_verdict'])}</td>"
        "</tr>"
        for row in rows
    )
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>R354 Profile-Guided Patch Audit</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #1f2937; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border-bottom: 1px solid #d1d5db; padding: 8px; text-align: right; }}
th:first-child, td:first-child, th:nth-child(2), td:nth-child(2), th:last-child, td:last-child {{ text-align: left; }}
code {{ background: #f3f4f6; padding: 1px 4px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>R354 Profile-Guided Patch Audit</h1>
<p>Profiler input: <code>{html.escape(report['profiler_input'])}</code>. Hidden labels score before/after profile outputs only after Rust executes each profile spec.</p>
<table>
<thead><tr><th>Task</th><th>Patch</th><th>Default AP</th><th>Patched AP</th><th>Delta AP</th><th>Delta top-5 lift</th><th>Delta first-positive work</th><th>Verdict</th></tr></thead>
<tbody>{table_rows}</tbody>
</table>
</body>
</html>
"""
    (out_dir / "index.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    start = time.perf_counter()
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    action_cards = {row["task"]: row for row in read_csv(R348_DIR / "task-action-counterfactual-cards.csv")}
    source_paths = [
        R324_DIR / "rank-feature-report.json",
        R324_DIR / "rank-feature-summary.csv",
        R324_DIR / "visible-query-utility-operations.jsonl",
        R348_DIR / "action-counterfactual-report.json",
        R348_DIR / "task-action-counterfactual-cards.csv",
        *(task["operation_file"] for task in r300.TASKS),
    ]
    source_status = ensure_sources_tracked_clean(source_paths)
    r324.validate_visible_operation_file(R324_DIR / "visible-query-utility-operations.jsonl")
    r324.validate_op_rank_rules()

    tasks = task_by_id()
    rows = [
        evaluate_task(
            out_dir,
            tasks[task_id],
            action_cards.get(task_id, {}),
            R324_DIR / "visible-query-utility-operations.jsonl",
        )
        for task_id in PATCH_PLANS
    ]
    report = summarize(rows, time.perf_counter() - start, source_status)
    write_reports(out_dir, report)
    print(json.dumps({"status": "pass", "report": rel(out_dir / "profile-patch-report.json")}, sort_keys=True))


if __name__ == "__main__":
    main()
