#!/usr/bin/env python3
"""R329: leave-target transfer probe for operation rank policies.

R324/R326 show that visible per-operation rank features can improve a
task-specific profiler ranking.  R329 tests a stricter mechanism-isolation
question: can a rank policy be selected without using the target task labels,
then still improve localization on the target operation-stack profile?

The profiler sees only the scrubbed visible-operation JSONL.  Hidden labels are
used offline to select policies on training tasks and to score the held-out
target ranking after Rust emits the profile.
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
DEFAULT_OUT_DIR = OUT_ROOT / "operation-rank-feature-transfer-r329"
RUN_ID = "R329"
STACK_VARIANTS = ("semantic", "coarse")
SELECTION_PROTOCOLS = ("leave_task", "leave_dataset")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import operation_query_utility_eval as r300  # noqa: E402
import operation_rank_feature_eval as r324  # noqa: E402
import operation_rank_feature_robustness_eval as r326  # noqa: E402
import operation_rust_rank_rule_eval as r322  # noqa: E402


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_status_short(paths: list[Path] | None = None, include_untracked: bool = True) -> str:
    args = ["status", "--short"]
    if not include_untracked:
        args.append("--untracked-files=no")
    if paths:
        args.append("--")
        args.extend(r322.rel(path) for path in paths)
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


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def fmt_optional(value: float | None) -> str:
    return "" if value is None else f"{value:.4f}"


def task_by_id() -> dict[str, dict[str, Any]]:
    return {task["id"]: task for task in r300.TASKS}


def transfer_candidates() -> list[dict[str, Any]]:
    candidates = [
        {
            "policy": "global_equal",
            "policy_kind": "global_equal_weight",
            "source_task": None,
            "source_dataset": "global-visible-feature-bank",
            "source_query_family": None,
            "rank_op_rules": r326.GLOBAL_EQUAL_RULES,
        }
    ]
    for task in r300.TASKS:
        candidates.append(
            {
                "policy": f"source_equal_{task['id']}",
                "policy_kind": "source_task_equal_weight",
                "source_task": task["id"],
                "source_dataset": task["dataset"],
                "source_query_family": task["query_family"],
                "rank_op_rules": r326.equalize_rules(r324.OP_RANK_RULES[task["id"]]),
            }
        )
    return candidates


def policy_specs() -> list[dict[str, Any]]:
    return [
        {
            "policy": "width",
            "policy_kind": "baseline",
            "source_task": None,
            "source_dataset": None,
            "source_query_family": None,
            "rank_op_rules": [],
        },
        *transfer_candidates(),
    ]


def write_profile_spec(
    out_dir: Path,
    task: dict[str, Any],
    stack_kind: str,
    stack: list[str],
    policy: dict[str, Any],
) -> Path:
    stem = f"{task['id']}-{stack_kind}-{r326.slug(policy['policy'])}"
    spec_path = out_dir / f"{stem}-profile-spec.json"
    spec: dict[str, Any] = {
        "output": f"{stem}.json",
        "format": "json",
        "view": "operations",
        "operation_files": [str(r326.R324_VISIBLE_OPERATIONS.resolve())],
        "stack": ",".join(stack),
        "where_rules": [f"analysis_task={task['id']}"],
        "rank_mode": "rule-score",
        "deterministic_output": True,
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
    output = out_dir / f"{task['id']}-{stack_kind}-{r326.slug(policy['policy'])}.json"
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
        "query_family": task["query_family"],
        "problem": task["problem"],
        "stack_kind": stack_kind,
        "stack": stack,
        "policy": policy["policy"],
        "policy_kind": policy["policy_kind"],
        "source_task": policy["source_task"],
        "source_dataset": policy["source_dataset"],
        "source_query_family": policy["source_query_family"],
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
        row["delta_vs_width"] = r322.rounded(
            {
                "ap": metric_delta(row["metrics"], width["metrics"], "ap"),
                "ap_at_20": metric_delta(row["metrics"], width["metrics"], "ap_at_20"),
                "top5_lift": metric_delta(row["metrics"], width["metrics"], "top5_lift"),
                "top5_recall": metric_delta(row["metrics"], width["metrics"], "top5_recall"),
                "first_positive_work": metric_delta(
                    row["metrics"], width["metrics"], "first_positive_work"
                ),
            }
        )


def allowed_candidate(
    candidate: dict[str, Any],
    target: dict[str, Any],
    protocol: str,
) -> bool:
    if protocol == "leave_task":
        return candidate["source_task"] != target["id"]
    if protocol == "leave_dataset":
        return candidate["source_dataset"] != target["dataset"]
    raise ValueError(f"unknown selection protocol: {protocol}")


def train_tasks_for(target: dict[str, Any], protocol: str) -> set[str]:
    if protocol == "leave_task":
        return {task["id"] for task in r300.TASKS if task["id"] != target["id"]}
    if protocol == "leave_dataset":
        return {task["id"] for task in r300.TASKS if task["dataset"] != target["dataset"]}
    raise ValueError(f"unknown selection protocol: {protocol}")


def select_transfer_policy(
    rows: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    target: dict[str, Any],
    stack_kind: str,
    protocol: str,
) -> dict[str, Any]:
    by_key = {(row["task"], row["stack_kind"], row["policy"]): row for row in rows}
    train_task_ids = train_tasks_for(target, protocol)
    allowed = [candidate for candidate in candidates if allowed_candidate(candidate, target, protocol)]
    if not allowed or not train_task_ids:
        raise SystemExit(f"no training candidates for {target['id']} {stack_kind} {protocol}")

    scored_candidates = []
    for candidate in allowed:
        train_rows = [
            by_key[(task_id, stack_kind, candidate["policy"])]
            for task_id in sorted(train_task_ids)
            if (task_id, stack_kind, candidate["policy"]) in by_key
        ]
        train_ap_deltas = [
            row["delta_vs_width"]["ap"]
            for row in train_rows
            if row["delta_vs_width"]["ap"] is not None
        ]
        train_first_positive_deltas = [
            row["delta_vs_width"]["first_positive_work"]
            for row in train_rows
            if row["delta_vs_width"]["first_positive_work"] is not None
        ]
        if not train_ap_deltas:
            continue
        target_row = by_key[(target["id"], stack_kind, candidate["policy"])]
        scored_candidates.append(
            {
                "candidate": candidate,
                "target_row": target_row,
                "train_tasks": sorted(train_task_ids),
                "train_mean_delta_ap_vs_width": mean(train_ap_deltas),
                "train_mean_delta_first_positive_work_vs_width": mean(
                    train_first_positive_deltas
                ),
                "train_task_count": len(train_rows),
            }
        )
    if not scored_candidates:
        raise SystemExit(f"no scored candidates for {target['id']} {stack_kind} {protocol}")

    selected = sorted(
        scored_candidates,
        key=lambda item: (
            -(item["train_mean_delta_ap_vs_width"] or 0.0),
            item["candidate"]["policy"],
        ),
    )[0]
    oracle = sorted(
        scored_candidates,
        key=lambda item: (
            -(item["target_row"]["delta_vs_width"]["ap"] or 0.0),
            item["candidate"]["policy"],
        ),
    )[0]
    target_equal_policy = f"source_equal_{target['id']}"
    target_equal = by_key[(target["id"], stack_kind, target_equal_policy)]
    width = by_key[(target["id"], stack_kind, "width")]
    selected_row = selected["target_row"]
    selected_ap = selected_row["metrics"]["ap"]
    target_equal_ap = target_equal["metrics"]["ap"]
    oracle_ap = oracle["target_row"]["metrics"]["ap"]
    return r322.rounded(
        {
            "target_task": target["id"],
            "target_dataset": target["dataset"],
            "target_query_family": target["query_family"],
            "stack_kind": stack_kind,
            "protocol": protocol,
            "train_tasks": selected["train_tasks"],
            "train_task_count": selected["train_task_count"],
            "allowed_policy_count": len(scored_candidates),
            "selected_policy": selected["candidate"]["policy"],
            "selected_policy_kind": selected["candidate"]["policy_kind"],
            "selected_source_task": selected["candidate"]["source_task"],
            "selected_source_dataset": selected["candidate"]["source_dataset"],
            "selected_train_mean_delta_ap_vs_width": selected[
                "train_mean_delta_ap_vs_width"
            ],
            "selected_train_mean_delta_first_positive_work_vs_width": selected[
                "train_mean_delta_first_positive_work_vs_width"
            ],
            "width_ap": width["metrics"]["ap"],
            "selected_ap": selected_ap,
            "selected_delta_ap_vs_width": selected_row["delta_vs_width"]["ap"],
            "selected_top5_lift": selected_row["metrics"]["top5_lift"],
            "selected_delta_top5_lift_vs_width": selected_row["delta_vs_width"][
                "top5_lift"
            ],
            "width_first_positive_work": width["metrics"]["first_positive_work"],
            "selected_first_positive_work": selected_row["metrics"][
                "first_positive_work"
            ],
            "selected_delta_first_positive_work_vs_width": selected_row[
                "delta_vs_width"
            ]["first_positive_work"],
            "target_equal_policy": target_equal_policy,
            "target_equal_ap": target_equal_ap,
            "target_equal_delta_ap_vs_width": target_equal["delta_vs_width"]["ap"],
            "ap_gap_to_target_equal": target_equal_ap - selected_ap,
            "selected_no_more_than_0_02_below_target_equal": (
                target_equal_ap - selected_ap
            )
            <= 0.02,
            "oracle_best_candidate": oracle["candidate"]["policy"],
            "oracle_best_ap": oracle_ap,
            "oracle_best_delta_ap_vs_width": oracle["target_row"]["delta_vs_width"][
                "ap"
            ],
            "ap_gap_to_oracle_candidate": oracle_ap - selected_ap,
        }
    )


def selection_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = transfer_candidates()
    selections = []
    for task in r300.TASKS:
        for stack_kind in STACK_VARIANTS:
            for protocol in SELECTION_PROTOCOLS:
                selections.append(select_transfer_policy(rows, candidates, task, stack_kind, protocol))
    return selections


def ratio(
    rows: list[dict[str, Any]],
    protocol: str,
    stack_kind: str,
    field: str,
    positive: bool = True,
) -> str:
    items = [
        row
        for row in rows
        if row["protocol"] == protocol and row["stack_kind"] == stack_kind
    ]
    count = sum(
        (row[field] > 0 if positive else row[field] < 0)
        for row in items
        if row[field] is not None
    )
    return f"{count}/{len(items)}"


def bool_ratio(rows: list[dict[str, Any]], protocol: str, field: str) -> str:
    items = [row for row in rows if row["protocol"] == protocol]
    count = sum(bool(row[field]) for row in items)
    return f"{count}/{len(items)}"


def mean_field(rows: list[dict[str, Any]], protocol: str, field: str) -> float | None:
    values = [
        row[field]
        for row in rows
        if row["protocol"] == protocol and row[field] is not None
    ]
    return mean(values)


def selected_policy_counts(rows: list[dict[str, Any]], protocol: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        if row["protocol"] != protocol:
            continue
        counts[row["selected_policy"]] = counts.get(row["selected_policy"], 0) + 1
    return dict(sorted(counts.items()))


def build_summary(selections: list[dict[str, Any]], policy_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return r322.rounded(
        {
            "candidate_policies": len(transfer_candidates()),
            "evaluated_policies_including_width": len({row["policy"] for row in policy_rows}),
            "policy_evaluations": len(policy_rows),
            "selection_rows": len(selections),
            "leave_task_semantic_ap_wins_vs_width": ratio(
                selections, "leave_task", "semantic", "selected_delta_ap_vs_width"
            ),
            "leave_task_coarse_ap_wins_vs_width": ratio(
                selections, "leave_task", "coarse", "selected_delta_ap_vs_width"
            ),
            "leave_dataset_semantic_ap_wins_vs_width": ratio(
                selections, "leave_dataset", "semantic", "selected_delta_ap_vs_width"
            ),
            "leave_dataset_coarse_ap_wins_vs_width": ratio(
                selections, "leave_dataset", "coarse", "selected_delta_ap_vs_width"
            ),
            "leave_task_semantic_first_positive_work_wins_vs_width": ratio(
                selections,
                "leave_task",
                "semantic",
                "selected_delta_first_positive_work_vs_width",
                positive=False,
            ),
            "leave_dataset_semantic_first_positive_work_wins_vs_width": ratio(
                selections,
                "leave_dataset",
                "semantic",
                "selected_delta_first_positive_work_vs_width",
                positive=False,
            ),
            "leave_task_no_more_than_0_02_ap_below_target_equal": bool_ratio(
                selections,
                "leave_task",
                "selected_no_more_than_0_02_below_target_equal",
            ),
            "leave_dataset_no_more_than_0_02_ap_below_target_equal": bool_ratio(
                selections,
                "leave_dataset",
                "selected_no_more_than_0_02_below_target_equal",
            ),
            "leave_task_mean_ap_gap_to_oracle_candidate": mean_field(
                selections, "leave_task", "ap_gap_to_oracle_candidate"
            ),
            "leave_dataset_mean_ap_gap_to_oracle_candidate": mean_field(
                selections, "leave_dataset", "ap_gap_to_oracle_candidate"
            ),
            "leave_task_selected_policy_counts": selected_policy_counts(
                selections, "leave_task"
            ),
            "leave_dataset_selected_policy_counts": selected_policy_counts(
                selections, "leave_dataset"
            ),
        }
    )


def write_policy_csv(out_dir: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "task",
        "dataset",
        "stack_kind",
        "policy",
        "policy_kind",
        "source_task",
        "source_dataset",
        "groups",
        "ap",
        "delta_ap_vs_width",
        "top5_lift",
        "delta_top5_lift_vs_width",
        "first_positive_work",
        "delta_first_positive_work_vs_width",
    ]
    with (out_dir / "rank-feature-transfer-summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as file:
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
                    "source_task": row["source_task"] or "",
                    "source_dataset": row["source_dataset"] or "",
                    "groups": row["groups"],
                    "ap": row["metrics"]["ap"],
                    "delta_ap_vs_width": row["delta_vs_width"]["ap"],
                    "top5_lift": row["metrics"]["top5_lift"],
                    "delta_top5_lift_vs_width": row["delta_vs_width"]["top5_lift"],
                    "first_positive_work": row["metrics"]["first_positive_work"],
                    "delta_first_positive_work_vs_width": row["delta_vs_width"][
                        "first_positive_work"
                    ],
                }
            )


def write_selection_csv(out_dir: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "target_task",
        "target_dataset",
        "stack_kind",
        "protocol",
        "train_task_count",
        "allowed_policy_count",
        "selected_policy",
        "selected_source_task",
        "selected_source_dataset",
        "selected_train_mean_delta_ap_vs_width",
        "width_ap",
        "selected_ap",
        "selected_delta_ap_vs_width",
        "target_equal_ap",
        "ap_gap_to_target_equal",
        "oracle_best_candidate",
        "oracle_best_ap",
        "ap_gap_to_oracle_candidate",
        "selected_first_positive_work",
        "selected_delta_first_positive_work_vs_width",
    ]
    with (out_dir / "rank-feature-transfer-selections.csv").open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") or "" for field in fieldnames})


def write_markdown(out_dir: Path, summary: dict[str, Any], selections: list[dict[str, Any]]) -> None:
    lines = [
        "# R329 Leave-Target Rank-Policy Transfer",
        "",
        f"- Profiler input: `{r322.rel(r326.R324_VISIBLE_OPERATIONS)}`",
        f"- Leave-task semantic AP wins vs width: {summary['leave_task_semantic_ap_wins_vs_width']}",
        f"- Leave-dataset semantic AP wins vs width: {summary['leave_dataset_semantic_ap_wins_vs_width']}",
        f"- Leave-task within 0.02 AP of target-equal policy: {summary['leave_task_no_more_than_0_02_ap_below_target_equal']}",
        f"- Leave-dataset within 0.02 AP of target-equal policy: {summary['leave_dataset_no_more_than_0_02_ap_below_target_equal']}",
        "",
        "## Held-Out Selections",
        "",
        "| Target | Dataset | Stack | Protocol | Selected policy | Delta AP | Gap to oracle | Delta WTFP |",
        "|---|---|---|---|---|---:|---:|---:|",
    ]
    for row in selections:
        lines.append(
            "| {target} | {dataset} | {stack} | {protocol} | {policy} | "
            "{delta_ap:.4f} | {gap:.4f} | {delta_wtfp} |".format(
                target=row["target_task"],
                dataset=row["target_dataset"],
                stack=row["stack_kind"],
                protocol=row["protocol"],
                policy=row["selected_policy"],
                delta_ap=row["selected_delta_ap_vs_width"],
                gap=row["ap_gap_to_oracle_candidate"],
                delta_wtfp=fmt_optional(row["selected_delta_first_positive_work_vs_width"]),
            )
        )
    lines.extend(
        [
            "",
            "Policy selection uses labels from non-target tasks only. The target task labels are used only after profiling to score the emitted ranking.",
            "",
        ]
    )
    (out_dir / "rank-feature-transfer-report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def write_html(out_dir: Path, summary: dict[str, Any], selections: list[dict[str, Any]]) -> None:
    items = "\n".join(
        f"<li>{html.escape(key)}: {html.escape(str(value))}</li>"
        for key, value in summary.items()
    )
    rows = "\n".join(
        f"<tr><td>{html.escape(row['target_task'])}</td>"
        f"<td>{html.escape(row['target_dataset'])}</td>"
        f"<td>{html.escape(row['stack_kind'])}</td>"
        f"<td>{html.escape(row['protocol'])}</td>"
        f"<td>{html.escape(row['selected_policy'])}</td>"
        f"<td>{row['selected_delta_ap_vs_width']:.4f}</td>"
        f"<td>{row['ap_gap_to_oracle_candidate']:.4f}</td>"
        f"<td>{fmt_optional(row['selected_delta_first_positive_work_vs_width'])}</td></tr>"
        for row in selections
    )
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>R329 Leave-Target Rank-Policy Transfer</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #1f2937; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; }}
th, td {{ border-bottom: 1px solid #d1d5db; padding: 8px; text-align: right; }}
th:first-child, td:first-child, th:nth-child(2), td:nth-child(2),
th:nth-child(3), td:nth-child(3), th:nth-child(4), td:nth-child(4),
th:nth-child(5), td:nth-child(5) {{ text-align: left; }}
code {{ background: #f3f4f6; padding: 1px 4px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>R329 Leave-Target Rank-Policy Transfer</h1>
<p>Profiler input: <code>{html.escape(r322.rel(r326.R324_VISIBLE_OPERATIONS))}</code>. Target labels are held out from policy selection and used only for offline scoring.</p>
<ul>{items}</ul>
<table>
<thead><tr><th>Target</th><th>Dataset</th><th>Stack</th><th>Protocol</th><th>Selected policy</th><th>Delta AP</th><th>Gap to oracle</th><th>Delta WTFP</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</body>
</html>
"""
    (out_dir / "index.html").write_text(html_doc, encoding="utf-8")


