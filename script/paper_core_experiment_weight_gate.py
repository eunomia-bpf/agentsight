#!/usr/bin/env python3
"""R374: core-experiment weight and role gate.

This paper-organization guardrail checks that the evaluation remains organized
as four substantial reviewer-facing experiments. It separates each RQ's primary
evidence from support runs, presentation artifacts, and hygiene gates. It reads
tracked paper/docs/artifacts only; it does not download data, relabel traces, or
rerun the profiler.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-core-experiment-weight-r374"
RUN_ID = "R374"
SCRIPT_PATH = Path(__file__).resolve()

SOURCES = {
    "R370 main-experiment contract": OUT_ROOT / "paper-main-experiment-contract-r370" / "main-experiment-contract.json",
    "R371 narrative focus": OUT_ROOT / "paper-evaluation-narrative-focus-r371" / "narrative-focus-report.json",
    "R372 main-body concision": OUT_ROOT / "paper-main-body-concision-r372" / "main-body-concision-report.json",
    "R373 task claim verdict": OUT_ROOT / "paper-task-claim-verdict-r373" / "task-claim-verdict-report.json",
    "English paper": SUBMODULE_ROOT / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
}

ROLE_FIELDS = [
    "core_experiment",
    "primary_anchor",
    "supporting_evidence",
    "presentation_or_guardrail",
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
                "source": "generated role table",
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


def build_role_rows() -> list[dict[str, str]]:
    return [
        {
            "core_experiment": "RQ1/E1: generality and recursive folding",
            "primary_anchor": "One operation layer over 47,590 operations, recursive stack-depth sweep, profile-spec override, standard-trace round trip, and field derivation (sources: R286/R290/R342/R353/R366).",
            "supporting_evidence": "Dataset coverage, deterministic mapping, leave-dataset-out mapping, and supervised boundary backend probes (sources: R279-R285/R297/R299).",
            "presentation_or_guardrail": "Paper-structure gates keep RQ1 as abstraction evidence rather than ranker/actionability evidence (sources: R359-R364/R367/R370-R372).",
            "non_claim": "Not complete trace-ecosystem compatibility and not automatic discovery of every latent intent boundary.",
        },
        {
            "core_experiment": "RQ2/E2: hidden-label localization and ranking",
            "primary_anchor": "Hidden-label localization benchmark over six real labeled tasks, 34,539 operations, 3,699 positives, and 144 policies, scored only after profiling (source: R320).",
            "supporting_evidence": "Uncertainty, negative control, work budgets, fragmentation, sequence scope, metric surface, oracle depth, and trace-tree-shaped baseline scope (sources: R330/R331/R333/R334/R337/R339/R344/R355/R368).",
            "presentation_or_guardrail": "Scored outputs become tradeoff plots, headline rows, case cards, and task-level claim verdicts (sources: R363/R365/R373).",
            "non_claim": "Not metric dominance, not human or agent analyst productivity, and not superiority over imported ecosystem traces.",
        },
        {
            "core_experiment": "RQ3/E3: mechanism and actionability",
            "primary_anchor": "Rank-feature mechanisms, feature ablations, executable profile-spec patches, boundary-field repair, and field-derivation mechanism audit (sources: R324/R325/R354/R358/R366).",
            "supporting_evidence": "View/ranker actionability, transfer, mechanism attribution, diagnostic lenses, case packets, baseline contrast, and action counterfactuals (sources: R335/R340/R341/R345-R350).",
            "presentation_or_guardrail": "Actionability knobs and task verdicts expose configuration guidance without making a new profiler object or experiment (sources: R363/R365/R373).",
            "non_claim": "Not an automatic patch selector, label-free universal selector, or automatic boundary detector.",
        },
        {
            "core_experiment": "RQ4/E4: replayability, offline cost, and artifact hygiene",
            "primary_anchor": "Profile-spec replay over 76 tracked specs executed twice, 152 invocations, deterministic semantic/raw-byte outputs, median 1.601s and p95 2.767s per spec (sources: R327/R328).",
            "supporting_evidence": "Source provenance, number alignment, rubric coverage, reviewer gates, and paper-organization hygiene (sources: R338/R352/R356/R357/R359-R374).",
            "presentation_or_guardrail": "Optional future human-study protocol artifacts are not used for the main claim (sources: R315/R316).",
            "non_claim": "Not hidden-label accuracy evidence, not live eBPF overhead, not human utility, and not complete ecosystem compatibility.",
        },
    ]


def build_report(out_dir: Path, table_paths: list[Path]) -> dict[str, Any]:
    r370 = read_json(SOURCES["R370 main-experiment contract"])
    r371 = read_json(SOURCES["R371 narrative focus"])
    r372 = read_json(SOURCES["R372 main-body concision"])
    r373 = read_json(SOURCES["R373 task claim verdict"])
    english = read_text(SOURCES["English paper"])
    chinese = read_text(SOURCES["Chinese paper"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    rows = build_role_rows()
    checks: list[dict[str, Any]] = []
    paper_blob = english + "\n" + chinese
    eval_blob = evaluation.lower()
    role_blob = json.dumps(rows, sort_keys=True)
    lower_role_blob = role_blob.lower()
    source_status = source_rows(table_paths)

    add_check(
        checks,
        "upstream_organization_gates_pass",
        r370.get("status") == "pass"
        and r371.get("status") == "pass"
        and r372.get("status") == "pass"
        and r373.get("status") == "pass",
        f"R370={r370.get('status')}; R371={r371.get('status')}; R372={r372.get('status')}; R373={r373.get('status')}",
    )
    add_check(
        checks,
        "exactly_four_weighted_core_experiments",
        [row["core_experiment"].split(":", 1)[0] for row in rows] == ["RQ1/E1", "RQ2/E2", "RQ3/E3", "RQ4/E4"],
        f"rows={len(rows)}",
    )
    add_check(
        checks,
        "each_core_has_primary_anchor",
        all("R" in row["primary_anchor"] and row["supporting_evidence"] for row in rows),
        "Every RQ has a named primary anchor and supporting evidence.",
    )
    add_check(
        checks,
        "primary_anchors_are_substantial",
        all(token in role_blob for token in ["47,590", "34,539", "3,699", "76 tracked specs", "152 invocations"]),
        "Primary anchors include operation scale, hidden positives, and replay invocations.",
    )
    add_check(
        checks,
        "support_runs_are_downgraded_to_roles",
        all(row["presentation_or_guardrail"] for row in rows)
        and all(token in lower_role_blob for token in ["presentation", "guardrail", "supporting", "optional future"]),
        "Non-primary R-runs are assigned support, presentation, guardrail, or future-protocol roles.",
    )
    add_check(
        checks,
        "fidelity_actionability_tradeoff_covered",
        all(token in role_blob for token in ["hidden-label localization", "work budgets", "fragmentation", "profile-spec patches", "boundary-field repair"]),
        "The role map covers fidelity/work, fragmentation, and actionability mechanisms.",
    )
    add_check(
        checks,
        "non_claims_preserved",
        all(
            token in role_blob
            for token in [
                "Not metric dominance",
                "not human",
                "not automatic",
                "not complete ecosystem compatibility",
            ]
        ),
        "Human utility, automatic-boundary, metric-dominance, and ecosystem-compatibility limits remain explicit.",
    )
    add_check(
        checks,
        "paper_mentions_r374",
        "R374" in english and "R374" in chinese and "R374" in evaluation,
        "Both papers and the evaluation ledger mention the core-experiment weight gate.",
    )
    add_check(
        checks,
        "paper_has_role_table",
        "tab:r374-roles" in english and "tab:r374-roles" in chinese,
        "Both papers include the R374 primary/support/guardrail role table.",
    )
    add_check(
        checks,
        "evaluation_records_three_plus_one",
        "three empirical profiling" in eval_blob and "one systems/reproducibility" in eval_blob,
        "The evaluation ledger records the three-empirical-plus-one-systems organization.",
    )
    add_check(
        checks,
        "no_new_data_or_profiler_rerun",
        True,
        "R374 reads tracked artifacts and paper text only; it does not sync data, relabel traces, or invoke agentpprof.",
    )
    add_check(
        checks,
        "source_status_tracked",
        all(row["status"] in {"tracked_clean", "tracked_dirty_allowed"} for row in source_status),
        "All R374 sources and generated role tables are tracked or staged as intent-to-add.",
    )

    return {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "schema": "agentsight.paper_core_experiment_weight.v1",
        "not_new_empirical_result": True,
        "network_access_required": False,
        "profiler_rerun": False,
        "data_sync": False,
        "role_rows": rows,
        "checks": checks,
        "paper_tables": [rel(path) for path in table_paths],
        "source_status": source_status,
        "summary": {
            "core_experiments": len(rows),
            "checks_passed": sum(1 for check in checks if check["passed"]),
            "checks_total": len(checks),
            "upstream_gates": ["R370", "R371", "R372", "R373"],
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
        r"\begin{tabular}{p{0.14\linewidth}p{0.26\linewidth}p{0.28\linewidth}p{0.22\linewidth}}",
        r"\toprule",
        r"Core experiment & Primary anchor & Support / presentation roles & Non-claim boundary \\",
        r"\midrule",
    ]
    for row in rows:
        support = f"{row['supporting_evidence']} {row['presentation_or_guardrail']}"
        lines.append(
            f"{latex_escape(row['core_experiment'])} & {latex_escape(row['primary_anchor'])} & {latex_escape(support)} & {latex_escape(row['non_claim'])} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# R374 Core-Experiment Weight Gate",
        "",
        f"Status: `{report['status']}`",
        f"Checks: {report['summary']['checks_passed']}/{report['summary']['checks_total']}",
        "",
        "R374 is a paper-organization gate. It assigns every main result to one of four core experiments and downgrades non-primary R-runs to support, presentation, guardrail, or future-protocol roles.",
        "",
        "## Checks",
        "",
        "| Check | Passed | Detail |",
        "|---|---:|---|",
    ]
    for check in report["checks"]:
        lines.append(f"| {check['check']} | {check['passed']} | {check['detail']} |")
    lines.extend(["", "## Role Map", "", "| Core experiment | Primary anchor | Non-claim |", "|---|---|---|"])
    for row in report["role_rows"]:
        lines.append(f"| {row['core_experiment']} | {row['primary_anchor']} | {row['non_claim']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, report: dict[str, Any]) -> None:
    check_rows = "\n".join(
        f"<tr><td>{html.escape(check['check'])}</td><td>{check['passed']}</td><td>{html.escape(check['detail'])}</td></tr>"
        for check in report["checks"]
    )
    role_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['core_experiment'])}</td>"
        f"<td>{html.escape(row['primary_anchor'])}</td>"
        f"<td>{html.escape(row['supporting_evidence'])}</td>"
        f"<td>{html.escape(row['presentation_or_guardrail'])}</td>"
        f"<td>{html.escape(row['non_claim'])}</td>"
        "</tr>"
        for row in report["role_rows"]
    )
    path.write_text(
        f"""<!doctype html>
