#!/usr/bin/env python3
"""R325: leave-one-feature ablation for Rust operation rank features.

R324 showed that Rust `rank_op_rules` can rank folded operation-stack groups
using visible per-operation feature density.  R325 asks which visible features
matter, which ones mislead, and whether semantic versus coarse stack depth is
the better action for each real labeled task.  Rust profiles only the scrubbed
visible-operation JSONL emitted by R324; hidden labels are not passed to Rust
and are used only by the offline scorer.
"""

from __future__ import annotations

import csv
import html
import json
import re
import time
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-rank-feature-ablation-r325"
R324_VISIBLE_OPERATIONS = (
    OUT_ROOT / "operation-rank-feature-r324" / "visible-query-utility-operations.jsonl"
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_query_utility_eval as r300  # noqa: E402
import operation_rank_feature_eval as r324  # noqa: E402
import operation_rust_rank_rule_eval as r322  # noqa: E402


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rule_label(rule: str) -> str:
    return rule.split("=", 1)[0].split(":", 1)[0]


def slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value)
    return value.strip("-").lower() or "policy"


def fmt_optional(value: float | None) -> str:
    return "" if value is None else f"{value:.4f}"


def policy_specs(rules: list[str]) -> list[dict[str, Any]]:
    rows = [
        {
            "policy": "width",
            "kind": "baseline",
            "dropped_feature": "",
            "rank_op_rules": [],
        },
        {
            "policy": "all_features",
            "kind": "all",
            "dropped_feature": "",
            "rank_op_rules": rules,
        },
    ]
    for rule in rules:
        label = rule_label(rule)
        rows.append(
            {
                "policy": f"drop_{label}",
                "kind": "drop_one",
                "dropped_feature": label,
                "rank_op_rules": [candidate for candidate in rules if candidate != rule],
                "dropped_rule": rule,
            }
        )
    return rows


def write_profile_spec(
    out_dir: Path,
    task: dict[str, Any],
    stack_kind: str,
    stack: list[str],
    policy: dict[str, Any],
    operation_file: Path,
) -> Path:
    stem = f"{task['id']}-{stack_kind}-{slug(policy['policy'])}"
    spec_path = out_dir / f"{stem}-profile-spec.json"
    spec: dict[str, Any] = {
        "output": f"{stem}.json",
        "format": "json",
        "view": "operations",
        "operation_files": [str(operation_file.resolve())],
        "stack": ",".join(stack),
        "where_rules": [f"analysis_task={task['id']}"],
        "rank_mode": "rule-score",
    }
    if policy["rank_op_rules"]:
        spec["rank_op_rules"] = policy["rank_op_rules"]
    write_json(spec_path, spec)
    return spec_path


def evaluate_policy(
    out_dir: Path,
    task: dict[str, Any],
    stack_kind: str,
    stack: list[str],
    policy: dict[str, Any],
    groups: dict[str, dict[str, Any]],
    summary: dict[str, Any],
    operation_file: Path,
) -> dict[str, Any]:
    spec_path = write_profile_spec(out_dir, task, stack_kind, stack, policy, operation_file)
    result = r324.run_agentpprof(spec_path)
    output = out_dir / f"{task['id']}-{stack_kind}-{slug(policy['policy'])}.json"
    profile = json.loads(output.read_text(encoding="utf-8"))["profile"]
    stacks = profile["stacks"]
    missing = sorted(set(stacks) ^ set(groups))
    mismatched_weights = [
        {"stack": stack_label, "rust": weight, "expected": groups[stack_label]["operations"]}
        for stack_label, weight in stacks.items()
        if stack_label in groups and int(weight) != groups[stack_label]["operations"]
    ]
    if missing or mismatched_weights:
        raise SystemExit(
            f"Rust stack output did not match expected groups for {task['id']} "
            f"{stack_kind} {policy['policy']}: missing_or_extra={missing[:3]} "
            f"mismatched={mismatched_weights[:3]}"
        )
    order = [row["stack"] for row in profile["ranking"]["top"]]
    metrics = r324.score_policy(order, groups, summary)
    return {
        "task": task["id"],
        "dataset": task["dataset"],
        "problem": task["problem"],
        "stack_kind": stack_kind,
        "stack": stack,
        "policy": policy["policy"],
        "policy_kind": policy["kind"],
        "dropped_feature": policy.get("dropped_feature", ""),
        "dropped_rule": policy.get("dropped_rule", ""),
        "rank_op_rules": policy["rank_op_rules"],
        "groups": summary["groups"],
        "operations": summary["operations"],
        "positives": summary["positives"],
        "profile_spec": r322.rel(spec_path),
        "rust_json": r322.rel(output),
        "agentpprof_result": result,
        "metrics": metrics,
        "top_features": [
            {
                "stack": row["stack"],
                "rank_score": row["rank_score"],
                "features": row.get("rank_operation_features", []),
            }
            for row in profile["ranking"]["top"][:3]
        ],
    }


