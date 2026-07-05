#!/usr/bin/env python3
"""R327: profile-spec cost and reproducibility probe.

This experiment complements the R320-R326 accuracy/actionability results.  It
does not download data or create a new workload.  It reuses tracked operation
profile specifications, runs the Rust profiler repeatedly against each spec,
and records runtime, output size, unique-stack count, and output hashes.

The claim is deliberately scoped: this is offline profile-spec execution cost
and determinism for existing operation JSONL inputs, not live eBPF overhead,
human productivity, or trace-ecosystem compatibility.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import subprocess
import tempfile
import time
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "docs" / "visexp" / "out"
DEFAULT_OUT_DIR = OUT_ROOT / "operation-profile-cost-r327"
DEFAULT_BINARY = ROOT / "agentpprof" / "target" / "debug" / "agentpprof"
SPEC_GROUPS = [
    ("r300_views", OUT_ROOT / "operation-query-utility-r300"),
    ("r324_rank_features", OUT_ROOT / "operation-rank-feature-r324"),
    ("r326_rank_feature_robustness", OUT_ROOT / "operation-rank-feature-robustness-r326"),
]
FORMAT_EXTENSIONS = {
    "json": ".json",
    "folded": ".folded",
    "pprof": ".pb.gz",
    "pb": ".pb.gz",
    "pb.gz": ".pb.gz",
    "svg": ".svg",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--reps", type=int, default=2)
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Do not build agentpprof if the configured binary is missing.",
    )
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise SystemExit(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def git_check(description: str, args: list[str], path: Path) -> None:
    result = subprocess.run(
        ["git", *args, "--", rel(path)],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        suffix = f": {detail}" if detail else ""
        raise SystemExit(f"{rel(path)} failed source check: {description}{suffix}")


def ensure_sources_tracked_clean(paths: list[Path]) -> dict[str, Any]:
    checked = []
    for path in sorted({item.resolve() for item in paths}):
        if not path.exists():
            raise SystemExit(f"missing source artifact {rel(path)}")
        git_check("source artifact is not git-tracked", ["ls-files", "--error-unmatch"], path)
        git_check("source artifact has unstaged changes", ["diff", "--quiet"], path)
        git_check("source artifact has staged changes", ["diff", "--cached", "--quiet"], path)
        checked.append(rel(path))
    return {
        "status": "pass",
        "tracked_clean_files": len(checked),
        "files": checked,
    }


def ensure_agentpprof_binary(binary: Path, skip_build: bool) -> dict[str, Any]:
    if skip_build:
        if not binary.exists():
            raise SystemExit(f"missing agentpprof binary: {rel(binary)}")
        return {
            "status": "present",
            "binary": rel(binary),
            "sha256": file_sha256(binary),
            "build_excluded_from_timings": True,
        }
    started = time.perf_counter()
    result = subprocess.run(
        ["cargo", "build", "--manifest-path", "agentpprof/Cargo.toml"],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    elapsed = time.perf_counter() - started
    if result.returncode != 0:
        raise SystemExit(f"cargo build failed:\n{result.stderr.strip()}")
    if not binary.exists():
        raise SystemExit(f"cargo build completed but binary is missing: {rel(binary)}")
    return {
        "status": "built",
        "binary": rel(binary),
        "sha256": file_sha256(binary),
        "elapsed_s": round(elapsed, 3),
        "build_excluded_from_timings": True,
    }


def discover_specs() -> list[dict[str, Any]]:
    specs = []
    for experiment, directory in SPEC_GROUPS:
        for spec_path in sorted(directory.glob("*profile-spec.json")):
            specs.append({"experiment": experiment, "path": spec_path})
    if not specs:
        raise SystemExit("no profile specs found for R327")
    return specs


def resolve_spec_path(base: Path, raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else base / path


def normalized_format(spec: dict[str, Any]) -> str:
    value = str(spec.get("format") or "").strip().lower().replace("_", "-")
    if value in {"foldedtxt", "folded-txt"}:
        return "folded"
    if value in {"pb", "pb-gz", "pb.gz", "pprof"}:
        return "pprof"
    if value in {"json", "folded", "svg"}:
        return value
    output = str(spec.get("output") or "")
    suffixes = "".join(Path(output).suffixes)
    if suffixes.endswith(".pb.gz"):
        return "pprof"
    if output.endswith(".folded"):
        return "folded"
    if output.endswith(".svg"):
        return "svg"
    return "json"


def stack_depth(spec: dict[str, Any]) -> int:
    stack = spec.get("stack")
    if isinstance(stack, str):
        return len([part for part in stack.split(",") if part.strip()])
    if isinstance(stack, list):
        return len(stack)
    return 0


def list_count(spec: dict[str, Any], key: str) -> int:
    value = spec.get(key) or []
    return len(value) if isinstance(value, list) else 1


def operation_rows(path: Path) -> int:
    rows = 0
    with path.open(encoding="utf-8") as file:
        for line in file:
            if line.strip():
                rows += 1
    return rows


def p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(0.95 * len(ordered)) - 1))
    return ordered[index]


def rounded(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value):
            return None
        if math.isinf(value):
            return "inf"
        return round(value, 4)
    if isinstance(value, dict):
        return {key: rounded(child) for key, child in value.items()}
    if isinstance(value, list):
        return [rounded(child) for child in value]
    return value


def output_extension(fmt: str) -> str:
    return FORMAT_EXTENSIONS.get(fmt, f".{fmt}")


def read_output_stats(path: Path, fmt: str) -> dict[str, Any]:
    data = path.read_bytes()
    stats = {
        "output_bytes": len(data),
        "raw_sha256": hashlib.sha256(data).hexdigest(),
    }
    if fmt == "json":
        payload = json.loads(data.decode("utf-8"))
        semantic_payload = deepcopy(payload)
        if isinstance(semantic_payload, dict):
            semantic_payload.pop("generated_at", None)
        semantic_bytes = json.dumps(
            semantic_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        stats["semantic_sha256"] = hashlib.sha256(semantic_bytes).hexdigest()
        profile = payload.get("profile") or {}
        stacks = profile.get("stacks") or {}
        stats["output_unique_stacks"] = len(stacks)
        ranking = profile.get("ranking") or {}
        stats["ranking_top_rows"] = len(ranking.get("top") or [])
    elif fmt == "folded":
        lines = [line for line in data.decode("utf-8").splitlines() if line.strip()]
        stats["semantic_sha256"] = stats["raw_sha256"]
        stats["output_unique_stacks"] = len(lines)
        stats["ranking_top_rows"] = 0
    else:
        stats["semantic_sha256"] = stats["raw_sha256"]
        stats["output_unique_stacks"] = None
        stats["ranking_top_rows"] = 0
    stats["sha256"] = stats["semantic_sha256"]
    return stats


def run_one(
    binary: Path,
    spec_path: Path,
    fmt: str,
    rep: int,
    run_dir: Path,
    agentpprof_args: list[str] | None = None,
) -> dict[str, Any]:
    output_path = run_dir / f"{spec_path.stem}-rep{rep}{output_extension(fmt)}"
    extra_args = agentpprof_args or []
    started = time.perf_counter()
    result = subprocess.run(
        [
            str(binary),
            *extra_args,
            "--profile-spec",
            rel(spec_path),
            "-o",
            str(output_path),
            "--format",
            fmt,
        ],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    if result.returncode != 0:
        raise SystemExit(
            f"agentpprof failed for {rel(spec_path)} rep {rep}:\n{result.stderr.strip()}"
        )
    if not output_path.exists():
        raise SystemExit(f"agentpprof did not write expected output {output_path}")
    try:
        stdout_json = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"agentpprof stdout was not JSON for {rel(spec_path)}: {exc}") from exc
    if stdout_json.get("status") != "ok":
        raise SystemExit(f"agentpprof returned non-ok status for {rel(spec_path)}")
    stats = read_output_stats(output_path, fmt)
    return {
        "rep": rep,
        "elapsed_ms": elapsed_ms,
        "stdout_bytes": len(result.stdout.encode("utf-8")),
        "stderr_bytes": len(result.stderr.encode("utf-8")),
        "samples": stdout_json.get("samples"),
        "unique_stacks": stdout_json.get("unique_stacks"),
        **stats,
    }


def summarize_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    runtimes = [float(row["elapsed_ms"]) for row in runs]
    output_bytes = [int(row["output_bytes"]) for row in runs]
    semantic_hashes = [row["semantic_sha256"] for row in runs]
    raw_hashes = [row["raw_sha256"] for row in runs]
    samples = [row.get("samples") for row in runs]
    unique_stacks = [row.get("unique_stacks") for row in runs]
    return {
        "reps": len(runs),
        "median_runtime_ms": median(runtimes),
        "min_runtime_ms": min(runtimes),
        "max_runtime_ms": max(runtimes),
        "p95_runtime_ms": p95(runtimes),
        "output_bytes": output_bytes[0],
        "median_output_bytes": median(output_bytes),
        "samples": samples[0],
        "unique_stacks": unique_stacks[0],
        "output_unique_stacks": runs[0].get("output_unique_stacks"),
        "hash": semantic_hashes[0],
        "semantic_hash": semantic_hashes[0],
        "raw_hash": raw_hashes[0],
        "deterministic_semantic_hash": len(set(semantic_hashes)) == 1,
        "deterministic_raw_hash": len(set(raw_hashes)) == 1,
        "deterministic_hash": len(set(semantic_hashes)) == 1,
        "stable_samples": len(set(samples)) == 1,
        "stable_unique_stacks": len(set(unique_stacks)) == 1,
    }


def evaluate_specs(
    binary: Path,
    specs: list[dict[str, Any]],
    reps: int,
    agentpprof_args: list[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if reps < 2:
        raise SystemExit("--reps must be at least 2 for determinism checking")
    rows = []
    operation_file_cache: dict[Path, int] = {}
    source_paths = [row["path"] for row in specs]
    for spec_row in specs:
        spec = load_json(spec_row["path"])
        base = spec_row["path"].parent
        for raw_path in spec.get("operation_files") or []:
            path = resolve_spec_path(base, raw_path).resolve()
            source_paths.append(path)
            if path not in operation_file_cache:
                operation_file_cache[path] = operation_rows(path)
        for raw_path in spec.get("op_map_files") or []:
            source_paths.append(resolve_spec_path(base, raw_path).resolve())
    source_check = ensure_sources_tracked_clean(source_paths)
    with tempfile.TemporaryDirectory(prefix="agentsight-r327-") as temp_dir:
        temp_path = Path(temp_dir)
        for index, spec_row in enumerate(specs, 1):
            spec_path = spec_row["path"]
            spec = load_json(spec_path)
            fmt = normalized_format(spec)
            runs = [
                run_one(binary, spec_path, fmt, rep, temp_path, agentpprof_args)
                for rep in range(1, reps + 1)
            ]
            summary = summarize_runs(runs)
            operation_files = [
                resolve_spec_path(spec_path.parent, raw_path).resolve()
                for raw_path in (spec.get("operation_files") or [])
            ]
            row = {
                "experiment": spec_row["experiment"],
                "spec": rel(spec_path),
                "format": fmt,
                "view": spec.get("view", "default"),
                "stack_depth": stack_depth(spec),
                "where_rules": list_count(spec, "where_rules"),
                "rank_rules": list_count(spec, "rank_rules"),
                "rank_op_rules": list_count(spec, "rank_op_rules"),
                "operation_files": [rel(path) for path in operation_files],
                "operation_rows": sum(operation_file_cache[path] for path in operation_files),
                **summary,
                "run_index": index,
            }
            rows.append(rounded(row))
    return rows, source_check


def aggregate(rows: list[dict[str, Any]], reps: int) -> dict[str, Any]:
    runtimes = [float(row["median_runtime_ms"]) for row in rows]
    bytes_values = [int(row["output_bytes"]) for row in rows]
    stacks = [int(row["unique_stacks"]) for row in rows if row.get("unique_stacks") is not None]
    experiments = Counter(row["experiment"] for row in rows)
    formats = Counter(row["format"] for row in rows)
    by_experiment = defaultdict(list)
    for row in rows:
        by_experiment[row["experiment"]].append(row)
    experiment_summary = {}
    for experiment, items in sorted(by_experiment.items()):
        values = [float(row["median_runtime_ms"]) for row in items]
        experiment_summary[experiment] = {
            "specs": len(items),
            "median_runtime_ms": median(values),
            "p95_runtime_ms": p95(values),
            "max_runtime_ms": max(values),
            "median_unique_stacks": median(
                [int(row["unique_stacks"]) for row in items if row.get("unique_stacks") is not None]
            ),
            "median_output_bytes": median([int(row["output_bytes"]) for row in items]),
        }
    deterministic_specs = sum(
        row["deterministic_semantic_hash"] and row["stable_samples"] and row["stable_unique_stacks"]
        for row in rows
    )
    raw_deterministic_specs = sum(row["deterministic_raw_hash"] for row in rows)
    return rounded(
        {
            "specs": len(rows),
            "reps_per_spec": reps,
            "profiler_invocations": len(rows) * reps,
            "experiments": dict(experiments),
            "formats": dict(formats),
            "semantic_deterministic_specs": f"{deterministic_specs}/{len(rows)}",
            "raw_byte_deterministic_specs": f"{raw_deterministic_specs}/{len(rows)}",
            "deterministic_specs": f"{deterministic_specs}/{len(rows)}",
            "all_specs_deterministic": deterministic_specs == len(rows),
            "median_runtime_ms": median(runtimes),
            "p95_runtime_ms": p95(runtimes),
            "max_runtime_ms": max(runtimes),
            "median_output_bytes": median(bytes_values),
            "max_output_bytes": max(bytes_values),
            "median_unique_stacks": median(stacks),
            "max_unique_stacks": max(stacks),
            "experiment_summary": experiment_summary,
        }
    )


def write_csv(out_dir: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "experiment",
        "spec",
        "format",
        "view",
        "stack_depth",
        "where_rules",
        "rank_rules",
        "rank_op_rules",
        "operation_rows",
        "samples",
        "unique_stacks",
        "median_runtime_ms",
        "p95_runtime_ms",
        "max_runtime_ms",
        "output_bytes",
        "deterministic_hash",
        "stable_samples",
        "stable_unique_stacks",
        "deterministic_semantic_hash",
        "deterministic_raw_hash",
        "hash",
        "raw_hash",
    ]
    with (out_dir / "profile-cost-summary.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_markdown(out_dir: Path, report: dict[str, Any]) -> None:
    summary = report["summary"]
    lines = [
        "# R327 Profile-Spec Cost and Reproducibility",
        "",
        "This probe reruns existing tracked profile specs against existing tracked operation JSONL inputs. It does not download or sync datasets.",
        "",
        f"- Specs: {summary['specs']}",
        f"- Repetitions per spec: {summary['reps_per_spec']}",
        f"- Profiler invocations: {summary['profiler_invocations']}",
        f"- Deterministic specs: {summary['deterministic_specs']}",
        f"- Raw-byte deterministic specs: {summary['raw_byte_deterministic_specs']} (JSON profiles include `generated_at`)",
        f"- Median per-spec runtime: {summary['median_runtime_ms']:.4f} ms",
        f"- P95 per-spec runtime: {summary['p95_runtime_ms']:.4f} ms",
        f"- Max per-spec runtime: {summary['max_runtime_ms']:.4f} ms",
        f"- Median output size: {summary['median_output_bytes']} bytes",
        f"- Max unique stacks: {summary['max_unique_stacks']}",
        "",
        "## By Experiment",
        "",
        "| Experiment | Specs | Median runtime (ms) | P95 runtime (ms) | Median unique stacks | Median output bytes |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for experiment, row in summary["experiment_summary"].items():
        lines.append(
            f"| {experiment} | {row['specs']} | {row['median_runtime_ms']:.4f} | "
            f"{row['p95_runtime_ms']:.4f} | {row['median_unique_stacks']} | "
            f"{row['median_output_bytes']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Scope",
            "",
            "R327 supports an offline reproducibility and profiler-cost claim for tracked operation-profile specs. It does not measure live eBPF capture overhead, human utility, or compatibility with full OpenTelemetry/Phoenix/LangSmith/Langfuse/Perfetto ecosystems.",
            "The determinism gate hashes semantic profile content after excluding the JSON `generated_at` field; raw-byte hashes are reported separately.",
        ]
    )
    (out_dir / "profile-cost-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_html(out_dir: Path, report: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    summary = report["summary"]
    experiment_rows = "\n".join(
        f"<tr><td>{html.escape(name)}</td><td>{item['specs']}</td>"
        f"<td>{item['median_runtime_ms']:.4f}</td>"
        f"<td>{item['p95_runtime_ms']:.4f}</td>"
        f"<td>{item['median_unique_stacks']}</td>"
        f"<td>{item['median_output_bytes']}</td></tr>"
        for name, item in summary["experiment_summary"].items()
    )
    slowest = sorted(rows, key=lambda row: row["median_runtime_ms"], reverse=True)[:10]
    slow_rows = "\n".join(
        f"<tr><td>{html.escape(row['experiment'])}</td><td><code>{html.escape(Path(row['spec']).name)}</code></td>"
        f"<td>{row['format']}</td><td>{row['unique_stacks']}</td>"
        f"<td>{row['median_runtime_ms']:.4f}</td><td>{row['output_bytes']}</td></tr>"
        for row in slowest
    )
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>R327 Profile-Spec Cost</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; color: #1f2937; }}
table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; }}
th, td {{ border-bottom: 1px solid #d1d5db; padding: 8px; text-align: right; }}
th:first-child, td:first-child, th:nth-child(2), td:nth-child(2) {{ text-align: left; }}
code {{ background: #f3f4f6; padding: 1px 4px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>R327 Profile-Spec Cost and Reproducibility</h1>
<p>Existing tracked profile specs were rerun against existing tracked operation JSONL inputs. No dataset download or sync is part of this probe.</p>
<ul>
<li>Specs: {summary['specs']}</li>
<li>Profiler invocations: {summary['profiler_invocations']}</li>
<li>Deterministic specs: {html.escape(summary['deterministic_specs'])}</li>
<li>Raw-byte deterministic specs: {html.escape(summary['raw_byte_deterministic_specs'])}</li>
<li>Median runtime: {summary['median_runtime_ms']:.4f} ms</li>
<li>P95 runtime: {summary['p95_runtime_ms']:.4f} ms</li>
</ul>
<h2>Experiment Summary</h2>
<table><thead><tr><th>Experiment</th><th>Specs</th><th>Median ms</th><th>P95 ms</th><th>Median stacks</th><th>Median bytes</th></tr></thead><tbody>{experiment_rows}</tbody></table>
<h2>Slowest Specs</h2>
<table><thead><tr><th>Experiment</th><th>Spec</th><th>Format</th><th>Stacks</th><th>Median ms</th><th>Bytes</th></tr></thead><tbody>{slow_rows}</tbody></table>
</body>
</html>
"""
    (out_dir / "index.html").write_text(html_doc, encoding="utf-8")


