#!/usr/bin/env python3
"""Split the product-generated trace into deterministic one-session workspaces.

This is orchestration glue, not a session parser: it copies complete contiguous
TraceNode blocks from the product-generated workspace and later merges only the
backend-produced annotation objects.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


EXPERIMENT = Path(__file__).resolve().parent
SOURCE_TRACE = EXPERIMENT / "workspace" / "trace.jsonl"
PASS_ROOT = EXPERIMENT / "annotation-pass"
MANIFEST = PASS_ROOT / "batch-manifest.json"


def read_session_blocks() -> list[tuple[dict, list[str]]]:
    blocks: list[tuple[dict, list[str]]] = []
    current_root: dict | None = None
    current_lines: list[str] = []
    for line_number, line in enumerate(
        SOURCE_TRACE.read_text(encoding="utf-8").splitlines(keepends=True), 1
    ):
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("kind") == "session":
            if current_root is not None:
                blocks.append((current_root, current_lines))
            current_root = row
            current_lines = []
        if current_root is None:
            raise ValueError(f"trace node before first session at line {line_number}")
        current_lines.append(line if line.endswith("\n") else line + "\n")
    if current_root is not None:
        blocks.append((current_root, current_lines))
    return blocks


def prepare() -> None:
    if PASS_ROOT.exists():
        raise FileExistsError(f"refusing to overwrite {PASS_ROOT}")
    blocks = read_session_blocks()
    if len(blocks) != 42:
        raise ValueError(f"expected 42 session blocks, found {len(blocks)}")

    PASS_ROOT.mkdir(parents=True)
    manifest_rows = []
    for ordinal, (root, lines) in enumerate(blocks, 1):
        batch_dir = PASS_ROOT / f"batch-{ordinal:03d}"
        workspace = batch_dir / "workspace"
        workspace.mkdir(parents=True)
        (workspace / "trace.jsonl").write_text("".join(lines), encoding="utf-8")
        (workspace / "annotation.json").write_text("{}\n", encoding="utf-8")
        (workspace / "stacks.folded").write_text("", encoding="utf-8")

        parsed = [json.loads(line) for line in lines]
        kinds: dict[str, int] = {}
        operations = 0
        tokens = 0
        for row in parsed:
            kind = row["kind"]
            kinds[kind] = kinds.get(kind, 0) + 1
            operations += row.get("metrics", {}).get("operations", 0)
            tokens += row.get("metrics", {}).get("tokens", 0)
        manifest_rows.append(
            {
                "batch": ordinal,
                "workspace": str(workspace.relative_to(EXPERIMENT)),
                "session_node_id": root["id"],
                "agent": root.get("data", {}).get("agent", "unknown"),
                "source_session": root.get("data", {}).get(
                    "source_session", "unknown"
                ),
                "nodes": len(parsed),
                "node_kinds": kinds,
                "operations": operations,
                "tokens": tokens,
            }
        )

    MANIFEST.write_text(
        json.dumps(
            {
                "policy": "product-trace contiguous session blocks; one session per batch",
                "batches": manifest_rows,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "batches": len(manifest_rows),
                "nodes": sum(row["nodes"] for row in manifest_rows),
                "operations": sum(row["operations"] for row in manifest_rows),
                "tokens": sum(row["tokens"] for row in manifest_rows),
            },
            sort_keys=True,
        )
    )


def merge() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    merged: dict[str, dict] = {}
    for row in manifest["batches"]:
        annotation_path = EXPERIMENT / row["workspace"] / "annotation.json"
        annotations = json.loads(annotation_path.read_text(encoding="utf-8"))
        if not isinstance(annotations, dict) or not annotations:
            raise ValueError(f"empty or invalid annotation batch {annotation_path}")
        overlap = sorted(set(merged).intersection(annotations))
        if overlap:
            raise ValueError(
                f"duplicate annotation IDs across batches: {overlap[:3]}"
            )
        merged.update(annotations)

    output = EXPERIMENT / "workspace" / "annotation.json"
    output.write_text(
        json.dumps(merged, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "ok",
                "batches": len(manifest["batches"]),
                "annotations": len(merged),
                "output": str(output.relative_to(EXPERIMENT)),
            },
            sort_keys=True,
        )
    )


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"prepare", "merge"}:
        raise SystemExit("usage: prepare_annotation_batches.py prepare|merge")
    if sys.argv[1] == "prepare":
        prepare()
    else:
        merge()


if __name__ == "__main__":
    main()
