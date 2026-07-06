#!/usr/bin/env python3
"""R370: main-experiment contract audit.

This is a paper-organization guardrail, not a new empirical result. It fixes the
evaluation story around four reviewer-facing experiments and records how smaller
R-numbered artifacts are allowed to appear: primary evidence, ablations,
counterpoints, provenance, or hygiene gates inside one of the four experiments.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-main-experiment-contract-r370"
RUN_ID = "R370"
SCRIPT_PATH = Path(__file__).resolve()

SOURCES = {
    "R360 core result tables": OUT_ROOT / "paper-core-result-tables-r360" / "core-result-tables.json",
    "R361 core claim evidence": OUT_ROOT / "paper-core-claim-evidence-r361" / "core-claim-evidence.json",
    "R363 visualization portfolio": OUT_ROOT / "paper-visualization-portfolio-r363" / "visualization-portfolio.json",
    "R364 core sufficiency": OUT_ROOT / "paper-core-experiment-sufficiency-r364" / "core-experiment-sufficiency.json",
    "R365 headline case studies": OUT_ROOT / "paper-headline-case-studies-r365" / "headline-case-studies.json",
    "R368 trace-tree baseline": OUT_ROOT / "paper-trace-tree-baseline-r368" / "trace-tree-baseline-report.json",
    "R369 reviewer evidence path": OUT_ROOT / "paper-reviewer-evidence-path-r369" / "evidence-path.json",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "English paper": SUBMODULE_ROOT / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
}

ROW_FIELDS = [
    "experiment",
    "primary_test",
    "workload_or_oracle",
    "baselines_and_metrics",
    "primary_evidence",
    "supporting_roles",
    "failure_interpretation",
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
            "sha256": sha256(path) if path.exists() else "",
        }
        for name, path in {"generator script": SCRIPT_PATH, **SOURCES}.items()
    ]


def build_contract_rows() -> list[dict[str, str]]:
    return [
        {
            "experiment": "RQ1/E1: Abstraction generality and recursive folding",
            "primary_test": "Can one operation layer be folded into task, phase, action, boundary, and fixed-session-shaped stacks without prompt/session-bound profiler objects?",
            "workload_or_oracle": "15 public labeled trace families / 47,590 operations; OSWorld-Human grouped boundaries and AgentNet step-quality labels are the strongest oracles.",
            "baselines_and_metrics": "Dataset-native, no-map, fixed-session, profile-spec replay, and trace round-trip baselines; coverage, stack counts, compression, boundary F1/V-measure, and equality.",
            "primary_evidence": "R286 stack-depth sweep; R290/R291 boundary and quality labels; R293/R321/R342 profile-spec replay and predicates; R353 trace exchange; R366 field-derivation consolidation.",
            "supporting_roles": "R279-R292 are coverage inputs; R281/R282/R285/R297/R299 are mapping and boundary probes; R294/R303/R306/R353 are exchange/provenance checks.",
            "failure_interpretation": "If a dataset requires a new profiler object or a fixed prompt/session hierarchy to obtain useful groups, narrow C1/C2 to the covered trace families.",
            "non_claim": "No complete trace-ecosystem compatibility and no automatic recovery of all latent intent boundaries.",
        },
        {
            "experiment": "RQ2/E2: Hidden-label localization and baseline tradeoff",
            "primary_test": "Do hot groups and top-ranked stacks correspond to hidden positives while requiring less inspection work than flat summaries and less fragmentation than fixed-session drilldown?",
            "workload_or_oracle": "Six oracle-backed tasks over AgentRewardBench, SATraj-OS, AgentNet, and OSWorld-Human; 34,539 operations and 3,699 positives.",
            "baselines_and_metrics": "Flat, fixed-session, dataset-native, raw-action, operation-stack, label-drilldown, and oracle upper bound; AP/AUPRC-style score, precision/recall/F1@k, nDCG, recall@work, work-to-first-positive, group count, fragmentation, and oracle-depth recall.",
            "primary_evidence": "R320 is the main benchmark; R333/R334/R337/R339/R344/R355 are budget, fragmentation, target, sequence, metric-surface, and oracle-depth slices; R368 scopes the trace-tree-shaped baseline.",
            "supporting_roles": "R300-R305 and R346/R347 are setup/case-packet evidence; R330/R331 are uncertainty and negative-control checks; R363/R365 are paper-facing views and case tables.",
            "failure_interpretation": "If flat or fixed-session dominates the Pareto surface, narrow C4 to the tasks/metrics where operation stacks remain selective and reduce fragmentation.",
            "non_claim": "No metric dominance, no human-productivity result, and no superiority claim over real imported OTel/Phoenix/LangSmith/Langfuse/Perfetto traces.",
        },
        {
            "experiment": "RQ3/E3: Mechanism isolation and profile-configuration actionability",
            "primary_test": "Which stack fields, mappings, rankers, lenses, and profile-spec patches explain localization gains or failures?",
            "workload_or_oracle": "The same six labeled tasks plus held-out OSWorld-Human boundary-backend operations from R297.",
            "baselines_and_metrics": "No-map, width, query-agnostic, rank-feature ablations, transfer policies, profile-spec before/after patches, boundary-derived fields, and fixed-session/raw-action counterpoints; AP, lift, work-to-first-positive, groups, feature criticality, action class, and transfer tolerance.",
            "primary_evidence": "R324/R325/R326 rank-feature and ablation results; R335/R340/R341/R345-R350 actionability and transfer evidence; R354 executable patches; R358 boundary-derived repair; R366 field-derivation mechanism audit.",
            "supporting_roles": "R345/R363 are diagnostic visualization portfolios; R346/R350 are bounded evidence packets; R349 is the action-transfer counterpoint.",
            "failure_interpretation": "If the same default view wins everywhere, remove the configurable-actionability claim; if transfer fails, keep actionability as post-hoc configuration guidance.",
            "non_claim": "No automatic patch selector, no label-free universal selector, and no automatic boundary detector.",
        },
        {
            "experiment": "RQ4/E4: Replayability, offline cost, and paper hygiene",
            "primary_test": "Can reviewers replay the offline profile-spec path and audit claim scope without syncing datasets or running a human/agent analyst study?",
            "workload_or_oracle": "76 tracked profile specs over tracked operation JSONL inputs, repeated under deterministic output mode; source-status and paper-text hashes.",
            "baselines_and_metrics": "Semantic versus raw-byte determinism, sample/stack equality, runtime, output size, source provenance, number alignment, two-abstraction checks, and must-not-claim checks.",
            "primary_evidence": "R327/R328 deterministic replay and local cost; R338/R352/R356/R357 claim/rubric/reviewer gates; R359-R370 paper-structure gates.",
            "supporting_roles": "R319/R343 are implementation and portability checks; R315/R316 remain optional future human-utility protocol artifacts.",
            "failure_interpretation": "If replay is not deterministic or paper claims outpace evidence, block artifact-readiness and narrow the abstract until the gate passes.",
            "non_claim": "No live eBPF overhead result, no hidden-label accuracy result, and no human or agent analyst utility result.",
        },
    ]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def build_checks(rows: list[dict[str, str]], sources: list[dict[str, str]], zh: str, en: str, evaluation: str) -> list[dict[str, str]]:
    row_blob = json.dumps(rows, sort_keys=True)
    paper_blob = zh + "\n" + en
    lower_paper = paper_blob.lower()
    lower_eval = " ".join(evaluation.lower().split())
    normalized_paper = " ".join(lower_paper.split())
    required_row_fields = ["primary_test", "workload_or_oracle", "baselines_and_metrics", "primary_evidence", "supporting_roles", "failure_interpretation", "non_claim"]
    guardrail_groups = [
        ["does not claim human-productivity", "not human utility", "不是 human utility", "不能推出开发者准确率"],
        ["automatic discovery of all intent boundaries", "not automatic boundary", "not automatic intent", "不声称自动发现", "不能声称所有 intent boundary"],
        ["metric dominance", "not metric dominance", "不是 metric dominance"],
        ["complete compatibility", "not complete ecosystem", "完整兼容", "完整 trace-ecosystem"],
    ]
    checks = [
        {
            "check": "exactly_four_core_experiments",
            "status": "pass" if [row["experiment"][:6] for row in rows] == ["RQ1/E1", "RQ2/E2", "RQ3/E3", "RQ4/E4"] else "fail",
            "evidence": "The main paper has four reviewer-facing experiment contracts, not a chronological R-run list.",
        },
        {
            "check": "each_core_has_executable_contract_fields",
            "status": "pass" if all(all(row.get(field) for field in required_row_fields) for row in rows) else "fail",
            "evidence": "Each core experiment states the primary test, workload/oracle, baselines/metrics, evidence, support roles, failure interpretation, and non-claim.",
        },
        {
            "check": "no_fifth_core_experiment",
            "status": "pass" if "RQ5" not in row_blob and "E5" not in row_blob else "fail",
            "evidence": "R363/R365/R366/R369/R370 are presentation, mechanism, or guardrail artifacts inside E1-E4, not additional main experiments.",
        },
        {
            "check": "localization_block_has_required_metrics",
            "status": "pass"
            if all(token in row_blob for token in ["precision/recall/F1", "AP/AUPRC", "nDCG", "work-to-first-positive", "fragmentation"])
            else "fail",
            "evidence": "RQ2/E2 carries the profiling-paper localization metrics requested by the claim.",
        },
        {
            "check": "paper_states_core_experiment_contract",
            "status": "pass"
            if all(token in paper_blob for token in ["R370", "RQ1/E1", "RQ2/E2", "RQ3/E3", "RQ4/E4"])
            else "fail",
            "evidence": "Chinese and English drafts mention R370 and the four core experiments.",
        },
        {
            "check": "paper_downgrades_r_runs_to_support",
            "status": "pass"
            if ("R 编号只作为 provenance" in paper_blob and "R-numbered runs are provenance" in paper_blob)
            else "fail",
            "evidence": "Both drafts explicitly keep R-numbered runs out of the main evaluation structure.",
        },
        {
            "check": "evaluation_records_three_empirical_plus_one_systems",
            "status": "pass"
            if "three empirical profiling questions plus one systems/reproducibility" in lower_eval
            else "fail",
            "evidence": "The evaluation ledger records the 3+1 experiment organization.",
        },
        {
            "check": "must_not_claims_preserved",
            "status": "pass"
            if all(any(token in normalized_paper or token in paper_blob for token in group) for group in guardrail_groups)
            else "fail",
            "evidence": "The paper keeps the human-utility, automatic-boundary, metric-dominance, and ecosystem-compatibility guardrails visible.",
        },
        {
            "check": "source_policy_no_new_data_or_profiler_rerun",
            "status": "pass" if all(row["status"] in {"tracked_clean", "tracked_dirty_allowed"} for row in sources) else "fail",
            "evidence": "R370 reads tracked paper/docs/artifacts only; it downloads no data, relabels nothing, and reruns no profiler.",
        },
    ]
    return checks


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R370 Main-Experiment Contract",
        "",
        f"- Status: `{payload['status']}`.",
        f"- Checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.",
        "- This is a paper-organization guardrail, not a new empirical result.",
        "",
        "## Core Experiments",
        "",
        "| Experiment | Primary test | Workload/oracle | Baselines and metrics | Primary evidence | Supporting roles | Failure interpretation | Non-claim |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['experiment']} | {row['primary_test']} | {row['workload_or_oracle']} | "
            f"{row['baselines_and_metrics']} | {row['primary_evidence']} | {row['supporting_roles']} | "
            f"{row['failure_interpretation']} | {row['non_claim']} |"
        )
    lines.extend(["", "## Checks", "", "| Check | Status | Evidence |", "|---|---|---|"])
    for check in payload["checks"]:
        lines.append(f"| `{check['check']}` | {check['status']} | {check['evidence']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['experiment'])}</td>"
        f"<td>{html.escape(row['primary_test'])}</td>"
        f"<td>{html.escape(row['workload_or_oracle'])}</td>"
        f"<td>{html.escape(row['baselines_and_metrics'])}</td>"
        f"<td>{html.escape(row['primary_evidence'])}</td>"
        f"<td>{html.escape(row['supporting_roles'])}</td>"
        f"<td>{html.escape(row['failure_interpretation'])}</td>"
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
<title>R370 Main-Experiment Contract</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ddd; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f6f6; }}
</style>
<h1>R370 Main-Experiment Contract</h1>
<p>Status: <code>{html.escape(payload['status'])}</code>;
checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.</p>
<h2>Core Experiments</h2>
<table><thead><tr><th>Experiment</th><th>Primary test</th><th>Workload/oracle</th><th>Baselines and metrics</th><th>Primary evidence</th><th>Supporting roles</th><th>Failure interpretation</th><th>Non-claim</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Checks</h2>
<table><thead><tr><th>Check</th><th>Status</th><th>Evidence</th></tr></thead><tbody>{checks}</tbody></table>
""",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    start = time.time()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    upstream_status = {
        "r360": read_json(SOURCES["R360 core result tables"])["status"],
        "r361": read_json(SOURCES["R361 core claim evidence"])["status"],
        "r363": read_json(SOURCES["R363 visualization portfolio"])["status"],
        "r364": read_json(SOURCES["R364 core sufficiency"])["status"],
        "r365": read_json(SOURCES["R365 headline case studies"])["status"],
        "r368": read_json(SOURCES["R368 trace-tree baseline"])["status"],
        "r369": read_json(SOURCES["R369 reviewer evidence path"])["status"],
    }
    rows = build_contract_rows()
    sources = source_rows()
    zh = read_text(SOURCES["Chinese paper"])
    en = read_text(SOURCES["English paper"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    checks = build_checks(rows, sources, zh, en, evaluation)
    checks.append(
        {
            "check": "upstream_r360_r369_gates_pass",
            "status": "pass" if all(status == "pass" for status in upstream_status.values()) else "fail",
            "evidence": json.dumps(upstream_status, sort_keys=True),
        }
    )
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "status": status,
        "git_commit": git_commit(),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": {
            "core_experiments": len(rows),
            "checks_total": len(checks),
            "checks_passed": sum(1 for check in checks if check["status"] == "pass"),
        },
        "rows": rows,
        "checks": checks,
        "sources": sources,
        "upstream_status": upstream_status,
    }

    (args.out_dir / "main-experiment-contract.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(args.out_dir / "main-experiment-contract.csv", rows, ROW_FIELDS)
    write_csv(args.out_dir / "main-experiment-contract-checks.csv", checks, ["check", "status", "evidence"])
    write_csv(args.out_dir / "source-status.csv", sources, ["source", "path", "status", "sha256"])
    write_markdown(args.out_dir / "main-experiment-contract.md", payload)
    write_html(args.out_dir / "index.html", payload)

    run_result = {
        "run_id": RUN_ID,
        "status": status,
        "checks": payload["summary"],
        "out_dir": rel(args.out_dir),
        "elapsed_s": round(time.time() - start, 3),
    }
    (args.out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
