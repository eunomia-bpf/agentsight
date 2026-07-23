#!/usr/bin/env python3
"""Materialize an outcome-blind AgentPProf workspace from AgentRewardBench.

This source adapter never opens AgentRewardBench's annotation CSV.  It accepts
only a precomputed list of eligible source-session IDs, locates the corresponding
released cleaned trajectories, and emits the shared three-file workspace.  The
initial annotation contains only deterministic session/prompt coverage; an
Agent or another backend refines it in place.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Iterable


ACTION_RE = re.compile(r"^\s*([A-Za-z_][\w.]*)\s*\(")
TARGET_LABELS = {
    "successful",
    "unsuccessful",
    "complete failure",
    "suboptimal",
    "somewhat optimal",
    "yes",
    "no",
}
PROMPT_OPERATIONS = {
    "assistantbench": "answer information request",
    "webarena": "execute website task",
    "workarena": "execute enterprise workflow",
    "visualwebarena": "execute visual task",
}
MAX_PROJECTION_WORKERS = 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path)
    parser.add_argument("--session-list", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--project-source", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.project_source is None:
        missing = [
            flag
            for flag, value in (
                ("--dataset-root", args.dataset_root),
                ("--session-list", args.session_list),
                ("--out", args.out),
            )
            if value is None
        ]
        if missing:
            parser.error(f"the following arguments are required: {', '.join(missing)}")
    return args


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def clean_text(value: Any, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def sanitize_slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    return value[:120] or "unknown"


def source_session_id(benchmark: str, task_id: str, model: str) -> str:
    return "__".join(sanitize_slug(part) for part in (benchmark, task_id, model))


def load_session_list(path: Path) -> list[str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    values = raw["sessions"] if isinstance(raw, dict) else raw
    require(isinstance(values, list), "session list must be an array or {sessions: [...]}")
    sessions = [str(value) for value in values]
    require(bool(sessions), "session list is empty")
    require(len(sessions) == len(set(sessions)), "session list contains duplicates")
    return sorted(sessions)


def index_sources(cleaned: Path) -> dict[str, tuple[str, str, Path]]:
    sources: dict[str, tuple[str, str, Path]] = {}
    for path in sorted(cleaned.glob("*/*/*/*.json")):
        benchmark = path.relative_to(cleaned).parts[0]
        model = path.relative_to(cleaned).parts[1]
        task_id = path.stem
        session = source_session_id(benchmark, task_id, model)
        require(session not in sources, f"duplicate source-session identity: {session}")
        sources[session] = (benchmark, model, path)
    return sources


def action_name(raw_action: Any) -> str:
    text = str(raw_action or "").strip()
    match = ACTION_RE.match(text)
    return match.group(1).rsplit(".", 1)[-1] if match else "unknown"


def project_source(path: Path) -> dict[str, Any]:
    try:
        import orjson

        source = orjson.loads(path.read_bytes())
    except ImportError:
        source = json.loads(path.read_text(encoding="utf-8"))
    return {
        "goal": clean_text(source.get("goal"), 600),
        "steps": [
            {
                "reasoning": clean_text(step.get("reasoning"), 1200),
                "action": clean_text(step.get("action"), 600),
                "url": clean_text(step.get("url"), 300),
                "axtree": clean_text(step.get("axtree"), 1200),
                "last_action_error": clean_text(
                    step.get("last_action_error"), 300
                ),
                "stats": step.get("stats") or {},
            }
            for step in source.get("steps") or []
            if str(step.get("action") or "").strip()
        ],
    }


def load_one_source_projection(path: Path) -> dict[str, Any]:
    run = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--project-source",
            str(path),
        ],
        check=False,
        capture_output=True,
    )
    require(
        run.returncode == 0,
        f"source projection worker failed for {path}: "
        f"{run.stderr.decode('utf-8', errors='replace')}",
    )
    projected = json.loads(run.stdout)
    require(isinstance(projected, dict), f"invalid source projection for {path}")
    return projected


def load_source_projections(paths: list[Path]) -> list[dict[str, Any]]:
    """Read only bounded model-visible fields in a fresh jq process.

    Some released accessibility trees are large enough that repeatedly
    materializing and freeing their full Python object graphs can exhaust the
    long-running adapter.  A bounded thread pool launches one isolated helper
    process per source and returns only the compact projection. Each helper
    exits after one file, so the allocator cannot retain the complete corpus.
    """

    require(bool(paths), "source projection list is empty")
    if len(paths) == 1:
        return [project_source(paths[0])]
    workers = min(MAX_PROJECTION_WORKERS, len(paths))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(load_one_source_projection, paths))


def load_source_projection(path: Path) -> dict[str, Any]:
    return project_source(path)


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as stream:
        for value in values:
            stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def annotation_input_matches(nodes: list[dict[str, Any]]) -> list[dict[str, str]]:
    matches = []
    for node in nodes:
        for key, value in node["data"].items():
            if isinstance(value, str) and value.strip().casefold() in TARGET_LABELS:
                matches.append(
                    {
                        "node": str(node["id"]),
                        "field": str(key),
                        "value": value.strip(),
                    }
                )
    return matches


def materialize(
    dataset_root: Path, sessions: list[str]
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str | None]], dict[str, Any]]:
    sources = index_sources(dataset_root / "cleaned")
    missing = [session for session in sessions if session not in sources]
    require(not missing, f"missing {len(missing)} source sessions; first: {missing[:3]}")

    nodes: list[dict[str, Any]] = []
    annotations: dict[str, dict[str, str | None]] = {}
    per_benchmark: dict[str, int] = {}
    operations = 0
    tokens = 0
    selected_sources = [(session, *sources[session]) for session in sessions]
    traces = load_source_projections([row[3] for row in selected_sources])

    for (session, benchmark, model, source), trace in zip(
        selected_sources, traces, strict=True
    ):
        goal = clean_text(trace.get("goal") or source.stem, 600)
        steps = [
            step
            for step in trace.get("steps") or []
            if str(step.get("action") or "").strip()
        ]
        per_benchmark[benchmark] = per_benchmark.get(benchmark, 0) + 1

        session_node = f"session:{session}"
        prompt_node = f"prompt:{session}"
        nodes.append(
            {
                "id": session_node,
                "parent": None,
                "kind": "session",
                "data": {
                    "agent": model,
                    "benchmark": benchmark,
                    "name": f"{benchmark} task",
                    "source_session": session,
                },
                "metrics": {},
                "path": [],
            }
        )
        nodes.append(
            {
                "id": prompt_node,
                "parent": session_node,
                "kind": "prompt",
                "data": {"name": "user request", "text": goal},
                "metrics": {},
                "path": [],
            }
        )
        annotations[session_node] = {
            "tag": "execute browser task",
            "parent": None,
            "next": None,
        }
        annotations[prompt_node] = {
            "tag": PROMPT_OPERATIONS.get(benchmark, "fulfill user request"),
            "parent": session_node,
            "next": None,
        }

        for index, step in enumerate(steps):
            evidence_id = f"{session}:step-{index:04d}"
            llm_id = f"llm:{evidence_id}"
            tool_id = f"tool:{evidence_id}"
            stats = step.get("stats") or {}
            step_tokens = int(stats.get("input_tokens") or 0) + int(
                stats.get("output_tokens") or 0
            )
            nodes.append(
                {
                    "id": llm_id,
                    "parent": prompt_node,
                    "kind": "llm",
                    "data": {
                        "name": f"step {index}",
                        "reasoning": clean_text(step.get("reasoning"), 1200),
                        "state_preview": clean_text(step.get("axtree"), 1200),
                        "url": clean_text(step.get("url"), 300),
                    },
                    "metrics": {"tokens": step_tokens} if step_tokens else {},
                    "path": [],
                }
            )
            nodes.append(
                {
                    "id": tool_id,
                    "parent": llm_id,
                    "kind": "tool",
                    "data": {
                        "action": clean_text(step.get("action"), 600),
                        "evidence_id": evidence_id,
                        "name": action_name(step.get("action")),
                        "visible_error": clean_text(step.get("last_action_error"), 300),
                    },
                    "metrics": {"operations": 1},
                    "path": [],
                }
            )
            operations += 1
            tokens += step_tokens

    return nodes, annotations, {
        "sessions": len(sessions),
        "operations": operations,
        "tokens": tokens,
        "by_benchmark": dict(sorted(per_benchmark.items())),
    }


def audit_markdown(
    dataset_root: Path,
    session_list: Path,
    summary: dict[str, Any],
    matches: list[dict[str, str]],
) -> str:
    match_lines = (
        "\n".join(
            f"- `{row['node']}` field `{row['field']}` has exact source value "
            f"`{row['value']}`. It is source-visible page/agent content, not an "
            "annotation-CSV value; reviewers must inspect it before accepting the backend input."
            for row in matches
        )
        if matches
        else "- No model-visible field exactly equals a registered expert-label string."
    )
    return f"""# AgentReward Annotation-Input Audit

