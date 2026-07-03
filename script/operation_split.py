#!/usr/bin/env python3
"""Split normalized operation JSONL into train/test files by operation groups.

This is a data-preparation helper for operation-stack evaluation. It preserves
operation records exactly, and only decides which operation groups go into each
file. The profiler still sees the same operation JSONL abstraction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class OperationLine:
    payload: dict[str, Any]
    raw: str
    source: str
    line_number: int


@dataclass
class Group:
    key: tuple[str, ...]
    stratify_key: tuple[str, ...]
    lines: list[OperationLine] = field(default_factory=list)

    @property
    def weight(self) -> int:
        return sum(int(line.payload.get("value") or 1) for line in self.lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation-file", action="append", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--train-ratio", type=float, default=0.7)
    parser.add_argument("--seed", default="operation-split-v1")
    parser.add_argument(
        "--group-field",
        action="append",
        default=None,
        help="Field(s) that define leakage-free groups; default: dataset,session",
    )
    parser.add_argument(
        "--stratify-field",
        action="append",
        default=None,
        help="Field(s) used for per-bucket splitting; default: dataset",
    )
    parser.add_argument("--train-name", default="train.operations.jsonl")
    parser.add_argument("--test-name", default="test.operations.jsonl")
    args = parser.parse_args()

    if not 0.0 < args.train_ratio < 1.0:
        raise SystemExit("--train-ratio must be between 0 and 1")
    group_fields = args.group_field or ["dataset", "session"]
    stratify_fields = args.stratify_field or ["dataset"]

    groups = load_groups(args.operation_file, group_fields, stratify_fields)
    if not groups:
        raise SystemExit("no operations loaded")

    train_groups, test_groups = split_groups(groups, args.train_ratio, args.seed)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    train_path = args.out_dir / args.train_name
    test_path = args.out_dir / args.test_name
    write_jsonl(train_path, train_groups)
    write_jsonl(test_path, test_groups)
    manifest = build_manifest(
        operation_files=args.operation_file,
        train_path=train_path,
        test_path=test_path,
        group_fields=group_fields,
        stratify_fields=stratify_fields,
        train_ratio=args.train_ratio,
        seed=args.seed,
        train_groups=train_groups,
        test_groups=test_groups,
    )
    manifest_path = args.out_dir / "split-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest["summary"], indent=2, sort_keys=True))
    return 0


def load_groups(
    paths: list[Path], group_fields: list[str], stratify_fields: list[str]
) -> list[Group]:
    groups: dict[tuple[str, ...], Group] = {}
    for path in paths:
        with path.open("r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, 1):
                if not line.strip():
                    continue
                payload = json.loads(line)
                fields = normalize_fields(payload.get("fields") or {})
                group_key = tuple(first_value(fields, field, "unknown") for field in group_fields)
                stratify_key = tuple(
                    first_value(fields, field, "unknown") for field in stratify_fields
                )
                group = groups.setdefault(group_key, Group(group_key, stratify_key))
                group.lines.append(
                    OperationLine(
                        payload=payload,
                        raw=line.rstrip("\n"),
                        source=str(path),
                        line_number=line_number,
                    )
                )
    return list(groups.values())


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


def first_value(fields: dict[str, list[str]], field: str, default: str) -> str:
    values = fields.get(field) or []
    return values[0] if values else default


def split_groups(
    groups: list[Group], train_ratio: float, seed: str
) -> tuple[list[Group], list[Group]]:
    buckets: dict[tuple[str, ...], list[Group]] = defaultdict(list)
    for group in groups:
        buckets[group.stratify_key].append(group)

    train: list[Group] = []
    test: list[Group] = []
    for bucket_key in sorted(buckets):
        bucket = sorted(
            buckets[bucket_key],
            key=lambda group: stable_hash(seed, bucket_key, group.key),
        )
        if len(bucket) == 1:
            train.extend(bucket)
            continue
        train_count = int(round(len(bucket) * train_ratio))
        train_count = max(1, min(len(bucket) - 1, train_count))
        train.extend(bucket[:train_count])
        test.extend(bucket[train_count:])
    return sort_groups(train), sort_groups(test)


def stable_hash(seed: str, bucket_key: tuple[str, ...], group_key: tuple[str, ...]) -> str:
    payload = json.dumps([seed, bucket_key, group_key], sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sort_groups(groups: list[Group]) -> list[Group]:
    return sorted(groups, key=lambda group: (group.stratify_key, group.key))


def write_jsonl(path: Path, groups: list[Group]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for group in groups:
            for line in group.lines:
                f.write(line.raw)
                f.write("\n")


def build_manifest(
    operation_files: list[Path],
    train_path: Path,
    test_path: Path,
    group_fields: list[str],
    stratify_fields: list[str],
    train_ratio: float,
    seed: str,
    train_groups: list[Group],
    test_groups: list[Group],
) -> dict[str, Any]:
    all_groups = train_groups + test_groups
    return {
        "summary": {
            "groups": len(all_groups),
            "train_groups": len(train_groups),
            "test_groups": len(test_groups),
            "operations": sum(len(group.lines) for group in all_groups),
            "train_operations": sum(len(group.lines) for group in train_groups),
            "test_operations": sum(len(group.lines) for group in test_groups),
            "train_weight": sum(group.weight for group in train_groups),
            "test_weight": sum(group.weight for group in test_groups),
        },
        "operation_files": [str(path) for path in operation_files],
        "train_file": str(train_path),
        "test_file": str(test_path),
        "group_fields": group_fields,
        "stratify_fields": stratify_fields,
        "train_ratio": train_ratio,
        "seed": seed,
        "by_stratum": by_stratum(train_groups, test_groups),
    }


def by_stratum(train_groups: list[Group], test_groups: list[Group]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, ...], dict[str, int]] = defaultdict(
        lambda: {
            "train_groups": 0,
            "test_groups": 0,
            "train_operations": 0,
            "test_operations": 0,
            "train_weight": 0,
            "test_weight": 0,
        }
    )
    for split, groups in (("train", train_groups), ("test", test_groups)):
        for group in groups:
            row = buckets[group.stratify_key]
            row[f"{split}_groups"] += 1
            row[f"{split}_operations"] += len(group.lines)
            row[f"{split}_weight"] += group.weight
    return [
        {"stratum": list(stratum), **values}
        for stratum, values in sorted(buckets.items())
    ]


if __name__ == "__main__":
    sys.exit(main())
