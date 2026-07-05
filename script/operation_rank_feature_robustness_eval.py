#!/usr/bin/env python3
"""R326: robustness probe for visible Rust operation rank features.

R324 shows task-specific visible operation features can improve ranking.
R325 shows which individual features are critical or misleading.  R326 asks
whether those gains are brittle: it compares weighted task-specific rules,
equal-weight task-specific rules, a global visible feature bank, and a
profile-guided repaired policy that drops R325 misleading features.  Rust sees
only the scrubbed visible-operation JSONL; hidden labels are not passed to Rust
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
DEFAULT_OUT_DIR = OUT_ROOT / "operation-rank-feature-robustness-r326"
R324_VISIBLE_OPERATIONS = (
    OUT_ROOT / "operation-rank-feature-r324" / "visible-query-utility-operations.jsonl"
)
R325_REPORT = (
    OUT_ROOT / "operation-rank-feature-ablation-r325" / "rank-feature-ablation-report.json"
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_query_utility_eval as r300  # noqa: E402
import operation_rank_feature_eval as r324  # noqa: E402
import operation_rust_rank_rule_eval as r322  # noqa: E402


GLOBAL_EQUAL_RULES = [
    "loop-like:1=repeat_signal=.*(loop|repeat|loop-like)",
    "failure:1=status=.*(fail|failure|error|unknown)",
    "navigation:1=action=(click|left_click|double_click|tripleclick|goto|go_back|scroll|hover|move_to|drag)",
    "write-action:1=action=(fill|type|key|hotkey|press|select_option|send_msg_to_user|clear|left_click_drag|system_command|drag)",
    "input-phase:1=phase=(input|modify)",
    "navigate-phase:1=phase=navigate",
    "risky-env:1=environment=(os|unknown_file|popup|induced_text|account|error_correction|infeasible)",
    "success:1=status=success",
    "finish-phase:-1=phase=finish",
]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value)
    return value.strip("-").lower() or "policy"


def fmt_optional(value: float | None) -> str:
    return "" if value is None else f"{value:.4f}"


def parse_rule(rule: str) -> tuple[str, float, str]:
    head, pattern = rule.split("=", 1)
    label, weight = head.split(":", 1)
    return label, float(weight), pattern


def rewrite_rule_weight(rule: str, weight: float) -> str:
    label, _, pattern = parse_rule(rule)
    if weight == int(weight):
        weight_text = str(int(weight))
    else:
        weight_text = f"{weight:.3f}".rstrip("0").rstrip(".")
    return f"{label}:{weight_text}={pattern}"


def equalize_rules(rules: list[str]) -> list[str]:
    out = []
    for rule in rules:
        _, weight, _ = parse_rule(rule)
        out.append(rewrite_rule_weight(rule, -1.0 if weight < 0 else 1.0))
    return out


def validate_rules_visible(rule_sets: dict[str, list[str]]) -> dict[str, Any]:
    hidden = set(r322.r320.HIDDEN_FIELDS)
    violations = []
    visible_fields = set()
    for policy, rules in rule_sets.items():
        for rule in rules:
            _, _, pattern = parse_rule(rule)
            for field in hidden:
                if f"{field}:" in pattern or f"{field}=" in pattern:
                    violations.append({"policy": policy, "rule": rule, "hidden_field": field})
            for chunk in (
                pattern.replace("|", " ")
                .replace("(", " ")
                .replace(")", " ")
                .replace(",", " ")
                .split()
            ):
                if "=" in chunk:
                    visible_fields.add(chunk.split("=", 1)[0])
    if violations:
        raise SystemExit(f"rank rules reference hidden fields: {violations}")
    return {
        "status": "pass",
        "hidden_fields": sorted(hidden),
        "rank_operation_rule_fields": sorted(visible_fields),
        "violations": violations,
    }


def load_r325_misleading_features() -> dict[tuple[str, str], set[str]]:
    report = json.loads(R325_REPORT.read_text(encoding="utf-8"))
    if report.get("status") != "pass":
        raise SystemExit(f"R325 report is not pass: {r322.rel(R325_REPORT)}")
    mapping: dict[tuple[str, str], set[str]] = {}
    for row in report["feature_findings"]:
        if row["classification"] != "misleading":
            continue
        mapping.setdefault((row["task"], row["stack_kind"]), set()).add(row["feature"])
    return mapping


def repair_rules(rules: list[str], drop_features: set[str]) -> list[str]:
    return [rule for rule in rules if parse_rule(rule)[0] not in drop_features]


def policy_specs(
    task: dict[str, Any],
    stack_kind: str,
    misleading: dict[tuple[str, str], set[str]],
) -> list[dict[str, Any]]:
    task_rules = r324.OP_RANK_RULES[task["id"]]
    drop_features = misleading.get((task["id"], stack_kind), set())
    return [
        {
            "policy": "width",
            "policy_kind": "baseline",
            "rank_op_rules": [],
            "drop_features": [],
            "uses_r325_feedback": False,
        },
        {
            "policy": "task_weighted",
            "policy_kind": "task_specific",
            "rank_op_rules": task_rules,
            "drop_features": [],
            "uses_r325_feedback": False,
        },
        {
            "policy": "task_equal",
            "policy_kind": "task_specific_equal_weight",
            "rank_op_rules": equalize_rules(task_rules),
            "drop_features": [],
            "uses_r325_feedback": False,
        },
        {
            "policy": "global_equal",
            "policy_kind": "global_equal_weight",
            "rank_op_rules": GLOBAL_EQUAL_RULES,
            "drop_features": [],
            "uses_r325_feedback": False,
        },
        {
            "policy": "r325_repaired",
            "policy_kind": "profile_guided_repair",
            "rank_op_rules": repair_rules(task_rules, drop_features),
            "drop_features": sorted(drop_features),
            "uses_r325_feedback": True,
        },
    ]


def write_profile_spec(
    out_dir: Path,
    task: dict[str, Any],
    stack_kind: str,
    stack: list[str],
    policy: dict[str, Any],
) -> Path:
    stem = f"{task['id']}-{stack_kind}-{slug(policy['policy'])}"
    spec_path = out_dir / f"{stem}-profile-spec.json"
    spec: dict[str, Any] = {
        "output": f"{stem}.json",
        "format": "json",
        "view": "operations",
        "operation_files": [str(R324_VISIBLE_OPERATIONS.resolve())],
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
) -> dict[str, Any]:
    spec_path = write_profile_spec(out_dir, task, stack_kind, stack, policy)
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
        "policy_kind": policy["policy_kind"],
        "uses_r325_feedback": policy["uses_r325_feedback"],
        "drop_features": policy["drop_features"],
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
        weighted = by_key[(row["task"], row["stack_kind"], "task_weighted")]
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
        row["delta_vs_task_weighted"] = r322.rounded(
            {
                "ap": metric_delta(row["metrics"], weighted["metrics"], "ap"),
                "ap_at_20": metric_delta(
                    row["metrics"], weighted["metrics"], "ap_at_20"
                ),
                "top5_lift": metric_delta(
                    row["metrics"], weighted["metrics"], "top5_lift"
                ),
                "first_positive_work": metric_delta(
                    row["metrics"], weighted["metrics"], "first_positive_work"
                ),
            }
        )


def selected(rows: list[dict[str, Any]], policy: str, stack_kind: str | None = None) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row["policy"] == policy and (stack_kind is None or row["stack_kind"] == stack_kind)
    ]


def wins_vs_width(
    rows: list[dict[str, Any]],
    policy: str,
    stack_kind: str,
    metric: str,
    positive: bool = True,
) -> str:
    items = selected(rows, policy, stack_kind)
    count = sum(
        (row["delta_vs_width"][metric] > 0 if positive else row["delta_vs_width"][metric] < 0)
        for row in items
        if row["delta_vs_width"][metric] is not None
    )
    return f"{count}/{len(items)}"


def within_weighted(rows: list[dict[str, Any]], policy: str, tolerance: float = 0.02) -> str:
    items = selected(rows, policy)
    count = sum(
        abs(row["delta_vs_task_weighted"]["ap"] or 0.0) <= tolerance for row in items
    )
    return f"{count}/{len(items)}"


def repair_findings(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings = []
    for row in selected(rows, "r325_repaired"):
        if not row["drop_features"]:
            continue
        delta = row["delta_vs_task_weighted"]
        findings.append(
            r322.rounded(
                {
                    "task": row["task"],
                    "dataset": row["dataset"],
                    "stack_kind": row["stack_kind"],
                    "drop_features": ",".join(row["drop_features"]),
                    "delta_ap_vs_task_weighted": delta["ap"],
                    "delta_top5_lift_vs_task_weighted": delta["top5_lift"],
                    "delta_first_positive_work_vs_task_weighted": delta[
                        "first_positive_work"
                    ],
                    "repaired_ap": row["metrics"]["ap"],
                    "task_weighted_ap": row["metrics"]["ap"] - (delta["ap"] or 0.0),
                }
            )
        )
    return findings


def write_csv(
    out_dir: Path,
    rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
) -> None:
    with (out_dir / "rank-feature-robustness-summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as file:
        fieldnames = [
            "task",
            "dataset",
            "stack_kind",
            "policy",
            "policy_kind",
            "uses_r325_feedback",
            "drop_features",
            "groups",
            "ap",
            "delta_ap_vs_width",
            "delta_ap_vs_task_weighted",
            "top5_lift",
            "delta_top5_lift_vs_width",
            "first_positive_work",
            "delta_first_positive_work_vs_width",
            "delta_first_positive_work_vs_task_weighted",
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
                    "uses_r325_feedback": row["uses_r325_feedback"],
                    "drop_features": ",".join(row["drop_features"]),
                    "groups": row["groups"],
                    "ap": row["metrics"]["ap"],
                    "delta_ap_vs_width": row["delta_vs_width"]["ap"],
                    "delta_ap_vs_task_weighted": row["delta_vs_task_weighted"]["ap"],
                    "top5_lift": row["metrics"]["top5_lift"],
                    "delta_top5_lift_vs_width": row["delta_vs_width"]["top5_lift"],
                    "first_positive_work": row["metrics"]["first_positive_work"],
                    "delta_first_positive_work_vs_width": row["delta_vs_width"][
                        "first_positive_work"
                    ],
                    "delta_first_positive_work_vs_task_weighted": row[
                        "delta_vs_task_weighted"
                    ]["first_positive_work"],
                }
            )
    with (out_dir / "rank-feature-repair-findings.csv").open(
        "w", encoding="utf-8", newline=""
    ) as file:
        fieldnames = [
            "task",
            "dataset",
            "stack_kind",
            "drop_features",
            "delta_ap_vs_task_weighted",
            "delta_top5_lift_vs_task_weighted",
            "delta_first_positive_work_vs_task_weighted",
            "repaired_ap",
            "task_weighted_ap",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in repair_rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_markdown(
    out_dir: Path,
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
    repair_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# R326 Operation Rank-Feature Robustness",
        "",
        f"- Profiler input: `{r322.rel(R324_VISIBLE_OPERATIONS)}`",
        f"- Global equal semantic AP wins vs width: {summary['global_equal_semantic_ap_wins_vs_width']}",
        f"- Global equal coarse AP wins vs width: {summary['global_equal_coarse_ap_wins_vs_width']}",
        f"- Task equal AP within 0.02 of weighted task policy: {summary['task_equal_ap_within_0_02_of_weighted']}",
        f"- Repaired policy AP improves over task weighted on R325-misleading cases: {summary['repaired_ap_improves_on_misleading_cases']}",
        f"- Repaired policy WTFP improves over task weighted on R325-misleading cases: {summary['repaired_first_positive_work_improves_on_misleading_cases']}",
        f"- Repaired policy improves both AP and WTFP on R325-misleading cases: {summary['repaired_both_ap_and_first_positive_work_improve_on_misleading_cases']}",
        "",
        "## Policy Summary",
        "",
        "| Task | Stack | Policy | AP | Delta AP vs width | WTFP |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in rows:
        if row["policy"] not in {"task_weighted", "task_equal", "global_equal", "r325_repaired"}:
            continue
        lines.append(
            f"| {row['task']} | {row['stack_kind']} | {row['policy']} | "
            f"{row['metrics']['ap']:.4f} | {row['delta_vs_width']['ap']:.4f} | "
            f"{fmt_optional(row['metrics']['first_positive_work'])} |"
        )
    lines.extend(
        [
            "",
            "## R325-Guided Repairs",
            "",
            "| Task | Stack | Dropped features | Delta AP | Delta WTFP |",
            "|---|---|---|---:|---:|",
        ]
    )
    for row in repair_rows:
        lines.append(
            f"| {row['task']} | {row['stack_kind']} | {row['drop_features']} | "
            f"{row['delta_ap_vs_task_weighted']:.4f} | "
            f"{fmt_optional(row['delta_first_positive_work_vs_task_weighted'])} |"
        )
    lines.append(
        "\nRust receives only scrubbed visible operations. Global/task-equal policies "
        "are label-free ranking policies; the repaired policy is a post-hoc "
        "actionability check driven by R325's offline scoring findings."
    )
    (out_dir / "rank-feature-robustness-report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def write_html(
    out_dir: Path,
    summary: dict[str, Any],
    repair_rows: list[dict[str, Any]],
) -> None:
    repair_html = "\n".join(
        f"<tr><td>{html.escape(row['task'])}</td><td>{html.escape(row['stack_kind'])}</td>"
        f"<td>{html.escape(row['drop_features'])}</td>"
        f"<td>{row['delta_ap_vs_task_weighted']:.4f}</td>"
        f"<td>{fmt_optional(row['delta_first_positive_work_vs_task_weighted'])}</td></tr>"
        for row in repair_rows
    )
    items = "\n".join(
        f"<li>{html.escape(key)}: {html.escape(str(value))}</li>"
        for key, value in summary.items()
    )
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>R326 Operation Rank-Feature Robustness</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #1f2937; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; }}
th, td {{ border-bottom: 1px solid #d1d5db; padding: 8px; text-align: right; }}
th:first-child, td:first-child, th:nth-child(2), td:nth-child(2), th:nth-child(3), td:nth-child(3) {{ text-align: left; }}
code {{ background: #f3f4f6; padding: 1px 4px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>R326 Operation Rank-Feature Robustness</h1>
<p>Profiler input: <code>{html.escape(r322.rel(R324_VISIBLE_OPERATIONS))}</code>. Hidden labels are not passed to Rust and are used only for offline scoring.</p>
<ul>{items}</ul>
<h2>R325-Guided Repairs</h2>
<table><thead><tr><th>Task</th><th>Stack</th><th>Dropped features</th><th>Delta AP</th><th>Delta WTFP</th></tr></thead><tbody>{repair_html}</tbody></table>
</body>
</html>
"""
    (out_dir / "index.html").write_text(html_doc, encoding="utf-8")


