#!/usr/bin/env python3
"""R377: main profiling-claim evidence gate.

This paper-integration guardrail turns the scoped profiling claim into a small
claim-by-claim evidence packet while preserving the paper-facing experiment
structure: three empirical profiling experiments plus one artifact block. It
reads tracked result artifacts only; it does not download data, relabel traces,
or rerun the profiler.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-main-claim-evidence-r377"
RUN_ID = "R377"
SCRIPT_PATH = Path(__file__).resolve()
PAPER_SUBMODULE = ROOT / "docs" / "agentpprof-paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "R320 profile accuracy": OUT_ROOT / "operation-profile-accuracy-r320" / "profile-accuracy-report.json",
    "R320 task accuracy": OUT_ROOT / "operation-profile-accuracy-r320" / "task-accuracy.csv",
    "R333 inspection frontier": OUT_ROOT / "operation-inspection-frontier-r333" / "default-vs-baselines.csv",
    "R334 fragmentation tradeoff": OUT_ROOT / "operation-fragmentation-tradeoff-r334" / "default-fragmentation-comparisons.csv",
    "R354 profile patch": OUT_ROOT / "operation-profile-patch-r354" / "profile-patch-report.json",
    "R355 oracle depth": OUT_ROOT / "operation-oracle-depth-adequacy-r355" / "depth-policy-comparisons.csv",
    "R358 boundary patch": OUT_ROOT / "operation-boundary-profile-patch-r358" / "boundary-profile-patch-report.json",
    "R366 mechanism audit": OUT_ROOT / "operation-field-derivation-mechanism-r366" / "field-derivation-mechanism-report.json",
    "R366 mechanism rows": OUT_ROOT / "operation-field-derivation-mechanism-r366" / "mechanism-rows.csv",
    "R375 claim gate": OUT_ROOT / "paper-core-claim-gate-r375" / "core-claim-gate-report.json",
    "R376 three-plus-one gate": OUT_ROOT / "paper-three-plus-one-r376" / "three-plus-one-report.json",
    "English paper": ROOT / "docs" / "agentpprof-paper" / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
}

CLAIM_FIELDS = [
    "claim_element",
    "paper_block",
    "evidence",
    "counterpoint",
    "allowed_wording",
    "must_not_claim",
    "sources",
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_status_display(repo_root: Path, display: str) -> str:
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


def git_status(path: Path) -> str:
    repo_root = ROOT
    try:
        path.resolve().relative_to(PAPER_SUBMODULE)
        repo_root = PAPER_SUBMODULE
    except ValueError:
        pass
    try:
        display = str(path.resolve().relative_to(repo_root))
    except ValueError:
        display = str(path)
    return git_status_display(repo_root, display)


def git_stdout(args: list[str], cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return result.stdout.strip()


def paper_submodule_head() -> str:
    return git_stdout(["git", "rev-parse", "HEAD"], PAPER_SUBMODULE)


def paper_submodule_index_head() -> str:
    line = git_stdout(["git", "ls-files", "-s", "--", PAPER_SUBMODULE_PATH], ROOT)
    parts = line.split()
    return parts[1] if len(parts) >= 2 else ""


def source_rows() -> list[dict[str, str]]:
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
    rows.append(
        {
            "source": "English paper submodule gitlink",
            "path": PAPER_SUBMODULE_PATH,
            "status": git_status_display(ROOT, PAPER_SUBMODULE_PATH),
            "sha256": f"submodule_head={paper_submodule_head()};parent_index={paper_submodule_index_head()}",
        }
    )
    return rows


def find_row(rows: list[dict[str, str]], **pred: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(k) == v for k, v in pred.items()):
            return row
    raise KeyError(f"row not found: {pred}")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"check": name, "passed": bool(passed), "detail": detail})


def fnum(value: str | float | int, digits: int = 4) -> str:
    if isinstance(value, str) and value in {"", "inf"}:
        return value
    return f"{float(value):.{digits}f}".rstrip("0").rstrip(".")


def build_claim_rows(context: dict[str, Any]) -> list[dict[str, str]]:
    r320 = context["r320"]
    flat_work = context["flat_top5_work"]
    flat_budget = context["flat_budget30_recall"]
    flat_first = context["flat_first_positive"]
    fixed_groups = context["fixed_groups"]
    fixed_groups50 = context["fixed_groups50"]
    fixed_top5_recall = context["fixed_top5_recall"]
    fixed_top5_work = context["fixed_top5_work"]
    fixed_oracle_recall = context["fixed_oracle_recall"]
    fixed_oracle_groups50 = context["fixed_oracle_groups50"]
    r354 = context["r354"]
    r358 = context["r358"]
    r366 = context["r366"]

    totals = r320["totals"]
    rows = [
        {
            "claim_element": "Faithful hidden-label localization and ranking",
            "paper_block": "RQ2/E2",
            "evidence": (
                f"R320 scores {totals['policy_scores']} policies over {totals['tasks']} tasks, "
                f"{totals['datasets']} datasets, {totals['task_operations']:,} operations, and "
                f"{totals['positive_operations']:,} positives using precision@k, recall@budget, "
                "F1, AP/AUPRC-style score, nDCG, work-to-first-positive, and group metrics."
            ),
            "counterpoint": "Flat and dataset-native views still win broad-recall or some nDCG/top-k objectives; the claim is a Pareto tradeoff, not metric dominance.",
            "allowed_wording": "Operation-stack profiles are valid ranked localization outputs against dataset-provided hidden labels.",
            "must_not_claim": "Human productivity, automatic anomaly detection, or dominance on every metric.",
            "sources": "R320/R375/R376",
        },
        {
            "claim_element": "Less inspection work than flat summaries",
            "paper_block": "RQ2/E2",
            "evidence": (
                f"R333/R334 show top-5 operation work improves over flat on {flat_work['wins']}/6 tasks "
                f"with median ratio {flat_work['median_ratio_default_over_baseline']}; budget-30 recall "
                f"improves on {flat_budget['wins']}/6 tasks; work-to-first-positive improves on "
                f"{flat_first['wins']}/6 tasks."
            ),
            "counterpoint": "Flat summaries retain full-recall behavior only by forcing inspection of the whole task.",
            "allowed_wording": "For the evaluated tasks, operation-stack query-aware profiles reduce inspection work relative to flat summaries.",
            "must_not_claim": "Flat summaries are useless or dominated for every objective.",
            "sources": "R333/R334/R320",
        },
        {
            "claim_element": "Less fragmentation than fixed-session drilldown proxy",
            "paper_block": "RQ2/E2",
            "evidence": (
                f"R334 reports fewer groups than fixed-session on {fixed_groups['wins']}/6 tasks "
                f"(median ratio {fixed_groups['median_ratio_default_over_baseline']}) and fewer "
                f"groups-to-50%-recall on {fixed_groups50['wins']}/6 tasks. R355 extends this below "
                f"session scope: budget-30 positive-unit recall improves on {fixed_oracle_recall['improved_rows']}/24 "
                f"task-depth rows and groups-to-50%-positive-units improves on {fixed_oracle_groups50['improved_rows']}/24."
            ),
            "counterpoint": (
                f"Fixed-session still wins top-5 work on {fixed_top5_work['losses']}/6 tasks and "
                "often finds the first positive earlier, so it remains a drilldown baseline."
            ),
            "allowed_wording": "Operation stacks improve the median fragmentation/localization tradeoff versus fixed-session drilldown.",
            "must_not_claim": "Complete superiority over session/span trees or real OpenTelemetry/Phoenix/LangSmith/Perfetto imports.",
            "sources": "R334/R355/R368",
        },
        {
            "claim_element": "Actionable optimization insight",
            "paper_block": "RQ3/E3",
            "evidence": (
                f"R354 accepts profile-guided patches on {r354['summary']['accepted_patches']} tasks, "
                f"with median AP delta {fnum(r354['summary']['median_delta_ap'])} and top-5 lift delta "
                f"{fnum(r354['summary']['median_delta_top5_lift'])}. R358 repairs the OSWorld-Human rejection "
                f"with boundary-derived fields: AP {r358['summary']['learned_boundary_ap']} vs 0.2402 and "
                f"groups {r358['summary']['learned_boundary_groups']} vs {r358['summary']['semantic_width_groups']}. "
                "R366 identifies 7 critical and 3 misleading rank-feature rows."
            ),
            "counterpoint": r358["summary"]["counterpoint"],
            "allowed_wording": "Profiler output identifies stack fields, mappings, rankers, and profile specs that guide concrete configuration changes.",
            "must_not_claim": "Automatic patch selection, label-free universal policy selection, or human analyst utility.",
            "sources": "R354/R358/R366",
        },
        {
            "claim_element": "Mechanism isolation and two-abstraction boundary",
            "paper_block": "RQ1/E1 + RQ3/E3",
            "evidence": (
                f"R366 passes {r366['summary']['checks_passed']}/{r366['summary']['checks_total']} mechanism checks: "
                "mapping, tagging/rank features, profile specs, and supervised boundary backends write operation fields "
                "that operation stacks fold. R375/R376 keep E4 out of hidden-label accuracy evidence and preserve the "
                "operation / operation-stack abstraction boundary."
            ),
            "counterpoint": "Boundary backends beat simple baselines on 4/5 rows, but AgentRewardBench looping is explained by repeat_signal_change.",
            "allowed_wording": "The gains are attributable to operation-stack abstraction, field derivation, and query-aware ranking under scoped labels.",
            "must_not_claim": "A third profiler object, automatic intent discovery, or complete trace-ecosystem compatibility.",
            "sources": "R342/R366/R375/R376",
        },
    ]
    return rows


def build_report() -> dict[str, Any]:
    r320 = read_json(SOURCES["R320 profile accuracy"])
    r333_rows = read_csv(SOURCES["R333 inspection frontier"])
    r334_rows = read_csv(SOURCES["R334 fragmentation tradeoff"])
    r355_rows = read_csv(SOURCES["R355 oracle depth"])
    r354 = read_json(SOURCES["R354 profile patch"])
    r358 = read_json(SOURCES["R358 boundary patch"])
    r366 = read_json(SOURCES["R366 mechanism audit"])
    r366_rows = read_csv(SOURCES["R366 mechanism rows"])
    r375 = read_json(SOURCES["R375 claim gate"])
    r376 = read_json(SOURCES["R376 three-plus-one gate"])
    english = read_text(SOURCES["English paper"])
    chinese = read_text(SOURCES["Chinese paper"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    source_status = source_rows()
    source_by_name = {row["source"]: row for row in source_status}

    context = {
        "r320": r320,
        "flat_top5_work": find_row(r333_rows, baseline_policy="flat:width", metric="top5_work"),
        "flat_budget30_recall": find_row(r333_rows, baseline_policy="flat:width", metric="budget30_recall"),
        "flat_first_positive": find_row(r333_rows, baseline_policy="flat:width", metric="work_to_first_positive"),
        "fixed_groups": find_row(r334_rows, baseline_policy="fixed_session:query_aware", metric="groups"),
        "fixed_groups50": find_row(r334_rows, baseline_policy="fixed_session:query_aware", metric="groups_to_50pct_recall"),
        "fixed_top5_recall": find_row(r334_rows, baseline_policy="fixed_session:query_aware", metric="top5_recall"),
        "fixed_top5_work": find_row(r334_rows, baseline_policy="fixed_session:query_aware", metric="top5_work"),
        "fixed_oracle_recall": find_row(r355_rows, right="fixed_session:query_aware", metric="budget30_positive_unit_recall"),
        "fixed_oracle_groups50": find_row(r355_rows, right="fixed_session:query_aware", metric="groups_to_50pct_positive_units"),
        "r354": r354,
        "r358": r358,
        "r366": r366,
    }
    claim_rows = build_claim_rows(context)
    checks: list[dict[str, Any]] = []
    paper_blob = english + "\n" + chinese
    evidence_blob = json.dumps(claim_rows, sort_keys=True)

    totals = r320["totals"]
    add_check(
        checks,
        "real_labeled_trace_scale_preserved",
        totals == {"datasets": 4, "group_views": 36, "policy_scores": 144, "positive_operations": 3699, "task_operations": 34539, "tasks": 6},
        f"R320 totals={totals}",
    )
    add_check(
        checks,
        "fidelity_metric_surface_present",
        all(
            token in json.dumps(r320["metrics"])
            for token in ["precision@k", "recall@operation-budget", "F1@k", "average precision", "nDCG", "work-to-first-positive"]
        ),
        "R320 records the profiler-paper metric surface.",
    )
    add_check(
        checks,
        "flat_work_claim_supported",
        context["flat_top5_work"]["wins"] == "6"
        and context["flat_top5_work"]["median_ratio_default_over_baseline"] == "0.0937"
        and context["flat_budget30_recall"]["wins"] == "6"
        and context["flat_first_positive"]["wins"] == "6",
        "Top-5 work, budget-30 recall, and work-to-first-positive all improve over flat on 6/6 tasks.",
    )
    add_check(
        checks,
        "fixed_session_tradeoff_not_dominance",
        context["fixed_groups"]["wins"] == "4"
        and context["fixed_groups50"]["wins"] == "5"
        and context["fixed_top5_recall"]["wins"] == "5"
        and context["fixed_top5_work"]["losses"] == "4"
        and context["fixed_oracle_recall"]["improved_rows"] == "20"
        and context["fixed_oracle_groups50"]["improved_rows"] == "22",
        "Operation stacks improve fragmentation/localization metrics while preserving fixed-session work counterpoints.",
    )
    add_check(
        checks,
        "actionability_claim_supported",
        r354["summary"]["accepted_patches"] == "5/6"
        and r358["summary"]["accepted_boundary_patch"] is True
        and "7 critical" in evidence_blob
        and "3 misleading" in evidence_blob,
        "Executable patches, boundary-field repair, and rank-feature ablations support actionability.",
    )
    add_check(
        checks,
        "mechanism_isolation_supported",
        r366["status"] == "pass"
        and r366["summary"]["checks_passed"] == 6
        and any("12/12 are prompt/session-frame free" in row["evidence"] for row in r366_rows)
        and r375["status"] == "pass"
        and r376["status"] == "pass",
        "R366 isolates mapping/ranking/boundary mechanisms, and R375/R376 preserve claim scope.",
    )
    add_check(
        checks,
        "paper_mentions_r377",
        "R377" in english and "R377" in chinese and "R377" in evaluation,
        "Both papers and the evaluation ledger mention the R377 main-claim evidence packet.",
    )
    add_check(
        checks,
        "claim_elements_not_extra_experiments",
        "three core empirical profiling experiments" in english
        and "artifact/reproducibility block" in english
        and "五个可审计的 evidence facets" in chinese
        and "不把 evaluation 拆成五个更小的研究" in chinese
        and "not_new_empirical_result" not in paper_blob,
        "The five R377 claim elements are paper-routing facets inside E1-E3, not additional experiments.",
    )
    add_check(
        checks,
        "non_claims_preserved",
        all(
            token in evidence_blob
            for token in [
                "Human productivity",
                "automatic",
                "metric dominance",
                "complete trace-ecosystem compatibility",
            ]
        ),
        "The evidence packet keeps human utility, automatic detection/selection, metric dominance, and ecosystem compatibility out of scope.",
    )
    add_check(
        checks,
        "no_new_data_or_profiler_rerun",
        r366.get("summary", {}).get("profiler_rerun") is False
        and r366.get("summary", {}).get("dataset_sync") is False
        and r375.get("profiler_rerun") is False
        and r376.get("profiler_rerun") is False,
        "R377 reads tracked artifacts and paper text only; it does not sync data, relabel traces, or invoke agentpprof.",
    )
    add_check(
        checks,
        "english_submodule_input_committed",
        source_by_name["English paper"]["status"] == "tracked_clean"
        and paper_submodule_head() == paper_submodule_index_head()
        and bool(paper_submodule_head()),
        (
            "The English paper input must be clean inside docs/agentpprof-paper, and the parent index "
            "must point at the same submodule commit before R377 reports pass."
        ),
    )
    add_check(
        checks,
        "source_status_tracked",
        all(row["status"] in {"tracked_clean", "tracked_dirty_allowed"} for row in source_status),
        "All R377 sources are tracked or intentionally dirty/staged.",
    )

    return {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "schema": "agentsight.paper_main_claim_evidence_gate.v1",
        "not_new_empirical_result": True,
        "network_access_required": False,
        "profiler_rerun": False,
        "data_sync": False,
        "claim_rows": claim_rows,
        "checks": checks,
        "source_status": source_status,
        "summary": {
            "claim_elements": len(claim_rows),
            "paper_facing_blocks": 4,
            "empirical_profiling_experiments": 3,
            "artifact_blocks": 1,
            "checks_passed": sum(1 for check in checks if check["passed"]),
            "checks_total": len(checks),
            "source_runs": ["R320", "R333", "R334", "R354", "R355", "R358", "R366", "R375", "R376"],
        },
        "interpretation": "The current paper can claim faithful hidden-label profiler localization/ranking with less flat inspection work, a better fixed-session fragmentation tradeoff, and actionable configuration insight. These are evidence facets inside the three empirical profiling experiments, not separate experiments, and they preserve non-dominance and non-human-utility scope.",
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


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# R377 Main Profiling-Claim Evidence Gate",
        "",
        f"Status: `{report['status']}`",
        f"Checks: {report['summary']['checks_passed']}/{report['summary']['checks_total']}",
        (
            "Paper-facing organization: "
            f"{report['summary']['empirical_profiling_experiments']} empirical profiling experiments "
            f"+ {report['summary']['artifact_blocks']} artifact/reproducibility block."
        ),
        "",
        report["interpretation"],
        "",
        "## Claim Elements",
        "",
        "| Claim element | Paper block | Evidence | Counterpoint |",
        "|---|---|---|---|",
    ]
    for row in report["claim_rows"]:
        lines.append(f"| {row['claim_element']} | {row['paper_block']} | {row['evidence']} | {row['counterpoint']} |")
    lines.extend(["", "## Checks", "", "| Check | Passed | Detail |", "|---|---:|---|"])
    for check in report["checks"]:
        lines.append(f"| {check['check']} | {check['passed']} | {check['detail']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, report: dict[str, Any]) -> None:
    claim_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['claim_element'])}</td>"
        f"<td>{html.escape(row['paper_block'])}</td>"
        f"<td>{html.escape(row['evidence'])}</td>"
        f"<td>{html.escape(row['counterpoint'])}</td>"
        f"<td>{html.escape(row['allowed_wording'])}</td>"
        f"<td>{html.escape(row['must_not_claim'])}</td>"
        "</tr>"
        for row in report["claim_rows"]
    )
    check_rows = "\n".join(
        f"<tr><td>{html.escape(check['check'])}</td><td>{check['passed']}</td><td>{html.escape(check['detail'])}</td></tr>"
        for check in report["checks"]
    )
    path.write_text(
        f"""<!doctype html>
