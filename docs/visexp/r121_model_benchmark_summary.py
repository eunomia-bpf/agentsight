#!/usr/bin/env python3
"""Summarize the R121 local-model tag benchmark.

The raw benchmark is kept under .agentsight. Committed outputs contain only
scrubbed paths, fixed synthetic fragment previews, hashes, tags, and aggregate
stability metrics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import date
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_INPUT = REPO_ROOT / ".agentsight" / "agentflame" / "model-benchmarks.json"
DEFAULT_OUT_JSON = SCRIPT_DIR / "out" / "model-benchmarks-r121.json"
DEFAULT_OUT_MD = SCRIPT_DIR / "out" / "model-benchmarks-r121.md"
DEFAULT_MODEL_DIR = Path.home() / "workspace" / "llama.cpp-latest" / "models"
TAG_RE = re.compile(r"^[a-z][a-z]{2,11}$")
EXPECTED_SIZE_CLASSES = ("0.6b", "1b", "3b")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path | None) -> str | None:
    if not path:
        return None
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def command_text(cmd: list[str], cwd: Path = REPO_ROOT, timeout: int = 10) -> str | None:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=timeout,
        )
    except Exception:
        return None
    text = (proc.stdout or "").strip()
    return text[:400] if text else None


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return scrub(str(path))


def scrub(value: object) -> str:
    text = str(value)
    home = str(Path.home())
    return text.replace(home, "$HOME").replace(f"home/{Path.home().name}", "$HOME")


def scrub_tree(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: scrub_tree(item) for key, item in value.items()}
    if isinstance(value, list):
        return [scrub_tree(item) for item in value]
    if isinstance(value, str):
        return scrub(value)
    return value


def pct(part: int | float, whole: int | float) -> float:
    return round(100.0 * part / whole, 3) if whole else 0.0


def model_size_class(name: str, label: str = "") -> str | None:
    text = f"{label} {name}".lower()
    if any(token in text for token in ("0.6b", "0_6b", "0-6b", "600m")):
        return "0.6b"
    if any(token in text for token in ("1.1b", "1.0b", "1b", "1000m", "1100m")):
        return "1b"
    if any(token in text for token in ("3b", "3.0b", "3000m")):
        return "3b"
    return None


def discover_models(model_dir: Path, bench: dict[str, Any]) -> dict[str, Any]:
    files = sorted(model_dir.glob("*.gguf")) if model_dir.exists() else []
    real_models = []
    vocab_only = []
    for path in files:
        size = path.stat().st_size
        entry = {"name": path.name, "bytes": size}
        if path.name.startswith("ggml-vocab-") or size < 100_000_000:
            vocab_only.append(entry)
            continue
        size_class = model_size_class(path.name)
        entry["label"] = size_class or path.stem
        real_models.append(entry)

    present_classes = {
        str(item.get("label")) for item in real_models if item.get("label") in EXPECTED_SIZE_CLASSES
    }
    bench_classes = []
    for model in bench.get("models") or []:
        size_class = model_size_class(scrub(model.get("path", "")), str(model.get("label", "")))
        if size_class:
            present_classes.add(size_class)
        bench_classes.append(
            {
                "label": model.get("label"),
                "size_class": size_class,
                "path": scrub(model.get("path", "")),
            }
        )
    return {
        "directory": scrub(model_dir),
        "real_model_ggufs": real_models,
        "bench_models": bench_classes,
        "vocab_only_gguf_count": len(vocab_only),
        "missing_size_classes": [size for size in EXPECTED_SIZE_CLASSES if size not in present_classes],
    }


def summarize_model(model: dict[str, Any]) -> dict[str, Any]:
    runs = model.get("runs") or []
    ok_runs = [run for run in runs if run.get("ok")]
    failed_runs = len(runs) - len(ok_runs)
    tags = [str(run.get("tag")) for run in ok_runs if run.get("tag")]
    invalid_tags = [tag for tag in tags if not TAG_RE.match(tag)]
    fragments = []
    for fragment in model.get("fragments") or []:
        fragments.append(
            {
                "fragment_id": fragment.get("fragment_id"),
                "fragment_hash": fragment.get("fragment_hash"),
                "preview": fragment.get("preview") or "",
                "ok_runs": fragment.get("ok_runs", 0),
                "failed_runs": fragment.get("failed_runs", 0),
                "tags": fragment.get("tags", []),
                "modal_tag": fragment.get("modal_tag"),
                "distinct_tags": fragment.get("distinct_tags", 0),
                "exact_stable": bool(fragment.get("exact_stable")),
                "latency_ms": [
                    run.get("latency_ms")
                    for run in fragment.get("runs", [])
                    if run.get("latency_ms") is not None
                ],
            }
        )

    model_path = Path(str(model.get("path") or ""))
    model_bytes = model_path.stat().st_size if model_path.exists() else None
    return {
        "label": model.get("label"),
        "size_class": model_size_class(str(model.get("path") or ""), str(model.get("label") or "")),
        "path": scrub(model.get("path", "")),
        "path_bytes": model_bytes,
        "path_sha256": file_sha256(model_path) if model_path.exists() else None,
        "load_ms": model.get("load_ms"),
        "total_runs": len(runs),
        "ok_runs": len(ok_runs),
        "failed_runs": failed_runs,
        "valid_tags": len(tags) - len(invalid_tags),
        "invalid_tags": invalid_tags,
        "latency_ms": [run.get("latency_ms") for run in ok_runs if run.get("latency_ms") is not None],
        "tags": tags,
        "stability": model.get("stability", {}),
        "fragments": fragments,
        "llm_calls": (model.get("tagger_stats") or {}).get("llm_calls", 0),
        "llm_successes": (model.get("tagger_stats") or {}).get("llm_successes", 0),
    }


def interpretation_lines(
    models: list[dict[str, Any]],
    workload_label: str,
    human_label_run_id: str,
    missing_size_classes: list[str],
) -> list[str]:
    runnable = [model for model in models if int(model.get("total_runs") or 0) > 0]
    all_valid = [
        str(model.get("label"))
        for model in runnable
        if int(model.get("ok_runs") or 0) == int(model.get("total_runs") or 0)
        and not model.get("invalid_tags")
    ]
    failed = [
        str(model.get("label"))
        for model in models
        if int(model.get("failed_runs") or 0) > 0 or int(model.get("total_runs") or 0) == 0
    ]
    stable = [
        (
            str(model.get("label")),
            int((model.get("stability") or {}).get("exact_stable_fragments") or 0),
            int((model.get("stability") or {}).get("fragment_count") or 0),
        )
        for model in runnable
    ]
    lines = []
    if all_valid:
        lines.append(
            "Local llama.cpp benchmark paths produced syntactically valid one-word tags for "
            + ", ".join(all_valid)
            + "."
        )
    if failed:
        lines.append(
            "Some configured model paths did not produce a full valid benchmark: "
            + ", ".join(failed)
            + "."
        )
    if stable:
        stability_text = ", ".join(f"{label} {ok}/{total}" for label, ok, total in stable)
        lines.append(f"Fixed-input exact stability over {workload_label}: {stability_text}.")
    if missing_size_classes:
        lines.append(
            "This run still lacks real benchmark coverage for size classes: "
            + ", ".join(missing_size_classes)
            + "."
        )
    if len(runnable) > 1:
        lines.append(
            "The compared GGUFs are locally available models with different families or "
            "quantization paths; use this as a deployment-cost smoke, not a controlled "
            "model-family scaling result."
        )
    lines.append(
        f"This run does not measure human adequacy; {human_label_run_id} remains required "
        "before C6 can become stronger than partial."
    )
    return lines


def summarize(
    bench: dict[str, Any],
    input_path: Path,
    model_dir: Path,
    run_id: str,
    workload_label: str,
    command: str,
    fragment_file: Path | None,
    human_label_run_id: str,
) -> dict[str, Any]:
    models = [summarize_model(model) for model in bench.get("models") or []]
    total_runs = sum(int(model["total_runs"]) for model in models)
    ok_runs = sum(int(model["ok_runs"]) for model in models)
    stable_fragments = sum(
        int((model.get("stability") or {}).get("exact_stable_fragments") or 0)
        for model in models
    )
    fragment_count = sum(
        int((model.get("stability") or {}).get("fragment_count") or 0) for model in models
    )
    generated_at = bench.get("generated_at") or date.today().isoformat()
    llama_server = Path(str(bench.get("llama_server") or ""))
    discovery = discover_models(model_dir, bench)
    summary = {
        "schema_version": 1,
        "run_id": run_id,
        "generated_at": generated_at,
        "source": rel(input_path),
        "provenance": {
            "repo_commit": command_text(["git", "rev-parse", "HEAD"]),
            "repo_dirty": bool(command_text(["git", "status", "--short"])),
            "command": command,
            "source_sha256": file_sha256(input_path),
            "fragment_file": rel(fragment_file) if fragment_file else None,
            "fragment_file_sha256": file_sha256(fragment_file) if fragment_file else None,
            "summary_script_sha256": file_sha256(Path(__file__).resolve()),
            "llama_server_sha256": file_sha256(llama_server) if llama_server.exists() else None,
            "llama_server_version": command_text([str(llama_server), "--version"]) if llama_server.exists() else None,
        },
        "model_discovery": discovery,
        "bench": {
            "llama_server": scrub(bench.get("llama_server", "")),
            "runs_per_model": bench.get("runs_per_model"),
            "repeats_per_fragment": bench.get("repeats_per_fragment", bench.get("runs_per_model")),
            "fragments_per_model": bench.get("fragments_per_model"),
            "fragment_previews_included": bool(bench.get("fragment_previews_included")),
            "models": models,
        },
        "aggregate": {
            "total_runs": total_runs,
            "ok_runs": ok_runs,
            "failed_runs": total_runs - ok_runs,
            "valid_run_pct": pct(ok_runs, total_runs),
            "exact_stable_fragments": stable_fragments,
            "fragment_count": fragment_count,
            "exact_stability_pct": pct(stable_fragments, fragment_count),
        },
        "interpretation": interpretation_lines(
            models,
            workload_label,
            human_label_run_id,
            discovery["missing_size_classes"],
        ),
    }
    return scrub_tree(summary)


def percentile(values: list[int], pct_value: float) -> int:
    if not values:
        return 0
    ordered = sorted(int(value) for value in values)
    idx = round((len(ordered) - 1) * pct_value)
    return ordered[max(0, min(idx, len(ordered) - 1))]


def compact_latency(values: list[Any]) -> str:
    ints = [int(value) for value in values if value is not None]
    if len(ints) <= 20:
        return ", ".join(str(value) for value in ints)
    return (
        f"n={len(ints)}, min={min(ints)}, p50={percentile(ints, 0.50)}, "
        f"p95={percentile(ints, 0.95)}, max={max(ints)}"
    )


def compact_tags(tags: list[str]) -> str:
    if len(tags) <= 20:
        return ", ".join(tags)
    counts: dict[str, int] = {}
    for tag in tags:
        counts[tag] = counts.get(tag, 0) + 1
    top = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:12]
    return ", ".join(f"{tag}:{count}" for tag, count in top)


def md_table(summary: dict[str, Any]) -> str:
    lines = [
        "| Model | Load ms | Runs | Ok | Failed | Valid run % | Stable fragments | Exact stability % | Latency ms | Tags |",
        "|-------|---------|------|----|--------|-------------|------------------|-------------------|------------|------|",
    ]
    for model in summary["bench"]["models"]:
        stability = model.get("stability") or {}
        lines.append(
            "| {label} | {load_ms} | {total_runs} | {ok_runs} | {failed_runs} | {valid:.3f} | {stable}/{fragments} | {stable_pct:.3f} | {latency} | {tags} |".format(
                label=model.get("label"),
                load_ms=model.get("load_ms"),
                total_runs=model.get("total_runs"),
                ok_runs=model.get("ok_runs"),
                failed_runs=model.get("failed_runs"),
                valid=pct(model.get("ok_runs", 0), model.get("total_runs", 0)),
                stable=stability.get("exact_stable_fragments", 0),
                fragments=stability.get("fragment_count", 0),
                stable_pct=float(stability.get("exact_stability_pct", 0.0)),
                latency=compact_latency(model.get("latency_ms", [])),
                tags=compact_tags(model.get("tags", [])),
            )
        )
    return "\n".join(lines)


def write_markdown(summary: dict[str, Any], path: Path, command: str, fragment_limit: int) -> None:
    model_discovery = summary["model_discovery"]
    bench_classes = ", ".join(
        f"{item.get('label')}->{item.get('size_class') or 'unknown'}"
        for item in model_discovery.get("bench_models", [])
    )
    interpretation = "\n".join(f"- {line}" for line in summary.get("interpretation", []))
    fragments = []
    for model in summary["bench"]["models"]:
        model_fragments = model.get("fragments", [])
        shown_fragments = model_fragments[:fragment_limit] if fragment_limit > 0 else []
        fragments.append(f"\n### Model `{model['label']}` Fragments\n")
        fragments.append("| Fragment | Stable | Distinct | Modal | Tags | Preview |")
        fragments.append("|----------|--------|----------|-------|------|---------|")
        for fragment in shown_fragments:
            fragments.append(
                "| {id} | {stable} | {distinct} | {modal} | {tags} | {preview} |".format(
                    id=fragment.get("fragment_id"),
                    stable="yes" if fragment.get("exact_stable") else "no",
                    distinct=fragment.get("distinct_tags"),
                    modal=fragment.get("modal_tag"),
                    tags=", ".join(fragment.get("tags", [])),
                    preview=(str(fragment.get("preview", "")) or "(omitted)").replace("|", "\\|"),
                )
            )
        omitted = len(model_fragments) - len(shown_fragments)
        if omitted > 0:
            fragments.append(f"\n{omitted} additional fragments are in the JSON artifact.")
    fragment_markdown = "\n".join(fragments)
    text = f"""# {summary['run_id']} Model Benchmark

