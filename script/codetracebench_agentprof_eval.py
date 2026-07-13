#!/usr/bin/env python3
"""Run source audits and the CodeTraceBench AgentProf RQ2 experiment path.

Source construction projects no step-label column.  The shared real-preflight
and full path reconstructs public benchmark operations, verifies release
AgentProf counts independently, estimates task-held-out differential profiles,
writes predictions, and only then loads incorrect-step labels for metrics.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import re
import shlex
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Iterable

import pyarrow.parquet as pq


MANIFEST_COLUMNS = [
    "traj_id",
    "agent",
    "model",
    "task_name",
    "difficulty",
    "category",
    "solved",
    "step_count",
    "source_relpath",
    "artifact_path",
]

PREFLIGHT_VARIANTS: tuple[tuple[str, str, Callable[["ManifestRow"], bool]], ...] = (
    (
        "MiniSWE session log",
        "mini-SWE-agent",
        lambda row: not (row.source_relpath or "").startswith("swe_raw/"),
    ),
    (
        "MiniSWE SWE raw",
        "mini-SWE-agent",
        lambda row: (row.source_relpath or "").startswith("swe_raw/"),
    ),
    (
        "OpenHands event stream",
        "OpenHands",
        lambda row: not (row.source_relpath or "").startswith("swe_raw/"),
    ),
    (
        "OpenHands SWE raw",
        "OpenHands",
        lambda row: (row.source_relpath or "").startswith("swe_raw/"),
    ),
    ("Terminus2 command stream", "Terminus2", lambda row: True),
    ("SWE-agent trajectory", "SWE-agent", lambda row: True),
)

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
BASH_FENCE_RE = re.compile(r"```bash\s*\n(.*?)\n?```", re.IGNORECASE | re.DOTALL)
MINISWE_MARKER_RE = re.compile(r"mini-swe-agent\s*\(step\s*(\d+)\s*,", re.IGNORECASE)


ACTION_KIND_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "communicate",
        re.compile(
            r"COMPLETE_TASK|SUBMIT_FINAL|\[(SendMessage|AskUser|TaskOutput|TaskStop)\]",
            re.IGNORECASE,
        ),
    ),
    (
        "version-control",
        re.compile(r"(?:^|[;&|\s])(?:git|gh)(?:\s|$)", re.IGNORECASE),
    ),
    (
        "install",
        re.compile(
            r"pip3?\s+install|uv\s+add|poetry\s+add|npm\s+(?:install|i)|"
            r"yarn\s+add|pnpm\s+add|apt(?:-get)?|yum|dnf|brew\s+install|cargo\s+add",
            re.IGNORECASE,
        ),
    ),
    (
        "test",
        re.compile(
            r"pytest|python3?\s+-m\s+pytest|cargo\s+test|go\s+test|npm\s+test|"
            r"yarn\s+test|pnpm\s+test|ctest|mvn\s+test|gradle\s+test|make\s+test",
            re.IGNORECASE,
        ),
    ),
    (
        "edit",
        re.compile(
            r"str_replace_editor\s+(?:str_replace|create|insert|undo_edit)|"
            r"\[(?:Write|Edit|NotebookEdit|FileWrite|FileEdit)\]|apply_patch|sed\s+-i|"
            r"(?:^|[;&|\s])(?:tee|touch|mkdir|rm|mv|cp|chmod|chown)(?:\s|$)|"
            r"(?:^|[;&|\s])cat\s.*(?:>|<<)|(?:^|[;&|\s])echo\s.*>",
            re.IGNORECASE,
        ),
    ),
    (
        "search",
        re.compile(
            r"\[(?:Grep|Glob|WebSearch|WebFetch)\]|"
            r"(?:^|[;&|\s])(?:rg|grep|find|fd|locate)(?:\s|$)",
            re.IGNORECASE,
        ),
    ),
    (
        "inspect",
        re.compile(
            r"str_replace_editor\s+view|\[(?:Read|FileRead|recall)\]|"
            r"(?:^|[;&|\s])(?:cat|sed|head|tail|less|more|ls|pwd|stat|file|wc|du|df|ps|which)(?:\s|$)",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True)
class ManifestRow:
    traj_id: str
    agent: str
    model: str
    task_name: str
    difficulty: str
    category: str
    solved: bool | None
    step_count: int
    source_relpath: str | None
    artifact_path: str | None


@dataclass(frozen=True)
class RawStep:
    step_id: int
    action: str
    observation: str | None
    source_ref: str


@dataclass(frozen=True)
class ProfiledStep:
    step_id: int
    action: str
    phase: str
    action_kind: str
    raw_action_key: str
    source_ref: str


@dataclass(frozen=True)
class PreflightSelection:
    variant: str
    row: ManifestRow


class SourceError(RuntimeError):
    """The released source does not satisfy the frozen source-only adapter."""


def load_manifest(path: Path) -> list[ManifestRow]:
    rows = pq.read_table(path, columns=MANIFEST_COLUMNS).to_pylist()
    return [ManifestRow(**row) for row in rows]


def artifact_path(raw_root: Path, row: ManifestRow) -> Path | None:
    if not row.artifact_path:
        return None
    candidates = (
        raw_root / row.artifact_path,
        raw_root / "hub" / row.artifact_path,
        raw_root / Path(row.artifact_path).name,
    )
    return next((path for path in candidates if path.is_file()), None)


def tar_members(archive: Path) -> list[str]:
    result = subprocess.run(
        ["tar", "--zstd", "-tf", str(archive)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line and not line.endswith("/")]


def tar_read(archive: Path, member: str) -> bytes:
    if member.startswith("/") or ".." in Path(member).parts:
        raise SourceError(f"unsafe archive member: {member}")
    result = subprocess.run(
        ["tar", "--zstd", "-xOf", str(archive), member],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def tar_text(archive: Path, member: str) -> str:
    return tar_read(archive, member).decode("utf-8", errors="replace")


def load_json(archive: Path, member: str) -> Any:
    try:
        return json.loads(tar_text(archive, member))
    except json.JSONDecodeError as error:
        raise SourceError(f"invalid JSON in {member}: {error}") from error


def extract_bash(content: str) -> str:
    match = BASH_FENCE_RE.search(content)
    return match.group(1).strip() if match else content.strip()


def parse_miniswe_log(
    archive: Path, member: str, expected: int, members: list[str]
) -> list[RawStep]:
    text = ANSI_RE.sub("", tar_text(archive, member)).replace("\r", "")
    markers = list(MINISWE_MARKER_RE.finditer(text))
    steps: list[RawStep] = []
    for index, marker in enumerate(markers):
        visible_id = int(marker.group(1))
        if visible_id != index + 1:
            raise SourceError(
                f"{member}: marker sequence expected {index + 1}, found {visible_id}"
            )
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        segment = text[marker.end() : end]
        # Only the assistant portion before the next visible User prompt can
        # define the action.  Protocol-error prompts themselves contain an
        # example bash fence and must never be mistaken for an execution.
        assistant_segment = re.split(r"\n\s*User\s*:\s*\n", segment, maxsplit=1)[0]
        fence = BASH_FENCE_RE.search(assistant_segment)
        if not fence:
            # A MiniSWE benchmark operation is an executed fenced command, as
            # in the official seed parser.  Prose-only assistant turns remain
            # visible source events but are not operations; no claim is made
            # that every such turn is a protocol retry.
            continue
        action = fence.group(1).strip()
        if not action:
            raise SourceError(f"{member}: empty MiniSWE action at marker {visible_id}")
        observation = None
        returncode = re.search(
            r"<returncode>.*?</returncode>.*?(?:<output>(.*?)</output>|<warning>(.*?)</warning>)",
            segment,
            re.DOTALL | re.IGNORECASE,
        )
        if returncode:
            observation = next((group for group in returncode.groups() if group is not None), "").strip()
        step_id = len(steps) + 1
        steps.append(RawStep(step_id, action, observation, f"{member}#marker-{visible_id}"))

    return steps


def parse_miniswe_messages(archive: Path, member: str) -> list[RawStep]:
    data = load_json(archive, member)
    messages = data.get("messages") if isinstance(data, dict) else None
    if not isinstance(messages, list):
        raise SourceError(f"{member}: missing MiniSWE messages[]")
    steps: list[RawStep] = []
    for message_index, message in enumerate(messages):
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        content = message.get("content")
        if not isinstance(content, str):
            continue
        fence = BASH_FENCE_RE.search(content)
        if not fence:
            continue
        action = fence.group(1).strip()
        observation = None
        for later in messages[message_index + 1 :]:
            if not isinstance(later, dict) or later.get("role") != "user":
                continue
            later_content = later.get("content")
            if isinstance(later_content, str) and "<returncode>" in later_content:
                observation = later_content
            break
        step_id = len(steps) + 1
        steps.append(RawStep(step_id, action, observation, f"{member}#message-{message_index}"))
    return steps


def parse_miniswe(
    archive: Path, members: list[str], expected: int
) -> tuple[list[RawStep], str]:
    trajectory = next((name for name in members if name.endswith(".traj.json")), None)
    if trajectory:
        return parse_miniswe_messages(archive, trajectory), "miniswe-message-trajectory"
    log = next((name for name in members if name.endswith("/sessions/agent.log")), None)
    if log:
        steps = parse_miniswe_log(archive, log, expected, members)
        return steps, "miniswe-agent-log-markers"
    raise SourceError("MiniSWE archive has neither sessions/agent.log nor .traj.json")


def render_tool_action(name: str, arguments: Any) -> str:
    parsed = arguments
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError:
            parsed = arguments
    if not isinstance(parsed, dict):
        return f"[{name}] {parsed}".strip()

    if name == "str_replace_editor":
        editor_command = parsed.get("command") or parsed.get("cmd") or ""
        path = parsed.get("path") or ""
        return f"str_replace_editor {editor_command} {path}".strip()
    command = parsed.get("command")
    if isinstance(command, str):
        return f"[{name}] {command}".strip()
    compact = json.dumps(parsed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"[{name}] {compact}".strip()


def load_openhands_call_records(
    archive: Path, members: list[str]
) -> list[tuple[int, float, str, dict[str, Any]]]:
    records: list[tuple[int, float, str, dict[str, Any]]] = []
    for member in members:
        if not member.endswith(".json") or member.endswith("/openhands_output.json"):
            continue
        if "/swe_raw/openhands" not in f"/{member}" and not member.startswith("swe_raw/openhands"):
            continue
        data = load_json(archive, member)
        messages = data.get("messages") if isinstance(data, dict) else None
        if (
            not isinstance(data, dict)
            or "response" not in data
            or "timestamp" not in data
            or not isinstance(messages, list)
        ):
            continue
        visible_tool_calls = sum(
            len(message.get("tool_calls") or [])
            for message in messages
            if isinstance(message, dict) and message.get("role") == "assistant"
        )
        records.append((visible_tool_calls, float(data["timestamp"]), member, data))
    return records


def parse_openhands_calls(archive: Path, members: list[str]) -> list[RawStep]:
    # The SWE raw release stores one complete request/response record per LLM
    # call.  OpenHands may restart or compact its context, so concatenating all
    # response files crosses branches and double-counts retained history.  Use
    # the request with the largest complete visible assistant-tool-call history;
    # this choice is structural and does not consult manifest step_count.  The
    # selected record's response is not yet an observed action in that request.
    records = load_openhands_call_records(archive, members)
    if not records:
        return []

    _, _, member, record = max(records, key=lambda item: (item[0], item[1], item[2]))
    steps: list[RawStep] = []
    for message_index, message in enumerate(record["messages"]):
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        tool_calls = message.get("tool_calls")
        if not isinstance(tool_calls, list):
            continue
        for tool_index, tool_call in enumerate(tool_calls):
            function = tool_call.get("function") if isinstance(tool_call, dict) else None
            if not isinstance(function, dict):
                continue
            name = str(function.get("name") or "tool")
            action = render_tool_action(name, function.get("arguments"))
            step_id = len(steps) + 1
            steps.append(
                RawStep(
                    step_id,
                    action,
                    None,
                    f"{member}#message-{message_index}-tool-{tool_index}",
                )
            )
    return steps


def load_openhands_events(archive: Path, members: list[str]) -> list[tuple[str, dict[str, Any]]]:
    events: list[tuple[str, dict[str, Any]]] = []
    for member in members:
        if not member.endswith(".json") or "/sessions/" not in f"/{member}":
            continue
        try:
            data = load_json(archive, member)
        except SourceError:
            continue
        candidates = data if isinstance(data, list) else [data]
        for candidate in candidates:
            if isinstance(candidate, dict) and isinstance(candidate.get("id"), int):
                events.append((member, candidate))
    by_id: dict[int, tuple[str, dict[str, Any]]] = {}
    for member, event in events:
        by_id.setdefault(int(event["id"]), (member, event))
    return [by_id[event_id] for event_id in sorted(by_id)]


def openhands_event_action(event: dict[str, Any]) -> str:
    action = str(event.get("action") or "")
    args = event.get("args")
    if action == "recall":
        # The raw recall payload repeats the entire task instruction.  Keep the
        # framework operation identity without letting task vocabulary decide
        # phase or semantic kind.
        return "[recall]"
    if action == "run_ipython" and isinstance(args, dict) and isinstance(args.get("code"), str):
        return f"[run_ipython] {args['code']}"
    if action == "run":
        metadata = event.get("tool_call_metadata")
        if isinstance(metadata, dict):
            meta_args = metadata.get("args")
            if isinstance(meta_args, dict) and isinstance(meta_args.get("command"), str):
                return f"[run] {meta_args['command']}"
        if isinstance(args, dict) and isinstance(args.get("command"), str):
            return f"[run] {args['command']}"
        message = event.get("message")
        if isinstance(message, str) and message.startswith("Running command:"):
            return f"[run] {message[len('Running command:'):].strip()}"
    return render_tool_action(action, args or event.get("message") or {})


def parse_openhands(
    archive: Path, members: list[str], expected: int
) -> tuple[list[RawStep], str]:
    call_steps = parse_openhands_calls(archive, members)
    if call_steps:
        return call_steps, "openhands-maximal-visible-action-context"
    events = load_openhands_events(archive, members)
    observations: dict[int, str] = {}
    for _, event in events:
        cause = event.get("cause")
        if not isinstance(cause, int) or "observation" not in event:
            continue
        observation = event.get("content") or event.get("message") or event.get("observation")
        if observation is not None:
            observations.setdefault(cause, str(observation))
    steps: list[RawStep] = []
    for member, event in events:
        action = event.get("action")
        # CodeTraceBench's native OpenHands step unit is a chronological agent
        # action.  Framework bookkeeping is not a step: user-side recall
        # repeats the task, ``system`` initializes the runtime, and ``message``
        # may be emitted hundreds of times after a non-terminating final reply.
        # Keep real agent actions, including think/finish/read/edit/run.  This
        # rule is source-structural and does not consult the manifest count.
        if (
            event.get("source") != "agent"
            or not action
            or action in {"system", "message"}
        ):
            continue
        step_id = len(steps) + 1
        steps.append(
            RawStep(
                step_id,
                openhands_event_action(event),
                observations.get(int(event["id"])),
                member,
            )
        )
    if not steps:
        raise SourceError("OpenHands archive has neither call records nor session events")
    return steps, "openhands-agent-actions"


def episode_number(member: str) -> int:
    match = re.search(r"/episode-(\d+)/", member)
    return int(match.group(1)) if match else 10**9


def command_text(command: Any) -> str:
    if isinstance(command, str):
        return command
    if isinstance(command, dict):
        keystrokes = command.get("keystrokes")
        if isinstance(keystrokes, str):
            return keystrokes
        return json.dumps(command, ensure_ascii=False, sort_keys=True)
    return str(command)


def parse_terminus2(
    archive: Path, members: list[str], expected: int
) -> tuple[list[RawStep], str]:
    # The released native Terminus2 operation stream is commands.txt.  Each
    # Python-literal string is one agent command record; list records are the
    # benchmark harness (recording, test launch, and control keystrokes).  Keep
    # empty string records because the benchmark counts an attempted command
    # step even when the agent emitted no command text.  Episode responses may
    # contain several command elements or malformed partial JSON and therefore
    # are not the benchmark step unit.
    command_member = next(
        (member for member in members if member.endswith("/commands.txt")), None
    )
    if command_member is None:
        raise SourceError("Terminus2 archive has no commands.txt")
    steps: list[RawStep] = []
    for line_number, line in enumerate(tar_text(archive, command_member).splitlines(), 1):
        try:
            command = ast.literal_eval(line)
        except (SyntaxError, ValueError) as error:
            raise SourceError(
                f"{command_member}:{line_number}: invalid command literal"
            ) from error
        if not isinstance(command, str):
            continue
        action = command.replace("\r\n", "\n").replace("\r", "\n")
        if action.endswith("\n"):
            action = action[:-1]
        steps.append(
            RawStep(
                len(steps) + 1,
                action,
                None,
                f"{command_member}#line-{line_number}",
            )
        )
    return steps, "terminus2-commands-txt-strings"


def parse_sweagent(
    archive: Path, members: list[str], expected: int
) -> tuple[list[RawStep], str]:
    trajectory_member = next((name for name in members if name.endswith(".traj")), None)
    if not trajectory_member:
        raise SourceError("SWE-agent archive has no .traj file")
    data = load_json(archive, trajectory_member)
    trajectory = data.get("trajectory") if isinstance(data, dict) else None
    if not isinstance(trajectory, list):
        raise SourceError(f"{trajectory_member}: missing trajectory[]")
    steps: list[RawStep] = []
    for index, item in enumerate(trajectory):
        if not isinstance(item, dict):
            raise SourceError(f"{trajectory_member}: trajectory[{index}] is not an object")
        action = item.get("action")
        if isinstance(action, dict):
            action_text = json.dumps(action, ensure_ascii=False, sort_keys=True)
        elif action is None:
            action_text = ""
        else:
            action_text = str(action)
        observation = item.get("observation")
        steps.append(
            RawStep(
                index + 1,
                action_text,
                str(observation) if observation is not None else None,
                f"{trajectory_member}#trajectory-{index}",
            )
        )
    return steps, "sweagent-trajectory-elements"


ADAPTERS: dict[str, Callable[[Path, list[str], int], tuple[list[RawStep], str]]] = {
    "mini-SWE-agent": parse_miniswe,
    "OpenHands": parse_openhands,
    "Terminus2": parse_terminus2,
    "SWE-agent": parse_sweagent,
}

VIEW_FIELDS: dict[str, tuple[str, ...]] = {
    "semantic": ("phase", "action_kind"),
    "raw-action": ("raw_action_key",),
    "phase": ("phase",),
}

SUPPORT_LEVELS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("agent-model-difficulty-category", ("agent", "model", "difficulty", "category")),
    ("agent-model-category", ("agent", "model", "category")),
    ("agent-model", ("agent", "model")),
)


def action_kind(action: str) -> str:
    if not action.strip():
        return "other"
    for label, pattern in ACTION_KIND_RULES:
        if pattern.search(action):
            return label
    return "execute"


def raw_action_key(action: str) -> str:
    structured = re.search(r"\[([A-Za-z][A-Za-z0-9_-]*)\]", action)
    if structured:
        return structured.group(1).lower()
    text = action.strip()
    if not text:
        return "other"
    try:
        tokens = shlex.split(text, posix=True)
    except ValueError:
        tokens = text.split()
    if not tokens:
        return "other"

    while tokens and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tokens[0]):
        tokens.pop(0)
    wrappers = {"env", "sudo", "timeout", "command"}
    while tokens and Path(tokens[0]).name.lower() in wrappers:
        tokens.pop(0)
        while tokens and (tokens[0].startswith("-") or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tokens[0])):
            tokens.pop(0)
    if tokens and Path(tokens[0]).name.lower() in {"bash", "sh"}:
        try:
            command_index = tokens.index("-c")
        except ValueError:
            command_index = -1
        if command_index >= 0 and command_index + 1 < len(tokens):
            return raw_action_key(tokens[command_index + 1])
    return Path(tokens[0]).name.lower() if tokens else "other"


def agentprof_stack_value(value: str) -> str:
    """Mirror AgentProf safe_frame value normalization for declared groups."""
    out = ""
    for character in value.lower():
        if character.isascii() and (character.isalnum() or character in "._:/+-"):
            out += character
        elif not out.endswith("_"):
            out += "_"
    normalized = out.strip("_;")
    return normalized or "unknown"


def load_classifier(codetracer_root: Path, store_path: Path) -> Any:
    source = codetracer_root / "src"
    if not source.is_dir():
        raise SourceError(f"CodeTracer source directory not found: {source}")
    sys.path.insert(0, str(source))
    try:
        from codetracer.services.classification import ClassificationStore
    finally:
        sys.path.pop(0)
    if store_path.exists():
        raise SourceError(f"classification store must be absent at preflight start: {store_path}")
    return ClassificationStore(store_path=store_path)


def profile_steps(raw_steps: Iterable[RawStep], classifier: Any) -> list[ProfiledStep]:
    return [
        ProfiledStep(
            step.step_id,
            step.action,
            # The released classifier handles the empty string but raises on a
            # whitespace-only string because ``splitlines()[0]`` is absent.
            # Canonicalize only whitespace emptiness; preserve every non-empty
            # raw action byte-for-byte for classification and grouping.
            classifier.classify(step.action if step.action.strip() else ""),
            action_kind(step.action),
            agentprof_stack_value(raw_action_key(step.action)),
            step.source_ref,
        )
        for step in raw_steps
    ]


def write_operation_jsonl(path: Path, row: ManifestRow, steps: list[ProfiledStep]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        for step in steps:
            record = {
                "value": 1,
                "fields": {
                    "traj_id": row.traj_id,
                    "framework": row.agent,
                    "step_id": str(step.step_id),
                    "phase": step.phase,
                    "action_kind": step.action_kind,
                    "raw_action_key": step.raw_action_key,
                    "source_ref": step.source_ref,
                },
            }
            output.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_combined_operation_jsonl(
    path: Path,
    rows: Iterable[tuple[ManifestRow, list[ProfiledStep]]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        for row, steps in rows:
            for step in steps:
                record = {
                    "value": 1,
                    "fields": {
                        "traj_id": row.traj_id,
                        "traj_key": hashlib.sha256(row.traj_id.encode("utf-8")).hexdigest()[:24],
                        "step_id": str(step.step_id),
                        "phase": step.phase,
                        "action_kind": step.action_kind,
                        "raw_action_key": step.raw_action_key,
                        "source_ref": step.source_ref,
                    },
                }
                output.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def operation_file_counter(path: Path, fields: tuple[str, ...]) -> Counter[str]:
    counter: Counter[str] = Counter()
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise SourceError(f"{path}:{line_number}: invalid operation JSON") from error
            record_fields = record.get("fields")
            if not isinstance(record_fields, dict):
                raise SourceError(f"{path}:{line_number}: missing operation fields")
            try:
                frames = [f"{field}:{record_fields[field]}" for field in fields]
            except KeyError as error:
                raise SourceError(
                    f"{path}:{line_number}: missing stack field {error.args[0]}"
                ) from error
            counter[";".join(frames)] += int(record.get("value", 1))
    return counter


def verify_agentprof_views(
    binary: Path,
    operation_file: Path,
    out: Path,
    include_trajectory: bool,
) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for view, group_fields in VIEW_FIELDS.items():
        fields = (("traj_key",) + group_fields) if include_trajectory else group_fields
        observed = invoke_agentpprof(
            binary,
            operation_file,
            out / f"{view}.json",
            fields,
        )
        expected = operation_file_counter(operation_file, fields)
        if observed != expected:
            missing = expected - observed
            extra = observed - expected
            raise SourceError(
                f"AgentProf {view} count mismatch for {operation_file}: "
                f"expected_total={sum(expected.values())}, observed_total={sum(observed.values())}, "
                f"missing_examples={missing.most_common(5)}, extra_examples={extra.most_common(5)}"
            )


def expected_counter(steps: list[ProfiledStep], fields: tuple[str, ...]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for step in steps:
        frames = [f"{field}:{getattr(step, field)}" for field in fields]
        counter[";".join(frames)] += 1
    return counter


def invoke_agentpprof(
    binary: Path,
    operation_file: Path,
    output: Path,
    fields: tuple[str, ...],
) -> Counter[str]:
    command = [
        str(binary),
        "--operation-file",
        str(operation_file),
        "--view",
        "operations",
        "--format",
        "json",
        "--output",
        str(output),
        "--stack",
        ",".join(fields),
        "--deterministic-output",
    ]
    result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    status = json.loads(result.stdout)
    if status.get("status") != "ok":
        raise SourceError(f"AgentProf returned non-ok status: {status}")
    profile = json.loads(output.read_text(encoding="utf-8"))
    stacks = profile.get("profile", {}).get("stacks")
    if not isinstance(stacks, dict):
        raise SourceError(f"AgentProf output has no profile.stacks: {output}")
    return Counter({str(stack): int(value) for stack, value in stacks.items()})


def extract_profile_population(
    rows: Iterable[ManifestRow],
    raw_root: Path,
    classifier: Any,
) -> tuple[dict[str, tuple[ManifestRow, list[ProfiledStep], str]], list[dict[str, str]]]:
    profiles: dict[str, tuple[ManifestRow, list[ProfiledStep], str]] = {}
    failures: list[dict[str, str]] = []
    for row in rows:
        archive = artifact_path(raw_root, row)
        if archive is None:
            failures.append(
                {"traj_id": row.traj_id, "reason": "missing archive", "adapter": "-"}
            )
            continue
        try:
            members = tar_members(archive)
            raw_steps, adapter = ADAPTERS[row.agent](archive, members, row.step_count)
            if len(raw_steps) != row.step_count:
                raise SourceError(
                    f"{adapter} emitted {len(raw_steps)} operations; public step_count is {row.step_count}"
                )
            if [step.step_id for step in raw_steps] != list(range(1, row.step_count + 1)):
                raise SourceError("adapter did not emit consecutive one-based step IDs")
            profiles[row.traj_id] = (row, profile_steps(raw_steps, classifier), adapter)
        except (SourceError, subprocess.CalledProcessError) as error:
            failures.append(
                {"traj_id": row.traj_id, "reason": str(error), "adapter": "-"}
            )
    return profiles, failures


def write_full_source_coverage(
    path: Path,
    rows: list[ManifestRow],
    profiles: dict[str, tuple[ManifestRow, list[ProfiledStep], str]],
    failures: list[dict[str, str]],
) -> None:
    failure_by_id = {failure["traj_id"]: failure for failure in failures}
    if set(profiles) & set(failure_by_id):
        raise SourceError("source coverage contains both success and failure for a trajectory")
    if set(profiles) | set(failure_by_id) != {row.traj_id for row in rows}:
        raise SourceError("source coverage is not terminal for every manifest trajectory")
    status_counts: Counter[str] = Counter()
    framework_counts: Counter[tuple[str, str]] = Counter()
    for row in rows:
        status = "source-valid" if row.traj_id in profiles else "excluded"
        status_counts[status] += 1
        framework_counts[(row.agent, status)] += 1
    lines = [
        "# CodeTraceBench Full Source Coverage",
        "",
        f"**Status:** COMPLETE — all {len(rows)} full-manifest trajectories have a terminal source status.",
        "",
        "This ledger was produced from the safe manifest projection and public raw archives. "
        "It does not load step annotations. Source-invalid rows are excluded rather than "
        "truncated, padded, synthesized, or count-fitted.",
        "",
        "## Summary",
        "",
        "| Framework | Source-valid | Excluded |",
        "|---|---:|---:|",
    ]
    for framework in sorted({row.agent for row in rows}):
        lines.append(
            f"| {markdown_escape(framework)} | "
            f"{framework_counts[(framework, 'source-valid')]} | "
            f"{framework_counts[(framework, 'excluded')]} |"
        )
    lines.extend(
        [
            "",
            f"Overall: {status_counts['source-valid']} source-valid; "
            f"{status_counts['excluded']} excluded.",
            "",
            "## Terminal Ledger",
            "",
            "| Trajectory | Framework | Outcome | Declared steps | Status | Adapter/reason |",
            "|---|---|---|---:|---|---|",
        ]
    )
    for row in sorted(rows, key=lambda item: item.traj_id):
        if row.traj_id in profiles:
            _, steps, adapter = profiles[row.traj_id]
            status = "source-valid"
            detail = f"{adapter}; {len(steps)} operations"
        else:
            status = "excluded"
            detail = failure_by_id[row.traj_id]["reason"]
        outcome = "missing" if row.solved is None else str(row.solved).lower()
        lines.append(
            f"| `{markdown_escape(row.traj_id)}` | {markdown_escape(row.agent)} | "
            f"{outcome} | {row.step_count} | {status} | {markdown_escape(detail)} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def group_for_step(step: ProfiledStep, view: str) -> tuple[str, ...]:
    return tuple(str(getattr(step, field)) for field in VIEW_FIELDS[view])


def support_key(row: ManifestRow, fields: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(getattr(row, field)) for field in fields)


def build_reference_index(
    reference_profiles: dict[str, tuple[ManifestRow, list[ProfiledStep], str]],
    *,
    outcome_override: dict[str, bool] | None = None,
    task_weights: Counter[str] | None = None,
    group_cache: dict[str, dict[str, Counter[tuple[str, ...]]]] | None = None,
) -> dict[
    str,
    dict[
        tuple[str, ...],
        dict[bool, dict[str, Any]],
    ],
]:
    index: dict[str, dict[tuple[str, ...], dict[bool, dict[str, Any]]]] = {}
    for level_name, fields in SUPPORT_LEVELS:
        level_index: dict[tuple[str, ...], dict[bool, dict[str, Any]]] = {}
        for row, steps, _ in reference_profiles.values():
            weight = 1 if task_weights is None else int(task_weights[row.task_name])
            if weight <= 0:
                continue
            outcome_value = (
                outcome_override[row.traj_id]
                if outcome_override is not None and row.traj_id in outcome_override
                else row.solved
            )
            if outcome_value is None:
                continue
            key = support_key(row, fields)
            outcome = bool(outcome_value)
            cell = level_index.setdefault(key, {})
            cohort = cell.setdefault(
                outcome,
                {
                    "trajectory_count": 0,
                    "task_trajectory_count": {},
                    "totals": Counter(),
                    "task_totals": {},
                    "groups": {view: Counter() for view in VIEW_FIELDS},
                    "task_groups": {view: {} for view in VIEW_FIELDS},
                },
            )
            cohort["trajectory_count"] += weight
            cohort["task_trajectory_count"].setdefault(row.task_name, 0)
            cohort["task_trajectory_count"][row.task_name] += weight
            cohort["totals"]["operations"] += len(steps) * weight
            cohort["task_totals"].setdefault(row.task_name, 0)
            cohort["task_totals"][row.task_name] += len(steps) * weight
            for view in VIEW_FIELDS:
                groups = (
                    group_cache[row.traj_id][view]
                    if group_cache is not None
                    else Counter(group_for_step(step, view) for step in steps)
                )
                weighted_groups = Counter(
                    {group: count * weight for group, count in groups.items()}
                )
                cohort["groups"][view].update(weighted_groups)
                task_groups = cohort["task_groups"][view].setdefault(
                    row.task_name, Counter()
                )
                task_groups.update(weighted_groups)
        index[level_name] = level_index
    return index


def build_group_cache(
    profiles: dict[str, tuple[ManifestRow, list[ProfiledStep], str]],
) -> dict[str, dict[str, Counter[tuple[str, ...]]]]:
    return {
        traj_id: {
            view: Counter(group_for_step(step, view) for step in steps)
            for view in VIEW_FIELDS
        }
        for traj_id, (_, steps, _) in profiles.items()
    }


def supported_target_cell(
    target: ManifestRow,
    reference_index: dict[str, dict[tuple[str, ...], dict[bool, dict[str, Any]]]],
) -> tuple[str, tuple[str, ...], dict[bool, dict[str, Any]], dict[bool, int]]:
    for level_name, fields in SUPPORT_LEVELS:
        key = support_key(target, fields)
        cell = reference_index[level_name].get(key, {})
        counts: dict[bool, int] = {}
        for outcome in (False, True):
            cohort = cell.get(outcome)
            if cohort is None:
                counts[outcome] = 0
                continue
            counts[outcome] = int(cohort["trajectory_count"]) - int(
                cohort["task_trajectory_count"].get(target.task_name, 0)
            )
        if counts[False] >= 10 and counts[True] >= 10:
            return level_name, key, cell, counts
    raise SourceError(f"{target.traj_id}: no source-valid 10-per-outcome reference stratum")


def differential_score_table(
    target: ManifestRow,
    cell: dict[bool, dict[str, Any]],
    view: str,
) -> dict[tuple[str, ...], float]:
    normalized: dict[bool, tuple[Counter[tuple[str, ...]], int]] = {}
    for outcome in (False, True):
        cohort = cell[outcome]
        counts = Counter(cohort["groups"][view])
        counts.subtract(cohort["task_groups"][view].get(target.task_name, Counter()))
        counts += Counter()  # Drop non-positive keys after exact subtraction.
        total = int(cohort["totals"]["operations"]) - int(
            cohort["task_totals"].get(target.task_name, 0)
        )
        if total <= 0 or sum(counts.values()) != total:
            raise SourceError(
                f"{target.traj_id}: invalid {view} outcome={outcome} reference total"
            )
        normalized[outcome] = (counts, total)
    failed, failed_total = normalized[False]
    successful, successful_total = normalized[True]
    groups = set(failed) | set(successful)
    return {
        group: failed[group] / failed_total - successful[group] / successful_total
        for group in groups
    }


def score_targets(
    target_profiles: dict[str, tuple[ManifestRow, list[ProfiledStep], str]],
    reference_index: dict[str, dict[tuple[str, ...], dict[bool, dict[str, Any]]]],
) -> tuple[dict[str, dict[str, Any]], Counter[str]]:
    scored: dict[str, dict[str, Any]] = {}
    support_counts: Counter[str] = Counter()
    for traj_id in sorted(target_profiles):
        row, steps, adapter = target_profiles[traj_id]
        level_name, key, cell, cohort_counts = supported_target_cell(row, reference_index)
        support_counts[level_name] += 1
        method_records: dict[str, list[dict[str, Any]]] = {}
        for view in VIEW_FIELDS:
            scores = differential_score_table(row, cell, view)
            method_records[view] = [
                {
                    "step_id": step.step_id,
                    "group": group_for_step(step, view),
                    "score": scores.get(group_for_step(step, view), 0.0),
                }
                for step in steps
            ]
        scored[traj_id] = {
            "row": row,
            "adapter": adapter,
            "support_level": level_name,
            "support_key": key,
            "failed_references": cohort_counts[False],
            "successful_references": cohort_counts[True],
            "methods": method_records,
        }
    return scored, support_counts


def build_custom_reference_index(
    reference_profiles: dict[str, tuple[ManifestRow, list[ProfiledStep], str]],
    group_fn: Callable[[ProfiledStep], tuple[str, ...]],
) -> dict[str, dict[tuple[str, ...], dict[bool, dict[str, Any]]]]:
    index: dict[str, dict[tuple[str, ...], dict[bool, dict[str, Any]]]] = {}
    for level_name, fields in SUPPORT_LEVELS:
        level_index: dict[tuple[str, ...], dict[bool, dict[str, Any]]] = {}
        for row, steps, _ in reference_profiles.values():
            if row.solved is None:
                continue
            key = support_key(row, fields)
            cohort = level_index.setdefault(key, {}).setdefault(
                bool(row.solved),
                {
                    "total": 0,
                    "task_totals": {},
                    "groups": Counter(),
                    "task_groups": {},
                },
            )
            groups = Counter(group_fn(step) for step in steps)
            cohort["total"] += len(steps)
            cohort["task_totals"].setdefault(row.task_name, 0)
            cohort["task_totals"][row.task_name] += len(steps)
            cohort["groups"].update(groups)
            cohort["task_groups"].setdefault(row.task_name, Counter()).update(groups)
        index[level_name] = level_index
    return index


def score_custom_view(
    target_profiles: dict[str, tuple[ManifestRow, list[ProfiledStep], str]],
    primary_scored: dict[str, dict[str, Any]],
    reference_index: dict[str, dict[tuple[str, ...], dict[bool, dict[str, Any]]]],
    group_fn: Callable[[ProfiledStep], tuple[str, ...]],
    view_name: str,
) -> dict[str, dict[str, Any]]:
    scored: dict[str, dict[str, Any]] = {}
    for traj_id, (row, steps, adapter) in target_profiles.items():
        support = primary_scored[traj_id]
        cell = reference_index[support["support_level"]][support["support_key"]]
        normalized: dict[bool, tuple[Counter[tuple[str, ...]], int]] = {}
        for outcome in (False, True):
            cohort = cell[outcome]
            groups = Counter(cohort["groups"])
            groups.subtract(cohort["task_groups"].get(row.task_name, Counter()))
            groups += Counter()
            total = int(cohort["total"]) - int(
                cohort["task_totals"].get(row.task_name, 0)
            )
            if total <= 0 or sum(groups.values()) != total:
                raise SourceError(
                    f"{traj_id}: invalid custom-view outcome={outcome} reference total"
                )
            normalized[outcome] = groups, total
        failed, failed_total = normalized[False]
        successful, successful_total = normalized[True]
        score_table = {
            group: failed[group] / failed_total
            - successful[group] / successful_total
            for group in set(failed) | set(successful)
        }
        scored[traj_id] = {
            "row": row,
            "adapter": adapter,
            "methods": {
                view_name: [
                    {
                        "step_id": step.step_id,
                        "group": group_fn(step),
                        "score": score_table.get(group_fn(step), 0.0),
                    }
                    for step in steps
                ]
            },
        }
    return scored


def build_absolute_reference_index(
    profiles: dict[str, tuple[ManifestRow, list[ProfiledStep], str]],
    group_fn: Callable[[ProfiledStep], tuple[str, ...]],
) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row, steps, _ in profiles.values():
        key = (row.agent, row.model)
        cell = index.setdefault(
            key,
            {"total": 0, "task_totals": {}, "groups": Counter(), "task_groups": {}},
        )
        groups = Counter(group_fn(step) for step in steps)
        cell["total"] += len(steps)
        cell["task_totals"].setdefault(row.task_name, 0)
        cell["task_totals"][row.task_name] += len(steps)
        cell["groups"].update(groups)
        cell["task_groups"].setdefault(row.task_name, Counter()).update(groups)
    return index


def score_absolute_view(
    target_profiles: dict[str, tuple[ManifestRow, list[ProfiledStep], str]],
    reference_index: dict[tuple[str, str], dict[str, Any]],
    group_fn: Callable[[ProfiledStep], tuple[str, ...]],
    view_name: str,
) -> dict[str, dict[str, Any]]:
    scored: dict[str, dict[str, Any]] = {}
    for traj_id, (row, steps, adapter) in target_profiles.items():
        cell = reference_index[(row.agent, row.model)]
        groups = Counter(cell["groups"])
        groups.subtract(cell["task_groups"].get(row.task_name, Counter()))
        groups += Counter()
        total = int(cell["total"]) - int(cell["task_totals"].get(row.task_name, 0))
        if total <= 0 or sum(groups.values()) != total:
            raise SourceError(f"{traj_id}: invalid absolute-hotspot reference total")
        scored[traj_id] = {
            "row": row,
            "adapter": adapter,
            "methods": {
                view_name: [
                    {
                        "step_id": step.step_id,
                        "group": group_fn(step),
                        "score": groups[group_fn(step)] / total,
                    }
                    for step in steps
                ]
            },
        }
    return scored


def make_flat_control(
    target_profiles: dict[str, tuple[ManifestRow, list[ProfiledStep], str]],
    view_name: str = "flat",
) -> dict[str, dict[str, Any]]:
    return {
        traj_id: {
            "row": row,
            "adapter": adapter,
            "methods": {
                view_name: [
                    {"step_id": step.step_id, "group": ("all",), "score": 0.0}
                    for step in steps
                ]
            },
        }
        for traj_id, (row, steps, adapter) in target_profiles.items()
    }


def partition_bucket(raw_key: str, seed: int, bucket_count: int) -> tuple[str, ...]:
    digest = hashlib.sha256(
        str(seed).encode("utf-8") + b"\0" + raw_key.encode("utf-8")
    ).digest()
    bucket = int.from_bytes(digest[:8], "big") % bucket_count
    width = max(2, len(str(bucket_count - 1)))
    return (f"bucket-{bucket:0{width}d}",)


def select_frequency_matched_partitions(
    all_profiles: dict[str, tuple[ManifestRow, list[ProfiledStep], str]],
    *,
    first_seed: int,
    candidate_count: int,
    retain_count: int,
) -> tuple[int, list[tuple[int, float]]]:
    semantic_mass: Counter[tuple[str, ...]] = Counter()
    raw_mass: Counter[str] = Counter()
    for _, steps, _ in all_profiles.values():
        semantic_mass.update((step.phase, step.action_kind) for step in steps)
        raw_mass.update(step.raw_action_key for step in steps)
    bucket_count = len(semantic_mass)
    total = sum(semantic_mass.values())
    semantic_shares = sorted(
        (count / total for count in semantic_mass.values()), reverse=True
    )
    candidates: list[tuple[float, int]] = []
    for seed in range(first_seed, first_seed + candidate_count):
        bucket_mass: Counter[tuple[str, ...]] = Counter()
        for raw_key, count in raw_mass.items():
            bucket_mass[partition_bucket(raw_key, seed, bucket_count)] += count
        if len(bucket_mass) != bucket_count:
            continue
        shares = sorted((count / total for count in bucket_mass.values()), reverse=True)
        distance = sum(abs(left - right) for left, right in zip(shares, semantic_shares))
        candidates.append((distance, seed))
    if len(candidates) < retain_count:
        raise SourceError(
            f"only {len(candidates)} non-empty frequency partitions for {retain_count} requested"
        )
    candidates.sort()
    return bucket_count, [(seed, distance) for distance, seed in candidates[:retain_count]]


def run_outcome_null_trials(
    reference_profiles: dict[str, tuple[ManifestRow, list[ProfiledStep], str]],
    target_profiles: dict[str, tuple[ManifestRow, list[ProfiledStep], str]],
    gold: dict[str, set[int]],
    *,
    repetitions: int,
    seed: int,
    group_cache: dict[str, dict[str, Counter[tuple[str, ...]]]],
) -> dict[str, list[dict[str, float | int | None]]]:
    cells: dict[tuple[str, str, str, str], list[ManifestRow]] = {}
    for row, _, _ in reference_profiles.values():
        if row.solved is None:
            continue
        key = (row.agent, row.model, row.difficulty, row.category)
        cells.setdefault(key, []).append(row)
    ordered_cells = [sorted(rows, key=lambda row: row.traj_id) for _, rows in sorted(cells.items())]
    rng = random.Random(seed)
    results: dict[str, list[dict[str, float | int | None]]] = {
        view: [] for view in VIEW_FIELDS
    }
    for repetition in range(repetitions):
        override: dict[str, bool] = {}
        for rows in ordered_cells:
            outcomes = [bool(row.solved) for row in rows]
            rng.shuffle(outcomes)
            override.update(
                {row.traj_id: outcome for row, outcome in zip(rows, outcomes, strict=True)}
            )
        index = build_reference_index(
            reference_profiles,
            outcome_override=override,
            group_cache=group_cache,
        )
        scored, _ = score_targets(target_profiles, index)
        for view in VIEW_FIELDS:
            results[view].append(pooled_tie_block_metrics(scored, gold, view))
        if (repetition + 1) % 100 == 0 or repetition + 1 == repetitions:
            print(f"outcome-null {repetition + 1}/{repetitions}", flush=True)
    return results


def run_task_cluster_bootstrap(
    reference_profiles: dict[str, tuple[ManifestRow, list[ProfiledStep], str]],
    target_profiles: dict[str, tuple[ManifestRow, list[ProfiledStep], str]],
    gold: dict[str, set[int]],
    *,
    repetitions: int,
    seed: int,
    group_cache: dict[str, dict[str, Counter[tuple[str, ...]]]],
) -> tuple[dict[str, list[dict[str, float | int | None]]], int]:
    tasks = sorted({row.task_name for row, _, _ in reference_profiles.values()})
    rng = random.Random(seed)
    results: dict[str, list[dict[str, float | int | None]]] = {
        view: [] for view in VIEW_FIELDS
    }
    attempts = 0
    maximum_attempts = max(repetitions * 3, repetitions + 100)
    while len(results["semantic"]) < repetitions and attempts < maximum_attempts:
        attempts += 1
        task_weights: Counter[str] = Counter(rng.choice(tasks) for _ in tasks)
        sampled_targets = {
            traj_id: profile
            for traj_id, profile in target_profiles.items()
            if task_weights[profile[0].task_name] > 0
        }
        if not sampled_targets:
            continue
        try:
            index = build_reference_index(
                reference_profiles,
                task_weights=task_weights,
                group_cache=group_cache,
            )
            scored, _ = score_targets(sampled_targets, index)
        except SourceError:
            continue
        for view in VIEW_FIELDS:
            results[view].append(
                pooled_tie_block_metrics(
                    scored,
                    gold,
                    view,
                    target_task_weights=task_weights,
                )
            )
        completed = len(results["semantic"])
        if completed % 250 == 0 or completed == repetitions:
            print(
                f"task-bootstrap {completed}/{repetitions} valid; attempts={attempts}",
                flush=True,
            )
    if len(results["semantic"]) != repetitions:
        raise SourceError(
            f"only {len(results['semantic'])}/{repetitions} valid task-bootstrap replicates "
            f"after {attempts} attempts"
        )
    return results, attempts


def summarize_repeated_metric(
    results: list[dict[str, float | int | None]], metric: str
) -> dict[str, float]:
    values = [float(result[metric]) for result in results if result[metric] is not None]
    if len(values) != len(results):
        raise SourceError(f"repeated metric {metric} contains undefined values")
    return {
        "mean": sum(values) / len(values),
        "p025": percentile(values, 0.025),
        "p500": percentile(values, 0.500),
        "p975": percentile(values, 0.975),
    }


def write_prediction_markdown(
    path: Path,
    scored: dict[str, dict[str, Any]],
) -> None:
    """Persist every prediction before the terminal label projection."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CodeTraceBench RQ2 Predictions (Pre-Label)",
        "",
        "These scores were written before the runner projected `incorrect_stages`. "
        "They use only raw operations, public outcome/cohort metadata, and task-held-out "
        "reference profiles.",
        "",
    ]
    for traj_id in sorted(scored):
        record = scored[traj_id]
        row: ManifestRow = record["row"]
        lines.extend(
            [
                f"## `{markdown_escape(traj_id)}`",
                "",
                f"- Adapter: `{record['adapter']}`",
                f"- Support: `{record['support_level']}` with "
                f"{record['failed_references']} failed and "
                f"{record['successful_references']} successful different-task references",
                f"- Public step count: {row.step_count}",
                "",
                "| Step | Semantic group | Semantic score | Raw-action group | Raw score | Phase group | Phase score |",
                "|---:|---|---:|---|---:|---|---:|",
            ]
        )
        semantic = record["methods"]["semantic"]
        raw = record["methods"]["raw-action"]
        phase = record["methods"]["phase"]
        for sem, raw_item, phase_item in zip(semantic, raw, phase, strict=True):
            if not (
                sem["step_id"] == raw_item["step_id"] == phase_item["step_id"]
            ):
                raise SourceError(f"{traj_id}: method step IDs diverged before prediction write")
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(sem["step_id"]),
                        markdown_escape(" -> ".join(sem["group"])),
                        f"{sem['score']:.12g}",
                        markdown_escape(" -> ".join(raw_item["group"])),
                        f"{raw_item['score']:.12g}",
                        markdown_escape(" -> ".join(phase_item["group"])),
                        f"{phase_item['score']:.12g}",
                    ]
                )
                + " |"
            )
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def terminal_load_incorrect_labels(
    verified_manifest: Path,
    allowed_ids: set[str],
) -> dict[str, set[int]]:
    # This is intentionally the only function that projects a step-label
    # column.  Call it only after prediction Markdown has been durably written.
    rows = pq.read_table(
        verified_manifest, columns=["traj_id", "incorrect_stages"]
    ).to_pylist()
    gold: dict[str, set[int]] = {}
    for row in rows:
        traj_id = str(row["traj_id"])
        if traj_id not in allowed_ids:
            continue
        step_ids: set[int] = set()
        for stage in row.get("incorrect_stages") or []:
            for step_id in stage.get("incorrect_step_ids") or []:
                step_ids.add(int(step_id))
        gold[traj_id] = step_ids
    missing = allowed_ids - set(gold)
    if missing:
        raise SourceError(f"terminal label join missed targets: {sorted(missing)}")
    return gold


