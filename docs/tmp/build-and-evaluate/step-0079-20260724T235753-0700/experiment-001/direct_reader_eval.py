#!/usr/bin/env python3
"""Query-aware direct-reader baseline for TraceElephant RQ2 (step 0079).

For each target-bearing trajectory, builds a source-only evidence packet
(task text + operation source IDs + source-visible content), invokes the
external grok CLI once, parses a ranked list of operation IDs, and scores
non-interpolated average precision against the frozen TraceElephant targets.

Compared against stored Direct-only (local_only) and Direct+AgentProf
(local_agentprof) per-query APs from step 0072 / rq2-current-agent-local-first.
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
from typing import Any, Iterable, Mapping, Sequence

from sklearn.metrics import average_precision_score


REPO_ROOT = Path(__file__).resolve().parents[5]
TRACE_ROOT = REPO_ROOT / ".agentsight/experiments/traceelephant-rq2-v1"
PACKET_ROOT = REPO_ROOT / ".agentsight/experiments/rq2-a0-v1/full/trace/packets"
BASELINE_PER_QUERY = (
    REPO_ROOT
    / ".agentsight/experiments/rq2-current-agent-local-first-v1/full/per-query.jsonl"
)
DEFAULT_OUT = Path(__file__).resolve().parent

# Paper / idea-story names for step-0072 methods on TraceElephant.
DIRECT_ONLY = "local_only"
DIRECT_AGENTPROF = "local_agentprof"
BASELINE_KEYS = (DIRECT_ONLY, DIRECT_AGENTPROF)
BASELINE_DISPLAY = {
    DIRECT_ONLY: "Direct-only",
    DIRECT_AGENTPROF: "Direct+AgentProf",
}

# Same TraceElephant bootstrap seeds as step 0072 full run.
BOOTSTRAP_SEEDS = {
    DIRECT_ONLY: 20260923,
    DIRECT_AGENTPROF: 20260924,
}
BOOTSTRAP_REPS = 10000

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

RETRY_INSTRUCTION = """Your previous reply was not valid strict JSON with key ranked_operation_ids listing known operation_id strings.
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


def build_reader_packet(session: Mapping[str, Any]) -> dict[str, Any]:
    """Exact source-visible packet content sent to the reader (no targets)."""
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


def build_prompt(packet: Mapping[str, Any], extra: str = "") -> str:
    body = json.dumps(packet, ensure_ascii=False, sort_keys=True)
    parts = [READER_INSTRUCTION.strip(), "", "Evidence packet:", body]
    if extra:
        parts.extend(["", extra.strip()])
    return "\n".join(parts)


def extract_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    # Prefer fenced JSON if present.
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    candidates: list[str] = []
    if fence:
        candidates.append(fence.group(1))
    # Whole-text parse.
    candidates.append(text)
    # First balanced-looking object span.
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
            # Unknown IDs invalidate the parse so the format retry can recover.
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
    """Invoke grok single-turn.

    Prefer ``-p`` for modest prompts (task-spec form). For large evidence
    packets that exceed OS ARG_MAX, fall back to ``--prompt-file`` with the
    identical prompt bytes so the model still receives the full packet.
    """
    started = time.monotonic()
    # Leave headroom for envp + concurrent processes (~2 MiB ARG_MAX).
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
            # max-turns=3 is a fixed decoding allowance so the model can emit a
            # final answer after an internal thinking step; still one CLI call.
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
        # Accept non-zero only when stdout is empty; some runs emit the answer
        # and still exit with a max-turns status.
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


