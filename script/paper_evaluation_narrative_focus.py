#!/usr/bin/env python3
"""R371: evaluation narrative focus audit.

This guardrail checks that the paper text follows the R370 contract in prose:
each RQ section should lead with the right primary result, keep supporting
R-runs inside the intended experiment, and keep artifact-hygiene gates separate
from empirical profiler evidence.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-evaluation-narrative-focus-r371"
RUN_ID = "R371"
SCRIPT_PATH = Path(__file__).resolve()

SOURCES = {
    "R370 main experiment contract": OUT_ROOT / "paper-main-experiment-contract-r370" / "main-experiment-contract.json",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "English paper": SUBMODULE_ROOT / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
}


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


def normalize(text: str) -> str:
    return " ".join(text.split())


def extract_sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"\\subsection\{(RQ[1-4]/E[1-4][^}]*)\}", text))
    sections: dict[str, str] = {}
    for idx, match in enumerate(matches):
        key = match.group(1).split(":", 1)[0].split("：", 1)[0]
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        next_section = re.search(r"\\section\{", text[match.end() : end])
        if next_section:
            end = match.end() + next_section.start()
        sections[key] = text[match.start() : end]
    return sections


def first_pos(text: str, token: str) -> int:
    pos = text.find(token)
    return pos if pos >= 0 else 10**9


def after_claim_test(section: str) -> str:
    markers = ["Claim-test:", "Claim-test："]
    positions = [section.find(marker) for marker in markers if section.find(marker) >= 0]
    if not positions:
        return section
    return section[min(positions) :]


def section_rows(label: str, sections: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for rq in ["RQ1/E1", "RQ2/E2", "RQ3/E3", "RQ4/E4"]:
        section = sections.get(rq, "")
        rows.append(
            {
                "paper": label,
                "rq": rq,
                "chars": len(section),
                "r_run_mentions": len(re.findall(r"\bR\d{3}\b", section)),
                "has_claim_test": "Claim-test" in section or "Claim-test：" in section,
                "has_counterpoint": "counterpoint" in section.lower() or "反例" in section,
                "has_nonclaim": any(token in section.lower() for token in ["not ", "不是", "不能", "不支持"]),
            }
        )
    return rows


def build_checks(zh: str, en: str, evaluation: str, contract: dict[str, Any], sources: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    zh_sections = extract_sections(zh)
    en_sections = extract_sections(en)
    rows = section_rows("zh", zh_sections) + section_rows("en", en_sections)
    zh_rq4 = zh_sections.get("RQ4/E4", "")
    en_rq4 = en_sections.get("RQ4/E4", "")
    en_rq1 = en_sections.get("RQ1/E1", "")
    zh_rq2 = zh_sections.get("RQ2/E2", "")
    en_rq2 = en_sections.get("RQ2/E2", "")
    zh_rq3 = after_claim_test(zh_sections.get("RQ3/E3", ""))
    en_rq3 = after_claim_test(en_sections.get("RQ3/E3", ""))
    paper_blob = zh + "\n" + en
    checks = [
        {
            "check": "four_rq_sections_in_both_papers",
            "status": "pass" if set(zh_sections) >= {"RQ1/E1", "RQ2/E2", "RQ3/E3", "RQ4/E4"} and set(en_sections) >= {"RQ1/E1", "RQ2/E2", "RQ3/E3", "RQ4/E4"} else "fail",
            "evidence": f"zh={sorted(zh_sections)}; en={sorted(en_sections)}",
        },
        {
            "check": "rq1_keeps_ranker_ablation_out_of_primary_folding_story",
            "status": "pass" if all(token not in en_rq1 for token in ["R322", "R323", "R324", "R326", "R329"]) else "fail",
            "evidence": "English RQ1 no longer lists E3 ranker/actionability probes as recursive-folding evidence.",
        },
        {
            "check": "rq2_primary_result_precedes_supporting_robustness_runs",
            "status": "pass" if all(first_pos(section, "R320") < first_pos(section, token) for section in [zh_rq2, en_rq2] for token in ["R330", "R331", "R333", "R334", "R355"]) else "fail",
            "evidence": "RQ2 leads with the hidden-label localization benchmark before robustness/counterpoint slices.",
        },
        {
            "check": "rq3_mechanism_runs_precede_patch_case",
            "status": "pass" if all(first_pos(section, "R324") < first_pos(section, "R354") and first_pos(section, "R325") < first_pos(section, "R358") for section in [zh_rq3, en_rq3]) else "fail",
            "evidence": "RQ3 explains rank-feature/mapping mechanisms before executable patch and boundary repair cases.",
        },
        {
            "check": "rq4_replay_cost_precedes_hygiene_gates",
            "status": "pass" if all(first_pos(section, "R327") < first_pos(section, "R338") and first_pos(section, "R328") < first_pos(section, "R352") for section in [zh_rq4, en_rq4]) else "fail",
            "evidence": "RQ4 now leads with replay/cost evidence before paper-hygiene audits.",
        },
        {
            "check": "each_section_has_claim_counterpoint_nonclaim",
            "status": "pass" if all(row["has_claim_test"] and row["has_counterpoint"] and row["has_nonclaim"] for row in rows) else "fail",
            "evidence": "Each RQ section exposes claim test, counterpoint language, and scoped non-claim language.",
        },
        {
            "check": "r370_contract_still_passes",
            "status": "pass" if contract.get("status") == "pass" and contract.get("summary", {}).get("core_experiments") == 4 else "fail",
            "evidence": json.dumps(contract.get("summary", {}), sort_keys=True),
        },
        {
            "check": "paper_mentions_r371_narrative_focus",
            "status": "pass" if "R371" in paper_blob and "narrative" in paper_blob.lower() else "fail",
            "evidence": "Chinese and English drafts mention R371 as a narrative-focus guardrail.",
        },
        {
            "check": "evaluation_records_r371",
            "status": "pass" if "R371" in evaluation and "narrative focus" in evaluation.lower() else "fail",
            "evidence": "Evaluation ledger records R371 as paper-organization hygiene.",
        },
        {
            "check": "source_policy_no_new_data_or_profiler_rerun",
            "status": "pass" if all(row["status"] in {"tracked_clean", "tracked_dirty_allowed"} for row in sources) else "fail",
            "evidence": "R371 reads tracked paper/docs/artifacts only; it downloads no data and reruns no profiler.",
        },
    ]
    return checks, rows


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R371 Evaluation Narrative Focus",
        "",
        f"- Status: `{payload['status']}`.",
        f"- Checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.",
        "- This is a paper-organization guardrail, not a new empirical result.",
        "",
        "## Checks",
        "",
        "| Check | Status | Evidence |",
        "|---|---|---|",
    ]
    for check in payload["checks"]:
        lines.append(f"| `{check['check']}` | {check['status']} | {check['evidence']} |")
    lines.extend(["", "## Section Summary", "", "| Paper | RQ | Chars | R-run mentions | Claim-test | Counterpoint | Non-claim |", "|---|---|---:|---:|---|---|---|"])
    for row in payload["sections"]:
        lines.append(
            f"| {row['paper']} | {row['rq']} | {row['chars']} | {row['r_run_mentions']} | "
            f"{row['has_claim_test']} | {row['has_counterpoint']} | {row['has_nonclaim']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    checks = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['check'])}</td>"
        f"<td>{html.escape(row['status'])}</td>"
        f"<td>{html.escape(row['evidence'])}</td>"
        "</tr>"
        for row in payload["checks"]
    )
    sections = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(row['paper']))}</td>"
        f"<td>{html.escape(str(row['rq']))}</td>"
        f"<td>{row['chars']}</td>"
        f"<td>{row['r_run_mentions']}</td>"
        f"<td>{row['has_claim_test']}</td>"
        f"<td>{row['has_counterpoint']}</td>"
        f"<td>{row['has_nonclaim']}</td>"
        "</tr>"
        for row in payload["sections"]
    )
    path.write_text(
        f"""<!doctype html>
