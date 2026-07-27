#!/usr/bin/env python3
"""Hierarchical vs flat semantic skeleton, one reader family (step 0089).

Hypothesis (the review's "why hierarchy" question): with the reader family
held fixed, the HIERARCHICAL semantic skeleton directs a reader to responsible
operations at least as well as a FLAT skeleton of the same leaf tags, while
opening less source content — i.e., the nesting itself carries navigation
value beyond the names.

This harness mirrors the step-0080 two-stage protocol on TraceElephant, with
these changes (each documented in execution-log.md):

- Reader for BOTH arms = opencode CLI (glm-5.2), run from an empty jail
  directory, instruction to answer directly in strict JSON, no tools —
  exactly the step-0083 addendum-002 recipe. Both arms same flags, one format
  retry, deterministic fallbacks, sequential arms with resume.
- Arm H (hierarchical): stage-1 skeleton = full semantic paths grouped by
  full path (as in step 0080), select <=5 groups.
- Arm F (flat): stage-1 skeleton = the SAME operations grouped by LEAF TAG
  only (last path component), parent paths stripped, a pure flat tag list;
  same <=5-group budget; stage 2 identical.
- Score: sklearn non-interpolated AP -> MAP over 220; content-opened fraction;
  paired 10,000-draw trajectory-cluster bootstrap H vs F (documented seed);
  index-hit rate per arm.
- PILOT of 40 queries per arm; operational gate (parse-failure rate < 10%)
  before the full 220.

Everything else — frozen TraceElephant inputs, packet schemas, AP/MAP,
paired bootstrap procedure, deterministic fallbacks — is identical to the
frozen step-0079/0080 protocols.
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
TRACE_ROOT = REPO_ROOT / ".agentsight/experiments/traceelephant-rq2-v1"
PACKET_ROOT = REPO_ROOT / ".agentsight/experiments/rq2-a0-v1/full/trace/packets"
BASELINE_PER_QUERY = (
    REPO_ROOT
    / ".agentsight/experiments/rq2-current-agent-local-first-v1/full/per-query.jsonl"
)
# Frozen target-blind Agent+Evidence paths used by step 0072 / step 0080.
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
DEFAULT_OUT = Path(__file__).resolve().parent

ARM_H = "hierarchical"
ARM_F = "flat"
ARMS = (ARM_H, ARM_F)
ARM_DISPLAY = {
    ARM_H: "Hierarchical skeleton (full semantic path)",
    ARM_F: "Flat skeleton (leaf tag only)",
}
ARM_TAG = {ARM_H: "H", ARM_F: "F"}

DIRECT_ONLY = "local_only"
DIRECT_AGENTPROF = "local_agentprof"
DIRECT_READER = "direct_reader"
REFERENCE_KEYS = (DIRECT_READER, DIRECT_AGENTPROF, DIRECT_ONLY)
REFERENCE_DISPLAY = {
    DIRECT_READER: "Direct reader (step 0079)",
    DIRECT_ONLY: "Direct-only (stored)",
    DIRECT_AGENTPROF: "Direct+AgentProf (stored)",
}

# Paired H-vs-F bootstrap seed (step 0089; documented).
H_VS_F_SEED = 20260989
CONTENT_DELTA_SEED = 20260990
BOOTSTRAP_REPS = 10000
MAX_SELECT_GROUPS = 5
PILOT_N = 40
PARSE_FAILURE_GATE = 0.10  # operational: proceed only if parse-failure rate < 10%.

# Stored reference MAPs (reproduced as invariants, mirroring step 0080).
STORED_DIRECT_ONLY_MAP = 0.20871255669979352
STORED_DIRECT_AGENTPROF_MAP = 0.32550420747157927
STORED_DIRECT_READER_MAP = 0.5019667175243024

# --- opencode reader constants (step-0083 addendum-002 recipe) ---
OPENCODE_TIMEOUT_S = 600
OPENCODE_BIN = "opencode"
OPENCODE_DEFAULT_MODEL = "glm-5.2"  # observed from stderr banner "> build · glm-5.2"

CLOSING = (
    "\n\nAnswer directly in strict JSON only. Do not use any tools, do not "
    "read or write any files, do not run any commands."
)

# Stage-1 instruction is arm-agnostic: the reader sees whatever skeleton paths
# the packet carries (full multi-component paths for H, single leaf tags for F).
STAGE1_INSTRUCTION = """You are diagnosing which groups of operations in an agent trajectory are most likely to contain the decisive mistake responsible for the agent's failure or incorrect solution.

You receive:
1) the original task text the agent was solving, and
2) a profile skeleton: every source operation with its stable operation_id, ordinal, and its semantic operation path, already grouped by path (each group lists its member ordinals and operation IDs). NO source content is provided.

Rules:
- Use only the provided task text and the profile skeleton (operation IDs, ordinals, semantic paths).
- Do not invent group paths or operation IDs.
- Select up to 5 groups (the group_path arrays shown in the packet) most likely to contain the decisive mistake.
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

