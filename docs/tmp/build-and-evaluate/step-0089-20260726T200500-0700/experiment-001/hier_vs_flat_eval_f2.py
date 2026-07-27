#!/usr/bin/env python3
"""Corrected flat control arm F2 (step 0089 amendment; binding).

The original arm F grouped operations by the LAST path component, which is the
outcome status frame (5 tags: blocked/failure/progress/success/unclear) — an
orchestrator spec error. This arm F2 is the corrected flat control.

Arm F2: identical protocol to arms H/F, but the flat grouping key is the DEEPEST
SEMANTIC frame — the path component immediately BEFORE the fixed three-frame
source-kind/call-tool/outcome suffix (documented in step 0081's provenance).
For a frozen ``source_preserving_agent`` path ``[task_family, ...semantic...,
source_kind, call_tool, outcome]`` that component is ``path[-4]``.

Arm H is NOT rerun. F2 is paired against the stored arm-H per-query results
(same reader family, flags, jail recipe). Seeds are documented below.

This harness imports the original ``hier_vs_flat_eval`` module and reuses its
loaders, reader invocation (``call_opencode`` / ``run_stage``), parsers,
fallbacks, packet builders, AP/MAP, and paired bootstrap — so the reader recipe
and protocol are byte-identical to arms H/F. The ONLY change is the F2 grouping
key, injected via a monkeypatch on ``base.arm_path`` (and an added
``ARM_TAG`` entry) so that ``base.process_one_query`` / ``base.run_arm_phase``
emit F2 packets into ``packets-F2-stage{1,2}/`` and cache reader responses into
``raw-responses-F2/``.

Modes:
  pilot    — 40 queries, operational gate (parse-failure < 10%); not a paper result
  full     — 220 queries with resume, then score H (stored) vs F2
  score-only — re-score H vs F2 from cached responses (no reader calls)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

HERE = Path(__file__).resolve().parent
BASE_HARNESS = HERE / "hier_vs_flat_eval.py"
DEFAULT_OUT = HERE

# Load the original harness module (byte-identical reader recipe / protocol).
_spec = importlib.util.spec_from_file_location("hier_vs_flat_eval_base", BASE_HARNESS)
base = importlib.util.module_from_spec(_spec)
assert _spec is not None and _spec.loader is not None
_spec.loader.exec_module(base)

# ---------------------------------------------------------------------------
# F2 arm identity — the corrected flat control
# ---------------------------------------------------------------------------

ARM_H = base.ARM_H
ARM_F = base.ARM_F          # superseded F(status) arm — kept for reference numbers
ARM_F2 = "flat2"
ARM_TAG_F2 = "F2"

# The corrected grouping key = the deepest semantic frame, i.e. the path
# component immediately BEFORE the fixed three-frame source-kind/call-tool/
# outcome suffix. For the frozen source_preserving_agent path that is path[-4].
F2_INDEX_FROM_END = 4

# Documented seeds for the F2 paired bootstrap (distinct from the H-vs-F seeds).
H_VS_F2_SEED = 20261089
CONTENT_DELTA_F2_SEED = 20261090
BOOTSTRAP_REPS = base.BOOTSTRAP_REPS

# Stored reference MAPs (invariants, mirror base harness).
STORED_DIRECT_ONLY_MAP = base.STORED_DIRECT_ONLY_MAP
STORED_DIRECT_AGENTPROF_MAP = base.STORED_DIRECT_AGENTPROF_MAP
STORED_DIRECT_READER_MAP = base.STORED_DIRECT_READER_MAP

DIRECT_ONLY = base.DIRECT_ONLY
DIRECT_AGENTPROF = base.DIRECT_AGENTPROF
DIRECT_READER = base.DIRECT_READER


# ---------------------------------------------------------------------------
# Patch base module so base.process_one_query / base.run_arm_phase drive the F2
# grouping and write into F2 directories. This reuses the EXACT reader recipe.
# ---------------------------------------------------------------------------

_orig_arm_path = base.arm_path


def arm_path_with_f2(full_path: Sequence[str], arm: str) -> list[str]:
    if arm == ARM_F2:
        base.require(
            len(full_path) >= F2_INDEX_FROM_END,
            f"F2 needs >= {F2_INDEX_FROM_END} path components, got {len(full_path)}",
        )
        return [str(full_path[-F2_INDEX_FROM_END])]
    return _orig_arm_path(full_path, arm)


base.arm_path = arm_path_with_f2
base.ARM_TAG[ARM_F2] = ARM_TAG_F2


# ---------------------------------------------------------------------------
# F2 vocabulary reporting (task spec: report tag-vocabulary size + group counts)
# ---------------------------------------------------------------------------


def f2_vocabulary(op_paths: Mapping[str, Sequence[str]]) -> dict[str, Any]:
    """Population-wide F2 tag vocabulary and group-count projection."""
    tags: dict[str, int] = {}
    per_seq_groups: dict[str, set[str]] = {}
    for operation_id, path in op_paths.items():
        base.require(
            len(path) >= F2_INDEX_FROM_END,
            f"F2 grouping needs >= {F2_INDEX_FROM_END} components: {operation_id}",
        )
        tag = str(path[-F2_INDEX_FROM_END])
        tags[tag] = tags.get(tag, 0) + 1
        sequence = operation_id.rsplit("#step-", 1)[0]
        per_seq_groups.setdefault(sequence, set()).add(tag)
    group_counts = sorted(len(s) for s in per_seq_groups.values())
    return {
        "index": F2_INDEX_FROM_END,
        "description": (
            "path component immediately before the fixed three-frame "
            "source-kind/call-tool/outcome suffix (deepest semantic frame)"
        ),
        "unique_tags": len(tags),
        "tag_vocabulary_sorted": [
            tag for tag, _ in sorted(tags.items(), key=lambda kv: (-kv[1], kv[0]))
        ],
        "tag_counts": dict(
            sorted(tags.items(), key=lambda kv: (-kv[1], kv[0]))
        ),
        "mean_groups_per_sequence": statistics.fmean(group_counts),
        "median_groups_per_sequence": statistics.median(group_counts),
        "min_groups_per_sequence": min(group_counts),
        "max_groups_per_sequence": max(group_counts),
    }


# ---------------------------------------------------------------------------
# Scoring: H (stored/cache re-derived) vs F2 (F2 run), with reference arms
# ---------------------------------------------------------------------------


def load_stored_h_per_query(path: Path) -> dict[str, dict[str, Any]]:
    """Load the stored arm-H per-query metrics (the authoritative H run)."""
    payload = base.read_json(path)
    out: dict[str, dict[str, Any]] = {}
    for row in payload["per_query"]:
        qid = str(row["query_id"])
        out[qid] = row["h"]
    base.require(len(out) == 220, f"expected 220 stored H rows, got {len(out)}")
    return out


def score_h_f2(
    rows_h: Mapping[str, Mapping[str, Any]],
    rows_f2: Mapping[str, Mapping[str, Any]],
    rows_f_status: Mapping[str, Mapping[str, Any]],
    query_ids: Sequence[str],
    baselines: Mapping[str, Mapping[str, Any]],
    direct_reader: Mapping[str, Mapping[str, Any]],
    projections: Mapping[str, Sequence[Mapping[str, Any]]],
    op_paths: Mapping[str, Sequence[str]],
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
                    ARM_H: float(rows_h[query_id]["ap_arm"]),
                    ARM_F2: float(rows_f2[query_id]["ap_arm"]),
                    ARM_F: float(rows_f_status[query_id]["ap_arm"]),
                    DIRECT_READER: float(direct_reader[query_id]["ap"][DIRECT_READER]),
                    DIRECT_ONLY: float(baseline_row["ap"][DIRECT_ONLY]),
                    DIRECT_AGENTPROF: float(baseline_row["ap"][DIRECT_AGENTPROF]),
                },
                "h": rows_h[query_id],
                "f2": rows_f2[query_id],
                "f_status": rows_f_status[query_id],
            }
        )

    map_scores = {
        ARM_H: statistics.fmean(row["ap"][ARM_H] for row in joined),
        ARM_F2: statistics.fmean(row["ap"][ARM_F2] for row in joined),
        ARM_F: statistics.fmean(row["ap"][ARM_F] for row in joined),
        DIRECT_READER: statistics.fmean(row["ap"][DIRECT_READER] for row in joined),
        DIRECT_ONLY: statistics.fmean(row["ap"][DIRECT_ONLY] for row in joined),
        DIRECT_AGENTPROF: statistics.fmean(row["ap"][DIRECT_AGENTPROF] for row in joined),
    }
    # Invariant reproductions (mirror base harness / step 0080).
    base.require(
        math.isclose(map_scores[DIRECT_ONLY], STORED_DIRECT_ONLY_MAP, abs_tol=1e-12),
        f"Direct-only MAP reproduction failed: {map_scores[DIRECT_ONLY]}",
    )
    base.require(
        math.isclose(
            map_scores[DIRECT_AGENTPROF], STORED_DIRECT_AGENTPROF_MAP, abs_tol=1e-12
        ),
        f"Direct+AgentProf MAP reproduction failed: {map_scores[DIRECT_AGENTPROF]}",
    )
    base.require(
        math.isclose(map_scores[DIRECT_READER], STORED_DIRECT_READER_MAP, abs_tol=1e-9),
        f"Direct-reader MAP reproduction failed: {map_scores[DIRECT_READER]}",
    )
    # Stored H MAP must reproduce the authoritative step-0089 H number exactly.
    base.require(
        math.isclose(map_scores[ARM_H], base.read_json(args.stored_raw)["summary"]["map"]["hierarchical"], abs_tol=1e-9),
        f"H MAP reproduction failed: {map_scores[ARM_H]}",
    )

    # Paired H - F2 bootstrap (primary).
    boot_hf2 = base.paired_bootstrap_deltas(
        joined,
        lambda row: row["ap"][ARM_H] - row["ap"][ARM_F2],
        repetitions=BOOTSTRAP_REPS,
        seed=H_VS_F2_SEED,
    )
    comparison_hf2 = {
        "direction": "hierarchical - flat2",
        "point_effect": map_scores[ARM_H] - map_scores[ARM_F2],
        "interval_95": boot_hf2["interval_95"],
        "median": boot_hf2["median"],
        "nonpositive_draws": boot_hf2["nonpositive_draws"],
        "repetitions": boot_hf2["repetitions"],
        "seed": boot_hf2["seed"],
        "strata": boot_hf2["strata"],
        "clusters": boot_hf2["clusters"],
    }
    base.write_json(out_dir / "bootstrap-deltas-H-minus-F2.json", boot_hf2["draws"])

    # Also H - F(status) bootstrap with the ORIGINAL documented seed, so the
    # superseded arm's interval is reproducible from the same per-query data.
    boot_hf = base.paired_bootstrap_deltas(
        joined,
        lambda row: row["ap"][ARM_H] - row["ap"][ARM_F],
        repetitions=BOOTSTRAP_REPS,
        seed=base.H_VS_F_SEED,
    )
    comparison_hf = {
        "direction": "hierarchical - flat(status)",
        "point_effect": map_scores[ARM_H] - map_scores[ARM_F],
        "interval_95": boot_hf["interval_95"],
        "median": boot_hf["median"],
        "nonpositive_draws": boot_hf["nonpositive_draws"],
        "repetitions": boot_hf["repetitions"],
        "seed": boot_hf["seed"],
    }

    # Content-efficiency H - F2 (secondary).
    content_metrics = (
        "content_opened_fraction",
        "stage2_evidence_chars",
        "selected_evidence_operation_count",
    )
    content_deltas: dict[str, Any] = {}
    for metric in content_metrics:
        boot = base.paired_bootstrap_deltas(
            joined,
            lambda row, m=metric: float(row["h"][m]) - float(row["f2"][m]),
            repetitions=BOOTSTRAP_REPS,
            seed=CONTENT_DELTA_F2_SEED,
        )
        content_deltas[metric] = {
            "direction": "hierarchical - flat2",
            "point_effect": statistics.fmean(
                float(row["h"][metric]) - float(row["f2"][metric]) for row in joined
            ),
            "interval_95": boot["interval_95"],
            "median": boot["median"],
            "nonpositive_draws": boot["nonpositive_draws"],
            "repetitions": boot["repetitions"],
            "seed": boot["seed"],
        }
        base.write_json(
            out_dir / f"bootstrap-content-delta-f2-{metric}.json", boot["draws"]
        )

    def cost_block(arm_rows: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
        walls = [float(r["wall_seconds"]) for r in arm_rows.values()]
        chars = [int(r["total_chars"]) for r in arm_rows.values()]
        tokens = [int(r["prompt_tokens_o200k"]) for r in arm_rows.values()]
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

    def group_block(arm_rows: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
        counts = [int(r["group_count"]) for r in arm_rows.values()]
        largest = [int(r["largest_group_size"]) for r in arm_rows.values()]
        opened = [float(r["content_opened_fraction"]) for r in arm_rows.values()]
        sel_ops = [int(r["selected_evidence_operation_count"]) for r in arm_rows.values()]
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
                1.0 if r["index_hit"] else 0.0 for r in arm_rows.values()
            ),
            "index_hits": sum(1 for r in arm_rows.values() if r["index_hit"]),
        }

    def failure_block(arm_rows: Mapping[str, Mapping[str, Any]]) -> dict[str, int]:
        s1_ok = sum(r["stage1_status"] == "ok" for r in arm_rows.values())
        s1_retry = sum(r["stage1_status"] == "ok_after_retry" for r in arm_rows.values())
        s1_fail = sum(r["stage1_largest_groups_fallback"] for r in arm_rows.values())
        s2_fail = sum(r["stage2_scored_as_original_order_failure"] for r in arm_rows.values())
        s2_ok = sum(r["stage2_status"] == "ok" for r in arm_rows.values())
        s2_retry = sum(r["stage2_status"] == "ok_after_retry" for r in arm_rows.values())
        return {
            "stage1_ok": s1_ok,
            "stage1_ok_after_retry": s1_retry,
            "stage1_largest_groups_fallback": s1_fail,
            "stage2_ok": s2_ok,
            "stage2_ok_after_retry": s2_retry,
            "stage2_original_order_failures": s2_fail,
        }

    rows_h_map = {qid: rows_h[qid] for qid in query_ids}
    rows_f2_map = {qid: rows_f2[qid] for qid in query_ids}
    rows_f_map = {qid: rows_f_status[qid] for qid in query_ids}

    step0079_summary = base.read_json(args.step_0079_raw)["summary"]
    cost79 = step0079_summary["cost"]

    f2_vocab = f2_vocabulary(op_paths)

    summary = {
        "mode": args.mode,
        "benchmark": "TraceElephant",
        "harness": "hier_vs_flat_eval_f2.py",
        "amendment": "F2 corrected flat control (path[-4] = deepest semantic frame)",
        "target_bearing_queries": len(joined),
        "operations": sum(len(rows) for rows in projections.values()),
        "map": map_scores,
        "paired_h_minus_f2": comparison_hf2,
        "paired_h_minus_f_status_superseded": comparison_hf,
        "content_deltas_h_minus_f2": content_deltas,
        "failure_tally": {
            ARM_H: failure_block(rows_h_map),
            ARM_F2: failure_block(rows_f2_map),
            ARM_F: failure_block(rows_f_map),
        },
        "group_stats": {
            ARM_H: group_block(rows_h_map),
            ARM_F2: group_block(rows_f2_map),
            ARM_F: group_block(rows_f_map),
        },
        "cost": {
            ARM_H: cost_block(rows_h_map),
            ARM_F2: cost_block(rows_f2_map),
            ARM_F: cost_block(rows_f_map),
        },
        "cost_step0079": {
            "queries": cost79["queries"],
            "mean_packet_chars": cost79["mean_packet_chars"],
            "mean_wall_seconds": cost79["mean_wall_seconds"],
            "median_wall_seconds": cost79["median_wall_seconds"],
            "total_wall_seconds": cost79["total_wall_seconds"],
        },
        "bootstrap_seeds": {
            "H_minus_F2": H_VS_F2_SEED,
            "content_delta_F2": CONTENT_DELTA_F2_SEED,
            "H_minus_F_status_superseded": base.H_VS_F_SEED,
            "content_delta_F_status_superseded": base.CONTENT_DELTA_SEED,
        },
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
            "default_model": base.OPENCODE_DEFAULT_MODEL,
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
            "instruction_closing": base.CLOSING.strip(),
            "model_family": (
                "opencode/glm-5.2 for arm F2 (reader family held fixed; identical "
                "to arms H/F); differs from step-0080 grok, not pooled with it"
            ),
            "workers": args.workers,
        },
        "arm_definition": {
            ARM_H: "full source_preserving_agent path grouped by full path (step-0080 style)",
            ARM_F2: (
                "deepest semantic frame only — path component immediately before "
                "the fixed three-frame source-kind/call-tool/outcome suffix "
                f"(path[-{F2_INDEX_FROM_END}]); parent paths stripped; grouped by "
                "that single semantic tag"
            ),
            ARM_F: (
                "SUPERSEDED: last path component (outcome status frame) only; "
                "kept for labeled reference, not the authoritative flat control"
            ),
            "f2_vocabulary": f2_vocab,
            "f_status_vocabulary_size": 5,
            "f_status_vocabulary": ["blocked", "failure", "progress", "success", "unclear"],
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
                "f2": row["f2"],
                "f_status": row["f_status"],
            }
        )

    base.write_json(
        out_dir / "raw-results-f2.json",
        {"per_query": per_query_out, "summary": summary},
    )
    base.write_json(out_dir / "summary-f2.json", summary)
    base.write_text(out_dir / "results.md", render_results_md(summary))
    print(
        f"[score-f2] MAP H={map_scores[ARM_H]:.6f} F2={map_scores[ARM_F2]:.6f} "
        f"F(status)={map_scores[ARM_F]:.6f} "
        f"dH-F2={map_scores[ARM_H]-map_scores[ARM_F2]:+.6f} "
        f"opened_H={summary['group_stats'][ARM_H]['mean_content_opened_fraction']:.4f} "
        f"opened_F2={summary['group_stats'][ARM_F2]['mean_content_opened_fraction']:.4f} "
        f"hit_H={summary['group_stats'][ARM_H]['index_hit_rate']:.4f} "
        f"hit_F2={summary['group_stats'][ARM_F2]['index_hit_rate']:.4f} "
        f"f2_tags={f2_vocab['unique_tags']} "
        f"harness_wall={summary['wall_seconds_harness']:.1f}s",
        flush=True,
    )
    return summary


# ---------------------------------------------------------------------------
# results.md renderer — F2 authoritative, F(status) superseded (labeled)
# ---------------------------------------------------------------------------


def render_results_md(summary: Mapping[str, Any]) -> str:
    map_scores = summary["map"]
    cmp_f2 = summary["paired_h_minus_f2"]
    cmp_f = summary["paired_h_minus_f_status_superseded"]
    cd = summary["content_deltas_h_minus_f2"]
    gh = summary["group_stats"][ARM_H]
    gf2 = summary["group_stats"][ARM_F2]
    gf = summary["group_stats"][ARM_F]
    ch = summary["cost"][ARM_H]
    cf2 = summary["cost"][ARM_F2]
    ft_h = summary["failure_tally"][ARM_H]
    ft_f2 = summary["failure_tally"][ARM_F2]
    ft_f = summary["failure_tally"][ARM_F]
    cost79 = summary["cost_step0079"]
    vocab = summary["arm_definition"]["f2_vocabulary"]
    lo, hi = cmp_f2["interval_95"]
    clo, chi = cd["content_opened_fraction"]["interval_95"]

    h_map = map_scores[ARM_H]
    f2_map = map_scores[ARM_F2]
    opened_h = gh["mean_content_opened_fraction"]
    opened_f2 = gf2["mean_content_opened_fraction"]
    nonpos = cmp_f2["nonpositive_draws"]
    ranking_at_least_as_well = (lo >= 0.0) or (h_map >= f2_map and lo > -0.02)
    less_content = opened_h < opened_f2
    if ranking_at_least_as_well and less_content:
        verdict = "SUPPORTED"
    elif h_map >= f2_map and less_content:
        verdict = "PARTIALLY SUPPORTED (H >= F2 on MAP but the H−F2 interval crosses 0)"
    elif h_map < f2_map:
        verdict = "NOT SUPPORTED (flat F2 matches or beats hierarchical on MAP)"
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
        f"## Verdict (arm F2 = corrected flat control): {verdict}",
        "",
        "**Amendment note.** The flat control was rerun as arm F2 per the binding",
        "step-0089 amendment. Arm F as originally executed grouped by the LAST path",
        "component — the outcome status frame (5 tags: blocked/failure/progress/",
        "success/unclear), an orchestrator spec error. Arm F2 groups by the DEEPEST",
        "SEMANTIC frame: the path component immediately before the fixed three-frame",
        "source-kind/call-tool/outcome suffix (i.e. `source_preserving_agent[-4]`),",
        "the strongest fair flat projection of the same operations. Arm H is NOT",
        "rerun; F2 is paired against the stored arm-H per-query results (same reader",
        f"family, flags, jail recipe). Bootstrap seeds: H−F2 = {H_VS_F2_SEED}, "
        f"H−F2 content = {CONTENT_DELTA_F2_SEED}, "
        f"H−F(status, superseded) = {base.H_VS_F_SEED}/{base.CONTENT_DELTA_SEED}.",
        "The superseded F(status) numbers are retained below, labeled as such.",
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
        f"- **Arm F2 grouping key**: `source_preserving_agent[-{F2_INDEX_FROM_END}]` — "
        f"the deepest semantic frame; tag-vocabulary size = **{vocab['unique_tags']}** "
        f"(population-wide); mean groups/sequence = {vocab['mean_groups_per_sequence']:.2f}, "
        f"median = {vocab['median_groups_per_sequence']:.1f}, "
        f"min = {vocab['min_groups_per_sequence']}, max = {vocab['max_groups_per_sequence']}.",
        f"- Arm F(status) grouping key (SUPERSEDED): last path component — "
        f"{summary['arm_definition']['f_status_vocabulary_size']} tags "
        f"({', '.join(summary['arm_definition']['f_status_vocabulary'])}).",
        "- Scoring: sklearn non-interpolated `average_precision_score`; arithmetic MAP",
        f"- Paired bootstrap: {BOOTSTRAP_REPS:,} resamples of trajectory clusters within strata",
        f"  (H−F2 seed {H_VS_F2_SEED}; H−F2 content seed {CONTENT_DELTA_F2_SEED}; "
        f"H−F(status) seed {base.H_VS_F_SEED}/{base.CONTENT_DELTA_SEED})",
        "",
        "## Arms (reader family held fixed)",
        "",
        f"- **Arm H (hierarchical)**: {summary['arm_definition'][ARM_H]}.",
        f"- **Arm F2 (flat, corrected control)**: {summary['arm_definition'][ARM_F2]}.",
        f"- Arm F (flat, SUPERSEDED): {summary['arm_definition'][ARM_F]}.",
        "- Reader (BOTH arms): `opencode run --pure` from an empty jail, "
        "`stdin=/dev/null`, default model glm-5.2, no tools, one format retry, "
        "deterministic fallbacks. Same flags / same instruction text for both arms.",
        "",
        "## MAP",
        "",
        "| Arm / method | MAP |",
        "|---|---:|",
        f"| **Arm H — hierarchical** | **{map_scores[ARM_H]:.6f}** |",
        f"| **Arm F2 — flat (deepest semantic frame, corrected control)** | **{map_scores[ARM_F2]:.6f}** |",
        f"| Arm F — flat (outcome status; SUPERSEDED) | {map_scores[ARM_F]:.6f} |",
        f"| Direct reader (step 0079, reference) | {map_scores[DIRECT_READER]:.6f} |",
        f"| Direct+AgentProf (stored, reference) | {map_scores[DIRECT_AGENTPROF]:.6f} |",
        f"| Direct-only (stored, reference) | {map_scores[DIRECT_ONLY]:.6f} |",
        "",
        "## Paired difference (H − F2) — authoritative flat control",
        "",
        "| Metric | Point Δ | 95% interval | Nonpositive draws / 10000 |",
        "|---|---:|---:|---:|",
        f"| MAP (H − F2) | {cmp_f2['point_effect']:+.6f} | [{lo:+.6f}, {hi:+.6f}] | {nonpos} |",
        f"| content_opened_fraction (H − F2) | {cd['content_opened_fraction']['point_effect']:+.6f} | "
        f"[{clo:+.6f}, {chi:+.6f}] | {cd['content_opened_fraction']['nonpositive_draws']} |",
        f"| stage2_evidence_chars (H − F2) | {cd['stage2_evidence_chars']['point_effect']:+.1f} | "
        f"[{cd['stage2_evidence_chars']['interval_95'][0]:+.1f}, "
        f"{cd['stage2_evidence_chars']['interval_95'][1]:+.1f}] | "
        f"{cd['stage2_evidence_chars']['nonpositive_draws']} |",
        f"| selected_evidence_ops (H − F2) | {cd['selected_evidence_operation_count']['point_effect']:+.3f} | "
        f"[{cd['selected_evidence_operation_count']['interval_95'][0]:+.3f}, "
        f"{cd['selected_evidence_operation_count']['interval_95'][1]:+.3f}] | "
        f"{cd['selected_evidence_operation_count']['nonpositive_draws']} |",
        "",
        "## Paired difference (H − F status) — SUPERSEDED, retained for continuity",
        "",
        "| Metric | Point Δ | 95% interval | Nonpositive draws / 10000 |",
        "|---|---:|---:|---:|",
        f"| MAP (H − F status) | {cmp_f['point_effect']:+.6f} | "
        f"[{cmp_f['interval_95'][0]:+.6f}, {cmp_f['interval_95'][1]:+.6f}] | "
        f"{cmp_f['nonpositive_draws']} |",
        "",
        "## Index-hit rate (target operation inside a selected group)",
        "",
        "| Arm | Index-hit rate | Hits / 220 | Mean groups | Median groups | Largest group (mean) |",
        "|---|---:|---:|---:|---:|---:|",
        f"| H (hierarchical) | {gh['index_hit_rate']:.4f} | {gh['index_hits']} | "
        f"{gh['mean_group_count']:.2f} | {gh['median_group_count']:.2f} | {gh['mean_largest_group_size']:.2f} |",
        f"| F2 (flat, corrected) | {gf2['index_hit_rate']:.4f} | {gf2['index_hits']} | "
        f"{gf2['mean_group_count']:.2f} | {gf2['median_group_count']:.2f} | {gf2['mean_largest_group_size']:.2f} |",
        f"| F (flat, SUPERSEDED) | {gf['index_hit_rate']:.4f} | {gf['index_hits']} | "
        f"{gf['mean_group_count']:.2f} | {gf['median_group_count']:.2f} | {gf['mean_largest_group_size']:.2f} |",
        "",
        "## Content opened (stage-2 evidence chars / step-0079 full packet chars)",
        "",
        "| Arm | Mean opened | Median opened | Mean selected evidence ops |",
        "|---|---:|---:|---:|",
        f"| H (hierarchical) | {gh['mean_content_opened_fraction']:.4f} | "
        f"{gh['median_content_opened_fraction']:.4f} | {gh['mean_selected_evidence_ops']:.2f} |",
        f"| F2 (flat, corrected) | {gf2['mean_content_opened_fraction']:.4f} | "
        f"{gf2['median_content_opened_fraction']:.4f} | {gf2['mean_selected_evidence_ops']:.2f} |",
        f"| F (flat, SUPERSEDED) | {gf['mean_content_opened_fraction']:.4f} | "
        f"{gf['median_content_opened_fraction']:.4f} | {gf['mean_selected_evidence_ops']:.2f} |",
        "",
        "## Failure tally",
        "",
        "| Tally | H | F2 | F (SUPERSEDED) |",
        "|---|---:|---:|---:|",
        f"| Stage-1 OK first attempt | {ft_h['stage1_ok']} | {ft_f2['stage1_ok']} | {ft_f['stage1_ok']} |",
        f"| Stage-1 OK after retry | {ft_h['stage1_ok_after_retry']} | {ft_f2['stage1_ok_after_retry']} | {ft_f['stage1_ok_after_retry']} |",
        f"| Stage-1 largest-groups fallback | {ft_h['stage1_largest_groups_fallback']} | {ft_f2['stage1_largest_groups_fallback']} | {ft_f['stage1_largest_groups_fallback']} |",
        f"| Stage-2 OK first attempt | {ft_h['stage2_ok']} | {ft_f2['stage2_ok']} | {ft_f['stage2_ok']} |",
        f"| Stage-2 OK after retry | {ft_h['stage2_ok_after_retry']} | {ft_f2['stage2_ok_after_retry']} | {ft_f['stage2_ok_after_retry']} |",
        f"| Stage-2 original-order failures | {ft_h['stage2_original_order_failures']} | {ft_f2['stage2_original_order_failures']} | {ft_f['stage2_original_order_failures']} |",
        "",
        "## Cost (per query)",
        "",
        "| Metric | H | F2 | F (SUPERSEDED) | Direct reader (0079) |",
        "|---|---:|---:|---:|---:|",
        f"| Mean total chars | {ch['mean_total_chars']:.1f} | {cf2['mean_total_chars']:.1f} | {summary['cost'][ARM_F]['mean_total_chars']:.1f} | {cost79['mean_packet_chars']:.1f} |",
        f"| Median total chars | {ch['median_total_chars']:.1f} | {cf2['median_total_chars']:.1f} | {summary['cost'][ARM_F]['median_total_chars']:.1f} | — |",
        f"| Mean wall seconds | {ch['mean_wall_seconds']:.2f} | {cf2['mean_wall_seconds']:.2f} | {summary['cost'][ARM_F]['mean_wall_seconds']:.2f} | {cost79['mean_wall_seconds']:.2f} |",
        f"| Median wall seconds | {ch['median_wall_seconds']:.2f} | {cf2['median_wall_seconds']:.2f} | {summary['cost'][ARM_F]['median_wall_seconds']:.2f} | {cost79['median_wall_seconds']:.2f} |",
        f"| Mean prompt tokens (o200k) | {ch['mean_prompt_tokens_o200k']:.0f} | {cf2['mean_prompt_tokens_o200k']:.0f} | {summary['cost'][ARM_F]['mean_prompt_tokens_o200k']:.0f} | — |",
        "",
        "## F2 tag vocabulary (population-wide)",
        "",
        f"Grouping key = `source_preserving_agent[-{F2_INDEX_FROM_END}]` (deepest semantic "
        f"frame, immediately before the source-kind/call-tool/outcome suffix). "
        f"Unique tags = **{vocab['unique_tags']}**.",
        "",
        f"Top tags by operation count: "
        + ", ".join(
            f"`{tag}` ({count})"
            for tag, count in list(vocab["tag_counts"].items())[:10]
        )
        + ".",
        "",
        "## Honest interpretation",
        "",
        f"On the complete TraceElephant population (n={summary['target_bearing_queries']}), "
        "with the opencode/glm-5.2 reader family held fixed, using the corrected flat "
        "control F2 (deepest semantic frame, not the outcome status tag):",
        f"- Hierarchical MAP = {map_scores[ARM_H]:.4f}; Flat F2 MAP = {map_scores[ARM_F2]:.4f}; "
        f"superseded F(status) MAP = {map_scores[ARM_F]:.4f}.",
        f"- Paired H − F2 ΔMAP = {cmp_f2['point_effect']:+.4f}, 95% interval "
        f"[{lo:+.4f}, {hi:+.4f}], {nonpos}/10000 nonpositive draws.",
        f"- Mean content opened: H = {opened_h:.1%}, F2 = {opened_f2:.1%} of the "
        f"step-0079 full-trace packet volume.",
        f"- Index-hit rate: H = {gh['index_hit_rate']:.1%}, F2 = {gf2['index_hit_rate']:.1%}.",
        f"- F2 flat tag vocabulary = {vocab['unique_tags']} semantic tags (vs. 5 outcome "
        "tags for the superseded F(status) arm).",
        "",
        f"**Verdict (F2 authoritative): {verdict}.**",
        "",
        "Caveats: F2 is the strongest single-frame flat projection of the same "
        "operations (the deepest semantic frame, with 42 tags), but it is still a "
        "one-component flat projection — the hierarchical arm keeps the full "
        "multi-component path. This measures whether the nesting carries navigation "
        "value beyond the single deepest semantic name for THIS reader family and "
        "workload. It does not evaluate other readers or other workloads, and it is "
        "not pooled with the step-0080 grok-reader result. The superseded F(status) "
        "arm grouped by the outcome tag (5 tags) and is retained only for continuity.",
        "",
        "This file reports the complete 220-query run. The 40-per-arm pilot is an "
        "operational gate (parse-failure rate < 10%), recorded in `execution-log.md`, "
        "and is not a paper result.",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=("pilot", "full", "score-only"),
        help=(
            "pilot: 40 F2 queries (operational gate); full: 220 F2 queries then "
            "score H vs F2; score-only: re-score H vs F2 from cached responses"
        ),
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--pilot-n", type=int, default=base.PILOT_N)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--trace-root", type=Path, default=base.TRACE_ROOT)
    parser.add_argument("--packet-root", type=Path, default=base.PACKET_ROOT)
    parser.add_argument("--baseline-per-query", type=Path, default=base.BASELINE_PER_QUERY)
    parser.add_argument("--group-mapping", type=Path, default=base.GROUP_MAPPING)
    parser.add_argument("--step-0079-raw", type=Path, default=base.STEP_0079_RAW)
    parser.add_argument(
        "--stored-raw",
        type=Path,
        default=DEFAULT_OUT / "raw-results.json",
        help="stored step-0089 raw-results.json with authoritative arm-H per-query",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()

    group_path = args.group_mapping.resolve()
    if not group_path.is_file():
        print(f"[abort] group mapping missing: {group_path}", flush=True)
        return 2

    packets = base.load_packets(args.packet_root.resolve())
    projections = base.load_projections(args.trace_root.resolve())
    targets = base.load_targets(args.trace_root.resolve())
    baselines = base.load_baseline_aps(args.baseline_per_query.resolve())
    direct_reader = base.load_direct_reader_aps(args.step_0079_raw.resolve())
    op_paths = base.load_group_mapping(group_path)

    base.require(
        set(packets)
        == set(projections)
        == set(targets)
        == set(baselines)
        == set(direct_reader),
        "query_id coverage mismatch among inputs",
    )
    for query_id, rows in projections.items():
        for row in rows:
            base.require(
                str(row["operation_id"]) in op_paths,
                f"unmapped op {row['operation_id']}",
            )

    all_ids = sorted(packets)
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
        "group_key": base.GROUP_KEY,
        "stored_raw_results": str(args.stored_raw.resolve()),
    }

    if args.mode == "pilot":
        pilot_ids = all_ids[: args.pilot_n]
        print(
            f"[pilot-f2] queries={len(pilot_ids)} workers={args.workers} "
            f"out={out_dir} jail={jail}",
            flush=True,
        )
        rows_f2 = base.run_arm_phase(
            ARM_F2, pilot_ids, packets, projections, targets, direct_reader,
            op_paths, out_dir, jail,
            workers=args.workers,
            force=args.force,
            started=started,
            phase_label="pilot-f2",
        )
        f2_fail = base.parse_failure_rate(rows_f2)
        f2_ok = base.parse_ok_rate(rows_f2)
        note = {
            "pilot_n": len(pilot_ids),
            "query_ids": list(pilot_ids),
            "parse_failure_gate": base.PARSE_FAILURE_GATE,
            "flat2": {
                "parse_failure_rate": f2_fail,
                "stage1_ok": f2_ok[0],
                "stage1_ok_after_retry": f2_ok[1],
                "stage1_largest_groups_fallback": f2_ok[2],
                "stage2_original_order_failures": f2_ok[3],
                "mean_ap": statistics.fmean(r["ap_arm"] for r in rows_f2.values()),
                "mean_content_opened_fraction": statistics.fmean(
                    r["content_opened_fraction"] for r in rows_f2.values()
                ),
                "index_hit_rate": statistics.fmean(
                    1.0 if r["index_hit"] else 0.0 for r in rows_f2.values()
                ),
            },
            "gate_pass": f2_fail < base.PARSE_FAILURE_GATE,
            "wall_seconds": time.monotonic() - started,
            "note": (
                "Operational pilot gate only (parse-failure rate < 10%); F2 is a "
                "new condition, so the gate is not score-based. Not a paper result."
            ),
        }
        base.write_json(out_dir / "pilot-f2-summary.json", note)
        print(
            f"[pilot-f2] parse_failure F2={f2_fail:.3f} "
            f"gate={'PASS' if f2_fail < base.PARSE_FAILURE_GATE else 'FAIL'} "
            f"wall={time.monotonic()-started:.1f}s",
            flush=True,
        )
        return 0

    # full or score-only
    query_ids = all_ids
    if args.limit is not None:
        query_ids = query_ids[: args.limit]

    def reload(arm: str) -> dict[str, dict[str, Any]]:
        rows: dict[str, dict[str, Any]] = {}
        for qid in query_ids:
            rows[qid] = base.process_one_query(
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

    if args.mode == "score-only":
        rows_f2 = reload(ARM_F2)
    else:
        base.require(
            len(query_ids) == 220,
            f"full population requires 220 queries, got {len(query_ids)}",
        )
        print(
            f"[full-f2] queries={len(query_ids)} workers={args.workers} "
            f"out={out_dir} jail={jail}",
            flush=True,
        )
        rows_f2 = base.run_arm_phase(
            ARM_F2, query_ids, packets, projections, targets, direct_reader,
            op_paths, out_dir, jail,
            workers=args.workers,
            force=args.force,
            started=started,
            phase_label="full-f2",
        )

    # H is NOT rerun: re-derive its metrics from the cached authoritative H run.
    rows_h = reload(ARM_H)
    # Superseded F(status) metrics re-derived from its cache for continuity.
    rows_f_status = reload(ARM_F)
    # Cross-check the stored H raw-results match the re-derived H cache.
    stored_h = load_stored_h_per_query(args.stored_raw.resolve())
    for qid in query_ids:
        base.require(
            math.isclose(
                float(rows_h[qid]["ap_arm"]),
                float(stored_h[qid]["ap_arm"]),
                abs_tol=1e-12,
            ),
            f"H AP mismatch for {qid}: cache={rows_h[qid]['ap_arm']} "
            f"stored={stored_h[qid]['ap_arm']}",
        )

    score_h_f2(
        rows_h, rows_f2, rows_f_status, query_ids, baselines, direct_reader,
        projections, op_paths, out_dir, started, provenance, args,
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except base.ExperimentError as exc:
        print(f"[experiment-error] {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
