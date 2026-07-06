#!/usr/bin/env python3
"""R367: audit the paper entry claim path for the RQ1/E1--RQ4/E4 structure.

This is a paper-integration gate, not a new empirical result. It checks that
the abstract, introduction/problem statement, and main result table present the
paper as three substantial empirical profiling experiments plus one
systems/reproducibility experiment, while R-numbered runs remain provenance.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
SUBMODULE_ROOT = ROOT / "docs" / "agentpprof-paper"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-entry-claim-path-r367"
RUN_ID = "R367"
SCRIPT_PATH = Path(__file__).resolve()

SOURCE_PATHS = {
    "generator script": SCRIPT_PATH,
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "English paper": SUBMODULE_ROOT / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "implementation doc": ROOT / "docs" / "implementation.md",
    "R360 core result tables": OUT_ROOT / "paper-core-result-tables-r360" / "core-result-tables.json",
    "R361 core claim evidence": OUT_ROOT / "paper-core-claim-evidence-r361" / "core-claim-evidence.json",
    "R364 core experiment sufficiency": OUT_ROOT
    / "paper-core-experiment-sufficiency-r364"
    / "core-experiment-sufficiency.json",
    "R366 field derivation mechanism": OUT_ROOT
    / "operation-field-derivation-mechanism-r366"
    / "field-derivation-mechanism-report.json",
}

ENTRY_SECTIONS = ["abstract", "intro_or_problem", "main_result_framing"]
CORE_EXPERIMENTS = ["E1", "E2", "E3", "E4"]
MUST_NOT_CLAIM = [
    "human productivity",
    "human utility",
    "automatic boundary discovery",
    "automatic intent boundary",
    "metric dominance",
    "complete trace-ecosystem compatibility",
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
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return result.stdout.strip()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def contains_all(text: str, tokens: list[str]) -> bool:
    lower = normalize(text)
    return all(token.lower() in lower for token in tokens)


def contains_any(text: str, tokens: list[str]) -> bool:
    lower = normalize(text)
    return any(token.lower() in lower for token in tokens)


def extract_between(text: str, start: str, end: str) -> str:
    start_idx = text.find(start)
    if start_idx < 0:
        return ""
    start_idx += len(start)
    end_idx = text.find(end, start_idx)
    return text[start_idx:] if end_idx < 0 else text[start_idx:end_idx]


def first_result_subsection_marker(text: str, language: str) -> str:
    if language == "en":
        for marker in [r"\subsection{RQ1/E1:", r"\subsection{E1:"]:
            if marker in text:
                return marker
        return r"\subsection{E1:"
    for marker in [r"\subsection{RQ1/E1：", r"\subsection{E1："]:
        if marker in text:
            return marker
    return r"\subsection{E1："


def extract_abstract(text: str) -> str:
    match = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", text, re.DOTALL)
    return match.group(1) if match else ""


def extract_language_sections(text: str, language: str) -> dict[str, str]:
    if language == "en":
        return {
            "abstract": extract_abstract(text),
            "intro_or_problem": extract_between(text, r"\section{Introduction}", r"\section{Design}"),
            "main_result_framing": extract_between(
                text,
                r"Table~\ref{tab:core-results} gives the paper-facing evaluation structure.",
                first_result_subsection_marker(text, "en"),
            ),
        }
    return {
        "abstract": extract_abstract(text),
        "intro_or_problem": extract_between(text, r"\section{问题}", r"\section{设计}"),
        "main_result_framing": extract_between(text, r"\section{结果}", first_result_subsection_marker(text, "zh")),
    }


def add_check(checks: list[dict[str, str]], name: str, condition: bool, evidence: str) -> None:
    checks.append({"check": name, "status": "pass" if condition else "fail", "evidence": evidence})


def source_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source, path in SOURCE_PATHS.items():
        rows.append({"source": source, "path": rel(path), "status": git_status(path), "sha256": sha256(path)})
    return rows


def token_matrix(zh_sections: dict[str, str], en_sections: dict[str, str]) -> list[dict[str, str]]:
    requirements = {
        "abstract": [
            "operation",
            "operation-stack",
            "three empirical",
            "systems/reproducibility",
            "E1",
            "E2",
            "E3",
            "E4",
            "RQ1",
            "RQ2",
            "RQ3",
            "RQ4",
            "not",
        ],
        "intro_or_problem": [
            "operation",
            "operation stack",
            "field",
            "recursive",
            "three empirical",
            "systems/reproducibility",
            "R-runs",
            "RQ1/E1",
        ],
        "main_result_framing": [
            "RQ1/E1",
            "RQ2/E2",
            "RQ3/E3",
            "RQ4/E4",
            "E1",
            "E2",
            "E3",
            "E4",
            "RQ / core experiment",
            "R374",
            "role map",
            "provenance",
        ],
    }
    zh_overrides = {
        "abstract": ["operation", "operation-stack", "三个经验性", "系统/复现", "RQ1", "RQ2", "RQ3", "RQ4", "不声称"],
        "intro_or_problem": ["operation", "operation fields", "递归折叠", "stack", "两个系统挑战"],
        "main_result_framing": ["RQ1/E1", "RQ2/E2", "RQ3/E3", "RQ4/E4", "RQ / core experiment", "R374", "role map", "provenance"],
    }
    rows: list[dict[str, str]] = []
    for language, sections, reqs in [
        ("zh", zh_sections, zh_overrides),
        ("en", en_sections, requirements),
    ]:
        for section in ENTRY_SECTIONS:
            text = sections.get(section, "")
            required = reqs[section]
            missing = [token for token in required if token.lower() not in normalize(text)]
            rows.append(
                {
                    "language": language,
                    "section": section,
                    "status": "pass" if not missing else "fail",
                    "missing_tokens": ";".join(missing),
                    "required_tokens": ";".join(required),
                }
            )
    return rows


def build_checks(
    zh: str,
    en: str,
    evaluation: str,
    implementation: str,
    r360: dict[str, Any],
    r361: dict[str, Any],
    r364: dict[str, Any],
    r366: dict[str, Any],
    matrix: list[dict[str, str]],
) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    combined = "\n".join([zh, en, evaluation, implementation])
    combined_norm = normalize(combined)

    add_check(
        checks,
        "entry_sections_share_e1_e4_structure",
        all(row["status"] == "pass" for row in matrix),
        f"{sum(row['status'] == 'pass' for row in matrix)}/{len(matrix)} entry token rows pass.",
    )
    add_check(
        checks,
        "paper_uses_three_plus_one_not_scattered_experiments",
        contains_any(combined, ["three empirical profiling questions plus one systems/reproducibility question"])
        and "三个经验性 profiling 问题加一个系统/复现问题" in combined
        and "零散 probe" in combined
        and "chronological run list" in combined_norm,
        "Chinese and English entry text present RQ1/E1-RQ4/E4 as three empirical profiling questions plus one systems/reproducibility question, not a chronological run list.",
    )
    add_check(
        checks,
        "only_two_profiler_abstractions_in_entry_path",
        contains_all(combined, ["operation", "operation stack"])
        and "第三种 profiler 对象" in combined
        and "third profiler object" in combined
        and all(obj in combined_norm for obj in ["prompt", "session", "tool", "process", "syscall"])
        and contains_any(combined, ["operation fields", "operation forms", "operation shapes"]),
        "Prompt/session/tool/process/syscall are presented as operation forms or fields under operation and operation stack.",
    )
    add_check(
        checks,
        "r_runs_are_provenance_not_paper_structure",
        "R 编号只作为 provenance" in combined
        and contains_any(combined, ["R-runs are provenance", "R-numbered runs are provenance"])
        and "E5" not in combined
        and "fifth core experiment" in combined,
        "R-numbered artifacts remain provenance and no E5 paper-facing experiment is introduced.",
    )
    add_check(
        checks,
        "e2_hidden_label_localization_numbers_visible",
        all(token in combined for token in ["34,539", "3,699", "144", "0.0937", "1.0", "5/6", "285.0", "157.5"]),
        "Entry path keeps the E2 hidden-label scale and flat/fixed-session tradeoff numbers visible.",
    )
    add_check(
        checks,
        "e3_actionability_and_boundary_scope_visible",
        all(token in combined for token in ["5/6", "0.2583", "0.2402", "74", "108"])
        and all(token in combined_norm for token in ["profile-spec", "actionability", "counterpoint"])
        and contains_any(combined, ["not automatic boundary discovery", "automatic intent boundary discovery"]),
        "Entry path keeps profile-spec actionability, boundary-field improvement, and boundary counterpoints visible.",
    )
    add_check(
        checks,
        "e4_replayability_not_accuracy_claim_visible",
        all(token in combined for token in ["76/76", "1.601s", "2.767s"])
        and contains_any(combined, ["not a hidden-label accuracy result", "不作为 profiler 的 empirical accuracy evidence"])
        and contains_any(combined, ["not live eBPF overhead", "live capture overhead result"]),
        "Entry path presents E4 as reproducibility/cost evidence rather than another accuracy or live-overhead result.",
    )
    add_check(
        checks,
        "generated_ledgers_match_entry_numbers",
        r360["status"] == "pass"
        and r360["summary"]["core_experiments"] == 4
        and r360["summary"]["metrics"] == 20
        and r361["status"] == "pass"
        and r361["summary"]["core_experiments"] == 4
        and r364["status"] == "pass"
        and r364["summary"]["core_experiments"] == 4
        and r366["status"] == "pass"
        and r366["summary"]["mechanism_rows"] == 6
        and r366["summary"]["boundary_family_rows"] == 5,
        "R360/R361/R364/R366 ledgers pass and preserve four core experiments plus internal R366 mechanism evidence.",
    )
    add_check(
        checks,
        "must_not_claim_boundaries_visible",
        all(contains_any(combined, [token, token.replace("-", " "), token.replace("complete ", "full ")]) for token in MUST_NOT_CLAIM),
        "Entry path excludes human utility/productivity, automatic boundary discovery, metric dominance, and complete ecosystem compatibility claims.",
    )
    add_check(
        checks,
        "visualization_not_flamegraph_only",
        "flamegraph" in combined_norm
        and contains_any(combined, ["five paper views", "baseline-tradeoff", "metric-heatmap", "diagnostic-lenses"])
        and contains_any(combined, ["not a fifth experiment", "不是第五个实验"]),
        "Presentation is framed as a small portfolio of analysis views, not a flamegraph-only result or extra experiment.",
    )
    add_check(
        checks,
        "input_policy_no_new_data_or_profiler_rerun",
        r360["input_policy"]["dataset_sync"] == "none"
        and r360["input_policy"]["profiler_rerun"] is False
        and r361["input_policy"]["dataset_sync"] == "none"
        and r361["input_policy"]["profiler_rerun"] is False
        and r364["input_policy"]["no_dataset_sync"] is True
        and r366["input_policy"]["no_dataset_sync"] is True
        and r366["input_policy"]["no_profiler_rerun"] is True,
        "The R367 sources are tracked ledgers/docs only: no dataset sync, no relabeling, and no profiler rerun.",
    )
    return checks


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R367 Paper Entry Claim Path Audit",
        "",
        f"- Status: `{payload['status']}`.",
        f"- Checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.",
        "- This is a paper-integration gate, not a new empirical result.",
        "- It keeps the paper organized as RQ1/E1--RQ4/E4 rather than a scattered R-run list.",
        "",
        "## Entry Token Matrix",
        "",
        "| Language | Section | Status | Missing tokens |",
        "|---|---|---|---|",
    ]
    for row in payload["entry_rows"]:
        lines.append(f"| {row['language']} | {row['section']} | {row['status']} | {row['missing_tokens']} |")
    lines.extend(["", "## Checks", "", "| Check | Status | Evidence |", "|---|---|---|"])
    for check in payload["checks"]:
        lines.append(f"| `{check['check']}` | {check['status']} | {check['evidence']} |")
    lines.extend(
        [
            "",
            "## Non-Claims",
            "",
            "- Not a new dataset, relabeling step, profiler rerun, or human/agent analyst task.",
            "- Not a fifth paper-facing experiment.",
            "- Not evidence for human productivity, automatic boundary discovery, metric dominance, live overhead, or complete trace-ecosystem compatibility.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    matrix_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['language'])}</td>"
        f"<td>{html.escape(row['section'])}</td>"
        f"<td>{html.escape(row['status'])}</td>"
        f"<td>{html.escape(row['missing_tokens'])}</td>"
        "</tr>"
        for row in payload["entry_rows"]
    )
    check_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['check'])}</td>"
        f"<td>{html.escape(row['status'])}</td>"
        f"<td>{html.escape(row['evidence'])}</td>"
        "</tr>"
        for row in payload["checks"]
    )
    page = f"""<!doctype html>
