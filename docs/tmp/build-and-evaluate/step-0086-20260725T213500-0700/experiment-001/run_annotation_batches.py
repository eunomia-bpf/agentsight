#!/usr/bin/env python3
"""Run the fixed Codex annotation backend over deterministic batch workspaces."""

from __future__ import annotations

import concurrent.futures
import json
import subprocess
import sys
import time
from pathlib import Path


EXPERIMENT = Path(__file__).resolve().parent
MANIFEST = EXPERIMENT / "annotation-pass" / "batch-manifest.json"
RECORDS = EXPERIMENT / "annotation-pass" / "run-records.jsonl"
FIXED_INSTRUCTION = (
    EXPERIMENT.parent.parent
    / "step-0077-20260723T233616-0700"
    / "experiment-001"
    / "automatic-backend-instruction.md"
)
AGENTPPROF = EXPERIMENT / "cargo-target" / "release" / "agentpprof"
MODEL = "gpt-5.6-sol"
WORKERS = 3


APPENDIX = """

Batch execution instruction: Complete the first and only annotation pass for
this entire one-session batch workspace. Read trace.jsonl in bounded chunks as
needed. Edit only annotation.json. Do not edit trace.jsonl or stacks.folded, do
not create any other file, and never run Git. Do not stop until every session
root and prompt has a meaningful mandatory annotation and every source-grounded
responsibility change that improves the profile has a nested noncrossing
annotation. The orchestrator will run AgentPProf validation after you finish.
"""


def completed_batches() -> set[int]:
    if not RECORDS.exists():
        return set()
    completed = set()
    for line in RECORDS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("status") == "ok":
            completed.add(int(row["batch"]))
    return completed


def run_batch(row: dict) -> dict:
    batch = int(row["batch"])
    workspace = EXPERIMENT / row["workspace"]
    annotation = workspace / "annotation.json"
    trace = workspace / "trace.jsonl"
    folded = workspace / "stacks.folded"
    validation_profile = workspace.parent / "validation.pb.gz"
    before_trace = trace.read_bytes()
    before_folded = folded.read_bytes()
    if json.loads(annotation.read_text(encoding="utf-8")):
        raise ValueError(f"batch {batch:03d} annotation is already nonempty")

    prompt = FIXED_INSTRUCTION.read_text(encoding="utf-8") + APPENDIX
    command = [
        "codex",
        "exec",
        "--model",
        MODEL,
        "--sandbox",
        "workspace-write",
        "--ephemeral",
        "--json",
        "--color",
        "never",
        "-C",
        str(workspace),
        "-",
    ]
    started = time.monotonic()
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )
    assert process.stdin is not None
    assert process.stdout is not None
    process.stdin.write(prompt)
    process.stdin.close()
    usage = None
    thread_id = None
    final_message = ""
    non_json_tail: list[str] = []
    for line in process.stdout:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            non_json_tail.append(line.strip())
            non_json_tail = non_json_tail[-5:]
            continue
        if event.get("type") == "thread.started":
            thread_id = event.get("thread_id")
        if event.get("type") == "turn.completed":
            usage = event.get("usage")
        item = event.get("item")
        if (
            event.get("type") == "item.completed"
            and isinstance(item, dict)
            and item.get("type") == "agent_message"
        ):
            final_message = item.get("text", "")
    return_code = process.wait()
    backend_wall = time.monotonic() - started
    if return_code != 0:
        raise RuntimeError(
            f"batch {batch:03d} backend failed with {return_code}: {non_json_tail}"
        )
    if usage is None:
        raise RuntimeError(f"batch {batch:03d} backend returned no usage counters")
    if trace.read_bytes() != before_trace or folded.read_bytes() != before_folded:
        raise RuntimeError(
            f"batch {batch:03d} backend changed trace.jsonl or stacks.folded"
        )
    unexpected = sorted(
        path.name
        for path in workspace.iterdir()
        if path.name not in {"trace.jsonl", "annotation.json", "stacks.folded"}
    )
    if unexpected:
        raise RuntimeError(
            f"batch {batch:03d} backend created unexpected files: {unexpected}"
        )

    annotations = json.loads(annotation.read_text(encoding="utf-8"))
    if not isinstance(annotations, dict) or not annotations:
        raise RuntimeError(f"batch {batch:03d} backend left annotation empty")

    validation_started = time.monotonic()
    validation = subprocess.run(
        [
            str(AGENTPPROF),
            "--annotation-file",
            str(annotation),
            "--view",
            "operations",
            "--deterministic-output",
            "--output",
            str(validation_profile),
        ],
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    validation_wall = time.monotonic() - validation_started
    if validation.returncode != 0:
        raise RuntimeError(
            f"batch {batch:03d} validation failed: {validation.stderr.strip()}"
        )
    validation_status = json.loads(validation.stdout)
    return {
        "batch": batch,
        "status": "ok",
        "model": MODEL,
        "worker_pattern": f"{WORKERS} parallel isolated one-session workers",
        "thread_id": thread_id,
        "backend_wall_seconds": round(backend_wall, 6),
        "validation_wall_seconds": round(validation_wall, 6),
        "usage": usage,
        "annotations": validation_status["annotations"],
        "nodes": validation_status["nodes"],
        "operation_mass": validation_status["samples"],
        "min_semantic_depth": validation_status["min_semantic_depth"],
        "max_semantic_depth": validation_status["max_semantic_depth"],
        "warning_count": len(validation_status["warnings"]),
        "issue_count": len(validation_status["issues"]),
        "final_message": final_message,
    }


def main() -> None:
    if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] != "resume"):
        raise SystemExit("usage: run_annotation_batches.py [resume]")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    done = completed_batches()
    pending = [row for row in manifest["batches"] if int(row["batch"]) not in done]
    print(
        json.dumps(
            {
                "status": "starting",
                "workers": WORKERS,
                "completed": len(done),
                "pending": len(pending),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    if not pending:
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(run_batch, row): row for row in pending}
        for future in concurrent.futures.as_completed(futures):
            row = futures[future]
            batch = int(row["batch"])
            try:
                result = future.result()
            except Exception as error:
                print(
                    json.dumps(
                        {"batch": batch, "status": "failed", "error": str(error)},
                        sort_keys=True,
                    ),
                    flush=True,
                )
                for other in futures:
                    other.cancel()
                raise
            with RECORDS.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(result, sort_keys=True) + "\n")
            print(
                json.dumps(
                    {
                        "batch": batch,
                        "status": "ok",
                        "backend_wall_seconds": result["backend_wall_seconds"],
                        "input_tokens": result["usage"].get("input_tokens"),
                        "output_tokens": result["usage"].get("output_tokens"),
                        "annotations": result["annotations"],
                        "max_semantic_depth": result["max_semantic_depth"],
                        "warnings": result["warning_count"],
                    },
                    sort_keys=True,
                ),
                flush=True,
            )


if __name__ == "__main__":
    main()
