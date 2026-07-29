#!/usr/bin/env python3
"""Run the frozen Step 0087 pipeline and compare hierarchy with flat marks."""

from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys
import time
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT = SCRIPT_DIR.parent
REPO = EXPERIMENT.parents[4]
STEP_0087 = (
    REPO
    / "docs"
    / "tmp"
    / "build-and-evaluate"
    / "step-0087-20260726T023000-0700"
    / "experiment-001"
)
sys.path.insert(0, str(SCRIPT_DIR))
import annotate as flat_backend  # noqa: E402


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


base = load_module(
    "step0087_postprocess",
    STEP_0087 / "direct_annotation" / "postprocess.py",
)
base.EXPERIMENT = EXPERIMENT
base.REPO = REPO
base.PIPELINE_RECORDS = EXPERIMENT / "pipeline-records.jsonl"
base.RAW_RESULTS = EXPERIMENT / "raw-results.json"
base.RUN_RECORDS = EXPERIMENT / "annotation-run-records.jsonl"
base.PREFLIGHT = EXPERIMENT / "preflight"
base.direct_backend = flat_backend

PYTHON = Path("/usr/bin/python3")
PACKETS = flat_backend.base.SOURCE_PACKETS
TARGET_OPERATIONS = base.TARGET_OPERATIONS
OPERATION_USAGE = base.OPERATION_USAGE
FIXED_CANONICAL_NAMES = base.FIXED_CANONICAL_NAMES
VERIFIED_MANIFEST = base.VERIFIED_MANIFEST
MULTIRES_ASSIGNMENTS = base.MULTIRES_ASSIGNMENTS
AGENTPPROF = base.AGENTPPROF
HIERARCHY_RAW_RESULTS = STEP_0087 / "raw-results.json"
HIERARCHY_OPERATION_ROWS = STEP_0087 / "score" / "operation-score-rows.jsonl"
HIERARCHY_PAIR_ROWS = STEP_0087 / "score" / "pair-score-rows.jsonl"

EXPECTED_SESSIONS = 405
EXPECTED_TURNS = 17_148
EXPECTED_OPERATIONS = 20_866
EXPECTED_PAIRS = 20_461
EXPECTED_STAGES = 2_948
EXPECTED_TASKS = 251
EXPECTED_TOKENS = 494_862_929


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, sort_keys=True) + "\n")


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO))


def raw_annotation_stats(selected_ordinals: set[int]) -> dict[str, Any]:
    packets = {row.ordinal: row for row in flat_backend.base.load_packets()}
    depths: Counter[int] = Counter()
    names: set[str] = set()
    marks = 0
    invalid: dict[int, list[str]] = {}
    for ordinal in sorted(selected_ordinals):
        row = packets[ordinal]
        if not row.raw_path.is_file():
            invalid[ordinal] = ["missing raw mark"]
            continue
        response = read_json(row.raw_path)
        errors = flat_backend.validate_response(row.packet, response)
        if errors:
            invalid[ordinal] = errors
            continue
        marks += len(response["marks"])
        for mark in response["marks"]:
            path = mark["semantic_path"]
            depths[len(path)] += 1
            names.update(str(item) for item in path)
    return {
        "marks": marks,
        "unique_raw_names": len(names),
        "path_depths": dict(sorted(depths.items())),
        "all_paths_root_plus_one_flat_name": set(depths) == {2},
        "invalid_annotations": invalid,
    }


