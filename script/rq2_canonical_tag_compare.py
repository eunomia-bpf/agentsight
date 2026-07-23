#!/usr/bin/env python3
"""Prepare and compare one deterministic short-tag RQ2 candidate.

``prepare`` reads only the existing sparse annotation files.  It maps every
open-vocabulary operation name through the fixed lexical rules below and
writes structurally identical annotations.  It never opens benchmark targets,
signals, packets, or result files.

``score`` runs only after the ordinary RQ2 evaluator has produced per-query
rows.  It recomputes MAP from those rows and performs the workload's registered
paired cluster bootstrap for the candidate-minus-current and
candidate-minus-native contrasts.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import random
import re
import statistics
from typing import Any, Iterable, Mapping, Sequence


WORKLOADS = ("agentprocess", "hint", "trace")
ALGORITHM = "action-object-lexicon-v1"
BOOTSTRAPS = {
    "agentprocess": (10_000, 20260716),
    "hint": (100_000, 20260722),
    "trace": (100_000, 20260713),
}

# Ordered, shared across all workloads, and intentionally independent of task
# IDs, benchmark names, tools, repositories, files, models, or outcomes.
VERB_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("repeat", ("repeat", "retry", "revisit")),
    ("recover", ("recover", "undo", "rollback")),
    ("understand", ("understand", "frame", "clarify")),
    ("plan", ("plan", "choose", "select", "prepare", "organize")),
    ("search", ("search", "lookup", "look up", "browse")),
    ("locate", ("locate", "find", "identify")),
    ("navigate", ("navigate", "open", "visit")),
    ("extract", ("extract", "capture", "parse")),
    ("compare", ("compare", "contrast", "rank")),
    ("compute", ("compute", "calculate", "derive")),
    ("diagnose", ("diagnose", "investigate", "debug", "assess")),
    ("reproduce", ("reproduce", "replicate")),
    ("test", ("test", "tests", "testing", "exercise")),
    ("edit", ("edit", "modify", "change", "implement", "apply", "patch")),
    ("build", ("build", "compile", "assemble")),
    ("configure", ("configure", "setup", "set up")),
    ("verify", ("verify", "check", "confirm")),
    ("validate", ("validate", "evaluate")),
    ("coordinate", ("coordinate", "delegate", "schedule")),
    ("authenticate", ("authenticate", "authorize")),
    ("update", ("update", "refresh")),
    ("create", ("create", "add", "write")),
    ("remove", ("remove", "delete", "clean", "archive")),
    ("deploy", ("deploy", "publish")),
    ("submit", ("submit", "reserve", "book")),
    ("escalate", ("escalate",)),
    ("communicate", ("communicate", "send", "broadcast", "notify")),
    ("report", ("report", "answer", "deliver", "present", "state", "summarize", "conclude")),
    ("resolve", ("resolve", "repair", "solve", "contain", "enforce")),
    ("collect", ("collect", "gather", "acquire")),
    ("read", ("read",)),
    ("inspect", ("inspect", "review", "analyze", "explore")),
    ("execute", ("execute", "run", "operate", "process", "manage", "complete", "continue", "use")),
)

OBJECT_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("completion", ("completion", "final answer", "final response", "conclusion")),
    ("failure", ("failure", "failed", "stalled", "error", "incident", "regression", "issue")),
    ("hypothesis", ("hypothesis", "claim", "question", "unknown")),
    ("evidence", ("evidence", "fact", "source", "citation", "web content")),
    ("request", ("request", "support", "assigned task", "user need")),
    ("workflow", ("workflow", "process", "campaign", "operations")),
    ("interaction", ("interaction", "conversation", "discussion", "message", "email", "notification")),
    ("record", ("record", "history", "document", "note", "thread", "calendar")),
    ("artifact", ("artifact", "file", "workspace", "repository", "codebase", "implementation", "reproducer")),
    ("interface", ("interface", "website", "page", "screen", "menu")),
    ("target", ("target", "candidate", "lookup")),
    ("result", ("result", "outcome", "answer", "response", "repair")),
    ("condition", ("condition", "state", "prerequisite", "status", "balance")),
    ("data", ("data", "input", "metric", "price", "rating", "weather", "content", "analytics")),
    ("user", ("user", "customer", "people", "candidate")),
    ("resource", ("resource", "service", "transaction", "order", "vehicle", "hotel", "restaurant")),
    ("deployment", ("deployment", "release")),
    ("change", ("change", "fix", "patch")),
    ("action", ("action", "operation", "command", "tool", "step", "approach", "option")),
    ("work", ("work", "task", "analysis", "investigation")),
)

QUALIFIER_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("external", ("external", "web", "remote")),
    ("local", ("local", "workspace", "repository")),
    ("alternate", ("alternate", "candidate", "tentative")),
)

CONTENT_STOPWORDS = {
    "a",
    "all",
    "an",
    "and",
    "assigned",
    "available",
    "current",
    "for",
    "from",
    "in",
    "into",
    "of",
    "or",
    "over",
    "relevant",
    "same",
    "specific",
    "task",
    "the",
    "through",
    "to",
    "with",
}

CONTENT_ALIASES = {
    "accounts": "account",
    "addresses": "address",
    "alerts": "alert",
    "analytics": "data",
    "applications": "application",
    "artifacts": "artifact",
    "candidates": "candidate",
    "certificates": "certificate",
    "channels": "channel",
    "companies": "provider",
    "credentials": "credential",
    "documents": "document",
    "files": "file",
    "github": "repository",
    "git": "repository",
    "hotels": "hotel",
    "ipaddresses": "address",
    "ips": "address",
    "messages": "message",
    "operations": "operation",
    "options": "option",
    "policies": "policy",
    "prices": "price",
    "records": "record",
    "repositories": "repository",
    "resources": "resource",
    "restaurants": "restaurant",
    "reviews": "review",
    "risks": "risk",
    "slack": "collaboration",
    "tests": "test",
    "tools": "tool",
    "users": "user",
    "workflows": "workflow",
}


class ExperimentError(RuntimeError):
    """A deterministic input or comparison failure."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ExperimentError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            require(isinstance(value, dict), f"{path}:{line_number}: expected object")
            rows.append(value)
    return rows


