#!/usr/bin/env python3
"""One-attempt v4 held-out conformance runner for the 2026-07-26 P1 audit.

All writes are confined to this experiment directory.  The script reuses the
reviewed RQ7 experiment glue and independent source checker, but freezes the
new 6x12 corpus and evaluates display lineage in the exact edge key.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


# The user authorized writes only below EXPERIMENT.  Set this before importing
# either local oracle module or ProcGrep adapters.
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

EXPERIMENT = Path(__file__).resolve().parents[1]
REPOSITORY = Path(__file__).resolve().parents[5]
PRIVATE = EXPERIMENT / "private"
PROJECTS_FILE = EXPERIMENT / "heldout-projects.json"
PROCGREP = Path("/tmp/procgrep-eval-2e827")

SPEC_VERSION = "native-root-conformance-v4"
SELECTION_SEED = "20260726-heldout-v4-001"
PROJECT_COUNT = 6
ROOTS_PER_PROJECT = 12
SOURCE_BYTES_CAP = 268_435_456
STABILITY_SECONDS = 60
DISCOVERY_CUTOFF_NS = 1_785_107_836_380_493_543
PROJECTS_SHA256 = "2de529d002815aefa74b1b8f8164ddf3b78b1e2f8e9e02214d43a9598f49368a"
PROCGREP_REVISION = "2e8277003dacaa774b5ef61ba150ae03a4f06693"
PROCGREP_LOCK_SHA256 = "e13620baf50cf9fbd6372128f3a6a020ae36d16ebceae22cc8a853d9ab8d73c3"

EXCLUSIONS = (
    (
        REPOSITORY
        / "docs/tmp/build-and-evaluate/step-0004-20260723T181008-0700/"
        "experiment-001/private/freeze.json",
        "838b814a31be1be48d28040d12235ee16489081f1d7214e8c7e814f8da057e35",
    ),
    (
        REPOSITORY
        / "docs/tmp/build-and-evaluate/step-0005-20260723T203751-0700/"
        "experiment-001/private/freeze.json",
        "2a7148ee78d0a0fadb99c768cbf6bda9fea2dce6e1ce844a8ae953e0fea38767",
    ),
    (
        REPOSITORY
        / "docs/tmp/build-and-evaluate/step-0005-20260723T203751-0700/"
        "experiment-002/private/freeze.json",
        "1d58ac89ceb074efdaea782a00e86cfbdb2f2a5d968a172623089d2d11a02d59",
    ),
)

FROZEN_CODE_HASHES = {
    "agentvis/research/rq7_measurement.py":
        "e50adb5cb3882e8eca83295a80716f9db4a73290de7fe648aeef5d79ed1f9240",
    "agentvis/research/rq7_source_oracle_check.py":
        "bf12c98ec60b97c9ce4997b892288f65c10ffa8a1572b855b8ca8f92113e61cc",
    "agent-session/src/parser.rs":
        "62cb20600b628dbe83c7f6c9b1556f5c899292963f202df984c4456695db798b",
    "agentvis/src/repository.rs":
        "313e8fbe92eb966e44522f1de3635b5c6e8a362f28b68dc1eca7d1bf8b69ce6c",
    "agent-session/tests/fixtures/strict-action-grammar.json":
        "685ccbfe5c601a5e02fca0f02700699b2bb31125110770c8ece71bdb7a6934a7",
    "agentvis/Cargo.lock":
        "c117357cf567baad5a8867f8def4d43a5f4733f1904d94a2c4cf662243553143",
}


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


measurement = load_module(
    "rq7_measurement_heldout_v4",
    REPOSITORY / "agentvis/research/rq7_measurement.py",
)
checker = load_module(
    "rq7_source_oracle_heldout_v4",
    REPOSITORY / "agentvis/research/rq7_source_oracle_check.py",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )


def write_csv(
    path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def run(
    command: list[str],
    *,
    cwd: Path = REPOSITORY,
    env: dict[str, str] | None = None,
) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {shlex.join(command)}\n"
            f"{result.stdout[-12000:]}"
        )
    return result.stdout


def verify_frozen_code() -> None:
    mismatches = {}
    for relative, expected in FROZEN_CODE_HASHES.items():
        actual = sha256_file(REPOSITORY / relative)
        if actual != expected:
            mismatches[relative] = {"expected": expected, "actual": actual}
    if mismatches:
        raise RuntimeError(f"frozen projection code changed: {mismatches}")
    if sha256_file(PROJECTS_FILE) != PROJECTS_SHA256:
        raise RuntimeError("heldout-projects.json changed after registration")
    if run(["git", "diff", "--quiet", "--", "agent-session", "agentvis"]):
        raise RuntimeError("unexpected output from projection-tree diff check")
    if run(["git", "-C", str(PROCGREP), "rev-parse", "HEAD"]).strip() != PROCGREP_REVISION:
        raise RuntimeError("ProcGrep revision mismatch")
    if sha256_file(PROCGREP / "uv.lock") != PROCGREP_LOCK_SHA256:
        raise RuntimeError("ProcGrep lock mismatch")
    if checker.SPEC_VERSION != SPEC_VERSION:
        raise RuntimeError(
            f"independent checker is {checker.SPEC_VERSION}, expected {SPEC_VERSION}"
        )
    protocol = (EXPERIMENT / "protocol.md").read_text()
    match = re.search(
        r"Held-out v4 runner SHA-256 \| `([0-9a-f]{64})`", protocol
    )
    if match is None or match.group(1) != sha256_file(Path(__file__)):
        raise RuntimeError("runner does not match the hash frozen in protocol.md")


def question_spec_v4() -> str:
    return """# RQ7 Held-Out Native-Root Conformance v4

Specification ID: `native-root-conformance-v4`.

All facts are derived only from the 72 hash-sealed held-out native files and
the six cutoff workspace manifests. A semantic session is `(vendor,
native_root_session_id)`; a source stream is provenance. Codex root precedence
is `session_id`, `parent_thread_id`, `thread_id`, then `id`. Sessions are
ordered by first included Tool timestamp and semantic root. Tool events are
ordered by timestamp, stable source-stream ID, source Tool ordinal, and native
record/call position.

Tool calls are attempted actions regardless of result. Status is `ok`, `fail`,
or `observed`; only `ok` establishes a confirmed effect. Exact paths come only
from declared structured path fields, patch headers, and direct operands of
cat/sed/head/tail/nl/less/more/touch/rm/mv/cp. Event workdir overrides session
cwd. Simple lexical inline `cd` changes the base for later direct file
commands. Dynamic/ambiguous cwd, paths outside the worktree, variables, globs,
search scopes, redirections, and heredocs are excluded. Static Codex
exec/apply_patch wrappers are decoded without evaluating JavaScript.

Actions in one call are ordered rename-source, rename-destination, then
lexicographic `(path, access, previous_path)`. Confirmed same-worktree rename
transfers identity. Confirmed delete followed by create starts a generation.
Failed/observed mutations remain attempted edges but do not change lifecycle
state.

For each held-out case, P0--P4 are newly ranked by distinct attempted calls;
the existing frozen HMAC path-ID rule breaks ties. A1--A5 are action counts and
order predicates. B1--B5 are attempted-call/read/mutation/first-class/session
facts for the new P0. C1--C5 are adjacent sharing, later revisit, P0 return,
P0 session span, and multi-session identity facts. D1--D5 are
tracked/untracked/absent for the new P0--P4 at cutoff.

