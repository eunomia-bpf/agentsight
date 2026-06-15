#!/usr/bin/env python3
"""Summarize the R121 local-model tag benchmark.

The raw benchmark is kept under .agentsight. Committed outputs contain only
scrubbed paths, fixed synthetic fragment previews, hashes, tags, and aggregate
stability metrics.
"""

from __future__ import annotations

import argparse
import json
import re
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    for size in ("0.6b", "1b", "3b"):
        if size in text:
            return size
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

    present_classes = {str(item.get("label")) for item in real_models}
    for model in bench.get("models") or []:
        size_class = model_size_class(scrub(model.get("path", "")), str(model.get("label", "")))
        if size_class:
            present_classes.add(size_class)
    return {
        "directory": scrub(model_dir),
        "real_model_ggufs": real_models,
        "vocab_only_gguf_count": len(vocab_only),
        "missing_size_classes": [size for size in ("0.6b", "1b") if size not in present_classes],
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

    return {
        "label": model.get("label"),
        "path": scrub(model.get("path", "")),
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


def summarize(bench: dict[str, Any], input_path: Path, model_dir: Path) -> dict[str, Any]:
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
    summary = {
        "schema_version": 1,
        "run_id": "R121",
        "generated_at": generated_at,
        "source": rel(input_path),
        "model_discovery": discover_models(model_dir, bench),
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
        "interpretation": [
            "The 3B local llama.cpp benchmark path works and produced syntactically valid one-word tags in every run.",
            "The fixed-input stability result is mixed: one synthetic coding fragment changed labels across identical repeats, while two fragments were exactly stable.",
            "No locally available 0.6B or 1B real model GGUF was found, so this run cannot support claims about those size classes.",
            "This run does not measure human adequacy; R122 remains required before C6 can become stronger than partial.",
        ],
    }
    return scrub_tree(summary)


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
                latency=", ".join(str(value) for value in model.get("latency_ms", [])),
                tags=", ".join(model.get("tags", [])),
            )
        )
    return "\n".join(lines)


def write_markdown(summary: dict[str, Any], path: Path, command: str) -> None:
    model_discovery = summary["model_discovery"]
    fragments = []
    for model in summary["bench"]["models"]:
        fragments.append(f"\n### Model `{model['label']}` Fragments\n")
        fragments.append("| Fragment | Stable | Distinct | Modal | Tags | Preview |")
        fragments.append("|----------|--------|----------|-------|------|---------|")
        for fragment in model.get("fragments", []):
            fragments.append(
                "| {id} | {stable} | {distinct} | {modal} | {tags} | {preview} |".format(
                    id=fragment.get("fragment_id"),
                    stable="yes" if fragment.get("exact_stable") else "no",
                    distinct=fragment.get("distinct_tags"),
                    modal=fragment.get("modal_tag"),
                    tags=", ".join(fragment.get("tags", [])),
                    preview=str(fragment.get("preview", "")).replace("|", "\\|"),
                )
            )
    fragment_markdown = "\n".join(fragments)
    text = f"""# R121 Model Benchmark

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
model weights for this benchmark. Missing size classes:
{", ".join(model_discovery["missing_size_classes"]) or "none"}.

{fragment_markdown}

Interpretation:

- Supported: the 3B local llama.cpp benchmark path works and produced valid
  one-word tags in {summary['aggregate']['ok_runs']}/{summary['aggregate']['total_runs']} runs.
- Mixed: fixed-input exact stability is {summary['aggregate']['exact_stable_fragments']}/{summary['aggregate']['fragment_count']} fragments ({summary['aggregate']['exact_stability_pct']:.3f}%).
- Not supported: 0.6B/1B feasibility and human adequacy.
- Claim impact: C2 can cite 3B syntax/latency feasibility; C6 remains partial
  until adequacy labels and a larger stability sample exist.
"""
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
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
    summary = summarize(bench, args.input, args.model_dir)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(summary, args.out_md, args.command)
    print(json.dumps({"json": rel(args.out_json), "markdown": rel(args.out_md)}, indent=2))


if __name__ == "__main__":
    main()
