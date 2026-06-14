#!/usr/bin/env python3
"""Run the local semantic flamegraph artifact pipeline end to end."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_LLAMA_CLI = REPO_ROOT.parent / "llama.cpp-latest" / "build" / "bin" / "llama-cli"


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except Exception:
        return path.name


def scrub(text: str, repo_root: Path) -> str:
    home = str(Path.home())
    cleaned = text.replace(home, "$HOME")
    cleaned = cleaned.replace(str(repo_root.resolve()), "$REPO")
    return cleaned[-2400:]


def default_model() -> str:
    model_dir = REPO_ROOT.parent / "llama.cpp-latest" / "models"
    if not model_dir.exists():
        return ""
    candidates = [
        path
        for path in sorted(model_dir.glob("*.gguf"))
        if "vocab" not in path.name.lower()
    ]
    preferred = [
        path
        for path in candidates
        if any(token in path.name.lower() for token in ("instruct", "chat", "qwen", "tinyllama"))
    ]
    preferred.extend(path for path in candidates if path not in preferred)
    return str(preferred[0]) if preferred else ""


def cmd_path(path: str | Path) -> str:
    return os.path.relpath(str(Path(path).resolve()), str(REPO_ROOT.resolve()))


def run_step(label: str, cmd: list[str], report: dict[str, Any]) -> None:
    started = time.time()
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = round(time.time() - started, 3)
    row = {
        "label": label,
        "returncode": proc.returncode,
        "duration_seconds": elapsed,
        "stdout_tail": scrub(proc.stdout, REPO_ROOT),
        "stderr_tail": scrub(proc.stderr, REPO_ROOT),
    }
    report["steps"].append(row)
    if proc.returncode != 0:
        raise SystemExit(f"{label} failed with return code {proc.returncode}")


def script(name: str) -> str:
    return cmd_path(SCRIPT_DIR / name)


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "schema_version": 1,
        "status": "running",
        "out_dir": rel(out_dir),
        "config": {
            "scan_files": args.scan_files,
            "max_sessions": args.max_sessions,
            "llama_limit": args.llama_limit,
            "model": Path(args.model).name if args.model else None,
            "llama_cli": Path(args.llama_cli).name if args.llama_cli else None,
            "lineage_snapshot": Path(args.lineage_snapshot).name if args.lineage_snapshot else "fixture",
            "skip_tests": args.skip_tests,
            "skip_stability": args.skip_stability,
        },
        "steps": [],
    }
    report_path = out_dir / "pipeline-report.json"
    summary_path = out_dir / "pipeline-summary.md"

    model_args: list[str] = []
    if args.model and args.llama_cli and Path(args.model).exists() and Path(args.llama_cli).exists():
        model_args = [
            "--model",
            cmd_path(args.model),
            "--llama-cli",
            cmd_path(args.llama_cli),
            "--llama-limit",
            str(args.llama_limit),
            "--llama-timeout",
            str(args.llama_timeout),
        ]

    try:
        run_step(
            "semantic-flamegraphs",
            [
                sys.executable,
                script("semantic_tag_flamegraph.py"),
                "--out",
                str(out_dir),
                "--scan-files",
                str(args.scan_files),
                "--max-sessions",
                str(args.max_sessions),
                *model_args,
            ],
            report,
        )

        lineage_cmd = [
            sys.executable,
            script("effect_lineage_smoke.py"),
            "--out",
            str(out_dir),
        ]
        if args.lineage_snapshot:
            lineage_cmd.extend(["--snapshot", cmd_path(args.lineage_snapshot)])
        else:
            lineage_cmd.append("--fixture")
        run_step("effect-lineage", lineage_cmd, report)

        if not args.skip_stability:
            run_step(
                "tag-stability",
                [
                    sys.executable,
                    script("tag_stability_smoke.py"),
                    "--out",
                    str(out_dir),
                    "--scan-files",
                    str(args.scan_files),
                    "--max-sessions",
                    str(args.max_sessions),
                    "--fragments",
                    str(args.stability_fragments),
                    "--repeats",
                    str(args.stability_repeats),
                    *model_args,
                ],
                report,
            )

        run_step("user-task-benchmark", [sys.executable, script("user_task_benchmark.py"), "--out", str(out_dir)], report)
        run_step("artifact-evaluation", [sys.executable, script("evaluate_artifacts.py"), "--out", str(out_dir)], report)
        run_step("visual-summary", [sys.executable, script("visual_summary.py"), "--out", str(out_dir)], report)
        run_step("artifact-verify", [sys.executable, script("verify_artifacts.py"), "--out", str(out_dir)], report)

        if not args.skip_tests:
            run_step(
                "unit-tests",
                [sys.executable, "-m", "unittest", "docs/visexp/test_semantic_tag_flamegraph.py"],
                report,
            )
        report["status"] = "ok"
    except BaseException:
        report["status"] = "failed"
        raise
    finally:
        report["duration_seconds"] = round(sum(step["duration_seconds"] for step in report["steps"]), 3)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        lines = [
            "# Pipeline Summary",
            "",
            f"- Status: {report['status']}",
            f"- Output directory: `{report['out_dir']}`",
            f"- Steps: {len(report['steps'])}",
            f"- Duration: {report['duration_seconds']} seconds",
            "",
            "| Step | Return code | Seconds |",
            "|------|-------------|---------|",
        ]
        for step in report["steps"]:
            lines.append(f"| {step['label']} | {step['returncode']} | {step['duration_seconds']} |")
        summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": report["status"], "out": rel(out_dir), "steps": len(report["steps"])}, indent=2))
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(SCRIPT_DIR / "out"))
    parser.add_argument("--scan-files", type=int, default=160)
    parser.add_argument("--max-sessions", type=int, default=36)
    parser.add_argument("--model", default=os.environ.get("AGENTSIGHT_VIS_MODEL", default_model()))
    parser.add_argument("--llama-cli", default=str(DEFAULT_LLAMA_CLI) if DEFAULT_LLAMA_CLI.exists() else "")
    parser.add_argument("--llama-limit", type=int, default=60)
    parser.add_argument("--llama-timeout", type=int, default=20)
    parser.add_argument("--lineage-snapshot", default="", help="Optional AgentSight snapshot JSON. Defaults to fixture smoke.")
    parser.add_argument("--stability-fragments", type=int, default=24)
    parser.add_argument("--stability-repeats", type=int, default=2)
    parser.add_argument("--skip-stability", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
