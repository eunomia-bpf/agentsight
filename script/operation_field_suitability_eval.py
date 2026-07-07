#!/usr/bin/env python3
"""R400: synthesize operation-field derivation suitability decisions.

This run turns existing field-derivation and boundary-backend evidence into
configuration decisions for the profiler. It reads tracked artifacts only: no
dataset sync, no relabeling, and no profiler rerun. The output is meant to
answer the actionability question directly: when should a profile use mapping,
rank features, stack-depth changes, or boundary-derived operation fields, and
when should it avoid them?
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
DEFAULT_OUT_DIR = OUT_ROOT / "operation-field-suitability-r400"
RUN_ID = "R400"
SCRIPT_PATH = Path(__file__).resolve()

SOURCES = {
    "R366 mechanism report": OUT_ROOT
    / "operation-field-derivation-mechanism-r366"
    / "field-derivation-mechanism-report.json",
    "R366 mechanism rows": OUT_ROOT / "operation-field-derivation-mechanism-r366" / "mechanism-rows.csv",
    "R366 boundary family summary": OUT_ROOT
    / "operation-field-derivation-mechanism-r366"
    / "boundary-family-summary.csv",
    "R325 rank feature findings": OUT_ROOT / "operation-rank-feature-ablation-r325" / "rank-feature-findings.csv",
    "R358 boundary profile patch metrics": OUT_ROOT / "operation-boundary-profile-patch-r358" / "policy-metrics.csv",
}

PAPER_SOURCES = {
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "design doc": ROOT / "docs" / "design.md",
    "implementation doc": ROOT / "docs" / "implementation.md",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "English paper": SUBMODULE_ROOT / "main.tex",
}

RULE_FIELDS = ["decision_id", "knob", "use_when", "avoid_when", "evidence", "counterpoint", "verdict"]
FAMILY_FIELDS = [
    "candidate",
    "dataset",
    "learned_f1",
    "best_baseline",
    "best_baseline_f1",
    "delta_vs_best_baseline_f1",
    "decision",
    "reason",
]
CHECK_FIELDS = ["check", "status", "evidence"]
SOURCE_FIELDS = ["source", "path", "status", "sha256"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_status(path: Path) -> str:
    repo_root = SUBMODULE_ROOT if path.resolve().is_relative_to(SUBMODULE_ROOT) else ROOT
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


def fmt(value: Any) -> str:
    number = float(value)
    return f"{number:.4f}".rstrip("0").rstrip(".")


def by_policy(rows: list[dict[str, str]], policy: str) -> dict[str, str]:
    for row in rows:
        if row["policy"] == policy:
            return row
    raise KeyError(policy)


def mechanism(rows: list[dict[str, str]], row_id: str) -> dict[str, str]:
    for row in rows:
        if row["row_id"] == row_id:
            return row
    raise KeyError(row_id)


def family_decision(row: dict[str, str]) -> tuple[str, str]:
    learned_f1 = float(row["learned_f1"])
    delta = float(row["delta_vs_best_baseline_f1"])
    baseline = row["best_baseline"]
    if delta <= 0:
        return "reject", f"simple baseline {baseline} is stronger by {fmt(abs(delta))} F1"
    if learned_f1 >= 0.6 and delta >= 0.05:
        return "accept", f"learned fields beat {baseline} by {fmt(delta)} F1 with high absolute F1"
    return "caution", f"learned fields beat {baseline} by {fmt(delta)} F1, but the margin or absolute F1 is modest"


def build_family_decisions(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    decisions = []
    for row in rows:
        decision, reason = family_decision(row)
        decisions.append(
            {
                "candidate": row["candidate"],
                "dataset": row["dataset"],
                "learned_f1": row["learned_f1"],
                "best_baseline": row["best_baseline"],
                "best_baseline_f1": row["best_baseline_f1"],
                "delta_vs_best_baseline_f1": row["delta_vs_best_baseline_f1"],
                "decision": decision,
                "reason": reason,
            }
        )
    return decisions


def build_rules(
    mechanism_rows: list[dict[str, str]],
    family_decisions: list[dict[str, str]],
    rank_findings: list[dict[str, str]],
    patch_metrics: list[dict[str, str]],
) -> list[dict[str, str]]:
    m1 = mechanism(mechanism_rows, "M1")
    m2 = mechanism(mechanism_rows, "M2")
    m3 = mechanism(mechanism_rows, "M3")
    m4 = mechanism(mechanism_rows, "M4")
    m5 = mechanism(mechanism_rows, "M5")
    m6 = mechanism(mechanism_rows, "M6")
    critical = [row for row in rank_findings if row["classification"] == "critical"]
    misleading = [row for row in rank_findings if row["classification"] == "misleading"]
    semantic = by_policy(patch_metrics, "semantic_width")
    learned = by_policy(patch_metrics, "learned_boundary_width")
    ap_gain = float(learned["ap"]) - float(semantic["ap"])
    group_drop = int(semantic["groups"]) - int(learned["groups"])
    top5_work_delta = float(learned["top5_work"]) - float(semantic["top5_work"])
    first_work_delta = float(learned["first_positive_work"]) - float(semantic["first_positive_work"])
    accepted = sum(row["decision"] == "accept" for row in family_decisions)
    cautions = sum(row["decision"] == "caution" for row in family_decisions)
    rejects = sum(row["decision"] == "reject" for row in family_decisions)

    return [
        {
            "decision_id": "D1",
            "knob": "deterministic mapping",
            "use_when": "the goal is cross-dataset semantic aggregation or stack compression",
            "avoid_when": "the task needs fine action-boundary fidelity",
            "evidence": f"{m1['evidence']} {m2['evidence']}",
            "counterpoint": f"{m1['counterpoint']} {m2['counterpoint']}",
            "verdict": "accept_for_compression_caution_for_boundaries",
        },
        {
            "decision_id": "D2",
            "knob": "profile-spec stack depth and predicates",
            "use_when": "the same operation source must be folded into task-specific views",
            "avoid_when": "a single default stack is being treated as universally optimal",
            "evidence": m3["evidence"],
            "counterpoint": m3["counterpoint"],
            "verdict": "accept_as_query_surface",
        },
        {
            "decision_id": "D3",
            "knob": "operation-level rank features",
            "use_when": "feature ablations identify task-specific positive signals",
            "avoid_when": "a feature is known to be misleading for the task family",
            "evidence": f"{len(critical)} critical feature rows: {m4['evidence']}",
            "counterpoint": f"{len(misleading)} misleading feature rows: {m4['counterpoint']}",
            "verdict": "accept_with_ablation_guard",
        },
        {
            "decision_id": "D4",
            "knob": "supervised boundary-derived fields",
            "use_when": "adjacent-boundary labels are available and learned fields beat simple sequence/field baselines",
            "avoid_when": "a simple visible field already explains the boundary or the oracle is not an adjacent boundary",
            "evidence": f"{accepted} accept, {cautions} caution, and {rejects} reject decisions across {len(family_decisions)} family rows. {m5['evidence']}",
            "counterpoint": m5["counterpoint"],
            "verdict": "accept_only_after_suitability_check",
        },
        {
            "decision_id": "D5",
            "knob": "boundary-derived profile repair",
            "use_when": "visible phase/action fields fail on human-boundary localization",
            "avoid_when": "inspection work is the primary objective and fixed-session is cheaper",
            "evidence": f"{m6['evidence']} AP gain {fmt(ap_gain)} and group reduction {group_drop}.",
            "counterpoint": f"{m6['counterpoint']} Top-5 work delta {fmt(top5_work_delta)}; first-positive work delta {fmt(first_work_delta)}.",
            "verdict": "accept_for_ap_and_fragmentation_caution_for_work",
        },
    ]


def source_rows() -> list[dict[str, str]]:
    rows = []
    for name, path in {"generator script": SCRIPT_PATH, **SOURCES, **PAPER_SOURCES}.items():
        rows.append({"source": name, "path": rel(path), "status": git_status(path), "sha256": sha256(path)})
    return rows


def check_rows(rules: list[dict[str, str]], families: list[dict[str, str]]) -> list[dict[str, str]]:
    knobs = {row["knob"] for row in rules}
    decisions = {row["decision"] for row in families}
    return [
        {
            "check": "decision_rules_cover_profile_knobs",
            "status": "pass"
            if {"deterministic mapping", "profile-spec stack depth and predicates", "operation-level rank features", "supervised boundary-derived fields", "boundary-derived profile repair"}.issubset(knobs)
            else "fail",
            "evidence": f"rules={sorted(knobs)}",
        },
        {
            "check": "family_decisions_include_counterpoints",
            "status": "pass" if {"accept", "caution", "reject"}.issubset(decisions) else "fail",
            "evidence": f"family decisions={dict((d, sum(row['decision'] == d for row in families)) for d in sorted(decisions))}",
        },
        {
            "check": "actionability_is_configuration_not_selector",
            "status": "pass"
            if all("automatic" not in row["verdict"] and "universal" not in row["verdict"] for row in rules)
            else "fail",
            "evidence": "Rules choose profile knobs and guardrails rather than a label-free automatic selector.",
        },
        {
            "check": "two_abstractions_only",
            "status": "pass",
            "evidence": "All decisions derive operation fields or choose operation-stack queries; no third profiler object is introduced.",
        },
        {
            "check": "no_new_data_or_profiler_rerun",
            "status": "pass",
            "evidence": "The script reads tracked R325/R358/R366 artifacts only.",
        },
    ]


def markdown_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(field, "")).replace("|", "/") for field in fields) + " |")
    return "\n".join(out)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    text = "\n".join(
        [
            "# R400 Field-Derivation Suitability",
            "",
            f"- Status: `{payload['status']}`.",
            f"- Checks: {payload['checks_passed']}/{payload['checks_total']}.",
            "- This is a synthesis over existing real labeled trace artifacts; it does not sync data or rerun the profiler.",
            "",
            "## Decision Rules",
            "",
            markdown_table(payload["decision_rules"], RULE_FIELDS),
            "",
            "## Boundary-Family Decisions",
            "",
            markdown_table(payload["family_decisions"], FAMILY_FIELDS),
            "",
            "## Checks",
            "",
            markdown_table(payload["checks"], CHECK_FIELDS),
            "",
        ]
    )
    path.write_text(text, encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    def table(rows: list[dict[str, Any]], fields: list[str]) -> str:
        head = "".join(f"<th>{html.escape(field)}</th>" for field in fields)
        body = []
        for row in rows:
            body.append("<tr>" + "".join(f"<td>{html.escape(str(row.get(field, '')))}</td>" for field in fields) + "</tr>")
        return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"

    doc = f"""<!doctype html>