<html>
<head>
<meta charset=\"utf-8\">
<title>R367 Paper Entry Claim Path Audit</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ddd; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f5f5f5; text-align: left; }}
code {{ background: #f3f3f3; padding: 0.1rem 0.2rem; }}
</style>
</head>
<body>
<h1>R367 Paper Entry Claim Path Audit</h1>
<p>Status: <code>{html.escape(payload['status'])}</code>;
checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.</p>
<h2>Entry Token Matrix</h2>
<table>
<tr><th>Language</th><th>Section</th><th>Status</th><th>Missing tokens</th></tr>
{matrix_rows}
</table>
<h2>Checks</h2>
<table>
<tr><th>Check</th><th>Status</th><th>Evidence</th></tr>
{check_rows}
</table>
</body>
</html>
"""
    path.write_text(page, encoding="utf-8")


def main() -> int:
    args = parse_args()
    out_dir = args.out_dir
    start = time.time()
    out_dir.mkdir(parents=True, exist_ok=True)

    zh = read_text(SOURCE_PATHS["Chinese paper"])
    en = read_text(SOURCE_PATHS["English paper"])
    evaluation = read_text(SOURCE_PATHS["evaluation ledger"])
    implementation = read_text(SOURCE_PATHS["implementation doc"])
    r360 = read_json(SOURCE_PATHS["R360 core result tables"])
    r361 = read_json(SOURCE_PATHS["R361 core claim evidence"])
    r364 = read_json(SOURCE_PATHS["R364 core experiment sufficiency"])
    r366 = read_json(SOURCE_PATHS["R366 field derivation mechanism"])

    zh_sections = extract_language_sections(zh, "zh")
    en_sections = extract_language_sections(en, "en")
    entry_rows = token_matrix(zh_sections, en_sections)
    checks = build_checks(zh, en, evaluation, implementation, r360, r361, r364, r366, entry_rows)
    checks_passed = sum(1 for check in checks if check["status"] == "pass")
    status = "pass" if checks_passed == len(checks) else "fail"
    payload = {
        "run_id": RUN_ID,
        "schema": "agentsight.paper-entry-claim-path.v1",
        "status": status,
        "commit": git_commit(),
        "elapsed_s": round(time.time() - start, 3),
        "claim": (
            "The paper entry path is organized as three empirical profiling "
            "experiments plus one systems/reproducibility experiment, with "
            "operation and operation stack as the only profiler abstractions."
        ),
        "input_policy": {
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "dataset_sync": "none",
            "hidden_label_use": "only through already-scored upstream artifacts",
            "network_access_required": False,
            "profiler_rerun": False,
        },
        "not_new_empirical_result": True,
        "not_a_human_study_result": True,
        "not_an_agent_analyst_task_result": True,
        "profiler_abstractions": ["operation", "operation stack"],
        "summary": {
            "checks_passed": checks_passed,
            "checks_total": len(checks),
            "entry_rows": len(entry_rows),
            "core_experiments": CORE_EXPERIMENTS,
            "status": status,
        },
        "entry_rows": entry_rows,
        "checks": checks,
        "source_status": source_rows(),
        "non_claims": [
            "not a new empirical result",
            "not a human or agent analyst study",
            "not a fifth paper-facing experiment",
            "not automatic boundary discovery",
            "not metric dominance",
            "not live eBPF overhead",
            "not complete trace-ecosystem compatibility",
        ],
    }

    write_csv(out_dir / "entry-token-matrix.csv", entry_rows, ["language", "section", "status", "missing_tokens", "required_tokens"])
    write_csv(out_dir / "entry-claim-checks.csv", checks, ["check", "status", "evidence"])
    write_csv(out_dir / "source-status.csv", payload["source_status"], ["source", "path", "status", "sha256"])
    (out_dir / "entry-claim-path-report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(out_dir / "entry-claim-path.md", payload)
    write_html(out_dir / "index.html", payload)
    run_result = {
        "run_id": RUN_ID,
        "status": status,
        "checks_passed": checks_passed,
        "checks_total": len(checks),
        "entry_rows": len(entry_rows),
        "report": rel(out_dir / "entry-claim-path-report.json"),
        "network_access_required": False,
        "not_new_empirical_result": True,
        "not_a_human_study_result": True,
        "not_an_agent_analyst_task_result": True,
    }
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
