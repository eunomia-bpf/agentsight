#!/usr/bin/env python3
"""Verify the R160 AgentFlame artifact-usability smoke output.

This checker is intentionally read-only. It inspects a generated AgentFlame
output directory, confirms that the community-facing artifacts exist, and writes
a small JSON audit. It does not read or modify raw Codex/Claude trace files.
"""

from __future__ import annotations

import argparse
import hashlib
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


def stable_hash(value: Any, length: int = 16) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]


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


def parse_optional_float(value: str | None, name: str) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except ValueError as exc:
        raise AssertionError(f"{name} must be a float, got {value!r}") from exc
    if parsed < 0:
        raise AssertionError(f"{name} must be non-negative")
    return parsed


def load_optional_report(path_arg: str | None) -> dict[str, Any] | None:
    if not path_arg:
        return None
    return read_json(Path(path_arg).resolve())


def tagger_summary(report: dict[str, Any] | None) -> dict[str, Any] | None:
    if report is None:
        return None
    tagger = report.get("llm_tagger") or {}
    return {
        "requests": int(tagger.get("requests") or 0),
        "cache_hits": int(tagger.get("cache_hits") or 0),
        "llm_calls": int(tagger.get("llm_calls") or 0),
        "llm_successes": int(tagger.get("llm_successes") or 0),
        "failure_count": len(tagger.get("failures") or []),
    }


def sanitized_input_manifest(report: dict[str, Any]) -> dict[str, Any]:
    sessions = []
    for row in report.get("sessions") or []:
        fingerprint_payload = {
            "source": row.get("source"),
            "session_file": row.get("session_file"),
            "session_id": row.get("session_id"),
            "prompt_count": row.get("prompt_count"),
            "tool_count": row.get("tool_count"),
            "llm_count": row.get("llm_count"),
            "cwd_hash": row.get("cwd_hash"),
        }
        sessions.append(
            {
                "fingerprint": stable_hash(fingerprint_payload),
                "source": row.get("source"),
                "prompt_count": row.get("prompt_count"),
                "tool_count": row.get("tool_count"),
                "llm_count": row.get("llm_count"),
                "cwd_hash": row.get("cwd_hash"),
            }
        )
    sessions.sort(key=lambda item: item["fingerprint"])
    inputs = report.get("inputs") or {}
    return {
        "manifest_schema": "r160-sanitized-input-v1",
        "manifest_hash": stable_hash(sessions, 24),
        "session_count": len(sessions),
        "scan_files": inputs.get("scan_files"),
        "max_sessions": inputs.get("max_sessions"),
        "tag_llm_calls": inputs.get("tag_llm_calls"),
        "session_fingerprints": sessions,
        "privacy": {
            "contains_raw_prompts": False,
            "contains_absolute_session_paths": False,
            "contains_session_filenames": False,
        },
    }


def local_report_privacy_summary(report: dict[str, Any]) -> dict[str, Any]:
    inputs = report.get("inputs") or {}
    sessions = report.get("sessions") or []
    roots = [str(inputs.get("codex_root") or ""), str(inputs.get("claude_root") or "")]
    session_files = [str(path) for path in inputs.get("session_files") or []]
    session_file_names = [str(row.get("session_file") or "") for row in sessions]
    has_absolute_roots = any(path.startswith("/") for path in roots if path)
    has_absolute_session_inputs = any(path.startswith("/") for path in session_files if path)
    return {
        "local_agentflame_json_public_release_ready": False,
        "contains_absolute_trace_roots": has_absolute_roots,
        "contains_absolute_session_inputs": has_absolute_session_inputs,
        "session_file_name_count": sum(1 for path in session_file_names if path),
        "boundary": ".agentsight/agentflame/*/agentflame.json is a local/private report; commit the R160 audit JSON, not raw local reports.",
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
    clean_report = load_optional_report(args.clean_agentflame_json)
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

    clean_tagger = tagger_summary(clean_report)
    cached_tagger = tagger_summary(report)
    clean_manifest = sanitized_input_manifest(clean_report) if clean_report else None
    cached_manifest = sanitized_input_manifest(report)
    input_equality = {
        "checked": clean_manifest is not None,
        "clean_manifest_hash": clean_manifest["manifest_hash"] if clean_manifest else None,
        "cached_manifest_hash": cached_manifest["manifest_hash"],
        "matches": clean_manifest == cached_manifest if clean_manifest else None,
    }
    if clean_manifest is not None and clean_manifest != cached_manifest:
        raise AssertionError(f"clean/cached input manifests differ: {input_equality}")
    if clean_tagger is not None:
        if clean_tagger["requests"] <= 0 or clean_tagger["llm_calls"] <= 0:
            raise AssertionError(f"clean run did not record uncached LLM work: {clean_tagger}")
        if clean_tagger["failure_count"]:
            raise AssertionError(f"clean run recorded tag failures: {clean_tagger}")
    if cached_tagger is not None and args.require_cached_rerun:
        if cached_tagger["requests"] <= 0:
            raise AssertionError("cached rerun did not record tag requests")
        if cached_tagger["llm_calls"] != 0:
            raise AssertionError(f"cached rerun made uncached LLM calls: {cached_tagger}")
        if cached_tagger["cache_hits"] != cached_tagger["requests"]:
            raise AssertionError(f"cached rerun was not fully cached: {cached_tagger}")

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
        "input_manifest": cached_manifest,
        "clean_cached_input_equality": input_equality,
        "local_report_privacy": local_report_privacy_summary(report),
        "run_metadata": {
            "scope": args.scope,
            "clean_command": args.clean_command,
            "cached_command": args.cached_command,
            "clean_runtime_seconds": parse_optional_float(
                args.clean_runtime_seconds, "clean_runtime_seconds"
            ),
            "cached_runtime_seconds": parse_optional_float(
                args.cached_runtime_seconds, "cached_runtime_seconds"
            ),
            "clean_agentflame_json": str(Path(args.clean_agentflame_json).resolve().relative_to(repo_root))
            if args.clean_agentflame_json
            else None,
            "require_cached_rerun": args.require_cached_rerun,
        },
        "clean_llm_tagger": clean_tagger,
        "cached_llm_tagger": cached_tagger,
        "redaction": redaction,
        "dirty_path_count": len(dirty_paths),
        "dirty_raw_trace_path_count": len(dirty_raw_trace_paths),
        "write_scope_boundary": "R160 checks output-directory containment for the report path and raw-trace git hygiene; it is not a full pre/post write-set audit.",
        "claim_boundary": "R160 checks bounded artifact usability, fixed-input cacheability, and hygiene; it does not support C5 user utility, C6 tag adequacy, fresh-clone installation, or full write-set containment.",
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
    parser.add_argument("--scope", default="bounded real local-history smoke")
    parser.add_argument("--clean-command")
    parser.add_argument("--cached-command")
    parser.add_argument("--clean-runtime-seconds")
    parser.add_argument("--cached-runtime-seconds")
    parser.add_argument("--clean-agentflame-json")
    parser.add_argument(
        "--require-cached-rerun",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require the final report to show all tag requests served from tags.json.",
    )
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
