#!/usr/bin/env python3
"""Fail-closed verification for the Step-0090 deterministic outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

import replay_measures as replay


EXP = Path(__file__).resolve().parent
REPO = EXP.parents[4]
R221 = REPO / "docs/visexp/out/r221-pprof-renderer-v1"
TOTAL_RE = re.compile(r"\bof ([0-9]+(?:\.[0-9]+)?)([A-Za-z]*) total\b")

PROFILES = {
    "git_time": {
        "stem": "git-multibranch.time",
        "input": "git-multibranch.time.jsonl",
        "expected_mass": 3982,
    },
    "file_read": {
        "stem": "selfprofile.file-read",
        "input": "selfprofile.file-read.jsonl",
        "expected_mass": 737,
    },
    "file_write": {
        "stem": "selfprofile.file-write",
        "input": "selfprofile.file-write.jsonl",
        "expected_mass": 31,
    },
    "network": {
        "stem": "selfprofile.network",
        "input": "selfprofile.network.jsonl",
        "expected_mass": 61,
    },
    "r114_system": {
        "stem": "r114.system-effects",
        "input": "r114.system-effects.jsonl",
        "expected_mass": 1520,
    },
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def stock_total(profile: Path) -> tuple[int, str]:
    completed = subprocess.run(
        ["go", "tool", "pprof", "-top", "-unit=minimum", str(profile)],
        check=True,
        text=True,
        capture_output=True,
    )
    match = TOTAL_RE.search(completed.stdout)
    if not match:
        raise ValueError(f"could not parse stock-pprof total for {profile.name}")
    value = float(match.group(1))
    if not value.is_integer():
        raise ValueError(f"noninteger stock-pprof total for {profile.name}: {value}")
    return int(value), match.group(2)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify() -> dict[str, Any]:
    prepared = json.loads((EXP / "prepared-measures.json").read_text(encoding="utf-8"))
    checks: dict[str, Any] = {}
    for name, spec in PROFILES.items():
        stem = spec["stem"]
        input_rows = replay.read_jsonl(EXP / spec["input"])
        input_mass = sum(row["value"] for row in input_rows)
        producer = json.loads((EXP / f"{stem}.stdout.json").read_text(encoding="utf-8"))
        profile = EXP / f"{stem}.pb.gz"
        second = EXP / f"{stem}.second.pb.gz"
        stock_mass, stock_unit = stock_total(profile)
        render = json.loads((EXP / f"{stem}.render.json").read_text(encoding="utf-8"))
        primary_sha = digest(profile)
        second_sha = digest(second)
        png = EXP / f"{stem}.png"
        external_png = R221 / f"{stem}.png"
        require(input_mass == spec["expected_mass"], f"{name}: input mass changed")
        require(producer["status"] == "ok", f"{name}: producer did not report ok")
        require(producer["warnings"] == [], f"{name}: producer warnings are nonempty")
        require(producer["samples"] == input_mass, f"{name}: producer mass delta")
        require(stock_mass == input_mass, f"{name}: stock pprof mass delta")
        require(
            render["source"]["selected_weight"] == input_mass,
            f"{name}: renderer pprof mass delta",
        )
        require(primary_sha == second_sha, f"{name}: deterministic bytes differ")
        require(png.stat().st_size > 0, f"{name}: local PNG missing/empty")
        require(external_png.stat().st_size > 0, f"{name}: external PNG missing/empty")
        checks[name] = {
            "rows": len(input_rows),
            "input_mass": input_mass,
            "producer_mass": producer["samples"],
            "stock_pprof_mass": stock_mass,
            "stock_pprof_output_unit": stock_unit,
            "rendered_mass": render["source"]["selected_weight"],
            "sha256": primary_sha,
            "second_sha256": second_sha,
            "byte_deterministic": primary_sha == second_sha,
            "png_bytes": png.stat().st_size,
            "external_png_bytes": external_png.stat().st_size,
            "conservation_delta": stock_mass - input_mass,
        }

    fixed_git = replay.read_jsonl(
        REPO
        / ".agentsight/experiments/rq1-matched-organization-v1/full/"
        "operations-count.jsonl"
    )
    timed_git = replay.read_jsonl(EXP / "git-multibranch.time.jsonl")
    require(len(fixed_git) == len(timed_git) == 489, "Git row cardinality changed")
    require(
        [row["fields"] for row in fixed_git] == [row["fields"] for row in timed_git],
        "Git factual fields or evidence order changed",
    )
    hierarchy = prepared["git_time"]["hierarchy_check"]
    require(hierarchy["exact_match"], "Git hierarchy check failed")
    require(hierarchy["rows"] == 489, "Git hierarchy row count changed")

    created_rows = [
        row
        for row in replay.read_jsonl(EXP / "selfprofile.file-write.jsonl")
        if row["fields"]["disposition"] == "created"
    ]
    require(len(created_rows) == 2, "successful retained Add File target count changed")
    require(
        all(row["fields"]["status"] == "ok" for row in created_rows),
        "created target lacks successful tool status",
    )
    require(
        all(row["fields"]["target"] not in {"", "unknown"} for row in created_rows),
        "created target is not exact",
    )

    network_status = prepared["step0086_effects"]["network_status_counts"]
    require(network_status == {"ok": 55}, "network status population changed")
    require(
        prepared["network_failure_correlation"]["available"] is False,
        "unexpected network-failure population",
    )

    original_r114 = replay.read_jsonl(
        REPO
        / ".agentsight/experiments/rq1-r114-current-profile-v1/full/profile/"
        "scoped-lineage-operations.jsonl"
    )
    projected_r114 = replay.read_jsonl(EXP / "r114.system-effects.jsonl")
    require(len(original_r114) == len(projected_r114) == 1520, "R114 rows changed")
    for original, projected in zip(original_r114, projected_r114):
        require(original["value"] == projected["value"], "R114 value changed")
        require(
            all(projected["fields"].get(key) == value for key, value in original["fields"].items()),
            "R114 factual field changed",
        )
    failure = prepared["r114_system_effects"]["failure_retry"]
    require(failure["false_negatives"] == 1, "R114 failure-task FN changed")
    require(
        failure["expected_python3_effect_retained"] is False,
        "unexpected retained python3 failure event",
    )

    return {
        "schema_version": 1,
        "status": "pass",
        "generated_at": "1970-01-01T00:00:00Z",
        "profiles": checks,
        "git_evidence_rows": 489,
        "git_factual_fields_and_order_unchanged": True,
        "git_hierarchy": hierarchy,
        "created_file_targets": [row["fields"] for row in created_rows],
        "network_status_counts": network_status,
        "network_failure_correlation_available": False,
        "r114_rows_preserved": 1520,
        "r114_failure_retry_false_negatives": failure["false_negatives"],
        "r114_failure_python3_effect_retained": False,
    }


if __name__ == "__main__":
    result = verify()
    replay.write_json(EXP / "profile-checks.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))
