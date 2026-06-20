#!/usr/bin/env python3
"""R260: paper/evidence consistency gate after the R258/R259 collection kits.

This is audit hygiene only. It checks that the paper and evidence docs describe
R258/R259 as paper-scale collection logistics and static export smoke, not as
developer-utility, tag-adequacy, or weak-accept evidence.
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
DEFAULT_OUT_DIR = OUT_DIR / "paper-r259-consistency-r260"

R258_JSON = OUT_DIR / "human-evidence-paper-scale-bundle-r258" / "human-evidence-paper-scale-bundle-r258.json"
R259_JSON = OUT_DIR / "human-evidence-paper-scale-static-kit-r259" / "static-collection-kit-r259.json"
R245_JSON = OUT_DIR / "claim-wording-consistency-r245" / "claim-wording-consistency-r245.json"

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

FALSE_GATE_KEYS = [
    "c5_supported",
    "c6_adequacy_supported",
    "c6_supported",
    "canonicalization_quality_supported",
    "long_tail_promotion_review_supported",
    "outcome_evidence_added",
    "weak_accept_supported",
]

PAPER_PATTERNS = {
    "r258_unified_bundle": r"R258.*43-member|R258.*43 个成员|R258.*43-member tarball",
    "r259_static_forms": r"R259.*12 个 participant forms.*6 个 labeler forms",
    "r259_synthetic_shape": r"R259.*168 行 synthetic C5.*1,002 行 C6 synthetic",
    "r259_no_outcome": r"R259.*0 个真实响应.*0 个人工标签|R259.*no real participant responses.*no human labels",
    "c5_table_mentions_r259": r"C5 user utility.*R259 paper-scale static collection kit",
    "c6_table_mentions_r259": r"C6 tag adequacy.*R258/R259.*static forms|C6 tag adequacy.*R259 paper-scale static collection kit",
    "limitations_mentions_r259": r"R259.*static collection forms.*仍需要真实参与者响应|R259.*static collection forms.*still need",
}

DOC_PATTERNS = {
    "claim_verdict": {
        "r259_source": r"Additional R259 source",
        "r259_no_outcome": r"R259 adds static forms.*outcome_evidence_added=false",
    },
    "results_summary": {
        "r259_note": r"R259 turns the same paper-scale C5/C6 materials into static browser forms",
        "r259_false_gate": r"R259.*keeps C5/C6/weak-accept gates false|R259.*adds no real responses or labels",
    },
    "experiment_audit": {
        "r259_audit": r"R259",
        "r259_not_outcome": r"not outcome evidence|no outcome evidence",
    },
    "followup_plan": {
        "r259_next_action": r"human-evidence-paper-scale-static-kit-r259",
        "real_returns_required": r"real C5/C6 returns|真实",
    },
    "state": {
        "latest_r259": r"Latest R259 artifact",
        "r259_gate_note": r"Paper-scale static collection kit note",
    },
}

FORBIDDEN_STRINGS = [
    "r259 supports c5",
    "r259 supports c6",
    "r259 proves developer utility",
    "r259 proves tag adequacy",
]

CONTEXTUAL_FORBIDDEN_STRINGS = [
    "c5_supported=true",
    "c6_supported=true",
    "c6_adequacy_supported=true",
    "weak_accept_supported=true",
]

ALLOW_CONTEXT_WORDS = [
    "unless",
    "only if",
    "requires",
    "required",
    "threshold",
    "decision gate",
    "if ",
    "若",
    "除非",
    "需要",
]


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
        raise FileNotFoundError(f"missing source artifact: {rel(path)}")
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


def false_gate_check(name: str, gate: dict[str, Any]) -> dict[str, Any]:
    observed = {key: gate.get(key) for key in FALSE_GATE_KEYS}
    return {
        "name": name,
        "passed": all(observed[key] is False for key in FALSE_GATE_KEYS)
        and gate.get("requires_real_human_returns") is True,
        "observed": observed | {"requires_real_human_returns": gate.get("requires_real_human_returns")},
    }


def regex_check(scope: str, name: str, pattern: str, text: str) -> dict[str, Any]:
    return {
        "scope": scope,
        "name": name,
        "pattern": pattern,
        "passed": re.search(pattern, text, re.IGNORECASE | re.DOTALL) is not None,
    }


def scan_forbidden(texts: dict[str, str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for source, text in texts.items():
        lowered = text.lower()
        for token in FORBIDDEN_STRINGS:
            if token in lowered:
                hits.append({"source": source, "token": token})
        for token in CONTEXTUAL_FORBIDDEN_STRINGS:
            for line_no, line in enumerate(lowered.splitlines(), start=1):
                if token not in line:
                    continue
                if any(word in line for word in ALLOW_CONTEXT_WORDS):
                    continue
                hits.append({"source": source, "token": token, "line": line_no})
    return hits


def build_checks(r258: dict[str, Any], r259: dict[str, Any], r245: dict[str, Any], texts: dict[str, str]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    r258_gate = r258.get("claim_gate", {})
    r259_gate = r259.get("claim_gate", {})
    r259_counts = r259.get("counts", {})
    r259_checks = r259.get("checks", {})
    r259_provenance = r259.get("provenance", {})

    checks.extend(
        [
            {
                "name": "r258_bundle_ready_no_outcomes",
                "passed": r258.get("status") == "paper_scale_human_evidence_bundle_ready_no_outcomes"
                and r258_gate.get("outcome_evidence_added") is False
                and r258_gate.get("weak_accept_supported") is False,
                "observed": {
                    "status": r258.get("status"),
                    "outcome_evidence_added": r258_gate.get("outcome_evidence_added"),
                    "weak_accept_supported": r258_gate.get("weak_accept_supported"),
                },
            },
            false_gate_check("r258_claim_gates_remain_false", r258_gate),
            {
                "name": "r259_static_kit_passed",
                "passed": r259.get("status") == "paper_scale_static_collection_kit_passed"
                and bool(r259_checks)
                and all(value is True for value in r259_checks.values()),
                "observed": {
                    "status": r259.get("status"),
                    "check_count": len(r259_checks),
                    "failed_checks": [key for key, value in r259_checks.items() if value is not True],
                },
            },
            {
                "name": "r259_expected_counts",
                "passed": r259_counts.get("participant_forms") == 12
                and r259_counts.get("labeler_forms") == 6
                and r259_counts.get("coordinator_forms") == 1
                and r259_counts.get("participant_response_rows") == 168
                and r259_counts.get("labeler_rows_total") == 1002,
                "observed": {
                    "participant_forms": r259_counts.get("participant_forms"),
                    "labeler_forms": r259_counts.get("labeler_forms"),
                    "coordinator_forms": r259_counts.get("coordinator_forms"),
                    "participant_response_rows": r259_counts.get("participant_response_rows"),
                    "labeler_rows_total": r259_counts.get("labeler_rows_total"),
                },
            },
            false_gate_check("r259_claim_gates_remain_false", r259_gate),
            {
                "name": "r259_no_new_human_or_llm_evidence",
                "passed": r259_provenance.get("participant_responses_added") == 0
                and r259_provenance.get("human_labels_added") == 0
                and r259_provenance.get("llm_called") is False
                and r259_provenance.get("raw_trace_read") is False,
                "observed": {
                    "participant_responses_added": r259_provenance.get("participant_responses_added"),
                    "human_labels_added": r259_provenance.get("human_labels_added"),
                    "llm_called": r259_provenance.get("llm_called"),
                    "raw_trace_read": r259_provenance.get("raw_trace_read"),
                },
            },
            {
                "name": "r245_still_keeps_claim_boundary",
                "passed": str(r245.get("status", "")).startswith("claim_wording_consistency_passed")
                and r245.get("claim_gate", {}).get("weak_accept_supported") is False
                and r245.get("claim_gate", {}).get("c5_supported") is False
                and r245.get("claim_gate", {}).get("c6_adequacy_supported") is False,
                "observed": {
                    "status": r245.get("status"),
                    "claim_gate": r245.get("claim_gate", {}),
                },
            },
        ]
    )

    paper = texts["paper"]
    for name, pattern in PAPER_PATTERNS.items():
        checks.append(regex_check("paper", name, pattern, paper))

    for source, patterns in DOC_PATTERNS.items():
        text = texts[source]
        for name, pattern in patterns.items():
            checks.append(regex_check(source, name, pattern, text))

    forbidden_hits = scan_forbidden(texts)
    checks.append(
        {
            "name": "forbidden_overclaim_strings_absent",
            "passed": not forbidden_hits,
            "observed": {"hits": forbidden_hits},
        }
    )

    return checks


def build_summary(out_dir: Path) -> dict[str, Any]:
    r258 = read_json(R258_JSON)
    r259 = read_json(R259_JSON)
    r245 = read_json(R245_JSON)
    texts = {name: read_text(path) for name, path in TEXT_SOURCES.items()}
    checks = build_checks(r258, r259, r245, texts)
    passed = all(check["passed"] for check in checks)

    source_paths = [R258_JSON, R259_JSON, R245_JSON, *TEXT_SOURCES.values()]
    summary = {
        "schema_version": 1,
        "run_id": "R260",
        "status": "paper_r259_consistency_passed" if passed else "paper_r259_consistency_failed",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_command": "python3 docs/visexp/r260_paper_r259_consistency.py",
        "source_artifacts": {
            "r258": rel(R258_JSON),
            "r259": rel(R259_JSON),
            "r245": rel(R245_JSON),
            "texts": {name: rel(path) for name, path in TEXT_SOURCES.items()},
        },
        "r259_counts": r259.get("counts", {}),
        "claim_gate": {
            "c5_supported": False,
            "c6_adequacy_supported": False,
            "c6_supported": False,
            "canonicalization_quality_supported": False,
            "long_tail_promotion_review_supported": False,
            "outcome_evidence_added": False,
            "requires_real_human_returns": True,
            "weak_accept_supported": False,
        },
        "claim_boundary": (
            "R260 audits paper/docs consistency after R258/R259. It adds no "
            "participant responses, no human labels, no model labels, and no "
            "new outcome evidence."
        ),
        "checks": checks,
        "check_count": len(checks),
        "passed_checks": sum(1 for check in checks if check["passed"]),
        "failed_checks": [check for check in checks if not check["passed"]],
        "provenance": {
            "generator": rel(Path(__file__)),
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--porcelain"])),
            "participant_responses_added": 0,
            "human_labels_added": 0,
            "llm_called": False,
            "raw_trace_read": False,
            "source_hashes": source_hashes(source_paths),
        },
    }

    json_path = out_dir / "paper-r259-consistency-r260.json"
    md_path = out_dir / "paper-r259-consistency-r260.md"
    write_json(json_path, summary)
    write_text(md_path, render_markdown(summary))
    return summary


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# R260 Paper/R259 Consistency Audit",
        "",
        f"Status: `{summary['status']}`",
        "",
        "R260 checks that R258/R259 are described as collection logistics only.",
        "",
        "## R259 Counts",
        "",
    ]
    counts = summary["r259_counts"]
    for key in [
        "participant_forms",
        "labeler_forms",
        "coordinator_forms",
        "participant_response_rows",
        "labeler_rows_total",
    ]:
        lines.append(f"- {key}: `{counts.get(key)}`")
    lines.extend(["", "## Checks", ""])
    for check in summary["checks"]:
        lines.append(f"- {check['name']}: `{check['passed']}`")
    lines.extend(
        [
            "",
            "## Claim Gate",
            "",
            "- weak_accept_supported: `False`",
            "- c5_supported: `False`",
            "- c6_supported: `False`",
            "- outcome_evidence_added: `False`",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_summary(args.out_dir)
    if summary["status"] != "paper_r259_consistency_passed":
        failed = ", ".join(check["name"] for check in summary["failed_checks"])
        raise SystemExit(f"R260 consistency audit failed: {failed}")
    print(
        f"R260 consistency audit passed: {summary['passed_checks']}/{summary['check_count']} checks"
    )


if __name__ == "__main__":
    main()
