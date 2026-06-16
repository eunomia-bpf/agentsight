#!/usr/bin/env python3
"""R202: llama.cpp smoke for R196 long-tail regeneration candidates.

This script reads generated AgentFlame/R189 artifacts only. It starts or uses a
llama.cpp-compatible server, asks R196 to regenerate one-word candidate labels
for generic/noisy long-tail rows, and writes a bounded audit summary. Regenerated
tags are proposals only: raw tags are preserved and no canonical map is updated.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_AGENTFLAME_DIR = REPO_ROOT / ".agentsight" / "agentflame" / "r170-full-current"
DEFAULT_R189_DIR = SCRIPT_DIR / "out" / "tag-consolidation-r189"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "long-tail-regeneration-r202"
DEFAULT_LOCAL_RUN_ROOT = REPO_ROOT / ".agentsight" / "agentflame"

sys.path.insert(0, str(SCRIPT_DIR))
import r196_long_tail_governance as r196  # noqa: E402
import r200_community_smoke as r200  # noqa: E402


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def git(args: list[str]) -> str | None:
    try:
        import subprocess

        return subprocess.check_output(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sanitized_llama_info(info: dict[str, Any], out_dir: Path, local_run_dir: Path) -> dict[str, Any]:
    replacements = [
        (str(REPO_ROOT.resolve()), "<repo>"),
        (str(out_dir.resolve()), "<out>"),
        (str(local_run_dir.resolve()), "<local-run>"),
        (str(Path.home()), "~"),
    ]
    return r200.sanitize_value(info, replacements)


def read_attempted_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            attempted = (
                row.get("regenerated_tag")
                or row.get("regeneration_error")
                or row.get("regenerated_valid") in {"True", "False"}
            )
            if attempted:
                rows.append(row)
    return rows


def summarize_attempts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid_rows = [row for row in rows if row.get("regenerated_valid") == "True"]
    invalid_rows = [row for row in rows if row.get("regenerated_valid") != "True"]
    changed_rows = [
        row
        for row in valid_rows
        if row.get("regenerated_tag") and row.get("regenerated_tag") != row.get("raw_tag")
    ]
    unchanged_rows = [
        row
        for row in valid_rows
        if row.get("regenerated_tag") and row.get("regenerated_tag") == row.get("raw_tag")
    ]
    by_dimension = Counter(str(row.get("dimension", "")) for row in rows)
    by_action = Counter(str(row.get("governance_action", "")) for row in rows)
    by_generated = Counter(str(row.get("regenerated_tag", "")) for row in valid_rows)
    invalid_errors = Counter(str(row.get("regeneration_error", "")) for row in invalid_rows)
    return {
        "attempted_rows": len(rows),
        "valid_rows": len(valid_rows),
        "invalid_rows": len(invalid_rows),
        "changed_valid_rows": len(changed_rows),
        "unchanged_valid_rows": len(unchanged_rows),
        "unique_valid_regenerated_tags": len(by_generated),
        "by_dimension": dict(sorted(by_dimension.items())),
        "by_governance_action": dict(sorted(by_action.items())),
        "top_regenerated_tags": by_generated.most_common(20),
        "invalid_error_samples": invalid_errors.most_common(8),
    }


def status_for(r196_payload: dict[str, Any], attempt_summary: dict[str, Any]) -> str:
    regeneration = r196_payload.get("summary", {}).get("regeneration", {})
    if not regeneration.get("enabled"):
        return "long_tail_regeneration_not_run"
    if attempt_summary["attempted_rows"] == 0:
        return "long_tail_regeneration_no_attempted_rows"
    if attempt_summary["invalid_rows"]:
        return "long_tail_regeneration_smoke_needs_review"
    return "long_tail_regeneration_smoke_passed"


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    attempts = payload["attempt_summary"]
    lines = [
        "# R202 Long-Tail Regeneration Smoke",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Scope",
        "",
        "- Reads generated R170 AgentFlame and R189/R196-derived artifacts only.",
        "- Starts or uses a llama.cpp-compatible server for bounded candidate regeneration.",
        "- Does not read or mutate raw Codex/Claude traces.",
        "- Does not update the canonical tag map.",
        "- Does not prove tag adequacy, merge quality, developer utility, or community adoption.",
        "",
        "## Result",
        "",
        f"- Attempted rows: `{attempts['attempted_rows']}`.",
        f"- Grammar-valid regenerated one-word candidates: `{attempts['valid_rows']}`.",
        f"- Invalid rows: `{attempts['invalid_rows']}`.",
        f"- Valid rows that changed from the raw tag: `{attempts['changed_valid_rows']}`.",
        f"- Valid rows unchanged from the raw tag: `{attempts['unchanged_valid_rows']}`.",
        f"- Unique valid regenerated tags: `{attempts['unique_valid_regenerated_tags']}`.",
        "",
        "## Top Regenerated Tags",
        "",
        "| tag | rows |",
        "|---|---:|",
    ]
    for tag, count in attempts["top_regenerated_tags"]:
        lines.append(f"| `{tag}` | {count} |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "R202 only proves that the optional llama.cpp regeneration path can produce "
            "grammar-valid candidate one-word labels for R196 review rows under the "
            "current local setup. Regenerated labels remain review candidates. They "
            "cannot support C5 user utility, C6 semantic adequacy, canonicalization "
            "quality, or community adoption without the existing human-evidence gates.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_local_audit_notice(path: Path) -> None:
    lines = [
        "# Local Audit Artifact",
        "",
        "This directory is produced by the R202 regeneration smoke as the detailed",
        "R196 governance run with regeneration enabled.",
        "",
        "It is not public-safe by default. The CSV/JSON/MD files may contain",
        "profile buckets such as local path components, tool names, process names,",
        "or other machine-specific fingerprints. They do not need raw prompt text",
        "to be useful for local audit, but they must be sanitized or excluded before",
        "a public artifact release.",
        "",
        "The public-oriented R202 files are the top-level summary JSON, summary",
        "Markdown, and bounded attempts CSV in the parent directory.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_payload(
    args: argparse.Namespace,
    out_dir: Path,
    local_run_dir: Path,
    detail_dir: Path,
    llama_info: dict[str, Any],
    r196_payload: dict[str, Any],
    attempted_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    attempt_summary = summarize_attempts(attempted_rows)
    summary_json = out_dir / "long-tail-regeneration-r202.json"
    summary_md = out_dir / "long-tail-regeneration-r202.md"
    attempts_csv = out_dir / "long-tail-regeneration-attempts-r202.csv"
    return {
        "schema_version": 1,
        "run_id": "R202",
        "generated_at": now_iso(),
        "status": status_for(r196_payload, attempt_summary),
        "method": {
            "regenerate_limit": args.regenerate_limit,
            "llama_timeout": args.llama_timeout,
            "raw_trace_policy": "read generated AgentFlame/R189 artifacts only; do not mutate raw traces",
            "candidate_only": True,
            "canonical_map_updated": False,
            "promotion_policy": "regenerated tags require R190/R124-style review before any display-map promotion",
            "privacy_policy": (
                "top-level summary/attempt CSV are public-oriented; r196_detail_dir is "
                "a local audit artifact that may contain path/profile buckets and must "
                "be sanitized or excluded before public release"
            ),
        },
        "input": {
            "agentflame_dir": rel(args.agentflame_dir),
            "r189_dir": rel(args.r189_dir),
            "r196_detail_dir": rel(detail_dir),
            "r196_governance_csv": rel(detail_dir / "long-tail-governance-r196.csv"),
            "r196_review_packet_csv": rel(detail_dir / "long-tail-review-packet-r196.csv"),
        },
        "llama": sanitized_llama_info(llama_info, out_dir, local_run_dir),
        "r196_summary": r196_payload.get("summary", {}),
        "attempt_summary": attempt_summary,
        "claim_gate": {
            "regeneration_path_smoke_supported": attempt_summary["attempted_rows"] > 0,
            "raw_tags_preserved": True,
            "canonical_map_updated": False,
            "semantic_adequacy_supported": False,
            "canonicalization_quality_supported": False,
            "developer_utility_supported": False,
            "community_adoption_supported": False,
            "requires_r124_labels_for_adequacy": True,
            "requires_r190_labels_for_merge_quality": True,
        },
        "artifacts": {
            "summary_json": rel(summary_json),
            "summary_md": rel(summary_md),
            "attempts_csv": rel(attempts_csv),
            "r196_detail_json": rel(detail_dir / "long-tail-governance-r196.json"),
            "r196_detail_md": rel(detail_dir / "long-tail-governance-r196.md"),
            "public_safe_by_default": [
                rel(summary_json),
                rel(summary_md),
                rel(attempts_csv),
            ],
            "local_audit_only": [
                rel(detail_dir / "long-tail-governance-r196.json"),
                rel(detail_dir / "long-tail-governance-r196.md"),
                rel(detail_dir / "long-tail-governance-r196.csv"),
                rel(detail_dir / "long-tail-review-packet-r196.csv"),
                rel(detail_dir / "LOCAL_AUDIT_ONLY.md"),
            ],
        },
        "provenance": {
            "git_head": git(["rev-parse", "HEAD"]),
            "git_status_short": git(["status", "--short"]),
            "script": rel(Path(__file__)),
            "script_sha256": sha256_file(Path(__file__)),
            "r196_script": rel(SCRIPT_DIR / "r196_long_tail_governance.py"),
            "r196_script_sha256": sha256_file(SCRIPT_DIR / "r196_long_tail_governance.py"),
        },
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.out_dir
    local_run_dir = args.local_run_dir
    if local_run_dir is None:
        local_run_dir = DEFAULT_LOCAL_RUN_ROOT / f"r202-long-tail-regeneration-{now_iso().replace(':', '')}"
    out_dir.mkdir(parents=True, exist_ok=True)
    local_run_dir.mkdir(parents=True, exist_ok=True)

    proc = None
    try:
        proc, llama_url, llama_info = r200.start_llama(args, local_run_dir)
        if llama_info.get("status") not in {None, "ready"} and not args.llama_url:
            payload = {
                "schema_version": 1,
                "run_id": "R202",
                "generated_at": now_iso(),
                "status": "blocked_no_llama",
                "llama": sanitized_llama_info(llama_info, out_dir, local_run_dir),
                "claim_gate": {
                    "regeneration_path_smoke_supported": False,
                    "semantic_adequacy_supported": False,
                    "canonicalization_quality_supported": False,
                    "developer_utility_supported": False,
                    "community_adoption_supported": False,
                },
            }
            write_json(out_dir / "long-tail-regeneration-r202.json", payload)
            write_markdown(out_dir / "long-tail-regeneration-r202.md", payload | {"attempt_summary": summarize_attempts([])})
            return payload

        detail_dir = out_dir / "r196-with-regeneration"
        r196_payload = r196.run(
            args.agentflame_dir,
            args.r189_dir,
            detail_dir,
            r196.GovernanceConfig(),
            llama_url=llama_url,
            regenerate_limit=args.regenerate_limit,
            llama_timeout=args.llama_timeout,
        )
        write_local_audit_notice(detail_dir / "LOCAL_AUDIT_ONLY.md")
        attempted_rows = read_attempted_rows(detail_dir / "long-tail-governance-r196.csv")
        payload = build_payload(args, out_dir, local_run_dir, detail_dir, llama_info, r196_payload, attempted_rows)
        fields = [
            "dimension",
            "raw_tag",
            "canonical_tag",
            "governance_action",
            "governance_reasons",
            "support",
            "top_processes",
            "top_effects",
            "top_context_tags",
            "regeneration_context_hash",
            "regenerated_tag",
            "regenerated_valid",
            "regeneration_error",
        ]
        write_csv(out_dir / "long-tail-regeneration-attempts-r202.csv", attempted_rows, fields)
        write_json(out_dir / "long-tail-regeneration-r202.json", payload)
        write_markdown(out_dir / "long-tail-regeneration-r202.md", payload)
        return payload
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except Exception:
                proc.kill()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agentflame-dir", type=Path, default=DEFAULT_AGENTFLAME_DIR)
    parser.add_argument("--r189-dir", type=Path, default=DEFAULT_R189_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--local-run-dir", type=Path)
    parser.add_argument("--llama-url", default="")
    parser.add_argument("--llama-server", default=str(r200.DEFAULT_LLAMA_SERVER))
    parser.add_argument("--model-path", default=str(r200.DEFAULT_MODEL_PATH))
    parser.add_argument("--model-name", default="r202-local")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--ctx-size", type=int, default=2048)
    parser.add_argument("--load-timeout", type=int, default=240)
    parser.add_argument("--llama-timeout", type=int, default=60)
    parser.add_argument("--regenerate-limit", type=int, default=50)
    return parser.parse_args()


def main() -> int:
    payload = run(parse_args())
    print(
        json.dumps(
            {
                "status": payload["status"],
                "attempted_rows": payload.get("attempt_summary", {}).get("attempted_rows", 0),
                "valid_rows": payload.get("attempt_summary", {}).get("valid_rows", 0),
                "invalid_rows": payload.get("attempt_summary", {}).get("invalid_rows", 0),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
