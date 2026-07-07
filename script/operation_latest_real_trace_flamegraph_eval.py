#!/usr/bin/env python3
"""Generate single-benchmark induced operation-stack flamegraphs.

R401 focuses on one real benchmark slice from the tracked R300 operation file.
It intentionally does not ask the user for a field order such as
phase->action->status. Instead, source fields are only candidate evidence. The
script induces a recursive task stack by choosing the next split that best
explains visible operation variation while avoiding fragmentation and hidden
oracle fields.
"""

from __future__ import annotations

import html
import json
import math
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs/visexp/agentpprof-python/src"))
from agentpprof.flamegraph import write_flamegraph_svg  # noqa: E402
from agentpprof.pprof import SemanticSample  # noqa: E402


OUT = ROOT / "docs/visexp/out/latest-real-trace-flamegraph-r401"
SOURCE = ROOT / "docs/visexp/out/operation-query-utility-r300/query-utility-operations.jsonl"
BENCHMARK_FILTER = "dataset=agent-reward-bench"
QUERY_FILTER = "analysis_task=agentreward_looping"
QUERY_NAME = "agentreward_looping"
QUERY_TERMS = {"looping", "loop", "repeat", "same", "run"}
VIEW_SPECS = {
    "agentreward-induced-overview": {
        "title": "AgentReward induced task stack",
        "purpose": "A query-conditioned task stack induced from visible operation fields, without session as a candidate.",
        "allow_session": False,
        "max_depth": 4,
    },
    "agentreward-induced-session-drilldown": {
        "title": "AgentReward induced task stack with session candidate",
        "purpose": "The same induction policy with session available as a candidate split when it explains visible variation.",
        "allow_session": True,
        "max_depth": 5,
    },
}
OVERVIEW_VIEW = "agentreward-induced-overview"
DRILLDOWN_VIEW = "agentreward-induced-session-drilldown"
CONSTANT_METADATA_FIELDS = {"source", "dataset"}
ORACLE_OR_LABEL_FIELDS = {
    "annotator",
    "boundary_label",
    "boundary_positive",
    "correct",
    "label",
    "looping",
    "optimality",
    "oracle",
    "problem_oracle",
    "problem_value",
    "redundant",
    "side_effect",
    "status",
    "target_positive",
    "unsafe",
}
ORACLE_OR_LABEL_PREFIXES = ("problem_",)
ORACLE_OR_LABEL_SUFFIXES = ("_positive", "_oracle", "_label")
METADATA_FIELDS = {
    "agent",
    "analysis_task",
    "benchmark",
    "dataset",
    "environment",
    "experiment",
    "project",
    "query_family",
    "source",
    "source_operation_file",
}
NOISY_ID_OR_NUMERIC_FIELDS = {
    "busted_retry",
    "input_tokens",
    "llm_retries",
    "output_tokens",
    "target",
    "turn",
}
MIN_SECOND_CHILD = 5
MAX_MAJORITY_FRACTION = 0.985
MIN_SCORE = 0.055
MIN_NODE_WEIGHT = 10


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


def load_benchmark_operations() -> list[dict[str, str]]:
    rows = []
    with SOURCE.open() as handle:
        for line in handle:
            record = json.loads(line)
            fields = record["fields"]
            if fields.get("dataset") != "agent-reward-bench":
                continue
            if fields.get("analysis_task") != QUERY_NAME:
                continue
            row = {str(key): str(value) for key, value in fields.items()}
            row["_value"] = str(record.get("value", 1))
            rows.append(row)
    if not rows:
        raise RuntimeError(f"no operations matched {BENCHMARK_FILTER} and {QUERY_FILTER}")
    return rows


def operation_value(row: dict[str, str]) -> int:
    try:
        return max(1, int(float(row.get("_value", "1"))))
    except ValueError:
        return 1


def node_weight(rows: list[dict[str, str]]) -> int:
    return sum(operation_value(row) for row in rows)


def is_numeric_value(value: str) -> bool:
    return bool(re.fullmatch(r"-?\d+(\.\d+)?", value or ""))


