#!/usr/bin/env python3
"""Selective old/new checks for projection-dependent supplementary metrics.

This intentionally does not regenerate the RQ7, user-question, or
session-dynamics artifact bundles.  It evaluates only the identity-dependent
headline estimands needed to decide whether those bundles need a later full
recompute.
"""

from __future__ import annotations

import csv
import gc
import gzip
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[5]
BUILD = REPO / "docs/tmp/build-and-evaluate"
OLD = BUILD / "rq1-rq4-recompute-final/rq1-raw"
NEW = BUILD / "rq1-rq4-recompute-v2-20260727/rq1-raw"
OUTPUT = NEW.parent / "sensitivity-spotcheck.json"
MUTATION_ACCESSES = {"write", "create", "delete", "rename", "rename_from"}


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def event_files(root: Path) -> list[Path]:
    paths = sorted((root / "events").glob("*.json.gz"))
    if len(paths) != 6:
        raise RuntimeError(f"expected six event files below {root}, found {len(paths)}")
    return paths


def load_event_payload(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def event_sort_key(event: dict[str, Any]) -> tuple[int, int, str]:
    return (
        int(event.get("ts_ms") or 0),
        int(event.get("source_tool_ordinal") or 0),
        str(event.get("id") or ""),
    )


def rq7_repeated_reads(root: Path, behavior: Any) -> dict[str, Any]:
    streams: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    shell_calls = 0
    native_read_edit_write = 0
    calls = 0
    for path in event_files(root):
        payload = load_event_payload(path)
        project = str(payload["repository"])
        for event in payload["events"]:
            calls += 1
            family = behavior.tool_family(event)
            shell_calls += family == "shell"
            native_read_edit_write += family in {"read", "edit", "write"}
            streams[(project, str(event["source_stream_id"]))].append(event)

    totals = Counter()
    for group in streams.values():
        group.sort(key=event_sort_key)
        segments: list[list[dict[str, Any]]] = []
        for event in group:
            if (
                not segments
                or segments[-1][-1].get("prompt_index") != event.get("prompt_index")
            ):
                segments.append([event])
            else:
                segments[-1].append(event)
        for segment in segments:
            seen_read: dict[tuple[str, str], tuple[int, tuple[int, int]]] = {}
            last_mutation: dict[tuple[str, str], tuple[int, int]] = {}
            identity_counts: Counter[tuple[str, str]] = Counter()
            for event_idx, event in enumerate(segment):
                records = sorted(
                    event.get("actions") or [],
                    key=lambda item: int(item.get("action_ordinal") or 0),
                )
                for record_idx, record in enumerate(records):
                    identity = record.get("artifact_id") or record.get("path")
                    if not identity:
                        continue
                    key = (
                        str(
                            record.get("worktree_id")
                            or event.get("worktree_id")
                            or ""
                        ),
                        str(identity),
                    )
                    position = (event_idx, record_idx)
                    access = str(record.get("access") or "")
                    if access == "read":
                        identity_counts[key] += 1
                        totals["read_instances"] += 1
                        if key in seen_read:
                            _previous_event, previous_position = seen_read[key]
                            totals["repeat_read_instances"] += 1
                            if last_mutation.get(key, (-1, -1)) <= previous_position:
                                totals["unchanged_repeat_instances"] += 1
                        seen_read[key] = (event_idx, position)
                    elif access in MUTATION_ACCESSES:
                        last_mutation[key] = position
            totals["group_identity_units"] += len(identity_counts)
            totals["repeated_group_identity_units"] += sum(
                count >= 2 for count in identity_counts.values()
            )
    result = dict(totals)
    result.update(
        {
            "calls": calls,
            "shell_calls": shell_calls,
            "native_read_edit_write_calls": native_read_edit_write,
            "repeat_read_share": (
                totals["repeat_read_instances"] / totals["read_instances"]
            ),
            "unchanged_share_among_repeats": (
                totals["unchanged_repeat_instances"]
                / totals["repeat_read_instances"]
            ),
        }
    )
    return result


def rq7_prefetch(root: Path, profile: Any) -> dict[str, Any]:
    calls, _corpus, _duplicates = profile.load_projected(root / "events")
    rows = profile.prefetch_profile(profile.build_episodes(calls))
    selected = [
        row
        for row in rows
        if row["project"] == "all"
        and row["split"] == "chronological_80_20_actionable"
        and row["context"] == "op_target"
        and row["top_k"] == 1
        and float(row["policy_threshold"]) == 0.25
    ]
    if len(selected) != 1:
        raise RuntimeError(f"unexpected actionable-prefetch rows: {len(selected)}")
    row = selected[0]
    return {
        key: row[key]
        for key in (
            "train_transitions",
            "test_transitions",
            "eligible_next_reads",
            "contexts_seen",
            "prefetches_issued",
            "exact_path_hits",
            "precision_per_prefetch",
        )
    }


def selected_user_questions(root: Path, questions: Any) -> dict[str, Any]:
    projects = read_json(root / "projects.json")
    artifacts = read_csv(root / "rq1-artifacts.csv")
    mutations = read_csv(root / "rq1-mutations.csv")
    _details, artifact_summary = questions.artifact_analysis(artifacts)
    allocation, comparisons, _checks, metadata, _audit = questions.action_allocation(
        root, projects
    )
    def one(rows: list[dict[str, Any]], **terms: Any) -> dict[str, Any]:
        matches = [
            row for row in rows if all(row.get(key) == value for key, value in terms.items())
        ]
        if len(matches) != 1:
            raise RuntimeError(f"expected one row for {terms}, found {len(matches)}")
        return matches[0]

    created_docs = one(
        artifact_summary, project="ALL_POOLED", artifact_type="paper/docs"
    )
    created_code = one(artifact_summary, project="ALL_POOLED", artifact_type="code")
    ok_read = one(
        comparisons,
        status_basis="ok_only",
        project="ALL_POOLED",
        action_mode="read",
    )
    ok_write = one(
        comparisons,
        status_basis="ok_only",
        project="ALL_POOLED",
        action_mode="write",
    )
    observed_write = one(
        comparisons,
        status_basis="ok_plus_observed",
        project="ALL_POOLED",
        action_mode="write",
    )
    result = {
        "artifacts": len(artifacts),
        "mutation_rows": len(mutations),
        "created_docs": {
            key: created_docs[key]
            for key in (
                "created_artifacts",
                "never_revisited_artifacts",
                "never_revisited_fraction",
                "later_read_artifacts",
                "later_read_fraction",
            )
        },
        "created_code": {
            key: created_code[key]
            for key in (
                "created_artifacts",
                "never_revisited_artifacts",
                "never_revisited_fraction",
                "later_read_artifacts",
                "later_read_fraction",
            )
        },
        "ok_read": {
            key: ok_read[key]
            for key in (
                "paper_docs_actions",
                "code_actions",
                "paper_docs_share",
                "code_share",
            )
        },
        "ok_write": {
            key: ok_write[key]
            for key in (
                "paper_docs_actions",
                "code_actions",
                "paper_docs_share",
                "code_share",
            )
        },
        "ok_observed_write": {
            key: observed_write[key]
            for key in (
                "paper_docs_actions",
                "code_actions",
                "paper_docs_share",
                "code_share",
            )
        },
    }
    try:
        episodes = questions.collapse_mutations(mutations, metadata)
    except ValueError as exc:
        result["requires_full_recompute"] = True
        result["blocked_identity_contract"] = str(exc)
        return result

    _order_details, order_summary = questions.test_code_order_analysis(episodes)
    churn = questions.churn_analysis(episodes)
    _paired_details, paired_summary = questions.paired_churn_analysis(episodes)
    order = one(order_summary, project="ALL_POOLED")
    test_churn = one(churn, project="ALL_POOLED", artifact_type="test")
    code_churn = one(churn, project="ALL_POOLED", artifact_type="code")
    paired = one(paired_summary, project="ALL_POOLED")
    result.update(
        {
            "mutation_episodes": len(episodes),
            "source_test_order": {
            key: order[key]
            for key in (
                "eligible_paired_episodes",
                "basename_pair_episodes",
                "same_event_module_fallback_episodes",
                "test_first",
                "code_first",
                "tied_same_tool_event",
            )
            },
            "test_churn": {
            key: test_churn[key]
            for key in (
                "mutated_artifacts",
                "mutation_episodes",
                "repeat_episode_fraction",
                "validation_association_fraction",
            )
            },
            "code_churn": {
            key: code_churn[key]
            for key in (
                "mutated_artifacts",
                "mutation_episodes",
                "repeat_episode_fraction",
                "validation_association_fraction",
            )
            },
            "paired_churn": {
            key: paired[key]
            for key in (
                "test_bearing_blocks",
                "code_zero_blocks",
                "repeat_test_blocks",
                "repeat_test_code_zero_blocks",
                "repeat_test_gt_code_blocks",
            )
            },
        }
    )
    return result


def selected_session_dynamics(root: Path, session: Any) -> dict[str, Any]:
    session.DATA = root / "events"
    corpus = session.load_corpus()
    metadata = session.session_metadata(corpus)
    drift = session.analyze_drift(corpus)
    startup = session.analyze_startup(corpus, metadata)
    bookkeeping = session.analyze_bookkeeping(corpus)
    failures = session.analyze_failures(corpus)

    paired = drift["paired_quantiles"]
    reread = paired[
        (paired.metric == "repeat_read_share_late_minus_early") & (paired.n >= 10)
    ]
    noncomposite = drift["paired_noncomposite_8h_quantiles"]
    reread_noncomposite = noncomposite[
        (noncomposite.metric == "repeat_read_share_late_minus_early")
        & (noncomposite.n >= 10)
    ]
    primary = startup["sessions"]
    primary = primary[(primary.n_prefix == 10) & primary.complete_prefix]
    call_frame = bookkeeping["calls"]
    access_frame = bookkeeping["accesses"]
    book_writes = access_frame[
        (access_frame.strict_class == "bookkeeping")
        & access_frame.is_write
        & access_frame.primary_access
    ]
    ordinary_writes = access_frame[
        (access_frame.strict_class == "ordinary")
        & access_frame.is_write
        & access_frame.project_path
        & access_frame.primary_access
    ]
    chains = failures["chains"]
    result = {
        "long_roots": int(
            drift["curve"][["project", "session_id"]].drop_duplicates().shape[0]
        ),
        "qualified_reread_delta": [
            {
                "project": str(row.project),
                "vendor": str(row.vendor),
                "n": int(row.n),
                "median": float(row.median),
            }
            for row in reread.itertuples(index=False)
        ],
        "qualified_noncomposite_reread_delta": [
            {
                "project": str(row.project),
                "vendor": str(row.vendor),
                "n": int(row.n),
                "median": float(row.median),
            }
            for row in reread_noncomposite.itertuples(index=False)
        ],
        "startup": {
            "complete_10_call_roots": int(len(primary)),
            "with_predecessor": int(primary.predecessor_available.sum()),
            "narrow_median": float(primary.narrow_share.median()),
            "narrow_q25": float(primary.narrow_share.quantile(0.25)),
            "narrow_q75": float(primary.narrow_share.quantile(0.75)),
            "extended_median": float(primary.extended_share.median()),
            "extended_q25": float(primary.extended_share.quantile(0.25)),
            "extended_q75": float(primary.extended_share.quantile(0.75)),
            "extended_p90": float(primary.extended_share.quantile(0.9)),
        },
        "bookkeeping": {
            "strict_gross_calls": int(call_frame.control_plane_strict.sum()),
            "strict_gross_share": float(call_frame.control_plane_strict.mean()),
            "strict_exclusive_share": float(
                call_frame.exclusive_bookkeeping_strict.mean()
            ),
            "broad_gross_share": float(call_frame.control_plane_broad.mean()),
            "bookkeeping_h50_opportunities": int(
                book_writes.h50_opportunity.sum()
            ),
            "bookkeeping_h50_revisit_share": float(
                book_writes[
                    book_writes.h50_opportunity
                ].read_within_50.mean()
            ),
            "ordinary_h50_opportunities": int(
                ordinary_writes.h50_opportunity.sum()
            ),
            "ordinary_h50_revisit_share": float(
                ordinary_writes[
                    ordinary_writes.h50_opportunity
                ].read_within_50.mean()
            ),
        },
        "failure_chains": {
            "chains": int(len(chains)),
            "member_calls": int(chains.length.sum()) if len(chains) else 0,
        },
    }
    del failures, bookkeeping, startup, drift, metadata, corpus
    gc.collect()
    return result


def main() -> None:
    behavior = load_module(
        "behavior_spotcheck",
        BUILD / "toolcall-behavior-20260726/analyze_toolcalls.py",
    )
    profile = load_module(
        "profile_spotcheck",
        BUILD / "toolcall-profile-20260726/analyze_toolcalls.py",
    )
    questions = load_module(
        "questions_spotcheck",
        BUILD / "user-questions-20260726/analyze_user_questions.py",
    )
    session = load_module(
        "session_spotcheck",
        BUILD / "session-dynamics-20260726/analysis.py",
    )
    results: dict[str, Any] = {"old": {}, "new": {}}
    for label, root in (("old", OLD), ("new", NEW)):
        results[label]["rq7_repeated_reads"] = rq7_repeated_reads(root, behavior)
        results[label]["rq7_prefetch"] = rq7_prefetch(root, profile)
        results[label]["user_questions"] = selected_user_questions(root, questions)
        results[label]["session_dynamics"] = selected_session_dynamics(root, session)
    with OUTPUT.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
