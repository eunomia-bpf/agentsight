#!/usr/bin/env python3
"""Recompute the invariance local grid on the repaired v2 projection.

The local project×vendor inputs are regenerated from v2 events and v2 RQ
rows.  The public RQ6 portion is deliberately not rerun because the projection
repair cannot affect it; its frozen external-status summary is hash-pinned and
reused only for the original classification gate.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Sequence


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BUILD = ROOT / "docs/tmp/build-and-evaluate"
V2 = BUILD / "rq1-rq4-recompute-v2-20260727"
LEGACY_ANALYSIS = HERE / "legacy_analysis.py"
BASELINE_CLASSIFICATION = HERE / "baseline-metric-classification.csv"
BEHAVIOR_SCRIPT = BUILD / "toolcall-behavior-20260726/analyze_toolcalls.py"
SESSION_SCRIPT = BUILD / "session-dynamics-20260726/analysis.py"
RQ6_REUSED = HERE / "baseline-rq6-external-summary.csv"


def import_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(
    path: Path,
    rows: list[dict[str, Any]],
    fields: Sequence[str] | None = None,
) -> None:
    if not rows:
        raise ValueError(f"refusing to write headerless empty output: {path}")
    if fields is None:
        fields = list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=list(fields),
            extrasaction="raise",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def regenerate_behavior(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BEHAVIOR_SCRIPT, output / "analyze_toolcalls.py")
    subprocess.run(
        [
            sys.executable,
            str(BEHAVIOR_SCRIPT),
            "--events-dir",
            str(V2 / "rq1-raw/events"),
            "--output-dir",
            str(output),
            "--no-native-batches",
        ],
        check=True,
    )


def regenerate_session_dynamics(output: Path) -> None:
    module = import_module(SESSION_SCRIPT, "session_dynamics_v2")
    module.HERE = output
    module.DATA = V2 / "rq1-raw/events"
    module.RAW = output / "raw"
    module.FIGURES = output / "figures"
    module.ensure_dirs()
    corpus = module.load_corpus()
    if len(corpus.events) != 181_303 or len(corpus.sessions) != 551:
        raise ValueError(
            f"unexpected v2 session corpus: "
            f"{len(corpus.events)} events/{len(corpus.sessions)} sessions"
        )
    module.run_analysis(corpus, write=True)


def external_status_from_reused_rq6() -> dict[str, str]:
    statuses = {}
    for row in read_csv(RQ6_REUSED):
        metric = row["mapped_local_metric"]
        if metric != "analogous_only":
            statuses[metric] = row["external_status"]
    return statuses


def classification_delta(
    current: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    previous = {
        row["metric"]: row
        for row in read_csv(BASELINE_CLASSIFICATION)
    }
    rows = []
    for row in current:
        old = previous[str(row["metric"])]
        rows.append(
            {
                "metric": row["metric"],
                "metric_label": row["metric_label"],
                "old_eligible_cells": old["eligible_cells"],
                "new_eligible_cells": row["eligible_cells"],
                "old_cv": old["cv"],
                "new_cv": row["cv"],
                "old_direction_consistency": old[
                    "direction_consistency"
                ],
                "new_direction_consistency": row[
                    "direction_consistency"
                ],
                "old_vendor_ss_share": old["vendor_ss_share"],
                "new_vendor_ss_share": row["vendor_ss_share"],
                "old_classification": old["classification"],
                "new_classification": row["classification"],
                "classification_changed": (
                    old["classification"] != row["classification"]
                ),
            }
        )
    return rows


def input_manifest() -> list[dict[str, Any]]:
    paths = [
        HERE / "analysis.py",
        LEGACY_ANALYSIS,
        BASELINE_CLASSIFICATION,
        BEHAVIOR_SCRIPT,
        SESSION_SCRIPT,
        RQ6_REUSED,
        V2 / "rq2/raw/rq2-trajectory.csv",
        V2 / "rq4/raw/rq4-accesses.csv",
        V2 / "extensions/rq1-revivals.csv",
        V2 / "extensions/rq1-dormancy-summary.csv",
        *sorted((V2 / "rq1-raw/events").glob("*.json.gz")),
    ]
    return [
        {
            "input": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "role": (
                "reused-rq6-public-summary"
                if path == RQ6_REUSED
                else "old-local-classification-baseline"
                if path == BASELINE_CLASSIFICATION
                else "v2-local-input"
                if V2 in path.parents
                else "analysis-code"
            ),
        }
        for path in paths
    ]


def run(output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    (output / "figures").mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="agentsight-invariance-v2-"
    ) as temporary:
        temporary_root = Path(temporary)
        behavior = temporary_root / "behavior"
        session = temporary_root / "session"
        regenerate_behavior(behavior)
        regenerate_session_dynamics(session)

        analysis = import_module(
            LEGACY_ANALYSIS, "invariance_mining_20260726_v2"
        )
        analysis.FINAL = V2
        analysis.BEHAVIOR = behavior
        analysis.SESSION = session
        analysis.RQ_EXTENSIONS = V2 / "extensions"
        for metric_spec in analysis.METRICS.values():
            metric_spec["source"] = str(metric_spec["source"]).replace(
                "final-HEAD", "repaired v2"
            )

        selected = set(analysis.PROJECTS)
        cells, _session_counts = analysis.load_behavior_metrics(selected)
        analysis.load_startup_and_drift(cells, selected)
        analysis.load_zero_validation(cells, selected)
        _target_counts, _local_external = analysis.load_path_metrics(
            cells, selected
        )
        analysis.load_shell_bursts(cells, selected)

        metric_rows = []
        for metric in analysis.METRICS:
            for project in analysis.PROJECTS:
                for vendor in analysis.VENDORS:
                    key = (project, vendor, metric)
                    if key in cells:
                        metric_rows.append(cells[key])
                    else:
                        metric_rows.append(
                            analysis.metric_row(
                                metric,
                                project,
                                vendor,
                                None,
                                None,
                                None,
                                0,
                                False,
                                "no observations",
                            )
                        )

        classifications = analysis.classify_metrics(
            metric_rows, external_status_from_reused_rq6()
        )
        deltas = classification_delta(classifications)
        write_csv(output / "local_grid_metrics.csv", metric_rows)
        write_csv(output / "metric_classification.csv", classifications)
        write_csv(output / "classification-delta.csv", deltas)
        write_csv(
            output / "rq6-reused-external-summary.csv",
            read_csv(RQ6_REUSED),
        )
        write_csv(output / "input-manifest.csv", input_manifest())
        analysis.plot_heatmaps(
            metric_rows, output / "figures/local-grid-heatmaps.png"
        )
        analysis.plot_classification(
            classifications, output / "figures/classification-cv.png"
        )

    class_counts = Counter(
        str(row["classification"]) for row in classifications
    )
    changed = [
        str(row["metric"])
        for row in deltas
        if bool(row["classification_changed"])
    ]
    path = next(
        row
        for row in classifications
        if row["metric"] == "path_locality_share"
    )
    summary = {
        "local_grid_rows": len(metric_rows),
        "metrics": len(classifications),
        "classification_counts": dict(sorted(class_counts.items())),
        "classification_changes": changed,
        "path_locality": {
            "classification": path["classification"],
            "eligible_cells": path["eligible_cells"],
            "cv": path["cv"],
            "direction_consistency": path["direction_consistency"],
            "leave_one_cell_out_invariant_stability": path[
                "leave_one_cell_out_invariant_stability"
            ],
            "external_status": path["external_status"],
        },
        "rq6_public_reused": True,
        "rq6_reused_sha256": sha256(RQ6_REUSED),
    }
    (output / "run-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=HERE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run(args.output_dir.resolve()), indent=2))


if __name__ == "__main__":
    main()