def metric_delta(left: dict[str, Any], right: dict[str, Any], metric: str) -> float | None:
    if left[metric] is None or right[metric] is None:
        return None
    return left[metric] - right[metric]


def annotate_deltas(rows: list[dict[str, Any]]) -> None:
    by_key = {(row["task"], row["stack_kind"], row["policy"]): row for row in rows}
    for row in rows:
        width = by_key[(row["task"], row["stack_kind"], "width")]
        all_features = by_key[(row["task"], row["stack_kind"], "all_features")]
        row["delta_vs_width"] = r322.rounded(
            {
                "ap": metric_delta(row["metrics"], width["metrics"], "ap"),
                "ap_at_20": metric_delta(row["metrics"], width["metrics"], "ap_at_20"),
                "top5_lift": metric_delta(row["metrics"], width["metrics"], "top5_lift"),
                "first_positive_work": metric_delta(
                    row["metrics"], width["metrics"], "first_positive_work"
                ),
            }
        )
        row["delta_vs_all_features"] = r322.rounded(
            {
                "ap": metric_delta(row["metrics"], all_features["metrics"], "ap"),
                "ap_at_20": metric_delta(
                    row["metrics"], all_features["metrics"], "ap_at_20"
                ),
                "top5_lift": metric_delta(
                    row["metrics"], all_features["metrics"], "top5_lift"
                ),
                "first_positive_work": metric_delta(
                    row["metrics"], all_features["metrics"], "first_positive_work"
                ),
            }
        )


def feature_findings(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings = []
    for row in rows:
        if row["policy_kind"] != "drop_one":
            continue
        delta = row["delta_vs_all_features"]
        ap_delta = delta["ap"] or 0.0
        fp_delta = delta["first_positive_work"]
        helpful = ap_delta <= -0.02 or (fp_delta is not None and fp_delta >= 0.05)
        harmful = ap_delta >= 0.02 or (fp_delta is not None and fp_delta <= -0.05)
        if helpful or harmful:
            findings.append(
                {
                    "task": row["task"],
                    "dataset": row["dataset"],
                    "stack_kind": row["stack_kind"],
                    "feature": row["dropped_feature"],
                    "rule": row["dropped_rule"],
                    "classification": "critical" if helpful else "misleading",
                    "drop_delta_ap_vs_all": ap_delta,
                    "drop_delta_top5_lift_vs_all": delta["top5_lift"],
                    "drop_delta_first_positive_work_vs_all": fp_delta,
                }
            )
    return sorted(
        r322.rounded(findings),
        key=lambda row: (
            row["classification"] != "critical",
            row["drop_delta_ap_vs_all"],
            row["task"],
            row["stack_kind"],
            row["feature"],
        ),
    )


def stack_depth_findings(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["task"], row["stack_kind"], row["policy"]): row for row in rows}
    out = []
    for task in r300.TASKS:
        semantic = by_key[(task["id"], "semantic", "all_features")]
        coarse = by_key[(task["id"], "coarse", "all_features")]
        sem_ap = semantic["metrics"]["ap"]
        coarse_ap = coarse["metrics"]["ap"]
        preferred = "coarse" if coarse_ap >= sem_ap else "semantic"
        out.append(
            r322.rounded(
                {
                    "task": task["id"],
                    "dataset": task["dataset"],
                    "preferred_by_ap": preferred,
                    "semantic_ap": sem_ap,
                    "coarse_ap": coarse_ap,
                    "coarse_minus_semantic_ap": coarse_ap - sem_ap,
                    "semantic_groups": semantic["groups"],
                    "coarse_groups": coarse["groups"],
                    "group_reduction": semantic["groups"] - coarse["groups"],
                }
            )
        )
    return out