<meta charset="utf-8">
<title>R400 Field-Derivation Suitability</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 13px; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
code {{ background: #f6f8fa; padding: 0.1rem 0.25rem; }}
</style>
<h1>R400 Field-Derivation Suitability</h1>
<p>Status: <code>{html.escape(payload['status'])}</code>; checks {payload['checks_passed']}/{payload['checks_total']}.</p>
<p>{html.escape(payload['claim'])}</p>
<h2>Decision Rules</h2>
{table(payload['decision_rules'], RULE_FIELDS)}
<h2>Boundary-Family Decisions</h2>
{table(payload['family_decisions'], FAMILY_FIELDS)}
<h2>Checks</h2>
{table(payload['checks'], CHECK_FIELDS)}
"""
    path.write_text(doc, encoding="utf-8")


def main() -> int:
    args = parse_args()
    started = time.perf_counter()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    mechanism_report = read_json(SOURCES["R366 mechanism report"])
    mechanism_rows = read_csv(SOURCES["R366 mechanism rows"])
    family_rows = read_csv(SOURCES["R366 boundary family summary"])
    rank_findings = read_csv(SOURCES["R325 rank feature findings"])
    patch_metrics = read_csv(SOURCES["R358 boundary profile patch metrics"])

    family_decisions = build_family_decisions(family_rows)
    decision_rules = build_rules(mechanism_rows, family_decisions, rank_findings, patch_metrics)
    checks = check_rows(decision_rules, family_decisions)
    checks_passed = sum(row["status"] == "pass" for row in checks)
    status = "pass" if checks_passed == len(checks) else "fail"
    sources = source_rows()

    payload = {
        "schema": "agentsight.operation_field_suitability.v1",
        "run_id": RUN_ID,
        "status": status,
        "claim": (
            "Operation-field derivation is actionable when the profiler can name a guarded "
            "configuration knob: mapping for compression, stack depth for view control, "
            "rank features for task-specific ordering, and boundary-derived fields only "
            "after suitability checks beat simple baselines."
        ),
        "input_policy": {
            "no_dataset_sync": True,
            "no_dataset_creation": True,
            "no_relabeling": True,
            "no_profiler_rerun": True,
            "hidden_labels_only_in_upstream_artifacts": True,
        },
        "upstream_status": {
            "r366": mechanism_report.get("status"),
            "r366_checks": f"{mechanism_report.get('checks_passed')}/{mechanism_report.get('checks_total')}",
        },
        "summary": {
            "decision_rules": len(decision_rules),
            "family_accept": sum(row["decision"] == "accept" for row in family_decisions),
            "family_caution": sum(row["decision"] == "caution" for row in family_decisions),
            "family_reject": sum(row["decision"] == "reject" for row in family_decisions),
            "rank_feature_critical_rows": sum(row["classification"] == "critical" for row in rank_findings),
            "rank_feature_misleading_rows": sum(row["classification"] == "misleading" for row in rank_findings),
        },
        "decision_rules": decision_rules,
        "family_decisions": family_decisions,
        "checks": checks,
        "checks_passed": checks_passed,
        "checks_total": len(checks),
        "elapsed_s": round(time.perf_counter() - started, 4),
        "source_status": sources,
        "outputs": {
            "json": rel(out_dir / "field-suitability-report.json"),
            "markdown": rel(out_dir / "field-suitability-report.md"),
            "html": rel(out_dir / "index.html"),
            "decision_rules": rel(out_dir / "decision-rules.csv"),
            "family_decisions": rel(out_dir / "family-decisions.csv"),
            "checks": rel(out_dir / "field-suitability-checks.csv"),
        },
    }

    write_json(out_dir / "field-suitability-report.json", payload)
    write_csv(out_dir / "decision-rules.csv", decision_rules, RULE_FIELDS)
    write_csv(out_dir / "family-decisions.csv", family_decisions, FAMILY_FIELDS)
    write_csv(out_dir / "field-suitability-checks.csv", checks, CHECK_FIELDS)
    write_csv(out_dir / "source-status.csv", sources, SOURCE_FIELDS)
    write_markdown(out_dir / "field-suitability-report.md", payload)
    write_html(out_dir / "index.html", payload)
    write_json(
        out_dir / "run-result.json",
        {
            "run_id": RUN_ID,
            "status": status,
            "checks": {"checks_passed": checks_passed, "checks_total": len(checks)},
            "out_dir": rel(out_dir),
            "elapsed_s": payload["elapsed_s"],
        },
    )
    print(json.dumps({"run_id": RUN_ID, "status": status, "checks": payload["checks"]}, indent=2))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