def process_one_query(
    query_id: str,
    session: Mapping[str, Any],
    projection_rows: Sequence[Mapping[str, Any]],
    target_step: int,
    baseline_row: Mapping[str, Any],
    out_dir: Path,
    force: bool = False,
) -> dict[str, Any]:
    packets_dir = out_dir / "packets"
    responses_dir = out_dir / "raw-responses"
    packets_dir.mkdir(parents=True, exist_ok=True)
    responses_dir.mkdir(parents=True, exist_ok=True)

    fname = safe_query_filename(query_id)
    packet_path = packets_dir / f"{fname}.json"
    response_path = responses_dir / f"{fname}.json"

    original_ids = [str(row["operation_id"]) for row in projection_rows]
    packet_ids = [str(op["operation_id"]) for op in session["operations"]]
    require(original_ids == packet_ids, f"{query_id}: packet/projection order mismatch")

    labels = [
        1 if int(row["step_id"]) == int(target_step) else 0 for row in projection_rows
    ]
    require(sum(labels) == 1, f"{query_id}: expected exactly one target operation")

    reader_packet = build_reader_packet(session)
    write_json(packet_path, reader_packet)
    packet_chars = len(
        json.dumps(reader_packet, ensure_ascii=False, sort_keys=True)
    )

    if response_path.exists() and not force:
        cached = read_json(response_path)
        ranking = list(cached["completed_ranking"])
        parse_status = str(cached.get("parse_status", "cached"))
        wall_s = float(cached.get("wall_seconds_total", 0.0))
        attempts = list(cached.get("attempts", []))
        failure = bool(cached.get("scored_as_original_order_failure", False))
    else:
        attempts = []
        ranking = None
        failure = False
        wall_s = 0.0
        parse_status = "ok"
        prompt = build_prompt(reader_packet)
        raw_text = ""
        for attempt_idx in range(2):
            extra = "" if attempt_idx == 0 else RETRY_INSTRUCTION
            prompt_attempt = build_prompt(reader_packet, extra=extra)
            try:
                raw_text, wall, meta = call_grok(prompt_attempt)
            except Exception as exc:  # noqa: BLE001 — record and fall through
                wall = 0.0
                meta = {"error": str(exc)}
                raw_text = ""
            wall_s += wall
            ranked = parse_ranked_ids(raw_text, original_ids) if raw_text else None
            attempts.append(
                {
                    "attempt": attempt_idx + 1,
                    "wall_seconds": wall,
                    "raw_response": raw_text,
                    "parsed_ranked_operation_ids": ranked,
                    "meta": meta,
                }
            )
            if ranked is not None:
                ranking = complete_ranking(ranked, original_ids)
                parse_status = "ok" if attempt_idx == 0 else "ok_after_retry"
                break
        if ranking is None:
            ranking = list(original_ids)
            parse_status = "failure_original_order"
            failure = True

        record = {
            "query_id": query_id,
            "parse_status": parse_status,
            "scored_as_original_order_failure": failure,
            "reader_ranked_operation_ids": (
                attempts[-1]["parsed_ranked_operation_ids"] if attempts else None
            ),
            "completed_ranking": ranking,
            "wall_seconds_total": wall_s,
            "packet_chars": packet_chars,
            "operation_count": len(original_ids),
            "attempts": attempts,
        }
        write_json(response_path, record)

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
    # Fallback if baseline missing stratum (should not happen).
    if not stratum:
        stratum = str(projection_rows[0]["cell"])
    if not cluster:
        cluster = query_id

    return {
        "query_id": query_id,
        "stratum": stratum,
        "cluster": cluster,
        "operations": len(original_ids),
        "targets": sum(labels),
        "target_operation_ids": target_operation_ids,
        "packet_chars": packet_chars,
        "wall_seconds": wall_s,
        "parse_status": parse_status,
        "scored_as_original_order_failure": failure,
        "ap": {
            "direct_reader": ap_reader,
            DIRECT_ONLY: float(baseline_row["ap"][DIRECT_ONLY]),
            DIRECT_AGENTPROF: float(baseline_row["ap"][DIRECT_AGENTPROF]),
        },
        "reader_rank_of_target": min(
            (ranking.index(oid) + 1 for oid in target_operation_ids), default=None
        ),
    }


def select_query_ids(
    all_ids: Sequence[str], mode: str, limit: int | None, validate_n: int
) -> list[str]:
    ordered = sorted(all_ids)
    if mode == "validate":
        return ordered[:validate_n]
    if limit is not None:
        return ordered[:limit]
    return ordered