Canonical answers are base-10 integers or exactly `read`, `mutate`, `tracked`,
`untracked`, `absent`.
"""


def primary_json_string(text: str, opening: int) -> tuple[str, int] | None:
    """Decode one static JSON-compatible double-quoted JavaScript string."""

    if opening >= len(text) or text[opening] != '"':
        return None
    escaped = False
    for index in range(opening + 1, len(text)):
        character = text[index]
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == '"':
            try:
                value = json.loads(text[opening:index + 1])
            except json.JSONDecodeError:
                return None
            return (value, index + 1) if isinstance(value, str) else None
    return None


def primary_wrapped_patch(text: str) -> str | None:
    assignment = re.compile(
        r"\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*"
    )
    for match in assignment.finditer(text):
        decoded = primary_json_string(text, match.end())
        if decoded is None:
            continue
        value, _ = decoded
        variable = re.escape(match.group(1))
        if (
            "*** Begin Patch" in value
            and re.search(
                rf"\btools\.apply_patch\s*\(\s*{variable}\s*\)", text
            )
        ):
            return value
    return None


def primary_normalized_arguments(
    name: str, args: dict[str, Any]
) -> dict[str, Any]:
    if name.lower() != "exec":
        return args
    text = measurement.command_text(name, args)
    patch = primary_wrapped_patch(text)
    nested = measurement.embedded_exec_arguments(text)
    normalized = dict(nested or args)
    if patch is not None:
        normalized["_heldout_wrapped_patch"] = patch
    return normalized


def primary_tool_atom(name: str, args: dict[str, Any]) -> str:
    lower = name.lower()
    if lower in {"read", "notebookread", "read_file"}:
        return "read_file"
    if lower in {
        "edit",
        "write",
        "notebookedit",
        "multiedit",
        "apply_patch",
    }:
        return "edit"
    if lower in {
        "grep",
        "glob",
        "websearch",
        "webfetch",
        "search_file_content",
        "list_directory",
    }:
        return "search_repo"
    if lower in {
        "todowrite",
        "exitplanmode",
        "update_plan",
        "write_todos",
        "exit_plan_mode",
    }:
        return "think"
    if lower in {
        "bash",
        "exec",
        "exec_command",
        "shell_command",
        "run_shell_command",
        "shell",
    }:
        if isinstance(args.get("_heldout_wrapped_patch"), str):
            return "edit"
        return measurement.command_atom(measurement.command_text(name, args))
    return "other"


def primary_shell_actions(
    command: str, cwd: str
) -> list[dict[str, str | None]]:
    actions: list[dict[str, str | None]] = []
    shell_cwd = cwd
    cwd_known = True
    for segment in measurement.shell_segments(command):
        if not segment or any(
            token and set(token) <= {"<", ">"} for token in segment
        ):
            continue
        executable = segment[0].rsplit("/", 1)[-1].lower()
        if executable == "cd":
            operands = [
                token
                for token in segment[1:]
                if token != "--" and not token.startswith("-")
            ]
            if (
                len(operands) != 1
                or any(character in operands[0] for character in "$*?[]{}<>")
                or operands[0].startswith("~")
            ):
                cwd_known = False
                continue
            target = Path(operands[0])
            if not target.is_absolute():
                if not cwd_known:
                    continue
                target = Path(shell_cwd) / target
            shell_cwd = os.path.normpath(str(target))
            cwd_known = True
            continue
        if executable not in measurement.READ_COMMANDS | measurement.MUTATE_COMMANDS:
            continue
        operands = measurement.file_operands(executable, segment[1:])
        qualified = []
        for operand in operands:
            if Path(operand).is_absolute():
                qualified.append(operand)
            elif cwd_known:
                qualified.append(os.path.normpath(str(Path(shell_cwd) / operand)))
        if executable in {"mv", "cp"}:
            if len(qualified) < 2:
                continue
            source, destination = qualified[-2:]
            if executable == "mv":
                actions.extend(
                    [
                        {
                            "path": source,
                            "access": "rename_from",
                            "previous_path": None,
                        },
                        {
                            "path": destination,
                            "access": "rename",
                            "previous_path": source,
                        },
                    ]
                )
            else:
                actions.extend(
                    [
                        {"path": source, "access": "read", "previous_path": None},
                        {
                            "path": destination,
                            "access": "create",
                            "previous_path": None,
                        },
                    ]
                )
            continue
        access = (
            "read"
            if executable in measurement.READ_COMMANDS
            else ("delete" if executable == "rm" else "create")
        )
        actions.extend(
            {
                "path": operand,
                "access": access,
                "previous_path": None,
            }
            for operand in qualified
        )
    return actions


def primary_event_actions(
    event: dict[str, Any],
) -> list[dict[str, str | None]]:
    if event.get("kind") != "tool":
        return []
    name = str(event.get("tool") or "").lower()
    args = event.get("args") if isinstance(event.get("args"), dict) else {}
    command = measurement.command_text(name, args)
    wrapped = args.get("_heldout_wrapped_patch")
    shell_tools = {
        "bash",
        "exec",
        "exec_command",
        "shell_command",
        "run_shell_command",
        "shell",
    }
    actions: list[dict[str, str | None]] = []
    if name in shell_tools and not isinstance(wrapped, str):
        actions.extend(
            primary_shell_actions(command, str(event.get("workdir") or ""))
        )
    is_patch = name == "apply_patch" or (
        name in shell_tools
        and (isinstance(wrapped, str) or "*** Begin Patch" in command)
    )
    if is_patch:
        patch = (
            wrapped
            if isinstance(wrapped, str)
            else command or str(args.get("patch") or "")
        )
        pending_update: str | None = None
        for raw_line in patch.splitlines():
            line = raw_line.strip()
            matched = measurement.PATCH_RE.fullmatch(line)
            if matched:
                kind, raw_path = matched.groups()
                path = raw_path.strip()
                access = {
                    "Add": "create",
                    "Update": "write",
                    "Delete": "delete",
                }[kind]
                actions.append(
                    {"path": path, "access": access, "previous_path": None}
                )
                pending_update = path if kind == "Update" else None
                continue
            moved = measurement.MOVE_RE.fullmatch(line)
            if moved and pending_update:
                actions = [
                    action
                    for action in actions
                    if not (
                        action["path"] == pending_update
                        and action["access"] == "write"
                    )
                ]
                actions.extend(
                    [
                        {
                            "path": pending_update,
                            "access": "rename_from",
                            "previous_path": None,
                        },
                        {
                            "path": moved.group(1).strip(),
                            "access": "rename",
                            "previous_path": pending_update,
                        },
                    ]
                )
                pending_update = None
    structured_access = {
        "read": "read",
        "notebookread": "read",
        "read_file": "read",
        "edit": "write",
        "notebookedit": "write",
        "multiedit": "write",
        "write": "create",
        "write_file": "create",
    }.get(name)
    if structured_access:
        actions.extend(
            {
                "path": path,
                "access": structured_access,
                "previous_path": None,
            }
            for path in measurement.structured_paths(args)
        )
    unique: dict[tuple[str, str, str | None], dict[str, str | None]] = {}
    for action in actions:
        unique[
            (
                str(action["path"]),
                str(action["access"]),
                action.get("previous_path"),
            )
        ] = action
    priority = {"rename_from": 0, "rename": 1}
    return sorted(
        unique.values(),
        key=lambda action: (
            priority.get(str(action["access"]), 2),
            str(action["path"]),
            str(action["access"]),
            str(action.get("previous_path") or ""),
        ),
    )


def configure_v4_primary() -> None:
    """Install an implementation independent of the standalone v4 checker."""

    measurement.SPEC_VERSION = SPEC_VERSION
    measurement.normalized_tool_arguments = primary_normalized_arguments
    measurement.tool_atom = primary_tool_atom
    measurement.event_path_actions = primary_event_actions
    measurement.question_spec = question_spec_v4


def v4_primary_fixture_gate() -> dict[str, Any]:
    """Exercise the v4-only primary grammar before any corpus is selected."""

    fixtures = [
        {
            "name": "inline-cd-relative-read",
            "tool": "exec_command",
            "args": {"cmd": "cd src; cat lib.rs"},
            "workdir": "/fixture",
            "atom": "other",
            "actions": [
                {
                    "path": "/fixture/src/lib.rs",
                    "access": "read",
                    "previous_path": None,
                }
            ],
        },
        {
            "name": "inline-cd-dynamic-cwd-excluded",
            "tool": "exec_command",
            "args": {"cmd": "cd \"$TARGET\"; cat lib.rs"},
            "workdir": "/fixture",
            "atom": "other",
            "actions": [],
        },
        {
            "name": "wrapped-static-apply-patch",
            "tool": "exec",
            "args": {
                "command": (
                    'const patch = "*** Begin Patch\\n*** Update File: old.txt'
                    '\\n*** Move to: new.txt\\n*** End Patch"; '
                    "const result = await tools.apply_patch(patch);"
                )
            },
            "workdir": "/fixture",
            "atom": "edit",
            "actions": [
                {
                    "path": "old.txt",
                    "access": "rename_from",
                    "previous_path": None,
                },
                {
                    "path": "new.txt",
                    "access": "rename",
                    "previous_path": "old.txt",
                },
            ],
        },
        {
            "name": "wrapped-exec-envelope-after-inline-cd",
            "tool": "exec",
            "args": {
                "command": (
                    'const result = await tools.exec_command('
                    '{"cmd":"cd docs; cat guide.md","workdir":"/fixture"});'
                )
            },
            "workdir": "/ignored",
            "atom": "other",
            "actions": [
                {
                    "path": "/fixture/docs/guide.md",
                    "access": "read",
                    "previous_path": None,
                }
            ],
        },
    ]
    configure_v4_primary()
    checked = []
    for fixture in fixtures:
        name = str(fixture["tool"])
        primary_args = primary_normalized_arguments(name, fixture["args"])
        independent_args = checker.unwrap_exec(name, fixture["args"])
        primary_event = {
            "kind": "tool",
            "tool": name,
            "args": primary_args,
            "workdir": str(primary_args.get("workdir") or fixture["workdir"]),
        }
        independent_event = {
            "kind": "tool",
            "name": name,
            "args": independent_args,
            "cwd": str(independent_args.get("workdir") or fixture["workdir"]),
        }
        primary_actions = primary_event_actions(primary_event)
        independent_actions = [
            {"path": path, "access": access, "previous_path": previous}
            for path, access, previous in checker.event_effects(independent_event)
        ]
        primary_atom = primary_tool_atom(name, primary_args)
        independent_atom = checker.atom_for(name, independent_args)
        expected_actions = fixture["actions"]
        expected_atom = fixture["atom"]
        if (
            primary_actions != expected_actions
            or independent_actions != expected_actions
            or primary_atom != expected_atom
            or independent_atom != expected_atom
        ):
            raise RuntimeError(
                f"v4 primary fixture mismatch {fixture['name']}: "
                f"primary_actions={primary_actions}, "
                f"independent_actions={independent_actions}, "
                f"primary_atom={primary_atom}, independent_atom={independent_atom}, "
                f"expected_actions={expected_actions}, expected_atom={expected_atom}"
            )
        checked.append(str(fixture["name"]))
    return {"count": len(checked), "fixtures": checked}


def fixture_environment(cargo_target: Path) -> dict[str, str]:
    """Keep fixture build products and Python caches inside the experiment."""

    environment = os.environ.copy()
    environment["CARGO_TARGET_DIR"] = str(cargo_target)
    environment["CARGO_NET_OFFLINE"] = "true"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def source_native_root(
    vendor: str, path: Path, fallback: str
) -> tuple[str, Any]:
    native = measurement.load_json_or_jsonl(path)
    return measurement.native_root_from_path(vendor, path, fallback), native


def exclusion_sets() -> tuple[
    set[str], set[tuple[str, str]], set[tuple[str, str, str]], list[dict[str, Any]]
]:
    hashes: set[str] = set()
    roots: set[tuple[str, str]] = set()
    calls: set[tuple[str, str, str]] = set()
    audit = []
    for freeze_path, expected_hash in EXCLUSIONS:
        actual_hash = sha256_file(freeze_path)
        if actual_hash != expected_hash:
            raise RuntimeError(f"exclusion manifest hash mismatch: {freeze_path}")
        freeze = read_json(freeze_path)
        archive = freeze_path.parent / "frozen-home"
        source_count = 0
        for project in freeze["projects"]:
            for source in project["sources"]:
                source_count += 1
                vendor = str(source["vendor"])
                archived = archive / str(source.get("home_relative") or "")
                if not archived.is_file():
                    raise RuntimeError(f"missing exclusion source: {archived}")
                if (
                    archived.stat().st_size != int(source["bytes"])
                    or sha256_file(archived) != str(source["sha256"])
                ):
                    raise RuntimeError(f"exclusion source integrity failure: {archived}")
                native_root, native = source_native_root(
                    vendor, archived, str(source["native_session_id"])
                )
                hashes.add(str(source["sha256"]))
                roots.add((vendor, native_root))
                events = measurement.native_events(
                    vendor,
                    archived,
                    {"worktree": str(project["worktree"])},
                )
                calls.update(
                    (vendor, native_root, str(event["call_id"]))
                    for event in events
                    if event.get("kind") == "tool"
                )
        audit.append(
            {
                "path": str(freeze_path),
                "sha256": actual_hash,
                "sources": source_count,
            }
        )
    return hashes, roots, calls, audit


def old_question_signatures() -> set[str]:
    freeze = read_json(EXCLUSIONS[0][0])
    return {
        sha256_bytes(
            json.dumps(
                {
                    key: row.get(key)
                    for key in (
                        "project",
                        "family",
                        "template",
                        "answer",
                        "p0_path",
                        "p0_path_id",
                        "path_id",
                        "witnesses",
                    )
                },
                sort_keys=True,
            ).encode()
        )
        for row in freeze["questions"]
    }


def freeze_corpus() -> dict[str, Any]:
    verify_frozen_code()
    configure_v4_primary()
    fixture_attempt_path = EXPERIMENT / "check-fixtures-attempt.json"
    if not fixture_attempt_path.is_file():
        raise RuntimeError("freeze requires the unique completed fixture attempt")
    fixture_attempt = read_json(fixture_attempt_path)
    if (
        fixture_attempt.get("terminal_status") != "complete"
        or fixture_attempt.get("runner_sha256") != sha256_file(Path(__file__))
        or (fixture_attempt.get("result") or {}).get("status") != "pass"
    ):
        raise RuntimeError("fixture attempt did not pass with the frozen runner")
    release = EXPERIMENT / "raw/freeze"
    if PRIVATE.exists() or release.exists():
        raise RuntimeError("freeze outputs are append-only")
    PRIVATE.mkdir(parents=True)
    release.mkdir(parents=True)

    excluded_hashes, excluded_roots, excluded_calls, exclusion_audit = (
        exclusion_sets()
    )
    project_input = read_json(PROJECTS_FILE)
    if not isinstance(project_input, list) or len(project_input) != PROJECT_COUNT:
        raise RuntimeError("project inventory must contain exactly six cases")

    roots_by_project: dict[str, list[Path]] = {}
    for row in project_input:
        roots_by_project[row["project"]] = measurement.worktrees(
            measurement.canonical(Path(row["repository_root"]))
        )
    unique_roots = sorted(
        {root for roots in roots_by_project.values() for root in roots}
    )
    print(
        f"[heldout-v4] discovering native sources across {len(unique_roots)} worktrees",
        flush=True,
    )
    discovered = measurement.discover_sources(
        Path.home(), unique_roots, DISCOVERY_CUTOFF_NS, SOURCE_BYTES_CAP
    )
    projects = []
    for row in project_input:
        repo = measurement.canonical(Path(row["repository_root"]))
        allowed_roots = {
            str(measurement.canonical(root))
            for root in roots_by_project[row["project"]]
        }
        candidates = [
            source
            for source in discovered
            if source["worktree"] in allowed_roots
            and source["sha256"] not in excluded_hashes
            and (source["vendor"], source["native_session_id"])
            not in excluded_roots
        ]
        selected_root, selected = measurement.select_sources(
            candidates,
            SOURCE_BYTES_CAP,
            ROOTS_PER_PROJECT,
            SELECTION_SEED,
        )
        if len(selected) != ROOTS_PER_PROJECT:
            raise RuntimeError(f"{row['project']} did not supply 12 roots")
        projects.append(
            {
                "project": row["project"],
                "repository_root": str(repo),
                "worktree": str(selected_root),
                "sources": selected,
            }
        )
        print(
            f"[heldout-v4] selected 12 roots for {row['project']} at {selected_root}",
            flush=True,
        )

    measurement.source_stability(projects, STABILITY_SECONDS)
    frozen_home = PRIVATE / "frozen-home"
    questions: list[dict[str, Any]] = []
    release_sources = []
    selected_hashes: set[str] = set()
    selected_roots: set[tuple[str, str]] = set()
    selected_calls: set[tuple[str, str, str]] = set()

    for project in projects:
        measurement.copy_selected(project["sources"], Path.home(), frozen_home)
        direct = measurement.direct_atoms(project["sources"], frozen_home)
        official = measurement.official_procgrep_atoms(
            PROCGREP, project["sources"], frozen_home
        )
        edges, sessions, calls = measurement.artifact_edges(
            project, project["sources"], frozen_home
        )
        anchors = measurement.choose_anchors(edges)
        snapshot = measurement.workspace_snapshot(
            Path(project["worktree"]),
            anchors,
            PRIVATE / "workspace" / project["project"],
        )
        project_questions = measurement.question_rows(
            project, direct, edges, sessions, anchors, snapshot
        )
        if len(project_questions) != 20:
            raise RuntimeError(f"{project['project']} did not yield 20 questions")
        source_cutoff = max(
            (int(row.get("last_ts_ms") or 0) for row in project["sources"]),
            default=0,
        )
        if source_cutoff > int(snapshot["cutoff_ms"]):
            raise RuntimeError(f"source cutoff exceeds workspace cutoff: {project['project']}")
        project.update(
            {
                "direct_action_atoms": direct,
                "procgrep_action_atoms": official,
                "oracle_edges": edges,
                "oracle_calls": calls,
                "sessions": sessions,
                "anchors": anchors,
                "workspace": snapshot,
                "source_cutoff_ms": source_cutoff,
                "questions": project_questions,
            }
        )
        questions.extend(project_questions)
        selected_hashes.update(str(row["sha256"]) for row in project["sources"])
        selected_roots.update(
            (str(row["vendor"]), str(row["native_session_id"]))
            for row in project["sources"]
        )
        selected_calls.update(
            (
                str(call["vendor"]),
                str(call["native_session_id"]).split(":", 1)[-1],
                str(call["call_id"]),
            )
            for call in calls
        )
        for source in project["sources"]:
            release_sources.append(
                {
                    "project": project["project"],
                    "vendor": source["vendor"],
                    "source_id": source["source_id"],
                    "bytes": source["bytes"],
                    "sha256": source["sha256"],
                    "session_id_hash": sha256_bytes(
                        source["session_id"].encode()
                    )[:16],
                    "worktree_id": measurement.worktree_id(
                        Path(project["worktree"])
                    ),
                }
            )

    split_audit = {
        "excluded_freezes": exclusion_audit,
        "file_hash_overlap": len(selected_hashes & excluded_hashes),
        "native_root_overlap": len(selected_roots & excluded_roots),
        "native_root_call_overlap": len(selected_calls & excluded_calls),
        "selected_file_hashes": len(selected_hashes),
        "selected_native_roots": len(selected_roots),
    }
    if (
        len(selected_hashes) != PROJECT_COUNT * ROOTS_PER_PROJECT
        or len(selected_roots) != PROJECT_COUNT * ROOTS_PER_PROJECT
        or any(
            split_audit[key] != 0
            for key in (
                "file_hash_overlap",
                "native_root_overlap",
                "native_root_call_overlap",
            )
        )
    ):
        raise RuntimeError(f"held-out split contract failed: {split_audit}")
    if len(questions) != 120 or Counter(row["family"] for row in questions) != {
        "A": 30,
        "B": 30,
        "C": 30,
        "D": 30,
    }:
        raise RuntimeError("question matrix is not 120 rows / 30 per family")

    old_signatures = old_question_signatures()
    new_signatures = {
        sha256_bytes(
            json.dumps(
                {
                    key: row.get(key)
                    for key in (
                        "project",
                        "family",
                        "template",
                        "answer",
                        "p0_path",
                        "p0_path_id",
                        "path_id",
                        "witnesses",
                    )
                },
                sort_keys=True,
            ).encode()
        )
        for row in questions
    }
    question_independence = {
        "old_question_rows": len(old_signatures),
        "new_question_rows": len(new_signatures),
        "exact_instance_overlap": len(old_signatures & new_signatures),
        "old_answers_or_rows_imported": False,
    }
    if question_independence["exact_instance_overlap"] != 0:
        raise RuntimeError(f"old question instance reused: {question_independence}")

    spec_text = question_spec_v4()
    (PRIVATE / "question-spec.md").write_text(spec_text)
    spec_hash = sha256_bytes(spec_text.encode())
    freeze = {
        "seed": SELECTION_SEED,
        "spec_version": SPEC_VERSION,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repository_revision": run(["git", "rev-parse", "HEAD"]).strip(),
        "runner_sha256": sha256_file(Path(__file__)),
        "frozen_code_hashes": FROZEN_CODE_HASHES,
        "procgrep_revision": PROCGREP_REVISION,
        "procgrep_lock_sha256": PROCGREP_LOCK_SHA256,
        "codex_version": run(["codex", "--version"]).strip(),
        "python_version": sys.version,
        "question_spec_sha256": spec_hash,
        "projects_file_sha256": sha256_file(PROJECTS_FILE),
        "discovery_cutoff_ns": DISCOVERY_CUTOFF_NS,
        "source_count_contract": {
            "projects": PROJECT_COUNT,
            "sources_per_project": ROOTS_PER_PROJECT,
            "total_sources": PROJECT_COUNT * ROOTS_PER_PROJECT,
        },
        "projects": projects,
        "questions": questions,
        "split_audit": split_audit,
        "question_independence": question_independence,
    }
    write_json(PRIVATE / "freeze.json", freeze)
    write_json(PRIVATE / "oracle-questions.json", questions)
    write_csv(
        release / "freeze-sources.csv",
        [
            "project",
            "vendor",
            "source_id",
            "bytes",
            "sha256",
            "session_id_hash",
            "worktree_id",
        ],
        release_sources,
    )
    public_questions = [
        measurement.sanitize_question(row, spec_hash) for row in questions
    ]
    write_csv(
        release / "questions.csv",
        [
            "id",
            "project",
            "family",
            "template",
            "path_id",
            "witness_hash",
            "question_spec_sha256",
        ],
        public_questions,
    )
    run(
        [
            sys.executable,
            str(REPOSITORY / "agentvis/research/rq7_source_oracle_check.py"),
            str(PRIVATE / "freeze.json"),
            str(PRIVATE / "oracle-check.json"),
        ]
    )
    checker_result = read_json(PRIVATE / "oracle-check.json")
    if checker_result.get("status") != "pass":
        raise RuntimeError("independent source checker did not pass")
    manifest_hash = measurement.audit_manifest(PRIVATE)
    summary = {
        "spec_version": SPEC_VERSION,
        "projects": PROJECT_COUNT,
        "sources": PROJECT_COUNT * ROOTS_PER_PROJECT,
        "questions": len(questions),
        "questions_per_family": dict(Counter(row["family"] for row in questions)),
        "vendors": dict(
            Counter(
                source["vendor"]
                for project in projects
                for source in project["sources"]
            )
        ),
        "question_spec_sha256": spec_hash,
        "private_audit_manifest_sha256": manifest_hash,
        "oracle_checker_sha256": checker_result["checker_sha256"],
        "split_audit": split_audit,
        "question_independence": question_independence,
    }
    write_json(release / "freeze-summary.json", summary)
    return summary


def build_and_seal() -> dict[str, Any]:
    verify_frozen_code()
    if not (PRIVATE / "freeze.json").is_file():
        raise RuntimeError("freeze must complete before build")
    build_root = EXPERIMENT / "build"
    if build_root.exists():
        raise RuntimeError("build output is append-only")
    build_root.mkdir(parents=True)
    fixture_command = [
        sys.executable,
        "agentvis/research/rq7_measurement.py",
        "check-action-fixtures",
        "--fixtures",
        "agent-session/tests/fixtures/strict-action-grammar.json",
    ]
    fixture_output = run(
        fixture_command,
        env=fixture_environment(build_root / "fixture-cargo-target"),
    )
    (build_root / "fixture-output.txt").write_text(fixture_output)
    target = build_root / "cargo-target"
    env = os.environ.copy()
    env["CARGO_TARGET_DIR"] = str(target)
    build_command = [
        "cargo",
        "build",
        "--release",
        "--locked",
        "--offline",
        "--manifest-path",
        "agentvis/Cargo.toml",
    ]
    build_output = run(build_command, env=env)
    (build_root / "cargo-build.log").write_text(build_output)
    binary = target / "release/agentvis"
    if not binary.is_file():
        raise RuntimeError("locked release build did not produce agentvis")
    seal = {
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repository_revision": run(["git", "rev-parse", "HEAD"]).strip(),
        "runner_sha256": sha256_file(Path(__file__)),
        "freeze_sha256": sha256_file(PRIVATE / "freeze.json"),
        "frozen_code_hashes": FROZEN_CODE_HASHES,
        "fixture_command": shlex.join(fixture_command),
        "fixture_output_sha256": sha256_file(build_root / "fixture-output.txt"),
        "build_command": shlex.join(build_command),
        "binary_path": str(binary),
        "binary_sha256": sha256_file(binary),
        "binary_bytes": binary.stat().st_size,
    }
    write_json(build_root / "code-seal.json", seal)
    return seal


def validate_seal() -> tuple[dict[str, Any], Path]:
    verify_frozen_code()
    seal_path = EXPERIMENT / "build/code-seal.json"
    seal = read_json(seal_path)
    if seal.get("runner_sha256") != sha256_file(Path(__file__)):
        raise RuntimeError("runner changed after code seal")
    if seal.get("freeze_sha256") != sha256_file(PRIVATE / "freeze.json"):
        raise RuntimeError("freeze changed after code seal")
    binary = Path(str(seal["binary_path"]))
    if not binary.is_file() or sha256_file(binary) != seal["binary_sha256"]:
        raise RuntimeError("sealed binary mismatch")
    return seal, binary


def trace_map(
    projection_dir: Path, projects: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    traces = [
        read_json(path)
        for path in sorted((projection_dir / "raw/events").glob("*.json"))
    ]
    mapped = {}
    for project in projects:
        expected = {
            identity
            for source in project["sources"]
            for identity in (source["source_stem"], source["native_session_id"])
        }
        ranked = []
        for trace in traces:
            actual = {
                str(event.get("session_id") or "")
                for event in trace.get("events") or []
            }
            overlap = sum(
                any(
                    identity == raw
                    or identity in raw
                    or raw in identity
                    for raw in actual
                )
                for identity in expected
            )
            ranked.append((overlap, trace))
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        if not ranked or ranked[0][0] == 0:
            raise RuntimeError(f"no projection trace for {project['project']}")
        if len(ranked) > 1 and ranked[0][0] == ranked[1][0]:
            raise RuntimeError(f"ambiguous projection trace for {project['project']}")
        mapped[project["project"]] = ranked[0][1]
    return mapped


def edge_key(row: dict[str, Any]) -> tuple[Any, ...]:
    """Exact attempted-edge key, including final display lineage."""

    return (
        row["project"],
        int(row["session_ordinal"]),
        row["native_session_id"],
        row["source_stream_id"],
        str(row["call_id"]),
        int(row["source_tool_ordinal"]),
        int(row["event_ordinal"]),
        int(row["action_ordinal"]),
        row["path"],
        row["display_path"],
        row["access"],
        row.get("previous_path"),
        row["artifact_id"],
    )


def call_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["project"],
        int(row["session_ordinal"]),
        row["native_session_id"],
        row["source_stream_id"],
        str(row["call_id"]),
        int(row["source_tool_ordinal"]),
        row["status"],
    )


def metrics(expected: Counter[Any], actual: Counter[Any]) -> dict[str, Any]:
    matched = sum((expected & actual).values())
    expected_count = sum(expected.values())
    actual_count = sum(actual.values())
    precision = (
        matched / actual_count if actual_count else float(expected_count == 0)
    )
    recall = (
        matched / expected_count if expected_count else float(actual_count == 0)
    )
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "expected": expected_count,
        "actual": actual_count,
        "matched": matched,
        "missing": expected_count - matched,
        "extra": actual_count - matched,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def project_ledgers(
    project: dict[str, Any], trace: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    production_edges, production_calls, _, error = measurement.production_projection(
        project, trace
    )
    if error:
        raise RuntimeError(error)
    oracle_edges = project["oracle_edges"]
    edge_calls = {
        (
            row["native_session_id"],
            row["source_stream_id"],
            str(row["call_id"]),
            int(row["source_tool_ordinal"]),
        )
        for row in oracle_edges + production_edges
    }
    oracle_calls = [
        row
        for row in project["oracle_calls"]
        if (
            row["native_session_id"],
            row["source_stream_id"],
            str(row["call_id"]),
            int(row["source_tool_ordinal"]),
        )
        in edge_calls
    ]
    production_edge_calls = [
        row
        for row in production_calls
        if (
            row["native_session_id"],
            row["source_stream_id"],
            str(row["call_id"]),
            int(row["source_tool_ordinal"]),
        )
        in edge_calls
    ]

    def grouped(
        expected_edges: list[dict[str, Any]],
        actual_edges: list[dict[str, Any]],
        expected_calls: list[dict[str, Any]],
        actual_calls: list[dict[str, Any]],
        sessions: list[dict[str, Any]],
        vendor: str | None = None,
    ) -> dict[str, Any]:
        filtered_sessions = [
            row for row in sessions if vendor is None or row["vendor"] == vendor
        ]
        return {
            "session_order": metrics(
                Counter(
                    (
                        project["project"],
                        row["semantic_session_id"],
                        int(row["session_ordinal"]),
                    )
                    for row in filtered_sessions
                ),
                Counter(
                    {
                        (
                            project["project"],
                            row["native_session_id"],
                            int(row["session_ordinal"]),
                        )
                        for row in production_calls
                        if vendor is None or row["vendor"] == vendor
                    }
                ),
            ),
            "attempted_edges": metrics(
                Counter(edge_key(row) for row in expected_edges),
                Counter(edge_key(row) for row in actual_edges),
            ),
            "confirmed_effect_edges": metrics(
                Counter(edge_key(row) for row in expected_edges if row["status"] == "ok"),
                Counter(edge_key(row) for row in actual_edges if row["status"] == "ok"),
            ),
            "edge_call_statuses": metrics(
                Counter(call_key(row) for row in expected_calls),
                Counter(call_key(row) for row in actual_calls),
            ),
        }

    result = grouped(
        oracle_edges,
        production_edges,
        oracle_calls,
        production_edge_calls,
        project["sessions"],
    )
    result["project"] = project["project"]
    result["by_vendor"] = {}
    for vendor in sorted({row["vendor"] for row in project["sessions"]}):
        result["by_vendor"][vendor] = grouped(
            [row for row in oracle_edges if row["vendor"] == vendor],
            [row for row in production_edges if row["vendor"] == vendor],
            [row for row in oracle_calls if row["vendor"] == vendor],
            [row for row in production_edge_calls if row["vendor"] == vendor],
            project["sessions"],
            vendor,
        )
    return production_edges, production_calls, result


def exact_group(group: dict[str, Any]) -> bool:
    return all(
        group[name]["precision"] == 1.0
        and group[name]["recall"] == 1.0
        and group[name]["f1"] == 1.0
        for name in (
            "session_order",
            "attempted_edges",
            "confirmed_effect_edges",
            "edge_call_statuses",
        )
    )


def question_gate(
    rows: list[dict[str, Any]], families: set[str]
) -> dict[str, Any]:
    selected = [
        row
        for row in rows
        if row["method"] == "trajectory" and row["family"] in families
    ]
    return {
        "total": len(selected),
        "correct": sum(int(row["correct"]) for row in selected),
        "wrong": sum(int(row["wrong"]) for row in selected),
        "abstain": sum(row["status"] == "abstain" for row in selected),
    }


def run_projection(
    names: set[str] | None,
    release_dir: Path,
    private_projection: Path,
    binary: Path,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    if release_dir.exists() or private_projection.exists():
        raise RuntimeError("projection outputs are append-only")
    os.environ["RQ7_AGENTVIS_BINARY"] = str(binary)
    rows, _ = measurement.deterministic_methods(
        PRIVATE,
        release_dir,
        names,
        projection_output=private_projection,
    )
    freeze = read_json(PRIVATE / "freeze.json")
    projects = [
        project
        for project in freeze["projects"]
        if names is None or project["project"] in names
    ]
    traces = trace_map(private_projection, projects)
    oracle_edges = []
    production_edges = []
    conformance = []
    production_calls = []
    for project in projects:
        pedges, pcalls, result = project_ledgers(
            project, traces[project["project"]]
        )
        oracle_edges.extend(project["oracle_edges"])
        production_edges.extend(pedges)
        production_calls.extend(pcalls)
        conformance.append(result)
    return rows, oracle_edges, production_edges, production_calls, conformance


def preflight() -> dict[str, Any]:
    seal, binary = validate_seal()
    freeze = read_json(PRIVATE / "freeze.json")
    if read_json(PRIVATE / "oracle-check.json").get("status") != "pass":
        raise RuntimeError("source checker did not pass")
    project = min(
        freeze["projects"],
        key=lambda row: (
            sum(int(source["bytes"]) for source in row["sources"]),
            row["project"],
        ),
    )
    rows, oracle_edges, production_edges, production_calls, conformance = run_projection(
        {project["project"]},
        EXPERIMENT / "raw/preflight/deterministic",
        PRIVATE / "preflight/projection",
        binary,
    )
    if (
        len(rows) != 80
        or len(conformance) != 1
        or not oracle_edges
    ):
        raise RuntimeError(
            "preflight mechanism did not materialize the complete one-case matrix"
        )
    bc = question_gate(rows, {"B", "C"})
    d = question_gate(rows, {"D"})
    result = {
        "status": "mechanism_pass",
        "project": project["project"],
        "rows": len(rows),
        "code_seal_sha256": sha256_file(EXPERIMENT / "build/code-seal.json"),
        "freeze_sha256": seal["freeze_sha256"],
        "scientific_conformance_pass": all(
            exact_group(row)
            and all(exact_group(group) for group in row["by_vendor"].values())
            for row in conformance
        ),
        "bc_gate": bc,
        "d_gate": d,
        "conformance": conformance,
        "note": (
            "Preflight gates only real-path execution and integrity. A scientific "
            "failure is retained and does not block the registered full run."
        ),
    }
    write_json(EXPERIMENT / "raw/preflight/preflight-result.json", result)
    return result


LEDGER_FIELDS = [
    "side",
    "project",
    "vendor",
    "native_session_id",
    "session_ordinal",
    "source_stream_id",
    "source_tool_ordinal",
    "call_id",
    "event_ordinal",
    "action_ordinal",
    "artifact_id",
    "path",
    "display_path",
    "access",
    "previous_path",
    "status",
    "confirmed_effect",
]


def aggregate_conformance(
    freeze: dict[str, Any],
    oracle_edges: list[dict[str, Any]],
    production_edges: list[dict[str, Any]],
    production_calls: list[dict[str, Any]],
) -> dict[str, Any]:
    oracle_calls = [
        call for project in freeze["projects"] for call in project["oracle_calls"]
    ]
    edge_calls = {
        (
            row["project"],
            row["native_session_id"],
            row["source_stream_id"],
            str(row["call_id"]),
            int(row["source_tool_ordinal"]),
        )
        for row in oracle_edges + production_edges
    }
    oracle_edge_calls = [
        row
        for row in oracle_calls
        if (
            row["project"],
            row["native_session_id"],
            row["source_stream_id"],
            str(row["call_id"]),
            int(row["source_tool_ordinal"]),
        )
        in edge_calls
    ]
    production_edge_calls = [
        row
        for row in production_calls
        if (
            row["project"],
            row["native_session_id"],
            row["source_stream_id"],
            str(row["call_id"]),
            int(row["source_tool_ordinal"]),
        )
        in edge_calls
    ]
    sessions = [
        (project["project"], session)
        for project in freeze["projects"]
        for session in project["sessions"]
    ]
    return {
        "session_order": metrics(
            Counter(
                (
                    project,
                    session["semantic_session_id"],
                    int(session["session_ordinal"]),
                )
                for project, session in sessions
            ),
            Counter(
                (
                    row["project"],
                    row["native_session_id"],
                    int(row["session_ordinal"]),
                )
                for row in production_calls
            ),
        ),
        "attempted_edges": metrics(
            Counter(edge_key(row) for row in oracle_edges),
            Counter(edge_key(row) for row in production_edges),
        ),
        "confirmed_effect_edges": metrics(
            Counter(edge_key(row) for row in oracle_edges if row["status"] == "ok"),
            Counter(edge_key(row) for row in production_edges if row["status"] == "ok"),
        ),
        "edge_call_statuses": metrics(
            Counter(call_key(row) for row in oracle_edge_calls),
            Counter(call_key(row) for row in production_edge_calls),
        ),
    }


def diff_rows(
    oracle_edges: list[dict[str, Any]],
    production_edges: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    oracle_by_key: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    production_by_key: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in oracle_edges:
        oracle_by_key[edge_key(row)].append(row)
    for row in production_edges:
        production_by_key[edge_key(row)].append(row)
    rows = []
    for side, left, right in (
        ("missing_from_projection", oracle_by_key, production_by_key),
        ("extra_in_projection", production_by_key, oracle_by_key),
    ):
        for key in sorted(left, key=lambda value: tuple(map(str, value))):
            count = len(left[key]) - len(right.get(key, []))
            if count <= 0:
                continue
            sample = left[key][0]
            rows.append({"diff": side, "count": count, **sample})
    return rows


def score_rows_by_family(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = [row for row in rows if row["method"] == "trajectory"]
    output = []
    for family in ("A", "B", "C", "D"):
        family_rows = [row for row in selected if row["family"] == family]
        output.append(
            {
                "family": family,
                "total": len(family_rows),
                "correct": sum(int(row["correct"]) for row in family_rows),
                "wrong": sum(int(row["wrong"]) for row in family_rows),
                "abstain": sum(row["status"] == "abstain" for row in family_rows),
            }
        )
    return output


def markdown_result(
    summary: dict[str, Any],
    questions: list[dict[str, Any]],
    edge_summary_rows: list[dict[str, Any]],
    diffs: list[dict[str, Any]],
) -> str:
    lines = [
        "# P1 Held-Out Question and Full Edge-Ledger Conformance",
        "",
        "## Outcome",
        "",
        f"- Run status: **{summary['run_status']}**.",
        f"- Tested hypothesis: **{summary['tested_hypothesis']}**.",
        f"- Strict held-out conformance decision: **{summary['status']}**.",
        f"- Held-out B+C: **{summary['bc_gate']['correct']}/60 correct**, "
        f"{summary['bc_gate']['wrong']} wrong, {summary['bc_gate']['abstain']} abstain.",
        f"- Held-out D: **{summary['d_gate']['correct']}/30 correct**, "
        f"{summary['d_gate']['wrong']} wrong, {summary['d_gate']['abstain']} abstain.",
        f"- Full attempted edge ledger: oracle={summary['overall_conformance']['attempted_edges']['expected']}, "
        f"projection={summary['overall_conformance']['attempted_edges']['actual']}, "
        f"missing={summary['overall_conformance']['attempted_edges']['missing']}, "
        f"extra={summary['overall_conformance']['attempted_edges']['extra']}.",
        "",
        "The earlier **60/60** is retained as repair-corpus regression evidence "
        "over the original 72 files and original 60 B+C rows.  The number above "
        "uses 60 newly instantiated B+C rows from 72 root-disjoint held-out "
        "files.  The denominators are comparable but are not pooled.",
        "",
        "## Question-family scores",
        "",
        "| Family | Correct | Wrong | Abstain |",
        "|---|---:|---:|---:|",
    ]
    for row in summary["family_scores"]:
        lines.append(
            f"| {row['family']} | {row['correct']}/{row['total']} | "
            f"{row['wrong']} | {row['abstain']} |"
        )
    lines.extend(
        [
            "",
            "## Edge-level ledger",
            "",
            "The exact attempted-edge key includes final `display_path` in "
            "addition to semantic root, source stream/tool ordinal, call/event/"
            "action order, path/access/previous path, and artifact generation. "
            "Confirmed effects and edge-call statuses are separately exact-gated.",
            "",
            "| Scope | Ledger | Expected | Actual | Matched | Missing | Extra | Precision | Recall | F1 |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in edge_summary_rows:
        lines.append(
            f"| {row['scope']} | {row['ledger']} | {row['expected']} | "
            f"{row['actual']} | {row['matched']} | {row['missing']} | "
            f"{row['extra']} | {row['precision']:.6f} | "
            f"{row['recall']:.6f} | {row['f1']:.6f} |"
        )
    lines.extend(
        [
            "",
            f"Row-level attempted-edge differences: **{sum(int(row['count']) for row in diffs)}**. "
            "The complete ledgers are in `raw/full/edge-ledger.csv`; differences "
            "are in `raw/full/edge-diff.csv`.",
            "",
            "## Per-question decisions",
            "",
            "| Question | Family | Expected | Trajectory | Status | Judgment |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in questions:
        judgment = (
            "correct"
            if int(row["correct"])
            else ("wrong" if int(row["wrong"]) else "abstain")
        )
        lines.append(
            f"| {row['id']} | {row['family']} | {row['expected']} | "
            f"{row['answer'] or '—'} | {row['status']} | {judgment} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "This run tests deterministic native-record conformance, not complete "
            "system effects or population generalization.  A-family rows are "
            "reported but do not gate the preregistered B/C/D and full-ledger "
            "decision.",
        ]
    )
    return "\n".join(lines) + "\n"


def full_run() -> dict[str, Any]:
    seal, binary = validate_seal()
    preflight_attempt = read_json(EXPERIMENT / "preflight-attempt.json")
    preflight_result = read_json(
        EXPERIMENT / "raw/preflight/preflight-result.json"
    )
    if (
        preflight_attempt.get("terminal_status") != "complete"
        or preflight_result.get("status") != "mechanism_pass"
        or preflight_result.get("freeze_sha256") != seal["freeze_sha256"]
        or preflight_result.get("code_seal_sha256")
        != sha256_file(EXPERIMENT / "build/code-seal.json")
    ):
        raise RuntimeError("full run requires the unique matching mechanism preflight")

    rows, oracle_edges, production_edges, production_calls, conformance = (
        run_projection(
            None,
            EXPERIMENT / "raw/full/deterministic",
            PRIVATE / "full/projection",
            binary,
        )
    )
    if (
        len(rows) != 480
        or len(conformance) != 6
        or not oracle_edges
    ):
        raise RuntimeError(
            "full mechanism did not materialize the complete six-case matrix"
        )
    freeze = read_json(PRIVATE / "freeze.json")
    overall = aggregate_conformance(
        freeze, oracle_edges, production_edges, production_calls
    )
    by_project_exact = all(
        exact_group(row)
        and all(exact_group(group) for group in row["by_vendor"].values())
        for row in conformance
    )
    overall_exact = exact_group(overall)
    bc = question_gate(rows, {"B", "C"})
    d = question_gate(rows, {"D"})
    strict_pass = (
        overall_exact
        and by_project_exact
        and bc == {"total": 60, "correct": 60, "wrong": 0, "abstain": 0}
        and d == {"total": 30, "correct": 30, "wrong": 0, "abstain": 0}
    )
    family_scores = score_rows_by_family(rows)
    summary = {
        "status": "pass" if strict_pass else "fail",
        "run_status": "valid",
        "tested_hypothesis": "supported" if strict_pass else "contradicted",
        "research_value": "decisive",
        "paper_impact": (
            "additional RQ evidence"
            if strict_pass
            else "mechanism or workload boundary"
        ),
        "projects": len(freeze["projects"]),
        "sources": sum(len(project["sources"]) for project in freeze["projects"]),
        "questions": len(freeze["questions"]),
        "question_independence": freeze["question_independence"],
        "split_audit": freeze["split_audit"],
        "source_checker": read_json(PRIVATE / "oracle-check.json"),
        "strict_edge_conformance": overall_exact and by_project_exact,
        "overall_conformance": overall,
        "project_conformance": conformance,
        "bc_gate": bc,
        "d_gate": d,
        "family_scores": family_scores,
        "old_repair_corpus_bc": {
            "correct": 60,
            "total": 60,
            "scope": "same 72 repair files / corrected v4 oracle",
        },
    }
    full_dir = EXPERIMENT / "raw/full"
    ledger_rows = [
        {"side": "oracle", **row} for row in oracle_edges
    ] + [{"side": "projection", **row} for row in production_edges]
    write_csv(full_dir / "edge-ledger.csv", LEDGER_FIELDS, ledger_rows)
    diffs = diff_rows(oracle_edges, production_edges)
    write_csv(
        full_dir / "edge-diff.csv",
        ["diff", "count", *[field for field in LEDGER_FIELDS if field != "side"]],
        diffs,
    )
    question_rows = sorted(
        [row for row in rows if row["method"] == "trajectory"],
        key=lambda row: (row["project"], row["family"], row["template"]),
    )
    write_csv(
        full_dir / "question-results.csv",
        [
            "id",
            "project",
            "family",
            "template",
            "method",
            "status",
            "answer",
            "expected",
            "correct",
            "wrong",
            "question_spec_sha256",
        ],
        question_rows,
    )
    write_csv(
        full_dir / "method-results.csv",
        [
            "id",
            "project",
            "family",
            "template",
            "method",
            "repetition",
            "status",
            "answer",
            "expected",
            "correct",
            "wrong",
            "question_spec_sha256",
        ],
        rows,
    )

    edge_summary_rows = []
    for scope, group in [("overall", overall)] + [
        (f"project:{row['project']}", row) for row in conformance
    ]:
        for ledger in (
            "session_order",
            "attempted_edges",
            "confirmed_effect_edges",
            "edge_call_statuses",
        ):
            edge_summary_rows.append(
                {"scope": scope, "ledger": ledger, **group[ledger]}
            )
    vendor_groups: dict[str, dict[str, Counter[Any]]] = {}
    for row in conformance:
        for vendor, group in row["by_vendor"].items():
            target = vendor_groups.setdefault(
                vendor,
                {
                    name: Counter()
                    for name in (
                        "session_order",
                        "attempted_edges",
                        "confirmed_effect_edges",
                        "edge_call_statuses",
                    )
                },
            )
            for name in target:
                metric = group[name]
                target[name].update(
                    {
                        "expected": metric["expected"],
                        "actual": metric["actual"],
                        "matched": metric["matched"],
                    }
                )
    for vendor, ledgers in sorted(vendor_groups.items()):
        for name, counts in ledgers.items():
            expected = counts["expected"]
            actual = counts["actual"]
            matched = counts["matched"]
            precision = matched / actual if actual else float(expected == 0)
            recall = matched / expected if expected else float(actual == 0)
            f1 = (
                2 * precision * recall / (precision + recall)
                if precision + recall
                else 0.0
            )
            edge_summary_rows.append(
                {
                    "scope": f"vendor:{vendor}",
                    "ledger": name,
                    "expected": expected,
                    "actual": actual,
                    "matched": matched,
                    "missing": expected - matched,
                    "extra": actual - matched,
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                }
            )
    write_csv(
        full_dir / "edge-summary.csv",
        [
            "scope",
            "ledger",
            "expected",
            "actual",
            "matched",
            "missing",
            "extra",
            "precision",
            "recall",
            "f1",
        ],
        edge_summary_rows,
    )
    write_json(full_dir / "summary.json", summary)
    (EXPERIMENT / "result.md").write_text(
        markdown_result(summary, question_rows, edge_summary_rows, diffs)
    )
    return summary


def attempt(command: str, function: Any) -> int:
    path = EXPERIMENT / f"{command}-attempt.json"
    if path.exists():
        raise RuntimeError(f"{command} attempt already exists: {path}")
    record = {
        "command": shlex.join(sys.argv),
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "terminal_status": "running",
        "runner_sha256": sha256_file(Path(__file__)),
    }
    write_json(path, record)
    try:
        result = function()
    except BaseException as error:
        record.update(
            {
                "terminal_status": "failed",
                "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "error_type": type(error).__name__,
                "error": str(error),
            }
        )
        write_json(path, record)
        raise
    record.update(
        {
            "terminal_status": "complete",
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "result": result,
        }
    )
    write_json(path, record)
    return 0


def check_fixtures() -> dict[str, Any]:
    verify_frozen_code()
    v4_result = v4_primary_fixture_gate()
    output = run(
        [
            sys.executable,
            "agentvis/research/rq7_measurement.py",
            "check-action-fixtures",
            "--fixtures",
            "agent-session/tests/fixtures/strict-action-grammar.json",
        ],
        env=fixture_environment(EXPERIMENT / "fixture/cargo-target"),
    )
    return {
        "status": "pass",
        "v4_primary": v4_result,
        "production_output": output.strip(),
        "cargo_target": str(EXPERIMENT / "fixture/cargo-target"),
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument(
        "command",
        choices=("check-fixtures", "freeze", "build", "preflight", "full"),
    )
    return root


def main() -> int:
    args = parser().parse_args()
    functions = {
        "check-fixtures": check_fixtures,
        "freeze": freeze_corpus,
        "build": build_and_seal,
        "preflight": preflight,
        "full": full_run,
    }
    return attempt(args.command, functions[args.command])


if __name__ == "__main__":
    raise SystemExit(main())
