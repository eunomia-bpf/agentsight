#!/usr/bin/env python3
"""Generate the B4/C5 developer forensic-task benchmark bundle.

The bundle is a protocol artifact, not a user-study result. It turns current
AgentFlame/R114/R131 artifacts into blinded participant packets, a deterministic
answer key, and a response template consumable by score_user_task_results.py.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_OUT = SCRIPT_DIR / "out"
DEFAULT_AGENTFLAME_DIR = REPO_ROOT / ".agentsight" / "agentflame" / "latest"

CONDITION_ORDER = [
    "trace-tree",
    "span-duration",
    "flat-summary",
    "nonsemantic-stack",
    "semantic-stack",
]

PRIMARY_UTILITY_TASKS = ["UT01", "UT04", "UT05", "UT06", "UT07", "UT08", "UT09", "UT10"]
LIMITATION_TASKS = ["UT02", "UT03", "UT11", "UT12", "UT13", "UT14"]
PARTICIPANT_COUNT = 5

PUBLIC_EXCERPT_KEYS = {
    "trace-tree": {
        "slice_id",
        "slice_kind",
        "slice_weight",
        "task_id",
        "category",
        "target_status",
        "lineage_status",
        "status",
        "metric",
        "value",
        "frame_index",
        "frame",
        "frame_type",
        "note",
    },
    "span-duration": {
        "slice_id",
        "slice_kind",
        "slice_weight",
        "task_id",
        "category",
        "duration_seconds",
        "status",
        "metric",
        "value",
        "span",
        "frame_index",
        "event_weight",
        "width_basis",
        "note",
    },
    "flat-summary": {
        "slice_id",
        "slice_kind",
        "slice_weight",
        "agent",
        "tool",
        "cmd",
        "call",
        "process",
        "effect",
        "status",
        "path",
        "count",
        "metric",
        "value",
        "model",
        "kind",
        "family",
        "variant",
        "weight",
        "fragments",
        "runs",
        "note",
    },
    "nonsemantic-stack": {
        "slice_id",
        "slice_kind",
        "slice_weight",
        "stack",
        "baseline_stack",
        "projected_stack",
        "weight",
        "family",
        "variant",
        "mixed_weight_share_pct",
        "mixed_residual_weight_share_pct",
        "residual_pct",
        "raw_join_pct",
        "out_of_scope_effect_events",
        "join_methods",
        "exact_stable_fragments",
        "fragments",
        "note",
    },
    "semantic-stack": {
        "slice_id",
        "slice_kind",
        "slice_weight",
        "stack",
        "semantic",
        "weight",
        "variant",
        "family",
        "total_weight",
        "mixed_weight_share_pct",
        "mixed_residual_weight_share_pct",
        "valid_runs",
        "total_runs",
        "p95_ms",
        "in_scope_effect_events",
        "joined_effect_events",
        "negative_effect_events_observed",
        "negative_joined_effect_events",
        "recall_pct",
        "scope",
        "note",
    },
}

FORBIDDEN_PUBLIC_KEYS = {
    "oracle",
    "oracle_sources",
    "answer_json",
    "projected_stack_hash",
    "top_full_semantic_variants",
    "top_semantic_variants",
    "full_semantic_variant_count",
    "semantic_variant_count",
    "variant_count",
    "mixing_against_full_semantics",
    "projection",
    "baseline_contrast",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def pct(part: int | float, whole: int | float) -> float:
    return round(100.0 * float(part) / float(whole), 3) if whole else 0.0


def stable_id(*parts: Any) -> str:
    text = "\n".join(str(part) for part in parts)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def percentile_nearest_rank(values: list[int | float], percentile: float) -> int | float:
    if not values:
        raise ValueError("cannot compute percentile for an empty list")
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((percentile / 100.0) * len(ordered) + 0.999999) - 1))
    return ordered[index]


def parse_variants(text: str) -> list[dict[str, Any]]:
    variants = []
    for part in text.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        semantic, weight_text = part.rsplit("=", 1)
        try:
            weight = int(weight_text)
        except ValueError:
            continue
        variants.append({"semantic": semantic.strip(), "weight": weight})
    return variants


def stack_frame(stack: str, prefix: str, default: str = "unknown") -> str:
    for frame in stack.split(";"):
        if frame.startswith(prefix):
            return frame.split(":", 1)[1]
    return default


def frame_list(stack: str) -> list[str]:
    return [frame for frame in stack.split(";") if frame]


def frame_type(frame: str) -> str:
    return frame.split(":", 1)[0] if ":" in frame else "frame"


def stack_without(stack: str, prefixes: tuple[str, ...]) -> str:
    return ";".join(frame for frame in frame_list(stack) if not frame.startswith(prefixes))


def with_slice(rows: list[dict[str, Any]], *, slice_id: str, slice_kind: str, slice_weight: int | float) -> list[dict[str, Any]]:
    return [
        {
            "slice_id": slice_id,
            "slice_kind": slice_kind,
            "slice_weight": slice_weight,
            **row,
        }
        for row in rows
    ]


def trace_rows_from_stack(slice_id: str, slice_kind: str, stack: str, weight: int | float) -> list[dict[str, Any]]:
    return with_slice(
        [
            {
                "frame_index": idx,
                "frame": frame,
                "frame_type": frame_type(frame),
                "status": "observed",
            }
            for idx, frame in enumerate(frame_list(stack), 1)
            if not frame.startswith(("session:", "prompt:"))
        ],
        slice_id=slice_id,
        slice_kind=slice_kind,
        slice_weight=weight,
    )


def span_rows_from_stack(slice_id: str, slice_kind: str, stack: str, weight: int | float) -> list[dict[str, Any]]:
    return with_slice(
        [
            {
                "frame_index": idx,
                "span": frame,
                "event_weight": weight,
                "width_basis": "event_weight_same_slice",
                "note": "duration unavailable in folded artifact",
            }
            for idx, frame in enumerate(frame_list(stack), 1)
            if not frame.startswith(("session:", "prompt:"))
        ],
        slice_id=slice_id,
        slice_kind=slice_kind,
        slice_weight=weight,
    )


def flat_rows_from_stack(slice_id: str, slice_kind: str, stack: str, weight: int | float) -> list[dict[str, Any]]:
    return with_slice(
        [
            {
                "agent": stack_frame(stack, "agent:"),
                "tool": stack_frame(stack, "tool:", stack_frame(stack, "call:", "unknown")),
                "call": stack_frame(stack, "call:", "unknown"),
                "cmd": stack_frame(stack, "cmd:", "unknown"),
                "process": stack_frame(stack, "process:", "unknown"),
                "effect": stack_frame(stack, "effect:", stack_frame(stack, "kind:", "unknown")),
                "status": stack_frame(stack, "status:", "unknown"),
                "path": stack_frame(stack, "path:", "unknown"),
                "model": stack_frame(stack, "model:", "unknown"),
                "kind": stack_frame(stack, "kind:", "unknown"),
                "weight": weight,
            }
        ],
        slice_id=slice_id,
        slice_kind=slice_kind,
        slice_weight=weight,
    )


def stack_slice_conditions(
    *,
    task_id: str,
    slice_kind: str,
    stack: str,
    weight: int | float,
    nonsemantic_rows: list[dict[str, Any]],
    semantic_rows: list[dict[str, Any]],
    flat_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    slice_id = stable_id(task_id, slice_kind, stack)
    return standard_conditions(
        trace_rows=trace_rows_from_stack(slice_id, slice_kind, stack, weight),
        span_rows=span_rows_from_stack(slice_id, slice_kind, stack, weight),
        flat_rows=with_slice(flat_rows, slice_id=slice_id, slice_kind=slice_kind, slice_weight=weight)
        if flat_rows is not None
        else flat_rows_from_stack(slice_id, slice_kind, stack, weight),
        nonsemantic_rows=with_slice(nonsemantic_rows, slice_id=slice_id, slice_kind=slice_kind, slice_weight=weight),
        semantic_rows=with_slice(semantic_rows, slice_id=slice_id, slice_kind=slice_kind, slice_weight=weight),
    )


def metric_slice_conditions(
    *,
    task_id: str,
    slice_kind: str,
    weight: int | float,
    trace_rows: list[dict[str, Any]],
    span_rows: list[dict[str, Any]],
    flat_rows: list[dict[str, Any]],
    nonsemantic_rows: list[dict[str, Any]],
    semantic_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    slice_id = stable_id(task_id, slice_kind, json.dumps(flat_rows, sort_keys=True))
    return standard_conditions(
        trace_rows=with_slice(trace_rows, slice_id=slice_id, slice_kind=slice_kind, slice_weight=weight),
        span_rows=with_slice(span_rows, slice_id=slice_id, slice_kind=slice_kind, slice_weight=weight),
        flat_rows=with_slice(flat_rows, slice_id=slice_id, slice_kind=slice_kind, slice_weight=weight),
        nonsemantic_rows=with_slice(nonsemantic_rows, slice_id=slice_id, slice_kind=slice_kind, slice_weight=weight),
        semantic_rows=with_slice(semantic_rows, slice_id=slice_id, slice_kind=slice_kind, slice_weight=weight),
    )


def variant_by(r131: dict[str, Any], family: str, variant: str) -> dict[str, Any]:
    for row in r131["variants"]:
        if row["family"] == family and row["variant"] == variant:
            return row
    raise AssertionError(f"missing R131 variant {family}/{variant}")


def first_example(row: dict[str, Any], contains: str | None = None) -> dict[str, Any]:
    examples = row["mixing_against_full_semantics"].get("examples") or []
    if contains is None:
        if not examples:
            raise AssertionError("variant has no examples")
        return examples[0]
    for example in examples:
        if contains in example["projected_stack"]:
            return example
    raise AssertionError(f"missing example containing {contains!r}")


def top_semantic(example: dict[str, Any]) -> dict[str, Any]:
    variants = semantic_variants(example)
    if not variants:
        raise AssertionError("example has no semantic variants")
    return variants[0]


def semantic_variants(example: dict[str, Any]) -> list[dict[str, Any]]:
    return example.get("top_full_semantic_variants") or example.get("top_semantic_variants") or []


def example_stack(example: dict[str, Any]) -> str:
    return example.get("projected_stack") or example.get("baseline_stack") or ""


def example_variant_count(example: dict[str, Any]) -> int:
    return int(example.get("full_semantic_variant_count") or example.get("semantic_variant_count") or 0)


def as_excerpt(title: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"title": title, "rows": rows}


def public_row(condition: str, row: dict[str, Any]) -> dict[str, Any]:
    allowed = PUBLIC_EXCERPT_KEYS[condition]
    return {key: value for key, value in row.items() if key in allowed}


def public_rows(condition: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [public_row(condition, row) for row in rows]


def public_condition_rows(condition: str, rows: list[dict[str, Any]], title: str) -> list[dict[str, Any]]:
    return [as_excerpt(title, public_rows(condition, rows))]


def reject_public_leaks(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        forbidden = sorted(set(value) & FORBIDDEN_PUBLIC_KEYS)
        if forbidden:
            raise AssertionError(f"participant packet leaks forbidden key(s) at {path}: {forbidden}")
        for key, child in value.items():
            reject_public_leaks(child, f"{path}.{key}")
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            reject_public_leaks(child, f"{path}[{idx}]")


def collect_slice_ids(value: Any) -> set[str]:
    ids: set[str] = set()
    if isinstance(value, dict):
        if "slice_id" in value:
            ids.add(str(value["slice_id"]))
        for child in value.values():
            ids |= collect_slice_ids(child)
    elif isinstance(value, list):
        for child in value:
            ids |= collect_slice_ids(child)
    return ids


def validate_task_same_slice(task_item: dict[str, Any]) -> None:
    expected: set[str] | None = None
    for condition in task_item["participant_view_conditions"]:
        ids = collect_slice_ids(condition.get("view_excerpt", []))
        if len(ids) != 1:
            raise AssertionError(
                f"{task_item['task_id']} {condition['condition']} must expose exactly one slice_id, got {sorted(ids)}"
            )
        if expected is None:
            expected = ids
        elif ids != expected:
            raise AssertionError(
                f"{task_item['task_id']} condition {condition['condition']} has slice_id {sorted(ids)}; expected {sorted(expected)}"
            )


def public_title(task_id: str) -> str:
    return f"Task {task_id}"


def conditions(*items: tuple[Any, ...]) -> list[dict[str, Any]]:
    out = []
    for item in items:
        name = item[0]
        views = item[1]
        excerpt = item[2] if len(item) > 2 else []
        out.append({"condition": name, "views": views, "view_excerpt": excerpt})
    return out


def standard_conditions(
    *,
    trace_rows: list[dict[str, Any]],
    span_rows: list[dict[str, Any]],
    flat_rows: list[dict[str, Any]],
    nonsemantic_rows: list[dict[str, Any]],
    semantic_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return conditions(
        (
            "trace-tree",
            ["session/tool chronological tree excerpt"],
            public_condition_rows("trace-tree", trace_rows, "trace tree excerpt"),
        ),
        (
            "span-duration",
            ["span-duration flamegraph excerpt"],
            public_condition_rows("span-duration", span_rows, "duration-ordered span excerpt"),
        ),
        (
            "flat-summary",
            ["process/effect/path summary excerpt"],
            public_condition_rows("flat-summary", flat_rows, "flat summary excerpt"),
        ),
        (
            "nonsemantic-stack",
            ["nonsemantic folded stack excerpt"],
            public_condition_rows("nonsemantic-stack", nonsemantic_rows, "nonsemantic folded excerpt"),
        ),
        (
            "semantic-stack",
            ["semantic effect flamegraph excerpt"],
            public_condition_rows("semantic-stack", semantic_rows, "semantic folded excerpt"),
        ),
    )


def answer_fields(answer: dict[str, Any]) -> list[str]:
    return sorted(answer)


def task(
    task_id: str,
    title: str,
    question: str,
    participant_view_conditions: list[dict[str, Any]],
    oracle_sources: list[str],
    oracle: dict[str, Any],
    baseline_contrast: str,
    skill: str,
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "claim": "C5",
        "analysis_role": "primary_utility" if task_id in PRIMARY_UTILITY_TASKS else "limitation_check",
        "skill": skill,
        "title": title,
        "question": question,
        "participant_view_conditions": participant_view_conditions,
        "oracle_sources": oracle_sources,
        "answer_format": {field: type(value).__name__ for field, value in oracle.items()},
        "oracle": oracle,
        "scoring": {
            "method": "exact field match against oracle",
            "required_fields": answer_fields(oracle),
        },
        "baseline_contrast": baseline_contrast,
    }


def r114_span_rows(r114: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    tasks = sorted(
        r114.get("tasks", []),
        key=lambda row: float(row.get("duration_seconds") or 0),
        reverse=True,
    )[:limit]
    return [
        {
            "task_id": row.get("task_id"),
            "category": row.get("category"),
            "duration_seconds": row.get("duration_seconds"),
            "status": row.get("status"),
        }
        for row in tasks
    ]


def r114_trace_rows(r114: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    return [
        {
            "task_id": row.get("task_id"),
            "category": row.get("category"),
            "target_status": row.get("target_status"),
            "lineage_status": row.get("lineage_status"),
        }
        for row in r114.get("tasks", [])[:limit]
    ]


def r114_flat_rows(r114: dict[str, Any]) -> list[dict[str, Any]]:
    agg = r114["aggregate"]
    return [
        {"metric": key, "value": agg.get(key)}
        for key in [
            "effect_events",
            "in_scope_effect_events",
            "joined_effect_events",
            "out_of_scope_effect_events",
            "negative_effect_events_observed",
            "negative_joined_effect_events",
            "raw_join_pct",
            "precision_pct",
            "recall_pct",
        ]
    ]


def build_tasks(
    *,
    out_dir: Path,
    agentflame_dir: Path,
    agent: dict[str, Any],
    r114: dict[str, Any],
    r123: dict[str, Any],
    r131: dict[str, Any],
) -> list[dict[str, Any]]:
    summary = agent["summary"]
    system_top = summary["system"]["top"]
    token_top = summary["token"]["top"]
    command_rows = summary["command_summary"]
    mixing = summary["semantic_mixing"]["nonsemantic"]["examples"]
    flat_mixing = summary["semantic_mixing"]["flat"]["examples"]
    system_no = variant_by(r131, "system", "no-semantic")
    system_session = variant_by(r131, "system", "session-only")
    system_prompt = variant_by(r131, "system", "prompt-only")
    token_prompt_llm = variant_by(r131, "token", "prompt+llm-call")
    no_example = first_example(system_no)
    session_example = first_example(system_session)
    prompt_example = first_example(system_prompt)
    cargo_example = next(ex for ex in mixing if "process:cargo;effect:test" in ex["baseline_stack"])
    python_example = next(ex for ex in mixing if "process:python3;effect:process" in ex["baseline_stack"])
    docker_example = next(ex for ex in mixing if "process:docker;effect:process" in ex["baseline_stack"])
    git_flat = next(ex for ex in flat_mixing if "process:git;effect:read" in ex["baseline_stack"])
    path_stack = next(row for row in system_top if "path:" in row["stack"])
    top_system = system_top[0]
    top_token = token_top[0]
    r114_agg = r114["aggregate"]
    r123_model = r123["aggregate"]
    r123_bench = r123["bench"]
    r123_bench_model = r123_bench["models"][0]
    r123_p95_ms = int(percentile_nearest_rank(r123_bench_model["latency_ms"], 95))

    def sem_rows(example: dict[str, Any]) -> list[dict[str, Any]]:
        return semantic_variants(example)[:8]

    def projected_row(example: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "projected_stack": example_stack(example),
                "weight": example["weight"],
            }
        ]

    tasks: list[dict[str, Any]] = []

    top = top_semantic(no_example)
    tasks.append(
        task(
            "UT01",
            "Top Nonsemantic System Mixing",
            "Which high-weight nonsemantic system bucket is dominated by which semantic region?",
            stack_slice_conditions(
                task_id="UT01",
                slice_kind="system-nonsemantic-bucket",
                stack=example_stack(no_example),
                weight=no_example["weight"],
                nonsemantic_rows=projected_row(no_example),
                semantic_rows=sem_rows(no_example),
            ),
            ["docs/visexp/out/semantic-ablation-r131.json"],
            {
                "projected_stack_hash": no_example["projected_stack_hash"],
                "weight": int(no_example["weight"]),
                "top_semantic": top["semantic"],
                "top_semantic_weight": int(top["weight"]),
            },
            "Trace/span/flat views show activity but do not expose the semantic split inside this repeated bucket.",
            "find-hidden-semantic-mixing",
        )
    )

    tasks.append(
        task(
            "UT02",
            "Prompt Axis Contribution",
            "How much does prompt-only projection reduce system-effect mixing compared with no semantic axis?",
            metric_slice_conditions(
                task_id="UT02",
                slice_kind="system-ablation-axis",
                weight=system_no["projection"]["total_weight"],
                trace_rows=[
                    {"metric": "family", "value": "system"},
                    {"metric": "comparison", "value": "no-semantic vs prompt-only"},
                ],
                span_rows=[
                    {"span": "no-semantic", "event_weight": system_no["projection"]["total_weight"], "width_basis": "same_projection_total"},
                    {"span": "prompt-only", "event_weight": system_prompt["projection"]["total_weight"], "width_basis": "same_projection_total"},
                ],
                flat_rows=[
                    {"variant": "no-semantic", "metric": "mixed_weight_share_pct", "value": system_no["mixing_against_full_semantics"]["mixed_weight_share_pct"]},
                    {"variant": "prompt-only", "metric": "mixed_weight_share_pct", "value": system_prompt["mixing_against_full_semantics"]["mixed_weight_share_pct"]},
                ],
                nonsemantic_rows=[
                    {"variant": "no-semantic", **system_no["mixing_against_full_semantics"]},
                    {"variant": "prompt-only", **system_prompt["mixing_against_full_semantics"]},
                ],
                semantic_rows=[system_no["projection"], system_prompt["projection"]],
            ),
            ["docs/visexp/out/semantic-ablation-r131.json"],
            {
                "no_semantic_mixed_pct": 90.219,
                "prompt_only_mixed_pct": 37.687,
                "reduction_points": 52.532,
                "no_semantic_residual_pct": 44.639,
                "prompt_only_residual_pct": 7.526,
            },
            "A nonsemantic flamegraph aggregates repeated work but cannot quantify which semantic axis reduced mixing.",
            "compare-semantic-axis",
        )
    )

    tasks.append(
        task(
            "UT03",
            "Session Versus Prompt Axis",
            "Which single semantic axis separates system effects better: session or prompt?",
            metric_slice_conditions(
                task_id="UT03",
                slice_kind="system-ablation-axis",
                weight=system_session["projection"]["total_weight"],
                trace_rows=[
                    {"metric": "family", "value": "system"},
                    {"metric": "comparison", "value": "session-only vs prompt-only"},
                ],
                span_rows=[
                    {"span": "session-only", "event_weight": system_session["projection"]["total_weight"], "width_basis": "same_projection_total"},
                    {"span": "prompt-only", "event_weight": system_prompt["projection"]["total_weight"], "width_basis": "same_projection_total"},
                ],
                flat_rows=[
                    {"variant": "session-only", "metric": "mixed_weight_share_pct", "value": system_session["mixing_against_full_semantics"]["mixed_weight_share_pct"]},
                    {"variant": "prompt-only", "metric": "mixed_weight_share_pct", "value": system_prompt["mixing_against_full_semantics"]["mixed_weight_share_pct"]},
                ],
                nonsemantic_rows=[
                    {"variant": "session-only", **system_session["mixing_against_full_semantics"]},
                    {"variant": "prompt-only", **system_prompt["mixing_against_full_semantics"]},
                ],
                semantic_rows=[
                    {"semantic": top_semantic(session_example)["semantic"], "weight": top_semantic(session_example)["weight"]},
                    {"semantic": top_semantic(prompt_example)["semantic"], "weight": top_semantic(prompt_example)["weight"]},
                ],
            ),
            ["docs/visexp/out/semantic-ablation-r131.json"],
            {
                "better_axis": "prompt",
                "session_only_mixed_pct": 84.18,
                "prompt_only_mixed_pct": 37.687,
                "session_only_residual_pct": 34.138,
                "prompt_only_residual_pct": 7.526,
            },
            "This task isolates mechanism: prompt tags carry most system-effect separation in the current corpus.",
            "compare-semantic-axis",
        )
    )

    tasks.append(
        task(
            "UT04",
            "Heaviest Repeated Semantic Stack",
            "Identify the heaviest semantic system stack and its semantic/effect fields.",
            stack_slice_conditions(
                task_id="UT04",
                slice_kind="semantic-system-stack",
                stack=top_system["stack"],
                weight=top_system["weight"],
                nonsemantic_rows=[{"stack": stack_without(top_system["stack"], ("session:", "prompt:")), "weight": top_system["weight"]}],
                semantic_rows=[top_system],
            ),
            [rel(agentflame_dir / "agentflame.json")],
            {
                "weight": int(top_system["weight"]),
                "session": stack_frame(top_system["stack"], "session:"),
                "prompt": stack_frame(top_system["stack"], "prompt:"),
                "call": stack_frame(top_system["stack"], "call:"),
                "effect": stack_frame(top_system["stack"], "effect:"),
                "status": stack_frame(top_system["stack"], "status:"),
            },
            "A flat summary can reveal volume, but the semantic stack names the task region causing it.",
            "find-repeated-heavy-behavior",
        )
    )

    tasks.append(
        task(
            "UT05",
            "Heaviest Path-Specific Read",
            "Find the heaviest path-specific system-effect stack and report process, path, and semantic tags.",
            stack_slice_conditions(
                task_id="UT05",
                slice_kind="semantic-path-stack",
                stack=path_stack["stack"],
                weight=path_stack["weight"],
                nonsemantic_rows=[{"stack": stack_without(path_stack["stack"], ("session:", "prompt:")), "weight": path_stack["weight"]}],
                semantic_rows=[path_stack],
            ),
            [rel(agentflame_dir / "agentflame.json")],
            {
                "weight": int(path_stack["weight"]),
                "session": stack_frame(path_stack["stack"], "session:"),
                "prompt": stack_frame(path_stack["stack"], "prompt:"),
                "process": stack_frame(path_stack["stack"], "process:"),
                "effect": stack_frame(path_stack["stack"], "effect:"),
                "path": stack_frame(path_stack["stack"], "path:"),
            },
            "Traditional file summaries can find a hot path, but not the prompt/session region that caused it.",
            "find-path-effect-provenance",
        )
    )

    for task_id, title, example, process_name in [
        ("UT06", "Cargo Test Semantic Split", cargo_example, "cargo"),
        ("UT07", "Python Process Semantic Split", python_example, "python3"),
        ("UT08", "Docker Process Semantic Split", docker_example, "docker"),
    ]:
        top_variant = top_semantic(example)
        tasks.append(
            task(
                task_id,
                title,
                f"For the {process_name} bucket, report total weight and the dominant semantic variant.",
                stack_slice_conditions(
                    task_id=task_id,
                    slice_kind=f"{process_name}-command-bucket",
                    stack=example_stack(example),
                    weight=example["weight"],
                    nonsemantic_rows=projected_row(example),
                    semantic_rows=sem_rows(example),
                ),
                [rel(agentflame_dir / "agentflame.json")],
                {
                    "baseline_stack": example["baseline_stack"],
                    "weight": int(example["weight"]),
                    "top_semantic": top_variant["semantic"],
                    "top_semantic_weight": int(top_variant["weight"]),
                },
                "The baseline can name the command/effect bucket; semantic aggregation identifies the task split.",
                "explain-command-effect-mixing",
            )
        )

    flat_top = top_semantic(git_flat)
    tasks.append(
        task(
            "UT09",
            "Flat Git Read Baseline Failure",
            "In the flat git/read bucket, which semantic region dominates?",
            stack_slice_conditions(
                task_id="UT09",
                slice_kind="flat-git-read-bucket",
                stack=example_stack(git_flat),
                weight=git_flat["weight"],
                flat_rows=projected_row(git_flat),
                nonsemantic_rows=projected_row(git_flat),
                semantic_rows=sem_rows(git_flat),
            ),
            [rel(agentflame_dir / "agentflame.json")],
            {
                "baseline_stack": git_flat["baseline_stack"],
                "weight": int(git_flat["weight"]),
                "top_semantic": flat_top["semantic"],
                "top_semantic_weight": int(flat_top["weight"]),
            },
            "Flat process summaries find git/read volume but lose the task intent behind it.",
            "compare-flat-vs-semantic",
        )
    )

    tasks.append(
        task(
            "UT10",
            "Largest Token Region",
            "Identify the largest token stack and report its semantic/token fields.",
            stack_slice_conditions(
                task_id="UT10",
                slice_kind="semantic-token-stack",
                stack=top_token["stack"],
                weight=top_token["weight"],
                flat_rows=[{"model": stack_frame(top_token["stack"], "model:"), "kind": stack_frame(top_token["stack"], "kind:"), "weight": top_token["weight"]}],
                nonsemantic_rows=[{"stack": stack_without(top_token["stack"], ("session:", "prompt:", "call:")), "weight": top_token["weight"]}],
                semantic_rows=[top_token],
            ),
            [rel(agentflame_dir / "agentflame.json")],
            {
                "weight": int(top_token["weight"]),
                "session": stack_frame(top_token["stack"], "session:"),
                "prompt": stack_frame(top_token["stack"], "prompt:"),
                "llm_call": stack_frame(top_token["stack"], "call:"),
                "model": stack_frame(top_token["stack"], "model:"),
                "kind": stack_frame(top_token["stack"], "kind:"),
            },
            "Token cost views need semantic frames to explain which task region consumed the token mass.",
            "find-token-hotspot",
        )
    )

    token_mix = token_prompt_llm["mixing_against_full_semantics"]
    tasks.append(
        task(
            "UT11",
            "LLM-Call Axis Boundary",
            "Does prompt+LLM-call alone fully explain token provenance, and what residual remains?",
            metric_slice_conditions(
                task_id="UT11",
                slice_kind="token-ablation-axis",
                weight=token_prompt_llm["projection"]["total_weight"],
                trace_rows=[
                    {"metric": "family", "value": "token"},
                    {"metric": "comparison", "value": "prompt+llm-call vs full token semantics"},
                ],
                span_rows=[
                    {"span": "prompt+llm-call", "event_weight": token_prompt_llm["projection"]["total_weight"], "width_basis": "same_projection_total"}
                ],
                flat_rows=[{"family": "token", "variant": "prompt+llm-call", "metric": "mixed_weight_share_pct", "value": token_mix["mixed_weight_share_pct"]}],
                nonsemantic_rows=[{"family": "token", "variant": "prompt+llm-call", "mixed_weight_share_pct": token_mix["mixed_weight_share_pct"]}],
                semantic_rows=[{"family": "token", "variant": "prompt+llm-call", "mixed_residual_weight_share_pct": token_mix["mixed_residual_weight_share_pct"]}],
            ),
            ["docs/visexp/out/semantic-ablation-r131.json"],
            {
                "prompt_llm_mixed_bucket_pct": 95.765,
                "prompt_llm_residual_pct": 0.027,
                "llm_call_system_effect_axis": False,
                "correct_scope": "token_navigation",
            },
            "This guards against overclaiming LLM-call tags as system-effect attribution axes.",
            "avoid-axis-overclaim",
        )
    )

    tasks.append(
        task(
            "UT12",
            "Exact-Lineage Negative Controls",
            "For the R114 exact-lineage suite, report scoped join and negative-control outcomes.",
            metric_slice_conditions(
                task_id="UT12",
                slice_kind="r114-lineage-suite",
                weight=r114_agg["in_scope_effect_events"],
                trace_rows=r114_trace_rows(r114, 8),
                span_rows=[
                    {"span": row.get("task_id"), "event_weight": row.get("duration_seconds"), "width_basis": "task_duration_seconds", "status": row.get("status")}
                    for row in r114_span_rows(r114, 8)
                ],
                flat_rows=r114_flat_rows(r114),
                nonsemantic_rows=[{"join_methods": r114_agg.get("join_methods", {})}],
                semantic_rows=[
                    {
                        "in_scope_effect_events": r114_agg["in_scope_effect_events"],
                        "joined_effect_events": r114_agg["joined_effect_events"],
                        "negative_effect_events_observed": r114_agg["negative_effect_events_observed"],
                        "negative_joined_effect_events": r114_agg["negative_joined_effect_events"],
                    }
                ],
            ),
            ["docs/visexp/out/live-record-r114.json", "docs/visexp/out/live-record-r114-analysis.json"],
            {
                "in_scope_effect_events": int(r114_agg["in_scope_effect_events"]),
                "joined_effect_events": int(r114_agg["joined_effect_events"]),
                "precision_pct": float(r114_agg["precision_pct"]),
                "recall_pct": float(r114_agg["recall_pct"]),
                "negative_effect_events_observed": int(r114_agg["negative_effect_events_observed"]),
                "negative_joined_effect_events": int(r114_agg["negative_joined_effect_events"]),
            },
            "Span traces show execution; exact provenance checks whether system effects inherit the right agent ancestry.",
            "check-exact-lineage",
        )
    )

    tasks.append(
        task(
            "UT13",
            "Raw Join Versus Scoped Recall",
            "Why is R114 raw join much lower than scoped recall, and what are the key numbers?",
            metric_slice_conditions(
                task_id="UT13",
                slice_kind="r114-lineage-scope",
                weight=r114_agg["effect_events"],
                trace_rows=r114_trace_rows(r114, 8),
                span_rows=[
                    {"span": row.get("task_id"), "event_weight": row.get("duration_seconds"), "width_basis": "task_duration_seconds", "status": row.get("status")}
                    for row in r114_span_rows(r114, 8)
                ],
                flat_rows=r114_flat_rows(r114),
                nonsemantic_rows=[{"raw_join_pct": r114_agg["raw_join_pct"], "out_of_scope_effect_events": r114_agg["out_of_scope_effect_events"]}],
                semantic_rows=[{"recall_pct": r114_agg["recall_pct"], "scope": "retargeted agent process family"}],
            ),
            ["docs/visexp/out/live-record-r114.json"],
            {
                "raw_join_pct": float(r114_agg["raw_join_pct"]),
                "recall_pct": float(r114_agg["recall_pct"]),
                "out_of_scope_effect_events": int(r114_agg["out_of_scope_effect_events"]),
                "correct_interpretation": "out_of_scope_effects_remain_orphaned",
            },
            "This task tests whether users avoid confusing raw coverage with scoped lineage recall.",
            "avoid-lineage-overclaim",
        )
    )

    tasks.append(
        task(
            "UT14",
            "3B Tag Stability Boundary",
            "Report the real-fragment 3B tag-stability numbers and the correct claim boundary.",
            metric_slice_conditions(
                task_id="UT14",
                slice_kind="r123-model-stability",
                weight=r123_model["total_runs"],
                trace_rows=[
                    {"metric": "model", "value": "3b"},
                    {"metric": "fragment_count", "value": r123_bench["fragments_per_model"]},
                ],
                span_rows=[
                    {"span": "3b-tagging", "event_weight": r123_model["total_runs"], "width_basis": "llm_call_count"}
                ],
                flat_rows=[{"model": "3b", "fragments": r123_bench["fragments_per_model"], "runs": r123_model["total_runs"]}],
                nonsemantic_rows=[{"exact_stable_fragments": r123_model["exact_stable_fragments"], "fragments": r123_bench["fragments_per_model"]}],
                semantic_rows=[{"valid_runs": r123_model["ok_runs"], "total_runs": r123_model["total_runs"], "p95_ms": r123_p95_ms}],
            ),
            ["docs/visexp/out/model-benchmarks-r123.json"],
            {
                "valid_runs": int(r123_model["ok_runs"]),
                "total_runs": int(r123_model["total_runs"]),
                "exact_stable_fragments": int(r123_model["exact_stable_fragments"]),
                "fragments": int(r123_bench["fragments_per_model"]),
                "p95_ms": r123_p95_ms,
                "human_adequacy_proven": False,
            },
            "This is a boundary task: stable one-word tags do not prove human adequacy.",
            "avoid-tag-overclaim",
        )
    )

    return tasks


def write_answer_key(path: Path, tasks: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["task_id", "answer_json"], lineterminator="\n")
        writer.writeheader()
        for item in tasks:
            writer.writerow(
                {
                    "task_id": item["task_id"],
                    "answer_json": json.dumps(item["oracle"], sort_keys=True),
                }
            )


def build_assignments(tasks: list[dict[str, Any]], participant_count: int = PARTICIPANT_COUNT) -> list[dict[str, Any]]:
    task_ids = [task["task_id"] for task in tasks]
    assignments = []
    for participant_index in range(participant_count):
        participant_id = f"P{participant_index + 1:02d}"
        for order_index in range(len(task_ids)):
            task_index = (order_index + participant_index) % len(task_ids)
            task_id = task_ids[task_index]
            condition = CONDITION_ORDER[(task_index + participant_index) % len(CONDITION_ORDER)]
            assignments.append(
                {
                    "participant_id": participant_id,
                    "order_index": order_index + 1,
                    "task_id": task_id,
                    "condition": condition,
                    "packet_id": f"{task_id}-{condition}",
                }
            )
    return assignments


def write_assignments(path: Path, assignments: list[dict[str, Any]]) -> None:
    fields = ["participant_id", "order_index", "task_id", "condition", "packet_id"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(assignments)


def write_response_template(path: Path, assignments: list[dict[str, Any]]) -> None:
    fields = [
        "participant_id",
        "order_index",
        "packet_id",
        "task_id",
        "condition",
        "response_json",
        "task_time_seconds",
        "confidence",
        "notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for assignment in assignments:
            writer.writerow(
                {
                    "participant_id": assignment["participant_id"],
                    "order_index": assignment["order_index"],
                    "packet_id": assignment["packet_id"],
                    "task_id": assignment["task_id"],
                    "condition": assignment["condition"],
                    "response_json": "{}",
                    "task_time_seconds": "",
                    "confidence": "",
                    "notes": "",
                }
            )


def participant_packets(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    packets = []
    forbidden_views = {
        "agentflame.json",
        "semantic-ablation-r131.json",
        "live-record-r114.json",
        "model-benchmarks-r123.json",
        "user-task-answer-key.csv",
    }
    for item in tasks:
        validate_task_same_slice(item)
        for condition in item["participant_view_conditions"]:
            views = list(condition["views"])
            leaked = sorted(set(views) & forbidden_views)
            if leaked:
                raise AssertionError(
                    f"{item['task_id']} {condition['condition']} exposes oracle-only views: {leaked}"
                )
            view_excerpt = condition.get("view_excerpt", [])
            reject_public_leaks(view_excerpt, f"{item['task_id']}.{condition['condition']}.view_excerpt")
            packets.append(
                {
                    "packet_id": f"{item['task_id']}-{condition['condition']}",
                    "task_id": item["task_id"],
                    "claim": item["claim"],
                    "condition": condition["condition"],
                    "title": public_title(item["task_id"]),
                    "question": item["question"],
                    "views": views,
                    "view_excerpt": view_excerpt,
                }
            )
    return packets


def write_participant_summary(path: Path, packets: list[dict[str, Any]]) -> None:
    lines = [
        "# User Task Participant Packets",
        "",
        "These packets are participant-facing condition assignments. They intentionally omit oracles and answer keys.",
        "",
        "## Packets",
        "",
    ]
    for packet in packets:
        lines.append(
            f"- {packet['packet_id']}: {packet['title']} using {packet['condition']} views."
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(path: Path, bundle: dict[str, Any]) -> None:
    lines = [
        "# User Task Benchmark Bundle",
        "",
        "This bundle defines B4/C5 pilot analysis tasks and answer keys. It is not a human-study result.",
        "",
        f"- Tasks: {len(bundle['tasks'])}.",
        f"- Primary utility tasks: {bundle['primary_utility_task_count']}.",
        f"- Limitation/comprehension tasks: {bundle['limitation_check_task_count']}.",
        f"- Participant packets: {bundle['packet_count']}.",
        f"- Pilot assignment rows: {bundle['assignment_count']}.",
        f"- Conditions: {', '.join(CONDITION_ORDER)}.",
        "",
        "## Tasks",
        "",
    ]
    for item in bundle["tasks"]:
        lines.append(f"- {item['task_id']} ({item['skill']}): {item['title']}.")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- The bundle makes the C5 pilot executable by defining questions, condition packets, assignments, and answer keys.",
            "- `user-task-response-template.csv` defines the response schema consumed by `score_user_task_results.py`.",
            "- Participants should see only their assigned condition packet; oracle sources and answer keys are for graders.",
            "- Every task's five condition excerpts share one `slice_id`; this checks the same-event-slice baseline-fairness requirement for the pilot packet.",
            "- C5 remains unsupported until participant responses are collected and scored.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def source_manifest(agentflame_dir: Path, out_dir: Path) -> list[dict[str, Any]]:
    paths = [
        agentflame_dir / "agentflame.json",
        out_dir / "live-record-r114.json",
        out_dir / "live-record-r114-analysis.json",
        out_dir / "semantic-ablation-r131.json",
        out_dir / "model-benchmarks-r123.json",
    ]
    return [
        {
            "path": rel(path),
            "exists": path.exists(),
            "sha256": sha256_file(path) if path.exists() else None,
        }
        for path in paths
    ]


def script_manifest() -> list[dict[str, Any]]:
    paths = [
        SCRIPT_DIR / "user_task_benchmark.py",
        SCRIPT_DIR / "score_user_task_results.py",
        SCRIPT_DIR / "test_semantic_tag_flamegraph.py",
    ]
    return [
        {
            "path": rel(path),
            "exists": path.exists(),
            "sha256": sha256_file(path) if path.exists() else None,
        }
        for path in paths
    ]


def generated_manifest(out_dir: Path) -> list[dict[str, Any]]:
    names = [
        "user-task-benchmark.json",
        "user-task-answer-key.csv",
        "user-task-participant-packets.json",
        "user-task-participant-packets.md",
        "user-task-assignments.csv",
        "user-task-response-template.csv",
        "user-task-benchmark.md",
    ]
    return [
        {
            "path": rel(out_dir / name),
            "exists": (out_dir / name).exists(),
            "sha256": sha256_file(out_dir / name) if (out_dir / name).exists() else None,
        }
        for name in names
    ]


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out).resolve()
    agentflame_dir = Path(args.agentflame_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    agent_path = agentflame_dir / "agentflame.json"
    r114_path = out_dir / "live-record-r114.json"
    r123_path = out_dir / "model-benchmarks-r123.json"
    r131_path = out_dir / "semantic-ablation-r131.json"
    for path in [agent_path, r114_path, r123_path, r131_path]:
        if not path.exists():
            raise FileNotFoundError(path)

    agent = read_json(agent_path)
    r114 = read_json(r114_path)
    r123 = read_json(r123_path)
    r131 = read_json(r131_path)
    tasks = build_tasks(
        out_dir=out_dir,
        agentflame_dir=agentflame_dir,
        agent=agent,
        r114=r114,
        r123=r123,
        r131=r131,
    )
    packets = participant_packets(tasks)
    assignments = build_assignments(tasks)
    bundle = {
        "schema_version": 2,
        "claim": "C5",
        "run_id": "R142-packet",
        "status": "pilot_packet_ready_no_participants",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_artifacts": source_manifest(agentflame_dir, out_dir),
        "script_artifacts": script_manifest(),
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "command": " ".join(args.command_argv),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
        "condition_order": CONDITION_ORDER,
        "task_count": len(tasks),
        "primary_utility_task_count": len([task for task in tasks if task["analysis_role"] == "primary_utility"]),
        "limitation_check_task_count": len([task for task in tasks if task["analysis_role"] == "limitation_check"]),
        "packet_count": len(packets),
        "assignment_count": len(assignments),
        "participant_protocol": {
            "design": "within-subject counterbalanced assignment across five visualization families",
            "conditions": CONDITION_ORDER,
            "metrics": [
                "exact_answer_accuracy",
                "field_accuracy_pct",
                "task_time_seconds",
                "false_positive_count",
                "confidence",
            ],
            "minimum_pilot_participants": PARTICIPANT_COUNT,
            "paper_run_participants": "12-20",
            "assignment": "P01-P05 seeded rotation; each participant receives one condition per task and each task is covered once per condition across the pilot template",
            "oracle_visibility": "participants see only assigned condition packets; oracle_sources and answer keys are for graders",
            "readiness_boundary": "pilot packet: content leakage, assignment coverage, and same-event-slice checks pass; C5 remains unsupported until scored participant responses exist",
            "claim_gate": "C5 can move beyond unsupported only after scored participant responses exist.",
        },
        "participant_packet_files": [
            "user-task-participant-packets.json",
            "user-task-participant-packets.md",
            "user-task-assignments.csv",
            "user-task-response-template.csv",
        ],
        "tasks": tasks,
    }
    (out_dir / "user-task-benchmark.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    write_answer_key(out_dir / "user-task-answer-key.csv", tasks)
    (out_dir / "user-task-participant-packets.json").write_text(
        json.dumps({"schema_version": 2, "packets": packets}, indent=2),
        encoding="utf-8",
    )
    write_participant_summary(out_dir / "user-task-participant-packets.md", packets)
    write_assignments(out_dir / "user-task-assignments.csv", assignments)
    write_response_template(out_dir / "user-task-response-template.csv", assignments)
    write_summary(out_dir / "user-task-benchmark.md", bundle)
    manifest = {
        "schema_version": 1,
        "run_id": bundle["run_id"],
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "generated_artifacts": generated_manifest(out_dir),
    }
    (out_dir / "user-task-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"tasks": len(tasks), "packets": len(packets), "out": str(out_dir)}, indent=2))
    return bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--agentflame-dir", default=str(DEFAULT_AGENTFLAME_DIR))
    return parser


if __name__ == "__main__":
    import sys

    parsed = build_parser().parse_args()
    parsed.command_argv = sys.argv
    run(parsed)
