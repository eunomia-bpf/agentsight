#!/usr/bin/env python3
"""Score mapped operation stacks against labeled operation fields.

This script is intentionally parallel to `agentpprof --operation-file`: it reads
normalized operation JSONL, applies deterministic operation-field mappings, then
computes coverage, clustering alignment, and sequence-boundary quality. It does
not introduce another profiler abstraction; it evaluates operation fields and
operation stacks.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Rule:
    field: str
    label: str
    regex: re.Pattern[str]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation-file", action="append", type=Path, required=True)
    parser.add_argument("--stack", required=True, help="Comma- or semicolon-separated stack fields")
    parser.add_argument("--op-map", action="append", default=[], help="FIELD:LABEL=REGEX")
    parser.add_argument(
        "--op-map-file",
        action="append",
        type=Path,
        default=[],
        help="Read FIELD:LABEL=REGEX rules; blank lines and # comments are ignored",
    )
    parser.add_argument("--coverage-field", action="append", default=[])
    parser.add_argument("--oracle-pair", action="append", default=[], help="PREDICTED_FIELD:ORACLE_FIELD")
    parser.add_argument("--boundary-pair", action="append", default=[], help="PREDICTED_FIELD:ORACLE_FIELD")
    parser.add_argument("--sequence-field", default="session")
    parser.add_argument("--turn-field", default="turn")
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--html-out", type=Path)
    parser.add_argument("--top", type=int, default=12)
    args = parser.parse_args()

    stack = parse_stack(args.stack)
    op_maps = load_rule_lines(args.op_map, args.op_map_file)
    rules = [parse_rule(raw) for raw in op_maps]
    operations = []
    for path in args.operation_file:
        operations.extend(load_operations(path))
    mapped = [apply_rules(operation, rules) for operation in operations]

    report = build_report(
        operations=mapped,
        stack=stack,
        coverage_fields=args.coverage_field,
        oracle_pairs=[parse_pair(pair) for pair in args.oracle_pair],
        boundary_pairs=[parse_pair(pair) for pair in args.boundary_pair],
        sequence_field=args.sequence_field,
        turn_field=args.turn_field,
        top=args.top,
        operation_files=[str(path) for path in args.operation_file],
        op_maps=op_maps,
        op_map_files=[str(path) for path in args.op_map_file],
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.html_out:
        args.html_out.parent.mkdir(parents=True, exist_ok=True)
        args.html_out.write_text(render_html(report), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


def parse_stack(raw: str) -> list[str]:
    fields = [part.strip() for part in re.split(r"[,;]", raw) if part.strip()]
    if not fields:
        raise SystemExit("--stack cannot be empty")
    return fields


def load_rule_lines(inline_rules: list[str], rule_files: list[Path]) -> list[str]:
    rules = list(inline_rules)
    for path in rule_files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise SystemExit(f"failed to read --op-map-file {path}: {exc}") from exc
        for line_number, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            try:
                parse_rule(stripped)
            except SystemExit as exc:
                raise SystemExit(
                    f"invalid --op-map-file {path} line {line_number}: {exc}"
                ) from exc
            rules.append(stripped)
    return rules


def parse_rule(raw: str) -> Rule:
    left, sep, pattern = raw.partition("=")
    if not sep:
        raise SystemExit(f"invalid --op-map {raw!r}; expected FIELD:LABEL=REGEX")
    field, sep, label = left.partition(":")
    if not sep or not field or not label:
        raise SystemExit(f"invalid --op-map {raw!r}; expected FIELD:LABEL=REGEX")
    if not pattern:
        raise SystemExit(f"invalid --op-map {raw!r}; regex pattern cannot be empty")
    return Rule(field=field, label=label, regex=re.compile(pattern))


def parse_pair(raw: str) -> tuple[str, str]:
    left, sep, right = raw.partition(":")
    if not sep or not left or not right:
        raise SystemExit(f"invalid pair {raw!r}; expected LEFT:RIGHT")
    return left, right


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
                    "_ordinal": len(operations),
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


def apply_rules(operation: dict[str, Any], rules: list[Rule]) -> dict[str, Any]:
    if not rules:
        return operation
    mapped = {
        **operation,
        "fields": {key: list(values) for key, values in operation["fields"].items()},
    }
    claimed: set[str] = set()
    for rule in rules:
        if rule.field in claimed:
            continue
        if rule.regex.search(searchable_text(mapped["fields"])):
            mapped["fields"][rule.field] = [rule.label]
            claimed.add(rule.field)
    return mapped


def searchable_text(fields: dict[str, list[str]]) -> str:
    parts = []
    for key in sorted(fields):
        parts.extend(f"{key}={value}" for value in fields[key])
    return " ".join(parts)


def build_report(
    operations: list[dict[str, Any]],
    stack: list[str],
    coverage_fields: list[str],
    oracle_pairs: list[tuple[str, str]],
    boundary_pairs: list[tuple[str, str]],
    sequence_field: str,
    turn_field: str,
    top: int,
    operation_files: list[str],
    op_maps: list[str],
    op_map_files: list[str],
) -> dict[str, Any]:
    stack_counts = Counter()
    for operation in operations:
        stack_counts[stack_key(operation, stack)] += operation["value"]
    total_weight = sum(operation["value"] for operation in operations)
    coverage_names = sorted(set(coverage_fields + stack))

    report = {
        "summary": {
            "operations": len(operations),
            "total_weight": total_weight,
            "unique_stacks": len(stack_counts),
            "compression_ratio": round(total_weight / len(stack_counts), 3) if stack_counts else 0.0,
        },
        "operation_files": operation_files,
        "op_maps": op_maps,
        "op_map_files": op_map_files,
        "stack": stack,
        "coverage": coverage_report(operations, coverage_names),
        "top_stacks": [
            {"stack": stack, "weight": weight}
            for stack, weight in stack_counts.most_common(top)
        ],
        "top_by_field": top_by_field(operations, coverage_names, top),
        "oracle_alignment": [
            alignment_report(operations, predicted, oracle)
            for predicted, oracle in oracle_pairs
        ],
        "boundary_alignment": [
            boundary_report(operations, predicted, oracle, sequence_field, turn_field)
            for predicted, oracle in boundary_pairs
        ],
    }
    return report


def stack_key(operation: dict[str, Any], stack: list[str]) -> str:
    frames = []
    for field in stack:
        value = first_value(operation, field, "unknown")
        frames.append(f"{field}:{value}")
    return ";".join(frames)


def first_value(operation: dict[str, Any], field: str, default: str = "") -> str:
    values = operation["fields"].get(field) or []
    return values[0] if values else default


def coverage_report(operations: list[dict[str, Any]], fields: list[str]) -> list[dict[str, Any]]:
    total = len(operations)
    result = []
    for field in fields:
        present = sum(1 for operation in operations if first_value(operation, field))
        result.append(
            {
                "field": field,
                "present": present,
                "total": total,
                "coverage": round(present / total, 4) if total else 0.0,
            }
        )
    return result


def top_by_field(operations: list[dict[str, Any]], fields: list[str], top: int) -> dict[str, list[dict[str, Any]]]:
    output = {}
    for field in fields:
        counts = Counter()
        for operation in operations:
            value = first_value(operation, field)
            if value:
                counts[value] += operation["value"]
        output[field] = [
            {"value": value, "weight": weight}
            for value, weight in counts.most_common(top)
        ]
    return output


def alignment_report(operations: list[dict[str, Any]], predicted: str, oracle: str) -> dict[str, Any]:
    counts: Counter[tuple[str, str]] = Counter()
    pred_counts: Counter[str] = Counter()
    oracle_counts: Counter[str] = Counter()
    total = 0
    for operation in operations:
        pred = first_value(operation, predicted)
        gold = first_value(operation, oracle)
        if not pred or not gold:
            continue
        weight = operation["value"]
        counts[(pred, gold)] += weight
        pred_counts[pred] += weight
        oracle_counts[gold] += weight
        total += weight
    mi = mutual_information(counts, pred_counts, oracle_counts, total)
    h_oracle = entropy(oracle_counts, total)
    h_pred = entropy(pred_counts, total)
    homogeneity = mi / h_oracle if h_oracle else 1.0
    completeness = mi / h_pred if h_pred else 1.0
    v_measure = (
        2 * homogeneity * completeness / (homogeneity + completeness)
        if homogeneity + completeness
        else 0.0
    )
    return {
        "predicted": predicted,
        "oracle": oracle,
        "support": total,
        "predicted_labels": len(pred_counts),
        "oracle_labels": len(oracle_counts),
        "homogeneity": round(homogeneity, 4),
        "completeness": round(completeness, 4),
        "v_measure": round(v_measure, 4),
        "top_confusions": top_confusions(counts, 12),
    }


def entropy(counts: Counter[str], total: int) -> float:
    if total <= 0:
        return 0.0
    return -sum((count / total) * math.log(count / total) for count in counts.values() if count)


def mutual_information(
    counts: Counter[tuple[str, str]],
    pred_counts: Counter[str],
    oracle_counts: Counter[str],
    total: int,
) -> float:
    if total <= 0:
        return 0.0
    value = 0.0
    for (pred, oracle), count in counts.items():
        value += (count / total) * math.log((count * total) / (pred_counts[pred] * oracle_counts[oracle]))
    return value


def top_confusions(counts: Counter[tuple[str, str]], top: int) -> list[dict[str, Any]]:
    return [
        {"predicted": pred, "oracle": oracle, "weight": weight}
        for (pred, oracle), weight in counts.most_common(top)
    ]


def boundary_report(
    operations: list[dict[str, Any]],
    predicted: str,
    oracle: str,
    sequence_field: str,
    turn_field: str,
) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        sequence = first_value(operation, sequence_field, "unknown")
        groups[sequence].append(operation)
    tp = fp = fn = tn = support = 0
    for group in groups.values():
        ordered = sorted(group, key=lambda operation: turn_key(operation, turn_field))
        for previous, current in zip(ordered, ordered[1:]):
            pred_boundary = first_value(previous, predicted) != first_value(current, predicted)
            oracle_boundary = first_value(previous, oracle) != first_value(current, oracle)
            support += 1
            if pred_boundary and oracle_boundary:
                tp += 1
            elif pred_boundary:
                fp += 1
            elif oracle_boundary:
                fn += 1
            else:
                tn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "predicted": predicted,
        "oracle": oracle,
        "sequence_field": sequence_field,
        "turn_field": turn_field,
        "adjacent_pairs": support,
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def turn_key(operation: dict[str, Any], turn_field: str) -> tuple[int, str, int]:
    value = first_value(operation, turn_field)
    try:
        return int(value), value, operation["_ordinal"]
    except ValueError:
        return 0, value, operation["_ordinal"]


def render_html(report: dict[str, Any]) -> str:
    summary = report["summary"]
    sections = [
        "<!doctype html><meta charset='utf-8'><title>Operation Stack Quality</title>",
        "<style>body{font-family:system-ui,sans-serif;margin:32px;max-width:1200px}"
        "table{border-collapse:collapse;width:100%;margin:16px 0}"
        "td,th{border:1px solid #ddd;padding:6px;text-align:left;vertical-align:top}"
        "th{background:#f6f6f6}code{white-space:pre-wrap}</style>",
        "<h1>Operation Stack Quality</h1>",
        f"<p>{summary['operations']} operations, {summary['unique_stacks']} unique stacks, "
        f"compression {summary['compression_ratio']}.</p>",
        table("Coverage", report["coverage"]),
        table("Oracle Alignment", report["oracle_alignment"]),
        table("Boundary Alignment", report["boundary_alignment"]),
        table("Top Stacks", report["top_stacks"]),
    ]
    return "\n".join(sections)


def table(title: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return f"<h2>{html.escape(title)}</h2><p>None.</p>"
    keys = list(rows[0].keys())
    out = [f"<h2>{html.escape(title)}</h2><table><tr>"]
    out.extend(f"<th>{html.escape(key)}</th>" for key in keys)
    out.append("</tr>")
    for row in rows:
        out.append("<tr>")
        for key in keys:
            out.append(f"<td>{html.escape(json.dumps(row.get(key), ensure_ascii=False))}</td>")
        out.append("</tr>")
    out.append("</table>")
    return "".join(out)


if __name__ == "__main__":
    sys.exit(main())
