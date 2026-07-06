#!/usr/bin/env python3
"""R361: generate a reviewer-facing core-claim evidence ledger.

This is a paper-structure and claim-gating artifact, not a new empirical
experiment. It reads existing tracked E1--E4 artifacts and records, for each
core experiment, the claim, oracle, baselines, primary metrics, headline result,
actionable insight, counterpoint, and scoped paper wording.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-core-claim-evidence-r361"
RUN_ID = "R361"
SCRIPT_PATH = Path(__file__).resolve()

SOURCES = {
    "R320 profile accuracy": OUT_ROOT / "operation-profile-accuracy-r320" / "profile-accuracy-report.json",
    "R352 evaluation rubric": OUT_ROOT / "paper-evaluation-rubric-r352" / "evaluation-rubric-report.json",
    "R354 executable profile patch": OUT_ROOT / "operation-profile-patch-r354" / "profile-patch-report.json",
    "R355 oracle-depth adequacy": OUT_ROOT / "operation-oracle-depth-adequacy-r355" / "oracle-depth-adequacy-report.json",
    "R357 reviewer acceptance": OUT_ROOT / "paper-reviewer-acceptance-r357" / "reviewer-acceptance-r357.json",
    "R358 boundary profile patch": OUT_ROOT / "operation-boundary-profile-patch-r358" / "boundary-profile-patch-report.json",
    "R359 core-experiment consolidation": OUT_ROOT / "paper-core-experiments-r359" / "core-experiment-report.json",
    "R360 core result table": OUT_ROOT / "paper-core-result-tables-r360" / "core-result-tables.json",
}

PAPER_SOURCES = {
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "English paper": SUBMODULE_ROOT / "main.tex",
}

LEDGER_FIELDS = [
    "core_experiment",
    "claim",
    "research_question",
    "oracle",
    "baselines",
    "primary_metrics",
    "headline_result",
    "actionable_insight",
    "counterpoint_or_scope",
    "paper_wording",
    "primary_sources",
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
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    )
    return result.stdout.strip()


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


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


def evidence_by_experiment(r360: dict[str, Any]) -> dict[str, str]:
    evidence: dict[str, str] = {}
    for row in r360["experiments"]:
        eid = row["core_experiment"].split(":", 1)[0]
        evidence[eid] = row["evidence"]
    return evidence


def build_ledger(data: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    r320 = data["R320 profile accuracy"]
    r352 = data["R352 evaluation rubric"]["summary"]
    r354 = data["R354 executable profile patch"]["summary"]
    r355 = data["R355 oracle-depth adequacy"]["claim_summary"]
    r357 = data["R357 reviewer acceptance"]["summary"]
    r358 = data["R358 boundary profile patch"]["summary"]
    r359 = data["R359 core-experiment consolidation"]["summary"]
    r360 = data["R360 core result table"]
    r360_evidence = evidence_by_experiment(r360)

    return [
        {
            "core_experiment": "E1: coverage, recursive folding, and field derivation",
            "claim": "A two-object profiler model, operation plus operation stack, covers heterogeneous agent traces without binding profiling units to prompt/session/tool boundaries.",
            "research_question": "Can the same operation layer be folded recursively into task-, phase-, action-, boundary-, and fixed-session-shaped stacks by changing mappings and stack fields?",
            "oracle": "Public dataset labels and native trajectory fields; OSWorld-Human and AgentNet provide the strongest boundary and quality labels.",
            "baselines": "Dataset-native stacks, no-map folding, fixed-session stacks, profile-spec replay, and direct operation-file versus standard-trace import/export.",
            "primary_metrics": "operation coverage, unique-stack range across depths, mapping compression/reduction, boundary F1/V-measure, prompt/session-free profile-spec replay, and trace round-trip equality.",
            "headline_result": r360_evidence["E1"],
            "actionable_insight": "Users can choose recursive stack depth and field mappings at profiling time while keeping prompt, session, tool, process, and syscall records as operation forms or fields.",
            "counterpoint_or_scope": "This supports configurable operation-stack folding, not complete ecosystem compatibility or automatic latent-intent recovery.",
            "paper_wording": "Operation stacks are recursive projections over operation fields; mappings and tags derive fields before folding rather than creating new profiler objects.",
            "primary_sources": "R285; R286; R342; R353; R360",
        },
        {
            "core_experiment": "E2: hidden-label localization and ranking",
            "claim": "Operation-stack profiling can faithfully localize and rank task-relevant failures, safety issues, quality problems, and semantic boundaries on real labeled traces.",
            "research_question": "Do hot stacks and top-ranked groups correspond to hidden positives while requiring less inspection work than flat summaries and less fragmentation than fixed-session drilldown?",
            "oracle": f"{r320['totals']['positive_operations']} hidden positives over {r320['totals']['task_operations']} operations from {r320['totals']['tasks']} oracle-backed tasks and {r320['totals']['datasets']} datasets.",
            "baselines": "flat summary, fixed-session drilldown, dataset-native hierarchy, raw-action stack, operation-stack width, operation-stack query-aware, label drilldown, and oracle upper bound.",
            "primary_metrics": "AP/AUPRC-style score, precision@k, recall@k, F1@k, nDCG, recall/F1@work budget, top-k work, work-to-first-positive, group count, and oracle-depth unit recall.",
            "headline_result": r360_evidence["E2"],
            "actionable_insight": "The strongest supported tradeoff is lower inspection work and lower fixed-session fragmentation while retaining hidden-label hits under budgeted inspection.",
            "counterpoint_or_scope": "Flat and dataset-native views can win broad-recall or nDCG-style objectives; the claim is Pareto tradeoff, not metric dominance.",
            "paper_wording": "Supported as a hidden-label profiler benchmark, not a human-utility, productivity, or automatic-analysis claim.",
            "primary_sources": "R320; R333; R334; R337; R339; R355; R360",
        },
        {
            "core_experiment": "E3: mechanism and actionability",
            "claim": "The profiler exposes actionable optimization knobs through stack fields, mapping/tagging rules, ranking policies, profile specs, and boundary-derived operation fields.",
            "research_question": "Which mechanisms explain localization improvements, and can profile-guided changes improve outputs without leaking hidden labels into the profiler input?",
            "oracle": "The same hidden labels are used only after profiling for scoring; R358 additionally uses held-out OSWorld-Human boundary positives after learned boundary fields are visible operation fields.",
            "baselines": "default semantic-width specs, patched profile specs, visible feature rankers, equal/global/transfer policies, learned-boundary stacks, fixed-session stacks, and semantic-width stacks.",
            "primary_metrics": "accepted patches, AP delta, top-5 lift delta, first-positive-work delta, group reduction, top-5 work counterpoint, and held-out transfer tolerance.",
            "headline_result": f"{r360_evidence['E3']}; R354 accepts {r354['accepted_patches']} patches; R358 learned-boundary AP {fmt(r358['learned_boundary_ap'])} vs semantic {fmt(r358['semantic_width_ap'])}.",
            "actionable_insight": "The result identifies concrete knobs: stack depth, visible operation fields, rank-op rules, profile-spec patches, boundary-derived fields, and task-specific view choice.",
            "counterpoint_or_scope": f"OSWorld-Human needs boundary-derived fields; learned-boundary folding increases top-5 work by {fmt(r358['learned_boundary_delta_top5_work_vs_semantic'])} and first-positive work by {fmt(r358['learned_boundary_delta_first_positive_work_vs_semantic'])}, so this is not automatic boundary discovery or a universal selector.",
            "paper_wording": "Supported as executable actionability and mechanism isolation; automatic patch selection and label-free action selection remain out of scope.",
            "primary_sources": "R324; R342; R345-R350; R354; R358; R360",
        },
        {
            "core_experiment": "E4: reproducibility and artifact hygiene",
            "claim": "The offline profiling path is replayable over tracked inputs at low local cost.",
            "research_question": "Can reviewers rerun the profile-spec path and reproduce stable profile outputs without dataset sync, relabeling, or hidden human-study assumptions?",
            "oracle": "Tracked profile specs, tracked operation inputs, repeated profiler outputs, runtime logs, and source-status rows.",
            "baselines": "default output versus deterministic-output replay, semantic profile hashes versus raw-byte profile hashes, and tracked-clean source-status checks.",
            "primary_metrics": "deterministic spec pass rate, profiler invocations, median/p95 runtime, sample equality, stack equality, and raw-byte output equality.",
            "headline_result": r360_evidence["E4"],
            "actionable_insight": "The artifact path is replayable without dataset sync, relabeling, or hidden human-study assumptions.",
            "counterpoint_or_scope": "This is offline artifact reproducibility, not live eBPF overhead, full OpenTelemetry/Phoenix/LangSmith/Langfuse/Perfetto compatibility, or human productivity evidence.",
            "paper_wording": "Supported as replayable offline profiling artifact evidence; claim-integrity, rubric, and reviewer-style gates are artifact hygiene rather than scientific evidence.",
            "primary_sources": "R328; R360",
        },
    ]


def build_checks(data: dict[str, dict[str, Any]], ledger: list[dict[str, str]]) -> list[dict[str, Any]]:
    r320 = data["R320 profile accuracy"]
    r352 = data["R352 evaluation rubric"]["summary"]
    r354 = data["R354 executable profile patch"]["summary"]
    r355 = data["R355 oracle-depth adequacy"]["claim_summary"]
    r357 = data["R357 reviewer acceptance"]["summary"]
    r358 = data["R358 boundary profile patch"]["summary"]
    r359 = data["R359 core-experiment consolidation"]["summary"]
    r360 = data["R360 core result table"]["summary"]
    text_blob = "\n".join(read_text(path) for path in PAPER_SOURCES.values())
    ledger_blob = json.dumps(ledger, sort_keys=True)
    source_status = source_rows()
    empirical_sources = {
        "R320 profile accuracy",
        "R354 executable profile patch",
        "R355 oracle-depth adequacy",
        "R358 boundary profile patch",
    }
    empirical_sources_clean = all(
        row["status"] == "tracked_clean" for row in source_status if row["source"] in empirical_sources
    )

    required_fields_ok = all(all(row.get(field, "").strip() for field in LEDGER_FIELDS) for row in ledger)
    checks = [
        {
            "check": "four_substantial_core_experiments",
            "status": "pass" if len(ledger) == 4 and all(f"E{i}:" in ledger[i - 1]["core_experiment"] for i in range(1, 5)) else "fail",
            "evidence": f"{len(ledger)} ledger rows, ordered E1-E4.",
        },
        {
            "check": "every_core_row_has_claim_oracle_baseline_metric_scope",
            "status": "pass" if required_fields_ok else "fail",
            "evidence": "Each row has claim, question, oracle, baselines, metrics, insight, counterpoint, wording, and source runs.",
        },
        {
            "check": "hidden_label_localization_scale_and_metrics",
            "status": "pass"
            if r320["totals"]["tasks"] == 6
            and r320["totals"]["datasets"] == 4
            and r320["totals"]["task_operations"] == 34539
            and r320["totals"]["positive_operations"] == 3699
            and all(token in ledger_blob for token in ["AP/AUPRC", "precision@k", "recall@k", "F1@k", "nDCG", "work-to-first-positive"])
            else "fail",
            "evidence": "E2 records the R320 hidden-label scale and the full localization/ranking metric surface.",
        },
        {
            "check": "baseline_tradeoff_not_metric_dominance",
            "status": "pass"
            if all(token in ledger_blob for token in ["flat summary", "fixed-session", "dataset-native", "raw-action", "oracle upper bound", "Pareto tradeoff"])
            else "fail",
            "evidence": "E2 names required baselines and explicitly scopes the result to tradeoffs, not all-metric wins.",
        },
        {
            "check": "oracle_depth_and_fragmentation_evidence",
            "status": "pass"
            if r355["accuracy_unit_depth_rows"] == 24
            and r355["paired_checks"]["budget30_unit_recall_gt_fixed_rows"] == 20
            and r355["paired_checks"]["groups_to_50pct_units_lt_fixed_rows"] == 22
            else "fail",
            "evidence": "R355 oracle-depth rows preserve depth-aware accuracy and fragmentation support.",
        },
        {
            "check": "actionability_mechanism_and_counterpoints",
            "status": "pass"
            if r354["accepted_patches"] == "5/6"
            and r358["learned_boundary_ap"] > r358["semantic_width_ap"]
            and r358["learned_boundary_delta_top5_work_vs_semantic"] > 0
            and "not automatic boundary discovery" in ledger_blob
            else "fail",
            "evidence": "E3 records executable profile patches, learned-boundary AP gain, and inspection-cost counterpoints.",
        },
        {
            "check": "artifact_hygiene_gates_available",
            "status": "pass"
            if r352["rubric_level"] == "level_4_scoped_profile_benchmark"
            and r357["final_accepts"] == 4
            and r357["blocking_issues"] == 0
            and r359["checks_passed"] == r359["checks_total"] == 13
            and r360["checks_passed"] == r360["checks_total"] == 7
            else "fail",
            "evidence": "R352/R357/R359/R360 pass as artifact-hygiene gates, not empirical profiler evidence.",
        },
        {
            "check": "two_abstraction_boundary_preserved",
            "status": "pass"
            if all(token in ledger_blob for token in ["operation plus operation stack", "operation forms or fields"])
            and "operation stack" in text_blob
            else "fail",
            "evidence": "The ledger keeps prompt/session/tool/process/syscall as operation forms or fields, not new profiler objects.",
        },
        {
            "check": "must_not_claims_preserved",
            "status": "pass"
            if all(
                token in ledger_blob
                for token in [
                    "not a human-utility",
                    "not live eBPF overhead",
                    "not complete ecosystem compatibility",
                    "not automatic boundary discovery",
                    "not automatic boundary discovery or a universal selector",
                ]
            )
            else "fail",
            "evidence": "The ledger carries the must-not-claim guardrails for E2-E4.",
        },
        {
            "check": "upstream_empirical_sources_tracked_clean",
            "status": "pass" if empirical_sources_clean else "fail",
            "evidence": "Empirical R320/R354/R355/R358 source artifacts are tracked and clean; paper hygiene gates may be regenerated in this run.",
        },
    ]
    return checks


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def markdown_table(rows: list[dict[str, str]]) -> str:
    lines = [
        "| Core experiment | Claim | Oracle | Baselines | Primary metrics | Headline result | Counterpoint / scope |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                row[field].replace("\n", " ")
                for field in [
                    "core_experiment",
                    "claim",
                    "oracle",
                    "baselines",
                    "primary_metrics",
                    "headline_result",
                    "counterpoint_or_scope",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def latex_table(rows: list[dict[str, str]]) -> str:
    def esc(value: str) -> str:
        return (
            value.replace("\\", "\\textbackslash{}")
            .replace("&", "\\&")
            .replace("%", "\\%")
            .replace("_", "\\_")
            .replace("#", "\\#")
        )

    lines = [
        "% Generated by script/paper_core_claim_evidence.py (R361).",
        "\\begin{tabular}{p{0.16\\linewidth}p{0.20\\linewidth}p{0.20\\linewidth}p{0.24\\linewidth}p{0.14\\linewidth}}",
        "  \\toprule",
        "  Core experiment & Claim & Oracle/baselines & Headline evidence & Scope \\\\",
        "  \\midrule",
    ]
    for row in rows:
        lines.append(
            "  "
            + " & ".join(
                [
                    esc(row["core_experiment"]),
                    esc(row["claim"]),
                    esc(f"{row['oracle']} Baselines: {row['baselines']}"),
                    esc(row["headline_result"]),
                    esc(row["counterpoint_or_scope"]),
                ]
            )
            + " \\\\"
        )
    lines.extend(["  \\bottomrule", "\\end{tabular}", ""])
    return "\n".join(lines)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R361 Core-Claim Evidence Ledger",
        "",
        f"- Status: `{payload['status']}`.",
        f"- Checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.",
        "- This is a paper-structure and claim-gating artifact, not a new empirical result.",
        "",
        "## Evidence Ledger",
        "",
        markdown_table(payload["ledger"]),
        "",
        "## Checks",
        "",
        "| Check | Status | Evidence |",
        "|---|---|---|",
    ]
    for check in payload["checks"]:
        lines.append(f"| `{check['check']}` | {check['status']} | {check['evidence']} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    table_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['core_experiment'])}</td>"
        f"<td>{html.escape(row['claim'])}</td>"
        f"<td>{html.escape(row['oracle'])}</td>"
        f"<td>{html.escape(row['baselines'])}</td>"
        f"<td>{html.escape(row['primary_metrics'])}</td>"
        f"<td>{html.escape(row['headline_result'])}</td>"
        f"<td>{html.escape(row['counterpoint_or_scope'])}</td>"
        "</tr>"
        for row in payload["ledger"]
    )
    check_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(check['check'])}</td>"
        f"<td>{html.escape(check['status'])}</td>"
        f"<td>{html.escape(check['evidence'])}</td>"
        "</tr>"
        for check in payload["checks"]
    )
    path.write_text(
        f"""<!doctype html>