STAGE2_INSTRUCTION = """You are diagnosing which operations in an agent trajectory are responsible for the agent's failure or incorrect solution on the assigned task.

You receive:
1) the original task text,
2) the full profile skeleton (operation IDs, ordinals, semantic paths grouped by path), and
3) source-visible content (source_summary) for ONLY the operations in the previously selected groups.

Rules:
- Use only the provided task text, profile skeleton, and the attached source_summary evidence.
- Do not invent operation IDs. Every ranked ID must appear exactly in the operations list.
- Rank operations by how likely each is responsible for the failure/incorrect outcome (most likely first).
- Prefer ranking among the operations that have source_summary evidence first; you may also rank other known operation_ids if needed.
- Cover at least every operation you consider plausibly responsible.
- Return ONLY strict JSON with this exact shape and no other text:
{"ranked_operation_ids": ["operation_id_most_likely", "operation_id_next", ...]}
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
# Frozen input loaders (TraceElephant) — identical to step 0080
# ---------------------------------------------------------------------------


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


def load_direct_reader_aps(path: Path) -> dict[str, dict[str, Any]]:
    payload = read_json(path)
    out: dict[str, dict[str, Any]] = {}
    for row in payload["per_query"]:
        query_id = str(row["query_id"])
        require(query_id not in out, f"duplicate direct_reader query {query_id}")
        out[query_id] = row
    require(len(out) == 220, f"expected 220 direct_reader rows, got {len(out)}")
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


# ---------------------------------------------------------------------------
# Skeleton builders — H uses full path, F uses leaf tag only
# ---------------------------------------------------------------------------


def arm_path(full_path: Sequence[str], arm: str) -> list[str]:
    """Project a frozen full semantic path to the arm's grouping key.

    H: the full path unchanged.
    F: the leaf (last component) only, parent paths stripped — a pure flat
    tag list per the task spec.
    """
    if arm == ARM_H:
        return list(full_path)
    if arm == ARM_F:
        require(len(full_path) >= 1, "empty semantic path")
        return [str(full_path[-1])]
    raise ExperimentError(f"unknown arm {arm}")


def build_skeleton(
    session: Mapping[str, Any],
    op_paths: Mapping[str, Sequence[str]],
    arm: str,
) -> dict[str, Any]:
    """Profile skeleton: ops + groups by the arm's path. No source content."""
    operations: list[dict[str, Any]] = []
    groups_map: dict[str, dict[str, Any]] = {}
    for op in session["operations"]:
        operation_id = str(op["operation_id"])
        ordinal = int(op["ordinal"])
        require(operation_id in op_paths, f"unmapped operation {operation_id}")
        arm_p = arm_path(op_paths[operation_id], arm)
        operations.append(
            {
                "operation_id": operation_id,
                "ordinal": ordinal,
                "semantic_path": arm_p,
            }
        )
        key = path_key(arm_p)
        if key not in groups_map:
            groups_map[key] = {
                "group_path": arm_p,
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
    largest_group_size = (
        max(len(g["member_operation_ids"]) for g in groups) if groups else 0
    )
    return {
        "task": str(session["task"]),
        "arm": arm,
        "operation_count": len(operations),
        "group_count": len(groups),
        "largest_group_size": largest_group_size,
        "operations": operations,
        "groups": groups,
    }


def build_stage1_packet(skeleton: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "task": skeleton["task"],
        "arm": skeleton["arm"],
        "operation_count": skeleton["operation_count"],
        "group_count": skeleton["group_count"],
        "largest_group_size": skeleton["largest_group_size"],
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
        "arm": skeleton["arm"],
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
    # addendum-002 point 4: every packet instruction ends with this sentence.
    parts.extend(["", CLOSING.strip()])
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Response parsing — FIRST JSON object in stdout (addendum-002 point 4)
# ---------------------------------------------------------------------------


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def extract_json_object(text: str) -> dict[str, Any] | None:
    """Return the FIRST JSON object in stdout (addendum-002 reader recipe)."""
    if not text:
        return None
    cleaned = _strip_ansi(text)
    for fence in re.finditer(
        r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.DOTALL
    ):
        try:
            value = json.loads(fence.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    n = len(cleaned)
    for start in range(n):
        if cleaned[start] != "{":
            continue
        depth = 0
        in_str = False
        esc = False
        end = -1
        for j in range(start, n):
            c = cleaned[j]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        end = j
                        break
        if end == -1:
            continue
        try:
            value = json.loads(cleaned[start : end + 1])
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
        resolved: list[str] | None = None
        if isinstance(item, list) and all(isinstance(x, str) for x in item):
            key = path_key(item)
            if key in valid_by_key:
                resolved = valid_by_key[key]
        elif isinstance(item, str):
            if item in alt_keys:
                resolved = alt_keys[item]
            elif item in valid_by_key:
                resolved = valid_by_key[item]
        elif isinstance(item, dict):
            if "group_path" in item and isinstance(item["group_path"], list):
                key = path_key([str(x) for x in item["group_path"]])
                if key in valid_by_key:
                    resolved = valid_by_key[key]
            elif "path_key" in item and str(item["path_key"]) in valid_by_key:
                resolved = valid_by_key[str(item["path_key"])]
        if resolved is None:
            return None
        key = path_key(resolved)
        if key in seen:
            continue
        seen.add(key)
        out.append(resolved)
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
# Bootstrap (identical procedure to steps 0072/0079-0081)
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
# Reader invocation: opencode CLI (step-0083 addendum-002 prescriptive recipe)
# ---------------------------------------------------------------------------

TOKENIZER = tiktoken.get_encoding("o200k_base")
ARGV_FALLBACK_BYTES = 900_000  # conservative; below ARG_MAX, leaves env headroom.


def call_opencode(
    prompt: str,
    jail: Path,
    timeout_s: int = OPENCODE_TIMEOUT_S,
) -> tuple[str, float, dict[str, Any]]:
    """Invoke the reader once.

    Fixed invocation (addendum-002 point 3)::

        opencode run --pure "<PACKET AND INSTRUCTION TEXT>"

    executed via subprocess with ``cwd=<reader-jail>`` (empty),
    ``stdin=/dev/null``. No additional flags are added. The observed default
    model is glm-5.2 (stderr banner ``> build · glm-5.2``). Prompts are passed
    directly as a single argv element (no shell) when below the conservative
    byte threshold; otherwise the addendum-002 ``bash -c '... "$(cat ...)"'``
    fallback is used. TraceElephant stage-2 prompts stay well under the
    threshold (max ~125 KiB), so the fallback is not expected to trigger.
    """
    started = time.monotonic()
    prompt_bytes = len(prompt.encode("utf-8"))
    fallback = prompt_bytes > ARGV_FALLBACK_BYTES
    if not fallback:
        cmd = [OPENCODE_BIN, "run", "--pure", prompt]
        delivery = "argv (opencode run --pure)"
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
            cwd=str(jail),
            stdin=subprocess.DEVNULL,
        )
    else:
        prompt_file = jail / "prompt.txt"
        prompt_file.write_text(prompt, encoding="utf-8")
        shell_cmd = f'{OPENCODE_BIN} run --pure "$(cat prompt.txt)"'
        proc = subprocess.run(
            ["bash", "-c", shell_cmd],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
            cwd=str(jail),
            stdin=subprocess.DEVNULL,
        )
        try:
            prompt_file.unlink(missing_ok=True)
        except OSError:
            pass
        delivery = "argv_fallback (bash -c cat prompt.txt)"
    wall = time.monotonic() - started
    stdout = proc.stdout or ""
    meta = {
        "returncode": proc.returncode,
        "stderr_tail": (proc.stderr or "")[-4000:],
        "delivery": delivery,
        "reader": "opencode run --pure",
        "reader_default_model": OPENCODE_DEFAULT_MODEL,
        "prompt_bytes": prompt_bytes,
        "prompt_tokens_o200k": len(TOKENIZER.encode(prompt)),
        "argv_fallback_triggered": fallback,
    }
    if proc.returncode != 0 and not stdout.strip():
        raise ExperimentError(
            f"opencode failed rc={proc.returncode}: "
            f"{(proc.stderr or stdout)[:1000]}"
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
    jail: Path,
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
            raw_text, wall, meta = call_opencode(prompt, jail=jail)
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
# Per-query processor (two-stage; arm-tagged output directories)
# ---------------------------------------------------------------------------


def process_one_query(
    arm: str,
    query_id: str,
    session: Mapping[str, Any],
    projection_rows: Sequence[Mapping[str, Any]],
    target_step: int,
    direct_reader_row: Mapping[str, Any],
    op_paths: Mapping[str, Sequence[str]],
    out_dir: Path,
    jail: Path,
    force: bool = False,
) -> dict[str, Any]:
    tag = ARM_TAG[arm]
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
        1 if int(row["step_id"]) == int(target_step) else 0 for row in projection_rows
    ]
    require(sum(labels) == 1, f"{query_id}: expected exactly one target operation")

    skeleton = build_skeleton(session, op_paths, arm)
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
                STAGE1_INSTRUCTION,
                STAGE1_RETRY,
                stage1_packet,
                parse_selected_groups,
                {"valid_paths": valid_paths},
                jail,
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
            STAGE2_INSTRUCTION,
            STAGE2_RETRY,
            stage2_packet,
            parse_ranked_ids,
            {"valid_ids": original_ids},
            jail,
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
            "arm": arm,
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
            "step0079_packet_chars": int(direct_reader_row["packet_chars"]),
        }
        write_json(response_path, record)

    total_chars = stage1_chars + stage2_chars
    step0079_chars = int(direct_reader_row["packet_chars"])
    evidence_only = {"selected_evidence": stage2_packet.get("selected_evidence", [])}
    stage2_evidence_chars = packet_char_count(evidence_only)
    content_opened_fraction = (
        stage2_evidence_chars / step0079_chars if step0079_chars > 0 else 0.0
    )

    # Index hit: at least one target operation sits in a selected group.
    selected_keys = {path_key(p) for p in selected_paths}
    selected_ids: set[str] = set()
    for group in skeleton["groups"]:
        if group["path_key"] in selected_keys:
            selected_ids.update(group["member_operation_ids"])
    target_operation_ids = [
        str(row["operation_id"])
        for row in projection_rows
        if int(row["step_id"]) == int(target_step)
    ]
    index_hit = any(oid in selected_ids for oid in target_operation_ids)

    scores = ranking_to_scores(ranking)
    score_vector = [scores[operation_id] for operation_id in original_ids]
    ap_arm = standard_ap(labels, score_vector)

    return {
        "query_id": query_id,
        "arm": arm,
        "operations": len(original_ids),
        "group_count": skeleton["group_count"],
        "largest_group_size": skeleton["largest_group_size"],
        "targets": sum(labels),
        "target_operation_ids": target_operation_ids,
        "selected_group_paths": selected_paths,
        "selected_evidence_operation_count": stage2_packet[
            "selected_evidence_operation_count"
        ],
        "stage1_chars": stage1_chars,
        "stage2_chars": stage2_chars,
        "stage2_evidence_chars": stage2_evidence_chars,
        "total_chars": total_chars,
        "step0079_packet_chars": step0079_chars,
        "content_opened_fraction": content_opened_fraction,
        "wall_seconds": wall_s,
        "stage1_wall_seconds": stage1_wall,
        "stage2_wall_seconds": stage2_wall,
        "prompt_tokens_o200k": prompt_tokens,
        "stage1_status": stage1_status,
        "stage2_status": stage2_status,
        "stage1_largest_groups_fallback": stage1_fallback,
        "stage2_scored_as_original_order_failure": stage2_failure,
        "index_hit": index_hit,
        "ap_arm": ap_arm,
        "reader_rank_of_target": min(
            (ranking.index(oid) + 1 for oid in target_operation_ids), default=None
        ),
    }


# ---------------------------------------------------------------------------
# Driver helpers
# ---------------------------------------------------------------------------


def run_arm_phase(
    arm: str,
    query_ids: Sequence[str],
    packets: Mapping[str, Mapping[str, Any]],
    projections: Mapping[str, Sequence[Mapping[str, Any]]],
    targets: Mapping[str, int],
    direct_reader: Mapping[str, Mapping[str, Any]],
    op_paths: Mapping[str, Sequence[str]],
    out_dir: Path,
    jail: Path,
    workers: int,
    force: bool,
    started: float,
    phase_label: str,
) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    errors: list[str] = []

    def work(query_id: str) -> dict[str, Any]:
        return process_one_query(
            arm=arm,
            query_id=query_id,
            session=packets[query_id],
            projection_rows=projections[query_id],
            target_step=targets[query_id],
            direct_reader_row=direct_reader[query_id],
            op_paths=op_paths,
            out_dir=out_dir,
            jail=jail,
            force=force,
        )

    items = list(query_ids)
    tag = ARM_TAG[arm]
    missing = 0
    for qid in items:
        resp = out_dir / f"raw-responses-{tag}" / f"{safe_query_filename(qid)}.json"
        if not (resp.exists() and not force):
            missing += 1
    print(
        f"[{phase_label}] arm={arm} queries={len(items)} to_call={missing} "
        f"cached={len(items)-missing} workers={workers}",
        flush=True,
    )

    if workers <= 1:
        for query_id in items:
            try:
                row = work(query_id)
                rows[row["query_id"]] = row
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{arm}:{query_id}: {exc}")
                print(f"[error] {arm}:{query_id}: {exc}", flush=True)
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(work, qid): qid for qid in items}
            done = 0
            for fut in as_completed(futures):
                qid = futures[fut]
                try:
                    row = fut.result()
                    rows[row["query_id"]] = row
                    done += 1
                    if done % 20 == 0 or done == len(items):
                        print(
                            f"[{phase_label}] {arm} {done}/{len(items)} "
                            f"elapsed={time.monotonic()-started:.0f}s",
                            flush=True,
                        )
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{arm}:{qid}: {exc}")
                    print(f"[error] {arm}:{qid}: {exc}", flush=True)

    require(not errors, f"errors on {len(errors)} items: {errors[:5]}")
    require(
        len(rows) == len(items),
        f"incomplete results for {arm}: {len(rows)}/{len(items)}",
    )
    return rows


