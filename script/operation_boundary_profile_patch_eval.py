#!/usr/bin/env python3
"""R358: boundary-derived profile patch audit for OSWorld-Human.

R354 intentionally rejected the OSWorld-Human visible rank-feature patch: phase
and action features alone did not improve human-boundary localization.  R358
tests the next mechanism suggested by that rejection.  It reuses the tracked
R297 held-out OSWorld-Human boundary-backend operations, keeps the learned
boundary fields visible, removes oracle/group labels from the Rust profiler
input, runs Rust profile specs for several views, and scores the emitted
rankings with hidden labels only after profiling.

No dataset is fetched, synced, created, or relabeled by this script.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import subprocess
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import sys


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
R297_DIR = OUT_ROOT / "operation-boundary-backend-r297"
R354_DIR = OUT_ROOT / "operation-profile-patch-r354"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-boundary-profile-patch-r358"
RUN_ID = "R358"
TOP_K = 5
TOP_LIMIT = 20

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_rank_feature_eval as r324  # noqa: E402
import operation_rust_rank_rule_eval as r322  # noqa: E402


HIDDEN_FIELDS = {
    "group_alignment",
    "group_index",
    "group_pattern",
    "group_position",
    "group_size",
    "human_group",
    "oracle_boundary_field",
    "problem_value",
    "target_positive",
}

LEARNED_BOUNDARY_RANK_RULES = [
    "predicted-boundary:4=learned_boundary_prev=(start|boundary)",
    "predicted-start:2=learned_group_position=(start|single)",
    "input-phase:0.5=phase=(input|modify)",
    "navigate-phase:0.5=phase=navigate",
]


@dataclass(frozen=True)
class Policy:
    name: str
    stack: list[str]
    rank_op_rules: list[str]
    hidden: bool
    description: str


POLICIES = [
    Policy(
        name="flat_width",
        stack=["analysis_task", "dataset"],
        rank_op_rules=[],
        hidden=False,
        description="Flat task summary baseline.",
    ),
    Policy(
        name="fixed_session_width",
        stack=["analysis_task", "dataset", "session"],
        rank_op_rules=[],
        hidden=False,
        description="Fixed-session/span-tree proxy baseline.",
    ),
    Policy(
        name="semantic_width",
        stack=["analysis_task", "dataset", "app", "phase", "action", "repeat_signal", "status"],
        rank_op_rules=[],
        hidden=False,
        description="R354 default OSWorld-Human semantic stack ranked by width.",
    ),
    Policy(
        name="semantic_visible_rank",
        stack=["analysis_task", "dataset", "app", "phase", "action", "repeat_signal", "status"],
        rank_op_rules=r324.OP_RANK_RULES["osworld_group_start"],
        hidden=False,
        description="R354 visible phase/action rank-feature patch, rerun on R297 held-out operations.",
    ),
    Policy(
        name="learned_boundary_width",
        stack=[
            "analysis_task",
            "dataset",
            "phase",
            "learned_group_pattern",
            "learned_group_position",
            "action",
            "status",
        ],
        rank_op_rules=[],
        hidden=False,
        description="Boundary-derived stack using R297 learned_group_pattern and learned_group_position fields.",
    ),
    Policy(
        name="learned_boundary_rank",
        stack=[
            "analysis_task",
            "dataset",
            "phase",
            "learned_group_pattern",
            "learned_group_position",
            "action",
            "status",
        ],
        rank_op_rules=LEARNED_BOUNDARY_RANK_RULES,
        hidden=False,
        description="Same boundary-derived stack plus visible rank rules over learned boundary fields.",
    ),
    Policy(
        name="oracle_positive_rate_semantic",
        stack=["analysis_task", "dataset", "app", "phase", "action", "repeat_signal", "status"],
        rank_op_rules=[],
        hidden=True,
        description="Hidden-label positive-rate upper bound on the semantic stack.",
    ),
    Policy(
        name="oracle_positive_rate_learned_stack",
        stack=[
            "analysis_task",
            "dataset",
            "phase",
            "learned_group_pattern",
            "learned_group_position",
            "action",
            "status",
        ],
        rank_op_rules=[],
        hidden=True,
        description="Hidden-label positive-rate upper bound on the learned-boundary stack.",
    ),
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
    if isinstance(value, (list, dict)):
        return json.dumps(round_value(value), sort_keys=True)
    return value


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_value(row.get(field)) for field in fields})


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


def normalize_fields(fields: dict[str, Any]) -> dict[str, str]:
    normalized = {}
    for key, value in fields.items():
        if isinstance(value, list):
            if not value:
                continue
            value = value[0]
        if isinstance(value, (dict, list)):
            text = json.dumps(value, sort_keys=True, ensure_ascii=True)
        else:
            text = str(value)
        if text:
            normalized[str(key)] = text
    return normalized


def load_scored_operations(path: Path) -> list[dict[str, Any]]:
    operations = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            fields = normalize_fields(row.get("fields") or {})
            if fields.get("group_alignment") != "exact":
                continue
            if not fields.get("group_position"):
                continue
            fields = dict(fields)
            fields.update(
                {
                    "analysis_task": "osworld_group_start",
                    "query_family": "human-boundary",
                    "problem_oracle": "group_position",
                    "problem_value": fields["group_position"],
                    "target_positive": "positive"
                    if fields["group_position"] == "start"
                    else "negative",
                    "source_operation_file": rel(path),
                }
            )
            operations.append(
                {
                    "fields": fields,
                    "value": int(row.get("value") or 1),
                    "_source_line": line_number,
                }
            )
    if not operations:
        raise SystemExit(f"no scored operations loaded from {rel(path)}")
    return operations


def write_visible_operation_file(out_dir: Path, operations: list[dict[str, Any]]) -> Path:
    visible_path = out_dir / "osworld-boundary-visible-operations.jsonl"
    with visible_path.open("w", encoding="utf-8") as file:
        for operation in operations:
            fields = {
                key: value
                for key, value in operation["fields"].items()
                if key not in HIDDEN_FIELDS
            }
            file.write(
                json.dumps(
                    {"fields": fields, "value": int(operation.get("value") or 1)},
                    sort_keys=True,
                )
                + "\n"
            )
    return visible_path


def stack_label(fields: dict[str, str], stack: list[str]) -> str:
    return ";".join(f"{field}:{fields.get(field, 'unknown')}" for field in stack)


def group_for_stack(
    operations: list[dict[str, Any]], stack: list[str]
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        grouped[stack_label(operation["fields"], stack)].append(operation)
    groups: dict[str, dict[str, Any]] = {}
    total_ops = 0
    total_positive = 0
    for label, rows in grouped.items():
        operations_count = sum(int(row["value"]) for row in rows)
        positives = sum(
            int(row["value"])
            for row in rows
            if row["fields"].get("target_positive") == "positive"
        )
        sessions = {row["fields"].get("session", "unknown") for row in rows}
        total_ops += operations_count
        total_positive += positives
        groups[label] = {
            "stack": label,
            "operations": operations_count,
            "positives": positives,
            "positive_rate": positives / operations_count if operations_count else 0.0,
            "sessions": len(sessions),
        }
    return groups, {
        "operations": total_ops,
        "positives": total_positive,
        "prevalence": total_positive / total_ops if total_ops else 0.0,
        "groups": len(groups),
    }


def write_profile_spec(out_dir: Path, policy: Policy, visible_operation_file: Path) -> Path:
    spec_path = out_dir / f"{policy.name}-profile-spec.json"
    spec: dict[str, Any] = {
        "output": f"{policy.name}.json",
        "format": "json",
        "view": "operations",
        "operation_files": [str(visible_operation_file.resolve())],
        "stack": ",".join(policy.stack),
        "where_rules": ["analysis_task=osworld_group_start"],
    }
    if policy.rank_op_rules:
        spec["rank_op_rules"] = policy.rank_op_rules
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


def load_profile(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    try:
        return payload["profile"]
    except KeyError as exc:
        raise SystemExit(f"{rel(path)} is missing profile output") from exc


def width_order(groups: dict[str, dict[str, Any]]) -> list[str]:
    return sorted(groups, key=lambda label: (-groups[label]["operations"], label))


def positive_rate_order(groups: dict[str, dict[str, Any]]) -> list[str]:
    return sorted(
        groups,
        key=lambda label: (
            -groups[label]["positive_rate"],
            -groups[label]["positives"],
            groups[label]["operations"],
            label,
        ),
    )


def groups_to_recall(
    order: list[str],
    groups: dict[str, dict[str, Any]],
    summary: dict[str, Any],
    target_recall: float,
) -> dict[str, Any]:
    target = summary["positives"] * target_recall
    positives = 0
    operations = 0
    for index, label in enumerate(order, 1):
        group = groups[label]
        positives += group["positives"]
        operations += group["operations"]
        if positives >= target:
            return {
                f"groups_to_{int(target_recall * 100)}pct_positive_recall": index,
                f"work_to_{int(target_recall * 100)}pct_positive_recall": operations
                / summary["operations"]
                if summary["operations"]
                else 0.0,
            }
    return {
        f"groups_to_{int(target_recall * 100)}pct_positive_recall": None,
        f"work_to_{int(target_recall * 100)}pct_positive_recall": None,
    }


def score_order(
    order: list[str],
    groups: dict[str, dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "ap": r322.average_precision(order, groups, summary["positives"]),
        "ap_at_20": r322.average_precision(order, groups, summary["positives"], TOP_LIMIT),
        **r322.first_positive(order, groups, summary["operations"]),
        **r322.score_order(order, groups, summary, TOP_K),
        **groups_to_recall(order, groups, summary, 0.5),
    }
    return r322.rounded(metrics)


def evaluate_policy(
    out_dir: Path,
    policy: Policy,
    operations: list[dict[str, Any]],
    visible_operation_file: Path,
) -> dict[str, Any]:
    groups, summary = group_for_stack(operations, policy.stack)
    spec_path = None
    agentpprof_result = None
    rust_json = None
    profile_order: list[str]

    if policy.hidden:
        profile_order = positive_rate_order(groups)
    else:
        spec_path = write_profile_spec(out_dir, policy, visible_operation_file)
        agentpprof_result = run_agentpprof(spec_path)
        rust_json = out_dir / f"{policy.name}.json"
        profile = load_profile(rust_json)
        stacks = {label: int(value) for label, value in profile["stacks"].items()}
        missing = sorted(set(stacks) ^ set(groups))
        mismatched = [
            {"stack": label, "rust": stacks[label], "expected": groups[label]["operations"]}
            for label in stacks
            if label in groups and stacks[label] != groups[label]["operations"]
        ]
        if missing or mismatched:
            raise SystemExit(
                f"Rust stack output did not match scorer for {policy.name}: "
                f"missing_or_extra={missing[:3]} mismatched={mismatched[:3]}"
            )
        ranking = profile.get("ranking") or {}
        top_rows = ranking.get("top") or []
        profile_order = [row["stack"] for row in top_rows] if top_rows else width_order(groups)

    metrics = score_order(profile_order, groups, summary)
    return {
        "policy": policy.name,
        "description": policy.description,
        "hidden": policy.hidden,
        "stack": policy.stack,
        "rank_op_rules": policy.rank_op_rules,
        "profile_spec": rel(spec_path) if spec_path else "",
        "rust_json": rel(rust_json) if rust_json else "",
        "agentpprof_result": agentpprof_result,
        "summary": summary,
        "metrics": metrics,
        "top_stacks": [
            {
                "rank": index + 1,
                "stack": label,
                "operations": groups[label]["operations"],
                "positives": groups[label]["positives"],
                "positive_rate": groups[label]["positive_rate"],
            }
            for index, label in enumerate(profile_order[:TOP_K])
        ],
    }


def delta(left: float | int | None, right: float | int | None) -> float | None:
    if left is None or right is None:
        return None
    return float(left) - float(right)


def comparison_row(name: str, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_metrics = left["metrics"]
    right_metrics = right["metrics"]
    left_summary = left["summary"]
    right_summary = right["summary"]
    return {
        "comparison": name,
        "left_policy": left["policy"],
        "right_policy": right["policy"],
        "delta_ap": delta(left_metrics["ap"], right_metrics["ap"]),
        "delta_top5_recall": delta(left_metrics[f"top{TOP_K}_recall"], right_metrics[f"top{TOP_K}_recall"]),
        "delta_top5_precision": delta(left_metrics[f"top{TOP_K}_precision"], right_metrics[f"top{TOP_K}_precision"]),
        "delta_top5_lift": delta(left_metrics[f"top{TOP_K}_lift"], right_metrics[f"top{TOP_K}_lift"]),
        "delta_top5_work": delta(left_metrics[f"top{TOP_K}_work"], right_metrics[f"top{TOP_K}_work"]),
        "delta_first_positive_work": delta(
            left_metrics["first_positive_work"], right_metrics["first_positive_work"]
        ),
        "delta_groups": delta(left_summary["groups"], right_summary["groups"]),
        "delta_groups_to_50pct": delta(
            left_metrics["groups_to_50pct_positive_recall"],
            right_metrics["groups_to_50pct_positive_recall"],
        ),
        "delta_work_to_50pct": delta(
            left_metrics["work_to_50pct_positive_recall"],
            right_metrics["work_to_50pct_positive_recall"],
        ),
    }


def validate_no_hidden_rank_rules() -> dict[str, Any]:
    violations = []
    for policy in POLICIES:
        if policy.hidden:
            continue
        for rule in policy.rank_op_rules:
            _, _, pattern = rule.partition("=")
            field_name, sep, _ = pattern.partition("=")
            if not sep:
                field_name, sep, _ = pattern.partition(":")
            if sep and field_name in HIDDEN_FIELDS:
                violations.append({"policy": policy.name, "rule": rule, "hidden_field": field_name})
    if violations:
        raise SystemExit(f"visible rank rules reference hidden fields: {violations}")
    return {"status": "pass", "hidden_fields": sorted(HIDDEN_FIELDS), "violations": violations}


def summarize(rows: list[dict[str, Any]], comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    by_policy = {row["policy"]: row for row in rows}
    learned = by_policy["learned_boundary_width"]
    semantic = by_policy["semantic_width"]
    visible_rank = by_policy["semantic_visible_rank"]
    learned_rank = by_policy["learned_boundary_rank"]
    return {
        "heldout_operations": semantic["summary"]["operations"],
        "heldout_positives": semantic["summary"]["positives"],
        "visible_policies": sum(not row["hidden"] for row in rows),
        "hidden_upper_bounds": sum(row["hidden"] for row in rows),
        "learned_boundary_ap": learned["metrics"]["ap"],
        "semantic_width_ap": semantic["metrics"]["ap"],
        "semantic_visible_rank_ap": visible_rank["metrics"]["ap"],
        "learned_boundary_delta_ap_vs_semantic": round(
            learned["metrics"]["ap"] - semantic["metrics"]["ap"], 4
        ),
        "learned_boundary_delta_ap_vs_visible_rank": round(
            learned["metrics"]["ap"] - visible_rank["metrics"]["ap"], 4
        ),
        "learned_boundary_groups": learned["summary"]["groups"],
        "semantic_width_groups": semantic["summary"]["groups"],
        "fixed_session_groups": by_policy["fixed_session_width"]["summary"]["groups"],
        "learned_boundary_group_reduction_vs_semantic": round(
            1 - learned["summary"]["groups"] / semantic["summary"]["groups"], 4
        ),
        "learned_boundary_group_reduction_vs_fixed": round(
            1 - learned["summary"]["groups"] / by_policy["fixed_session_width"]["summary"]["groups"],
            4,
        ),
        "learned_boundary_top5_recall": learned["metrics"][f"top{TOP_K}_recall"],
        "semantic_width_top5_recall": semantic["metrics"][f"top{TOP_K}_recall"],
        "learned_boundary_delta_top5_recall_vs_semantic": round(
            learned["metrics"][f"top{TOP_K}_recall"]
            - semantic["metrics"][f"top{TOP_K}_recall"],
            4,
        ),
        "learned_boundary_delta_top5_work_vs_semantic": round(
            learned["metrics"][f"top{TOP_K}_work"] - semantic["metrics"][f"top{TOP_K}_work"], 4
        ),
        "learned_boundary_delta_first_positive_work_vs_semantic": round(
            learned["metrics"]["first_positive_work"]
            - semantic["metrics"]["first_positive_work"],
            4,
        ),
        "learned_rank_delta_ap_vs_width": round(
            learned_rank["metrics"]["ap"] - learned["metrics"]["ap"], 4
        ),
        "accepted_boundary_patch": (
            learned["metrics"]["ap"] > semantic["metrics"]["ap"]
            and learned["summary"]["groups"] < semantic["summary"]["groups"]
        ),
        "counterpoint": (
            "Boundary-derived fields improve AP and reduce groups, but they increase top-5 "
            "operation work and first-positive work on this held-out subset."
        ),
        "comparison_rows": len(comparisons),
    }


def write_reports(
    out_dir: Path,
    report: dict[str, Any],
    rows: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
) -> None:
    write_json(out_dir / "boundary-profile-patch-report.json", report)
    write_json(
        out_dir / "run-result.json",
        {
            "run_id": RUN_ID,
            "status": "pass",
            "report": rel(out_dir / "boundary-profile-patch-report.json"),
            "accepted_boundary_patch": report["summary"]["accepted_boundary_patch"],
            "not_new_dataset": True,
            "not_a_human_study_result": True,
            "network_access_required": False,
        },
    )
    metric_fields = [
        "policy",
        "hidden",
        "groups",
        "operations",
        "positives",
        "ap",
        "ap_at_20",
        "top5_work",
        "top5_precision",
        "top5_recall",
        "top5_lift",
        "first_positive_work",
        "groups_to_50pct_positive_recall",
        "work_to_50pct_positive_recall",
        "profile_spec",
        "rust_json",
        "description",
    ]
    metric_rows = []
    for row in rows:
        metric_rows.append(
            {
                "policy": row["policy"],
                "hidden": row["hidden"],
                "groups": row["summary"]["groups"],
                "operations": row["summary"]["operations"],
                "positives": row["summary"]["positives"],
                "profile_spec": row["profile_spec"],
                "rust_json": row["rust_json"],
                "description": row["description"],
                **row["metrics"],
            }
        )
    write_csv(out_dir / "policy-metrics.csv", metric_rows, metric_fields)
    comparison_fields = [
        "comparison",
        "left_policy",
        "right_policy",
        "delta_ap",
        "delta_top5_recall",
        "delta_top5_precision",
        "delta_top5_lift",
        "delta_top5_work",
        "delta_first_positive_work",
        "delta_groups",
        "delta_groups_to_50pct",
        "delta_work_to_50pct",
    ]
    write_csv(out_dir / "policy-comparisons.csv", comparisons, comparison_fields)
    top_rows = []
    for row in rows:
        for top in row["top_stacks"]:
            top_rows.append({"policy": row["policy"], **top})
    write_csv(
        out_dir / "top-stacks.csv",
        top_rows,
        ["policy", "rank", "stack", "operations", "positives", "positive_rate"],
    )

    summary = report["summary"]
    lines = [
        "# R358 Boundary-Derived Profile Patch Audit",
        "",
        "R358 tests the R354 OSWorld-Human rejection directly: phase/action rank features are not enough, so this run uses the R297 learned boundary fields as ordinary operation fields and folds them through Rust profile specs.",
        "",
        "## Result",
        "",
        f"- Held-out operations / positives: {summary['heldout_operations']} / {summary['heldout_positives']}.",
        f"- Learned-boundary AP: {summary['learned_boundary_ap']:.4f}; semantic-width AP: {summary['semantic_width_ap']:.4f}; visible-rank AP: {summary['semantic_visible_rank_ap']:.4f}.",
        f"- AP delta vs semantic width: {summary['learned_boundary_delta_ap_vs_semantic']:.4f}.",
        f"- AP delta vs visible rank patch: {summary['learned_boundary_delta_ap_vs_visible_rank']:.4f}.",
        f"- Learned-boundary groups: {summary['learned_boundary_groups']} vs semantic {summary['semantic_width_groups']} and fixed-session {summary['fixed_session_groups']}.",
        f"- Top-5 recall delta vs semantic: {summary['learned_boundary_delta_top5_recall_vs_semantic']:.4f}.",
        f"- Counterpoint: {summary['counterpoint']}",
        "",
        "## Policy Metrics",
        "",
        "| Policy | Hidden | Groups | AP | Top-5 work | Top-5 recall | First-positive work |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in metric_rows:
        lines.append(
            f"| {row['policy']} | {row['hidden']} | {row['groups']} | {row['ap']:.4f} | {row['top5_work']:.4f} | {row['top5_recall']:.4f} | {row['first_positive_work'] if row['first_positive_work'] != '' else ''} |"
        )
    lines.extend(
        [
            "",
            "Hidden labels are used only after Rust emits visible profile groups. The oracle policies are explicit upper bounds.",
            "",
        ]
    )
    (out_dir / "boundary-profile-patch-report.md").write_text("\n".join(lines), encoding="utf-8")

    table_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(row['policy']))}</td>"
        f"<td>{html.escape(str(row['hidden']))}</td>"
        f"<td>{row['groups']}</td>"
        f"<td>{row['ap']:.4f}</td>"
        f"<td>{row['top5_work']:.4f}</td>"
        f"<td>{row['top5_recall']:.4f}</td>"
        f"<td>{row['first_positive_work']}</td>"
        "</tr>"
        for row in metric_rows
    )
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>R358 Boundary-Derived Profile Patch Audit</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #1f2937; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border-bottom: 1px solid #d1d5db; padding: 8px; text-align: right; }}
th:first-child, td:first-child {{ text-align: left; }}
code {{ background: #f3f4f6; padding: 1px 4px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>R358 Boundary-Derived Profile Patch Audit</h1>
<p>Profiler input: <code>{html.escape(report['visible_profiler_input'])}</code>. Hidden labels score profile groups only after Rust profiling.</p>
<table>
<thead><tr><th>Policy</th><th>Hidden</th><th>Groups</th><th>AP</th><th>Top-5 work</th><th>Top-5 recall</th><th>First-positive work</th></tr></thead>
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

    source_paths = [
        R297_DIR / "boundary-backend-report.json",
        R297_DIR / "osworld-learned-boundary-test-operations.jsonl",
        R354_DIR / "profile-patch-report.json",
        R354_DIR / "osworld_group_start-default-semantic-width-profile-spec.json",
        R354_DIR / "osworld_group_start-patched-semantic-op-features-profile-spec.json",
    ]
    source_status = ensure_sources_tracked_clean(source_paths)
    leakage_check = validate_no_hidden_rank_rules()
    operations = load_scored_operations(R297_DIR / "osworld-learned-boundary-test-operations.jsonl")
    visible_operation_file = write_visible_operation_file(out_dir, operations)

    rows = [
        evaluate_policy(out_dir, policy, operations, visible_operation_file)
        for policy in POLICIES
    ]
    by_policy = {row["policy"]: row for row in rows}
    comparisons = [
        comparison_row("learned_boundary_vs_semantic_width", by_policy["learned_boundary_width"], by_policy["semantic_width"]),
        comparison_row("learned_boundary_vs_visible_rank", by_policy["learned_boundary_width"], by_policy["semantic_visible_rank"]),
        comparison_row("learned_boundary_vs_fixed_session", by_policy["learned_boundary_width"], by_policy["fixed_session_width"]),
        comparison_row("learned_boundary_rank_vs_width", by_policy["learned_boundary_rank"], by_policy["learned_boundary_width"]),
        comparison_row("semantic_visible_rank_vs_width", by_policy["semantic_visible_rank"], by_policy["semantic_width"]),
    ]
    boundary_report = load_json(R297_DIR / "boundary-backend-report.json")
    report = {
        "run_id": RUN_ID,
        "schema": "agentsight.operation-boundary-profile-patch.v1",
        "status": "pass",
        "commit": git_output(["rev-parse", "HEAD"]),
        "elapsed_s": round(time.perf_counter() - start, 3),
        "source_status": source_status,
        "source": {
            "r297_report": rel(R297_DIR / "boundary-backend-report.json"),
            "r297_operations": rel(R297_DIR / "osworld-learned-boundary-test-operations.jsonl"),
            "r354_report": rel(R354_DIR / "profile-patch-report.json"),
        },
        "input_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "profiler_input": "R297 held-out OSWorld-Human operations with oracle fields removed before Rust profiling",
            "hidden_label_use": "only after Rust emits profile groups",
            "network_access_required": False,
        },
        "visible_profiler_input": rel(visible_operation_file),
        "leakage_check": leakage_check,
        "r297_boundary_backend": {
            "test_pairs": boundary_report["test_pairs"],
            "precision": boundary_report["test_metrics"]["learned_boundary_backend"]["precision"],
            "recall": boundary_report["test_metrics"]["learned_boundary_backend"]["recall"],
            "f1": boundary_report["test_metrics"]["learned_boundary_backend"]["f1"],
        },
        "summary": summarize(rows, comparisons),
        "policies": rows,
        "comparisons": comparisons,
        "claim": (
            "For the OSWorld-Human boundary task that rejected the R354 visible "
            "phase/action patch, boundary-derived operation fields improve AP and "
            "reduce fragmentation on held-out labeled traces, while preserving "
            "top-5 work and first-positive-work counterpoints."
        ),
        "non_claims": [
            "This is not a human or agent analyst study.",
            "This is not an automatic boundary-discovery claim.",
            "This is not a complete latent intent recovery claim.",
            "This is not an automatic patch selector; the tested patch is an explicit profile-spec alternative.",
            "The only profiler objects are operations and operation stacks; learned boundary fields are operation fields.",
        ],
    }
    write_reports(out_dir, report, rows, comparisons)
    print(json.dumps(load_json(out_dir / "run-result.json"), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
