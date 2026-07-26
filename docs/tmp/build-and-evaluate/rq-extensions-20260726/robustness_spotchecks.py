#!/usr/bin/env python3
"""Audit the two named latent projection risks against the frozen corpus."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


WHITELISTED_SUFFIXES = {
    "rs",
    "py",
    "md",
    "json",
    "ts",
    "tsx",
    "toml",
    "lock",
    "js",
    "c",
    "h",
    "svg",
    "html",
    "css",
}
RECOGNIZED_FILE_COMMANDS = {
    "cp",
    "mv",
    "rm",
    "touch",
    "cat",
    "sed",
    "head",
    "tail",
    "nl",
    "less",
    "more",
    "git",
}
REDIRECTIONS = {">", ">>", "&>", "&>>", "<", "<<", "<<<", "<>"}


def read_json(path: Path) -> Any:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            return json.load(stream)
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def event_path(events_dir: Path, project: str) -> Path:
    names = [project, "eunomia-dev"] if project == "eunomia.dev" else [project]
    for name in names:
        for suffix in (".json", ".json.gz"):
            candidate = events_dir / f"{name}{suffix}"
            if candidate.is_file():
                return candidate
    raise FileNotFoundError(project)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def cwd_values(data: bytes) -> list[str]:
    values = []
    for line in data.splitlines():
        try:
            row = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        value = row.get("cwd")
        if not value and isinstance(row.get("payload"), dict):
            value = row["payload"].get("cwd")
        if isinstance(value, str) and value:
            values.append(value)
    return values


def under_root(value: str, root: Path) -> bool:
    try:
        Path(value).relative_to(root)
        return True
    except ValueError:
        return False


def iso_ms(value: Any) -> int | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return int(parsed.timestamp() * 1000)


def claude_file_facts(path: Path, repository_root: Path, cutoff_ms: int) -> dict[str, Any]:
    data = path.read_bytes()
    first_values = cwd_values(data[: 256 * 1024])
    all_values = cwd_values(data)
    session_ids: set[str] = set()
    call_ids: set[str] = set()
    timed_calls = 0
    for line in data.splitlines():
        try:
            row = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        for key in ("sessionId", "session_id"):
            if isinstance(row.get(key), str):
                session_ids.add(row[key])
        if row.get("type") != "assistant":
            continue
        timestamp = iso_ms(row.get("timestamp"))
        if timestamp is None or timestamp > cutoff_ms:
            continue
        content = (row.get("message") or {}).get("content") or []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_use":
                timed_calls += 1
                if isinstance(item.get("id"), str) and item["id"]:
                    call_ids.add(item["id"])
    return {
        "bytes": len(data),
        "matching_cwd_first_256k": sum(
            under_root(value, repository_root) for value in first_values
        ),
        "any_cwd_first_256k": len(first_values),
        "matching_cwd_full_file": sum(
            under_root(value, repository_root) for value in all_values
        ),
        "any_cwd_full_file": len(all_values),
        "native_session_ids": ";".join(sorted(session_ids)),
        "timed_tool_call_occurrences_before_cutoff": timed_calls,
        "unique_timed_call_ids_before_cutoff": len(call_ids),
        "_call_ids": call_ids,
    }


def audit_encoded_claude_root(
    rq1_root: Path,
    output: Path,
    claude_projects: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    projects = read_json(rq1_root / "projects.json")
    dotted = [
        row
        for row in projects
        if "." in Path(str(row["repository_root"])).name
    ]
    frozen_call_ids: set[str] = set()
    frozen_source_files: set[str] = set()
    for row in projects:
        payload = read_json(event_path(rq1_root / "events", str(row["project"])))
        for event in payload["events"]:
            if event.get("source_call_id"):
                frozen_call_ids.add(str(event["source_call_id"]))
            if event.get("source_file"):
                frozen_source_files.add(os.path.realpath(str(event["source_file"])))

    file_rows: list[dict[str, Any]] = []
    project_rows: list[dict[str, Any]] = []
    affected_call_ids: set[str] = set()
    affected_files: set[str] = set()

    for project in dotted:
        name = str(project["project"])
        root = Path(str(project["repository_root"]))
        cutoff_ms = int(project["cutoff_ms"])
        buggy_encoding = str(root).replace("/", "-")
        observed_encoding = buggy_encoding.replace(".", "-")
        candidate_dir = claude_projects / observed_encoding
        candidates = sorted(candidate_dir.rglob("*.jsonl")) if candidate_dir.is_dir() else []
        affected_project_calls: set[str] = set()
        affected_project_files = 0
        cwdless_full_files = 0
        for path in candidates:
            facts = claude_file_facts(path, root, cutoff_ms)
            affected = facts["matching_cwd_first_256k"] == 0
            cwdless_full = facts["any_cwd_full_file"] == 0
            cwdless_full_files += int(cwdless_full)
            if affected:
                affected_project_files += 1
                affected_files.add(os.path.realpath(path))
                affected_project_calls.update(facts["_call_ids"])
                affected_call_ids.update(facts["_call_ids"])
            file_rows.append(
                {
                    "project": name,
                    "repository_root": str(root),
                    "buggy_encoded_root": buggy_encoding,
                    "observed_claude_project_dir": observed_encoding,
                    "source_file": path,
                    "relative_source_file": path.relative_to(candidate_dir),
                    "source_file_in_frozen_events": (
                        os.path.realpath(path) in frozen_source_files
                    ),
                    "matching_cwd_first_256k": facts["matching_cwd_first_256k"],
                    "any_cwd_first_256k": facts["any_cwd_first_256k"],
                    "matching_cwd_full_file": facts["matching_cwd_full_file"],
                    "any_cwd_full_file": facts["any_cwd_full_file"],
                    "cwdless_full_file": cwdless_full,
                    "filter_reliant_due_to_no_matching_cwd_first_256k": affected,
                    "native_session_ids": facts["native_session_ids"],
                    "timed_tool_call_occurrences_before_cutoff": facts[
                        "timed_tool_call_occurrences_before_cutoff"
                    ],
                    "unique_timed_call_ids_before_cutoff": facts[
                        "unique_timed_call_ids_before_cutoff"
                    ],
                }
            )
        lost_calls = affected_project_calls - frozen_call_ids
        project_rows.append(
            {
                "project": name,
                "repository_root": str(root),
                "buggy_encoded_root": buggy_encoding,
                "observed_claude_project_dir": observed_encoding,
                "encoding_matches": buggy_encoding == observed_encoding,
                "candidate_transcript_files": len(candidates),
                "files_with_matching_cwd_first_256k": sum(
                    int(row["matching_cwd_first_256k"] > 0)
                    for row in file_rows
                    if row["project"] == name
                ),
                "filter_reliant_files": affected_project_files,
                "fully_cwdless_files": cwdless_full_files,
                "affected_unique_tool_call_ids_before_cutoff": len(
                    affected_project_calls
                ),
                "affected_call_ids_absent_from_frozen_events": len(lost_calls),
            }
        )

    summary = {
        "dotted_projects": len(dotted),
        "candidate_transcript_files": sum(
            int(row["candidate_transcript_files"]) for row in project_rows
        ),
        "filter_reliant_files": len(affected_files),
        "fully_cwdless_files": sum(
            int(row["fully_cwdless_files"]) for row in project_rows
        ),
        "affected_unique_tool_call_ids_before_cutoff": len(affected_call_ids),
        "affected_call_ids_absent_from_frozen_events": len(
            affected_call_ids - frozen_call_ids
        ),
        "corpus_impact": bool(affected_call_ids - frozen_call_ids),
    }
    write_csv(
        output / "encoded-claude-root-files.csv",
        file_rows,
        [
            "project",
            "repository_root",
            "buggy_encoded_root",
            "observed_claude_project_dir",
            "source_file",
            "relative_source_file",
            "source_file_in_frozen_events",
            "matching_cwd_first_256k",
            "any_cwd_first_256k",
            "matching_cwd_full_file",
            "any_cwd_full_file",
            "cwdless_full_file",
            "filter_reliant_due_to_no_matching_cwd_first_256k",
            "native_session_ids",
            "timed_tool_call_occurrences_before_cutoff",
            "unique_timed_call_ids_before_cutoff",
        ],
    )
    write_csv(
        output / "encoded-claude-root-summary.csv",
        project_rows,
        list(project_rows[0]) if project_rows else ["project"],
    )
    return file_rows, project_rows, summary


def strip_heredoc_bodies(command: str) -> str:
    pending: list[str] = []
    output: list[str] = []
    pattern = re.compile(r"<<-?\s*(['\"]?)([^'\";\s|&><]+)\1")
    for line in command.splitlines():
        if pending:
            if line.lstrip("\t").rstrip() == pending[0]:
                pending.pop(0)
            continue
        output.append(line)
        for match in pattern.finditer(line):
            if not line[match.start() :].startswith("<<<"):
                pending.append(match.group(2))
    return "\n".join(output)


def shell_segments(command: str) -> list[list[str]]:
    """Port of agent-session's high-confidence shell tokenizer."""
    command = strip_heredoc_bodies(command)
    segments: list[list[str]] = []
    tokens: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False
    index = 0

    def word() -> None:
        if current:
            tokens.append("".join(current))
            current.clear()

    def segment() -> None:
        if tokens:
            segments.append(tokens.copy())
            tokens.clear()

    while index < len(command):
        char = command[index]
        lookahead = command[index + 1] if index + 1 < len(command) else ""
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif quote == char:
            quote = None
        elif quote is not None:
            current.append(char)
        elif char in {"'", '"'}:
            quote = char
        elif char == "#" and not current:
            while index < len(command) and command[index] != "\n":
                index += 1
            segment()
        elif char.isspace():
            word()
            if char == "\n":
                segment()
        elif char == "&" and lookahead == ">":
            word()
            index += 1
            operator = "&>"
            if index + 1 < len(command) and command[index + 1] == ">":
                index += 1
                operator = "&>>"
            tokens.append(operator)
        elif char in ";|()" or char == "&":
            word()
            if char in "|&" and lookahead == char:
                index += 1
            segment()
        elif char in "><":
            word()
            operator = char
            while (
                index + 1 < len(command)
                and command[index + 1] == char
                and len(operator) < 3
            ):
                index += 1
                operator += char
            tokens.append(operator)
        else:
            current.append(char)
        index += 1
    word()
    segment()
    return segments


