#!/usr/bin/env python3
"""Summarize skill labels from standard pprof profiles."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SAMPLE_RE = re.compile(r"^\s*(-?\d+):\s*(.*)$")
LABEL_RE = re.compile(r"([A-Za-z0-9_]+):\[([^\]]*)\]")
LOCATION_RE = re.compile(r"^\s*(\d+):.* M=\d+ (.*) agentpprof:\d+")


def raw_samples(profile: Path) -> list[tuple[int, dict[str, str], list[str]]]:
    result = subprocess.run(
        ["go", "tool", "pprof", "-raw", str(profile)],
        check=True,
        capture_output=True,
        text=True,
    )
    raw_rows: list[tuple[int, dict[str, str], list[int]]] = []
    pending_value: int | None = None
    pending_locations: list[int] = []
    in_samples = False
    lines = result.stdout.splitlines()
    for line in lines:
        if line == "Samples:":
            in_samples = True
            continue
        if not in_samples:
            continue
        if line.startswith("Locations"):
            break
        match = SAMPLE_RE.match(line)
        if match:
            pending_value = int(match.group(1))
            pending_locations = [
                int(value) for value in match.group(2).split() if value.isdigit()
            ]
            continue
        if pending_value is None:
            continue
        labels = dict(LABEL_RE.findall(line))
        if labels:
            raw_rows.append((pending_value, labels, pending_locations))
            pending_value = None
            pending_locations = []
    locations = {
        int(match.group(1)): match.group(2)
        for line in lines
        if (match := LOCATION_RE.match(line))
    }
    return [
        (
            value,
            labels,
            [locations[location] for location in location_ids if location in locations],
        )
        for value, labels, location_ids in raw_rows
    ]


def percent(value: int, total: int) -> float:
    return round(100.0 * value / total, 6) if total else 0.0


def summarize_profile(profile: Path) -> dict[str, Any]:
    samples = raw_samples(profile)
    by_skill: Counter[str] = Counter()
    by_skill_session: dict[str, Counter[str]] = defaultdict(Counter)
    by_skill_evidence: dict[str, Counter[str]] = defaultdict(Counter)
    session_named: dict[str, Counter[str]] = defaultdict(Counter)
    pprof_total = 0
    for value, labels, frames in samples:
        pprof_total += value
        skill = labels.get("skill", "")
        source_session = labels.get("source_session", "unknown")
        by_skill[skill] += value
        by_skill_session[skill][source_session] += value
        for frame in frames:
            if frame.startswith(("call:", "prompt:", "token:", "tool:")):
                by_skill_evidence[skill][frame] += value
        if skill and skill != "unscoped":
            session_named[source_session][skill] += value

    named_total = sum(
        value for skill, value in by_skill.items() if skill and skill != "unscoped"
    )
    top_rows: list[dict[str, Any]] = []
    for skill, value in sorted(
        (
            (skill, value)
            for skill, value in by_skill.items()
            if skill and skill != "unscoped"
        ),
        key=lambda item: (-item[1], item[0]),
    ):
        sessions = by_skill_session[skill]
        max_session, max_value = max(
            sessions.items(), key=lambda item: (item[1], item[0])
        )
        ranks = Counter()
        for source_session, skill_value in sessions.items():
            rank = 1 + sum(
                candidate_value > skill_value
                for candidate_value in session_named[source_session].values()
            )
            ranks[rank] += 1
        top_rows.append(
            {
                "skill": skill,
                "value": value,
                "overall_percent": percent(value, pprof_total),
                "named_percent": percent(value, named_total),
                "sessions": len(sessions),
                "max_single_session_value": max_value,
                "max_single_session_share_percent": percent(max_value, value),
                "max_single_session_id": max_session,
                "session_rank_distribution": {
                    str(rank): count for rank, count in sorted(ranks.items())
                },
                "evidence_breakdown": dict(
                    sorted(
                        by_skill_evidence[skill].items(),
                        key=lambda item: (-item[1], item[0]),
                    )
                ),
            }
        )

    return {
        "pprof_total": pprof_total,
        "pprof_samples": len(samples),
        "named_total": named_total,
        "unscoped_total": by_skill.get("unscoped", 0),
        "named_coverage_percent": percent(named_total, pprof_total),
        "skills": len(top_rows),
        "top_skills": top_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tokens-profile", required=True, type=Path)
    parser.add_argument("--operations-profile", required=True, type=Path)
    parser.add_argument("--tokens-run", required=True, type=Path)
    parser.add_argument("--operations-run", required=True, type=Path)
    parser.add_argument("--source-oracle", required=True, type=Path)
    args = parser.parse_args()

    token_run = json.loads(args.tokens_run.read_text())
    operation_run = json.loads(args.operations_run.read_text())
    oracle = json.loads(args.source_oracle.read_text())
    tokens = summarize_profile(args.tokens_profile)
    operations = summarize_profile(args.operations_profile)

    token_totals = {
        "raw_unique_source": oracle["raw_token_total"],
        "parsed_source": token_run["source_samples_before_filters"],
        "folded": token_run["samples"],
        "pprof": tokens["pprof_total"],
    }
    operation_totals = {
        "raw_unique_source": oracle["raw_operation_total"],
        "parsed_source": operation_run["source_samples_before_filters"],
        "folded": operation_run["samples"],
        "pprof": operations["pprof_total"],
    }
    output = {
        "corpus": {
            "requested_files": oracle["requested_files"],
            "readable_files": oracle["readable_files"],
            "parseable_sessions": oracle["parseable_sessions"],
            "excluded_files": oracle["excluded_files"],
            "skill_sessions": oracle["sessions_with_exact_skill_invocation"],
            "distinct_skills": oracle["distinct_skills"],
            "skill_invocations": oracle["exact_skill_invocations"],
            "distinct_recorded_cwds": oracle["distinct_recorded_cwds"],
            "raw_prompt_records": oracle["raw_prompt_records"],
            "raw_tool_invocations": oracle["raw_tool_invocations"],
            "raw_llm_rows_before_dedup": oracle[
                "raw_llm_rows_before_dedup"
            ],
            "raw_unique_llm_completions": oracle[
                "raw_unique_llm_completions"
            ],
            "deduplicated_llm_fragments": oracle[
                "deduplicated_llm_fragments"
            ],
            "llm_rows_without_stable_source_id": oracle[
                "llm_rows_without_stable_source_id"
            ],
            "skill_invocations_by_name": oracle["skill_invocations"],
        },
        "conservation": {
            "tokens": {
                **token_totals,
                "all_equal": len(set(token_totals.values())) == 1,
            },
            "operations": {
                **operation_totals,
                "all_equal": len(set(operation_totals.values())) == 1,
            },
        },
        "tokens": tokens,
        "operations": operations,
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