Date: {str(summary.get("generated_at", ""))[:10]}

Command:

```bash
{command}
```

Result:

{md_table(summary)}

Model discovery found {len(model_discovery['real_model_ggufs'])} real model GGUF(s).
The remaining {model_discovery['vocab_only_gguf_count']} GGUF files in
`{model_discovery['directory']}` are vocab fixtures or too small to be usable
model weights for this benchmark. Bench model classes:
{bench_classes or "none"}.

Missing size classes:
{", ".join(model_discovery["missing_size_classes"]) or "none"}.

{fragment_markdown}

Interpretation:

{interpretation}

Claim impact: C2 can cite only the model classes that actually ran. C6 remains
partial until human adequacy labels exist.
"""
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--run-id", default="R121")
    parser.add_argument("--workload-label", default="three fixed synthetic fragments")
    parser.add_argument("--fragment-file", type=Path, default=None)
    parser.add_argument("--human-label-run-id", default="R124")
    parser.add_argument("--md-fragment-limit", type=int, default=50)
    parser.add_argument(
        "--command",
        default=(
            "cargo run --manifest-path agentflame/Cargo.toml -- bench "
            "--llama-server $HOME/workspace/llama.cpp-latest/build/bin/llama-server "
            "--runs 3 --load-timeout 240 --request-timeout 60 "
            "--include-fragment-previews "
            "--out .agentsight/agentflame/model-benchmarks.json "
            "--model 3b=$HOME/workspace/llama.cpp-latest/models/qwen2.5-3b-instruct-q4_k_m.gguf"
        ),
    )
    args = parser.parse_args()

    bench = read_json(args.input)
    summary = summarize(
        bench,
        args.input,
        args.model_dir,
        args.run_id,
        args.workload_label,
        args.command,
        args.fragment_file,
        args.human_label_run_id,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(summary, args.out_md, args.command, args.md_fragment_limit)
    print(json.dumps({"json": rel(args.out_json), "markdown": rel(args.out_md)}, indent=2))


if __name__ == "__main__":
    main()
