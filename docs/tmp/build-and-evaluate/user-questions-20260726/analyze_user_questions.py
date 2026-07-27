#!/usr/bin/env python3
"""Answer four user-facing questions from the final-HEAD RQ1 export.

The analyses are deliberately descriptive. They consume only the exported
artifact table, mutation table, project coverage, and event JSON files; they
do not infer artifact quality, intent, progress, usefulness, or time spent.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


DEFAULT_INPUT = Path(
    "docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw"
)
DEFAULT_OUTPUT = Path(
    "docs/tmp/build-and-evaluate/user-questions-20260726"
)

PROJECT_ORDER = (
    "agentsight",
    "ActPlane",
    "bpf-developer-tutorial",
    "eunomia.dev",
    "agentskill-observability-paper",
    "academic-writing-skills",
)
FIVE_TYPES = ("paper/docs", "code", "test", "config", "other")
FOUR_TYPES = ("paper/docs", "code", "test", "other")
MUTATION_ACCESSES = {"create", "write", "rename", "delete"}

TEST_PARTS = {
    "test",
    "tests",
    "testing",
    "__tests__",
    "spec",
    "specs",
}
DOC_PARTS = {
    "doc",
    "docs",
    "paper",
    "papers",
    "note",
    "notes",
    "research",
}
CONFIG_PARTS = {
    ".github",
    ".gitlab",
    ".circleci",
    "config",
    ".config",
    "ci",
}
CONFIG_NAMES = {
    ".clang-format",
    ".clang-tidy",
    ".dockerignore",
    ".editorconfig",
    ".gitignore",
    ".gitmodules",
    ".pre-commit-config.yaml",
    "cargo.lock",
    "cargo.toml",
    "cmakelists.txt",
    "compose.yaml",
    "compose.yml",
    "docker-compose.yaml",
    "docker-compose.yml",
    "dockerfile",
    "go.mod",
    "go.sum",
    "makefile",
    "package-lock.json",
    "package.json",
    "pnpm-lock.yaml",
    "pom.xml",
    "pyproject.toml",
    "requirements.txt",
    "setup.cfg",
    "setup.py",
    "tox.ini",
    "yarn.lock",
}
DOC_EXTENSIONS = {
    ".adoc",
    ".bib",
    ".md",
    ".mdx",
    ".org",
    ".pdf",
    ".rst",
    ".tex",
    ".txt",
    ".typ",
}
CONFIG_EXTENSIONS = {
    ".cfg",
    ".ini",
    ".lock",
    ".toml",
    ".yaml",
    ".yml",
}
CODE_EXTENSIONS = {
    ".asm",
    ".bash",
    ".c",
    ".cc",
    ".clj",
    ".cjs",
    ".cpp",
    ".cs",
    ".css",
    ".cu",
    ".cuh",
    ".dart",
    ".ex",
    ".exs",
    ".fs",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".j2",
    ".jinja",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".lua",
    ".mjs",
    ".mm",
    ".php",
    ".pl",
    ".proto",
    ".py",
    ".r",
    ".rb",
    ".rs",
    ".scala",
    ".scss",
    ".sh",
    ".sql",
    ".svelte",
    ".swift",
    ".ts",
    ".tsx",
    ".vue",
    ".zig",
}
DATA_RESULT_EXTENSIONS = {
    ".csv",
    ".db",
    ".gif",
    ".jpeg",
    ".jpg",
    ".json",
    ".jsonl",
    ".log",
    ".mp4",
    ".npy",
    ".npz",
    ".parquet",
    ".png",
    ".sqlite",
    ".svg",
    ".tsv",
}
PAPER_ASSET_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".pdf", ".png", ".svg"}
GENERIC_MODULE_ROOTS = {
    "src",
    "source",
    "sources",
    "lib",
    "libs",
    "test",
    "tests",
    "testing",
    "__tests__",
    "spec",
    "specs",
}
GENERATED_PATH_PARTS = {
    "__pycache__",
    ".pytest_cache",
    "node_modules",
}
TEST_SUPPORT_OR_OUTPUT_PARTS = {
    "bench",
    "benches",
    "benchmark",
    "benchmarks",
    "data",
    "fixture",
    "fixtures",
    "log",
    "logs",
    "output",
    "outputs",
    "result",
    "results",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def read_json(path: Path) -> dict[str, Any] | list[Any]:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            return json.load(stream)
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def event_path(events_dir: Path, project: str) -> Path:
    names = (project, "eunomia-dev") if project == "eunomia.dev" else (project,)
    for name in names:
        for suffix in (".json.gz", ".json"):
            candidate = events_dir / f"{name}{suffix}"
            if candidate.is_file():
                return candidate
    raise FileNotFoundError(f"missing event export for {project}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(
    path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=fieldnames,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def fraction(numerator: int, denominator: int) -> float | str:
    return numerator / denominator if denominator else ""


def normalized_path(path: str) -> tuple[str, tuple[str, ...], str, str]:
    normalized = str(PurePosixPath(path)).replace("\\", "/").lower()
    parts = PurePosixPath(normalized).parts
    basename = parts[-1] if parts else ""
    suffix = PurePosixPath(basename).suffix
    return normalized, parts, basename, suffix


def classify_path(path: str) -> str:
    """Classify a path using the report's declared precedence."""
    normalized, parts, basename, suffix = normalized_path(path)
    executable_test_name = suffix in CODE_EXTENSIONS and (
        basename.startswith("test_")
        or bool(re.match(r".+_(?:test|tests)\.[^.]+$", basename))
        or ".test." in basename
        or ".spec." in basename
    )
    test_support_or_output = (
        any(part in TEST_PARTS for part in parts)
        and any(part in TEST_SUPPORT_OR_OUTPUT_PARTS for part in parts)
    )
    executable_test_path = (
        suffix in CODE_EXTENSIONS
        and any(part in TEST_PARTS for part in parts)
        and not any(part in GENERATED_PATH_PARTS for part in parts)
        and not test_support_or_output
    )
    if (
        executable_test_name
        and not any(part in GENERATED_PATH_PARTS for part in parts)
        and not test_support_or_output
    ) or executable_test_path:
        return "test"
    # Explicit document extensions/names take precedence over the directory
    # (for example, a Markdown checklist under .github remains a document).
    if (
        bool(
            re.match(
                r"^(readme|changelog|changes|license|contributing)"
                r"(?:\.[^.]+)?$",
                basename,
            )
        )
        or suffix in DOC_EXTENSIONS
    ):
        return "paper/docs"
    if (
        any(part in {"paper", "papers"} for part in parts)
        and suffix in PAPER_ASSET_EXTENSIONS
    ):
        return "paper/docs"
    config_json = (
        basename.endswith("config.json")
        or basename.startswith("tsconfig")
        or basename.startswith("jsconfig")
    )
    if (
        basename in CONFIG_NAMES
        or suffix in CONFIG_EXTENSIONS
        or config_json
    ):
        return "config"
    if any(part in GENERATED_PATH_PARTS for part in parts):
        return "other"
    if test_support_or_output:
        return "other"
    if suffix in CODE_EXTENSIONS:
        return "code"
    if any(part in CONFIG_PARTS for part in parts):
        return "config"
    if suffix in DATA_RESULT_EXTENSIONS:
        return "other"
    # Directory-only evidence is a fallback after recognizable file types, so
    # docs/analyze.py remains code rather than being counted as prose.
    if any(part in DOC_PARTS for part in parts):
        return "paper/docs"
    return "other"