def normalized_words(value: str) -> str:
    value = value.casefold().replace("_", " ").replace("-", " ")
    return " ".join(re.findall(r"[a-z0-9]+", value))


def matches(text: str, phrase: str) -> bool:
    normalized = normalized_words(phrase)
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])", text))


def choose_rule(
    text: str, rules: Sequence[tuple[str, Sequence[str]]], fallback: str
) -> str:
    for output, phrases in rules:
        if any(matches(text, phrase) for phrase in phrases):
            return output
    return fallback


def canonicalize_tag(value: str) -> str:
    """Map one old name to a reusable one-to-three-word operation tag."""
    text = normalized_words(value)
    require(bool(text), "blank operation tag")
    verb = choose_rule(text, VERB_RULES, "execute")
    obj = choose_rule(text, OBJECT_RULES, "work")

    # Completion language attached to a workflow is execution, while language
    # that presents a result is reporting.  This disambiguation is lexical and
    # shared; it does not inspect an occurrence's position or outcome.
    if verb == "execute" and matches(text, "complete") and obj == "completion":
        verb, obj = "report", "completion"
    if verb == "report" and obj == "workflow":
        obj = "completion"

    tag = f"{verb} {obj}"
    qualifier = choose_rule(text, QUALIFIER_RULES, "")
    if qualifier and qualifier not in {verb, obj}:
        tag = f"{tag} {qualifier}"
    words = tag.split()
    require(1 <= len(words) <= 3, f"invalid canonical tag: {tag!r}")
    return tag


def specific_canonicalize_tag(value: str) -> str:
    """Use old-name head nouns to preserve a boundary the base map collides."""
    text = normalized_words(value)
    verb = canonicalize_tag(value).split()[0]
    action_words = {
        token
        for _output, phrases in VERB_RULES
        for phrase in phrases
        for token in normalized_words(phrase).split()
    }
    content = []
    for token in text.split():
        if token in CONTENT_STOPWORDS or token in action_words or token.isdigit():
            continue
        normalized = CONTENT_ALIASES.get(token, token)
        if normalized not in content and normalized != verb:
            content.append(normalized)
    if not content:
        return canonicalize_tag(value)
    objects = content if len(content) == 1 else [content[0], content[-1]]
    return " ".join([verb, *objects])


def collision_refinements(
    payloads: Mapping[tuple[str, str], Mapping[str, Any]],
    mapping: Mapping[str, str],
) -> tuple[set[str], int]:
    refinements: set[str] = set()
    collisions = 0
    for payload in payloads.values():
        for session in payload["sessions"]:
            previous_old: tuple[str, ...] | None = None
            previous_new: tuple[str, ...] | None = None
            for mark in session["marks"]:
                old = tuple(str(tag) for tag in mark["semantic_path"])
                new = tuple(mapping[tag] for tag in old)
                if new == previous_new:
                    collisions += 1
                    require(previous_old is not None, "missing previous path")
                    for left, right in zip(previous_old, old, strict=True):
                        if left != right and mapping[left] == mapping[right]:
                            refinements.update((left, right))
                previous_old, previous_new = old, new
    return refinements, collisions


