#!/usr/bin/env python3
"""Prepare information-matched PROFILE and RAW-OPERATIONS analyst packages."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = next(
    parent for parent in SCRIPT_DIR.parents if (parent / "docs" / "visexp").is_dir()
)
DEFAULT_SOURCE = (
    REPO_ROOT
    / "docs/visexp/out/agentreward-diff-pprof-v1/"
    "agentreward-338-pairs-bad-minus-good.operations.pb.gz"
)
DEFAULT_OUTPUT_ROOT = SCRIPT_DIR / "analyst-packages"
DEFAULT_REPORT = SCRIPT_DIR / "preparation-report.json"
PROFILE_DIRNAME = "PROFILE"
RAW_DIRNAME = "RAW-OPERATIONS"
RAW_FILENAME = "samples.jsonl"

PROFILE_README = """# Analyst evidence package

This directory contains one standard pprof differential profile built from
338 same-task bad/good AgentReward pairs drawn from 440 source trajectories.
Its semantic stack is `task -> subtask -> strategy -> action -> object ->
result`.

The sample type is `operations/count`. Positive samples are operations from
the bad side of a pair and negative samples are operations from the good side.
The signed profile is bad minus good. Sample labels retain source lineage and
comparison metadata.

Inspect the profile with stock pprof, for example:

```bash
go tool pprof -top agentreward-338-pairs-bad-minus-good.operations.pb.gz
go tool pprof -tags agentreward-338-pairs-bad-minus-good.operations.pb.gz
go tool pprof -raw agentreward-338-pairs-bad-minus-good.operations.pb.gz
```

No aggregate result summary or rendered figure is included.
"""

RAW_README = """# Analyst evidence package

This directory contains flat JSONL sample tuples for 338 same-task bad/good
AgentReward pairs drawn from 440 source trajectories. The semantic stack is
`task -> subtask -> strategy -> action -> object -> result`.

Each line in `samples.jsonl` has exactly these fields:

- `sample_type`: pprof sample type;
- `unit`: pprof sample unit;
- `value`: signed sample value, with positive for the bad side and negative
  for the good side;
- `stack_frames`: ordered pprof frame names in leaf-to-root order; and
- `labels`: the exact pprof string labels, represented as key-to-value-list.

The file preserves duplicate tuples and source order. It contains no derived
rates, pair manifest, aggregate result summary, or rendered figure.

Basic inspection examples:

```bash
head -n 1 samples.jsonl | jq .
jq -c 'select(.value > 0)' samples.jsonl
jq -c 'select(.value < 0)' samples.jsonl
```
"""

SAMPLE_RE = re.compile(
    r"^\s*(?P<values>-?\d+(?:\s+-?\d+)*)\s*:\s*"
    r"(?P<locations>\d+(?:\s+\d+)*)\s*$"
)
LOCATION_RE = re.compile(r"^\s*(?P<id>\d+):\s+\S+\s+(?P<body>.*)$")
LOCATION_BODY_RE = re.compile(
    r"^(?:M=\d+\s+)?(?:\[F\]\s+)?"
    r"(?P<name>.+?)\s+\S+:-?\d+\s+s=-?\d+(?:\(.*\))?$"
)
LABEL_RE = re.compile(r"(?P<key>[^\s:\[\]]+):\[(?P<values>[^\]]*)\]")


class PreparationError(RuntimeError):
    """Raised when lossless preparation cannot be established."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_stock_pprof(source: Path, go_binary: str = "go") -> tuple[str, str]:
    command = [go_binary, "tool", "pprof", "-raw", str(source)]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise PreparationError(
            f"stock pprof failed with status {completed.returncode}: "
            f"{completed.stderr.strip()}"
        )
    return completed.stdout, completed.stderr


def parse_sample_types(line: str) -> list[tuple[str, str]]:
    sample_types: list[tuple[str, str]] = []
    for token in line.split():
        token = token.removesuffix("[dflt]")
        if "/" not in token:
            raise PreparationError(f"unrecognized sample type token: {token!r}")
        sample_type, unit = token.rsplit("/", 1)
        if not sample_type or not unit:
            raise PreparationError(f"incomplete sample type token: {token!r}")
        sample_types.append((sample_type, unit))
    if not sample_types:
        raise PreparationError("profile has no sample types")
    return sample_types


