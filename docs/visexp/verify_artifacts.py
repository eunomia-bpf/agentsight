#!/usr/bin/env python3
"""Verify generated docs/visexp artifacts are internally consistent."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


def read_folded(path: Path) -> tuple[int, int]:
    count = 0
    total = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line:
                continue
            stack, _, weight = line.rpartition(" ")
            if not stack or not weight.isdigit():
                raise AssertionError(f"invalid folded line in {path}: {line[:120]}")
            count += 1
            total += int(weight)
    return count, total


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_no_sensitive_text(path: Path) -> None:
    # R122/R124 deliberately contain redacted prompt previews for human labels.
    # The verifier checks secret/path shapes, not ordinary prompt wording.
    pattern = re.compile(
        r"/home/[A-Za-z0-9._-]+|Bearer|api_key|sk-[A-Za-z0-9]{20,}|ANTHROPIC_API|OPENAI_API"
    )
    text = path.read_text(encoding="utf-8", errors="replace")
    match = pattern.search(text)
    if match:
        raise AssertionError(f"sensitive-looking text in {path}: {match.group(0)}")


def run(out_dir: Path) -> dict[str, int | str]:
    summary = json.loads((out_dir / "aggregation.json").read_text(encoding="utf-8"))
    manifest_path = out_dir / "input-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    system_lines, system_total = read_folded(out_dir / "semantic-system.folded.txt")
    nonsemantic_lines, nonsemantic_total = read_folded(out_dir / "nonsemantic-system.folded.txt")
    token_lines, token_total = read_folded(out_dir / "semantic-token.folded.txt")
    dimension_path = out_dir / "tag-dimensions.json"
    dimensions = json.loads(dimension_path.read_text(encoding="utf-8")) if dimension_path.exists() else {}

    checks = {
        "system_lines": system_lines,
        "system_total": system_total,
        "nonsemantic_lines": nonsemantic_lines,
        "nonsemantic_total": nonsemantic_total,
        "token_lines": token_lines,
        "token_total": token_total,
    }

    expected = {
        "system_lines": summary["system_unique_stacks"],
        "system_total": summary["expanded_system_observations"],
        "nonsemantic_lines": summary["nonsemantic_system_unique_stacks"],
        "nonsemantic_total": summary["nonsemantic_system_total_weight"],
        "token_lines": summary["token_unique_stacks"],
        "token_total": summary["token_total_weight"],
    }
    for key, value in expected.items():
        if checks[key] != value:
            raise AssertionError(f"{key}: expected {value}, got {checks[key]}")

    required_dimensions = {
        "session-system": system_total,
        "prompt-system": system_total,
        "session-token": token_total,
        "prompt-token": token_total,
        "llm-token": token_total,
    }
    dimension_rows = {
        row.get("view"): row
        for row in dimensions.get("views", [])
        if isinstance(row, dict)
    }
    for view, expected_total in required_dimensions.items():
        folded_path = out_dir / f"{view}.folded.txt"
        svg_path = out_dir / f"{view}.svg"
        if not folded_path.exists() or not svg_path.exists():
            raise AssertionError(f"missing dimension view artifact: {view}")
        lines, total = read_folded(folded_path)
        if total != expected_total:
            raise AssertionError(f"{view}: expected total {expected_total}, got {total}")
        row = dimension_rows.get(view)
        if not row:
            raise AssertionError(f"missing tag-dimensions.json row: {view}")
        if row.get("total_weight") != total or row.get("unique_stacks") != lines:
            raise AssertionError(f"{view}: folded totals do not match tag-dimensions.json")

    if summary["tag_contract"]["invalid_count"] != 0:
        raise AssertionError("tag contract has invalid tags")
    if len(manifest.get("sessions", [])) != summary["session_count"]:
        raise AssertionError("input manifest session count does not match summary")
    if summary.get("input_manifest_sha256") != file_sha256(manifest_path):
        raise AssertionError("input manifest sha256 does not match summary")
    if summary["system_collapsed_observations"] != summary["expanded_system_observations"] - summary["system_unique_stacks"]:
        raise AssertionError("collapsed observation count is inconsistent")
    if summary["expanded_system_observations"] < summary["raw_tool_events"]:
        raise AssertionError("expanded observations cannot be smaller than raw tool events")

    with (out_dir / "prompt-tags.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if rows and any(row.get("preview") != "redacted" for row in rows):
        raise AssertionError("prompt previews are not redacted")

    with (out_dir / "agent-diff.csv").open("r", encoding="utf-8", newline="") as handle:
        diff_rows = list(csv.DictReader(handle))
    required = {"cohort", "winner", "rate_delta_per_1k", "codex_rate_per_1k", "claude_rate_per_1k", "stack"}
    if not diff_rows or not required.issubset(diff_rows[0].keys()):
        raise AssertionError("agent-diff.csv is missing normalized diff columns")

    packets_path = out_dir / "user-task-participant-packets.json"
    response_template_path = out_dir / "user-task-response-template.csv"
    if packets_path.exists() and response_template_path.exists():
        packets = json.loads(packets_path.read_text(encoding="utf-8")).get("packets", [])
        with response_template_path.open("r", encoding="utf-8", newline="") as handle:
            template_rows = list(csv.DictReader(handle))
        required_template_fields = {
            "participant_id",
            "packet_id",
            "task_id",
            "condition",
            "response_json",
            "task_time_seconds",
            "confidence",
            "notes",
        }
        if template_rows and not required_template_fields.issubset(template_rows[0].keys()):
            raise AssertionError("user-task-response-template.csv is missing required columns")
        if len(template_rows) != len(packets):
            raise AssertionError("response template row count does not match participant packets")
        if {row["packet_id"] for row in template_rows} != {packet["packet_id"] for packet in packets}:
            raise AssertionError("response template packet IDs do not match participant packets")
        if any(
            row.get("response_json") != "{}"
            or row.get("task_time_seconds")
            or row.get("confidence")
            or row.get("notes")
            for row in template_rows
        ):
            raise AssertionError("response template must not contain participant responses")
        user_task_results_path = out_dir / "user-task-results.json"
        if not user_task_results_path.exists():
            raise AssertionError("user-task-results.json is missing")
        user_task_results = json.loads(user_task_results_path.read_text(encoding="utf-8"))
        response_contract = user_task_results.get("response_contract") or {}
        if "valid" not in response_contract:
            raise AssertionError("user-task-results.json is missing response_contract.valid")
        if not response_contract.get("valid"):
            raise AssertionError("user-task-results.json records an invalid response contract")
        analysis = user_task_results.get("claim_analysis") or {}
        gate = analysis.get("claim_gate") or {}
        thresholds = analysis.get("thresholds") or {}
        if "c5_supported" not in gate or "pilot_ready" not in gate:
            raise AssertionError("user-task-results.json is missing C5 claim gate fields")
        if "paper_scale_test" not in thresholds or "holm_correction_family" not in thresholds:
            raise AssertionError("C5 claim analysis is missing paper-scale statistical contract fields")
        if "order" not in str(thresholds.get("paper_scale_test")):
            raise AssertionError("C5 paper-scale statistical contract must include order blocking")
        if thresholds.get("semantic_condition") != "semantic-stack":
            raise AssertionError("C5 claim analysis has wrong semantic condition")
        if "event-count-proxy" not in thresholds.get("baseline_conditions", []):
            raise AssertionError("C5 baseline conditions must include the explicit event-count proxy")
        if "span-duration" in thresholds.get("baseline_conditions", []):
            raise AssertionError("C5 scorer must not treat event-count packets as span-duration baseline")
        if user_task_results.get("status") == "participant_results_empty" and gate.get("c5_supported"):
            raise AssertionError("empty C5 participant results must not support C5")
        if gate.get("c5_supported") and not gate.get("paper_model_ready"):
            raise AssertionError("C5 cannot be supported without the paper-scale model gate")
        prereg_path = out_dir / "user-task-preregistration-r142.json"
        if not prereg_path.exists():
            raise AssertionError("R142 user-task preregistration artifact is missing")
        prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
        if prereg.get("status") != "frozen_before_collection":
            raise AssertionError("R142 preregistration must be frozen before participant collection")
        if (prereg.get("validation") or {}).get("status") != "ok":
            raise AssertionError("R142 preregistration validation did not pass")
        prereg_conditions = prereg.get("conditions") or {}
        if prereg_conditions.get("semantic_condition") != thresholds.get("semantic_condition"):
            raise AssertionError("R142 preregistration semantic condition does not match scorer")
        if prereg_conditions.get("baseline_conditions") != thresholds.get("baseline_conditions"):
            raise AssertionError("R142 preregistration baselines do not match scorer")
        if "event-count-proxy" not in prereg_conditions.get("condition_order", []):
            raise AssertionError("R142 preregistration must include event-count-proxy")
        if "span-duration" in prereg_conditions.get("condition_order", []):
            raise AssertionError("R142 preregistration must not contain span-duration")
        prereg_plan = prereg.get("analysis_plan") or {}
        if prereg_plan.get("paper_scale_test") != thresholds.get("paper_scale_test"):
            raise AssertionError("R142 preregistration paper-scale test does not match scorer")
        if "order" not in str(prereg_plan.get("paper_scale_test")):
            raise AssertionError("R142 preregistration must block on participant/task/order")
        if prereg_plan.get("paper_min_participants") != thresholds.get("min_participants_for_claim"):
            raise AssertionError("R142 preregistration participant threshold does not match scorer")
        if (prereg.get("tasks") or {}).get("task_count") != len({packet["task_id"] for packet in packets}):
            raise AssertionError("R142 preregistration task count does not match packets")
        if (prereg.get("tasks") or {}).get("primary_utility_task_count") != thresholds.get("min_task_pairs_for_claim"):
            raise AssertionError("R142 preregistration primary task count must equal the C5 claim threshold")
        assignment = prereg.get("assignment_design") or {}
        if assignment.get("assignment_row_count") != len(template_rows):
            raise AssertionError("R142 preregistration assignment row count does not match response template")
        if not assignment.get("complete_task_condition_coverage"):
            raise AssertionError("R142 preregistration assignment must cover every condition per task")
        source_files = prereg.get("source_files") or {}
        expected_hash_paths = {
            "bundle": out_dir / "user-task-benchmark.json",
            "assignments": out_dir / "user-task-assignments.csv",
            "answer_key": out_dir / "user-task-answer-key.csv",
            "response_template": response_template_path,
            "scorer": Path(__file__).resolve().parent / "score_user_task_results.py",
        }
        for name, path in expected_hash_paths.items():
            recorded = (source_files.get(name) or {}).get("sha256")
            if recorded != file_sha256(path):
                raise AssertionError(f"R142 preregistration source hash mismatch for {name}")
        claim_gates_path = out_dir / "claim-gates.csv"
        if claim_gates_path.exists():
            with claim_gates_path.open("r", encoding="utf-8", newline="") as handle:
                gates = {row.get("claim"): row for row in csv.DictReader(handle)}
            c5 = gates.get("C5 user utility over trace tree/process logs")
            if not c5 or f"c5_supported={gate.get('c5_supported')}" not in c5.get("evidence", ""):
                raise AssertionError("C5 claim gate does not include current scorer status")

    tag_packet_path = out_dir / "tag-adequacy-label-packet-r122.csv"
    tag_results_path = out_dir / "tag-adequacy-results-r124.json"
    tag_results_csv_path = out_dir / "tag-adequacy-results-r124.csv"
    if tag_packet_path.exists():
        if not tag_results_path.exists() or not tag_results_csv_path.exists():
            raise AssertionError("R124 tag adequacy results are missing")
        with tag_packet_path.open("r", encoding="utf-8", newline="") as handle:
            tag_packet_rows = list(csv.DictReader(handle))
        if tag_packet_rows:
            required_tag_fields = {
                "fragment_index",
                "fragment_hash",
                "kind",
                "source",
                "model",
                "candidate_tag",
                "candidate_model",
                "candidate_exact_stable",
                "candidate_distinct_tags",
                "preview",
                "labeler_1",
                "labeler_2",
                "adjudicated_label",
            }
            if not required_tag_fields.issubset(tag_packet_rows[0].keys()):
                raise AssertionError("R122 tag adequacy packet is missing candidate tag columns")
            if any(not row.get("candidate_tag") for row in tag_packet_rows):
                raise AssertionError("R122 tag adequacy packet has rows without candidate tags")
        blinded_path = out_dir / "tag-adequacy-blinded-label-sheet-r124.csv"
        blinded_manifest_path = out_dir / "tag-adequacy-blinded-label-sheet-r124.json"
        if not blinded_path.exists() or not blinded_manifest_path.exists():
            raise AssertionError("R124 blinded label sheet artifacts are missing")
        with blinded_path.open("r", encoding="utf-8", newline="") as handle:
            blinded_rows = list(csv.DictReader(handle))
        with blinded_path.open("r", encoding="utf-8", newline="") as handle:
            blinded_reader = csv.DictReader(handle)
            visible_fields = list(blinded_reader.fieldnames or [])
        expected_blinded_fields = [
            "row_id",
            "fragment_index",
            "fragment_level",
            "redacted_preview",
            "candidate_tag",
            "rubric",
            "label",
            "notes",
        ]
        if visible_fields != expected_blinded_fields:
            raise AssertionError("R124 blinded label sheet has wrong visible columns")
        forbidden_blinded_fields = {
            "fragment_hash",
            "source",
            "model",
            "candidate_model",
            "candidate_exact_stable",
            "candidate_distinct_tags",
            "text_chars",
            "labeler_1",
            "labeler_2",
            "adjudicated_label",
        }
        if forbidden_blinded_fields & set(visible_fields):
            raise AssertionError("R124 blinded label sheet exposes hidden source fields")
        if len(blinded_rows) != len(tag_packet_rows):
            raise AssertionError("R124 blinded label sheet row count does not match R122 packet")
        if any(row.get("label") or row.get("notes") for row in blinded_rows):
            raise AssertionError("R124 blinded label sheet template must not contain labels")
        blinded_manifest = json.loads(blinded_manifest_path.read_text(encoding="utf-8"))
        if blinded_manifest.get("row_count") != len(tag_packet_rows):
            raise AssertionError("R124 blinded label sheet manifest row count mismatch")
        if (blinded_manifest.get("privacy") or {}).get("public_sheet_scan", {}).get("status") != "ok":
            raise AssertionError("R124 blinded label sheet privacy scan failed")
        join_manifest_path = out_dir / "tag-adequacy-label-join-r124.json"
        adjudication_template_path = out_dir / "tag-adequacy-adjudication-template-r124.csv"
        if not join_manifest_path.exists() or not adjudication_template_path.exists():
            raise AssertionError("R124 label join protocol artifacts are missing")
        join_manifest = json.loads(join_manifest_path.read_text(encoding="utf-8"))
        if join_manifest.get("status") != "ready_for_independent_label_collection":
            raise AssertionError("default R124 join manifest must wait for independent human labels")
        if (join_manifest.get("source_packet") or {}).get("row_count") != len(tag_packet_rows):
            raise AssertionError("R124 join manifest source row count mismatch")
        if (join_manifest.get("blinded_sheet") or {}).get("row_count") != len(blinded_rows):
            raise AssertionError("R124 join manifest blinded row count mismatch")
        summary = join_manifest.get("summary") or {}
        if summary.get("labeler_1_count") or summary.get("labeler_2_count"):
            raise AssertionError("committed R124 join manifest must not contain human labels")
        if (join_manifest.get("outputs") or {}).get("joined_labels"):
            raise AssertionError("committed R124 join manifest must not point to joined human labels")
        with adjudication_template_path.open("r", encoding="utf-8", newline="") as handle:
            adjudication_reader = csv.DictReader(handle)
            adjudication_fields = list(adjudication_reader.fieldnames or [])
            adjudication_rows = list(adjudication_reader)
        expected_adjudication_fields = [
            "row_id",
            "fragment_index",
            "fragment_level",
            "candidate_tag",
            "labeler_1",
            "labeler_2",
            "adjudicated_label",
            "notes",
        ]
        if adjudication_fields != expected_adjudication_fields:
            raise AssertionError("R124 adjudication template has wrong columns")
        if adjudication_rows:
            raise AssertionError("default R124 adjudication template must be empty until labels disagree")
        tag_results = json.loads(tag_results_path.read_text(encoding="utf-8"))
        tag_summary = tag_results.get("summary", {})
        if tag_summary.get("packet_row_count") != len(tag_packet_rows):
            raise AssertionError("R124 packet row count does not match R122 packet")
        if tag_summary.get("candidate_tag_count") != len(tag_packet_rows):
            raise AssertionError("R124 candidate tag count does not match R122 packet")
        with tag_results_csv_path.open("r", encoding="utf-8", newline="") as handle:
            tag_scored_rows = list(csv.DictReader(handle))
        if len(tag_scored_rows) != len(tag_packet_rows):
            raise AssertionError("R124 scored row count does not match R122 packet")
        claim_gates_path = out_dir / "claim-gates.csv"
        if claim_gates_path.exists():
            with claim_gates_path.open("r", encoding="utf-8", newline="") as handle:
                gates = {row.get("claim"): row for row in csv.DictReader(handle)}
            c6 = gates.get("C6 tag stability and adequacy")
            if not c6 or f"tag_adequacy={tag_results.get('status')}" not in c6.get("evidence", ""):
                raise AssertionError("C6 claim gate does not include current R124 status")

    r180_path = out_dir / "model-benchmarks-r180.json"
    if r180_path.exists():
        r180 = json.loads(r180_path.read_text(encoding="utf-8"))
        if r180.get("run_id") != "R180":
            raise AssertionError("R180 model benchmark has the wrong run_id")
        aggregate = r180.get("aggregate") or {}
        if aggregate.get("total_runs") != 2700 or aggregate.get("ok_runs") != 2700:
            raise AssertionError("R180 model benchmark must contain 2700/2700 successful runs")
        if aggregate.get("failed_runs") != 0:
            raise AssertionError("R180 model benchmark has failed runs")
        bench = r180.get("bench") or {}
        if bench.get("fragment_previews_included"):
            raise AssertionError("R180 committed benchmark summary must omit fragment previews")
        models = bench.get("models") or []
        labels = {model.get("label") for model in models}
        if labels != {"0.6b", "1.1b", "3b"}:
            raise AssertionError("R180 model labels do not match the expected local models")
        size_classes = {model.get("size_class") for model in models}
        if size_classes != {"0.6b", "1b", "3b"}:
            raise AssertionError("R180 size classes do not cover 0.6b/1b/3b")
        for model in models:
            stability = model.get("stability") or {}
            if model.get("total_runs") != 900 or model.get("ok_runs") != 900:
                raise AssertionError(f"R180 {model.get('label')} did not run 900/900 valid requests")
            if stability.get("fragment_count") != 300:
                raise AssertionError(f"R180 {model.get('label')} does not cover 300 fragments")
            if model.get("invalid_tags"):
                raise AssertionError(f"R180 {model.get('label')} has invalid tags")
            if any(fragment.get("preview") for fragment in model.get("fragments", [])):
                raise AssertionError("R180 committed fragments must not include previews")
        discovery = r180.get("model_discovery") or {}
        if discovery.get("missing_size_classes"):
            raise AssertionError("R180 should not report missing 0.6b/1b/3b size classes")
        interpretation = " ".join(str(item) for item in r180.get("interpretation") or [])
        if "human adequacy" not in interpretation or "not a controlled" not in interpretation:
            raise AssertionError("R180 interpretation must preserve adequacy and comparability limits")
        claim_gates_path = out_dir / "claim-gates.csv"
        if claim_gates_path.exists():
            with claim_gates_path.open("r", encoding="utf-8", newline="") as handle:
                gates = {row.get("claim"): row for row in csv.DictReader(handle)}
            c2 = gates.get("C2 one-word tags in stack grammar")
            c6 = gates.get("C6 tag stability and adequacy")
            if not c2 or "model_benchmark=R180" not in c2.get("evidence", ""):
                raise AssertionError("C2 claim gate does not include current R180 benchmark")
            if not c6 or "model_benchmark=R180" not in c6.get("evidence", ""):
                raise AssertionError("C6 claim gate does not include current R180 benchmark")

    r182_path = out_dir / "live-network-r182.json"
    if r182_path.exists():
        r182 = json.loads(r182_path.read_text(encoding="utf-8"))
        if r182.get("run_id") != "R182":
            raise AssertionError("R182 network lineage artifact has the wrong run_id")
        if r182.get("status") not in {"ok", "partial"}:
            raise AssertionError("R182 network lineage artifact has an unexpected status")
        boundary = str(r182.get("boundary") or "")
        if "C5" not in boundary or "C6" not in boundary:
            raise AssertionError("R182 boundary must explicitly exclude C5/C6 outcome evidence")
        aggregate = r182.get("aggregate") or {}
        network = r182.get("network_aggregate") or {}
        tasks = r182.get("tasks") or []
        task_count = aggregate.get("tasks")
        if task_count != len(tasks):
            raise AssertionError("R182 aggregate task count does not match task rows")
        if len(r182.get("manifest") or []) != len(tasks):
            raise AssertionError("R182 manifest task count does not match task rows")
        for row in tasks:
            if "network_lineage" not in row:
                raise AssertionError("R182 task row is missing network_lineage")
        if r182.get("status") == "ok":
            if network.get("network_effect_events", 0) <= 0:
                raise AssertionError("R182 ok status requires observed network effects")
            if network.get("joined_network_effect_events", 0) <= 0:
                raise AssertionError("R182 ok status requires joined network effects")
            if network.get("orphan_network_effect_events", 0) != 0:
                raise AssertionError("R182 ok status requires zero orphan network effects")
            if network.get("target_specific_network_effect_events", 0) <= 0:
                raise AssertionError("R182 ok status requires target-specific loopback or child-process network effects")
            if network.get("joined_target_specific_network_effect_events", 0) != network.get("target_specific_network_effect_events", 0):
                raise AssertionError("R182 ok status requires all target-specific network effects to join")
            if network.get("orphan_target_specific_network_effect_events", 0) != 0:
                raise AssertionError("R182 ok status requires zero target-specific network orphans")
            if aggregate.get("precision_pct", 0.0) < 98.0 or aggregate.get("recall_pct", 0.0) < 95.0:
                raise AssertionError("R182 ok status requires precision/recall thresholds")
            if aggregate.get("negative_effect_events_observed", 0) <= 0:
                raise AssertionError("R182 ok status requires observed negative controls")
            if aggregate.get("negative_joined_effect_events", 0) != 0:
                raise AssertionError("R182 ok status requires zero joined negative-control effects")
            if aggregate.get("negative_control_tasks_observed", 0) != len(tasks):
                raise AssertionError("R182 ok status requires negative controls for every task")

    r184_path = out_dir / "weak-accept-gate-r184.json"
    if r184_path.exists():
        r184 = json.loads(r184_path.read_text(encoding="utf-8"))
        if r184.get("run_id") != "R184":
            raise AssertionError("R184 weak-accept gate has the wrong run_id")
        c5 = r184.get("c5_user_utility") or {}
        c6 = r184.get("c6_tag_adequacy") or {}
        overall = r184.get("overall") or {}
        if c5.get("supported") != bool(c5.get("c5_supported")):
            raise AssertionError("R184 C5 supported flag must match c5_supported")
        if c6.get("supported") != bool(c6.get("adequacy_supported")):
            raise AssertionError("R184 C6 supported flag must match adequacy_supported")
        if overall.get("human_evidence_supported") != bool(c5.get("supported") and c6.get("supported")):
            raise AssertionError("R184 human evidence gate must require both C5 and C6")
        if "subagent review" not in (overall.get("disallowed_evidence") or []):
            raise AssertionError("R184 must reject subagent review as C5/C6 evidence")
        if "LLM-filled labels" not in (overall.get("disallowed_evidence") or []):
            raise AssertionError("R184 must reject LLM-filled labels as C6 evidence")
        if not overall.get("human_evidence_supported") and r184.get("status") != "not_weak_accept":
            raise AssertionError("R184 must remain not_weak_accept while human evidence is missing")

    r170_path = out_dir / "full-history-r170.json"
    if r170_path.exists():
        r170 = json.loads(r170_path.read_text(encoding="utf-8"))
        if r170.get("status") != "full_history_refresh_passed":
            raise AssertionError("R170 full-history refresh did not pass")
        r170_summary = r170.get("summary") or {}
        if not r170_summary.get("session_count") or not r170_summary.get("system_observations"):
            raise AssertionError("R170 summary is missing full-history counts")
        if not (r170.get("integrity") or {}).get("all_folded_totals_match_report"):
            raise AssertionError("R170 folded totals do not match the report")
        r170_llm = r170.get("llm_tagger") or {}
        if r170_llm.get("failure_count") != 0:
            raise AssertionError("R170 LLM tagger reported failures")
        if r170_llm.get("requests", 0) < r170_llm.get("cache_hits", 0):
            raise AssertionError("R170 cache hits cannot exceed tag requests")
        if r170_llm.get("final_cache_tags", 0) < r170_llm.get("seed_cache_tags", 0):
            raise AssertionError("R170 final cache must include the seeded cache")
        boundary = r170.get("claim_boundary", "")
        if "does not provide human tag adequacy" not in boundary or "developer utility" not in boundary:
            raise AssertionError("R170 claim boundary must exclude C5/C6 outcome evidence")

    for path in out_dir.glob("*"):
        if path.suffix in {".json", ".csv", ".txt", ".html", ".svg"}:
            assert_no_sensitive_text(path)

    return {"status": "ok", **checks}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent / "out"))
    return parser


if __name__ == "__main__":
    result = run(Path(build_parser().parse_args().out))
    print(json.dumps(result, indent=2))
