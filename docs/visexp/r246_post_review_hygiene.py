#!/usr/bin/env python3
"""R246: post-R245 OSDI review hygiene gate.

This run records the post-R245 read-only OSDI review and checks the fixable
provenance issues it found. It is audit hygiene only: it must not upgrade C5,
C6, broad C4, or weak-accept status without real participant/label evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUT_DIR = SCRIPT_DIR / "out"
DEFAULT_REVIEW_JSON = OUT_DIR / "osdi-gate-review-r246.json"
DEFAULT_REVIEW_MD = OUT_DIR / "osdi-gate-review-r246.md"
DEFAULT_R224_METADATA = OUT_DIR / "semantic-ablation-r224-r170" / "r224-rerun-metadata.json"

R170 = OUT_DIR / "full-history-r170.json"
R224 = OUT_DIR / "semantic-ablation-r224-r170" / "semantic-ablation-r131.json"
R245 = OUT_DIR / "claim-wording-consistency-r245" / "claim-wording-consistency-r245.json"
R195 = OUT_DIR / "human-evidence-pipeline-r195.json"
R124 = OUT_DIR / "tag-adequacy-results-r124.json"
USER_TASK = OUT_DIR / "user-task-results.json"

TEXT_SOURCES = {
    "paper": SCRIPT_DIR / "paper" / "main.tex",
    "claim_verdict": SCRIPT_DIR / "CLAIM_VERDICT.md",
    "experiment_audit": SCRIPT_DIR / "EXPERIMENT_AUDIT.md",
    "experiment_tracker": SCRIPT_DIR / "EXPERIMENT_TRACKER.md",
    "followup_plan": SCRIPT_DIR / "FOLLOWUP_PLAN.md",
    "results_summary": SCRIPT_DIR / "RESULTS_SUMMARY.md",
}

EXACT_R170_COMMAND = (
    "cargo run --manifest-path agentflame/Cargo.toml -- run --project-root . "
    "--scan-files 10000 --max-sessions 10000 --llama-url http://127.0.0.1:18080 "
    "--model local-r170 --timeout 60 --out .agentsight/agentflame/r170-full-current"
)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing artifact: {rel(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"missing text source: {rel(path)}")
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def source_hashes(paths: list[Path]) -> dict[str, str]:
    return {rel(path): sha256_file(path) for path in paths if path.exists()}


def nested_get(mapping: dict[str, Any], keys: list[str], default: Any = None) -> Any:
    value: Any = mapping
    for key in keys:
        if not isinstance(value, dict):
            return default
        value = value.get(key)
    return value if value is not None else default


def build_r224_metadata(r224: dict[str, Any]) -> dict[str, Any]:
    provenance = r224.get("provenance", {})
    return {
        "schema_version": 1,
        "run_id": "R224",
        "checker_id": "R131",
        "status": "rerun_metadata_clarified",
        "source_artifact": rel(R224),
        "source_artifact_sha256": sha256_file(R224),
        "source_run_id": r224.get("run_id"),
        "source_command": provenance.get("command"),
        "input": ".agentsight/agentflame/r170-full-current",
        "claim_boundary": (
            "R224 is a rerun of the R131 semantic-axis checker over the R170 "
            "current full-history denominator. The checked JSON keeps the "
            "checker-local run_id R131, so this metadata records the paper-level "
            "rerun id R224 and prevents interpreting the file name as a separate "
            "algorithm or outcome result."
        ),
        "provenance": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": rel(Path(__file__)),
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--porcelain"])),
            "source_repo_commit": provenance.get("repo_commit"),
            "source_repo_dirty": provenance.get("repo_dirty"),
        },
    }


def build_checks(
    r170: dict[str, Any],
    r224: dict[str, Any],
    r245: dict[str, Any],
    r195: dict[str, Any],
    r124: dict[str, Any],
    user_task: dict[str, Any],
    texts: dict[str, str],
) -> list[dict[str, Any]]:
    all_text = "\n".join(texts.values())
    paper = texts["paper"]
    audit = texts["experiment_audit"]
    results = texts["results_summary"]
    tracker = texts["experiment_tracker"]
    verdict = texts["claim_verdict"]

    r195_gate = r195.get("claim_gate", {})
    r245_gate = r245.get("claim_gate", {})
    user_task_gate = nested_get(user_task, ["claim_analysis", "claim_gate"], {})
    r124_summary = r124.get("summary", {})
    r124_gate = r124.get("claim_gate", {})

    checks = [
        {
            "name": "c5_real_participants_still_absent",
            "passed": user_task.get("status") == "participant_results_empty"
            and int(user_task.get("participant_count", -1)) == 0
            and user_task_gate.get("c5_supported") is False
            and r195_gate.get("c5_supported") is False,
            "observed": {
                "user_task_status": user_task.get("status"),
                "user_task_participant_count": user_task.get("participant_count"),
                "user_task_c5_supported": user_task_gate.get("c5_supported"),
                "r195_c5_supported": r195_gate.get("c5_supported"),
            },
        },
        {
            "name": "c6_human_labels_still_absent",
            "passed": r124.get("status") == "human_labels_empty"
            and int(r124_summary.get("final_label_count", -1)) == 0
            and r124_gate.get("adequacy_supported") is False
            and r195_gate.get("c6_adequacy_supported") is False,
            "observed": {
                "r124_status": r124.get("status"),
                "r124_final_label_count": r124_summary.get("final_label_count"),
                "r124_adequacy_supported": r124_gate.get("adequacy_supported"),
                "r195_c6_adequacy_supported": r195_gate.get("c6_adequacy_supported"),
            },
        },
        {
            "name": "weak_accept_still_not_supported",
            "passed": r245_gate.get("weak_accept_supported") is False
            and r195_gate.get("weak_accept_supported", False) is False,
            "observed": {
                "r245_weak_accept_supported": r245_gate.get("weak_accept_supported"),
                "r195_weak_accept_supported": r195_gate.get("weak_accept_supported"),
            },
        },
        {
            "name": "r170_source_command_matches_paper",
            "passed": r170.get("source_command") == EXACT_R170_COMMAND
            and EXACT_R170_COMMAND in paper,
            "observed": {
                "r170_source_command": r170.get("source_command"),
                "paper_has_exact_command": EXACT_R170_COMMAND in paper,
            },
        },
        {
            "name": "r170_dirty_provenance_acknowledged",
            "passed": nested_get(r170, ["provenance", "repo_dirty"]) is True
            and "repo_dirty=true" in all_text
            and "dirty-provenance" in all_text,
            "observed": {
                "r170_repo_dirty": nested_get(r170, ["provenance", "repo_dirty"]),
                "docs_mention_repo_dirty_true": "repo_dirty=true" in all_text,
                "docs_mention_dirty_provenance": "dirty-provenance" in all_text,
            },
        },
        {
            "name": "r224_metadata_clarifies_rerun_identity",
            "passed": r224.get("run_id") == "R131"
            and "r224-rerun-metadata.json" in all_text
            and "checker_id" in results
            and "R131" in results
            and "R224" in results,
            "observed": {
                "source_run_id": r224.get("run_id"),
                "results_mentions_metadata": "r224-rerun-metadata.json" in results,
                "results_mentions_checker_id": "checker_id" in results,
            },
        },
        {
            "name": "r246_recorded_in_main_evidence_docs",
            "passed": all("R246" in texts[name] for name in [
                "claim_verdict",
                "experiment_audit",
                "experiment_tracker",
                "followup_plan",
                "results_summary",
            ]),
            "observed": {
                name: ("R246" in texts[name])
                for name in [
                    "claim_verdict",
                    "experiment_audit",
                    "experiment_tracker",
                    "followup_plan",
                    "results_summary",
                ]
            },
        },
        {
            "name": "r170_dirty_caveat_reaches_verdict_and_audit",
            "passed": "repo_dirty=true" in verdict and "repo_dirty=true" in audit,
            "observed": {
                "verdict_mentions_repo_dirty_true": "repo_dirty=true" in verdict,
                "audit_mentions_repo_dirty_true": "repo_dirty=true" in audit,
            },
        },
        {
            "name": "tracker_records_r246_gate",
            "passed": "| R246 |" in tracker and "no outcome evidence" in tracker,
            "observed": {
                "tracker_has_r246_row": "| R246 |" in tracker,
                "tracker_has_no_outcome_boundary": "no outcome evidence" in tracker,
            },
        },
    ]
    return checks


def build_review_payload(args: argparse.Namespace) -> dict[str, Any]:
    r170 = read_json(R170)
    r224 = read_json(R224)
    r245 = read_json(R245)
    r195 = read_json(R195)
    r124 = read_json(R124)
    user_task = read_json(USER_TASK)
    texts = {name: read_text(path) for name, path in TEXT_SOURCES.items()}

    r224_metadata = build_r224_metadata(r224)
    checks = build_checks(r170, r224, r245, r195, r124, user_task, texts)
    passed = sum(1 for check in checks if check["passed"])

    source_paths = [R170, R224, R245, R195, R124, USER_TASK, *TEXT_SOURCES.values()]
    payload: dict[str, Any] = {
        "schema_version": 1,
        "run_id": "R246",
        "status": "post_review_hygiene_passed" if passed == len(checks) else "post_review_hygiene_failed",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_command": "python3 docs/visexp/r246_post_review_hygiene.py",
        "review_type": "read_only_osdi_gate_review_plus_author_hygiene_response",
        "review_verdict": {
            "maturity": "Level 3 mechanism evidence",
            "weak_accept_supported": False,
            "summary": (
                "The project remains below OSDI weak accept because C5 has zero "
                "real participant responses and C6 has zero real human labels. "
                "R246 fixes provenance and metadata hygiene only."
            ),
        },
        "must_fix_before_weak_accept": [
            "Collect and score real R142/R151 developer-task responses for C5.",
            "Collect and score blinded R124 human tag-adequacy labels for C6.",
        ],
        "author_response": [
            "Record R170 as dirty-provenance mechanism evidence rather than a clean release artifact.",
            "Align the paper's R170 command with the committed R170 source command.",
            "Clarify that R224 is a paper-level rerun of the R131 semantic-axis checker over the R170 denominator.",
            "Keep all C5/C6/weak-accept gates false until real human data exists.",
        ],
        "checks": checks,
        "checks_passed": passed,
        "checks_total": len(checks),
        "claim_gate": {
            "weak_accept_supported": False,
            "c5_supported": False,
            "c6_adequacy_supported": False,
            "broad_c4_supported": False,
            "outcome_evidence_added": False,
        },
        "r224_metadata_path": rel(args.r224_metadata),
        "r224_metadata_sha256_after_write": None,
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--porcelain"])),
            "generator": rel(Path(__file__)),
            "source_hashes": source_hashes(source_paths),
            "raw_trace_read": False,
            "llm_called": False,
            "participant_responses_added": 0,
            "human_labels_added": 0,
        },
    }
    return payload, r224_metadata


def render_markdown(payload: dict[str, Any]) -> str:
    checks = payload["checks"]
    lines = [
        "# R246 Post-Review Hygiene Gate",
        "",
        f"Run ID: `{payload['run_id']}`",
        f"Status: `{payload['status']}`",
        f"Generated at: `{payload['generated_at']}`",
        f"Source command: `{payload['source_command']}`",
        "",
        "## Verdict",
        "",
        "The post-R245 OSDI review keeps the project at Level 3 mechanism evidence, not weak accept.",
        "The blocking evidence gaps are unchanged: C5 has no real participant responses and C6 has no real human adequacy labels.",
        "R246 records only author-side hygiene fixes for provenance and run identity.",
        "",
        "## Must Fix Before Weak Accept",
        "",
    ]
    for item in payload["must_fix_before_weak_accept"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Author Response",
            "",
        ]
    )
    for item in payload["author_response"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Mechanical Checks",
            "",
            "| Check | Passed | Observed |",
            "|-------|--------|----------|",
        ]
    )
    for check in checks:
        observed = json.dumps(check.get("observed", {}), sort_keys=True)
        lines.append(f"| `{check['name']}` | `{check['passed']}` | `{observed}` |")
    gate = payload["claim_gate"]
    lines.extend(
        [
            "",
            "## Claim Gate",
            "",
            f"- weak_accept_supported: `{gate['weak_accept_supported']}`",
            f"- c5_supported: `{gate['c5_supported']}`",
            f"- c6_adequacy_supported: `{gate['c6_adequacy_supported']}`",
            f"- broad_c4_supported: `{gate['broad_c4_supported']}`",
            f"- outcome_evidence_added: `{gate['outcome_evidence_added']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-json", type=Path, default=DEFAULT_REVIEW_JSON)
    parser.add_argument("--review-md", type=Path, default=DEFAULT_REVIEW_MD)
    parser.add_argument("--r224-metadata", type=Path, default=DEFAULT_R224_METADATA)
    args = parser.parse_args()

    payload, r224_metadata = build_review_payload(args)
    write_json(args.r224_metadata, r224_metadata)
    payload["r224_metadata_sha256_after_write"] = sha256_file(args.r224_metadata)
    write_json(args.review_json, payload)
    write_text(args.review_md, render_markdown(payload))

    if payload["checks_passed"] != payload["checks_total"]:
        failed = [check["name"] for check in payload["checks"] if not check["passed"]]
        print(f"R246 hygiene failed: {failed}")
        return 1
    print(f"R246 hygiene passed: {payload['checks_passed']}/{payload['checks_total']} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