def main() -> None:
    started = time.perf_counter()
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    binary_status = ensure_agentpprof_binary(args.binary, args.skip_build)
    specs = discover_specs()
    rows, source_check = evaluate_specs(args.binary.resolve(), specs, args.reps)
    summary = aggregate(rows, args.reps)
    status = "pass" if summary["all_specs_deterministic"] else "fail"
    report = {
        "run_id": "R327",
        "status": status,
        "commit": git_output(["rev-parse", "HEAD"]),
        "elapsed_s": round(time.perf_counter() - started, 3),
        "binary_status": binary_status,
        "source_check": source_check,
        "summary": summary,
        "spec_rows": rows,
        "claim": (
            "Existing operation-profile specs execute reproducibly and at low "
            "offline cost on tracked real labeled-operation inputs."
        ),
        "non_claims": [
            "This is not live eBPF capture overhead.",
            "This is not a human or agent analyst productivity study.",
            "This does not download, sync, or create a dataset.",
            "This does not claim complete compatibility with OpenTelemetry, Phoenix, LangSmith, Langfuse, or Perfetto.",
        ],
    }
    write_json(args.out_dir / "profile-cost-report.json", rounded(report))
    write_json(
        args.out_dir / "run-result.json",
        {
            "status": status,
            "report": rel(args.out_dir / "profile-cost-report.json"),
        },
    )
    write_csv(args.out_dir, rows)
    write_markdown(args.out_dir, report)
    write_html(args.out_dir, report, rows)
    if status != "pass":
        raise SystemExit("R327 determinism check failed")


if __name__ == "__main__":
    main()
