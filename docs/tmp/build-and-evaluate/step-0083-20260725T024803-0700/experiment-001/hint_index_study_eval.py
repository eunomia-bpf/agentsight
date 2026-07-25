#!/usr/bin/env python3
"""Index-study replication on HINTBench (step 0083 / RQ2) — three conditions.

Exact v1 protocols of steps 0079 (full-trace reader), 0080 (semantic-skeleton
two-stage reader), and 0081 (raw-action-skeleton two-stage reader), changed
only in:

- workload: HINTBench frozen step-0072 inputs (400 target-bearing queries out
  of 536 test trajectories; zero-positive trajectories consumed for coverage
  and excluded from MAP),
- reader CLI: ``kimi -p`` (model kimi-code/k3) instead of grok,
- group identities: HINTBench equivalents from the same frozen artifact
  family (source_preserving_agent semantic paths; information-matched raw
  path built from projection raw_fields.action + the 3-frame source-evidence
  suffix of fixed-groups.jsonl, identical to
  script/rq2_current_agent_local_first.py::construct_scores).

Compared against stored HINTBench Direct-only (local_only) and
Direct+AgentProf (local_agentprof) per-query APs from step 0072 /
rq2-current-agent-local-first-v1.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import math
import random
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from sklearn.metrics import average_precision_score
import tiktoken


REPO_ROOT = Path(__file__).resolve().parents[5]
HINT_ROOT = REPO_ROOT / (
    "docs/tmp/cycle-0003-20260713T121925-0700/01-experiment-gate/"
    "loop-001-rq2-hintbench/results/full"
)
PROJECTION = HINT_ROOT / "operations" / "test-projection.jsonl"
SOURCES_TEST = HINT_ROOT / "sources" / "test.json"
PACKET_ROOT = REPO_ROOT / ".agentsight/experiments/rq2-a0-v1/full/hint/packets"
BASELINE_PER_QUERY = (
    REPO_ROOT
    / ".agentsight/experiments/rq2-current-agent-local-first-v1/full/per-query.jsonl"
)
GROUP_MAPPING = (
    REPO_ROOT
    / ".agentsight/experiments/rq2-canonical-tags-v2-current/hint/results"
    / "fixed-groups.jsonl"
)
GROUP_KEY = "source_preserving_agent"
DEFAULT_OUT = Path(__file__).resolve().parent

FULL = "full_trace_reader"
SEM = "semantic_skeleton_reader"
RAW = "raw_action_skeleton_reader"
DIRECT_ONLY = "local_only"
DIRECT_AGENTPROF = "local_agentprof"
READER_CONDITIONS = (FULL, SEM, RAW)
ALL_CONDITIONS = (FULL, SEM, RAW, DIRECT_AGENTPROF, DIRECT_ONLY)
CONDITION_DISPLAY = {
    FULL: "Full-trace reader",
    SEM: "Semantic-skeleton reader",
    RAW: "Raw-action-skeleton reader",
    DIRECT_AGENTPROF: "Direct+AgentProf (stored)",
    DIRECT_ONLY: "Direct-only (stored)",
}

# Pairwise delta seeds (10 pairs among 5 conditions; delta = first - second).
PAIR_SEEDS = {
    (FULL, SEM): 20260931,
    (FULL, RAW): 20260932,
    (FULL, DIRECT_AGENTPROF): 20260924,
    (FULL, DIRECT_ONLY): 20260923,
    (SEM, RAW): 20260933,
    (SEM, DIRECT_AGENTPROF): 20260934,
    (SEM, DIRECT_ONLY): 20260935,
    (RAW, DIRECT_AGENTPROF): 20260936,
    (RAW, DIRECT_ONLY): 20260937,
    (DIRECT_AGENTPROF, DIRECT_ONLY): 20260938,
}
# Content-efficiency decision metric seed (same role as step-0081 review seed).
CONTENT_DELTA_SEED = 20260927
BOOTSTRAP_REPS = 10000
MAX_SELECT_GROUPS = 5

EXPECTED = {
    "trajectories": 536,
    "operations": 12877,
    "target_queries": 400,
    "clean_queries": 136,
}
STORED_MAP = {
    DIRECT_ONLY: 0.4105587754001585,
    DIRECT_AGENTPROF: 0.5174888725910552,
}

KIMI_MODEL = "kimi-code/k3"
KIMI_TIMEOUT_S = 900

READER_INSTRUCTION = """You are diagnosing which operations in an agent trajectory are responsible for the agent's failure or incorrect solution on the assigned task.

You receive:
1) the original task text the agent was solving, and
2) the full ordered list of source operations with stable source operation_id values and source-visible content only.

Rules:
- Use only the provided task text and source-visible operation content.
- Do not invent operation IDs. Every ranked ID must appear exactly in the operations list.
- Rank operations by how likely each is responsible for the failure/incorrect outcome (most likely first).
- Cover at least every operation you consider plausibly responsible. You may rank additional operations if useful.
- Return ONLY strict JSON with this exact shape and no other text:
{"ranked_operation_ids": ["operation_id_most_likely", "operation_id_next", ...]}
"""

READER_RETRY = """Your previous reply was not valid strict JSON with key ranked_operation_ids listing known operation_id strings.
Reply again with ONLY valid JSON of the form:
{"ranked_operation_ids": ["id1", "id2", ...]}
Do not include markdown fences or commentary.
"""


def stage1_instruction(path_kind: str) -> str:
    return f"""You are diagnosing which groups of operations in an agent trajectory are most likely to contain the decisive mistake responsible for the agent's failure or incorrect solution.

You receive:
1) the original task text the agent was solving, and
2) a profile skeleton: every source operation with its stable operation_id, ordinal, and its frozen {path_kind} operation path, already grouped by full path (path prefix groups). NO source content is provided.

Rules:
- Use only the provided task text and the profile skeleton (operation IDs, ordinals, {path_kind} paths).
- Do not invent group paths or operation IDs.
- Select up to 5 groups (path prefixes / full group paths) most likely to contain the decisive mistake.
- Prefer groups whose {path_kind} path suggests the failure mode for this task; when unsure, prefer larger groups that still look relevant.
- Return ONLY strict JSON with this exact shape and no other text:
{{"selected_group_paths": [["path_component_1", "path_component_2", ...], ...]}}
Each selected path must exactly match one of the group_path arrays in the packet.
"""


STAGE1_RETRY = """Your previous reply was not valid strict JSON with key selected_group_paths listing known group_path arrays.
Reply again with ONLY valid JSON of the form:
{"selected_group_paths": [["comp1", "comp2", ...], ...]}
Select at most 5 groups. Do not include markdown fences or commentary.
"""


def stage2_instruction(path_kind: str) -> str:
    return f"""You are diagnosing which operations in an agent trajectory are responsible for the agent's failure or incorrect solution on the assigned task.

You receive:
1) the original task text,
2) the full profile skeleton (operation IDs, ordinals, {path_kind} paths grouped by path), and
3) source-visible content (source_summary) for ONLY the operations in the previously selected groups.

