#!/usr/bin/env python3
"""R394: two-abstraction documentation consistency gate.

This is a paper/docs hygiene guardrail. It checks that maintained docs and paper
drafts describe tagging, mapping, LLM tags, clustering, predicates, and profile
specs as operation-field derivation and query configuration before operation
stack folding. It does not fetch datasets, relabel traces, rerun profiler
experiments, or execute a human/agent analyst task.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-two-abstraction-doc-r394"
RUN_ID = "R394"
SCRIPT_PATH = Path(__file__).resolve()
PAPER_SUBMODULE = ROOT / "docs" / "agentpprof-paper"
PAPER_SUBMODULE_PATH = "docs/agentpprof-paper"

SOURCES = {
    "rust cli": ROOT / "agentpprof" / "src" / "main.rs",
    "agentpprof readme": ROOT / "agentpprof" / "README.md",
    "English user guide": ROOT / "docs" / "agentpprof.md",
    "Chinese user guide": ROOT / "docs" / "agentpprof-zh.md",
    "idea story": ROOT / "docs" / "idea-story.md",
    "design": ROOT / "docs" / "design.md",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "English paper": PAPER_SUBMODULE / "main.tex",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
}

FORBIDDEN = [
    "意图" + "识别层",
    "折叠出结构" + "在前",
    "标签聚合" + "在后",
    "third profiler abstraction" + " for tagging",
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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_stdout(args: list[str], cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return result.stdout.strip()


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


def normalize(text: str) -> str:
    return " ".join(text.split())


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"check": name, "passed": bool(passed), "detail": detail})


def contains_all(text: str, needles: list[str]) -> bool:
    return all(needle in text for needle in needles)


def build_report() -> dict[str, Any]:
    texts = {name: read_text(path) for name, path in SOURCES.items()}
    normalized = {name: normalize(text) for name, text in texts.items()}
    joined = "\n".join(texts.values())
    source_status = source_rows()
    source_by_name = {row["source"]: row for row in source_status}
    checks: list[dict[str, Any]] = []

    add_check(
        checks,
        "core_docs_name_only_two_profiler_abstractions",
        contains_all(
            texts["Chinese user guide"],
            ["核心是两个抽象", "操作", "操作栈", "不是三个 profiler 抽象"],
        )
        and contains_all(
            texts["English user guide"],
            ["two abstractions", "operations", "operation stacks"],
        )
        and contains_all(
            texts["idea story"],
            ["two profiler abstractions", "`operation`", "`operation stack`"],
        )
        and contains_all(
            texts["design"],
            ["only two core abstractions", "`operation`", "`operation stack`"],
        ),
        "Chinese/English guides plus canonical docs name operation and operation stack as the only profiler abstractions.",
    )
    add_check(
        checks,
        "field_derivation_precedes_stack_folding",
        "字段派生在前，按 `--stack` 折叠与聚合在后" in texts["Chinese user guide"]
        and "Tags and mappings derive operation fields before folding" in texts["rust cli"]
        and "derive fields with mapping/tagging, choose a query subset, and fold" in normalized["English user guide"]
        and "derive operation fields before stack construction" in normalized["agentpprof readme"],
        "Docs and CLI help agree that tagging/mapping derive operation fields before operation-stack folding.",
    )
    add_check(
        checks,
        "tagging_mapping_not_third_abstraction",
        "tagger 和 mapping 后端只负责写入字段" in texts["Chinese user guide"]
        and "without adding another profiler abstraction" in texts["agentpprof readme"]
        and "they do not create a third profiler abstraction" in texts["idea story"]
        and "not a third profiler abstraction" in texts["English user guide"],
        "Tagging, mapping, and profile specs are described as field derivation/configuration, not profiler objects.",
    )
    add_check(
        checks,
        "llm_tags_are_field_derivation_assistance",
        "It is field-derivation assistance, not an automatic boundary detector"
        in normalized["English user guide"]
        and "它是字段派生辅助，不是自动边界 detector" in texts["Chinese user guide"]
        and "LLM tags are cached under the user cache directory" in texts["agentpprof readme"]
        and "derive operation fields before stack construction without adding another profiler abstraction"
        in normalized["agentpprof readme"],
        "LLM tags are documented as replayable/auxiliary operation-field derivation, not boundary detection or a new abstraction.",
    )
    add_check(
        checks,
        "clustering_is_exploratory_field_source",
        "Clustering is an exploratory way to propose operation-field candidates"
        in normalized["English user guide"]
        and "make them reproducible through rules, profile specs, or imported dataset labels"
        in normalized["English user guide"]
        and "聚类结果应当通过规则、profile spec 或数据集已有标签固化后再用于可复现实验"
        in texts["Chinese user guide"]
        and "topic clustering" in texts["English user guide"],
        "Clustering is documented as exploratory operation-field proposal material that must be made reproducible before paper use.",
    )
    add_check(
        checks,
        "trace_session_span_are_containers_or_fields",
        "Trace schema 是 `agentsight.agent-session.trace.v1`" in texts["Chinese user guide"]
        and "不是 profiler 的第三个抽象" in texts["Chinese user guide"]
        and "format for parsed sessions, not a profiler abstraction" in normalized["English user guide"]
        and "session, span, task, and trace identifiers are operation fields" in normalized["design"].lower()
        and "trace/span/session 明确当作 exchange container 或 baseline shape" in texts["Chinese paper"],
        "Trace/session/span wording keeps those objects as containers, fields, or baselines rather than profiler abstractions.",
    )
    add_check(
        checks,
        "automatic_boundary_and_detector_nonclaims_visible",
        "不自动声称发现了真实 intent boundary" in texts["Chinese user guide"]
        and "不是自动边界 detector" in texts["Chinese user guide"]
        and "Fully unsupervised intent-boundary discovery is not supported" in texts["idea story"]
        and "automatic discovery of all intent boundaries" in texts["English paper"]
        and "自动发现所有 intent boundary" in texts["Chinese paper"],
        "Docs and papers preserve automatic-boundary/detector non-claims.",
    )
    forbidden_hits = {phrase: joined.count(phrase) for phrase in FORBIDDEN if phrase in joined}
    add_check(
        checks,
        "no_stale_field_derivation_order_or_layer_terms",
        not forbidden_hits,
        f"Forbidden stale wording hits={forbidden_hits}",
    )
    add_check(
        checks,
        "paper_structure_remains_three_plus_one",
        "three core empirical profiling experiments" in texts["English paper"]
        and "artifact/reproducibility block" in texts["English paper"]
        and "三个核心经验性 profiling 实验" in texts["Chinese paper"]
        and "artifact/reproducibility block" in texts["Chinese paper"]
        and "three core empirical profiling experiments plus one artifact/reproducibility block" in texts["idea story"],
        "Paper and idea story retain three empirical profiling experiments plus one artifact/reproducibility block.",
    )
    add_check(
        checks,
        "r394_registered_in_evaluation_ledger",
        "R394" in texts["evaluation ledger"] and "two-abstraction documentation consistency" in texts["evaluation ledger"],
        "Evaluation ledger records this documentation consistency gate.",
    )
    add_check(
        checks,
        "english_submodule_clean",
        source_by_name["English paper"]["status"] == "tracked_clean"
        and paper_submodule_head() == paper_submodule_index_head(),
        "English paper submodule is clean and the parent gitlink matches it.",
    )
    add_check(
        checks,
        "source_status_tracked_or_dirty_allowed",
        all(
            row["status"] in {"tracked_clean", "tracked_dirty_allowed"}
            or (row["source"] == "generator script" and row["status"] == "untracked_or_missing")
            for row in source_status
        ),
        "All guard inputs are tracked or intentionally dirty while this guard is being generated.",
    )

    summary = {
        "checks_passed": sum(1 for check in checks if check["passed"]),
        "checks_total": len(checks),
        "data_sync": False,
        "profiler_rerun": False,
        "human_or_agent_analyst_task": False,
    }
    return {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "schema": "agentsight.paper_two_abstraction_doc_gate.v1",
        "network_access_required": False,
        "data_sync": False,
        "profiler_rerun": False,
        "human_or_agent_analyst_task": False,
        "checks": checks,
        "source_status": source_status,
        "summary": summary,
        "interpretation": (
            "Maintained docs and paper drafts keep operation and operation stack "
            "as the only profiler abstractions. Tagging, mapping, clustering, "
            "predicates, and profile specs are field derivation or query "
            "configuration before operation-stack folding."
        ),
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
        "# R394 Two-Abstraction Documentation Gate",
        "",
        f"Status: `{report['status']}`",
        f"Checks: {report['summary']['checks_passed']}/{report['summary']['checks_total']}",
        "",
        report["interpretation"],
        "",
        "## Checks",
        "",
        "| Check | Passed | Detail |",
        "|---|---:|---|",
    ]
    for check in report["checks"]:
        lines.append(f"| {check['check']} | {check['passed']} | {check['detail']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, report: dict[str, Any]) -> None:
    check_rows = "\n".join(
        f"<tr><td>{html.escape(check['check'])}</td><td>{check['passed']}</td><td>{html.escape(check['detail'])}</td></tr>"
        for check in report["checks"]
    )
    path.write_text(
        f"""<!doctype html>
<meta charset="utf-8">
<title>{RUN_ID} Two-Abstraction Documentation Gate</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
th {{ background: #f6f8fa; }}
.status {{ font-weight: 700; }}
</style>
<h1>{RUN_ID} Two-Abstraction Documentation Gate</h1>
<p class="status">Status: {html.escape(report['status'])}; checks {report['summary']['checks_passed']}/{report['summary']['checks_total']}.</p>
<p>{html.escape(report['interpretation'])}</p>
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
        },
        "out_dir": rel(out_dir),
        "elapsed_s": round(time.time() - start, 3),
    }
    (out_dir / "two-abstraction-doc-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "run-result.json").write_text(json.dumps(run_result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "two-abstraction-doc-checks.csv", report["checks"])
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    write_markdown(out_dir / "two-abstraction-doc.md", report)
    write_html(out_dir / "index.html", report)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
