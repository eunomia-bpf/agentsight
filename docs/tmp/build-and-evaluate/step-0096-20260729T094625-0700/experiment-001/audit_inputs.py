#!/usr/bin/env python3
"""Audit operation coverage and model-visible target-label absence."""

from __future__ import annotations

import json
from pathlib import Path

import run_annotation


HERE = Path(__file__).resolve().parent
TARGETS = (
    run_annotation.REPO
    / "docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl"
)
OPERATION_USAGE = run_annotation.OPERATION_USAGE


def flatten_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from flatten_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from flatten_strings(item)


def main() -> int:
    packets = run_annotation.load_packets()
    packet_strings = set()
    packet_strings_by_field = {}
    visible_fields = set()
    operations = set()
    for packet in packets:
        packet_strings.update(flatten_strings(packet))
        for key, value in packet.items():
            packet_strings_by_field.setdefault(key, set()).update(flatten_strings(value))
        visible_fields.update(packet)
        for turn in packet["turns"]:
            visible_fields.update(f"turns.{key}" for key in turn)
            operations.update(
                (str(packet["session"]), str(item)) for item in turn["operation_ids"]
            )
    target_labels = set()
    target_rows = 0
    with TARGETS.open(encoding="utf-8") as stream:
        for line in stream:
            json.loads(line)
            target_rows += 1
    selected_sessions = {str(packet["session"]) for packet in packets}
    with OPERATION_USAGE.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if str(row["session"]) in selected_sessions:
                target_labels.add(str(row["official_stage"]))
    collisions = sorted(target_labels & packet_strings)
    substring_collisions = []
    for field, values in packet_strings_by_field.items():
        for label in target_labels:
            if any(label in value for value in values):
                substring_collisions.append({"field": field, "target_label": label})
                break
    report = {
        "model_visible_top_level_and_turn_fields": sorted(visible_fields),
        "target_label_count": len(target_labels),
        "exact_target_labels_visible": collisions,
        "exact_target_label_collision_count": len(collisions),
        "target_label_substring_collisions_by_top_level_field": substring_collisions,
        "target_label_substring_collision_field_count": len(substring_collisions),
        "packet_operation_ids": len(operations),
        "target_rows": target_rows,
        "note": "Final selected-population coverage is also checked by the scorer.",
    }
    output = HERE / "input-audit.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if collisions or substring_collisions else 0


if __name__ == "__main__":
    raise SystemExit(main())