def candidate_fields(rows: list[dict[str, str]], allow_session: bool, used_fields: set[str]) -> list[str]:
    keys = sorted(set().union(*(row.keys() for row in rows)))
    candidates = []
    for field in keys:
        if field.startswith("_") or field in used_fields:
            continue
        if is_oracle_or_label_field(field) or field in METADATA_FIELDS or field in NOISY_ID_OR_NUMERIC_FIELDS:
            continue
        if field == "session" and not allow_session:
            continue
        values = [row.get(field, "unknown") or "unknown" for row in rows]
        counts = Counter(values)
        if len(counts) <= 1:
            continue
        if len(counts) > max(40, len(rows) // 2):
            continue
        if sum(1 for value in values if is_numeric_value(value)) / max(1, len(values)) > 0.8:
            continue
        candidates.append(field)
    return candidates


def is_oracle_or_label_field(field: str) -> bool:
    return (
        field in ORACLE_OR_LABEL_FIELDS
        or field.startswith(ORACLE_OR_LABEL_PREFIXES)
        or field.endswith(ORACLE_OR_LABEL_SUFFIXES)
    )


def entropy(counts: Counter[str]) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    return -sum((count / total) * math.log2(count / total) for count in counts.values() if count)


def conditional_entropy(rows: list[dict[str, str]], split_field: str, target_field: str) -> float:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get(split_field, "unknown") or "unknown"].append(row)
    total = len(rows)
    return sum(
        (len(group) / total) * entropy(Counter(row.get(target_field, "unknown") or "unknown" for row in group))
        for group in groups.values()
    )


def split_counts(rows: list[dict[str, str]], field: str) -> Counter[str]:
    return Counter(row.get(field, "unknown") or "unknown" for row in rows)


def score_split(rows: list[dict[str, str]], field: str, candidates: list[str]) -> dict[str, Any] | None:
    counts = split_counts(rows, field)
    values = sorted(counts.values(), reverse=True)
    total = sum(values)
    if len(values) <= 1:
        return None
    second = values[1] if len(values) > 1 else 0
    majority_fraction = values[0] / max(1, total)
    if second < MIN_SECOND_CHILD or majority_fraction > MAX_MAJORITY_FRACTION:
        return None

    split_entropy = entropy(counts)
    balance = split_entropy / math.log2(len(counts)) if len(counts) > 1 else 0.0
    coverage = 1.0 - majority_fraction
    information_gains = []
    for target in candidates:
        if target == field:
            continue
        target_entropy = entropy(split_counts(rows, target))
        if target_entropy <= 0:
            continue
        gain = max(0.0, target_entropy - conditional_entropy(rows, field, target)) / target_entropy
        information_gains.append(gain)
    structural_gain = sum(information_gains) / len(information_gains) if information_gains else 0.0

    searchable = " ".join([field, *counts.keys()]).lower()
    query_bonus = sum(1 for term in QUERY_TERMS if term in searchable) / len(QUERY_TERMS)
    cardinality_penalty = math.log2(len(counts) + 1) / math.log2(total + 1)
    small_child_penalty = sum(count for count in counts.values() if count < MIN_SECOND_CHILD) / max(1, total)
    score = (
        0.62 * structural_gain
        + 0.26 * balance * coverage
        + 0.18 * query_bonus
        - 0.08 * cardinality_penalty
        - 0.20 * small_child_penalty
    )
    return {
        "field": field,
        "score": round(score, 6),
        "structural_gain": round(structural_gain, 6),
        "balance": round(balance, 6),
        "coverage": round(coverage, 6),
        "query_bonus": round(query_bonus, 6),
        "cardinality_penalty": round(cardinality_penalty, 6),
        "small_child_penalty": round(small_child_penalty, 6),
        "groups": dict(sorted(counts.items(), key=lambda item: (-item[1], item[0]))),
    }