def terminal_load_label_families(
    verified_manifest: Path,
    allowed_ids: set[str],
) -> dict[str, dict[str, set[int]]]:
    """Load incorrect and unuseful IDs together only after predictions exist."""
    rows = pq.read_table(
        verified_manifest, columns=["traj_id", "incorrect_stages"]
    ).to_pylist()
    incorrect: dict[str, set[int]] = {}
    unuseful: dict[str, set[int]] = {}
    for row in rows:
        traj_id = str(row["traj_id"])
        if traj_id not in allowed_ids:
            continue
        incorrect_ids: set[int] = set()
        unuseful_ids: set[int] = set()
        for stage in row.get("incorrect_stages") or []:
            incorrect_ids.update(
                int(step_id) for step_id in stage.get("incorrect_step_ids") or []
            )
            unuseful_ids.update(
                int(step_id) for step_id in stage.get("unuseful_step_ids") or []
            )
        incorrect[traj_id] = incorrect_ids
        unuseful[traj_id] = unuseful_ids
    missing = allowed_ids - set(incorrect)
    if missing:
        raise SourceError(f"terminal label join missed targets: {sorted(missing)}")
    union = {
        traj_id: incorrect[traj_id] | unuseful[traj_id] for traj_id in incorrect
    }
    return {"incorrect": incorrect, "unuseful": unuseful, "union": union}


