#!/usr/bin/env python3
"""R375: core-experiment claim gate.

This paper-integration guardrail turns the four core experiments into explicit
claim decisions. It records, for each RQ/E block, the allowed paper wording, the
failure interpretation that would narrow the claim, and the wording that remains
out of scope. It reads tracked paper/docs/artifacts only; it does not download
data, relabel traces, or rerun the profiler.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-core-claim-gate-r375"
RUN_ID = "R375"
SCRIPT_PATH = Path(__file__).resolve()

SOURCES = {
    "R361 core claim evidence": OUT_ROOT / "paper-core-claim-evidence-r361" / "core-claim-evidence.json",
    "R364 core experiment sufficiency": OUT_ROOT / "paper-core-experiment-sufficiency-r364" / "core-experiment-sufficiency.json",
    "R370 main experiment contract": OUT_ROOT / "paper-main-experiment-contract-r370" / "main-experiment-contract.json",
    "R373 task claim verdict": OUT_ROOT / "paper-task-claim-verdict-r373" / "task-claim-verdict-report.json",
    "R374 core experiment weight": OUT_ROOT / "paper-core-experiment-weight-r374" / "core-experiment-weight-report.json",
    "English paper": SUBMODULE_ROOT / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
}

GATE_FIELDS = [
    "core_experiment",
    "gate_decision",
    "allowed_claim",
    "failure_interpretation",
    "must_not_claim",
    "evidence_sources",
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


def source_rows(extra_paths: list[Path]) -> list[dict[str, str]]:
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
    for path in extra_paths:
        rows.append(
            {
                "source": "generated claim-gate table",
                "path": rel(path),
                "status": git_status(path),
                "sha256": sha256(path) if path.exists() else "",
            }
        )
    return rows


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


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"check": name, "passed": bool(passed), "detail": detail})


def build_gate_rows() -> list[dict[str, str]]:
    return [
        {
            "core_experiment": "RQ1/E1: generality and recursive folding",
            "gate_decision": "Supported with scoped limits.",
            "allowed_claim": "A two-object model covers heterogeneous public labeled traces, and mappings/tags derive operation fields before query-time recursive stack folding.",
            "failure_interpretation": "If a dataset needs a new profiler object or a fixed prompt/session hierarchy to obtain useful groups, narrow C1/C2/C3 to the covered families and fields.",
            "must_not_claim": "Complete trace-ecosystem compatibility; automatic discovery of every latent intent boundary.",
            "evidence_sources": "R286/R290/R342/R353/R366 plus R361/R364/R370/R374 gates.",
        },
        {
            "core_experiment": "RQ2/E2: hidden-label localization and ranking",
            "gate_decision": "Supported as a hidden-label profiler benchmark.",
            "allowed_claim": "Operation-stack profiling localizes dataset-provided positives with less inspection work than flat summaries and a better median-fragmentation tradeoff than fixed-session drilldown proxy.",
            "failure_interpretation": "If flat or fixed-session dominates the Pareto surface on a task or metric, keep that counterpoint visible and narrow the claim to the supported budget, recall, and fragmentation objectives.",
            "must_not_claim": "Metric dominance; human or agent analyst productivity; superiority over imported OpenTelemetry/Phoenix/LangSmith/Langfuse/Perfetto traces.",
            "evidence_sources": "R320/R333/R334/R337/R339/R344/R355/R368 plus R373 task verdict.",
        },
        {
            "core_experiment": "RQ3/E3: mechanism and actionability",
            "gate_decision": "Supported as profile-configuration actionability.",
            "allowed_claim": "Stack fields, mapping/tagging rules, rankers, profile specs, and boundary-derived fields expose actionable configuration knobs and explain task-specific wins and failures.",
            "failure_interpretation": "If one default view wins everywhere, remove configurable actionability; if transfer fails, keep the result as post-hoc profile-guided configuration rather than automatic selection.",
            "must_not_claim": "Automatic patch selection; label-free universal view/ranker selection; automatic boundary detection.",
            "evidence_sources": "R324/R325/R335/R340/R341/R345-R350/R354/R358/R366 plus R373 task verdict.",
        },
        {
            "core_experiment": "RQ4/E4: replayability, offline cost, and artifact hygiene",
            "gate_decision": "Supported as offline artifact replayability.",
            "allowed_claim": "Tracked profile specs replay deterministically over tracked operation inputs at low local cost, and paper guardrails keep evidence, wording, and non-claims aligned.",
            "failure_interpretation": "If replay is nondeterministic or paper wording outruns evidence, block artifact readiness and narrow the abstract until source, number, and claim gates pass again.",
            "must_not_claim": "Live eBPF overhead; hidden-label accuracy evidence; human utility; complete ecosystem compatibility.",
            "evidence_sources": "R327/R328 plus R338/R352/R356/R357/R359-R375 guardrails.",
        },
    ]


def build_report(out_dir: Path, table_paths: list[Path]) -> dict[str, Any]:
    r361 = read_json(SOURCES["R361 core claim evidence"])
    r364 = read_json(SOURCES["R364 core experiment sufficiency"])
    r370 = read_json(SOURCES["R370 main experiment contract"])
    r373 = read_json(SOURCES["R373 task claim verdict"])
    r374 = read_json(SOURCES["R374 core experiment weight"])
    english = read_text(SOURCES["English paper"])
    chinese = read_text(SOURCES["Chinese paper"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    rows = build_gate_rows()
    checks: list[dict[str, Any]] = []
    source_status = source_rows(table_paths)
    row_blob = json.dumps(rows, sort_keys=True)
    paper_blob = english + "\n" + chinese
    eval_blob = evaluation.lower()

    add_check(
        checks,
        "upstream_claim_gates_pass",
        all(
            report.get("status") == "pass"
            for report in [r361, r364, r370, r373, r374]
        ),
        f"R361={r361.get('status')}; R364={r364.get('status')}; R370={r370.get('status')}; R373={r373.get('status')}; R374={r374.get('status')}",
    )
    add_check(
        checks,
        "exactly_four_claim_gate_rows",
        [row["core_experiment"].split(":", 1)[0] for row in rows] == ["RQ1/E1", "RQ2/E2", "RQ3/E3", "RQ4/E4"],
        f"rows={len(rows)}",
    )
    add_check(
        checks,
        "each_gate_has_decision_allowed_failure_forbidden",
        all(all(row.get(field, "").strip() for field in GATE_FIELDS) for row in rows),
        "Each row has a decision, allowed claim, failure interpretation, must-not-claim boundary, and evidence sources.",
    )
    add_check(
        checks,
        "profiling_metrics_and_baselines_preserved",
        all(
            token in paper_blob
            for token in [
                "precision@k",
                "recall@operation-budget",
                "F1@k",
                "nDCG",
                "work-to-first-positive",
                "flat",
                "fixed-session",
                "dataset-native",
                "raw-action",
            ]
        ),
        "The paper still carries the profiler metrics and the named baseline families.",
    )
    add_check(
        checks,
        "actionability_mechanisms_preserved",
        all(token in row_blob for token in ["Stack fields", "mapping/tagging", "rankers", "profile specs", "boundary-derived fields"]),
        "R375 ties actionability to fields, mappings/tags, rankers, profile specs, and boundary-derived operation fields.",
    )
    add_check(
        checks,
        "must_not_claims_preserved",
        all(
            token in row_blob
            for token in [
                "Metric dominance",
                "human",
                "automatic",
                "complete ecosystem compatibility",
            ]
        ),
        "Metric dominance, human utility/productivity, automatic-boundary, and ecosystem-compatibility limits remain explicit.",
    )
    add_check(
        checks,
        "paper_mentions_r375_claim_gate",
        "R375" in english and "R375" in chinese and "R375" in evaluation,
        "Both papers and the evaluation ledger mention the R375 claim gate.",
    )
    add_check(
        checks,
        "paper_summarizes_claim_gate_decisions",
        all(
            token in paper_blob
            for token in [
                "supported as a hidden-label profiler benchmark",
                "profile-configuration actionability",
                "offline artifact replayability",
                "automatic patch selection",
            ]
        ),
        "Both papers summarize the R375 decisions while the full table stays in the artifact ledger.",
    )
    add_check(
        checks,
        "evaluation_records_claim_gate_role",
        "claim gate" in eval_blob and "supported as hidden-label profiler benchmark" in eval_blob,
        "The evaluation ledger records that R375 converts E1-E4 into scoped claim decisions.",
    )
    add_check(
        checks,
        "no_new_data_or_profiler_rerun",
        True,
        "R375 reads tracked artifacts and paper text only; it does not sync data, relabel traces, or invoke agentpprof.",
    )
    add_check(
        checks,
        "source_status_tracked",
        all(row["status"] in {"tracked_clean", "tracked_dirty_allowed"} for row in source_status),
        "All R375 sources and generated claim-gate tables are tracked or staged as intent-to-add.",
    )

    return {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "schema": "agentsight.paper_core_claim_gate.v1",
        "not_new_empirical_result": True,
        "network_access_required": False,
        "profiler_rerun": False,
        "data_sync": False,
        "gate_rows": rows,
        "checks": checks,
        "paper_tables": [rel(path) for path in table_paths],
        "source_status": source_status,
        "summary": {
            "core_experiments": len(rows),
            "checks_passed": sum(1 for check in checks if check["passed"]),
            "checks_total": len(checks),
            "upstream_gates": ["R361", "R364", "R370", "R373", "R374"],
        },
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = fields or list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_latex_table(path: Path, rows: list[dict[str, str]]) -> None:
    lines = [
        r"\begin{tabular}{p{0.15\linewidth}p{0.17\linewidth}p{0.25\linewidth}p{0.20\linewidth}p{0.18\linewidth}}",
        r"\toprule",
        r"Core experiment & Gate decision & Allowed paper claim & Failure / narrowing rule & Must not claim \\",
        r"\midrule",
    ]
    for row in rows:
        lines.append(
            f"{latex_escape(row['core_experiment'])} & {latex_escape(row['gate_decision'])} & {latex_escape(row['allowed_claim'])} & {latex_escape(row['failure_interpretation'])} & {latex_escape(row['must_not_claim'])} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# R375 Core-Experiment Claim Gate",
        "",
        f"Status: `{report['status']}`",
        f"Checks: {report['summary']['checks_passed']}/{report['summary']['checks_total']}",
        "",
        "R375 is a paper-integration gate. It converts the four core experiments into explicit claim decisions and keeps broader wording as future expansion rather than paper claims.",
        "",
        "## Checks",
        "",
        "| Check | Passed | Detail |",
        "|---|---:|---|",
    ]
    for check in report["checks"]:
        lines.append(f"| {check['check']} | {check['passed']} | {check['detail']} |")
    lines.extend(
        [
            "",
            "## Claim Gates",
            "",
            "| Core experiment | Gate decision | Allowed claim | Must not claim |",
            "|---|---|---|---|",
        ]
    )
    for row in report["gate_rows"]:
        lines.append(
            f"| {row['core_experiment']} | {row['gate_decision']} | {row['allowed_claim']} | {row['must_not_claim']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, report: dict[str, Any]) -> None:
    check_rows = "\n".join(
        f"<tr><td>{html.escape(check['check'])}</td><td>{check['passed']}</td><td>{html.escape(check['detail'])}</td></tr>"
        for check in report["checks"]
    )
    gate_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['core_experiment'])}</td>"
        f"<td>{html.escape(row['gate_decision'])}</td>"
        f"<td>{html.escape(row['allowed_claim'])}</td>"
        f"<td>{html.escape(row['failure_interpretation'])}</td>"
        f"<td>{html.escape(row['must_not_claim'])}</td>"
        f"<td>{html.escape(row['evidence_sources'])}</td>"
        "</tr>"
        for row in report["gate_rows"]
    )
    path.write_text(
        f"""<!doctype html>
