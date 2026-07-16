#!/usr/bin/env python3
"""Evaluate reference-calibrated recurrence on existing complete trajectories.

The candidate keeps the current action-transition NPMI score and changes only
its scalar cutoff.  The cutoff maximizes operation-weighted B-cubed F1 on
reference-only group annotations, then applies unchanged to label-withheld
OSWorld-Human folds and CodeTraceBench failed trajectories.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import pyarrow.parquet as pq

from operation_boundary_backend_eval import (
    DEFAULT_OPERATION_FILE,
    binary_metrics,
    group_sequences,
    load_operations,
    normalize_fields,
    parse_requirement,
    sort_sequences,
    turn_key,
)
from rq3_codetracebench_stage_fidelity_eval import load_visible_operations
from rq3_osworld_boundary_fidelity_eval import exact_f1
from rq3_recurrence_stack_induction_eval import (
    EXPECTED as OSWORLD_EXPECTED,
    FOLD_COUNT,
    fold_for,
    predict_fold,
    transition_npmi,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CODETRACE_REFERENCE = (
    ROOT / "docs/visexp/out/codetracebench-rq2/full/reference-operations.jsonl"
)
DEFAULT_CODETRACE_TARGET = (
    ROOT / "docs/visexp/out/codetracebench-rq2/full/target-operations.jsonl"
)
DEFAULT_CODETRACE_MANIFEST = (
    ROOT / ".agentsight/experiments/codetracebench-rq2/manifests/verified.parquet"
)
DEFAULT_OSWORLD_BASELINE = (
    ROOT / ".agentsight/experiments/rq3-monotone-recurrence-v1/full/summary.json"
)
DEFAULT_CODETRACE_BASELINE = (
    ROOT
    / ".agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/full/summary.json"
)
CODETRACE_EXPECTED = {
    "reference_sessions": 2634,
    "reference_operations": 108569,
    "score_reference_sessions": 2229,
    "score_reference_operations": 87703,
    "calibration_sessions": 483,
    "calibration_operations": 18152,
    "calibration_stages": 2886,
    "target_sessions": 405,
    "target_operations": 20866,
    "target_pairs": 20461,
    "target_stages": 2948,
    "unavailable_non_target_manifest_sessions": 112,
}
EXPECTED_ACTIONS = {
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("preflight", "full"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--osworld-operations", type=Path, default=DEFAULT_OPERATION_FILE)
    parser.add_argument(
        "--codetrace-reference", type=Path, default=DEFAULT_CODETRACE_REFERENCE
    )
    parser.add_argument("--codetrace-target", type=Path, default=DEFAULT_CODETRACE_TARGET)
    parser.add_argument(
        "--codetrace-manifest", type=Path, default=DEFAULT_CODETRACE_MANIFEST
    )
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


def partition_metrics(rows: list[dict[str, Any]], method: str) -> dict[str, Any]:
    require(bool(rows), "B-cubed requires at least one operation")
    predicted_totals: Counter[str] = Counter(str(row[method]) for row in rows)
    oracle_totals: Counter[str] = Counter(str(row["oracle_group"]) for row in rows)
    overlaps: Counter[tuple[str, str]] = Counter(
        (str(row[method]), str(row["oracle_group"])) for row in rows
    )
    precision = sum(
        overlaps[(str(row[method]), str(row["oracle_group"]))]
        / predicted_totals[str(row[method])]
        for row in rows
    ) / len(rows)
    recall = sum(
        overlaps[(str(row[method]), str(row["oracle_group"]))]
        / oracle_totals[str(row["oracle_group"])]
        for row in rows
    ) / len(rows)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "operations": len(rows),
        "predicted_groups": len(predicted_totals),
        "oracle_groups": len(oracle_totals),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def boundary_metrics(rows: list[dict[str, Any]], method: str) -> dict[str, Any]:
    metrics = binary_metrics(
        [bool(row[method]) for row in rows],
        [bool(row["oracle_boundary"]) for row in rows],
    )
    return {**metrics, "f1_exact": exact_f1(metrics)}


def cutoff_candidates(scores: Iterable[float]) -> list[float]:
    distinct = sorted(set(float(score) for score in scores))
    require(bool(distinct), "calibration requires at least one observed transition score")
    require(all(math.isfinite(score) for score in distinct), "non-finite NPMI score")
    candidates = [math.nextafter(distinct[0], -math.inf)]
    for left, right in zip(distinct, distinct[1:]):
        midpoint = (left + right) / 2.0
        if midpoint <= left:
            midpoint = math.nextafter(left, math.inf)
        require(left < midpoint < right, "cannot construct a separating cutoff")
        candidates.append(midpoint)
    candidates.append(math.nextafter(distinct[-1], math.inf))
    require(
        all(math.isfinite(candidate) for candidate in candidates),
        "non-finite cutoff candidate",
    )
    return candidates


def predict_boundaries(
    sessions: list[str],
    visible: dict[str, list[str]],
    association: dict[tuple[str, str], float],
    cutoff: float,
) -> dict[tuple[str, int], dict[str, Any]]:
    predictions: dict[tuple[str, int], dict[str, Any]] = {}
    for session in sessions:
        actions = visible[session]
        for position, (left, right) in enumerate(zip(actions, actions[1:]), 1):
            score = association.get((left, right))
            key = (session, position)
            require(key not in predictions, f"duplicate pair prediction: {key}")
            predictions[key] = {
                "session": session,
                "position": position,
                "left_action": left,
                "right_action": right,
                "npmi": score,
                "unseen_in_reference": score is None,
                "cutoff": cutoff,
                "boundary": score is None or score < cutoff,
            }
    return predictions


def assignments_from_predictions(
    sessions: list[str],
    visible: dict[str, list[str]],
    predictions: dict[tuple[str, int], dict[str, Any]],
    method: str,
) -> dict[tuple[str, int], str]:
    assignments: dict[tuple[str, int], str] = {}
    for session in sessions:
        group = 0
        for index in range(len(visible[session])):
            if index:
                prediction = predictions[(session, index)]
                if bool(prediction[method]):
                    group += 1
            assignments[(session, index)] = f"{session}:group-{group:04d}"
    return assignments


def fit_cutoff(
    calibration_sessions: list[str],
    visible: dict[str, list[str]],
    association: dict[tuple[str, str], float],
    oracle: dict[tuple[str, int], str],
) -> tuple[float, dict[str, Any]]:
    calibration_scores = []
    unseen = 0
    for session in calibration_sessions:
        for left, right in zip(visible[session], visible[session][1:]):
            score = association.get((left, right))
            if score is None:
                unseen += 1
            else:
                calibration_scores.append(score)
    candidates = cutoff_candidates(calibration_scores)
    evaluated = []
    for cutoff in candidates:
        predictions = predict_boundaries(
            calibration_sessions, visible, association, cutoff
        )
        assignments = assignments_from_predictions(
            calibration_sessions, visible, predictions, "boundary"
        )
        rows = [
            {
                "candidate": assignments[(session, index)],
                "oracle_group": oracle[(session, index)],
            }
            for session in calibration_sessions
            for index in range(len(visible[session]))
        ]
        metrics = partition_metrics(rows, "candidate")
        evaluated.append({"cutoff": cutoff, "partition": metrics})
    best_f1 = max(float(row["partition"]["f1"]) for row in evaluated)
    ties = [row for row in evaluated if float(row["partition"]["f1"]) == best_f1]
    selected = min(ties, key=lambda row: float(row["cutoff"]))
    return float(selected["cutoff"]), {
        "calibration_sessions": len(calibration_sessions),
        "calibration_operations": sum(
            len(visible[session]) for session in calibration_sessions
        ),
        "calibration_pairs": sum(
            len(visible[session]) - 1 for session in calibration_sessions
        ),
        "observed_calibration_pairs": len(calibration_scores),
        "unseen_calibration_pairs": unseen,
        "distinct_scores": len(set(calibration_scores)),
        "candidate_cutoffs": len(candidates),
        "best_ties": len(ties),
        "selected_cutoff": float(selected["cutoff"]),
        "selected_partition": selected["partition"],
    }


def osworld_source(path: Path) -> tuple[dict[str, list[str]], list[str]]:
    """Return only eligible visible actions; no group value leaves this loader."""
    operations = load_operations(path)
    groups = group_sequences(
        operations,
        "session",
        "human_group",
        parse_requirement("group_alignment=exact"),
    )
    sort_sequences(groups, "turn")
    sessions = sorted(groups)
    counts = {
        "operations": sum(len(groups[session]) for session in sessions),
        "sessions": len(sessions),
        "pairs": sum(len(groups[session]) - 1 for session in sessions),
    }
    expected_visible = {
        key: OSWORLD_EXPECTED[key] for key in ("operations", "sessions", "pairs")
    }
    require(counts == expected_visible, f"OSWorld source counts changed: {counts}")
    visible = {
        session: [str(row["fields"]["action"]) for row in groups[session]]
        for session in sessions
    }
    return visible, sessions


def osworld_oracle(
    path: Path, sessions: list[str], visible: dict[str, list[str]]
) -> dict[tuple[str, int], str]:
    """Load group values only for the explicitly selected sessions."""
    wanted = set(sessions)
    selected: dict[str, list[dict[str, Any]]] = {session: [] for session in sessions}
    with path.open(encoding="utf-8") as source:
        for ordinal, line in enumerate(source):
            if not line.strip():
                continue
            record = json.loads(line)
            fields = normalize_fields(record.get("fields") or {})
            session = fields.get("session")
            if session not in wanted:
                continue
            if fields.get("group_alignment") != "exact" or not fields.get(
                "human_group"
            ):
                continue
            selected[session].append(
                {
                    "fields": fields,
                    "_ordinal": ordinal,
                }
            )
    oracle: dict[tuple[str, int], str] = {}
    for session in sessions:
        rows = selected[session]
        rows.sort(key=lambda row: turn_key(row, "turn"))
        require(len(rows) == len(visible[session]), f"oracle coverage: {session}")
        for index, row in enumerate(rows):
            require(
                row["fields"].get("action") == visible[session][index],
                f"oracle/action alignment: {session}:{index}",
            )
            oracle[(session, index)] = (
                f"{session}:{row['fields']['human_group']}"
            )
    return oracle


def score_osworld_fold(
    fold: int,
    source: Path,
    sessions: list[str],
    visible: dict[str, list[str]],
    out_dir: Path,
) -> dict[str, Any]:
    train = [session for session in sessions if fold_for(session) != fold]
    target = [session for session in sessions if fold_for(session) == fold]
    require(bool(train) and bool(target), f"OSWorld fold {fold} is empty")
    association, _, association_report = transition_npmi(train, visible)
    train_oracle = osworld_oracle(source, train, visible)
    cutoff, calibration = fit_cutoff(train, visible, association, train_oracle)
    candidate = predict_boundaries(target, visible, association, cutoff)
    current, current_report = predict_fold(fold, sessions, visible)
    require(set(candidate) == set(current), f"OSWorld fold {fold} pair mismatch")

    prediction_rows = []
    for key in sorted(candidate):
        row = dict(candidate[key])
        row["current_boundary"] = bool(current[key]["boundary"])
        prediction_rows.append(row)
    prediction_path = out_dir / f"fold-{fold}-predictions.jsonl"
    write_jsonl(prediction_path, prediction_rows)

    # Target annotations are accessed only after the target predictions exist.
    require(prediction_path.is_file(), "OSWorld target predictions were not persisted")
    target_oracle = osworld_oracle(source, target, visible)
    candidate_assignments = assignments_from_predictions(
        target, visible, candidate, "boundary"
    )
    current_for_assignment = {
        key: {"boundary": bool(value["boundary"])} for key, value in current.items()
    }
    current_assignments = assignments_from_predictions(
        target, visible, current_for_assignment, "boundary"
    )
    operation_rows = [
        {
            "session": session,
            "fold": fold,
            "operation_index": index,
            "action": visible[session][index],
            "oracle_group": target_oracle[(session, index)],
            "candidate": candidate_assignments[(session, index)],
            "current": current_assignments[(session, index)],
        }
        for session in target
        for index in range(len(visible[session]))
    ]
    pair_rows = []
    for key in sorted(candidate):
        session, position = key
        left_group = target_oracle[(session, position - 1)]
        right_group = target_oracle[(session, position)]
        pair_rows.append(
            {
                **candidate[key],
                "fold": fold,
                "candidate": bool(candidate[key]["boundary"]),
                "current": bool(current[key]["boundary"]),
                "oracle_boundary": left_group != right_group,
            }
        )
    return {
        "fold": fold,
        "train_sessions": len(train),
        "target_sessions": len(target),
        "association": association_report,
        "current_calibration": current_report,
        "calibration": calibration,
        "pair_rows": pair_rows,
        "operation_rows": operation_rows,
    }


def evaluate_osworld(mode: str, source: Path, out_dir: Path) -> dict[str, Any]:
    visible, sessions = osworld_source(source)
    selected_folds = [0] if mode == "preflight" else list(range(FOLD_COUNT))
    folds = [
        score_osworld_fold(fold, source, sessions, visible, out_dir)
        for fold in selected_folds
    ]
    pair_rows = [row for fold in folds for row in fold.pop("pair_rows")]
    operation_rows = [row for fold in folds for row in fold.pop("operation_rows")]
    selected_sessions = [
        session for session in sessions if fold_for(session) in selected_folds
    ]
    require(
        len(operation_rows)
        == sum(len(visible[session]) for session in selected_sessions),
        "OSWorld operation coverage mismatch",
    )
    require(
        len(pair_rows)
        == sum(len(visible[session]) - 1 for session in selected_sessions),
        "OSWorld pair coverage mismatch",
    )
    write_jsonl(out_dir / "pair-decisions.jsonl", pair_rows)
    write_jsonl(out_dir / "operation-assignments.jsonl", operation_rows)
    metrics = {
        method: {
            "boundary": boundary_metrics(pair_rows, method),
            "partition": partition_metrics(operation_rows, method),
        }
        for method in ("candidate", "current")
    }
    if mode == "full":
        require(
            metrics["candidate"]["partition"]["oracle_groups"]
            == OSWORLD_EXPECTED["human_groups"],
            "OSWorld oracle group count changed",
        )
        historical = json.loads(DEFAULT_OSWORLD_BASELINE.read_text(encoding="utf-8"))
        require(
            abs(
                metrics["current"]["boundary"]["f1_exact"]
                - float(historical["boundary_metrics"]["recurrence"]["f1_exact"])
            )
            < 1e-15,
            "OSWorld current boundary baseline changed",
        )
        require(
            abs(
                metrics["current"]["partition"]["f1"]
                - float(historical["partition_metrics"]["recurrence"]["f1"])
            )
            < 1e-15,
            "OSWorld current partition baseline changed",
        )
    return {
        "source": relative(source),
        "selected_folds": selected_folds,
        "population": {
            "sessions": len(selected_sessions),
            "operations": len(operation_rows),
            "pairs": len(pair_rows),
            "oracle_groups": metrics["candidate"]["partition"]["oracle_groups"],
        },
        "folds": folds,
        "metrics": metrics,
        "prediction_before_target_oracle": True,
    }


def load_stage_map(
    path: Path,
    selected: list[str],
    operations: dict[str, list[dict[str, Any]]],
    expected_solved: bool,
    isolated_rows_path: Path,
) -> tuple[dict[tuple[str, int], str], dict[str, str], int]:
    isolated_rows_path.parent.mkdir(parents=True, exist_ok=True)
    selected_path = isolated_rows_path.with_name(
        f"{isolated_rows_path.stem}-selected-ids.json"
    )
    write_json(selected_path, selected)
    extraction_code = """