def process_name(token: str) -> str:
    return PurePosixPath(token.strip("'\"")).name


def shell_file_operands(name: str, operands: list[str]) -> list[str]:
    option_arity: dict[str, set[str]] = {
        "head": {"-n", "--lines", "-c", "--bytes"},
        "tail": {
            "-n",
            "--lines",
            "-c",
            "--bytes",
            "-s",
            "--sleep-interval",
            "--pid",
        },
        "sed": {"-e", "--expression", "-f", "--file"},
        "nl": {
            "-b",
            "--body-numbering",
            "-d",
            "--section-delimiter",
            "-f",
            "--footer-numbering",
            "-h",
            "--header-numbering",
            "-i",
            "--line-increment",
            "-l",
            "--join-blank-lines",
            "-n",
            "--number-format",
            "-s",
            "--number-separator",
            "-v",
            "--starting-line-number",
            "-w",
            "--number-width",
        },
    }
    arity = option_arity.get(name, set())
    values: list[str] = []
    skip_next = False
    end_options = False
    explicit_sed_program = False
    for token in operands:
        if skip_next:
            skip_next = False
            continue
        if token == "--":
            end_options = True
            continue
        option = token.split("=", 1)[0]
        if not end_options and option in arity:
            explicit_sed_program |= name == "sed" and option in {
                "-e",
                "--expression",
                "-f",
                "--file",
            }
            skip_next = "=" not in token
            continue
        if not end_options and token.startswith("-"):
            continue
        values.append(token)
    if name == "sed" and not explicit_sed_program and values:
        values.pop(0)
    return values


