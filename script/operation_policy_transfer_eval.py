#!/usr/bin/env python3
"""R340: cross-task and cross-family visible policy transfer audit.

This audit does not fetch, sync, create, or relabel datasets. It reads the
already-scored R320 and R339 artifacts and asks whether a visible profiler
policy can be selected from non-target tasks/families, then evaluated on the
held-out task. Hidden labels are not used to select on the target task.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
R320_DIR = OUT_ROOT / "operation-profile-accuracy-r320"
R339_DIR = OUT_ROOT / "operation-sequence-adequacy-r339"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-policy-transfer-r340"
RUN_ID = "R340"

R320_REPORT = R320_DIR / "profile-accuracy-report.json"
R320_POLICY_SCORES = R320_DIR / "policy-scores.csv"
R339_REPORT = R339_DIR / "sequence-adequacy-report.json"
R339_TASK_SCORES = R339_DIR / "task-sequence-adequacy.csv"

DEFAULT_POLICY = "operation_stack:query_aware"
WIDTH_POLICY = "operation_stack:width"
FIXED_POLICY = "fixed_session:query_aware"
FLAT_POLICY = "flat:width"
RAW_ACTION_POLICY = "raw_action_stack:query_aware"
DATASET_NATIVE_POLICY = "dataset_native:query_aware"
BASELINE_POLICIES = {
    "default_operation_stack_query_aware": DEFAULT_POLICY,
    "operation_stack_width": WIDTH_POLICY,
    "fixed_session_query_aware": FIXED_POLICY,
    "flat_width": FLAT_POLICY,
    "raw_action_query_aware": RAW_ACTION_POLICY,
    "dataset_native_query_aware": DATASET_NATIVE_POLICY,
}

OBJECTIVES = {
    "ranking_fidelity_ap": {
        "metric": "average_precision",
        "direction": "higher",
        "source": "R320",
        "tolerance": 0.02,
        "question": "Can a non-target-selected policy preserve AP ranking fidelity?",
    },
    "top5_localization_f1": {
        "metric": "top5_f1",
        "direction": "higher",
        "source": "R320",
        "tolerance": 0.02,
        "question": "Can transfer choose a good top-five precision/recall tradeoff?",
    },
    "budget30_operation_recall": {
        "metric": "budget30_recall",
        "direction": "higher",
        "source": "R320",
        "tolerance": 0.02,
        "question": "Can transfer choose policies with high operation recall under 30% work?",
    },
    "first_positive_work": {
        "metric": "work_to_first_positive",
        "direction": "lower",
        "source": "R320",
        "tolerance": 0.02,
        "question": "Can transfer preserve first-positive work without target labels?",
    },
    "groups_to_50pct": {
        "metric": "groups_to_50pct_recall",
        "direction": "lower",
        "source": "R320",
        "tolerance": 5.0,
        "question": "Can transfer keep the ranked-group cost near the best visible policy?",
    },
    "sequence_top5_session_recall": {
        "metric": "top5_positive_session_recall",
        "direction": "higher",
        "source": "R339",
        "tolerance": 0.02,
        "question": "Can transfer hit positive sessions in the top five groups?",
    },
    "sequence_budget30_session_recall": {
        "metric": "budget30_positive_session_recall",
        "direction": "higher",
        "source": "R339",
        "tolerance": 0.02,
        "question": "Can transfer preserve positive-session recall under 30% work?",
    },
    "sequence_budget30_session_work": {
        "metric": "budget30_session_work",
        "direction": "lower",
        "source": "R339",
        "tolerance": 0.02,
        "question": "Can transfer keep session scope small under a 30% operation budget?",
    },
}

PROTOCOLS = ("leave_task", "leave_dataset")


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(round_value(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_value(row.get(field)) for field in fields})


def format_value(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value):
            return ""
        if math.isinf(value):
            return "inf"
        return round(value, 4)
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(round_value(value), sort_keys=True)
    return value


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


def parse_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    return float(value)


def policy_key(row: dict[str, str]) -> str:
    return f"{row['view']}:{row['ranker']}"


def direction_better(left: float | None, right: float | None, direction: str) -> bool:
    if left is None:
        return False
    if right is None:
        return True
    return left > right if direction == "higher" else left < right


def direction_delta(left: float | None, right: float | None, direction: str) -> float | None:
    if left is None or right is None:
        return None
    return left - right if direction == "higher" else right - left


def is_within_tolerance(value: float | None, best: float | None, direction: str, tolerance: float) -> bool:
    if value is None or best is None:
        return False
    if direction == "higher":
        return value >= best - tolerance
    return value <= best + tolerance


def visible_policy_rows() -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]]]:
    rows_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    tasks: dict[str, dict[str, Any]] = {}
    numeric_r320 = {
        "operations",
        "positives",
        "groups",
        "average_precision",
        "ndcg",
        "top5_precision",
        "top5_recall",
        "top5_f1",
        "top5_work",
        "budget30_recall",
        "budget30_f1",
        "budget30_work",
        "work_to_first_positive",
        "groups_to_50pct_recall",
        "work_to_50pct_recall",
    }
    for raw in read_csv(R320_POLICY_SCORES):
        if raw["uses_hidden_fields"] != "False":
            continue
        task = raw["task"]
        policy = policy_key(raw)
        tasks[task] = {
            "task": task,
            "dataset": raw["dataset"],
            "query_family": raw["query_family"],
        }
        row: dict[str, Any] = {
            "task": task,
            "dataset": raw["dataset"],
            "query_family": raw["query_family"],
            "view": raw["view"],
            "ranker": raw["ranker"],
            "policy": policy,
            "uses_hidden_fields": False,
        }
        for field in numeric_r320:
            row[field] = parse_float(raw.get(field))
        rows_by_key[(task, policy)] = row

    numeric_r339 = {
        "top5_positive_session_recall",
        "top5_session_work",
        "budget30_positive_session_recall",
        "budget30_session_work",
        "budget30_positive_session_lift",
        "budget30_session_efficiency",
    }
    for raw in read_csv(R339_TASK_SCORES):
        if raw["uses_hidden_fields"] != "False":
            continue
        key = (raw["task"], policy_key(raw))
        if key not in rows_by_key:
            continue
        for field in numeric_r339:
            rows_by_key[key][field] = parse_float(raw.get(field))

    return list(tasks.values()), rows_by_key


def candidate_policies(rows_by_key: dict[tuple[str, str], dict[str, Any]]) -> list[str]:
    policies = sorted({policy for _, policy in rows_by_key})
    return [policy for policy in policies if not policy.startswith("label_drilldown:")]


def train_tasks(tasks: list[dict[str, Any]], target: dict[str, Any], protocol: str) -> list[str]:
    if protocol == "leave_task":
        return [task["task"] for task in tasks if task["task"] != target["task"]]
    if protocol == "leave_dataset":
        return [task["task"] for task in tasks if task["dataset"] != target["dataset"]]
    raise ValueError(f"unknown protocol {protocol}")


def policy_metric_values(
    rows_by_key: dict[tuple[str, str], dict[str, Any]],
    task_ids: list[str],
    policy: str,
    metric: str,
) -> list[float]:
    values = []
    for task in task_ids:
        value = rows_by_key[(task, policy)].get(metric)
        if value is not None:
            values.append(float(value))
    return values


def best_policy_for_tasks(
    rows_by_key: dict[tuple[str, str], dict[str, Any]],
    task_ids: list[str],
    policies: list[str],
    metric: str,
    direction: str,
) -> tuple[str, float]:
    scored = []
    for policy in policies:
        values = policy_metric_values(rows_by_key, task_ids, policy, metric)
        if len(values) != len(task_ids):
            continue
        scored.append((policy, mean(values)))
    if not scored:
        raise SystemExit(f"no candidate policies for metric={metric} tasks={task_ids}")
    return max(scored, key=lambda item: item[1]) if direction == "higher" else min(scored, key=lambda item: item[1])


def sorted_target_policies(
    rows_by_key: dict[tuple[str, str], dict[str, Any]],
    target_task: str,
    policies: list[str],
    metric: str,
    direction: str,
) -> list[tuple[str, float | None]]:
    scored = [(policy, rows_by_key[(target_task, policy)].get(metric)) for policy in policies]
    scored = [item for item in scored if item[1] is not None]
    return sorted(scored, key=lambda item: item[1], reverse=(direction == "higher"))


def build_decisions(
    tasks: list[dict[str, Any]],
    rows_by_key: dict[tuple[str, str], dict[str, Any]],
    policies: list[str],
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for protocol in PROTOCOLS:
        for target in tasks:
            train_task_ids = train_tasks(tasks, target, protocol)
            for objective, spec in OBJECTIVES.items():
                metric = spec["metric"]
                direction = spec["direction"]
                selected_policy, train_mean = best_policy_for_tasks(
                    rows_by_key, train_task_ids, policies, metric, direction
                )
                target_order = sorted_target_policies(
                    rows_by_key, target["task"], policies, metric, direction
                )
                best_policy, best_value = target_order[0]
                selected_value = rows_by_key[(target["task"], selected_policy)].get(metric)
                default_value = rows_by_key[(target["task"], DEFAULT_POLICY)].get(metric)
                width_value = rows_by_key[(target["task"], WIDTH_POLICY)].get(metric)
                fixed_value = rows_by_key[(target["task"], FIXED_POLICY)].get(metric)
                flat_value = rows_by_key[(target["task"], FLAT_POLICY)].get(metric)
                selected_rank = 1 + [policy for policy, _ in target_order].index(selected_policy)
                decisions.append(
                    {
                        "protocol": protocol,
                        "task": target["task"],
                        "dataset": target["dataset"],
                        "query_family": target["query_family"],
                        "objective": objective,
                        "metric": metric,
                        "direction": direction,
                        "question": spec["question"],
                        "train_tasks": len(train_task_ids),
                        "selected_policy": selected_policy,
                        "selected_view": selected_policy.split(":", 1)[0],
                        "selected_ranker": selected_policy.split(":", 1)[1],
                        "selected_train_mean": train_mean,
                        "selected_target_value": selected_value,
                        "selected_target_rank": selected_rank,
                        "best_visible_policy": best_policy,
                        "best_visible_value": best_value,
                        "default_value": default_value,
                        "width_value": width_value,
                        "fixed_value": fixed_value,
                        "flat_value": flat_value,
                        "selected_exact_best": selected_policy == best_policy,
                        "selected_within_tolerance": is_within_tolerance(
                            selected_value, best_value, direction, spec["tolerance"]
                        ),
                        "selected_delta_vs_best": direction_delta(selected_value, best_value, direction),
                        "selected_delta_vs_default": direction_delta(selected_value, default_value, direction),
                        "selected_delta_vs_width": direction_delta(selected_value, width_value, direction),
                        "selected_delta_vs_fixed": direction_delta(selected_value, fixed_value, direction),
                        "selected_delta_vs_flat": direction_delta(selected_value, flat_value, direction),
                        "selected_beats_default": direction_better(selected_value, default_value, direction),
                        "selected_beats_width": direction_better(selected_value, width_value, direction),
                        "selected_beats_fixed": direction_better(selected_value, fixed_value, direction),
                        "selected_beats_flat": direction_better(selected_value, flat_value, direction),
                        "default_within_tolerance": is_within_tolerance(
                            default_value, best_value, direction, spec["tolerance"]
                        ),
                    }
                )
    return decisions


def summarize_decisions(decisions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    objective_rows: list[dict[str, Any]] = []
    for (protocol, objective), group in sorted(group_by(decisions, ["protocol", "objective"]).items()):
        objective_rows.append(summarize_group(group, {"protocol": protocol, "objective": objective}))

    selected_rows = []
    selected_counts = Counter(row["selected_policy"] for row in decisions)
    for policy, count in selected_counts.most_common():
        selected_rows.append(
            {
                "selected_policy": policy,
                "selected_view": policy.split(":", 1)[0],
                "selected_ranker": policy.split(":", 1)[1],
                "decisions": count,
                "exact_best": sum(row["selected_exact_best"] for row in decisions if row["selected_policy"] == policy),
                "within_tolerance": sum(
                    row["selected_within_tolerance"] for row in decisions if row["selected_policy"] == policy
                ),
            }
        )

    task_rows = []
    for (protocol, task), group in sorted(group_by(decisions, ["protocol", "task"]).items()):
        task_rows.append(summarize_group(group, {"protocol": protocol, "task": task, "dataset": group[0]["dataset"]}))
    return objective_rows, selected_rows, task_rows


def group_by(rows: list[dict[str, Any]], keys: list[str]) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[key] for key in keys)].append(row)
    return groups


def summarize_group(rows: list[dict[str, Any]], prefix: dict[str, Any]) -> dict[str, Any]:
    return {
        **prefix,
        "decisions": len(rows),
        "exact_best": sum(row["selected_exact_best"] for row in rows),
        "within_tolerance": sum(row["selected_within_tolerance"] for row in rows),
        "default_within_tolerance": sum(row["default_within_tolerance"] for row in rows),
        "beats_default": sum(row["selected_beats_default"] for row in rows),
        "beats_width": sum(row["selected_beats_width"] for row in rows),
        "beats_fixed": sum(row["selected_beats_fixed"] for row in rows),
        "beats_flat": sum(row["selected_beats_flat"] for row in rows),
        "median_target_rank": median([row["selected_target_rank"] for row in rows]),
        "median_delta_vs_best": median(
            [row["selected_delta_vs_best"] for row in rows if row["selected_delta_vs_best"] is not None]
        ),
        "operation_stack_selected": sum(row["selected_view"] == "operation_stack" for row in rows),
        "fixed_session_selected": sum(row["selected_view"] == "fixed_session" for row in rows),
        "flat_selected": sum(row["selected_view"] == "flat" for row in rows),
        "dataset_native_selected": sum(row["selected_view"] == "dataset_native" for row in rows),
        "raw_action_selected": sum(row["selected_view"] == "raw_action_stack" for row in rows),
    }


def build_case_cards(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards = []
    for (protocol, task), group in sorted(group_by(decisions, ["protocol", "task"]).items()):
        exact = sum(row["selected_exact_best"] for row in group)
        within = sum(row["selected_within_tolerance"] for row in group)
        selected_views = Counter(row["selected_view"] for row in group)
        hard = [
            f"{row['objective']}->{row['selected_policy']} rank {row['selected_target_rank']}"
            for row in group
            if not row["selected_within_tolerance"]
        ][:3]
        cards.append(
            {
                "protocol": protocol,
                "task": task,
                "dataset": group[0]["dataset"],
                "objectives": len(group),
                "exact_best": exact,
                "within_tolerance": within,
                "dominant_selected_view": selected_views.most_common(1)[0][0],
                "selected_views": dict(selected_views),
                "hard_counterexamples": "; ".join(hard),
            }
        )
    return cards


def build_report(
    out_dir: Path,
    tasks: list[dict[str, Any]],
    policies: list[str],
    decisions: list[dict[str, Any]],
    objective_rows: list[dict[str, Any]],
    selected_rows: list[dict[str, Any]],
    task_rows: list[dict[str, Any]],
    case_cards: list[dict[str, Any]],
    source_status: dict[str, str],
) -> dict[str, Any]:
    by_protocol = {protocol: summarize_group([row for row in decisions if row["protocol"] == protocol], {"protocol": protocol}) for protocol in PROTOCOLS}
    total = summarize_group(decisions, {"protocol": "all"})
    default_rows = [row for row in decisions if row["selected_policy"] == DEFAULT_POLICY]
    claim_summary = {
        "supported_wording": (
            "Selecting visible view/ranker policies from non-target tasks gives an auditable "
            "transfer signal: it often stays near the best visible held-out policy, but exact "
            "best policy selection remains task- and objective-specific."
        ),
        "scope_guardrails": [
            "does not use target hidden labels for policy selection",
            "does not prove an automatic universal selector",
            "does not make operation-stack query-aware the best policy for every objective",
            "does not replace task-specific actionability cards or fixed-session counterpoints",
        ],
        "must_not_claim": [
            "target hidden labels are used to select the transferred policy",
            "R340 proves an automatic universal selector",
            "operation-stack query-aware is the best policy for every objective",
            "task-specific actionability cards or fixed-session counterpoints are unnecessary",
        ],
        "total_decisions": len(decisions),
        "visible_policies": len(policies),
        "tasks": len(tasks),
        "objectives": len(OBJECTIVES),
        "protocols": list(PROTOCOLS),
        "exact_best_decisions": total["exact_best"],
        "within_tolerance_decisions": total["within_tolerance"],
        "default_within_tolerance_decisions": total["default_within_tolerance"],
        "operation_stack_selected_decisions": total["operation_stack_selected"],
        "fixed_session_selected_decisions": total["fixed_session_selected"],
        "selected_beats_width_decisions": total["beats_width"],
        "selected_beats_fixed_decisions": total["beats_fixed"],
        "selected_beats_flat_decisions": total["beats_flat"],
        "leave_task": by_protocol["leave_task"],
        "leave_dataset": by_protocol["leave_dataset"],
        "default_selected_decisions": len(default_rows),
    }
    return {
        "schema": "agentsight.operation-policy-transfer.v1",
        "run_id": RUN_ID,
        "created_unix": time.time(),
        "commit": git_output(["rev-parse", "HEAD"]),
        "source_status": source_status,
        "source_paths": [rel(R320_REPORT), rel(R320_POLICY_SCORES), rel(R339_REPORT), rel(R339_TASK_SCORES)],
        "input_policy": {
            "dataset_sync": "none",
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "network_access_required": False,
            "target_hidden_label_use": "not used for policy selection",
            "hidden_label_use": "R340 reads already-scored R320/R339 metrics and selects only from non-target tasks/families",
        },
        "profiler_abstractions": ["operation", "operation stack"],
        "summary": {
            "overall": "pass",
            "tasks": len(tasks),
            "visible_policies": len(policies),
            "objectives": len(OBJECTIVES),
            "protocols": len(PROTOCOLS),
            "transfer_decisions": len(decisions),
            "source_artifacts_tracked_clean": all(status == "tracked_clean" for status in source_status.values()),
            "network_access_required": False,
            "dataset_sync": "none",
        },
        "claim_summary": claim_summary,
        "objective_summary": objective_rows,
        "selected_policy_summary": selected_rows,
        "task_transfer_cards": task_rows,
        "case_cards": case_cards,
        "artifact_paths": {
            "report": rel(out_dir / "policy-transfer-report.json"),
            "markdown": rel(out_dir / "policy-transfer-report.md"),
            "transfer_decisions": rel(out_dir / "transfer-decisions.csv"),
            "objective_summary": rel(out_dir / "objective-transfer-summary.csv"),
            "selected_policy_summary": rel(out_dir / "selected-policy-summary.csv"),
            "task_cards": rel(out_dir / "task-transfer-cards.csv"),
            "index": rel(out_dir / "index.html"),
        },
    }


def build_markdown(path: Path, report: dict[str, Any]) -> None:
    cs = report["claim_summary"]
    lines = [
        "# Operation Policy Transfer Audit R340",
        "",
        "R340 selects visible profile policies using only non-target tasks or non-target datasets, then scores the selected policy on the held-out task using already-scored R320/R339 metrics.",
        "",
        "## Verdict",
        "",
        f"- Transfer decisions: {cs['total_decisions']}.",
        f"- Exact held-out best selections: {cs['exact_best_decisions']}/{cs['total_decisions']}.",
        f"- Within-tolerance selections: {cs['within_tolerance_decisions']}/{cs['total_decisions']}.",
        f"- Operation-stack selected decisions: {cs['operation_stack_selected_decisions']}/{cs['total_decisions']}.",
        f"- Beats width baseline: {cs['selected_beats_width_decisions']}/{cs['total_decisions']}.",
        f"- Beats fixed-session baseline: {cs['selected_beats_fixed_decisions']}/{cs['total_decisions']}.",
        "",
        "Supported wording: " + cs["supported_wording"],
        "",
        "Scope guardrails:",
        *[f"- {item}" for item in cs["scope_guardrails"]],
        "",
        "Must not claim:",
        *[f"- {item}" for item in cs["must_not_claim"]],
        "",
        "## Objective Summary",
        "",
        "| Protocol | Objective | Decisions | Exact best | Within tolerance | Median target rank | Operation-stack selected |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in report["objective_summary"]:
        lines.append(
            f"| {row['protocol']} | {row['objective']} | {row['decisions']} | {row['exact_best']} | {row['within_tolerance']} | {row['median_target_rank']} | {row['operation_stack_selected']} |"
        )
    lines.extend(
        [
            "",
            "## Task Cards",
            "",
            "| Protocol | Task | Dataset | Exact best | Within tolerance | Dominant selected view | Counterexamples |",
            "|---|---|---|---:|---:|---|---|",
        ]
    )
    for row in report["case_cards"]:
        lines.append(
            f"| {row['protocol']} | {row['task']} | {row['dataset']} | {row['exact_best']} | {row['within_tolerance']} | {row['dominant_selected_view']} | {row['hard_counterexamples']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_html(path: Path, report: dict[str, Any]) -> None:
    def table(rows: list[dict[str, Any]], fields: list[str]) -> str:
        head = "".join(f"<th>{html.escape(field)}</th>" for field in fields)
        body = []
        for row in rows:
            body.append(
                "<tr>"
                + "".join(f"<td>{html.escape(str(format_value(row.get(field, ''))))}</td>" for field in fields)
                + "</tr>"
            )
        return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"

    cs = report["claim_summary"]
    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>R340 Operation Policy Transfer Audit</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 32px; line-height: 1.45; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 13px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 6px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f6f8fa; }}
    code {{ background: #f6f8fa; padding: 1px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>R340 Operation Policy Transfer Audit</h1>
  <p>{html.escape(cs['supported_wording'])}</p>
  <h2>Claim Summary</h2>
  {table([cs], ['total_decisions', 'visible_policies', 'exact_best_decisions', 'within_tolerance_decisions', 'operation_stack_selected_decisions', 'selected_beats_width_decisions', 'selected_beats_fixed_decisions'])}
  <h2>Objectives</h2>
  {table(report['objective_summary'], ['protocol', 'objective', 'decisions', 'exact_best', 'within_tolerance', 'median_target_rank', 'operation_stack_selected'])}
  <h2>Task Cards</h2>
  {table(report['case_cards'], ['protocol', 'task', 'dataset', 'exact_best', 'within_tolerance', 'dominant_selected_view', 'hard_counterexamples'])}
</body>
</html>
"""
    path.write_text(content, encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    source_status = ensure_sources_tracked_clean([R320_REPORT, R320_POLICY_SCORES, R339_REPORT, R339_TASK_SCORES])
    # Load reports to fail early if the source JSON schemas drift.
    load_json(R320_REPORT)
    load_json(R339_REPORT)
    tasks, rows_by_key = visible_policy_rows()
    policies = candidate_policies(rows_by_key)
    decisions = build_decisions(tasks, rows_by_key, policies)
    objective_rows, selected_rows, task_rows = summarize_decisions(decisions)
    case_cards = build_case_cards(decisions)
    report = build_report(out_dir, tasks, policies, decisions, objective_rows, selected_rows, task_rows, case_cards, source_status)

    write_json(out_dir / "policy-transfer-report.json", report)
    build_markdown(out_dir / "policy-transfer-report.md", report)
    build_html(out_dir / "index.html", report)
    write_csv(
        out_dir / "transfer-decisions.csv",
        decisions,
        [
            "protocol",
            "task",
            "dataset",
            "query_family",
            "objective",
            "metric",
            "direction",
            "train_tasks",
            "selected_policy",
            "selected_train_mean",
            "selected_target_value",
            "selected_target_rank",
            "best_visible_policy",
            "best_visible_value",
            "default_value",
            "width_value",
            "fixed_value",
            "flat_value",
            "selected_exact_best",
            "selected_within_tolerance",
            "selected_delta_vs_best",
            "selected_delta_vs_default",
            "selected_delta_vs_width",
            "selected_delta_vs_fixed",
            "selected_delta_vs_flat",
            "selected_beats_default",
            "selected_beats_width",
            "selected_beats_fixed",
            "selected_beats_flat",
            "default_within_tolerance",
        ],
    )
    write_csv(
        out_dir / "objective-transfer-summary.csv",
        objective_rows,
        [
            "protocol",
            "objective",
            "decisions",
            "exact_best",
            "within_tolerance",
            "default_within_tolerance",
            "beats_default",
            "beats_width",
            "beats_fixed",
            "beats_flat",
            "median_target_rank",
            "median_delta_vs_best",
            "operation_stack_selected",
            "fixed_session_selected",
            "flat_selected",
            "dataset_native_selected",
            "raw_action_selected",
        ],
    )
    write_csv(
        out_dir / "selected-policy-summary.csv",
        selected_rows,
        ["selected_policy", "selected_view", "selected_ranker", "decisions", "exact_best", "within_tolerance"],
    )
    write_csv(
        out_dir / "task-transfer-cards.csv",
        case_cards,
        ["protocol", "task", "dataset", "objectives", "exact_best", "within_tolerance", "dominant_selected_view", "selected_views", "hard_counterexamples"],
    )
    write_json(
        out_dir / "run-result.json",
        {
            "run_id": RUN_ID,
            "schema": report["schema"],
            "summary": report["summary"],
            "commit": report["commit"],
        },
    )
    print(json.dumps(report["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
