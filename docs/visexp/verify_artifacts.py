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