def write_reports(
    out_dir: Path,
    rows: list[dict[str, Any]],
    leakage_check: dict[str, Any],
    profiler_input_check: dict[str, Any],
    elapsed_s: float,
) -> None:
    annotate_deltas(rows)
    repair_rows = repair_findings(rows)
    repaired_ap_wins = sum(
        (row["delta_ap_vs_task_weighted"] or 0.0) > 0 for row in repair_rows
    )
    repaired_wtfp_wins = sum(
        row["delta_first_positive_work_vs_task_weighted"] is not None
        and row["delta_first_positive_work_vs_task_weighted"] < 0
        for row in repair_rows
    )
    repaired_both_wins = sum(
        (row["delta_ap_vs_task_weighted"] or 0.0) > 0
        and row["delta_first_positive_work_vs_task_weighted"] is not None
        and row["delta_first_positive_work_vs_task_weighted"] < 0
        for row in repair_rows
    )
    summary = {
        "global_equal_semantic_ap_wins_vs_width": wins_vs_width(
            rows, "global_equal", "semantic", "ap"
        ),
        "global_equal_coarse_ap_wins_vs_width": wins_vs_width(
            rows, "global_equal", "coarse", "ap"
        ),
        "global_equal_semantic_first_positive_work_wins_vs_width": wins_vs_width(
            rows, "global_equal", "semantic", "first_positive_work", positive=False
        ),
        "task_equal_ap_within_0_02_of_weighted": within_weighted(rows, "task_equal"),
        "task_equal_ap_improves_vs_width_semantic": wins_vs_width(
            rows, "task_equal", "semantic", "ap"
        ),
        "task_equal_ap_improves_vs_width_coarse": wins_vs_width(
            rows, "task_equal", "coarse", "ap"
        ),
        "repaired_ap_improves_on_misleading_cases": f"{repaired_ap_wins}/{len(repair_rows)}",
        "repaired_first_positive_work_improves_on_misleading_cases": f"{repaired_wtfp_wins}/{len(repair_rows)}",
        "repaired_both_ap_and_first_positive_work_improve_on_misleading_cases": f"{repaired_both_wins}/{len(repair_rows)}",
    }
    report = {
        "run_id": "R326",
        "status": "pass",
        "source_operations": r322.rel(r322.SOURCE_OPERATIONS),
        "profiler_operation_file": r322.rel(R324_VISIBLE_OPERATIONS),
        "r325_source_report": r322.rel(R325_REPORT),
        "commit": r322.git_output(["rev-parse", "HEAD"]),
        "elapsed_s": round(elapsed_s, 3),
        "tasks": len(r300.TASKS),
        "policies": sorted({row["policy"] for row in rows}),
        "summary": summary,
        "leakage_check": leakage_check,
        "profiler_input_check": profiler_input_check,
        "repair_findings": repair_rows,
        "policy_rows": rows,
        "claim": (
            "Visible operation rank policies are not only one hand-tuned setting: "
            "equalized and global visible-feature policies provide robustness checks, "
            "and R325-guided repairs demonstrate actionable policy edits."
        ),
        "non_claims": [
            "This is not a learned detector or a human/agent analyst study.",
            "This does not add abstractions beyond operation and operation stack.",
            "This does not download, sync, or create a new dataset.",
            "Global/task-equal policies do not use hidden labels for Rust ranking.",
            "The repaired policy is a post-hoc actionability check using R325 offline-scored findings, not a label-free deployment policy.",
        ],
    }
    write_json(out_dir / "rank-feature-robustness-report.json", r322.rounded(report))
    write_json(
        out_dir / "run-result.json",
        {
            "status": "pass",
            "report": r322.rel(out_dir / "rank-feature-robustness-report.json"),
        },
    )
    write_csv(out_dir, rows, repair_rows)
    write_markdown(out_dir, summary, rows, repair_rows)
    write_html(out_dir, summary, repair_rows)


