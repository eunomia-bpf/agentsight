#!/usr/bin/env python3
"""R201: sensitivity analysis for R196 long-tail governance.

This script reads generated AgentFlame/R189 artifacts only. It does not read or
modify raw Codex/Claude traces. The purpose is to test whether the R196
long-tail governance story is robust to reasonable threshold and generic-vocab
changes, not to prove semantic adequacy.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_AGENTFLAME_DIR = REPO_ROOT / ".agentsight" / "agentflame" / "r170-full-current"
DEFAULT_R189_DIR = SCRIPT_DIR / "out" / "tag-consolidation-r189"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "long-tail-sensitivity-r201"
R196_PATH = SCRIPT_DIR / "r196_long_tail_governance.py"


def load_r196():
    spec = importlib.util.spec_from_file_location("r196_long_tail_governance", R196_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {R196_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


r196 = load_r196()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


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
        import subprocess

        return subprocess.check_output(
            ["git", *args],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def pct(part: float | int, whole: float | int) -> float:
    return round(100.0 * float(part) / float(whole), 3) if whole else 0.0


def grid_rationale() -> dict[str, str]:
    return {
        "tail_thresholds": (
            "Sweep half/default/double support cutoffs: 50/100/200 for "
            "session and prompt tags, and 5/10/20 for LLM-call tags."
        ),
        "split_thresholds": (
            "Sweep permissive and conservative multi-peak detection while "
            "holding the baseline tail thresholds fixed."
        ),
        "generic_vocabulary": (
            "Perturb the noisy/generic-token list in both directions to test "
            "routing stability without mutating raw tags."
        ),
    }


def variant_specs() -> list[dict[str, Any]]:
    default_generics = sorted(r196.GENERIC_TAGS)
    expanded_generics = sorted(set(default_generics) | {"bashoutput", "output", "localization", "localized"})
    narrow_generics = sorted(set(default_generics) - {"codex", "agent", "model"})
    return [
        {
            "variant": "baseline",
            "description": "R196 default thresholds and generic/noisy vocabulary.",
            "config": r196.GovernanceConfig(),
            "generic_tags": default_generics,
        },
        {
            "variant": "lower_tail_threshold",
            "description": "More tags qualify as supported heads; fewer rows are long-tail by support.",
            "config": r196.GovernanceConfig(session_tail_support=50, prompt_tail_support=50, llm_tail_support=5),
            "generic_tags": default_generics,
        },
        {
            "variant": "higher_tail_threshold",
            "description": "More tags qualify as long-tail; tests review-required row/support stability.",
            "config": r196.GovernanceConfig(session_tail_support=200, prompt_tail_support=200, llm_tail_support=20),
            "generic_tags": default_generics,
        },
        {
            "variant": "aggressive_split",
            "description": "Lower contextual-split support and allow broader multi-peak profiles.",
            "config": r196.GovernanceConfig(
                session_tail_support=100,
                prompt_tail_support=100,
                llm_tail_support=10,
                split_min_support=100,
                split_top_share_max=0.60,
                split_second_share_min=0.10,
            ),
            "generic_tags": default_generics,
        },
        {
            "variant": "conservative_split",
            "description": "Higher contextual-split support and stricter second-peak requirement.",
            "config": r196.GovernanceConfig(
                session_tail_support=100,
                prompt_tail_support=100,
                llm_tail_support=10,
                split_min_support=500,
                split_top_share_max=0.35,
                split_second_share_min=0.20,
            ),
            "generic_tags": default_generics,
        },
        {
            "variant": "narrow_generic_vocab",
            "description": "Treat project/source identifiers as less automatically generic.",
            "config": r196.GovernanceConfig(),
            "generic_tags": narrow_generics,
        },
        {
            "variant": "expanded_generic_vocab",
            "description": "Route more known noisy model-output words to review/regeneration.",
            "config": r196.GovernanceConfig(),
            "generic_tags": expanded_generics,
        },
    ]


def run_variant(agentflame_dir: Path, r189_dir: Path, spec: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    original_generics = set(r196.GENERIC_TAGS)
    try:
        r196.GENERIC_TAGS = set(spec["generic_tags"])
        rows, provenance = r196.build_rows(agentflame_dir, r189_dir, spec["config"])
        rows.sort(key=lambda row: (str(row["dimension"]), str(row["raw_tag"])))
        summary = r196.summarize(rows, {"enabled": False, "attempted": 0, "valid": 0, "invalid": 0, "failures": []})
        return rows, {"summary": summary, "provenance": provenance}
    finally:
        r196.GENERIC_TAGS = original_generics


def rows_by_key(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(str(row["dimension"]), str(row["raw_tag"])): row for row in rows}


def compute_variant_record(
    spec: dict[str, Any],
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
    baseline_rows_by_key: dict[tuple[str, str], dict[str, Any]] | None,
    baseline_head_keys: set[tuple[str, str]],
) -> dict[str, Any]:
    total_support = sum(int(row["support"]) for row in rows)
    review_support = sum(int(row["support"]) for row in rows if row["requires_review"])
    long_tail_support = sum(int(row["support"]) for row in rows if row["is_long_tail"])
    action_counts = {action: int(summary["action_counts"].get(action, 0)) for action in r196.ACTION_ORDER}

    current_by_key = rows_by_key(rows)
    changed_from_baseline = 0
    review_changed_from_baseline = 0
    if baseline_rows_by_key is not None:
        for key, row in current_by_key.items():
            base = baseline_rows_by_key.get(key)
            if base is None:
                continue
            if str(base["governance_action"]) != str(row["governance_action"]):
                changed_from_baseline += 1
            if bool(base["requires_review"]) != bool(row["requires_review"]):
                review_changed_from_baseline += 1

    head_still_head = sum(
        1
        for key in baseline_head_keys
        if current_by_key.get(key) is not None and current_by_key[key]["governance_action"] == "keep_head"
    )
    head_to_review = sum(
        1
        for key in baseline_head_keys
        if current_by_key.get(key) is not None and current_by_key[key]["requires_review"]
    )

    config = spec["config"]
    return {
        "variant": spec["variant"],
        "description": spec["description"],
        "session_tail_support": config.session_tail_support,
        "prompt_tail_support": config.prompt_tail_support,
        "llm_tail_support": config.llm_tail_support,
        "regenerate_min_support": config.regenerate_min_support,
        "split_min_support": config.split_min_support,
        "split_top_share_max": config.split_top_share_max,
        "split_second_share_min": config.split_second_share_min,
        "generic_tag_count": len(spec["generic_tags"]),
        "tag_count": len(rows),
        "total_support": total_support,
        "review_required_tags": int(summary["review_required_tags"]),
        "review_required_support": review_support,
        "review_required_support_pct": pct(review_support, total_support),
        "long_tail_tags": int(summary["long_tail_tags"]),
        "long_tail_support": long_tail_support,
        "long_tail_support_pct": pct(long_tail_support, total_support),
        "changed_action_tags_vs_baseline": changed_from_baseline,
        "changed_review_gate_tags_vs_baseline": review_changed_from_baseline,
        "baseline_head_tags": len(baseline_head_keys),
        "baseline_heads_still_head": head_still_head,
        "baseline_head_stability_pct": pct(head_still_head, len(baseline_head_keys)),
        "baseline_heads_to_review": head_to_review,
        **{f"action_{action}": count for action, count in action_counts.items()},
    }


def movement_rows(
    baseline_rows: list[dict[str, Any]],
    variant_name: str,
    rows: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    base = rows_by_key(baseline_rows)
    out: list[dict[str, Any]] = []
    for row in rows:
        key = (str(row["dimension"]), str(row["raw_tag"]))
        base_row = base.get(key)
        if base_row is None:
            continue
        action_changed = str(base_row["governance_action"]) != str(row["governance_action"])
        review_changed = bool(base_row["requires_review"]) != bool(row["requires_review"])
        if not action_changed and not review_changed:
            continue
        out.append(
            {
                "variant": variant_name,
                "dimension": row["dimension"],
                "raw_tag": row["raw_tag"],
                "support": int(row["support"]),
                "baseline_action": base_row["governance_action"],
                "variant_action": row["governance_action"],
                "baseline_requires_review": base_row["requires_review"],
                "variant_requires_review": row["requires_review"],
                "is_generic_or_noisy": row["is_generic_or_noisy"],
                "is_multimodal": row["is_multimodal"],
                "top_processes": row["top_processes"],
                "top_context_tags": row["top_context_tags"],
            }
        )
    out.sort(key=lambda item: (-int(item["support"]), str(item["variant"]), str(item["dimension"]), str(item["raw_tag"])))
    return out[:limit]


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# R201 Long-Tail Governance Sensitivity",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Scope",
        "",
        "- Reads generated R170 AgentFlame and R189 canonical-tag artifacts only.",
        "- Does not read or mutate raw Codex/Claude traces.",
        "- Tests whether R196 long-tail governance is robust to threshold and generic-vocabulary changes.",
        "- Does not prove tag adequacy, merge quality, developer utility, or community adoption.",
        "",
        "## Grid Rationale",
        "",
        f"- Tail thresholds: {payload['method']['sensitivity_grid_rationale']['tail_thresholds']}",
        f"- Split thresholds: {payload['method']['sensitivity_grid_rationale']['split_thresholds']}",
        f"- Generic vocabulary: {payload['method']['sensitivity_grid_rationale']['generic_vocabulary']}",
        "",
        "## Variant Summary",
        "",
        "| variant | review tags | review support | long-tail tags | long-tail support | changed actions | head stability |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["variant_records"]:
        lines.append(
            f"| `{row['variant']}` | {row['review_required_tags']} | "
            f"{row['review_required_support_pct']}% | {row['long_tail_tags']} | "
            f"{row['long_tail_support_pct']}% | {row['changed_action_tags_vs_baseline']} | "
            f"{row['baseline_head_stability_pct']}% |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Baseline review-required support is `{payload['baseline']['review_required_support_pct']}%` of total support.",
            f"- Worst variant review-required support is `{payload['extremes']['max_review_support_pct']['review_required_support_pct']}%` in `{payload['extremes']['max_review_support_pct']['variant']}`.",
            f"- Lowest baseline-head stability is `{payload['extremes']['min_head_stability_pct']['baseline_head_stability_pct']}%` in `{payload['extremes']['min_head_stability_pct']['variant']}`.",
            "- These are policy-sensitivity measurements. Any regenerated or merged tag still needs R190/R124-style human review before a quality claim.",
            "",
            "## Claim Boundary",
            "",
            "R201 strengthens the design argument that R196 is an auditable governance layer rather than an opaque taxonomy. It does not support C5 user utility, C6 tag adequacy, canonicalization quality, or community adoption. It only reports how review-required row/support counts and display grouping change within this policy grid.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(agentflame_dir: Path, r189_dir: Path, out_dir: Path, movement_limit: int) -> dict[str, Any]:
    specs = variant_specs()
    variant_rows: dict[str, list[dict[str, Any]]] = {}
    variant_summaries: dict[str, dict[str, Any]] = {}
    provenance: dict[str, Any] | None = None

    for spec in specs:
        rows, result = run_variant(agentflame_dir, r189_dir, spec)
        variant_rows[spec["variant"]] = rows
        variant_summaries[spec["variant"]] = result["summary"]
        if provenance is None:
            provenance = result["provenance"]

    baseline_rows = variant_rows["baseline"]
    baseline_by_key = rows_by_key(baseline_rows)
    baseline_head_keys = {
        key for key, row in baseline_by_key.items() if str(row["governance_action"]) == "keep_head"
    }

    records = [
        compute_variant_record(
            spec,
            variant_rows[spec["variant"]],
            variant_summaries[spec["variant"]],
            None if spec["variant"] == "baseline" else baseline_by_key,
            baseline_head_keys,
        )
        for spec in specs
    ]
    movements: list[dict[str, Any]] = []
    per_variant_limit = max(1, movement_limit // max(1, len(specs) - 1))
    for spec in specs:
        if spec["variant"] == "baseline":
            continue
        movements.extend(movement_rows(baseline_rows, spec["variant"], variant_rows[spec["variant"]], per_variant_limit))
    movements.sort(key=lambda item: (str(item["variant"]), -int(item["support"]), str(item["dimension"]), str(item["raw_tag"])))

    baseline = next(row for row in records if row["variant"] == "baseline")
    max_review = max(records, key=lambda row: row["review_required_support_pct"])
    min_head = min(records, key=lambda row: row["baseline_head_stability_pct"])
    max_changed = max(records, key=lambda row: row["changed_action_tags_vs_baseline"])

    out_dir.mkdir(parents=True, exist_ok=True)
    variant_csv = out_dir / "long-tail-sensitivity-r201.csv"
    movement_csv = out_dir / "long-tail-sensitivity-movements-r201.csv"
    json_path = out_dir / "long-tail-sensitivity-r201.json"
    md_path = out_dir / "long-tail-sensitivity-r201.md"

    variant_fields = list(records[0].keys())
    movement_fields = list(movements[0].keys()) if movements else [
        "variant",
        "dimension",
        "raw_tag",
        "support",
        "baseline_action",
        "variant_action",
        "baseline_requires_review",
        "variant_requires_review",
        "is_generic_or_noisy",
        "is_multimodal",
        "top_processes",
        "top_context_tags",
    ]
    write_csv(variant_csv, records, variant_fields)
    write_csv(movement_csv, movements, movement_fields)

    payload = {
        "schema_version": 1,
        "run_id": "R201",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "long_tail_sensitivity_complete",
        "input": provenance,
        "method": {
            "baseline": "R196 default policy",
            "variant_count": len(specs),
            "sensitivity_grid_rationale": grid_rationale(),
            "variants": [
                {
                    "variant": spec["variant"],
                    "description": spec["description"],
                    "config": asdict(spec["config"]),
                    "generic_tags_sha256": hashlib.sha256("\n".join(spec["generic_tags"]).encode("utf-8")).hexdigest(),
                    "generic_tag_count": len(spec["generic_tags"]),
                }
                for spec in specs
            ],
            "raw_trace_policy": "read generated AgentFlame/R189 artifacts only; do not mutate raw traces",
            "llm_regeneration": "not run; this is deterministic policy sensitivity",
        },
        "baseline": baseline,
        "variant_records": records,
        "movement_sample_count": len(movements),
        "extremes": {
            "max_review_support_pct": max_review,
            "min_head_stability_pct": min_head,
            "max_changed_action_tags": max_changed,
        },
        "claim_gate": {
            "sensitivity_artifact_supported": True,
            "raw_tags_preserved": True,
            "semantic_adequacy_supported": False,
            "canonicalization_quality_supported": False,
            "developer_utility_supported": False,
            "community_adoption_supported": False,
            "llm_regeneration_run": False,
            "requires_r124_labels_for_adequacy": True,
            "requires_r190_labels_for_merge_quality": True,
        },
        "artifacts": {
            "summary_json": rel(json_path),
            "summary_md": rel(md_path),
            "variant_csv": rel(variant_csv),
            "movement_csv": rel(movement_csv),
        },
        "provenance": {
            "git_head": git(["rev-parse", "HEAD"]),
            "git_status_short": git(["status", "--short"]),
            "script": rel(Path(__file__)),
            "script_sha256": sha256_file(Path(__file__)),
            "r196_script": rel(R196_PATH),
            "r196_script_sha256": sha256_file(R196_PATH),
        },
    }
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agentflame-dir", type=Path, default=DEFAULT_AGENTFLAME_DIR)
    parser.add_argument("--r189-dir", type=Path, default=DEFAULT_R189_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--movement-limit", type=int, default=120)
    args = parser.parse_args()

    payload = run(args.agentflame_dir, args.r189_dir, args.out_dir, args.movement_limit)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "variant_count": payload["method"]["variant_count"],
                "baseline_review_support_pct": payload["baseline"]["review_required_support_pct"],
                "max_review_variant": payload["extremes"]["max_review_support_pct"]["variant"],
                "max_review_support_pct": payload["extremes"]["max_review_support_pct"]["review_required_support_pct"],
                "min_head_stability_variant": payload["extremes"]["min_head_stability_pct"]["variant"],
                "min_head_stability_pct": payload["extremes"]["min_head_stability_pct"]["baseline_head_stability_pct"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
