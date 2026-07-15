#!/usr/bin/env python3
"""Run the reviewed R315 fixed-reader prioritization experiment.

Collection reads only visible R315 packets. Scoring is a separate command that
loads the existing hidden key after every model response has been collected.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


FORBIDDEN_MODEL_KEYS = {
    "packet_id",
    "view",
    "ranker",
    "response_prompt",
    "rank",
    "group_id",
    "alias_to_group_id",
    "looping",
    "side_effect",
    "safety",
    "step_correct",
    "step_redundant",
    "human_group",
    "group_pattern",
    "group_position",
    "positive_operations",
    "positive_rate",
    "positive_recall",
    "positive_precision",
    "positive_lift",
}

ALLOWED_GROUP_FIELDS = (
    "operations",
    "sessions",
    "stack",
    "stack_frames",
    "visible_features",
    "field_examples",
    "operation_examples",
    "session_examples",
)

SCORE_METRICS = (
    "positive_recall",
    "positive_precision",
    "work_fraction",
    "positive_lift",
    "positive_hit",
    "high_lift_hit",
)


class ExperimentError(RuntimeError):
    """An execution or scoring defect that invalidates the planned run."""


class RetryableResponseError(RuntimeError):
    """One transport or response-schema attempt failed."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ExperimentError(f"{path}:{line_number}: expected JSON object")
            rows.append(value)
    return rows


def append_jsonl(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(dict(value)) + "\n")
        handle.flush()


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_keys(child)