def pooled_tie_block_metrics(
    scored: dict[str, dict[str, Any]],
    gold: dict[str, set[int]],
    view: str,
    target_task_weights: Counter[str] | None = None,
) -> dict[str, float | int | None]:
    by_score: dict[float, list[int]] = {}
    zero_positive_trajectories = 0
    for traj_id, record in scored.items():
        row: ManifestRow = record["row"]
        weight = (
            1
            if target_task_weights is None
            else int(target_task_weights[row.task_name])
        )
        if weight <= 0:
            continue
        positives = gold[traj_id]
        zero_positive_trajectories += int(not positives) * weight
        for item in record["methods"][view]:
            score = float(item["score"])
            counts = by_score.setdefault(score, [0, 0])
            counts[0] += weight
            counts[1] += int(int(item["step_id"]) in positives) * weight
    blocks = [
        (score, counts[0], counts[1])
        for score, counts in sorted(by_score.items(), reverse=True)
    ]
    total_steps = sum(block_size for _, block_size, _ in blocks)
    total_positive = sum(block_positive for _, _, block_positive in blocks)
    if total_steps == 0:
        raise SourceError(f"{view}: no scored steps")

    if total_positive == 0:
        return {
            "average_precision": None,
            "recall_at_30_work": None,
            "work_at_50_recall": None,
            "first_positive_work": None,
            "total_steps": total_steps,
            "total_positive": 0,
            "tie_blocks": len(blocks),
            "zero_positive_trajectories": zero_positive_trajectories,
        }

    average_precision = 0.0
    cumulative_steps = 0
    cumulative_positive = 0
    recall_at_30 = 0.0
    work_at_50: float | None = None
    first_positive_work: float | None = None
    within_30 = True
    for _, block_size, block_positive in blocks:
        next_steps = cumulative_steps + block_size
        next_positive = cumulative_positive + block_positive
        precision_after = next_positive / next_steps
        average_precision += precision_after * (block_positive / total_positive)
        if within_30 and next_steps / total_steps <= 0.30:
            recall_at_30 = next_positive / total_positive
        else:
            within_30 = False
        if work_at_50 is None and next_positive / total_positive >= 0.50:
            work_at_50 = next_steps / total_steps
        if first_positive_work is None and block_positive > 0:
            first_positive_work = next_steps / total_steps
        cumulative_steps = next_steps
        cumulative_positive = next_positive
    return {
        "average_precision": average_precision,
        "recall_at_30_work": recall_at_30,
        "work_at_50_recall": work_at_50,
        "first_positive_work": first_positive_work,
        "total_steps": total_steps,
        "total_positive": total_positive,
        "tie_blocks": len(blocks),
        "zero_positive_trajectories": zero_positive_trajectories,
    }


