#!/usr/bin/env python3
"""Infer reusable operation-field mappings from labeled operation JSONL.

The output is a plain `FIELD:LABEL=REGEX` rule file accepted by
`agentpprof --op-map-file` and `script/operation_stack_quality.py
--op-map-file`. This keeps the profiler model to two abstractions: operations
and operation stacks. The learned artifact is only a source of operation-field
rewrite rules.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Predicate:
    field: str
    value: str


@dataclass(frozen=True)
class InferredRule:
    field: str
    label: str
    predicates: tuple[Predicate, ...]
    support: int
    effective_support: int
    raw_pattern: str | None = None

    @property
    def text(self) -> str:
        if self.raw_pattern is not None:
            return f"{self.field}:{self.label}=({self.raw_pattern})"
        pattern = "|".join(
            f"{predicate.field}={re.escape(predicate.value)}"
            for predicate in self.predicates
        )
        return f"{self.field}:{self.label}=({pattern})"

    def matches(self, text: str) -> bool:
        return re.search(self.text.split("=", 1)[1], text) is not None


TASK_FAMILIES: tuple[tuple[str, tuple[Predicate, ...]], ...] = (
    (
        "software",
        (
            Predicate("dataset", "swe-agent-trajectories"),
            Predicate("tool", "swe-agent"),
            Predicate("task", "software-engineering"),
        ),
    ),
    (
        "web",
        (
            Predicate("dataset", "weblinx-chat"),
            Predicate("dataset", "webshop-expert"),
            Predicate("dataset", "agenttrek"),
            Predicate("dataset", "mind2web"),
            Predicate("tool", "browser"),
            Predicate("tool", "webshop"),
            Predicate("task", "web-navigation"),
            Predicate("task", "web-automation"),
            Predicate("task", "shopping"),
            Predicate("task", "travel"),
        ),
    ),
    (
        "api",
        (
            Predicate("dataset", "api-bank"),
            Predicate("tool", "api"),
            Predicate("task", "api-call"),
        ),
    ),
    (
        "tool",
        (
            Predicate("dataset", "toolbench"),
            Predicate("task", "tool-use"),
        ),
    ),
    (
        "mobile",
        (
            Predicate("dataset", "android-control"),
            Predicate("dataset", "gui-odyssey"),
            Predicate("tool", "android"),
            Predicate("tool", "mobile-gui"),
            Predicate("task", "mobile-control"),
            Predicate("task", "mobile-cross-app"),
        ),
    ),
    (
        "desktop",
        (
            Predicate("dataset", "satraj-os-safety"),
            Predicate("dataset", "osworld-human"),
            Predicate("tool", "computer"),
            Predicate("task", "desktop-computer-use"),
        ),
    ),
)

PHASE_FAMILIES: tuple[tuple[str, tuple[Predicate, ...]], ...] = (
    (
        "finish",
        (
            Predicate("action", "submit"),
            Predicate("action", "send_msg_to_user"),
            Predicate("action", "finish"),
            Predicate("action", "complete"),
        ),
    ),
    (
        "api",
        (
            Predicate("dataset", "api-bank"),
            Predicate("dataset", "toolbench"),
            Predicate("tool", "api"),
            Predicate("task", "api-call"),
            Predicate("task", "tool-use"),
        ),
    ),
    (
        "input",
        (
            Predicate("action", "fill"),
            Predicate("action", "type"),
            Predicate("action", "text"),
            Predicate("action", "text_input"),
            Predicate("action", "key"),
            Predicate("action", "press"),
            Predicate("action", "hotkey"),
            Predicate("action", "key_down"),
            Predicate("action", "key_up"),
        ),
    ),
    (
        "navigate",
        (
            Predicate("action", "click"),
            Predicate("action", "left_click"),
            Predicate("action", "double_click"),
            Predicate("action", "triple_click"),
            Predicate("action", "right_click"),
            Predicate("action", "middle_click"),
            Predicate("action", "go"),
            Predicate("action", "goto"),
            Predicate("action", "open"),
            Predicate("action", "load"),
            Predicate("action", "open_app"),
            Predicate("action", "scroll"),
            Predicate("action", "hscroll"),
            Predicate("action", "mouse_move"),
            Predicate("action", "move_to"),
            Predicate("action", "drag"),
            Predicate("action", "left_click_drag"),
            Predicate("action", "mouse_down"),
            Predicate("action", "mouse_up"),
            Predicate("action", "select"),
        ),
    ),
    (
        "observe",
        (
            Predicate("action", "observe"),
            Predicate("action", "wait"),
            Predicate("action", "check"),
            Predicate("action", "repeat_until_done"),
        ),
    ),
    (
        "system",
        (
            Predicate("action", "shell"),
            Predicate("action", "open_file"),
            Predicate("action", "close_window"),
        ),
    ),
    (
        "fail",
        (
            Predicate("action", "fail"),
            Predicate("status", "infeasible"),
        ),
    ),
    (
        "inspect",
        (
            Predicate("action", "look"),
            Predicate("action", "search"),
            Predicate("action", "find"),
            Predicate("action", "find_file"),
            Predicate("action", "search_dir"),
            Predicate("action", "search_file"),
        ),
    ),
    (
        "modify",
        (
            Predicate("action", "edit"),
            Predicate("action", "create"),
        ),
    ),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation-file", action="append", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="Text op-map rules output")
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--min-support", type=int, default=1)
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()

    operations = []
    for path in args.operation_file:
        operations.extend(load_operations(path))
    if not operations:
        raise SystemExit("no operations loaded")

    rules = infer_rules(operations, min_support=args.min_support)
    write_rules(args.out, rules, args.operation_file)
    report = build_report(operations, rules, args.operation_file, args.top)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "operations": len(operations),
                "rules": len(rules),
                "out": str(args.out),
                "json_out": str(args.json_out),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def load_operations(path: Path) -> list[dict[str, Any]]:
    operations = []
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            if not line.strip():
                continue
            payload = json.loads(line)
            fields = normalize_fields(payload.get("fields") or {})
            operations.append(
                {
                    "fields": fields,
                    "value": int(payload.get("value") or 1),
                    "_file": str(path),
                    "_line": line_number,
                }
            )
    return operations


def normalize_fields(fields: dict[str, Any]) -> dict[str, list[str]]:
    normalized: dict[str, list[str]] = {}
    for key, value in fields.items():
        values = value if isinstance(value, list) else [value]
        labels = [stringify_label(item) for item in values]
        labels = [label for label in labels if label]
        if labels:
            normalized[str(key)] = labels
    return normalized


def stringify_label(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, ensure_ascii=True)
    return str(value)


def infer_rules(operations: list[dict[str, Any]], min_support: int) -> list[InferredRule]:
    rules = []
    for field, family_specs in (
        ("task", TASK_FAMILIES),
        ("phase", PHASE_FAMILIES),
    ):
        for label, predicates in family_specs:
            observed = tuple(
                predicate
                for predicate in predicates
                if predicate_support(operations, predicate) >= min_support
            )
            if not observed:
                continue
            support = rule_support(operations, observed)
            if support < min_support:
                continue
            rules.append(
                InferredRule(
                    field=field,
                    label=label,
                    predicates=observed,
                    support=support,
                    effective_support=0,
                )
            )
            if field == "phase" and label == "api":
                rules.extend(infer_generic_phase_rules(operations, min_support))
    effective = effective_supports(operations, rules)
    mapped = [
        InferredRule(
            field=rule.field,
            label=rule.label,
            predicates=rule.predicates,
            support=rule.support,
            effective_support=effective[(rule.field, rule.label)],
            raw_pattern=rule.raw_pattern,
        )
        for rule in rules
    ]
    return [rule for rule in mapped if rule.effective_support >= min_support]


def infer_generic_phase_rules(
    operations: list[dict[str, Any]], min_support: int
) -> list[InferredRule]:
    pattern = r"op=tool.*domain=|domain=.*op=tool"
    support = raw_rule_support(operations, pattern)
    if support < min_support:
        return []
    return [
        InferredRule(
            field="phase",
            label="api",
            predicates=(),
            support=support,
            effective_support=0,
            raw_pattern=pattern,
        )
    ]


def predicate_support(operations: list[dict[str, Any]], predicate: Predicate) -> int:
    return sum(
        operation["value"]
        for operation in operations
        if predicate.value in operation["fields"].get(predicate.field, [])
    )


def rule_support(operations: list[dict[str, Any]], predicates: tuple[Predicate, ...]) -> int:
    return sum(
        operation["value"]
        for operation in operations
        if any(
            predicate.value in operation["fields"].get(predicate.field, [])
            for predicate in predicates
        )
    )


def raw_rule_support(operations: list[dict[str, Any]], pattern: str) -> int:
    regex = re.compile(pattern)
    return sum(
        operation["value"]
        for operation in operations
        if regex.search(searchable_text(operation["fields"]))
    )


def effective_supports(
    operations: list[dict[str, Any]], rules: list[InferredRule]
) -> Counter[tuple[str, str]]:
    counts: Counter[tuple[str, str]] = Counter()
    for operation in operations:
        claimed: set[str] = set()
        text = searchable_text(operation["fields"])
        for rule in rules:
            if rule.field in claimed:
                continue
            if rule.matches(text):
                counts[(rule.field, rule.label)] += operation["value"]
                claimed.add(rule.field)
    return counts


def searchable_text(fields: dict[str, list[str]]) -> str:
    parts = []
    for key in sorted(fields):
        parts.extend(f"{key}={value}" for value in fields[key])
    return " ".join(parts)


def write_rules(paths_out: Path, rules: list[InferredRule], operation_files: list[Path]) -> None:
    paths_out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Generated by script/operation_map_infer.py",
        "# One operation-field mapping per line. Blank lines and # comments are ignored.",
    ]
    lines.extend(f"# Source: {path}" for path in operation_files)
    lines.append("")
    lines.extend(rule.text for rule in rules)
    paths_out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report(
    operations: list[dict[str, Any]],
    rules: list[InferredRule],
    operation_files: list[Path],
    top: int,
) -> dict[str, Any]:
    field_counts = {
        field: [
            {"value": value, "weight": weight}
            for value, weight in count_field(operations, field).most_common(top)
        ]
        for field in ("dataset", "task", "phase", "action", "tool")
    }
    return {
        "summary": {
            "operations": len(operations),
            "total_weight": sum(operation["value"] for operation in operations),
            "rules": len(rules),
            "rule_source": "seeded taxonomy over observed labeled operation fields",
        },
        "operation_files": [str(path) for path in operation_files],
        "rules": [
            {
                "rule": rule.text,
                "field": rule.field,
                "label": rule.label,
                "support": rule.support,
                "effective_support": rule.effective_support,
                "predicates": [
                    {"field": predicate.field, "value": predicate.value}
                    for predicate in rule.predicates
                ],
                "raw_pattern": rule.raw_pattern,
            }
            for rule in rules
        ],
        "observed_fields": field_counts,
    }


def count_field(operations: list[dict[str, Any]], field: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for operation in operations:
        for value in operation["fields"].get(field, []):
            counts[value] += operation["value"]
    return counts


if __name__ == "__main__":
    sys.exit(main())