def validate_visible_source(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("visible_only") is not True:
        raise ExperimentError("visible packet input must declare visible_only=true")
    cases = value.get("cases")
    if not isinstance(cases, list) or len(cases) != 18:
        raise ExperimentError("visible packet input must contain exactly 18 cases")
    packet_ids = [case.get("packet_id") for case in cases if isinstance(case, dict)]
    if len(packet_ids) != 18 or len(set(packet_ids)) != 18:
        raise ExperimentError("visible packet IDs must be 18 unique strings")
    return value


def visible_group(group: Mapping[str, Any], alias: str) -> dict[str, Any]:
    output: dict[str, Any] = {"alias": alias}
    for field in ALLOWED_GROUP_FIELDS:
        if field in group:
            output[field] = group[field]
    forbidden = sorted(set(walk_keys(output)) & FORBIDDEN_MODEL_KEYS)
    if forbidden:
        raise ExperimentError(f"visible group retained forbidden keys: {forbidden}")
    return output


def build_messages(problem: str, groups: Sequence[Mapping[str, Any]], budget: int) -> list[dict[str, str]]:
    visible_input = {
        "target_problem": problem,
        "selection_budget": budget,
        "visible_groups": list(groups),
    }
    system = (
        "You diagnose one agent-profile packet using only the visible evidence supplied. "
        "Choose the groups most likely to contain the target phenomenon. Do not assume "
        "unshown labels or metadata. Return only one JSON object with exactly two keys: "
        "selected_group_aliases and visible_evidence. selected_group_aliases must contain "
        f"exactly {budget} distinct aliases ordered from most to least useful. "
        "visible_evidence must be a non-empty array of short strings grounded in visible fields."
    )
    user = "Visible diagnostic packet:\n" + json.dumps(
        visible_input, ensure_ascii=False, sort_keys=True
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_presentations(
    visible: Mapping[str, Any],
    packet_filter: str | None,
    order_scheme: str,
    model: str,
    temperature: float,
    seed: int,
    max_tokens: int,
) -> list[dict[str, Any]]:
    if order_scheme != "cyclic-5":
        raise ExperimentError("only the reviewed cyclic-5 order scheme is supported")
    presentations: list[dict[str, Any]] = []
    selected_cases = [
        case
        for case in visible["cases"]
        if packet_filter is None or case.get("packet_id") == packet_filter
    ]
    if packet_filter is not None and len(selected_cases) != 1:
        raise ExperimentError(f"packet filter {packet_filter!r} did not select exactly one case")

    for case in sorted(selected_cases, key=lambda row: str(row["packet_id"])):
        groups = case.get("groups")
        if not isinstance(groups, list) or len(groups) not in {1, 5}:
            raise ExperimentError(f"{case['packet_id']}: expected one or five visible groups")
        if not isinstance(case.get("problem"), str) or not case["problem"].strip():
            raise ExperimentError(f"{case['packet_id']}: missing visible problem statement")
        group_ids = [group.get("group_id") for group in groups if isinstance(group, dict)]
        if len(group_ids) != len(groups) or any(not isinstance(item, str) for item in group_ids):
            raise ExperimentError(f"{case['packet_id']}: invalid group IDs")
        if len(set(group_ids)) != len(group_ids):
            raise ExperimentError(f"{case['packet_id']}: duplicate group IDs")
        base = sorted(groups, key=lambda group: str(group["group_id"]))
        rotations = range(5) if len(base) == 5 else range(1)

        for rotation in rotations:
            ordered = base[rotation:] + base[:rotation]
            aliases = [f"G{index:02d}" for index in range(1, len(ordered) + 1)]
            alias_map = {
                alias: str(group["group_id"])
                for alias, group in zip(aliases, ordered, strict=True)
            }
            model_groups = [
                visible_group(group, alias)
                for alias, group in zip(aliases, ordered, strict=True)
            ]
            budget = 1 if len(model_groups) == 1 else 3
            messages = build_messages(case["problem"], model_groups, budget)
            request = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "top_p": 1.0,
                "max_tokens": max_tokens,
                "seed": seed,
                "stream": False,
                "reasoning_format": "none",
                "chat_template_kwargs": {"enable_thinking": False},
            }
            request_text = canonical_json(request)
            leaked_ids = sorted(group_id for group_id in group_ids if group_id in request_text)
            if leaked_ids:
                raise ExperimentError(
                    f"{case['packet_id']} rotation {rotation}: request leaked original IDs {leaked_ids}"
                )
            body_keys = set(walk_keys({"problem": case["problem"], "groups": model_groups}))
            forbidden = sorted(body_keys & FORBIDDEN_MODEL_KEYS)
            if forbidden:
                raise ExperimentError(
                    f"{case['packet_id']} rotation {rotation}: request leaked keys {forbidden}"
                )
            presentations.append(
                {
                    "presentation_id": f"{case['packet_id']}#rotation-{rotation}",
                    "packet_id": case["packet_id"],
                    "task": case["task"],
                    "dataset": case["dataset"],
                    "view": case["view"],
                    "rotation": rotation,
                    "selection_budget": budget,
                    "base_group_ids": [str(group["group_id"]) for group in base],
                    "alias_to_group_id": alias_map,
                    "request": request,
                }
            )
    return presentations


def get_json(url: str, timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "AgentProf-R315-Reader/2"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            value = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise ExperimentError(f"failed to read {url}: {error}") from error
    if not isinstance(value, dict):
        raise ExperimentError(f"{url}: expected JSON object")
    return value


def post_json(url: str, body: Mapping[str, Any], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=canonical_json(dict(body)).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "AgentProf-R315-Reader/2"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            value = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RetryableResponseError(f"HTTP {error.code}: {detail}") from error
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RetryableResponseError(f"request failed: {error}") from error
    if not isinstance(value, dict):
        raise RetryableResponseError("chat endpoint returned a non-object")
    return value


def assistant_content(response: Mapping[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise RetryableResponseError("response omitted choices[0]")
    message = choices[0].get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise RetryableResponseError("response omitted assistant content")
    return content


def parse_json_object(text: str) -> dict[str, Any]:
    candidates = [text.strip()]
    if "```" in text:
        pieces = text.split("```")
        candidates.extend(piece.removeprefix("json").strip() for piece in pieces[1::2])
    decoder = json.JSONDecoder()
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            start = candidate.find("{")
            if start < 0:
                continue
            try:
                value, _ = decoder.raw_decode(candidate[start:])
            except json.JSONDecodeError:
                continue
        if isinstance(value, dict):
            return value
    raise RetryableResponseError("assistant content contained no JSON object")


def parse_selection(content: str, aliases: set[str], budget: int) -> dict[str, Any]:
    value = parse_json_object(content)
    if set(value) != {"selected_group_aliases", "visible_evidence"}:
        raise RetryableResponseError("response must contain exactly the two reviewed keys")
    selected = value["selected_group_aliases"]
    evidence = value["visible_evidence"]
    if not isinstance(selected, list) or len(selected) != budget:
        raise RetryableResponseError(f"response must select exactly {budget} aliases")
    if any(not isinstance(alias, str) or alias not in aliases for alias in selected):
        raise RetryableResponseError("response selected an alias outside the packet")
    if len(set(selected)) != len(selected):
        raise RetryableResponseError("response selected duplicate aliases")
    if not isinstance(evidence, list) or not evidence or any(
        not isinstance(item, str) or not item.strip() for item in evidence
    ):
        raise RetryableResponseError("visible_evidence must be a non-empty string array")
    return {
        "selected_group_aliases": selected,
        "visible_evidence": [item.strip() for item in evidence],
    }


def validate_model(models: Mapping[str, Any], requested: str) -> None:
    identifiers: set[str] = set()
    for key in ("models", "data"):
        rows = models.get(key)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            for field in ("id", "name", "model"):
                if isinstance(row.get(field), str):
                    identifiers.add(row[field])
    if requested not in identifiers:
        raise ExperimentError(
            f"requested model {requested!r} absent from /models identifiers {sorted(identifiers)}"
        )


def collect_one(
    presentation: Mapping[str, Any],
    base_url: str,
    timeout: float,
    attempts: int,
) -> dict[str, Any]:
    errors: list[str] = []
    raw_attempts: list[dict[str, Any]] = []
    aliases = set(presentation["alias_to_group_id"])
    for attempt in range(1, attempts + 1):
        try:
            response = post_json(
                base_url.rstrip("/") + "/chat/completions",
                presentation["request"],
                timeout,
            )
            content = assistant_content(response)
            parsed = parse_selection(content, aliases, int(presentation["selection_budget"]))
            selected_ids = [
                presentation["alias_to_group_id"][alias]
                for alias in parsed["selected_group_aliases"]
            ]
            raw_attempts.append(
                {"attempt": attempt, "success": True, "response": response, "content": content}
            )
            return {
                **dict(presentation),
                "status": "success",
                "attempt_count": attempt,
                "errors": errors,
                "attempts": raw_attempts,
                "selected_group_aliases": parsed["selected_group_aliases"],
                "selected_group_ids": selected_ids,
                "visible_evidence": parsed["visible_evidence"],
            }
        except (RetryableResponseError, OSError) as error:
            errors.append(str(error))
            raw_attempts.append({"attempt": attempt, "success": False, "error": str(error)})
    return {
        **dict(presentation),
        "status": "failed",
        "attempt_count": attempts,
        "errors": errors,
        "attempts": raw_attempts,
        "selected_group_aliases": [],
        "selected_group_ids": [],
        "visible_evidence": [],
    }


def run_collect(args: argparse.Namespace) -> None:
    visible = validate_visible_source(load_json(args.visible_packets))
    if args.attempts < 1:
        raise ExperimentError("--attempts must be positive")
    models = get_json(args.base_url.rstrip("/") + "/models", args.timeout)
    validate_model(models, args.model)
    presentations = build_presentations(
        visible,
        args.packet_id,
        args.order_scheme,
        args.model,
        args.temperature,
        args.seed,
        args.max_tokens,
    )
    expected = 5 if args.packet_id else 66
    if len(presentations) != expected:
        raise ExperimentError(f"planned collection expected {expected} presentations, got {len(presentations)}")

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    responses_path = out_dir / "responses.jsonl"
    existing_rows = read_jsonl(responses_path)
    existing: dict[str, dict[str, Any]] = {}
    for row in existing_rows:
        presentation_id = row.get("presentation_id")
        if not isinstance(presentation_id, str) or presentation_id in existing:
            raise ExperimentError("existing response file has invalid or duplicate presentation IDs")
        existing[presentation_id] = row

    completed = 0
    started = time.time()
    for index, presentation in enumerate(presentations, start=1):
        presentation_id = presentation["presentation_id"]
        old = existing.get(presentation_id)
        if old is not None:
            if old.get("status") != "success" or old.get("request") != presentation["request"]:
                raise ExperimentError(f"stale or failed existing record for {presentation_id}")
            completed += 1
            print(f"[{index}/{len(presentations)}] resume {presentation_id}", flush=True)
            continue
        print(f"[{index}/{len(presentations)}] collect {presentation_id}", flush=True)
        record = collect_one(presentation, args.base_url, args.timeout, args.attempts)
        append_jsonl(responses_path, record)
        if record["status"] != "success":
            write_json(
                out_dir / "collection-summary.json",
                {
                    "status": "invalid",
                    "planned_presentations": len(presentations),
                    "completed_presentations": completed,
                    "failed_presentation": presentation_id,
                    "model": args.model,
                    "order_scheme": args.order_scheme,
                    "responses": str(responses_path),
                },
            )
            raise ExperimentError(f"{presentation_id} failed after {args.attempts} attempts")
        completed += 1

    summary = {
        "status": "complete",
        "planned_presentations": len(presentations),
        "completed_presentations": completed,
        "unique_packets": len({row["packet_id"] for row in presentations}),
        "tasks": len({row["task"] for row in presentations}),
        "views": sorted({row["view"] for row in presentations}),
        "model": args.model,
        "base_url": args.base_url,
        "order_scheme": args.order_scheme,
        "temperature": args.temperature,
        "seed": args.seed,
        "max_tokens": args.max_tokens,
        "attempt_limit": args.attempts,
        "elapsed_seconds": time.time() - started,
        "responses": str(responses_path),
        "model_metadata": models,
    }
    write_json(out_dir / "collection-summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


def validate_hidden_source(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("hidden") is not True:
        raise ExperimentError("hidden scoring input must declare hidden=true")
    cases = value.get("cases")
    if not isinstance(cases, list) or len(cases) != 18:
        raise ExperimentError("hidden scoring input must contain exactly 18 cases")
    return value


def task_totals(hidden_cases: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, float]]:
    totals: dict[str, dict[str, float]] = {}
    for case in hidden_cases:
        if case.get("view") != "flat":
            continue
        groups = case.get("groups")
        if not isinstance(groups, list) or len(groups) != 1:
            raise ExperimentError(f"{case.get('packet_id')}: flat key must have one group")
        group = groups[0]
        operations = float(group["operations"])
        positives = float(group["positive_operations"])
        totals[str(case["task"])] = {
            "operations": operations,
            "positives": positives,
            "prevalence": positives / operations if operations else 0.0,
        }
    if len(totals) != 6:
        raise ExperimentError(f"expected totals for six tasks, got {len(totals)}")
    return totals


def score_record(
    response: Mapping[str, Any],
    hidden_case: Mapping[str, Any],
    totals: Mapping[str, Mapping[str, float]],
    high_lift_threshold: float,
) -> dict[str, Any]:
    hidden_groups = {str(group["group_id"]): group for group in hidden_case["groups"]}
    selected = response.get("selected_group_ids")
    if not isinstance(selected, list) or len(selected) != int(response["selection_budget"]):
        raise ExperimentError(f"{response['presentation_id']}: invalid selected IDs")
    if any(group_id not in hidden_groups for group_id in selected):
        raise ExperimentError(f"{response['presentation_id']}: selected ID absent from hidden key")
    selected_groups = [hidden_groups[group_id] for group_id in selected]
    task_total = totals[str(response["task"])]
    operations = sum(float(group["operations"]) for group in selected_groups)
    positives = sum(float(group["positive_operations"]) for group in selected_groups)
    precision = positives / operations if operations else 0.0
    recall = positives / task_total["positives"] if task_total["positives"] else 0.0
    work = operations / task_total["operations"] if task_total["operations"] else 0.0
    lift = precision / task_total["prevalence"] if task_total["prevalence"] else 0.0
    group_lifts = [
        float(group["positive_rate"]) / task_total["prevalence"]
        if task_total["prevalence"]
        else 0.0
        for group in selected_groups
    ]
    return {
        "presentation_id": response["presentation_id"],
        "packet_id": response["packet_id"],
        "task": response["task"],
        "dataset": response["dataset"],
        "view": response["view"],
        "rotation": response["rotation"],
        "selected_group_ids": ";".join(str(item) for item in selected),
        "selected_groups": len(selected),
        "selected_operations": operations,
        "selected_positive_operations": positives,
        "positive_recall": recall,
        "positive_precision": precision,
        "work_fraction": work,
        "positive_lift": lift,
        "positive_hit": positives > 0,
        "high_lift_hit": any(
            float(group["positive_operations"]) > 0 and group_lift >= high_lift_threshold
            for group, group_lift in zip(selected_groups, group_lifts, strict=True)
        ),
    }


def mean(values: Sequence[float]) -> float:
    return float(statistics.mean(values))


def aggregate_task_views(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["task"]), str(row["view"]))].append(row)
    output: list[dict[str, Any]] = []
    for (task, view), items in sorted(grouped.items()):
        expected = 1 if view == "flat" else 5
        if len(items) != expected:
            raise ExperimentError(f"{task}/{view}: expected {expected} presentations, got {len(items)}")
        output.append(
            {
                "task": task,
                "dataset": items[0]["dataset"],
                "view": view,
                "presentations": len(items),
                **{
                    metric: mean([float(item[metric]) for item in items])
                    for metric in SCORE_METRICS
                },
            }
        )
    if len(output) != 18:
        raise ExperimentError(f"expected 18 task/view aggregates, got {len(output)}")
    return output


def compare_task_views(rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    indexed = {(str(row["task"]), str(row["view"])): row for row in rows}
    tasks = sorted({str(row["task"]) for row in rows})
    paired: list[dict[str, Any]] = []
    for task in tasks:
        proposed = indexed[(task, "operation_stack")]
        baseline = indexed[(task, "fixed_session")]
        paired.append(
            {
                "task": task,
                "dataset": proposed["dataset"],
                **{
                    f"operation_stack_{metric}": float(proposed[metric])
                    for metric in SCORE_METRICS
                },
                **{
                    f"fixed_session_{metric}": float(baseline[metric])
                    for metric in SCORE_METRICS
                },
                **{
                    f"delta_{metric}": float(proposed[metric]) - float(baseline[metric])
                    for metric in SCORE_METRICS
                },
            }
        )
    if len(paired) != 6:
        raise ExperimentError(f"expected six paired tasks, got {len(paired)}")

    metrics: dict[str, Any] = {}
    for metric in SCORE_METRICS:
        deltas = [float(row[f"delta_{metric}"]) for row in paired]
        metrics[metric] = {
            "task_deltas": {row["task"]: row[f"delta_{metric}"] for row in paired},
            "median_delta": float(statistics.median(deltas)),
            "mean_delta": mean(deltas),
            "improved_tasks": sum(delta > 0 for delta in deltas),
            "tied_tasks": sum(delta == 0 for delta in deltas),
            "worse_tasks": sum(delta < 0 for delta in deltas),
        }
    for metric in ("positive_recall", "positive_precision"):
        item = metrics[metric]
        item["passes"] = item["median_delta"] > 0 and item["improved_tasks"] >= 4
    passed = sum(bool(metrics[metric]["passes"]) for metric in ("positive_recall", "positive_precision"))
    verdict = "supported" if passed == 2 else "mixed" if passed == 1 else "contradicted"
    return paired, {"verdict": verdict, "metrics": metrics}


def bool_text(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


def deduplicate_ranker(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("top_k") == "3"]
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["packet_id"]].append(row)
    if len(grouped) != 18:
        raise ExperimentError(f"R316 control expected 18 packets, got {len(grouped)}")
    compare_fields = (
        "task",
        "dataset",
        "view",
        "positive_hit",
        "high_lift_hit",
        "positive_recall",
        "work_fraction",
        "positive_lift",
        "positive_precision",
        "selected_groups",
        "selected_operations",
        "selected_positive_operations",
    )
    output: list[dict[str, Any]] = []
    for packet_id, items in sorted(grouped.items()):
        reference = {field: items[0][field] for field in compare_fields}
        if any({field: item[field] for field in compare_fields} != reference for item in items[1:]):
            raise ExperimentError(f"R316 repeated rows disagree for {packet_id}")
        output.append(
            {
                "packet_id": packet_id,
                "task": reference["task"],
                "dataset": reference["dataset"],
                "view": reference["view"],
                "assignment_repetitions": len(items),
                "positive_hit": bool_text(reference["positive_hit"]),
                "high_lift_hit": bool_text(reference["high_lift_hit"]),
                **{
                    field: float(reference[field])
                    for field in (
                        "positive_recall",
                        "work_fraction",
                        "positive_lift",
                        "positive_precision",
                        "selected_groups",
                        "selected_operations",
                        "selected_positive_operations",
                    )
                },
            }
        )
    return output


def write_result_report(path: Path, summary: Mapping[str, Any], paired: Sequence[Mapping[str, Any]]) -> None:
    metrics = summary["paired_comparison"]["metrics"]
    lines = [
        "# R315 Fixed-Reader Result",
        "",
        f"- Run status: **{summary['run_status'].upper()}**",
        f"- Tested hypothesis: **{summary['tested_hypothesis'].upper()}**",
        "- Selected RQ: **RQ2 — Does profiler output correspond to real problems?**",
        f"- Presentations: {summary['presentations']} over {summary['unique_packets']} unique packets and {summary['tasks']} paired tasks.",
        "",
        "## Registered Primary Comparison",
        "",
        "| Metric | Median delta | Improved / tied / worse tasks | Pass |",
        "|---|---:|---:|---|",
    ]
    for metric in ("positive_recall", "positive_precision"):
        item = metrics[metric]
        lines.append(
            f"| {metric} | {item['median_delta']:.6f} | "
            f"{item['improved_tasks']} / {item['tied_tasks']} / {item['worse_tasks']} | "
            f"{item['passes']} |"
        )
    lines.extend(
        [
            "",
            "## Task Rows",
            "",
            "| Task | Recall: stack / session / delta | Precision: stack / session / delta | Work: stack / session / delta |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in paired:
        lines.append(
            f"| {row['task']} | {row['operation_stack_positive_recall']:.4f} / "
            f"{row['fixed_session_positive_recall']:.4f} / {row['delta_positive_recall']:+.4f} | "
            f"{row['operation_stack_positive_precision']:.4f} / "
            f"{row['fixed_session_positive_precision']:.4f} / {row['delta_positive_precision']:+.4f} | "
            f"{row['operation_stack_work_fraction']:.4f} / "
            f"{row['fixed_session_work_fraction']:.4f} / {row['delta_work_fraction']:+.4f} |"
        )
    lines.extend(
        [
            "",
            "## Scope",
            "",
            "This result covers one deterministic Qwen3.6-27B reader, six tasks, existing top-five R315 packets, and a fixed three-group selection budget. It is not a human study and does not establish human productivity, remediation, raw-action superiority, cross-model generality, or universal view dominance.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_score(args: argparse.Namespace) -> None:
    visible = validate_visible_source(load_json(args.visible_packets))
    hidden = validate_hidden_source(load_json(args.hidden_key))
    visible_by_packet = {case["packet_id"]: case for case in visible["cases"]}
    hidden_by_packet = {case["packet_id"]: case for case in hidden["cases"]}
    if set(visible_by_packet) != set(hidden_by_packet):
        raise ExperimentError("visible and hidden packet IDs differ")
    for packet_id in visible_by_packet:
        visible_ids = {group["group_id"] for group in visible_by_packet[packet_id]["groups"]}
        hidden_ids = {group["group_id"] for group in hidden_by_packet[packet_id]["groups"]}
        if visible_ids != hidden_ids:
            raise ExperimentError(f"{packet_id}: visible and hidden group IDs differ")

    responses = read_jsonl(args.responses)
    if len(responses) != 66 or any(row.get("status") != "success" for row in responses):
        raise ExperimentError("scoring requires exactly 66 successful response records")
    if len({row.get("presentation_id") for row in responses}) != 66:
        raise ExperimentError("response presentation IDs are not unique")
    totals = task_totals(hidden["cases"])
    presentation_rows = [
        score_record(row, hidden_by_packet[row["packet_id"]], totals, args.high_lift_threshold)
        for row in responses
    ]
    task_view_rows = aggregate_task_views(presentation_rows)
    paired_rows, paired_summary = compare_task_views(task_view_rows)
    ranker_rows = deduplicate_ranker(args.ranker_scores)

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    presentation_fields = (
        "presentation_id",
        "packet_id",
        "task",
        "dataset",
        "view",
        "rotation",
        "selected_group_ids",
        "selected_groups",
        "selected_operations",
        "selected_positive_operations",
        *SCORE_METRICS,
    )
    task_view_fields = ("task", "dataset", "view", "presentations", *SCORE_METRICS)
    paired_fields = tuple(paired_rows[0])
    ranker_fields = tuple(ranker_rows[0])
    write_csv(out_dir / "presentation-scores.csv", presentation_rows, presentation_fields)
    write_csv(out_dir / "task-view-scores.csv", task_view_rows, task_view_fields)
    write_csv(out_dir / "paired-task-comparison.csv", paired_rows, paired_fields)
    write_csv(out_dir / "ranker-control.csv", ranker_rows, ranker_fields)

    summary = {
        "run_status": "valid",
        "tested_hypothesis": paired_summary["verdict"],
        "research_value": "pending independent review",
        "paper_impact": "additional RQ2 evidence",
        "presentations": len(responses),
        "unique_packets": len({row["packet_id"] for row in responses}),
        "tasks": len({row["task"] for row in responses}),
        "views": sorted({row["view"] for row in responses}),
        "order_scheme": "cyclic-5",
        "high_lift_threshold": args.high_lift_threshold,
        "paired_comparison": paired_summary,
        "outputs": {
            "presentation_scores": str(out_dir / "presentation-scores.csv"),
            "task_view_scores": str(out_dir / "task-view-scores.csv"),
            "paired_task_comparison": str(out_dir / "paired-task-comparison.csv"),
            "ranker_control": str(out_dir / "ranker-control.csv"),
            "result_report": str(out_dir / "result-report.md"),
        },
    }
    write_json(out_dir / "summary.json", summary)
    write_result_report(out_dir / "result-report.md", summary, paired_rows)
    print(json.dumps(summary, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)

    collect = subparsers.add_parser("collect", help="collect rank-hidden reader responses")
    collect.add_argument("--visible-packets", type=Path, required=True)
    collect.add_argument("--base-url", required=True)
    collect.add_argument("--model", required=True)
    collect.add_argument("--out-dir", type=Path, required=True)
    collect.add_argument("--packet-id")
    collect.add_argument("--order-scheme", choices=["cyclic-5"], required=True)
    collect.add_argument("--temperature", type=float, required=True)
    collect.add_argument("--seed", type=int, required=True)
    collect.add_argument("--max-tokens", type=int, required=True)
    collect.add_argument("--attempts", type=int, required=True)
    collect.add_argument("--timeout", type=float, default=600.0)

    score = subparsers.add_parser("score", help="score completed responses against hidden key")
    score.add_argument("--visible-packets", type=Path, required=True)
    score.add_argument("--hidden-key", type=Path, required=True)
    score.add_argument("--ranker-scores", type=Path, required=True)
    score.add_argument("--responses", type=Path, required=True)
    score.add_argument("--out-dir", type=Path, required=True)
    score.add_argument("--high-lift-threshold", type=float, default=1.5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        if args.mode == "collect":
            run_collect(args)
        else:
            run_score(args)
    except (ExperimentError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
