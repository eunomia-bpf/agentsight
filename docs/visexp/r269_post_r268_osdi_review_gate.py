#!/usr/bin/env python3
"""R269: post-R268 independent OSDI review gate.

This records the read-only Epicurus review after R268 and mechanically checks
that the paper keeps R268 scoped as C5-return orchestration rather than outcome
evidence. It adds no participant responses and no human labels.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUT_DIR = SCRIPT_DIR / "out"

RUN_ID = "R269"
OUT_JSON = OUT_DIR / "osdi-gate-review-r269.json"
OUT_MD = OUT_DIR / "osdi-gate-review-r269.md"

TEXT_SOURCES = {
    "paper": SCRIPT_DIR / "paper" / "main.tex",
    "state": SCRIPT_DIR / "STATE.md",
    "followup": SCRIPT_DIR / "FOLLOWUP_PLAN.md",
    "claim_verdict": SCRIPT_DIR / "CLAIM_VERDICT.md",
    "experiment_audit": SCRIPT_DIR / "EXPERIMENT_AUDIT.md",
}

JSON_SOURCES = {
    "r142_paper": OUT_DIR / "user-task-paper-r249" / "scored" / "user-task-results.json",
    "r124": OUT_DIR / "tag-adequacy-results-r124.json",
    "r190": OUT_DIR / "tag-consolidation-audit-r190" / "merge-risk-audit-results-r190.json",
    "r203": OUT_DIR / "long-tail-promotion-r203" / "long-tail-promotion-r203.json",
    "r267": OUT_DIR / "osdi-gate-review-r267.json",
    "r268": OUT_DIR / "c5-real-return-pipeline-r268" / "c5-real-return-pipeline-r268.json",
}

SUBAGENT_REVIEW = {
    "agent_nickname": "Epicurus",
    "review_type": "independent_read_only_osdi_review_after_r268",
    "maturity": "Level 3",
    "weak_accept_ready": False,
    "overall_verdict": (
        "Current maturity is Level 3 conference-paper mechanism evidence, not "
        "Level 4 and not OSDI weak accept. C5 has zero participant responses and "
        "C6 has zero human labels."
    ),
    "severity_ranked_findings": [
        {
            "severity": "blocker",
            "claim": "C5 developer utility",
            "finding": "Launch packets, forms, answer keys, and scorers exist, but no real participant outcomes exist.",
        },
        {
            "severity": "blocker",
            "claim": "C6 tag adequacy",
            "finding": "Syntax/stability and behavior association are proxies; R124/R190/R203 have 0 final labels.",
        },
        {
            "severity": "major",
            "claim": "C4 exact lineage",
            "finding": "Fixed/controlled workloads are credible; broad Codex/Claude-launched target-network coverage remains partial.",
        },
        {
            "severity": "major",
            "claim": "C7 community readiness",
            "finding": "Install/package smokes do not prove crates.io publish/readback, external-machine install, write-set audit, or external developer success.",
        },
    ],
    "not_outcome_evidence": [
        "R187/R249/R255/R258/R259 launch/static collection artifacts",
        "R263-R268 intake/safety/adjudication/public-summary/orchestration gates",
        "R242/R244 synthetic-return/export smokes",
        "R267/subagent reviews",
        "R180 syntax/stability",
        "R251 behavior association",
        "R189-R218 display/canonicalization/governance/frontend artifacts",
        "C7 install/package smokes",
    ],
    "wording_fix": {
        "old": "用来辅助三类 developer questions",
        "required_new": "planned C5 tasks",
        "reason": "Until real C5 outcomes pass, the paper should describe candidate decompositions for planned tasks, not assistance that has already been validated.",
    },
    "first_next_experiment": {
        "name": "paper-scale C5 user-task study through R268",
        "private_input": "private/completed-paper-scale-r264/c5/user-task-response-template-r249-paper.csv",
        "command": "python3 docs/visexp/r268_c5_real_return_scoring_pipeline.py",
        "private_result": "private/completed-paper-scale-r264/r195-scored/human-evidence-pipeline-r195.json",
        "public_summary": "docs/visexp/out/c5-real-return-pipeline-r268/public-summary-r266",
        "oracle": (
            "At least 12 participants, at least 8 primary semantic-vs-baseline task "
            "pairs per baseline, semantic-stack beats all baselines by >=10 pp exact "
            "accuracy or >=20% median time reduction, Holm-corrected participant/task/"
            "order blocked permutation p<=0.05, and false-positive increase <=5 pp."
        ),
    },
}


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def sha256_file(path: Path) -> str:
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


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing JSON source: {rel(path)}")
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


def build_checks(jsons: dict[str, dict[str, Any]], texts: dict[str, str]) -> list[dict[str, Any]]:
    paper = texts["paper"]
    state = texts["state"]
    followup = texts["followup"]
    audit = texts["experiment_audit"]
    verdict = texts["claim_verdict"]
    all_text = "\n".join(texts.values())

    r142 = jsons["r142_paper"]
    r124 = jsons["r124"]
    r190 = jsons["r190"]
    r203 = jsons["r203"]
    r267 = jsons["r267"]
    r268 = jsons["r268"]

    r142_gate = ((r142.get("claim_analysis") or {}).get("claim_gate") or {})
    r124_gate = r124.get("claim_gate") or {}
    r190_gate = r190.get("claim_gate") or {}
    r203_gate = r203.get("claim_gate") or {}
    r267_gate = r267.get("claim_gate") or {}
    r268_gate = r268.get("claim_gate") or {}
    r268_private = r268.get("private_input") or {}
    r268_execution = r268.get("execution") or {}

    return [
        {
            "name": "epicurus_review_keeps_level3_not_weak_accept",
            "passed": SUBAGENT_REVIEW["maturity"] == "Level 3"
            and SUBAGENT_REVIEW["weak_accept_ready"] is False,
            "observed": {
                "maturity": SUBAGENT_REVIEW["maturity"],
                "weak_accept_ready": SUBAGENT_REVIEW["weak_accept_ready"],
            },
        },
        {
            "name": "r268_waits_for_private_c5_returns",
            "passed": r268.get("status") == "awaiting_private_c5_returns"
            and r268_private.get("exists") is False
            and r268_private.get("path_kind") == "private"
            and r268_gate.get("c5_supported") is False
            and r268_gate.get("weak_accept_supported") is False
            and r268_execution.get("raw_private_rows_exported") is False
            and r268_execution.get("private_hashes_exported") is False,
            "observed": {
                "status": r268.get("status"),
                "private_exists": r268_private.get("exists"),
                "path_kind": r268_private.get("path_kind"),
                "c5_supported": r268_gate.get("c5_supported"),
                "weak_accept_supported": r268_gate.get("weak_accept_supported"),
                "raw_private_rows_exported": r268_execution.get("raw_private_rows_exported"),
                "private_hashes_exported": r268_execution.get("private_hashes_exported"),
            },
        },
        {
            "name": "c5_c6_outcomes_still_absent",
            "passed": r142.get("status") == "participant_results_empty"
            and r142.get("participant_count") == 0
            and r142.get("response_count") == 0
            and r142_gate.get("c5_supported") is False
            and (r124.get("summary") or {}).get("final_label_count") == 0
            and r124_gate.get("adequacy_supported") is False
            and (r190.get("summary") or {}).get("final_label_count") == 0
            and r190_gate.get("canonicalization_quality_supported") is False
            and (r203.get("summary") or {}).get("final_label_count") == 0
            and r203_gate.get("long_tail_promotion_review_supported") is False,
            "observed": {
                "c5_status": r142.get("status"),
                "participant_count": r142.get("participant_count"),
                "response_count": r142.get("response_count"),
                "r124_final_label_count": (r124.get("summary") or {}).get("final_label_count"),
                "r190_final_label_count": (r190.get("summary") or {}).get("final_label_count"),
                "r203_final_label_count": (r203.get("summary") or {}).get("final_label_count"),
            },
        },
        {
            "name": "paper_tightens_developer_question_wording",
            "passed": SUBAGENT_REVIEW["wording_fix"]["old"] not in paper
            and SUBAGENT_REVIEW["wording_fix"]["required_new"] in paper,
            "observed": {
                "old_phrase_present": SUBAGENT_REVIEW["wording_fix"]["old"] in paper,
                "new_phrase_present": SUBAGENT_REVIEW["wording_fix"]["required_new"] in paper,
            },
        },
        {
            "name": "paper_keeps_event_count_proxy_boundary",
            "passed": "event-count proxy" in paper
            and "它不能直接当作 span-duration baseline" in paper,
            "observed": {
                "event_count_proxy_mentioned": "event-count proxy" in paper,
                "not_span_duration_boundary": "它不能直接当作 span-duration baseline" in paper,
            },
        },
        {
            "name": "state_followup_record_r268_without_upgrading_claims",
            "passed": "Latest R268 artifact" in state
            and "R268 only orchestrates private C5 scoring" in state
            and "Do not upgrade C5/C6" in state
            and "R268" in followup
            and "awaiting_private_c5_returns" in followup,
            "observed": {
                "state_latest_r268": "Latest R268 artifact" in state,
                "state_r268_boundary": "R268 only orchestrates private C5 scoring" in state,
                "state_no_upgrade_boundary": "Do not upgrade C5/C6" in state,
                "followup_mentions_r268": "R268" in followup,
                "followup_waiting_status": "awaiting_private_c5_returns" in followup,
            },
        },
        {
            "name": "evidence_docs_keep_non_outcome_boundary",
            "passed": "R268" in verdict
            and "R268" in audit
            and "subagent review" in all_text
            and "cannot substitute" in all_text
            and "mock responses" in all_text
            and "placeholder rows" in all_text,
            "observed": {
                "claim_verdict_mentions_r268": "R268" in verdict,
                "audit_mentions_r268": "R268" in audit,
                "subagent_boundary": "subagent review" in all_text and "cannot substitute" in all_text,
                "mock_responses_disallowed": "mock responses" in all_text,
                "placeholder_rows_disallowed": "placeholder rows" in all_text,
            },
        },
        {
            "name": "prior_review_gate_remains_not_weak_accept",
            "passed": r267.get("status") == "post_r266_osdi_review_gate_passed"
            and r267_gate.get("weak_accept_supported") is False,
            "observed": {
                "r267_status": r267.get("status"),
                "r267_weak_accept_supported": r267_gate.get("weak_accept_supported"),
            },
        },
    ]


def build_payload() -> dict[str, Any]:
    jsons = {name: read_json(path) for name, path in JSON_SOURCES.items()}
    texts = {name: read_text(path) for name, path in TEXT_SOURCES.items()}
    checks = build_checks(jsons, texts)
    status = "post_r268_osdi_review_gate_passed" if all(check["passed"] for check in checks) else "post_r268_osdi_review_gate_failed"
    return {
        "schema_version": 1,
        "run_id": RUN_ID,
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_command": "python3 docs/visexp/r269_post_r268_osdi_review_gate.py",
        "review_type": SUBAGENT_REVIEW["review_type"],
        "review_verdict": {
            "maturity": SUBAGENT_REVIEW["maturity"],
            "weak_accept_supported": False,
            "summary": SUBAGENT_REVIEW["overall_verdict"],
        },
        "subagent_review": SUBAGENT_REVIEW,
        "checks": checks,
        "checks_passed": sum(1 for check in checks if check["passed"]),
        "checks_total": len(checks),
        "claim_gate": {
            "c5_supported": False,
            "c6_supported": False,
            "developer_utility_supported": False,
            "tag_adequacy_supported": False,
            "outcome_evidence_added": False,
            "weak_accept_supported": False,
        },
        "residual_risks": [
            "Weak accept still requires real C5 participant responses scored through R268/R195/R266.",
            "Weak accept still requires real C6 human labels and adjudication where needed.",
            "R269 is read-only review hygiene and cannot substitute for outcome evidence.",
            "C4 broad agent-launched target-network coverage and C7 community adoption remain partial.",
        ],
        "provenance": {
            "generator": rel(Path(__file__).resolve()),
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "llm_called": False,
            "subagent_review_used": True,
            "subagent_nickname": SUBAGENT_REVIEW["agent_nickname"],
            "participant_responses_added": 0,
            "human_labels_added": 0,
            "raw_trace_read": False,
            "source_hashes": source_hashes([*TEXT_SOURCES.values(), *JSON_SOURCES.values()]),
        },
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    review = payload["subagent_review"]
    next_exp = review["first_next_experiment"]
    lines = [
        "# R269 Post-R268 OSDI Review Gate",
        "",
        f"Run ID: `{payload['run_id']}`",
        f"Status: `{payload['status']}`",
        f"Generated at: `{payload['generated_at']}`",
        f"Source command: `{payload['source_command']}`",
        "",
        "## Verdict",
        "",
        review["overall_verdict"],
        "",
        "R269 is review hygiene only. It adds no participant responses, no human labels, and no weak-accept support.",
        "",
        "## Severity-Ranked Findings",
        "",
        "| Severity | Claim | Finding |",
        "|----------|-------|---------|",
    ]
    for finding in review["severity_ranked_findings"]:
        lines.append(f"| `{finding['severity']}` | {finding['claim']} | {finding['finding']} |")

    lines.extend(
        [
            "",
            "## Useful But Not Outcome Evidence",
            "",
        ]
    )
    for item in review["not_outcome_evidence"]:
        lines.append(f"- {item}.")

    lines.extend(
        [
            "",
            "## Highest-Value Next Gate",
            "",
            f"- Name: `{next_exp['name']}`.",
            f"- Private input: `{next_exp['private_input']}`.",
            f"- Command: `{next_exp['command']}`.",
            f"- Private result: `{next_exp['private_result']}`.",
            f"- Public summary: `{next_exp['public_summary']}`.",
            f"- Oracle: {next_exp['oracle']}",
            "",
            "## Mechanical Checks",
            "",
            "| Check | Passed | Observed |",
            "|-------|--------|----------|",
        ]
    )
    for check in payload["checks"]:
        observed = json.dumps(check["observed"], sort_keys=True)
        lines.append(f"| `{check['name']}` | `{check['passed']}` | `{observed}` |")

    lines.extend(
        [
            "",
            "## Claim Gate",
            "",
        ]
    )
    for key, value in payload["claim_gate"].items():
        lines.append(f"- {key}: `{value}`")

    lines.extend(
        [
            "",
            "## Residual Risks",
            "",
        ]
    )
    for risk in payload["residual_risks"]:
        lines.append(f"- {risk}")
    lines.append("")
    write_text(path, "\n".join(lines))


def run() -> dict[str, Any]:
    payload = build_payload()
    write_json(OUT_JSON, payload)
    write_markdown(OUT_MD, payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "checks_passed": payload["checks_passed"],
                "checks_total": payload["checks_total"],
            },
            indent=2,
        )
    )
    return payload


if __name__ == "__main__":
    run()
