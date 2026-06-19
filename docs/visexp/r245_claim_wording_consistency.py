#!/usr/bin/env python3
"""R245: post-R244 claim wording consistency audit.

This is an audit artifact, not new outcome evidence. It checks that current
paper/docs wording remains aligned with the strongest machine-readable gates
after R238/R240/R242-R244, and records that R219 is now a useful older board
with post-R219 addenda rather than the final machine-readable claim board.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
OUT_DIR = SCRIPT_DIR / "out"
DEFAULT_OUT_DIR = OUT_DIR / "claim-wording-consistency-r245"

SOURCE_JSON = {
    "r184_weak_accept": OUT_DIR / "weak-accept-gate-r184.json",
    "r195_human_pipeline": OUT_DIR / "human-evidence-pipeline-r195.json",
    "r219_claim_readiness": OUT_DIR / "claim-readiness-r219" / "claim-readiness-r219.json",
    "r238_agent_execution_witness": OUT_DIR
    / "agent-execution-witness-network-capture-r238"
    / "agent-execution-witness-network-capture-r238.json",
    "r240_lineage_guard": OUT_DIR / "lineage-guard-r240" / "lineage-guard-r240.json",
    "r242_contract_smoke": OUT_DIR
    / "human-evidence-contract-r242"
    / "human-evidence-contract-r242.json",
    "r243_collection_kit": OUT_DIR / "human-evidence-collection-kit-r243" / "collection-kit-r243.json",
    "r244_export_smoke": OUT_DIR
    / "human-evidence-collection-kit-export-smoke-r244"
    / "collection-kit-export-smoke-r244.json",
}

SOURCE_TEXT = {
    "claim_verdict": SCRIPT_DIR / "CLAIM_VERDICT.md",
    "experiment_audit": SCRIPT_DIR / "EXPERIMENT_AUDIT.md",
    "followup_plan": SCRIPT_DIR / "FOLLOWUP_PLAN.md",
    "results_summary": SCRIPT_DIR / "RESULTS_SUMMARY.md",
    "paper": SCRIPT_DIR / "paper" / "main.tex",
}

POST_R219_ARTIFACTS = {
    "r238_agent_execution_witness",
    "r240_lineage_guard",
    "r242_contract_smoke",
    "r243_collection_kit",
    "r244_export_smoke",
}

FORBIDDEN_STRINGS = [
    "weak_accept_supported=true",
    "developer utility supported",
    "tag adequacy supported",
    "semantic correctness proven",
    "human evidence supported",
]

CONTEXTUAL_FORBIDDEN_STRINGS = [
    "c5_supported=true",
    "c6_adequacy_supported=true",
]

ALLOW_CONTEXT_WORDS = [
    "after",
    "gate",
    "if",
    "only if",
    "produce",
    "requires",
    "required",
    "threshold",
    "until",
]

PAPER_REQUIRED_PATTERNS = {
    "weak_accept_boundary": r"不到 OSDI weak accept|not OSDI weak accept",
    "c5_zero_outcome": r"0 个参与者响应|0 participant responses|尚无 participant responses",
    "c6_zero_outcome": r"0 个人工标签|0 final adequacy labels|human labels remain missing",
    "r244_no_inbox": r"R244.*不进入 R195 inbox|R244.*not\s+the\s+R195\s+inbox",
    "mechanism_not_completed_artifact": r"supported mechanism plus partial systems artifact",
}

DOC_REQUIRED_PATTERNS = {
    "claim_verdict": {
        "r244_boundary": r"R244 addendum",
        "r244_no_c5_c6": r"cannot support C5 or C6|不能支持 C5",
    },
    "experiment_audit": {
        "r244_not_outcome": r"R244 collection-kit export smoke is not outcome evidence",
        "c5_c6_blockers": r"C5 requires .*participant responses.*C6 requires .*human labels",
    },
    "followup_plan": {
        "r244_boundary": r"R244 smoke-tests",
        "r244_no_c5_c6": r"still does not satisfy C5/C6|仍不满足 C5/C6",
    },
    "results_summary": {
        "r244_summary": r"R244 smoke-tests",
        "r244_not_inbox": r"not\s+the\s+R195\s+inbox|不进入 R195 inbox",
    },
}


def rel(path: Path | None) -> str | None:
    if path is None:
        return None
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
        raise FileNotFoundError(f"missing source artifact: {rel(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"missing source text: {rel(path)}")
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def false_gate_values(mapping: dict[str, Any], keys: list[str]) -> dict[str, bool]:
    return {key: bool(mapping.get(key)) is False for key in keys}


def check_required_patterns(texts: dict[str, str]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    paper = texts["paper"]
    for name, pattern in PAPER_REQUIRED_PATTERNS.items():
        checks.append(
            {
                "scope": "paper",
                "name": name,
                "pattern": pattern,
                "passed": re.search(pattern, paper, re.IGNORECASE | re.DOTALL) is not None,
            }
        )
    for doc_name, patterns in DOC_REQUIRED_PATTERNS.items():
        text = texts[doc_name]
        for name, pattern in patterns.items():
            checks.append(
                {
                    "scope": doc_name,
                    "name": name,
                    "pattern": pattern,
                    "passed": re.search(pattern, text, re.IGNORECASE | re.DOTALL) is not None,
                }
            )
    return checks


def scan_forbidden(texts: dict[str, str]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for name, text in texts.items():
        lowered = text.lower()
        for token in FORBIDDEN_STRINGS:
            if token in lowered:
                hits.append({"source": name, "token": token})
        for token in CONTEXTUAL_FORBIDDEN_STRINGS:
            for line_no, line in enumerate(lowered.splitlines(), start=1):
                if token not in line:
                    continue
                if any(word in line for word in ALLOW_CONTEXT_WORDS):
                    continue
                hits.append({"source": name, "token": token, "line": str(line_no)})
    return hits


def build_evidence_checks(artifacts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    r184 = artifacts["r184_weak_accept"]
    r195 = artifacts["r195_human_pipeline"]
    r238 = artifacts["r238_agent_execution_witness"]
    r240 = artifacts["r240_lineage_guard"]
    r242 = artifacts["r242_contract_smoke"]
    r243 = artifacts["r243_collection_kit"]
    r244 = artifacts["r244_export_smoke"]

    r184_c5 = r184.get("c5_user_utility", {})
    r184_c6 = r184.get("c6_tag_adequacy", {})
    r184_overall = r184.get("overall", {})
    r195_gate = r195.get("claim_gate", {})
    r238_aggregate = r238.get("aggregate", {})
    r238_gate = r238.get("claim_gate", {})
    r240_checks = r240.get("checks", {})
    r242_checks = r242.get("checks", {})
    r243_gate = r243.get("claim_gate", {})
    r244_gate = r244.get("claim_gate", {})
    r244_checks = r244.get("checks", {})

    checks = [
        {
            "name": "r184_weak_accept_false",
            "passed": r184.get("status") == "not_weak_accept"
            and r184_overall.get("weak_accept_supported") is False,
            "observed": {
                "status": r184.get("status"),
                "weak_accept_supported": r184_overall.get("weak_accept_supported"),
            },
        },
        {
            "name": "r184_c5_empty",
            "passed": r184_c5.get("supported") is False
            and int(r184_c5.get("response_count", -1)) == 0
            and r184_c5.get("c5_supported") is False,
            "observed": {
                "status": r184_c5.get("status"),
                "response_count": r184_c5.get("response_count"),
                "c5_supported": r184_c5.get("c5_supported"),
            },
        },
        {
            "name": "r184_c6_empty",
            "passed": r184_c6.get("supported") is False
            and int(r184_c6.get("final_label_count", -1)) == 0
            and r184_c6.get("adequacy_supported") is False,
            "observed": {
                "status": r184_c6.get("status"),
                "final_label_count": r184_c6.get("final_label_count"),
                "adequacy_supported": r184_c6.get("adequacy_supported"),
            },
        },
        {
            "name": "r195_no_human_inputs",
            "passed": r195.get("status") == "awaiting_human_inputs"
            and not r195.get("operations")
            and all(
                false_gate_values(
                    r195_gate,
                    [
                        "c5_supported",
                        "c6_adequacy_supported",
                        "canonicalization_quality_supported",
                        "long_tail_promotion_review_supported",
                        "canonical_map_updated",
                    ],
                ).values()
            ),
            "observed": {"status": r195.get("status"), "claim_gate": r195_gate},
        },
        {
            "name": "r242_synthetic_only",
            "passed": r242.get("status") == "passed"
            and all(
                bool(r242_checks.get(key))
                for key in [
                    "synthetic_ready_all_operations_scored",
                    "synthetic_ready_claim_gates_remain_false",
                    "canonical_empty_gates_preserved",
                ]
            ),
            "observed": {"status": r242.get("status"), "checks": r242_checks},
        },
        {
            "name": "r243_collection_kit_no_outcomes",
            "passed": r243.get("status") == "collection_kit_ready_no_outcomes"
            and all(
                false_gate_values(
                    r243_gate,
                    [
                        "c5_supported",
                        "c6_adequacy_supported",
                        "canonicalization_quality_supported",
                        "long_tail_promotion_review_supported",
                        "canonical_map_updated",
                        "weak_accept_supported",
                    ],
                ).values()
            ),
            "observed": {"status": r243.get("status"), "claim_gate": r243_gate},
        },
        {
            "name": "r244_export_smoke_no_outcomes",
            "passed": r244.get("status") == "collection_kit_export_smoke_passed"
            and all(
                bool(r244_checks.get(key))
                for key in [
                    "browser_checks_ok",
                    "participant_export_count",
                    "labeler_export_count",
                    "merged_rows_ok",
                    "merged_participants_ok",
                    "labeler_cells_blank",
                    "leak_scan_ok",
                ]
            )
            and r244_checks.get("participant_export_count") == 5
            and r244_checks.get("labeler_export_count") == 6
            and all(
                false_gate_values(
                    r244_gate,
                    [
                        "c5_supported",
                        "c6_adequacy_supported",
                        "canonicalization_quality_supported",
                        "long_tail_promotion_review_supported",
                        "canonical_map_updated",
                        "weak_accept_supported",
                    ],
                ).values()
            ),
            "observed": {"status": r244.get("status"), "checks": r244_checks, "claim_gate": r244_gate},
        },
        {
            "name": "r238_still_partial_not_broad_network",
            "passed": r238.get("status") == "partial"
            and r238_aggregate.get("joined_target_network_effect_events") == 13
            and r238_aggregate.get("target_network_effect_events") == 16
            and r238_aggregate.get("negative_joined_effect_events") == 0
            and r238_gate.get("claude_launched_capture_gate") is False
            and r238_gate.get("r237_boundary_resolved") is False,
            "observed": {"status": r238.get("status"), "aggregate": r238_aggregate, "claim_gate": r238_gate},
        },
        {
            "name": "r240_regression_guard_only",
            "passed": r240.get("status") == "passed"
            and all(bool(value) for value in r240_checks.values())
            and "not live capture" in (r240.get("claim_boundary") or ""),
            "observed": {
                "status": r240.get("status"),
                "checks": r240_checks,
                "claim_boundary": r240.get("claim_boundary"),
            },
        },
    ]
    return checks


def r219_supersession(artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_keys = set((artifacts["r219_claim_readiness"].get("source_artifacts") or {}).keys())
    expected_to_be_absent = sorted(POST_R219_ARTIFACTS - source_keys)
    return {
        "status": "post_r219_addenda_required" if expected_to_be_absent else "current",
        "r219_status": artifacts["r219_claim_readiness"].get("status"),
        "missing_post_r219_sources": expected_to_be_absent,
        "interpretation": (
            "R219 remains a useful older readiness board, but R238/R240/R242-R244 "
            "must be read as post-R219 addenda or through R245."
        )
        if expected_to_be_absent
        else "R219 source list already includes the post-R219 artifacts checked here.",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# R245 Claim Wording Consistency Audit",
        "",
        f"Status: `{payload['status']}`",
        "",
        "R245 is an audit artifact. It does not create participant responses, human",
        "labels, merge-quality labels, or new lineage coverage.",
        "",
        "## Summary",
        "",
        f"- Hard evidence checks passed: {payload['summary']['hard_checks_passed']}/{payload['summary']['hard_checks_total']}",
        f"- Required wording checks passed: {payload['summary']['wording_checks_passed']}/{payload['summary']['wording_checks_total']}",
        f"- Forbidden strong-claim hits: {payload['summary']['forbidden_hit_count']}",
        f"- R219 supersession: `{payload['r219_supersession']['status']}`",
        "",
        "## Claim Boundary",
        "",
        "- C5 remains unsupported until real R142/R151 participant responses are scored.",
        "- C6 remains partial until real R124 adequacy labels, and optionally R190/R203 review labels, are scored.",
        "- R238 remains partial for broad agent-launched target-network capture.",
        "- R240 is regression-guard evidence, not new broad live-capture evidence.",
        "- R242/R243/R244 are contract/collection/export readiness evidence only.",
        "",
        "## Failed Checks",
        "",
    ]
    failed = [
        *[check for check in payload["hard_evidence_checks"] if not check["passed"]],
        *[check for check in payload["wording_checks"] if not check["passed"]],
    ]
    if failed:
        for check in failed:
            lines.append(f"- `{check.get('name')}` in `{check.get('scope', 'evidence')}`")
    else:
        lines.append("- None.")

    lines.extend(["", "## Source Artifacts", ""])
    for name, info in payload["source_artifacts"].items():
        lines.append(f"- `{name}`: `{info['path']}`")
    lines.append("")
    return "\n".join(lines)


def run(out_dir: Path) -> dict[str, Any]:
    artifacts = {name: read_json(path) for name, path in SOURCE_JSON.items()}
    texts = {name: read_text(path) for name, path in SOURCE_TEXT.items()}

    hard_checks = build_evidence_checks(artifacts)
    wording_checks = check_required_patterns(texts)
    forbidden_hits = scan_forbidden(texts)
    supersession = r219_supersession(artifacts)

    hard_ok = all(check["passed"] for check in hard_checks)
    wording_ok = all(check["passed"] for check in wording_checks)
    no_forbidden = not forbidden_hits
    status = (
        "claim_wording_consistency_passed_with_post_r219_addendum_note"
        if hard_ok and wording_ok and no_forbidden
        else "claim_wording_consistency_failed"
    )

    source_artifacts = {
        name: {"path": rel(path), "sha256": sha256_file(path)}
        for name, path in SOURCE_JSON.items()
    }
    source_texts = {
        name: {"path": rel(path), "sha256": sha256_file(path)}
        for name, path in SOURCE_TEXT.items()
    }

    payload: dict[str, Any] = {
        "schema_version": 1,
        "run_id": "R245",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "claim_boundary": (
            "R245 audits wording and source-gate consistency after R244. It does not "
            "upgrade C5/C6, does not create human evidence, and does not broaden C4."
        ),
        "summary": {
            "hard_checks_total": len(hard_checks),
            "hard_checks_passed": sum(1 for check in hard_checks if check["passed"]),
            "wording_checks_total": len(wording_checks),
            "wording_checks_passed": sum(1 for check in wording_checks if check["passed"]),
            "forbidden_hit_count": len(forbidden_hits),
            "weak_accept_supported": False,
            "c5_supported": False,
            "c6_adequacy_supported": False,
        },
        "claim_gate": {
            "reads_generated_artifacts_only": True,
            "raw_trace_read": False,
            "llm_called": False,
            "c5_supported": False,
            "c6_adequacy_supported": False,
            "canonicalization_quality_supported": False,
            "long_tail_promotion_review_supported": False,
            "weak_accept_supported": False,
        },
        "r219_supersession": supersession,
        "hard_evidence_checks": hard_checks,
        "wording_checks": wording_checks,
        "forbidden_hits": forbidden_hits,
        "source_artifacts": source_artifacts,
        "source_texts": source_texts,
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--porcelain"])),
            "script_sha256": sha256_file(Path(__file__)),
        },
    }

    out_json = out_dir / "claim-wording-consistency-r245.json"
    out_md = out_dir / "claim-wording-consistency-r245.md"
    write_json(out_json, payload)
    write_text(out_md, render_markdown(payload))
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = run(args.out_dir)
    print(f"wrote {rel(args.out_dir / 'claim-wording-consistency-r245.json')}")
    if payload["status"].endswith("_failed"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