def selected_file_operands(segment: list[str]) -> list[tuple[str, str]]:
    if not segment or any(token in REDIRECTIONS for token in segment[1:]):
        return []
    name = process_name(segment[0])
    values = shell_file_operands(name, segment[1:])
    if name == "git" and values and values[0] in {"rm", "mv"}:
        return selected_file_operands([values[0], *values[1:]])
    if name in {"cp", "mv"} and len(values) >= 2:
        source, target = values[-2:]
        if name == "cp":
            return [(source, "read"), (target, "create")]
        return [(source, "rename_from"), (target, "rename")]
    access = {
        "rm": "delete",
        "touch": "create",
        "cat": "read",
        "sed": "read",
        "head": "read",
        "tail": "read",
        "nl": "read",
        "less": "read",
        "more": "read",
    }.get(name)
    return [(value, access) for value in values] if access else []


def earlier_rejection(part: str) -> str | None:
    value = part.strip("'\"")
    lower = value.lower()
    components = value.split("/")
    sed_expression = value.startswith("s/") and (
        (flags := value.rsplit("/", 1)[-1]) == ""
        or all(flag in "gimpe" for flag in flags)
    )
    title_phrase = len(components) >= 3 and all(
        component.isalpha() and component[:1].isupper()
        for component in components
    )
    if not value:
        return "empty"
    if value.startswith("-"):
        return "option"
    if value.startswith("$"):
        return "variable"
    if value.startswith(("http://", "https://")):
        return "url"
    if lower.startswith(("origin/", "refs/", "repos/")):
        return "git_namespace"
    if value == "HEAD" or value.startswith("HEAD."):
        return "git_head"
    if "..." in value:
        return "range"
    if title_phrase:
        return "title_phrase"
    if sed_expression:
        return "sed_expression"
    if any(char.isspace() for char in value):
        return "whitespace"
    if any(char in '{}()=;<>|`*?[]"#$,:@^!' for char in value):
        return "punctuation"
    return None


