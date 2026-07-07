#!/usr/bin/env python3
"""R405: read-only English-paper experiment gap audit.

This is a paper-integration guardrail, not a new empirical experiment. It reads
the English submodule draft only to identify which claims are already backed by
outer-repo artifacts and which statements must remain future work or non-claims.
It does not edit, restore, update, commit, or otherwise touch the submodule.
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
DEFAULT_OUT_DIR = OUT_ROOT / "paper-english-experiment-gap-audit-r405"
RUN_ID = "R405"
SCRIPT_PATH = Path(__file__).resolve()

SOURCES = {
    "English paper draft": SUBMODULE_ROOT / "main.tex",
    "Chinese paper draft": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "design notes": ROOT / "docs" / "design.md",
    "implementation notes": ROOT / "docs" / "implementation.md",
    "R320 hidden-label benchmark": OUT_ROOT / "operation-profile-accuracy-r320" / "profile-accuracy-report.json",
    "R344 metric consistency": OUT_ROOT / "operation-metric-consistency-r344" / "metric-consistency-report.json",
    "R355 oracle-depth adequacy": OUT_ROOT / "operation-oracle-depth-adequacy-r355" / "oracle-depth-adequacy-report.json",
    "R366 field derivation": OUT_ROOT / "operation-field-derivation-mechanism-r366" / "field-derivation-mechanism-report.json",
    "R368 trace-tree baseline": OUT_ROOT / "paper-trace-tree-baseline-r368" / "trace-tree-baseline-report.json",
    "R375 claim gate": OUT_ROOT / "paper-core-claim-gate-r375" / "core-claim-gate-report.json",
    "R400 field suitability": OUT_ROOT / "operation-field-suitability-r400" / "field-suitability-report.json",
}

OPERATION_JSONL_SOURCES = {
    "AgentNet operations": OUT_ROOT / "external-agent-trace-agentnet-r291" / "agentnet-operations.jsonl",
    "AgentRewardBench operations": OUT_ROOT / "external-agent-trace-agentreward-r288" / "agentreward-operations.jsonl",
    "OSWorld-Human operations": OUT_ROOT / "external-agent-trace-osworldhuman-r290" / "osworld-human-operations.jsonl",
    "SATraj-OS operations": OUT_ROOT / "external-agent-trace-satraj-r289" / "satraj-operations.jsonl",
    "ScaleCUA operations": OUT_ROOT / "external-agent-trace-scalecua-r292" / "scalecua-operations.jsonl",
    "R300 query utility operations": OUT_ROOT / "operation-query-utility-r300" / "query-utility-operations.jsonl",
}

FREE_TEXT_FIELDS = {
    "prompt",
    "text",
    "instruction",
    "goal",
    "query",
    "utterance",
    "message",
    "user_request",
    "task_text",
    "task_instruction",
}

ORACLE_FIELDS = {
    "target_positive",
    "problem_oracle",
    "problem_value",
    "looping",
    "side_effect",
    "safety",
    "attack_type",
    "step_correct",
    "step_redundant",
    "human_group",
    "group_pattern",
    "group_position",
}

ROW_FIELDS = [
    "paper_area",
    "claim_or_gap",
    "english_line",
    "outer_evidence",
    "status",
    "next_action",
    "claim_rule",
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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


def source_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for name, path in {"generator script": SCRIPT_PATH, **SOURCES, **OPERATION_JSONL_SOURCES}.items():
        rows.append(
            {
                "source": name,
                "path": rel(path),
                "status": git_status(path),
                "sha256": sha256(path) if path.exists() else "",
            }
        )
    return rows


def line_for(text: str, needle: str) -> str:
    for index, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return str(index)
    return ""


def line_for_any(text: str, needles: list[str]) -> str:
    for needle in needles:
        line = line_for(text, needle)
        if line:
            return line
    return ""


def contains_all(text: str, needles: list[str]) -> bool:
    return all(needle in text for needle in needles)


def scan_operation_text_oracles() -> dict[str, Any]:
    dataset_rows: list[dict[str, Any]] = []
    total_rows = 0
    total_with_free_text = 0
    total_with_oracle = 0
    total_with_both = 0
    for name, path in OPERATION_JSONL_SOURCES.items():
        rows = read_jsonl(path)
        text_fields: set[str] = set()
        oracle_fields: set[str] = set()
        rows_with_free_text = 0
        rows_with_oracle = 0
        rows_with_both = 0
        categorical_task_values: set[str] = set()
        for row in rows:
            fields = row.get("fields", {})
            present_text = {
                key
                for key in FREE_TEXT_FIELDS
                if isinstance(fields.get(key), str) and len(fields.get(key, "").strip()) >= 8
            }
            present_oracle = {
                key
                for key in ORACLE_FIELDS
                if isinstance(fields.get(key), str) and fields.get(key, "").strip()
            }
            if fields.get("task"):
                categorical_task_values.add(str(fields["task"]))
            text_fields.update(present_text)
            oracle_fields.update(present_oracle)
            if present_text:
                rows_with_free_text += 1
            if present_oracle:
                rows_with_oracle += 1
            if present_text and present_oracle:
                rows_with_both += 1
        total_rows += len(rows)
        total_with_free_text += rows_with_free_text
        total_with_oracle += rows_with_oracle
        total_with_both += rows_with_both
        dataset_rows.append(
            {
                "source": name,
                "path": rel(path),
                "rows": len(rows),
                "rows_with_free_text": rows_with_free_text,
                "rows_with_oracle": rows_with_oracle,
                "rows_with_both": rows_with_both,
                "free_text_fields": sorted(text_fields),
                "oracle_fields": sorted(oracle_fields),
                "categorical_task_values": sorted(categorical_task_values)[:8],
            }
        )
    return {
        "sources": dataset_rows,
        "summary": {
            "sources": len(dataset_rows),
            "rows": total_rows,
            "rows_with_free_text": total_with_free_text,
            "rows_with_oracle": total_with_oracle,
            "rows_with_both": total_with_both,
            "has_same_input_free_text_oracle": total_with_both > 0,
        },
    }


def build_rows(
    english: str, chinese: str, evaluation: str, operation_text_scan: dict[str, Any]
) -> list[dict[str, str]]:
    scan = operation_text_scan["summary"]
    return [
        {
            "paper_area": "Overall structure",
            "claim_or_gap": "English draft still presents three RQs, while the outer paper/evaluation ledger uses three empirical profiling experiments plus one replayability/scope-control block.",
            "english_line": line_for(english, "that unsemantic views merge (RQ1)"),
            "outer_evidence": "docs/visexp/paper/main.tex and docs/evaluation.md contain RQ1/E1-RQ4/E4.",
            "status": "gap_to_sync_when_english_edits_are_allowed",
            "next_action": "Do not edit the submodule now. When explicitly allowed, port the four-block structure from the Chinese paper into English.",
            "claim_rule": "Keep the reviewer-facing paper as 3 empirical profiling experiments plus 1 reproducibility/scope block, not a run ledger.",
        },
        {
            "paper_area": "Fidelity / localization",
            "claim_or_gap": "Operation-stack groups localize dataset-provided hidden positives with less flat-summary inspection work and less fixed-session fragmentation.",
            "english_line": line_for(english, "hidden-label localization"),
            "outer_evidence": "R320/R344/R355/R368: 6 tasks, 34,539 operations, 3,699 positives; Work@5 0.0937 vs flat 1.0; median groups 157.5 vs fixed-session 285.0; metric counterpoints preserved.",
            "status": "supported_by_outer_artifacts",
            "next_action": "Use as the main profiling-paper claim; keep flat/fixed-session counterpoints visible.",
            "claim_rule": "Claim profiler localization/ranking fidelity against hidden labels, not human analyst accuracy or universal dominance.",
        },
        {
            "paper_area": "Actionability",
            "claim_or_gap": "Profiler output can guide profile-configuration changes: stack fields, rank features, mapping rules, depth, and boundary-derived fields.",
            "english_line": line_for(english, "agent-driven diagnosis is future work"),
            "outer_evidence": "R324/R325/R335/R340/R341/R345-R350/R354/R358/R366/R400 provide feature, patch, boundary, and suitability evidence; R354 has 5/6 accepted executable profile-spec patches.",
            "status": "supported_as_profile_configuration",
            "next_action": "Write actionability as configuration insight, not automatic patch selection or agent-driven diagnosis.",
            "claim_rule": "Actionability is 'what to tune and why', not an automatic optimizer.",
        },
        {
            "paper_area": "Intent recognition / taggers",
            "claim_or_gap": "Direct regex-vs-embedding-vs-LLM tagger comparison on the same free-form prompts remains future work.",
            "english_line": line_for_any(
                english,
                [
                    "direct comparison among regex, embedding, and LLM taggers",
                    "and LLM taggers on the same free-form prompts remains future work",
                    "assessment of the LLM/regex tagger",
                ],
            ),
            "outer_evidence": (
                "R366 supports deterministic/supervised field derivation and suitability checks, but not a completed same-prompt backend comparison. "
                f"R405 scans {scan['sources']} tracked operation JSONL sources / {scan['rows']} rows and finds "
                f"{scan['rows_with_both']} rows with both public free-form text and oracle semantic labels."
            ),
            "status": "must_remain_future_work",
            "next_action": "Do not claim LLM/regex/embedding tagger accuracy until a same-input evaluation exists.",
            "claim_rule": "Mapping/tagging are operation-field derivation mechanisms; they are not evidence of universal intent recognition.",
        },
        {
            "paper_area": "Boundary detection",
            "claim_or_gap": "Current boundary evidence is supervised or deterministic field derivation, not automatic discovery of every latent intent boundary.",
            "english_line": line_for_any(
                english,
                [
                    "detecting true semantic boundaries",
                    "human-annotated ground truth remains future work",
                    "agent-driven diagnosis is future work",
                ],
            ),
            "outer_evidence": "R297/R299/R355/R366/R400: OSWorld-Human and selected label families support scoped boundary fields; family suitability includes accept/caution/reject outcomes.",
            "status": "supported_only_with_scope",
            "next_action": "Keep 'automatic intent boundary discovery' out of the claim; require family-specific suitability.",
            "claim_rule": "Boundary backends write operation fields before folding and remain inside the two abstractions.",
        },
        {
            "paper_area": "Human utility",
            "claim_or_gap": "The evidence does not show improved human/agent analyst accuracy, time-to-answer, or productivity.",
            "english_line": line_for(english, "human executions"),
            "outer_evidence": "R315/R316 are protocol/sensitivity artifacts; docs/evaluation.md explicitly gates human-utility claims.",
            "status": "unsupported_non_claim",
            "next_action": "Only run an analyst study if the paper wants human utility claims.",
            "claim_rule": "The main claim is profiler fidelity/work/actionability on labeled traces, not analyst productivity.",
        },
        {
            "paper_area": "Trace ecosystem compatibility",
            "claim_or_gap": "The project has standard-trace exchange smoke tests, but no complete compatibility claim for OpenTelemetry/Phoenix/LangSmith/Langfuse/Perfetto producer traces.",
            "english_line": line_for(english, "trace-ecosystem integration"),
            "outer_evidence": "R306/R353 cover Chrome/Perfetto-style exchange containers and byte-identical replay on fixtures/prefixes; real producer imports remain pending.",
            "status": "unsupported_non_claim",
            "next_action": "Import one real producer trace before claiming ecosystem compatibility or span-tree superiority.",
            "claim_rule": "Current span-tree baseline is fixed-session-shaped drilldown, not full ecosystem parity.",
        },
        {
            "paper_area": "Two abstractions",
            "claim_or_gap": "Outer Chinese paper now frames prompt/session/span/task as fields, containers, or baseline shapes over operations, not profiler objects.",
            "english_line": line_for_any(
                english,
                [
                    "two-level representation",
                    "operation-stack profiler",
                    "operation table",
                ],
            ),
            "outer_evidence": "Chinese paper abstract/design plus R394/R375 guardrails preserve operation and operation-stack as the only profiler abstractions.",
            "status": "supported_in_outer_paper",
            "next_action": "When English edits are allowed, align terminology to operation/operation-stack and avoid extra abstract objects.",
            "claim_rule": "Only operation and operation stack are profiler abstractions; mappings, tags, predicates, rankers, and specs configure them.",
        },
    ]


def build_checks(
    rows: list[dict[str, str]],
    english: str,
    chinese: str,
    evaluation: str,
    operation_text_scan: dict[str, Any],
) -> list[dict[str, Any]]:
    row_blob = json.dumps(rows, ensure_ascii=False, sort_keys=True)
    scan = operation_text_scan["summary"]
    checks: list[dict[str, Any]] = []
    checks.append(
        {
            "check": "english_submodule_read_only_scope",
            "passed": True,
            "detail": "This script opens docs/agentpprof-paper/main.tex for reading only and writes outputs only under the outer docs/visexp/out tree.",
        }
    )
    checks.append(
        {
            "check": "three_empirical_plus_one_scope_detected",
            "passed": contains_all(chinese + "\n" + evaluation, ["RQ1/E1", "RQ2/E2", "RQ3/E3", "RQ4/E4"]),
            "detail": "Outer Chinese paper/evaluation ledger expose the four reviewer-facing blocks.",
        }
    )
    checks.append(
        {
            "check": "english_three_rq_gap_detected",
            "passed": contains_all(english, ["RQ1", "RQ2", "RQ3"]) and "RQ4/E4" not in english,
            "detail": "The English submodule draft remains behind the outer four-block organization.",
        }
    )
    checks.append(
        {
            "check": "main_claim_has_outer_evidence",
            "passed": contains_all(row_blob, ["R320", "Work@5 0.0937", "157.5 vs fixed-session 285.0"]),
            "detail": "R405 maps the core localization/work/fragmentation claim to tracked outer artifacts.",
        }
    )
    checks.append(
        {
            "check": "future_work_gaps_explicit",
            "passed": contains_all(
                row_blob,
                [
                    "same free-form prompts remains future work",
                    "improved human/agent analyst accuracy",
                    "OpenTelemetry/Phoenix/LangSmith/Langfuse/Perfetto",
                ],
            ),
            "detail": "R405 lists tagger-comparison, human-utility, and ecosystem-compatibility gaps as non-claims or future work.",
        }
    )
    checks.append(
        {
            "check": "tagger_gap_has_no_current_free_text_oracle",
            "passed": scan["rows"] > 0 and scan["rows_with_both"] == 0,
            "detail": (
                f"Scanned {scan['sources']} tracked operation JSONL sources and {scan['rows']} rows; "
                f"{scan['rows_with_free_text']} rows had public free-form text fields, "
                f"{scan['rows_with_oracle']} rows had oracle fields, and {scan['rows_with_both']} rows had both."
            ),
        }
    )
    checks.append(
        {
            "check": "two_abstraction_boundary_preserved",
            "passed": contains_all(row_blob, ["Only operation and operation stack", "operation and operation-stack"]),
            "detail": "R405 routes mappings, tags, predicates, rankers, and profile specs back to the two profiler abstractions.",
        }
    )
    return checks


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        f"# {RUN_ID} English Paper Experiment Gap Audit",
        "",
        "This is a read-only audit over the English submodule draft and outer-repo evidence.",
        "It is not a new empirical experiment and it does not edit the submodule.",
        "",
        f"- Status: {report['status']}",
        f"- Git commit: `{report['git_commit']}`",
        f"- Rows: {len(report['rows'])}",
        "",
        "## Claim/Gaps",
        "",
        "| Area | Status | Claim or gap | Outer evidence | Next action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["paper_area"],
                    row["status"],
                    row["claim_or_gap"],
                    row["outer_evidence"],
                    row["next_action"],
                ]
            )
            + " |"
        )
    lines.extend(["", "## Checks", "", "| Check | Passed | Detail |", "| --- | --- | --- |"])
    for check in report["checks"]:
        lines.append(f"| {check['check']} | {check['passed']} | {check['detail']} |")
    lines.extend(["", "## Operation Text/Oracle Scan", "", "| Source | Rows | Free-text rows | Oracle rows | Rows with both | Free-text fields | Oracle fields |", "| --- | ---: | ---: | ---: | ---: | --- | --- |"])
    for row in report["operation_text_oracle_scan"]["sources"]:
        lines.append(
            f"| {row['source']} | {row['rows']} | {row['rows_with_free_text']} | {row['rows_with_oracle']} | {row['rows_with_both']} | "
            f"{', '.join(row['free_text_fields']) or '-'} | {', '.join(row['oracle_fields']) or '-'} |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_html(path: Path, report: dict[str, Any]) -> None:
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['paper_area'])}</td>"
        f"<td>{html.escape(row['status'])}</td>"
        f"<td>{html.escape(row['claim_or_gap'])}</td>"
        f"<td>{html.escape(row['outer_evidence'])}</td>"
        f"<td>{html.escape(row['next_action'])}</td>"
        "</tr>"
        for row in report["rows"]
    )
    checks = "\n".join(
        "<tr>"
        f"<td>{html.escape(check['check'])}</td>"
        f"<td>{html.escape(str(check['passed']))}</td>"
        f"<td>{html.escape(check['detail'])}</td>"
        "</tr>"
        for check in report["checks"]
    )
    scan_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['source'])}</td>"
        f"<td>{row['rows']}</td>"
        f"<td>{row['rows_with_free_text']}</td>"
        f"<td>{row['rows_with_oracle']}</td>"
        f"<td>{row['rows_with_both']}</td>"
        f"<td>{html.escape(', '.join(row['free_text_fields']) or '-')}</td>"
        f"<td>{html.escape(', '.join(row['oracle_fields']) or '-')}</td>"
        "</tr>"
        for row in report["operation_text_oracle_scan"]["sources"]
    )
    path.write_text(
        f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{RUN_ID} English Paper Experiment Gap Audit</title>
  <style>
    body {{ font-family: sans-serif; margin: 2rem; line-height: 1.4; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #ccc; padding: 0.35rem; vertical-align: top; }}
    th {{ background: #f2f2f2; }}
  </style>
</head>
<body>
  <h1>{RUN_ID} English Paper Experiment Gap Audit</h1>
  <p>Status: <strong>{html.escape(report['status'])}</strong></p>
  <h2>Claim/Gaps</h2>
  <table>
    <tr><th>Area</th><th>Status</th><th>Claim or gap</th><th>Outer evidence</th><th>Next action</th></tr>
    {rows}
  </table>
  <h2>Checks</h2>
  <table>
    <tr><th>Check</th><th>Passed</th><th>Detail</th></tr>
    {checks}
  </table>
  <h2>Operation Text/Oracle Scan</h2>
  <table>
    <tr><th>Source</th><th>Rows</th><th>Free-text rows</th><th>Oracle rows</th><th>Rows with both</th><th>Free-text fields</th><th>Oracle fields</th></tr>
    {scan_rows}
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

    english = read_text(SOURCES["English paper draft"])
    chinese = read_text(SOURCES["Chinese paper draft"])
    evaluation = read_text(SOURCES["evaluation ledger"])
    operation_text_scan = scan_operation_text_oracles()
    rows = build_rows(english, chinese, evaluation, operation_text_scan)
    checks = build_checks(rows, english, chinese, evaluation, operation_text_scan)
    report: dict[str, Any] = {
        "run_id": RUN_ID,
        "status": "pass" if all(check["passed"] for check in checks) else "fail",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": git_commit(),
        "scope": "read-only English submodule audit; outer-repo outputs only",
        "rows": rows,
        "checks": checks,
        "operation_text_oracle_scan": operation_text_scan,
        "source_status": source_rows(),
    }

    write_csv(out_dir / "english-experiment-gap-audit.csv", rows, ROW_FIELDS)
    write_csv(out_dir / "english-experiment-gap-checks.csv", checks, ["check", "passed", "detail"])
    (out_dir / "english-experiment-gap-audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_markdown(out_dir / "english-experiment-gap-audit.md", report)
    write_html(out_dir / "index.html", report)
    write_csv(out_dir / "source-status.csv", report["source_status"], ["source", "path", "status", "sha256"])
    (out_dir / "run-result.json").write_text(
        json.dumps({"status": report["status"], "run_id": RUN_ID}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if report["status"] != "pass":
        raise SystemExit(f"{RUN_ID} failed; see {rel(out_dir / 'english-experiment-gap-audit.json')}")
    print(f"{RUN_ID} wrote {rel(out_dir / 'english-experiment-gap-audit.json')}")


if __name__ == "__main__":
    main()
