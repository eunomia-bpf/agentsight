#!/usr/bin/env python3
"""Verify Rust/Python equivalence for the tested reference calibration path."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rq3_reference_calibrated_existing_traces_eval as experiment


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BINARY = ROOT / "agentpprof/target/release/agentpprof"
DEFAULT_ANALYSIS_ROOT = (
    ROOT / ".agentsight/experiments/rq3-reference-calibrated-existing-traces-v1/full"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--analysis-root", type=Path, default=DEFAULT_ANALYSIS_ROOT)
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


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def product_rows(
    visible: dict[str, list[str]],
    sessions: Iterable[str],
    oracle: dict[tuple[str, int], str] | None = None,
) -> Iterable[dict[str, Any]]:
    for session in sorted(sessions):
        for index, action in enumerate(visible[session]):
            fields = {"session": session, "action": action}
            if oracle is not None:
                fields["group"] = oracle[(session, index)]
            yield {"value": 1, "fields": fields}


def run_product(
    binary: Path,
    out_dir: Path,
    reference_rows: Iterable[dict[str, Any]],
    calibration_rows: Iterable[dict[str, Any]],
    target_rows: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    reference_path = out_dir / "reference.jsonl"
    calibration_path = out_dir / "calibration.jsonl"
    target_path = out_dir / "target.jsonl"
    profile_path = out_dir / "profile.json"
    write_jsonl(reference_path, reference_rows)
    write_jsonl(calibration_path, calibration_rows)
    write_jsonl(target_path, target_rows)
    command = [
        str(binary.resolve()),
        "--operation-file",
        str(target_path.resolve()),
        "--view",
        "operations",
        "--format",
        "json",
        "--output",
        str(profile_path.resolve()),
        "--induce-operation-stack",
        "--induce-reference-operation-file",
        str(reference_path.resolve()),
        "--induce-calibration-operation-file",
        str(calibration_path.resolve()),
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
    require(completed.returncode == 0, f"agentpprof failed in {relative(out_dir)}")
    status = json.loads(completed.stdout)
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    require(status["status"] == "ok", "agentpprof status is not ok")
    require(
        int(status["samples"]) == int(profile["profile"]["summary"]["total_weight"]),
        "agentpprof target mass mismatch",
    )
    return profile["profile"]["operation_stack_induction"]


def close(left: float, right: float, tolerance: float = 1e-12) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=tolerance)


def expected_segments(
    visible: dict[str, list[str]],
    sessions: list[str],
    predictions: dict[tuple[str, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    output = []
    for session in sorted(sessions):
        boundaries = [0]
        for position in range(1, len(visible[session])):
            if bool(predictions[(session, position)]["boundary"]):
                boundaries.append(position)
        boundaries.append(len(visible[session]))
        for start, end in zip(boundaries, boundaries[1:]):
            compact = []
            for action in visible[session][start:end]:
                if not compact or compact[-1] != action:
                    compact.append(action)
            output.append(
                {
                    "session": session,
                    "start": start,
                    "end": end,
                    "motif": "action=" + "-then-".join(compact),
                }
            )
    return output


def compare_report(
    report: dict[str, Any],
    expected_predictions: list[dict[str, Any]],
    expected_calibration: dict[str, Any],
    visible: dict[str, list[str]],
    target_sessions: list[str],
) -> dict[str, Any]:
    supervised = report["supervised_calibration"]
    require(
        supervised["policy"] == "reference-group-bcubed-scalar-calibration",
        "unexpected Rust supervised policy",
    )
    require(
        int(supervised["candidate_cutoffs"])
        == int(expected_calibration["candidate_cutoffs"]),
        "candidate cutoff count mismatch",
    )
    require(
        int(supervised["distinct_scores"])
        == int(expected_calibration["distinct_scores"]),
        "distinct score count mismatch",
    )
    require(
        int(supervised["best_ties"]) == int(expected_calibration["best_ties"]),
        "best tie count mismatch",
    )
    require(
        float(supervised["selected_cutoff"])
        == float(expected_calibration["selected_cutoff"]),
        "selected cutoff mismatch",
    )
    for rust_key, python_key in (
        ("selected_precision", "precision"),
        ("selected_recall", "recall"),
        ("selected_f1", "f1"),
    ):
        require(
            close(
                float(supervised[rust_key]),
                float(expected_calibration["selected_partition"][python_key]),
            ),
            f"calibration {rust_key} mismatch",
        )

    expected = {
        (str(row["session"]), int(row["position"])): row
        for row in expected_predictions
    }
    actual = {
        (str(row["session"]), int(row["position"])): row
        for row in report["boundary_decisions"]
    }
    require(set(actual) == set(expected), "target decision key mismatch")
    for key, rust in actual.items():
        python = expected[key]
        require(bool(rust["boundary"]) == bool(python["boundary"]), f"boundary {key}")
        require(
            bool(rust["label_free_boundary"]) == bool(python["current_boundary"]),
            f"label-free boundary {key}",
        )
        require(
            float(rust["applied_cutoff"]) == float(python["cutoff"]),
            f"applied cutoff {key}",
        )
        if python["npmi"] is None:
            require(rust["npmi"] is None, f"unseen NPMI {key}")
        else:
            require(
                close(float(rust["npmi"]), float(python["npmi"]), 1e-15),
                f"NPMI {key}",
            )
    expected_segment_rows = expected_segments(visible, target_sessions, expected)
    require(report["segments"] == expected_segment_rows, "segment or motif mismatch")
    require(
        int(report["target_operations"])
        == sum(len(visible[session]) for session in target_sessions),
        "target operation count mismatch",
    )
    return {
        "target_sessions": len(target_sessions),
        "target_operations": int(report["target_operations"]),
        "target_decisions": len(actual),
        "segments": len(report["segments"]),
        "selected_cutoff": float(supervised["selected_cutoff"]),
        "calibration_f1": float(supervised["selected_f1"]),
        "all_decisions_equal": True,
        "all_npmi_equal_within_1e-15": True,
        "all_segments_and_motifs_equal": True,
    }


def stage_oracle(path: Path, selected: list[str]) -> dict[tuple[str, int], str]:
    wanted = set(selected)
    rows = json.loads(path.read_text(encoding="utf-8"))
    require({str(row["traj_id"]) for row in rows} == wanted, "stage source IDs")
    oracle = {}
    for row in rows:
        session = str(row["traj_id"])
        cursor = 1
        for stage in row["stages"] or []:
            start = int(stage["start_step_id"])
            end = int(stage["end_step_id"])
            require(start == cursor, f"stage gap: {session}")
            group = f"{session}:stage-{int(stage['stage_id']):04d}"
            for step_id in range(start, end + 1):
                oracle[(session, step_id - 1)] = group
            cursor = end + 1
    return oracle


def verify_osworld(
    binary: Path, analysis_root: Path, analysis: dict[str, Any], out_dir: Path
) -> list[dict[str, Any]]:
    source = experiment.absolute(experiment.DEFAULT_OPERATION_FILE)
    visible, sessions = experiment.osworld_source(source)
    output = []
    for fold in range(experiment.FOLD_COUNT):
        train = [session for session in sessions if experiment.fold_for(session) != fold]
        target = [session for session in sessions if experiment.fold_for(session) == fold]
        oracle = experiment.osworld_oracle(source, train, visible)
        report = run_product(
            binary,
            out_dir / f"fold-{fold}",
            product_rows(visible, train),
            product_rows(visible, train, oracle),
            product_rows(visible, target),
        )
        expected_predictions = load_jsonl(
            analysis_root / f"osworld-human/fold-{fold}-predictions.jsonl"
        )
        expected_calibration = analysis["osworld"]["folds"][fold]["calibration"]
        row = compare_report(
            report, expected_predictions, expected_calibration, visible, target
        )
        row["fold"] = fold
        output.append(row)
    return output


def verify_codetrace(
    binary: Path, analysis_root: Path, analysis: dict[str, Any], out_dir: Path
) -> dict[str, Any]:
    reference_path = experiment.absolute(experiment.DEFAULT_CODETRACE_REFERENCE)
    target_path = experiment.absolute(experiment.DEFAULT_CODETRACE_TARGET)
    manifest_path = experiment.absolute(experiment.DEFAULT_CODETRACE_MANIFEST)
    references = experiment.load_visible_operations(reference_path)
    targets = experiment.load_visible_operations(target_path)
    target_ids = set(targets)
    score_reference = sorted(set(references) - target_ids)
    identities = pq.read_table(
        manifest_path, columns=["traj_id", "solved", "step_count"]
    ).to_pylist()
    by_id = {str(row["traj_id"]): row for row in identities}
    calibration = sorted(
        session
        for session in score_reference
        if session in by_id
        and by_id[session]["solved"] is True
        and int(by_id[session]["step_count"]) == len(references[session])
    )
    visible_reference = {
        session: [str(row["action"]) for row in references[session]]
        for session in score_reference
    }
    visible_target = {
        session: [str(row["action"]) for row in targets[session]]
        for session in sorted(targets)
    }
    oracle = stage_oracle(
        analysis_root / "codetracebench/calibration-stage-source.json", calibration
    )
    report = run_product(
        binary,
        out_dir,
        product_rows(visible_reference, score_reference),
        product_rows(visible_reference, calibration, oracle),
        product_rows(visible_target, sorted(targets)),
    )
    expected_predictions = load_jsonl(
        analysis_root / "codetracebench/target-predictions.jsonl"
    )
    label_free = {
        (str(row["session"]), int(row["position"])): bool(row["recurrence"])
        for row in load_jsonl(
            ROOT
            / ".agentsight/experiments/rq3-monotone-recurrence-codetracebench-v1/full/pair-decisions.jsonl"
        )
    }
    require(
        len(label_free) == len(expected_predictions),
        "CodeTrace label-free decision coverage mismatch",
    )
    for row in expected_predictions:
        row["current_boundary"] = label_free[
            (str(row["session"]), int(row["position"]))
        ]
    return compare_report(
        report,
        expected_predictions,
        analysis["codetrace"]["calibration"],
        visible_target,
        sorted(targets),
    )


def markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Rust/Python Reference-Calibration Equivalence",
        "",
        "**Verdict:** PASS",
        "",
        "## Complete Coverage",
        "",
        f"- OSWorld-Human: {sum(row['target_sessions'] for row in summary['osworld'])} sessions / {sum(row['target_operations'] for row in summary['osworld'])} operations / {sum(row['target_decisions'] for row in summary['osworld'])} decisions across five folds.",
        f"- CodeTraceBench: {summary['codetrace']['target_sessions']} sessions / {summary['codetrace']['target_operations']} operations / {summary['codetrace']['target_decisions']} decisions.",
        "",
        "Every selected cutoff, calibration objective, NPMI value, target boundary, segment, and motif matches the independently reviewed Python result.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    binary = absolute(args.binary)
    analysis_root = absolute(args.analysis_root)
    out_dir = absolute(args.out)
    require(binary.is_file(), f"missing release binary: {relative(binary)}")
    summary_path = analysis_root / "summary.json"
    require(summary_path.is_file(), f"missing analysis summary: {relative(summary_path)}")
    analysis = json.loads(summary_path.read_text(encoding="utf-8"))
    require(analysis["mode"] == "full", "equivalence requires the full analysis")
    out_dir.mkdir(parents=True, exist_ok=True)

    osworld = verify_osworld(binary, analysis_root, analysis, out_dir / "osworld-human")
    codetrace = verify_codetrace(
        binary, analysis_root, analysis, out_dir / "codetracebench"
    )
    summary = {
        "schema": "agentsight.rq3-reference-calibrated-rust-equivalence.v1",
        "status": "pass",
        "binary": relative(binary),
        "analysis_root": relative(analysis_root),
        "osworld": osworld,
        "codetrace": codetrace,
        "validity": {
            "complete_populations": sum(row["target_sessions"] for row in osworld)
            == 287
            and codetrace["target_sessions"] == 405,
            "all_selected_cutoffs_equal": True,
            "all_target_decisions_equal": True,
            "all_npmi_equal_within_1e-15": True,
            "all_segments_and_motifs_equal": True,
        },
    }
    write_json(out_dir / "summary.json", summary)
    (out_dir / "report.md").write_text(markdown_report(summary), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "pass",
                "osworld_decisions": sum(row["target_decisions"] for row in osworld),
                "codetrace_decisions": codetrace["target_decisions"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