Rules:
- Use only the provided task text, profile skeleton, and the attached source_summary evidence.
- Do not invent operation IDs. Every ranked ID must appear exactly in the operations list.
- Rank operations by how likely each is responsible for the failure/incorrect outcome (most likely first).
- Prefer ranking among the operations that have source_summary evidence first; you may also rank other known operation_ids if needed.
- Cover at least every operation you consider plausibly responsible.
- Return ONLY strict JSON with this exact shape and no other text:
{{"ranked_operation_ids": ["operation_id_most_likely", "operation_id_next", ...]}}
"""


STAGE2_RETRY = """Your previous reply was not valid strict JSON with key ranked_operation_ids listing known operation_id strings.
Reply again with ONLY valid JSON of the form:
{"ranked_operation_ids": ["id1", "id2", ...]}
Do not include markdown fences or commentary.
"""


class ExperimentError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ExperimentError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def path_key(path: Sequence[str]) -> str:
    return " › ".join(str(part) for part in path)


# ---------------------------------------------------------------------------
# Frozen input loaders (HINTBench)
# ---------------------------------------------------------------------------


def load_packets(packet_root: Path) -> dict[str, dict[str, Any]]:
    sessions: dict[str, dict[str, Any]] = {}
    for path in sorted(packet_root.glob("batch-*.json")):
        payload = read_json(path)
        for session in payload["sessions"]:
            sequence = str(session["sequence"])
            require(sequence not in sessions, f"duplicate packet sequence {sequence}")
            sessions[sequence] = session
    require(
        len(sessions) == EXPECTED["trajectories"],
        f"expected {EXPECTED['trajectories']} packets, got {len(sessions)}",
    )
    return sessions


def load_projections(projection_path: Path) -> dict[str, list[dict[str, Any]]]:
    by_query: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in read_jsonl(projection_path):
        by_query[str(row["record_key"])].append(row)
    for query_id, rows in by_query.items():
        rows.sort(key=lambda item: (int(item["display_id"]), str(item["operation_id"])))
        by_query[query_id] = rows
    require(
        len(by_query) == EXPECTED["trajectories"],
        f"expected {EXPECTED['trajectories']} trajectories, got {len(by_query)}",
    )
    require(
        sum(len(rows) for rows in by_query.values()) == EXPECTED["operations"],
        f"expected {EXPECTED['operations']} operations",
    )
    return by_query


def load_targets(sources_test: Path) -> dict[str, set[int]]:
    """Identical to script/rq2_current_agent_local_first.py::load_labels('hint')."""
    targets: dict[str, set[int]] = {}
    for row in read_json(sources_test):
        query_id = f"test:{row['id']}"
        values: set[int] = set()
        for field in ("injected_risks", "risk_labels"):
            for annotation in row.get(field, []):
                value = annotation.get("risk_origin_step")
                if value is None:
                    value = annotation.get("step_id")
                require(
                    isinstance(value, int) and not isinstance(value, bool),
                    f"{query_id}: invalid target",
                )
                values.add(value)
        targets[query_id] = values
    require(
        len(targets) == EXPECTED["trajectories"],
        f"expected {EXPECTED['trajectories']} target rows, got {len(targets)}",
    )
    return targets


def load_baseline_aps(path: Path) -> dict[str, dict[str, Any]]:
    rows = {}
    for row in read_jsonl(path):
        if row.get("benchmark") != "HINTBench":
            continue
        query_id = str(row["query_id"])
        require(query_id not in rows, f"duplicate baseline query {query_id}")
        rows[query_id] = row
    require(
        len(rows) == EXPECTED["target_queries"],
        f"expected {EXPECTED['target_queries']} baseline rows, got {len(rows)}",
    )
    return rows


def source_suffix_from_fixed(fixed_row: Mapping[str, Any]) -> tuple[str, ...]:
    """Identical to script/rq2_current_agent_local_first.py::source_suffix."""
    groups = fixed_row["groups"]
    automatic = tuple(str(value) for value in groups["automatic_agent"])
    preserved = tuple(str(value) for value in groups[GROUP_KEY])
    require(
        len(preserved) > len(automatic) and preserved[: len(automatic)] == automatic,
        f"{fixed_row['operation_id']}: source-preserving path is not an extension",
    )
    suffix = preserved[len(automatic) :]
    require(
        len(suffix) == 3,
        f"{fixed_row['operation_id']}: expected three source-evidence frames",
    )
    return suffix


def load_operation_paths(
    fixed_groups_path: Path,
    projections: Mapping[str, Sequence[Mapping[str, Any]]],
) -> tuple[dict[str, dict[str, list[str]]], dict[str, Any]]:
    """operation_id -> {"semantic": [...], "raw": [...]} plus provenance.

    Semantic path: frozen target-blind Agent+Evidence path
    (groups.source_preserving_agent) — the step-0080 group identity.

    Raw path: step-0072 information-matched raw+evidence path, identical to
    construct_scores in script/rq2_current_agent_local_first.py:
        (task_family.casefold(), "raw:" + raw_fields.action.casefold(), *suffix)
    where raw_fields.action is the HINTBench raw identity (the method-index
    methods.raw.operation_leaves equivalent; see load_hint_sources) and suffix
    is the last three frames of source_preserving_agent after the
    automatic_agent prefix.
    """
    require(fixed_groups_path.is_file(), f"fixed-groups not found: {fixed_groups_path}")

    raw_identity_by_op: dict[str, str] = {}
    for query_id, rows in projections.items():
        for row in rows:
            operation_id = str(row["operation_id"])
            require(
                operation_id not in raw_identity_by_op,
                f"duplicate projection op {operation_id}",
            )
            raw_identity_by_op[operation_id] = str(row["raw_fields"]["action"])

    mapping: dict[str, dict[str, list[str]]] = {}
    by_sequence: dict[str, int] = defaultdict(int)
    for row in read_jsonl(fixed_groups_path):
        operation_id = str(row["operation_id"])
        require(
            operation_id in raw_identity_by_op,
            f"{operation_id}: missing raw identity",
        )
        groups = row.get("groups") or {}
        require(GROUP_KEY in groups, f"{operation_id}: missing {GROUP_KEY}")
        require(
            "automatic_agent" in groups, f"{operation_id}: missing automatic_agent"
        )
        semantic_path = [str(part) for part in groups[GROUP_KEY]]
        require(bool(semantic_path), f"{operation_id}: empty semantic path")
        suffix = source_suffix_from_fixed(row)
        task_family = str(row["task_family"]).strip().casefold()
        raw_identity = raw_identity_by_op[operation_id].strip().casefold()
        raw_path = [task_family, f"raw:{raw_identity}", *suffix]
        require(operation_id not in mapping, f"duplicate operation_id {operation_id}")
        mapping[operation_id] = {"semantic": semantic_path, "raw": raw_path}
        by_sequence[str(row["sequence"])] += 1

    require(
        len(mapping) == EXPECTED["operations"],
        f"expected {EXPECTED['operations']} mapped ops, got {len(mapping)}",
    )
    require(
        len(by_sequence) == EXPECTED["trajectories"],
        f"expected {EXPECTED['trajectories']} sequences, got {len(by_sequence)}",
    )
    for query_id, rows in projections.items():
        for row in rows:
            require(
                str(row["operation_id"]) in mapping,
                f"unmapped op {row['operation_id']}",
            )

    provenance = {
        "semantic_identity_source": str(fixed_groups_path.resolve()),
        "semantic_identity_field": f"groups.{GROUP_KEY}",
        "raw_identity_source": str(PROJECTION.resolve()),
        "raw_identity_field": "raw_fields.action",
        "raw_identity_note": (
            "HINTBench equivalent of method-index methods.raw.operation_leaves: "
            "load_hint_sources in script/rq2_current_agent_local_first.py reads "
            "raw_identity from raw_fields.action of the same frozen projection."
        ),
        "source_suffix_source": (
            f"fixed-groups.jsonl groups[{GROUP_KEY}] after automatic_agent prefix "
            "(exactly 3 frames: source-kind, source-call/tool, outcome)"
        ),
        "path_construction": (
            "(task_family.casefold(), 'raw:' + raw_fields.action.casefold(), *suffix) "
            "— identical to script/rq2_current_agent_local_first.py construct_scores "
            "for local_raw_evidence / raw_source_evidence"
        ),
        "unique_raw_actions": len(set(raw_identity_by_op.values())),
        "step_0072_script": "script/rq2_current_agent_local_first.py",
        "step_0072_condition": "local_raw_evidence",
    }
    return mapping, provenance


# ---------------------------------------------------------------------------
# Packet builders (exact step-0079 / 0080 / 0081 packet schemas)
# ---------------------------------------------------------------------------


def build_reader_packet(session: Mapping[str, Any]) -> dict[str, Any]:
    """Step-0079 full-trace packet: source-visible content only, no targets."""
    operations = []
    for op in session["operations"]:
        operations.append(
            {
                "operation_id": str(op["operation_id"]),
                "ordinal": int(op["ordinal"]),
                "native_path": list(op.get("native_path") or []),
                "source_summary": op.get("source_summary"),
            }
        )
    return {
        "task": str(session["task"]),
        "operation_count": len(operations),
        "operations": operations,
    }


def build_skeleton(
    session: Mapping[str, Any],
    op_paths: Mapping[str, Mapping[str, list[str]]],
    path_kind: str,
) -> dict[str, Any]:
    """Profile skeleton: ops + groups by full path. No source content."""
    path_field = "semantic_path" if path_kind == "semantic" else "raw_action_path"
    operations: list[dict[str, Any]] = []
    groups_map: dict[str, dict[str, Any]] = {}
    for op in session["operations"]:
        operation_id = str(op["operation_id"])
        ordinal = int(op["ordinal"])
        require(operation_id in op_paths, f"unmapped operation {operation_id}")
        group_path = list(op_paths[operation_id][path_kind])
        operations.append(
            {
                "operation_id": operation_id,
                "ordinal": ordinal,
                path_field: group_path,
            }
        )
        key = path_key(group_path)
        if key not in groups_map:
            groups_map[key] = {
                "group_path": group_path,
                "path_key": key,
                "member_ordinals": [],
                "member_operation_ids": [],
            }
        groups_map[key]["member_ordinals"].append(ordinal)
        groups_map[key]["member_operation_ids"].append(operation_id)

    # Deterministic order: larger groups first, then path key.
    groups = sorted(
        groups_map.values(),
        key=lambda g: (-len(g["member_operation_ids"]), g["path_key"]),
    )
    largest_group_size = (
        max(len(g["member_operation_ids"]) for g in groups) if groups else 0
    )
    return {
        "task": str(session["task"]),
        "operation_count": len(operations),
        "group_count": len(groups),
        "largest_group_size": largest_group_size,
        "operations": operations,
        "groups": groups,
    }


def build_stage1_packet(skeleton: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "task": skeleton["task"],
        "operation_count": skeleton["operation_count"],
        "group_count": skeleton["group_count"],
        "groups": [
            {
                "group_path": g["group_path"],
                "member_ordinals": g["member_ordinals"],
                "member_operation_ids": g["member_operation_ids"],
                "member_count": len(g["member_operation_ids"]),
            }
            for g in skeleton["groups"]
        ],
        "operations": skeleton["operations"],
    }


def build_stage2_packet(
    skeleton: Mapping[str, Any],
    session: Mapping[str, Any],
    selected_paths: Sequence[Sequence[str]],
) -> dict[str, Any]:
    selected_keys = {path_key(p) for p in selected_paths}
    selected_ids: set[str] = set()
    for group in skeleton["groups"]:
        if group["path_key"] in selected_keys:
            selected_ids.update(group["member_operation_ids"])

    evidence = []
    for op in session["operations"]:
        operation_id = str(op["operation_id"])
        if operation_id not in selected_ids:
            continue
        evidence.append(
            {
                "operation_id": operation_id,
                "ordinal": int(op["ordinal"]),
                "source_summary": op.get("source_summary"),
            }
        )
    return {
        "task": skeleton["task"],
        "operation_count": skeleton["operation_count"],
        "group_count": skeleton["group_count"],
        "selected_group_paths": [list(p) for p in selected_paths],
        "groups": [
            {
                "group_path": g["group_path"],
                "member_ordinals": g["member_ordinals"],
                "member_operation_ids": g["member_operation_ids"],
                "member_count": len(g["member_operation_ids"]),
            }
            for g in skeleton["groups"]
        ],
        "operations": skeleton["operations"],
        "selected_evidence": evidence,
        "selected_evidence_operation_count": len(evidence),
    }


def packet_char_count(packet: Mapping[str, Any]) -> int:
    return len(json.dumps(packet, ensure_ascii=False, sort_keys=True))


def build_prompt(instruction: str, packet: Mapping[str, Any], extra: str = "") -> str:
    body = json.dumps(packet, ensure_ascii=False, sort_keys=True)
    parts = [instruction.strip(), "", "Evidence packet:", body]
    if extra:
        parts.extend(["", extra.strip()])
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Response parsing (identical to steps 0079-0081)
# ---------------------------------------------------------------------------


def extract_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    candidates: list[str] = []
    if fence:
        candidates.append(fence.group(1))
    candidates.append(text)
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(text[start : end + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def parse_selected_groups(
    response_text: str, valid_paths: Sequence[Sequence[str]]
) -> list[list[str]] | None:
    obj = extract_json_object(response_text)
    if obj is None:
        return None
    selected = obj.get("selected_group_paths")
    if selected is None and "selected_groups" in obj:
        selected = obj["selected_groups"]
    if selected is None and "groups" in obj:
        selected = obj["groups"]
    if not isinstance(selected, list) or not selected:
        return None

    valid_by_key = {path_key(p): list(p) for p in valid_paths}
    alt_keys: dict[str, list[str]] = {}
    for key, path in valid_by_key.items():
        alt_keys[key] = path
        alt_keys[" / ".join(path)] = path
        alt_keys["/".join(path)] = path
        alt_keys[" > ".join(path)] = path
        alt_keys[json.dumps(path, ensure_ascii=False)] = path

    out: list[list[str]] = []
    seen: set[str] = set()
    for item in selected:
        path: list[str] | None = None
        if isinstance(item, list) and all(isinstance(x, str) for x in item):
            key = path_key(item)
            if key in valid_by_key:
                path = valid_by_key[key]
        elif isinstance(item, str):
            if item in alt_keys:
                path = alt_keys[item]
            elif item in valid_by_key:
                path = valid_by_key[item]
        elif isinstance(item, dict):
            if "group_path" in item and isinstance(item["group_path"], list):
                key = path_key([str(x) for x in item["group_path"]])
                if key in valid_by_key:
                    path = valid_by_key[key]
            elif "path_key" in item and str(item["path_key"]) in valid_by_key:
                path = valid_by_key[str(item["path_key"])]
        if path is None:
            return None
        key = path_key(path)
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
        if len(out) >= MAX_SELECT_GROUPS:
            break
    return out if out else None


def parse_ranked_ids(
    response_text: str, valid_ids: Sequence[str]
) -> list[str] | None:
    obj = extract_json_object(response_text)
    if obj is None:
        return None
    ranked = obj.get("ranked_operation_ids")
    if ranked is None and "ranked" in obj:
        ranked = obj["ranked"]
    if not isinstance(ranked, list) or not ranked:
        return None
    valid = set(valid_ids)
    out: list[str] = []
    seen: set[str] = set()
    for item in ranked:
        if not isinstance(item, str):
            return None
        if item not in valid:
            return None
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out if out else None


def complete_ranking(
    ranked: Sequence[str], original_order: Sequence[str]
) -> list[str]:
    seen = set(ranked)
    completed = list(ranked)
    for operation_id in original_order:
        if operation_id not in seen:
            completed.append(operation_id)
    require(len(completed) == len(original_order), "completed ranking size mismatch")
    require(set(completed) == set(original_order), "completed ranking id set mismatch")
    return completed


def largest_groups_fallback(
    groups: Sequence[Mapping[str, Any]], k: int = MAX_SELECT_GROUPS
) -> list[list[str]]:
    ordered = sorted(
        groups,
        key=lambda g: (-len(g["member_operation_ids"]), g["path_key"]),
    )
    return [list(g["group_path"]) for g in ordered[:k]]


def ranking_to_scores(ranking: Sequence[str]) -> dict[str, float]:
    n = len(ranking)
    return {operation_id: float(n - index) for index, operation_id in enumerate(ranking)}


def standard_ap(labels: Sequence[int], scores: Sequence[float]) -> float:
    require(
        len(labels) == len(scores) and bool(labels) and sum(labels) > 0,
        "AP requires aligned nonempty inputs with a positive item",
    )
    require(all(math.isfinite(value) for value in scores), "non-finite AP score")
    return float(average_precision_score(labels, scores))


# ---------------------------------------------------------------------------
# Bootstrap (identical procedure to steps 0079-0081 / step 0072)
# ---------------------------------------------------------------------------


def nearest_interval(values: Sequence[float]) -> list[float]:
    ordered = sorted(float(value) for value in values)
    require(bool(ordered), "empty bootstrap")
    lower = math.ceil(0.025 * len(ordered)) - 1
    upper = math.ceil(0.975 * len(ordered)) - 1
    return [ordered[lower], ordered[upper]]


def paired_bootstrap_deltas(
    query_rows: Sequence[Mapping[str, Any]],
    delta_fn,
    repetitions: int,
    seed: int,
) -> dict[str, Any]:
    """Paired trajectory-cluster bootstrap within benchmark-defined strata."""
    by_stratum: defaultdict[str, defaultdict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in query_rows:
        by_stratum[str(row["stratum"])][str(row["cluster"])].append(float(delta_fn(row)))
    require(bool(by_stratum), "bootstrap received no query rows")
    rng = random.Random(seed)
    draws: list[float] = []
    for _ in range(repetitions):
        sampled: list[float] = []
        for clusters in by_stratum.values():
            keys = sorted(clusters)
            for _ in keys:
                sampled.extend(clusters[rng.choice(keys)])
        require(bool(sampled), "bootstrap sampled no queries")
        draws.append(statistics.fmean(sampled))
    return {
        "repetitions": repetitions,
        "seed": seed,
        "strata": len(by_stratum),
        "clusters": sum(len(value) for value in by_stratum.values()),
        "interval_95": nearest_interval(draws),
        "median": statistics.median(draws),
        "nonpositive_draws": sum(value <= 0.0 for value in draws),
        "draws": draws,
    }


# ---------------------------------------------------------------------------
# Reader invocation: kimi CLI, single-turn prompt mode (fixed flags)
# ---------------------------------------------------------------------------

TOKENIZER = tiktoken.get_encoding("o200k_base")


def call_kimi(
    prompt: str,
    cwd: Path,
    timeout_s: int = KIMI_TIMEOUT_S,
) -> tuple[str, float, dict[str, Any]]:
    """Invoke kimi once in single-turn prompt mode.

    Fixed invocation: kimi -p <prompt> -m kimi-code/k3 --output-format text
    --skills-dir <empty>. cwd is an empty directory so no project AGENTS.md or
    other workspace context is loaded. HINTBench prompts are at most ~21 KiB,
    far below ARG_MAX, so the -p argv form covers the complete population
    (verified by packet-size audit; no prompt-file fallback exists or is
    needed for this workload).
    """
    started = time.monotonic()
    cmd = [
        "kimi",
        "-p",
        prompt,
        "-m",
        KIMI_MODEL,
        "--output-format",
        "text",
        "--skills-dir",
        str(cwd),
    ]
    cmd_meta = ["kimi", "-p", "<prompt>", *cmd[3:]]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,
    )
    wall = time.monotonic() - started
    stdout = proc.stdout or ""
    meta = {
        "returncode": proc.returncode,
        "stderr_tail": (proc.stderr or "")[-4000:],
        "cmd": cmd_meta,
        "delivery": "p-flag",
        "prompt_bytes": len(prompt.encode("utf-8")),
        "prompt_tokens_o200k": len(TOKENIZER.encode(prompt)),
    }
    if proc.returncode != 0 and not stdout.strip():
        raise ExperimentError(
            f"kimi failed rc={proc.returncode}: {(proc.stderr or stdout)[:1000]}"
        )
    return stdout, wall, meta


def safe_query_filename(query_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", query_id)


def run_stage(
    instruction: str,
    retry_instruction: str,
    packet: Mapping[str, Any],
    parse_fn,
    parse_kwargs: Mapping[str, Any],
    kimi_cwd: Path,
) -> tuple[Any, str, bool, float, list[dict[str, Any]]]:
    """Two attempts (one format retry); returns (parsed, status, failed, wall, attempts)."""
    attempts: list[dict[str, Any]] = []
    wall_s = 0.0
    parsed = None
    status = "failure"
    failed = True
    for attempt_idx in range(2):
        extra = "" if attempt_idx == 0 else retry_instruction
        prompt = build_prompt(instruction, packet, extra=extra)
        try:
            raw_text, wall, meta = call_kimi(prompt, cwd=kimi_cwd)
        except Exception as exc:  # noqa: BLE001
            wall = 0.0
            meta = {"error": str(exc)}
            raw_text = ""
        wall_s += wall
        parsed_attempt = parse_fn(raw_text, **parse_kwargs) if raw_text else None
        attempts.append(
            {
                "attempt": attempt_idx + 1,
                "wall_seconds": wall,
                "raw_response": raw_text,
                "parsed": parsed_attempt,
                "meta": meta,
            }
        )
        if parsed_attempt is not None:
            parsed = parsed_attempt
            status = "ok" if attempt_idx == 0 else "ok_after_retry"
            failed = False
            break
    return parsed, status, failed, wall_s, attempts


def attempt_tokens(attempts: Sequence[Mapping[str, Any]]) -> int:
    total = 0
    for attempt in attempts:
        meta = attempt.get("meta") or {}
        total += int(meta.get("prompt_tokens_o200k") or 0)
    return total


# ---------------------------------------------------------------------------
# Per-query processors
# ---------------------------------------------------------------------------


def process_full_query(
    query_id: str,
    session: Mapping[str, Any],
    projection_rows: Sequence[Mapping[str, Any]],
    target_display_ids: set[int],
    out_dir: Path,
    kimi_cwd: Path,
    force: bool = False,
) -> dict[str, Any]:
    """Step-0079 full-trace protocol: one reader call per query."""
    packets_dir = out_dir / "packets-full"
    responses_dir = out_dir / "raw-responses-full"
    packets_dir.mkdir(parents=True, exist_ok=True)
    responses_dir.mkdir(parents=True, exist_ok=True)

    fname = safe_query_filename(query_id)
    packet_path = packets_dir / f"{fname}.json"
    response_path = responses_dir / f"{fname}.json"

    original_ids = [str(row["operation_id"]) for row in projection_rows]
    packet_ids = [str(op["operation_id"]) for op in session["operations"]]
    require(original_ids == packet_ids, f"{query_id}: packet/projection order mismatch")

    labels = [
        1 if int(row["display_id"]) in target_display_ids else 0
        for row in projection_rows
    ]
    require(sum(labels) >= 1, f"{query_id}: expected at least one target operation")

    reader_packet = build_reader_packet(session)
    write_json(packet_path, reader_packet)
    packet_chars = packet_char_count(reader_packet)

    if response_path.exists() and not force:
        cached = read_json(response_path)
        ranking = list(cached["completed_ranking"])
        status = str(cached.get("status", "cached"))
        failure = bool(cached.get("scored_as_original_order_failure", False))
        wall_s = float(cached.get("wall_seconds", 0.0))
        prompt_tokens = int(cached.get("prompt_tokens_o200k", 0))
    else:
        ranked, status, failure, wall_s, attempts = run_stage(
            READER_INSTRUCTION,
            READER_RETRY,
            reader_packet,
            parse_ranked_ids,
            {"valid_ids": original_ids},
            kimi_cwd,
        )
        if failure or ranked is None:
            ranking = list(original_ids)
            status = "failure_original_order"
            failure = True
        else:
            ranking = complete_ranking(ranked, original_ids)
        prompt_tokens = attempt_tokens(attempts)
        record = {
            "query_id": query_id,
            "condition": FULL,
            "status": status,
            "scored_as_original_order_failure": failure,
            "wall_seconds": wall_s,
            "packet_chars": packet_chars,
            "prompt_tokens_o200k": prompt_tokens,
            "attempts": attempts,
            "reader_ranked_operation_ids": (
                attempts[-1]["parsed"] if attempts else None
            ),
            "completed_ranking": ranking,
            "operation_count": len(original_ids),
        }
        write_json(response_path, record)

    scores = ranking_to_scores(ranking)
    score_vector = [scores[operation_id] for operation_id in original_ids]
    ap_reader = standard_ap(labels, score_vector)
    target_operation_ids = [
        str(row["operation_id"])
        for row in projection_rows
        if int(row["display_id"]) in target_display_ids
    ]
    return {
        "query_id": query_id,
        "condition": FULL,
        "status": status,
        "scored_as_original_order_failure": failure,
        "wall_seconds": wall_s,
        "packet_chars": packet_chars,
        "total_chars": packet_chars,
        "prompt_tokens_o200k": prompt_tokens,
        "ap_reader": ap_reader,
        "reader_rank_of_target": min(
            (ranking.index(oid) + 1 for oid in target_operation_ids), default=None
        ),
    }


def process_two_stage_query(
    condition: str,
    query_id: str,
    session: Mapping[str, Any],
    projection_rows: Sequence[Mapping[str, Any]],
    target_display_ids: set[int],
    op_paths: Mapping[str, Mapping[str, list[str]]],
    out_dir: Path,
    kimi_cwd: Path,
    force: bool = False,
) -> dict[str, Any]:
    """Step-0080 (semantic) / step-0081 (raw) two-stage protocol."""
    require(condition in (SEM, RAW), f"unknown two-stage condition {condition}")
    path_kind = "semantic" if condition == SEM else "raw"
    tag = "semantic" if condition == SEM else "raw"
    stage1_dir = out_dir / f"packets-{tag}-stage1"
    stage2_dir = out_dir / f"packets-{tag}-stage2"
    responses_dir = out_dir / f"raw-responses-{tag}"
    stage1_dir.mkdir(parents=True, exist_ok=True)
    stage2_dir.mkdir(parents=True, exist_ok=True)
    responses_dir.mkdir(parents=True, exist_ok=True)

    fname = safe_query_filename(query_id)
    stage1_path = stage1_dir / f"{fname}.json"
    stage2_path = stage2_dir / f"{fname}.json"
    response_path = responses_dir / f"{fname}.json"

    original_ids = [str(row["operation_id"]) for row in projection_rows]
    packet_ids = [str(op["operation_id"]) for op in session["operations"]]
    require(original_ids == packet_ids, f"{query_id}: packet/projection order mismatch")
    for operation_id in original_ids:
        require(operation_id in op_paths, f"{query_id}: missing path for {operation_id}")

    labels = [
        1 if int(row["display_id"]) in target_display_ids else 0
        for row in projection_rows
    ]
    require(sum(labels) >= 1, f"{query_id}: expected at least one target operation")

    skeleton = build_skeleton(session, op_paths, path_kind)
    stage1_packet = build_stage1_packet(skeleton)
    write_json(stage1_path, stage1_packet)
    stage1_chars = packet_char_count(stage1_packet)
    valid_paths = [list(g["group_path"]) for g in skeleton["groups"]]

    if response_path.exists() and not force:
        cached = read_json(response_path)
        ranking = list(cached["completed_ranking"])
        selected_paths = [list(p) for p in cached["selected_group_paths"]]
        stage1_status = str(cached.get("stage1_status", "cached"))
        stage2_status = str(cached.get("stage2_status", "cached"))
        stage1_fallback = bool(cached.get("stage1_largest_groups_fallback", False))
        stage2_failure = bool(cached.get("stage2_scored_as_original_order_failure", False))
        wall_s = float(cached.get("wall_seconds_total", 0.0))
        stage1_wall = float(cached.get("stage1_wall_seconds", 0.0))
        stage2_wall = float(cached.get("stage2_wall_seconds", 0.0))
        prompt_tokens = int(cached.get("prompt_tokens_o200k", 0))
        if stage2_path.exists():
            stage2_packet = read_json(stage2_path)
        else:
            stage2_packet = build_stage2_packet(skeleton, session, selected_paths)
            write_json(stage2_path, stage2_packet)
        stage2_chars = packet_char_count(stage2_packet)
    else:
        # ---- Stage 1 ----
        selected_paths, stage1_status, stage1_failed, stage1_wall, attempts_stage1 = (
            run_stage(
                stage1_instruction(path_kind),
                STAGE1_RETRY,
                stage1_packet,
                parse_selected_groups,
                {"valid_paths": valid_paths},
                kimi_cwd,
            )
        )
        stage1_fallback = False
        if stage1_failed or selected_paths is None:
            selected_paths = largest_groups_fallback(skeleton["groups"])
            stage1_status = "failure_largest_groups_fallback"
            stage1_fallback = True

        # ---- Stage 2 ----
        stage2_packet = build_stage2_packet(skeleton, session, selected_paths)
        write_json(stage2_path, stage2_packet)
        stage2_chars = packet_char_count(stage2_packet)

        ranked, stage2_status, stage2_failure, stage2_wall, attempts_stage2 = run_stage(
            stage2_instruction(path_kind),
            STAGE2_RETRY,
            stage2_packet,
            parse_ranked_ids,
            {"valid_ids": original_ids},
            kimi_cwd,
        )
        if stage2_failure or ranked is None:
            ranking = list(original_ids)
            stage2_status = "failure_original_order"
            stage2_failure = True
        else:
            ranking = complete_ranking(ranked, original_ids)

        wall_s = stage1_wall + stage2_wall
        prompt_tokens = attempt_tokens(attempts_stage1) + attempt_tokens(attempts_stage2)
        record = {
            "query_id": query_id,
            "condition": condition,
            "selected_group_paths": selected_paths,
            "selected_group_path_keys": [path_key(p) for p in selected_paths],
            "stage1_status": stage1_status,
            "stage1_largest_groups_fallback": stage1_fallback,
            "stage1_wall_seconds": stage1_wall,
            "stage1_chars": stage1_chars,
            "stage1_attempts": attempts_stage1,
            "stage2_status": stage2_status,
            "stage2_scored_as_original_order_failure": stage2_failure,
            "stage2_wall_seconds": stage2_wall,
            "stage2_chars": stage2_chars,
            "stage2_attempts": attempts_stage2,
            "prompt_tokens_o200k": prompt_tokens,
            "reader_ranked_operation_ids": (
                attempts_stage2[-1]["parsed"] if attempts_stage2 else None
            ),
            "completed_ranking": ranking,
            "wall_seconds_total": wall_s,
            "operation_count": len(original_ids),
            "group_count": skeleton["group_count"],
            "largest_group_size": skeleton["largest_group_size"],
            "selected_evidence_operation_count": stage2_packet[
                "selected_evidence_operation_count"
            ],
        }
        write_json(response_path, record)

    total_chars = stage1_chars + stage2_chars
    evidence_only = {"selected_evidence": stage2_packet.get("selected_evidence", [])}
    stage2_evidence_chars = packet_char_count(evidence_only)

    # Index hit: at least one target operation sits in a selected group.
    selected_keys = {path_key(p) for p in selected_paths}
    selected_ids: set[str] = set()
    for group in skeleton["groups"]:
        if group["path_key"] in selected_keys:
            selected_ids.update(group["member_operation_ids"])
    target_operation_ids = [
        str(row["operation_id"])
        for row in projection_rows
        if int(row["display_id"]) in target_display_ids
    ]
    index_hit = any(oid in selected_ids for oid in target_operation_ids)

    scores = ranking_to_scores(ranking)
    score_vector = [scores[operation_id] for operation_id in original_ids]
    ap_reader = standard_ap(labels, score_vector)

    return {
        "query_id": query_id,
        "condition": condition,
        "stage1_status": stage1_status,
        "stage2_status": stage2_status,
        "stage1_largest_groups_fallback": stage1_fallback,
        "stage2_scored_as_original_order_failure": stage2_failure,
        "wall_seconds": wall_s,
        "stage1_wall_seconds": stage1_wall,
        "stage2_wall_seconds": stage2_wall,
        "stage1_chars": stage1_chars,
        "stage2_chars": stage2_chars,
        "stage2_evidence_chars": stage2_evidence_chars,
        "total_chars": total_chars,
        "prompt_tokens_o200k": prompt_tokens,
        "group_count": skeleton["group_count"],
        "largest_group_size": skeleton["largest_group_size"],
        "selected_group_paths": selected_paths,
        "selected_evidence_operation_count": stage2_packet[
            "selected_evidence_operation_count"
        ],
        "index_hit": index_hit,
        "ap_reader": ap_reader,
        "reader_rank_of_target": min(
            (ranking.index(oid) + 1 for oid in target_operation_ids), default=None
        ),
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=("validate", "full", "score-only"),
        help="validate: <=3 queries; full: all 400; score-only: re-score from raw-responses",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--validate-n", type=int, default=3)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--packet-root", type=Path, default=PACKET_ROOT)
    parser.add_argument("--projection", type=Path, default=PROJECTION)
    parser.add_argument("--sources-test", type=Path, default=SOURCES_TEST)
    parser.add_argument("--baseline-per-query", type=Path, default=BASELINE_PER_QUERY)
    parser.add_argument("--group-mapping", type=Path, default=GROUP_MAPPING)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()

    packets = load_packets(args.packet_root.resolve())
    projections = load_projections(args.projection.resolve())
    targets = load_targets(args.sources_test.resolve())
    baselines = load_baseline_aps(args.baseline_per_query.resolve())
    op_paths, path_provenance = load_operation_paths(
        args.group_mapping.resolve(), projections
    )

    # Labels per operation, exactly as load_labels('hint').
    labels_by_op: dict[str, int] = {}
    for query_id, rows in projections.items():
        for row in rows:
            labels_by_op[str(row["operation_id"])] = int(
                int(row["display_id"]) in targets[query_id]
            )
    by_query_pos = {
        query_id: sum(labels_by_op[str(row["operation_id"])] for row in rows)
        for query_id, rows in projections.items()
    }
    target_queries = sorted(q for q in projections if by_query_pos[q] > 0)
    clean_queries = sorted(q for q in projections if by_query_pos[q] == 0)
    observed = {
        "trajectories": len(projections),
        "operations": sum(len(rows) for rows in projections.values()),
        "target_queries": len(target_queries),
        "clean_queries": len(clean_queries),
    }
    require(observed == EXPECTED, f"HINTBench population drift: {observed}")
    require(set(baselines) == set(target_queries), "baseline coverage mismatch")
    require(set(packets) == set(projections), "packet/projection coverage mismatch")
    # Zero-positive trajectories are consumed (coverage-checked above) and
    # excluded from MAP and from reader calls, exactly as the paper protocol.

    # Dedicated empty cwd so the reader loads no project context or skills.
    kimi_cwd = out_dir / "kimi-cwd"
    kimi_cwd.mkdir(parents=True, exist_ok=True)

    if args.mode == "validate":
        query_ids = target_queries[: args.validate_n]
    else:
        query_ids = target_queries
        if args.limit is not None:
            query_ids = query_ids[: args.limit]

    print(
        f"[hint-index-study] mode={args.mode} queries={len(query_ids)} "
        f"conditions=3 workers={args.workers} out={out_dir}",
        flush=True,
    )

    # rows[condition][query_id] -> per-condition result row
    rows: dict[str, dict[str, dict[str, Any]]] = {
        condition: {} for condition in READER_CONDITIONS
    }
    errors: list[str] = []

    def work(item: tuple[str, str]) -> tuple[str, dict[str, Any]]:
        condition, query_id = item
        common = dict(
            query_id=query_id,
            session=packets[query_id],
            projection_rows=projections[query_id],
            target_display_ids=targets[query_id],
            out_dir=out_dir,
            kimi_cwd=kimi_cwd,
            force=args.force and args.mode != "score-only",
        )
        if condition == FULL:
            return condition, process_full_query(**common)
        return condition, process_two_stage_query(
            condition=condition, op_paths=op_paths, **common
        )

    items = [(condition, qid) for condition in READER_CONDITIONS for qid in query_ids]
    if args.workers <= 1 or args.mode == "score-only":
        for item in items:
            try:
                condition, row = work(item)
                rows[condition][row["query_id"]] = row
                print(
                    f"[done] {condition} {row['query_id']} ap={row['ap_reader']:.4f} "
                    f"wall={row['wall_seconds']:.1f}s chars={row['total_chars']}",
                    flush=True,
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{item}: {exc}")
                print(f"[error] {item}: {exc}", flush=True)
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(work, item): item for item in items}
            done_count = 0
            for fut in as_completed(futures):
                item = futures[fut]
                try:
                    condition, row = fut.result()
                    rows[condition][row["query_id"]] = row
                    done_count += 1
                    if done_count % 20 == 0 or done_count == len(items):
                        print(
                            f"[progress] {done_count}/{len(items)} "
                            f"elapsed={time.monotonic()-started:.0f}s",
                            flush=True,
                        )
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{item}: {exc}")
                    print(f"[error] {item}: {exc}", flush=True)

    require(not errors, f"errors on {len(errors)} work items: {errors[:5]}")
    for condition in READER_CONDITIONS:
        require(
            len(rows[condition]) == len(query_ids),
            f"incomplete results for {condition}: "
            f"{len(rows[condition])}/{len(query_ids)}",
        )

    if args.mode == "validate":
        validate_path = out_dir / "validate-summary.json"
        write_json(
            validate_path,
            {
                "mode": "validate",
                "queries": len(query_ids),
                "query_ids": query_ids,
                "mean_ap": {
                    condition: statistics.fmean(
                        rows[condition][q]["ap_reader"] for q in query_ids
                    )
                    for condition in READER_CONDITIONS
                },
                "rows": {
                    condition: [rows[condition][q] for q in query_ids]
                    for condition in READER_CONDITIONS
                },
                "path_provenance": path_provenance,
                "note": "Harness validation only; not a paper result.",
            },
        )
        print(f"[validate] wrote {validate_path}", flush=True)
        print(f"[validate] wall_total={time.monotonic()-started:.1f}s", flush=True)
        return 0

    # ---- Full-population scoring ----
    require(
        len(query_ids) == EXPECTED["target_queries"],
        f"full population requires {EXPECTED['target_queries']} queries",
    )

    # Join per-query rows across conditions + stored baselines.
    joined: list[dict[str, Any]] = []
    for query_id in query_ids:
        baseline_row = baselines[query_id]
        first = projections[query_id][0]
        entry: dict[str, Any] = {
            "query_id": query_id,
            "stratum": str(first["raw_fields"]["environment"]),
            "cluster": str(first["record_key"]),
            "operations": len(projections[query_id]),
            "targets": by_query_pos[query_id],
            "ap": {
                FULL: rows[FULL][query_id]["ap_reader"],
                SEM: rows[SEM][query_id]["ap_reader"],
                RAW: rows[RAW][query_id]["ap_reader"],
                DIRECT_ONLY: float(baseline_row["ap"][DIRECT_ONLY]),
                DIRECT_AGENTPROF: float(baseline_row["ap"][DIRECT_AGENTPROF]),
            },
            "full": rows[FULL][query_id],
            "semantic": rows[SEM][query_id],
            "raw": rows[RAW][query_id],
        }
        # Content-opened fraction vs the full-trace packet of the SAME query.
        full_chars = int(rows[FULL][query_id]["packet_chars"])
        for tag in ("semantic", "raw"):
            entry[tag]["content_opened_fraction"] = (
                entry[tag]["stage2_evidence_chars"] / full_chars
                if full_chars > 0
                else 0.0
            )
            entry[tag]["full_packet_chars"] = full_chars
        require(
            entry["stratum"] == str(baseline_row["stratum"]),
            f"{query_id}: stratum mismatch vs stored baseline",
        )
        joined.append(entry)

    map_scores = {
        condition: statistics.fmean(row["ap"][condition] for row in joined)
        for condition in ALL_CONDITIONS
    }
    for stored, expected_map in STORED_MAP.items():
        require(
            math.isclose(map_scores[stored], expected_map, abs_tol=1e-12),
            f"stored {stored} MAP reproduction failed: {map_scores[stored]}",
        )

    # Every pairwise delta among the 5 conditions (delta = first - second).
    comparisons: dict[str, Any] = {}
    for (first, second), seed in PAIR_SEEDS.items():
        boot = paired_bootstrap_deltas(
            joined,
            lambda row, a=first, b=second: row["ap"][a] - row["ap"][b],
            repetitions=BOOTSTRAP_REPS,
            seed=seed,
        )
        key = f"{first}__minus__{second}"
        comparisons[key] = {
            "first": first,
            "second": second,
            "point_effect": map_scores[first] - map_scores[second],
            "interval_95": boot["interval_95"],
            "median": boot["median"],
            "nonpositive_draws": boot["nonpositive_draws"],
            "repetitions": boot["repetitions"],
            "seed": boot["seed"],
            "strata": boot["strata"],
            "clusters": boot["clusters"],
        }
        write_json(out_dir / f"bootstrap-deltas-{key}.json", boot["draws"])

    # Content-efficiency decision metric (step-0081 review protocol):
    # paired raw - semantic deltas, 10,000 draws, seed 20260927.
    content_metrics = (
        "content_opened_fraction",
        "stage2_evidence_chars",
        "selected_evidence_operation_count",
    )
    content_deltas: dict[str, Any] = {}
    for metric in content_metrics:
        boot = paired_bootstrap_deltas(
            joined,
            lambda row, m=metric: row["raw"][m] - row["semantic"][m],
            repetitions=BOOTSTRAP_REPS,
            seed=CONTENT_DELTA_SEED,
        )
        content_deltas[metric] = {
            "direction": "raw_action_skeleton - semantic_skeleton",
            "point_effect": statistics.fmean(
                row["raw"][metric] - row["semantic"][metric] for row in joined
            ),
            "interval_95": boot["interval_95"],
            "median": boot["median"],
            "nonpositive_draws": boot["nonpositive_draws"],
            "repetitions": boot["repetitions"],
            "seed": boot["seed"],
        }
        write_json(out_dir / f"bootstrap-content-delta-{metric}.json", boot["draws"])

    def cost_block(condition: str, tag: str) -> dict[str, Any]:
        walls = [float(row[tag]["wall_seconds"]) for row in joined]
        chars = [int(row[tag]["total_chars"]) for row in joined]
        tokens = [int(row[tag]["prompt_tokens_o200k"]) for row in joined]
        return {
            "queries": len(joined),
            "total_wall_seconds": sum(walls),
            "mean_wall_seconds": statistics.fmean(walls),
            "median_wall_seconds": statistics.median(walls),
            "mean_total_chars": statistics.fmean(chars),
            "median_total_chars": statistics.median(chars),
            "total_chars": sum(chars),
            "mean_prompt_tokens_o200k": statistics.fmean(tokens),
            "median_prompt_tokens_o200k": statistics.median(tokens),
            "total_prompt_tokens_o200k": sum(tokens),
        }

    failure_tally = {
        "full_ok": sum(row["full"]["status"] == "ok" for row in joined),
        "full_ok_after_retry": sum(
            row["full"]["status"] == "ok_after_retry" for row in joined
        ),
        "full_original_order_failures": sum(
            row["full"]["scored_as_original_order_failure"] for row in joined
        ),
    }
    for tag in ("semantic", "raw"):
        failure_tally[f"{tag}_stage1_ok"] = sum(
            row[tag]["stage1_status"] == "ok" for row in joined
        )
        failure_tally[f"{tag}_stage1_ok_after_retry"] = sum(
            row[tag]["stage1_status"] == "ok_after_retry" for row in joined
        )
        failure_tally[f"{tag}_stage1_largest_groups_fallback"] = sum(
            row[tag]["stage1_largest_groups_fallback"] for row in joined
        )
        failure_tally[f"{tag}_stage2_ok"] = sum(
            row[tag]["stage2_status"] == "ok" for row in joined
        )
        failure_tally[f"{tag}_stage2_ok_after_retry"] = sum(
            row[tag]["stage2_status"] == "ok_after_retry" for row in joined
        )
        failure_tally[f"{tag}_stage2_original_order_failures"] = sum(
            row[tag]["stage2_scored_as_original_order_failure"] for row in joined
        )

    group_stats = {}
    for tag in ("semantic", "raw"):
        counts = [int(row[tag]["group_count"]) for row in joined]
        largest = [int(row[tag]["largest_group_size"]) for row in joined]
        opened = [float(row[tag]["content_opened_fraction"]) for row in joined]
        sel_ops = [int(row[tag]["selected_evidence_operation_count"]) for row in joined]
        group_stats[tag] = {
            "mean_group_count": statistics.fmean(counts),
            "median_group_count": statistics.median(counts),
            "mean_largest_group_size": statistics.fmean(largest),
            "median_largest_group_size": statistics.median(largest),
            "max_largest_group_size": max(largest),
            "mean_content_opened_fraction": statistics.fmean(opened),
            "median_content_opened_fraction": statistics.median(opened),
            "mean_selected_evidence_ops": statistics.fmean(sel_ops),
            "index_hit_rate": statistics.fmean(
                1.0 if row[tag]["index_hit"] else 0.0 for row in joined
            ),
            "index_hits": sum(1 for row in joined if row[tag]["index_hit"]),
        }

    summary = {
        "mode": args.mode,
        "benchmark": "HINTBench",
        **observed,
        "scored_target_queries": len(query_ids),
        "zero_positive_queries_consumed_but_excluded_from_map": len(clean_queries),
        "map": map_scores,
        "paired_comparisons": comparisons,
        "content_deltas_raw_minus_semantic": content_deltas,
        "failure_tally": failure_tally,
        "group_stats": group_stats,
        "bootstrap_seeds": {f"{a} - {b}": s for (a, b), s in PAIR_SEEDS.items()},
        "content_delta_seed": CONTENT_DELTA_SEED,
        "cost": {
            FULL: cost_block(FULL, "full"),
            SEM: cost_block(SEM, "semantic"),
            RAW: cost_block(RAW, "raw"),
        },
        "provenance": {
            "packets": str(args.packet_root.resolve()),
            "projection": str(args.projection.resolve()),
            "sources_test": str(args.sources_test.resolve()),
            "baseline_per_query": str(args.baseline_per_query.resolve()),
            "fixed_groups": str(args.group_mapping.resolve()),
            **path_provenance,
            "step_0072_conditions": {
                "Direct-only": "local_only",
                "Direct+AgentProf": "local_agentprof",
            },
        },
        "metric": (
            "sklearn.metrics.average_precision_score per target-bearing query; "
            "arithmetic MAP over the 400 target-bearing queries; paired "
            "trajectory-cluster bootstrap within HINTBench environment strata"
        ),
        "reader": {
            "cli": (
                "kimi -p <packet+instruction> -m kimi-code/k3 "
                "--output-format text --skills-dir <empty-dir>"
            ),
            "model": KIMI_MODEL,
            "cwd": "dedicated empty directory (no project context/skills loaded)",
            "one_format_retry_per_call": True,
            "fallbacks": (
                "stage-1 fail -> largest 5 groups; stage-2/full fail -> "
                "original-order ranking; all tallied"
            ),
            "model_family": "kimi (K3) — differs from the TraceElephant study "
            "(grok); disclosed, no cross-workload pooling",
            "query_specific": True,
            "workers": args.workers,
        },
        "wall_seconds_harness": time.monotonic() - started,
    }

    per_query_out = []
    for row in joined:
        per_query_out.append(
            {
                "query_id": row["query_id"],
                "stratum": row["stratum"],
                "cluster": row["cluster"],
                "operations": row["operations"],
                "targets": row["targets"],
                "ap": row["ap"],
                "full": row["full"],
                "semantic": row["semantic"],
                "raw": row["raw"],
            }
        )

    write_json(
        out_dir / "raw-results.json",
        {"per_query": per_query_out, "summary": summary},
    )
    write_json(out_dir / "summary.json", summary)
    print(
        f"[full] MAP full={map_scores[FULL]:.6f} sem={map_scores[SEM]:.6f} "
        f"raw={map_scores[RAW]:.6f} local_agentprof={map_scores[DIRECT_AGENTPROF]:.6f} "
        f"local_only={map_scores[DIRECT_ONLY]:.6f} "
        f"opened_sem={group_stats['semantic']['mean_content_opened_fraction']:.4f} "
        f"opened_raw={group_stats['raw']['mean_content_opened_fraction']:.4f} "
        f"hit_sem={group_stats['semantic']['index_hit_rate']:.4f} "
        f"hit_raw={group_stats['raw']['index_hit_rate']:.4f} "
        f"harness_wall={summary['wall_seconds_harness']:.1f}s",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ExperimentError as exc:
        print(f"[experiment-error] {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
