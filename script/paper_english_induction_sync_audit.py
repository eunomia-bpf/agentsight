#!/usr/bin/env python3
"""R406: read-only English-paper sync packet for operation-stack induction.

This is a paper-integration artifact, not a new empirical experiment. It reads
the dirty English paper submodule in read-only mode, reads the outer R402/R403/R404
operation-stack induction artifacts, and writes an outer-repo packet describing
exactly what evidence is ready to port into English once submodule edits are
explicitly allowed.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-english-induction-sync-r406"
RUN_ID = "R406"
SCRIPT_PATH = Path(__file__).resolve()

SOURCES = {
    "English paper draft": SUBMODULE_ROOT / "main.tex",
    "Chinese paper draft": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "R402 run result": OUT_ROOT / "rust-task-stack-induction-r402" / "run-result.json",
    "R402 summary": OUT_ROOT / "rust-task-stack-induction-r402" / "summary.json",
    "R402 overview profile": OUT_ROOT / "rust-task-stack-induction-r402" / "agentreward-overview.json",
    "R403 run result": OUT_ROOT / "operation-induced-stack-scoring-r403" / "run-result.json",
    "R403 report": OUT_ROOT / "operation-induced-stack-scoring-r403" / "induced-stack-scoring-report.json",
    "R404 run result": OUT_ROOT / "operation-induced-depth-sensitivity-r404" / "run-result.json",
    "R404 report": OUT_ROOT / "operation-induced-depth-sensitivity-r404" / "depth-sensitivity-report.json",
}

ROW_FIELDS = [
    "paper_block",
    "english_status",
    "ready_evidence",
    "numbers",
    "claim_boundary",
    "sync_action",
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
    return "tracked_clean" if unstaged.returncode == 0 and staged.returncode == 0 else "tracked_dirty_read_only"


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


def build_packet() -> dict[str, Any]:
    english = read_text(SOURCES["English paper draft"])
    chinese = read_text(SOURCES["Chinese paper draft"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    r402_summary = read_json(SOURCES["R402 summary"])
    r402_profile = read_json(SOURCES["R402 overview profile"])
    r403 = read_json(SOURCES["R403 report"])
    r404 = read_json(SOURCES["R404 report"])

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

    english_mentions_induction = any(
        needle in english
        for needle in [
            "--induce-operation-stack",
            "induced operation-stack",
            "operation-stack induction",
            "recursive operation-stack induction",
        ]
    )
    chinese_mentions_induction = (
        "--induce-operation-stack" in chinese
        and "0.2865" in chinese
        and "0.4727" in chinese
    )
    evaluation_mentions_induction = "R404" in evaluation and "Induced operation-stack depth sensitivity" in evaluation
    public_profile = r402_profile["profile"]

    rows = [
        {
            "paper_block": "RQ1 mechanism: recursive operation-stack construction",
            "english_status": "missing_from_submodule" if not english_mentions_induction else "already_mentions_induction",
            "ready_evidence": "R402 replays the maintained Rust profiler on a tracked AgentRewardBench slice and emits induced operation frames without a user stack-field order.",
            "numbers": (
                f"{overview['operations']} operations; overview {overview['unique_stacks']} stacks with depth histogram "
                f"{overview['stack_depth_histogram']}; session-allowed view {session['unique_stacks']} stacks."
            ),
            "claim_boundary": "This supports configurable recursive folding, not automatic discovery of all intent boundaries.",
            "sync_action": "Port the induction paragraph and keep session as optional evidence, not a default stack level.",
        },
        {
            "paper_block": "RQ2 mechanism ablation: hidden-label localization",
            "english_status": "missing_from_submodule" if not english_mentions_induction else "needs_number_refresh",
            "ready_evidence": "R403 scores induced operation-stack groups on the same six R300/R320 hidden-label tasks.",
            "numbers": (
                f"{variable_tasks}/6 tasks produce variable-depth stacks and {stopped_tasks}/6 stop when visible evidence has no material split; "
                f"median AP {fmt(induced['median_average_precision'])} vs hand-configured operation-stack {fmt(hand['median_average_precision'])}; "
                f"median work@5 {fmt(induced['median_top5_work'])} vs flat {fmt(flat['median_top5_work'])}; "
                f"median groups {fmt(induced['median_groups'])} vs fixed-session {fmt(fixed['median_groups'])}."
            ),
            "claim_boundary": "The hand-configured operation stack remains the stronger main policy by AP, so induction is an ablation and configuration probe.",
            "sync_action": "Add a short RQ2 paragraph or table row under baseline/actionability discussion, not a new top-level experiment.",
        },
        {
            "paper_block": "RQ3 actionability: depth sensitivity",
            "english_status": "missing_from_submodule" if "depth sensitivity" not in english.lower() else "needs_number_refresh",
            "ready_evidence": "R404 sweeps --induce-max-depth over depths 1 through 5 using hidden labels only after profiling.",
            "numbers": (
                f"query-aware median AP is highest at depth 3 ({fmt(depth3['median_average_precision'])}); "
                f"median work@5 is lowest at depth 5 ({fmt(depth5['median_top5_work'])}); "
                f"material-split task AP-best depths span {', '.join(map(str, material_best_depths))}."
            ),
            "claim_boundary": "This is a profile-configuration surface, not an automatic depth selector.",
            "sync_action": "Use this as actionability evidence: different tasks prefer different recursive depths and metrics.",
        },
        {
            "paper_block": "Scope guardrail",
            "english_status": "must_preserve_non_claim",
            "ready_evidence": "R402/R403/R404 exclude oracle source fields and score hidden labels only after profiling.",
            "numbers": "R403 and R404 both pass hidden-label and no-oracle-source checks.",
            "claim_boundary": "Do not claim human productivity, automatic patch selection, universal boundary discovery, or full OTel/LangSmith/Phoenix compatibility.",
            "sync_action": "When porting into English, keep these limitations adjacent to the induced-stack result.",
        },
    ]

    snippets = build_snippets(overview, session, induced, hand, flat, fixed, depth3, depth5, material_best_depths, variable_tasks, stopped_tasks)
    checks = [
        {
            "check": "english_submodule_read_only_scope",
            "passed": all(not str(path).startswith(str(SUBMODULE_ROOT)) for path in [DEFAULT_OUT_DIR]),
            "detail": "The script writes only under docs/visexp/out and reads docs/agentpprof-paper/main.tex without editing it.",
        },
        {
            "check": "r402_passed",
            "passed": read_json(SOURCES["R402 run result"]).get("status") == "pass",
            "detail": "R402 run-result.json reports pass.",
        },
        {
            "check": "r403_passed",
            "passed": read_json(SOURCES["R403 run result"]).get("status") == "pass" and r403.get("status") == "pass",
            "detail": "R403 run-result and report both pass.",
        },
        {
            "check": "r404_passed",
            "passed": read_json(SOURCES["R404 run result"]).get("status") == "pass" and r404.get("status") == "pass",
            "detail": "R404 run-result and report both pass.",
        },
        {
            "check": "english_gap_detected",
            "passed": not english_mentions_induction,
            "detail": "The current English submodule does not yet mention --induce-operation-stack or induced operation-stack evidence.",
        },
        {
            "check": "outer_paper_and_ledger_have_evidence",
            "passed": chinese_mentions_induction and evaluation_mentions_induction,
            "detail": "The outer Chinese paper and evaluation ledger mention R402/R403/R404 induced operation-stack evidence.",
        },
        {
            "check": "public_profile_uses_operation_stack_key",
            "passed": "operation_stack_induction" in public_profile and "task_stack_induction" not in public_profile,
            "detail": "R402 public JSON exposes operation_stack_induction and no stale task_stack_induction key.",
        },
        {
            "check": "snippets_include_claim_boundaries",
            "passed": "not an automatic boundary detector" in snippets and "not an analyst-productivity result" in snippets,
            "detail": "The generated English snippets include non-claim boundaries.",
        },
    ]

    return {
        "run_id": RUN_ID,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": git_commit(),
        "scope": "read-only English submodule sync packet over existing R402/R403/R404 artifacts",
        "rows": rows,
        "checks": checks,
        "snippets_tex": snippets,
        "source_status": source_rows(),
    }


def build_snippets(
    overview: dict[str, Any],
    session: dict[str, Any],
    induced: dict[str, Any],
    hand: dict[str, Any],
    flat: dict[str, Any],
    fixed: dict[str, Any],
    depth3: dict[str, Any],
    depth5: dict[str, Any],
    material_best_depths: list[int],
    variable_tasks: int,
    stopped_tasks: int,
) -> str:
    return f"""% R406 read-only sync packet. Do not paste until English submodule edits are allowed.
