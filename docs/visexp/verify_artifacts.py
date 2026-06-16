#!/usr/bin/env python3
"""Verify generated docs/visexp artifacts are internally consistent."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


R187_FORBIDDEN_LAUNCH_KEYS = {
    "answer_format",
    "answer_json",
    "answer_key",
    "baseline_contrast",
    "oracle",
    "oracle_sources",
    "projected_stack_hash",
    "scoring",
    "skill",
    "top_full_semantic_variants",
    "top_semantic_variants",
    "full_semantic_variant_count",
    "semantic_variant_count",
    "variant_count",
    "mixing_against_full_semantics",
    "projection",
}


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


def scan_forbidden_launch_keys(value: object, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in R187_FORBIDDEN_LAUNCH_KEYS:
                hits.append(child_path)
            hits.extend(scan_forbidden_launch_keys(child, child_path))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            hits.extend(scan_forbidden_launch_keys(child, f"{path}[{idx}]"))
    return hits


def as_int(value: object) -> int:
    if value in (None, ""):
        return 0
    return int(float(str(value)))


def as_bool(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def pct(part: int | float, whole: int | float) -> float | None:
    if not whole:
        return None
    return round(100.0 * float(part) / float(whole), 3)


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_counter_text(text: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for item in str(text or "").split(";"):
        item = item.strip()
        if not item or "=" not in item:
            continue
        key, value = item.rsplit("=", 1)
        key = key.strip()
        if not key:
            continue
        counter[key] += as_int(value.strip())
    return counter


def top_k_coverage(rows: list[dict[str, str]], key: str, top_k: int) -> dict[str, int | float | None]:
    support_by_label: Counter[str] = Counter()
    for row in rows:
        label = row.get(key) or ""
        if label:
            support_by_label[label] += as_int(row.get("support"))
    total = sum(support_by_label.values())
    top_total = sum(count for _, count in support_by_label.most_common(top_k))
    return {
        "unique_labels": len(support_by_label),
        "total_support": total,
        "top_k_support": top_total,
        "top_k_coverage_pct": pct(top_total, total),
    }


def r205_dimension_metrics(rows: list[dict[str, str]], top_k: int) -> dict[str, int | float | None]:
    raw = top_k_coverage(rows, "raw_tag", top_k)
    canonical = top_k_coverage(rows, "canonical_tag", top_k)
    total_support = sum(as_int(row.get("support")) for row in rows)
    long_tail_support = sum(as_int(row.get("support")) for row in rows if as_bool(row.get("is_long_tail")))
    review_support = sum(as_int(row.get("support")) for row in rows if as_bool(row.get("requires_review")))
    raw_unique = int(raw["unique_labels"] or 0)
    canonical_unique = int(canonical["unique_labels"] or 0)
    raw_top = raw["top_k_coverage_pct"]
    canonical_top = canonical["top_k_coverage_pct"]
    return {
        "row_count": len(rows),
        "support_total": total_support,
        "raw_unique_tags": raw_unique,
        "canonical_unique_tags": canonical_unique,
        "canonical_unique_reduction": raw_unique - canonical_unique,
        "canonical_unique_reduction_pct": pct(raw_unique - canonical_unique, raw_unique),
        "raw_top20_coverage_pct": raw_top,
        "canonical_top20_coverage_pct": canonical_top,
        "top20_coverage_gain_pct_points": (
            round(float(canonical_top) - float(raw_top), 3)
            if raw_top is not None and canonical_top is not None
            else None
        ),
        "long_tail_rows": sum(1 for row in rows if as_bool(row.get("is_long_tail"))),
        "long_tail_support_pct": pct(long_tail_support, total_support),
        "review_required_rows": sum(1 for row in rows if as_bool(row.get("requires_review"))),
        "review_required_support_pct": pct(review_support, total_support),
    }


def r205_dimension_summary(rows: list[dict[str, str]], top_k: int) -> dict[str, dict[str, int | float | None]]:
    by_dimension: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_dimension[row.get("dimension") or "unknown"].append(row)
    summary = {"overall": r205_dimension_metrics(rows, top_k)}
    for dimension, group in sorted(by_dimension.items()):
        summary[dimension] = r205_dimension_metrics(group, top_k)
    return summary


def r205_canonical_map_consistency(
    r189_rows: list[dict[str, str]],
    r196_rows: list[dict[str, str]],
) -> dict[str, int | bool]:
    by_key: dict[tuple[str, str], dict[str, str]] = {}
    duplicate_keys = 0
    for row in r189_rows:
        key = (row.get("dimension", ""), row.get("raw_tag", ""))
        if key in by_key:
            duplicate_keys += 1
        by_key[key] = row

    missing = 0
    canonical_mismatches = 0
    auto_total = 0
    auto_from_merge = 0
    auto_bad = 0
    for row in r196_rows:
        key = (row.get("dimension", ""), row.get("raw_tag", ""))
        source = by_key.get(key)
        if source is None:
            missing += 1
            continue
        if source.get("canonical_tag") != row.get("canonical_tag"):
            canonical_mismatches += 1
        if row.get("governance_action") == "auto_canonicalize_existing":
            auto_total += 1
            if source.get("action") == "merge":
                auto_from_merge += 1
            else:
                auto_bad += 1

    return {
        "r189_rows": len(r189_rows),
        "r196_rows": len(r196_rows),
        "r189_duplicate_keys": duplicate_keys,
        "r196_rows_missing_from_r189": missing,
        "canonical_mismatch_rows": canonical_mismatches,
        "auto_canonicalize_existing_rows": auto_total,
        "auto_canonicalize_existing_from_r189_merge_rows": auto_from_merge,
        "auto_canonicalize_existing_bad_rows": auto_bad,
        "consistent": (
            duplicate_keys == 0
            and missing == 0
            and canonical_mismatches == 0
            and auto_total == auto_from_merge
            and len(r189_rows) == len(r196_rows)
        ),
    }


def verify_r207_launch_readiness(out_dir: Path, r207_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    r207 = json.loads(r207_path.read_text(encoding="utf-8"))

    def require(condition: bool, message: str) -> None:
        if not condition:
            raise AssertionError(message)

    require(r207.get("run_id") == "R207", "R207 human launch readiness artifact has the wrong run_id")
    require(r207.get("status") == "launch_ready_no_outcomes", "R207 should be launch-ready but outcome-empty")

    checks = r207.get("checks") or {}
    for key in [
        "source_files_ok",
        "sheet_rows_blank_and_valid",
        "response_template_blank_and_valid",
        "participant_packets_ready",
        "readmes_ok",
        "r195_awaiting_inputs",
    ]:
        require(bool(checks.get(key)), f"R207 readiness check failed: {key}")

    source_files = r207.get("source_files") or {}
    require(source_files, "R207 source_files are missing")
    for name, info in source_files.items():
        path_text = info.get("path")
        require(bool(path_text), f"R207 source file {name} is missing a path")
        path = Path(path_text)
        if not path.is_absolute():
            path = repo_root / path
        require(path.exists(), f"R207 source file {name} does not exist: {path_text}")
        actual_sha = file_sha256(path)
        require(info.get("exists"), f"R207 source file {name} is not marked existing")
        require(info.get("sha256") == actual_sha, f"R207 source file {name} sha256 is stale")
        if info.get("expected_sha256") is not None:
            require(
                info.get("expected_sha256") == actual_sha,
                f"R207 source file {name} expected sha256 does not match",
            )
        require(info.get("sha256_match"), f"R207 source file {name} reports sha256 mismatch")

    r195_path_text = ((source_files.get("r195_pipeline") or {}).get("path") or "")
    r195_path = Path(r195_path_text)
    if not r195_path.is_absolute():
        r195_path = repo_root / r195_path
    r195 = json.loads(r195_path.read_text(encoding="utf-8"))
    required_inputs = (r195.get("input_contract") or {}).get("required_inputs") or {}
    expected_required_keys = {
        "r142_responses",
        "r124_labeler_1",
        "r124_labeler_2",
        "r190_labeler_1",
        "r190_labeler_2",
        "r203_labeler_1",
        "r203_labeler_2",
    }
    require(set(required_inputs) == expected_required_keys, "R195 required input contract changed unexpectedly")

    expected_names = {
        key: Path(record.get("path", "")).name
        for key, record in required_inputs.items()
    }
    expected_paths = {
        key: record.get("path", "")
        for key, record in required_inputs.items()
    }
    return_plan = r207.get("return_file_plan") or []
    require(len(return_plan) == len(expected_required_keys), "R207 return-file plan must contain all R195 required inputs")
    actual_names: dict[str, str] = {}
    actual_paths: dict[str, str] = {}
    for row in return_plan:
        key = row.get("r195_input_key")
        require(key in expected_required_keys, f"R207 return-file plan has unknown R195 key: {key}")
        require(key not in actual_names, f"R207 return-file plan duplicates R195 key: {key}")
        actual_names[str(key)] = row.get("r195_inbox_name", "")
        actual_paths[str(key)] = row.get("r195_inbox_path", "")
        require(row.get("group"), f"R207 return-file row {key} is missing group")
        require(row.get("human_file"), f"R207 return-file row {key} is missing human_file")
        require(row.get("counts_as_evidence_when"), f"R207 return-file row {key} is missing evidence boundary")
    require(actual_names == expected_names, "R207 return-file names must be derived from R195 required input paths")
    require(actual_paths == expected_paths, "R207 return-file paths must match R195 required input paths")
    require(
        set(r207.get("r195_required_input_keys") or []) == expected_required_keys,
        "R207 recorded R195 input keys do not match the live R195 contract",
    )

    embedded_r195 = r207.get("r195_status") or {}
    require(r195.get("status") == "awaiting_human_inputs", "R195 source status should await human inputs")
    require(embedded_r195.get("status") == r195.get("status"), "R207 embedded R195 status is stale")
    require(r195.get("operations") == {}, "R195 source operations must be empty before human returns")
    require(embedded_r195.get("operations") == {}, "R207 embedded R195 operations must be empty")
    r195_gate = r195.get("claim_gate") or {}
    embedded_r195_gate = embedded_r195.get("claim_gate") or {}
    for key in [
        "c5_supported",
        "c6_adequacy_supported",
        "canonicalization_quality_supported",
        "long_tail_promotion_review_supported",
        "canonical_map_updated",
    ]:
        require(not r195_gate.get(key), f"R195 source must not enable {key}")
        require(not embedded_r195_gate.get(key), f"R207 embedded R195 gate must not enable {key}")
    require(r195_gate.get("requires_real_human_data"), "R195 source must require real human data")
    require(embedded_r195_gate.get("requires_real_human_data"), "R207 embedded R195 gate must require real human data")

    gate = r207.get("claim_gate") or {}
    require(bool(gate.get("launch_readiness_supported")), "R207 should support launch readiness only")
    for key in [
        "c5_supported",
        "c6_adequacy_supported",
        "canonicalization_quality_supported",
        "long_tail_promotion_review_supported",
        "canonical_map_updated",
        "subagent_or_llm_outputs_count_as_evidence",
    ]:
        require(not gate.get(key), f"R207 must not enable {key}")
    require(gate.get("requires_real_participants"), "R207 must require real participants")
    require(gate.get("requires_real_human_labels"), "R207 must require real human labels")

    launch_units = r207.get("launch_units") or {}
    response_template = launch_units.get("r142_response_template") or {}
    expected_conditions = {
        "trace-tree",
        "event-count-proxy",
        "flat-summary",
        "nonsemantic-stack",
        "semantic-stack",
    }
    require(response_template.get("exists"), "R207 R142 response template is missing")
    require(response_template.get("fields_match"), "R207 R142 response template fields do not match")
    require(response_template.get("blank"), "R207 R142 response template must remain blank")
    require(response_template.get("row_count") == 70, "R207 must see a 70-row R142 response template")
    require(response_template.get("real_response_like_rows") == 0, "R207 response template must not contain responses")
    require(response_template.get("participant_count") == 5, "R207 response template must cover five participants")
    require(response_template.get("task_count") == 14, "R207 response template must cover fourteen tasks")
    require(set(response_template.get("conditions") or []) == expected_conditions, "R207 response template conditions changed")

    participants = launch_units.get("r142_participants") or {}
    require(participants.get("ready"), "R207 participant packets are not ready")
    require(participants.get("packet_count") == 5, "R207 must see five R142 participant packets")
    require(participants.get("forbidden_key_hit_count") == 0, "R207 participant packets leak forbidden keys")
    for packet in participants.get("packets") or []:
        participant_id = packet.get("participant_id")
        require((packet.get("json") or {}).get("exists"), f"R207 participant {participant_id} JSON is missing")
        require((packet.get("json") or {}).get("sha256_match"), f"R207 participant {participant_id} JSON hash is stale")
        require((packet.get("md") or {}).get("exists"), f"R207 participant {participant_id} markdown is missing")
        require((packet.get("md") or {}).get("sha256_match"), f"R207 participant {participant_id} markdown hash is stale")
        require(packet.get("assignment_count") == 14, f"R207 participant {participant_id} assignment count changed")
        require(packet.get("task_count") == 14, f"R207 participant {participant_id} task count changed")
        require(not packet.get("forbidden_key_hits"), f"R207 participant {participant_id} has forbidden key hits")

    for group_key, expected_rows in [
        ("r124_sheets", 300),
        ("r190_sheets", 160),
        ("r203_sheets", 41),
    ]:
        sheets = launch_units.get(group_key) or {}
        require(set(sheets) == {"labeler_1", "labeler_2"}, f"R207 {group_key} must contain two labeler sheets")
        for labeler, sheet in sheets.items():
            require(sheet.get("exists"), f"R207 {group_key}.{labeler} is missing")
            require(sheet.get("fields_match"), f"R207 {group_key}.{labeler} fields do not match")
            require(sheet.get("blank"), f"R207 {group_key}.{labeler} must remain blank")
            require(sheet.get("row_count") == expected_rows, f"R207 {group_key}.{labeler} row count changed")
            require(sheet.get("nonblank_label_cells") == 0, f"R207 {group_key}.{labeler} contains label cells")
            require(sheet.get("rows_with_nonblank_labels") == 0, f"R207 {group_key}.{labeler} contains label rows")
            require(sheet.get("invalid_value_count") == 0, f"R207 {group_key}.{labeler} contains invalid label values")

    readmes = launch_units.get("readmes") or {}
    require(set(readmes) == {"r193", "r142", "r124", "r190", "r203"}, "R207 README checks are incomplete")
    for name, item in readmes.items():
        require(item.get("exists"), f"R207 README {name} is missing")
        require(item.get("ok"), f"R207 README {name} failed required phrase checks")
        require(not item.get("missing_required_phrases"), f"R207 README {name} is missing phrases")


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

    r187_manifest_path = out_dir / "user-task-pilot-r142" / "launch" / "manifest.json"
    if r187_manifest_path.exists():
        launch_dir = r187_manifest_path.parent
        r187 = json.loads(r187_manifest_path.read_text(encoding="utf-8"))
        if r187.get("run_id") != "R187":
            raise AssertionError("R187 launch manifest has the wrong run_id")
        if r187.get("status") != "pilot_launch_ready_no_responses":
            raise AssertionError("R187 launch manifest has the wrong status")
        if r187.get("source_protocol") != "R142":
            raise AssertionError("R187 must package the R142 protocol")
        if r187.get("participant_count") != 5 or r187.get("participant_ids") != ["P01", "P02", "P03", "P04", "P05"]:
            raise AssertionError("R187 participant IDs must be exactly P01-P05")
        if r187.get("task_count") != 14 or r187.get("assignment_count") != 70 or r187.get("packet_count") != 70:
            raise AssertionError("R187 launch counts do not match the frozen R142 packet")
        if r187.get("response_template_rows") != 70 or r187.get("real_response_count") != 0:
            raise AssertionError("R187 must contain a blank 70-row response template and zero responses")
        gate = r187.get("claim_gate") or {}
        if not gate.get("launch_ready") or gate.get("pilot_ready") or gate.get("c5_supported"):
            raise AssertionError("R187 launch package must not support pilot or C5 outcome claims")
        if not gate.get("requires_real_participants"):
            raise AssertionError("R187 must require real participants before C5 can advance")
        leak_scan = r187.get("leak_scan") or {}
        if leak_scan.get("status") != "ok" or leak_scan.get("answer_key_included"):
            raise AssertionError("R187 launch leak scan failed or included the answer key")
        if leak_scan.get("forbidden_key_hits"):
            raise AssertionError("R187 launch manifest records forbidden participant keys")
        if any(path.name == "user-task-answer-key.csv" for path in launch_dir.rglob("*") if path.is_file()):
            raise AssertionError("R187 launch directory must not include the answer key")

        response_template_path = launch_dir / "responses" / "user-task-response-template-r142-pilot.csv"
        if not response_template_path.exists():
            raise AssertionError("R187 response template is missing")
        with response_template_path.open("r", encoding="utf-8", newline="") as handle:
            response_rows = list(csv.DictReader(handle))
        if len(response_rows) != 70:
            raise AssertionError("R187 response template must have 70 rows")
        if any(
            row.get("response_json") != "{}"
            or row.get("task_time_seconds")
            or row.get("confidence")
            or row.get("notes")
            for row in response_rows
        ):
            raise AssertionError("R187 response template must remain blank")

        participants_dir = launch_dir / "participants"
        for participant_id in ["P01", "P02", "P03", "P04", "P05"]:
            json_path = participants_dir / f"{participant_id}.json"
            md_path = participants_dir / f"{participant_id}.md"
            if not json_path.exists() or not md_path.exists():
                raise AssertionError(f"R187 participant files are missing for {participant_id}")
            packet = json.loads(json_path.read_text(encoding="utf-8"))
            if packet.get("participant_id") != participant_id or packet.get("assignment_count") != 14:
                raise AssertionError(f"R187 participant packet has wrong metadata for {participant_id}")
            if len(packet.get("tasks") or []) != 14:
                raise AssertionError(f"R187 participant packet has wrong task count for {participant_id}")
            hits = scan_forbidden_launch_keys(packet)
            if hits:
                raise AssertionError(f"R187 participant packet leaks forbidden keys: {hits[:5]}")
            assert_no_sensitive_text(json_path)
            assert_no_sensitive_text(md_path)

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

    r205_path = out_dir / "long-tail-compaction-r205" / "long-tail-compaction-r205.json"
    if r205_path.exists():
        r205 = json.loads(r205_path.read_text(encoding="utf-8"))
        if r205.get("run_id") != "R205":
            raise AssertionError("R205 long-tail compaction artifact has the wrong run_id")
        if r205.get("status") != "compaction_metrics_ready_no_quality_claims":
            raise AssertionError("R205 committed artifact must remain metrics-only until human review lands")
        gate = r205.get("claim_gate") or {}
        expected_true = {
            "compaction_metrics_supported",
            "canonical_overlay_only",
            "raw_tags_preserved",
            "requires_r124_labels_for_adequacy",
            "requires_r190_labels_for_merge_quality",
            "requires_r203_labels_for_promotion_quality",
        }
        for key in expected_true:
            if not gate.get(key):
                raise AssertionError(f"R205 claim gate should enable {key}")
        expected_false = {
            "canonical_map_updated",
            "canonicalization_quality_supported",
            "community_adoption_supported",
            "developer_utility_supported",
            "long_tail_promotion_review_supported",
            "semantic_adequacy_supported",
        }
        for key in expected_false:
            if gate.get(key):
                raise AssertionError(f"R205 claim gate must not enable {key}")

        repo_root = Path(__file__).resolve().parents[2]
        r205_input = r205.get("input") or {}
        for key, recorded_hash in r205_input.items():
            if not key.endswith("_sha256"):
                continue
            path_key = key[: -len("_sha256")]
            source_path = repo_root / str(r205_input.get(path_key) or "")
            if not source_path.exists():
                raise AssertionError(f"R205 input path is missing for {path_key}")
            if file_sha256(source_path) != recorded_hash:
                raise AssertionError(f"R205 input hash mismatch for {path_key}")

        outputs = r205.get("outputs") or {}
        summary_md_path = repo_root / str(outputs.get("summary_md") or "")
        dimensions_csv_path = repo_root / str(outputs.get("dimensions_csv") or "")
        if not summary_md_path.exists() or not dimensions_csv_path.exists():
            raise AssertionError("R205 markdown or dimensions CSV output is missing")

        r189_rows = csv_rows(repo_root / str(r205_input.get("r189_map") or ""))
        r196_rows = csv_rows(repo_root / str(r205_input.get("r196_csv") or ""))
        recomputed = r205_dimension_summary(r196_rows, 20)
        consistency = r205_canonical_map_consistency(r189_rows, r196_rows)
        recorded_consistency = (
            (r205.get("input_consistency") or {}).get("r189_r196_canonical_overlay") or {}
        )
        for key, value in consistency.items():
            if recorded_consistency.get(key) != value:
                raise AssertionError(f"R205 R189/R196 consistency mismatch for {key}")
        if not consistency["consistent"]:
            raise AssertionError("R205 R196 canonical overlay is inconsistent with R189")

        metrics = (r205.get("compaction_metrics") or {}).get("overall") or {}
        recomputed_overall = recomputed["overall"]
        direct_metric_keys = [
            "row_count",
            "support_total",
            "raw_unique_tags",
            "canonical_unique_tags",
            "canonical_unique_reduction",
            "canonical_unique_reduction_pct",
            "long_tail_rows",
            "long_tail_support_pct",
            "review_required_rows",
            "review_required_support_pct",
        ]
        for key in direct_metric_keys:
            if metrics.get(key) != recomputed_overall.get(key):
                raise AssertionError(f"R205 overall metric mismatch for {key}")
        if (metrics.get("raw_top_k") or {}).get("top_k_coverage_pct") != recomputed_overall.get(
            "raw_top20_coverage_pct"
        ):
            raise AssertionError("R205 raw top-20 coverage does not match recomputed R196 rows")
        if (metrics.get("canonical_top_k") or {}).get("top_k_coverage_pct") != recomputed_overall.get(
            "canonical_top20_coverage_pct"
        ):
            raise AssertionError("R205 canonical top-20 coverage does not match recomputed R196 rows")
        if metrics.get("top_k_coverage_gain_pct_points") != recomputed_overall.get(
            "top20_coverage_gain_pct_points"
        ):
            raise AssertionError("R205 top-20 coverage gain does not match recomputed R196 rows")

        if metrics.get("raw_unique_tags") != 1546 or metrics.get("canonical_unique_tags") != 1364:
            raise AssertionError("R205 raw/canonical unique tag counts changed unexpectedly")
        if metrics.get("canonical_unique_reduction") != 182:
            raise AssertionError("R205 canonical unique reduction changed unexpectedly")
        if metrics.get("review_required_support_pct") != 1.926:
            raise AssertionError("R205 review-required support must match the committed metrics")

        dimensions = (r205.get("compaction_metrics") or {}).get("dimensions") or {}
        dimensions_csv = {row.get("dimension"): row for row in csv_rows(dimensions_csv_path)}
        for dimension, recomputed_row in recomputed.items():
            csv_row = dimensions_csv.get(dimension)
            if not csv_row:
                raise AssertionError(f"R205 dimensions CSV is missing {dimension}")
            json_row = metrics if dimension == "overall" else dimensions.get(dimension) or {}
            for key in direct_metric_keys:
                if json_row.get(key) != recomputed_row.get(key):
                    raise AssertionError(f"R205 {dimension} JSON metric mismatch for {key}")
            if json_row.get("top_k_coverage_gain_pct_points") != recomputed_row.get(
                "top20_coverage_gain_pct_points"
            ):
                raise AssertionError(f"R205 {dimension} JSON metric mismatch for top-20 gain")
            if as_int(csv_row.get("raw_unique_tags")) != recomputed_row["raw_unique_tags"]:
                raise AssertionError(f"R205 {dimension} CSV raw tag count mismatch")
            if as_int(csv_row.get("canonical_unique_tags")) != recomputed_row["canonical_unique_tags"]:
                raise AssertionError(f"R205 {dimension} CSV canonical tag count mismatch")
            if float(csv_row.get("review_required_support_pct") or 0.0) != recomputed_row[
                "review_required_support_pct"
            ]:
                raise AssertionError(f"R205 {dimension} CSV review support mismatch")

        summary_md = summary_md_path.read_text(encoding="utf-8")
        for phrase in [
            "compaction_metrics_ready_no_quality_claims",
            "raw unique tags | 1546",
            "canonical unique tags | 1364",
            "review-required support pct | 1.926",
        ]:
            if phrase not in summary_md:
                raise AssertionError(f"R205 markdown is missing required phrase: {phrase}")

        if (r205.get("regeneration") or {}).get("valid_rows") != 41:
            raise AssertionError("R205 regeneration valid row count changed unexpectedly")
        promotion = r205.get("promotion") or {}
        if promotion.get("final_label_count") != 0 or promotion.get("canonical_map_updated"):
            raise AssertionError("R205 promotion gate must remain unlabeled and map-neutral")
        merge_quality = r205.get("merge_quality") or {}
        if merge_quality.get("final_label_count") != 0:
            raise AssertionError("R205 merge-quality summary must not contain human labels")
        if merge_quality.get("overmerge_rate_pct") is not None or merge_quality.get("undermerge_rate_pct") is not None:
            raise AssertionError("R205 merge-quality rates must stay unset without human labels")

    r209_path = out_dir / "reversible-display-map-r209" / "reversible-display-map-r209.json"
    if r209_path.exists():
        r209 = json.loads(r209_path.read_text(encoding="utf-8"))
        if r209.get("run_id") != "R209":
            raise AssertionError("R209 reversible display-map artifact has the wrong run_id")
        if r209.get("status") != "reversible_display_map_ready_no_map_update":
            raise AssertionError("R209 committed artifact must not apply an unreviewed map update")
        gate = r209.get("claim_gate") or {}
        expected_true = {
            "reversible_display_map_supported",
            "raw_tags_preserved",
            "canonical_overlay_only",
            "active_alias_overlay_only",
            "no_hidden_other_bucket",
            "drilldown_available",
            "drilldown_raw_tags_complete",
            "requires_r124_labels_for_adequacy",
            "requires_r190_labels_for_merge_quality",
            "requires_r203_labels_for_promotion_quality",
        }
        for key in expected_true:
            if not gate.get(key):
                raise AssertionError(f"R209 claim gate should enable {key}")
        expected_false = {
            "canonical_map_updated",
            "regenerated_tags_active_without_review",
            "canonicalization_quality_supported",
            "long_tail_promotion_review_supported",
            "semantic_adequacy_supported",
            "developer_utility_supported",
            "community_adoption_supported",
        }
        for key in expected_false:
            if gate.get(key):
                raise AssertionError(f"R209 claim gate must not enable {key}")

        repo_root = Path(__file__).resolve().parents[2]
        r209_input = r209.get("input") or {}
        for key, recorded_hash in r209_input.items():
            if not key.endswith("_sha256"):
                continue
            path_key = key[: -len("_sha256")]
            source_path = repo_root / str(r209_input.get(path_key) or "")
            if not source_path.exists():
                raise AssertionError(f"R209 input path is missing for {path_key}")
            if file_sha256(source_path) != recorded_hash:
                raise AssertionError(f"R209 input hash mismatch for {path_key}")

        outputs = r209.get("outputs") or {}
        display_path = repo_root / str(outputs.get("active_display_map_csv") or "")
        drilldown_path = repo_root / str(outputs.get("display_drilldown_csv") or "")
        diff_path = repo_root / str(outputs.get("reviewed_display_map_diff_csv") or "")
        summary_md_path = repo_root / str(outputs.get("summary_md") or "")
        for path in [display_path, drilldown_path, diff_path, summary_md_path]:
            if not path.exists():
                raise AssertionError(f"R209 output is missing: {path}")

        r196_rows = csv_rows(repo_root / str(r209_input.get("r196_csv") or ""))
        r203_rows = csv_rows(repo_root / str(r209_input.get("r203_results") or ""))
        display_rows = csv_rows(display_path)
        drilldown_rows = csv_rows(drilldown_path)
        diff_rows = csv_rows(diff_path)

        def keyed(rows: list[dict[str, str]], label: str) -> dict[tuple[str, str], dict[str, str]]:
            out: dict[tuple[str, str], dict[str, str]] = {}
            for source_row in rows:
                key = (source_row.get("dimension", ""), source_row.get("raw_tag", ""))
                if key in out:
                    raise AssertionError(f"R209 {label} has duplicate key {key}")
                out[key] = source_row
            return out

        r196_by_key = keyed(r196_rows, "R196 input")
        r203_by_key = keyed(r203_rows, "R203 input")
        display_by_key = keyed(display_rows, "active display map")
        r196_keys = set(r196_by_key)
        display_keys = set(display_by_key)
        if r196_keys != display_keys:
            raise AssertionError("R209 active display map does not exactly cover R196 raw tags")
        if any((row.get("active_display_tag") or "").lower() in {"other", "others"} for row in display_rows):
            raise AssertionError("R209 active display map must not hide rows in other/others")
        if any(as_bool(row.get("map_update_allowed")) for row in display_rows):
            raise AssertionError("R209 must not mark map updates allowed in the committed artifact")
        if any(not as_bool(row.get("raw_drilldown_required")) for row in display_rows):
            raise AssertionError("R209 must keep raw drilldown required for every display row")
        if any(
            row.get("candidate_display_tag")
            and row.get("candidate_display_tag") == row.get("active_display_tag")
            and row.get("candidate_display_tag") != row.get("raw_tag")
            for row in display_rows
        ):
            raise AssertionError("R209 activated a regenerated candidate without a reviewed map diff")

        for key, source_row in r196_by_key.items():
            display_row = display_by_key[key]
            raw_tag = source_row.get("raw_tag", "")
            canonical_tag = source_row.get("canonical_tag", "") or raw_tag
            action = source_row.get("governance_action", "")
            reason = source_row.get("governance_reasons", "")
            is_alias_overlay = action == "auto_canonicalize_existing" and reason == "r189_alias"
            is_unreviewed_merge = (
                action == "auto_canonicalize_existing"
                and reason != "r189_alias"
                and canonical_tag != raw_tag
            )
            expected_active = canonical_tag if is_alias_overlay else raw_tag
            expected_source = (
                "r189_alias_overlay"
                if is_alias_overlay and expected_active != raw_tag
                else "raw_preserved"
            )
            direct_fields = {
                "dimension": source_row.get("dimension", ""),
                "raw_tag": raw_tag,
                "active_display_tag": expected_active,
                "active_source": expected_source,
                "canonical_tag": canonical_tag,
                "governance_action": action,
                "governance_reasons": source_row.get("governance_reasons", ""),
            }
            for field, expected in direct_fields.items():
                if display_row.get(field) != expected:
                    raise AssertionError(f"R209 display row {key} mismatch for {field}")
            if as_int(display_row.get("support")) != as_int(source_row.get("support")):
                raise AssertionError(f"R209 display row {key} copied the wrong support")
            if as_bool(display_row.get("requires_review")) != as_bool(source_row.get("requires_review")):
                raise AssertionError(f"R209 display row {key} copied the wrong requires_review flag")
            if as_bool(display_row.get("is_long_tail")) != as_bool(source_row.get("is_long_tail")):
                raise AssertionError(f"R209 display row {key} copied the wrong is_long_tail flag")

            promotion_row = r203_by_key.get(key)
            expected_candidate = ""
            expected_candidate_source = ""
            expected_candidate_state = "none"
            expected_promotion_label = ""
            expected_final_source = ""
            expected_label_state = ""
            if is_unreviewed_merge:
                expected_candidate = canonical_tag
                expected_candidate_source = "r189_profile_guarded_merge_candidate"
                expected_candidate_state = "pending_merge_review"
            if promotion_row:
                expected_promotion_label = (
                    promotion_row.get("final_label") or promotion_row.get("promotion_label", "")
                )
                expected_final_source = promotion_row.get("final_source", "")
                expected_label_state = promotion_row.get("label_state", "")
                regenerated = promotion_row.get("regenerated_tag", "")
                if regenerated and as_bool(promotion_row.get("grammar_valid")):
                    expected_candidate = regenerated
                    expected_candidate_source = "r202_llama_candidate"
                    expected_candidate_state = "pending_review"
                    if expected_promotion_label:
                        expected_candidate_state = f"reviewed_{expected_promotion_label}"
                        if expected_final_source:
                            expected_candidate_state = f"{expected_candidate_state}:{expected_final_source}"
                    if expected_label_state:
                        if not expected_final_source:
                            expected_candidate_state = f"{expected_candidate_state}:{expected_label_state}"
                        elif expected_label_state not in {"final", ""}:
                            expected_candidate_state = f"{expected_candidate_state}:{expected_label_state}"
            candidate_fields = {
                "candidate_display_tag": expected_candidate,
                "candidate_source": expected_candidate_source,
                "candidate_state": expected_candidate_state,
                "promotion_label": expected_promotion_label,
                "promotion_final_source": expected_final_source,
                "label_state": expected_label_state,
            }
            for field, expected in candidate_fields.items():
                if display_row.get(field) != expected:
                    raise AssertionError(f"R209 display row {key} mismatch for {field}")

        display_support = sum(as_int(row.get("support")) for row in display_rows)
        drilldown_support = sum(as_int(row.get("support")) for row in drilldown_rows)
        if display_support != drilldown_support:
            raise AssertionError("R209 drilldown support does not preserve display-map support")
        display_groups: defaultdict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
        for row in display_rows:
            display_groups[(row.get("dimension", ""), row.get("active_display_tag", ""))].append(row)
        seen_drilldown_keys: set[tuple[str, str]] = set()
        for row in drilldown_rows:
            key = (row.get("dimension", ""), row.get("active_display_tag", ""))
            if key in seen_drilldown_keys:
                raise AssertionError(f"R209 drilldown has duplicate display bucket {key}")
            seen_drilldown_keys.add(key)
            group = display_groups.get(key)
            if not group:
                raise AssertionError(f"R209 drilldown bucket has no display rows: {key}")
            raw_counts = Counter({item.get("raw_tag", ""): as_int(item.get("support")) for item in group})
            raw_counts.pop("", None)
            if parse_counter_text(row.get("raw_tags", "")) != raw_counts:
                raise AssertionError(f"R209 drilldown bucket {key} does not list complete raw membership")
            if as_int(row.get("raw_tag_count")) != len(group):
                raise AssertionError(f"R209 drilldown bucket {key} has wrong raw_tag_count")
            if as_int(row.get("support")) != sum(as_int(item.get("support")) for item in group):
                raise AssertionError(f"R209 drilldown bucket {key} has wrong support")
            if as_int(row.get("review_required_rows")) != sum(
                1 for item in group if as_bool(item.get("requires_review"))
            ):
                raise AssertionError(f"R209 drilldown bucket {key} has wrong review_required_rows")
            if as_int(row.get("review_required_support")) != sum(
                as_int(item.get("support")) for item in group if as_bool(item.get("requires_review"))
            ):
                raise AssertionError(f"R209 drilldown bucket {key} has wrong review_required_support")
            if as_int(row.get("long_tail_rows")) != sum(1 for item in group if as_bool(item.get("is_long_tail"))):
                raise AssertionError(f"R209 drilldown bucket {key} has wrong long_tail_rows")
            if as_int(row.get("long_tail_support")) != sum(
                as_int(item.get("support")) for item in group if as_bool(item.get("is_long_tail"))
            ):
                raise AssertionError(f"R209 drilldown bucket {key} has wrong long_tail_support")
            if as_int(row.get("candidate_rows")) != sum(1 for item in group if item.get("candidate_display_tag")):
                raise AssertionError(f"R209 drilldown bucket {key} has wrong candidate_rows")
            if as_int(row.get("active_merge_rows")) != sum(
                1 for item in group if item.get("raw_tag") != item.get("active_display_tag")
            ):
                raise AssertionError(f"R209 drilldown bucket {key} has wrong active_merge_rows")
        if set(display_groups) != seen_drilldown_keys:
            raise AssertionError("R209 drilldown buckets do not exactly cover active display buckets")

        for row in diff_rows:
            key = (row.get("dimension", ""), row.get("raw_tag", ""))
            display_row = display_by_key.get(key)
            if not display_row:
                raise AssertionError(f"R209 diff row references unknown display key {key}")
            if display_row.get("promotion_label") != "promote":
                raise AssertionError(f"R209 diff row {key} is not backed by a promote label")
            if display_row.get("promotion_final_source") not in {"consensus", "adjudicated"}:
                raise AssertionError(f"R209 diff row {key} is not backed by strong review source")
            if display_row.get("label_state") != "final":
                raise AssertionError(f"R209 diff row {key} is not backed by final label state")
            if row.get("from_display_tag") != display_row.get("active_display_tag"):
                raise AssertionError(f"R209 diff row {key} has wrong source display tag")
            if row.get("to_display_tag") != display_row.get("candidate_display_tag"):
                raise AssertionError(f"R209 diff row {key} has wrong candidate display tag")
            if as_int(row.get("support")) != as_int(display_row.get("support")):
                raise AssertionError(f"R209 diff row {key} has wrong support")
        summary = r209.get("summary") or {}
        checks = {
            "raw_tag_rows": len(r196_rows),
            "display_map_rows": len(display_rows),
            "drilldown_rows": len(drilldown_rows),
            "reviewed_diff_rows": len(diff_rows),
            "total_support": display_support,
            "active_display_unique_labels": len(
                {row.get("active_display_tag", "") for row in display_rows if row.get("active_display_tag")}
            ),
            "candidate_rows": sum(1 for row in display_rows if row.get("candidate_display_tag")),
            "active_merge_rows": sum(1 for row in display_rows if row.get("raw_tag") != row.get("active_display_tag")),
            "review_required_rows": sum(1 for row in display_rows if as_bool(row.get("requires_review"))),
            "long_tail_rows": sum(1 for row in display_rows if as_bool(row.get("is_long_tail"))),
            "drilldown_raw_tags_complete": True,
        }
        for key, value in checks.items():
            if summary.get(key) != value:
                raise AssertionError(f"R209 summary mismatch for {key}")
        if summary.get("raw_tag_rows") != 1811 or summary.get("active_display_unique_labels") != 1509:
            raise AssertionError("R209 raw/display label counts changed unexpectedly")
        if summary.get("candidate_rows") != 209 or summary.get("reviewed_diff_rows") != 0:
            raise AssertionError("R209 candidate/diff counts changed unexpectedly")
        if summary.get("pending_merge_candidate_rows") != 168:
            raise AssertionError("R209 pending merge candidate count changed unexpectedly")
        if summary.get("regenerated_candidate_rows") != 41 or summary.get("alias_active_rows") != 63:
            raise AssertionError("R209 candidate/source split changed unexpectedly")
        if summary.get("hidden_other_rows") != 0 or not summary.get("raw_coverage_complete"):
            raise AssertionError("R209 reversibility summary failed")
        if summary.get("review_required_support_pct") != 1.926:
            raise AssertionError("R209 review-required support must match committed metrics")
        summary_md = summary_md_path.read_text(encoding="utf-8")
        for phrase in [
            "reversible_display_map_ready_no_map_update",
            "raw tag rows | 1811",
            "active display labels | 1509",
            "candidate rows | 209",
            "pending merge candidate rows | 168",
            "regenerated candidate rows | 41",
            "alias active rows | 63",
            "drilldown raw tags complete | True",
            "hidden `other` rows | 0",
            "review-required support pct | 1.926",
        ]:
            if phrase not in summary_md:
                raise AssertionError(f"R209 markdown is missing required phrase: {phrase}")

    r211_path = out_dir / "stack-examples-r211" / "stack-examples-r211.json"
    if r211_path.exists():
        r211 = json.loads(r211_path.read_text(encoding="utf-8"))
        if r211.get("run_id") != "R211":
            raise AssertionError("R211 stack-example artifact has the wrong run_id")
        if r211.get("status") != "stack_examples_ready_no_outcome_claims":
            raise AssertionError("R211 committed artifact must remain figure/example evidence only")
        gate = r211.get("claim_gate") or {}
        expected_true = {
            "rq2_figure_inputs_supported",
            "reads_generated_artifacts_only",
        }
        for key in expected_true:
            if not gate.get(key):
                raise AssertionError(f"R211 claim gate should enable {key}")
        expected_false = {
            "raw_trace_read",
            "llm_called",
            "developer_utility_supported",
            "semantic_adequacy_supported",
            "exact_lineage_breadth_supported",
        }
        for key in expected_false:
            if gate.get(key):
                raise AssertionError(f"R211 claim gate must not enable {key}")

        repo_root = Path(__file__).resolve().parents[2]
        r211_input = r211.get("input") or {}
        for key, recorded_hash in r211_input.items():
            if not key.endswith("_sha256"):
                continue
            path_key = key[: -len("_sha256")]
            source_path = repo_root / str(r211_input.get(path_key) or "")
            if not source_path.exists():
                raise AssertionError(f"R211 input path is missing for {path_key}")
            if file_sha256(source_path) != recorded_hash:
                raise AssertionError(f"R211 input hash mismatch for {path_key}")

        outputs = r211.get("outputs") or {}
        required_outputs = {
            "summary_md",
            "tag_distribution_csv",
            "process_splits_csv",
            "baseline_collapse_csv",
            "top_stack_examples_csv",
            "tag_distribution_svg",
            "process_splits_svg",
        }
        missing = sorted(key for key in required_outputs if not (repo_root / str(outputs.get(key) or "")).exists())
        if missing:
            raise AssertionError(f"R211 outputs are missing: {missing}")

        tag_rows = csv_rows(repo_root / str(outputs.get("tag_distribution_csv") or ""))
        process_rows = csv_rows(repo_root / str(outputs.get("process_splits_csv") or ""))
        collapse_rows = csv_rows(repo_root / str(outputs.get("baseline_collapse_csv") or ""))
        stack_rows = csv_rows(repo_root / str(outputs.get("top_stack_examples_csv") or ""))
        summary = r211.get("summary") or {}
        expected_counts = {
            "session_count": 325,
            "system_observations": 183714,
            "semantic_system_stacks": 26829,
            "nonsemantic_system_stacks": 11967,
            "semantic_system_total_weight": 183714,
            "tag_dimensions": 6,
            "tag_distribution_rows": len(tag_rows),
            "process_split_rows": len(process_rows),
            "baseline_collapse_examples": len(collapse_rows),
            "top_stack_examples": len(stack_rows),
            "top_process_distinct_prompt_tags": 176,
            "largest_baseline_ambiguous_weight": 6820,
        }
        for key, value in expected_counts.items():
            if summary.get(key) != value:
                raise AssertionError(f"R211 summary mismatch for {key}")
        if summary.get("nonsemantic_mixed_weight_pct") != 90.402:
            raise AssertionError("R211 nonsemantic mixed-weight percentage changed unexpectedly")
        if summary.get("flat_mixed_weight_pct") != 90.918:
            raise AssertionError("R211 flat mixed-weight percentage changed unexpectedly")
        if summary.get("top_process_by_weight") != "rg":
            raise AssertionError("R211 top process should remain rg for the committed R170/R189 artifacts")
        if summary.get("largest_baseline_ambiguous_share_pct") != 51.918:
            raise AssertionError("R211 largest baseline ambiguous share changed unexpectedly")

        tag_first = tag_rows[0]
        if tag_first.get("dimension") != "session_tag_by_sessions" or tag_first.get("tag") != "review":
            raise AssertionError("R211 tag distribution first row changed unexpectedly")
        if as_int(tag_first.get("unique_tags_in_dimension")) != 60:
            raise AssertionError("R211 session tag unique count changed unexpectedly")
        process_first = process_rows[0]
        if process_first.get("process") != "rg" or as_int(process_first.get("distinct_prompt_tags")) != 176:
            raise AssertionError("R211 process split first row changed unexpectedly")
        if as_int(process_first.get("ambiguous_weight")) != 19282:
            raise AssertionError("R211 rg ambiguous weight changed unexpectedly")
        collapse_first = collapse_rows[0]
        if collapse_first.get("system_key") != "process:tool:tool;effect:process;status:ok":
            raise AssertionError("R211 baseline-collapse first key changed unexpectedly")
        if as_int(collapse_first.get("distinct_prompt_tags")) != 93:
            raise AssertionError("R211 baseline-collapse prompt count changed unexpectedly")
        if "refactor=6316" not in collapse_first.get("top_prompt_splits", ""):
            raise AssertionError("R211 baseline-collapse split text is missing refactor support")
        if "prompt:review" not in collapse_first.get("example_semantic_stacks", ""):
            raise AssertionError("R211 baseline-collapse examples do not include semantic prompt stacks")
        if stack_rows[0].get("short_stack", "").count("prompt:refactor") != 1:
            raise AssertionError("R211 top stack example lost prompt semantics")

        summary_md = (repo_root / str(outputs.get("summary_md") or "")).read_text(encoding="utf-8")
        for phrase in [
            "stack_examples_ready_no_outcome_claims",
            "Nonsemantic mixed weight: 90.402%",
            "process:git;effect:read;status:ok",
            "R211 supports figure selection",
        ]:
            if phrase not in summary_md:
                raise AssertionError(f"R211 markdown is missing required phrase: {phrase}")
        for key, title in [
            ("tag_distribution_svg", "R211 Label Distribution"),
            ("process_splits_svg", "R211 Process Split By Prompt Semantics"),
        ]:
            text = (repo_root / str(outputs.get(key) or "")).read_text(encoding="utf-8")
            if title not in text:
                raise AssertionError(f"R211 SVG {key} is missing title text")
        checks.update(
            {
                "r211_tag_distribution_rows": len(tag_rows),
                "r211_process_split_rows": len(process_rows),
                "r211_baseline_collapse_examples": len(collapse_rows),
                "r211_top_stack_examples": len(stack_rows),
            }
        )

    r212_path = out_dir / "display-compaction-ablation-r212" / "display-compaction-ablation-r212.json"
    if r212_path.exists():
        r212 = json.loads(r212_path.read_text(encoding="utf-8"))
        if r212.get("run_id") != "R212":
            raise AssertionError("R212 display-compaction artifact has the wrong run_id")
        if r212.get("status") != "display_compaction_ablation_ready_no_quality_claims":
            raise AssertionError("R212 committed artifact must remain mechanics-only")
        gate = r212.get("claim_gate") or {}
        expected_true = {
            "display_compaction_ablation_supported",
            "effect_weight_conserved",
            "r209_alias_only_active_verified",
            "reads_generated_artifacts_only",
            "requires_r190_labels_for_merge_quality",
            "requires_r203_labels_for_promotion_quality",
        }
        for key in expected_true:
            if not gate.get(key):
                raise AssertionError(f"R212 claim gate should enable {key}")
        expected_false = {
            "raw_trace_read",
            "llm_called",
            "false_merge_rate_supported",
            "missed_merge_rate_supported",
            "canonicalization_quality_supported",
            "semantic_adequacy_supported",
            "developer_utility_supported",
            "community_adoption_supported",
            "llm_token_display_compaction_supported",
        }
        for key in expected_false:
            if gate.get(key):
                raise AssertionError(f"R212 claim gate must not enable {key}")
        method = r212.get("method") or {}
        if method.get("compacted_tag_levels") != ["session", "prompt"]:
            raise AssertionError("R212 must declare session/prompt as the compacted tag levels")
        if method.get("excluded_tag_levels") != ["llm", "token"]:
            raise AssertionError("R212 must declare LLM/token display compaction out of scope")

        repo_root = Path(__file__).resolve().parents[2]
        r212_input = r212.get("input") or {}
        for key, recorded_hash in r212_input.items():
            if not key.endswith("_sha256"):
                continue
            path_key = key[: -len("_sha256")]
            source_path = repo_root / str(r212_input.get(path_key) or "")
            if not source_path.exists():
                raise AssertionError(f"R212 input path is missing for {path_key}")
            if file_sha256(source_path) != recorded_hash:
                raise AssertionError(f"R212 input hash mismatch for {path_key}")

        outputs = r212.get("outputs") or {}
        summary_md_path = repo_root / str(outputs.get("summary_md") or "")
        variant_csv_path = repo_root / str(outputs.get("variant_summary_csv") or "")
        behavior_csv_path = repo_root / str(outputs.get("behavior_ambiguity_csv") or "")
        for path in [summary_md_path, variant_csv_path, behavior_csv_path]:
            if not path.exists():
                raise AssertionError(f"R212 output is missing: {path}")

        variant_rows = csv_rows(variant_csv_path)
        behavior_rows = csv_rows(behavior_csv_path)
        if len(variant_rows) != 4 or len(behavior_rows) != 64:
            raise AssertionError("R212 variant or behavior row count changed unexpectedly")
        summary = r212.get("summary") or {}
        expected_summary = {
            "semantic_system_stacks_raw": 26829,
            "semantic_system_total_weight": 183714,
            "variant_count": 4,
            "behavior_rows": 64,
            "raw_stack_count": 26829,
            "r209_stack_count": 26612,
            "profile_guarded_stack_count": 26067,
            "r209_active_display_labels": 1509,
            "r209_active_alias_rows": 63,
            "r209_pending_merge_candidate_rows": 168,
            "r209_regenerated_candidate_rows": 41,
        }
        for key, value in expected_summary.items():
            if summary.get(key) != value:
                raise AssertionError(f"R212 summary mismatch for {key}")
        if not summary.get("effect_weight_conserved") or not summary.get("r209_alias_only_equivalent"):
            raise AssertionError("R212 must conserve weight and keep R209 alias-only equivalent")
        if summary.get("profile_guarded_unreviewed_weight_pct") != 2.532:
            raise AssertionError("R212 profile-guarded unreviewed weight changed unexpectedly")
        if summary.get("false_merge_rate_pct") is not None or summary.get("missed_merge_rate_pct") is not None:
            raise AssertionError("R212 merge-quality rates must stay unset without human labels")

        variants = {row.get("variant"): row for row in variant_rows}
        if as_int(variants["raw"].get("stack_count")) != 26829:
            raise AssertionError("R212 raw stack count changed unexpectedly")
        if as_int(variants["alias_only"].get("stack_count")) != 26612:
            raise AssertionError("R212 alias-only stack count changed unexpectedly")
        if as_int(variants["r209_conservative_display"].get("stack_count")) != 26612:
            raise AssertionError("R212 R209 stack count changed unexpectedly")
        if as_int(variants["profile_guarded_candidate_applied"].get("stack_count")) != 26067:
            raise AssertionError("R212 profile-guarded stack count changed unexpectedly")
        if as_int(variants["profile_guarded_candidate_applied"].get("unreviewed_profile_merge_weight_active")) != 4652:
            raise AssertionError("R212 profile-guarded unreviewed weight changed unexpectedly")

        behavior_by_key = {
            (row.get("behavior_key"), row.get("variant")): row for row in behavior_rows
        }
        git_raw = behavior_by_key[("process:git;effect:read;status:ok", "raw")]
        git_r209 = behavior_by_key[("process:git;effect:read;status:ok", "r209_conservative_display")]
        cargo_raw = behavior_by_key[("process:cargo;effect:test;status:ok", "raw")]
        cargo_profile = behavior_by_key[
            ("process:cargo;effect:test;status:ok", "profile_guarded_candidate_applied")
        ]
        if as_int(git_raw.get("distinct_prompt_tags")) != 146:
            raise AssertionError("R212 git/read raw prompt count changed unexpectedly")
        if as_int(git_r209.get("distinct_prompt_tags")) != 133:
            raise AssertionError("R212 git/read R209 prompt count changed unexpectedly")
        if as_int(cargo_raw.get("distinct_prompt_tags")) != 62:
            raise AssertionError("R212 cargo/test raw prompt count changed unexpectedly")
        if as_int(cargo_profile.get("distinct_prompt_tags")) != 52:
            raise AssertionError("R212 cargo/test profile prompt count changed unexpectedly")

        summary_md = summary_md_path.read_text(encoding="utf-8")
        for phrase in [
            "display_compaction_ablation_ready_no_quality_claims",
            "profile_guarded_candidate_applied",
            "process:git;effect:read;status:ok",
            "R212 conserves total system-effect weight",
            "LLM/token display compaction is out of scope",
        ]:
            if phrase not in summary_md:
                raise AssertionError(f"R212 markdown is missing required phrase: {phrase}")
        checks.update(
            {
                "r212_variant_rows": len(variant_rows),
                "r212_behavior_rows": len(behavior_rows),
                "r212_r209_stack_count": summary.get("r209_stack_count"),
                "r212_profile_guarded_stack_count": summary.get("profile_guarded_stack_count"),
            }
        )

    r213_path = out_dir / "display-mode-drilldown-r213" / "display-mode-drilldown-r213.json"
    if r213_path.exists():
        r213 = json.loads(r213_path.read_text(encoding="utf-8"))
        if r213.get("run_id") != "R213":
            raise AssertionError("R213 display-mode artifact has the wrong run_id")
        if r213.get("status") != "display_mode_drilldown_smoke_ready_no_quality_claims":
            raise AssertionError("R213 committed artifact must remain mechanics-only")
        gate = r213.get("claim_gate") or {}
        expected_true = {
            "data_layer_mode_smoke_supported",
            "all_modes_support_preserved",
            "raw_drilldown_visible",
            "display_drilldown_available",
            "pending_drilldown_available",
            "pending_membership_unchanged",
            "drilldown_membership_matches_display_map",
            "reads_generated_artifacts_only",
        }
        for key in expected_true:
            if not gate.get(key):
                raise AssertionError(f"R213 claim gate should enable {key}")
        expected_false = {
            "renderer_mode_smoke_supported",
            "raw_trace_read",
            "llm_called",
            "canonical_map_updated",
            "hidden_other_bucket",
            "semantic_adequacy_supported",
            "canonicalization_quality_supported",
            "developer_utility_supported",
            "community_adoption_supported",
        }
        for key in expected_false:
            if gate.get(key):
                raise AssertionError(f"R213 claim gate must not enable {key}")

        repo_root = Path(__file__).resolve().parents[2]
        r213_input = r213.get("input") or {}
        for key, recorded_hash in r213_input.items():
            if not key.endswith("_sha256"):
                continue
            path_key = key[: -len("_sha256")]
            source_path = repo_root / str(r213_input.get(path_key) or "")
            if not source_path.exists():
                raise AssertionError(f"R213 input path is missing for {path_key}")
            if file_sha256(source_path) != recorded_hash:
                raise AssertionError(f"R213 input hash mismatch for {path_key}")

        outputs = r213.get("outputs") or {}
        summary_md_path = repo_root / str(outputs.get("summary_md") or "")
        mode_csv_path = repo_root / str(outputs.get("mode_summary_csv") or "")
        queue_csv_path = repo_root / str(outputs.get("pending_review_queue_csv") or "")
        sample_csv_path = repo_root / str(outputs.get("sample_panels_csv") or "")
        for path in [summary_md_path, mode_csv_path, queue_csv_path, sample_csv_path]:
            if not path.exists():
                raise AssertionError(f"R213 output is missing: {path}")

        mode_rows = csv_rows(mode_csv_path)
        queue_rows = csv_rows(queue_csv_path)
        sample_rows = csv_rows(sample_csv_path)
        if len(mode_rows) != 3:
            raise AssertionError("R213 must expose exactly raw/display/pending modes")
        if len(queue_rows) != 323 or len(sample_rows) != 36:
            raise AssertionError("R213 queue or sample row count changed unexpectedly")
        summary = r213.get("summary") or {}
        expected_summary = {
            "total_support": 482398,
            "mode_count": 3,
            "raw_bucket_count": 1811,
            "display_bucket_count": 1748,
            "pending_bucket_count": 1748,
            "raw_rows": 1811,
            "drilldown_rows": 1748,
            "pending_review_queue_rows": 323,
            "candidate_overlay_rows": 209,
            "review_required_rows": 323,
            "review_required_support": 9293,
            "active_merge_rows": 63,
            "hidden_other_rows": 0,
        }
        for key, value in expected_summary.items():
            if summary.get(key) != value:
                raise AssertionError(f"R213 summary mismatch for {key}")
        for key in [
            "all_modes_support_preserved",
            "display_drilldown_available",
            "pending_drilldown_available",
            "pending_membership_unchanged",
            "drilldown_raw_tags_complete",
            "drilldown_membership_matches_display_map",
            "r209_raw_coverage_complete",
            "r209_no_hidden_other_bucket",
        ]:
            if not summary.get(key):
                raise AssertionError(f"R213 summary should enable {key}")
        if summary.get("false_merge_rate_pct") is not None or summary.get("missed_merge_rate_pct") is not None:
            raise AssertionError("R213 merge-quality rates must stay unset without human labels")

        modes = {row.get("mode"): row for row in mode_rows}
        if as_int(modes["raw"].get("bucket_count")) != 1811:
            raise AssertionError("R213 raw mode bucket count changed unexpectedly")
        if as_int(modes["display"].get("bucket_count")) != 1748:
            raise AssertionError("R213 display mode bucket count changed unexpectedly")
        if as_int(modes["pending"].get("candidate_overlay_rows")) != 209:
            raise AssertionError("R213 pending candidate overlay count changed unexpectedly")
        if as_int(modes["pending"].get("review_required_rows")) != 323:
            raise AssertionError("R213 pending review row count changed unexpectedly")
        first_queue = queue_rows[0]
        if first_queue.get("raw_tag") != "ignored" or as_int(first_queue.get("support")) != 1221:
            raise AssertionError("R213 top pending queue row changed unexpectedly")
        if "pending regenerated-label promotion review" not in first_queue.get("review_reason", ""):
            raise AssertionError("R213 top pending queue row lost its review reason")

        summary_md = summary_md_path.read_text(encoding="utf-8")
        for phrase in [
            "display_mode_drilldown_smoke_ready_no_quality_claims",
            "raw/display/pending modes preserve support",
            "Pending/review queue rows: `323`",
            "does not exercise the frontend renderer",
            "does not support semantic adequacy",
        ]:
            if phrase not in summary_md:
                raise AssertionError(f"R213 markdown is missing required phrase: {phrase}")
        checks.update(
            {
                "r213_mode_rows": len(mode_rows),
                "r213_pending_queue_rows": len(queue_rows),
                "r213_sample_panel_rows": len(sample_rows),
                "r213_display_bucket_count": summary.get("display_bucket_count"),
                "r213_review_required_support": summary.get("review_required_support"),
            }
        )

    r214_path = out_dir / "long-tail-control-r214" / "long-tail-control-r214.json"
    if r214_path.exists():
        r214 = json.loads(r214_path.read_text(encoding="utf-8"))
        if r214.get("run_id") != "R214":
            raise AssertionError("R214 long-tail control artifact has the wrong run_id")
        if r214.get("status") != "long_tail_control_loop_ready_no_quality_claims":
            raise AssertionError("R214 committed artifact must remain mechanics-only")
        gate = r214.get("claim_gate") or {}
        expected_true = {
            "long_tail_control_loop_supported",
            "active_alias_only_default",
            "pending_candidates_visible",
            "rollup_preview_supported",
            "regeneration_versioned_candidate_only",
            "review_queue_prioritized",
            "raw_tags_preserved",
            "reads_generated_artifacts_only",
        }
        for key in expected_true:
            if not gate.get(key):
                raise AssertionError(f"R214 claim gate should enable {key}")
        expected_false = {
            "raw_trace_read",
            "llm_called",
            "canonical_map_updated",
            "rollup_changes_default_membership",
            "regeneration_candidates_promoted",
            "semantic_adequacy_supported",
            "canonicalization_quality_supported",
            "developer_utility_supported",
            "frontend_renderer_supported",
        }
        for key in expected_false:
            if gate.get(key):
                raise AssertionError(f"R214 claim gate must not enable {key}")

        repo_root = Path(__file__).resolve().parents[2]
        r214_input = r214.get("input") or {}
        for key, recorded_hash in r214_input.items():
            if not key.endswith("_sha256"):
                continue
            path_key = key[: -len("_sha256")]
            source_path = repo_root / str(r214_input.get(path_key) or "")
            if not source_path.exists():
                raise AssertionError(f"R214 input path is missing for {path_key}")
            if file_sha256(source_path) != recorded_hash:
                raise AssertionError(f"R214 input hash mismatch for {path_key}")

        outputs = r214.get("outputs") or {}
        summary_md_path = repo_root / str(outputs.get("summary_md") or "")
        dimension_csv_path = repo_root / str(outputs.get("dimension_control_csv") or "")
        action_csv_path = repo_root / str(outputs.get("action_gates_csv") or "")
        trigger_csv_path = repo_root / str(outputs.get("trigger_gates_csv") or "")
        rollup_csv_path = repo_root / str(outputs.get("rollup_preview_csv") or "")
        priority_csv_path = repo_root / str(outputs.get("review_priority_csv") or "")
        for path in [summary_md_path, dimension_csv_path, action_csv_path, trigger_csv_path, rollup_csv_path, priority_csv_path]:
            if not path.exists():
                raise AssertionError(f"R214 output is missing: {path}")

        dimension_rows = csv_rows(dimension_csv_path)
        action_rows = csv_rows(action_csv_path)
        trigger_rows = csv_rows(trigger_csv_path)
        rollup_rows = csv_rows(rollup_csv_path)
        priority_rows = csv_rows(priority_csv_path)
        summary = r214.get("summary") or {}
        expected_summary = {
            "total_support": 482398,
            "raw_tag_rows": 1811,
            "active_default_merge_rows": 63,
            "active_candidate_merge_rows": 0,
            "pending_candidate_rows": 209,
            "pending_merge_candidate_rows": 168,
            "regenerated_candidate_rows": 41,
            "review_required_rows": 323,
            "review_required_support": 9293,
            "review_required_support_pct": 1.926,
            "long_tail_rows": 1575,
            "long_tail_support_pct": 1.746,
            "prompt_review_required_support_pct": 3.258,
            "prompt_long_tail_support_pct": 2.996,
            "dimension_rows": 4,
            "action_rows": 6,
            "trigger_rows": 6,
            "rollup_preview_rows": 7,
            "priority_rows": 25,
            "regeneration_attempted_rows": 41,
            "regeneration_valid_rows": 41,
            "regeneration_changed_valid_rows": 32,
            "regeneration_unique_candidate_tags": 25,
            "regeneration_promotable_rows_now": 0,
        }
        for key, value in expected_summary.items():
            if summary.get(key) != value:
                raise AssertionError(f"R214 summary mismatch for {key}")
        if summary.get("failed_triggers") != [
            "prompt_review_budget",
            "head_stability_under_high_tail_threshold",
        ]:
            raise AssertionError("R214 failed trigger set changed unexpectedly")
        for key in [
            "raw_tags_preserved",
            "no_hidden_other_bucket",
            "drilldown_membership_matches_display_map",
            "human_review_rows_available",
        ]:
            if not summary.get(key):
                raise AssertionError(f"R214 summary should enable {key}")
        if summary.get("rollup_preview_default"):
            raise AssertionError("R214 rollup preview must not become the default display membership")

        if len(dimension_rows) != 4 or len(action_rows) != 6 or len(trigger_rows) != 6 or len(rollup_rows) != 7 or len(priority_rows) != 25:
            raise AssertionError("R214 output row counts changed unexpectedly")
        prompt_row = {row.get("dimension"): row for row in dimension_rows}["prompt"]
        if prompt_row.get("governance_priority") != "prioritize_review":
            raise AssertionError("R214 prompt row should prioritize review")
        actions = {row.get("action"): row for row in action_rows}
        if as_int(actions["active_alias_display"].get("rows")) != 63:
            raise AssertionError("R214 active alias rows changed unexpectedly")
        if as_int(actions["pending_profile_merge_candidate"].get("rows")) != 168:
            raise AssertionError("R214 pending profile merge rows changed unexpectedly")
        if as_int(actions["pending_llm_regenerated_or_split_candidate"].get("rows")) != 41:
            raise AssertionError("R214 regenerated candidate rows changed unexpectedly")
        triggers = {row.get("trigger"): row for row in trigger_rows}
        if as_bool(triggers["prompt_review_budget"].get("passed")):
            raise AssertionError("R214 prompt review budget should fail in the current artifact")
        if as_bool(triggers["head_stability_under_high_tail_threshold"].get("passed")):
            raise AssertionError("R214 high-tail head stability gate should fail in the current artifact")
        rollups = {row.get("rollup_bucket"): row for row in rollup_rows}
        if as_int(rollups["head_preserved"].get("support")) != 464133:
            raise AssertionError("R214 head-preserved rollup support changed unexpectedly")
        if as_int(rollups["pending_llm_regeneration"].get("rows")) != 39:
            raise AssertionError("R214 regeneration rollup rows changed unexpectedly")
        if as_bool(rollups["pending_profile_merge"].get("active_display_allowed")):
            raise AssertionError("R214 pending profile merges must not be allowed as default")
        if as_bool(rollups["pending_llm_regeneration"].get("active_display_allowed")):
            raise AssertionError("R214 pending regeneration must not be allowed as default")
        if sum(as_int(row.get("rows")) for row in rollup_rows) != 1811:
            raise AssertionError("R214 rollup rows must partition all raw tag rows")
        if sum(as_int(row.get("support")) for row in rollup_rows) != 482398:
            raise AssertionError("R214 rollup support must preserve total support")
        r209_display_rows = csv_rows(repo_root / str(r214_input.get("r209_display_csv") or ""))
        rollup_specs = {
            "head_preserved": lambda row: row.get("governance_action") == "keep_head",
            "rare_distinct_preserved": lambda row: row.get("governance_action") == "keep_rare_distinct",
            "active_alias_overlay": lambda row: row.get("active_source") == "r189_alias_overlay",
            "pending_profile_merge": lambda row: row.get("candidate_source") == "r189_profile_guarded_merge_candidate",
            "pending_review_merge_no_candidate": lambda row: row.get("governance_action") == "review_merge",
            "pending_llm_regeneration": lambda row: row.get("governance_action") == "regenerate_candidate",
            "pending_contextual_split": lambda row: row.get("governance_action") == "contextual_split_candidate",
        }
        if set(rollups) != set(rollup_specs):
            raise AssertionError("R214 rollup buckets changed unexpectedly")
        for bucket, predicate in rollup_specs.items():
            matched = [row for row in r209_display_rows if predicate(row)]
            expected_rows = len(matched)
            expected_support = sum(as_int(row.get("support")) for row in matched)
            if as_int(rollups[bucket].get("rows")) != expected_rows:
                raise AssertionError(f"R214 rollup row count mismatch for {bucket}")
            if as_int(rollups[bucket].get("support")) != expected_support:
                raise AssertionError(f"R214 rollup support mismatch for {bucket}")
        first_priority = priority_rows[0]
        if first_priority.get("raw_tag") != "ignored" or as_int(first_priority.get("support")) != 1221:
            raise AssertionError("R214 top review-priority row changed unexpectedly")

        method = r214.get("method") or {}
        regen_policy = method.get("regeneration_version_policy") or {}
        if not regen_policy.get("candidate_only") or regen_policy.get("map_update_allowed"):
            raise AssertionError("R214 regeneration policy must remain candidate-only")
        if regen_policy.get("candidate_key") != "dimension;raw_tag;profile_hash;generator_version":
            raise AssertionError("R214 regeneration candidate key changed unexpectedly")

        summary_md = summary_md_path.read_text(encoding="utf-8")
        for phrase in [
            "long_tail_control_loop_ready_no_quality_claims",
            "active-alias-only with pending overlays",
            "Rollup preview rows: `7`; active by default: `False`",
            "The rollup preview groups raw-tag rows by governance state",
            "Failed control triggers: `prompt_review_budget, head_stability_under_high_tail_threshold`",
            "It does not prove that any candidate merge or regenerated label is correct",
        ]:
            if phrase not in summary_md:
                raise AssertionError(f"R214 markdown is missing required phrase: {phrase}")
        checks.update(
            {
                "r214_dimension_rows": len(dimension_rows),
                "r214_action_rows": len(action_rows),
                "r214_trigger_rows": len(trigger_rows),
                "r214_rollup_rows": len(rollup_rows),
                "r214_priority_rows": len(priority_rows),
                "r214_failed_triggers": len(summary.get("failed_triggers") or []),
            }
        )

    r215_path = out_dir / "frontend-renderer-mode-r215" / "frontend-renderer-mode-r215.json"
    if r215_path.exists():
        r215 = json.loads(r215_path.read_text(encoding="utf-8"))
        if r215.get("run_id") != "R215":
            raise AssertionError("R215 frontend renderer-mode artifact has the wrong run_id")
        if r215.get("status") != "frontend_renderer_mode_smoke_ready_no_quality_claims":
            raise AssertionError("R215 committed artifact must remain mechanics-only")
        gate = r215.get("claim_gate") or {}
        expected_true = {
            "frontend_renderer_model_smoke_supported",
            "support_preserved",
            "pending_membership_unchanged",
            "negative_fixtures_rejected",
            "reads_generated_artifacts_only",
        }
        for key in expected_true:
            if not gate.get(key):
                raise AssertionError(f"R215 claim gate should enable {key}")
        expected_false = {
            "raw_trace_read",
            "llm_called",
            "canonical_map_updated",
            "frontend_dom_renderer_supported",
            "semantic_adequacy_supported",
            "canonicalization_quality_supported",
            "developer_utility_supported",
            "community_adoption_supported",
        }
        for key in expected_false:
            if gate.get(key):
                raise AssertionError(f"R215 claim gate must not enable {key}")

        repo_root = Path(__file__).resolve().parents[2]
        r215_input = r215.get("input") or {}
        for key, recorded_hash in r215_input.items():
            if not key.endswith("_sha256"):
                continue
            path_key = key[: -len("_sha256")]
            source_path = repo_root / str(r215_input.get(path_key) or "")
            if not source_path.exists():
                raise AssertionError(f"R215 input path is missing for {path_key}")
            if file_sha256(source_path) != recorded_hash:
                raise AssertionError(f"R215 input hash mismatch for {path_key}")

        outputs = r215.get("outputs") or {}
        summary_md_path = repo_root / str(outputs.get("summary_md") or "")
        mode_csv_path = repo_root / str(outputs.get("mode_summary_csv") or "")
        sample_csv_path = repo_root / str(outputs.get("sample_buckets_csv") or "")
        negative_csv_path = repo_root / str(outputs.get("negative_fixtures_csv") or "")
        for path in [summary_md_path, mode_csv_path, sample_csv_path, negative_csv_path]:
            if not path.exists():
                raise AssertionError(f"R215 output is missing: {path}")

        mode_rows = csv_rows(mode_csv_path)
        sample_rows = csv_rows(sample_csv_path)
        negative_rows = csv_rows(negative_csv_path)
        if len(mode_rows) != 3 or len(sample_rows) != 36 or len(negative_rows) != 2:
            raise AssertionError("R215 output row counts changed unexpectedly")
        summary = r215.get("summary") or {}
        expected_summary = {
            "compiled_frontend_module": True,
            "node_harness_executed": True,
            "frontend_dom_renderer_exercised": False,
            "total_support": 482398,
            "raw_bucket_count": 1811,
            "display_bucket_count": 1748,
            "pending_bucket_count": 1748,
            "candidate_overlay_rows": 209,
            "review_required_rows": 323,
            "review_required_support": 9293,
            "active_merge_rows": 63,
            "hidden_other_rows": 0,
            "membership_matches_display_map": True,
            "pending_membership_equals_display": True,
            "wrong_drilldown_rejected": True,
            "candidate_promotion_rejected": True,
            "r213_display_bucket_count": 1748,
            "r214_pending_candidate_rows": 209,
        }
        for key, value in expected_summary.items():
            if summary.get(key) != value:
                raise AssertionError(f"R215 summary mismatch for {key}")
        if float(summary.get("tsc_ms") or 0) <= 0 or float(summary.get("node_ms") or 0) <= 0:
            raise AssertionError("R215 TypeScript compile and Node timings must be positive")

        modes = {row.get("mode"): row for row in mode_rows}
        if as_int(modes["raw"].get("bucket_count")) != 1811:
            raise AssertionError("R215 raw mode bucket count changed unexpectedly")
        if as_int(modes["display"].get("bucket_count")) != 1748:
            raise AssertionError("R215 display mode bucket count changed unexpectedly")
        if as_int(modes["pending"].get("candidate_overlay_rows")) != 209:
            raise AssertionError("R215 pending candidate overlay count changed unexpectedly")
        if as_int(modes["pending"].get("review_required_rows")) != 323:
            raise AssertionError("R215 pending review row count changed unexpectedly")
        negatives = {row.get("case"): row for row in negative_rows}
        for case in [
            "wrong_drilldown_raw_membership",
            "candidate_display_tag_used_as_active_membership",
        ]:
            if not as_bool(negatives[case].get("passed")) or negatives[case].get("observed") != "rejected":
                raise AssertionError(f"R215 negative fixture did not reject {case}")

        summary_md = summary_md_path.read_text(encoding="utf-8")
        for phrase in [
            "frontend_renderer_mode_smoke_ready_no_quality_claims",
            "Compiles and runs `frontend/src/utils/agentflameDisplayModes.ts` under Node",
            "Renders R209 display-map/drilldown rows and cross-checks R213/R214 summaries",
            "Does not exercise a browser DOM or visual click path",
            "wrong_drilldown_raw_membership",
            "candidate_display_tag_used_as_active_membership",
            "does not support semantic adequacy",
        ]:
            if phrase not in summary_md:
                raise AssertionError(f"R215 markdown is missing required phrase: {phrase}")
        checks.update(
            {
                "r215_mode_rows": len(mode_rows),
                "r215_sample_rows": len(sample_rows),
                "r215_negative_rows": len(negative_rows),
                "r215_display_bucket_count": summary.get("display_bucket_count"),
                "r215_review_required_rows": summary.get("review_required_rows"),
            }
        )

    r216_path = out_dir / "browser-dom-mode-r216" / "browser-dom-mode-r216.json"
    if not r216_path.exists():
        raise AssertionError("R216 browser DOM mode artifact is required once cited as completed evidence")
    if r216_path.exists():
        r216 = json.loads(r216_path.read_text(encoding="utf-8"))
        if r216.get("run_id") != "R216":
            raise AssertionError("R216 browser DOM mode artifact has the wrong run_id")
        if r216.get("status") != "browser_dom_mode_smoke_ready_no_quality_claims":
            raise AssertionError("R216 committed artifact must remain mechanics-only")
        gate = r216.get("claim_gate") or {}
        expected_true = {
            "browser_dom_mode_smoke_supported",
            "support_preserved",
            "pending_membership_unchanged",
            "negative_fixtures_rejected",
            "mode_controls_exercised",
            "browser_dom_harness_supported",
            "reads_generated_artifacts_only",
        }
        for key in expected_true:
            if not gate.get(key):
                raise AssertionError(f"R216 claim gate should enable {key}")
        expected_false = {
            "raw_trace_read",
            "llm_called",
            "canonical_map_updated",
            "production_agentflame_view_supported",
            "visual_drilldown_supported",
            "semantic_adequacy_supported",
            "canonicalization_quality_supported",
            "developer_utility_supported",
            "community_adoption_supported",
        }
        for key in expected_false:
            if gate.get(key):
                raise AssertionError(f"R216 claim gate must not enable {key}")

        repo_root = Path(__file__).resolve().parents[2]
        r216_input = r216.get("input") or {}
        for key, recorded_hash in r216_input.items():
            if not key.endswith("_sha256"):
                continue
            path_key = key[: -len("_sha256")]
            source_path = repo_root / str(r216_input.get(path_key) or "")
            if not source_path.exists():
                raise AssertionError(f"R216 input path is missing for {path_key}")
            if file_sha256(source_path) != recorded_hash:
                raise AssertionError(f"R216 input hash mismatch for {path_key}")

        outputs = r216.get("outputs") or {}
        summary_md_path = repo_root / str(outputs.get("summary_md") or "")
        mode_csv_path = repo_root / str(outputs.get("mode_summary_csv") or "")
        checks_csv_path = repo_root / str(outputs.get("dom_checks_csv") or "")
        dom_dump_path = repo_root / str(outputs.get("dom_dump_html") or "")
        screenshot_path = repo_root / str(outputs.get("screenshot_png") or "")
        for path in [summary_md_path, mode_csv_path, checks_csv_path, dom_dump_path, screenshot_path]:
            if not path.exists():
                raise AssertionError(f"R216 output is missing: {path}")
        if file_sha256(dom_dump_path) != outputs.get("dom_dump_html_sha256"):
            raise AssertionError("R216 DOM dump hash mismatch")
        if file_sha256(screenshot_path) != outputs.get("screenshot_png_sha256"):
            raise AssertionError("R216 screenshot hash mismatch")
        for path in [r216_path, summary_md_path, dom_dump_path]:
            assert_no_sensitive_text(path)

        mode_rows = csv_rows(mode_csv_path)
        dom_check_rows = csv_rows(checks_csv_path)
        if len(mode_rows) != 3 or len(dom_check_rows) != 7:
            raise AssertionError("R216 output row counts changed unexpectedly")
        summary = r216.get("summary") or {}
        expected_summary = {
            "compiled_frontend_module": True,
            "browser_dom_renderer_exercised": True,
            "production_agentflame_view_exercised": False,
            "visual_drilldown_exercised": False,
            "dom_ready": True,
            "mode_buttons": 3,
            "rendered_rows": 12,
            "mode_clicks_verified": True,
            "current_mode_after_checks": "pending",
            "visible_bucket_count": 1748,
            "visible_total_support": 482398,
            "visible_candidate_overlay_rows": 209,
            "visible_review_required_rows": 323,
            "total_support": 482398,
            "raw_bucket_count": 1811,
            "display_bucket_count": 1748,
            "pending_bucket_count": 1748,
            "candidate_overlay_rows": 209,
            "review_required_rows": 323,
            "review_required_support": 9293,
            "active_merge_rows": 63,
            "hidden_other_rows": 0,
            "membership_matches_display_map": True,
            "pending_membership_equals_display": True,
            "wrong_drilldown_rejected": True,
            "candidate_promotion_rejected": True,
            "r213_display_bucket_count": 1748,
            "r214_pending_candidate_rows": 209,
            "r215_display_bucket_count": 1748,
        }
        for key, value in expected_summary.items():
            if summary.get(key) != value:
                raise AssertionError(f"R216 summary mismatch for {key}")
        if float(summary.get("tsc_ms") or 0) <= 0 or float(summary.get("browser_ms") or 0) <= 0:
            raise AssertionError("R216 TypeScript compile and browser timings must be positive")
        if as_int(summary.get("dom_dump_bytes")) < 10000:
            raise AssertionError("R216 DOM dump is unexpectedly small")
        if as_int(summary.get("screenshot_bytes")) < 10000:
            raise AssertionError("R216 screenshot is unexpectedly small")

        modes = {row.get("mode"): row for row in mode_rows}
        if as_int(modes["raw"].get("bucket_count")) != 1811:
            raise AssertionError("R216 raw mode bucket count changed unexpectedly")
        if as_int(modes["display"].get("bucket_count")) != 1748:
            raise AssertionError("R216 display mode bucket count changed unexpectedly")
        if as_int(modes["pending"].get("candidate_overlay_rows")) != 209:
            raise AssertionError("R216 pending candidate overlay count changed unexpectedly")
        if as_int(modes["pending"].get("review_required_rows")) != 323:
            raise AssertionError("R216 pending review row count changed unexpectedly")
        check_by_name = {row.get("check"): row for row in dom_check_rows}
        for check_name in [
            "click_raw",
            "click_display",
            "click_pending",
            "membership_matches_display_map",
            "pending_membership_equals_display",
            "wrong_drilldown_rejected",
            "candidate_promotion_rejected",
        ]:
            row = check_by_name.get(check_name)
            if not row or not as_bool(row.get("passed")):
                raise AssertionError(f"R216 DOM check did not pass: {check_name}")

        summary_md = summary_md_path.read_text(encoding="utf-8")
        for phrase in [
            "browser_dom_mode_smoke_ready_no_quality_claims",
            "Compiles `frontend/src/utils/agentflameDisplayModes.ts` as a browser ES module",
            "Programmatically clicks raw/display/pending mode controls",
            "Does not exercise the production React `AgentFlameView`",
            "wrong_drilldown_rejected",
            "candidate_promotion_rejected",
            "does not support semantic adequacy",
        ]:
            if phrase not in summary_md:
                raise AssertionError(f"R216 markdown is missing required phrase: {phrase}")
        checks.update(
            {
                "r216_mode_rows": len(mode_rows),
                "r216_dom_check_rows": len(dom_check_rows),
                "r216_display_bucket_count": summary.get("display_bucket_count"),
                "r216_review_required_rows": summary.get("review_required_rows"),
                "r216_screenshot_bytes": summary.get("screenshot_bytes"),
            }
        )

    r217_path = out_dir / "production-react-display-r217" / "production-react-display-r217.json"
    if not r217_path.exists():
        raise AssertionError("R217 production React display artifact is required once cited as completed evidence")
    if r217_path.exists():
        r217 = json.loads(r217_path.read_text(encoding="utf-8"))
        if r217.get("run_id") != "R217":
            raise AssertionError("R217 production React display artifact has the wrong run_id")
        if r217.get("status") != "production_react_display_mode_smoke_ready_no_click_or_quality_claims":
            raise AssertionError("R217 committed artifact must remain mechanics-only")
        gate = r217.get("claim_gate") or {}
        expected_true = {
            "production_react_display_mode_smoke_supported",
            "built_static_frontend",
            "display_artifacts_loaded",
            "support_preserved",
            "mode_controls_rendered",
            "reads_generated_artifacts_only",
        }
        for key in expected_true:
            if not gate.get(key):
                raise AssertionError(f"R217 claim gate should enable {key}")
        expected_false = {
            "raw_trace_read",
            "llm_called",
            "canonical_map_updated",
            "mode_click_path_supported",
            "visual_drilldown_supported",
            "semantic_adequacy_supported",
            "canonicalization_quality_supported",
            "developer_utility_supported",
            "community_adoption_supported",
        }
        for key in expected_false:
            if gate.get(key):
                raise AssertionError(f"R217 claim gate must not enable {key}")

        repo_root = Path(__file__).resolve().parents[2]
        r217_input = r217.get("input") or {}
        for key, recorded_hash in r217_input.items():
            if not key.endswith("_sha256"):
                continue
            path_key = key[: -len("_sha256")]
            source_path = repo_root / str(r217_input.get(path_key) or "")
            if not source_path.exists():
                raise AssertionError(f"R217 input path is missing for {path_key}")
            if file_sha256(source_path) != recorded_hash:
                raise AssertionError(f"R217 input hash mismatch for {path_key}")

        outputs = r217.get("outputs") or {}
        summary_md_path = repo_root / str(outputs.get("summary_md") or "")
        dom_dump_path = repo_root / str(outputs.get("dom_dump_html") or "")
        screenshot_path = repo_root / str(outputs.get("screenshot_png") or "")
        fixture_display_path = repo_root / str(outputs.get("fixture_display_csv") or "")
        fixture_drilldown_path = repo_root / str(outputs.get("fixture_drilldown_csv") or "")
        for path in [summary_md_path, dom_dump_path, screenshot_path, fixture_display_path, fixture_drilldown_path]:
            if not path.exists():
                raise AssertionError(f"R217 output is missing: {path}")
        if file_sha256(dom_dump_path) != outputs.get("dom_dump_html_sha256"):
            raise AssertionError("R217 DOM dump hash mismatch")
        if file_sha256(screenshot_path) != outputs.get("screenshot_png_sha256"):
            raise AssertionError("R217 screenshot hash mismatch")
        if file_sha256(fixture_display_path) != r217_input.get("display_csv_sha256"):
            raise AssertionError("R217 fixture display CSV does not match the source display CSV")
        if file_sha256(fixture_drilldown_path) != r217_input.get("drilldown_csv_sha256"):
            raise AssertionError("R217 fixture drilldown CSV does not match the source drilldown CSV")
        for path in [r217_path, summary_md_path, dom_dump_path]:
            assert_no_sensitive_text(path)

        summary = r217.get("summary") or {}
        expected_summary = {
            "production_agentflame_view_exercised": True,
            "browser_dom_renderer_exercised": True,
            "display_panel_rendered": True,
            "mode_controls_rendered": True,
            "mode_button_count": 3,
            "default_display_mode": "display",
            "visible_bucket_count": 1748,
            "visible_total_support": 482398,
            "visible_candidate_overlay_rows": 0,
            "visible_review_required_rows": 0,
            "membership_matches_display_map": True,
        }
        for key, value in expected_summary.items():
            if summary.get(key) != value:
                raise AssertionError(f"R217 summary mismatch for {key}")
        if float(summary.get("build_ms") or 0) <= 0 or float(summary.get("browser_ms") or 0) <= 0:
            raise AssertionError("R217 frontend build and browser timings must be positive")
        if as_int(summary.get("dom_dump_bytes")) < 10000:
            raise AssertionError("R217 DOM dump is unexpectedly small")
        if as_int(summary.get("screenshot_bytes")) < 10000:
            raise AssertionError("R217 screenshot is unexpectedly small")

        summary_md = summary_md_path.read_text(encoding="utf-8")
        for phrase in [
            "production_react_display_mode_smoke_ready_no_click_or_quality_claims",
            "Builds the real Next static frontend",
            "checks the production `AgentFlameView` DOM",
            "Does not click the production controls",
            "does not support click-path interaction",
        ]:
            if phrase not in summary_md:
                raise AssertionError(f"R217 markdown is missing required phrase: {phrase}")
        checks.update(
            {
                "r217_display_bucket_count": summary.get("visible_bucket_count"),
                "r217_mode_button_count": summary.get("mode_button_count"),
                "r217_screenshot_bytes": summary.get("screenshot_bytes"),
            }
        )

    r218_path = out_dir / "display-map-update-gate-r218" / "display-map-update-gate-r218.json"
    if not r218_path.exists():
        raise AssertionError("R218 display-map update gate artifact is required once cited as completed evidence")
    if r218_path.exists():
        r218 = json.loads(r218_path.read_text(encoding="utf-8"))
        if r218.get("run_id") != "R218":
            raise AssertionError("R218 display-map update gate artifact has the wrong run_id")
        if r218.get("status") != "display_map_update_gate_ready_synthetic_review_only":
            raise AssertionError("R218 committed artifact must remain synthetic-review mechanics only")
        gate = r218.get("claim_gate") or {}
        expected_true = {
            "reviewed_display_map_update_gate_supported",
            "profile_merge_promotion_previewed",
            "llm_regeneration_promotion_previewed",
            "unsafe_promotions_rejected",
            "raw_tags_preserved",
            "support_preserved",
            "reads_generated_artifacts_only",
            "synthetic_review_fixtures_only",
        }
        for key in expected_true:
            if not gate.get(key):
                raise AssertionError(f"R218 claim gate should enable {key}")
        expected_false = {
            "raw_trace_read",
            "llm_called",
            "canonical_map_updated",
            "semantic_adequacy_supported",
            "canonicalization_quality_supported",
            "long_tail_promotion_quality_supported",
            "developer_utility_supported",
            "community_adoption_supported",
        }
        for key in expected_false:
            if gate.get(key):
                raise AssertionError(f"R218 claim gate must not enable {key}")

        repo_root = Path(__file__).resolve().parents[2]
        r218_input = r218.get("input") or {}
        for key, recorded_hash in r218_input.items():
            if not key.endswith("_sha256"):
                continue
            path_key = key[: -len("_sha256")]
            source_path = repo_root / str(r218_input.get(path_key) or "")
            if not source_path.exists():
                raise AssertionError(f"R218 input path is missing for {path_key}")
            if file_sha256(source_path) != recorded_hash:
                raise AssertionError(f"R218 input hash mismatch for {path_key}")

        outputs = r218.get("outputs") or {}
        summary_md_path = repo_root / str(outputs.get("summary_md") or "")
        fixture_csv_path = repo_root / str(outputs.get("review_fixture_csv") or "")
        diff_csv_path = repo_root / str(outputs.get("accepted_diff_csv") or "")
        rejected_csv_path = repo_root / str(outputs.get("rejected_rows_csv") or "")
        preview_csv_path = repo_root / str(outputs.get("preview_rows_csv") or "")
        for path in [summary_md_path, fixture_csv_path, diff_csv_path, rejected_csv_path, preview_csv_path]:
            if not path.exists():
                raise AssertionError(f"R218 output is missing: {path}")
        for path in [r218_path, summary_md_path, fixture_csv_path, diff_csv_path, rejected_csv_path, preview_csv_path]:
            assert_no_sensitive_text(path)

        fixture_rows = csv_rows(fixture_csv_path)
        diff_rows = csv_rows(diff_csv_path)
        rejected_rows = csv_rows(rejected_csv_path)
        preview_rows = csv_rows(preview_csv_path)
        if len(fixture_rows) != 6 or len(diff_rows) != 2 or len(rejected_rows) != 4 or len(preview_rows) != 1811:
            raise AssertionError("R218 output row counts changed unexpectedly")
        summary = r218.get("summary") or {}
        expected_summary = {
            "fixture_rows": 6,
            "expected_accepts": 2,
            "expected_rejects": 4,
            "accepted_diff_rows": 2,
            "rejected_rows": 4,
            "profile_merge_accepts": 1,
            "llm_regeneration_accepts": 1,
            "original_display_rows": 1811,
            "preview_rows": 1811,
            "original_total_support": 482398,
            "preview_total_support": 482398,
            "support_preserved": True,
            "raw_key_coverage_preserved": True,
            "preview_changed_rows": 2,
            "hidden_other_rows": 0,
            "canonical_map_updated": False,
            "raw_tags_preserved": True,
            "expected_results_matched": True,
        }
        for key, value in expected_summary.items():
            if summary.get(key) != value:
                raise AssertionError(f"R218 summary mismatch for {key}")
        reject_reasons = {row.get("reject_reason") for row in rejected_rows}
        for reason in [
            "review_not_final_consensus_or_adjudicated_promote",
            "invalid_or_forbidden_display_tag",
            "missing_source_row",
        ]:
            if reason not in reject_reasons:
                raise AssertionError(f"R218 rejected rows missing reason: {reason}")
        if any(row.get("to_display_tag") in {"other", "others"} for row in diff_rows):
            raise AssertionError("R218 accepted diff must not create an other bucket")
        summary_md = summary_md_path.read_text(encoding="utf-8")
        for phrase in [
            "display_map_update_gate_ready_synthetic_review_only",
            "Uses synthetic review fixtures over real R209 candidate rows",
            "Previews a reviewed display-map diff but does not update the canonical map",
            "Rejects unclear, weak, hidden-`other`, and missing-source promotion rows",
            "does not support any claim that the accepted fixture labels are semantically correct",
        ]:
            if phrase not in summary_md:
                raise AssertionError(f"R218 markdown is missing required phrase: {phrase}")
        checks.update(
            {
                "r218_fixture_rows": len(fixture_rows),
                "r218_accepted_diff_rows": len(diff_rows),
                "r218_rejected_rows": len(rejected_rows),
                "r218_preview_rows": len(preview_rows),
            }
        )

    r219_path = out_dir / "claim-readiness-r219" / "claim-readiness-r219.json"
    if not r219_path.exists():
        raise AssertionError("R219 claim-readiness gap artifact is required once cited as completed evidence")
    if r219_path.exists():
        r219 = json.loads(r219_path.read_text(encoding="utf-8"))
        if r219.get("run_id") != "R219":
            raise AssertionError("R219 claim-readiness artifact has the wrong run_id")
        if r219.get("status") != "osdi_weak_accept_not_supported":
            raise AssertionError("R219 committed artifact must keep the current weak-accept boundary")
        source_artifacts = r219.get("source_artifacts") or {}
        for key in [
            "r160_artifact_usability",
            "r213_display_mode",
            "r214_long_tail_control",
            "r215_frontend_renderer",
            "r216_browser_dom",
            "r217_production_react",
            "r218_update_gate",
        ]:
            if key not in source_artifacts:
                raise AssertionError(f"R219 source artifacts must include {key}")
        gate = r219.get("claim_gate") or {}
        expected_true = {
            "claim_readiness_gap_gate_supported",
            "reads_generated_artifacts_only",
            "requires_c5_human_participants",
            "requires_c6_human_labels",
            "synthetic_or_subagent_evidence_disallowed",
        }
        for key in expected_true:
            if not gate.get(key):
                raise AssertionError(f"R219 claim gate should enable {key}")
        expected_false = {
            "raw_trace_read",
            "llm_called",
            "weak_accept_supported",
        }
        for key in expected_false:
            if gate.get(key):
                raise AssertionError(f"R219 claim gate must not enable {key}")

        repo_root = Path(__file__).resolve().parents[2]
        outputs = r219.get("outputs") or {}
        claim_csv_path = repo_root / str(outputs.get("claim_csv") or "")
        rq_csv_path = repo_root / str(outputs.get("rq_csv") or "")
        next_csv_path = repo_root / str(outputs.get("next_experiments_csv") or "")
        summary_md_path = repo_root / str(outputs.get("summary_md") or "")
        for path in [claim_csv_path, rq_csv_path, next_csv_path, summary_md_path]:
            if not path.exists():
                raise AssertionError(f"R219 output is missing: {path}")
        for path in [r219_path, claim_csv_path, rq_csv_path, next_csv_path, summary_md_path]:
            assert_no_sensitive_text(path)

        summary = r219.get("summary") or {}
        expected_summary = {
            "r170_sessions": 325,
            "r170_system_observations": 183714,
            "r170_semantic_system_stacks": 26829,
            "r180_total_runs": 2700,
            "r180_ok_runs": 2700,
            "r114_precision_pct": 100.0,
            "r114_recall_pct": 100.0,
            "r114_negative_joined": 0,
            "r114_negative_observed": 3170,
            "r182_status": "partial",
            "r184_status": "not_weak_accept",
            "r195_status": "awaiting_human_inputs",
            "r160_status": "artifact_usability_smoke_passed",
            "r213_status": "display_mode_drilldown_smoke_ready_no_quality_claims",
            "r214_status": "long_tail_control_loop_ready_no_quality_claims",
            "r215_status": "frontend_renderer_mode_smoke_ready_no_quality_claims",
            "r216_status": "browser_dom_mode_smoke_ready_no_quality_claims",
            "r124_status": "human_labels_empty",
            "r190_status": "human_labels_empty",
            "r203_status": "human_labels_empty",
            "c5_participants": 0,
            "c5_responses": 0,
            "c6_final_labels": 0,
            "r217_display_buckets": 1748,
            "r217_support": 482398,
            "r218_accepted_diff_rows": 2,
            "r218_rejected_rows": 4,
            "r218_canonical_map_updated": False,
        }
        for key, value in expected_summary.items():
            if summary.get(key) != value:
                raise AssertionError(f"R219 summary mismatch for {key}")
        overall = r219.get("overall") or {}
        if overall.get("weak_accept_supported"):
            raise AssertionError("R219 must not support weak accept while C5/C6 are missing")
        for phrase in [
            "C5/RQ4 has no supported real participant outcome",
            "C6/RQ5 has no supported independent human adequacy labels",
        ]:
            if phrase not in (overall.get("blockers") or []):
                raise AssertionError(f"R219 missing blocker: {phrase}")
        for phrase in [
            "subagent review",
            "LLM-filled labels",
            "synthetic review fixtures",
        ]:
            if phrase not in (overall.get("disallowed_evidence") or []):
                raise AssertionError(f"R219 missing disallowed evidence: {phrase}")

        claim_rows = csv_rows(claim_csv_path)
        rq_rows = csv_rows(rq_csv_path)
        next_rows = csv_rows(next_csv_path)
        if len(claim_rows) != 7 or len(rq_rows) != 6 or len(next_rows) != 5:
            raise AssertionError("R219 readiness row counts changed unexpectedly")
        verdicts = {row.get("claim", "").split()[0]: row.get("verdict") for row in claim_rows}
        expected_verdicts = {
            "C1": "supported",
            "C2": "supported_for_syntax_latency",
            "C3": "supported_as_mechanism",
            "C4": "supported_for_fixed_command_mode_suite",
            "C5": "unsupported",
            "C6": "partial_syntax_stability_only",
            "C7": "partial",
        }
        for key, value in expected_verdicts.items():
            if verdicts.get(key) != value:
                raise AssertionError(f"R219 claim verdict mismatch for {key}")
        if [row.get("run_id") for row in next_rows[:2]] != ["R142-pilot-return", "R124-labels-return"]:
            raise AssertionError("R219 must keep R142 and R124 as the P0 next evidence rows")
        summary_md = summary_md_path.read_text(encoding="utf-8")
        for phrase in [
            "R219 Claim Readiness Gap Gate",
            "does not read raw agent traces",
            "Weak accept supported: `False`",
            "C5 participant responses: 0",
            "C6 final adequacy labels: 0",
        ]:
            if phrase not in summary_md:
                raise AssertionError(f"R219 markdown is missing required phrase: {phrase}")
        checks.update(
            {
                "r219_claim_rows": len(claim_rows),
                "r219_rq_rows": len(rq_rows),
                "r219_next_rows": len(next_rows),
                "r219_c5_responses": summary.get("c5_responses"),
                "r219_c6_final_labels": summary.get("c6_final_labels"),
            }
        )

    r186_path = out_dir / "osdi-plan-review-r186.md"
    if r186_path.exists():
        r186_text = r186_path.read_text(encoding="utf-8")
        required_r186_phrases = [
            "Level 3",
            "not C5/C6 outcome evidence",
            "R142 five-participant",
            "R124 human",
            "not_weak_accept",
        ]
        for phrase in required_r186_phrases:
            if phrase not in r186_text:
                raise AssertionError(f"R186 plan review is missing required phrase: {phrase}")

    r188_path = out_dir / "osdi-plan-review-r188.md"
    if r188_path.exists():
        r188_text = r188_path.read_text(encoding="utf-8")
        required_r188_phrases = [
            "Level 3",
            "Not OSDI weak accept",
            "real participant responses",
            "independent human labels",
            "R187 is launch material only",
            "cannot count for C5 or C6",
        ]
        for phrase in required_r188_phrases:
            if phrase not in r188_text:
                raise AssertionError(f"R188 plan review is missing required phrase: {phrase}")

    r206_path = out_dir / "osdi-rq-gate-review-r206.md"
    if r206_path.exists():
        r206_text = r206_path.read_text(encoding="utf-8")
        required_r206_phrases = [
            "Level 3",
            "not OSDI weak accept",
            "Plan-wording blockers: none material",
            "Evidence blockers: C5 responses and C6 human labels are mandatory",
            "semantic attribution of system effects",
            "event-count-proxy",
        ]
        for phrase in required_r206_phrases:
            if phrase not in r206_text:
                raise AssertionError(f"R206 RQ gate review is missing required phrase: {phrase}")

    r208_path = out_dir / "osdi-gate-review-r208.md"
    if r208_path.exists():
        r208_text = r208_path.read_text(encoding="utf-8")
        required_r208_phrases = [
            "Not OSDI weak accept yet",
            "Level 3",
            "reversible long-tail compaction boundary",
            "R205 compaction metrics",
            "R207 launch-readiness",
            "C5 developer utility remains unsupported",
            "C6 semantic adequacy remains unproven",
            "Compaction quality cannot be claimed from R205 alone",
            "real R142 pilot",
            "R124 adequacy labels",
        ]
        for phrase in required_r208_phrases:
            if phrase not in r208_text:
                raise AssertionError(f"R208 gate review is missing required phrase: {phrase}")

    r207_path = out_dir / "human-evidence-launch-r207" / "human-evidence-launch-r207.json"
    if r207_path.exists():
        verify_r207_launch_readiness(out_dir, r207_path)

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