def choose_split(rows: list[dict[str, str]], allow_session: bool, used_fields: set[str]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    candidates = candidate_fields(rows, allow_session, used_fields)
    scored = [score for field in candidates if (score := score_split(rows, field, candidates))]
    scored.sort(key=lambda item: (-item["score"], item["field"]))
    selected = scored[0] if scored and scored[0]["score"] >= MIN_SCORE else None
    return selected, scored[:8]


def task_frame(value: str) -> str:
    text = (value or "unknown").lower()
    cleaned = "".join(ch if ch.isalnum() or ch in "._:/+-" else "_" for ch in text).strip("_;")
    return f"task:{cleaned or 'unknown'}"


def recursive_fold(
    rows: list[dict[str, str]],
    spec: dict[str, Any],
    prefix: tuple[str, ...],
    stacks: Counter[tuple[str, ...]],
    stops: Counter[str],
    split_decisions: list[dict[str, Any]],
    used_fields: set[str],
    depth: int,
) -> None:
    weight = node_weight(rows)
    if depth >= spec["max_depth"]:
        stacks[prefix] += weight
        stops["max_depth"] += 1
        return
    if weight < MIN_NODE_WEIGHT:
        stacks[prefix] += weight
        stops["small_node"] += 1
        return

    selected, scored = choose_split(rows, spec["allow_session"], used_fields)
    if not selected:
        stacks[prefix] += weight
        stops["no_material_split"] += 1
        return

    field = selected["field"]
    split_decisions.append(
        {
            "path": list(prefix),
            "source_field": field,
            "node_weight": weight,
            "selected_score": selected,
            "candidate_scores": scored,
        }
    )
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get(field, "unknown") or "unknown"].append(row)
    for value, child_rows in sorted(groups.items(), key=lambda item: (-node_weight(item[1]), item[0])):
        recursive_fold(
            child_rows,
            spec,
            prefix + (task_frame(value),),
            stacks,
            stops,
            split_decisions,
            used_fields | {field},
            depth + 1,
        )


def induced_profile(
    rows: list[dict[str, str]], spec: dict[str, Any]
) -> tuple[Counter[tuple[str, ...]], Counter[str], list[dict[str, Any]]]:
    stacks: Counter[tuple[str, ...]] = Counter()
    stops: Counter[str] = Counter()
    split_decisions: list[dict[str, Any]] = []
    recursive_fold(rows, spec, (), stacks, stops, split_decisions, set(), 0)
    return stacks, stops, split_decisions


def stack_depth_histogram(stacks: Counter[tuple[str, ...]]) -> dict[str, int]:
    hist: Counter[str] = Counter()
    for stack in stacks:
        hist[str(len(stack))] += 1
    return dict(sorted(hist.items(), key=lambda item: int(item[0])))


def top_by_level(stacks: Counter[tuple[str, ...]]) -> dict[str, list[tuple[str, int]]]:
    totals: dict[str, dict[str, int]] = defaultdict(dict)
    for stack, weight in stacks.items():
        for index, frame in enumerate(stack, start=1):
            level = f"task_level_{index}"
            value = frame.split(":", 1)[1] if ":" in frame else frame
            totals[level][value] = totals[level].get(value, 0) + weight
    return {
        field: sorted(values.items(), key=lambda item: (-item[1], item[0]))[:10]
        for field, values in totals.items()
    }


def selected_source_fields(split_decisions: list[dict[str, Any]]) -> list[str]:
    return sorted({decision["source_field"] for decision in split_decisions})


def selected_oracle_source_fields(fields: list[str]) -> list[str]:
    return sorted(field for field in fields if is_oracle_or_label_field(field))


