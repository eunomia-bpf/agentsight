#!/usr/bin/env python3
"""Verify the R160 AgentFlame artifact-usability smoke output.

This checker is intentionally read-only. It inspects a generated AgentFlame
output directory, confirms that the community-facing artifacts exist, and writes
a small JSON audit. It does not read or modify raw Codex/Claude trace files.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


REQUIRED_ARTIFACT_KEYS = {
    "dashboard",
    "tag_cache",
    "semantic_system_folded",
    "nonsemantic_system_folded",
    "system_flamegraph",
    "token_flamegraph",
    "prompt_system",
    "session_system",
    "llm_token",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_dirty_paths(repo_root: Path) -> list[str]:
    proc = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return [f"git_status_failed:{proc.stderr.strip()}"]
    return [line[3:] for line in proc.stdout.splitlines() if len(line) >= 4]


def folded_total(path: Path) -> int:
    total = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                total += int(line.rsplit(" ", 1)[1])
            except (IndexError, ValueError) as exc:
                raise AssertionError(f"invalid folded line in {path}: {line!r}") from exc
    return total


def redaction_summary(report: dict[str, Any]) -> dict[str, Any]:
    rows = report.get("prompt_tags") or []
    preview_count = sum(1 for row in rows if "preview" in row)
    non_redacted = [
        row.get("prompt_hash", "")
        for row in rows
        if row.get("preview") not in {None, "", "redacted"}
    ]
    return {
        "prompt_preview_rows": preview_count,
        "non_redacted_prompt_preview_count": len(non_redacted),
        "non_redacted_prompt_preview_hashes": non_redacted[:10],
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    agentflame_dir = Path(args.agentflame_dir).resolve()
    out_path = Path(args.out).resolve()
    if not agentflame_dir.exists():
        raise AssertionError(f"agentflame output directory does not exist: {agentflame_dir}")
    if not str(agentflame_dir).startswith(str(repo_root / ".agentsight" / "agentflame")):
        raise AssertionError("agentflame output must stay under .agentsight/agentflame for R160")

    report_path = agentflame_dir / "agentflame.json"
    tags_path = agentflame_dir / "tags.json"
    if not report_path.exists() or not tags_path.exists():
        raise AssertionError("agentflame.json and tags.json are required")

    report = read_json(report_path)
    artifacts = report.get("artifacts") or {}
    missing_keys = sorted(REQUIRED_ARTIFACT_KEYS - set(artifacts))
    missing_files = []
    for key in sorted(REQUIRED_ARTIFACT_KEYS & set(artifacts)):
        path = agentflame_dir / str(artifacts[key])
        if not path.exists():
            missing_files.append(str(path.relative_to(repo_root)))
    if missing_keys or missing_files:
        raise AssertionError(f"missing artifact keys={missing_keys} files={missing_files}")

    semantic_total = folded_total(agentflame_dir / str(artifacts["semantic_system_folded"]))
    nonsemantic_total = folded_total(agentflame_dir / str(artifacts["nonsemantic_system_folded"]))
    summary = report.get("summary") or {}
    expected_system = int((summary.get("system") or {}).get("total_weight") or 0)
    if semantic_total != expected_system or nonsemantic_total != expected_system:
        raise AssertionError(
            f"folded totals mismatch: semantic={semantic_total} nonsemantic={nonsemantic_total} expected={expected_system}"
        )

    redaction = redaction_summary(report)
    if redaction["non_redacted_prompt_preview_count"]:
        raise AssertionError("prompt previews are not fully redacted")

    dirty_paths = git_dirty_paths(repo_root)
    dirty_raw_trace_paths = [
        path
        for path in dirty_paths
        if ".codex/" in path or ".claude/" in path or path.endswith(".jsonl")
    ]
    if dirty_raw_trace_paths:
        raise AssertionError(f"raw trace-like paths are dirty in git status: {dirty_raw_trace_paths[:10]}")

    result = {
        "schema_version": 1,
        "run_id": "R160",
        "status": "artifact_usability_smoke_passed",
        "agentflame_dir": str(agentflame_dir.relative_to(repo_root)),
        "required_artifact_keys": sorted(REQUIRED_ARTIFACT_KEYS),
        "system_observations": expected_system,
        "semantic_system_total": semantic_total,
        "nonsemantic_system_total": nonsemantic_total,
        "session_count": summary.get("session_count"),
        "raw_tool_events": summary.get("raw_tool_events"),
        "raw_llm_events": summary.get("raw_llm_events"),
        "llm_tagger": report.get("llm_tagger") or {},
        "redaction": redaction,
        "dirty_path_count": len(dirty_paths),
        "dirty_raw_trace_path_count": len(dirty_raw_trace_paths),
        "claim_boundary": "R160 checks artifact usability and hygiene; it does not support C5 user utility or C6 tag adequacy.",
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "out": str(out_path)}, indent=2))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--agentflame-dir", required=True)
    parser.add_argument("--out", default="docs/visexp/out/artifact-usability-r160.json")
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
