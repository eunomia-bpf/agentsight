#!/usr/bin/env python3
"""Run R229 controlled multi-workspace exact-lineage replication.

R229 is a local replication run, not human evidence. It reuses the R114
record/export/lineage oracle over a smaller suite that spans the repository and
several disposable project workspaces. The result can strengthen C4/RQ3 within
the fixed command-mode scope, but it does not prove full-history exact lineage.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from r114_live_record_suite import (
    DEFAULT_OUT,
    REPO_ROOT,
    Task,
    aggregate,
    manifest_rows,
    record_task,
    rel,
    resolve_executable,
    scrub_artifact_value,
)


DEFAULT_WORK = Path("/tmp/agentsight-r229-exact-lineage")
WORK_MARKER = ".agentsight-r229-exact-lineage"


R229_TASKS = [
    Task(
        "r229-repo-r191-read",
        "repo-read",
        (
            "Read docs/visexp/out/live-network-r191.md. Answer exactly one line: "
            "r191_status=<Completeness value>. Do not modify files."
        ),
        sandbox="read-only",
        workspace="repo",
    ),
    Task(
        "r229-python-fix",
        "edit-test",
        (
            "Fix calc.py so `python3 -m unittest` passes. You may edit files in "
            "the current directory only. After running the test, answer exactly "
            "one line: tests=<passed|failed>."
        ),
        sandbox="workspace-write",
        workspace="python_bug",
    ),
    Task(
        "r229-shell-fix",
        "edit-test",
        (
            "Run `bash check.sh`, fix the script so it exits 0, then answer "
            "exactly one line: check=<passed|failed>."
        ),
        sandbox="workspace-write",
        workspace="shell_fix",
    ),
    Task(
        "r229-json-write",
        "write",
        (
            "Create result.json with exactly {\"status\":\"ok\",\"run\":\"r229\"}. "
            "You may edit files in the current directory only. Answer exactly "
            "one line: result_json=<created|missing>."
        ),
        sandbox="workspace-write",
        workspace="json_write",
    ),
    Task(
        "r229-typo-edit",
        "edit",
        (
            "Fix the typo in README.md by changing 'flamgraph' to 'flamegraph'. "
            "You may edit files in the current directory only. Answer exactly "
            "one line: typo_fixed=<yes|no>."
        ),
        sandbox="workspace-write",
        workspace="typo_repo",
    ),
]


def prepare_work_dir(work_dir: Path) -> None:
    resolved = work_dir.resolve()
    default_resolved = DEFAULT_WORK.resolve()
    if work_dir.exists():
        marker = work_dir / WORK_MARKER
        if resolved != default_resolved and not marker.exists() and any(work_dir.iterdir()):
            raise SystemExit(
                f"refusing to remove non-empty unmarked work dir: {work_dir}. "
                f"Use an empty directory or one containing {WORK_MARKER}."
            )
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / WORK_MARKER).write_text(
        "owned by docs/visexp/r229_exact_lineage_replication.py\n",
        encoding="utf-8",
    )


def replication_gate(aggregate_result: dict[str, Any], task_count: int) -> bool:
    target_statuses = aggregate_result.get("target_statuses") or {}
    return (
        aggregate_result.get("tasks") == task_count
        and target_statuses.get("completed", 0) == task_count
        and aggregate_result.get("negative_control_tasks_observed", 0) == task_count
        and aggregate_result.get("negative_effect_events_observed", 0) > 0
        and aggregate_result.get("negative_joined_effect_events", 0) == 0
        and aggregate_result.get("precision_pct", 0.0) >= 98.0
        and aggregate_result.get("recall_pct", 0.0) >= 95.0
        and aggregate_result.get("in_scope_effect_events", 0) > 0
    )


def workspace_distribution(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(row.get("workspace") or "unknown") for row in rows))


def category_distribution(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(row.get("category") or "unknown") for row in rows))


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    agg = result["aggregate"]
    broad_statuses = Counter(
        str((row.get("lineage") or {}).get("status") or "unknown") for row in result["tasks"]
    )
    lines = [
        "# R229 Exact Lineage Replication",
        "",
        f"Last updated: {date.today().isoformat()}",
        "Stage at update: execute/analyze",
        "Source/command: `python3 docs/visexp/r229_exact_lineage_replication.py --out docs/visexp/out`",
        f"Completeness: {result['status']}",
        "",
        "R229 reruns the R114 record/export/lineage oracle over a controlled",
        "multi-workspace suite. It checks whether prompt/tool/process/effect",
        "lineage remains clean across repo read, edit/test, shell fix, JSON write,",
        "and typo-edit workloads while wrapper negative controls run concurrently.",
        "",
        "Raw SQLite DBs, exported snapshots, and per-event lineage CSVs stay in",
        "the local work dir and are not committed.",
        "",
        "## Aggregate",
        "",
        f"- Tasks: {agg['tasks']} ({agg['task_statuses']})",
        f"- Workspaces: {result['workspace_distribution']}",
        f"- Categories: {result['category_distribution']}",
        f"- Record status: {agg.get('record_statuses', {})}; target status: {agg.get('target_statuses', {})}; lineage status: {agg.get('lineage_statuses', {})}",
        f"- Effects: joined={agg['joined_effect_events']} / {agg['effect_events']} = {agg['raw_join_pct']}%",
        f"- Scope accounting: in_scope={agg.get('in_scope_effect_events', 0)}, out_of_scope={agg.get('out_of_scope_effect_events', 0)}",
        f"- Scoped oracle: true_positives={agg.get('true_positives', 0)}, false_positives={agg.get('false_positives', 0)}, false_negatives={agg.get('false_negatives', 0)}",
        f"- Precision/recall: precision={agg['precision_pct']}%, recall={agg['recall_pct']}%",
        f"- Negative controls: tasks_observed={agg.get('negative_control_tasks_observed', 0)}/{agg['tasks']}, observed={agg['negative_effect_events_observed']}, joined={agg['negative_joined_effect_events']}",
        f"- Broad smoke status: {dict(broad_statuses)}",
        f"- Join methods: {agg['join_methods']}",
        "",
        "The raw join rate is intentionally lower than scoped precision: wrapper,",
        "out-of-scope, and negative-control effects should remain orphan instead of",
        "being attributed to the target agent task. R229 therefore passes the scoped",
        "precision/negative-control oracle even though the broad lineage smoke treats",
        "those intentional orphans as failures.",
        "",
        "## Per Task",
        "",
        "| Task | Cat | Workspace | Target | Lineage | Effects | Joined | In scope | Out scope | Neg observed | Neg joined | Answer |",
        "|------|-----|-----------|--------|---------|--------:|-------:|---------:|----------:|-------------:|-----------:|--------|",
    ]
    for row in result["tasks"]:
        lineage = row.get("lineage") or {}
        pr = row.get("precision_recall") or {}
        answer = str(row.get("answer") or "").replace("|", "\\|").replace("\n", " ")[:100]
        lines.append(
            f"| `{row['task_id']}` | {row.get('category')} | {row.get('workspace')} | "
            f"{row.get('target_status')} | {row.get('lineage_status')} | "
            f"{int(lineage.get('effect_events') or 0)} | {int(lineage.get('joined_effect_events') or 0)} | "
            f"{pr.get('in_scope_effect_events', 0)} | {pr.get('out_of_scope_effect_events', 0)} | "
            f"{pr.get('negative_effect_events_observed', 0)} | {pr.get('negative_joined_effect_events', 0)} | "
            f"{answer} |"
        )
    lines.extend(["", "## Claim Boundary", "", result["boundary"]])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    selected = R229_TASKS[: args.task_limit]
    if args.print_manifest:
        payload = {"schema_version": 1, "run_id": "R229", "tasks": manifest_rows(selected)}
        print(json.dumps(payload, indent=2))
        return payload

    work_dir = Path(args.work_dir)
    prepare_work_dir(work_dir)
    agentsight_bin = Path(resolve_executable(args.agentsight_bin, "agentsight"))
    codex_bin = resolve_executable(args.codex_bin, "codex")
    rows = [
        record_task(task, agentsight_bin, codex_bin, work_dir, args.timeout, args.negative_mode)
        for task in selected
    ]
    aggregate_result = aggregate(rows)
    passed = replication_gate(aggregate_result, len(rows))
    status = "ok" if passed else "partial"
    boundary = (
        "R229 strengthens C4/RQ3 for the fixed command-mode scope by replicating "
        "the R114 exact-lineage oracle across multiple controlled workspaces and "
        "workload categories with zero negative-control joins. It does not prove "
        "full-history exact lineage, arbitrary prompt compliance, cross-repository "
        "generality, C5 developer utility, or C6 tag adequacy."
        if passed
        else "R229 is partial: controlled multi-workspace exact-lineage replication did not meet all precision/recall or negative-control gates."
    )
    result = {
        "schema_version": 1,
        "run_id": "R229",
        "status": status,
        "scope": "controlled_multi_workspace_codex_record_lineage_replication",
        "artifact_boundary": (
            "Raw SQLite DBs and exported snapshots stay in the local work dir; "
            "committed artifacts contain scrubbed task-level summaries only."
        ),
        "generated_at": date.today().isoformat(),
        "work_dir": str(work_dir),
        "agentsight_bin": rel(agentsight_bin),
        "codex_bin": str(codex_bin),
        "task_limit": args.task_limit,
        "negative_mode": args.negative_mode,
        "manifest": manifest_rows(selected),
        "workspace_distribution": workspace_distribution(rows),
        "category_distribution": category_distribution(rows),
        "aggregate": aggregate_result,
        "tasks": rows,
        "boundary": boundary,
    }
    result = scrub_artifact_value(result)
    json_path = out_dir / "exact-lineage-replication-r229.json"
    md_path = out_dir / "exact-lineage-replication-r229.md"
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_markdown(md_path, result)
    print(json.dumps({"status": result["status"], "aggregate": result["aggregate"]}, indent=2))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--work-dir", default=str(DEFAULT_WORK))
    parser.add_argument("--agentsight-bin", default=str(REPO_ROOT / "collector/target/debug/agentsight"))
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--task-limit", type=int, default=len(R229_TASKS))
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--negative-mode", choices=("wrapper", "external"), default="wrapper")
    parser.add_argument("--print-manifest", action="store_true")
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