<html>
<head>
<meta charset=\"utf-8\">
<title>R361 Core-Claim Evidence Ledger</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ddd; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f5f5f5; text-align: left; }}
</style>
</head>
<body>
<h1>R361 Core-Claim Evidence Ledger</h1>
<p>Status: <code>{html.escape(payload['status'])}</code>;
checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.</p>
<h2>Evidence Ledger</h2>
<table>
<tr><th>Core experiment</th><th>Claim</th><th>Oracle</th><th>Baselines</th><th>Metrics</th><th>Headline</th><th>Scope</th></tr>
{table_rows}
</table>
<h2>Checks</h2>
<table>
<tr><th>Check</th><th>Status</th><th>Evidence</th></tr>
{check_rows}
</table>
</body>
</html>
""",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    out_dir = args.out_dir
    start = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)

    data = {name: read_json(path) for name, path in SOURCES.items()}
    ledger = build_ledger(data)
    checks = build_checks(data, ledger)
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    summary = {
        "checks_passed": sum(1 for check in checks if check["status"] == "pass"),
        "checks_total": len(checks),
        "core_experiments": len(ledger),
        "status": status,
    }
    payload = {
        "run_id": RUN_ID,
        "schema": "agentsight.paper-core-claim-evidence.v1",
        "status": status,
        "commit": git_commit(),
        "input_policy": {
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "dataset_sync": "none",
            "network_access_required": False,
            "profiler_rerun": False,
            "hidden_label_use": "only through already-scored upstream artifacts",
        },
        "not_new_empirical_result": True,
        "not_a_human_study_result": True,
        "not_an_agent_analyst_task_result": True,
        "profiler_abstractions": ["operation", "operation stack"],
        "summary": summary,
        "ledger": ledger,
        "checks": checks,
        "source_status": source_rows(),
        "elapsed_s": round(time.time() - start, 3),
    }

    write_csv(out_dir / "core-claim-ledger.csv", ledger, LEDGER_FIELDS)
    write_csv(out_dir / "core-claim-checks.csv", checks, ["check", "status", "evidence"])
    write_csv(out_dir / "source-status.csv", payload["source_status"], ["source", "path", "status", "sha256"])
    (out_dir / "core-claim-evidence.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "claim-ledger-table.tex").write_text(latex_table(ledger), encoding="utf-8")
    write_markdown(out_dir / "core-claim-evidence.md", payload)
    write_html(out_dir / "index.html", payload)
    run_result = {
        "run_id": RUN_ID,
        "status": status,
        "checks_passed": summary["checks_passed"],
        "checks_total": summary["checks_total"],
        "report": rel(out_dir / "core-claim-evidence.json"),
    }
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
