#!/usr/bin/env python3
"""R319: audit implementation/docs consistency for the semantic profiler.

This is a reproducibility and paper-hygiene gate. It does not fetch datasets,
rerun profiler experiments, or execute a human/agent analyst task. It checks
that the maintained Rust CLI, canonical docs, and Chinese paper agree on the
two core abstractions, profile specs, operation predicates, rank policies, and
standard trace exchange boundary.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "implementation-consistency-r319"

SOURCE_PATHS = {
    "rust_cli": ROOT / "agentpprof" / "src" / "main.rs",
    "rust_profile": ROOT / "agentpprof" / "src" / "profile.rs",
    "rust_standard_trace": ROOT / "agentpprof" / "src" / "standard_trace.rs",
    "standard_trace_cli_test": ROOT / "agentpprof" / "tests" / "standard_trace_cli.rs",
    "implementation_doc": ROOT / "docs" / "implementation.md",
    "design_doc": ROOT / "docs" / "design.md",
    "evaluation_doc": ROOT / "docs" / "evaluation.md",
    "paper_main": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "claim_setup": ROOT / "docs" / "visexp" / "paper" / "evaluation-claims-setup.zh-CN.md",
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


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SystemExit(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def read_sources() -> dict[str, str]:
    sources = {}
    for key, path in SOURCE_PATHS.items():
        if not path.exists():
            raise SystemExit(f"missing {key}: {rel(path)}")
        sources[key] = path.read_text(encoding="utf-8")
    return sources


def check(condition: bool, name: str, evidence: str, failure: str) -> dict[str, Any]:
    return {
        "check": name,
        "status": "pass" if condition else "fail",
        "evidence": evidence if condition else failure,
    }


def contains_all(text: str, needles: list[str]) -> bool:
    return all(needle in text for needle in needles)


def normalize_ws(text: str) -> str:
    return " ".join(text.replace("> ", "").split())


def build_checks(sources: dict[str, str]) -> list[dict[str, Any]]:
    rust_cli = sources["rust_cli"]
    rust_profile = sources["rust_profile"]
    rust_standard_trace = sources["rust_standard_trace"]
    standard_trace_test = sources["standard_trace_cli_test"]
    implementation = sources["implementation_doc"]
    design = sources["design_doc"]
    evaluation = sources["evaluation_doc"]
    paper = sources["paper_main"]
    claim_setup = sources["claim_setup"]

    docs_joined = "\n".join([implementation, design, evaluation, paper, claim_setup])
    claim_setup_flat = normalize_ws(claim_setup)
    return [
        check(
            contains_all(
                rust_cli,
                [
                    "profile_specs: Vec<PathBuf>",
                    "struct RawProfileSpec",
                    "fn load_profile_specs",
                    "operation_files: Vec<PathBuf>",
                    "op_map_files: Vec<PathBuf>",
                    "where_rules: Vec<String>",
                    "rank_rules: Vec<String>",
                ],
            ),
            "rust_profile_spec_cli_present",
            "agentpprof/src/main.rs defines --profile-spec, RawProfileSpec, operation_files, op_map_files, where_rules, and rank_rules.",
            "Rust CLI profile-spec support is missing or renamed.",
        ),
        check(
            contains_all(
                rust_cli,
                [
                    "merge_spec_first(&spec.operation_files, &args.operation_files)",
                    "merge_cli_first(&args.stack_rules, &spec.stack_rules)",
                    "effective_where_rules(&args.where_rules, &spec.where_rules)",
                    "merge_cli_first(&args.rank_rules, &spec.rank_rules)",
                    "load_effective_op_map_rules",
                ],
            ),
            "rust_profile_spec_override_contract",
            "Profile specs provide operation inputs while CLI stack/rule overrides remain explicit.",
            "Profile-spec precedence/override contract is not visible in the Rust CLI.",
        ),
        check(
            contains_all(
                rust_cli,
                [
                    "standard_trace_files: Vec<PathBuf>",
                    "export_standard_trace: Option<PathBuf>",
                    "include_standard_trace_args",
                    "operation_records_from_chrome_trace_files",
                ],
            )
            and "CHROME_TRACE_FORMAT" in rust_standard_trace,
            "rust_standard_trace_cli_present",
            "Rust CLI exposes standard trace import/export and routes imports into operation records.",
            "Rust CLI standard-trace import/export support is missing.",
        ),
        check(
            contains_all(
                standard_trace_test,
                [
                    "cli_exports_and_imports_standard_trace",
                    "standard_trace_events",
                    "chrome-trace-event-json",
                    "--standard-trace-file",
                ],
            ),
            "standard_trace_cli_test_present",
            "agentpprof has a CLI test for standard trace export and import.",
            "Standard trace CLI round-trip test is missing.",
        ),
        check(
            contains_all(
                rust_profile,
                [
                    "pub struct OperationStackConfig",
                    "with_field_rules",
                    "with_filters",
                    "with_rank_rules",
                    "parse_operation_filters",
                    "parse_stack_rank_rules",
                    "summarize_ranked_counter",
                    "build_profile_from_operation_files",
                    "build_profile_from_operation_records",
                ],
            ),
            "rust_operation_stack_source_of_truth",
            "Operation mapping, query predicates, stack folding, and visible rank summaries live in the Rust profile path used by operation files and trace imports.",
            "Rust profile source of truth for operation-stack folding is incomplete.",
        ),
        check(
            "`--where`" in design
            and "`where_rules`" in evaluation
            and "operation-where-filter-r321" in evaluation
            and "predicate" in docs_joined,
            "operation_predicate_documented_as_query_not_object",
            "Docs record --where/where_rules as a query predicate over operation fields, with R321 as the implementation probe.",
            "Operation predicates are missing from docs/evaluation or are not tied to R321.",
        ),
        check(
            "`--rank-rule`" in implementation
            and "`rank_rules`" in design
            and "operation-rust-rank-rule-r322" in evaluation
            and "R322" in paper,
            "operation_rank_policy_documented_as_projection_not_object",
            "Docs record --rank-rule/rank_rules as a visible operation-stack group ranking projection, with R322 as the implementation probe.",
            "Operation rank policies are missing from docs/evaluation/paper or are not tied to R322.",
        ),
        check(
            "`agentpprof/src/standard_trace.rs`" in implementation
            and "`agentpprof/tests/standard_trace_cli.rs`" in implementation
            and "`--profile-spec`" in implementation
            and "Profile specs are implemented" in implementation,
            "implementation_doc_records_current_rust_surface",
            "docs/implementation.md records profile specs and standard trace support as current implementation.",
            "docs/implementation.md does not describe the current Rust profile-spec/standard-trace surface.",
        ),
        check(
            "Add a config-file profile spec" not in implementation
            and "profile spec" in implementation
            and "| Profile-spec reproducibility for operation-stack experiments is implemented" in evaluation,
            "profile_spec_not_stale_pending_task",
            "Profile-spec support is no longer listed as a pending implementation task.",
            "Profile-spec support still appears as a stale pending task.",
        ),
        check(
            "operation` and `operation stack`" in design
            and "operation 和 operation stack" in paper
            and "operation fields 与 operation-stack queries" in claim_setup_flat,
            "two_abstraction_boundary_in_docs",
            "Design, paper, and claim setup preserve operation plus operation stack as the core model.",
            "Two-abstraction boundary is missing from one of the canonical paper docs.",
        ),
        check(
            "third profiler abstraction" not in docs_joined
            or "not a third profiler abstraction" in docs_joined
            or "不是第三个 profiler 抽象" in docs_joined,
            "third_abstraction_guarded",
            "Any third-abstraction language is guarded as a non-claim.",
            "Third-abstraction wording appears without an explicit guardrail.",
        ),
        check(
            "controlled human/agent analyst study" in implementation
            and "real OpenTelemetry GenAI, OpenInference, or Perfetto" in implementation
            and "Deeper subtask/step/sequence-level failure adequacy scorer" in evaluation,
            "remaining_gates_are_real_research_gaps",
            "Remaining implementation/evaluation gates are analyst utility, real trace producer import, and deeper boundary adequacy.",
            "Remaining gates are not stated as research gaps in implementation/evaluation docs.",
        ),
    ]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, checks: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["check", "status", "evidence"],
            lineterminator="\n",
        )
        writer.writeheader()
        for row in checks:
            writer.writerow(
                {
                    "check": row["check"],
                    "status": row["status"],
                    "evidence": row["evidence"],
                }
            )


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Implementation Consistency R319",
        "",
        "R319 checks that the maintained Rust semantic-profiler path, canonical docs, and Chinese paper agree on the current implementation boundary. It is not a dataset sync, not a new profiling run, and not a human/agent analyst-task result.",
        "",
        f"- Overall: `{payload['overall']}`",
        f"- Checks passed: {payload['summary']['passed_checks']} / {payload['summary']['total_checks']}",
        f"- Commit at generation: `{payload['commit']}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Evidence |",
        "|---|---|---|",
    ]
    for row in payload["checks"]:
        lines.append(
            f"| `{row['check']}` | {row['status']} | {row['evidence']} |"
        )
    lines.extend(
        [
            "",
            "## Remaining Gates",
            "",
            "- Execute the controlled human/agent analyst study before claiming accuracy, time-to-answer, productivity, or user utility.",
            "- Add stronger calibrated boundary/backends before claiming automatic or universal intent-boundary discovery.",
            "- Import a real OpenTelemetry GenAI, OpenInference, or Perfetto trace producer before claiming trace-platform compatibility.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, payload: dict[str, Any]) -> None:
    rows = "\n".join(
        "<tr>"
        f"<td><code>{html.escape(row['check'])}</code></td>"
        f"<td>{html.escape(row['status'])}</td>"
        f"<td>{html.escape(row['evidence'])}</td>"
        "</tr>"
        for row in payload["checks"]
    )
    body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Implementation Consistency R319</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.45; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d0d7de; padding: 0.45rem; vertical-align: top; }}
    th {{ background: #f6f8fa; text-align: left; }}
    code {{ background: #f6f8fa; padding: 0.1rem 0.2rem; border-radius: 3px; }}
  </style>
</head>
<body>
  <h1>Implementation Consistency R319</h1>
  <p>Overall: <code>{html.escape(payload['overall'])}</code></p>
  <p>Checks passed: {payload['summary']['passed_checks']} / {payload['summary']['total_checks']}</p>
  <table>
    <thead><tr><th>Check</th><th>Status</th><th>Evidence</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>
"""
    path.write_text(body, encoding="utf-8")


