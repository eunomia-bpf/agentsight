#!/usr/bin/env python3
"""Profile-guided reader protocol v2 on TraceElephant (step 0082 / RQ2-RQ4).

COPY of step-0080 harness with ONLY two protocol changes:
  Change A — width-annotated stage-1 skeleton (ops mass; tokens if present)
  Change B — lean stage 2 (task + selected ops' source_summary only)

Compared against:
- step-0080 profile_reader
- step-0081 raw_action_reader
- step-0079 direct_reader
- step-0072 Direct+AgentProf (local_agentprof)
- step-0072 Direct-only (local_only)
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

import tiktoken
from sklearn.metrics import average_precision_score


REPO_ROOT = Path(__file__).resolve().parents[5]
TRACE_ROOT = REPO_ROOT / ".agentsight/experiments/traceelephant-rq2-v1"
PACKET_ROOT = REPO_ROOT / ".agentsight/experiments/rq2-a0-v1/full/trace/packets"
BASELINE_PER_QUERY = (
    REPO_ROOT
    / ".agentsight/experiments/rq2-current-agent-local-first-v1/full/per-query.jsonl"
)
GROUP_MAPPING = (
    REPO_ROOT
    / ".agentsight/experiments/rq2-canonical-tags-v2-current/trace/results"
    / "fixed-groups.jsonl"
)
GROUP_KEY = "source_preserving_agent"
STEP_0079_RAW = (
    REPO_ROOT
    / "docs/tmp/build-and-evaluate"
    / "step-0079-20260724T235753-0700/experiment-001/raw-results.json"
)
STEP_0080_RAW = (
    REPO_ROOT
    / "docs/tmp/build-and-evaluate"
    / "step-0080-20260725T004136-0700/experiment-001/raw-results.json"
)
STEP_0081_RAW = (
    REPO_ROOT
    / "docs/tmp/build-and-evaluate"
    / "step-0081-20260725T012438-0700/experiment-001/raw-results.json"
)
DEFAULT_OUT = Path(__file__).resolve().parent

DIRECT_ONLY = "local_only"
DIRECT_AGENTPROF = "local_agentprof"
DIRECT_READER = "direct_reader"
PROFILE_READER = "profile_reader"
RAW_ACTION_READER = "raw_action_reader"
PROFILE_READER_V2 = "profile_reader_v2"
BASELINE_KEYS = (
    PROFILE_READER,
    RAW_ACTION_READER,
    DIRECT_READER,
    DIRECT_AGENTPROF,
    DIRECT_ONLY,
)
BASELINE_DISPLAY = {
    PROFILE_READER: "Profile reader (step 0080)",
    RAW_ACTION_READER: "Raw-action reader (step 0081)",
    DIRECT_READER: "Direct reader (step 0079)",
    DIRECT_ONLY: "Direct-only",
    DIRECT_AGENTPROF: "Direct+AgentProf",
}

# Reuse prior seeds for shared baselines; new fixed seeds for 0080/0081.
BOOTSTRAP_SEEDS = {
    DIRECT_ONLY: 20260923,
    DIRECT_AGENTPROF: 20260924,
    DIRECT_READER: 20260925,
    PROFILE_READER: 20260926,
    RAW_ACTION_READER: 20260927,
}
BOOTSTRAP_REPS = 10000
MAX_SELECT_GROUPS = 5

# Published logical-token reference means (tiktoken o200k_base over stored packets).
REF_TOKENS_STEP0079 = 12615
REF_TOKENS_STEP0080 = 15991
REF_INDEX_HITS_STEP0080 = 154
REF_CONTENT_OPENED_STEP0080 = 0.53

# Additive width: frozen projection/packets expose no per-op token mass
# (projection has no token field; pprof count value is 1/op). Documented.
ADDITIVE_MEASURE = "operation_count"
ADDITIVE_MEASURE_NOTE = (
    "Frozen projection.jsonl and source packets expose no per-operation token "
    "mass field; pprof count units equal 1 per operation. Group additive mass "
    "is therefore member operation count only (ops=N)."
)

TIKTOKEN_ENCODING = "o200k_base"
_TOKEN_ENCODER = None


def token_encoder():
    global _TOKEN_ENCODER
    if _TOKEN_ENCODER is None:
        _TOKEN_ENCODER = tiktoken.get_encoding(TIKTOKEN_ENCODING)
    return _TOKEN_ENCODER


STAGE1_INSTRUCTION = """You are diagnosing which groups of operations in an agent trajectory are most likely to contain the decisive mistake responsible for the agent's failure or incorrect solution.

You receive:
1) the original task text the agent was solving, and
2) a profile skeleton: every source operation with its stable operation_id, ordinal, and its frozen semantic operation path, already grouped by full path (path prefix groups). NO source content is provided.

Rules:
- Use only the provided task text and the profile skeleton (operation IDs, ordinals, semantic paths).
- Do not invent group paths or operation IDs.
- Select up to 5 groups (path prefixes / full group paths) most likely to contain the decisive mistake.
- Prefer groups whose semantic path suggests the failure mode for this task; when unsure, prefer larger groups that still look relevant.
- Return ONLY strict JSON with this exact shape and no other text:
{"selected_group_paths": [["path_component_1", "path_component_2", ...], ...]}
Each selected path must exactly match one of the group_path arrays in the packet.
"""

STAGE1_RETRY = """Your previous reply was not valid strict JSON with key selected_group_paths listing known group_path arrays.
Reply again with ONLY valid JSON of the form:
{"selected_group_paths": [["comp1", "comp2", ...], ...]}
Select at most 5 groups. Do not include markdown fences or commentary.
"""

# Change B: lean stage-2 instruction — rank opened operation IDs only.
STAGE2_INSTRUCTION = """You are diagnosing which operations in an agent trajectory are responsible for the agent's failure or incorrect solution on the assigned task.

You receive:
1) the original task text, and
2) source-visible content (source_summary) for ONLY the operations in previously selected groups. Each opened operation has its operation_id, ordinal, and source_summary. NO full profile skeleton is provided; unopened operations are not listed.

Rules:
- Use only the provided task text and the attached opened operations' source_summary evidence.
- Do not invent operation IDs. Every ranked ID must appear exactly among the opened operations.
- Rank the opened operation IDs by how likely each is responsible for the failure/incorrect outcome (most likely first).
- Cover at least every opened operation you consider plausibly responsible.
- Return ONLY strict JSON with this exact shape and no other text:
{"ranked_operation_ids": ["operation_id_most_likely", "operation_id_next", ...]}
"""

STAGE2_RETRY = """Your previous reply was not valid strict JSON with key ranked_operation_ids listing known opened operation_id strings.
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


def stored_packet_text(packet: Mapping[str, Any]) -> str:
    """Serialize exactly as write_json (indent=2, sort_keys) for token accounting."""
    return json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def packet_char_count(packet: Mapping[str, Any]) -> int:
    # Match step-0080: compact sort_keys dump for char metric continuity.
    return len(json.dumps(packet, ensure_ascii=False, sort_keys=True))


def packet_token_count(packet: Mapping[str, Any]) -> int:
    """Logical tokens over the stored packet form (tiktoken o200k_base)."""
    return len(token_encoder().encode(stored_packet_text(packet)))


