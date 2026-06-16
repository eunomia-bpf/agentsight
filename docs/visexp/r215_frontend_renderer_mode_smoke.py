#!/usr/bin/env python3
"""R215: frontend renderer-model smoke for AgentFlame display modes.

This run exercises the TypeScript display-mode model used by the frontend. It
does not read raw agent traces, call an LLM, or update the canonical map. The
oracle compiles the frontend module, runs it under Node over the generated R209
display-map artifacts, and checks negative fixtures that should fail if raw
drilldown or pending membership is wired incorrectly.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
FRONTEND_DIR = REPO_ROOT / "frontend"
FRONTEND_MODULE = FRONTEND_DIR / "src" / "utils" / "agentflameDisplayModes.ts"
DEFAULT_R209_DIR = SCRIPT_DIR / "out" / "reversible-display-map-r209"
DEFAULT_R213_DIR = SCRIPT_DIR / "out" / "display-mode-drilldown-r213"
DEFAULT_R214_DIR = SCRIPT_DIR / "out" / "long-tail-control-r214"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out" / "frontend-renderer-mode-r215"

MODE_FIELDS = [
    "mode",
    "bucket_count",
    "total_support",
    "candidate_overlay_rows",
    "review_required_rows",
    "review_required_support",
    "active_merge_rows",
    "hidden_other_rows",
    "top_bucket",
    "top_bucket_support",
    "top_bucket_raw_tags",
]

SAMPLE_FIELDS = [
    "mode",
    "rank",
    "dimension",
    "display_tag",
    "support",
    "raw_tag_count",
    "candidate_rows",
    "review_required_rows",
    "has_pending_overlay",
    "raw_tags",
]

NEGATIVE_FIELDS = [
    "case",
    "expected",
    "observed",
    "passed",
    "reason",
]


HARNESS_TS = r"""
import * as fs from 'fs';
import {
  drilldownMembershipMatchesDisplayMap,
  renderAgentFlameModes,
} from './agentflameDisplayModes';

const fixturePath = process.argv[2];
const resultPath = process.argv[3];
if (!fixturePath || !resultPath) {
  throw new Error('usage: node r215_harness.js <fixture.json> <result.json>');
}

const payload = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));
const displayRows = payload.displayRows;
const drilldownRows = payload.drilldownRows;

function bucketSignature(result: any): string {
  return result.buckets
    .map((bucket: any) => [
      bucket.dimension,
      bucket.displayTag,
      bucket.rawTags.map((raw: any) => `${raw.tag}=${raw.support}`).sort().join(';'),
    ].join('\u0001'))
    .sort()
    .join('\u0002');
}

function summarizeMode(result: any) {
  const top = result.buckets[0] ?? null;
  return {
    mode: result.mode,
    bucketCount: result.bucketCount,
    totalSupport: result.totalSupport,
    candidateOverlayRows: result.candidateOverlayRows,
    reviewRequiredRows: result.reviewRequiredRows,
    reviewRequiredSupport: result.reviewRequiredSupport,
    activeMergeRows: result.activeMergeRows,
    hiddenOtherRows: result.hiddenOtherRows,
    topBucket: top ? {
      dimension: top.dimension,
      displayTag: top.displayTag,
      support: top.support,
      rawTagCount: top.rawTagCount,
    } : null,
  };
}

function sampleBuckets(result: any) {
  return result.buckets.slice(0, 12).map((bucket: any, index: number) => ({
    mode: result.mode,
    rank: index + 1,
    dimension: bucket.dimension,
    displayTag: bucket.displayTag,
    support: bucket.support,
    rawTagCount: bucket.rawTagCount,
    candidateRows: bucket.candidateRows,
    reviewRequiredRows: bucket.reviewRequiredRows,
    hasPendingOverlay: bucket.hasPendingOverlay,
    rawTags: bucket.rawTags.map((raw: any) => `${raw.tag}=${raw.support}`).join('; '),
  }));
}

