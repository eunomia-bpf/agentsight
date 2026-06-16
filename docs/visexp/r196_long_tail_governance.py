#!/usr/bin/env python3
"""R196: generate an auditable long-tail tag governance packet.

The script reads generated AgentFlame/R189 artifacts only. It does not rescan or
mutate raw Codex/Claude traces. The goal is to make the open-vocabulary tag
layer operational: rare tags can be kept, merged through the existing canonical
overlay, sent to human/LLM regeneration, or flagged for contextual split.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_AGENTFLAME_DIR = REPO_ROOT / ".agentsight" / "agentflame" / "r170-full-current"
DEFAULT_R189_DIR = SCRIPT_DIR / "out" / "tag-consolidation-r189"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "long-tail-governance-r196"
R189_PATH = SCRIPT_DIR / "r189_tag_consolidation.py"

VALID_TAG_RE = re.compile(r"^[a-z][a-z0-9]{0,31}$")
GENERIC_TAGS = {
    "agent",
    "call",
    "change",
    "changes",
    "check",
    "code",
    "command",
    "file",
    "files",
    "fix",
    "ignored",
    "job",
    "model",
    "process",
    "prompt",
    "run",
    "task",
    "tool",
    "update",
    "work",
}

ACTION_ORDER = {
    "auto_canonicalize_existing": 0,
    "review_merge": 1,
    "contextual_split_candidate": 2,
    "regenerate_candidate": 3,
    "keep_rare_distinct": 4,
    "keep_head": 5,
}


def load_r189():
    spec = importlib.util.spec_from_file_location("r189_tag_consolidation", R189_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {R189_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


r189 = load_r189()


@dataclass(frozen=True)
class GovernanceConfig:
    session_tail_support: int = 100
    prompt_tail_support: int = 100
    llm_tail_support: int = 10
    regenerate_min_support: int = 3
    split_min_support: int = 250
    split_top_share_max: float = 0.45
    split_second_share_min: float = 0.15


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def pct(part: float | int, whole: float | int) -> float:
    return round(100.0 * float(part) / float(whole), 3) if whole else 0.0


def primary_support(profile: Any, dimension: str) -> int:
    if dimension == "llm":
        return int(profile.event_count)
    return int(profile.effect_weight or profile.row_count)


def tail_threshold(dimension: str, config: GovernanceConfig) -> int:
    if dimension == "session":
        return config.session_tail_support
    if dimension == "prompt":
        return config.prompt_tail_support
    return config.llm_tail_support


def generic_or_noisy(tag: str) -> bool:
    clean = r189.clean_tag(tag)
    if clean in GENERIC_TAGS:
        return True
    if len(clean) <= 2:
        return True
    return bool(r189.looks_compound_or_noisy(clean))


def top_share(counter: Counter[str]) -> tuple[float, float, int]:
    total = sum(counter.values())
    if not total:
        return 0.0, 0.0, 0
    values = [value for _, value in counter.most_common(2)]
    first = values[0] / total if values else 0.0
    second = values[1] / total if len(values) > 1 else 0.0
    return first, second, len(counter)


def multimodal_profile(profile: Any, dimension: str, config: GovernanceConfig) -> tuple[bool, list[str]]:
    checks: list[tuple[str, Counter[str]]] = []
    if dimension == "llm":
        checks = [("prompts", profile.prompts), ("sessions", profile.sessions), ("models", profile.models)]
    else:
        checks = [
            ("processes", profile.processes),
            ("effects", profile.effects),
            ("paths", profile.paths),
            ("contexts", profile.sessions if dimension == "prompt" else profile.prompts),
        ]

    reasons: list[str] = []
    for name, counter in checks:
        first, second, distinct = top_share(counter)
        if distinct >= 3 and first <= config.split_top_share_max and second >= config.split_second_share_min:
            reasons.append(f"multi_peak_{name}")
    return bool(reasons), reasons


def compact_counter(counter: Counter[str], limit: int = 6) -> str:
    return "; ".join(f"{key}={value}" for key, value in counter.most_common(limit))


def profile_digest(profile: Any, dimension: str) -> dict[str, str]:
    context_counter = profile.prompts if dimension in {"session", "llm"} else profile.sessions
    return {
        "top_processes": compact_counter(profile.processes),
        "top_effects": compact_counter(profile.effects),
        "top_paths": compact_counter(profile.paths),
        "top_context_tags": compact_counter(context_counter),
        "top_models": compact_counter(profile.models),
        "top_kinds": compact_counter(profile.kinds),
    }


def regeneration_context(row: dict[str, Any]) -> str:
    parts = [
        f"dimension={row['dimension']}",
        f"raw_tag={row['raw_tag']}",
        f"canonical_tag={row['canonical_tag']}",
        f"support={row['support']}",
        f"top_processes={row['top_processes']}",
        f"top_effects={row['top_effects']}",
        f"top_paths={row['top_paths']}",
        f"top_context_tags={row['top_context_tags']}",
        f"top_models={row['top_models']}",
        f"top_kinds={row['top_kinds']}",
    ]
    return "\n".join(part for part in parts if not part.endswith("="))


def governance_decision(
    mapping_row: dict[str, Any],
    profile: Any,
    dimension: str,
    config: GovernanceConfig,
) -> dict[str, Any]:
    tag = r189.clean_tag(str(mapping_row["raw_tag"]))
    support = int(mapping_row.get("support") or primary_support(profile, dimension))
    threshold = tail_threshold(dimension, config)
    is_tail = support < threshold
    is_generic = generic_or_noisy(tag)
    is_multimodal, split_reasons = multimodal_profile(profile, dimension, config)
    mapping_action = str(mapping_row.get("action") or "keep")
    mapping_reason = str(mapping_row.get("reason") or "")

    reasons: list[str] = []
    requires_review = False

    if mapping_action == "merge" and str(mapping_row.get("canonical_tag")) != tag:
        action = "auto_canonicalize_existing"
        reasons.append(f"r189_{mapping_reason or 'merge'}")
        requires_review = mapping_reason != "alias"
    elif mapping_action == "review":
        action = "review_merge"
        reasons.append("r189_review_suggestion_not_applied")
        requires_review = True
    elif is_generic and is_multimodal and support >= config.split_min_support:
        action = "contextual_split_candidate"
        reasons.extend(split_reasons)
        reasons.append("generic_or_noisy_tag")
        requires_review = True
    elif is_generic and support >= config.regenerate_min_support:
        action = "regenerate_candidate"
        reasons.append("generic_or_noisy_tag")
        if is_tail:
            reasons.append("long_tail")
        requires_review = True
    elif is_tail:
        action = "keep_rare_distinct"
        reasons.append("rare_distinct_by_current_profile")
    else:
        action = "keep_head"
        reasons.append("head_or_supported_tag")

    return {
        "governance_action": action,
        "governance_reasons": ";".join(reasons),
        "requires_review": requires_review,
        "is_long_tail": is_tail,
        "is_generic_or_noisy": is_generic,
        "is_multimodal": is_multimodal,
        "tail_threshold": threshold,
    }


def read_mapping_rows(mapping_path: Path) -> dict[tuple[str, str], dict[str, str]]:
    rows = read_csv(mapping_path)
    return {
        (str(row["dimension"]), r189.clean_tag(str(row["raw_tag"]))): row
        for row in rows
    }


def build_rows(agentflame_dir: Path, r189_dir: Path, config: GovernanceConfig) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    report_path = agentflame_dir / "agentflame.json"
    system_path = agentflame_dir / "semantic-system.folded.txt"
    token_path = agentflame_dir / "semantic-token.folded.txt"
    mapping_path = r189_dir / "canonical-tag-map-r189.csv"

    report = r189.read_json(report_path)
    system = r189.read_folded(system_path)
    token = r189.read_folded(token_path)
    profiles_by_dim = r189.collect_profiles(report, system, token)
    mapping_by_key = read_mapping_rows(mapping_path)

    rows: list[dict[str, Any]] = []
    missing_mapping = 0
    for dimension, profiles in profiles_by_dim.items():
        for tag, profile in sorted(profiles.items()):
            mapping = mapping_by_key.get((dimension, tag))
            if mapping is None:
                missing_mapping += 1
                mapping = {
                    "dimension": dimension,
                    "raw_tag": tag,
                    "canonical_tag": tag,
                    "suggested_tag": tag,
                    "action": "keep",
                    "reason": "missing_r189_mapping",
                    "confidence": "0",
                    "profile_similarity": "0",
                    "support": str(primary_support(profile, dimension)),
                }
            decision = governance_decision(mapping, profile, dimension, config)
            digest = profile_digest(profile, dimension)
            row = {
                "dimension": dimension,
                "raw_tag": tag,
                "canonical_tag": mapping.get("canonical_tag") or tag,
                "suggested_tag": mapping.get("suggested_tag") or tag,
                "r189_action": mapping.get("action") or "keep",
                "r189_reason": mapping.get("reason") or "",
                "r189_confidence": mapping.get("confidence") or "",
                "r189_profile_similarity": mapping.get("profile_similarity") or "",
                "row_count": int(profile.row_count),
                "effect_weight": int(profile.effect_weight),
                "event_count": int(profile.event_count),
                "token_weight": int(profile.token_weight),
                "support": int(mapping.get("support") or primary_support(profile, dimension)),
                **decision,
                **digest,
                "review_label": "",
                "review_notes": "",
            }
            context = regeneration_context(row)
            row["regeneration_context_hash"] = hashlib.sha256(context.encode("utf-8")).hexdigest()[:16]
            rows.append(row)

    provenance = {
        "agentflame_dir": rel(agentflame_dir),
        "agentflame_json": rel(report_path),
        "agentflame_json_sha256": sha256_file(report_path),
        "system_folded": rel(system_path),
        "system_folded_sha256": sha256_file(system_path),
        "token_folded": rel(token_path),
        "token_folded_sha256": sha256_file(token_path),
        "r189_mapping": rel(mapping_path),
        "r189_mapping_sha256": sha256_file(mapping_path),
        "missing_r189_mapping_rows": missing_mapping,
    }
    return rows, provenance


def llama_regenerate(llama_url: str, context: str, timeout: int) -> tuple[str, bool, str]:
    body = {
        "model": "local",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Return exactly one lowercase ASCII word for the coding-agent "
                    "tag. No punctuation, no explanation."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Choose a better one-word navigation tag for this redacted "
                    "behavior profile. Prefer existing concise task words when "
                    "they fit; otherwise invent one clear word.\n\n" + context[:4000]
                ),
            },
        ],
        "temperature": 0,
        "max_tokens": 8,
    }
    request = urllib.request.Request(
        llama_url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return "", False, f"{type(exc).__name__}: {exc}"
    try:
        text = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        return "", False, f"missing_content: {exc}"
    tag = r189.clean_tag(str(text).split()[0] if str(text).split() else "")
    return tag, bool(VALID_TAG_RE.fullmatch(tag)), ""


def apply_optional_regeneration(
    rows: list[dict[str, Any]],
    llama_url: str,
    regenerate_limit: int,
    timeout: int,
) -> dict[str, Any]:
    metrics = {
        "enabled": bool(llama_url and regenerate_limit),
        "attempted": 0,
        "valid": 0,
        "invalid": 0,
        "failures": [],
    }
    if not llama_url or regenerate_limit == 0:
        return metrics

    candidates = [
        row
        for row in rows
        if row["governance_action"] in {"regenerate_candidate", "contextual_split_candidate"}
    ]
    if regenerate_limit > 0:
        candidates = candidates[:regenerate_limit]

    for row in candidates:
        context = regeneration_context(row)
        tag, valid, error = llama_regenerate(llama_url, context, timeout)
        metrics["attempted"] += 1
        row["regenerated_tag"] = tag
        row["regenerated_valid"] = valid
        row["regeneration_error"] = error
        if valid:
            metrics["valid"] += 1
        else:
            metrics["invalid"] += 1
            if error:
                metrics["failures"].append(error)
    metrics["failures"] = metrics["failures"][:8]
    return metrics


def summarize(rows: list[dict[str, Any]], regeneration: dict[str, Any]) -> dict[str, Any]:
    by_action: Counter[str] = Counter(str(row["governance_action"]) for row in rows)
    by_dimension: dict[str, Any] = {}
    for dimension in sorted({str(row["dimension"]) for row in rows}):
        dim_rows = [row for row in rows if row["dimension"] == dimension]
        support_total = sum(int(row["support"]) for row in dim_rows)
        tail_rows = [row for row in dim_rows if row["is_long_tail"]]
        review_rows = [row for row in dim_rows if row["requires_review"]]
        action_counts = Counter(str(row["governance_action"]) for row in dim_rows)
        by_dimension[dimension] = {
            "unique_tags": len(dim_rows),
            "support_total": support_total,
            "long_tail_tags": len(tail_rows),
            "long_tail_support": sum(int(row["support"]) for row in tail_rows),
            "long_tail_support_pct": pct(sum(int(row["support"]) for row in tail_rows), support_total),
            "review_required_tags": len(review_rows),
            "review_required_support": sum(int(row["support"]) for row in review_rows),
            "review_required_support_pct": pct(sum(int(row["support"]) for row in review_rows), support_total),
            "actions": dict(sorted(action_counts.items())),
        }

    status = "long_tail_governance_candidates_ready_no_regeneration"
    if regeneration.get("enabled"):
        status = "long_tail_governance_candidates_ready_with_regeneration_smoke"
        if regeneration.get("invalid"):
            status = "long_tail_governance_regeneration_needs_review"

    return {
        "status": status,
        "tag_count": len(rows),
        "review_required_tags": sum(1 for row in rows if row["requires_review"]),
        "long_tail_tags": sum(1 for row in rows if row["is_long_tail"]),
        "action_counts": dict(sorted(by_action.items())),
        "dimensions": by_dimension,
        "regeneration": regeneration,
        "claim_gate": {
            "raw_tags_preserved": True,
            "canonical_overlay_only": True,
            "long_tail_governance_supported": True,
            "semantic_adequacy_supported": False,
            "canonicalization_quality_supported": False,
            "requires_independent_review_for_regenerated_tags": True,
            "llm_regeneration_is_candidate_only": True,
            "requires_r190_labels_for_merge_quality": True,
        },
    }


def write_markdown(path: Path, payload: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    summary = payload["summary"]
    lines = [
        "# R196 Long-Tail Tag Governance",
        "",
        f"Status: `{summary['status']}`",
        "",
        "## Scope",
        "",
        f"- Input AgentFlame artifact: `{payload['input']['agentflame_dir']}`.",
        f"- R189 mapping: `{payload['input']['r189_mapping']}`.",
        "- Raw agent traces are not read or modified.",
        "- Raw one-word tags are preserved; R196 only emits governance candidates.",
        "",
        "## Action Counts",
        "",
        "| action | tags |",
        "|---|---:|",
    ]
    for action, count in sorted(summary["action_counts"].items(), key=lambda item: ACTION_ORDER.get(item[0], 99)):
        lines.append(f"| `{action}` | {count} |")
    lines.extend(
        [
            "",
            "## Dimension Summary",
            "",
            "| dimension | tags | long-tail tags | long-tail support | review tags | review support |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for dimension, dim in sorted(summary["dimensions"].items()):
        lines.append(
            f"| {dimension} | {dim['unique_tags']} | {dim['long_tail_tags']} | "
            f"{dim['long_tail_support_pct']}% | {dim['review_required_tags']} | "
            f"{dim['review_required_support_pct']}% |"
        )
    lines.extend(
        [
            "",
            f"Review packet rows: {summary['review_required_tags']}; accepted review labels: 0.",
            "",
            "## Highest-Support Review Candidates",
            "",
            "| dimension | raw tag | action | support | reason | top profile |",
            "|---|---|---|---:|---|---|",
        ]
    )
    candidates = [row for row in rows if row["requires_review"]]
    candidates.sort(key=lambda row: (-int(row["support"]), ACTION_ORDER.get(str(row["governance_action"]), 99), str(row["raw_tag"])))
    for row in candidates[:30]:
        profile = row["top_processes"] or row["top_context_tags"] or row["top_models"]
        lines.append(
            f"| {row['dimension']} | `{row['raw_tag']}` | `{row['governance_action']}` | "
            f"{row['support']} | {row['governance_reasons']} | {profile} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "R196 supports a governance mechanism for long-tail tags: existing R189 "
            "merges stay auditable, risky review rows are surfaced, generic/noisy "
            "tags can be sent to regeneration, and high-support multi-peak tags can "
            "be split contextually. It does not prove semantic adequacy or merge "
            "quality. Optional LLM regeneration proposes candidate tags only; it does "
            "not count as C5 developer-utility evidence, C6 human adequacy evidence, "
            "or R190 merge-quality evidence. R124 human labels and R190 merge-risk "
            "labels are still required.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(
    agentflame_dir: Path,
    r189_dir: Path,
    out_dir: Path,
    config: GovernanceConfig,
    llama_url: str = "",
    regenerate_limit: int = 0,
    llama_timeout: int = 30,
) -> dict[str, Any]:
    rows, provenance = build_rows(agentflame_dir, r189_dir, config)
    rows.sort(key=lambda row: (ACTION_ORDER.get(str(row["governance_action"]), 99), -int(row["support"]), str(row["dimension"]), str(row["raw_tag"])))
    regeneration = apply_optional_regeneration(rows, llama_url, regenerate_limit, llama_timeout)
    summary = summarize(rows, regeneration)

    out_dir.mkdir(parents=True, exist_ok=True)
    all_fields = [
        "dimension",
        "raw_tag",
        "canonical_tag",
        "suggested_tag",
        "r189_action",
        "r189_reason",
        "r189_confidence",
        "r189_profile_similarity",
        "governance_action",
        "governance_reasons",
        "requires_review",
        "is_long_tail",
        "is_generic_or_noisy",
        "is_multimodal",
        "tail_threshold",
        "row_count",
        "effect_weight",
        "event_count",
        "token_weight",
        "support",
        "top_processes",
        "top_effects",
        "top_paths",
        "top_context_tags",
        "top_models",
        "top_kinds",
        "regeneration_context_hash",
        "regenerated_tag",
        "regenerated_valid",
        "regeneration_error",
        "review_label",
        "review_notes",
    ]
    write_csv(out_dir / "long-tail-governance-r196.csv", rows, all_fields)
    review_rows = [row for row in rows if row["requires_review"]]
    write_csv(out_dir / "long-tail-review-packet-r196.csv", review_rows, all_fields)

    payload = {
        "schema_version": 1,
        "run_id": "R196",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "input": provenance,
        "method": {
            "raw_tags_preserved": True,
            "raw_trace_policy": "read generated AgentFlame/R189 artifacts only; do not mutate raw traces",
            "governance_actions": sorted(ACTION_ORDER, key=lambda action: ACTION_ORDER[action]),
            "tail_thresholds": {
                "session_support": config.session_tail_support,
                "prompt_support": config.prompt_tail_support,
                "llm_events": config.llm_tail_support,
            },
            "regeneration_policy": (
                "optional llama.cpp-compatible profile-only regeneration for generic/noisy "
                "or contextual-split candidates; disabled unless --llama-url and --regenerate-limit are set"
            ),
        },
        "summary": summary,
        "artifacts": {
            "governance_csv": rel(out_dir / "long-tail-governance-r196.csv"),
            "review_packet_csv": rel(out_dir / "long-tail-review-packet-r196.csv"),
            "summary_md": rel(out_dir / "long-tail-governance-r196.md"),
        },
        "provenance": {
            "git_head": git(["rev-parse", "HEAD"]),
            "git_status_short": git(["status", "--short"]),
            "script": rel(Path(__file__)),
            "script_sha256": sha256_file(Path(__file__)),
        },
    }
    write_json(out_dir / "long-tail-governance-r196.json", payload)
    write_markdown(out_dir / "long-tail-governance-r196.md", payload, rows)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agentflame-dir", type=Path, default=DEFAULT_AGENTFLAME_DIR)
    parser.add_argument("--r189-dir", type=Path, default=DEFAULT_R189_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--llama-url", default="")
    parser.add_argument("--regenerate-limit", type=int, default=0)
    parser.add_argument("--llama-timeout", type=int, default=30)
    args = parser.parse_args()

    payload = run(
        args.agentflame_dir,
        args.r189_dir,
        args.out_dir,
        GovernanceConfig(),
        llama_url=args.llama_url,
        regenerate_limit=args.regenerate_limit,
        llama_timeout=args.llama_timeout,
    )
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