def render_results_md(summary: Mapping[str, Any]) -> str:
    map_scores = summary["map"]
    lines = [
        "# Results: query-aware direct-reader baseline on TraceElephant (RQ2)",
        "",
        "## Population",
        "",
        f"- Workload: TraceElephant complete RQ2 collection",
        f"- Trajectories / target-bearing queries scored: {summary['target_bearing_queries']}",
        f"- Operations: {summary['operations']}",
        f"- Zero-positive trajectories: {summary['zero_positive_queries']} (excluded from MAP, same as existing protocol)",
        f"- All {summary['target_bearing_queries']} target-bearing queries are included; zero-positive count is 0 on this workload.",
        "",
        "## Input provenance (read-only, frozen)",
        "",
        f"- Source-only packets: `{summary['provenance']['packets']}`",
        f"- Operation projections / stable IDs: `{summary['provenance']['projections']}`",
        f"- Annotated targets (mistake_step): `{summary['provenance']['targets']}`",
        f"- Stored Direct-only / Direct+AgentProf per-query AP: `{summary['provenance']['baseline_per_query']}`",
        f"  (from step 0072 / `rq2-current-agent-local-first-v1`; Direct-only = `local_only`, Direct+AgentProf = `local_agentprof`)",
        f"- Scoring: sklearn non-interpolated `average_precision_score` per target-bearing trajectory; arithmetic MAP",
        f"- Paired bootstrap: 10,000 resamples of trajectory clusters within benchmark strata (cell); seeds {summary['bootstrap_seeds']}",
        "",
        "## Disclosures",
        "",
        "- Reader model is the external **grok** family invoked via the grok CLI single-turn path",
        "  (`-p` by default; `--prompt-file` for large packets that exceed OS ARG_MAX headroom).",
        "  Fixed decoding: `--output-format plain --max-turns 3 --tools '' --no-subagents --verbatim`.",
        "  This differs from the TraceElephant annotation backend used to build AgentProf groups.",
        "- The direct reader is **query-specific**: it sees the task text and the full source-visible",
        "  trajectory for that query and produces a ranking once per query.",
        "  The AgentPProf hierarchy is constructed once (source-only, query-agnostic grouping) and",
        "  then replayed for ranking; that asymmetry is intentional and not hidden.",
        "- Reader packets contain only task text, operation_id, ordinal, native_path, and source_summary.",
        "  No target labels, outcome labels, gold answers, localizer hits, or risk scores.",
        "",
        "## MAP",
        "",
        "| Method | MAP |",
        "|---|---:|",
        f"| Direct reader (this experiment) | {map_scores['direct_reader']:.6f} |",
        f"| Direct-only (stored) | {map_scores[DIRECT_ONLY]:.6f} |",
        f"| Direct+AgentProf (stored) | {map_scores[DIRECT_AGENTPROF]:.6f} |",
        "",
        "## Paired differences (reader − baseline)",
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
    lines.extend(
        [
            "",
            "## Failure tally",
            "",
            f"- Parse failures scored as original-order ranking: "
            f"{summary['failure_tally']['original_order_failures']}",
            f"- OK first attempt: {summary['failure_tally']['ok']}",
            f"- OK after one format retry: {summary['failure_tally']['ok_after_retry']}",
            "",
            "## Cost",
            "",
            f"- Queries: {summary['cost']['queries']}",
            f"- Total wall time (sum of per-query grok walls): "
            f"{summary['cost']['total_wall_seconds']:.2f} s",
            f"- Mean wall time per query: {summary['cost']['mean_wall_seconds']:.2f} s",
            f"- Median wall time per query: {summary['cost']['median_wall_seconds']:.2f} s",
            f"- Total packet characters: {summary['cost']['total_packet_chars']}",
            f"- Mean packet characters: {summary['cost']['mean_packet_chars']:.1f}",
            f"- Max packet characters: {summary['cost']['max_packet_chars']}",
            "",
            "Token counts are not always exposed by the plain-output CLI path; wall time and",
            "packet character volume are the primary recorded cost measures.",
            "",
            "## Honest interpretation",
            "",
        ]
    )
    reader_map = map_scores["direct_reader"]
    direct_map = map_scores[DIRECT_ONLY]
    agent_map = map_scores[DIRECT_AGENTPROF]
    d_vs_direct = summary["paired_comparisons"][DIRECT_ONLY]
    d_vs_agent = summary["paired_comparisons"][DIRECT_AGENTPROF]
    lines.append(
        f"On the complete TraceElephant population (n={summary['target_bearing_queries']}), "
        f"the query-aware direct reader achieves MAP={reader_map:.4f}. "
        f"Direct-only MAP is {direct_map:.4f} and Direct+AgentProf MAP is {agent_map:.4f} "
        f"(stored step-0072 values)."
    )
    lines.append("")
    lo, hi = d_vs_direct["interval_95"]
    lines.append(
        f"Versus Direct-only, the paired point difference is "
        f"{d_vs_direct['point_effect']:+.4f} with 95% interval [{lo:+.4f}, {hi:+.4f}]."
    )
    lo, hi = d_vs_agent["interval_95"]
    lines.append(
        f"Versus Direct+AgentProf, the paired point difference is "
        f"{d_vs_agent['point_effect']:+.4f} with 95% interval [{lo:+.4f}, {hi:+.4f}]."
    )
    lines.append("")
    lines.append(
        "Because the reader is query-specific and sees the full source-visible trajectory "
        "for that localization query, it is a strong current-practice competitor rather than "
        "an information-matched ablation of AgentPProf. A higher or lower MAP than "
        "Direct+AgentProf therefore does not by itself prove or refute the value of a "
        "once-built semantic hierarchy for multi-query / multi-measure reuse; it bounds "
        "how much ranking quality a one-shot full-trace reader can extract on this workload."
    )
    lines.append("")
    if summary["failure_tally"]["original_order_failures"]:
        lines.append(
            "Some queries fell back to original-order ranking after two parse failures; "
            "those are included in MAP and counted in the failure tally above."
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
    parser.add_argument("--force", action="store_true", help="re-call grok even if cached")
    parser.add_argument("--trace-root", type=Path, default=TRACE_ROOT)
    parser.add_argument("--packet-root", type=Path, default=PACKET_ROOT)
    parser.add_argument("--baseline-per-query", type=Path, default=BASELINE_PER_QUERY)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()

    packets = load_packets(args.packet_root.resolve())
    projections = load_projections(args.trace_root.resolve())
    targets = load_targets(args.trace_root.resolve())
    baselines = load_baseline_aps(args.baseline_per_query.resolve())

    require(set(packets) == set(projections) == set(targets) == set(baselines),
            "query_id coverage mismatch among inputs")

    query_ids = select_query_ids(
        sorted(packets),
        mode=args.mode if args.mode != "score-only" else "full",
        limit=args.limit if args.mode != "validate" else args.validate_n,
        validate_n=args.validate_n,
    )
    if args.mode == "validate":
        query_ids = sorted(packets)[: args.validate_n]
    elif args.mode == "full":
        query_ids = sorted(packets)
        if args.limit is not None:
            query_ids = query_ids[: args.limit]
    else:  # score-only uses whatever responses exist, but default to all
        query_ids = sorted(packets)
        if args.limit is not None:
            query_ids = query_ids[: args.limit]

    print(
        f"[direct-reader] mode={args.mode} queries={len(query_ids)} "
        f"workers={args.workers} out={out_dir}",
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
            out_dir=out_dir,
            force=args.force and args.mode != "score-only",
        )

    if args.workers <= 1 or args.mode == "score-only":
        for query_id in query_ids:
            try:
                row = work(query_id)
                results.append(row)
                print(
                    f"[done] {query_id} ap={row['ap']['direct_reader']:.4f} "
                    f"status={row['parse_status']} wall={row['wall_seconds']:.1f}s",
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
                        f"[done] {qid} ap={row['ap']['direct_reader']:.4f} "
                        f"status={row['parse_status']} wall={row['wall_seconds']:.1f}s",
                        flush=True,
                    )
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{qid}: {exc}")
                    print(f"[error] {qid}: {exc}", flush=True)

    results.sort(key=lambda row: row["query_id"])
    require(not errors, f"errors on {len(errors)} queries: {errors[:5]}")
    require(len(results) == len(query_ids), "incomplete results")

    # For validate mode, do not write population results as the paper result.
    if args.mode == "validate":
        validate_path = out_dir / "validate-summary.json"
        write_json(
            validate_path,
            {
                "mode": "validate",
                "queries": len(results),
                "query_ids": [row["query_id"] for row in results],
                "mean_ap_direct_reader": statistics.fmean(
                    row["ap"]["direct_reader"] for row in results
                ),
                "rows": results,
                "note": "Harness validation only; not a paper result.",
            },
        )
        print(f"[validate] wrote {validate_path}", flush=True)
        print(f"[validate] wall_total={time.monotonic()-started:.1f}s", flush=True)
        return 0

    # Full / score-only population metrics.
    require(len(results) == 220, f"full population requires 220 rows, got {len(results)}")
    map_scores = {
        "direct_reader": statistics.fmean(row["ap"]["direct_reader"] for row in results),
        DIRECT_ONLY: statistics.fmean(row["ap"][DIRECT_ONLY] for row in results),
        DIRECT_AGENTPROF: statistics.fmean(row["ap"][DIRECT_AGENTPROF] for row in results),
    }
    # Reproduce stored baseline MAPs within tolerance.
    require(
        math.isclose(map_scores[DIRECT_ONLY], 0.20871255669979352, abs_tol=1e-12),
        f"Direct-only MAP reproduction failed: {map_scores[DIRECT_ONLY]}",
    )
    require(
        math.isclose(map_scores[DIRECT_AGENTPROF], 0.32550420747157927, abs_tol=1e-12),
        f"Direct+AgentProf MAP reproduction failed: {map_scores[DIRECT_AGENTPROF]}",
    )

    comparisons: dict[str, Any] = {}
    for key in BASELINE_KEYS:
        boot = paired_bootstrap(
            results,
            reader_key="direct_reader",
            baseline_key=key,
            repetitions=BOOTSTRAP_REPS,
            seed=BOOTSTRAP_SEEDS[key],
        )
        comparisons[key] = {
            "point_effect": map_scores["direct_reader"] - map_scores[key],
            "interval_95": boot["interval_95"],
            "median": boot["median"],
            "nonpositive_draws": boot["nonpositive_draws"],
            "repetitions": boot["repetitions"],
            "seed": boot["seed"],
            "strata": boot["strata"],
            "clusters": boot["clusters"],
        }
        # Keep draws only in bootstrap-deltas file to keep raw-results smaller.
        write_json(out_dir / f"bootstrap-deltas-vs-{key}.json", boot["draws"])

    walls = [float(row["wall_seconds"]) for row in results]
    chars = [int(row["packet_chars"]) for row in results]
    failure_tally = {
        "ok": sum(row["parse_status"] == "ok" for row in results),
        "ok_after_retry": sum(row["parse_status"] == "ok_after_retry" for row in results),
        "original_order_failures": sum(
            row["scored_as_original_order_failure"] for row in results
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
        "cost": {
            "queries": len(results),
            "total_wall_seconds": sum(walls),
            "mean_wall_seconds": statistics.fmean(walls),
            "median_wall_seconds": statistics.median(walls),
            "total_packet_chars": sum(chars),
            "mean_packet_chars": statistics.fmean(chars),
            "max_packet_chars": max(chars),
            "min_packet_chars": min(chars),
        },
        "provenance": {
            "packets": str(args.packet_root.resolve()),
            "projections": str(
                (args.trace_root / "operations" / "projection.jsonl").resolve()
            ),
            "targets": str((args.trace_root / "scorer" / "targets.jsonl").resolve()),
            "baseline_per_query": str(args.baseline_per_query.resolve()),
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
            "cli": (
                "grok -p <packet+instruction> --output-format plain --max-turns 3 "
                "(--prompt-file used when prompt exceeds ~100KB ARG_MAX headroom)"
            ),
            "model_family": "external grok (CLI default)",
            "query_specific": True,
            "agentpprof_hierarchy_once_built_and_replayed": True,
        },
        "wall_seconds_harness": time.monotonic() - started,
    }

    raw_results = {
        "summary": {
            k: v for k, v in summary.items() if k != "paired_comparisons"
        } | {
            "paired_comparisons": {
                key: {kk: vv for kk, vv in cmp_.items()}
                for key, cmp_ in comparisons.items()
            }
        },
        "per_query": results,
    }
    write_json(out_dir / "raw-results.json", raw_results)
    write_text(out_dir / "results.md", render_results_md(summary))
    write_json(out_dir / "summary.json", summary)

    print(
        f"[full] MAP direct_reader={map_scores['direct_reader']:.6f} "
        f"direct_only={map_scores[DIRECT_ONLY]:.6f} "
        f"direct_agentprof={map_scores[DIRECT_AGENTPROF]:.6f}",
        flush=True,
    )
    print(f"[full] failures={failure_tally}", flush=True)
    print(f"[full] harness_wall={time.monotonic()-started:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ExperimentError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
