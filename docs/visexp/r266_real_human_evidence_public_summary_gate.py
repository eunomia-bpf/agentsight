#!/usr/bin/env python3
"""R266: publish only aggregate real-human evidence from private R195 outputs.

R195 is allowed to score private participant responses and label sheets. This
gate is the promotion boundary: it reads an R195 summary from a private/external
location, rejects synthetic or public-repo inputs, and writes a public-safe
aggregate summary that can be cited by the paper without leaking raw responses,
label rows, notes, commands, or private file paths.
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
OUT_ROOT = SCRIPT_DIR / "out"

DEFAULT_PRIVATE_R195_JSON = (
    REPO_ROOT
    / "private"
    / "completed-paper-scale-r264"
    / "r195-scored"
    / "human-evidence-pipeline-r195.json"
)
DEFAULT_OUT_DIR = OUT_ROOT / "human-evidence-public-summary-r266"

R195_SUPPORTED_STATUSES = {
    "scored_human_inputs_with_supported_gate",
    "scored_human_inputs_no_supported_gate",
}
R195_NOT_READY_STATUSES = {
    "awaiting_human_inputs",
    "partial_human_inputs",
    "ready_to_score_no_run",
    "needs_adjudication",
    "scoring_failed",
}
SYNTHETIC_PATH_MARKERS = {
    "human-evidence-contract-r242",
    "human-return-safety-r263",
    "human-adjudication-r265",
    "r242",
    "r244",
    "r259",
    "r263",
    "r265",
    "synthetic",
}
FORBIDDEN_OUTPUT_KEYS = {
    "cmd",
    "commands",
    "response_json",
    "notes",
    "labeler_1_notes",
    "labeler_2_notes",
    "adjudication_notes",
    "scored_rows",
    "rows",
    "stdout_tail",
    "stderr_tail",
    "path",
    "input_path",
    "output_path",
}


def rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def sha256_file(path: Path) -> str | None:
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def source_kind(path: Path) -> str:
    resolved = path.resolve()
    repo = REPO_ROOT.resolve()
    try:
        relative = resolved.relative_to(repo)
    except ValueError:
        return "external"
    if relative.parts and relative.parts[0] == "private":
        return "private_repo"
    return "public_repo"


def source_label(kind: str, exists: bool) -> str:
    if not exists:
        return "not_present"
    if kind == "private_repo":
        return "private_repo_redacted"
    if kind == "external":
        return "external_redacted"
    return "public_repo_redacted"


def resolve_output_path(value: str | None) -> Path | None:
    if not value:
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return REPO_ROOT / candidate


def safe_get(payload: dict[str, Any], *keys: str) -> Any:
    cursor: Any = payload
    for key in keys:
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(key)
    return cursor


def selected_mapping(mapping: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {key: mapping.get(key) for key in keys if key in mapping}


def summarize_label_summary(summary: dict[str, Any], kind: str) -> dict[str, Any]:
    common = [
        "packet_row_count",
        "candidate_tag_count",
        "final_label_count",
        "strong_final_label_count",
        "unlabeled_count",
        "single_label_count",
        "unadjudicated_disagreement_count",
        "both_labeler_count",
        "paired_label_coverage_pct",
        "inter_labeler_agreement_pct",
        "cohen_kappa",
        "final_label_counts",
        "final_source_counts",
        "label_state_counts",
    ]
    by_kind = {
        "r124": [
            "candidate_tag_coverage_pct",
            "adequate_share_pct",
            "generic_noisy_share_pct",
            "misleading_share_pct",
        ],
        "r190": [
            "audit_row_count",
            "overmerge_rate_pct",
            "undermerge_rate_pct",
            "unclear_share_pct",
            "by_audit_type",
        ],
        "r203": [
            "promotion_row_count",
            "grammar_valid_rows",
            "changed_from_raw_rows",
            "promotion_decision_count",
            "unclear_share_pct",
        ],
    }
    return selected_mapping(summary, common + by_kind.get(kind, []))


def summarize_r142_child(child: dict[str, Any]) -> dict[str, Any]:
    analysis = child.get("claim_analysis") or {}
    paper = analysis.get("paper_scale_primary") or {}
    comparisons = []
    for row in paper.get("comparisons") or []:
        comparisons.append(
            selected_mapping(
                row,
                [
                    "baseline_condition",
                    "role_filter",
                    "task_pair_count",
                    "model_row_count",
                    "model_participant_count",
                    "model_task_count",
                    "model_accuracy_delta_pp",
                    "accuracy_holm_p_value",
                    "median_task_time_reduction_pct",
                    "model_time_reduction_pct",
                    "time_holm_p_value",
                    "model_false_positive_delta_pp",
                    "mean_false_positive_delta_pp",
                ],
            )
        )
    return {
        "status": child.get("status"),
        "participant_count": child.get("participant_count"),
        "response_count": child.get("response_count"),
        "task_count": child.get("task_count"),
        "response_contract": selected_mapping(
            child.get("response_contract") or {},
            [
                "valid",
                "assignment_row_count",
                "response_row_count",
                "scorable_row_count",
                "placeholder_row_count",
                "complete_assigned_rows",
                "template_only",
            ],
        ),
        "claim_analysis_status": analysis.get("status"),
        "paper_scale_primary": {
            "successful_comparison_count": paper.get("successful_comparison_count"),
            "model_ready": paper.get("model_ready"),
            "holm_family": paper.get("holm_family"),
            "statistical_model": paper.get("statistical_model"),
            "comparisons": comparisons,
        },
        "claim_gate": analysis.get("claim_gate") or {},
    }


def summarize_operations(r195: dict[str, Any], source_json: Path) -> dict[str, Any]:
    operations = r195.get("operations") or {}
    public: dict[str, Any] = {}
    for name in ("r124", "r190", "r203"):
        op = operations.get(name) or {}
        public[name] = {
            "status": op.get("status"),
            "join_status": op.get("join_status"),
            "claim_gate": op.get("claim_gate") or {},
            "summary": summarize_label_summary(op.get("summary") or op.get("join_summary") or {}, name),
        }
    r142 = operations.get("r142") or {}
    r142_summary: dict[str, Any] = {
        "status": r142.get("status"),
        "participant_count": r142.get("participant_count"),
        "response_count": r142.get("response_count"),
        "claim_gate": r142.get("claim_gate") or {},
    }
    child_path = resolve_output_path(safe_get(r142, "outputs", "result_json"))
    if child_path and child_path.exists():
        try:
            r142_summary["child_summary"] = summarize_r142_child(read_json(child_path))
            r142_summary["child_summary_sha256"] = sha256_file(child_path)
        except Exception as exc:
            r142_summary["child_summary_error"] = str(exc)
    public["r142"] = r142_summary
    public["operation_statuses"] = {
        name: (operations.get(name) or {}).get("status")
        for name in sorted(operations)
    }
    public["source_summary_sha256"] = sha256_file(source_json)
    return public


def forbidden_output_key_hits(value: Any, prefix: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}"
            if key in FORBIDDEN_OUTPUT_KEYS:
                hits.append(child_prefix)
            hits.extend(forbidden_output_key_hits(child, child_prefix))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            hits.extend(forbidden_output_key_hits(child, f"{prefix}[{idx}]"))
    return hits


def r195_safety_status(r195: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if r195.get("run_id") != "R195":
        reasons.append("not_r195_payload")
    safety = safe_get(r195, "input_contract", "safety") or {}
    if safety.get("unsafe") or safety.get("status") == "unsafe_return_inputs":
        reasons.append("r195_safety_unsafe")
    if safe_get(r195, "input_contract", "human_return_content_status") == "known_synthetic_or_forbidden_marker":
        reasons.append("known_synthetic_or_forbidden_marker")
    return not reasons, reasons


def path_marker_status(path: Path) -> tuple[bool, list[str]]:
    text = rel(path) or str(path)
    hits = sorted(marker for marker in SYNTHETIC_PATH_MARKERS if marker in text)
    return not hits, hits


def public_input_status(kind: str) -> tuple[bool, str | None]:
    if kind == "public_repo":
        return False, "public_repo_r195_input_not_promotable"
    return True, None


def claim_gate_from_r195(r195: dict[str, Any], accepted: bool) -> dict[str, Any]:
    source_gate = r195.get("claim_gate") or {}
    c5 = accepted and bool(source_gate.get("c5_supported"))
    c6 = accepted and bool(source_gate.get("c6_adequacy_supported"))
    canonical = accepted and bool(source_gate.get("canonicalization_quality_supported"))
    promotion = accepted and bool(source_gate.get("long_tail_promotion_review_supported"))
    map_updated = accepted and bool(source_gate.get("canonical_map_updated"))
    return {
        "c5_supported": c5,
        "c6_adequacy_supported": c6,
        "canonicalization_quality_supported": canonical,
        "long_tail_promotion_review_supported": promotion,
        "canonical_map_updated": map_updated,
        "weak_accept_supported": bool(c5 and c6),
        "public_claim_update_allowed": bool(accepted and (c5 or c6 or canonical or promotion)),
        "requires_real_human_returns": not bool(c5 and c6),
    }


def status_for(
    *,
    exists: bool,
    kind_ok: bool,
    path_ok: bool,
    r195_ok: bool,
    r195_status: str | None,
    content_ready: bool,
    accepted: bool,
    gate: dict[str, Any],
) -> str:
    if not exists:
        return "awaiting_private_scored_r195"
    if not kind_ok:
        return "public_repo_r195_input_not_promotable"
    if not path_ok or not r195_ok:
        return "unsafe_or_synthetic_scored_input"
    if r195_status in R195_NOT_READY_STATUSES:
        if r195_status == "needs_adjudication":
            return "needs_adjudication_before_public_summary"
        return "r195_not_ready_for_public_summary"
    if r195_status not in R195_SUPPORTED_STATUSES:
        return "unknown_r195_status"
    if not content_ready:
        return "r195_not_ready_for_public_summary"
    if accepted and gate["weak_accept_supported"]:
        return "public_summary_ready_with_weak_accept_gate"
    if accepted and gate["public_claim_update_allowed"]:
        return "public_summary_ready_with_partial_supported_gate"
    return "public_summary_ready_no_supported_gate"


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    source = args.r195_json
    exists = source.exists()
    kind = source_kind(source)
    kind_ok, kind_reason = public_input_status(kind)
    path_ok, path_markers = path_marker_status(source)
    r195: dict[str, Any] = {}
    parse_error = None
    r195_ok = False
    r195_reasons: list[str] = []
    if exists:
        try:
            r195 = read_json(source)
            r195_ok, r195_reasons = r195_safety_status(r195)
        except Exception as exc:
            parse_error = str(exc)
            r195_reasons = ["invalid_json"]
    else:
        r195_reasons = ["missing_private_scored_r195"]

    r195_status = r195.get("status") if isinstance(r195, dict) else None
    content_status = safe_get(r195, "input_contract", "human_return_content_status")
    content_ready = content_status == "has_filled_values"
    accepted = bool(
        exists
        and kind_ok
        and path_ok
        and r195_ok
        and content_ready
        and r195_status in R195_SUPPORTED_STATUSES
    )
    gate = claim_gate_from_r195(r195, accepted)
    status = status_for(
        exists=exists,
        kind_ok=kind_ok,
        path_ok=path_ok,
        r195_ok=r195_ok,
        r195_status=r195_status,
        content_ready=content_ready,
        accepted=accepted,
        gate=gate,
    )
    operations = summarize_operations(r195, source) if exists and isinstance(r195, dict) else {}
    public_summary = {
        "schema_version": 1,
        "run_id": "R266",
        "status": status,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": {
            "kind": kind,
            "display": source_label(kind, exists),
            "exists": exists,
            "sha256": sha256_file(source),
            "r195_status": r195_status,
            "r195_run_id": r195.get("run_id") if isinstance(r195, dict) else None,
            "parse_error": parse_error,
        },
        "checks": {
            "input_is_private_or_external": kind_ok,
            "input_kind_rejection_reason": kind_reason,
            "path_has_no_synthetic_markers": path_ok,
            "synthetic_path_marker_hits": path_markers,
            "r195_payload_safety_passed": r195_ok,
            "r195_payload_safety_reasons": r195_reasons,
            "r195_content_has_filled_values": content_ready,
            "r195_status_supported_for_public_summary": r195_status in R195_SUPPORTED_STATUSES,
            "public_output_excludes_raw_fields": True,
        },
        "r195_public_aggregate": {
            "input_contract_status": content_status,
            "readiness_overall_status": safe_get(r195, "input_contract", "readiness", "overall_status"),
            "claim_gate_from_r195": r195.get("claim_gate") if isinstance(r195, dict) else {},
            "operations": operations,
        },
        "claim_gate": gate,
        "claim_boundary": (
            "R266 is only a public promotion gate for private R195 aggregate results. "
            "It cannot create participant responses, human labels, adjudication decisions, "
            "or a canonical-map update. Public-repo, synthetic, unsafe, awaiting, partial, "
            "or needs-adjudication R195 inputs keep all promoted claim gates false."
        ),
        "privacy_boundary": {
            "raw_rows_exported": False,
            "commands_exported": False,
            "private_paths_exported": False,
            "notes_exported": False,
            "source_paths_redacted": True,
        },
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script": rel(Path(__file__).resolve()),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }
    key_hits = forbidden_output_key_hits(public_summary)
    public_summary["checks"]["public_output_forbidden_key_hits"] = key_hits
    public_summary["checks"]["public_output_excludes_raw_fields"] = not key_hits
    if key_hits and status.startswith("public_summary_ready"):
        public_summary["status"] = "public_summary_privacy_violation"
        public_summary["claim_gate"] = claim_gate_from_r195(r195, False)
    return public_summary


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    gate = payload["claim_gate"]
    checks = payload["checks"]
    lines = [
        "# R266 Real Human Evidence Public Summary Gate",
        "",
        f"Status: `{payload['status']}`",
        f"Source kind: `{payload['source']['kind']}`",
        f"R195 status: `{payload['source']['r195_status']}`",
        "",
        "## Claim Gates",
        "",
        f"- C5 supported: `{gate['c5_supported']}`.",
        f"- C6 adequacy supported: `{gate['c6_adequacy_supported']}`.",
        f"- Canonicalization quality supported: `{gate['canonicalization_quality_supported']}`.",
        f"- Long-tail promotion review supported: `{gate['long_tail_promotion_review_supported']}`.",
        f"- Weak accept supported: `{gate['weak_accept_supported']}`.",
        f"- Public claim update allowed: `{gate['public_claim_update_allowed']}`.",
        "",
        "## Safety Checks",
        "",
        f"- Private or external input: `{checks['input_is_private_or_external']}`.",
        f"- Synthetic path markers: `{checks['synthetic_path_marker_hits']}`.",
        f"- R195 payload safety passed: `{checks['r195_payload_safety_passed']}`.",
        f"- Raw-field privacy scan passed: `{checks['public_output_excludes_raw_fields']}`.",
        "",
        "## Aggregate Operations",
        "",
    ]
    operations = payload["r195_public_aggregate"].get("operations") or {}
    statuses = operations.get("operation_statuses") or {}
    if not statuses:
        lines.append("No private scored R195 aggregate is available yet.")
    else:
        for name, status in sorted(statuses.items()):
            lines.append(f"- `{name}`: `{status}`.")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            payload["claim_boundary"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    payload = build_payload(args)
    out_json = args.out_dir / "human-evidence-public-summary-r266.json"
    out_md = args.out_dir / "human-evidence-public-summary-r266.md"
    write_json(out_json, payload)
    write_markdown(out_md, payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "claim_gate": payload["claim_gate"],
                "out_json": rel(out_json),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r195-json", type=Path, default=DEFAULT_PRIVATE_R195_JSON)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
