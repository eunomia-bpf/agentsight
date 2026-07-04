#!/usr/bin/env python3
"""R312: audit paper submission claims against R310/R311 evidence.

R312 does not fetch datasets or rerun profiling experiments. It reads the
tracked R310/R311 audit artifacts plus the current Chinese draft, then checks
whether the paper carries the scoped evidence, guardrails, and two-abstraction
boundary needed for a submission-quality argument.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-submission-audit-r312"
SOURCE_PATHS = {
    "r310_evidence_matrix": OUT_ROOT
    / "paper-evidence-matrix-r310"
    / "evidence-matrix.json",
    "r311_robustness_audit": OUT_ROOT
    / "paper-robustness-audit-r311"
    / "robustness-audit.json",
    "paper_main_tex": ROOT / "docs" / "visexp" / "paper" / "main.tex",
}

NEGATION_MARKERS = [
    "不支持",
    "不能",
    "不是",
    "不引入",
    "不增加",
    "不新增",
    "不证明",
    "仍需",
    "仍是后续",
    "后续工作",
    "下一步",
    "排除",
    "缺口",
    "限制",
    "not ",
    "not-",
    "future work",
    "unsupported",
    "must-not",
    "fail-for-stronger",
    "narrow",
    "only after",
]


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


def ensure_artifacts_tracked_clean(paths: list[Path]) -> None:
    for path in paths:
        if not path.exists():
            raise SystemExit(f"missing source artifact {rel(path)}")
        git_check("source artifact is not git-tracked", ["ls-files", "--error-unmatch"], path)
        git_check("source artifact has unstaged changes", ["diff", "--quiet"], path)
        git_check("source artifact has staged changes", ["diff", "--cached", "--quiet"], path)


def ensure_tracked(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"missing source file {rel(path)}")
    git_check("source file is not git-tracked", ["ls-files", "--error-unmatch"], path)


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def find_lines(text: str, pattern: str) -> list[int]:
    regex = re.compile(pattern)
    return [index for index, line in enumerate(text.splitlines(), start=1) if regex.search(line)]


def has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def guarded_occurrences(text: str, pattern: str) -> dict[str, Any]:
    regex = re.compile(pattern, re.IGNORECASE)
    occurrences = []
    unguarded = []
    for index, line in enumerate(text.splitlines(), start=1):
        if regex.search(line):
            item = {"line": index, "text": line.strip()}
            occurrences.append(item)
            lower = line.lower()
            if not any(marker in lower for marker in NEGATION_MARKERS):
                unguarded.append(item)
    return {
        "pattern": pattern,
        "occurrences": occurrences,
        "unguarded": unguarded,
        "status": "pass" if not unguarded else "fail",
    }


def required_number_checks(text: str, r310: dict[str, Any], r311: dict[str, Any]) -> list[dict[str, Any]]:
    metrics = r310["problem_value_metrics"]
    summary = r311["summary"]
    checks = [
        ("datasets", str(metrics["datasets"]), "R310 problem-value dataset count"),
        ("tasks", str(metrics["tasks"]), "R310/R311 analysis task count"),
        ("operations", f"{metrics['operations']:,}", "R310/R311 operation count"),
        ("positives", f"{metrics['positive_operations']:,}", "R310 positive-operation count"),
        (
            "more_selective_than_flat",
            summary["operation_stack_more_selective_than_flat"],
            "R311 operation-stack selectivity over flat",
        ),
        (
            "positive_group_coverage",
            summary["operation_stack_positive_group_coverage"],
            "R311 positive-group coverage",
        ),
        (
            "high_lift_coverage",
            summary["operation_stack_high_lift_coverage"],
            "R311 high-lift coverage",
        ),
        (
            "higher_recall_than_fixed",
            summary["operation_stack_higher_recall_than_fixed"],
            "R311 selected-recall comparison",
        ),
        (
            "lower_work_than_fixed",
            summary["operation_stack_lower_work_than_fixed"],
            "R311 selected-work comparison",
        ),
        (
            "fixed_lower_work_counterpoint",
            summary["fixed_session_lower_work_counterpoint"],
            "R311 fixed-session lower-work counterpoint",
        ),
    ]
    rows = []
    for key, needle, source in checks:
        rows.append(
            {
                "key": key,
                "expected_text": needle,
                "source": source,
                "status": "pass" if needle in text else "fail",
                "lines": find_lines(text, re.escape(needle)),
            }
        )
    return rows


def two_abstraction_checks(text: str) -> list[dict[str, Any]]:
    return [
        {
            "check": "declares_two_core_abstractions",
            "status": "pass"
            if has_any(text, [r"两个核心抽象", r"two[- ]object", r"two abstractions"])
            else "fail",
            "evidence_lines": find_lines(text, r"两个核心抽象|two[- ]object|two abstractions"),
        },
        {
            "check": "operation_named",
            "status": "pass" if "operation" in text else "fail",
            "evidence_lines": find_lines(text, r"operation"),
        },
        {
            "check": "operation_stack_named",
            "status": "pass" if "operation stack" in text or "operation-stack" in text else "fail",
            "evidence_lines": find_lines(text, r"operation stack|operation-stack"),
        },
        {
            "check": "third_abstraction_only_guarded",
            "status": guarded_occurrences(text, r"第三个抽象|third abstraction")["status"],
            "evidence_lines": find_lines(text, r"第三个抽象|third abstraction"),
        },
    ]


def guardrail_checks(text: str) -> list[dict[str, Any]]:
    patterns = [
        ("human_utility", r"human utility|人类用户效用|开发者效率|developer productivity"),
        ("automatic_detection", r"automatic detection|自动异常检测|detector"),
        ("unsupervised_boundary", r"unsupervised|无监督"),
        ("fixed_session_dominance", r"universal fixed-session dominance|无条件支配|支配 fixed-session"),
        ("trace_ecosystem", r"complete trace-ecosystem|完整.*生态兼容|OpenTelemetry/Chrome"),
    ]
    rows = []
    for key, pattern in patterns:
        guarded = guarded_occurrences(text, pattern)
        rows.append(
            {
                "key": key,
                "pattern": pattern,
                "status": guarded["status"] if guarded["occurrences"] else "warn_missing_guardrail",
                "occurrence_count": len(guarded["occurrences"]),
                "unguarded": guarded["unguarded"],
            }
        )
    return rows


def paper_style_checks(text: str) -> list[dict[str, Any]]:
    run_mentions = len(re.findall(r"\bR\d{3}\b", text))
    table_rows = len(re.findall(r"\\\\", text))
    return [
        {
            "check": "run_id_density",
            "value": run_mentions,
            "status": "warn" if run_mentions > 90 else "pass",
            "interpretation": (
                "The draft is still artifact-log heavy; paper integration should "
                "move more RIDs into tables or appendices."
                if run_mentions > 90
                else "Run-ID density is acceptable for the current draft."
            ),
        },
        {
            "check": "large_table_density",
            "value": table_rows,
            "status": "warn" if table_rows > 45 else "pass",
            "interpretation": (
                "The draft relies heavily on dense tables; a final paper should "
                "compress result inventory into fewer reviewer-facing tables."
                if table_rows > 45
                else "Table density is acceptable for the current draft."
            ),
        },
    ]


def claim_alignment(r310: dict[str, Any], r311: dict[str, Any]) -> list[dict[str, Any]]:
    r311_summary = r311["summary"]
    return [
        {
            "claim": "C1",
            "status": "scoped_ready",
            "paper_use": "mechanism claim",
            "evidence": "R310 marks C1 scoped paper-ready; R312 checks that the draft states operation/operation-stack as the core model.",
            "remaining_gap": "Import a real external OpenTelemetry GenAI or Perfetto trace before claiming ecosystem compatibility.",
        },
        {
            "claim": "C2",
            "status": "scoped_ready",
            "paper_use": "recursive stack-depth claim",
            "evidence": "R310 marks C2 scoped paper-ready; R312 checks the draft keeps stack depth as a query over operation fields.",
            "remaining_gap": "Deeper sequence/subtask boundary evidence would expand the claim.",
        },
        {
            "claim": "C3",
            "status": "partial",
            "paper_use": "extension-point claim only",
            "evidence": "R310 keeps C3 partial, and R312 checks that unsupervised boundary discovery remains guarded.",
            "remaining_gap": "Calibrated boundary backends and simple-baseline comparisons on another family.",
        },
        {
            "claim": "C4",
            "status": "automated_proxy_ready",
            "paper_use": "inspectability-tradeoff claim",
            "evidence": (
                f"R311 reports flat selectivity {r311_summary['operation_stack_more_selective_than_flat']}, "
                f"high-lift {r311_summary['operation_stack_high_lift_coverage']}, "
                f"higher recall than fixed {r311_summary['operation_stack_higher_recall_than_fixed']}, "
                f"and lower work than fixed only {r311_summary['operation_stack_lower_work_than_fixed']}."
            ),
            "remaining_gap": "Controlled human/agent analyst study before user-utility wording.",
        },
    ]


def status_from_rows(rows: list[dict[str, Any]]) -> str:
    statuses = {row["status"] for row in rows}
    if "fail" in statuses:
        return "fail"
    if any(status.startswith("warn") or status == "warn" for status in statuses):
        return "warn"
    return "pass"


def readiness_summary(
    number_rows: list[dict[str, Any]],
    abstraction_rows: list[dict[str, Any]],
    guardrail_rows: list[dict[str, Any]],
    style_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    checks = {
        "number_alignment": status_from_rows(number_rows),
        "two_abstraction_boundary": status_from_rows(abstraction_rows),
        "must_not_claim_guardrails": status_from_rows(guardrail_rows),
        "paper_structure": status_from_rows(style_rows),
    }
    blocking = [key for key, value in checks.items() if value == "fail"]
    warnings = [key for key, value in checks.items() if value == "warn"]
    if blocking:
        overall = "needs_work"
    elif warnings:
        overall = "scoped_claim_ready_but_paper_needs_structure_polish"
    else:
        overall = "scoped_claim_ready"
    return {
        "overall": overall,
        "checks": checks,
        "blocking": blocking,
        "warnings": warnings,
        "submission_position": (
            "The scoped mechanism and automated inspectability claims are aligned "
            "with R310/R311 evidence, but the draft should not be treated as a "
            "full OSDI/NeurIPS submission until paper-structure polish and the "
            "controlled analyst-study gap are addressed."
        ),
    }


def build_payload() -> dict[str, Any]:
    ensure_artifacts_tracked_clean(
        [
            SOURCE_PATHS["r310_evidence_matrix"],
            SOURCE_PATHS["r311_robustness_audit"],
        ]
    )
    ensure_tracked(SOURCE_PATHS["paper_main_tex"])
    r310 = load_json(SOURCE_PATHS["r310_evidence_matrix"])
    r311 = load_json(SOURCE_PATHS["r311_robustness_audit"])
    paper_text = SOURCE_PATHS["paper_main_tex"].read_text(encoding="utf-8")

    number_rows = required_number_checks(paper_text, r310, r311)
    abstraction_rows = two_abstraction_checks(paper_text)
    guardrail_rows = guardrail_checks(paper_text)
    style_rows = paper_style_checks(paper_text)

    return {
        "schema": "agentsight.paper-submission-audit.v1",
        "run_id": "R312",
        "commit": git_output(["rev-parse", "HEAD"]),
        "input_policy": {
            "dataset_sync": "none",
            "source_artifacts": {key: rel(path) for key, path in SOURCE_PATHS.items()},
            "clean_requirement": "R310/R311 audit artifacts must be git-tracked and clean; the paper draft is read from the current worktree and hashed.",
            "purpose": "paper claim/evidence/guardrail audit only; no new empirical result",
        },
        "profiler_abstractions": ["operation", "operation stack"],
        "paper_hash": text_hash(paper_text),
        "claim_alignment": claim_alignment(r310, r311),
        "number_alignment_checks": number_rows,
        "two_abstraction_checks": abstraction_rows,
        "guardrail_checks": guardrail_rows,
        "paper_style_checks": style_rows,
        "readiness_summary": readiness_summary(
            number_rows,
            abstraction_rows,
            guardrail_rows,
            style_rows,
        ),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["readiness_summary"]
    lines = [
        "# Paper Submission Audit R312",
        "",
        "R312 audits the current Chinese draft against the R310/R311 evidence. It does not sync datasets or rerun profilers.",
        "",
        "## Readiness",
        "",
        f"- Overall: {summary['overall']}.",
        f"- Number alignment: {summary['checks']['number_alignment']}.",
        f"- Two-abstraction boundary: {summary['checks']['two_abstraction_boundary']}.",
        f"- Must-not-claim guardrails: {summary['checks']['must_not_claim_guardrails']}.",
        f"- Paper structure: {summary['checks']['paper_structure']}.",
        f"- Position: {summary['submission_position']}",
        "",
        "## Claim Alignment",
        "",
        "| Claim | Status | Paper use | Remaining gap |",
        "|---|---|---|---|",
    ]
    for row in payload["claim_alignment"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["claim"],
                    row["status"],
                    row["paper_use"],
                    row["remaining_gap"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Number Checks",
            "",
            "| Key | Expected text | Status | Lines |",
            "|---|---|---|---|",
        ]
    )
    for row in payload["number_alignment_checks"]:
        lines.append(
            f"| {row['key']} | {row['expected_text']} | {row['status']} | {', '.join(map(str, row['lines'])) or 'missing'} |"
        )
    lines.extend(
        [
            "",
            "## Guardrail Checks",
            "",
            "| Key | Status | Occurrences | Unguarded |",
            "|---|---|---|---|",
        ]
    )
    for row in payload["guardrail_checks"]:
        unguarded = ", ".join(str(item["line"]) for item in row["unguarded"]) or "none"
        lines.append(
            f"| {row['key']} | {row['status']} | {row['occurrence_count']} | {unguarded} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["category", "key", "status", "detail"])
        writer.writeheader()
        for row in payload["number_alignment_checks"]:
            writer.writerow(
                {
                    "category": "number_alignment",
                    "key": row["key"],
                    "status": row["status"],
                    "detail": row["expected_text"],
                }
            )
        for row in payload["two_abstraction_checks"]:
            writer.writerow(
                {
                    "category": "two_abstraction",
                    "key": row["check"],
                    "status": row["status"],
                    "detail": ",".join(map(str, row["evidence_lines"][:8])),
                }
            )
        for row in payload["guardrail_checks"]:
            writer.writerow(
                {
                    "category": "guardrail",
                    "key": row["key"],
                    "status": row["status"],
                    "detail": f"occurrences={row['occurrence_count']}; unguarded={len(row['unguarded'])}",
                }
            )
        for row in payload["paper_style_checks"]:
            writer.writerow(
                {
                    "category": "paper_style",
                    "key": row["check"],
                    "status": row["status"],
                    "detail": row["interpretation"],
                }
            )


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


def write_tex(path: Path, payload: dict[str, Any]) -> None:
    rows = payload["readiness_summary"]["checks"]
    lines = [
        r"\begin{table}[t]",
        r"  \centering",
        r"  \scriptsize",
        r"  \caption{R312 paper submission audit over the current Chinese draft.}",
        r"  \label{tab:r312-submission-audit}",
        r"  \begin{tabular}{p{0.44\linewidth}p{0.38\linewidth}}",
        r"    \toprule",
        r"    Check & Status \\",
        r"    \midrule",
    ]
    for key, value in rows.items():
        lines.append(f"    {tex_escape(key)} & {tex_escape(value)} \\\\")
    lines.extend(
        [
            r"    \bottomrule",
            r"  \end{tabular}",
            r"\end{table}",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    checks = payload["readiness_summary"]["checks"]
    check_rows = "\n".join(
        f"<tr><th>{html.escape(key)}</th><td>{html.escape(value)}</td></tr>"
        for key, value in checks.items()
    )
    number_rows = "\n".join(
        "<tr>"
        f"<th>{html.escape(row['key'])}</th>"
        f"<td>{html.escape(row['expected_text'])}</td>"
        f"<td>{html.escape(row['status'])}</td>"
        f"<td>{html.escape(', '.join(map(str, row['lines'])) or 'missing')}</td>"
        "</tr>"
        for row in payload["number_alignment_checks"]
    )
    path.write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paper Submission Audit R312</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }
    h1 { font-size: 1.6rem; margin-bottom: 0.25rem; }
    table { border-collapse: collapse; margin-top: 1rem; max-width: 1100px; }
    th, td { border: 1px solid #d8dee9; padding: 0.55rem 0.75rem; text-align: left; vertical-align: top; }
    th { background: #f6f8fa; }
  </style>
</head>
<body>
  <h1>Paper Submission Audit R312</h1>
  <p>R312 checks the current Chinese draft against R310/R311 evidence without syncing datasets.</p>
  <h2>Readiness</h2>
  <table>
    <tr><th>Check</th><th>Status</th></tr>
"""
        + check_rows
        + """
  </table>
  <h2>Number Checks</h2>
  <table>
    <tr><th>Key</th><th>Expected</th><th>Status</th><th>Lines</th></tr>
"""
        + number_rows
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

    json_path = args.out_dir / "submission-audit.json"
    md_path = args.out_dir / "submission-audit.md"
    csv_path = args.out_dir / "submission-audit.csv"
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
            "overall": payload["readiness_summary"]["overall"],
            "checks": payload["readiness_summary"]["checks"],
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