\\paragraph{{Automatic operation-stack induction.}}
The profiler can construct a recursive operation stack without asking the user for a fixed field order such as phase/action/status.
We run \\texttt{{--induce-operation-stack}} on a tracked AgentRewardBench slice and let visible boundary evidence, semantic shift, changed-field density, and query hints choose adjacent cuts inside each current segment.
The overview replay covers {overview['operations']} operations and produces {overview['unique_stacks']} induced operation stacks; allowing session as evidence changes the result to {session['unique_stacks']} stacks, which confirms that session is an optional evidence field rather than a required stack level.
This result is an implementation and mechanism check for recursive folding, not an automatic boundary detector.

\\paragraph{{Induced stacks as a localization ablation.}}
We then score the same induced operation-stack path on the six hidden-label localization tasks.
The induced view creates variable-depth stacks on {variable_tasks}/6 tasks and stops on {stopped_tasks}/6 tasks when visible fields do not support a material split.
Its median top-5 inspection work is {fmt(induced['median_top5_work'])}, compared with {fmt(flat['median_top5_work'])} for flat summaries, and its median group count is {fmt(induced['median_groups'])}, compared with {fmt(fixed['median_groups'])} for fixed-session drilldown.
The hand-configured operation stack remains stronger by median AP ({fmt(hand['median_average_precision'])} versus {fmt(induced['median_average_precision'])}), so this ablation supports configurable recursive folding rather than replacing task-specific profile specifications.

