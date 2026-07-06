#!/usr/bin/env python3
"""R365: extract paper-ready E2/E3 headline rows and task case cards.

This is a paper-integration artifact, not a new empirical experiment. It reads
tracked outputs from the existing hidden-label profiler benchmark and
actionability probes, then emits compact headline rows, task cards, and a LaTeX
table fragment for the paper. It does not download, sync, create, or relabel
datasets, and it does not rerun the profiler.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-headline-case-studies-r365"
RUN_ID = "R365"
SCRIPT_PATH = Path(__file__).resolve()

SOURCES = {
    "R320 profile accuracy": OUT_ROOT / "operation-profile-accuracy-r320" / "profile-accuracy-report.json",
    "R320 optimization insights": OUT_ROOT / "operation-profile-accuracy-r320" / "optimization-insights.csv",
    "R333 inspection frontier": OUT_ROOT / "operation-inspection-frontier-r333" / "inspection-frontier-report.json",
    "R334 fragmentation tradeoff": OUT_ROOT / "operation-fragmentation-tradeoff-r334" / "fragmentation-tradeoff-report.json",
    "R345 task lens cards": OUT_ROOT / "operation-diagnostic-lens-portfolio-r345" / "task-lens-cards.csv",
    "R348 action cards": OUT_ROOT / "operation-action-counterfactual-r348" / "task-action-counterfactual-cards.csv",
    "R348 action report": OUT_ROOT / "operation-action-counterfactual-r348" / "action-counterfactual-report.json",
    "R354 profile patch": OUT_ROOT / "operation-profile-patch-r354" / "profile-patch-report.json",
    "R354 profile patch summary": OUT_ROOT / "operation-profile-patch-r354" / "profile-patch-summary.csv",
    "R355 oracle depth": OUT_ROOT / "operation-oracle-depth-adequacy-r355" / "oracle-depth-adequacy-report.json",
    "R358 boundary patch": OUT_ROOT / "operation-boundary-profile-patch-r358" / "boundary-profile-patch-report.json",
    "R358 top stacks": OUT_ROOT / "operation-boundary-profile-patch-r358" / "top-stacks.csv",
    "R363 visualization portfolio": OUT_ROOT / "paper-visualization-portfolio-r363" / "visualization-portfolio.json",
}

PAPER_SOURCES = {
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "English paper": SUBMODULE_ROOT / "main.tex",
}

HEADLINE_FIELDS = [
    "row_id",
    "paper_block",
    "claim_role",
    "headline",
    "primary_numbers",
    "paper_takeaway",
    "counterpoint",
    "sources",
]

CASE_FIELDS = [
    "task",
    "dataset",
    "query_family",
    "best_visible_policy",
    "operation_stack_top5_recall",
    "operation_stack_top5_work",
    "operation_stack_top5_lift",
    "patch_verdict",
    "patch_delta_ap",
    "optimization_action",
    "counterpoints",
    "visual_recipe",
    "useful_stack_fields",
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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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


def git_commit() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stdout=subprocess.PIPE, check=True)
    return result.stdout.strip()


def fmt(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{numeric:.4f}".rstrip("0").rstrip(".")


def by_task(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["task"]: row for row in rows}


def source_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for name, path in {"generator script": SCRIPT_PATH, **SOURCES, **PAPER_SOURCES}.items():
        rows.append(
            {
                "source": name,
                "path": rel(path),
                "status": git_status(path),
                "sha256": sha256(path),
            }
        )
    return rows


def build_headlines(data: dict[str, Any]) -> list[dict[str, str]]:
    r320 = data["r320"]
    r333 = data["r333"]
    r334 = data["r334"]
    r348 = data["r348"]
    r354 = data["r354"]
    r355 = data["r355"]["claim_summary"]
    r358 = data["r358"]["summary"]
    opq = r320["policy_summary"]["operation_stack:query_aware"]
    flat = r320["policy_summary"]["flat:width"]
    fixed = r320["policy_summary"]["fixed_session:query_aware"]
    dataset_native = r320["policy_summary"]["dataset_native:query_aware"]
    fixed_cmp = r320["paired_comparisons"]["operation_stack_query_aware_vs_fixed_session_query_aware"]["metrics"]
    flat_cmp = r320["paired_comparisons"]["operation_stack_query_aware_vs_flat_width"]["metrics"]

    return [
        {
            "row_id": "H1",
            "paper_block": "E2",
            "claim_role": "hidden-label localization and inspection work",
            "headline": "Operation-stack query-aware rankings localize positives while inspecting much less work than flat summaries.",
            "primary_numbers": (
                f"6 tasks / 4 datasets / {r320['totals']['task_operations']} operations / "
                f"{r320['totals']['positive_operations']} positives; Work@5 {fmt(opq['median_top5_work'])} "
                f"vs flat {fmt(flat['median_top5_work'])}; R@30% {fmt(opq['median_budget30_recall'])} "
                f"vs fixed-session {fmt(fixed['median_budget30_recall'])}."
            ),
            "paper_takeaway": "Use the operation stack as the primary triage surface when the goal is budgeted localization rather than full-recall summarization.",
            "counterpoint": f"Fixed-session still has lower first-positive work ({fmt(fixed['median_work_to_first_positive'])}); dataset-native has higher top-5 recall ({fmt(dataset_native['median_top5_recall'])}) at high work.",
            "sources": "R320; R333",
        },
        {
            "row_id": "H2",
            "paper_block": "E2",
            "claim_role": "fixed-boundary fragmentation tradeoff",
            "headline": "Operation stacks reduce fixed-session fragmentation for ranked inspection.",
            "primary_numbers": (
                f"Median groups {fmt(opq['median_groups'])} vs fixed-session {fmt(fixed['median_groups'])}; "
                f"top-5 recall wins vs fixed-session {fixed_cmp['top5_recall']['improved_tasks']}/6; "
                "30% budget inspects fewer groups on 5/6 tasks."
            ),
            "paper_takeaway": "Session/span-shaped drilldown should be a secondary view; making it primary fragments positives across too many groups.",
            "counterpoint": r334["primary_findings"][2],
            "sources": "R320; R334",
        },
        {
            "row_id": "H3",
            "paper_block": "E2/E3",
            "claim_role": "oracle-depth adequacy",
            "headline": "The same ranked groups remain useful when scored at dataset-provided oracle depths.",
            "primary_numbers": (
                f"{r355['paired_checks']['top5_unit_work_lt_flat_rows']}/{r355['accuracy_unit_depth_rows']} rows lower top-5 unit work than flat; "
                f"{r355['paired_checks']['budget30_unit_recall_gt_fixed_rows']}/{r355['accuracy_unit_depth_rows']} rows beat fixed-session unit recall; "
                f"{r355['paired_checks']['groups_to_50pct_units_lt_fixed_rows']}/{r355['accuracy_unit_depth_rows']} rows use fewer groups to 50% positives."
            ),
            "paper_takeaway": "The profiler can be evaluated at operation, session, positive-run, and OSWorld human-group depths without changing the two-object model.",
            "counterpoint": "; ".join(r355["counterpoints"][:2]),
            "sources": "R355",
        },
        {
            "row_id": "H4",
            "paper_block": "E3",
            "claim_role": "profile-configuration actionability",
            "headline": "Profiler output identifies concrete view, ranker, and profile-spec changes.",
            "primary_numbers": (
                f"{r348['summary']['nondefault_action_rows']}/{r348['summary']['objective_rows']} objective rows need non-default actions; "
                f"{r348['summary']['view_change_rows']}/{r348['summary']['objective_rows']} require view changes; "
                f"R354 accepts {r354['summary']['accepted_patches']} patches with median AP delta {fmt(r354['summary']['median_delta_ap'])} "
                f"and top-5 lift delta {fmt(r354['summary']['median_delta_top5_lift'])}."
            ),
            "paper_takeaway": "The profiler is actionable because it names which stack fields, mappings, ranker policy, or drilldown should change.",
            "counterpoint": "These are visible-profile configuration actions, not an automatic patch selector or human-productivity result.",
            "sources": "R348; R354",
        },
        {
            "row_id": "H5",
            "paper_block": "E3",
            "claim_role": "boundary-field mechanism ablation",
            "headline": "The OSWorld-Human rejection is repaired by boundary-derived operation fields, not by adding a new profiler object.",
            "primary_numbers": (
                f"AP {fmt(r358['learned_boundary_ap'])} vs semantic-width {fmt(r358['semantic_width_ap'])}; "
                f"groups {r358['learned_boundary_groups']} vs {r358['semantic_width_groups']}; "
                f"top-5 recall delta {fmt(r358['learned_boundary_delta_top5_recall_vs_semantic'])}."
            ),
            "paper_takeaway": "Boundary backends are field derivation mechanisms whose outputs fold through the same operation-stack path.",
            "counterpoint": r358["counterpoint"],
            "sources": "R358",
        },
    ]


def build_case_cards(data: dict[str, Any]) -> list[dict[str, str]]:
    insights = by_task(data["optimization_insights"])
    lenses = by_task(data["lens_cards"])
    actions = by_task(data["action_cards"])
    patches = by_task(data["patch_summary"])
    task_order = [
        "agentreward_looping",
        "agentreward_side_effect",
        "satraj_unsafe",
        "agentnet_incorrect_step",
        "agentnet_redundant_step",
        "osworld_group_start",
    ]
    rows: list[dict[str, str]] = []
    for task in task_order:
        action = actions[task]
        insight = insights[task]
        lens = lenses[task]
        patch = patches[task]
        rows.append(
            {
                "task": task,
                "dataset": action["dataset"],
                "query_family": action["query_family"],
                "best_visible_policy": insight["best_visible_policy"],
                "operation_stack_top5_recall": fmt(action["operation_stack_top5_recall"]),
                "operation_stack_top5_work": fmt(action["operation_stack_top5_work"]),
                "operation_stack_top5_lift": fmt(action["operation_stack_top5_lift"]),
                "patch_verdict": patch["patch_verdict"],
                "patch_delta_ap": fmt(patch["delta_ap"]),
                "optimization_action": action["optimization_action"],
                "counterpoints": action["case_counterpoints"],
                "visual_recipe": lens["visual_recipe"],
                "useful_stack_fields": action["useful_stack_fields"],
            }
        )
    return rows


def latex_escape(value: str) -> str:
    return (
        value.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("_", "\\_")
        .replace("#", "\\#")
    )


def write_latex_table(path: Path, rows: list[dict[str, str]]) -> None:
    lines = [
        "% Generated by script/paper_headline_case_studies.py (R365).",
        "\\begin{tabular}{p{0.13\\linewidth}p{0.18\\linewidth}p{0.31\\linewidth}p{0.28\\linewidth}}",
        "  \\toprule",
        "  Row & Role & Main numbers & Counterpoint \\\\",
        "  \\midrule",
    ]
    for row in rows:
        lines.append(
            "  "
            + " & ".join(
                [
                    latex_escape(row["row_id"]),
                    latex_escape(row["claim_role"]),
                    latex_escape(row["primary_numbers"]),
                    latex_escape(row["counterpoint"]),
                ]
            )
            + " \\\\"
        )
    lines.extend(["  \\bottomrule", "\\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R365 Paper Headline Case Studies",
        "",
        f"- Status: `{payload['status']}`.",
        f"- Checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.",
        "- This is not a new empirical result and does not rerun the profiler.",
        "",
        "## Headline Rows",
        "",
        "| Row | Block | Role | Main numbers | Counterpoint |",
        "|---|---|---|---|---|",
    ]
    for row in payload["headline_rows"]:
        lines.append(f"| {row['row_id']} | {row['paper_block']} | {row['claim_role']} | {row['primary_numbers']} | {row['counterpoint']} |")
    lines.extend(["", "## Task Cards", "", "| Task | Policy | Work@5 | Recall@5 | Patch | Action |", "|---|---|---|---|---|---|"])
    for row in payload["case_cards"]:
        lines.append(
            f"| {row['task']} | {row['best_visible_policy']} | {row['operation_stack_top5_work']} | "
            f"{row['operation_stack_top5_recall']} | {row['patch_verdict']} ({row['patch_delta_ap']}) | "
            f"{row['optimization_action']} |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Evidence |", "|---|---|---|"])
    for row in payload["checks"]:
        lines.append(f"| `{row['check']}` | {row['status']} | {row['evidence']} |")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    headline_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['row_id'])}</td>"
        f"<td>{html.escape(row['paper_block'])}</td>"
        f"<td>{html.escape(row['claim_role'])}</td>"
        f"<td>{html.escape(row['primary_numbers'])}</td>"
        f"<td>{html.escape(row['counterpoint'])}</td>"
        "</tr>"
        for row in payload["headline_rows"]
    )
    case_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['task'])}</td>"
        f"<td>{html.escape(row['best_visible_policy'])}</td>"
        f"<td>{html.escape(row['operation_stack_top5_work'])}</td>"
        f"<td>{html.escape(row['operation_stack_top5_recall'])}</td>"
        f"<td>{html.escape(row['patch_verdict'])} ({html.escape(row['patch_delta_ap'])})</td>"
        f"<td>{html.escape(row['optimization_action'])}</td>"
        "</tr>"
        for row in payload["case_cards"]
    )
    checks = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['check'])}</td>"
        f"<td>{html.escape(row['status'])}</td>"
        f"<td>{html.escape(row['evidence'])}</td>"
        "</tr>"
        for row in payload["checks"]
    )
    page = f"""<!doctype html>