def annotation_files(path: Path) -> list[Path]:
    files = sorted(path.glob("batch-*.json"))
    require(bool(files), f"no annotation files under {path}")
    return files


def transformed_payload(
    payload: Mapping[str, Any], mapping: Mapping[str, str], source: Path
) -> dict[str, Any]:
    require(set(payload) == {"batch", "sessions"}, f"{source}: top-level keys")
    sessions = []
    for session in payload["sessions"]:
        require(
            isinstance(session, dict) and {"sequence", "marks"} <= set(session),
            f"{source}: session keys",
        )
        marks = []
        previous: tuple[str, ...] | None = None
        for mark in session["marks"]:
            require(
                set(mark) == {"start_operation_id", "semantic_path"},
                f"{source}: mark keys",
            )
            old_path = mark["semantic_path"]
            require(isinstance(old_path, list) and old_path, f"{source}: path")
            new_path = tuple(mapping[str(tag)] for tag in old_path)
            require(
                new_path != previous,
                f"{session['sequence']}: adjacent paths collide after canonicalization",
            )
            previous = new_path
            marks.append(
                {
                    "start_operation_id": mark["start_operation_id"],
                    "semantic_path": list(new_path),
                }
            )
        sessions.append({**session, "marks": marks})
    return {"batch": payload["batch"], "sessions": sessions}


def prepare(current_root: Path, out: Path, mapping_out: Path) -> dict[str, Any]:
    payloads: dict[tuple[str, str], Mapping[str, Any]] = {}
    old_tags: set[str] = set()
    input_counts: dict[str, dict[str, int]] = {}
    for workload in WORKLOADS:
        source_dir = current_root / workload / "annotations"
        sessions = marks = 0
        for path in annotation_files(source_dir):
            payload = read_json(path)
            payloads[(workload, path.name)] = payload
            sessions += len(payload["sessions"])
            for session in payload["sessions"]:
                marks += len(session["marks"])
                for mark in session["marks"]:
                    for tag in mark["semantic_path"]:
                        require(isinstance(tag, str), f"{path}: non-string tag")
                        old_tags.add(tag)
        input_counts[workload] = {"sessions": sessions, "marks": marks}

    mapping = {tag: canonicalize_tag(tag) for tag in sorted(old_tags)}
    refinements, initial_collisions = collision_refinements(payloads, mapping)
    for tag in refinements:
        mapping[tag] = specific_canonicalize_tag(tag)
    unresolved, remaining_collisions = collision_refinements(payloads, mapping)
    require(
        remaining_collisions == 0,
        "canonicalization still has adjacent path collisions after deterministic "
        f"head-noun refinement: {sorted(unresolved)[:8]}",
    )
    output_counts: dict[str, dict[str, int]] = {}
    for workload in WORKLOADS:
        sessions = marks = 0
        for (item_workload, name), payload in sorted(payloads.items()):
            if item_workload != workload:
                continue
            transformed = transformed_payload(
                payload, mapping, current_root / workload / "annotations" / name
            )
            write_json(out / workload / "annotations" / name, transformed)
            sessions += len(transformed["sessions"])
            marks += sum(len(row["marks"]) for row in transformed["sessions"])
        output_counts[workload] = {"sessions": sessions, "marks": marks}
        require(
            output_counts[workload] == input_counts[workload],
            f"{workload}: structural count drift",
        )

    report = {
        "schema": "agentsight.rq2-canonical-tag-map.v1",
        "algorithm": ALGORITHM,
        "inputs": {
            "allowed": ["pre-canonical semantic operation-name strings"],
            "forbidden": [
                "packets",
                "source summaries",
                "targets",
                "outcomes",
                "expert labels",
                "localizer or judge signals",
                "per-query AP",
                "MAP summaries",
            ],
        },
        "counts": input_counts,
        "old_unique_tags": len(mapping),
        "new_unique_tags": len(set(mapping.values())),
        "initial_adjacent_collisions": initial_collisions,
        "collision_refined_tags": len(refinements),
        "remaining_adjacent_collisions": remaining_collisions,
        "one_word_tags": sum(len(tag.split()) == 1 for tag in mapping.values()),
        "two_word_tags": sum(len(tag.split()) == 2 for tag in mapping.values()),
        "three_word_tags": sum(len(tag.split()) == 3 for tag in mapping.values()),
        "mapping": mapping,
    }
    write_json(mapping_out, report)
    return report


