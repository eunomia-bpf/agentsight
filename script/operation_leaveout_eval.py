#!/usr/bin/env python3
"""Run leave-one-dataset-out operation-stack mapping evaluation.

Each dataset is held out as test data. Operation-field mappings are inferred
from all remaining datasets, then evaluated through the Rust `agentpprof`
operation-file path and the Python quality/stack-analysis helpers. The core
profiler abstraction remains unchanged: the script only prepares operation JSONL
inputs and compares operation-stack outputs.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation-file", action="append", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--stack",
        default="project,dataset,task,phase,op,tool,action,status",
    )
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--project-name", default="external-agent-traces")
    parser.add_argument("--agentpprof-manifest", default="agentpprof/Cargo.toml")
    parser.add_argument("--keep-splits", action="store_true")
    args = parser.parse_args()

    operations = load_operations(args.operation_file)
    by_dataset: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for operation in operations:
        by_dataset[first_value(operation["fields"], "dataset", "unknown")].append(operation)
    if len(by_dataset) < 2:
        raise SystemExit("leave-dataset-out evaluation requires at least two datasets")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for dataset in sorted(by_dataset):
        rows.append(run_leaveout(dataset, by_dataset, args))

    summary = build_summary(args, rows, operations)
    summary_path = args.out_dir / "leaveout-summary.json"
    html_path = args.out_dir / "leaveout-summary.html"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    html_path.write_text(render_html(summary), encoding="utf-8")
    print(json.dumps(summary["summary"], indent=2, sort_keys=True))
    return 0


def load_operations(paths: list[Path]) -> list[dict[str, Any]]:
    operations = []
    for path in paths:
        with path.open("r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, 1):
                if not line.strip():
                    continue
                payload = json.loads(line)
                fields = normalize_fields(payload.get("fields") or {})
                operations.append(
                    {
                        "payload": payload,
                        "fields": fields,
                        "raw": line.rstrip("\n"),
                        "source": str(path),
                        "line_number": line_number,
                        "value": int(payload.get("value") or 1),
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


def first_value(fields: dict[str, list[str]], field: str, default: str) -> str:
    values = fields.get(field) or []
    return values[0] if values else default


def run_leaveout(
    dataset: str,
    by_dataset: dict[str, list[dict[str, Any]]],
    args: argparse.Namespace,
) -> dict[str, Any]:
    dataset_dir = args.out_dir / dataset
    dataset_dir.mkdir(parents=True, exist_ok=True)
    train_ops = [
        operation
        for name, operations in by_dataset.items()
        if name != dataset
        for operation in operations
    ]
    test_ops = by_dataset[dataset]
    train_path = dataset_dir / "train.operations.jsonl"
    test_path = dataset_dir / "test.operations.jsonl"
    write_operations(train_path, train_ops)
    write_operations(test_path, test_ops)

    op_map_txt = dataset_dir / "train-op-map.txt"
    op_map_json = dataset_dir / "train-op-map.json"
    run(
        [
            sys.executable,
            "script/operation_map_infer.py",
            "--operation-file",
            str(train_path),
            "--out",
            str(op_map_txt),
            "--json-out",
            str(op_map_json),
        ]
    )

    mapped_folded = dataset_dir / "mapped.folded"
    nomap_folded = dataset_dir / "nomap.folded"
    mapped_result = dataset_dir / "agentpprof-result.json"
    nomap_result = dataset_dir / "agentpprof-nomap-result.json"
    run_agentpprof(args, test_path, mapped_folded, mapped_result, ["--op-map-file", str(op_map_txt)])
    run_agentpprof(args, test_path, nomap_folded, nomap_result, [])

    mapped_quality = dataset_dir / "quality.json"
    nomap_quality = dataset_dir / "quality-nomap.json"
    run_quality(args, test_path, mapped_quality, ["--op-map-file", str(op_map_txt)])
    run_quality(args, test_path, nomap_quality, [])

    run_stack_analysis(mapped_folded, dataset_dir / "stack-analysis.json")
    run_stack_analysis(nomap_folded, dataset_dir / "stack-analysis-nomap.json")

    if not args.keep_splits:
        train_path.unlink(missing_ok=True)
        test_path.unlink(missing_ok=True)

    row = summarize_leaveout(
        dataset=dataset,
        train_ops=train_ops,
        test_ops=test_ops,
        op_map_json=op_map_json,
        mapped_result=mapped_result,
        nomap_result=nomap_result,
        mapped_quality=mapped_quality,
        nomap_quality=nomap_quality,
        dataset_dir=dataset_dir,
    )
    (dataset_dir / "summary.json").write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")
    return row


def write_operations(path: Path, operations: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for operation in operations:
            f.write(operation["raw"])
            f.write("\n")


def run_agentpprof(
    args: argparse.Namespace,
    operation_file: Path,
    output: Path,
    result_path: Path,
    extra_args: list[str],
) -> None:
    cmd = [
        "cargo",
        "run",
        "--quiet",
        "--manifest-path",
        args.agentpprof_manifest,
        "--",
        "--project-root",
        args.project_root,
        "--project-name",
        args.project_name,
        "--operation-file",
        str(operation_file),
        "--view",
        "operations",
        "--format",
        "folded",
        "-o",
        str(output),
        "--stack",
        args.stack,
        *extra_args,
    ]
    with result_path.open("w", encoding="utf-8") as f:
        run(cmd, stdout=f)


def run_quality(
    args: argparse.Namespace,
    operation_file: Path,
    output: Path,
    extra_args: list[str],
) -> None:
    run(
        [
            sys.executable,
            "script/operation_stack_quality.py",
            "--operation-file",
            str(operation_file),
            *extra_args,
            "--stack",
            args.stack,
            "--coverage-field",
            "task",
            "--coverage-field",
            "phase",
            "--oracle-pair",
            "phase:action",
            "--oracle-pair",
            "task:dataset",
            "--oracle-pair",
            "tool:dataset",
            "--boundary-pair",
            "phase:action",
            "--json-out",
            str(output),
        ]
    )


def run_stack_analysis(folded: Path, output: Path) -> None:
    run(
        [
            sys.executable,
            "script/operation_stack_analysis.py",
            "--folded",
            str(folded),
            "--json-out",
            str(output),
        ]
    )


def run(
    cmd: list[str],
    stdout: Any | None = None,
) -> None:
    subprocess.run(cmd, check=True, stdout=stdout)


def summarize_leaveout(
    dataset: str,
    train_ops: list[dict[str, Any]],
    test_ops: list[dict[str, Any]],
    op_map_json: Path,
    mapped_result: Path,
    nomap_result: Path,
    mapped_quality: Path,
    nomap_quality: Path,
    dataset_dir: Path,
) -> dict[str, Any]:
    op_map = read_json(op_map_json)
    mapped = read_json(mapped_result)
    nomap = read_json(nomap_result)
    mapped_q = read_json(mapped_quality)
    nomap_q = read_json(nomap_quality)
    mapped_summary = mapped_q["summary"]
    nomap_summary = nomap_q["summary"]
    row = {
        "dataset": dataset,
        "result_dir": str(dataset_dir),
        "train_operations": len(train_ops),
        "test_operations": len(test_ops),
        "train_weight": sum(operation["value"] for operation in train_ops),
        "test_weight": sum(operation["value"] for operation in test_ops),
        "rules": op_map["summary"]["rules"],
        "mapped_unique_stacks": mapped["unique_stacks"],
        "nomap_unique_stacks": nomap["unique_stacks"],
        "mapped_compression": mapped_summary["compression_ratio"],
        "nomap_compression": nomap_summary["compression_ratio"],
        "stack_reduction": nomap["unique_stacks"] - mapped["unique_stacks"],
        "compression_delta": round(
            mapped_summary["compression_ratio"] - nomap_summary["compression_ratio"], 3
        ),
        "mapped_phase_action_v": alignment_v(mapped_q, "phase", "action"),
        "nomap_phase_action_v": alignment_v(nomap_q, "phase", "action"),
        "mapped_task_dataset_v": alignment_v(mapped_q, "task", "dataset"),
        "nomap_task_dataset_v": alignment_v(nomap_q, "task", "dataset"),
        "mapped_boundary_f1": boundary_f1(mapped_q, "phase", "action"),
        "nomap_boundary_f1": boundary_f1(nomap_q, "phase", "action"),
        "top_test_actions": top_field(test_ops, "action", 8),
        "top_test_tasks": top_field(test_ops, "task", 8),
        "top_test_tools": top_field(test_ops, "tool", 8),
    }
    return row


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def alignment_v(report: dict[str, Any], predicted: str, oracle: str) -> float:
    for item in report["oracle_alignment"]:
        if item["predicted"] == predicted and item["oracle"] == oracle:
            return item["v_measure"]
    return 0.0


def boundary_f1(report: dict[str, Any], predicted: str, oracle: str) -> float:
    for item in report["boundary_alignment"]:
        if item["predicted"] == predicted and item["oracle"] == oracle:
            return item["f1"]
    return 0.0


def top_field(operations: list[dict[str, Any]], field: str, top: int) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    for operation in operations:
        for value in operation["fields"].get(field, []):
            counts[value] += operation["value"]
    return [{"value": value, "weight": weight} for value, weight in counts.most_common(top)]


def build_summary(
    args: argparse.Namespace,
    rows: list[dict[str, Any]],
    operations: list[dict[str, Any]],
) -> dict[str, Any]:
    positive = [row for row in rows if row["stack_reduction"] > 0]
    negative = [row for row in rows if row["stack_reduction"] < 0]
    total_test = sum(row["test_operations"] for row in rows)
    weighted_reduction = sum(row["stack_reduction"] * row["test_operations"] for row in rows)
    return {
        "summary": {
            "datasets": len(rows),
            "operations": len(operations),
            "total_test_operations": total_test,
            "positive_stack_reduction_datasets": len(positive),
            "negative_stack_reduction_datasets": len(negative),
            "weighted_stack_reduction_per_1k_ops": round(
                weighted_reduction / total_test * 1000, 3
            )
            if total_test
            else 0.0,
            "mean_mapped_task_dataset_v": round(
                sum(row["mapped_task_dataset_v"] for row in rows) / len(rows), 4
            ),
            "mean_nomap_task_dataset_v": round(
                sum(row["nomap_task_dataset_v"] for row in rows) / len(rows), 4
            ),
        },
        "operation_files": [str(path) for path in args.operation_file],
        "stack": args.stack,
        "rows": rows,
    }


def render_html(summary: dict[str, Any]) -> str:
    keys = [
        "dataset",
        "test_operations",
        "rules",
        "mapped_unique_stacks",
        "nomap_unique_stacks",
        "stack_reduction",
        "mapped_compression",
        "nomap_compression",
        "mapped_task_dataset_v",
        "nomap_task_dataset_v",
        "mapped_boundary_f1",
        "nomap_boundary_f1",
    ]
    parts = [
        "<!doctype html><meta charset='utf-8'><title>Leave-Dataset-Out Operation Mapping</title>",
        "<style>body{font-family:system-ui,sans-serif;margin:32px;max-width:1280px}"
        "table{border-collapse:collapse;width:100%;margin:16px 0}"
        "td,th{border:1px solid #ddd;padding:6px;text-align:left}"
        "th{background:#f6f6f6}code{white-space:pre-wrap}</style>",
        "<h1>Leave-Dataset-Out Operation Mapping</h1>",
        f"<p><code>{html.escape(json.dumps(summary['summary'], sort_keys=True))}</code></p>",
        "<table><tr>",
    ]
    parts.extend(f"<th>{html.escape(key)}</th>" for key in keys)
    parts.append("</tr>")
    for row in summary["rows"]:
        parts.append("<tr>")
        for key in keys:
            parts.append(f"<td>{html.escape(str(row.get(key, '')))}</td>")
        parts.append("</tr>")
    parts.append("</table>")
    return "\n".join(parts)


if __name__ == "__main__":
    sys.exit(main())