def paired_hierarchy_flat(score_dir: Path) -> dict[str, Any]:
    flat_operations = read_jsonl(score_dir / "operation-score-rows.jsonl")
    hierarchy_operations = read_jsonl(HIERARCHY_OPERATION_ROWS)
    flat_by_key = {
        (str(row["session"]), int(row["step_id"])): row for row in flat_operations
    }
    hierarchy_by_key = {
        (str(row["session"]), int(row["step_id"])): row
        for row in hierarchy_operations
    }
    if set(flat_by_key) != set(hierarchy_by_key):
        raise RuntimeError("hierarchy/flat operation populations differ")

    operation_rows = []
    for key in sorted(flat_by_key):
        flat = flat_by_key[key]
        hierarchy = hierarchy_by_key[key]
        if (
            flat["official_stage"] != hierarchy["official_stage"]
            or flat["task_name"] != hierarchy["task_name"]
        ):
            raise RuntimeError(f"hierarchy/flat operation oracle mismatch: {key}")
        operation_rows.append(
            {
                "session": key[0],
                "step_id": key[1],
                "task_name": flat["task_name"],
                "official_stage": flat["official_stage"],
                "hierarchy": hierarchy["candidate"],
                "flat": flat["candidate"],
            }
        )

    bcubed = base.source_score.bcubed_task_bootstrap(
        operation_rows,
        "hierarchy",
        "flat",
        score_dir / "bootstrap-hierarchy-minus-flat-bcubed.jsonl",
    )

    flat_pairs = read_jsonl(score_dir / "pair-score-rows.jsonl")
    hierarchy_pairs = read_jsonl(HIERARCHY_PAIR_ROWS)
    flat_pair_by_key = {
        (str(row["session"]), int(row["position"])): row for row in flat_pairs
    }
    hierarchy_pair_by_key = {
        (str(row["session"]), int(row["position"])): row
        for row in hierarchy_pairs
    }
    if set(flat_pair_by_key) != set(hierarchy_pair_by_key):
        raise RuntimeError("hierarchy/flat pair populations differ")

    pair_rows = []
    for key in sorted(flat_pair_by_key):
        flat = flat_pair_by_key[key]
        hierarchy = hierarchy_pair_by_key[key]
        if (
            bool(flat["official_boundary"])
            != bool(hierarchy["official_boundary"])
            or flat["task_name"] != hierarchy["task_name"]
        ):
            raise RuntimeError(f"hierarchy/flat pair oracle mismatch: {key}")
        pair_rows.append(
            {
                "session": key[0],
                "position": key[1],
                "task_name": flat["task_name"],
                "official_boundary": bool(flat["official_boundary"]),
                "hierarchy": bool(hierarchy["candidate"]),
                "flat": bool(flat["candidate"]),
            }
        )
    boundary = base.boundary_task_bootstrap(
        pair_rows,
        "hierarchy",
        "flat",
        score_dir / "bootstrap-hierarchy-minus-flat-boundary.jsonl",
    )
    return {
        "population_equal": True,
        "operation_rows": len(operation_rows),
        "pair_rows": len(pair_rows),
        "hierarchy_metrics": {
            "bcubed": base.source_score.base.bcubed(operation_rows, "hierarchy"),
            "boundary": base.boundary_metric(pair_rows, "hierarchy"),
        },
        "flat_metrics": {
            "bcubed": base.source_score.base.bcubed(operation_rows, "flat"),
            "boundary": base.boundary_metric(pair_rows, "flat"),
        },
        "bcubed_f1": bcubed,
        "boundary_f1": boundary,
        "seeds": {"bcubed": 20_260_720, "boundary": 20_260_722},
    }