def selected_step_ids_at_budget(
    method_records: list[dict[str, Any]], budget: float = 0.30
) -> tuple[set[int], int]:
    by_score: dict[float, list[int]] = {}
    for item in method_records:
        by_score.setdefault(float(item["score"]), []).append(int(item["step_id"]))
    total = len(method_records)
    selected: set[int] = set()
    exposed_blocks = 0
    for _, step_ids in sorted(by_score.items(), key=lambda item: item[0], reverse=True):
        if (len(selected) + len(step_ids)) / total > budget:
            break
        selected.update(step_ids)
        exposed_blocks += 1
    return selected, exposed_blocks


def compatibility_metrics(
    scored: dict[str, dict[str, Any]],
    gold: dict[str, set[int]],
    view: str,
) -> dict[str, float | int | None]:
    precision_values: list[float] = []
    recall_values: list[float] = []
    f1_values: list[float] = []
    zero_burdens: list[float] = []
    zero_exposed = 0
    zero_steps = 0
    exposed_groups = 0
    unique_groups: set[tuple[str, ...]] = set()
    for traj_id, record in scored.items():
        method = record["methods"][view]
        selected, block_count = selected_step_ids_at_budget(method)
        exposed_groups += block_count
        unique_groups.update(tuple(item["group"]) for item in method)
        positives = gold[traj_id]
        if not positives:
            zero_exposed += len(selected)
            zero_steps += len(method)
            zero_burdens.append(len(selected) / len(method))
            continue
        true_positive = len(selected & positives)
        precision = true_positive / len(selected) if selected else 0.0
        recall = true_positive / len(positives)
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall > 0
            else 0.0
        )
        precision_values.append(precision)
        recall_values.append(recall)
        f1_values.append(f1)
    mean = lambda values: sum(values) / len(values) if values else None
    return {
        "eligible_positive_trajectories": len(precision_values),
        "macro_precision": mean(precision_values),
        "macro_recall": mean(recall_values),
        "macro_f1": mean(f1_values),
        "zero_positive_trajectories": len(zero_burdens),
        "zero_positive_pooled_burden": (
            zero_exposed / zero_steps if zero_steps else None
        ),
        "zero_positive_macro_burden": mean(zero_burdens),
        "exposed_score_blocks": exposed_groups,
        "unique_groups": len(unique_groups),
    }


