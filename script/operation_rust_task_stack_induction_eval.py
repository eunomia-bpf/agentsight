#!/usr/bin/env python3
"""Replay Rust boundary-based operation-stack induction on one real labeled trace slice."""

from __future__ import annotations

import html
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/visexp/out/rust-task-stack-induction-r402"
SOURCE = ROOT / "docs/visexp/out/operation-query-utility-r300/query-utility-operations.jsonl"
FILTERS = ["dataset=agent-reward-bench", "analysis_task=agentreward_looping"]
QUERY_TERMS = ["loop", "repeat"]
ORACLE_FIELDS = {
    "annotator",
    "attack",
    "attack_type",
    "boundary_label",
    "boundary_positive",
    "correct",
    "expected_action",
    "gold",
    "gold_action",
    "group",
    "group_id",
    "group_pattern",
    "human_boundary",
    "human_group",
    "label",
    "looping",
    "optimality",
    "oracle",
    "problem_oracle",
    "problem_value",
    "redundant",
    "reference",
    "reference_action",
    "safe",
    "safety",
    "side_effect",
    "status",
    "step_correct",
    "step_optimal",
    "step_redundant",
    "step_success",
    "target_positive",
    "unsafe",
}
ORACLE_PREFIXES = (
    "gold_",
    "group_",
    "human_",
    "label_",
    "oracle_",
    "problem_",
    "reference_",
    "target_",
)
ORACLE_SUFFIXES = (
    "_answer",
    "_attack",
    "_correct",
    "_gold",
    "_ground_truth",
    "_label",
    "_oracle",
    "_positive",
    "_redundant",
    "_reference",
    "_safe",
    "_safety",
    "_target",
    "_unsafe",
)
VIEWS = {
    "agentreward-overview": {
        "title": "Rust induced operation stack",
        "allow_session": False,
    },
    "agentreward-session": {
        "title": "Rust induced operation stack with session candidate",
        "allow_session": True,
    },
}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def clean_output_dir() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in OUT.iterdir():
        if path.is_file():
            path.unlink()


def is_oracle_field(field: str) -> bool:
    return (
        field in ORACLE_FIELDS
        or field.startswith(ORACLE_PREFIXES)
        or field.endswith(ORACLE_SUFFIXES)
    )


def run_agentpprof(view_name: str, spec: dict[str, Any], fmt: str) -> dict[str, Any]:
    suffix = {"json": ".json", "svg": ".svg", "folded": ".folded"}[fmt]
    output = OUT / f"{view_name}{suffix}"
    cmd = [
        "cargo",
        "run",
        "--manifest-path",
        "agentpprof/Cargo.toml",
        "--",
        "--operation-file",
        str(SOURCE.relative_to(ROOT)),
        "--view",
        "operations",
        "--format",
        fmt,
        "--output",
        str(output.relative_to(ROOT)),
        "--induce-operation-stack",
        "--deterministic-output",
    ]
    for predicate in FILTERS:
        cmd.extend(["--where", predicate])
    if spec["allow_session"]:
        cmd.append("--induce-allow-session")
    for term in QUERY_TERMS:
        cmd.extend(["--induce-query-term", term])
    if fmt == "svg":
        cmd.extend(["--svg-width", "1600"])
    completed = run(cmd)
    start = completed.stdout.find("{")
    status = json.loads(completed.stdout[start:]) if start >= 0 else {}
    status["command"] = cmd
    return status


def maybe_convert_png(svg: Path, png: Path) -> bool:
    converter = shutil.which("convert")
    if not converter:
        return False
    run(["convert", "-background", "white", str(svg.relative_to(ROOT)), str(png.relative_to(ROOT))])
    return True


def depth_histogram(stacks: dict[str, int]) -> dict[str, int]:
    hist: Counter[str] = Counter()
    for stack in stacks:
        hist[str(len([frame for frame in stack.split(";") if frame]))] += 1
    return dict(sorted(hist.items(), key=lambda item: int(item[0])))


def all_frames_are_induced_operation(stacks: dict[str, int]) -> bool:
    return all(
        frame.startswith("operation:")
        for stack in stacks
        for frame in stack.split(";")
        if frame
    )