def load_packets(packet_root: Path) -> dict[str, dict[str, Any]]:
    sessions: dict[str, dict[str, Any]] = {}
    for path in sorted(packet_root.glob("batch-*.json")):
        payload = read_json(path)
        for session in payload["sessions"]:
            sequence = str(session["sequence"])
            require(sequence not in sessions, f"duplicate packet sequence {sequence}")
            sessions[sequence] = session
    require(len(sessions) == 220, f"expected 220 packets, got {len(sessions)}")
    return sessions


def load_projections(trace_root: Path) -> dict[str, list[dict[str, Any]]]:
    by_query: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in read_jsonl(trace_root / "operations" / "projection.jsonl"):
        by_query[str(row["trace_id"])].append(row)
    for query_id, rows in by_query.items():
        rows.sort(key=lambda item: (int(item["step_id"]), str(item["operation_id"])))
        by_query[query_id] = rows
    require(len(by_query) == 220, f"expected 220 trajectories, got {len(by_query)}")
    require(
        sum(len(rows) for rows in by_query.values()) == 5960,
        "expected 5960 operations",
    )
    return by_query


def load_targets(trace_root: Path) -> dict[str, int]:
    targets = {
        str(row["trace_id"]): int(row["mistake_step"])
        for row in read_jsonl(trace_root / "scorer" / "targets.jsonl")
    }
    require(len(targets) == 220, f"expected 220 targets, got {len(targets)}")
    return targets


def load_baseline_aps(path: Path) -> dict[str, dict[str, Any]]:
    rows = {}
    for row in read_jsonl(path):
        if row.get("benchmark") != "TraceElephant":
            continue
        query_id = str(row["query_id"])
        require(query_id not in rows, f"duplicate baseline query {query_id}")
        rows[query_id] = row
    require(len(rows) == 220, f"expected 220 baseline rows, got {len(rows)}")
    return rows


def load_stored_reader_aps(path: Path, method_key: str) -> dict[str, dict[str, Any]]:
    payload = read_json(path)
    out: dict[str, dict[str, Any]] = {}
    for row in payload["per_query"]:
        query_id = str(row["query_id"])
        require(query_id not in out, f"duplicate {method_key} query {query_id}")
        out[query_id] = row
    require(len(out) == 220, f"expected 220 {method_key} rows, got {len(out)}")
    return out


def load_group_mapping(path: Path) -> dict[str, list[str]]:
    """operation_id -> source_preserving_agent path (list of components)."""
    require(path.is_file(), f"group mapping not found: {path}")
    mapping: dict[str, list[str]] = {}
    by_sequence: dict[str, int] = defaultdict(int)
    for row in read_jsonl(path):
        operation_id = str(row["operation_id"])
        groups = row.get("groups") or {}
        require(
            GROUP_KEY in groups,
            f"{operation_id}: missing {GROUP_KEY} in frozen group mapping",
        )
        path_parts = [str(part) for part in groups[GROUP_KEY]]
        require(bool(path_parts), f"{operation_id}: empty semantic path")
        require(operation_id not in mapping, f"duplicate operation_id {operation_id}")
        mapping[operation_id] = path_parts
        by_sequence[str(row["sequence"])] += 1
    require(len(mapping) == 5960, f"expected 5960 mapped ops, got {len(mapping)}")
    require(len(by_sequence) == 220, f"expected 220 sequences, got {len(by_sequence)}")
    return mapping


def detect_token_mass_available(
    projection_rows: Sequence[Mapping[str, Any]],
    session: Mapping[str, Any],
) -> bool:
    """True only if a numeric per-op token field is already exposed."""
    token_keys = (
        "tokens",
        "token_mass",
        "token_count",
        "prompt_tokens",
        "input_tokens",
        "total_tokens",
        "additive_tokens",
    )
    for row in projection_rows[:5]:
        for key in token_keys:
            if key in row and isinstance(row[key], (int, float)):
                return True
        raw = row.get("raw_fields") or {}
        if isinstance(raw, dict):
            for key in token_keys:
                if key in raw and isinstance(raw[key], (int, float)):
                    return True
    for op in session["operations"][:5]:
        for key in token_keys:
            if key in op and isinstance(op[key], (int, float)):
                return True
        summary = op.get("source_summary")
        if isinstance(summary, dict):
            for key in token_keys:
                if key in summary and isinstance(summary[key], (int, float)):
                    return True
    return False


def build_skeleton(
    session: Mapping[str, Any],
    op_paths: Mapping[str, Sequence[str]],
) -> dict[str, Any]:
    """Profile skeleton: ops + groups by full semantic path. No source content."""
    operations: list[dict[str, Any]] = []
    groups_map: dict[str, dict[str, Any]] = {}
    for op in session["operations"]:
        operation_id = str(op["operation_id"])
        ordinal = int(op["ordinal"])
        require(operation_id in op_paths, f"unmapped operation {operation_id}")
        semantic_path = list(op_paths[operation_id])
        operations.append(
            {
                "operation_id": operation_id,
                "ordinal": ordinal,
                "semantic_path": semantic_path,
            }
        )
        key = path_key(semantic_path)
        if key not in groups_map:
            groups_map[key] = {
                "group_path": semantic_path,
                "path_key": key,
                "member_ordinals": [],
                "member_operation_ids": [],
            }
        groups_map[key]["member_ordinals"].append(ordinal)
        groups_map[key]["member_operation_ids"].append(operation_id)

    groups = sorted(
        groups_map.values(),
        key=lambda g: (-len(g["member_operation_ids"]), g["path_key"]),
    )
    return {
        "task": str(session["task"]),
        "operation_count": len(operations),
        "group_count": len(groups),
        "operations": operations,
        "groups": groups,
    }


def annotate_group_widths(group: Mapping[str, Any]) -> dict[str, Any]:
    """Change A: attach member count / additive mass; tokens omitted when absent."""
    ops = len(group["member_operation_ids"])
    # pprof count mass == member operation count (value 1 per op).
    additive_mass = ops
    width_bracket = f"[ops={ops}]"
    members_part = (
        "members: ordinals="
        + ",".join(str(x) for x in group["member_ordinals"])
        + " ids="
        + ",".join(str(x) for x in group["member_operation_ids"])
    )
    group_line = f"{group['path_key']}  {width_bracket}  {members_part}"
    return {
        "group_path": list(group["group_path"]),
        "path_key": group["path_key"],
        "member_ordinals": list(group["member_ordinals"]),
        "member_operation_ids": list(group["member_operation_ids"]),
        "member_count": ops,
        "ops": ops,
        "additive_mass": additive_mass,
        "additive_measure": ADDITIVE_MEASURE,
        "width_annotation": width_bracket,
        "group_line": group_line,
    }


def build_stage1_packet(skeleton: Mapping[str, Any]) -> dict[str, Any]:
    """Change A: width-annotated groups; still no source content."""
    annotated_groups = [annotate_group_widths(g) for g in skeleton["groups"]]
    return {
        "task": skeleton["task"],
        "operation_count": skeleton["operation_count"],
        "group_count": skeleton["group_count"],
        "additive_measure": ADDITIVE_MEASURE,
        "additive_measure_note": ADDITIVE_MEASURE_NOTE,
        "groups": annotated_groups,
        # Compact per-op listing without source content.
        "operations": skeleton["operations"],
        # Human-readable width lines (same info as groups[*].group_line).
        "group_lines": [g["group_line"] for g in annotated_groups],
    }