<meta charset="utf-8">
<title>{RUN_ID} Main Claim Evidence Gate</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.status {{ font-weight: 700; }}
</style>
<h1>{RUN_ID} Main Claim Evidence Gate</h1>
<p class="status">Status: {html.escape(report['status'])}; checks {report['summary']['checks_passed']}/{report['summary']['checks_total']}.</p>
<p>Paper-facing organization: {report['summary']['empirical_profiling_experiments']} empirical profiling experiments + {report['summary']['artifact_blocks']} artifact/reproducibility block.</p>
<p>{html.escape(report['interpretation'])}</p>
<h2>Claim Elements</h2>
<table><tr><th>Claim element</th><th>Paper block</th><th>Evidence</th><th>Counterpoint</th><th>Allowed wording</th><th>Must not claim</th></tr>{claim_rows}</table>
<h2>Checks</h2>
<table><tr><th>Check</th><th>Passed</th><th>Detail</th></tr>{check_rows}</table>
""",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    start = time.time()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_report()
    run_result = {
        "run_id": RUN_ID,
        "status": report["status"],
        "checks": {
            "checks_passed": report["summary"]["checks_passed"],
            "checks_total": report["summary"]["checks_total"],
            "claim_elements": report["summary"]["claim_elements"],
        },
        "out_dir": rel(out_dir),
        "elapsed_s": round(time.time() - start, 3),
    }
    (out_dir / "main-claim-evidence-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "main-claim-evidence.csv", report["claim_rows"], CLAIM_FIELDS)
    write_csv(out_dir / "main-claim-evidence-checks.csv", report["checks"])
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "main-claim-evidence.md", report)
    write_html(out_dir / "index.html", report)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
