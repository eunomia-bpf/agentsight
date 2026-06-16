from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from . import __version__
from .flamegraph import write_flamegraph_svg
from .parser import annotate_sessions, discover_sessions
from .pprof import write_pprof
from .project import PROFILE_BUILDERS, folded_lines, project_name_from_root, summarize_sessions


def display_path(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentpprof",
        description="Build pprof-compatible semantic profiles from local coding-agent sessions.",
    )
    parser.add_argument("--version", action="version", version=f"agentpprof {__version__}")
    sub = parser.add_subparsers(dest="command")

    export = sub.add_parser("export", help="export semantic pprof profiles")
    export.add_argument("--project-root", type=Path, default=Path("."))
    export.add_argument("--out", type=Path, default=Path(".agentsight/agentpprof/latest"))
    export.add_argument("--codex-root", type=Path)
    export.add_argument("--claude-root", type=Path)
    export.add_argument("--session-file", type=Path, action="append", default=[])
    export.add_argument("--scan-files", type=int, default=160)
    export.add_argument("--max-sessions", type=int, default=36)
    export.add_argument(
        "--profile",
        choices=["all", *PROFILE_BUILDERS.keys()],
        default="all",
        help="which profile projection to export",
    )
    export.add_argument(
        "--render",
        choices=["none", "top", "all"],
        default="top",
        help="run go tool pprof for text reports; all also tries SVG graphs",
    )
    export.set_defaults(func=command_export)
    return parser


def run_pprof_reports(out_dir: Path, profile_name: str, profile_path: Path, mode: str) -> list[str]:
    warnings: list[str] = []
    if mode == "none":
        return warnings
    go = shutil.which("go")
    if not go:
        warnings.append("go tool not found; skipped pprof reports")
        return warnings
    top_path = out_dir / f"{profile_name}.top.txt"
    proc = subprocess.run(
        [go, "tool", "pprof", "-top", str(profile_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode == 0:
        top_path.write_text(proc.stdout, encoding="utf-8")
    else:
        warnings.append(f"go tool pprof -top failed for {profile_name}: {proc.stderr.strip()}")
    if mode == "all":
        svg_path = out_dir / f"{profile_name}.svg"
        proc = subprocess.run(
            [go, "tool", "pprof", "-svg", "-output", str(svg_path), str(profile_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if proc.returncode != 0:
            warnings.append(f"go tool pprof -svg failed for {profile_name}: {proc.stderr.strip()}")
    return warnings


def command_export(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    project_name = project_name_from_root(project_root)

    sessions, warnings = discover_sessions(
        project_root=project_root,
        codex_root=args.codex_root,
        claude_root=args.claude_root,
        session_files=args.session_file,
        scan_files=args.scan_files,
        max_sessions=args.max_sessions,
    )
    annotate_sessions(sessions)
    selected = PROFILE_BUILDERS.keys() if args.profile == "all" else [args.profile]

    artifacts: dict[str, dict[str, object]] = {}
    for profile_name in selected:
        sample_type, sample_unit, builder = PROFILE_BUILDERS[profile_name]
        samples = builder(project_name, sessions)
        profile_path = out_dir / f"{profile_name}.pb.gz"
        folded_path = out_dir / f"{profile_name}.folded.txt"
        flamegraph_path = out_dir / f"{profile_name}.flame.svg"
        write_pprof(
            profile_path,
            sample_type,
            sample_unit,
            samples,
            comments=[
                "agentpprof semantic profile",
                f"projection={profile_name}",
                f"project={project_name}",
            ],
        )
        folded_path.write_text("\n".join(folded_lines(samples)) + ("\n" if samples else ""), encoding="utf-8")
        write_flamegraph_svg(
            flamegraph_path,
            samples,
            title=f"agentpprof {profile_name} flamegraph",
            unit=sample_unit,
        )
        warnings.extend(run_pprof_reports(out_dir, profile_name, profile_path, args.render))
        artifacts[profile_name] = {
            "profile": display_path(profile_path, out_dir),
            "folded": display_path(folded_path, out_dir),
            "flamegraph": display_path(flamegraph_path, out_dir),
            "samples": len(samples),
            "total_value": sum(sample.value for sample in samples),
        }

    summary = {
        "schema_version": 1,
        "tool": "agentpprof",
        "project": {"name": project_name, "root": str(project_root)},
        "inputs": {
            "codex_root": str(args.codex_root or Path.home() / ".codex" / "sessions"),
            "claude_root": str(args.claude_root) if args.claude_root else None,
            "session_files": [str(path) for path in args.session_file],
            "scan_files": args.scan_files,
            "max_sessions": args.max_sessions,
        },
        "summary": summarize_sessions(sessions),
        "artifacts": artifacts,
        "warnings": warnings,
    }
    summary_path = out_dir / "agentpprof.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": "ok", "out": str(out_dir), "summary": str(summary_path), "artifacts": artifacts}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 2
    return int(args.func(args))