def build_stage2_packet(
    skeleton: Mapping[str, Any],
    session: Mapping[str, Any],
    selected_paths: Sequence[Sequence[str]],
) -> dict[str, Any]:
    """Change B: lean stage 2 — task + opened ops only (no skeleton re-send)."""
    selected_keys = {path_key(p) for p in selected_paths}
    selected_ids: set[str] = set()
    for group in skeleton["groups"]:
        if group["path_key"] in selected_keys:
            selected_ids.update(group["member_operation_ids"])

    opened: list[dict[str, Any]] = []
    for op in session["operations"]:
        operation_id = str(op["operation_id"])
        if operation_id not in selected_ids:
            continue
        opened.append(
            {
                "operation_id": operation_id,
                "ordinal": int(op["ordinal"]),
                "source_summary": op.get("source_summary"),
            }
        )
    # Change B: ONLY task + opened ops (id/ordinal/source_summary). No skeleton,
    # no unopened paths, no selected_group_paths in the model-visible packet.
    return {
        "task": skeleton["task"],
        "opened_operations": opened,
    }


def build_prompt(instruction: str, packet: Mapping[str, Any], extra: str = "") -> str:
    body = json.dumps(packet, ensure_ascii=False, sort_keys=True)
    parts = [instruction.strip(), "", "Evidence packet:", body]
    if extra:
        parts.extend(["", extra.strip()])
    return "\n".join(parts)


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


def nearest_interval(values: Sequence[float]) -> list[float]:
    ordered = sorted(float(value) for value in values)
    require(bool(ordered), "empty bootstrap")
    lower = math.ceil(0.025 * len(ordered)) - 1
    upper = math.ceil(0.975 * len(ordered)) - 1
    return [ordered[lower], ordered[upper]]


def paired_bootstrap(
    query_rows: Sequence[Mapping[str, Any]],
    reader_key: str,
    baseline_key: str,
    repetitions: int,
    seed: int,
) -> dict[str, Any]:
    by_stratum: defaultdict[str, defaultdict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in query_rows:
        delta = float(row["ap"][reader_key]) - float(row["ap"][baseline_key])
        by_stratum[str(row["stratum"])][str(row["cluster"])].append(delta)
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
        "baseline": baseline_key,
        "baseline_display": BASELINE_DISPLAY[baseline_key],
        "repetitions": repetitions,
        "seed": seed,
        "strata": len(by_stratum),
        "clusters": sum(len(value) for value in by_stratum.values()),
        "interval_95": nearest_interval(draws),
        "median": statistics.median(draws),
        "nonpositive_draws": sum(value <= 0.0 for value in draws),
        "draws": draws,
    }


def call_grok(
    prompt: str,
    timeout_s: int = 600,
    prompt_file: Path | None = None,
) -> tuple[str, float, dict[str, Any]]:
    started = time.monotonic()
    use_file = prompt_file is not None or len(prompt.encode("utf-8")) > 100_000
    tmp_path: Path | None = None
    try:
        if use_file:
            if prompt_file is None:
                import tempfile

                handle = tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    suffix=".prompt.txt",
                    delete=False,
                )
                handle.write(prompt)
                handle.close()
                tmp_path = Path(handle.name)
                prompt_path = tmp_path
            else:
                prompt_file.write_text(prompt, encoding="utf-8")
                prompt_path = prompt_file
            cmd = [
                "grok",
                "--prompt-file",
                str(prompt_path),
                "--output-format",
                "plain",
                "--max-turns",
                "3",
                "--tools",
                "",
                "--no-subagents",
                "--verbatim",
            ]
            cmd_meta = cmd[:2] + ["<prompt-file>", *cmd[3:]]
            delivery = "prompt-file"
        else:
            cmd = [
                "grok",
                "-p",
                prompt,
                "--output-format",
                "plain",
                "--max-turns",
                "3",
                "--tools",
                "",
                "--no-subagents",
                "--verbatim",
            ]
            cmd_meta = cmd[:2] + ["<prompt>", *cmd[3:]]
            delivery = "p-flag"
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        wall = time.monotonic() - started
        stdout = proc.stdout or ""
        meta = {
            "returncode": proc.returncode,
            "stderr_tail": (proc.stderr or "")[-4000:],
            "cmd": cmd_meta,
            "delivery": delivery,
            "prompt_bytes": len(prompt.encode("utf-8")),
        }
        if proc.returncode != 0 and not stdout.strip():
            raise ExperimentError(
                f"grok failed rc={proc.returncode}: {(proc.stderr or stdout)[:1000]}"
            )
        return stdout, wall, meta
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass


def safe_query_filename(query_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", query_id)


def run_stage(
    instruction: str,
    retry_instruction: str,
    packet: Mapping[str, Any],
    parse_fn,
    parse_kwargs: Mapping[str, Any],
) -> tuple[Any, str, bool, float, list[dict[str, Any]]]:
    """Two attempts; returns (parsed, status, failed, wall, attempts)."""
    attempts: list[dict[str, Any]] = []
    wall_s = 0.0
    parsed = None
    status = "failure"
    failed = True
    for attempt_idx in range(2):
        extra = "" if attempt_idx == 0 else retry_instruction
        prompt = build_prompt(instruction, packet, extra=extra)
        try:
            raw_text, wall, meta = call_grok(prompt)
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


def index_hit(
    selected_paths: Sequence[Sequence[str]],
    target_operation_ids: Sequence[str],
    op_paths: Mapping[str, Sequence[str]],
) -> bool:
    """Step-0080 analysis-001: every target op's group is among selected groups."""
    sel_set = {tuple(p) for p in selected_paths}
    target_groups = [tuple(op_paths[oid]) for oid in target_operation_ids]
    return all(g in sel_set for g in target_groups)


def process_one_query(
    query_id: str,
    session: Mapping[str, Any],
    projection_rows: Sequence[Mapping[str, Any]],
    target_step: int,
    baseline_row: Mapping[str, Any],
    direct_reader_row: Mapping[str, Any],
    profile_reader_row: Mapping[str, Any],
    raw_action_row: Mapping[str, Any],
    op_paths: Mapping[str, Sequence[str]],
    out_dir: Path,
    force: bool = False,
) -> dict[str, Any]:
    stage1_dir = out_dir / "packets-stage1"
    stage2_dir = out_dir / "packets-stage2"
    responses_dir = out_dir / "raw-responses"
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
        1 if int(row["step_id"]) == int(target_step) else 0 for row in projection_rows
    ]
    require(sum(labels) == 1, f"{query_id}: expected exactly one target operation")

    # Document that token mass is not present (checked once per trajectory).
    require(
        not detect_token_mass_available(projection_rows, session),
        f"{query_id}: unexpected token mass field; update additive measure handling",
    )

    skeleton = build_skeleton(session, op_paths)
    stage1_packet = build_stage1_packet(skeleton)
    write_json(stage1_path, stage1_packet)
    stage1_chars = packet_char_count(stage1_packet)
    stage1_tokens = packet_token_count(stage1_packet)
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
        if stage2_path.exists():
            stage2_packet = read_json(stage2_path)
        else:
            stage2_packet = build_stage2_packet(skeleton, session, selected_paths)
            write_json(stage2_path, stage2_packet)
        stage2_chars = packet_char_count(stage2_packet)
        stage2_tokens = packet_token_count(stage2_packet)
    else:
        # ---- Stage 1 ----
        selected_paths, stage1_status, stage1_failed, stage1_wall, attempts_stage1 = (
            run_stage(
                STAGE1_INSTRUCTION,
                STAGE1_RETRY,
                stage1_packet,
                parse_selected_groups,
                {"valid_paths": valid_paths},
            )
        )
        stage1_fallback = False
        if stage1_failed or selected_paths is None:
            selected_paths = largest_groups_fallback(skeleton["groups"])
            stage1_status = "failure_largest_groups_fallback"
            stage1_fallback = True

        # ---- Stage 2 (lean) ----
        stage2_packet = build_stage2_packet(skeleton, session, selected_paths)
        write_json(stage2_path, stage2_packet)
        stage2_chars = packet_char_count(stage2_packet)
        stage2_tokens = packet_token_count(stage2_packet)

        opened_ids = [
            str(op["operation_id"]) for op in stage2_packet["opened_operations"]
        ]
        # Fallback valid set: if no groups selected somehow, nothing to rank.
        parse_ids = opened_ids if opened_ids else original_ids
        selected_evidence_operation_count = len(opened_ids)

        ranked, stage2_status, stage2_failure, stage2_wall, attempts_stage2 = run_stage(
            STAGE2_INSTRUCTION,
            STAGE2_RETRY,
            stage2_packet,
            parse_ranked_ids,
            {"valid_ids": parse_ids},
        )
        if stage2_failure or ranked is None:
            ranking = list(original_ids)
            stage2_status = "failure_original_order"
            stage2_failure = True
        else:
            # Deterministic completion: append unopened in original trace order.
            ranking = complete_ranking(ranked, original_ids)

        wall_s = stage1_wall + stage2_wall
        record = {
            "query_id": query_id,
            "selected_group_paths": selected_paths,
            "selected_group_path_keys": [path_key(p) for p in selected_paths],
            "stage1_status": stage1_status,
            "stage1_largest_groups_fallback": stage1_fallback,
            "stage1_wall_seconds": stage1_wall,
            "stage1_chars": stage1_chars,
            "stage1_tokens": stage1_tokens,
            "stage1_attempts": attempts_stage1,
            "stage2_status": stage2_status,
            "stage2_scored_as_original_order_failure": stage2_failure,
            "stage2_wall_seconds": stage2_wall,
            "stage2_chars": stage2_chars,
            "stage2_tokens": stage2_tokens,
            "stage2_attempts": attempts_stage2,
            "reader_ranked_operation_ids": (
                attempts_stage2[-1]["parsed"] if attempts_stage2 else None
            ),
            "completed_ranking": ranking,
            "wall_seconds_total": wall_s,
            "operation_count": len(original_ids),
            "group_count": skeleton["group_count"],
            "selected_evidence_operation_count": selected_evidence_operation_count,
            "step0079_packet_chars": int(direct_reader_row["packet_chars"]),
            "additive_measure": ADDITIVE_MEASURE,
            "protocol": "profile_reader_v2_lean_width",
        }
        write_json(response_path, record)

    selected_evidence_operation_count = len(stage2_packet.get("opened_operations", []))
    total_chars = stage1_chars + stage2_chars
    total_tokens = stage1_tokens + stage2_tokens
    step0079_chars = int(direct_reader_row["packet_chars"])
    # Content-opened fraction: stage-2 evidence payload / step-0079 full packet.
    # Match step-0080: evidence-only wrapper over the opened source_summary list.
    evidence_only = {
        "selected_evidence": [
            {
                "operation_id": op["operation_id"],
                "ordinal": op["ordinal"],
                "source_summary": op.get("source_summary"),
            }
            for op in stage2_packet.get("opened_operations", [])
        ]
    }
    stage2_evidence_chars = packet_char_count(evidence_only)
    content_opened_fraction = (
        stage2_evidence_chars / step0079_chars if step0079_chars > 0 else 0.0
    )

    scores = ranking_to_scores(ranking)
    score_vector = [scores[operation_id] for operation_id in original_ids]
    ap_reader = standard_ap(labels, score_vector)

    target_operation_ids = [
        str(row["operation_id"])
        for row in projection_rows
        if int(row["step_id"]) == int(target_step)
    ]
    stratum = str(baseline_row["stratum"])
    cluster = str(baseline_row["cluster"])
    if not stratum:
        stratum = str(projection_rows[0]["cell"])
    if not cluster:
        cluster = query_id

    hit = index_hit(selected_paths, target_operation_ids, op_paths)

    return {
        "query_id": query_id,
        "stratum": stratum,
        "cluster": cluster,
        "operations": len(original_ids),
        "group_count": skeleton["group_count"],
        "targets": sum(labels),
        "target_operation_ids": target_operation_ids,
        "selected_group_paths": selected_paths,
        "index_hit": hit,
        "selected_evidence_operation_count": selected_evidence_operation_count,
        "stage1_chars": stage1_chars,
        "stage2_chars": stage2_chars,
        "stage2_evidence_chars": stage2_evidence_chars,
        "total_chars": total_chars,
        "stage1_tokens": stage1_tokens,
        "stage2_tokens": stage2_tokens,
        "total_tokens": total_tokens,
        "step0079_packet_chars": step0079_chars,
        "content_opened_fraction": content_opened_fraction,
        "wall_seconds": wall_s,
        "stage1_wall_seconds": stage1_wall,
        "stage2_wall_seconds": stage2_wall,
        "stage1_status": stage1_status,
        "stage2_status": stage2_status,
        "stage1_largest_groups_fallback": stage1_fallback,
        "stage2_scored_as_original_order_failure": stage2_failure,
        "ap": {
            PROFILE_READER_V2: ap_reader,
            PROFILE_READER: float(profile_reader_row["ap"][PROFILE_READER]),
            RAW_ACTION_READER: float(raw_action_row["ap"][RAW_ACTION_READER]),
            DIRECT_READER: float(direct_reader_row["ap"][DIRECT_READER]),
            DIRECT_ONLY: float(baseline_row["ap"][DIRECT_ONLY]),
            DIRECT_AGENTPROF: float(baseline_row["ap"][DIRECT_AGENTPROF]),
        },
        "reader_rank_of_target": min(
            (ranking.index(oid) + 1 for oid in target_operation_ids), default=None
        ),
        "additive_measure": ADDITIVE_MEASURE,
    }


