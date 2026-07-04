#!/usr/bin/env python3
"""R321: verify query-time operation predicates over existing labeled traces.

This is an implementation/reproducibility probe, not a new dataset.  It reuses
the tracked R300 operation JSONL, writes profile specs with `where_rules`, runs
the Rust profiler, and checks that mapping-derived predicates select the
expected operation subset before recursive stack folding.
"""

from __future__ import annotations

import csv
import html
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
SOURCE_OPERATIONS = OUT_ROOT / "operation-query-utility-r300" / "query-utility-operations.jsonl"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-where-filter-r321"

PROBES = [
    {
        "name": "looping_dynamic_task",
        "op_maps": ["task_family:where_probe_loop=(analysis_task=agentreward_looping)"],
        "where_rules": ["task_family=where_probe_loop"],
        "stack": "task_family,dataset,query_family,environment,phase,action,repeat_signal,status",
    },
    {
        "name": "looping_dynamic_task_without_success",
        "op_maps": ["task_family:where_probe_loop=(analysis_task=agentreward_looping)"],
        "where_rules": ["task_family=where_probe_loop", "status!=success"],
        "stack": "task_family,dataset,query_family,environment,phase,action,repeat_signal,status",
    },
    {
        "name": "safety_dynamic_task",
        "op_maps": ["task_family:where_probe_safety=(analysis_task=satraj_unsafe)"],
        "where_rules": ["task_family=where_probe_safety"],
        "stack": "task_family,dataset,environment,attack_type,safety,phase,action,status",
    },
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SystemExit(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def git_check(description: str, args: list[str], path: Path) -> None:
    result = subprocess.run(
        ["git", *args, "--", rel(path)],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        suffix = f": {detail}" if detail else ""
        raise SystemExit(f"{rel(path)} failed source check: {description}{suffix}")


def ensure_source_tracked_clean(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"missing source artifact {rel(path)}")
    git_check("source artifact is not git-tracked", ["ls-files", "--error-unmatch"], path)
    git_check("source artifact has unstaged changes", ["diff", "--quiet"], path)
    git_check("source artifact has staged changes", ["diff", "--cached", "--quiet"], path)


def load_operations(path: Path) -> list[dict[str, Any]]:
    operations = []
    with path.open(encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            fields = dict(record.get("fields") or {})
            fields.update({k: v for k, v in record.items() if k not in {"fields", "value"}})
            operations.append({"fields": fields, "value": int(record.get("value", 1) or 1)})
    return operations


def parse_op_map(raw: str) -> tuple[str, str, re.Pattern[str]]:
    left, pattern = raw.split("=", 1)
    field, label = left.split(":", 1)
    return field, label, re.compile(pattern)


def parse_where(raw: str) -> tuple[str, re.Pattern[str], bool]:
    if "!=" in raw:
        field, pattern = raw.split("!=", 1)
        return field, re.compile(pattern), True
    field, pattern = raw.split("=", 1)
    return field, re.compile(pattern), False


def searchable_text(fields: dict[str, Any]) -> str:
    chunks = []
    for key in sorted(fields):
        value = fields[key]
        values = value if isinstance(value, list) else [value]
        chunks.extend(f"{key}={item}" for item in values if item is not None)
    return " ".join(str(chunk) for chunk in chunks)


def apply_op_maps(fields: dict[str, Any], raw_rules: list[str]) -> dict[str, Any]:
    mapped = dict(fields)
    claimed = set()
    for raw_rule in raw_rules:
        field, label, pattern = parse_op_map(raw_rule)
        if field in claimed:
            continue
        if pattern.search(searchable_text(mapped)):
            mapped[field] = label
            claimed.add(field)
    return mapped


def matches_where(fields: dict[str, Any], raw_rules: list[str]) -> bool:
    for raw_rule in raw_rules:
        field, pattern, negated = parse_where(raw_rule)
        value = fields.get(field)
        values = value if isinstance(value, list) else ([] if value is None else [value])
        matched = any(
            pattern.search(str(item)) or pattern.search(f"{field}={item}") for item in values
        )
        if negated:
            matched = not matched
        if not matched:
            return False
    return True


def assert_mapped_labels_are_sentinels(operations: list[dict[str, Any]], probes: list[dict[str, Any]]) -> None:
    existing_values = {
        str(value)
        for op in operations
        for value in op["fields"].values()
        if not isinstance(value, list)
    }
    existing_values.update(
        str(item)
        for op in operations
        for value in op["fields"].values()
        if isinstance(value, list)
        for item in value
    )
    for probe in probes:
        for raw_rule in probe["op_maps"]:
            _, label, _ = parse_op_map(raw_rule)
            if label in existing_values:
                raise SystemExit(
                    f"mapped label {label!r} already exists in source operations; "
                    "R321 needs sentinel labels to prove predicates see mapped fields"
                )


def expected_count(operations: list[dict[str, Any]], probe: dict[str, Any]) -> int:
    total = 0
    for op in operations:
        fields = apply_op_maps(op["fields"], probe["op_maps"])
        if matches_where(fields, probe["where_rules"]):
            total += op["value"]
    return total


def run_agentpprof(spec_path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "cargo",
            "run",
            "--quiet",
            "--manifest-path",
            "agentpprof/Cargo.toml",
            "--",
            "--profile-spec",
            rel(spec_path),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"agentpprof failed for {rel(spec_path)}:\n{result.stderr.strip()}"
        )
    return json.loads(result.stdout)


def read_folded(path: Path) -> tuple[int, int]:
    total = 0
    stacks = 0
    with path.open(encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            stacks += 1
            total += int(line.rsplit(" ", 1)[1])
    return total, stacks


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(out_dir: Path, rows: list[dict[str, Any]], elapsed_s: float) -> None:
    report = {
        "run_id": "R321",
        "status": "pass" if all(row["count_matches_expected"] for row in rows) else "fail",
        "source_operations": rel(SOURCE_OPERATIONS),
        "commit": git_output(["rev-parse", "HEAD"]),
        "elapsed_s": round(elapsed_s, 3),
        "probes": rows,
        "claim": (
            "Rust agentpprof can apply query-time operation predicates after "
            "mapping/tagging and before recursive operation-stack folding."
        ),
        "non_claims": [
            "This does not add a new profiler abstraction beyond operation and operation stack.",
            "This does not use hidden oracle labels to rank groups.",
            "This does not download or create a new test dataset.",
        ],
    }
    write_json(out_dir / "where-filter-report.json", report)
    write_json(out_dir / "run-result.json", {"status": report["status"], "report": rel(out_dir / "where-filter-report.json")})

    with (out_dir / "where-filter-summary.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "probe",
                "expected_samples",
                "actual_samples",
                "unique_stacks",
                "where_rules",
                "count_matches_expected",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "probe": row["probe"],
                    "expected_samples": row["expected_samples"],
                    "actual_samples": row["actual_samples"],
                    "unique_stacks": row["unique_stacks"],
                    "where_rules": " && ".join(row["where_rules"]),
                    "count_matches_expected": row["count_matches_expected"],
                }
            )

    lines = [
        "# R321 Operation Predicate Reproducibility",
        "",
        f"Status: `{report['status']}`.",
        "",
        "R321 verifies that `--where`/`where_rules` acts as a query predicate over",
        "operations after mapping/tagging and before recursive stack folding.",
        "",
        "| Probe | Predicate | Expected samples | Folded samples | Unique stacks |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {probe} | `{where}` | {expected} | {actual} | {stacks} |".format(
                probe=row["probe"],
                where=" && ".join(row["where_rules"]),
                expected=row["expected_samples"],
                actual=row["actual_samples"],
                stacks=row["unique_stacks"],
            )
        )
    lines.extend(
        [
            "",
            "Interpretation: profile specs now carry the full operation-stack query:",
            "operation source, field mappings, query predicate, stack projection, and output.",
            "This makes the implementation closer to the paper's model where views are",
            "query evaluations over operations, not fixed prompt/session trees.",
        ]
    )
    (out_dir / "where-filter-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    html_rows = "\n".join(
        "<tr><td>{}</td><td><code>{}</code></td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            html.escape(row["probe"]),
            html.escape(" && ".join(row["where_rules"])),
            row["expected_samples"],
            row["actual_samples"],
            row["unique_stacks"],
        )
        for row in rows
    )
    (out_dir / "index.html").write_text(
        f"""<!doctype html>
<meta charset="utf-8">
<title>R321 Operation Predicate Reproducibility</title>
<style>body{{font-family:system-ui,sans-serif;max-width:980px;margin:32px auto;line-height:1.45}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:6px 8px}}code{{background:#f5f5f5;padding:1px 3px}}</style>
<h1>R321 Operation Predicate Reproducibility</h1>
<p>Status: <strong>{html.escape(report["status"])}</strong></p>
<table>
<thead><tr><th>Probe</th><th>Predicate</th><th>Expected samples</th><th>Folded samples</th><th>Unique stacks</th></tr></thead>
<tbody>{html_rows}</tbody>
</table>
""",
        encoding="utf-8",
    )


def main() -> None:
    start = time.time()
    ensure_source_tracked_clean(SOURCE_OPERATIONS)
    out_dir = DEFAULT_OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    operations = load_operations(SOURCE_OPERATIONS)
    assert_mapped_labels_are_sentinels(operations, PROBES)
    rows = []
    for probe in PROBES:
        folded_path = out_dir / f"{probe['name']}.folded"
        spec_path = out_dir / f"{probe['name']}-profile-spec.json"
        result_path = out_dir / f"{probe['name']}-agentpprof-result.json"
        spec = {
            "format": "folded",
            "operation_files": [str(SOURCE_OPERATIONS.resolve())],
            "output": folded_path.name,
            "project_name": "external-agent-traces",
            "view": "operations",
            "stack": probe["stack"],
            "op_maps": probe["op_maps"],
            "where_rules": probe["where_rules"],
        }
        write_json(spec_path, spec)
        profiler_result = run_agentpprof(spec_path)
        write_json(result_path, profiler_result)
        actual_samples, unique_stacks = read_folded(folded_path)
        expected_samples = expected_count(operations, probe)
        rows.append(
            {
                "probe": probe["name"],
                "where_rules": probe["where_rules"],
                "op_maps": probe["op_maps"],
                "stack": probe["stack"],
                "profile_spec": rel(spec_path),
                "folded": rel(folded_path),
                "agentpprof_result": rel(result_path),
                "expected_samples": expected_samples,
                "actual_samples": actual_samples,
                "unique_stacks": unique_stacks,
                "count_matches_expected": expected_samples == actual_samples,
            }
        )
    write_report(out_dir, rows, time.time() - start)
    print(json.dumps({"status": "ok", "out_dir": rel(out_dir), "probes": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
