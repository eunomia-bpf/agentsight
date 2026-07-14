#!/usr/bin/env python3
"""Evaluate existing task/action tag backends against isolated native labels."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
UNMATCHED = "unmatched"
CELL_SPECS = {
    "task-mind2web": ("mind2web", "task", "task_preview", "task"),
    "task-scienceworld": ("webshop-expert", "task", "task_preview", "task"),
    "action-android-control": ("android-control", "action", "step_preview", "action"),
    "action-gui-odyssey": ("gui-odyssey", "action", "action_raw", "action"),
}
EXPECTED = {
    "preflight": {"mind2web", "gui-odyssey"},
    "full": {spec[0] for spec in CELL_SPECS.values()},
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=sorted(EXPECTED), required=True)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--agentpprof-manifest", type=Path, required=True)
    args = parser.parse_args()

    by_dataset, input_files = load_inputs(args.input_root)
    missing = EXPECTED[args.mode] - set(by_dataset)
    if missing:
        raise SystemExit(f"missing required input datasets: {sorted(missing)}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    cluster_tagger = load_module(
        "agentpprof_cluster_tagger", ROOT / "agentpprof/backend/python/cluster_tagger.py"
    )
    dataset_adapter = load_module("agent_trace_datasets", ROOT / "script/agent_trace_datasets.py")

    cell_results = []
    union_operations = []
    for cell, (dataset, axis, text_field, reference_field) in CELL_SPECS.items():
        if dataset not in by_dataset:
            continue
        result, profile_operations = run_cell(
            cell=cell,
            dataset=dataset,
            axis=axis,
            text_field=text_field,
            reference_field=reference_field,
            source_operations=by_dataset[dataset],
            out_dir=args.out_dir / cell,
            manifest=args.agentpprof_manifest,
            cluster_tagger=cluster_tagger,
            dataset_adapter=dataset_adapter,
        )
        cell_results.append(result)
        union_operations.extend(profile_operations)

    union_dir = args.out_dir / "union"
    union_dir.mkdir(parents=True, exist_ok=True)
    union_path = union_dir / "profile.operations.jsonl"
    write_jsonl(union_path, union_operations)
    union_profile = run_profile(union_path, union_dir, args.agentpprof_manifest)

    summary = {
        "mode": args.mode,
        "input_root": str(args.input_root),
        "input_files": [str(path) for path in input_files],
        "cells": cell_results,
        "union": union_profile,
        "unavailable": {
            "phase": "no independent native phase reference in the reused R285 sources",
            "action-mind2web": "action_reprs directly serializes the native operation suffix",
            "other-r285-cells": "adapter constants or same-parser reconstructions",
        },
    }
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load module {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_inputs(root: Path) -> tuple[dict[str, list[dict[str, Any]]], list[Path]]:
    files = sorted(root.glob("**/operations-*.jsonl"))
    if not files:
        raise SystemExit(f"no operation files under {root}")
    by_dataset: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in files:
        for payload in read_jsonl(path):
            dataset = first(payload.get("fields") or {}, "dataset")
            if dataset:
                by_dataset[dataset].append(payload)
    return dict(by_dataset), files


def run_cell(
    *,
    cell: str,
    dataset: str,
    axis: str,
    text_field: str,
    reference_field: str,
    source_operations: list[dict[str, Any]],
    out_dir: Path,
    manifest: Path,
    cluster_tagger: ModuleType,
    dataset_adapter: ModuleType,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = prepare_rows(dataset, text_field, reference_field, source_operations)
    if axis == "task":
        source_audit = {"status": "not-applicable", "reason": "task references are sidecar-only"}
        predictions, backend_error = task_predictions(rows, cluster_tagger)
    else:
        source_audit = audit_action_inputs(rows)
        (out_dir / "source-field-audit.json").write_text(
            json.dumps(source_audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        if source_audit["status"] == "unavailable":
            return (
                {
                    "cell": cell,
                    "dataset": dataset,
                    "axis": axis,
                    "status": "unavailable",
                    "operations": len(rows),
                    "operation_weight": sum(row["value"] for row in rows),
                    "reason": "visible text directly serializes the structured gold action",
                    "source_audit": source_audit,
                },
                [],
            )
        predictions, backend_error = action_predictions(rows, dataset_adapter)

    references = [
        {"id": row["id"], "reference": row["reference"], "value": row["value"]}
        for row in rows
    ]
    predictor_inputs = [
        {"id": row["id"], "session": row["session"], "text": row["text"]}
        for row in rows
    ]
    prediction_rows = [{"id": row["id"], "predicted": predictions[row["id"]]} for row in rows]
    write_jsonl(out_dir / "reference.sidecar.jsonl", references)
    write_jsonl(out_dir / "predictor-input.jsonl", predictor_inputs)
    write_jsonl(out_dir / "predictions.jsonl", prediction_rows)

    scored_operations = []
    profile_operations = []
    for row in rows:
        predicted = predictions[row["id"]]
        score_fields = {
            "dataset": dataset,
            "cell": cell,
            "session": row["session"],
            "turn": row["turn"],
            "predicted_tag": predicted,
            "constant_tag": "constant",
            "reference_tag": row["reference"],
        }
        scored_operations.append({"value": row["value"], "fields": score_fields})
        profile_operations.append(
            {
                "value": row["value"],
                "fields": {
                    "project": "external-agent-traces",
                    "dataset": dataset,
                    "cell": cell,
                    "session": row["session"],
                    "turn": row["turn"],
                    "tag": predicted,
                    "op": "tag",
                },
            }
        )

    scored_path = out_dir / "scored.operations.jsonl"
    profile_path = out_dir / "profile.operations.jsonl"
    write_jsonl(scored_path, scored_operations)
    write_jsonl(profile_path, profile_operations)
    score = run_scorer(scored_path, out_dir)
    profile = run_profile(profile_path, out_dir, manifest)

    total_weight = sum(row["value"] for row in rows)
    unmatched_weight = sum(
        row["value"] for row in rows if predictions[row["id"]] == UNMATCHED
    )
    result = {
        "cell": cell,
        "dataset": dataset,
        "axis": axis,
        "status": "completed",
        "operations": len(rows),
        "operation_weight": total_weight,
        "sessions": len({row["session"] for row in rows}),
        "reference_labels": len({row["reference"] for row in rows}),
        "predicted_labels": len(set(predictions.values())),
        "unmatched_weight": unmatched_weight,
        "coverage": round((total_weight - unmatched_weight) / total_weight, 6)
        if total_weight
        else 0.0,
        "backend_error": backend_error,
        "source_audit": source_audit,
        "v_measure": alignment(score, "predicted_tag")["v_measure"],
        "constant_v_measure": alignment(score, "constant_tag")["v_measure"],
        "score_file": str(out_dir / "score.json"),
        "profile": profile,
    }
    return result, profile_operations


def prepare_rows(
    dataset: str,
    text_field: str,
    reference_field: str,
    operations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for ordinal, operation in enumerate(operations):
        fields = operation.get("fields") or {}
        session = first(fields, "session") or f"row-{ordinal}"
        turn = first(fields, "turn") or str(ordinal)
        reference = first(fields, reference_field)
        if not reference:
            raise SystemExit(f"{dataset} operation {ordinal} lacks {reference_field}")
        text = first(fields, text_field)
        if dataset == "android-control" and not text:
            text = first(fields, "action_raw")
        rows.append(
            {
                "id": f"{dataset}:{session}:{turn}:{ordinal}",
                "session": session,
                "turn": turn,
                "reference": reference,
                "text": text,
                "value": int(operation.get("value") or 1),
            }
        )
    return rows


def task_predictions(
    rows: list[dict[str, Any]], cluster_tagger: ModuleType
) -> tuple[dict[str, str], str | None]:
    by_session: dict[str, str] = {}
    for row in rows:
        if row["text"]:
            previous = by_session.setdefault(row["session"], row["text"])
            if previous != row["text"]:
                raise SystemExit(f"task text changed inside session {row['session']}")
    prompts = list(by_session.values())
    tags: dict[str, str] = {}
    backend_error = None
    if len(prompts) >= 2:
        try:
            tags, _ = cluster_tagger.cluster_prompts(prompts)
        except ValueError as exc:
            backend_error = str(exc)
    predictions = {}
    for row in rows:
        prompt = by_session.get(row["session"], "")
        predictions[row["id"]] = tags.get(cluster_tagger.hash_prompt(prompt), UNMATCHED)
    return predictions, backend_error


def action_predictions(
    rows: list[dict[str, Any]], dataset_adapter: ModuleType
) -> tuple[dict[str, str], None]:
    predictions = {}
    for row in rows:
        predicted = dataset_adapter.action_verb(row["text"]) if row["text"] else "unknown"
        predictions[row["id"]] = (
            UNMATCHED if predicted in {"", "none", "unknown", UNMATCHED} else predicted
        )
    return predictions, None


def audit_action_inputs(rows: list[dict[str, Any]]) -> dict[str, Any]:
    direct_copies = []
    for row in rows:
        text = row["text"].strip()
        reference = row["reference"].strip()
        escaped = re.escape(reference)
        explicit_field = re.search(
            rf"(?i)(?:^|[{{,\s])['\"]?(?:action|action_type)['\"]?\s*[:=]\s*['\"]?{escaped}(?:['\"]|[,}}\s]|$)",
            text,
        )
        arrow_suffix = re.search(rf"(?i)->\s*{escaped}\s*$", text)
        uppercase_enum = text == reference.upper() and text != reference.lower()
        if explicit_field or arrow_suffix or uppercase_enum:
            direct_copies.append(
                {"id": row["id"], "reference": reference, "text": text[:180]}
            )
    return {
        "status": "unavailable" if direct_copies else "available",
        "rows": len(rows),
        "rows_with_text": sum(bool(row["text"].strip()) for row in rows),
        "structured_gold_copies": len(direct_copies),
        "examples": direct_copies[:5],
        "criterion": "explicit action/action_type field, arrow-suffixed gold label, or exact uppercase enum; ordinary natural-language action words remain visible evidence",
    }


def run_scorer(operation_file: Path, out_dir: Path) -> dict[str, Any]:
    score_path = out_dir / "score.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "script/operation_stack_quality.py"),
            "--operation-file",
            str(operation_file),
            "--stack",
            "dataset,cell,predicted_tag",
            "--oracle-pair",
            "predicted_tag:reference_tag",
            "--oracle-pair",
            "constant_tag:reference_tag",
            "--json-out",
            str(score_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return json.loads(score_path.read_text(encoding="utf-8"))


def run_profile(operation_file: Path, out_dir: Path, manifest: Path) -> dict[str, Any]:
    folded = out_dir / "profile.folded"
    completed = subprocess.run(
        [
            "cargo",
            "run",
            "--quiet",
            "--manifest-path",
            str(manifest),
            "--",
            "--project-root",
            ".",
            "--project-name",
            "external-agent-traces",
            "--operation-file",
            str(operation_file),
            "--view",
            "operations",
            "--format",
            "folded",
            "-o",
            str(folded),
            "--stack",
            "project,dataset,cell,tag,op",
        ],
        check=True,
        text=True,
        capture_output=True,
        cwd=ROOT,
    )
    result = json.loads(completed.stdout)
    (out_dir / "agentpprof-result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    operations = read_jsonl(operation_file)
    input_weight = sum(int(row.get("value") or 1) for row in operations)
    folded_weight = sum(
        int(line.rsplit(" ", 1)[1])
        for line in folded.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    return {
        "input_rows": len(operations),
        "input_weight": input_weight,
        "reported_operations": result["operations"],
        "reported_samples": result["samples"],
        "unique_stacks": result["unique_stacks"],
        "folded_weight": folded_weight,
        "rows_conserved": result["operations"] == len(operations),
        "weight_conserved": folded_weight == input_weight,
        "result_file": str(out_dir / "agentpprof-result.json"),
        "folded_file": str(folded),
    }


def alignment(score: dict[str, Any], predicted: str) -> dict[str, Any]:
    return next(
        row
        for row in score["oracle_alignment"]
        if row["predicted"] == predicted and row["oracle"] == "reference_tag"
    )


def first(fields: dict[str, Any], key: str) -> str:
    value = fields.get(key)
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value) if value is not None else ""


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
