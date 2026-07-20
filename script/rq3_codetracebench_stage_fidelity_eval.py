#!/usr/bin/env python3
"""Score unchanged Rust recurrence induction against CodeTraceBench stages.

Visible operation files are converted to the release constructor's minimal
``{session, action}`` input and predicted before this program reads the official
stage ranges.  The scorer then compares the resulting partitions with the
complete ground-truth stage intervals on the already-run CodeTraceBench target
population.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import random
import subprocess
from typing import Any, Iterable

import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_REFERENCE_SESSIONS = 2634
EXPECTED_REFERENCE_OPERATIONS = 108569
EXPECTED_TARGET_SESSIONS = 405
EXPECTED_TARGET_OPERATIONS = 20866
EXPECTED_DISJOINT_REFERENCE_SESSIONS = 2229
EXPECTED_DISJOINT_REFERENCE_OPERATIONS = 87703
EXPECTED_ACTION_KINDS = {
    "communicate",
    "edit",
    "execute",
    "inspect",
    "install",
    "other",
    "search",
    "test",
    "version-control",
}
METHODS = (
    "recurrence",
    "current_recurrence",
    "raw_action_key_change",
    "phase_change",
    "action_change",
    "always_boundary",
    "session_one_block",
)
ALTERNATIVES = METHODS[1:]
DEFAULT_CURRENT_SUMMARY = (
    ROOT
    / ".agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/full/summary.json"
)
DEFAULT_CURRENT_ASSIGNMENTS = (
    ROOT
    / ".agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/full/operation-assignments.jsonl"
)
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20260719


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("preflight", "full"))
    parser.add_argument("--agentpprof-bin", type=Path, required=True)
    parser.add_argument("--reference-operations", type=Path, required=True)
    parser.add_argument("--target-operations", type=Path, required=True)
    parser.add_argument("--verified-manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def absolute(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, sort_keys=True) + "\n")


def load_visible_operations(path: Path) -> dict[str, list[dict[str, Any]]]:
    """Load only existing operation fields; no manifest or stage is available."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            record = json.loads(line)
            fields = record.get("fields")
            require(isinstance(fields, dict), f"{path}:{line_number}: missing fields")
            require(record.get("value") == 1, f"{path}:{line_number}: non-unit value")
            for field in (
                "traj_id",
                "step_id",
                "action_kind",
                "raw_action_key",
                "phase",
            ):
                require(fields.get(field) not in (None, ""), f"{path}:{line_number}: {field}")
            step_id = int(fields["step_id"])
            require(step_id > 0, f"{path}:{line_number}: non-positive step_id")
            grouped[str(fields["traj_id"])].append(
                {
                    "session": str(fields["traj_id"]),
                    "step_id": step_id,
                    "action": str(fields["action_kind"]),
                    "action_detail": str(fields["raw_action_key"]),
                    "phase": str(fields["phase"]),
                }
            )
    for session, rows in grouped.items():
        rows.sort(key=lambda row: int(row["step_id"]))
        require(
            [int(row["step_id"]) for row in rows] == list(range(1, len(rows) + 1)),
            f"{path}: {session}: steps are not consecutive one-based IDs",
        )
    return dict(grouped)


def minimal_rows(
    grouped: dict[str, list[dict[str, Any]]], sessions: Iterable[str]
) -> list[dict[str, Any]]:
    output = []
    for session in sorted(sessions):
        for row in grouped[session]:
            output.append(
                {
                    "fields": {
                        "action": row["action"],
                        "action_detail": row["action_detail"],
                        "session": session,
                    },
                    "value": 1,
                }
            )
    return output


