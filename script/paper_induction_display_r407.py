#!/usr/bin/env python3
"""R407: paper-facing display for operation-stack induction evidence.

This is a paper-integration artifact, not a new empirical experiment. It reads
tracked R402/R403/R404 operation-stack induction outputs and emits a compact
claim-facing table for the Chinese paper plus markdown/HTML/CSV/JSON evidence.
The English paper submodule is not read or modified by this script.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-induction-display-r407"
RUN_ID = "R407"
SCRIPT_PATH = Path(__file__).resolve()
CHINESE_PAPER = ROOT / "docs" / "visexp" / "paper" / "main.tex"
TABLE_INPUT = r"\input{../out/paper-induction-display-r407/induction-claim-table.tex}"

SOURCES = {
    "Chinese paper draft": CHINESE_PAPER,
    "R402 run result": OUT_ROOT / "rust-task-stack-induction-r402" / "run-result.json",
    "R402 summary": OUT_ROOT / "rust-task-stack-induction-r402" / "summary.json",
    "R403 run result": OUT_ROOT / "operation-induced-stack-scoring-r403" / "run-result.json",
    "R403 report": OUT_ROOT / "operation-induced-stack-scoring-r403" / "induced-stack-scoring-report.json",
    "R404 run result": OUT_ROOT / "operation-induced-depth-sensitivity-r404" / "run-result.json",
    "R404 report": OUT_ROOT / "operation-induced-depth-sensitivity-r404" / "depth-sensitivity-report.json",
    "R406 English sync packet": OUT_ROOT / "paper-english-induction-sync-r406" / "english-induction-sync.json",
}

ROW_FIELDS = [
    "paper_block",
    "question",
    "evidence",
    "main_numbers",
    "supported_conclusion",
    "non_claim",
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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    )
    return result.stdout.strip()


def git_status(path: Path) -> str:
    try:
        display = str(path.resolve().relative_to(ROOT))
    except ValueError:
        display = str(path)
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", display],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tracked.returncode != 0:
        return "untracked_or_missing"
    unstaged = subprocess.run(["git", "diff", "--quiet", "--", display], cwd=ROOT, check=False)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet", "--", display], cwd=ROOT, check=False)
    return "tracked_clean" if unstaged.returncode == 0 and staged.returncode == 0 else "tracked_dirty_allowed"


def source_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for name, path in {"generator script": SCRIPT_PATH, **SOURCES}.items():
        rows.append(
            {
                "source": name,
                "path": rel(path),
                "status": git_status(path),
                "sha256": sha256(path) if path.exists() else "",
            }
        )
    return rows


def row_by(report: dict[str, Any], **matches: Any) -> dict[str, Any]:
    for row in report["policy_summary"]:
        if all(row.get(key) == value for key, value in matches.items()):
            return row
    raise KeyError(matches)


def depth_row(report: dict[str, Any], depth: int, ranker: str = "query_aware") -> dict[str, Any]:
    for row in report["depth_summary"]:
        if int(row["max_depth"]) == depth and row["ranker"] == ranker:
            return row
    raise KeyError((depth, ranker))


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def hist_text(hist: dict[str, Any]) -> str:
    return "/".join(f"{depth}:{count}" for depth, count in sorted(hist.items(), key=lambda item: int(item[0])))


def tex_escape(value: str) -> str:
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
    return "".join(replacements.get(ch, ch) for ch in value)


def build_packet() -> dict[str, Any]:
    paper = read_text(CHINESE_PAPER)
    r402_run = read_json(SOURCES["R402 run result"])
    r402_summary = read_json(SOURCES["R402 summary"])
    r403_run = read_json(SOURCES["R403 run result"])
    r403 = read_json(SOURCES["R403 report"])
    r404_run = read_json(SOURCES["R404 run result"])
    r404 = read_json(SOURCES["R404 report"])
    r406 = read_json(SOURCES["R406 English sync packet"])

    overview = r402_summary["agentreward-overview"]
    session = r402_summary["agentreward-session"]
    induced = row_by(r403, view="induced_operation_stack", ranker="query_aware")
    hand = row_by(r403, view="operation_stack", ranker="query_aware")
    flat = row_by(r403, view="flat", ranker="width")
    fixed = row_by(r403, view="fixed_session", ranker="query_aware")
    variable_tasks = sum(1 for view in r403["views"] if view["variable_depth"])
    stopped_tasks = sum(1 for view in r403["views"] if not view["variable_depth"])
    depth3 = depth_row(r404, 3)
    depth5 = depth_row(r404, 5)
    material_best_depths = sorted(
        {
            int(row["best_average_precision_depth"])
            for row in r404["best_depth_by_task"]
            if float(row["average_precision_span"]) > 0.0001
        }
    )

    rows = [
        {
            "paper_block": "E1 recursive formation",
            "question": "Can the profiler form recursive operation stacks without a user-supplied field chain?",
            "evidence": "Rust induction replay over one tracked AgentRewardBench slice.",
            "main_numbers": (
                f"{overview['operations']} operations; {overview['unique_stacks']} induced stacks; "
                f"depth histogram {hist_text(overview['stack_depth_histogram'])}; session-as-evidence view has {session['unique_stacks']} stacks."
            ),
            "supported_conclusion": "Visible boundary evidence can induce ragged operation-only stacks, and session remains optional evidence.",
            "non_claim": "Not automatic discovery of all intent boundaries.",
        },
        {
            "paper_block": "E2 localization ablation",
            "question": "Do induced stacks work as a visible profiler view on real hidden-label tasks?",
            "evidence": "The induced view is scored on the same six R300/R320 labeled tasks as the main benchmark.",
            "main_numbers": (
                f"{variable_tasks}/6 variable-depth tasks, {stopped_tasks}/6 material-stop tasks; "
                f"AP {fmt(induced['median_average_precision'])} vs hand-configured {fmt(hand['median_average_precision'])}; "
                f"work@5 {fmt(induced['median_top5_work'])} vs flat {fmt(flat['median_top5_work'])}; "
                f"groups {fmt(induced['median_groups'])} vs fixed-session {fmt(fixed['median_groups'])}."
            ),
            "supported_conclusion": "Induction reduces flat work and fixed-session fragmentation, but hand-configured specs remain stronger by AP.",
            "non_claim": "Not a replacement for task-specific profile specs.",
        },
        {
            "paper_block": "E3 depth actionability",
            "question": "Is induced-stack depth a real tuning surface?",
            "evidence": "The depth cap is swept from 1 to 5 while hidden labels are used only after profiling.",
            "main_numbers": (
                f"best query-aware median AP at depth 3 ({fmt(depth3['median_average_precision'])}); "
                f"lowest median work@5 at depth 5 ({fmt(depth5['median_top5_work'])}); "
                f"material-split AP-best depths span {', '.join(map(str, material_best_depths))}."
            ),
            "supported_conclusion": "Different objectives prefer different recursive depths, so depth is a profile-configuration knob.",
            "non_claim": "Not an automatic depth selector or analyst-productivity result.",
        },
    ]

    checks = [
        {
            "check": "r402_passed",
            "passed": r402_run.get("status") == "pass",
            "detail": "R402 run-result reports pass.",
        },
        {
            "check": "r403_passed",
            "passed": r403_run.get("status") == "pass" and r403.get("status") == "pass",
            "detail": "R403 run-result and report both pass.",
        },
        {
            "check": "r404_passed",
            "passed": r404_run.get("status") == "pass" and r404.get("status") == "pass",
            "detail": "R404 run-result and report both pass.",
        },
        {
            "check": "r406_passed",
            "passed": all(check["passed"] for check in r406["checks"]),
            "detail": "The read-only English sync packet has no failing checks.",
        },
        {
            "check": "table_has_three_claim_rows",
            "passed": len(rows) == 3 and {row["paper_block"] for row in rows} == {
                "E1 recursive formation",
                "E2 localization ablation",
                "E3 depth actionability",
            },
            "detail": "The display is organized as three claim-facing rows, not a run ledger.",
        },
        {
            "check": "non_claim_boundaries_present",
            "passed": all(row["non_claim"].startswith("Not ") for row in rows),
            "detail": "Each table row carries an explicit non-claim.",
        },
        {
            "check": "chinese_paper_inputs_table",
            "passed": TABLE_INPUT in paper,
            "detail": "The Chinese paper inputs the generated R407 table fragment.",
        },
    ]

    return {
        "run_id": RUN_ID,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": git_commit(),
        "scope": "paper-facing display over existing R402/R403/R404 artifacts; no new empirical experiment",
        "rows": rows,
        "checks": checks,
        "source_status": source_rows(),
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_table(path: Path, rows: list[dict[str, str]]) -> None:
    lines = [
        r"\begin{table*}[t]",
        r"  \centering",
        r"  \small",
        r"  \caption{自动 operation-stack induction 的 claim-facing 证据。该表把 R402--R404 组织为机制、定位消融和深度调优三条证据；hidden labels 只在 profiling 后评分。}",
        r"  \label{tab:induction-display}",
        r"  \begin{tabular}{p{0.18\textwidth}p{0.24\textwidth}p{0.29\textwidth}p{0.21\textwidth}}",
        r"    \toprule",
        r"    证据块 & Reviewer question & 主要数字 & 支持的结论 / 边界 \\",
        r"    \midrule",
    ]
    for row in rows:
        conclusion = f"{row['supported_conclusion']} {row['non_claim']}"
        lines.append(
            "    "
            + " & ".join(
                [
                    tex_escape(row["paper_block"]),
                    tex_escape(row["question"]),
                    tex_escape(row["main_numbers"]),
                    tex_escape(conclusion),
                ]
            )
            + r" \\"
        )
    lines.extend([r"    \bottomrule", r"  \end{tabular}", r"\end{table*}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_markdown(path: Path, packet: dict[str, Any]) -> None:
    lines = [
        "# R407 Paper Induction Display",
        "",
        "This artifact converts existing R402/R403/R404 induction evidence into one claim-facing paper table.",
        "It is not a new empirical experiment.",
        "",
        f"- Status: {'pass' if all(check['passed'] for check in packet['checks']) else 'fail'}",
        f"- Git commit: `{packet['git_commit']}`",
        "",
        "| Paper block | Question | Evidence | Main numbers | Supported conclusion | Non-claim |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in packet["rows"]:
        lines.append("| " + " | ".join(str(row[field]).replace("|", "\\|") for field in ROW_FIELDS) + " |")
    lines.extend(["", "## Checks", "", "| Check | Passed | Detail |", "| --- | --- | --- |"])
    for check in packet["checks"]:
        lines.append(f"| {check['check']} | {check['passed']} | {check['detail']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, packet: dict[str, Any]) -> None:
    status = "pass" if all(check["passed"] for check in packet["checks"]) else "fail"
    row_html = "\n".join(
        "<tr>" + "".join(f"<td>{html.escape(str(row[field]))}</td>" for field in ROW_FIELDS) + "</tr>"
        for row in packet["rows"]
    )
    check_html = "\n".join(
        f"<tr><td>{html.escape(check['check'])}</td><td>{check['passed']}</td><td>{html.escape(check['detail'])}</td></tr>"
        for check in packet["checks"]
    )
    path.write_text(
        f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{RUN_ID} induction display</title>
  <style>
    body {{ font-family: sans-serif; margin: 2rem; line-height: 1.45; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #ccc; padding: 0.35rem; vertical-align: top; }}
  </style>
</head>
<body>
  <h1>{RUN_ID} Paper Induction Display</h1>
  <p>Status: <strong>{status}</strong>. Existing R402/R403/R404 evidence only; no new empirical run.</p>
  <table>
    <thead><tr>{''.join(f'<th>{html.escape(field)}</th>' for field in ROW_FIELDS)}</tr></thead>
    <tbody>{row_html}</tbody>
  </table>
  <h2>Checks</h2>
  <table>
    <thead><tr><th>Check</th><th>Passed</th><th>Detail</th></tr></thead>
    <tbody>{check_html}</tbody>
  </table>
</body>
</html>
""",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    packet = build_packet()
    passed = all(check["passed"] for check in packet["checks"])

    (out_dir / "induction-display.json").write_text(
        json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(out_dir / "induction-display.csv", packet["rows"], ROW_FIELDS)
    write_csv(out_dir / "induction-display-checks.csv", packet["checks"], ["check", "passed", "detail"])
    write_csv(out_dir / "source-status.csv", packet["source_status"], ["source", "path", "status", "sha256"])
    write_table(out_dir / "induction-claim-table.tex", packet["rows"])
    write_markdown(out_dir / "induction-display.md", packet)
    write_html(out_dir / "index.html", packet)
    run_result = {
        "run_id": RUN_ID,
        "status": "pass" if passed else "fail",
        "out_dir": rel(out_dir),
        "checks": {
            "checks_passed": sum(1 for check in packet["checks"] if check["passed"]),
            "checks_total": len(packet["checks"]),
        },
    }
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(run_result, indent=2, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