def main() -> None:
    start = time.perf_counter()
    out_dir = DEFAULT_OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    source_paths = sorted(
        {
            r322.SOURCE_OPERATIONS,
            R324_VISIBLE_OPERATIONS,
            R325_REPORT,
            *(task["operation_file"] for task in r300.TASKS),
        }
    )
    r322.ensure_sources_tracked_clean(source_paths)
    misleading = load_r325_misleading_features()
    rule_sets = {"global_equal": GLOBAL_EQUAL_RULES}
    for task in r300.TASKS:
        task_rules = r324.OP_RANK_RULES[task["id"]]
        rule_sets[f"{task['id']}:task_weighted"] = task_rules
        rule_sets[f"{task['id']}:task_equal"] = equalize_rules(task_rules)
    leakage_check = validate_rules_visible(rule_sets)
    profiler_input_check = r324.validate_visible_operation_file(R324_VISIBLE_OPERATIONS)
    rows = []
    for task in r300.TASKS:
        for stack_kind, stack in (
            ("semantic", list(task["semantic_stack"])),
            ("coarse", r324.coarse_stack(task)),
        ):
            groups, summary = r324.group_task_for_stack(task, stack)
            for policy in policy_specs(task, stack_kind, misleading):
                rows.append(
                    evaluate_policy(
                        out_dir,
                        task,
                        stack_kind,
                        stack,
                        policy,
                        groups,
                        summary,
                    )
                )
    write_reports(out_dir, rows, leakage_check, profiler_input_check, time.perf_counter() - start)


if __name__ == "__main__":
    main()
