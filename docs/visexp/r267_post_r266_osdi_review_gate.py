#!/usr/bin/env python3
"""R267: post-R266 independent OSDI review gate.

This records the read-only subagent review after R266 and mechanically checks
that the paper and evidence artifacts still keep C5, C6, and weak-accept gates
false. It is review hygiene only; it adds no participant responses or human
labels.
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

RUN_ID = "R267"
OUT_JSON = OUT_DIR / "osdi-gate-review-r267.json"
OUT_MD = OUT_DIR / "osdi-gate-review-r267.md"

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
    "r264": OUT_DIR / "human-return-intake-r264" / "human-return-intake-r264.json",
    "r265": OUT_DIR / "human-adjudication-r265" / "human-adjudication-r265.json",
    "r266": OUT_DIR / "human-evidence-public-summary-r266" / "human-evidence-public-summary-r266.json",
}

SUBAGENT_REVIEW = {
    "agent_nickname": "Plato",
    "review_type": "independent_read_only_osdi_review_after_r266",
    "maturity": "Level 3",
    "weak_accept_ready": False,
    "overall_verdict": (
        "Credible conference-paper mechanism evidence, but not a Level 4 systems "
        "narrative and not weak-accept-ready because C5 and C6 have no admissible "
        "human outcome evidence."
    ),
    "severity_ranked_findings": [
        {
            "severity": "blocker",
            "claim": "C5 developer utility",
            "finding": "No admissible participant outcome evidence; packets/forms/scorers exist but responses remain zero.",
        },
        {
            "severity": "blocker",
            "claim": "C6 tag adequacy",
            "finding": "No human adequacy labels; syntax/stability and behavior association remain proxies only.",
        },
        {
            "severity": "major",
            "claim": "C4 exact lineage",
            "finding": "Strong in fixed/controlled scopes, but broad Claude/Codex-launched target-network coverage remains partial.",
        },
        {
            "severity": "major",
            "claim": "C7 artifact readiness",
            "finding": "Install/package smokes are useful but do not prove crates.io, external-machine, write-set, or external-developer success.",
        },
        {
            "severity": "minor",
            "claim": "R264/R265/R266 naming",
            "finding": "Names are easy to overread, but contents and paper/state wording keep them scoped as hygiene gates.",
        },
    ],
    "claim_verdict": {
        "C1": "supported for this local history run",
        "C2": "syntax/latency supported; adequacy not supported",
        "C3": "mechanism supported; quality/user value not supported",
        "C4": "supported in fixed/controlled scopes; broad scope partial",
        "C5": "unsupported",
        "C6": "protocol ready only; human adequacy unsupported",
        "C7": "partial",
    },
    "first_next_experiment": {
        "name": "paper-scale C5 user-task study",
        "private_input": "private/completed-paper-scale-r264/c5/user-task-response-template-r249-paper.csv",
        "preflight_command": "python3 docs/visexp/r264_human_return_intake_preflight.py",
        "score_command": (
            "python3 docs/visexp/r195_human_evidence_pipeline.py "
            "--r142-responses private/completed-paper-scale-r264/c5/user-task-response-template-r249-paper.csv "
            "--r142-bundle docs/visexp/out/user-task-benchmark.json "
            "--r142-answer-key docs/visexp/out/user-task-answer-key.csv "
            "--r142-assignments docs/visexp/out/user-task-paper-r249/user-task-assignments-r249-paper.csv "
            "--scored-dir private/completed-paper-scale-r264/r195-scored "
            "--out-json private/completed-paper-scale-r264/r195-scored/human-evidence-pipeline-r195.json "
            "--out-md private/completed-paper-scale-r264/r195-scored/human-evidence-pipeline-r195.md"
        ),
        "oracle": (
            "C5 passes only if all four baselines are beaten on primary utility tasks by "
            ">=10 pp exact accuracy or >=20% median time reduction, Holm-corrected "
            "participant/task/order fixed-effect permutation p<=0.05, at least 12 "
            "participants, at least 8 task pairs per baseline, and no >5 pp false-positive increase."
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
    r264 = jsons["r264"]
    r265 = jsons["r265"]
    r266 = jsons["r266"]

    r142_gate = ((r142.get("claim_analysis") or {}).get("claim_gate") or {})
    r124_gate = r124.get("claim_gate") or {}
    r190_gate = r190.get("claim_gate") or {}
    r203_gate = r203.get("claim_gate") or {}
    r264_gate = r264.get("claim_gate") or {}
    r266_gate = r266.get("claim_gate") or {}

    return [
        {
            "name": "subagent_review_keeps_level3_not_weak_accept",
            "passed": SUBAGENT_REVIEW["maturity"] == "Level 3"
            and SUBAGENT_REVIEW["weak_accept_ready"] is False,
            "observed": {
                "maturity": SUBAGENT_REVIEW["maturity"],
                "weak_accept_ready": SUBAGENT_REVIEW["weak_accept_ready"],
            },
        },
        {
            "name": "c5_still_has_zero_participant_responses",
            "passed": r142.get("status") == "participant_results_empty"
            and r142.get("participant_count") == 0
            and r142.get("response_count") == 0
            and r142_gate.get("c5_supported") is False,
            "observed": {
                "status": r142.get("status"),
                "participant_count": r142.get("participant_count"),
                "response_count": r142.get("response_count"),
                "c5_supported": r142_gate.get("c5_supported"),
            },
        },
        {
            "name": "c6_label_gates_still_empty",
            "passed": (r124.get("summary") or {}).get("final_label_count") == 0
            and r124_gate.get("adequacy_supported") is False
            and (r190.get("summary") or {}).get("final_label_count") == 0
            and r190_gate.get("canonicalization_quality_supported") is False
            and (r203.get("summary") or {}).get("final_label_count") == 0
            and r203_gate.get("long_tail_promotion_review_supported") is False,
            "observed": {
                "r124_final_label_count": (r124.get("summary") or {}).get("final_label_count"),
                "r124_adequacy_supported": r124_gate.get("adequacy_supported"),
                "r190_final_label_count": (r190.get("summary") or {}).get("final_label_count"),
                "r190_canonicalization_quality_supported": r190_gate.get("canonicalization_quality_supported"),
                "r203_final_label_count": (r203.get("summary") or {}).get("final_label_count"),
                "r203_long_tail_promotion_review_supported": r203_gate.get("long_tail_promotion_review_supported"),
            },
        },
        {
            "name": "r264_r265_r266_are_hygiene_only",
            "passed": r264.get("status") == "awaiting_private_returns"
            and r264_gate.get("weak_accept_supported") is False
            and r265.get("status") == "passed"
            and (r265.get("checks") or {}).get("adjudicated_claim_gates_false") is True
            and r266.get("status") == "awaiting_private_scored_r195"
            and r266_gate.get("weak_accept_supported") is False
            and r266_gate.get("public_claim_update_allowed") is False,
            "observed": {
                "r264_status": r264.get("status"),
                "r264_weak_accept_supported": r264_gate.get("weak_accept_supported"),
                "r265_status": r265.get("status"),
                "r265_adjudicated_claim_gates_false": (r265.get("checks") or {}).get("adjudicated_claim_gates_false"),
                "r266_status": r266.get("status"),
                "r266_weak_accept_supported": r266_gate.get("weak_accept_supported"),
                "r266_public_claim_update_allowed": r266_gate.get("public_claim_update_allowed"),
            },
        },
        {
            "name": "paper_keeps_post_r266_review_boundary",
            "passed": "当前版本仍不到 OSDI weak accept" in paper
            and "C5 仍然没有真实 participant responses" in paper
            and "C6 仍然没有真实 human adequacy labels" in paper
            and "R260--R267" in paper
            and "不提升 C5/C6 或 weak-accept gate" in paper,
            "observed": {
                "weak_accept_boundary": "当前版本仍不到 OSDI weak accept" in paper,
                "c5_missing": "C5 仍然没有真实 participant responses" in paper,
                "c6_missing": "C6 仍然没有真实 human adequacy labels" in paper,
                "r267_review_hygiene_scoped": "R260--R267" in paper,
                "no_upgrade_boundary": "不提升 C5/C6 或 weak-accept gate" in paper,
            },
        },
        {
            "name": "state_and_followup_record_r267_without_upgrading_claims",
            "passed": "Latest R267 artifact" in state
            and "R267" in followup
            and "weak_accept_supported=false" in state
            and "Do not upgrade C5/C6" in state,
            "observed": {
                "state_latest_r267": "Latest R267 artifact" in state,
                "followup_mentions_r267": "R267" in followup,
                "state_false_weak_accept": "weak_accept_supported=false" in state,
                "state_no_upgrade_boundary": "Do not upgrade C5/C6" in state,
            },
        },
        {
            "name": "evidence_docs_keep_real_human_requirement",
            "passed": "real participant responses" in all_text
            and "human labels" in all_text
            and "subagent review" in all_text
            and "cannot substitute" in all_text
            and "R266" in verdict
            and "R266" in audit,
            "observed": {
                "real_participant_responses": "real participant responses" in all_text,
                "human_labels": "human labels" in all_text,
                "subagent_review_boundary": "subagent review" in all_text and "cannot substitute" in all_text,
                "claim_verdict_mentions_r266": "R266" in verdict,
                "experiment_audit_mentions_r266": "R266" in audit,
            },
        },
    ]


def build_payload() -> dict[str, Any]:
    jsons = {name: read_json(path) for name, path in JSON_SOURCES.items()}
    texts = {name: read_text(path) for name, path in TEXT_SOURCES.items()}
    checks = build_checks(jsons, texts)
    status = "post_r266_osdi_review_gate_passed" if all(check["passed"] for check in checks) else "post_r266_osdi_review_gate_failed"
    return {
        "schema_version": 1,
        "run_id": RUN_ID,
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_command": "python3 docs/visexp/r267_post_r266_osdi_review_gate.py",
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
            "Weak accept still requires real C5 participant responses and real C6 human labels scored through R195/R266.",
            "R267 is a read-only review gate and cannot substitute for outcome evidence.",
            "C4 exact lineage remains scoped to fixed/controlled workloads; broad agent-launched target-network coverage is partial.",
            "C7 still lacks crates.io publish/readback, external-machine install, full write-set audit, and external developer feedback.",
        ],
        "provenance": {
            "generator": rel(Path(__file__).resolve()),
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "llm_called": False,
            "subagent_review_used": True,
            "participant_responses_added": 0,
            "human_labels_added": 0,
            "raw_trace_read": False,
            "source_hashes": source_hashes([*TEXT_SOURCES.values(), *JSON_SOURCES.values()]),
        },
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    review = payload["subagent_review"]
    lines = [
        "# R267 Post-R266 OSDI Review Gate",
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
        "R267 is review hygiene only. It adds no participant responses, no human labels, and no weak-accept support.",
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
            "## Claim Verdict",
            "",
            "| Claim | Verdict |",
            "|-------|---------|",
        ]
    )
    for claim, verdict in review["claim_verdict"].items():
        lines.append(f"| `{claim}` | {verdict} |")

    next_exp = review["first_next_experiment"]
    lines.extend(
        [
            "",
            "## First Next Experiment",
            "",
            f"- Name: `{next_exp['name']}`.",
            f"- Private input: `{next_exp['private_input']}`.",
            f"- Preflight: `{next_exp['preflight_command']}`.",
            f"- Score: `{next_exp['score_command']}`.",
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
    print(json.dumps({"status": payload["status"], "checks_passed": payload["checks_passed"], "checks_total": payload["checks_total"]}, indent=2))
    return payload


if __name__ == "__main__":
    run()