def parse_failure_rate(rows: Mapping[str, Mapping[str, Any]]) -> float:
    if not rows:
        return 1.0
    failures = sum(
        1
        for r in rows.values()
        if r["stage1_largest_groups_fallback"]
        or r["stage2_scored_as_original_order_failure"]
    )
    return failures / len(rows)


def parse_ok_rate(rows: Mapping[str, Mapping[str, Any]]) -> tuple[int, int, int, int]:
    s1_ok = sum(r["stage1_status"] == "ok" for r in rows.values())
    s1_retry = sum(r["stage1_status"] == "ok_after_retry" for r in rows.values())
    s1_fail = sum(r["stage1_largest_groups_fallback"] for r in rows.values())
    s2_fail = sum(r["stage2_scored_as_original_order_failure"] for r in rows.values())
    return s1_ok, s1_retry, s1_fail, s2_fail


# ---------------------------------------------------------------------------
# Scoring + report
# ---------------------------------------------------------------------------


def score_arms(
    rows_h: Mapping[str, Mapping[str, Any]],
    rows_f: Mapping[str, Mapping[str, Any]],
    query_ids: Sequence[str],
    baselines: Mapping[str, Mapping[str, Any]],
    direct_reader: Mapping[str, Mapping[str, Any]],
    projections: Mapping[str, Sequence[Mapping[str, Any]]],
    out_dir: Path,
    started: float,
    provenance: Mapping[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    joined: list[dict[str, Any]] = []
    for query_id in query_ids:
        baseline_row = baselines[query_id]
        first = projections[query_id][0]
        stratum = str(baseline_row["stratum"]) or str(first.get("cell", ""))
        cluster = str(baseline_row["cluster"]) or query_id
        joined.append(
            {
                "query_id": query_id,
                "stratum": stratum,
                "cluster": cluster,
                "operations": len(projections[query_id]),
                "ap": {
                    ARM_H: rows_h[query_id]["ap_arm"],
                    ARM_F: rows_f[query_id]["ap_arm"],
                    DIRECT_READER: float(direct_reader[query_id]["ap"][DIRECT_READER]),
                    DIRECT_ONLY: float(baseline_row["ap"][DIRECT_ONLY]),
                    DIRECT_AGENTPROF: float(baseline_row["ap"][DIRECT_AGENTPROF]),
                },
                "h": rows_h[query_id],
                "f": rows_f[query_id],
            }
        )

    map_scores = {
        ARM_H: statistics.fmean(row["ap"][ARM_H] for row in joined),
        ARM_F: statistics.fmean(row["ap"][ARM_F] for row in joined),
        DIRECT_READER: statistics.fmean(row["ap"][DIRECT_READER] for row in joined),
        DIRECT_ONLY: statistics.fmean(row["ap"][DIRECT_ONLY] for row in joined),
        DIRECT_AGENTPROF: statistics.fmean(
            row["ap"][DIRECT_AGENTPROF] for row in joined
        ),
    }
    # Invariant reproductions (mirrors step 0080).
    require(
        math.isclose(map_scores[DIRECT_ONLY], STORED_DIRECT_ONLY_MAP, abs_tol=1e-12),
        f"Direct-only MAP reproduction failed: {map_scores[DIRECT_ONLY]}",
    )
    require(
        math.isclose(
            map_scores[DIRECT_AGENTPROF], STORED_DIRECT_AGENTPROF_MAP, abs_tol=1e-12
        ),
        f"Direct+AgentProf MAP reproduction failed: {map_scores[DIRECT_AGENTPROF]}",
    )
    require(
        math.isclose(map_scores[DIRECT_READER], STORED_DIRECT_READER_MAP, abs_tol=1e-9),
        f"Direct-reader MAP reproduction failed: {map_scores[DIRECT_READER]}",
    )

    # Paired H - F bootstrap (primary).
    boot_hf = paired_bootstrap_deltas(
        joined,
        lambda row: row["ap"][ARM_H] - row["ap"][ARM_F],
        repetitions=BOOTSTRAP_REPS,
        seed=H_VS_F_SEED,
    )
    comparison_hf = {
        "direction": "hierarchical - flat",
        "point_effect": map_scores[ARM_H] - map_scores[ARM_F],
        "interval_95": boot_hf["interval_95"],
        "median": boot_hf["median"],
        "nonpositive_draws": boot_hf["nonpositive_draws"],
        "repetitions": boot_hf["repetitions"],
        "seed": boot_hf["seed"],
        "strata": boot_hf["strata"],
        "clusters": boot_hf["clusters"],
    }
    write_json(out_dir / "bootstrap-deltas-H-minus-F.json", boot_hf["draws"])

    # Content-efficiency: H - F on content_opened_fraction (secondary).
    content_metrics = (
        "content_opened_fraction",
        "stage2_evidence_chars",
        "selected_evidence_operation_count",
    )
    content_deltas: dict[str, Any] = {}
    for metric in content_metrics:
        boot = paired_bootstrap_deltas(
            joined,
            lambda row, m=metric: row["h"][m] - row["f"][m],
            repetitions=BOOTSTRAP_REPS,
            seed=CONTENT_DELTA_SEED,
        )
        content_deltas[metric] = {
            "direction": "hierarchical - flat",
            "point_effect": statistics.fmean(
                row["h"][metric] - row["f"][metric] for row in joined
            ),
            "interval_95": boot["interval_95"],
            "median": boot["median"],
            "nonpositive_draws": boot["nonpositive_draws"],
            "repetitions": boot["repetitions"],
            "seed": boot["seed"],
        }
        write_json(out_dir / f"bootstrap-content-delta-{metric}.json", boot["draws"])

    def cost_block(arm: str) -> dict[str, Any]:
        tag = arm
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

    def group_block(arm: str) -> dict[str, Any]:
        counts = [int(row[arm]["group_count"]) for row in joined]
        largest = [int(row[arm]["largest_group_size"]) for row in joined]
        opened = [float(row[arm]["content_opened_fraction"]) for row in joined]
        sel_ops = [int(row[arm]["selected_evidence_operation_count"]) for row in joined]
        return {
            "mean_group_count": statistics.fmean(counts),
            "median_group_count": statistics.median(counts),
            "mean_largest_group_size": statistics.fmean(largest),
            "median_largest_group_size": statistics.median(largest),
            "max_largest_group_size": max(largest),
            "mean_content_opened_fraction": statistics.fmean(opened),
            "median_content_opened_fraction": statistics.median(opened),
            "mean_selected_evidence_ops": statistics.fmean(sel_ops),
            "index_hit_rate": statistics.fmean(
                1.0 if row[arm]["index_hit"] else 0.0 for row in joined
            ),
            "index_hits": sum(1 for row in joined if row[arm]["index_hit"]),
        }

    def failure_block(arm: str) -> dict[str, int]:
        s1_ok, s1_retry, s1_fail, s2_fail = parse_ok_rate(
            {row["query_id"]: row[arm] for row in joined}
        )
        s2_ok = sum(row[arm]["stage2_status"] == "ok" for row in joined)
        s2_retry = sum(row[arm]["stage2_status"] == "ok_after_retry" for row in joined)
        return {
            "stage1_ok": s1_ok,
            "stage1_ok_after_retry": s1_retry,
            "stage1_largest_groups_fallback": s1_fail,
            "stage2_ok": s2_ok,
            "stage2_ok_after_retry": s2_retry,
            "stage2_original_order_failures": s2_fail,
        }

    step0079_summary = read_json(args.step_0079_raw)["summary"]
    cost79 = step0079_summary["cost"]

    summary = {
        "mode": args.mode,
        "benchmark": "TraceElephant",
        "harness": "hier_vs_flat_eval.py",
        "target_bearing_queries": len(joined),
        "operations": sum(len(rows) for rows in projections.values()),
        "map": map_scores,
        "paired_h_minus_f": comparison_hf,
        "content_deltas_h_minus_f": content_deltas,
        "failure_tally": {ARM_H: failure_block("h"), ARM_F: failure_block("f")},
        "group_stats": {ARM_H: group_block("h"), ARM_F: group_block("f")},
        "cost": {ARM_H: cost_block("h"), ARM_F: cost_block("f")},
        "cost_step0079": {
            "queries": cost79["queries"],
            "mean_packet_chars": cost79["mean_packet_chars"],
            "mean_wall_seconds": cost79["mean_wall_seconds"],
            "median_wall_seconds": cost79["median_wall_seconds"],
            "total_wall_seconds": cost79["total_wall_seconds"],
        },
        "bootstrap_seeds": {"H_minus_F": H_VS_F_SEED, "content_delta": CONTENT_DELTA_SEED},
        "bootstrap_reps": BOOTSTRAP_REPS,
        "provenance": provenance,
        "metric": (
            "sklearn.metrics.average_precision_score per target-bearing query; "
            "arithmetic MAP over 220; paired trajectory-cluster bootstrap within "
            "TraceElephant strata"
        ),
        "reader": {
            "cli": "opencode run --pure <packet+instruction>",
            "delivery": "argv (single positional argument)",
            "default_model": OPENCODE_DEFAULT_MODEL,
            "model_source": "observed stderr banner '> build · glm-5.2'",
            "cwd": "reader-jail (fresh empty directory; no project context)",
            "stdin": "/dev/null",
            "no_flags_added": (
                "addendum-002 forbids invented flags / config / agent-file touch"
            ),
            "one_format_retry_per_call": True,
            "fallbacks": (
                "stage-1 fail -> largest 5 groups; stage-2 fail -> original-order "
                "ranking; all tallied"
            ),
            "parser": "FIRST JSON object in stdout (balanced-brace scan, ANSI stripped)",
            "instruction_closing": CLOSING.strip(),
            "model_family": (
                "opencode/glm-5.2 for BOTH arms (reader family held fixed); differs "
                "from the step-0080 grok reader, disclosed, not pooled with it"
            ),
            "workers": args.workers,
        },
        "arm_definition": {
            ARM_H: "full source_preserving_agent path grouped by full path (step-0080 style)",
            ARM_F: "leaf tag (last path component) only, parent paths stripped, grouped by leaf",
            "leaf_unique_tags": 5,
            "leaf_tag_vocabulary": ["blocked", "failure", "progress", "success", "unclear"],
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
                "ap": row["ap"],
                "h": row["h"],
                "f": row["f"],
            }
        )

    write_json(
        out_dir / "raw-results.json", {"per_query": per_query_out, "summary": summary}
    )
    write_json(out_dir / "summary.json", summary)
    write_text(out_dir / "results.md", render_results_md(summary))
    print(
        f"[score] MAP H={map_scores[ARM_H]:.6f} F={map_scores[ARM_F]:.6f} "
        f"dH-F={map_scores[ARM_H]-map_scores[ARM_F]:+.6f} "
        f"opened_H={summary['group_stats'][ARM_H]['mean_content_opened_fraction']:.4f} "
        f"opened_F={summary['group_stats'][ARM_F]['mean_content_opened_fraction']:.4f} "
        f"hit_H={summary['group_stats'][ARM_H]['index_hit_rate']:.4f} "
        f"hit_F={summary['group_stats'][ARM_F]['index_hit_rate']:.4f} "
        f"harness_wall={summary['wall_seconds_harness']:.1f}s",
        flush=True,
    )
    return summary


def render_results_md(summary: Mapping[str, Any]) -> str:
    map_scores = summary["map"]
    cmp_ = summary["paired_h_minus_f"]
    cd = summary["content_deltas_h_minus_f"]
    gh = summary["group_stats"][ARM_H]
    gf = summary["group_stats"][ARM_F]
    ch = summary["cost"][ARM_H]
    cf = summary["cost"][ARM_F]
    ft_h = summary["failure_tally"][ARM_H]
    ft_f = summary["failure_tally"][ARM_F]
    cost79 = summary["cost_step0079"]
    lo, hi = cmp_["interval_95"]
    clo, chi = cd["content_opened_fraction"]["interval_95"]

    # Hypothesis verdict.
    h_map = map_scores[ARM_H]
    f_map = map_scores[ARM_F]
    opened_h = gh["mean_content_opened_fraction"]
    opened_f = gf["mean_content_opened_fraction"]
    nonpos = cmp_["nonpositive_draws"]
    # "At least as well" on ranking: lower 95% bound of H-F >= 0 (strict) OR
    # point >= 0 with the interval not clearly negative.
    ranking_at_least_as_well = (lo >= 0.0) or (h_map >= f_map and lo > -0.02)
    less_content = opened_h < opened_f
    if ranking_at_least_as_well and less_content:
        verdict = "SUPPORTED"
    elif h_map >= f_map and less_content:
        verdict = "PARTIALLY SUPPORTED (H >= F on MAP but the H−F interval crosses 0)"
    elif h_map < f_map:
        verdict = "NOT SUPPORTED (flat arm matches or beats hierarchical on MAP)"
    else:
        verdict = "NOT SUPPORTED (hierarchical did not open less content)"

    lines = [
        "# Results: hierarchical vs flat semantic skeleton (one reader family)",
        "",
        "## Hypothesis (the review's \"why hierarchy\" question)",
        "",
        "With the reader family held fixed, the HIERARCHICAL semantic skeleton",
        "directs a reader to responsible operations at least as well as a FLAT",
        "skeleton of the same leaf tags, while opening less source content — i.e.,",
        "the nesting itself carries navigation value beyond the names.",
        "",
        f"## Verdict: {verdict}",
        "",
        "## Population",
        "",
        "- Workload: TraceElephant complete RQ2 collection",
        f"- Target-bearing queries scored: {summary['target_bearing_queries']}",
        f"- Operations: {summary['operations']}",
        "",
        "## Input provenance (read-only, frozen; reused from step 0080)",
        "",
        f"- Source-only packets: `{summary['provenance']['packets']}`",
        f"- Operation projections / stable IDs: `{summary['provenance']['projections']}`",
        f"- Annotated targets (mistake_step): `{summary['provenance']['targets']}`",
        f"- Stored Direct-only / Direct+AgentProf per-query AP: `{summary['provenance']['baseline_per_query']}`",
        f"- Step 0079 direct_reader per-query AP / costs: `{summary['provenance']['step_0079_raw']}`",
        f"- **Frozen Agent+Evidence group mapping**: `{summary['provenance']['group_mapping']}`",
        f"  (key `{summary['provenance']['group_key']}`; step-0072 source_preserving_agent paths)",
        f"- Leaf-tag vocabulary (arm F grouping key): {summary['arm_definition']['leaf_unique_tags']} tags — "
        f"{', '.join(summary['arm_definition']['leaf_tag_vocabulary'])}",
        f"- Scoring: sklearn non-interpolated `average_precision_score`; arithmetic MAP",
        f"- Paired bootstrap: {BOOTSTRAP_REPS:,} resamples of trajectory clusters within strata",
        f"  (H−F seed {H_VS_F_SEED}; content-delta seed {CONTENT_DELTA_SEED})",
        "",
        "## Arms (reader family held fixed)",
        "",
        f"- **Arm H (hierarchical)**: {summary['arm_definition'][ARM_H]}.",
        f"- **Arm F (flat)**: {summary['arm_definition'][ARM_F]}.",
        "- Reader (BOTH arms): `opencode run --pure` from an empty jail, "
        "`stdin=/dev/null`, default model glm-5.2, no tools, one format retry, "
        "deterministic fallbacks. Same flags / same instruction text for both arms.",
        "",
        "## MAP",
        "",
        "| Arm / method | MAP |",
        "|---|---:|",
        f"| **Arm H — hierarchical** | **{map_scores[ARM_H]:.6f}** |",
        f"| **Arm F — flat (leaf tag)** | **{map_scores[ARM_F]:.6f}** |",
        f"| Direct reader (step 0079, reference) | {map_scores[DIRECT_READER]:.6f} |",
        f"| Direct+AgentProf (stored, reference) | {map_scores[DIRECT_AGENTPROF]:.6f} |",
        f"| Direct-only (stored, reference) | {map_scores[DIRECT_ONLY]:.6f} |",
        "",
        "## Paired difference (H − F)",
        "",
        "| Metric | Point Δ | 95% interval | Nonpositive draws / 10000 |",
        "|---|---:|---:|---:|",
        f"| MAP (H − F) | {cmp_['point_effect']:+.6f} | [{lo:+.6f}, {hi:+.6f}] | {nonpos} |",
        f"| content_opened_fraction (H − F) | {cd['content_opened_fraction']['point_effect']:+.6f} | "
        f"[{clo:+.6f}, {chi:+.6f}] | {cd['content_opened_fraction']['nonpositive_draws']} |",
        f"| stage2_evidence_chars (H − F) | {cd['stage2_evidence_chars']['point_effect']:+.1f} | "
        f"[{cd['stage2_evidence_chars']['interval_95'][0]:+.1f}, "
        f"{cd['stage2_evidence_chars']['interval_95'][1]:+.1f}] | "
        f"{cd['stage2_evidence_chars']['nonpositive_draws']} |",
        f"| selected_evidence_ops (H − F) | {cd['selected_evidence_operation_count']['point_effect']:+.3f} | "
        f"[{cd['selected_evidence_operation_count']['interval_95'][0]:+.3f}, "
        f"{cd['selected_evidence_operation_count']['interval_95'][1]:+.3f}] | "
        f"{cd['selected_evidence_operation_count']['nonpositive_draws']} |",
        "",
        "## Index-hit rate (target operation inside a selected group)",
        "",
        "| Arm | Index-hit rate | Hits / 220 | Mean groups | Median groups | Largest group (mean) |",
        "|---|---:|---:|---:|---:|---:|",
        f"| H (hierarchical) | {gh['index_hit_rate']:.4f} | {gh['index_hits']} | "
        f"{gh['mean_group_count']:.2f} | {gh['median_group_count']:.2f} | {gh['mean_largest_group_size']:.2f} |",
        f"| F (flat) | {gf['index_hit_rate']:.4f} | {gf['index_hits']} | "
        f"{gf['mean_group_count']:.2f} | {gf['median_group_count']:.2f} | {gf['mean_largest_group_size']:.2f} |",
        "",
        "## Content opened (stage-2 evidence chars / step-0079 full packet chars)",
        "",
        "| Arm | Mean opened | Median opened | Mean selected evidence ops |",
        "|---|---:|---:|---:|",
        f"| H (hierarchical) | {gh['mean_content_opened_fraction']:.4f} | "
        f"{gh['median_content_opened_fraction']:.4f} | {gh['mean_selected_evidence_ops']:.2f} |",
        f"| F (flat) | {gf['mean_content_opened_fraction']:.4f} | "
        f"{gf['median_content_opened_fraction']:.4f} | {gf['mean_selected_evidence_ops']:.2f} |",
        "",
        "## Failure tally",
        "",
        "| Tally | H | F |",
        "|---|---:|---:|",
        f"| Stage-1 OK first attempt | {ft_h['stage1_ok']} | {ft_f['stage1_ok']} |",
        f"| Stage-1 OK after retry | {ft_h['stage1_ok_after_retry']} | {ft_f['stage1_ok_after_retry']} |",
        f"| Stage-1 largest-groups fallback | {ft_h['stage1_largest_groups_fallback']} | {ft_f['stage1_largest_groups_fallback']} |",
        f"| Stage-2 OK first attempt | {ft_h['stage2_ok']} | {ft_f['stage2_ok']} |",
        f"| Stage-2 OK after retry | {ft_h['stage2_ok_after_retry']} | {ft_f['stage2_ok_after_retry']} |",
        f"| Stage-2 original-order failures | {ft_h['stage2_original_order_failures']} | {ft_f['stage2_original_order_failures']} |",
        "",
        "## Cost (per query)",
        "",
        "| Metric | H | F | Direct reader (0079) |",
        "|---|---:|---:|---:|",
        f"| Mean total chars | {ch['mean_total_chars']:.1f} | {cf['mean_total_chars']:.1f} | {cost79['mean_packet_chars']:.1f} |",
        f"| Median total chars | {ch['median_total_chars']:.1f} | {cf['median_total_chars']:.1f} | — |",
        f"| Mean wall seconds | {ch['mean_wall_seconds']:.2f} | {cf['mean_wall_seconds']:.2f} | {cost79['mean_wall_seconds']:.2f} |",
        f"| Median wall seconds | {ch['median_wall_seconds']:.2f} | {cf['median_wall_seconds']:.2f} | {cost79['median_wall_seconds']:.2f} |",
        f"| Mean prompt tokens (o200k) | {ch['mean_prompt_tokens_o200k']:.0f} | {cf['mean_prompt_tokens_o200k']:.0f} | — |",
        "",
        "## Honest interpretation",
        "",
        f"On the complete TraceElephant population (n={summary['target_bearing_queries']}), "
        f"with the opencode/glm-5.2 reader family held fixed for both arms:",
        f"- Hierarchical MAP = {map_scores[ARM_H]:.4f}; Flat MAP = {map_scores[ARM_F]:.4f}.",
        f"- Paired H − F ΔMAP = {cmp_['point_effect']:+.4f}, 95% interval "
        f"[{lo:+.4f}, {hi:+.4f}], {nonpos}/10000 nonpositive draws.",
        f"- Mean content opened: H = {opened_h:.1%}, F = {opened_f:.1%} of the "
        f"step-0079 full-trace packet volume.",
        f"- Index-hit rate: H = {gh['index_hit_rate']:.1%}, F = {gf['index_hit_rate']:.1%}.",
        "",
        f"**Verdict: {verdict}.**",
        "",
        "Caveats: the flat arm's leaf tag is the operation outcome "
        "(success/progress/failure/blocked/unclear), so arm F groups by outcome "
        "only — a deliberately coarse flat projection of the same operations. "
        "This measures whether the hierarchical nesting carries navigation value "
        "beyond the leaf names for THIS reader family and workload. It does not "
        "evaluate other flat projections (e.g., a mid-depth prefix), other "
        "readers, or other workloads, and it is not pooled with the step-0080 "
        "grok-reader result.",
        "",
        "This file reports the complete 220-query run. The 40-per-arm pilot is "
        "an operational gate (parse-failure rate < 10%), recorded in "
        "`execution-log.md`, and is not a paper result.",
        "",
    ]
    return "\n".join(lines)


def write_pilot_note(
    out_dir: Path,
    rows_h: Mapping[str, Mapping[str, Any]],
    rows_f: Mapping[str, Mapping[str, Any]],
    pilot_ids: Sequence[str],
    started: float,
) -> None:
    h_fail = parse_failure_rate(rows_h)
    f_fail = parse_failure_rate(rows_f)
    h_ok = parse_ok_rate(rows_h)
    f_ok = parse_ok_rate(rows_f)
    note = {
        "pilot_n_per_arm": PILOT_N,
        "query_ids": list(pilot_ids),
        "parse_failure_gate": PARSE_FAILURE_GATE,
        "hierarchical": {
            "parse_failure_rate": h_fail,
            "stage1_ok": h_ok[0],
            "stage1_ok_after_retry": h_ok[1],
            "stage1_largest_groups_fallback": h_ok[2],
            "stage2_original_order_failures": h_ok[3],
            "mean_ap": statistics.fmean(r["ap_arm"] for r in rows_h.values()),
            "mean_content_opened_fraction": statistics.fmean(
                r["content_opened_fraction"] for r in rows_h.values()
            ),
            "index_hit_rate": statistics.fmean(
                1.0 if r["index_hit"] else 0.0 for r in rows_h.values()
            ),
        },
        "flat": {
            "parse_failure_rate": f_fail,
            "stage1_ok": f_ok[0],
            "stage1_ok_after_retry": f_ok[1],
            "stage1_largest_groups_fallback": f_ok[2],
            "stage2_original_order_failures": f_ok[3],
            "mean_ap": statistics.fmean(r["ap_arm"] for r in rows_f.values()),
            "mean_content_opened_fraction": statistics.fmean(
                r["content_opened_fraction"] for r in rows_f.values()
            ),
            "index_hit_rate": statistics.fmean(
                1.0 if r["index_hit"] else 0.0 for r in rows_f.values()
            ),
        },
        "gate_pass": (h_fail < PARSE_FAILURE_GATE and f_fail < PARSE_FAILURE_GATE),
        "wall_seconds": time.monotonic() - started,
        "note": (
            "Operational pilot gate only (parse-failure rate < 10% per arm); "
            "both arms are new conditions, so the gate is not score-based. "
            "Not a paper result."
        ),
    }
    write_json(out_dir / "pilot-summary.json", note)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=("pilot", "full", "score-only"),
        help=(
            "pilot: 40 queries/arm (operational gate); full: 220/arm sequentially "
            "then score; score-only: re-score from cached responses"
        ),
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--pilot-n", type=int, default=PILOT_N)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--trace-root", type=Path, default=TRACE_ROOT)
    parser.add_argument("--packet-root", type=Path, default=PACKET_ROOT)
    parser.add_argument("--baseline-per-query", type=Path, default=BASELINE_PER_QUERY)
    parser.add_argument("--group-mapping", type=Path, default=GROUP_MAPPING)
    parser.add_argument("--step-0079-raw", type=Path, default=STEP_0079_RAW)
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
    direct_reader = load_direct_reader_aps(args.step_0079_raw.resolve())
    op_paths = load_group_mapping(group_path)

    require(
        set(packets)
        == set(projections)
        == set(targets)
        == set(baselines)
        == set(direct_reader),
        "query_id coverage mismatch among inputs",
    )
    for query_id, rows in projections.items():
        for row in rows:
            require(
                str(row["operation_id"]) in op_paths,
                f"unmapped op {row['operation_id']}",
            )

    all_ids = sorted(packets)

    # Fresh EMPTY jail directory (addendum-002 point 2).
    jail = out_dir / "reader-jail"
    jail.mkdir(parents=True, exist_ok=True)

    provenance = {
        "packets": str(args.packet_root.resolve()),
        "projections": str(
            (args.trace_root / "operations" / "projection.jsonl").resolve()
        ),
        "targets": str((args.trace_root / "scorer" / "targets.jsonl").resolve()),
        "baseline_per_query": str(args.baseline_per_query.resolve()),
        "step_0079_raw": str(args.step_0079_raw.resolve()),
        "group_mapping": str(group_path),
        "group_key": GROUP_KEY,
    }

    if args.mode == "pilot":
        pilot_ids = all_ids[: args.pilot_n]
        print(
            f"[pilot] queries/arm={len(pilot_ids)} workers={args.workers} "
            f"out={out_dir} jail={jail}",
            flush=True,
        )
        rows_h = run_arm_phase(
            ARM_H, pilot_ids, packets, projections, targets, direct_reader,
            op_paths, out_dir, jail,
            workers=args.workers,
            force=args.force,
            started=started,
            phase_label="pilot",
        )
        rows_f = run_arm_phase(
            ARM_F, pilot_ids, packets, projections, targets, direct_reader,
            op_paths, out_dir, jail,
            workers=args.workers,
            force=args.force,
            started=started,
            phase_label="pilot",
        )
        write_pilot_note(out_dir, rows_h, rows_f, pilot_ids, started)
        h_fail = parse_failure_rate(rows_h)
        f_fail = parse_failure_rate(rows_f)
        print(
            f"[pilot] parse_failure H={h_fail:.3f} F={f_fail:.3f} "
            f"gate={'PASS' if (h_fail < PARSE_FAILURE_GATE and f_fail < PARSE_FAILURE_GATE) else 'FAIL'} "
            f"wall={time.monotonic()-started:.1f}s",
            flush=True,
        )
        return 0

    # full or score-only: both arms over all 220, sequentially, with resume.
    query_ids = all_ids
    if args.limit is not None:
        query_ids = query_ids[: args.limit]

    if args.mode == "score-only":
        # Re-score from cached responses only; no reader calls.
        def reload(arm: str) -> dict[str, dict[str, Any]]:
            tag = ARM_TAG[arm]
            rows: dict[str, dict[str, Any]] = {}
            for qid in query_ids:
                rows[qid] = process_one_query(
                    arm=arm,
                    query_id=qid,
                    session=packets[qid],
                    projection_rows=projections[qid],
                    target_step=targets[qid],
                    direct_reader_row=direct_reader[qid],
                    op_paths=op_paths,
                    out_dir=out_dir,
                    jail=jail,
                    force=False,
                )
            return rows

        rows_h = reload(ARM_H)
        rows_f = reload(ARM_F)
    else:
        require(
            len(query_ids) == 220, f"full population requires 220 queries, got {len(query_ids)}"
        )
        print(
            f"[full] queries/arm={len(query_ids)} workers={args.workers} "
            f"out={out_dir} jail={jail}",
            flush=True,
        )
        rows_h = run_arm_phase(
            ARM_H, query_ids, packets, projections, targets, direct_reader,
            op_paths, out_dir, jail,
            workers=args.workers,
            force=args.force,
            started=started,
            phase_label="phase1/2",
        )
        rows_f = run_arm_phase(
            ARM_F, query_ids, packets, projections, targets, direct_reader,
            op_paths, out_dir, jail,
            workers=args.workers,
            force=args.force,
            started=started,
            phase_label="phase2/2",
        )

    score_arms(
        rows_h, rows_f, query_ids, baselines, direct_reader, projections,
        out_dir, started, provenance, args,
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ExperimentError as exc:
        print(f"[experiment-error] {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
