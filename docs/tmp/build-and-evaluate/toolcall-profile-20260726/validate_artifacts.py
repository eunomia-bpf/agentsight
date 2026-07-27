#!/usr/bin/env python3
"""Validate frozen tool-call profile artifacts and write a hash manifest."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def overall(name: str) -> dict[str, str]:
    return next(row for row in csv_rows(name) if row.get("project") == "all")


def main() -> None:
    metadata = json.loads((ROOT / "metadata.json").read_text(encoding="utf-8"))
    reproducibility = metadata["reproducibility"]
    assert sha256(ROOT / "analyze_toolcalls.py") == reproducibility["script_sha256"]
    for entry in reproducibility["input_manifest"]:
        assert sha256(Path(entry["path"])) == entry["sha256"]
    for name, expected in reproducibility["csv_sha256"].items():
        assert sha256(ROOT / name) == expected

    corpus = overall("corpus_summary.csv")
    timeline = overall("timeline_profile.csv")
    ilp = overall("ilp_profile.csv")
    polling = next(
        row
        for row in csv_rows("polling.csv")
        if row["project"] == "all" and row["wait_tool"] == "__ALL_WAIT_TOOLS__"
    )
    speculation = overall("speculation.csv")
    assert int(corpus["projected_calls"]) == 180_764
    assert int(timeline["tool_busy_union_ms"]) + int(
        timeline["between_tool_model_gap_ms"]
    ) == int(timeline["within_episode_span_ms"])
    assert (
        int(ilp["already_concurrent_adjacent_edges"])
        + int(ilp["already_batched_disjoint_adjacent_edges"])
        + int(ilp["remaining_sequential_disjoint_adjacent_edges"])
        == int(ilp["parallel_candidate_adjacent_edges"])
    )
    assert int(polling["event_driven_calls_saved_upper"]) == 1_456
    assert int(speculation["last_test_command_predictor_hits"]) == 718

    report = (ROOT / "report.md").read_text(encoding="utf-8")
    required_anchors = (
        "180,764",
        "42,679",
        "1,801",
        "5,132",
        "1,456",
        "2,911",
        "633",
        "126",
        "94",
        "6.93×",
    )
    missing = [anchor for anchor in required_anchors if anchor not in report]
    assert not missing, f"report missing final CSV anchors: {missing}"

    artifact_names = sorted(
        path.name
        for path in ROOT.iterdir()
        if path.is_file() and path.name != "artifact-manifest.json"
    )
    manifest = {
        "validated": True,
        "files": {
            name: {"size_bytes": (ROOT / name).stat().st_size, "sha256": sha256(ROOT / name)}
            for name in artifact_names
        },
        "checks": {
            "analysis_script_matches_metadata": True,
            "input_files_match_metadata": True,
            "csv_files_match_metadata": True,
            "timeline_arithmetic": True,
            "parallel_split_arithmetic": True,
            "report_contains_final_metric_anchors": True,
        },
    }
    path = ROOT / "artifact-manifest.json"
    temp = path.with_suffix(".json.tmp")
    temp.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temp, path)
    print(f"validated {len(artifact_names)} artifacts; wrote {path.name}")


if __name__ == "__main__":
    main()