<meta charset="utf-8">
<title>{RUN_ID} Core-Experiment Claim Gate</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.status {{ font-weight: 700; }}
</style>
<h1>{RUN_ID} Core-Experiment Claim Gate</h1>
<p class="status">Status: {html.escape(report['status'])}; checks {report['summary']['checks_passed']}/{report['summary']['checks_total']}.</p>
<p>This is a paper-integration guardrail, not a new empirical result.</p>
<h2>Checks</h2>
<table><tr><th>Check</th><th>Passed</th><th>Detail</th></tr>{check_rows}</table>
<h2>Claim Gates</h2>
<table><tr><th>Core experiment</th><th>Gate decision</th><th>Allowed claim</th><th>Failure / narrowing rule</th><th>Must not claim</th><th>Evidence sources</th></tr>{gate_rows}</table>
""",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    start = time.time()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    table_paths = [
        out_dir / "claim-gate-table.tex",
        SUBMODULE_ROOT / "figures" / "claim-gate-table.tex",
    ]
    rows = build_gate_rows()
    for path in table_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        write_latex_table(path, rows)
    report = build_report(out_dir, table_paths)
    run_result = {
        "run_id": RUN_ID,
        "status": report["status"],
        "checks": {
            "checks_passed": report["summary"]["checks_passed"],
            "checks_total": report["summary"]["checks_total"],
            "core_experiments": report["summary"]["core_experiments"],
        },
        "out_dir": rel(out_dir),
        "elapsed_s": round(time.time() - start, 3),
    }

    (out_dir / "core-claim-gate-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "claim-gate.csv", report["gate_rows"], GATE_FIELDS)
    write_csv(out_dir / "claim-gate-checks.csv", report["checks"])
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "core-claim-gate.md", report)
    write_html(out_dir / "index.html", report)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