def target_filter_rejection(part: str, command_name: str) -> str | None:
    value = part.strip("'\"")
    if earlier_rejection(value) is not None:
        return None
    if len(value.encode("utf-8")) > 140:
        return "long_gt_140_non_sed" if command_name != "sed" else None
    suffix = PurePosixPath(value).suffix.lstrip(".")
    if "/" not in value and suffix not in WHITELISTED_SUFFIXES:
        return "bare_nonwhitelisted_extension"
    return None


def normalized_token(token: str) -> str:
    value = token.strip().strip("'\"`,:")
    value = value.removeprefix("file://")
    if value.startswith("./"):
        value = value[2:]
    return str(PurePosixPath(value))


def path_matches(token: str, candidate: str) -> bool:
    token = normalized_token(token)
    candidate = normalized_token(candidate)
    if not token or not candidate:
        return False
    if token == candidate:
        return True
    if not token.startswith("/") and candidate.endswith(f"/{token}"):
        return True
    return "/" not in token and PurePosixPath(candidate).name == token


def edge_match(
    token: str,
    access: str | None,
    edges: Iterable[dict[str, Any]],
) -> bool:
    return any(
        path_matches(token, str(edge.get("path", "")))
        and (access is None or edge.get("access") == access)
        for edge in edges
    )


def known_artifact_match(
    token: str,
    paths: set[str],
    root_file_tokens: set[str],
    basenames: set[str],
) -> bool:
    value = normalized_token(token)
    if value in paths:
        return True
    if "/" not in value:
        # A bare token is ambiguous (e.g., `cargo build`). Treat it as a
        # known-path candidate only when that exact name was observed as a
        # repository-root artifact, not merely as a basename in some subtree.
        return value in root_file_tokens
    # Absolute/long tokens can be recognized cheaply by the basename of an
    # already observed artifact. This remains an intentionally loose bound.
    return PurePosixPath(value).name in basenames