def nearest_rank_interval(values: Sequence[float]) -> list[float]:
    require(bool(values), "empty bootstrap")
    ordered = sorted(values)
    lower = math.ceil(0.025 * len(ordered)) - 1
    upper = math.ceil(0.975 * len(ordered)) - 1
    return [ordered[lower], ordered[upper]]


def workload_clusters(
    benchmark: str, root: Path, query_ids: Iterable[str]
) -> tuple[dict[str, tuple[str, str]], dict[str, list[str]] | None]:
    query_ids = set(query_ids)
    assignments: dict[str, tuple[str, str]] = {}
    universe: dict[str, list[str]] | None = None
    if benchmark == "agentprocess":
        all_clusters: defaultdict[str, set[str]] = defaultdict(set)
        for row in read_jsonl(root / "group-assignments.jsonl"):
            family = str(row["family"])
            task = str(row["task_id"])
            all_clusters[family].add(task)
            query = str(row["trajectory_id"])
            if query in query_ids:
                assignments[query] = (family, task)
        universe = {key: sorted(value) for key, value in all_clusters.items()}
    elif benchmark == "hint":
        for row in read_jsonl(root / "operations" / "test-projection.jsonl"):
            query = str(row["record_key"])
            if query in query_ids:
                environment = str(row["raw_fields"]["environment"])
                previous = assignments.get(query)
                current = (environment, query)
                require(
                    previous is None or previous == current,
                    f"{query}: inconsistent HINT environment",
                )
                assignments[query] = current
    elif benchmark == "trace":
        for query in query_ids:
            head = query.split("/", 1)[0]
            cell = head.removeprefix("captain-runs-")
            assignments[query] = (cell, query)
    else:
        raise ExperimentError(f"unknown benchmark: {benchmark}")
    require(set(assignments) == query_ids, f"{benchmark}: query cluster coverage")
    return assignments, universe