def four_type(five_type: str) -> str:
    return five_type if five_type in {"paper/docs", "code", "test"} else "other"


def module_anchor(path: str) -> str:
    """Return a conservative top-level module anchor for code/test pairing."""
    _, parts, _, _ = normalized_path(path)
    if not parts or len(parts) == 1:
        return "repo-root"
    first = parts[0]
    return "repo-root" if first in GENERIC_MODULE_ROOTS else first


def self_test_classification() -> None:
    expected = {
        "tests/foo.rs": "test",
        "docs/test_notes.md": "paper/docs",
        "docs/analyze.py": "code",
        "tests/result.json": "other",
        "tests/__pycache__/test_foo.py": "other",
        "tests/results/test_runner.py": "other",
        "fixtures/sample.json": "other",
        "benchmarks/report.csv": "other",
        ".github/guide.md": "paper/docs",
        "docs/paper/figure.svg": "paper/docs",
        "docs/paper/main.tex": "paper/docs",
        "Cargo.toml": "config",
        "src/config.rs": "code",
        "docs/data.jsonl": "other",
        "docs/data.json": "other",
        "config/settings.json": "config",
        "docs/diagram.svg": "other",
        "README": "paper/docs",
    }
    for path, artifact_type in expected.items():
        actual = classify_path(path)
        if actual != artifact_type:
            raise AssertionError(
                f"classification self-test failed: {path}: "
                f"{actual} != {artifact_type}"
            )
    module_expected = {
        "collector/src/main.rs": "collector",
        "collector/tests/cli.rs": "collector",
        "src/main.rs": "repo-root",
        "tests/test_main.py": "repo-root",
    }
    for path, module in module_expected.items():
        actual = module_anchor(path)
        if actual != module:
            raise AssertionError(
                f"module self-test failed: {path}: {actual} != {module}"
            )