def main() -> None:
    args = parse_args()
    sources = read_sources()
    checks = build_checks(sources)
    passed = sum(1 for row in checks if row["status"] == "pass")
    failed = [row for row in checks if row["status"] != "pass"]
    overall = "implementation_consistent" if not failed else "needs_changes"
    args.out_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "run_id": "R319",
        "overall": overall,
        "status": "ok" if not failed else "fail",
        "commit": git_output(["rev-parse", "HEAD"]),
        "not_dataset_sync": True,
        "not_new_empirical_result": True,
        "not_a_human_study_result": True,
        "not_an_agent_study_result": True,
        "source_paths": {key: rel(path) for key, path in SOURCE_PATHS.items()},
        "summary": {
            "total_checks": len(checks),
            "passed_checks": passed,
            "failed_checks": len(failed),
            "remaining_gates": [
                "controlled human/agent analyst study",
                "calibrated boundary backend beyond simple derived-field baselines",
                "real OpenTelemetry GenAI, OpenInference, or Perfetto trace import",
            ],
        },
        "checks": checks,
    }

    write_json(args.out_dir / "implementation-consistency.json", payload)
    write_csv(args.out_dir / "implementation-consistency.csv", checks)
    write_markdown(args.out_dir / "implementation-consistency.md", payload)
    write_html(args.out_dir / "index.html", payload)
    run_result = {
        "run_id": "R319",
        "status": payload["status"],
        "overall": overall,
        "report": rel(args.out_dir / "implementation-consistency.json"),
        "html": rel(args.out_dir / "index.html"),
        "checks": len(checks),
        "failed_checks": len(failed),
        "not_dataset_sync": True,
        "not_new_empirical_result": True,
    }
    write_json(args.out_dir / "run-result.json", run_result)
    print(json.dumps(run_result, indent=2, sort_keys=True))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