def parse_labels(line: str) -> dict[str, list[str]]:
    labels: dict[str, list[str]] = {}
    position = 0
    while position < len(line):
        while position < len(line) and line[position].isspace():
            position += 1
        if position == len(line):
            break
        match = LABEL_RE.match(line, position)
        if match is None:
            raise PreparationError(f"unrecognized pprof label text: {line!r}")
        key = match.group("key")
        if key in labels:
            raise PreparationError(f"duplicate label key in stock raw output: {key}")
        values_text = match.group("values")
        labels[key] = values_text.split() if values_text else []
        position = match.end()
    return labels


def parse_stock_raw(raw: str) -> list[dict[str, Any]]:
    """Parse stock ``go tool pprof -raw`` output into flat sample tuples.

    The fixed input uses one frame per location and string labels whose values
    contain no whitespace. Unsupported/ambiguous raw constructs fail closed.
    """

    lines = raw.splitlines()
    try:
        samples_header = lines.index("Samples:")
        locations_header = lines.index("Locations")
        mappings_header = lines.index("Mappings")
    except ValueError as exc:
        raise PreparationError("stock raw output is missing a required section") from exc
    if not samples_header < locations_header < mappings_header:
        raise PreparationError("stock raw sections are out of order")
    if samples_header + 1 >= locations_header:
        raise PreparationError("stock raw output has no sample-type line")

    sample_types = parse_sample_types(lines[samples_header + 1])
    raw_samples: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in lines[samples_header + 2 : locations_header]:
        if not line.strip():
            continue
        match = SAMPLE_RE.match(line)
        if match is not None:
            values = [int(value) for value in match.group("values").split()]
            if len(values) != len(sample_types):
                raise PreparationError(
                    "sample value count does not match sample-type count"
                )
            current = {
                "values": values,
                "location_ids": [
                    int(location) for location in match.group("locations").split()
                ],
                "labels": {},
            }
            raw_samples.append(current)
            continue
        if current is None or not line.startswith(" " * 16):
            raise PreparationError(f"unrecognized sample line: {line!r}")
        if current["labels"]:
            raise PreparationError(
                "multiple label lines are ambiguous in stock raw output; "
                "numeric labels are not supported by this fixed-input adapter"
            )
        current["labels"] = parse_labels(line.strip())

    locations: dict[int, str] = {}
    for line in lines[locations_header + 1 : mappings_header]:
        if not line.strip():
            continue
        match = LOCATION_RE.match(line)
        if match is None:
            raise PreparationError(
                "inline or otherwise unrecognized pprof location; "
                "the fixed input requires one frame per location"
            )
        location_id = int(match.group("id"))
        body_match = LOCATION_BODY_RE.match(match.group("body"))
        if body_match is None:
            raise PreparationError(f"unrecognized location line: {line!r}")
        if location_id in locations:
            raise PreparationError(f"duplicate location id: {location_id}")
        locations[location_id] = body_match.group("name")

    records: list[dict[str, Any]] = []
    for sample in raw_samples:
        try:
            stack = [locations[location] for location in sample["location_ids"]]
        except KeyError as exc:
            raise PreparationError(f"sample references unknown location {exc.args[0]}") from exc
        for index, (sample_type, unit) in enumerate(sample_types):
            records.append(
                {
                    "sample_type": sample_type,
                    "unit": unit,
                    "value": sample["values"][index],
                    "stack_frames": stack,
                    "labels": sample["labels"],
                }
            )
    if not records:
        raise PreparationError("profile contains no samples")
    return records


def tuple_key(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        record["sample_type"],
        record["unit"],
        record["value"],
        tuple(record["stack_frames"]),
        tuple(
            (key, tuple(values))
            for key, values in sorted(record["labels"].items())
        ),
    )


def tuple_multiset(records: Iterable[dict[str, Any]]) -> Counter[tuple[Any, ...]]:
    return Counter(tuple_key(record) for record in records)


