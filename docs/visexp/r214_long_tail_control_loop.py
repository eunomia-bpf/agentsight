#!/usr/bin/env python3
"""R214: adaptive control loop for long-tail semantic compaction.

This run turns the R196/R201/R205/R209/R213 long-tail artifacts into an
explicit display-control policy. It does not read raw agent traces, call an LLM,
or update the canonical map. The output is a reviewer-facing mechanism artifact:
what may be active by default, what remains pending, what triggers review, and
which threshold changes are unsafe without human labels.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_R196_DIR = SCRIPT_DIR / "out" / "long-tail-governance-r196"
DEFAULT_R201_DIR = SCRIPT_DIR / "out" / "long-tail-sensitivity-r201"
DEFAULT_R202_DIR = SCRIPT_DIR / "out" / "long-tail-regeneration-r202"
DEFAULT_R205_DIR = SCRIPT_DIR / "out" / "long-tail-compaction-r205"
DEFAULT_R209_DIR = SCRIPT_DIR / "out" / "reversible-display-map-r209"
DEFAULT_R213_DIR = SCRIPT_DIR / "out" / "display-mode-drilldown-r213"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "long-tail-control-r214"

DIMENSION_FIELDS = [
    "dimension",
    "raw_unique_tags",
    "canonical_unique_tags",
    "canonical_unique_reduction_pct",
    "long_tail_support_pct",
    "review_required_support_pct",
    "governance_priority",
    "recommended_mode",
    "reason",
]

ACTION_FIELDS = [
    "action",
    "rows",
    "support",
    "support_pct",
    "default_display_effect",
    "promotion_gate",
]

TRIGGER_FIELDS = [
    "trigger",
    "actual",
    "threshold",
    "comparator",
    "passed",
    "response",
]

PRIORITY_FIELDS = [
    "rank",
    "dimension",
    "raw_tag",
    "active_display_tag",
    "support",
    "candidate_display_tag",
    "candidate_source",
    "governance_action",
    "review_reason",
]

ROLLUP_FIELDS = [
    "rollup_bucket",
    "rows",
    "support",
    "support_pct",
    "active_membership_effect",
    "active_display_allowed",
    "required_gate",
    "raw_drilldown_required",
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def as_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(str(value)))


def as_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(str(value))


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def pct(part: int | float, whole: int | float) -> float:
    return round(100.0 * float(part) / float(whole), 3) if whole else 0.0


def dimension_priority(long_tail_pct: float, review_pct: float) -> tuple[str, str, str]:
    if review_pct >= 3.0:
        return (
            "prioritize_review",
            "pending",
            "review-required support is above the per-dimension review budget",
        )
    if long_tail_pct >= 3.0:
        return (
            "tail_fragmentation_watch",
            "display",
            "long-tail support is near or above the fragmentation budget",
        )
    if review_pct >= 1.5:
        return (
            "monitor_pending_load",
            "display+pending",
            "overall map is usable but pending load should remain visible",
        )
    return (
        "stable_default",
        "display",
        "tail and review support are below current budgets",
    )


def trigger_passed(actual: float, threshold: float, comparator: str) -> bool:
    if comparator == "<=":
        return actual <= threshold
    if comparator == ">=":
        return actual >= threshold
    raise ValueError(f"unsupported comparator: {comparator}")


def trigger_row(
    trigger: str,
    actual: float,
    threshold: float,
    comparator: str,
    pass_response: str,
    fail_response: str,
) -> dict[str, Any]:
    passed = trigger_passed(actual, threshold, comparator)
    return {
        "trigger": trigger,
        "actual": round(actual, 3),
        "threshold": round(threshold, 3),
        "comparator": comparator,
        "passed": passed,
        "response": pass_response if passed else fail_response,
    }


def queue_reason(row: dict[str, str]) -> str:
    if row.get("candidate_source") == "r189_profile_guarded_merge_candidate":
        return "review profile merge before display-map promotion"
    if row.get("candidate_source") == "r202_llama_candidate":
        return "review regenerated label before display-map promotion"
    if as_bool(row.get("requires_review")):
        return "review required before display-map promotion"
    return "not queued"


def dimension_rows(r205_dimension_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in r205_dimension_rows:
        dimension = row.get("dimension", "")
        long_tail_pct = as_float(row.get("long_tail_support_pct"))
        review_pct = as_float(row.get("review_required_support_pct"))
        priority, mode, reason = dimension_priority(long_tail_pct, review_pct)
        rows.append(
            {
                "dimension": dimension,
                "raw_unique_tags": as_int(row.get("raw_unique_tags")),
                "canonical_unique_tags": as_int(row.get("canonical_unique_tags")),
                "canonical_unique_reduction_pct": as_float(row.get("canonical_unique_reduction_pct")),
                "long_tail_support_pct": long_tail_pct,
                "review_required_support_pct": review_pct,
                "governance_priority": priority,
                "recommended_mode": mode,
                "reason": reason,
            }
        )
    return rows


def support_summary(rows: list[dict[str, str]], predicate: Any) -> tuple[int, int]:
    selected = [row for row in rows if predicate(row)]
    return len(selected), sum(as_int(row.get("support")) for row in selected)


def action_rows(
    r196_rows: list[dict[str, str]],
    display_rows: list[dict[str, str]],
    r196_summary: dict[str, Any],
    r209_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    total = as_int(r209_summary.get("total_support"))
    counts = r196_summary.get("action_counts") or {}
    alias_rows, alias_support = support_summary(
        display_rows,
        lambda row: row.get("active_source") == "r189_alias_overlay",
    )
    profile_rows, profile_support = support_summary(
        display_rows,
        lambda row: row.get("candidate_source") == "r189_profile_guarded_merge_candidate",
    )
    regenerated_rows, regenerated_support = support_summary(
        display_rows,
        lambda row: row.get("candidate_source") == "r202_llama_candidate",
    )
    rare_rows, rare_support = support_summary(
        r196_rows,
        lambda row: row.get("governance_action") == "keep_rare_distinct",
    )
    head_rows, head_support = support_summary(
        r196_rows,
        lambda row: row.get("governance_action") == "keep_head",
    )
    review_rows, review_support = support_summary(
        display_rows,
        lambda row: as_bool(row.get("requires_review")),
    )
    rows = [
        {
            "action": "active_alias_display",
            "rows": alias_rows,
            "support": alias_support,
            "support_pct": pct(alias_support, total),
            "default_display_effect": "active",
            "promotion_gate": "deterministic alias only; raw drilldown required",
        },
        {
            "action": "pending_profile_merge_candidate",
            "rows": profile_rows,
            "support": profile_support,
            "support_pct": pct(profile_support, total),
            "default_display_effect": "pending",
            "promotion_gate": "requires paired merge-risk review and display-map diff",
        },
        {
            "action": "pending_llm_regenerated_or_split_candidate",
            "rows": regenerated_rows,
            "support": regenerated_support,
            "support_pct": pct(regenerated_support, total),
            "default_display_effect": "candidate_only",
            "promotion_gate": "requires R202 grammar check plus R203 promotion review",
        },
        {
            "action": "review_required_total",
            "rows": review_rows,
            "support": review_support,
            "support_pct": pct(review_support, total),
            "default_display_effect": "candidate_only",
            "promotion_gate": "any reviewed map update must be paired/adjudicated",
        },
        {
            "action": "keep_rare_distinct",
            "rows": rare_rows,
            "support": rare_support,
            "support_pct": pct(rare_support, total),
            "default_display_effect": "raw_preserved",
            "promotion_gate": "none; rare distinct tags are not hidden in other",
        },
        {
            "action": "keep_head",
            "rows": head_rows,
            "support": head_support,
            "support_pct": pct(head_support, total),
            "default_display_effect": "active_raw_or_canonical",
            "promotion_gate": "preserve unless sensitivity or human labels show risk",
        },
    ]
    expected = {
        "pending_profile_merge_candidate": as_int(r209_summary.get("pending_merge_candidate_rows")),
        "pending_llm_regenerated_or_split_candidate": as_int(r209_summary.get("regenerated_candidate_rows")),
        "review_required_total": as_int(r209_summary.get("review_required_rows")),
    }
    actual = {row["action"]: row["rows"] for row in rows}
    for action, value in expected.items():
        if actual.get(action) != value:
            raise AssertionError(f"R214 action count mismatch for {action}: {actual.get(action)} != {value}")
    if counts.get("keep_rare_distinct") != rare_rows or counts.get("keep_head") != head_rows:
        raise AssertionError("R214 R196 keep action counts changed while building action gates")
    return rows


def rollup_preview_rows(display_rows: list[dict[str, str]], total_support: int) -> list[dict[str, Any]]:
    """Partition raw-tag rows into governance-state rollups without changing membership."""
    buckets = [
        (
            "head_preserved",
            lambda row: row.get("governance_action") == "keep_head",
            "active_raw_or_canonical",
            True,
            "none; preserve broad semantic heads unless later evidence shows harm",
        ),
        (
            "rare_distinct_preserved",
            lambda row: row.get("governance_action") == "keep_rare_distinct",
            "active_raw",
            True,
            "none; keep visible rather than hiding under other",
        ),
        (
            "active_alias_overlay",
            lambda row: row.get("active_source") == "r189_alias_overlay",
            "active_alias_merge",
            True,
            "deterministic alias plus raw drilldown",
        ),
        (
            "pending_profile_merge",
            lambda row: row.get("candidate_source") == "r189_profile_guarded_merge_candidate",
            "pending_overlay_only",
            False,
            "paired merge-risk review plus reviewed display-map diff",
        ),
        (
            "pending_review_merge_no_candidate",
            lambda row: row.get("governance_action") == "review_merge",
            "pending_review_queue_only",
            False,
            "paired merge-risk review; no candidate display tag is active",
        ),
        (
            "pending_llm_regeneration",
            lambda row: row.get("governance_action") == "regenerate_candidate",
            "pending_overlay_only",
            False,
            "R202 grammar-valid candidate plus R203 promotion review",
        ),
        (
            "pending_contextual_split",
            lambda row: row.get("governance_action") == "contextual_split_candidate",
            "pending_overlay_only",
            False,
            "split review plus reviewed display-map diff",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for name, predicate, effect, allowed_default, gate in buckets:
        matched = [row for row in display_rows if predicate(row)]
        support = sum(as_int(row.get("support")) for row in matched)
        rows.append(
            {
                "rollup_bucket": name,
                "rows": len(matched),
                "support": support,
                "support_pct": pct(support, total_support),
                "active_membership_effect": effect,
                "active_display_allowed": allowed_default,
                "required_gate": gate,
                "raw_drilldown_required": True,
            }
        )

    row_total = sum(as_int(row["rows"]) for row in rows)
    support_total = sum(as_int(row["support"]) for row in rows)
    if row_total != len(display_rows):
        raise AssertionError(f"R214 rollup rows do not partition display rows: {row_total} != {len(display_rows)}")
    if support_total != total_support:
        raise AssertionError(f"R214 rollup support does not preserve total: {support_total} != {total_support}")
    return rows


def regeneration_version_policy(
    r202_payload: dict[str, Any],
    r209_summary: dict[str, Any],
) -> dict[str, Any]:
    attempts = r202_payload.get("attempt_summary") or {}
    pending_rows = as_int(r209_summary.get("regenerated_candidate_rows"))
    final_labels = as_int(r209_summary.get("r203_final_labels"))
    return {
        "candidate_key": "dimension;raw_tag;profile_hash;generator_version",
        "rerun_behavior": "write a new candidate version; never overwrite raw_tag or accepted map versions",
        "profile_packet_only": True,
        "raw_trace_or_prompt_text_required": False,
        "candidate_only": True,
        "attempted_rows": as_int(attempts.get("attempted_rows")),
        "grammar_valid_rows": as_int(attempts.get("valid_rows")),
        "changed_valid_rows": as_int(attempts.get("changed_valid_rows")),
        "unique_candidate_tags": as_int(attempts.get("unique_valid_regenerated_tags")),
        "pending_regenerated_rows": pending_rows,
        "final_labels_available": final_labels,
        "promotable_rows_now": 0 if final_labels == 0 else final_labels,
        "map_update_allowed": False,
        "promotion_gate": "paired/adjudicated R203 labels plus a reviewed display-map diff",
    }


def review_priority_rows(display_rows: list[dict[str, str]], limit: int = 25) -> list[dict[str, Any]]:
    candidates = [
        row
        for row in display_rows
        if row.get("candidate_display_tag") or as_bool(row.get("requires_review"))
    ]
    candidates.sort(key=lambda row: (-as_int(row.get("support")), row.get("dimension", ""), row.get("raw_tag", "")))
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(candidates[:limit], start=1):
        rows.append(
            {
                "rank": index,
                "dimension": row.get("dimension", ""),
                "raw_tag": row.get("raw_tag", ""),
                "active_display_tag": row.get("active_display_tag", ""),
                "support": as_int(row.get("support")),
                "candidate_display_tag": row.get("candidate_display_tag", ""),
                "candidate_source": row.get("candidate_source", ""),
                "governance_action": row.get("governance_action", ""),
                "review_reason": queue_reason(row),
            }
        )
    return rows


def trigger_rows(
    r201_rows: list[dict[str, str]],
    r205_dimension_rows: list[dict[str, str]],
    r209_summary: dict[str, Any],
    r213_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    by_dimension = {row.get("dimension", ""): row for row in r205_dimension_rows}
    by_variant = {row.get("variant", ""): row for row in r201_rows}
    overall = by_dimension["overall"]
    prompt = by_dimension["prompt"]
    high_tail = by_variant["higher_tail_threshold"]
    return [
        trigger_row(
            "overall_long_tail_budget",
            as_float(overall.get("long_tail_support_pct")),
            3.0,
            "<=",
            "default display can stay alias-only with raw drilldown",
            "open long-tail refinement before using compact view as default",
        ),
        trigger_row(
            "overall_review_budget",
            as_float(overall.get("review_required_support_pct")),
            2.0,
            "<=",
            "pending overlay is acceptable as a default warning surface",
            "force pending mode or review queue before compact display",
        ),
        trigger_row(
            "prompt_review_budget",
            as_float(prompt.get("review_required_support_pct")),
            3.0,
            "<=",
            "prompt tags are within the review budget",
            "prioritize prompt-level review before promoting candidates",
        ),
        trigger_row(
            "head_stability_under_high_tail_threshold",
            as_float(high_tail.get("baseline_head_stability_pct")),
            80.0,
            ">=",
            "tail thresholds can be tuned without destabilizing head labels",
            "do not raise tail thresholds automatically; require review",
        ),
        trigger_row(
            "hidden_other_bucket",
            as_float(r209_summary.get("hidden_other_rows")),
            0.0,
            "<=",
            "no hidden other bucket is present",
            "reject map: raw tags would become unauditable",
        ),
        trigger_row(
            "display_drilldown_membership",
            1.0 if r213_summary.get("drilldown_membership_matches_display_map") else 0.0,
            1.0,
            ">=",
            "display drilldown matches active map membership",
            "reject map: display buckets cannot explain raw membership",
        ),
    ]


def summarize(
    dims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    triggers: list[dict[str, Any]],
    rollups: list[dict[str, Any]],
    priority: list[dict[str, Any]],
    regen_policy: dict[str, Any],
    r196_summary: dict[str, Any],
    r209_summary: dict[str, Any],
    r213_summary: dict[str, Any],
) -> dict[str, Any]:
    by_dimension = {row["dimension"]: row for row in dims}
    failed = [row["trigger"] for row in triggers if not as_bool(row.get("passed"))]
    return {
        "total_support": as_int(r209_summary.get("total_support")),
        "raw_tag_rows": as_int(r209_summary.get("raw_tag_rows")),
        "active_default_merge_rows": as_int(r209_summary.get("alias_active_rows")),
        "active_candidate_merge_rows": 0,
        "pending_candidate_rows": as_int(r209_summary.get("candidate_rows")),
        "pending_merge_candidate_rows": as_int(r209_summary.get("pending_merge_candidate_rows")),
        "regenerated_candidate_rows": as_int(r209_summary.get("regenerated_candidate_rows")),
        "review_required_rows": as_int(r209_summary.get("review_required_rows")),
        "review_required_support": as_int(r209_summary.get("review_required_support")),
        "review_required_support_pct": as_float(r209_summary.get("review_required_support_pct")),
        "long_tail_rows": as_int(r209_summary.get("long_tail_rows")),
        "long_tail_support_pct": as_float(r209_summary.get("long_tail_support_pct")),
        "prompt_review_required_support_pct": by_dimension["prompt"]["review_required_support_pct"],
        "prompt_long_tail_support_pct": by_dimension["prompt"]["long_tail_support_pct"],
        "dimension_rows": len(dims),
        "action_rows": len(actions),
        "trigger_rows": len(triggers),
        "rollup_preview_rows": len(rollups),
        "priority_rows": len(priority),
        "failed_triggers": failed,
        "default_policy": "active_alias_only_with_pending_overlay",
        "rollup_preview_default": False,
        "map_update_allowed": False,
        "raw_tags_preserved": True,
        "no_hidden_other_bucket": as_int(r209_summary.get("hidden_other_rows")) == 0,
        "drilldown_membership_matches_display_map": bool(
            r213_summary.get("drilldown_membership_matches_display_map")
        ),
        "human_review_rows_available": as_int(r196_summary.get("review_required_tags")) == as_int(
            r209_summary.get("review_required_rows")
        ),
        "regeneration_attempted_rows": regen_policy["attempted_rows"],
        "regeneration_valid_rows": regen_policy["grammar_valid_rows"],
        "regeneration_changed_valid_rows": regen_policy["changed_valid_rows"],
        "regeneration_unique_candidate_tags": regen_policy["unique_candidate_tags"],
        "regeneration_promotable_rows_now": regen_policy["promotable_rows_now"],
    }


def write_markdown(
    path: Path,
    payload: dict[str, Any],
    dims: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    triggers: list[dict[str, Any]],
    rollups: list[dict[str, Any]],
    priority: list[dict[str, Any]],
) -> None:
    summary = payload["summary"]
    lines = [
        "# R214 Long-Tail Control Loop",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Boundary",
        "",
        "- Reads generated R196/R201/R205/R209/R213 artifacts only.",
        "- Does not read or mutate raw Codex/Claude traces.",
        "- Does not call an LLM or update the canonical display map.",
        "- Specifies display-control gates only; no semantic adequacy or merge-quality claim.",
        "",
        "## Policy",
        "",
        "The default compact view is active-alias-only with pending overlays. "
        "Profile merges, regenerated tags, and contextual splits may be shown as "
        "candidates, but they cannot change display membership until a reviewed "
        "display-map diff exists.",
        "",
        f"Active default merge rows: `{summary['active_default_merge_rows']}`.",
        f"Pending candidate rows: `{summary['pending_candidate_rows']}`.",
        f"Review-required rows/support: `{summary['review_required_rows']}` / "
        f"`{summary['review_required_support_pct']}`%.",
        f"Regeneration candidates: `{summary['regeneration_attempted_rows']}` attempted, "
        f"`{summary['regeneration_valid_rows']}` grammar-valid, "
        f"`{summary['regeneration_promotable_rows_now']}` promotable without human labels.",
        f"Rollup preview rows: `{summary['rollup_preview_rows']}`; active by default: "
        f"`{summary['rollup_preview_default']}`.",
        f"Failed control triggers: `{', '.join(summary['failed_triggers']) or 'none'}`.",
        "",
        "## Dimension Priorities",
        "",
        "| dimension | raw tags | canonical tags | long-tail support % | review support % | priority | mode |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for row in dims:
        lines.append(
            f"| {row['dimension']} | {row['raw_unique_tags']} | {row['canonical_unique_tags']} | "
            f"{row['long_tail_support_pct']} | {row['review_required_support_pct']} | "
            f"{row['governance_priority']} | {row['recommended_mode']} |"
        )
    lines.extend(
        [
            "",
            "## Action Gates",
            "",
            "| action | rows | default effect | gate |",
            "|---|---:|---|---|",
        ]
    )
    for row in actions:
        lines.append(
            f"| {row['action']} | {row['rows']} | {row['default_display_effect']} | {row['promotion_gate']} |"
        )
    lines.extend(
        [
            "",
            "## Trigger Gates",
            "",
            "| trigger | actual | threshold | pass | response |",
            "|---|---:|---:|---|---|",
        ]
    )
    for row in triggers:
        lines.append(
            f"| {row['trigger']} | {row['actual']} | {row['comparator']} {row['threshold']} | "
            f"{row['passed']} | {row['response']} |"
        )
    lines.extend(
        [
            "",
            "## Rollup Preview",
            "",
            "The rollup preview groups raw-tag rows by governance state so users can "
            "inspect long-tail burden. It is not the default flamegraph membership.",
            "",
            "| bucket | rows | support | active display | gate |",
            "|---|---:|---:|---|---|",
        ]
    )
    for row in rollups:
        lines.append(
            f"| {row['rollup_bucket']} | {row['rows']} | {row['support']} | "
            f"{row['active_display_allowed']} | {row['required_gate']} |"
        )
    lines.extend(
        [
            "",
            "## Review Priority Sample",
            "",
            "| rank | dimension | raw tag | active display | candidate | support | reason |",
            "|---:|---|---|---|---|---:|---|",
        ]
    )
    for row in priority[:12]:
        lines.append(
            f"| {row['rank']} | {row['dimension']} | `{row['raw_tag']}` | "
            f"`{row['active_display_tag']}` | `{row['candidate_display_tag']}` | "
            f"{row['support']} | {row['review_reason']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "R214 supports the existence of an auditable long-tail control loop: raw "
            "tags remain immutable, deterministic aliases may be active, and all "
            "LLM-regenerated/profile/split candidates stay pending until review. "
            "It does not prove that any candidate merge or regenerated label is correct.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_payload(args: argparse.Namespace) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    inputs = {
        "r196_json": args.r196_dir / "long-tail-governance-r196.json",
        "r196_csv": args.r196_dir / "long-tail-governance-r196.csv",
        "r201_csv": args.r201_dir / "long-tail-sensitivity-r201.csv",
        "r202_json": args.r202_dir / "long-tail-regeneration-r202.json",
        "r205_dimensions_csv": args.r205_dir / "long-tail-compaction-dimensions-r205.csv",
        "r209_json": args.r209_dir / "reversible-display-map-r209.json",
        "r209_display_csv": args.r209_dir / "active-display-map-r209.csv",
        "r213_json": args.r213_dir / "display-mode-drilldown-r213.json",
    }
    for path in inputs.values():
        if not path.exists():
            raise FileNotFoundError(f"missing R214 input artifact: {rel(path)}")

    r196 = read_json(inputs["r196_json"])
    r196_rows = read_csv(inputs["r196_csv"])
    r201_rows = read_csv(inputs["r201_csv"])
    r202 = read_json(inputs["r202_json"])
    r205_dimension_rows = read_csv(inputs["r205_dimensions_csv"])
    r209 = read_json(inputs["r209_json"])
    display_rows = read_csv(inputs["r209_display_csv"])
    r213 = read_json(inputs["r213_json"])

    dims = dimension_rows(r205_dimension_rows)
    actions = action_rows(r196_rows, display_rows, r196.get("summary") or {}, r209.get("summary") or {})
    triggers = trigger_rows(r201_rows, r205_dimension_rows, r209.get("summary") or {}, r213.get("summary") or {})
    rollups = rollup_preview_rows(display_rows, as_int(r209.get("summary", {}).get("total_support")))
    priority = review_priority_rows(display_rows)
    regen_policy = regeneration_version_policy(r202, r209.get("summary") or {})
    summary = summarize(
        dims,
        actions,
        triggers,
        rollups,
        priority,
        regen_policy,
        r196.get("summary") or {},
        r209.get("summary") or {},
        r213.get("summary") or {},
    )

    payload = {
        "run_id": "R214",
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": "long_tail_control_loop_ready_no_quality_claims",
        "claim": "C3 display compaction governance; C6 protocol/gate only",
        "claim_boundary": (
            "R214 specifies an auditable control loop for long-tail display compaction. "
            "It supports active deterministic aliases plus pending merge/regeneration/split "
            "queues, but it does not support semantic adequacy, merge quality, developer "
            "utility, or canonical-map updates."
        ),
        "input": {
            key: rel(path) for key, path in inputs.items()
        }
        | {
            f"{key}_sha256": sha256_file(path)
            for key, path in inputs.items()
        },
        "method": {
            "raw_tag_policy": "raw tags are immutable and always drilldown-visible",
            "active_policy": "only deterministic aliases and reviewed diffs may change default display membership",
            "candidate_policy": "profile merges, regenerated labels, and split labels stay pending",
            "regeneration_version_policy": regen_policy,
            "rollup_policy": (
                "rollup preview partitions the long-tail burden by governance state; "
                "it is inspectable but not active default membership"
            ),
            "trigger_policy": "tail/review/head-stability/drilldown gates decide when review is required",
            "review_policy": "paired/adjudicated human labels are required before map update",
        },
        "summary": summary,
        "claim_gate": {
            "long_tail_control_loop_supported": bool(
                summary["raw_tags_preserved"]
                and summary["no_hidden_other_bucket"]
                and summary["drilldown_membership_matches_display_map"]
                and not summary["map_update_allowed"]
            ),
            "active_alias_only_default": summary["active_candidate_merge_rows"] == 0,
            "pending_candidates_visible": summary["pending_candidate_rows"] > 0,
            "rollup_preview_supported": summary["rollup_preview_rows"] > 0,
            "rollup_changes_default_membership": False,
            "regeneration_versioned_candidate_only": bool(regen_policy["candidate_only"]),
            "regeneration_candidates_promoted": False,
            "review_queue_prioritized": len(priority) > 0,
            "raw_tags_preserved": bool(summary["raw_tags_preserved"]),
            "reads_generated_artifacts_only": True,
            "raw_trace_read": False,
            "llm_called": False,
            "canonical_map_updated": False,
            "semantic_adequacy_supported": False,
            "canonicalization_quality_supported": False,
            "developer_utility_supported": False,
            "frontend_renderer_supported": False,
        },
        "outputs": {
            "summary_json": rel(args.out_dir / "long-tail-control-r214.json"),
            "summary_md": rel(args.out_dir / "long-tail-control-r214.md"),
            "dimension_control_csv": rel(args.out_dir / "dimension-control-r214.csv"),
            "action_gates_csv": rel(args.out_dir / "action-gates-r214.csv"),
            "trigger_gates_csv": rel(args.out_dir / "trigger-gates-r214.csv"),
            "rollup_preview_csv": rel(args.out_dir / "rollup-preview-r214.csv"),
            "review_priority_csv": rel(args.out_dir / "review-priority-r214.csv"),
        },
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }
    return payload, dims, actions, triggers, rollups, priority


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r196-dir", type=Path, default=DEFAULT_R196_DIR)
    parser.add_argument("--r201-dir", type=Path, default=DEFAULT_R201_DIR)
    parser.add_argument("--r202-dir", type=Path, default=DEFAULT_R202_DIR)
    parser.add_argument("--r205-dir", type=Path, default=DEFAULT_R205_DIR)
    parser.add_argument("--r209-dir", type=Path, default=DEFAULT_R209_DIR)
    parser.add_argument("--r213-dir", type=Path, default=DEFAULT_R213_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload, dims, actions, triggers, rollups, priority = build_payload(args)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "long-tail-control-r214.json", payload)
    write_markdown(args.out_dir / "long-tail-control-r214.md", payload, dims, actions, triggers, rollups, priority)
    write_csv(args.out_dir / "dimension-control-r214.csv", dims, DIMENSION_FIELDS)
    write_csv(args.out_dir / "action-gates-r214.csv", actions, ACTION_FIELDS)
    write_csv(args.out_dir / "trigger-gates-r214.csv", triggers, TRIGGER_FIELDS)
    write_csv(args.out_dir / "rollup-preview-r214.csv", rollups, ROLLUP_FIELDS)
    write_csv(args.out_dir / "review-priority-r214.csv", priority, PRIORITY_FIELDS)
    print(json.dumps({"status": payload["status"], "summary_json": payload["outputs"]["summary_json"]}))


if __name__ == "__main__":
    main()