def audit_parser_filters(
    rq1_root: Path, output: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    projects = read_json(rq1_root / "projects.json")
    occurrence_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []

    for project_row in projects:
        project = str(project_row["project"])
        payload = read_json(event_path(rq1_root / "events", project))
        events = payload["events"]
        known_paths = {
            str(action["path"])
            for event in events
            for action in event.get("actions", [])
            if not action.get("scope", False)
        }
        known_root_file_tokens = {path for path in known_paths if "/" not in path}
        known_basenames = {PurePosixPath(path).name for path in known_paths}
        counts: Counter[str] = Counter()
        unique_candidates: set[tuple[str, str, str]] = set()
        unique_upper: set[tuple[str, str, str]] = set()

        for event in events:
            if event.get("category") != "shell":
                continue
            command = str(event.get("command", ""))
            # extract_tool_paths uses patch markers instead of shell_file_actions
            # when a Tool call embeds an apply_patch payload.
            if "*** Begin Patch" in command:
                continue
            source_paths = event.get("source_paths", [])
            actions = event.get("actions", [])
            high_confidence: dict[tuple[str, str], int] = Counter()
            segments = shell_segments(command)
            for segment in segments:
                for token, access in selected_file_operands(segment):
                    high_confidence[(token, access)] += 1

            # Exact high-confidence operands used by production shell extraction.
            for (token, access), occurrences in high_confidence.items():
                command_name = next(
                    (
                        process_name(segment[0])
                        for segment in segments
                        if any(
                            selected_token == token and selected_access == access
                            for selected_token, selected_access in selected_file_operands(segment)
                        )
                    ),
                    str(event.get("command_name", "")),
                )
                reason = target_filter_rejection(token, command_name)
                if reason is None:
                    continue
                source_match = edge_match(token, access, source_paths)
                action_match = edge_match(token, access, actions)
                key = (str(event["id"]), normalized_token(token), reason)
                unique_candidates.add(key)
                counts[f"{reason}_high_conf_occurrences"] += occurrences
                counts[f"{reason}_high_conf_unique_event_operands"] += 1
                counts[f"{reason}_source_edge_matches"] += int(source_match)
                counts[f"{reason}_action_edge_matches"] += int(action_match)
                occurrence_rows.append(
                    {
                        "project": project,
                        "event_id": event["id"],
                        "command_name": command_name,
                        "reason": reason,
                        "evidence_class": "production_high_confidence_operand",
                        "token": token,
                        "occurrences_in_event": occurrences,
                        "known_artifact_token": known_artifact_match(
                            token,
                            known_paths,
                            known_root_file_tokens,
                            known_basenames,
                        ),
                        "source_path_edge_present": source_match,
                        "in_scope_action_edge_present": action_match,
                        "upper_bound_unmatched_candidate": not source_match,
                    }
                )
                if not source_match:
                    unique_upper.add(key)

        summary = {
            "project": project,
            "tool_actions": len(events),
            "shell_events": sum(
                event.get("category") == "shell" for event in events
            ),
        }
        for reason in (
            "bare_nonwhitelisted_extension",
            "long_gt_140_non_sed",
        ):
            summary.update(
                {
                    f"{reason}_high_conf_occurrences": counts[
                        f"{reason}_high_conf_occurrences"
                    ],
                    f"{reason}_high_conf_unique_event_operands": counts[
                        f"{reason}_high_conf_unique_event_operands"
                    ],
                    f"{reason}_source_edge_matches": counts[
                        f"{reason}_source_edge_matches"
                    ],
                    f"{reason}_action_edge_matches": counts[
                        f"{reason}_action_edge_matches"
                    ],
                    f"{reason}_upper_bound_unmatched_event_operands": sum(
                        key[2] == reason for key in unique_upper
                    ),
                }
            )
        summaries.append(summary)

    pooled = {
        "project": "POOLED",
        "tool_actions": sum(int(row["tool_actions"]) for row in summaries),
        "shell_events": sum(int(row["shell_events"]) for row in summaries),
    }
    for field in summaries[0]:
        if field not in {"project", "tool_actions", "shell_events"}:
            pooled[field] = sum(int(row[field]) for row in summaries)
    summaries.append(pooled)
    pooled_upper = sum(
        int(pooled[f"{reason}_upper_bound_unmatched_event_operands"])
        for reason in ("bare_nonwhitelisted_extension", "long_gt_140_non_sed")
    )
    summary = {
        "high_confidence_operand_occurrences_rejected": sum(
            int(pooled[f"{reason}_high_conf_occurrences"])
            for reason in ("bare_nonwhitelisted_extension", "long_gt_140_non_sed")
        ),
        "high_confidence_unique_event_operands_rejected": sum(
            int(pooled[f"{reason}_high_conf_unique_event_operands"])
            for reason in ("bare_nonwhitelisted_extension", "long_gt_140_non_sed")
        ),
        "high_confidence_source_edge_matches": sum(
            int(pooled[f"{reason}_source_edge_matches"])
            for reason in ("bare_nonwhitelisted_extension", "long_gt_140_non_sed")
        ),
        "high_confidence_action_edge_matches": sum(
            int(pooled[f"{reason}_action_edge_matches"])
            for reason in ("bare_nonwhitelisted_extension", "long_gt_140_non_sed")
        ),
        "conservative_upper_bound_unmatched_event_operands": pooled_upper,
        "file_action_edges_dropped_by_plausible_path_token": 0,
        "reason_file_edge_impact_is_zero": (
            "plausible_path_token gates ToolEvent.path_groups only; "
            "ToolEvent.paths/FileAction edges use shell_file_actions"
        ),
    }
    write_csv(
        output / "parser-filter-occurrences.csv",
        occurrence_rows,
        [
            "project",
            "event_id",
            "command_name",
            "reason",
            "evidence_class",
            "token",
            "occurrences_in_event",
            "known_artifact_token",
            "source_path_edge_present",
            "in_scope_action_edge_present",
            "upper_bound_unmatched_candidate",
        ],
    )
    write_csv(
        output / "parser-filter-summary.csv",
        summaries,
        list(summaries[0]),
    )
    return occurrence_rows, summaries, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rq1-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--claude-projects",
        type=Path,
        default=Path.home() / ".claude/projects",
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    _, encoded_rows, encoded_summary = audit_encoded_claude_root(
        args.rq1_root, args.output, args.claude_projects
    )
    _, parser_rows, parser_summary = audit_parser_filters(
        args.rq1_root, args.output
    )
    summary = {
        "encoded_claude_root": encoded_summary,
        "plausible_path_token": parser_summary,
        "encoded_project_rows": encoded_rows,
        "parser_project_rows": parser_rows,
    }
    (args.output / "robustness-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
