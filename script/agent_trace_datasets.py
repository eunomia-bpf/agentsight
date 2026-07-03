#!/usr/bin/env python3
"""Sample labeled agent-trajectory datasets into operation JSONL.

The durable profiler abstraction is an operation plus an operation stack. This
script keeps third-party datasets outside the repository, then emits a small
normalized operation JSONL file that `agentpprof --operation-file` can fold with
the same `--stack`, `--op-map`, and `--stack-rule` machinery used for local traces.
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any


HF_DATASET_VIEWER = "https://datasets-server.huggingface.co"
GITHUB_API = "https://api.github.com/repos"
DEFAULT_OUT = Path(".agentsight/datasets/agent-traces")
OSWORLD_HUMAN_APPS = [
    "chrome",
    "gimp",
    "libreoffice_calc",
    "libreoffice_impress",
    "libreoffice_writer",
    "multi_apps",
    "os",
    "thunderbird",
    "vlc",
    "vs_code",
]


DATASETS: dict[str, dict[str, Any]] = {
    "weblinx-chat": {
        "title": "WebLINX chat split",
        "hf_repo": "McGill-NLP/WebLINX",
        "config": "chat",
        "split": "validation",
        "access": "hf-viewer",
        "adapter": "weblinx-chat",
        "source": "https://mcgill-nlp.github.io/weblinx/",
        "paper": "https://arxiv.org/abs/2402.05930",
        "why": "Expert web-navigation demonstrations with action, history, turn, and demo ids.",
    },
    "mind2web": {
        "title": "Mind2Web",
        "hf_repo": "osunlp/Mind2Web",
        "config": "default",
        "split": "train",
        "repo_file": "data/train/train_10.json",
        "access": "large-repo-json",
        "adapter": "mind2web",
        "source": "https://osu-nlp-group.github.io/Mind2Web/",
        "paper": "https://arxiv.org/abs/2306.06070",
        "why": "Crowdsourced web task action sequences; best as an oracle dataset after full-file download.",
        "note": "Dataset Viewer row groups are too large; use HF repo files or the official raw dump for full runs.",
    },
    "webshop-expert": {
        "title": "WebShop expert trajectories",
        "hf_repo": "lclan/webshop_expert_trajectories",
        "config": "default",
        "split": "test",
        "access": "hf-viewer",
        "adapter": "webshop-expert",
        "source": "https://webshop-pnlp.github.io/",
        "paper": "https://papers.neurips.cc/paper_files/paper/2022/hash/82ad13ec01f9fe44c01cb91814fd7b8c-Abstract-Datasets_and_Benchmarks.html",
        "why": "Human/expert shopping task trajectories with task metadata, rewards, and action conversations.",
    },
    "api-bank": {
        "title": "API-Bank",
        "hf_repo": "liminghao1630/API-Bank",
        "config": "default",
        "split": "train",
        "access": "hf-viewer",
        "adapter": "api-bank",
        "source": "https://github.com/AlibabaResearch/DAMO-ConvAI/tree/main/api-bank",
        "paper": "https://arxiv.org/abs/2304.08244",
        "why": "Tool/API-use dialogue instances with gold API request outputs.",
    },
    "agenttrek": {
        "title": "AgentTrek",
        "hf_repo": "xlangai/AgentTrek",
        "config": "default",
        "split": "train",
        "access": "hf-viewer",
        "adapter": "agenttrek",
        "source": "https://agenttrek.github.io/",
        "paper": "https://arxiv.org/abs/2412.09605",
        "why": "Synthetic-but-verified GUI/web trajectories with action tags from tutorial-guided replay.",
    },
    "agentnet": {
        "title": "AgentNet",
        "hf_repo": "xlangai/AgentNet",
        "config": "default",
        "split": "train",
        "repo_file": "agentnet_ubuntu_5k.jsonl",
        "access": "hf-repo-jsonl-stream",
        "adapter": "agentnet",
        "drop_raw_fields": [
            "instruction",
            "natural_language_task",
            "actual_task",
            "reason",
            "traj",
        ],
        "source": "https://huggingface.co/datasets/xlangai/AgentNet",
        "paper": "https://arxiv.org/abs/2508.09123",
        "why": "Large human-annotated desktop computer-use trajectories with PyAutoGUI actions, task outcomes, and step correctness labels.",
        "note": "Sampler streams the requested JSONL prefix/range from Hugging Face instead of downloading the full 282MB/1.4GB trajectory files.",
    },
    "swe-agent-trajectories": {
        "title": "SWE-agent trajectories",
        "hf_repo": "nebius/SWE-agent-trajectories",
        "config": "default",
        "split": "train",
        "access": "hf-viewer",
        "adapter": "swe-agent",
        "source": "https://huggingface.co/datasets/nebius/SWE-agent-trajectories",
        "paper": "https://arxiv.org/abs/2405.15793",
        "why": "Large software-engineering agent trajectories with actions, observations, model name, and success target.",
    },
    "trail": {
        "title": "TRAIL",
        "hf_repo": "PatronusAI/TRAIL",
        "access": "hf-gated-files",
        "source": "https://github.com/patronus-ai/trail-benchmark",
        "paper": "https://arxiv.org/abs/2505.08638",
        "why": "148 human-annotated execution traces with 841 reasoning/planning/execution errors.",
        "note": "HF repo is auto-gated; use after authentication or manual accepted access.",
    },
    "android-control": {
        "title": "AndroidControl",
        "hf_repo": "smolagents/android-control",
        "config": "default",
        "split": "train",
        "access": "hf-viewer",
        "adapter": "android-control",
        "drop_raw_fields": ["screenshots_b64"],
        "source": "https://github.com/google-research/google-research/blob/master/android_control/README.md",
        "paper": "https://arxiv.org/abs/2406.03679",
        "why": "Human Android demonstrations with high-level goals, step instructions, screenshots, trees, and actions.",
        "note": "Rows include screenshot payloads; the sampler strips screenshots from saved raw rows after download.",
    },
    "gui-odyssey": {
        "title": "GUI-Odyssey",
        "hf_repo": "OpenGVLab/GUI-Odyssey",
        "config": "default",
        "split": "all",
        "access": "hf-viewer",
        "adapter": "gui-odyssey",
        "source": "https://github.com/OpenGVLab/GUI-Odyssey",
        "paper": "https://arxiv.org/abs/2406.08451",
        "why": "Cross-app mobile GUI episodes with task/category/app metadata and annotated action steps.",
    },
    "aitw": {
        "title": "Android in the Wild",
        "access": "official-gcs",
        "source": "https://research.google/pubs/android-in-the-wild-a-large-scale-dataset-for-android-device-control/",
        "paper": "https://arxiv.org/abs/2307.10088",
        "why": "Large device-control demonstrations with screens, actions, and natural language instructions.",
        "note": "Use the official google-research/android_in_the_wild release for full data.",
    },
    "toolbench": {
        "title": "ToolBench / ToolLLM",
        "hf_repo": "tuandunghcmut/toolbench-v1",
        "config": "default",
        "split": "validation",
        "access": "hf-viewer",
        "adapter": "toolbench-conversation",
        "source": "https://github.com/OpenBMB/ToolBench",
        "paper": "https://arxiv.org/abs/2307.16789",
        "why": "Tool-use instructions, solution paths, real API calls, and reasoning traces.",
        "note": "Uses a Hugging Face mirror for lightweight sampling; official release remains the canonical source.",
    },
    "tau-bench-trajectories": {
        "title": "tau-bench agent trajectories",
        "hf_repo": "AgentSuite/tau-bench-trajectories",
        "config": "default",
        "split": "train",
        "repo_file": "gpt-4o-mini.jsonl",
        "access": "hf-repo-jsonl",
        "adapter": "tau-bench",
        "source": "https://github.com/sierra-research/tau-bench",
        "paper": "https://arxiv.org/abs/2406.12045",
        "why": "Multi-turn tool-agent-user trajectories with messages, function calls, outcomes, and gold task actions.",
        "note": "Dataset Viewer is preview-only; sampler downloads one per-model JSONL file from the HF repo.",
    },
    "agent-reward-bench": {
        "title": "AgentRewardBench",
        "hf_repo": "McGill-NLP/agent-reward-bench",
        "config": "annotations",
        "split": "full",
        "access": "agent-reward-bench",
        "adapter": "agent-reward-bench",
        "source": "https://github.com/McGill-NLP/agent-reward-bench",
        "paper": "https://arxiv.org/abs/2504.08942",
        "why": "Expert-reviewed web-agent trajectories with success, side-effect, looping, and optimality labels.",
        "note": "Sampler reads the annotations table, then downloads only matching cleaned trajectory JSON files; screenshots are never downloaded.",
    },
    "satraj-os-safety": {
        "title": "SATraj-OS safety trajectories",
        "hf_repo": "AI45Research/SATraj-OS",
        "config": "safety",
        "split": "train",
        "access": "hf-viewer",
        "adapter": "satraj-os",
        "drop_raw_fields": ["messages", "task"],
        "source": "https://huggingface.co/datasets/AI45Research/SATraj-OS",
        "paper": "https://arxiv.org/abs/2605.06230",
        "why": "Large desktop computer-use trajectories with success, safety, reward, and attack labels.",
        "note": "The capability config is not fully readable through Dataset Viewer; the safety config is sampled through rows and raw messages are redacted from saved raw rows.",
    },
    "scalecua-navigation": {
        "title": "ScaleCUA Ubuntu navigation trajectories",
        "hf_repo": "OpenGVLab/ScaleCUA-Data",
        "config": "default",
        "split": "train",
        "repo_file": "annotations/data_20250428_ubuntu_navigation_20250506.jsonl",
        "access": "hf-repo-jsonl-stream",
        "adapter": "scalecua",
        "drop_raw_fields": ["conversations"],
        "source": "https://huggingface.co/datasets/OpenGVLab/ScaleCUA-Data",
        "paper": "https://arxiv.org/abs/2509.15221",
        "why": "Large cross-platform GUI operation trajectories; the Ubuntu navigation subset exposes multi-step tasks, previous operations, and gold actions.",
        "note": "Sampler streams the requested annotation JSONL range from Hugging Face instead of downloading image archives or full annotation files.",
    },
    "osworld-human": {
        "title": "OSWorld-Human reference trajectories",
        "github_repo": "WukLab/osworld-human",
        "config": "default",
        "split": "main",
        "access": "github-directory-json",
        "adapter": "osworld-human",
        "paths": OSWORLD_HUMAN_APPS,
        "drop_raw_fields": ["instruction", "config", "evaluator"],
        "source": "https://github.com/WukLab/osworld-human",
        "paper": "https://arxiv.org/abs/2506.16042",
        "why": "Manual OSWorld reference trajectories with single-action and grouped-action boundaries.",
        "note": "This repository contains benchmark solutions and should not be used for training; use only for profiling/evaluation analysis.",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    list_parser = sub.add_parser("list", help="List known labeled trajectory sources")
    list_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    sample = sub.add_parser("sample", help="Download a small supported sample")
    sample.add_argument("dataset", choices=sorted(DATASETS))
    sample.add_argument("--limit", type=int, default=50)
    sample.add_argument("--offset", type=int, default=0)
    sample.add_argument("--config", help="Override the HF Dataset Viewer config")
    sample.add_argument("--split", help="Override the HF Dataset Viewer split")
    sample.add_argument("--repo-file", help="Override the HF repo file for large JSON datasets")
    sample.add_argument("--out", type=Path, default=DEFAULT_OUT)
    sample.add_argument(
        "--include-text",
        action="store_true",
        help="Include instruction/action-history text in normalized operations",
    )

    args = parser.parse_args()
    if args.cmd == "list":
        return cmd_list(args)
    if args.cmd == "sample":
        return cmd_sample(args)
    parser.error(f"unknown command {args.cmd}")
    return 2


def cmd_list(args: argparse.Namespace) -> int:
    if args.json:
        print(json.dumps(DATASETS, indent=2, sort_keys=True))
        return 0
    for key, item in DATASETS.items():
        hf = item.get("hf_repo") or item.get("github_repo") or "no-hf-repo"
        print(f"{key:16} {item['access']:15} {hf:28} {item['title']}")
    return 0


def cmd_sample(args: argparse.Namespace) -> int:
    dataset = dict(DATASETS[args.dataset])
    if args.config:
        dataset["config"] = args.config
    if args.split:
        dataset["split"] = args.split
    if args.repo_file:
        dataset["repo_file"] = args.repo_file
    if args.limit <= 0:
        raise SystemExit("--limit must be positive")

    out_dir = args.out / args.dataset / f"{dataset['config']}-{dataset['split']}"
    out_dir.mkdir(parents=True, exist_ok=True)
    if dataset["access"] == "hf-viewer":
        rows = hf_viewer_rows(dataset, args.offset, args.limit)
    elif dataset["access"] == "large-repo-json":
        rows = hf_repo_json_rows(dataset, out_dir, args.offset, args.limit)
    elif dataset["access"] == "hf-repo-jsonl":
        rows = hf_repo_jsonl_rows(dataset, out_dir, args.offset, args.limit)
    elif dataset["access"] == "hf-repo-jsonl-stream":
        rows = hf_repo_jsonl_stream_rows(dataset, args.offset, args.limit)
    elif dataset["access"] == "agent-reward-bench":
        rows = agent_reward_bench_rows(dataset, out_dir, args.offset, args.limit)
    elif dataset["access"] == "github-directory-json":
        rows = github_directory_json_rows(dataset, out_dir, args.offset, args.limit)
    else:
        note = dataset.get("note", "No lightweight sampler is configured for this dataset.")
        raise SystemExit(f"{args.dataset} is not sampleable by this command: {note}")
    raw_path = out_dir / f"rows-{args.offset}-{args.offset + len(rows)}.jsonl"
    op_path = out_dir / f"operations-{args.offset}-{args.offset + len(rows)}.jsonl"
    manifest_path = out_dir / "manifest.json"

    operations: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        operations.extend(
            normalize_row(args.dataset, dataset, row, args.offset + row_index, args.include_text)
        )
    write_jsonl(raw_path, redact_raw_rows(rows, dataset.get("drop_raw_fields", [])))
    write_jsonl(op_path, operations)
    manifest = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "dataset": args.dataset,
        "source": dataset,
        "offset": args.offset,
        "limit": args.limit,
        "rows": len(rows),
        "operations": len(operations),
        "raw_rows": str(raw_path),
        "operation_jsonl": str(op_path),
        "privacy": "raw rows may contain task text; operation JSONL omits text unless --include-text is set",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


def hf_viewer_rows(dataset: dict[str, Any], offset: int, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    while len(rows) < limit:
        length = min(100, limit - len(rows))
        params = urllib.parse.urlencode(
            {
                "dataset": dataset["hf_repo"],
                "config": dataset["config"],
                "split": dataset["split"],
                "offset": offset + len(rows),
                "length": length,
            }
        )
        fallback_first_rows = False
        try:
            payload = get_json(f"{HF_DATASET_VIEWER}/rows?{params}")
        except urllib.error.HTTPError as error:
            if rows:
                break
            if offset != 0:
                raise SystemExit(f"Dataset Viewer rows request failed: HTTP {error.code}") from error
            payload = hf_first_rows(dataset)
            fallback_first_rows = True
        if "error" in payload:
            raise SystemExit(payload["error"])
        batch = [entry["row"] for entry in payload.get("rows", [])]
        if not batch:
            break
        rows.extend(batch[: limit - len(rows)])
        if fallback_first_rows:
            break
    return rows


def hf_first_rows(dataset: dict[str, Any]) -> dict[str, Any]:
    params = urllib.parse.urlencode(
        {
            "dataset": dataset["hf_repo"],
            "config": dataset["config"],
            "split": dataset["split"],
        }
    )
    return get_json(f"{HF_DATASET_VIEWER}/first-rows?{params}")


def hf_repo_json_rows(
    dataset: dict[str, Any], out_dir: Path, offset: int, limit: int
) -> list[dict[str, Any]]:
    repo_file = dataset["repo_file"]
    source_path = out_dir / Path(repo_file).name
    if not source_path.exists():
        encoded = urllib.parse.quote(repo_file)
        url = f"https://huggingface.co/datasets/{dataset['hf_repo']}/resolve/main/{encoded}"
        with urllib.request.urlopen(url, timeout=120) as response:
            source_path.write_bytes(response.read())
    with source_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, list):
        raise SystemExit(f"{repo_file} did not contain a JSON list")
    return payload[offset : offset + limit]


def hf_repo_jsonl_rows(
    dataset: dict[str, Any], out_dir: Path, offset: int, limit: int
) -> list[dict[str, Any]]:
    repo_file = dataset["repo_file"]
    source_path = out_dir / Path(repo_file).name
    if not source_path.exists():
        encoded = urllib.parse.quote(repo_file)
        url = f"https://huggingface.co/datasets/{dataset['hf_repo']}/resolve/main/{encoded}"
        with urllib.request.urlopen(url, timeout=120) as response:
            source_path.write_bytes(response.read())
    rows: list[dict[str, Any]] = []
    with source_path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f):
            if line_number < offset:
                continue
            if len(rows) >= limit:
                break
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def hf_repo_jsonl_stream_rows(
    dataset: dict[str, Any], offset: int, limit: int
) -> list[dict[str, Any]]:
    repo_file = dataset["repo_file"]
    encoded = urllib.parse.quote(repo_file)
    url = f"https://huggingface.co/datasets/{dataset['hf_repo']}/resolve/main/{encoded}"
    rows: list[dict[str, Any]] = []
    with urllib.request.urlopen(url, timeout=180) as response:
        for line_number, raw_line in enumerate(response):
            if line_number < offset:
                continue
            if len(rows) >= limit:
                break
            line = raw_line.decode("utf-8").strip()
            if line:
                rows.append(json.loads(line))
    return rows


def agent_reward_bench_rows(
    dataset: dict[str, Any], out_dir: Path, offset: int, limit: int
) -> list[dict[str, Any]]:
    rows = hf_viewer_rows(dataset, offset, limit)
    cache_dir = out_dir / "trajectory-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    enriched = []
    for row in rows:
        item = dict(row)
        trajectory_path = agent_reward_trajectory_path(item)
        item["trajectory_path"] = trajectory_path
        try:
            payload = hf_repo_json_object(dataset["hf_repo"], trajectory_path, cache_dir)
        except urllib.error.HTTPError as error:
            item["trajectory_error"] = f"HTTP {error.code}"
        else:
            item["trajectory"] = prune_agent_reward_trajectory(payload)
        enriched.append(item)
    return enriched


def agent_reward_trajectory_path(row: dict[str, Any]) -> str:
    benchmark = str(row.get("benchmark") or "")
    model_name = str(row.get("model_name") or "")
    exp_name = str(row.get("exp_name") or "")
    task_id = str(row.get("task_id") or "")
    filename = task_id if task_id.endswith(".json") else f"{task_id}.json"
    return f"cleaned/{benchmark}/{model_name}/{exp_name}/{filename}"


def hf_repo_json_object(repo: str, repo_file: str, cache_dir: Path) -> dict[str, Any]:
    cache_path = cache_dir / f"{stable_id(repo_file)}.json"
    if not cache_path.exists():
        encoded = urllib.parse.quote(repo_file)
        url = f"https://huggingface.co/datasets/{repo}/resolve/main/{encoded}"
        with urllib.request.urlopen(url, timeout=180) as response:
            cache_path.write_bytes(response.read())
    with cache_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise SystemExit(f"{repo_file} did not contain a JSON object")
    return payload


def github_directory_json_rows(
    dataset: dict[str, Any], out_dir: Path, offset: int, limit: int
) -> list[dict[str, Any]]:
    index_path = out_dir / "github-index.json"
    cache_dir = out_dir / "github-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    if not index_path.exists():
        entries = github_directory_index(dataset)
        index_path.write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        entries = json.loads(index_path.read_text(encoding="utf-8"))
    rows = []
    for entry in entries[offset : offset + limit]:
        cache_path = cache_dir / f"{stable_id(entry['path'])}.json"
        if not cache_path.exists():
            with urllib.request.urlopen(entry["download_url"], timeout=120) as response:
                cache_path.write_bytes(response.read())
        with cache_path.open("r", encoding="utf-8") as f:
            row = json.load(f)
        if not isinstance(row, dict):
            raise SystemExit(f"{entry['path']} did not contain a JSON object")
        row["_github_path"] = entry["path"]
        row["_github_application"] = entry["application"]
        row["_github_file"] = entry["name"]
        rows.append(row)
    return rows


def github_directory_index(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    repo = dataset["github_repo"]
    entries = []
    for path in dataset.get("paths") or []:
        payload = get_json(f"{GITHUB_API}/{repo}/contents/{urllib.parse.quote(path)}")
        if not isinstance(payload, list):
            raise SystemExit(f"GitHub contents for {repo}/{path} did not return a list")
        for item in payload:
            if item.get("type") != "file" or not str(item.get("name") or "").endswith(".json"):
                continue
            entries.append(
                {
                    "application": path,
                    "name": item["name"],
                    "path": item["path"],
                    "download_url": item["download_url"],
                    "size": item.get("size"),
                }
            )
    return sorted(entries, key=lambda item: (item["application"], item["name"]))


def prune_agent_reward_trajectory(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary_info") or {}
    return {
        "benchmark": payload.get("benchmark"),
        "agent": payload.get("agent"),
        "model": payload.get("model"),
        "experiment": payload.get("experiment"),
        "valid": payload.get("valid"),
        "goal": truncate_clean(str(payload.get("goal") or ""), 240),
        "summary_info": {
            key: summary.get(key)
            for key in [
                "n_steps",
                "cum_reward",
                "cum_raw_reward",
                "err_msg",
                "terminated",
                "truncated",
                "stats.cum_input_tokens",
                "stats.cum_output_tokens",
                "stats.cum_step_elapsed",
                "stats.cum_agent_elapsed",
            ]
            if key in summary
        },
        "steps": [prune_agent_reward_step(step) for step in payload.get("steps") or []],
    }


def prune_agent_reward_step(step: dict[str, Any]) -> dict[str, Any]:
    stats = step.get("stats") or {}
    return {
        "num": step.get("num"),
        "action": step.get("action"),
        "reasoning": truncate_clean(str(step.get("reasoning") or ""), 360),
        "url": truncate_clean(str(step.get("url") or ""), 240),
        "focused_element": step.get("focused_element"),
        "last_action_error": truncate_clean(str(step.get("last_action_error") or ""), 240),
        "stats": {
            key: stats.get(key)
            for key in ["n_retry_llm", "n_retry", "busted_retry", "input_tokens", "output_tokens", "cost"]
            if key in stats
        },
    }


def get_json(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_row(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    row_index: int,
    include_text: bool,
) -> list[dict[str, Any]]:
    adapter = dataset.get("adapter")
    if adapter == "weblinx-chat":
        return [normalize_weblinx_chat(dataset_id, dataset, row, include_text)]
    if adapter == "mind2web":
        return normalize_mind2web(dataset_id, dataset, row, include_text)
    if adapter == "webshop-expert":
        return normalize_webshop_expert(dataset_id, dataset, row, include_text)
    if adapter == "api-bank":
        return [normalize_api_bank(dataset_id, dataset, row, row_index, include_text)]
    if adapter == "agenttrek":
        return normalize_agenttrek(dataset_id, dataset, row, row_index, include_text)
    if adapter == "agentnet":
        return normalize_agentnet(dataset_id, dataset, row, row_index, include_text)
    if adapter == "swe-agent":
        return normalize_swe_agent(dataset_id, dataset, row, row_index, include_text)
    if adapter == "android-control":
        return normalize_android_control(dataset_id, dataset, row, row_index, include_text)
    if adapter == "gui-odyssey":
        return normalize_gui_odyssey(dataset_id, dataset, row, row_index, include_text)
    if adapter == "toolbench-conversation":
        return normalize_toolbench_conversation(dataset_id, dataset, row, row_index, include_text)
    if adapter == "tau-bench":
        return normalize_tau_bench(dataset_id, dataset, row, row_index, include_text)
    if adapter == "agent-reward-bench":
        return normalize_agent_reward_bench(dataset_id, dataset, row, row_index, include_text)
    if adapter == "satraj-os":
        return normalize_satraj_os(dataset_id, dataset, row, row_index, include_text)
    if adapter == "scalecua":
        return [normalize_scalecua(dataset_id, dataset, row, row_index, include_text)]
    if adapter == "osworld-human":
        return normalize_osworld_human(dataset_id, dataset, row, row_index, include_text)
    raise SystemExit(f"no adapter for dataset {dataset_id}")


def normalize_weblinx_chat(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    include_text: bool,
) -> dict[str, Any]:
    action = str(row.get("action") or "unknown")
    action_name = first_match(r"^([A-Za-z_][A-Za-z0-9_]*)", action, "unknown").lower()
    target = first_match(r'uid=(?:"([^"]+)"|([^,)]+))', action, "none")
    if target == "None":
        target = "none"

    fields: dict[str, Any] = {
        "project": "external-agent-traces",
        "agent": "human-demo",
        "dataset": dataset_id,
        "source": dataset["hf_repo"],
        "session": str(row.get("demo") or "unknown"),
        "turn": str(row.get("turn") or "unknown"),
        "task": "web-navigation",
        "phase": action_name,
        "op": "action",
        "tool": "browser",
        "action": action_name,
        "target": sanitize_label(target),
        "status": "gold",
    }
    if include_text:
        instruction = latest_instructor_utterance(str(row.get("action_history") or ""))
        if instruction:
            fields["task_preview"] = truncate_clean(instruction, 180)
        fields["action_raw"] = truncate_clean(action, 180)
    return {"value": 1, "fields": fields}


def normalize_mind2web(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    include_text: bool,
) -> list[dict[str, Any]]:
    session = str(row.get("annotation_id") or stable_id(row))
    task = sanitize_label(str(row.get("domain") or "web-task"))
    operations = []
    action_reprs = row.get("action_reprs") or []
    for turn, action in enumerate(row.get("actions") or []):
        operation = action.get("operation") or {}
        action_name = sanitize_label(str(operation.get("op") or operation.get("original_op") or "unknown"))
        original = sanitize_label(str(operation.get("original_op") or action_name))
        fields: dict[str, Any] = {
            "project": "external-agent-traces",
            "agent": "human-demo",
            "dataset": dataset_id,
            "source": dataset["hf_repo"],
            "session": session,
            "turn": str(turn),
            "task": task,
            "phase": action_name,
            "op": "action",
            "tool": "browser",
            "action": action_name,
            "original_action": original,
            "website": sanitize_label(str(row.get("website") or "unknown")),
            "domain": sanitize_label(str(row.get("domain") or "unknown")),
            "subdomain": sanitize_label(str(row.get("subdomain") or "unknown")),
            "status": "gold",
        }
        if include_text:
            fields["task_preview"] = truncate_clean(str(row.get("confirmed_task") or ""), 180)
            if turn < len(action_reprs):
                fields["action_raw"] = truncate_clean(str(action_reprs[turn]), 180)
        operations.append({"value": 1, "fields": fields})
    return operations


def normalize_webshop_expert(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    include_text: bool,
) -> list[dict[str, Any]]:
    info = row.get("info") or {}
    session = str(row.get("id") or stable_id(row))
    reward = int(info.get("reward") or 0)
    task = sanitize_label(str(info.get("task_name") or "webshop-task"))
    operations = []
    for turn, message in enumerate(row.get("conversations") or []):
        if message.get("role") != "assistant":
            continue
        content = str(message.get("content") or "")
        action = extract_action_block(content)
        if not action:
            continue
        action_name = action_verb(action)
        fields: dict[str, Any] = {
            "project": "external-agent-traces",
            "agent": str(info.get("agent_arch") or "expert"),
            "dataset": dataset_id,
            "source": dataset["hf_repo"],
            "session": session,
            "turn": str(turn),
            "task": task,
            "phase": action_name,
            "op": "action",
            "tool": "webshop",
            "action": action_name,
            "status": "success" if reward > 0 else "unknown",
            "score": str(message.get("score") or reward),
        }
        if include_text:
            fields["action_raw"] = truncate_clean(action, 180)
        operations.append({"value": 1, "fields": fields})
    return operations


def normalize_api_bank(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    row_index: int,
    include_text: bool,
) -> dict[str, Any]:
    output = str(row.get("output") or "")
    api_name = first_match(r"\[([A-Za-z_][A-Za-z0-9_]*)\(", output, "unknown_api")
    domain = first_match(r'"apiCode":\s*"([A-Za-z_][A-Za-z0-9_]*)"', str(row.get("input") or ""), api_name)
    fields: dict[str, Any] = {
        "project": "external-agent-traces",
        "agent": "gold-api",
        "dataset": dataset_id,
        "source": dataset["hf_repo"],
        "session": f"api-bank-{row_index}",
        "task": "api-call",
        "phase": "api",
        "op": "tool",
        "tool": "api",
        "action": sanitize_label(api_name),
        "domain": sanitize_label(domain),
        "status": "gold",
    }
    if include_text:
        fields["action_raw"] = truncate_clean(output, 180)
    return {"value": 1, "fields": fields}


def normalize_agenttrek(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    row_index: int,
    include_text: bool,
) -> list[dict[str, Any]]:
    operations = []
    session = f"agenttrek-{row_index}"
    for turn, message in enumerate(row.get("messages") or []):
        if message.get("role") != "assistant":
            continue
        content = str(message.get("content") or "")
        action = first_match(r"<action>\s*(.*?)\s*</action>", content, "")
        if not action:
            continue
        action_name = action_verb(action)
        fields: dict[str, Any] = {
            "project": "external-agent-traces",
            "agent": "vlm-agent",
            "dataset": dataset_id,
            "source": dataset["hf_repo"],
            "session": session,
            "turn": str(turn),
            "task": "web-gui",
            "phase": action_name,
            "op": "action",
            "tool": "browser",
            "action": action_name,
            "status": "verified",
        }
        if include_text:
            fields["action_raw"] = truncate_clean(action, 180)
        operations.append({"value": 1, "fields": fields})
    return operations


def normalize_agentnet(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    row_index: int,
    include_text: bool,
) -> list[dict[str, Any]]:
    session = sanitize_label(str(row.get("task_id") or f"agentnet-{row_index}"))
    domain = sanitize_label(str(row.get("domain") or "desktop"))
    traj = [step for step in row.get("traj") or [] if isinstance(step, dict)]
    status = agentnet_task_status(row, traj)
    parsed_steps: list[tuple[int, dict[str, Any], str, str, str]] = []
    signatures: list[tuple[str, str]] = []
    for ordinal, step in enumerate(traj):
        value = step.get("value") or {}
        if not isinstance(value, dict):
            value = {}
        code = str(value.get("code") or "")
        action = agentnet_code_action(code)
        target = agentnet_action_target(action, code)
        signatures.append((action, target))
        parsed_steps.append((ordinal, step, code, action, target))

    repeat_features = repeat_features_for_signatures(signatures)
    operations = []
    for ordinal, step, code, action, target in parsed_steps:
        value = step.get("value") or {}
        repeat = repeat_features[ordinal]
        correct = normalize_bool_outcome(value.get("last_step_correct"), "correct", "incorrect")
        redundant = normalize_bool_outcome(value.get("last_step_redundant"), "redundant", "necessary")
        fields: dict[str, Any] = {
            "project": "external-agent-traces",
            "agent": "human-annotated",
            "dataset": dataset_id,
            "source": dataset["hf_repo"],
            "session": session,
            "turn": str(step.get("index") if step.get("index") is not None else ordinal),
            "step": str(ordinal),
            "task": "desktop-computer-use",
            "benchmark": "agentnet",
            "environment": domain,
            "domain": domain,
            "phase": agentnet_action_phase(action),
            "op": "action",
            "tool": "computer",
            "action": action,
            "target": target,
            "status": status,
            "step_correct": correct,
            "step_redundant": redundant,
            "alignment_score": normalize_score(row.get("alignment_score")),
            "efficiency_score": normalize_score(row.get("efficiency_score")),
            "task_difficulty": normalize_score(row.get("task_difficulty")),
            "repeat_state": repeat["repeat_state"],
            "repeat_signal": repeat["repeat_signal"],
            "repeat_run": repeat["repeat_run"],
        }
        if include_text:
            fields["task_preview"] = truncate_clean(str(row.get("instruction") or ""), 180)
            fields["action_raw"] = truncate_clean(str(value.get("action") or code), 180)
        operations.append({"value": 1, "fields": fields})
    return operations


def agentnet_code_action(code: str) -> str:
    name = first_match(r"pyautogui\.([A-Za-z_][A-Za-z0-9_]*)", code, "")
    if not name:
        name = first_match(r"computer\.([A-Za-z_][A-Za-z0-9_]*)", code, "")
    if not name:
        name = first_match(r"^([A-Za-z_][A-Za-z0-9_]*)", code.strip(), "unknown")
    label = sanitize_label(name)
    aliases = {
        "doubleclick": "double_click",
        "tripleclick": "triple_click",
        "leftclick": "click",
        "rightclick": "right_click",
        "middleclick": "middle_click",
        "moveto": "move_to",
        "dragto": "drag",
        "dragrel": "drag",
        "mousemove": "move_to",
        "write": "type",
        "typewrite": "type",
        "screenshot": "observe",
    }
    return aliases.get(label, label or "unknown")


def agentnet_action_phase(action: str) -> str:
    if action == "terminate":
        return "finish"
    return osworld_action_phase(action)


def agentnet_action_target(action: str, code: str) -> str:
    if action in {"click", "double_click", "triple_click", "right_click", "middle_click"}:
        return coordinate_bucket(code)
    if action in {"move_to", "drag", "mouse_down", "mouse_up"}:
        return coordinate_bucket(code)
    if action in {"hotkey", "press", "key_down", "key_up"}:
        keys = re.findall(r"['\"]([^'\"]+)['\"]", code)
        return sanitize_label("-".join(keys[:4]) or "key")
    if action in {"type"}:
        return "text"
    if action == "scroll":
        return "scroll"
    if action in {"observe", "wait"}:
        return "none"
    if action == "terminate":
        return sanitize_label(first_match(r"status=['\"]([^'\"]+)['\"]", code, "none"))
    return "none"


def agentnet_task_status(row: dict[str, Any], traj: list[dict[str, Any]]) -> str:
    status = normalize_bool_outcome(row.get("task_completed"), "success", "failure")
    if status != "unknown":
        return status
    for step in reversed(traj):
        value = step.get("value") or {}
        if not isinstance(value, dict):
            continue
        code = str(value.get("code") or "")
        if agentnet_code_action(code) == "terminate":
            target = agentnet_action_target("terminate", code)
            if target in {"success", "failure"}:
                return target
    return "unknown"


def normalize_score(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return sanitize_label(str(value))


def normalize_swe_agent(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    row_index: int,
    include_text: bool,
) -> list[dict[str, Any]]:
    operations = []
    session = str(row.get("instance_id") or f"swe-{row_index}")
    status = str(row.get("exit_status") or "unknown")
    success = "success" if row.get("target") is True else "failure"
    for turn, event in enumerate(row.get("trajectory") or []):
        role = str(event.get("role") or "")
        if role not in {"ai", "assistant"}:
            continue
        text = str(event.get("text") or "")
        command = extract_code_command(text)
        if not command:
            continue
        command_name = action_verb(command)
        fields: dict[str, Any] = {
            "project": "external-agent-traces",
            "agent": sanitize_label(str(row.get("model_name") or "swe-agent")),
            "dataset": dataset_id,
            "source": dataset["hf_repo"],
            "session": session,
            "turn": str(turn),
            "task": "software-issue",
            "phase": command_name,
            "op": "tool",
            "tool": "swe-agent",
            "action": command_name,
            "cmd": command_name,
            "status": success,
            "exit": sanitize_label(status),
        }
        if include_text:
            fields["command"] = truncate_clean(command, 180)
        operations.append({"value": 1, "fields": fields})
    return operations


def normalize_android_control(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    row_index: int,
    include_text: bool,
) -> list[dict[str, Any]]:
    session = str(row.get("episode_id") or f"android-control-{row_index}")
    step_instructions = row.get("step_instructions") or []
    operations = []
    for turn, action in enumerate(row.get("actions") or []):
        action_name = sanitize_label(str(action.get("action_type") or "unknown"))
        app_name = sanitize_label(str(action.get("app_name") or "unknown-app"))
        fields: dict[str, Any] = {
            "project": "external-agent-traces",
            "agent": "human-demo",
            "dataset": dataset_id,
            "source": dataset["hf_repo"],
            "session": session,
            "turn": str(turn),
            "task": "mobile-control",
            "step": str(turn),
            "phase": action_name,
            "op": "action",
            "tool": "android",
            "action": action_name,
            "app": app_name,
            "status": "gold",
        }
        direction = sanitize_label(str(action.get("direction") or ""))
        if direction != "none":
            fields["direction"] = direction
        if include_text:
            fields["task_preview"] = truncate_clean(str(row.get("goal") or ""), 180)
            if turn < len(step_instructions):
                fields["step_preview"] = truncate_clean(str(step_instructions[turn]), 180)
            if action.get("text"):
                fields["action_raw"] = truncate_clean(str(action.get("text")), 180)
        operations.append({"value": 1, "fields": fields})
    return operations


def normalize_gui_odyssey(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    row_index: int,
    include_text: bool,
) -> list[dict[str, Any]]:
    session = str(row.get("episode_id") or f"gui-odyssey-{row_index}")
    operations = []
    for turn, step in enumerate(parse_gui_odyssey_steps(row.get("steps"))):
        action_name = sanitize_label(str(step.get("action") or "unknown"))
        fields: dict[str, Any] = {
            "project": "external-agent-traces",
            "agent": "human-demo",
            "dataset": dataset_id,
            "source": dataset["hf_repo"],
            "session": session,
            "turn": str(step.get("step") if step.get("step") is not None else turn),
            "task": "mobile-cross-app",
            "phase": action_name,
            "op": "action",
            "tool": "mobile-gui",
            "action": action_name,
            "category": sanitize_label(str(row.get("category") or "unknown")),
            "device": sanitize_label(str(row.get("device_name") or "unknown")),
            "status": "gold",
        }
        app = sanitize_label(str(row.get("app") or "unknown-app"))
        if app != "none":
            fields["app"] = app
        if include_text:
            fields["task_preview"] = truncate_clean(str(row.get("instruction") or ""), 180)
            fields["action_raw"] = truncate_clean(str(step.get("info") or ""), 180)
        operations.append({"value": 1, "fields": fields})
    return operations


def normalize_toolbench_conversation(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    row_index: int,
    include_text: bool,
) -> list[dict[str, Any]]:
    session = stable_id(row.get("id") or row_index)
    operations = []
    messages = conversation_messages(row.get("conversations"))
    for turn, message in enumerate(messages):
        if str(message.get("from") or "").lower() != "assistant":
            continue
        content = str(message.get("value") or "")
        action = extract_action_block(content)
        if not action:
            continue
        action_name = action_verb(action)
        tool_name = infer_toolbench_tool(action)
        fields: dict[str, Any] = {
            "project": "external-agent-traces",
            "agent": "autogpt",
            "dataset": dataset_id,
            "source": dataset["hf_repo"],
            "session": session,
            "turn": str(turn),
            "task": "tool-use",
            "phase": "finish" if action_name == "finish" else "api",
            "op": "finish" if action_name == "finish" else "tool",
            "tool": tool_name,
            "action": action_name,
            "domain": tool_name,
            "status": "gold",
        }
        if include_text:
            fields["task_preview"] = truncate_clean(str(row.get("id") or ""), 180)
            fields["action_raw"] = truncate_clean(content, 180)
        operations.append({"value": 1, "fields": fields})
    return operations


def normalize_agent_reward_bench(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    row_index: int,
    include_text: bool,
) -> list[dict[str, Any]]:
    trajectory = row.get("trajectory") or {}
    steps = [step for step in trajectory.get("steps") or [] if step.get("action")]
    if not steps:
        fields = agent_reward_base_fields(dataset_id, dataset, row, row_index, "trajectory")
        fields.update(
            {
                "phase": "trajectory",
                "op": "trajectory",
                "tool": "browser",
                "action": "trajectory",
                "step_error": "missing-trajectory" if row.get("trajectory_error") else "none",
                "repeat_state": "unknown",
                "repeat_signal": "unknown",
            }
        )
        return [{"value": 1, "fields": fields}]

    repeat_features = agent_reward_repeat_features(steps)
    operations = []
    for ordinal, step in enumerate(steps):
        action_raw = str(step.get("action") or "")
        action = action_verb(action_raw)
        error = str(step.get("last_action_error") or "")
        repeat = repeat_features[ordinal]
        fields = agent_reward_base_fields(
            dataset_id,
            dataset,
            row,
            row_index,
            str(step.get("num") if step.get("num") is not None else ordinal),
        )
        fields.update(
            {
                "phase": agent_reward_action_phase(action),
                "op": "action",
                "tool": "browser",
                "action": action,
                "target": sanitize_label(agent_reward_action_target(action_raw)),
                "step_error": "error" if error else "ok",
                "repeat_state": repeat["repeat_state"],
                "repeat_signal": repeat["repeat_signal"],
                "repeat_run": repeat["repeat_run"],
            }
        )
        stats = step.get("stats") or {}
        for source_key, field_key in [
            ("input_tokens", "input_tokens"),
            ("output_tokens", "output_tokens"),
            ("n_retry_llm", "llm_retries"),
            ("busted_retry", "busted_retry"),
        ]:
            if source_key in stats:
                fields[field_key] = str(stats[source_key])
        if include_text:
            fields["task_preview"] = truncate_clean(str(trajectory.get("goal") or ""), 180)
            fields["reasoning"] = truncate_clean(str(step.get("reasoning") or ""), 180)
            fields["action_raw"] = truncate_clean(action_raw, 180)
        operations.append({"value": 1, "fields": fields})
    return operations


def agent_reward_repeat_features(steps: list[dict[str, Any]]) -> list[dict[str, str]]:
    signatures: list[tuple[str, str]] = []
    for step in steps:
        action_raw = str(step.get("action") or "")
        signatures.append((action_verb(action_raw), sanitize_label(agent_reward_action_target(action_raw))))
    return repeat_features_for_signatures(signatures)


def agent_reward_base_fields(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    row_index: int,
    turn: str,
) -> dict[str, Any]:
    success = normalize_success_label(str(row.get("trajectory_success") or "unknown"))
    side_effect = normalize_yes_no_label(str(row.get("trajectory_side_effect") or "unknown"))
    looping = normalize_yes_no_label(str(row.get("trajectory_looping") or "unknown"))
    optimality = normalize_optimality_label(str(row.get("trajectory_optimality") or "unknown"))
    benchmark = sanitize_label(str(row.get("benchmark") or "unknown"))
    task_id = sanitize_label(str(row.get("task_id") or f"agent-reward-{row_index}"))
    model_name = sanitize_label(str(row.get("model_name") or "unknown-model"))
    return {
        "project": "external-agent-traces",
        "agent": model_name,
        "dataset": dataset_id,
        "source": dataset["hf_repo"],
        "session": task_id,
        "turn": turn,
        "task": "web-agent-eval",
        "benchmark": benchmark,
        "environment": benchmark,
        "status": success,
        "side_effect": side_effect,
        "looping": looping,
        "optimality": optimality,
        "annotator": sanitize_label(str(row.get("annotator_name") or "expert")),
        "experiment": sanitize_label(str(row.get("exp_name") or "unknown-experiment")),
    }


def agent_reward_action_phase(action: str) -> str:
    if action in {"fill", "type", "press", "keyboard"}:
        return "input"
    if action in {"click", "hover", "select", "scroll", "goto", "go_back", "go_forward"}:
        return "navigate"
    if action in {"report_infeasible", "send_msg_to_user", "stop", "finish", "final_answer"}:
        return "finish"
    if action in {"noop", "wait", "observe"}:
        return "observe"
    return "browser-action"


def agent_reward_action_target(action: str) -> str:
    if action_verb(action) in {"report_infeasible", "send_msg_to_user", "finish", "final_answer"}:
        return "none"
    target = first_match(r"['\"]([^'\"]+)['\"]", action, "none")
    if len(target) > 64:
        return "none"
    return target


def normalize_success_label(value: str) -> str:
    label = sanitize_label(value)
    if label in {"successful", "success", "succeeded", "pass", "passed"}:
        return "success"
    if label in {"unsuccessful", "failure", "failed", "fail"}:
        return "failure"
    return label


def normalize_yes_no_label(value: str) -> str:
    label = sanitize_label(value)
    if label in {"yes", "true", "1"}:
        return "yes"
    if label in {"no", "false", "0"}:
        return "no"
    return label


def normalize_optimality_label(value: str) -> str:
    label = re.sub(r"^\s*\d+\.\s*", "", value.strip())
    return sanitize_label(label or value)


def normalize_satraj_os(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    row_index: int,
    include_text: bool,
) -> list[dict[str, Any]]:
    result = row.get("result") or {}
    attack = result.get("attack") or {}
    task_meta = parse_json_object(row.get("task"))
    session = sanitize_label(str(row.get("trajectory_id") or f"satraj-{row_index}"))
    domain = sanitize_label(str(task_meta.get("domain") or row.get("trajectory_category") or "desktop"))
    status = normalize_bool_outcome(result.get("success"), "success", "failure")
    safety = normalize_bool_outcome(result.get("safety"), "safe", "unsafe")
    attack_flag = normalize_bool_outcome(attack.get("is_attack"), "attack", "benign")
    messages = [message for message in row.get("messages") or [] if isinstance(message, dict)]

    operations = []
    action_signatures: list[tuple[str, str]] = []
    parsed_steps: list[tuple[int, dict[str, str], str, str]] = []
    for message_index, message in enumerate(messages):
        if str(message.get("role") or "").lower() != "assistant":
            continue
        params = extract_xml_tool_call_params(str(message.get("content") or ""))
        action = sanitize_label(params.get("action") or "")
        if not action:
            continue
        target = satraj_action_target(action, params)
        action_signatures.append((action, target))
        parsed_steps.append((message_index, params, action, target))

    repeat_features = repeat_features_for_signatures(action_signatures)
    for ordinal, (message_index, params, action, target) in enumerate(parsed_steps):
        repeat = repeat_features[ordinal]
        fields: dict[str, Any] = {
            "project": "external-agent-traces",
            "agent": "computer-use-agent",
            "dataset": dataset_id,
            "source": dataset["hf_repo"],
            "session": session,
            "turn": str(message_index),
            "step": str(ordinal),
            "task": "desktop-computer-use",
            "benchmark": "satraj-os",
            "environment": domain,
            "category": sanitize_label(str(row.get("trajectory_category") or "unknown")),
            "phase": satraj_action_phase(action),
            "op": "action",
            "tool": "computer",
            "action": action,
            "target": target,
            "status": status,
            "safety": safety,
            "attack": attack_flag,
            "attack_type": sanitize_label(str(attack.get("attack_type") or "none")),
            "reward": sanitize_label(str(result.get("reward") if result.get("reward") is not None else "unknown")),
            "repeat_state": repeat["repeat_state"],
            "repeat_signal": repeat["repeat_signal"],
            "repeat_run": repeat["repeat_run"],
        }
        if include_text:
            fields["parameter_shape"] = sanitize_label("-".join(sorted(params)) or "none")
        operations.append({"value": 1, "fields": fields})
    return operations


def normalize_scalecua(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    row_index: int,
    include_text: bool,
) -> dict[str, Any]:
    image = str(row.get("image") or "")
    session = sanitize_label(scalecua_session_from_image(image) or f"scalecua-{row_index}")
    step = scalecua_step_from_image(image, row_index)
    platform = scalecua_platform(dataset, image)
    trajectory_type = scalecua_trajectory_type(dataset)
    conversations = conversation_messages(row.get("conversations"))
    human_text = "\n".join(
        str(message.get("value") or "")
        for message in conversations
        if str(message.get("from") or "").lower() == "human"
    )
    gpt_text = "\n".join(
        str(message.get("value") or "")
        for message in conversations
        if str(message.get("from") or "").lower() == "gpt"
    )
    action_raw = scalecua_action_payload(gpt_text)
    action = scalecua_action_verb(action_raw)
    target = scalecua_action_target(action, action_raw)
    history_depth = scalecua_history_depth(human_text)
    status = target if action == "terminate" and target in {"success", "failure"} else "gold"
    task_family = "web-navigation" if platform == "web" else (
        "mobile-control" if platform in {"android", "iphone", "ios"} else "desktop-computer-use"
    )
    fields: dict[str, Any] = {
        "project": "external-agent-traces",
        "agent": "human-expert-plus-model-annotated",
        "dataset": dataset_id,
        "source": dataset["hf_repo"],
        "session": session,
        "turn": str(step),
        "step": str(step),
        "task": task_family,
        "benchmark": "scalecua",
        "environment": scalecua_environment_from_image(image),
        "platform": platform,
        "trajectory_type": trajectory_type,
        "phase": scalecua_action_phase(action),
        "op": "action",
        "tool": "computer" if task_family == "desktop-computer-use" else (
            "browser" if task_family == "web-navigation" else "mobile-gui"
        ),
        "action": action,
        "target": target,
        "status": status,
        "history_depth": str(history_depth),
        "history_state": "with-history" if history_depth > 0 else "start",
        "screen_size": scalecua_screen_bucket(row),
    }
    if include_text:
        fields["task_preview"] = truncate_clean(scalecua_task_text(human_text), 180)
        fields["action_raw"] = truncate_clean(action_raw or gpt_text, 180)
    return {"value": 1, "fields": fields}


def scalecua_session_from_image(image: str) -> str:
    if "/images/" in image:
        return image.split("/images/", 1)[0]
    return str(Path(image).parent)


def scalecua_step_from_image(image: str, row_index: int) -> int:
    match = re.search(r"(?:step|before_screenshot)_([0-9]+)", image)
    if match:
        return int(match.group(1))
    return row_index


def scalecua_platform(dataset: dict[str, Any], image: str) -> str:
    repo_file = str(dataset.get("repo_file") or "").lower()
    image_l = image.lower()
    for platform in ["ubuntu", "windows", "android", "iphone", "mac", "web"]:
        if platform in repo_file or platform in image_l:
            return "ios" if platform == "iphone" else platform
    return "gui"


def scalecua_trajectory_type(dataset: dict[str, Any]) -> str:
    repo_file = str(dataset.get("repo_file") or "")
    if "navigation" in repo_file:
        return "navigation"
    if "human_action_grounding" in repo_file:
        return "human-action-grounding"
    if "action_grounding" in repo_file:
        return "action-grounding"
    if "internvl_grounding" in repo_file:
        return "grounding"
    return "gui-operation"


def scalecua_environment_from_image(image: str) -> str:
    if not image:
        return "unknown"
    return sanitize_label(image.split("/", 1)[0])


def scalecua_action_payload(text: str) -> str:
    match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.DOTALL | re.IGNORECASE)
    if match:
        return re.sub(r"\s+", " ", match.group(1)).strip()
    return extract_action_block(text)


def scalecua_action_verb(action_raw: str) -> str:
    action = action_verb(action_raw)
    aliases = {
        "doubleclick": "double_click",
        "tripleclick": "triple_click",
        "rightclick": "right_click",
        "leftclick": "click",
        "moveto": "move_to",
        "dragto": "drag",
        "typewrite": "type",
        "write": "type",
    }
    return aliases.get(action, action)


def scalecua_action_phase(action: str) -> str:
    if action == "terminate":
        return "finish"
    return osworld_action_phase(action)


def scalecua_action_target(action: str, action_raw: str) -> str:
    if action in {"click", "double_click", "triple_click", "right_click", "move_to", "drag"}:
        return coordinate_bucket(action_raw)
    if action in {"type", "write"}:
        return "text"
    if action in {"press", "hotkey", "key_down", "key_up"}:
        keys = re.findall(r"['\"]([^'\"]+)['\"]", action_raw)
        return sanitize_label("-".join(keys[:4]) or "key")
    if action == "scroll":
        return "scroll"
    if action == "terminate":
        return sanitize_label(first_match(r"status=['\"]([^'\"]+)['\"]", action_raw, "complete"))
    return "none"


def scalecua_history_depth(human_text: str) -> int:
    if "Previous operations:" not in human_text:
        return 0
    tail = human_text.split("Previous operations:", 1)[1]
    return len(re.findall(r"\bStep\s+[0-9]+:", tail))


def scalecua_task_text(human_text: str) -> str:
    match = re.search(r"\bTask:\s*(.*?)(?:\n\nPrevious operations:|$)", human_text, re.DOTALL)
    if match:
        return re.sub(r"\s+", " ", match.group(1)).strip()
    return re.sub(r"\s+", " ", human_text.replace("<image>", " ")).strip()


def scalecua_screen_bucket(row: dict[str, Any]) -> str:
    width = row.get("width")
    height = row.get("height")
    if isinstance(width, int) and isinstance(height, int):
        return f"{width}x{height}"
    return "unknown"


def normalize_osworld_human(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    row_index: int,
    include_text: bool,
) -> list[dict[str, Any]]:
    truth = row.get("human-ground-truth") or {}
    single_actions = [str(action) for action in truth.get("single-action") or []]
    grouped_actions = [
        [str(action) for action in group]
        for group in truth.get("grouped-action") or []
        if isinstance(group, list)
    ]
    group_alignment = osworld_group_alignment(single_actions, grouped_actions)
    group_meta = (
        osworld_group_meta(single_actions, grouped_actions)
        if group_alignment == "exact"
        else []
    )
    application = sanitize_label(
        str(row.get("_github_application") or row.get("snapshot") or "desktop")
    )
    session = sanitize_label(str(row.get("id") or f"osworld-human-{row_index}"))
    status = "infeasible" if osworld_is_infeasible(row, single_actions) else "gold"
    repeat_features = repeat_features_for_signatures(
        [
            (
                osworld_action_verb(action),
                osworld_action_target(osworld_action_verb(action), action),
            )
            for action in single_actions
        ]
    )

    operations = []
    for turn, raw_action in enumerate(single_actions):
        action = osworld_action_verb(raw_action)
        repeat = repeat_features[turn]
        fields: dict[str, Any] = {
            "project": "external-agent-traces",
            "agent": "human-demo",
            "dataset": dataset_id,
            "source": dataset["github_repo"],
            "session": session,
            "turn": str(turn),
            "step": str(turn),
            "task": "desktop-computer-use",
            "benchmark": "osworld-human",
            "environment": application,
            "app": application,
            "phase": osworld_action_phase(action),
            "op": "action",
            "tool": "computer",
            "action": action,
            "target": osworld_action_target(action, raw_action),
            "status": "infeasible" if action == "fail" else status,
            "group_alignment": group_alignment,
            "repeat_state": repeat["repeat_state"],
            "repeat_signal": repeat["repeat_signal"],
            "repeat_run": repeat["repeat_run"],
        }
        if group_meta:
            group = group_meta[turn]
            fields.update(
                {
                    "human_group": f"group-{group['index']:03d}",
                    "group_index": str(group["index"]),
                    "group_size": str(group["size"]),
                    "group_position": str(group["position"]),
                    "group_pattern": str(group["pattern"]),
                }
            )
        if include_text:
            fields["task_preview"] = truncate_clean(str(row.get("instruction") or ""), 180)
            fields["action_raw"] = truncate_clean(raw_action, 180)
        operations.append({"value": 1, "fields": fields})
    return operations


def osworld_group_meta(
    single_actions: list[str], grouped_actions: list[list[str]]
) -> list[dict[str, Any]]:
    flat_grouped = [action for group in grouped_actions for action in group]
    if single_actions != flat_grouped:
        raise ValueError("OSWorld-Human grouped actions do not match single actions exactly")
    meta: list[dict[str, Any]] = []
    cursor = 0
    for group_index, group in enumerate(grouped_actions):
        size = max(1, len(group))
        pattern = osworld_group_pattern(group)
        for group_pos, _ in enumerate(group):
            if cursor >= len(single_actions):
                break
            meta.append(
                {
                    "index": group_index,
                    "size": size,
                    "position": osworld_group_position(group_pos, size),
                    "pattern": pattern,
                }
            )
            cursor += 1
    return meta


def osworld_group_alignment(single_actions: list[str], grouped_actions: list[list[str]]) -> str:
    flat_grouped = [action for group in grouped_actions for action in group]
    if single_actions == flat_grouped:
        return "exact"
    if len(single_actions) != len(flat_grouped):
        return "length-mismatch"
    return "content-mismatch"


def osworld_group_position(position: int, size: int) -> str:
    if size <= 1:
        return "single"
    if position == 0:
        return "start"
    if position == size - 1:
        return "end"
    return "middle"


def osworld_group_pattern(actions: list[str]) -> str:
    verbs = {osworld_action_verb(action) for action in actions}
    if "fail" in verbs:
        return "fail"
    if verbs & {"shell", "open_file", "close_window"}:
        return "system"
    input_verbs = {"type", "press", "hotkey", "key_down", "key_up"}
    pointing_verbs = {
        "click",
        "double_click",
        "triple_click",
        "right_click",
        "move_to",
        "drag",
        "mouse_down",
        "mouse_up",
        "select",
    }
    if verbs & input_verbs and verbs & pointing_verbs:
        return "select-and-input"
    if verbs & input_verbs:
        return "input"
    if verbs & {"drag", "mouse_down", "mouse_up", "move_to"}:
        return "pointing"
    if verbs & {"click", "double_click", "triple_click", "right_click", "select"}:
        return "select"
    if "scroll" in verbs:
        return "scroll"
    if verbs & {"wait", "check", "repeat_until_done"}:
        return "observe"
    return sorted(verbs)[0] if verbs else "unknown"


def osworld_action_verb(raw_action: str) -> str:
    raw = raw_action.strip()
    match = re.search(r"`([^`]+)`", raw)
    verb = match.group(1) if match else raw.split(maxsplit=1)[0] if raw else "unknown"
    label = sanitize_label(verb)
    aliases = {
        "typing": "type",
        "rress": "press",
        "hoteky": "hotkey",
        "hotekey": "hotkey",
        "doubleclick": "double_click",
        "drag_to": "drag",
        "drag_and_drop": "drag",
        "scroll_left": "scroll",
        "key_down": "key_down",
        "key-down": "key_down",
        "key_up": "key_up",
        "key-up": "key_up",
        "keyup": "key_up",
        "keydown": "key_down",
        "key": "press",
        "move_on": "move_to",
    }
    if label.startswith("move_to"):
        return "move_to"
    if label.startswith("hotkey"):
        return "hotkey"
    if label.startswith("key_up"):
        return "key_up"
    if label.startswith("key_down"):
        return "key_down"
    if label.endswith("-click"):
        return "click"
    if label == "sudo" or label.startswith("sudo-"):
        return "shell"
    return aliases.get(label, label or "unknown")


def osworld_action_phase(action: str) -> str:
    if action in {"type", "press", "hotkey", "key_down", "key_up"}:
        return "input"
    if action in {
        "click",
        "double_click",
        "triple_click",
        "right_click",
        "move_to",
        "drag",
        "mouse_down",
        "mouse_up",
        "scroll",
        "select",
    }:
        return "navigate"
    if action in {"wait", "check", "repeat_until_done"}:
        return "observe"
    if action == "fail":
        return "fail"
    if action in {"shell", "open_file", "close_window"}:
        return "system"
    return "desktop-action"


def osworld_action_target(action: str, raw_action: str) -> str:
    if action == "type":
        return "text"
    if action in {"press", "hotkey", "key_down", "key_up"}:
        return "key"
    if action in {"click", "double_click", "triple_click", "right_click", "select"}:
        return "ui"
    if action in {"move_to", "drag", "mouse_down", "mouse_up"}:
        return "pointer"
    if action == "scroll":
        return "scroll"
    if action in {"fail", "wait", "check"}:
        return "none"
    if action in {"shell", "open_file", "close_window"}:
        return "system"
    return sanitize_label(first_match(r"`[^`]+`\s+(.+)$", raw_action, "none"))[:64] or "none"


def osworld_is_infeasible(row: dict[str, Any], single_actions: list[str]) -> bool:
    evaluator = row.get("evaluator") or {}
    if str(evaluator.get("func") or "").lower() == "infeasible":
        return True
    return any(osworld_action_verb(action) == "fail" for action in single_actions)


def parse_json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def extract_xml_tool_call_params(content: str) -> dict[str, str]:
    params: dict[str, str] = {}
    for match in re.finditer(r"<parameter=([^>]+)>\s*(.*?)\s*</parameter>", content, re.DOTALL):
        key = sanitize_label(match.group(1))
        value = re.sub(r"\s+", " ", match.group(2)).strip()
        if key and value:
            params[key] = value
    return params


def satraj_action_phase(action: str) -> str:
    if action in {"key", "type"}:
        return "input"
    if action in {
        "mouse_move",
        "left_click",
        "left_click_drag",
        "right_click",
        "middle_click",
        "double_click",
        "triple_click",
        "scroll",
        "hscroll",
    }:
        return "navigate"
    if action == "wait":
        return "observe"
    if action in {"terminate", "answer"}:
        return "finish"
    return "computer-action"


def satraj_action_target(action: str, params: dict[str, str]) -> str:
    if action in {"type", "answer"} and params.get("text"):
        return "text"
    if params.get("coordinate"):
        return coordinate_bucket(params["coordinate"])
    if params.get("keys"):
        return sanitize_label(params["keys"])
    if params.get("pixels"):
        return "pixels"
    if params.get("time"):
        return "time"
    if params.get("status"):
        return sanitize_label(params["status"])
    return "none"


def coordinate_bucket(value: str) -> str:
    numbers = re.findall(r"-?\d+(?:\.\d+)?", value)
    if len(numbers) < 2:
        return "coordinate"
    try:
        x = float(numbers[0])
        y = float(numbers[1])
    except ValueError:
        return "coordinate"
    if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
        x *= 1000.0
        y *= 1000.0
    return f"x{int(x // 100) * 100}-y{int(y // 100) * 100}"


def normalize_bool_outcome(value: Any, true_label: str, false_label: str) -> str:
    if value is True:
        return true_label
    if value is False:
        return false_label
    return "unknown"


def repeat_features_for_signatures(signatures: list[tuple[str, str]]) -> list[dict[str, str]]:
    features: list[dict[str, str]] = []
    last_signature: tuple[str, str] | None = None
    same_run = 0
    max_same_run = 0
    max_recent_signature = 0
    max_recent_target = 0
    for index, signature in enumerate(signatures):
        if signature == last_signature:
            same_run += 1
        else:
            same_run = 1
        last_signature = signature
        max_same_run = max(max_same_run, same_run)

        window = signatures[max(0, index - 4) : index + 1]
        recent_signature = sum(1 for item in window if item == signature)
        target = signature[1]
        recent_target = (
            sum(1 for item in window if item[1] == target)
            if target and target != "none"
            else recent_signature
        )
        max_recent_signature = max(max_recent_signature, recent_signature)
        max_recent_target = max(max_recent_target, recent_target)

        if same_run >= 3:
            repeat_state = "same-action-run"
        elif recent_signature >= 3:
            repeat_state = "same-action-window"
        elif target != "none" and recent_target >= 4:
            repeat_state = "target-window"
        elif same_run == 2 or recent_signature == 2 or recent_target == 2:
            repeat_state = "light-repeat"
        else:
            repeat_state = "single"
        features.append(
            {
                "repeat_state": repeat_state,
                "repeat_run": "3plus" if same_run >= 3 else str(same_run),
            }
        )

    trajectory_signal = (
        "loop-like"
        if max_same_run >= 3 or max_recent_signature >= 3 or max_recent_target >= 4
        else "none"
    )
    for feature in features:
        feature["repeat_signal"] = trajectory_signal
    return features


def normalize_tau_bench(
    dataset_id: str,
    dataset: dict[str, Any],
    row: dict[str, Any],
    row_index: int,
    include_text: bool,
) -> list[dict[str, Any]]:
    meta = row.get("meta") or {}
    task_description = meta.get("task_description") or {}
    expected_actions = {
        sanitize_label(str(action.get("name") or ""))
        for action in task_description.get("actions") or []
        if isinstance(action, dict)
    }
    outcome = tau_bench_outcome(row)
    session = sanitize_label(str(meta.get("id") or meta.get("task_id") or f"tau-{row_index}"))
    environment = sanitize_label(str(row.get("task_name") or "unknown"))
    model = sanitize_label(str(row.get("model_path") or "unknown-model"))
    operations = []
    for ordinal, message in enumerate(row.get("messages") or []):
        if not isinstance(message, dict):
            continue
        role = str(message.get("role") or "unknown").lower()
        if role == "system":
            continue
        turn = str(message.get("turn_idx") if message.get("turn_idx") is not None else ordinal)
        if role == "user":
            content = str(message.get("content") or "")
            action = "finish" if "###STOP###" in content else "user_message"
            phase = "finish" if action == "finish" else "dialogue"
            fields = tau_base_fields(
                dataset_id, dataset, session, turn, model, environment, role, outcome
            )
            fields.update(
                {
                    "phase": phase,
                    "op": "prompt",
                    "tool": "user",
                    "action": action,
                    "actor": "user",
                }
            )
            if include_text:
                fields["message_preview"] = truncate_clean(content, 180)
            operations.append({"value": 1, "fields": fields})
            continue
        if role == "tool":
            tool_name = sanitize_label(str(message.get("name") or "tool"))
            fields = tau_base_fields(
                dataset_id, dataset, session, turn, model, environment, role, outcome
            )
            fields.update(
                {
                    "phase": "observe",
                    "op": "observation",
                    "tool": tool_name,
                    "action": "observe",
                    "actor": "tool",
                }
            )
            if include_text:
                fields["message_preview"] = truncate_clean(str(message.get("content") or ""), 180)
            operations.append({"value": 1, "fields": fields})
            continue
        if role == "assistant":
            tool_calls = message.get("tool_calls") or []
            if tool_calls:
                for call_index, tool_call in enumerate(tool_calls):
                    function = tool_call.get("function") or {}
                    action = sanitize_label(str(function.get("name") or "unknown_tool"))
                    fields = tau_base_fields(
                        dataset_id,
                        dataset,
                        session,
                        f"{turn}.{call_index}",
                        model,
                        environment,
                        role,
                        outcome,
                    )
                    fields.update(
                        {
                            "phase": tau_tool_phase(action),
                            "op": "tool",
                            "tool": action,
                            "action": action,
                            "actor": "assistant",
                            "oracle_action": "expected" if action in expected_actions else "extra",
                        }
                    )
                    if include_text:
                        fields["arguments"] = truncate_clean(str(function.get("arguments") or ""), 180)
                    operations.append({"value": 1, "fields": fields})
                continue
            content = str(message.get("content") or "")
            if content:
                fields = tau_base_fields(
                    dataset_id, dataset, session, turn, model, environment, role, outcome
                )
                fields.update(
                    {
                        "phase": "dialogue",
                        "op": "llm",
                        "tool": "assistant",
                        "action": "respond",
                        "actor": "assistant",
                    }
                )
                if include_text:
                    fields["message_preview"] = truncate_clean(content, 180)
                operations.append({"value": 1, "fields": fields})
    return operations


def tau_base_fields(
    dataset_id: str,
    dataset: dict[str, Any],
    session: str,
    turn: str,
    model: str,
    environment: str,
    role: str,
    outcome: str,
) -> dict[str, Any]:
    return {
        "project": "external-agent-traces",
        "agent": model,
        "dataset": dataset_id,
        "source": dataset["hf_repo"],
        "session": session,
        "turn": turn,
        "task": "tool-agent-user",
        "benchmark": "tau-bench",
        "environment": environment,
        "role": sanitize_label(role),
        "status": outcome,
    }


def tau_bench_outcome(row: dict[str, Any]) -> str:
    meta = row.get("meta") or {}
    eval_result = row.get("eval_result") or {}
    if meta.get("is_correct") is True:
        return "success"
    if meta.get("is_correct") is False:
        return "failure"
    score = eval_result.get("score")
    if isinstance(score, (int, float)):
        if score >= 1.0:
            return "success"
        if score <= 0.0:
            return "failure"
    return "unknown"


def tau_tool_phase(action: str) -> str:
    if action.startswith(("cancel_", "exchange_", "modify_", "return_", "update_")):
        return "modify"
    if action.startswith(("find_", "get_", "list_", "search_")):
        return "inspect"
    if action.startswith(("book_", "reserve_", "send_")):
        return "modify"
    return "api"


def parse_gui_odyssey_steps(raw_steps: Any) -> list[dict[str, Any]]:
    if isinstance(raw_steps, list):
        return [step for step in raw_steps if isinstance(step, dict)]
    if not raw_steps:
        return []
    try:
        parsed = ast.literal_eval(str(raw_steps))
    except (SyntaxError, ValueError):
        return []
    if isinstance(parsed, list):
        return [step for step in parsed if isinstance(step, dict)]
    return []


def first_match(pattern: str, text: str, default: str) -> str:
    match = re.search(pattern, text)
    if not match:
        return default
    for group in match.groups():
        if group:
            return group
    return match.group(0)


def extract_action_block(text: str) -> str:
    match = re.search(r"Action:\s*(.*)", text, re.DOTALL)
    if not match:
        return ""
    action = match.group(1).strip()
    return action.splitlines()[0].strip()


def extract_code_command(text: str) -> str:
    match = re.search(r"```(?:[A-Za-z0-9_-]+)?\s*\n(.*?)```", text, re.DOTALL)
    if not match:
        return ""
    command = match.group(1).strip()
    return command.splitlines()[0].strip()


def action_verb(action: str) -> str:
    action = action.strip()
    if not action:
        return "unknown"
    verb = first_match(r"^([A-Za-z_][A-Za-z0-9_-]*)", action, "unknown")
    return sanitize_label(verb)


def infer_toolbench_tool(action: str) -> str:
    match = re.search(r"_for_([A-Za-z0-9_]+)", action)
    if match:
        return sanitize_label(match.group(1))
    return action_verb(action)


def conversation_messages(conversations: Any) -> list[dict[str, Any]]:
    if isinstance(conversations, list):
        return [message for message in conversations if isinstance(message, dict)]
    if isinstance(conversations, dict):
        senders = conversations.get("from") or []
        values = conversations.get("value") or []
        return [{"from": sender, "value": value} for sender, value in zip(senders, values)]
    return []


def stable_id(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=True)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def latest_instructor_utterance(text: str) -> str:
    utterances = re.findall(r'say\(speaker="instructor", utterance="(.*?)"\)', text, re.DOTALL)
    return utterances[-1] if utterances else ""


def sanitize_label(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_.:-]+", "-", value)
    return value.strip("-") or "none"


def truncate_clean(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "..."


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=False))
            f.write("\n")


def redact_raw_rows(rows: list[dict[str, Any]], drop_fields: list[str]) -> list[dict[str, Any]]:
    if not drop_fields:
        return rows
    return [
        {key: value for key, value in row.items() if key not in drop_fields}
        for row in rows
    ]


if __name__ == "__main__":
    sys.exit(main())
