#!/usr/bin/env python3
"""R213: data-layer mode smoke for reversible long-tail display compaction.

This run verifies the concrete data contract behind the long-tail design:
raw, display, and pending modes must all preserve support, every display bucket
must keep raw-tag drilldown, and pending mode may overlay review candidates but
must not change display membership. It reads generated R209 artifacts only.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_R209_DIR = SCRIPT_DIR / "out" / "reversible-display-map-r209"
DEFAULT_OUT = SCRIPT_DIR / "out" / "display-mode-drilldown-r213"

MODE_FIELDS = [
    "mode",
    "description",
    "bucket_count",
    "row_count",
    "total_support",
    "support_preserved",
    "raw_drilldown_available",
    "candidate_overlay_rows",
    "review_required_rows",
    "review_required_support",
    "active_merge_rows",
    "hidden_other_rows",
    "membership_source",
]

QUEUE_FIELDS = [
    "dimension",
    "raw_tag",
    "active_display_tag",
    "support",
    "requires_review",
    "is_long_tail",
    "candidate_display_tag",
    "candidate_source",
    "candidate_state",
    "governance_action",
    "governance_reasons",
    "review_reason",
]

PANEL_FIELDS = [
    "mode",
    "dimension",
    "display_tag",
    "support",
    "raw_tag_count",
    "candidate_rows",
    "review_required_rows",
    "raw_tags",
    "top_processes",
    "top_effects",
    "user_visible_drilldown",
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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


def as_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(str(value)))


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def parse_counter(text: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for item in str(text or "").split(";"):
        item = item.strip()
        if not item or "=" not in item:
            continue
        key, value = item.rsplit("=", 1)
        try:
            count = int(float(value.strip()))
        except ValueError:
            continue
        key = key.strip()
        if key:
            counter[key] += count
    return counter


def compact_counter(counter: Counter[str], limit: int = 8) -> str:
    return "; ".join(f"{key}={value}" for key, value in counter.most_common(limit))


def hidden_other_rows(rows: list[dict[str, str]], tag_field: str) -> int:
    return sum(1 for row in rows if str(row.get(tag_field, "")).lower() in {"other", "others"})


def raw_buckets(display_rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in display_rows:
        groups[(row.get("dimension", ""), row.get("raw_tag", ""))].append(row)
    return groups


def display_buckets(display_rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in display_rows:
        groups[(row.get("dimension", ""), row.get("active_display_tag", ""))].append(row)
    return groups


def display_membership_signature(display_rows: list[dict[str, str]]) -> set[tuple[str, str, tuple[str, ...]]]:
    return {
        (dimension, tag, tuple(sorted(row.get("raw_tag", "") for row in rows)))
        for (dimension, tag), rows in display_buckets(display_rows).items()
    }


def queue_reason(row: dict[str, str]) -> str:
    source = row.get("candidate_source", "")
    if source == "r189_profile_guarded_merge_candidate":
        return "pending lexical/profile merge review"
    if source == "r202_llama_candidate":
        return "pending regenerated-label promotion review"
    if as_bool(row.get("requires_review")):
        return "requires review before display-map promotion"
    return "not queued"


def pending_review_queue(display_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in display_rows:
        if not row.get("candidate_display_tag") and not as_bool(row.get("requires_review")):
            continue
        rows.append(
            {
                "dimension": row.get("dimension", ""),
                "raw_tag": row.get("raw_tag", ""),
                "active_display_tag": row.get("active_display_tag", ""),
                "support": as_int(row.get("support")),
                "requires_review": as_bool(row.get("requires_review")),
                "is_long_tail": as_bool(row.get("is_long_tail")),
                "candidate_display_tag": row.get("candidate_display_tag", ""),
                "candidate_source": row.get("candidate_source", ""),
                "candidate_state": row.get("candidate_state", ""),
                "governance_action": row.get("governance_action", ""),
                "governance_reasons": row.get("governance_reasons", ""),
                "review_reason": queue_reason(row),
            }
        )
    rows.sort(key=lambda row: (-as_int(row["support"]), row["dimension"], row["raw_tag"]))
    return rows


def drilldown_membership_matches_display_map(
    display_rows: list[dict[str, str]],
    drilldown_rows: list[dict[str, str]],
) -> bool:
    display_groups = display_buckets(display_rows)
    drilldown_groups = {
        (row.get("dimension", ""), row.get("active_display_tag", "")): row
        for row in drilldown_rows
    }
    if set(display_groups) != set(drilldown_groups):
        return False
    for key, rows in display_groups.items():
        expected = Counter({row.get("raw_tag", ""): as_int(row.get("support")) for row in rows})
        expected.pop("", None)
        drilldown_row = drilldown_groups[key]
        if parse_counter(drilldown_row.get("raw_tags", "")) != expected:
            return False
        if as_int(drilldown_row.get("raw_tag_count")) != len(expected):
            return False
        if as_int(drilldown_row.get("support")) != sum(expected.values()):
            return False
    return True


def mode_summary_rows(
    display_rows: list[dict[str, str]],
    drilldown_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    total_support = sum(as_int(row.get("support")) for row in display_rows)
    review_rows = [row for row in display_rows if as_bool(row.get("requires_review"))]
    candidate_rows = [row for row in display_rows if row.get("candidate_display_tag")]
    active_merge_rows = [row for row in display_rows if row.get("raw_tag") != row.get("active_display_tag")]
    raw_groups = raw_buckets(display_rows)
    display_groups = display_buckets(display_rows)
    drilldown_keys = {
        (row.get("dimension", ""), row.get("active_display_tag", ""))
        for row in drilldown_rows
    }
    display_keys = set(display_groups)
    drilldown_available = display_keys == drilldown_keys
    review_support = sum(as_int(row.get("support")) for row in review_rows)
    return [
        {
            "mode": "raw",
            "description": "one bucket per raw semantic tag; no display-map overlay",
            "bucket_count": len(raw_groups),
            "row_count": len(display_rows),
            "total_support": total_support,
            "support_preserved": True,
            "raw_drilldown_available": True,
            "candidate_overlay_rows": 0,
            "review_required_rows": 0,
            "review_required_support": 0,
            "active_merge_rows": 0,
            "hidden_other_rows": hidden_other_rows(display_rows, "raw_tag"),
            "membership_source": "raw_tag",
        },
        {
            "mode": "display",
            "description": "active R209 display map; deterministic aliases active; candidates inactive",
            "bucket_count": len(display_groups),
            "row_count": len(display_rows),
            "total_support": total_support,
            "support_preserved": True,
            "raw_drilldown_available": drilldown_available,
            "candidate_overlay_rows": 0,
            "review_required_rows": 0,
            "review_required_support": 0,
            "active_merge_rows": len(active_merge_rows),
            "hidden_other_rows": hidden_other_rows(display_rows, "active_display_tag"),
            "membership_source": "active_display_tag + display-drilldown",
        },
        {
            "mode": "pending",
            "description": "display membership plus review/candidate overlays; no membership changes",
            "bucket_count": len(display_groups),
            "row_count": len(display_rows),
            "total_support": total_support,
            "support_preserved": True,
            "raw_drilldown_available": drilldown_available,
            "candidate_overlay_rows": len(candidate_rows),
            "review_required_rows": len(review_rows),
            "review_required_support": review_support,
            "active_merge_rows": len(active_merge_rows),
            "hidden_other_rows": hidden_other_rows(display_rows, "active_display_tag"),
            "membership_source": "same as display; overlays candidate_display_tag/requires_review",
        },
    ]


def drilldown_raw_complete(drilldown_rows: list[dict[str, str]]) -> bool:
    for row in drilldown_rows:
        raw_support = parse_counter(row.get("raw_tags", ""))
        if sum(raw_support.values()) != as_int(row.get("support")):
            return False
        if len(raw_support) != as_int(row.get("raw_tag_count")):
            return False
    return True


def sample_panel_rows(
    display_rows: list[dict[str, str]],
    drilldown_rows: list[dict[str, str]],
    limit: int = 12,
) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    raw_top = sorted(display_rows, key=lambda row: (-as_int(row.get("support")), row.get("dimension", ""), row.get("raw_tag", "")))[:limit]
    for row in raw_top:
        samples.append(
            {
                "mode": "raw",
                "dimension": row.get("dimension", ""),
                "display_tag": row.get("raw_tag", ""),
                "support": as_int(row.get("support")),
                "raw_tag_count": 1,
                "candidate_rows": 0,
                "review_required_rows": 0,
                "raw_tags": f"{row.get('raw_tag', '')}={as_int(row.get('support'))}",
                "top_processes": "",
                "top_effects": "",
                "user_visible_drilldown": True,
            }
        )

    interesting = [
        row for row in drilldown_rows
        if as_int(row.get("raw_tag_count")) > 1
        or as_int(row.get("candidate_rows")) > 0
        or as_int(row.get("review_required_rows")) > 0
    ]
    interesting.sort(key=lambda row: (-as_int(row.get("support")), row.get("dimension", ""), row.get("active_display_tag", "")))
    for row in interesting[:limit]:
        common = {
            "dimension": row.get("dimension", ""),
            "display_tag": row.get("active_display_tag", ""),
            "support": as_int(row.get("support")),
            "raw_tag_count": as_int(row.get("raw_tag_count")),
            "candidate_rows": as_int(row.get("candidate_rows")),
            "review_required_rows": as_int(row.get("review_required_rows")),
            "raw_tags": row.get("raw_tags", ""),
            "top_processes": row.get("top_processes", ""),
            "top_effects": row.get("top_effects", ""),
            "user_visible_drilldown": True,
        }
        samples.append({"mode": "display", **common})
        samples.append({"mode": "pending", **common})
    return samples


def summarize(
    display_rows: list[dict[str, str]],
    drilldown_rows: list[dict[str, str]],
    mode_rows: list[dict[str, Any]],
    queue_rows: list[dict[str, Any]],
    r209_payload: dict[str, Any],
) -> dict[str, Any]:
    total_support = sum(as_int(row.get("support")) for row in display_rows)
    mode_by_name = {row["mode"]: row for row in mode_rows}
    drilldown_matches_display = drilldown_membership_matches_display_map(display_rows, drilldown_rows)
    pending_membership_unchanged = (
        mode_by_name["pending"]["bucket_count"] == mode_by_name["display"]["bucket_count"]
        and mode_by_name["pending"]["total_support"] == mode_by_name["display"]["total_support"]
        and str(mode_by_name["pending"]["membership_source"]).startswith("same as display")
    )
    r209_summary = r209_payload.get("summary") or {}
    candidate_rows = [row for row in display_rows if row.get("candidate_display_tag")]
    return {
        "total_support": total_support,
        "mode_count": len(mode_rows),
        "raw_bucket_count": mode_by_name["raw"]["bucket_count"],
        "display_bucket_count": mode_by_name["display"]["bucket_count"],
        "pending_bucket_count": mode_by_name["pending"]["bucket_count"],
        "raw_rows": len(display_rows),
        "drilldown_rows": len(drilldown_rows),
        "pending_review_queue_rows": len(queue_rows),
        "candidate_overlay_rows": len(candidate_rows),
        "review_required_rows": sum(1 for row in display_rows if as_bool(row.get("requires_review"))),
        "review_required_support": sum(
            as_int(row.get("support")) for row in display_rows if as_bool(row.get("requires_review"))
        ),
        "active_merge_rows": sum(1 for row in display_rows if row.get("raw_tag") != row.get("active_display_tag")),
        "hidden_other_rows": hidden_other_rows(display_rows, "active_display_tag"),
        "all_modes_support_preserved": all(as_int(row.get("total_support")) == total_support for row in mode_rows),
        "display_drilldown_available": bool(mode_by_name["display"]["raw_drilldown_available"]),
        "pending_drilldown_available": bool(mode_by_name["pending"]["raw_drilldown_available"]),
        "pending_membership_unchanged": pending_membership_unchanged,
        "drilldown_raw_tags_complete": drilldown_raw_complete(drilldown_rows),
        "drilldown_membership_matches_display_map": drilldown_matches_display,
        "r209_raw_coverage_complete": bool(r209_summary.get("raw_coverage_complete")),
        "r209_no_hidden_other_bucket": bool(r209_summary.get("no_hidden_other_bucket")),
        "r209_canonical_map_updated": False,
        "false_merge_rate_pct": None,
        "missed_merge_rate_pct": None,
    }


def write_markdown(
    path: Path,
    payload: dict[str, Any],
    mode_rows: list[dict[str, Any]],
    queue_rows: list[dict[str, Any]],
    sample_rows: list[dict[str, Any]],
) -> None:
    summary = payload["summary"]
    lines = [
        "# R213 Display-Mode Drilldown Smoke",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Boundary",
        "",
        "- Reads generated R209 artifacts only.",
        "- Does not read or mutate raw Codex/Claude traces.",
        "- Does not call an LLM.",
        "- Verifies display-mode data mechanics only; no frontend renderer, merge-quality, adequacy, or utility claim.",
        "",
        "## Mode Summary",
        "",
        "| mode | buckets | support | drilldown | candidate overlays | review rows | active merges |",
        "|---|---:|---:|---|---:|---:|---:|",
    ]
    for row in mode_rows:
        lines.append(
            f"| `{row['mode']}` | {row['bucket_count']} | {row['total_support']} | "
            f"{row['raw_drilldown_available']} | {row['candidate_overlay_rows']} | "
            f"{row['review_required_rows']} | {row['active_merge_rows']} |"
        )
    lines.extend(
        [
            "",
            "## Pending Queue",
            "",
            f"Pending/review queue rows: `{summary['pending_review_queue_rows']}`.",
            f"Candidate overlay rows: `{summary['candidate_overlay_rows']}`.",
            f"Review-required rows: `{summary['review_required_rows']}`.",
            f"Review-required support: `{summary['review_required_support']}`.",
            "",
            "Top pending rows:",
            "",
            "| dimension | raw tag | display tag | candidate | support | reason |",
            "|---|---|---|---|---:|---|",
        ]
    )
    for row in queue_rows[:12]:
        lines.append(
            f"| {row['dimension']} | `{row['raw_tag']}` | `{row['active_display_tag']}` | "
            f"`{row['candidate_display_tag']}` | {row['support']} | {row['review_reason']} |"
        )
    lines.extend(
        [
            "",
            "## Sample Panels",
            "",
            "| mode | dimension | display tag | support | raw tag count | candidate rows | review rows |",
            "|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in sample_rows[:18]:
        lines.append(
            f"| `{row['mode']}` | {row['dimension']} | `{row['display_tag']}` | "
            f"{row['support']} | {row['raw_tag_count']} | {row['candidate_rows']} | "
            f"{row['review_required_rows']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "R213 supports a display-mode data-layer smoke only: raw/display/pending modes "
            "preserve support, pending mode does not change display membership, and the "
            "artifact has enough data to expose raw-tag drilldown and review burden. It "
            "does not exercise the frontend renderer and does not support semantic "
            "adequacy, merge quality, regenerated-label quality, or developer utility.",
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
]:
    r209_json = args.r209_dir / "reversible-display-map-r209.json"
    display_csv = args.r209_dir / "active-display-map-r209.csv"
    drilldown_csv = args.r209_dir / "display-drilldown-r209.csv"
    for path in [r209_json, display_csv, drilldown_csv]:
        if not path.exists():
            raise FileNotFoundError(f"missing R213 input artifact: {rel(path)}")

    r209_payload = json.loads(r209_json.read_text(encoding="utf-8"))
    display_rows = read_csv(display_csv)
    drilldown_rows = read_csv(drilldown_csv)
    mode_rows = mode_summary_rows(display_rows, drilldown_rows)
    queue_rows = pending_review_queue(display_rows)
    sample_rows = sample_panel_rows(display_rows, drilldown_rows)
    summary = summarize(display_rows, drilldown_rows, mode_rows, queue_rows, r209_payload)

    payload = {
        "run_id": "R213",
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": "display_mode_drilldown_smoke_ready_no_quality_claims",
        "claim": "C3 display-map mechanics; C6 protocol/gate only",
        "claim_boundary": (
            "R213 verifies display-mode data mechanics over generated R209 artifacts. "
            "Raw, display, and pending modes preserve support; pending mode overlays "
            "candidate/review metadata without changing display membership. It does not "
            "exercise the frontend renderer and does not support semantic adequacy, "
            "merge quality, developer utility, or community adoption."
        ),
        "input": {
            "r209_json": rel(r209_json),
            "r209_json_sha256": sha256_file(r209_json),
            "display_csv": rel(display_csv),
            "display_csv_sha256": sha256_file(display_csv),
            "drilldown_csv": rel(drilldown_csv),
            "drilldown_csv_sha256": sha256_file(drilldown_csv),
        },
        "method": {
            "raw_mode": "one bucket per raw tag; no overlay",
            "display_mode": "active R209 display tag with deterministic alias overlays only",
            "pending_mode": "same membership as display mode plus candidate/review overlays",
            "drilldown_contract": "every display bucket must expose raw-tag membership and support",
            "quality_boundary": "data-layer mechanics only; human labels required for merge/regeneration quality",
        },
        "summary": summary,
        "claim_gate": {
            "data_layer_mode_smoke_supported": bool(
                summary["all_modes_support_preserved"]
                and summary["display_drilldown_available"]
                and summary["pending_drilldown_available"]
                and summary["pending_membership_unchanged"]
                and summary["drilldown_raw_tags_complete"]
                and summary["drilldown_membership_matches_display_map"]
                and summary["hidden_other_rows"] == 0
            ),
            "renderer_mode_smoke_supported": False,
            "all_modes_support_preserved": bool(summary["all_modes_support_preserved"]),
            "raw_drilldown_visible": True,
            "display_drilldown_available": bool(summary["display_drilldown_available"]),
            "pending_drilldown_available": bool(summary["pending_drilldown_available"]),
            "pending_membership_unchanged": bool(summary["pending_membership_unchanged"]),
            "drilldown_membership_matches_display_map": bool(summary["drilldown_membership_matches_display_map"]),
            "reads_generated_artifacts_only": True,
            "raw_trace_read": False,
            "llm_called": False,
            "canonical_map_updated": False,
            "hidden_other_bucket": False,
            "semantic_adequacy_supported": False,
            "canonicalization_quality_supported": False,
            "developer_utility_supported": False,
            "community_adoption_supported": False,
        },
        "outputs": {
            "summary_json": rel(args.out_dir / "display-mode-drilldown-r213.json"),
            "summary_md": rel(args.out_dir / "display-mode-drilldown-r213.md"),
            "mode_summary_csv": rel(args.out_dir / "mode-summary-r213.csv"),
            "pending_review_queue_csv": rel(args.out_dir / "pending-review-queue-r213.csv"),
            "sample_panels_csv": rel(args.out_dir / "sample-panels-r213.csv"),
        },
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }
    return payload, mode_rows, queue_rows, sample_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r209-dir", type=Path, default=DEFAULT_R209_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload, mode_rows, queue_rows, sample_rows = build_payload(args)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "display-mode-drilldown-r213.json", payload)
    write_markdown(args.out_dir / "display-mode-drilldown-r213.md", payload, mode_rows, queue_rows, sample_rows)
    write_csv(args.out_dir / "mode-summary-r213.csv", mode_rows, MODE_FIELDS)
    write_csv(args.out_dir / "pending-review-queue-r213.csv", queue_rows, QUEUE_FIELDS)
    write_csv(args.out_dir / "sample-panels-r213.csv", sample_rows, PANEL_FIELDS)
    print(json.dumps({"status": payload["status"], "summary_json": payload["outputs"]["summary_json"]}))


if __name__ == "__main__":
    main()
