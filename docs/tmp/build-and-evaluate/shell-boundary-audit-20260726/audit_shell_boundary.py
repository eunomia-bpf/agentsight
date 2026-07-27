#!/usr/bin/env python3
"""Audit compound-shell/wrapper path exposure in the final RQ1--RQ4 corpus.

The script is deliberately projection-independent where possible:

* broad syntax shapes are detected from Tool command text;
* high-confidence path operands are recovered with a small shell lexer;
* already projected action rows are retained as a lower-bound cross-check;
* RQ1 sensitivities are joined to the generated artifact/mutation ledgers;
* RQ3 locality is reconstructed directly from the final event JSON;
* RQ4 boundary counts are read from the final generated boundary ledger.

It writes only CSV files next to this script.  It does not invoke Git, mutate
the source corpus, or edit the paper.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import re
import shlex
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


SHELL_TOOLS = {
    "bash",
    "exec",
    "exec_command",
    "shell_command",
    "run_shell_command",
    "shell",
}
CONTROL_TOKENS = {";", ";;", "&", "&&", "|", "||", "(", ")"}
REDIRECTION_RE = re.compile(r"^(?:\d*)(?:<|>|<<|>>|<<<|<>|>&|<&|&>|&>>)$")
JS_WRAPPER_RE = re.compile(
    r"(?:\btools\.[A-Za-z_][A-Za-z0-9_]*\s*\(|"
    r"\b(?:const|let|var)\s+[A-Za-z_$][A-Za-z0-9_$]*\s*=|"
    r"\bawait\s+|\bPromise\.all\s*\(|\btext\s*\()"
)
SHELL_C_RE = re.compile(
    r"(?:^|[;&|(\n]\s*)(?:(?:sudo|env|command|timeout|nice)\s+)*"
    r"(?:/[^\s]+/)?(?:ba|da|z|k)?sh\s+(?:[^;&|\n]*\s)?-c(?:\s|$)"
)
SCRIPT_RE = re.compile(r"\.(?:sh|bash|zsh|py|pl|rb|js|mjs|ts)$", re.I)
KNOWN_BASENAMES = {
    "makefile",
    "dockerfile",
    "license",
    "readme",
    "cargo.toml",
    "cargo.lock",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
}
READ_COMMANDS = {
    "cat",
    "sed",
    "head",
    "tail",
    "nl",
    "less",
    "more",
    "diff",
    "cmp",
    "stat",
    "file",
    "ls",
    "grep",
    "rg",
    "find",
}
MUTATE_COMMANDS = {
    "rm",
    "touch",
    "mkdir",
    "rmdir",
    "truncate",
    "tee",
    "cp",
    "mv",
    "install",
    "ln",
}
MUTATION_ACCESSES = {"write", "create", "rename", "delete", "unknown_mutation"}
NONDELETE_MUTATION_ACCESSES = {"write", "create", "rename", "unknown_mutation"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bool_text(value: object) -> bool:
    return str(value).lower() == "true"


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def strip_heredoc_bodies(command: str) -> str:
    """Remove heredoc bodies while retaining the command line."""
    pending: list[str] = []
    output: list[str] = []
    marker_re = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
    for line in command.splitlines():
        if pending:
            expected = pending[0]
            if line.lstrip("\t").rstrip() == expected:
                pending.pop(0)
            continue
        output.append(line)
        pending.extend(match.group(2) for match in marker_re.finditer(line))
    return "\n".join(output)


def has_unquoted_newline(command: str) -> bool:
    quote = ""
    escaped = False
    for character in strip_heredoc_bodies(command):
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif quote:
            if character == quote:
                quote = ""
        elif character in {"'", '"', "`"}:
            quote = character
        elif character == "\n":
            return True
    return False


def quote_spans_newline(command: str) -> bool:
    quote = ""
    escaped = False
    for character in strip_heredoc_bodies(command):
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif quote:
            if character == quote:
                quote = ""
            elif character == "\n":
                return True
        elif character in {"'", '"', "`"}:
            quote = character
    return False


def decode_static_js_string(text: str, opening: int) -> tuple[str, int] | None:
    if opening >= len(text) or text[opening] not in {"'", '"', "`"}:
        return None
    quote = text[opening]
    escaped = False
    for offset in range(opening + 1, len(text)):
        character = text[offset]
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == quote:
            raw = text[opening : offset + 1]
            if quote == "`":
                body = raw[1:-1]
                if "${" in body:
                    return None
                try:
                    return bytes(body, "utf-8").decode("unicode_escape"), offset + 1
                except UnicodeDecodeError:
                    return body, offset + 1
            try:
                value = json.loads(raw) if quote == '"' else ast.literal_eval(raw)
            except (json.JSONDecodeError, SyntaxError, ValueError):
                return None
            return (value, offset + 1) if isinstance(value, str) else None
    return None


def balanced_object(text: str, opening: int) -> tuple[str, int] | None:
    if opening < 0 or opening >= len(text) or text[opening] != "{":
        return None
    depth = 0
    quote = ""
    escaped = False
    for offset in range(opening, len(text)):
        character = text[offset]
        if escaped:
            escaped = False
        elif quote and character == "\\":
            escaped = True
        elif quote:
            if character == quote:
                quote = ""
        elif character in {"'", '"', "`"}:
            quote = character
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return text[opening : offset + 1], offset + 1
    return None


def static_field(obj: str, field: str) -> str | None:
    pattern = re.compile(rf"(?:[\"']?{re.escape(field)}[\"']?)\s*:\s*")
    match = pattern.search(obj)
    if not match:
        return None
    decoded = decode_static_js_string(obj, match.end())
    return decoded[0] if decoded else None


def nested_shell_commands(command: str) -> list[str]:
    """Decode static tools.exec_command/tools.shell_command envelopes."""
    marker = re.compile(r"tools\.(?:exec_command|shell_command)\s*\(")
    output: list[str] = []
    for match in marker.finditer(command):
        opening = command.find("{", match.end())
        found = balanced_object(command, opening)
        if not found:
            continue
        obj, _ = found
        nested = static_field(obj, "cmd") or static_field(obj, "command")
        if nested:
            output.append(nested)
    return output


def tokenize_shell(command: str) -> list[str]:
    lexer = shlex.shlex(
        strip_heredoc_bodies(command),
        posix=True,
        punctuation_chars=";&|<>()",
    )
    lexer.whitespace_split = True
    lexer.commenters = "#"
    try:
        return list(lexer)
    except ValueError:
        tokens: list[str] = []
        for line in strip_heredoc_bodies(command).splitlines():
            try:
                line_lexer = shlex.shlex(
                    line,
                    posix=True,
                    punctuation_chars=";&|<>()",
                )
                line_lexer.whitespace_split = True
                line_lexer.commenters = "#"
                tokens.extend(list(line_lexer))
                tokens.append(";")
            except ValueError:
                continue
        return tokens


def shell_segments(command: str) -> list[list[str]]:
    tokens = tokenize_shell(command)
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in CONTROL_TOKENS or (
            token and set(token) <= {";", "&", "|", "(", ")"}
        ):
            if current:
                segments.append(current)
                current = []
        else:
            current.append(token)
    if current:
        segments.append(current)
    return segments


def strip_prefixes(tokens: list[str]) -> list[str]:
    tokens = list(tokens)
    while tokens:
        name = tokens[0].rsplit("/", 1)[-1]
        if name in {"sudo", "command", "nice"}:
            tokens = tokens[1:]
        elif name == "timeout" and len(tokens) >= 2:
            tokens = tokens[2:]
        elif name == "env":
            tokens = tokens[1:]
            while tokens and ("=" in tokens[0] or tokens[0].startswith("-")):
                tokens = tokens[1:]
        else:
            break
    return tokens


def plausible_path(token: str) -> bool:
    value = token.strip().strip(",")
    if not value or value in {"-", "--", ".", ".."}:
        return value in {".", ".."}
    if value.isdigit() or value.startswith(("http://", "https://", "git@")):
        return False
    if value.startswith(("$(", "<(", ">(", "${")):
        return False
    if value in {"true", "false", "null"}:
        return False
    if value.startswith(("/", "./", "../", "~/", ".")):
        return True
    if "/" in value:
        return True
    lower = value.lower()
    if lower in KNOWN_BASENAMES:
        return True
    suffix = PurePosixPath(value).suffix
    return bool(suffix and 1 < len(suffix) <= 10 and suffix[1:].isalnum())


def remove_options(
    values: list[str],
    option_arity: set[str] | None = None,
) -> list[str]:
    option_arity = option_arity or set()
    output: list[str] = []
    skip = False
    options_done = False
    for value in values:
        if skip:
            skip = False
            continue
        if value == "--":
            options_done = True
            continue
        name = value.split("=", 1)[0]
        if not options_done and name in option_arity:
            skip = "=" not in value
        elif not options_done and value.startswith("-"):
            continue
        else:
            output.append(value)
    return output


def redirection_effects(tokens: list[str]) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    for index, token in enumerate(tokens):
        if not REDIRECTION_RE.match(token):
            continue
        if "<" in token and ">" not in token:
            access = "read"
        else:
            access = "create"
        if index + 1 < len(tokens) and plausible_path(tokens[index + 1]):
            output.append((access, tokens[index + 1]))
    return output


def clean_redirections(tokens: list[str]) -> list[str]:
    output: list[str] = []
    skip = False
    for token in tokens:
        if skip:
            skip = False
            continue
        if REDIRECTION_RE.match(token):
            if output and output[-1].isdigit():
                output.pop()
            skip = True
            continue
        output.append(token)
    return output


def script_invocation(tokens: list[str]) -> list[str]:
    tokens = strip_prefixes(tokens)
    if not tokens:
        return []
    executable = tokens[0].rsplit("/", 1)[-1].lower()
    if SCRIPT_RE.search(tokens[0]):
        return [value for value in tokens if plausible_path(value)]
    if executable in {
        "bash",
        "sh",
        "dash",
        "zsh",
        "ksh",
        "python",
        "python3",
        "perl",
        "ruby",
        "node",
        "deno",
    }:
        candidates = [
            value
            for value in tokens[1:]
            if not value.startswith("-") and SCRIPT_RE.search(value)
        ]
        if candidates:
            return [value for value in tokens[1:] if plausible_path(value)]
    return []


def effects_for_segment(tokens: list[str]) -> list[tuple[str, str]]:
    """Return conservative (access, operand) pairs from one shell segment."""
    tokens = strip_prefixes(tokens)
    if not tokens:
        return []
    effects = redirection_effects(tokens)
    cleaned = clean_redirections(tokens)
    if not cleaned:
        return effects
    name = cleaned[0].rsplit("/", 1)[-1].lower()
    operands = cleaned[1:]

    scripts = script_invocation(cleaned)
    if scripts:
        effects.extend(("unknown_mutation", value) for value in scripts)
        return effects

    if name == "git" and operands:
        subcommand = operands[0]
        values = remove_options(operands[1:])
        values = [value for value in values if plausible_path(value)]
        if subcommand == "rm":
            effects.extend(("delete", value) for value in values)
        elif subcommand == "mv" and len(values) >= 2:
            effects.extend(("rename", value) for value in values)
        return effects

    if name not in READ_COMMANDS | MUTATE_COMMANDS:
        return effects

    arity = {
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
        "grep": {"-e", "--regexp", "-f", "--file", "-m", "--max-count"},
        "rg": {
            "-e",
            "--regexp",
            "-f",
            "--file",
            "-g",
            "--glob",
            "-t",
            "--type",
            "-T",
            "--type-not",
        },
    }.get(name, set())
    values = remove_options(operands, arity)

    if name == "sed":
        explicit = any(
            value.split("=", 1)[0] in {"-e", "--expression", "-f", "--file"}
            for value in operands
        )
        if not explicit and values:
            values = values[1:]
    elif name in {"grep", "rg"}:
        explicit = any(
            value.split("=", 1)[0] in {"-e", "--regexp", "-f", "--file"}
            for value in operands
        )
        if not explicit and values:
            values = values[1:]
    elif name == "find":
        values = [value for value in values if not value.startswith("-")]
        values = values[:1]

    paths = [value for value in values if plausible_path(value)]
    if name in READ_COMMANDS:
        effects.extend(("read", value) for value in paths)
    elif name in {"rm", "rmdir"}:
        effects.extend(("delete", value) for value in paths)
    elif name in {"touch", "mkdir", "truncate", "tee"}:
        effects.extend(("create", value) for value in paths)
    elif name in {"cp", "install"} and len(paths) >= 2:
        sources, destination = paths[:-1], paths[-1]
        effects.extend(("read", value) for value in sources)
        # A multi-source directory copy can create one child per source.
        effects.extend(("create", destination) for _ in sources)
    elif name in {"mv", "ln"} and len(paths) >= 2:
        effects.extend(("rename", value) for value in paths)
    return effects


def analyzed_commands(tool_name: str, command: str) -> list[str]:
    nested = nested_shell_commands(command)
    if nested:
        return nested
    if tool_name.lower() == "exec" and JS_WRAPPER_RE.search(command):
        return []
    return [command]


def command_effects(tool_name: str, command: str) -> list[tuple[str, str]]:
    output: list[tuple[str, str]] = []
    for candidate in analyzed_commands(tool_name, command):
        for segment in shell_segments(candidate):
            output.extend(effects_for_segment(segment))
    return output


def segment_facts(tool_name: str, command: str) -> dict[str, bool]:
    commands = analyzed_commands(tool_name, command) or [command]
    segments = [
        strip_prefixes(segment)
        for candidate in commands
        for segment in shell_segments(candidate)
    ]
    segments = [segment for segment in segments if segment]
    redirection_file = False
    multisource_cp = False
    recursive_multi_git_rm = False
    wrapper_script = False
    for segment in segments:
        raw_name = segment[0].rsplit("/", 1)[-1].lower()
        has_redirection = any(REDIRECTION_RE.match(token) for token in segment)
        cleaned = clean_redirections(segment)
        if not cleaned:
            continue
        name = cleaned[0].rsplit("/", 1)[-1].lower()
        if has_redirection and name in READ_COMMANDS | MUTATE_COMMANDS | {"git"}:
            redirection_file = True
        if name in {"cp", "mv", "install"}:
            values = [
                value
                for value in remove_options(cleaned[1:])
                if plausible_path(value)
            ]
            multisource_cp |= len(values) >= 3
        if name == "git" and len(cleaned) >= 2 and cleaned[1] == "rm":
            values = [
                value
                for value in remove_options(cleaned[2:])
                if plausible_path(value)
            ]
            recursive_multi_git_rm |= (
                any(
                    option in {"-r", "-R", "--recursive"}
                    or option.startswith(("-r", "-R"))
                    for option in cleaned[2:]
                )
                or len(values) >= 2
            )
        wrapper_script |= bool(script_invocation(segment))
        # Preserve the raw name access to avoid an unused-variable false signal
        # in static linters while documenting prefix normalization.
        _ = raw_name
    nested_count = len(nested_shell_commands(command))
    js_envelope = tool_name.lower() == "exec" and bool(JS_WRAPPER_RE.search(command))
    process_substitution = "<(" in command or ">(" in command
    compound_control = (
        len(segments) >= 2
        or has_unquoted_newline(command)
        or process_substitution
    )
    shell_c_wrapper = bool(SHELL_C_RE.search(command))
    leading_backslash = bool(re.match(r"^\s*\\\r?\n", command))
    multiline_quoted = quote_spans_newline(command) and compound_control
    multi_exec_envelope = nested_count >= 2
    broad = any(
        [
            compound_control,
            shell_c_wrapper,
            wrapper_script,
            js_envelope,
            process_substitution,
        ]
    )
    heldout_trigger = any(
        [
            multisource_cp,
            recursive_multi_git_rm,
            process_substitution,
            leading_backslash,
            redirection_file,
            multiline_quoted,
            multi_exec_envelope,
        ]
    )
    return {
        "compound_control": compound_control,
        "shell_c_wrapper": shell_c_wrapper,
        "wrapper_script": wrapper_script,
        "exec_envelope": js_envelope,
        "process_substitution": process_substitution,
        "redirection_file_command": redirection_file,
        "multisource_cp_mv": multisource_cp,
        "recursive_multi_git_rm": recursive_multi_git_rm,
        "leading_backslash": leading_backslash,
        "multiline_quoted_compound": multiline_quoted,
        "multi_exec_envelope": multi_exec_envelope,
        "broad_compound_wrapper": broad,
        "heldout_trigger": heldout_trigger,
    }


def capacity(
    projected: list[tuple[str, str]],
    lexical: list[tuple[str, str]],
    accesses: set[str],
) -> int:
    projected_n = sum(access in accesses for access, _ in projected)
    lexical_n = sum(access in accesses for access, _ in lexical)
    return max(projected_n, lexical_n)


def event_row(project: str, event_index: int, event: dict[str, Any]) -> dict[str, object]:
    command = str(event.get("command") or "")
    tool_name = str(event.get("tool_name") or "")
    facts = segment_facts(tool_name, command)
    projected = [
        (str(action.get("access") or "read"), str(action.get("path") or ""))
        for action in event.get("actions", [])
        if action.get("path")
    ]
    lexical = command_effects(tool_name, command)
    projected_distinct = sorted(set(projected))
    lexical_distinct = sorted(set(lexical))
    path_capacity = max(len(projected_distinct), len(lexical_distinct))
    flags = [name for name, present in facts.items() if present and name not in {
        "broad_compound_wrapper", "heldout_trigger"
    }]
    return {
        "project": project,
        "vendor": str(event.get("vendor") or ""),
        "event_index": event_index,
        "event_id": str(event.get("id") or ""),
        "source_call_id": str(event.get("source_call_id") or ""),
        "session_id": str(event.get("session_id") or ""),
        "worktree_id": str(event.get("worktree_id") or ""),
        "tool_name": tool_name,
        "category": str(event.get("category") or ""),
        "status": str(event.get("status") or "observed"),
        **facts,
        "shape_flags": ";".join(flags),
        "projected_path_rows": len(projected),
        "projected_distinct_path_accesses": len(projected_distinct),
        "lexical_distinct_path_accesses": len(lexical_distinct),
        "path_operand_capacity": path_capacity,
        "contains_path_operand": path_capacity > 0,
        "create_capacity": capacity(projected_distinct, lexical_distinct, {"create"}),
        "nondelete_mutation_capacity": capacity(
            projected_distinct,
            lexical_distinct,
            NONDELETE_MUTATION_ACCESSES,
        ),
        "mutation_capacity": capacity(
            projected_distinct,
            lexical_distinct,
            MUTATION_ACCESSES,
        ),
        "command_sha256": hashlib.sha256(command.encode()).hexdigest(),
        "command_preview": re.sub(r"\s+", " ", command).strip()[:240],
        "_event": event,
        "_projected": projected_distinct,
        "_lexical": lexical_distinct,
    }


def load_corpus(events_dir: Path) -> tuple[
    list[dict[str, object]],
    dict[str, list[dict[str, Any]]],
    dict[str, str],
]:
    rows: list[dict[str, object]] = []
    events_by_project: dict[str, list[dict[str, Any]]] = {}
    input_hashes: dict[str, str] = {}
    for path in sorted(events_dir.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        project = str(document["repository"])
        events = list(document["events"])
        events_by_project[project] = events
        input_hashes[path.name] = sha256(path)
        rows.extend(event_row(project, index, event) for index, event in enumerate(events))
    return rows, events_by_project, input_hashes


def public_event_row(row: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in row.items() if not key.startswith("_")}


def exposure_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[("ALL", "ALL")].append(row)
        groups[(str(row["project"]), "ALL")].append(row)
        groups[("ALL", str(row["vendor"]))].append(row)
        groups[(str(row["project"]), str(row["vendor"]))].append(row)
    output: list[dict[str, object]] = []
    for (project, vendor), selected in sorted(groups.items()):
        broad = [row for row in selected if bool(row["broad_compound_wrapper"])]
        trigger = [row for row in selected if bool(row["heldout_trigger"])]
        output.append({
            "project": project,
            "vendor": vendor,
            "tool_actions": len(selected),
            "shell_actions": sum(row["category"] == "shell" for row in selected),
            "broad_compound_wrapper_actions": len(broad),
            "broad_with_path_operand": sum(bool(row["contains_path_operand"]) for row in broad),
            "broad_path_operand_capacity": sum(int(row["path_operand_capacity"]) for row in broad),
            "heldout_trigger_actions": len(trigger),
            "heldout_trigger_with_path_operand": sum(bool(row["contains_path_operand"]) for row in trigger),
            "heldout_trigger_path_operand_capacity": sum(int(row["path_operand_capacity"]) for row in trigger),
            **{
                flag: sum(bool(row[flag]) for row in selected)
                for flag in [
                    "compound_control",
                    "shell_c_wrapper",
                    "wrapper_script",
                    "exec_envelope",
                    "process_substitution",
                    "redirection_file_command",
                    "multisource_cp_mv",
                    "recursive_multi_git_rm",
                    "leading_backslash",
                    "multiline_quoted_compound",
                    "multi_exec_envelope",
                ]
            },
        })
    return output


def ratio_interval(
    numerator: int,
    denominator: int,
    origin_numerator: int,
    origin_denominator: int,
    endpoint_sensitive: int,
    endpoint_observed: int,
    missing_outcome_capacity: int,
    new_denominator_capacity: int,
) -> tuple[int, int, int, int, float, float]:
    denominator_min = max(0, denominator - origin_denominator)
    denominator_max = denominator_min + new_denominator_capacity
    fixed_numerator = max(0, numerator - origin_numerator - endpoint_observed)
    numerator_min = max(0, fixed_numerator - missing_outcome_capacity)
    numerator_max = min(
        denominator_max,
        fixed_numerator
        + endpoint_sensitive
        + missing_outcome_capacity
        + new_denominator_capacity,
    )
    lower = numerator_min / denominator_max if denominator_max else math.nan
    upper_denominator = denominator_max
    upper = numerator_max / upper_denominator if upper_denominator else math.nan
    return (
        numerator_min,
        numerator_max,
        denominator_min,
        denominator_max,
        lower,
        upper,
    )


def rq1_sensitivity(
    root: Path,
    event_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    summary_rows = read_csv(root / "rq1-summary.csv")
    artifacts = read_csv(root / "rq1-artifacts.csv")
    mutations = read_csv(root / "rq1-mutations.csv")
    summary = {row["project"]: row for row in summary_rows}
    artifacts_by_project: dict[str, list[dict[str, str]]] = defaultdict(list)
    mutations_by_project: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in artifacts:
        artifacts_by_project[row["project"]].append(row)
    for row in mutations:
        mutations_by_project[row["project"]].append(row)

    event_index_by_id = {
        (str(row["project"]), str(row["event_id"])): int(row["event_index"])
        for row in event_rows
    }
    scopes = {
        "broad": {
            (str(row["project"]), str(row["event_id"]))
            for row in event_rows
            if row["broad_compound_wrapper"] and row["contains_path_operand"]
        },
        "heldout_trigger": {
            (str(row["project"]), str(row["event_id"]))
            for row in event_rows
            if row["heldout_trigger"] and row["contains_path_operand"]
        },
    }
    row_by_key = {
        (str(row["project"]), str(row["event_id"])): row for row in event_rows
    }
    output: list[dict[str, object]] = []
    for scope_name, risky in scopes.items():
        project_outputs: list[dict[str, object]] = []
        for project in summary:
            project_risky = {event_id for candidate, event_id in risky if candidate == project}
            risky_indexes = {
                event_index_by_id[(project, event_id)]
                for event_id in project_risky
            }
            confirmed_rows = [
                row_by_key[(project, event_id)]
                for event_id in project_risky
                if row_by_key[(project, event_id)]["status"] == "ok"
            ]
            path_capacity = sum(int(row["path_operand_capacity"]) for row in confirmed_rows)
            create_capacity = sum(int(row["create_capacity"]) for row in confirmed_rows)
            mutation_capacity = sum(
                int(row["nondelete_mutation_capacity"]) for row in confirmed_rows
            )

            project_artifacts = artifacts_by_project[project]
            introductions = [
                row
                for row in project_artifacts
                if bool_text(row["introduced_eligible"])
                and bool_text(row["final_state_known"])
            ]
            introduction_origins = [
                row for row in introductions if int(row["first_event_index"]) in risky_indexes
            ]
            project_mutations = mutations_by_project[project]
            non_delete = [row for row in project_mutations if row["operation"] != "delete"]
            origin_mutations = [
                row for row in non_delete if row["event_id"] in project_risky
            ]
            risky_mutated_ids = {
                row["artifact_id"]
                for row in project_mutations
                if row["event_id"] in project_risky
            }
            touched_introductions = [
                row
                for row in introductions
                if row["artifact_id"] in risky_mutated_ids
                and row not in introduction_origins
            ]

            base_intro_num = int(summary[project]["introduced_persisted"])
            base_intro_den = int(summary[project]["introduced_eligible"])
            intro_origin_num = sum(bool_text(row["final_exists"]) for row in introduction_origins)
            intro_origin_den = len(introduction_origins)
            touched_intro_success = sum(
                bool_text(row["final_exists"]) for row in touched_introductions
            )
            intro_fixed = max(
                0,
                base_intro_num
                - intro_origin_num
                - touched_intro_success
                - path_capacity,
            )
            intro_den_min = base_intro_den - intro_origin_den
            intro_den_max = intro_den_min + create_capacity
            intro_num_min = intro_fixed
            touched_intro_fail = len(touched_introductions) - touched_intro_success
            intro_num_max = min(
                intro_den_max,
                base_intro_num
                - intro_origin_num
                + touched_intro_fail
                + path_capacity
                + create_capacity,
            )
            intro_lower = intro_num_min / intro_den_max if intro_den_max else math.nan
            intro_upper = intro_num_max / intro_den_max if intro_den_max else math.nan
            intro_ablation_den = base_intro_den - intro_origin_den
            intro_ablation_num_lower = (
                base_intro_num
                - intro_origin_num
                - touched_intro_success
            )
            intro_ablation_num_upper = min(
                intro_ablation_den,
                intro_ablation_num_lower + len(touched_introductions),
            )
            intro_ablation_lower = (
                intro_ablation_num_lower / intro_ablation_den
                if intro_ablation_den
                else math.nan
            )
            intro_ablation_upper = (
                intro_ablation_num_upper / intro_ablation_den
                if intro_ablation_den
                else math.nan
            )

            project_metrics = [(
                "persistence",
                base_intro_num,
                base_intro_den,
                intro_origin_num,
                intro_origin_den,
                len(touched_introductions),
                touched_intro_success,
                path_capacity,
                create_capacity,
                intro_num_min,
                intro_num_max,
                intro_den_min,
                intro_den_max,
                intro_lower,
                intro_upper,
                intro_ablation_lower,
                intro_ablation_upper,
                intro_ablation_num_lower,
                intro_ablation_num_upper,
                intro_ablation_den,
            )]
            for metric, field, observed_value in [
                ("reuse", "reuse_outcome", "observed_reuse"),
                ("validation", "validation_outcome", "observed_validation"),
            ]:
                base_num = int(summary[project][f"{metric}_observed"])
                base_den = int(summary[project][f"{metric}_eligible"])
                origin_num = sum(row[field] == observed_value for row in origin_mutations)
                origin_den = len(origin_mutations)
                endpoint_field = (
                    "reuse_event_index" if metric == "reuse" else "validation_event_index"
                )
                endpoint_rows = [
                    row
                    for row in non_delete
                    if row not in origin_mutations
                    and row[endpoint_field]
                    and int(row[endpoint_field]) in risky_indexes
                ]
                endpoint_observed = sum(
                    row[field] == observed_value for row in endpoint_rows
                )
                interval = ratio_interval(
                    base_num,
                    base_den,
                    origin_num,
                    origin_den,
                    len(endpoint_rows),
                    endpoint_observed,
                    path_capacity,
                    mutation_capacity,
                )
                ablation_den = base_den - origin_den
                ablation_num_lower = (
                    base_num
                    - origin_num
                    - endpoint_observed
                )
                ablation_num_upper = min(
                    ablation_den,
                    ablation_num_lower + len(endpoint_rows),
                )
                ablation_lower = (
                    ablation_num_lower / ablation_den
                    if ablation_den
                    else math.nan
                )
                ablation_upper = (
                    ablation_num_upper / ablation_den
                    if ablation_den
                    else math.nan
                )
                project_metrics.append((
                    metric,
                    base_num,
                    base_den,
                    origin_num,
                    origin_den,
                    len(endpoint_rows),
                    endpoint_observed,
                    path_capacity,
                    mutation_capacity,
                    *interval,
                    ablation_lower,
                    ablation_upper,
                    ablation_num_lower,
                    ablation_num_upper,
                    ablation_den,
                ))

            for values in project_metrics:
                (
                    metric,
                    base_num,
                    base_den,
                    origin_num,
                    origin_den,
                    endpoint_sensitive,
                    endpoint_observed,
                    outcome_capacity,
                    new_den_capacity,
                    num_min,
                    num_max,
                    den_min,
                    den_max,
                    lower,
                    upper,
                    ablation_lower,
                    ablation_upper,
                    ablation_num_lower,
                    ablation_num_upper,
                    ablation_den,
                ) = values
                baseline = base_num / base_den if base_den else math.nan
                max_shift_pp = max(
                    abs(lower - baseline),
                    abs(upper - baseline),
                ) * 100 if not math.isnan(baseline) else math.nan
                row = {
                    "scope": scope_name,
                    "project": project,
                    "metric": metric,
                    "baseline_numerator": base_num,
                    "baseline_denominator": base_den,
                    "baseline_rate": baseline,
                    "origin_affected_numerator": origin_num,
                    "origin_affected_denominator": origin_den,
                    "endpoint_sensitive_rows": endpoint_sensitive,
                    "endpoint_observed_rows": endpoint_observed,
                    "missing_outcome_capacity": outcome_capacity,
                    "new_denominator_capacity": new_den_capacity,
                    "numerator_min": num_min,
                    "numerator_max": num_max,
                    "denominator_min": den_min,
                    "denominator_max": den_max,
                    "rate_lower": lower,
                    "rate_upper": upper,
                    "current_projection_ablation_lower": ablation_lower,
                    "current_projection_ablation_upper": ablation_upper,
                    "current_projection_ablation_numerator_min": ablation_num_lower,
                    "current_projection_ablation_numerator_max": ablation_num_upper,
                    "current_projection_ablation_denominator": ablation_den,
                    "current_projection_ablation_max_shift_pp": max(
                        abs(ablation_lower - baseline),
                        abs(ablation_upper - baseline),
                    ) * 100,
                    "max_absolute_shift_pp": max_shift_pp,
                    "material_ge_1pp": max_shift_pp >= 1.0,
                }
                output.append(row)
                project_outputs.append(row)

        for metric in ["persistence", "reuse", "validation"]:
            selected = [row for row in project_outputs if row["metric"] == metric]
            base_num = sum(int(row["baseline_numerator"]) for row in selected)
            base_den = sum(int(row["baseline_denominator"]) for row in selected)
            num_min = sum(int(row["numerator_min"]) for row in selected)
            num_max = sum(int(row["numerator_max"]) for row in selected)
            den_min = sum(int(row["denominator_min"]) for row in selected)
            den_max = sum(int(row["denominator_max"]) for row in selected)
            baseline = base_num / base_den if base_den else math.nan
            lower = num_min / den_max if den_max else math.nan
            upper = num_max / den_max if den_max else math.nan
            # Pool the exact numerator/denominator bounds instead of averaging
            # project rates.
            ablation_den = sum(
                int(row["current_projection_ablation_denominator"])
                for row in selected
            )
            ablation_num_lower = sum(
                int(row["current_projection_ablation_numerator_min"])
                for row in selected
            )
            ablation_num_upper = sum(
                int(row["current_projection_ablation_numerator_max"])
                for row in selected
            )
            ablation_lower = (
                ablation_num_lower / ablation_den if ablation_den else math.nan
            )
            ablation_upper = (
                ablation_num_upper / ablation_den if ablation_den else math.nan
            )
            output.append({
                "scope": scope_name,
                "project": "ALL",
                "metric": metric,
                "baseline_numerator": base_num,
                "baseline_denominator": base_den,
                "baseline_rate": baseline,
                "origin_affected_numerator": sum(
                    int(row["origin_affected_numerator"]) for row in selected
                ),
                "origin_affected_denominator": sum(
                    int(row["origin_affected_denominator"]) for row in selected
                ),
                "endpoint_sensitive_rows": sum(
                    int(row["endpoint_sensitive_rows"]) for row in selected
                ),
                "endpoint_observed_rows": sum(
                    int(row["endpoint_observed_rows"]) for row in selected
                ),
                "missing_outcome_capacity": sum(
                    int(row["missing_outcome_capacity"]) for row in selected
                ),
                "new_denominator_capacity": sum(
                    int(row["new_denominator_capacity"]) for row in selected
                ),
                "numerator_min": num_min,
                "numerator_max": num_max,
                "denominator_min": den_min,
                "denominator_max": den_max,
                "rate_lower": lower,
                "rate_upper": upper,
                "current_projection_ablation_lower": ablation_lower,
                "current_projection_ablation_upper": ablation_upper,
                "current_projection_ablation_numerator_min": ablation_num_lower,
                "current_projection_ablation_numerator_max": ablation_num_upper,
                "current_projection_ablation_denominator": ablation_den,
                "current_projection_ablation_max_shift_pp": max(
                    abs(ablation_lower - baseline),
                    abs(ablation_upper - baseline),
                ) * 100,
                "max_absolute_shift_pp": max(
                    abs(lower - baseline),
                    abs(upper - baseline),
                ) * 100,
                "material_ge_1pp": max(
                    abs(lower - baseline),
                    abs(upper - baseline),
                ) * 100 >= 1.0,
            })
    return output


def module_for(path: str) -> str:
    parts = PurePosixPath(path).parts
    return parts[0] if len(parts) > 1 else "repo-root-files"


def rq3_sensitivity(
    events_by_project: dict[str, list[dict[str, Any]]],
    event_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    row_by_key = {
        (str(row["project"]), str(row["event_id"])): row for row in event_rows
    }
    output: list[dict[str, object]] = []
    for scope_name, scope_field in [
        ("broad", "broad_compound_wrapper"),
        ("heldout_trigger", "heldout_trigger"),
    ]:
        for project, events in events_by_project.items():
            base_calls: dict[tuple[str, str], dict[str, object]] = {}
            possible_calls: dict[tuple[str, str], dict[str, object]] = {}
            risky_ids = {
                str(row["event_id"])
                for row in event_rows
                if row["project"] == project
                and row[scope_field]
                and row["contains_path_operand"]
                and row["status"] in {"ok", "observed"}
            }
            for event_index, event in enumerate(events):
                if str(event.get("status") or "observed") not in {"ok", "observed"}:
                    continue
                event_id = str(event["id"])
                by_worktree: dict[str, dict[str, set[str]]] = defaultdict(
                    lambda: {"paths": set(), "modules": set()}
                )
                for action in event.get("actions", []):
                    if (
                        action.get("scope")
                        or not action.get("worktree_id")
                        or not action.get("path")
                    ):
                        continue
                    worktree = str(action["worktree_id"])
                    path = str(action["path"])
                    by_worktree[worktree]["paths"].add(path)
                    by_worktree[worktree]["modules"].add(module_for(path))
                for worktree, values in by_worktree.items():
                    key = (worktree, event_id)
                    base_calls[key] = {
                        "event_index": event_index,
                        "paths": values["paths"],
                        "modules": values["modules"],
                        "risky": event_id in risky_ids,
                    }
                    possible_calls[key] = base_calls[key]
                row = row_by_key[(project, event_id)]
                home = str(event.get("worktree_id") or "")
                if (
                    event_id in risky_ids
                    and bool(row["contains_path_operand"])
                    and home
                    and (home, event_id) not in possible_calls
                ):
                    possible_calls[(home, event_id)] = {
                        "event_index": event_index,
                        "paths": set(),
                        "modules": set(),
                        "risky": True,
                    }

            def lanes(calls: dict[tuple[str, str], dict[str, object]]) -> dict[
                str, list[dict[str, object]]
            ]:
                result: dict[str, list[dict[str, object]]] = defaultdict(list)
                for (worktree, _), call in calls.items():
                    result[worktree].append(call)
                for values in result.values():
                    values.sort(key=lambda row: int(row["event_index"]))
                return result

            base_local = 0
            base_cross = 0
            current_unchanged_local = 0
            current_unchanged_cross = 0
            for values in lanes(base_calls).values():
                for previous, current in zip(values, values[1:]):
                    if previous["paths"] & current["paths"]:
                        base_local += 1
                        if not previous["risky"] and not current["risky"]:
                            current_unchanged_local += 1
                    elif previous["modules"] & current["modules"]:
                        base_local += 1
                        if not previous["risky"] and not current["risky"]:
                            current_unchanged_local += 1
                    else:
                        base_cross += 1
                        if not previous["risky"] and not current["risky"]:
                            current_unchanged_cross += 1
            unchanged_local = 0
            unchanged_cross = 0
            max_transitions = 0
            uncertain = 0
            for values in lanes(possible_calls).values():
                max_transitions += max(0, len(values) - 1)
                for previous, current in zip(values, values[1:]):
                    if previous["risky"] or current["risky"]:
                        uncertain += 1
                        continue
                    if previous["paths"] & current["paths"]:
                        unchanged_local += 1
                    elif previous["modules"] & current["modules"]:
                        unchanged_local += 1
                    else:
                        unchanged_cross += 1
            base_total = base_local + base_cross
            baseline = base_local / base_total if base_total else math.nan
            lower = unchanged_local / max_transitions if max_transitions else math.nan
            upper = (
                1.0 - unchanged_cross / max_transitions
                if max_transitions
                else math.nan
            )
            relabel_lower = (
                current_unchanged_local / base_total if base_total else math.nan
            )
            relabel_upper = (
                1.0 - current_unchanged_cross / base_total
                if base_total
                else math.nan
            )
            output.append({
                "scope": scope_name,
                "project": project,
                "baseline_path_calls": len(base_calls),
                "baseline_transitions": base_total,
                "baseline_local": base_local,
                "baseline_cross_module": base_cross,
                "baseline_locality": baseline,
                "risk_path_calls_current_or_possible": sum(
                    bool(call["risky"]) for call in possible_calls.values()
                ),
                "max_transitions_after_admission": max_transitions,
                "unchanged_local_transitions": unchanged_local,
                "unchanged_cross_transitions": unchanged_cross,
                "uncertain_adjacent_transitions_at_max_admission": uncertain,
                "locality_lower": lower,
                "locality_upper": upper,
                "current_projection_relabel_lower": relabel_lower,
                "current_projection_relabel_upper": relabel_upper,
                "current_projection_relabel_max_shift_pp": max(
                    abs(relabel_lower - baseline),
                    abs(relabel_upper - baseline),
                ) * 100,
                "max_absolute_shift_pp": max(
                    abs(lower - baseline),
                    abs(upper - baseline),
                ) * 100,
                "material_ge_1pp": max(
                    abs(lower - baseline),
                    abs(upper - baseline),
                ) * 100 >= 1.0,
            })
    return output


def rq4_sensitivity(
    rq4_root: Path,
    event_rows: list[dict[str, object]],
    events_by_project: dict[str, list[dict[str, Any]]],
) -> list[dict[str, object]]:
    boundaries = read_csv(rq4_root / "rq4-boundaries.csv")
    components = read_csv(rq4_root / "rq4-components.csv")
    projects = sorted({row["project"] for row in components})
    output: list[dict[str, object]] = []

    def component_counts(
        project: str,
        risky_ids: set[str],
    ) -> tuple[int, int]:
        by_session: dict[tuple[str, str], list[int]] = defaultdict(list)
        for event in events_by_project[project]:
            event_id = str(event["id"])
            home = str(event.get("worktree_id") or "")
            if event_id in risky_ids:
                targets = {home} if home else set()
            else:
                targets = {
                    str(action["worktree_id"])
                    for action in event.get("actions", [])
                    if action.get("worktree_id")
                }
                if home:
                    targets.add(home)
            for worktree in targets:
                by_session[(worktree, str(event["session_id"]))].append(
                    int(event["ts_ms"])
                )
        intervals: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for (worktree, _session), timestamps in by_session.items():
            intervals[worktree].append((min(timestamps), max(timestamps)))
        component_n = 0
        boundary_n = 0
        for values in intervals.values():
            values.sort()
            lane_components = 0
            current_end: int | None = None
            for start, end in values:
                if current_end is None or start > current_end:
                    lane_components += 1
                    current_end = end
                else:
                    current_end = max(current_end, end)
            component_n += lane_components
            boundary_n += max(0, lane_components - 1)
        return component_n, boundary_n

    for scope_name, scope_field in [
        ("broad", "broad_compound_wrapper"),
        ("heldout_trigger", "heldout_trigger"),
    ]:
        for project in projects:
            project_boundaries = [row for row in boundaries if row["project"] == project]
            project_components = [row for row in components if row["project"] == project]
            replay_components, replay_boundaries = component_counts(project, set())
            if (
                replay_components != len(project_components)
                or replay_boundaries != len(project_boundaries)
            ):
                raise ValueError(
                    f"RQ4 component replay diverged for {project}: "
                    f"{replay_components}/{replay_boundaries} vs "
                    f"{len(project_components)}/{len(project_boundaries)}"
                )
            risk_rows = [
                row
                for row in event_rows
                if row["project"] == project
                and row[scope_field]
                and row["contains_path_operand"]
            ]
            risky_ids = {str(row["event_id"]) for row in risk_rows}
            remote_target_events = 0
            for row in risk_rows:
                event = row["_event"]
                home = str(event.get("worktree_id") or "")
                targets = {
                    str(action["worktree_id"])
                    for action in event.get("actions", [])
                    if action.get("path") and action.get("worktree_id")
                }
                if any(target != home for target in targets):
                    remote_target_events += 1
            ablated_components, ablated_boundaries = component_counts(
                project,
                risky_ids,
            )
            known_worktrees = {
                str(event.get("worktree_id"))
                for event in events_by_project[project]
                if event.get("worktree_id")
            } | {
                str(action["worktree_id"])
                for event in events_by_project[project]
                for action in event.get("actions", [])
                if action.get("worktree_id")
            }
            risky_sessions = {
                str(row["session_id"]) for row in risk_rows
            }
            reassignment_capacity = len(risky_sessions) * max(
                0,
                len(known_worktrees) - 1,
            )
            # The v2 failure class changes path admission inside the already
            # attributed event/worktree.  RQ4 components and boundary counts
            # are functions of source-session intervals, not path labels.
            output.append({
                "scope": scope_name,
                "project": project,
                "baseline_components": len(project_components),
                "baseline_boundaries": len(project_boundaries),
                "risk_path_actions": len(risk_rows),
                "risk_events_with_projected_nonhome_target": remote_target_events,
                "current_projection_path_ablation_components": ablated_components,
                "current_projection_path_ablation_boundaries": ablated_boundaries,
                "current_projection_path_ablation_boundary_shift": (
                    ablated_boundaries - len(project_boundaries)
                ),
                "scope_preserving_component_shift_upper": 0,
                "scope_preserving_boundary_shift_upper": 0,
                "known_worktrees": len(known_worktrees),
                "risky_sessions": len(risky_sessions),
                "cross_worktree_reassignment_capacity": reassignment_capacity,
                "material_for_boundary_count_scope_preserving": False,
                "cross_worktree_boundary_bound": "out_of_v2_boundary_not_estimated",
                "note": (
                    "Path-label/admission correction within the event's attributed "
                    "worktree cannot change source-session component or boundary count."
                ),
            })
    return output


def heldout_modes(v2_root: Path) -> list[dict[str, object]]:
    edge_diff = read_csv(v2_root / "raw/full/edge-diff.csv")
    calls: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in edge_diff:
        calls[(row["project"], row["call_id"])].append(row)
    projection_dir = v2_root / "private/full/projection/raw/events"
    event_lookup: dict[tuple[str, str], dict[str, Any]] = {}
    for path in sorted(projection_dir.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        project = str(document["repository"])
        for event in document["events"]:
            event_lookup[(project, str(event.get("source_call_id") or ""))] = event
    output: list[dict[str, object]] = []
    for (project, call_id), diffs in sorted(calls.items()):
        event = event_lookup[(project, call_id)]
        command = str(event.get("command") or "")
        facts = segment_facts(str(event.get("tool_name") or ""), command)
        missing = sum(int(row["count"]) for row in diffs if row["diff"] == "missing_from_projection")
        extra = sum(int(row["count"]) for row in diffs if row["diff"] == "extra_in_projection")
        output.append({
            "project": project,
            "vendor": str(event.get("vendor") or ""),
            "call_id": call_id,
            "tool_name": str(event.get("tool_name") or ""),
            "status": str(event.get("status") or ""),
            "missing_edges": missing,
            "extra_edges": extra,
            "diff_accesses": ";".join(sorted({row["access"] for row in diffs})),
            "diff_paths": ";".join(sorted({row["path"] for row in diffs})),
            "shape_flags": ";".join(
                name
                for name, value in facts.items()
                if value and name not in {"broad_compound_wrapper", "heldout_trigger"}
            ),
            "command_sha256": hashlib.sha256(command.encode()).hexdigest(),
            "command_preview": re.sub(r"\s+", " ", command).strip()[:400],
        })
    return output


def self_check() -> None:
    multi = "cp src/a.c src/b.c out/ 2>&1"
    facts = segment_facts("Bash", multi)
    assert facts["multisource_cp_mv"]
    assert facts["redirection_file_command"]
    effects = command_effects("Bash", multi)
    assert ("read", "src/a.c") in effects
    assert ("read", "src/b.c") in effects
    assert sum(access == "create" for access, _ in effects) == 2
    assert not any(path in {"1", "2", ">&"} for _, path in effects)

    assert segment_facts(
        "exec_command",
        "git rm -r --ignore-unmatch docs/tree",
    )["recursive_multi_git_rm"]
    assert segment_facts(
        "Bash",
        "diff <(sed -n '1p' a.txt) <(sed -n '1p' b.txt)",
    )["process_substitution"]
    assert segment_facts("Bash", "\\\n# comment\nsed -n '1p' a.txt")[
        "leading_backslash"
    ]
    wrapped = (
        'const rs=await Promise.all(['
        'tools.exec_command({cmd:"cat a.md"}),'
        'tools.exec_command({cmd:"cat b.md"})]);'
    )
    assert len(nested_shell_commands(wrapped)) == 2
    assert segment_facts("exec", wrapped)["multi_exec_envelope"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--recompute-root",
        type=Path,
        default=Path("docs/tmp/build-and-evaluate/rq1-rq4-recompute-final"),
    )
    parser.add_argument(
        "--v2-root",
        type=Path,
        default=Path("docs/tmp/build-and-evaluate/rq7-heldout-20260726/v2"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/tmp/build-and-evaluate/shell-boundary-audit-20260726"),
    )
    args = parser.parse_args()
    self_check()
    events_dir = args.recompute_root / "rq1-raw/events"
    rows, events_by_project, input_hashes = load_corpus(events_dir)
    if len(rows) != 181_303:
        raise ValueError(f"unexpected final-HEAD Tool-action count: {len(rows)}")

    exposure_rows = [
        public_event_row(row)
        for row in rows
        if row["broad_compound_wrapper"] or row["heldout_trigger"]
    ]
    exposure_fields = list(exposure_rows[0])
    write_csv(args.output / "compound_actions.csv", exposure_rows, exposure_fields)

    summary_rows = exposure_summary(rows)
    write_csv(
        args.output / "exposure_summary.csv",
        summary_rows,
        list(summary_rows[0]),
    )

    rq1_rows = rq1_sensitivity(args.recompute_root / "rq1-raw", rows)
    write_csv(
        args.output / "rq1_sensitivity.csv",
        rq1_rows,
        list(rq1_rows[0]),
    )

    rq3_rows = rq3_sensitivity(events_by_project, rows)
    write_csv(
        args.output / "rq3_sensitivity.csv",
        rq3_rows,
        list(rq3_rows[0]),
    )

    rq4_rows = rq4_sensitivity(
        args.recompute_root / "rq4/raw",
        rows,
        events_by_project,
    )
    write_csv(
        args.output / "rq4_sensitivity.csv",
        rq4_rows,
        list(rq4_rows[0]),
    )

    mode_rows = heldout_modes(args.v2_root)
    write_csv(
        args.output / "heldout_failure_modes.csv",
        mode_rows,
        list(mode_rows[0]),
    )

    provenance_rows = [
        {"input": name, "sha256": digest}
        for name, digest in sorted(input_hashes.items())
    ]
    provenance_paths = [
        args.recompute_root / "rq1-raw/projects.json",
        args.recompute_root / "rq1-raw/rq1-summary.csv",
        args.recompute_root / "rq1-raw/rq1-artifacts.csv",
        args.recompute_root / "rq1-raw/rq1-mutations.csv",
        args.recompute_root / "rq4/raw/rq4-components.csv",
        args.recompute_root / "rq4/raw/rq4-boundaries.csv",
        args.recompute_root / "commands.log",
        args.v2_root / "protocol.md",
        args.v2_root / "result.md",
        args.v2_root / "result-review.md",
        args.v2_root / "raw/full/edge-diff.csv",
        Path("docs/paper/main.tex"),
        Path("docs/paper/supplement.tex"),
        Path(
            "docs/tmp/bootstrap/step-0002-20260722T182000-0700/"
            "experiment-rq6-external-boundary/local-anchor.csv"
        ),
        *sorted(
            (args.v2_root / "private/full/projection/raw/events").glob("*.json")
        ),
    ]
    for path in provenance_paths:
        provenance_rows.append({
            "input": str(path),
            "sha256": sha256(path),
        })
    write_csv(
        args.output / "input_provenance.csv",
        provenance_rows,
        ["input", "sha256"],
    )

    print(json.dumps({
        "tool_actions": len(rows),
        "compound_rows": len(exposure_rows),
        "outputs": [
            "compound_actions.csv",
            "exposure_summary.csv",
            "rq1_sensitivity.csv",
            "rq3_sensitivity.csv",
            "rq4_sensitivity.csv",
            "heldout_failure_modes.csv",
            "input_provenance.csv",
        ],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
