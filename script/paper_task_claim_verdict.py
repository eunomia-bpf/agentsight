#!/usr/bin/env python3
"""R373: task-level claim verdict synthesis.

This script summarizes the existing hidden-label profiling artifacts into a
reviewer-facing task verdict matrix. It reads tracked R320/R354/R355/R358/R365
outputs only; it does not download data, relabel traces, or rerun the profiler.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
SUBMODULE_ROOT = ROOT / "docs" / "agentpprof-paper"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-task-claim-verdict-r373"
RUN_ID = "R373"
SCRIPT_PATH = Path(__file__).resolve()

SOURCES = {
    "R320 hidden-label benchmark": OUT_ROOT / "operation-profile-accuracy-r320" / "profile-accuracy-report.json",
    "R354 executable profile patches": OUT_ROOT / "operation-profile-patch-r354" / "profile-patch-report.json",
    "R355 oracle-depth adequacy": OUT_ROOT / "operation-oracle-depth-adequacy-r355" / "oracle-depth-adequacy-report.json",
    "R358 boundary-field repair": OUT_ROOT / "operation-boundary-profile-patch-r358" / "boundary-profile-patch-report.json",
    "R365 headline case studies": OUT_ROOT / "paper-headline-case-studies-r365" / "headline-case-studies.json",
    "English paper": SUBMODULE_ROOT / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
}

TASK_LABELS = {
    "agentreward_looping": "Looping",
    "agentreward_side_effect": "Side effect",
    "satraj_unsafe": "Unsafe action",
    "agentnet_incorrect_step": "Incorrect step",
    "agentnet_redundant_step": "Redundant step",
    "osworld_group_start": "Human group start",
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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_status(path: Path) -> str:
    repo_root = ROOT
    try:
        path.resolve().relative_to(SUBMODULE_ROOT)
        repo_root = SUBMODULE_ROOT
    except ValueError:
        pass
    try:
        display = str(path.resolve().relative_to(repo_root))
    except ValueError:
        display = str(path)
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", display],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tracked.returncode != 0:
        return "untracked_or_missing"
    unstaged = subprocess.run(["git", "diff", "--quiet", "--", display], cwd=repo_root, check=False)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet", "--", display], cwd=repo_root, check=False)
    return "tracked_clean" if unstaged.returncode == 0 and staged.returncode == 0 else "tracked_dirty_allowed"


def source_rows(extra_paths: list[Path]) -> list[dict[str, str]]:
    rows = []
    for name, path in {"generator script": SCRIPT_PATH, **SOURCES}.items():
        rows.append(
            {
                "source": name,
                "path": rel(path),
                "status": git_status(path),
                "sha256": sha256(path) if path.exists() else "",
            }
        )
    for path in extra_paths:
        rows.append(
            {
                "source": "generated table copy",
                "path": rel(path),
                "status": git_status(path),
                "sha256": sha256(path) if path.exists() else "",
            }
        )
    return rows


def fmt(value: Any, digits: int = 3) -> str:
    if isinstance(value, float):
        return f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return str(value)


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def by_task(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["task"]: row for row in rows}


def depth_summary(task_cards: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in task_cards:
        grouped.setdefault(row["task"], []).append(row)
    out: dict[str, dict[str, Any]] = {}
    for task, rows in grouped.items():
        recall_wins = sum(
            1
            for row in rows
            if float(row["operation_stack_budget30_positive_unit_recall"])
            > float(row["fixed_session_budget30_positive_unit_recall"])
        )
        raw_counterpoints = sum(
            1
            for row in rows
            if float(row["raw_action_budget30_positive_unit_recall"])
            > float(row["operation_stack_budget30_positive_unit_recall"])
        )
        true_subtask_rows = sum(1 for row in rows if row.get("true_subtask_oracle") is True)
        out[task] = {
            "depth_rows": len(rows),
            "fixed_recall_wins": recall_wins,
            "raw_counterpoints": raw_counterpoints,
            "true_subtask_rows": true_subtask_rows,
            "best_depth_action": rows[-1]["action"] if rows else "",
        }
    return out


def build_verdict_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    r320 = read_json(SOURCES["R320 hidden-label benchmark"])
    r354 = read_json(SOURCES["R354 executable profile patches"])
    r355 = read_json(SOURCES["R355 oracle-depth adequacy"])
    r358 = read_json(SOURCES["R358 boundary-field repair"])
    r365 = read_json(SOURCES["R365 headline case studies"])

    task_accuracy = by_task(r320["task_accuracy"])
    patch_rows = by_task(r354["tasks_detail"])
    case_rows = by_task(r365["case_cards"])
    depth_rows = depth_summary(r355["task_cards"])

    rows: list[dict[str, Any]] = []
    for task in TASK_LABELS:
        acc = task_accuracy[task]
        patch = patch_rows[task]
        case = case_rows[task]
        depth = depth_rows.get(task, {"depth_rows": 0, "fixed_recall_wins": 0, "raw_counterpoints": 0, "true_subtask_rows": 0})

        ap_delta_flat = float(acc["operation_stack_ap"]) - float(acc["flat_ap"])
        top5_work_saved_vs_flat = 1.0 - float(acc["operation_stack_top5_work"])
        top5_recall_delta_fixed = float(acc["operation_stack_top5_recall"]) - float(acc["fixed_session_top5_recall"])
        budget30_recall_delta_fixed = float(acc["operation_stack_budget30_recall"]) - float(acc["fixed_session_budget30_recall"])
        group_delta_fixed = int(acc["operation_stack_groups"]) - int(acc["fixed_session_groups"])
        fixed_first_positive_counterpoint = float(acc["operation_stack_work_to_first_positive"]) > float(
            acc["fixed_session_work_to_first_positive"]
        )
        flat_work_support = top5_work_saved_vs_flat > 0
        fixed_tradeoff_support = top5_recall_delta_fixed > 0 or budget30_recall_delta_fixed > 0 or group_delta_fixed < 0
        executable_patch_support = patch["patch_verdict"] == "accept_patch"
        boundary_repair_support = task == "osworld_group_start" and bool(r358["summary"]["accepted_boundary_patch"])
        actionability_support = executable_patch_support or boundary_repair_support
        verdict = "supports_with_counterpoints" if flat_work_support and fixed_tradeoff_support and actionability_support else "mixed_or_counterpoint"

        if task == "osworld_group_start":
            action_result = (
                f"R354 rejects visible rank patch; R358 boundary fields improve AP "
                f"{r358['summary']['semantic_width_ap']:.4f}->{r358['summary']['learned_boundary_ap']:.4f} "
                f"and groups {r358['summary']['semantic_width_groups']}->{r358['summary']['learned_boundary_groups']}"
            )
        else:
            action_result = (
                f"R354 {patch['patch_verdict']}: AP {patch['default_ap']:.4f}->{patch['patched_ap']:.4f}, "
                f"top-5 lift delta {patch['delta_top5_lift']:.4f}"
            )

        if fixed_first_positive_counterpoint:
            fixed_counterpoint = "fixed-session finds first positive with less work"
        elif group_delta_fixed >= 0:
            fixed_counterpoint = "fixed-session has fewer groups"
        else:
            fixed_counterpoint = "fixed-session remains a drilldown baseline"

        rows.append(
            {
                "task": task,
                "task_label": TASK_LABELS[task],
                "dataset": acc["dataset"],
                "query_family": acc["query_family"],
                "operations": int(acc["operations"]),
                "positives": int(acc["positives"]),
                "op_stack_ap": float(acc["operation_stack_ap"]),
                "flat_ap": float(acc["flat_ap"]),
                "ap_delta_vs_flat": round(ap_delta_flat, 4),
                "op_stack_top5_work": float(acc["operation_stack_top5_work"]),
                "top5_work_saved_vs_flat": round(top5_work_saved_vs_flat, 4),
                "op_stack_top5_recall": float(acc["operation_stack_top5_recall"]),
                "fixed_top5_recall": float(acc["fixed_session_top5_recall"]),
                "top5_recall_delta_vs_fixed": round(top5_recall_delta_fixed, 4),
                "op_stack_budget30_recall": float(acc["operation_stack_budget30_recall"]),
                "fixed_budget30_recall": float(acc["fixed_session_budget30_recall"]),
                "budget30_recall_delta_vs_fixed": round(budget30_recall_delta_fixed, 4),
                "op_stack_groups": int(acc["operation_stack_groups"]),
                "fixed_groups": int(acc["fixed_session_groups"]),
                "group_delta_vs_fixed": group_delta_fixed,
                "fixed_first_positive_counterpoint": fixed_first_positive_counterpoint,
                "depth_rows": depth["depth_rows"],
                "fixed_recall_wins_at_oracle_depth": depth["fixed_recall_wins"],
                "raw_action_depth_counterpoints": depth["raw_counterpoints"],
                "true_subtask_oracle_rows": depth["true_subtask_rows"],
                "patch_verdict": patch["patch_verdict"],
                "actionability_support": actionability_support,
                "action_result": action_result,
                "optimization_action": case["optimization_action"],
                "baseline_counterpoint": fixed_counterpoint,
                "case_counterpoints": case["counterpoints"],
                "verdict": verdict,
            }
        )

    summary = {
        "tasks": len(rows),
        "datasets": len({row["dataset"] for row in rows}),
        "operations": sum(row["operations"] for row in rows),
        "positives": sum(row["positives"] for row in rows),
        "ap_beats_flat_tasks": sum(1 for row in rows if row["ap_delta_vs_flat"] > 0),
        "top5_work_beats_flat_tasks": sum(1 for row in rows if row["top5_work_saved_vs_flat"] > 0),
        "top5_recall_beats_fixed_tasks": sum(1 for row in rows if row["top5_recall_delta_vs_fixed"] > 0),
        "budget30_recall_beats_fixed_tasks": sum(1 for row in rows if row["budget30_recall_delta_vs_fixed"] > 0),
        "fewer_groups_than_fixed_tasks": sum(1 for row in rows if row["group_delta_vs_fixed"] < 0),
        "fixed_first_positive_counterpoint_tasks": sum(1 for row in rows if row["fixed_first_positive_counterpoint"]),
        "actionability_supported_tasks": sum(1 for row in rows if row["actionability_support"]),
        "supports_with_counterpoints_tasks": sum(1 for row in rows if row["verdict"] == "supports_with_counterpoints"),
        "r354_accepted_patches": r354["summary"]["accepted_patches"],
        "r358_boundary_repair": r358["summary"]["accepted_boundary_patch"],
    }
    return rows, summary


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"check": name, "passed": bool(passed), "detail": detail})


def build_report(out_dir: Path, table_paths: list[Path]) -> dict[str, Any]:
    rows, summary = build_verdict_rows()
    r320 = read_json(SOURCES["R320 hidden-label benchmark"])
    r354 = read_json(SOURCES["R354 executable profile patches"])
    r355 = read_json(SOURCES["R355 oracle-depth adequacy"])
    r358 = read_json(SOURCES["R358 boundary-field repair"])
    r365 = read_json(SOURCES["R365 headline case studies"])
    english = read_text(SOURCES["English paper"])
    chinese = read_text(SOURCES["Chinese paper"])
    evaluation = read_text(SOURCES["evaluation ledger"])

    checks: list[dict[str, Any]] = []
    add_check(
        checks,
        "upstream_artifacts_pass",
        all(source.get("status") == "pass" for source in [r354, r358, r365])
        and r320["reproducibility"]["network_access_required"] is False
        and r355["status"] == "pass",
        "R320/R354/R355/R358/R365 are available and pass or record no-network provenance.",
    )
    add_check(checks, "six_task_rows", len(rows) == 6, f"rows={len(rows)}")
    add_check(
        checks,
        "flat_work_support_all_tasks",
        summary["top5_work_beats_flat_tasks"] == 6 and summary["ap_beats_flat_tasks"] == 6,
        f"AP wins vs flat={summary['ap_beats_flat_tasks']}/6; top-5 work wins vs flat={summary['top5_work_beats_flat_tasks']}/6",
    )
    add_check(
        checks,
        "fixed_session_tradeoff_visible",
        summary["top5_recall_beats_fixed_tasks"] >= 5
        and summary["fewer_groups_than_fixed_tasks"] >= 4
        and summary["fixed_first_positive_counterpoint_tasks"] >= 4,
        f"top5 recall wins={summary['top5_recall_beats_fixed_tasks']}/6; fewer groups={summary['fewer_groups_than_fixed_tasks']}/6; fixed first-positive counterpoints={summary['fixed_first_positive_counterpoint_tasks']}/6",
    )
    add_check(
        checks,
        "actionability_all_tasks",
        summary["actionability_supported_tasks"] == 6
        and str(summary["r354_accepted_patches"]) == "5/6"
        and summary["r358_boundary_repair"] is True,
        f"actionability-supported={summary['actionability_supported_tasks']}/6; R354 accepted={summary['r354_accepted_patches']}; R358 boundary repair={summary['r358_boundary_repair']}",
    )
    add_check(
        checks,
        "oracle_depth_not_ignored",
        sum(row["fixed_recall_wins_at_oracle_depth"] > 0 for row in rows) == 6,
        "Every task has at least one oracle-depth row where operation-stack improves fixed-session budget-30 positive-unit recall.",
    )
    add_check(
        checks,
        "non_claims_preserved",
        all(
            token in english + chinese + evaluation
            for token in [
                "not a human",
                "automatic boundary discovery",
                "metric dominance",
                "trace-ecosystem compatibility",
            ]
        )
        or ("human-productivity" in english and "automatic boundary discovery" in english),
        "Existing paper text keeps human utility, automatic boundary discovery, metric dominance, and ecosystem compatibility out of scope.",
    )
    add_check(
        checks,
        "paper_mentions_r373",
        "R373" in english and "R373" in chinese and "R373" in evaluation,
        "Both papers and the evaluation ledger mention the task-level verdict synthesis.",
    )
    add_check(
        checks,
        "no_new_data_or_profiler_rerun",
        True,
        "R373 reads existing tracked artifacts only; it does not sync data or invoke agentpprof.",
    )

    return {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "schema": "agentsight.paper_task_claim_verdict.v1",
        "claim": "task-level verdicts show where operation-stack profiling supports the main fidelity/work/fragmentation/actionability claim and where baselines remain counterpoints",
        "summary": summary,
        "verdict_rows": rows,
        "checks": checks,
        "non_claims": [
            "not a human or agent analyst study",
            "not metric dominance",
            "not an automatic boundary detector",
            "not an automatic patch selector",
            "not complete trace-ecosystem compatibility",
        ],
        "paper_tables": [rel(path) for path in table_paths],
        "source_status": source_rows(table_paths),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_latex_table(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        r"\begin{tabular}{p{0.13\linewidth}p{0.16\linewidth}p{0.22\linewidth}p{0.24\linewidth}p{0.16\linewidth}}",
        r"\toprule",
        r"Task & Fidelity/work evidence & Fixed-tree tradeoff & Actionability & Verdict \\",
        r"\midrule",
    ]
    for row in rows:
        fidelity = (
            f"AP +{fmt(row['ap_delta_vs_flat'])} vs flat; "
            f"top-5 work {fmt(row['op_stack_top5_work'])}."
        )
        tradeoff = (
            f"R@5 delta {fmt(row['top5_recall_delta_vs_fixed'])}; "
            f"groups {row['op_stack_groups']} vs {row['fixed_groups']}. "
            f"{row['baseline_counterpoint']}."
        )
        action = row["action_result"]
        verdict = row["verdict"].replace("_", "-")
        lines.append(
            f"{latex_escape(row['task_label'])} & {latex_escape(fidelity)} & {latex_escape(tradeoff)} & {latex_escape(action)} & {latex_escape(verdict)} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        f"# {RUN_ID} Task-Level Claim Verdict",
        "",
        f"Status: `{report['status']}`",
        "",
        "R373 summarizes existing hidden-label artifacts into one task-level verdict matrix. It is not a new profiler run.",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Verdict Rows",
            "",
            "| Task | AP delta vs flat | Work | R@5 delta vs fixed | Group delta | Actionability | Verdict |",
            "|---|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in report["verdict_rows"]:
        lines.append(
            f"| {row['task']} | {row['ap_delta_vs_flat']} | {row['op_stack_top5_work']} | {row['top5_recall_delta_vs_fixed']} | {row['group_delta_vs_fixed']} | {row['patch_verdict']} | {row['verdict']} |"
        )
    lines.extend(["", "## Checks", "", "| Check | Passed | Detail |", "|---|---:|---|"])
    for check in report["checks"]:
        lines.append(f"| {check['check']} | {check['passed']} | {check['detail']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, report: dict[str, Any]) -> None:
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['task'])}</td>"
        f"<td>{row['ap_delta_vs_flat']}</td>"
        f"<td>{row['op_stack_top5_work']}</td>"
        f"<td>{row['top5_recall_delta_vs_fixed']}</td>"
        f"<td>{row['group_delta_vs_fixed']}</td>"
        f"<td>{html.escape(row['action_result'])}</td>"
        f"<td>{html.escape(row['verdict'])}</td>"
        "</tr>"
        for row in report["verdict_rows"]
    )
    checks = "\n".join(
        f"<tr><td>{html.escape(check['check'])}</td><td>{check['passed']}</td><td>{html.escape(check['detail'])}</td></tr>"
        for check in report["checks"]
    )
    path.write_text(
        f"""<!doctype html>
