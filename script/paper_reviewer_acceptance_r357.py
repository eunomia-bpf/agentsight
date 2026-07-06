#!/usr/bin/env python3
"""R357: reviewer-acceptance refresh after the R356 claim-integrity gate.

This is a submission-readiness artifact. It records the current read-only
reviewer closure and mechanically checks that the accepted paper state still
rests on tracked R351/R352/R354/R355/R356 evidence. It does not fetch or sync
datasets, rerun profiler experiments, create labels, or run a human/agent
analyst study.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SUBMODULE_ROOT = ROOT / "docs" / "agentpprof-paper"
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-reviewer-acceptance-r357"

SOURCE_PATHS = {
    "english_paper": SUBMODULE_ROOT / "main.tex",
    "chinese_paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "claim_setup": ROOT / "docs" / "visexp" / "paper" / "evaluation-claims-setup.zh-CN.md",
    "design": ROOT / "docs" / "design.md",
    "implementation": ROOT / "docs" / "implementation.md",
    "evaluation": ROOT / "docs" / "evaluation.md",
    "r351": OUT_ROOT / "paper-reviewer-acceptance-r351" / "reviewer-acceptance.json",
    "r351_run": OUT_ROOT / "paper-reviewer-acceptance-r351" / "run-result.json",
    "r352": OUT_ROOT / "paper-evaluation-rubric-r352" / "evaluation-rubric-report.json",
    "r352_run": OUT_ROOT / "paper-evaluation-rubric-r352" / "run-result.json",
    "r354": OUT_ROOT / "operation-profile-patch-r354" / "profile-patch-report.json",
    "r354_run": OUT_ROOT / "operation-profile-patch-r354" / "run-result.json",
    "r355": OUT_ROOT / "operation-oracle-depth-adequacy-r355" / "oracle-depth-adequacy-report.json",
    "r355_run": OUT_ROOT / "operation-oracle-depth-adequacy-r355" / "run-result.json",
    "r356": OUT_ROOT / "paper-claim-integrity-r356" / "claim-integrity-r356-report.json",
    "r356_run": OUT_ROOT / "paper-claim-integrity-r356" / "run-result.json",
    "r356_numbers": OUT_ROOT / "paper-claim-integrity-r356" / "number-checks.csv",
    "r356_text": OUT_ROOT / "paper-claim-integrity-r356" / "text-coverage.csv",
    "r356_guardrails": OUT_ROOT / "paper-claim-integrity-r356" / "guardrail-checks.csv",
    "r356_abstractions": OUT_ROOT / "paper-claim-integrity-r356" / "abstraction-text-checks.csv",
}

REVIEW_EVENTS = [
    {
        "reviewer": "Linnaeus",
        "agent_id": "019f35f7-af07-7fd1-bc74-975191ba11f9",
        "focus": "OSDI/SOSP systems profiling claim and tradeoff review",
        "final_verdict": "ACCEPT",
        "blocking_issues": [],
        "non_blocking_notes": [
            "The paper preserves flat full-recall, fixed-session first-positive, dataset-native recall, metric, and depth-gap counterpoints.",
        ],
        "rationale": "The scoped claim is label-scored profiler localization/ranking, not human utility or universal automation; baselines, metrics, R354/R355 supplements, and tradeoffs are represented without blocking drift.",
    },
    {
        "reviewer": "Meitner",
        "agent_id": "019f35f7-ca48-7f23-bca8-412091f9197c",
        "focus": "NeurIPS/ML hidden-label evaluation and leakage review",
        "final_verdict": "ACCEPT",
        "blocking_issues": [],
        "non_blocking_notes": [
            "One R356 text-coverage line hit is marked missing because tokens are split across nearby English lines, but the full R355 protocol and counterpoint are present.",
        ],
        "rationale": "R356 keeps labels out of visible profiling/ranking, uses hidden labels only for offline scoring, reports the right baselines and metrics, and keeps R354/R355 non-claims explicit.",
    },
    {
        "reviewer": "Volta",
        "agent_id": "019f35f7-e3a3-7280-b428-6c45447b3c60",
        "focus": "Artifact provenance, source cleanliness, and reproducibility review",
        "final_verdict": "ACCEPT",
        "blocking_issues": [],
        "non_blocking_notes": [
            "Some R356 text-coverage rows can have status pass with line hits missing because line tracing requires all tokens on one line; this is traceability polish, not provenance failure.",
        ],
        "rationale": "The top-level and submodule worktrees were clean at review time, R356 is an audit rather than a new empirical result, source provenance is tracked clean or hashed, and R356 CSV outputs parse with all checks passing.",
    },
    {
        "reviewer": "Beauvoir",
        "agent_id": "019f35f7-fe67-7312-a0e2-e6ba65f9bb23",
        "focus": "Claim-safety and must-not-claim boundary review",
        "final_verdict": "ACCEPT",
        "blocking_issues": [],
        "non_blocking_notes": [],
        "rationale": "The paper scopes value to profiler fidelity and actionable tradeoffs over operation and operation stack, while excluding human utility, automatic selectors, complete boundary discovery, and full trace-ecosystem compatibility.",
    },
]

MUST_NOT_CLAIMS = [
    "human utility",
    "human-productivity",
    "automatic boundary discovery",
    "automatic patch selector",
    "complete compatibility",
    "ecosystem compatibility",
    "universal selector",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def repo_for(path: Path) -> Path:
    resolved = path.resolve()
    if resolved.is_relative_to(SUBMODULE_ROOT.resolve()):
        return SUBMODULE_ROOT
    return ROOT


def repo_rel(path: Path, repo_root: Path | None = None) -> str:
    root = repo_root or ROOT
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def root_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(args: list[str], *, cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SystemExit(f"git {' '.join(args)} failed in {cwd}: {detail}")
    return result


def git_path_status(path: Path, *, require_clean: bool) -> str:
    repo_root = repo_for(path)
    rel = repo_rel(path, repo_root)
    tracked = git_output(["ls-files", "--error-unmatch", rel], cwd=repo_root, check=False)
    if tracked.returncode != 0:
        return "untracked"
    if require_clean:
        dirty = git_output(["diff", "--quiet", "--", rel], cwd=repo_root, check=False)
        if dirty.returncode != 0:
            return "dirty"
        staged = git_output(["diff", "--cached", "--quiet", "--", rel], cwd=repo_root, check=False)
        if staged.returncode != 0:
            return "staged"
        return "tracked_clean"
    return "tracked_hashed"


def ensure_sources_exist() -> None:
    missing = [f"{name}: {root_rel(path)}" for name, path in SOURCE_PATHS.items() if not path.exists()]
    if missing:
        raise SystemExit("missing sources:\n" + "\n".join(missing))


def check(
    rows: list[dict[str, Any]],
    name: str,
    condition: bool,
    evidence: str,
    failure: str,
    *,
    source: str,
    actual: Any = "",
    expected: Any = "",
) -> None:
    rows.append(
        {
            "check": name,
            "status": "pass" if condition else "fail",
            "actual": json.dumps(actual, sort_keys=True) if isinstance(actual, (dict, list)) else str(actual),
            "expected": json.dumps(expected, sort_keys=True) if isinstance(expected, (dict, list)) else str(expected),
            "source": source,
            "evidence": evidence if condition else failure,
        }
    )


def pass_count(rows: list[dict[str, str]]) -> int:
    return sum(row.get("status") == "pass" for row in rows)


def build_source_status() -> list[dict[str, str]]:
    paper_sources = {"english_paper", "chinese_paper", "claim_setup", "design", "implementation", "evaluation"}
    clean_sources = {"r354", "r354_run", "r355", "r355_run"}
    rows: list[dict[str, str]] = []
    for name, path in SOURCE_PATHS.items():
        require_clean = name in clean_sources
        rows.append(
            {
                "source": name,
                "role": "paper_or_doc"
                if name in paper_sources
                else ("tracked_clean_empirical_artifact" if require_clean else "tracked_hashed_audit_artifact"),
                "path": root_rel(path),
                "status": git_path_status(path, require_clean=require_clean),
                "sha256": sha256_file(path),
            }
        )
    return rows


def build_checks(sources: dict[str, Any], texts: dict[str, str], csvs: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    r351 = sources["r351"]
    r351_run = sources["r351_run"]
    r352 = sources["r352"]
    r352_run = sources["r352_run"]
    r354 = sources["r354"]
    r354_run = sources["r354_run"]
    r355 = sources["r355"]
    r355_run = sources["r355_run"]
    r356 = sources["r356"]
    r356_run = sources["r356_run"]

    final_accepts = sum(event["final_verdict"] == "ACCEPT" for event in REVIEW_EVENTS)
    blocking_issues = sum(len(event["blocking_issues"]) for event in REVIEW_EVENTS)
    non_blocking_notes = sum(len(event["non_blocking_notes"]) for event in REVIEW_EVENTS)
    check(
        rows,
        "r357_four_current_reviewers_accept",
        final_accepts == 4,
        "All four current reviewers returned ACCEPT.",
        "At least one current reviewer did not accept.",
        source="REVIEW_EVENTS",
        actual=final_accepts,
        expected=4,
    )
    check(
        rows,
        "r357_no_current_reviewer_blockers",
        blocking_issues == 0,
        "Current reviewer closure has zero blocking issues.",
        "Current reviewer closure has blocking issues.",
        source="REVIEW_EVENTS",
        actual=blocking_issues,
        expected=0,
    )
    check(
        rows,
        "r357_non_blocking_notes_recorded",
        non_blocking_notes == 3,
        "Three non-blocking notes are recorded as traceability/provenance polish, not claim blockers.",
        "Unexpected number of non-blocking notes.",
        source="REVIEW_EVENTS",
        actual=non_blocking_notes,
        expected=3,
    )

    r356_summary = r356["summary"]
    r356_run_summary = r356_run["summary"]
    for source_name, summary in [("r356_report", r356_summary), ("r356_run", r356_run_summary)]:
        check(
            rows,
            f"{source_name}_overall_pass_no_warnings",
            summary["overall"] == "pass" and summary["blocking"] == [] and summary["warnings"] == [],
            "R356 passes with no blockers or warnings.",
            "R356 does not pass cleanly.",
            source=source_name,
            actual={"overall": summary["overall"], "blocking": summary["blocking"], "warnings": summary["warnings"]},
            expected={"overall": "pass", "blocking": [], "warnings": []},
        )
    check(
        rows,
        "r356_number_text_guardrail_counts_pass",
        r356_summary["number_checks_passed"] == 69
        and r356_summary["number_checks_total"] == 69
        and r356_summary["text_checks_passed"] == 18
        and r356_summary["text_checks_total"] == 18
        and r356_summary["guardrail_checks_passed"] == 54
        and r356_summary["guardrail_checks_total"] == 54,
        "R356 passes 69/69 number checks, 18/18 text checks, and 54/54 guardrail checks.",
        "R356 check counts do not match the accepted paper state.",
        source="claim-integrity-r356-report.json",
        actual=r356_summary,
        expected="69/69, 18/18, 54/54",
    )
    check(
        rows,
        "r356_csv_rows_all_pass",
        pass_count(csvs["r356_numbers"]) == 69
        and pass_count(csvs["r356_text"]) == 18
        and pass_count(csvs["r356_guardrails"]) == 54
        and pass_count(csvs["r356_abstractions"]) == len(csvs["r356_abstractions"]),
        "R356 CSV outputs parse cleanly and all rows pass.",
        "One or more R356 CSV rows failed.",
        source="R356 CSV outputs",
        actual={
            "numbers": f"{pass_count(csvs['r356_numbers'])}/{len(csvs['r356_numbers'])}",
            "text": f"{pass_count(csvs['r356_text'])}/{len(csvs['r356_text'])}",
            "guardrails": f"{pass_count(csvs['r356_guardrails'])}/{len(csvs['r356_guardrails'])}",
            "abstractions": f"{pass_count(csvs['r356_abstractions'])}/{len(csvs['r356_abstractions'])}",
        },
        expected="all pass",
    )
    check(
        rows,
        "r356_two_abstraction_and_source_gate",
        r356_summary["profiler_abstractions"] == ["operation", "operation stack"]
        and r356_summary["two_abstraction_boundary"] == "pass"
        and r356_summary["source_artifacts_tracked_clean"] is True
        and r356_summary["network_access_required"] is False,
        "R356 confirms tracked-clean sources, no network requirement, and only operation plus operation stack abstractions.",
        "R356 abstraction/source gate does not match the scoped claim.",
        source="claim-integrity-r356-report.json",
        actual=r356_summary,
        expected="tracked clean, network false, operation/operation stack",
    )

    r354_summary = r354["summary"]
    check(
        rows,
        "r354_profile_patch_actionability_supported",
        r354["status"] == "pass"
        and r354_run["status"] == "pass"
        and r354_summary["accepted_patches"] == "5/6"
        and r354_summary["rejected_or_needs_mapping"] == "1/6"
        and abs(float(r354_summary["median_delta_ap"]) - 0.0376) < 0.00005
        and abs(float(r354_summary["median_delta_top5_lift"]) - 0.5750) < 0.0002
        and abs(float(r354_summary["median_delta_first_positive_work"]) - (-0.0859)) < 0.00005,
        "R354 supports executable profile-spec actionability with 5/6 accepted patches and the accepted AP/lift/work deltas.",
        "R354 actionability numbers do not match accepted paper state.",
        source="profile-patch-report.json",
        actual=r354_summary,
        expected="5/6 accepted, 1/6 rejected, 0.0376 AP, 0.5750 lift, -0.0859 WTFP",
    )
    check(
        rows,
        "r354_nonclaims_preserved",
        any("not a human or agent analyst study" in item.lower() for item in r354["non_claims"])
        and any("not an automatic label-free patch selector" in item.lower() for item in r354["non_claims"])
        and any("only profiler objects are operations and operation stacks" in item.lower() for item in r354["non_claims"]),
        "R354 non-claims rule out human utility, automatic patch selection, and extra profiler abstractions.",
        "R354 non-claim guardrails are missing.",
        source="profile-patch-report.json",
        actual=r354["non_claims"],
        expected="human/agent analyst false, auto patch selector false, two abstractions",
    )

    r355_claim = r355["claim_summary"]
    paired = r355_claim["paired_checks"]
    medians = r355_claim["default_all_depth_medians"]
    check(
        rows,
        "r355_oracle_depth_adequacy_supported",
        r355["status"] == "pass"
        and r355_run["status"] == "pass"
        and r355_claim["accuracy_unit_depth_rows"] == 24
        and abs(float(medians["budget30_positive_unit_recall"]) - 0.4342) < 0.00005
        and abs(float(medians["budget30_positive_unit_f1"]) - 0.4484) < 0.00005
        and abs(float(r355_claim["positive_run_medians"]["budget30_positive_unit_recall"]) - 0.4908) < 0.00005
        and paired["budget30_unit_recall_gt_fixed_rows"] == 20
        and paired["budget30_unit_f1_gt_fixed_rows"] == 18
        and paired["groups_to_50pct_units_lt_fixed_rows"] == 22
        and paired["depth_gap_lt_fixed_rows"] == 0,
        "R355 supports oracle-depth triage while preserving the fixed-session depth-gap counterpoint.",
        "R355 oracle-depth numbers do not match accepted paper state.",
        source="oracle-depth-adequacy-report.json",
        actual={"claim": r355_claim, "paired": paired},
        expected="24 rows, 0.4342 recall, 0.4484 F1, 0.4908 positive-run recall, 20/24, 18/24, 22/24, depth gap 0",
    )
    check(
        rows,
        "r355_nonclaims_preserved",
        any("does not claim automatic discovery of all intent boundaries" in item.lower() for item in r355["non_claims"])
        and any("positive-run units are derived proxy episodes" in item.lower() for item in r355["non_claims"])
        and any("not a human or agent analyst study" in item.lower() for item in r355["non_claims"]),
        "R355 non-claims rule out automatic boundary discovery, identify positive-run as proxy, and avoid human-study claims.",
        "R355 non-claim guardrails are missing.",
        source="oracle-depth-adequacy-report.json",
        actual=r355["non_claims"],
        expected="auto boundary false, positive-run proxy, no human study",
    )

    r352_summary = r352["summary"]
    check(
        rows,
        "r352_rubric_gate_still_passes",
        r352["status"] == "ok"
        and r352_run["status"] == "ok"
        and r352_summary["overall"] == "pass"
        and r352_summary["required_checks_passed"] == 26
        and r352_summary["required_checks_total"] == 26
        and r352_summary["rubric_level"] == "level_4_scoped_profile_benchmark",
        "R352 still classifies the evidence as a level_4_scoped_profile_benchmark with 26/26 required checks.",
        "R352 rubric gate no longer matches accepted state.",
        source="evaluation-rubric-report.json",
        actual=r352_summary,
        expected="level_4_scoped_profile_benchmark, 26/26",
    )
    check(
        rows,
        "r351_prior_reviewer_gate_still_accepted",
        r351["overall"] == "accepted"
        and r351_run["overall"] == "accepted"
        and r351["summary"]["final_accepts"] == 4
        and r351["summary"]["blocking_issues"] == 0
        and r351["summary"]["checks_passed"] == r351["summary"]["checks_total"],
        "R351 prior reviewer gate remains accepted with 4 accepts, zero blockers, and all checks passing.",
        "R351 prior reviewer gate is not accepted.",
        source="reviewer-acceptance-r351.json",
        actual=r351["summary"],
        expected="4 accepts, 0 blockers, all checks pass",
    )

    combined_text = "\n".join(texts.values()).lower()
    check(
        rows,
        "must_not_claim_boundaries_visible",
        all(token in combined_text for token in MUST_NOT_CLAIMS),
        "Current docs/papers visibly preserve human-utility, automatic-boundary, automatic-selector, ecosystem-compatibility, and universal-selector guardrails.",
        "One or more must-not-claim boundary tokens is missing from the current docs/papers.",
        source="paper and docs text",
        actual={token: token in combined_text for token in MUST_NOT_CLAIMS},
        expected={token: True for token in MUST_NOT_CLAIMS},
    )
    check(
        rows,
        "r357_documentation_anchor_present",
        "R357" in texts["evaluation"]
        and "four current reviewer ACCEPT verdicts" in texts["evaluation"]
        and "not a new empirical result" in texts["evaluation"],
        "docs/evaluation.md records R357 as a reviewer-acceptance refresh, not a new empirical result.",
        "docs/evaluation.md does not yet describe R357 correctly.",
        source="docs/evaluation.md",
        actual="R357" in texts["evaluation"],
        expected=True,
    )
    check(
        rows,
        "two_abstraction_language_visible",
        "operation and operation stack" in texts["evaluation"].lower()
        and "operation stack" in texts["english_paper"].lower()
        and "operation stack" in texts["chinese_paper"].lower(),
        "Current drafts and evaluation docs keep operation and operation stack as the profiler abstractions.",
        "Two-abstraction language is not visible in current texts.",
        source="paper and docs text",
        actual="operation stack present",
        expected="operation and operation stack",
    )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Paper Reviewer Acceptance R357",
        "",
        "R357 records a reviewer-acceptance refresh after R356. It is a submission-readiness gate, not a new empirical result, not a human/agent analyst study, and not a trace-ecosystem compatibility test.",
        "",
        "## Verdict",
        "",
        f"- Overall: {payload['overall']}.",
        f"- Current reviewer accepts: {payload['summary']['final_accepts']}/{payload['summary']['reviewers']}.",
        f"- Current reviewer blocking issues: {payload['summary']['blocking_issues']}.",
        f"- Non-blocking notes: {payload['summary']['non_blocking_notes']}.",
        f"- Mechanical checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.",
        "",
        "## Checks",
        "",
        "| Check | Status | Evidence |",
        "|---|---|---|",
    ]
    for row in payload["checks"]:
        lines.append(f"| {row['check']} | {row['status']} | {row['evidence']} |")
    lines.extend(
        [
            "",
            "## Reviewers",
            "",
            "| Reviewer | Focus | Verdict | Blocking | Notes |",
            "|---|---|---|---:|---:|",
        ]
    )
    for event in payload["review_events"]:
        lines.append(
            f"| {event['reviewer']} | {event['focus']} | {event['final_verdict']} | {len(event['blocking_issues'])} | {len(event['non_blocking_notes'])} |"
        )
    lines.extend(["", "## Non-Claims", ""])
    for item in payload["claim_scope"]["does_not_support"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    check_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['check'])}</td>"
        f"<td>{html.escape(row['status'])}</td>"
        f"<td>{html.escape(row['evidence'])}</td>"
        "</tr>"
        for row in payload["checks"]
    )
    reviewer_rows = "\n".join(
        "<tr>"
        f"<th>{html.escape(event['reviewer'])}</th>"
        f"<td>{html.escape(event['focus'])}</td>"
        f"<td>{html.escape(event['final_verdict'])}</td>"
        f"<td>{len(event['blocking_issues'])}</td>"
        f"<td>{len(event['non_blocking_notes'])}</td>"
        "</tr>"
        for event in payload["review_events"]
    )
    path.write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paper Reviewer Acceptance R357</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }
    h1 { font-size: 1.6rem; }
    p, li { max-width: 920px; line-height: 1.5; }
    table { border-collapse: collapse; margin-top: 1.25rem; min-width: 940px; }
    th, td { border: 1px solid #d8dee9; padding: 0.5rem 0.65rem; text-align: left; vertical-align: top; }
    th { background: #f6f8fa; }
  </style>
</head>
<body>
  <h1>Paper Reviewer Acceptance R357</h1>
  <p>Reviewer-acceptance refresh after R356. This is a submission-readiness gate, not a new empirical result.</p>
  <h2>Checks</h2>
  <table>
    <tr><th>Check</th><th>Status</th><th>Evidence</th></tr>
"""
        + check_rows
        + """
  </table>
  <h2>Reviewers</h2>
  <table>
    <tr><th>Reviewer</th><th>Focus</th><th>Verdict</th><th>Blocking</th><th>Notes</th></tr>
"""
        + reviewer_rows
        + """
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
    ensure_sources_exist()

    json_sources = {
        name: load_json(path)
        for name, path in SOURCE_PATHS.items()
        if name.startswith("r") and path.suffix == ".json"
    }
    texts = {
        name: path.read_text(encoding="utf-8")
        for name, path in SOURCE_PATHS.items()
        if name in {"english_paper", "chinese_paper", "claim_setup", "design", "implementation", "evaluation"}
    }
    csvs = {
        name: read_csv(path)
        for name, path in SOURCE_PATHS.items()
        if name.startswith("r356_") and path.suffix == ".csv"
    }
    checks = build_checks(json_sources, texts, csvs)
    source_status = build_source_status()

    final_accepts = sum(event["final_verdict"] == "ACCEPT" for event in REVIEW_EVENTS)
    blocking_issues = sum(len(event["blocking_issues"]) for event in REVIEW_EVENTS)
    non_blocking_notes = sum(len(event["non_blocking_notes"]) for event in REVIEW_EVENTS)
    checks_passed = sum(row["status"] == "pass" for row in checks)
    overall = "accepted" if checks_passed == len(checks) and blocking_issues == 0 else "needs_changes"
    source_gate = all(
        row["status"] in {"tracked_clean", "tracked_hashed"}
        for row in source_status
    )

    report_json = out_dir / "reviewer-acceptance-r357.json"
    report_md = out_dir / "reviewer-acceptance-r357.md"
    review_csv = out_dir / "reviewer-verdicts.csv"
    checks_csv = out_dir / "acceptance-checks.csv"
    source_csv = out_dir / "source-status.csv"
    index_html = out_dir / "index.html"
    run_result = out_dir / "run-result.json"

    report = {
        "run_id": "R357",
        "schema": "agentsight.paper-reviewer-acceptance-r357.v1",
        "status": "ok" if overall == "accepted" and source_gate else "needs_changes",
        "overall": overall if source_gate else "needs_changes",
        "commit": git_output(["rev-parse", "HEAD"]).stdout.strip(),
        "input_policy": {
            "sources": "current paper/docs plus tracked R351/R352/R354/R355/R356 artifacts",
            "dataset_sync": "none",
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "profiler_rerun": "none inside R357",
            "human_or_agent_analyst_task": "none",
            "network_access_required": False,
        },
        "not_new_empirical_result": True,
        "not_a_human_study_result": True,
        "not_an_agent_analyst_task_result": True,
        "network_access_required": False,
        "profiler_abstractions": ["operation", "operation stack"],
        "summary": {
            "reviewers": len(REVIEW_EVENTS),
            "final_accepts": final_accepts,
            "blocking_issues": blocking_issues,
            "non_blocking_notes": non_blocking_notes,
            "checks_passed": checks_passed,
            "checks_total": len(checks),
            "source_gate": "pass" if source_gate else "fail",
            "r356_number_checks": "69/69",
            "r356_text_checks": "18/18",
            "r356_guardrail_checks": "54/54",
            "r354_accepted_patches": json_sources["r354"]["summary"]["accepted_patches"],
            "r354_median_delta_ap": json_sources["r354"]["summary"]["median_delta_ap"],
            "r354_median_delta_top5_lift": json_sources["r354"]["summary"]["median_delta_top5_lift"],
            "r355_accuracy_task_depth_rows": json_sources["r355"]["claim_summary"]["accuracy_unit_depth_rows"],
            "r355_budget30_unit_recall": json_sources["r355"]["claim_summary"]["default_all_depth_medians"]["budget30_positive_unit_recall"],
            "r355_fixed_recall_wins": json_sources["r355"]["claim_summary"]["paired_checks"]["budget30_unit_recall_gt_fixed_rows"],
            "r352_rubric_level": json_sources["r352"]["summary"]["rubric_level"],
            "r351_final_accepts": json_sources["r351"]["summary"]["final_accepts"],
        },
        "checks": checks,
        "source_status": source_status,
        "review_events": REVIEW_EVENTS,
        "claim_scope": {
            "supports": [
                "current reviewer acceptance of the scoped R356 paper state",
                "submission-readiness for a profiler-localization paper claim",
                "continued alignment between R354/R355/R356 evidence and the two-abstraction operation/operation-stack design",
            ],
            "does_not_support": [
                "human or agent analyst accuracy/productivity/time-to-answer improvement",
                "automatic discovery of all intent or subtask boundaries",
                "complete OpenTelemetry/Phoenix/LangSmith/Langfuse/Perfetto compatibility",
                "automatic label-free patch or action selection",
                "universal dominance over flat, fixed-session/span-tree, dataset-native, or raw-action views",
            ],
        },
        "outputs": {
            "json": root_rel(report_json),
            "markdown": root_rel(report_md),
            "reviewer_csv": root_rel(review_csv),
            "checks_csv": root_rel(checks_csv),
            "source_csv": root_rel(source_csv),
            "html": root_rel(index_html),
            "run_result": root_rel(run_result),
        },
    }

    write_json(report_json, report)
    write_markdown(report_md, report)
    write_csv(
        review_csv,
        [
            {
                "reviewer": event["reviewer"],
                "agent_id": event["agent_id"],
                "focus": event["focus"],
                "final_verdict": event["final_verdict"],
                "blocking_issue_count": len(event["blocking_issues"]),
                "non_blocking_note_count": len(event["non_blocking_notes"]),
                "rationale": event["rationale"],
            }
            for event in REVIEW_EVENTS
        ],
        ["reviewer", "agent_id", "focus", "final_verdict", "blocking_issue_count", "non_blocking_note_count", "rationale"],
    )
    write_csv(checks_csv, checks, ["check", "status", "actual", "expected", "source", "evidence"])
    write_csv(source_csv, source_status, ["source", "role", "path", "status", "sha256"])
    write_html(index_html, report)
    write_json(
        run_result,
        {
            "run_id": "R357",
            "status": report["status"],
            "overall": report["overall"],
            "report": root_rel(report_json),
            "html": root_rel(index_html),
            "reviewers": len(REVIEW_EVENTS),
            "final_accepts": final_accepts,
            "blocking_issues": blocking_issues,
            "non_blocking_notes": non_blocking_notes,
            "checks_passed": checks_passed,
            "checks_total": len(checks),
            "source_gate": "pass" if source_gate else "fail",
            "not_new_empirical_result": True,
            "not_a_human_study_result": True,
            "not_an_agent_analyst_task_result": True,
            "network_access_required": False,
        },
    )
    print(json.dumps(load_json(run_result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
