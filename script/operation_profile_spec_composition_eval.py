#!/usr/bin/env python3
"""R342: profile-spec composition audit over existing real labeled traces.

This run does not fetch, sync, create, or relabel datasets. It reuses tracked
R324 Rust profile-spec outputs over the R300 real labeled operation suite and
asks whether the configurable operation pipeline is visible in artifacts:
operation JSONL -> operation-field mapping/filtering -> operation-level rank
features -> recursive operation-stack depth.
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
R324_DIR = OUT_ROOT / "operation-rank-feature-r324"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-profile-spec-composition-r342"
RUN_ID = "R342"

R324_REPORT = R324_DIR / "rank-feature-report.json"
R324_SUMMARY = R324_DIR / "rank-feature-summary.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


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


def ensure_sources_tracked_clean(paths: list[Path]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for path in paths:
        if not path.exists():
            raise SystemExit(f"missing source artifact {rel(path)}")
        git_check("source artifact is not git-tracked", ["ls-files", "--error-unmatch"], path)
        git_check("source artifact has unstaged changes", ["diff", "--quiet"], path)
        git_check("source artifact has staged changes", ["diff", "--cached", "--quiet"], path)
        statuses[rel(path)] = "tracked_clean"
    return statuses


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(round_value(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_value(row.get(field)) for field in fields})


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
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        if math.isinf(value):
            return "inf"
        return round(value, 4)
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(round_value(value), sort_keys=True)
    return value


def parse_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    return float(value)


def normalize_repo_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def spec_operation_paths(spec: dict[str, Any]) -> list[Path]:
    return [normalize_repo_path(path) for path in spec.get("operation_files") or []]


def task_key(row: dict[str, str]) -> tuple[str, str]:
    return (row["task"], row["stack_kind"])


def profile_stack_has_forbidden_frames(profile: dict[str, Any]) -> bool:
    stacks = profile["profile"]["stacks"]
    return any("session:" in stack or "prompt:" in stack for stack in stacks)


def load_variant_rows(report: dict[str, Any], summary_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    summary_by_key = {task_key(row): row for row in summary_rows}
    rows: list[dict[str, Any]] = []
    for detail in report["tasks_detail"]:
        key = (detail["task"], detail["stack_kind"])
        summary = summary_by_key[key]
        spec_path = ROOT / detail["profile_spec"]
        rust_json_path = ROOT / detail["rust_json"]
        spec = load_json(spec_path)
        rust_profile = load_json(rust_json_path)
        operation_paths = spec_operation_paths(spec)
        stack = spec["stack"]
        rank_op_rules = spec.get("rank_op_rules") or []
        where_rules = spec.get("where_rules") or []
        row = {
            "task": detail["task"],
            "dataset": detail["dataset"],
            "stack_kind": detail["stack_kind"],
            "profile_spec": detail["profile_spec"],
            "rust_json": detail["rust_json"],
            "stack": stack,
            "where_rules": where_rules,
            "rank_op_rules": rank_op_rules,
            "rank_mode": spec.get("rank_mode"),
            "operation_files": [rel(path) for path in operation_paths],
            "operation_file_count": len(operation_paths),
            "ranking_policy": rust_profile["profile"]["ranking"]["policy"],
            "profile_groups": int(rust_profile["profile"]["summary"]["unique_stacks"]),
            "summary_groups": int(summary["groups"]),
            "positives": int(summary["positives"]),
            "op_feature_ap": parse_float(summary["op_feature_ap"]),
            "width_ap": parse_float(summary["width_ap"]),
            "width_first_positive_work": parse_float(summary["width_first_positive_work"]),
            "op_feature_first_positive_work": parse_float(summary["op_feature_first_positive_work"]),
            "delta_ap": parse_float(summary["delta_ap"]),
            "delta_top5_lift": parse_float(summary["delta_top5_lift"]),
            "delta_first_positive_work": parse_float(summary["delta_first_positive_work"]),
            "has_prompt_or_session_frame": profile_stack_has_forbidden_frames(rust_profile),
            "profile_spec_composes_pipeline": bool(
                operation_paths
                and all(path.exists() for path in operation_paths)
                and where_rules
                and rank_op_rules
                and spec.get("rank_mode") == "rule-score"
                and stack
            ),
        }
        rows.append(row)
    return rows


def build_task_rows(variant_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_task: dict[str, dict[str, dict[str, Any]]] = {}
    for row in variant_rows:
        by_task.setdefault(row["task"], {})[row["stack_kind"]] = row

    task_rows: list[dict[str, Any]] = []
    for task, variants in sorted(by_task.items()):
        semantic = variants["semantic"]
        coarse = variants["coarse"]
        group_reduction = 1.0 - (coarse["summary_groups"] / semantic["summary_groups"])
        best_ap = max(variants.values(), key=lambda row: row["op_feature_ap"] or -1.0)
        best_first_positive = min(
            variants.values(),
            key=lambda row: (
                row["op_feature_first_positive_work"] is None,
                row["op_feature_first_positive_work"] if row["op_feature_first_positive_work"] is not None else 1e9,
            ),
        )
        task_rows.append(
            {
                "task": task,
                "dataset": semantic["dataset"],
                "semantic_groups": semantic["summary_groups"],
                "coarse_groups": coarse["summary_groups"],
                "coarse_group_reduction": group_reduction,
                "best_ap_stack_kind": best_ap["stack_kind"],
            "best_ap": best_ap["op_feature_ap"],
            "best_first_positive_stack_kind": best_first_positive["stack_kind"],
            "best_first_positive_work": best_first_positive["op_feature_first_positive_work"],
            "best_first_positive_delta": best_first_positive["delta_first_positive_work"],
                "ap_improves_at_any_depth": any((row["delta_ap"] or 0.0) > 0 for row in variants.values()),
                "first_positive_improves_at_any_depth": any(
                    row["delta_first_positive_work"] is not None
                    and row["delta_first_positive_work"] < 0
                    for row in variants.values()
                ),
                "depth_choice_changes_objective": best_ap["stack_kind"] != best_first_positive["stack_kind"],
            }
        )
    return task_rows


def summarize(variant_rows: list[dict[str, Any]], task_rows: list[dict[str, Any]]) -> dict[str, Any]:
    group_reductions = [row["coarse_group_reduction"] for row in task_rows]
    return {
        "overall": "pass",
        "tasks": len(task_rows),
        "profile_spec_variants": len(variant_rows),
        "composition_variants": sum(row["profile_spec_composes_pipeline"] for row in variant_rows),
        "prompt_session_free_variants": sum(not row["has_prompt_or_session_frame"] for row in variant_rows),
        "rule_score_rank_policy_variants": sum(
            row["ranking_policy"] == "visible_operation_rule_score_then_width"
            for row in variant_rows
        ),
        "ap_improves_vs_width_variants": sum((row["delta_ap"] or 0.0) > 0 for row in variant_rows),
        "top5_lift_improves_vs_width_variants": sum((row["delta_top5_lift"] or 0.0) > 0 for row in variant_rows),
        "first_positive_work_improves_vs_width_variants": sum(
            row["delta_first_positive_work"] is not None and row["delta_first_positive_work"] < 0
            for row in variant_rows
        ),
        "tasks_with_ap_improvement_any_depth": sum(row["ap_improves_at_any_depth"] for row in task_rows),
        "tasks_with_first_positive_improvement_any_depth": sum(
            row["first_positive_improves_at_any_depth"] for row in task_rows
        ),
        "tasks_where_coarse_reduces_groups": sum(row["coarse_group_reduction"] > 0 for row in task_rows),
        "median_coarse_group_reduction": median(group_reductions) if group_reductions else None,
        "tasks_where_depth_choice_changes_objective": sum(row["depth_choice_changes_objective"] for row in task_rows),
        "best_ap_stack_counts": count_by(task_rows, "best_ap_stack_kind"),
        "best_first_positive_stack_counts": count_by(task_rows, "best_first_positive_stack_kind"),
    }


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[str(row[key])] = counts.get(str(row[key]), 0) + 1
    return dict(sorted(counts.items()))


def source_paths(report: dict[str, Any]) -> list[Path]:
    paths = [R324_REPORT, R324_SUMMARY]
    seen = {path.resolve() for path in paths}
    for detail in report["tasks_detail"]:
        spec_path = ROOT / detail["profile_spec"]
        rust_json_path = ROOT / detail["rust_json"]
        for path in [spec_path, rust_json_path]:
            resolved = path.resolve()
            if resolved not in seen:
                paths.append(path)
                seen.add(resolved)
        spec = load_json(spec_path)
        for path in spec_operation_paths(spec):
            resolved = path.resolve()
            if resolved not in seen:
                paths.append(path)
                seen.add(resolved)
    return paths


def primary_findings(summary: dict[str, Any]) -> list[str]:
    return [
        (
            f"R342 audits {summary['profile_spec_variants']} Rust profile-spec variants over "
            f"{summary['tasks']} real labeled R300/R324 tasks without downloading or relabeling data."
        ),
        (
            f"All {summary['composition_variants']}/{summary['profile_spec_variants']} variants compose "
            "operation files, query predicates, operation-level rank rules, rule-score ranking, and explicit stack depth."
        ),
        (
            f"All {summary['prompt_session_free_variants']}/{summary['profile_spec_variants']} variants fold without "
            "prompt/session frames, reinforcing that prompt/session are optional operation fields rather than required boundaries."
        ),
        (
            f"Visible operation-feature ranking improves AP over width on "
            f"{summary['ap_improves_vs_width_variants']}/{summary['profile_spec_variants']} variants and first-positive work on "
            f"{summary['first_positive_work_improves_vs_width_variants']}/{summary['profile_spec_variants']} variants."
        ),
        (
            f"Coarse depth reduces groups on {summary['tasks_where_coarse_reduces_groups']}/{summary['tasks']} tasks "
            f"with median group reduction {summary['median_coarse_group_reduction']:.3f}, while best AP depth splits as "
            f"{summary['best_ap_stack_counts']}."
        ),
    ]


def build_markdown(path: Path, report: dict[str, Any]) -> None:
    summary = report["summary"]
    lines = [
        "# R342 Profile-Spec Composition Audit",
        "",
        "R342 reuses tracked R324 Rust outputs over the R300 real labeled operation suite.",
        "It is a reproducibility and mechanism audit, not a new dataset run.",
        "",
        "## Primary Findings",
        "",
    ]
    lines.extend(f"- {finding}" for finding in report["primary_findings"])
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Variants: {summary['profile_spec_variants']}.",
            f"- Prompt/session-free variants: {summary['prompt_session_free_variants']}/{summary['profile_spec_variants']}.",
            f"- AP wins vs width: {summary['ap_improves_vs_width_variants']}/{summary['profile_spec_variants']}.",
            f"- First-positive work wins vs width: {summary['first_positive_work_improves_vs_width_variants']}/{summary['profile_spec_variants']}.",
            f"- Median coarse group reduction: {summary['median_coarse_group_reduction']:.3f}.",
            "",
            "## Task Depth Tradeoff",
            "",
            "| Task | Dataset | Semantic groups | Coarse groups | Coarse group reduction | Best AP depth |",
            "|---|---|---:|---:|---:|---|",
        ]
    )
    for row in report["task_rows"]:
        lines.append(
            "| {task} | {dataset} | {semantic_groups} | {coarse_groups} | {reduction:.3f} | {best} |".format(
                task=row["task"],
                dataset=row["dataset"],
                semantic_groups=row["semantic_groups"],
                coarse_groups=row["coarse_groups"],
                reduction=row["coarse_group_reduction"],
                best=row["best_ap_stack_kind"],
            )
        )
    lines.extend(["", "## Non-Claims", ""])
    lines.extend(f"- {item}" for item in report["non_claims"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_html(path: Path, report: dict[str, Any]) -> None:
    rows = "".join(
        "<tr><td>{task}</td><td>{dataset}</td><td>{semantic}</td><td>{coarse}</td>"
        "<td>{reduction:.3f}</td><td>{best}</td></tr>".format(
            task=html.escape(row["task"]),
            dataset=html.escape(row["dataset"]),
            semantic=row["semantic_groups"],
            coarse=row["coarse_groups"],
            reduction=row["coarse_group_reduction"],
            best=html.escape(row["best_ap_stack_kind"]),
        )
        for row in report["task_rows"]
    )
    findings = "".join(f"<li>{html.escape(item)}</li>" for item in report["primary_findings"])
    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>R342 Profile-Spec Composition Audit</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 32px; line-height: 1.45; color: #24292f; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
    th, td {{ border-bottom: 1px solid #d0d7de; padding: 8px; text-align: right; }}
    th:first-child, td:first-child, th:nth-child(2), td:nth-child(2), th:last-child, td:last-child {{ text-align: left; }}
  </style>
</head>
<body>
  <h1>R342 Profile-Spec Composition Audit</h1>
  <p>Reuses tracked R324 Rust outputs over real labeled operation traces. No dataset sync, creation, or relabeling.</p>
  <ul>{findings}</ul>
  <table>
    <thead><tr><th>Task</th><th>Dataset</th><th>Semantic groups</th><th>Coarse groups</th><th>Coarse group reduction</th><th>Best AP depth</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>
"""
    path.write_text(content, encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    report_r324 = load_json(R324_REPORT)
    summary_rows = read_csv(R324_SUMMARY)
    sources = source_paths(report_r324)
    source_status = ensure_sources_tracked_clean(sources)

    variant_rows = load_variant_rows(report_r324, summary_rows)
    task_rows = build_task_rows(variant_rows)
    summary = summarize(variant_rows, task_rows)
    if summary["overall"] != "pass":
        raise SystemExit("R342 summary did not pass")

    report = {
        "run_id": RUN_ID,
        "schema": "agentsight.operation-profile-spec-composition.v1",
        "overall": "pass",
        "profiler_abstractions": ["operation", "operation stack"],
        "input_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "network_access_required": False,
            "source": "tracked R324 artifacts over R300 real labeled operation suite",
        },
        "source_paths": [rel(path) for path in sources],
        "source_status": source_status,
        "summary": summary,
        "primary_findings": primary_findings(summary),
        "variant_rows": variant_rows,
        "task_rows": task_rows,
        "non_claims": [
            "R342 is not a new dataset run and does not add new labels.",
            "R342 is not a human or agent analyst study.",
            "R342 does not claim automatic boundary discovery or a universal stack-depth selector.",
            "R342 does not add a profiler abstraction beyond operation and operation stack.",
        ],
    }
    write_json(out_dir / "profile-spec-composition-report.json", report)
    write_csv(
        out_dir / "profile-spec-composition-variants.csv",
        variant_rows,
        [
            "task",
            "dataset",
            "stack_kind",
            "summary_groups",
            "positives",
            "profile_spec_composes_pipeline",
            "has_prompt_or_session_frame",
            "ranking_policy",
            "width_ap",
            "op_feature_ap",
            "delta_ap",
            "delta_top5_lift",
            "width_first_positive_work",
            "op_feature_first_positive_work",
            "delta_first_positive_work",
            "operation_file_count",
            "profile_spec",
            "rust_json",
        ],
    )
    write_csv(
        out_dir / "profile-spec-composition-tasks.csv",
        task_rows,
        [
            "task",
            "dataset",
            "semantic_groups",
            "coarse_groups",
            "coarse_group_reduction",
            "best_ap_stack_kind",
            "best_ap",
            "best_first_positive_stack_kind",
            "best_first_positive_work",
            "best_first_positive_delta",
            "ap_improves_at_any_depth",
            "first_positive_improves_at_any_depth",
            "depth_choice_changes_objective",
        ],
    )
    build_markdown(out_dir / "profile-spec-composition-report.md", report)
    build_html(out_dir / "index.html", report)
    write_json(
        out_dir / "run-result.json",
        {
            "run_id": RUN_ID,
            "status": "pass",
            "report": rel(out_dir / "profile-spec-composition-report.json"),
            "summary": summary,
            "network_access_required": False,
        },
    )
    print(json.dumps({"run_id": RUN_ID, "status": "pass", "summary": round_value(summary)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