function corruptFirstDrilldownRawTag(rows: any[]) {
  const next = rows.map(row => ({ ...row }));
  const index = next.findIndex(row => typeof row.raw_tags === 'string' && row.raw_tags.includes('='));
  if (index < 0) throw new Error('fixture has no drilldown row to corrupt');
  next[index].raw_tags = next[index].raw_tags.replace(/^[^=;]+=/, '__wrong__=');
  return next;
}

function promoteCandidatesAsActive(rows: any[]) {
  return rows.map(row => {
    if (!row.candidate_display_tag) return { ...row };
    return { ...row, active_display_tag: row.candidate_display_tag };
  });
}

const modes = renderAgentFlameModes(displayRows, drilldownRows);
const membershipMatches = drilldownMembershipMatchesDisplayMap(displayRows, drilldownRows);
const pendingMembershipEqualsDisplay =
  bucketSignature(modes.pending) === bucketSignature(modes.display);

const wrongDrilldownRejected =
  !drilldownMembershipMatchesDisplayMap(displayRows, corruptFirstDrilldownRawTag(drilldownRows));
const candidatePromotionRejected =
  !drilldownMembershipMatchesDisplayMap(promoteCandidatesAsActive(displayRows), drilldownRows);

const result = {
  membershipMatches,
  pendingMembershipEqualsDisplay,
  wrongDrilldownRejected,
  candidatePromotionRejected,
  modes: {
    raw: summarizeMode(modes.raw),
    display: summarizeMode(modes.display),
    pending: summarizeMode(modes.pending),
  },
  samples: [
    ...sampleBuckets(modes.raw),
    ...sampleBuckets(modes.display),
    ...sampleBuckets(modes.pending),
  ],
};