## Source Boundary

- Dataset source: `{dataset_root}`
- Eligible source-only session list: `{session_list}`
- Sessions: {summary['sessions']}
- Operations: {summary['operations']}
- Provider-reported tokens: {summary['tokens']}
- Benchmark distribution: `{json.dumps(summary['by_benchmark'], sort_keys=True)}`

The materializer opens only the session list and released `cleaned/` trajectory
JSON. It does not open `data/annotations.csv`, a pair file, an evaluation
summary, or any previous pprof.

## Model-Visible Fields

- session: `agent`, `benchmark`, `name`, `source_session`
- prompt: `name`, `text`
- LLM: `name`, `reasoning`, `state_preview`, `url`
- tool: `action`, `evidence_id`, `name`, `visible_error`
- additive measurements: `operations`, `tokens`

The adapter omits `summary_info` wholesale. It never emits expert success,
looping, side-effect, or optimality labels; reward; pair membership; pair side;
pair identifiers; or any derived target verdict.

## Literal Expert-Label Scan

Registered exact strings/aliases:
`Successful`, `Unsuccessful`, `Complete Failure`, `Suboptimal`,
`Somewhat Optimal`, `Yes`, and `No`.

{match_lines}
"""


def main() -> None:
    args = parse_args()
    if args.project_source is not None:
        sys.stdout.buffer.write(
            json.dumps(
                project_source(args.project_source),
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        return
    sessions = load_session_list(args.session_list)
    nodes, annotations, summary = materialize(args.dataset_root, sessions)
    args.out.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out / "trace.jsonl", nodes)
    write_json(args.out / "annotation.json", annotations)
    matches = annotation_input_matches(nodes)
    audit_path = args.out.parent / f"{args.out.name}.input-audit.md"
    audit_path.write_text(
        audit_markdown(args.dataset_root, args.session_list, summary, matches),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                **summary,
                "trace_nodes": len(nodes),
                "seed_annotations": len(annotations),
                "exact_target_label_matches": len(matches),
                "input_audit": str(audit_path),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