def wins(rows: list[dict[str, Any]], stack_kind: str, metric: str, positive: bool = True) -> str:
    selected = [
        row
        for row in rows
        if row["stack_kind"] == stack_kind and row["policy"] == "all_features"
    ]
    count = sum(
        (row["delta_vs_width"][metric] > 0 if positive else row["delta_vs_width"][metric] < 0)
        for row in selected
        if row["delta_vs_width"][metric] is not None
    )
    return f"{count}/{len(selected)}"


def write_reports(
    out_dir: Path,
    rows: list[dict[str, Any]],
    leakage_check: dict[str, Any],
    profiler_input_check: dict[str, Any],
    elapsed_s: float,
) -> None:
    annotate_deltas(rows)
    feature_rows = feature_findings(rows)
    stack_rows = stack_depth_findings(rows)
    summary = {
        "semantic_all_feature_ap_improves_vs_width_tasks": wins(rows, "semantic", "ap"),
        "semantic_all_feature_first_positive_work_improves_vs_width_tasks": wins(
            rows, "semantic", "first_positive_work", positive=False
        ),
        "coarse_all_feature_ap_improves_vs_width_tasks": wins(rows, "coarse", "ap"),
        "coarse_all_feature_first_positive_work_improves_vs_width_tasks": wins(
            rows, "coarse", "first_positive_work", positive=False
        ),
        "critical_feature_instances": sum(
            row["classification"] == "critical" for row in feature_rows
        ),
        "misleading_feature_instances": sum(
            row["classification"] == "misleading" for row in feature_rows
        ),
        "coarse_preferred_by_ap_tasks": f"{sum(row['preferred_by_ap'] == 'coarse' for row in stack_rows)}/{len(stack_rows)}",
    }
    report = {
        "run_id": "R325",
        "status": "pass",
        "source_operations": r322.rel(r322.SOURCE_OPERATIONS),
        "profiler_operation_file": r322.rel(R324_VISIBLE_OPERATIONS),
        "commit": r322.git_output(["rev-parse", "HEAD"]),
        "elapsed_s": round(elapsed_s, 3),
        "tasks": len(r300.TASKS),
        "policies": sorted({row["policy"] for row in rows}),
        "summary": summary,
        "leakage_check": leakage_check,
        "profiler_input_check": profiler_input_check,
        "feature_findings": feature_rows,
        "stack_depth_findings": stack_rows,
        "policy_rows": rows,
        "claim": (
            "Visible operation rank features are actionable knobs: leave-one-out "
            "ablation identifies which fields drive localization gains and which "
            "tasks require a different stack depth or boundary-derived field."
        ),
        "non_claims": [
            "This is not a learned detector or a human/agent analyst study.",
            "This does not add abstractions beyond operation and operation stack.",
            "Rust receives only scrubbed visible operations; hidden labels are not passed to Rust and are used only for offline scoring.",
            "Feature rules are hand-authored visible policies and may exploit visible correlates.",
        ],
    }
    write_json(out_dir / "rank-feature-ablation-report.json", r322.rounded(report))
    write_json(
        out_dir / "run-result.json",
        {
            "status": "pass",
            "report": r322.rel(out_dir / "rank-feature-ablation-report.json"),
        },
    )
    write_csv(out_dir, rows, feature_rows, stack_rows)
    write_markdown(out_dir, summary, feature_rows, stack_rows)
    write_html(out_dir, summary, feature_rows, stack_rows)


