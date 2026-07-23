#!/usr/bin/env python3
"""Build source-only semantic-operation marks for TraceElephant packets.

The classifier deliberately consumes only the annotation packet contract:
task text, source summaries, source-native paths, and operation identifiers.  It
normalizes many concrete native events into a small number of task-progress
operations, while preserving returns to the same work as repeated spans.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import glob
import json
from pathlib import Path
import re
from typing import Any, Iterable


FORBIDDEN_OPERATION_KEYS = {
    "label",
    "labels",
    "localizer_hit",
    "mistake",
    "risk",
    "score",
    "target",
    "judge",
    "group",
}


def lower(value: Any) -> str:
    return str(value or "").lower()


def native(operation: dict[str, Any], index: int) -> str:
    path = operation.get("native_path") or []
    return lower(path[index]) if index < len(path) else ""


def source(operation: dict[str, Any]) -> dict[str, Any]:
    value = operation.get("source_summary")
    return value if isinstance(value, dict) else {}


def parse_tool_calls(operation: dict[str, Any]) -> list[dict[str, Any]]:
    def decode(raw: Any) -> list[dict[str, Any]]:
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, dict)]
        if not isinstance(raw, str) or not raw.strip():
            return []
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return []
        return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []

    summary = source(operation)
    calls = decode(summary.get("tool_calls"))
    return calls if calls else decode(summary.get("tool_logs"))


def tool_details(operation: dict[str, Any]) -> str:
    parts = [native(operation, 4)]
    for call in parse_tool_calls(operation):
        function = call.get("function") or {}
        if not isinstance(function, dict):
            continue
        parts.extend([lower(function.get("name")), lower(function.get("arguments"))])
    return " ".join(parts)


def extract_path(operation: dict[str, Any]) -> str:
    for call in parse_tool_calls(operation):
        function = call.get("function") or {}
        arguments = function.get("arguments") if isinstance(function, dict) else None
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                match = re.search(r'"path"\s*:\s*"([^\"]+)"', arguments)
                if match:
                    return lower(match.group(1))
        if isinstance(arguments, dict) and arguments.get("path"):
            return lower(arguments["path"])
    observed = str(source(operation).get("last_input") or "").replace("\\/", "/")
    candidates = [candidate.rstrip(".,:;)'\"]}") for candidate in re.findall(r"/testbed/[A-Za-z0-9_./-]+", observed)]
    for distinctive in ("reproduce_error.py", "/settings.py", "/app/"):
        for candidate in candidates:
            if distinctive in candidate:
                return lower(candidate)
    if candidates:
        return lower(candidates[0])
    return ""


def extract_command(operation: dict[str, Any]) -> str:
    for call in parse_tool_calls(operation):
        function = call.get("function") or {}
        arguments = function.get("arguments") if isinstance(function, dict) else None
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                match = re.search(r'"command"\s*:\s*"([^\"]+)"', arguments)
                if match:
                    return lower(match.group(1))
        if isinstance(arguments, dict) and arguments.get("command"):
            return lower(arguments["command"])
    return ""


def has_any(text: str, terms: Iterable[str]) -> bool:
    return any(term in text for term in terms)


def web_goal(task: str) -> str:
    text = lower(task)
    if has_any(text, ("attached image", "attached file", "local file", ".png", ".jpg", ".pdf", ".csv", ".xlsx", ".mp3", ".wav")):
        return "Answer from provided artifact"
    if has_any(text, ("route", "metro station", "in what order", "sequence", "directly after", "directly before")):
        return "Reconstruct requested sequence"
    if has_any(text, ("percentage", "probability", "how likely", "how much", "calculate", "convert", "total score", "difference between")):
        return "Compute requested result"
    if has_any(text, ("smallest", "largest", "most recent", "which member", "which gyms", "compare", "list all")):
        return "Compare candidate evidence"
    return "Locate requested fact"


def is_test_path(path: str) -> bool:
    relative = path.removeprefix("/testbed/")
    name = Path(relative).name
    return (
        relative.startswith("tests/")
        or "/tests/" in f"/{relative}"
        or name.startswith("test_")
        or name.endswith("_test.py")
        or name == "tests.py"
    )


def swe_path(phase: str, leaf: str | None = None) -> list[str]:
    path = ["Repair software regression"]
    if leaf is None:
        path.append(phase)
    else:
        path.extend([phase, leaf])
    return path


def classify_swe(operation: dict[str, Any]) -> list[str]:
    phase = native(operation, 1)
    action = native(operation, 2)
    tool = tool_details(operation)
    path = extract_path(operation)
    command = extract_command(operation)
    status = native(operation, 5)

    if "submit" in tool or native(operation, 3) == "submit":
        return swe_path("Submit repair")
    if native(operation, 4) == "response:stop" and phase == "response":
        return swe_path("Report repair outcome")

    if "undo_edit" in tool:
        return swe_path("Change implementation", "Undo failed change")

    if "str_replace_editor:view" in tool or ("view" in tool and not command):
        if "reproduce" in path or path.endswith("settings.py"):
            return swe_path("Reproduce issue", "Inspect reproducer")
        if is_test_path(path):
            return swe_path("Understand issue", "Inspect regression tests")
        suffix = Path(path).suffix if path else ""
        if not suffix or path.rstrip("/") == "/testbed":
            return swe_path("Understand issue", "Explore repository")
        return swe_path("Understand issue", "Inspect implementation")

    if "str_replace_editor:create" in tool:
        if "reproduce" in path:
            return swe_path("Reproduce issue", "Create reproducer")
        if is_test_path(path):
            return swe_path("Change implementation", "Add regression test")
        if path.endswith("settings.py") or "/app/" in path:
            return swe_path("Reproduce issue", "Repair reproducer harness")
        return swe_path("Change implementation", "Create implementation artifact")

    if has_any(tool, ("str_replace", "str_replace_editor:insert")):
        if "reproduce" in path or path.endswith("settings.py"):
            return swe_path("Reproduce issue", "Repair reproducer harness")
        if is_test_path(path):
            return swe_path("Change implementation", "Add regression test")
        return swe_path("Change implementation", "Implement fix")

    if "bash" in tool or command:
        combined = f"{command} {tool}"
        if has_any(command, ("rm /testbed/reproduce", "rm -f /testbed/reproduce")):
            return swe_path("Clean temporary artifacts")
        if has_any(command, ("git diff", "git status")):
            return swe_path("Verify repair", "Review changes")
        if has_any(command, ("pytest", "runtests", "tox ", "test_", "/tests/", " tests/")):
            return swe_path("Verify repair", "Run regression tests")
        if "reproduce" in command or ("python" in command and ".py" in command):
            return swe_path("Reproduce issue", "Run reproducer")
        if has_any(command, ("grep ", "rg ", "find ", "grep -")):
            return swe_path("Understand issue", "Search codebase")
        if phase == "information" or action == "inspect":
            return swe_path("Understand issue", "Inspect runtime behavior")
        if phase == "verification" or action == "verify":
            leaf = "Assess failed verification" if status == "failure" else "Run targeted verification"
            return swe_path("Verify repair", leaf)
        return swe_path("Change implementation", "Execute repair command")

    if phase == "verification" or action == "verify":
        leaf = "Assess failed verification" if status == "failure" else "Assess verification result"
        return swe_path("Verify repair", leaf)
    if phase == "information":
        return swe_path("Understand issue", "Inspect evidence")
    if phase in {"execution", "artifact"}:
        return swe_path("Change implementation", "Apply repair")
    return swe_path("Continue repair")


def web_path(goal: str, phase: str, leaf: str | None = None) -> list[str]:
    path = ["Solve evidence-backed task", goal]
    if leaf is None:
        path.append(phase)
    else:
        path.extend([phase, leaf])
    return path


def instruction_path(goal: str, response: str) -> list[str] | None:
    """Map an orchestrator instruction onto the work it initiates.

    Magentic-One records the instruction and the following concrete tool call as
    separate native events.  Giving both the same path folds that transport
    detail into one semantic operation instead of creating an artificial
    orchestrator/tool alternation.
    """
    if "instruction_or_question" not in response:
        return None
    if has_any(response, ("web search", "search for", "find online", "look up")):
        return web_path(goal, "Acquire evidence", "Search web")
    if has_any(response, ("download", "csv", "data file", "add to cart", "obtain the data")):
        return web_path(goal, "Acquire evidence", "Acquire source data")
    if has_any(response, ("select", "dropdown", "date range", "enter ", "fill ", "input ")):
        return web_path(goal, "Acquire evidence", "Configure source query")
    if has_any(response, ("open the", "click", "navigate", "follow the link", "visit the")):
        return web_path(goal, "Acquire evidence", "Navigate candidate source")
    if has_any(response, ("inspect", "read the", "scroll", "check the page", "summarize")):
        return web_path(goal, "Acquire evidence", "Read candidate source")
    if has_any(response, ("local file", "attached", "image", "pdf")):
        return web_path(goal, "Acquire evidence", "Inspect provided artifact")
    if has_any(response, ("calculate", "compute", "analyze", "python", "coder")):
        return web_path(goal, "Reason over evidence", "Analyze evidence with code")
    if has_any(response, ("verify", "double-check", "validate", "check the answer")):
        return web_path(goal, "Verify result", "Check candidate answer")
    return None


def classify_web(
    operation: dict[str, Any],
    task: str,
    ordinal: int,
    is_last: bool,
    recovery_seen: bool,
    verification_seen: bool,
) -> list[str]:
    goal = web_goal(task)
    summary = source(operation)
    agent = lower(summary.get("agent_name"))
    input_text = lower(summary.get("last_input"))
    response = lower(summary.get("response"))
    combined = f"{input_text} {response}"
    phase = native(operation, 1)
    action = native(operation, 2)
    tool = tool_details(operation)

    final_cue = has_any(response, ("## answer", "final answer", "terminate"))
    final_position = is_last or phase == "response"
    if final_cue and final_position:
        unsupported = has_any(
            response,
            (
                "without direct evidence",
                "unable to verify",
                "could not verify",
                "couldn't verify",
                "no direct source",
                "could not access",
            ),
        )
        tentative = has_any(response, ("approximately", "probably", "likely", "estimate", "estimated", "educated guess"))
        if unsupported or (tentative and recovery_seen and not verification_seen):
            return web_path(goal, "State unsupported conclusion")
        if tentative:
            return web_path(goal, "State tentative conclusion")
        return web_path(goal, "Deliver final answer")

    if has_any(input_text, ("what went wrong", "root cause of the failure", "new plan so we can try again")):
        return web_path(goal, "Recover stalled work", "Diagnose failed attempt")
    if action == "recover" or phase == "recovery":
        return web_path(goal, "Recover stalled work", "Choose alternate approach")
    if "seek_experts_help" in tool:
        leaf = "Request alternate expertise" if action == "recover" else "Delegate specialist"
        return web_path(goal, "Coordinate investigation", leaf)

    initiated = instruction_path(goal, response)
    if initiated is not None and native(operation, 4) == "response:stop":
        return initiated

    if "web_search" in tool:
        return web_path(goal, "Acquire evidence", "Search web")
    if "open_path" in tool or "filesurfer" in agent:
        if "answer_question" in tool:
            return web_path(goal, "Reason over evidence", "Extract artifact evidence")
        return web_path(goal, "Acquire evidence", "Inspect provided artifact")
    if has_any(tool, ("summarize_page", "answer_question")):
        return web_path(goal, "Reason over evidence", "Extract source evidence")
    if has_any(tool, ("scroll_down", "scroll_up", "find_on_page")):
        return web_path(goal, "Acquire evidence", "Read candidate source")
    if has_any(tool, ("input_text", "hover")):
        return web_path(goal, "Acquire evidence", "Configure source query")
    if has_any(tool, ("visit_url", "click", "history_back")):
        if has_any(input_text, ("download", "csv", "data file", "add to cart")):
            return web_path(goal, "Acquire evidence", "Acquire source data")
        if has_any(input_text, ("select", "dropdown", "date range", "fill", "enter")):
            return web_path(goal, "Acquire evidence", "Configure source query")
        return web_path(goal, "Acquire evidence", "Navigate candidate source")

    if has_any(agent, ("coder", "pythonprogramming", "csvhandling", "computerterminal", "code")):
        if phase == "verification" or action == "verify":
            return web_path(goal, "Verify result", "Verify computed result")
        return web_path(goal, "Reason over evidence", "Analyze evidence with code")
    if has_any(agent, ("verification_expert", "dataverification")) or phase == "verification":
        return web_path(goal, "Verify result", "Check candidate answer")

    if phase == "response" and action == "report":
        if is_last:
            return web_path(goal, "Report unresolved task")
        return web_path(goal, "Reason over evidence", "Present candidate answer")

    if has_any(agent, ("websurfer", "informationextraction", "webserving")):
        if phase == "information" and action == "report":
            return web_path(goal, "Reason over evidence", "Summarize gathered evidence")
        if phase == "information" and action == "inspect":
            return web_path(goal, "Acquire evidence", "Inspect candidate source")
        if phase == "information" and action == "act":
            if has_any(input_text, ("search result", "code output", "execution succeeded")):
                return web_path(goal, "Reason over evidence", "Evaluate retrieved evidence")
            if has_any(response, ("start by", "perform a web search", "first, i will", "i'll start")):
                return web_path(goal, "Acquire evidence", "Plan evidence retrieval")
            return web_path(goal, "Reason over evidence", "Extract evidence")
        if phase == "coordination":
            return web_path(goal, "Coordinate investigation", "Select next lookup")
        if action == "report":
            return web_path(goal, "Reason over evidence", "Summarize gathered evidence")

    if agent in {"orchestrator", "magenticoneorchestrator"}:
        if ordinal == 0 and has_any(input_text, ("pre-survey", "given or verified facts")):
            return web_path(goal, "Frame task")
        if has_any(input_text, ("match roles", "expert pool", "skill set")):
            return web_path(goal, "Coordinate investigation", "Assemble specialist team")
        if "select the next role" in input_text:
            return web_path(goal, "Coordinate investigation", "Select next specialist")
        if phase == "information" and action == "plan":
            return web_path(goal, "Frame task", "Identify facts and unknowns")
        if phase == "artifact":
            return web_path(goal, "Reason over evidence", "Transform provided evidence")
        if phase == "coordination":
            return web_path(goal, "Coordinate investigation", "Delegate next subtask")
        if action == "verify":
            return web_path(goal, "Verify result", "Check answer completeness")

    if phase == "information":
        return web_path(goal, "Acquire evidence", "Inspect available evidence")
    if phase == "verification" or action == "verify":
        return web_path(goal, "Verify result", "Check candidate answer")
    if phase == "coordination":
        return web_path(goal, "Coordinate investigation")
    if phase == "execution":
        return web_path(goal, "Reason over evidence", "Execute analysis step")
    return web_path(goal, "Continue investigation")


def leaf(path: list[str]) -> str:
    return path[-1]


def fold_dispatch_transport(family: str, paths: list[list[str]]) -> list[list[str]]:
    """Attach Captain-Agent's selector event to the work it dispatches.

    Captain-Agent emits role selection as a separate request immediately before
    the selected expert works.  The selector is transport, not a task boundary;
    team assembly and genuine recovery remain explicit operations.
    """
    if not family.startswith("Captain-Agent/"):
        return paths
    folded = [list(path) for path in paths]
    dispatch_leaves = {"Select next specialist", "Delegate next subtask"}
    for ordinal in range(len(folded) - 2, -1, -1):
        if leaf(folded[ordinal]) not in dispatch_leaves:
            continue
        next_path = folded[ordinal + 1]
        if "Coordinate investigation" not in next_path:
            folded[ordinal] = list(next_path)
    return folded


def build_findings(
    operations: list[dict[str, Any]], paths: list[list[str]], spans: Counter[tuple[str, ...]]
) -> list[str]:
    counts = Counter(tuple(path) for path in paths)
    top_path, top_count = counts.most_common(1)[0]
    findings = [
        f"The largest source-visible operation is '{leaf(list(top_path))}' with {top_count} of {len(operations)} operations."
    ]

    repeated = [
        (path, span_count, counts[path])
        for path, span_count in spans.items()
        if span_count >= 2 and counts[path] >= 3
    ]
    if repeated:
        path, span_count, operation_count = max(repeated, key=lambda item: (item[2], item[1]))
        findings.append(
            f"The trace returns to '{leaf(list(path))}' in {span_count} separate spans covering {operation_count} operations, exposing repeated or retried work."
        )

    recovery_count = sum(1 for path in paths if "Recover stalled work" in path)
    if recovery_count:
        findings.append(f"The source-visible trajectory contains {recovery_count} recovery operations after stalled or failed work.")

    final_leaf = leaf(paths[-1])
    if final_leaf == "State unsupported conclusion":
        findings.append("The session ends with an answer despite source-visible uncertainty or failed evidence acquisition and no later verification step.")
    elif final_leaf == "State tentative conclusion":
        findings.append("The session ends with an explicitly tentative answer rather than a fully verified conclusion.")
    elif final_leaf in {"Deliver final answer", "Submit repair", "Report repair outcome"}:
        findings.append(f"The final source-visible operation is '{final_leaf}'.")
    else:
        findings.append(f"The session ends in '{final_leaf}' without a source-visible completion operation.")
    return findings


def annotate_session(session: dict[str, Any]) -> dict[str, Any]:
    operations = session.get("operations") or []
    if not operations:
        raise ValueError(f"session {session.get('sequence')} has no operations")
    family = str(session.get("task_family") or "")
    task = str(session.get("task") or "")
    paths: list[list[str]] = []
    recovery_seen = False
    verification_seen = False
    for ordinal, operation in enumerate(operations):
        illegal = FORBIDDEN_OPERATION_KEYS.intersection(operation)
        if illegal:
            raise ValueError(f"forbidden packet keys {sorted(illegal)} in {operation.get('operation_id')}")
        if family == "SWE-Agent/SWE-Bench":
            path = classify_swe(operation)
        else:
            path = classify_web(
                operation,
                task,
                ordinal,
                ordinal == len(operations) - 1,
                recovery_seen,
                verification_seen,
            )
        if "Recover stalled work" in path:
            recovery_seen = True
        if "Verify result" in path:
            verification_seen = True
        paths.append(path)

    paths = fold_dispatch_transport(family, paths)

    marks: list[dict[str, Any]] = []
    spans: Counter[tuple[str, ...]] = Counter()
    previous: list[str] | None = None
    for operation, path in zip(operations, paths):
        if path != previous:
            marks.append(
                {
                    "start_operation_id": operation["operation_id"],
                    "semantic_path": path,
                }
            )
            spans[tuple(path)] += 1
            previous = path

    return {
        "sequence": session["sequence"],
        "marks": marks,
        "findings": build_findings(operations, paths, spans),
    }


def validate_batch(packet: dict[str, Any], annotation: dict[str, Any]) -> tuple[int, int, Counter[int]]:
    if set(annotation) != {"batch", "sessions"}:
        raise ValueError("annotation top-level keys must be exactly batch and sessions")
    packet_sessions = packet.get("sessions") or []
    if len(packet_sessions) != len(annotation["sessions"]):
        raise ValueError("session count changed")
    operation_total = 0
    mark_total = 0
    depths: Counter[int] = Counter()
    for source_session, result_session in zip(packet_sessions, annotation["sessions"]):
        if set(result_session) != {"sequence", "marks", "findings"}:
            raise ValueError(f"unexpected session keys for {result_session.get('sequence')}")
        if source_session["sequence"] != result_session["sequence"]:
            raise ValueError("session order or identity changed")
        operations = source_session["operations"]
        identifiers = [operation["operation_id"] for operation in operations]
        positions = {identifier: ordinal for ordinal, identifier in enumerate(identifiers)}
        marks = result_session["marks"]
        if not marks or marks[0]["start_operation_id"] != identifiers[0]:
            raise ValueError(f"first mark does not cover {source_session['sequence']}")
        previous_position = -1
        previous_path: list[str] | None = None
        for mark in marks:
            if set(mark) != {"start_operation_id", "semantic_path"}:
                raise ValueError(f"unexpected mark keys in {source_session['sequence']}")
            identifier = mark["start_operation_id"]
            if identifier not in positions or positions[identifier] <= previous_position:
                raise ValueError(f"unknown or unordered mark {identifier}")
            path = mark["semantic_path"]
            if not isinstance(path, list) or not path or not all(isinstance(part, str) and part for part in path):
                raise ValueError(f"empty semantic path at {identifier}")
            if path == previous_path:
                raise ValueError(f"redundant consecutive path at {identifier}")
            previous_position = positions[identifier]
            previous_path = path
            depths[len(path)] += 1
        operation_total += len(operations)
        mark_total += len(marks)
    return len(packet_sessions), operation_total, depths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packets", required=True, help="glob for source-only batch packets")
    parser.add_argument("--output", required=True)
    parser.add_argument("--expected-sessions", type=int)
    parser.add_argument("--expected-operations", type=int)
    args = parser.parse_args()

    packet_paths = [Path(path) for path in sorted(glob.glob(args.packets))]
    if not packet_paths:
        raise SystemExit("no packet files matched")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    total_sessions = 0
    total_operations = 0
    total_marks = 0
    depth_distribution: Counter[int] = Counter()
    emitted: list[str] = []
    for packet_path in packet_paths:
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        annotation = {
            "batch": packet_path.stem,
            "sessions": [annotate_session(session) for session in packet.get("sessions") or []],
        }
        sessions, operations, depths = validate_batch(packet, annotation)
        output_path = output / packet_path.name
        output_path.write_text(json.dumps(annotation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        total_sessions += sessions
        total_operations += operations
        total_marks += sum(len(session["marks"]) for session in annotation["sessions"])
        depth_distribution.update(depths)
        emitted.append(str(output_path))

    if args.expected_sessions is not None and total_sessions != args.expected_sessions:
        raise SystemExit(f"expected {args.expected_sessions} sessions, got {total_sessions}")
    if args.expected_operations is not None and total_operations != args.expected_operations:
        raise SystemExit(f"expected {args.expected_operations} operations, got {total_operations}")
    print(
        json.dumps(
            {
                "packet_count": len(packet_paths),
                "sessions": total_sessions,
                "operations": total_operations,
                "marks": total_marks,
                "depth_distribution": dict(sorted(depth_distribution.items())),
                "outputs": emitted,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