def mass_inventory(records: Iterable[dict[str, Any]]) -> dict[str, dict[str, int]]:
    grouped: dict[tuple[str, str], list[int]] = defaultdict(list)
    for record in records:
        grouped[(record["sample_type"], record["unit"])].append(record["value"])
    inventory: dict[str, dict[str, int]] = {}
    for (sample_type, unit), values in sorted(grouped.items()):
        inventory[f"{sample_type}/{unit}"] = {
            "positive": sum(value for value in values if value > 0),
            "negative": sum(value for value in values if value < 0),
            "negative_magnitude": -sum(value for value in values if value < 0),
            "net": sum(values),
            "absolute": sum(abs(value) for value in values),
            "zero_sample_count": sum(value == 0 for value in values),
        }
    return inventory


def distinct_value_inventory(values: Iterable[str]) -> dict[str, Any]:
    distinct = sorted(set(values))
    result: dict[str, Any] = {
        "json_type": "string",
        "distinct_count": len(distinct),
    }
    encoded = "\n".join(distinct).encode("utf-8")
    result["distinct_values_sha256"] = hashlib.sha256(encoded).hexdigest()
    if len(distinct) <= 64:
        result["literal_values"] = distinct
    return result


def field_inventory(records: list[dict[str, Any]]) -> dict[str, Any]:
    label_values: dict[str, list[str]] = defaultdict(list)
    frame_classes: set[str] = set()
    value_classes: set[str] = set()
    for record in records:
        value = record["value"]
        value_classes.add("positive" if value > 0 else "negative" if value < 0 else "zero")
        for frame in record["stack_frames"]:
            frame_classes.add(frame.split(":", 1)[0] if ":" in frame else "unprefixed")
        for key, values in record["labels"].items():
            label_values[key].extend(values)

    return {
        "top_level_fields": [
            "sample_type",
            "unit",
            "value",
            "stack_frames",
            "labels",
        ],
        "sample_type": distinct_value_inventory(
            record["sample_type"] for record in records
        ),
        "unit": distinct_value_inventory(record["unit"] for record in records),
        "value": {
            "json_type": "integer",
            "literal_classes": sorted(value_classes),
        },
        "stack_frames": {
            "json_type": "array[string]",
            "order": "leaf_to_root",
            "literal_classes": sorted(frame_classes),
        },
        "labels": {
            "json_type": "object[string,array[string]]",
            "keys": {
                key: distinct_value_inventory(values)
                for key, values in sorted(label_values.items())
            },
        },
    }


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    expected_fields = {
        "sample_type",
        "unit",
        "value",
        "stack_frames",
        "labels",
    }
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            record = json.loads(line)
            if set(record) != expected_fields:
                raise PreparationError(
                    f"{path.name}:{line_number} has unexpected fields: {sorted(record)}"
                )
            records.append(record)
    return records


def prepare_directory(path: Path, expected_names: set[str]) -> None:
    if path.is_symlink():
        raise PreparationError(f"package directory may not be a symlink: {path}")
    path.mkdir(parents=True, exist_ok=True)
    unexpected = {entry.name for entry in path.iterdir()} - expected_names
    if unexpected:
        raise PreparationError(
            f"refusing to retain unrelated files in isolated package {path}: "
            f"{sorted(unexpected)}"
        )