def artifact_analysis(
    artifacts: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    details: list[dict[str, Any]] = []
    counts: Counter[tuple[str, str]] = Counter()
    revisits: Counter[tuple[str, str]] = Counter()
    rereads: Counter[tuple[str, str]] = Counter()
    for row in artifacts:
        if row["birth_state"] != "confirmed_create":
            continue
        artifact_type = four_type(classify_path(row["first_path"]))
        final_type = (
            four_type(classify_path(row["final_path"]))
            if row["final_path"]
            else ""
        )
        renamed_across_type = bool(
            row["final_path"] and final_type != artifact_type
        )
        # The first confirmed mutation is the create itself. A later read or
        # second mutation is a revisit even when it occurs in the same Tool
        # event (46 create/delete compound episodes exist in this export).
        any_revisit = (
            int(row["last_event_index"]) > int(row["first_event_index"])
            or int(row["reads"]) > 0
            or int(row["mutations"]) > 1
        )
        later_read = int(row["reads"]) > 0
        details.append(
            {
                "project": row["project"],
                "worktree_id": row["worktree_id"],
                "artifact_id": row["artifact_id"],
                "first_path": row["first_path"],
                "final_path": row["final_path"],
                "artifact_type": artifact_type,
                "final_artifact_type": final_type,
                "renamed_across_type": renamed_across_type,
                "first_event_index": int(row["first_event_index"]),
                "last_event_index": int(row["last_event_index"]),
                "any_revisit": any_revisit,
                "never_revisited": not any_revisit,
                "later_read": later_read,
                "later_read_count": int(row["reads"]),
                "mutation_count": int(row["mutations"]),
            }
        )
        if later_read and not any_revisit:
            raise ValueError(
                f"later read without later event: "
                f"{row['project']}:{row['artifact_id']}"
            )
        for project in (row["project"], "ALL_POOLED"):
            key = (project, artifact_type)
            counts[key] += 1
            revisits[key] += any_revisit
            rereads[key] += later_read

    summary: list[dict[str, Any]] = []
    for project in (*PROJECT_ORDER, "ALL_POOLED"):
        for artifact_type in FOUR_TYPES:
            key = (project, artifact_type)
            created = counts[key]
            revisited = revisits[key]
            read_later = rereads[key]
            summary.append(
                {
                    "project": project,
                    "artifact_type": artifact_type,
                    "created_artifacts": created,
                    "revisited_artifacts": revisited,
                    "never_revisited_artifacts": created - revisited,
                    "never_revisited_fraction": fraction(created - revisited, created),
                    "later_read_artifacts": read_later,
                    "later_read_fraction": fraction(read_later, created),
                }
            )
    return details, summary


def collapse_mutations(
    mutations: list[dict[str, str]],
    event_metadata: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[tuple[int, dict[str, str]]]] = (
        defaultdict(list)
    )
    for row_index, row in enumerate(mutations):
        grouped[
            (
                row["project"],
                row["worktree_id"],
                row["artifact_id"],
                row["event_id"],
            )
        ].append((row_index, row))

    episodes: list[dict[str, Any]] = []
    for key, indexed_rows in grouped.items():
        project, worktree_id, artifact_id, event_id = key
        rows = [row for _, row in indexed_rows]
        event_indexes = {int(row["event_index"]) for row in rows}
        timestamps = {int(row["ts_ms"]) for row in rows}
        sessions = {row["session_id"] for row in rows}
        if len(event_indexes) != 1 or len(timestamps) != 1 or len(sessions) != 1:
            raise ValueError(f"inconsistent compound mutation episode: {key}")
        if len({row["path"] for row in rows}) != 1:
            raise ValueError(f"compound mutation crosses paths: {key}")
        if len({classify_path(row["path"]) for row in rows}) != 1:
            raise ValueError(f"compound mutation crosses types: {key}")
        last_row = indexed_rows[-1][1]
        artifact_type = classify_path(last_row["path"])
        metadata = event_metadata.get((project, event_id), {})
        prompt_index = metadata.get("prompt_index", "")
        if prompt_index == "":
            raise ValueError(f"missing prompt index for mutation event: {key}")
        source_stream_id = metadata.get("source_stream_id", "")
        if source_stream_id == "":
            raise ValueError(f"missing source stream for mutation event: {key}")
        if metadata.get("session_id") != next(iter(sessions)):
            raise ValueError(f"session join mismatch for mutation event: {key}")
        csv_operations = [row["operation"] for row in rows]
        raw_operations = metadata.get("mutation_ops_by_worktree_path", {}).get(
            (worktree_id, last_row["path"]), []
        )
        if len(rows) > 1 and csv_operations != raw_operations:
            raise ValueError(
                f"compound mutation order mismatch for {key}: "
                f"{csv_operations} != {raw_operations}"
            )
        episodes.append(
            {
                "project": project,
                "worktree_id": worktree_id,
                "artifact_id": artifact_id,
                "event_id": event_id,
                "event_index": next(iter(event_indexes)),
                "ts_ms": next(iter(timestamps)),
                "session_id": next(iter(sessions)),
                "source_stream_id": source_stream_id,
                "prompt_index": prompt_index,
                "path": last_row["path"],
                "artifact_type": artifact_type,
                "module_anchor": module_anchor(last_row["path"]),
                "operations": ";".join(
                    sorted({row["operation"] for row in rows})
                ),
                "raw_mutation_rows": len(rows),
                # A create+delete compound episode is evaluated from its final
                # mutation row, after same-call supersession has closed.
                "validation_outcome": last_row["validation_outcome"],
                "validation_associated": (
                    last_row["validation_outcome"] == "observed_validation"
                ),
                "_row_index": indexed_rows[0][0],
            }
        )

    episodes.sort(
        key=lambda row: (
            PROJECT_ORDER.index(str(row["project"])),
            int(row["event_index"]),
            int(row["_row_index"]),
        )
    )
    by_artifact: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(
        list
    )
    for row in episodes:
        by_artifact[
            (row["project"], row["worktree_id"], row["artifact_id"])
        ].append(row)
    for rows in by_artifact.values():
        rows.sort(key=lambda row: (int(row["event_index"]), int(row["_row_index"])))
        for ordinal, row in enumerate(rows, 1):
            row["artifact_episode_ordinal"] = ordinal
            row["repeat_episode"] = ordinal > 1
    for row in episodes:
        row.pop("_row_index")
    return episodes


def basename_pair_key(path: str, artifact_type: str) -> tuple[str, str]:
    """Return a conservative source/test basename key."""
    _, _, basename, suffix = normalized_path(path)
    stem = basename[: -len(suffix)] if suffix else basename
    if artifact_type == "test":
        if stem.startswith("test_"):
            stem = stem[5:]
        stem = re.sub(r"_(?:test|tests|spec)$", "", stem)
        stem = re.sub(r"\.(?:test|spec)$", "", stem)
    return stem, suffix


def test_code_order_analysis(
    episodes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Pair source/tests by basename, then use same-event module co-occurrence."""
    grouped: dict[
        tuple[str, str, str, str, int | str, str], list[dict[str, Any]]
    ] = defaultdict(list)
    for row in episodes:
        if row["artifact_type"] not in {"test", "code"}:
            continue
        grouped[
            (
                row["project"],
                row["worktree_id"],
                row["session_id"],
                row["source_stream_id"],
                row["prompt_index"],
                row["module_anchor"],
            )
        ].append(row)

    details: list[dict[str, Any]] = []
    for group_key, rows in grouped.items():
        (
            project,
            worktree_id,
            session_id,
            source_stream_id,
            prompt_index,
            module,
        ) = group_key
        by_pair_key: dict[
            tuple[str, str], dict[str, list[dict[str, Any]]]
        ] = defaultdict(lambda: {"test": [], "code": []})
        for row in rows:
            pair_key = basename_pair_key(
                str(row["path"]), str(row["artifact_type"])
            )
            by_pair_key[pair_key][str(row["artifact_type"])].append(row)

        used_artifacts: set[str] = set()
        for pair_key, classes in sorted(by_pair_key.items()):
            test_rows = classes["test"]
            code_rows = classes["code"]
            test_artifacts = {str(row["artifact_id"]) for row in test_rows}
            code_artifacts = {str(row["artifact_id"]) for row in code_rows}
            # Ambiguous many-to-many stems are not called reliable pairs.
            if len(test_artifacts) != 1 or len(code_artifacts) != 1:
                continue
            first_test = min(int(row["event_index"]) for row in test_rows)
            first_code = min(int(row["event_index"]) for row in code_rows)
            order = (
                "test_first"
                if first_test < first_code
                else "code_first"
                if first_code < first_test
                else "tied_same_tool_event"
            )
            used_artifacts.update(test_artifacts | code_artifacts)
            details.append(
                {
                    "project": project,
                    "worktree_id": worktree_id,
                    "session_id": session_id,
                    "source_stream_id": source_stream_id,
                    "prompt_index": prompt_index,
                    "module_anchor": module,
                    "pairing_method": "basename_pair",
                    "pair_key": f"{pair_key[0]}{pair_key[1]}",
                    "test_paths": ";".join(
                        sorted({str(row["path"]) for row in test_rows})
                    ),
                    "code_paths": ";".join(
                        sorted({str(row["path"]) for row in code_rows})
                    ),
                    "order": order,
                    "first_test_event_index": first_test,
                    "first_code_event_index": first_code,
                    "test_artifacts": 1,
                    "code_artifacts": 1,
                    "test_mutation_episodes": len(test_rows),
                    "code_mutation_episodes": len(code_rows),
                }
            )

        # Conservative fallback: remaining test and code mutations must occur
        # in the same Tool event and module; their order is therefore tied.
        by_event: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            if str(row["artifact_id"]) not in used_artifacts:
                by_event[int(row["event_index"])].append(row)
        for event_index, event_rows in sorted(by_event.items()):
            test_rows = [
                row for row in event_rows if row["artifact_type"] == "test"
            ]
            code_rows = [
                row for row in event_rows if row["artifact_type"] == "code"
            ]
            if not test_rows or not code_rows:
                continue
            details.append(
                {
                    "project": project,
                    "worktree_id": worktree_id,
                    "session_id": session_id,
                    "source_stream_id": source_stream_id,
                    "prompt_index": prompt_index,
                    "module_anchor": module,
                    "pairing_method": "same_event_module_fallback",
                    "pair_key": "",
                    "test_paths": ";".join(
                        sorted({str(row["path"]) for row in test_rows})
                    ),
                    "code_paths": ";".join(
                        sorted({str(row["path"]) for row in code_rows})
                    ),
                    "order": "tied_same_tool_event",
                    "first_test_event_index": event_index,
                    "first_code_event_index": event_index,
                    "test_artifacts": len(
                        {row["artifact_id"] for row in test_rows}
                    ),
                    "code_artifacts": len(
                        {row["artifact_id"] for row in code_rows}
                    ),
                    "test_mutation_episodes": len(test_rows),
                    "code_mutation_episodes": len(code_rows),
                }
            )

    details.sort(
        key=lambda row: (
            PROJECT_ORDER.index(str(row["project"])),
            str(row["worktree_id"]),
            str(row["session_id"]),
            str(row["source_stream_id"]),
            int(row["prompt_index"]),
            str(row["module_anchor"]),
            int(row["first_test_event_index"]),
            str(row["pairing_method"]),
        )
    )

    counts: Counter[tuple[str, str]] = Counter()
    for row in details:
        for project in (row["project"], "ALL_POOLED"):
            counts[(project, str(row["order"]))] += 1
            counts[(project, str(row["pairing_method"]))] += 1
    summary: list[dict[str, Any]] = []
    for project in (*PROJECT_ORDER, "ALL_POOLED"):
        total = sum(
            counts[(project, order)]
            for order in ("test_first", "code_first", "tied_same_tool_event")
        )
        summary.append(
            {
                "project": project,
                "eligible_paired_episodes": total,
                "basename_pair_episodes": counts[
                    (project, "basename_pair")
                ],
                "same_event_module_fallback_episodes": counts[
                    (project, "same_event_module_fallback")
                ],
                "test_first": counts[(project, "test_first")],
                "test_first_fraction": fraction(
                    counts[(project, "test_first")], total
                ),
                "code_first": counts[(project, "code_first")],
                "code_first_fraction": fraction(
                    counts[(project, "code_first")], total
                ),
                "tied_same_tool_event": counts[
                    (project, "tied_same_tool_event")
                ],
                "tied_fraction": fraction(
                    counts[(project, "tied_same_tool_event")], total
                ),
            }
        )
    return details, summary


def action_allocation(
    input_root: Path, projects_payload: list[dict[str, Any]]
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[tuple[str, str], dict[str, Any]],
    list[dict[str, Any]],
]:
    counts: Counter[tuple[str, str, str, str]] = Counter()
    event_checks: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    event_metadata: dict[tuple[str, str], dict[str, Any]] = {}
    audit_counts: Counter[tuple[str, str, str, str, str]] = Counter()
    for project_row in projects_payload:
        project = str(project_row["project"])
        path = event_path(input_root / "events", project)
        payload = read_json(path)
        if not isinstance(payload, dict):
            raise TypeError(f"unexpected event payload: {path}")
        if payload.get("repository") != project:
            raise ValueError(
                f"event repository mismatch: {payload.get('repository')} != {project}"
            )
        if payload.get("revision") != project_row["revision"]:
            raise ValueError(
                f"event revision mismatch for {project}: "
                f"{payload.get('revision')} != {project_row['revision']}"
            )
        events = payload["events"]
        if len(events) != int(project_row["tool_actions"]):
            raise ValueError(
                f"event count mismatch for {project}: "
                f"{len(events)} != {project_row['tool_actions']}"
            )
        admitted_by_status: Counter[str] = Counter()
        excluded_rename_from_by_status: Counter[str] = Counter()
        for event in events:
            event_key = (project, str(event["id"]))
            if event_key in event_metadata:
                raise ValueError(f"duplicate event ID: {event_key}")
            ordered_actions = sorted(
                event.get("actions", []),
                key=lambda action: int(action.get("action_ordinal", 0)),
            )
            mutation_ops_by_worktree_path: dict[
                tuple[str, str], list[str]
            ] = defaultdict(list)
            if event.get("status") == "ok":
                for action in ordered_actions:
                    if action.get("scope", False):
                        continue
                    access = str(action.get("access", ""))
                    if access in MUTATION_ACCESSES:
                        mutation_ops_by_worktree_path[
                            (
                                str(action.get("worktree_id", "")),
                                str(action.get("path", "")),
                            )
                        ].append(access)
            event_metadata[event_key] = {
                "prompt_index": event.get("prompt_index", ""),
                "source_stream_id": event.get("source_stream_id", ""),
                "session_id": event.get("session_id", ""),
                "mutation_ops_by_worktree_path": dict(
                    mutation_ops_by_worktree_path
                ),
            }
            status = str(event.get("status", ""))
            if status not in {"ok", "observed"}:
                continue
            for action in ordered_actions:
                if action.get("scope", False):
                    continue
                access = str(action.get("access", ""))
                if access == "read":
                    mode = "read"
                elif access in MUTATION_ACCESSES:
                    mode = "write"
                elif access == "rename_from":
                    excluded_rename_from_by_status[status] += 1
                    continue
                else:
                    continue
                path_value = str(action.get("path", ""))
                artifact_type = classify_path(path_value)
                bases = (
                    ("ok_only", "ok_plus_observed")
                    if status == "ok"
                    else ("observed_only", "ok_plus_observed")
                )
                for basis in bases:
                    counts[(basis, project, mode, artifact_type)] += 1
                    counts[(basis, "ALL_POOLED", mode, artifact_type)] += 1
                admitted_by_status[status] += 1

                _, parts, _, suffix = normalized_path(path_value)
                conflicts: list[str] = []
                if any(part in DOC_PARTS for part in parts) and suffix in CODE_EXTENSIONS:
                    conflicts.append("docs_path_with_code_extension")
                if any(part in TEST_PARTS for part in parts) and suffix not in CODE_EXTENSIONS:
                    conflicts.append("test_path_with_noncode_extension")
                if any(
                    part in {"bench", "benches", "benchmark", "benchmarks", "fixture", "fixtures"}
                    for part in parts
                ):
                    conflicts.append("bench_or_fixture_path")
                if (
                    any(part in {"paper", "papers"} for part in parts)
                    and suffix in PAPER_ASSET_EXTENSIONS
                ):
                    conflicts.append("paper_asset")
                for conflict in conflicts:
                    audit_counts[
                        (project, path_value, conflict, artifact_type, status)
                    ] += 1
        event_checks.append(
            {
                "project": project,
                "tool_events": len(events),
                "ok_nonscope_read_write_actions": admitted_by_status["ok"],
                "observed_nonscope_read_write_actions": admitted_by_status[
                    "observed"
                ],
                "ok_plus_observed_nonscope_read_write_actions": (
                    admitted_by_status["ok"] + admitted_by_status["observed"]
                ),
                "excluded_ok_rename_from_helpers": (
                    excluded_rename_from_by_status["ok"]
                ),
                "excluded_observed_rename_from_helpers": (
                    excluded_rename_from_by_status["observed"]
                ),
            }
        )
        provenance.append(
            {
                "input": str(path),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
        )

    rows: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    for basis in ("ok_only", "observed_only", "ok_plus_observed"):
        for project in (*PROJECT_ORDER, "ALL_POOLED"):
            for mode in ("read", "write"):
                total = sum(
                    counts[(basis, project, mode, kind)] for kind in FIVE_TYPES
                )
                for kind in FIVE_TYPES:
                    count = counts[(basis, project, mode, kind)]
                    rows.append(
                        {
                            "status_basis": basis,
                            "project": project,
                            "action_mode": mode,
                            "artifact_type": kind,
                            "actions": count,
                            "share_within_project_mode": fraction(count, total),
                            "project_mode_total": total,
                        }
                    )
                docs = counts[(basis, project, mode, "paper/docs")]
                code = counts[(basis, project, mode, "code")]
                if docs > code:
                    larger = "paper/docs"
                elif code > docs:
                    larger = "code"
                else:
                    larger = "tie"
                comparisons.append(
                    {
                        "status_basis": basis,
                        "project": project,
                        "action_mode": mode,
                        "paper_docs_actions": docs,
                        "code_actions": code,
                        "paper_docs_share": fraction(docs, total),
                        "code_share": fraction(code, total),
                        "larger_category": larger,
                        "paper_docs_to_code_ratio": (
                            docs / code if code else ""
                        ),
                    }
                )

    audit_rows: list[dict[str, Any]] = []
    audit_grouped: Counter[tuple[str, str, str, str]] = Counter()
    for (project, path_value, conflict, artifact_type, status), count in (
        audit_counts.items()
    ):
        audit_grouped[(project, path_value, conflict, artifact_type)] += count
    for key in sorted(audit_grouped):
        project, path_value, conflict, artifact_type = key
        audit_rows.append(
            {
                "project": project,
                "path": path_value,
                "audit_reason": conflict,
                "assigned_type": artifact_type,
                "ok_plus_observed_actions": audit_grouped[key],
            }
        )
    return (
        rows,
        comparisons,
        event_checks + provenance,
        event_metadata,
        audit_rows,
    )


def churn_analysis(
    episodes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for project in (*PROJECT_ORDER, "ALL_POOLED"):
        selected = [
            row
            for row in episodes
            if (project == "ALL_POOLED" or row["project"] == project)
            and row["artifact_type"] in {"test", "code"}
        ]
        for artifact_type in ("test", "code"):
            rows = [
                row for row in selected if row["artifact_type"] == artifact_type
            ]
            artifact_keys = {
                (row["project"], row["worktree_id"], row["artifact_id"])
                for row in rows
            }
            repeated_artifacts = {
                key
                for key in artifact_keys
                if sum(
                    (
                        row["project"],
                        row["worktree_id"],
                        row["artifact_id"],
                    )
                    == key
                    for row in rows
                )
                > 1
            }
            repeat_episodes = sum(bool(row["repeat_episode"]) for row in rows)
            validated = sum(
                bool(row["validation_associated"]) for row in rows
            )
            outcome_counts = Counter(
                str(row["validation_outcome"]) for row in rows
            )
            summary.append(
                {
                    "project": project,
                    "artifact_type": artifact_type,
                    "mutated_artifacts": len(artifact_keys),
                    "mutation_episodes": len(rows),
                    "episodes_per_mutated_artifact": (
                        len(rows) / len(artifact_keys) if artifact_keys else ""
                    ),
                    "repeat_episodes": repeat_episodes,
                    "repeat_episode_fraction": fraction(
                        repeat_episodes, len(rows)
                    ),
                    "repeated_artifacts": len(repeated_artifacts),
                    "repeated_artifact_fraction": fraction(
                        len(repeated_artifacts), len(artifact_keys)
                    ),
                    "validation_associated_episodes": validated,
                    "validation_association_fraction": fraction(
                        validated, len(rows)
                    ),
                    "competing_supersede_episodes": outcome_counts[
                        "competing_supersede"
                    ],
                    "censored_end_episodes": outcome_counts["censored_end"],
                }
            )
    return summary


def paired_churn_analysis(
    episodes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Compare test/code churn inside the same stream-prompt-module block."""
    grouped: dict[
        tuple[str, str, str, str, int | str, str], list[dict[str, Any]]
    ] = defaultdict(list)
    for row in episodes:
        if row["artifact_type"] not in {"test", "code"}:
            continue
        grouped[
            (
                row["project"],
                row["worktree_id"],
                row["session_id"],
                row["source_stream_id"],
                row["prompt_index"],
                row["module_anchor"],
            )
        ].append(row)

    details: list[dict[str, Any]] = []
    for key, rows in grouped.items():
        test_rows = [row for row in rows if row["artifact_type"] == "test"]
        if not test_rows:
            continue
        code_rows = [row for row in rows if row["artifact_type"] == "code"]
        test_counts = Counter(str(row["artifact_id"]) for row in test_rows)
        code_counts = Counter(str(row["artifact_id"]) for row in code_rows)
        repeated_test_identities = sum(count > 1 for count in test_counts.values())
        repeated_code_identities = sum(count > 1 for count in code_counts.values())
        test_repeat_episodes = sum(count - 1 for count in test_counts.values())
        code_repeat_episodes = sum(count - 1 for count in code_counts.values())
        (
            project,
            worktree_id,
            session_id,
            source_stream_id,
            prompt_index,
            module,
        ) = key
        details.append(
            {
                "project": project,
                "worktree_id": worktree_id,
                "session_id": session_id,
                "source_stream_id": source_stream_id,
                "prompt_index": prompt_index,
                "module_anchor": module,
                "test_artifacts": len(test_counts),
                "code_artifacts": len(code_counts),
                "test_mutation_episodes": len(test_rows),
                "code_mutation_episodes": len(code_rows),
                "test_to_code_episode_ratio": (
                    len(test_rows) / len(code_rows) if code_rows else ""
                ),
                "code_zero": not code_rows,
                "test_repeat_episodes_within_block": test_repeat_episodes,
                "code_repeat_episodes_within_block": code_repeat_episodes,
                "repeated_test_identities_within_block": (
                    repeated_test_identities
                ),
                "repeated_code_identities_within_block": (
                    repeated_code_identities
                ),
                "repeat_test_with_code_zero": (
                    repeated_test_identities > 0 and not code_rows
                ),
            }
        )
    details.sort(
        key=lambda row: (
            PROJECT_ORDER.index(str(row["project"])),
            str(row["worktree_id"]),
            str(row["session_id"]),
            str(row["source_stream_id"]),
            int(row["prompt_index"]),
            str(row["module_anchor"]),
        )
    )

    summaries: list[dict[str, Any]] = []
    for project in (*PROJECT_ORDER, "ALL_POOLED"):
        rows = [
            row
            for row in details
            if project == "ALL_POOLED" or row["project"] == project
        ]
        repeat_rows = [
            row
            for row in rows
            if int(row["repeated_test_identities_within_block"]) > 0
        ]
        code_in_repeat = [
            int(row["code_mutation_episodes"]) for row in repeat_rows
        ]
        repeat_ratios = [
            int(row["test_mutation_episodes"])
            / int(row["code_mutation_episodes"])
            for row in repeat_rows
            if int(row["code_mutation_episodes"]) > 0
        ]
        summaries.append(
            {
                "project": project,
                "test_bearing_blocks": len(rows),
                "code_zero_blocks": sum(bool(row["code_zero"]) for row in rows),
                "code_zero_block_fraction": fraction(
                    sum(bool(row["code_zero"]) for row in rows), len(rows)
                ),
                "repeat_test_blocks": len(repeat_rows),
                "repeat_test_code_zero_blocks": sum(
                    bool(row["repeat_test_with_code_zero"]) for row in rows
                ),
                "repeat_test_gt_code_blocks": sum(
                    int(row["test_mutation_episodes"])
                    > int(row["code_mutation_episodes"])
                    for row in repeat_rows
                ),
                "max_test_to_code_ratio_in_repeat_test_blocks": (
                    max(repeat_ratios) if repeat_ratios else ""
                ),
                "test_gt_code_episode_blocks": sum(
                    int(row["test_mutation_episodes"])
                    > int(row["code_mutation_episodes"])
                    for row in rows
                ),
                "test_mutation_episodes": sum(
                    int(row["test_mutation_episodes"]) for row in rows
                ),
                "code_mutation_episodes": sum(
                    int(row["code_mutation_episodes"]) for row in rows
                ),
                "median_code_episodes_in_repeat_test_blocks": (
                    statistics.median(code_in_repeat) if code_in_repeat else ""
                ),
            }
        )
    return details, summaries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    self_test_classification()

    projects_payload = read_json(args.input / "projects.json")
    if not isinstance(projects_payload, list):
        raise TypeError("projects.json must be a list")
    project_names = tuple(row["project"] for row in projects_payload)
    if project_names != PROJECT_ORDER:
        raise ValueError(f"unexpected project order/set: {project_names}")

    artifacts_path = args.input / "rq1-artifacts.csv"
    mutations_path = args.input / "rq1-mutations.csv"
    projects_path = args.input / "projects.json"
    artifacts = read_csv(artifacts_path)
    mutations = read_csv(mutations_path)
    if len(artifacts) != 5_746:
        raise ValueError(f"unexpected artifact count: {len(artifacts)}")
    if len(mutations) != 13_906:
        raise ValueError(f"unexpected mutation-row count: {len(mutations)}")

    artifact_details, artifact_summary = artifact_analysis(artifacts)
    (
        allocation,
        comparisons,
        event_checks_and_hashes,
        event_metadata,
        classification_audit,
    ) = action_allocation(args.input, projects_payload)
    mutation_episodes = collapse_mutations(mutations, event_metadata)
    if len(mutation_episodes) != 13_860:
        raise ValueError(
            f"unexpected artifact-mutation episode count: "
            f"{len(mutation_episodes)}"
        )
    if sum(int(row["raw_mutation_rows"]) for row in mutation_episodes) != len(
        mutations
    ):
        raise ValueError("collapsed mutation episodes do not reconcile to rows")
    order_details, order_summary = test_code_order_analysis(
        mutation_episodes
    )
    if any(
        not str(row["test_paths"]) or not str(row["code_paths"])
        for row in order_details
    ):
        raise ValueError("paired test/code episode lacks auditable paths")
    churn = churn_analysis(mutation_episodes)
    paired_churn_details, paired_churn_summary = paired_churn_analysis(
        mutation_episodes
    )

    write_csv(
        args.output / "a-created-artifacts.csv",
        artifact_details,
        [
            "project",
            "worktree_id",
            "artifact_id",
            "first_path",
            "final_path",
            "artifact_type",
            "final_artifact_type",
            "renamed_across_type",
            "first_event_index",
            "last_event_index",
            "any_revisit",
            "never_revisited",
            "later_read",
            "later_read_count",
            "mutation_count",
        ],
    )
    write_csv(
        args.output / "a-created-revisit-summary.csv",
        artifact_summary,
        [
            "project",
            "artifact_type",
            "created_artifacts",
            "revisited_artifacts",
            "never_revisited_artifacts",
            "never_revisited_fraction",
            "later_read_artifacts",
            "later_read_fraction",
        ],
    )
    write_csv(
        args.output / "b-module-session-episodes.csv",
        order_details,
        [
            "project",
            "worktree_id",
            "session_id",
            "source_stream_id",
            "prompt_index",
            "module_anchor",
            "pairing_method",
            "pair_key",
            "test_paths",
            "code_paths",
            "order",
            "first_test_event_index",
            "first_code_event_index",
            "test_artifacts",
            "code_artifacts",
            "test_mutation_episodes",
            "code_mutation_episodes",
        ],
    )
    write_csv(
        args.output / "b-order-summary.csv",
        order_summary,
        [
            "project",
            "eligible_paired_episodes",
            "basename_pair_episodes",
            "same_event_module_fallback_episodes",
            "test_first",
            "test_first_fraction",
            "code_first",
            "code_first_fraction",
            "tied_same_tool_event",
            "tied_fraction",
        ],
    )
    write_csv(
        args.output / "c-action-allocation.csv",
        allocation,
        [
            "status_basis",
            "project",
            "action_mode",
            "artifact_type",
            "actions",
            "share_within_project_mode",
            "project_mode_total",
        ],
    )
    write_csv(
        args.output / "c-paper-vs-code.csv",
        comparisons,
        [
            "status_basis",
            "project",
            "action_mode",
            "paper_docs_actions",
            "code_actions",
            "paper_docs_share",
            "code_share",
            "larger_category",
            "paper_docs_to_code_ratio",
        ],
    )
    write_csv(
        args.output / "d-mutation-episodes.csv",
        mutation_episodes,
        [
            "project",
            "worktree_id",
            "artifact_id",
            "event_id",
            "event_index",
            "ts_ms",
            "session_id",
            "source_stream_id",
            "prompt_index",
            "path",
            "artifact_type",
            "module_anchor",
            "operations",
            "raw_mutation_rows",
            "artifact_episode_ordinal",
            "repeat_episode",
            "validation_outcome",
            "validation_associated",
        ],
    )
    write_csv(
        args.output / "d-churn-summary.csv",
        churn,
        [
            "project",
            "artifact_type",
            "mutated_artifacts",
            "mutation_episodes",
            "episodes_per_mutated_artifact",
            "repeat_episodes",
            "repeat_episode_fraction",
            "repeated_artifacts",
            "repeated_artifact_fraction",
            "validation_associated_episodes",
            "validation_association_fraction",
            "competing_supersede_episodes",
            "censored_end_episodes",
        ],
    )
    write_csv(
        args.output / "d-paired-test-blocks.csv",
        paired_churn_details,
        [
            "project",
            "worktree_id",
            "session_id",
            "source_stream_id",
            "prompt_index",
            "module_anchor",
            "test_artifacts",
            "code_artifacts",
            "test_mutation_episodes",
            "code_mutation_episodes",
            "test_to_code_episode_ratio",
            "code_zero",
            "test_repeat_episodes_within_block",
            "code_repeat_episodes_within_block",
            "repeated_test_identities_within_block",
            "repeated_code_identities_within_block",
            "repeat_test_with_code_zero",
        ],
    )
    write_csv(
        args.output / "d-paired-test-block-summary.csv",
        paired_churn_summary,
        [
            "project",
            "test_bearing_blocks",
            "code_zero_blocks",
            "code_zero_block_fraction",
            "repeat_test_blocks",
            "repeat_test_code_zero_blocks",
            "repeat_test_gt_code_blocks",
            "max_test_to_code_ratio_in_repeat_test_blocks",
            "test_gt_code_episode_blocks",
            "test_mutation_episodes",
            "code_mutation_episodes",
            "median_code_episodes_in_repeat_test_blocks",
        ],
    )
    write_csv(
        args.output / "classification-audit.csv",
        classification_audit,
        [
            "project",
            "path",
            "audit_reason",
            "assigned_type",
            "ok_plus_observed_actions",
        ],
    )

    provenance_rows = [
        {
            "input": str(projects_path),
            "sha256": sha256(projects_path),
            "bytes": projects_path.stat().st_size,
        },
        {
            "input": str(artifacts_path),
            "sha256": sha256(artifacts_path),
            "bytes": artifacts_path.stat().st_size,
        },
        {
            "input": str(mutations_path),
            "sha256": sha256(mutations_path),
            "bytes": mutations_path.stat().st_size,
        },
    ]
    provenance_rows.extend(
        row for row in event_checks_and_hashes if "input" in row
    )
    write_csv(
        args.output / "input-provenance.csv",
        provenance_rows,
        ["input", "sha256", "bytes"],
    )
    write_csv(
        args.output / "reconciliation.csv",
        (row for row in event_checks_and_hashes if "project" in row),
        [
            "project",
            "tool_events",
            "ok_nonscope_read_write_actions",
            "observed_nonscope_read_write_actions",
            "ok_plus_observed_nonscope_read_write_actions",
            "excluded_ok_rename_from_helpers",
            "excluded_observed_rename_from_helpers",
        ],
    )

    print(
        json.dumps(
            {
                "projects": len(projects_payload),
                "created_artifacts": len(artifact_details),
                "raw_mutation_rows": len(mutations),
                "artifact_mutation_episodes": len(mutation_episodes),
                "eligible_test_code_paired_episodes": len(
                    order_details
                ),
                "test_bearing_prompt_module_blocks": len(
                    paired_churn_details
                ),
                "output": str(args.output),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