def write_csv(
    out_dir: Path,
    rows: list[dict[str, Any]],
    feature_rows: list[dict[str, Any]],
    stack_rows: list[dict[str, Any]],
) -> None:
    with (out_dir / "rank-feature-ablation-summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as file:
        fieldnames = [
            "task",
            "dataset",
            "stack_kind",
            "policy",
            "policy_kind",
            "dropped_feature",
            "groups",
            "ap",
            "delta_ap_vs_width",
            "delta_ap_vs_all_features",
            "top5_lift",
            "delta_top5_lift_vs_all_features",
            "first_positive_work",
            "delta_first_positive_work_vs_all_features",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "task": row["task"],
                    "dataset": row["dataset"],
                    "stack_kind": row["stack_kind"],
                    "policy": row["policy"],
                    "policy_kind": row["policy_kind"],
                    "dropped_feature": row["dropped_feature"],
                    "groups": row["groups"],
                    "ap": row["metrics"]["ap"],
                    "delta_ap_vs_width": row["delta_vs_width"]["ap"],
                    "delta_ap_vs_all_features": row["delta_vs_all_features"]["ap"],
                    "top5_lift": row["metrics"]["top5_lift"],
                    "delta_top5_lift_vs_all_features": row["delta_vs_all_features"][
                        "top5_lift"
                    ],
                    "first_positive_work": row["metrics"]["first_positive_work"],
                    "delta_first_positive_work_vs_all_features": row[
                        "delta_vs_all_features"
                    ]["first_positive_work"],
                }
            )
    with (out_dir / "rank-feature-findings.csv").open(
        "w", encoding="utf-8", newline=""
    ) as file:
        fieldnames = [
            "task",
            "dataset",
            "stack_kind",
            "feature",
            "classification",
            "drop_delta_ap_vs_all",
            "drop_delta_top5_lift_vs_all",
            "drop_delta_first_positive_work_vs_all",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in feature_rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
    with (out_dir / "rank-feature-stack-depth.csv").open(
        "w", encoding="utf-8", newline=""
    ) as file:
        fieldnames = [
            "task",
            "dataset",
            "preferred_by_ap",
            "semantic_ap",
            "coarse_ap",
            "coarse_minus_semantic_ap",
            "semantic_groups",
            "coarse_groups",
            "group_reduction",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in stack_rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_markdown(
    out_dir: Path,
    summary: dict[str, Any],
    feature_rows: list[dict[str, Any]],
    stack_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# R325 Operation Rank-Feature Ablation",
        "",
        f"- Profiler input: `{r322.rel(R324_VISIBLE_OPERATIONS)}`",
        f"- Semantic AP wins vs width: {summary['semantic_all_feature_ap_improves_vs_width_tasks']}",
        f"- Coarse AP wins vs width: {summary['coarse_all_feature_ap_improves_vs_width_tasks']}",
        f"- Critical feature instances: {summary['critical_feature_instances']}",
        f"- Misleading feature instances: {summary['misleading_feature_instances']}",
        f"- Coarse preferred by AP: {summary['coarse_preferred_by_ap_tasks']}",
        "",
        "## Critical And Misleading Features",
        "",
        "| Task | Stack | Feature | Class | Drop AP Delta | Drop WTFP Delta |",
        "|---|---|---|---|---:|---:|",
    ]
    for row in feature_rows[:30]:
        lines.append(
            f"| {row['task']} | {row['stack_kind']} | {row['feature']} | "
            f"{row['classification']} | {row['drop_delta_ap_vs_all']:.4f} | "
            f"{fmt_optional(row['drop_delta_first_positive_work_vs_all'])} |"
        )
    lines.extend(
        [
            "",
            "## Stack Depth",
            "",
            "| Task | Preferred | Semantic AP | Coarse AP | Group Reduction |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for row in stack_rows:
        lines.append(
            f"| {row['task']} | {row['preferred_by_ap']} | {row['semantic_ap']:.4f} | "
            f"{row['coarse_ap']:.4f} | {row['group_reduction']} |"
        )
    lines.append(
        "\nRust receives only scrubbed visible operations; hidden labels are not passed to Rust and are used only for offline scoring."
    )
    (out_dir / "rank-feature-ablation-report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def write_html(
    out_dir: Path,
    summary: dict[str, Any],
    feature_rows: list[dict[str, Any]],
    stack_rows: list[dict[str, Any]],
) -> None:
    feature_html = "\n".join(
        f"<tr><td>{html.escape(row['task'])}</td><td>{html.escape(row['stack_kind'])}</td>"
        f"<td>{html.escape(row['feature'])}</td><td>{html.escape(row['classification'])}</td>"
        f"<td>{row['drop_delta_ap_vs_all']:.4f}</td>"
        f"<td>{fmt_optional(row['drop_delta_first_positive_work_vs_all'])}</td></tr>"
        for row in feature_rows[:40]
    )
    stack_html = "\n".join(
        f"<tr><td>{html.escape(row['task'])}</td><td>{html.escape(row['preferred_by_ap'])}</td>"
        f"<td>{row['semantic_ap']:.4f}</td><td>{row['coarse_ap']:.4f}</td>"
        f"<td>{row['group_reduction']}</td></tr>"
        for row in stack_rows
    )
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>R325 Operation Rank-Feature Ablation</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #1f2937; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; }}
th, td {{ border-bottom: 1px solid #d1d5db; padding: 8px; text-align: right; }}
th:first-child, td:first-child, th:nth-child(2), td:nth-child(2), th:nth-child(3), td:nth-child(3), th:nth-child(4), td:nth-child(4) {{ text-align: left; }}
code {{ background: #f3f4f6; padding: 1px 4px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>R325 Operation Rank-Feature Ablation</h1>
<p>Profiler input: <code>{html.escape(r322.rel(R324_VISIBLE_OPERATIONS))}</code>. Hidden labels are not passed to Rust and are used only for offline scoring.</p>
<ul>
<li>Semantic AP wins vs width: {summary['semantic_all_feature_ap_improves_vs_width_tasks']}</li>
<li>Coarse AP wins vs width: {summary['coarse_all_feature_ap_improves_vs_width_tasks']}</li>
<li>Critical feature instances: {summary['critical_feature_instances']}</li>
<li>Misleading feature instances: {summary['misleading_feature_instances']}</li>
<li>Coarse preferred by AP: {summary['coarse_preferred_by_ap_tasks']}</li>
</ul>
<h2>Critical And Misleading Features</h2>
<table><thead><tr><th>Task</th><th>Stack</th><th>Feature</th><th>Class</th><th>Drop AP Delta</th><th>Drop WTFP Delta</th></tr></thead><tbody>{feature_html}</tbody></table>
<h2>Stack Depth</h2>
<table><thead><tr><th>Task</th><th>Preferred</th><th>Semantic AP</th><th>Coarse AP</th><th>Group Reduction</th></tr></thead><tbody>{stack_html}</tbody></table>
</body>
</html>
"""
    (out_dir / "index.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    start = time.perf_counter()
    out_dir = DEFAULT_OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    source_paths = sorted(
        {r322.SOURCE_OPERATIONS, R324_VISIBLE_OPERATIONS, *(task["operation_file"] for task in r300.TASKS)}
    )
    r322.ensure_sources_tracked_clean(source_paths)
    leakage_check = r324.validate_op_rank_rules()
    profiler_input_check = r324.validate_visible_operation_file(R324_VISIBLE_OPERATIONS)
    rows = []
    for task in r300.TASKS:
        for stack_kind, stack in (
            ("semantic", list(task["semantic_stack"])),
            ("coarse", r324.coarse_stack(task)),
        ):
            groups, summary = r324.group_task_for_stack(task, stack)
            for policy in policy_specs(r324.OP_RANK_RULES[task["id"]]):
                rows.append(
                    evaluate_policy(
                        out_dir,
                        task,
                        stack_kind,
                        stack,
                        policy,
                        groups,
                        summary,
                        R324_VISIBLE_OPERATIONS,
                    )
                )
    write_reports(out_dir, rows, leakage_check, profiler_input_check, time.perf_counter() - start)


if __name__ == "__main__":
    main()