def write_reports(
    out_dir: Path,
    rows: list[dict[str, Any]],
    selections: list[dict[str, Any]],
    source_check: dict[str, Any],
    leakage_check: dict[str, Any],
    profiler_input_check: dict[str, Any],
    elapsed_s: float,
) -> None:
    summary = build_summary(selections, rows)
    source_status = {
        "tracked_status_short": git_status_short(include_untracked=False),
        "code_status_short": git_status_short(
            [
                ROOT / "script" / "operation_rank_feature_transfer_eval.py",
                ROOT / "script" / "operation_rank_feature_robustness_eval.py",
                ROOT / "script" / "operation_rank_feature_eval.py",
                ROOT / "script" / "operation_rust_rank_rule_eval.py",
                ROOT / "agentpprof",
            ]
        ),
        "untracked_outputs_excluded_from_tracked_status": True,
    }
    report = {
        "run_id": RUN_ID,
        "status": "pass",
        "commit": r322.git_output(["rev-parse", "HEAD"]),
        "elapsed_s": round(elapsed_s, 3),
        "source_operations": r322.rel(r322.SOURCE_OPERATIONS),
        "profiler_operation_file": r322.rel(r326.R324_VISIBLE_OPERATIONS),
        "tasks": len(r300.TASKS),
        "stack_variants": list(STACK_VARIANTS),
        "selection_protocols": list(SELECTION_PROTOCOLS),
        "summary": summary,
        "source_check": source_check,
        "source_status": source_status,
        "leakage_check": leakage_check,
        "profiler_input_check": profiler_input_check,
        "selection_label_use": {
            "target_hidden_labels_used_for_policy_selection": False,
            "training_hidden_labels_used_for_policy_selection": True,
            "target_hidden_labels_used_for_final_scoring": True,
            "rust_profiler_receives_hidden_labels": False,
        },
        "policy_rows": rows,
        "selection_rows": selections,
        "claim": (
            "Held-out transfer selection tests whether operation rank policies can "
            "localize task-relevant operation-stack groups without selecting the "
            "policy on the target task labels."
        ),
        "non_claims": [
            "This is not a human/agent analyst productivity study.",
            "This is not a label-free deployment ranker; policy selection still uses labeled training tasks.",
            "This does not claim automatic discovery of all intent or semantic boundaries.",
            "This does not add abstractions beyond operation and operation stack.",
            "This does not download, sync, or create a new dataset.",
            "The oracle-best candidate is a hidden-label upper bound for headroom only.",
            "The global feature bank is a fixed visible-feature policy, not a learned cross-dataset model.",
        ],
    }
    write_json(out_dir / "rank-feature-transfer-report.json", r322.rounded(report))
    write_json(
        out_dir / "run-result.json",
        {"status": "pass", "report": r322.rel(out_dir / "rank-feature-transfer-report.json")},
    )
    write_policy_csv(out_dir, rows)
    write_selection_csv(out_dir, selections)
    write_markdown(out_dir, summary, selections)
    write_html(out_dir, summary, selections)