def run_recurrence(
    binary: Path,
    out_dir: Path,
    reference_rows: list[dict[str, Any]],
    target_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    reference_file = out_dir / "reference-input.jsonl"
    target_file = out_dir / "target-input.jsonl"
    profile_file = out_dir / "profile.json"
    write_jsonl(reference_file, reference_rows)
    write_jsonl(target_file, target_rows)
    command = [
        str(binary.resolve()),
        "--operation-file",
        str(target_file.resolve()),
        "--view",
        "operations",
        "--format",
        "json",
        "--output",
        str(profile_file.resolve()),
        "--induce-operation-stack",
        "--induce-reference-operation-file",
        str(reference_file.resolve()),
        "--deterministic-output",
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    write_json(out_dir / "command.json", command)
    (out_dir / "stdout.json").write_text(completed.stdout, encoding="utf-8")
    (out_dir / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
    require(completed.returncode == 0, f"agentpprof failed: {completed.returncode}")
    status = json.loads(completed.stdout)
    profile = json.loads(profile_file.read_text(encoding="utf-8"))
    require(status.get("status") == "ok", "agentpprof status is not ok")
    require(status.get("samples") == len(target_rows), "target sample count mismatch")
    require(
        profile["profile"]["summary"]["total_weight"] == len(target_rows),
        "target profile mass mismatch",
    )
    return status, profile


def recurrence_predictions(
    profile: dict[str, Any],
    targets: dict[str, list[dict[str, Any]]],
    selected: list[str],
) -> tuple[dict[tuple[str, int], bool], dict[tuple[str, int], str], dict[str, Any]]:
    report = profile["profile"]["operation_stack_induction"]
    require(
        report.get("policy")
        == "cross-session-action-transition-npmi-operation-stack-induction",
        "unexpected recurrence policy",
    )
    require(report.get("sequence_field") == "session", "unexpected sequence field")
    require(report.get("association_field") == "action", "unexpected action field")
    require(
        report.get("selected_source_fields") == ["action", "action_detail"],
        "unexpected recurrence source fields",
    )
    detail_report = report.get("detail_recurrence")
    require(isinstance(detail_report, dict), "missing detail recurrence report")
    require(
        detail_report.get("association_field") == "action_detail",
        "unexpected detail association field",
    )
    expected_pairs = sum(len(targets[session]) - 1 for session in selected)
    raw_decisions = report.get("boundary_decisions") or []
    require(len(raw_decisions) == expected_pairs, "recurrence decision coverage mismatch")
    decisions: dict[tuple[str, int], bool] = {}
    for row in raw_decisions:
        key = (str(row["session"]), int(row["position"]))
        require(key not in decisions, f"duplicate recurrence decision: {key}")
        require(
            not bool(row["boundary"]) or bool(row["coarse_boundary"]),
            f"detail recurrence added a coarse-relative boundary: {key}",
        )
        decisions[key] = bool(row["boundary"])
    expected_keys = {
        (session, position)
        for session in selected
        for position in range(1, len(targets[session]))
    }
    require(set(decisions) == expected_keys, "recurrence decision keys mismatch")

    motifs: dict[tuple[str, int], str] = {}
    by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for segment in report.get("segments") or []:
        by_session[str(segment["session"])].append(segment)
    require(set(by_session) == set(selected), "recurrence segment session mismatch")
    for session in selected:
        segments = sorted(by_session[session], key=lambda row: int(row["start"]))
        cursor = 0
        for segment in segments:
            start = int(segment["start"])
            end = int(segment["end"])
            require(start == cursor and end > start, f"{session}: segment gap/overlap")
            for position in range(start, end):
                motifs[(session, position + 1)] = str(segment["motif"])
            cursor = end
        require(cursor == len(targets[session]), f"{session}: segment coverage mismatch")
    return decisions, motifs, report


def load_stages_after_prediction(
    manifest_path: Path,
    targets: dict[str, list[dict[str, Any]]],
    selected: list[str],
) -> tuple[dict[tuple[str, int], str], dict[str, str], dict[str, str]]:
    """The only function allowed to read scorer-only official stages."""
    table = pq.read_table(
        manifest_path,
        columns=["traj_id", "agent", "task_name", "solved", "step_count", "stages"],
    )
    wanted = set(selected)
    stage_by_step: dict[tuple[str, int], str] = {}
    framework_by_session: dict[str, str] = {}
    task_by_session: dict[str, str] = {}
    seen: set[str] = set()
    for row in table.to_pylist():
        session = str(row["traj_id"])
        if session not in wanted:
            continue
        require(session not in seen, f"duplicate manifest target: {session}")
        seen.add(session)
        require(row["solved"] is False, f"selected target is not failed: {session}")
        require(int(row["step_count"]) == len(targets[session]), f"{session}: step count")
        cursor = 1
        for stage in row["stages"] or []:
            start = int(stage["start_step_id"])
            end = int(stage["end_step_id"])
            require(start == cursor and end >= start, f"{session}: stage gap/overlap")
            stage_id = f"{session}:stage-{int(stage['stage_id']):04d}"
            for step_id in range(start, end + 1):
                key = (session, step_id)
                require(key not in stage_by_step, f"duplicate official stage step: {key}")
                stage_by_step[key] = stage_id
            cursor = end + 1
        require(cursor == len(targets[session]) + 1, f"{session}: incomplete stages")
        framework_by_session[session] = str(row["agent"])
        task_by_session[session] = str(row["task_name"])
    require(seen == wanted, "verified manifest target coverage mismatch")
    return stage_by_step, framework_by_session, task_by_session


def score_rows(
    targets: dict[str, list[dict[str, Any]]],
    selected: list[str],
    recurrence: dict[tuple[str, int], bool],
    motifs: dict[tuple[str, int], str],
    official: dict[tuple[str, int], str],
    frameworks: dict[str, str],
    tasks: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pairs = []
    operations = []
    for session in selected:
        rows = targets[session]
        group_numbers = {
            method: 0
            for method in METHODS
            if method not in {"current_recurrence"}
        }
        for index, row in enumerate(rows):
            step_id = int(row["step_id"])
            key = (session, step_id)
            if index:
                previous = rows[index - 1]
                pair_key = (session, index)
                values = {
                    "recurrence": recurrence[pair_key],
                    "phase_change": previous["phase"] != row["phase"],
                    "action_change": previous["action"] != row["action"],
                    "raw_action_key_change": previous["action_detail"]
                    != row["action_detail"],
                    "always_boundary": True,
                    "session_one_block": False,
                }
                label = official[(session, step_id - 1)] != official[key]
                pair = {
                    "session": session,
                    "framework": frameworks[session],
                    "position": index,
                    "left_step_id": step_id - 1,
                    "right_step_id": step_id,
                    "left_action": previous["action"],
                    "right_action": row["action"],
                    "left_phase": previous["phase"],
                    "right_phase": row["phase"],
                    "official_boundary": label,
                    **values,
                }
                pairs.append(pair)
                for method, boundary in values.items():
                    if boundary:
                        group_numbers[method] += 1
            operation = {
                "session": session,
                "framework": frameworks[session],
                "task_name": tasks[session],
                "step_id": step_id,
                "action": row["action"],
                "action_detail": row["action_detail"],
                "phase": row["phase"],
                "official_stage": official[key],
                "recurrence_motif": motifs[key],
            }
            for method in group_numbers:
                operation[method] = f"{session}:{method}-{group_numbers[method]:04d}"
            operations.append(operation)
    return pairs, operations


def boundary_metrics(rows: list[dict[str, Any]], method: str) -> dict[str, Any]:
    tp = sum(bool(row[method]) and bool(row["official_boundary"]) for row in rows)
    fp = sum(bool(row[method]) and not bool(row["official_boundary"]) for row in rows)
    fn = sum(not bool(row[method]) and bool(row["official_boundary"]) for row in rows)
    tn = sum(not bool(row[method]) and not bool(row["official_boundary"]) for row in rows)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
    return {
        "pairs": len(rows),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def bcubed(rows: list[dict[str, Any]], method: str) -> dict[str, Any]:
    predicted_totals: Counter[str] = Counter(str(row[method]) for row in rows)
    official_totals: Counter[str] = Counter(str(row["official_stage"]) for row in rows)
    overlap: Counter[tuple[str, str]] = Counter(
        (str(row[method]), str(row["official_stage"])) for row in rows
    )
    precision = sum(
        overlap[(str(row[method]), str(row["official_stage"]))]
        / predicted_totals[str(row[method])]
        for row in rows
    ) / len(rows)
    recall = sum(
        overlap[(str(row[method]), str(row["official_stage"]))]
        / official_totals[str(row["official_stage"])]
        for row in rows
    ) / len(rows)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "operations": len(rows),
        "predicted_groups": len(predicted_totals),
        "official_groups": len(official_totals),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def attach_current_recurrence(
    pair_rows: list[dict[str, Any]],
    operation_rows: list[dict[str, Any]],
    path: Path,
) -> None:
    current: dict[tuple[str, int], str] = {}
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            row = json.loads(line)
            key = (str(row["session"]), int(row["step_id"]))
            require(key not in current, f"duplicate current assignment at line {line_number}")
            current[key] = str(row["recurrence"])

    expected = {(str(row["session"]), int(row["step_id"])) for row in operation_rows}
    require(expected <= set(current), "current recurrence baseline lacks selected operations")
    for row in operation_rows:
        key = (str(row["session"]), int(row["step_id"]))
        row["current_recurrence"] = current[key]
    for row in pair_rows:
        session = str(row["session"])
        left = current[(session, int(row["left_step_id"]))]
        right = current[(session, int(row["right_step_id"]))]
        row["current_recurrence"] = left != right


def percentile(values: list[float], probability: float) -> float:
    require(bool(values), "percentile requires values")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def task_cluster_bootstrap(
    rows: list[dict[str, Any]], out_dir: Path
) -> dict[str, Any]:
    rows_by_session: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_session[str(row["session"])].append(row)

    task_sessions: dict[str, list[str]] = defaultdict(list)
    sufficient: dict[tuple[str, str], tuple[float, float, int]] = {}
    for session, session_rows in rows_by_session.items():
        tasks = {str(row["task_name"]) for row in session_rows}
        require(len(tasks) == 1, f"session has multiple task names: {session}")
        task = next(iter(tasks))
        task_sessions[task].append(session)
        for method in ("recurrence", "current_recurrence"):
            metric = bcubed(session_rows, method)
            count = len(session_rows)
            sufficient[(session, method)] = (
                metric["precision"] * count,
                metric["recall"] * count,
                count,
            )

    tasks = sorted(task_sessions)
    require(len(tasks) == 251, f"expected 251 task clusters, got {len(tasks)}")

    def f1_for(draw: list[str], method: str) -> float:
        precision_sum = 0.0
        recall_sum = 0.0
        operations = 0
        for task in draw:
            for session in task_sessions[task]:
                precision, recall, count = sufficient[(session, method)]
                precision_sum += precision
                recall_sum += recall
                operations += count
        precision = precision_sum / operations
        recall = recall_sum / operations
        return (
            2.0 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )

    generator = random.Random(BOOTSTRAP_SEED)
    deltas = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        draw = generator.choices(tasks, k=len(tasks))
        deltas.append(f1_for(draw, "recurrence") - f1_for(draw, "current_recurrence"))
    write_jsonl(
        out_dir / "task-bootstrap-deltas.jsonl",
        [{"resample": index, "delta": delta} for index, delta in enumerate(deltas)],
    )
    return {
        "unit": "task_name",
        "clusters": len(tasks),
        "resamples": BOOTSTRAP_RESAMPLES,
        "seed": BOOTSTRAP_SEED,
        "mean_delta": sum(deltas) / len(deltas),
        "median_delta": percentile(deltas, 0.5),
        "ci95": [percentile(deltas, 0.025), percentile(deltas, 0.975)],
        "positive_fraction": sum(delta > 0.0 for delta in deltas) / len(deltas),
        "raw_deltas": relative(out_dir / "task-bootstrap-deltas.jsonl"),
    }


def aggregate(
    pair_rows: list[dict[str, Any]], operation_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        method: {
            "boundary": boundary_metrics(pair_rows, method),
            "partition": bcubed(operation_rows, method),
        }
        for method in METHODS
    }


def population_relation(metrics: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    candidate_partition = float(metrics["recurrence"]["partition"]["f1"])
    current_partition = float(current["partition"]["f1"])
    relation = (
        "higher"
        if candidate_partition > current_partition
        else "equal"
        if candidate_partition == current_partition
        else "lower"
    )
    return {
        "population_relation": relation,
        "boundary_f1_delta_vs_current": metrics["recurrence"]["boundary"]["f1"]
        - current["boundary"]["f1"],
        "partition_f1_delta_vs_current": candidate_partition - current_partition,
        "overall_verdict": "requires the complete OSWorld-Human population",
    }


def markdown_report(summary: dict[str, Any]) -> str:
    preflight = summary["mode"] == "preflight"
    lines = [
        "# CodeTraceBench RQ3 Stage-Fidelity Result",
        "",
        f"**Mode:** {summary['mode']}",
        f"**Run status:** {summary['run_status']}",
        f"**Tested hypothesis:** {summary['tested_hypothesis']}",
        "",
        "## Preflight Population" if preflight else "## Complete Population",
        "",
        f"- Reference: {summary['population']['reference_sessions']} disjoint sessions / {summary['population']['reference_operations']} operations.",
        f"- Target: {summary['population']['target_sessions']} sessions / {summary['population']['target_operations']} operations / {summary['population']['target_pairs']} adjacent pairs.",
        f"- Official stages: {summary['population']['official_stages']} complete intervals.",
        "",
        "## Diagnostic Metrics (not a scientific result)"
        if preflight
        else "## Primary Results",
        "",
        "| Method | Boundary precision | Boundary recall | Boundary F1 | B-cubed F1 |",
        "|---|---:|---:|---:|---:|",
    ]
    for method in METHODS:
        row = summary["metrics"][method]
        lines.append(
            f"| {method} | {row['boundary']['precision']:.6f} | {row['boundary']['recall']:.6f} | {row['boundary']['f1']:.6f} | {row['partition']['f1']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            summary["interpretation"],
            "",
            "The official stage ranges were loaded only after the release Rust path wrote its predictions. The Rust inputs contain only unit weight, `session`, coarse `action`, and source-visible `action_detail`; target IDs are absent from the reference corpus.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    out_dir = absolute(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    binary = absolute(args.agentpprof_bin)
    reference_path = absolute(args.reference_operations)
    target_path = absolute(args.target_operations)
    manifest_path = absolute(args.verified_manifest)
    for path in (
        binary,
        reference_path,
        target_path,
        manifest_path,
        DEFAULT_CURRENT_SUMMARY,
        DEFAULT_CURRENT_ASSIGNMENTS,
    ):
        require(path.is_file(), f"missing input: {relative(path)}")

    version = subprocess.run(
        [str(binary.resolve()), "--version"],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    require(version.returncode == 0, "agentpprof --version failed")
    require(version.stdout.strip() == "agentpprof 0.2.37", "unexpected binary version")

    # Visible construction phase.  No manifest is read above or in these loaders.
    references = load_visible_operations(reference_path)
    targets = load_visible_operations(target_path)
    require(len(references) == EXPECTED_REFERENCE_SESSIONS, "reference sessions changed")
    require(
        sum(map(len, references.values())) == EXPECTED_REFERENCE_OPERATIONS,
        "reference operations changed",
    )
    require(len(targets) == EXPECTED_TARGET_SESSIONS, "target sessions changed")
    require(
        sum(map(len, targets.values())) == EXPECTED_TARGET_OPERATIONS,
        "target operations changed",
    )
    target_ids = set(targets)
    disjoint_reference_ids = sorted(set(references) - target_ids)
    require(not (set(disjoint_reference_ids) & target_ids), "reference/target overlap")
    require(
        len(disjoint_reference_ids) == EXPECTED_DISJOINT_REFERENCE_SESSIONS,
        "disjoint reference sessions changed",
    )
    require(
        sum(len(references[session]) for session in disjoint_reference_ids)
        == EXPECTED_DISJOINT_REFERENCE_OPERATIONS,
        "disjoint reference operations changed",
    )
    action_kinds = {
        row["action"]
        for session in disjoint_reference_ids
        for row in references[session]
    }
    require(action_kinds == EXPECTED_ACTION_KINDS, "reference action kinds changed")

    selected = sorted(targets)
    if args.mode == "preflight":
        selected = selected[:1]
    reference_rows = minimal_rows(references, disjoint_reference_ids)
    target_rows = minimal_rows(targets, selected)
    require(
        all(
            set(row) == {"fields", "value"}
            and set(row["fields"]) == {"session", "action", "action_detail"}
            and row["value"] == 1
            for row in reference_rows + target_rows
        ),
        "minimal recurrence input contract violated",
    )
    status, profile = run_recurrence(binary, out_dir, reference_rows, target_rows)
    recurrence, motifs, recurrence_report = recurrence_predictions(
        profile, targets, selected
    )

    # Scoring phase. Official stages become readable only after prediction.
    official, frameworks, tasks = load_stages_after_prediction(
        manifest_path, targets, selected
    )
    pair_rows, operation_rows = score_rows(
        targets, selected, recurrence, motifs, official, frameworks, tasks
    )
    attach_current_recurrence(
        pair_rows, operation_rows, DEFAULT_CURRENT_ASSIGNMENTS
    )
    metrics = aggregate(pair_rows, operation_rows)
    by_framework = {
        framework: aggregate(
            [row for row in pair_rows if row["framework"] == framework],
            [row for row in operation_rows if row["framework"] == framework],
        )
        for framework in sorted(set(frameworks.values()))
    }
    historical = None
    local_relation = None
    bootstrap = None
    if args.mode == "full":
        historical = json.loads(DEFAULT_CURRENT_SUMMARY.read_text(encoding="utf-8"))
        require(
            historical["population"]
            == {
                "reference_sessions": EXPECTED_DISJOINT_REFERENCE_SESSIONS,
                "reference_operations": EXPECTED_DISJOINT_REFERENCE_OPERATIONS,
                "target_sessions": EXPECTED_TARGET_SESSIONS,
                "target_operations": EXPECTED_TARGET_OPERATIONS,
                "target_pairs": EXPECTED_TARGET_OPERATIONS - EXPECTED_TARGET_SESSIONS,
                "official_stages": 2948,
                "frameworks": dict(Counter(frameworks.values())),
                "action_kinds": sorted(action_kinds),
            },
            "historical CodeTraceBench population changed",
        )
        for field in ("precision", "recall", "f1"):
            require(
                abs(
                    float(metrics["current_recurrence"]["partition"][field])
                    - float(historical["metrics"]["recurrence"]["partition"][field])
                )
                <= 1e-12,
                f"current recurrence baseline reproduction failed: {field}",
            )
        local_relation = population_relation(metrics, historical["metrics"]["recurrence"])
        bootstrap = task_cluster_bootstrap(operation_rows, out_dir)
    official_stage_count = len(set(official.values()))
    expected_target_operations = sum(len(targets[session]) for session in selected)
    expected_target_pairs = expected_target_operations - len(selected)
    require(len(operation_rows) == expected_target_operations, "scored operation coverage")
    require(len(pair_rows) == expected_target_pairs, "scored pair coverage")
    require(
        recurrence_report["reference_sessions"] == EXPECTED_DISJOINT_REFERENCE_SESSIONS
        and recurrence_report["reference_operations"]
        == EXPECTED_DISJOINT_REFERENCE_OPERATIONS,
        "Rust reference population mismatch",
    )
    require(
        recurrence_report["target_sessions"] == len(selected)
        and recurrence_report["target_operations"] == expected_target_operations,
        "Rust target population mismatch",
    )

    write_jsonl(out_dir / "pair-decisions.jsonl", pair_rows)
    write_jsonl(out_dir / "operation-assignments.jsonl", operation_rows)
    if local_relation is None:
        tested_hypothesis = "not tested"
        verdict = {
            "verdict": "not tested",
            "reason": "preflight establishes only real end-to-end executability",
        }
        interpretation = (
            "This one-session preflight establishes only that the approved real-data "
            "path executes end to end. It does not test the hypothesis; the displayed "
            "metrics are diagnostics only."
        )
    else:
        delta = float(local_relation["partition_f1_delta_vs_current"])
        ci95 = bootstrap["ci95"]
        if delta > 0.0 and float(ci95[0]) > 0.0:
            codetrace_verdict = "supported"
        elif delta > 0.0:
            codetrace_verdict = "promising_but_not_established"
        else:
            codetrace_verdict = "contradicted"
        tested_hypothesis = f"codetrace_{codetrace_verdict}"
        verdict = {
            **local_relation,
            "codetrace_verdict": codetrace_verdict,
            "experiment_verdict": "pending_osworld_fallback_and_independent_review",
            "task_cluster_bootstrap_ci95": ci95,
        }
        interpretation = (
            "The multi-resolution candidate is "
            f"{local_relation['population_relation']} than the current release recurrence "
            "on complete CodeTraceBench ordinary B-cubed F1. Its registered mechanism "
            f"verdict for this population is {codetrace_verdict}. The experiment verdict "
            "remains pending the Rust-level OSWorld fallback check, all validity checks, "
            "and independent result review."
        )
    summary = {
        "schema": "agentsight.rq3-codetracebench-stage-fidelity.v1",
        "mode": args.mode,
        "run_status": "valid",
        "tested_hypothesis": tested_hypothesis,
        "research_value": "supporting" if args.mode == "full" else "dependency-only",
        "paper_impact": (
            "implementation-selection evidence only"
            if args.mode == "full"
            else "none; preflight only"
        ),
        "next_paper_decision": (
            "route valid result to independent result review"
            if args.mode == "full"
            else "run the complete approved population without changing the plan"
        ),
        "interpretation": interpretation,
        "inputs": {
            "binary": relative(binary),
            "version": version.stdout.strip(),
            "reference_operations": relative(reference_path),
            "target_operations": relative(target_path),
            "verified_manifest": relative(manifest_path),
            "rust_reference_input": relative(out_dir / "reference-input.jsonl"),
            "rust_target_input": relative(out_dir / "target-input.jsonl"),
        },
        "population": {
            "reference_sessions": len(disjoint_reference_ids),
            "reference_operations": len(reference_rows),
            "target_sessions": len(selected),
            "target_operations": expected_target_operations,
            "target_pairs": expected_target_pairs,
            "official_stages": official_stage_count,
            "frameworks": dict(Counter(frameworks.values())),
            "action_kinds": sorted(action_kinds),
        },
        "metrics": metrics,
        "per_framework": by_framework,
        "verdict": verdict,
        "current_recurrence_baseline": (
            historical["metrics"]["recurrence"] if historical else None
        ),
        "task_cluster_bootstrap": bootstrap,
        "recurrence": {
            key: recurrence_report[key]
            for key in (
                "policy",
                "reference_sessions",
                "reference_operations",
                "reference_transitions",
                "target_sessions",
                "target_operations",
                "predicted_groups",
                "unique_motifs",
                "unseen_target_transitions",
                "same_action_reference_transitions",
                "action_change_reference_transitions",
                "global_low_center",
                "global_high_center",
                "global_cutoff",
                "cross_action_low_center",
                "cross_action_high_center",
                "cross_action_cutoff",
                "cross_action_applied_cutoff",
                "removed_current_boundaries",
                "added_current_boundaries",
                "selected_source_fields",
            )
        }
        | {"detail_recurrence": recurrence_report["detail_recurrence"]},
        "validity": {
            "full_population_scored": args.mode == "full"
            and (
                len(selected) == EXPECTED_TARGET_SESSIONS
                and expected_target_operations == EXPECTED_TARGET_OPERATIONS
            ),
            "reference_target_session_disjoint": True,
            "rust_inputs_only_unit_session_action_and_action_detail": True,
            "action_detail_is_preexisting_source_visible_raw_action_key": True,
            "phase_and_stages_excluded_from_rust": True,
            "official_stages_loaded_after_prediction": True,
            "official_stage_coverage_exact": len(official) == expected_target_operations,
            "every_pair_scored_once": len(pair_rows) == expected_target_pairs,
            "every_operation_assigned_once": len(operation_rows)
            == expected_target_operations,
            "all_target_weight_conserved": status["samples"]
            == expected_target_operations,
            "algorithm_or_threshold_search": False,
            "candidate_boundary_subset_of_coarse_release": recurrence_report[
                "detail_recurrence"
            ]["added_coarse_boundaries"]
            == 0,
            "current_release_baseline_reproduced": all(
                abs(
                    float(metrics["current_recurrence"]["partition"][field])
                    - float(
                        historical["metrics"]["recurrence"]["partition"][field]
                    )
                )
                <= 1e-12
                for field in ("precision", "recall", "f1")
            )
            if historical
            else True,
        },
        "raw": {
            "profile": relative(out_dir / "profile.json"),
            "pair_decisions": relative(out_dir / "pair-decisions.jsonl"),
            "operation_assignments": relative(
                out_dir / "operation-assignments.jsonl"
            ),
        },
    }
    write_json(out_dir / "summary.json", summary)
    (out_dir / "report.md").write_text(markdown_report(summary), encoding="utf-8")
    print(
        json.dumps(
            {
                "mode": args.mode,
                "status": "valid",
                "tested_hypothesis": tested_hypothesis,
                "target_sessions": len(selected),
                "target_operations": expected_target_operations,
                "boundary_f1": metrics["recurrence"]["boundary"]["f1"],
                "bcubed_f1": metrics["recurrence"]["partition"]["f1"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