def paired_bootstrap(
    deltas: Mapping[str, float],
    assignments: Mapping[str, tuple[str, str]],
    repetitions: int,
    seed: int,
    universe: Mapping[str, Sequence[str]] | None,
) -> dict[str, Any]:
    by_stratum: defaultdict[str, defaultdict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for query, delta in deltas.items():
        stratum, cluster = assignments[query]
        by_stratum[stratum][cluster].append(float(delta))
    if universe is not None:
        for stratum, clusters in universe.items():
            for cluster in clusters:
                by_stratum[stratum][cluster]
    rng = random.Random(seed)
    draws = []
    for _ in range(repetitions):
        sample: list[float] = []
        for clusters in by_stratum.values():
            keys = sorted(clusters)
            for _key in keys:
                sample.extend(clusters[rng.choice(keys)])
        require(bool(sample), "bootstrap selected no target-bearing query")
        draws.append(statistics.fmean(sample))
    interval = nearest_rank_interval(draws)
    return {
        "repetitions": repetitions,
        "seed": seed,
        "strata": len(by_stratum),
        "clusters": sum(len(value) for value in by_stratum.values()),
        "interval_95": interval,
        "median": statistics.median(draws),
        "nonpositive_draws": sum(value <= 0.0 for value in draws),
        "classification": (
            "positive"
            if interval[0] > 0.0
            else "negative"
            if interval[1] < 0.0
            else "inconclusive"
        ),
    }


def indexed_rows(path: Path) -> dict[str, Mapping[str, Any]]:
    rows = {str(row["query_id"]): row for row in read_jsonl(path)}
    require(bool(rows), f"{path}: empty per-query input")
    require(len(rows) == len(read_jsonl(path)), f"{path}: duplicate query ID")
    return rows


def require_fair_group_inputs(current_path: Path, candidate_path: Path) -> None:
    """Reject a naming comparison that changes structure or source evidence."""
    current_source = current_path.parent / "source-operations.jsonl"
    candidate_source = candidate_path.parent / "source-operations.jsonl"
    require(current_source.is_file(), f"missing current source input: {current_source}")
    require(
        candidate_source.is_file(),
        f"missing candidate source input: {candidate_source}",
    )
    require(
        current_source.read_bytes() == candidate_source.read_bytes(),
        "current/candidate source-evidence rows differ",
    )
    current_groups = read_jsonl(current_path.parent / "fixed-groups.jsonl")
    candidate_groups = read_jsonl(candidate_path.parent / "fixed-groups.jsonl")
    require(
        len(current_groups) == len(candidate_groups),
        "current/candidate fixed-group coverage differs",
    )
    for current, candidate in zip(current_groups, candidate_groups):
        for field in ("operation_id", "sequence", "task_family"):
            require(
                current[field] == candidate[field],
                f"current/candidate fixed-group {field} differs",
            )
        current_paths = current["groups"]
        candidate_paths = candidate["groups"]
        for method in ("native_tree", "recurrence"):
            require(
                current_paths[method] == candidate_paths[method],
                f"current/candidate {method} differs",
            )
        current_agent = current_paths["automatic_agent"]
        candidate_agent = candidate_paths["automatic_agent"]
        require(
            len(current_agent) == len(candidate_agent),
            "current/candidate automatic path depth differs",
        )
        current_source_path = current_paths["source_preserving_agent"]
        candidate_source_path = candidate_paths["source_preserving_agent"]
        require(
            current_source_path[: len(current_agent)] == current_agent
            and candidate_source_path[: len(candidate_agent)] == candidate_agent,
            "source-preserving path does not extend its automatic path",
        )
        require(
            current_source_path[len(current_agent) :]
            == candidate_source_path[len(candidate_agent) :],
            "current/candidate source-evidence suffix differs",
        )


def score_comparison(
    benchmark: str,
    root: Path,
    current_path: Path,
    candidate_path: Path,
    out: Path,
) -> dict[str, Any]:
    require_fair_group_inputs(current_path, candidate_path)
    current = indexed_rows(current_path)
    candidate = indexed_rows(candidate_path)
    require(set(current) == set(candidate), "current/candidate query coverage")
    queries = sorted(current)
    for query in queries:
        require(
            int(current[query]["operations"]) == int(candidate[query]["operations"])
            and int(current[query]["targets"]) == int(candidate[query]["targets"]),
            f"{query}: operation or target drift",
        )
    current_ap = {
        query: float(current[query]["ap"]["source_preserving_agent"]) for query in queries
    }
    candidate_ap = {
        query: float(candidate[query]["ap"]["source_preserving_agent"]) for query in queries
    }
    native_ap = {
        query: float(candidate[query]["ap"]["native_tree"]) for query in queries
    }
    agent_only_ap = {
        query: float(candidate[query]["ap"]["automatic_agent"]) for query in queries
    }
    assignments, universe = workload_clusters(benchmark, root, queries)
    repetitions, seed = BOOTSTRAPS[benchmark]
    candidate_current = {
        query: candidate_ap[query] - current_ap[query] for query in queries
    }
    candidate_native = {
        query: candidate_ap[query] - native_ap[query] for query in queries
    }
    candidate_evidence = {
        query: candidate_ap[query] - agent_only_ap[query] for query in queries
    }
    report = {
        "schema": "agentsight.rq2-canonical-tag-comparison.v1",
        "benchmark": benchmark,
        "queries": len(queries),
        "metric": "standard non-interpolated per-query AP; arithmetic-mean MAP",
        "map": {
            "current_source_preserving_agent": statistics.fmean(current_ap.values()),
            "canonical_source_preserving_agent": statistics.fmean(candidate_ap.values()),
            "canonical_agent_only": statistics.fmean(agent_only_ap.values()),
            "native_tree": statistics.fmean(native_ap.values()),
        },
        "canonical_minus_current": {
            "point": statistics.fmean(candidate_current.values()),
            "paired_bootstrap": paired_bootstrap(
                candidate_current,
                assignments,
                repetitions,
                seed,
                universe,
            ),
        },
        "canonical_minus_native": {
            "point": statistics.fmean(candidate_native.values()),
            "paired_bootstrap": paired_bootstrap(
                candidate_native,
                assignments,
                repetitions,
                seed,
                universe,
            ),
        },
        "canonical_evidence_minus_agent_only": {
            "point": statistics.fmean(candidate_evidence.values()),
            "paired_bootstrap": paired_bootstrap(
                candidate_evidence,
                assignments,
                repetitions,
                seed,
                universe,
            ),
        },
    }
    write_json(out, report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--current-root", type=Path, required=True)
    prepare_parser.add_argument("--out", type=Path, required=True)
    prepare_parser.add_argument("--mapping-out", type=Path, required=True)

    score_parser = subparsers.add_parser("score")
    score_parser.add_argument("--benchmark", choices=WORKLOADS, required=True)
    score_parser.add_argument("--root", type=Path, required=True)
    score_parser.add_argument("--current-results", type=Path, required=True)
    score_parser.add_argument("--candidate-results", type=Path, required=True)
    score_parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "prepare":
        report = prepare(
            args.current_root.resolve(),
            args.out.resolve(),
            args.mapping_out.resolve(),
        )
    else:
        report = score_comparison(
            args.benchmark,
            args.root.resolve(),
            args.current_results.resolve(),
            args.candidate_results.resolve(),
            args.out.resolve(),
        )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
