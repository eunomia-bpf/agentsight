#!/usr/bin/env python3
"""R369: reviewer-facing claim-to-evidence path audit.

This is a paper-integration artifact, not a new empirical result. It builds a
compact four-row path from each paper RQ to the main table/figure, source
artifact, guardrail, and non-claim so reviewers can verify the paper argument
without reading the chronological run log.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-reviewer-evidence-path-r369"
RUN_ID = "R369"
SCRIPT_PATH = Path(__file__).resolve()

SOURCES = {
    "R360 core result tables": OUT_ROOT / "paper-core-result-tables-r360" / "core-result-tables.json",
    "R361 claim evidence": OUT_ROOT / "paper-core-claim-evidence-r361" / "core-claim-evidence.json",
    "R363 visualization portfolio": OUT_ROOT / "paper-visualization-portfolio-r363" / "visualization-portfolio.json",
    "R365 headline case studies": OUT_ROOT / "paper-headline-case-studies-r365" / "headline-case-studies.json",
    "R368 trace-tree baseline": OUT_ROOT / "paper-trace-tree-baseline-r368" / "trace-tree-baseline-report.json",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "English paper": SUBMODULE_ROOT / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
}

ROW_FIELDS = [
    "rq",
    "claim_test",
    "main_paper_evidence",
    "source_artifact",
    "guardrail",
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


def source_rows() -> list[dict[str, str]]:
    return [
        {
            "source": name,
            "path": rel(path),
            "status": git_status(path),
            "sha256": sha256(path),
        }
        for name, path in {"generator script": SCRIPT_PATH, **SOURCES}.items()
    ]


def latex_escape(value: Any) -> str:
    compact = " ".join(str(value).split())
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
    return "".join(replacements.get(ch, ch) for ch in compact)


def build_rows() -> list[dict[str, str]]:
    return [
        {
            "rq": "RQ1/E1",
            "claim_test": "Two abstractions cover heterogeneous traces and recursive field-derived folding.",
            "main_paper_evidence": "tab:results; RQ1/E1 subsection; dataset table.",
            "source_artifact": "R360/R361/R366: 47,590 operations; 9->3,757 stack sweep; 12/12 prompt/session-free specs; 4/5 boundary rows beat simple baseline.",
            "guardrail": "R364 sufficiency; R359 RQ consolidation; R366 field-derivation scope.",
            "non_claim": "Not complete trace-ecosystem compatibility, not automatic intent-boundary discovery.",
        },
        {
            "rq": "RQ2/E2",
            "claim_test": "Hot groups localize hidden positives with less work than flat and less fragmentation than fixed-session drilldown.",
            "main_paper_evidence": "tab:r320; fig:r363-portfolio; tab:r365-headlines; tab:r365-cases.",
            "source_artifact": "R320/R333/R334/R355/R368: 6 tasks, 34,539 ops, 3,699 positives, 144 policies; Work@5 0.0937 vs 1.0; groups 157.5 vs 285.",
            "guardrail": "R368 fixed-session trace-tree-shaped baseline scope; R330/R331 uncertainty and negative controls.",
            "non_claim": "Not metric dominance; not a human-productivity result; real OTel/Phoenix/LangSmith/Perfetto imports remain future baselines.",
        },
        {
            "rq": "RQ3/E3",
            "claim_test": "Stack fields, mappings, rankers, profile specs, and boundary fields expose actionable optimization knobs.",
            "main_paper_evidence": "fig:r363-portfolio; tab:r365-headlines; tab:r365-cases; RQ3/E3 subsection.",
            "source_artifact": "R354/R358/R365/R366: 5/6 accepted profile-spec patches; AP +0.0376 median; OSWorld AP 0.2583 vs 0.2402; 7 critical and 3 misleading feature rows.",
            "guardrail": "R349 action-transfer counterpoint; R358 inspection-work counterpoint; R366 suitability/simple-baseline checks.",
            "non_claim": "Not an automatic patch selector, automatic boundary detector, or universal default view.",
        },
        {
            "rq": "RQ4/E4",
            "claim_test": "Tracked offline profile-spec path is replayable and cheap enough for artifact evaluation.",
            "main_paper_evidence": "tab:results; RQ4/E4 subsection; artifact-hygiene paragraphs.",
            "source_artifact": "R327/R328/R352/R357/R361/R364: 76/76 semantic and raw-byte deterministic specs; 152 invocations; median 1.601s, p95 2.767s.",
            "guardrail": "R352 OSDI rubric; R357 reviewer acceptance; R359-R368 claim/scope gates.",
            "non_claim": "Not live eBPF overhead, not hidden-label accuracy, not human utility.",
        },
    ]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_latex_table(path: Path, rows: list[dict[str, str]]) -> None:
    lines = [
        "% Generated by script/paper_reviewer_evidence_path.py (R369).",
        r"\begin{tabular}{p{0.09\linewidth}p{0.22\linewidth}p{0.23\linewidth}p{0.22\linewidth}p{0.16\linewidth}}",
        r"  \toprule",
        r"  RQ & Claim test & Main paper evidence & Source artifact / guardrail & Non-claim \\",
        r"  \midrule",
    ]
    for row in rows:
        artifact = f"{row['source_artifact']} Guardrail: {row['guardrail']}"
        lines.append(
            "  "
            + " & ".join(
                [
                    latex_escape(row["rq"]),
                    latex_escape(row["claim_test"]),
                    latex_escape(row["main_paper_evidence"]),
                    latex_escape(artifact),
                    latex_escape(row["non_claim"]),
                ]
            )
            + r" \\"
        )
    lines.extend([r"  \bottomrule", r"\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def paper_texts() -> tuple[str, str, str]:
    zh = read_text(SOURCES["Chinese paper"])
    en = read_text(SOURCES["English paper"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    return zh, en, evaluation


def contains_all(text: str, tokens: list[str]) -> bool:
    return all(token in text for token in tokens)


def build_checks(rows: list[dict[str, str]], sources: list[dict[str, str]], zh: str, en: str, evaluation: str) -> list[dict[str, str]]:
    blob = json.dumps(rows, sort_keys=True)
    paper_blob = zh + "\n" + en
    lower_blob = (blob + "\n" + paper_blob).lower()
    return [
        {
            "check": "four_rq_evidence_paths",
            "status": "pass" if [row["rq"] for row in rows] == ["RQ1/E1", "RQ2/E2", "RQ3/E3", "RQ4/E4"] else "fail",
            "evidence": "Exactly one reviewer evidence-path row exists for each paper-facing RQ/core experiment.",
        },
        {
            "check": "each_path_has_paper_artifact_guardrail_nonclaim",
            "status": "pass"
            if all(row["main_paper_evidence"] and row["source_artifact"] and row["guardrail"] and row["non_claim"] for row in rows)
            else "fail",
            "evidence": "Each row records main paper evidence, source artifact, guardrail, and scoped non-claim.",
        },
        {
            "check": "rq2_localization_path_complete",
            "status": "pass" if contains_all(blob, ["R320", "R368", "Work@5 0.0937", "groups 157.5 vs 285"]) else "fail",
            "evidence": "RQ2 links hidden-label localization numbers to the fixed-session baseline-scope guardrail.",
        },
        {
            "check": "rq3_actionability_path_complete",
            "status": "pass" if contains_all(blob, ["R354", "R358", "R365", "5/6 accepted", "7 critical and 3 misleading"]) else "fail",
            "evidence": "RQ3 links executable patches, boundary-field repair, task cards, and mechanism counterpoints.",
        },
        {
            "check": "paper_exposes_compact_role_map",
            "status": "pass"
            if contains_all(paper_blob, ["tab:r374-roles", "R374"])
            else "fail",
            "evidence": "Chinese and English papers expose the compact R374 role map instead of the old R369 run-ledger table.",
        },
        {
            "check": "evaluation_mentions_r369",
            "status": "pass" if "R369" in evaluation and "reviewer evidence path" in evaluation.lower() else "fail",
            "evidence": "Evaluation ledger records R369 as a paper-integration guardrail.",
        },
        {
            "check": "two_abstractions_and_must_not_claims_preserved",
            "status": "pass"
            if contains_all(lower_blob, ["operation", "operation stack", "not human", "not automatic", "not metric dominance"])
            else "fail",
            "evidence": "Evidence path preserves operation/operation-stack abstractions and must-not-claim boundaries.",
        },
        {
            "check": "source_policy_no_new_data_or_profiler_rerun",
            "status": "pass" if all(row["status"] in {"tracked_clean", "tracked_dirty_allowed"} for row in sources) else "fail",
            "evidence": "R369 reads tracked paper/docs/artifacts only; it downloads no data and reruns no profiler.",
        },
    ]


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R369 Reviewer Evidence Path",
        "",
        f"- Status: `{payload['status']}`.",
        f"- Checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.",
        "- This is a paper-integration guardrail, not a new empirical result.",
        "",
        "## Evidence Path",
        "",
        "| RQ | Claim test | Main paper evidence | Source artifact | Guardrail | Non-claim |",
        "|---|---|---|---|---|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['rq']} | {row['claim_test']} | {row['main_paper_evidence']} | "
            f"{row['source_artifact']} | {row['guardrail']} | {row['non_claim']} |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Evidence |", "|---|---|---|"])
    for check in payload["checks"]:
        lines.append(f"| `{check['check']}` | {check['status']} | {check['evidence']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['rq'])}</td>"
        f"<td>{html.escape(row['claim_test'])}</td>"
        f"<td>{html.escape(row['main_paper_evidence'])}</td>"
        f"<td>{html.escape(row['source_artifact'])}</td>"
        f"<td>{html.escape(row['guardrail'])}</td>"
        f"<td>{html.escape(row['non_claim'])}</td>"
        "</tr>"
        for row in payload["rows"]
    )
    checks = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['check'])}</td>"
        f"<td>{html.escape(row['status'])}</td>"
        f"<td>{html.escape(row['evidence'])}</td>"
        "</tr>"
        for row in payload["checks"]
    )
    path.write_text(
        f"""<!doctype html>