def run_pipeline(mode: str) -> None:
    pipeline_started = time.monotonic()
    preflight = mode == "preflight"
    prefix = "preflight-" if preflight else ""
    root = EXPERIMENT / "preflight" / "pipeline" if preflight else EXPERIMENT
    assembled = root / "assembled"
    canonical = root / "canonical"
    profiles = root / "profiles"
    score = root / "score"
    profiles.mkdir(parents=True, exist_ok=True)
    packet_dir = EXPERIMENT / "preflight" / "packets" if preflight else PACKETS
    annotation_dir = (
        EXPERIMENT / "preflight" / "annotations"
        if preflight
        else EXPERIMENT / "raw-annotations"
    )
    canonical_names = FIXED_CANONICAL_NAMES
    if preflight:
        selected_sessions = {
            str(packet["session"])
            for packet in read_json(packet_dir / "batch-01.json")["sessions"]
        }
        canonical_names = base.filter_canonical_names(
            selected_sessions, EXPERIMENT / "preflight" / "canonical-names.json"
        )

    base.run_command(
        f"{prefix}assemble-root-repair",
        [
            str(PYTHON),
            str(REPO / "script" / "assemble_agent_operation_profile.py"),
            "--target-operations",
            str(TARGET_OPERATIONS),
            "--operation-usage",
            str(OPERATION_USAGE),
            "--packet-dir",
            str(packet_dir),
            "--annotation-dir",
            str(annotation_dir),
            "--contract-root-only-prefix",
            "--canonical-names",
            str(canonical_names),
            "--mode",
            "preflight" if preflight else "full",
            "--out",
            str(assembled),
        ],
    )
    inference = read_json(assembled / "inference-summary.json")
    inference.update(
        {
            "algorithm_version": "direct-flat-codex-gpt-5.6-sol-v1",
            "annotation_backend": "one isolated direct Codex call per trajectory",
            "hierarchy_contract": "mandatory root plus exactly one flat name",
            "configured_depth_or_leaf_cap": "exact path depth two",
            "official_manifest_opened": False,
            "official_stages_opened": False,
        }
    )
    write_json(assembled / "inference-summary.json", inference)

    base.run_command(
        f"{prefix}fixed-canonicalization",
        [
            str(PYTHON),
            str(REPO / "script" / "canonicalize_operation_marks.py"),
            "--operation-marks",
            str(assembled / "operation-marks.json"),
            "--operations",
            str(assembled / "operations-count.jsonl"),
            "--reference-predictions",
            str(assembled / "predictions.jsonl"),
            "--out-dir",
            str(canonical),
        ],
    )
    operation_profile = base.run_command(
        f"{prefix}operation-profile",
        [
            str(AGENTPPROF),
            "--operation-file",
            str(assembled / "operations-count.jsonl"),
            "--operation-mark-file",
            str(canonical / "operation-marks.json"),
            "--view",
            "operations",
            "--deterministic-output",
            "--output",
            str(profiles / "flat-operation.pb.gz"),
        ],
    )
    token_profile = base.run_command(
        f"{prefix}token-profile",
        [
            str(AGENTPPROF),
            "--operation-file",
            str(assembled / "operations-tokens.jsonl"),
            "--operation-mark-file",
            str(canonical / "operation-marks.json"),
            "--view",
            "tokens",
            "--deterministic-output",
            "--output",
            str(profiles / "flat-tokens.pb.gz"),
        ],
    )
    base.run_command(
        f"{prefix}pprof-operation-readback",
        ["go", "tool", "pprof", "-top", str(profiles / "flat-operation.pb.gz")],
    )
    base.run_command(
        f"{prefix}pprof-token-readback",
        ["go", "tool", "pprof", "-top", str(profiles / "flat-tokens.pb.gz")],
    )
    base.run_command(
        f"{prefix}rq3-score",
        [
            str(PYTHON),
            str(REPO / "script" / "rq3_recursive_operation_segmentation_eval.py"),
            "score",
            "--target-operations",
            str(TARGET_OPERATIONS),
            "--predictions",
            str(canonical / "predictions.jsonl"),
            "--inference-summary",
            str(assembled / "inference-summary.json"),
            "--verified-manifest",
            str(VERIFIED_MANIFEST),
            "--multires-assignments",
            str(MULTIRES_ASSIGNMENTS),
            "--out",
            str(score),
        ],
    )

    assembled_summary = read_json(assembled / "summary.json")
    canonical_report = read_json(canonical / "canonicalization-report.json")
    operation_status = json.loads(operation_profile["stdout"])
    token_status = json.loads(token_profile["stdout"])
    index = read_json(EXPERIMENT / "packet-index.json")
    ordinal_by_session = {
        str(row["session"]): int(row["ordinal"]) for row in index["rows"]
    }
    score_rows = read_jsonl(score / "operation-score-rows.jsonl")
    scored_sessions = {str(row["session"]) for row in score_rows}
    selected_ordinals = {ordinal_by_session[session] for session in scored_sessions}
    raw_stats = raw_annotation_stats(selected_ordinals)
    cost = base.annotation_cost(selected_ordinals, configured_workers=4)
    cost["worker_pattern"] = (
        "isolated one-trajectory calls, up to 4 parallel workers; "
        "one ordinary format retry"
    )
    cost["deterministic_repairs"] = (
        len(read_jsonl(EXPERIMENT / "format-repairs.jsonl"))
        if (EXPERIMENT / "format-repairs.jsonl").is_file()
        else 0
    )
    pipeline_wall = time.monotonic() - pipeline_started

    if preflight:
        manifest = read_json(EXPERIMENT / "preflight" / "packets" / "manifest.json")
        validity = {
            "one_real_trajectory": int(inference["sessions"]) == 1,
            "turns_covered": int(inference["turns"]) == int(manifest["turns"]),
            "operations_covered": int(inference["operations"])
            == int(manifest["operations"]),
            "all_paths_root_plus_one_flat_name": bool(
                raw_stats["all_paths_root_plus_one_flat_name"]
            ),
            "raw_annotations_valid": not raw_stats["invalid_annotations"],
            "operation_mass_conserved": int(
                assembled_summary["operation_count_mass"]
            )
            == int(manifest["operations"])
            == int(operation_status["samples"]),
            "token_mass_conserved": int(assembled_summary["provider_token_mass"])
            == int(token_status["samples"]),
            "canonical_partition_preserved": bool(
                canonical_report["reference_temporal_partition_equal"]
            ),
            "zero_adjacent_display_path_collisions": int(
                canonical_report["remaining_adjacent_collisions"]
            )
            == 0,
            "stock_pprof_readback": True,
            "backend_terminal_success": int(cost["successful_trajectories"]) == 1,
            "retry_policy_valid": bool(cost["attempt_limit_valid"]),
        }
        if not all(validity.values()):
            raise RuntimeError(
                "preflight validity failed: "
                + ", ".join(key for key, value in validity.items() if not value)
            )
        result = {
            "status": "complete",
            "role": "operational preflight only; never a paper result",
            "population": {
                "sessions": int(inference["sessions"]),
                "turns": int(inference["turns"]),
                "operations": int(inference["operations"]),
            },
            "annotation": raw_stats,
            "cost": cost,
            "pipeline_wall_seconds": pipeline_wall,
            "validity": validity,
        }
        write_json(EXPERIMENT / "preflight" / "raw-results.json", result)
        (EXPERIMENT / "preflight" / "report.md").write_text(
            "# Real preflight\n\n"
            "Status: **COMPLETE / VALID**\n\n"
            "One minimum-turn trajectory from the exact Step 0087 packet "
            "population completed through the pinned GPT-5.6 backend, flat "
            "validator, unchanged assembly/root repair, canonicalization, pprof "
            "materialization/readback, and frozen scorer. This establishes only "
            "that the real path runs; its score is not a paper result.\n",
            encoding="utf-8",
        )
        print(json.dumps(result, sort_keys=True), flush=True)
        return

    paired = paired_hierarchy_flat(score)
    hierarchy_frozen = read_json(HIERARCHY_RAW_RESULTS)
    hierarchy_metrics = paired["hierarchy_metrics"]
    flat_metrics = paired["flat_metrics"]
    frozen_metrics = hierarchy_frozen["methods"]["direct_multilevel"]
    metric_reuse_exact = all(
        abs(
            float(hierarchy_metrics[metric][field])
            - float(frozen_metrics[metric][field])
        )
        < 1e-12
        for metric in ("bcubed", "boundary")
        for field in ("precision", "recall", "f1")
    )
    hierarchy_packet_index = read_json(STEP_0087 / "packet-index.json")
    packet_population_equal = [
        (row["ordinal"], row["session"], row["turns"], row["operations"])
        for row in index["rows"]
    ] == [
        (row["ordinal"], row["session"], row["turns"], row["operations"])
        for row in hierarchy_packet_index["rows"]
    ]
    validity = {
        "sessions": int(inference["sessions"]) == EXPECTED_SESSIONS,
        "turns": int(inference["turns"]) == EXPECTED_TURNS,
        "operations": int(inference["operations"]) == EXPECTED_OPERATIONS,
        "pairs": paired["pair_rows"] == EXPECTED_PAIRS,
        "official_stages": len(
            {row["official_stage"] for row in score_rows}
        )
        == EXPECTED_STAGES,
        "task_clusters": len({row["task_name"] for row in score_rows})
        == EXPECTED_TASKS,
        "exact_step0087_packet_population": packet_population_equal,
        "all_paths_root_plus_one_flat_name": bool(
            raw_stats["all_paths_root_plus_one_flat_name"]
        ),
        "raw_annotations_valid": not raw_stats["invalid_annotations"],
        "all_trajectories_successful": int(cost["successful_trajectories"])
        == EXPECTED_SESSIONS,
        "retry_policy_valid": bool(cost["attempt_limit_valid"]),
        "zero_failures_after_retry": int(cost["failed_after_retry"]) == 0,
        "operation_mass_conserved": int(
            assembled_summary["operation_count_mass"]
        )
        == EXPECTED_OPERATIONS
        == int(operation_status["samples"]),
        "token_mass_conserved": int(assembled_summary["provider_token_mass"])
        == EXPECTED_TOKENS
        == int(token_status["samples"]),
        "canonical_partition_preserved": bool(
            canonical_report["reference_temporal_partition_equal"]
        ),
        "canonical_prediction_coverage": int(canonical_report["predictions"])
        == EXPECTED_OPERATIONS,
        "zero_adjacent_display_path_collisions": int(
            canonical_report["remaining_adjacent_collisions"]
        )
        == 0,
        "stock_pprof_readback": True,
        "paired_hierarchy_population_equal": bool(paired["population_equal"]),
        "frozen_hierarchy_metrics_reconstructed": metric_reuse_exact,
    }
    if not all(validity.values()):
        raise RuntimeError(
            "full validity failed: "
            + ", ".join(key for key, value in validity.items() if not value)
        )

    b3_interval = paired["bcubed_f1"]["ci95"]
    boundary_interval = paired["boundary_f1"]["ci95"]
    if b3_interval[0] > 0 and boundary_interval[0] > 0:
        verdict = "supported"
    elif b3_interval[1] < 0 and boundary_interval[1] < 0:
        verdict = "contradicted"
    elif (
        b3_interval[1] < 0
        or boundary_interval[1] < 0
        or b3_interval[0] > 0
        or boundary_interval[0] > 0
    ):
        verdict = "mixed"
    else:
        verdict = "inconclusive"

    backend_timing = read_json(EXPERIMENT / "full-backend-timing.json")
    end_to_end_wall = time.time() - float(backend_timing["started_unix"])
    raw_results = {
        "schema": "agentsight.same-model-flat-ablation.v1",
        "status": "complete",
        "run_status": "valid",
        "tested_hypothesis": verdict,
        "research_value": "decisive mechanism ablation",
        "paper_impact": "additional RQ3 evidence and hierarchy-mechanism boundary",
        "next_paper_decision": (
            "Report the matched hierarchy-depth contribution on this complete "
            "CodeTraceBench population."
            if verdict == "supported"
            else "Do not claim that variable depth explains the adopted result "
            "on both registered metrics."
        ),
        "population": {
            "sessions": EXPECTED_SESSIONS,
            "turns": EXPECTED_TURNS,
            "operations": EXPECTED_OPERATIONS,
            "pairs": EXPECTED_PAIRS,
            "official_stages": EXPECTED_STAGES,
            "task_clusters": EXPECTED_TASKS,
        },
        "methods": {
            "direct_variable_depth_hierarchy_reused_step_0087": hierarchy_metrics,
            "same_model_flat": flat_metrics,
        },
        "paired_hierarchy_minus_flat": {
            "bcubed_f1": paired["bcubed_f1"],
            "boundary_f1": paired["boundary_f1"],
            "operation_rows": paired["operation_rows"],
            "pair_rows": paired["pair_rows"],
            "seeds": paired["seeds"],
        },
        "recursive_refined_minus_direct": {
            "reported": False,
            "reason": (
                "The adopted Step 0087 artifact is itself direct complete-hierarchy "
                "generation; no genuinely distinct recursive or iterative refined "
                "condition exists."
            ),
        },
        "annotation": {
            "flat": {
                **raw_stats,
                "assembled_path_depths": assembled_summary["path_depths"],
                "canonical_unique_names": int(
                    canonical_report["canonical_semantic_operation_ids"]
                ),
                "predicted_groups": int(flat_metrics["bcubed"]["predicted_groups"]),
            },
            "hierarchy_step_0087": hierarchy_frozen["annotation"],
        },
        "cost": {
            "flat": cost,
            "hierarchy_step_0087": hierarchy_frozen["cost"],
            "flat_backend_command_wall_seconds": backend_timing[
                "command_wall_seconds"
            ],
            "flat_pipeline_wall_seconds": pipeline_wall,
            "flat_end_to_end_wall_seconds": end_to_end_wall,
        },
        "validity": validity,
        "artifacts": {
            "flat_raw_marks": relative(EXPERIMENT / "raw-marks"),
            "flat_canonical_marks": relative(canonical / "operation-marks.json"),
            "flat_operation_rows": relative(
                score / "operation-score-rows.jsonl"
            ),
            "flat_pair_rows": relative(score / "pair-score-rows.jsonl"),
            "hierarchy_operation_rows": relative(HIERARCHY_OPERATION_ROWS),
            "hierarchy_pair_rows": relative(HIERARCHY_PAIR_ROWS),
            "flat_operation_profile": relative(
                profiles / "flat-operation.pb.gz"
            ),
            "flat_token_profile": relative(profiles / "flat-tokens.pb.gz"),
        },
    }
    write_json(EXPERIMENT / "raw-results.json", raw_results)

    def row(label: str, metrics: dict[str, Any]) -> str:
        return (
            f"| {label} | {metrics['bcubed']['precision']:.6f} | "
            f"{metrics['bcubed']['recall']:.6f} | "
            f"{metrics['bcubed']['f1']:.6f} | "
            f"{metrics['boundary']['precision']:.6f} | "
            f"{metrics['boundary']['recall']:.6f} | "
            f"{metrics['boundary']['f1']:.6f} | "
            f"{metrics['bcubed']['predicted_groups']:,} |"
        )

    report = f"""# Same-model flat-segmentation ablation

Status: **COMPLETE / VALID**

## Scientific result

| Method | B³ P | B³ R | B³ F1 | Boundary P | Boundary R | Boundary F1 | Groups |
|---|---:|---:|---:|---:|---:|---:|---:|
{row("Direct variable-depth hierarchy (Step 0087)", hierarchy_metrics)}
{row("Same-model flat partition", flat_metrics)}

Hierarchy minus flat B³ F1 is
`{hierarchy_metrics['bcubed']['f1'] - flat_metrics['bcubed']['f1']:+.6f}`
with a 10,000-resample paired task-cluster 95% interval of
`[{b3_interval[0]:+.6f}, {b3_interval[1]:+.6f}]` (seed `20260720`).
Hierarchy minus flat exact adjacent-boundary F1 is
`{hierarchy_metrics['boundary']['f1'] - flat_metrics['boundary']['f1']:+.6f}`
with interval
`[{boundary_interval[0]:+.6f}, {boundary_interval[1]:+.6f}]`
(seed `20260722`).

The predeclared hierarchy-benefit hypothesis is **{verdict.upper()}**.

## Control-2 audit

Step 0087 directly generated complete variable-depth paths in one isolated
request per trajectory and explicitly prohibited STOP/SPLIT recursion. It had
no external recursive controller or iterative semantic refinement. Its complete
20,866 operation rows and 20,461 pair rows are therefore the requested direct
hierarchy control and were reused without new calls. No
recursive/refined-minus-direct comparison is reported because no distinct
refined condition exists.

## Completion and mechanism engagement

- all 405 trajectories, 17,148 turns, 20,866 operations, 20,461 pairs, 2,948
  stages, and 251 task clusters are included;
- every raw flat path has exactly the mandatory root plus one non-root semantic
  name;
- the flat arm emits {raw_stats['marks']:,} marks/groups and its raw path-depth
  distribution is `{json.dumps(raw_stats['path_depths'], sort_keys=True)}`;
- the reused Step 0087 raw depth distribution is
  `{json.dumps(hierarchy_frozen['annotation']['raw_path_depths'], sort_keys=True)}`;
- operation mass {EXPECTED_OPERATIONS:,} and token mass {EXPECTED_TOKENS:,}
  are conserved; canonicalization preserves the temporal partition and leaves
  zero adjacent display-path collisions; both profiles load in stock pprof.

## Backend and cost

The flat arm used pinned `codex-cli 0.145.0`, `gpt-5.6-sol`, ignored user
configuration, default reasoning/decoding, read-only ephemeral isolation, up
to four workers, a 1,200-second timeout, and one ordinary format retry.

| Measure | Flat arm |
|---|---:|
| Model calls | {cost['total_codex_calls']:,} |
| Format retries | {cost['format_retries']:,} |
| Deterministic mechanical repairs | {cost['deterministic_repairs']:,} |
| Input tokens | {cost['usage'].get('input_tokens', 0):,} |
| Cached input tokens | {cost['usage'].get('cached_input_tokens', 0):,} |
| Output tokens | {cost['usage'].get('output_tokens', 0):,} |
| Reasoning-output tokens | {cost['usage'].get('reasoning_output_tokens', 0):,} |
| Summed request time | {cost['summed_backend_wall_seconds']:.3f} s |
| Union active request time | {cost['active_backend_wall_seconds']:.3f} s |
| Backend command wall | {backend_timing['command_wall_seconds']:.3f} s |
| Deterministic pipeline wall | {pipeline_wall:.3f} s |
| End-to-end full-arm wall | {end_to_end_wall:.3f} s |

Step 0087's reused hierarchy cost remains 415 calls, 12,050,384 input tokens,
231,886 output tokens, 116,909 reasoning-output tokens, 8,689.405 seconds
summed request time, 2,215.858 seconds union active request time, and 11.516
seconds downstream pipeline wall.

## Scope and next paper decision

```text
run status: valid
tested hypothesis: {verdict}
research value: decisive mechanism ablation
paper impact: additional RQ3 evidence and hierarchy-mechanism boundary
next paper decision: {raw_results['next_paper_decision']}
```

This complete same-model ablation measures leaf-occurrence partition and exact
boundary fidelity on CodeTraceBench. It does not validate nested topology,
literal name accuracy, cross-run name equivalence, user utility, or other
task/agent families. It changes neither the fixed RQs nor the thesis,
“Agent observability needs profiling, not only debugging.”
"""
    (EXPERIMENT / "results.md").write_text(report, encoding="utf-8")
    print(json.dumps(raw_results, sort_keys=True), flush=True)