def subset_scored(
    scored: dict[str, dict[str, Any]], framework: str
) -> dict[str, dict[str, Any]]:
    return {
        traj_id: record
        for traj_id, record in scored.items()
        if record["row"].agent == framework
    }


def percentile(values: list[float], probability: float) -> float:
    if not values:
        raise SourceError("cannot compute percentile of an empty sample")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def write_end_to_end_report(
    path: Path,
    mode: str,
    full_rows: list[ManifestRow],
    verified_rows: list[ManifestRow],
    target_candidates: list[ManifestRow],
    target_profiles: dict[str, tuple[ManifestRow, list[ProfiledStep], str]],
    target_failures: list[dict[str, str]],
    reference_candidates: list[ManifestRow],
    reference_profiles: dict[str, tuple[ManifestRow, list[ProfiledStep], str]],
    reference_failures: list[dict[str, str]],
    support_counts: Counter[str],
    metrics: dict[str, dict[str, float | int | None]],
    prediction_path: Path,
) -> None:
    status = "PASS" if target_profiles and not (set(row.traj_id for row in target_candidates) - set(target_profiles)) else "PARTIAL PASS"
    if mode == "real-preflight" and target_failures:
        status = "FAIL"
    if mode == "full":
        status = "INCOMPLETE"
    lines = [
        f"# CodeTraceBench RQ2 {'REAL PREFLIGHT' if mode == 'real-preflight' else 'Primary Full-Path'} Report",
        "",
        f"**Status:** {status}",
        "",
        "## End-To-End Boundary",
        "",
        f"The runner loaded {len(full_rows)} full-manifest and {len(verified_rows)} verified safe-projection rows, "
        f"extracted {len(reference_profiles)}/{len(reference_candidates)} candidate reference trajectories and "
        f"{len(target_profiles)}/{len(target_candidates)} target trajectories, invoked release AgentProf for "
        "semantic/raw-action/phase reference and target views, computed task-held-out failed-minus-successful "
        "scores, and wrote predictions before the terminal label join.",
        "",
        f"Pre-label predictions: `{prediction_path}`",
        "",
        "## Reference Support",
        "",
        "| Fallback level | Targets |",
        "|---|---:|",
    ]
    for level_name, _ in SUPPORT_LEVELS:
        lines.append(f"| `{level_name}` | {support_counts[level_name]} |")
    lines.extend(
        [
            "",
            "## Terminal Incorrect-Step Metrics",
            "",
            "| Method | Pooled tie-aware AP | Recall @ 30% work | Work @ 50% recall | Steps | Incorrect steps | Tie blocks | Zero-positive targets |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for view in VIEW_FIELDS:
        result = metrics[view]
        def show(value: Any) -> str:
            return "undefined" if value is None else (f"{value:.6f}" if isinstance(value, float) else str(value))
        lines.append(
            "| "
            + " | ".join(
                [
                    view,
                    show(result["average_precision"]),
                    show(result["recall_at_30_work"]),
                    show(result["work_at_50_recall"]),
                    str(result["total_steps"]),
                    str(result["total_positive"]),
                    str(result["tie_blocks"]),
                    str(result["zero_positive_trajectories"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Source Exclusions",
            "",
            f"Target failures: {len(target_failures)}. Reference failures: {len(reference_failures)}. "
            "Every exclusion is based on missing raw source, adapter failure, or public-count mismatch "
            "before label projection; no trajectory is truncated or padded.",
            "",
            "| Population | Trajectory | Reason |",
            "|---|---|---|",
        ]
    )
    for population, failures in (("target", target_failures), ("reference", reference_failures)):
        for failure in failures:
            lines.append(
                f"| {population} | `{markdown_escape(failure['traj_id'])}` | "
                f"{markdown_escape(failure['reason'])} |"
            )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            (
                "REAL PREFLIGHT is complete when status is PASS: the actual real-input, source alignment, "
                "AgentProf, matching, scoring, prediction, terminal-label, and metric path all ran. "
                "Metric sign is not a preflight gate. Independent review is still required before the full run."
                if mode == "real-preflight"
                else "This report covers the shared deterministic primary path. Full declared controls, nulls, "
                "and uncertainty runs must also complete before scientific result review."
            ),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def metric_text(value: Any) -> str:
    if value is None:
        return "undefined"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def write_partition_selection(
    path: Path,
    *,
    bucket_count: int,
    candidate_count: int,
    partitions: list[tuple[int, float]],
    first_seed: int,
) -> None:
    lines = [
        "# Frequency-Matched Partition Selection (Pre-Label)",
        "",
        "This selection used only source-valid operation mass and normalized raw-action keys. "
        "It was written before the runner projected `incorrect_stages`.",
        "",
        f"- Semantic occupied group count: {bucket_count}",
        f"- Candidate seeds: {candidate_count}, beginning at {first_seed}",
        f"- Retained non-empty closest-mass partitions: {len(partitions)}",
        "",
        "| Rank | Seed | L1 mass-share distance |",
        "|---:|---:|---:|",
    ]
    for rank, (seed, distance) in enumerate(partitions, 1):
        lines.append(f"| {rank} | {seed} | {distance:.12g} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_full_experiment_report(path: Path, result: dict[str, Any]) -> None:
    status = result["status"]
    lines = [
        "# CodeTraceBench RQ2 Complete Experiment Report",
        "",
        f"**Status:** {status}",
        "",
        "## Population And Execution",
        "",
        f"- Full manifest rows with terminal source status: {result['full_rows']}",
        f"- Source-valid full trajectories: {result['source_valid_full']}",
        f"- Explicit source exclusions: {result['source_excluded_full']}",
        f"- Source-valid failed verified targets: {result['target_count']}",
        f"- Target steps: {result['target_steps']}",
        f"- Source-valid outcome-bearing references: {result['reference_count']}",
        f"- Runtime: {result['runtime_seconds']:.3f} seconds",
        "",
        f"Coverage ledger: `{result['coverage_path']}`",
        f"Pre-label predictions: `{result['prediction_path']}`",
        f"Pre-label partition selection: `{result['partition_path']}`",
        "",
        "## Primary Incorrect-Step Result",
        "",
        "| Method | Pooled tie-aware AP | Recall @ 30% work | Work @ 50% recall | First-positive work | Steps | Incorrect steps | Zero-positive targets |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for view in VIEW_FIELDS:
        metric = result["primary_metrics"][view]
        lines.append(
            "| "
            + " | ".join(
                [
                    view,
                    metric_text(metric["average_precision"]),
                    metric_text(metric["recall_at_30_work"]),
                    metric_text(metric["work_at_50_recall"]),
                    metric_text(metric["first_positive_work"]),
                    str(metric["total_steps"]),
                    str(metric["total_positive"]),
                    str(metric["zero_positive_trajectories"]),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## CodeTracer-Compatible Per-Trajectory Metrics",
            "",
            "Only trajectories with at least one incorrect step enter macro P/R/F1. "
            "Zero-positive burden is reported separately.",
            "",
            "| Method | Eligible | Macro P | Macro R | Macro F1 | Zero-positive targets | Pooled zero-positive burden | Macro zero-positive burden | Unique groups |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for view in VIEW_FIELDS:
        metric = result["compatibility"][view]
        lines.append(
            "| "
            + " | ".join(
                [
                    view,
                    str(metric["eligible_positive_trajectories"]),
                    metric_text(metric["macro_precision"]),
                    metric_text(metric["macro_recall"]),
                    metric_text(metric["macro_f1"]),
                    str(metric["zero_positive_trajectories"]),
                    metric_text(metric["zero_positive_pooled_burden"]),
                    metric_text(metric["zero_positive_macro_burden"]),
                    str(metric["unique_groups"]),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Secondary Label Families",
            "",
            "These use the frozen pre-label scores and cannot select the primary method.",
            "",
            "| Label family | Method | AP | Recall @ 30% | Work @ 50% | Positive steps |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for family in ("unuseful", "union"):
        for view in VIEW_FIELDS:
            metric = result["secondary_metrics"][family][view]
            lines.append(
                f"| {family} | {view} | {metric_text(metric['average_precision'])} | "
                f"{metric_text(metric['recall_at_30_work'])} | "
                f"{metric_text(metric['work_at_50_recall'])} | {metric['total_positive']} |"
            )

    lines.extend(
        [
            "",
            "## Framework Breakdown",
            "",
            "| Framework | Method | Targets | AP | Recall @ 30% | Work @ 50% |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for framework, methods in sorted(result["framework_metrics"].items()):
        for view in VIEW_FIELDS:
            metric = methods[view]
            lines.append(
                f"| {markdown_escape(framework)} | {view} | {result['framework_targets'][framework]} | "
                f"{metric_text(metric['average_precision'])} | "
                f"{metric_text(metric['recall_at_30_work'])} | "
                f"{metric_text(metric['work_at_50_recall'])} |"
            )

    lines.extend(
        [
            "",
            "## Controls",
            "",
            "| Control | AP | Recall @ 30% | Work @ 50% |",
            "|---|---:|---:|---:|",
        ]
    )
    for name, metric in result["control_metrics"].items():
        lines.append(
            f"| {name} | {metric_text(metric['average_precision'])} | "
            f"{metric_text(metric['recall_at_30_work'])} | "
            f"{metric_text(metric['work_at_50_recall'])} |"
        )
    partition_aps = [
        float(item["metrics"]["average_precision"])
        for item in result["partition_metrics"]
    ]
    semantic_ap = float(result["primary_metrics"]["semantic"]["average_precision"])
    lines.extend(
        [
            "",
            "Flat and per-session one-block controls are merged because neither defines "
            "an outcome-informed recurrent ordering. Framework-native operation identity is "
            "the public step unit already consumed by the raw-action baseline. The official "
            "CodeTracer tree remains a navigation reference, while its target-blind phase "
            "classifier is the matched scored baseline above.",
            "",
            "### Frequency-Matched Non-Semantic Partitions",
            "",
            f"Evaluated partitions: {len(partition_aps)}. AP median "
            f"{percentile(partition_aps, 0.5):.6f}, 2.5--97.5% range "
            f"[{percentile(partition_aps, 0.025):.6f}, {percentile(partition_aps, 0.975):.6f}]. "
            f"Semantic-minus-best-partition AP: {semantic_ap - max(partition_aps):.6f}; "
            f"semantic-minus-median AP: {semantic_ap - percentile(partition_aps, 0.5):.6f}.",
            "",
            "## Outcome Null",
            "",
            "| Method | Trials | Null mean AP | Null 2.5% | Null 97.5% | One-sided empirical p (null AP >= observed) |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for view in VIEW_FIELDS:
        trials = result["null_results"][view]
        summary = summarize_repeated_metric(trials, "average_precision")
        observed = float(result["primary_metrics"][view]["average_precision"])
        exceed = sum(float(item["average_precision"]) >= observed for item in trials)
        p_value = (exceed + 1) / (len(trials) + 1)
        lines.append(
            f"| {view} | {len(trials)} | {summary['mean']:.6f} | "
            f"{summary['p025']:.6f} | {summary['p975']:.6f} | {p_value:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Task-Clustered Bootstrap",
            "",
            f"Valid replicates: {len(result['bootstrap_results']['semantic'])}; "
            f"sampling attempts: {result['bootstrap_attempts']}.",
            "",
            "| Method | Metric | Bootstrap mean | 95% percentile interval |",
            "|---|---|---:|---:|",
        ]
    )
    for view in VIEW_FIELDS:
        for metric_name in ("average_precision", "recall_at_30_work", "work_at_50_recall"):
            summary = summarize_repeated_metric(result["bootstrap_results"][view], metric_name)
            lines.append(
                f"| {view} | {metric_name} | {summary['mean']:.6f} | "
                f"[{summary['p025']:.6f}, {summary['p975']:.6f}] |"
            )
    lines.extend(
        [
            "",
            "| Paired AP difference | Mean | 95% percentile interval |",
            "|---|---:|---:|",
        ]
    )
    for baseline in ("raw-action", "phase"):
        differences = [
            float(semantic["average_precision"]) - float(other["average_precision"])
            for semantic, other in zip(
                result["bootstrap_results"]["semantic"],
                result["bootstrap_results"][baseline],
                strict=True,
            )
        ]
        lines.append(
            f"| semantic - {baseline} | {sum(differences) / len(differences):.6f} | "
            f"[{percentile(differences, 0.025):.6f}, {percentile(differences, 0.975):.6f}] |"
        )

    lines.extend(
        [
            "",
            "## Completion Audit",
            "",
            f"- Frequency candidates/retained: {result['partition_candidates']}/"
            f"{len(result['partition_metrics'])} (required 10,000/200).",
            f"- Outcome-null trials: {len(result['null_results']['semantic'])} (required 2,000).",
            f"- Task-bootstrap replicates: {len(result['bootstrap_results']['semantic'])} "
            "(required 10,000).",
            f"- Source coverage: {result['full_rows']}/{result['full_rows']} terminal rows.",
            "",
            "The report is PASS only when the approved full counts and every component above "
            "complete. Git state does not affect this status.",
            "",
            "## Result-Review Handoff",
            "",
            "This report records the completed tested-hypothesis result. It does not answer the "
            "entire RQ, rewrite the hypothesis, or authorize a paper-story change. The next node "
            "is independent scientific result review.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run_end_to_end(args: argparse.Namespace, mode: str) -> None:
    full_rows = load_manifest(args.full_manifest)
    verified_rows = load_manifest(args.verified_manifest)
    full_by_id = {row.traj_id: row for row in full_rows}
    if len(full_by_id) != len(full_rows):
        raise SourceError("full manifest contains duplicate trajectory IDs")
    if not {row.traj_id for row in verified_rows}.issubset(full_by_id):
        raise SourceError("verified manifest is not a subset of full manifest")

    if mode == "real-preflight":
        selections = select_preflight_rows(verified_rows, args.raw_root)
        target_candidates = [selection.row for selection in selections]
    else:
        target_candidates = [
            row
            for row in verified_rows
            if row.solved is False and artifact_path(args.raw_root, row) is not None
        ]

    broad_cells = {(row.agent, row.model) for row in target_candidates}
    reference_candidates = [
        row
        for row in full_rows
        if row.solved is not None
        and (row.agent, row.model) in broad_cells
        and artifact_path(args.raw_root, row) is not None
    ]

    run_out = args.out / mode
    run_out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="codetracebench-rq2-classifier-") as tmp:
        classifier = load_classifier(
            args.codetracer_root, Path(tmp) / "classifications.jsonl"
        )
        reference_profiles, reference_failures = extract_profile_population(
            reference_candidates, args.raw_root, classifier
        )
        target_profiles, target_failures = extract_profile_population(
            target_candidates, args.raw_root, classifier
        )

    if mode == "real-preflight" and len(target_profiles) != len(target_candidates):
        raise SourceError(
            f"real preflight lost targets: {len(target_profiles)}/{len(target_candidates)} source-valid"
        )

    reference_operations = run_out / "reference-operations.jsonl"
    target_operations = run_out / "target-operations.jsonl"
    write_combined_operation_jsonl(
        reference_operations,
        ((row, steps) for row, steps, _ in reference_profiles.values()),
    )
    write_combined_operation_jsonl(
        target_operations,
        ((row, steps) for row, steps, _ in target_profiles.values()),
    )
    verify_agentprof_views(
        args.agentpprof_bin,
        reference_operations,
        run_out / "agentprof-reference",
        include_trajectory=True,
    )
    verify_agentprof_views(
        args.agentpprof_bin,
        target_operations,
        run_out / "agentprof-target",
        include_trajectory=True,
    )

    reference_index = build_reference_index(reference_profiles)
    scored, support_counts = score_targets(target_profiles, reference_index)
    prediction_path = run_out / "predictions-pre-label.md"
    write_prediction_markdown(prediction_path, scored)

    gold = terminal_load_incorrect_labels(args.verified_manifest, set(scored))
    metrics = {
        view: pooled_tie_block_metrics(scored, gold, view) for view in VIEW_FIELDS
    }
    report = run_out / "report.md"
    write_end_to_end_report(
        report,
        mode,
        full_rows,
        verified_rows,
        target_candidates,
        target_profiles,
        target_failures,
        reference_candidates,
        reference_profiles,
        reference_failures,
        support_counts,
        metrics,
        prediction_path,
    )
    print(report)


def run_real_preflight(args: argparse.Namespace) -> None:
    run_end_to_end(args, "real-preflight")


def run_full(args: argparse.Namespace) -> None:
    started = time.perf_counter()
    full_rows = load_manifest(args.full_manifest)
    verified_rows = load_manifest(args.verified_manifest)
    full_by_id = {row.traj_id: row for row in full_rows}
    if len(full_by_id) != len(full_rows):
        raise SourceError("full manifest contains duplicate trajectory IDs")
    if not {row.traj_id for row in verified_rows}.issubset(full_by_id):
        raise SourceError("verified manifest is not a subset of full manifest")

    run_out = args.out / "full"
    run_out.mkdir(parents=True, exist_ok=True)
    print(f"full-source extraction start: {len(full_rows)} manifest rows", flush=True)
    with tempfile.TemporaryDirectory(prefix="codetracebench-rq2-classifier-") as tmp:
        classifier = load_classifier(
            args.codetracer_root, Path(tmp) / "classifications.jsonl"
        )
        all_profiles, all_failures = extract_profile_population(
            full_rows, args.raw_root, classifier
        )
    print(
        f"full-source extraction complete: {len(all_profiles)} valid; "
        f"{len(all_failures)} excluded",
        flush=True,
    )

    coverage_path = run_out / "full-source-coverage.md"
    write_full_source_coverage(coverage_path, full_rows, all_profiles, all_failures)
    verified_by_id = {row.traj_id: row for row in verified_rows}
    target_profiles: dict[str, tuple[ManifestRow, list[ProfiledStep], str]] = {}
    for traj_id, verified_row in verified_by_id.items():
        if verified_row.solved is not False or traj_id not in all_profiles:
            continue
        _, steps, adapter = all_profiles[traj_id]
        target_profiles[traj_id] = verified_row, steps, adapter
    reference_profiles = {
        traj_id: profile
        for traj_id, profile in all_profiles.items()
        if profile[0].solved is not None
    }
    if not target_profiles:
        raise SourceError("full run has no source-valid failed verified targets")

    reference_operations = run_out / "reference-operations.jsonl"
    target_operations = run_out / "target-operations.jsonl"
    write_combined_operation_jsonl(
        reference_operations,
        ((row, steps) for row, steps, _ in reference_profiles.values()),
    )
    write_combined_operation_jsonl(
        target_operations,
        ((row, steps) for row, steps, _ in target_profiles.values()),
    )
    verify_agentprof_views(
        args.agentpprof_bin,
        reference_operations,
        run_out / "agentprof-reference",
        include_trajectory=True,
    )
    verify_agentprof_views(
        args.agentpprof_bin,
        target_operations,
        run_out / "agentprof-target",
        include_trajectory=True,
    )
    print("release-AgentProf exact-count checks complete", flush=True)

    group_cache = build_group_cache(reference_profiles)
    reference_index = build_reference_index(
        reference_profiles, group_cache=group_cache
    )
    primary_scored, support_counts = score_targets(target_profiles, reference_index)
    prediction_path = run_out / "predictions-pre-label.md"
    write_prediction_markdown(prediction_path, primary_scored)

    bucket_count, partitions = select_frequency_matched_partitions(
        all_profiles,
        first_seed=args.seed,
        candidate_count=args.partition_candidates,
        retain_count=args.partition_retained,
    )
    partition_path = run_out / "frequency-partitions-pre-label.md"
    write_partition_selection(
        partition_path,
        bucket_count=bucket_count,
        candidate_count=args.partition_candidates,
        partitions=partitions,
        first_seed=args.seed,
    )
    print(
        f"pre-label outputs complete: {len(primary_scored)} targets; "
        f"{len(partitions)} frequency partitions",
        flush=True,
    )

    absolute_controls: dict[str, dict[str, dict[str, Any]]] = {}
    for view in VIEW_FIELDS:
        name = f"absolute-{view}"
        group_fn = lambda step, current=view: group_for_step(step, current)
        absolute_index = build_absolute_reference_index(all_profiles, group_fn)
        absolute_controls[name] = score_absolute_view(
            target_profiles, absolute_index, group_fn, name
        )
    flat_scored = make_flat_control(target_profiles)

    label_families = terminal_load_label_families(
        args.verified_manifest, set(primary_scored)
    )
    incorrect_gold = label_families["incorrect"]
    primary_metrics = {
        view: pooled_tie_block_metrics(primary_scored, incorrect_gold, view)
        for view in VIEW_FIELDS
    }
    compatibility = {
        view: compatibility_metrics(primary_scored, incorrect_gold, view)
        for view in VIEW_FIELDS
    }
    secondary_metrics = {
        family: {
            view: pooled_tie_block_metrics(primary_scored, labels, view)
            for view in VIEW_FIELDS
        }
        for family, labels in label_families.items()
        if family != "incorrect"
    }
    frameworks = sorted({record["row"].agent for record in primary_scored.values()})
    framework_metrics: dict[str, dict[str, dict[str, float | int | None]]] = {}
    framework_targets: dict[str, int] = {}
    for framework in frameworks:
        subset = subset_scored(primary_scored, framework)
        framework_targets[framework] = len(subset)
        framework_metrics[framework] = {
            view: pooled_tie_block_metrics(subset, incorrect_gold, view)
            for view in VIEW_FIELDS
        }

    control_metrics: dict[str, dict[str, float | int | None]] = {
        "flat/session-one-block": pooled_tie_block_metrics(
            flat_scored, incorrect_gold, "flat"
        )
    }
    for name, scored in absolute_controls.items():
        control_metrics[name] = pooled_tie_block_metrics(
            scored, incorrect_gold, name
        )

    partition_metrics: list[dict[str, Any]] = []
    for index, (partition_seed, distance) in enumerate(partitions, 1):
        group_fn = lambda step, current=partition_seed: partition_bucket(
            step.raw_action_key, current, bucket_count
        )
        custom_index = build_custom_reference_index(reference_profiles, group_fn)
        view_name = f"partition-{partition_seed}"
        scored = score_custom_view(
            target_profiles,
            primary_scored,
            custom_index,
            group_fn,
            view_name,
        )
        partition_metrics.append(
            {
                "seed": partition_seed,
                "distance": distance,
                "metrics": pooled_tie_block_metrics(
                    scored, incorrect_gold, view_name
                ),
            }
        )
        if index % 25 == 0 or index == len(partitions):
            print(f"frequency-control {index}/{len(partitions)}", flush=True)

    null_results = run_outcome_null_trials(
        reference_profiles,
        target_profiles,
        incorrect_gold,
        repetitions=args.permutations,
        seed=args.seed,
        group_cache=group_cache,
    )
    bootstrap_results, bootstrap_attempts = run_task_cluster_bootstrap(
        reference_profiles,
        target_profiles,
        incorrect_gold,
        repetitions=args.bootstraps,
        seed=args.seed,
        group_cache=group_cache,
    )

    complete = (
        len(full_rows) == 3316
        and len(target_profiles) == 405
        and args.partition_candidates >= 10000
        and len(partition_metrics) >= 200
        and len(null_results["semantic"]) >= 2000
        and len(bootstrap_results["semantic"]) >= 10000
        and set(support_counts) <= {name for name, _ in SUPPORT_LEVELS}
    )
    result = {
        "status": "PASS" if complete else "INCOMPLETE",
        "full_rows": len(full_rows),
        "source_valid_full": len(all_profiles),
        "source_excluded_full": len(all_failures),
        "target_count": len(target_profiles),
        "target_steps": sum(len(steps) for _, steps, _ in target_profiles.values()),
        "reference_count": len(reference_profiles),
        "runtime_seconds": time.perf_counter() - started,
        "coverage_path": coverage_path,
        "prediction_path": prediction_path,
        "partition_path": partition_path,
        "primary_metrics": primary_metrics,
        "compatibility": compatibility,
        "secondary_metrics": secondary_metrics,
        "framework_metrics": framework_metrics,
        "framework_targets": framework_targets,
        "control_metrics": control_metrics,
        "partition_metrics": partition_metrics,
        "partition_candidates": args.partition_candidates,
        "null_results": null_results,
        "bootstrap_results": bootstrap_results,
        "bootstrap_attempts": bootstrap_attempts,
    }
    report = run_out / "report.md"
    write_full_experiment_report(report, result)
    print(report, flush=True)


def select_preflight_rows(
    rows: list[ManifestRow], raw_root: Path
) -> list[PreflightSelection]:
    selected: list[PreflightSelection] = []
    for variant, framework, predicate in PREFLIGHT_VARIANTS:
        candidates = sorted(
            (
                row
                for row in rows
                if row.agent == framework
                and row.solved is False
                and predicate(row)
                and artifact_path(raw_root, row) is not None
            ),
            key=lambda row: row.traj_id,
        )
        if not candidates:
            raise SourceError(
                f"no downloaded raw-available failed preflight row for {variant} ({framework})"
            )
        # Pick the first source-valid row, not merely the first archive.  The
        # released manifest contains a small number of raw/normalization
        # mismatches; source validity is determined only from raw structure and
        # the public step_count, never from incorrect-step annotations.
        chosen = None
        for candidate in candidates:
            archive = artifact_path(raw_root, candidate)
            assert archive is not None
            try:
                members = tar_members(archive)
                raw_steps, _ = ADAPTERS[candidate.agent](
                    archive, members, candidate.step_count
                )
            except (SourceError, subprocess.CalledProcessError):
                continue
            if len(raw_steps) == candidate.step_count:
                chosen = candidate
                break
        if chosen is None:
            raise SourceError(
                f"no source-valid failed preflight row for {variant} ({framework})"
            )
        selected.append(PreflightSelection(variant, chosen))
    return selected


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def source_variant(row: ManifestRow) -> str:
    return "swe_raw" if (row.source_relpath or "").startswith("swe_raw/") else "native"


def run_source_audit(args: argparse.Namespace) -> None:
    """Audit every verified raw archive without projecting step labels."""
    rows = load_manifest(args.verified_manifest)
    args.out.mkdir(parents=True, exist_ok=True)
    coverage: Counter[tuple[str, str, str, str]] = Counter()
    invalid: list[dict[str, Any]] = []
    openhands_swe = Counter()

    for row in rows:
        variant = source_variant(row)
        archive = artifact_path(args.raw_root, row)
        if archive is None:
            coverage[(row.agent, variant, "missing", "-")] += 1
            invalid.append(
                {
                    "row": row,
                    "variant": variant,
                    "status": "missing archive",
                    "observed": None,
                    "adapter": "-",
                    "detail": "artifact_path absent or archive unavailable",
                }
            )
            continue

        try:
            members = tar_members(archive)
            raw_steps, adapter = ADAPTERS[row.agent](
                archive, members, row.step_count
            )
            consecutive = [step.step_id for step in raw_steps] == list(
                range(1, len(raw_steps) + 1)
            )
            status = (
                "exact"
                if len(raw_steps) == row.step_count and consecutive
                else "mismatch"
            )
            coverage[(row.agent, variant, status, adapter)] += 1
            if status != "exact":
                invalid.append(
                    {
                        "row": row,
                        "variant": variant,
                        "status": "step mismatch",
                        "observed": len(raw_steps),
                        "adapter": adapter,
                        "detail": (
                            "non-consecutive IDs"
                            if not consecutive
                            else "source operation count differs from public step_count"
                        ),
                    }
                )

            if row.agent == "OpenHands" and variant == "swe_raw":
                records = load_openhands_call_records(archive, members)
                ordered = sorted(records, key=lambda item: (item[1], item[2]))
                visible = [item[0] for item in ordered]
                maximum = max(visible, default=0)
                openhands_swe["rows"] += 1
                openhands_swe["exact"] += int(status == "exact")
                openhands_swe["context_decrease_rows"] += int(
                    any(later < earlier for earlier, later in zip(visible, visible[1:]))
                )
                openhands_swe["maximum_tie_rows"] += int(
                    sum(count == maximum for count in visible) > 1
                )
                openhands_swe["request_records"] += len(records)
        except (SourceError, subprocess.CalledProcessError) as error:
            coverage[(row.agent, variant, "error", "-")] += 1
            invalid.append(
                {
                    "row": row,
                    "variant": variant,
                    "status": "adapter error",
                    "observed": None,
                    "adapter": "-",
                    "detail": str(error),
                }
            )

    cells: dict[tuple[str, str], Counter[str]] = {}
    adapters: dict[tuple[str, str], set[str]] = {}
    for (agent, variant, status, adapter), count in coverage.items():
        cells.setdefault((agent, variant), Counter())[status] += count
        if adapter != "-":
            adapters.setdefault((agent, variant), set()).add(adapter)

    exact_total = sum(counts["exact"] for counts in cells.values())
    raw_total = sum(
        counts["exact"] + counts["mismatch"] + counts["error"]
        for counts in cells.values()
    )
    lines = [
        "# CodeTraceBench Verified-Source Alignment Audit",
        "",
        "**Status:** PARTIAL PASS — the complete verified population was inspected; "
        f"{exact_total}/{raw_total} available raw archives align exactly, and "
        f"{len(invalid)} rows are excluded from label-aligned scoring rather than count-fitted.",
        "",
        "## Information Boundary",
        "",
        "The audit loads only the runner's safe manifest projection: trajectory identity, "
        "framework/model/task/cohort fields, outcome, public step count, and raw-artifact paths. "
        "It does not project or read stages, incorrect/unuseful step IDs, labels, annotation paths, "
        "or annotation reasoning. Adapter rules are source-structural. The public step count is "
        "used only as an assertion; the runner never truncates, pads, synthesizes, or selects a "
        "branch to make a count match.",
        "",
        "## Complete Verified-Population Result",
        "",
        "| Framework | Source layout | Verified rows | Raw available | Exact | Mismatch | Error | Missing | Adapter |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for cell in sorted(cells):
        counts = cells[cell]
        total = sum(counts.values())
        raw_available = total - counts["missing"]
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_escape(cell[0]),
                    cell[1],
                    str(total),
                    str(raw_available),
                    str(counts["exact"]),
                    str(counts["mismatch"]),
                    str(counts["error"]),
                    str(counts["missing"]),
                    markdown_escape(", ".join(sorted(adapters.get(cell, set()))) or "-"),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## OpenHands SWE-Raw Lineage Audit",
            "",
            f"All {openhands_swe['rows']} verified OpenHands SWE-raw archives were inspected. "
            f"The maximum-visible-assistant-tool-history rule aligns exactly for "
            f"{openhands_swe['exact']}/{openhands_swe['rows']} rows. "
            f"{openhands_swe['context_decrease_rows']} rows contain at least one chronological "
            "context decrease (restart or compaction), and "
            f"{openhands_swe['maximum_tie_rows']} rows have more than one request at the maximum "
            f"visible-tool count, across {openhands_swe['request_records']} request records. "
            "Selection maximizes assistant tool-call history and breaks ties by timestamp/path; "
            "it never uses the manifest step count or response content.",
            "",
            "This establishes a complete source-only structural result for the released SWE-raw "
            "OpenHands population. It does not by itself prove the eventual differential scorer or "
            "label join.",
            "",
            "## Invalid Or Unresolved Rows",
            "",
            "Rows below remain visible as source-quality exclusions. They are not silently repaired "
            "and cannot enter label-aligned target metrics until a published or independently "
            "source-grounded normalization rule resolves them.",
            "",
            "| Trajectory | Framework/layout | Expected | Observed | Status | Adapter | Detail |",
            "|---|---|---:|---:|---|---|---|",
        ]
    )
    for item in invalid:
        row = item["row"]
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{markdown_escape(row.traj_id)}`",
                    markdown_escape(f"{row.agent}/{item['variant']}"),
                    str(row.step_count),
                    "-" if item["observed"] is None else str(item["observed"]),
                    item["status"],
                    markdown_escape(item["adapter"]),
                    markdown_escape(item["detail"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Use only exact, source-valid failed verified trajectories for step-localization "
            "metrics. Keep auditing every full-manifest archive for reference-profile coverage. "
            "This is an experiment-plan repair caused by released source/normalization drift; it "
            "does not change RQ2, the tested hypothesis, the thesis, or the paper story.",
            "",
        ]
    )
    report = args.out / "verified-source-alignment-audit.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    print(report)


def run_preflight(args: argparse.Namespace) -> None:
    rows = load_manifest(args.verified_manifest)
    selected = select_preflight_rows(rows, args.raw_root)
    args.out.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="codetracebench-rq2-classifier-") as tmp:
        classifier = load_classifier(args.codetracer_root, Path(tmp) / "classifications.jsonl")
        for selection in selected:
            row = selection.row
            archive = artifact_path(args.raw_root, row)
            if archive is None:
                raise SourceError(f"selected archive disappeared: {row.traj_id}")
            members = tar_members(archive)
            raw_steps, adapter = ADAPTERS[row.agent](archive, members, row.step_count)
            if len(raw_steps) != row.step_count:
                raise SourceError(
                    f"{row.traj_id}: {adapter} emitted {len(raw_steps)} steps, "
                    f"manifest declares {row.step_count}"
                )
            if [step.step_id for step in raw_steps] != list(range(1, row.step_count + 1)):
                raise SourceError(f"{row.traj_id}: adapter did not emit consecutive one-based IDs")

            steps = profile_steps(raw_steps, classifier)
            row_dir = args.out / "preflight" / row.traj_id
            operation_file = row_dir / "operations.jsonl"
            write_operation_jsonl(operation_file, row, steps)
            views = {
                "semantic": ("phase", "action_kind"),
                "raw-action": ("raw_action_key",),
                "phase": ("phase",),
            }
            for view, fields in views.items():
                observed = invoke_agentpprof(
                    args.agentpprof_bin,
                    operation_file,
                    row_dir / f"{view}.json",
                    fields,
                )
                expected = expected_counter(steps, fields)
                if observed != expected:
                    raise SourceError(
                        f"{row.traj_id}: AgentProf {view} counts differ; "
                        f"expected={expected}, observed={observed}"
                    )

            kind_counts = Counter(step.action_kind for step in steps)
            stack_counts = Counter((step.phase, step.action_kind) for step in steps)
            records.append(
                {
                    "row": row,
                    "variant": selection.variant,
                    "archive": archive,
                    "adapter": adapter,
                    "kind_counts": kind_counts,
                    "stack_count": len(stack_counts),
                }
            )

    report = args.out / "preflight-report.md"
    lines = [
        "# CodeTraceBench RQ2 Real Preflight",
        "",
        "**Source-only check:** PARTIAL PASS — six selected official source variants across four frameworks align exactly and AgentProf counts match.",
        "**REAL PREFLIGHT:** INCOMPLETE — this command does not yet exercise task-held-out reference construction, differential scoring, prediction writing, terminal label join, or the declared RQ2 metrics.",
        "",
        "## Information Boundary",
        "",
        "Selection used only framework, manifest outcome, archive availability, and trajectory ID order. "
        "The runner projected no `incorrect_stages`, stage, label, reason, or annotation path column. "
        "Every operation and stack was fixed before any hidden step label is eligible to load.",
        "",
        "## Four-Framework, Six-Variant Result",
        "",
        "| Framework / source variant | Trajectory | Source adapter | Steps | Action kinds | Semantic stacks | AgentProf |",
        "|---|---|---|---:|---|---:|---|",
    ]
    for record in records:
        row = record["row"]
        kind_text = ", ".join(
            f"{kind}={count}" for kind, count in sorted(record["kind_counts"].items())
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_escape(f"{row.agent} / {record['variant']}"),
                    f"`{markdown_escape(row.traj_id)}`",
                    f"`{record['adapter']}`",
                    str(row.step_count),
                    markdown_escape(kind_text),
                    str(record["stack_count"]),
                    "semantic/raw/phase exact",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "This dependency check passes only the selected source-adapter and profiler-engagement boundary. "
            "It is not the approved REAL PREFLIGHT, is not evidence for RQ2, and is not a smoke-test "
            "substitute for the declared full run. The next step is to implement and review one shared "
            "end-to-end preflight/full scoring path before running all 3,291 published raw archives.",
            "",
        ]
    )
    report.write_text("\n".join(lines), encoding="utf-8")
    print(report)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight = subparsers.add_parser(
        "preflight", help="run the six-source-variant source-only dependency check"
    )
    preflight.add_argument("--verified-manifest", type=Path, required=True)
    preflight.add_argument("--raw-root", type=Path, required=True)
    preflight.add_argument("--codetracer-root", type=Path, required=True)
    preflight.add_argument("--agentpprof-bin", type=Path, required=True)
    preflight.add_argument("--out", type=Path, required=True)
    preflight.set_defaults(func=run_preflight)
    audit = subparsers.add_parser(
        "source-audit", help="audit every verified raw archive without loading step labels"
    )
    audit.add_argument("--verified-manifest", type=Path, required=True)
    audit.add_argument("--raw-root", type=Path, required=True)
    audit.add_argument("--out", type=Path, required=True)
    audit.set_defaults(func=run_source_audit)
    for command, help_text, func in (
        (
            "real-preflight",
            "run the shared end-to-end path on six source-valid real targets",
            run_real_preflight,
        ),
        (
            "full",
            "run the shared deterministic primary path on all source-valid failed targets",
            run_full,
        ),
    ):
        evaluation = subparsers.add_parser(command, help=help_text)
        evaluation.add_argument("--full-manifest", type=Path, required=True)
        evaluation.add_argument("--verified-manifest", type=Path, required=True)
        evaluation.add_argument("--raw-root", type=Path, required=True)
        evaluation.add_argument("--codetracer-root", type=Path, required=True)
        evaluation.add_argument("--agentpprof-bin", type=Path, required=True)
        evaluation.add_argument("--out", type=Path, required=True)
        evaluation.set_defaults(func=func)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        args.func(args)
    except (SourceError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"preflight failed: {error}") from error


if __name__ == "__main__":
    main()
