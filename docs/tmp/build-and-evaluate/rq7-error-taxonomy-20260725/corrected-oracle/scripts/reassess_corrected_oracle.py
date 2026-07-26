#!/usr/bin/env python3
"""Reassess all frozen RQ7 questions with the corrected v4 source oracle.

The frozen v2 artifact is read only.  This script reuses its source manifest,
workspace snapshots, questions, and HEAD method answers, while rebuilding
source-direct edges and answers with the current independent oracle.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import random
import re
import statistics
import subprocess
import types
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[6]
EXPERIMENT = (
    REPO
    / "docs/tmp/build-and-evaluate/"
    "step-0004-20260723T181008-0700/experiment-001"
)
RERUN = (
    REPO
    / "docs/tmp/build-and-evaluate/"
    "rq7-error-taxonomy-20260725/rerun-at-HEAD"
)
OUTPUT = Path(__file__).resolve().parents[1]
PRIVATE = EXPERIMENT / "private"
FROZEN_HOME = PRIVATE / "frozen-home"
V3_REVISION = "69afb4866"
SEED = 20260722
TRACE_FILES = {
    "agentsight": "agentsight.json",
    "ActPlane": "ActPlane.json",
    "bpf-developer-tutorial": "bpf-developer-tutorial.json",
    "eunomia.dev": "eunomia-dev.json",
    "agentskill-observability-paper": "agentskill-observability-paper.json",
    "academic-writing-skills": "academic-writing-skills.json",
}


def load_current_oracle() -> Any:
    path = REPO / "agentvis/research/rq7_source_oracle_check.py"
    spec = importlib.util.spec_from_file_location("rq7_oracle_v4", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load corrected oracle")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_v3_oracle() -> Any:
    completed = subprocess.run(
        [
            "git",
            "show",
            f"{V3_REVISION}:agentvis/research/rq7_source_oracle_check.py",
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr)
    module = types.ModuleType("rq7_oracle_v3")
    exec(compile(completed.stdout, f"{V3_REVISION}:rq7_source_oracle_check.py", "exec"), module.__dict__)
    return module


def load_v2_oracle() -> Any:
    path = OUTPUT / "scripts/rq7_oracle_corrected.py"
    spec = importlib.util.spec_from_file_location("rq7_oracle_v2", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load preserved v2 oracle")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def action_transition_evidence(
    v2: Any,
    v4: Any,
    project: dict[str, Any],
) -> dict[str, Any]:
    transitions: Counter[tuple[str, str]] = Counter()
    samples: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    old_counts: Counter[str] = Counter()
    new_counts: Counter[str] = Counter()
    for source_meta in project["sources"]:
        path = FROZEN_HOME / source_meta["home_relative"]
        native = v4.load_native(path)
        old_events = [
            event
            for event in v2.events_from_source(
                source_meta["vendor"],
                native,
                project["worktree"],
            )
            if event.get("kind") == "tool"
        ]
        new_events = [
            event
            for event in v4.events_from_source(
                source_meta["vendor"],
                native,
                project["worktree"],
            )
            if event.get("kind") == "tool"
            and event.get("ts") is not None
        ]
        old = {
            str(event["id"]): event
            for event in old_events
        }
        new = {
            str(event["id"]): event
            for event in new_events
        }
        old_counts.update(
            str(event["atom"])
            for event in old_events
        )
        new_counts.update(
            str(event["atom"])
            for event in new_events
        )
        for call_id in sorted(set(old) | set(new)):
            old_atom = (
                str(old[call_id]["atom"])
                if call_id in old
                else "<absent>"
            )
            new_atom = (
                str(new[call_id]["atom"])
                if call_id in new
                else "<excluded>"
            )
            if old_atom == new_atom:
                continue
            key = (old_atom, new_atom)
            transitions[key] += 1
            if len(samples[key]) < 5:
                event = new.get(call_id) or old[call_id]
                args = (
                    event.get("args")
                    if isinstance(event.get("args"), dict)
                    else {}
                )
                samples[key].append(
                    {
                        "source_id": source_meta["source_id"],
                        "record_index": event.get("record"),
                        "call_id": call_id,
                        "tool": event.get("name"),
                        "command": v4.command_of(
                            str(event.get("name") or ""),
                            args,
                        )[:300],
                    }
                )
    return {
        "old_atom_counts": dict(old_counts),
        "new_atom_counts": dict(new_counts),
        "transitions": [
            {
                "old_atom": key[0],
                "new_atom": key[1],
                "count": count,
                "samples": samples[key],
            }
            for key, count in sorted(transitions.items())
        ],
    }


def derive_source_project(
    oracle: Any,
    project: dict[str, Any],
) -> dict[str, Any]:
    """Apply the oracle grammar without requiring a version-matched freeze ledger."""
    root = Path(project["worktree"])
    sessions: list[dict[str, Any]] = []
    for source_meta in project["sources"]:
        path = FROZEN_HOME / source_meta["home_relative"]
        if (
            path.stat().st_size != source_meta["bytes"]
            or oracle.digest_file(path) != source_meta["sha256"]
        ):
            raise RuntimeError(f"source hash/size mismatch: {source_meta['source_id']}")
        native = oracle.load_native(path)
        derived_native_identity = oracle.native_identity(
            source_meta["vendor"],
            native,
            path.stem,
        )
        events = [
            event
            for event in oracle.events_from_source(
                source_meta["vendor"],
                native,
                str(root),
            )
            if event.get("ts") is not None
        ]
        if not any(event.get("kind") == "tool" for event in events):
            continue
        first = min(
            event["ts"]
            for event in events
            if event.get("kind") == "tool"
        )
        # The immutable questions use the v2 source-file session model.  As in
        # rerun-at-HEAD, preserve those session IDs/ordinals while applying the
        # corrected parser and path grammar.
        semantic = source_meta["session_id"]
        sessions.append(
            {
                **source_meta,
                "events": events,
                "first": first,
                "semantic_session_id": semantic,
                "derived_native_identity": derived_native_identity,
                "source_stream_id": source_meta["sha256"][:16],
            }
        )
    frozen_order = {
        row["session_id"]: row["session_ordinal"]
        for row in project["sessions"]
    }
    sessions.sort(
        key=lambda row: frozen_order[row["semantic_session_id"]]
    )

    sequences = {
        row["semantic_session_id"]: [
            event["atom"]
            for event in row["events"]
        ]
        for row in sessions
    }
    ordered = []
    for session_ordinal, session in enumerate(sessions):
        for event in session["events"]:
            if event.get("kind") != "tool":
                continue
            ordered.append(
                (
                    event["ts"],
                    session["sha256"],
                    event["record"],
                    event["call"],
                    session_ordinal,
                    session,
                    event,
                )
            )
    ordered.sort(key=lambda row: row[:4])

    identities = oracle.Identities()
    edges: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    call_details: dict[tuple[str, str], dict[str, Any]] = {}
    pending: dict[tuple[str, str], str] = {}
    for event_ordinal, (
        _,
        _,
        _,
        _,
        session_ordinal,
        session,
        event,
    ) in enumerate(ordered):
        call = {
            "project": project["project"],
            "source_id": session["source_id"],
            "source_sha256": session["sha256"],
            "vendor": session["vendor"],
            "native_session_id": session["semantic_session_id"],
            "session_ordinal": session_ordinal,
            "source_stream_id": session["source_stream_id"],
            "source_tool_ordinal": event["tool_ordinal"],
            "record_index": event["record"],
            "call_index": event["call"],
            "call_id": str(event["id"]),
            "status": str(event.get("status") or "observed"),
            "atom": str(event["atom"]),
            "tool": str(event.get("name") or ""),
            "cwd": str(event.get("cwd") or root),
            "command": oracle.command_of(
                str(event.get("name") or ""),
                event.get("args") if isinstance(event.get("args"), dict) else {},
            ),
            "wrapped_patch": bool(
                isinstance(event.get("args"), dict)
                and isinstance(event["args"].get("_wrapped_patch"), str)
            ),
        }
        calls.append(call)
        call_details[(session["source_id"], str(event["id"]))] = call

        normalized_effects = []
        for raw_path, access, old_raw in oracle.event_effects(event):
            normalized = oracle.repo_path(
                raw_path,
                str(event.get("cwd") or root),
                root,
            )
            if normalized is None:
                continue
            previous = (
                oracle.repo_path(
                    old_raw,
                    str(event.get("cwd") or root),
                    root,
                )
                if old_raw
                else None
            )
            normalized_effects.append((normalized, access, previous))
        normalized_effects = list(dict.fromkeys(normalized_effects))
        normalized_effects.sort(
            key=lambda effect: (
                {"rename_from": 0, "rename": 1}.get(effect[1], 2),
                effect[0],
                effect[1],
                effect[2] or "",
            )
        )
        for action_ordinal, (normalized, access, previous) in enumerate(
            normalized_effects
        ):
            pending_key = (
                session["semantic_session_id"],
                str(event["id"]),
            )
            if access == "rename_from":
                pending[pending_key] = normalized
            elif access == "rename" and previous is None:
                previous = pending.get(pending_key)
            status = str(event.get("status") or "observed")
            identity = identities.resolve(
                normalized,
                access,
                previous,
                status == "ok",
            )
            edges.append(
                {
                    "project": project["project"],
                    "source_id": session["source_id"],
                    "source_sha256": session["sha256"],
                    "vendor": session["vendor"],
                    "session_id": session["semantic_session_id"],
                    "session_ordinal": session_ordinal,
                    "source_stream_id": session["source_stream_id"],
                    "source_tool_ordinal": event["tool_ordinal"],
                    "record_index": event["record"],
                    "call_index": event["call"],
                    "call_id": str(event["id"]),
                    "event_ordinal": event_ordinal,
                    "action_ordinal": action_ordinal,
                    "artifact_id": identity,
                    "path": normalized,
                    "access": access,
                    "previous_path": previous,
                    "action_class": "read" if access == "read" else "mutate",
                    "status": status,
                    "confirmed_effect": status == "ok",
                }
            )
    for edge in edges:
        edge["display_path"] = identities.display[edge["artifact_id"]]

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        grouped[edge["artifact_id"]].append(edge)
    anchors = []
    for identity, rows in grouped.items():
        anchors.append(
            {
                "artifact_id": identity,
                "path": rows[-1]["display_path"],
                "path_id": oracle.path_id(rows[-1]["display_path"]),
                "call_count": len(
                    {
                        (row["session_id"], row["call_id"])
                        for row in rows
                    }
                ),
            }
        )
    anchors.sort(key=lambda row: (-row["call_count"], row["path_id"]))
    anchors = anchors[:5]

    p0_path = project["anchors"][0]["path"]
    p0_candidates = [
        anchor
        for anchor in anchors
        if anchor["path"] == p0_path
    ]
    if not p0_candidates:
        candidates = []
        for identity, rows in grouped.items():
            if any(
                row["path"] == p0_path or row["display_path"] == p0_path
                for row in rows
            ):
                candidates.append(
                    (
                        len(
                            {
                                (row["session_id"], row["call_id"])
                                for row in rows
                            }
                        ),
                        identity,
                    )
                )
        if not candidates:
            raise RuntimeError(
                f"frozen P0 is absent after correction: {project['project']}"
            )
        candidates.sort(reverse=True)
        p0_identity = candidates[0][1]
    else:
        p0_identity = p0_candidates[0]["artifact_id"]

    p0_edges = [
        row
        for row in edges
        if row["artifact_id"] == p0_identity
    ]
    p0_calls = {
        (row["session_id"], row["call_id"]): row
        for row in p0_edges
    }
    p0_ordinals = sorted(
        {row["session_ordinal"] for row in p0_edges}
    )
    session_sets = [set() for _ in sessions]
    for edge in edges:
        session_sets[edge["session_ordinal"]].add(edge["artifact_id"])
    prior: set[str] = set()
    revisit = 0
    for current in session_sets:
        revisit += bool(prior & current)
        prior |= current
    presence = [
        index in p0_ordinals
        for index in range(len(sessions))
    ]
    seen = False
    gap = False
    returns = 0
    for active in presence:
        if active:
            returns += bool(seen and gap)
            seen, gap = True, False
        elif seen:
            gap = True
    artifact_sessions: dict[str, set[int]] = defaultdict(set)
    for edge in edges:
        artifact_sessions[edge["artifact_id"]].add(
            edge["session_ordinal"]
        )

    joined = [
        " ".join(sequence) + " "
        for sequence in sequences.values()
    ]
    answers: dict[str, str] = {
        "A1": str(
            sum(
                sequence.count("read_file")
                for sequence in sequences.values()
            )
        ),
        "A2": str(
            sum(
                sequence.count("edit")
                for sequence in sequences.values()
            )
        ),
        "A3": str(
            sum(
                sequence.count("run_test")
                for sequence in sequences.values()
            )
        ),
        "A4": str(
            sum(
                bool(
                    re.search(
                        r"read_file (?:[a-z_]+ )*edit ",
                        line,
                    )
                )
                for line in joined
            )
        ),
        "A5": str(
            sum(
                bool(
                    re.search(
                        r"edit (?:[a-z_]+ )*run_test ",
                        line,
                    )
                )
                for line in joined
            )
        ),
        "B1": str(len(p0_calls)),
        "B2": str(
            sum(
                row["action_class"] == "read"
                for row in p0_calls.values()
            )
        ),
        "B3": str(
            sum(
                row["action_class"] == "mutate"
                for row in p0_calls.values()
            )
        ),
        "B4": min(
            p0_edges,
            key=lambda row: row["event_ordinal"],
        )["action_class"],
        "B5": str(len(p0_ordinals)),
        "C1": str(
            sum(
                bool(left & right)
                for left, right in zip(
                    session_sets,
                    session_sets[1:],
                )
            )
        ),
        "C2": str(revisit),
        "C3": str(returns),
        "C4": str(p0_ordinals[-1] - p0_ordinals[0]),
        "C5": str(
            sum(
                len(ordinals) >= 2
                for ordinals in artifact_sessions.values()
            )
        ),
    }
    for index, row in enumerate(
        project["workspace"]["paths"],
        start=1,
    ):
        index_entry = str(row.get("index_entry") or "")
        present = bool(row.get("present"))
        answers[f"D{index}"] = (
            "tracked"
            if index_entry
            else ("untracked" if present else "absent")
        )

    return {
        "answers": answers,
        "anchors": anchors,
        "p0_identity": p0_identity,
        "edges": edges,
        "calls": calls,
        "call_details": call_details,
        "sessions": [
            {
                "source_id": row["source_id"],
                "semantic_session_id": row["semantic_session_id"],
                "session_ordinal": index,
            }
            for index, row in enumerate(sessions)
        ],
    }


def edge_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("source_id") or ""),
        str(row.get("call_id") or ""),
        str(row.get("path") or ""),
        str(row.get("access") or ""),
        str(row.get("previous_path") or ""),
    )


def counter_rows(
    counter: Counter[tuple[str, str, str, str, str]],
) -> list[dict[str, Any]]:
    return [
        {
            "source_id": key[0],
            "call_id": key[1],
            "path": key[2],
            "access": key[3],
            "previous_path": key[4] or None,
            "count": count,
        }
        for key, count in sorted(counter.items())
    ]


def projection_edges(
    project: dict[str, Any],
    source_result: dict[str, Any],
) -> list[dict[str, Any]]:
    call_sources: dict[str, set[str]] = defaultdict(set)
    for call in source_result["calls"]:
        call_sources[call["call_id"]].add(call["source_id"])
    target_worktree = hashlib.sha256(
        os.path.realpath(project["worktree"]).encode()
    ).hexdigest()[:12]
    trace = json.loads(
        (
            RERUN
            / "projection/raw/events"
            / TRACE_FILES[project["project"]]
        ).read_text()
    )
    edges = []
    for event_ordinal, event in enumerate(
        trace.get("events") or []
    ):
        call_id = str(event.get("source_call_id") or "")
        sources = call_sources.get(call_id, set())
        if len(sources) != 1:
            continue
        source_id = next(iter(sources))
        for action in event.get("actions") or []:
            if (
                action.get("scope")
                or action.get("worktree_id") != target_worktree
            ):
                continue
            path = str(action.get("path") or "")
            if not path:
                continue
            edges.append(
                {
                    "project": project["project"],
                    "source_id": source_id,
                    "call_id": call_id,
                    "event_ordinal": event_ordinal,
                    "path": path,
                    "access": str(
                        action.get("access") or "write"
                    ),
                    "previous_path": str(
                        action.get("previous_path") or ""
                    )
                    or None,
                }
            )
    return edges


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    fraction = position - low
    return (
        ordered[low] * (1 - fraction)
        + ordered[high] * fraction
    )


def bootstrap_contrast(
    rows: list[dict[str, Any]],
    projects: list[str],
) -> dict[str, Any]:
    scores = {}
    for project in projects:
        by_method = {}
        for method in ("trajectory", "procgrep"):
            selected = [
                row
                for row in rows
                if row["project"] == project
                and row["method"] == method
                and row["family"] in {"B", "C"}
            ]
            by_method[method] = (
                sum(int(row["correct"]) for row in selected)
                / len(selected)
            )
        scores[project] = (
            by_method["trajectory"]
            - by_method["procgrep"]
        )
    rng = random.Random(SEED)
    draws = []
    for _ in range(10_000):
        sample = [
            rng.choice(projects)
            for _ in projects
        ]
        draws.append(
            statistics.mean(scores[project] for project in sample)
        )
    return {
        "estimate": statistics.mean(scores.values()),
        "ci_low": percentile(draws, 0.025),
        "ci_high": percentile(draws, 0.975),
        "project_effects": scores,
        "seed": SEED,
        "draws": 10_000,
    }


def write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, Any]],
) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    freeze = json.loads((PRIVATE / "freeze.json").read_text())
    v4 = load_current_oracle()
    v3 = load_v3_oracle()
    v2 = load_v2_oracle()
    if v4.SPEC_VERSION != "native-root-conformance-v4":
        raise RuntimeError(f"unexpected oracle version: {v4.SPEC_VERSION}")

    v3_results = {}
    v4_results = {}
    projection = {}
    all_v4_edges = []
    edge_diffs = {}
    evidence = {
        "v4_spec_version": v4.SPEC_VERSION,
        "v3_revision": V3_REVISION,
        "projects": {},
    }
    for project in freeze["projects"]:
        name = project["project"]
        before = derive_source_project(v3, project)
        after = derive_source_project(v4, project)
        v3_results[name] = before
        v4_results[name] = after
        all_v4_edges.extend(after["edges"])

        before_counter = Counter(
            edge_key(row)
            for row in before["edges"]
        )
        after_counter = Counter(
            edge_key(row)
            for row in after["edges"]
        )
        frozen_counter = Counter(
            edge_key(row)
            for row in project["oracle_edges"]
        )
        projected = projection_edges(project, after)
        projection[name] = projected
        projected_counter = Counter(
            edge_key(row)
            for row in projected
        )
        edge_diffs[name] = {
            "v4_only_vs_v3": counter_rows(
                after_counter - before_counter
            ),
            "v3_only_vs_v4": counter_rows(
                before_counter - after_counter
            ),
            "v4_only_vs_frozen_v2": counter_rows(
                after_counter - frozen_counter
            ),
            "frozen_v2_only_vs_v4": counter_rows(
                frozen_counter - after_counter
            ),
            "projection_only_vs_v4": counter_rows(
                projected_counter - after_counter
            ),
            "v4_only_vs_projection": counter_rows(
                after_counter - projected_counter
            ),
        }

        patch_calls = [
            call
            for call in after["calls"]
            if call["wrapped_patch"]
        ]
        patch_keys = {
            (call["source_id"], call["call_id"])
            for call in patch_calls
        }
        patch_edges = [
            row
            for row in after["edges"]
            if (row["source_id"], row["call_id"]) in patch_keys
        ]
        inline_cd_calls = [
            call
            for call in after["calls"]
            if re.search(
                r"(^|[;&|]\s*)cd\s+",
                call["command"],
            )
        ]
        evidence["projects"][name] = {
            "v3_edges": len(before["edges"]),
            "v4_edges": len(after["edges"]),
            "v3_answers": before["answers"],
            "v4_answers": after["answers"],
            "frozen_anchors": project["anchors"],
            "v4_ranked_anchors": after["anchors"],
            "wrapped_patch_calls": len(patch_calls),
            "wrapped_patch_edges": len(patch_edges),
            "wrapped_patch_headers_by_access": dict(
                Counter(row["access"] for row in patch_edges)
            ),
            "wrapped_patch_samples": [
                {
                    key: call[key]
                    for key in (
                        "source_id",
                        "record_index",
                        "call_id",
                        "status",
                    )
                }
                for call in patch_calls[:3]
            ],
            "inline_cd_calls": len(inline_cd_calls),
            "inline_cd_samples": [
                {
                    "source_id": call["source_id"],
                    "record_index": call["record_index"],
                    "call_id": call["call_id"],
                    "command": call["command"][:500],
                }
                for call in inline_cd_calls[:5]
            ],
            "action_v2_to_v4": action_transition_evidence(
                v2,
                v4,
                project,
            ),
        }

    corrected_answers = {}
    answer_rows = []
    frozen_answers = {
        row["id"]: str(row["answer"])
        for row in freeze["questions"]
    }
    for question in freeze["questions"]:
        corrected = v4_results[question["project"]]["answers"][
            question["template"]
        ]
        corrected_answers[question["id"]] = corrected
        answer_rows.append(
            {
                "id": question["id"],
                "project": question["project"],
                "family": question["family"],
                "template": question["template"],
                "frozen_expected": str(question["answer"]),
                "corrected_expected": corrected,
                "changed": int(
                    str(question["answer"]) != corrected
                ),
            }
        )

    with (
        RERUN / "method-results.csv"
    ).open(newline="") as handle:
        method_rows = list(csv.DictReader(handle))
    for row in method_rows:
        row["expected"] = corrected_answers[row["id"]]
        answered = row["status"] == "answer"
        row["correct"] = int(
            answered
            and str(row["answer"]) == row["expected"]
        )
        row["wrong"] = int(
            answered
            and str(row["answer"]) != row["expected"]
        )

    original_trajectory_wrong = {
        row["id"]
        for row in csv.DictReader(
            (RERUN / "method-results.csv").open(newline="")
        )
        if row["method"] == "trajectory"
        and row["family"] in {"B", "C"}
        and int(row["wrong"])
    }
    corrected_trajectory_wrong = {
        row["id"]
        for row in method_rows
        if row["method"] == "trajectory"
        and row["family"] in {"B", "C"}
        and int(row["wrong"])
    }

    aggregate = []
    for method in (
        "final_state",
        "counts",
        "procgrep",
        "trajectory",
    ):
        for family in "ABCD":
            selected = [
                row
                for row in method_rows
                if row["method"] == method
                and row["family"] == family
            ]
            correct = sum(int(row["correct"]) for row in selected)
            wrong = sum(int(row["wrong"]) for row in selected)
            abstain = sum(
                row["status"] == "abstain"
                for row in selected
            )
            answered = len(selected) - abstain
            aggregate.append(
                {
                    "method": method,
                    "family": family,
                    "correct": correct,
                    "wrong": wrong,
                    "abstain": abstain,
                    "correct_coverage": correct / len(selected),
                    "conditional_accuracy": (
                        correct / answered if answered else 0.0
                    ),
                }
            )

    projects = [
        project["project"]
        for project in freeze["projects"]
    ]
    per_project = {}
    for project in projects:
        selected = [
            row
            for row in method_rows
            if row["project"] == project
            and row["method"] == "trajectory"
            and row["family"] in {"B", "C"}
        ]
        correct = sum(int(row["correct"]) for row in selected)
        answered = sum(
            row["status"] == "answer"
            for row in selected
        )
        per_project[project] = {
            "correct": correct,
            "wrong": sum(int(row["wrong"]) for row in selected),
            "answered": answered,
            "conditional_accuracy": (
                correct / answered if answered else 0.0
            ),
        }

    contrast = bootstrap_contrast(method_rows, projects)
    changed_answers = [
        row
        for row in answer_rows
        if row["changed"]
    ]
    changed_previously_correct = []
    original_rows_by_id = {
        row["id"]: row
        for row in csv.DictReader(
            (RERUN / "method-results.csv").open(newline="")
        )
        if row["method"] == "trajectory"
    }
    for row in changed_answers:
        old_method = original_rows_by_id[row["id"]]
        if int(old_method["correct"]):
            changed_previously_correct.append(row["id"])

    summary = {
        "oracle_spec_version": v4.SPEC_VERSION,
        "questions": len(answer_rows),
        "changed_expected_answers": len(changed_answers),
        "changed_previously_correct_trajectory_rows": changed_previously_correct,
        "initial_nine_mismatches": sorted(original_trajectory_wrong),
        "initial_nine_dissolved": sorted(
            original_trajectory_wrong - corrected_trajectory_wrong
        ),
        "remaining_from_initial_nine": sorted(
            original_trajectory_wrong & corrected_trajectory_wrong
        ),
        "new_bc_mismatches": sorted(
            corrected_trajectory_wrong - original_trajectory_wrong
        ),
        "corrected_bc_mismatches": sorted(
            corrected_trajectory_wrong
        ),
        "aggregate": aggregate,
        "trajectory_bc_by_project": per_project,
        "trajectory_minus_procgrep_bc": contrast,
        "source_edge_counts": {
            project: {
                "v3": len(v3_results[project]["edges"]),
                "v4": len(v4_results[project]["edges"]),
                "projection": len(projection[project]),
            }
            for project in projects
        },
    }

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(
        OUTPUT / "corrected-answers.csv",
        [
            "id",
            "project",
            "family",
            "template",
            "frozen_expected",
            "corrected_expected",
            "changed",
        ],
        answer_rows,
    )
    write_csv(
        OUTPUT / "method-results.csv",
        list(method_rows[0]),
        method_rows,
    )
    (OUTPUT / "corrected-oracle-edges.json").write_text(
        json.dumps(
            all_v4_edges,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    (OUTPUT / "oracle-edge-diff.json").write_text(
        json.dumps(
            edge_diffs,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    (OUTPUT / "source-evidence.json").write_text(
        json.dumps(
            evidence,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    (OUTPUT / "summary.json").write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