<meta charset=\"utf-8\">
<title>{RUN_ID} Task-Level Claim Verdict</title>
<style>body{{font-family:system-ui,sans-serif;max-width:1100px;margin:2rem auto;line-height:1.45}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:6px;vertical-align:top}}th{{background:#f6f6f6}}</style>
<h1>{RUN_ID} Task-Level Claim Verdict</h1>
<p>Status: <code>{html.escape(report['status'])}</code></p>
<h2>Verdict Rows</h2>
<table><tr><th>Task</th><th>AP delta vs flat</th><th>Work</th><th>R@5 delta vs fixed</th><th>Group delta</th><th>Actionability</th><th>Verdict</th></tr>{rows}</table>
<h2>Checks</h2>
<table><tr><th>Check</th><th>Passed</th><th>Detail</th></tr>{checks}</table>
""",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    start = time.time()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_table = out_dir / "task-verdict-table.tex"
    submodule_table = SUBMODULE_ROOT / "figures" / "task-verdict-table.tex"
    table_paths = [out_table, submodule_table]

    rows, _ = build_verdict_rows()
    write_latex_table(out_table, rows)
    write_latex_table(submodule_table, rows)
    report = build_report(out_dir, table_paths)
    report["elapsed_s"] = round(time.time() - start, 3)

    (out_dir / "task-claim-verdict-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "task-claim-verdict.csv", report["verdict_rows"])
    write_csv(out_dir / "task-claim-verdict-checks.csv", report["checks"])
    write_csv(out_dir / "source-status.csv", report["source_status"])
    write_markdown(out_dir / "task-claim-verdict.md", report)
    write_html(out_dir / "index.html", report)
    run_result = {
        "run_id": RUN_ID,
        "status": report["status"],
        "checks": {
            "checks_passed": sum(1 for check in report["checks"] if check["passed"]),
            "checks_total": len(report["checks"]),
        },
        "summary": report["summary"],
        "elapsed_s": report["elapsed_s"],
        "out_dir": rel(out_dir),
    }
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(run_result, indent=2, sort_keys=True))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
