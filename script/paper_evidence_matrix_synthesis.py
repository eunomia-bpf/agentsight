#!/usr/bin/env python3
"""R310: synthesize a paper-ready claim/evidence matrix.

R310 does not fetch datasets or introduce profiler abstractions. It reads the
tracked R307 claim gate and R309 real-problem value synthesis, then emits a
paper-facing matrix that separates supported wording from unsupported claims.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-evidence-matrix-r310"
SOURCE_PATHS = {
    "r307_claim_readiness": OUT_ROOT
    / "paper-claim-readiness-r307"
    / "paper-readiness-synthesis.json",
    "r309_problem_value": OUT_ROOT
    / "operation-problem-value-r309"
    / "problem-value-report.json",
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


def compact_list(values: list[str], limit: int = 2) -> str:
    if len(values) <= limit:
        return "; ".join(values)
    return "; ".join(values[:limit]) + f"; +{len(values) - limit} more"


def r309_metrics(r309: dict[str, Any]) -> dict[str, Any]:
    summary = r309["summary"]
    stack = summary["operation_stack"]
    ranking = r309["ranking_policy_context"]
    fixed_less_work = summary["tasks"] - stack["tasks_less_work_than_fixed_session"]
    return {
        "datasets": summary["dataset_count"],
        "dataset_names": summary["datasets"],
        "tasks": summary["tasks"],
        "operations": summary["operation_count"],
        "positive_operations": summary["positive_operation_count"],
        "operation_stack_positive_coverage": stack["positive_coverage"],
        "operation_stack_high_lift_coverage": stack["high_lift_coverage"],
        "operation_stack_more_selective_than_flat": f"{stack['tasks_more_selective_than_flat']}/{summary['tasks']}",
        "operation_stack_higher_recall_than_fixed_session": f"{stack['tasks_higher_recall_than_fixed_session']}/{summary['tasks']}",
        "fixed_session_lower_selected_work": f"{fixed_less_work}/{summary['tasks']}",
        "median_selected_work": stack["median_selected_work"],
        "median_selected_recall": stack["median_selected_recall"],
        "median_top_group_lift": stack["median_top_group_lift"],
        "top10_query_aware_work": ranking["top10_query_aware_operation_stack_work"],
        "top10_query_aware_lift": ranking["top10_query_aware_operation_stack_lift"],
        "top10_width_work": ranking["top10_width_operation_stack_work"],
        "top10_width_lift": ranking["top10_width_operation_stack_lift"],
    }


def readiness_level(claim: str, verdict: str) -> str:
    if claim in {"C1", "C2"}:
        return "paper-ready mechanism claim with scoped wording"
    if claim == "C3":
        return "partial extension-point claim; needs stronger calibrated backend evidence"
    if claim == "C4":
        return "paper-ready automated inspectability proxy; not user utility"
    return verdict


def paper_use(claim: str) -> str:
    return {
        "C1": "Use in abstract/design as heterogeneous operation model and trace exchange evidence.",
        "C2": "Use in design/results as recursive stack-depth evidence.",
        "C3": "Use as extension-point evidence, with negative controls and scoped language.",
        "C4": "Use in evaluation/discussion as real-problem proxy value and counterpoints.",
    }.get(claim, "Use only with source-specific wording.")


def next_gate(claim: str, r307: dict[str, Any]) -> str:
    if claim == "C3":
        return "Add calibrated boundary backends and compare against simple derived-field baselines on another family."
    if claim == "C4":
        return r307["paper_readiness"]["next_gate"]
    if claim == "C1":
        return "Import one real external OpenTelemetry GenAI or Perfetto trace bundle and verify operation-stack parity."
    if claim == "C2":
        return "Validate deeper sequence/subtask boundaries beyond adjacent action labels."
    return "Keep claim tied to tracked artifacts."


def headline_numbers(claim: str, row: dict[str, Any], metrics: dict[str, Any]) -> list[str]:
    if claim == "C4":
        return [
            f"{metrics['datasets']} datasets / {metrics['tasks']} tasks / {metrics['operations']} task-operations",
            f"operation-stack more selective than flat: {metrics['operation_stack_more_selective_than_flat']}",
            f"high-lift evidence: {metrics['operation_stack_high_lift_coverage']}",
            f"higher selected recall than fixed-session: {metrics['operation_stack_higher_recall_than_fixed_session']}",
            f"fixed-session lower selected work: {metrics['fixed_session_lower_selected_work']}",
            f"top-10 query-aware work/lift {metrics['top10_query_aware_work']}/{metrics['top10_query_aware_lift']} vs width {metrics['top10_width_work']}/{metrics['top10_width_lift']}",
        ]
    return row["evidence"]


def build_matrix() -> dict[str, Any]:
    ensure_sources_tracked_clean(list(SOURCE_PATHS.values()))
    r307 = load_json(SOURCE_PATHS["r307_claim_readiness"])
    r309 = load_json(SOURCE_PATHS["r309_problem_value"])
    metrics = r309_metrics(r309)

    claim_rows: list[dict[str, Any]] = []
    for row in r307["claim_verdicts"]:
        claim = row["claim"]
        claim_rows.append(
            {
                "claim": claim,
                "verdict": row["verdict"],
                "readiness_level": readiness_level(claim, row["verdict"]),
                "paper_use": paper_use(claim),
                "supported_wording": row["current_supported_wording"],
                "headline_numbers": headline_numbers(claim, row, metrics),
                "must_not_claim": row["must_not_claim"],
                "next_gate": next_gate(claim, r307),
                "source_artifacts": [
                    rel(SOURCE_PATHS["r307_claim_readiness"]),
                    rel(SOURCE_PATHS["r309_problem_value"]) if claim == "C4" else "",
                ],
            }
        )

    global_must_not_claim = sorted(
        set(r307["paper_readiness"]["must_not_claim"])
        | {
            "human accuracy or time improvement",
            "automatic anomaly detection",
            "universal dominance over fixed-session baselines",
            "unsupervised intent discovery",
            "complete trace ecosystem compatibility",
        }
    )
    partial_claims = [
        row["claim"]
        for row in claim_rows
        if "partial" in row["verdict"] or row["claim"] == "C3"
    ]
    scoped_ready_claims = [
        row["claim"]
        for row in claim_rows
        if row["claim"] in {"C1", "C2", "C4"}
    ]

    return {
        "schema": "agentsight.paper-evidence-matrix.v1",
        "run_id": "R310",
        "commit": git_output(["rev-parse", "HEAD"]),
        "input_policy": {
            "dataset_sync": "none",
            "source_artifacts": {key: rel(path) for key, path in SOURCE_PATHS.items()},
            "source_requirement": "git-tracked and clean before synthesis",
            "purpose": "paper claim/evidence matrix only; no new empirical result",
        },
        "profiler_abstractions": ["operation", "operation stack"],
        "claim_count": len(claim_rows),
        "scoped_paper_ready_claims": scoped_ready_claims,
        "partial_claims": partial_claims,
        "evidence_level": (
            "level-3 conference-paper evidence for mechanism claims; "
            "automated proxy evidence for value; level-4 remains blocked by "
            "a controlled analyst study and stronger boundary calibration"
        ),
        "highest_risks": [
            "user utility is not proven without a controlled analyst study",
            "boundary generalization remains partial and family-specific",
            "standard trace exchange is fixture-level, not full ecosystem compatibility",
        ],
        "problem_value_metrics": metrics,
        "claim_scope": r309["claim_scope"],
        "global_must_not_claim": global_must_not_claim,
        "claim_matrix": claim_rows,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    metrics = payload["problem_value_metrics"]
    lines = [
        "# Paper Evidence Matrix R310",
        "",
        "R310 is a paper-facing synthesis over tracked R307/R309 artifacts. It does not sync datasets, rerun converters, or introduce profiler abstractions.",
        "",
        "## Headline",
        "",
        f"- Abstractions: {', '.join(payload['profiler_abstractions'])}.",
        f"- Claims: {payload['claim_count']} total; scoped paper-ready claims: {', '.join(payload['scoped_paper_ready_claims'])}; partial claims: {', '.join(payload['partial_claims'])}.",
        f"- Problem-value suite: {metrics['datasets']} datasets / {metrics['tasks']} tasks / {metrics['operations']} operations / {metrics['positive_operations']} positives.",
        f"- Operation-stack evidence: high-lift {metrics['operation_stack_high_lift_coverage']}, more selective than flat {metrics['operation_stack_more_selective_than_flat']}, higher recall than fixed-session {metrics['operation_stack_higher_recall_than_fixed_session']}.",
        f"- Counterpoint: fixed-session lower selected work {metrics['fixed_session_lower_selected_work']}.",
        "",
        "## Claim Matrix",
        "",
        "| Claim | Verdict | Paper use | Headline evidence | Must not claim |",
        "|---|---|---|---|---|",
    ]
    for row in payload["claim_matrix"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["claim"],
                    row["verdict"],
                    row["paper_use"],
                    compact_list(row["headline_numbers"], 3),
                    compact_list(row["must_not_claim"], 2),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Global Must-Not-Claim",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["global_must_not_claim"])
    lines.extend(["", "## Source Artifacts", ""])
    for key, source in payload["input_policy"]["source_artifacts"].items():
        lines.append(f"- `{key}`: `{source}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "claim",
                "verdict",
                "readiness_level",
                "paper_use",
                "supported_wording",
                "headline_numbers",
                "must_not_claim",
                "next_gate",
            ],
        )
        writer.writeheader()
        for row in payload["claim_matrix"]:
            writer.writerow(
                {
                    "claim": row["claim"],
                    "verdict": row["verdict"],
                    "readiness_level": row["readiness_level"],
                    "paper_use": row["paper_use"],
                    "supported_wording": row["supported_wording"],
                    "headline_numbers": "; ".join(row["headline_numbers"]),
                    "must_not_claim": "; ".join(row["must_not_claim"]),
                    "next_gate": row["next_gate"],
                }
            )


def write_tex(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        r"\begin{table*}[t]",
        r"  \centering",
        r"  \scriptsize",
        r"  \caption{Paper-ready claim/evidence matrix generated by R310.}",
        r"  \label{tab:r310-evidence-matrix}",
        r"  \begin{tabular}{p{0.08\linewidth}p{0.16\linewidth}p{0.36\linewidth}p{0.28\linewidth}}",
        r"    \toprule",
        r"    Claim & Verdict & Paper-ready evidence & Boundary \\",
        r"    \midrule",
    ]
    for row in payload["claim_matrix"]:
        lines.append(
            "    "
            + " & ".join(
                [
                    tex_escape(row["claim"]),
                    tex_escape(row["verdict"]),
                    tex_escape(compact_list(row["headline_numbers"], 2)),
                    tex_escape(compact_list(row["must_not_claim"], 2)),
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
    rows = []
    for row in payload["claim_matrix"]:
        evidence = "<br>".join(html.escape(item) for item in row["headline_numbers"])
        limits = "<br>".join(html.escape(item) for item in row["must_not_claim"])
        rows.append(
            "<tr>"
            f"<th>{html.escape(row['claim'])}</th>"
            f"<td>{html.escape(row['verdict'])}</td>"
            f"<td>{html.escape(row['readiness_level'])}</td>"
            f"<td>{evidence}</td>"
            f"<td>{limits}</td>"
            "</tr>"
        )
    path.write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paper Evidence Matrix R310</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }
    h1 { font-size: 1.6rem; margin-bottom: 0.25rem; }
    p { max-width: 900px; line-height: 1.5; }
    table { border-collapse: collapse; margin-top: 1.5rem; max-width: 1180px; }
    th, td { border: 1px solid #d8dee9; padding: 0.55rem 0.75rem; text-align: left; vertical-align: top; }
    th { background: #f6f8fa; width: 70px; }
    code { background: #f6f8fa; padding: 0.1rem 0.25rem; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>Paper Evidence Matrix R310</h1>
  <p>
    R310 reads the tracked R307 claim gate and R309 problem-value synthesis.
    It keeps the model to two abstractions: <code>operation</code> and
    <code>operation stack</code>.
  </p>
  <table>
    <tr><th>Claim</th><th>Verdict</th><th>Readiness</th><th>Evidence</th><th>Boundary</th></tr>
"""
        + "\n".join(rows)
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
    payload = build_matrix()

    json_path = args.out_dir / "evidence-matrix.json"
    md_path = args.out_dir / "evidence-matrix.md"
    csv_path = args.out_dir / "evidence-matrix.csv"
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
            "claim_count": payload["claim_count"],
            "scoped_paper_ready_claims": payload["scoped_paper_ready_claims"],
            "partial_claims": payload["partial_claims"],
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