import json
import sys
from pathlib import Path
import pyarrow.parquet as pq

manifest = Path(sys.argv[1])
wanted = set(json.loads(Path(sys.argv[2]).read_text(encoding="utf-8")))
output = Path(sys.argv[3])
table = pq.read_table(
    manifest,
    columns=["traj_id", "agent", "solved", "step_count", "stages"],
)
rows = [row for row in table.to_pylist() if str(row["traj_id"]) in wanted]
output.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
"""
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            extraction_code,
            str(path.resolve()),
            str(selected_path.resolve()),
            str(isolated_rows_path.resolve()),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    (isolated_rows_path.parent / f"{isolated_rows_path.stem}-extract.stdout").write_text(
        completed.stdout, encoding="utf-8"
    )
    (isolated_rows_path.parent / f"{isolated_rows_path.stem}-extract.stderr").write_text(
        completed.stderr, encoding="utf-8"
    )
    require(completed.returncode == 0, "isolated manifest stage extraction failed")
    rows = json.loads(isolated_rows_path.read_text(encoding="utf-8"))
    wanted = set(selected)
    require(
        {str(row["traj_id"]) for row in rows} == wanted,
        "isolated manifest selection mismatch",
    )
    seen: set[str] = set()
    stage_by_step: dict[tuple[str, int], str] = {}
    framework_by_session: dict[str, str] = {}
    stage_count = 0
    for row in rows:
        session = str(row["traj_id"])
        require(session in wanted, f"unexpected manifest session: {session}")
        require(session not in seen, f"duplicate manifest session: {session}")
        seen.add(session)
        require(row["solved"] is expected_solved, f"unexpected solved value: {session}")
        require(
            int(row["step_count"]) == len(operations[session]),
            f"stage step count mismatch: {session}",
        )
        cursor = 1
        for stage in row["stages"] or []:
            start = int(stage["start_step_id"])
            end = int(stage["end_step_id"])
            require(start == cursor and end >= start, f"stage gap/overlap: {session}")
            stage_id = f"{session}:stage-{int(stage['stage_id']):04d}"
            for step_id in range(start, end + 1):
                key = (session, step_id - 1)
                require(key not in stage_by_step, f"duplicate stage step: {key}")
                stage_by_step[key] = stage_id
            cursor = end + 1
            stage_count += 1
        require(cursor == len(operations[session]) + 1, f"incomplete stages: {session}")
        framework_by_session[session] = str(row["agent"])
    require(seen == wanted, "manifest stage coverage mismatch")
    return stage_by_step, framework_by_session, stage_count


def evaluate_codetrace(
    mode: str,
    reference_path: Path,
    target_path: Path,
    manifest_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    references = load_visible_operations(reference_path)
    targets = load_visible_operations(target_path)
    require(len(references) == CODETRACE_EXPECTED["reference_sessions"], "reference sessions")
    require(
        sum(map(len, references.values())) == CODETRACE_EXPECTED["reference_operations"],
        "reference operations",
    )
    require(len(targets) == CODETRACE_EXPECTED["target_sessions"], "target sessions")
    require(
        sum(map(len, targets.values())) == CODETRACE_EXPECTED["target_operations"],
        "target operations",
    )
    target_ids = set(targets)
    score_reference = sorted(set(references) - target_ids)
    require(
        len(score_reference) == CODETRACE_EXPECTED["score_reference_sessions"],
        "score reference sessions",
    )
    require(
        sum(len(references[session]) for session in score_reference)
        == CODETRACE_EXPECTED["score_reference_operations"],
        "score reference operations",
    )
    actions = {
        session: [str(row["action"]) for row in references[session]]
        for session in score_reference
    }
    target_actions = {
        session: [str(row["action"]) for row in targets[session]]
        for session in sorted(targets)
    }
    all_actions = {
        row["action"]
        for session in score_reference
        for row in references[session]
    }
    require(all_actions == EXPECTED_ACTIONS, "CodeTrace action kinds changed")

    identities = pq.read_table(
        manifest_path, columns=["traj_id", "agent", "solved", "step_count"]
    ).to_pylist()
    by_id = {str(row["traj_id"]): row for row in identities}
    calibration = sorted(
        session
        for session in score_reference
        if session in by_id
        and by_id[session]["solved"] is True
        and int(by_id[session]["step_count"]) == len(references[session])
    )
    require(
        len(calibration) == CODETRACE_EXPECTED["calibration_sessions"],
        "calibration sessions",
    )
    require(
        sum(len(references[session]) for session in calibration)
        == CODETRACE_EXPECTED["calibration_operations"],
        "calibration operations",
    )
    unavailable = set(by_id) - target_ids - set(references)
    require(
        len(unavailable)
        == CODETRACE_EXPECTED["unavailable_non_target_manifest_sessions"],
        "unavailable manifest references",
    )

    association, _, association_report = transition_npmi(score_reference, actions)
    calibration_oracle, calibration_frameworks, calibration_stages = load_stage_map(
        manifest_path,
        calibration,
        references,
        True,
        out_dir / "calibration-stage-source.json",
    )
    require(
        calibration_stages == CODETRACE_EXPECTED["calibration_stages"],
        "calibration stages",
    )
    cutoff, calibration_report = fit_cutoff(
        calibration, actions, association, calibration_oracle
    )

    selected = sorted(targets)
    if mode == "preflight":
        selected = selected[:1]
    candidate = predict_boundaries(selected, target_actions, association, cutoff)
    prediction_rows = [dict(candidate[key]) for key in sorted(candidate)]
    prediction_path = out_dir / "target-predictions.jsonl"
    write_jsonl(prediction_path, prediction_rows)

    # Failed-target stages become available only after target predictions exist.
    require(prediction_path.is_file(), "CodeTrace target predictions were not persisted")
    target_oracle, target_frameworks, target_stages = load_stage_map(
        manifest_path,
        selected,
        targets,
        False,
        out_dir / "target-stage-source.json",
    )
    assignments = assignments_from_predictions(
        selected, target_actions, candidate, "boundary"
    )
    operation_rows = [
        {
            "session": session,
            "framework": target_frameworks[session],
            "operation_index": index,
            "action": target_actions[session][index],
            "oracle_group": target_oracle[(session, index)],
            "candidate": assignments[(session, index)],
        }
        for session in selected
        for index in range(len(target_actions[session]))
    ]
    pair_rows = []
    for key in sorted(candidate):
        session, position = key
        pair_rows.append(
            {
                **candidate[key],
                "framework": target_frameworks[session],
                "candidate": bool(candidate[key]["boundary"]),
                "oracle_boundary": target_oracle[(session, position - 1)]
                != target_oracle[(session, position)],
            }
        )
    require(
        len(operation_rows) == sum(len(targets[session]) for session in selected),
        "CodeTrace operation coverage mismatch",
    )
    require(
        len(pair_rows)
        == sum(len(targets[session]) - 1 for session in selected),
        "CodeTrace pair coverage mismatch",
    )
    write_jsonl(out_dir / "pair-decisions.jsonl", pair_rows)
    write_jsonl(out_dir / "operation-assignments.jsonl", operation_rows)
    candidate_metrics = {
        "boundary": boundary_metrics(pair_rows, "candidate"),
        "partition": partition_metrics(operation_rows, "candidate"),
    }
    per_framework = {
        framework: {
            "boundary": boundary_metrics(
                [row for row in pair_rows if row["framework"] == framework],
                "candidate",
            ),
            "partition": partition_metrics(
                [row for row in operation_rows if row["framework"] == framework],
                "candidate",
            ),
        }
        for framework in sorted(set(target_frameworks.values()))
    }
    baseline = json.loads(DEFAULT_CODETRACE_BASELINE.read_text(encoding="utf-8"))
    current_metrics = baseline["metrics"]["recurrence"] if mode == "full" else None
    if mode == "full":
        require(len(selected) == CODETRACE_EXPECTED["target_sessions"], "full targets")
        require(len(operation_rows) == CODETRACE_EXPECTED["target_operations"], "full ops")
        require(len(pair_rows) == CODETRACE_EXPECTED["target_pairs"], "full pairs")
        require(target_stages == CODETRACE_EXPECTED["target_stages"], "full stages")
    return {
        "inputs": {
            "reference": relative(reference_path),
            "target": relative(target_path),
            "manifest": relative(manifest_path),
        },
        "population": {
            "score_reference_sessions": len(score_reference),
            "score_reference_operations": sum(
                len(references[session]) for session in score_reference
            ),
            "calibration_sessions": len(calibration),
            "calibration_operations": sum(
                len(references[session]) for session in calibration
            ),
            "calibration_stages": calibration_stages,
            "target_sessions": len(selected),
            "target_operations": len(operation_rows),
            "target_pairs": len(pair_rows),
            "target_stages": target_stages,
            "target_frameworks": dict(Counter(target_frameworks.values())),
            "calibration_frameworks": dict(Counter(calibration_frameworks.values())),
        },
        "association": association_report,
        "calibration": calibration_report,
        "metrics": {"candidate": candidate_metrics, "current": current_metrics},
        "per_framework": per_framework,
        "prediction_before_target_oracle": True,
    }


def relation(candidate: float, current: float) -> str:
    if candidate > current:
        return "higher"
    if candidate < current:
        return "lower"
    return "equal"


def markdown_report(summary: dict[str, Any]) -> str:
    os_metrics = summary["osworld"]["metrics"]
    ct_metrics = summary["codetrace"]["metrics"]
    lines = [
        "# Reference-Calibrated Existing-Trajectory Result",
        "",
        f"**Mode:** {summary['mode']}  ",
        f"**Run status:** {summary['run_status']}  ",
        f"**Tested hypothesis:** {summary['tested_hypothesis']}",
        "",
        "## Population",
        "",
        (
            f"- OSWorld-Human: {summary['osworld']['population']['sessions']} sessions, "
            f"{summary['osworld']['population']['operations']} operations, "
            f"{summary['osworld']['population']['pairs']} pairs."
        ),
        (
            f"- CodeTraceBench: {summary['codetrace']['population']['calibration_sessions']} "
            f"calibration sessions -> {summary['codetrace']['population']['target_sessions']} "
            f"target sessions / {summary['codetrace']['population']['target_operations']} operations."
        ),
        "",
        "## B-cubed Partition Fidelity",
        "",
        "| Population | Candidate | Current Step 0024 | Delta |",
        "|---|---:|---:|---:|",
    ]
    os_candidate = float(os_metrics["candidate"]["partition"]["f1"])
    os_current = float(os_metrics["current"]["partition"]["f1"])
    lines.append(
        f"| OSWorld-Human | {os_candidate:.6f} | {os_current:.6f} | {os_candidate-os_current:+.6f} |"
    )
    if ct_metrics["current"] is not None:
        ct_candidate = float(ct_metrics["candidate"]["partition"]["f1"])
        ct_current = float(ct_metrics["current"]["partition"]["f1"])
        lines.append(
            f"| CodeTraceBench | {ct_candidate:.6f} | {ct_current:.6f} | {ct_candidate-ct_current:+.6f} |"
        )
    else:
        lines.append(
            f"| CodeTraceBench preflight | {float(ct_metrics['candidate']['partition']['f1']):.6f} | n/a | n/a |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            summary["interpretation"],
            "",
            "Preflight metrics are diagnostic only. Full-run classification follows the fixed plan and never changes the paper story, thesis, or RQs automatically.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    out_dir = absolute(args.out)
    osworld_path = absolute(args.osworld_operations)
    reference_path = absolute(args.codetrace_reference)
    target_path = absolute(args.codetrace_target)
    manifest_path = absolute(args.codetrace_manifest)
    for path in (osworld_path, reference_path, target_path, manifest_path):
        require(path.is_file(), f"missing input: {relative(path)}")
    out_dir.mkdir(parents=True, exist_ok=True)

    osworld = evaluate_osworld(
        args.mode, osworld_path, out_dir / "osworld-human"
    )
    codetrace = evaluate_codetrace(
        args.mode,
        reference_path,
        target_path,
        manifest_path,
        out_dir / "codetracebench",
    )
    if args.mode == "preflight":
        tested_hypothesis = "not tested"
        interpretation = (
            "The real existing-trajectory fitting, persistence, and scoring paths ran "
            "end to end. Preflight does not classify the scientific hypothesis."
        )
        relations = None
    else:
        os_candidate = float(osworld["metrics"]["candidate"]["partition"]["f1"])
        os_current = float(osworld["metrics"]["current"]["partition"]["f1"])
        ct_candidate = float(codetrace["metrics"]["candidate"]["partition"]["f1"])
        ct_current = float(codetrace["metrics"]["current"]["partition"]["f1"])
        relations = {
            "osworld": {
                "relation": relation(os_candidate, os_current),
                "delta": os_candidate - os_current,
            },
            "codetrace": {
                "relation": relation(ct_candidate, ct_current),
                "delta": ct_candidate - ct_current,
            },
        }
        higher = sum(row["relation"] == "higher" for row in relations.values())
        if higher == 2:
            tested_hypothesis = "supported"
        elif higher == 1:
            tested_hypothesis = "mixed"
        else:
            tested_hypothesis = "contradicted"
        interpretation = (
            "Reference-only scalar calibration is "
            f"{relations['osworld']['relation']} on OSWorld-Human and "
            f"{relations['codetrace']['relation']} on CodeTraceBench relative to the "
            "current Step 0024 constructor. This is supporting algorithm evidence on "
            "reused development populations, not a whole-RQ3 or thesis verdict."
        )

    summary = {
        "schema": "agentsight.rq3-reference-calibrated-existing-traces.v1",
        "mode": args.mode,
        "run_status": "valid",
        "tested_hypothesis": tested_hypothesis,
        "research_value": "supporting" if args.mode == "full" else "dependency-only",
        "paper_impact": (
            "additional RQ3 algorithm evidence" if args.mode == "full" else "none"
        ),
        "interpretation": interpretation,
        "algorithm": {
            "base": "Step 0024 action-transition NPMI recurrence",
            "change": "one scalar cutoff maximizing reference-only operation-weighted B-cubed F1",
            "unseen_transition": "boundary",
            "target_label_access": "after persisted predictions only",
            "target_informed_retry": False,
        },
        "relations": relations,
        "osworld": osworld,
        "codetrace": codetrace,
        "validity": {
            "existing_trajectories_only": True,
            "complete_populations": args.mode == "full"
            and osworld["population"]["sessions"] == OSWORLD_EXPECTED["sessions"]
            and codetrace["population"]["target_sessions"]
            == CODETRACE_EXPECTED["target_sessions"],
            "reference_only_cutoff": True,
            "prediction_before_target_oracle": osworld[
                "prediction_before_target_oracle"
            ]
            and codetrace["prediction_before_target_oracle"],
            "one_assignment_per_operation": True,
            "one_candidate_no_retry": True,
            "paper_product_skills_untouched": True,
        },
        "raw": {
            "osworld": relative(out_dir / "osworld-human"),
            "codetrace": relative(out_dir / "codetracebench"),
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
                "osworld_candidate_bcubed": osworld["metrics"]["candidate"][
                    "partition"
                ]["f1"],
                "codetrace_candidate_bcubed": codetrace["metrics"]["candidate"][
                    "partition"
                ]["f1"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
