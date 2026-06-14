from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

from .analysis import AnalysisConfig, run_analysis
from .render import write_dashboard
from .session_history import DEFAULT_CODEX_ROOT, default_claude_root
from .tagging import LlamaCppTagger, TaggingError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentflame",
        description="Read local AI agent session history, tag it with a local LLM, and render semantic flamegraphs.",
    )
    sub = parser.add_subparsers(dest="command")
    run = sub.add_parser("run", help="Generate AgentFlame JSON, folded stacks, SVGs, and HTML dashboard.")
    run.add_argument("--project-root", default=".", help="Repository root whose local sessions should be selected.")
    run.add_argument("--project-name", default="", help="Name used in folded stack project frames.")
    run.add_argument("--out", default="", help="Output directory. Defaults to .agentsight/agentflame/latest under project root.")
    run.add_argument("--codex-root", default="", help=f"Codex session root. Default: {DEFAULT_CODEX_ROOT}")
    run.add_argument("--claude-root", default="", help="Claude project session root. Default is derived from --project-root.")
    run.add_argument("--scan-files", type=int, default=160)
    run.add_argument("--max-sessions", type=int, default=36)
    run.add_argument("--llama-url", default="http://127.0.0.1:8080", help="Local llama.cpp server base URL.")
    run.add_argument("--model", default="local", help="Model id sent to /v1/chat/completions.")
    run.add_argument("--timeout", type=int, default=30, help="LLM request timeout in seconds.")
    run.add_argument(
        "--max-uncached-tags",
        type=int,
        default=-1,
        help="-1 means no limit. Any exhausted budget fails the run rather than using non-LLM fallback.",
    )
    run.add_argument("--include-previews", action="store_true", help="Store prompt previews in agentflame.json. Off by default.")
    run.add_argument("--tag-llm-calls", action="store_true", help="Use the LLM to tag each LLM call. Default token views inherit prompt tags for speed.")
    run.add_argument("--open", action="store_true", help="Open the generated dashboard in a browser.")

    render = sub.add_parser("render", help="Re-render dashboard from an existing agentflame.json and folded files.")
    render.add_argument("--out", default=".agentsight/agentflame/latest", help="Directory containing agentflame.json.")
    render.add_argument("--open", action="store_true")
    return parser


def command_run(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    out_dir = Path(args.out).resolve() if args.out else project_root / ".agentsight" / "agentflame" / "latest"
    project_name = args.project_name or project_root.name
    codex_root = Path(args.codex_root).expanduser() if args.codex_root else DEFAULT_CODEX_ROOT
    claude_root = Path(args.claude_root).expanduser() if args.claude_root else default_claude_root(project_root)
    tagger = LlamaCppTagger(
        cache_path=out_dir / "tags.json",
        base_url=args.llama_url,
        model=args.model,
        timeout_s=args.timeout,
        max_uncached=args.max_uncached_tags,
    )
    config = AnalysisConfig(
        project_root=project_root,
        out_dir=out_dir,
        project_name=project_name,
        codex_root=codex_root,
        claude_root=claude_root,
        scan_files=args.scan_files,
        max_sessions=args.max_sessions,
        include_previews=args.include_previews,
        tag_llm_calls=args.tag_llm_calls,
    )
    try:
        payload = run_analysis(config, tagger)
        write_dashboard(out_dir, payload)
    except TaggingError as exc:
        print(f"agentflame: tagging failed: {exc}", file=sys.stderr)
        print("Start llama.cpp server, for example: llama-server -m /path/to/model.gguf --port 8080", file=sys.stderr)
        return 2
    index = out_dir / "index.html"
    print(
        json.dumps(
            {
                "status": "ok",
                "out": str(out_dir),
                "dashboard": str(index),
                "agentflame_json": str(out_dir / "agentflame.json"),
                "tags_json": str(out_dir / "tags.json"),
                "sessions": payload["summary"]["session_count"],
                "system_unique_stacks": payload["summary"]["system"]["unique_stacks"],
                "llm_tag_calls": payload["llm_tagger"]["llm_calls"],
                "cache_hits": payload["llm_tagger"]["cache_hits"],
            },
            indent=2,
        )
    )
    if args.open:
        webbrowser.open(index.resolve().as_uri())
    return 0


def command_render(args: argparse.Namespace) -> int:
    out_dir = Path(args.out).resolve()
    payload_path = out_dir / "agentflame.json"
    if not payload_path.exists():
        print(f"agentflame: missing {payload_path}", file=sys.stderr)
        return 2
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    write_dashboard(out_dir, payload)
    index = out_dir / "index.html"
    print(json.dumps({"status": "ok", "dashboard": str(index)}, indent=2))
    if args.open:
        webbrowser.open(index.resolve().as_uri())
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] not in {"run", "render", "-h", "--help"}:
        argv = ["run", *argv]
    elif not argv:
        argv = ["run"]
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        return command_run(args)
    if args.command == "render":
        return command_render(args)
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
