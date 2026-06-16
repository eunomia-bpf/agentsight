#!/usr/bin/env python3
"""Reviewer-facing claim/RQ readiness gate for AgentFlame.

R219 is an audit artifact, not new outcome evidence. It reads already generated
public/research summaries and records which OSDI claims are supported, partial,
or still blocked. It must not read raw agent traces or call any model.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "claim-readiness-r219"


SOURCE_PATHS = {
    "r170_full_history": "docs/visexp/out/full-history-r170.json",
    "r180_model_benchmarks": "docs/visexp/out/model-benchmarks-r180.json",
    "r131_semantic_ablation": "docs/visexp/out/semantic-ablation-r131.json",
    "r114_live_record": "docs/visexp/out/live-record-r114.json",
    "r182_live_network": "docs/visexp/out/live-network-r182.json",
    "r184_weak_accept": "docs/visexp/out/weak-accept-gate-r184.json",
    "r195_human_pipeline": "docs/visexp/out/human-evidence-pipeline-r195.json",
    "r207_launch_readiness": "docs/visexp/out/human-evidence-launch-r207/human-evidence-launch-r207.json",
    "r160_artifact_usability": "docs/visexp/out/artifact-usability-r160.json",
    "r213_display_mode": "docs/visexp/out/display-mode-drilldown-r213/display-mode-drilldown-r213.json",
    "r214_long_tail_control": "docs/visexp/out/long-tail-control-r214/long-tail-control-r214.json",
    "r215_frontend_renderer": "docs/visexp/out/frontend-renderer-mode-r215/frontend-renderer-mode-r215.json",
    "r216_browser_dom": "docs/visexp/out/browser-dom-mode-r216/browser-dom-mode-r216.json",
    "r217_production_react": "docs/visexp/out/production-react-display-r217/production-react-display-r217.json",
    "r218_update_gate": "docs/visexp/out/display-map-update-gate-r218/display-map-update-gate-r218.json",
    "r124_tag_adequacy": "docs/visexp/out/tag-adequacy-results-r124.json",
    "r190_merge_quality": "docs/visexp/out/tag-consolidation-audit-r190/merge-risk-audit-results-r190.json",
    "r203_promotion_quality": "docs/visexp/out/long-tail-promotion-r203/long-tail-promotion-r203.json",
    "r142_user_task_results": "docs/visexp/out/user-task-results.json",
    "r200_community_smoke": "docs/visexp/out/community-smoke-r200.json",
    "r209_display_map": "docs/visexp/out/reversible-display-map-r209/reversible-display-map-r209.json",
    "r211_stack_examples": "docs/visexp/out/stack-examples-r211/stack-examples-r211.json",
    "r212_display_ablation": "docs/visexp/out/display-compaction-ablation-r212/display-compaction-ablation-r212.json",
}


CLAIM_FIELDS = [
    "claim",
    "verdict",
    "evidence_level",
    "primary_evidence",
    "blocking_gap",
    "next_gate",
]

RQ_FIELDS = [
    "rq",
    "verdict",
    "evidence_level",
    "primary_evidence",
    "falsifier_remaining",
    "next_gate",
]

NEXT_FIELDS = [
    "priority",
    "run_id",
    "claim",
    "block",
    "purpose",
    "command_or_input",
    "oracle",
    "result_path",
]


def repo_path(relative: str) -> Path:
    return REPO_ROOT / relative


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json_required(relative: str) -> dict[str, Any]:
    path = repo_path(relative)
    if not path.exists():
        raise FileNotFoundError(f"required R219 source artifact is missing: {relative}")
    return json.loads(path.read_text(encoding="utf-8"))


def as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def percent(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(100.0 * numerator / denominator, 3)


def artifact_statuses(artifacts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    r170 = artifacts["r170_full_history"]
    r180 = artifacts["r180_model_benchmarks"]
    r114 = artifacts["r114_live_record"]
    r182 = artifacts["r182_live_network"]
    r184 = artifacts["r184_weak_accept"]
    r195 = artifacts["r195_human_pipeline"]
    r160 = artifacts["r160_artifact_usability"]
    r213 = artifacts["r213_display_mode"]
    r214 = artifacts["r214_long_tail_control"]
    r215 = artifacts["r215_frontend_renderer"]
    r216 = artifacts["r216_browser_dom"]
    r217 = artifacts["r217_production_react"]
    r218 = artifacts["r218_update_gate"]
    r124 = artifacts["r124_tag_adequacy"]
    r190 = artifacts["r190_merge_quality"]
    r203 = artifacts["r203_promotion_quality"]
    r142 = artifacts["r142_user_task_results"]

    r114_aggregate = r114.get("aggregate") or {}
    r114_tp = as_int(r114_aggregate.get("true_positives"))
    r114_fp = as_int(r114_aggregate.get("false_positives"))
    r114_fn = as_int(r114_aggregate.get("false_negatives"))
    r114_negative_joined = as_int(r114_aggregate.get("negative_joined_effect_events"))
    r114_negative_observed = as_int(r114_aggregate.get("negative_effect_events_observed"))

    r170_summary = r170.get("summary") or {}
    r180_aggregate = r180.get("aggregate") or {}
    r217_summary = r217.get("summary") or {}
    r218_summary = r218.get("summary") or {}
    r184_c5 = r184.get("c5_user_utility") or {}
    r184_c6 = r184.get("c6_tag_adequacy") or {}

    return {
        "r170_sessions": as_int(r170_summary.get("session_count")),
        "r170_system_observations": as_int(r170_summary.get("system_observations")),
        "r170_semantic_system_stacks": as_int(r170_summary.get("semantic_system_stacks")),
        "r180_total_runs": as_int(r180_aggregate.get("total_runs")),
        "r180_ok_runs": as_int(r180_aggregate.get("ok_runs")),
        "r180_exact_stable_fragments": as_int(r180_aggregate.get("exact_stable_fragments")),
        "r180_fragment_count": as_int(r180_aggregate.get("fragment_count")),
        "r114_status": r114.get("status"),
        "r114_precision_pct": percent(r114_tp, r114_tp + r114_fp),
        "r114_recall_pct": percent(r114_tp, r114_tp + r114_fn),
        "r114_negative_joined": r114_negative_joined,
        "r114_negative_observed": r114_negative_observed,
        "r182_status": r182.get("status"),
        "r184_status": r184.get("status"),
        "r195_status": r195.get("status"),
        "r160_status": r160.get("status"),
        "r213_status": r213.get("status"),
        "r214_status": r214.get("status"),
        "r215_status": r215.get("status"),
        "r216_status": r216.get("status"),
        "r142_status": r142.get("status"),
        "r124_status": r124.get("status"),
        "r190_status": r190.get("status"),
        "r203_status": r203.get("status"),
        "c5_supported": bool(r184_c5.get("supported")),
        "c5_participants": as_int(r184_c5.get("participant_count")),
        "c5_responses": as_int(r184_c5.get("response_count")),
        "c6_supported": bool(r184_c6.get("supported")),
        "c6_final_labels": as_int(r184_c6.get("final_label_count")),
        "r217_display_buckets": as_int(r217_summary.get("visible_bucket_count")),
        "r217_support": as_int(r217_summary.get("visible_total_support")),
        "r218_accepted_diff_rows": as_int(r218_summary.get("accepted_diff_rows")),
        "r218_rejected_rows": as_int(r218_summary.get("rejected_rows")),
        "r218_canonical_map_updated": bool(r218_summary.get("canonical_map_updated")),
    }


def claim_rows(status: dict[str, Any]) -> list[dict[str, str]]:
    c5_missing = status["c5_participants"] == 0 or status["c5_responses"] == 0
    c6_missing = status["c6_final_labels"] == 0
    return [
        {
            "claim": "C1 semantic folded stacks over real histories",
            "verdict": "supported",
            "evidence_level": "mechanism/full-local-history",
            "primary_evidence": (
                f"R170: {status['r170_sessions']} sessions, "
                f"{status['r170_system_observations']} system observations, "
                f"{status['r170_semantic_system_stacks']} semantic system stacks"
            ),
            "blocking_gap": "multi-repo generalization and public package remain C7 scope",
            "next_gate": "rerun only after parser/tagger changes",
        },
        {
            "claim": "C2 local one-word tagging feasibility",
            "verdict": "supported_for_syntax_latency",
            "evidence_level": "local-small-model-benchmark",
            "primary_evidence": (
                f"R180: {status['r180_ok_runs']}/{status['r180_total_runs']} valid outputs, "
                f"{status['r180_exact_stable_fragments']}/{status['r180_fragment_count']} exact-stable fragments"
            ),
            "blocking_gap": "human semantic adequacy is C6, not C2",
            "next_gate": "collect R124 labels before claiming adequacy",
        },
        {
            "claim": "C3 semantic partitioning and display mechanics",
            "verdict": "supported_as_mechanism",
            "evidence_level": "ablation/display-contract",
            "primary_evidence": (
                f"R217 production default display: {status['r217_display_buckets']} buckets, "
                f"{status['r217_support']} support; R218 accepted {status['r218_accepted_diff_rows']} "
                f"preview diffs and rejected {status['r218_rejected_rows']} unsafe rows"
            ),
            "blocking_gap": "visual drilldown, developer utility, and merge quality are not proven",
            "next_gate": "C5 participant study and R190/R203 human review labels",
        },
        {
            "claim": "C4 exact semantic-effect lineage",
            "verdict": "supported_for_fixed_command_mode_suite",
            "evidence_level": "controlled-live-lineage",
            "primary_evidence": (
                f"R114 status {status['r114_status']}: precision {status['r114_precision_pct']}%, "
                f"recall {status['r114_recall_pct']}%, negative joins "
                f"{status['r114_negative_joined']}/{status['r114_negative_observed']}; "
                f"R182 network status {status['r182_status']}"
            ),
            "blocking_gap": "target-specific network and cross-repo/full-history exact capture remain partial",
            "next_gate": "R191 target-specific network lineage hardening",
        },
        {
            "claim": "C5 developer utility",
            "verdict": "unsupported" if c5_missing else "partial_or_failed",
            "evidence_level": "launch_ready_no_outcomes",
            "primary_evidence": (
                f"R184/R195: {status['c5_participants']} participants, "
                f"{status['c5_responses']} responses, pipeline {status['r195_status']}"
            ),
            "blocking_gap": "real participant responses are missing",
            "next_gate": "collect and score R142 pilot responses through R195",
        },
        {
            "claim": "C6 tag adequacy and merge/promotion quality",
            "verdict": "partial_syntax_stability_only" if c6_missing else "partial_or_failed",
            "evidence_level": "protocol_ready_no_human_labels",
            "primary_evidence": (
                f"R124 {status['r124_status']}, R190 {status['r190_status']}, "
                f"R203 {status['r203_status']}, final adequacy labels {status['c6_final_labels']}"
            ),
            "blocking_gap": "independent adequacy, merge-risk, and promotion labels are missing",
            "next_gate": "collect R124/R190/R203 paired labels and score through R195",
        },
        {
            "claim": "C7 community/open-source usefulness",
            "verdict": "partial",
            "evidence_level": "local-public-safe-smoke",
            "primary_evidence": "R160 fixed-session smoke and R200 generated-fixture smoke pass",
            "blocking_gap": "no external fresh-clone run or external developer feedback",
            "next_gate": "fresh clone on another machine plus write-set/sanitization audit",
        },
    ]


def rq_rows(status: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "rq": "RQ1 feasibility/cost",
            "verdict": "supported",
            "evidence_level": "full-history plus local model benchmark",
            "primary_evidence": f"R170 full run and R180 {status['r180_ok_runs']}/{status['r180_total_runs']} valid model outputs",
            "falsifier_remaining": "parser/tagger changes could invalidate the run",
            "next_gate": "rerun after implementation changes only",
        },
        {
            "rq": "RQ2 semantic partitioning",
            "verdict": "supported_as_mechanism",
            "evidence_level": "ablation plus display artifacts",
            "primary_evidence": "R131/R211 show baseline collapse; R209-R218 show reversible display mechanics",
            "falsifier_remaining": "developer tasks may show no practical benefit",
            "next_gate": "R142 C5 outcomes",
        },
        {
            "rq": "RQ3 exact lineage",
            "verdict": "supported_for_fixed_command_mode_suite",
            "evidence_level": "controlled live AgentSight suite",
            "primary_evidence": f"R114 precision {status['r114_precision_pct']}%, recall {status['r114_recall_pct']}%",
            "falsifier_remaining": "target-specific network and arbitrary-history capture remain open",
            "next_gate": "R191 target-specific network suite",
        },
        {
            "rq": "RQ4 developer utility",
            "verdict": "unsupported",
            "evidence_level": "materials_ready_no_outcomes",
            "primary_evidence": f"R142/R187/R207 launch materials; {status['c5_responses']} scored responses",
            "falsifier_remaining": "semantic view may not improve accuracy/time or may increase false positives",
            "next_gate": "collect real R142 responses",
        },
        {
            "rq": "RQ5 tag adequacy",
            "verdict": "partial",
            "evidence_level": "syntax_stability_plus_empty_human_protocol",
            "primary_evidence": f"R180 syntax/stability; R124/R190/R203 human-label gates all {status['r124_status']}/{status['r190_status']}/{status['r203_status']}",
            "falsifier_remaining": "labels may be generic, misleading, or low agreement",
            "next_gate": "collect paired R124/R190/R203 labels",
        },
        {
            "rq": "RQ6 artifact/community",
            "verdict": "partial",
            "evidence_level": "local smoke only",
            "primary_evidence": "R160 and R200 pass bounded local/generated-fixture smokes",
            "falsifier_remaining": "fresh-clone or external developer run may fail",
            "next_gate": "external fresh-clone run",
        },
    ]


def next_experiment_rows() -> list[dict[str, str]]:
    return [
        {
            "priority": "P0",
            "run_id": "R142-pilot-return",
            "claim": "C5/RQ4",
            "block": "B4",
            "purpose": "Score real developer responses for the frozen semantic-vs-baseline forensic tasks.",
            "command_or_input": "place r142-pilot-responses.csv in docs/visexp/out/human-evidence-r195/inbox and run python3 docs/visexp/r195_human_evidence_pipeline.py",
            "oracle": "frozen answer key, response contract, Holm-corrected participant/task/order blocked permutation gate",
            "result_path": "docs/visexp/out/human-evidence-r195/scored/",
        },
        {
            "priority": "P0",
            "run_id": "R124-labels-return",
            "claim": "C6/RQ5",
            "block": "B5",
            "purpose": "Score independent human adequacy labels for one-word session/prompt/LLM-call tags.",
            "command_or_input": "return r124-labeler-1.csv and r124-labeler-2.csv, adjudicate disagreements, then run R195",
            "oracle": "adequacy/generic/misleading rubric, paired label coverage, kappa/agreement and adequacy thresholds",
            "result_path": "docs/visexp/out/human-evidence-r195/scored/",
        },
        {
            "priority": "P1",
            "run_id": "R190-R203-labels-return",
            "claim": "C3/C6",
            "block": "B8",
            "purpose": "Score merge-risk and regenerated-label promotion quality before any display-map promotion claim.",
            "command_or_input": "return r190-labeler-*.csv and r203-labeler-*.csv, adjudicate disagreements, then run R195",
            "oracle": "overmerge/undermerge and promote/reject rubrics with no canonical-map update unless gates pass",
            "result_path": "docs/visexp/out/human-evidence-r195/scored/",
        },
        {
            "priority": "P1",
            "run_id": "R191-target-network-lineage",
            "claim": "C4/RQ3",
            "block": "B3",
            "purpose": "Harden exact lineage for target-specific network effects rather than low-level agent-process rows only.",
            "command_or_input": "new fixed Codex network tasks under agentsight record --trace-net",
            "oracle": "target-specific network events >0, all joined, zero negative-control joins",
            "result_path": "docs/visexp/out/live-network-r191.json",
        },
        {
            "priority": "P2",
            "run_id": "R220-fresh-clone-community",
            "claim": "C7/RQ6",
            "block": "B7",
            "purpose": "Run a fresh-clone public setup and write-set/sanitization audit outside the current dirty artifact branch.",
            "command_or_input": "fresh clone, documented install, generated fixture run, write-set audit",
            "oracle": "expected files exist, no raw trace leaks, no writes outside declared output paths",
            "result_path": "docs/visexp/out/fresh-clone-community-r220.json",
        },
    ]


def overall_status(claims: list[dict[str, str]]) -> dict[str, Any]:
    verdict_by_claim = {row["claim"].split()[0]: row["verdict"] for row in claims}
    c5_ok = verdict_by_claim.get("C5") == "supported"
    c6_ok = verdict_by_claim.get("C6") == "supported"
    blockers: list[str] = []
    if not c5_ok:
        blockers.append("C5/RQ4 has no supported real participant outcome")
    if not c6_ok:
        blockers.append("C6/RQ5 has no supported independent human adequacy labels")
    return {
        "status": "osdi_weak_accept_not_supported" if blockers else "human_evidence_ready_for_claim_audit",
        "weak_accept_supported": False,
        "human_evidence_supported": not blockers,
        "blockers": blockers,
        "disallowed_evidence": [
            "subagent review",
            "LLM-filled labels",
            "synthetic review fixtures",
            "empty launch packets",
            "syntax-only tag validity",
        ],
    }


def claim_gate(overall: dict[str, Any]) -> dict[str, bool]:
    return {
        "claim_readiness_gap_gate_supported": True,
        "reads_generated_artifacts_only": True,
        "raw_trace_read": False,
        "llm_called": False,
        "weak_accept_supported": bool(overall.get("weak_accept_supported")),
        "requires_c5_human_participants": "C5/RQ4 has no supported real participant outcome"
        in (overall.get("blockers") or []),
        "requires_c6_human_labels": "C6/RQ5 has no supported independent human adequacy labels"
        in (overall.get("blockers") or []),
        "synthetic_or_subagent_evidence_disallowed": True,
    }


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    summary = result["summary"]
    lines = [
        "# R219 Claim Readiness Gap Gate",
        "",
        f"Status: `{result['status']}`",
        "",
        "R219 is a reviewer-facing claim-readiness audit over generated artifacts.",
        "It does not read raw agent traces, does not call an LLM, and does not count synthetic or subagent evidence as C5/C6 support.",
        "",
        "## Summary",
        "",
        f"- R170 full-history sessions: {summary['r170_sessions']}.",
        f"- R170 system observations: {summary['r170_system_observations']}.",
        f"- R180 valid outputs: {summary['r180_ok_runs']}/{summary['r180_total_runs']}.",
        f"- R114 command-mode precision/recall: {summary['r114_precision_pct']}%/{summary['r114_recall_pct']}%.",
        f"- R217 production display buckets/support: {summary['r217_display_buckets']}/{summary['r217_support']}.",
        f"- R218 preview accepted/rejected rows: {summary['r218_accepted_diff_rows']}/{summary['r218_rejected_rows']}.",
        f"- C5 participant responses: {summary['c5_responses']}.",
        f"- C6 final adequacy labels: {summary['c6_final_labels']}.",
        "",
        "## Verdict",
        "",
        f"- Weak accept supported: `{result['overall']['weak_accept_supported']}`.",
        f"- Human evidence supported: `{result['overall']['human_evidence_supported']}`.",
        f"- Blockers: {result['overall']['blockers']}.",
        "",
        "## Claim Rows",
        "",
    ]
    for row in result["claims"]:
        lines.append(f"- {row['claim']}: `{row['verdict']}`. Next: {row['next_gate']}")
    lines.extend(["", "## RQ Rows", ""])
    for row in result["rqs"]:
        lines.append(f"- {row['rq']}: `{row['verdict']}`. Next: {row['next_gate']}")
    lines.extend(["", "## Next Experiments", ""])
    for row in result["next_experiments"]:
        lines.append(f"- {row['priority']} {row['run_id']}: {row['purpose']}")
    lines.extend(["", "## Disallowed Evidence", ""])
    for item in result["overall"]["disallowed_evidence"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    artifacts = {key: read_json_required(path) for key, path in SOURCE_PATHS.items()}
    summary = artifact_statuses(artifacts)
    claims = claim_rows(summary)
    rqs = rq_rows(summary)
    next_rows = next_experiment_rows()
    overall = overall_status(claims)
    gate = claim_gate(overall)
    return {
        "schema_version": 1,
        "run_id": "R219",
        "claim": "Claim/RQ readiness gap gate for OSDI review",
        "status": overall["status"],
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_artifacts": SOURCE_PATHS,
        "summary": summary,
        "claims": claims,
        "rqs": rqs,
        "next_experiments": next_rows,
        "overall": overall,
        "claim_gate": gate,
        "claim_boundary": (
            "R219 is an audit/readiness artifact only. It cannot satisfy C5/C6, cannot replace human "
            "participant responses or independent labels, and cannot upgrade the paper to weak accept."
        ),
        "outputs": {
            "claim_csv": rel(Path(args.out_dir) / "claim-readiness-r219.csv"),
            "rq_csv": rel(Path(args.out_dir) / "rq-readiness-r219.csv"),
            "next_experiments_csv": rel(Path(args.out_dir) / "next-experiments-r219.csv"),
            "summary_md": rel(Path(args.out_dir) / "claim-readiness-r219.md"),
        },
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = build_result(args)
    result_path = out_dir / "claim-readiness-r219.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(out_dir / "claim-readiness-r219.csv", result["claims"], CLAIM_FIELDS)
    write_csv(out_dir / "rq-readiness-r219.csv", result["rqs"], RQ_FIELDS)
    write_csv(out_dir / "next-experiments-r219.csv", result["next_experiments"], NEXT_FIELDS)
    write_markdown(out_dir / "claim-readiness-r219.md", result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    return parser.parse_args()


def main() -> None:
    result = run(parse_args())
    print(json.dumps({"status": result["status"], "run_id": result["run_id"]}, sort_keys=True))


if __name__ == "__main__":
    main()