def main() -> None:
    start = time.perf_counter()
    out_dir = DEFAULT_OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    source_paths = sorted(
        {
            r322.SOURCE_OPERATIONS,
            r326.R324_VISIBLE_OPERATIONS,
            *(task["operation_file"] for task in r300.TASKS),
        }
    )
    r322.ensure_sources_tracked_clean(source_paths)
    source_check = {
        "status": "pass",
        "tracked_clean_files": len(source_paths),
        "files": [r322.rel(path) for path in source_paths],
    }
    rule_sets = {candidate["policy"]: candidate["rank_op_rules"] for candidate in transfer_candidates()}
    leakage_check = r326.validate_rules_visible(rule_sets)
    profiler_input_check = r324.validate_visible_operation_file(r326.R324_VISIBLE_OPERATIONS)

    rows = []
    policies = policy_specs()
    for task in r300.TASKS:
        for stack_kind, stack in (
            ("semantic", list(task["semantic_stack"])),
            ("coarse", r324.coarse_stack(task)),
        ):
            groups, summary = r324.group_task_for_stack(task, stack)
            for policy in policies:
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
    annotate_deltas(rows)
    selections = selection_rows(rows)
    write_reports(
        out_dir,
        rows,
        selections,
        source_check,
        leakage_check,
        profiler_input_check,
        time.perf_counter() - start,
    )


if __name__ == "__main__":
    main()
