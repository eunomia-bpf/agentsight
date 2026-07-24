#!/usr/bin/env python3
"""Independent source reconciliation for the RQ6 public-trace experiment."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import shlex
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any


TOPIC = re.compile(r"research_topics/([^/]+)/")
VALIDATE = re.compile(
    r"(?:^|[;&|]\s*)(?:pytest|cargo\s+(?:test|check|build)|go\s+test|"
    r"npm\s+(?:test|run\s+(?:test|lint|build))|pnpm\s+(?:test|lint|build)|"
    r"yarn\s+(?:test|lint|build)|make\s+(?:test|check)|mvn\s+test|gradle\s+test)\b",
    re.IGNORECASE,
)
MUTATING_SHELL = re.compile(r"(?:^|[;&|]\s*)(?:rm|mv|cp|touch|mkdir|install|patch)\b|(?:>>?|\bsed\s+-i\b)")
PATH_TOKEN = re.compile(r"(?:/workspace/|/testbed/|\./|\.\./)[^\s'\";|&<>]+|[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+")


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def normalize(value: str) -> str | None:
    value = value.strip().strip("'\"").replace("\\", "/")
    value = re.sub(r"^(?:/workspace/[^/]+|/testbed)(?:/|$)", "", value)
    value = re.sub(r"^\./", "", value).rstrip("/,:)")
    if not value or value.startswith(("http://", "https://")) or value in {".", "..", "/"}:
        return None
    path = PurePosixPath(value)
    return None if path.is_absolute() or ".." in path.parts else str(path)


def root(path: str) -> str:
    parts = PurePosixPath(path).parts
    return parts[0] if len(parts) > 1 else "repo-root-files"


def arguments(call: dict[str, Any]) -> dict[str, Any]:
    value = (call.get("function") or {}).get("arguments")
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return decoded if isinstance(decoded, dict) else {}


def paths_from_shell(command: str) -> set[str]:
    candidates = set(PATH_TOKEN.findall(command))
    try:
        for token in shlex.split(command):
            if token.startswith("-") or ("=" in token and not token.startswith(("./", "../", "/"))):
                continue
            if "/" in token or re.search(r"\.[A-Za-z0-9]{1,8}$", token):
                candidates.add(token)
    except ValueError:
        pass
    return {path for token in candidates if (path := normalize(token))}


def project_call(call: dict[str, Any]) -> tuple[bool, bool, set[str]]:
    function = call.get("function") or {}
    name = str(function.get("name") or "").lower()
    args = arguments(call)
    mutate = name in {"write", "edit"}
    validate = False
    paths: set[str] = set()
    if name == "str_replace_editor":
        mutate = str(args.get("command") or "").lower() in {"create", "str_replace", "insert", "undo_edit"}
    if name in {"bash", "execute_bash"}:
        command = str(args.get("command") or args.get("cmd") or "")
        mutate = bool(MUTATING_SHELL.search(command))
        validate = bool(VALIDATE.search(command))
        paths.update(paths_from_shell(command))
    for key in ["path", "file_path", "old_path", "new_path"]:
        value = args.get(key)
        if isinstance(value, str) and (path := normalize(value)):
            paths.add(path)
    return mutate, validate, paths


def all_calls(row: dict[str, Any], corpus: str) -> list[dict[str, Any]]:
    messages = row.get("trajectory", []) if corpus == "openswe" else row.get("messages", [])
    return [
        call
        for message in messages
        if message.get("role") == "assistant"
        for call in (message.get("tool_calls") or [])
    ]


def recount(row: dict[str, Any], corpus: str) -> dict[str, int]:
    calls = all_calls(row, corpus)
    projected = [project_call(call) for call in calls]
    path_calls = [paths for _, _, paths in projected if paths]
    transitions = Counter()
    for left, right in zip(path_calls, path_calls[1:]):
        if left & right:
            transitions["same_path"] += 1
        elif {root(path) for path in left} & {root(path) for path in right}:
            transitions["same_module"] += 1
        else:
            transitions["cross_module"] += 1
    return {
        "tool_calls": len(calls),
        "path_resolved_calls": len(path_calls),
        "mutation_calls": sum(mutate for mutate, _, _ in projected),
        "validation_attempts": sum(validate for _, validate, _ in projected),
        "eligible_transitions": sum(transitions.values()),
        "same_path": transitions["same_path"],
        "same_module": transitions["same_module"],
        "cross_module": transitions["cross_module"],
    }


def topic(row: dict[str, Any]) -> str:
    system = next((message.get("content") or "" for message in row.get("messages", []) if message.get("role") == "system"), "")
    match = TOPIC.search(system)
    return match.group(1) if match else ""


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = read_csv(args.experiment / "sample-manifest.csv")
    metrics = {row["row_id"]: row for row in read_csv(args.experiment / "trajectory-metrics.csv")}
    mismatches = []
    totals = Counter()
    clusters: dict[tuple[str, str], set[str]] = {}
    openswe_strata_by_instance: dict[str, set[str]] = {}
    for entry in manifest:
        corpus = entry["corpus"]
        stratum = f"{entry['config']}-{entry['split']}"
        path = args.experiment / "raw" / corpus / stratum / f"{int(entry['row_offset']):06d}.json.gz"
        with gzip.open(path, "rb") as stream:
            row = json.loads(stream.read())
        row_sha = hashlib.sha256(canonical(row)).hexdigest()
        if row_sha != entry["row_sha256"]:
            mismatches.append(f"row hash: {entry['row_id']}")
        row_id = str(row.get("trajectory_id") if corpus == "openswe" else row.get("sample_id"))
        cluster = str(row.get("instance_id") if corpus == "openswe" else topic(row))
        if row_id != entry["row_id"] or cluster != entry["cluster_id"]:
            mismatches.append(f"identity: {entry['row_id']}")
        clusters.setdefault((corpus, entry["config"] + "/" + entry["split"]), set()).add(cluster)
        if corpus == "openswe":
            openswe_strata_by_instance.setdefault(cluster, set()).add(entry["config"] + "/" + entry["split"])
        actual = recount(row, corpus)
        expected = metrics.get(row_id)
        if expected is None:
            mismatches.append(f"missing metrics: {row_id}")
            continue
        for field, value in actual.items():
            totals[field] += value
            if int(expected[field]) != value:
                mismatches.append(f"{field}: {row_id}: {expected[field]} != {value}")

    expected_groups = {
        ("openswe", "openhands/minimax_m25"),
        ("openswe", "openhands/qwen35_122b"),
        ("openswe", "sweagent/minimax_m25"),
        ("openswe", "sweagent/qwen35_122b"),
        ("ideatrail", "default/train"),
    }
    if set(clusters) != expected_groups:
        mismatches.append("strata do not match the preregistration")
    for key, values in clusters.items():
        if len(values) != 64:
            mismatches.append(f"independent unit count {key}: {len(values)}")
    if len(manifest) != 320 or len(metrics) != 320:
        mismatches.append(f"row counts manifest={len(manifest)} metrics={len(metrics)}")

    result = {
        "status": "PASS" if not mismatches else "BLOCK",
        "manifest_rows": len(manifest),
        "metric_rows": len(metrics),
        "independent_units_by_stratum": {f"{key[0]}:{key[1]}": len(value) for key, value in sorted(clusters.items())},
        "openswe_unique_instance_ids_across_strata": len(openswe_strata_by_instance),
        "openswe_instance_ids_selected_in_multiple_strata": {
            instance: sorted(strata)
            for instance, strata in sorted(openswe_strata_by_instance.items())
            if len(strata) > 1
        },
        "recounted_totals": dict(sorted(totals.items())),
        "mismatches": mismatches[:100],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if mismatches:
        raise SystemExit(f"RQ6 source reconciliation BLOCK: {len(mismatches)} mismatches")


if __name__ == "__main__":
    main()
