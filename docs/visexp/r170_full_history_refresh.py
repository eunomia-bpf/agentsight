#!/usr/bin/env python3
"""Summarize a refreshed full-history AgentFlame run without leaking trace paths."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_AGENTFLAME_DIR = REPO_ROOT / ".agentsight" / "agentflame" / "r170-full-current"
DEFAULT_BASELINE_DIR = REPO_ROOT / ".agentsight" / "agentflame" / "latest"
DEFAULT_OUT_JSON = SCRIPT_DIR / "out" / "full-history-r170.json"
DEFAULT_OUT_MD = SCRIPT_DIR / "out" / "full-history-r170.md"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_folded_total(path: Path) -> dict[str, int]:
    unique = 0
    total = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line:
                continue
            stack, _, weight = line.rpartition(" ")
            if not stack or not weight.isdigit():
                raise AssertionError(f"invalid folded line in {path}: {line[:120]}")
            unique += 1
            total += int(weight)
    return {"unique_stacks": unique, "total_weight": total}


def tags_count(path: Path) -> int:
    if not path.exists():
        return 0
    payload = read_json(path)
    tags = payload.get("tags") if isinstance(payload, dict) else None
    return len(tags or {})


def counter_summary(report: dict[str, Any], name: str, folded: dict[str, int]) -> dict[str, Any]:
    summary = (report.get("summary") or {}).get(name) or {}
    expected_total = summary.get("total_weight")
    expected_unique = summary.get("unique_stacks")
    matches = expected_total == folded["total_weight"] and expected_unique == folded["unique_stacks"]
    return {
        "report_unique_stacks": expected_unique,
        "report_total_weight": expected_total,
        "folded_unique_stacks": folded["unique_stacks"],
        "folded_total_weight": folded["total_weight"],
        "matches_folded": matches,
    }


def build_summary(agentflame_dir: Path, baseline_dir: Path) -> dict[str, Any]:
    report_path = agentflame_dir / "agentflame.json"
    tags_path = agentflame_dir / "tags.json"
    if not report_path.exists():
        raise AssertionError(f"missing AgentFlame report: {report_path}")
    report = read_json(report_path)
    summary = report.get("summary") or {}
    llm_tagger = report.get("llm_tagger") or {}
    folded = {
        "semantic_system": read_folded_total(agentflame_dir / "semantic-system.folded.txt"),
        "nonsemantic_system": read_folded_total(agentflame_dir / "nonsemantic-system.folded.txt"),
        "semantic_token": read_folded_total(agentflame_dir / "semantic-token.folded.txt"),
    }
    integrity = {
        "semantic_system": counter_summary(report, "system", folded["semantic_system"]),
        "nonsemantic_system": counter_summary(report, "nonsemantic_system", folded["nonsemantic_system"]),
        "semantic_token": counter_summary(report, "token", folded["semantic_token"]),
    }
    all_folded_match = all(row["matches_folded"] for row in integrity.values())
    failures = llm_tagger.get("failures") or []
    tag_counts = {
        "seed_cache_tags": tags_count(baseline_dir / "tags.json"),
        "final_cache_tags": tags_count(tags_path),
    }
    tag_counts["new_cache_entries"] = tag_counts["final_cache_tags"] - tag_counts["seed_cache_tags"]
    status = "full_history_refresh_passed" if all_folded_match and not failures else "full_history_refresh_failed"
    return {
        "schema_version": 1,
        "run_id": "R170",
        "claim": "C1,C2,C3,C7 mechanism/artifact refresh",
        "status": status,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source_command": (
            "cargo run --manifest-path agentflame/Cargo.toml -- run --project-root . "
            "--scan-files 10000 --max-sessions 10000 --llama-url http://127.0.0.1:18080 "
            "--model local-r170 --timeout 60 --out .agentsight/agentflame/r170-full-current"
        ),
        "agentflame_artifacts": {
            "dir": rel(agentflame_dir),
            "report": rel(report_path),
            "report_sha256": file_sha256(report_path),
            "tags": rel(tags_path),
            "tags_sha256": file_sha256(tags_path),
        },
        "input_scope": {
            "scan_files": (report.get("inputs") or {}).get("scan_files"),
            "max_sessions": (report.get("inputs") or {}).get("max_sessions"),
            "tag_llm_calls": (report.get("inputs") or {}).get("tag_llm_calls"),
            "session_file_mode": bool((report.get("inputs") or {}).get("session_files")),
            "absolute_trace_roots_redacted": True,
            "raw_trace_policy": "read-only local input; raw trace files are not copied into committed artifacts",
        },
        "summary": {
            "report_generated_at": report.get("generated_at"),
            "session_count": summary.get("session_count"),
            "source_counts": summary.get("source_counts"),
            "raw_tool_events": summary.get("raw_tool_events"),
            "raw_llm_events": summary.get("raw_llm_events"),
            "system_observations": (summary.get("system") or {}).get("total_weight"),
            "semantic_system_stacks": (summary.get("system") or {}).get("unique_stacks"),
            "nonsemantic_system_stacks": (summary.get("nonsemantic_system") or {}).get("unique_stacks"),
            "semantic_system_compression": (summary.get("system") or {}).get("compression_ratio"),
            "nonsemantic_system_compression": (summary.get("nonsemantic_system") or {}).get("compression_ratio"),
            "semantic_mixing": {
                "nonsemantic_mixed_weight_pct": ((summary.get("semantic_mixing") or {}).get("nonsemantic") or {}).get("mixed_weight_pct"),
                "flat_mixed_weight_pct": ((summary.get("semantic_mixing") or {}).get("flat") or {}).get("mixed_weight_pct"),
            },
        },
        "llm_tagger": {
            "requests": llm_tagger.get("requests"),
            "cache_hits": llm_tagger.get("cache_hits"),
            "llm_calls": llm_tagger.get("llm_calls"),
            "llm_successes": llm_tagger.get("llm_successes"),
            "failure_count": len(failures),
            "cache_seed": rel(baseline_dir / "tags.json"),
            **tag_counts,
        },
        "integrity": {
            "all_folded_totals_match_report": all_folded_match,
            "folded": integrity,
            "warning_count": len(report.get("warnings") or []),
            "warnings_redacted": True,
        },
        "claim_boundary": (
            "R170 refreshes the current full-history AgentFlame annotation path with a real "
            "llama.cpp-compatible server and a seeded local tag cache. It strengthens mechanism "
            "and artifact reproducibility evidence only; it does not provide human tag adequacy, "
            "developer utility, broad exact lineage, or community adoption evidence."
        ),
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": file_sha256(Path(__file__).resolve()),
        },
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    llm = payload["llm_tagger"]
    integrity = payload["integrity"]
    lines = [
        "# R170 Full-History Refresh",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Scope",
        "",
        f"- Sessions: {summary.get('session_count')}.",
        f"- Source counts: `{summary.get('source_counts')}`.",
        f"- Raw tool events: {summary.get('raw_tool_events')}.",
        f"- Raw LLM events: {summary.get('raw_llm_events')}.",
        f"- System observations: {summary.get('system_observations')}.",
        "",
        "## LLM Tagger",
        "",
        f"- Requests: {llm.get('requests')}.",
        f"- Cache hits: {llm.get('cache_hits')}.",
        f"- New llama.cpp calls: {llm.get('llm_calls')}.",
        f"- Failures: {llm.get('failure_count')}.",
        f"- Cache entries: {llm.get('seed_cache_tags')} -> {llm.get('final_cache_tags')}.",
        "",
        "## Integrity",
        "",
        f"- Folded totals match report: {integrity.get('all_folded_totals_match_report')}.",
        f"- Warning count: {integrity.get('warning_count')} (details redacted).",
        "",
        "## Claim Boundary",
        "",
        payload["claim_boundary"],
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    payload = build_summary(args.agentflame_dir, args.baseline_dir)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(args.out_md, payload)
    print(json.dumps({"status": payload["status"], **payload["summary"], "llm_calls": payload["llm_tagger"]["llm_calls"]}, indent=2))
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agentflame-dir", type=Path, default=DEFAULT_AGENTFLAME_DIR)
    parser.add_argument("--baseline-dir", type=Path, default=DEFAULT_BASELINE_DIR)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