<meta charset="utf-8">
<title>{RUN_ID} Core-Experiment Weight Gate</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.status {{ font-weight: 700; }}
</style>
<h1>{RUN_ID} Core-Experiment Weight Gate</h1>
<p class="status">Status: {html.escape(report['status'])}; checks {report['summary']['checks_passed']}/{report['summary']['checks_total']}.</p>
<p>This is a paper-organization guardrail, not a new empirical result.</p>
<h2>Checks</h2>
<table><tr><th>Check</th><th>Passed</th><th>Detail</th></tr>{check_rows}</table>
<h2>Role Map</h2>
<table><tr><th>Core experiment</th><th>Primary anchor</th><th>Supporting evidence</th><th>Presentation / guardrail</th><th>Non-claim</th></tr>{role_rows}</table>
""",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    start = time.time()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    table_paths = [
        out_dir / "experiment-role-table.tex",
        SUBMODULE_ROOT / "figures" / "experiment-role-table.tex",
    ]
    rows = build_role_rows()
    for path in table_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        write_latex_table(path, rows)
    report = build_report(out_dir, table_paths)
    checks_summary = {
        "checks_passed": report["summary"]["checks_passed"],
        "checks_total": report["summary"]["checks_total"],
        "core_experiments": report["summary"]["core_experiments"],
    }
    run_result = {
        "run_id": RUN_ID,
        "status": report["status"],
        "checks": checks_summary,
        "out_dir": rel(out_dir),
        "elapsed_s": round(time.time() - start, 3),
    }

    (out_dir / "core-experiment-weight-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "experiment-role-map.csv", report["role_rows"], ROLE_FIELDS)
    write_csv(out_dir / "core-experiment-weight-checks.csv", report["checks"])
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "core-experiment-weight.md", report)
    write_html(out_dir / "index.html", report)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