def summarize_profile(
    view_name: str,
    spec: dict[str, Any],
    stacks: Counter[tuple[str, ...]],
    stops: Counter[str],
    split_decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    total_weight = sum(stacks.values())
    unique_stacks = len(stacks)
    fields = selected_source_fields(split_decisions)
    return {
        "view": view_name,
        "title": spec["title"],
        "purpose": spec["purpose"],
        "query": QUERY_FILTER,
        "operations": total_weight,
        "unique_stacks": unique_stacks,
        "compression_ratio": round(total_weight / unique_stacks, 3) if unique_stacks else 0,
        "max_stack_reuse": max(stacks.values()) if stacks else 0,
        "visual_stack_frame": "task",
        "source_fields_selected_by_induction": fields,
        "source_fields_hidden_oracle_overlap": selected_oracle_source_fields(fields),
        "stack": "task",
        "max_stack_depth": max((len(stack) for stack in stacks), default=0),
        "stack_depth_histogram": stack_depth_histogram(stacks),
        "stop_reasons": dict(sorted(stops.items())),
        "where": f"{BENCHMARK_FILTER};{QUERY_FILTER}",
        "constant_metadata_fields_omitted": sorted(CONSTANT_METADATA_FIELDS),
        "top_by_level": top_by_level(stacks),
        "top_stacks": [
            {"stack": ";".join(stack), "weight": weight}
            for stack, weight in sorted(stacks.items(), key=lambda item: (-item[1], item[0]))[:12]
        ],
    }


def maybe_convert_png(svg: Path, png: Path) -> bool:
    converter = shutil.which("convert")
    if not converter:
        return False
    run(
        [
            converter,
            "-background",
            "white",
            str(svg.relative_to(ROOT)),
            str(png.relative_to(ROOT)),
        ]
    )
    return True


def write_folded(path: Path, stacks: Counter[tuple[str, ...]]) -> None:
    lines = [
        f"{';'.join(stack)} {weight}"
        for stack, weight in sorted(stacks.items(), key=lambda item: (";".join(item[0]), item[1]))
    ]
    path.write_text("\n".join(lines) + "\n")


def write_profile_json(
    path: Path,
    view_name: str,
    spec: dict[str, Any],
    summary: dict[str, Any],
    stacks: Counter[tuple[str, ...]],
    split_decisions: list[dict[str, Any]],
) -> None:
    stack_map = {";".join(stack): weight for stack, weight in sorted(stacks.items())}
    ranking = [
        {"stack": stack, "weight": weight, "rank_score": float(weight)}
        for stack, weight in sorted(stack_map.items(), key=lambda item: (-item[1], item[0]))[:20]
    ]
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "generated_at": "1970-01-01T00:00:00Z",
                "profile": {
                    "view": view_name,
                    "sample_type": "operations",
                    "unit": "count",
                    "folding_policy": {
                        "name": "query-conditioned-greedy-task-stack-induction",
                        "min_score": MIN_SCORE,
                        "min_second_child": MIN_SECOND_CHILD,
                        "max_majority_fraction": MAX_MAJORITY_FRACTION,
                        "max_depth": spec["max_depth"],
                        "allow_session": spec["allow_session"],
                    },
                    "visual_stack_frame": "task",
                    "query": QUERY_FILTER,
                    "excluded_oracle_fields": sorted(ORACLE_OR_LABEL_FIELDS),
                    "excluded_oracle_field_prefixes": list(ORACLE_OR_LABEL_PREFIXES),
                    "excluded_oracle_field_suffixes": list(ORACLE_OR_LABEL_SUFFIXES),
                    "summary": summary,
                    "split_decisions": split_decisions,
                    "ranking": {"policy": "width", "groups": len(stacks), "top": ranking},
                    "stacks": stack_map,
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def generate_view(view_name: str, spec: dict[str, Any], rows: list[dict[str, str]]) -> dict[str, Any]:
    base = OUT / view_name
    stacks, stops, split_decisions = induced_profile(rows, spec)
    summary = summarize_profile(view_name, spec, stacks, stops, split_decisions)
    samples = [SemanticSample(stack=stack, value=weight) for stack, weight in stacks.items()]
    write_flamegraph_svg(
        base.with_suffix(".svg"),
        samples,
        f"{spec['title']} operation-stack profile",
        "operations",
        width=1600,
    )
    write_folded(base.with_suffix(".folded"), stacks)
    write_profile_json(base.with_suffix(".profile.json"), view_name, spec, summary, stacks, split_decisions)
    png_written = maybe_convert_png(base.with_suffix(".svg"), base.with_suffix(".png"))
    return {
        "summary": summary,
        "split_decisions": split_decisions,
        "statuses": {
            "svg": {"status": "ok", "generator": "task-stack-induction", "output": str(base.with_suffix(".svg").relative_to(ROOT))},
            "folded": {"status": "ok", "generator": "task-stack-induction", "output": str(base.with_suffix(".folded").relative_to(ROOT))},
            "profile_json": {"status": "ok", "generator": "task-stack-induction", "output": str(base.with_suffix(".profile.json").relative_to(ROOT))},
        },
        "outputs": {
            "svg": base.name + ".svg",
            "png": base.name + ".png" if png_written else None,
            "folded": base.name + ".folded",
            "profile_json": base.name + ".profile.json",
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    lines = [
        "# R401 Latest Real-Trace Operation-Stack Flamegraph",
        "",
        "This artifact focuses on one real benchmark slice and one diagnostic query:",
        f"`{BENCHMARK_FILTER};{QUERY_FILTER}` from the tracked R300 operation file.",
        "It does not ask for a field order. Source fields are candidate mapping inputs, and the rendered stack uses only `task:` frames.",
        "R401 is a visualization/profiler-shape artifact; it is not paper-level localization accuracy evidence.",
        "",
        f"- source: `{result['source']}`",
        f"- filter: `{BENCHMARK_FILTER};{QUERY_FILTER}`",
        f"- folding policy: `{result['folding_policy']['name']}`",
        "",
    ]
    for view in result["views"].values():
        summary = view["summary"]
        lines.extend(
            [
                f"## {summary['title']}",
                "",
                summary["purpose"],
                "",
                f"- operations: {summary['operations']}",
                f"- unique stacks: {summary['unique_stacks']}",
                f"- compression ratio: {summary['compression_ratio']}",
                f"- max stack reuse: {summary['max_stack_reuse']}",
                f"- visual stack frame: `{summary['visual_stack_frame']}`",
                f"- source fields selected by induction: `{summary['source_fields_selected_by_induction']}`",
                f"- hidden/oracle source-field overlap: `{summary['source_fields_hidden_oracle_overlap']}`",
                f"- max stack depth: {summary['max_stack_depth']}",
                f"- stack depth histogram: `{summary['stack_depth_histogram']}`",
                f"- stop reasons: `{summary['stop_reasons']}`",
            ]
        )
        for field in sorted(summary["top_by_level"], key=lambda key: int(key.rsplit("_", 1)[1])):
            rows = summary["top_by_level"].get(field, [])
            if not rows:
                continue
            lines.extend(["", f"| {field} | operations |", "|---|---:|"])
            lines.extend(f"| {name} | {weight} |" for name, weight in rows)
        lines.extend(["", "| selected source field | node weight | score | path |", "|---|---:|---:|---|"])
        for decision in view["split_decisions"][:12]:
            lines.append(
                "| {field} | {weight} | {score} | `{path}` |".format(
                    field=decision["source_field"],
                    weight=decision["node_weight"],
                    score=decision["selected_score"]["score"],
                    path=";".join(decision["path"]) or "<root>",
                )
            )
        lines.append("")
    (OUT / "report.md").write_text("\n".join(lines) + "\n")


def write_index(result: dict[str, Any]) -> None:
    def row(cells: list[Any]) -> str:
        return "<tr>" + "".join(f"<td>{html.escape(str(cell))}</td>" for cell in cells) + "</tr>"

    sections = []
    for view in result["views"].values():
        summary = view["summary"]
        output = view["outputs"]
        field_tables = []
        for field in sorted(summary["top_by_level"], key=lambda key: int(key.rsplit("_", 1)[1])):
            rows = summary["top_by_level"].get(field, [])
            if not rows:
                continue
            body = "\n".join(row([name, weight]) for name, weight in rows)
            field_tables.append(
                f"<h3>{html.escape(field)}</h3>"
                f"<table><thead><tr><th>{html.escape(field)}</th><th>operations</th></tr></thead><tbody>{body}</tbody></table>"
            )
        split_rows = "\n".join(
            row([
                decision["source_field"],
                decision["node_weight"],
                decision["selected_score"]["score"],
                ";".join(decision["path"]) or "<root>",
            ])
            for decision in view["split_decisions"][:20]
        )
        top_rows = "\n".join(row([item["weight"], item["stack"]]) for item in summary["top_stacks"][:10])
        command_rows = "\n".join(
            row([name, f"{status['generator']} -> {status['output']}"])
            for name, status in view["statuses"].items()
        )
        sections.append(
            f"""
<section>
<h2>{html.escape(summary['title'])}</h2>
<p>{html.escape(summary['purpose'])}</p>
<p>
<span class="metric">operations: {summary['operations']}</span>
<span class="metric">unique stacks: {summary['unique_stacks']}</span>
<span class="metric">depths: {html.escape(str(summary['stack_depth_histogram']))}</span>
<span class="metric">oracle-field overlap: {len(summary['source_fields_hidden_oracle_overlap'])}</span>
</p>
<p><code>visual frame: {html.escape(summary['visual_stack_frame'])}</code></p>
<p><code>selected source fields: {html.escape(str(summary['source_fields_selected_by_induction']))}</code></p>
<p><strong>Stop reasons:</strong> <code>{html.escape(str(summary['stop_reasons']))}</code></p>
<iframe src="{html.escape(output['svg'])}"></iframe>
{''.join(field_tables)}
<h3>Selected Splits</h3>
<table><thead><tr><th>source field</th><th>node weight</th><th>score</th><th>path</th></tr></thead><tbody>{split_rows}</tbody></table>
<h3>Top Stacks</h3>
<table><thead><tr><th>weight</th><th>stack</th></tr></thead><tbody>{top_rows}</tbody></table>
<h3>Replay Outputs</h3>
<table><thead><tr><th>output</th><th>generator</th></tr></thead><tbody>{command_rows}</tbody></table>
</section>
"""
        )
    html_doc = f"""<!doctype html>
<meta charset="utf-8">
<title>R401 AgentReward Induced Operation-Stack Flamegraphs</title>
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
<h1>R401 AgentReward Induced Operation-Stack Flamegraphs</h1>
<p>The profiler folds one real benchmark slice from the tracked R300 operation
file. The user supplies a profiling query, not a stack field order. The
induction algorithm chooses visible source fields only as split evidence,
records those choices in JSON, and renders every frame as a recursive
<code>task:</code> frame. Leaves stop early when no candidate split clears the
information-gain and fragmentation gate.</p>
<p><strong>Source:</strong> <code>{html.escape(result['source'])}</code><br>
<strong>Filter:</strong> <code>{html.escape(BENCHMARK_FILTER)};{html.escape(QUERY_FILTER)}</code><br>
<strong>Omitted visual constants:</strong> <code>source,dataset</code></p>
{''.join(sections)}
"""
    (OUT / "index.html").write_text(html_doc)


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(SOURCE)
    clean_output_dir()
    rows = load_benchmark_operations()
    views = {name: generate_view(name, spec, rows) for name, spec in VIEW_SPECS.items()}
    checks = {
        "uses_tracked_real_trace": SOURCE.exists(),
        "single_benchmark_query_rows_loaded": len(rows) == 729,
        "single_benchmark_filter": BENCHMARK_FILTER == "dataset=agent-reward-bench",
        "single_query_filter": QUERY_FILTER == "analysis_task=agentreward_looping",
        "no_user_field_order": all("fields" not in spec for spec in VIEW_SPECS.values()),
        "visual_stack_uses_only_task_frames": all(
            all(frame.startswith("task:") for stack in view["summary"]["top_stacks"] for frame in stack["stack"].split(";"))
            for view in views.values()
        ),
        "no_hidden_oracle_source_fields_selected": all(
            not view["summary"]["source_fields_hidden_oracle_overlap"] for view in views.values()
        ),
        "overview_does_not_allow_session_candidate": not VIEW_SPECS[OVERVIEW_VIEW]["allow_session"],
        "drilldown_allows_session_candidate": VIEW_SPECS[DRILLDOWN_VIEW]["allow_session"],
        "all_views_match_query_count": all(view["summary"]["operations"] == 729 for view in views.values()),
        "overview_has_variable_leaf_depth": len(views[OVERVIEW_VIEW]["summary"]["stack_depth_histogram"]) > 1,
        "drilldown_has_variable_leaf_depth": len(views[DRILLDOWN_VIEW]["summary"]["stack_depth_histogram"]) > 1,
        "drilldown_is_more_detailed": views[OVERVIEW_VIEW]["summary"]["unique_stacks"]
        < views[DRILLDOWN_VIEW]["summary"]["unique_stacks"],
    }
    result = {
        "run_id": "R401",
        "status": "pass" if all(checks.values()) else "fail",
        "source": str(SOURCE.relative_to(ROOT)),
        "filter": f"{BENCHMARK_FILTER};{QUERY_FILTER}",
        "folding_policy": {
            "name": "query-conditioned-greedy-task-stack-induction",
            "min_score": MIN_SCORE,
            "min_second_child": MIN_SECOND_CHILD,
            "max_majority_fraction": MAX_MAJORITY_FRACTION,
        },
        "checks": checks,
        "views": views,
    }
    (OUT / "run-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (OUT / "summary.json").write_text(
        json.dumps({name: view["summary"] for name, view in views.items()}, indent=2, sort_keys=True)
        + "\n"
    )
    write_markdown(result)
    write_index(result)
    print(json.dumps({"status": result["status"], "checks": checks}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