fs.writeFileSync(resultPath, JSON.stringify(result, null, 2) + '\n', 'utf8');
"""


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def as_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(str(value)))


def mode_rows(harness: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for mode in ["raw", "display", "pending"]:
        data = harness["modes"][mode]
        top = data.get("topBucket") or {}
        sample = next((row for row in harness["samples"] if row["mode"] == mode and row["rank"] == 1), {})
        rows.append(
            {
                "mode": mode,
                "bucket_count": data["bucketCount"],
                "total_support": data["totalSupport"],
                "candidate_overlay_rows": data["candidateOverlayRows"],
                "review_required_rows": data["reviewRequiredRows"],
                "review_required_support": data["reviewRequiredSupport"],
                "active_merge_rows": data["activeMergeRows"],
                "hidden_other_rows": data["hiddenOtherRows"],
                "top_bucket": f"{top.get('dimension', '')}:{top.get('displayTag', '')}",
                "top_bucket_support": top.get("support", 0),
                "top_bucket_raw_tags": sample.get("rawTags", ""),
            }
        )
    return rows


def sample_rows(harness: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "mode": row["mode"],
            "rank": row["rank"],
            "dimension": row["dimension"],
            "display_tag": row["displayTag"],
            "support": row["support"],
            "raw_tag_count": row["rawTagCount"],
            "candidate_rows": row["candidateRows"],
            "review_required_rows": row["reviewRequiredRows"],
            "has_pending_overlay": row["hasPendingOverlay"],
            "raw_tags": row["rawTags"],
        }
        for row in harness["samples"]
    ]


def negative_rows(harness: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "case": "wrong_drilldown_raw_membership",
            "expected": "rejected",
            "observed": "rejected" if harness["wrongDrilldownRejected"] else "accepted",
            "passed": bool(harness["wrongDrilldownRejected"]),
            "reason": "raw_tags list must match active display-map membership",
        },
        {
            "case": "candidate_display_tag_used_as_active_membership",
            "expected": "rejected",
            "observed": "rejected" if harness["candidatePromotionRejected"] else "accepted",
            "passed": bool(harness["candidatePromotionRejected"]),
            "reason": "pending candidates must not change active display membership",
        },
    ]


def run_ts_harness(
    display_rows: list[dict[str, str]],
    drilldown_rows: list[dict[str, str]],
    module_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    tsc = FRONTEND_DIR / "node_modules" / ".bin" / "tsc"
    if not tsc.exists():
        raise FileNotFoundError(f"missing TypeScript compiler: {rel(tsc)}")
    with tempfile.TemporaryDirectory(prefix="agentsight-r215-") as tmp_text:
        tmp = Path(tmp_text)
        src = tmp / "src"
        build = tmp / "build"
        src.mkdir()
        build.mkdir()
        shutil.copyfile(module_path, src / "agentflameDisplayModes.ts")
        (src / "r215_harness.ts").write_text(HARNESS_TS, encoding="utf-8")
        fixture = tmp / "fixture.json"
        result = tmp / "result.json"
        write_json(fixture, {"displayRows": display_rows, "drilldownRows": drilldown_rows})

        tsc_cmd = [
            str(tsc),
            "--target",
            "ES2020",
            "--module",
            "commonjs",
            "--strict",
            "--esModuleInterop",
            "--skipLibCheck",
            "--types",
            "node",
            "--typeRoots",
            str(FRONTEND_DIR / "node_modules" / "@types"),
            "--outDir",
            str(build),
            str(src / "agentflameDisplayModes.ts"),
            str(src / "r215_harness.ts"),
        ]
        start = time.monotonic()
        tsc_run = subprocess.run(
            tsc_cmd,
            cwd=FRONTEND_DIR,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        tsc_ms = round((time.monotonic() - start) * 1000.0, 3)
        if tsc_run.returncode != 0:
            raise RuntimeError(f"R215 tsc failed:\n{tsc_run.stdout}")

        node_cmd = ["node", str(build / "r215_harness.js"), str(fixture), str(result)]
        start = time.monotonic()
        node_run = subprocess.run(
            node_cmd,
            cwd=FRONTEND_DIR,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        node_ms = round((time.monotonic() - start) * 1000.0, 3)
        if node_run.returncode != 0:
            raise RuntimeError(f"R215 node harness failed:\n{node_run.stdout}")

        return read_json(result), {
            "tsc_ms": tsc_ms,
            "node_ms": node_ms,
            "tsc_command": " ".join(tsc_cmd),
            "node_command": "node <compiled r215_harness.js> <fixture.json> <result.json>",
            "tsc_stdout": tsc_run.stdout.strip(),
            "node_stdout": node_run.stdout.strip(),
        }


def summarize(
    harness: dict[str, Any],
    r213: dict[str, Any],
    r214: dict[str, Any],
    compile_info: dict[str, Any],
) -> dict[str, Any]:
    modes = harness["modes"]
    pending = modes["pending"]
    display = modes["display"]
    raw = modes["raw"]
    return {
        "compiled_frontend_module": True,
        "node_harness_executed": True,
        "frontend_dom_renderer_exercised": False,
        "total_support": raw["totalSupport"],
        "raw_bucket_count": raw["bucketCount"],
        "display_bucket_count": display["bucketCount"],
        "pending_bucket_count": pending["bucketCount"],
        "candidate_overlay_rows": pending["candidateOverlayRows"],
        "review_required_rows": pending["reviewRequiredRows"],
        "review_required_support": pending["reviewRequiredSupport"],
        "active_merge_rows": display["activeMergeRows"],
        "hidden_other_rows": max(
            as_int(raw["hiddenOtherRows"]),
            as_int(display["hiddenOtherRows"]),
            as_int(pending["hiddenOtherRows"]),
        ),
        "membership_matches_display_map": bool(harness["membershipMatches"]),
        "pending_membership_equals_display": bool(harness["pendingMembershipEqualsDisplay"]),
        "wrong_drilldown_rejected": bool(harness["wrongDrilldownRejected"]),
        "candidate_promotion_rejected": bool(harness["candidatePromotionRejected"]),
        "r213_display_bucket_count": (r213.get("summary") or {}).get("display_bucket_count"),
        "r214_pending_candidate_rows": (r214.get("summary") or {}).get("pending_candidate_rows"),
        "tsc_ms": compile_info["tsc_ms"],
        "node_ms": compile_info["node_ms"],
    }


def write_markdown(path: Path, payload: dict[str, Any], modes: list[dict[str, Any]], negatives: list[dict[str, Any]]) -> None:
    summary = payload["summary"]
    lines = [
        "# R215 Frontend Renderer-Mode Smoke",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Boundary",
        "",
        "- Compiles and runs `frontend/src/utils/agentflameDisplayModes.ts` under Node.",
        "- Renders R209 display-map/drilldown rows and cross-checks R213/R214 summaries.",
        "- Does not read or mutate raw Codex/Claude traces.",
        "- Does not call an LLM or update the canonical display map.",
        "- Does not exercise a browser DOM or visual click path.",
        "",
        "## Mode Summary",
        "",
        "| mode | buckets | support | candidates | review rows | review support | active merges | hidden other |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in modes:
        lines.append(
            f"| `{row['mode']}` | {row['bucket_count']} | {row['total_support']} | "
            f"{row['candidate_overlay_rows']} | {row['review_required_rows']} | "
            f"{row['review_required_support']} | {row['active_merge_rows']} | {row['hidden_other_rows']} |"
        )
    lines.extend(
        [
            "",
            "## Negative Fixtures",
            "",
            "| case | observed | pass | reason |",
            "|---|---|---|---|",
        ]
    )
    for row in negatives:
        lines.append(
            f"| `{row['case']}` | {row['observed']} | {row['passed']} | {row['reason']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "R215 supports a frontend renderer-model smoke: the TypeScript display-mode "
            "consumer compiles, preserves R209 support and membership, keeps pending "
            "candidates from changing display membership, and rejects corrupted "
            "drilldown membership. It does not support semantic adequacy, merge "
            "quality, developer utility, or a browser/DOM renderer claim.",
            "",
            f"TypeScript compile time: `{summary['tsc_ms']}` ms. Node harness time: `{summary['node_ms']}` ms.",
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
    r213_json = args.r213_dir / "display-mode-drilldown-r213.json"
    r214_json = args.r214_dir / "long-tail-control-r214.json"
    for path in [r209_json, display_csv, drilldown_csv, r213_json, r214_json, FRONTEND_MODULE]:
        if not path.exists():
            raise FileNotFoundError(f"missing R215 input artifact: {rel(path)}")

    r209 = read_json(r209_json)
    r213 = read_json(r213_json)
    r214 = read_json(r214_json)
    display_rows = read_csv(display_csv)
    drilldown_rows = read_csv(drilldown_csv)
    harness, compile_info = run_ts_harness(display_rows, drilldown_rows, FRONTEND_MODULE)
    modes = mode_rows(harness)
    samples = sample_rows(harness)
    negatives = negative_rows(harness)
    summary = summarize(harness, r213, r214, compile_info)
    r209_summary = r209.get("summary") or {}
    status = "frontend_renderer_mode_smoke_ready_no_quality_claims"

    payload = {
        "run_id": "R215",
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "claim": "C3 frontend display-mode consumer; C6 protocol/gate only",
        "claim_boundary": (
            "R215 compiles and runs the frontend TypeScript display-mode consumer over "
            "generated R209 artifacts. It is a renderer-model integration smoke, not "
            "a browser DOM, semantic adequacy, merge-quality, or developer-utility result."
        ),
        "input": {
            "r209_json": rel(r209_json),
            "r209_json_sha256": sha256_file(r209_json),
            "display_csv": rel(display_csv),
            "display_csv_sha256": sha256_file(display_csv),
            "drilldown_csv": rel(drilldown_csv),
            "drilldown_csv_sha256": sha256_file(drilldown_csv),
            "r213_json": rel(r213_json),
            "r213_json_sha256": sha256_file(r213_json),
            "r214_json": rel(r214_json),
            "r214_json_sha256": sha256_file(r214_json),
            "frontend_module": rel(FRONTEND_MODULE),
            "frontend_module_sha256": sha256_file(FRONTEND_MODULE),
        },
        "method": {
            "frontend_module": rel(FRONTEND_MODULE),
            "compile": "TypeScript module compiled with frontend node_modules/.bin/tsc",
            "execute": "compiled Node harness renders raw/display/pending modes from R209 rows",
            "negative_fixtures": [
                "corrupt one drilldown raw_tags entry while preserving support/count shape",
                "promote candidate_display_tag as active_display_tag before review",
            ],
            "quality_boundary": "renderer-model mechanics only; no DOM/browser, adequacy, quality, or utility claim",
            "compile_info": compile_info,
        },
        "summary": summary,
        "claim_gate": {
            "frontend_renderer_model_smoke_supported": bool(
                summary["compiled_frontend_module"]
                and summary["node_harness_executed"]
                and summary["membership_matches_display_map"]
                and summary["pending_membership_equals_display"]
                and summary["wrong_drilldown_rejected"]
                and summary["candidate_promotion_rejected"]
                and summary["total_support"] == r209_summary.get("total_support")
            ),
            "support_preserved": summary["total_support"] == r209_summary.get("total_support"),
            "pending_membership_unchanged": bool(summary["pending_membership_equals_display"]),
            "negative_fixtures_rejected": bool(
                summary["wrong_drilldown_rejected"] and summary["candidate_promotion_rejected"]
            ),
            "reads_generated_artifacts_only": True,
            "raw_trace_read": False,
            "llm_called": False,
            "canonical_map_updated": False,
            "frontend_dom_renderer_supported": False,
            "semantic_adequacy_supported": False,
            "canonicalization_quality_supported": False,
            "developer_utility_supported": False,
            "community_adoption_supported": False,
        },
        "outputs": {
            "summary_json": rel(args.out_dir / "frontend-renderer-mode-r215.json"),
            "summary_md": rel(args.out_dir / "frontend-renderer-mode-r215.md"),
            "mode_summary_csv": rel(args.out_dir / "mode-summary-r215.csv"),
            "sample_buckets_csv": rel(args.out_dir / "sample-buckets-r215.csv"),
            "negative_fixtures_csv": rel(args.out_dir / "negative-fixtures-r215.csv"),
        },
        "provenance": {
            "repo_commit": git(["rev-parse", "HEAD"]),
            "repo_dirty": bool(git(["status", "--short"])),
            "script_sha256": sha256_file(Path(__file__).resolve()),
        },
    }
    return payload, modes, samples, negatives


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r209-dir", type=Path, default=DEFAULT_R209_DIR)
    parser.add_argument("--r213-dir", type=Path, default=DEFAULT_R213_DIR)
    parser.add_argument("--r214-dir", type=Path, default=DEFAULT_R214_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload, modes, samples, negatives = build_payload(args)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "frontend-renderer-mode-r215.json", payload)
    write_markdown(args.out_dir / "frontend-renderer-mode-r215.md", payload, modes, negatives)
    write_csv(args.out_dir / "mode-summary-r215.csv", modes, MODE_FIELDS)
    write_csv(args.out_dir / "sample-buckets-r215.csv", samples, SAMPLE_FIELDS)
    write_csv(args.out_dir / "negative-fixtures-r215.csv", negatives, NEGATIVE_FIELDS)
    print(json.dumps({"status": payload["status"], "summary_json": payload["outputs"]["summary_json"]}))


if __name__ == "__main__":
    main()
