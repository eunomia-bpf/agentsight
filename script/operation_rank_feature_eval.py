#!/usr/bin/env python3
"""R324: evaluate Rust operation-level rank features on existing labeled traces.

R322/R323 rank folded stack text.  R324 adds a mechanism probe for Rust
`rank_op_rules`: visible regex rules run on mapped operation fields before
folding, then the profiler aggregates matched operation weight inside each
operation-stack group.  Hidden labels are used only after Rust emits the ranked
JSON profile.
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
DEFAULT_OUT_DIR = OUT_ROOT / "operation-rank-feature-r324"
TOP_LIMIT = 20
TOP_K_VALUES = [5, 10]

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_query_utility_eval as r300  # noqa: E402
import operation_rust_rank_rule_eval as r322  # noqa: E402


OP_RANK_RULES = {
    "agentreward_looping": [
        "loop-like:5=repeat_signal=loop-like",
        "failure:1.5=status=(failure|error)",
        "navigation:0.5=action=(click|left_click|goto|go_back|scroll|hover|move_to|drag)",
    ],
    "agentreward_side_effect": [
        "write-action:3=action=(fill|type|key|hotkey|press|select_option|send_msg_to_user|clear)",
        "input-phase:2=phase=(input|modify)",
        "failure:1=status=(failure|error)",
        "navigation:0.5=action=(click|left_click|goto|go_back|scroll|hover|move_to|drag)",
        "finish-phase:-0.5=phase=finish",
    ],
    "satraj_unsafe": [
        "risky-env:2=environment=(os|unknown_file|popup|induced_text|account|error_correction|infeasible)",
        "write-action:2=action=(fill|type|key|hotkey|press|select_option|send_msg_to_user|left_click_drag|system_command)",
        "input-phase:1.5=phase=(input|modify)",
        "success:0.5=status=success",
        "loop-like:0.5=repeat_signal=.*(loop|repeat)",
    ],
    "agentnet_incorrect_step": [
        "failure:2=status=.*(fail|error)",
        "loop-like:1.5=repeat_signal=.*(loop|repeat)",
        "risky-env:1=environment=(error_correction|infeasible|unknown_file|popup|induced_text|account)",
        "input-phase:0.5=phase=(input|modify)",
    ],
    "agentnet_redundant_step": [
        "loop-like:4=repeat_signal=.*(loop|repeat)",
        "failure:1=status=.*(fail|error)",
        "navigation:0.5=action=(click|left_click|double_click|tripleclick|move_to|drag|scroll|hover|goto|go_back)",
    ],
    "osworld_group_start": [
        "input-phase:1.5=phase=(input|modify)",
        "navigate-phase:1=phase=navigate",
        "write-action:1=action=(fill|type|key|hotkey|press|select_option|send_msg_to_user|drag)",
        "navigation:0.5=action=(click|left_click|double_click|tripleclick|move_to|drag|scroll|hover|goto|go_back)",
        "finish-phase:0.5=phase=finish",
    ],
}


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_visible_operation_file(out_dir: Path) -> Path:
    """Write the profiler input with oracle/scoring fields removed.

    The R300 operation JSONL intentionally carries hidden labels so Python can
    score policies after ranking.  Rust should not see those labels for R324,
    because rank-op regexes are intentionally flexible.
    """
    hidden = set(r322.r320.HIDDEN_FIELDS)
    output = out_dir / "visible-query-utility-operations.jsonl"
    rows = 0
    with r322.SOURCE_OPERATIONS.open(encoding="utf-8") as source, output.open(
        "w", encoding="utf-8"
    ) as sink:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            fields = {
                key: value
                for key, value in (row.get("fields") or {}).items()
                if key not in hidden
            }
            sink.write(
                json.dumps(
                    {"value": int(row.get("value") or 1), "fields": fields},
                    sort_keys=True,
                )
                + "\n"
            )
            rows += 1
    if rows == 0:
        raise SystemExit(f"visible profiler input is empty: {r322.rel(output)}")
    return output


def coarse_stack(task: dict[str, Any]) -> list[str]:
    dataset = task["dataset"]
    if dataset == "agent-reward-bench":
        return ["analysis_task", "dataset", "benchmark", "phase"]
    if dataset == "satraj-os-safety":
        return ["analysis_task", "dataset", "environment", "phase"]
    if dataset == "agentnet":
        return ["analysis_task", "dataset", "environment", "phase"]
    if dataset == "osworld-human":
        return ["analysis_task", "dataset", "app", "phase"]
    return ["analysis_task", "dataset", "phase"]


def group_task_for_stack(
    task: dict[str, Any], stack: list[str]
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in r300.load_task_operations(task):
        grouped[r322.stack_label(operation["fields"], stack)].append(operation)

    groups = {}
    total_ops = 0
    total_positive = 0
    for stack_label, rows in grouped.items():
        operations = sum(int(operation["value"]) for operation in rows)
        positives = sum(
            int(operation["value"])
            for operation in rows
            if operation["fields"].get("target_positive") == "positive"
        )
        total_ops += operations
        total_positive += positives
        groups[stack_label] = {
            "stack": stack_label,
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


def write_profile_spec(
    out_dir: Path,
    task: dict[str, Any],
    stack_kind: str,
    stack: list[str],
    operation_file: Path,
) -> Path:
    spec_path = out_dir / f"{task['id']}-{stack_kind}-op-features-profile-spec.json"
    spec = {
        "output": f"{task['id']}-{stack_kind}-op-features.json",
        "format": "json",
        "view": "operations",
        "operation_files": [str(operation_file.resolve())],
        "stack": ",".join(stack),
        "where_rules": [f"analysis_task={task['id']}"],
        "rank_op_rules": OP_RANK_RULES[task["id"]],
        "rank_mode": "rule-score",
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


def evaluate_task_stack(
    out_dir: Path,
    task: dict[str, Any],
    stack_kind: str,
    stack: list[str],
    operation_file: Path,
) -> dict[str, Any]:
    groups, summary = group_task_for_stack(task, stack)
    spec_path = write_profile_spec(out_dir, task, stack_kind, stack, operation_file)
    agentpprof_result = run_agentpprof(spec_path)
    output = out_dir / f"{task['id']}-{stack_kind}-op-features.json"
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
            f"Rust stack output did not match expected task groups for {task['id']} "
            f"{stack_kind}: missing_or_extra={missing[:3]} mismatched={mismatched_weights[:3]}"
        )

    width_order = sorted(stacks, key=lambda stack_label: (-int(stacks[stack_label]), stack_label))
    op_feature_order = [row["stack"] for row in profile["ranking"]["top"]]
    scored = {
        "width": score_policy(width_order, groups, summary),
        "op_feature": score_policy(op_feature_order, groups, summary),
    }
    return {
        "task": task["id"],
        "dataset": task["dataset"],
        "problem": task["problem"],
        "stack_kind": stack_kind,
        "stack": stack,
        "summary": summary,
        "rank_op_rules": OP_RANK_RULES[task["id"]],
        "profile_spec": r322.rel(spec_path),
        "rust_json": r322.rel(output),
        "agentpprof_result": agentpprof_result,
        "policy": profile["ranking"]["policy"],
        "top_operation_features": [
            {
                "stack": row["stack"],
                "rank_score": row["rank_score"],
                "features": row.get("rank_operation_features", []),
            }
            for row in profile["ranking"]["top"][:3]
        ],
        "metrics": scored,
        "deltas": r322.rounded(
            {
                "op_feature_vs_width_ap": scored["op_feature"]["ap"] - scored["width"]["ap"],
                "op_feature_vs_width_ap_at_20": scored["op_feature"]["ap_at_20"]
                - scored["width"]["ap_at_20"],
                "op_feature_vs_width_top5_lift": scored["op_feature"]["top5_lift"]
                - scored["width"]["top5_lift"],
                "op_feature_vs_width_first_positive_work": (
                    None
                    if scored["op_feature"]["first_positive_work"] is None
                    or scored["width"]["first_positive_work"] is None
                    else scored["op_feature"]["first_positive_work"]
                    - scored["width"]["first_positive_work"]
                ),
            }
        ),
    }


def validate_op_rank_rules() -> dict[str, Any]:
    hidden = set(r322.r320.HIDDEN_FIELDS)
    violations = []
    visible_fields = set()
    for task_id, rules in OP_RANK_RULES.items():
        for rule in rules:
            _, pattern = rule.split("=", 1)
            for field in hidden:
                if f"{field}:" in pattern or f"{field}=" in pattern:
                    violations.append({"task": task_id, "rule": rule, "hidden_field": field})
            for chunk in pattern.replace("|", " ").replace("(", " ").replace(")", " ").split():
                if "=" in chunk:
                    visible_fields.add(chunk.split("=", 1)[0])
    if violations:
        raise SystemExit(f"operation rank rules reference hidden fields: {violations}")
    return {
        "status": "pass",
        "hidden_fields": sorted(hidden),
        "rank_operation_rule_fields": sorted(visible_fields),
        "violations": violations,
    }


def validate_visible_operation_file(path: Path) -> dict[str, Any]:
    hidden = set(r322.r320.HIDDEN_FIELDS)
    violations = []
    rows = 0
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                continue
            rows += 1
            fields = json.loads(line).get("fields") or {}
            overlap = sorted(hidden & set(fields))
            if overlap:
                violations.append({"line": line_number, "hidden_fields": overlap})
                if len(violations) >= 5:
                    break
    if violations:
        raise SystemExit(f"visible profiler input still has hidden fields: {violations}")
    return {
        "status": "pass",
        "profiler_operation_file": r322.rel(path),
        "rows": rows,
        "scrubbed_hidden_fields": sorted(hidden),
        "violations": violations,
    }


def write_reports(
    out_dir: Path,
    rows: list[dict[str, Any]],
    leakage_check: dict[str, Any],
    profiler_input_check: dict[str, Any],
    elapsed_s: float,
) -> None:
    semantic_rows = [row for row in rows if row["stack_kind"] == "semantic"]
    coarse_rows = [row for row in rows if row["stack_kind"] == "coarse"]

    def wins(items: list[dict[str, Any]], delta: str, positive: bool = True) -> str:
        count = sum(
            (row["deltas"][delta] > 0 if positive else row["deltas"][delta] < 0)
            for row in items
            if row["deltas"][delta] is not None
        )
        return f"{count}/{len(items)}"

    report = {
        "run_id": "R324",
        "status": "pass",
        "source_operations": r322.rel(r322.SOURCE_OPERATIONS),
        "profiler_operation_file": profiler_input_check["profiler_operation_file"],
        "commit": r322.git_output(["rev-parse", "HEAD"]),
        "elapsed_s": round(elapsed_s, 3),
        "tasks": len(r300.TASKS),
        "stack_variants": ["semantic", "coarse"],
        "summary": {
            "semantic_op_feature_ap_improves_vs_width_tasks": wins(
                semantic_rows, "op_feature_vs_width_ap"
            ),
            "semantic_op_feature_top5_lift_improves_vs_width_tasks": wins(
                semantic_rows, "op_feature_vs_width_top5_lift"
            ),
            "semantic_op_feature_first_positive_work_improves_vs_width_tasks": wins(
                semantic_rows, "op_feature_vs_width_first_positive_work", positive=False
            ),
            "coarse_op_feature_ap_improves_vs_width_tasks": wins(
                coarse_rows, "op_feature_vs_width_ap"
            ),
            "coarse_op_feature_top5_lift_improves_vs_width_tasks": wins(
                coarse_rows, "op_feature_vs_width_top5_lift"
            ),
            "coarse_op_feature_first_positive_work_improves_vs_width_tasks": wins(
                coarse_rows, "op_feature_vs_width_first_positive_work", positive=False
            ),
        },
        "leakage_check": leakage_check,
        "profiler_input_check": profiler_input_check,
        "tasks_detail": rows,
        "claim": (
            "Rust agentpprof can aggregate visible per-operation rank features inside "
            "operation-stack groups, making query-aware group-feature ranking a "
            "reproducible profile-spec policy rather than a Python-only analysis."
        ),
        "non_claims": [
            "This does not create a learned detector or human-utility result.",
            "This does not add a profiler abstraction beyond operation and operation stack.",
            "This does not download, sync, or create a new dataset.",
            "Rust profiles a scrubbed visible-operation JSONL; hidden labels score the emitted ranking only after profiling.",
        ],
    }
    write_json(out_dir / "rank-feature-report.json", r322.rounded(report))
    write_json(
        out_dir / "run-result.json",
        {"status": "pass", "report": r322.rel(out_dir / "rank-feature-report.json")},
    )

    fieldnames = [
        "task",
        "dataset",
        "stack_kind",
        "groups",
        "positives",
        "width_ap",
        "op_feature_ap",
        "delta_ap",
        "width_top5_lift",
        "op_feature_top5_lift",
        "delta_top5_lift",
        "width_first_positive_work",
        "op_feature_first_positive_work",
        "delta_first_positive_work",
    ]
    with (out_dir / "rank-feature-summary.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "task": row["task"],
                    "dataset": row["dataset"],
                    "stack_kind": row["stack_kind"],
                    "groups": row["summary"]["groups"],
                    "positives": row["summary"]["positives"],
                    "width_ap": row["metrics"]["width"]["ap"],
                    "op_feature_ap": row["metrics"]["op_feature"]["ap"],
                    "delta_ap": row["deltas"]["op_feature_vs_width_ap"],
                    "width_top5_lift": row["metrics"]["width"]["top5_lift"],
                    "op_feature_top5_lift": row["metrics"]["op_feature"]["top5_lift"],
                    "delta_top5_lift": row["deltas"]["op_feature_vs_width_top5_lift"],
                    "width_first_positive_work": row["metrics"]["width"][
                        "first_positive_work"
                    ],
                    "op_feature_first_positive_work": row["metrics"]["op_feature"][
                        "first_positive_work"
                    ],
                    "delta_first_positive_work": row["deltas"][
                        "op_feature_vs_width_first_positive_work"
                    ],
                }
            )

    lines = [
        "# R324 Rust Operation Rank-Feature Probe",
        "",
        f"- Source operations for scoring: `{r322.rel(r322.SOURCE_OPERATIONS)}`",
        f"- Profiler input: `{profiler_input_check['profiler_operation_file']}`",
        f"- Semantic AP wins vs width: {report['summary']['semantic_op_feature_ap_improves_vs_width_tasks']}",
        f"- Coarse AP wins vs width: {report['summary']['coarse_op_feature_ap_improves_vs_width_tasks']}",
        "",
        "| Task | Stack | Groups | Width AP | Op-feature AP | Delta AP | Delta top-5 lift |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {task} | {stack_kind} | {groups} | {width:.4f} | {rank:.4f} | {delta:.4f} | {lift:.4f} |".format(
                task=row["task"],
                stack_kind=row["stack_kind"],
                groups=row["summary"]["groups"],
                width=row["metrics"]["width"]["ap"],
                rank=row["metrics"]["op_feature"]["ap"],
                delta=row["deltas"]["op_feature_vs_width_ap"],
                lift=row["deltas"]["op_feature_vs_width_top5_lift"],
            )
        )
    lines.extend(
        [
            "",
            "Rust emits the ranked JSON from the scrubbed visible-operation input first. Hidden labels are used only for this offline scoring.",
            "",
        ]
    )
    (out_dir / "rank-feature-report.md").write_text("\n".join(lines), encoding="utf-8")

    table_rows = "\n".join(
        f"<tr><td>{html.escape(row['task'])}</td><td>{html.escape(row['stack_kind'])}</td>"
        f"<td>{row['summary']['groups']}</td>"
        f"<td>{row['metrics']['width']['ap']:.4f}</td>"
        f"<td>{row['metrics']['op_feature']['ap']:.4f}</td>"
        f"<td>{row['deltas']['op_feature_vs_width_ap']:.4f}</td>"
        f"<td>{row['deltas']['op_feature_vs_width_top5_lift']:.4f}</td></tr>"
        for row in rows
    )
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>R324 Rust Operation Rank-Feature Probe</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #1f2937; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border-bottom: 1px solid #d1d5db; padding: 8px; text-align: right; }}
th:first-child, td:first-child {{ text-align: left; }}
code {{ background: #f3f4f6; padding: 1px 4px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>R324 Rust Operation Rank-Feature Probe</h1>
<p>Scoring source: <code>{html.escape(r322.rel(r322.SOURCE_OPERATIONS))}</code>. Profiler input: <code>{html.escape(profiler_input_check['profiler_operation_file'])}</code>. Hidden labels are used only after ranking.</p>
<table>
<thead><tr><th>Task</th><th>Stack</th><th>Groups</th><th>Width AP</th><th>Op-feature AP</th><th>Delta AP</th><th>Delta top-5 lift</th></tr></thead>
<tbody>{table_rows}</tbody>
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
    leakage_check = validate_op_rank_rules()
    visible_operation_file = write_visible_operation_file(out_dir)
    profiler_input_check = validate_visible_operation_file(visible_operation_file)
    rows = []
    for task in r300.TASKS:
        rows.append(
            evaluate_task_stack(
                out_dir,
                task,
                "semantic",
                list(task["semantic_stack"]),
                visible_operation_file,
            )
        )
        rows.append(
            evaluate_task_stack(
                out_dir,
                task,
                "coarse",
                coarse_stack(task),
                visible_operation_file,
            )
        )
    write_reports(out_dir, rows, leakage_check, profiler_input_check, time.perf_counter() - start)


if __name__ == "__main__":
    main()