def relative_or_absolute(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def prepare_packages(
    source: Path,
    output_root: Path,
    report_path: Path,
    go_binary: str = "go",
) -> dict[str, Any]:
    source = source.resolve()
    if not source.is_file():
        raise PreparationError(f"source profile does not exist: {source}")

    raw_text, pprof_stderr = run_stock_pprof(source, go_binary)
    source_records = parse_stock_raw(raw_text)

    profile_dir = output_root / PROFILE_DIRNAME
    raw_dir = output_root / RAW_DIRNAME
    profile_name = source.name
    prepare_directory(profile_dir, {profile_name, "README.md"})
    prepare_directory(raw_dir, {RAW_FILENAME, "README.md"})

    profile_copy = profile_dir / profile_name
    shutil.copyfile(source, profile_copy)
    (profile_dir / "README.md").write_text(PROFILE_README, encoding="utf-8")

    raw_path = raw_dir / RAW_FILENAME
    with raw_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in source_records:
            handle.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
            )
    (raw_dir / "README.md").write_text(RAW_README, encoding="utf-8")

    reconstructed = read_jsonl(raw_path)
    source_multiset = tuple_multiset(source_records)
    reconstructed_multiset = tuple_multiset(reconstructed)
    missing = source_multiset - reconstructed_multiset
    extra = reconstructed_multiset - source_multiset
    source_mass = mass_inventory(source_records)
    reconstructed_mass = mass_inventory(reconstructed)
    source_sha = sha256_file(source)
    copied_sha = sha256_file(profile_copy)
    equality = (
        not missing
        and not extra
        and source_mass == reconstructed_mass
        and source_sha == copied_sha
    )
    if not equality:
        raise PreparationError("package reconstruction or profile copy is not lossless")

    profile_files = sorted(path for path in profile_dir.iterdir() if path.is_file())
    raw_files = sorted(path for path in raw_dir.iterdir() if path.is_file())
    report: dict[str, Any] = {
        "schema_version": 1,
        "source": {
            "profile": relative_or_absolute(source),
            "sha256": source_sha,
            "stock_command": [
                go_binary,
                "tool",
                "pprof",
                "-raw",
                relative_or_absolute(source),
            ],
            "stock_stderr": pprof_stderr.strip(),
        },
        "packages": {
            PROFILE_DIRNAME: {
                "directory": relative_or_absolute(profile_dir),
                "files": {
                    path.name: {
                        "bytes": path.stat().st_size,
                        "sha256": sha256_file(path),
                    }
                    for path in profile_files
                },
                "model_visible_data_classes": [
                    "neutral population and stack description",
                    "standard pprof sample types and units",
                    "signed sample values",
                    "ordered stack frame names",
                    "pprof string labels",
                ],
            },
            RAW_DIRNAME: {
                "directory": relative_or_absolute(raw_dir),
                "files": {
                    path.name: {
                        "bytes": path.stat().st_size,
                        "sha256": sha256_file(path),
                    }
                    for path in raw_files
                },
                "model_visible_data_classes": [
                    "neutral population and tuple-schema description",
                    "sample type and unit literals",
                    "signed integer values",
                    "leaf-to-root stack frame strings",
                    "exact pprof string-label keys and values",
                ],
            },
        },
        "field_inventory": field_inventory(reconstructed),
        "tuple_equivalence": {
            "stock_raw_tuple_count": len(source_records),
            "jsonl_tuple_count": len(reconstructed),
            "stock_raw_unique_tuple_count": len(source_multiset),
            "jsonl_unique_tuple_count": len(reconstructed_multiset),
            "missing_tuple_count": sum(missing.values()),
            "extra_tuple_count": sum(extra.values()),
            "complete_multiset_equal": not missing and not extra,
        },
        "mass_conservation": {
            "stock_raw": source_mass,
            "jsonl": reconstructed_mass,
            "equal": source_mass == reconstructed_mass,
        },
        "sha256_checks": {
            "source_profile": source_sha,
            "profile_package_copy": copied_sha,
            "profile_copy_equal": source_sha == copied_sha,
            "raw_jsonl": sha256_file(raw_path),
        },
        "content_boundary": {
            "profile_package_unexpected_files": [],
            "raw_package_unexpected_files": [],
            "derived_fields_absent": [
                "repeat_rate",
                "nonprogress_rate",
                "error_rate",
            ],
            "excluded_artifact_classes": [
                "pair manifests",
                "aggregate result summaries",
                "rendered figures",
                "prior conclusions",
                "evaluation reports",
            ],
        },
        "status": "PASS",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--go", default="go", help="Go executable used for stock pprof")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = prepare_packages(args.source, args.output_root, args.report, args.go)
    print(
        json.dumps(
            {
                "status": report["status"],
                "tuple_count": report["tuple_equivalence"]["jsonl_tuple_count"],
                "report": str(args.report),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