def split_field_counts(induction: dict[str, Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for decision in induction["split_decisions"]:
        counts[decision.get("primary_evidence_field") or decision["source_field"]] += 1
    return dict(sorted(counts.items()))


def evidence_field_counts(induction: dict[str, Any]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for decision in induction["split_decisions"]:
        for field in decision["selected_score"].get("evidence_fields", []):
            counts[field] += 1
    return dict(sorted(counts.items()))


def operation_stack_induction_report(profile: dict[str, Any]) -> dict[str, Any]:
    report = profile.get("operation_stack_induction")
    if report is not None:
        return report
    return profile["task_stack_induction"]


def summarize_view(view_name: str, spec: dict[str, Any], statuses: dict[str, Any]) -> dict[str, Any]:
    profile_doc = json.loads((OUT / f"{view_name}.json").read_text())
    profile = profile_doc["profile"]
    induction = operation_stack_induction_report(profile)
    stacks = profile["stacks"]
    selected_fields = induction.get("selected_evidence_fields") or induction["selected_source_fields"]
    oracle_overlap = sorted(field for field in selected_fields if is_oracle_field(field))
    return {
        "view": view_name,
        "title": spec["title"],
        "allow_session": spec["allow_session"],
        "operations": profile["summary"]["total_weight"],
        "unique_stacks": profile["summary"]["unique_stacks"],
        "compression_ratio": profile["summary"]["compression_ratio"],
        "max_stack_reuse": profile["summary"]["max_stack_reuse"],
        "stack": statuses["json"].get("stack"),
        "induce_operation_stack": statuses["json"].get("induce_operation_stack"),
        "induce_task_stack": statuses["json"].get("induce_task_stack"),
        "selected_evidence_fields": selected_fields,
        "selected_source_fields": selected_fields,
        "oracle_source_field_overlap": oracle_overlap,
        "split_source_field_counts": split_field_counts(induction),
        "split_evidence_field_counts": evidence_field_counts(induction),
        "stop_reasons": induction["stop_reasons"],
        "split_decision_count": len(induction["split_decisions"]),
        "stack_depth_histogram": depth_histogram(stacks),
        "all_frames_are_induced_operation": all_frames_are_induced_operation(stacks),
        "top_stacks": profile["ranking"]["top"][:12],
        "statuses": statuses,
    }


def write_report(result: dict[str, Any]) -> None:
    lines = [
        "# R402 Rust Operation-Stack Induction",
        "",
        "This artifact replays the Rust `agentpprof --induce-operation-stack` implementation on one tracked real-trace slice.",
        "It is a mechanism and visualization artifact: it shows that Rust derives recursive operation-stack segments from adjacent boundary evidence without a user-provided field order.",
        "It is not the paper's hidden-label localization accuracy result.",
        "",
        f"- source: `{result['source']}`",
        f"- filters: `{';'.join(FILTERS)}`",
        f"- query terms: `{QUERY_TERMS}`",
        "",
    ]
    for view in result["views"].values():
        lines.extend(
            [
                f"## {view['title']}",
                "",
                f"- operations: {view['operations']}",
                f"- unique stacks: {view['unique_stacks']}",
                f"- compression ratio: {view['compression_ratio']}",
                f"- stack: `{view['stack']}`",
                f"- selected evidence fields: `{view['selected_evidence_fields']}`",
                f"- split evidence primary-field counts: `{view['split_source_field_counts']}`",
                f"- split evidence-field counts: `{view['split_evidence_field_counts']}`",
                f"- oracle source-field overlap: `{view['oracle_source_field_overlap']}`",
                f"- stack depth histogram: `{view['stack_depth_histogram']}`",
                f"- stop reasons: `{view['stop_reasons']}`",
                f"- split decisions: {view['split_decision_count']}",
                "",
                "| weight | stack |",
                "|---:|---|",
            ]
        )
        lines.extend(f"| {row['weight']} | `{row['stack']}` |" for row in view["top_stacks"][:10])
        lines.append("")
    (OUT / "report.md").write_text("\n".join(lines) + "\n")


def write_index(result: dict[str, Any]) -> None:
    def row(cells: list[Any]) -> str:
        return "<tr>" + "".join(f"<td>{html.escape(str(cell))}</td>" for cell in cells) + "</tr>"

    sections = []
    for view_name, view in result["views"].items():
        top_rows = "\n".join(row([item["weight"], item["stack"]]) for item in view["top_stacks"][:10])
        sections.append(
            f"""
<section>
<h2>{html.escape(view['title'])}</h2>
<p>
<span class="metric">operations: {view['operations']}</span>
<span class="metric">unique stacks: {view['unique_stacks']}</span>
<span class="metric">depths: {html.escape(str(view['stack_depth_histogram']))}</span>
<span class="metric">oracle overlap: {len(view['oracle_source_field_overlap'])}</span>
</p>
	<p><code>selected evidence fields: {html.escape(str(view['selected_evidence_fields']))}</code></p>
<iframe src="{html.escape(view_name + '.svg')}"></iframe>
<h3>Top Stacks</h3>
<table><thead><tr><th>weight</th><th>stack</th></tr></thead><tbody>{top_rows}</tbody></table>
</section>
"""
        )
    html_doc = f"""<!doctype html>
<meta charset="utf-8">
	<title>R402 Rust Operation-Stack Induction</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 24px; color: #1f2933; }}
h1, h2, h3 {{ margin-bottom: 0.3rem; }}
p {{ max-width: 980px; line-height: 1.45; }}
table {{ border-collapse: collapse; margin: 12px 0 24px; width: 100%; }}
th, td {{ border: 1px solid #d8dee9; padding: 6px 8px; vertical-align: top; font-size: 13px; }}
th {{ background: #eef2f7; text-align: left; }}
.metric {{ display: inline-block; margin-right: 18px; font-weight: 650; }}
iframe {{ width: 100%; height: 420px; border: 1px solid #d8dee9; }}
code {{ background: #eef2f7; padding: 1px 4px; border-radius: 4px; }}
section {{ margin-bottom: 42px; }}
</style>
	<h1>R402 Rust Operation-Stack Induction</h1>
	<p>Rust `agentpprof` derives recursive operation-stack segments over one AgentRewardBench
	query slice. The output stack uses only induced segment frames; selected
	evidence fields are recorded as provenance.</p>
{''.join(sections)}
"""
    (OUT / "index.html").write_text(html_doc)


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    clean_output_dir()
    views: dict[str, Any] = {}
    for view_name, spec in VIEWS.items():
        statuses = {fmt: run_agentpprof(view_name, spec, fmt) for fmt in ["json", "folded", "svg"]}
        maybe_convert_png(OUT / f"{view_name}.svg", OUT / f"{view_name}.png")
        views[view_name] = summarize_view(view_name, spec, statuses)
    checks = {
        "uses_tracked_r300_source": SOURCE.exists(),
        "single_benchmark_query": FILTERS == ["dataset=agent-reward-bench", "analysis_task=agentreward_looping"],
        "all_views_use_rust_induction": all(view["induce_operation_stack"] for view in views.values()),
        "all_views_use_boundary_policy": all(
            view["top_stacks"]
            and "recursive-information-gain-operation-stack-induction"
            == operation_stack_induction_report(json.loads((OUT / f"{view_name}.json").read_text())["profile"])["policy"]
            for view_name, view in views.items()
        ),
        "all_views_fold_operation_stack": all(view["stack"] == "operation" for view in views.values()),
        "all_frames_are_induced_operation": all(
            view["all_frames_are_induced_operation"] for view in views.values()
        ),
        "split_decisions_have_boundaries": all(
            decision["selected_score"]["cut_after"] > 0
            and decision["selected_score"]["left_label"] != decision["selected_score"]["right_label"]
            for view_name in views
            for decision in operation_stack_induction_report(
                json.loads((OUT / f"{view_name}.json").read_text())["profile"]
            )["split_decisions"]
        ),
        "boundary_evidence_fields_can_recur": all(max(view["split_source_field_counts"].values() or [0]) > 1 for view in views.values()),
        "no_oracle_source_fields_selected": all(not view["oracle_source_field_overlap"] for view in views.values()),
        "overview_omits_session_candidate": "session" not in views["agentreward-overview"]["selected_evidence_fields"],
        "session_view_can_select_session": "session" in views["agentreward-session"]["selected_evidence_fields"],
        "variable_depth_in_both_views": all(len(view["stack_depth_histogram"]) > 1 for view in views.values()),
        "query_count_matches_agentreward_looping": all(view["operations"] == 729 for view in views.values()),
    }
    result = {
        "run_id": "R402",
        "status": "pass" if all(checks.values()) else "fail",
        "source": str(SOURCE.relative_to(ROOT)),
        "filters": FILTERS,
        "query_terms": QUERY_TERMS,
        "checks": checks,
        "views": views,
    }
    (OUT / "run-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (OUT / "summary.json").write_text(json.dumps(views, indent=2, sort_keys=True) + "\n")
    write_report(result)
    write_index(result)
    print(json.dumps({"status": result["status"], "checks": checks}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