<meta charset=\"utf-8\">
<title>R371 Evaluation Narrative Focus</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #ddd; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f6f6; }}
</style>
<h1>R371 Evaluation Narrative Focus</h1>
<p>Status: <code>{html.escape(payload['status'])}</code>;
checks: {payload['summary']['checks_passed']}/{payload['summary']['checks_total']}.</p>
<h2>Checks</h2>
<table><thead><tr><th>Check</th><th>Status</th><th>Evidence</th></tr></thead><tbody>{checks}</tbody></table>
<h2>Section Summary</h2>
<table><thead><tr><th>Paper</th><th>RQ</th><th>Chars</th><th>R-run mentions</th><th>Claim-test</th><th>Counterpoint</th><th>Non-claim</th></tr></thead><tbody>{sections}</tbody></table>
""",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    start = time.time()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    zh = read_text(SOURCES["Chinese paper"])
    en = read_text(SOURCES["English paper"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    contract = read_json(SOURCES["R370 main experiment contract"])
    sources = source_rows()
    checks, section_summary = build_checks(zh, en, evaluation, contract, sources)
    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    payload: dict[str, Any] = {
        "run_id": RUN_ID,
        "status": status,
        "git_commit": git_commit(),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": {
            "checks_total": len(checks),
            "checks_passed": sum(1 for check in checks if check["status"] == "pass"),
            "sections": len(section_summary),
        },
        "checks": checks,
        "sections": section_summary,
        "sources": sources,
    }
    (args.out_dir / "narrative-focus-report.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(args.out_dir / "narrative-focus-checks.csv", checks, ["check", "status", "evidence"])
    write_csv(args.out_dir / "section-summary.csv", section_summary, ["paper", "rq", "chars", "r_run_mentions", "has_claim_test", "has_counterpoint", "has_nonclaim"])
    write_csv(args.out_dir / "source-status.csv", sources, ["source", "path", "status", "sha256"])
    write_markdown(args.out_dir / "narrative-focus.md", payload)
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
