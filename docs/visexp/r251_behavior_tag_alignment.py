#!/usr/bin/env python3
"""R251: behavioral grounding check for semantic prompt tags.

This run reads generated R170 folded stacks only. It does not read raw
Codex/Claude sessions, does not call an LLM, and does not add human labels.

The experiment asks a narrower C6-adjacent question: are prompt/session tags
measurably aligned with observed system behavior profiles, beyond what would be
expected from a session-preserving random shuffle of prompt tags? Passing this
check supports behavioral grounding, not human semantic adequacy.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import math
import random
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_FOLDED = REPO_ROOT / ".agentsight" / "agentflame" / "r170-full-current" / "semantic-system.folded.txt"
DEFAULT_OUT = SCRIPT_DIR / "out" / "behavior-tag-alignment-r251"

PROMPT_PROFILE_FIELDS = [
    "rank",
    "prompt_tag",
    "total_weight",
    "weight_share_pct",
    "distinct_behaviors",
    "top_behavior",
    "top_behavior_weight",
    "top_behavior_share_pct",
    "behavior_entropy_bits",
    "top_behaviors",
]

BEHAVIOR_PROFILE_FIELDS = [
    "rank",
    "behavior_key",
    "total_weight",
    "weight_share_pct",
    "distinct_prompt_tags",
    "top_prompt_tag",
    "top_prompt_weight",
    "top_prompt_share_pct",
    "prompt_entropy_bits",
    "top_prompt_tags",
]

NULL_FIELDS = [
    "metric",
    "actual",
    "null_mean",
    "null_p50",
    "null_p95",
    "null_max",
    "one_sided_p_value",
    "actual_gt_null_p95",
]

LOW_COHERENCE_FIELDS = [
    "rank",
    "prompt_tag",
    "total_weight",
    "top_behavior_share_pct",
    "distinct_behaviors",
    "behavior_entropy_bits",
    "top_behaviors",
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return str(path)


def git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def repo_dirty() -> bool:
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return bool(out.strip())
    except Exception:
        return True


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(str(value)))


def pct(part: int | float, whole: int | float) -> float | None:
    if not whole:
        return None
    return round(100.0 * float(part) / float(whole), 3)


def entropy_from_counter(counter: Counter[Any]) -> float:
    total = sum(counter.values())
    if not total:
        return 0.0
    entropy = 0.0
    for count in counter.values():
        if not count:
            continue
        p = count / total
        entropy -= p * math.log2(p)
    return entropy


def compact_counter(counter: Counter[str], limit: int = 8) -> str:
    return "; ".join(f"{key}={value}" for key, value in counter.most_common(limit))


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return round(values[0], 6)
    ordered = sorted(values)
    rank = (len(ordered) - 1) * q
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return round(ordered[lower], 6)
    frac = rank - lower
    return round(ordered[lower] * (1 - frac) + ordered[upper] * frac, 6)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_folded_line(line: str) -> tuple[str, int]:
    stack, _, weight = line.rstrip("\n").rpartition(" ")
    if not stack or not weight:
        raise ValueError(f"invalid folded line: {line[:160]}")
    return stack, as_int(weight)


def frames_from_stack(stack: str) -> dict[str, list[str]]:
    frames: dict[str, list[str]] = defaultdict(list)
    for frame in stack.split(";"):
        if ":" not in frame:
            continue
        key, value = frame.split(":", 1)
        frames[key].append(value)
    return frames


def first_frame(frames: dict[str, list[str]], key: str, default: str = "") -> str:
    values = frames.get(key) or []
    return values[0] if values else default


def process_label(frames: dict[str, list[str]]) -> str:
    process = first_frame(frames, "process")
    if process:
        return process
    call = first_frame(frames, "call")
    if call:
        return call.replace("/", ":")
    tool = first_frame(frames, "tool")
    cmd = first_frame(frames, "cmd")
    return cmd or tool or "unknown"


def behavior_key(frames: dict[str, list[str]]) -> str:
    process = process_label(frames)
    effect = first_frame(frames, "effect", "unknown")
    status = first_frame(frames, "status", "unknown")
    return f"process:{process};effect:{effect};status:{status}"


def read_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            stack, weight = parse_folded_line(line)
            frames = frames_from_stack(stack)
            session = first_frame(frames, "session", "unknown")
            prompt = first_frame(frames, "prompt", "unknown")
            behavior = behavior_key(frames)
            if prompt == "unknown" or not prompt:
                continue
            rows.append(
                {
                    "session": session or "unknown",
                    "prompt": prompt,
                    "behavior": behavior,
                    "weight": weight,
                }
            )
    return rows


def weighted_counter(rows: Iterable[dict[str, Any]], key: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter[str(row[key])] += int(row["weight"])
    return counter


def conditional_entropy(rows: Iterable[dict[str, Any]], condition_keys: tuple[str, ...], target_key: str) -> float:
    by_condition: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    condition_weight: Counter[tuple[str, ...]] = Counter()
    total = 0
    for row in rows:
        weight = int(row["weight"])
        condition = tuple(str(row[key]) for key in condition_keys)
        target = str(row[target_key])
        by_condition[condition][target] += weight
        condition_weight[condition] += weight
        total += weight
    if not total:
        return 0.0
    return sum((condition_weight[key] / total) * entropy_from_counter(counter) for key, counter in by_condition.items())


def profile_purity(rows: Iterable[dict[str, Any]], label_key: str, target_key: str) -> float:
    by_label: dict[str, Counter[str]] = defaultdict(Counter)
    total = 0
    for row in rows:
        weight = int(row["weight"])
        by_label[str(row[label_key])][str(row[target_key])] += weight
        total += weight
    if not total:
        return 0.0
    top_weight = sum(max(counter.values()) for counter in by_label.values() if counter)
    return top_weight / total


def metrics_for_rows(rows: list[dict[str, Any]]) -> dict[str, float]:
    behavior_entropy = entropy_from_counter(weighted_counter(rows, "behavior"))
    behavior_given_session = conditional_entropy(rows, ("session",), "behavior")
    behavior_given_prompt = conditional_entropy(rows, ("prompt",), "behavior")
    behavior_given_session_prompt = conditional_entropy(rows, ("session", "prompt"), "behavior")
    session_reduction = 0.0 if behavior_entropy == 0 else (behavior_entropy - behavior_given_session) / behavior_entropy
    prompt_reduction = 0.0 if behavior_entropy == 0 else (behavior_entropy - behavior_given_prompt) / behavior_entropy
    if behavior_given_session:
        conditional_prompt_reduction = (behavior_given_session - behavior_given_session_prompt) / behavior_given_session
    else:
        conditional_prompt_reduction = 0.0
    return {
        "behavior_entropy_bits": behavior_entropy,
        "behavior_entropy_given_session_bits": behavior_given_session,
        "behavior_entropy_given_prompt_bits": behavior_given_prompt,
        "behavior_entropy_given_session_prompt_bits": behavior_given_session_prompt,
        "session_behavior_uncertainty_reduction_pct": 100.0 * session_reduction,
        "prompt_behavior_uncertainty_reduction_pct": 100.0 * prompt_reduction,
        "prompt_gain_beyond_session_pct": 100.0 * conditional_prompt_reduction,
        "prompt_top_behavior_purity_pct": 100.0 * profile_purity(rows, "prompt", "behavior"),
        "session_top_behavior_purity_pct": 100.0 * profile_purity(rows, "session", "behavior"),
    }


def expand_events(rows: list[dict[str, Any]]) -> tuple[list[str], list[str], list[str]]:
    sessions: list[str] = []
    prompts: list[str] = []
    behaviors: list[str] = []
    for row in rows:
        weight = int(row["weight"])
        if weight <= 0:
            continue
        sessions.extend([str(row["session"])] * weight)
        prompts.extend([str(row["prompt"])] * weight)
        behaviors.extend([str(row["behavior"])] * weight)
    return sessions, prompts, behaviors


def rows_from_events(sessions: list[str], prompts: list[str], behaviors: list[str]) -> list[dict[str, Any]]:
    grouped: Counter[tuple[str, str, str]] = Counter()
    for session, prompt, behavior in zip(sessions, prompts, behaviors, strict=True):
        grouped[(session, prompt, behavior)] += 1
    return [
        {"session": session, "prompt": prompt, "behavior": behavior, "weight": weight}
        for (session, prompt, behavior), weight in grouped.items()
    ]


def session_preserving_prompt_shuffle(
    sessions: list[str],
    prompts: list[str],
    rng: random.Random,
) -> list[str]:
    shuffled = list(prompts)
    indices_by_session: dict[str, list[int]] = defaultdict(list)
    for index, session in enumerate(sessions):
        indices_by_session[session].append(index)
    for indices in indices_by_session.values():
        values = [shuffled[index] for index in indices]
        rng.shuffle(values)
        for index, value in zip(indices, values, strict=True):
            shuffled[index] = value
    return shuffled


def null_distributions(
    rows: list[dict[str, Any]],
    permutations: int,
    seed: int,
) -> dict[str, list[float]]:
    sessions, prompts, behaviors = expand_events(rows)
    rng = random.Random(seed)
    out = {
        "prompt_gain_beyond_session_pct": [],
        "prompt_top_behavior_purity_pct": [],
    }
    for _ in range(permutations):
        shuffled_prompts = session_preserving_prompt_shuffle(sessions, prompts, rng)
        shuffled_rows = rows_from_events(sessions, shuffled_prompts, behaviors)
        metrics = metrics_for_rows(shuffled_rows)
        for key in out:
            out[key].append(metrics[key])
    return out


def null_summary_rows(actual: dict[str, float], nulls: dict[str, list[float]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for metric, values in nulls.items():
        actual_value = actual[metric]
        if not values:
            continue
        ge_count = sum(1 for value in values if value >= actual_value)
        p_value = (ge_count + 1) / (len(values) + 1)
        null_p95 = percentile(values, 0.95)
        rows.append(
            {
                "metric": metric,
                "actual": round(actual_value, 6),
                "null_mean": round(sum(values) / len(values), 6),
                "null_p50": percentile(values, 0.50),
                "null_p95": null_p95,
                "null_max": round(max(values), 6),
                "one_sided_p_value": round(p_value, 6),
                "actual_gt_null_p95": bool(null_p95 is not None and actual_value > null_p95),
            }
        )
    return rows


def prompt_profile_rows(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    by_prompt: dict[str, Counter[str]] = defaultdict(Counter)
    total = sum(int(row["weight"]) for row in rows)
    for row in rows:
        by_prompt[str(row["prompt"])][str(row["behavior"])] += int(row["weight"])
    out: list[dict[str, Any]] = []
    for rank, (prompt, counter) in enumerate(
        sorted(by_prompt.items(), key=lambda item: sum(item[1].values()), reverse=True)[:limit],
        start=1,
    ):
        weight = sum(counter.values())
        top_behavior, top_weight = counter.most_common(1)[0]
        out.append(
            {
                "rank": rank,
                "prompt_tag": prompt,
                "total_weight": weight,
                "weight_share_pct": pct(weight, total),
                "distinct_behaviors": len(counter),
                "top_behavior": top_behavior,
                "top_behavior_weight": top_weight,
                "top_behavior_share_pct": pct(top_weight, weight),
                "behavior_entropy_bits": round(entropy_from_counter(counter), 6),
                "top_behaviors": compact_counter(counter),
            }
        )
    return out


def behavior_profile_rows(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    by_behavior: dict[str, Counter[str]] = defaultdict(Counter)
    total = sum(int(row["weight"]) for row in rows)
    for row in rows:
        by_behavior[str(row["behavior"])][str(row["prompt"])] += int(row["weight"])
    out: list[dict[str, Any]] = []
    for rank, (behavior, counter) in enumerate(
        sorted(by_behavior.items(), key=lambda item: sum(item[1].values()), reverse=True)[:limit],
        start=1,
    ):
        weight = sum(counter.values())
        top_prompt, top_weight = counter.most_common(1)[0]
        out.append(
            {
                "rank": rank,
                "behavior_key": behavior,
                "total_weight": weight,
                "weight_share_pct": pct(weight, total),
                "distinct_prompt_tags": len(counter),
                "top_prompt_tag": top_prompt,
                "top_prompt_weight": top_weight,
                "top_prompt_share_pct": pct(top_weight, weight),
                "prompt_entropy_bits": round(entropy_from_counter(counter), 6),
                "top_prompt_tags": compact_counter(counter),
            }
        )
    return out


def low_coherence_prompt_rows(rows: list[dict[str, Any]], min_weight: int, limit: int) -> list[dict[str, Any]]:
    profiles = prompt_profile_rows(rows, limit=10_000)
    candidates = [
        row for row in profiles if int(row["total_weight"]) >= min_weight and row["top_behavior_share_pct"] is not None
    ]
    candidates.sort(key=lambda row: (float(row["top_behavior_share_pct"]), -int(row["total_weight"])))
    out: list[dict[str, Any]] = []
    for rank, row in enumerate(candidates[:limit], start=1):
        out.append(
            {
                "rank": rank,
                "prompt_tag": row["prompt_tag"],
                "total_weight": row["total_weight"],
                "top_behavior_share_pct": row["top_behavior_share_pct"],
                "distinct_behaviors": row["distinct_behaviors"],
                "behavior_entropy_bits": row["behavior_entropy_bits"],
                "top_behaviors": row["top_behaviors"],
            }
        )
    return out


def write_svg(path: Path, actual: dict[str, float], null_rows: list[dict[str, Any]]) -> None:
    metrics = [
        ("prompt_gain_beyond_session_pct", "Prompt gain beyond session"),
        ("prompt_top_behavior_purity_pct", "Prompt top-behavior purity"),
    ]
    row_lookup = {row["metric"]: row for row in null_rows}
    width = 920
    height = 250
    margin_left = 240
    bar_max = 100.0
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="24" y="32" font-family="Arial, sans-serif" font-size="18" font-weight="700">R251 behavior-tag alignment</text>',
        '<text x="24" y="55" font-family="Arial, sans-serif" font-size="12" fill="#555">Actual prompt tags vs session-preserving shuffled prompt tags (p95 null marker)</text>',
    ]
    y = 92
    for metric, label in metrics:
        row = row_lookup.get(metric, {})
        actual_value = float(actual.get(metric, 0.0))
        p95 = float(row.get("null_p95") or 0.0)
        actual_w = int((actual_value / bar_max) * 520)
        p95_x = margin_left + int((p95 / bar_max) * 520)
        lines.extend(
            [
                f'<text x="24" y="{y + 18}" font-family="Arial, sans-serif" font-size="13">{html.escape(label)}</text>',
                f'<rect x="{margin_left}" y="{y}" width="520" height="26" fill="#f1f5f9" stroke="#d0d7de"/>',
                f'<rect x="{margin_left}" y="{y}" width="{actual_w}" height="26" fill="#2563eb"/>',
                f'<line x1="{p95_x}" y1="{y - 5}" x2="{p95_x}" y2="{y + 31}" stroke="#dc2626" stroke-width="2"/>',
                f'<text x="{margin_left + 535}" y="{y + 18}" font-family="Arial, sans-serif" font-size="13">{actual_value:.2f}% actual, {p95:.2f}% null p95</text>',
            ]
        )
        y += 62
    lines.extend(
        [
            '<rect x="24" y="218" width="12" height="12" fill="#2563eb"/>',
            '<text x="42" y="229" font-family="Arial, sans-serif" font-size="12">actual</text>',
            '<line x1="100" y1="224" x2="124" y2="224" stroke="#dc2626" stroke-width="2"/>',
            '<text x="132" y="229" font-family="Arial, sans-serif" font-size="12">session-preserving shuffle p95</text>',
            "</svg>",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_markdown(
    path: Path,
    payload: dict[str, Any],
    null_rows: list[dict[str, Any]],
    prompt_rows: list[dict[str, Any]],
    low_rows: list[dict[str, Any]],
) -> None:
    metrics = payload["metrics"]
    lines = [
        "# R251 Behavior-Tag Alignment",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Boundary",
        "",
        "- Reads generated R170 semantic folded stacks only.",
        "- Does not read raw agent histories.",
        "- Does not call an LLM.",
        "- Does not add human labels or user responses.",
        "- Supports behavioral grounding only; C6 human semantic adequacy remains unsupported.",
        "",
        "## Main Metrics",
        "",
        "| metric | value |",
        "|---|---:|",
        f"| total system-effect weight | {payload['dataset']['total_weight']} |",
        f"| stack rows | {payload['dataset']['stack_rows']} |",
        f"| prompt tags | {payload['dataset']['unique_prompt_tags']} |",
        f"| session tags | {payload['dataset']['unique_session_tags']} |",
        f"| behavior keys | {payload['dataset']['unique_behavior_keys']} |",
        f"| behavior entropy | {metrics['behavior_entropy_bits']:.3f} bits |",
        f"| prompt uncertainty reduction | {metrics['prompt_behavior_uncertainty_reduction_pct']:.3f}% |",
        f"| prompt gain beyond session | {metrics['prompt_gain_beyond_session_pct']:.3f}% |",
        f"| prompt top-behavior purity | {metrics['prompt_top_behavior_purity_pct']:.3f}% |",
        "",
        "## Session-Preserving Null",
        "",
        "| metric | actual | null p95 | p value | pass p95 |",
        "|---|---:|---:|---:|---|",
    ]
    for row in null_rows:
        lines.append(
            f"| `{row['metric']}` | {row['actual']:.3f} | {row['null_p95']:.3f} | "
            f"{row['one_sided_p_value']:.4f} | {row['actual_gt_null_p95']} |"
        )
    lines.extend(
        [
            "",
            "## Top Prompt Profiles",
            "",
            "| prompt | weight | top behavior | top share | distinct behaviors |",
            "|---|---:|---|---:|---:|",
        ]
    )
    for row in prompt_rows[:10]:
        lines.append(
            f"| `{row['prompt_tag']}` | {row['total_weight']} | `{row['top_behavior']}` | "
            f"{row['top_behavior_share_pct']}% | {row['distinct_behaviors']} |"
        )
    lines.extend(
        [
            "",
            "## Low-Coherence Review Queue",
            "",
            "| prompt | weight | top share | distinct behaviors | top behaviors |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for row in low_rows[:10]:
        lines.append(
            f"| `{row['prompt_tag']}` | {row['total_weight']} | {row['top_behavior_share_pct']}% | "
            f"{row['distinct_behaviors']} | `{row['top_behaviors']}` |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "R251 is useful because it falsifies the weakest version of the tagging story: "
            "prompt tags are not treated as adequate merely because they are one-word strings. "
            "The run checks whether prompt tags retain behavior information beyond session "
            "membership under a session-preserving null. It still cannot decide whether a "
            "human developer would call each tag semantically correct; that requires the R124 "
            "label-return path.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folded", type=Path, default=DEFAULT_FOLDED)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--permutations", type=int, default=100)
    parser.add_argument("--seed", type=int, default=251)
    parser.add_argument("--profile-limit", type=int, default=40)
    parser.add_argument("--low-coherence-min-weight", type=int, default=100)
    args = parser.parse_args()

    if not args.folded.exists():
        raise FileNotFoundError(args.folded)

    rows = read_rows(args.folded)
    if not rows:
        raise RuntimeError("no prompt-tagged folded rows found")

    total_weight = sum(int(row["weight"]) for row in rows)
    actual_metrics = metrics_for_rows(rows)
    nulls = null_distributions(rows, permutations=args.permutations, seed=args.seed)
    null_rows = null_summary_rows(actual_metrics, nulls)
    prompt_rows = prompt_profile_rows(rows, limit=args.profile_limit)
    behavior_rows = behavior_profile_rows(rows, limit=args.profile_limit)
    low_rows = low_coherence_prompt_rows(
        rows,
        min_weight=args.low_coherence_min_weight,
        limit=args.profile_limit,
    )

    null_passes = {row["metric"]: bool(row["actual_gt_null_p95"]) for row in null_rows}
    behavior_alignment_supported = all(null_passes.values()) if null_passes else False

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    prompt_csv = out_dir / "prompt-behavior-profiles-r251.csv"
    behavior_csv = out_dir / "behavior-prompt-profiles-r251.csv"
    null_csv = out_dir / "session-shuffle-null-r251.csv"
    low_csv = out_dir / "low-coherence-prompts-r251.csv"
    svg_path = out_dir / "behavior-tag-alignment-r251.svg"
    json_path = out_dir / "behavior-tag-alignment-r251.json"
    md_path = out_dir / "behavior-tag-alignment-r251.md"

    write_csv(prompt_csv, prompt_rows, PROMPT_PROFILE_FIELDS)
    write_csv(behavior_csv, behavior_rows, BEHAVIOR_PROFILE_FIELDS)
    write_csv(null_csv, null_rows, NULL_FIELDS)
    write_csv(low_csv, low_rows, LOW_COHERENCE_FIELDS)
    write_svg(svg_path, actual_metrics, null_rows)

    payload = {
        "run_id": "R251",
        "status": "behavior_alignment_supported" if behavior_alignment_supported else "behavior_alignment_not_supported",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "dataset": {
            "folded_path": rel(args.folded),
            "folded_sha256": sha256_file(args.folded),
            "stack_rows": len(rows),
            "total_weight": total_weight,
            "unique_prompt_tags": len(weighted_counter(rows, "prompt")),
            "unique_session_tags": len(weighted_counter(rows, "session")),
            "unique_behavior_keys": len(weighted_counter(rows, "behavior")),
            "behavior_key": "process/effect/status",
        },
        "method": {
            "permutations": args.permutations,
            "seed": args.seed,
            "null": "session-preserving prompt-tag shuffle over expanded system-effect observations",
            "unit": "system-effect weight from folded stack samples",
        },
        "metrics": {key: round(value, 6) for key, value in actual_metrics.items()},
        "null_summary": null_rows,
        "claim_gates": {
            "behavior_alignment_supported": behavior_alignment_supported,
            "c6_human_semantic_adequacy_supported": False,
            "c5_developer_utility_supported": False,
            "weak_accept_supported": False,
        },
        "outputs": {
            "json": rel(json_path),
            "markdown": rel(md_path),
            "svg": rel(svg_path),
            "prompt_profiles_csv": rel(prompt_csv),
            "behavior_profiles_csv": rel(behavior_csv),
            "null_csv": rel(null_csv),
            "low_coherence_csv": rel(low_csv),
        },
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": repo_dirty(),
            "raw_trace_read": False,
            "llm_called": False,
            "human_labels_added": False,
            "participant_responses_added": False,
        },
    }
    write_json(json_path, payload)
    write_markdown(md_path, payload, null_rows, prompt_rows, low_rows)

    print(
        json.dumps(
            {
                "run_id": "R251",
                "status": payload["status"],
                "total_weight": total_weight,
                "prompt_gain_beyond_session_pct": payload["metrics"]["prompt_gain_beyond_session_pct"],
                "prompt_purity_pct": payload["metrics"]["prompt_top_behavior_purity_pct"],
                "weak_accept_supported": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
