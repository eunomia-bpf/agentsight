#!/usr/bin/env python3
"""R352: OSDI-style evaluation rubric audit over the existing profiler evidence.

This is a paper-organization gate, not a new empirical result. It reads the
tracked R320-R351 artifacts and current paper text, then checks whether the
current evidence supports a scoped top-conference profiling claim:
operation/operation-stack profiling faithfully localizes, ranks, and explains
task-relevant problems in real labeled agent traces with less inspection work
or less fragmentation than flat summaries and fixed-session drilldown.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
SUBMODULE_ROOT = ROOT / "docs" / "agentpprof-paper"
DEFAULT_OUT_DIR = OUT_ROOT / "paper-evaluation-rubric-r352"
RUN_ID = "R352"
ABSTRACTIONS = ["operation", "operation stack"]

EMPIRICAL_SOURCES = {
    "R320 profile accuracy": OUT_ROOT / "operation-profile-accuracy-r320" / "profile-accuracy-report.json",
    "R320 policy scores": OUT_ROOT / "operation-profile-accuracy-r320" / "policy-scores.csv",
    "R327 profile cost": OUT_ROOT / "operation-profile-cost-r327" / "profile-cost-report.json",
    "R328 deterministic output": OUT_ROOT
    / "operation-profile-deterministic-output-r328"
    / "deterministic-output-report.json",
    "R330 uncertainty": OUT_ROOT / "operation-profile-uncertainty-r330" / "uncertainty-report.json",
    "R331 negative control": OUT_ROOT
    / "operation-profile-negative-control-r331"
    / "negative-control-report.json",
    "R333 inspection frontier": OUT_ROOT
    / "operation-inspection-frontier-r333"
    / "inspection-frontier-report.json",
    "R334 fragmentation": OUT_ROOT
    / "operation-fragmentation-tradeoff-r334"
    / "fragmentation-tradeoff-report.json",
    "R335 actionability": OUT_ROOT
    / "operation-actionability-synthesis-r335"
    / "actionability-synthesis-report.json",
    "R336 actionability selection": OUT_ROOT
    / "operation-actionability-selection-r336"
    / "actionability-selection-report.json",
    "R337 inspection target": OUT_ROOT
    / "operation-inspection-target-r337"
    / "inspection-target-report.json",
    "R339 sequence adequacy": OUT_ROOT
    / "operation-sequence-adequacy-r339"
    / "sequence-adequacy-report.json",
    "R340 policy transfer": OUT_ROOT
    / "operation-policy-transfer-r340"
    / "policy-transfer-report.json",
    "R341 mechanism attribution": OUT_ROOT
    / "operation-mechanism-attribution-r341"
    / "mechanism-attribution-report.json",
    "R342 profile composition": OUT_ROOT
    / "operation-profile-spec-composition-r342"
    / "profile-spec-composition-report.json",
    "R344 metric consistency": OUT_ROOT
    / "operation-metric-consistency-r344"
    / "metric-consistency-report.json",
    "R345 diagnostic lens": OUT_ROOT
    / "operation-diagnostic-lens-portfolio-r345"
    / "diagnostic-lens-report.json",
    "R346 diagnostic casebook": OUT_ROOT
    / "operation-diagnostic-casebook-r346"
    / "diagnostic-casebook-report.json",
    "R347 baseline contrast": OUT_ROOT
    / "operation-case-baseline-contrast-r347"
    / "case-baseline-contrast-report.json",
    "R348 action counterfactual": OUT_ROOT
    / "operation-action-counterfactual-r348"
    / "action-counterfactual-report.json",
    "R349 action transfer": OUT_ROOT
    / "operation-action-transfer-r349"
    / "action-transfer-report.json",
    "R350 evidence packet": OUT_ROOT
    / "operation-evidence-packet-r350"
    / "evidence-packet-report.json",
}

GATE_SOURCES = {
    "R338 claim integrity": OUT_ROOT / "paper-claim-integrity-r338" / "claim-integrity-report.json",
    "R351 reviewer acceptance": OUT_ROOT
    / "paper-reviewer-acceptance-r351"
    / "reviewer-acceptance.json",
}

PAPER_SOURCES = {
    "evaluation ledger": ROOT / "docs" / "evaluation.md",
    "Chinese claim setup": ROOT / "docs" / "visexp" / "paper" / "evaluation-claims-setup.zh-CN.md",
    "Chinese paper": ROOT / "docs" / "visexp" / "paper" / "main.tex",
    "English paper": SUBMODULE_ROOT / "main.tex",
}

MUST_NOT_CLAIM_MARKERS = [
    "human utility",
    "human/agent analyst",
    "automatic action selector",
    "automatic universal selector",
    "single-view dominance",
    "完整 trace ecosystem",
    "完整 intent-boundary discovery",
    "not a human-productivity claim",
    "automatic boundary discovery",
    "complete trace-ecosystem compatibility",
]

RUBRIC_AREAS = [
    "claim_evidence_alignment",
    "workload_and_setup",
    "fidelity_accuracy",
    "baseline_tradeoff",
    "actionability",
    "generality",
    "mechanism_isolation",
    "robustness_statistics",
    "reproducibility_overhead",
    "claim_scope_guardrails",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def repo_rel(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root))
    except ValueError:
        return str(path.resolve())


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_output(args: list[str], *, cwd: Path = ROOT) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SystemExit(f"git {' '.join(args)} failed in {cwd}: {detail}")
    return result.stdout.strip()


def git_path_status(path: Path, *, repo_root: Path, require_clean: bool) -> str:
    if not path.exists():
        raise SystemExit(f"missing source path: {rel(path)}")
    display = repo_rel(path, repo_root)
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", display],
        cwd=repo_root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if tracked.returncode != 0:
        detail = tracked.stderr.strip() or tracked.stdout.strip()
        raise SystemExit(f"{rel(path)} is not git-tracked: {detail}")
    unstaged = subprocess.run(["git", "diff", "--quiet", "--", display], cwd=repo_root, check=False)
    staged = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", display], cwd=repo_root, check=False
    )
    dirty = unstaged.returncode != 0 or staged.returncode != 0
    if require_clean and dirty:
        raise SystemExit(f"{rel(path)} must be tracked-clean evidence for {RUN_ID}")
    return "tracked_clean" if not dirty else "tracked_dirty_allowed"


def collect_source_status() -> dict[str, dict[str, Any]]:
    status: dict[str, dict[str, Any]] = {}
    for name, path in EMPIRICAL_SOURCES.items():
        status[name] = {
            "path": rel(path),
            "sha256": sha256_file(path),
            "status": git_path_status(path, repo_root=ROOT, require_clean=True),
            "role": "empirical_evidence",
        }
    for name, path in GATE_SOURCES.items():
        status[name] = {
            "path": rel(path),
            "sha256": sha256_file(path),
            "status": git_path_status(path, repo_root=ROOT, require_clean=False),
            "role": "paper_gate",
        }
    for name, path in PAPER_SOURCES.items():
        repo_root = SUBMODULE_ROOT if path.resolve().is_relative_to(SUBMODULE_ROOT.resolve()) else ROOT
        status[name] = {
            "path": rel(path),
            "sha256": sha256_file(path),
            "status": git_path_status(path, repo_root=repo_root, require_clean=False),
            "role": "paper_text",
        }
    return status


def check(
    rows: list[dict[str, Any]],
    *,
    area: str,
    name: str,
    condition: bool,
    evidence: str,
    failure: str,
    required: bool = True,
) -> None:
    if area not in RUBRIC_AREAS:
        raise SystemExit(f"unknown rubric area: {area}")
    rows.append(
        {
            "area": area,
            "check": name,
            "required": required,
            "status": "pass" if condition else "fail",
            "evidence": evidence if condition else failure,
        }
    )


def as_policy(row: dict[str, str]) -> str:
    return f"{row['view']}:{row['ranker']}"


def build_checks(reports: dict[str, dict[str, Any]], r320_scores: list[dict[str, str]], paper_text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    r320 = reports["R320"]
    r327 = reports["R327"]
    r328 = reports["R328"]
    r330 = reports["R330"]
    r331 = reports["R331"]
    r333 = reports["R333"]
    r334 = reports["R334"]
    r335 = reports["R335"]
    r336 = reports["R336"]
    r337 = reports["R337"]
    r339 = reports["R339"]
    r340 = reports["R340"]
    r341 = reports["R341"]
    r342 = reports["R342"]
    r344 = reports["R344"]
    r345 = reports["R345"]
    r346 = reports["R346"]
    r347 = reports["R347"]
    r348 = reports["R348"]
    r349 = reports["R349"]
    r350 = reports["R350"]
    r338 = reports["R338"]
    r351 = reports["R351"]

    views = sorted({row["view"] for row in r320_scores})
    rankers = sorted({row["ranker"] for row in r320_scores})
    policies = sorted({as_policy(row) for row in r320_scores})
    visible_non_oracle = [
        policy
        for policy in policies
        if not policy.startswith("label_drilldown:") and "oracle" not in policy
    ]

    check(
        rows,
        area="claim_evidence_alignment",
        name="paper_integrity_gate_passes",
        condition=r338["summary"]["overall"] == "pass"
        and r338["summary"]["number_checks_passed"] == r338["summary"]["number_checks_total"]
        and r338["summary"]["guardrails"] == "pass"
        and r338["summary"]["two_abstraction_boundary"] == "pass",
        evidence=(
            f"R338 passes {r338['summary']['number_checks_total']} number checks, "
            f"{r338['summary']['source_policy_checks_total']} source-policy checks, "
            f"and {r338['summary']['guardrail_checks_total']} guardrail checks."
        ),
        failure="R338 no longer fully passes the claim-integrity gate.",
    )
    check(
        rows,
        area="claim_evidence_alignment",
        name="reviewer_gate_accepts_scoped_claim",
        condition=r351["overall"] == "accepted"
        and r351["summary"]["final_accepts"] == 4
        and r351["summary"]["blocking_issues"] == 0
        and r351["summary"]["checks_passed"] == r351["summary"]["checks_total"],
        evidence="R351 records 4/4 ACCEPT, zero blocking issues, and all mechanical checks passing.",
        failure="R351 does not accept the current scoped claim.",
    )
    check(
        rows,
        area="claim_evidence_alignment",
        name="two_abstractions_only",
        condition=r338["summary"]["profiler_abstractions"] == ABSTRACTIONS
        and r339["summary"]["profiler_abstractions"] == ABSTRACTIONS
        and "prompt/session" in paper_text
        and "operation stack" in paper_text,
        evidence="The current evidence and paper text keep only operation and operation stack as profiler abstractions.",
        failure="The abstraction boundary is missing or drifting.",
    )

    totals = r320["totals"]
    check(
        rows,
        area="workload_and_setup",
        name="real_labeled_workload_scale",
        condition=totals["datasets"] == 4
        and totals["tasks"] == 6
        and totals["task_operations"] == 34539
        and totals["positive_operations"] == 3699,
        evidence="R320 scores 6 tasks over 4 public labeled trace families, 34,539 operations, and 3,699 positives.",
        failure="R320 workload scale no longer matches the paper setup.",
    )
    check(
        rows,
        area="workload_and_setup",
        name="baseline_and_ranker_surface_present",
        condition={"flat", "fixed_session", "dataset_native", "raw_action_stack", "operation_stack", "label_drilldown"}.issubset(
            views
        )
        and {"width", "visible_risk", "query_aware", "oracle_upper_bound"}.issubset(rankers)
        and len(visible_non_oracle) == 15
        and totals["policy_scores"] == 144,
        evidence="R320 covers flat, fixed-session, dataset-native, raw-action, operation-stack, and oracle drilldown views with 15 visible non-oracle policies and 144 policy scores.",
        failure="The benchmark is missing required views, rankers, or policy-score rows.",
    )
    check(
        rows,
        area="workload_and_setup",
        name="source_policy_uses_existing_datasets",
        condition=r320["input_policy"]["dataset_creation"] == "none"
        and r320["input_policy"]["dataset_sync"] == "none"
        and len(r333["input_policy"]["source_operations"]) == 4
        and r331["source_check"]["tracked_clean_files"] >= 6,
        evidence="R320/R333/R331 use existing tracked operation JSONL from four real labeled trace families; no dataset sync or creation is recorded.",
        failure="One or more setup artifacts records dataset creation/sync or missing tracked source operations.",
    )

    required_metrics = set(r344["summary"]["required_metrics_covered"])
    check(
        rows,
        area="fidelity_accuracy",
        name="localization_metrics_cover_profiler_claim",
        condition={
            "average_precision",
            "ndcg",
            "top5_precision",
            "top5_recall",
            "top5_f1",
            "budget30_recall",
            "budget30_f1",
            "work_to_first_positive",
            "groups",
        }.issubset(required_metrics)
        and r344["summary"]["metric_comparisons"] == 50
        and r344["summary"]["task_metric_delta_rows"] == 300,
        evidence="R344 covers AP/AUPRC-style score, nDCG, P/R/F1@5, budgeted recall/F1, work-to-first-positive, and group fragmentation across 50 comparisons.",
        failure="The metric surface is incomplete for a profiling localization/ranking claim.",
    )
    check(
        rows,
        area="fidelity_accuracy",
        name="hot_groups_recover_real_positives",
        condition=r350["summary"]["packets_with_top5_positive"] == 6
        and r350["summary"]["packets_with_top1_positive"] == 5
        and r350["summary"]["median_top5_work"] <= 0.1
        and r346["summary"]["tasks_with_positive_in_top5"] == 6,
        evidence="R350/R346 show top-5 operation-stack packets contain positives on 6/6 tasks, top-1 on 5/6, at median top-5 work 0.0937.",
        failure="Top-ranked groups no longer consistently recover positives.",
    )
    check(
        rows,
        area="fidelity_accuracy",
        name="hidden_label_leakage_control",
        condition=r320["leakage_check"]["status"] == "pass"
        and r320["leakage_check"]["overlap"] == []
        and "only after" in r320["input_policy"]["hidden_label_use"],
        evidence="R320 leakage check passes with no overlap between visible rank fields and hidden oracle labels.",
        failure="Hidden-label leakage control does not pass.",
    )

    check(
        rows,
        area="baseline_tradeoff",
        name="operation_stack_beats_flat_on_inspection_work",
        condition=r350["summary"]["operation_stack_beats_flat_work_tasks"] == 6
        and r347["summary"]["wins_vs_flat_top5_work"] == 6,
        evidence="Operation-stack top-ranked evidence uses less top-5 work than flat summaries on 6/6 tasks.",
        failure="Operation-stack no longer beats flat summaries on top-ranked work.",
    )
    check(
        rows,
        area="baseline_tradeoff",
        name="operation_stack_reduces_fixed_session_fragmentation",
        condition=r350["summary"]["operation_stack_beats_fixed_recall_tasks"] == 5
        and r350["summary"]["operation_stack_fewer_groups_than_fixed_tasks"] == 4
        and r337["summary"]["default_vs_fixed_target25"]["group_wins"] == 5,
        evidence="Operation-stack beats fixed-session top-5 recall on 5/6 tasks, uses fewer groups on 4/6, and wins fixed-25%-recall group cost on 5/6.",
        failure="Fixed-session fragmentation/recall tradeoff evidence is too weak.",
    )
    check(
        rows,
        area="baseline_tradeoff",
        name="counterpoints_are_preserved",
        condition=r344["summary"]["counterpoint_verdicts"] == 16
        and r350["summary"]["packets_with_baseline_counterpoints"] == 6
        and r335["summary"]["cards_where_fixed_session_has_lower_wtfp"] == 4,
        evidence="R344 has 16 counterpoint verdicts; R350 keeps baseline counterpoints for 6/6 packets; fixed-session lower-WTFP remains 4/6.",
        failure="Counterpoints have been collapsed into an overclaim.",
    )

    check(
        rows,
        area="actionability",
        name="diagnostic_cards_have_concrete_actions",
        condition=r335["summary"]["actionability_cards"] == 6
        and r335["summary"]["cards_with_optimization_action"] == 6
        and r345["summary"]["actionable_task_cards"] == 6
        and r350["summary"]["packets_with_nondefault_actions"] == 6,
        evidence="R335/R345/R350 produce concrete optimization actions for all 6 tasks and non-default action packets for 6/6 tasks.",
        failure="Actionability evidence is missing concrete task-level actions.",
    )
    check(
        rows,
        area="actionability",
        name="objective_level_knobs_are_not_universal_selector",
        condition=r341["summary"]["actionable_objective_rows"] == 36
        and r341["summary"]["nondefault_best_objective_rows"] == 27
        and r348["summary"]["visible_non_oracle_best_rows"] == 36
        and r348["summary"]["view_change_rows"] == 25
        and r349["summary"]["selected_action_exact"] == 7,
        evidence="R341/R348 show 36 objective-level actions with 27 non-default best rows and 25 view changes, while R349 keeps exact action transfer weak at 7/60.",
        failure="Actionability is either missing objective-level knobs or overclaiming an automatic selector.",
    )
    check(
        rows,
        area="actionability",
        name="diagnostic_lenses_are_disaggregated",
        condition=r345["summary"]["lens_count"] == 6
        and r345["summary"]["objective_rows"] == 36
        and r345["summary"]["tasks_with_three_or_more_best_views"] == 6
        and r345["summary"]["non_operation_stack_best_objectives"] == 25,
        evidence="R345 disaggregates 6 diagnostic lenses over 36 objective rows; every task needs at least 3 best views and non-operation-stack views win 25/36 objectives.",
        failure="The paper lacks disaggregated lens/actionability evidence.",
    )

    check(
        rows,
        area="generality",
        name="multiple_trace_families_and_problem_types",
        condition=r350["summary"]["datasets"] == 4
        and r339["summary"]["datasets"] == [
            "agent-reward-bench",
            "agentnet",
            "osworld-human",
            "satraj-os-safety",
        ]
        and r341["summary"]["mechanism_task_counts"]["stack_depth_tradeoff"] == 6
        and r345["summary"]["tasks"] == 6,
        evidence="The main benchmark spans AgentRewardBench, AgentNet, OSWorld-Human, and SATraj safety traces with six problem tasks.",
        failure="Generality over multiple real labeled trace families is not visible.",
    )
    check(
        rows,
        area="generality",
        name="sequence_scope_and_boundary_scope_are_scored",
        condition=r339["summary"]["overall"] == "pass"
        and r339["claim_summary"]["budget30"]["median_positive_session_recall"] > r339["claim_summary"]["budget30"][
            "fixed_positive_session_recall"
        ]
        and r342["summary"]["prompt_session_free_variants"] == 12,
        evidence="R339 scores sequence/session-scope recall tradeoffs, while R342 confirms 12/12 recursive stack specs are prompt/session-free.",
        failure="The evidence does not cover trajectory/session scope or prompt/session-free recursive stacks.",
    )

    check(
        rows,
        area="mechanism_isolation",
        name="recursive_stack_depth_and_mapping_are_isolated",
        condition=r342["summary"]["composition_variants"] == 12
        and r342["summary"]["tasks_where_coarse_reduces_groups"] == 6
        and r342["summary"]["tasks_where_depth_choice_changes_objective"] == 3
        and r335["summary"]["cards_with_positive_mapping_gain"] == 2
        and r335["summary"]["cards_with_negative_mapping_gain"] == 4,
        evidence="R342 isolates recursive stack depth over 12 specs; coarse depth reduces groups on 6/6 tasks and depth changes the best objective on 3/6, while R335 records both positive and negative mapping effects.",
        failure="Mechanism evidence does not isolate stack depth and mapping/tagging effects.",
    )
    check(
        rows,
        area="mechanism_isolation",
        name="query_aware_ranking_and_feature_ablation_are_visible",
        condition=r335["summary"]["cards_with_ranker_ap_gain"] == 6
        and r335["summary"]["cards_with_critical_features"] == 4
        and r335["summary"]["cards_with_misleading_features"] == 2
        and r340["input_policy"]["target_hidden_label_use"] == "not used for policy selection",
        evidence="R335 identifies ranker gains, critical features, and misleading features; R340 selects policies without target hidden labels.",
        failure="Ranking/mechanism improvements may be label leakage or unisolated artifacts.",
    )
    check(
        rows,
        area="mechanism_isolation",
        name="negative_control_calibrates_signal",
        condition=any(
            row["policy"] == "operation_stack:query_aware"
            and row["metric"] == "average_precision"
            and int(row["beyond_95pct_null_tasks"]) == 6
            for row in r331["policy_summary"]
        )
        and r331["input_policy"]["dataset_sync"] == "none"
        and r331["input_policy"]["profiler_rerun"] == "none",
        evidence="R331 fixes visible group/ranking order and shows operation-stack query-aware AP exceeds the permutation null on 6/6 tasks without rerunning the profiler.",
        failure="Negative-control calibration is missing or too weak.",
    )

    check(
        rows,
        area="robustness_statistics",
        name="bootstrap_uncertainty_has_support_and_counterpoints",
        condition=r330["source_check"]["status"] == "pass"
        and r330["finding_summary"]["supported_metric_checks"] == 10
        and r330["finding_summary"]["mixed_or_counterpoint_metric_checks"] == 10,
        evidence="R330 task-family bootstrap has 10 supported checks and 10 mixed/counterpoint checks, preserving statistical uncertainty.",
        failure="Bootstrap uncertainty evidence is missing or no longer balanced with counterpoints.",
    )
    check(
        rows,
        area="robustness_statistics",
        name="heldout_policy_transfer_is_scoped_guardrail",
        condition=r340["summary"]["transfer_decisions"] == 96
        and r340["claim_summary"]["within_tolerance_decisions"] == 62
        and r349["summary"]["selected_visible_non_oracle_rows"] == 60
        and r349["summary"]["selected_within_tolerance"] == 35
        and r349["summary"]["selected_action_exact"] == 7,
        evidence="R340/R349 provide held-out visible policy-transfer guardrails: 96 decisions, 62/96 within tolerance in R340, and 35/60 within tolerance but only 7/60 exact action in R349.",
        failure="Held-out transfer either leaks target labels or overclaims exact automatic action selection.",
    )

    check(
        rows,
        area="reproducibility_overhead",
        name="profile_spec_cost_and_determinism_are_reported",
        condition=r327["status"] == "pass"
        and r327["summary"]["semantic_deterministic_specs"] == "76/76"
        and r328["status"] == "pass"
        and r328["summary"]["semantic_deterministic_specs"] == "76/76"
        and r328["summary"]["raw_byte_deterministic_specs"] == "76/76"
        and r328["source_status"]["git_status_short"] == ""
        and r328["source_status"]["code_status_short"] == "",
        evidence="R327/R328 cover 76 specs and 152 invocations; R328 clean rerun gives 76/76 semantic and raw-byte deterministic outputs.",
        failure="Profile-spec determinism/cost evidence is missing or dirty.",
    )
    check(
        rows,
        area="reproducibility_overhead",
        name="no_network_or_dataset_sync_in_final_gates",
        condition=r338["summary"]["network_access_required"] is False
        and r338["summary"]["source_artifacts_tracked_clean"] is True
        and r350["summary"]["network_access_required"] is False
        and r351["network_access_required"] is False,
        evidence="R338/R350/R351 require no network access, use tracked evidence, and do not sync/create/relabel datasets.",
        failure="Final gates are not reproducible from tracked artifacts.",
    )

    check(
        rows,
        area="claim_scope_guardrails",
        name="must_not_claim_boundaries_visible",
        condition=all(marker in paper_text for marker in MUST_NOT_CLAIM_MARKERS)
        and r338["summary"]["guardrail_checks_passed"] == r338["summary"]["guardrail_checks_total"],
        evidence="Paper text and R338 visibly exclude human utility, automatic boundary/action selection, single-view dominance, and full ecosystem compatibility claims.",
        failure="One or more must-not-claim boundary is missing from the paper state.",
    )
    check(
        rows,
        area="claim_scope_guardrails",
        name="rubric_claim_is_scoped_profiler_claim",
        condition=r351["not_new_empirical_result"] is True
        and r351["not_a_human_study_result"] is True
        and r351["not_an_agent_analyst_task_result"] is True
        and "not human utility" in paper_text,
        evidence="R351 and the paper scope the result as a hidden-label profiler benchmark, not a human/agent analyst study.",
        failure="The paper state may be drifting toward unsupported human-utility claims.",
    )

    return rows


def build_residual_risks(reports: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    r349 = reports["R349"]["summary"]
    r350 = reports["R350"]["summary"]
    return [
        {
            "risk": "human_or_agent_analyst_utility",
            "status": "not_claimed",
            "paper_handling": "R352 is a profiler-output benchmark audit; it does not support analyst accuracy, time, or productivity claims.",
        },
        {
            "risk": "automatic_intent_boundary_discovery",
            "status": "not_claimed",
            "paper_handling": "Recursive stack fields and existing labels are evaluated, but the paper does not claim complete automatic boundary discovery.",
        },
        {
            "risk": "complete_trace_ecosystem_compatibility",
            "status": "not_claimed",
            "paper_handling": "Trace import/export examples remain artifact-level exchange evidence, not full OpenTelemetry/Phoenix/LangSmith/Langfuse/Perfetto compatibility.",
        },
        {
            "risk": "automatic_action_selector",
            "status": "counterpoint_preserved",
            "paper_handling": f"R349 exact action transfer remains {r349['selected_action_exact']}/60 and non-default exact action remains {r349['nondefault_target_action_exact']}/{r349['nondefault_target_rows']}.",
        },
        {
            "risk": "universal_budget_dominance",
            "status": "counterpoint_preserved",
            "paper_handling": f"R350 strict 30% work packets hold for {r350['packets_with_30pct_work_budget']}/6 tasks, so the claim is bounded rather than universal.",
        },
        {
            "risk": "broader_family_coverage",
            "status": "future_work",
            "paper_handling": "The main label-scored claim uses six tasks from four oracle-rich families; broader tool/API/mobile coverage remains optional future generality.",
        },
    ]


def summarize_checks(checks: list[dict[str, Any]]) -> dict[str, Any]:
    required = [row for row in checks if row["required"]]
    required_passed = [row for row in required if row["status"] == "pass"]
    by_area: dict[str, dict[str, int]] = {}
    for area in RUBRIC_AREAS:
        area_rows = [row for row in checks if row["area"] == area]
        by_area[area] = {
            "checks": len(area_rows),
            "passed": sum(1 for row in area_rows if row["status"] == "pass"),
            "required": sum(1 for row in area_rows if row["required"]),
        }
    return {
        "overall": "pass" if len(required) == len(required_passed) else "needs_work",
        "rubric_level": "level_4_scoped_profile_benchmark" if len(required) == len(required_passed) else "below_level_4",
        "checks_total": len(checks),
        "checks_passed": sum(1 for row in checks if row["status"] == "pass"),
        "required_checks_total": len(required),
        "required_checks_passed": len(required_passed),
        "rubric_areas_passed": sum(1 for row in by_area.values() if row["checks"] and row["passed"] == row["checks"]),
        "rubric_areas_total": len([area for area in by_area.values() if area["checks"]]),
        "by_area": by_area,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Paper Evaluation Rubric R352",
        "",
        "R352 maps the existing tracked profiler-evaluation artifacts to an OSDI-style profiling-paper rubric. It is not a new empirical result, does not download or sync datasets, and does not rerun the profiler.",
        "",
        "## Verdict",
        "",
        f"- Overall: {report['summary']['overall']}.",
        f"- Rubric level: {report['summary']['rubric_level']}.",
        f"- Checks: {report['summary']['checks_passed']}/{report['summary']['checks_total']}.",
        f"- Required checks: {report['summary']['required_checks_passed']}/{report['summary']['required_checks_total']}.",
        "",
        "## Rubric Checks",
        "",
        "| Area | Check | Status | Evidence |",
        "|---|---|---|---|",
    ]
    for row in report["checks"]:
        lines.append(f"| {row['area']} | {row['check']} | {row['status']} | {row['evidence']} |")
    lines.extend(["", "## Residual Risks", "", "| Risk | Status | Handling |", "|---|---|---|"])
    for row in report["residual_risks"]:
        lines.append(f"| {row['risk']} | {row['status']} | {row['paper_handling']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(path: Path, report: dict[str, Any]) -> None:
    check_rows = []
    for row in report["checks"]:
        check_rows.append(
            "<tr>"
            f"<td>{html.escape(row['area'])}</td>"
            f"<td>{html.escape(row['check'])}</td>"
            f"<td>{html.escape(row['status'])}</td>"
            f"<td>{html.escape(row['evidence'])}</td>"
            "</tr>"
        )
    risk_rows = []
    for row in report["residual_risks"]:
        risk_rows.append(
            "<tr>"
            f"<td>{html.escape(row['risk'])}</td>"
            f"<td>{html.escape(row['status'])}</td>"
            f"<td>{html.escape(row['paper_handling'])}</td>"
            "</tr>"
        )
    path.write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Paper Evaluation Rubric R352</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; color: #1f2933; }
    h1 { font-size: 1.6rem; }
    p, li { max-width: 920px; line-height: 1.5; }
    table { border-collapse: collapse; margin-top: 1.5rem; min-width: 980px; }
    th, td { border: 1px solid #d8dee9; padding: 0.5rem 0.65rem; text-align: left; vertical-align: top; }
    th { background: #f6f8fa; }
  </style>
</head>
<body>
  <h1>Paper Evaluation Rubric R352</h1>
  <p>Existing-artifact OSDI-style rubric audit for the scoped operation/operation-stack profiler claim.</p>
  <p>Overall: <strong>"""
        + html.escape(report["summary"]["overall"])
        + """</strong>. Required checks: """
        + f"{report['summary']['required_checks_passed']}/{report['summary']['required_checks_total']}"
        + """.</p>
  <h2>Checks</h2>
  <table>
    <tr><th>Area</th><th>Check</th><th>Status</th><th>Evidence</th></tr>
"""
        + "\n".join(check_rows)
        + """
  </table>
  <h2>Residual Risks</h2>
  <table>
    <tr><th>Risk</th><th>Status</th><th>Handling</th></tr>
"""
        + "\n".join(risk_rows)
        + """
  </table>
</body>
</html>
""",
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    source_status = collect_source_status()
    reports = {
        "R320": load_json(EMPIRICAL_SOURCES["R320 profile accuracy"]),
        "R327": load_json(EMPIRICAL_SOURCES["R327 profile cost"]),
        "R328": load_json(EMPIRICAL_SOURCES["R328 deterministic output"]),
        "R330": load_json(EMPIRICAL_SOURCES["R330 uncertainty"]),
        "R331": load_json(EMPIRICAL_SOURCES["R331 negative control"]),
        "R333": load_json(EMPIRICAL_SOURCES["R333 inspection frontier"]),
        "R334": load_json(EMPIRICAL_SOURCES["R334 fragmentation"]),
        "R335": load_json(EMPIRICAL_SOURCES["R335 actionability"]),
        "R336": load_json(EMPIRICAL_SOURCES["R336 actionability selection"]),
        "R337": load_json(EMPIRICAL_SOURCES["R337 inspection target"]),
        "R339": load_json(EMPIRICAL_SOURCES["R339 sequence adequacy"]),
        "R340": load_json(EMPIRICAL_SOURCES["R340 policy transfer"]),
        "R341": load_json(EMPIRICAL_SOURCES["R341 mechanism attribution"]),
        "R342": load_json(EMPIRICAL_SOURCES["R342 profile composition"]),
        "R344": load_json(EMPIRICAL_SOURCES["R344 metric consistency"]),
        "R345": load_json(EMPIRICAL_SOURCES["R345 diagnostic lens"]),
        "R346": load_json(EMPIRICAL_SOURCES["R346 diagnostic casebook"]),
        "R347": load_json(EMPIRICAL_SOURCES["R347 baseline contrast"]),
        "R348": load_json(EMPIRICAL_SOURCES["R348 action counterfactual"]),
        "R349": load_json(EMPIRICAL_SOURCES["R349 action transfer"]),
        "R350": load_json(EMPIRICAL_SOURCES["R350 evidence packet"]),
        "R338": load_json(GATE_SOURCES["R338 claim integrity"]),
        "R351": load_json(GATE_SOURCES["R351 reviewer acceptance"]),
    }
    r320_scores = read_csv(EMPIRICAL_SOURCES["R320 policy scores"])
    paper_text = "\n".join(path.read_text(encoding="utf-8") for path in PAPER_SOURCES.values())
    checks = build_checks(reports, r320_scores, paper_text)
    summary = summarize_checks(checks)
    residual_risks = build_residual_risks(reports)
    report = {
        "run_id": RUN_ID,
        "schema": "agentsight.paper-evaluation-rubric.v1",
        "status": "ok" if summary["overall"] == "pass" else "needs_work",
        "summary": {
            **summary,
            "datasets": reports["R350"]["summary"]["datasets"],
            "tasks": reports["R350"]["summary"]["tasks"],
            "objective_rows": reports["R350"]["summary"]["objective_rows"],
            "top5_positive_packets": reports["R350"]["summary"]["packets_with_top5_positive"],
            "strict_30pct_packets": reports["R350"]["summary"]["packets_with_30pct_work_budget"],
            "within_tolerance_transfer_decisions": reports["R349"]["summary"]["selected_within_tolerance"],
            "exact_action_transfer_decisions": reports["R349"]["summary"]["selected_action_exact"],
            "empirical_sources_tracked_clean": all(
                row["status"] == "tracked_clean"
                for row in source_status.values()
                if row["role"] == "empirical_evidence"
            ),
            "network_access_required": False,
        },
        "input_policy": {
            "dataset_creation": "none",
            "dataset_relabeling": "none",
            "dataset_sync": "none",
            "profiler_rerun": "none",
            "hidden_label_use": "R352 reads already-scored hidden-label artifacts only to audit claim support; it does not form new rankings",
            "network_access_required": False,
        },
        "not_new_empirical_result": True,
        "not_a_human_study_result": True,
        "not_an_agent_analyst_task_result": True,
        "profiler_abstractions": ABSTRACTIONS,
        "claim": (
            "Operation/operation-stack profiling can accurately localize task-relevant failures, "
            "quality problems, and semantic boundaries in real labeled agent traces while requiring "
            "less inspection work than flat summaries and less fragmentation than fixed-session drilldown."
        ),
        "source_status": source_status,
        "checks": checks,
        "residual_risks": residual_risks,
        "commit": git_output(["rev-parse", "HEAD"]),
    }

    report_json = out_dir / "evaluation-rubric-report.json"
    checks_csv = out_dir / "evaluation-rubric-checks.csv"
    residual_csv = out_dir / "residual-risks.csv"
    source_csv = out_dir / "source-status.csv"
    report_md = out_dir / "evaluation-rubric-report.md"
    index_html = out_dir / "index.html"
    run_result = out_dir / "run-result.json"

    write_json(report_json, report)
    write_csv(checks_csv, checks, ["area", "check", "required", "status", "evidence"])
    write_csv(residual_csv, residual_risks, ["risk", "status", "paper_handling"])
    write_csv(source_csv, list(source_status.values()), ["role", "status", "path", "sha256"])
    write_markdown(report_md, report)
    write_html(index_html, report)
    write_json(
        run_result,
        {
            "run_id": RUN_ID,
            "status": report["status"],
            "overall": summary["overall"],
            "rubric_level": summary["rubric_level"],
            "checks_passed": summary["checks_passed"],
            "checks_total": summary["checks_total"],
            "required_checks_passed": summary["required_checks_passed"],
            "required_checks_total": summary["required_checks_total"],
            "outputs": {
                "report_json": rel(report_json),
                "checks_csv": rel(checks_csv),
                "residual_csv": rel(residual_csv),
                "source_csv": rel(source_csv),
                "markdown": rel(report_md),
                "html": rel(index_html),
            },
        },
    )
    print(json.dumps(load_json(run_result), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