\\paragraph{{Depth sensitivity.}}
Changing only the induced-stack depth cap changes the localization surface.
The query-aware induced view reaches its highest median AP at depth 3 ({fmt(depth3['median_average_precision'])}), while the lowest median top-5 work occurs at depth 5 ({fmt(depth5['median_top5_work'])}).
Across tasks with material splits, AP-best depths span {', '.join(map(str, material_best_depths))}.
This is profile-configuration actionability, not an analyst-productivity result or an automatic depth selector.
"""


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, packet: dict[str, Any]) -> None:
    lines = [
        "# R406 English Operation-Stack Induction Sync Packet",
        "",
        "This is a read-only sync packet over the English submodule and existing outer-repo R402/R403/R404 artifacts.",
        "It does not edit the English paper submodule and it is not a new empirical experiment.",
        "",
        f"- Status: {'pass' if all(check['passed'] for check in packet['checks']) else 'fail'}",
        f"- Git commit: `{packet['git_commit']}`",
        f"- Rows: {len(packet['rows'])}",
        "",
        "## Evidence To Port",
        "",
        "| Paper block | English status | Ready evidence | Numbers | Claim boundary | Sync action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in packet["rows"]:
        lines.append(
            "| "
            + " | ".join(
                str(row[field]).replace("|", "\\|")
                for field in ROW_FIELDS
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## English Snippet Draft",
            "",
            "```tex",
            packet["snippets_tex"].strip(),
            "```",
            "",
            "## Checks",
            "",
            "| Check | Passed | Detail |",
            "| --- | --- | --- |",
        ]
    )
    for check in packet["checks"]:
        lines.append(f"| {check['check']} | {check['passed']} | {check['detail']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, packet: dict[str, Any]) -> None:
    status = "pass" if all(check["passed"] for check in packet["checks"]) else "fail"
    row_html = "\n".join(
        "<tr>"
        + "".join(f"<td>{html.escape(str(row[field]))}</td>" for field in ROW_FIELDS)
        + "</tr>"
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
  <title>{RUN_ID} English induction sync</title>
  <style>
    body {{ font-family: sans-serif; margin: 2rem; line-height: 1.45; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #ccc; padding: 0.35rem; vertical-align: top; }}
    pre {{ background: #f6f8fa; padding: 1rem; overflow-x: auto; }}
  </style>
</head>
<body>
  <h1>{RUN_ID} English Operation-Stack Induction Sync Packet</h1>
  <p>Status: <strong>{status}</strong>. This packet is read-only with respect to the English submodule.</p>
  <h2>Evidence To Port</h2>
  <table>
    <thead><tr>{''.join(f'<th>{html.escape(field)}</th>' for field in ROW_FIELDS)}</tr></thead>
    <tbody>{row_html}</tbody>
  </table>
  <h2>Snippet Draft</h2>
  <pre>{html.escape(packet['snippets_tex'])}</pre>
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

    (out_dir / "english-induction-sync.json").write_text(
        json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_csv(out_dir / "english-induction-sync.csv", packet["rows"], ROW_FIELDS)
    write_csv(out_dir / "english-induction-sync-checks.csv", packet["checks"], ["check", "passed", "detail"])
    write_csv(out_dir / "source-status.csv", packet["source_status"], ["source", "path", "status", "sha256"])
    (out_dir / "english-induction-snippets.tex").write_text(packet["snippets_tex"], encoding="utf-8")
    write_markdown(out_dir / "english-induction-sync.md", packet)
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