def render_results_md(summary: Mapping[str, Any]) -> str:
    map_scores = summary["map"]
    cost = summary["cost"]
    targets = summary["registered_targets"]
    lines = [
        "# Results: profile-guided reader v2 on TraceElephant (RQ2/RQ4)",
        "",
        "## Scientific question",
        "",
        "Does protocol v2 (width-annotated stage-1 skeleton + lean stage-2,",
        "no skeleton re-send) retain ranking quality while reducing logical",
        "input tokens below the full-trace reader and content opened ≤ step 0080?",
        "",
        "## Population",
        "",
        f"- Workload: TraceElephant complete RQ2 collection",
        f"- Trajectories / target-bearing queries scored: {summary['target_bearing_queries']}",
        f"- Operations: {summary['operations']}",
        f"- Zero-positive trajectories: {summary['zero_positive_queries']} (excluded from MAP)",
        "",
        "## Input provenance (read-only, frozen)",
        "",
        f"- Source-only packets: `{summary['provenance']['packets']}`",
        f"- Operation projections / stable IDs: `{summary['provenance']['projections']}`",
        f"- Annotated targets (mistake_step): `{summary['provenance']['targets']}`",
        f"- Stored Direct-only / Direct+AgentProf per-query AP: `{summary['provenance']['baseline_per_query']}`",
        f"  (Direct-only = `local_only`, Direct+AgentProf = `local_agentprof`)",
        f"- Step 0079 direct_reader: `{summary['provenance']['step_0079_raw']}`",
        f"- Step 0080 profile_reader: `{summary['provenance']['step_0080_raw']}`",
        f"- Step 0081 raw_action_reader: `{summary['provenance']['step_0081_raw']}`",
        f"- **Frozen Agent+Evidence group mapping**: `{summary['provenance']['group_mapping']}`",
        f"  (key `{summary['provenance']['group_key']}`)",
        f"- Scoring: sklearn non-interpolated `average_precision_score`; arithmetic MAP",
        f"- Paired bootstrap: 10,000 trajectory-cluster resamples within strata; seeds {summary['bootstrap_seeds']}",
        f"- Logical tokens: tiktoken `{TIKTOKEN_ENCODING}` over stored packet JSON (indent=2, sort_keys)",
        "",
        "## Protocol changes vs step 0080",
        "",
        "### Change A — width-annotated stage 1",
        "",
        "- Each group carries member operation count and additive mass.",
        f"- Additive measure used: **`{ADDITIVE_MEASURE}`**.",
        f"- {ADDITIVE_MEASURE_NOTE}",
        "- Format: `<path>  [ops=N]  members: ordinals=... ids=...` in `group_line` / `group_lines`.",
        "- Stage-1 instruction unchanged: select up to 5 groups, ordered, strict JSON.",
        "",
        "### Change B — lean stage 2",
        "",
        "- Packet contains ONLY: task text + opened operations"
        " (`operation_id`, `ordinal`, `source_summary`).",
        "- NO skeleton re-send; NO paths for unopened operations.",
        "- Instruction: rank opened operation IDs; deterministic completion appends",
        "  unopened ops in original trace order (identical to step 0080 completion).",
        "",
        "## Registered targets (from 000-step-entry.md)",
        "",
        f"| Target | Threshold | Measured | Met? |",
        f"|---|---:|---:|:---:|",
        f"| MAP | ≥ {targets['map_threshold']:.2f} | {map_scores[PROFILE_READER_V2]:.6f} | "
        f"{'YES' if targets['map_met'] else 'NO'} |",
        f"| Mean total logical tokens / query | < {targets['tokens_threshold']} | "
        f"{cost['mean_total_tokens']:.1f} | "
        f"{'YES' if targets['tokens_met'] else 'NO'} |",
        f"| Mean content-opened fraction | ≤ {targets['content_opened_threshold']:.0%} | "
        f"{cost['mean_content_opened_fraction']:.4f} | "
        f"{'YES' if targets['content_opened_met'] else 'NO'} |",
        "",
        f"- All three registered targets met: **{'YES' if targets['all_met'] else 'NO'}**",
        "",
        "## MAP",
        "",
        "| Method | MAP |",
        "|---|---:|",
        f"| Profile reader v2 (this experiment) | {map_scores[PROFILE_READER_V2]:.6f} |",
        f"| Profile reader (step 0080) | {map_scores[PROFILE_READER]:.6f} |",
        f"| Raw-action reader (step 0081) | {map_scores[RAW_ACTION_READER]:.6f} |",
        f"| Direct reader (step 0079) | {map_scores[DIRECT_READER]:.6f} |",
        f"| Direct+AgentProf (stored) | {map_scores[DIRECT_AGENTPROF]:.6f} |",
        f"| Direct-only (stored) | {map_scores[DIRECT_ONLY]:.6f} |",
        "",
        "## Paired differences (profile_reader_v2 − baseline)",
        "",
        "| Baseline | Point ΔMAP | 95% interval | Nonpositive draws / 10000 |",
        "|---|---:|---:|---:|",
    ]
    for key in BASELINE_KEYS:
        cmp_ = summary["paired_comparisons"][key]
        lo, hi = cmp_["interval_95"]
        lines.append(
            f"| {BASELINE_DISPLAY[key]} | {cmp_['point_effect']:+.6f} | "
            f"[{lo:+.6f}, {hi:+.6f}] | {cmp_['nonpositive_draws']} |"
        )

    idx = summary["index_hit"]
    lines.extend(
        [
            "",
            "## Index-hit rate (step-0080 analysis-001 definition)",
            "",
            "Hit = every target operation's group is among the ≤5 selected groups.",
            "",
            f"| Run | Hits / 220 | Rate |",
            f"|---|---:|---:|",
            f"| Profile reader v2 (this) | {idx['hits']}/220 | {idx['rate']:.4f} |",
            f"| Profile reader (step 0080) | {idx['step0080_hits']}/220 | "
            f"{idx['step0080_rate']:.4f} |",
            "",
            "## Failure tally",
            "",
            f"- Stage-1 largest-groups fallbacks: {summary['failure_tally']['stage1_largest_groups_fallback']}",
            f"- Stage-1 OK first attempt: {summary['failure_tally']['stage1_ok']}",
            f"- Stage-1 OK after retry: {summary['failure_tally']['stage1_ok_after_retry']}",
            f"- Stage-2 original-order failures: {summary['failure_tally']['stage2_original_order_failures']}",
            f"- Stage-2 OK first attempt: {summary['failure_tally']['stage2_ok']}",
            f"- Stage-2 OK after retry: {summary['failure_tally']['stage2_ok_after_retry']}",
            "",
            "## Cost — logical tokens (tiktoken o200k_base over stored packets)",
            "",
            "| Metric | Profile reader v2 | Step 0080 two-stage | Step 0079 full-trace |",
            "|---|---:|---:|---:|",
            f"| Mean total tokens / query | {cost['mean_total_tokens']:.1f} | "
            f"{REF_TOKENS_STEP0080} | {REF_TOKENS_STEP0079} |",
            f"| Median total tokens / query | {cost['median_total_tokens']:.1f} | — | — |",
            f"| Mean stage-1 tokens | {cost['mean_stage1_tokens']:.1f} | 4837 | — |",
            f"| Mean stage-2 tokens | {cost['mean_stage2_tokens']:.1f} | 11154 | — |",
            "",
            f"- Ratio vs step-0079 full-trace mean: "
            f"**{cost['mean_total_tokens'] / REF_TOKENS_STEP0079:.3f}x**",
            f"- Ratio vs step-0080 two-stage mean: "
            f"**{cost['mean_total_tokens'] / REF_TOKENS_STEP0080:.3f}x**",
            "",
            "## Cost — characters / content opened (same definition as step 0080)",
            "",
            "| Metric | Profile reader v2 | Direct reader (0079) |",
            "|---|---:|---:|",
            f"| Queries | {cost['queries']} | {summary['cost_step0079']['queries']} |",
            f"| Mean total chars / query | {cost['mean_total_chars']:.1f} | "
            f"{summary['cost_step0079']['mean_packet_chars']:.1f} |",
            f"| Median total chars / query | {cost['median_total_chars']:.1f} | — |",
            f"| Mean stage-1 chars | {cost['mean_stage1_chars']:.1f} | — |",
            f"| Mean stage-2 chars | {cost['mean_stage2_chars']:.1f} | — |",
            f"| Mean stage-2 evidence-only chars | {cost['mean_stage2_evidence_chars']:.1f} | — |",
            f"| Mean wall seconds / query | {cost['mean_wall_seconds']:.2f} | "
            f"{summary['cost_step0079']['mean_wall_seconds']:.2f} |",
            f"| Median wall seconds / query | {cost['median_wall_seconds']:.2f} | "
            f"{summary['cost_step0079']['median_wall_seconds']:.2f} |",
            f"| Total wall seconds (sum) | {cost['total_wall_seconds']:.2f} | "
            f"{summary['cost_step0079']['total_wall_seconds']:.2f} |",
            "",
            f"- Mean content-opened fraction (stage-2 evidence chars / step-0079 full packet chars): "
            f"**{cost['mean_content_opened_fraction']:.4f}**",
            f"- Median content-opened fraction: {cost['median_content_opened_fraction']:.4f}",
            f"- Step-0080 mean content-opened fraction (reference): {REF_CONTENT_OPENED_STEP0080:.2f}",
            f"- Mean selected evidence operations / query: {cost['mean_selected_evidence_ops']:.2f}",
            f"- Mean groups available / query: {cost['mean_group_count']:.2f}",
            "",
            "## Honest interpretation",
            "",
        ]
    )
    pr = map_scores[PROFILE_READER_V2]
    lines.append(
        f"On the complete TraceElephant population (n={summary['target_bearing_queries']}), "
        f"profile-guided reader v2 achieves MAP={pr:.4f}. "
        f"Step-0080 profile reader MAP is {map_scores[PROFILE_READER]:.4f}; "
        f"step-0081 raw-action reader is {map_scores[RAW_ACTION_READER]:.4f}; "
        f"step-0079 full-trace direct reader is {map_scores[DIRECT_READER]:.4f}; "
        f"stored Direct+AgentProf is {map_scores[DIRECT_AGENTPROF]:.4f} and "
        f"Direct-only is {map_scores[DIRECT_ONLY]:.4f}."
    )
    lines.append("")
    for key in BASELINE_KEYS:
        cmp_ = summary["paired_comparisons"][key]
        lo, hi = cmp_["interval_95"]
        lines.append(
            f"Versus {BASELINE_DISPLAY[key]}, the paired point difference is "
            f"{cmp_['point_effect']:+.4f} with 95% interval [{lo:+.4f}, {hi:+.4f}]."
        )
    lines.append("")
    lines.append(
        f"Mean logical input is {cost['mean_total_tokens']:.0f} tokens/query "
        f"(stage-1 {cost['mean_stage1_tokens']:.0f} + stage-2 {cost['mean_stage2_tokens']:.0f}) "
        f"versus step-0079 full-trace {REF_TOKENS_STEP0079} and step-0080 two-stage "
        f"{REF_TOKENS_STEP0080}. Mean content opened is "
        f"{cost['mean_content_opened_fraction']:.1%} of the step-0079 full packet "
        f"character volume. Index-hit rate is {idx['hits']}/220 "
        f"versus step-0080's {idx['step0080_hits']}/220."
    )
    lines.append("")
    if not targets["all_met"]:
        lines.append(
            "Registered targets were not all met. Under the no-negative-results policy "
            "this remains an iteration step: findings feed protocol v3 rather than any "
            "paper claim."
        )
    else:
        lines.append(
            "All three registered targets were met on the complete population."
        )
    lines.append("")
    lines.append(
        "This measures whether width annotations and a lean stage-2 packet improve "
        "the once-built Agent+Evidence index protocol relative to step 0080. It does "
        "not evaluate a different grouping construction, multi-query reuse, or models "
        "other than the grok CLI reader used in steps 0079–0081."
    )
    lines.append("")
    lines.append(
        "This file reports the complete population run only. The ≤3-query harness "
        "validation is not a paper result."
    )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=("validate", "full", "score-only"),
        help="validate: ≤3 queries; full: all 220; score-only: re-score from raw-responses",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--validate-n", type=int, default=3)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--trace-root", type=Path, default=TRACE_ROOT)
    parser.add_argument("--packet-root", type=Path, default=PACKET_ROOT)
    parser.add_argument("--baseline-per-query", type=Path, default=BASELINE_PER_QUERY)
    parser.add_argument("--group-mapping", type=Path, default=GROUP_MAPPING)
    parser.add_argument("--step-0079-raw", type=Path, default=STEP_0079_RAW)
    parser.add_argument("--step-0080-raw", type=Path, default=STEP_0080_RAW)
    parser.add_argument("--step-0081-raw", type=Path, default=STEP_0081_RAW)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()

    group_path = args.group_mapping.resolve()
    if not group_path.is_file():
        write_text(
            out_dir / "results.md",
            "\n".join(
                [
                    "# Results: ABORTED — frozen group mapping not located",
                    "",
                    f"Expected mapping path: `{group_path}`",
                    "",
                ]
            ),
        )
        print(f"[abort] group mapping missing: {group_path}", flush=True)
        return 2

    packets = load_packets(args.packet_root.resolve())
    projections = load_projections(args.trace_root.resolve())
    targets = load_targets(args.trace_root.resolve())
    baselines = load_baseline_aps(args.baseline_per_query.resolve())
    direct_reader = load_stored_reader_aps(args.step_0079_raw.resolve(), DIRECT_READER)
    profile_reader = load_stored_reader_aps(
        args.step_0080_raw.resolve(), PROFILE_READER
    )
    raw_action = load_stored_reader_aps(
        args.step_0081_raw.resolve(), RAW_ACTION_READER
    )
    op_paths = load_group_mapping(group_path)

    require(
        set(packets)
        == set(projections)
        == set(targets)
        == set(baselines)
        == set(direct_reader)
        == set(profile_reader)
        == set(raw_action),
        "query_id coverage mismatch among inputs",
    )
    for query_id, rows in projections.items():
        for row in rows:
            require(
                str(row["operation_id"]) in op_paths,
                f"unmapped op {row['operation_id']}",
            )

    if args.mode == "validate":
        query_ids = sorted(packets)[: args.validate_n]
    elif args.mode == "full":
        query_ids = sorted(packets)
        if args.limit is not None:
            query_ids = query_ids[: args.limit]
    else:
        query_ids = sorted(packets)
        if args.limit is not None:
            query_ids = query_ids[: args.limit]

    print(
        f"[profile-reader-v2] mode={args.mode} queries={len(query_ids)} "
        f"workers={args.workers} out={out_dir}",
        flush=True,
    )
    print(
        f"[profile-reader-v2] group_mapping={group_path} key={GROUP_KEY} "
        f"additive={ADDITIVE_MEASURE} tiktoken={TIKTOKEN_ENCODING}",
        flush=True,
    )

    results: list[dict[str, Any]] = []
    errors: list[str] = []

    def work(query_id: str) -> dict[str, Any]:
        return process_one_query(
            query_id=query_id,
            session=packets[query_id],
            projection_rows=projections[query_id],
            target_step=targets[query_id],
            baseline_row=baselines[query_id],
            direct_reader_row=direct_reader[query_id],
            profile_reader_row=profile_reader[query_id],
            raw_action_row=raw_action[query_id],
            op_paths=op_paths,
            out_dir=out_dir,
            force=args.force and args.mode != "score-only",
        )

    if args.workers <= 1 or args.mode == "score-only":
        for query_id in query_ids:
            try:
                row = work(query_id)
                results.append(row)
                print(
                    f"[done] {query_id} ap={row['ap'][PROFILE_READER_V2]:.4f} "
                    f"s1={row['stage1_status']} s2={row['stage2_status']} "
                    f"wall={row['wall_seconds']:.1f}s chars={row['total_chars']} "
                    f"tok={row['total_tokens']} opened={row['content_opened_fraction']:.3f} "
                    f"hit={row['index_hit']}",
                    flush=True,
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{query_id}: {exc}")
                print(f"[error] {query_id}: {exc}", flush=True)
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(work, qid): qid for qid in query_ids}
            for fut in as_completed(futures):
                qid = futures[fut]
                try:
                    row = fut.result()
                    results.append(row)
                    print(
                        f"[done] {qid} ap={row['ap'][PROFILE_READER_V2]:.4f} "
                        f"s1={row['stage1_status']} s2={row['stage2_status']} "
                        f"wall={row['wall_seconds']:.1f}s chars={row['total_chars']} "
                        f"tok={row['total_tokens']} opened={row['content_opened_fraction']:.3f} "
                        f"hit={row['index_hit']}",
                        flush=True,
                    )
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{qid}: {exc}")
                    print(f"[error] {qid}: {exc}", flush=True)

    results.sort(key=lambda row: row["query_id"])
    require(not errors, f"errors on {len(errors)} queries: {errors[:5]}")
    require(len(results) == len(query_ids), "incomplete results")

    if args.mode == "validate":
        validate_path = out_dir / "validate-summary.json"
        write_json(
            validate_path,
            {
                "mode": "validate",
                "queries": len(results),
                "query_ids": [row["query_id"] for row in results],
                "mean_ap_profile_reader_v2": statistics.fmean(
                    row["ap"][PROFILE_READER_V2] for row in results
                ),
                "mean_content_opened_fraction": statistics.fmean(
                    row["content_opened_fraction"] for row in results
                ),
                "mean_total_tokens": statistics.fmean(
                    row["total_tokens"] for row in results
                ),
                "mean_stage1_tokens": statistics.fmean(
                    row["stage1_tokens"] for row in results
                ),
                "mean_stage2_tokens": statistics.fmean(
                    row["stage2_tokens"] for row in results
                ),
                "additive_measure": ADDITIVE_MEASURE,
                "additive_measure_note": ADDITIVE_MEASURE_NOTE,
                "rows": results,
                "group_mapping": str(group_path),
                "note": "Harness validation only; not a paper result.",
            },
        )
        print(f"[validate] wrote {validate_path}", flush=True)
        print(f"[validate] wall_total={time.monotonic()-started:.1f}s", flush=True)
        return 0

    require(len(results) == 220, f"full population requires 220 rows, got {len(results)}")
    map_scores = {
        PROFILE_READER_V2: statistics.fmean(
            row["ap"][PROFILE_READER_V2] for row in results
        ),
        PROFILE_READER: statistics.fmean(row["ap"][PROFILE_READER] for row in results),
        RAW_ACTION_READER: statistics.fmean(
            row["ap"][RAW_ACTION_READER] for row in results
        ),
        DIRECT_READER: statistics.fmean(row["ap"][DIRECT_READER] for row in results),
        DIRECT_ONLY: statistics.fmean(row["ap"][DIRECT_ONLY] for row in results),
        DIRECT_AGENTPROF: statistics.fmean(
            row["ap"][DIRECT_AGENTPROF] for row in results
        ),
    }
    require(
        math.isclose(map_scores[DIRECT_ONLY], 0.20871255669979352, abs_tol=1e-12),
        f"Direct-only MAP reproduction failed: {map_scores[DIRECT_ONLY]}",
    )
    require(
        math.isclose(map_scores[DIRECT_AGENTPROF], 0.32550420747157927, abs_tol=1e-12),
        f"Direct+AgentProf MAP reproduction failed: {map_scores[DIRECT_AGENTPROF]}",
    )
    require(
        math.isclose(map_scores[DIRECT_READER], 0.5019667175243024, abs_tol=1e-9),
        f"Direct-reader MAP reproduction failed: {map_scores[DIRECT_READER]}",
    )
    require(
        math.isclose(map_scores[PROFILE_READER], 0.4553334084291099, abs_tol=1e-9),
        f"Profile-reader MAP reproduction failed: {map_scores[PROFILE_READER]}",
    )
    require(
        math.isclose(map_scores[RAW_ACTION_READER], 0.4651286099436219, abs_tol=1e-9),
        f"Raw-action-reader MAP reproduction failed: {map_scores[RAW_ACTION_READER]}",
    )

    comparisons: dict[str, Any] = {}
    for key in BASELINE_KEYS:
        boot = paired_bootstrap(
            results,
            reader_key=PROFILE_READER_V2,
            baseline_key=key,
            repetitions=BOOTSTRAP_REPS,
            seed=BOOTSTRAP_SEEDS[key],
        )
        comparisons[key] = {
            "point_effect": map_scores[PROFILE_READER_V2] - map_scores[key],
            "interval_95": boot["interval_95"],
            "median": boot["median"],
            "nonpositive_draws": boot["nonpositive_draws"],
            "repetitions": boot["repetitions"],
            "seed": boot["seed"],
            "strata": boot["strata"],
            "clusters": boot["clusters"],
        }
        write_json(out_dir / f"bootstrap-deltas-vs-{key}.json", boot["draws"])

    walls = [float(row["wall_seconds"]) for row in results]
    total_chars = [int(row["total_chars"]) for row in results]
    s1_chars = [int(row["stage1_chars"]) for row in results]
    s2_chars = [int(row["stage2_chars"]) for row in results]
    s2_ev = [int(row["stage2_evidence_chars"]) for row in results]
    total_tokens = [int(row["total_tokens"]) for row in results]
    s1_tokens = [int(row["stage1_tokens"]) for row in results]
    s2_tokens = [int(row["stage2_tokens"]) for row in results]
    opened = [float(row["content_opened_fraction"]) for row in results]
    selected_ops = [int(row["selected_evidence_operation_count"]) for row in results]
    group_counts = [int(row["group_count"]) for row in results]
    hits = sum(1 for row in results if row["index_hit"])

    failure_tally = {
        "stage1_ok": sum(row["stage1_status"] == "ok" for row in results),
        "stage1_ok_after_retry": sum(
            row["stage1_status"] == "ok_after_retry" for row in results
        ),
        "stage1_largest_groups_fallback": sum(
            row["stage1_largest_groups_fallback"] for row in results
        ),
        "stage2_ok": sum(row["stage2_status"] == "ok" for row in results),
        "stage2_ok_after_retry": sum(
            row["stage2_status"] == "ok_after_retry" for row in results
        ),
        "stage2_original_order_failures": sum(
            row["stage2_scored_as_original_order_failure"] for row in results
        ),
    }

    step0079_summary = read_json(args.step_0079_raw.resolve())["summary"]
    cost79 = step0079_summary["cost"]

    mean_total_tokens = statistics.fmean(total_tokens)
    mean_opened = statistics.fmean(opened)
    map_v2 = map_scores[PROFILE_READER_V2]
    map_threshold = 0.48
    tokens_threshold = REF_TOKENS_STEP0079
    content_threshold = REF_CONTENT_OPENED_STEP0080
    registered_targets = {
        "map_threshold": map_threshold,
        "tokens_threshold": tokens_threshold,
        "content_opened_threshold": content_threshold,
        "map_met": map_v2 >= map_threshold,
        "tokens_met": mean_total_tokens < tokens_threshold,
        "content_opened_met": mean_opened <= content_threshold,
        "all_met": (
            map_v2 >= map_threshold
            and mean_total_tokens < tokens_threshold
            and mean_opened <= content_threshold
        ),
    }

    summary = {
        "mode": args.mode,
        "benchmark": "TraceElephant",
        "target_bearing_queries": 220,
        "operations": 5960,
        "zero_positive_queries": 0,
        "map": map_scores,
        "paired_comparisons": comparisons,
        "failure_tally": failure_tally,
        "bootstrap_seeds": BOOTSTRAP_SEEDS,
        "index_hit": {
            "hits": hits,
            "queries": 220,
            "rate": hits / 220.0,
            "definition": (
                "every target operation's group among selected groups "
                "(step-0080 analysis-001)"
            ),
            "step0080_hits": REF_INDEX_HITS_STEP0080,
            "step0080_rate": REF_INDEX_HITS_STEP0080 / 220.0,
        },
        "registered_targets": registered_targets,
        "additive_measure": ADDITIVE_MEASURE,
        "additive_measure_note": ADDITIVE_MEASURE_NOTE,
        "cost": {
            "queries": len(results),
            "total_wall_seconds": sum(walls),
            "mean_wall_seconds": statistics.fmean(walls),
            "median_wall_seconds": statistics.median(walls),
            "mean_total_chars": statistics.fmean(total_chars),
            "median_total_chars": statistics.median(total_chars),
            "mean_stage1_chars": statistics.fmean(s1_chars),
            "mean_stage2_chars": statistics.fmean(s2_chars),
            "mean_stage2_evidence_chars": statistics.fmean(s2_ev),
            "mean_content_opened_fraction": mean_opened,
            "median_content_opened_fraction": statistics.median(opened),
            "mean_selected_evidence_ops": statistics.fmean(selected_ops),
            "mean_group_count": statistics.fmean(group_counts),
            "max_total_chars": max(total_chars),
            "min_total_chars": min(total_chars),
            "mean_total_tokens": mean_total_tokens,
            "median_total_tokens": statistics.median(total_tokens),
            "mean_stage1_tokens": statistics.fmean(s1_tokens),
            "mean_stage2_tokens": statistics.fmean(s2_tokens),
            "median_stage1_tokens": statistics.median(s1_tokens),
            "median_stage2_tokens": statistics.median(s2_tokens),
            "tiktoken_encoding": TIKTOKEN_ENCODING,
            "ref_tokens_step0079": REF_TOKENS_STEP0079,
            "ref_tokens_step0080": REF_TOKENS_STEP0080,
            "token_ratio_vs_step0079": mean_total_tokens / REF_TOKENS_STEP0079,
            "token_ratio_vs_step0080": mean_total_tokens / REF_TOKENS_STEP0080,
        },
        "cost_step0079": {
            "queries": cost79["queries"],
            "mean_packet_chars": cost79["mean_packet_chars"],
            "mean_wall_seconds": cost79["mean_wall_seconds"],
            "median_wall_seconds": cost79["median_wall_seconds"],
            "total_wall_seconds": cost79["total_wall_seconds"],
            "total_packet_chars": cost79["total_packet_chars"],
        },
        "provenance": {
            "packets": str(args.packet_root.resolve()),
            "projections": str(
                (args.trace_root / "operations" / "projection.jsonl").resolve()
            ),
            "targets": str((args.trace_root / "scorer" / "targets.jsonl").resolve()),
            "baseline_per_query": str(args.baseline_per_query.resolve()),
            "step_0079_raw": str(args.step_0079_raw.resolve()),
            "step_0080_raw": str(args.step_0080_raw.resolve()),
            "step_0081_raw": str(args.step_0081_raw.resolve()),
            "group_mapping": str(group_path),
            "group_key": GROUP_KEY,
            "step_0072_conditions": {
                "Direct-only": "local_only",
                "Direct+AgentProf": "local_agentprof",
            },
        },
        "metric": (
            "sklearn.metrics.average_precision_score per target-bearing trajectory; "
            "arithmetic MAP; paired cluster bootstrap within strata"
        ),
        "reader": {
            "stages": 2,
            "stage1": "width-annotated profile skeleton group selection (≤5)",
            "stage2": "lean source_summary ranking (opened ops only)",
            "cli": (
                "grok -p/--prompt-file --output-format plain --max-turns 3 "
                "--tools '' --no-subagents --verbatim"
            ),
            "model_family": "external grok (CLI default)",
            "query_specific": True,
            "profile_once_built": True,
            "protocol_version": "v2",
            "changes_vs_0080": [
                "width-annotated stage-1 groups (ops mass)",
                "lean stage-2 (no skeleton re-send)",
            ],
        },
        "wall_seconds_harness": time.monotonic() - started,
    }

    per_query_out = []
    for row in results:
        per_query_out.append(
            {
                k: v
                for k, v in row.items()
                if k not in {"stage1_attempts", "stage2_attempts"}
            }
        )

    write_json(
        out_dir / "raw-results.json",
        {"per_query": per_query_out, "summary": summary},
    )
    write_json(out_dir / "summary.json", summary)
    write_text(out_dir / "results.md", render_results_md(summary))
    print(
        f"[full] MAP profile_reader_v2={map_scores[PROFILE_READER_V2]:.6f} "
        f"direct_reader={map_scores[DIRECT_READER]:.6f} "
        f"tokens={summary['cost']['mean_total_tokens']:.1f} "
        f"opened={summary['cost']['mean_content_opened_fraction']:.4f} "
        f"index_hits={hits}/220 "
        f"targets_met={registered_targets['all_met']} "
        f"harness_wall={summary['wall_seconds_harness']:.1f}s",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ExperimentError as exc:
        print(f"[fatal] {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