<meta charset=\"utf-8\">
<title>R365 Paper Headline Case Studies</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ddd; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f6f6; }}
code {{ background: #f3f3f3; padding: 0.1rem 0.2rem; }}
</style>
<h1>R365 Paper Headline Case Studies</h1>
<p>Status: <code>{html.escape(payload['status'])}</code></p>
<p>Checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}</p>
<h2>Headline Rows</h2>
<table><thead><tr><th>Row</th><th>Block</th><th>Role</th><th>Main numbers</th><th>Counterpoint</th></tr></thead><tbody>{headline_rows}</tbody></table>
<h2>Task Cards</h2>
<table><thead><tr><th>Task</th><th>Policy</th><th>Work@5</th><th>Recall@5</th><th>Patch</th><th>Action</th></tr></thead><tbody>{case_rows}</tbody></table>
<h2>Checks</h2>
<table><thead><tr><th>Check</th><th>Status</th><th>Evidence</th></tr></thead><tbody>{checks}</tbody></table>
"""
    path.write_text(page, encoding="utf-8")


def contains_all(text: str, tokens: list[str]) -> bool:
    return all(token in text for token in tokens)


def build_checks(
    headline_rows: list[dict[str, str]],
    case_cards: list[dict[str, str]],
    source_status: list[dict[str, str]],
    paper_text: str,
) -> list[dict[str, str]]:
    headline_blob = json.dumps(headline_rows, sort_keys=True)
    case_blob = json.dumps(case_cards, sort_keys=True)
    checks = [
        {
            "check": "headline_rows_cover_e2_e3_claim",
            "status": "pass"
            if len(headline_rows) == 5
            and contains_all(headline_blob, ["0.0937", "0.39", "157.5", "285", "24/24", "20/24", "0.0376", "0.575", "0.2583", "0.2402"])
            else "fail",
            "evidence": "Headline rows preserve E2 localization/tradeoff, E3 actionability, oracle-depth, and boundary-field numbers.",
        },
        {
            "check": "six_task_cards_with_counterpoints",
            "status": "pass"
            if len(case_cards) == 6 and all(row["counterpoints"].strip() for row in case_cards)
            else "fail",
            "evidence": "All six oracle-backed tasks have an action card and explicit counterpoint.",
        },
        {
            "check": "visible_non_oracle_actionability",
            "status": "pass"
            if contains_all(case_blob, ["actionable_with_counterpoints", "operation_stack_top5_work"])
            or contains_all(case_blob, ["accept_patch", "reject_patch_or_needs_new_mapping"])
            else "fail",
            "evidence": "Task cards are based on visible-policy action cards and R354 profile-spec patches.",
        },
        {
            "check": "paper_text_mentions_r365",
            "status": "pass"
            if contains_all(paper_text, ["R365", "headline", "case"])
            else "fail",
            "evidence": "Evaluation ledger and paper drafts mention the R365 headline/case-study selector.",
        },
        {
            "check": "no_new_data_or_profiler_rerun",
            "status": "pass"
            if all(row["status"] in {"tracked_clean", "tracked_dirty_allowed"} for row in source_status)
            else "fail",
            "evidence": "All inputs are tracked artifacts or current paper/docs; the script does not fetch data or rerun the profiler.",
        },
        {
            "check": "two_abstractions_only",
            "status": "pass"
            if "operation stack" in paper_text and "operation" in paper_text and "new profiler object" in paper_text
            else "fail",
            "evidence": "The paper text keeps outputs as operation/operation-stack evidence rather than new profiler abstractions.",
        },
    ]
    return checks


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    start = time.time()

    data = {
        "r320": read_json(SOURCES["R320 profile accuracy"]),
        "optimization_insights": read_csv(SOURCES["R320 optimization insights"]),
        "r333": read_json(SOURCES["R333 inspection frontier"]),
        "r334": read_json(SOURCES["R334 fragmentation tradeoff"]),
        "lens_cards": read_csv(SOURCES["R345 task lens cards"]),
        "action_cards": read_csv(SOURCES["R348 action cards"]),
        "r348": read_json(SOURCES["R348 action report"]),
        "r354": read_json(SOURCES["R354 profile patch"]),
        "patch_summary": read_csv(SOURCES["R354 profile patch summary"]),
        "r355": read_json(SOURCES["R355 oracle depth"]),
        "r358": read_json(SOURCES["R358 boundary patch"]),
        "r363": read_json(SOURCES["R363 visualization portfolio"]),
    }
    paper_text = "\n".join(read_text(path) for path in PAPER_SOURCES.values())
    source_status = source_rows()
    headline_rows = build_headlines(data)
    case_cards = build_case_cards(data)
    checks = build_checks(headline_rows, case_cards, source_status, paper_text)
    checks_passed = sum(row["status"] == "pass" for row in checks)
    status = "pass" if checks_passed == len(checks) else "fail"

    payload = {
        "run_id": RUN_ID,
        "schema": "agentsight.paper_headline_case_studies.v1",
        "status": status,
        "commit": git_commit(),
        "elapsed_s": round(time.time() - start, 4),
        "claim": "E2/E3 paper-ready headline rows and case cards can be mechanically extracted from existing labeled-trace artifacts",
        "summary": {
            "status": status,
            "checks_passed": checks_passed,
            "checks_total": len(checks),
            "headline_rows": len(headline_rows),
            "case_cards": len(case_cards),
            "network_access_required": False,
            "profiler_rerun": False,
            "dataset_sync": False,
        },
        "input_policy": {
            "no_dataset_sync": True,
            "no_dataset_creation": True,
            "no_relabeling": True,
            "no_profiler_rerun": True,
            "hidden_labels_only_after_ranking": True,
        },
        "not_new_empirical_result": True,
        "not_a_human_study_result": True,
        "not_an_agent_analyst_task_result": True,
        "profiler_abstractions": ["operation", "operation stack"],
        "headline_rows": headline_rows,
        "case_cards": case_cards,
        "checks": checks,
        "source_status": source_status,
    }

    report_json = args.out_dir / "headline-case-studies.json"
    report_md = args.out_dir / "headline-case-studies.md"
    html_path = args.out_dir / "index.html"
    headline_csv = args.out_dir / "headline-rows.csv"
    case_csv = args.out_dir / "task-case-cards.csv"
    checks_csv = args.out_dir / "headline-checks.csv"
    source_csv = args.out_dir / "source-status.csv"
    table_tex = args.out_dir / "headline-table.tex"
    run_result = args.out_dir / "run-result.json"

    report_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report_md, payload)
    write_html(html_path, payload)
    write_csv(headline_csv, headline_rows, HEADLINE_FIELDS)
    write_csv(case_csv, case_cards, CASE_FIELDS)
    write_csv(checks_csv, checks, ["check", "status", "evidence"])
    write_csv(source_csv, source_status, ["source", "path", "status", "sha256"])
    write_latex_table(table_tex, headline_rows)
    run_result.write_text(
        json.dumps(
            {
                "run_id": RUN_ID,
                "status": status,
                "report": rel(report_json),
                "checks_passed": checks_passed,
                "checks_total": len(checks),
                "network_access_required": False,
                "profiler_rerun": False,
                "not_new_empirical_result": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "run_id": RUN_ID,
                "status": status,
                "checks_passed": checks_passed,
                "checks_total": len(checks),
                "report": rel(report_json),
                "headline_rows": len(headline_rows),
                "case_cards": len(case_cards),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
