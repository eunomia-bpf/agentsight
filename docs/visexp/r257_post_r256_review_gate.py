#!/usr/bin/env python3
"""R257: post-R256 review gate.

This run records the read-only post-R256 OSDI/artifact reviews and mechanically
checks the author response. It is review/audit hygiene only. It must not upgrade
C5, C6, crates.io publication, community adoption, or weak-accept status.
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
RUN_ID = "R257"
DEFAULT_OUT_DIR = OUT_DIR
DEFAULT_REVIEW_JSON = OUT_DIR / "osdi-gate-review-r257.json"
DEFAULT_REVIEW_MD = OUT_DIR / "osdi-gate-review-r257.md"

R256_JSON = OUT_DIR / "agentpprof-crate-package-r256" / "agentpprof-crate-package-r256.json"
R256_MD = OUT_DIR / "agentpprof-crate-package-r256" / "agentpprof-crate-package-r256.md"
R256_FILES = OUT_DIR / "agentpprof-crate-package-r256" / "package-files-r256.txt"
R256_LOG = OUT_DIR / "agentpprof-crate-package-r256" / "cargo-package-r256.txt"

TEXT_SOURCES = {
    "paper": SCRIPT_DIR / "paper" / "main.tex",
    "claim_verdict": SCRIPT_DIR / "CLAIM_VERDICT.md",
    "experiment_audit": SCRIPT_DIR / "EXPERIMENT_AUDIT.md",
    "experiment_plan": SCRIPT_DIR / "EXPERIMENT_PLAN.md",
    "experiment_tracker": SCRIPT_DIR / "EXPERIMENT_TRACKER.md",
    "followup_plan": SCRIPT_DIR / "FOLLOWUP_PLAN.md",
    "results_summary": SCRIPT_DIR / "RESULTS_SUMMARY.md",
    "state": SCRIPT_DIR / "STATE.md",
}

REVIEW_FINDINGS = [
    {
        "reviewer": "osdi_claim_evidence_review",
        "type": "must_fix",
        "issue": (
            "C7 wording in CLAIM_VERDICT grouped R256 with fixture readback paths "
            "and implied local crate-package dry-run evidence was over a committed fixture."
        ),
        "author_response_check": "claim_verdict_r256_readback_boundary_fixed",
    },
    {
        "reviewer": "osdi_claim_evidence_review",
        "type": "stale_wording",
        "issue": (
            "EXPERIMENT_AUDIT still described C7 gaps as beyond local/GitHub-branch smokes, "
            "omitting pinned-revision and crate-package dry-run smokes."
        ),
        "author_response_check": "audit_r208_stale_c7_wording_fixed",
    },
    {
        "reviewer": "artifact_provenance_review",
        "type": "residual_risk",
        "issue": (
            "The .crate archive itself is not retained; the equality claim depends on "
            "the script-recorded archive inspection, hash, and size."
        ),
        "author_response_check": "r256_boundary_does_not_claim_publish_or_adoption",
    },
    {
        "reviewer": "artifact_provenance_review",
        "type": "residual_risk",
        "issue": (
            "no_private_history_discovery and no_llm_calls are provenance assertions "
            "from the package script path, not independently monitored runtime facts."
        ),
        "author_response_check": "r256_boundary_does_not_claim_runtime_monitoring",
    },
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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


def build_checks(r256: dict[str, Any], texts: dict[str, str]) -> list[dict[str, Any]]:
    claim_verdict = texts["claim_verdict"]
    experiment_audit = texts["experiment_audit"]
    paper = texts["paper"]
    all_text = "\n".join(texts.values())
    r256_gates = r256.get("gates", {})
    package = r256.get("package", {})
    files = package.get("files", [])

    return [
        {
            "name": "r256_artifact_passed",
            "passed": r256.get("status") == "passed"
            and r256.get("c7_crate_package_smoke_supported") is True
            and r256_gates.get("cargo_package_ok") is True
            and r256_gates.get("archive_files_match_list") is True,
            "observed": {
                "status": r256.get("status"),
                "c7_crate_package_smoke_supported": r256.get("c7_crate_package_smoke_supported"),
                "cargo_package_ok": r256_gates.get("cargo_package_ok"),
                "archive_files_match_list": r256_gates.get("archive_files_match_list"),
            },
        },
        {
            "name": "r256_package_scope_exact",
            "passed": len(files) == 8
            and "examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl" in files
            and package.get("missing_required_files") == []
            and package.get("forbidden_package_hits") == [],
            "observed": {
                "file_count": len(files),
                "has_public_fixture_file": (
                    "examples/codex/sessions/2026/06/18/public-agentpprof-fixture.jsonl" in files
                ),
                "missing_required_files": package.get("missing_required_files"),
                "forbidden_package_hits": package.get("forbidden_package_hits"),
            },
        },
        {
            "name": "r256_does_not_upgrade_human_or_publish_gates",
            "passed": r256.get("weak_accept_supported") is False
            and r256.get("c5_supported") is False
            and r256.get("c6_supported") is False
            and r256.get("crates_publish_supported") is False
            and r256.get("external_machine_install_supported") is False
            and r256.get("developer_utility_supported") is False,
            "observed": {
                "weak_accept_supported": r256.get("weak_accept_supported"),
                "c5_supported": r256.get("c5_supported"),
                "c6_supported": r256.get("c6_supported"),
                "crates_publish_supported": r256.get("crates_publish_supported"),
                "external_machine_install_supported": r256.get("external_machine_install_supported"),
                "developer_utility_supported": r256.get("developer_utility_supported"),
            },
        },
        {
            "name": "claim_verdict_r256_readback_boundary_fixed",
            "passed": (
                "R256 packages that fixture file but does not run `agentpprof` over it" in claim_verdict
                and "local crate-package dry-run evidence for the intended 8-file crate contents" in claim_verdict
                and "local crate-package dry-run evidence over a committed fixture" not in claim_verdict
                and "R248/R253/R254/R256 simply" not in claim_verdict
            ),
            "observed": {
                "separates_package_from_readback": (
                    "R256 packages that fixture file but does not run `agentpprof` over it" in claim_verdict
                ),
                "has_intended_file_set_wording": (
                    "local crate-package dry-run evidence for the intended 8-file crate contents" in claim_verdict
                ),
                "old_over_fixture_phrase_absent": (
                    "local crate-package dry-run evidence over a committed fixture" not in claim_verdict
                ),
                "old_grouping_absent": "R248/R253/R254/R256 simply" not in claim_verdict,
            },
        },
        {
            "name": "audit_r208_stale_c7_wording_fixed",
            "passed": (
                "beyond the local, GitHub-branch, pinned-revision, and crate-package" in experiment_audit
                and "beyond the local/GitHub-branch smokes" not in experiment_audit
            ),
            "observed": {
                "new_phrase_present": (
                    "beyond the local, GitHub-branch, pinned-revision, and crate-package" in experiment_audit
                ),
                "old_phrase_absent": "beyond the local/GitHub-branch smokes" not in experiment_audit,
            },
        },
        {
            "name": "paper_keeps_r256_packaging_only",
            "passed": (
                "R256 只证明本地 crate packaging" in paper
                and "crates.io publish/readback" in paper
                and "当前版本仍不到 OSDI weak accept" in paper
            ),
            "observed": {
                "paper_says_packaging_only": "R256 只证明本地 crate packaging" in paper,
                "paper_keeps_crates_io_gap": "crates.io publish/readback" in paper,
                "paper_keeps_weak_accept_boundary": "当前版本仍不到 OSDI weak accept" in paper,
            },
        },
        {
            "name": "evidence_docs_keep_c5_c6_blockers",
            "passed": (
                "C5" in all_text
                and "C6" in all_text
                and "real participant responses" in all_text
                and "human labels" in all_text
                and "weak_accept_supported=false" in all_text
            ),
            "observed": {
                "mentions_real_participant_responses": "real participant responses" in all_text,
                "mentions_human_labels": "human labels" in all_text,
                "mentions_false_weak_accept_gate": "weak_accept_supported=false" in all_text,
            },
        },
    ]


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    r256 = read_json(R256_JSON)
    texts = {name: read_text(path) for name, path in TEXT_SOURCES.items()}
    checks = build_checks(r256, texts)
    passed = sum(1 for check in checks if check["passed"])
    source_paths = [R256_JSON, R256_MD, R256_FILES, R256_LOG, *TEXT_SOURCES.values()]
    status = "post_r256_review_gate_passed" if passed == len(checks) else "post_r256_review_gate_failed"

    return {
        "schema_version": 1,
        "run_id": RUN_ID,
        "status": status,
        "generated_at": now_iso(),
        "source_command": "python3 docs/visexp/r257_post_r256_review_gate.py",
        "review_type": "read_only_osdi_and_artifact_review_plus_author_response",
        "review_verdict": {
            "maturity": "Level 3 mechanism evidence",
            "weak_accept_supported": False,
            "summary": (
                "R256 strengthens only C7 local crate-package readiness. "
                "The post-R256 reviews found no remaining artifact-provenance must-fix "
                "issues after author wording fixes, but C5 and C6 still lack real human data."
            ),
        },
        "review_findings": REVIEW_FINDINGS,
        "author_response": [
            "Separated R248/R253/R254 fixture readback evidence from R256 crate-package dry-run evidence in CLAIM_VERDICT.",
            "Removed stale C7 wording that stopped at local/GitHub-branch smokes in EXPERIMENT_AUDIT.",
            "Kept R256 scoped to local crate-package dry-run and kept C5/C6/weak-accept/crates-publish gates false.",
        ],
        "checks": checks,
        "checks_passed": passed,
        "checks_total": len(checks),
        "claim_gate": {
            "weak_accept_supported": False,
            "c5_supported": False,
            "c6_supported": False,
            "crates_publish_supported": False,
            "external_machine_install_supported": False,
            "developer_utility_supported": False,
            "outcome_evidence_added": False,
        },
        "residual_risks": [
            "The .crate archive itself is not retained; R256 records archive hash, size, and archive/list equality from the run.",
            "R256 privacy scan covers generated summary/log/list artifacts for path leakage, not a full semantic scan of package contents.",
            "R256 no-private-history and no-LLM claims are script-path assertions, not independently monitored runtime facts.",
            "Weak accept still requires real C5 participant responses and real C6 human labels scored through the existing gates.",
        ],
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


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# R257 Post-R256 Review Gate",
        "",
        f"Run ID: `{payload['run_id']}`",
        f"Status: `{payload['status']}`",
        f"Generated at: `{payload['generated_at']}`",
        f"Source command: `{payload['source_command']}`",
        "",
        "## Verdict",
        "",
        payload["review_verdict"]["summary"],
        "",
        "R257 is audit hygiene only. It adds no participant responses, no human labels, no crates.io publish/readback, and no external-machine evidence.",
        "",
        "## Review Findings",
        "",
        "| Reviewer | Type | Finding | Response check |",
        "|----------|------|---------|----------------|",
    ]
    for finding in payload["review_findings"]:
        lines.append(
            f"| `{finding['reviewer']}` | `{finding['type']}` | {finding['issue']} | `{finding['author_response_check']}` |"
        )
    lines.extend(["", "## Author Response", ""])
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
    for check in payload["checks"]:
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
            f"- c6_supported: `{gate['c6_supported']}`",
            f"- crates_publish_supported: `{gate['crates_publish_supported']}`",
            f"- external_machine_install_supported: `{gate['external_machine_install_supported']}`",
            f"- developer_utility_supported: `{gate['developer_utility_supported']}`",
            f"- outcome_evidence_added: `{gate['outcome_evidence_added']}`",
            "",
            "## Residual Risks",
            "",
        ]
    )
    for item in payload["residual_risks"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-json", type=Path, default=DEFAULT_REVIEW_JSON)
    parser.add_argument("--review-md", type=Path, default=DEFAULT_REVIEW_MD)
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.review_json, payload)
    write_text(args.review_md, render_markdown(payload))
    if payload["checks_passed"] != payload["checks_total"]:
        failed = [check["name"] for check in payload["checks"] if not check["passed"]]
        print(f"R257 review gate failed: {failed}")
        return 1
    print(f"R257 review gate passed: {payload['checks_passed']}/{payload['checks_total']} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
