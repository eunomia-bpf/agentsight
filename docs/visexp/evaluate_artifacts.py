#!/usr/bin/env python3
"""Evaluate whether semantic flamegraph artifacts add non-trivial information.

This is intentionally not a user-study substitute. It is an offline checker for
the current artifact: aggregation strength, semantic separation relative to
non-semantic baselines, tag contract quality, and claim-gate status.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TAG_RE = re.compile(r"^[a-z][a-z0-9]{1,15}$")
MIN_MIXED_WEIGHT_SHARE_PCT = 5.0
GENERIC_TAGS = {
    "agent",
    "analysis",
    "answer",
    "assistant",
    "chat",
    "code",
    "coding",
    "data",
    "doing",
    "general",
    "prompt",
    "request",
    "response",
    "session",
    "task",
    "unknown",
    "work",
    "working",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_folded(path: Path) -> Counter[str]:
    stacks: Counter[str] = Counter()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.rstrip("\n")
            if not line:
                continue
            stack, _, weight = line.rpartition(" ")
            if not stack or not weight.isdigit():
                raise AssertionError(f"invalid folded line in {path}: {line[:120]}")
            stacks[stack] += int(weight)
    return stacks


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def frame_value(frames: list[str], prefix: str, default: str = "unknown") -> str:
    for frame in frames:
        if frame.startswith(prefix):
            return frame.split(":", 1)[1]
    return default


def drop_frame_prefixes(stack: str, prefixes: tuple[str, ...]) -> str:
    return ";".join(frame for frame in stack.split(";") if not frame.startswith(prefixes))


def shannon_entropy(counter: Counter[str]) -> float:
    total = sum(counter.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in counter.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy


def pct(part: int | float, whole: int | float) -> float:
    return round(100.0 * part / whole, 3) if whole else 0.0


def compression_summary(stacks: Counter[str]) -> dict[str, Any]:
    total = sum(stacks.values())
    unique = len(stacks)
    repeated_stacks = sum(1 for weight in stacks.values() if weight > 1)
    collapsed = sum(weight - 1 for weight in stacks.values() if weight > 1)
    return {
        "total_observations": total,
        "unique_stacks": unique,
        "compression_ratio": round(total / unique, 3) if unique else 0,
        "repeated_stack_count": repeated_stacks,
        "collapsed_observations": collapsed,
        "collapsed_observation_share_pct": pct(collapsed, total),
        "max_stack_reuse": max(stacks.values()) if stacks else 0,
    }


def mixing_summary(
    stacks: Counter[str],
    drop_prefixes: tuple[str, ...],
    baseline_kind: str,
    example_limit: int = 15,
) -> dict[str, Any]:
    buckets: dict[str, Counter[str]] = defaultdict(Counter)
    for stack, weight in stacks.items():
        frames = stack.split(";")
        semantic_key = (
            f"session:{frame_value(frames, 'session:')}/"
            f"prompt:{frame_value(frames, 'prompt:')}"
        )
        baseline_stack = drop_frame_prefixes(stack, drop_prefixes)
        buckets[baseline_stack][semantic_key] += weight

    mixed = {
        stack: variants
        for stack, variants in buckets.items()
        if len(variants) > 1
    }
    total_weight = sum(stacks.values())
    mixed_weight = sum(sum(variants.values()) for variants in mixed.values())
    examples = []
    for stack, variants in sorted(
        mixed.items(),
        key=lambda item: (-sum(item[1].values()), -len(item[1]), item[0]),
    )[:example_limit]:
        examples.append(
            {
                "baseline_kind": baseline_kind,
                "baseline_stack": stack,
                "weight": sum(variants.values()),
                "semantic_variant_count": len(variants),
                "top_semantic_variants": [
                    {"semantic": key, "weight": value}
                    for key, value in variants.most_common(8)
                ],
            }
        )
    return {
        "baseline_kind": baseline_kind,
        "baseline_bucket_count": len(buckets),
        "mixed_bucket_count": len(mixed),
        "mixed_bucket_share_pct": pct(len(mixed), len(buckets)),
        "mixed_weight": mixed_weight,
        "mixed_weight_share_pct": pct(mixed_weight, total_weight),
        "max_semantic_variants_per_bucket": max((len(v) for v in buckets.values()), default=0),
        "examples": examples,
    }


def tag_quality(
    prompt_rows: list[dict[str, str]],
    sessions: list[dict[str, Any]],
    aggregation: dict[str, Any],
) -> dict[str, Any]:
    prompt_tags = Counter(row.get("prompt_tag", "") for row in prompt_rows)
    session_tags = Counter(str(row.get("session_tag", "")) for row in sessions)
    invalid_prompt_tags = sorted(tag for tag in prompt_tags if not TAG_RE.fullmatch(tag))
    generic_prompt_rows = sum(count for tag, count in prompt_tags.items() if tag in GENERIC_TAGS)
    prompt_total = sum(prompt_tags.values())

    by_hash: dict[str, Counter[str]] = defaultdict(Counter)
    for row in prompt_rows:
        prompt_hash = row.get("prompt_hash", "")
        if prompt_hash:
            by_hash[prompt_hash][row.get("prompt_tag", "")] += 1
    hash_conflicts = {
        prompt_hash: tags
        for prompt_hash, tags in by_hash.items()
        if len(tags) > 1
    }

    prompt_entropy = shannon_entropy(prompt_tags)
    return {
        "prompt_rows": prompt_total,
        "unique_prompt_tags": len(prompt_tags),
        "top_prompt_tags": [
            {"tag": tag, "count": count}
            for tag, count in prompt_tags.most_common(12)
        ],
        "prompt_tag_entropy_bits": round(prompt_entropy, 3),
        "prompt_tag_normalized_entropy": round(
            prompt_entropy / math.log2(len(prompt_tags)), 3
        )
        if len(prompt_tags) > 1
        else 0.0,
        "generic_prompt_row_share_pct": pct(generic_prompt_rows, prompt_total),
        "invalid_prompt_tags": invalid_prompt_tags[:20],
        "invalid_prompt_tag_count": len(invalid_prompt_tags),
        "same_hash_multi_tag_count": len(hash_conflicts),
        "same_hash_multi_tag_examples": [
            {
                "prompt_hash": prompt_hash,
                "tags": dict(tags),
            }
            for prompt_hash, tags in list(sorted(hash_conflicts.items()))[:10]
        ],
        "session_count": len(sessions),
        "unique_session_tags": len(session_tags),
        "top_session_tags": [
            {"tag": tag, "count": count}
            for tag, count in session_tags.most_common(12)
        ],
        "artifact_tag_contract_invalid_count": aggregation.get("tag_contract", {}).get(
            "invalid_count", 0
        ),
    }


def prompt_weight_summary(stacks: Counter[str]) -> dict[str, Any]:
    by_prompt: Counter[str] = Counter()
    by_session: Counter[str] = Counter()
    by_pair: Counter[str] = Counter()
    for stack, weight in stacks.items():
        frames = stack.split(";")
        session = frame_value(frames, "session:")
        prompt = frame_value(frames, "prompt:")
        by_prompt[prompt] += weight
        by_session[session] += weight
        by_pair[f"{session}/{prompt}"] += weight
    total = sum(stacks.values())
    return {
        "total_system_observations": total,
        "unique_prompt_tags": len(by_prompt),
        "unique_session_prompt_pairs": len(by_pair),
        "top_prompt_weight_share_pct": pct(by_prompt.most_common(1)[0][1], total) if by_prompt else 0.0,
        "top5_prompt_weight_share_pct": pct(sum(v for _, v in by_prompt.most_common(5)), total),
        "top_prompt_tags": [
            {"prompt_tag": tag, "weight": weight, "share_pct": pct(weight, total)}
            for tag, weight in by_prompt.most_common(12)
        ],
        "top_session_prompt_pairs": [
            {"session_prompt": tag, "weight": weight, "share_pct": pct(weight, total)}
            for tag, weight in by_pair.most_common(12)
        ],
    }


def tag_stability_evidence(stability: dict[str, Any] | None) -> str:
    if not stability:
        return "tag_stability_smoke=missing"
    pieces = [f"smoke_verdict={stability.get('smoke_verdict', 'unknown')}"]
    annotators = stability.get("annotator_metrics", {})
    if isinstance(annotators, dict):
        for name, metrics in sorted(annotators.items()):
            if isinstance(metrics, dict):
                pieces.append(
                    f"{name}_stable_pct={metrics.get('exact_stable_fragment_share_pct')}"
                )
                pieces.append(
                    f"{name}_generic_pct={metrics.get('generic_output_share_pct')}"
                )
    pairs = stability.get("cross_annotator_metrics", {}).get("pairs", [])
    if isinstance(pairs, list):
        for pair in pairs:
            if isinstance(pair, dict):
                pieces.append(
                    f"{pair.get('left')}_vs_{pair.get('right')}_exact_pct="
                    f"{pair.get('modal_exact_match_pct')}"
                )
    return " ".join(pieces)


def user_task_evidence(
    bundle: dict[str, Any] | None,
    results: dict[str, Any] | None = None,
    response_template_exists: bool = False,
) -> str:
    if not bundle:
        return "task_bundle=missing scorer=ready participant_results=missing"
    tasks = bundle.get("tasks", [])
    status = bundle.get("status", "unknown")
    template = "present" if response_template_exists else "missing"
    if not results:
        return (
            f"task_bundle={status} task_count={len(tasks)} "
            "scorer=ready "
            f"response_template={template} "
            "participant_results=missing"
        )
    if results.get("status") == "participant_results_empty":
        return (
            f"task_bundle={status} task_count={len(tasks)} "
            "scorer=ready "
            f"response_template={template} "
            f"ignored_placeholder_rows={results.get('ignored_placeholder_rows')} "
            "participant_results=missing"
        )
    return (
        f"task_bundle={status} task_count={len(tasks)} "
        f"scorer_results={results.get('status', 'unknown')} "
        f"participants={results.get('participant_count')} "
        f"responses={results.get('response_count')} "
        f"exact_accuracy_pct={results.get('summary', {}).get('overall', {}).get('exact_accuracy_pct')}"
    )


def effect_lineage_evidence(lineage: dict[str, Any] | None) -> str:
    if not lineage:
        return "effect_lineage_smoke=missing live_exact_capture=missing"
    return (
        f"effect_lineage_smoke={lineage.get('status', 'unknown')} "
        f"source={lineage.get('source', 'unknown')} "
        f"effect_events={lineage.get('effect_events')} "
        f"join_rate_pct={lineage.get('join_rate_pct')} "
        f"orphans={lineage.get('orphan_effect_events')} "
        f"orphan_reasons={lineage.get('orphan_reasons', {})} "
        "live_exact_capture=missing"
    )


def build_claim_gates(
    aggregation: dict[str, Any],
    compression: dict[str, Any],
    nonsemantic_mixing: dict[str, Any],
    flat_mixing: dict[str, Any],
    quality: dict[str, Any],
    stability: dict[str, Any] | None = None,
    user_tasks: dict[str, Any] | None = None,
    user_task_results: dict[str, Any] | None = None,
    response_template_exists: bool = False,
    effect_lineage: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    c1_ok = compression["compression_ratio"] > 1 and compression["repeated_stack_count"] > 0
    c2_ok = (
        quality["artifact_tag_contract_invalid_count"] == 0
        and quality["invalid_prompt_tag_count"] == 0
        and quality["unique_prompt_tags"] > 1
    )
    c3_ok = (
        nonsemantic_mixing["mixed_bucket_count"] > 0
        and flat_mixing["mixed_bucket_count"] > 0
        and nonsemantic_mixing["mixed_weight_share_pct"] >= MIN_MIXED_WEIGHT_SHARE_PCT
        and flat_mixing["mixed_weight_share_pct"] >= MIN_MIXED_WEIGHT_SHARE_PCT
    )
    source_counts = aggregation.get("source_counts", {})
    agent_diff_exists = source_counts.get("codex", 0) or source_counts.get("claude", 0)
    return [
        {
            "claim": "C1 folded aggregation",
            "verdict": "supported" if c1_ok else "unsupported",
            "oracle": "system folded total exceeds unique stacks and repeated stacks exist",
            "evidence": (
                f"compression={compression['compression_ratio']} "
                f"repeated={compression['repeated_stack_count']}"
            ),
        },
        {
            "claim": "C2 one-word tags in stack grammar",
            "verdict": "supported" if c2_ok else "partial",
            "oracle": "all committed tags match the one-word grammar and vocabulary is non-trivial",
            "evidence": (
                f"invalid={quality['invalid_prompt_tag_count']} "
                f"unique_prompt_tags={quality['unique_prompt_tags']}"
            ),
        },
        {
            "claim": "C3 semantic stacks add information beyond flat/nonsemantic baselines",
            "verdict": "supported" if c3_ok else "partial",
            "oracle": "baseline buckets mix multiple session/prompt tags that semantic stacks separate",
            "evidence": (
                f"nonsemantic_mixed={nonsemantic_mixing['mixed_bucket_count']} "
                f"nonsemantic_weight_pct={nonsemantic_mixing['mixed_weight_share_pct']} "
                f"flat_mixed={flat_mixing['mixed_bucket_count']} "
                f"flat_weight_pct={flat_mixing['mixed_weight_share_pct']}"
            ),
        },
        {
            "claim": "D1 normalized agent differences",
            "verdict": "diagnostic" if agent_diff_exists else "unsupported",
            "oracle": "observational, unpaired source cohorts exist; no causal benchmark claim",
            "evidence": f"sources={aggregation.get('source_counts', {})}",
        },
        {
            "claim": "C5 user utility over trace tree/process logs",
            "verdict": "unsupported",
            "oracle": "requires scored participant responses with time, accuracy, false positives, and confidence",
            "evidence": user_task_evidence(user_tasks, user_task_results, response_template_exists),
        },
        {
            "claim": "C4 exact AgentSight effect stream preserves value",
            "verdict": "unsupported",
            "oracle": "requires live AgentSight exact effects from real sessions to pass lineage checker",
            "evidence": effect_lineage_evidence(effect_lineage),
        },
        {
            "claim": "C6 tag stability and adequacy",
            "verdict": "partial" if quality["same_hash_multi_tag_count"] == 0 else "unsupported",
            "oracle": "smoke checks repeated-run syntax/stability; human adequacy remains required",
            "evidence": (
                f"same_hash_multi_tag_count={quality['same_hash_multi_tag_count']} "
                f"{tag_stability_evidence(stability)}"
            ).strip(),
        },
    ]


def write_mixing_csv(path: Path, sections: list[dict[str, Any]]) -> None:
    fields = [
        "baseline_kind",
        "rank",
        "weight",
        "semantic_variant_count",
        "top_semantic_variants",
        "baseline_stack",
    ]
    rows: list[dict[str, Any]] = []
    for section in sections:
        for idx, example in enumerate(section["examples"], 1):
            rows.append(
                {
                    "baseline_kind": example["baseline_kind"],
                    "rank": idx,
                    "weight": example["weight"],
                    "semantic_variant_count": example["semantic_variant_count"],
                    "top_semantic_variants": "; ".join(
                        f"{item['semantic']}={item['weight']}"
                        for item in example["top_semantic_variants"]
                    ),
                    "baseline_stack": example["baseline_stack"],
                }
            )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_claim_csv(path: Path, gates: list[dict[str, str]]) -> None:
    fields = ["claim", "verdict", "oracle", "evidence"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(gates)


def write_summary_md(path: Path, result: dict[str, Any]) -> None:
    compression = result["aggregation_strength"]["semantic_system"]
    nonsemantic = result["semantic_information_gain"]["nonsemantic_stack_mixing"]
    flat = result["semantic_information_gain"]["flat_effect_mixing"]
    quality = result["tag_quality"]
    gates = result["claim_gates"]
    lines = [
        "# Semantic Flamegraph Evaluation",
        "",
        "This report is generated by `evaluate_artifacts.py` from committed `out/` artifacts.",
        "It is an artifact audit, not a substitute for the planned human and paired-agent experiments.",
        "",
        "## Current Artifact Metrics",
        "",
        f"- Semantic system compression: {compression['compression_ratio']}x "
        f"({compression['total_observations']} observations, {compression['unique_stacks']} stacks).",
        f"- Collapsed observation share: {compression['collapsed_observation_share_pct']}%.",
        f"- Non-semantic baseline mixed buckets: {nonsemantic['mixed_bucket_count']} "
        f"({nonsemantic['mixed_weight_share_pct']}% of observation weight).",
        f"- Flat effect baseline mixed buckets: {flat['mixed_bucket_count']} "
        f"({flat['mixed_weight_share_pct']}% of observation weight).",
        f"- Prompt tags: {quality['unique_prompt_tags']} unique, "
        f"{quality['generic_prompt_row_share_pct']}% generic rows, "
        f"{quality['same_hash_multi_tag_count']} same-hash tag conflicts.",
        "",
        "## Claim Gates",
        "",
        "| Claim | Verdict | Evidence |",
        "|-------|---------|----------|",
    ]
    for gate in gates:
        lines.append(
            f"| {gate['claim']} | {gate['verdict']} | {gate['evidence']} |"
        )
    lines.extend(
        [
            "",
            "## Highest-Value Next Runs",
            "",
            "1. Collect a B4 response CSV and score it with `score_user_task_results.py` to test C5.",
            "2. Expand B5 with manual adequacy labels and a larger multi-model tag stability run for C6.",
            "3. Run the B3 lineage checker on live exact AgentSight effects from real sessions to test C4.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(out_dir: Path, write_outputs: bool = True) -> dict[str, Any]:
    aggregation = read_json(out_dir / "aggregation.json")
    sessions = read_json(out_dir / "sessions.json")
    prompt_rows = read_csv_rows(out_dir / "prompt-tags.csv")
    system = read_folded(out_dir / "semantic-system.folded.txt")
    nonsemantic = read_folded(out_dir / "nonsemantic-system.folded.txt")
    token = read_folded(out_dir / "semantic-token.folded.txt")

    semantic_compression = compression_summary(system)
    nonsemantic_compression = compression_summary(nonsemantic)
    token_compression = compression_summary(token)
    nonsemantic_mixing = mixing_summary(
        system,
        ("session:", "prompt:"),
        "nonsemantic_without_session_prompt",
    )
    flat_mixing = mixing_summary(
        system,
        ("project:", "agent:", "session:", "prompt:"),
        "flat_effect_without_project_agent_session_prompt",
    )
    quality = tag_quality(prompt_rows, sessions, aggregation)
    prompt_weights = prompt_weight_summary(system)
    stability_path = out_dir / "tag-stability-smoke.json"
    stability = read_json(stability_path) if stability_path.exists() else None
    user_tasks_path = out_dir / "user-task-benchmark.json"
    user_tasks = read_json(user_tasks_path) if user_tasks_path.exists() else None
    user_task_results_path = out_dir / "user-task-results.json"
    user_task_results = read_json(user_task_results_path) if user_task_results_path.exists() else None
    response_template_exists = (out_dir / "user-task-response-template.csv").exists()
    effect_lineage_path = out_dir / "effect-lineage-smoke.json"
    effect_lineage = read_json(effect_lineage_path) if effect_lineage_path.exists() else None
    gates = build_claim_gates(
        aggregation,
        semantic_compression,
        nonsemantic_mixing,
        flat_mixing,
        quality,
        stability,
        user_tasks,
        user_task_results,
        response_template_exists,
        effect_lineage,
    )

    result = {
        "schema_version": 1,
        "source_artifact": {
            "out_dir": str(out_dir),
            "session_fingerprint": aggregation.get("session_fingerprint"),
            "input_manifest_sha256": aggregation.get("input_manifest_sha256"),
        },
        "aggregation_strength": {
            "semantic_system": semantic_compression,
            "nonsemantic_system": nonsemantic_compression,
            "semantic_token": token_compression,
        },
        "semantic_information_gain": {
            "interpretation": (
                "A mixed baseline bucket means ordinary/nonsemantic grouping merges "
                "multiple session/prompt tags that semantic stacks keep separate."
            ),
            "nonsemantic_stack_mixing": nonsemantic_mixing,
            "flat_effect_mixing": flat_mixing,
            "prompt_weight_concentration": prompt_weights,
        },
        "tag_quality": quality,
        "tag_stability_smoke": stability,
        "user_task_benchmark": user_tasks,
        "user_task_results": user_task_results,
        "effect_lineage_smoke": effect_lineage,
        "claim_gates": gates,
    }

    if write_outputs:
        (out_dir / "evaluation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        write_mixing_csv(
            out_dir / "semantic-mixing.csv",
            [nonsemantic_mixing, flat_mixing],
        )
        write_claim_csv(out_dir / "claim-gates.csv", gates)
        write_summary_md(out_dir / "evaluation-summary.md", result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent / "out"))
    parser.add_argument("--no-write", action="store_true", help="only print the evaluation JSON")
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    evaluation = run(Path(args.out), write_outputs=not args.no_write)
    print(json.dumps(evaluation, indent=2))