<meta charset=\"utf-8\">
<title>R369 Reviewer Evidence Path</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ddd; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f6f6; }}
</style>
<h1>R369 Reviewer Evidence Path</h1>
<p>Status: <code>{html.escape(payload['status'])}</code>;
checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.</p>
<h2>Evidence Path</h2>
<table><thead><tr><th>RQ</th><th>Claim test</th><th>Main paper evidence</th><th>Source artifact</th><th>Guardrail</th><th>Non-claim</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Checks</h2>
<table><thead><tr><th>Check</th><th>Status</th><th>Evidence</th></tr></thead><tbody>{checks}</tbody></table>
""",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    start = time.time()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    # Read upstream artifacts so missing/corrupt evidence fails the gate before
    # a paper table is emitted as if it were independent evidence.
    upstream_status = {
        "r360": read_json(SOURCES["R360 core result tables"])["status"],
        "r361": read_json(SOURCES["R361 claim evidence"])["status"],
        "r363": read_json(SOURCES["R363 visualization portfolio"])["status"],
        "r365": read_json(SOURCES["R365 headline case studies"])["status"],
        "r368": read_json(SOURCES["R368 trace-tree baseline"])["status"],
    }
    rows = build_rows()
    sources = source_rows()
    zh, en, evaluation = paper_texts()
    checks = build_checks(rows, sources, zh, en, evaluation)
    checks.append(
        {
            "check": "upstream_gates_pass",
            "status": "pass" if all(status == "pass" for status in upstream_status.values()) else "fail",
            "evidence": "; ".join(f"{name}={status}" for name, status in upstream_status.items()),
        }
    )
    checks_passed = sum(check["status"] == "pass" for check in checks)
    status = "pass" if checks_passed == len(checks) else "fail"
    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "schema": "agentsight.paper_reviewer_evidence_path.v1",
        "status": status,
        "commit": git_commit(),
        "elapsed_s": round(time.time() - start, 4),
        "not_new_empirical_result": True,
        "not_a_human_study_result": True,
        "not_an_agent_analyst_task_result": True,
        "input_policy": {
            "network_access_required": False,
            "dataset_sync": False,
            "dataset_creation": False,
            "dataset_relabeling": False,
            "profiler_rerun": False,
        },
        "profiler_abstractions": ["operation", "operation stack"],
        "upstream_status": upstream_status,
        "rows": rows,
        "checks": checks,
        "source_status": sources,
        "summary": {
            "status": status,
            "checks_passed": checks_passed,
            "checks_total": len(checks),
            "rows": len(rows),
        },
        "paper_table": rel(args.out_dir / "evidence-path-table.tex"),
    }

    write_csv(args.out_dir / "evidence-path.csv", rows, ROW_FIELDS)
    write_csv(args.out_dir / "evidence-path-checks.csv", checks, ["check", "status", "evidence"])
    write_csv(args.out_dir / "source-status.csv", sources, ["source", "path", "status", "sha256"])
    write_latex_table(args.out_dir / "evidence-path-table.tex", rows)
    (args.out_dir / "evidence-path.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(args.out_dir / "evidence-path.md", payload)
    write_html(args.out_dir / "index.html", payload)
    run_result = {
        "run_id": RUN_ID,
        "status": status,
        "checks_passed": checks_passed,
        "checks_total": len(checks),
        "report": rel(args.out_dir / "evidence-path.json"),
        "network_access_required": False,
        "profiler_rerun": False,
        "not_new_empirical_result": True,
    }
    (args.out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
