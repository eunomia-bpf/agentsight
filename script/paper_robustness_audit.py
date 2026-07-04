#!/usr/bin/env python3
"""R311: audit paper claims against existing robustness and counterpoint evidence.

R311 does not fetch datasets or rerun profilers. It reads tracked, clean R302,
R305, R308, R309, and R310 artifacts, then emits a reviewer-stress matrix that
separates what the current paper can claim from what it must not claim.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-robustness-audit-r311"
SOURCE_PATHS = {
    "r302_ranking": OUT_ROOT
    / "operation-analyst-ranking-r302"
    / "ranking-report.json",
    "r305_case_baseline": OUT_ROOT
    / "operation-case-baseline-r305"
    / "case-baseline-report.json",
    "r308_analyst_outcome": OUT_ROOT
    / "operation-analyst-outcome-r308"
    / "analyst-outcome-report.json",
    "r309_problem_value": OUT_ROOT
    / "operation-problem-value-r309"
    / "problem-value-report.json",
    "r310_evidence_matrix": OUT_ROOT
    / "paper-evidence-matrix-r310"
    / "evidence-matrix.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


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


def ensure_sources_tracked_clean(paths: list[Path]) -> None:
    for path in paths:
        if not path.exists():
            raise SystemExit(f"missing source artifact {rel(path)}")
        git_check("source artifact is not git-tracked", ["ls-files", "--error-unmatch"], path)
        git_check("source artifact has unstaged changes", ["diff", "--quiet"], path)
        git_check("source artifact has staged changes", ["diff", "--cached", "--quiet"], path)


def round_value(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, dict):
        return {key: round_value(child) for key, child in value.items()}
    if isinstance(value, list):
        return [round_value(child) for child in value]
    return value


def fmt_ratio(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def compact_list(values: list[str], limit: int = 2) -> str:
    if len(values) <= limit:
        return "; ".join(values)
    return "; ".join(values[:limit]) + f"; +{len(values) - limit} more"


def tex_escape(value: Any) -> str:
    text = str(value)
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


def support_label(checks: dict[str, bool]) -> str:
    if (
        checks["selective_vs_flat"]
        and checks["positive_group"]
        and checks["high_lift_evidence"]
        and checks["selected_lift_ge_one"]
        and checks["higher_recall_than_fixed"]
    ):
        return "strong_proxy_support"
    if checks["selective_vs_flat"] and checks["positive_group"]:
        return "scoped_proxy_support"
    return "counterexample_or_low_signal"


def task_robustness_rows(r309: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for card in r309["problem_cards"]:
        op = card["r305_case_packet"]["operation_stack"]
        flat = card["r305_case_packet"]["flat"]
        fixed = card["r305_case_packet"]["fixed_session"]
        outcome = card["r308_first_evidence"]
        checks = {
            "selective_vs_flat": float(op["work"]) < float(flat["work"]),
            "positive_group": outcome["operation_stack_first_positive_work"] is not None,
            "high_lift_evidence": bool(outcome["operation_stack_high_lift"]),
            "selected_lift_ge_one": float(op["lift"]) >= 1.0,
            "higher_recall_than_fixed": float(op["recall"]) > float(fixed["recall"]),
            "lower_work_than_fixed": float(op["work"]) < float(fixed["work"]),
        }
        rows.append(
            round_value(
                {
                    "task": card["task"],
                    "dataset": card["dataset"],
                    "query_family": card["query_family"],
                    "problem": card["problem"],
                    "oracle": card["oracle"],
                    "operation_stack": op,
                    "flat": flat,
                    "fixed_session": fixed,
                    "checks": checks,
                    "support_label": support_label(checks),
                    "counterpoints": card["counterpoints"],
                    "supported_interpretation": card["supported_interpretation"],
                }
            )
        )
    return rows


def count(rows: list[dict[str, Any]], check: str) -> int:
    return sum(1 for row in rows if row["checks"][check])


def stress_tests(
    rows: list[dict[str, Any]],
    r302: dict[str, Any],
    r310: dict[str, Any],
) -> list[dict[str, Any]]:
    metrics = r310["problem_value_metrics"]
    task_count = len(rows)
    r302_medians = r302["summary"]["medians"]
    query_top10 = r302_medians["operation_stack:query_aware:top_10_groups"]
    width_top10 = r302_medians["operation_stack:width:top_10_groups"]
    return [
        {
            "question": "Is this only a flat trace or prompt/session flamegraph?",
            "verdict": "pass",
            "evidence": [
                "R310 keeps exactly two profiler abstractions: operation and operation stack",
                "C1/C2 support arbitrary stack fields and recursive depth under scoped wording",
                "R306 standard-trace exchange preserves folded operation-stack output on the fixture",
            ],
            "paper_wording": "Claim a two-abstraction profiler model with stack specs, not a prompt/session/span hierarchy.",
        },
        {
            "question": "Does the operation-stack view add value over flat packets?",
            "verdict": "pass",
            "evidence": [
                f"operation-stack packets are more selective than flat on {count(rows, 'selective_vs_flat')}/{task_count} tasks",
                f"positive groups appear in {count(rows, 'positive_group')}/{task_count} tasks",
                f"high-lift evidence appears in {count(rows, 'high_lift_evidence')}/{task_count} tasks",
            ],
            "paper_wording": "Claim inspectability over flat summaries under oracle-backed proxy tasks.",
        },
        {
            "question": "Does the operation-stack view universally dominate fixed-session drilldown?",
            "verdict": "narrow",
            "evidence": [
                f"selected recall is higher than fixed-session on {count(rows, 'higher_recall_than_fixed')}/{task_count} tasks",
                f"selected work is lower than fixed-session on only {count(rows, 'lower_work_than_fixed')}/{task_count} tasks",
                metrics["fixed_session_lower_selected_work"] + " tasks have lower selected work under fixed-session",
            ],
            "paper_wording": "Claim a recall/selectivity tradeoff, not universal dominance.",
        },
        {
            "question": "Is query-aware analysis just oracle leakage?",
            "verdict": "pass_with_scope",
            "evidence": [
                "R302 rankers exclude hidden oracle fields",
                (
                    "top-10 query-aware operation-stack work/lift "
                    f"{query_top10['median_inspected_operation_fraction']}/"
                    f"{query_top10['median_positive_lift']} vs width "
                    f"{width_top10['median_inspected_operation_fraction']}/"
                    f"{width_top10['median_positive_lift']}"
                ),
                "rankers are hand-written visible-field heuristics, not learned detectors",
            ],
            "paper_wording": "Use as configurable analysis-policy evidence, not automatic anomaly detection.",
        },
        {
            "question": "Does the evidence prove human/agent analyst utility?",
            "verdict": "fail_for_stronger_claim",
            "evidence": [
                "R308/R309 are automated replays over hidden labels",
                "no analyst timing, accuracy, or workload study has been run",
                "the existing visible packets are suitable inputs for that next controlled study",
            ],
            "paper_wording": "Claim automated inspectability proxy value only.",
        },
        {
            "question": "Is boundary discovery solved?",
            "verdict": "partial",
            "evidence": [
                "R310 keeps C3 partial",
                "R299 shows family-specific calibration and simple-baseline counterexamples",
                "deterministic and supervised field derivation are supported; unsupervised intent discovery is not",
            ],
            "paper_wording": "Frame boundary backends as extension points that derive stackable fields.",
        },
        {
            "question": "Is the novelty only the flamegraph visualization?",
            "verdict": "pass",
            "evidence": [
                "R302 ranking policies, R305 cross-view case packets, R308 first-evidence outcomes, and R309 problem cards are non-flamegraph analyses over the same stacks",
                "R310 evidence matrix and this R311 stress audit are paper-facing analyses, not profiler abstractions",
            ],
            "paper_wording": "State novelty as query-time recursive operation stacks plus auditable non-flamegraph analyses.",
        },
    ]


def claim_posture(r310: dict[str, Any]) -> dict[str, Any]:
    rows = r310["claim_matrix"]
    return {
        "paper_ready_mechanism_claims": [row["claim"] for row in rows if row["claim"] in {"C1", "C2"}],
        "paper_ready_proxy_value_claims": [row["claim"] for row in rows if row["claim"] == "C4"],
        "partial_claims": r310["partial_claims"],
        "recommended_posture": (
            "Submit as a systems/ML-observability paper about a two-abstraction "
            "semantic profiler and automated inspectability proxy evidence, not "
            "as a human-productivity or unsupervised-boundary paper."
        ),
        "must_not_claim": r310["global_must_not_claim"],
    }


def build_payload() -> dict[str, Any]:
    ensure_sources_tracked_clean(list(SOURCE_PATHS.values()))
    r302 = load_json(SOURCE_PATHS["r302_ranking"])
    r305 = load_json(SOURCE_PATHS["r305_case_baseline"])
    r308 = load_json(SOURCE_PATHS["r308_analyst_outcome"])
    r309 = load_json(SOURCE_PATHS["r309_problem_value"])
    r310 = load_json(SOURCE_PATHS["r310_evidence_matrix"])
    rows = task_robustness_rows(r309)
    task_count = len(rows)

    return {
        "schema": "agentsight.paper-robustness-audit.v1",
        "run_id": "R311",
        "commit": git_output(["rev-parse", "HEAD"]),
        "input_policy": {
            "dataset_sync": "none",
            "source_artifacts": {key: rel(path) for key, path in SOURCE_PATHS.items()},
            "source_requirement": "git-tracked and clean before synthesis",
            "purpose": "reviewer stress-test synthesis only; no new dataset or profiler run",
        },
        "profiler_abstractions": ["operation", "operation stack"],
        "source_sanity": {
            "r305_task_view_scores": len(r305["task_view_scores"]),
            "r308_task_view_outcomes": len(r308["task_view_outcomes"]),
            "r309_problem_cards": len(r309["problem_cards"]),
            "r310_claims": r310["claim_count"],
        },
        "summary": {
            "datasets": r310["problem_value_metrics"]["datasets"],
            "tasks": task_count,
            "operations": r310["problem_value_metrics"]["operations"],
            "positive_operations": r310["problem_value_metrics"]["positive_operations"],
            "operation_stack_more_selective_than_flat": f"{count(rows, 'selective_vs_flat')}/{task_count}",
            "operation_stack_positive_group_coverage": f"{count(rows, 'positive_group')}/{task_count}",
            "operation_stack_high_lift_coverage": f"{count(rows, 'high_lift_evidence')}/{task_count}",
            "operation_stack_higher_recall_than_fixed": f"{count(rows, 'higher_recall_than_fixed')}/{task_count}",
            "operation_stack_lower_work_than_fixed": f"{count(rows, 'lower_work_than_fixed')}/{task_count}",
            "fixed_session_lower_work_counterpoint": r310["problem_value_metrics"][
                "fixed_session_lower_selected_work"
            ],
            "sign_test_caution": (
                "Counts are task-level robustness checks over six oracle-backed tasks, "
                "not a statistical generalization claim."
            ),
        },
        "claim_posture": claim_posture(r310),
        "task_robustness": rows,
        "reviewer_stress_tests": stress_tests(rows, r302, r310),
        "paper_claim_delta": [
            {
                "claim": "C1",
                "status": "keep_scoped",
                "delta": "Trace exchange and heterogeneous operations are paper-ready, but standard trace support remains fixture-level.",
            },
            {
                "claim": "C2",
                "status": "keep_scoped",
                "delta": "Recursive stack-depth and arbitrary fields are paper-ready, but not perfect intent recovery.",
            },
            {
                "claim": "C3",
                "status": "partial",
                "delta": "Boundary backends should be described as deterministic/supervised field derivation extension points.",
            },
            {
                "claim": "C4",
                "status": "automated_proxy_ready",
                "delta": "Problem-value evidence supports inspectability and novelty, while human utility remains the next controlled study.",
            },
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# Paper Robustness Audit R311",
        "",
        "R311 reads existing tracked artifacts only. It does not sync datasets, rerun profilers, or add abstractions.",
        "",
        "## Headline",
        "",
        f"- Abstractions: {', '.join(payload['profiler_abstractions'])}.",
        f"- Workload: {summary['datasets']} datasets / {summary['tasks']} tasks / {summary['operations']} operations / {summary['positive_operations']} positives.",
        f"- Operation-stack vs flat: more selective {summary['operation_stack_more_selective_than_flat']}; positive group {summary['operation_stack_positive_group_coverage']}; high-lift {summary['operation_stack_high_lift_coverage']}.",
        f"- Operation-stack vs fixed-session: higher selected recall {summary['operation_stack_higher_recall_than_fixed']}; lower selected work {summary['operation_stack_lower_work_than_fixed']}; fixed-session lower-work counterpoint {summary['fixed_session_lower_work_counterpoint']}.",
        f"- Guardrail: {summary['sign_test_caution']}",
        "",
        "## Reviewer Stress Tests",
        "",
        "| Question | Verdict | Evidence | Paper wording |",
        "|---|---|---|---|",
    ]
    for row in payload["reviewer_stress_tests"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["question"],
                    row["verdict"],
                    compact_list(row["evidence"], 2),
                    row["paper_wording"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Task Robustness",
            "",
            "| Task | Dataset | Support | Operation-stack work/recall/lift | Counterpoints |",
            "|---|---|---|---|---|",
        ]
    )
    for row in payload["task_robustness"]:
        op = row["operation_stack"]
        lines.append(
            "| "
            + " | ".join(
                [
                    row["task"],
                    row["dataset"],
                    row["support_label"],
                    f"{fmt_ratio(op['work'])} / {fmt_ratio(op['recall'])} / {fmt_ratio(op['lift'])}",
                    compact_list(row["counterpoints"], 2) if row["counterpoints"] else "none",
                ]
            )
            + " |"
        )
    lines.extend(["", "## Must Not Claim", ""])
    lines.extend(f"- {item}" for item in payload["claim_posture"]["must_not_claim"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "task",
                "dataset",
                "query_family",
                "support_label",
                "operation_stack_work",
                "operation_stack_recall",
                "operation_stack_lift",
                "flat_work",
                "fixed_session_work",
                "fixed_session_recall",
                "selective_vs_flat",
                "high_lift_evidence",
                "higher_recall_than_fixed",
                "lower_work_than_fixed",
                "selected_lift_ge_one",
                "counterpoints",
            ],
        )
        writer.writeheader()
        for row in payload["task_robustness"]:
            op = row["operation_stack"]
            flat = row["flat"]
            fixed = row["fixed_session"]
            writer.writerow(
                {
                    "task": row["task"],
                    "dataset": row["dataset"],
                    "query_family": row["query_family"],
                    "support_label": row["support_label"],
                    "operation_stack_work": op["work"],
                    "operation_stack_recall": op["recall"],
                    "operation_stack_lift": op["lift"],
                    "flat_work": flat["work"],
                    "fixed_session_work": fixed["work"],
                    "fixed_session_recall": fixed["recall"],
                    "selective_vs_flat": row["checks"]["selective_vs_flat"],
                    "high_lift_evidence": row["checks"]["high_lift_evidence"],
                    "higher_recall_than_fixed": row["checks"]["higher_recall_than_fixed"],
                    "lower_work_than_fixed": row["checks"]["lower_work_than_fixed"],
                    "selected_lift_ge_one": row["checks"]["selected_lift_ge_one"],
                    "counterpoints": "; ".join(row["counterpoints"]),
                }
            )


def write_tex(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        r"\begin{table*}[t]",
        r"  \centering",
        r"  \scriptsize",
        r"  \caption{Reviewer-stress audit generated by R311 from existing labeled-agent artifacts.}",
        r"  \label{tab:r311-robustness-audit}",
        r"  \begin{tabular}{p{0.18\linewidth}p{0.14\linewidth}p{0.17\linewidth}p{0.18\linewidth}p{0.25\linewidth}}",
        r"    \toprule",
        r"    Task & Dataset & Support & Stack work/recall/lift & Counterpoint \\",
        r"    \midrule",
    ]
    for row in payload["task_robustness"]:
        op = row["operation_stack"]
        lines.append(
            "    "
            + " & ".join(
                [
                    tex_escape(row["task"]),
                    tex_escape(row["dataset"]),
                    tex_escape(row["support_label"]),
                    tex_escape(f"{fmt_ratio(op['work'])}/{fmt_ratio(op['recall'])}/{fmt_ratio(op['lift'])}"),
                    tex_escape(compact_list(row["counterpoints"], 2) if row["counterpoints"] else "none"),
                ]
            )
            + r" \\"
        )
    lines.extend(
        [
            r"    \bottomrule",
            r"  \end{tabular}",
            r"\end{table*}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    stress_rows = []
    for row in payload["reviewer_stress_tests"]:
        evidence = "<br>".join(html.escape(item) for item in row["evidence"])
        stress_rows.append(
            "<tr>"
            f"<th>{html.escape(row['question'])}</th>"
            f"<td>{html.escape(row['verdict'])}</td>"
            f"<td>{evidence}</td>"
            f"<td>{html.escape(row['paper_wording'])}</td>"
            "</tr>"
        )
    task_rows = []
    for row in payload["task_robustness"]:
        op = row["operation_stack"]
        task_rows.append(
            "<tr>"
            f"<th>{html.escape(row['task'])}</th>"
            f"<td>{html.escape(row['dataset'])}</td>"
            f"<td>{html.escape(row['support_label'])}</td>"
            f"<td>{fmt_ratio(op['work'])} / {fmt_ratio(op['recall'])} / {fmt_ratio(op['lift'])}</td>"
            f"<td>{html.escape(compact_list(row['counterpoints'], 2) if row['counterpoints'] else 'none')}</td>"
            "</tr>"
        )
    summary = payload["summary"]
    path.write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paper Robustness Audit R311</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }
    h1 { font-size: 1.6rem; margin-bottom: 0.25rem; }
    h2 { margin-top: 2rem; }
    p { max-width: 980px; line-height: 1.5; }
    table { border-collapse: collapse; margin-top: 1rem; max-width: 1240px; }
    th, td { border: 1px solid #d8dee9; padding: 0.55rem 0.75rem; text-align: left; vertical-align: top; }
    th { background: #f6f8fa; }
    code { background: #f6f8fa; padding: 0.1rem 0.25rem; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>Paper Robustness Audit R311</h1>
  <p>
    R311 stress-tests the current paper claims using existing tracked artifacts
    only. The profiler model remains exactly two abstractions:
    <code>operation</code> and <code>operation stack</code>.
  </p>
"""
        + f"""  <p>
    Workload: {summary['datasets']} datasets / {summary['tasks']} tasks /
    {summary['operations']} operations / {summary['positive_operations']} positives.
    Operation-stack packets are more selective than flat on
    {summary['operation_stack_more_selective_than_flat']} tasks and have
    high-lift evidence on {summary['operation_stack_high_lift_coverage']} tasks.
  </p>
  <h2>Reviewer Stress Tests</h2>
  <table>
    <tr><th>Question</th><th>Verdict</th><th>Evidence</th><th>Paper Wording</th></tr>
"""
        + "\n".join(stress_rows)
        + """
  </table>
  <h2>Task Robustness</h2>
  <table>
    <tr><th>Task</th><th>Dataset</th><th>Support</th><th>Stack work/recall/lift</th><th>Counterpoints</th></tr>
"""
        + "\n".join(task_rows)
        + """
  </table>
</body>
</html>
""",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload()

    json_path = args.out_dir / "robustness-audit.json"
    md_path = args.out_dir / "robustness-audit.md"
    csv_path = args.out_dir / "robustness-audit.csv"
    tex_path = args.out_dir / "evidence-table.tex"
    html_path = args.out_dir / "index.html"
    run_result_path = args.out_dir / "run-result.json"

    payload["outputs"] = {
        "json": rel(json_path),
        "markdown": rel(md_path),
        "csv": rel(csv_path),
        "tex": rel(tex_path),
        "html": rel(html_path),
        "run_result": rel(run_result_path),
    }
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    write_csv(csv_path, payload)
    write_tex(tex_path, payload)
    write_html(html_path, payload)
    write_json(
        run_result_path,
        {
            "run_id": payload["run_id"],
            "status": "ok",
            "tasks": payload["summary"]["tasks"],
            "operation_stack_more_selective_than_flat": payload["summary"][
                "operation_stack_more_selective_than_flat"
            ],
            "operation_stack_high_lift_coverage": payload["summary"][
                "operation_stack_high_lift_coverage"
            ],
            "operation_stack_higher_recall_than_fixed": payload["summary"][
                "operation_stack_higher_recall_than_fixed"
            ],
            "operation_stack_lower_work_than_fixed": payload["summary"][
                "operation_stack_lower_work_than_fixed"
            ],
            "json": rel(json_path),
            "markdown": rel(md_path),
            "csv": rel(csv_path),
            "tex": rel(tex_path),
            "html": rel(html_path),
        },
    )
    print(json.dumps(load_json(run_result_path), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