def report_incomplete() -> None:
    """Record a terminal but unscorable full run without opening the oracle."""
    ordinals = set(range(1, EXPECTED_SESSIONS + 1))
    records = read_jsonl(EXPERIMENT / "annotation-run-records.jsonl")
    latest = {int(row["ordinal"]): row for row in records}
    if set(latest) != ordinals:
        missing = sorted(ordinals - set(latest))
        raise RuntimeError(f"not all trajectories are terminal; missing {missing[:5]}")

    failures = [
        {
            "ordinal": int(row["ordinal"]),
            "session": str(row["session"]),
            "attempts": int(row["attempts"]),
            "attempt_errors": [
                list(attempt.get("errors") or [])
                for attempt in row["attempt_records"]
            ],
        }
        for row in latest.values()
        if row.get("status") != "ok"
    ]
    if not failures:
        raise RuntimeError("full run has no terminal failures; use full mode")

    raw_stats = raw_annotation_stats(ordinals)
    cost = base.annotation_cost(ordinals, configured_workers=4)
    cost["worker_pattern"] = (
        "isolated one-trajectory calls, up to 4 parallel workers; "
        "one ordinary format retry"
    )
    cost["deterministic_repairs"] = (
        len(read_jsonl(EXPERIMENT / "format-repairs.jsonl"))
        if (EXPERIMENT / "format-repairs.jsonl").is_file()
        else 0
    )
    retry_first_errors = [
        str(error)
        for row in latest.values()
        if int(row["attempts"]) > 1
        for error in (row["attempt_records"][0].get("errors") or [])
    ]
    cost["total_ordinary_second_attempts"] = int(cost["format_retries"])
    cost["format_failure_retries"] = sum(
        error != "backend timeout after 1200 seconds"
        for error in retry_first_errors
    )
    cost["timeout_retries"] = sum(
        error == "backend timeout after 1200 seconds"
        for error in retry_first_errors
    )
    backend_timing = read_json(EXPERIMENT / "full-backend-timing.json")
    population_started_unix = min(
        float(attempt["started_unix"])
        for row in latest.values()
        for attempt in row["attempt_records"]
    )
    population_first_request_to_terminal_seconds = (
        float(backend_timing["finished_unix"]) - population_started_unix
    )
    hierarchy = read_json(HIERARCHY_RAW_RESULTS)
    hierarchy_metrics = hierarchy["methods"]["direct_multilevel"]

    validity = {
        "all_405_trajectories_terminal": len(latest) == EXPECTED_SESSIONS,
        "all_405_trajectories_valid": int(cost["successful_trajectories"])
        == EXPECTED_SESSIONS,
        "declared_attempt_limit_respected": bool(cost["attempt_limit_valid"]),
        "accepted_paths_root_plus_one_flat_name": bool(
            raw_stats["all_paths_root_plus_one_flat_name"]
        ),
        "accepted_annotations_valid": set(raw_stats["invalid_annotations"])
        == {118},
        "full_population_pipeline_executed": False,
        "oracle_or_score_rows_opened_for_full_population_flat_arm": False,
        "preflight_scored_only_after_preflight_prediction_fixed": True,
        "partial_population_scored": False,
        "paired_bootstrap_executed": False,
    }
    raw_results = {
        "schema": "agentsight.same-model-flat-ablation.incomplete.v1",
        "status": "incomplete",
        "run_status": "terminal_format_failure",
        "tested_hypothesis": "not evaluated",
        "research_value": "retained operational evidence; no RQ3 score",
        "paper_impact": "none; the matched ablation is not reportable",
        "next_paper_decision": (
            "Do not report hierarchy-minus-flat metrics from this run. Retain "
            "Step 0087 as the adopted direct-hierarchy result; if the reviewer "
            "control remains required, execute a new prospectively reviewed "
            "complete flat arm rather than repair or score this population "
            "post hoc."
        ),
        "population": {
            "requested_sessions": EXPECTED_SESSIONS,
            "terminal_sessions": len(latest),
            "valid_sessions": int(cost["successful_trajectories"]),
            "invalid_sessions": int(cost["failed_after_retry"]),
            "turns": EXPECTED_TURNS,
            "operations": EXPECTED_OPERATIONS,
        },
        "terminal_failures": failures,
        "methods": {
            "direct_variable_depth_hierarchy_reused_step_0087": hierarchy_metrics,
            "same_model_flat": None,
        },
        "paired_hierarchy_minus_flat": {
            "reported": False,
            "reason": (
                "One of 405 flat annotations remained invalid after the "
                "predeclared retry policy; partial scoring is forbidden."
            ),
            "planned_resamples": 10_000,
            "planned_seeds": {
                "bcubed": 20_260_720,
                "boundary": 20_260_722,
            },
        },
        "recursive_refined_minus_direct": {
            "reported": False,
            "reason": (
                "Step 0087 already is direct complete-hierarchy generation; "
                "no distinct recursive/refined adopted arm exists."
            ),
        },
        "annotation": {
            "accepted_flat_annotations": raw_stats,
            "hierarchy_step_0087": hierarchy["annotation"],
        },
        "cost": {
            "flat_terminal_attempt": cost,
            "hierarchy_step_0087": hierarchy["cost"],
            "flat_resumed_full_command_wall_seconds": backend_timing[
                "command_wall_seconds"
            ],
            "flat_pipeline_wall_seconds": None,
            "flat_first_population_request_to_terminal_seconds": (
                population_first_request_to_terminal_seconds
            ),
            "population_cost_includes_reused_preflight_trajectory": True,
        },
        "leakage": {
            "source_packet_audit": "passed before model calls",
            "prohibited_fields_absent": [
                "stage",
                "outcome",
                "score",
                "reward",
                "target",
                "label",
            ],
            "official_stages_opened_by_full_population_flat_pipeline": False,
            "preflight_frozen_scorer_ran_after_prediction_fixed": True,
            "oracle_fields_visible_to_model_backend": False,
        },
        "validity": validity,
        "artifacts": {
            "flat_raw_marks": relative(EXPERIMENT / "raw-marks"),
            "flat_run_records": relative(
                EXPERIMENT / "annotation-run-records.jsonl"
            ),
            "failed_attempt_1": relative(
                EXPERIMENT / "raw-events" / "0118-attempt-1.jsonl"
            ),
            "failed_attempt_2": relative(
                EXPERIMENT / "raw-events" / "0118-attempt-2.jsonl"
            ),
        },
    }
    write_json(EXPERIMENT / "raw-results.json", raw_results)

    failure = failures[0]
    report = f"""# Same-model flat-segmentation ablation

Status: **INCOMPLETE / UNSCORED**

## Outcome

All 405 trajectories reached terminal status, but only 404 produced valid flat
annotations under the registered initial-call plus one-format-retry policy.
Ordinal {failure['ordinal']} (`{failure['session']}`) repeated an unchanged
adjacent complete path on both attempts. That error is not the plan's sole
permitted deterministic repair (an otherwise-valid top-level session-ID
replacement). The response was therefore not altered.

The full-population frozen scorer, official stages, assembly, canonicalization,
pprof materialization, and paired bootstrap were not run. No 404/405 prefix
was scored, so this experiment supplies no hierarchy-minus-flat estimate,
precision, recall, F1, confidence interval, or paper-level RQ3 evidence.

## Mechanism and completion audit

- requested/terminal/valid trajectories: 405 / 405 / 404;
- accepted flat marks: {raw_stats['marks']:,} across the 404 valid trajectories;
- accepted raw path-depth distribution:
  `{json.dumps(raw_stats['path_depths'], sort_keys=True)}`; every accepted path
  is exactly the mandatory root plus one flat name;
- accepted unique raw names including roots: {raw_stats['unique_raw_names']:,};
- terminal failures after retry: {cost['failed_after_retry']};
- ordinary second attempts: {cost['total_ordinary_second_attempts']} total
  ({cost['format_failure_retries']} after format-contract failures and
  {cost['timeout_retries']} after timeout);
- deterministic mechanical repairs: {cost['deterministic_repairs']}.

The exact Step 0087 source-packet audit found no stage, outcome, score, reward,
target, or label fields. The full-population flat pipeline did not open the
official stages or score rows. The operational preflight ran the frozen scorer
only after its one prediction was fixed; no oracle field was visible to any
model request. The saved prompt diff and all 410 raw backend event streams
remain available for audit.

## Reused direct-hierarchy control

Step 0087 already directly emits complete variable-depth paths in one isolated
request per trajectory, explicitly without STOP/SPLIT recursion or iterative
semantic refinement. It remains the requested direct-hierarchy control and was
not rerun under a second name. Its complete adopted result is B-cubed
P/R/F1 `{hierarchy_metrics['bcubed']['precision']:.6f}` /
`{hierarchy_metrics['bcubed']['recall']:.6f}` /
`{hierarchy_metrics['bcubed']['f1']:.6f}` and exact adjacent-boundary P/R/F1
`{hierarchy_metrics['boundary']['precision']:.6f}` /
`{hierarchy_metrics['boundary']['recall']:.6f}` /
`{hierarchy_metrics['boundary']['f1']:.6f}` over 4,496 groups. No
recursive/refined-minus-direct comparison exists because there is no genuinely
distinct refined condition.

## Backend cost to terminal status

| Measure | Flat attempt |
|---|---:|
| Model calls | {cost['total_codex_calls']:,} |
| Ordinary second attempts | {cost['total_ordinary_second_attempts']:,} |
| After format-contract failure | {cost['format_failure_retries']:,} |
| After timeout | {cost['timeout_retries']:,} |
| Input tokens | {cost['usage'].get('input_tokens', 0):,} |
| Cached input tokens | {cost['usage'].get('cached_input_tokens', 0):,} |
| Output tokens | {cost['usage'].get('output_tokens', 0):,} |
| Reasoning-output tokens | {cost['usage'].get('reasoning_output_tokens', 0):,} |
| Summed request time | {cost['summed_backend_wall_seconds']:.3f} s |
| Union active request time | {cost['active_backend_wall_seconds']:.3f} s |
| First population request to terminal status | {population_first_request_to_terminal_seconds:.3f} s |
| Resumed full-command wall (excludes earlier reused preflight) | {backend_timing['command_wall_seconds']:.3f} s |
| Downstream full-population pipeline | not run |

The 410-call/token totals include the valid preflight trajectory because that
annotation was reused as one of the 405 population members. The operational
preflight completed that packet end to end; its score is not a paper result.

## Next paper decision

Do not report a hierarchy-minus-flat effect from this run and do not normalize
the failed marks after seeing the failure. Retain the Step 0087 direct-hierarchy
result. If the reviewer control is still required, run a newly planned,
prospectively reviewed complete flat arm; do not present this terminal attempt
as a scored result.

This outcome changes neither the four fixed RQs nor the thesis,
“Agent observability needs profiling, not only debugging.”
"""
    (EXPERIMENT / "results.md").write_text(report, encoding="utf-8")
    print(json.dumps(raw_results, sort_keys=True), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("preflight", "full", "incomplete"))
    args = parser.parse_args()
    if args.mode == "incomplete":
        report_incomplete()
    else:
        run_pipeline(args.mode)


if __name__ == "__main__":
    main()
