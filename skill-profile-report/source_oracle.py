#!/usr/bin/env python3
"""Independent raw-source census for one frozen Claude JSONL snapshot."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

MAX_REPORTED_TOKEN_COMPONENT = 10_000_000
MAX_ESTIMATED_TOKEN_COMPONENT = 2_000_000


def clean_prompt(text: str) -> str:
    normalized = " ".join(text.split())
    if normalized.startswith("<session>") and normalized.endswith("</session>"):
        normalized = normalized[len("<session>") : -len("</session>")].strip()
    return normalized


def compact_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                kind = item.get("type", "")
                if kind in {"tool_result", "tool_use", "function_call"}:
                    continue
                if kind == "thinking" and item.get("thinking"):
                    parts.append(str(item["thinking"]))
                elif isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("content"), str):
                    parts.append(item["content"])
        return "\n".join(parts)
    if isinstance(value, dict):
        for key in ("text", "content"):
            if isinstance(value.get(key), str):
                return value[key]
    return ""


def collect_local_text(value: Any, output: list[str]) -> None:
    if isinstance(value, str):
        output.append(value)
    elif isinstance(value, list):
        for item in value:
            collect_local_text(item, output)
    elif isinstance(value, dict):
        if value.get("type") in {"tool_use", "function_call", "tool_result"}:
            return
        for key in ("text", "content", "message", "input", "prompt"):
            if key in value:
                collect_local_text(value[key], output)


def local_message_preview(value: Any) -> str:
    parts: list[str] = []
    collect_local_text(value, parts)
    return clean_prompt(" ".join(parts))


def is_tool_result(obj: dict[str, Any], content: Any) -> bool:
    if "toolUseResult" in obj or "tool_use_result" in obj:
        return True
    return isinstance(content, list) and any(
        isinstance(item, dict) and item.get("type") == "tool_result"
        for item in content
    )


def starts_prompt(
    obj: dict[str, Any],
    content: Any,
    text: str,
    active_prompt_id: str | None,
) -> bool:
    if (
        obj.get("isMeta") is True
        or "sourceToolUseID" in obj
        or "sourceToolAssistantUUID" in obj
        or any(
            key in obj for key in ("attachment", "attachments", "image", "images")
        )
        or (
            isinstance(content, list)
            and bool(content)
            and all(
                isinstance(item, dict)
                and item.get("type")
                in {"attachment", "document", "file", "image"}
                for item in content
            )
        )
        or text.startswith(
            (
                "<local-command-caveat>",
                "<local-command-stdout>",
                "<system-reminder>",
                "<ide_opened_file>",
                "<ide_selection>",
            )
        )
    ):
        return False
    prompt_id = obj.get("promptId")
    if isinstance(prompt_id, str) and prompt_id:
        return active_prompt_id != prompt_id
    return active_prompt_id is None


def timestamp_ms(value: Any) -> int | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return int(parsed.timestamp() * 1000)


def short_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:12]


def add_prompt(
    prompts: list[tuple[str, int | None]], text: str, timestamp: int | None
) -> int:
    normalized = clean_prompt(text)
    if not normalized:
        return max(len(prompts) - 1, 0)
    digest = short_hash(normalized)
    for index in range(len(prompts) - 1, -1, -1):
        previous_hash, previous_timestamp = prompts[index]
        same_time = (
            previous_timestamp is not None
            and timestamp is not None
            and abs(previous_timestamp - timestamp) <= 1000
        ) or (
            previous_timestamp is None
            and timestamp is None
            and index == len(prompts) - 1
        )
        if previous_hash == digest and same_time:
            return index
    prompts.append((digest, timestamp))
    return len(prompts) - 1


def token_mass(response: dict[str, int]) -> int:
    components = [
        response["input"],
        response["output"],
        response["cache"],
    ]
    accepted = [
        value
        for value in components
        if 1 <= value <= MAX_REPORTED_TOKEN_COMPONENT
    ]
    if accepted:
        return sum(accepted)
    total = response["total"]
    if 1 <= total <= MAX_ESTIMATED_TOKEN_COMPONENT:
        return total
    return 1


def parse_file(path: Path) -> dict[str, Any]:
    prompts: list[tuple[str, int | None]] = []
    tools = 0
    prompt_preview = ""
    active_prompt_id: str | None = None
    current_prompt_index = 0
    model_present = False
    exact_skills: list[str] = []
    cwd = ""
    valid_rows = 0
    invalid_rows = 0
    llm_rows = 0
    missing_source_id_rows = 0
    responses: list[dict[str, Any]] = []
    by_source: dict[tuple[int, str], int] = {}
    result_model_usage: dict[str, dict[str, int]] = {}
    assistant_model_usage: dict[str, dict[str, int]] = {}
    seen_usage_ids: set[str] = set()

    try:
        lines = path.read_text(errors="strict").splitlines()
    except (OSError, UnicodeError):
        return {"readable": False}

    for line in lines:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            invalid_rows += 1
            continue
        if not isinstance(obj, dict):
            continue
        valid_rows += 1
        if not cwd and isinstance(obj.get("cwd"), str) and obj["cwd"]:
            cwd = obj["cwd"]
        kind = obj.get("type", "")
        message = obj.get("message")
        if not isinstance(message, dict):
            message = {}

        if kind == "result":
            model_usage = obj.get("modelUsage")
            if isinstance(model_usage, dict):
                for model, usage in model_usage.items():
                    if not isinstance(usage, dict):
                        continue
                    result_model_usage.setdefault(
                        str(model),
                        {"input": 0, "output": 0, "cache": 0, "total": 0},
                    )
                    target = result_model_usage[str(model)]
                    values = {
                        "input": int(usage.get("inputTokens", 0) or 0),
                        "output": int(usage.get("outputTokens", 0) or 0),
                        "cache": int(
                            (usage.get("cacheCreationInputTokens", 0) or 0)
                            + (usage.get("cacheReadInputTokens", 0) or 0)
                        ),
                    }
                    for field, value in values.items():
                        target[field] += value
                    target["total"] += sum(values.values())
            continue

        if kind == "assistant":
            if isinstance(message.get("model"), str):
                model_present = True
            usage = message.get("usage")
            if not isinstance(usage, dict):
                usage = {}
            source_id = (
                message.get("id") or obj.get("requestId") or obj.get("uuid") or ""
            )
            usage_id = source_id or obj.get("uuid") or "usage"
            if usage and usage_id not in seen_usage_ids:
                seen_usage_ids.add(str(usage_id))
                model = str(message.get("model") or "unknown")
                target = assistant_model_usage.setdefault(
                    model, {"input": 0, "output": 0, "cache": 0, "total": 0}
                )
                values = {
                    "input": int(usage.get("input_tokens", 0) or 0),
                    "output": int(usage.get("output_tokens", 0) or 0),
                    "cache": int(
                        (usage.get("cache_creation_input_tokens", 0) or 0)
                        + (usage.get("cache_read_input_tokens", 0) or 0)
                    ),
                }
                for field, value in values.items():
                    target[field] += value
                target["total"] += sum(values.values())

            content = message.get("content")
            if isinstance(content, list):
                for item in content:
                    if not isinstance(item, dict) or item.get("type") != "tool_use":
                        continue
                    tools += 1
                    if item.get("name") == "Skill":
                        skill_input = item.get("input")
                        skill = (
                            skill_input.get("skill")
                            if isinstance(skill_input, dict)
                            else None
                        )
                        if isinstance(skill, str) and skill.strip():
                            exact_skills.append(skill.strip())

            text = compact_text(content)
            if text.strip() or usage:
                llm_rows += 1
                if not source_id:
                    missing_source_id_rows += 1
                response = {
                    "prompt_index": current_prompt_index,
                    "source_id": str(source_id),
                    "text_hash": short_hash(
                        text
                        + json.dumps(
                            usage, separators=(",", ":"), ensure_ascii=False
                        )
                    ),
                    "timestamp": timestamp_ms(obj.get("timestamp")),
                    "input": int(usage.get("input_tokens", 0) or 0),
                    "output": int(usage.get("output_tokens", 0) or 0),
                    "cache": int(
                        (usage.get("cache_creation_input_tokens", 0) or 0)
                        + (usage.get("cache_read_input_tokens", 0) or 0)
                    ),
                    "total": 0,
                }
                duplicate_index: int | None = None
                if source_id:
                    duplicate_index = by_source.get(
                        (current_prompt_index, str(source_id))
                    )
                elif responses:
                    previous = responses[-1]
                    if (
                        not previous["source_id"]
                        and previous["prompt_index"] == current_prompt_index
                        and previous["text_hash"] == response["text_hash"]
                        and previous["timestamp"] is not None
                        and response["timestamp"] is not None
                        and abs(previous["timestamp"] - response["timestamp"]) <= 1000
                    ):
                        duplicate_index = len(responses) - 1
                if duplicate_index is None:
                    if source_id:
                        by_source[(current_prompt_index, str(source_id))] = len(
                            responses
                        )
                    responses.append(response)
                else:
                    previous = responses[duplicate_index]
                    for field in ("input", "output", "cache", "total"):
                        previous[field] = max(previous[field], response[field])
            continue

        if kind == "queue-operation" and not prompt_preview:
            if obj.get("operation") == "enqueue" and isinstance(obj.get("content"), str):
                text = clean_prompt(obj["content"])
                if text:
                    prompt_preview = text
                    current_prompt_index = add_prompt(
                        prompts, text, timestamp_ms(obj.get("timestamp"))
                    )
            continue

        if kind == "last-prompt" and not prompt_preview:
            if isinstance(obj.get("lastPrompt"), str):
                text = clean_prompt(obj["lastPrompt"])
                if text:
                    prompt_preview = text
                    current_prompt_index = add_prompt(
                        prompts, text, timestamp_ms(obj.get("timestamp"))
                    )
            continue

        if kind == "user":
            content = message.get("content")
            if is_tool_result(obj, content):
                continue
            text = local_message_preview(content)
            if text and starts_prompt(obj, content, text, active_prompt_id):
                prompt_preview = prompt_preview or text
                prompt_id = obj.get("promptId")
                active_prompt_id = (
                    prompt_id
                    if isinstance(prompt_id, str) and prompt_id
                    else None
                )
                current_prompt_index = add_prompt(
                    prompts, text, timestamp_ms(obj.get("timestamp"))
                )

    model_usage = result_model_usage or assistant_model_usage
    model_token_total = sum(usage["total"] for usage in model_usage.values())
    parseable = bool(
        model_token_total or tools or prompt_preview or model_present
    )
    if not parseable:
        return {
            "readable": True,
            "parseable": False,
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
        }

    if not prompts and prompt_preview:
        prompts.append((short_hash(prompt_preview), None))
    if not prompts:
        prompts.append(("bootstrap", None))
    if not responses:
        for usage in model_usage.values():
            if usage["total"] > 0:
                responses.append(dict(usage))

    return {
        "readable": True,
        "parseable": True,
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "prompts": len(prompts),
        "tools": tools,
        "llm_rows": llm_rows,
        "unique_llm": len(responses),
        "missing_source_id_rows": missing_source_id_rows,
        "tokens": sum(token_mass(response) for response in responses),
        "skills": exact_skills,
        "cwd": cwd,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    totals: Counter[str] = Counter()
    skills: Counter[str] = Counter()
    skill_sessions = 0
    projects: set[str] = set()
    for path in args.paths:
        totals["requested_files"] += 1
        result = parse_file(path)
        if result.get("readable"):
            totals["readable_files"] += 1
        else:
            continue
        totals["valid_json_rows"] += int(result.get("valid_rows", 0))
        totals["invalid_json_rows"] += int(result.get("invalid_rows", 0))
        if not result.get("parseable"):
            continue
        totals["parseable_sessions"] += 1
        for field in (
            "prompts",
            "tools",
            "llm_rows",
            "unique_llm",
            "missing_source_id_rows",
            "tokens",
        ):
            totals[field] += int(result.get(field, 0))
        session_skills = result.get("skills", [])
        if session_skills:
            skill_sessions += 1
            skills.update(session_skills)
        cwd = result.get("cwd")
        if cwd:
            projects.add(str(cwd))

    raw_operation_total = totals["prompts"] + totals["tools"] + totals["unique_llm"]
    output = {
        "requested_files": totals["requested_files"],
        "readable_files": totals["readable_files"],
        "parseable_sessions": totals["parseable_sessions"],
        "excluded_files": totals["requested_files"] - totals["parseable_sessions"],
        "valid_json_rows": totals["valid_json_rows"],
        "invalid_json_rows": totals["invalid_json_rows"],
        "raw_prompt_records": totals["prompts"],
        "raw_tool_invocations": totals["tools"],
        "raw_llm_rows_before_dedup": totals["llm_rows"],
        "raw_unique_llm_completions": totals["unique_llm"],
        "deduplicated_llm_fragments": totals["llm_rows"] - totals["unique_llm"],
        "llm_rows_without_stable_source_id": totals["missing_source_id_rows"],
        "raw_operation_total": raw_operation_total,
        "raw_token_total": totals["tokens"],
        "sessions_with_exact_skill_invocation": skill_sessions,
        "distinct_skills": len(skills),
        "exact_skill_invocations": sum(skills.values()),
        "skill_invocations": dict(sorted(skills.items())),
        "distinct_recorded_cwds": len(projects),
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
